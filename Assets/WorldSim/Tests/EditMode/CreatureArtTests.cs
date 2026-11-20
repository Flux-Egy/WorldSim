using System;
using System.IO;
using NUnit.Framework;
using WorldSim.Core.Life;
using WorldSim.Render.Art;

namespace WorldSim.Tests
{
    /// <summary>Every built-in species has pack art for every pose, age, sex and era.</summary>
    public class CreatureArtTests
    {
        static ArtIndex Ix => ArtIndexTests.Index;

        [Test]
        public void EverySpecies_EveryPose_ResolvesToExistingArt()
        {
            int checkedCount = 0;
            foreach (SpeciesId s in Enum.GetValues(typeof(SpeciesId)))
            {
                Assert.IsNotNull(CreatureArt.PackKey(s), s.ToString());
                foreach (CreaturePose pose in Enum.GetValues(typeof(CreaturePose)))
                    for (int young = 0; young < 2; young++)
                        for (int male = 0; male < 2; male++)
                            for (int era = 0; era < 3; era++)
                                for (int air = 0; air < 2; air++)
                                {
                                    string name = CreatureArt.Resolve(s, pose, young == 1, male == 1, (Era)era, air == 1, out bool anim);
                                    Assert.IsNotNull(name);
                                    bool found = anim ? Ix.TryGetAnimId(name, out _) : Ix.TryGetFrameId(name, out _);
                                    Assert.IsTrue(found, $"{s} {pose} young={young} male={male} era={(Era)era}: missing {(anim ? "animation" : "frame")} {name}");
                                    checkedCount++;
                                }
            }
            Assert.Greater(checkedCount, 1000);
        }

        [Test]
        public void PeopleUseTheirRace_AndRecolour()
        {
            Assert.AreEqual("h_dwarf_f_modern_walk", CreatureArt.Resolve(SpeciesId.Dwarf, CreaturePose.Walk, false, false, Era.Modern, false, out _));
            Assert.AreEqual("h_elf_m_child_cower", CreatureArt.Resolve(SpeciesId.Elf, CreaturePose.Attack, true, true, Era.Tribal, false, out _));
            Assert.IsTrue(Ix.TryGetAnimId("h_orc_m_medieval_idle", out int id));
            Assert.IsTrue(Ix.Frame(Ix.AnimFrame(id, 0)).Recolor, "people frames carry recolour masks");
            Assert.IsTrue(CreatureArt.IsPerson(SpeciesId.Human));
            Assert.IsFalse(CreatureArt.IsPerson(SpeciesId.Wolf));
        }

        [Test]
        public void BirdsFly_FishSwim_AnimalsHaveStillDeathFrames()
        {
            Assert.AreEqual("crow_adult_fly", CreatureArt.Resolve(SpeciesId.Bird, CreaturePose.Walk, false, true, Era.Tribal, true, out _));
            Assert.AreEqual("crow_adult_walk", CreatureArt.Resolve(SpeciesId.Bird, CreaturePose.Walk, false, true, Era.Tribal, false, out _));
            Assert.AreEqual("carp_young_swim", CreatureArt.Resolve(SpeciesId.Fish, CreaturePose.Run, true, true, Era.Tribal, false, out _));
            Assert.AreEqual("a_wolf_adult_dead", CreatureArt.Resolve(SpeciesId.Wolf, CreaturePose.Dead, false, true, Era.Tribal, false, out bool anim));
            Assert.IsFalse(anim);
            Assert.IsNull(CreatureArt.Resolve((SpeciesId)1000, CreaturePose.Idle, false, true, Era.Tribal, false, out _));
        }

#if !UNITY_2017_1_OR_NEWER
        [Test]
        public void AnimalKeys_MatchCreaturesJson()
        {
            string path = Path.GetFullPath(Path.Combine(ArtIndexTests.ArtDir(), "..", "WorldSimData", "creatures.json"));
            using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(path));
            var creatures = doc.RootElement.GetProperty("creatures");
            foreach (SpeciesId s in Enum.GetValues(typeof(SpeciesId)))
            {
                if (CreatureArt.IsPerson(s)) continue;
                string key = CreatureArt.PackKey(s);
                Assert.IsTrue(creatures.TryGetProperty(key, out var c), "creatures.json has no " + key);
                string dead = CreatureArt.Resolve(s, CreaturePose.Dead, false, true, Era.Tribal, false, out _);
                StringAssert.StartsWith(c.GetProperty("sprite_prefix").GetString(), dead, key);
            }
        }
#endif
    }
}
