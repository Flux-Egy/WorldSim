using System.Collections.Generic;

namespace WorldSim.Presentation.Input
{
    /// <summary>One finger that is currently down, in screen pixels.</summary>
    public struct TouchSample
    {
        public int Id;
        public float X;
        public float Y;

        public TouchSample(int id, float x, float y) { Id = id; X = x; Y = y; }
    }

    /// <summary>
    /// Touch gesture state machine (§8.1, §8.2). Pure C#, no Unity types, so it is unit-tested
    /// in plain .NET (Tools/CoreTests). Feed it every frame with the fingers that are down;
    /// read the outputs, which are valid until the next <see cref="Update"/>.
    ///
    /// Rules that satisfy §8.2:
    ///  - Two fingers enter Pinching. While pinching, single-finger pan never happens.
    ///  - When a pinch loses a finger, the recognizer waits until ALL fingers are up
    ///    (<see cref="State.WaitAllUp"/>), so the remaining finger cannot jump into a pan,
    ///    whatever order the fingers are released in.
    ///  - Zero fingers always returns to Idle, so no release order can leave it stuck.
    /// </summary>
    public sealed class GestureRecognizer
    {
        public enum State { Idle, Pressed, Panning, Pinching, WaitAllUp }

        // Tunables (pixels are physical screen pixels; scaled by DPI via PixelScale).
        public float PixelScale = 1f;
        public float TapMaxSeconds = 0.30f;
        public float TapSlopPx = 18f;
        public float DoubleTapSeconds = 0.35f;
        public float DoubleTapSlopPx = 60f;
        public float LongPressSeconds = 0.55f;

        // ---- Outputs (reset every Update) ----
        public float PanDx, PanDy;
        public float PinchScale = 1f;
        public float PinchCenterX, PinchCenterY;
        public bool Tap, DoubleTap, LongPress;
        public float GestureX, GestureY;

        public State Current { get; private set; } = State.Idle;

        /// <summary>True while exactly one finger is down and no pinch is involved (paint strokes).</summary>
        public bool IsSingleFingerDown => Current == State.Pressed || Current == State.Panning;
        /// <summary>Current position of that finger (valid while <see cref="IsSingleFingerDown"/>).</summary>
        public float PrimaryX => _lastX;
        public float PrimaryY => _lastY;

        int _primaryId, _secondaryId;
        float _startX, _startY, _startTime, _lastX, _lastY;
        float _lastPinchDistance, _lastCenterX, _lastCenterY;
        bool _longPressFired;
        float _lastTapTime = -10f, _lastTapX, _lastTapY;

        public void Update(float time, IReadOnlyList<TouchSample> down)
        {
            PanDx = PanDy = 0f;
            PinchScale = 1f;
            Tap = DoubleTap = LongPress = false;

            int n = down.Count;
            switch (Current)
            {
                case State.Idle:
                    if (n == 1) BeginPress(time, down[0]);
                    else if (n >= 2) BeginPinch(down);
                    break;

                case State.Pressed:
                    if (n == 0) { ReleasePress(time); Current = State.Idle; break; }
                    if (n >= 2) { BeginPinch(down); break; }
                    if (down[0].Id != _primaryId) { BeginPress(time, down[0]); break; }
                    var t = down[0];
                    if (Dist(t.X, t.Y, _startX, _startY) > TapSlopPx * PixelScale)
                    {
                        Current = State.Panning;
                        PanDx = t.X - _lastX; PanDy = t.Y - _lastY;
                    }
                    else if (!_longPressFired && time - _startTime >= LongPressSeconds)
                    {
                        _longPressFired = true;
                        LongPress = true; GestureX = t.X; GestureY = t.Y;
                        Current = State.WaitAllUp; // releasing after a long press must not tap
                    }
                    _lastX = t.X; _lastY = t.Y;
                    break;

                case State.Panning:
                    if (n == 0) { Current = State.Idle; break; }
                    if (n >= 2) { BeginPinch(down); break; }
                    if (down[0].Id != _primaryId) { Current = State.WaitAllUp; break; }
                    PanDx = down[0].X - _lastX; PanDy = down[0].Y - _lastY;
                    _lastX = down[0].X; _lastY = down[0].Y;
                    break;

                case State.Pinching:
                    if (n == 0) { Current = State.Idle; break; }
                    if (!TryFind(down, _primaryId, out var a) || !TryFind(down, _secondaryId, out var b))
                    {
                        Current = State.WaitAllUp; // lost a pinch finger: no pan until all are up
                        break;
                    }
                    float d = Dist(a.X, a.Y, b.X, b.Y);
                    float cx = (a.X + b.X) * 0.5f, cy = (a.Y + b.Y) * 0.5f;
                    if (_lastPinchDistance > 1f && d > 1f) PinchScale = d / _lastPinchDistance;
                    PinchCenterX = cx; PinchCenterY = cy;
                    PanDx = cx - _lastCenterX; PanDy = cy - _lastCenterY; // two-finger drag pans
                    _lastPinchDistance = d; _lastCenterX = cx; _lastCenterY = cy;
                    break;

                case State.WaitAllUp:
                    if (n == 0) Current = State.Idle;
                    break;
            }
        }

        void BeginPress(float time, TouchSample t)
        {
            Current = State.Pressed;
            _primaryId = t.Id;
            _startX = _lastX = t.X; _startY = _lastY = t.Y;
            _startTime = time;
            _longPressFired = false;
        }

        void ReleasePress(float time)
        {
            if (time - _startTime > TapMaxSeconds) return;
            GestureX = _lastX; GestureY = _lastY;
            bool isDouble = time - _lastTapTime <= DoubleTapSeconds &&
                            Dist(_lastX, _lastY, _lastTapX, _lastTapY) <= DoubleTapSlopPx * PixelScale;
            if (isDouble)
            {
                DoubleTap = true;
                _lastTapTime = -10f; // a third tap starts a new sequence
            }
            else
            {
                Tap = true;
                _lastTapTime = time; _lastTapX = _lastX; _lastTapY = _lastY;
            }
        }

        void BeginPinch(IReadOnlyList<TouchSample> down)
        {
            Current = State.Pinching;
            _primaryId = down[0].Id;
            _secondaryId = down[1].Id;
            _lastPinchDistance = Dist(down[0].X, down[0].Y, down[1].X, down[1].Y);
            _lastCenterX = (down[0].X + down[1].X) * 0.5f;
            _lastCenterY = (down[0].Y + down[1].Y) * 0.5f;
            PinchCenterX = _lastCenterX; PinchCenterY = _lastCenterY;
        }

        static bool TryFind(IReadOnlyList<TouchSample> down, int id, out TouchSample t)
        {
            for (int i = 0; i < down.Count; i++)
                if (down[i].Id == id) { t = down[i]; return true; }
            t = default;
            return false;
        }

        static float Dist(float ax, float ay, float bx, float by)
        {
            float dx = ax - bx, dy = ay - by;
            return (float)System.Math.Sqrt(dx * dx + dy * dy);
        }
    }
}
