// The new terrain look (rebuild phase 2) rendered from the real art pack, without Unity:
//
//   dotnet run -c Release --project Tools/WorldPreview -- pack <seedHex> <size> <outDir> [cropX cropY cropTiles ...]
//
// Writes the whole map at zoom 1/4 (far_quarter.png, lod16 tiles) and 1/8 (far_eighth.png, lod8 tiles), and per
// (cellX cellY cells) place: near (x2), mid (x1, twice the area) and the same area at zoom 1/4 enlarged x4.
using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using WorldSim.Core;
using WorldSim.Render;
using WorldSim.Render.Art;
using WorldSim.Render.Terrain;

sealed class PackArt : IArtPixels
{
    readonly ArtIndex _ix;
    readonly string _root;
    readonly Dictionary<int, (uint[] px, int w, int h)> _pages = new Dictionary<int, (uint[], int, int)>();

    public PackArt(string root)
    {
        _root = root;
        _ix = ArtIndex.Parse(File.ReadAllBytes(Path.Combine(root, "art_index.bytes")));
    }

    public bool TryFrame(string name, out int id) => _ix.TryGetFrameId(name, out id);
    public int Width(int id) => _ix.Frame(id).W;
    public int Height(int id) => _ix.Frame(id).H;
    public float PivotX(int id) => _ix.Frame(id).PivotX;
    public float PivotY(int id) => _ix.Frame(id).PivotY;

    readonly Dictionary<int, (byte[] codes, int w, int h)> _masks = new Dictionary<int, (byte[], int, int)>();
    uint[] _lut;

    public bool Mask(int id, int x, int y, out int region, out int step)
    {
        region = 0; step = 0;
        var f = _ix.Frame(id);
        var pg = _ix.Page(f.Atlas, f.Page);
        if (pg.MaskId < 0) return false;
        int key = f.Atlas * 64 + f.Page;
        if (!_masks.TryGetValue(key, out var m))
        {
            var px = PngDecoder.Decode(File.ReadAllBytes(Path.Combine(_root, _ix.GetString(pg.MaskId) + ".png")), out int w, out int h);
            var codes = new byte[px.Length];
            for (int i = 0; i < px.Length; i++) codes[i] = (byte)Rgba.R(px[i]);
            m = (codes, w, h);
            _masks[key] = m;
        }
        if (_lut == null) _lut = PngDecoder.Decode(File.ReadAllBytes(Path.Combine(_root, "mask_lut.png")), out _, out _);
        int code = m.codes[(m.h - 1 - (f.Y + y)) * m.w + f.X + x];
        uint e = _lut[code];
        if (code == 0 || Rgba.A(e) == 0) return false;
        region = Rgba.R(e) / 36;
        step = (Rgba.G(e) - 40 + 22) / 44;                          // greys 40, 84, 128, 172, 216 -> 0..4
        return region > 0;
    }

    public uint Pixel(int id, int x, int y)
    {
        var f = _ix.Frame(id);
        int key = f.Atlas * 64 + f.Page;
        if (!_pages.TryGetValue(key, out var page))
        {
            var pg = _ix.Page(f.Atlas, f.Page);
            var px = PngDecoder.Decode(File.ReadAllBytes(Path.Combine(_root, _ix.GetString(pg.ImageId) + ".png")), out int w, out int h);
            page = (px, w, h);
            _pages[key] = page;
        }
        int gy = page.h - 1 - (f.Y + y);           // decoder rows are bottom-up
        return page.px[gy * page.w + f.X + x];
    }
}

