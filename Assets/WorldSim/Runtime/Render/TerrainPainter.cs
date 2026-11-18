using WorldSim.Core;

namespace WorldSim.Render
{
    /// <summary>Read-only tile grid (row-major). Implemented by NativeArray wrappers in Unity
    /// and by managed arrays in tools/tests.</summary>
    public interface ITileSource { TileData Get(int index); }

    /// <summary>Writable RGBA32 pixel buffer (row 0 = bottom, Unity convention).</summary>
    public interface IPixelTarget { uint Get(int index); void Set(int index, uint color); }

    /// <summary>Read-only sprite atlas from <see cref="SpriteLibrary.Build"/>.</summary>
    public interface IAtlasSource { uint Get(int index); }

    /// <summary>
    /// Paints the world into a pixel buffer: ground (organic biome edges, relief light, layered
    /// water with foam and wave dots, lava) and decorations (procedural sprites, back to front).
    /// Pure and deterministic; generic over struct sources so Burst compiles it without
    /// virtual calls, and plain .NET can run it (Tools/WorldPreview shows exactly what the
    /// game shows). Presentation only: nothing here feeds back into the simulation.
    /// </summary>
    public static class TerrainPainter
    {
        /// <summary>8 px per tile up to 256 tiles, 4 up to 512, then 2: the texture stays ≤2048².</summary>
        public static int PixelsPerTileFor(int widthTiles, int heightTiles)
        {
            int m = widthTiles > heightTiles ? widthTiles : heightTiles;
            return m <= 256 ? 8 : m <= 512 ? 4 : 2;
        }

        // ---------------------------------------------------------------- palette
        public static uint BaseColor(Biome b)
        {
            switch (b)
            {
                case Biome.DeepWater: return Rgba.Pack(30, 76, 156);
                case Biome.ShallowWater: return Rgba.Pack(56, 126, 206);
                case Biome.Sand: return Rgba.Pack(228, 210, 148);
                case Biome.Grass: return Rgba.Pack(104, 174, 64);
                case Biome.Forest: return Rgba.Pack(72, 144, 54);
                case Biome.Mountain: return Rgba.Pack(124, 116, 108);
                case Biome.Snow: return Rgba.Pack(232, 238, 246);
                case Biome.Desert: return Rgba.Pack(232, 198, 120);
                case Biome.Savanna: return Rgba.Pack(194, 184, 90);
                case Biome.Jungle: return Rgba.Pack(46, 128, 52);
                case Biome.Swamp: return Rgba.Pack(84, 104, 66);
                case Biome.Taiga: return Rgba.Pack(76, 118, 96);
                case Biome.Tundra: return Rgba.Pack(156, 166, 146);
                case Biome.BirchForest: return Rgba.Pack(132, 184, 88);
                case Biome.CrystalFields: return Rgba.Pack(150, 196, 214);
                case Biome.MushroomGrove: return Rgba.Pack(140, 106, 150);
                case Biome.EmberWastes: return Rgba.Pack(74, 62, 60);
                case Biome.Glimmerwood: return Rgba.Pack(66, 150, 142);
                case Biome.Lava: return Rgba.Pack(226, 76, 24);
                default: return Rgba.Pack(200, 60, 160); // unknown (mod) biome without a colour
            }
        }

        static uint PixelHash(int x, int y)
        {
            unchecked { return (uint)(SplitMix64.Mix(((ulong)(uint)x << 32) | (uint)y) >> 32); }
        }

        static bool IsWater(Biome b) => b == Biome.DeepWater || b == Biome.ShallowWater;

