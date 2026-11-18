namespace WorldSim.Core
{
    /// <summary>
    /// Built-in biome ids (§4.1 <c>biomeId</c>). Values are part of saves and world hashes:
    /// never renumber, only append. Ids from 128 upward are reserved for mod terrain, assigned at
    /// runtime from mod string keys (plan item 7). Names of the fictional biomes (14–18) are
    /// invented for this game.
    /// </summary>
    public enum Biome : byte
    {
        DeepWater = 0,
        ShallowWater = 1,
        Sand = 2,          // beaches
        Grass = 3,
        Forest = 4,        // temperate broadleaf
        Mountain = 5,
        Snow = 6,          // ice sheets and snow peaks
        Desert = 7,
        Savanna = 8,
        Jungle = 9,
        Swamp = 10,
        Taiga = 11,
        Tundra = 12,
        BirchForest = 13,
        CrystalFields = 14,
        MushroomGrove = 15,
        EmberWastes = 16,
        Glimmerwood = 17,
        Lava = 18,

        FirstModBiome = 128,
    }

    /// <summary>
    /// Per-tile decoration (trees, plants, rocks, crystals). Drives both visuals and resources
    /// (trees give wood, rocks give stone). Persisted: only append.
    /// </summary>
    public enum Decoration : byte
    {
        None = 0,
        OakTree = 1,
        PineTree = 2,
        BirchTree = 3,
        PalmTree = 4,
        JungleTree = 5,
        DeadTree = 6,
        Bush = 7,
        BerryBush = 8,
        Flowers = 9,
        TallGrass = 10,
        Cactus = 11,
        Rock = 12,
        Boulder = 13,
        Reeds = 14,
        Mushroom = 15,
        GiantMushroom = 16,
        Crystal = 17,
        EmberRock = 18,
        GlowTree = 19,
        SnowPine = 20,
        IceRock = 21,
        SwampTree = 22,
        AcaciaTree = 23,

        Count = 24,
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
    /// Per-tile terrain data: the five §4.1 fields plus the decoration id. Six bytes, blittable,
    /// safe for NativeArray and Burst.
    /// </summary>
    public struct TileData
    {
        public byte BiomeId;
        public byte Height;
        public byte Moisture;
        public byte Temperature;
        public byte ResourceFlags;
        public byte DecorationId;

        public Biome Biome => (Biome)BiomeId;
        public Decoration Decoration => (Decoration)DecorationId;
        public bool IsWater => BiomeId == (byte)Core.Biome.DeepWater || BiomeId == (byte)Core.Biome.ShallowWater;
        public bool Has(ResourceFlags flag) => (ResourceFlags & (byte)flag) != 0;

        public static bool IsTree(Decoration d) =>
            d == Decoration.OakTree || d == Decoration.PineTree || d == Decoration.BirchTree ||
            d == Decoration.PalmTree || d == Decoration.JungleTree || d == Decoration.DeadTree ||
            d == Decoration.GlowTree || d == Decoration.SnowPine || d == Decoration.SwampTree ||
            d == Decoration.AcaciaTree;

        public static bool IsRock(Decoration d) =>
            d == Decoration.Rock || d == Decoration.Boulder || d == Decoration.EmberRock || d == Decoration.IceRock;
    }
}
