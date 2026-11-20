using System;
using System.IO;
using NUnit.Framework;
using WorldSim.Render.Art;

namespace WorldSim.Tests
{
    public class ArtIndexTests
    {
        const string Rel = "Assets/WorldSim/Resources/WorldSimArt";

        /// <summary>Finds the art folder from the test's working directory or binary location (Unity: project root; .NET: Tools/CoreTests/bin/...).</summary>
        internal static string ArtDir()
        {
            foreach (var start in new[] { Directory.GetCurrentDirectory(), AppContext.BaseDirectory })
            {
                var d = new DirectoryInfo(start);
                for (int i = 0; d != null && i < 8; i++, d = d.Parent)
                {
                    var p = Path.Combine(d.FullName, Rel);
                    if (File.Exists(Path.Combine(p, "art_index.bytes"))) return p;
                }
            }
            Assert.Fail("art_index.bytes not found above " + Directory.GetCurrentDirectory());
            return null;
        }

        static ArtIndex _index;
        internal static ArtIndex Index => _index ??= ArtIndex.Parse(File.ReadAllBytes(Path.Combine(ArtDir(), "art_index.bytes")));

        [Test]
        public void Hash_IsFnv1a64()
        {
            Assert.AreEqual(0xCBF29CE484222325UL, ArtIndex.Hash(""));
            Assert.AreEqual(0xAF63DC4C8601EC8CUL, ArtIndex.Hash("a"));
            Assert.AreEqual(0x85944171F73967E8UL, ArtIndex.Hash("foobar"));
        }

        [Test]
        public void Index_HasEveryAtlasAndPage()
        {
            var ix = Index;
            Assert.Greater(ix.AtlasCount, 0);
            Assert.Greater(ix.FrameCount, 0);
            for (int a = 0; a < ix.AtlasCount; a++)
            {
                Assert.AreEqual(16, ix.AtlasPpu(a), ix.AtlasPath(a));
                for (int p = 0; p < ix.AtlasPageCount(a); p++)
                {
                    var page = ix.Page(a, p);
                    Assert.IsTrue(File.Exists(Path.Combine(ArtDir(), ix.GetString(page.ImageId) + ".png")), ix.GetString(page.ImageId));
                    if (page.MaskId >= 0) Assert.IsTrue(File.Exists(Path.Combine(ArtDir(), ix.GetString(page.MaskId) + ".png")), ix.GetString(page.MaskId));
                }
            }
        }

        [Test]
        public void EveryFrame_IsFoundByItsOwnName_AndFitsItsPage()
        {
            var ix = Index;
            for (int i = 0; i < ix.FrameCount; i++)
            {
                string name = ix.FrameName(i);
                Assert.IsTrue(ix.TryGetFrameId(name, out int id), name);
                Assert.AreEqual(i, id, name);
                var f = ix.Frame(i);
                var page = ix.Page(f.Atlas, f.Page);
                Assert.IsTrue(f.X >= 0 && f.Y >= 0 && f.X + f.W <= page.Width && f.Y + f.H <= page.Height, name);
                if (f.Recolor) Assert.GreaterOrEqual(page.MaskId, 0, name + " recolours but its page has no mask");
            }
        }

        [Test]
        public void EveryAnimation_IsFound_AndReferencesValidFrames()
        {
            var ix = Index;
            for (int a = 0; a < ix.AnimCount; a++)
            {
                string name = ix.AnimName(a);
                Assert.IsTrue(ix.TryGetAnimId(name, out int id), name);
                Assert.AreEqual(a, id, name);
                Assert.Greater(ix.AnimFrameCount(a), 0, name);
                Assert.Greater(ix.AnimFps(a), 0f, name);
                for (int k = 0; k < ix.AnimFrameCount(a); k++)
                    Assert.IsTrue(ix.AnimFrame(a, k) >= 0 && ix.AnimFrame(a, k) < ix.FrameCount, name);
                for (int e = 0; e < ix.AnimEventCount(a); e++)
                    Assert.IsTrue(ix.AnimEventFrame(a, e) < ix.AnimFrameCount(a), name + " event past the last frame");
            }
        }

        [Test]
        public void UnknownNames_AreNotFound()
        {
            Assert.IsFalse(Index.TryGetFrameId("no_such_frame_xyz", out _));
            Assert.IsFalse(Index.TryGetFrameId("", out _));
            Assert.IsFalse(Index.TryGetFrameId(null, out _));
            Assert.IsFalse(Index.TryGetAnimId("no_such_anim_xyz", out _));
            Assert.IsFalse(Index.TryGetFrameId("é_non_ascii", out _));
        }

