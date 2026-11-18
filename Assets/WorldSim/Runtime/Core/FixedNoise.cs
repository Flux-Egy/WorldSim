namespace WorldSim.Core
{
    /// <summary>
    /// 2D gradient (Perlin-style) noise in Q16.16 fixed point: integer math only, so results are
    /// bit-identical on x64, ARM64, Mono, IL2CPP and Burst (§4.3). Burst-compatible: static,
    /// no arrays, no managed references.
    ///
    /// Deviation from §4.2 ("SimplexNoise or OpenSimplex2"): both reference implementations are
    /// floating point, and float results are not guaranteed identical across CPUs. Gradient
    /// noise with a quintic fade has the same visual role (smooth, band-limited octaves) and is
    /// exact in integers. Recorded in docs/IMPLEMENTATION_PLAN.md.
    /// </summary>
    public static class FixedNoise
    {
        public const int FracBits = 16;
        public const int One = 1 << FracBits;   // 1.0 in Q16.16
        const int FracMask = One - 1;

        /// <summary>Hash of a lattice point. Uses only the seed and the integer coordinates.</summary>
        public static ulong LatticeHash(ulong seed, int ix, int iy)
        {
            unchecked
            {
                ulong h = seed + (ulong)(uint)ix * 0x9E3779B97F4A7C15UL + (ulong)(uint)iy * 0xC2B2AE3D27D4EB4FUL;
                return SplitMix64.Mix(h);
            }
        }

        /// <summary>Quintic fade 6t^5 - 15t^4 + 10t^3 for t in [0, One]. Result in [0, One].</summary>
        public static int Fade(int t)
        {
            long tl = t;
            long t3 = (tl * tl >> FracBits) * tl >> FracBits;
            long inner = (tl * (6L * tl - 15L * One) >> FracBits) + 10L * One; // 6t^2 - 15t + 10
            return (int)(t3 * inner >> FracBits);
        }

        /// <summary>Dot product of one of 8 lattice gradients with (dx, dy), all Q16.16.</summary>
        static long Grad(ulong hash, long dx, long dy)
        {
            switch ((int)(hash >> 61)) // top 3 bits: best-mixed bits of SplitMix64
            {
                case 0: return dx + dy;
                case 1: return -dx + dy;
                case 2: return dx - dy;
                case 3: return -dx - dy;
                case 4: return dx;
                case 5: return -dx;
                case 6: return dy;
                default: return -dy;
            }
        }

        static long Lerp(long a, long b, int t) => a + ((b - a) * t >> FracBits);

        /// <summary>
        /// Gradient noise at (x, y) given in Q16.16 lattice units. Output is Q16.16, roughly
        /// in [-One, One] (never beyond ±One by construction of the gradient set and fade).
        /// </summary>
        public static int Sample(ulong seed, long x, long y)
        {
            int ix = (int)(x >> FracBits);           // floor, also for negatives (arithmetic shift)
            int iy = (int)(y >> FracBits);
            long fx = x & FracMask;                   // fractional part in [0, One)
            long fy = y & FracMask;

            long n00 = Grad(LatticeHash(seed, ix, iy), fx, fy);
            long n10 = Grad(LatticeHash(seed, ix + 1, iy), fx - One, fy);
            long n01 = Grad(LatticeHash(seed, ix, iy + 1), fx, fy - One);
            long n11 = Grad(LatticeHash(seed, ix + 1, iy + 1), fx - One, fy - One);

            int u = Fade((int)fx);
            int v = Fade((int)fy);
            long nx0 = Lerp(n00, n10, u);
            long nx1 = Lerp(n01, n11, u);
            long n = Lerp(nx0, nx1, v);

            // Diagonal gradients can reach |n| slightly above 1 near cell centres; clamp keeps
            // the documented range exact.
            if (n > One) n = One;
            if (n < -One) n = -One;
            return (int)n;
        }

        /// <summary>
        /// Fractal sum of <paramref name="octaves"/> layers. <paramref name="x"/>/<paramref name="y"/>
        /// are world positions in Q16.16 tiles; <paramref name="period"/> is the base feature size in
        /// tiles. Each octave halves the period and amplitude and uses its own derived seed.
        /// Output Q16.16, normalised to roughly [-One, One].
        /// </summary>
        public static int Fbm(ulong seed, long x, long y, int period, int octaves)
        {
            if (period < 1) period = 1;
            long sum = 0;
            long amplitude = One;
            long totalAmplitude = 0;
            for (int o = 0; o < octaves; o++)
            {
                ulong octaveSeed = SplitMix64.NthOutput(seed, (ulong)(o + 1));
                long sx = x / period;  // Q16.16 lattice coordinates for this octave
                long sy = y / period;
                sum += Sample(octaveSeed, sx, sy) * amplitude >> FracBits;
                totalAmplitude += amplitude;
                amplitude >>= 1;
                period >>= 1;
                if (period < 1) period = 1;
            }
            return (int)(sum * One / totalAmplitude);
        }
    }
}
