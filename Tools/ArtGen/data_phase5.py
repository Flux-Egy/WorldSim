"""Phase 5 data: creature stats, interaction rules (who can do what to whom, which animations / death / FX / SFX),
animation-event index and the asset size report.  Output -> Resources/WorldSimData/*.json"""
import os, sys, json, glob
import animals as AN, bestiary as BS, beings as BE, spells as SPL, humans as HU
import export_humans as EH

# ------------------------------------------------------------------ creature stats
DIET = {'herbivore': {'cow', 'sheep', 'goat', 'horse', 'deer', 'rabbit', 'pig', 'elephant', 'mammoth', 'giraffe', 'zebra', 'rhino', 'hippo', 'buffalo', 'yak', 'moose',
                      'reindeer', 'llama', 'panda', 'squirrel', 'tortoise', 'kangaroo', 'sauropod', 'ox', 'thunder_hare', 'frost_elk', 'horned_strider', 'steppe_ram',
                      'woolly_rhino', 'tusk_seal', 'stone_ram', 'glimmer_deer', 'rock_tortoise', 'unicorn', 'pegasus', 'chicken', 'duck'},
        'carnivore': {'wolf', 'fox', 'bear', 'lion', 'tiger', 'leopard', 'hyena', 'polar_bear', 'cat', 'dog', 'crocodile', 'ice_wolf', 'shadow_panther', 'sand_fox', 'cliff_lynx',
                      'ember_hound', 'lava_salamander', 'hellhound', 'dragon', 'wyvern', 'griffin', 'chimera', 'basilisk', 'bog_lurker', 'nightmare'},
        }
HABITAT = {'elephant': 'SAVANNA', 'giraffe': 'SAVANNA', 'zebra': 'SAVANNA', 'lion': 'SAVANNA', 'hyena': 'SAVANNA', 'rhino': 'SAVANNA', 'buffalo': 'SAVANNA',
           'tiger': 'JUNGLE', 'leopard': 'JUNGLE', 'panda': 'FOREST', 'hippo': 'SWAMP', 'crocodile': 'SWAMP', 'yak': 'MOUNTAIN', 'llama': 'MOUNTAIN', 'moose': 'PINE TAIGA',
           'reindeer': 'TUNDRA', 'polar_bear': 'SNOW', 'mammoth': 'TUNDRA', 'kangaroo': 'STEPPE', 'camel': 'DESERT DUNES', 'sauropod': 'JUNGLE', 'raccoon': 'FOREST',
           'badger': 'FOREST', 'squirrel': 'FOREST', 'hedgehog': 'MEADOW', 'tortoise': 'BEACH', 'lizard': 'BADLANDS', 'rat': 'FARMLAND', 'ox': 'FARMLAND'}
DOMESTIC = {'cow', 'sheep', 'goat', 'horse', 'pig', 'chicken', 'duck', 'dog', 'cat', 'ox', 'llama', 'yak', 'reindeer', 'camel', 'elephant'}
PRODUCE = {'cow': ['milk', 'meat', 'leather'], 'sheep': ['wool', 'meat'], 'goat': ['milk', 'meat'], 'chicken': ['eggs', 'meat'], 'duck': ['eggs', 'meat'], 'pig': ['meat'],
           'llama': ['wool'], 'yak': ['milk', 'wool'], 'bee': ['honey'], 'ox': ['work'], 'horse': ['mount'], 'camel': ['mount', 'milk'], 'elephant': ['mount', 'work']}
RIDABLE = {'horse', 'camel', 'elephant', 'mammoth', 'reindeer', 'unicorn', 'pegasus', 'griffin', 'dragon', 'wyvern', 'nightmare', 'ox', 'yak', 'llama', 'giant_eagle', 'roc'}


def size_of(spec):
    r = spec.get('rx', 5)
    return 'tiny' if r < 3.5 else 'small' if r < 5.5 else 'medium' if r < 8 else 'large' if r < 11 else 'huge'


