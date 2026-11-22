using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using WorldSim.Core;
using WorldSim.Presentation.Art;
using WorldSim.Render;
using WorldSim.Render.Terrain;
using WorldSim.Simulation;

namespace WorldSim.Presentation.Terrain
{
    /// <summary>
    /// The approved terrain look in the game (Playable Alpha step 2). <see cref="TerrainComposer"/> itself is the runtime
    /// baker, run on background threads:
    /// <list type="bullet">
    /// <item>Near: 32x32-cell chunks (512x512 px, 16 px per cell) baked on demand around the camera, cached, released
    /// when far away; only edited chunks re-bake.</item>
    /// <item>Mid (4 px/cell), Far (2 px/cell) and Map (2 px/cell): one texture each for the whole world.</item>
    /// <item>Layers cross-fade by screen pixels per tile, so zooming never jumps.</item>
    /// </list>
    /// The composer draws with tile row 0 at the top (3/4 view: lifted land and tree tops go up the screen), so the world
    /// is shown with tile y going down: world y = <see cref="WorldHeight"/> - tile y. Use <see cref="TileToWorldY"/>.
    /// </summary>
    public sealed class PackTerrainView
    {
        public const int Chunk = 32;
        const int Px = TerrainLayout.CellPixels;
        const int MaxNearChunks = 40;
        const int MaxBakesInFlight = 2;

        // Screen pixels per tile where each layer fades in (start, full).
        const float NearFrom = 7f, NearFull = 11f;
        const float MidFrom = 2.2f, MidFull = 3.2f;
        const float FarFrom = 1.0f, FarFull = 1.5f;

        public static int WorldHeight { get; private set; }
        public static float TileToWorldY(float tileY) => WorldHeight - tileY;
        public static float WorldToTileY(float worldY) => WorldHeight - worldY;

        static RawArtPixels _art;
        static Material _animated;              // WorldSim/TerrainAnimated: water, lava and foam move
        static Dictionary<string, uint> _mapColors;

        TileData[] _tiles;
        TerrainLayout _layout;
        TerrainField _field;
        TerrainStyle _style;
        System.Func<Biome, int, uint> _mapZoomColors;
        int _w, _h, _generation;

        readonly Transform _root;
        readonly SpriteRenderer _mid, _far, _mapLayer;
        readonly Dictionary<int, NearChunk> _chunks = new Dictionary<int, NearChunk>();
        readonly ConcurrentQueue<BakeResult> _done = new ConcurrentQueue<BakeResult>();
        int _inFlight;
        readonly HashSet<int> _dirtyChunks = new HashSet<int>();
        bool _zoomLayersDirty;
        float _dirtySince = -1f;

        public float NearAlpha { get; private set; }
        public float PixelsPerTile { get; private set; }
        public bool Ready => _layout != null;

        sealed class NearChunk
        {
            public SpriteRenderer Renderer;
            public Texture2D Texture;
            public bool Valid;              // the texture shows the current tiles
            public int Epoch;               // bumped on every invalidation; stale bakes are dropped
            public bool Baking;
            public float LastWanted;
        }

        readonly HashSet<int> _awaitingLayout = new HashSet<int>();

        struct BakeResult
        {
            public int Generation, Key;     // Generation = world build; Key >= 0: near chunk; -1 mid, -2 far, -3 map
            public int Epoch;               // near chunk epoch at bake time
            public uint[] Pixels;           // bottom-up rows, ready for Texture2D
            public int Width, Height;
            public TerrainLayout Layout;    // set when a new layout comes with the result
            public TerrainField Field;
        }

        public PackTerrainView()
        {
            _root = new GameObject("PackTerrain").transform;
            _mapLayer = Layer("TerrainMap", 0);
            _far = Layer("TerrainFar", 1);
            _mid = Layer("TerrainMid", 2);
        }

        SpriteRenderer Layer(string name, int order)
        {
            var sr = new GameObject(name).AddComponent<SpriteRenderer>();
            sr.transform.SetParent(_root, false);
            sr.sortingOrder = order;
            sr.enabled = false;
            return sr;
        }

        static void EnsureArt()
        {
            if (_art != null) return;
            _art = new RawArtPixels(WorldSimArtDB.Instance.Index);
            var lod = Resources.Load<TextAsset>("WorldSimData/lod");
            _mapColors = TerrainPalette.ParseMapColors(lod != null ? lod.text : "{}");
            var shader = Shader.Find("WorldSim/TerrainAnimated");
            if (shader != null) _animated = new Material(shader) { name = "TerrainAnimated" };
            Debug.Log($"[WorldSim] Terrain baker: {_art.RawPageCount} raw art pages, {_mapColors.Count} map colours, animated shader {(shader != null ? "ok" : "MISSING")}");
        }