        // ---------------------------------------------------------------- ground pass
        /// <summary>Tile sampled for a pixel after a small random displacement: biome borders
        /// become irregular pixel edges instead of tile-grid squares.</summary>
        static int DisplacedIndex(int gx, int gy, int w, int h, int ppt)
        {
            int block = ppt >= 4 ? 1 : 0;                // displacement noise in 2x2 blocks when detailed
            uint hs = PixelHash(gx >> block, (gy >> block) + 7919);
            int span = ppt + 1;
            int dx = (int)(hs % (uint)span) - ppt / 2;
            int dy = (int)((hs >> 12) % (uint)span) - ppt / 2;
            int tx = (gx + dx) / ppt, ty = (gy + dy) / ppt;
            if (gx + dx < 0) tx = 0;
            if (gy + dy < 0) ty = 0;
            if (tx >= w) tx = w - 1;
            if (ty >= h) ty = h - 1;
            return ty * w + tx;
        }

        /// <summary>Paints every pixel of one row of tiles (call once per tile row; rows are independent).</summary>
        public static void PaintGroundRow<TT, TP>(ref TT tiles, ref TP pixels, int w, int h, int ppt, int tileRow)
            where TT : struct, ITileSource where TP : struct, IPixelTarget
        {
            int texW = w * ppt, texH = h * ppt;
            for (int py = 0; py < ppt; py++)
            {
                int gy = tileRow * ppt + py;
                for (int gx = 0; gx < texW; gx++)
                {
                    int idx = DisplacedIndex(gx, gy, w, h, ppt);
                    TileData t = tiles.Get(idx);
                    uint c = GroundPixel(ref tiles, t, idx, gx, gy, w, h, ppt, texW, texH);
                    pixels.Set(gy * texW + gx, c);
                }
            }
        }

        static uint GroundPixel<TT>(ref TT tiles, TileData t, int idx, int gx, int gy, int w, int h, int ppt, int texW, int texH)
            where TT : struct, ITileSource
        {
            Biome b = (Biome)t.BiomeId;
            uint hs = PixelHash(gx, gy);
            uint baseC = BaseColor(b);

            if (IsWater(b))
            {
                // Continuous depth gradient (no hard deep/shallow line): mix by height.
                int depthT = (t.Height - 40) * 256 / (WorldGenerator.SeaLevel - 40);
                if (depthT < 0) depthT = 0;
                if (depthT > 256) depthT = 256;
                depthT = depthT * depthT / 256;                           // ease: most change near the coast
                uint c = Rgba.Mix(Rgba.Pack(22, 62, 140), Rgba.Pack(70, 148, 222), depthT);
                // Foam where a neighbouring pixel samples land.
                bool shore = false;
                if (gx > 0 && !IsWater(tiles.Get(DisplacedIndex(gx - 1, gy, w, h, ppt)).Biome)) shore = true;
                else if (gx < texW - 1 && !IsWater(tiles.Get(DisplacedIndex(gx + 1, gy, w, h, ppt)).Biome)) shore = true;
                else if (gy > 0 && !IsWater(tiles.Get(DisplacedIndex(gx, gy - 1, w, h, ppt)).Biome)) shore = true;
                else if (gy < texH - 1 && !IsWater(tiles.Get(DisplacedIndex(gx, gy + 1, w, h, ppt)).Biome)) shore = true;
                if (shore) return (hs & 3) != 0 ? Rgba.Pack(196, 228, 240) : Rgba.Shift(c, 40);
                // Sparse wave dots, a little denser in shallow water.
                int period = b == Biome.ShallowWater ? 9 : 13;
                if (((gx + (gy >> 1) * 5) % period == 0) && (gy % 3 == 0)) return Rgba.Shift(c, 26);
                return Rgba.Shift(c, (int)(hs % 5) - 2);
            }

            if (b == Biome.Lava)
            {
                uint n = hs & 15;
                if (n < 3) return Rgba.Pack(255, 210, 80);
                if (n > 12) return Rgba.Pack(150, 30, 20);
                return Rgba.Shift(baseC, (int)(hs >> 8 & 15) - 8);
            }

            // Land: speckled base with lighter/darker pixels, height tint and top-left relief.
            int nsel = (int)(hs & 15);
            uint col = baseC;
            if (nsel < 2) col = Rgba.Shift(baseC, 16);
            else if (nsel > 12) col = Rgba.Shift(baseC, -16);
            int heightTint = (t.Height - 150) / 7;
            int sx = idx % w, sy = idx / w;
            int upLeft = (sx > 0 && sy < h - 1) ? tiles.Get(idx + w - 1).Height : t.Height;
            int relief = t.Height - upLeft;
            if (relief > 8) relief = 8;
            if (relief < -8) relief = -8;
            col = Rgba.Shift(col, heightTint + relief * 2 + (int)(hs >> 8 & 3) - 1);
            if (b == Biome.Mountain && (hs & 63) == 0) col = Rgba.Pack(150, 146, 140);   // pebbles
            if (b == Biome.EmberWastes && (hs & 127) == 1) col = Rgba.Pack(240, 110, 30); // embers
            if (b == Biome.CrystalFields && (hs & 63) == 2) col = Rgba.Pack(210, 240, 250);
            if (b == Biome.Glimmerwood && (hs & 127) == 3) col = Rgba.Pack(230, 230, 150);
            return col;
        }

