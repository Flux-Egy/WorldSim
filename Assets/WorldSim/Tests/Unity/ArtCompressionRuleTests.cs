using NUnit.Framework;
using WorldSim.EditorTools;

namespace WorldSim.Tests.UnityOnly
{
    /// <summary>Owner decision 2026-11-20 (Art Lab A/B): which art pages use ASTC 4x4 on Android.</summary>
    public class ArtCompressionRuleTests
    {
        const string R = "Assets/WorldSim/Resources/WorldSimArt/";

        [TestCase("Terrain/terrain_tiles.png")]
        [TestCase("Terrain/biomes_extra.png")]
        [TestCase("Terrain/farms_roads.png")]
        [TestCase("Nature/nature_props.png")]
        [TestCase("Buildings/houses_culture_kit_0.png")]
        [TestCase("Buildings/Disaster/disaster_houses_0.png")]
        [TestCase("FX/Spells/spells.png")]
        public void Compressed(string page) => Assert.IsTrue(WorldSimArtPostprocessor.UsesAstc(R + page), page);

        [TestCase("Terrain/lod.png")]
        [TestCase("UI/ui_kit.png")]
        [TestCase("UI/Icons/icons.png")]
        [TestCase("UI/font_5x7.png")]
        [TestCase("Characters/people.png")]
        [TestCase("Characters/Fauna/fauna_land.png")]
        [TestCase("Units/army.png")]
        [TestCase("Units/Soldiers/soldiers_actions.png")]
        public void Uncompressed(string page) => Assert.IsFalse(WorldSimArtPostprocessor.UsesAstc(R + page), page);
    }
}
