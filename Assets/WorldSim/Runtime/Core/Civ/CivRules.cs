using System;
using WorldSim.Core.Life;

namespace WorldSim.Core.Civ
{
    /// <summary>Settlement size tiers (Beta B4). Persisted: only append.</summary>
    public enum SettlementTier : byte { Camp = 0, Village = 1, Town = 2, City = 3, Metropolis = 4 }

    /// <summary>
    /// Eras are open-ended (plan A1): after the ninth era the game keeps going with "Beyond" tiers
    /// that cost more and raise weapon strength. Persisted indices: only append before Beyond.
    /// </summary>
    public enum Era : byte
    {
        Stone = 0, Bronze = 1, Iron = 2, Medieval = 3, Renaissance = 4,
        Industrial = 5, Modern = 6, Space = 7, Beyond = 8,
    }

    /// <summary>Buildings a settlement can raise. The 64-bit mask is persisted, so only append.</summary>
    public enum Building : byte
    {
        Huts = 0, Farm = 1, Granary = 2, Lumberyard = 3, Quarry = 4, Palisade = 5,
        Shrine = 6, Barracks = 7, Market = 8, Library = 9, Workshop = 10, Watchtower = 11,
        Aqueduct = 12, University = 13, Factory = 14, Starport = 15,
        Count = 16,
    }

    /// <summary>What happened, for the chronicle. Persisted in saves later, only append.</summary>
    public enum ChronicleKind : byte
    {
        WorldSettled = 0, SettlementFounded = 1, TierUp = 2, EraUp = 3, WarDeclared = 4,
        PeaceMade = 5, Battle = 6, SettlementCaptured = 7, KingdomFallen = 8, Disaster = 9,
        CreedSpread = 10, GoldenAge = 11, Plague = 12, Migration = 13,
    }

    /// <summary>Player-triggered world powers (Beta B5). Only append.</summary>
    public enum PowerKind : byte
    {
        Meteor = 0, Quake = 1, Storm = 2, Fire = 3, Bloom = 4, Bless = 5, Curse = 6, Heal = 7,
    }

    /// <summary>
    /// Pure civilization arithmetic: tiers, housing, production, research, diplomacy and eras.
    /// Integer-only and independent of Unity so the exact same rules can be unit-tested in CI.
    /// </summary>
    public static class CivRules
    {
        public const int MaxKingdoms = 12;
        public const int MaxSettlements = 64;
        public const int YearsPerTick = 600; // 10 Hz: one year every 60 s at 1x (matches species table)

        // ---- settlements ----

        public static SettlementTier TierForPopulation(int population)
        {
            if (population >= 260) return SettlementTier.Metropolis;
            if (population >= 110) return SettlementTier.City;
            if (population >= 45) return SettlementTier.Town;
            if (population >= 16) return SettlementTier.Village;
            return SettlementTier.Camp;
        }

        public static int NextTierPopulation(int tier)
        {
            switch ((SettlementTier)tier)
            {
                case SettlementTier.Camp: return 16;
                case SettlementTier.Village: return 45;
                case SettlementTier.Town: return 110;
                case SettlementTier.City: return 260;
                default: return int.MaxValue;
            }
        }

        /// <summary>How many residents the huts and houses can hold at this tier.</summary>
        public static int Housing(int tier) => 14 + tier * 26 + tier * tier * 8;
        public static int WorkRadius(int tier) => 4 + tier * 2;
        public static int WallHp(int tier) => 90 + tier * 120;
        public static int FoodPerPerson(int population) => 1 + population / 24; // per production step
        public static int ResearchPerPopulation(int population) => population / 5 + 1;

        /// <summary>Production step: food from near farms/fertile land, wood and stone from near tiles.</summary>
        public static int FoodYield(int fertileTiles, int farms, int population)
            => fertileTiles / 3 + farms * 4 + 2 - FoodPerPerson(population);

        public static int WoodYield(int forestTiles, int lumberyards) => forestTiles / 5 + lumberyards * 2;
        public static int StoneYield(int mountainTiles, int quarries) => mountainTiles / 5 + quarries * 2;
        public static int GoldYield(int markets, int population) => markets * 2 + population / 30;

        /// <summary>Research cost of the next era. Beyond eras keep growing (open-ended).</summary>
        public static int ResearchForEra(int eraLevel)
        {
            int e = eraLevel < 0 ? 0 : eraLevel;
            int baseCost = 140 + e * e * 55 + e * 90;
            if (e > (int)Era.Beyond) baseCost += (e - (int)Era.Beyond) * 900;
            return baseCost;
        }

        public static string EraName(int eraLevel)
        {
            if (eraLevel < 0) eraLevel = 0;
            if (eraLevel <= (int)Era.Beyond) return ((Era)eraLevel).ToString();
            return "Beyond " + Roman(eraLevel - (int)Era.Beyond);
        }

        public static int EraWeapon(int eraLevel) => 10 + Math.Max(0, eraLevel) * 7;

        public static string Roman(int n)
        {
            if (n <= 0) return "I";
            // Small, deterministic numerals; levels above 30 simply use decimal.
            if (n > 30) return n.ToString();
            int[] values = { 10, 9, 5, 4, 1 };
            string[] symbols = { "X", "IX", "V", "IV", "I" };
            var s = new System.Text.StringBuilder();
            for (int i = 0; i < values.Length; i++)
                while (n >= values[i]) { s.Append(symbols[i]); n -= values[i]; }
            return s.ToString();
        }

        // ---- buildings ----

