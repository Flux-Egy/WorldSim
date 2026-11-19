using System;
using System.IO;
using System.IO.Compression;
using NUnit.Framework;
using WorldSim.Render;

namespace WorldSim.Tests
{
    public class PngDecoderTests
    {
        // Builds a PNG in memory with a known pattern, using every row filter (0-4) so the
        // decoder's un-filtering is exercised, then checks the decoded pixels match exactly.
        [TestCase(6)] // RGBA
        [TestCase(2)] // RGB
        [TestCase(3)] // palette + tRNS
        public void Decode_RoundTripsEveryFilter(int colorType)
        {
            const int w = 7, h = 10;
            var expected = new uint[w * h]; // top-down here; decoder returns bottom-up
            var palette = new uint[] { 0, Rgba.Pack(200, 30, 40), Rgba.Pack(10, 220, 90, 128), Rgba.Pack(250, 250, 250) };
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    uint c = colorType == 3 ? palette[(x * 3 + y) % 4]
                        : Rgba.Pack((x * 37 + y * 11) & 255, (x * 5 + y * 70) & 255, (x * y * 13) & 255, colorType == 6 ? (x + y) % 3 == 0 ? 0 : 255 - y * 9 : 255);
                    if (Rgba.A(c) == 0) c = 0;
                    expected[y * w + x] = c;
                }

            byte[] png = Encode(expected, w, h, colorType, palette);
            uint[] got = PngDecoder.Decode(png, out int gw, out int gh);
            Assert.AreEqual(w, gw);
            Assert.AreEqual(h, gh);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                    Assert.AreEqual(expected[y * w + x], got[(h - 1 - y) * w + x], $"pixel {x},{y}");
        }

        [Test]
        public void Decode_RejectsNonPng()
        {
            Assert.Throws<InvalidDataException>(() => PngDecoder.Decode(new byte[] { 1, 2, 3, 4, 5, 6, 7, 8, 9 }, out _, out _));
        }

        static byte[] Encode(uint[] px, int w, int h, int colorType, uint[] palette)
        {
            int ch = colorType == 6 ? 4 : colorType == 2 ? 3 : 1;
            int stride = w * ch;
            var raw = new MemoryStream();
            var prev = new byte[stride];
            for (int y = 0; y < h; y++)
            {
                var cur = new byte[stride];
                for (int x = 0; x < w; x++)
                {
                    uint c = px[y * w + x];
                    int i = x * ch;
                    if (colorType == 3) cur[i] = (byte)Array.IndexOf(palette, c);
                    else
                    {
                        cur[i] = (byte)Rgba.R(c); cur[i + 1] = (byte)Rgba.G(c); cur[i + 2] = (byte)Rgba.B(c);
                        if (ch == 4) cur[i + 3] = (byte)Rgba.A(c);
                    }
                }
                int filter = y % 5;
                raw.WriteByte((byte)filter);
                for (int i = 0; i < stride; i++)
                {
                    int a = i >= ch ? cur[i - ch] : 0, b = prev[i], c = i >= ch ? prev[i - ch] : 0;
                    int pred = filter == 0 ? 0 : filter == 1 ? a : filter == 2 ? b : filter == 3 ? (a + b) >> 1 : Paeth(a, b, c);
                    raw.WriteByte(unchecked((byte)(cur[i] - pred)));
                }
                prev = cur;
            }

            var outS = new MemoryStream();
            outS.Write(new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 }, 0, 8);
            var ihdr = new byte[13];
            Be(ihdr, 0, w); Be(ihdr, 4, h);
            ihdr[8] = 8; ihdr[9] = (byte)colorType;
            Chunk(outS, "IHDR", ihdr);
            if (colorType == 3)
            {
                var plte = new byte[palette.Length * 3];
                var trns = new byte[palette.Length];
                for (int k = 0; k < palette.Length; k++)
                {
                    plte[k * 3] = (byte)Rgba.R(palette[k]); plte[k * 3 + 1] = (byte)Rgba.G(palette[k]); plte[k * 3 + 2] = (byte)Rgba.B(palette[k]);
                    trns[k] = (byte)Rgba.A(palette[k]);
                }
                Chunk(outS, "PLTE", plte);
                Chunk(outS, "tRNS", trns);
            }
            var z = new MemoryStream();
            z.WriteByte(0x78); z.WriteByte(0x9C);
            using (var d = new DeflateStream(z, CompressionMode.Compress, true)) raw.WriteTo(d);
            z.Write(new byte[4], 0, 4); // Adler-32 (ignored by the decoder)
            Chunk(outS, "IDAT", z.ToArray());
            Chunk(outS, "IEND", new byte[0]);
            return outS.ToArray();
        }

        static int Paeth(int a, int b, int c)
        {
            int p = a + b - c, pa = Math.Abs(p - a), pb = Math.Abs(p - b), pc = Math.Abs(p - c);
            return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
        }

        static void Be(byte[] a, int o, int v)
        {
            unchecked { a[o] = (byte)(v >> 24); a[o + 1] = (byte)(v >> 16); a[o + 2] = (byte)(v >> 8); a[o + 3] = (byte)v; }
        }

        static void Chunk(Stream s, string type, byte[] data)
        {
            var len = new byte[4];
            Be(len, 0, data.Length);
            s.Write(len, 0, 4);
            for (int i = 0; i < 4; i++) s.WriteByte((byte)type[i]);
            s.Write(data, 0, data.Length);
            s.Write(new byte[4], 0, 4); // CRC (ignored by the decoder)
        }
    }
}
