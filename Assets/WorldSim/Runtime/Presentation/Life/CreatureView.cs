using System.Collections.Generic;
using Unity.Collections;
using Unity.Entities;
using UnityEngine;
using WorldSim.Core.Life;
using WorldSim.Presentation.Art;
using WorldSim.Presentation.Terrain;
using WorldSim.Render.Art;
using WorldSim.Simulation.Life;

namespace WorldSim.Presentation.Life
{
    /// <summary>
    /// Draws creatures with the art pack (Playable Alpha step 2): near zoom shows each creature's pack animation
    /// (<see cref="CreatureArt"/>: walk, run, idle, eat, sleep, attack...) standing on the lifted terrain; mid zoom shows
    /// coloured dots; far zoom hides them. A pool of SpriteRenderers, only for creatures inside the camera.
    /// World y follows the terrain's top-down layout (<see cref="PackTerrainView.TileToWorldY"/>).
    /// </summary>
    public sealed class CreatureView
    {
        const float SpritesFrom = 7f;      // screen px per tile: full sprites (matches the near terrain layer)
        const float DotsFrom = 2.2f;       // coloured dots at mid zoom
        const int MaxVisible = 1500;

        readonly List<SpriteRenderer> _pool = new List<SpriteRenderer>();
        readonly Dictionary<uint, Vector2> _shown = new Dictionary<uint, Vector2>();
        readonly HashSet<uint> _seen = new HashSet<uint>();
        readonly List<uint> _stale = new List<uint>();
        readonly Dictionary<string, (Sprite[] frames, float fps)> _anims = new Dictionary<string, (Sprite[], float)>();
        readonly Transform _root;
        readonly Sprite _dot;
        EntityQuery _query;
        bool _queryReady;

        public CreatureView()
        {
            _root = new GameObject("Creatures").transform;
            var tex = new Texture2D(1, 1, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, name = "Dot" };
            tex.SetPixel(0, 0, Color.white);
            tex.Apply(false, true);
            _dot = Sprite.Create(tex, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 1f, 0, SpriteMeshType.FullRect);
        }

        public void Tick(EntityManager em, Camera cam, PackTerrainView terrain, uint tick, float time, float dt)
        {
            if (!_queryReady)
            {
                _query = em.CreateEntityQuery(ComponentType.ReadOnly<Creature>(), ComponentType.ReadOnly<Mover>(), ComponentType.ReadOnly<Brain>());
                _queryReady = true;
            }
            float ppt = Screen.height / Mathf.Max(0.01f, 2f * cam.orthographicSize);
            bool sprites = ppt >= SpritesFrom, dots = !sprites && ppt >= DotsFrom;
            int used = 0;
            if (sprites || dots)
            {
                float halfH = cam.orthographicSize + 2f, halfW = halfH * cam.aspect + 2f;
                Vector3 cp = cam.transform.position;
                var creatures = _query.ToComponentDataArray<Creature>(Allocator.Temp);
                var movers = _query.ToComponentDataArray<Mover>(Allocator.Temp);
                var brains = _query.ToComponentDataArray<Brain>(Allocator.Temp);
                _seen.Clear();
                float dotSize = Mathf.Max(0.35f, 2.2f / Mathf.Max(0.5f, ppt));
                for (int i = 0; i < creatures.Length && used < MaxVisible; i++)
                {
                    Mover m = movers[i];
                    float tx = m.PosQ.x / 65536f, ty = m.PosQ.y / 65536f;
                    var target = new Vector2(tx, PackTerrainView.TileToWorldY(ty));
                    if (Mathf.Abs(target.x - cp.x) > halfW || Mathf.Abs(target.y - cp.y) > halfH) continue;
                    Creature c = creatures[i];
                    _seen.Add(c.StableId);

                    // Glide toward the simulation position (ticks are 10 Hz, frames ~60 Hz).
                    Vector2 pos = _shown.TryGetValue(c.StableId, out var prev) && (prev - target).sqrMagnitude < 4f
                        ? Vector2.MoveTowards(prev, target, Mathf.Max(0.5f, (prev - target).magnitude * 12f) * dt)
                        : target;
                    _shown[c.StableId] = pos;
                    float lift = terrain != null ? terrain.LiftAt((int)tx, (int)ty) : 0f;

                    SpriteRenderer sr = Get(used++);
                    sr.transform.localPosition = new Vector3(pos.x, pos.y + lift, 0f);
                    sr.sortingOrder = 20 + Mathf.Clamp((int)(ty * 8f), 0, 30000);           // lower on screen = in front
                    SpeciesDef def = SpeciesTable.Get(c.Species);
                    if (dots)
                    {
                        sr.sprite = _dot;
                        sr.flipX = false;
                        sr.transform.localScale = new Vector3(dotSize, dotSize, 1f);
                        uint col = def.IsSapient ? def.ColorB : def.ColorA;
                        sr.color = new Color32((byte)col, (byte)(col >> 8), (byte)(col >> 16), 255);
                        continue;
                    }
                    sr.transform.localScale = Vector3.one;
                    sr.color = Color.white;
                    bool young = tick - c.BornTick < (uint)def.AdultAtTicks;
                    CreaturePose pose = PoseOf(brains[i].Action, m.Moving != 0);
                    string name = CreatureArt.Resolve(c.Species, pose, young, c.Sex == 1, Era.Tribal,
                                                      airborne: c.Species == SpeciesId.Bird && m.Moving != 0, out bool isAnim);
                    sr.sprite = Frame(name, isAnim, time + (c.StableId % 97) * 0.13f);
                    sr.flipX = m.FacingLeft != 0;
                }
                creatures.Dispose(); movers.Dispose(); brains.Dispose();
                // Forget creatures that left the view or died, so their glide restarts cleanly.
                _stale.Clear();
                foreach (var id in _shown.Keys) if (!_seen.Contains(id)) _stale.Add(id);
                foreach (var id in _stale) _shown.Remove(id);
            }
            for (int i = used; i < _pool.Count; i++) if (_pool[i].enabled) _pool[i].enabled = false;
        }

