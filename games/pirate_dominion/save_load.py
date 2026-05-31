import json
import os
from datetime import datetime

_SAVE_DIR = os.path.join(os.path.expanduser("~/.local/share/pirate-arcade"), "saves")
_SAVE_FILE = os.path.join(_SAVE_DIR, "pirate_dominion.json")
SAVE_VERSION = 2


def _save_path():
    return _SAVE_FILE


def _ensure_dir():
    os.makedirs(_SAVE_DIR, exist_ok=True)


def has_save():
    return os.path.isfile(_save_path())


def delete_save():
    path = _save_path()
    if os.path.isfile(path):
        os.remove(path)


def save_game(players, properties, gameplay):
    _ensure_dir()
    data = {
        'version': SAVE_VERSION,
        'timestamp': datetime.now().isoformat(),
        'players': [
            {
                'idx': p.idx,
                'money': p.money,
                'position': p.position,
                'properties': p.properties[:],
                'bankrupt': p.bankrupt,
                'in_jail': p.in_jail,
                'jail_attempts': p.jail_attempts,
                'skip_turns': p.skip_turns,
                'jail_free_cards': dict(p.jail_free_cards),
            }
            for p in players
        ],
        'properties': [p.idx if p is not None else None for p in properties],
        'gameplay': {
            'phase': gameplay.phase,
            'current_idx': gameplay.current_idx,
            'dice': list(gameplay.dice) if gameplay.dice else [0, 0],
            'doubles_count': gameplay.doubles_count,
            'turn_count': gameplay.turn_count,
            'mortgaged': list(gameplay.mortgaged),
            'property_levels': list(gameplay.property_levels),
            'shuffled_chance': list(gameplay.shuffled_chance),
            'shuffled_chest': list(gameplay.shuffled_chest),
            'chance_ptr': gameplay.chance_ptr,
            'chest_ptr': gameplay.chest_ptr,
            'current_card': gameplay.current_card,
        },
    }
    tmp = _save_path() + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f)
    os.replace(tmp, _save_path())


def peek_save():
    path = _save_path()
    if not os.path.isfile(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        ver = data.get('version', 1)
        if ver < 1 or ver > SAVE_VERSION:
            return None
        pdata = data['players']
        return {'player_count': len(pdata)}
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def load_game(players, properties, gameplay):
    path = _save_path()
    if not os.path.isfile(path):
        return False
    with open(path, 'r') as f:
        data = json.load(f)

    ver = data.get('version', 1)
    if ver < 1 or ver > SAVE_VERSION:
        return False

    pdata = data['players']
    if len(pdata) != len(players):
        return False

    for p, pd in zip(players, pdata):
        p.money = pd['money']
        p.position = pd['position']
        p.properties = pd['properties'][:]
        p.bankrupt = pd['bankrupt']
        p.in_jail = pd.get('in_jail', False)
        p.jail_attempts = pd.get('jail_attempts', 0)
        p.skip_turns = pd['skip_turns']
        p.jail_free_cards = pd.get('jail_free_cards', {'chance': False, 'chest': False})

    for i, owner_idx in enumerate(data['properties']):
        properties[i] = players[owner_idx] if owner_idx is not None else None

    gd = data['gameplay']
    gameplay.phase = gd['phase']
    gameplay.current_idx = gd['current_idx']
    gameplay.dice = tuple(gd['dice'])
    gameplay.doubles_count = gd['doubles_count']
    gameplay.turn_count = gd['turn_count']
    gameplay.mortgaged = gd['mortgaged'][:]
    gameplay.property_levels = gd['property_levels'][:]
    gameplay.shuffled_chance = gd['shuffled_chance'][:]
    gameplay.shuffled_chest = gd['shuffled_chest'][:]
    gameplay.chance_ptr = gd['chance_ptr']
    gameplay.chest_ptr = gd['chest_ptr']
    gameplay.current_card = gd.get('current_card')
    return True
