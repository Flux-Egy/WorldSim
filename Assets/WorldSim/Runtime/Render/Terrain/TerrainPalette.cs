using System.Collections.Generic;
using WorldSim.Core;
using WorldSim.Render.Art;

namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// The approved colours (owner, 2026-11-22): grass and water take the vivid shades of the bright candidate; the map
    /// zoom mutes neutral land so kingdoms stand out. Built from <c>WorldSimData/lod.json</c> "map_colors".
    /// </summary>
    public static class TerrainPalette
    {
        /// <summary>Minimal reader for the flat "map_colors": { "key": "#rrggbb", ... } object of lod.json.</summary>
        public static Dictionary<string, uint> ParseMapColors(string json)
        {
            var d = new Dictionary<string, uint>();
            int start = json.IndexOf("\"map_colors\"", System.StringComparison.Ordinal);
            if (start < 0) return d;
            int open = json.IndexOf('{', start), close = json.IndexOf('}', open);
            string body = json.Substring(open + 1, close - open - 1);
            foreach (string part in body.Split(','))
            {
                int q1 = part.IndexOf('"'), q2 = part.IndexOf('"', q1 + 1), h = part.IndexOf('#');
                if (q1 < 0 || q2 < 0 || h < 0 || h + 7 > part.Length) continue;
                string key = part.Substring(q1 + 1, q2 - q1 - 1), hex = part.Substring(h + 1, 6);
                d[key] = Rgba.Pack(System.Convert.ToInt32(hex.Substring(0, 2), 16), System.Convert.ToInt32(hex.Substring(2, 2), 16),
                                   System.Convert.ToInt32(hex.Substring(4, 2), 16));
            }
            return d;
        }

        public static uint Vivid(uint c, int saturation, int brightness)
        {
            int r = Rgba.R(c), g = Rgba.G(c), b = Rgba.B(c), l = (r * 30 + g * 59 + b * 11) / 100;
            return Rgba.Pack(l + (r - l) * saturation / 100 + brightness, l + (g - l) * saturation / 100 + brightness,
                             l + (b - l) * saturation / 100 + brightness);
        }

        public static uint MapColor(Dictionary<string, uint> map, Biome b, int band)
        {
            string key = band >= 0 && !(b == Biome.CoralShallows && band == 2) ? "water_depth_" + (band > 2 ? 2 : band) : BiomeArt.MapColorKey(b);
            return key != null && map.TryGetValue(key, out uint c) ? c : Rgba.Pack(255, 0, 255);
        }

        /// <summary>The approved ground style: grass-like biomes and water retinted to the vivid palette.</summary>
        public static TerrainStyle ApprovedStyle(Dictionary<string, uint> map) =>
            new TerrainStyle { Target = (b, band) => Vivid(MapColor(map, b, band), 150, 10) };

        /// <summary>Map zoom colours: water vivid, neutral land muted so kingdom colours stand out.</summary>
        public static System.Func<Biome, int, uint> MapZoomColors(Dictionary<string, uint> map) =>
            (b, band) => band >= 0 ? Vivid(MapColor(map, b, band), 110, 0) : Vivid(MapColor(map, b, band), 45, 18);
    }
}
