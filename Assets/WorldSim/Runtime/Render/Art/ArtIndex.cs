using System;
using System.Text;

namespace WorldSim.Render.Art
{
    /// <summary>One frame of the art pack, as stored in the index. Pixel rect has a top-left origin.</summary>
    public readonly struct ArtFrame
    {
        public readonly int Atlas, Page, X, Y, W, H, FirstAnchor, AnchorCount, NameId;
        public readonly float PivotX, PivotY; // normalised, from the bottom-left (Unity convention)
        public readonly bool Recolor;

        public ArtFrame(int nameId, int atlas, int page, bool recolor, int x, int y, int w, int h, float pivotX, float pivotY, int firstAnchor, int anchorCount)
        {
            NameId = nameId; Atlas = atlas; Page = page; Recolor = recolor; X = x; Y = y; W = w; H = h;
            PivotX = pivotX; PivotY = pivotY; FirstAnchor = firstAnchor; AnchorCount = anchorCount;
        }
    }

    /// <summary>One texture page of an atlas; mask is -1 when the page has no recolour mask.</summary>
    public readonly struct ArtPage
    {
        public readonly int ImageId, MaskId, Width, Height;
        public ArtPage(int imageId, int maskId, int width, int height) { ImageId = imageId; MaskId = maskId; Width = width; Height = height; }
    }

    /// <summary>
    /// Read-only view of art_index.bytes, written by Tools/ArtIndex/build_art_index.py. Pure C# (no Unity), so the
    /// game, Burst-side code and the .NET tests share it. Name lookups hash the name (FNV-1a 64 over UTF-8) and binary
    /// search a sorted hash table, then confirm the bytes: no per-name strings are created at load time.
    ///
    /// Format v1, little-endian: "WSAI", u32 version;
    ///   strings: u32 n, n x (u32 offset, u16 length), u32 blobLength, blob (UTF-8)
    ///   atlases: u32 n, n x (u32 pathId, u16 ppu, u16 pageCount, pageCount x (u32 imageId, u32 maskId|0xFFFFFFFF, u16 w, u16 h))
    ///   frames:  u32 n, n x u64 nameHash (sorted), n x (u32 nameId, u16 atlas, u8 page, u8 flags(1=recolor), u16 x, y, w, h,
    ///            f32 pivotX, f32 pivotY, u32 firstAnchor, u16 anchorCount)
    ///   anchors: u32 n, n x (u32 nameId, i16 x, i16 y)      x/y in px from the frame's top-left
    ///   anims:   u32 n, n x u64 nameHash (sorted), n x (u32 nameId, f32 fps, u8 loop, u32 firstFrame, u16 frameCount,
    ///            u32 firstEvent, u16 eventCount)
    ///   animFrames: u32 n, n x i32 frame index;   events: u32 n, n x (u16 frame, u32 nameId)
    /// </summary>
    public sealed class ArtIndex
    {
        public const int Version = 1;
        const ulong FnvOffset = 0xCBF29CE484222325UL, FnvPrime = 0x100000001B3UL;

        readonly byte[] _blob;
        readonly int[] _strOffset, _strLength;
        readonly string[] _strCache;
        readonly int[] _atlasPath, _atlasPpu, _atlasFirstPage, _atlasPageCount;
        readonly ArtPage[] _pages;
        readonly ulong[] _frameHash, _animHash;
        readonly ArtFrame[] _frames;
        readonly int[] _anchorName; readonly short[] _anchorX, _anchorY;
        readonly int[] _animName, _animFirstFrame, _animFrameCount, _animFirstEvent, _animEventCount;
        readonly float[] _animFps; readonly bool[] _animLoop;
        readonly int[] _animFrames;
        readonly int[] _eventFrame, _eventName;

        public int AtlasCount => _atlasPath.Length;
        public int FrameCount => _frames.Length;
        public int AnimCount => _animName.Length;

