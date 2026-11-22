using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;
using WorldSim.Core;
using WorldSim.Core.Life;

namespace WorldSim.Simulation.Life
{
    /// <summary>Shared world queries for life systems (pure, Burst-compatible).</summary>
    public static class LifeRules
    {
        public const int One = FixedNoise.One;

        public static int2 TileOf(int2 posQ) => new int2(posQ.x >> 16, posQ.y >> 16);
        public static int2 CenterQ(int2 tile) => new int2((tile.x << 16) + One / 2, (tile.y << 16) + One / 2);

        public static bool CanStand(SpeciesDef d, TileData t)
        {
            if ((d.Habitat & Habitat.Air) != 0) return true;
            bool water = t.IsWater;
            if ((d.Habitat & Habitat.Water) != 0 && (d.Habitat & Habitat.Land) == 0) return water;
            return !water && t.BiomeId != (byte)Biome.Lava;
        }

        public static bool Edible(TileData t)
        {
            var d = (Decoration)t.DecorationId;
            if (d == Decoration.BerryBush || d == Decoration.Bush || d == Decoration.TallGrass || d == Decoration.Flowers) return true;
            switch ((Biome)t.BiomeId)
            {
                case Biome.Meadow: case Biome.Forest: case Biome.Savanna: case Biome.Jungle: case Biome.BirchForest:
                case Biome.PineTaiga: case Biome.Swamp: case Biome.Glimmerwood: case Biome.Tundra: case Biome.FungalGrove:
                case Biome.FlowerField: case Biome.Steppe: case Biome.Farmland: case Biome.RockyHighland:
                    return true;
                default: return false;
            }
        }

        public static bool IsPrey(SpeciesId hunter, SpeciesId prey)
        {
            switch (hunter)
            {
                case SpeciesId.Wolf: return prey == SpeciesId.Rabbit || prey == SpeciesId.Sheep || prey == SpeciesId.Deer || prey == SpeciesId.Cow;
                case SpeciesId.Fox: return prey == SpeciesId.Rabbit || prey == SpeciesId.Bird;
                case SpeciesId.Bear: return prey == SpeciesId.Deer || prey == SpeciesId.Sheep || prey == SpeciesId.Cow || prey == SpeciesId.Fish;
                case SpeciesId.Human: case SpeciesId.Elf: case SpeciesId.Orc: case SpeciesId.Dwarf:
                    return prey == SpeciesId.Rabbit || prey == SpeciesId.Deer || prey == SpeciesId.Sheep || prey == SpeciesId.Cow || prey == SpeciesId.Fish;
                default: return false;
            }
        }

        public static bool IsThreat(SpeciesDef self, SpeciesId other)
        {
            if (self.Kind == CreatureKind.Fish) return other == SpeciesId.Bear;
            if (self.Kind == CreatureKind.Herbivore || self.Kind == CreatureKind.Bird) return IsPrey(other, self.Id);
            if (self.Kind == CreatureKind.Sapient) return other == SpeciesId.Bear || other == SpeciesId.Wolf;
            return false;
        }

        public static long ISqrt(long v)
        {
            if (v <= 0) return 0;
            long r = (long)math.sqrt((double)v);
            while (r * r > v) r--;
            while ((r + 1) * (r + 1) <= v) r++;
            return r;
        }
    }

    /// <summary>
    /// Creates creatures from <see cref="SpawnCreatureCommand"/>s (player spawns and births).
    /// Managed (names are strings), runs first in the simulation tick.
    /// </summary>
    [UpdateInGroup(typeof(SimulationTickGroup))]
    [UpdateAfter(typeof(SimulationClockSystem))]
    public partial struct CreatureSpawnSystem : ISystem
    {
        EntityArchetype _archetype, _sapientArchetype;

