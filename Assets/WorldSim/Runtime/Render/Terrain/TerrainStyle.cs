namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// How the ground is coloured (art-style candidates for the owner to choose from, Playable Alpha step 1).
    /// Null = the pack tiles as they are. <see cref="Ground"/> replaces the ground colour entirely (flat palettes,
    /// external tile sets); <see cref="Saturation"/>/<see cref="Brightness"/> grade the final ground colour.
    /// </summary>
    public sealed class TerrainStyle
    {
        /// <summary>Optional ground source: (biome, water band or -1 on land, world x, world y) -> colour.</summary>
        public System.Func<WorldSim.Core.Biome, int, int, int, uint> Ground;
        /// <summary>100 = unchanged.</summary>
        public int Saturation = 100;
        /// <summary>Added to each channel.</summary>
        public int Brightness;
        /// <summary>0-100: how much texture detail of the pack tiles is flattened towards the tile's mean colour.</summary>
        public int Calm;

        public uint Grade(uint c)
        {
            if (Saturation == 100 && Brightness == 0) return c;
            int r = Rgba.R(c), g = Rgba.G(c), b = Rgba.B(c);
            int l = (r * 30 + g * 59 + b * 11) / 100;
            r = l + (r - l) * Saturation / 100 + Brightness;
            g = l + (g - l) * Saturation / 100 + Brightness;
            b = l + (b - l) * Saturation / 100 + Brightness;
            return Rgba.Pack(r, g, b);
        }
    }
}
