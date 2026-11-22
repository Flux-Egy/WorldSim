using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using WorldSim.Core;
using WorldSim.Core.Life;
using WorldSim.Core.Powers;
using WorldSim.Render;

namespace WorldSim.Presentation.UI
{
    /// <summary>
    /// HUD built in code (no prefabs yet): a slim top bar (world name, seed, hash), the selected
    /// tile panel, and a bottom toolbar with tabs and pixel-art icon buttons (icons from
    /// <see cref="IconLibrary"/>). Tabs for features that arrive in later Beta milestones say so
    /// instead of showing dead buttons. Also hosts the first-launch fiction notice (plan A3).
    /// Follows §12.1: Canvas Scaler "Scale With Screen Size" (1080x1920 reference), anchors pinned
    /// to edges, and safe-area handling. Text uses uGUI's built-in "LegacyRuntime.ttf".
    /// </summary>
    public sealed class WorldHud
    {
        public const string FictionNotice =
            "WorldSim is a work of fiction.\n\n" +
            "Every creed, belief, ritual, kingdom, name and character in this game is invented " +
            "by the game itself. None of them represents, describes or refers to any real " +
            "religion, belief, people or place. Any resemblance is coincidental.\n\n" +
            "This is only a game.";

        const float ToolbarHeight = 360f;

        readonly RectTransform _safeRoot, _topBar, _infoPanel, _toolbar, _noticeOverlay, _content;
        readonly Text _title, _info, _placeholder;
        readonly Font _font;
        readonly List<Image> _tabImages = new List<Image>();
        readonly Dictionary<Icon, Sprite> _icons = new Dictionary<Icon, Sprite>();
        Text _sizeLabel;
        Rect _appliedSafeArea;

        /// <summary>A terrain brush the player picked (Beta B2).</summary>
        public struct ToolChoice
        {
            public TerrainTool Tool;
            public Biome Biome;
            public string Label;
        }

        /// <summary>Raised with the chosen brush, or null when brushes are switched off.</summary>
        public event Action<ToolChoice?> ToolChanged;
        public event Action BrushSizeClicked;
        Text _brushSizeLabel;
        Image _selectedToolImage;

        /// <summary>Species to place with the finger (Beta B3), or null to stop spawning.</summary>
        public event Action<SpeciesId?> SpawnChanged;
        /// <summary>A power picked in the Powers tab (null = back to inspecting); the player then taps the map.</summary>
        public event Action<PowerKind?> PowerChanged;

        static readonly (PowerKind kind, string icon, string label)[] PowerButtons =
        {
            (PowerKind.Lightning, "picon_bolt", "Lightning"), (PowerKind.Meteor, "picon_meteor", "Meteor"),
            (PowerKind.Bomb, "picon_hazard", "Bomb"), (PowerKind.Missile, "picon_missile", "Missile"),
            (PowerKind.Nuke, "picon_nuke", "Nuke"), (PowerKind.Wildfire, "picon_fire", "Wildfire"),
            (PowerKind.Rain, "picon_rain", "Rain"), (PowerKind.Quake, "picon_quake", "Quake"),
            (PowerKind.Forest, "picon_tree", "Forest"), (PowerKind.Bless, "picon_bless", "Bless"),
            (PowerKind.Plague, "picon_plague", "Plague"), (PowerKind.SpawnPeople, "picon_human", "People"),
            (PowerKind.SpawnAnimals, "picon_sheep", "Animals"),
        };
        public event Action PauseClicked, SpeedClicked;
        /// <summary>Time bar: speed index into x1, x2, x5, x10.</summary>
        public event Action<int> SpeedSelected;
        static readonly string[] TimeLabels = { "II", "x1", "x2", "x5", "x10" };
        readonly List<Image> _timeImages = new List<Image>();