        public void OnCreate(ref SystemState state)
        {
            Entity e = state.EntityManager.CreateEntity(typeof(LifeState));
            state.EntityManager.AddBuffer<SpawnCreatureCommand>(e);
            state.EntityManager.SetComponentData(e, new LifeState { NextStableId = 1 });
            _archetype = state.EntityManager.CreateArchetype(typeof(Creature), typeof(CreatureTraits), typeof(Mover), typeof(Vitals), typeof(Brain));
            _sapientArchetype = state.EntityManager.CreateArchetype(typeof(Creature), typeof(CreatureTraits), typeof(Mover), typeof(Vitals), typeof(Brain), typeof(CreatureName));
            state.RequireForUpdate<WorldMap>();
            state.RequireForUpdate<SimulationClock>();
        }

        public void OnUpdate(ref SystemState state)
        {
            Entity queueEntity = SystemAPI.GetSingletonEntity<LifeState>();
            DynamicBuffer<SpawnCreatureCommand> queue = state.EntityManager.GetBuffer<SpawnCreatureCommand>(queueEntity);
            if (queue.Length == 0) return;
            var commands = queue.ToNativeArray(Allocator.Temp);
            queue.Clear();

            WorldMap map = SystemAPI.GetSingleton<WorldMap>();
            LifeState life = state.EntityManager.GetComponentData<LifeState>(queueEntity);
            uint tick = (uint)SystemAPI.GetSingleton<SimulationClock>().Tick;
            ulong agentsSeed = new WorldSeed(map.Seed).Derive(SeedStream.Agents);

            for (int i = 0; i < commands.Length; i++)
            {
                if (!map.Tiles.IsCreated || life.Population >= LifeLimits.MaxCreatures) break;
                SpawnCreatureCommand c = commands[i];
                SpeciesDef d = SpeciesTable.Get(c.Species);
                if (d.MaxHp == 0) continue;
                if (!FindStandable(map, d, c.Tile, out int2 tile)) continue;

                uint id = life.NextStableId++;
                var rng = Pcg32.ForKey(agentsSeed, id);
                TraitSet traits = Traits.Roll(ref rng, c.ParentA, c.ParentB, c.HasParents != 0);
                TraitTotals mod = Traits.Combined(traits);
                int jitter = (int)rng.NextUInt(41) - 20;                        // +-20% natural lifespan spread
                uint lifespan = (uint)Traits.Scale(Traits.Scale(d.LifespanTicks, mod.LifespanPct), jitter);

                Entity e = state.EntityManager.CreateEntity(d.IsSapient ? _sapientArchetype : _archetype);
                state.EntityManager.SetComponentData(e, new Creature
                {
                    // Births start young; creatures placed by the world or the player start as young adults, so a
                    // new world's herds and peoples can have families straight away (uint arithmetic wraps on purpose).
                    Species = c.Species, StableId = id, Sex = (byte)rng.NextUInt(2),
                    BornTick = c.HasParents != 0 ? tick : unchecked(tick - (uint)d.AdultAtTicks), LifespanTicks = lifespan,
                    LastBirthTick = tick,
                });
                state.EntityManager.SetComponentData(e, new CreatureTraits { Set = traits });
                int2 pos = LifeRules.CenterQ(tile);
                state.EntityManager.SetComponentData(e, new Mover { PosQ = pos, TargetQ = pos, SpeedQ = Traits.Scale(d.SpeedQ16, mod.SpeedPct) });
                short hp = (short)Traits.Scale(d.MaxHp, mod.HpPct);
                state.EntityManager.SetComponentData(e, new Vitals
                {
                    Hp = hp, MaxHp = hp, Attack = (short)Traits.Scale(d.Attack == 0 ? 1 : d.Attack, mod.AttackPct),
                    Hunger = (byte)(20 + rng.NextUInt(60)), Thirst = (byte)(20 + rng.NextUInt(60)),
                    Bravery = (byte)math.clamp(100 + mod.BraveryPct, 10, 250),
                });
                state.EntityManager.SetComponentData(e, new Brain { NextThinkTick = tick + id % LifeLimits.ThinkInterval });
                if (d.IsSapient)
                    state.EntityManager.SetComponentData(e, new CreatureName { Value = new FixedString32Bytes(NameGenerator.Person(c.Species, ref rng)) });
                life.Population++;
                if (d.IsSapient) life.Peoples++;
            }
            commands.Dispose();
            state.EntityManager.SetComponentData(queueEntity, life);
        }

