using WorldSim.Core;

namespace WorldSim.Render
{
    /// <summary>
    /// Procedural pixel-art sprites for every <see cref="Decoration"/>, drawn in code (no
    /// external art). Designed at 8 pixels per tile; each sprite lives in a 16x16 cell, origin
    /// bottom-left, anchored at the bottom centre (x = 8). Pixels with alpha below 255 are
    /// shadows: they darken whatever is underneath instead of replacing it.
    /// Built once at startup into a flat array (cell index = decoration * Variants + variant).
    /// </summary>
    public static class SpriteLibrary
    {
        public const int Cell = 16;
        public const int Variants = 3;
        public const int CellPixels = Cell * Cell;
        public const uint Shadow = 0x60000000; // alpha 96: "darken underneath" marker

        public static int CellIndex(Decoration d, int variant) => (int)d * Variants + variant;
        public static int AtlasLength => (int)Decoration.Count * Variants * CellPixels;

        public static uint[] Build()
        {
            var atlas = new uint[AtlasLength];
            for (int d = 1; d < (int)Decoration.Count; d++)
                for (int v = 0; v < Variants; v++)
                    Draw(new Canvas(atlas, CellIndex((Decoration)d, v) * CellPixels), (Decoration)d, v);
            return atlas;
        }

        /// <summary>Drawing helper over one 16x16 cell of the atlas.</summary>
        struct Canvas
        {
            readonly uint[] _buf;
            readonly int _off;
            public Canvas(uint[] buf, int off) { _buf = buf; _off = off; }

            public void Set(int x, int y, uint c)
            {
                if (x < 0 || y < 0 || x >= Cell || y >= Cell) return;
                _buf[_off + y * Cell + x] = c;
            }

            public uint Get(int x, int y) => x < 0 || y < 0 || x >= Cell || y >= Cell ? 0 : _buf[_off + y * Cell + x];

            public void Rect(int x0, int y0, int w, int h, uint c)
            {
                for (int y = y0; y < y0 + h; y++) for (int x = x0; x < x0 + w; x++) Set(x, y, c);
            }

            /// <summary>Filled ellipse with top-left light, bottom-right shade and a dark rim.</summary>
            public void Blob(int cx, int cy, int rx, int ry, uint baseC, uint light, uint dark, uint rim)
            {
                for (int y = cy - ry; y <= cy + ry; y++)
                    for (int x = cx - rx; x <= cx + rx; x++)
                    {
                        int dx = x - cx, dy = y - cy;
                        int d = dx * dx * ry * ry + dy * dy * rx * rx;
                        int r2 = rx * rx * ry * ry;
                        if (d > r2) continue;
                        uint c = baseC;
                        int s = dx - dy; // light from top-left
                        if (s <= -(rx + ry) / 2) c = light;
                        else if (s >= (rx + ry) / 2) c = dark;
                        if (d > r2 * 64 / 100 && (dx > 0 || dy < 0)) c = rim;
                        Set(x, y, c);
                    }
            }

            public void GroundShadow(int cx, int rx)
            {
                for (int x = cx - rx; x <= cx + rx; x++) { Set(x, 0, Shadow); if (x > cx - rx && x < cx + rx) Set(x, 1, Shadow); }
            }
        }

        static uint P(int r, int g, int b) => Rgba.Pack(r, g, b);