        /// <summary>Highlights the time bar: the pause button while paused, else the running speed.</summary>
        public void SetTimeState(bool paused, int speedIndex)
        {
            for (int i = 0; i < _timeImages.Count; i++) UiKit.Select(_timeImages[i], paused ? i == 0 : i == speedIndex + 1);
        }
        public event Action TimeLabelsRequested;
        Text _pauseLabel, _speedLabel;
        Image _selectedSpawnImage;

        public event Action NewWorldClicked;
        public event Action SizeClicked;
        public event Action LandClicked, ClimateClicked, MountainsClicked, BlankClicked;
        Text _landLabel, _climateLabel, _mountainsLabel, _blankLabel;
        public event Action NoticeAccepted;
        /// <summary>Settings > "Art test": show/hide the art pack check (developer).</summary>
        public event Action ArtTestClicked;

        public bool IsNoticeOpen => _noticeOverlay.gameObject.activeSelf;

        struct TabDef { public string Name; public Icon Icon; public string Milestone; }

        static readonly TabDef[] Tabs =
        {
            new TabDef { Name = "World", Icon = Icon.Globe, Milestone = null },
            new TabDef { Name = "Terrain", Icon = Icon.Mountain, Milestone = null },
            new TabDef { Name = "Life", Icon = Icon.People, Milestone = null },
            new TabDef { Name = "Nations", Icon = Icon.Castle, Milestone = "Villages, kingdoms and wars come next (Alpha step 3)." },
            new TabDef { Name = "Powers", Icon = Icon.Storm, Milestone = null },
            new TabDef { Name = "Settings", Icon = Icon.Gear, Milestone = null },
        };

        static readonly string[] TabIcons = { "icon_globe", "icon_pick", "picon_human", "icon_crown", "picon_bolt", "icon_gear" };

        readonly Canvas _canvas;

        /// <summary>Hides or shows the whole HUD (e.g. for the Art Lab's fixed-camera captures).</summary>
        public bool Visible { get => _canvas.enabled; set => _canvas.enabled = value; }

        /// <summary>Settings > "Art lab": fixed-camera sprite grid for pixel-exact comparisons (developer).</summary>
        public event Action ArtLabClicked;

