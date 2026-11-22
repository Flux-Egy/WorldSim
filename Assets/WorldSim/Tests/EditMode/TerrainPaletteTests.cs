using System.IO;
using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Render;
using WorldSim.Render.Terrain;

namespace WorldSim.Tests
{
    public class TerrainPaletteTests
    {
        [Test]
        public void ParsesMapColors_AndEveryBiomeHasOne()
        {
            string json = File.ReadAllText(Path.Combine(ArtIndexTests.ArtDir(), "..", "WorldSimData", "lod.json"));
            var map = TerrainPalette.ParseMapColors(json);
            Assert.GreaterOrEqual(map.Count, 30);
            Assert.AreEqual(Rgba.Pack(0x77, 0xa8, 0x55), map["meadow"]);
            for (int b = 0; b < (int)Biome.Count; b++)
                Assert.AreNotEqual(Rgba.Pack(255, 0, 255), TerrainPalette.MapColor(map, (Biome)b, Biomes.IsWater((Biome)b) ? 1 : -1), ((Biome)b).ToString());
            var style = TerrainPalette.ApprovedStyle(map);
            Assert.AreNotEqual(0u, style.Target(Biome.Meadow, -1));
        }
    }
}