        static void Draw(Canvas c, Decoration d, int v)
        {
            uint trunk = P(104, 72, 44), trunkDark = P(74, 50, 32);
            switch (d)
            {
                case Decoration.OakTree:
                {
                    int r = 4 + (v == 2 ? 1 : 0);
                    uint g = v == 1 ? P(70, 140, 50) : P(60, 128, 46);
                    c.GroundShadow(8, r);
                    c.Rect(7, 1, 2, 4, trunk); c.Set(8, 1, trunkDark); c.Set(8, 2, trunkDark);
                    c.Blob(8, 5 + r, r, r - (v == 0 ? 1 : 0), g, Rgba.Shift(g, 34), Rgba.Shift(g, -26), Rgba.Shift(g, -46));
                    break;
                }
                case Decoration.PineTree:
                case Decoration.SnowPine:
                {
                    int top = 12 + v;
                    uint g = P(40, 98, 66), lt = P(62, 128, 84), dk = P(26, 70, 48);
                    c.GroundShadow(8, 3);
                    c.Rect(8, 1, 1, 3, trunkDark);
                    for (int y = 3; y <= top; y++)
                    {
                        int tier = (top - y) % 4;              // stepped silhouette
                        int w = (top - y) / 3 + 1 + (tier == 0 ? 1 : 0);
                        for (int x = 8 - w; x <= 8 + w - 1; x++)
                        {
                            uint col = x < 8 ? lt : x > 8 ? dk : g;
                            if (d == Decoration.SnowPine && (tier == 0 || x < 7) && (x + y) % 2 == 0) col = P(236, 242, 250);
                            c.Set(x, y, col);
                        }
                    }
                    break;
                }
                case Decoration.BirchTree:
                {
                    uint bark = P(232, 230, 222), mark = P(40, 40, 40), g = P(138, 192, 86);
                    c.GroundShadow(8, 3);
                    c.Rect(8, 1, 1, 8, bark); c.Set(8, 3, mark); c.Set(8, 6, mark);
                    c.Blob(8, 10 + v % 2, 3, 3 + v % 2, g, Rgba.Shift(g, 30), Rgba.Shift(g, -30), Rgba.Shift(g, -50));
                    break;
                }
                case Decoration.PalmTree:
                {
                    int lean = v - 1;
                    c.GroundShadow(8, 3);
                    for (int y = 1; y <= 9; y++) c.Set(8 + (y * lean) / 6, y, (y & 1) == 0 ? trunk : trunkDark);
                    int tx = 8 + (9 * lean) / 6, ty = 10;
                    uint g = P(66, 150, 60), dk = P(40, 104, 44);
                    for (int i = 1; i <= 4; i++)
                    {
                        c.Set(tx - i, ty - i / 2, i > 2 ? dk : g); c.Set(tx + i, ty - i / 2, i > 2 ? dk : g);
                        c.Set(tx - i / 2, ty + 1, g); c.Set(tx + i / 2, ty + 1, g);
                    }
                    c.Set(tx, ty, P(120, 90, 40));
                    break;
                }
                case Decoration.JungleTree:
                {
                    uint g = P(30, 106, 40);
                    c.GroundShadow(8, 5);
                    c.Rect(7, 1, 2, 4, trunkDark);
                    c.Blob(8, 9, 5 + (v == 2 ? 1 : 0), 5, g, Rgba.Shift(g, 30), Rgba.Shift(g, -18), Rgba.Shift(g, -30));
                    c.Set(5, 6, P(54, 140, 50)); c.Set(5, 5, P(54, 140, 50)); c.Set(11, 6, P(54, 140, 50)); // vines
                    if (v == 1) { c.Set(9, 11, P(230, 70, 80)); c.Set(6, 8, P(240, 200, 60)); }             // fruit
                    break;
                }
                case Decoration.DeadTree:
                {
                    uint b = P(110, 92, 74), bd = P(80, 66, 54);
                    c.GroundShadow(8, 2);
                    c.Rect(8, 1, 1, 8, b);
                    c.Set(7, 6, bd); c.Set(6, 7, bd); c.Set(9, 5, b); c.Set(10, 6, b); c.Set(10, 7, bd);
                    if (v > 0) { c.Set(7, 9, bd); c.Set(9, 9, b); }
                    break;
                }
                case Decoration.Bush:
                case Decoration.BerryBush:
                {
                    uint g = v == 2 ? P(84, 150, 58) : P(70, 136, 52);
                    c.GroundShadow(8, 3);
                    c.Blob(8, 3, 3, 2 + v % 2, g, Rgba.Shift(g, 30), Rgba.Shift(g, -24), Rgba.Shift(g, -40));
                    if (d == Decoration.BerryBush) { c.Set(7, 4, P(214, 40, 60)); c.Set(9, 3, P(214, 40, 60)); c.Set(8, 2, P(214, 40, 60)); }
                    break;
                }
                case Decoration.Flowers:
                {
                    uint[] cols = { P(240, 80, 90), P(250, 210, 70), P(246, 246, 246), P(186, 110, 230) };
                    for (int i = 0; i < 4; i++)
                    {
                        int x = 4 + (i * 3 + v * 2) % 9, y = 1 + (i * 2 + v) % 4;
                        c.Set(x, y - 1, P(60, 130, 50));
                        c.Set(x, y, cols[(i + v) % 4]);
                    }
                    break;
                }
                case Decoration.TallGrass:
                {
                    uint g = P(132, 186, 80), dk = P(92, 150, 60);
                    for (int i = 0; i < 4; i++)
                    {
                        int x = 5 + i * 2 + (v & 1), hgt = 2 + (i + v) % 2;
                        for (int y = 0; y < hgt; y++) c.Set(x, y, y == hgt - 1 ? g : dk);
                    }
                    break;
                }
                case Decoration.Cactus:
                {
                    uint g = P(76, 150, 70), lt = P(110, 186, 96), dk = P(48, 104, 48);
                    c.GroundShadow(8, 2);
                    int hgt = 7 + v;
                    for (int y = 1; y <= hgt; y++) { c.Set(7, y, lt); c.Set(8, y, g); c.Set(9, y, dk); }
                    c.Set(6, 4, lt); c.Set(5, 4, lt); c.Set(5, 5, lt); c.Set(5, 6, g);
                    if (v != 1) { c.Set(10, 5, dk); c.Set(11, 5, dk); c.Set(11, 6, dk); c.Set(11, 7, g); }
                    break;
                }
                case Decoration.Rock:
                case Decoration.Boulder:
                case Decoration.EmberRock:
                case Decoration.IceRock:
                {
                    bool big = d == Decoration.Boulder;
                    uint g = d == Decoration.EmberRock ? P(60, 50, 50) : d == Decoration.IceRock ? P(170, 206, 230) : P(130, 128, 124);
                    c.GroundShadow(8, big ? 4 : 3);
                    c.Blob(8, big ? 3 : 2, big ? 4 : 2 + v % 2, big ? 3 : 2, g, Rgba.Shift(g, 40), Rgba.Shift(g, -26), Rgba.Shift(g, -44));
                    if (d == Decoration.EmberRock) { c.Set(7, 2, P(255, 140, 30)); c.Set(8, 3, P(255, 90, 20)); c.Set(9, 2, P(255, 170, 60)); }
                    break;
                }
                case Decoration.Reeds:
                {
                    uint g = P(110, 140, 70), tip = P(120, 82, 46);
                    for (int i = 0; i < 4; i++)
                    {
                        int x = 5 + i * 2 + (v % 2), hgt = 3 + (i + v) % 3;
                        for (int y = 0; y < hgt; y++) c.Set(x, y, y == hgt - 1 ? tip : g);
                    }
                    break;
                }
                case Decoration.Mushroom:
                {
                    uint cap = v == 1 ? P(200, 150, 90) : P(214, 50, 50);
                    c.Rect(8, 1, 1, 2, P(236, 228, 210));
                    c.Rect(7, 3, 3, 1, cap); c.Set(8, 4, cap); c.Set(7, 3, Rgba.Shift(cap, 30));
                    if (v != 1) c.Set(9, 3, P(250, 250, 250));
                    break;
                }
                case Decoration.GiantMushroom:
                {
                    uint cap = v == 0 ? P(150, 70, 180) : v == 1 ? P(200, 60, 70) : P(90, 120, 200);
                    c.GroundShadow(8, 4);
                    c.Rect(7, 1, 2, 6, P(232, 222, 196)); c.Set(8, 2, P(200, 190, 170));
                    c.Blob(8, 9, 5, 3, cap, Rgba.Shift(cap, 40), Rgba.Shift(cap, -30), Rgba.Shift(cap, -50));
                    c.Set(6, 10, P(250, 250, 250)); c.Set(10, 9, P(250, 250, 250)); c.Set(8, 11, P(250, 250, 250));
                    break;
                }
                case Decoration.Crystal:
                {
                    uint g = v == 0 ? P(110, 220, 240) : v == 1 ? P(200, 130, 250) : P(120, 250, 190);
                    uint lt = Rgba.Shift(g, 50), dk = Rgba.Shift(g, -60);
                    c.GroundShadow(8, 3);
                    int[] xs = { 6, 8, 10 }; int[] hs = { 4, 7, 5 };
                    for (int i = 0; i < 3; i++)
                        for (int y = 1; y <= hs[i]; y++)
                        {
                            c.Set(xs[i], y, y == hs[i] ? lt : g);
                            if (y < hs[i] - 1) c.Set(xs[i] + 1, y, dk);
                        }
                    break;
                }
                case Decoration.GlowTree:
                {
                    uint g = v == 1 ? P(70, 190, 170) : P(60, 160, 190);
                    c.GroundShadow(8, 4);
                    c.Rect(7, 1, 2, 4, P(70, 50, 90));
                    c.Blob(8, 9, 4, 4, g, Rgba.Shift(g, 40), Rgba.Shift(g, -30), Rgba.Shift(g, -50));
                    c.Set(6, 10, P(250, 240, 160)); c.Set(10, 8, P(240, 150, 240)); c.Set(8, 12, P(250, 250, 220));
                    break;
                }
                case Decoration.SwampTree:
                {
                    uint g = P(84, 104, 56);
                    c.GroundShadow(8, 4);
                    c.Rect(8, 1, 1, 6, P(70, 58, 44));
                    c.Blob(8, 9, 5, 3, g, Rgba.Shift(g, 24), Rgba.Shift(g, -24), Rgba.Shift(g, -36));
                    c.Set(4, 7, g); c.Set(4, 6, g); c.Set(12, 7, g); c.Set(12, 6, g); c.Set(12, 5, Rgba.Shift(g, -20)); // drooping moss
                    break;
                }
                case Decoration.AcaciaTree:
                {
                    uint g = P(110, 146, 56);
                    c.GroundShadow(8, 4);
                    c.Rect(8, 1, 1, 6, trunk); c.Set(7, 6, trunk); c.Set(9, 7, trunk);
                    c.Blob(8, 9, 6, 1 + (v == 2 ? 1 : 0), g, Rgba.Shift(g, 30), Rgba.Shift(g, -24), Rgba.Shift(g, -40));
                    break;
                }
            }
        }
    }
}
