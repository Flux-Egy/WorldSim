using System.Collections.Generic;
using UnityEngine;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Loads the generated sound library from Resources/WorldSimAudio (SFX, Ambient, Music; OGG Vorbis).
    /// Animation events named "sfx:&lt;key&gt;" map to a clip through <see cref="ResolveEventSfx"/>.
    /// </summary>
    public sealed class WorldSimAudioDB
    {
        public const string Root = "WorldSimAudio";
        static WorldSimAudioDB _instance;
        public static WorldSimAudioDB Instance => _instance ??= new WorldSimAudioDB();

        readonly Dictionary<string, AudioClip> _cache = new Dictionary<string, AudioClip>();

        // short event keys used in animation data -> clip names in the pack
        static readonly Dictionary<string, string> EventMap = new Dictionary<string, string>
        {
            { "attack", "combat_sword_swing" }, { "swing", "combat_sword_swing" }, { "bow", "combat_arrow_shoot" }, { "shot", "combat_rifle_shot" },
            { "cast", "magic_charge" }, { "roar", "creature_roar" }, { "eat", "creature_chomp" }, { "flap", "creature_flap" }, { "quake", "disaster_quake" },
            { "breath", "creature_dragon_breath" }, { "hurt", "body_hurt_m" }, { "scream", "body_scream" }, { "cheer", "body_cheer" },
            { "chop", "world_chop" }, { "mine", "world_mine" }, { "hammer", "world_hammer" }, { "tree_fall", "world_tree_fall" },
            { "impact", "magic_fire_impact" }, { "nova", "magic_nova" }, { "summon", "magic_portal" }, { "titan_death", "creature_titan" },
            { "ship_sink", "world_splash_big" }, { "tornado", "disaster_tornado_hit" }, { "tsunami", "disaster_tsunami" }, { "volcano", "disaster_volcano" },
            { "thunder", "magic_thunder" }, { "firework", "disaster_fireworks" }, { "death", "body_death" },
            { "death_weapon", "body_death" }, { "death_arrow", "body_death" }, { "death_explosion", "combat_explosion_small" }, { "death_burn", "body_burn" },
            { "death_freeze", "body_shatter" }, { "death_electric", "body_electrocute" }, { "death_poison", "body_cough" }, { "death_drown", "body_bubbles" },
            { "death_crushed", "body_crush" }, { "death_vaporized", "extra_blast_near" },
            { "house_fire", "building_house_fire" }, { "building_crack", "building_crack" }, { "building_collapse", "building_collapse" },
             { "death_eaten", "creature_chomp" }, { "death_dissolve", "body_dissolve" }, { "death_irradiated", "body_irradiated" },
        };

        public AudioClip Sfx(string name) => Load("SFX/" + name);
        public AudioClip Ambient(string name) => Load("Ambient/amb_" + name);
        public AudioClip Music(string era) => Load("Music/music_" + era);

        /// <summary>"sfx:roar" -> clip, or null if the event is not a sound cue.</summary>
        public AudioClip ResolveEventSfx(string eventName)
        {
            if (string.IsNullOrEmpty(eventName) || !eventName.StartsWith("sfx:")) return null;
            var key = eventName.Substring(4);
            return EventMap.TryGetValue(key, out var clip) ? Sfx(clip) : Sfx(key);
        }

        AudioClip Load(string path)
        {
            if (_cache.TryGetValue(path, out var c)) return c;
            c = Resources.Load<AudioClip>(Root + "/" + path);
            _cache[path] = c;
            return c;
        }
    }
}