def stat_block(size, carn, magic=False):
    base = {'tiny': (8, 1, 1.2), 'small': (20, 3, 1.4), 'medium': (45, 7, 1.3), 'large': (110, 14, 1.0), 'huge': (260, 26, .8), 'titan': (5000, 120, .5)}[size]
    hp, dmg, spd = base
    if carn: dmg = int(dmg * 1.6)
    if magic: hp, dmg = int(hp * 1.8), int(dmg * 1.8)
    return dict(hp=hp, damage=dmg, speed=spd)


def creatures():
    BS.install(); BS.install_magic()
    out = {}
    land = [n for n in AN.SP if not n.startswith('_')]
    for n in land:
        s = AN.SP[n]
        carn = n in DIET['carnivore']
        cat = 'magic_beast' if n in BS.MAGIC_SP else 'biome_creature' if n in BS.BIOME_SP else 'animal'
        size = size_of(s)
        out[n] = dict(category=cat, sprite_prefix=f'a_{n}_', atlas='fauna_land', diet='carnivore' if carn else 'herbivore' if n in DIET['herbivore'] else 'omnivore',
                      habitat=BS.BIOME_SP[n][0] if n in BS.BIOME_SP else HABITAT.get(n, 'ANY_LAND'), size=size, hostile=carn, tameable=n in DOMESTIC or n in RIDABLE,
                      ridable=n in RIDABLE, produce=PRODUCE.get(n, ['meat']), flying=n in ('dragon', 'wyvern', 'griffin', 'pegasus', 'chimera'),
                      poses=list(BS.POSES) + ['hurt', 'dead', 'remains', 'burnt', 'frozen'], has_young=True, **stat_block(size, carn, cat == 'magic_beast'))
    for n, s in list(BS.BIRDS.items()) + list(BS.GROUND_BIRDS.items()):
        magic = n in BS.MAGIC_BIRDS
        size = 'huge' if s.get('size', 1) > 2.2 else 'large' if s.get('size', 1) > 1.5 else 'small'
        out[n] = dict(category='magic_beast' if magic else 'bird', sprite_prefix=f'c_{n}_', atlas='fauna_critters', diet='carnivore' if n in ('eagle', 'owl', 'giant_eagle', 'roc', 'mesa_vulture', 'thunderbird', 'phoenix') else 'omnivore',
                      habitat='ANY', size=size, hostile=n in ('giant_eagle', 'roc', 'thunderbird', 'mesa_vulture'), flying=n in BS.BIRDS, tameable=n in ('parrot', 'eagle', 'giant_eagle', 'roc'),
                      ridable=n in RIDABLE, can_grab_human=n in ('roc', 'giant_eagle', 'thunderbird'), produce=['feathers', 'meat'], **stat_block(size, False, magic))
    for n, (f, s) in BS.SPECIAL.items():
        out[n] = dict(category='critter', sprite_prefix=f'c_{n}_', atlas='fauna_critters', size='tiny', hostile=n in ('snake', 'cobra'), venomous=n in ('snake', 'cobra', 'bee'),
                      flying=bool(s.get('fly')), produce=PRODUCE.get(n, []), habitat='ANY', **stat_block('tiny', n in ('snake', 'cobra')))
    for n, (bi, f, s) in BS.BIOME_SPECIAL.items():
        size = 'huge' if s.get('size', 1) > 1.7 or f is BS.worm else 'medium'
        out[n] = dict(category='biome_creature', sprite_prefix=f'c_{n}_', atlas='fauna_critters', habitat=bi, size=size, hostile=True,
                      venomous=n in ('dune_scorpion', 'giant_spider', 'cave_spider', 'mire_toad'), can_swallow_human=n == 'sand_worm', **stat_block(size, True))
    for n, v in BS.SEA.items():
        kind = v[5]
        size = 'huge' if v[1] > 40 else 'large' if v[1] > 20 else 'small'
        out[n] = dict(category='sea', sprite_prefix=f's_{n}_', atlas='fauna_sea', habitat='OCEAN' if n not in ('carp', 'catfish', 'piranha', 'salmon') else 'RIVER/LAKE',
                      size=size, hostile=n in ('shark', 'hammerhead', 'piranha', 'orca', 'kraken_spawn', 'coral_serpent'), fishable=size != 'huge', aquatic=True,
                      produce=['fish'] if kind != 'whale' else ['oil', 'meat'], **stat_block(size, n in ('shark', 'hammerhead', 'piranha', 'orca')))
    for n, s in BE.B.items():
        h = s['h']
        size = 'small' if h < 22 else 'medium' if h < 33 else 'large' if h < 42 else 'huge'
        spirit = s['lower'] in ('smoke', 'float')
        out[n] = dict(category='supernatural', sprite_prefix=f'm_{n}_', atlas='beings', size=size, hostile=n not in ('treant', 'water_elemental'), spirit=spirit,
                      flying=bool(s.get('wings')) or spirit, death='dissolve' if spirit else 'fall',
                      abilities=(['possess_human', 'grant_wish', 'vanish'] if n in ('jinn', 'marid', 'sand_djinn') else ['fire_aura', 'curse'] if n in ('demon', 'demon_lord', 'afreet', 'imp')
                                 else ['raise_dead'] if n == 'lich' else ['drain_life'] if n in ('vampire', 'wraith', 'shade') else []),
                      summonable_by=['demon_gate'] if n in ('demon', 'imp', 'demon_lord') else ['jinn_binding'] if n in ('jinn', 'marid', 'afreet', 'sand_djinn') else ['raise_dead'] if n in ('skeleton', 'zombie', 'ghoul') else [],
                      poses=['idle', 'move', 'attack', 'cast', 'hurt', 'death'], **stat_block(size, True, True))
    for n in list(BE.TITANS) + list(BE.SPECIAL_TITANS):
        poses = list(BE.TITAN_POSES) if n in BE.TITANS else list(BE.SPECIAL_TITANS[n][2])
        out[n] = dict(category='titan', sprite_prefix=f't_{n}_', atlas='titans', size='titan', hostile=True, aquatic=n in ('sea_serpent', 'kraken'),
                      poses=poses + ['hurt', 'death', 'remains', 'burnt'], can_grab_human='grab' in poses, stomp='stomp' in poses, breath='breath' in poses,
                      destroys_buildings=True, sinks_ships=n in ('sea_serpent', 'kraken'), **stat_block('titan', True, True))
    return out


