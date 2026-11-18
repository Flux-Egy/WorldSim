using System;

namespace WorldSim.Core
{
    /// <summary>
    /// Independent random streams derived from one world seed. Values are part of the save
    /// format and of world hashes: never renumber, only append.
    /// </summary>
    public enum SeedStream : ulong
    {
        Height = 1,
        Moisture = 2,
        Temperature = 3,
        Resources = 4,
        EdgeRefine = 5,
        Detail = 6,
        Agents = 7,
        AiNoise = 8,
        Disasters = 9,
        Economy = 10,
    }

    /// <summary>The single seed a world is generated from (§4.3).</summary>
    [Serializable]
    public readonly struct WorldSeed : IEquatable<WorldSeed>
    {
        public readonly ulong Value;

        public WorldSeed(ulong value) { Value = value; }

        /// <summary>
        /// Sub-seed for a stream: the n-th SplitMix64 output of the world seed, n = stream id.
        /// Streams are statistically independent and stable across versions.
        /// </summary>
        public ulong Derive(SeedStream stream)
        {
            return SplitMix64.NthOutput(Value, (ulong)stream);
        }

        public Pcg32 CreateRandom(SeedStream stream, ulong key = 0)
        {
            return Pcg32.ForKey(Derive(stream), key);
        }

        public bool Equals(WorldSeed other) => Value == other.Value;
        public override bool Equals(object obj) => obj is WorldSeed other && Equals(other);
        public override int GetHashCode() => Value.GetHashCode();
        public override string ToString() => "0x" + Value.ToString("X16");

        public static bool operator ==(WorldSeed a, WorldSeed b) => a.Value == b.Value;
        public static bool operator !=(WorldSeed a, WorldSeed b) => a.Value != b.Value;
    }
}
