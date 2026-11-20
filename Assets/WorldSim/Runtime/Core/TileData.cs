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
        // The art pack's 24 biomes + the 4 simulation biomes it lacked (art patch v3.3) + water depths.
        // Values 0-18 keep their old numbers (renamed to the pack's names); 19+ are new.
        DeepWater = 0,
        ShallowWater = 1,
        Beach = 2,          // was Sand
        Meadow = 3,         // was Grass
        Forest = 4,         // temperate broadleaf
        Mountain = 5,
        Snow = 6,           // snow fields and peaks
        DesertDunes = 7,    // was Desert
        Savanna = 8,
        Jungle = 9,
        Swamp = 10,
        PineTaiga = 11,     // was Taiga
        Tundra = 12,
        BirchForest = 13,
        CrystalCaves = 14,  // was CrystalFields
        FungalGrove = 15,   // was MushroomGrove
        EmberWastes = 16,
        Glimmerwood = 17,
        Lava = 18,
        FlowerField = 19,
        Badlands = 20,
        Steppe = 21,
        Glacier = 22,
        RockyHighland = 23,
        Volcanic = 24,
        AshWaste = 25,
        SaltFlats = 26,
        CoralShallows = 27, // warm shallow sea (water)
        Farmland = 28,      // made by people, never generated
        IrradiatedWaste = 29, // made by nuclear strikes, never generated
        Count = 30,
        FirstModBiome = 128,
    }

    /// <summary>Biome groups used by generation, editing and life.</summary>
    public static class Biomes
    {
        /// <summary>Open water (swimmers only): deep, shallow and coral shallows.</summary>
        public static bool IsWater(Biome b) => b == Biome.DeepWater || b == Biome.ShallowWater || b == Biome.CoralShallows;

        /// <summary>The rare, coherent "anomaly" regions (crystal, fungal, glimmer, fire family). Kept when only the height moves.</summary>
        public static bool IsAnomaly(Biome b) =>
            b == Biome.CrystalCaves || b == Biome.FungalGrove || b == Biome.Glimmerwood || b == Biome.EmberWastes ||
            b == Biome.Volcanic || b == Biome.AshWaste;
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
        Coral = 24,         // coral shallows (in water)
        Fern = 25,
        CharredStump = 26,  // ember wastes, ash
        EmberVent = 27,     // ember wastes: smoking vent
        LavaRock = 28,      // volcanic

        Count = 29,
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
        public bool IsWater => Biomes.IsWater((Core.Biome)BiomeId);
        public bool Has(ResourceFlags flag) => (ResourceFlags & (byte)flag) != 0;

        public static bool IsTree(Decoration d) =>
            d == Decoration.OakTree || d == Decoration.PineTree || d == Decoration.BirchTree ||
            d == Decoration.PalmTree || d == Decoration.JungleTree || d == Decoration.DeadTree ||
            d == Decoration.GlowTree || d == Decoration.SnowPine || d == Decoration.SwampTree ||
            d == Decoration.AcaciaTree;

        public static bool IsRock(Decoration d) =>
            d == Decoration.Rock || d == Decoration.Boulder || d == Decoration.EmberRock || d == Decoration.IceRock ||
            d == Decoration.LavaRock;
    }
}
