using WorldSim.Core.Life;

namespace WorldSim.Render
{
    /// <summary>
    /// Procedural creature sprites (Beta B3): 12x12 cells, facing right, origin bottom-left,
    /// anchored at the bottom centre (x = 6), designed at 8 pixels per tile. Two animation frames
    /// per species (legs, wings or tail). Peoples get race features (elf ears, orc tusks, dwarf
    /// beard); the tunic colour is a placeholder until kingdoms colour their people (B4).
    /// </summary>
    public static class CreatureSprites
    {
        public const int Cell = 12;
        public const int Frames = 2;
        public const int CellPixels = Cell * Cell;

        /// <summary>Index of a species in the atlas (order of <see cref="SpeciesTable.All"/>).</summary>
        public static int SlotOf(SpeciesId id)
        {
            for (int i = 0; i < SpeciesTable.All.Length; i++) if (SpeciesTable.All[i] == id) return i;
            return 0;
        }

        public static int CellIndex(SpeciesId id, int frame) => SlotOf(id) * Frames + frame;

        public static uint[] Build()
        {
            var atlas = new uint[SpeciesTable.All.Length * Frames * CellPixels];
            for (int s = 0; s < SpeciesTable.All.Length; s++)
                for (int f = 0; f < Frames; f++)
                    Draw(atlas, (s * Frames + f) * CellPixels, SpeciesTable.Get(SpeciesTable.All[s]), f);
            return atlas;
        }

        static uint P(int r, int g, int b) => Rgba.Pack(r, g, b);

