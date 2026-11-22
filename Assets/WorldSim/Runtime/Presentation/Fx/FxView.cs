using System;
using System.Collections.Generic;
using UnityEngine;
using WorldSim.Presentation.Art;

namespace WorldSim.Presentation.Fx
{
    /// <summary>
    /// Short-lived effects from the art pack (Playable Alpha: interactions): animations played once or looped for a
    /// while (explosions, smoke, fire, lightning, nuke cloud), projectiles that fly to a target (meteor, bomb, missile),
    /// camera shake, a full-screen flash, and one-shot sounds that fade with zoom. Pooled sprites; timers on unscaled time.
    /// </summary>
    public sealed class FxView
    {
        sealed class Fx
        {
            public SpriteRenderer R;
            public Sprite[] Frames;
            public float Fps, Start, End;
            public bool Loop, Fade;
            public Vector3 From, To;
            public bool Flying;
            public Action OnEnd;
        }

        readonly Transform _root;
        readonly List<Fx> _active = new List<Fx>();
        readonly Stack<SpriteRenderer> _free = new Stack<SpriteRenderer>();
        readonly Dictionary<string, (Sprite[] frames, float fps)> _anims = new Dictionary<string, (Sprite[], float)>();
        readonly List<(float at, Action act)> _timers = new List<(float, Action)>();
        readonly AudioSource _audio;
        readonly SpriteRenderer _flash;
        Camera _cam;
        float _shakeUntil, _shakeAmount, _flashStart, _flashUntil;
        Vector3 _shakeOffset;
        float _now;

        public float PixelsPerTile { get; set; } = 8f;

        /// <summary>Effects grow when the camera is far out, so a strike still reads at mid and far zoom.</summary>
        float ZoomBoost => Mathf.Clamp(12f / Mathf.Max(1f, PixelsPerTile), 1f, 5f);

        public FxView(Camera cam)
        {
            _cam = cam;
            _root = new GameObject("Fx").transform;
            _audio = cam.gameObject.GetComponent<AudioSource>();
            if (_audio == null) _audio = cam.gameObject.AddComponent<AudioSource>();
            _audio.playOnAwake = false;
            var tex = new Texture2D(1, 1, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, name = "FlashPixel" };
            tex.SetPixel(0, 0, Color.white);
            tex.Apply(false, true);
            _flash = new GameObject("Flash").AddComponent<SpriteRenderer>();
            _flash.sprite = Sprite.Create(tex, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 1f);
            _flash.sortingOrder = 32000;
            _flash.enabled = false;
        }

        (Sprite[] frames, float fps) Anim(string name)
        {
            if (_anims.TryGetValue(name, out var a)) return a;
            var db = WorldSimArtDB.Instance;
            if (db.TryGetAnim(name, out var anim) && anim.Frames.Length > 0)
            {
                var f = new Sprite[anim.Frames.Length];
                for (int i = 0; i < f.Length; i++) f[i] = db.GetSprite(anim.Frames[i]);
                a = (f, anim.Fps > 0 ? anim.Fps : 8f);
            }
            else
            {
                var s = db.GetSprite(name);
                a = (s != null ? new[] { s } : new Sprite[0], 1f);
                if (s == null) Debug.LogWarning("[WorldSim] fx art missing: " + name);
            }
            _anims[name] = a;
            return a;
        }

        /// <summary>A frame sequence by explicit names (e.g. the nuke cloud nuke_0..nuke_12).</summary>
        public void PlayFrames(string prefix, int count, float fps, Vector3 pos, float scale, int order, float holdLast = 0f)
        {
            string key = prefix + "#" + count;
            if (!_anims.ContainsKey(key))
            {
                var db = WorldSimArtDB.Instance;
                var f = new List<Sprite>();
                for (int i = 0; i < count; i++) { var s = db.GetSprite(prefix + i); if (s != null) f.Add(s); }
                _anims[key] = (f.ToArray(), fps);
            }
            Play(key, pos, scale, order, loopSeconds: 0f, holdLast: holdLast);
        }

        /// <summary>Plays an animation once (loopSeconds = 0) or loops it for that many seconds, fading at the end.</summary>
        public void Play(string anim, Vector3 pos, float scale = 1f, int order = 31000, float loopSeconds = 0f, float holdLast = 0f)
        {
            var a = Anim(anim);
            if (a.frames.Length == 0) return;
            var fx = new Fx
            {
                R = Get(), Frames = a.frames, Fps = a.fps, Start = _now, Loop = loopSeconds > 0f, Fade = true,
                End = _now + (loopSeconds > 0f ? loopSeconds : a.frames.Length / a.fps + holdLast),
            };
            fx.R.transform.localPosition = pos;
            fx.R.transform.localScale = new Vector3(scale * ZoomBoost, scale * ZoomBoost, 1f);
            fx.R.sortingOrder = order;
            fx.R.sprite = a.frames[0];
            _active.Add(fx);
        }

