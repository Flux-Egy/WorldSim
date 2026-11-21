using System.Collections.Generic;

namespace WorldSim.Core.Civ
{
    /// <summary>
    /// Deterministic eight-direction A* on the tile grid, allocated once and reused. Ties are
    /// broken by tile index so the same map always produces the same path. No Unity types: this
    /// runs in the managed civilization director and in plain .NET tests.
    /// </summary>
    public sealed class AStarGrid
    {
        public const int DirCount = 8;
        static readonly int[] Dx = { 1, -1, 0, 0, 1, 1, -1, -1 };
        static readonly int[] Dy = { 0, 0, 1, -1, 1, -1, 1, -1 };

        readonly int _w, _h;
        readonly int[] _gScore;      // cost from start
        readonly int[] _cameFrom;
        readonly int[] _stamp;       // visit marker per search
        readonly int[] _closed;      // closed marker per search
        readonly int[] _heapTile;    // binary heap of tile indices
        readonly int[] _heapF;       // f score per heap slot
        int _heapCount;
        int _search;

        public AStarGrid(int width, int height)
        {
            _w = width;
            _h = height;
            int n = width * height;
            _gScore = new int[n];
            _cameFrom = new int[n];
            _stamp = new int[n];
            _closed = new int[n];
            _heapTile = new int[n];
            _heapF = new int[n];
        }

        public int Width => _w;
        public int Height => _h;

        /// <summary>
        /// Finds a path over tiles where <paramref name="blocked"/>[tile] == 0. Writes tile
        /// indices from the first step (excluding the start) through the goal into
        /// <paramref name="path"/>; returns false if unreachable or beyond the expansion cap.
        /// </summary>
        public bool Find(byte[] blocked, int startX, int startY, int goalX, int goalY, List<int> path, int maxExpanded = 60000)
        {
            path.Clear();
            if (!InBounds(startX, startY) || !InBounds(goalX, goalY)) return false;
            int start = startY * _w + startX, goal = goalY * _w + goalX;
            if (blocked[start] != 0 || blocked[goal] != 0) return false;
            if (start == goal) return true;

            _search++;
            _heapCount = 0;
            SetG(start, 0);
            Push(start, Heuristic(startX, startY, goalX, goalY));

            int expanded = 0;
            while (_heapCount > 0 && expanded < maxExpanded)
            {
                int current = Pop();
                if (_closed[current] == _search) continue;
                _closed[current] = _search;
                if (current == goal) return Build(path, start, goal);
                expanded++;

                int cx = current % _w, cy = current / _w;
                for (int d = 0; d < DirCount; d++)
                {
                    int nx = cx + Dx[d], ny = cy + Dy[d];
                    if (nx < 0 || ny < 0 || nx >= _w || ny >= _h) continue;
                    int ni = ny * _w + nx;
                    if (blocked[ni] != 0 || _closed[ni] == _search) continue;
                    // No corner cutting: diagonal steps need both orthogonal neighbours open.
                    if (d >= 4 && (blocked[cy * _w + nx] != 0 || blocked[ny * _w + cx] != 0)) continue;
                    int step = d >= 4 ? 14 : 10;
                    int ng = _gScore[current] + step;
                    if (_stamp[ni] != _search || ng < _gScore[ni])
                    {
                        SetG(ni, ng);
                        _cameFrom[ni] = current;
                        Push(ni, ng + Heuristic(nx, ny, goalX, goalY));
                    }
                }
            }
            return false;
        }

        bool InBounds(int x, int y) => x >= 0 && y >= 0 && x < _w && y < _h;

        int Heuristic(int x, int y, int gx, int gy)
        {
            int dx = x > gx ? x - gx : gx - x;
            int dy = y > gy ? y - gy : gy - y;
            // Octile distance, same scale as the step costs above.
            return dx > dy ? 14 * dy + 10 * (dx - dy) : 14 * dx + 10 * (dy - dx);
        }

        void SetG(int i, int g)
        {
            if (_stamp[i] != _search) _stamp[i] = _search;
            _gScore[i] = g;
        }

        bool Build(List<int> path, int start, int goal)
        {
            var scratch = new List<int>();
            int at = goal;
            while (at != start)
            {
                scratch.Add(at);
                at = _cameFrom[at];
                if (scratch.Count > _w * _h) return false;
            }
            for (int i = scratch.Count - 1; i >= 0; i--) path.Add(scratch[i]);
            return true;
        }

        // ---- binary heap keyed by f, tie-broken by tile index (deterministic) ----

        void Push(int tile, int f)
        {
            int i = _heapCount++;
            _heapTile[i] = tile;
            _heapF[i] = f;
            while (i > 0)
            {
                int parent = (i - 1) >> 1;
                if (Less(parent, i)) break;
                Swap(parent, i);
                i = parent;
            }
        }

        bool Less(int a, int b)
        {
            if (_heapF[a] != _heapF[b]) return _heapF[a] < _heapF[b];
            return _heapTile[a] < _heapTile[b];
        }

        void Swap(int a, int b)
        {
            int t = _heapTile[a]; _heapTile[a] = _heapTile[b]; _heapTile[b] = t;
            int f = _heapF[a]; _heapF[a] = _heapF[b]; _heapF[b] = f;
        }

        int Pop()
        {
            int top = _heapTile[0];
            _heapCount--;
            if (_heapCount > 0)
            {
                _heapTile[0] = _heapTile[_heapCount];
                _heapF[0] = _heapF[_heapCount];
                int i = 0;
                while (true)
                {
                    int l = i * 2 + 1, r = l + 1, best = i;
                    if (l < _heapCount && Less(l, best)) best = l;
                    if (r < _heapCount && Less(r, best)) best = r;
                    if (best == i) break;
                    Swap(i, best);
                    i = best;
                }
            }
            return top;
        }
    }
}