static class PackPreview
{
    public static int Run(string[] a)
    {
        ulong seed = Convert.ToUInt64(a[1].Replace("0x", ""), 16);
        int size = int.Parse(a[2]);
        string outDir = a[3];
        Directory.CreateDirectory(outDir);
        var p = WorldGenParams.Create(new WorldSeed(seed), size, size);
        var tiles = new TileData[size * size];
        WorldGenerator.Generate(p, tiles);
        Console.WriteLine($"seed=0x{seed:X16} size={size} hash=0x{WorldHash.Compute(seed, size, size, tiles):X16}");

        string root = FindArt();
        var art = new PackArt(root);
        var lay = new TerrainLayout(tiles, size, size);
        var field = new TerrainField(tiles, lay);
        var map = MapColors(root);
        var style = new TerrainStyle { Target = (b, band) => Vivid(MapColor(map, b, band), 150, 10) };
        Func<Biome, int, uint> mapColor = (b, band) => band >= 0 ? Vivid(MapColor(map, b, band), 110, 0) : Vivid(MapColor(map, b, band), 45, 18);   // neutral land muted, kingdoms pop
        var demo = DemoKingdoms(tiles, lay, size, root, out var capitals);
        foreach (var (dx, dy) in capitals) Console.WriteLine($"demo kingdom capital at cell {dx},{dy}");

        var sw = System.Diagnostics.Stopwatch.StartNew();
        var mid = TerrainComposer.ComposeZoom(tiles, lay, field, art, ZoomLayer.Mid, demo, style);
        var far = TerrainComposer.ComposeZoom(tiles, lay, field, art, ZoomLayer.Far, demo, style);
        var mapImg = TerrainComposer.ComposeZoom(tiles, lay, field, art, ZoomLayer.Map, demo, style, mapColor);
        Save(Path.Combine(outDir, "mid_whole.png"), mid, size * 4, size * 4, 1);
        Save(Path.Combine(outDir, "far_whole.png"), far, size * 2, size * 2, 1);
        Save(Path.Combine(outDir, "map_whole.png"), mapImg, size * 2, size * 2, 1);
        Console.WriteLine($"zoom layers in {sw.ElapsedMilliseconds} ms");

        // Per place (centre cellX cellY, near window n cells): near x2, and the four zooms side by side (512 px each).
        for (int i = 4; i + 2 < a.Length; i += 3)
        {
            int cx = int.Parse(a[i]), cy = int.Parse(a[i + 1]), n = int.Parse(a[i + 2]);
            int nx0 = Math.Clamp(cx - n / 2, 0, size - n), ny0 = Math.Clamp(cy - n / 2, 0, size - n);
            var near = TerrainComposer.ComposeNear(tiles, lay, field, art, nx0, ny0, n, n, true, out int w, out int h, style);
            Save(Path.Combine(outDir, $"{cx}_{cy}_near_x2.png"), near, w, h, 2);
            WriteQuad(Path.Combine(outDir, $"{cx}_{cy}_four_zooms.png"), tiles, lay, field, art, style, size, cx, cy, mid, far, mapImg);
        }
        return 0;
    }

    /// <summary>Near (32 cells, 16 px/cell), Mid (128 cells, 4 px), Far (256 cells, 2 px), Map (256 cells, 2 px), each
    /// 512 x 512, centred on the same place, in a 2 x 2 grid; the near window is outlined on the other three.</summary>
    static void WriteQuad(string path, TileData[] tiles, TerrainLayout lay, TerrainField field, IArtPixels art, TerrainStyle style,
                          int size, int cx, int cy, uint[] mid, uint[] far, uint[] map)
    {
        const int P = 512, Gap = 8;
        int W = P * 2 + Gap, H = P * 2 + Gap;
        var o = new uint[W * H];
        for (int i = 0; i < o.Length; i++) o[i] = Rgba.Pack(14, 16, 22);
        int n0 = 32, nx0 = Math.Clamp(cx - n0 / 2, 0, size - n0), ny0 = Math.Clamp(cy - n0 / 2, 0, size - n0);
        var near = TerrainComposer.ComposeNear(tiles, lay, field, art, nx0, ny0, n0, n0, true, out int nw, out _, style);
        Blit(o, W, 0, 0, near, nw, 0, 0, P);
        void Panel(uint[] src, int srcW, int ppc, int ox, int oy)
        {
            int cells = P / ppc;
            int sx0 = Math.Clamp(cx - cells / 2, 0, Math.Max(0, size - cells)), sy0 = Math.Clamp(cy - cells / 2, 0, Math.Max(0, size - cells));
            Blit(o, W, ox, oy, src, srcW, sx0 * ppc, sy0 * ppc, Math.Min(P, size * ppc));
            uint y = Rgba.Pack(255, 225, 90);
            int rx = ox + (nx0 - sx0) * ppc, ry = oy + (ny0 - sy0) * ppc, rs = n0 * ppc;
            for (int k = 0; k <= rs; k++)
            {
                Put(o, W, rx + k, ry, y); Put(o, W, rx + k, ry + rs, y); Put(o, W, rx, ry + k, y); Put(o, W, rx + rs, ry + k, y);
            }
        }
        Panel(mid, size * 4, 4, P + Gap, 0);
        Panel(far, size * 2, 2, 0, P + Gap);
        Panel(map, size * 2, 2, P + Gap, P + Gap);
        Save(path, o, W, H, 1);
    }

    static void Blit(uint[] dst, int dstW, int ox, int oy, uint[] src, int srcW, int sx, int sy, int n)
    {
        int srcH = src.Length / srcW;
        for (int y = 0; y < n && sy + y < srcH; y++)
            for (int x = 0; x < n && sx + x < srcW; x++)
                dst[(oy + y) * dstW + ox + x] = src[(sy + y) * srcW + sx + x];
    }

