# Rebuild: art gaps (for the art side)

Phase 1 of the rebuild (`rebuild/pack-foundation`) maps every simulation biome and decoration to pack art
(`Assets/WorldSim/Runtime/Render/Art/BiomeArt.cs`, checked by `BiomeArtTests`). All 30 biomes have their own tiles
(including Lava, Birch Forest, Glimmerwood and Ember Wastes from patch v3.3/v3.4.1) and far-zoom tiles.

These decorations have **no dedicated pack art yet** and use the closest pack prop as a stand-in
(`BiomeArt.IsStandIn`):

| Decoration | Where it grows | Stand-in now | Wanted |
|---|---|---|---|
| JungleTree | Jungle | `tree_5_*` (big broadleaf) | tall rainforest tree, buttress roots, vines |
| AcaciaTree | Savanna | `tree_3_*` | flat-topped acacia |
| SwampTree | Swamp | `tree_2_*` | drooping willow / mangrove |
| BerryBush | Meadow, Forest, Flower field | `bush_*` | bush with red berries (food source) |
| TallGrass | Meadow, Steppe, Tundra, Savanna | `fern_*` | grass tuft, steppe grass |

Each wanted prop needs the same set as the existing trees: 2-3 variants, seasonal sway frames in
`Nature/nature_seasonal` (`<name>_<v>_<season>_sway_<f>`), and `fall`, `stump`, `burning`, `burnt` states for trees.
