using System.Collections.Generic;
using WorldSim.Core;
using WorldSim.Render.Art;

namespace WorldSim.Render.Terrain
{
    /// <summary>Read access to art-pack frames as pixels (the preview tool decodes the atlas PNGs; tests can fake it).</summary>
    public interface IArtPixels
    {
        bool TryFrame(string name, out int id);
        int Width(int id);
        int Height(int id);
        /// <summary>Pivot, normalised from the bottom-left (Unity convention).</summary>
        float PivotX(int id);
        float PivotY(int id);
        /// <summary>Pixel at (x, y) from the frame's top-left, packed as <see cref="Rgba"/>.</summary>
        uint Pixel(int id, int x, int y);
        /// <summary>Recolour mask at (x, y): region 1..6 (TEAM, ACC, ACC2, ROOF, SKIN, HAIR) and ramp step 0..4;
        /// false where the frame has no mask or the pixel no region.</summary>
        bool Mask(int id, int x, int y, out int region, out int step);
    }

    /// <summary>
    /// CPU reference compositor for the new terrain look (rebuild phase 2). The Unity renderer draws the same picture
    /// with a shader; this one feeds the preview tool and tests. Output rows are top-down, packed as <see cref="Rgba"/>.
    /// <para>Near/mid zoom (1 art px per world px): per-pixel ground from <see cref="TerrainField"/>; every 16 px square
    /// samples a random 16 px window of a random tile variant, flipped/rotated by hash (no visible repeat); terraces
    /// rise <see cref="TerrainLayout.LiftPerLevel"/> px per level, with a continuous dark face under every drop, a light
    /// lip on top, a thin outline on the sides, shadow east of higher ground and slightly lighter high ground; shore
    /// foam; pack props drawn back to front.</para>
    /// <para>Far zoom: the pack's 16 px (1/4) or 8 px (1/8) LOD tiles, smooth contours, no elevation lines, and trees
    /// as small crown clusters.</para>
    /// </summary>
    public static class TerrainComposer
    {
        const int Px = TerrainLayout.CellPixels;

