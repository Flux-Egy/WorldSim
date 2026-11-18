using System.Collections.Generic;
using NUnit.Framework;
using WorldSim.Presentation.Input;
using State = WorldSim.Presentation.Input.GestureRecognizer.State;

namespace WorldSim.Tests
{
    /// <summary>Stage 3 acceptance (§8.2) for the touch state machine, without a device.</summary>
    public class GestureRecognizerTests
    {
        GestureRecognizer _g;
        float _t;

        [SetUp] public void SetUp() { _g = new GestureRecognizer(); _t = 0f; }

        void Frame(float dt, params TouchSample[] down) { _t += dt; _g.Update(_t, new List<TouchSample>(down)); }
        static TouchSample F(int id, float x, float y) => new TouchSample(id, x, y);

        [Test]
        public void QuickTap_FiresTap()
        {
            Frame(0.016f, F(1, 100, 100));
            Frame(0.05f, F(1, 102, 101));
            Frame(0.05f);
            Assert.IsTrue(_g.Tap);
            Assert.AreEqual(State.Idle, _g.Current);
        }

        [Test]
        public void TwoQuickTaps_FireDoubleTap()
        {
            Frame(0.016f, F(1, 100, 100)); Frame(0.05f);
            Assert.IsTrue(_g.Tap);
            Frame(0.1f, F(2, 105, 98)); Frame(0.05f);
            Assert.IsTrue(_g.DoubleTap);
            Assert.IsFalse(_g.Tap);
        }

        [Test]
        public void HoldStill_FiresLongPress_AndReleaseDoesNotTap()
        {
            Frame(0.016f, F(1, 50, 50));
            for (int i = 0; i < 40; i++) Frame(0.016f, F(1, 51, 50));
            Assert.AreEqual(State.WaitAllUp, _g.Current);
            Frame(0.016f);
            Assert.IsFalse(_g.Tap);
            Assert.AreEqual(State.Idle, _g.Current);
        }

        [Test]
        public void Drag_Pans_WithoutJump()
        {
            Frame(0.016f, F(1, 0, 0));
            Frame(0.016f, F(1, 30, 0));   // passes slop: starts panning
            Assert.AreEqual(State.Panning, _g.Current);
            Frame(0.016f, F(1, 40, 5));
            Assert.AreEqual(10f, _g.PanDx, 1e-4);
            Assert.AreEqual(5f, _g.PanDy, 1e-4);
        }

        [Test]
        public void Pinch_DoesNotPan_AfterFirstFingerLifts()
        {
            Frame(0.016f, F(1, 100, 100), F(2, 200, 100));
            Frame(0.016f, F(1, 90, 100), F(2, 210, 100));
            Assert.AreEqual(State.Pinching, _g.Current);
            Assert.Greater(_g.PinchScale, 1f);
            Frame(0.016f, F(2, 210, 100));          // finger 1 lifts first
            Frame(0.016f, F(2, 400, 300));          // remaining finger moves a lot
            Assert.AreEqual(0f, _g.PanDx);
            Assert.AreEqual(0f, _g.PanDy);
            Frame(0.016f);
            Assert.AreEqual(State.Idle, _g.Current);
        }

        [Test]
        public void Pinch_DoesNotPan_AfterSecondFingerLifts()
        {
            Frame(0.016f, F(1, 100, 100), F(2, 200, 100));
            Frame(0.016f, F(1, 100, 100));          // finger 2 lifts first
            Frame(0.016f, F(1, 300, 300));
            Assert.AreEqual(0f, _g.PanDx);
            Assert.AreEqual(State.WaitAllUp, _g.Current);
            Frame(0.016f);
            Assert.AreEqual(State.Idle, _g.Current);
        }

        [Test]
        public void BothFingersLiftSameFrame_ReturnsToIdle()
        {
            Frame(0.016f, F(1, 100, 100), F(2, 200, 100));
            Frame(0.016f);
            Assert.AreEqual(State.Idle, _g.Current);
            Frame(0.016f, F(3, 10, 10));            // next gesture works normally
            Assert.AreEqual(State.Pressed, _g.Current);
        }

        [Test]
        public void PanThenSecondFinger_SwitchesToPinch()
        {
            Frame(0.016f, F(1, 0, 0));
            Frame(0.016f, F(1, 50, 0));
            Assert.AreEqual(State.Panning, _g.Current);
            Frame(0.016f, F(1, 50, 0), F(2, 150, 0));
            Assert.AreEqual(State.Pinching, _g.Current);
        }
    }
}
