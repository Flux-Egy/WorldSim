using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using WorldSim.Presentation.Art;

namespace WorldSim.Presentation.UI
{
    /// <summary>
    /// The art pack's UI kit for the HUD (Playable Alpha: new UI): 9-slice frames and buttons (UI/ui_kit: frame_9slice,
    /// button_primary, button_on), pack icons (icon_*, picon_* power icons, creature portraits). Borders are scaled up
    /// x3 on the 1080-wide canvas so the pixel art reads on a phone; point filtering keeps it crisp.
    /// </summary>
    public static class UiKit
    {
        const float Scale = 3f;
        static readonly Dictionary<string, Sprite> Cache = new Dictionary<string, Sprite>();

        /// <summary>A pack sprite rebuilt with 9-slice borders (pixels).</summary>
        public static Sprite Sliced(string name, float border)
        {
            string key = name + "#" + border;
            if (Cache.TryGetValue(key, out var s)) return s;
            var src = WorldSimArtDB.Instance.GetSprite(name);
            s = src == null ? null : Sprite.Create(src.texture, src.rect, new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect,
                                                   new Vector4(border, border, border, border));
            Cache[key] = s;
            return s;
        }

        /// <summary>A pack icon, the x2 version when the pack has one.</summary>
        public static Sprite Icon(string name)
        {
            var db = WorldSimArtDB.Instance;
            var x2 = db.GetSprite(name + "_x2");
            return x2 != null ? x2 : db.GetSprite(name);
        }

        static Image Skin(RectTransform rt, string sprite, float border, Color tint)
        {
            var img = rt.gameObject.GetComponent<Image>();
            if (img == null) img = rt.gameObject.AddComponent<Image>();   // Unity objects: no ?? (overloaded ==)
            var s = Sliced(sprite, border);
            if (s != null)
            {
                img.sprite = s;
                img.type = Image.Type.Sliced;
                img.pixelsPerUnitMultiplier = 1f / Scale;
            }
            img.color = tint;
            return img;
        }

        /// <summary>The gold-edged frame (dark inside); brightness is kept for callers but the frame keeps its colours.</summary>
        public static Image Panel(RectTransform rt, float brightness = 1f, float alpha = 0.96f) =>
            Skin(rt, "frame_9slice", 8f, new Color(1f, 1f, 1f, alpha));

        /// <summary>Calm dark-slate button; the selected one turns green (button_on).</summary>
        public static Image Button(RectTransform rt) => Skin(rt, "button_ghost", 5f, Color.white);

        /// <summary>Selected buttons and tabs switch to the "on" art; others go back to the primary art.</summary>
        public static void Select(Image img, bool on)
        {
            if (img == null) return;
            var s = Sliced(on ? "button_on" : "button_ghost", 5f);
            if (s != null) { img.sprite = s; img.type = Image.Type.Sliced; img.pixelsPerUnitMultiplier = 1f / Scale; }
            img.color = Color.white;
        }
    }
}
