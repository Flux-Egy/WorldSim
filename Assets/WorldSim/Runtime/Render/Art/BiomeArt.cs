using WorldSim.Core;

namespace WorldSim.Render.Art
{
    /// <summary>
    /// Maps simulation biomes and decorations to art-pack frame names (pure C#, no allocations per call).
    /// Every name returned here is checked against the art index by <c>BiomeArtTests</c>.
    /// Tiles: <c>t_&lt;key&gt;_&lt;0..3&gt;</c> (Terrain/terrain_tiles, Terrain/biomes_extra); lava is animated
    /// (<c>t_lava_&lt;v&gt;</c>, frames <c>t_lava_&lt;v&gt;_&lt;f&gt;</c>). Far zoom: <c>t_&lt;key&gt;_&lt;v&gt;_lod16|lod8</c> (Terrain/lod).
    /// Map colours: <c>WorldSimData/lod.json</c> "map_colors", by <see cref="MapColorKey"/>.
    /// </summary>
    public static class BiomeArt
    {
        public const int TileVariants = 4;

        // Indexed by Biome value; null = no tile (water uses water_depth_N).
        static readonly string[] Keys =
        {
            null, null,             // DeepWater, ShallowWater
            "beach", "meadow", "forest", "mountain", "snow", "desert_dunes", "savanna", "jungle", "swamp",
            "pine_taiga", "tundra", "birch_forest", "crystal_caves", "fungal_grove", "ember_wastes", "glimmerwood", "lava",
            "flower_field", "badlands", "steppe", "glacier", "rocky_highland", "volcanic", "ash_waste", "salt_flats",
            "coral_shallows", "farmland", "irradiated_waste",
        };

        static readonly string[,] Tiles = BuildTiles("");
        static readonly string[,] Lod16 = BuildTiles("_lod16");
        static readonly string[,] Lod8 = BuildTiles("_lod8");
        static readonly string[] LavaAnims = { "t_lava_0", "t_lava_1", "t_lava_2", "t_lava_3" };

        static string[,] BuildTiles(string suffix)
        {
            var t = new string[Keys.Length, TileVariants];
            for (int b = 0; b < Keys.Length; b++)
                for (int v = 0; v < TileVariants; v++)
                    if (Keys[b] != null)
                        t[b, v] = b == (int)Biome.Lava && suffix.Length == 0 ? "t_lava_" + v + "_0" : "t_" + Keys[b] + "_" + v + suffix;
            return t;
        }

        /// <summary>The pack's biome key ("meadow", "pine_taiga", ...), or null for open water and unknown biomes.</summary>
        public static string Key(Biome b) => (int)b < Keys.Length ? Keys[(int)b] : null;

        /// <summary>Key into lod.json "map_colors" (water: water_depth_0 deep .. water_depth_2 shallow).</summary>
        public static string MapColorKey(Biome b) =>
            b == Biome.DeepWater ? "water_depth_0" : b == Biome.ShallowWater ? "water_depth_2" : Key(b);

        /// <summary>Static ground tile (variant 0..3), or null for open water.</summary>
        public static string Tile(Biome b, int variant) =>
            (int)b < Keys.Length ? Tiles[(int)b, variant & 3] : null;

        /// <summary>Animation for animated ground (lava), or null.</summary>
        public static string TileAnim(Biome b, int variant) => b == Biome.Lava ? LavaAnims[variant & 3] : null;

        /// <summary>Far-zoom tile: 16 px (zoom 1/4) or 8 px (zoom 1/8). Null for open water (drawn in its map colour).</summary>
        public static string LodTile(Biome b, int variant, int pixels) =>
            (int)b >= Keys.Length ? null : pixels >= 16 ? Lod16[(int)b, variant & 3] : Lod8[(int)b, variant & 3];

        /// <summary>Water surface tile by depth step (0 deep .. 2 shallow).</summary>
        public static string Water(int depth) => depth <= 0 ? "water_depth_0" : depth == 1 ? "water_depth_1" : "water_depth_2";

