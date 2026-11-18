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