        // ------------------------------------------------------------------------------------------------ near / mid
        /// <summary>Renders the cell window [cx0, cx0+cw) x [cy0, cy0+ch) at 1 art pixel per pixel (cw*16 x ch*16).</summary>
        public static uint[] ComposeNear(TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art,
                                         int cx0, int cy0, int cw, int ch, bool props, out int imageW, out int imageH)
        {
            int W = cw * Px, H = ch * Px;
            imageW = W; imageH = H;
            int X0 = cx0 * Px, Y0 = cy0 * Px;
            var img = new uint[W * H];
            var water = new bool[W * H];
            var cache = new FrameCache(art);
            uint ocean = art.Pixel(cache.Water[0], 0, 0);
            for (int i = 0; i < img.Length; i++) { img[i] = ocean; water[i] = true; }

            int rowLen = W;
            var curCell = new int[rowLen]; var curLv = new int[rowLen];
            var nextCell = new int[rowLen]; var nextLv = new int[rowLen];
            var snowAbove = new int[rowLen];                          // rows since the last snow pixel above (0 = none)
            int worldH = lay.Height * Px, worldW = lay.Width * Px;
            int yStart = Y0 - TerrainLayout.MaxLift - 8, yEnd = Y0 + H + TerrainLayout.MaxLift + 48;
            if (yStart < 0) yStart = 0;
            if (yEnd > worldH) yEnd = worldH;
            FillRow(field, lay, X0, yStart, curCell, curLv);

            var propRows = props ? CollectProps(tiles, lay, cache, cx0, cy0, cw, ch) : null;
            uint snowShadow = Rgba.Pack(70, 86, 120);

            for (int y = yStart; y < yEnd; y++)
            {
                if (y + 1 < worldH) FillRow(field, lay, X0, y + 1, nextCell, nextLv);
                else { System.Array.Copy(curCell, nextCell, rowLen); System.Array.Copy(curLv, nextLv, rowLen); }

                for (int i = 0; i < W; i++)
                {
                    int x = X0 + i;
                    if (x >= worldW) break;
                    int cell = curCell[i], L = curLv[i];
                    bool isWater = L < TerrainLayout.WaterLevel;
                    bool isSnow = lay.RenderBiome[cell] == (byte)Biome.Snow;
                    int lift = TerrainLayout.Lift(L);
                    uint baseC = Ground(tiles, lay, field, cache, art, cell, x, y);
                    uint c = baseC;
                    bool coastDrop = !isWater && lift > TerrainLayout.Lift(nextLv[i]);
                    if (!isWater)
                    {
                        c = Hillshade(c, field, x, y);
                        if (!isSnow && snowAbove[i] > 0)                                        // soft blue-grey shadow south of snow
                            c = Rgba.Mix(c, snowShadow, snowAbove[i] == 1 ? 130 : snowAbove[i] == 2 ? 86 : 44);
                        if (coastDrop) c = Rgba.Shift(c, 16);                                   // light lip above the coast cliff
                    }
                    snowAbove[i] = isSnow ? 1 : snowAbove[i] > 0 && snowAbove[i] < 3 ? snowAbove[i] + 1 : 0;
                    if (isSnow) snowAbove[i] = 1;

                    int sy = y - lift - Y0;
                    if (sy >= 0 && sy < H) { img[sy * W + i] = c; water[sy * W + i] = isWater; }

                    if (coastDrop)                                                               // the only cliff: land over water/beach
                        for (int k = 1; k <= lift; k++)
                        {
                            int fy = sy + k;
                            if (fy < 0 || fy >= H) continue;
                            img[fy * W + i] = Rgba.Darken(baseC, k == lift ? 46 : 60);
                            water[fy * W + i] = false;
                        }
                }

                if (propRows != null && propRows.TryGetValue(y, out var list))
                    foreach (var p in list) DrawProp(field, art, img, W, H, X0, Y0, p);

                var t1 = curCell; curCell = nextCell; nextCell = t1;
                var t2 = curLv; curLv = nextLv; nextLv = t2;
            }
            AddFoam(img, water, W, H, cache, art);
            return img;
        }

        static void FillRow(TerrainField field, TerrainLayout lay, int x0, int y, int[] cells, int[] levels)
        {
            int maxX = lay.Width * Px - 1;
            for (int i = 0; i < cells.Length; i++)
            {
                int x = x0 + i;
                if (x < 0) x = 0; else if (x > maxX) x = maxX;
                field.Pick(x, y, out cells[i], out levels[i]);
            }
        }

        /// <summary>Ground colour of a world pixel: a random window of a random variant per 16 px square, flipped and
        /// rotated by hash, so seamless tiles never show their repeat. Water keeps its horizontal ripples (no rotation).</summary>
        static uint Ground(TileData[] tiles, TerrainLayout lay, TerrainField field, FrameCache cache, IArtPixels art, int cell, int x, int y)
        {
            Biome b = (Biome)lay.RenderBiome[cell];
            if (tiles[cell].IsWater)
            {
                int band = field.WaterBand(x, y);
                if (!(b == Biome.CoralShallows && band == 2)) return art.Pixel(cache.Water[band], x & 63, y & 63);
            }
            // Patches of ~16 px with noise-warped, irregular borders; inside a patch the (wrapping, seamless) tile is
            // sampled continuously with its own variant, offset, flip and rotation, so no grid and no visible repeat.
            int px = x + TerrainField.Noise(x, y, 0x2F1B) * 7 / 128, py = y + TerrainField.Noise(x, y, 0x6C35) * 7 / 128;
            uint h = TerrainLayout.Hash(px >> 4, (py >> 4) + 7919);
            int u = x, v = y;
            int t = (int)((h >> 2) & 7);
            if ((t & 1) != 0) u = -u;
            if ((t & 2) != 0) v = -v;
            if ((t & 4) != 0) { int s = u; u = v; v = s; }
            int f = cache.Tile(b, (int)(h & 3));
            if (f < 0) return Rgba.Pack(255, 0, 255);
            uint c = art.Pixel(f, (u + (int)((h >> 5) & 63)) & 63, (v + (int)((h >> 11) & 63)) & 63);
            return Rock(c, b, field.Height(x, y), cache.Mean(f));
        }

