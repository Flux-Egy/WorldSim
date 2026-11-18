using WorldSim.Presentation;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem.UI;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace WorldSim.EditorTools
{
    /// <summary>
    /// One-click project configuration for Stage 1. Everything set here is also asserted by
    /// <see cref="WorldSimBuild"/> before a build, so drift is caught at build time.
    /// </summary>
    public static class WorldSimProjectSetup
    {
        public const string ScenesFolder = "Assets/WorldSim/Scenes";
        public const string BootScenePath = ScenesFolder + "/Boot.unity";

        public const string CompanyName = "Flux-Egy";
        public const string ProductName = "WorldSim";
        public const string ApplicationId = "com.fluxegy.worldsim";

        [MenuItem("WorldSim/Setup/Apply Android Project Settings")]
        public static void ApplyAndroidSettings()
        {
            ApplyAndroidSettingsCore();
            ReportManualSteps();
        }

        /// <summary>Applies settings without the manual-step report (CI bootstrap reports separately).</summary>
        public static void ApplyAndroidSettingsCore()
        {
            var android = NamedBuildTarget.Android;

            PlayerSettings.SetScriptingBackend(android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.SetManagedStrippingLevel(android, ManagedStrippingLevel.High);
            PlayerSettings.SetApiCompatibilityLevel(android, ApiCompatibilityLevel.NET_Standard);
            PlayerSettings.SetIl2CppCompilerConfiguration(android, Il2CppCompilerConfiguration.Release);
            PlayerSettings.Android.optimizedFramePacing = true;

            // App identity. The application id is permanent once a build is distributed:
            // Android treats a different id as a different app, so updates would not install.
            PlayerSettings.companyName = CompanyName;
            PlayerSettings.productName = ProductName;
            PlayerSettings.SetApplicationIdentifier(android, ApplicationId);

            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android,
                new[] { GraphicsDeviceType.Vulkan, GraphicsDeviceType.OpenGLES3 });

            if (GraphicsSettings.defaultRenderPipeline is UniversalRenderPipelineAsset urp)
            {
                urp.useSRPBatcher = true;
                EditorUtility.SetDirty(urp);
            }
            else
            {
                Debug.LogWarning("[WorldSim] No URP asset assigned. Create one via Assets > Create > Rendering > " +
                                 "URP Asset (with 2D Renderer) and assign it in Project Settings > Graphics.");
            }

            AssetDatabase.SaveAssets();
            Debug.Log($"[WorldSim] Android settings applied: {ApplicationId} \"{ProductName}\", IL2CPP, ARM64, stripping High, Vulkan+GLES3, SRP Batcher.");
        }

        [MenuItem("WorldSim/Setup/Create Boot Scene")]
        public static void CreateBootScene()
        {
            if (System.IO.File.Exists(BootScenePath) &&
                !EditorUtility.DisplayDialog("WorldSim", "Boot.unity exists. Overwrite?", "Overwrite", "Cancel"))
                return;
            CreateBootSceneFile();
        }

        /// <summary>Non-interactive version, used by CI bootstrap. Overwrites without asking.</summary>
        public static void CreateBootSceneFile()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var camGo = new GameObject("WorldCamera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 10f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.08f, 0.1f, 0.14f);
            camGo.transform.position = new Vector3(0f, 0f, -10f);
            var ppc = camGo.AddComponent<PixelPerfectCamera>();
            ppc.assetsPPU = 16;

            var boot = new GameObject("WorldSimBootstrap");
            boot.AddComponent<WorldSimBootstrap>();

            var es = new GameObject("EventSystem");
            es.AddComponent<EventSystem>();
            es.AddComponent<InputSystemUIInputModule>();

            System.IO.Directory.CreateDirectory(ScenesFolder);
            EditorSceneManager.SaveScene(scene, BootScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(BootScenePath, true) };
            Debug.Log("[WorldSim] Created " + BootScenePath + " and set it as the only build scene.");
        }

        /// <summary>Settings without a stable public scripting API. Reported, never guessed.</summary>
        public static bool ReportManualSteps()
        {
            bool ok = true;
#if ENABLE_LEGACY_INPUT_MANAGER
            Debug.LogError("[WorldSim] MANUAL: Project Settings > Player > Other Settings > Active Input Handling " +
                           "= 'Input System Package (New)'. Legacy input must be off for mobile builds (§8.1).");
            ok = false;
#endif
            if (!(GraphicsSettings.defaultRenderPipeline is UniversalRenderPipelineAsset))
            {
                Debug.LogError("[WorldSim] MANUAL: assign a URP asset that uses the 2D Renderer in Project Settings > Graphics.");
                ok = false;
            }
            return ok;
        }
    }
}
