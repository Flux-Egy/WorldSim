using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;
using WorldSim.Core.Life;
using WorldSim.Core.Powers;

namespace WorldSim.Simulation.Life
{
    /// <summary>A power used by the player at a tile (lightning, meteor, bomb, plague, bless...).</summary>
    public struct PowerStrikeCommand : IBufferElementData
    {
        public PowerKind Kind;
        public int2 Tile;
    }

    /// <summary>Tag of the singleton holding the power queue.</summary>
    public struct PowerQueue : IComponentData { }

    /// <summary>
    /// Applies powers to living creatures (Playable Alpha): damage by blast zone (<see cref="PowerRules"/>: fireball and
    /// blast kill, thermal burns, shock hurts), the rest run away from the strike; bless heals. The land changes are
    /// queued separately as terrain edits. Deaths are handled by the life simulation (health at zero).
    /// </summary>
    [UpdateInGroup(typeof(SimulationTickGroup))]
    [UpdateAfter(typeof(CreatureSpawnSystem))]
    [UpdateBefore(typeof(LifeSimSystem))]
    public partial struct PowerSystem : ISystem
    {
        public void OnCreate(ref SystemState state)
        {
            Entity e = state.EntityManager.CreateEntity(typeof(PowerQueue));
            state.EntityManager.AddBuffer<PowerStrikeCommand>(e);
            state.RequireForUpdate<SimulationClock>();
        }

        public void OnUpdate(ref SystemState state)
        {
            Entity qe = SystemAPI.GetSingletonEntity<PowerQueue>();
            DynamicBuffer<PowerStrikeCommand> queue = state.EntityManager.GetBuffer<PowerStrikeCommand>(qe);
            if (queue.Length == 0) return;
            var strikes = queue.ToNativeArray(Allocator.Temp);
            queue.Clear();
            uint tick = (uint)SystemAPI.GetSingleton<SimulationClock>().Tick;

            foreach (var (vit, brain, mover) in SystemAPI.Query<RefRW<Vitals>, RefRW<Brain>, RefRW<Mover>>())
            {
                for (int s = 0; s < strikes.Length; s++)
                {
                    PowerStrikeCommand st = strikes[s];
                    long cx = ((long)st.Tile.x << 16) + (1 << 15), cy = ((long)st.Tile.y << 16) + (1 << 15);
                    long dx = mover.ValueRO.PosQ.x - cx, dy = mover.ValueRO.PosQ.y - cy;
                    int dist = PowerRules.DistTenths(dx, dy);
                    if (st.Kind == PowerKind.Bless)
                    {
                        if (dist <= PowerRules.SupportRadius(PowerKind.Bless) * 10)
                        {
                            Vitals v = vit.ValueRO;
                            v.Hp = v.MaxHp; v.Hunger = 0; v.Thirst = 0; v.Fatigue = 0;
                            vit.ValueRW = v;
                        }
                        continue;
                    }
                    int zone = PowerRules.ZoneOf(st.Kind, dist);
                    if (zone < 0) continue;
                    Vitals hurt = vit.ValueRO;
                    int dmg = hurt.MaxHp * PowerRules.DamagePercent(st.Kind, zone) / 100;
                    hurt.Hp = (short)math.max(0, hurt.Hp - math.max(1, dmg));
                    vit.ValueRW = hurt;
                    if (hurt.Hp > 0 && PowerRules.Flees(zone))
                    {
                        // Run straight away from the strike for a while.
                        long len = math.max(1L, (long)math.sqrt((double)(dx * dx + dy * dy)));
                        long run = 7L << 16;
                        Mover m = mover.ValueRO;
                        m.TargetQ = new int2((int)(m.PosQ.x + dx * run / len), (int)(m.PosQ.y + dy * run / len));
                        m.Moving = 1;
                        mover.ValueRW = m;
                        Brain b = brain.ValueRO;
                        b.Action = CreatureAction.Flee;
                        b.NextThinkTick = tick + 30;
                        brain.ValueRW = b;
                    }
                }
            }
            strikes.Dispose();
        }
    }
}