        static bool FindStandable(WorldMap map, SpeciesDef d, int2 want, out int2 tile)
        {
            for (int r = 0; r <= 3; r++)
                for (int dy = -r; dy <= r; dy++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (math.max(math.abs(dx), math.abs(dy)) != r) continue;
                        int x = want.x + dx, y = want.y + dy;
                        if (!map.InBounds(x, y)) continue;
                        if (LifeRules.CanStand(d, map.Get(x, y))) { tile = new int2(x, y); return true; }
                    }
            tile = want;
            return false;
        }
    }

    /// <summary>
    /// Needs, utility-AI decisions (§5.2), movement and interactions for every creature, once per
    /// simulation tick (10 Hz). Single-threaded Burst with deterministic iteration and event
    /// application order, so the same world and seed produce the same life history.
    /// </summary>
    [BurstCompile]
    [UpdateInGroup(typeof(SimulationTickGroup))]
    [UpdateAfter(typeof(CreatureSpawnSystem))]
    public partial struct LifeSimSystem : ISystem
    {
        struct Snap
        {
            public Entity Entity;
            public int2 PosQ;
            public SpeciesId Species;
            public byte Sex;
            public byte Adult;
            public uint StableId;
            public ulong Traits;
        }

        struct Hit { public Entity Target; public short Damage; public Entity Attacker; }
        struct Birth { public Entity A, B; }

        public void OnCreate(ref SystemState state)
        {
            state.RequireForUpdate<WorldMap>();
            state.RequireForUpdate<LifeState>();
            state.RequireForUpdate<SimulationClock>();
        }

