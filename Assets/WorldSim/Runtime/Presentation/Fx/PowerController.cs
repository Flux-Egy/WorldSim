using Unity.Entities;
using Unity.Mathematics;
using UnityEngine;
using WorldSim.Core;
using WorldSim.Core.Life;
using WorldSim.Core.Powers;
using WorldSim.Presentation.Terrain;
using WorldSim.Simulation;
using WorldSim.Simulation.Life;

namespace WorldSim.Presentation.Fx
{
    /// <summary>
    /// Uses a power where the player taps (Playable Alpha: interactions): the strike's look and sound (a meteor falls,
    /// a bomb drops, a missile flies, a mushroom cloud rises, lightning strikes...), then at impact its effects: creatures
    /// by blast zone (<see cref="PowerSystem"/>), the land (craters, scorch, fallout, rain, quake, new forest as terrain
    /// edits) and spawns. Everything after impact goes through the simulation's queues.
    /// </summary>
    public sealed class PowerController
    {
        readonly EntityManager _em;
        readonly FxView _fx;
        readonly EntityQuery _powerQuery, _editQuery, _lifeQuery;
        uint _rng = 0x9E3779B9u;

        public PowerController(EntityManager em, FxView fx)
        {
            _em = em;
            _fx = fx;
            _powerQuery = em.CreateEntityQuery(ComponentType.ReadOnly<PowerQueue>());
            _editQuery = em.CreateEntityQuery(ComponentType.ReadOnly<TerrainEditQueue>());
            _lifeQuery = em.CreateEntityQuery(ComponentType.ReadOnly<LifeState>());
        }

        static Vector3 World(int x, int y, float lift = 0f) => new Vector3(x + 0.5f, PackTerrainView.TileToWorldY(y + 0.5f) + lift, 0f);

        public void Use(PowerKind k, int x, int y)
        {
            Vector3 at = World(x, y);
            switch (k)
            {
                case PowerKind.Lightning:
                    _fx.Play("wx_lightning_strike", at + new Vector3(0f, 2f, 0f), 1.4f, 31800);
                    _fx.Sound("magic_thunder");
                    _fx.Flash(0.12f);
                    Impact(k, x, y, 0.12f);
                    _fx.After(0.15f, () => _fx.Play("smoke_rise", at, 1.5f, 31000));
                    break;
                case PowerKind.Meteor:
                    _fx.Sound("disaster_meteor");
                    _fx.Fly("wx_meteor", at + new Vector3(18f, 26f, 0f), at, 1.1f, 2.2f, () =>
                    {
                        Boom(at, 5.5f, "extra_blast_near", 0.8f, 1.2f);
                        Impact(k, x, y, 0f);
                        Fires(at, 7, 6f);
                    });
                    break;
                case PowerKind.Bomb:
                    _fx.Sound("creature_whoosh_magic", 0.6f);
                    _fx.Fly("bomb_2", at + new Vector3(0f, 14f, 0f), at, 0.7f, 1.6f, () =>
                    {
                        Boom(at, 3f, "combat_explosion_big", 0.5f, 0.6f);
                        Impact(k, x, y, 0f);
                        Fires(at, 3, 4f);
                    });
                    break;
                case PowerKind.Missile:
                    _fx.Sound("magic_fire_launch", 0.8f);
                    _fx.Fly("missile_315", at + new Vector3(-22f, 10f, 0f), at, 0.9f, 1.6f, () =>
                    {
                        Boom(at, 4f, "extra_blast_near", 0.6f, 0.8f);
                        Impact(k, x, y, 0f);
                        Fires(at, 4, 5f);
                    });
                    break;
                case PowerKind.Nuke:
                    _fx.Sound("magic_charge", 0.7f);
                    _fx.Fly("bomb_2", at + new Vector3(0f, 18f, 0f), at, 1.2f, 2f, () =>
                    {
                        _fx.Flash(1.4f);
                        _fx.Shake(2.5f, 2.2f);
                        _fx.Sound("extra_nuke_near", 1f);
                        _fx.PlayFrames("nuke_", 13, 6f, at, 7f, 31900, holdLast: 2.5f);
                        _fx.Play("explosion_2", at, 9f, 31850);
                        Impact(k, x, y, 0f);
                        Fires(at, 14, 9f);
                    });
                    break;
                case PowerKind.Wildfire:
                    _fx.Sound("building_house_fire", 0.8f);
                    Fires(at, 12, 5f);
                    Impact(k, x, y, 0.6f);
                    break;
                case PowerKind.Rain:
                    _fx.Sound("building_debris_rain", 0.35f);
                    for (int i = 0; i < 6; i++)
                    {
                        Vector3 o = new Vector3(Rand(-8f, 8f), Rand(-8f, 8f), 0f);
                        _fx.Play("wx_rain_tile", at + o, 4f, 31200, loopSeconds: 4f);
                    }
                    Impact(k, x, y, 1.5f);
                    break;
                case PowerKind.Quake:
                    _fx.Sound("disaster_quake");
                    _fx.Shake(1.6f, 1.8f);
                    _fx.Play("wx_quake", at, 5f, 31000, loopSeconds: 1.6f);
                    for (int i = 0; i < 6; i++) _fx.Play("smoke_rise", at + new Vector3(Rand(-9f, 9f), Rand(-9f, 9f), 0f), 2f, 31000);
                    Impact(k, x, y, 0.4f);
                    break;
                case PowerKind.Forest:
                    _fx.Sound("magic_heal", 0.7f);
                    for (int i = 0; i < 8; i++) _fx.PlayFrames("sparkle_", 2, 4f, at + new Vector3(Rand(-5f, 5f), Rand(-5f, 5f), 0f), 1.5f, 31000, holdLast: 0.6f);
                    Impact(k, x, y, 0.3f);
                    break;
                case PowerKind.Bless:
                    _fx.Sound("magic_heal");
                    for (int i = 0; i < 10; i++) _fx.Play("status_heal", at + new Vector3(Rand(-6f, 6f), Rand(-6f, 6f), 0f), 1.6f, 31000, loopSeconds: 1.5f);
                    Impact(k, x, y, 0.2f);
                    break;
                case PowerKind.Plague:
                    _fx.Sound("event_plague");
                    for (int i = 0; i < 10; i++) _fx.Play("status_sick", at + new Vector3(Rand(-7f, 7f), Rand(-7f, 7f), 0f), 1.6f, 31000, loopSeconds: 2.5f);
                    Impact(k, x, y, 0.3f);
                    break;
                case PowerKind.SpawnPeople:
                case PowerKind.SpawnAnimals:
                    _fx.Sound("event_birth", 0.8f);
                    _fx.PlayFrames("sparkle_", 2, 4f, at, 2f, 31000, holdLast: 0.6f);
                    Spawn(k, x, y);
                    break;
            }
        }

