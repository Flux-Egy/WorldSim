// WorldSim/TerrainAnimated
// Brings the baked terrain chunks and zoom layers to life (Playable Alpha demo). The baker (TerrainComposer, tagAnimated)
// marks animated pixels in the alpha channel; every other pixel is opaque (255):
//   254 water: slow diagonal light streaks and rare pixel glints that move with time;
//   253 lava:  a warm glow pulse travelling across the flow;
//   252 foam:  a 2-pixel shimmer along the shore.
// Effects are computed per texel (floor(uv * texture size)), so they stay crisp pixel art at every zoom; tagged pixels are
// output fully opaque. The layer cross-fade uses the vertex colour alpha (SpriteRenderer.color). Plain CG unlit pass:
// renders in URP's 2D Renderer like WorldSim/RecolorSprite. Lives under Resources so Shader.Find works in player builds.
Shader "WorldSim/TerrainAnimated"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        _Speed ("Animation speed", Float) = 1
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
            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            float _Speed;
            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            v2f vert (appdata v) { v2f o; o.pos = UnityObjectToClipPos(v.vertex); o.uv = v.uv; o.color = v.color; return o; }

            float hash21(float2 p) { return frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453); }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);
                float tag = round(col.a * 255.0);
                float t = _Time.y * _Speed;
                float2 p = floor(i.uv * _MainTex_TexelSize.zw);
                if (tag > 253.5 && tag < 254.5)
                {
                    // water: long, slow light streaks (pixel-stepped) + rare glints that blink in place
                    float s = sin(p.x * 0.17 + p.y * 0.31 - t * 1.3) * sin(p.y * 0.07 - p.x * 0.03 + t * 0.6);
                    col.rgb += s > 0.80 ? 0.06 : (s < -0.85 ? -0.03 : 0.0);
                    float g = hash21(p + floor(t * 2.0 + hash21(floor(p / 8.0)) * 8.0));
                    col.rgb = g > 0.9975 ? lerp(col.rgb, float3(0.92, 0.97, 1.0), 0.65) : col.rgb;
                    col.a = 1.0;
                }
                else if (tag > 252.5 && tag < 253.5)
                {
                    // lava: a slow glow wave plus flickering hot spots
                    float w = 0.5 + 0.5 * sin(p.x * 0.11 + p.y * 0.07 - t * 1.7);
                    float hot = hash21(floor(p / 2.0) + floor(t * 3.0));
                    col.rgb *= 0.82 + 0.32 * w;
                    col.rgb = hot > 0.985 ? lerp(col.rgb, float3(1.0, 0.86, 0.35), 0.7) : col.rgb;
                    col.a = 1.0;
                }
                else if (tag > 251.5 && tag < 252.5)
                {
                    // foam: pairs of pixels brighten and dim along the shore
                    float f = hash21(floor(p / 2.0) + floor(t * 2.5));
                    col.rgb = lerp(col.rgb, float3(0.97, 0.99, 1.0), f > 0.55 ? 0.35 : 0.0);
                    col.a = 1.0;
                }
                col *= i.color;
                return col;
            }
            ENDCG
        }
    }
}