        ArtIndex(byte[] d)
        {
            int p = 0;
            if (d.Length < 8 || d[0] != 'W' || d[1] != 'S' || d[2] != 'A' || d[3] != 'I') throw new FormatException("not an art index");
            p = 4;
            int version = I32(d, ref p);
            if (version != Version) throw new FormatException("art index version " + version + ", expected " + Version);

            int ns = I32(d, ref p);
            _strOffset = new int[ns]; _strLength = new int[ns]; _strCache = new string[ns];
            for (int i = 0; i < ns; i++) { _strOffset[i] = I32(d, ref p); _strLength[i] = U16(d, ref p); }
            int blobLen = I32(d, ref p);
            _blob = new byte[blobLen];
            Buffer.BlockCopy(d, p, _blob, 0, blobLen); p += blobLen;

            int na = I32(d, ref p);
            _atlasPath = new int[na]; _atlasPpu = new int[na]; _atlasFirstPage = new int[na]; _atlasPageCount = new int[na];
            var pages = new System.Collections.Generic.List<ArtPage>();
            for (int a = 0; a < na; a++)
            {
                _atlasPath[a] = I32(d, ref p); _atlasPpu[a] = U16(d, ref p); _atlasPageCount[a] = U16(d, ref p); _atlasFirstPage[a] = pages.Count;
                for (int k = 0; k < _atlasPageCount[a]; k++)
                {
                    int img = I32(d, ref p); uint mask = unchecked((uint)I32(d, ref p)); int w = U16(d, ref p), h = U16(d, ref p);
                    pages.Add(new ArtPage(img, mask == 0xFFFFFFFFu ? -1 : (int)mask, w, h));
                }
            }
            _pages = pages.ToArray();

            int nf = I32(d, ref p);
            _frameHash = new ulong[nf];
            for (int i = 0; i < nf; i++) _frameHash[i] = U64(d, ref p);
            _frames = new ArtFrame[nf];
            for (int i = 0; i < nf; i++)
            {
                int name = I32(d, ref p), atlas = U16(d, ref p), page = d[p++], flags = d[p++];
                int x = U16(d, ref p), y = U16(d, ref p), w = U16(d, ref p), h = U16(d, ref p);
                float px = F32(d, ref p), py = F32(d, ref p);
                int fa = I32(d, ref p), ac = U16(d, ref p);
                _frames[i] = new ArtFrame(name, atlas, page, (flags & 1) != 0, x, y, w, h, px, py, fa, ac);
            }

            int nan = I32(d, ref p);
            _anchorName = new int[nan]; _anchorX = new short[nan]; _anchorY = new short[nan];
            for (int i = 0; i < nan; i++) { _anchorName[i] = I32(d, ref p); _anchorX[i] = unchecked((short)U16(d, ref p)); _anchorY[i] = unchecked((short)U16(d, ref p)); }

            int nm = I32(d, ref p);
            _animHash = new ulong[nm];
            for (int i = 0; i < nm; i++) _animHash[i] = U64(d, ref p);
            _animName = new int[nm]; _animFps = new float[nm]; _animLoop = new bool[nm];
            _animFirstFrame = new int[nm]; _animFrameCount = new int[nm]; _animFirstEvent = new int[nm]; _animEventCount = new int[nm];
            for (int i = 0; i < nm; i++)
            {
                _animName[i] = I32(d, ref p); _animFps[i] = F32(d, ref p); _animLoop[i] = d[p++] != 0;
                _animFirstFrame[i] = I32(d, ref p); _animFrameCount[i] = U16(d, ref p);
                _animFirstEvent[i] = I32(d, ref p); _animEventCount[i] = U16(d, ref p);
            }
            int naf = I32(d, ref p);
            _animFrames = new int[naf];
            for (int i = 0; i < naf; i++) _animFrames[i] = I32(d, ref p);
            int ne = I32(d, ref p);
            _eventFrame = new int[ne]; _eventName = new int[ne];
            for (int i = 0; i < ne; i++) { _eventFrame[i] = U16(d, ref p); _eventName[i] = I32(d, ref p); }
            if (p != d.Length) throw new FormatException("art index has " + (d.Length - p) + " trailing bytes");
        }

        public static ArtIndex Parse(byte[] data) => new ArtIndex(data ?? throw new ArgumentNullException(nameof(data)));

        // ---- strings ----
        public string GetString(int id)
        {
            if (id < 0) return null;
            return _strCache[id] ??= Encoding.UTF8.GetString(_blob, _strOffset[id], _strLength[id]);
        }

        bool StringEquals(int id, string s)
        {
            int len = _strLength[id], off = _strOffset[id];
            if (s.Length == len)
            {
                for (int i = 0; i < len; i++)
                {
                    char c = s[i];
                    if (c >= 0x80) return GetString(id) == s;   // non-ASCII: fall back to a full compare
                    if (_blob[off + i] != (byte)c) return false;
                }
                return true;
            }
            return GetString(id) == s;
        }

