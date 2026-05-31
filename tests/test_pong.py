import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame as pg
pg.display.init()
pg.font.init()
pg.display.set_mode((1, 1), flags=pg.HIDDEN)

import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from games.pong.gameplay import Gameplay
from games.pong.paddle import Paddle
from games.pong.ball import Ball
from games.pong.powerup import PowerUp
from games.pong.ai import AI
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
# Ball
# ---------------------------------------------------------------------------

def test_ball_reset():
    b = Ball()
    assert b.x == c.WINDOW_WIDTH // 2
    assert b.y == c.WINDOW_HEIGHT // 2
    assert abs((b.vx ** 2 + b.vy ** 2) ** 0.5 - c.BALL_SPEED_INITIAL) < 1


def test_ball_update_moves():
    b = Ball()
    x0, y0 = b.x, b.y
    b.update(0.1)
    assert b.x != x0 or b.y != y0


def test_ball_bump_speed():
    b = Ball()
    s0 = b.speed
    b.bump_speed()
    assert b.speed > s0


def test_ball_max_speed_clamp():
    b = Ball()
    for _ in range(20):
        b.bump_speed()
    assert b.speed <= c.BALL_MAX_SPEED


# ---------------------------------------------------------------------------
# Paddle
# ---------------------------------------------------------------------------

