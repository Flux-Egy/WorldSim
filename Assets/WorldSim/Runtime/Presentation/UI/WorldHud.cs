using System;
using UnityEngine;
using UnityEngine.UI;

namespace WorldSim.Presentation.UI
{
    /// <summary>
    /// Stage 2/3 HUD built in code (no prefabs yet): a top bar with seed and world hash, a
    /// button row (notice, map size, new world), a bottom panel for the selected tile, and the
    /// first-launch fiction notice (plan A3). Follows §12.1: Canvas Scaler "Scale With Screen
    /// Size" (1080x1920 reference), anchors pinned to edges, and safe-area handling.
    /// Text uses uGUI's built-in "LegacyRuntime.ttf" (the font uGUI's Text itself falls back to);
    /// TextMeshPro needs its Essential Resources imported, which this headless project has not done.
    /// </summary>
    public sealed class WorldHud
    {
        public const string FictionNotice =
            "WorldSim is a work of fiction.\n\n" +
            "Every creed, belief, ritual, kingdom, name and character in this game is invented " +
            "by the game itself. None of them represents, describes or refers to any real " +
            "religion, belief, people or place. Any resemblance is coincidental.\n\n" +
            "This is only a game.";

        readonly RectTransform _safeRoot;
        readonly RectTransform _topBar;
        readonly RectTransform _infoPanel;
        readonly RectTransform _noticeOverlay;
        readonly Text _title;
        readonly Text _info;
        readonly Text _sizeLabel;
        readonly Font _font;
        Rect _appliedSafeArea;

        public event Action NewWorldClicked;
        public event Action SizeClicked;
        public event Action NoticeAccepted;

        public bool IsNoticeOpen => _noticeOverlay.gameObject.activeSelf;

        public WorldHud(Transform parent)
        {
            var canvasGo = new GameObject("HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGo.transform.SetParent(parent, false);
            var canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080, 1920);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            _font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            _safeRoot = NewRect("SafeArea", canvasGo.transform);
            Stretch(_safeRoot);

            // ---- Top bar: title row + button row ----
            _topBar = NewRect("TopBar", _safeRoot);
            _topBar.anchorMin = new Vector2(0, 1); _topBar.anchorMax = new Vector2(1, 1);
            _topBar.pivot = new Vector2(0.5f, 1); _topBar.sizeDelta = new Vector2(0, 230);
            AddImage(_topBar, new Color(0.06f, 0.08f, 0.12f, 0.82f));

            _title = AddText(_topBar, 34, TextAnchor.MiddleLeft);
            var titleRt = _title.rectTransform;
            titleRt.anchorMin = new Vector2(0, 1); titleRt.anchorMax = new Vector2(1, 1);
            titleRt.pivot = new Vector2(0.5f, 1);
            titleRt.offsetMin = new Vector2(28, -110); titleRt.offsetMax = new Vector2(-28, -6);

            AddButton(_topBar, "New world", new Color(0.22f, 0.52f, 0.34f), 300, -20, () => NewWorldClicked?.Invoke());
            _sizeLabel = AddButton(_topBar, "Size", new Color(0.24f, 0.36f, 0.56f), 300, -340, () => SizeClicked?.Invoke());
            AddButton(_topBar, "Notice", new Color(0.32f, 0.32f, 0.38f), 200, -660, ShowNotice);

            // ---- Bottom info panel ----
            _infoPanel = NewRect("TileInfo", _safeRoot);
            _infoPanel.anchorMin = new Vector2(0, 0); _infoPanel.anchorMax = new Vector2(1, 0);
            _infoPanel.pivot = new Vector2(0.5f, 0); _infoPanel.sizeDelta = new Vector2(0, 250);
            AddImage(_infoPanel, new Color(0.06f, 0.08f, 0.12f, 0.82f));
            _info = AddText(_infoPanel, 36, TextAnchor.MiddleLeft);
            _info.rectTransform.anchorMin = Vector2.zero; _info.rectTransform.anchorMax = Vector2.one;
            _info.rectTransform.offsetMin = new Vector2(28, 12); _info.rectTransform.offsetMax = new Vector2(-28, -12);
            _infoPanel.gameObject.SetActive(false);

            // ---- Fiction notice (modal; blocks world input while open) ----
            _noticeOverlay = NewRect("FictionNotice", _safeRoot);
            Stretch(_noticeOverlay);
            AddImage(_noticeOverlay, new Color(0f, 0f, 0f, 0.86f)); // raycast target: swallows UI clicks
            var card = NewRect("Card", _noticeOverlay);
            card.anchorMin = new Vector2(0.06f, 0.25f); card.anchorMax = new Vector2(0.94f, 0.75f);
            card.offsetMin = Vector2.zero; card.offsetMax = Vector2.zero;
            AddImage(card, new Color(0.10f, 0.13f, 0.19f, 1f));
            var noticeText = AddText(card, 40, TextAnchor.UpperLeft);
            noticeText.rectTransform.anchorMin = Vector2.zero; noticeText.rectTransform.anchorMax = Vector2.one;
            noticeText.rectTransform.offsetMin = new Vector2(44, 170); noticeText.rectTransform.offsetMax = new Vector2(-44, -44);
            noticeText.text = FictionNotice;
            var ok = NewRect("Accept", card);
            ok.anchorMin = new Vector2(0.5f, 0); ok.anchorMax = new Vector2(0.5f, 0);
            ok.pivot = new Vector2(0.5f, 0); ok.sizeDelta = new Vector2(520, 120);
            ok.anchoredPosition = new Vector2(0, 36);
            var okImg = AddImage(ok, new Color(0.22f, 0.52f, 0.34f));
            var okBtn = ok.gameObject.AddComponent<Button>();
            okBtn.targetGraphic = okImg;
            okBtn.onClick.AddListener(() => { _noticeOverlay.gameObject.SetActive(false); NoticeAccepted?.Invoke(); });
            var okLabel = AddText(ok, 42, TextAnchor.MiddleCenter);
            Stretch(okLabel.rectTransform);
            okLabel.text = "I understand";
            _noticeOverlay.gameObject.SetActive(false);

            ApplySafeArea();
        }

