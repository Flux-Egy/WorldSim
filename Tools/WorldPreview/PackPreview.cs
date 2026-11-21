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
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var lay = new TerrainLayout(tiles, size, size);
        var field = new TerrainField(tiles, lay);
        var demo = DemoKingdoms(tiles, lay, size, root, out var demoPlaces);
        var far = TerrainComposer.ComposeFar(tiles, lay, field, art, 4, demo);
        var map = TerrainComposer.ComposeFar(tiles, lay, field, art, 2, demo);
        foreach (var (dx, dy) in demoPlaces) Console.WriteLine($"demo kingdom capital at cell {dx},{dy}");
        Save(Path.Combine(outDir, "far_quarter.png"), far, size * 4, size * 4, 1);
        Save(Path.Combine(outDir, "far_eighth.png"), map, size * 2, size * 2, 1);
        Console.WriteLine($"far in {sw.ElapsedMilliseconds} ms");
        // Each place (cellX cellY cells): near = x2 of the window, mid = x1 of a window twice as big around it,
        // far = the same area at zoom 1/4, enlarged x4 so its pixels can be judged.
        for (int i = 4; i + 2 < a.Length; i += 3)
        {
            int cx = int.Parse(a[i]), cy = int.Parse(a[i + 1]), n = int.Parse(a[i + 2]);
            string tag = $"{cx}_{cy}";
            var near = TerrainComposer.ComposeNear(tiles, lay, field, art, cx, cy, n, n, true, out int w, out int h);
            Save(Path.Combine(outDir, $"{tag}_near_x2.png"), near, w, h, 2);
            int mx = Math.Max(0, cx - n / 2), my = Math.Max(0, cy - n / 2), mn = Math.Min(2 * n, Math.Min(size - mx, size - my));
            var mid = TerrainComposer.ComposeNear(tiles, lay, field, art, mx, my, mn, mn, true, out int mw, out int mh);
            Save(Path.Combine(outDir, $"{tag}_mid_x1.png"), mid, mw, mh, 1);
            var crop = new uint[mn * 4 * mn * 4];
            for (int y = 0; y < mn * 4; y++) Array.Copy(far, (my * 4 + y) * size * 4 + mx * 4, crop, y * mn * 4, mn * 4);
            Save(Path.Combine(outDir, $"{tag}_far_quarter_x4.png"), crop, mn * 4, mn * 4, 4);
        }
        Console.WriteLine($"done in {sw.ElapsedMilliseconds} ms");
        return 0;
    }

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
        return o;
    }

    /// <summary>
    /// Art-style candidates for the same place (Playable Alpha step 1): writes style_A/B/C.png (near, x2) and
    /// styles_compare.png (all three stacked, labelled).
    ///   A = our pack, improved (brighter, more saturated, calmer texture)
    ///   B = flat bright palette (WorldBox-like: clean colour, 3 soft tones, sparse speckles)
    ///   C = Kenney "Roguelike pack" ground tiles (CC0), tinted per biome
    /// </summary>
    public static int Styles(string[] a)
    {
        ulong seed = Convert.ToUInt64(a[1].Replace("0x", ""), 16);
        int size = int.Parse(a[2]); string outDir = a[3]; string kenneySheet = a[4];
        int cx = int.Parse(a[5]), cy = int.Parse(a[6]), n = int.Parse(a[7]);
        Directory.CreateDirectory(outDir);
        var p = WorldGenParams.Create(new WorldSeed(seed), size, size);
        var tiles = new TileData[size * size];
        WorldGenerator.Generate(p, tiles);
        string root = FindArt();
        var art = new PackArt(root);
        var lay = new TerrainLayout(tiles, size, size);
        var field = new TerrainField(tiles, lay);

        var map = MapColors(root);
        var styles = new (string tag, string label, TerrainStyle style)[]
        {
            ("A", "A: our pack, improved", new TerrainStyle { Saturation = 135, Brightness = 8, Calm = 45 }),
            ("B", "B: flat bright palette", new TerrainStyle { Ground = FlatGround(map) }),
            ("C", "C: Kenney Roguelike pack (CC0), tinted", new TerrainStyle { Ground = KenneyGround(kenneySheet, map) }),
        };
        var panels = new List<(string, uint[], int, int)>();
        foreach (var (tag, label, style) in styles)
        {
            var img = TerrainComposer.ComposeNear(tiles, lay, field, art, cx, cy, n, n, true, out int w, out int h, style);
            Save(Path.Combine(outDir, $"style_{tag}.png"), img, w, h, 2);
            panels.Add((label, img, w, h));
        }
        // Stack the three, labelled, for the phone (portrait).
        int pw = panels[0].Item3, ph = panels[0].Item4, gap = 14;
        int W = pw, H = (ph + gap) * panels.Count;
        var all = new uint[W * H];
        for (int i = 0; i < all.Length; i++) all[i] = Rgba.Pack(18, 20, 28);
        for (int k = 0; k < panels.Count; k++)
            Array.Copy(panels[k].Item2, 0, all, (k * (ph + gap) + gap) * W, pw * ph);
        Save(Path.Combine(outDir, "styles_compare.png"), all, W, H, 2);
        Console.WriteLine("labels top to bottom: " + string.Join(" | ", panels.ConvertAll(x => x.Item1)));
        return 0;
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

    /// <summary>B: one clean, vivid colour per biome; three soft tones in ~12 px blobs; rare 1 px light speckles.</summary>
    static Func<Biome, int, int, int, uint> FlatGround(Dictionary<string, uint> map) => (b, band, x, y) =>
    {
        uint basec = Vivid(MapColor(map, b, band), 150, 10);
        int n = TerrainField.Noise(x * 2 / 3, y * 2 / 3, 0x4455);
        int tone = n > 40 ? 7 : n < -40 ? -7 : 0;
        uint c = Rgba.Shift(basec, tone);
        uint hsh = TerrainLayout.Hash(x * 7 + 3, y * 13 + 5);
        if (band < 0 && (hsh & 255) < 3) c = Rgba.Shift(basec, 22);                                  // sparse speckle
        if (band >= 0 && (hsh & 511) < 2) c = Rgba.Shift(basec, 40);                                 // water glints
        return c;
    };

    /// <summary>C: Kenney Roguelike pack ground tiles (16 px, 1 px margin), tinted towards each biome's colour.</summary>
    static Func<Biome, int, int, int, uint> KenneyGround(string sheetPath, Dictionary<string, uint> map)
    {
        var px = PngDecoder.Decode(File.ReadAllBytes(sheetPath), out int sw, out int sh);
        uint At(int tx, int ty, int x, int y) => px[(sh - 1 - (ty * 17 + y)) * sw + tx * 17 + x];
        (int, int) TileFor(Biome b, int band)
        {
            if (band >= 0 && !(b == Biome.CoralShallows && band == 2)) return (0, 0);                   // water
            switch (b)
            {
                case Biome.Beach: case Biome.DesertDunes: case Biome.SaltFlats: case Biome.Savanna: return (8, 0);   // sand
                case Biome.Mountain: case Biome.RockyHighland: case Biome.Volcanic: case Biome.AshWaste: return (7, 0); // stone
                case Biome.Snow: case Biome.Glacier: return (8, 0);
                case Biome.Badlands: case Biome.Farmland: case Biome.EmberWastes: return (6, 0);                   // dirt
                default: return (5, 0);                                                                          // grass
            }
        }
        var means = new Dictionary<(int, int), uint>();
        uint Mean((int, int) t)
        {
            if (means.TryGetValue(t, out uint m)) return m;
            long r = 0, g = 0, bl = 0;
            for (int y = 0; y < 16; y++) for (int x = 0; x < 16; x++) { uint c = At(t.Item1, t.Item2, x, y); r += Rgba.R(c); g += Rgba.G(c); bl += Rgba.B(c); }
            return means[t] = Rgba.Pack((int)(r / 256), (int)(g / 256), (int)(bl / 256));
        }
        return (b, band, x, y) =>
        {
            var t = TileFor(b, band);
            uint c = At(t.Item1, t.Item2, x & 15, y & 15), mean = Mean(t), target = Vivid(MapColor(map, b, band), 140, 12);
            // keep the tile's light/dark detail, move its average to the biome colour
            return Rgba.Pack(Rgba.R(target) + Rgba.R(c) - Rgba.R(mean), Rgba.G(target) + Rgba.G(c) - Rgba.G(mean), Rgba.B(target) + Rgba.B(c) - Rgba.B(mean));
        };
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
