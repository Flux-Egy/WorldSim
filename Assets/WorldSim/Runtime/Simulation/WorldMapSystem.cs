using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Jobs;
using WorldSim.Core;

namespace WorldSim.Simulation
{
    /// <summary>
    /// Ask for a (new) world. Create an entity with this component; <see cref="WorldMapSystem"/>
    /// consumes it on its next update.
    /// </summary>
    public struct WorldGenRequest : IComponentData
    {
        public ulong Seed;
        public int Width;
        public int Height;
        public WorldGenSettings Settings;   // zero value is fixed up to Default below
    }

    /// <summary>
    /// The terrain grid (§4.1), as a singleton owned by <see cref="WorldMapSystem"/>. The tile
    /// array is only valid until the next generation: readers must compare
    /// <see cref="Version"/> and never keep the NativeArray across frames.
    /// </summary>
    public struct WorldMap : IComponentData
    {
        public NativeArray<TileData> Tiles;
        public int Width;
        public int Height;
        public ulong Seed;
        public WorldGenSettings Settings;
        /// <summary>FNV-1a world hash (§4.3), identical on every platform for the same seed.</summary>
        public ulong Hash;
        /// <summary>Incremented on every (re)generation; 0 means no world yet.</summary>
        public uint Version;
        /// <summary>Incremented whenever terrain edits change tiles (Beta B2).</summary>
        public uint EditVersion;
        /// <summary>Tiles changed by the edits of the latest <see cref="EditVersion"/>.</summary>
        public TileRect DirtyRect;

        public bool IsCreated => Tiles.IsCreated;

        public bool InBounds(int x, int y) => x >= 0 && y >= 0 && x < Width && y < Height;

        public TileData Get(int x, int y) => Tiles[y * Width + x];
    }

    /// <summary>
    /// Generates the world with Burst jobs from <see cref="WorldGenerator"/> (integer-only, so the
    /// result and its hash match the reference generator and the golden hashes in the tests).
    /// Runs in Initialization, outside the fixed simulation tick: generation is a one-shot load.
    /// </summary>
    [UpdateInGroup(typeof(InitializationSystemGroup))]
    public partial struct WorldMapSystem : ISystem
    {
        EntityQuery _requests;

        public void OnCreate(ref SystemState state)
        {
            state.EntityManager.CreateSingleton(new WorldMap());
            _requests = state.GetEntityQuery(ComponentType.ReadOnly<WorldGenRequest>());
            state.RequireForUpdate(_requests);
        }

        public void OnDestroy(ref SystemState state)
        {
            if (SystemAPI.TryGetSingleton(out WorldMap map) && map.Tiles.IsCreated)
                map.Tiles.Dispose();
        }

        public void OnUpdate(ref SystemState state)
        {
            // Last request wins if several were made in one frame.
            var requests = _requests.ToComponentDataArray<WorldGenRequest>(Allocator.Temp);
            WorldGenRequest req = requests[requests.Length - 1];
            requests.Dispose();
            state.EntityManager.DestroyEntity(_requests);

            if (req.Width < 16 || req.Height < 16 || req.Width > 4096 || req.Height > 4096)
            {
                UnityEngine.Debug.LogError($"[WorldSim] Rejected world size {req.Width}x{req.Height}.");
                return;
            }

            ref WorldMap map = ref SystemAPI.GetSingletonRW<WorldMap>().ValueRW;
            if (map.Tiles.IsCreated) map.Tiles.Dispose();

            WorldGenSettings settings = req.Settings;
            if (settings.Mountains == 0 && settings.LandBias == 0 && settings.Temperature == 0 && settings.Moisture == 0 && settings.Blank == 0)
                settings = WorldGenSettings.Default; // an all-zero request means "defaults"
            var p = WorldGenParams.Create(new WorldSeed(req.Seed), req.Width, req.Height, settings);
            var tiles = new NativeArray<TileData>(req.Width * req.Height, Allocator.Persistent,
                NativeArrayOptions.UninitializedMemory);
            var hash = new NativeReference<ulong>(Allocator.TempJob);

            JobHandle gen = new GenerateTilesJob { Params = p, Tiles = tiles }
                .Schedule(tiles.Length, 256, state.Dependency);
            JobHandle hashed = new HashTilesJob
            {
                Seed = req.Seed, Width = req.Width, Height = req.Height, Settings = settings, Tiles = tiles, Result = hash,
            }.Schedule(gen);
            hashed.Complete(); // one-shot load: the world must exist before anything reads it

            map.Tiles = tiles;
            map.Width = req.Width;
            map.Height = req.Height;
            map.Seed = req.Seed;
            map.Settings = settings;
            map.Hash = hash.Value;
            map.Version++;
            hash.Dispose();

            UnityEngine.Debug.Log($"[WorldSim] World generated: seed=0x{req.Seed:X16} size={req.Width}x{req.Height} " +
                                  $"hash=0x{map.Hash:X16} version={map.Version}");
        }

        [BurstCompile]
        struct GenerateTilesJob : IJobParallelFor
        {
            public WorldGenParams Params;
            [WriteOnly] public NativeArray<TileData> Tiles;

            public void Execute(int i)
            {
                Tiles[i] = WorldGenerator.GenerateTile(Params, i % Params.Width, i / Params.Width);
            }
        }

        [BurstCompile]
        struct HashTilesJob : IJob
        {
            public ulong Seed;
            public int Width;
            public int Height;
            public WorldGenSettings Settings;
            [ReadOnly] public NativeArray<TileData> Tiles;
            public NativeReference<ulong> Result;

            public void Execute()
            {
                StableHash64 h = WorldHash.Begin(Seed, Width, Height, Settings);
                for (int i = 0; i < Tiles.Length; i++) WorldHash.AddTile(ref h, Tiles[i]);
                Result.Value = h.Value;
            }
        }
    }
}
