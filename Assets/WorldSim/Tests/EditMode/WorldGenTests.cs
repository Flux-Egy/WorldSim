using WorldSim.Core;
using NUnit.Framework;

namespace WorldSim.Tests
{
    /// <summary>
    /// Stage 2 acceptance (§4.3, §19): same seed gives an identical world hash on every run and
    /// every platform. The golden hashes were produced on ARM64 (.NET 8, 2026-11-18) and are
    /// re-checked by CI on x64. If generation changes on purpose, regenerate them with
    /// Tools/WorldPreview and say so in the commit message (it changes every world).
    /// </summary>
    public class WorldGenTests
    {
        const int Size = 256;

        static TileData[] Generate(ulong seed, int size = Size)
        {
            var p = WorldGenParams.Create(new WorldSeed(seed), size, size);
            var tiles = new TileData[size * size];
            WorldGenerator.Generate(p, tiles);
            return tiles;
        }

        // Regenerated 2026-11-21 (rebuild, owner-approved): pack biomes, larger coherent climate regions, snow only on
        // peaks, rarer/smaller anomaly patches, about half the decorations, palms only on hot beaches/deserts; 2026-11-22: mountains <= 15 % of land.
        [TestCase(0x5EEDUL, 0xBFA0A28272C01496UL)]
        [TestCase(0xC0FFEEUL, 0x5E78FFCCF27D2491UL)]
        [TestCase(0x1UL, 0xED2630C383B73C8BUL)]
        public void GoldenHash_IsStableAcrossPlatforms(ulong seed, ulong expected)
        {
            ulong hash = WorldHash.Compute(seed, Size, Size, Generate(seed));
            Assert.AreEqual(expected, hash, $"world hash for seed 0x{seed:X} changed: 0x{hash:X16}");
        }

        [Test]
        public void SameSeed_TwoRuns_IdenticalHash()
        {
            ulong a = WorldHash.Compute(42, Size, Size, Generate(42));
            ulong b = WorldHash.Compute(42, Size, Size, Generate(42));
            Assert.AreEqual(a, b);
        }

        [Test]
        public void DifferentSeeds_DifferentWorlds()
        {
            Assert.AreNotEqual(WorldHash.Compute(1, Size, Size, Generate(1)),
                               WorldHash.Compute(2, Size, Size, Generate(2)));
        }

        [Test]
        public void TileOrder_DoesNotMatter()
        {
            // Parallel jobs generate tiles in arbitrary order; each tile must depend only on (x, y).
            var p = WorldGenParams.Create(new WorldSeed(7), 64, 64);
            var forward = new TileData[64 * 64];
            WorldGenerator.Generate(p, forward);
            for (int i = forward.Length - 1; i >= 0; i--)
            {
                var t = WorldGenerator.GenerateTile(p, i % 64, i / 64);
                Assert.AreEqual(forward[i].BiomeId, t.BiomeId);
                Assert.AreEqual(forward[i].Height, t.Height);
                Assert.AreEqual(forward[i].Moisture, t.Moisture);
                Assert.AreEqual(forward[i].Temperature, t.Temperature);
                Assert.AreEqual(forward[i].ResourceFlags, t.ResourceFlags);
                Assert.AreEqual(forward[i].DecorationId, t.DecorationId);
            }
        }

        [Test]
        public void Distribution_IsPlausible()
        {
            var tiles = Generate(0x5EED);
            var counts = new int[256];
            int water = 0;
            foreach (var t in tiles) { counts[t.BiomeId]++; if (t.IsWater) water++; }
            double waterShare = (double)water / tiles.Length;
            Assert.That(waterShare, Is.InRange(0.25, 0.70), "water share");
            for (int b = (int)Biome.DeepWater; b <= (int)Biome.Snow; b++)
                // Snow only caps the (now rarer, <= 15 % of land) mountain peaks: present, but small.
                Assert.That((double)counts[b] / tiles.Length, Is.GreaterThan(b == (int)Biome.Snow ? 0.001 : 0.005), $"biome {(Biome)b} missing");
            int distinct = 0;
            foreach (int c in counts) if (c > 0) distinct++;
            Assert.That(distinct, Is.GreaterThanOrEqualTo(12), "biome variety");
        }