        /// <summary>Rock gets darker and heavier (more texture contrast) the higher it is; low rock stays calm.</summary>
        static uint Rock(uint c, Biome b, int height16, uint mean)
        {
            if (b != Biome.Mountain && b != Biome.RockyHighland) return c;
            int t = (height16 / 16 - 188) * 100 / 52;                   // 0 at the foothills .. 100 near the snow line
            if (t < 0) t = 0; else if (t > 100) t = 100;
            c = Calm(c, mean, 55 - t * 55 / 100);
            return Rgba.Darken(c, 100 - t * 20 / 100);
        }

        /// <summary>Soft hillshade, light from the top-left: slopes facing it a little lighter, the others a little
        /// darker (at most about 14%), from the smoothed height, so there are no edges.</summary>
        static uint Hillshade(uint c, TerrainField field, int x, int y)
        {
            int gx = field.Height(x + 12, y) - field.Height(x - 12, y);
            int gy = field.Height(x, y + 12) - field.Height(x, y - 12);
            int pct = (gx + gy) / 10;
            if (pct > 14) pct = 14; else if (pct < -14) pct = -14;
            return pct == 0 ? c : Scale(c, 100 + pct);
        }

        static uint Scale(uint c, int pct) => Rgba.Pack(Rgba.R(c) * pct / 100, Rgba.G(c) * pct / 100, Rgba.B(c) * pct / 100);

        static uint Calm(uint c, uint mean, int percent)
        {
            int k = 100 - percent;
            return Rgba.Pack(Rgba.R(mean) + (Rgba.R(c) - Rgba.R(mean)) * k / 100,
                             Rgba.G(mean) + (Rgba.G(c) - Rgba.G(mean)) * k / 100,
                             Rgba.B(mean) + (Rgba.B(c) - Rgba.B(mean)) * k / 100);
        }

        struct PropDraw { public int Cell, Frame, FootX, FootY; }

        static Dictionary<int, List<PropDraw>> CollectProps(TileData[] tiles, TerrainLayout lay, FrameCache cache, int cx0, int cy0, int cw, int ch)
        {
            var rows = new Dictionary<int, List<PropDraw>>();
            int ry0 = System.Math.Max(0, cy0 - 1), ry1 = System.Math.Min(lay.Height, cy0 + ch + 4);
            int rx0 = System.Math.Max(0, cx0 - 2), rx1 = System.Math.Min(lay.Width, cx0 + cw + 2);
            for (int cy = ry0; cy < ry1; cy++)
                for (int cx = rx0; cx < rx1; cx++)
                {
                    int cell = cy * lay.Width + cx;
                    TileData t = tiles[cell];
                    if (t.DecorationId == 0 || lay.Level[cell] == TerrainLayout.TopLevel) continue;   // nothing pokes out of snow caps
                    uint h = TerrainLayout.Hash(cx + 104729, cy);
                    string name = BiomeArt.Prop(t.Decoration, (int)(h % 97));
                    if (name == null || !cache.Frame(name, out int f)) continue;
                    var p = new PropDraw
                    {
                        Cell = cell, Frame = f,
                        FootX = cx * Px + Px / 2 + (int)((h >> 8) % 7) - 3,
                        FootY = cy * Px + Px / 2 + (int)((h >> 12) % 5) - 2,
                    };
                    if (!rows.TryGetValue(p.FootY, out var list)) rows[p.FootY] = list = new List<PropDraw>();
                    list.Add(p);
                }
            return rows;
        }

