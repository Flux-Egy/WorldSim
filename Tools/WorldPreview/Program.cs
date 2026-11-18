// Renders a generated world to PNG with the exact Core + Render sources the game compiles.
//
//   dotnet run -c Release --project Tools/WorldPreview -- <seedHex> <size> <out.png> [cropX cropY cropTiles]
//
// Writes the full map (texture at the game's pixels-per-tile) and, if a crop is given, a second
// image "<out>.crop.png" of that tile window at full resolution. Prints the world hash.
using System;
using System.IO;
using System.IO.Compression;
using WorldSim.Core;
using WorldSim.Render;

struct ArrayTiles : ITileSource { public TileData[] A; public TileData Get(int i) => A[i]; }
struct ArrayPixels : IPixelTarget { public uint[] A; public uint Get(int i) => A[i]; public void Set(int i, uint c) => A[i] = c; }
struct ArrayAtlas : IAtlasSource { public uint[] A; public uint Get(int i) => A[i]; }

static class Program
{
    static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "icons") return IconSheet(args[1]);
        if (args.Length == 2 && args[0] == "sprites") return SpriteSheet(args[1]);
        if (args.Length == 2 && args[0] == "creatures") return CreatureSheet(args[1]);
        if (args.Length < 3) { Console.Error.WriteLine("usage: WorldPreview <seedHex> <size> <out.png> [cropX cropY cropTiles]"); return 2; }
        ulong seed = Convert.ToUInt64(args[0].Replace("0x", ""), 16);
        int size = int.Parse(args[1]);
        var p = WorldGenParams.Create(new WorldSeed(seed), size, size);
        var tiles = new TileData[size * size];
        var sw = System.Diagnostics.Stopwatch.StartNew();
        WorldGenerator.Generate(p, tiles);
        long genMs = sw.ElapsedMilliseconds;
        ulong hash = WorldHash.Compute(seed, size, size, tiles);

        int ppt = TerrainPainter.PixelsPerTileFor(size, size);
        int texW = size * ppt;
        var px = new uint[texW * texW];
        var t = new ArrayTiles { A = tiles }; var pix = new ArrayPixels { A = px }; var atlas = new ArrayAtlas { A = SpriteLibrary.Build() };
        sw.Restart();
        for (int row = 0; row < size; row++) TerrainPainter.PaintGroundRow(ref t, ref pix, size, size, ppt, row);
        TerrainPainter.PaintDecorations(ref t, ref pix, ref atlas, size, size, ppt);
        long paintMs = sw.ElapsedMilliseconds;

        var counts = new int[256]; var decos = new int[256];
        foreach (var x in tiles) { counts[x.BiomeId]++; decos[x.DecorationId]++; }
        Console.WriteLine($"seed=0x{seed:X16} size={size} hash=0x{hash:X16} gen={genMs}ms paint={paintMs}ms ppt={ppt}");
        Console.Write("  biomes:");
        foreach (Biome b in Enum.GetValues(typeof(Biome))) if ((int)b < 128 && counts[(int)b] > 0) Console.Write($" {b}={100.0 * counts[(int)b] / tiles.Length:F1}%");
        Console.WriteLine();
        Console.WriteLine($"  decorated tiles: {100.0 * (tiles.Length - decos[0]) / tiles.Length:F1}%");

        WritePng(args[2], px, texW, 0, 0, texW, texW, Math.Max(1, texW / 1024));
        int opp = TerrainPainter.OverviewPixelsPerTile(size, size);
        if (opp > 0)
        {
            int ow = size * opp;
            var ov = new uint[ow * ow]; var ovp = new ArrayPixels { A = ov };
            for (int row = 0; row < size; row++) TerrainPainter.PaintOverviewRow(ref t, ref ovp, size, size, opp, row);
            WritePng(Path.ChangeExtension(args[2], ".overview.png"), ov, ow, 0, 0, ow, ow, 1);
        }
        if (args.Length >= 6)
        {
            int cx = int.Parse(args[3]) * ppt, cy = int.Parse(args[4]) * ppt, cs = int.Parse(args[5]) * ppt;
            WritePng(Path.ChangeExtension(args[2], ".crop.png"), px, texW, cx, cy, cs, cs, 1, args.Length > 6 ? int.Parse(args[6]) : 1);
        }
        return 0;
    }

    /// <summary>All toolbar icons in a row, 6x scale, on a mid-grey background.</summary>
    static int IconSheet(string path)
    {
        int n = (int)Icon.Count, s = IconLibrary.Size, w = n * (s + 2);
        var px = new uint[w * (s + 2)];
        for (int i = 0; i < px.Length; i++) px[i] = Rgba.Pack(70, 78, 70);
        for (int k = 0; k < n; k++)
        {
            uint[] ic = IconLibrary.Build((Icon)k);
            for (int y = 0; y < s; y++) for (int x = 0; x < s; x++) if (ic[y * s + x] != 0) px[(y + 1) * w + k * (s + 2) + 1 + x] = ic[y * s + x];
        }
        WritePng(path, px, w, 0, 0, w, s + 2, 1, 6);
        return 0;
    }

    /// <summary>Every species (columns) x animation frame (rows) on grass, 8x scale.</summary>
    static int CreatureSheet(string path)
    {
        int c = WorldSim.Render.CreatureSprites.Cell, n = WorldSim.Core.Life.SpeciesTable.All.Length;
        int w = n * (c + 2), h = 2 * (c + 2);
        var px = new uint[w * h];
        for (int i = 0; i < px.Length; i++) px[i] = Rgba.Pack(104, 174, 64);
        uint[] atlas = WorldSim.Render.CreatureSprites.Build();
        for (int s = 0; s < n; s++)
            for (int f = 0; f < 2; f++)
            {
                int start = (s * 2 + f) * c * c, ox = s * (c + 2) + 1, oy = (1 - f) * (c + 2) + 1;
                for (int y = 0; y < c; y++) for (int x = 0; x < c; x++)
                {
                    uint col = atlas[start + y * c + x];
                    if (col == 0) continue;
                    int i = (oy + y) * w + ox + x;
                    px[i] = Rgba.A(col) < 255 ? Rgba.Darken(px[i], 74) : col;
                }
            }
        WritePng(path, px, w, 0, 0, w, h, 1, 8);
        return 0;
    }

    /// <summary>Every decoration sprite (rows) and variant (columns) on grass, 6x scale.</summary>
    static int SpriteSheet(string path)
    {
        int c = SpriteLibrary.Cell, rows = (int)Decoration.Count - 1, cols = SpriteLibrary.Variants;
        int w = cols * (c + 2), h = rows * (c + 2);
        var px = new uint[w * h];
        for (int i = 0; i < px.Length; i++) px[i] = Rgba.Pack(104, 174, 64);
        uint[] atlas = SpriteLibrary.Build();
        for (int d = 1; d <= rows; d++)
            for (int v = 0; v < cols; v++)
            {
                int start = SpriteLibrary.CellIndex((Decoration)d, v) * SpriteLibrary.CellPixels;
                int ox = v * (c + 2) + 1, oy = (rows - d) * (c + 2) + 1;
                for (int y = 0; y < c; y++) for (int x = 0; x < c; x++)
                {
                    uint col = atlas[start + y * c + x];
                    if (col == 0) continue;
                    int i = (oy + y) * w + ox + x;
                    px[i] = Rgba.A(col) < 255 ? Rgba.Darken(px[i], 74) : col;
                }
            }
        WritePng(path, px, w, 0, 0, w, h, 1, 6);
        return 0;
    }

    /// <summary>Writes a window of the bottom-up RGBA texture as a top-down RGB PNG, optionally downscaled.</summary>
    static void WritePng(string path, uint[] px, int texW, int x0, int y0, int w, int h, int down, int up = 1)
    {
        int ow = w / down * up, oh = h / down * up;
        var rgb = new byte[ow * oh * 3];
        for (int oy = 0; oy < oh; oy++)
            for (int ox = 0; ox < ow; ox++)
            {
                int gx = x0 + ox / up * down, gy = y0 + (oh - 1 - oy) / up * down;
                uint c = px[gy * texW + gx];
                int i = (oy * ow + ox) * 3;
                rgb[i] = (byte)Rgba.R(c); rgb[i + 1] = (byte)Rgba.G(c); rgb[i + 2] = (byte)Rgba.B(c);
            }
        using var fs = File.Create(path);
        fs.Write(new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 });
        var ihdr = new byte[13]; BE(ihdr, 0, (uint)ow); BE(ihdr, 4, (uint)oh); ihdr[8] = 8; ihdr[9] = 2;
        Chunk(fs, "IHDR", ihdr);
        using var raw = new MemoryStream();
        for (int y = 0; y < oh; y++) { raw.WriteByte(0); raw.Write(rgb, y * ow * 3, ow * 3); }
        using var z = new MemoryStream();
        using (var zs = new ZLibStream(z, CompressionLevel.Fastest, true)) raw.WriteTo(zs);
        Chunk(fs, "IDAT", z.ToArray());
        Chunk(fs, "IEND", Array.Empty<byte>());
    }

    static void Chunk(Stream s, string type, byte[] data)
    {
        var len = new byte[4]; BE(len, 0, (uint)data.Length); s.Write(len);
        var td = new byte[4 + data.Length];
        for (int i = 0; i < 4; i++) td[i] = (byte)type[i];
        Buffer.BlockCopy(data, 0, td, 4, data.Length);
        s.Write(td);
        var crc = new byte[4]; BE(crc, 0, Crc(td)); s.Write(crc);
    }

    static void BE(byte[] b, int o, uint v) { unchecked { b[o] = (byte)(v >> 24); b[o + 1] = (byte)(v >> 16); b[o + 2] = (byte)(v >> 8); b[o + 3] = (byte)v; } }

    static uint Crc(byte[] d)
    {
        uint c = 0xFFFFFFFF;
        foreach (byte x in d) { c ^= x; for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320 ^ (c >> 1) : c >> 1; }
        return ~c;
    }
}
