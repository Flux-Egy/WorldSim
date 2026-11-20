using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Art Lab (Settings > "Art lab", developer): a fixed-camera grid of 102 sprites, three per atlas, at exactly 3
    /// screen pixels per art pixel, positions snapped to the pixel grid, animations frozen, HUD hidden and a flat
    /// background. Opening it twice gives the same image, so two builds can be compared pixel by pixel from phone
    /// screenshots (e.g. uncompressed vs ASTC). Tap anywhere to close. Logs "[WorldSim] ArtLab".
    /// The layout was packed offline (tallest first) from atlas_index.json; positions are in art pixels from the
    /// lab's top-left corner. Frames missing from the pack are skipped and logged.
    /// </summary>
    public sealed class ArtLabView : MonoBehaviour
    {
        public const int Scale = 3;                  // screen pixels per art pixel
        const int TopMargin = 220;                   // keep clear of the status bar and notifications
        const int Layer = 31;                        // lab objects and lab camera only
        static readonly Vector3 Origin = new Vector3(1000f, 1000f, 0f);   // far away from the world
        static readonly Color Background = new Color(0.5f, 0.5f, 0.5f, 1f);

        static readonly (string name, int x, int y)[] Layout =
        {
            ("wonder_space_elevator__collapse_2", 0, 0),
            ("wonder_space_elevator", 60, 0),
            ("t_colossus_roar_1", 120, 0),
            ("nuke_12", 202, 0),
            ("t_frost_giant_roar_0", 340, 0),
            ("b_5_seat_v0__collapse_2", 0, 196),
            ("h_cone_plaster_palace_1__collapse_2", 62, 196),
            ("b_5_seat_v0", 136, 196),
            ("h_cone_plaster_palace_1", 198, 196),
            ("t_sea_serpent_death_3", 0, 290),
            ("m_demon_lord_move_0", 168, 290),
            ("t_meadow_0", 219, 290),
            ("t_meadow_spring_0", 285, 290),
            ("t_pine_taiga_autumn_3", 351, 290),
            ("t_salt_flats_3", 0, 366),
            ("t_steppe_1", 66, 366),
            ("t_steppe_spring_3", 132, 366),
            ("wx_rain_tile_0", 198, 366),
            ("sp_warp_gate_circle_7", 264, 366),
            ("wx_lightning_strike_1", 313, 366),
            ("ad_laser_ad_1", 335, 366),
            ("ship_ironclad_90_1", 378, 366),
            ("st_hgv_900_1", 0, 432),
            ("reticle", 20, 432),
            ("sanctum_wave_1__collapse_0", 71, 432),
            ("b_2_commerce_v0__collapse_2", 139, 432),
            ("h_tiered_plaster_rich_0__collapse_3", 203, 432),
            ("a_giraffe_adult_walk_1", 251, 432),
            ("m_ogre_move_2", 281, 432),
            ("air_wing_0", 314, 432),
            ("b_4_research_v1", 340, 432),
            ("u_pikeman_0", 392, 432),
            ("h_gable_adobe_rich_0", 0, 484),
            ("lightning_0", 60, 484),
            ("wall_3_corner", 76, 484),
            ("ov_smoke_column_0", 116, 484),
            ("c_roc_adult_fly_0", 138, 484),
            ("m_shade_move_1", 185, 484),
            ("h_elf_m_tribal_cast_1", 213, 484),
            ("sol_elf_battlemage_cast_1", 233, 484),
            ("b_1_research_v0__collapse_2", 253, 484),
            ("ad_sam_3", 295, 484),
            ("ov_bandage", 332, 484),
            ("decal_scorch_xl_0", 354, 484),
            ("ship_freighter_135_1", 0, 528),
            ("air_wing_225", 52, 528),
            ("statue_abstract_stone__collapse_3", 88, 528),
            ("b_4_rich_v1", 116, 528),
            ("farm_potato_plowed", 182, 528),
            ("farm_wheat_plowed", 248, 528),
            ("st_icbm_225_1", 314, 528),
            ("a_camel_adult_1", 378, 528),
            ("ic_food_32", 0, 564),
            ("portrait_s_catfish_32", 34, 564),
            ("road_paved_0", 68, 564),
            ("u_hoplite_3", 102, 564),
            ("fountain_2", 120, 564),
            ("tree_5_0", 160, 564),
            ("tree_5_0_spring_sway_0", 190, 564),
            ("air_loiter_135", 220, 564),
            ("ship_cog_180_0", 251, 564),
            ("sol_orc_battlemage_death_dissolve_1", 307, 564),
            ("u_xbow_3", 332, 564),
            ("p_adult_m_poor_pants_skullcap_1", 353, 564),
            ("s_whale_adult_idle_1", 0, 598),
            ("h_orc_f_tribal_melee_2", 57, 598),
            ("p_elder_m_ruler_kilt_circlet_1", 86, 598),
            ("h_cone_reedw_poor_0__collapse_3", 103, 598),
            ("tree_4_2_winter_sway_1", 139, 598),
            ("h_hip_logs_poor_1", 165, 598),
            ("ad_ciws_1", 203, 598),
            ("wx_quake_2", 250, 598),
            ("palm_0_0_fall_1", 297, 598),
            ("h_orc_m_child_idle_1", 321, 598),
            ("a_lion_adult_hurt", 338, 598),
            ("a_fox_adult_3", 366, 598),
            ("sol_human_swordsman_death_burn_3", 396, 598),
            ("c_phoenix_adult_sleep_0", 0, 627),
            ("pine_3_green", 22, 627),
            ("badge_scarlet", 44, 627),
            ("sp_poison_dart_proj_2_2", 64, 627),
            ("ov_fire_m_1", 80, 627),
            ("a_sand_fox_young_walk_1", 146, 627),
            ("sp_boulder_throw_proj_0_2", 170, 627),
            ("portrait_a_donkey_16", 194, 627),
            ("a_sheep_young_dead_classic", 212, 627),
            ("flag_lemon_pennant_0", 231, 627),
            ("flag_orchid_square_3", 247, 627),
            ("icon_joy_x2", 263, 627),
            ("fern_0", 279, 627),
            ("s_squid_young_attack_1", 297, 627),
            ("c_penguin_young_burnt", 314, 627),
            ("select_ring", 330, 627),
            ("fire_1", 353, 627),
            ("ov_flood_s_0", 371, 627),
            ("s_angelfish_young_idle_0", 0, 649),
            ("decal_puddle_1", 11, 649),
            ("pt_stone_2", 31, 649),
            ("missile_225", 41, 649),
            ("g_A", 49, 649),
            ("g_T", 56, 649),
            ("g_comma", 63, 649),
        };

        readonly List<GameObject> _objects = new List<GameObject>();
        Camera _camera;
        WorldSim.Presentation.UI.WorldHud _hud;
        float _openedAt;

        public bool Showing => _camera != null;

        public void Open(WorldSim.Presentation.UI.WorldHud hud)
        {
            if (Showing) return;
            _hud = hud;
            var db = WorldSimArtDB.Instance;
            int ppu = 16;
            float unitsPerScreenPx = 1f / (ppu * Scale);
            int x0 = Mathf.Max(0, (Screen.width - 426 * Scale) / 2);

            var camGo = new GameObject("ArtLab Camera");
            _camera = camGo.AddComponent<Camera>();
            _camera.orthographic = true;
            _camera.orthographicSize = Screen.height * 0.5f * unitsPerScreenPx;
            _camera.clearFlags = CameraClearFlags.SolidColor;
            _camera.backgroundColor = Background;
            _camera.cullingMask = 1 << Layer;
            _camera.depth = 100;
            // screen top-left = Origin; camera centre = half a screen right and down (exact multiples of a screen pixel)
            camGo.transform.position = Origin + new Vector3(Screen.width * 0.5f * unitsPerScreenPx, -Screen.height * 0.5f * unitsPerScreenPx, -10f);

            var ramp = WorldSimPalette.BuildRampTexture(
                WorldSimPalette.RampFrom(new Color(0.80f, 0.22f, 0.20f)), WorldSimPalette.RampFrom(new Color(0.55f, 0.35f, 0.20f)),
                WorldSimPalette.RampFrom(new Color(0.30f, 0.45f, 0.30f)), WorldSimPalette.RampFrom(new Color(0.70f, 0.20f, 0.18f)),
                new Color(0.85f, 0.65f, 0.50f), new Color(0.25f, 0.18f, 0.12f));

            int shown = 0, missing = 0;
            foreach (var (name, x, y) in Layout)
            {
                if (!db.TryGetFrameId(name, out int id)) { missing++; Debug.LogWarning("[WorldSim] ArtLab: frame missing: " + name); continue; }
                var f = db.Frame(id);
                // bottom-left of the sprite on an exact screen pixel, then move to its pivot
                float left = x0 + x * Scale, bottom = TopMargin + (y + f.H) * Scale;
                var pos = Origin + new Vector3(left * unitsPerScreenPx + f.PivotX * f.W / ppu, -bottom * unitsPerScreenPx + f.PivotY * f.H / ppu, 0f);
                var go = new GameObject("ArtLab " + name) { layer = Layer };
                go.transform.position = pos;
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = 32000;
                var rc = go.AddComponent<WorldSimRecolor>();
                rc.SetFrame(name);
                if (f.Recolor) rc.SetPalette(ramp);
                _objects.Add(go);
                shown++;
            }
            if (_hud != null) _hud.Visible = false;
            _openedAt = Time.unscaledTime;
            Debug.Log($"[WorldSim] ArtLab shown: {shown} sprites, {missing} missing, scale {Scale}, screen {Screen.width}x{Screen.height}, " +
                      $"art loaded {db.LoadedTextureBytes / (1024f * 1024f):0.0} MiB, all textures {Texture.currentTextureMemory / (1024f * 1024f):0.0} MiB");
        }

        public void Close()
        {
            if (!Showing) return;
            foreach (var go in _objects) if (go != null) Destroy(go);
            _objects.Clear();
            Destroy(_camera.gameObject);
            _camera = null;
            if (_hud != null) _hud.Visible = true;
            Debug.Log("[WorldSim] ArtLab closed");
        }

        void Update()
        {
            if (!Showing || Time.unscaledTime - _openedAt < 1f) return;   // ignore the tap that opened it
            var pointer = Pointer.current;
            if (pointer != null && pointer.press.wasPressedThisFrame) Close();
        }
    }
}
