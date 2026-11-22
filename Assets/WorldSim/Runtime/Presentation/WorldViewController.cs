using System.Collections.Generic;
using Unity.Entities;
using UnityEngine;
using UnityEngine.InputSystem.EnhancedTouch;
using UnityEngine.Rendering.Universal;
using WorldSim.Core;
using WorldSim.Core.Life;
using WorldSim.Presentation.Input;
using WorldSim.Presentation.Life;
using WorldSim.Simulation.Life;
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
        const string SizePrefKey = "worldsim.mapSizeIndex.v2";   // v2: default back to 256 (owner, Alpha step 2)
        const string NoticePrefKey = "worldsim.fictionNoticeAccepted.v1";
        int _sizeIndex;

        // ---- Generation settings (Beta B2); applied by the next "New world" ----
        static readonly (string name, sbyte v)[] LandOptions = { ("Islands", -22), ("Balanced", 0), ("Continents", 22) };
        static readonly (string name, sbyte v)[] ClimateOptions = { ("Ice age", -30), ("Cold", -15), ("Temperate", 0), ("Warm", 15), ("Hot", 30) };
        static readonly (string name, byte v)[] MountainOptions = { ("Few peaks", 40), ("Mountains", 100), ("Many peaks", 170) };
        static readonly (string name, byte v)[] BlankOptions = { ("Generated", 0), ("Empty ocean", 1), ("Flat land", 2) };
        int _land = 1, _climate = 2, _mountains = 1, _blank;

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

        PackTerrainView _terrainView;
        PropView _propView;
        WorldSim.Presentation.Fx.FxView _fx;
        WorldSim.Presentation.Fx.AudioView _audio;
        WorldSim.Presentation.Fx.PowerController _powers;
        WorldSim.Core.Powers.PowerKind? _power;
        float _lastPowerTime;
        SpriteRenderer _selection;

        // ---- Life (Beta B3) ----
        CreatureView _creatureView;
        SpeciesId? _spawn;
        int _lastSpawnX = int.MinValue, _lastSpawnY = int.MinValue;
        float _lastSpawnTime;
        Entity _selectedCreature = Entity.Null;
        float _nextUiRefresh;
        bool _paused;
        int _speedIndex;
        static readonly float[] Speeds = { 1f, 2f, 5f, 10f };
        EntityQuery _lifeQuery, _clockQuery;

        // ---- Terrain brushes (Beta B2) ----
        static readonly int[] BrushRadii = { 0, 1, 3, 6, 10 };
        const string BrushPrefKey = "worldsim.brushIndex";
        WorldHud.ToolChoice? _tool;
        int _brushIndex = 2;
        EntityQuery _editQuery;
        uint _shownEditVersion;
        int _lastDabX = int.MinValue, _lastDabY = int.MinValue;
        float _lastDabTime;
        const float DabInterval = 0.06f; // continuous tools (raise/lower) repeat while held

        bool _ready;
        readonly DevStats _stats = new DevStats();
        uint _populatedVersion;

        void Start()
        {
            // HUD first: if a later step fails, the player sees the error instead of a blank screen
            // (device run 2026-11-18 failed in CreateGlobalLight before the HUD existed).
            _hud = new WorldHud(transform);
            _hud.NewWorldClicked += NewWorld;
            _hud.SizeClicked += CycleSize;
            _hud.SizeLabelRequested += UpdateSizeLabel;
            _hud.LandClicked += () => Cycle(ref _land, LandOptions.Length, "worldsim.land");
            _hud.ClimateClicked += () => Cycle(ref _climate, ClimateOptions.Length, "worldsim.climate");
            _hud.MountainsClicked += () => Cycle(ref _mountains, MountainOptions.Length, "worldsim.mountains");
            _hud.BlankClicked += () => Cycle(ref _blank, BlankOptions.Length, "worldsim.blank");
            _land = Mathf.Clamp(PlayerPrefs.GetInt("worldsim.land", 1), 0, LandOptions.Length - 1);
            _climate = Mathf.Clamp(PlayerPrefs.GetInt("worldsim.climate", 2), 0, ClimateOptions.Length - 1);
            _mountains = Mathf.Clamp(PlayerPrefs.GetInt("worldsim.mountains", 1), 0, MountainOptions.Length - 1);
            _blank = Mathf.Clamp(PlayerPrefs.GetInt("worldsim.blank", 0), 0, BlankOptions.Length - 1);
            _hud.NoticeAccepted += () => { PlayerPrefs.SetInt(NoticePrefKey, 1); PlayerPrefs.Save(); };
            _hud.ToolChanged += OnToolChanged;
            _hud.SpawnChanged += sp => { _spawn = sp; _lastSpawnX = int.MinValue; if (sp.HasValue) { _hud.HideInfo(); _selectedCreature = Entity.Null; } };
            _hud.PauseClicked += TogglePause;
            _hud.SpeedClicked += CycleSpeed;
            _hud.SpeedSelected += SelectSpeed;
            _hud.PowerChanged += pw => { _power = pw; if (pw.HasValue) { _hud.HideInfo(); _selectedCreature = Entity.Null; } };
            _hud.TimeLabelsRequested += UpdateTimeLabels;
            _hud.BrushSizeClicked += CycleBrush;
            _hud.BrushSizeLabelRequested += UpdateBrushLabel;
            _hud.ArtLabClicked += () =>
            {
                var lab = GetComponent<WorldSim.Presentation.Art.ArtLabView>();
                if (lab == null) lab = gameObject.AddComponent<WorldSim.Presentation.Art.ArtLabView>();
                lab.Open(_hud);
            };
            _hud.ArtTestClicked += () =>
            {
                var view = GetComponent<WorldSim.Presentation.Art.ArtTestView>();
                if (view == null) view = gameObject.AddComponent<WorldSim.Presentation.Art.ArtTestView>(); // Unity objects: no ?? (overloaded ==)
                view.Toggle(_cam);
            };
            _brushIndex = Mathf.Clamp(PlayerPrefs.GetInt(BrushPrefKey, 2), 0, BrushRadii.Length - 1);
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
                _terrainView = new PackTerrainView();
                _propView = new PropView();
                _selection = CreateSelectionMarker();

                EnhancedTouchSupport.Enable();
                _gestures.PixelScale = Screen.dpi > 0 ? Screen.dpi / 160f : 2f;

                _em = World.DefaultGameObjectInjectionWorld.EntityManager;
                _mapQuery = _em.CreateEntityQuery(ComponentType.ReadOnly<WorldMap>());
                _editQuery = _em.CreateEntityQuery(ComponentType.ReadOnly<TerrainEditQueue>());
                _lifeQuery = _em.CreateEntityQuery(ComponentType.ReadOnly<LifeState>());
                _clockQuery = _em.CreateEntityQuery(ComponentType.ReadOnly<WorldSim.Simulation.SimulationClock>());
                _creatureView = new CreatureView();
                _fx = new WorldSim.Presentation.Fx.FxView(_cam);
                _audio = new WorldSim.Presentation.Fx.AudioView(_cam);
                _powers = new WorldSim.Presentation.Fx.PowerController(_em, _fx);
                UpdateTimeLabels();

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

        readonly System.Diagnostics.Stopwatch _frameWatch = new System.Diagnostics.Stopwatch();

        void Update()
        {
            if (!_ready) return;
            _frameWatch.Restart();
            UpdateWorldView();
            _stats.ControllerMs = _frameWatch.Elapsed.TotalMilliseconds;
            _stats.Tick(Time.unscaledTime, Time.unscaledDeltaTime, _terrainView);
        }

        void UpdateWorldView()
        {
            _hud.Tick();
            RefreshWorldIfChanged();
            if (_map.Version == 0) return;

            CollectTouches();
            _gestures.Update(Time.unscaledTime, _down);

            if (_gestures.PinchScale != 1f)
                _rig.ZoomAt(_gestures.PinchScale, new Vector2(_gestures.PinchCenterX, _gestures.PinchCenterY));

            if (_power.HasValue)
            {
                // Powers: one finger taps where to strike; two fingers still pan and zoom.
                if (_gestures.Current == GestureRecognizer.State.Pinching && (_gestures.PanDx != 0f || _gestures.PanDy != 0f))
                    _rig.PanScreen(_gestures.PanDx, _gestures.PanDy);
                if (_gestures.Tap && Time.unscaledTime - _lastPowerTime > 0.25f)
                {
                    Vector3 w = _rig.ScreenToWorld(new Vector2(_gestures.GestureX, _gestures.GestureY));
                    int px = Mathf.FloorToInt(w.x), py = Mathf.FloorToInt(PackTerrainView.WorldToTileY(w.y));
                    if (_map.InBounds(px, py)) { _powers.Use(_power.Value, px, py); _lastPowerTime = Time.unscaledTime; }
                }
            }
            else if (_spawn.HasValue)
            {
                if (_gestures.Current == GestureRecognizer.State.Pinching && (_gestures.PanDx != 0f || _gestures.PanDy != 0f))
                    _rig.PanScreen(_gestures.PanDx, _gestures.PanDy);
                UpdateSpawn();
            }
            else if (_tool.HasValue)
            {
                // Brush mode: one finger paints; two fingers still pan and zoom.
                if (_gestures.Current == GestureRecognizer.State.Pinching && (_gestures.PanDx != 0f || _gestures.PanDy != 0f))
                    _rig.PanScreen(_gestures.PanDx, _gestures.PanDy);
                UpdateBrush();
            }
            else
            {
                if (_gestures.PanDx != 0f || _gestures.PanDy != 0f)
                    _rig.PanScreen(_gestures.PanDx, _gestures.PanDy);
                var at = new Vector2(_gestures.GestureX, _gestures.GestureY);
                if (_gestures.Tap) Select(at, longPress: false);
                if (_gestures.LongPress) Select(at, longPress: true);
                if (_gestures.DoubleTap) _rig.GlideTo(_rig.ScreenToWorld(at));
            }

            _rig.Tick(Time.unscaledDeltaTime);
            _terrainView.Tick(_cam, Time.unscaledTime);
            _propView.Tick(_cam, _terrainView, Time.unscaledTime);
            _fx.PixelsPerTile = _terrainView.PixelsPerTile;
            _fx.Tick(Time.unscaledTime);
            _audio.Tick(_cam, _terrainView, Time.unscaledTime);
            uint simTick = _clockQuery.IsEmpty ? 0u : (uint)_clockQuery.GetSingleton<WorldSim.Simulation.SimulationClock>().Tick;
            _creatureView.Tick(_em, _cam, _terrainView, simTick, Time.unscaledTime, Time.unscaledDeltaTime);
            if (Time.unscaledTime >= _nextUiRefresh) { _nextUiRefresh = Time.unscaledTime + 0.25f; RefreshLifeUi(); } // §12.4: <=4 Hz
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
            if (!map.IsCreated) return;
            if (map.Version == _shownVersion)
            {
                if (map.EditVersion != _shownEditVersion)
                {
                    _shownEditVersion = map.EditVersion;
                    _map = map;
                    _terrainView.MarkDirty(map, map.DirtyRect, Time.unscaledTime);
                    _hud.SetTitle($"WorldSim   seed 0x{map.Seed:X}   {map.Width}x{map.Height}\nedited world");
                }
                return;
            }
            _map = map;
            _shownVersion = map.Version;
            _shownEditVersion = map.EditVersion;

            _terrainView.Build(map, _cam);
            _rig.SetWorld(map.Width, map.Height);
            SpawnStartingLife(map);
            _selection.enabled = false;
            _hud.HideInfo();
            _hud.SetTitle($"WorldSim   seed 0x{map.Seed:X}   {map.Width}x{map.Height}\nworld hash 0x{map.Hash:X16}");
            SaveSeed(map.Seed);
        }

        /// <summary>A new world starts with life (Playable Alpha step 2): peoples, herds, predators, birds and fish.</summary>
        void SpawnStartingLife(WorldMap map)
        {
            if (map.Version == _populatedVersion || map.Settings.Blank != 0 || _lifeQuery.IsEmpty) return;
            _populatedVersion = map.Version;
            var plan = StartingLife.Plan(map.Tiles.ToArray(), map.Width, map.Height, map.Seed);
            Entity q = _lifeQuery.GetSingletonEntity();
            var buffer = _em.GetBuffer<SpawnCreatureCommand>(q);
            foreach (var sp in plan)
                buffer.Add(new SpawnCreatureCommand { Species = sp.Species, Tile = new Unity.Mathematics.int2(sp.X, sp.Y) });
            Debug.Log($"[WorldSim] Starting life: {plan.Count} creatures queued");
        }

        void Select(Vector2 screen, bool longPress)
        {
            Vector3 w = _rig.ScreenToWorld(screen);
            if (CreatureView.FindNearest(_em, new Vector2(w.x, w.y - 0.5f), 1.2f, out Entity creature))
            {
                _selectedCreature = creature;
                _selection.enabled = false;
                RefreshLifeUi();
                return;
            }
            _selectedCreature = Entity.Null;
            int x = Mathf.FloorToInt(w.x), y = Mathf.FloorToInt(PackTerrainView.WorldToTileY(w.y));
            if (!_map.InBounds(x, y)) { _selection.enabled = false; _hud.HideInfo(); return; }

            // Re-read the singleton: the array handle is only valid for the current world version.
            WorldMap map = _mapQuery.GetSingleton<WorldMap>();
            if (map.Version != _shownVersion) return;
            TileData t = map.Get(x, y);

            _selection.transform.position = new Vector3(x, PackTerrainView.TileToWorldY(y + 1), 0f);
            _selection.transform.localScale = Vector3.one;
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

        void UpdateSpawn()
        {
            if (!_gestures.IsSingleFingerDown) { _lastSpawnX = int.MinValue; return; }
            Vector3 w = _rig.ScreenToWorld(new Vector2(_gestures.PrimaryX, _gestures.PrimaryY));
            int x = Mathf.FloorToInt(w.x), y = Mathf.FloorToInt(PackTerrainView.WorldToTileY(w.y));
            if (!_map.InBounds(x, y)) return;
            float now = Time.unscaledTime;
            bool moved = Mathf.Abs(x - _lastSpawnX) + Mathf.Abs(y - _lastSpawnY) >= 2;
            if (!moved && now - _lastSpawnTime < 0.35f) return;
            _lastSpawnX = x; _lastSpawnY = y; _lastSpawnTime = now;
            Entity q = _lifeQuery.GetSingletonEntity();
            _em.GetBuffer<SpawnCreatureCommand>(q).Add(new SpawnCreatureCommand { Species = _spawn.Value, Tile = new Unity.Mathematics.int2(x, y) });
        }

        void TogglePause()
        {
            _paused = !_paused;
            var group = World.DefaultGameObjectInjectionWorld.GetExistingSystemManaged<WorldSim.Simulation.SimulationTickGroup>();
            if (group != null) group.Enabled = !_paused;
            UpdateTimeLabels();
        }

        void CycleSpeed()
        {
            _speedIndex = (_speedIndex + 1) % Speeds.Length;
            var group = World.DefaultGameObjectInjectionWorld.GetExistingSystemManaged<WorldSim.Simulation.SimulationTickGroup>();
            if (group != null) group.SetTickSeconds(WorldSim.Simulation.SimulationTickGroup.DefaultTickSeconds / Speeds[_speedIndex]);
            UpdateTimeLabels();
        }

        void UpdateTimeLabels()
        {
            _hud.SetTimeLabels(_paused ? "Play" : "Pause", $"Speed x{Speeds[_speedIndex]:0}");
            _hud.SetTimeState(_paused, _speedIndex);
        }

        void SelectSpeed(int index)
        {
            _speedIndex = Mathf.Clamp(index, 0, Speeds.Length - 1);
            if (_paused) TogglePause();
            var group = World.DefaultGameObjectInjectionWorld.GetExistingSystemManaged<WorldSim.Simulation.SimulationTickGroup>();
            if (group != null) group.SetTickSeconds(WorldSim.Simulation.SimulationTickGroup.DefaultTickSeconds / Speeds[_speedIndex]);
            UpdateTimeLabels();
        }

        /// <summary>Population in the title and the selected creature's panel, refreshed at most 4x/s.</summary>
        void RefreshLifeUi()
        {
            if (_lifeQuery.IsEmpty || _map.Version == 0) return;
            LifeState life = _lifeQuery.GetSingleton<LifeState>();
            _hud.SetTitle($"seed 0x{_map.Seed:X}   {_map.Width}x{_map.Height}   population {life.Population}   peoples {life.Peoples}\n" +
                          _stats.Line);

            if (_selectedCreature == Entity.Null) return;
            if (!_em.Exists(_selectedCreature) || !_em.HasComponent<Creature>(_selectedCreature))
            {
                _hud.ShowInfo("This creature has died.");
                _selectedCreature = Entity.Null;
                return;
            }
            Creature c = _em.GetComponentData<Creature>(_selectedCreature);
            Vitals v = _em.GetComponentData<Vitals>(_selectedCreature);
            Brain b = _em.GetComponentData<Brain>(_selectedCreature);
            TraitSet traits = _em.GetComponentData<CreatureTraits>(_selectedCreature).Set;
            uint tick = (uint)_clockQuery.GetSingleton<WorldSim.Simulation.SimulationClock>().Tick;
            string name = _em.HasComponent<CreatureName>(_selectedCreature)
                ? _em.GetComponentData<CreatureName>(_selectedCreature).Value.ToString() + ", " : "";
            int years = (int)((tick - c.BornTick) / 600);
            var list = new List<string>();
            for (int i = 0; i < (int)Trait.Count; i++) if (traits.Has((Trait)i)) list.Add(((Trait)i).ToString());
            _hud.ShowInfo($"{name}{c.Species} ({(c.Sex == 0 ? "female" : "male")}), {years} years   {b.Action}\n" +
                          $"health {v.Hp}/{v.MaxHp}   hunger {v.Hunger * 100 / 255}%   thirst {v.Thirst * 100 / 255}%   tired {v.Fatigue * 100 / 255}%\n" +
                          $"traits: {(list.Count == 0 ? "none" : string.Join(", ", list))}");
        }

        void OnToolChanged(WorldHud.ToolChoice? tool)
        {
            _tool = tool;
            _hud.HideInfo();
            if (_selection != null) _selection.enabled = false;
            _lastDabX = _lastDabY = int.MinValue;
        }

        void CycleBrush()
        {
            _brushIndex = (_brushIndex + 1) % BrushRadii.Length;
            PlayerPrefs.SetInt(BrushPrefKey, _brushIndex);
            PlayerPrefs.Save();
            UpdateBrushLabel();
        }

        void UpdateBrushLabel() => _hud.SetBrushSizeLabel($"Size {BrushRadii[_brushIndex] * 2 + 1}");

        /// <summary>
        /// While one finger is down in brush mode: queue a dab on the tile under it. Paint-type
        /// tools dab when the finger reaches a new tile; raise/lower keep dabbing while held.
        /// The brush outline follows the finger.
        /// </summary>
        void UpdateBrush()
        {
            int r = BrushRadii[_brushIndex];
            if (!_gestures.IsSingleFingerDown)
            {
                _selection.enabled = false;
                _lastDabX = _lastDabY = int.MinValue;
                return;
            }
            Vector3 w = _rig.ScreenToWorld(new Vector2(_gestures.PrimaryX, _gestures.PrimaryY));
            int x = Mathf.FloorToInt(w.x), y = Mathf.FloorToInt(PackTerrainView.WorldToTileY(w.y));
            _selection.enabled = true;
            _selection.transform.position = new Vector3(x - r, PackTerrainView.TileToWorldY(y + r + 1), 0f);
            _selection.transform.localScale = new Vector3(2 * r + 1, 2 * r + 1, 1f);
            if (!_map.InBounds(x, y)) return;

            WorldHud.ToolChoice tool = _tool.Value;
            bool continuous = tool.Tool == TerrainTool.Raise || tool.Tool == TerrainTool.Lower || tool.Tool == TerrainTool.Flatten;
            bool moved = x != _lastDabX || y != _lastDabY;
            float now = Time.unscaledTime;
            if (!moved && !(continuous && now - _lastDabTime >= DabInterval)) return;
            _lastDabX = x; _lastDabY = y; _lastDabTime = now;

            Entity q = _editQuery.GetSingletonEntity();
            _em.GetBuffer<TerrainEditCommand>(q).Add(new TerrainEditCommand
            {
                Edit = new TerrainEdit { Tool = tool.Tool, Biome = tool.Biome, X = x, Y = y, Radius = r },
            });
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

        void UpdateSizeLabel()
        {
            _hud.SetSizeLabel($"{SizeNames[_sizeIndex]} {Sizes[_sizeIndex]}");
            _hud.SetWorldOptionLabels(LandOptions[_land].name, ClimateOptions[_climate].name,
                MountainOptions[_mountains].name, BlankOptions[_blank].name);
        }

        void Cycle(ref int index, int count, string prefKey)
        {
            index = (index + 1) % count;
            PlayerPrefs.SetInt(prefKey, index);
            PlayerPrefs.Save();
            UpdateSizeLabel();
        }

        WorldGenSettings CurrentSettings => new WorldGenSettings
        {
            LandBias = LandOptions[_land].v,
            Temperature = ClimateOptions[_climate].v,
            Mountains = MountainOptions[_mountains].v,
            Blank = BlankOptions[_blank].v,
        };

        void RequestWorld(ulong seed, int size)
        {
            Entity e = _em.CreateEntity(typeof(WorldGenRequest));
            _em.SetComponentData(e, new WorldGenRequest { Seed = seed, Width = size, Height = size, Settings = CurrentSettings });
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
