using System;
using System.Collections.Generic;
using UnityEngine;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Runtime access to the generated art pack (Resources/WorldSimArt). Reads the atlas JSON files listed in
    /// atlas_index.json, loads the PNG pages, and builds sprites on demand with Sprite.Create, so no editor slicing
    /// and no extra package are needed. Names, pivots, anchors, tags and animations come from the JSON.
    /// Pixel art: every page is imported point-filtered and uncompressed by WorldSimArtPostprocessor.
    /// </summary>
    public sealed class WorldSimArtDB
    {
        public const string Root = "WorldSimArt";
        const string RecolorShaderName = "WorldSim/RecolorSprite";

#pragma warning disable 0649 // JSON DTOs: fields are filled by JsonUtility
        [Serializable] sealed class IndexJ { public string[] atlases; }
        [Serializable] sealed class AnchorJ { public string name; public int x; public int y; }
        [Serializable] sealed class FrameJ
        {
            public string name; public int page; public int x; public int y; public int w; public int h;
            public float pivotX; public float pivotY; public bool recolor; public AnchorJ[] anchors; public string tagsJson;
        }
        [Serializable] sealed class PageJ { public string image; public string mask; public int w; public int h; }
        [Serializable] sealed class EventJ { public int frame; public string name; }
        [Serializable] sealed class AnimJ { public string name; public string[] frames; public float fps; public bool loop; public EventJ[] events; }
        [Serializable] sealed class AtlasJ { public string atlas; public int ppu; public PageJ[] pageList; public FrameJ[] frameList; public AnimJ[] animList; }
#pragma warning restore 0649

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

        sealed class Entry
        {
            public FrameJ Frame;
            public Texture2D Texture;
            public Texture2D Mask;
            public int PageHeight;
            public int Ppu;
            public Sprite Sprite;
        }

        static WorldSimArtDB _instance;
        static Material _recolorMaterial;

        readonly Dictionary<string, Entry> _frames = new Dictionary<string, Entry>(StringComparer.Ordinal);
        readonly Dictionary<string, Anim> _anims = new Dictionary<string, Anim>(StringComparer.Ordinal);

        /// <summary>Lazily loaded shared instance.</summary>
        public static WorldSimArtDB Instance => _instance ??= Load();

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

        public static WorldSimArtDB Load()
        {
            var db = new WorldSimArtDB();
            var index = Resources.Load<TextAsset>(Root + "/atlas_index");
            if (index == null) { Debug.LogError("WorldSimArtDB: Resources/" + Root + "/atlas_index.json missing"); return db; }
            var list = JsonUtility.FromJson<IndexJ>(index.text);
            if (list?.atlases == null) return db;
            foreach (var path in list.atlases) db.AddAtlas(path);
            return db;
        }

        void AddAtlas(string path)
        {
            var ta = Resources.Load<TextAsset>(Root + "/" + path);
            if (ta == null) { Debug.LogWarning("WorldSimArtDB: atlas json not found: " + path); return; }
            var atlas = JsonUtility.FromJson<AtlasJ>(ta.text);
            if (atlas?.pageList == null || atlas.frameList == null) return;
            int slash = path.LastIndexOf('/');
            string dir = slash >= 0 ? path.Substring(0, slash + 1) : "";
            int ppu = atlas.ppu > 0 ? atlas.ppu : 16;

            var tex = new Texture2D[atlas.pageList.Length];
            var masks = new Texture2D[atlas.pageList.Length];
            for (int p = 0; p < atlas.pageList.Length; p++)
            {
                var page = atlas.pageList[p];
                tex[p] = Resources.Load<Texture2D>(Root + "/" + dir + StripExt(page.image));
                if (!string.IsNullOrEmpty(page.mask)) masks[p] = Resources.Load<Texture2D>(Root + "/" + dir + StripExt(page.mask));
                if (tex[p] == null) Debug.LogWarning("WorldSimArtDB: page not found: " + dir + page.image);
            }
            foreach (var f in atlas.frameList)
            {
                if (f.page < 0 || f.page >= tex.Length || tex[f.page] == null) continue;
                _frames[f.name] = new Entry
                {
                    Frame = f, Texture = tex[f.page], Mask = masks[f.page], PageHeight = atlas.pageList[f.page].h, Ppu = ppu
                };
            }
            if (atlas.animList != null)
                foreach (var a in atlas.animList)
                    {
                        var ev = a.events == null ? Array.Empty<AnimEvent>() : new AnimEvent[a.events.Length];
                        for (int i = 0; a.events != null && i < a.events.Length; i++) ev[i] = new AnimEvent(a.events[i].frame, a.events[i].name);
                        _anims[a.name] = new Anim(a.frames, a.fps, a.loop, ev);
                    }
        }

        static string StripExt(string file)
        {
            int dot = file.LastIndexOf('.');
            return dot > 0 ? file.Substring(0, dot) : file;
        }

        public int FrameCount => _frames.Count;
        public IEnumerable<string> FrameNames => _frames.Keys;
        public IEnumerable<string> AnimNames => _anims.Keys;
        public bool Has(string name) => _frames.ContainsKey(name);

        public bool TryGetSprite(string name, out Sprite sprite)
        {
            sprite = null;
            if (!_frames.TryGetValue(name, out var e)) return false;
            if (e.Sprite == null)
            {
                var f = e.Frame;
                var rect = new Rect(f.x, e.PageHeight - f.y - f.h, f.w, f.h);   // JSON is top-left origin
                e.Sprite = Sprite.Create(e.Texture, rect, new Vector2(f.pivotX, f.pivotY), e.Ppu, 0, SpriteMeshType.FullRect);
                e.Sprite.name = f.name;
            }
            sprite = e.Sprite;
            return true;
        }

        public Sprite GetSprite(string name) => TryGetSprite(name, out var s) ? s : null;

        /// <summary>Recolour mask page for this frame (null when the frame has nothing to recolour).</summary>
        public Texture2D GetMask(string name) => _frames.TryGetValue(name, out var e) && e.Frame.recolor ? e.Mask : null;

        public bool IsRecolor(string name) => _frames.TryGetValue(name, out var e) && e.Frame.recolor && e.Mask != null;

        /// <summary>Raw tag object (era, category, roof, wall, tier, species, angle, frame...) as JSON text.</summary>
        public string GetTagsJson(string name) => _frames.TryGetValue(name, out var e) ? e.Frame.tagsJson : null;

        public bool TryGetAnim(string name, out Anim anim) => _anims.TryGetValue(name, out anim);

        /// <summary>Anchor (muzzle, hand, smoke point...) in local units relative to the sprite pivot.</summary>
        public bool TryGetAnchor(string frame, string anchor, out Vector2 local)
        {
            local = default;
            if (!_frames.TryGetValue(frame, out var e) || e.Frame.anchors == null) return false;
            var f = e.Frame;
            foreach (var a in f.anchors)
            {
                if (a.name != anchor) continue;
                float px = a.x - f.pivotX * f.w;
                float py = (f.h - a.y) - f.pivotY * f.h;
                local = new Vector2(px / e.Ppu, py / e.Ppu);
                return true;
            }
            return false;
        }
    }
}
