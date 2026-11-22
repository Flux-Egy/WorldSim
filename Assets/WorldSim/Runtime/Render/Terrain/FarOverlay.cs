using System.Collections.Generic;

namespace WorldSim.Render.Terrain
{
    /// <summary>
    /// What the far zoom draws on top of the ground so the world reads at a glance: farms (striped patches), roads
    /// (1 px lines), and the pack's <c>mk_*</c> markers (Terrain/lod) at a constant screen size, kingdom markers in the
    /// kingdom's TEAM ramp. Filled by the presentation layer from the simulation (or by the preview tool with demo data).
    /// </summary>
    public sealed class FarOverlay
    {
        public struct Marker
        {
            public string Frame;        // mk_village, mk_city, mk_capital, mk_army, mk_monster, mk_fire, ...
            public int CellX, CellY;
            public int Kingdom;         // index into TeamRamps, or -1 for markers without kingdom colour
        }

        public struct Farm { public int CellX, CellY; }

        /// <summary>Per kingdom: the TEAM ramp, five colours from dark to light (kingdom_palettes.json "team").</summary>
        public readonly List<uint[]> TeamRamps = new List<uint[]>();
        public readonly List<Marker> Markers = new List<Marker>();
        public readonly List<Farm> Farms = new List<Farm>();
        /// <summary>Roads as cell paths: x0, y0, x1, y1, ... (straight segments between the points).</summary>
        public readonly List<int[]> Roads = new List<int[]>();

        static readonly uint FarmA = Rgba.Pack(200, 170, 82), FarmB = Rgba.Pack(140, 120, 62);
        static readonly uint Road = Rgba.Pack(160, 128, 88), RoadShadow = Rgba.Pack(96, 80, 56);

        /// <summary>Optional kingdom territory per cell: 0 = none, k + 1 = kingdom k. <see cref="TerritoryWidth"/> cells per row.</summary>
        public byte[] Territory;
        public int TerritoryWidth;

        /// <param name="mapMode">Map zoom: strong territory fill, roads and capitals only.</param>
        public void Draw(uint[] img, int W, int H, int ppc, IArtPixels art, bool mapMode = false)
        {
            if (Territory != null && TerritoryWidth > 0) DrawTerritory(img, W, H, ppc, mapMode);
            if (mapMode)
            {
                foreach (var r in Roads)
                    for (int k = 0; k + 3 < r.Length; k += 2)
                        Line(img, W, H, r[k] * ppc + ppc / 2, r[k + 1] * ppc + ppc / 2, r[k + 2] * ppc + ppc / 2, r[k + 3] * ppc + ppc / 2, false);
                DrawMarkers(img, W, H, ppc, art, m => m.Frame == "mk_capital");
                return;
            }
            foreach (var f in Farms)
                for (int y = 0; y < ppc; y++)
                    for (int x = 0; x < ppc; x++)
                        Put(img, W, H, f.CellX * ppc + x, f.CellY * ppc + y, (y & 1) == 0 ? FarmA : FarmB);

            foreach (var r in Roads)
                for (int k = 0; k + 3 < r.Length; k += 2)
                    Line(img, W, H, r[k] * ppc + ppc / 2, r[k + 1] * ppc + ppc / 2, r[k + 2] * ppc + ppc / 2, r[k + 3] * ppc + ppc / 2, ppc >= 4);

            // Settlements read as a small cluster of houses with roofs in the kingdom's colour (owner, 2026-11-22);
            // other markers (army, monster, events) keep their mk_* icons.
            foreach (var m in Markers)
            {
                int houses = m.Frame == "mk_village" ? 2 : m.Frame == "mk_town" ? 3 : m.Frame == "mk_city" ? 4 : m.Frame == "mk_capital" ? 5 : 0;
                if (houses > 0) DrawHouses(img, W, H, ppc, m, houses);
            }
            DrawMarkers(img, W, H, ppc, art, m => m.Frame != "mk_village" && m.Frame != "mk_town" && m.Frame != "mk_city" && m.Frame != "mk_capital");
        }

        static readonly int[,] HouseSpots = { { 0, 0 }, { -5, 2 }, { 5, 1 }, { -2, -4 }, { 3, -5 } };
        static readonly uint Wall = Rgba.Pack(226, 212, 176), WallShade = Rgba.Pack(180, 164, 128), Door = Rgba.Pack(92, 70, 52);

