using WorldSim.Core;

namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// Which cell (and terrace) every world pixel shows. Instead of 16 px squares, each pixel looks at the four nearest
    /// cell centres (bilinear weights) at a slightly noise-warped position and picks, in order:
    /// land or water (by total weight), then the terrace, then the biome (or the water band), each by the largest
    /// support. Region edges become smooth, rounded contours with a small noise wiggle; lone cells become small round
    /// blobs instead of notches or teeth. Close biome contests are ordered-dithered over 2-3 px (a soft, crisp blend).
    /// Pure C#, deterministic, integer only.
    /// </summary>
    public sealed class TerrainField
    {
        const int Px = TerrainLayout.CellPixels;
        public const int WarpPixels = 3;      // contour wiggle amplitude
        const int DitherBand = 140;           // of 1024: support gap below which two biomes are dithered

        readonly TileData[] _tiles;
        readonly TerrainLayout _lay;
        readonly int _w, _h;

        static readonly int[] Bayer =
        {
            0, 8, 2, 10,
            12, 4, 14, 6,
            3, 11, 1, 9,
            15, 7, 13, 5,
        };

        public TerrainField(TileData[] tiles, TerrainLayout layout)
        {
            _tiles = tiles; _lay = layout; _w = layout.Width; _h = layout.Height;
        }

        /// <summary>World pixel (X, Y), 16 per cell -> the cell whose ground it shows and its terrace.</summary>
        public void Pick(int x, int y, out int cell, out int level)
        {
            // Smooth warp of the sample point (value noise, period 8 px).
            int wx = x + Noise(x, y, 0x51ED) * WarpPixels / 128;
            int wy = y + Noise(x, y, 0x7A3B) * WarpPixels / 128;
            int gx = wx - Px / 2, gy = wy - Px / 2;
            int i0 = gx >> 4, j0 = gy >> 4;                       // arithmetic shift = floor
            int fx = gx & 15, fy = gy & 15;
            int ax1 = 2 * fx + 1, ax0 = 32 - ax1, ay1 = 2 * fy + 1, ay0 = 32 - ay1;   // weights sum to 32 each

            int c0 = Cell(i0, j0), c1 = Cell(i0 + 1, j0), c2 = Cell(i0, j0 + 1), c3 = Cell(i0 + 1, j0 + 1);
            int w0 = ax0 * ay0, w1 = ax1 * ay0, w2 = ax0 * ay1, w3 = ax1 * ay1;  // sum 1024

            // 1) land or water
            int land = (Water(c0) ? 0 : w0) + (Water(c1) ? 0 : w1) + (Water(c2) ? 0 : w2) + (Water(c3) ? 0 : w3);
            bool isLand = land * 2 > 1024 || (land * 2 == 1024 && ((x ^ y) & 1) == 0);

            // 2) terrace (land) or band (water): key with the largest support among the matching cells
            int k0 = Key(c0, isLand), k1 = Key(c1, isLand), k2 = Key(c2, isLand), k3 = Key(c3, isLand);
            int bestKey = Best(k0, w0, k1, w1, k2, w2, k3, w3, out _, out _, out _);

            // 3) biome within that terrace/band, dithered where two biomes are nearly tied
            int b0 = k0 == bestKey ? BiomeOf(c0) : -1, b1 = k1 == bestKey ? BiomeOf(c1) : -1;
            int b2 = k2 == bestKey ? BiomeOf(c2) : -1, b3 = k3 == bestKey ? BiomeOf(c3) : -1;
            int bestBiome = Best(b0, w0, b1, w1, b2, w2, b3, w3, out int s1, out int second, out int s2);
            if (second >= 0 && s1 - s2 < DitherBand)
            {
                int t = (s1 - s2) * 16 / DitherBand;               // 0..15: 0 = tie
                if (Bayer[(y & 3) * 4 + (x & 3)] > 7 + t / 2) bestBiome = second;
            }

            // The cell of that terrace/band and biome with the largest weight.
            int pick = -1, bw = -1;
            if (k0 == bestKey && b0 == bestBiome && w0 > bw) { bw = w0; pick = c0; }
            if (k1 == bestKey && b1 == bestBiome && w1 > bw) { bw = w1; pick = c1; }
            if (k2 == bestKey && b2 == bestBiome && w2 > bw) { bw = w2; pick = c2; }
            if (k3 == bestKey && b3 == bestBiome && w3 > bw) { pick = c3; }
            cell = pick;
            level = _lay.Level[pick];
        }

        int Cell(int i, int j)
        {
            if (i < 0) i = 0; else if (i >= _w) i = _w - 1;
            if (j < 0) j = 0; else if (j >= _h) j = _h - 1;
            return j * _w + i;
        }

        bool Water(int c) => _lay.Level[c] < TerrainLayout.WaterLevel;
        int BiomeOf(int c) => _lay.RenderBiome[c];
        int Key(int c, bool land) => Water(c) == !land ? (land ? _lay.Level[c] : 100 + _lay.Band[c]) : -1;

        /// <summary>Sums weights per key (keys &lt; 0 ignored); returns the best key, its support and the runner-up.</summary>
        static int Best(int k0, int w0, int k1, int w1, int k2, int w2, int k3, int w3, out int s1, out int second, out int s2)
        {
            int best = -1; s1 = -1; second = -1; s2 = -1;
            for (int n = 0; n < 4; n++)
            {
                int k = n == 0 ? k0 : n == 1 ? k1 : n == 2 ? k2 : k3;
                if (k < 0) continue;
                bool seen = false;
                for (int m = 0; m < n; m++) if ((m == 0 ? k0 : m == 1 ? k1 : m == 2 ? k2 : k3) == k) seen = true;
                if (seen) continue;
                int s = (k0 == k ? w0 : 0) + (k1 == k ? w1 : 0) + (k2 == k ? w2 : 0) + (k3 == k ? w3 : 0);
                if (s > s1 || (s == s1 && k > best)) { second = best; s2 = s1; best = k; s1 = s; }
                else if (s > s2) { second = k; s2 = s; }
            }
            return best;
        }

        /// <summary>Smooth value noise in [-128, 127], period 8 px.</summary>
        public static int Noise(int x, int y, int seed)
        {
            int xi = x >> 3, yi = y >> 3, fx = x & 7, fy = y & 7;
            int a = Lattice(xi, yi, seed), b = Lattice(xi + 1, yi, seed), c = Lattice(xi, yi + 1, seed), d = Lattice(xi + 1, yi + 1, seed);
            int top = a * (8 - fx) + b * fx, bottom = c * (8 - fx) + d * fx;
            return (top * (8 - fy) + bottom * fy) / 64;
        }

        static int Lattice(int x, int y, int seed) => (int)(TerrainLayout.Hash(x * 31 + seed, y) & 255) - 128;
    }
}