        public static int BuildingCost(Building b)
        {
            switch (b)
            {
                case Building.Huts: return 12;
                case Building.Farm: return 20;
                case Building.Granary: return 28;
                case Building.Lumberyard: return 24;
                case Building.Quarry: return 26;
                case Building.Palisade: return 35;
                case Building.Shrine: return 30;
                case Building.Barracks: return 40;
                case Building.Market: return 45;
                case Building.Library: return 50;
                case Building.Workshop: return 55;
                case Building.Watchtower: return 60;
                case Building.Aqueduct: return 70;
                case Building.University: return 90;
                case Building.Factory: return 120;
                case Building.Starport: return 180;
                default: return 999;
            }
        }

        /// <summary>Earliest era that allows a building. Beyond gets everything.</summary>
        public static int BuildingEra(Building b)
        {
            switch (b)
            {
                case Building.Huts: return 0;
                case Building.Farm: return 0;
                case Building.Granary: return 1;
                case Building.Lumberyard: return 0;
                case Building.Quarry: return 1;
                case Building.Palisade: return 1;
                case Building.Shrine: return 1;
                case Building.Barracks: return 2;
                case Building.Market: return 2;
                case Building.Library: return 3;
                case Building.Workshop: return 3;
                case Building.Watchtower: return 3;
                case Building.Aqueduct: return 4;
                case Building.University: return 5;
                case Building.Factory: return 6;
                case Building.Starport: return 8;
                default: return 8;
            }
        }

        /// <summary>
        /// The next building a settlement wants, given what it already has, its era and its
        /// population. Deterministic order: food first, then safety, then knowledge and wealth.
        /// </summary>
        public static Building NextBuilding(ulong built, int eraLevel, int population, int tier)
        {
            // Priority list; each entry is raised once, except Farms (up to 3) and Huts (tier).
            for (int i = 0; i < (int)Building.Count; i++)
            {
                var b = (Building)i;
                if (BuildingEra(b) > eraLevel) continue;
                int wanted = b == Building.Farm ? 3 : b == Building.Huts ? 1 + tier / 2 : 1;
                if (CountBuilt(built, b) >= wanted) continue;
                if ((b == Building.Shrine || b == Building.Library || b == Building.Market) && population < 30) continue;
                if ((b == Building.Barracks || b == Building.Watchtower) && population < 45) continue;
                if (b == Building.University && population < 120) continue;
                if (b == Building.Factory && population < 150) continue;
                return b;
            }
            return Building.Count;
        }

        public static int CountBuilt(ulong mask, Building b)
        {
            // Two bits per building are reserved for how many were raised (0..3); the first copy
            // is bit 2*i. This keeps one ulong for sixteen building kinds (plan B4 scope).
            int shift = (int)b * 2;
            return (int)((mask >> shift) & 3UL);
        }

        public static ulong AddBuilding(ulong mask, Building b)
        {
            int shift = (int)b * 2;
            int n = (int)((mask >> shift) & 3UL);
            if (n >= 3) return mask;
            return (mask & ~(3UL << shift)) | ((ulong)(n + 1) << shift);
        }

        public static bool HasBuilding(ulong mask, Building b) => CountBuilt(mask, b) > 0;

        // ---- kingdom colours (distinct on the map, no meaning attached) ----

        static readonly uint[] Colors =
        {
            0xE05A5A, 0x4E8FE0, 0x64C06A, 0xD9A641, 0x9B6BD6, 0xE08A45,
            0x55C4C4, 0xD65E9E, 0x8CA84C, 0xC46B4A, 0x6C86C8, 0xC7C25A,
        };

        public static uint KingdomColor(int index) => Colors[((index % Colors.Length) + Colors.Length) % Colors.Length];

        // ---- diplomacy ----

        /// <summary>
        /// A pair's relation drifts toward the average of the two peoples' aggression. Returns the
        /// new relation in [-100, 100].
        /// </summary>
        public static int DriftRelation(int relation, int aggressionA, int aggressionB, int roll0To99)
        {
            int pull = (aggressionA + aggressionB) / 2 - 50; // -50 .. +50
            int step = (roll0To99 - 50) / 25 + pull / 25;
            int r = relation + step;
            if (r > 100) r = 100;
            if (r < -100) r = -100;
            return r;
        }

        public static bool DeclareWar(int relation, int aggression, int roll0To99)
            => relation < 25 && roll0To99 < aggression / 3 + (relation < 0 ? 12 : 0);

        public static bool MakePeace(int relation, int warTicks, int roll0To99)
            => warTicks > 1800 && (relation > -35 || roll0To99 > 82);

        public static int WarCostPerTick(int population) => 1 + population / 120;

        // ---- powers ----

        public static int PowerRadius(PowerKind p)
        {
            switch (p)
            {
                case PowerKind.Meteor: return 3;
                case PowerKind.Quake: return 6;
                case PowerKind.Storm: return 5;
                case PowerKind.Fire: return 3;
                case PowerKind.Bloom: return 5;
                case PowerKind.Bless: return 4;
                case PowerKind.Curse: return 4;
                case PowerKind.Heal: return 4;
                default: return 3;
            }
        }

        public static int PowerCooldownTicks(PowerKind p)
        {
            switch (p)
            {
                case PowerKind.Meteor: return 900;
                case PowerKind.Quake: return 1200;
                case PowerKind.Storm: return 700;
                case PowerKind.Fire: return 500;
                case PowerKind.Bloom: return 400;
                case PowerKind.Bless: return 600;
                case PowerKind.Curse: return 600;
                case PowerKind.Heal: return 500;
                default: return 500;
            }
        }
    }
}
