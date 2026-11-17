namespace GodSim.ModAPI
{
    /// <summary>
    /// Version of the public modding surface. Mods declare the API version they were built
    /// against in mod.json, and the loader warns on a major mismatch (§14.2).
    /// Registries and event hooks (§9.3) arrive in Stage 8. This assembly stays free of
    /// Unity.Entities so mods never depend on simulation internals.
    /// </summary>
    public static class ModApiVersion
    {
        public const int Major = 0;
        public const int Minor = 1;
        public const string String = "0.1";
    }
}
