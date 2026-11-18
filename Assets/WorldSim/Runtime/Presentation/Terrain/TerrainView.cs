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
    ///  - near: animated water: two wave layers scroll over the open water, masked to water tiles
    ///          (SpriteMask), fading in as the camera gets close. Off-screen cost is nil when far.
    /// One world unit = one tile everywhere.
    /// </summary>
    public sealed class TerrainView
    {
        // Screen pixels per tile at which the far view switches (with hysteresis).
        const float FarEnter = 3.0f, FarExit = 3.6f;
        const float WavesFrom = 5f, WavesFull = 10f;
        const int WaveOrder = 2;

        readonly SpriteRenderer _detail, _overview, _waveA, _waveB;
        readonly SpriteMask _mask;
        Texture2D _detailTex, _overviewTex, _maskTex;
        bool _far;
        int _w, _h;

        public TerrainView()
        {
            _detail = new GameObject("TerrainDetail").AddComponent<SpriteRenderer>();
            _overview = new GameObject("TerrainOverview").AddComponent<SpriteRenderer>();
            _overview.enabled = false;

            _mask = new GameObject("WaterMask").AddComponent<SpriteMask>();
            _mask.alphaCutoff = 0.5f;
            _waveA = CreateWaveLayer("WavesA", 0, new Color(1f, 1f, 1f, 0.9f));
            _waveB = CreateWaveLayer("WavesB", 1, new Color(1f, 1f, 1f, 0.6f));
        }

        static SpriteRenderer CreateWaveLayer(string name, int variant, Color tint)
        {
            int n = TerrainPainter.WaveTileSize;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Repeat };
            tex.SetPixelData(TerrainPainter.BuildWaveTile(variant), 0);
            tex.Apply(false, true);
            var sr = new GameObject(name).AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, n, n), Vector2.zero, 8f, 0, SpriteMeshType.FullRect);
            sr.drawMode = SpriteDrawMode.Tiled;
            sr.tileMode = SpriteTileMode.Continuous;
            sr.maskInteraction = SpriteMaskInteraction.VisibleInsideMask;
            sr.sortingOrder = WaveOrder;
            sr.color = tint;
            sr.enabled = false;
            return sr;
        }

        /// <summary>(Re)builds every texture for a freshly generated world.</summary>
        public void Build(WorldMap map)
        {
            _w = map.Width; _h = map.Height;

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
            _maskTex = Recreate(_maskTex, _w, _h, "WaterMask");
            TerrainTexture.PaintOpenWaterMask(_maskTex, map.Tiles, _w, _h);
            _mask.sprite = Sprite.Create(_maskTex, new Rect(0, 0, _w, _h), Vector2.zero, 1f, 0, SpriteMeshType.FullRect);

            var size = new Vector2(_w + 8, _h + 8);
            _waveA.size = size;
            _waveB.size = size;
            _far = false;
            ApplyLod();
        }

        /// <summary>Call once per frame after the camera moved.</summary>
        public void Tick(Camera cam, float time)
        {
            if (_detailTex == null) return;
            float pxPerTile = Screen.height / Mathf.Max(0.01f, 2f * cam.orthographicSize);

            bool far = _overview.sprite != null && (_far ? pxPerTile < FarExit : pxPerTile < FarEnter);
            if (far != _far) { _far = far; ApplyLod(); }

            float waveAlpha = Mathf.Clamp01((pxPerTile - WavesFrom) / (WavesFull - WavesFrom));
            bool waves = !_far && waveAlpha > 0f;
            _waveA.enabled = waves;
            _waveB.enabled = waves;
            if (!waves) return;

            // Scroll the two layers in different directions; positions wrap every wave tile
            // (4 world units), the layers are 8 units larger than the map so edges never show.
            const float tileUnits = 4f;
            _waveA.transform.position = new Vector3(-4f + Mathf.Repeat(time * 0.35f, tileUnits), -4f + Mathf.Repeat(time * 0.12f, tileUnits), 0f);
            _waveB.transform.position = new Vector3(-4f + Mathf.Repeat(-time * 0.22f, tileUnits), -4f + Mathf.Repeat(time * 0.27f, tileUnits), 0f);
            _waveA.color = new Color(1f, 1f, 1f, 0.9f * waveAlpha);
            _waveB.color = new Color(1f, 1f, 1f, 0.6f * waveAlpha);
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
            if (_maskTex != null) Object.Destroy(_maskTex);
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
