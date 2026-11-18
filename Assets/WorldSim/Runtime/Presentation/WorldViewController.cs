using System.Collections.Generic;
using Unity.Entities;
using UnityEngine;
using UnityEngine.InputSystem.EnhancedTouch;
using UnityEngine.Rendering.Universal;
using WorldSim.Core;
using WorldSim.Presentation.Input;
using WorldSim.Presentation.Terrain;
using WorldSim.Presentation.UI;
using WorldSim.Simulation;
using ETouch = UnityEngine.InputSystem.EnhancedTouch.Touch;
using TileData = WorldSim.Core.TileData; // URP also defines UnityEngine.Rendering.Universal.TileData
using ETouchPhase = UnityEngine.InputSystem.TouchPhase;

namespace WorldSim.Presentation
{
    /// <summary>
    /// Stage 2/3 world view (presentation glue only, §3.2): requests a world from the ECS
    /// <see cref="WorldMapSystem"/>, draws it, and maps touch gestures to camera moves and tile
    /// inspection. All terrain data is read from the WorldMap singleton; nothing here changes
    /// simulation state except asking for a new world.
    /// </summary>
    public sealed class WorldViewController : MonoBehaviour
    {
        /// <summary>First-launch seed. Its hash is pinned in WorldGenTests, so the value shown
        /// on a device can be compared with CI (§4.3 cross-device acceptance).</summary>
        public const ulong DefaultSeed = 0x5EED;
        /// <summary>Map sizes offered now (plan A5). Huge/Titanic need chunked rendering first.</summary>
        static readonly int[] Sizes = { 256, 512, 1024 };
        static readonly string[] SizeNames = { "Small", "Medium", "Large" };
        const string SeedPrefKey = "worldsim.lastSeed";
        const string SizePrefKey = "worldsim.mapSizeIndex";
        const string NoticePrefKey = "worldsim.fictionNoticeAccepted.v1";
        int _sizeIndex;

        Camera _cam;
        CameraRig _rig;
        WorldHud _hud;
        readonly GestureRecognizer _gestures = new GestureRecognizer();
        readonly List<TouchSample> _down = new List<TouchSample>(4);
        readonly HashSet<int> _uiTouches = new HashSet<int>();

        EntityManager _em;
        EntityQuery _mapQuery;
        uint _shownVersion;
        WorldMap _map;

        TerrainView _terrainView;
        SpriteRenderer _selection;

        bool _ready;

        void Start()
        {
            // HUD first: if a later step fails, the player sees the error instead of a blank screen
            // (device run 2026-11-18 failed in CreateGlobalLight before the HUD existed).
            _hud = new WorldHud(transform);
            _hud.NewWorldClicked += NewWorld;
            _hud.SizeClicked += CycleSize;
            _hud.SizeLabelRequested += UpdateSizeLabel;
            _hud.NoticeAccepted += () => { PlayerPrefs.SetInt(NoticePrefKey, 1); PlayerPrefs.Save(); };
            _hud.SetTitle("WorldSim\nGenerating world...");
            _sizeIndex = Mathf.Clamp(PlayerPrefs.GetInt(SizePrefKey, 0), 0, Sizes.Length - 1);
            UpdateSizeLabel();
            if (PlayerPrefs.GetInt(NoticePrefKey, 0) != 1) _hud.ShowNotice(); // plan A3: first launch

            try
            {
                _cam = Camera.main;
                // Pixel Perfect Camera drives orthographicSize itself, which fights free pinch zoom.
                // Integer-step pixel-perfect zoom returns with the graphics settings (§7.2).
                var ppc = _cam.GetComponent<PixelPerfectCamera>();
                if (ppc != null) ppc.enabled = false;
                _rig = new CameraRig(_cam);

                CreateGlobalLight();
                _terrainView = new TerrainView();
                _selection = CreateSelectionMarker();

                EnhancedTouchSupport.Enable();
                _gestures.PixelScale = Screen.dpi > 0 ? Screen.dpi / 160f : 2f;

                _em = World.DefaultGameObjectInjectionWorld.EntityManager;
                _mapQuery = _em.CreateEntityQuery(ComponentType.ReadOnly<WorldMap>());

                RequestWorld(LoadSeed(), CurrentSize);
                _ready = true;
            }
            catch (System.Exception e)
            {
                Debug.LogException(e);
                _hud.SetTitle("WorldSim: startup error\n" + e.GetType().Name + ": " + e.Message);
            }
        }