        static CreaturePose PoseOf(CreatureAction a, bool moving)
        {
            switch (a)
            {
                case CreatureAction.Flee: return moving ? CreaturePose.Run : CreaturePose.Idle;
                case CreatureAction.Hunt: return moving ? CreaturePose.Run : CreaturePose.Attack;
                case CreatureAction.Eat:
                case CreatureAction.Drink: return moving ? CreaturePose.Walk : CreaturePose.Eat;
                case CreatureAction.Sleep: return moving ? CreaturePose.Walk : CreaturePose.Sleep;
                default: return moving ? CreaturePose.Walk : CreaturePose.Idle;
            }
        }

        Sprite Frame(string name, bool isAnim, float time)
        {
            if (name == null) return _dot;
            if (!_anims.TryGetValue(name, out var a))
            {
                var db = WorldSimArtDB.Instance;
                if (isAnim && db.TryGetAnim(name, out var anim) && anim.Frames.Length > 0)
                {
                    var frames = new Sprite[anim.Frames.Length];
                    for (int i = 0; i < frames.Length; i++) frames[i] = db.GetSprite(anim.Frames[i]);
                    a = (frames, anim.Fps > 0 ? anim.Fps : 6f);
                }
                else
                {
                    var s = db.GetSprite(name);
                    a = (new[] { s != null ? s : _dot }, 1f);
                    if (s == null) Debug.LogWarning("[WorldSim] creature art missing: " + name);
                }
                _anims[name] = a;
            }
            int f = (int)(time * a.fps) % a.frames.Length;
            return a.frames[f] != null ? a.frames[f] : _dot;
        }

        SpriteRenderer Get(int i)
        {
            while (_pool.Count <= i)
            {
                var sr = new GameObject("Creature").AddComponent<SpriteRenderer>();
                sr.transform.SetParent(_root, false);
                _pool.Add(sr);
            }
            var r = _pool[i];
            if (!r.enabled) r.enabled = true;
            return r;
        }

        /// <summary>Nearest creature to a world point (tile coordinates are converted with the terrain's y flip).</summary>
        public static bool FindNearest(EntityManager em, Vector2 world, float maxDist, out Entity found)
        {
            var q = em.CreateEntityQuery(ComponentType.ReadOnly<Mover>(), ComponentType.ReadOnly<Creature>());
            var ents = q.ToEntityArray(Allocator.Temp);
            var movers = q.ToComponentDataArray<Mover>(Allocator.Temp);
            found = Entity.Null;
            float best = maxDist * maxDist;
            float tileY = PackTerrainView.WorldToTileY(world.y);
            for (int i = 0; i < ents.Length; i++)
            {
                float dx = movers[i].PosQ.x / 65536f - world.x, dy = movers[i].PosQ.y / 65536f - tileY;
                float d = dx * dx + dy * dy;
                if (d < best) { best = d; found = ents[i]; }
            }
            ents.Dispose(); movers.Dispose(); q.Dispose();
            return found != Entity.Null;
        }
    }
}
