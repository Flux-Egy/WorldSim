namespace WorldSim.Core
{
    /// <summary>
    /// Player-chosen generation settings (Beta B2). Part of a world's identity: they enter the
    /// world hash whenever they differ from <see cref="Default"/>. Persisted: only append fields.
    /// </summary>
    public struct WorldGenSettings
    {
        public sbyte LandBias;     // percent: -30 (islands) .. +30 (one big continent)
        public byte Mountains;     // percent of normal ridge height: 0 .. 200
        public sbyte Temperature;  // percent shift: -40 (ice age) .. +40 (hot)
        public sbyte Moisture;     // percent shift: -40 (dry) .. +40 (wet)
        public byte Blank;         // 0 = generated, 1 = empty ocean, 2 = flat land

        public static WorldGenSettings Default => new WorldGenSettings { Mountains = 100 };

        public bool IsDefault => LandBias == 0 && Mountains == 100 && Temperature == 0 && Moisture == 0 && Blank == 0;
    }

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
        public WorldGenSettings Settings;

        public static WorldGenParams Create(WorldSeed seed, int width, int height) =>
            Create(seed, width, height, WorldGenSettings.Default);

        public static WorldGenParams Create(WorldSeed seed, int width, int height, WorldGenSettings settings)
        {
            return new WorldGenParams
            {
                Settings = settings,
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
        public const byte HighlandFrom = 188;    // dry land from here up: rocky highland
        public const byte MountainFrom = 204;
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
            long h = (long)n * 170 / 100 + One * 4 / 100 - falloff * 120 / 100 + (long)p.Settings.LandBias * One / 100;
            if (h > -One * 10 / 100) h += ridgeLift * p.Settings.Mountains / 100;
            if (p.Settings.Blank == 1) h = -One * 45 / 100;                       // empty ocean
            else if (p.Settings.Blank == 2) h = falloff > One / 2 ? -One * 30 / 100 : One * 12 / 100; // flat land, ocean rim
            byte height = ToByte(h);

            // ---- Moisture and temperature fields ----
            // fBm clusters near 0: stretch x1.6 so very dry (desert) and very wet (jungle, swamp) occur.
            // Two octaves over a third of the map: large, coherent climate regions (rebuild: "big clean biomes").
            byte moisture = ToByte((long)FixedNoise.Fbm(p.MoistureSeed, wx, wy, Clamp(minDim * 2 / 5, 12, MaxClimatePeriod), 2) * 185 / 100
                                   + (long)p.Settings.Moisture * One / 100);

            // Temperature: warm equator (middle row), cold poles, colder with altitude.
            long latitude = One - Abs((long)y * 2 * One / Max(1, p.Height - 1) - One); // [0, One]
            long tNoise = FixedNoise.Fbm(p.TemperatureSeed, wx, wy, Clamp(minDim / 3, 12, MaxClimatePeriod), 2);
            long altitudeChill = height > SeaLevel ? (long)(height - SeaLevel) * One / (255 - SeaLevel) : 0;
            long t = (latitude * 2 - One) * 80 / 100 + tNoise * 35 / 100 - altitudeChill * 45 / 100
                     + (long)p.Settings.Temperature * One / 100;
            byte temperature = ToByte(t);

            // ---- Pass 3b (edge refinement): smooth small-scale threshold jitter (period ~3 tiles).
            // Smooth rather than per-tile random, so borders get wiggly instead of speckled.
            int jitter = FixedNoise.Sample(p.EdgeRefineSeed ^ 0x3C3C3C3C3C3C3C3CUL, px / 5, py / 5) * 2 / One; // -2..+2

            // ---- Pass 2: biome (climate table + fictional anomaly regions) ----
            Biome biome = Classify(height, moisture, temperature, jitter);
            if (p.Settings.Blank == 0) biome = ApplyAnomaly(p, wx, wy, minDim, biome);

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
            int m = moisture + jitter;
            int t = temperature;
            if (h < DeepWaterBelow) return Biome.DeepWater;
            if (h < SeaLevel) return t >= 168 && h >= SeaLevel - 10 ? Biome.CoralShallows : Biome.ShallowWater; // warm reefs near shore
            if (h < BeachBelow) return Biome.Beach;
            if (h >= SnowPeakFrom) return Biome.Snow;                                // snow caps only on the peaks
            if (h >= MountainFrom) return Biome.Mountain;
            if (h >= HighlandFrom && m < 128 && t >= 48) return Biome.RockyHighland;   // dry foothills below the peaks

            if (t < 16) return Biome.Glacier;                                        // polar ice sheet (small)
            if (t < 64) return m >= 125 ? Biome.PineTaiga : Biome.Tundra;            // cold
            if (t < 110)                                                             // cool
            {
                if (m >= 150) return Biome.PineTaiga;
                if (m >= 118) return Biome.BirchForest;
                return m < 72 ? Biome.Steppe : Biome.Meadow;
            }
            if (t < 150)                                                             // temperate
            {
                if (m >= 168 && h < 140) return Biome.Swamp;
                if (m >= 134) return Biome.Forest;
                if (m >= 120) return Biome.FlowerField;                              // the meadow-forest edge
                return m < 80 ? Biome.Steppe : Biome.Meadow;
            }
            if (t < 176)                                                             // warm
                return m >= 160 ? Biome.Jungle : m >= 118 ? Biome.Forest : m >= 100 ? Biome.Meadow : Biome.Savanna;
            // hot
            if (m >= 150) return Biome.Jungle;
            if (m >= 92) return Biome.Savanna;
            if (h >= 156) return Biome.Badlands;                                     // raised dry land: eroded mesas
            if (m < 60 && h < 134) return Biome.SaltFlats;                           // driest low basins
            return Biome.DesertDunes;
        }

        /// <summary>
        /// Rare, coherent regions of the fictional biomes: a low-frequency field picks a few
        /// patches of lowland (several percent of land); a second coarse field decides which kind each
        /// patch is. Ember wastes get a lava core.
        /// </summary>
        static Biome ApplyAnomaly(in WorldGenParams p, long wx, long wy, int minDim, Biome b)
        {
            if (Biomes.IsWater(b) || b == Biome.Beach || b == Biome.Mountain || b == Biome.Snow ||
                b == Biome.Glacier || b == Biome.RockyHighland || b == Biome.SaltFlats)
                return b;
            int period = Clamp(minDim / 7, 12, 50);
            int a = FixedNoise.Fbm(p.AnomalySeed, wx, wy, period, 2);              // [-One, One]
            int threshold = One * 36 / 100;                                          // rare: a few small patches per map
            if (a < threshold) return b;
            int kind = FixedNoise.Sample(p.AnomalySeed ^ 0x1F1F1F1F1F1F1F1FUL, wx / (period * 2), wy / (period * 2));
            // Sample is ~[-0.7, 0.7]; split into four bands. The fire family is ringed: ember wastes, ash, volcanic rock, lava core.
            if (kind < -One * 18 / 100) return Biome.CrystalCaves;
            if (kind < 0) return Biome.FungalGrove;
            if (kind < One * 18 / 100) return Biome.Glimmerwood;
            if (a > One * 47 / 100) return Biome.Lava;
            if (a > One * 43 / 100) return Biome.Volcanic;
            if (a > One * 40 / 100) return Biome.AshWaste;
            return Biome.EmberWastes;
        }

        /// <summary>
        /// Clumped decoration scatter (pass 4): each biome has a base density per decoration;
        /// a smooth "grove" field (period ~7 tiles) modulates it, so forests have clearings and
        /// grassland has small groves instead of uniform noise.
        /// </summary>
        public static Decoration ScatterDecoration(in WorldGenParams p, int x, int y, long px, long py, Biome b, byte temperature)
        {
            ulong h = FixedNoise.LatticeHash(p.DecorationSeed, x, y);
            int roll = (int)(h % 1000);                      // 0..999
            int pick = (int)((h >> 20) % 100);               // variant choice 0..99
            int grove = FixedNoise.Sample(p.DecorationSeed ^ 0x7E7E7E7E7E7E7E7EUL, px / 7, py / 7); // ~[-0.7,0.7]
            int clump = 100 + grove * 90 / One;              // ~37..163 percent

            switch (b)
            {
                case Biome.Meadow:
                    if (roll < (31 * clump / 100)) return pick < 80 ? Decoration.OakTree : Decoration.BirchTree;
                    if (roll < (31 * clump / 100) + 20) return pick < 60 ? Decoration.Bush : Decoration.BerryBush;
                    if (roll < (31 * clump / 100) + 55) return pick < 55 ? Decoration.Flowers : Decoration.TallGrass;
                    if (roll < (31 * clump / 100) + 62) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Forest:
                    if (roll < (252 * clump / 100)) return pick < 85 ? Decoration.OakTree : Decoration.BirchTree;
                    if (roll < (252 * clump / 100) + 40) return pick < 70 ? Decoration.Bush : Decoration.BerryBush;
                    if (roll < (252 * clump / 100) + 60) return pick < 50 ? Decoration.Mushroom : Decoration.Fern;
                    return Decoration.None;
                case Biome.BirchForest:
                    if (roll < (216 * clump / 100)) return pick < 80 ? Decoration.BirchTree : Decoration.PineTree;
                    if (roll < (216 * clump / 100) + 45) return pick < 50 ? Decoration.Flowers : Decoration.TallGrass;
                    return Decoration.None;
                case Biome.PineTaiga:
                    if (roll < (252 * clump / 100)) return temperature < 50 && pick < 45 ? Decoration.SnowPine : Decoration.PineTree;
                    if (roll < (252 * clump / 100) + 15) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Tundra:
                    if (roll < 12) return Decoration.SnowPine;
                    if (roll < 27) return Decoration.Rock;
                    if (roll < 37) return Decoration.TallGrass;
                    return Decoration.None;
                case Biome.Snow:
                    if (roll < 9) return Decoration.IceRock;
                    if (roll < 13) return Decoration.SnowPine;
                    return Decoration.None;
                case Biome.Jungle:
                    if (roll < (292 * clump / 100)) return Decoration.JungleTree;          // palms only on hot beaches and deserts
                    if (roll < (292 * clump / 100) + 60) return pick < 50 ? Decoration.Fern : Decoration.Bush;
                    if (roll < (292 * clump / 100) + 80) return Decoration.Flowers;
                    return Decoration.None;
                case Biome.Savanna:
                    if (roll < (20 * clump / 100)) return Decoration.AcaciaTree;
                    if (roll < (20 * clump / 100) + 60) return Decoration.TallGrass;
                    if (roll < (20 * clump / 100) + 72) return Decoration.Bush;
                    if (roll < (20 * clump / 100) + 77) return Decoration.Rock;
                    return Decoration.None;
                case Biome.DesertDunes:
                    if (roll < 3) return Decoration.PalmTree;                         // a rare oasis palm
                    if (roll < 11) return Decoration.Cactus;
                    if (roll < 18) return Decoration.Rock;
                    if (roll < 20) return Decoration.DeadTree;
                    return Decoration.None;
                case Biome.Swamp:
                    if (roll < (126 * clump / 100)) return Decoration.SwampTree;
                    if (roll < (126 * clump / 100) + 85) return Decoration.Reeds;
                    if (roll < (126 * clump / 100) + 105) return Decoration.Mushroom;
                    return Decoration.None;
                case Biome.Beach:
                    if (temperature > 170 && roll < 15) return Decoration.PalmTree;
                    if (roll < 22) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Mountain:
                    if (roll < 35) return pick < 60 ? Decoration.Rock : Decoration.Boulder;
                    if (roll < 42) return Decoration.PineTree;
                    return Decoration.None;
                case Biome.CrystalCaves:
                    if (roll < (76 * clump / 100)) return Decoration.Crystal;
                    if (roll < (76 * clump / 100) + 20) return Decoration.Rock;
                    return Decoration.None;
                case Biome.FungalGrove:
                    if (roll < (135 * clump / 100)) return Decoration.GiantMushroom;
                    if (roll < (135 * clump / 100) + 80) return Decoration.Mushroom;
                    return Decoration.None;
                case Biome.EmberWastes:
                    if (roll < 40) return Decoration.EmberRock;
                    if (roll < 60) return Decoration.CharredStump;
                    if (roll < 70) return Decoration.EmberVent;
                    return Decoration.None;
                case Biome.Glimmerwood:
                    if (roll < (216 * clump / 100)) return Decoration.GlowTree;
                    if (roll < (216 * clump / 100) + 60) return Decoration.Flowers;
                    return Decoration.None;
                case Biome.FlowerField:
                    if (roll < 130) return pick < 70 ? Decoration.Flowers : Decoration.TallGrass;
                    if (roll < 150) return pick < 50 ? Decoration.Bush : Decoration.BerryBush;
                    if (roll < (13 * clump / 100) + 150) return Decoration.BirchTree;
                    return Decoration.None;
                case Biome.Steppe:
                    if (roll < 75) return Decoration.TallGrass;
                    if (roll < 87) return Decoration.Rock;
                    if (roll < 92) return Decoration.Bush;
                    return Decoration.None;
                case Biome.Badlands:
                    if (roll < 30) return pick < 55 ? Decoration.Rock : Decoration.Boulder;
                    if (roll < 37) return Decoration.DeadTree;
                    if (roll < 42) return Decoration.Cactus;
                    return Decoration.None;
                case Biome.SaltFlats:
                    if (roll < 6) return Decoration.Rock;
                    return Decoration.None;
                case Biome.Glacier:
                    if (roll < 10) return Decoration.IceRock;
                    return Decoration.None;
                case Biome.RockyHighland:
                    if (roll < 45) return pick < 55 ? Decoration.Rock : Decoration.Boulder;
                    if (roll < 57) return Decoration.PineTree;
                    if (roll < 67) return Decoration.TallGrass;
                    return Decoration.None;
                case Biome.Volcanic:
                    if (roll < 45) return pick < 60 ? Decoration.LavaRock : Decoration.EmberRock;
                    if (roll < 50) return Decoration.EmberVent;
                    return Decoration.None;
                case Biome.AshWaste:
                    if (roll < 30) return Decoration.CharredStump;
                    if (roll < 45) return Decoration.DeadTree;
                    return Decoration.None;
                case Biome.CoralShallows:
                    if (roll < (99 * clump / 100)) return Decoration.Coral;
                    return Decoration.None;
                default:
                    return Decoration.None; // water, lava, farmland, irradiated waste
            }
        }

        /// <summary>Resources follow the decoration (trees: wood, rocks: stone) and the biome (ore).</summary>
        public static byte Resources(in WorldGenParams p, int x, int y, Biome biome, Decoration deco)
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
                case Biome.CrystalCaves:
                    if (deco == Decoration.Crystal) f |= ResourceFlags.Gems;
                    break;
                case Biome.EmberWastes:
                case Biome.Volcanic:
                    if (roll < 300) f |= ResourceFlags.Gold;
                    break;
                case Biome.RockyHighland:
                case Biome.Badlands:
                    f |= ResourceFlags.Stone;
                    if (roll < 120) f |= ResourceFlags.Gold;
                    break;
                case Biome.Glacier:
                    if (roll < 40) f |= ResourceFlags.Gems;
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
        public static StableHash64 Begin(ulong seed, int width, int height) =>
            Begin(seed, width, height, WorldGenSettings.Default);

        /// <summary>Settings are hashed only when non-default, so default worlds keep their golden hashes.</summary>
        public static StableHash64 Begin(ulong seed, int width, int height, WorldGenSettings s)
        {
            var h = StableHash64.Create();
            h.Add(seed);
            h.Add(width);
            h.Add(height);
            if (!s.IsDefault)
            {
                h.Add(unchecked((byte)s.LandBias)); h.Add(s.Mountains);
                h.Add(unchecked((byte)s.Temperature)); h.Add(unchecked((byte)s.Moisture)); h.Add(s.Blank);
            }
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
