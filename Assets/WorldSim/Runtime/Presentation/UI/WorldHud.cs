using System;
using UnityEngine;
using UnityEngine.UI;

namespace WorldSim.Presentation.UI
{
    /// <summary>
    /// Minimal Stage 2/3 HUD built in code (no prefabs yet): top bar with seed, world hash and
    /// "New world"; bottom panel with the selected tile. Follows §12.1: Canvas Scaler "Scale With
    /// Screen Size" (1080x1920 reference), anchors pinned to edges, and safe-area handling.
    /// Text uses uGUI's built-in "LegacyRuntime.ttf" (the same font uGUI's Text falls back to);
    /// TextMeshPro needs its Essential Resources imported, which this headless project has not done.
    /// </summary>
    public sealed class WorldHud
    {
        readonly RectTransform _safeRoot;
        readonly RectTransform _topBar;
        readonly RectTransform _infoPanel;
        readonly Text _title;
        readonly Text _info;
        Rect _appliedSafeArea;

        public event Action NewWorldClicked;

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

            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            _safeRoot = NewRect("SafeArea", canvasGo.transform);
            Stretch(_safeRoot);

            // Top bar
            _topBar = NewRect("TopBar", _safeRoot);
            _topBar.anchorMin = new Vector2(0, 1); _topBar.anchorMax = new Vector2(1, 1);
            _topBar.pivot = new Vector2(0.5f, 1); _topBar.sizeDelta = new Vector2(0, 150);
            AddImage(_topBar, new Color(0.06f, 0.08f, 0.12f, 0.82f));

            _title = AddText(_topBar, font, 34, TextAnchor.MiddleLeft);
            var titleRt = _title.rectTransform;
            titleRt.anchorMin = new Vector2(0, 0); titleRt.anchorMax = new Vector2(1, 1);
            titleRt.offsetMin = new Vector2(28, 8); titleRt.offsetMax = new Vector2(-330, -8);

            var button = NewRect("NewWorldButton", _topBar);
            button.anchorMin = new Vector2(1, 0.5f); button.anchorMax = new Vector2(1, 0.5f);
            button.pivot = new Vector2(1, 0.5f); button.sizeDelta = new Vector2(290, 104);
            button.anchoredPosition = new Vector2(-20, 0);
            var buttonImage = AddImage(button, new Color(0.22f, 0.52f, 0.34f, 1f));
            var btn = button.gameObject.AddComponent<Button>();
            btn.targetGraphic = buttonImage;
            btn.onClick.AddListener(() => NewWorldClicked?.Invoke());
            var label = AddText(button, font, 38, TextAnchor.MiddleCenter);
            Stretch(label.rectTransform);
            label.text = "New world";

            // Bottom info panel
            _infoPanel = NewRect("TileInfo", _safeRoot);
            _infoPanel.anchorMin = new Vector2(0, 0); _infoPanel.anchorMax = new Vector2(1, 0);
            _infoPanel.pivot = new Vector2(0.5f, 0); _infoPanel.sizeDelta = new Vector2(0, 250);
            AddImage(_infoPanel, new Color(0.06f, 0.08f, 0.12f, 0.82f));
            _info = AddText(_infoPanel, font, 36, TextAnchor.MiddleLeft);
            _info.rectTransform.anchorMin = Vector2.zero; _info.rectTransform.anchorMax = Vector2.one;
            _info.rectTransform.offsetMin = new Vector2(28, 12); _info.rectTransform.offsetMax = new Vector2(-28, -12);
            _infoPanel.gameObject.SetActive(false);

            ApplySafeArea();
        }

        public void SetTitle(string text) => _title.text = text;

        public void ShowInfo(string text)
        {
            _info.text = text;
            _infoPanel.gameObject.SetActive(true);
        }

        public void HideInfo() => _infoPanel.gameObject.SetActive(false);

        /// <summary>True if a touch at this screen point belongs to the UI, not the world.</summary>
        public bool IsOverUi(Vector2 screenPoint)
        {
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

        static Text AddText(RectTransform parent, Font font, int size, TextAnchor anchor)
        {
            var rt = NewRect("Text", parent);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font;
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
