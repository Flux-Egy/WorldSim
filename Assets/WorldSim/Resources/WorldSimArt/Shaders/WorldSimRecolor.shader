// WorldSim/RecolorSprite
// Recolours the masked parts of a sprite with the owner's palette (kingdom TEAM, culture ACC/ACC2/ROOF, person SKIN/HAIR).
// _MaskTex  (mask page of the same atlas, linear; set per renderer by WorldSimRecolor via MaterialPropertyBlock):  R = regionId*36 (1 TEAM, 2 ACC, 3 ACC2, 4 ROOF, 5 SKIN, 6 HAIR), G = shade, A = 255 if masked
// _RampTex  5 x 8 px, point filtered, row r-1 = region r. Rows 1-4: 5-step dark->light ramp. Rows 5-6: base colour in column 2.
// Also: _Flash (hit flash to white), _Sick (pale-green skin), _Night (multiply tint used by the day/night system).
// Building states (v3.1): _Burn (0 = normal, ~0.4 burning, 1 = burnt shell), _Frost (blue tint + snow on top edges), _Overgrown (moss/vine speckle).
// Fire, smoke and flood are separate overlay sprites (Buildings/Disaster/building_overlays) placed on the 'roof' anchor / pivot.
// Written as a plain CG unlit pass: renders in URP (SRPDefaultUnlit pass, incl. the 2D Renderer). It is unlit: Light2D does not affect it,
// so night uses _Night (or port to a Sprite-Lit Shader Graph later). Lives under Resources so Shader.Find works in player builds.
Shader "WorldSim/RecolorSprite"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        [PerRendererData] _MaskTex ("Recolour mask (secondary texture)", 2D) = "black" {}
        [PerRendererData] _RampTex ("Palette ramps 5x8", 2D) = "white" {}
        [PerRendererData] _Flash ("Hit flash", Range(0,1)) = 0
        [PerRendererData] _Sick ("Sick", Range(0,1)) = 0
        [PerRendererData] _Burn ("Burnt", Range(0,1)) = 0
        [PerRendererData] _Frost ("Frozen", Range(0,1)) = 0
        [PerRendererData] _Overgrown ("Overgrown", Range(0,1)) = 0
        _Night ("Night tint", Color) = (1,1,1,1)
        _UseRamp ("Use ramp", Float) = 1
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" "PreviewType"="Plane" "CanUseSpriteAtlas"="True" }
        Cull Off ZWrite Off Lighting Off
        Blend SrcAlpha OneMinusSrcAlpha
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex, _MaskTex, _RampTex;
            float _Flash, _Sick, _UseRamp, _Burn, _Frost, _Overgrown;
            float4 _MainTex_TexelSize;
            fixed4 _Night;
            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            v2f vert (appdata v) { v2f o; o.pos = UnityObjectToClipPos(v.vertex); o.uv = v.uv; o.color = v.color; return o; }

            // reproduces lib.lit(): k<0 darkens, k>0 lightens toward white
            float3 litc(float3 c, float k) { return k >= 0 ? c + (1 - c) * k : c * (1 + k); }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);
                fixed4 m = tex2D(_MaskTex, i.uv);
                if (_UseRamp > 0.5 && m.a > 0.5)
                {
                    float region = round(m.r * 255.0 / 36.0);          // 1..6
                    float g = m.g * 255.0;
                    float v = (region - 0.5) / 8.0;
                    if (region <= 4.5)
                    {
                        float idx = clamp(round((g - 40.0) / 44.0), 0, 4);   // greys 40,84,128,172,216 -> 0..4
                        col.rgb = tex2D(_RampTex, float2((idx + 0.5) / 5.0, v)).rgb;
                    }
                    else
                    {
                        float3 baseC = tex2D(_RampTex, float2(2.5 / 5.0, v)).rgb;
                        float k = g < 128.0 ? g / 128.0 - 1.0 : (g - 128.0) / 127.0;
                        col.rgb = litc(baseC, k);
                        if (region < 5.5) col.rgb = lerp(col.rgb, col.rgb * 0.62 + float3(0.60, 0.69, 0.48) * 0.38, _Sick);
                    }
                }
                if (_Burn > 0.001)
                {
                    float l = dot(col.rgb, float3(0.30, 0.59, 0.11));
                    col.rgb = lerp(col.rgb, l * 0.32 + 0.035, _Burn);
                }
                if (_Overgrown > 0.001)
                {
                    float2 px = floor(i.uv * _MainTex_TexelSize.zw);
                    float n = frac(sin(dot(px, float2(12.9898, 78.233))) * 43758.5453);
                    if (n < _Overgrown * 0.35) col.rgb = lerp(col.rgb, n < _Overgrown * 0.17 ? float3(0.31, 0.50, 0.21) : float3(0.42, 0.60, 0.27), 0.85);
                }
                if (_Frost > 0.001)
                {
                    col.rgb = lerp(col.rgb, col.rgb * 0.75 + float3(0.66, 0.80, 0.92) * 0.32, _Frost);
                    // snow on top edges: opaque texel whose neighbour one or two texels above is transparent
                    float up1 = tex2D(_MainTex, i.uv + float2(0, _MainTex_TexelSize.y)).a;
                    float up2 = tex2D(_MainTex, i.uv + float2(0, 2 * _MainTex_TexelSize.y)).a;
                    if (col.a > 0.5 && (up1 < 0.5 || up2 < 0.5)) col.rgb = lerp(col.rgb, float3(0.94, 0.97, 0.99), _Frost);
                }
                col.rgb = lerp(col.rgb, 1, _Flash);
                col *= i.color;
                col.rgb *= _Night.rgb;
                return col;
            }
            ENDCG
        }
    }
}
