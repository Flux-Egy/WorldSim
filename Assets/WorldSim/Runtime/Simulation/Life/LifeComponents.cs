using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;
using WorldSim.Core.Life;

namespace WorldSim.Simulation.Life
{
    /// <summary>What a creature is doing (Beta B3 utility AI, §5.2). Persisted: only append.</summary>
    public enum CreatureAction : byte { Idle = 0, Wander = 1, Eat = 2, Drink = 3, Sleep = 4, Flee = 5, Hunt = 6, Mate = 7 }

    /// <summary>Identity of a living creature.</summary>
    public struct Creature : IComponentData
    {
        public SpeciesId Species;
        public uint StableId;      // never reused; deterministic tie-breaks and RNG keys
        public byte Sex;           // 0 female, 1 male
        public uint BornTick;
        public uint LifespanTicks; // after traits
        public uint LastBirthTick;
    }

    public struct CreatureTraits : IComponentData { public TraitSet Set; }

    /// <summary>Position and movement in Q16.16 tile units (integer-only, deterministic).</summary>
    public struct Mover : IComponentData
    {
        public int2 PosQ;
        public int2 TargetQ;
        public int SpeedQ;         // per tick, after traits
        public byte Moving;
        public byte FacingLeft;
    }

    public struct Vitals : IComponentData
    {
        public short Hp, MaxHp, Attack;
        public byte Hunger, Thirst, Fatigue; // 0 = fine .. 255 = critical
        public byte Bravery;                  // flee threshold modifier (traits)
    }

    public struct Brain : IComponentData
    {
        public CreatureAction Action;
        public uint NextThinkTick;
        public Entity Target;      // prey or mate
        public ushort ActionTicks; // remaining ticks for timed actions (sleep, eat)
    }

    /// <summary>Display name (peoples only).</summary>
    public struct CreatureName : IComponentData { public FixedString32Bytes Value; }

    /// <summary>Spawn request (player powers and births). Drained by <see cref="CreatureSpawnSystem"/>.</summary>
    public struct SpawnCreatureCommand : IBufferElementData
    {
        public SpeciesId Species;
        public int2 Tile;
        public byte HasParents;
        public TraitSet ParentA, ParentB;
    }

    /// <summary>Tag of the singleton holding the spawn queue, plus life-wide counters.</summary>
    public struct LifeState : IComponentData
    {
        public uint NextStableId;
        public int Population;
        public int Peoples;   // sapient count
        public uint Births, Deaths;
    }

    public static class LifeLimits
    {
        public const int MaxCreatures = 3000;
        public const int ThinkInterval = 5;     // ticks between decisions (staggered by StableId)
        public const int CellShift = 3;         // spatial cells of 8x8 tiles
    }
}