        [BurstCompile]
        public void OnUpdate(ref SystemState state)
        {
            WorldMap map = SystemAPI.GetSingleton<WorldMap>();
            if (!map.Tiles.IsCreated) return;
            uint tick = (uint)SystemAPI.GetSingleton<SimulationClock>().Tick;
            ulong noiseSeed = new WorldSeed(map.Seed).Derive(SeedStream.AiNoise);

            // ---- snapshot + spatial index (positions at the start of the tick) ----
            var snaps = new NativeList<Snap>(256, Allocator.Temp);
            var byEntity = new NativeHashMap<Entity, int>(256, Allocator.Temp);
            var cells = new NativeParallelMultiHashMap<int, int>(256, Allocator.Temp);
            foreach (var (c, m, e) in SystemAPI.Query<RefRO<Creature>, RefRO<Mover>>().WithEntityAccess())
            {
                SpeciesDef d = SpeciesTable.Get(c.ValueRO.Species);
                int idx = snaps.Length;
                snaps.Add(new Snap
                {
                    Entity = e, PosQ = m.ValueRO.PosQ, Species = c.ValueRO.Species, Sex = c.ValueRO.Sex, StableId = c.ValueRO.StableId,
                    Adult = (byte)(tick - c.ValueRO.BornTick >= (uint)d.AdultAtTicks ? 1 : 0),
                });
                byEntity.Add(e, idx);
                cells.Add(CellKey(LifeRules.TileOf(m.ValueRO.PosQ)), idx);
            }
            foreach (var (t, e) in SystemAPI.Query<RefRO<CreatureTraits>>().WithEntityAccess())
                if (byEntity.TryGetValue(e, out int i)) { Snap s = snaps[i]; s.Traits = t.ValueRO.Set.Bits; snaps[i] = s; }

            var hits = new NativeList<Hit>(16, Allocator.Temp);
            var births = new NativeList<Birth>(8, Allocator.Temp);
            var dead = new NativeList<Entity>(16, Allocator.Temp);

            // ---- needs, aging, brain, movement ----
            foreach (var (cRO, traitsRO, vit, brain, mover, e) in SystemAPI
                         .Query<RefRO<Creature>, RefRO<CreatureTraits>, RefRW<Vitals>, RefRW<Brain>, RefRW<Mover>>().WithEntityAccess())
            {
                Creature c = cRO.ValueRO;
                SpeciesDef d = SpeciesTable.Get(c.Species);
                TraitTotals mod = Traits.Combined(traitsRO.ValueRO.Set);
                ref Vitals v = ref vit.ValueRW;
                ref Brain b = ref brain.ValueRW;
                ref Mover m = ref mover.ValueRW;

                // Needs: rates per 10 ticks, staggered by id.
                if ((tick + c.StableId) % 10 == 0)
                {
                    v.Hunger = Add(v.Hunger, Traits.Scale(d.HungerRate, mod.HungerPct));
                    v.Thirst = Add(v.Thirst, (byte)((d.ThirstRate + 1) / 2));   // demo balance: thirst no longer wipes out inland herds
                    if (b.Action != CreatureAction.Sleep) v.Fatigue = Add(v.Fatigue, 2);
                    if (v.Hunger == 255 || v.Thirst == 255) v.Hp -= 2;
                    else if (v.Hp < v.MaxHp && v.Hunger < 150 && v.Thirst < 150) v.Hp++;
                }
                if (v.Hp <= 0 || tick - c.BornTick > c.LifespanTicks) { dead.Add(e); continue; }

                // Timed actions.
                if (b.Action == CreatureAction.Sleep && b.ActionTicks > 0)
                {
                    b.ActionTicks--;
                    v.Fatigue = Sub(v.Fatigue, 3);
                    continue;
                }
                if (b.Action == CreatureAction.Eat && b.ActionTicks > 0)
                {
                    b.ActionTicks--;
                    v.Hunger = Sub(v.Hunger, 6);
                    continue;
                }

                int2 tile = LifeRules.TileOf(m.PosQ);
                if (tick >= b.NextThinkTick)
                {
                    Think(ref b, ref m, ref v, c, d, mod, tile, map, snaps, cells, byEntity, noiseSeed, tick);
                    b.NextThinkTick = tick + LifeLimits.ThinkInterval;
                }

                // Chase: keep following a moving target.
                if ((b.Action == CreatureAction.Hunt || b.Action == CreatureAction.Mate) && byEntity.TryGetValue(b.Target, out int ti))
                {
                    m.TargetQ = snaps[ti].PosQ;
                    long dx = snaps[ti].PosQ.x - m.PosQ.x, dy = snaps[ti].PosQ.y - m.PosQ.y;
                    if (dx * dx + dy * dy <= (long)LifeRules.One * LifeRules.One)   // within one tile
                    {
                        if (b.Action == CreatureAction.Hunt) hits.Add(new Hit { Target = b.Target, Damage = v.Attack, Attacker = e });
                        else if (c.StableId < snaps[ti].StableId) births.Add(new Birth { A = e, B = b.Target });
                        b.Action = CreatureAction.Idle;
                        b.NextThinkTick = tick + 8;
                        continue;
                    }
                }

                Move(ref m, ref b, ref v, d, map, tick);
            }

            // ---- interactions (deterministic order: the order they were produced) ----
            var vitalsLookup = SystemAPI.GetComponentLookup<Vitals>(false);
            var creatureLookup = SystemAPI.GetComponentLookup<Creature>(false);
            var traitsLookup = SystemAPI.GetComponentLookup<CreatureTraits>(true);
            for (int i = 0; i < hits.Length; i++)
            {
                Hit h = hits[i];
                if (!vitalsLookup.HasComponent(h.Target) || !vitalsLookup.HasComponent(h.Attacker)) continue;
                Vitals tv = vitalsLookup[h.Target];
                if (tv.Hp <= 0) continue;
                tv.Hp -= h.Damage;
                vitalsLookup[h.Target] = tv;
                if (tv.Hp <= 0)
                {
                    dead.Add(h.Target);
                    Vitals av = vitalsLookup[h.Attacker];
                    av.Hunger = Sub(av.Hunger, 160);
                    vitalsLookup[h.Attacker] = av;
                }
            }

            Entity lifeEntity = SystemAPI.GetSingletonEntity<LifeState>();
            DynamicBuffer<SpawnCreatureCommand> spawnQueue = SystemAPI.GetBuffer<SpawnCreatureCommand>(lifeEntity);
            LifeState life = SystemAPI.GetComponent<LifeState>(lifeEntity);
            for (int i = 0; i < births.Length; i++)
            {
                Birth bth = births[i];
                if (!creatureLookup.HasComponent(bth.A) || !creatureLookup.HasComponent(bth.B)) continue;
                Creature a = creatureLookup[bth.A], bb = creatureLookup[bth.B];
                if (a.Species != bb.Species || a.Sex == bb.Sex) continue;
                if (tick - a.LastBirthTick < 400 || tick - bb.LastBirthTick < 400) continue;
                SpeciesDef d = SpeciesTable.Get(a.Species);
                TraitSet ta = traitsLookup[bth.A].Set, tb = traitsLookup[bth.B].Set;
                var rng = Pcg32.ForKey(noiseSeed ^ 0xB1B1B1B1UL, ((ulong)a.StableId << 32) | tick);
                int fertility = Traits.Scale(d.FertilityPct, (Traits.Combined(ta).FertilityPct + Traits.Combined(tb).FertilityPct) / 2);
                if (rng.NextUInt(100) >= (uint)fertility) continue;
                a.LastBirthTick = tick; bb.LastBirthTick = tick;
                creatureLookup[bth.A] = a; creatureLookup[bth.B] = bb;
                int litter = 1 + (int)rng.NextUInt((uint)math.max(1, (int)d.LitterMax));
                int2 at = LifeRules.TileOf(snaps[byEntity[bth.A]].PosQ);
                for (int k = 0; k < litter && life.Population + spawnQueue.Length < LifeLimits.MaxCreatures; k++)
                    spawnQueue.Add(new SpawnCreatureCommand { Species = a.Species, Tile = at, HasParents = 1, ParentA = ta, ParentB = tb });
                life.Births += (uint)litter;
            }

            // ---- deaths: dedupe, read what we need, then destroy in one structural change ----
            var unique = new NativeHashSet<Entity>(dead.Length + 1, Allocator.Temp);
            var toDestroy = new NativeList<Entity>(dead.Length, Allocator.Temp);
            for (int i = 0; i < dead.Length; i++)
            {
                Entity de = dead[i];
                if (!unique.Add(de) || !creatureLookup.HasComponent(de)) continue;
                if (SpeciesTable.Get(creatureLookup[de].Species).IsSapient) life.Peoples--;
                life.Population--; life.Deaths++;
                toDestroy.Add(de);
            }
            SystemAPI.SetComponent(lifeEntity, life);
            if (toDestroy.Length > 0) state.EntityManager.DestroyEntity(toDestroy.AsArray());
            unique.Dispose(); toDestroy.Dispose();

            snaps.Dispose(); byEntity.Dispose(); cells.Dispose(); hits.Dispose(); births.Dispose(); dead.Dispose();
        }