        /// <summary>A projectile (a sprite or animation) flying from one point to another, then the callback.</summary>
        public void Fly(string anim, Vector3 from, Vector3 to, float seconds, float scale, Action onArrive)
        {
            var a = Anim(anim);
            if (a.frames.Length == 0) { onArrive?.Invoke(); return; }
            var fx = new Fx
            {
                R = Get(), Frames = a.frames, Fps = a.fps, Start = _now, End = _now + seconds, Loop = true,
                From = from, To = to, Flying = true, OnEnd = onArrive,
            };
            fx.R.transform.localScale = new Vector3(scale * ZoomBoost, scale * ZoomBoost, 1f);
            fx.R.sortingOrder = 31500;
            fx.R.sprite = a.frames[0];
            Vector3 d = to - from;
            fx.R.flipX = d.x < 0f;
            _active.Add(fx);
        }

        public void After(float seconds, Action act) => _timers.Add((_now + seconds, act));

        public void Shake(float amount, float seconds)
        {
            _shakeAmount = Mathf.Max(amount, _now < _shakeUntil ? _shakeAmount : 0f);
            _shakeUntil = Mathf.Max(_shakeUntil, _now + seconds);
        }

        public void Flash(float seconds) { _flashStart = _now; _flashUntil = _now + seconds; }

        /// <summary>One-shot sound, quieter when zoomed far out (owner: "sounds fade with far zoom").</summary>
        public void Sound(string clip, float volume = 1f)
        {
            var c = WorldSimAudioDB.Instance.Sfx(clip);
            if (c == null) return;
            float zoomFade = Mathf.Clamp01(Mathf.InverseLerp(1.5f, 8f, PixelsPerTile)) * 0.75f + 0.25f;
            _audio.PlayOneShot(c, volume * zoomFade);
        }

        public void Tick(float now)
        {
            _now = now;
            // Undo last frame's shake before anything reads the camera.
            if (_shakeOffset != Vector3.zero) { _cam.transform.position -= _shakeOffset; _shakeOffset = Vector3.zero; }

            for (int i = _timers.Count - 1; i >= 0; i--)
                if (now >= _timers[i].at) { var act = _timers[i].act; _timers.RemoveAt(i); act(); }

            for (int i = _active.Count - 1; i >= 0; i--)
            {
                Fx fx = _active[i];
                float t = now - fx.Start;
                int f = (int)(t * fx.Fps);
                fx.R.sprite = fx.Frames[fx.Loop ? f % fx.Frames.Length : Mathf.Min(f, fx.Frames.Length - 1)];
                if (fx.Flying)
                {
                    float k = Mathf.Clamp01(t / Mathf.Max(0.01f, fx.End - fx.Start));
                    fx.R.transform.localPosition = Vector3.Lerp(fx.From, fx.To, k * k);         // accelerates in
                }
                float left = fx.End - now;
                if (fx.Fade && !fx.Flying) fx.R.color = new Color(1f, 1f, 1f, Mathf.Clamp01(left / 0.35f));
                if (now >= fx.End)
                {
                    _active.RemoveAt(i);
                    fx.R.enabled = false;
                    fx.R.color = Color.white;
                    fx.R.flipX = false;
                    _free.Push(fx.R);
                    fx.OnEnd?.Invoke();
                }
            }

            if (now < _shakeUntil)
            {
                float k = (_shakeUntil - now) * _shakeAmount * _cam.orthographicSize * 0.02f;
                _shakeOffset = new Vector3(Mathf.Sin(now * 71f) * k, Mathf.Cos(now * 57f) * k, 0f);
                _cam.transform.position += _shakeOffset;
            }

            bool flash = now < _flashUntil;
            if (_flash.enabled != flash) _flash.enabled = flash;
            if (flash)
            {
                float h = _cam.orthographicSize * 2f;
                Vector3 cp = _cam.transform.position;
                _flash.transform.position = new Vector3(cp.x, cp.y, 0f);
                _flash.transform.localScale = new Vector3(h * _cam.aspect + 2f, h + 2f, 1f);
                _flash.color = new Color(1f, 1f, 0.94f, Mathf.Clamp01((_flashUntil - now) / Mathf.Max(0.01f, _flashUntil - _flashStart)));
            }
        }

        SpriteRenderer Get()
        {
            SpriteRenderer r = _free.Count > 0 ? _free.Pop() : null;
            if (r == null)
            {
                r = new GameObject("FxSprite").AddComponent<SpriteRenderer>();
                r.transform.SetParent(_root, false);
            }
            r.enabled = true;
            return r;
        }
    }
}