# ------------------------------------------------------------------ interaction rules
DEATH_BY_DAMAGE = {'blade': 'weapon', 'blunt': 'weapon', 'pierce': 'arrow', 'bullet': 'weapon', 'explosive': 'explosion', 'fire': 'burn', 'cold': 'freeze', 'lightning': 'electric',
                   'poison': 'poison', 'disease': 'poison', 'water': 'drown', 'crush': 'crushed', 'bite': 'eaten', 'magic': 'dissolve', 'radiation': 'irradiated', 'nuclear': 'burn'}
WEAPON_DAMAGE = {'club': 'blunt', 'sling': 'blunt', 'spear': 'pierce', 'bow': 'pierce', 'xbow': 'pierce', 'sword': 'blade', 'axe': 'blade', 'musket': 'bullet', 'rifle': 'bullet',
                 'flamer': 'fire', 'laser': 'magic', 'staff': 'magic', 'cannon': 'explosive', 'tank': 'explosive', 'artillery': 'explosive', 'bomb': 'explosive', 'missile': 'explosive',
                 'nuke': 'nuclear'}
SPELL_DAMAGE = {'fire': 'fire', 'ice': 'cold', 'lightning': 'lightning', 'poison': 'poison', 'arcane': 'magic', 'earth': 'crush', 'wind': 'blunt', 'shadow': 'magic', 'water': 'water',
                'sand': 'blunt', 'light': 'fire', 'smoke': 'magic', 'life': None}
