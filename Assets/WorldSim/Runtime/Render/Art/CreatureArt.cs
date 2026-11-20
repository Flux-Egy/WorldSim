using WorldSim.Core.Life;

namespace WorldSim.Render.Art
{
    /// <summary>What a creature is visibly doing (the renderer maps simulation actions to these).</summary>
    public enum CreaturePose : byte { Idle = 0, Walk = 1, Run = 2, Eat = 3, Sleep = 4, Attack = 5, Hurt = 6, Dead = 7 }

    /// <summary>The era a people's clothing comes from (people_actions: tribal, medieval, modern).</summary>
    public enum Era : byte { Tribal = 0, Medieval = 1, Modern = 2 }

    /// <summary>
    /// Maps simulation species to art-pack creatures (WorldSimData/creatures.json keys) and resolves the art for a pose.
    /// People: <c>h_&lt;race&gt;_&lt;m|f&gt;_&lt;era|child&gt;_&lt;action&gt;</c> (Characters/People/people_actions, recolourable).
    /// Animals: anims <c>&lt;key&gt;_&lt;adult|young&gt;_&lt;pose&gt;</c>, single frames <c>&lt;prefix&gt;&lt;key&gt;_&lt;age&gt;_&lt;pose&gt;</c>
    /// (Characters/Fauna). Every combination is checked against the art index by <c>CreatureArtTests</c>.
    /// </summary>
    public static class CreatureArt
    {
        /// <summary>The creatures.json key for a built-in species, or null for unknown (mod) species.</summary>
        public static string PackKey(SpeciesId s)
        {
            switch (s)
            {
                case SpeciesId.Human: return "human";
                case SpeciesId.Elf: return "elf";
                case SpeciesId.Orc: return "orc";
                case SpeciesId.Dwarf: return "dwarf";
                case SpeciesId.Rabbit: return "rabbit";
                case SpeciesId.Sheep: return "sheep";
                case SpeciesId.Deer: return "deer";
                case SpeciesId.Cow: return "cow";
                case SpeciesId.Wolf: return "wolf";
                case SpeciesId.Bear: return "bear";
                case SpeciesId.Fox: return "fox";
                case SpeciesId.Bird: return "crow";    // the generic bird of the simulation
                case SpeciesId.Fish: return "carp";    // the generic fish (rivers, lakes, coasts)
                default: return null;
            }
        }

        public static bool IsPerson(SpeciesId s) => s == SpeciesId.Human || s == SpeciesId.Elf || s == SpeciesId.Orc || s == SpeciesId.Dwarf;

        static string Prefix(SpeciesId s) => s == SpeciesId.Bird ? "c_" : s == SpeciesId.Fish ? "s_" : "a_";

        static readonly string[] Eras = { "tribal", "medieval", "modern" };

        /// <summary>
        /// The art for a pose: a looping/one-shot animation name (<paramref name="isAnimation"/> true) or a single frame.
        /// Null for unknown species. <paramref name="airborne"/> picks the flight animation for birds.
        /// </summary>
        public static string Resolve(SpeciesId s, CreaturePose pose, bool young, bool male, Era era, bool airborne, out bool isAnimation)
        {
            isAnimation = true;
            string key = PackKey(s);
            if (key == null) return null;
            if (IsPerson(s))
            {
                string stem = "h_" + key + (male ? "_m_" : "_f_") + (young ? "child" : Eras[(int)era <= 2 ? (int)era : 1]) + "_";
                return stem + PersonAction(pose, young);
            }

            string age = young ? "_young_" : "_adult_";
            if (pose == CreaturePose.Hurt || pose == CreaturePose.Dead)
            {
                isAnimation = false;
                return Prefix(s) + key + age + (pose == CreaturePose.Hurt ? "hurt" : "dead");
            }
            if (s == SpeciesId.Fish)
                return key + age + (pose == CreaturePose.Attack ? "attack" : pose == CreaturePose.Idle || pose == CreaturePose.Sleep || pose == CreaturePose.Eat ? "idle" : "swim");
            if (s == SpeciesId.Bird)
            {
                if (airborne && pose != CreaturePose.Sleep) return key + age + "fly";
                if (pose == CreaturePose.Sleep || pose == CreaturePose.Attack) return key + age + (pose == CreaturePose.Sleep ? "sleep" : "attack");
                return key + age + (pose == CreaturePose.Walk || pose == CreaturePose.Run ? "walk" : "idle");
            }
            return key + age + AnimalPose(pose);
        }

        static string AnimalPose(CreaturePose p)
        {
            switch (p)
            {
                case CreaturePose.Walk: return "walk";
                case CreaturePose.Run: return "run";
                case CreaturePose.Eat: return "eat";
                case CreaturePose.Sleep: return "sleep";
                case CreaturePose.Attack: return "attack";
                default: return "idle";
            }
        }

        static string PersonAction(CreaturePose p, bool child)
        {
            switch (p)
            {
                case CreaturePose.Walk: return "walk";
                case CreaturePose.Run: return "run";
                case CreaturePose.Eat: return "eat";
                case CreaturePose.Sleep: return "sleep";
                case CreaturePose.Attack: return child ? "cower" : "melee";
                case CreaturePose.Hurt: return "hurt";
                case CreaturePose.Dead: return child ? "death_fade" : "death_weapon";
                default: return "idle";
            }
        }
    }
}
