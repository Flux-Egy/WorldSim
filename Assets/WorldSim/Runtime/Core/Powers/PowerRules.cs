using System.Collections.Generic;

namespace WorldSim.Core.Powers
{
    /// <summary>The player's powers and disasters (Playable Alpha; pack data: life_and_powers.json "powers").</summary>
    public enum PowerKind : byte
    {
        None = 0,
        Lightning = 1, Meteor = 2, Bomb = 3, Missile = 4, Nuke = 5, Wildfire = 6, Rain = 7, Quake = 8,
        Forest = 9, Bless = 10, Plague = 11, SpawnPeople = 12, SpawnAnimals = 13,
    }

    /// <summary>
    /// What a power does where it lands, deterministic and pure. Blast zones (radii in tiles, from interactions.json
    /// "blast_zones"): 0 fireball, 1 blast, 2 thermal, 3 shock, 4 fallout. A creature's damage depends on its zone
    /// (fireball and blast kill, thermal burns, shock hurts); the land gets craters, scorch and fallout.
    /// </summary>
    public static class PowerRules
    {
        /// <summary>Zone radii in tenths of a tile: fireball, blast, thermal, shock, fallout (0 = none).</summary>
        public static int[] Zones(PowerKind k)
        {
            switch (k)
            {
                case PowerKind.Lightning: return new[] { 5, 10, 15, 25, 0 };
                case PowerKind.Bomb: return new[] { 5, 20, 40, 70, 0 };          // aerial_bomb
                case PowerKind.Missile: return new[] { 10, 30, 50, 90, 0 };      // cruise_missile
                case PowerKind.Meteor: return new[] { 30, 70, 120, 200, 0 };     // meteor
                case PowerKind.Nuke: return new[] { 40, 90, 160, 260, 320 };     // tactical_nuke (fallout capped to the brush limit)
                case PowerKind.Wildfire: return new[] { 0, 0, 55, 0, 0 };        // burns, no blast
                case PowerKind.Quake: return new[] { 0, 0, 0, 120, 0 };          // shakes and hurts
                case PowerKind.Plague: return new[] { 0, 0, 0, 100, 0 };
                default: return new[] { 0, 0, 0, 0, 0 };
            }
        }

        /// <summary>Zone 0..4 for a distance in tenths of a tile, or -1 outside every zone.</summary>
        public static int ZoneOf(PowerKind k, int dist10)
        {
            int[] z = Zones(k);
            for (int i = 0; i < z.Length; i++) if (z[i] > 0 && dist10 <= z[i]) return i;
            return -1;
        }

        /// <summary>Percent of max health lost in a zone (fireball 100, blast 90, thermal 60, shock 25, fallout 15).</summary>
        public static int DamagePercent(PowerKind k, int zone)
        {
            if (zone < 0) return 0;
            if (k == PowerKind.Plague) return 35;
            if (k == PowerKind.Quake) return 20;
            switch (zone) { case 0: return 100; case 1: return 90; case 2: return 60; case 3: return 25; default: return 15; }
        }

        /// <summary>Creatures in these zones run away from the strike.</summary>
        public static bool Flees(int zone) => zone >= 2;

        /// <summary>Radius in tiles inside which a supportive power acts (bless heals, spawns place creatures).</summary>
        public static int SupportRadius(PowerKind k) =>
            k == PowerKind.Bless ? 8 : k == PowerKind.Forest ? 6 : k == PowerKind.Rain ? 10 : k == PowerKind.SpawnPeople || k == PowerKind.SpawnAnimals ? 2 : 0;

        /// <summary>The land changes a power leaves, applied in order (later ones win where they overlap).</summary>
        public static List<TerrainEdit> TerrainEdits(PowerKind k, int x, int y)
        {
            var list = new List<TerrainEdit>(3);
            int[] z = Zones(k);
            void Add(TerrainTool tool, int radiusTenths)
            {
                int r = (radiusTenths + 5) / 10;
                if (r >= 0 && radiusTenths > 0) list.Add(new TerrainEdit { Tool = tool, X = x, Y = y, Radius = r > 32 ? 32 : r });
            }
            switch (k)
            {
                case PowerKind.Nuke: Add(TerrainTool.Irradiate, z[4]); Add(TerrainTool.Scorch, z[2]); Add(TerrainTool.Crater, z[1]); break;
                case PowerKind.Meteor:
                case PowerKind.Missile:
                case PowerKind.Bomb: Add(TerrainTool.Scorch, z[2]); Add(TerrainTool.Crater, z[1]); break;
                case PowerKind.Lightning: Add(TerrainTool.Scorch, z[1]); break;
                case PowerKind.Wildfire: Add(TerrainTool.Scorch, z[2]); break;
                case PowerKind.Rain: Add(TerrainTool.Wet, 100); break;
                case PowerKind.Quake: Add(TerrainTool.Quake, z[3]); break;
                case PowerKind.Forest: Add(TerrainTool.PlantTrees, 60); break;
            }
            return list;
        }

        /// <summary>Integer distance in tenths of a tile between two Q16.16 positions.</summary>
        public static int DistTenths(long dxQ16, long dyQ16)
        {
            long d2 = (dxQ16 * dxQ16 + dyQ16 * dyQ16) >> 16;              // Q16 squared -> Q16
            long tenths2 = d2 * 100;                                      // still Q16
            long v = (long)System.Math.Sqrt(tenths2 / 65536.0);
            return v > int.MaxValue ? int.MaxValue : (int)v;
        }
    }
}
