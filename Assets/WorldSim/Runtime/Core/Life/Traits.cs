namespace WorldSim.Core.Life
{
    /// <summary>
    /// Unit traits (plan A4, Beta B3). Bit index in <see cref="TraitSet"/>: persisted, only append
    /// (max 64). Groups of mutually exclusive traits share a <see cref="TraitInfo.Group"/>.
    /// </summary>
    public enum Trait : byte
    {
        Genius = 0, Smart = 1, Dull = 2,
        Strong = 3, Weak = 4,
        Brave = 5, Coward = 6,
        Kind = 7, Aggressive = 8,
        Healthy = 9, Frail = 10,
        Fertile = 11, Infertile = 12,
        LongLived = 13, ShortLived = 14,
        Fast = 15, Slow = 16,
        Charismatic = 17,
        Lucky = 18, Clumsy = 19,
        Glutton = 20, Hardy = 21,
        Curious = 22, Lazy = 23,
        Count = 24,
    }

    /// <summary>Modifiers a trait applies. Percentages are added to 100.</summary>
    public struct TraitInfo
    {
        public byte Group;          // 0 = no exclusion group
        public sbyte SpeedPct, HpPct, AttackPct, LifespanPct, FertilityPct, HungerPct;
        public sbyte ResearchPct;   // used by civilizations (B4)
        public sbyte BraveryPct;    // raises (or lowers) the danger needed before fleeing
        public sbyte AggressionPct; // drives fights and wars
        public byte BirthChancePermille; // spontaneous chance per birth (before inheritance)
    }

    /// <summary>Summed trait modifiers (percent deltas) as ints, so many traits cannot overflow.</summary>
    public struct TraitTotals
    {
        public int SpeedPct, HpPct, AttackPct, LifespanPct, FertilityPct, HungerPct, ResearchPct, BraveryPct, AggressionPct;
    }

    /// <summary>64-bit set of <see cref="Trait"/>s. Blittable.</summary>
    public struct TraitSet
    {
        public ulong Bits;
        public bool Has(Trait t) => (Bits & (1UL << (int)t)) != 0;
        public void Add(Trait t) { Bits |= 1UL << (int)t; }
        public void Remove(Trait t) { Bits &= ~(1UL << (int)t); }
        public int Count { get { int n = 0; ulong b = Bits; while (b != 0) { b &= b - 1; n++; } return n; } }
    }

    /// <summary>Trait table, combined modifiers and genetics. Pure and deterministic.</summary>
    public static class Traits
    {
        public static TraitInfo Info(Trait t)
        {
            switch (t)
            {
                case Trait.Genius: return new TraitInfo { Group = 1, ResearchPct = 100, BirthChancePermille = 8 };
                case Trait.Smart: return new TraitInfo { Group = 1, ResearchPct = 35, BirthChancePermille = 80 };
                case Trait.Dull: return new TraitInfo { Group = 1, ResearchPct = -40, BirthChancePermille = 70 };
                case Trait.Strong: return new TraitInfo { Group = 2, AttackPct = 40, HpPct = 15, BirthChancePermille = 70 };
                case Trait.Weak: return new TraitInfo { Group = 2, AttackPct = -35, HpPct = -10, BirthChancePermille = 60 };
                case Trait.Brave: return new TraitInfo { Group = 3, BraveryPct = 60, BirthChancePermille = 70 };
                case Trait.Coward: return new TraitInfo { Group = 3, BraveryPct = -50, BirthChancePermille = 60 };
                case Trait.Kind: return new TraitInfo { Group = 4, AggressionPct = -50, BirthChancePermille = 80 };
                case Trait.Aggressive: return new TraitInfo { Group = 4, AggressionPct = 70, AttackPct = 10, BirthChancePermille = 70 };
                case Trait.Healthy: return new TraitInfo { Group = 5, HpPct = 25, LifespanPct = 10, BirthChancePermille = 70 };
                case Trait.Frail: return new TraitInfo { Group = 5, HpPct = -30, LifespanPct = -15, BirthChancePermille = 50 };
                case Trait.Fertile: return new TraitInfo { Group = 6, FertilityPct = 60, BirthChancePermille = 60 };
                case Trait.Infertile: return new TraitInfo { Group = 6, FertilityPct = -90, BirthChancePermille = 25 };
                case Trait.LongLived: return new TraitInfo { Group = 7, LifespanPct = 40, BirthChancePermille = 35 };
                case Trait.ShortLived: return new TraitInfo { Group = 7, LifespanPct = -30, BirthChancePermille = 35 };
                case Trait.Fast: return new TraitInfo { Group = 8, SpeedPct = 30, BirthChancePermille = 60 };
                case Trait.Slow: return new TraitInfo { Group = 8, SpeedPct = -25, BirthChancePermille = 50 };
                case Trait.Charismatic: return new TraitInfo { ResearchPct = 5, BirthChancePermille = 40 };
                case Trait.Lucky: return new TraitInfo { Group = 9, HpPct = 5, BirthChancePermille = 40 };
                case Trait.Clumsy: return new TraitInfo { Group = 9, AttackPct = -15, BirthChancePermille = 40 };
                case Trait.Glutton: return new TraitInfo { Group = 10, HungerPct = 50, HpPct = 10, BirthChancePermille = 40 };
                case Trait.Hardy: return new TraitInfo { Group = 10, HungerPct = -35, BirthChancePermille = 40 };
                case Trait.Curious: return new TraitInfo { Group = 11, ResearchPct = 20, SpeedPct = 5, BirthChancePermille = 60 };
                case Trait.Lazy: return new TraitInfo { Group = 11, ResearchPct = -20, SpeedPct = -10, BirthChancePermille = 50 };
                default: return default;
            }
        }

        /// <summary>Sum of all trait modifiers (percent deltas).</summary>
        public static TraitTotals Combined(TraitSet set)
        {
            var r = new TraitTotals();
            for (int i = 0; i < (int)Trait.Count; i++)
            {
                if ((set.Bits & (1UL << i)) == 0) continue;
                TraitInfo t = Info((Trait)i);
                r.SpeedPct += t.SpeedPct; r.HpPct += t.HpPct; r.AttackPct += t.AttackPct;
                r.LifespanPct += t.LifespanPct; r.FertilityPct += t.FertilityPct; r.HungerPct += t.HungerPct;
                r.ResearchPct += t.ResearchPct; r.BraveryPct += t.BraveryPct; r.AggressionPct += t.AggressionPct;
            }
            return r;
        }

        /// <summary>Applies a percent delta to a value (never below 1).</summary>
        public static int Scale(int value, int pct)
        {
            long v = (long)value * (100 + pct) / 100;
            return v < 1 ? 1 : (int)v;
        }

        /// <summary>Adds <paramref name="t"/> after removing anything in its exclusion group.</summary>
        public static void AddExclusive(ref TraitSet set, Trait t)
        {
            byte g = Info(t).Group;
            if (g != 0)
                for (int i = 0; i < (int)Trait.Count; i++)
                    if (i != (int)t && Info((Trait)i).Group == g) set.Remove((Trait)i);
            set.Add(t);
        }

        /// <summary>
        /// Traits of a newborn (A4): each parent trait is inherited with 45% chance (conflicts in a
        /// group resolve in favour of the first parent), then each trait can appear spontaneously
        /// at its birth chance, and a rare mutation (2%) flips one random trait. With no parents
        /// (spawned by the player) only spontaneous traits apply.
        /// </summary>
        public static TraitSet Roll(ref Pcg32 rng, TraitSet parentA, TraitSet parentB, bool hasParents)
        {
            var set = new TraitSet();
            if (hasParents)
            {
                for (int i = 0; i < (int)Trait.Count; i++)
                {
                    if (parentB.Has((Trait)i) && rng.NextUInt(100) < 45) AddExclusive(ref set, (Trait)i);
                    if (parentA.Has((Trait)i) && rng.NextUInt(100) < 45) AddExclusive(ref set, (Trait)i);
                }
            }
            for (int i = 0; i < (int)Trait.Count; i++)
            {
                TraitInfo info = Info((Trait)i);
                if (rng.NextUInt(1000) < info.BirthChancePermille && !GroupTaken(set, info.Group, (Trait)i))
                    set.Add((Trait)i);
            }
            if (rng.NextUInt(100) < 2)
            {
                var t = (Trait)rng.NextUInt((uint)Trait.Count);
                if (set.Has(t)) set.Remove(t); else AddExclusive(ref set, t);
            }
            return set;
        }

        static bool GroupTaken(TraitSet set, byte group, Trait except)
        {
            if (group == 0) return false;
            for (int i = 0; i < (int)Trait.Count; i++)
                if (i != (int)except && set.Has((Trait)i) && Info((Trait)i).Group == group) return true;
            return false;
        }
    }
}