        public WorldHud(Transform parent)
        {
            var canvasGo = new GameObject("HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGo.transform.SetParent(parent, false);
            _canvas = canvasGo.GetComponent<Canvas>();
            _canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080, 1920);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            _font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            _safeRoot = NewRect("SafeArea", canvasGo.transform);
            Stretch(_safeRoot);

            // ---- Top bar ----
            _topBar = NewRect("TopBar", _safeRoot);
            _topBar.anchorMin = new Vector2(0, 1); _topBar.anchorMax = new Vector2(1, 1);
            _topBar.pivot = new Vector2(0.5f, 1); _topBar.sizeDelta = new Vector2(0, 120);
            UiKit.Panel(_topBar, 0.45f, 0.92f);
            _title = AddText(_topBar, 32, TextAnchor.MiddleLeft);
            Fill(_title.rectTransform, 28, 6, -28, -6);

            // ---- Time bar (always visible, top right): pause and x1 x2 x5 x10 ----
            var timeBar = NewRect("TimeBar", _safeRoot);
            timeBar.anchorMin = timeBar.anchorMax = new Vector2(1, 1);
            timeBar.pivot = new Vector2(1, 1);
            timeBar.sizeDelta = new Vector2(TimeLabels.Length * 104 + 16, 96);
            timeBar.anchoredPosition = new Vector2(-12, -132);
            UiKit.Panel(timeBar, 0.45f, 0.9f);
            for (int i = 0; i < TimeLabels.Length; i++)
            {
                int slot = i;
                var b = NewRect("Time" + i, timeBar);
                b.anchorMin = b.anchorMax = new Vector2(0, 0.5f);
                b.pivot = new Vector2(0, 0.5f);
                b.sizeDelta = new Vector2(96, 76);
                b.anchoredPosition = new Vector2(10 + i * 104, 0);
                var img = UiKit.Button(b);
                _timeImages.Add(img);
                var btn = b.gameObject.AddComponent<Button>();
                btn.targetGraphic = img;
                btn.onClick.AddListener(() => { if (slot == 0) PauseClicked?.Invoke(); else SpeedSelected?.Invoke(slot - 1); });
                var t = AddText(b, 30, TextAnchor.MiddleCenter);
                Stretch(t.rectTransform);
                t.text = TimeLabels[i];
            }

            // ---- Bottom toolbar: tab strip + content ----
            _toolbar = NewRect("Toolbar", _safeRoot);
            _toolbar.anchorMin = new Vector2(0, 0); _toolbar.anchorMax = new Vector2(1, 0);
            _toolbar.pivot = new Vector2(0.5f, 0); _toolbar.sizeDelta = new Vector2(0, ToolbarHeight);
            UiKit.Panel(_toolbar, 0.55f, 0.97f);

            float tabW = 1f / Tabs.Length;
            for (int i = 0; i < Tabs.Length; i++)
            {
                int index = i;
                var tab = NewRect("Tab" + Tabs[i].Name, _toolbar);
                tab.anchorMin = new Vector2(i * tabW, 1); tab.anchorMax = new Vector2((i + 1) * tabW, 1);
                tab.pivot = new Vector2(0.5f, 1); tab.sizeDelta = new Vector2(-8, 96);
                tab.anchoredPosition = new Vector2(0, -10);
                var img = UiKit.Button(tab);
                _tabImages.Add(img);
                var btn = tab.gameObject.AddComponent<Button>();
                btn.targetGraphic = img;
                btn.onClick.AddListener(() => SelectTab(index));
                AddPackIcon(tab, TabIcons[i], 52, new Vector2(0, 14));
                var label = AddText(tab, 22, TextAnchor.LowerCenter);
                Fill(label.rectTransform, 0, 2, 0, 0);
                label.text = Tabs[i].Name;
            }

            _content = NewRect("Content", _toolbar);
            _content.anchorMin = Vector2.zero; _content.anchorMax = Vector2.one;
            _content.offsetMin = new Vector2(16, 12); _content.offsetMax = new Vector2(-16, -116);
            _placeholder = AddText(_content, 34, TextAnchor.MiddleCenter);
            Stretch(_placeholder.rectTransform);
            _placeholder.color = new Color(0.75f, 0.80f, 0.85f);

            // ---- Selected tile panel (above the toolbar) ----
            _infoPanel = NewRect("TileInfo", _safeRoot);
            _infoPanel.anchorMin = new Vector2(0, 0); _infoPanel.anchorMax = new Vector2(1, 0);
            _infoPanel.pivot = new Vector2(0.5f, 0); _infoPanel.sizeDelta = new Vector2(0, 190);
            _infoPanel.anchoredPosition = new Vector2(0, ToolbarHeight);
            UiKit.Panel(_infoPanel, 0.45f, 0.94f);
            _info = AddText(_infoPanel, 32, TextAnchor.MiddleLeft);
            Fill(_info.rectTransform, 28, 10, -28, -10);
            _infoPanel.gameObject.SetActive(false);

            // ---- Fiction notice (modal) ----
            _noticeOverlay = NewRect("FictionNotice", _safeRoot);
            Stretch(_noticeOverlay);
            AddImage(_noticeOverlay, new Color(0f, 0f, 0f, 0.86f));
            var card = NewRect("Card", _noticeOverlay);
            card.anchorMin = new Vector2(0.06f, 0.25f); card.anchorMax = new Vector2(0.94f, 0.75f);
            card.offsetMin = Vector2.zero; card.offsetMax = Vector2.zero;
            UiKit.Panel(card, 0.6f, 1f);
            var noticeText = AddText(card, 40, TextAnchor.UpperLeft);
            Fill(noticeText.rectTransform, 44, 170, -44, -44);
            noticeText.text = FictionNotice;
            var ok = NewRect("Accept", card);
            ok.anchorMin = new Vector2(0.5f, 0); ok.anchorMax = new Vector2(0.5f, 0);
            ok.pivot = new Vector2(0.5f, 0); ok.sizeDelta = new Vector2(520, 120);
            ok.anchoredPosition = new Vector2(0, 36);
            var okImg = UiKit.Button(ok);
            var okBtn = ok.gameObject.AddComponent<Button>();
            okBtn.targetGraphic = okImg;
            okBtn.onClick.AddListener(() => { _noticeOverlay.gameObject.SetActive(false); NoticeAccepted?.Invoke(); });
            var okLabel = AddText(ok, 42, TextAnchor.MiddleCenter);
            Stretch(okLabel.rectTransform);
            okLabel.text = "I understand";
            _noticeOverlay.gameObject.SetActive(false);

            SelectTab(0);
            ApplySafeArea();
        }