        void OnDestroy()
        {
            if (EnhancedTouchSupport.enabled) EnhancedTouchSupport.Disable();
            _terrainView?.Dispose();
        }

        void Update()
        {
            if (!_ready) return;
            _hud.Tick();
            RefreshWorldIfChanged();
            if (_map.Version == 0) return;

            CollectTouches();
            _gestures.Update(Time.unscaledTime, _down);

            if (_gestures.PinchScale != 1f)
                _rig.ZoomAt(_gestures.PinchScale, new Vector2(_gestures.PinchCenterX, _gestures.PinchCenterY));
            if (_gestures.PanDx != 0f || _gestures.PanDy != 0f)
                _rig.PanScreen(_gestures.PanDx, _gestures.PanDy);

            var at = new Vector2(_gestures.GestureX, _gestures.GestureY);
            if (_gestures.Tap) Select(at, longPress: false);
            if (_gestures.LongPress) Select(at, longPress: true);
            if (_gestures.DoubleTap) _rig.GlideTo(_rig.ScreenToWorld(at));

            _rig.Tick(Time.unscaledDeltaTime);
            _terrainView.Tick(_cam, Time.unscaledTime);
        }

        void CollectTouches()
        {
            _down.Clear();
            foreach (ETouch t in ETouch.activeTouches)
            {
                ETouchPhase phase = t.phase;
                if (phase == ETouchPhase.Began && _hud.IsOverUi(t.screenPosition)) _uiTouches.Add(t.touchId);
                bool ended = phase == ETouchPhase.Ended || phase == ETouchPhase.Canceled;
                if (_uiTouches.Contains(t.touchId))
                {
                    if (ended) _uiTouches.Remove(t.touchId);
                    continue; // touches that started on the HUD never move the world
                }
                if (!ended) _down.Add(new TouchSample(t.touchId, t.screenPosition.x, t.screenPosition.y));
            }
        }

        void RefreshWorldIfChanged()
        {
            if (_mapQuery.IsEmpty) return;
            WorldMap map = _mapQuery.GetSingleton<WorldMap>();
            if (map.Version == _shownVersion || !map.IsCreated) return;
            _map = map;
            _shownVersion = map.Version;

            _terrainView.Build(map);
            _rig.SetWorld(map.Width, map.Height);
            _selection.enabled = false;
            _hud.HideInfo();
            _hud.SetTitle($"WorldSim   seed 0x{map.Seed:X}   {map.Width}x{map.Height}\nworld hash 0x{map.Hash:X16}");
            SaveSeed(map.Seed);
        }

        void Select(Vector2 screen, bool longPress)
        {
            Vector3 w = _rig.ScreenToWorld(screen);
            int x = Mathf.FloorToInt(w.x), y = Mathf.FloorToInt(w.y);
            if (!_map.InBounds(x, y)) { _selection.enabled = false; _hud.HideInfo(); return; }

            // Re-read the singleton: the array handle is only valid for the current world version.
            WorldMap map = _mapQuery.GetSingleton<WorldMap>();
            if (map.Version != _shownVersion) return;
            TileData t = map.Get(x, y);

            _selection.transform.position = new Vector3(x, y, 0f);
            _selection.enabled = true;
            string res = ResourceText((ResourceFlags)t.ResourceFlags);
            string deco = t.DecorationId != 0 ? $"   {(Decoration)t.DecorationId}" : "";
            string text = $"{(Biome)t.BiomeId}{deco}  ({x}, {y})\n" +
                          $"height {t.Height}   moisture {t.Moisture}   temperature {t.Temperature}\n" +
                          $"resources: {res}";
            if (longPress) text += "\n(long-press actions arrive with the powers stage)";
            _hud.ShowInfo(text);
        }

