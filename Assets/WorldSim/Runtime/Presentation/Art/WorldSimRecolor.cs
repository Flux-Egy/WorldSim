using UnityEngine;

namespace WorldSim.Presentation.Art
{
    /// <summary>
    /// Shows one pack frame on a SpriteRenderer and feeds the recolour shader: mask page, palette ramp,
    /// hit flash, sickness and night tint (MaterialPropertyBlock, no per-object materials).
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public sealed class WorldSimRecolor : MonoBehaviour
    {
        static readonly int MaskId = Shader.PropertyToID("_MaskTex");
        static readonly int RampId = Shader.PropertyToID("_RampTex");
        static readonly int FlashId = Shader.PropertyToID("_Flash");
        static readonly int SickId = Shader.PropertyToID("_Sick");
        static readonly int UseRampId = Shader.PropertyToID("_UseRamp");
        static readonly int BurnId = Shader.PropertyToID("_Burn");
        static readonly int FrostId = Shader.PropertyToID("_Frost");
        static readonly int OvergrownId = Shader.PropertyToID("_Overgrown");

        SpriteRenderer _sr;
        MaterialPropertyBlock _mpb;
        Texture2D _mask;
        public Texture2D Ramp;
        [Range(0, 1)] public float Flash;
        [Range(0, 1)] public float Sick;
        /// <summary>0 normal, ~0.4 while burning (with ov_fire_* on top), 1 = burnt shell.</summary>
        [Range(0, 1)] public float Burn;
        /// <summary>Blizzard / ice spells: blue tint plus snow on top edges.</summary>
        [Range(0, 1)] public float Frost;
        /// <summary>Abandoned ruins: moss and vine speckle.</summary>
        [Range(0, 1)] public float Overgrown;

        void Awake() { Init(); }

        void Init()
        {
            if (_sr != null) return;
            _sr = GetComponent<SpriteRenderer>();
            _mpb = new MaterialPropertyBlock();
        }

        /// <summary>Show a frame by name; switches to the recolour material when the frame has a mask.</summary>
        public void SetFrame(string frameName)
        {
            Init();
            var db = WorldSimArtDB.Instance;
            _sr.sprite = db.GetSprite(frameName);
            _mask = db.GetMask(frameName);
            if (_mask != null && WorldSimArtDB.RecolorMaterial != null) _sr.sharedMaterial = WorldSimArtDB.RecolorMaterial;
            Push();
        }

        public void SetPalette(Texture2D ramp) { Ramp = ramp; Push(); }
        public void Hit(float amount = 1f) { Flash = amount; Push(); }
        public void SetSick(float amount) { Sick = amount; Push(); }
        public void SetBuildingState(float burn, float frost, float overgrown) { Burn = burn; Frost = frost; Overgrown = overgrown; Push(); }

        void LateUpdate()
        {
            if (Flash <= 0f) return;
            Flash = Mathf.Max(0f, Flash - Time.deltaTime * 8f);
            Push();
        }

        void Push()
        {
            if (_sr == null) return;
            _sr.GetPropertyBlock(_mpb);
            if (_mask != null) _mpb.SetTexture(MaskId, _mask);
            if (Ramp != null) _mpb.SetTexture(RampId, Ramp);
            _mpb.SetFloat(UseRampId, _mask != null && Ramp != null ? 1f : 0f);
            _mpb.SetFloat(FlashId, Flash);
            _mpb.SetFloat(SickId, Sick);
            _mpb.SetFloat(BurnId, Burn);
            _mpb.SetFloat(FrostId, Frost);
            _mpb.SetFloat(OvergrownId, Overgrown);
            _sr.SetPropertyBlock(_mpb);
        }
    }
}