        public void SetTitle(string text) => _title.text = text;
        public void SetSizeLabel(string text) { if (_sizeLabel != null) _sizeLabel.text = text; }

        /// <summary>Labels of the World tab's generation-setting buttons.</summary>
        public void SetWorldOptionLabels(string land, string climate, string mountains, string blank)
        {
            if (_landLabel != null) _landLabel.text = land;
            if (_climateLabel != null) _climateLabel.text = climate;
            if (_mountainsLabel != null) _mountainsLabel.text = mountains;
            if (_blankLabel != null) _blankLabel.text = blank;
        }
        public void ShowNotice() => _noticeOverlay.gameObject.SetActive(true);
        public void ShowInfo(string text) { _info.text = text; _infoPanel.gameObject.SetActive(true); }
        public void HideInfo() => _infoPanel.gameObject.SetActive(false);

        /// <summary>True if a touch at this screen point belongs to the UI, not the world.</summary>
        public bool IsOverUi(Vector2 screenPoint)
        {
            if (IsNoticeOpen) return true;
            if (RectTransformUtility.RectangleContainsScreenPoint(_topBar, screenPoint, null)) return true;
            if (RectTransformUtility.RectangleContainsScreenPoint(_toolbar, screenPoint, null)) return true;
            return _infoPanel.gameObject.activeSelf &&
                   RectTransformUtility.RectangleContainsScreenPoint(_infoPanel, screenPoint, null);
        }

        /// <summary>Call every frame: re-applies the safe area when rotation or the notch changes it.</summary>
        public void Tick()
        {
            if (Screen.safeArea != _appliedSafeArea) ApplySafeArea();
        }

