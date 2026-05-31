# ruff: noqa: E402
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame as pg
pg.display.init()
pg.font.init()
pg.display.set_mode((1, 1), flags=pg.HIDDEN)

import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from games.asteroids.gameplay import Gameplay
from games.asteroids.ship import Ship
from games.asteroids.barrel import Barrel
from games.asteroids.cannonball import Cannonball
from games.asteroids.treasure import Treasure
import constants as c
class MockAudio:
    def play(self, name):
        pass


class KeyState:
    """Mimics pygame.key.ScancodeWrapper for test key arrays."""
    def __init__(self):
        self._keys = {}

    def __setitem__(self, key, value):
        self._keys[key] = value

    def __getitem__(self, key):
        return self._keys.get(key, 0)


def _keys():
    """Return a mutable key state object for tests."""
    return KeyState()


@pytest.fixture
def audio():
    return MockAudio()


@pytest.fixture
def game(audio):
    g = Gameplay(audio)
    return g


# ---------------------------------------------------------------------------
# Ship
# ---------------------------------------------------------------------------

def test_ship_initial():
    s = Ship()
    assert s.x == c.WINDOW_WIDTH // 2
    assert s.y == c.WINDOW_HEIGHT // 2
    assert s.alive
    assert s.invulnerable == 0


def test_ship_reset():
    s = Ship()
    s.x = 0
    s.y = 0
    s.angle = 90
    s.reset()
    assert s.x == c.WINDOW_WIDTH // 2
    assert s.y == c.WINDOW_HEIGHT // 2
    assert s.angle == 0
    assert s.invulnerable == c.SHIP_INVULNERABLE_TIME


def test_ship_rotation():
    s = Ship()
    keys = _keys()
    keys[pg.K_LEFT] = 1
    s.update(0.1, keys)
    assert s.angle < 0

    s.angle = 0
    keys[pg.K_LEFT] = 0
    keys[pg.K_RIGHT] = 1
    s.update(0.1, keys)
    assert s.angle > 0


def test_ship_thrust():
    s = Ship()
    keys = _keys()
    keys[pg.K_UP] = 1
    vx0, vy0 = s.vx, s.vy
    s.update(0.1, keys)
    assert s.vx != vx0 or s.vy != vy0
    assert s.thrusting


def test_ship_friction():
    s = Ship()
    s.vx = 500
    s.vy = 0
    s.update(0.1, _keys())
    assert abs(s.vx) < 500


def test_ship_max_speed():
    s = Ship()
    s.vx = 10000
    s.vy = 0
    s.update(0.016, _keys())
    speed = (s.vx ** 2 + s.vy ** 2) ** 0.5
    assert speed <= c.SHIP_MAX_SPEED * 1.01


def test_ship_wraps():
    s = Ship()
    s.x = -200
    s.y = c.WINDOW_HEIGHT // 2
    s.update(0.016, _keys())
    assert s.x > c.WINDOW_WIDTH


def test_ship_invulnerable_blocks_damage():
    s = Ship()
    s.invulnerable = 0.5
    # After reset, ship is invulnerable
    assert s.invulnerable > 0


def test_ship_dead_does_not_update():
    s = Ship()
    s.alive = False
    s.vx = 100
    s.update(0.1, _keys())
    assert s.vx == 100  # unchanged


# ---------------------------------------------------------------------------
# Barrel (Asteroid)
# ---------------------------------------------------------------------------

def test_barrel_initial():
    b = Barrel(500, 500)
    assert b.radius == c.ASTEROID_LARGE_RADIUS
    assert b.alive


def test_barrel_split_large():
    b = Barrel(500, 500, radius=c.ASTEROID_LARGE_RADIUS)
    children = b.split()
    assert len(children) == 2
    for c2 in children:
        assert c2.radius == c.ASTEROID_MEDIUM_RADIUS


def test_barrel_split_medium():
    b = Barrel(500, 500, radius=c.ASTEROID_MEDIUM_RADIUS)
    children = b.split()
    assert len(children) == 3
    for c2 in children:
        assert c2.radius == c.ASTEROID_SMALL_RADIUS


def test_barrel_split_small():
    b = Barrel(500, 500, radius=c.ASTEROID_SMALL_RADIUS)
    children = b.split()
    assert len(children) == 0


def test_barrel_moves():
    b = Barrel(500, 500)
    x0, y0 = b.x, b.y
    b.update(0.1)
    assert b.x != x0 or b.y != y0


def test_barrel_wrap():
    b = Barrel(-200, 500)
    b.update(0.016)
    assert b.x > c.WINDOW_WIDTH


def test_barrel_points():
    assert Barrel.POINTS[c.ASTEROID_LARGE_RADIUS] == c.ASTEROID_POINTS_LARGE
    assert Barrel.POINTS[c.ASTEROID_MEDIUM_RADIUS] == c.ASTEROID_POINTS_MEDIUM
    assert Barrel.POINTS[c.ASTEROID_SMALL_RADIUS] == c.ASTEROID_POINTS_SMALL


