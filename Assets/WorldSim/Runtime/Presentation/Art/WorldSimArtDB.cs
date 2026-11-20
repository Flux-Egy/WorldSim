using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WorldSim.Render.Art;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Runtime access to the art pack (Resources/WorldSimArt), loaded on demand.
    ///
    /// Startup reads only the compact index (art_index.bytes, built by Tools/ArtIndex/build_art_index.py):
    /// no atlas JSON is parsed and no texture is loaded. A page texture loads the first time one of its frames
    /// is asked for; its recolour mask loads separately, only when a mask is asked for. <see cref="Release"/>
    /// unloads whole atlases by path prefix ("Characters/Titans", "Buildings/Disaster"...), but never one that
    /// something still shows: atlases with leases, or used by any active SpriteRenderer or UI Image, are kept.
    /// Sprites created from a released page are destroyed.
    ///
    /// The public API of the original pack loader is kept (GetSprite, TryGetAnim, TryGetAnchor, GetMask,
    /// IsRecolor, GetTagsJson...), so WorldSimRecolor and pack code work unchanged. Instanced renderers use the
    /// int API instead: <see cref="TryGetFrameId"/>, <see cref="Frame"/>, <see cref="UvRect"/>,
    /// <see cref="GetPageTexture"/>, <see cref="GetMaskTexture"/>.
    /// </summary>
    public sealed class WorldSimArtDB
    {
        public const string Root = "WorldSimArt";
        public const string IndexAsset = Root + "/art_index";
        const string RecolorShaderName = "WorldSim/RecolorSprite";

        /// <summary>A gameplay/audio cue fired when an animation reaches a frame (e.g. "hit", "spawn_projectile", "sfx:roar").</summary>
        public readonly struct AnimEvent
        {
            public readonly int Frame;
            public readonly string Name;
            public AnimEvent(int frame, string name) { Frame = frame; Name = name; }
        }

        /// <summary>One animation from the pack: frame sprite names, playback speed, looping and frame events.</summary>
        public readonly struct Anim
        {
            public readonly string[] Frames;
            public readonly float Fps;
            public readonly bool Loop;
            public readonly AnimEvent[] Events;
            public Anim(string[] frames, float fps, bool loop, AnimEvent[] events) { Frames = frames; Fps = fps; Loop = loop; Events = events ?? Array.Empty<AnimEvent>(); }
        }

        sealed class AtlasState
        {
            public Texture2D[] Pages, Masks;
            public readonly Dictionary<int, Sprite> Sprites = new Dictionary<int, Sprite>();
            public Dictionary<string, string> Tags;   // frame name -> tagsJson, loaded on first GetTagsJson
            public int Leases;
            public bool AnyLoaded
            {
                get
                {
                    if (Pages != null) foreach (var t in Pages) if (t != null) return true;
                    if (Masks != null) foreach (var t in Masks) if (t != null) return true;
                    return false;
                }
            }
        }

#pragma warning disable 0649 // JSON DTOs for the on-demand tag lookup
        [Serializable] sealed class TagFrameJ { public string name; public string tagsJson; }
        [Serializable] sealed class TagAtlasJ { public TagFrameJ[] frameList; }
#pragma warning restore 0649

        static WorldSimArtDB _instance;
        static Material _recolorMaterial;

        readonly ArtIndex _index;
        readonly AtlasState[] _atlases;
        readonly Dictionary<int, Anim> _animCache = new Dictionary<int, Anim>();

        /// <summary>Shared instance; loads only the index.</summary>
        public static WorldSimArtDB Instance => _instance ??= Load();

        /// <summary>The frame/animation index (pure C#; safe to hand to non-Unity code).</summary>
        public ArtIndex Index => _index;

        /// <summary>Material for sprites whose frame has recolor == true (kingdom / culture / person colours).</summary>
        public static Material RecolorMaterial
        {
            get
            {
                if (_recolorMaterial == null)
                {
                    var shader = Shader.Find(RecolorShaderName);
                    if (shader == null) { Debug.LogError("WorldSimArtDB: shader " + RecolorShaderName + " not found"); return null; }
                    _recolorMaterial = new Material(shader) { name = "WorldSimRecolor (runtime)" };
                }
                return _recolorMaterial;
            }
        }

        WorldSimArtDB(ArtIndex index)
        {
            _index = index;
            _atlases = new AtlasState[index.AtlasCount];
            for (int a = 0; a < _atlases.Length; a++) _atlases[a] = new AtlasState();
        }

        /// <summary>Reads the index only. Throws if it is missing or malformed (a broken build should fail loudly).</summary>
        public static WorldSimArtDB Load()
        {
            var ta = Resources.Load<TextAsset>(IndexAsset);
            if (ta == null) throw new InvalidOperationException("WorldSimArtDB: Resources/" + IndexAsset + ".bytes missing (run Tools/ArtIndex/build_art_index.py)");
            var index = ArtIndex.Parse(ta.bytes);
            Resources.UnloadAsset(ta);
            return new WorldSimArtDB(index);
        }

        // ---------------------------------------------------------------- name API (pack-compatible)

        public int FrameCount => _index.FrameCount;
        public IEnumerable<string> FrameNames { get { for (int i = 0; i < _index.FrameCount; i++) yield return _index.FrameName(i); } }
        public IEnumerable<string> AnimNames { get { for (int i = 0; i < _index.AnimCount; i++) yield return _index.AnimName(i); } }
        public bool Has(string name) => _index.TryGetFrameId(name, out _);

        public bool TryGetSprite(string name, out Sprite sprite)
        {
            sprite = null;
            return _index.TryGetFrameId(name, out int id) && (sprite = GetSprite(id)) != null;
        }

        public Sprite GetSprite(string name) => TryGetSprite(name, out var s) ? s : null;

        /// <summary>Recolour mask page for this frame (null when the frame has nothing to recolour). Loads the mask on demand.</summary>
        public Texture2D GetMask(string name)
        {
            if (!_index.TryGetFrameId(name, out int id)) return null;
            var f = _index.Frame(id);
            return f.Recolor ? GetMaskTexture(f.Atlas, f.Page) : null;
        }

        /// <summary>True when the frame recolours and its page has a mask. Loads nothing.</summary>
        public bool IsRecolor(string name)
        {
            if (!_index.TryGetFrameId(name, out int id)) return false;
            var f = _index.Frame(id);
            return f.Recolor && _index.Page(f.Atlas, f.Page).MaskId >= 0;
        }

        /// <summary>Raw tag object (era, category, roof, wall, tier, species, angle, frame...) as JSON text. The first call
        /// for an atlas parses that atlas's JSON once (rare: build lookup tables from it, don't call per frame).</summary>
        public string GetTagsJson(string name)
        {
            if (!_index.TryGetFrameId(name, out int id)) return null;
            var st = _atlases[_index.Frame(id).Atlas];
            if (st.Tags == null)
            {
                st.Tags = new Dictionary<string, string>(StringComparer.Ordinal);
                var ta = Resources.Load<TextAsset>(Root + "/" + _index.AtlasPath(_index.Frame(id).Atlas));
                if (ta != null)
                {
                    var j = JsonUtility.FromJson<TagAtlasJ>(ta.text);
                    if (j?.frameList != null) foreach (var f in j.frameList) st.Tags[f.name] = f.tagsJson;
                    Resources.UnloadAsset(ta);
                }
            }
            return st.Tags.TryGetValue(name, out var tags) ? tags : null;
        }

        public bool TryGetAnim(string name, out Anim anim)
        {
            anim = default;
            if (!_index.TryGetAnimId(name, out int id)) return false;
            if (!_animCache.TryGetValue(id, out anim))
            {
                var frames = new string[_index.AnimFrameCount(id)];
                for (int i = 0; i < frames.Length; i++) frames[i] = _index.FrameName(_index.AnimFrame(id, i));
                var events = new AnimEvent[_index.AnimEventCount(id)];
                for (int i = 0; i < events.Length; i++) events[i] = new AnimEvent(_index.AnimEventFrame(id, i), _index.AnimEventName(id, i));
                anim = new Anim(frames, _index.AnimFps(id), _index.AnimLoop(id), events);
                _animCache[id] = anim;
            }
            return true;
        }

        /// <summary>Anchor (muzzle, hand, smoke point...) in local units relative to the sprite pivot. Loads nothing.</summary>
        public bool TryGetAnchor(string frame, string anchor, out Vector2 local)
        {
            local = default;
            if (!_index.TryGetFrameId(frame, out int id) || !_index.TryGetAnchor(id, anchor, out int ax, out int ay)) return false;
            var f = _index.Frame(id);
            int ppu = _index.AtlasPpu(f.Atlas);
            float px = ax - f.PivotX * f.W;
            float py = (f.H - ay) - f.PivotY * f.H;
            local = new Vector2(px / ppu, py / ppu);
            return true;
        }

        // ---------------------------------------------------------------- int API (instancing / ECS)

        public bool TryGetFrameId(string name, out int id) => _index.TryGetFrameId(name, out id);
        public ArtFrame Frame(int id) => _index.Frame(id);

        /// <summary>UV rect of a frame inside its page: (xMin, yMin, width, height), normalised, bottom-left origin.</summary>
        public Vector4 UvRect(int id)
        {
            var f = _index.Frame(id);
            var p = _index.Page(f.Atlas, f.Page);
            return new Vector4((float)f.X / p.Width, (float)(p.Height - f.Y - f.H) / p.Height, (float)f.W / p.Width, (float)f.H / p.Height);
        }

        public Sprite GetSprite(int id)
        {
            var f = _index.Frame(id);
            var st = _atlases[f.Atlas];
            if (st.Sprites.TryGetValue(id, out var cached) && cached != null) return cached;
            var tex = GetPageTexture(f.Atlas, f.Page);
            if (tex == null) return null;
            int pageH = _index.Page(f.Atlas, f.Page).Height;
            var rect = new Rect(f.X, pageH - f.Y - f.H, f.W, f.H);   // index is top-left origin
            var s = Sprite.Create(tex, rect, new Vector2(f.PivotX, f.PivotY), _index.AtlasPpu(f.Atlas), 0, SpriteMeshType.FullRect);
            s.name = _index.FrameName(id);
            st.Sprites[id] = s;
            return s;
        }

        /// <summary>Colour page texture; loads it on first use.</summary>
        public Texture2D GetPageTexture(int atlas, int page)
        {
            var st = _atlases[atlas];
            st.Pages ??= new Texture2D[_index.AtlasPageCount(atlas)];
            if (st.Pages[page] == null)
            {
                string path = _index.GetString(_index.Page(atlas, page).ImageId);
                st.Pages[page] = Resources.Load<Texture2D>(Root + "/" + path);
                if (st.Pages[page] == null) Debug.LogWarning("WorldSimArtDB: page not found: " + path);
            }
            return st.Pages[page];
        }

        /// <summary>Recolour mask texture of a page (null when the page has none); loads it on first use, separately from the page.</summary>
        public Texture2D GetMaskTexture(int atlas, int page)
        {
            int maskId = _index.Page(atlas, page).MaskId;
            if (maskId < 0) return null;
            var st = _atlases[atlas];
            st.Masks ??= new Texture2D[_index.AtlasPageCount(atlas)];
            if (st.Masks[page] == null)
            {
                EnsureMaskLut();
                string path = _index.GetString(maskId);
                st.Masks[page] = Resources.Load<Texture2D>(Root + "/" + path);
                if (st.Masks[page] == null) Debug.LogWarning("WorldSimArtDB: mask not found: " + path);
            }
            return st.Masks[page];
        }

        static readonly int MaskLutId = Shader.PropertyToID("_MaskLut");
        Texture2D _maskLut;

        /// <summary>Masks are one byte per pixel (codes); the recolour shader decodes them through this 256 x 1 lookup
        /// table, set as the global _MaskLut. Loaded with the first mask and kept (1 KB).</summary>
        public Texture2D MaskLut { get { EnsureMaskLut(); return _maskLut; } }

        void EnsureMaskLut()
        {
            if (_maskLut != null) return;
            _maskLut = Resources.Load<Texture2D>(Root + "/mask_lut");
            if (_maskLut == null) { Debug.LogError("WorldSimArtDB: Resources/" + Root + "/mask_lut.png missing (run Tools/ArtIndex/encode_masks.py)"); return; }
            Shader.SetGlobalTexture(MaskLutId, _maskLut);
        }

        // ---------------------------------------------------------------- lifecycle

        /// <summary>Keeps every atlas under a path prefix from being released while the lease is held (e.g. by an instanced renderer).</summary>
        public sealed class Lease : IDisposable
        {
            readonly WorldSimArtDB _db; readonly int[] _atlases; bool _done;
            internal Lease(WorldSimArtDB db, int[] atlases) { _db = db; _atlases = atlases; foreach (int a in atlases) db._atlases[a].Leases++; }
            public void Dispose() { if (_done) return; _done = true; foreach (int a in _atlases) _db._atlases[a].Leases--; }
        }

        public Lease Acquire(string pathPrefix) => new Lease(this, AtlasesUnder(pathPrefix));

        int[] AtlasesUnder(string prefix)
        {
            var list = new List<int>();
            for (int a = 0; a < _atlases.Length; a++)
                if (string.IsNullOrEmpty(prefix) || _index.AtlasPath(a).StartsWith(prefix, StringComparison.Ordinal)) list.Add(a);
            return list.ToArray();
        }

        public bool IsAtlasLoaded(int atlas) => _atlases[atlas].AnyLoaded;
        public bool IsMaskLoaded(int atlas, int page) => _atlases[atlas].Masks != null && _atlases[atlas].Masks[page] != null;
        public bool IsPageLoaded(int atlas, int page) => _atlases[atlas].Pages != null && _atlases[atlas].Pages[page] != null;

        public int LoadedAtlasCount { get { int n = 0; foreach (var st in _atlases) if (st.AnyLoaded) n++; return n; } }

        /// <summary>Bytes of the pages (RGBA32: 4 per pixel) and masks (R8: 1 per pixel) currently loaded.</summary>
        public long LoadedTextureBytes
        {
            get
            {
                long total = 0;
                for (int a = 0; a < _atlases.Length; a++)
                {
                    var st = _atlases[a];
                    for (int p = 0; p < _index.AtlasPageCount(a); p++)
                    {
                        var pg = _index.Page(a, p);
                        long pixels = (long)pg.Width * pg.Height;
                        if (st.Pages != null && st.Pages[p] != null) total += pixels * 4;
                        if (st.Masks != null && st.Masks[p] != null) total += pixels;
                    }
                }
                return total;
            }
        }

        /// <summary>
        /// Unloads every atlas whose path starts with <paramref name="pathPrefix"/> ("" = all), except atlases that are
        /// still in use: held by a <see cref="Lease"/>, or shown by an active SpriteRenderer (sprite or recolour mask) or
        /// UI Image. Sprites created from released pages are destroyed. Returns how many atlases were unloaded;
        /// <paramref name="kept"/> lists the ones kept because they are in use.
        /// </summary>
        public int Release(string pathPrefix, List<string> kept = null)
        {
            var targets = AtlasesUnder(pathPrefix);
            var inUse = TexturesInUse();
            int released = 0;
            foreach (int a in targets)
            {
                var st = _atlases[a];
                if (!st.AnyLoaded) continue;
                if (st.Leases > 0 || UsesAny(st, inUse)) { kept?.Add(_index.AtlasPath(a)); continue; }
                foreach (var s in st.Sprites.Values) DestroyObject(s);
                st.Sprites.Clear();
                Unload(st.Pages);
                Unload(st.Masks);
                released++;
            }
            return released;
        }

        /// <summary>Loads every page under a path prefix without stalling a frame (masks too when asked). Use as a coroutine.</summary>
        public IEnumerator Preload(string pathPrefix, bool masks = false)
        {
            foreach (int a in AtlasesUnder(pathPrefix))
            {
                var st = _atlases[a];
                int pages = _index.AtlasPageCount(a);
                st.Pages ??= new Texture2D[pages];
                st.Masks ??= new Texture2D[pages];
                for (int p = 0; p < pages; p++)
                {
                    if (st.Pages[p] == null)
                    {
                        var req = Resources.LoadAsync<Texture2D>(Root + "/" + _index.GetString(_index.Page(a, p).ImageId));
                        yield return req;
                        if (st.Pages[p] == null) st.Pages[p] = req.asset as Texture2D;
                    }
                    int maskId = _index.Page(a, p).MaskId;
                    if (masks && maskId >= 0 && st.Masks[p] == null)
                    {
                        var req = Resources.LoadAsync<Texture2D>(Root + "/" + _index.GetString(maskId));
                        yield return req;
                        if (st.Masks[p] == null) st.Masks[p] = req.asset as Texture2D;
                    }
                }
            }
        }

        static readonly int MaskTexId = Shader.PropertyToID("_MaskTex");

        static HashSet<Texture> TexturesInUse()
        {
            var used = new HashSet<Texture>();
            var mpb = new MaterialPropertyBlock();
            foreach (var sr in UnityEngine.Object.FindObjectsByType<SpriteRenderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            {
                if (!sr.enabled) continue;
                if (sr.sprite != null) used.Add(sr.sprite.texture);
                if (sr.HasPropertyBlock())
                {
                    sr.GetPropertyBlock(mpb);
                    var mask = mpb.GetTexture(MaskTexId);
                    if (mask != null) used.Add(mask);
                }
            }
            foreach (var img in UnityEngine.Object.FindObjectsByType<UnityEngine.UI.Image>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                if (img.enabled && img.sprite != null) used.Add(img.sprite.texture);
            return used;
        }

        static bool UsesAny(AtlasState st, HashSet<Texture> used)
        {
            if (st.Pages != null) foreach (var t in st.Pages) if (t != null && used.Contains(t)) return true;
            if (st.Masks != null) foreach (var t in st.Masks) if (t != null && used.Contains(t)) return true;
            return false;
        }

        static void Unload(Texture2D[] textures)
        {
            if (textures == null) return;
            for (int i = 0; i < textures.Length; i++)
            {
                if (textures[i] != null) Resources.UnloadAsset(textures[i]);
                textures[i] = null;
            }
        }

        static void DestroyObject(UnityEngine.Object o)
        {
            if (o == null) return;
            if (Application.isPlaying) UnityEngine.Object.Destroy(o); else UnityEngine.Object.DestroyImmediate(o);
        }
    }
}
