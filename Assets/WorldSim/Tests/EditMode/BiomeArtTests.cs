using System;
using System.IO;
using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Render.Art;

namespace WorldSim.Tests
{
    /// <summary>Every biome and decoration has real pack art: every name BiomeArt returns exists in the art index.</summary>
    public class BiomeArtTests
    {
        static ArtIndex Ix => ArtIndexTests.Index;

        static void Frame(string name)
        {
            Assert.IsNotNull(name);
            Assert.IsTrue(Ix.TryGetFrameId(name, out _), "missing frame " + name);
        }

        [Test]
        public void EveryLandBiome_HasFourTiles_AndBothFarZoomTiles()
        {
            for (int b = 0; b < (int)Biome.Count; b++)
            {
                var biome = (Biome)b;
                if (Biomes.IsWater(biome) && biome != Biome.CoralShallows) { Assert.IsNull(BiomeArt.Tile(biome, 0)); continue; }
                Assert.IsNotNull(BiomeArt.Key(biome), biome.ToString());
                for (int v = 0; v < BiomeArt.TileVariants; v++)
                {
                    Frame(BiomeArt.Tile(biome, v));
                    Frame(BiomeArt.LodTile(biome, v, 16));
                    Frame(BiomeArt.LodTile(biome, v, 8));
                }
            }
        }

        [Test]
        public void TheFourSimBiomes_UseTheirOwnArt_NotStandIns()
        {
            Assert.AreEqual("t_lava_2_0", BiomeArt.Tile(Biome.Lava, 2));
            Assert.AreEqual("t_birch_forest_1", BiomeArt.Tile(Biome.BirchForest, 1));
            Assert.AreEqual("t_glimmerwood_3", BiomeArt.Tile(Biome.Glimmerwood, 3));
            Assert.AreEqual("t_ember_wastes_0", BiomeArt.Tile(Biome.EmberWastes, 0));
            for (int v = 0; v < 4; v++)
            {
                Assert.IsTrue(Ix.TryGetAnimId(BiomeArt.TileAnim(Biome.Lava, v), out _), "lava animation " + v);
                Assert.IsNull(BiomeArt.TileAnim(Biome.Meadow, v));
            }
            StringAssert.StartsWith("glimmer_", BiomeArt.Prop(Decoration.GlowTree, 0));
            StringAssert.StartsWith("birch_", BiomeArt.Prop(Decoration.BirchTree, 0));
            StringAssert.StartsWith("ember_vent", BiomeArt.Prop(Decoration.EmberVent, 0));
        }

        [Test]
        public void WaterAndMapColourKeys()
        {
            for (int d = 0; d < 3; d++) Frame(BiomeArt.Water(d));
            Assert.AreEqual("water_depth_0", BiomeArt.MapColorKey(Biome.DeepWater));
            Assert.AreEqual("water_depth_2", BiomeArt.MapColorKey(Biome.ShallowWater));
            Assert.AreEqual("pine_taiga", BiomeArt.MapColorKey(Biome.PineTaiga));
            Assert.IsNull(BiomeArt.Key((Biome)200));
            Assert.IsNull(BiomeArt.Tile((Biome)200, 0));
        }

        [Test]
        public void EveryDecoration_HasPackFrames_AndItsAnimationsExist()
        {
            Assert.IsNull(BiomeArt.Prop(Decoration.None, 0));
            for (int d = 1; d < (int)Decoration.Count; d++)
            {
                var deco = (Decoration)d;
                int n = BiomeArt.PropVariantCount(deco);
                Assert.Greater(n, 0, deco.ToString());
                for (int v = 0; v < n; v++)
                {
                    Frame(BiomeArt.Prop(deco, v));
                    string anim = BiomeArt.PropAnim(deco, v);
                    if (anim != null) Assert.IsTrue(Ix.TryGetAnimId(anim, out _), "missing animation " + anim);
                }
                Assert.AreEqual(BiomeArt.Prop(deco, 0), BiomeArt.Prop(deco, n), "variants wrap");
            }
            Assert.IsNull(BiomeArt.Prop((Decoration)250, 0));
        }

        [Test]
        public void LivingProps_HaveRealAnimations()
        {
            int living = 0;
            for (int d = 1; d < (int)Decoration.Count; d++)
                for (int v = 0; v < BiomeArt.PropVariantCount((Decoration)d); v++)
                {
                    string anim = BiomeArt.LivingAnim((Decoration)d, v);
                    if (anim == null) continue;
                    Assert.IsTrue(Ix.TryGetAnimId(anim, out _), $"{(Decoration)d} variant {v}: missing animation {anim}");
                    living++;
                }
            Assert.Greater(living, 25, "trees, pines, palms, bushes, birches, glimmers and vents move");
            Assert.AreEqual("pine_5_0_winter_sway", BiomeArt.LivingAnim(Decoration.SnowPine, 0));
            Assert.IsNull(BiomeArt.LivingAnim(Decoration.Rock, 0));
        }

#if !UNITY_2017_1_OR_NEWER
        [Test]
        public void MapColours_InLodJson_CoverEveryBiome()
        {
            string dir = Path.GetFullPath(Path.Combine(ArtIndexTests.ArtDir(), "..", "WorldSimData"));
            using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "lod.json")));
            var colours = doc.RootElement.GetProperty("map_colors");
            for (int b = 0; b < (int)Biome.Count; b++)
            {
                string key = BiomeArt.MapColorKey((Biome)b);
                Assert.IsTrue(colours.TryGetProperty(key, out var c), "no map colour for " + (Biome)b);
                StringAssert.IsMatch("^#[0-9a-f]{6}$", c.GetString());
            }
        }
#endif
    }
}
