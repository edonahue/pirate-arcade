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

from games.breakout.gameplay import Gameplay
from games.breakout.paddle import Paddle
from games.breakout.ball import Ball
from games.breakout.brick import Brick
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
# Paddle
# ---------------------------------------------------------------------------

def test_paddle_initial():
    p = Paddle()
    assert p.x == c.WINDOW_WIDTH // 2
    assert p.y == c.WINDOW_HEIGHT - c.PADDLE_BREAKOUT_MARGIN


def test_paddle_move_left():
    p = Paddle()
    p.vx = -c.PADDLE_BREAKOUT_SPEED
    x0 = p.x
    p.update(0.1)
    assert p.x < x0


def test_paddle_move_right():
    p = Paddle()
    p.vx = c.PADDLE_BREAKOUT_SPEED
    x0 = p.x
    p.update(0.1)
    assert p.x > x0


def test_paddle_clamp_left():
    p = Paddle()
    p.x = 0
    p.vx = -c.PADDLE_BREAKOUT_SPEED
    p.update(0.1)
    assert p.x >= p.width // 2


def test_paddle_clamp_right():
    p = Paddle()
    p.x = c.WINDOW_WIDTH
    p.vx = c.PADDLE_BREAKOUT_SPEED
    p.update(0.1)
    assert p.x <= c.WINDOW_WIDTH - p.width // 2


# ---------------------------------------------------------------------------
# Ball
# ---------------------------------------------------------------------------

def test_ball_initial():
    b = Ball()
    assert not b.launched
    assert b.vx == 0
    assert b.vy == 0


def test_ball_stick_to_paddle():
    p = Paddle()
    b = Ball()
    b.stick_to_paddle(p)
    assert b.x == p.x
    assert b.y == p.y - p.height // 2 - b.radius


def test_ball_launch():
    b = Ball()
    b.launch()
    assert b.launched
    assert b.vy < 0  # must go up


def test_ball_launch_idempotent():
    b = Ball()
    b.launch()
    vx0, vy0 = b.vx, b.vy
    b.launch()
    assert b.vx == vx0 and b.vy == vy0


def test_ball_update_only_when_launched():
    b = Ball()
    b.x = 500
    b.update(0.1)
    assert b.x == 500


def test_ball_reset_clears_launched():
    b = Ball()
    b.launch()
    b.reset()
    assert not b.launched
    assert b.vx == 0


def test_ball_bump_speed():
    b = Ball()
    s0 = b.speed
    b.bump_speed()
    assert b.speed > s0


# ---------------------------------------------------------------------------
# Brick
# ---------------------------------------------------------------------------

def test_brick_initial_alive():
    b = Brick(0, 0)
    assert b.alive


def test_brick_hit_destroys():
    b = Brick(0, 0)
    b.hit()
    assert not b.alive


def test_brick_points_increase_with_row():
    b0 = Brick(0, 0)
    b7 = Brick(0, 7)
    assert b7.points > b0.points
    assert b7.points == (7 + 1) * c.BRICK_POINTS_BASE


def test_brick_rect():
    b = Brick(0, 0)
    r = b.rect
    assert r.width == c.BRICK_WIDTH
    assert r.height == c.BRICK_HEIGHT
    assert r.x == c.BRICK_LEFT
    assert r.y == c.BRICK_MARGIN_TOP


# ---------------------------------------------------------------------------
# Gameplay
# ---------------------------------------------------------------------------

def test_gameplay_initial_bricks(game):
    assert len(game.bricks) == c.BRICK_ROWS * c.BRICK_COLS
    assert game.remaining_bricks == len(game.bricks)


def test_gameplay_reset(game):
    game.score = 500
    game.lives = 1
    game.reset()
    assert game.score == 0
    assert game.lives == c.PLAYER_LIVES
    assert game.remaining_bricks == c.BRICK_ROWS * c.BRICK_COLS


def test_gameplay_ball_out_loses_life(game):
    game.ball.launch()
    game.ball.y = c.WINDOW_HEIGHT + game.ball.radius + 10
    lives_before = game.lives
    game.update(0.016, _keys())
    assert game.lives == lives_before - 1


def test_gameplay_ball_out_game_over(game):
    game.lives = 1
    game.ball.launch()
    game.ball.y = c.WINDOW_HEIGHT + game.ball.radius + 10
    result = game.update(0.016, _keys())
    assert result[0] == 'game_over'
    assert result[1] == 'lost'


def test_gameplay_win(game):
    game.ball.launch()
    for b in game.bricks:
        b.health = 0
    game.remaining_bricks = 0
    result = game.update(0.016, _keys())
    assert result[0] == 'game_over'
    assert result[1] == 'won'


def test_gameplay_wall_bounce_top(game):
    game.ball.launch()
    game.ball.y = game.ball.radius
    game.ball.vy = -100
    game.update(0.016, _keys())
    assert game.ball.vy > 0


def test_gameplay_wall_bounce_left(game):
    game.ball.launch()
    game.ball.x = game.ball.radius
    game.ball.vx = -100
    game.update(0.016, _keys())
    assert game.ball.vx > 0


def test_gameplay_wall_bounce_right(game):
    game.ball.launch()
    game.ball.x = c.WINDOW_WIDTH - game.ball.radius
    game.ball.vx = 100
    game.update(0.016, _keys())
    assert game.ball.vx < 0


def test_gameplay_paddle_bounce(game):
    game.ball.launch()
    game.paddle.x = c.WINDOW_WIDTH // 2
    game.paddle.y = c.WINDOW_HEIGHT - c.PADDLE_BREAKOUT_MARGIN
    # Offset ball from paddle center so angle produces non-zero vy
    game.ball.x = game.paddle.x + 20
    game.ball.y = game.paddle.y - game.paddle.height // 2 - game.ball.radius
    game.ball.vx = 0
    game.ball.vy = 100
    game.update(0.016, _keys())
    assert game.ball.vy < 0


def test_gameplay_brick_collision(game):
    game.ball.launch()
    brick = game.bricks[0]
    game.ball.x = brick.x + brick.width // 2
    game.ball.y = brick.y
    game.ball.vy = 100
    game.ball.vx = 0
    n0 = game.remaining_bricks
    game.update(0.016, _keys())
    assert game.remaining_bricks <= n0


def test_gameplay_ball_sticks_before_launch(game):
    game.ball.launched = False
    game.paddle.x = 500
    game.update(0.016, _keys())
    assert game.ball.x == game.paddle.x


def test_gameplay_update_with_none_keys(game):
    result = game.update(0.016, None)
    assert result == ('playing', None)
