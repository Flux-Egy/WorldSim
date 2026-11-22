using UnityEngine;

namespace WorldSim.Presentation
{
    /// <summary>
    /// Orthographic camera rig (§8.2): pan and zoom clamped to the world bounds, zoom anchored on
    /// the pinch centre, smoothed glide for double-tap centring. One world unit = one tile.
    /// </summary>
    public sealed class CameraRig
    {
        readonly Camera _cam;
        Vector2 _worldMin, _worldMax;
        float _minSize = 6f, _maxSize = 64f;
        Vector2? _glideTarget;

        public CameraRig(Camera cam)
        {
            _cam = cam;
            _cam.orthographic = true;
        }

        public float OrthoSize => _cam.orthographicSize;

        /// <summary>Sets the world rectangle and shows the whole map width (zoom limits follow).</summary>
        public void SetWorld(float width, float height)
        {
            _worldMin = Vector2.zero;
            _worldMax = new Vector2(width, height);
            float fitWidth = width * 0.5f / Mathf.Max(0.1f, _cam.aspect);
            float fitHeight = height * 0.5f;
            // Zoom out well past the whole map so the far and map layers are reachable (owner, Alpha step 2).
            _maxSize = Mathf.Max(fitWidth, fitHeight) * 4f;
            _minSize = Mathf.Max(5f, Screen.height / (2f * 48f));   // closest zoom ~48 screen px per tile
            _cam.orthographicSize = Mathf.Clamp(fitWidth, _minSize, _maxSize);
            _cam.transform.position = new Vector3(width * 0.5f, height * 0.5f, -10f);
            _glideTarget = null;
            Clamp();
        }

        /// <summary>Moves the view by a screen-space finger delta (content follows the finger).</summary>
        public void PanScreen(float dxPixels, float dyPixels)
        {
            float unitsPerPixel = 2f * _cam.orthographicSize / Mathf.Max(1, Screen.height);
            _cam.transform.position -= new Vector3(dxPixels * unitsPerPixel, dyPixels * unitsPerPixel, 0f);
            _glideTarget = null;
            Clamp();
        }

        /// <summary>Zooms by <paramref name="scale"/> (>1 = zoom in), keeping the world point under the anchor fixed.</summary>
        public void ZoomAt(float scale, Vector2 screenAnchor)
        {
            if (scale <= 0f || Mathf.Approximately(scale, 1f)) return;
            Vector3 before = ScreenToWorld(screenAnchor);
            _cam.orthographicSize = Mathf.Clamp(_cam.orthographicSize / scale, _minSize, _maxSize);
            Vector3 after = ScreenToWorld(screenAnchor);
            _cam.transform.position += before - after;
            _glideTarget = null;
            Clamp();
        }

        public void GlideTo(Vector2 worldPoint) => _glideTarget = worldPoint;

        /// <summary>Call once per frame.</summary>
        public void Tick(float dt)
        {
            if (_glideTarget is Vector2 target)
            {
                Vector3 p = _cam.transform.position;
                Vector2 next = Vector2.Lerp(p, target, 1f - Mathf.Exp(-12f * dt));
                _cam.transform.position = new Vector3(next.x, next.y, p.z);
                if ((next - target).sqrMagnitude < 0.0004f) _glideTarget = null;
                Clamp();
            }
        }

        public Vector3 ScreenToWorld(Vector2 screen)
        {
            Vector3 w = _cam.ScreenToWorldPoint(new Vector3(screen.x, screen.y, -_cam.transform.position.z));
            w.z = 0f;
            return w;
        }

        void Clamp()
        {
            float halfH = _cam.orthographicSize;
            float halfW = halfH * _cam.aspect;
            Vector3 p = _cam.transform.position;
            p.x = ClampAxis(p.x, halfW, _worldMin.x, _worldMax.x);
            p.y = ClampAxis(p.y, halfH, _worldMin.y, _worldMax.y);
            _cam.transform.position = p;
        }

        static float ClampAxis(float v, float half, float min, float max)
        {
            if (max - min <= half * 2f) return (min + max) * 0.5f; // view wider than world: centre it
            return Mathf.Clamp(v, min + half, max - half);
        }
    }
}
