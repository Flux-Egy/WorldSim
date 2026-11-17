using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GodSim.EditorTools
{
    /// <summary>
    /// Headless project bootstrap for CI (no human ever opens the Editor in this project's
    /// current workflow). Idempotent: it only fixes what is missing or wrong, so it is safe to
    /// run before every build. Changing Active Input Handling only takes effect after an
    /// Editor restart, so CI runs this in its own Unity invocation, before the build.
    ///
    ///   -executeMethod GodSim.EditorTools.GodSimCI.Bootstrap
    ///
    /// UNVERIFIED (confirm on the first successful CI run):
    ///   - the serialized property name "activeInputHandler" (1 = Input System Package).
    ///     The method fails loudly if the property is not found.
    /// Verified against URP 17.3.0 source (Unity-Technologies/Graphics, 6000.3/staging):
    ///   - the Renderer2DData creation steps (see EnsureUrpAsset).
    /// </summary>
    public static class GodSimCI
    {
        public const string SettingsFolder = "Assets/GodSim/Settings";
        const string UrpPackagePath = "Packages/com.unity.render-pipelines.universal";
        const int InputSystemPackageOnly = 1;

        public static void Bootstrap()
        {
            bool ok = true;
            try
            {
                ok &= EnsureActiveInputHandler();
                ok &= EnsureUrpAsset();
                GodSimProjectSetup.ApplyAndroidSettingsCore();

                if (!File.Exists(GodSimProjectSetup.BootScenePath))
                    GodSimProjectSetup.CreateBootSceneFile();
                else
                    Debug.Log("[GodSim CI] Boot scene present.");

                AssetDatabase.SaveAssets();
            }
            catch (System.Exception e)
            {
                Debug.LogException(e);
                ok = false;
            }

            Debug.Log(ok ? "[GodSim CI] Bootstrap OK." : "[GodSim CI] Bootstrap FAILED. See errors above.");
            if (Application.isBatchMode) EditorApplication.Exit(ok ? 0 : 1);
        }

        static bool EnsureActiveInputHandler()
        {
            Object[] objs = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset");
            if (objs == null || objs.Length == 0)
            {
                Debug.LogError("[GodSim CI] Could not load ProjectSettings/ProjectSettings.asset.");
                return false;
            }

            var so = new SerializedObject(objs[0]);
            SerializedProperty prop = so.FindProperty("activeInputHandler");
            if (prop == null)
            {
                Debug.LogError("[GodSim CI] Property 'activeInputHandler' not found. Set Active Input Handling " +
                               "manually and commit ProjectSettings/ProjectSettings.asset.");
                return false;
            }

            if (prop.intValue != InputSystemPackageOnly)
            {
                Debug.Log($"[GodSim CI] activeInputHandler {prop.intValue} -> {InputSystemPackageOnly} " +
                          "(takes effect on next Editor start).");
                prop.intValue = InputSystemPackageOnly;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
            return true;
        }

        static bool EnsureUrpAsset()
        {
            if (GraphicsSettings.defaultRenderPipeline is UniversalRenderPipelineAsset)
            {
                Debug.Log("[GodSim CI] URP asset already assigned.");
                return true;
            }

            // Mirrors URP 17.3's own "Create > Rendering > URP Asset (with 2D Renderer)" path
            // (Editor/2D/Renderer2DMenus.cs: CreateRendererData + CreateRendererAsset):
            //   1. CreateInstance<Renderer2DData>()
            //   2. postProcessData = PostProcessData.GetDefaultPostProcessData(). Both members are
            //      internal, so the serialized field m_PostProcessData is set to the same asset.
            //   3. AssetDatabase.CreateAsset, then ResourceReloader.ReloadAllNullIn(data, packagePath),
            //      which fills the default shaders and materials (otherwise sprites render magenta).
            Directory.CreateDirectory(SettingsFolder);
            var rendererData = ScriptableObject.CreateInstance<Renderer2DData>();
            AssetDatabase.CreateAsset(rendererData, SettingsFolder + "/GodSim2DRenderer.asset");

            var postProcess = AssetDatabase.LoadAssetAtPath<PostProcessData>(UrpPackagePath + "/Runtime/Data/PostProcessData.asset");
            if (postProcess == null)
            {
                Debug.LogError("[GodSim CI] Default PostProcessData.asset not found in the URP package.");
                return false;
            }
            var so = new SerializedObject(rendererData);
            SerializedProperty ppProp = so.FindProperty("m_PostProcessData");
            if (ppProp == null)
            {
                Debug.LogError("[GodSim CI] Renderer2DData.m_PostProcessData not found (URP version changed?).");
                return false;
            }
            ppProp.objectReferenceValue = postProcess;
            so.ApplyModifiedPropertiesWithoutUndo();

            ResourceReloader.ReloadAllNullIn(rendererData, UrpPackagePath);
            EditorUtility.SetDirty(rendererData);

            UniversalRenderPipelineAsset urp = UniversalRenderPipelineAsset.Create(rendererData);
            AssetDatabase.CreateAsset(urp, SettingsFolder + "/GodSimURP.asset");

            GraphicsSettings.defaultRenderPipeline = urp;
            int current = QualitySettings.GetQualityLevel();
            for (int i = 0; i < QualitySettings.names.Length; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = urp;
            }
            QualitySettings.SetQualityLevel(current, false);

            AssetDatabase.SaveAssets();
            Debug.Log("[GodSim CI] Created and assigned " + SettingsFolder + "/GodSimURP.asset (2D Renderer).");
            return true;
        }
    }
}
