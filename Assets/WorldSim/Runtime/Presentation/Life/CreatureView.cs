using System.Collections.Generic;
using Unity.Collections;
using Unity.Entities;
using UnityEngine;
using WorldSim.Core.Life;
using WorldSim.Render;
using WorldSim.Simulation.Life;

namespace WorldSim.Presentation.Life
{
    /// <summary>
    /// Draws creatures (Beta B3) with a pool of SpriteRenderers, only for those inside the camera
    /// view and only when zoomed in enough to see them (zoom-dependent detail, owner request).
    /// Positions glide between 10 Hz simulation ticks (§7.2 interpolation); walk frames alternate
    /// while moving; sprites face their direction of travel. Presentation only: reads ECS data.
    /// </summary>
    public sealed class CreatureView
    {
        const float MinPxPerTile = 3.5f;   // below this creatures are too small to draw
        const int MaxVisible = 1500;

        readonly Sprite[] _sprites;        // [cellIndex]
        readonly List<SpriteRenderer> _pool = new List<SpriteRenderer>();
        readonly Dictionary<uint, Vector2> _shown = new Dictionary<uint, Vector2>();
        readonly HashSet<uint> _seen = new HashSet<uint>();
        readonly List<uint> _stale = new List<uint>();
        readonly Transform _root;
        EntityQuery _query;
        bool _queryReady;

        public CreatureView()
        {
            _root = new GameObject("Creatures").transform;
            int cells = SpeciesTable.All.Length * CreatureSprites.Frames, c = CreatureSprites.Cell;
            var tex = new Texture2D(cells * c, c, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = "CreatureAtlas" };
            uint[] atlas = CreatureSprites.Build();
            var px = new uint[cells * c * c];
            for (int i = 0; i < cells; i++)
                for (int y = 0; y < c; y++)
                    for (int x = 0; x < c; x++)
                        px[y * cells * c + i * c + x] = atlas[i * CreatureSprites.CellPixels + y * c + x];
            tex.SetPixelData(px, 0);
            tex.Apply(false, true);
            _sprites = new Sprite[cells];
            for (int i = 0; i < cells; i++)
                _sprites[i] = Sprite.Create(tex, new Rect(i * c, 0, c, c), new Vector2(0.5f, 0f), 8f, 0, SpriteMeshType.FullRect);
        }

        /// <summary>Draws visible creatures. <paramref name="em"/> is the default ECS world's manager.</summary>
        public void Tick(EntityManager em, Camera cam, float time, float dt)
        {
            if (!_queryReady)
            {
                _query = em.CreateEntityQuery(ComponentType.ReadOnly<Creature>(), ComponentType.ReadOnly<Mover>(), ComponentType.ReadOnly<Brain>());
                _queryReady = true;
            }
            float pxPerTile = Screen.height / Mathf.Max(0.01f, 2f * cam.orthographicSize);
            int used = 0;
            if (pxPerTile >= MinPxPerTile)
            {
                float halfH = cam.orthographicSize + 2f, halfW = halfH * cam.aspect + 2f;
                Vector3 cp = cam.transform.position;
                var creatures = _query.ToComponentDataArray<Creature>(Allocator.Temp);
                var movers = _query.ToComponentDataArray<Mover>(Allocator.Temp);
                _seen.Clear();
                for (int i = 0; i < creatures.Length && used < MaxVisible; i++)
                {
                    Mover m = movers[i];
                    var target = new Vector2(m.PosQ.x / 65536f, m.PosQ.y / 65536f);
                    if (Mathf.Abs(target.x - cp.x) > halfW || Mathf.Abs(target.y - cp.y) > halfH) continue;
                    Creature c = creatures[i];
                    _seen.Add(c.StableId);

                    // Glide toward the simulation position (ticks are 10 Hz, frames ~60 Hz).
                    Vector2 pos = _shown.TryGetValue(c.StableId, out var prev) && (prev - target).sqrMagnitude < 4f
                        ? Vector2.MoveTowards(prev, target, Mathf.Max(0.5f, (prev - target).magnitude * 12f) * dt)
                        : target;
                    _shown[c.StableId] = pos;

                    SpriteRenderer sr = Get(used++);
                    int frame = m.Moving != 0 ? (int)(time * 6f + c.StableId) & 1 : 0;
                    sr.sprite = _sprites[CreatureSprites.CellIndex(c.Species, frame)];
                    sr.flipX = m.FacingLeft != 0;
                    sr.transform.localPosition = new Vector3(pos.x, pos.y - 0.4f, 0f);
                    sr.sortingOrder = 20 + Mathf.Clamp(4000 - (int)(pos.y * 8f), 0, 30000); // lower = in front
                }
                creatures.Dispose(); movers.Dispose();
                // Forget creatures that left the view or died, so their glide restarts cleanly.
                _stale.Clear();
                foreach (var id in _shown.Keys) if (!_seen.Contains(id)) _stale.Add(id);
                foreach (var id in _stale) _shown.Remove(id);
            }
            for (int i = used; i < _pool.Count; i++) if (_pool[i].enabled) _pool[i].enabled = false;
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

        /// <summary>Nearest creature to a world point within <paramref name="maxDist"/> tiles, if any.</summary>
        public static bool FindNearest(EntityManager em, Vector2 world, float maxDist, out Entity found)
        {
            var q = em.CreateEntityQuery(ComponentType.ReadOnly<Mover>(), ComponentType.ReadOnly<Creature>());
            var ents = q.ToEntityArray(Allocator.Temp);
            var movers = q.ToComponentDataArray<Mover>(Allocator.Temp);
            found = Entity.Null;
            float best = maxDist * maxDist;
            for (int i = 0; i < ents.Length; i++)
            {
                float dx = movers[i].PosQ.x / 65536f - world.x, dy = movers[i].PosQ.y / 65536f - world.y;
                float d = dx * dx + dy * dy;
                if (d < best) { best = d; found = ents[i]; }
            }
            ents.Dispose(); movers.Dispose(); q.Dispose();
            return found != Entity.Null;
        }
    }
}
