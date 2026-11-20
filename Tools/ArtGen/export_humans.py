"""Phase 2 export: action + death sprites for every people species (human/elf/orc/dwarf), civilians and soldiers."""
import os
import numpy as np
from xcore import Atlas
import humans as HU

OUT = None
DONE = None
CW, CH, X0, Y0 = 46, 46, 9, 5
PIV = (X0 + 13, Y0 + 31)

CHILD_ACTIONS = ['blinded', 'idle', 'walk', 'run', 'hurt', 'cheer', 'eat', 'sleep', 'flee', 'cower', 'sick', 'possessed', 'grabbed', 'swim', 'burning', 'carry', 'gather', 'talk']
SOLDIERS = {   # type: look additions, attack action, era
    'club': (dict(outfit='tribal', weapon='club', helmet='feather'), 'melee', 'stone'),
    'sling': (dict(outfit='tribal', weapon='sling', helmet='band'), 'throw', 'stone'),
    'spearman': (dict(outfit='tribal', weapon='spear', shield='wood', helmet='leather'), 'stab', 'bronze'),
    'hoplite': (dict(outfit='medieval', weapon='spear', shield='iron', helmet='iron', armor=True), 'stab', 'bronze'),
    'archer': (dict(outfit='medieval', weapon='bow', helmet='leather'), 'shoot_bow', 'iron'),
    'swordsman': (dict(outfit='medieval', weapon='sword', shield='wood', helmet='iron'), 'melee', 'iron'),
    'knight': (dict(outfit='medieval', weapon='sword', shield='iron', helmet='iron', armor=True), 'melee', 'medieval'),
    'xbow': (dict(outfit='medieval', weapon='xbow', helmet='iron'), 'shoot_bow', 'medieval'),
    'musket': (dict(outfit='medieval', weapon='musket', helmet='tricorn'), 'shoot_gun', 'gunpowder'),
    'rifle': (dict(outfit='modern', weapon='rifle', helmet='steel', vest=True), 'shoot_gun', 'industrial'),
    'flame': (dict(outfit='modern', weapon='flamer', helmet='steel', vest=True), 'shoot_gun', 'modern'),
    'laser': (dict(outfit='modern', weapon='laser', helmet='visor', vest=True), 'shoot_gun', 'future'),
    'battlemage': (dict(outfit='medieval', weapon='staff', helmet='band'), 'cast', 'magic'),
}
DEATH_FPS = 8


def _add_set(at, base, look, actions, regions, tags, deaths=None):
    for ac in actions:
        nf = HU.ACTIONS[ac]
        keys = []
        for f in range(nf):
            key = f'{base}_{ac}_{f}'
            g = {}
            def fn(a, ctx, ac=ac, f=f):
                r = HU.act(a, X0, Y0, look, ac, f, ctx)
                if r: g.update(r)
            import xcore
            probe = np.zeros((CH, CW, 3), np.uint8); r0 = HU.act(probe, X0, Y0, look, ac, f, xcore.Ctx()) or {}
            an = {k: r0[k] for k in ('head', 'hand') if k in r0}
            at.add(key, fn, CW, CH, PIV, regions=regions, tags=dict(tags, action=ac, frame=f), anchors=an)
            keys.append(key)
        ev = {'chop': [(2, 'hit_resource'), (2, 'sfx:chop')], 'mine': [(2, 'hit_resource'), (2, 'sfx:mine')], 'farm': [(2, 'work_tick')], 'build': [(2, 'work_tick'), (2, 'sfx:hammer')],
              'melee': [(2, 'hit'), (1, 'sfx:swing')], 'stab': [(2, 'hit')], 'throw': [(2, 'spawn_projectile')], 'shoot_bow': [(2, 'spawn_projectile'), (2, 'sfx:bow')],
              'shoot_gun': [(1, 'spawn_projectile'), (1, 'sfx:shot')], 'cast': [(2, 'spawn_spell'), (0, 'sfx:cast')], 'walk': [(0, 'step'), (2, 'step')], 'run': [(0, 'step'), (2, 'step')],
              'cheer': [(0, 'sfx:cheer')], 'hurt': [(0, 'sfx:hurt')], 'flee': [(0, 'sfx:scream')], 'grabbed': [(0, 'sfx:scream')]}.get(ac, [])
        loop = ac not in ('hurt', 'melee', 'stab', 'throw', 'shoot_bow', 'shoot_gun', 'cast', 'block', 'tame')
        at.anim(f'{base}_{ac}', keys, {'run': 10, 'flee': 11, 'burning': 11, 'idle': 3, 'sleep': 2, 'shoot_gun': 10, 'melee': 10}.get(ac, 7), loop, ev)
    for kind, nf in (deaths or HU.DEATHS).items():
        keys = []
        for f in range(nf):
            key = f'{base}_death_{kind}_{f}'
            at.add(key, lambda a, ctx, kind=kind, f=f: HU.death(a, X0, Y0, look, kind, f, ctx), CW, CH, PIV, regions=regions, tags=dict(tags, death=kind, frame=f))
            keys.append(key)
        at.anim(f'{base}_death_{kind}', keys, DEATH_FPS, False, [(0, f'sfx:death_{kind}'), (nf - 1, 'corpse')])


def ex_humans():
    at = Atlas('people_actions', os.path.join(OUT, 'Characters', 'People'))
    reg = ('ACC', 'ACC2', 'SKIN', 'HAIR')
    for sp in HU.SPECIES:
        for g in 'mf':
            for outfit in HU.OUTFITS:
                look = dict(species=sp, gender=g, outfit=outfit)
                _add_set(at, f'h_{sp}_{g}_{outfit}', look, list(HU.ACTIONS), reg, {'species': sp, 'gender': g, 'outfit': outfit, 'age': 'adult'})
            look = dict(species=sp, gender=g, outfit='medieval', child=True)
            _add_set(at, f'h_{sp}_{g}_child', look, CHILD_ACTIONS, reg, {'species': sp, 'gender': g, 'outfit': 'medieval', 'age': 'child'}, deaths=HU.CHILD_DEATHS)
    DONE('people_actions', at)


def ex_soldiers():
    at = Atlas('soldiers_actions', os.path.join(OUT, 'Units', 'Soldiers'))
    reg = ('TEAM', 'SKIN', 'HAIR')
    for sp in HU.SPECIES:
        for st, (lk, atk, era) in SOLDIERS.items():
            look = dict(species=sp, gender='m', soldier=True, **lk)
            acts = ['idle', 'walk', 'run', 'hurt', 'cheer', 'flee', 'cower', 'knocked', 'blinded', 'burning', atk] + (['block'] if lk.get('shield') else []) + (['ride'] if st in ('knight', 'archer', 'musket') else [])
            _add_set(at, f'sol_{sp}_{st}', look, acts, reg, {'species': sp, 'soldier': st, 'era': era, 'attack': atk})
    DONE('soldiers_actions', at)


CATS = {'humans': ex_humans, 'soldiers': ex_soldiers}
