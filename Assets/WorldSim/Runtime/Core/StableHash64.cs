namespace WorldSim.Core
{
    /// <summary>
    /// Streaming FNV-1a 64-bit hash with explicit little-endian byte order. Used for world-state
    /// hashes (§4.3, §10.4, §14.1) so results are identical on x64 Editor and ARM64 devices.
    /// Not cryptographic. Mod assembly hashes use SHA-256 instead.
    /// </summary>
    public struct StableHash64
    {
        public const ulong OffsetBasis = 0xCBF29CE484222325UL;
        public const ulong Prime = 0x100000001B3UL;

        public ulong Value;

        public static StableHash64 Create() => new StableHash64 { Value = OffsetBasis };

        public void Add(byte b)
        {
            unchecked { Value = (Value ^ b) * Prime; }
        }

        public void Add(ushort v) { Add((byte)v); Add((byte)(v >> 8)); }

        public void Add(uint v)
        {
            Add((byte)v); Add((byte)(v >> 8)); Add((byte)(v >> 16)); Add((byte)(v >> 24));
        }

        public void Add(int v) { Add(unchecked((uint)v)); }

        public void Add(ulong v) { Add((uint)v); Add((uint)(v >> 32)); }

        public void Add(long v) { Add(unchecked((ulong)v)); }
    }
}
