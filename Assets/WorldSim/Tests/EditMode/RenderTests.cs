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
            for (int d = 1; d < (int)Decoration.Count; d++)
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
