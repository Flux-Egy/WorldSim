using WorldSim.Core;

namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// Per-cell data of the new terrain look (rebuild phase 2), shared by the CPU reference compositor and the Unity
    /// renderer: terraces (<see cref="LevelOf"/>: 0-2 water, 3 beach = water surface, 4-12 land; the top face rises
    /// <see cref="LiftPerLevel"/> px per level), water depth rings by distance to land, and the biome each cell is drawn
    /// with (<see cref="RenderBiome"/>: everything on the snow terrace is snow). Per-pixel borders come from
    /// <see cref="TerrainField"/>. Pure C#, deterministic.
    /// </summary>
    public sealed class TerrainLayout
    {
        public const int CellPixels = 16;
        public const int LiftPerLevel = 3;
        public const int WaterLevel = 3;
        public const int TopLevel = 12;
        public const int MaxLift = (TopLevel - WaterLevel) * LiftPerLevel;

        public readonly int Width, Height;          // cells
        /// <summary>Per cell: terrace 0..12.</summary>
        public readonly byte[] Level;
        /// <summary>Per cell: water band 0 deep, 1 ocean, 2 shallows; 255 for land.</summary>
        public readonly byte[] Band;
        /// <summary>Per cell: the biome whose tile is drawn (the simulation biome, except snow on the snow terrace).</summary>
        public readonly byte[] RenderBiome;
        /// <summary>Per cell: height blurred over 3x3 (water counts as beach height), for the light far-zoom hillshade.</summary>
        public readonly byte[] SmoothHeight;

        public static int Lift(int level) => level > WaterLevel ? (level - WaterLevel) * LiftPerLevel : 0;

        /// <summary>
        /// Height byte -> render terrace (water by biome so coral shallows and edits stay consistent). The art pack's
        /// 10 gameplay levels (world_rules.json) map onto these; the renderer gives mountains three terraces instead of
        /// one plateau so their height reads: 4 lowland, 5 hills, 7 highland, 9-11 mountain, 12 snow peak.
        /// </summary>
        public static byte LevelOf(TileData t)
        {
            if (t.IsWater) return 2;
            int h = t.Height;
            if (t.BiomeId == (byte)Biome.Beach || h < WorldGenerator.BeachBelow) return 3;
            if (h < 150) return 4;                                              // lowland: flat, no clutter of small cliffs
            if (h < 184) return 5;                                              // hills
            if (h < WorldGenerator.MountainFrom) return 7;                      // highland: a two-level step up
            if (h < 216) return 9;
            if (h < 228) return 10;
            if (h < WorldGenerator.SnowPeakFrom) return 11;
            return 12;
        }

        /// <summary>
        /// Levels from a 3x3 box-averaged height (water and beach stay as the tile says), then a majority pass that
        /// removes one-cell terraces: contours become long, readable cliff lines instead of scattered fragments.
        /// </summary>
        static byte[] SmoothLevels(TileData[] tiles, int w, int h)
        {
            var lv = new byte[tiles.Length];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    int i = y * w + x;
                    TileData t = tiles[i];
                    byte own = LevelOf(t);
                    if (own <= WaterLevel) { lv[i] = own; continue; }
                    int sum = 0, n = 0;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
                            TileData o = tiles[ny * w + nx];
                            sum += o.IsWater ? WorldGenerator.BeachBelow : o.Height;
                            n++;
                        }
                    var avg = t;
                    avg.Height = (byte)(sum / n);
                    byte l = LevelOf(avg);
                    if (l <= WaterLevel) l = WaterLevel + 1;                       // land stays land
                    if (t.BiomeId == (byte)Biome.Snow && l < TopLevel) l = TopLevel; // snow caps sit on top
                    else if (l == TopLevel && t.BiomeId != (byte)Biome.Snow) l = TopLevel - 1;
                    lv[i] = l;
                }
            for (int pass = 0; pass < 2; pass++) lv = Majority(lv, w, h);
            MergeSmallTerraces(lv, w, h, 40);              // owner: fewer, clearer terraces even at near zoom
            return lv;
        }

        /// <summary>Terrace patches smaller than <paramref name="minCells"/> join their most common neighbour terrace,
        /// so cliffs only outline real plateaus (no scattered cliff fragments).</summary>
        static void MergeSmallTerraces(byte[] lv, int w, int h, int minCells)
        {
            var comp = new int[lv.Length];
            for (int i = 0; i < comp.Length; i++) comp[i] = -1;
            var stack = new int[lv.Length];
            var members = new int[lv.Length];
            var votes = new int[TopLevel + 1];
            int id = 0;
            for (int start = 0; start < lv.Length; start++)
            {
                if (comp[start] >= 0 || lv[start] <= WaterLevel) continue;
                int sp = 0, n = 0;
                stack[sp++] = start; comp[start] = id;
                System.Array.Clear(votes, 0, votes.Length);
                while (sp > 0)
                {
                    int c = stack[--sp];
                    members[n++] = c;
                    int cx = c % w, cy = c / w;
                    for (int k = 0; k < 4; k++)
                    {
                        int nx = cx + (k == 0 ? 1 : k == 1 ? -1 : 0), ny = cy + (k == 2 ? 1 : k == 3 ? -1 : 0);
                        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
                        int o = ny * w + nx;
                        if (lv[o] == lv[start]) { if (comp[o] < 0) { comp[o] = id; stack[sp++] = o; } }
                        else if (lv[o] > WaterLevel) votes[lv[o]]++;
                    }
                }
                id++;
                if (n >= minCells) continue;
                int best = -1;
                for (int l = WaterLevel + 1; l <= TopLevel; l++) if (votes[l] > 0 && (best < 0 || votes[l] > votes[best])) best = l;
                if (best < 0) continue;                                   // an island: keep it
                for (int m = 0; m < n; m++) lv[members[m]] = (byte)best;
            }
        }

        static byte[] Majority(byte[] lv, int w, int h)
        {
            var outLv = (byte[])lv.Clone();
            var votes = new int[TopLevel + 1];
            for (int y = 1; y < h - 1; y++)
                for (int x = 1; x < w - 1; x++)
                {
                    int i = y * w + x;
                    if (lv[i] <= WaterLevel) continue;
                    System.Array.Clear(votes, 0, votes.Length);
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                            if ((dx | dy) != 0) votes[lv[i + dy * w + dx]]++;
                    if (votes[lv[i]] >= 3) continue;
                    int best = lv[i];
                    for (int l = WaterLevel + 1; l <= TopLevel; l++) if (votes[l] > votes[best]) best = l;
                    outLv[i] = (byte)best;
                }
            return outLv;
        }

        /// <summary>Cliff material for a level: earth (lowland, hills), stone (highland, mountain), snow (peaks).</summary>
        public static string CliffMaterial(int level) => level <= 7 ? "earth" : level < TopLevel ? "stone" : "snow";

        public TerrainLayout(TileData[] tiles, int width, int height)
        {
            Width = width; Height = height;
            Level = SmoothLevels(tiles, width, height);
            Band = WaterBands(tiles, width, height);
            RenderBiome = new byte[tiles.Length];
            for (int i = 0; i < tiles.Length; i++)
                RenderBiome[i] = Level[i] == TopLevel ? (byte)Biome.Snow : tiles[i].BiomeId;
            SmoothHeight = new byte[tiles.Length];
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    int sum = 0, n = 0;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
                            var t = tiles[ny * width + nx];
                            sum += t.IsWater ? WorldGenerator.BeachBelow : t.Height; n++;
                        }
                    SmoothHeight[y * width + x] = (byte)(sum / n);
                }
        }

        public static uint Hash(int x, int y)
        {
            unchecked { return (uint)(SplitMix64.Mix(((ulong)(uint)x << 32) | (uint)y ^ 0x9E3779B97F4A7C15UL) >> 32); }
        }

        /// <summary>Distance-to-land rings (8-neighbour BFS): 1-2 shallows, 3-5 ocean, deeper beyond.</summary>
        static byte[] WaterBands(TileData[] tiles, int w, int h)
        {
            var dist = new int[tiles.Length];
            var queue = new int[tiles.Length];
            int head = 0, tail = 0;
            for (int i = 0; i < tiles.Length; i++)
            {
                if (tiles[i].IsWater) dist[i] = int.MaxValue;
                else { dist[i] = 0; queue[tail++] = i; }
            }
            while (head < tail)
            {
                int c = queue[head++], cx = c % w, cy = c / w;
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int nx = cx + dx, ny = cy + dy;
                        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
                        int n = ny * w + nx;
                        if (dist[n] > dist[c] + 1) { dist[n] = dist[c] + 1; queue[tail++] = n; }
                    }
            }
            var band = new byte[tiles.Length];
            for (int i = 0; i < band.Length; i++)
                band[i] = dist[i] == 0 ? (byte)255 : dist[i] <= 2 ? (byte)2 : dist[i] <= 5 ? (byte)1 : (byte)0;
            return band;
        }
    }
}
