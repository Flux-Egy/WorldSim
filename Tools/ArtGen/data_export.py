"""Exports the design data the art was generated from, so the Unity game uses the same rules (Data/*.json)."""
import json, os
import culturegen as cg
from buildings import ERAS, CATS, CAT_NAMES
import army2, airsheet, terrain, featureboard, export_all as XA

OUT = os.environ.get('WORLDSIM_DATA_OUT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Assets', 'WorldSim', 'Resources', 'WorldSimData')
os.makedirs(OUT, exist_ok=True)
hexs = lambda rp: ['#%02x%02x%02x' % tuple(c) for c in rp]

culture = {
    'how_it_works': 'Each new kingdom rolls 3 founders with 2 traits each. Votes: leader x2. Top 2 values -> belief, rule, town layout, roof, dress, colours, crest symbol. Biome -> wall material, skin & hair pools.',
    'traits': cg.TRAITS, 'trait_colors': cg.TRAIT_COL, 'value_of_trait': cg.VALUE_OF, 'rule_of_value': cg.RULE,
    'belief_of_value': {k: {'name': v[0], 'hue': v[1]} for k, v in cg.BELIEF.items()},
    'biome_walls': cg.BIOMES, 'biome_ground_tint': cg.BIOME_TINT, 'biome_skins': cg.SKIN_BY, 'biome_hairs': cg.HAIR_BY,
    'symbol_of_value': cg.SYM_BY_VALUE, 'crest_symbols': list(cg.SYMBOLS),
    'roof_rules': ['nomadic or steppe -> yurt', 'GRANDEUR/DEVOUT -> dome|cone', 'TRADITION/SCHOLARLY -> tiered|hip', 'COMMUNAL -> gable|thatch',
                   'MERCANTILE -> flat|hip', 'else -> gable|cone|flat|thatch', 'river/steppe: gable/tiered 50% -> flat', 'snow/forest: flat -> gable'],
    'ornament_rules': {'MARTIAL': ['banner', 'spikes'], 'DEVOUT': ['spire'], 'GRANDEUR': ['spire'], 'MERCANTILE': ['awning'], 'ARTISAN': ['tiles'],
                       'COMMUNAL': ['garden'], 'TRADITION': ['totem'], 'trait KIND': ['garden'], 'trait PROUD or GRANDEUR': ['tall towers']},
    'layout_of_value': {'MARTIAL': 'RING + WALLS', 'MERCANTILE': 'ALONG ROADS', 'DEVOUT': 'AROUND SANCTUM', 'COMMUNAL': 'CLUSTERS', 'SCHOLARLY': 'GRID',
                        'GRANDEUR': 'AXIAL AVENUE', 'TRADITION': 'TERRACES', 'NOMADIC': 'CAMP CIRCLES', 'ARTISAN': 'WINDING QUARTERS'},
    'dress': {'garment': 'river/coast/jungle -> robe|pants, else pants|kilt; nomads pants; women dress', 'male_head_by_value': {'MARTIAL': ['band', 'feathers'], 'DEVOUT': ['turban (river/coast)', 'hood'],
              'MERCANTILE': ['turban', 'skullcap', 'flatcap'], 'SCHOLARLY': ['skullcap', 'band'], 'GRANDEUR': ['turban'], 'TRADITION': ['bonnet', 'band'], 'NOMADIC': ['furhat'],
              'COMMUNAL': ['bare', 'band'], 'ARTISAN': ['feathers', 'bonnet'], 'SNOW biome': ['furhat']},
              'female_head': 'DEVOUT/GRANDEUR/TRADITION -> scarf|veil|bare|kerchief, else bare|kerchief|band', 'ruler_crown': {'MARTIAL': 'crown_north', 'GRANDEUR': 'crown_river', 'DEVOUT': 'crown_river', 'NOMADIC': 'furhat', 'else': 'circlet'}},
    'palette': 'ACC = hsv ramp from belief hue (+-18), ACC2 = complementary-ish (+150..200); ROOF = ACC for dome/cone, else from gable list; TEAM = kingdom colour',
    'names': {'consonant_sets': cg.CONS, 'vowel_sets': cg.VOWS, 'endings': cg.ENDS, 'patterns': [['CV', 'CVC'], ['CV', 'CV', 'CVC'], ['CVC', 'CV'], ['CV', 'CVN']],
              'rules': 'one consonant+vowel set per culture (children cultures keep it -> names sound related); collapse 3+ vowels to 2; max 8 letters; place = word + ending'},
    'split_rules': ['sea / mountain isolation for 200+ years', 'new seer (PIOUS/CURIOUS hero)', 'conquest merges -> hybrid', 'civil war', 'child keeps ~78% genes, mutates 1 visual gene'],
}
army = {'eras': ERAS, 'roles': army2.ROLES,
        'units': [{'era': e, 'era_name': ERAS[e], 'name': n, 'needs': req.split('+')} for e in range(6) for (n, req) in army2.U[e]],
        'aircraft': [{'id': k, 'name': n, 'era': e, 'needs': r.split('+')} for (k, n, e, r) in airsheet.NAMES],
        'air_defence': ['sam', 'radar', 'flak', 'ciws', 'laser_ad'],
        'sprite_keys': 'Units/army.json: u_<kind>_<frame>, m_<mounted>_<frame>, x_<machine>; Units/aircraft.json: air_<type>_<angle>, air_heli_<angle>_<frame>'}
