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

        public void Draw(uint[] img, int W, int H, int ppc, IArtPixels art)
        {
            foreach (var f in Farms)
                for (int y = 0; y < ppc; y++)
                    for (int x = 0; x < ppc; x++)
                        Put(img, W, H, f.CellX * ppc + x, f.CellY * ppc + y, (y & 1) == 0 ? FarmA : FarmB);

            foreach (var r in Roads)
                for (int k = 0; k + 3 < r.Length; k += 2)
                    Line(img, W, H, r[k] * ppc + ppc / 2, r[k + 1] * ppc + ppc / 2, r[k + 2] * ppc + ppc / 2, r[k + 3] * ppc + ppc / 2, ppc >= 4);

            var sorted = new List<Marker>(Markers);
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
