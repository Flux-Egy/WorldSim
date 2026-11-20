using System.Collections.Generic;
using NUnit.Framework;
using UnityEngine;
using WorldSim.Presentation.Art;

namespace WorldSim.Tests.UnityOnly
{
    /// <summary>
    /// Unity-only (real Resources, real textures): the art loader reads only its index at start, loads a page the first
    /// time one of its frames is used, loads masks separately, and never releases an atlas something still shows.
    /// </summary>
    public class ArtDBLoadingTests
    {
        const string Tree = "tree_5_0";                       // Nature/nature_props (no mask)
        const string Person = "p_adult_m_poor_robe_turban_0"; // Characters/people (recolours)
        readonly List<GameObject> _spawned = new List<GameObject>();

        [TearDown]
        public void TearDown()
        {
            foreach (var go in _spawned) if (go != null) Object.DestroyImmediate(go);
            _spawned.Clear();
        }

        GameObject Show(Sprite s)
        {
            var go = new GameObject("ArtDBTest");
            go.AddComponent<SpriteRenderer>().sprite = s;
            _spawned.Add(go);
            return go;
        }

        [Test]
        public void Load_ReadsOnlyTheIndex()
        {
            var db = WorldSimArtDB.Load();
            Assert.Greater(db.FrameCount, 20000);
            Assert.AreEqual(0, db.LoadedAtlasCount);
            Assert.AreEqual(0, db.LoadedTextureBytes);
        }

        [Test]
        public void Sprite_LoadsOnlyItsOwnPage_AndNotTheMask()
        {
            var db = WorldSimArtDB.Load();
            var s = db.GetSprite(Person);
            Assert.IsNotNull(s);
            Assert.AreEqual(1, db.LoadedAtlasCount);
            Assert.IsTrue(db.TryGetFrameId(Person, out int id));
            var f = db.Frame(id);
            Assert.IsTrue(db.IsPageLoaded(f.Atlas, f.Page));
            Assert.IsFalse(db.IsMaskLoaded(f.Atlas, f.Page), "masks must load only when asked for");
            Assert.IsNotNull(db.GetMask(Person));
            Assert.IsTrue(db.IsMaskLoaded(f.Atlas, f.Page));
            Assert.AreEqual(f.W, (int)s.rect.width);
            Assert.AreEqual(f.H, (int)s.rect.height);
        }

        [Test]
        public void Release_UnloadsUnusedAtlas_AndDestroysItsSprites()
        {
            var db = WorldSimArtDB.Load();
            var s = db.GetSprite(Tree);
            Assert.IsNotNull(s);
            Assert.AreEqual(1, db.Release("Nature"));
            Assert.AreEqual(0, db.LoadedAtlasCount);
            Assert.IsTrue(s == null, "sprites made from a released page must be destroyed");
            Assert.IsNotNull(db.GetSprite(Tree), "a released atlas loads again on demand");
        }

        [Test]
        public void Release_KeepsAtlasShownByASpriteRenderer()
        {
            var db = WorldSimArtDB.Load();
            var go = Show(db.GetSprite(Tree));
            var kept = new List<string>();
            Assert.AreEqual(0, db.Release("Nature", kept));
            Assert.AreEqual(1, kept.Count);
            Assert.AreEqual(1, db.LoadedAtlasCount);
            Object.DestroyImmediate(go);
            Assert.AreEqual(1, db.Release("Nature"));
        }

        [Test]
        public void Release_KeepsLeasedAtlas()
        {
            var db = WorldSimArtDB.Load();
            var lease = db.Acquire("Nature");
            db.GetSprite(Tree);
            Assert.AreEqual(0, db.Release("Nature"));
            lease.Dispose();
            Assert.AreEqual(1, db.Release("Nature"));
        }

        [Test]
        public void Release_KeepsAtlasWhoseMaskIsInUse()
        {
            // WorldSimRecolor uses the shared instance and puts the mask in a MaterialPropertyBlock.
            var db = WorldSimArtDB.Instance;
            var go = new GameObject("ArtDBRecolorTest");
            _spawned.Add(go);
            go.AddComponent<SpriteRenderer>();
            go.AddComponent<WorldSimRecolor>().SetFrame(Person);
            Assert.AreEqual(0, db.Release("Characters/people"));
            Object.DestroyImmediate(go);
            Assert.AreEqual(1, db.Release("Characters/people"));
        }

        [Test]
        public void UvRect_MatchesTheSpriteRect()
        {
            var db = WorldSimArtDB.Load();
            Assert.IsTrue(db.TryGetFrameId(Person, out int id));
            var s = db.GetSprite(id);
            var uv = db.UvRect(id);
            var tex = s.texture;
            Assert.AreEqual(s.rect.x / tex.width, uv.x, 1e-6f);
            Assert.AreEqual(s.rect.y / tex.height, uv.y, 1e-6f);
            Assert.AreEqual(s.rect.width / tex.width, uv.z, 1e-6f);
            Assert.AreEqual(s.rect.height / tex.height, uv.w, 1e-6f);
        }
    }
}
