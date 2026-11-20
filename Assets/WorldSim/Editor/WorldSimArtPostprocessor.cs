using UnityEditor;
using UnityEngine;

namespace WorldSim.EditorTools
{
    /// <summary>
    /// Import settings for the generated art pack (Assets/WorldSim/Resources/WorldSimArt): pixel art pages are
    /// point-filtered, uncompressed, no mipmaps, no resize; recolour masks (*_mask.png) are linear data.
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
            ti.textureType = TextureImporterType.Default;
            ti.textureShape = TextureImporterShape.Texture2D;
            ti.sRGBTexture = !isMask;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = !isMask;
            ti.mipmapEnabled = false;
            ti.filterMode = FilterMode.Point;
            ti.wrapMode = TextureWrapMode.Clamp;
            ti.npotScale = TextureImporterNPOTScale.None;
            ti.isReadable = false;
            ti.maxTextureSize = 4096;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
        }
    }
}
