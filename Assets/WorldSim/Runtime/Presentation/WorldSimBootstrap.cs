using WorldSim.Modding;
using WorldSim.ModAPI;
using UnityEngine;

namespace WorldSim.Presentation
{
    /// <summary>
    /// Boot scene entry point (presentation glue only). Stage 1 applies safe frame-pacing
    /// defaults and logs the build profile. Settings persistence (§2.1) replaces the
    /// hard-coded values in Stage 9.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class WorldSimBootstrap : MonoBehaviour
    {
        [SerializeField] int defaultTargetFrameRate = 60;

        void Awake()
        {
            DontDestroyOnLoad(gameObject);

            // On mobile, vSyncCount is ignored and targetFrameRate drives pacing.
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = defaultTargetFrameRate;

            Debug.Log($"[WorldSim] Boot. Unity {Application.unityVersion}, ModAPI {ModApiVersion.String}, " +
                      $"modder build: {ModdingBuildFlags.IsModderBuild}, " +
                      $"display: {Screen.currentResolution.width}x{Screen.currentResolution.height} " +
                      $"@ {Screen.currentResolution.refreshRateRatio.value:F1} Hz");

#if ENABLE_LEGACY_INPUT_MANAGER
            Debug.LogError("[WorldSim] Legacy Input Manager is enabled. Set Player > Active Input Handling " +
                           "to 'Input System Package (New)' (§8.1).");
#endif

            if (GetComponent<WorldViewController>() == null)
                gameObject.AddComponent<WorldViewController>();
        }
    }
}
