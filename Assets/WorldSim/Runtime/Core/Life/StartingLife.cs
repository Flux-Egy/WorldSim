using System.Collections.Generic;

namespace WorldSim.Core.Life
{
    /// <summary>
    /// Who lives in a new world before the player does anything (Playable Alpha step 2: "the world starts with life").
    /// Deterministic from the seed: one small band of each people on land that suits it, far apart from the others,
    /// plus herds of animals, a few predators, birds and fish. Each entry is a spawn request for the life simulation.
    /// </summary>
    public static class StartingLife
    {
        public struct Spawn { public SpeciesId Species; public int X, Y; }

        public const int PeopleBand = 6;
        public const int MinBandDistance = 24;

        public static List<Spawn> Plan(TileData[] tiles, int w, int h, ulong worldSeed)
        {
            var list = new List<Spawn>();
            var rng = Pcg32.ForKey(new WorldSeed(worldSeed).Derive(SeedStream.Agents), 0x5747A27);
            float area = w * h / (256f * 256f);                      // counts scale with the map

            // Peoples, each on its preferred land, far from the other bands.
            var bands = new List<(int x, int y)>();
            Band(SpeciesId.Human, b => b == Biome.Meadow || b == Biome.FlowerField || b == Biome.Forest);
            Band(SpeciesId.Elf, b => b == Biome.Forest || b == Biome.BirchForest || b == Biome.Glimmerwood || b == Biome.Meadow);
            Band(SpeciesId.Orc, b => b == Biome.Steppe || b == Biome.Savanna || b == Biome.Badlands || b == Biome.Meadow);
            Band(SpeciesId.Dwarf, b => b == Biome.RockyHighland || b == Biome.Tundra || b == Biome.PineTaiga || b == Biome.Meadow);

            // Animals in small herds.
            Herds(SpeciesId.Sheep, 4, 3, Grassy);
            Herds(SpeciesId.Cow, 3, 2, Grassy);
            Herds(SpeciesId.Rabbit, 5, 3, Grassy);
            Herds(SpeciesId.Deer, 4, 3, b => b == Biome.Forest || b == Biome.BirchForest || b == Biome.Meadow || b == Biome.PineTaiga);
            Herds(SpeciesId.Wolf, 2, 2, b => b == Biome.Forest || b == Biome.PineTaiga || b == Biome.Tundra);
            Herds(SpeciesId.Fox, 3, 1, Grassy);
            Herds(SpeciesId.Bear, 2, 1, b => b == Biome.Forest || b == Biome.PineTaiga || b == Biome.BirchForest);
            Herds(SpeciesId.Bird, 5, 3, b => !Biomes.IsWater(b) && b != Biome.Lava);
            Herds(SpeciesId.Fish, 8, 3, b => b == Biome.ShallowWater || b == Biome.CoralShallows);
            return list;

            void Band(SpeciesId s, System.Func<Biome, bool> land)
            {
                if (!Find(land, 400, out int cx, out int cy, true) && !Find(Grassy, 400, out cx, out cy, true)) return;
                bands.Add((cx, cy));
                for (int i = 0; i < PeopleBand; i++) list.Add(new Spawn { Species = s, X = cx + (i % 3) - 1, Y = cy + i / 3 });
            }

            void Herds(SpeciesId s, int herds, int size, System.Func<Biome, bool> land)
            {
                int n = (int)(herds * area + 0.5f);
                for (int k = 0; k < n; k++)
                {
                    if (!Find(land, 200, out int cx, out int cy, false)) return;
                    for (int i = 0; i < size; i++)
                    {
                        int x = cx + (int)rng.NextUInt(5) - 2, y = cy + (int)rng.NextUInt(5) - 2;
                        if (x < 0 || y < 0 || x >= w || y >= h || !land(tiles[y * w + x].Biome)) { x = cx; y = cy; }
                        list.Add(new Spawn { Species = s, X = x, Y = y });
                    }
                }
            }

            bool Find(System.Func<Biome, bool> land, int tries, out int fx, out int fy, bool farFromBands)
            {
                for (int t = 0; t < tries; t++)
                {
                    int x = 4 + (int)rng.NextUInt((uint)(w - 8)), y = 4 + (int)rng.NextUInt((uint)(h - 8));
                    if (!land(tiles[y * w + x].Biome)) continue;
                    if (farFromBands)
                    {
                        bool ok = true;
                        foreach (var b in bands)
                            if ((b.x - x) * (b.x - x) + (b.y - y) * (b.y - y) < MinBandDistance * MinBandDistance) { ok = false; break; }
                        if (!ok) continue;
                    }
                    fx = x; fy = y;
                    return true;
                }
                fx = fy = 0;
                return false;
            }
        }

        static bool Grassy(Biome b) =>
            b == Biome.Meadow || b == Biome.FlowerField || b == Biome.Savanna || b == Biome.Steppe || b == Biome.Forest || b == Biome.BirchForest;
    }
}