        /// <summary>FNV-1a 64 over the UTF-8 bytes of the name (same as the Python builder).</summary>
        public static ulong Hash(string s)
        {
            ulong h = FnvOffset;
            unchecked
            {
                for (int i = 0; i < s.Length; i++)
                {
                    char c = s[i];
                    if (c >= 0x80)
                    {
                        h = FnvOffset;
                        foreach (byte b in Encoding.UTF8.GetBytes(s)) h = (h ^ b) * FnvPrime;
                        return h;
                    }
                    h = (h ^ c) * FnvPrime;
                }
            }
            return h;
        }

        static int Find(ulong[] hashes, ulong h)
        {
            int lo = 0, hi = hashes.Length - 1;
            while (lo <= hi)
            {
                int mid = (lo + hi) >> 1;
                ulong v = hashes[mid];
                if (v == h) return mid;
                if (v < h) lo = mid + 1; else hi = mid - 1;
            }
            return -1;
        }

        // ---- atlases and pages ----
        public string AtlasPath(int atlas) => GetString(_atlasPath[atlas]);
        public int AtlasPpu(int atlas) => _atlasPpu[atlas];
        public int AtlasPageCount(int atlas) => _atlasPageCount[atlas];
        public ArtPage Page(int atlas, int page) => _pages[_atlasFirstPage[atlas] + page];

        /// <summary>Atlas whose path is exactly <paramref name="path"/> (e.g. "Characters/People/people_actions"), or -1.</summary>
        public int FindAtlas(string path)
        {
            for (int a = 0; a < _atlasPath.Length; a++) if (StringEquals(_atlasPath[a], path)) return a;
            return -1;
        }

        // ---- frames ----
        public bool TryGetFrameId(string name, out int id)
        {
            id = -1;
            if (string.IsNullOrEmpty(name)) return false;
            int i = Find(_frameHash, Hash(name));
            if (i < 0 || !StringEquals(_frames[i].NameId, name)) return false;
            id = i;
            return true;
        }

        public ArtFrame Frame(int id) => _frames[id];
        public string FrameName(int id) => GetString(_frames[id].NameId);

        /// <summary>Anchor of a frame in px from the frame's top-left.</summary>
        public bool TryGetAnchor(int frameId, string anchor, out int x, out int y)
        {
            var f = _frames[frameId];
            for (int i = f.FirstAnchor; i < f.FirstAnchor + f.AnchorCount; i++)
                if (StringEquals(_anchorName[i], anchor)) { x = _anchorX[i]; y = _anchorY[i]; return true; }
            x = y = 0;
            return false;
        }

        // ---- animations ----
        public bool TryGetAnimId(string name, out int id)
        {
            id = -1;
            if (string.IsNullOrEmpty(name)) return false;
            int i = Find(_animHash, Hash(name));
            if (i < 0 || !StringEquals(_animName[i], name)) return false;
            id = i;
            return true;
        }

        public string AnimName(int anim) => GetString(_animName[anim]);
        public float AnimFps(int anim) => _animFps[anim];
        public bool AnimLoop(int anim) => _animLoop[anim];
        public int AnimFrameCount(int anim) => _animFrameCount[anim];
        public int AnimFrame(int anim, int i) => _animFrames[_animFirstFrame[anim] + i];
        public int AnimEventCount(int anim) => _animEventCount[anim];
        public int AnimEventFrame(int anim, int i) => _eventFrame[_animFirstEvent[anim] + i];
        public string AnimEventName(int anim, int i) => GetString(_eventName[_animFirstEvent[anim] + i]);

        // ---- little-endian readers ----
        static int I32(byte[] d, ref int p) { int v = d[p] | (d[p + 1] << 8) | (d[p + 2] << 16) | (d[p + 3] << 24); p += 4; return v; }
        static int U16(byte[] d, ref int p) { int v = d[p] | (d[p + 1] << 8); p += 2; return v; }
        static ulong U64(byte[] d, ref int p)
        {
            ulong lo = unchecked((uint)I32(d, ref p)), hi = unchecked((uint)I32(d, ref p));
            return lo | (hi << 32);
        }
        static float F32(byte[] d, ref int p) => BitConverter.Int32BitsToSingle(I32(d, ref p));
    }
}
