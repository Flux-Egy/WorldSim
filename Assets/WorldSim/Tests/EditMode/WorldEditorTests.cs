using NUnit.Framework;
using WorldSim.Core;

namespace WorldSim.Tests
{
    /// <summary>Beta B2 terrain brushes: effects, consistency and determinism.</summary>
    public class WorldEditorTests
    {
        struct Grid : ITileGrid
        {
            public TileData[] A;
            public TileData Get(int i) => A[i];
            public void Set(int i, TileData t) => A[i] = t;
        }

        const int N = 64;

        static (Grid grid, WorldGenParams p) World(ulong seed = 3)
        {
            var p = WorldGenParams.Create(new WorldSeed(seed), N, N);
            var tiles = new TileData[N * N];
            WorldGenerator.Generate(p, tiles);
            return (new Grid { A = tiles }, p);
        }

        static TerrainEdit Edit(TerrainTool tool, int x, int y, int r, Biome b = Biome.Meadow) =>
            new TerrainEdit { Tool = tool, X = x, Y = y, Radius = r, Biome = b };

        [Test]
        public void PaintWater_MakesConsistentWater()
        {
            var (g, p) = World();
            WorldEditor.Apply(ref g, p, Edit(TerrainTool.PaintBiome, 32, 32, 3, Biome.DeepWater));
            TileData t = g.Get(32 * N + 32);
            Assert.AreEqual(Biome.DeepWater, t.Biome);
            Assert.AreEqual(0, t.DecorationId);
            Assert.AreEqual(0, t.ResourceFlags);
            Assert.Less(t.Height, WorldGenerator.SeaLevel);
        }

        [Test]
        public void RaiseRepeatedly_ClimbsToMountainThenSnow()
        {
            var (g, p) = World();
            WorldEditor.Apply(ref g, p, Edit(TerrainTool.PaintBiome, 20, 20, 0, Biome.Meadow));
            bool sawMountain = false;
            for (int i = 0; i < 40; i++)
            {
                WorldEditor.Apply(ref g, p, Edit(TerrainTool.Raise, 20, 20, 0));
                if (g.Get(20 * N + 20).Biome == Biome.Mountain) sawMountain = true;
            }
            Assert.IsTrue(sawMountain, "passes through mountain");
            Assert.AreEqual(Biome.Snow, g.Get(20 * N + 20).Biome, "ends as a snow peak");
        }

        [Test]
        public void LowerRepeatedly_SinksIntoWater()
        {
            var (g, p) = World();
            WorldEditor.Apply(ref g, p, Edit(TerrainTool.PaintBiome, 40, 40, 0, Biome.Meadow));
            for (int i = 0; i < 20; i++) WorldEditor.Apply(ref g, p, Edit(TerrainTool.Lower, 40, 40, 0));
            Assert.IsTrue(g.Get(40 * N + 40).IsWater);
        }

        [Test]
        public void PlantThenClear_TogglesTreesAndWood()
        {
            var (g, p) = World();
            WorldEditor.Apply(ref g, p, Edit(TerrainTool.PaintBiome, 10, 10, 2, Biome.Meadow));
            WorldEditor.Apply(ref g, p, Edit(TerrainTool.PlantTrees, 10, 10, 2));
            TileData t = g.Get(10 * N + 10);
            Assert.IsTrue(TileData.IsTree(t.Decoration));
            Assert.IsTrue(t.Has(ResourceFlags.Wood));
            WorldEditor.Apply(ref g, p, Edit(TerrainTool.ClearDecorations, 10, 10, 2));
            t = g.Get(10 * N + 10);
            Assert.AreEqual(0, t.DecorationId);
            Assert.IsFalse(t.Has(ResourceFlags.Wood));
        }

        [Test]
        public void TouchedRect_IsClippedToMap_AndEmptyWhenNothingChanges()
        {
            var (g, p) = World();
            TileRect r = WorldEditor.Apply(ref g, p, Edit(TerrainTool.PaintBiome, 0, 0, 5, Biome.Lava));
            Assert.IsFalse(r.IsEmpty);
            Assert.AreEqual(0, r.XMin); Assert.AreEqual(0, r.YMin);
            Assert.LessOrEqual(r.XMax, 5); Assert.LessOrEqual(r.YMax, 5);
            TileRect again = WorldEditor.Apply(ref g, p, Edit(TerrainTool.PaintBiome, 0, 0, 5, Biome.Lava));
            Assert.IsTrue(again.IsEmpty, "painting the same biome again changes nothing");
        }

        [Test]
        public void SameEdits_SameWorld()
        {
            ulong Run()
            {
                var (g, p) = World(11);
                for (int i = 0; i < 30; i++)
                {
                    var tool = (TerrainTool)(1 + i % 6);
                    WorldEditor.Apply(ref g, p, Edit(tool, (i * 7) % N, (i * 13) % N, i % 5, (Biome)(i % 19)));
                }
                return WorldHash.Compute(11, N, N, g.A);
            }
            Assert.AreEqual(Run(), Run());
        }
    }
}
