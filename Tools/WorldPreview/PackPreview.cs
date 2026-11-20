// The new terrain look (rebuild phase 2) rendered from the real art pack, without Unity:
//
//   dotnet run -c Release --project Tools/WorldPreview -- pack <seedHex> <size> <outDir> [cropX cropY cropTiles ...]
//
// Writes the whole map at zoom 1/4 (far_quarter.png, lod16 tiles) and 1/8 (far_eighth.png, lod8 tiles), and per
// (cellX cellY cells) place: near (x2), mid (x1, twice the area) and the same area at zoom 1/4 enlarged x4.
using System;
using System.Collections.Generic;
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
        var far = TerrainComposer.ComposeFar(tiles, lay, field, art, 4);
        var map = TerrainComposer.ComposeFar(tiles, lay, field, art, 2);
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
