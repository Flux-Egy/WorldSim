namespace WorldSim.Core
{
    /// <summary>
    /// Everything world generation needs, as plain values (blittable, safe to copy into Burst
    /// jobs). Built once per world from the single <see cref="WorldSeed"/> (§4.3).
    /// </summary>
    public struct WorldGenParams
    {
        public int Width;
        public int Height;
        public ulong HeightSeed;
        public ulong MoistureSeed;
        public ulong TemperatureSeed;
        public ulong EdgeRefineSeed;
        public ulong DetailSeed;
        public ulong ResourceSeed;
        public ulong AnomalySeed;
        public ulong DecorationSeed;

        public static WorldGenParams Create(WorldSeed seed, int width, int height)
        {
            return new WorldGenParams
            {
                Width = width,
                Height = height,
                HeightSeed = seed.Derive(SeedStream.Height),
                MoistureSeed = seed.Derive(SeedStream.Moisture),
                TemperatureSeed = seed.Derive(SeedStream.Temperature),
                EdgeRefineSeed = seed.Derive(SeedStream.EdgeRefine),
                DetailSeed = seed.Derive(SeedStream.Detail),
                ResourceSeed = seed.Derive(SeedStream.Resources),
                AnomalySeed = seed.Derive(SeedStream.Anomaly),
                DecorationSeed = seed.Derive(SeedStream.Decoration),
            };
        }
    }

    /// <summary>
    /// Deterministic layered world generation (§4.2), integer-only. Each tile depends only on
    /// (params, x, y), so tiles can be generated in any order or in parallel (Burst
    /// IJobParallelFor) with identical results.
    ///
    /// Passes, in §4.2 order:
    ///   1. Continental shape: low-frequency fBm height, pulled down towards the map border so
    ///      the world is land surrounded by ocean.
    ///   2. Biome assignment: a climate table over (height, moisture, temperature), then rare
    ///      coherent "anomaly" regions that become the fictional biomes.
    ///   3. Edge refinement: a second noise layer warps the sampling position and jitters the
    ///      biome thresholds, so borders are irregular instead of straight contour lines.
    ///   4. Detail: clumped scatter of decorations (trees, plants, rocks, crystals) and ore;
    ///      resources follow from biome and decoration.
    /// </summary>
    public static class WorldGenerator
    {
        const int One = FixedNoise.One;

        // Height thresholds on the 0..255 height byte.
        public const byte DeepWaterBelow = 88;
        public const byte SeaLevel = 112;        // below: shallow water
        public const byte BeachBelow = 119;      // below: sand
        public const byte MountainFrom = 196;
        public const byte SnowPeakFrom = 240;

        // Feature sizes scale with the map up to these limits (in tiles). Past them a bigger map
        // gets MORE continents, ranges and climate zones instead of the same ones magnified
        // (plan A5). All limits are above what a 256-tile map uses, so its golden hashes hold.
        public const int MaxContinentPeriod = 180;
        public const int MaxRidgePeriod = 110;
        public const int MaxClimatePeriod = 130;
        public const int MaxWarpPeriod = 110;
        public const int MaxWarpAmplitude = 40;
        public const int MaxBorderBand = 48;

        public static TileData GenerateTile(in WorldGenParams p, int x, int y)
        {
            long px = (long)x << FixedNoise.FracBits;
            long py = (long)y << FixedNoise.FracBits;
            int minDim = p.Width < p.Height ? p.Width : p.Height;

            // ---- Pass 3a (edge refinement): domain warp, up to ~10% of the map size ----
            int warpPeriod = Clamp(minDim / 5, 8, MaxWarpPeriod);
            long warpAmp = Clamp(minDim / 10, 2, MaxWarpAmplitude);
            long wx = px + FixedNoise.Fbm(p.EdgeRefineSeed, px, py, warpPeriod, 3) * warpAmp;
            long wy = py + FixedNoise.Fbm(p.EdgeRefineSeed ^ 0xA5A5A5A5A5A5A5A5UL, px, py, warpPeriod, 3) * warpAmp;

            // ---- Pass 1: continental height ----
            int continentPeriod = Clamp(minDim / 3, 16, MaxContinentPeriod);
            int n = FixedNoise.Fbm(p.HeightSeed, wx, wy, continentPeriod, 5); // [-One, One], clusters near 0
            // Ridges: 1 - |noise| peaks along lines, which reads as mountain ranges.
            long ridge = One - Abs(FixedNoise.Fbm(p.HeightSeed ^ 0x5A5A5A5A5A5A5A5AUL, wx, wy, Clamp(minDim / 5, 12, MaxRidgePeriod), 3));
            long ridgeLift = ridge > One * 74 / 100 ? (ridge - One * 74 / 100) * 2 : 0;  // 0..0.52
            long falloff = BorderFalloff(x, y, p.Width, p.Height);           // [0, One]
            // fBm stretched x1.7 (its octave sum rarely nears ±1), small land bias, ridges only
            // lift land that is already above sea level, border pulled down to ocean.
            long h = (long)n * 170 / 100 + One * 4 / 100 - falloff * 120 / 100;
            if (h > -One * 10 / 100) h += ridgeLift;
            byte height = ToByte(h);

            // ---- Moisture and temperature fields ----
            // fBm clusters near 0: stretch x1.6 so very dry (desert) and very wet (jungle, swamp) occur.
            byte moisture = ToByte((long)FixedNoise.Fbm(p.MoistureSeed, wx, wy, Clamp(minDim / 4, 12, MaxClimatePeriod), 4) * 160 / 100);

            // Temperature: warm equator (middle row), cold poles, colder with altitude.
            long latitude = One - Abs((long)y * 2 * One / Max(1, p.Height - 1) - One); // [0, One]
            long tNoise = FixedNoise.Fbm(p.TemperatureSeed, wx, wy, Clamp(minDim / 3, 12, MaxClimatePeriod), 3);
            long altitudeChill = height > SeaLevel ? (long)(height - SeaLevel) * One / (255 - SeaLevel) : 0;
            long t = (latitude * 2 - One) * 80 / 100 + tNoise * 35 / 100 - altitudeChill * 45 / 100;
            byte temperature = ToByte(t);

            // ---- Pass 3b (edge refinement): smooth small-scale threshold jitter (period ~3 tiles).
            // Smooth rather than per-tile random, so borders get wiggly instead of speckled.
            int jitter = FixedNoise.Sample(p.EdgeRefineSeed ^ 0x3C3C3C3C3C3C3C3CUL, px / 3, py / 3) * 5 / One; // -5..+5

            // ---- Pass 2: biome (climate table + fictional anomaly regions) ----
            Biome biome = Classify(height, moisture, temperature, jitter);
            biome = ApplyAnomaly(p, wx, wy, minDim, biome);

            // ---- Pass 4: decorations and resources ----
            Decoration deco = ScatterDecoration(p, x, y, px, py, biome, temperature);
            byte resources = Resources(p, x, y, biome, deco);

            return new TileData
            {
                BiomeId = (byte)biome,
                Height = height,
                Moisture = moisture,
                Temperature = temperature,
                ResourceFlags = resources,
                DecorationId = (byte)deco,
            };
        }

        /// <summary>
        /// Climate table (pass 2). Water and relief by height; lowland biome by temperature band
        /// and moisture. Public so the table can be unit-tested.
        /// </summary>
        public static Biome Classify(byte height, byte moisture, byte temperature, int jitter)
        {
            int h = height + jitter;
            int m = moisture + jitter * 2;
            int t = temperature;
            if (h < DeepWaterBelow) return Biome.DeepWater;
            if (h < SeaLevel) return Biome.ShallowWater;
            if (h < BeachBelow) return t < 40 ? Biome.Snow : Biome.Sand;
            if (h >= SnowPeakFrom) return Biome.Snow;
            if (h >= MountainFrom) return t < 48 ? Biome.Snow : Biome.Mountain;

            if (t < 34) return Biome.Snow;                                         // polar ice
            if (t < 64) return m >= 125 ? Biome.Taiga : Biome.Tundra;              // cold
            if (t < 110) return m >= 150 ? Biome.Taiga : m >= 118 ? Biome.BirchForest : Biome.Grass; // cool
            if (t < 150)                                                            // temperate
            {
                if (m >= 168 && h < 140) return Biome.Swamp;
                return m >= 134 ? Biome.Forest : Biome.Grass;
            }
            if (t < 176) return m >= 160 ? Biome.Jungle : m >= 118 ? Biome.Forest : m >= 100 ? Biome.Grass : Biome.Savanna; // warm
            return m >= 150 ? Biome.Jungle : m >= 92 ? Biome.Savanna : Biome.Desert; // hot
        }

        /// <summary>
        /// Rare, coherent regions of the fictional biomes: a low-frequency field picks a few
        /// patches of lowland (several percent of land); a second coarse field decides which kind each
        /// patch is. Ember wastes get a lava core.
        /// </summary>
        static Biome ApplyAnomaly(in WorldGenParams p, long wx, long wy, int minDim, Biome b)
        {
            if (b == Biome.DeepWater || b == Biome.ShallowWater || b == Biome.Sand ||
                b == Biome.Mountain || b == Biome.Snow)
                return b;
            int period = Clamp(minDim / 5, 16, 70);
            int a = FixedNoise.Fbm(p.AnomalySeed, wx, wy, period, 2);              // [-One, One]
            int threshold = One * 22 / 100;
            if (a < threshold) return b;
            int kind = FixedNoise.Sample(p.AnomalySeed ^ 0x1F1F1F1F1F1F1F1FUL, wx / (period * 2), wy / (period * 2));
            // Sample is ~[-0.7, 0.7]; split into four bands.
            if (kind < -One * 18 / 100) return Biome.CrystalFields;
            if (kind < 0) return Biome.MushroomGrove;
            if (kind < One * 18 / 100) return Biome.Glimmerwood;
            return a > One * 40 / 100 ? Biome.Lava : Biome.EmberWastes;
        }

        /// <summary>
        /// Clumped decoration scatter (pass 4): each biome has a base density per decoration;
        /// a smooth "grove" field (period ~7 tiles) modulates it, so forests have clearings and
        /// grassland has small groves instead of uniform noise.
        /// </summary>
        static Decoration ScatterDecoration(in WorldGenParams p, int x, int y, long px, long py, Biome b, byte temperature)
        {
            ulong h = FixedNoise.LatticeHash(p.DecorationSeed, x, y);
            int roll = (int)(h % 1000);                      // 0..999
            int pick = (int)((h >> 20) % 100);               // variant choice 0..99
            int grove = FixedNoise.Sample(p.DecorationSeed ^ 0x7E7E7E7E7E7E7E7EUL, px / 7, py / 7); // ~[-0.7,0.7]
            int clump = 100 + grove * 90 / One;              // ~37..163 percent

            switch (b)
            {
                case Biome.Grass:
                    if (roll < (70 * clump / 100)) return pick < 80 ? Decoration.OakTree : Decoration.BirchTree;
                    if (roll < (70 * clump / 100) + 40) return pick < 60 ? Decoration.Bush : Decoration.BerryBush;
                    if (roll < (70 * clump / 100) + 110) return pick < 55 ? Decoration.Flowers : Decoration.TallGrass;
                    if (roll < (70 * clump / 100) + 125) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Forest:
                    if (roll < (560 * clump / 100)) return pick < 85 ? Decoration.OakTree : Decoration.BirchTree;
                    if (roll < (560 * clump / 100) + 80) return pick < 70 ? Decoration.Bush : Decoration.BerryBush;
                    if (roll < (560 * clump / 100) + 120) return Decoration.Mushroom;
                    return Decoration.None;
                case Biome.BirchForest:
                    if (roll < (480 * clump / 100)) return pick < 80 ? Decoration.BirchTree : Decoration.PineTree;
                    if (roll < (480 * clump / 100) + 90) return pick < 50 ? Decoration.Flowers : Decoration.TallGrass;
                    return Decoration.None;
                case Biome.Taiga:
                    if (roll < (560 * clump / 100)) return temperature < 50 && pick < 45 ? Decoration.SnowPine : Decoration.PineTree;
                    if (roll < (560 * clump / 100) + 30) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Tundra:
                    if (roll < 25) return Decoration.SnowPine;
                    if (roll < 55) return Decoration.Rock;
                    if (roll < 75) return Decoration.TallGrass;
                    return Decoration.None;
                case Biome.Snow:
                    if (roll < 18) return Decoration.IceRock;
                    if (roll < 26) return Decoration.SnowPine;
                    return Decoration.None;
                case Biome.Jungle:
                    if (roll < (650 * clump / 100)) return pick < 80 ? Decoration.JungleTree : Decoration.PalmTree;
                    if (roll < (650 * clump / 100) + 120) return Decoration.Bush;
                    if (roll < (650 * clump / 100) + 160) return Decoration.Flowers;
                    return Decoration.None;
                case Biome.Savanna:
                    if (roll < (45 * clump / 100)) return Decoration.AcaciaTree;
                    if (roll < (45 * clump / 100) + 120) return Decoration.TallGrass;
                    if (roll < (45 * clump / 100) + 145) return Decoration.Bush;
                    if (roll < (45 * clump / 100) + 155) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Desert:
                    if (roll < 22) return Decoration.Cactus;
                    if (roll < 36) return Decoration.Rock;
                    if (roll < 40) return Decoration.DeadTree;
                    return Decoration.None;
                case Biome.Swamp:
                    if (roll < (280 * clump / 100)) return Decoration.SwampTree;
                    if (roll < (280 * clump / 100) + 170) return Decoration.Reeds;
                    if (roll < (280 * clump / 100) + 210) return Decoration.Mushroom;
                    return Decoration.None;
                case Biome.Sand:
                    if (temperature > 170 && roll < 30) return Decoration.PalmTree;
                    if (roll < 45) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Mountain:
                    if (roll < 70) return pick < 60 ? Decoration.Rock : Decoration.Boulder;
                    if (roll < 85) return Decoration.PineTree;
                    return Decoration.None;
                case Biome.CrystalFields:
                    if (roll < (170 * clump / 100)) return Decoration.Crystal;
                    if (roll < (170 * clump / 100) + 40) return Decoration.Rock;
                    return Decoration.None;
                case Biome.MushroomGrove:
                    if (roll < (300 * clump / 100)) return Decoration.GiantMushroom;
                    if (roll < (300 * clump / 100) + 160) return Decoration.Mushroom;
                    return Decoration.None;
                case Biome.EmberWastes:
                    if (roll < 110) return Decoration.EmberRock;
                    if (roll < 150) return Decoration.DeadTree;
                    return Decoration.None;
                case Biome.Glimmerwood:
                    if (roll < (480 * clump / 100)) return Decoration.GlowTree;
                    if (roll < (480 * clump / 100) + 120) return Decoration.Flowers;
                    return Decoration.None;
                default:
                    return Decoration.None; // water, lava
            }
        }

        /// <summary>Resources follow the decoration (trees: wood, rocks: stone) and the biome (ore).</summary>
        static byte Resources(in WorldGenParams p, int x, int y, Biome biome, Decoration deco)
        {
            uint roll = (uint)(FixedNoise.LatticeHash(p.ResourceSeed, x, y) % 10000); // 0.01% resolution
            ResourceFlags f = ResourceFlags.None;
            if (TileData.IsTree(deco)) f |= ResourceFlags.Wood;
            if (TileData.IsRock(deco)) f |= ResourceFlags.Stone;
            switch (biome)
            {
                case Biome.Mountain:
                    f |= ResourceFlags.Stone;
                    if (roll < 250) f |= ResourceFlags.Gold;       // 2.5%
                    else if (roll < 330) f |= ResourceFlags.Gems;  // 0.8%
                    break;
                case Biome.Snow:
                    if (roll < 60) f |= ResourceFlags.Gems;
                    break;
                case Biome.CrystalFields:
                    if (deco == Decoration.Crystal) f |= ResourceFlags.Gems;
                    break;
                case Biome.EmberWastes:
                    if (roll < 300) f |= ResourceFlags.Gold;
                    break;
            }
            return (byte)f;
        }

        /// <summary>0 in the interior, rising to One at the map border (outer 14% of the smaller side).</summary>
        static long BorderFalloff(int x, int y, int w, int h)
        {
            int dx = Min(x, w - 1 - x);
            int dy = Min(y, h - 1 - y);
            int d = Min(dx, dy);                     // tiles to the nearest border
            int band = Clamp(Min(w, h) * 14 / 100, 4, MaxBorderBand);
            if (d >= band) return 0;
            long t = (long)(band - d) * One / band;  // 0..One towards the border
            return t * t >> FixedNoise.FracBits;     // ease-in
        }

        /// <summary>Maps Q16.16 in [-One, One] to 0..255 (clamped).</summary>
        static byte ToByte(long v)
        {
            long b = (v + One) * 255 / (2L * One);
            if (b < 0) b = 0;
            if (b > 255) b = 255;
            return (byte)b;
        }

        static int Max(int a, int b) => a > b ? a : b;
        static int Clamp(int v, int lo, int hi) => v < lo ? lo : v > hi ? hi : v;
        static int Min(int a, int b) => a < b ? a : b;
        static long Abs(long a) => a < 0 ? -a : a;

        /// <summary>Single-threaded reference generator (tests, tools). Simulation uses the Burst job.</summary>
        public static void Generate(in WorldGenParams p, TileData[] tiles)
        {
            for (int y = 0; y < p.Height; y++)
                for (int x = 0; x < p.Width; x++)
                    tiles[y * p.Width + x] = GenerateTile(p, x, y);
        }
    }

    /// <summary>
    /// World-state hash (§4.3 acceptance, §14.1). FNV-1a over a header (seed, size) and the six
    /// bytes of every tile in row-major order. Shared by the reference generator, the Burst
    /// hashing job and the save system, so every hash is computed one way.
    /// </summary>
    public static class WorldHash
    {
        public static StableHash64 Begin(ulong seed, int width, int height)
        {
            var h = StableHash64.Create();
            h.Add(seed);
            h.Add(width);
            h.Add(height);
            return h;
        }

        public static void AddTile(ref StableHash64 h, TileData t)
        {
            h.Add(t.BiomeId);
            h.Add(t.Height);
            h.Add(t.Moisture);
            h.Add(t.Temperature);
            h.Add(t.ResourceFlags);
            h.Add(t.DecorationId);
        }

        public static ulong Compute(ulong seed, int width, int height, TileData[] tiles)
        {
            var h = Begin(seed, width, height);
            for (int i = 0; i < tiles.Length; i++) AddTile(ref h, tiles[i]);
            return h.Value;
        }
    }
}
