using Unity.Burst;
using Unity.Entities;

namespace GodSim.Simulation
{
    /// <summary>
    /// All simulation-critical systems update inside this group, at a fixed tick rate that is
    /// independent of render frame rate (§7.2, §18.3). Presentation interpolates between ticks.
    /// </summary>
    [UpdateInGroup(typeof(SimulationSystemGroup))]
    public partial class SimulationTickGroup : ComponentSystemGroup
    {
        public const float DefaultTickSeconds = 0.1f; // 10 Hz ("Normal" simulation rate)

        protected override void OnCreate()
        {
            base.OnCreate();
            RateManager = new RateUtils.FixedRateCatchUpManager(DefaultTickSeconds);
        }

        /// <summary>Changes the tick interval (Settings > Simulation Rate, thermal fallback).</summary>
        public void SetTickSeconds(float seconds)
        {
            RateManager.Timestep = seconds;
        }
    }

    /// <summary>Monotonic simulation tick counter. The only notion of "time" simulation code may use.</summary>
    public struct SimulationClock : IComponentData
    {
        public ulong Tick;
    }

    [UpdateInGroup(typeof(SimulationTickGroup), OrderFirst = true)]
    [BurstCompile]
    public partial struct SimulationClockSystem : ISystem
    {
        public void OnCreate(ref SystemState state)
        {
            state.EntityManager.CreateSingleton(new SimulationClock());
        }

        [BurstCompile]
        public void OnUpdate(ref SystemState state)
        {
            SystemAPI.GetSingletonRW<SimulationClock>().ValueRW.Tick++;
        }
    }
}