        static int CellKey(int2 tile) => ((tile.y >> LifeLimits.CellShift) << 16) | (tile.x >> LifeLimits.CellShift);

        static byte Add(byte v, int d) => (byte)math.min(255, v + d);
        static byte Sub(byte v, int d) => (byte)math.max(0, v - d);

        /// <summary>Utility scoring (§5.2): curves over needs, threat and opportunity, plus deterministic noise.</summary>
        static void Think(ref Brain b, ref Mover m, ref Vitals v, Creature c, SpeciesDef d, TraitTotals mod, int2 tile, WorldMap map,
            NativeList<Snap> snaps, NativeParallelMultiHashMap<int, int> cells, NativeHashMap<Entity, int> byEntity, ulong noiseSeed, uint tick)
        {
            var rng = Pcg32.ForKey(noiseSeed, ((ulong)c.StableId << 32) | tick);
            int sight = d.SightTiles;

            // Nearest threat / prey / mate in sight.
            int threat = -1, prey = -1, mate = -1;
            long threatD = long.MaxValue, preyD = long.MaxValue, mateD = long.MaxValue;
            bool adult = tick - c.BornTick >= (uint)d.AdultAtTicks;
            int2 cell0 = tile >> LifeLimits.CellShift;
            int cr = (sight >> LifeLimits.CellShift) + 1;
            for (int cy = cell0.y - cr; cy <= cell0.y + cr; cy++)
                for (int cx = cell0.x - cr; cx <= cell0.x + cr; cx++)
                {
                    if (cx < 0 || cy < 0) continue;
                    int key = (cy << 16) | cx;
                    if (!cells.TryGetFirstValue(key, out int idx, out var it)) continue;
                    do
                    {
                        Snap o = snaps[idx];
                        if (o.StableId == c.StableId) continue;
                        long dx = (o.PosQ.x - m.PosQ.x) >> 8, dy = (o.PosQ.y - m.PosQ.y) >> 8; // Q8 to avoid overflow
                        long dist2 = dx * dx + dy * dy;
                        if (dist2 > (long)sight * sight * 65536) continue;
                        if (LifeRules.IsThreat(d, o.Species) && dist2 < threatD) { threatD = dist2; threat = idx; }
                        if (LifeRules.IsPrey(c.Species, o.Species) && dist2 < preyD) { preyD = dist2; prey = idx; }
                        if (adult && o.Species == c.Species && o.Sex != c.Sex && o.Adult != 0 && dist2 < mateD) { mateD = dist2; mate = idx; }
                    } while (cells.TryGetNextValue(out idx, ref it));
                }

            int hungerScore = v.Hunger * v.Hunger / 65;       // quadratic, 0..1000
            int thirstScore = v.Thirst * v.Thirst / 65;
            int fatigueScore = v.Fatigue > 170 ? (v.Fatigue - 120) * 7 : v.Fatigue / 3;
            int fleeScore = 0;
            if (threat >= 0)
            {
                long dist = LifeRules.ISqrt(threatD) >> 8;      // tiles
                fleeScore = (int)((sight - dist) * 1000 / math.max(1, sight)) * 100 / math.max(10, (int)v.Bravery);
            }
            int mateScore = (mate >= 0 && v.Hunger < 140 && v.Thirst < 140 && tick - c.LastBirthTick > 400) ? 420 : 0;
            int wanderScore = 140;
            if (d.Kind == CreatureKind.Fish) thirstScore = 0;
            // Small deterministic noise per option so identical creatures don't move in lockstep (§5.2).
            int eat = hungerScore + (int)rng.NextUInt(60);
            int drink = thirstScore + (int)rng.NextUInt(60);
            int sleep = fatigueScore + (int)rng.NextUInt(60);
            int flee = fleeScore + (int)rng.NextUInt(60);
            int mating = mateScore + (int)rng.NextUInt(60);
            int wander = wanderScore + (int)rng.NextUInt(60);
            int best = math.max(math.max(math.max(eat, drink), math.max(sleep, flee)), math.max(mating, wander));

            if (best == flee && threat >= 0)
            {
                int2 away = m.PosQ - snaps[threat].PosQ;
                int2 dir = math.sign(away);
                int2 goal = math.clamp(tile + dir * 6, 0, new int2(map.Width - 1, map.Height - 1));
                b.Action = CreatureAction.Flee; m.TargetQ = LifeRules.CenterQ(goal); m.Moving = 1;
                return;
            }
            if (best == sleep)
            {
                b.Action = CreatureAction.Sleep; b.ActionTicks = 60; m.Moving = 0;
                return;
            }
            if (best == eat)
            {
                bool hunts = d.IsPredator || (d.IsSapient && (v.Hunger > 180 || mod.AggressionPct > 0));
                if (hunts && prey >= 0)
                {
                    b.Action = CreatureAction.Hunt; b.Target = snaps[prey].Entity; m.Moving = 1;
                    return;
                }
                if (d.EatsPlants || d.Kind == CreatureKind.Fish)
                {
                    TileData here = map.Get(tile.x, tile.y);
                    if (d.Kind == CreatureKind.Fish ? here.IsWater : LifeRules.Edible(here))
                    {
                        b.Action = CreatureAction.Eat; b.ActionTicks = 20; m.Moving = 0;
                        return;
                    }
                    if (FindTile(map, d, tile, 6, ref rng, wantWater: false, out int2 food))
                    {
                        b.Action = CreatureAction.Eat; b.ActionTicks = 0; m.TargetQ = LifeRules.CenterQ(food); m.Moving = 1;
                        return;
                    }
                }
            }
            if (best == drink && d.Kind != CreatureKind.Fish)
            {
                if (FindTile(map, d, tile, sight, ref rng, wantWater: true, out int2 water))
                {
                    b.Action = CreatureAction.Drink; m.TargetQ = LifeRules.CenterQ(water); m.Moving = 1;
                    return;
                }
            }
            if (best == mating && mate >= 0)
            {
                b.Action = CreatureAction.Mate; b.Target = snaps[mate].Entity; m.Moving = 1;
                return;
            }
            // Wander.
            int2 to = tile + new int2((int)rng.NextUInt(13) - 6, (int)rng.NextUInt(13) - 6);
            to = math.clamp(to, 0, new int2(map.Width - 1, map.Height - 1));
            b.Action = CreatureAction.Wander; m.TargetQ = LifeRules.CenterQ(to); m.Moving = 1;
        }

