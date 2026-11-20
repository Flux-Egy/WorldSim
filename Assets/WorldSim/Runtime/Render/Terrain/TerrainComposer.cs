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
    }

    /// <summary>
    /// CPU reference compositor for the new terrain look (rebuild phase 2): pack tiles on the 4 px sub-cell layout,
    /// elevation with cliff faces, water depth bands, shore foam, then props, all drawn back to front.
    /// The Unity renderer draws the same picture with a shader; this one is for the preview tool and tests.
    /// Output rows are top-down, packed as <see cref="Rgba"/>.
    /// </summary>
    public static class TerrainComposer
    {
        const int Px = TerrainLayout.CellPixels, Sp = TerrainLayout.SubPixels, Spc = TerrainLayout.SubPerCell;

        /// <summary>Near zoom (1 px = 1 art pixel). Renders cells [cx0, cx0+cw) x [cy0, cy0+ch); the image is
        /// <c>cw*16</c> wide and <c>ch*16 + TerrainLayout.MaxLift</c> high (room for the lifted back row).</summary>
        public static uint[] ComposeNear(TileData[] tiles, TerrainLayout lay, IArtPixels art, int cx0, int cy0, int cw, int ch,
                                         bool props, out int imageW, out int imageH)
        {
            // A window inside the map: draw extra rows above and below (lifted land reaches up to 2-3 cells), then cut.
            const int Margin = 4;
            int ry0 = cy0 - Margin < 0 ? 0 : cy0 - Margin, ry1 = cy0 + ch + Margin > lay.Height ? lay.Height : cy0 + ch + Margin;
            if (ry0 != cy0 || ry1 != cy0 + ch)
            {
                var big = ComposeRows(tiles, lay, art, cx0, ry0, cw, ry1 - ry0, props, out int bw, out int bh);
                int skip = (cy0 - ry0) * Px;                                         // rows above the window
                imageW = bw; imageH = ch * Px + TerrainLayout.MaxLift;
                var cut = new uint[imageW * imageH];
                for (int y = 0; y < imageH; y++) System.Array.Copy(big, (y + skip) * bw, cut, y * bw, bw);
                return cut;
            }
            return ComposeRows(tiles, lay, art, cx0, cy0, cw, ch, props, out imageW, out imageH);
        }

        static uint[] ComposeRows(TileData[] tiles, TerrainLayout lay, IArtPixels art, int cx0, int cy0, int cw, int ch,
                                  bool props, out int imageW, out int imageH)
        {
            int W = cw * Px, top = TerrainLayout.MaxLift, H = ch * Px + top;
            imageW = W; imageH = H;
            var img = new uint[W * H];
            var water = new bool[W * H];
            var cache = new FrameCache(art);
            uint ocean = Pixel(art, cache.Water[0], 0, 0);
            for (int i = 0; i < img.Length; i++) { img[i] = ocean; water[i] = true; }

            for (int cy = cy0; cy < cy0 + ch; cy++)
            {
                for (int sr = 0; sr < Spc; sr++)
                {
                    int sy = cy * Spc + sr;
                    for (int sx = cx0 * Spc; sx < (cx0 + cw) * Spc; sx++)
                        DrawSubCell(tiles, lay, cache, art, img, water, W, H, cx0, cy0, top, sx, sy);
                }
                if (props)
                    for (int cx = cx0; cx < cx0 + cw; cx++) DrawProp(tiles, lay, cache, art, img, W, H, cx0, cy0, top, cx, cy);
            }
            AddFoam(img, water, W, H, cache, art);
            return img;
        }

        static void DrawSubCell(TileData[] tiles, TerrainLayout lay, FrameCache cache, IArtPixels art, uint[] img, bool[] water,
                                int W, int H, int cx0, int cy0, int top, int sx, int sy)
        {
            int s = sy * lay.SubWidth + sx;
            int cell = lay.SubCell[s];
            int level = lay.SubLevel[s];
            int lift = TerrainLayout.Lift(level);
            int ox = (sx - cx0 * Spc) * Sp, oy = (sy - cy0 * Spc) * Sp + top - lift;
            TileData t = tiles[cell];
            bool isWater = t.IsWater;
            int tile = GroundFrame(t, lay.Band[cell], cell, lay.Width, cache, art);
            int wx0 = sx * Sp, wy0 = sy * Sp;

            // Front neighbour (one sub-cell down): a lower one shows this sub-cell's cliff face.
            int frontLevel = sy + 1 < lay.SubHeight ? lay.SubLevel[s + lay.SubWidth] : level;
            if (frontLevel < TerrainLayout.WaterLevel) frontLevel = TerrainLayout.WaterLevel;
            bool rim = level > TerrainLayout.WaterLevel && frontLevel < level;
            // Light from the top-left: ground right of a higher sub-cell lies in its shadow.
            // A terrace d sub-cells to the west shades this one when it is at least d levels higher (~45 degree light).
            bool shade = false;
            if (level >= TerrainLayout.WaterLevel)
                for (int d = 1; d <= 3 && sx - d >= 0 && !shade; d++)
                    shade = lay.SubLevel[s - d] >= level + d;
            if (!shade && sx > 0 && lay.SubLevel[s - 1] > level && level >= TerrainLayout.WaterLevel) shade = true;
            int calm = Calmness(t.Biome);

            for (int y = 0; y < Sp; y++)
            {
                int py = oy + y;
                if (py < 0 || py >= H) continue;
                for (int x = 0; x < Sp; x++)
                {
                    int i = py * W + ox + x;
                    uint c = Pixel(art, tile, (wx0 + x) & 63, (wy0 + y) & 63);
                    if (calm > 0) c = Calm(c, cache.Mean(tile), calm);
                    if (shade) c = Rgba.Darken(c, 82);                         // in the shadow of higher ground to the west
                    if (rim && y == Sp - 1) c = Rgba.Shift(c, 14);              // lit edge above a drop
                    img[i] = c;
                    water[i] = isWater;
                }
            }

            if (!rim) return;
            int drop = TerrainLayout.Lift(level) - TerrainLayout.Lift(frontLevel);
            int diff = drop / TerrainLayout.LiftPerLevel;
            int cliff = cache.Cliff(TerrainLayout.CliffMaterial(level), diff > 4 ? 4 : diff);
            int ch = art.Height(cliff);
            for (int k = 0; k < drop + 2; k++)
            {
                int py = oy + Sp + k;
                if (py < 0 || py >= H) continue;
                int row = k < ch ? k : 2 + (k - 2) % (ch - 2);                   // stack faces taller than 4 levels
                for (int x = 0; x < Sp; x++)
                {
                    uint c = Pixel(art, cliff, (wx0 + x) & 63, row);
                    if (Rgba.A(c) < 128) continue;
                    int i = py * W + ox + x;
                    img[i] = c;
                    water[i] = false;
                }
            }
        }

        /// <summary>How much of a ground tile's detail to keep (0 = all). Big rocky areas read better calm: the
        /// mountain's height, cliffs and shadows carry the shape, not a busy repeating texture.</summary>
        static int Calmness(Biome b) => b == Biome.Mountain ? 55 : b == Biome.RockyHighland ? 35 : 0;

        static uint Calm(uint c, uint mean, int percent)
        {
            int k = 100 - percent;
            return Rgba.Pack(Rgba.R(mean) + (Rgba.R(c) - Rgba.R(mean)) * k / 100,
                             Rgba.G(mean) + (Rgba.G(c) - Rgba.G(mean)) * k / 100,
                             Rgba.B(mean) + (Rgba.B(c) - Rgba.B(mean)) * k / 100);
        }

        static int GroundFrame(TileData t, byte band, int cell, int w, FrameCache cache, IArtPixels art)
        {
            Biome b = t.Biome;
            int cx = cell % w, cy = cell / w;
            // One variant per 64 px block keeps the seamless tiles seamless inside a biome.
            int variant = (int)(TerrainLayout.Hash(cx >> 2, (cy >> 2) + 7919) & 3);
            if (b == Biome.CoralShallows && band == 2) return cache.Tile(b, variant);
            if (t.IsWater) return cache.Water[band > 2 ? 2 : band];
            return cache.Tile(b, variant);
        }

        static void DrawProp(TileData[] tiles, TerrainLayout lay, FrameCache cache, IArtPixels art, uint[] img, int W, int H,
                             int cx0, int cy0, int top, int cx, int cy)
        {
            TileData t = tiles[cy * lay.Width + cx];
            if (t.DecorationId == 0) return;
            uint h = TerrainLayout.Hash(cx + 104729, cy);
            string name = BiomeArt.Prop(t.Decoration, (int)(h % 97));
            if (name == null || !cache.Frame(name, out int f)) return;
            int fw = art.Width(f), fh = art.Height(f);
            int lift = TerrainLayout.Lift(lay.Level[cy * lay.Width + cx]);
            // Foot point: cell centre, nudged a little so props don't sit on a visible grid.
            int footX = (cx - cx0) * Px + Px / 2 + (int)((h >> 8) % 7) - 3;
            int footY = (cy - cy0) * Px + Px / 2 + (int)((h >> 12) % 5) - 2 + top - lift;
            int left = footX - (int)(art.PivotX(f) * fw);
            int topY = footY - (int)((1f - art.PivotY(f)) * fh);
            for (int y = 0; y < fh; y++)
            {
                int py = topY + y;
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
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int i = y * W + x;
                    if (!water[i]) continue;
                    if (Land(water, W, H, x - 1, y) || Land(water, W, H, x + 1, y) || Land(water, W, H, x, y - 1) || Land(water, W, H, x, y + 1)) dist[i] = 1;
                }
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int i = y * W + x;
                    if (!water[i] || dist[i] != 0) continue;
                    if (One(dist, W, H, x - 1, y) || One(dist, W, H, x + 1, y) || One(dist, W, H, x, y - 1) || One(dist, W, H, x, y + 1)) dist[i] = 2;
                }
            int foam = cache.Foam;
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int i = y * W + x;
                    if (dist[i] == 0) continue;
                    uint c = foam >= 0 ? art.Pixel(foam, x & 63, dist[i] - 1) : Rgba.Pack(230, 240, 245);
                    int a = Rgba.A(c);
                    if (a > 0) img[i] = Rgba.Mix(img[i], c, dist[i] == 1 ? a : a / 2);
                }
        }

        static bool Land(bool[] water, int W, int H, int x, int y) => x >= 0 && y >= 0 && x < W && y < H && !water[y * W + x];
        static bool One(byte[] d, int W, int H, int x, int y) => x >= 0 && y >= 0 && x < W && y < H && d[y * W + x] == 1;

        static uint Pixel(IArtPixels art, int f, int x, int y) => f < 0 ? Rgba.Pack(255, 0, 255) : art.Pixel(f, x, y);

        /// <summary>Far zoom: one cell = 4 px from the 16 px LOD tiles (zoom 1/4); water in its band colour.</summary>
        public static uint[] ComposeFar(TileData[] tiles, TerrainLayout lay, IArtPixels art)
        {
            int W = lay.Width * 4, H = lay.Height * 4;
            var img = new uint[W * H];
            var cache = new FrameCache(art);
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int cell = (y >> 2) * lay.Width + (x >> 2);
                    TileData t = tiles[cell];
                    int variant = (int)(TerrainLayout.Hash((x >> 2) >> 2, ((y >> 2) >> 2) + 7919) & 3);
                    int f = t.IsWater ? cache.Water[lay.Band[cell] > 2 ? 2 : lay.Band[cell]] : cache.Lod(t.Biome, variant);
                    uint c = t.IsWater ? art.Pixel(f, (x * 4) & 63, (y * 4) & 63) : Pixel(art, f, x & 15, y & 15);
                    if (!t.IsWater)
                    {
                        int lv = lay.Level[cell], cx = x >> 2, cy = y >> 2;
                        int west = cx > 0 ? lay.Level[cell - 1] : lv;
                        int front = cy + 1 < lay.Height ? lay.Level[cell + lay.Width] : lv;
                        if (west > lv) c = Rgba.Darken(c, 82);                        // shadow east of higher ground
                        if (front < lv && lv >= 7 && (y & 3) == 3)
                            c = Rgba.Darken(c, lv >= 9 ? 62 : 72);                    // a cliff line at the drop
                    }
                    img[y * W + x] = c;
                }
            return img;
        }

        /// <summary>Frame ids looked up once per name.</summary>
        sealed class FrameCache
        {
            readonly IArtPixels _art;
            readonly System.Collections.Generic.Dictionary<string, int> _ids = new System.Collections.Generic.Dictionary<string, int>();
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

            readonly System.Collections.Generic.Dictionary<int, uint> _means = new System.Collections.Generic.Dictionary<int, uint>();

            /// <summary>Average colour of a 64 px tile.</summary>
            public uint Mean(int f)
            {
                if (f < 0) return 0;
                if (_means.TryGetValue(f, out uint m)) return m;
                long r = 0, g = 0, b = 0;
                for (int y = 0; y < 64; y++)
                    for (int x = 0; x < 64; x++) { uint c = _art.Pixel(f, x, y); r += Rgba.R(c); g += Rgba.G(c); b += Rgba.B(c); }
                m = Rgba.Pack((int)(r / 4096), (int)(g / 4096), (int)(b / 4096));
                _means[f] = m;
                return m;
            }
            public int Tile(Biome b, int v) => Id(BiomeArt.Tile(b, v));
            public int Lod(Biome b, int v) => Id(BiomeArt.LodTile(b, v, 16));
            public int Cliff(string mat, int diff) => Id("cliff_" + mat + "_" + (diff < 1 ? 1 : diff));
        }
    }
}