CORPSE_BY_DEATH = {'weapon': 'dead', 'arrow': 'dead', 'explosion': 'burnt', 'burn': 'burnt', 'freeze': 'frozen', 'electric': 'burnt', 'poison': 'dead', 'drown': 'dead',
                   'crushed': 'remains', 'eaten': 'remains', 'dissolve': None, 'irradiated': 'dead'}


def interactions(cr):
    rules = []
    def R(attacker, victim, verb, attacker_anim, victim_anim, damage=None, fx=None, sfx=None, outcome=None, note=None):
        r = dict(attacker=attacker, victim=victim, verb=verb, attacker_anim=attacker_anim, victim_anim=victim_anim)
        if damage: r['damage_type'] = damage; r['victim_death'] = DEATH_BY_DAMAGE.get(damage)
        if fx: r['fx'] = fx
        if sfx: r['sfx'] = sfx
        if outcome: r['outcome'] = outcome
        if note: r['note'] = note
        rules.append(r)
    # humans vs humans / soldiers
    for st, (lk, atk, era) in EH.SOLDIERS.items():
        dmg = WEAPON_DAMAGE.get(lk['weapon'], 'blade')
        proj = {'shoot_bow': 'arrow_<deg>', 'shoot_gun': 'fx muzzle + bullet', 'throw': 'spear/stone projectile', 'cast': 'spell projectile'}.get(atk)
        R(f'soldier:{st}', 'human|soldier', 'attack', f'sol_<species>_{st}_{atk}', 'h_*_hurt -> h_*_death_' + DEATH_BY_DAMAGE[dmg], dmg, proj, 'combat_*', 'kill or wound')
        R(f'soldier:{st}', 'animal|creature', 'hunt/attack', f'sol_<species>_{st}_{atk}', 'a_*_hurt -> a_*_dead', dmg, proj, None, 'kill; corpse gives meat/leather')
        R(f'soldier:{st}', 'titan', 'attack titan', f'sol_<species>_{st}_{atk}', 't_*_hurt (+ t_fx_stuck_arrows_* on hit anchor)', dmg, proj, None,
          'titan hp drains slowly; morale check: soldiers may switch to flee/cower', 'many humans needed; titan answers with stomp/grab/breath')
    # predators eat humans and animals
    for n, c in cr.items():
        if c.get('category') in ('animal', 'biome_creature', 'magic_beast') and c.get('hostile'):
            R(n, 'human', 'hunt', f'{n}_adult_attack', 'h_*_flee -> h_*_hurt -> h_*_death_eaten', 'bite', 'dust puff', 'creature_growl / creature_chomp', 'human eaten; grave stone left (no gore)')
            R(n, 'herbivore', 'hunt', f'{n}_adult_attack -> {n}_adult_eat', 'a_*_hurt -> a_*_remains', 'bite', None, 'creature_chomp')
        if c.get('category') == 'sea' and c.get('hostile'):
            R(n, 'human(swimming)|fisher', 'attack from water', f'{n}_adult_attack', 'h_*_swim -> h_*_death_eaten', 'bite', 'splash', 'world_splash')
    for n, c in cr.items():
        if c.get('can_grab_human'):
            R(n, 'human', 'grab and carry', f'{n}_grab' if c['category'] == 'titan' else f'{n}_adult_fly', 'h_*_grabbed (dangles, struggles)', 'crush', None, 'body_scream',
              'carried off; dropped = death_crushed, eaten = death_eaten')
        if c.get('stomp'): R(n, 'human|building|unit', 'stomp', f'{n}_stomp', 'h_*_death_crushed', 'crush', 't_fx_crack_*', 'creature_step_big', 'area kill radius ~2 tiles; buildings -> __damaged/__ruined')
        if c.get('breath'): R(n, 'area', 'fire breath', f'{n}_breath', 'h_*_burning -> h_*_death_burn', 'fire', 'wx_wildfire_* on tiles', 'creature_dragon_breath', 'sets trees (…_burning) and farms (farm_*_burnt) on fire')
        if c.get('sinks_ships'): R(n, 'ship', 'sink ship', f'{n}_grab', 'ship_*_sink', 'crush', 'splash', 'creature_tentacle', 'crew -> h_*_swim / h_*_death_drown')
        if c.get('can_swallow_human'): R(n, 'human|animal', 'swallow from below', f'{n}_adult_attack', 'h_*_death_eaten', 'bite', 'sand burst', 'creature_burrow')
    # supernatural
    R('jinn|marid|sand_djinn', 'human', 'possess', 'm_jinn_possess (or <kind>_cast)', 'h_*_possessed + ov_possessed_* overlay', None, 'smoke ribbon', 'magic_whisper',
      'human becomes controlled for N days; exorcism-free: ends when the jinn is killed or leaves')
    R('demon|demon_lord|afreet|imp', 'human|building', 'burn', '<kind>_attack / <kind>_cast', 'h_*_burning -> h_*_death_burn', 'fire', 'sp_fireball_*', 'magic_fire_launch')
    R('lich', 'corpse', 'raise dead', 'lich_cast', 'corpse -> m_skeleton_* / m_zombie_* (sp_raise_dead_circle)', None, 'sp_raise_dead_circle_*', 'magic_portal')
    R('vampire|wraith|shade', 'human', 'drain life', '<kind>_cast', 'h_*_sick -> h_*_death_dissolve', 'magic', 'sp_life_drain_beam_*', 'magic_curse')
    R('ghoul|zombie', 'human', 'bite / infect', '<kind>_attack', 'h_*_sick -> rises as zombie', 'disease', None, 'creature_moan')
    R('human', 'supernatural', 'attack', 'sol_* attack', 'm_<kind>_hurt -> m_<kind>_death_* (spirits dissolve)', 'blade', None, None, 'spirits take reduced physical damage; magic/fire full')
    # spells
    for sp, (el, shape) in SPL.SPELLS.items():
        dmg = SPELL_DAMAGE.get(el)
        R('caster', 'target/area', f'cast {sp}', '<caster>_cast (event spawn_spell)', ('h_*_death_' + DEATH_BY_DAMAGE[dmg]) if dmg else 'heal / buff', dmg,
          f'sp_{sp}_*', 'magic_*', 'buff' if shape == 'aura' and el in ('life', 'arcane', 'earth', 'wind') else 'damage' if dmg else 'support')
    # strategic weapons & disasters
    R('missile/nuke', 'area', 'strike', 'st_* flight -> nuke_* / boom_*', 'h_*_death_explosion (core), h_*_death_burn (ring), h_*_death_irradiated (fallout, days later)', 'nuclear',
      'nuke_*, shockwave_*, crater_nuclear, fallout_*', 'world_nuke, world_siren', 'buildings in radius -> __ruined; trees -> *_burnt; fallout decal for N years')
    for wx, death in (('tornado', 'crushed'), ('tsunami', 'drown'), ('volcano', 'burn'), ('lightning_strike', 'electric'), ('meteor', 'explosion'), ('wildfire', 'burn'), ('quake', 'crushed'),
                      ('blizzard', 'freeze'), ('plague', 'poison'), ('acid_rain', 'poison')):
        R(f'disaster:{wx}', 'area', wx, f'wx_{wx}_*', f'h_*_flee / h_*_death_{death}', None, f'wx_{wx}_*', f'disaster_{wx}', None)
    for cause, st in (('explosion nearby', '_Flash -> __damaged'), ('direct hit / bomb / missile', '__collapse (anim) -> __ruined'), ('fire / fire spell / dragon breath / lightning', '_Burn .4 + ov_fire -> _Burn 1'),
                      ('tsunami / flood / river overflow', 'ov_flood (until water recedes) -> __damaged'), ('quake / titan stomp', '__collapse'), ('blizzard / ice spell', '_Frost'),
                      ('kingdom extinct for years', '_Overgrown')):
        R(f'cause:{cause}', 'building', 'damage building', None, st, None, 'decal_rubble / pt_dust / pt_smoke / pt_ember', 'building_*', 'residents: flee, cower or die by zone rules')
    # work / peaceful interactions
    for act, target, res in (('chop', 'tree', 'logs_* (tree *_fall -> *_stump)'), ('mine', 'ore', 'ore_*_<0..3> depletion'), ('farm', 'farm tile', 'farm_<crop>_<stage>'), ('build', 'construction', 'b_*__construction -> b_*'),
                             ('fish', 'water', 'fish item'), ('herd', 'domestic animal', 'animal follows'), ('milk', 'cow|goat|yak|camel', 'milk'), ('tame', 'tameable animal', 'animal joins kingdom'),
                             ('ride', 'ridable animal', 'h_*_ride placed on animal top anchor'), ('gather', 'bush/field', 'food'), ('water', 'farm', 'farm stays green'), ('carry', 'item', 'moves cargo')):
        R('human', target, act, f'h_*_{act}', None, None, None, f'world_{act}' if act in ('chop', 'mine', 'hammer') else None, res)
    return rules


