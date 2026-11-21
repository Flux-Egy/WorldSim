using WorldSim.Core.Life;

namespace WorldSim.Core.Civ
{
    /// <summary>
    /// Invented kingdom, settlement, dynasty and creed names (Beta B4). Built from syllables that
    /// belong to the game's fictional peoples; none of them names a real place, people or belief.
    /// Deterministic from the RNG. Main thread only (strings).
    /// </summary>
    public static class CivNames
    {
        static readonly string[] Roots =
        {
            "Vael", "Bran", "Cor", "Dun", "Eld", "Fen", "Gar", "Hal", "Ith", "Jor", "Kel", "Lor",
            "Mor", "Nar", "Orin", "Pel", "Quen", "Rav", "Syl", "Tor", "Ulm", "Vey", "Wren", "Yar",
            "Zel", "Ash", "Brume", "Cinder", "Dawn", "Ember", "Frost", "Glim", "Hollow", "Iron",
            "Jade", "Kite", "Lark", "Moss", "Night", "Oak", "Pine", "Quill", "Reed", "Stone",
            "Thorn", "Umber", "Vine", "Willow", "Yew", "Zephyr",
        };

        static readonly string[] KingdomForms =
        {
            "Kingdom of {0}", "Realm of {0}", "Dominion of {0}", "League of {0}", "Crown of {0}",
            "Concord of {0}", "Halls of {0}", "March of {0}", "{0} Reach", "{0} Vale",
            "High {0}", "Old {0}",
        };

        static readonly string[] SettlementSuffix =
        {
            "ford", "hold", "rest", "watch", "field", "reach", "gate", "spire", "haven", "moor",
            "glen", "hollow", "stead", "crag", "bay", "crest", "fall", "wick", "bourne", "dale",
        };

        static readonly string[] Creeds =
        {
            "The Quiet Flame", "The Hollow Star", "The Turning Root", "The Silver Tide",
            "The Long Song", "The Stone Dream", "The Open Hand", "The Wandering Light",
            "The Deep Choir", "The First Dawn", "The Unbroken Thread", "The Still Water",
            "The Bright Path", "The Nine Lanterns", "The Sleeping Mountain", "The Rain That Sings",
            "The Last Ember", "The Thousand Leaves", "The Woven Sky", "The Patient River",
        };

        static readonly string[] DynastyForms =
        {
            "House {0}", "Clan {0}", "Line of {0}", "Kin {0}", "The {0} Folk", "Blood of {0}",
        };

        public static string Kingdom(ref Pcg32 rng)
        {
            string root = Roots[rng.NextUInt((uint)Roots.Length)];
            string form = KingdomForms[rng.NextUInt((uint)KingdomForms.Length)];
            return form.Replace("{0}", root);
        }

        public static string Settlement(string kingdomName, ref Pcg32 rng)
        {
            // The settlement borrows a sound from its kingdom, then takes a place suffix.
            string root = Roots[rng.NextUInt((uint)Roots.Length)];
            return root + SettlementSuffix[rng.NextUInt((uint)SettlementSuffix.Length)];
        }

        public static string Creed(ref Pcg32 rng) => Creeds[rng.NextUInt((uint)Creeds.Length)];

        public static string Dynasty(ref Pcg32 rng)
        {
            string root = Roots[rng.NextUInt((uint)Roots.Length)];
            string form = DynastyForms[rng.NextUInt((uint)DynastyForms.Length)];
            return form.Replace("{0}", root);
        }

        /// <summary>Ruler given name plus a dynasty, e.g. "Maren of House Vael".</summary>
        public static string Ruler(SpeciesId people, ref Pcg32 rng)
        {
            return NameGenerator.Person(people, ref rng) + " of " + Dynasty(ref rng);
        }

        public static string Unique(string name, System.Collections.Generic.HashSet<string> used)
        {
            if (used.Add(name)) return name;
            for (int i = 2; i < 100; i++)
            {
                string candidate = name + " " + CivRules.Roman(i);
                if (used.Add(candidate)) return candidate;
            }
            return name;
        }
    }
}