        [Test]
        public void MapBorder_IsOcean()
        {
            var tiles = Generate(0xC0FFEE);
            for (int i = 0; i < Size; i++)
            {
                Assert.IsTrue(tiles[i].IsWater, "bottom row");
                Assert.IsTrue(tiles[(Size - 1) * Size + i].IsWater, "top row");
                Assert.IsTrue(tiles[i * Size].IsWater, "left column");
                Assert.IsTrue(tiles[i * Size + Size - 1].IsWater, "right column");
            }
        }

        [Test]
        public void Resources_MatchDecorationsAndBiomes()
        {
            int decorated = 0;
            foreach (var t in Generate(0x1))
            {
                Decoration d = t.Decoration;
                Assert.AreEqual(TileData.IsTree(d), t.Has(ResourceFlags.Wood), "wood iff tree");
                if (TileData.IsRock(d) || t.Biome == Biome.Mountain || t.Biome == Biome.RockyHighland || t.Biome == Biome.Badlands) Assert.IsTrue(t.Has(ResourceFlags.Stone));
                if (t.Has(ResourceFlags.Gold)) Assert.That(t.Biome, Is.EqualTo(Biome.Mountain).Or.EqualTo(Biome.EmberWastes).Or.EqualTo(Biome.Volcanic)
                    .Or.EqualTo(Biome.RockyHighland).Or.EqualTo(Biome.Badlands));
                if (t.IsWater || t.Biome == Biome.Lava) Assert.AreEqual(0, t.ResourceFlags);
                if (t.IsWater && t.Biome != Biome.CoralShallows || t.Biome == Biome.Lava) Assert.AreEqual(0, t.DecorationId);
                if (t.Biome == Biome.CoralShallows) Assert.That(d, Is.EqualTo(Decoration.None).Or.EqualTo(Decoration.Coral));
                Assert.Less(t.DecorationId, (byte)Decoration.Count);
                if (d != Decoration.None) decorated++;
            }
            Assert.Greater(decorated, 256 * 256 / 20, "decorations present");
        }

        [Test]
        public void Classify_ClimateTable()
        {
            Assert.AreEqual(Biome.DeepWater, WorldGenerator.Classify(10, 128, 128, 0));
            Assert.AreEqual(Biome.ShallowWater, WorldGenerator.Classify(100, 128, 128, 0));
            Assert.AreEqual(Biome.Beach, WorldGenerator.Classify(115, 128, 128, 0));
            Assert.AreEqual(Biome.Meadow, WorldGenerator.Classify(150, 100, 128, 0));
            Assert.AreEqual(Biome.Steppe, WorldGenerator.Classify(150, 60, 128, 0));
            Assert.AreEqual(Biome.FlowerField, WorldGenerator.Classify(150, 125, 128, 0));
            Assert.AreEqual(Biome.Forest, WorldGenerator.Classify(150, 200, 128, 0));
            Assert.AreEqual(Biome.Swamp, WorldGenerator.Classify(130, 200, 128, 0));
            Assert.AreEqual(Biome.Mountain, WorldGenerator.Classify(210, 128, 128, 0));
            Assert.AreEqual(Biome.Snow, WorldGenerator.Classify(250, 128, 128, 0));   // peak
            Assert.AreEqual(Biome.Glacier, WorldGenerator.Classify(150, 128, 10, 0)); // polar ice sheet
            Assert.AreEqual(Biome.Tundra, WorldGenerator.Classify(150, 100, 28, 0));  // no lowland snow: snow is for peaks
            Assert.AreEqual(Biome.Tundra, WorldGenerator.Classify(150, 60, 50, 0));
            Assert.AreEqual(Biome.PineTaiga, WorldGenerator.Classify(150, 200, 50, 0));
            Assert.AreEqual(Biome.BirchForest, WorldGenerator.Classify(150, 130, 90, 0));
            Assert.AreEqual(Biome.DesertDunes, WorldGenerator.Classify(140, 70, 230, 0));
            Assert.AreEqual(Biome.SaltFlats, WorldGenerator.Classify(125, 30, 230, 0));
            Assert.AreEqual(Biome.Badlands, WorldGenerator.Classify(165, 30, 230, 0));
            Assert.AreEqual(Biome.CoralShallows, WorldGenerator.Classify(108, 128, 200, 0));
            Assert.AreEqual(Biome.ShallowWater, WorldGenerator.Classify(108, 128, 120, 0));
            Assert.AreEqual(Biome.Snow, WorldGenerator.Classify(245, 128, 60, 0));     // every peak is snow-capped
            Assert.AreEqual(Biome.Mountain, WorldGenerator.Classify(220, 128, 20, 0)); // cold mountains stay rock below the cap
            Assert.AreEqual(Biome.Beach, WorldGenerator.Classify(115, 128, 20, 0));    // cold coasts still have a beach
            Assert.AreEqual(Biome.RockyHighland, WorldGenerator.Classify(195, 90, 128, 0));
            Assert.AreEqual(Biome.Forest, WorldGenerator.Classify(195, 140, 128, 0)); // wet foothills stay green
            Assert.AreEqual(Biome.Savanna, WorldGenerator.Classify(150, 120, 230, 0));
            Assert.AreEqual(Biome.Jungle, WorldGenerator.Classify(150, 200, 230, 0));
        }