BLAST_ZONES = {   # radius in tiles for each zone; zone effects below
    'grenade': [0, .5, 1.5, 3, 0], 'cannon_shell': [0, 1, 2, 4, 0], 'catapult_stone': [0, .6, 0, 2, 0], 'aerial_bomb': [.5, 2, 4, 7, 0], 'cruise_missile': [1, 3, 5, 9, 0],
    'ballistic_missile': [2, 5, 8, 14, 0], 'tactical_nuke': [4, 9, 16, 26, 40], 'strategic_nuke': [10, 22, 40, 64, 110], 'meteor': [3, 7, 12, 20, 0], 'volcano_blast': [3, 6, 10, 16, 0]}
ZONE_EFFECTS = [
    dict(zone=0, name='fireball', human='h_*_death_vaporized', animal='a_*_burnt (no corpse for small)', building='*__collapse -> rubble (b_*__ruined)', tree='removed (decal_scorch)',
         ground='decal_crater_<size> + decal_scorch', sfx='extra_blast_near / extra_nuke_near', chance_survive=0.0),
    dict(zone=1, name='blast', human='h_*_death_explosion (flung)', animal='a_*_dead / a_*_burnt', building='*__collapse (stage 0..3)', tree='*_fall + *_burnt',
         ground='decal_scorch + decal_rubble', sfx='extra_blast_near', chance_survive=0.1),
    dict(zone=2, name='thermal', human='h_*_burning (flee) -> h_*_death_burn; survivors h_*_hurt', animal='a_*_burnt', building='shader _Burn 0.4 + ov_fire_<w_class> on roof anchor + ov_smoke_column -> _Burn 1.0 (burnt)', tree='*_burning -> *_burnt',
         ground='decal_ash', sfx='extra_blast_mid + building_house_fire', chance_survive=0.4),
    dict(zone=3, name='shockwave', human='h_*_knocked (flung, gets up) + h_*_hurt; some h_*_death_crushed (debris)', animal='a_*_hurt / flee', building='_Flash then *__damaged',
         tree='*_sway hard / some *_fall', ground='pt_* debris particles', sfx='extra_blast_mid + extra_shockwave_pass + building_glass_break', chance_survive=0.85),
    dict(zone=4, name='flash_and_fallout', human='h_*_blinded (flash); days later h_*_sick -> h_*_death_irradiated', animal='sick', building='intact; fallout overlay', tree='intact; autumn tint',
         ground='fallout_* decal', sfx='extra_blast_far + extra_ear_ring + world_geiger', chance_survive=0.95),
]


