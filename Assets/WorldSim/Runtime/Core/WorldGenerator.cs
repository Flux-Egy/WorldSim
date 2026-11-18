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
    ///   2. Biome assignment: a small decision tree over (height, moisture, temperature).
    ///   3. Edge refinement: a second noise layer warps the sampling position and jitters the
    ///      biome thresholds, so borders are irregular instead of straight contour lines.
    ///   4. Detail: high-frequency hashing scatters lone trees, rocks and ore (resourceFlags).
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
            byte moisture = ToByte(FixedNoise.Fbm(p.MoistureSeed, wx, wy, Clamp(minDim / 4, 12, MaxClimatePeriod), 4));

            // Temperature: warm equator (middle row), cold poles, colder with altitude.
            long latitude = One - Abs((long)y * 2 * One / Max(1, p.Height - 1) - One); // [0, One]
            long tNoise = FixedNoise.Fbm(p.TemperatureSeed, wx, wy, Clamp(minDim / 3, 12, MaxClimatePeriod), 3);
            long altitudeChill = height > SeaLevel ? (long)(height - SeaLevel) * One / (255 - SeaLevel) : 0;
            long t = (latitude * 2 - One) * 80 / 100 + tNoise * 35 / 100 - altitudeChill * 45 / 100;
            byte temperature = ToByte(t);

            // ---- Pass 3b (edge refinement): smooth small-scale threshold jitter (period ~3 tiles).
            // Smooth rather than per-tile random, so borders get wiggly instead of speckled.
            int jitter = FixedNoise.Sample(p.EdgeRefineSeed ^ 0x3C3C3C3C3C3C3C3CUL, px / 3, py / 3) * 5 / One; // -5..+5

            // ---- Pass 2: biome ----
            Biome biome = Classify(height, moisture, temperature, jitter);

            // ---- Pass 4: detail scatter ----
            byte resources = ScatterResources(p, x, y, biome);

            return new TileData
            {
                BiomeId = (byte)biome,
                Height = height,
                Moisture = moisture,
                Temperature = temperature,
                ResourceFlags = resources,
            };
        }

        /// <summary>Biome decision tree (pass 2). Public so the table can be unit-tested.</summary>
        public static Biome Classify(byte height, byte moisture, byte temperature, int jitter)
        {
            int h = height + jitter;
            if (h < DeepWaterBelow) return Biome.DeepWater;
            if (h < SeaLevel) return Biome.ShallowWater;
            if (h < BeachBelow) return temperature < 40 ? Biome.Snow : Biome.Sand;
            if (h >= SnowPeakFrom) return Biome.Snow;
            if (h >= MountainFrom) return temperature < 48 ? Biome.Snow : Biome.Mountain;

            // Lowlands
            if (temperature < 34) return Biome.Snow;                         // tundra
            if (temperature > 205 && moisture < 80) return Biome.Sand;       // desert
            if (moisture + jitter * 2 > 134) return Biome.Forest;
            return Biome.Grass;
        }

        /// <summary>Pass 4: per-tile resource and decoration flags from an independent hash.</summary>
        static byte ScatterResources(in WorldGenParams p, int x, int y, Biome biome)
        {
            ulong r = FixedNoise.LatticeHash(p.ResourceSeed, x, y);
            ulong d = FixedNoise.LatticeHash(p.DetailSeed, x, y);
            uint roll = (uint)(r % 10000);   // 0.01% resolution
            uint detail = (uint)(d % 10000);

            ResourceFlags f = ResourceFlags.None;
            switch (biome)
            {
                case Biome.Forest:
                    f |= ResourceFlags.Wood;
                    break;
                case Biome.Grass:
                    if (detail < 400) f |= ResourceFlags.Wood;    // 4% lone trees
                    else if (detail < 550) f |= ResourceFlags.Stone; // 1.5% rocks
                    break;
                case Biome.Sand:
                    if (detail < 120) f |= ResourceFlags.Stone;
                    break;
                case Biome.Mountain:
                    f |= ResourceFlags.Stone;
                    if (roll < 250) f |= ResourceFlags.Gold;       // 2.5%
                    else if (roll < 330) f |= ResourceFlags.Gems;  // 0.8%
                    break;
                case Biome.Snow:
                    if (roll < 60) f |= ResourceFlags.Gems;        // 0.6%
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
    /// World-state hash (§4.3 acceptance, §14.1). FNV-1a over a header (seed, size) and the five
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
        }

        public static ulong Compute(ulong seed, int width, int height, TileData[] tiles)
        {
            var h = Begin(seed, width, height);
            for (int i = 0; i < tiles.Length; i++) AddTile(ref h, tiles[i]);
            return h.Value;
        }
    }
}
