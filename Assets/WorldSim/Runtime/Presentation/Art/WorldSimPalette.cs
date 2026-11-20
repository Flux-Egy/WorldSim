using System.Collections.Generic;
using UnityEngine;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Builds the 5x8 palette ramp texture used by the WorldSim/RecolorSprite shader.
    /// Rows: 1 TEAM (kingdom), 2 ACC, 3 ACC2, 4 ROOF (culture), 5 SKIN, 6 HAIR (person). Rows 1-4 are 5-step
    /// dark-to-light ramps; rows 5-6 hold one base colour (the shader re-applies the original shading).
    /// Textures are cached by colour key: build one per kingdom+culture and reuse it.
    /// </summary>
    public static class WorldSimPalette
    {
        public const int Team = 1, Acc = 2, Acc2 = 3, Roof = 4, Skin = 5, Hair = 6;
        static readonly Dictionary<string, Texture2D> Cache = new Dictionary<string, Texture2D>();

        /// <summary>5-step ramp from one mid colour, same shape as the Python art ramps (dark to light).</summary>
        public static Color[] RampFrom(Color mid)
        {
            Color.RGBToHSV(mid, out float h, out float s, out float v);
            var r = new Color[5];
            float[] ds = { .15f, .08f, 0f, -.1f, -.25f };
            float[] dv = { -.32f, -.17f, 0f, .14f, .28f };
            for (int i = 0; i < 5; i++) r[i] = Color.HSVToRGB(h, Mathf.Clamp01(s + ds[i]), Mathf.Clamp01(v + dv[i]));
            return r;
        }

        public static Texture2D BuildRampTexture(Color[] team, Color[] acc, Color[] acc2, Color[] roof, Color skin, Color hair)
        {
            string key = string.Join("|", Key(team), Key(acc), Key(acc2), Key(roof), ColorUtility.ToHtmlStringRGB(skin), ColorUtility.ToHtmlStringRGB(hair));
            if (Cache.TryGetValue(key, out var cached) && cached != null) return cached;
            var t = new Texture2D(5, 8, TextureFormat.RGBA32, false, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = "WorldSimRamp" };
            var px = new Color[40];
            for (int i = 0; i < px.Length; i++) px[i] = Color.white;
            void Row(int region, Color[] ramp) { for (int x = 0; x < 5; x++) px[(region - 1) * 5 + x] = ramp[x]; }
            Row(Team, team); Row(Acc, acc); Row(Acc2, acc2); Row(Roof, roof);
            for (int x = 0; x < 5; x++) { px[(Skin - 1) * 5 + x] = skin; px[(Hair - 1) * 5 + x] = hair; }
            t.SetPixels(px);
            t.Apply(false, true);
            Cache[key] = t;
            return t;
        }

        static string Key(Color[] r)
        {
            var s = new System.Text.StringBuilder(40);
            foreach (var c in r) s.Append(ColorUtility.ToHtmlStringRGB(c));
            return s.ToString();
        }
    }
}
