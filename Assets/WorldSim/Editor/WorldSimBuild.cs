using System;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace WorldSim.EditorTools
{
    /// <summary>
    /// Build profiles (§15.4, §18.1).
    ///   Release: IL2CPP, ARM64, stripping High, non-development.
    ///   Modder:  development build, WORLDSIM_MODDER + WORLDSIM_MODLOADER_VERBOSE.
    ///            Its scripting backend depends on open Decision A (see docs/IMPLEMENTATION_PLAN.md).
    ///            Until that is decided it uses IL2CPP ARM64 too, so it runs on 64-bit-only phones.
    ///
    /// Command-line use:
    ///   Unity -batchmode -quit -projectPath . -buildTarget Android \
    ///         -executeMethod WorldSim.EditorTools.WorldSimBuild.BuildReleaseCI
    /// </summary>
    public static class WorldSimBuild
    {
        const string OutputDir = "Builds/Android";

        // Fixed TEST signing key, committed on purpose: every CI build used to get a fresh random
        // debug key, so Android refused to install a new build over the previous one
        // (INSTALL_FAILED_UPDATE_INCOMPATIBLE, seen on device 2026-11-18). This key is public and
        // must never sign a store release; store builds will use a key from GitHub secrets.
        const string TestKeystore = "ci/worldsim-test.keystore";
        const string TestKeyAlias = "worldsim-test";
        const string TestKeyPassword = "worldsim-test";

        [MenuItem("WorldSim/Build/Android Release (IL2CPP ARM64)")]
        public static void BuildReleaseMenu() => Build(isModder: false);

        [MenuItem("WorldSim/Build/Android Modder (development, verbose loader)")]
        public static void BuildModderMenu() => Build(isModder: true);

        public static void BuildReleaseCI() => ReportToGameCI(Build(isModder: false));
        public static void BuildModderCI() => ReportToGameCI(Build(isModder: true));

        /// <returns>The build report, or null if the build was refused before starting.</returns>
        static BuildReport Build(bool isModder)
        {
            if (!WorldSimProjectSetup.ReportManualSteps())
            {
                Debug.LogError("[WorldSim] Build aborted: fix the MANUAL items above.");
                return null;
            }

            string[] scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            if (scenes.Length == 0)
            {
                Debug.LogError("[WorldSim] No scenes in Build Settings. Run WorldSim > Setup > Create Boot Scene.");
                return null;
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

                ConfigureTestSigning();

                var options = new BuildPlayerOptions
                {
                    scenes = scenes,
                    target = BuildTarget.Android,
                    locationPathName = $"{OutputDir}/WorldSim-{(isModder ? "modder" : "release")}.apk",
                    options = isModder ? BuildOptions.Development | BuildOptions.AllowDebugging : BuildOptions.None,
                    extraScriptingDefines = isModder
                        ? new[] { "WORLDSIM_MODDER", "WORLDSIM_MODLOADER_VERBOSE" }
                        : Array.Empty<string>(),
                };

                BuildReport report = BuildPipeline.BuildPlayer(options);
                var s = report.summary;
                Debug.Log($"[WorldSim] Build {(isModder ? "Modder" : "Release")}: {s.result}, " +
                          $"{s.totalSize / (1024f * 1024f):F1} MB, {s.totalErrors} errors, {s.totalTime}");
                return report;
            }
            finally
            {
                PlayerSettings.SetScriptingBackend(android, prevBackend);
                PlayerSettings.Android.targetArchitectures = prevArch;
                PlayerSettings.SetManagedStrippingLevel(android, prevStripping);
            }
        }

        static void ConfigureTestSigning()
        {
            string path = System.IO.Path.GetFullPath(TestKeystore);
            if (!System.IO.File.Exists(path))
            {
                Debug.LogWarning("[WorldSim] " + TestKeystore + " not found; Unity will sign with a random debug key.");
                PlayerSettings.Android.useCustomKeystore = false;
                return;
            }
            PlayerSettings.Android.useCustomKeystore = true;
            PlayerSettings.Android.keystoreName = path;
            PlayerSettings.Android.keystorePass = TestKeyPassword;
            PlayerSettings.Android.keyaliasName = TestKeyAlias;
            PlayerSettings.Android.keyaliasPass = TestKeyPassword;
            Debug.Log("[WorldSim] Signing with the committed TEST key (" + TestKeystore + ").");
        }

        static void ReportToGameCI(BuildReport report)
        {
            if (report == null)
            {
                GameCIReporter.ExitWithResult(BuildResult.Failed);
                return;
            }
            GameCIReporter.ReportSummary(report.summary);
            GameCIReporter.ExitWithResult(report.summary.result);
        }
    }
}
