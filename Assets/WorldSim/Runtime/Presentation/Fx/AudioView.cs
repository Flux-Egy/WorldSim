using UnityEngine;
using WorldSim.Core;
using WorldSim.Presentation.Art;
using WorldSim.Presentation.Terrain;

namespace WorldSim.Presentation.Fx
{
    /// <summary>
    /// Ambience for the land under the camera (forest, ocean, desert wind, snow wind, jungle, swamp, volcanic...) and a
    /// quiet music loop. Ambience is loudest near the ground and fades as the camera zooms out; the music stays low.
    /// </summary>
    public sealed class AudioView
    {
        readonly AudioSource _ambient, _music;
        string _wanted, _playing;
        float _wantedSince;

        public AudioView(Camera cam)
        {
            var go = new GameObject("Audio");
            _ambient = go.AddComponent<AudioSource>();
            _ambient.loop = true; _ambient.playOnAwake = false; _ambient.volume = 0f;
            _music = go.AddComponent<AudioSource>();
            _music.loop = true; _music.playOnAwake = false; _music.volume = 0.22f;
            var clip = WorldSimAudioDB.Instance.Music("peace");
            if (clip != null) { _music.clip = clip; _music.Play(); }
        }

        public void Tick(Camera cam, PackTerrainView terrain, float now)
        {
            if (terrain == null || terrain.Tiles == null) return;
            Vector3 p = cam.transform.position;
            int x = Mathf.Clamp((int)p.x, 0, terrain.WorldWidth - 1), y = Mathf.Clamp((int)PackTerrainView.WorldToTileY(p.y), 0, PackTerrainView.WorldHeight - 1);
            string want = AmbientFor(terrain.Tiles[y * terrain.WorldWidth + x].Biome);
            if (want != _wanted) { _wanted = want; _wantedSince = now; }
            if (_wanted != _playing && now - _wantedSince > 1.5f)
            {
                var clip = WorldSimAudioDB.Instance.Ambient(_wanted);
                if (clip != null) { _ambient.clip = clip; _ambient.Play(); }
                _playing = _wanted;
            }
            float zoom = Mathf.Clamp01(Mathf.InverseLerp(2f, 14f, terrain.PixelsPerTile));
            _ambient.volume = Mathf.MoveTowards(_ambient.volume, 0.15f + 0.45f * zoom, Time.unscaledDeltaTime * 0.5f);
        }

        static string AmbientFor(Biome b)
        {
            switch (b)
            {
                case Biome.DeepWater: case Biome.ShallowWater: case Biome.CoralShallows: case Biome.Beach: return "ocean";
                case Biome.DesertDunes: case Biome.SaltFlats: case Biome.Badlands: case Biome.Savanna: case Biome.Steppe: return "desert_wind";
                case Biome.Snow: case Biome.Glacier: case Biome.Tundra: case Biome.Mountain: case Biome.RockyHighland: return "snow_wind";
                case Biome.Jungle: return "jungle";
                case Biome.Swamp: case Biome.FungalGrove: return "swamp";
                case Biome.Volcanic: case Biome.Lava: case Biome.EmberWastes: case Biome.AshWaste: return "volcanic";
                case Biome.IrradiatedWaste: return "wasteland";
                case Biome.Farmland: return "farm_day";
                default: return "forest_day";
            }
        }
    }
}