        // ---------------------------------------------------------------- overview (far zoom)
        /// <summary>
        /// Pixels per tile of the clean far-zoom texture, or 0 when the detail texture is already
        /// coarse enough to serve as the overview (large maps).
        /// </summary>
        public static int OverviewPixelsPerTile(int widthTiles, int heightTiles)
        {
            int detail = PixelsPerTileFor(widthTiles, heightTiles);
            return detail >= 8 ? 2 : detail >= 4 ? 1 : 0;
        }

        /// <summary>Canopy colour of a tree type, used to tint forests in the far view.</summary>
        public static uint TreeTint(Decoration d)
        {
            switch (d)
            {
                case Decoration.PineTree: return Rgba.Pack(40, 98, 66);
                case Decoration.SnowPine: return Rgba.Pack(150, 176, 168);
                case Decoration.BirchTree: return Rgba.Pack(126, 180, 80);
                case Decoration.PalmTree: return Rgba.Pack(66, 150, 60);
                case Decoration.JungleTree: return Rgba.Pack(28, 100, 38);
                case Decoration.DeadTree: return Rgba.Pack(110, 92, 74);
                case Decoration.GlowTree: return Rgba.Pack(60, 160, 180);
                case Decoration.SwampTree: return Rgba.Pack(72, 92, 50);
                case Decoration.AcaciaTree: return Rgba.Pack(110, 146, 56);
                default: return Rgba.Pack(56, 124, 46);
            }
        }

        /// <summary>
        /// One tile row of the far-zoom texture: calm colours, relief light, forests as darker
        /// canopy, a light coastal band, no per-pixel noise or sprites, so the whole world reads
        /// cleanly when zoomed out instead of shimmering.
        /// </summary>
        public static void PaintOverviewRow<TT, TP>(ref TT tiles, ref TP pixels, int w, int h, int opp, int tileRow)
            where TT : struct, ITileSource where TP : struct, IPixelTarget
        {
            int texW = w * opp;
            for (int tx = 0; tx < w; tx++)
            {
                int idx = tileRow * w + tx;
                TileData t = tiles.Get(idx);
                Biome b = (Biome)t.BiomeId;
                uint c;
                if (IsWater(b))
                {
                    int depthT = (t.Height - 40) * 256 / (WorldGenerator.SeaLevel - 40);
                    if (depthT < 0) depthT = 0;
                    if (depthT > 256) depthT = 256;
                    c = Rgba.Mix(Rgba.Pack(22, 62, 140), Rgba.Pack(70, 148, 222), depthT * depthT / 256);
                    if (TouchesLand(ref tiles, tx, tileRow, w, h)) c = Rgba.Pack(120, 186, 230);
                }
                else
                {
                    c = BaseColor(b);
                    Decoration d = (Decoration)t.DecorationId;
                    if (TileData.IsTree(d)) c = Rgba.Mix(c, TreeTint(d), 170);
                    int upLeft = (tx > 0 && tileRow < h - 1) ? tiles.Get(idx + w - 1).Height : t.Height;
                    int relief = t.Height - upLeft;
                    if (relief > 8) relief = 8;
                    if (relief < -8) relief = -8;
                    c = Rgba.Shift(c, (t.Height - 150) / 7 + relief * 2);
                }
                for (int py = 0; py < opp; py++)
                    for (int px = 0; px < opp; px++)
                        pixels.Set((tileRow * opp + py) * texW + tx * opp + px, c);
            }
        }

