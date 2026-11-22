using System.Collections.Generic;
using UnityEngine;
using WorldSim.Presentation.Art;
using WorldSim.Render.Terrain;

namespace WorldSim.Presentation.Terrain
{
    /// <summary>
    /// Trees, bushes, palms, pines, birches, glimmer trees, vents and every other decoration as live sprites at near zoom
    /// (Playable Alpha demo: "everything moves"). Same placement as the baked view (<see cref="TerrainComposer.TryPlaceProp"/>),
    /// each with its pack animation (wind sway, glow, smoke) at its own phase. Sorted by row with the creatures, so a
    /// creature walks in front of or behind a tree correctly. Only the props inside the camera are drawn (pooled).
    /// </summary>
    public sealed class PropView
    {
        const int MaxProps = 2600;

        struct Placed { public string Frame, Anim; public Vector3 Pos; public int Order; public float Phase; }

        readonly Transform _root;
        readonly List<SpriteRenderer> _pool = new List<SpriteRenderer>();
        readonly List<Placed> _visible = new List<Placed>(1024);
        readonly Dictionary<string, (Sprite[] frames, float fps)> _anims = new Dictionary<string, (Sprite[], float)>();
        RectInt _scanned = new RectInt(0, 0, -1, -1);
        object _scannedLayout;
        int _shown;

        public PropView() { _root = new GameObject("Props").transform; }

        public void Tick(Camera cam, PackTerrainView terrain, float time)
        {
            float alpha = terrain.NearAlpha;
            if (alpha <= 0f || terrain.Layout == null)
            {
                Hide(0);
                return;
            }
            // Visible tile rectangle plus a margin (tall trees stand below the screen's bottom edge).
            float halfH = cam.orthographicSize, halfW = halfH * cam.aspect;
            Vector3 p = cam.transform.position;
            int w = terrain.WorldWidth, h = PackTerrainView.WorldHeight;
            int x0 = Mathf.Max(0, Mathf.FloorToInt(p.x - halfW) - 2), x1 = Mathf.Min(w - 1, Mathf.CeilToInt(p.x + halfW) + 2);
            int y0 = Mathf.Max(0, Mathf.FloorToInt(PackTerrainView.WorldToTileY(p.y + halfH)) - 2);
            int y1 = Mathf.Min(h - 1, Mathf.CeilToInt(PackTerrainView.WorldToTileY(p.y - halfH)) + 4);
            var rect = new RectInt(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
            if (!rect.Equals(_scanned) || !ReferenceEquals(_scannedLayout, terrain.Layout)) Scan(terrain, rect);

            int n = Mathf.Min(_visible.Count, MaxProps);
            var tint = new Color(1f, 1f, 1f, alpha);
            for (int i = 0; i < n; i++)
            {
                Placed pl = _visible[i];
                SpriteRenderer sr = Get(i);
                sr.sprite = Frame(pl.Anim ?? pl.Frame, pl.Anim != null, time + pl.Phase);
                sr.transform.localPosition = pl.Pos;
                sr.sortingOrder = pl.Order;
                sr.color = tint;
            }
            Hide(n);
        }

        void Scan(PackTerrainView terrain, RectInt rect)
        {
            _scanned = rect;
            _scannedLayout = terrain.Layout;
            _visible.Clear();
            var tiles = terrain.Tiles; var lay = terrain.Layout; var field = terrain.Field;
            for (int cy = rect.yMin; cy < rect.yMax; cy++)
                for (int cx = rect.xMin; cx < rect.xMax; cx++)
                {
                    if (tiles[cy * lay.Width + cx].DecorationId == 0) continue;
                    if (!TerrainComposer.TryPlaceProp(tiles, lay, field, cx, cy, out string frame, out string anim, out int fx, out int fy, out int lift)) continue;
                    _visible.Add(new Placed
                    {
                        Frame = frame, Anim = anim,
                        Pos = new Vector3(fx / 16f, PackTerrainView.TileToWorldY(fy / 16f) + lift / 16f, 0f),
                        Order = 20 + Mathf.Clamp(fy / 2, 0, 30000),               // same scale as creatures (tile y * 8)
                        Phase = ((cx * 7919 + cy * 104729) & 1023) / 97f,
                    });
                }
        }

        Sprite Frame(string name, bool isAnim, float time)
        {
            if (!_anims.TryGetValue(name, out var a))
            {
                var db = WorldSimArtDB.Instance;
                if (isAnim && db.TryGetAnim(name, out var anim) && anim.Frames.Length > 0)
                {
                    var frames = new Sprite[anim.Frames.Length];
                    for (int i = 0; i < frames.Length; i++) frames[i] = db.GetSprite(anim.Frames[i]);
                    a = (frames, anim.Fps > 0 ? anim.Fps : 4f);
                }
                else a = (new[] { db.GetSprite(name) }, 1f);
                _anims[name] = a;
            }
            int f = a.frames.Length == 1 ? 0 : (int)(time * a.fps) % a.frames.Length;
            return a.frames[f];
        }

        SpriteRenderer Get(int i)
        {
            while (_pool.Count <= i)
            {
                var sr = new GameObject("Prop").AddComponent<SpriteRenderer>();
                sr.transform.SetParent(_root, false);
                _pool.Add(sr);
            }
            var r = _pool[i];
            if (!r.enabled) r.enabled = true;
            return r;
        }

        void Hide(int from)
        {
            for (int i = from; i < _shown && i < _pool.Count; i++) _pool[i].enabled = false;
            _shown = from;
        }
    }
}
