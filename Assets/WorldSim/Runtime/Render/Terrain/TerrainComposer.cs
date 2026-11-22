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
    /// <summary>Zoom layers, each drawn with its own level of detail.</summary>
    public enum ZoomLayer : byte { Near = 0, Mid = 1, Far = 2, Map = 3 }

    public static class TerrainComposer
    {
        const int Px = TerrainLayout.CellPixels;

        // ------------------------------------------------------------------------------------------------ near / mid
        /// <summary>Renders the cell window [cx0, cx0+cw) x [cy0, cy0+ch) at 1 art pixel per pixel (cw*16 x ch*16).</summary>
        public static uint[] ComposeNear(TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art,
                                         int cx0, int cy0, int cw, int ch, bool props, out int imageW, out int imageH,
                                         TerrainStyle style = null)
        {
            int W = cw * Px, H = ch * Px;
            imageW = W; imageH = H;
            int X0 = cx0 * Px, Y0 = cy0 * Px;
            var img = new uint[W * H];
            var water = new bool[W * H];
            var cache = new FrameCache(art);
            uint ocean = art.Pixel(cache.Water[0], 0, 0);
            for (int i = 0; i < img.Length; i++) { img[i] = ocean; water[i] = true; }

            const int West = 8;                                      // columns west of the window, for shadows
            int rowLen = W + West + 1;
            var curCell = new int[rowLen]; var curLv = new int[rowLen];
            var nextCell = new int[rowLen]; var nextLv = new int[rowLen];
            int worldH = lay.Height * Px, worldW = lay.Width * Px;
            int yStart = Y0 - TerrainLayout.MaxLift - 2, yEnd = Y0 + H + TerrainLayout.MaxLift + 48;
            if (yStart < 0) yStart = 0;
            if (yEnd > worldH) yEnd = worldH;
            FillRow(field, lay, X0 - West, yStart, curCell, curLv);

            var propRows = props ? CollectProps(tiles, lay, cache, cx0, cy0, cw, ch) : null;

            for (int y = yStart; y < yEnd; y++)
            {
                if (y + 1 < worldH) FillRow(field, lay, X0 - West, y + 1, nextCell, nextLv);
                else { System.Array.Copy(curCell, nextCell, rowLen); System.Array.Copy(curLv, nextLv, rowLen); }

                for (int i = West; i < West + W; i++)
                {
                    int x = X0 + i - West;
                    if (x >= worldW) break;
                    int cell = curCell[i], L = curLv[i];
                    bool isWater = L < TerrainLayout.WaterLevel;
                    int lift = TerrainLayout.Lift(L);
                    uint baseC = Ground(tiles, lay, cache, art, cell, x, y, style);
                    uint c = baseC;
                    int front = nextLv[i] < TerrainLayout.WaterLevel ? TerrainLayout.WaterLevel : nextLv[i];
                    if (!isWater)
                    {
                        if (L > 4) c = Rgba.Shift(c, System.Math.Min(10, 2 * (L - 4)));          // high ground a bit lighter
                        bool shade = false;
                        for (int d = 1; d <= West && !shade; d++)
                            shade = TerrainLayout.Lift(curLv[i - d]) - lift - d >= 0;           // ~45 degree light from the west
                        if (shade) c = Rgba.Darken(c, 88);
                        if (front < L) c = Rgba.Shift(c, 14);                                    // light lip above a drop
                        else if (L > TerrainLayout.WaterLevel && (curLv[i - 1] < L || (i + 1 < rowLen && curLv[i + 1] < L)))
                            c = Rgba.Darken(c, 86);                                              // thin side outline
                    }
                    int sy = y - lift - Y0, sx = i - West;
                    if (sy >= 0 && sy < H) { img[sy * W + sx] = c; water[sy * W + sx] = isWater; }

                    if (!isWater && front < L)
                    {
                        int drop = lift - TerrainLayout.Lift(front);
                        bool snow = lay.RenderBiome[cell] == (byte)Biome.Snow;
                        for (int k = 1; k <= drop; k++)
                        {
                            int fy = sy + k;
                            if (fy < 0 || fy >= H) continue;
                            int pct = snow ? (k == drop ? 78 : 86) : (k == drop ? 58 : 70);   // a dark shade of the same ground, moderate contrast
                            img[fy * W + sx] = Rgba.Darken(baseC, pct);
                            water[fy * W + sx] = false;
                        }
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
        static uint Ground(TileData[] tiles, TerrainLayout lay, FrameCache cache, IArtPixels art, int cell, int x, int y, TerrainStyle style)
        {
            Biome b = (Biome)lay.RenderBiome[cell];
            if (tiles[cell].IsWater && !(b == Biome.CoralShallows && lay.Band[cell] == 2))
            {
                int band = lay.Band[cell] > 2 ? 2 : lay.Band[cell];
                int wf = cache.Water[band];
                uint w = art.Pixel(wf, x & 63, y & 63);
                return style == null ? w : style.Retint(w, cache.Mean(wf), b, band);
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
            int calm = Calmness(b);
            if (calm > 0) c = Calm(c, cache.Mean(f), calm);
            return style == null ? c : style.Retint(c, cache.Mean(f), b, -1);
        }

        /// <summary>Rock and snow are calmed (fewer, softer blotches); the rest keeps its texture.</summary>
        static int Calmness(Biome b) =>
            b == Biome.Mountain ? 62 : b == Biome.RockyHighland ? 45 : b == Biome.Snow || b == Biome.Glacier ? 45 : 0;

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
            int foam = cache.Foam;
            for (int i = 0; i < img.Length; i++)
            {
                if (dist[i] == 0) continue;
                uint c = foam >= 0 ? art.Pixel(foam, (i % W) & 63, dist[i] - 1) : Rgba.Pack(230, 240, 245);
                int a = Rgba.A(c);
                if (a > 0) img[i] = Rgba.Mix(img[i], c, dist[i] == 1 ? a : a / 2);
            }
        }

        static bool Land(bool[] water, int W, int H, int x, int y) => x >= 0 && y >= 0 && x < W && y < H && !water[y * W + x];
        static bool Is(byte[] d, int W, int H, int x, int y, int v) => x >= 0 && y >= 0 && x < W && y < H && d[y * W + x] == v;

        // ------------------------------------------------------------------------------------------------ mid / far / map
        /// <summary>
        /// The zoomed-out layers, each with its own detail (owner's table, 2026-11-22), never a shrunk near view:
        /// <list type="bullet">
        /// <item><b>Mid</b> (4 px per cell, lod16 tiles): only big cliffs (2+ levels) as a thin line at half the near
        /// contrast; tree crowns as small dots; settlements/roads/farms from the overlay.</item>
        /// <item><b>Far</b> (2 px per cell, lod8 tiles): no elevation lines, a very light hillshade on mountains only;
        /// forests as darker patches by real tree density; markers and kingdom borders from the overlay.</item>
        /// <item><b>Map</b> (2 px per cell): flat map colours, kingdom territory in its colour with borders, capitals
        /// and roads only.</item>
        /// </list>
        /// </summary>
        public static uint[] ComposeZoom(TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art, ZoomLayer zoom,
                                         FarOverlay overlay = null, TerrainStyle style = null, System.Func<Biome, int, uint> mapColor = null)
        {
            int ppc = zoom == ZoomLayer.Mid ? 4 : 2, lodPx = ppc * 4, step = Px / ppc;
            int W = lay.Width * ppc, H = lay.Height * ppc;
            var img = new uint[W * H];
            var cache = new FrameCache(art);
            byte[] density = zoom == ZoomLayer.Far ? TreeDensity(tiles, lay) : null;
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int wx0 = x * step + step / 2, wy0 = y * step + step / 2;
                    field.Pick(wx0, wy0, out int cell, out int level);
                    Biome b = (Biome)lay.RenderBiome[cell];
                    bool water = tiles[cell].IsWater && !(b == Biome.CoralShallows && lay.Band[cell] == 2);
                    int band = lay.Band[cell] > 2 ? 2 : lay.Band[cell];
                    uint c;
                    if (zoom == ZoomLayer.Map && mapColor != null)
                        c = mapColor(b, tiles[cell].IsWater ? band : -1);
                    else if (water)
                    {
                        int wf = cache.Water[band];
                        c = art.Pixel(wf, (x * step) & 63, (y * step) & 63);
                        if (style != null) c = style.Retint(c, cache.Mean(wf), b, band);
                    }
                    else
                    {
                        // Irregular patches, continuous wrapped sampling, random variant/offset/flip/rotation: no grid.
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
                            int calm = Calmness(b) + (b == Biome.Beach ? 60 : 0);
                            if (calm > 0) c = Calm(c, cache.Mean(f), calm > 90 ? 90 : calm);
                            if (style != null) c = style.Retint(c, cache.Mean(f), b, -1);
                        }
                        if (zoom == ZoomLayer.Mid)
                        {
                            // Big cliffs only (2+ levels down to the pixel in front): a 1 px line at half contrast.
                            field.Pick(wx0, wy0 + step, out _, out int front);
                            if (front >= TerrainLayout.WaterLevel && level - front >= 2) c = Rgba.Darken(c, 80);
                        }
                        else
                        {
                            if (IsRockOrSnow(b)) c = LightHillshade(c, field, wx0, wy0, x, y);
                            if (density != null && density[cell] > 0) c = Rgba.Darken(c, 100 - density[cell]);
                        }
                    }
                    img[y * W + x] = c;
                }
            if (zoom == ZoomLayer.Mid) DrawTreeClusters(tiles, lay, field, art, cache, img, W, H);
            if (overlay != null) overlay.Draw(img, W, H, ppc, art, zoom == ZoomLayer.Map);
            return img;
        }

        /// <summary>Kept for callers of the first far renderer: 4 = Mid, 2 = Far.</summary>
        public static uint[] ComposeFar(TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art, int pixelsPerCell) =>
            ComposeZoom(tiles, lay, field, art, pixelsPerCell >= 4 ? ZoomLayer.Mid : ZoomLayer.Far);

        static bool IsRockOrSnow(Biome b) => b == Biome.Mountain || b == Biome.RockyHighland || b == Biome.Snow || b == Biome.Glacier || b == Biome.Volcanic;

        static readonly int[] Bayer4 = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };

        /// <summary>Far zoom: a very light (at most 8 %), stepped and dithered hillshade on mountains; no lines.</summary>
        static uint LightHillshade(uint c, TerrainField field, int wx, int wy, int x, int y)
        {
            int g = field.Height(wx + 16, wy) - field.Height(wx - 16, wy) + field.Height(wx, wy + 16) - field.Height(wx, wy - 16);
            int v = g * 8 / 160;                                         // percent x16
            if (v > 128) v = 128; else if (v < -128) v = -128;
            int q = v >= 0 ? v / 64 : -((-v + 63) / 64);                // steps of 4 %
            if ((v - q * 64) / 4 > Bayer4[(y & 3) * 4 + (x & 3)]) q++;
            int pct = q * 4;
            return pct == 0 ? c : Rgba.Pack(Rgba.R(c) * (100 + pct) / 100, Rgba.G(c) * (100 + pct) / 100, Rgba.B(c) * (100 + pct) / 100);
        }

        /// <summary>Per cell: how much darker (0..16 %) the far ground is, from the trees in its 5x5 neighbourhood.</summary>
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
                    int v = n * 16 * 100 / (total * 35);                   // 35 % trees -> 16 % darker
                    d[y * w + x] = (byte)(v > 16 ? 16 : v);
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