        static void DrawProp(TerrainField field, IArtPixels art, uint[] img, int W, int H, int X0, int Y0, PropDraw p)
        {
            field.Pick(p.FootX, p.FootY, out int footCell, out int level);
            if (footCell != p.Cell) return;                          // its ground was rounded away at a border
            int f = p.Frame, fw = art.Width(f), fh = art.Height(f);
            int left = p.FootX - X0 - (int)(art.PivotX(f) * fw);
            int top = p.FootY - TerrainLayout.Lift(level) - Y0 - (int)((1f - art.PivotY(f)) * fh);
            for (int y = 0; y < fh; y++)
            {
                int py = top + y;
                if (py < 0 || py >= H) continue;
                for (int x = 0; x < fw; x++)
                {
                    int px = left + x;
                    if (px < 0 || px >= W) continue;
                    uint c = art.Pixel(f, x, y);
                    int a = Rgba.A(c);
                    if (a == 0) continue;
                    img[py * W + px] = a == 255 ? c : Rgba.Mix(img[py * W + px], c, a);
                }
            }
        }

        /// <summary>One and two pixels of foam on the water side of every shore (shore_foam_0 rows 0-1).</summary>
        static void AddFoam(uint[] img, bool[] water, int W, int H, FrameCache cache, IArtPixels art)
        {
            var dist = new byte[img.Length];
            for (int pass = 1; pass <= 2; pass++)
                for (int y = 0; y < H; y++)
                    for (int x = 0; x < W; x++)
                    {
                        int i = y * W + x;
                        if (!water[i] || dist[i] != 0) continue;
                        bool near = pass == 1
                            ? Land(water, W, H, x - 1, y) || Land(water, W, H, x + 1, y) || Land(water, W, H, x, y - 1) || Land(water, W, H, x, y + 1)
                            : Is(dist, W, H, x - 1, y, 1) || Is(dist, W, H, x + 1, y, 1) || Is(dist, W, H, x, y - 1, 1) || Is(dist, W, H, x, y + 1, 1);
                        if (near) dist[i] = (byte)pass;
                    }
            for (int i = 0; i < img.Length; i++)
            {
                if (dist[i] == 0) continue;
                img[i] = Rgba.Mix(img[i], Rgba.Pack(242, 248, 251), dist[i] == 1 ? 210 : 70);   // thin white foam line
            }
        }

        static bool Land(bool[] water, int W, int H, int x, int y) => x >= 0 && y >= 0 && x < W && y < H && !water[y * W + x];
        static bool Is(byte[] d, int W, int H, int x, int y, int v) => x >= 0 && y >= 0 && x < W && y < H && d[y * W + x] == v;