        // ------------------------------------------------------------------ props
        // Static frames per decoration (index = Decoration value). Entries marked "stand-in" have no dedicated
        // pack art yet and use the closest pack prop; see docs/art/REBUILD_ART_GAPS.md.
        static readonly string[][] Props =
        {
            new string[0],                                                                // None
            new[] { "tree_4_0", "tree_4_1", "tree_4_2", "tree_5_0", "tree_5_1", "tree_5_2" }, // OakTree
            new[] { "pine_5_green", "pine_4_green", "pine_3_green" },                       // PineTree
            new[] { "birch_5_0_summer_sway_0", "birch_5_1_summer_sway_0", "birch_4_0_summer_sway_0",
                    "birch_4_1_summer_sway_0", "birch_3_0_summer_sway_0", "birch_3_1_summer_sway_0" }, // BirchTree
            new[] { "palm_0", "palm_1", "palm_2" },                                         // PalmTree
            new[] { "tree_5_0", "tree_5_1", "tree_5_2" },                                   // JungleTree (stand-in)
            new[] { "deadtree_0", "deadtree_1" },                                           // DeadTree
            new[] { "bush_0", "bush_1", "bush_2" },                                         // Bush
            new[] { "bush_0", "bush_1", "bush_2" },                                         // BerryBush (stand-in)
            new[] { "flowers_0", "flowers_1", "flowers_2" },                                // Flowers
            new[] { "fern_0", "fern_1" },                                                   // TallGrass (stand-in)
            new[] { "cactus_0", "cactus_1" },                                               // Cactus
            new[] { "rock_1.4_0", "rock_1.4_1", "rock_1.8_0", "rock_1.8_1" },               // Rock
            new[] { "rock_2.4_0", "rock_2.4_1" },                                           // Boulder
            new[] { "reeds" },                                                              // Reeds
            new[] { "mushroom_small" },                                                     // Mushroom
            new[] { "mushroom_big" },                                                       // GiantMushroom
            new[] { "crystal_5fe0e8", "crystal_c45aa8", "crystal_8a7ae8" },                 // Crystal
            new[] { "ember_rock_0", "ember_rock_1" },                                       // EmberRock
            new[] { "glimmer_5_0_0", "glimmer_5_1_0", "glimmer_4_0_0", "glimmer_4_1_0", "glimmer_3_0_0", "glimmer_3_1_0" }, // GlowTree
            new[] { "pine_5_snow", "pine_4_snow", "pine_3_snow" },                          // SnowPine
            new[] { "iceblock" },                                                           // IceRock
            new[] { "tree_2_0", "tree_2_1", "tree_2_2" },                                   // SwampTree (stand-in)
            new[] { "tree_3_0", "tree_3_1", "tree_3_2" },                                   // AcaciaTree (stand-in)
            new[] { "coral_e87a8a", "coral_f0a050", "coral_c45aa8", "coral_e8e070" },       // Coral
            new[] { "fern_0", "fern_1" },                                                   // Fern
            new[] { "charred_stump_0", "charred_stump_1" },                                 // CharredStump
            new[] { "ember_vent_0" },                                                       // EmberVent
            new[] { "lava_rock_0", "lava_rock_1" },                                         // LavaRock
        };

        // Looping animations matching Props entry by entry (null = static).
        static readonly string[][] PropAnims = BuildPropAnims();

        static string[][] BuildPropAnims()
        {
            var a = new string[Props.Length][];
            a[(int)Decoration.BirchTree] = new[] { "birch_5_0_summer_sway", "birch_5_1_summer_sway", "birch_4_0_summer_sway",
                                                   "birch_4_1_summer_sway", "birch_3_0_summer_sway", "birch_3_1_summer_sway" };
            a[(int)Decoration.GlowTree] = new[] { "glimmer_5_0", "glimmer_5_1", "glimmer_4_0", "glimmer_4_1", "glimmer_3_0", "glimmer_3_1" };
            a[(int)Decoration.EmberVent] = new[] { "ember_vent" };
            return a;
        }

        public static int PropVariantCount(Decoration d) => (int)d < Props.Length ? Props[(int)d].Length : 0;

        /// <summary>Static prop frame; <paramref name="variant"/> wraps. Null for None and unknown decorations.</summary>
        public static string Prop(Decoration d, int variant)
        {
            if ((int)d >= Props.Length) return null;
            var p = Props[(int)d];
            return p.Length == 0 ? null : p[(int)((uint)variant % (uint)p.Length)];
        }

        /// <summary>Looping animation for the same variant as <see cref="Prop"/>, or null when the prop is static.</summary>
        public static string PropAnim(Decoration d, int variant)
        {
            if ((int)d >= PropAnims.Length) return null;
            var p = PropAnims[(int)d];
            return p == null ? null : p[(int)((uint)variant % (uint)p.Length)];
        }

        /// <summary>
        /// The looping animation that brings a prop to life: the decoration's own (birch sway, glimmer glow, ember vent
        /// smoke) or the seasonal wind sway of Nature/nature_seasonal for trees, pines, palms and bushes (summer; snowy
        /// pines use the winter sway). Null for props without one (rocks, flowers, cactus...).
        /// </summary>
        public static string LivingAnim(Decoration d, int variant)
        {
            string own = PropAnim(d, variant);
            if (own != null) return own;
            string f = Prop(d, variant);
            if (f == null) return null;
            if (f.StartsWith("tree_", System.StringComparison.Ordinal) && f.Length == 8 && f[5] >= '3') return f + "_summer_sway";      // tree_S_V
            if (f.StartsWith("pine_", System.StringComparison.Ordinal))
                return "pine_" + f[5] + "_0_" + (f.EndsWith("snow", System.StringComparison.Ordinal) ? "winter" : "summer") + "_sway";
            if (f.StartsWith("palm_", System.StringComparison.Ordinal)) return "palm_0_" + ((f[5] - '0') % 2) + "_summer_sway";
            if (f.StartsWith("bush_", System.StringComparison.Ordinal)) return "bush_0_" + f[5] + "_summer_sway";
            return null;
        }

        /// <summary>True when the decoration's art is a stand-in until dedicated pack art exists.</summary>
        public static bool IsStandIn(Decoration d) =>
            d == Decoration.JungleTree || d == Decoration.BerryBush || d == Decoration.TallGrass ||
            d == Decoration.SwampTree || d == Decoration.AcaciaTree;
    }
}