def test_paddle_initial():
    p = Paddle(c.PADDLE_MARGIN, c.WINDOW_HEIGHT // 2)
    assert p.x == c.PADDLE_MARGIN
    assert p.y == c.WINDOW_HEIGHT // 2


def test_paddle_move():
    p = Paddle(c.PADDLE_MARGIN, c.WINDOW_HEIGHT // 2)
    p.vy = c.PADDLE_SPEED
    p.update(0.1)
    assert p.y > c.WINDOW_HEIGHT // 2


def test_paddle_clamp_top():
    p = Paddle(c.PADDLE_MARGIN, 0)
    p.vy = -c.PADDLE_SPEED
    p.update(0.1)
    assert p.y >= p.height // 2


def test_paddle_clamp_bottom():
    p = Paddle(c.PADDLE_MARGIN, c.WINDOW_HEIGHT)
    p.vy = c.PADDLE_SPEED
    p.update(0.1)
    assert p.y <= c.WINDOW_HEIGHT - p.height // 2


def test_paddle_big_activation():
    p = Paddle(c.PADDLE_MARGIN, c.WINDOW_HEIGHT // 2)
    h0 = p.height
    p.activate_big()
    assert p.height > h0
    assert p.is_big


def test_paddle_big_expires():
    p = Paddle(c.PADDLE_MARGIN, c.WINDOW_HEIGHT // 2)
    p.activate_big()
    p.update(c.PADDLE_BIG_DURATION + 0.1)
    assert not p.is_big
    assert p.height == p.base_height


# ---------------------------------------------------------------------------
# PowerUp
# ---------------------------------------------------------------------------

def test_powerup_spawn():
    pu = PowerUp()
    assert pu.timer > 0
    assert not pu.expired


def test_powerup_expires():
    pu = PowerUp()
    pu.timer = 0.001
    pu.update(0.1)
    assert pu.expired


def test_powerup_bounces():
    pu = PowerUp()
    pu.y = c.POWERUP_SIZE // 2
    pu.vy = -100
    pu.update(0.1)
    assert pu.vy > 0


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------

def test_ai_set_difficulty():
    ai = AI()
    ai.set_difficulty('easy')
    assert ai.speed_factor == c.AI_DIFFICULTIES['easy']['speed_factor']

    ai.set_difficulty('hard')
    assert ai.speed_factor == c.AI_DIFFICULTIES['hard']['speed_factor']


def test_ai_moves_toward_ball():
    ai = AI('medium')
    paddle = Paddle(c.WINDOW_WIDTH - c.PADDLE_MARGIN, 100)
    ball = Ball()
    ball.y = 500
    paddle.vy = 0
    for _ in range(10):
        ai.update(paddle, ball, 0.1)
    assert paddle.vy != 0


# ---------------------------------------------------------------------------
# Gameplay — scoring
# ---------------------------------------------------------------------------

def test_gameplay_reset(game):
    game.reset()
    assert game.player_score == 0
    assert game.ai_score == 0
    assert game.powerup is None


def test_gameplay_ball_out_left_scores_ai(game):
    game.ball.x = -100
    result = game.update(0.016, _keys())
    assert result == ('playing', None)
    assert game.ai_score == 1


def test_gameplay_ball_out_right_scores_player(game):
    game.ball.x = c.WINDOW_WIDTH + 100
    result = game.update(0.016, _keys())
    assert result == ('playing', None)
    assert game.player_score == 1


def test_gameplay_win_condition_player(game):
    game.player_score = 10
    game.ai_score = 9
    game.ball.x = c.WINDOW_WIDTH + 100
    game.update(0.016, _keys())
    # 11-9 meets win-by-2 threshold, result is game_over
    result = game.update(0.016, _keys())
    assert result[0] == 'game_over'
    assert result[1] == 'player'


def test_gameplay_win_condition_ai(game):
    game.ai_score = 10
    game.player_score = 9
    game.ball.x = -100
    game.update(0.016, _keys())
    # 11-9 meets win-by-2 threshold, result is game_over
    result = game.update(0.016, _keys())
    assert result[0] == 'game_over'
    assert result[1] == 'ai'


def test_gameplay_paddle_collision_changes_ball_direction(game):
    game.player_paddle.y = c.WINDOW_HEIGHT // 2
    game.player_paddle.x = c.PADDLE_MARGIN
    game.ball.x = c.PADDLE_MARGIN + c.PADDLE_WIDTH // 2 + c.BALL_SIZE // 2
    game.ball.y = c.WINDOW_HEIGHT // 2
    game.ball.vx = -c.BALL_SPEED_INITIAL
    game.ball.vy = 0
    result = game.update(0.016, _keys())
    # Ball should bounce right
    assert game.ball.vx > 0


def test_gameplay_powerup_spawn(game):
    game.powerup_spawn_timer = 0
    game.update(0.016, _keys())
    assert game.powerup is not None


def test_gameplay_powerup_collected(game):
    game.powerup = PowerUp()
    game.powerup.x = game.player_paddle.x
    game.powerup.y = game.player_paddle.y
    game.update(0.016, _keys())
    assert game.powerup is None
    assert game.player_paddle.is_big


def test_gameplay_reset_round(game):
    game.player_score = 5
    game.ai_score = 3
    game.reset_round()
    assert game.player_score == 5
    assert game.ai_score == 3
    assert game.ball.x == c.WINDOW_WIDTH // 2


def test_gameplay_wall_hit_bounce(game):
    game.ball.y = c.BALL_SIZE // 2
    game.ball.vy = -100
    game.update(0.016, _keys())
    assert game.ball.vy > 0


def test_gameplay_update_with_none_keys(game):
    result = game.update(0.016, None)
    assert result == ('playing', None)


def test_gameplay_set_difficulty(game):
    game.set_difficulty('easy')
    assert game.ai.speed_factor == c.AI_DIFFICULTIES['easy']['speed_factor']

    game.set_difficulty('hard')
    assert game.ai.speed_factor == c.AI_DIFFICULTIES['hard']['speed_factor']


def test_gameplay_ball_trail(game):
    game.ball.trail.clear()
    game.update(0.016, _keys())
    assert len(game.ball.trail) > 0


def test_gameplay_hit_particles_produced(game):
    game.player_paddle.y = c.WINDOW_HEIGHT // 2
    game.player_paddle.x = c.PADDLE_MARGIN
    game.ball.x = c.PADDLE_MARGIN + c.PADDLE_WIDTH // 2 + c.BALL_SIZE // 2
    game.ball.y = c.WINDOW_HEIGHT // 2
    game.ball.vx = -c.BALL_SPEED_INITIAL
    game.ball.vy = 0
    n0 = len(game.hit_particles)
    game.update(0.016, _keys())
    assert len(game.hit_particles) > n0
