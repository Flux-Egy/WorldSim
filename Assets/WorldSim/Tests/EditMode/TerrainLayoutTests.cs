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

        static TerrainLayout Map(int n, System.Func<int, int, TileData> f, out TileData[] tiles)
        {
            tiles = new TileData[n * n];
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++) tiles[y * n + x] = f(x, y);
            return new TerrainLayout(tiles, n, n);
        }

        [Test]
        public void Field_IsDeterministic_AndCellCentresShowTheirOwnCell()
        {
            var lay = Map(16, (x, y) => x < 8 ? T(Biome.Meadow, 130) : y < 8 ? T(Biome.Forest, 132) : T(Biome.DeepWater, 40), out var tiles);
            var a = new TerrainField(tiles, lay);
            var b = new TerrainField(tiles, lay);
            for (int y = 0; y < 16 * 16; y += 3)
                for (int x = 0; x < 16 * 16; x += 3)
                {
                    a.Pick(x, y, out int c1, out int l1);
                    b.Pick(x, y, out int c2, out int l2);
                    Assert.AreEqual(c1, c2); Assert.AreEqual(l1, l2);
                    int own = (y >> 4) * 16 + (x >> 4);
                    int ox = own % 16, oy = own / 16, px = c1 % 16, py = c1 / 16;
                    Assert.LessOrEqual(System.Math.Abs(ox - px), 1, "a pixel only shows a neighbouring cell");
                    Assert.LessOrEqual(System.Math.Abs(oy - py), 1);
                }
            for (int cy = 2; cy < 14; cy++)
                for (int cx = 2; cx < 14; cx++)
                {
                    if ((cx == 7 || cx == 8) || (cy == 7 || cy == 8)) continue;   // skip the border rows
                    a.Pick(cx * 16 + 8, cy * 16 + 8, out int c, out _);
                    Assert.AreEqual(cy * 16 + cx, c, $"centre of cell {cx},{cy}");
                }
        }

        [Test]
        public void Field_RoundsALoneCell_IntoABlobSmallerThanTheCell()
        {
            var lay = Map(9, (x, y) => x == 4 && y == 4 ? T(Biome.Meadow, 130) : T(Biome.DeepWater, 40), out var tiles);
            var f = new TerrainField(tiles, lay);
            int land = 0;
            for (int y = 0; y < 9 * 16; y++)
                for (int x = 0; x < 9 * 16; x++)
                {
                    f.Pick(x, y, out int c, out int l);
                    if (l >= TerrainLayout.WaterLevel) { land++; Assert.AreEqual(4 * 9 + 4, c); }
                }
            Assert.Greater(land, 40, "the island is still there");
            Assert.Less(land, 256, "no square corners: smaller than its 16x16 cell");
        }

        [Test]
        public void SnowTerrace_DrawsAsSnow_AndSmallTerracesMerge()
        {
            var lay = Map(20, (x, y) => x >= 5 && x < 15 && y >= 5 && y < 15 ? (x == 9 && y == 9 ? T(Biome.Mountain, 236) : T(Biome.Snow, 250)) : T(Biome.Mountain, 210), out _);
            Assert.AreEqual(TerrainLayout.TopLevel, lay.Level[9 * 20 + 9], "a rock cell inside the cap joins the cap");
            Assert.AreEqual((byte)Biome.Snow, lay.RenderBiome[9 * 20 + 9], "and is drawn as snow");
            Assert.AreEqual((byte)Biome.Mountain, lay.RenderBiome[2 * 20 + 2]);
        }
    }
}