def anim_events(art_root):
    out = {}
    for f in glob.glob(os.path.join(art_root, '**', '*.json'), recursive=True):
        try: d = json.load(open(f))
        except Exception: continue
        if not isinstance(d, dict) or 'animList' not in d: continue
        for a in d['animList']:
            if a.get('events'): out[a['name']] = a['events']
    return out


def size_report(root):
    res = os.path.join(root, 'Assets', 'WorldSim', 'Resources')
    def du(p):
        return sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(p) for f in fs if not f.endswith('.meta'))
    art = os.path.join(res, 'WorldSimArt')
    n_sprites = 0; n_anims = 0
    per = {}
    for f in glob.glob(os.path.join(art, '**', '*.json'), recursive=True):
        d = json.load(open(f))
        if isinstance(d, dict) and 'frameList' in d:
            n_sprites += len(d['frameList']); n_anims += len(d.get('animList', []))
            per[d.get('atlas', os.path.basename(f))] = len(d['frameList'])
    aud = os.path.join(res, 'WorldSimAudio')
    n_audio = len(glob.glob(os.path.join(aud, '**', '*.ogg'), recursive=True))
    data = os.path.join(res, 'WorldSimData')
    return dict(sprites=n_sprites, animations=n_anims, audio_clips=n_audio, data_files=len(glob.glob(os.path.join(data, '*.json'))),
                bytes=dict(art=du(art), audio=du(aud), data=du(data), code_and_tools=du(os.path.join(root, 'Assets', 'WorldSim', 'Runtime')) + du(os.path.join(root, 'Tools'))),
                per_atlas=per)


