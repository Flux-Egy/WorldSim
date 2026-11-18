using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using UnityEngine;
using WorldSim.Core;
using WorldSim.Render;

namespace WorldSim.Presentation.Terrain
{
    /// <summary>
    /// Paints the world texture with Burst jobs that call the pure <see cref="TerrainPainter"/>
    /// (WorldSim.Render). That is the same code Tools/WorldPreview runs in plain .NET, so the
    /// preview images match the game. The ground is a parallel job (one tile row per index); the
    /// decorations are a single job that runs afterwards, back to front.
    /// </summary>
    public static class TerrainTexture
    {
        static NativeArray<uint> s_atlas; // procedural sprite atlas, built once

        public static int PixelsPerTileFor(int widthTiles, int heightTiles) =>
            TerrainPainter.PixelsPerTileFor(widthTiles, heightTiles);

        public static Texture2D Create(int widthTiles, int heightTiles)
        {
            int ppt = PixelsPerTileFor(widthTiles, heightTiles);
            return new Texture2D(widthTiles * ppt, heightTiles * ppt, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
                name = "WorldTerrain",
            };
        }

        /// <summary>Fills <paramref name="tex"/> from <paramref name="tiles"/> and uploads it.</summary>
        public static void Paint(Texture2D tex, NativeArray<TileData> tiles, int width, int height)
        {
            if (!s_atlas.IsCreated)
                s_atlas = new NativeArray<uint>(SpriteLibrary.Build(), Allocator.Persistent);

            int ppt = PixelsPerTileFor(width, height);
            NativeArray<uint> pixels = tex.GetPixelData<uint>(0);
            var src = new NativeTiles { A = tiles };
            var dst = new NativePixels { A = pixels };

            JobHandle ground = new GroundJob { Tiles = src, Pixels = dst, W = width, H = height, Ppt = ppt }
                .Schedule(height, 2);
            new DecorationJob { Tiles = src, Pixels = dst, Atlas = new NativeAtlas { A = s_atlas }, W = width, H = height, Ppt = ppt }
                .Schedule(ground).Complete();
            tex.Apply(false, false); // stays readable: terrain painting (B2) repaints regions
        }

        /// <summary>
        /// Repaints only what changed after terrain edits to tile rows [yMin, yMax] (Beta B2), with
        /// the same pure code a full paint uses (RenderTests proves partial == full). Uploads once.
        /// </summary>
        public static void RepaintRows(Texture2D tex, NativeArray<TileData> tiles, int width, int height, int yMin, int yMax)
        {
            if (!s_atlas.IsCreated)
                s_atlas = new NativeArray<uint>(SpriteLibrary.Build(), Allocator.Persistent);
            new RepaintJob
            {
                Tiles = new NativeTiles { A = tiles }, Pixels = new NativePixels { A = tex.GetPixelData<uint>(0) },
                Atlas = new NativeAtlas { A = s_atlas }, W = width, H = height, Ppt = PixelsPerTileFor(width, height),
                YMin = yMin, YMax = yMax,
            }.Schedule().Complete();
            tex.Apply(false, false);
        }

        /// <summary>Repaints overview rows [yMin-1, yMax+1] (the coastal band reads neighbours).</summary>
        public static void RepaintOverviewRows(Texture2D tex, NativeArray<TileData> tiles, int width, int height, int opp, int yMin, int yMax)
        {
            int r0 = yMin - 1 < 0 ? 0 : yMin - 1, r1 = yMax + 1 > height - 1 ? height - 1 : yMax + 1;
            var job = new OverviewJob { Tiles = new NativeTiles { A = tiles }, Pixels = new NativePixels { A = tex.GetPixelData<uint>(0) }, W = width, H = height, Opp = opp, RowOffset = r0 };
            job.Schedule(r1 - r0 + 1, 8).Complete();
            tex.Apply(false, false);
        }

