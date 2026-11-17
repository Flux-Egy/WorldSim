using System;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace GodSim.EditorTools
{
    /// <summary>
    /// Build profiles (§15.4, §18.1).
    ///   Release: IL2CPP, ARM64, stripping High, non-development.
    ///   Modder:  development build, GODSIM_MODDER + GODSIM_MODLOADER_VERBOSE.
    ///            Its scripting backend depends on open Decision A (see docs/IMPLEMENTATION_PLAN.md).
    ///            Until that is decided it uses IL2CPP ARM64 too, so it runs on 64-bit-only phones.
    ///
    /// Command-line use:
    ///   Unity -batchmode -quit -projectPath . -buildTarget Android \
    ///         -executeMethod GodSim.EditorTools.GodSimBuild.BuildReleaseCI
    /// </summary>
    public static class GodSimBuild
    {
        const string OutputDir = "Builds/Android";

        [MenuItem("GodSim/Build/Android Release (IL2CPP ARM64)")]
        public static void BuildReleaseMenu() => Build(isModder: false);

        [MenuItem("GodSim/Build/Android Modder (development, verbose loader)")]
        public static void BuildModderMenu() => Build(isModder: true);

        public static void BuildReleaseCI() => ExitWith(Build(isModder: false));
        public static void BuildModderCI() => ExitWith(Build(isModder: true));

        static bool Build(bool isModder)
        {
            if (!GodSimProjectSetup.ReportManualSteps())
            {
                Debug.LogError("[GodSim] Build aborted: fix the MANUAL items above.");
                return false;
            }

            string[] scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            if (scenes.Length == 0)
            {
                Debug.LogError("[GodSim] No scenes in Build Settings. Run GodSim > Setup > Create Boot Scene.");
                return false;
            }

            var android = NamedBuildTarget.Android;
            var prevBackend = PlayerSettings.GetScriptingBackend(android);
            var prevArch = PlayerSettings.Android.targetArchitectures;
            var prevStripping = PlayerSettings.GetManagedStrippingLevel(android);

            try
            {
                PlayerSettings.SetScriptingBackend(android, ScriptingImplementation.IL2CPP);
                PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
                PlayerSettings.SetManagedStrippingLevel(android,
                    isModder ? ManagedStrippingLevel.Minimal : ManagedStrippingLevel.High);

                var options = new BuildPlayerOptions
                {
                    scenes = scenes,
                    target = BuildTarget.Android,
                    locationPathName = $"{OutputDir}/GodSim-{(isModder ? "modder" : "release")}.apk",
                    options = isModder ? BuildOptions.Development | BuildOptions.AllowDebugging : BuildOptions.None,
                    extraScriptingDefines = isModder
                        ? new[] { "GODSIM_MODDER", "GODSIM_MODLOADER_VERBOSE" }
                        : Array.Empty<string>(),
                };

                BuildReport report = BuildPipeline.BuildPlayer(options);
                var s = report.summary;
                Debug.Log($"[GodSim] Build {(isModder ? "Modder" : "Release")}: {s.result}, " +
                          $"{s.totalSize / (1024f * 1024f):F1} MB, {s.totalErrors} errors, {s.totalTime}");
                return s.result == BuildResult.Succeeded;
            }
            finally
            {
                PlayerSettings.SetScriptingBackend(android, prevBackend);
                PlayerSettings.Android.targetArchitectures = prevArch;
                PlayerSettings.SetManagedStrippingLevel(android, prevStripping);
            }
        }

        static void ExitWith(bool success)
        {
            if (Application.isBatchMode) EditorApplication.Exit(success ? 0 : 1);
        }
    }
}
