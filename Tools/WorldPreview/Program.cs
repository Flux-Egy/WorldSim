// Renders a generated world to a PNG using the exact Core sources the game compiles.
//
//   dotnet run -c Release --project Tools/WorldPreview -- <seedHex> <size> <out.png> [scale]
//
// Prints the world hash so it can be compared with the in-game value (§4.3).
using System;
using System.IO;
using System.IO.Compression;
using WorldSim.Core;

static class Program
{
    static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.Error.WriteLine("usage: WorldPreview <seedHex> <size> <out.png> [scale]");
            return 2;
        }
        ulong seed = Convert.ToUInt64(args[0].Replace("0x", ""), 16);
        int size = int.Parse(args[1]);
        int scale = args.Length > 3 ? int.Parse(args[3]) : 1;

        var p = WorldGenParams.Create(new WorldSeed(seed), size, size);
        var tiles = new TileData[size * size];
        var sw = System.Diagnostics.Stopwatch.StartNew();
        WorldGenerator.Generate(p, tiles);
        sw.Stop();
        ulong hash = WorldHash.Compute(seed, size, size, tiles);

        var counts = new int[256];
        foreach (var t in tiles) counts[t.BiomeId]++;
        Console.WriteLine($"seed=0x{seed:X16} size={size} hash=0x{hash:X16} gen={sw.ElapsedMilliseconds}ms");
        foreach (Biome b in Enum.GetValues(typeof(Biome)))
            if ((int)b < 128) Console.WriteLine($"  {b,-13} {100.0 * counts[(int)b] / tiles.Length,5:F1}%");

        int w = size * scale;
        var rgb = new byte[w * w * 3];
        for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                var t = tiles[y * size + x];
                (byte r, byte g, byte b) = Color(t);
                for (int sy = 0; sy < scale; sy++)
                    for (int sx = 0; sx < scale; sx++)
                    {
                        // PNG rows go top-down; world y=0 is the bottom (Unity convention).
                        int py = (size - 1 - y) * scale + sy, px = x * scale + sx;
                        int i = (py * w + px) * 3;
                        rgb[i] = r; rgb[i + 1] = g; rgb[i + 2] = b;
                    }
            }
        WritePng(args[2], w, w, rgb);
        return 0;
    }

    // Same palette the game uses (kept in sync with Presentation's TerrainPalette by hand).
    static (byte, byte, byte) Color(TileData t)
    {
        (int r, int g, int b) c = (Biome)t.BiomeId switch
        {
            Biome.DeepWater => (28, 62, 122),
            Biome.ShallowWater => (52, 112, 178),
            Biome.Sand => (222, 204, 140),
            Biome.Grass => (104, 168, 72),
            Biome.Forest => (44, 112, 52),
            Biome.Mountain => (128, 120, 112),
            Biome.Snow => (236, 240, 246),
            _ => (255, 0, 255),
        };
        int shade = (t.Height - 128) / 6; // subtle relief
        if (t.Has(ResourceFlags.Gold)) c = (232, 196, 48);
        else if (t.Has(ResourceFlags.Gems)) c = (176, 72, 200);
        else if (t.BiomeId == (byte)Biome.Grass && t.Has(ResourceFlags.Wood)) c = (60, 128, 56);
        return (Clamp(c.r + shade), Clamp(c.g + shade), Clamp(c.b + shade));
    }

    static byte Clamp(int v) => (byte)(v < 0 ? 0 : v > 255 ? 255 : v);

    static void WritePng(string path, int w, int h, byte[] rgb)
    {
        using var fs = File.Create(path);
        fs.Write(new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 });
        var ihdr = new byte[13];
        BE(ihdr, 0, (uint)w); BE(ihdr, 4, (uint)h);
        ihdr[8] = 8; ihdr[9] = 2; // 8-bit RGB
        Chunk(fs, "IHDR", ihdr);
        using var raw = new MemoryStream();
        for (int y = 0; y < h; y++) { raw.WriteByte(0); raw.Write(rgb, y * w * 3, w * 3); }
        using var z = new MemoryStream();
        using (var zs = new ZLibStream(z, CompressionLevel.Optimal, true)) raw.WriteTo(zs);
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
        foreach (byte x in d)
        {
            c ^= x;
            for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320 ^ (c >> 1) : c >> 1;
        }
        return ~c;
    }
}
