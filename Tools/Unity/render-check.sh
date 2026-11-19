#!/usr/bin/env bash
# Codespace only. Proves the headless Editor can REALLY render (Xvfb virtual display + software
# OpenGL), independent of Unity MCP. Creates a throwaway project under /tmp, renders a lit
# cube with a camera into a texture, writes $STATE/render-check.png and checks its pixels:
# the corner must be the clear colour and the centre must be the cube, not blank or black.
#
# Needs an active license (run Tools/Unity/up.sh first, or it activates via up.sh's state).
# Uses its own project, so it can run while the WorldSim Editor is up.
set -euo pipefail
STATE=/workspaces/.unity-state
PROJ=/tmp/worldsim-render-check
OUT="$STATE/render-check.png"
mkdir -p "$STATE"
[ -f "$STATE/activated-via" ] || { echo "No active Unity license. Run Tools/Unity/up.sh first."; exit 1; }
"$(dirname "$0")/install-editor.sh" >/dev/null

rm -rf "$PROJ" "$OUT"
echo "== Creating a throwaway project"
/opt/unity/Editor/Unity -batchmode -nographics -quit -createProject "$PROJ" -logFile "$STATE/render-check-create.log" \
  || { echo "Could not create the test project. Log: $STATE/render-check-create.log"; exit 1; }
mkdir -p "$PROJ/Assets/Editor"
cat > "$PROJ/Assets/Editor/RenderCheck.cs" <<'EOF'
using System.IO;
using UnityEditor;
using UnityEngine;

public static class RenderCheck
{
    public static void Run()
    {
        string path = System.Environment.GetEnvironmentVariable("RENDER_CHECK_OUT");
        var bg = new Color32(40, 90, 200, 255);
        var cam = new GameObject("cam").AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = bg;
        cam.transform.position = new Vector3(0, 0, -3);
        var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube.transform.rotation = Quaternion.Euler(30, 45, 0);
        var light = new GameObject("light").AddComponent<Light>();
        light.type = LightType.Directional;
        light.transform.rotation = Quaternion.Euler(50, -30, 0);

        var rt = new RenderTexture(256, 256, 24);
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        var tex = new Texture2D(256, 256, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, 256, 256), 0, 0);
        tex.Apply();
        File.WriteAllBytes(path, tex.EncodeToPNG());

        Color32 corner = tex.GetPixel(4, 4), centre = tex.GetPixel(128, 128);
        bool cornerIsBg = Mathf.Abs(corner.r - bg.r) < 12 && Mathf.Abs(corner.g - bg.g) < 12 && Mathf.Abs(corner.b - bg.b) < 12;
        bool centreIsCube = Mathf.Abs(centre.r - bg.r) + Mathf.Abs(centre.g - bg.g) + Mathf.Abs(centre.b - bg.b) > 40;
        bool ok = SystemInfo.graphicsDeviceType != UnityEngine.Rendering.GraphicsDeviceType.Null && cornerIsBg && centreIsCube;
        Debug.Log($"RENDER_CHECK {(ok ? "PASS" : "FAIL")} device={SystemInfo.graphicsDeviceType} renderer=\"{SystemInfo.graphicsDeviceName}\" corner={corner} centre={centre}");
        EditorApplication.Exit(ok ? 0 : 2);
    }
}
EOF

echo "== Render check: rendering through Xvfb + software OpenGL (2-5 min)"
set +e
RENDER_CHECK_OUT="$OUT" xvfb-run -a -s "-screen 0 1280x720x24" /opt/unity/Editor/Unity \
  -batchmode -force-glcore -projectPath "$PROJ" -executeMethod RenderCheck.Run \
  -logFile "$STATE/render-check.log"
code=$?
set -e
grep -E "RENDER_CHECK|Renderer:|GfxDevice|OpenGL" "$STATE/render-check.log" | head -8
if [ $code -eq 0 ] && [ -s "$OUT" ]; then
  echo "PASS: real rendering works. Image: $OUT"
else
  echo "FAIL (exit $code): no usable rendering. Log: $STATE/render-check.log"
  exit 1
fi
