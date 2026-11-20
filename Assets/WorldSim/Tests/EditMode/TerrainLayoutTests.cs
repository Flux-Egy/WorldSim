using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Render.Terrain;

namespace WorldSim.Tests
{
    /// <summary>The new terrain layout: terraces, water depth rings, crisp sub-cell borders.</summary>
    public class TerrainLayoutTests
    {
        static TileData T(Biome b, byte h) => new TileData { BiomeId = (byte)b, Height = h };

        [Test]
        public void Levels_FollowHeight_WaterAndBeachAtTheSurface_SnowOnTop()
        {
            Assert.AreEqual(2, TerrainLayout.LevelOf(T(Biome.DeepWater, 40)));
            Assert.AreEqual(2, TerrainLayout.LevelOf(T(Biome.CoralShallows, 108)));
            Assert.AreEqual(3, TerrainLayout.LevelOf(T(Biome.Beach, 116)));
            Assert.AreEqual(4, TerrainLayout.LevelOf(T(Biome.Meadow, 130)));
            Assert.AreEqual(5, TerrainLayout.LevelOf(T(Biome.Forest, 170)));
            Assert.AreEqual(7, TerrainLayout.LevelOf(T(Biome.RockyHighland, 195)));
            Assert.AreEqual(9, TerrainLayout.LevelOf(T(Biome.Mountain, 210)));
            Assert.AreEqual(11, TerrainLayout.LevelOf(T(Biome.Mountain, 235)));
            Assert.AreEqual(TerrainLayout.TopLevel, TerrainLayout.LevelOf(T(Biome.Snow, 250)));
            Assert.AreEqual(0, TerrainLayout.Lift(2));
            Assert.AreEqual(0, TerrainLayout.Lift(3));
            Assert.AreEqual(TerrainLayout.LiftPerLevel, TerrainLayout.Lift(4));
            Assert.AreEqual("earth", TerrainLayout.CliffMaterial(5));
            Assert.AreEqual("stone", TerrainLayout.CliffMaterial(10));
            Assert.AreEqual("snow", TerrainLayout.CliffMaterial(TerrainLayout.TopLevel));
        }

        [Test]
        public void WaterBands_AreRingsAroundLand()
        {
            const int N = 20;
            var tiles = new TileData[N * N];
            for (int i = 0; i < tiles.Length; i++) tiles[i] = T(Biome.DeepWater, 40);
            tiles[10 * N + 10] = T(Biome.Meadow, 130);
            var lay = new TerrainLayout(tiles, N, N);
            Assert.AreEqual(255, lay.Band[10 * N + 10], "land");
            Assert.AreEqual(2, lay.Band[10 * N + 11], "1 cell: shallows");
            Assert.AreEqual(2, lay.Band[12 * N + 12], "2 cells (diagonal counts 1): shallows");
            Assert.AreEqual(1, lay.Band[10 * N + 14], "4 cells: ocean");
            Assert.AreEqual(0, lay.Band[10 * N + 17], "7 cells: deep");
        }

        [Test]
        public void SubCells_OnlyBorrowFromTheSameTerrace_AndAreDeterministic()
        {
            const int N = 16;
            var tiles = new TileData[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                    tiles[y * N + x] = x < 8 ? T(Biome.Meadow, 130) : y < 8 ? T(Biome.Forest, 132) : T(Biome.Mountain, 210);
            var a = new TerrainLayout(tiles, N, N);
            var b = new TerrainLayout(tiles, N, N);
            CollectionAssert.AreEqual(a.SubCell, b.SubCell);
            bool borrowed = false;
            for (int s = 0; s < a.SubCell.Length; s++)
            {
                int sx = s % a.SubWidth, sy = s / a.SubWidth;
                int own = (sy / TerrainLayout.SubPerCell) * N + sx / TerrainLayout.SubPerCell;
                Assert.AreEqual(a.Level[own], a.SubLevel[s], "a sub-cell keeps its cell's terrace");
                if (a.SubCell[s] != own)
                {
                    borrowed = true;
                    int ox = own % N, oy = own / N, cx = a.SubCell[s] % N, cy = a.SubCell[s] / N;
                    Assert.LessOrEqual(System.Math.Abs(ox - cx), 1);
                    Assert.LessOrEqual(System.Math.Abs(oy - cy), 1);
                }
            }
            Assert.IsTrue(borrowed, "meadow/forest border (same terrace) gets a pixel-stair wiggle");
        }
    }
}