        void SelectTab(int index)
        {
            for (int i = 0; i < _tabImages.Count; i++) UiKit.Select(_tabImages[i], i == index);
            for (int i = _content.childCount - 1; i >= 0; i--)
            {
                var child = _content.GetChild(i);
                if (child != _placeholder.transform) UnityEngine.Object.Destroy(child.gameObject);
            }
            _sizeLabel = null;
            _landLabel = _climateLabel = _mountainsLabel = _blankLabel = null;
            _brushSizeLabel = null;
            _selectedToolImage = null;
            ToolChanged?.Invoke(null); // switching tabs always returns to inspect mode
            SpawnChanged?.Invoke(null);
            PowerChanged?.Invoke(null);
            _pauseLabel = _speedLabel = null;
            _selectedSpawnImage = null;
            _placeholder.text = Tabs[index].Milestone ?? "";
            if (index == 0)
            {
                RectTransform row = BuildScrollRow(0f);
                AddRowButton(row, GetIconSprite(Icon.Globe), "New world", () => NewWorldClicked?.Invoke());
                _sizeLabel = AddRowButton(row, GetIconSprite(Icon.Resize), "Size", () => SizeClicked?.Invoke());
                _landLabel = AddRowButton(row, GetSwatchSprite(Biome.Meadow), "Land", () => LandClicked?.Invoke());
                _climateLabel = AddRowButton(row, GetSwatchSprite(Biome.Snow), "Climate", () => ClimateClicked?.Invoke());
                _mountainsLabel = AddRowButton(row, GetIconSprite(Icon.Mountain), "Mountains", () => MountainsClicked?.Invoke());
                _blankLabel = AddRowButton(row, GetSwatchSprite(Biome.DeepWater), "Generated", () => BlankClicked?.Invoke());
                AddRowButton(row, GetIconSprite(Icon.Info), "Notice", ShowNotice);
                SizeLabelRequested?.Invoke();
            }
            else if (index == 1)
            {
                BuildTerrainPalette();
            }
            else if (index == 5)
            {
                // Developer checks until the real Settings screen (B8).
                RectTransform row = BuildScrollRow(0f);
                AddRowButton(row, GetIconSprite(Icon.Gear), "Art test", () => ArtTestClicked?.Invoke());
                AddRowButton(row, GetIconSprite(Icon.Gear), "Art lab", () => ArtLabClicked?.Invoke());
            }
            else if (index == 4)
            {
                RectTransform row = BuildScrollRow(0f);
                foreach (var pw in PowerButtons)
                {
                    PowerKind kind = pw.kind;
                    AddSelectableButton(row, UiKit.Icon(pw.icon), pw.label, on => PowerChanged?.Invoke(on ? kind : (PowerKind?)null));
                }
            }
            else if (index == 2)
            {
                RectTransform row = BuildScrollRow(0f);
                _pauseLabel = AddRowButton(row, GetIconSprite(Icon.Pause), "Pause", () => PauseClicked?.Invoke());
                _speedLabel = AddRowButton(row, GetIconSprite(Icon.Fast), "Speed", () => SpeedClicked?.Invoke());
                foreach (SpeciesId id in SpeciesTable.All)
                {
                    SpeciesId species = id;
                    AddSelectableButton(row, GetCreatureSprite(id), id.ToString(),
                        on => SpawnChanged?.Invoke(on ? species : (SpeciesId?)null));
                }
                TimeLabelsRequested?.Invoke();
            }
        }

        /// <summary>Raised when the Terrain tab is rebuilt, so the owner can refill the brush size label.</summary>
        public event Action BrushSizeLabelRequested;

        public void SetBrushSizeLabel(string text) { if (_brushSizeLabel != null) _brushSizeLabel.text = text; }

        static readonly (TerrainTool tool, Biome biome, Icon icon, string label)[] TerrainTools =
        {
            (TerrainTool.Raise, Biome.Meadow, Icon.Raise, "Raise"),
            (TerrainTool.Lower, Biome.Meadow, Icon.Lower, "Lower"),
            (TerrainTool.Flatten, Biome.Meadow, Icon.Flatten, "Flatten"),
            (TerrainTool.PlantTrees, Biome.Meadow, Icon.Tree, "Trees"),
            (TerrainTool.ClearDecorations, Biome.Meadow, Icon.Eraser, "Clear"),
        };

        static readonly (Biome biome, string label)[] PaintableBiomes =
        {
            (Biome.DeepWater, "Ocean"), (Biome.ShallowWater, "Shallows"), (Biome.Beach, "Sand"), (Biome.Meadow, "Grass"),
            (Biome.Forest, "Forest"), (Biome.BirchForest, "Birch"), (Biome.Jungle, "Jungle"), (Biome.Savanna, "Savanna"),
            (Biome.DesertDunes, "Desert"), (Biome.Swamp, "Swamp"), (Biome.PineTaiga, "Taiga"), (Biome.Tundra, "Tundra"),
            (Biome.Snow, "Snow"), (Biome.Mountain, "Mountain"), (Biome.Lava, "Lava"), (Biome.EmberWastes, "Embers"),
            (Biome.CrystalCaves, "Crystal"), (Biome.FungalGrove, "Fungal"), (Biome.Glimmerwood, "Glimmer"),
            (Biome.CoralShallows, "Coral"), (Biome.FlowerField, "Flowers"), (Biome.Steppe, "Steppe"),
            (Biome.Badlands, "Badlands"), (Biome.SaltFlats, "Salt"), (Biome.Glacier, "Glacier"),
            (Biome.RockyHighland, "Highland"), (Biome.Volcanic, "Volcanic"), (Biome.AshWaste, "Ash"),
            (Biome.Farmland, "Farmland"),
        };