        static string ResourceText(ResourceFlags f)
        {
            if (f == ResourceFlags.None) return "none";
            var parts = new List<string>(4);
            if ((f & ResourceFlags.Wood) != 0) parts.Add("wood");
            if ((f & ResourceFlags.Stone) != 0) parts.Add("stone");
            if ((f & ResourceFlags.Gold) != 0) parts.Add("gold");
            if ((f & ResourceFlags.Gems) != 0) parts.Add("gems");
            return string.Join(", ", parts);
        }

        void NewWorld()
        {
            // Picking a seed is not world generation: a time-based value is fine here (§4.3
            // forbids UnityEngine.Random *inside* generation, which stays seed-only).
            ulong seed = SplitMix64.Mix((ulong)System.DateTime.UtcNow.Ticks) & 0xFFFFFFFFUL;
            _hud.SetTitle("WorldSim\nGenerating world...");
            RequestWorld(seed, CurrentSize);
        }

        int CurrentSize => Sizes[_sizeIndex];

        /// <summary>Changes the size used by the next "New world" (the current world is kept).</summary>
        void CycleSize()
        {
            _sizeIndex = (_sizeIndex + 1) % Sizes.Length;
            PlayerPrefs.SetInt(SizePrefKey, _sizeIndex);
            PlayerPrefs.Save();
            UpdateSizeLabel();
        }

        void UpdateSizeLabel() => _hud.SetSizeLabel($"{SizeNames[_sizeIndex]} {Sizes[_sizeIndex]}");

        void RequestWorld(ulong seed, int size)
        {
            Entity e = _em.CreateEntity(typeof(WorldGenRequest));
            _em.SetComponentData(e, new WorldGenRequest { Seed = seed, Width = size, Height = size });
        }

        static ulong LoadSeed()
        {
            string s = PlayerPrefs.GetString(SeedPrefKey, "");
            return ulong.TryParse(s, out ulong v) ? v : DefaultSeed;
        }

        static void SaveSeed(ulong seed)
        {
            PlayerPrefs.SetString(SeedPrefKey, seed.ToString());
            PlayerPrefs.Save();
        }

        /// <summary>
        /// URP's 2D renderer clears the light texture to black when no Global light exists
        /// (RendererLighting.cs, URP 17.3), which would render lit sprites black. Created inactive
        /// so Awake/OnEnable register it as Global from the start.
        /// </summary>
        void CreateGlobalLight()
        {
            var go = new GameObject("GlobalLight2D");
            go.SetActive(false);
            go.transform.SetParent(transform, false);
            var light = go.AddComponent<Light2D>();
            // Order matters (URP 17.3): the lightType setter calls
            // Light2DManager.ErrorIfDuplicateGlobalLight, which iterates targetSortingLayers. On an
            // inactive, just-added light that array is still null (Awake fills it later), so the
            // layers must be set first, otherwise NullReferenceException (seen on device).
            SortingLayer[] layers = SortingLayer.layers;
            var ids = new int[layers.Length];
            for (int i = 0; i < layers.Length; i++) ids[i] = layers[i].id;
            light.targetSortingLayers = ids;
            light.lightType = Light2D.LightType.Global;
            light.intensity = 1f;
            light.color = Color.white;
            go.SetActive(true);
        }

        SpriteRenderer CreateSelectionMarker()
        {
            var tex = new Texture2D(1, 1, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            tex.SetPixel(0, 0, Color.white);
            tex.Apply();
            var sr = new GameObject("Selection").AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, 1, 1), Vector2.zero, 1f);
            sr.color = new Color(1f, 0.95f, 0.4f, 0.45f);
            sr.sortingOrder = 10;
            sr.enabled = false;
            return sr;
        }
    }
}
