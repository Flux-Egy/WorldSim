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
