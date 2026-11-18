namespace WorldSim.Core
{
    /// <summary>
    /// PCG32 (pcg_setseq_64_xsh_rr_32, O'Neill 2014), matching the reference C implementation.
    /// Deterministic across platforms. Never use UnityEngine.Random for simulation or worldgen.
    /// Value type, no allocations, safe to copy into Burst jobs (each job owns its own copy).
    /// </summary>
    public struct Pcg32
    {
        const ulong Multiplier = 6364136223846793005UL;

        ulong _state;
        ulong _inc;

        public Pcg32(ulong initState, ulong initSequence)
        {
            _state = 0UL;
            _inc = (initSequence << 1) | 1UL;
            NextUInt();
            unchecked { _state += initState; }
            NextUInt();
        }

        /// <summary>Builds a stream from a world sub-seed plus a stable key (entity id, tile index, ...).</summary>
        public static Pcg32 ForKey(ulong subSeed, ulong key)
        {
            return new Pcg32(SplitMix64.Mix(subSeed ^ SplitMix64.Mix(key)), key);
        }

        public uint NextUInt()
        {
            unchecked
            {
                ulong old = _state;
                _state = old * Multiplier + _inc;
                uint xorShifted = (uint)(((old >> 18) ^ old) >> 27);
                int rot = (int)(old >> 59);
                return (xorShifted >> rot) | (xorShifted << ((-rot) & 31));
            }
        }

        /// <summary>Unbiased integer in [0, bound). Returns 0 when bound is 0.</summary>
        public uint NextUInt(uint bound)
        {
            if (bound == 0) return 0;
            unchecked
            {
                uint threshold = (0u - bound) % bound; // (2^32 - bound) % bound
                while (true)
                {
                    uint r = NextUInt();
                    if (r >= threshold) return r % bound;
                }
            }
        }

        /// <summary>Unbiased integer in [minInclusive, maxExclusive).</summary>
        public int NextInt(int minInclusive, int maxExclusive)
        {
            if (maxExclusive <= minInclusive) return minInclusive;
            unchecked
            {
                uint range = (uint)(maxExclusive - minInclusive);
                return minInclusive + (int)NextUInt(range);
            }
        }

        /// <summary>
        /// Float in [0, 1) built from 24 random bits. The product is exact (an integer below 2^24
        /// times a power of two), so the result is bit-identical on every platform.
        /// </summary>
        public float NextFloat01()
        {
            return (NextUInt() >> 8) * (1.0f / 16777216.0f);
        }
    }
}
