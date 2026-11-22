using System.Collections.Generic;
using UnityEngine;
using WorldSim.Render;
using WorldSim.Render.Art;
using WorldSim.Render.Terrain;

namespace WorldSim.Presentation.Terrain
{
    /// <summary>
    /// CPU pixels of the art pack for the terrain baker. GPU textures can't be read back (terrain pages are ASTC on
    /// Android), so the pages the baker needs ship as raw PNG bytes in <c>Resources/WorldSimArt/Raw</c>
    /// (<c>Tools/ArtIndex/export_raw.py</c>) and are decoded with <see cref="PngDecoder"/>. Load on the main thread
    /// (Resources), then <see cref="Pixel"/> is thread-safe: pages decode once, under a lock.
    /// </summary>
    public sealed class RawArtPixels : IArtPixels
    {
        readonly ArtIndex _ix;
        readonly Dictionary<string, byte[]> _raw = new Dictionary<string, byte[]>();
        readonly Dictionary<int, (uint[] px, int w, int h)> _pages = new Dictionary<int, (uint[], int, int)>();
        readonly Dictionary<int, (byte[] codes, int w, int h)> _masks = new Dictionary<int, (byte[], int, int)>();
        uint[] _lut;
        readonly object _lock = new object();

        public RawArtPixels(ArtIndex index)
        {
            _ix = index;
            foreach (var t in Resources.LoadAll<TextAsset>("WorldSimArt/Raw"))
            {
                _raw[t.name] = t.bytes;
                Resources.UnloadAsset(t);
            }
        }

        /// <summary>Raw pages found in Resources (the baker needs the terrain, LOD and nature pages).</summary>
        public int RawPageCount => _raw.Count;

        public bool TryFrame(string name, out int id) => _ix.TryGetFrameId(name, out id);
        public int Width(int id) => _ix.Frame(id).W;
        public int Height(int id) => _ix.Frame(id).H;
        public float PivotX(int id) => _ix.Frame(id).PivotX;
        public float PivotY(int id) => _ix.Frame(id).PivotY;

        static string Key(string path) => path.Replace("/", "__");

        public uint Pixel(int id, int x, int y)
        {
            var f = _ix.Frame(id);
            var page = Page(f.Atlas, f.Page);
            if (page.px == null) return 0xFFFF00FF;                       // missing raw page: magenta, easy to spot
            int gy = page.h - 1 - (f.Y + y);                              // decoder rows are bottom-up
            return page.px[gy * page.w + f.X + x];
        }

        (uint[] px, int w, int h) Page(int atlas, int pageIndex)
        {
            int key = atlas * 64 + pageIndex;
            lock (_lock)
            {
                if (_pages.TryGetValue(key, out var p)) return p;
                var pg = _ix.Page(atlas, pageIndex);
                p = (null, 0, 0);
                if (_raw.TryGetValue(Key(_ix.GetString(pg.ImageId)), out byte[] bytes))
                {
                    var px = PngDecoder.Decode(bytes, out int w, out int h);
                    p = (px, w, h);
                }
                _pages[key] = p;
                return p;
            }
        }

        public bool Mask(int id, int x, int y, out int region, out int step)
        {
            region = 0; step = 0;
            var f = _ix.Frame(id);
            var pg = _ix.Page(f.Atlas, f.Page);
            if (pg.MaskId < 0) return false;
            int key = f.Atlas * 64 + f.Page;
            (byte[] codes, int w, int h) m;
            lock (_lock)
            {
                if (!_masks.TryGetValue(key, out m))
                {
                    m = (null, 0, 0);
                    if (_raw.TryGetValue(Key(_ix.GetString(pg.MaskId)), out byte[] bytes))
                    {
                        var px = PngDecoder.Decode(bytes, out int w, out int h);
                        var codes = new byte[px.Length];
                        for (int i = 0; i < px.Length; i++) codes[i] = (byte)Rgba.R(px[i]);
                        m = (codes, w, h);
                    }
                    _masks[key] = m;
                }
                if (_lut == null && _raw.TryGetValue("mask_lut", out byte[] lut)) _lut = PngDecoder.Decode(lut, out _, out _);
            }
            if (m.codes == null || _lut == null) return false;
            int code = m.codes[(m.h - 1 - (f.Y + y)) * m.w + f.X + x];
            uint e = _lut[code];
            if (code == 0 || Rgba.A(e) == 0) return false;
            region = Rgba.R(e) / 36;
            step = (Rgba.G(e) - 40 + 22) / 44;
            return region > 0;
        }
    }
}
