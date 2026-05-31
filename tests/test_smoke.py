import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame as pg
pg.display.init()
pg.font.init()
pg.display.set_mode((1, 1), flags=pg.HIDDEN)

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


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


class MockAudio:
    def play(self, name):
        pass


def test_launcher_imports():
    """Launcher module loads without error."""
    from launcher import Launcher
    assert Launcher is not None


def test_pong_game_init():
    """Pong game initializes without error."""
    from games.pong.game import PongGame
    from games.pong.menu import Menu
    from games.pong.gameplay import Gameplay
    surface = pg.Surface((1600, 900))
    audio = MockAudio()
    game = PongGame(surface, audio)
    assert game.state == 'menu'
    assert game.gameplay is not None


def test_breakout_game_init():
    """Breakout game initializes without error."""
    from games.breakout.game import BreakoutGame
    from games.breakout.gameplay import Gameplay
    surface = pg.Surface((1600, 900))
    audio = MockAudio()
    game = BreakoutGame(surface, audio)
    assert game.state == 'menu'


def test_asteroids_game_init():
    """Asteroids game initializes without error."""
    from games.asteroids.game import AsteroidsGame
    from games.asteroids.gameplay import Gameplay
    surface = pg.Surface((1600, 900))
    audio = MockAudio()
    game = AsteroidsGame(surface, audio)
    assert game.state == 'menu'


def test_pirate_dominion_game_init():
    """Pirate Dominion game initializes without error."""
    from games.pirate_dominion.game import PirateDominion
    from games.pirate_dominion.menu import Menu
    surface = pg.Surface((1600, 900))
    audio = MockAudio()
    game = PirateDominion(surface, audio)
    assert game.state == 'menu'


def test_pong_gameplay_runs_few_frames():
    """Pong gameplay.update runs 60 frames without crashing."""
    from games.pong.gameplay import Gameplay
    g = Gameplay(MockAudio())
    for _ in range(60):
        result = g.update(0.016, _keys())
        assert result is not None


def test_breakout_gameplay_runs_few_frames():
    """Breakout gameplay.update runs 60 frames without crashing."""
    from games.breakout.gameplay import Gameplay
    g = Gameplay(MockAudio())
    for _ in range(60):
        result = g.update(0.016, _keys())
        assert result is not None


def test_asteroids_gameplay_runs_few_frames():
    """Asteroids gameplay.update runs 60 frames without crashing."""
    from games.asteroids.gameplay import Gameplay
    g = Gameplay(MockAudio())
    for _ in range(60):
        result = g.update(0.016, _keys())
        assert result is not None


def test_renderer_imports():
    """Renderer module imports without error."""
    import renderer
    assert renderer.draw_center_line is not None
    assert renderer.draw_pause_overlay is not None
    assert renderer.draw_game_over is not None
    assert renderer.HitParticle is not None


def test_constants_complete():
    """All expected constants are defined."""
    import constants as c
    assert c.WINDOW_WIDTH == 1600
    assert c.WINDOW_HEIGHT == 900
    assert c.FPS == 60
    assert c.PIRATE_GOLD is not None
    assert c.PIRATE_NAVY is not None
    assert c.PIRATE_CANNON is not None
    assert c.POWERUP_COLOR == c.PIRATE_TREASURE
    assert c.PAUSE_HIGHLIGHT == c.PIRATE_TREASURE


def test_highscores_import():
    """Highscores module loads without error."""
    import highscores
    assert highscores is not None


def test_audio_import():
    """Audio module loads without error."""
    import audio
    assert audio is not None


def test_util_import():
    """Util module loads without error."""
    import util
    assert util is not None
