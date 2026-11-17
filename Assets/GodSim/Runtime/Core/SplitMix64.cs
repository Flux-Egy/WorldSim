namespace GodSim.Core
{
    /// <summary>
    /// SplitMix64 (Steele, Lea, Flood 2014). Used to derive independent sub-seeds.
    /// Pure integer math: identical on every CPU, Burst-compatible (no managed refs).
    /// </summary>
    public struct SplitMix64
    {
        public const ulong GoldenGamma = 0x9E3779B97F4A7C15UL;

        public ulong State;

        public SplitMix64(ulong seed) { State = seed; }

        public ulong Next()
        {
            unchecked
            {
                State += GoldenGamma;
                return Mix(State);
            }
        }

        /// <summary>The SplitMix64 finaliser. A strong 64-bit bijective hash.</summary>
        public static ulong Mix(ulong z)
        {
            unchecked
            {
                z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
                return z ^ (z >> 31);
            }
        }

        /// <summary>
        /// The n-th output (1-based) of a SplitMix64 stream seeded with <paramref name="seed"/>,
        /// computed in O(1). Equivalent to calling Next() n times.
        /// </summary>
        public static ulong NthOutput(ulong seed, ulong n)
        {
            unchecked { return Mix(seed + n * GoldenGamma); }
        }
    }
}