        [Test]
        public void Noise_FadeEndpoints_And_Range()
        {
            Assert.AreEqual(0, FixedNoise.Fade(0));
            Assert.AreEqual(FixedNoise.One, FixedNoise.Fade(FixedNoise.One));
            var rng = new Pcg32(3, 5);
            for (int i = 0; i < 20000; i++)
            {
                long x = rng.NextInt(-1 << 24, 1 << 24), y = rng.NextInt(-1 << 24, 1 << 24);
                int n = FixedNoise.Sample(99, x, y);
                Assert.That(n, Is.InRange(-FixedNoise.One, FixedNoise.One));
            }
        }

        [Test]
        public void Noise_IsZeroOnLatticePoints()
        {
            // Gradient noise property: at integer lattice points every gradient is dotted with 0.
            for (int i = -5; i <= 5; i++)
                Assert.AreEqual(0, FixedNoise.Sample(1234, (long)i << FixedNoise.FracBits, (long)(i * 3) << FixedNoise.FracBits));
        }
    }
}

namespace WorldSim.Tests
{
    using NUnit.Framework;
    using WorldSim.Core;

    /// <summary>Beta B2 generation settings and blank worlds.</summary>
    public class WorldGenSettingsTests
    {
        const int N = 128;

        static TileData[] Gen(WorldGenSettings s, ulong seed = 0x5EED)
        {
            var p = WorldGenParams.Create(new WorldSeed(seed), N, N, s);
            var t = new TileData[N * N];
            WorldGenerator.Generate(p, t);
            return t;
        }

        static double WaterShare(TileData[] t) { int w = 0; foreach (var x in t) if (x.IsWater) w++; return (double)w / t.Length; }

        [Test]
        public void EmptyOcean_IsAllWater_FlatLand_IsMostlyLand()
        {
            Assert.AreEqual(1.0, WaterShare(Gen(new WorldGenSettings { Mountains = 100, Blank = 1 })));
            Assert.Less(WaterShare(Gen(new WorldGenSettings { Mountains = 100, Blank = 2 })), 0.35);
        }

        [Test]
        public void LandBias_MovesTheCoastline()
        {
            double islands = WaterShare(Gen(new WorldGenSettings { Mountains = 100, LandBias = -25 }));
            double normal = WaterShare(Gen(WorldGenSettings.Default));
            double continent = WaterShare(Gen(new WorldGenSettings { Mountains = 100, LandBias = 25 }));
            Assert.Greater(islands, normal);
            Assert.Greater(normal, continent);
        }

        [Test]
        public void IceAge_HasMoreSnow_ThanHotWorld()
        {
            int Snow(TileData[] t) { int n = 0; foreach (var x in t) if (x.Biome == Biome.Snow || x.Biome == Biome.Tundra) n++; return n; }
            Assert.Greater(Snow(Gen(new WorldGenSettings { Mountains = 100, Temperature = -35 })),
                           Snow(Gen(new WorldGenSettings { Mountains = 100, Temperature = 35 })));
        }

        [Test]
        public void Settings_AreHashed_OnlyWhenNotDefault()
        {
            var a = WorldHash.Begin(1, N, N).Value;
            var b = WorldHash.Begin(1, N, N, WorldGenSettings.Default).Value;
            var c = WorldHash.Begin(1, N, N, new WorldGenSettings { Mountains = 150 }).Value;
            Assert.AreEqual(a, b);
            Assert.AreNotEqual(a, c);
        }
    }
}