        static bool TouchesLand<TT>(ref TT tiles, int x, int y, int w, int h) where TT : struct, ITileSource
        {
            if (x > 0 && !IsWater(tiles.Get(y * w + x - 1).Biome)) return true;
            if (x < w - 1 && !IsWater(tiles.Get(y * w + x + 1).Biome)) return true;
            if (y > 0 && !IsWater(tiles.Get((y - 1) * w + x).Biome)) return true;
            if (y < h - 1 && !IsWater(tiles.Get((y + 1) * w + x).Biome)) return true;
            return false;
        }

        // ---------------------------------------------------------------- water waves (near zoom)
        public const int WaveTileSize = 32; // texels; 4x4 tiles at 8 px per tile

        /// <summary>
        /// A repeating, mostly transparent wave tile: short light crests. Two copies scroll over the
        /// water (masked to water tiles) at different speeds when the camera is close.
        /// </summary>
        public static uint[] BuildWaveTile(int variant)
        {
            var px = new uint[WaveTileSize * WaveTileSize];
            uint crest = Rgba.Pack(210, 236, 250, 200), soft = Rgba.Pack(170, 214, 244, 140);
            for (int i = 0; i < 9; i++)
            {
                uint hs = PixelHash(i * 13 + variant * 101, i * 7 + 5);
                int x0 = (int)(hs % WaveTileSize), y0 = (int)((hs >> 8) % WaveTileSize), len = 3 + (int)((hs >> 16) % 4);
                for (int k = 0; k < len; k++)
                {
                    int x = (x0 + k) % WaveTileSize;
                    int y = (y0 + (k == 0 || k == len - 1 ? 0 : 1)) % WaveTileSize; // little arc
                    px[y * WaveTileSize + x] = k == 0 || k == len - 1 ? soft : crest;
                }
            }
            return px;
        }

        // ---------------------------------------------------------------- decoration pass
        /// <summary>
        /// Draws all decorations, from the top row of the map down, so sprites lower on screen
        /// (nearer the viewer) overlap the ones behind them. Single pass; call after the ground.
        /// </summary>
        public static void PaintDecorations<TT, TP, TA>(ref TT tiles, ref TP pixels, ref TA atlas, int w, int h, int ppt)
            where TT : struct, ITileSource where TP : struct, IPixelTarget where TA : struct, IAtlasSource
        {
            PaintDecorationRows(ref tiles, ref pixels, ref atlas, w, h, ppt, 0, h - 1, 0, h * ppt - 1);
        }