        [Test]
        public void RejectsCorruptData()
        {
            Assert.Throws<FormatException>(() => ArtIndex.Parse(new byte[] { 1, 2, 3, 4, 5, 6, 7, 8 }));
            var bytes = File.ReadAllBytes(Path.Combine(ArtDir(), "art_index.bytes"));
            var withTrailing = new byte[bytes.Length + 1];
            Buffer.BlockCopy(bytes, 0, withTrailing, 0, bytes.Length);
            Assert.Throws<FormatException>(() => ArtIndex.Parse(withTrailing));
        }

#if !UNITY_2017_1_OR_NEWER
        // .NET only (System.Text.Json): every field of every frame, anchor and animation matches the source JSON.
        [Test]
        public void Index_MatchesTheAtlasJson()
        {
            var ix = Index;
            string dir = ArtDir();
            using var idx = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "atlas_index.json")));
            int frames = 0, anims = 0, atlas = 0;
            foreach (var pathEl in idx.RootElement.GetProperty("atlases").EnumerateArray())
            {
                string path = pathEl.GetString();
                Assert.AreEqual(path, ix.AtlasPath(atlas));
                using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, path + ".json")));
                var root = doc.RootElement;
                foreach (var f in root.GetProperty("frameList").EnumerateArray())
                {
                    string name = f.GetProperty("name").GetString();
                    Assert.IsTrue(ix.TryGetFrameId(name, out int id), name);
                    var fr = ix.Frame(id);
                    Assert.AreEqual(atlas, fr.Atlas, name);
                    Assert.AreEqual(f.GetProperty("page").GetInt32(), fr.Page, name);
                    Assert.AreEqual(f.GetProperty("x").GetInt32(), fr.X, name);
                    Assert.AreEqual(f.GetProperty("y").GetInt32(), fr.Y, name);
                    Assert.AreEqual(f.GetProperty("w").GetInt32(), fr.W, name);
                    Assert.AreEqual(f.GetProperty("h").GetInt32(), fr.H, name);
                    Assert.AreEqual((float)f.GetProperty("pivotX").GetDouble(), fr.PivotX, name);
                    Assert.AreEqual((float)f.GetProperty("pivotY").GetDouble(), fr.PivotY, name);
                    bool recolor = f.TryGetProperty("recolor", out var rc) && rc.GetBoolean();
                    Assert.AreEqual(recolor, fr.Recolor, name);
                    if (f.TryGetProperty("anchors", out var an) && an.ValueKind == System.Text.Json.JsonValueKind.Array)
                    {
                        Assert.AreEqual(an.GetArrayLength(), fr.AnchorCount, name);
                        foreach (var a in an.EnumerateArray())
                        {
                            Assert.IsTrue(ix.TryGetAnchor(id, a.GetProperty("name").GetString(), out int ax, out int ay), name);
                            Assert.AreEqual(a.GetProperty("x").GetInt32(), ax, name);
                            Assert.AreEqual(a.GetProperty("y").GetInt32(), ay, name);
                        }
                    }
                    frames++;
                }
                if (root.TryGetProperty("animList", out var al) && al.ValueKind == System.Text.Json.JsonValueKind.Array)
                    foreach (var m in al.EnumerateArray())
                    {
                        string name = m.GetProperty("name").GetString();
                        Assert.IsTrue(ix.TryGetAnimId(name, out int id), name);
                        Assert.AreEqual((float)m.GetProperty("fps").GetDouble(), ix.AnimFps(id), name);
                        Assert.AreEqual(m.TryGetProperty("loop", out var lp) && lp.GetBoolean(), ix.AnimLoop(id), name);
                        var fl = m.GetProperty("frames");
                        Assert.AreEqual(fl.GetArrayLength(), ix.AnimFrameCount(id), name);
                        int k = 0;
                        foreach (var fn in fl.EnumerateArray()) Assert.AreEqual(fn.GetString(), ix.FrameName(ix.AnimFrame(id, k++)), name);
                        int evs = m.TryGetProperty("events", out var ev) && ev.ValueKind == System.Text.Json.JsonValueKind.Array ? ev.GetArrayLength() : 0;
                        Assert.AreEqual(evs, ix.AnimEventCount(id), name);
                        k = 0;
                        if (evs > 0)
                            foreach (var e in ev.EnumerateArray())
                            {
                                Assert.AreEqual(e.GetProperty("frame").GetInt32(), ix.AnimEventFrame(id, k), name);
                                Assert.AreEqual(e.GetProperty("name").GetString(), ix.AnimEventName(id, k), name);
                                k++;
                            }
                        anims++;
                    }
                atlas++;
            }
            Assert.AreEqual(ix.AtlasCount, atlas);
            Assert.AreEqual(ix.FrameCount, frames);
            Assert.AreEqual(ix.AnimCount, anims);
        }
#endif
    }
}
