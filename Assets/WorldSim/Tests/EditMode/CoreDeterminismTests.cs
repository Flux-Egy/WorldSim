using WorldSim.Core;
using NUnit.Framework;

namespace WorldSim.Tests
{
    /// <summary>
    /// Known-answer tests. Expected values come from the published reference implementations
    /// and were cross-checked with an independent Python implementation.
    /// </summary>
    public class CoreDeterminismTests
    {
        [Test]
        public void SplitMix64_MatchesReferenceVectors()
        {
            var rng = new SplitMix64(0);
            Assert.AreEqual(0xE220A8397B1DCDAFUL, rng.Next());
            Assert.AreEqual(0x6E789E6AA1B965F4UL, rng.Next());
            Assert.AreEqual(0x06C45D188009454FUL, rng.Next());
        }

        [Test]
        public void SplitMix64_NthOutput_EqualsSequentialNext()
        {
            var rng = new SplitMix64(0x123456789ABCDEF0UL);
            for (ulong n = 1; n <= 16; n++)
                Assert.AreEqual(rng.Next(), SplitMix64.NthOutput(0x123456789ABCDEF0UL, n));
        }

        [Test]
        public void Pcg32_MatchesReferenceDemoOutput()
        {
            // pcg32-demo, pcg32_srandom_r(&rng, 42u, 54u)
            var rng = new Pcg32(42, 54);
            uint[] expected = { 0xA15C02B7, 0x7B47F409, 0xBA1D3330, 0x83D2F293, 0xBFA4784B, 0xCBED606E };
            foreach (uint e in expected) Assert.AreEqual(e, rng.NextUInt());
        }

        [Test]
        public void Pcg32_BoundedStaysInRange()
        {
            var rng = new Pcg32(7, 11);
            for (int i = 0; i < 10000; i++)
            {
                int v = rng.NextInt(-5, 6);
                Assert.That(v, Is.InRange(-5, 5));
                float f = rng.NextFloat01();
                Assert.That(f, Is.GreaterThanOrEqualTo(0f).And.LessThan(1f));
            }
        }

        [Test]
        public void WorldSeed_DeriveIsStableAndStreamsDiffer()
        {
            var seed = new WorldSeed(0x123456789ABCDEF0UL);
            Assert.AreEqual(0x161922C645CE50E8UL, seed.Derive(SeedStream.Height));
            Assert.AreNotEqual(seed.Derive(SeedStream.Height), seed.Derive(SeedStream.Moisture));
            Assert.AreNotEqual(seed.Derive(SeedStream.Moisture), seed.Derive(SeedStream.Temperature));
        }

        [Test]
        public void StableHash64_MatchesFnv1aVectors()
        {
            var empty = StableHash64.Create();
            Assert.AreEqual(0xCBF29CE484222325UL, empty.Value);

            var a = StableHash64.Create();
            a.Add((byte)'a');
            Assert.AreEqual(0xAF63DC4C8601EC8CUL, a.Value);

            var foobar = StableHash64.Create();
            foreach (char c in "foobar") foobar.Add((byte)c);
            Assert.AreEqual(0x85944171F73967E8UL, foobar.Value);
        }
    }
}
