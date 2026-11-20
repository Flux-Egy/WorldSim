using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Developer check for the art pack on a phone (Settings > "Art test"): shows one culture house and one walking
    /// person in three kingdom colours at the centre of the view, and logs memory before showing, after showing and
    /// after releasing. Log lines start with "[WorldSim] ArtTest" (read them with: logcat -s Unity).
    /// </summary>
    public sealed class ArtTestView : MonoBehaviour
    {
        const string House = "h_cone_plaster_palace_1";
        const string Walk = "walk_adult_m_poor_robe_turban";
        static readonly Color[] Kingdoms = { new Color(0.80f, 0.22f, 0.20f), new Color(0.20f, 0.42f, 0.85f), new Color(0.90f, 0.72f, 0.18f) };

        readonly List<GameObject> _objects = new List<GameObject>();
        readonly List<(WorldSimRecolor rc, Texture2D ramp)> _walkers = new List<(WorldSimRecolor, Texture2D)>();
        WorldSimArtDB.Anim _walk;
        float _time;

        public bool Showing => _objects.Count > 0;

        public void Toggle(Camera cam)
        {
            if (Showing) Hide(); else Show(cam);
        }

        void Show(Camera cam)
        {
            var db = WorldSimArtDB.Instance;
            LogMemory("before show", db);
            Vector3 c = cam != null ? cam.transform.position : Vector3.zero;
            if (!db.TryGetAnim(Walk, out _walk)) Debug.LogError("[WorldSim] ArtTest: animation missing: " + Walk);
            for (int k = 0; k < Kingdoms.Length; k++)
            {
                var ramp = WorldSimPalette.BuildRampTexture(
                    WorldSimPalette.RampFrom(Kingdoms[k]), WorldSimPalette.RampFrom(new Color(0.55f, 0.35f, 0.20f)),
                    WorldSimPalette.RampFrom(new Color(0.30f, 0.45f, 0.30f)), WorldSimPalette.RampFrom(Kingdoms[k] * 0.85f),
                    new Color(0.85f, 0.65f, 0.50f), new Color(0.25f, 0.18f, 0.12f));
                float x = c.x + (k - 1) * 5f;
                var house = Spawn("ArtTest House " + k, new Vector3(x, c.y + 1.5f, 0f), 30000);
                var hrc = house.GetComponent<WorldSimRecolor>();
                hrc.SetFrame(House);
                hrc.SetPalette(ramp);
                if (_walk.Frames != null && _walk.Frames.Length > 0)
                {
                    var person = Spawn("ArtTest Person " + k, new Vector3(x, c.y - 1.5f, 0f), 30001);
                    var prc = person.GetComponent<WorldSimRecolor>();
                    prc.SetFrame(_walk.Frames[0]);
                    prc.SetPalette(ramp);
                    _walkers.Add((prc, ramp));
                }
            }
            LogMemory("after show (house + walking person x3 colours)", db);
        }

        GameObject Spawn(string name, Vector3 pos, int order)
        {
            var go = new GameObject(name);
            go.transform.position = pos;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            go.AddComponent<WorldSimRecolor>();
            _objects.Add(go);
            return go;
        }

        void Hide()
        {
            foreach (var go in _objects) if (go != null) Destroy(go);
            _objects.Clear();
            _walkers.Clear();
            Invoke(nameof(ReleaseAfterDestroy), 0.1f);   // Destroy runs at the end of the frame
        }

        void ReleaseAfterDestroy()
        {
            var db = WorldSimArtDB.Instance;
            var kept = new List<string>();
            int released = db.Release("", kept);
            Debug.Log("[WorldSim] ArtTest: released " + released + " atlases" + (kept.Count > 0 ? ", kept (in use): " + string.Join(", ", kept) : ""));
            LogMemory("after release", db);
        }

        void Update()
        {
            if (_walkers.Count == 0 || _walk.Frames == null || _walk.Fps <= 0f) return;
            _time += Time.deltaTime;
            int frame = (int)(_time * _walk.Fps) % _walk.Frames.Length;
            foreach (var (rc, ramp) in _walkers)
            {
                rc.SetFrame(_walk.Frames[frame]);
                rc.SetPalette(ramp);
            }
        }

        static void LogMemory(string when, WorldSimArtDB db)
        {
            Debug.Log($"[WorldSim] ArtTest {when}: atlases loaded {db.LoadedAtlasCount}, art pages+masks {db.LoadedTextureBytes / (1024f * 1024f):0.0} MiB, " +
                      $"all textures {Texture.currentTextureMemory / (1024f * 1024f):0.0} MiB, process RSS {RssMiB()}");
        }

        /// <summary>Resident memory of the whole process from /proc (Android/Linux); "n/a" elsewhere.</summary>
        static string RssMiB()
        {
            try
            {
                foreach (var line in File.ReadAllLines("/proc/self/status"))
                    if (line.StartsWith("VmRSS:"))
                    {
                        var parts = line.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                        return (long.Parse(parts[1]) / 1024f).ToString("0") + " MiB";
                    }
            }
            catch (System.Exception) { }
            return "n/a";
        }
    }
}
