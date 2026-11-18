namespace WorldSim.Render
{
    /// <summary>
    /// Colours as packed uint in the memory layout of Unity's Color32 / TextureFormat.RGBA32
    /// on little-endian CPUs (r | g&lt;&lt;8 | b&lt;&lt;16 | a&lt;&lt;24), so painted pixels can be written
    /// straight into Texture2D.GetPixelData&lt;uint&gt;. Pure and Burst-compatible.
    /// </summary>
    public static class Rgba
    {
        public const uint Transparent = 0;

        public static uint Pack(int r, int g, int b, int a = 255)
        {
            unchecked { return (uint)(C(r) | (C(g) << 8) | (C(b) << 16) | (C(a) << 24)); }
        }

        public static int R(uint c) => (int)(c & 0xFF);
        public static int G(uint c) => (int)((c >> 8) & 0xFF);
        public static int B(uint c) => (int)((c >> 16) & 0xFF);
        public static int A(uint c) => (int)(c >> 24);

        /// <summary>Adds <paramref name="d"/> to each channel (brighten/darken), alpha kept.</summary>
        public static uint Shift(uint c, int d) => Pack(R(c) + d, G(c) + d, B(c) + d, A(c));

        /// <summary>Linear mix, t in 0..256.</summary>
        public static uint Mix(uint a, uint b, int t)
        {
            int u = 256 - t;
            return Pack((R(a) * u + R(b) * t) >> 8, (G(a) * u + G(b) * t) >> 8, (B(a) * u + B(b) * t) >> 8, 255);
        }

        /// <summary>Darkens <paramref name="c"/> to <paramref name="percent"/>% brightness.</summary>
        public static uint Darken(uint c, int percent) =>
            Pack(R(c) * percent / 100, G(c) * percent / 100, B(c) * percent / 100, A(c));

        static int C(int v) => v < 0 ? 0 : v > 255 ? 255 : v;
    }
}
