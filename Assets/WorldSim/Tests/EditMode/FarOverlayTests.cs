using NUnit.Framework;
using WorldSim.Render;
using WorldSim.Render.Terrain;

namespace WorldSim.Tests
{
    /// <summary>Far-zoom overlay: kingdom markers take the kingdom's TEAM ramp, others keep their art; farms and roads draw.</summary>
    public class FarOverlayTests
    {
        /// <summary>One 4x4 marker: left half TEAM (step 3), right half plain red.</summary>
        sealed class FakeArt : IArtPixels
        {
            public bool TryFrame(string name, out int id) { id = name == "mk_army" ? 0 : -1; return id == 0; }
            public int Width(int id) => 4;
            public int Height(int id) => 4;
            public float PivotX(int id) => 0.5f;
            public float PivotY(int id) => 0.5f;
            public uint Pixel(int id, int x, int y) => Rgba.Pack(200, 0, 0);
            public bool Mask(int id, int x, int y, out int region, out int step) { region = x < 2 ? 1 : 0; step = 3; return x < 2; }
        }

        [Test]
        public void KingdomMarker_IsRecoloured_FarmsAndRoadsDraw()
        {
            const int W = 40, H = 40;
            var img = new uint[W * H];
            var o = new FarOverlay();
            var ramp = new[] { Rgba.Pack(0, 0, 10), Rgba.Pack(0, 0, 20), Rgba.Pack(0, 0, 30), Rgba.Pack(0, 0, 200), Rgba.Pack(0, 0, 250) };
            o.TeamRamps.Add(ramp);
            o.Markers.Add(new FarOverlay.Marker { Frame = "mk_army", CellX = 2, CellY = 2, Kingdom = 0 });
            o.Markers.Add(new FarOverlay.Marker { Frame = "mk_city", CellX = 6, CellY = 2, Kingdom = 0 });
            o.Markers.Add(new FarOverlay.Marker { Frame = "mk_missing", CellX = 5, CellY = 5, Kingdom = 0 });
            o.Farms.Add(new FarOverlay.Farm { CellX = 8, CellY = 8 });
            o.Roads.Add(new[] { 0, 9, 9, 9 });
            o.Draw(img, W, H, 4, new FakeArt());
            // marker centred on cell (2,2) at 4 px per cell -> pixel (10,10); 4x4 from (8,8)
            Assert.AreEqual(ramp[3], img[8 * W + 8], "TEAM pixel takes the kingdom ramp step");
            Assert.AreEqual(Rgba.Pack(200, 0, 0), img[8 * W + 11], "non-TEAM pixel keeps its colour");
            Assert.AreEqual(ramp[2], img[(2 * 4 + 2 - 1) * W + 6 * 4 + 2], "a settlement is drawn as houses with roofs in the kingdom colour");
            Assert.AreNotEqual(0u, img[32 * W + 32], "farm patch");
            Assert.AreNotEqual(0u, img[38 * W + 2], "road");
        }
    }
}
