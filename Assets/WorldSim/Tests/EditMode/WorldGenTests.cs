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

        // Regenerated 2026-11-18 for Beta B1 (19 biomes, decorations, stretched moisture).
        [TestCase(0x5EEDUL, 0xAD06CD8E776A783CUL)]
        [TestCase(0xC0FFEEUL, 0xA5E2D7CA353B7D8EUL)]
        [TestCase(0x1UL, 0x8E42B86FB7CE7364UL)]
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
                Assert.That((double)counts[b] / tiles.Length, Is.GreaterThan(0.005), $"biome {(Biome)b} missing");
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
                if (TileData.IsRock(d) || t.Biome == Biome.Mountain) Assert.IsTrue(t.Has(ResourceFlags.Stone));
                if (t.Has(ResourceFlags.Gold)) Assert.That(t.Biome, Is.EqualTo(Biome.Mountain).Or.EqualTo(Biome.EmberWastes));
                if (t.IsWater || t.Biome == Biome.Lava) { Assert.AreEqual(0, t.ResourceFlags); Assert.AreEqual(0, t.DecorationId); }
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
            Assert.AreEqual(Biome.Sand, WorldGenerator.Classify(115, 128, 128, 0));
            Assert.AreEqual(Biome.Grass, WorldGenerator.Classify(150, 60, 128, 0));
            Assert.AreEqual(Biome.Forest, WorldGenerator.Classify(150, 200, 128, 0));
            Assert.AreEqual(Biome.Swamp, WorldGenerator.Classify(130, 200, 128, 0));
            Assert.AreEqual(Biome.Mountain, WorldGenerator.Classify(210, 128, 128, 0));
            Assert.AreEqual(Biome.Snow, WorldGenerator.Classify(250, 128, 128, 0));   // peak
            Assert.AreEqual(Biome.Snow, WorldGenerator.Classify(150, 128, 10, 0));    // polar
            Assert.AreEqual(Biome.Tundra, WorldGenerator.Classify(150, 60, 50, 0));
            Assert.AreEqual(Biome.Taiga, WorldGenerator.Classify(150, 200, 50, 0));
            Assert.AreEqual(Biome.BirchForest, WorldGenerator.Classify(150, 130, 90, 0));
            Assert.AreEqual(Biome.Desert, WorldGenerator.Classify(150, 40, 230, 0));
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
