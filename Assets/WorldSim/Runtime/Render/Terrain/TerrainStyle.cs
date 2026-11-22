using WorldSim.Core;

namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// Colour grading of the pack ground (owner, 2026-11-22: keep the v2 look, take the grass and water shades of the
    /// bright candidate). <see cref="Target"/> gives the wanted average colour for a biome (or a water band); grass-like
    /// biomes and water move their tile's average to it and keep the tile's own light/dark detail.
    /// </summary>
    public sealed class TerrainStyle
    {
        /// <summary>(biome, water band or -1 on land) -> wanted average colour, or 0 to keep the tile as it is.</summary>
        public System.Func<Biome, int, uint> Target;

        public uint Retint(uint c, uint tileMean, Biome b, int band)
        {
            if (Target == null || !(band >= 0 || IsGrassy(b))) return c;
            uint t = Target(b, band);
            if (t == 0) return c;
            return Rgba.Pack(Rgba.R(t) + Rgba.R(c) - Rgba.R(tileMean), Rgba.G(t) + Rgba.G(c) - Rgba.G(tileMean), Rgba.B(t) + Rgba.B(c) - Rgba.B(tileMean));
        }

        public static bool IsGrassy(Biome b) =>
            b == Biome.Meadow || b == Biome.FlowerField || b == Biome.Forest || b == Biome.BirchForest || b == Biome.Jungle ||
            b == Biome.PineTaiga || b == Biome.Swamp || b == Biome.Steppe || b == Biome.Savanna || b == Biome.Tundra;
    }
}
