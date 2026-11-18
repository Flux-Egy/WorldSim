using Unity.Collections;
using Unity.Entities;
using WorldSim.Core;

namespace WorldSim.Simulation
{
    /// <summary>Queued brush dab (Beta B2). Presentation appends; <see cref="TerrainEditSystem"/> drains.</summary>
    public struct TerrainEditCommand : IBufferElementData
    {
        public TerrainEdit Edit;
    }

    /// <summary>Tag of the singleton entity that holds the <see cref="TerrainEditCommand"/> buffer.</summary>
    public struct TerrainEditQueue : IComponentData { }

    /// <summary>
    /// Applies queued terrain edits to the <see cref="WorldMap"/> with the deterministic
    /// <see cref="WorldEditor"/>, then publishes the changed rectangle (EditVersion, DirtyRect).
    /// Runs in Initialization right after generation, i.e. before MonoBehaviour Update, so edits
    /// queued in one frame are visible to presentation in the next.
    /// </summary>
    [UpdateInGroup(typeof(InitializationSystemGroup))]
    [UpdateAfter(typeof(WorldMapSystem))]
    public partial struct TerrainEditSystem : ISystem
    {
        struct NativeGrid : ITileGrid
        {
            public NativeArray<TileData> A;
            public TileData Get(int i) => A[i];
            public void Set(int i, TileData t) => A[i] = t;
        }

        public void OnCreate(ref SystemState state)
        {
            Entity e = state.EntityManager.CreateEntity(typeof(TerrainEditQueue));
            state.EntityManager.AddBuffer<TerrainEditCommand>(e);
            state.RequireForUpdate<WorldMap>();
        }

        public void OnUpdate(ref SystemState state)
        {
            DynamicBuffer<TerrainEditCommand> queue = SystemAPI.GetSingletonBuffer<TerrainEditCommand>();
            if (queue.Length == 0) return;

            ref WorldMap map = ref SystemAPI.GetSingletonRW<WorldMap>().ValueRW;
            if (!map.Tiles.IsCreated) { queue.Clear(); return; }

            var p = WorldGenParams.Create(new WorldSeed(map.Seed), map.Width, map.Height, map.Settings);
            var grid = new NativeGrid { A = map.Tiles };
            TileRect dirty = TileRect.Empty;
            for (int i = 0; i < queue.Length; i++)
            {
                TileRect r = WorldEditor.Apply(ref grid, p, queue[i].Edit);
                if (!r.IsEmpty) dirty.Include(r.XMin, r.YMin, r.XMax, r.YMax);
            }
            queue.Clear();

            if (!dirty.IsEmpty)
            {
                map.DirtyRect = dirty;
                map.EditVersion++;
            }
        }
    }
}
