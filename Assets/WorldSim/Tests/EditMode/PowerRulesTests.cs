using NUnit.Framework;
using WorldSim.Core;
using WorldSim.Core.Powers;

namespace WorldSim.Tests
{
    public class PowerRulesTests
    {
        [Test]
        public void Zones_DamageFallsWithDistance()
        {
            Assert.AreEqual(0, PowerRules.ZoneOf(PowerKind.Meteor, 10));
            Assert.AreEqual(1, PowerRules.ZoneOf(PowerKind.Meteor, 50));
            Assert.AreEqual(2, PowerRules.ZoneOf(PowerKind.Meteor, 100));
            Assert.AreEqual(3, PowerRules.ZoneOf(PowerKind.Meteor, 180));
            Assert.AreEqual(-1, PowerRules.ZoneOf(PowerKind.Meteor, 250));
            Assert.AreEqual(4, PowerRules.ZoneOf(PowerKind.Nuke, 300));
            int last = 101;
            for (int z = 0; z <= 4; z++) { int d = PowerRules.DamagePercent(PowerKind.Bomb, z); Assert.Less(d, last); last = d; }
            Assert.AreEqual(0, PowerRules.DamagePercent(PowerKind.Bomb, -1));
            Assert.AreEqual(2, PowerRules.ZoneOf(PowerKind.Wildfire, 30), "wildfire burns");
            Assert.AreEqual(10, PowerRules.DistTenths(1 << 16, 0));
            Assert.AreEqual(50, PowerRules.DistTenths(3 << 16, 4 << 16));
        }

        [Test]
        public void Strikes_LeaveCraterScorchAndFallout()
        {
            const int N = 96;
            var p = WorldGenParams.Create(new WorldSeed(0x5EED), N, N);
            var tiles = new TileData[N * N];
            for (int i = 0; i < tiles.Length; i++)
                tiles[i] = new TileData { BiomeId = (byte)Biome.Forest, Height = 150, Moisture = 150, Temperature = 130, DecorationId = (byte)Decoration.OakTree };
            var grid = new ArrayGrid { Tiles = tiles };
            foreach (var e in PowerRules.TerrainEdits(PowerKind.Nuke, 48, 48)) WorldEditor.Apply(ref grid, p, e);
            Assert.AreEqual((byte)Biome.Volcanic, tiles[48 * N + 48].BiomeId, "crater centre");
            Assert.Less(tiles[48 * N + 48].Height, 150, "pushed down");
            Assert.AreEqual(0, tiles[48 * N + 48].DecorationId);
            var ring = tiles[48 * N + 48 + 13];
            Assert.That(ring.DecorationId == (byte)Decoration.CharredStump || ring.DecorationId == (byte)Decoration.DeadTree || ring.DecorationId == 0);
            Assert.AreEqual((byte)Biome.IrradiatedWaste, tiles[48 * N + 48 + 24].BiomeId, "fallout ring");
            Assert.AreEqual((byte)Biome.Forest, tiles[2 * N + 2].BiomeId, "far away untouched");
        }

        [Test]
        public void Rain_GreensDryLand_Forest_PlantsTrees()
        {
            const int N = 40;
            var p = WorldGenParams.Create(new WorldSeed(1), N, N);
            var tiles = new TileData[N * N];
            for (int i = 0; i < tiles.Length; i++)
                tiles[i] = new TileData { BiomeId = (byte)Biome.DesertDunes, Height = 140, Moisture = 70, Temperature = 200 };
            var grid = new ArrayGrid { Tiles = tiles };
            foreach (var e in PowerRules.TerrainEdits(PowerKind.Rain, 20, 20)) WorldEditor.Apply(ref grid, p, e);
            Assert.Greater(tiles[20 * N + 20].Moisture, 70);
            Assert.AreNotEqual((byte)Biome.DesertDunes, tiles[20 * N + 20].BiomeId, "rain greens the desert centre");
            int trees = 0;
            foreach (var e in PowerRules.TerrainEdits(PowerKind.Forest, 20, 20)) WorldEditor.Apply(ref grid, p, e);
            foreach (var t in tiles) if (TileData.IsTree(t.Decoration)) trees++;
            Assert.Greater(trees, 20);
        }

        struct ArrayGrid : ITileGrid
        {
            public TileData[] Tiles;
            public TileData Get(int i) => Tiles[i];
            public void Set(int i, TileData t) => Tiles[i] = t;
        }
    }
}
