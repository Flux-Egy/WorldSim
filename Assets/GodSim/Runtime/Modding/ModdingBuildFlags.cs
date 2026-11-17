namespace GodSim.Modding
{
    /// <summary>
    /// Compile-time flags set by the build profiles in GodSim.EditorTools.GodSimBuild.
    /// GODSIM_MODDER enables the verbose loader build (§15.4, §18.1).
    /// </summary>
    public static class ModdingBuildFlags
    {
#if GODSIM_MODDER
        public const bool IsModderBuild = true;
#else
        public const bool IsModderBuild = false;
#endif

#if GODSIM_MODLOADER_VERBOSE
        public const bool VerboseLoaderLogging = true;
#else
        public const bool VerboseLoaderLogging = false;
#endif
    }
}