        void BuildTerrainPalette()
        {
            // Brush size (fixed at the left) + horizontally scrolling tools and biome swatches.
            _brushSizeLabel = AddToolButton(0, Icon.Brush, "Size", () => BrushSizeClicked?.Invoke());
            BrushSizeLabelRequested?.Invoke();

            RectTransform row = BuildScrollRow(196f);

            foreach (var t in TerrainTools)
            {
                var choice = new ToolChoice { Tool = t.tool, Biome = t.biome, Label = t.label };
                AddPaletteButton(row, GetIconSprite(t.icon), t.label, choice);
            }
            foreach (var b in PaintableBiomes)
            {
                var choice = new ToolChoice { Tool = TerrainTool.PaintBiome, Biome = b.biome, Label = b.label };
                AddPaletteButton(row, GetSwatchSprite(b.biome), b.label, choice);
            }
        }

        /// <summary>A horizontally scrolling row of buttons filling the content area (left inset in px).</summary>
        RectTransform BuildScrollRow(float leftInset)
        {
            var viewport = NewRect("RowViewport", _content);
            viewport.anchorMin = Vector2.zero; viewport.anchorMax = Vector2.one;
            viewport.offsetMin = new Vector2(leftInset, 0); viewport.offsetMax = Vector2.zero;
            viewport.gameObject.AddComponent<RectMask2D>();
            AddImage(viewport, new Color(0, 0, 0, 0.001f)); // catches drags between buttons
            var scroll = viewport.gameObject.AddComponent<ScrollRect>();
            scroll.horizontal = true; scroll.vertical = false;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 30f;

            var row = NewRect("Row", viewport);
            row.anchorMin = new Vector2(0, 0); row.anchorMax = new Vector2(0, 1);
            row.pivot = new Vector2(0, 0.5f);
            var layout = row.gameObject.AddComponent<HorizontalLayoutGroup>();
            layout.spacing = 14; layout.childAlignment = TextAnchor.MiddleLeft;
            layout.childControlWidth = false; layout.childControlHeight = false;
            layout.childForceExpandWidth = false; layout.childForceExpandHeight = false;
            var fitter = row.gameObject.AddComponent<ContentSizeFitter>();
            fitter.horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
            scroll.content = row;
            scroll.viewport = viewport;
            return row;
        }

        /// <summary>Plain action button in a scroll row; returns its label for live updates.</summary>
        Text AddRowButton(RectTransform row, Sprite icon, string label, Action onClick)
        {
            var rt = NewRect(label + "Button", row);
            rt.sizeDelta = new Vector2(160, 200);
            var img = UiKit.Button(rt);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.onClick.AddListener(() => onClick());
            var iconRt = NewRect("Icon", rt);
            iconRt.anchorMin = iconRt.anchorMax = new Vector2(0.5f, 0.5f);
            iconRt.sizeDelta = new Vector2(88, 88);
            iconRt.anchoredPosition = new Vector2(0, 26);
            var iconImg = iconRt.gameObject.AddComponent<Image>();
            iconImg.sprite = icon; iconImg.raycastTarget = false; iconImg.preserveAspect = true;
            var text = AddText(rt, 24, TextAnchor.LowerCenter);
            Fill(text.rectTransform, 2, 8, -2, 0);
            text.text = label;
            return text;
        }

