using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Core.Life;

namespace WorldSim.Tests
{
    /// <summary>Beta B3 core data: species, traits and genetics (plan A4), names.</summary>
    public class LifeCoreTests
    {
        [Test]
        public void EverySpecies_HasSaneParameters()
        {
            foreach (SpeciesId id in SpeciesTable.All)
            {
                SpeciesDef d = SpeciesTable.Get(id);
                Assert.AreEqual(id, d.Id);
                Assert.Greater(d.SpeedQ16, 0, $"{id} speed");
                Assert.Greater(d.MaxHp, 0, $"{id} hp");
                Assert.Greater(d.LifespanTicks, d.AdultAtTicks, $"{id} lifespan");
                Assert.AreNotEqual(0, (int)d.Habitat, $"{id} habitat");
            }
        }

        [Test]
        public void RolledTraits_NeverContainTwoFromOneGroup()
        {
            var rng = new Pcg32(5, 9);
            var parentA = new TraitSet(); parentA.Add(Trait.Genius); parentA.Add(Trait.Strong);
            var parentB = new TraitSet(); parentB.Add(Trait.Dull); parentB.Add(Trait.Weak);
            for (int i = 0; i < 5000; i++)
            {
                TraitSet t = Traits.Roll(ref rng, parentA, parentB, hasParents: i % 2 == 0);
                for (int a = 0; a < (int)Trait.Count; a++)
                    for (int b = a + 1; b < (int)Trait.Count; b++)
                    {
                        byte g = Traits.Info((Trait)a).Group;
                        if (g != 0 && g == Traits.Info((Trait)b).Group)
                            Assert.IsFalse(t.Has((Trait)a) && t.Has((Trait)b), $"{(Trait)a} and {(Trait)b} together");
                    }
            }
        }

        [Test]
        public void Inheritance_MakesParentTraitsCommon()
        {
            var rng = new Pcg32(7, 1);
            var genius = new TraitSet(); genius.Add(Trait.Genius);
            int withParents = 0, without = 0;
            for (int i = 0; i < 4000; i++)
            {
                if (Traits.Roll(ref rng, genius, genius, true).Has(Trait.Genius)) withParents++;
                if (Traits.Roll(ref rng, default, default, false).Has(Trait.Genius)) without++;
            }
            Assert.Greater(withParents, 4000 * 50 / 100, "two genius parents pass it on often");
            Assert.Less(without, 4000 * 3 / 100, "spontaneous genius stays rare");
        }

        [Test]
        public void Roll_IsDeterministic()
        {
            var a = new Pcg32(99, 3); var b = new Pcg32(99, 3);
            var p = new TraitSet { Bits = 0b1010101010101UL };
            for (int i = 0; i < 200; i++)
                Assert.AreEqual(Traits.Roll(ref a, p, p, true).Bits, Traits.Roll(ref b, p, p, true).Bits);
        }

        [Test]
        public void Combined_SumsModifiers()
        {
            var s = new TraitSet(); s.Add(Trait.Genius); s.Add(Trait.Curious); s.Add(Trait.Fast);
            TraitTotals t = Traits.Combined(s);
            Assert.AreEqual(120, t.ResearchPct);
            Assert.AreEqual(35, t.SpeedPct);
            Assert.AreEqual(150, Traits.Scale(100, 50));
            Assert.AreEqual(1, Traits.Scale(10, -200), "never below 1");
        }

        [Test]
        public void Names_AreDeterministic_AndNonEmpty()
        {
            foreach (var people in new[] { SpeciesId.Human, SpeciesId.Elf, SpeciesId.Orc, SpeciesId.Dwarf })
            {
                var a = new Pcg32(1, (ulong)people); var b = new Pcg32(1, (ulong)people);
                for (int i = 0; i < 50; i++)
                {
                    string n = NameGenerator.Person(people, ref a);
                    Assert.AreEqual(n, NameGenerator.Person(people, ref b));
                    Assert.GreaterOrEqual(n.Length, 3);
                    Assert.IsTrue(char.IsUpper(n[0]));
                }
            }
        }
    }
}