        static void Draw(uint[] a, int off, SpeciesDef d, int f)
        {
            void S(int x, int y, uint c) { if (x >= 0 && y >= 0 && x < Cell && y < Cell) a[off + y * Cell + x] = c; }
            void R(int x0, int y0, int w, int h, uint c) { for (int y = y0; y < y0 + h; y++) for (int x = x0; x < x0 + w; x++) S(x, y, c); }
            uint shadow = SpriteLibrary.Shadow;
            uint body = d.ColorA, detail = d.ColorB, dark = Rgba.Shift(d.ColorA, -50), eye = P(20, 20, 24);

            switch (d.Id)
            {
                case SpeciesId.Human:
                case SpeciesId.Elf:
                case SpeciesId.Orc:
                case SpeciesId.Dwarf:
                {
                    bool dwarf = d.Id == SpeciesId.Dwarf;
                    int top = dwarf ? 7 : 9;                       // head top row
                    uint hair = d.Id == SpeciesId.Elf ? P(236, 210, 120) : d.Id == SpeciesId.Orc ? P(40, 40, 36) :
                                dwarf ? P(190, 100, 40) : P(110, 70, 40);
                    R(4, 0, 4, 1, shadow);
                    // legs (alternate per frame)
                    uint legs = P(70, 60, 56);
                    if (f == 0) { S(5, 1, legs); S(6, 1, legs); } else { S(4, 1, legs); S(7, 1, legs); }
                    R(4, 2, 4, dwarf ? 2 : 3, detail);                     // tunic
                    S(3, dwarf ? 3 : 4, body); S(8, dwarf ? 3 : 4, body);   // hands
                    int hy = dwarf ? 4 : 5;
                    R(4, hy, 4, 3, body);                                  // head
                    S(7, hy + 1, eye);
                    R(4, top - 1, 4, 1, hair); S(4, top - 2, hair);       // hair
                    if (d.Id == SpeciesId.Elf) { S(3, hy + 2, body); S(2, hy + 3, body); }        // pointed ear
                    if (d.Id == SpeciesId.Orc) S(7, hy, P(240, 240, 230));                         // tusk
                    if (dwarf) { R(5, hy - 1, 3, 2, hair); S(6, hy - 2, hair); }                 // beard
                    break;
                }
                case SpeciesId.Rabbit:
                    R(3, 0, 6, 1, shadow);
                    R(4, 1, 4, 2, body); R(7, 2, 2, 2, body); S(8, 3, eye);
                    S(7, 4, body); S(8, 4, body); S(7, 5, f == 0 ? body : detail);     // ears
                    S(3, 2, detail);                                                    // tail
                    if (f == 1) { S(4, 1, dark); S(7, 1, dark); }
                    break;
                case SpeciesId.Sheep:
                case SpeciesId.Cow:
                {
                    bool cow = d.Id == SpeciesId.Cow;
                    R(2, 0, 8, 1, shadow);
                    uint leg = cow ? P(60, 50, 50) : P(50, 50, 50);
                    if (f == 0) { S(3, 1, leg); S(7, 1, leg); } else { S(4, 1, leg); S(6, 1, leg); }
                    R(2, 2, 7, 3, body);                                  // body
                    if (cow) { S(4, 3, detail); S(5, 4, detail); S(3, 2, detail); }
                    else { S(2, 4, Rgba.Shift(body, -20)); S(5, 4, Rgba.Shift(body, -20)); }
                    R(8, 3, 2, 3, cow ? body : detail); S(9, 4, eye);    // head
                    if (cow) { S(8, 6, P(230, 220, 200)); S(9, 6, P(230, 220, 200)); }
                    break;
                }
                case SpeciesId.Deer:
                    R(2, 0, 8, 1, shadow);
                    if (f == 0) { S(3, 1, dark); S(3, 2, dark); S(7, 1, dark); S(7, 2, dark); }
                    else { S(4, 1, dark); S(4, 2, dark); S(6, 1, dark); S(6, 2, dark); }
                    R(3, 3, 5, 2, body); S(2, 4, detail);
                    R(8, 4, 1, 2, body); R(8, 6, 2, 2, body); S(9, 7, eye);
                    S(8, 8, P(150, 120, 80)); S(7, 9, P(150, 120, 80)); S(9, 9, P(150, 120, 80)); // antlers
                    break;
                case SpeciesId.Wolf:
                case SpeciesId.Fox:
                case SpeciesId.Bear:
                {
                    bool bear = d.Id == SpeciesId.Bear;
                    R(1, 0, 10, 1, shadow);
                    if (f == 0) { S(3, 1, dark); S(8, 1, dark); } else { S(4, 1, dark); S(7, 1, dark); }
                    R(2, 2, bear ? 7 : 6, bear ? 4 : 2, body);
                    int hx = bear ? 8 : 7;
                    R(hx, bear ? 4 : 3, 3, 2, body); S(hx + 2, bear ? 5 : 4, eye);
                    S(hx, bear ? 6 : 5, body);                                         // ear
                    if (!bear) { S(1, 3, body); S(0, 4, d.Id == SpeciesId.Fox ? detail : body); } // tail
                    if (d.Id == SpeciesId.Fox) S(hx + 2, 3, detail);
                    break;
                }
                case SpeciesId.Bird:
                    R(4, 0, 4, 1, shadow);
                    R(4, 4, 4, 2, body); S(8, 5, detail); S(7, 5, eye);                 // body, beak
                    if (f == 0) { R(4, 6, 3, 1, Rgba.Shift(body, 30)); S(3, 7, Rgba.Shift(body, 30)); }
                    else { R(4, 3, 3, 1, Rgba.Shift(body, 30)); S(3, 2, Rgba.Shift(body, 30)); }
                    break;
                case SpeciesId.Fish:
                    R(3, 2, 5, 2, body); S(4, 4, body); S(5, 4, body); S(4, 1, body); S(5, 1, body);
                    S(7, 3, eye); S(3, 3, detail);
                    if (f == 0) { S(2, 3, dark); S(1, 4, dark); S(1, 2, dark); } else { S(2, 2, dark); S(1, 3, dark); S(1, 1, dark); }
                    break;
            }
            // 1-px dark outline around opaque pixels for readability at any zoom.
            uint ol = P(28, 24, 30);
            var copy = new uint[CellPixels];
            for (int i = 0; i < CellPixels; i++) copy[i] = a[off + i];
            for (int y = 0; y < Cell; y++)
                for (int x = 0; x < Cell; x++)
                {
                    if (copy[y * Cell + x] != 0) continue;
                    bool near = false;
                    for (int k = 0; k < 4 && !near; k++)
                    {
                        int nx = x + (k == 0 ? 1 : k == 1 ? -1 : 0), ny = y + (k == 2 ? 1 : k == 3 ? -1 : 0);
                        if (nx < 0 || ny < 0 || nx >= Cell || ny >= Cell) continue;
                        uint c = copy[ny * Cell + nx];
                        if (c != 0 && Rgba.A(c) == 255) near = true;
                    }
                    if (near) a[off + y * Cell + x] = ol;
                }
        }
    }
}
