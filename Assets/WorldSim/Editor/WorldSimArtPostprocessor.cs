using UnityEditor;
using UnityEngine;

namespace WorldSim.EditorTools
{
    /// <summary>
    /// Import settings for the generated art pack (Assets/WorldSim/Resources/WorldSimArt): pixel art pages are
    /// point-filtered, uncompressed, no mipmaps, no resize; recolour masks (*_mask.png) are one-byte linear data (R8),
    /// and their lookup table (mask_lut.png) is linear RGBA.
    /// Sprites are built at runtime by WorldSimArtDB (Sprite.Create), so the pages import as plain textures.
    /// </summary>
    public sealed class WorldSimArtPostprocessor : AssetPostprocessor
    {
        const string Folder = "/Resources/WorldSimArt/";

        /// <summary>Atlas folders compressed with ASTC on Android: terrain (except the LOD atlas with its 16 px markers),
        /// nature, buildings (including their disaster/collapse states) and effects.</summary>
        public static bool UsesAstc(string path)
        {
            int i = path.IndexOf(Folder, System.StringComparison.Ordinal);
            if (i < 0) return false;
            string rel = path.Substring(i + Folder.Length);
            if (rel.StartsWith("Terrain/lod", System.StringComparison.Ordinal)) return false;
            return rel.StartsWith("Terrain/", System.StringComparison.Ordinal) || rel.StartsWith("Nature/", System.StringComparison.Ordinal)
                || rel.StartsWith("Buildings/", System.StringComparison.Ordinal) || rel.StartsWith("FX/", System.StringComparison.Ordinal);
        }

        void OnPreprocessTexture()
        {
            string path = assetPath.Replace('\\', '/');
            if (!path.Contains(Folder)) return;
            var ti = (TextureImporter)assetImporter;
            bool isMask = path.EndsWith("_mask.png");
            bool isLut = path.EndsWith("/mask_lut.png");
            ti.textureType = TextureImporterType.Default;
            ti.textureShape = TextureImporterShape.Texture2D;
            ti.sRGBTexture = !isMask && !isLut;          // masks and their lookup table are data, not colour
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = !isMask && !isLut;
            ti.mipmapEnabled = false;
            ti.filterMode = FilterMode.Point;
            ti.wrapMode = TextureWrapMode.Clamp;
            ti.npotScale = TextureImporterNPOTScale.None;
            ti.isReadable = false;
            ti.maxTextureSize = 4096;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            if (!isMask && !isLut && UsesAstc(path))
            {
                // Owner decision (2026-11-20, after the Art Lab A/B test: 90.3% of pixels identical, 0.03% visibly
                // different, texture memory -54%): ASTC 4x4 on Android for large, low-contrast art only. UI, icons,
                // portraits, the font, people, animals, units and the far-zoom markers stay uncompressed, because
                // ASTC visibly shifts colours on small high-contrast sprites. Masks and their LUT are data: never.
                ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
                {
                    name = "Android", overridden = true, maxTextureSize = 4096,
                    format = TextureImporterFormat.ASTC_4x4, textureCompression = TextureImporterCompression.CompressedHQ,
                    compressionQuality = 100,
                });
            }
            if (isMask)
            {
                // One byte per pixel: the mask is an 8-bit grey PNG of codes (Tools/ArtIndex/encode_masks.py).
                ti.textureType = TextureImporterType.SingleChannel;
                var settings = new TextureImporterSettings();
                ti.ReadTextureSettings(settings);
                settings.singleChannelComponent = TextureImporterSingleChannelComponent.Red;
                ti.SetTextureSettings(settings);
                foreach (var platform in new[] { "Standalone", "Android" })
                    ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
                    {
                        name = platform, overridden = true, maxTextureSize = 4096,
                        format = TextureImporterFormat.R8, textureCompression = TextureImporterCompression.Uncompressed,
                    });
            }
        }
    }
}
