using Unity.Profiling;
using UnityEngine;
using WorldSim.Presentation.Terrain;

namespace WorldSim.Presentation
{
    /// <summary>
    /// Developer counters for the HUD and logcat (Playable Alpha step 2): frames per second, process memory (RSS read
    /// from /proc on Android/Linux, Unity's reserved memory elsewhere), draw calls and batches (ProfilerRecorder; shown
    /// as "n/a" where the player doesn't provide them), and terrain chunks. Logs one "[WorldSim] Stats" line every 5 s.
    /// </summary>
    public sealed class DevStats
    {
        ProfilerRecorder _drawCalls, _batches;
        bool _started;
        int _frames;
        float _windowStart, _nextLog;
        public float Fps { get; private set; }
        public string Line { get; private set; } = "";

        public void Tick(float time, float dt, PackTerrainView terrain)
        {
            if (!_started)
            {
                _started = true;
                _drawCalls = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count");
                _batches = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count");
                _windowStart = time;
                _nextLog = time + 5f;
            }
            _frames++;
            if (time - _windowStart < 0.5f) return;
            Fps = _frames / (time - _windowStart);
            _frames = 0;
            _windowStart = time;

            long rssMb = ProcessRssMb();
            string draws = _drawCalls.Valid && _drawCalls.LastValue > 0 ? _drawCalls.LastValue.ToString() : "n/a";
            string batches = _batches.Valid && _batches.LastValue > 0 ? _batches.LastValue.ToString() : "n/a";
            int chunks = terrain != null ? terrain.NearChunksLoaded : 0;
            float ppt = terrain != null ? terrain.PixelsPerTile : 0f;
            Line = $"fps {Fps:0}   mem {rssMb} MB   draws {draws}   batches {batches}   chunks {chunks}   zoom {ppt:0.0}px/tile";
            if (time >= _nextLog)
            {
                _nextLog = time + 5f;
                Debug.Log("[WorldSim] Stats " + Line);
            }
        }

        static long ProcessRssMb()
        {
            try
            {
                foreach (string l in System.IO.File.ReadAllLines("/proc/self/status"))
                    if (l.StartsWith("VmRSS:"))
                    {
                        var parts = l.Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries);
                        return long.Parse(parts[1]) / 1024;
                    }
            }
            catch (System.Exception) { }
            return UnityEngine.Profiling.Profiler.GetTotalReservedMemoryLong() / (1024 * 1024);
        }
    }
}