        // ------------------------------------------------------------------------------------------------ far
        /// <summary>Far zoom: <paramref name="pixelsPerCell"/> 4 (zoom 1/4, lod16 tiles) or 2 (zoom 1/8, lod8 tiles).
        /// Smooth contours, depth bands and hillshade from the same field, a clean foam line on every coast, no
        /// elevation lines; forests darkened by their real tree density, trees as small crowns (1/4), and the
        /// optional <paramref name="overlay"/> (farms, roads, kingdom/army/monster/event markers at constant size).</summary>
        public static uint[] ComposeFar(TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art, int pixelsPerCell,
                                        FarOverlay overlay = null)
        {
            int ppc = pixelsPerCell >= 4 ? 4 : 2, lodPx = ppc * 4, step = Px / ppc;
            int W = lay.Width * ppc, H = lay.Height * ppc;
            var img = new uint[W * H];
            var isWater = new bool[W * H];
            var cache = new FrameCache(art);
            var density = TreeDensity(tiles, lay);
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int wx0 = x * step + step / 2, wy0 = y * step + step / 2;
                    field.Pick(wx0, wy0, out int cell, out _);
                    Biome b = (Biome)lay.RenderBiome[cell];
                    uint c;
                    bool water = tiles[cell].IsWater;
                    int band = water ? field.WaterBand(wx0, wy0) : 255;
                    if (water && !(b == Biome.CoralShallows && band == 2))
                        c = art.Pixel(cache.Water[band], (x * step) & 63, (y * step) & 63);
                    else
                    {
                        // Same idea as near zoom: irregular patches, continuous wrapped sampling, random variant,
                        // offset, flip and rotation.
                        int wx = x + TerrainField.Noise(x * 3, y * 3, 0x2F1B) * 3 / 128, wy = y + TerrainField.Noise(x * 3, y * 3, 0x6C35) * 3 / 128;
                        uint h = TerrainLayout.Hash(wx >> 3, (wy >> 3) + 7919);
                        int u = x, v = y, t = (int)((h >> 2) & 7), m = lodPx - 1;
                        if ((t & 1) != 0) u = -u;
                        if ((t & 2) != 0) v = -v;
                        if ((t & 4) != 0) { int sw = u; u = v; v = sw; }
                        int f = cache.Lod(b, (int)(h & 3), lodPx);
                        c = f < 0 ? Rgba.Pack(255, 0, 255) : art.Pixel(f, (u + (int)((h >> 5) & 63)) & m, (v + (int)((h >> 11) & 63)) & m);
                        if (f >= 0)
                        {
                            if (b == Biome.Beach || b == Biome.Snow) c = Calm(c, cache.Mean(f), 75);   // clean rims, no speckle
                            c = Rock(c, b, field.Height(wx0, wy0), cache.Mean(f));
                        }
                        if (!water)
                        {
                            c = Hillshade(c, field, wx0, wy0);
                            if (density[cell] > 0) c = Rgba.Darken(c, 100 - density[cell]);          // forests read darker
                        }
                    }
                    img[y * W + x] = c;
                    isWater[y * W + x] = water;
                }
            // A clean 1 px foam line on the water side of every coast (no dotted rims).
            var foam = new bool[W * H];
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int i = y * W + x;
                    if (!isWater[i]) continue;
                    if ((x > 0 && !isWater[i - 1]) || (x + 1 < W && !isWater[i + 1]) || (y > 0 && !isWater[i - W]) || (y + 1 < H && !isWater[i + W]))
                        foam[i] = true;
                }
            for (int i = 0; i < foam.Length; i++) if (foam[i]) img[i] = Rgba.Mix(img[i], Rgba.Pack(242, 248, 251), ppc == 4 ? 150 : 110);

