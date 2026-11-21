using System.Collections.Generic;
using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Core.Civ;
using WorldSim.Core.Life;

namespace WorldSim.Tests
{
    /// <summary>Beta B4 core: eras, settlement arithmetic, diplomacy and deterministic pathfinding.</summary>
    public class CivCoreTests
    {
        [Test]
        public void Tier_Thresholds_Are_Monotonic()
        {
            Assert.AreEqual(SettlementTier.Camp, CivRules.TierForPopulation(0));
            Assert.AreEqual(SettlementTier.Village, CivRules.TierForPopulation(16));
            Assert.AreEqual(SettlementTier.Town, CivRules.TierForPopulation(45));
            Assert.AreEqual(SettlementTier.City, CivRules.TierForPopulation(110));
            Assert.AreEqual(SettlementTier.Metropolis, CivRules.TierForPopulation(260));
            Assert.Greater(CivRules.Housing(4), CivRules.Housing(3));
            Assert.Greater(CivRules.NextTierPopulation(3), CivRules.NextTierPopulation(2));
        }

        [Test]
        public void Buildings_Are_Wanted_In_A_Sane_Order_And_Only_Once()
        {
            ulong built = 0;
            Assert.AreEqual(Building.Huts, CivRules.NextBuilding(built, 0, 10, 0));
            built = CivRules.AddBuilding(built, Building.Huts);
            Assert.AreEqual(Building.Farm, CivRules.NextBuilding(built, 0, 10, 0));
            built = CivRules.AddBuilding(built, Building.Farm);
            built = CivRules.AddBuilding(built, Building.Farm);
            built = CivRules.AddBuilding(built, Building.Farm);
            Assert.AreEqual(3, CivRules.CountBuilt(built, Building.Farm));
            Assert.AreNotEqual(Building.Farm, CivRules.NextBuilding(built, 0, 10, 0));
            // Three copies is the cap.
            ulong capped = CivRules.AddBuilding(built, Building.Farm);
            Assert.AreEqual(3, CivRules.CountBuilt(capped, Building.Farm));
        }

        [Test]
        public void Building_Bits_Do_Not_Overlap()
        {
            ulong mask = 0;
            for (int i = 0; i < (int)Building.Count; i++) mask = CivRules.AddBuilding(mask, (Building)i);
            for (int i = 0; i < (int)Building.Count; i++)
            {
                Assert.AreEqual(1, CivRules.CountBuilt(mask, (Building)i), ((Building)i).ToString());
                Assert.IsTrue(CivRules.HasBuilding(mask, (Building)i));
            }
        }

        [Test]
        public void Era_Costs_Always_Increase_And_Beyond_Never_Ends()
        {
            int prev = 0;
            for (int era = 0; era < 20; era++)
            {
                int cost = CivRules.ResearchForEra(era);
                Assert.Greater(cost, prev, $"era {era}");
                prev = cost;
                Assert.IsNotEmpty(CivRules.EraName(era));
            }
            StringAssert.StartsWith("Beyond", CivRules.EraName(9));
            Assert.Greater(CivRules.EraWeapon(9), CivRules.EraWeapon(8));
        }

        [Test]
        public void Relation_Drift_Is_Bounded_And_Peace_Comes_Eventually()
        {
            var rng = new Pcg32(1, 2);
            int relation = 0;
            for (int i = 0; i < 10000; i++)
            {
                relation = CivRules.DriftRelation(relation, 80, 20, (int)rng.NextUInt(100));
                Assert.That(relation, Is.InRange(-100, 100));
            }
            Assert.IsTrue(CivRules.MakePeace(-100, 5000, 99));
            Assert.IsFalse(CivRules.MakePeace(-100, 10, 0));
        }

        [Test]
        public void AStar_Finds_A_Path_Around_A_Wall()
        {
            const int w = 24, h = 16;
            var blocked = new byte[w * h];
            for (int y = 0; y < h; y++) blocked[y * w + 12] = 1;
            blocked[15 * w + 12] = 0; // one gap
            var astar = new AStarGrid(w, h);
            var path = new List<int>();
            Assert.IsTrue(astar.Find(blocked, 2, 2, 20, 2, path));
            Assert.Greater(path.Count, 0);
            Assert.AreEqual(2 * w + 20, path[path.Count - 1]);
            foreach (int p in path) Assert.AreEqual(0, blocked[p]);
            // The path has to go through the gap (not across the wall).
            Assert.IsTrue(path.Contains(15 * w + 12));
        }

        [Test]
        public void AStar_Returns_False_When_The_Goal_Is_Sealed()
        {
            const int w = 12, h = 12;
            var blocked = new byte[w * h];
            for (int x = 3; x <= 8; x++) { blocked[3 * w + x] = 1; blocked[8 * w + x] = 1; }
            for (int y = 3; y <= 8; y++) { blocked[y * w + 3] = 1; blocked[y * w + 8] = 1; }
            var astar = new AStarGrid(w, h);
            var path = new List<int>();
            Assert.IsFalse(astar.Find(blocked, 1, 1, 5, 5, path));
            Assert.IsEmpty(path);
        }

        [Test]
        public void AStar_Is_Deterministic_And_Does_Not_Cut_Corners()
        {
            const int w = 20, h = 20;
            var blocked = new byte[w * h];
            blocked[5 * w + 5] = 1;
            blocked[5 * w + 6] = 1;
            blocked[6 * w + 5] = 1;
            var a = new AStarGrid(w, h);
            var p1 = new List<int>();
            var p2 = new List<int>();
            Assert.IsTrue(a.Find(blocked, 2, 2, 10, 10, p1));
            Assert.IsTrue(a.Find(blocked, 2, 2, 10, 10, p2));
            CollectionAssert.AreEqual(p1, p2);
            for (int i = 1; i < p1.Count; i++)
            {
                int ax = p1[i - 1] % w, ay = p1[i - 1] / w;
                int bx = p1[i] % w, by = p1[i] / w;
                Assert.LessOrEqual(System.Math.Abs(ax - bx) + System.Math.Abs(ay - by), 2);
                if (ax != bx && ay != by)
                {
                    Assert.AreEqual(0, blocked[ay * w + bx], "diagonal corner cut");
                    Assert.AreEqual(0, blocked[by * w + ax], "diagonal corner cut");
                }
            }
        }

        [Test]
        public void Kingdom_Names_Are_Deterministic_And_Invented()
        {
            var rng = new Pcg32(11, 22);
            string a = CivNames.Kingdom(ref rng);
            string b = CivNames.Kingdom(ref rng);
            Assert.IsNotEmpty(a);
            Assert.IsNotEmpty(b);
            var again = new Pcg32(11, 22);
            Assert.AreEqual(a, CivNames.Kingdom(ref again));
            Assert.AreEqual(b, CivNames.Kingdom(ref again));
            var used = new HashSet<string>();
            for (int i = 0; i < 50; i++)
            {
                string n = CivRules.EraName(i);
                Assert.IsNotEmpty(n);
            }
        }

        [Test]
        public void Ruler_Names_Use_Fictional_Peoples()
        {
            var rng = new Pcg32(7, 3);
            string human = CivNames.Ruler(SpeciesId.Human, ref rng);
            string elf = CivNames.Ruler(SpeciesId.Elf, ref rng);
            Assert.IsNotEmpty(human);
            Assert.IsNotEmpty(elf);
            Assert.AreNotEqual(human, elf);
        }
    }
}
