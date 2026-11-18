namespace WorldSim.Render
{
    /// <summary>Toolbar icons. Persisted only as UI references, so the order may change freely.</summary>
    public enum Icon
    {
        Globe, Resize, Info, Mountain, People, Animal, Storm, Spark, Castle, Gear,
        Pause, Play, Fast, Brush, Eraser, Tree, Water, Clock,
        Count,
    }

    /// <summary>
    /// Procedural 16x16 pixel-art icons for the toolbar (original designs, drawn in code).
    /// Transparent background; a dark 1-px outline is added around every shape so icons stay
    /// readable on any button colour.
    /// </summary>
    public static class IconLibrary
    {
        public const int Size = 16;

        static uint P(int r, int g, int b) => Rgba.Pack(r, g, b);

        public static uint[] Build(Icon icon)
        {
            var px = new uint[Size * Size];
            void S(int x, int y, uint c) { if (x >= 0 && y >= 0 && x < Size && y < Size) px[y * Size + x] = c; }
            void R(int x0, int y0, int w, int h, uint c) { for (int y = y0; y < y0 + h; y++) for (int x = x0; x < x0 + w; x++) S(x, y, c); }
            void Circle(int cx, int cy, int r, uint c) { for (int y = -r; y <= r; y++) for (int x = -r; x <= r; x++) if (x * x + y * y <= r * r + r) S(cx + x, cy + y, c); }

            uint white = P(240, 240, 236), gold = P(244, 200, 70), green = P(86, 170, 70), dkGreen = P(50, 118, 52),
                 blue = P(70, 150, 230), dkBlue = P(40, 96, 180), grey = P(150, 150, 150), brown = P(130, 90, 56), red = P(220, 70, 60);

            switch (icon)
            {
                case Icon.Globe:
                    Circle(8, 8, 6, blue); R(4, 7, 4, 4, green); R(9, 4, 3, 3, green); R(10, 10, 2, 2, green); S(5, 11, dkGreen);
                    break;
                case Icon.Resize:
                    R(2, 2, 5, 1, white); R(2, 2, 1, 5, white); R(9, 13, 5, 1, white); R(13, 9, 1, 5, white);
                    for (int i = 3; i <= 12; i++) S(i, i, white);
                    break;
                case Icon.Info:
                    Circle(8, 8, 6, blue); R(7, 4, 2, 5, white); R(7, 10, 2, 2, white);
                    break;
                case Icon.Mountain:
                    for (int y = 2; y <= 12; y++) for (int x = 8 - (12 - y); x <= 8 + (12 - y); x++) S(x, y, x < 8 ? P(150, 140, 130) : P(110, 102, 96));
                    for (int y = 9; y <= 12; y++) for (int x = 8 - (12 - y); x <= 8 + (12 - y); x++) S(x, y, white);
                    R(1, 2, 14, 1, green);
                    break;
                case Icon.People:
                    Circle(5, 10, 2, P(240, 200, 160)); R(3, 3, 5, 5, red);
                    Circle(11, 10, 2, P(200, 150, 110)); R(9, 3, 5, 5, blue);
                    break;
                case Icon.Animal:
                    R(3, 5, 9, 4, P(230, 230, 230)); R(11, 7, 3, 4, P(230, 230, 230)); S(13, 9, P(30, 30, 30));
                    R(3, 2, 1, 3, P(90, 90, 90)); R(6, 2, 1, 3, P(90, 90, 90)); R(9, 2, 1, 3, P(90, 90, 90)); R(11, 2, 1, 3, P(90, 90, 90));
                    break;
                case Icon.Storm:
                    Circle(6, 11, 3, grey); Circle(10, 11, 3, grey); R(4, 9, 9, 3, grey);
                    S(9, 7, gold); S(8, 6, gold); S(8, 5, gold); S(7, 4, gold); S(8, 4, gold); S(7, 3, gold); S(6, 2, gold);
                    break;
                case Icon.Spark:
                    for (int i = 2; i <= 13; i++) { S(i, 8, gold); S(8, i, gold); }
                    for (int i = 5; i <= 11; i++) { S(i, i, P(255, 240, 160)); S(i, 16 - i, P(255, 240, 160)); }
                    Circle(8, 8, 1, white);
                    break;
                case Icon.Castle:
                    R(3, 2, 10, 8, grey); R(2, 9, 3, 4, grey); R(11, 9, 3, 4, grey); R(2, 12, 1, 2, grey); R(4, 12, 1, 2, grey);
                    R(11, 12, 1, 2, grey); R(13, 12, 1, 2, grey); R(7, 2, 2, 4, brown); R(8, 11, 1, 4, brown); R(9, 13, 3, 2, red);
                    break;
                case Icon.Gear:
                    Circle(8, 8, 5, grey); Circle(8, 8, 2, P(60, 60, 60));
                    R(7, 1, 2, 2, grey); R(7, 13, 2, 2, grey); R(1, 7, 2, 2, grey); R(13, 7, 2, 2, grey);
                    break;
                case Icon.Pause:
                    R(4, 3, 3, 10, white); R(9, 3, 3, 10, white);
                    break;
                case Icon.Play:
                    for (int x = 4; x <= 12; x++) { int h = 12 - x; R(x, 8 - h / 2 - 1, 1, h + (h > 0 ? 1 : 0) + 1, white); }
                    break;
                case Icon.Fast:
                    for (int x = 2; x <= 7; x++) { int h = 7 - x; R(x, 8 - h, 1, 2 * h + 1, white); }
                    for (int x = 8; x <= 13; x++) { int h = 13 - x; R(x, 8 - h, 1, 2 * h + 1, white); }
                    break;
                case Icon.Brush:
                    for (int i = 6; i <= 13; i++) { S(i, i, brown); S(i + 1, i, brown); }
                    R(2, 2, 4, 4, red); R(3, 3, 3, 3, P(250, 120, 100));
                    break;
                case Icon.Eraser:
                    for (int i = 0; i < 7; i++) R(3 + i, 4 + i, 5, 2, i < 3 ? P(240, 160, 180) : white);
                    break;
                case Icon.Tree:
                    R(7, 2, 2, 4, brown); Circle(8, 9, 4, green); Circle(7, 10, 2, P(120, 200, 90));
                    break;
                case Icon.Water:
                    for (int y = 3; y <= 13; y++) { int w = y < 9 ? (y - 3) / 2 + 1 : 4 - (y - 9) / 2; if (w < 1) w = 1; R(8 - w, 16 - y, 2 * w, 1, blue); }
                    S(6, 6, P(180, 220, 250)); S(6, 7, P(180, 220, 250));
                    break;
                case Icon.Clock:
                    Circle(8, 8, 6, white); R(8, 8, 1, 5, P(40, 40, 40)); R(8, 8, 4, 1, P(40, 40, 40));
                    break;
            }
            Outline(px);
            return px;
        }

        /// <summary>Adds a 1-px dark outline around every opaque shape.</summary>
        static void Outline(uint[] px)
        {
            uint ol = Rgba.Pack(24, 22, 30);
            var copy = (uint[])px.Clone();
            for (int y = 0; y < Size; y++)
                for (int x = 0; x < Size; x++)
                {
                    if (copy[y * Size + x] != 0) continue;
                    bool near = false;
                    for (int dy = -1; dy <= 1 && !near; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (nx >= 0 && ny >= 0 && nx < Size && ny < Size && copy[ny * Size + nx] != 0 && copy[ny * Size + nx] != ol) { near = true; break; }
                        }
                    if (near) px[y * Size + x] = ol;
                }
        }
    }
}
