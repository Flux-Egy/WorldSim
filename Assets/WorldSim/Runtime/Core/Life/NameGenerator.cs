namespace WorldSim.Core.Life
{
    /// <summary>
    /// Invented names per people (Beta B3), built from syllables so they sound consistent within
    /// a people and refer to nothing real. Deterministic from the RNG. Main thread only (strings).
    /// </summary>
    public static class NameGenerator
    {
        static readonly string[][] Start =
        {
            new[] { "Al", "Bran", "Cor", "Da", "Ed", "Fen", "Gar", "Hal", "Ir", "Jor", "Ka", "Le", "Mar", "Nor", "Os", "Per", "Ro", "Sa", "Tor", "Vel" }, // Human
            new[] { "Ae", "Cae", "El", "Fae", "Gil", "Il", "Lae", "Mi", "Nae", "Si", "Tha", "Ya", "Ael", "Ny", "Ri", "Syl" },                            // Elf
            new[] { "Gr", "Kr", "Mog", "Ug", "Zug", "Brak", "Dur", "Gor", "Hruk", "Nar", "Rok", "Shag", "Th", "Vor" },                                  // Orc
            new[] { "Bal", "Dor", "Dw", "Fun", "Gim", "Kil", "Mor", "Nal", "Or", "Thr", "Bof", "Dur", "Gro", "Hil" },                                   // Dwarf
        };
        static readonly string[][] Mid =
        {
            new[] { "a", "e", "i", "o", "an", "en", "ar", "or", "el", "in" },
            new[] { "a", "e", "i", "ae", "ia", "ri", "la", "le", "th", "ne" },
            new[] { "a", "u", "o", "ag", "ug", "ra", "ok", "ru" },
            new[] { "a", "o", "i", "un", "ar", "or", "in", "ur" },
        };
        static readonly string[][] End =
        {
            new[] { "n", "d", "ric", "las", "mund", "ton", "wyn", "sa", "ra", "ell", "en", "a", "o" },
            new[] { "iel", "wen", "ndor", "lith", "ras", "thil", "riel", "nor", "wyn", "ae" },
            new[] { "k", "g", "gash", "nak", "dush", "rag", "uk", "tar", "zog" },
            new[] { "in", "li", "rin", "dain", "grim", "bur", "nor", "ek", "dal" },
        };

        /// <summary>A personal name for a member of <paramref name="people"/> (Human, Elf, Orc, Dwarf).</summary>
        public static string Person(SpeciesId people, ref Pcg32 rng)
        {
            int k = people == SpeciesId.Elf ? 1 : people == SpeciesId.Orc ? 2 : people == SpeciesId.Dwarf ? 3 : 0;
            string a = Start[k][rng.NextUInt((uint)Start[k].Length)];
            string b = rng.NextUInt(100) < 55 ? Mid[k][rng.NextUInt((uint)Mid[k].Length)] : "";
            string c = End[k][rng.NextUInt((uint)End[k].Length)];
            return a + b + c;
        }
    }
}