        void DrawHouses(uint[] img, int W, int H, int ppc, Marker m, int count)
        {
            uint[] ramp = m.Kingdom >= 0 && m.Kingdom < TeamRamps.Count ? TeamRamps[m.Kingdom] : null;
            uint roofLight = ramp != null ? ramp[3] : Rgba.Pack(200, 90, 60), roof = ramp != null ? ramp[2] : Rgba.Pack(170, 70, 50);
            int cx = m.CellX * ppc + ppc / 2, cy = m.CellY * ppc + ppc / 2;
            int scale = ppc >= 4 ? 1 : 0;                                        // mid: 5x5 houses, far: 3x3
            for (int k = 0; k < count; k++)
            {
                int hx = cx + HouseSpots[k, 0] * (scale + 1) / 2, hy = cy + HouseSpots[k, 1] * (scale + 1) / 2;
                if (scale == 1)
                {
                    // . r r r .   roof (light top row)
                    // r R R R r
                    // w w w w s   wall, shade on the right
                    // w d w w s
                    for (int x = 1; x <= 3; x++) Put(img, W, H, hx - 2 + x, hy - 2, roofLight);
                    for (int x = 0; x <= 4; x++) Put(img, W, H, hx - 2 + x, hy - 1, roof);
                    for (int x = 0; x <= 4; x++) { Put(img, W, H, hx - 2 + x, hy, x == 4 ? WallShade : Wall); Put(img, W, H, hx - 2 + x, hy + 1, x == 4 ? WallShade : x == 1 ? Door : Wall); }
                    Put(img, W, H, hx - 1, hy + 2, Rgba.Pack(60, 70, 50));   // a pixel of ground shadow
                    Put(img, W, H, hx, hy + 2, Rgba.Pack(60, 70, 50));
                }
                else
                {
                    Put(img, W, H, hx, hy - 1, roofLight);
                    for (int x = -1; x <= 1; x++) { Put(img, W, H, hx + x, hy, roof); Put(img, W, H, hx + x, hy + 1, x == 1 ? WallShade : Wall); }
                }
            }
            if (m.Frame == "mk_capital" && ramp != null)                        // a small banner over the capital
            {
                int fx = cx + 1, fy = cy - 3 - 3 * scale;
                for (int y = 0; y < 3 + scale * 2; y++) Put(img, W, H, fx, fy + y, Rgba.Pack(70, 54, 40));
                Put(img, W, H, fx + 1, fy, ramp[3]); Put(img, W, H, fx + 2, fy, ramp[2]); Put(img, W, H, fx + 1, fy + 1, ramp[2]);
            }
        }

        void DrawTerritory(uint[] img, int W, int H, int ppc, bool mapMode)
        {
            int tw = TerritoryWidth, th = Territory.Length / tw;
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    int cx = x / ppc, cy = y / ppc;
                    if (cx >= tw || cy >= th) continue;
                    int k = Territory[cy * tw + cx] - 1;
                    if (k < 0 || k >= TeamRamps.Count) continue;
                    uint[] ramp = TeamRamps[k];
                    // Border: a neighbouring pixel that belongs to another owner (or none).
                    bool border = false;
                    for (int d = 0; d < 4 && !border; d++)
                    {
                        int nx = x + (d == 0 ? 1 : d == 1 ? -1 : 0), ny = y + (d == 2 ? 1 : d == 3 ? -1 : 0);
                        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
                        int ncx = nx / ppc, ncy = ny / ppc;
                        if (ncx >= tw || ncy >= th || Territory[ncy * tw + ncx] != k + 1) border = true;
                    }
                    int i = y * W + x;
                    img[i] = border ? (mapMode ? ramp[1] : Rgba.Mix(img[i], ramp[1], 200)) : Rgba.Mix(img[i], ramp[2], mapMode ? 150 : 64);   // ~25 % tint off the map
                }
        }

        void DrawMarkers(uint[] img, int W, int H, int ppc, IArtPixels art, System.Predicate<Marker> keep)
        {
            var sorted = Markers.FindAll(keep);
            sorted.Sort((a, b) => a.CellY != b.CellY ? a.CellY.CompareTo(b.CellY) : a.CellX.CompareTo(b.CellX));
            foreach (var m in sorted)
            {
                if (!art.TryFrame(m.Frame, out int f)) continue;
                int fw = art.Width(f), fh = art.Height(f);
                int left = m.CellX * ppc + ppc / 2 - (int)(art.PivotX(f) * fw);
                int top = m.CellY * ppc + ppc / 2 - (int)((1f - art.PivotY(f)) * fh);
                uint[] ramp = m.Kingdom >= 0 && m.Kingdom < TeamRamps.Count ? TeamRamps[m.Kingdom] : null;
                for (int y = 0; y < fh; y++)
                    for (int x = 0; x < fw; x++)
                    {
                        uint c = art.Pixel(f, x, y);
                        int a = Rgba.A(c);
                        if (a == 0) continue;
                        if (ramp != null && art.Mask(f, x, y, out int region, out int step) && region <= 4)
                            c = ramp[step < 0 ? 0 : step > 4 ? 4 : step];
                        int px = left + x, py = top + y;
                        if (px < 0 || py < 0 || px >= W || py >= H) continue;
                        img[py * W + px] = a == 255 ? c : Rgba.Mix(img[py * W + px], c, a);
                    }
            }
        }

        static void Line(uint[] img, int W, int H, int x0, int y0, int x1, int y1, bool shadow)
        {
            int dx = System.Math.Abs(x1 - x0), dy = -System.Math.Abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1, err = dx + dy;
            while (true)
            {
                if (shadow && y0 + 1 < H && x0 >= 0 && x0 < W && y0 + 1 >= 0) img[(y0 + 1) * W + x0] = Rgba.Mix(img[(y0 + 1) * W + x0], RoadShadow, 110);
                Put(img, W, H, x0, y0, Road);
                if (x0 == x1 && y0 == y1) break;
                int e2 = 2 * err;
                if (e2 >= dy) { err += dy; x0 += sx; }
                if (e2 <= dx) { err += dx; y0 += sy; }
            }
        }

        static void Put(uint[] img, int W, int H, int x, int y, uint c) { if (x >= 0 && y >= 0 && x < W && y < H) img[y * W + x] = c; }
    }
}