        /// <summary>Takes a copy of the world and starts baking (layout and zoom layers on a background thread).</summary>
        public void Build(WorldMap map, Camera cam)
        {
            EnsureArt();
            _w = map.Width; _h = map.Height;
            WorldHeight = _h;
            _tiles = map.Tiles.ToArray();
            _style = TerrainPalette.ApprovedStyle(_mapColors);
            _mapZoomColors = TerrainPalette.MapZoomColors(_mapColors);
            _generation++;
            _layout = null; _field = null;
            foreach (var c in _chunks.Values) Release(c);
            _chunks.Clear();
            _dirtyChunks.Clear();
            _awaitingLayout.Clear();
            _inFlight = 0;
            uint deep = TerrainPalette.Vivid(TerrainPalette.MapColor(_mapColors, Biome.DeepWater, 0), 150, 10);
            cam.backgroundColor = new Color32((byte)Rgba.R(deep), (byte)Rgba.G(deep), (byte)Rgba.B(deep), 255);
            StartLayoutAndZoomBake(_tiles, _generation);
        }

        /// <summary>A terrain edit: copy the tiles again, re-layout, re-bake the touched near chunks and the zoom layers.</summary>
        public void MarkDirty(WorldMap map, TileRect rect, float time)
        {
            if (rect.IsEmpty || !map.IsCreated) return;
            _tiles = map.Tiles.ToArray();
            for (int cy = (rect.YMin - 2) / Chunk; cy <= (rect.YMax + 2) / Chunk; cy++)
                for (int cx = (rect.XMin - 2) / Chunk; cx <= (rect.XMax + 2) / Chunk; cx++)
                    if (cx >= 0 && cy >= 0 && cx * Chunk < _w && cy * Chunk < _h) _dirtyChunks.Add(cy * 1024 + cx);
            _zoomLayersDirty = true;
            if (_dirtySince < 0f) _dirtySince = time;
        }

        void StartLayoutAndZoomBake(TileData[] tiles, int generation)
        {
            var style = _style;
            var mapColors = _mapZoomColors;
            int w = _w, h = _h;
            Task.Run(() =>
            {
                try
                {
                    var layout = new TerrainLayout(tiles, w, h);
                    var field = new TerrainField(tiles, layout);
                    _done.Enqueue(new BakeResult { Generation = generation, Key = int.MinValue, Layout = layout, Field = field });
                    Enqueue(generation, -1, TerrainComposer.ComposeZoom(tiles, layout, field, _art, ZoomLayer.Mid, null, style, null, _animated != null), w * 4, h * 4);
                    Enqueue(generation, -2, TerrainComposer.ComposeZoom(tiles, layout, field, _art, ZoomLayer.Far, null, style, null, _animated != null), w * 2, h * 2);
                    Enqueue(generation, -3, TerrainComposer.ComposeZoom(tiles, layout, field, _art, ZoomLayer.Map, null, style, mapColors), w * 2, h * 2);
                }
                catch (System.Exception e) { Debug.LogException(e); }
            });
        }

        void Enqueue(int generation, int key, uint[] topDown, int width, int height) =>
            _done.Enqueue(new BakeResult { Generation = generation, Key = key, Pixels = FlipRows(topDown, width, height), Width = width, Height = height });

        static uint[] FlipRows(uint[] src, int w, int h)
        {
            var dst = new uint[src.Length];
            for (int y = 0; y < h; y++) System.Array.Copy(src, y * w, dst, (h - 1 - y) * w, w);
            return dst;
        }