        void Boom(Vector3 at, float scale, string sound, float shake, float flash)
        {
            _fx.Play("explosion_2", at, scale, 31850);
            _fx.Play("explosion_1", at + new Vector3(1.2f, 0.6f, 0f), scale * 0.6f, 31860);
            _fx.After(0.25f, () => _fx.Play("smoke_rise", at + new Vector3(0f, 1f, 0f), scale * 0.9f, 31700));
            _fx.Sound(sound);
            _fx.Shake(shake, 0.6f + shake * 0.4f);
            if (flash > 0f) _fx.Flash(flash * 0.25f);
        }

        void Fires(Vector3 at, int count, float radius)
        {
            for (int i = 0; i < count; i++)
            {
                Vector3 o = new Vector3(Rand(-radius, radius), Rand(-radius, radius), 0f);
                if (o.magnitude > radius) o *= radius / o.magnitude;
                float delay = Rand(0.1f, 0.6f), life = Rand(3f, 6f);
                _fx.After(delay, () => _fx.Play("fire", at + o, 1.6f, 31600, loopSeconds: life));
            }
        }

        /// <summary>Effects on creatures and land, after an optional delay (the moment of impact).</summary>
        void Impact(PowerKind k, int x, int y, float delay)
        {
            _fx.After(delay, () =>
            {
                if (!_powerQuery.IsEmpty)
                    _em.GetBuffer<PowerStrikeCommand>(_powerQuery.GetSingletonEntity()).Add(new PowerStrikeCommand { Kind = k, Tile = new int2(x, y) });
                if (!_editQuery.IsEmpty)
                {
                    var edits = _em.GetBuffer<TerrainEditCommand>(_editQuery.GetSingletonEntity());
                    foreach (var e in PowerRules.TerrainEdits(k, x, y)) edits.Add(new TerrainEditCommand { Edit = e });
                }
            });
        }

        void Spawn(PowerKind k, int x, int y)
        {
            if (_lifeQuery.IsEmpty) return;
            var buffer = _em.GetBuffer<SpawnCreatureCommand>(_lifeQuery.GetSingletonEntity());
            SpeciesId[] kinds = k == PowerKind.SpawnPeople
                ? new[] { SpeciesId.Human, SpeciesId.Elf, SpeciesId.Orc, SpeciesId.Dwarf }
                : new[] { SpeciesId.Sheep, SpeciesId.Cow, SpeciesId.Deer, SpeciesId.Rabbit, SpeciesId.Wolf };
            SpeciesId s = kinds[(int)(Next() % (uint)kinds.Length)];
            for (int i = 0; i < 5; i++)
                buffer.Add(new SpawnCreatureCommand { Species = s, Tile = new int2(x + (int)(Next() % 3) - 1, y + (int)(Next() % 3) - 1) });
        }

        uint Next() { _rng ^= _rng << 13; _rng ^= _rng >> 17; _rng ^= _rng << 5; return _rng; }
        float Rand(float a, float b) => a + (b - a) * (Next() % 10000) / 10000f;
    }
}
