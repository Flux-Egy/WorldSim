using System.Collections.Generic;
using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Core.Life;

namespace WorldSim.Tests
{
    /// <summary>A new world starts with life: deterministic, on suitable land or water, peoples far apart.</summary>
    public class StartingLifeTests
    {
        static TileData[] World(ulong seed, int size)
        {
            var p = WorldGenParams.Create(new WorldSeed(seed), size, size);
            var tiles = new TileData[size * size];
            WorldGenerator.Generate(p, tiles);
            return tiles;
        }

        [Test]
        public void Plan_IsDeterministic_HasEveryPeopleAndAnimals_OnTheRightGround()
        {
            const int N = 256;
            var tiles = World(0x3660A6F1, N);
            var a = StartingLife.Plan(tiles, N, N, 0x3660A6F1);
            var b = StartingLife.Plan(tiles, N, N, 0x3660A6F1);
            Assert.AreEqual(a.Count, b.Count);
            for (int i = 0; i < a.Count; i++) { Assert.AreEqual(a[i].X, b[i].X); Assert.AreEqual(a[i].Y, b[i].Y); Assert.AreEqual(a[i].Species, b[i].Species); }

            var count = new Dictionary<SpeciesId, int>();
            foreach (var s in a)
            {
                count[s.Species] = count.TryGetValue(s.Species, out int c) ? c + 1 : 1;
                Assert.That(s.X, Is.InRange(0, N - 1)); Assert.That(s.Y, Is.InRange(0, N - 1));
                var t = tiles[s.Y * N + s.X];
                if (s.Species == SpeciesId.Fish) Assert.IsTrue(t.IsWater, "fish start in water");
                else if (s.Species != SpeciesId.Bird) Assert.IsFalse(t.IsWater && s.Species != SpeciesId.Human && s.Species != SpeciesId.Elf && s.Species != SpeciesId.Orc && s.Species != SpeciesId.Dwarf, $"{s.Species} on land");
            }
            foreach (var p in new[] { SpeciesId.Human, SpeciesId.Elf, SpeciesId.Orc, SpeciesId.Dwarf })
                Assert.AreEqual(StartingLife.PeopleBand, count[p], p.ToString());
            Assert.Greater(count[SpeciesId.Sheep] + count[SpeciesId.Cow] + count[SpeciesId.Rabbit] + count[SpeciesId.Deer], 20, "herbivores");
            Assert.Greater(count[SpeciesId.Fish], 10, "fish");
        }

        [Test]
        public void PeopleBands_AreFarApart()
        {
            const int N = 256;
            var tiles = World(0x5EED, N);
            var plan = StartingLife.Plan(tiles, N, N, 0x5EED);
            var firsts = new List<StartingLife.Spawn>();
            SpeciesId last = 0;
            foreach (var s in plan) if ((int)s.Species <= 4 && s.Species != last) { firsts.Add(s); last = s.Species; }
            for (int i = 0; i < firsts.Count; i++)
                for (int j = i + 1; j < firsts.Count; j++)
                {
                    int dx = firsts[i].X - firsts[j].X, dy = firsts[i].Y - firsts[j].Y;
                    Assert.GreaterOrEqual(dx * dx + dy * dy, (StartingLife.MinBandDistance - 2) * (StartingLife.MinBandDistance - 2));
                }
        }
    }
}
