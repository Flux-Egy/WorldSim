using WorldSim.Core;

namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// The new terrain look (rebuild phase 2), as data both renderers share (the CPU reference/preview compositor and
    /// the Unity shader renderer):
    /// <list type="bullet">
    /// <item>A 4 px sub-cell grid (4 x 4 per 16 px cell). Each sub-cell takes the tile of a neighbouring cell picked by
    /// a deterministic +-1 sub-cell displacement, so biome borders, coasts and terraces become crisp 4 px pixel stairs
    /// instead of 16 px squares or blurred blends.</item>
    /// <item>Terraces (<see cref="LevelOf"/>): 0-2 water, 3 beach (= water surface), 4-12 land.
    /// The top face rises 6 px per level above the beach; a lower sub-cell in front shows a cliff face.</item>
    /// <item>Water depth bands by distance to land: shallows (1-2 cells), ocean (3-5), deep beyond.</item>
    /// </list>
    /// Pure C#, deterministic, no allocations except the result arrays.
    /// </summary>
    public sealed class TerrainLayout
    {
        public const int CellPixels = 16;
        public const int SubPixels = 4;
        public const int SubPerCell = CellPixels / SubPixels;
        public const int LiftPerLevel = 6;
        public const int WaterLevel = 3;
        public const int TopLevel = 12;
        public const int MaxLift = (TopLevel - WaterLevel) * LiftPerLevel;

        public readonly int Width, Height;          // cells
        public readonly int SubWidth, SubHeight;    // sub-cells
        /// <summary>Per sub-cell: index of the cell whose tile it shows.</summary>
        public readonly int[] SubCell;
        /// <summary>Per sub-cell: elevation level 0..9 of that cell.</summary>
        public readonly byte[] SubLevel;
        /// <summary>Per cell: elevation level 0..9.</summary>
        public readonly byte[] Level;
        /// <summary>Per cell: water band 0 deep, 1 ocean, 2 shallows; 255 for land.</summary>
        public readonly byte[] Band;

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
            return lv;
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
            SubWidth = width * SubPerCell; SubHeight = height * SubPerCell;
            Level = SmoothLevels(tiles, width, height);
            Band = WaterBands(tiles, width, height);

            SubCell = new int[SubWidth * SubHeight];
            SubLevel = new byte[SubCell.Length];
            for (int sy = 0; sy < SubHeight; sy++)
                for (int sx = 0; sx < SubWidth; sx++)
                {
                    int own = (sy / SubPerCell) * width + sx / SubPerCell;
                    Displace(sx, sy, out int dx, out int dy);
                    int nx = Clamp((sx + dx) / SubPerCell, width), ny = Clamp((sy + dy) / SubPerCell, height);
                    int cell = ny * width + nx;
                    // Displace only within one terrace: cliff lines stay straight, continuous 16 px steps.
                    if (Level[cell] != Level[own]) cell = own;
                    int s = sy * SubWidth + sx;
                    SubCell[s] = cell;
                    SubLevel[s] = Level[cell];
                }
        }

        static int Clamp(int v, int n) => v < 0 ? 0 : v >= n ? n - 1 : v;

        /// <summary>Deterministic +-1 sub-cell offset; only sub-cells on a cell's rim move, so the result is a border wiggle.</summary>
        public static void Displace(int sx, int sy, out int dx, out int dy)
        {
            uint h = Hash(sx, sy);
            int lx = sx % SubPerCell, ly = sy % SubPerCell;
            dx = lx == 0 ? -(int)(h & 1) : lx == SubPerCell - 1 ? (int)(h & 1) : 0;
            dy = ly == 0 ? -(int)((h >> 1) & 1) : ly == SubPerCell - 1 ? (int)((h >> 1) & 1) : 0;
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