        /// <summary>Food (edible, standable) or water tile within <paramref name="radius"/>, scanning rings from a random start.</summary>
        static bool FindTile(WorldMap map, SpeciesDef d, int2 from, int radius, ref Pcg32 rng, bool wantWater, out int2 found)
        {
            int start = (int)rng.NextUInt(8);
            for (int r = 1; r <= radius; r++)
                for (int k = 0; k < 8 * r; k++)
                {
                    int s = (k + start * r) % (8 * r);
                    int2 p = RingPoint(from, r, s);
                    if (!map.InBounds(p.x, p.y)) continue;
                    TileData t = map.Get(p.x, p.y);
                    bool ok = wantWater ? t.IsWater : (LifeRules.CanStand(d, t) && (d.Kind == CreatureKind.Fish ? t.IsWater : LifeRules.Edible(t)));
                    if (ok) { found = p; return true; }
                }
            found = from;
            return false;
        }

        static int2 RingPoint(int2 c, int r, int s)
        {
            int side = s / (2 * r), off = s % (2 * r);
            switch (side)
            {
                case 0: return new int2(c.x - r + off, c.y - r);
                case 1: return new int2(c.x + r, c.y - r + off);
                case 2: return new int2(c.x + r - off, c.y + r);
                default: return new int2(c.x - r, c.y + r - off);
            }
        }