            if (ppc == 4) DrawTreeClusters(tiles, lay, field, art, cache, img, W, H);
            if (overlay != null) overlay.Draw(img, W, H, ppc, art);
            return img;
        }

        /// <summary>Per cell: how much darker (0..14 %) the far ground is, from the trees in its 5x5 neighbourhood.</summary>
        static byte[] TreeDensity(TileData[] tiles, TerrainLayout lay)
        {
            int w = lay.Width, h = lay.Height;
            var d = new byte[tiles.Length];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    int n = 0, total = 0;
                    for (int dy = -2; dy <= 2; dy++)
                        for (int dx = -2; dx <= 2; dx++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
                            total++;
                            if (TileData.IsTree(tiles[ny * w + nx].Decoration)) n++;
                        }
                    d[y * w + x] = (byte)(n * 14 * 100 / (total * 40));                  // 40 % trees -> 14 % darker
                    if (d[y * w + x] > 14) d[y * w + x] = 14;
                }
            return d;
        }

        /// <summary>Trees at zoom 1/4: a 2x2 crown (light top-left, dark bottom-right) in the prop's own colours.</summary>
        static void DrawTreeClusters(TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art, FrameCache cache, uint[] img, int W, int H)
        {
            for (int cy = 0; cy < lay.Height; cy++)
                for (int cx = 0; cx < lay.Width; cx++)
                {
                    int cell = cy * lay.Width + cx;
                    TileData t = tiles[cell];
                    if (!TileData.IsTree(t.Decoration) || lay.Level[cell] == TerrainLayout.TopLevel) continue;
                    field.Pick(cx * Px + 8, cy * Px + 8, out int at, out _);
                    if (at != cell) continue;
                    uint h = TerrainLayout.Hash(cx + 104729, cy);
                    string name = BiomeArt.Prop(t.Decoration, (int)(h % 97));
                    if (name == null || !cache.Frame(name, out int f)) continue;
                    cache.Crown(f, out uint light, out uint mid, out uint dark);
                    // A small round crown:  . L .  /  L M D  /  . D .  with a shadow pixel below-right.
                    int x0 = cx * 4 + (int)((h >> 8) & 1), y0 = cy * 4 + (int)((h >> 9) & 1);
                    if (y0 + 3 < H && x0 + 2 < W) img[(y0 + 3) * W + x0 + 2] = Rgba.Darken(img[(y0 + 3) * W + x0 + 2], 72);
                    Put(img, W, H, x0 + 1, y0, light);
                    Put(img, W, H, x0, y0 + 1, light); Put(img, W, H, x0 + 1, y0 + 1, mid); Put(img, W, H, x0 + 2, y0 + 1, dark);
                    Put(img, W, H, x0 + 1, y0 + 2, dark);
                }
        }

        static void Put(uint[] img, int W, int H, int x, int y, uint c) { if (x >= 0 && y >= 0 && x < W && y < H) img[y * W + x] = c; }

        // ------------------------------------------------------------------------------------------------ frames
        sealed class FrameCache
        {
            readonly IArtPixels _art;
            readonly Dictionary<string, int> _ids = new Dictionary<string, int>();
            readonly Dictionary<int, uint> _means = new Dictionary<int, uint>();
            readonly Dictionary<int, (uint, uint, uint)> _crowns = new Dictionary<int, (uint, uint, uint)>();
            public readonly int[] Water = new int[3];
            public readonly int Foam;

            public FrameCache(IArtPixels art)
            {
                _art = art;
                for (int d = 0; d < 3; d++) Water[d] = Id(BiomeArt.Water(d));
                Foam = Id("shore_foam_0");
            }

            int Id(string name)
            {
                if (name == null) return -1;
                if (_ids.TryGetValue(name, out int id)) return id;
                if (!_art.TryFrame(name, out id)) id = -1;
                _ids[name] = id;
                return id;
            }

            public bool Frame(string name, out int id) { id = Id(name); return id >= 0; }
            public int Tile(Biome b, int v) => Id(BiomeArt.Tile(b, v));
            public int Lod(Biome b, int v, int px) => Id(BiomeArt.LodTile(b, v, px));

            /// <summary>Average colour of a frame's opaque pixels.</summary>
            public uint Mean(int f)
            {
                if (_means.TryGetValue(f, out uint m)) return m;
                m = Average(f, _art.Height(f));
                _means[f] = m;
                return m;
            }

            /// <summary>Crown colours of a tree prop: the mean of its upper two thirds, lightened and darkened.</summary>
            public void Crown(int f, out uint light, out uint mid, out uint dark)
            {
                if (!_crowns.TryGetValue(f, out var v))
                {
                    uint m = Average(f, _art.Height(f) * 2 / 3);
                    if (m == 0) m = Rgba.Pack(60, 110, 50);
                    v = (Rgba.Shift(m, 34), m, Rgba.Darken(m, 58));
                    _crowns[f] = v;
                }
                light = v.Item1; mid = v.Item2; dark = v.Item3;
            }

            uint Average(int f, int rows)
            {
                long r = 0, g = 0, bl = 0, n = 0;
                for (int y = 0; y < rows; y++)
                    for (int x = 0; x < _art.Width(f); x++)
                    {
                        uint c = _art.Pixel(f, x, y);
                        if (Rgba.A(c) < 128) continue;
                        r += Rgba.R(c); g += Rgba.G(c); bl += Rgba.B(c); n++;
                    }
                return n == 0 ? 0 : Rgba.Pack((int)(r / n), (int)(g / n), (int)(bl / n));
            }
        }
    }
}
