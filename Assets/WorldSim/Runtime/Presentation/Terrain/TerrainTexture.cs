using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using UnityEngine;
using WorldSim.Core;

namespace WorldSim.Presentation.Terrain
{
    /// <summary>
    /// Turns the tile grid into a pixel-art texture: <see cref="PixelsPerTileFor"/>² texels per tile,
    /// filled by a Burst job (§3.3: no per-pixel managed work). Presentation only: colours never
    /// feed back into the simulation.
    ///
    /// Stage 2 deviation from §7.3 (blend shader + texture atlas): there is no art yet, so detail
    /// is procedural (per-pixel hash shading, trees, rocks, ore, coastal foam, relief light).
    /// A custom terrain/water shader replaces this in the rendering stage.
    /// </summary>
    public static class TerrainTexture
    {
        /// <summary>
        /// 4 px per tile up to 512 tiles, then 2 px: a 1024-tile map is a 2048² texture (16 MB)
        /// instead of 4096² (64 MB). Larger maps use chunked rendering (plan A5).
        /// </summary>
        public static int PixelsPerTileFor(int widthTiles, int heightTiles) =>
            (widthTiles > heightTiles ? widthTiles : heightTiles) <= 512 ? 4 : 2;

        public static Texture2D Create(int widthTiles, int heightTiles)
        {
            int ppt = PixelsPerTileFor(widthTiles, heightTiles);
            var tex = new Texture2D(widthTiles * ppt, heightTiles * ppt, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
                name = "WorldTerrain",
            };
            return tex;
        }

        /// <summary>Fills <paramref name="tex"/> from <paramref name="tiles"/> and uploads it.</summary>
        public static void Paint(Texture2D tex, NativeArray<TileData> tiles, int width, int height)
        {
            NativeArray<Color32> pixels = tex.GetPixelData<Color32>(0);
            new PaintJob { Tiles = tiles, Width = width, Height = height, Ppt = PixelsPerTileFor(width, height), Pixels = pixels }
                .Schedule(height, 4).Complete();
            tex.Apply(false, false); // stays readable: terrain painting (Stage 6) repaints regions
        }

        [BurstCompile]
        struct PaintJob : IJobParallelFor
        {
            [ReadOnly] public NativeArray<TileData> Tiles;
            public int Width;
            public int Height;
            public int Ppt; // pixels per tile: 4 or 2
            [NativeDisableParallelForRestriction, WriteOnly] public NativeArray<Color32> Pixels;

            public void Execute(int ty)   // one row of tiles = Ppt rows of pixels
            {
                int texWidth = Width * Ppt;
                for (int tx = 0; tx < Width; tx++)
                {
                    TileData t = Tiles[ty * Width + tx];
                    int relief = Relief(tx, ty, t.Height);
                    bool coast = t.IsWater && TouchesLand(tx, ty);
                    for (int py = 0; py < Ppt; py++)
                        for (int px = 0; px < Ppt; px++)
                        {
                            // Patterns are designed on a 4x4 grid; at 2 px per tile sample every other cell.
                            int sx = px * 4 / Ppt, sy = py * 4 / Ppt;
                            Color32 c = Shade(t, tx, ty, sx, sy, relief, coast);
                            Pixels[(ty * Ppt + py) * texWidth + tx * Ppt + px] = c;
                        }
                }
            }

            int HeightAt(int x, int y, int fallback)
            {
                if (x < 0 || y < 0 || x >= Width || y >= Height) return fallback;
                return Tiles[y * Width + x].Height;
            }

            // Light from the top-left: compare with the up-left neighbour.
            int Relief(int x, int y, int h)
            {
                int d = h - HeightAt(x - 1, y + 1, h);
                if (d > 6) d = 6;
                if (d < -6) d = -6;
                return d * 3;
            }

            bool TouchesLand(int x, int y)
            {
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int nx = x + dx, ny = y + dy;
                        if (nx < 0 || ny < 0 || nx >= Width || ny >= Height) continue;
                        if (!Tiles[ny * Width + nx].IsWater) return true;
                    }
                return false;
            }

            static Color32 Shade(TileData t, int tx, int ty, int px, int py, int relief, bool coast)
            {
                // Per-pixel noise from a hash of (tile, pixel): stable, no RNG state.
                uint h = (uint)(SplitMix64.Mix(((ulong)(uint)tx << 32 | (uint)ty) * 16UL + (ulong)(py * 4 + px)) >> 40);
                int n = (int)(h & 15) - 8;     // -8..7
                bool speck = (h & 0x300) == 0; // ~25% of pixels

                int r, g, b;
                switch ((Biome)t.BiomeId)
                {
                    case Biome.DeepWater:
                        r = 30; g = 66; b = 128; n /= 3;
                        b += (t.Height - 60) / 3;
                        break;
                    case Biome.ShallowWater:
                        r = 56; g = 118; b = 184; n /= 3;
                        g += (t.Height - 100) / 2;
                        if (coast && speck) { r = 168; g = 208; b = 232; }   // foam
                        break;
                    case Biome.Sand:
                        r = 222; g = 204; b = 142;
                        if (speck) { r -= 18; g -= 18; b -= 14; }
                        break;
                    case Biome.Grass:
                        r = 104; g = 170; b = 72;
                        if (speck) { r -= 14; g -= 10; b -= 8; }
                        break;
                    case Biome.Forest:
                        r = 46; g = 116; b = 54;
                        if ((px + py + (int)(h >> 4 & 1)) % 2 == 0) { r += 14; g += 22; b += 10; } // canopy texture
                        break;
                    case Biome.Mountain:
                        r = 128; g = 120; b = 112;
                        if (px + py <= 1) { r += 22; g += 22; b += 22; }       // lit ridge
                        else if (px + py >= 5) { r -= 18; g -= 18; b -= 18; } // shadow side
                        break;
                    case Biome.Snow:
                        r = 234; g = 240; b = 248;
                        if (speck) { r -= 14; g -= 10; b -= 4; }
                        break;
                    default: // unknown / mod biome without a colour yet: obvious, not magenta
                        r = 200; g = 60; b = 160;
                        break;
                }

                // Resource and decoration pixels (Stage 2 placeholders until sprites exist).
                if (t.Has(ResourceFlags.Gold) && px == 1 && py == 2) { r = 240; g = 200; b = 40; n = 0; relief = 0; }
                else if (t.Has(ResourceFlags.Gems) && px == 2 && py == 1) { r = 190; g = 70; b = 220; n = 0; relief = 0; }
                else if (t.Has(ResourceFlags.Wood) && t.BiomeId == (byte)Biome.Grass)
                {
                    if (py >= 2 && px >= 1 && px <= 2) { r = 40; g = 110; b = 44; }        // canopy
                    else if (py == 1 && px == 1) { r = 96; g = 66; b = 40; }             // trunk
                }
                else if (t.Has(ResourceFlags.Stone) && t.BiomeId != (byte)Biome.Mountain && px == 2 && py == 1)
                {
                    r = 140; g = 136; b = 128;                                            // rock
                }

                r += n + relief; g += n + relief; b += n + relief;
                return new Color32(Clamp(r), Clamp(g), Clamp(b), 255);
            }

            static byte Clamp(int v) => (byte)(v < 0 ? 0 : v > 255 ? 255 : v);
        }
    }
}