        /// <summary>Steps toward the target; impassable tiles end the move (and complete a drink).</summary>
        static void Move(ref Mover m, ref Brain b, ref Vitals v, SpeciesDef d, WorldMap map, uint tick)
        {
            if (m.Moving == 0) return;
            long dx = m.TargetQ.x - m.PosQ.x, dy = m.TargetQ.y - m.PosQ.y;
            long dist = LifeRules.ISqrt(dx * dx + dy * dy);
            if (dist <= m.SpeedQ)
            {
                m.Moving = 0;
                if (b.Action == CreatureAction.Eat) b.ActionTicks = 20; // arrived at food
                else { b.Action = CreatureAction.Idle; b.NextThinkTick = tick + 2; }
                return;
            }
            int2 next = new int2((int)(m.PosQ.x + dx * m.SpeedQ / dist), (int)(m.PosQ.y + dy * m.SpeedQ / dist));
            int2 nt = LifeRules.TileOf(next);
            if (!map.InBounds(nt.x, nt.y)) { m.Moving = 0; b.NextThinkTick = tick; return; }
            TileData t = map.Get(nt.x, nt.y);
            if (!LifeRules.CanStand(d, t))
            {
                m.Moving = 0;
                if (b.Action == CreatureAction.Drink && t.IsWater) v.Thirst = 0;
                b.Action = CreatureAction.Idle;
                b.NextThinkTick = tick + 3;
                return;
            }
            m.FacingLeft = (byte)(dx < 0 ? 1 : 0);
            m.PosQ = next;
        }
    }
}
