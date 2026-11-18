using UnityEngine;
using WorldSim.Core;
using WorldSim.Render;
using WorldSim.Simulation;

namespace WorldSim.Presentation.Terrain
{
    /// <summary>
    /// Draws the world with zoom-dependent level of detail (owner request, 2026-11-18):
    ///  - far:  clean overview texture (no sprites, no per-pixel noise), so zooming out reads as
    ///          a calm map instead of shimmering;
    ///  - mid/near: full-detail texture (decorations baked in);
    ///  - near: animated water: pre-painted wave frames (already masked to open water when
    ///          painted) cycle a few times per second, fading in as the camera gets close.
    ///          SpriteMask is not used: it was null at runtime in the IL2CPP build (device log
    ///          2026-11-18: NullReferenceException in TerrainView..ctor).
    /// One world unit = one tile everywhere.
    /// </summary>
    public sealed class TerrainView
    {
        // Screen pixels per tile at which the far view switches (with hysteresis).
        const float FarEnter = 3.0f, FarExit = 3.6f;
        const float WavesFrom = 5f, WavesFull = 10f;
        const int WaveOrder = 2;

        const float WaveFps = 5f;

        readonly SpriteRenderer _detail, _overview, _waves;
        Texture2D _detailTex, _overviewTex;
        readonly Texture2D[] _waveTex = new Texture2D[TerrainPainter.WaveFrames];
        readonly Sprite[] _waveSprites = new Sprite[TerrainPainter.WaveFrames];
        int _shownWaveFrame = -1;
        bool _far;
        int _w, _h;
        TileRect _pending = TileRect.Empty;
        float _lastFlush;
        WorldMap _map;
        const float RepaintInterval = 0.066f; // ~15 repaints per second while painting

        public TerrainView()
        {
            _detail = new GameObject("TerrainDetail").AddComponent<SpriteRenderer>();
            _overview = new GameObject("TerrainOverview").AddComponent<SpriteRenderer>();
            _overview.enabled = false;

            _waves = new GameObject("TerrainWaves").AddComponent<SpriteRenderer>();
            _waves.sortingOrder = WaveOrder;
            _waves.enabled = false;
        }

        /// <summary>(Re)builds every texture for a freshly generated world.</summary>
        public void Build(WorldMap map)
        {
            _w = map.Width; _h = map.Height;
            _map = map;
            _pending = TileRect.Empty;

            int ppt = TerrainTexture.PixelsPerTileFor(_w, _h);
            _detailTex = Recreate(_detailTex, _w * ppt, _h * ppt, "WorldTerrain");
            TerrainTexture.Paint(_detailTex, map.Tiles, _w, _h);
            _detail.sprite = Sprite.Create(_detailTex, new Rect(0, 0, _detailTex.width, _detailTex.height), Vector2.zero, ppt, 0, SpriteMeshType.FullRect);

            int opp = TerrainPainter.OverviewPixelsPerTile(_w, _h);
            if (opp > 0)
            {
                _overviewTex = Recreate(_overviewTex, _w * opp, _h * opp, "WorldOverview");
                TerrainTexture.PaintOverview(_overviewTex, map.Tiles, _w, _h, opp);
                _overview.sprite = Sprite.Create(_overviewTex, new Rect(0, 0, _overviewTex.width, _overviewTex.height), Vector2.zero, opp, 0, SpriteMeshType.FullRect);
            }
            else
            {
                _overview.sprite = null;
            }

            // Waves only over open water (not shoreline tiles), so they never cross the beach.
            int wpp = TerrainPainter.WavePixelsPerTile(_w, _h);
            for (int f = 0; f < TerrainPainter.WaveFrames; f++)
            {
                _waveTex[f] = Recreate(_waveTex[f], _w * wpp, _h * wpp, "Waves" + f);
                TerrainTexture.PaintWaves(_waveTex[f], map.Tiles, _w, _h, wpp, f, 0, _h - 1);
                _waveSprites[f] = Sprite.Create(_waveTex[f], new Rect(0, 0, _w * wpp, _h * wpp), Vector2.zero, wpp, 0, SpriteMeshType.FullRect);
            }
            _shownWaveFrame = -1;
            _far = false;
            ApplyLod();
        }

        /// <summary>Queues a repaint of tiles changed by terrain edits (flushed at most ~15x/s).</summary>
        public void MarkDirty(WorldMap map, TileRect rect)
        {
            _map = map;
            if (!rect.IsEmpty) _pending.Include(rect.XMin, rect.YMin, rect.XMax, rect.YMax);
        }

        void FlushIfDue(float time)
        {
            if (_pending.IsEmpty || time - _lastFlush < RepaintInterval || !_map.Tiles.IsCreated) return;
            _lastFlush = time;
            TileRect r = _pending;
            _pending = TileRect.Empty;
            TerrainTexture.RepaintRows(_detailTex, _map.Tiles, _w, _h, r.YMin, r.YMax);
            int opp = TerrainPainter.OverviewPixelsPerTile(_w, _h);
            if (opp > 0 && _overviewTex != null)
                TerrainTexture.RepaintOverviewRows(_overviewTex, _map.Tiles, _w, _h, opp, r.YMin, r.YMax);
            int wpp = TerrainPainter.WavePixelsPerTile(_w, _h);
            for (int f = 0; f < TerrainPainter.WaveFrames; f++)
                if (_waveTex[f] != null) TerrainTexture.PaintWaves(_waveTex[f], _map.Tiles, _w, _h, wpp, f, r.YMin - 1, r.YMax + 1);
        }

        /// <summary>Call once per frame after the camera moved.</summary>
        public void Tick(Camera cam, float time)
        {
            if (_detailTex == null) return;
            FlushIfDue(time);
            float pxPerTile = Screen.height / Mathf.Max(0.01f, 2f * cam.orthographicSize);

            bool far = _overview.sprite != null && (_far ? pxPerTile < FarExit : pxPerTile < FarEnter);
            if (far != _far) { _far = far; ApplyLod(); }

            float waveAlpha = Mathf.Clamp01((pxPerTile - WavesFrom) / (WavesFull - WavesFrom));
            bool waves = !_far && waveAlpha > 0f && _waveSprites[0] != null;
            _waves.enabled = waves;
            if (!waves) return;
            int frame = (int)(time * WaveFps) % TerrainPainter.WaveFrames;
            if (frame != _shownWaveFrame) { _shownWaveFrame = frame; _waves.sprite = _waveSprites[frame]; }
            _waves.color = new Color(1f, 1f, 1f, 0.85f * waveAlpha);
        }

        void ApplyLod()
        {
            _overview.enabled = _far;
            _detail.enabled = !_far;
        }

        public void Dispose()
        {
            if (_detailTex != null) Object.Destroy(_detailTex);
            if (_overviewTex != null) Object.Destroy(_overviewTex);
            foreach (var t in _waveTex) if (t != null) Object.Destroy(t);
            TerrainTexture.DisposeAtlas();
        }

        static Texture2D Recreate(Texture2D tex, int w, int h, string name)
        {
            if (tex != null && tex.width == w && tex.height == h) return tex;
            if (tex != null) Object.Destroy(tex);
            return new Texture2D(w, h, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
                name = name,
            };
        }
    }
}
