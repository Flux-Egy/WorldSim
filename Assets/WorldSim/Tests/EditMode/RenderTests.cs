using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Render;

namespace WorldSim.Tests
{
    public class RenderTests
    {
        struct ArrayTiles : ITileSource { public TileData[] A; public TileData Get(int i) => A[i]; }
        struct ArrayPixels : IPixelTarget { public uint[] A; public uint Get(int i) => A[i]; public void Set(int i, uint c) => A[i] = c; }
        struct ArrayAtlas : IAtlasSource { public uint[] A; public uint Get(int i) => A[i]; }

        [Test]
        public void EverySpriteVariant_HasVisiblePixels()
        {
            uint[] atlas = SpriteLibrary.Build();
            Assert.AreEqual(SpriteLibrary.AtlasLength, atlas.Length);
            // The old procedural library (removed in rebuild phase 3) only draws the original 23 decorations.
            for (int d = 1; d <= (int)Decoration.AcaciaTree; d++)
                for (int v = 0; v < SpriteLibrary.Variants; v++)
                {
                    int opaque = 0, start = SpriteLibrary.CellIndex((Decoration)d, v) * SpriteLibrary.CellPixels;
                    for (int i = 0; i < SpriteLibrary.CellPixels; i++) if (Rgba.A(atlas[start + i]) == 255) opaque++;
                    Assert.GreaterOrEqual(opaque, 4, $"{(Decoration)d} variant {v} is (almost) empty");
                }
        }

        [Test]
        public void Painting_IsDeterministic_AndFillsEveryPixel()
        {
            const int n = 48;
            var p = WorldGenParams.Create(new WorldSeed(9), n, n);
            var tiles = new TileData[n * n];
            WorldGenerator.Generate(p, tiles);
            int ppt = TerrainPainter.PixelsPerTileFor(n, n);
            uint[] a = Paint(tiles, n, ppt), b = Paint(tiles, n, ppt);
            Assert.AreEqual(a, b);
            foreach (uint c in a) Assert.AreEqual(255, Rgba.A(c), "every pixel opaque");
        }

        [Test]
        public void PixelsPerTile_KeepsTextureWithin2048()
        {
            foreach (int size in new[] { 256, 512, 1024 })
                Assert.LessOrEqual(size * TerrainPainter.PixelsPerTileFor(size, size), 2048);
        }

        struct Grid : ITileGrid
        {
            public TileData[] A;
            public TileData Get(int i) => A[i];
            public void Set(int i, TileData t) => A[i] = t;
        }

        [Test]
        public void PartialRepaint_AfterEdits_EqualsFullRepaint()
        {
            const int n = 64;
            var p = WorldGenParams.Create(new WorldSeed(21), n, n);
            var tiles = new TileData[n * n];
            WorldGenerator.Generate(p, tiles);
            int ppt = TerrainPainter.PixelsPerTileFor(n, n);
            uint[] px = Paint(tiles, n, ppt);
            var atlas = new ArrayAtlas { A = SpriteLibrary.Build() };
            var grid = new Grid { A = tiles };
            var edits = new[]
            {
                new TerrainEdit { Tool = TerrainTool.PaintBiome, Biome = Biome.DeepWater, X = 30, Y = 30, Radius = 4 },
                new TerrainEdit { Tool = TerrainTool.PlantTrees, X = 12, Y = 50, Radius = 3 },
                new TerrainEdit { Tool = TerrainTool.Raise, X = 50, Y = 10, Radius = 5 },
                new TerrainEdit { Tool = TerrainTool.PaintBiome, Biome = Biome.Lava, X = 2, Y = 62, Radius = 2 },
            };
            foreach (var e in edits)
            {
                TileRect r = WorldEditor.Apply(ref grid, p, e);
                if (r.IsEmpty) continue;
                var t = new ArrayTiles { A = tiles }; var pix = new ArrayPixels { A = px };
                TerrainPainter.RepaintRows(ref t, ref pix, ref atlas, n, n, ppt, r.YMin, r.YMax);
            }
            Assert.AreEqual(Paint(tiles, n, ppt), px, "partial repaint must match a full repaint pixel for pixel");
        }

        [Test]
        public void Waves_OnlyOverOpenWater_AndFramesDiffer()
        {
            const int n = 64;
            var p = WorldGenParams.Create(new WorldSeed(5), n, n);
            var tiles = new TileData[n * n];
            WorldGenerator.Generate(p, tiles);
            int wpp = TerrainPainter.WavePixelsPerTile(n, n);
            var t = new ArrayTiles { A = tiles };
            var f0 = new uint[n * wpp * n * wpp]; var f1 = new uint[f0.Length];
            var p0 = new ArrayPixels { A = f0 }; var p1 = new ArrayPixels { A = f1 };
            for (int row = 0; row < n; row++) { TerrainPainter.PaintWaveRow(ref t, ref p0, n, n, wpp, 0, row); TerrainPainter.PaintWaveRow(ref t, ref p1, n, n, wpp, 1, row); }
            int crests = 0;
            for (int i = 0; i < f0.Length; i++)
            {
                if (f0[i] == 0) continue;
                crests++;
                int gx = i % (n * wpp), gy = i / (n * wpp), tx = gx / wpp, ty = gy / wpp;
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int x = tx + dx, y = ty + dy;
                        if (x < 0 || y < 0 || x >= n || y >= n) continue;
                        Assert.IsTrue(tiles[y * n + x].IsWater, "a wave pixel next to land");
                    }
            }
            Assert.Greater(crests, 0, "some waves exist");
            Assert.AreNotEqual(f0, f1, "frames animate");
        }

        static uint[] Paint(TileData[] tiles, int n, int ppt)
        {
            var px = new uint[n * ppt * n * ppt];
            var t = new ArrayTiles { A = tiles }; var pix = new ArrayPixels { A = px }; var atlas = new ArrayAtlas { A = SpriteLibrary.Build() };
            for (int row = 0; row < n; row++) TerrainPainter.PaintGroundRow(ref t, ref pix, n, n, ppt, row);
            TerrainPainter.PaintDecorations(ref t, ref pix, ref atlas, n, n, ppt);
            return px;
        }
    }
}
