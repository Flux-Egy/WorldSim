namespace WorldSim.Core.Life
{
    /// <summary>Built-in species (Beta B3). Persisted ids: only append. Mods add theirs from 1000.</summary>
    public enum SpeciesId : ushort
    {
        Human = 1, Elf = 2, Orc = 3, Dwarf = 4,
        Rabbit = 20, Sheep = 21, Deer = 22, Cow = 23,
        Wolf = 40, Bear = 41, Fox = 42,
        Bird = 60,
        Fish = 70,
    }

    public enum CreatureKind : byte { Sapient = 0, Herbivore = 1, Predator = 2, Bird = 3, Fish = 4 }

    [System.Flags]
    public enum Habitat : byte { Land = 1, Water = 2, Air = 4 }

    /// <summary>
    /// Static, blittable species parameters (§5.1). All rates are per simulation tick (10 Hz) in
    /// fixed units so the simulation stays integer-only and deterministic.
    /// </summary>
    public struct SpeciesDef
    {
        public SpeciesId Id;
        public CreatureKind Kind;
        public Habitat Habitat;
        public int SpeedQ16;        // tiles per tick, Q16.16 (e.g. One/10 = 1 tile per second)
        public short MaxHp;
        public short Attack;        // damage per hit
        public int LifespanTicks;   // average; traits scale it
        public int AdultAtTicks;
        public byte HungerRate;     // hunger points per 10 ticks (0..255 scale)
        public byte ThirstRate;
        public byte FertilityPct;   // chance per mating attempt
        public byte LitterMax;
        public byte SightTiles;
        public uint ColorA, ColorB; // packed RGBA (body, detail) for procedural sprites

        public bool IsSapient => Kind == CreatureKind.Sapient;
        public bool IsPredator => Kind == CreatureKind.Predator;
        public bool EatsPlants => Kind == CreatureKind.Herbivore || Kind == CreatureKind.Sapient || Kind == CreatureKind.Bird;
    }

    /// <summary>The built-in species table. Pure data; mods will extend it through the ModAPI (B?).</summary>
    public static class SpeciesTable
    {
        const int One = FixedNoise.One;
        const int Second = 10;          // ticks
        const int Year = 600;           // ticks: one in-game year = 60 s at 1x

        static uint C(int r, int g, int b) => unchecked((uint)(r | (g << 8) | (b << 16) | (255 << 24)));

        public static readonly SpeciesId[] All =
        {
            SpeciesId.Human, SpeciesId.Elf, SpeciesId.Orc, SpeciesId.Dwarf,
            SpeciesId.Rabbit, SpeciesId.Sheep, SpeciesId.Deer, SpeciesId.Cow,
            SpeciesId.Wolf, SpeciesId.Bear, SpeciesId.Fox, SpeciesId.Bird, SpeciesId.Fish,
        };

        public static SpeciesDef Get(SpeciesId id)
        {
            switch (id)
            {
                case SpeciesId.Human: return Sapient(id, One / 9, 100, 70 * Year, C(232, 190, 150), C(70, 110, 190));
                case SpeciesId.Elf: return Sapient(id, One / 8, 85, 160 * Year, C(240, 214, 180), C(70, 150, 90));
                case SpeciesId.Orc: return Sapient(id, One / 9, 140, 50 * Year, C(110, 160, 80), C(130, 70, 50));
                case SpeciesId.Dwarf: return Sapient(id, One / 11, 130, 120 * Year, C(220, 170, 130), C(150, 100, 60));
                case SpeciesId.Rabbit: return Animal(id, CreatureKind.Herbivore, One / 7, 20, 2, 8 * Year, 60, 4, C(196, 180, 160), C(240, 236, 230));
                case SpeciesId.Sheep: return Animal(id, CreatureKind.Herbivore, One / 14, 40, 3, 12 * Year, 40, 2, C(240, 240, 236), C(60, 60, 60));
                case SpeciesId.Deer: return Animal(id, CreatureKind.Herbivore, One / 8, 50, 5, 15 * Year, 30, 1, C(170, 120, 70), C(240, 230, 210));
                case SpeciesId.Cow: return Animal(id, CreatureKind.Herbivore, One / 16, 80, 6, 18 * Year, 30, 1, C(240, 240, 240), C(50, 40, 40));
                case SpeciesId.Wolf: return Animal(id, CreatureKind.Predator, One / 7, 70, 14, 12 * Year, 25, 2, C(130, 130, 136), C(80, 80, 86));
                case SpeciesId.Bear: return Animal(id, CreatureKind.Predator, One / 11, 160, 26, 25 * Year, 15, 1, C(110, 76, 50), C(70, 48, 32));
                case SpeciesId.Fox: return Animal(id, CreatureKind.Predator, One / 8, 40, 8, 10 * Year, 30, 2, C(220, 120, 50), C(250, 245, 240));
                case SpeciesId.Bird:
                {
                    var d = Animal(id, CreatureKind.Bird, One / 5, 15, 1, 6 * Year, 40, 2, C(60, 60, 70), C(230, 170, 60));
                    d.Habitat = Habitat.Air | Habitat.Land | Habitat.Water;
                    return d;
                }
                case SpeciesId.Fish:
                {
                    var d = Animal(id, CreatureKind.Fish, One / 8, 10, 0, 5 * Year, 50, 3, C(110, 170, 210), C(230, 240, 250));
                    d.Habitat = Habitat.Water;
                    d.ThirstRate = 0;
                    return d;
                }
                default: return default;
            }
        }

        static SpeciesDef Sapient(SpeciesId id, int speed, short hp, int life, uint skin, uint cloth) => new SpeciesDef
        {
            Id = id, Kind = CreatureKind.Sapient, Habitat = Habitat.Land, SpeedQ16 = speed, MaxHp = hp, Attack = 10,
            LifespanTicks = life, AdultAtTicks = life / 5, HungerRate = 3, ThirstRate = 4, FertilityPct = 30,
            LitterMax = 1, SightTiles = 10, ColorA = skin, ColorB = cloth,
        };

        static SpeciesDef Animal(SpeciesId id, CreatureKind kind, int speed, short hp, short atk, int life, byte fert, byte litter, uint a, uint b) => new SpeciesDef
        {
            Id = id, Kind = kind, Habitat = Habitat.Land, SpeedQ16 = speed, MaxHp = hp, Attack = atk, LifespanTicks = life,
            AdultAtTicks = life / 6, HungerRate = (byte)(kind == CreatureKind.Predator ? 4 : 3), ThirstRate = 4,
            FertilityPct = fert, LitterMax = litter, SightTiles = (byte)(kind == CreatureKind.Predator ? 9 : 7), ColorA = a, ColorB = b,
        };
    }
}