        public void SetTitle(string text) => _title.text = text;
        public void SetSizeLabel(string text) => _sizeLabel.text = text;
        public void ShowNotice() => _noticeOverlay.gameObject.SetActive(true);

        public void ShowInfo(string text)
        {
            _info.text = text;
            _infoPanel.gameObject.SetActive(true);
        }

        public void HideInfo() => _infoPanel.gameObject.SetActive(false);

        /// <summary>True if a touch at this screen point belongs to the UI, not the world.</summary>
        public bool IsOverUi(Vector2 screenPoint)
        {
            if (IsNoticeOpen) return true;
            if (RectTransformUtility.RectangleContainsScreenPoint(_topBar, screenPoint, null)) return true;
            return _infoPanel.gameObject.activeSelf &&
                   RectTransformUtility.RectangleContainsScreenPoint(_infoPanel, screenPoint, null);
        }

        /// <summary>Call every frame: re-applies the safe area when rotation or the notch changes it.</summary>
        public void Tick()
        {
            if (Screen.safeArea != _appliedSafeArea) ApplySafeArea();
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

        /// <summary>Button in the top bar's lower row, right-aligned at <paramref name="x"/> from the right edge.</summary>
        Text AddButton(RectTransform bar, string label, Color color, float width, float x, Action onClick)
        {
            var rt = NewRect(label + "Button", bar);
            rt.anchorMin = new Vector2(1, 0); rt.anchorMax = new Vector2(1, 0);
            rt.pivot = new Vector2(1, 0); rt.sizeDelta = new Vector2(width, 96);
            rt.anchoredPosition = new Vector2(x, 14);
            var img = AddImage(rt, color);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.onClick.AddListener(() => onClick());
            var text = AddText(rt, 36, TextAnchor.MiddleCenter);
            Stretch(text.rectTransform);
            text.text = label;
            return text;
        }

        static RectTransform NewRect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero; rt.offsetMax = Vector2.zero;
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