world = {'biomes': [{'name': n, 'ground': c, 'props': p, 'speckle': s} for (n, c, p, s) in terrain.BIOMES],
         'elevation_levels': [{'level': i, 'name': n, 'color': c} for i, (n, c) in enumerate(terrain.LEVELS)],
         'elevation_render': 'draw rows back->front; top face at y - level*6 px (fine grid); if the cell in front is lower draw cliff_<mat>_<diff> below; water surface = level 3',
         'building_categories': CATS, 'category_names': CAT_NAMES, 'house_tiers': XA.TIERS,
         'day_night': {'tint': {'stone': [.20, .23, .40], 'medieval': [.25, .28, .47], 'modern': [.30, .33, .52], 'future': [.26, .28, .50]},
                       'lights': 'pixels with lit/fire/cyan colours keep full brightness + additive glow (radius 3 & 9 px); street lights per era: torch stakes, torch poles, gas lamps, sodium, holo pylons'}}
life = {'disease_template': {'name': 'generated from culture namer', 'vectors': ['AIR', 'RATS', 'WATER', 'ANIMALS'], 'stages': ['HEALTHY', 'INFECTED (no symptoms)', 'SICK', 'SEVERE', 'IMMUNE or DEAD'],
                             'cures_by_era': {'ANCIENT': 'herbs (slows)', 'MEDIEVAL': 'quarantine', 'MODERN': 'vaccine'}, 'visuals': 'shader _Sick on SKIN, status bubbles, cough cloud, flies, sweat overlay'},
        'combat_feedback': ['hit flash (_Flash=1 then fades)', 'damage numbers (3x5 font, red)', 'hp bar 12x3', 'animals die legs-up (a_*_dead)', 'people lie down (rotate 90)', 'grave sprite'],
        'powers': {'NATURE': ['rain', 'drought', 'lightning', 'quake', 'meteor', 'wildfire'], 'LIFE': ['humans', 'animals', 'forest'], 'FATE': ['bless', 'plague', 'inspire'], 'NATIONS': ['war', 'peace', 'take control']}}
backlog = [{'feature': n, 'source': tag, 'comments': v, 'what': d} for (fn, n, tag, v, d) in featureboard.B1 + featureboard.B2]

army['strategic'] = {
    'units': [
        {'id': 'srbm', 'name': 'TACTICAL BALLISTIC MISSILE', 'era': 4, 'needs': ['STEEL', 'FUEL', 'ROCKETRY'], 'launch_from': ['tel'], 'range_tiles': 300, 'warhead': 'conventional (explosion_2 x3)'},
        {'id': 'cruise', 'name': 'CRUISE MISSILE', 'era': 4, 'needs': ['STEEL', 'FUEL', 'GUIDANCE'], 'launch_from': ['tel', 'ship', 'bomber'], 'range_tiles': 220, 'flies_low': True},
        {'id': 'icbm', 'name': 'NUCLEAR ICBM', 'era': 4, 'needs': ['URANIUM', 'ENRICHMENT', 'ROCKETRY'], 'launch_from': ['silo', 'tel'], 'range_tiles': 'whole map', 'warhead': 'nuclear'},
        {'id': 'abm', 'name': 'INTERCEPTOR (ABM)', 'era': 4, 'needs': ['STEEL', 'RADAR', 'GUIDANCE'], 'launch_from': ['abm_battery'], 'intercept_chance': {'srbm': .6, 'cruise': .5, 'icbm': .3, 'hgv': .1}},
        {'id': 'hgv', 'name': 'HYPERSONIC GLIDER', 'era': 5, 'needs': ['FUSION', 'COMPOSITES'], 'launch_from': ['silo'], 'range_tiles': 'whole map', 'intercept_only_by': 'laser_ad / future ABM'}],
    'flight': 'boost: missile_flight sprites pointing up (270) with exhaust -> arc across the map (pick the nearest of 16 directions every frame) -> re-entry sprite over the target -> impact. Show a dotted arc + LAUNCH DETECTED alert to every nation with radar.',
    'nuclear_detonation': {'sequence': 'nuke_0..12 at 5 fps (flash frames also flash the screen white), shockwave decal 4 frames, then crater_nuclear + fallout overlay + radiation_glow + hazard_marker props',
                           'effects': {'blast_radius_tiles': 12, 'fire_radius_tiles': 20, 'buildings': 'ruined inside blast, damaged inside fire radius', 'people': 'die inside blast; RADIATION SICKNESS (disease stages, no contagion) inside fallout',
                                       'terrain': 'cells inside blast become IRRADIATED WASTE biome for 50-200 years', 'fallout': 'drifts with wind for 2-5 years'},
                           'politics': 'every nation remembers: relations -60 with the user, allies may leave, AI uses deterrence (a nation with nukes is rarely attacked by another nuclear nation). 5+ detonations in 10 years -> nuclear winter (global cold, famine).'},
    'sprite_keys': 'Units/strategic.json: st_tel_<0-5>, st_silo_<0-3>, st_abm_battery_<0-1>, st_<srbm|cruise|icbm|abm|hgv>_<angle x10>_<frame>, st_reentry_<0-1>, nuke_<0-12>, shockwave_<0-3>, crater_nuclear, fallout_<0-1>, radiation_glow, hazard_marker, grave_marker'}
life['powers']['STRIKES'] = ['missile strike', 'nuclear strike']
life['radiation_sickness'] = {'cause': 'fallout zone or irradiated waste', 'contagious': False, 'stages': ['EXPOSED', 'SICK', 'SEVERE', 'RECOVERED or DEAD'], 'visuals': 'same _Sick skin tint + status_sick bubble + radiation_glow under the person'}

for name, obj in (('culture_rules', culture), ('army_roster', army), ('world_rules', world), ('life_and_powers', life), ('feature_backlog', backlog)):
    json.dump(obj, open(os.path.join(OUT, name + '.json'), 'w'), indent=1)
    print('wrote', name)
