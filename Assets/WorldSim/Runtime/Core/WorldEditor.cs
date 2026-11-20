namespace WorldSim.Core
{
    /// <summary>Terrain tools (Beta B2). Values are stored in edit commands: only append.</summary>
    public enum TerrainTool : byte
    {
        None = 0,
        Raise = 1,
        Lower = 2,
        PaintBiome = 3,   // uses TerrainEdit.Biome
        PlantTrees = 4,
        ClearDecorations = 5,
        Flatten = 6,
    }

    /// <summary>One brush dab. Blittable: travels through ECS buffers and, later, save files.</summary>
    public struct TerrainEdit
    {
        public TerrainTool Tool;
        public Biome Biome;
        public int X, Y;          // centre tile
        public int Radius;        // tiles; 0 = single tile
    }

    /// <summary>Inclusive tile rectangle touched by edits (for partial repaint).</summary>
    public struct TileRect
    {
        public int XMin, YMin, XMax, YMax;
        public bool IsEmpty => XMax < XMin || YMax < YMin;
        public static TileRect Empty => new TileRect { XMin = int.MaxValue, YMin = int.MaxValue, XMax = int.MinValue, YMax = int.MinValue };

        public void Include(int x0, int y0, int x1, int y1)
        {
            if (x0 < XMin) XMin = x0;
            if (y0 < YMin) YMin = y0;
            if (x1 > XMax) XMax = x1;
            if (y1 > YMax) YMax = y1;
        }
    }

    /// <summary>Mutable tile grid. Implemented over NativeArray in the simulation and arrays in tests.</summary>
    public interface ITileGrid
    {
        TileData Get(int index);
        void Set(int index, TileData tile);
    }

    /// <summary>
    /// Applies terrain brushes (Beta B2) deterministically: the same edits on the same world give
    /// the same tiles on every device. After a change the tile is made consistent again: biome
    /// follows height for raise/lower; decorations and resources are re-scattered with the world
    /// generator's own rules, keyed by position, so painted land looks like generated land.
    /// </summary>
    public static class WorldEditor
    {
        // Representative heights so a painted biome sits in its natural height band.
        public static byte NaturalHeight(Biome b)
        {
            switch (b)
            {
                case Biome.DeepWater: return 70;
                case Biome.ShallowWater: return 102;
                case Biome.Beach: return 115;
                case Biome.Mountain: return 212;
                case Biome.Snow: return 150;
                case Biome.Lava: return 140;
                case Biome.Swamp: return 124;
                case Biome.CoralShallows: return 108;
                case Biome.Glacier: return 245;
                case Biome.RockyHighland: return 186;
                case Biome.SaltFlats: return 125;
                default: return 145;
            }
        }

        public static bool IsWaterBiome(Biome b) => Biomes.IsWater(b);

        /// <summary>Applies one dab; returns the touched rectangle (empty if nothing changed).</summary>
        public static TileRect Apply<TG>(ref TG grid, in WorldGenParams p, TerrainEdit e) where TG : struct, ITileGrid
        {
            var touched = TileRect.Empty;
            int r = e.Radius < 0 ? 0 : e.Radius > 32 ? 32 : e.Radius;
            int r2 = r * r + r;                       // slightly rounder discs
            for (int y = e.Y - r; y <= e.Y + r; y++)
            {
                if (y < 0 || y >= p.Height) continue;
                for (int x = e.X - r; x <= e.X + r; x++)
                {
                    if (x < 0 || x >= p.Width) continue;
                    int dx = x - e.X, dy = y - e.Y, d2 = dx * dx + dy * dy;
                    if (d2 > r2) continue;
                    int i = y * p.Width + x;
                    TileData before = grid.Get(i);
                    TileData after = ApplyToTile(p, before, x, y, e, d2, r2);
                    if (!Same(before, after))
                    {
                        grid.Set(i, after);
                        touched.Include(x, y, x, y);
                    }
                }
            }
            return touched;
        }

        static TileData ApplyToTile(in WorldGenParams p, TileData t, int x, int y, TerrainEdit e, int d2, int r2)
        {
            // Strength falls off towards the brush edge (centre 100%, rim ~35%).
            int falloff = r2 == 0 ? 100 : 100 - d2 * 65 / (r2 == 0 ? 1 : r2);
            switch (e.Tool)
            {
                case TerrainTool.Raise:
                case TerrainTool.Lower:
                {
                    int step = 6 * falloff / 100 + 1;
                    int h = t.Height + (e.Tool == TerrainTool.Raise ? step : -step);
                    t.Height = (byte)(h < 0 ? 0 : h > 255 ? 255 : h);
                    Biome nb = WorldGenerator.Classify(t.Height, t.Moisture, t.Temperature, 0);
                    // Keep invented biomes on land when only the height moved a little.
                    Biome old = (Biome)t.BiomeId;
                    if ((Biomes.IsAnomaly(old) || old == Biome.Lava || old == Biome.Farmland || old == Biome.IrradiatedWaste) && !IsWaterBiome(nb) && nb != Biome.Mountain && nb != Biome.Snow && nb != Biome.Glacier)
                        nb = old;
                    return Refresh(p, t, x, y, nb, keepDecorationIfValid: true);
                }
                case TerrainTool.Flatten:
                {
                    int target = 145, h = t.Height + (target - t.Height) * falloff / 200;
                    t.Height = (byte)h;
                    return Refresh(p, t, x, y, WorldGenerator.Classify(t.Height, t.Moisture, t.Temperature, 0), true);
                }
                case TerrainTool.PaintBiome:
                {
                    if ((Biome)t.BiomeId == e.Biome) return t;
                    t.Height = NaturalHeight(e.Biome);
                    return Refresh(p, t, x, y, e.Biome, keepDecorationIfValid: false);
                }
                case TerrainTool.PlantTrees:
                {
                    Biome b = (Biome)t.BiomeId;
                    if (IsWaterBiome(b) || b == Biome.Lava) return t;
                    Decoration tree = TreeFor(b, t.Temperature, x, y, p);
                    if (tree == Decoration.None || t.DecorationId == (byte)tree) return t;
                    t.DecorationId = (byte)tree;
                    t.ResourceFlags = WorldGenerator.Resources(p, x, y, b, tree);
                    return t;
                }
                case TerrainTool.ClearDecorations:
                {
                    if (t.DecorationId == 0) return t;
                    t.DecorationId = 0;
                    t.ResourceFlags = WorldGenerator.Resources(p, x, y, (Biome)t.BiomeId, Decoration.None);
                    return t;
                }
            }
            return t;
        }

        /// <summary>Sets the biome and re-derives decoration and resources with the generator's rules.</summary>
        static TileData Refresh(in WorldGenParams p, TileData t, int x, int y, Biome b, bool keepDecorationIfValid)
        {
            bool biomeChanged = t.BiomeId != (byte)b;
            t.BiomeId = (byte)b;
            Decoration d = (Decoration)t.DecorationId;
            if (biomeChanged || !keepDecorationIfValid || IsWaterBiome(b) || b == Biome.Lava)
            {
                long px = (long)x << FixedNoise.FracBits, py = (long)y << FixedNoise.FracBits;
                d = WorldGenerator.ScatterDecoration(p, x, y, px, py, b, t.Temperature);
            }
            t.DecorationId = (byte)d;
            t.ResourceFlags = WorldGenerator.Resources(p, x, y, b, d);
            return t;
        }

        /// <summary>The tree (or tree-like plant) that naturally grows in a biome, deterministic by position.</summary>
        public static Decoration TreeFor(Biome b, byte temperature, int x, int y, in WorldGenParams p)
        {
            int pick = (int)(FixedNoise.LatticeHash(p.DecorationSeed ^ 0x5151515151515151UL, x, y) % 100);
            switch (b)
            {
                case Biome.PineTaiga: case Biome.Mountain: return temperature < 50 ? Decoration.SnowPine : Decoration.PineTree;
                case Biome.Tundra: case Biome.Snow: return Decoration.SnowPine;
                case Biome.BirchForest: return pick < 80 ? Decoration.BirchTree : Decoration.PineTree;
                case Biome.Jungle: return pick < 80 ? Decoration.JungleTree : Decoration.PalmTree;
                case Biome.Savanna: return Decoration.AcaciaTree;
                case Biome.DesertDunes: return pick < 70 ? Decoration.Cactus : Decoration.DeadTree;
                case Biome.Swamp: return Decoration.SwampTree;
                case Biome.Beach: return Decoration.PalmTree;
                case Biome.Glimmerwood: case Biome.CrystalCaves: return Decoration.GlowTree;
                case Biome.FungalGrove: return Decoration.GiantMushroom;
                case Biome.EmberWastes: case Biome.AshWaste: case Biome.Badlands: return Decoration.DeadTree;
                case Biome.RockyHighland: return Decoration.PineTree;
                case Biome.Glacier: case Biome.SaltFlats: case Biome.Volcanic: case Biome.IrradiatedWaste: return Decoration.None;
                default: return pick < 85 ? Decoration.OakTree : Decoration.BirchTree;
            }
        }

        static bool Same(TileData a, TileData b) =>
            a.BiomeId == b.BiomeId && a.Height == b.Height && a.Moisture == b.Moisture &&
            a.Temperature == b.Temperature && a.ResourceFlags == b.ResourceFlags && a.DecorationId == b.DecorationId;
    }
}