        /// <summary>Paints the clean far-zoom texture (<paramref name="opp"/> pixels per tile).</summary>
        public static void PaintOverview(Texture2D tex, NativeArray<TileData> tiles, int width, int height, int opp)
        {
            var job = new OverviewJob { Tiles = new NativeTiles { A = tiles }, Pixels = new NativePixels { A = tex.GetPixelData<uint>(0) }, W = width, H = height, Opp = opp };
            job.Schedule(height, 8).Complete();
            tex.Apply(false, false);
        }

        /// <summary>
        /// One texel per tile: opaque for open water (water with no land among its 8 neighbours),
        /// transparent elsewhere. Used as the SpriteMask for the wave layers.
        /// </summary>
        public static void PaintOpenWaterMask(Texture2D tex, NativeArray<TileData> tiles, int width, int height)
            => PaintOpenWaterMask(tex, tiles, width, height, 0, 0, width - 1, height - 1);

        /// <summary>Region variant (inclusive tile bounds, grown by one for the neighbour test).</summary>
        public static void PaintOpenWaterMask(Texture2D tex, NativeArray<TileData> tiles, int width, int height, int x0, int y0, int x1, int y1)
        {
            NativeArray<uint> px = tex.GetPixelData<uint>(0);
            uint on = Rgba.Pack(255, 255, 255, 255);
            x0 = x0 - 1 < 0 ? 0 : x0 - 1; y0 = y0 - 1 < 0 ? 0 : y0 - 1;
            x1 = x1 + 1 > width - 1 ? width - 1 : x1 + 1; y1 = y1 + 1 > height - 1 ? height - 1 : y1 + 1;
            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    bool open = tiles[y * width + x].IsWater;
                    for (int dy = -1; dy <= 1 && open; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
                            if (!tiles[ny * width + nx].IsWater) { open = false; break; }
                        }
                    px[y * width + x] = open ? on : 0u;
                }
            tex.Apply(false, false);
        }

        /// <summary>Releases the sprite atlas (call when the world view is destroyed).</summary>
        public static void DisposeAtlas()
        {
            if (s_atlas.IsCreated) s_atlas.Dispose();
        }

        struct NativeTiles : ITileSource
        {
            [ReadOnly] public NativeArray<TileData> A;
            public TileData Get(int i) => A[i];
        }

        struct NativePixels : IPixelTarget
        {
            [NativeDisableParallelForRestriction] public NativeArray<uint> A;
            public uint Get(int i) => A[i];
            public void Set(int i, uint c) => A[i] = c;
        }

        struct NativeAtlas : IAtlasSource
        {
            [ReadOnly] public NativeArray<uint> A;
            public uint Get(int i) => A[i];
        }

        [BurstCompile]
        struct GroundJob : IJobParallelFor
        {
            public NativeTiles Tiles;
            public NativePixels Pixels;
            public int W, H, Ppt;

            public void Execute(int tileRow) => TerrainPainter.PaintGroundRow(ref Tiles, ref Pixels, W, H, Ppt, tileRow);
        }

        [BurstCompile]
        struct OverviewJob : IJobParallelFor
        {
            public NativeTiles Tiles;
            public NativePixels Pixels;
            public int W, H, Opp, RowOffset;

            public void Execute(int i) => TerrainPainter.PaintOverviewRow(ref Tiles, ref Pixels, W, H, Opp, RowOffset + i);
        }

        [BurstCompile]
        struct RepaintJob : IJob
        {
            public NativeTiles Tiles;
            public NativePixels Pixels;
            public NativeAtlas Atlas;
            public int W, H, Ppt, YMin, YMax;

            public void Execute() => TerrainPainter.RepaintRows(ref Tiles, ref Pixels, ref Atlas, W, H, Ppt, YMin, YMax);
        }

        [BurstCompile]
        struct DecorationJob : IJob
        {
            public NativeTiles Tiles;
            public NativePixels Pixels;
            public NativeAtlas Atlas;
            public int W, H, Ppt;

            public void Execute() => TerrainPainter.PaintDecorations(ref Tiles, ref Pixels, ref Atlas, W, H, Ppt);
        }
    }
}