    static void Put(uint[] img, int W, int x, int y, uint c) { if (x >= 0 && y >= 0 && x < W && y * W + x < img.Length) img[y * W + x] = c; }

    /// <summary>
    /// DEMO data only (the simulation has no kingdoms until milestone B4): three kingdoms on open lowland far apart,
    /// each a capital, a town and villages linked by roads over land, farms around them, plus an army between two
    /// kingdoms, a monster in the mountains and a fire. Deterministic from the world.
    /// </summary>
    static FarOverlay DemoKingdoms(TileData[] tiles, TerrainLayout lay, int size, string artRoot, out List<(int, int)> capitals)
    {
        var o = new FarOverlay();
        capitals = new List<(int, int)>();
        string json = File.ReadAllText(Path.Combine(artRoot, "..", "WorldSimData", "kingdom_palettes.json"));
        using var doc = System.Text.Json.JsonDocument.Parse(json);
        foreach (string name in new[] { "scarlet", "azure", "gold" })
            foreach (var p in doc.RootElement.GetProperty("palettes").EnumerateArray())
                if (p.GetProperty("name").GetString() == name)
                {
                    var ramp = new uint[5];
                    int k = 0;
                    foreach (var c in p.GetProperty("team").EnumerateArray())
                    {
                        string h = c.GetString();
                        ramp[k++] = Rgba.Pack(Convert.ToInt32(h.Substring(1, 2), 16), Convert.ToInt32(h.Substring(3, 2), 16), Convert.ToInt32(h.Substring(5, 2), 16));
                    }
                    o.TeamRamps.Add(ramp);
                }

        bool Open(int x, int y)
        {
            if (x < 2 || y < 2 || x >= size - 2 || y >= size - 2) return false;
            var t = tiles[y * size + x];
            return !t.IsWater && lay.Level[y * size + x] <= 5 &&
                   (t.Biome == Biome.Meadow || t.Biome == Biome.FlowerField || t.Biome == Biome.Savanna || t.Biome == Biome.Steppe || t.Biome == Biome.Forest);
        }
        bool LandLine(int x0, int y0, int x1, int y1)
        {
            int n = Math.Max(Math.Abs(x1 - x0), Math.Abs(y1 - y0));
            for (int i = 0; i <= n; i++)
            {
                int x = x0 + (x1 - x0) * i / Math.Max(1, n), y = y0 + (y1 - y0) * i / Math.Max(1, n);
                if (tiles[y * size + x].IsWater || lay.Level[y * size + x] >= 9) return false;
            }
            return true;
        }

        var used = new List<(int x, int y)>();
        for (int k = 0; k < 3; k++)
        {
            (int x, int y) best = (-1, -1); int bestScore = -1;
            for (int y = 6; y < size - 6; y += 3)
                for (int x = 6; x < size - 6; x += 3)
                {
                    if (!Open(x, y)) continue;
                    int open = 0;
                    for (int dy = -4; dy <= 4; dy++) for (int dx = -4; dx <= 4; dx++) if (Open(x + dx, y + dy)) open++;
                    int far = int.MaxValue;
                    foreach (var u in used) far = Math.Min(far, Math.Abs(u.x - x) + Math.Abs(u.y - y));
                    if (used.Count > 0 && far < 70) continue;
                    int score = open * 4 + (used.Count > 0 ? Math.Min(far, 120) : 0) + (int)(TerrainLayout.Hash(x, y) & 15);
                    if (score > bestScore) { bestScore = score; best = (x, y); }
                }
            if (best.x < 0) break;
            used.Add(best);
            capitals.Add(best);
            o.Markers.Add(new FarOverlay.Marker { Frame = "mk_capital", CellX = best.x, CellY = best.y, Kingdom = k });
            int placed = 0;
            for (int a = 0; a < 16 && placed < 4; a++)
            {
                double ang = a * 2.399 + k;
                int r = 9 + (a % 3) * 4;
                int vx = best.x + (int)(Math.Cos(ang) * r), vy = best.y + (int)(Math.Sin(ang) * r);
                if (!Open(vx, vy) || !LandLine(best.x, best.y, vx, vy)) continue;
                o.Markers.Add(new FarOverlay.Marker { Frame = placed == 0 ? "mk_town" : "mk_village", CellX = vx, CellY = vy, Kingdom = k });
                o.Roads.Add(new[] { best.x, best.y, vx, vy });
                for (int fy = -2; fy <= 2; fy++)
                    for (int fx = -2; fx <= 2; fx++)
                        if ((Math.Abs(fx) + Math.Abs(fy)) >= 2 && (TerrainLayout.Hash(vx + fx, vy + fy) & 3) == 0 && Open(vx + fx, vy + fy))
                            o.Farms.Add(new FarOverlay.Farm { CellX = vx + fx, CellY = vy + fy });
                placed++;
            }
        }
        if (used.Count >= 2)
        {
            // An army marching out of the first capital towards the second: the last land cell 10-16 cells along.
            int ax = -1, ay = -1;
            for (int d = 10; d <= 16; d++)
            {
                double len = Math.Sqrt(Math.Pow(used[1].x - used[0].x, 2) + Math.Pow(used[1].y - used[0].y, 2));
                int x = used[0].x + (int)((used[1].x - used[0].x) * d / len), y = used[0].y + (int)((used[1].y - used[0].y) * d / len);
                if (x < 0 || y < 0 || x >= size || y >= size || tiles[y * size + x].IsWater) break;
                ax = x; ay = y;
            }
            if (ax >= 0) o.Markers.Add(new FarOverlay.Marker { Frame = "mk_army", CellX = ax, CellY = ay, Kingdom = 0 });
        }
        for (int y = 4; y < size - 4; y += 7)
            for (int x = 4; x < size - 4; x += 7)
                if (lay.Level[y * size + x] == 10 && !o.Markers.Exists(m => m.Frame == "mk_monster"))
                    o.Markers.Add(new FarOverlay.Marker { Frame = "mk_monster", CellX = x, CellY = y, Kingdom = -1 });
        if (used.Count >= 3)
            o.Markers.Add(new FarOverlay.Marker { Frame = "mk_fire", CellX = used[2].x + 6, CellY = used[2].y - 5, Kingdom = -1 });
        // Territory: land within 16 cells of a kingdom's settlement, nearest settlement wins.
        o.TerritoryWidth = size;
        o.Territory = new byte[size * size];
        for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                if (tiles[y * size + x].IsWater) continue;
                int best = -1, bestD = 16 * 16 + 1;
                foreach (var m in o.Markers)
                {
                    if (m.Kingdom < 0 || m.Frame == "mk_army") continue;
                    int d = (m.CellX - x) * (m.CellX - x) + (m.CellY - y) * (m.CellY - y);
                    if (d < bestD) { bestD = d; best = m.Kingdom; }
                }
                if (best >= 0) o.Territory[y * size + x] = (byte)(best + 1);
            }
        return o;
    }

    static Dictionary<string, uint> MapColors(string root)
    {
        var d = new Dictionary<string, uint>();
        using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "..", "WorldSimData", "lod.json")));
        foreach (var e in doc.RootElement.GetProperty("map_colors").EnumerateObject())
        {
            string h = e.Value.GetString();
            d[e.Name] = Rgba.Pack(Convert.ToInt32(h.Substring(1, 2), 16), Convert.ToInt32(h.Substring(3, 2), 16), Convert.ToInt32(h.Substring(5, 2), 16));
        }
        return d;
    }

    static uint Vivid(uint c, int sat, int bright)
    {
        int r = Rgba.R(c), g = Rgba.G(c), b = Rgba.B(c), l = (r * 30 + g * 59 + b * 11) / 100;
        return Rgba.Pack(l + (r - l) * sat / 100 + bright, l + (g - l) * sat / 100 + bright, l + (b - l) * sat / 100 + bright);
    }

    static uint MapColor(Dictionary<string, uint> map, Biome b, int band)
    {
        string key = band >= 0 && !(b == Biome.CoralShallows && band == 2) ? "water_depth_" + Math.Min(2, band) : BiomeArt.MapColorKey(b);
        return key != null && map.TryGetValue(key, out uint c) ? c : Rgba.Pack(255, 0, 255);
    }

    static string FindArt()
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d != null; d = d.Parent)
        {
            string r = Path.Combine(d.FullName, "Assets", "WorldSim", "Resources", "WorldSimArt");
            if (File.Exists(Path.Combine(r, "art_index.bytes"))) return r;
        }
        throw new FileNotFoundException("art_index.bytes");
    }

    /// <summary>Top-down image -> PNG via Program.WritePng (which expects bottom-up rows), scaled up by <paramref name="up"/>.</summary>
    static void Save(string path, uint[] img, int w, int h, int up)
    {
        var flipped = new uint[img.Length];
        for (int y = 0; y < h; y++) Array.Copy(img, y * w, flipped, (h - 1 - y) * w, w);
        Program.WritePng(path, flipped, w, 0, 0, w, h, 1, up);
    }
}