        public void SetTimeLabels(string pause, string speed)
        {
            if (_pauseLabel != null) _pauseLabel.text = pause;
            if (_speedLabel != null) _speedLabel.text = speed;
        }

        /// <summary>Toggle button: one selected per row; tapping the selected one switches it off.</summary>
        void AddSelectableButton(RectTransform row, Sprite icon, string label, Action<bool> onToggle)
        {
            Text t = AddRowButton(row, icon, label, () => { });
            var img = t.transform.parent.GetComponent<Image>();
            var btn = t.transform.parent.GetComponent<Button>();
            btn.onClick.RemoveAllListeners();
            btn.onClick.AddListener(() =>
            {
                bool deselect = _selectedSpawnImage == img;
                if (_selectedSpawnImage != null) UiKit.Select(_selectedSpawnImage, false);
                _selectedSpawnImage = deselect ? null : img;
                if (!deselect) UiKit.Select(img, true);
                onToggle(!deselect);
            });
        }

        readonly Dictionary<SpeciesId, Sprite> _creatureIcons = new Dictionary<SpeciesId, Sprite>();

        Sprite GetCreatureSprite(SpeciesId id)
        {
            if (_creatureIcons.TryGetValue(id, out var s)) return s;
            // Pack portrait for animals (portrait_a_sheep_32...), the first idle frame for peoples and the rest.
            string key = WorldSim.Render.Art.CreatureArt.PackKey(id);
            string prefix = id == SpeciesId.Bird ? "c_" : id == SpeciesId.Fish ? "s_" : "a_";
            var db = WorldSim.Presentation.Art.WorldSimArtDB.Instance;
            s = WorldSim.Render.Art.CreatureArt.IsPerson(id) ? null : db.GetSprite("portrait_" + prefix + key + "_32");
            if (s == null)
            {
                string anim = WorldSim.Render.Art.CreatureArt.Resolve(id, WorldSim.Render.Art.CreaturePose.Idle, false, true,
                                                                      WorldSim.Render.Art.Era.Medieval, false, out bool isAnim);
                if (isAnim && db.TryGetAnim(anim, out var a) && a.Frames.Length > 0) s = db.GetSprite(a.Frames[0]);
                else if (!isAnim) s = db.GetSprite(anim);
            }
            _creatureIcons[id] = s;
            return s;
        }

        void AddPaletteButton(RectTransform row, Sprite icon, string label, ToolChoice choice)
        {
            var rt = NewRect(label + "Tool", row);
            rt.sizeDelta = new Vector2(150, 200);
            var img = UiKit.Button(rt);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.onClick.AddListener(() =>
            {
                bool deselect = _selectedToolImage == img;
                if (_selectedToolImage != null) UiKit.Select(_selectedToolImage, false);
                _selectedToolImage = deselect ? null : img;
                if (!deselect) UiKit.Select(img, true);
                ToolChanged?.Invoke(deselect ? (ToolChoice?)null : choice);
            });
            var iconRt = NewRect("Icon", rt);
            iconRt.anchorMin = iconRt.anchorMax = new Vector2(0.5f, 0.5f);
            iconRt.sizeDelta = new Vector2(88, 88);
            iconRt.anchoredPosition = new Vector2(0, 26);
            var iconImg = iconRt.gameObject.AddComponent<Image>();
            iconImg.sprite = icon; iconImg.raycastTarget = false; iconImg.preserveAspect = true;
            var text = AddText(rt, 24, TextAnchor.LowerCenter);
            Fill(text.rectTransform, 2, 8, -2, 0);
            text.text = label;
        }

        readonly Dictionary<Biome, Sprite> _swatches = new Dictionary<Biome, Sprite>();