if __name__ == '__main__':
    root = sys.argv[1]
    data = os.path.join(root, 'Assets', 'WorldSim', 'Resources', 'WorldSimData'); os.makedirs(data, exist_ok=True)
    cr = creatures()
    json.dump(dict(creatures=cr, note='stats are starting values for balancing; poses = available animation names'), open(os.path.join(data, 'creatures.json'), 'w'), indent=1)
    rules = interactions(cr)
    json.dump(dict(rules=rules, blast_zones=BLAST_ZONES, zone_effects=ZONE_EFFECTS,
                   building_states={'baked': ['__damaged', '__ruined', '__construction', '__collapse_0..3'],
                                    'shader': {'hit': '_Flash', 'burning': '_Burn 0.4 + ov_fire_<w_class> + ov_smoke_column', 'burnt': '_Burn 1', 'frozen': '_Frost 1', 'overgrown': '_Overgrown 0.6'},
                                    'overlay': {'flooded': 'ov_flood_<w_class> at the pivot'}, 'w_class': 'tag on every building frame (s/m/l/xl)', 'roof': 'anchor on every building frame'},
                   child_deaths='any cause -> h_<species>_<g>_child_death_fade_0..3 (fade + grave stone); owner decision',
                   death_by_damage=DEATH_BY_DAMAGE, corpse_by_death=CORPSE_BY_DEATH, weapon_damage=WEAPON_DAMAGE, spell_damage=SPELL_DAMAGE,
                   death_types=list(HU.DEATHS), human_actions=list(HU.ACTIONS),
                   naming={'human': 'h_<species>_<m|f>_<tribal|medieval|modern|child>_<action>_<f> / _death_<type>_<f>', 'soldier': 'sol_<species>_<type>_<action>_<f>',
                           'animal': 'a_<species>_<adult|young>_<pose>_<f>', 'critter': 'c_<species>_<adult|young>_<pose>_<f>', 'sea': 's_<species>_<adult|young>_<pose>_<f>',
                           'being': 'm_<kind>_<pose>_<f>', 'titan': 't_<name>_<pose>_<f>', 'spell': 'sp_<spell>_<part>_<f>'}),
              open(os.path.join(data, 'interactions.json'), 'w'), indent=1)
    ev = anim_events(os.path.join(root, 'Assets', 'WorldSim', 'Resources', 'WorldSimArt'))
    json.dump(dict(events=ev, note='frame index -> event; sfx:<key> resolved by WorldSimAudioDB.ResolveEventSfx'), open(os.path.join(data, 'animation_events.json'), 'w'))
    rep = size_report(root)
    json.dump(rep, open(os.path.join(data, 'asset_report.json'), 'w'), indent=1)
    print(len(cr), 'creatures', len(rules), 'rules', len(ev), 'animations with events')
    print({k: v for k, v in rep.items() if k != 'per_atlas'})
