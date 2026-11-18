namespace WorldSim.Core
{
    /// <summary>
    /// Built-in biome ids (§4.1 <c>biomeId</c>). Values are part of saves and world hashes:
    /// never renumber, only append. Ids from 128 upward are reserved for mod terrain, which is
    /// assigned at runtime from mod string keys (see plan item 7).
    /// </summary>
    public enum Biome : byte
    {
        DeepWater = 0,
        ShallowWater = 1,
        Sand = 2,
        Grass = 3,
        Forest = 4,
        Mountain = 5,
        Snow = 6,

        FirstModBiome = 128,
    }

    /// <summary>§4.1 <c>resourceFlags</c> bitmask. Values are persisted: only append.</summary>
    [System.Flags]
    public enum ResourceFlags : byte
    {
        None = 0,
        Wood = 1 << 0,
        Stone = 1 << 1,
        Gold = 1 << 2,
        Gems = 1 << 3,
    }

    /// <summary>
    /// Per-tile terrain data (§4.1). Five bytes, blittable, safe for NativeArray and Burst.
    /// </summary>
    public struct TileData
    {
        public byte BiomeId;
        public byte Height;
        public byte Moisture;
        public byte Temperature;
        public byte ResourceFlags;

        public Biome Biome => (Biome)BiomeId;
        public bool IsWater => BiomeId == (byte)Core.Biome.DeepWater || BiomeId == (byte)Core.Biome.ShallowWater;
        public bool Has(ResourceFlags flag) => (ResourceFlags & (byte)flag) != 0;
    }
}