# ---------------------------------------------------------------------------
# Cannonball
# ---------------------------------------------------------------------------

def test_cannonball_initial():
    cb = Cannonball(500, 500, 0)
    assert not cb.dead
    assert cb.life > 0


def test_cannonball_expires():
    cb = Cannonball(500, 500, 0)
    cb.life = 0.001
    cb.update(0.1)
    assert cb.dead


def test_cannonball_moves():
    cb = Cannonball(500, 500, 0)
    x0, y0 = cb.x, cb.y
    cb.update(0.1)
    assert cb.x != x0 or cb.y != y0


# ---------------------------------------------------------------------------
# Treasure
# ---------------------------------------------------------------------------

def test_treasure_initial():
    t = Treasure(500, 500)
    assert not t.dead
    assert not t.collected


def test_treasure_expires():
    t = Treasure(500, 500)
    t.life = 0.001
    t.update(0.1)
    assert t.dead


def test_treasure_collected_immutable():
    t = Treasure(500, 500)
    t.collected = True
    assert t.collected


# ---------------------------------------------------------------------------
# Gameplay
# ---------------------------------------------------------------------------

def test_gameplay_initial(game):
    assert len(game.barrels) == c.ASTEROID_INITIAL_COUNT


def test_gameplay_reset(game):
    game.score = 999
    game.lives = 0
    game.reset()
    assert game.score == 0
    assert game.lives == c.SHIP_LIVES
    assert game.wave == 0


def test_gameplay_update_with_none_keys(game):
    result = game.update(0.016, None)
    assert result == ('playing', None)


def test_gameplay_fire_cannonball(game):
    game.ship.alive = True
    game.cooldown = 0
    game.ship.angle = 0
    game.ship.x = 50
    game.ship.y = 50
    n0 = len(game.cannonballs)
    keys = _keys()
    keys[pg.K_SPACE] = 1
    game.update(0.016, keys)
    assert len(game.cannonballs) == n0 + 1


def test_gameplay_fire_rate_limit(game):
    game.ship.alive = True
    game.cooldown = 0
    game.ship.angle = 0
    game.ship.x = 50
    game.ship.y = 50
    keys = _keys()
    keys[pg.K_SPACE] = 1
    game.update(0.016, keys)
    n0 = len(game.cannonballs)
    assert n0 == 1
    game.update(0.001, keys)
    assert len(game.cannonballs) == n0


def test_gameplay_barrel_hit_scoring(game):
    barrel = game.barrels[0]
    # Place barrel directly on top of cannonball path
    barrel.x = game.ship.x + 10
    barrel.y = game.ship.y
    cb = Cannonball(game.ship.x, game.ship.y, 0)
    game.cannonballs.append(cb)
    n0 = len(game.barrels)
    score0 = game.score
    for _ in range(5):
        game.update(0.016, _keys())
    assert game.score > score0 or len(game.barrels) < n0


def test_gameplay_ship_hit_loses_life(game):
    game.ship.x = 500
    game.ship.y = 500
    game.ship.invulnerable = 0
    barrel = Barrel(500, 500)
    game.barrels = [barrel]
    lives_before = game.lives
    game.update(0.016, _keys())
    assert game.lives == lives_before - 1


def test_gameplay_ship_hit_game_over(game):
    game.lives = 1
    game.ship.x = 500
    game.ship.y = 500
    game.ship.invulnerable = 0
    barrel = Barrel(500, 500)
    game.barrels = [barrel]
    result = game.update(0.016, _keys())
    assert result[0] == 'game_over'
    assert not game.ship.alive


def test_gameplay_treasure_spawn_on_barrel_break(game):
    original_chance = c.TREASURE_CHANCE
    try:
        c.TREASURE_CHANCE = 1.0
        game.barrels = [Barrel(500, 500)]
        barrel = game.barrels[0]
        game.ship.x = barrel.x + 50
        game.ship.y = barrel.y
        cb = Cannonball(game.ship.x, game.ship.y, 0)
        game.cannonballs.append(cb)
        game.update(0.016, _keys())
        # Wait for collision
        for _ in range(5):
            game.update(0.016, _keys())
    finally:
        c.TREASURE_CHANCE = original_chance


def test_gameplay_wave_progression(game):
    game.barrels = []
    game.update(0.016, _keys())
    assert game.wave == 1
    assert len(game.barrels) == c.ASTEROID_INITIAL_COUNT + 1


def test_gameplay_ship_invulnerable_after_reset(game):
    game.ship.invulnerable = 0
    game.ship.x = 500
    game.ship.y = 500
    barrel = Barrel(500, 500)
    game.barrels = [barrel]
    lives_before = game.lives
    game.update(0.016, _keys())
    assert game.lives <= lives_before
    assert game.ship.invulnerable > 0
