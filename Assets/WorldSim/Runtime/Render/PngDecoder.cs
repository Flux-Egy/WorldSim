using System;
using System.IO;
using System.IO.Compression;

namespace WorldSim.Render
{
    /// <summary>
    /// Minimal PNG decoder for the game's own art files (8-bit RGB, RGBA, grey, grey+alpha and
    /// palette images, non-interlaced). Pure C#, so the game and Tools/WorldPreview decode the
    /// exact same pixels, and pixel art never goes through texture import settings (which would
    /// filter or compress it on Android). Output rows are bottom-up (Unity convention), packed
    /// as <see cref="Rgba"/>.
    /// </summary>
    public static class PngDecoder
    {
        public static uint[] Decode(byte[] png, out int width, out int height)
        {
            if (png.Length < 8 || png[0] != 137 || png[1] != 80 || png[2] != 78 || png[3] != 71)
                throw new InvalidDataException("not a PNG");
            int pos = 8;
            width = height = 0;
            int bitDepth = 0, colorType = 0, interlace = 0;
            byte[] palette = null, trns = null;
            var idat = new MemoryStream();
            while (pos + 8 <= png.Length)
            {
                int len = (png[pos] << 24) | (png[pos + 1] << 16) | (png[pos + 2] << 8) | png[pos + 3];
                string type = new string(new[] { (char)png[pos + 4], (char)png[pos + 5], (char)png[pos + 6], (char)png[pos + 7] });
                int data = pos + 8;
                switch (type)
                {
                    case "IHDR":
                        width = (png[data] << 24) | (png[data + 1] << 16) | (png[data + 2] << 8) | png[data + 3];
                        height = (png[data + 4] << 24) | (png[data + 5] << 16) | (png[data + 6] << 8) | png[data + 7];
                        bitDepth = png[data + 8]; colorType = png[data + 9]; interlace = png[data + 12];
                        break;
                    case "PLTE": palette = Slice(png, data, len); break;
                    case "tRNS": trns = Slice(png, data, len); break;
                    case "IDAT": idat.Write(png, data, len); break;
                }
                if (type == "IEND") break;
                pos = data + len + 4; // skip CRC
            }
            if (bitDepth != 8 || interlace != 0) throw new NotSupportedException($"PNG bit depth {bitDepth}, interlace {interlace}");
            int channels = colorType == 0 ? 1 : colorType == 2 ? 3 : colorType == 3 ? 1 : colorType == 4 ? 2 : colorType == 6 ? 4 : 0;
            if (channels == 0) throw new NotSupportedException($"PNG colour type {colorType}");

            byte[] raw = Inflate(idat.ToArray());
            int stride = width * channels;
            var cur = new byte[stride];
            var prev = new byte[stride];
            var pixels = new uint[width * height];
            int src = 0;
            for (int y = 0; y < height; y++)
            {
                byte filter = raw[src++];
                Buffer.BlockCopy(raw, src, cur, 0, stride);
                src += stride;
                Unfilter(filter, cur, prev, channels);
                int row = (height - 1 - y) * width; // bottom-up
                for (int x = 0; x < width; x++)
                {
                    int i = x * channels;
                    uint c;
                    switch (colorType)
                    {
                        case 0: c = Rgba.Pack(cur[i], cur[i], cur[i]); break;
                        case 2: c = Rgba.Pack(cur[i], cur[i + 1], cur[i + 2]); break;
                        case 4: c = Rgba.Pack(cur[i], cur[i], cur[i], cur[i + 1]); break;
                        case 6: c = Rgba.Pack(cur[i], cur[i + 1], cur[i + 2], cur[i + 3]); break;
                        default:
                        {
                            int k = cur[i];
                            int a = trns != null && k < trns.Length ? trns[k] : 255;
                            c = Rgba.Pack(palette[k * 3], palette[k * 3 + 1], palette[k * 3 + 2], a);
                            break;
                        }
                    }
                    if (Rgba.A(c) == 0) c = 0; // canonical transparent
                    pixels[row + x] = c;
                }
                var t = prev; prev = cur; cur = t;
            }
            return pixels;
        }

        static byte[] Slice(byte[] a, int start, int len)
        {
            var r = new byte[len];
            Buffer.BlockCopy(a, start, r, 0, len);
            return r;
        }

        static byte[] Inflate(byte[] zlib)
        {
            // zlib = 2-byte header + raw deflate + Adler-32; DeflateStream reads the raw part.
            using (var input = new MemoryStream(zlib, 2, zlib.Length - 2))
            using (var deflate = new DeflateStream(input, CompressionMode.Decompress))
            using (var output = new MemoryStream())
            {
                deflate.CopyTo(output);
                return output.ToArray();
            }
        }

        static void Unfilter(byte filter, byte[] cur, byte[] prev, int bpp)
        {
            unchecked
            {
                for (int i = 0; i < cur.Length; i++)
                {
                    int a = i >= bpp ? cur[i - bpp] : 0, b = prev[i], c = i >= bpp ? prev[i - bpp] : 0;
                    switch (filter)
                    {
                        case 1: cur[i] = (byte)(cur[i] + a); break;
                        case 2: cur[i] = (byte)(cur[i] + b); break;
                        case 3: cur[i] = (byte)(cur[i] + ((a + b) >> 1)); break;
                        case 4:
                        {
                            int p = a + b - c, pa = Math.Abs(p - a), pb = Math.Abs(p - b), pc = Math.Abs(p - c);
                            cur[i] = (byte)(cur[i] + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c));
                            break;
                        }
                    }
                }
            }
        }
    }
}