        /// <summary>
        /// Draws the decorations of tile rows [<paramref name="rowMin"/>, <paramref name="rowMax"/>]
        /// (top to bottom), writing only pixel rows [<paramref name="clipMin"/>, <paramref name="clipMax"/>].
        /// Used for partial repaints after terrain edits: the clip keeps sprites that reach into the
        /// repainted band from being drawn twice (shadows would darken twice) outside it.
        /// </summary>
        public static void PaintDecorationRows<TT, TP, TA>(ref TT tiles, ref TP pixels, ref TA atlas, int w, int h, int ppt,
            int rowMin, int rowMax, int clipMin, int clipMax)
            where TT : struct, ITileSource where TP : struct, IPixelTarget where TA : struct, IAtlasSource
        {
            int texW = w * ppt, texH = h * ppt;
            if (rowMin < 0) rowMin = 0;
            if (rowMax > h - 1) rowMax = h - 1;
            if (clipMin < 0) clipMin = 0;
            if (clipMax > texH - 1) clipMax = texH - 1;
            int step = 8 / ppt;                                 // sprite pixels per texture pixel
            if (step < 1) step = 1;
            for (int ty = rowMax; ty >= rowMin; ty--)
                for (int tx = 0; tx < w; tx++)
                {
                    TileData t = tiles.Get(ty * w + tx);
                    if (t.DecorationId == 0 || t.DecorationId >= (byte)Decoration.Count) continue;
                    uint hs = PixelHash(tx * 31 + 17, ty * 57 + 3);
                    int variant = (int)(hs % SpriteLibrary.Variants);
                    bool flip = (hs & 0x100) != 0;
                    int jitterX = (int)((hs >> 9) % 3) - 1;          // -1..1 sprite pixels
                    int jitterY = (int)((hs >> 11) % 3);             // 0..2 sprite pixels up
                    int shade = (int)((hs >> 13) % 17) - 8;
                    int cellBase = SpriteLibrary.CellIndex((Decoration)t.DecorationId, variant) * SpriteLibrary.CellPixels;
                    int anchorX = tx * ppt + ppt / 2, anchorY = ty * ppt;

                    for (int sy = 0; sy < SpriteLibrary.Cell; sy += step)
                        for (int sx = 0; sx < SpriteLibrary.Cell; sx += step)
                        {
                            int srcX = flip ? SpriteLibrary.Cell - 1 - sx : sx;
                            uint c = atlas.Get(cellBase + sy * SpriteLibrary.Cell + srcX);
                            if (c == 0) continue;
                            int gx = anchorX + (sx - 8 + jitterX) / step;
                            int gy = anchorY + (sy + jitterY) / step;
                            if (gx < 0 || gy < clipMin || gx >= texW || gy > clipMax) continue;
                            int i = gy * texW + gx;
                            pixels.Set(i, Rgba.A(c) < 255 ? Rgba.Darken(pixels.Get(i), 74) : Rgba.Shift(c, shade));
                        }
                }
        }

        /// <summary>Tile rows whose ground must be repainted after tiles in [yMin, yMax] changed
        /// (displaced sampling, foam and relief read neighbours up to 2 tiles away).</summary>
        public static void GroundRowsFor(int yMin, int yMax, int h, out int rowMin, out int rowMax)
        {
            rowMin = yMin - 2 < 0 ? 0 : yMin - 2;
            rowMax = yMax + 2 > h - 1 ? h - 1 : yMax + 2;
        }

        /// <summary>Tallest sprite reach above its own tile, in tiles (16 sprite px + 2 px jitter at 8 px per tile).</summary>
        public const int SpriteReachTiles = 3;

        /// <summary>
        /// Repaints everything affected by changes to tiles in rows [yMin, yMax]: ground of the
        /// neighbouring rows, then every decoration that can reach into those pixel rows, clipped
        /// to them. Produces exactly the pixels a full repaint would (see RenderTests).
        /// </summary>
        public static void RepaintRows<TT, TP, TA>(ref TT tiles, ref TP pixels, ref TA atlas, int w, int h, int ppt, int yMin, int yMax)
            where TT : struct, ITileSource where TP : struct, IPixelTarget where TA : struct, IAtlasSource
        {
            GroundRowsFor(yMin, yMax, h, out int rowMin, out int rowMax);
            for (int row = rowMin; row <= rowMax; row++) PaintGroundRow(ref tiles, ref pixels, w, h, ppt, row);
            PaintDecorationRows(ref tiles, ref pixels, ref atlas, w, h, ppt,
                rowMin - SpriteReachTiles, rowMax, rowMin * ppt, (rowMax + 1) * ppt - 1);
        }
    }
}