        /// <summary>16x16 swatch: the biome colour with a light speckle and a dark frame.</summary>
        Sprite GetSwatchSprite(Biome b)
        {
            if (_swatches.TryGetValue(b, out var s)) return s;
            int n = IconLibrary.Size;
            var px = new uint[n * n];
            uint c = TerrainPainter.BaseColor(b), frame = Rgba.Pack(24, 22, 30);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    bool edge = x == 1 || y == 1 || x == n - 2 || y == n - 2;
                    bool outside = x == 0 || y == 0 || x == n - 1 || y == n - 1;
                    px[y * n + x] = outside ? 0u : edge ? frame : ((x * 7 + y * 3) % 11 == 0 ? Rgba.Shift(c, 22) : c);
                }
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
            tex.SetPixelData(px, 0);
            tex.Apply(false, true);
            s = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);
            _swatches[b] = s;
            return s;
        }

        /// <summary>Raised when the World tab is rebuilt, so the owner can refill the size label.</summary>
        public event Action SizeLabelRequested;

        Text AddToolButton(int slot, Icon icon, string label, Action onClick)
        {
            const float w = 168f, h = 200f, gap = 14f;
            var rt = NewRect(label + "Button", _content);
            rt.anchorMin = new Vector2(0, 0.5f); rt.anchorMax = new Vector2(0, 0.5f);
            rt.pivot = new Vector2(0, 0.5f); rt.sizeDelta = new Vector2(w, h);
            rt.anchoredPosition = new Vector2(slot * (w + gap), 0);
            var img = UiKit.Button(rt);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.onClick.AddListener(() => onClick());
            AddIcon(rt, icon, 96, new Vector2(0, 26));
            var text = AddText(rt, 26, TextAnchor.LowerCenter);
            Fill(text.rectTransform, 4, 8, -4, 0);
            text.text = label;
            return text;
        }

        void AddPackIcon(RectTransform parent, string icon, float size, Vector2 offset)
        {
            var rt = NewRect("Icon", parent);
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(size, size);
            rt.anchoredPosition = offset;
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = UiKit.Icon(icon);
            img.raycastTarget = false;
            img.preserveAspect = true;
        }

        void AddIcon(RectTransform parent, Icon icon, float size, Vector2 offset)
        {
            var rt = NewRect("Icon", parent);
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(size, size);
            rt.anchoredPosition = offset;
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = GetIconSprite(icon);
            img.raycastTarget = false;
            img.preserveAspect = true;
        }

        Sprite GetIconSprite(Icon icon)
        {
            if (_icons.TryGetValue(icon, out var s)) return s;
            int n = IconLibrary.Size;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
            tex.SetPixelData(IconLibrary.Build(icon), 0);
            tex.Apply(false, true);
            s = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);
            _icons[icon] = s;
            return s;
        }

        void ApplySafeArea()
        {
            Rect safe = Screen.safeArea;
            _appliedSafeArea = safe;
            if (Screen.width <= 0 || Screen.height <= 0) return;
            _safeRoot.anchorMin = new Vector2(safe.xMin / Screen.width, safe.yMin / Screen.height);
            _safeRoot.anchorMax = new Vector2(safe.xMax / Screen.width, safe.yMax / Screen.height);
            _safeRoot.offsetMin = Vector2.zero;
            _safeRoot.offsetMax = Vector2.zero;
        }

        static RectTransform NewRect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        static void Stretch(RectTransform rt) => Fill(rt, 0, 0, 0, 0);

        static void Fill(RectTransform rt, float left, float bottom, float right, float top)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
            rt.offsetMin = new Vector2(left, bottom); rt.offsetMax = new Vector2(right, top);
        }

        static Image AddImage(RectTransform rt, Color color)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.color = color;
            return img;
        }

        Text AddText(RectTransform parent, int size, TextAnchor anchor)
        {
            var rt = NewRect("Text", parent);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = _font;
            t.fontSize = size;
            t.alignment = anchor;
            t.color = new Color(0.93f, 0.95f, 0.98f);
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }
    }
}