        public void Tick(Camera cam, float time)
        {
            if (_tiles == null) return;
            ApplyFinishedBakes(time);
            if (_layout == null) return;

            // Edits: after a short pause in painting, re-layout; the touched chunks re-bake once the new layout is in.
            if (_dirtySince >= 0f && time - _dirtySince > 0.25f)
            {
                _dirtySince = -1f;
                _awaitingLayout.UnionWith(_dirtyChunks);
                _dirtyChunks.Clear();
                if (_zoomLayersDirty) { _zoomLayersDirty = false; StartLayoutAndZoomBake(_tiles, _generation); }
            }

            float ppt = Screen.height / Mathf.Max(0.01f, 2f * cam.orthographicSize);
            PixelsPerTile = ppt;
            float near = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(NearFrom, NearFull, ppt));
            float mid = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(MidFrom, MidFull, ppt));
            float far = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(FarFrom, FarFull, ppt));
            NearAlpha = near;

            // Opaque bottom layer, each layer above fades in; layers fully covered are switched off.
            // The mid layer stays under the near chunks, so a chunk still baking never shows a hole.
            SetLayer(_mapLayer, 1f, far < 1f);
            SetLayer(_far, far, far > 0f && mid < 1f);
            SetLayer(_mid, mid, mid > 0f);
            TickNear(cam, time, near);
        }

        static void SetLayer(SpriteRenderer sr, float alpha, bool on)
        {
            on &= sr.sprite != null;
            if (sr.enabled != on) sr.enabled = on;
            if (on) sr.color = new Color(1f, 1f, 1f, alpha);
        }

        void TickNear(Camera cam, float time, float alpha)
        {
            if (alpha <= 0f)
            {
                foreach (var c in _chunks.Values) if (c.Renderer != null && c.Renderer.enabled) c.Renderer.enabled = false;
                ReleaseOld(time, 0f);
                return;
            }
            float halfH = cam.orthographicSize, halfW = halfH * cam.aspect;
            Vector3 p = cam.transform.position;
            // Visible tile rectangle (tile y goes down the screen), one chunk of margin.
            int tx0 = Mathf.FloorToInt(p.x - halfW), tx1 = Mathf.CeilToInt(p.x + halfW);
            int ty0 = Mathf.FloorToInt(WorldToTileY(p.y + halfH)), ty1 = Mathf.CeilToInt(WorldToTileY(p.y - halfH));
            int cx0 = Mathf.Max(0, tx0 / Chunk - 1), cx1 = Mathf.Min((_w - 1) / Chunk, tx1 / Chunk + 1);
            int cy0 = Mathf.Max(0, ty0 / Chunk - 1), cy1 = Mathf.Min((_h - 1) / Chunk, ty1 / Chunk + 1);

            // Nearest-first bake requests.
            int ccx = Mathf.Clamp((int)p.x / Chunk, cx0, cx1), ccy = Mathf.Clamp((int)WorldToTileY(p.y) / Chunk, cy0, cy1);
            for (int ring = 0; ring <= Mathf.Max(cx1 - cx0, cy1 - cy0) + 1 && _inFlight < MaxBakesInFlight; ring++)
                for (int cy = ccy - ring; cy <= ccy + ring; cy++)
                    for (int cx = ccx - ring; cx <= ccx + ring; cx++)
                    {
                        if (cx < cx0 || cx > cx1 || cy < cy0 || cy > cy1) continue;
                        if (System.Math.Max(System.Math.Abs(cx - ccx), System.Math.Abs(cy - ccy)) != ring) continue;
                        int key = cy * 1024 + cx;
                        if (!_chunks.TryGetValue(key, out var c)) _chunks[key] = c = new NearChunk();
                        c.LastWanted = time;
                        if (!c.Valid && !c.Baking && _inFlight < MaxBakesInFlight) BakeNear(key, cx, cy, c);
                    }

            foreach (var kv in _chunks)
            {
                var c = kv.Value;
                if (c.Renderer == null) continue;
                int cx = kv.Key % 1024, cy = kv.Key / 1024;
                bool visible = cx >= cx0 && cx <= cx1 && cy >= cy0 && cy <= cy1;
                if (c.Renderer.enabled != visible) c.Renderer.enabled = visible;
                if (visible) c.Renderer.color = new Color(1f, 1f, 1f, alpha);
            }
            ReleaseOld(time, 4f);
        }

        void BakeNear(int key, int cx, int cy, NearChunk c)
        {
            c.Baking = true;
            _inFlight++;
            var tiles = _tiles; var layout = _layout; var field = _field; var style = _style;
            int generation = _generation, epoch = c.Epoch;
            Task.Run(() =>
            {
                try
                {
                    int cw = System.Math.Min(Chunk, _w - cx * Chunk), ch = System.Math.Min(Chunk, _h - cy * Chunk);
                    // Props are live sprites (PropView, they sway); the chunk bakes ground, cliffs, water and foam only.
                    var img = TerrainComposer.ComposeNear(tiles, layout, field, _art, cx * Chunk, cy * Chunk, cw, ch, false, out int iw, out int ih,
                                                          style, _animated != null);
                    _done.Enqueue(new BakeResult { Generation = generation, Key = key, Epoch = epoch, Pixels = FlipRows(img, iw, ih), Width = iw, Height = ih });
                }
                catch (System.Exception e)
                {
                    Debug.LogException(e);
                    _done.Enqueue(new BakeResult { Generation = generation, Key = key, Epoch = epoch });
                }
            });
        }

        void ApplyFinishedBakes(float time)
        {
            int uploads = 0;
            while (uploads < 3 && _done.TryDequeue(out var r))
            {
                if (r.Key >= 0) _inFlight = System.Math.Max(0, _inFlight - 1);
                if (r.Generation != _generation) continue;                      // from a previous world
                if (r.Key == int.MinValue)
                {
                    _layout = r.Layout; _field = r.Field;
                    foreach (int key in _awaitingLayout)
                        if (_chunks.TryGetValue(key, out var stale)) { stale.Epoch++; stale.Valid = false; }
                    _awaitingLayout.Clear();
                    continue;
                }
                if (r.Key >= 0)
                {
                    if (!_chunks.TryGetValue(r.Key, out var c)) continue;
                    c.Baking = false;
                    if (r.Pixels == null || r.Epoch != c.Epoch) continue;
                    int cx = r.Key % 1024, cy = r.Key / 1024;
                    Upload(ref c.Texture, ref c.Renderer, r, Px, new Vector3(cx * Chunk, TileToWorldY(cy * Chunk), 0f), 3, "Chunk" + cx + "_" + cy);
                    c.Valid = true;
                    uploads++;
                }
                else
                {
                    SpriteRenderer layer = r.Key == -1 ? _mid : r.Key == -2 ? _far : _mapLayer;
                    Texture2D tex = layer.sprite != null ? layer.sprite.texture : null;
                    SpriteRenderer sr = layer;
                    Upload(ref tex, ref sr, r, r.Key == -1 ? 4 : 2, new Vector3(0f, WorldHeight, 0f), layer.sortingOrder, layer.name);
                    uploads++;
                }
            }
        }

        /// <summary>A fresh, GPU-only texture per bake (no CPU copy kept), shown by a top-left-pivoted sprite.</summary>
        void Upload(ref Texture2D tex, ref SpriteRenderer sr, BakeResult r, int ppu, Vector3 topLeft, int order, string name)
        {
            var fresh = new Texture2D(r.Width, r.Height, TextureFormat.RGBA32, false, false)
            {
                filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = name,
            };
            fresh.SetPixelData(r.Pixels, 0);
            fresh.Apply(false, true);
            if (sr == null)
            {
                sr = new GameObject(name).AddComponent<SpriteRenderer>();
                sr.transform.SetParent(_root, false);
                sr.sortingOrder = order;
            }
            if (_animated != null && sr.sharedMaterial != _animated) sr.sharedMaterial = _animated;
            Sprite old = sr.sprite;
            sr.sprite = Sprite.Create(fresh, new Rect(0, 0, r.Width, r.Height), new Vector2(0f, 1f), ppu, 0, SpriteMeshType.FullRect);
            sr.transform.localPosition = topLeft;
            if (old != null) { Texture2D oldTex = old.texture; Object.Destroy(old); if (oldTex != null) Object.Destroy(oldTex); }
            tex = fresh;
        }

        void ReleaseOld(float time, float keepSeconds)
        {
            if (_chunks.Count <= MaxNearChunks / 2) return;
            List<int> drop = null;
            foreach (var kv in _chunks)
                if (!kv.Value.Baking && time - kv.Value.LastWanted > keepSeconds && _chunks.Count - (drop?.Count ?? 0) > MaxNearChunks / 2)
                    (drop ??= new List<int>()).Add(kv.Key);
            if (drop == null) return;
            foreach (int key in drop) { Release(_chunks[key]); _chunks.Remove(key); }
        }

        static void Release(NearChunk c)
        {
            if (c.Renderer != null) { if (c.Renderer.sprite != null) Object.Destroy(c.Renderer.sprite); Object.Destroy(c.Renderer.gameObject); }
            if (c.Texture != null) Object.Destroy(c.Texture);
            c.Renderer = null; c.Texture = null;
        }

        /// <summary>How high land is drawn at a tile (world units), so creatures stand on lifted ground.</summary>
        public float LiftAt(int tileX, int tileY)
        {
            if (_layout == null || tileX < 0 || tileY < 0 || tileX >= _w || tileY >= _h) return 0f;
            return TerrainLayout.Lift(_layout.Level[tileY * _w + tileX]) / (float)Px;
        }

        /// <summary>The baked world (read-only), for the live prop sprites.</summary>
        public TileData[] Tiles => _tiles;
        public TerrainLayout Layout => _layout;
        public TerrainField Field => _field;
        public int WorldWidth => _w;

        public int NearChunksLoaded
        {
            get { int n = 0; foreach (var c in _chunks.Values) if (c.Texture != null) n++; return n; }
        }

        public void Dispose()
        {
            foreach (var c in _chunks.Values) Release(c);
            _chunks.Clear();
            if (_root != null) Object.Destroy(_root.gameObject);
        }
    }
}
