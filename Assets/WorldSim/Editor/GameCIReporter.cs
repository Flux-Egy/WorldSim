using System;
using UnityEditor;
using UnityEditor.Build.Reporting;

namespace WorldSim.EditorTools
{
    /// <summary>
    /// Speaks the stdout contract game-ci's CLI checks after Unity exits
    /// (game-ci/cli v0.1.76, src/model/unity/build-validation/unity-build-validation.ts):
    /// a run passes only if stdout contains "Build succeeded!" or a "# Build results #" block
    /// with "Errors: 0" followed by "Size:". The text and exit codes copy game-ci's own default
    /// build script (dist/default-build-script/.../Reporting/StdOutReporter.cs), so custom
    /// buildMethods are validated exactly like game-ci's built-in one.
    /// </summary>
    public static class GameCIReporter
    {
        static readonly string EOL = Environment.NewLine;

        public static void ReportSummary(BuildSummary summary)
        {
            Console.WriteLine(
                $"{EOL}" +
                $"###########################{EOL}" +
                $"#      Build results      #{EOL}" +
                $"###########################{EOL}" +
                $"{EOL}" +
                $"Duration: {summary.totalTime}{EOL}" +
                $"Warnings: {summary.totalWarnings}{EOL}" +
                $"Errors: {summary.totalErrors}{EOL}" +
                $"Size: {summary.totalSize} bytes{EOL}" +
                $"{EOL}");
        }

        /// <summary>Prints the result line and exits Unity (batch mode only) with game-ci's codes.</summary>
        public static void ExitWithResult(BuildResult result)
        {
            int code;
            switch (result)
            {
                case BuildResult.Succeeded: Console.WriteLine("Build succeeded!"); code = 0; break;
                case BuildResult.Failed: Console.WriteLine("Build failed!"); code = 101; break;
                case BuildResult.Cancelled: Console.WriteLine("Build cancelled!"); code = 102; break;
                default: Console.WriteLine("Build result is unknown!"); code = 103; break;
            }
            if (UnityEngine.Application.isBatchMode) EditorApplication.Exit(code);
        }

        /// <summary>For non-build steps (CI bootstrap): success or failure with no player output.</summary>
        public static void ExitWithSuccess(bool success)
        {
            ExitWithResult(success ? BuildResult.Succeeded : BuildResult.Failed);
        }
    }
}
