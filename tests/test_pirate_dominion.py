import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame as pg
pg.display.init()
pg.font.init()
pg.display.set_mode((1, 1), flags=pg.HIDDEN)

import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from games.pirate_dominion.player import Player
from games.pirate_dominion.gameplay import (
    Gameplay, PHASE_ROLL, PHASE_BUY, PHASE_UPGRADE, PHASE_CARD,
    PHASE_PAY_TAX, PHASE_PAY_RENT, PHASE_END_TURN, PHASE_GAME_OVER,
    PHASE_ANNOUNCE,
)
import constants as c


class MockAudio:
    def play(self, name):
        pass


@pytest.fixture
def audio():
    return MockAudio()


@pytest.fixture
def game(audio):
    players = [
        Player(0, "Captain", "Jolly Roger", is_ai=False),
        Player(1, "AI-Easy", "Treasure Chest", is_ai=True, difficulty='easy'),
        Player(2, "AI-Med", "Cannon", is_ai=True, difficulty='medium'),
        Player(3, "AI-Hard", "Anchor", is_ai=True, difficulty='hard'),
    ]
    properties = [None] * len(c.PD_PROPERTIES)
    g = Gameplay(players, properties, audio)
    g.current_idx = 0
    g.phase = PHASE_ROLL
    return g


# ---------------------------------------------------------------------------
# Card amount parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Advance to START — collect 200 doubloons", 200),
    ("Buried treasure! — collect 150 doubloons", 150),
    ("Kraken attack! — pay 100 doubloons for repairs", -100),
    ("Press gang! — pay 50 doubloons to free your crew", -50),
    ("Friendly natives — collect 75 doubloons", 75),
    ("Shipworm damage — pay 120 doubloons", -120),
    ("Stowaway found — collect 50 doubloon reward", 50),
    ("Map to hidden loot — collect 200 doubloons", 200),
    ("Hurricane! — pay 150 doubloons for repairs", -150),
    ("Merchant convoy — collect 100 doubloons", 100),
    ("Inheritance from old salt — collect 200 doubloons", 200),
    ("Port fees — pay 80 doubloons", -80),
    ("Rum shipment sold — collect 120 doubloons", 120),
    ("Ship repairs — pay 150 doubloons", -150),
    ("Treasure map sold — collect 100 doubloons", 100),
    ("Crew's wages — pay 60 doubloons", -60),
    ("Prize ship captured — collect 250 doubloons", 250),
    ("Medical emergency — pay 100 doubloons", -100),
    ("Gold doubloons found — collect 180 doubloons", 180),
    ("Admiral's reward — collect 100 doubloons", 100),
    ("Mutiny quelled — pay 90 doubloons", -90),
    ("Rough seas — lose a turn (next roll skip)", 0),
])
def test_parse_card_amount(game, text, expected):
    assert game._parse_card_amount(text) == expected


# ---------------------------------------------------------------------------
# AI upgrade — all difficulties must advance past PHASE_UPGRADE
# ---------------------------------------------------------------------------

def _setup_monopoly(game, player_idx, group, prop_indices):
    """Give player full ownership of a property group."""
    for i in prop_indices:
        game.properties[i] = game.players[player_idx]
        game.players[player_idx].properties.append(i)


def test_ai_upgrade_easy_advances_phase(game):
    """Easy AI must not hang on PHASE_UPGRADE (regression for 1a)."""
    ai = game.players[1]
    game.current_idx = 1
    game.phase = PHASE_UPGRADE
    game._upgrade_prop_idx = 0
    ai.money = 9999
    _setup_monopoly(game, 1, 0, [0, 1, 2])
    game._ai_decide_upgrade()
    assert game.phase != PHASE_UPGRADE


def test_ai_upgrade_medium_advances_phase(game):
    """Medium AI must not hang on PHASE_UPGRADE."""
    ai = game.players[2]
    game.current_idx = 2
    game.phase = PHASE_UPGRADE
    game._upgrade_prop_idx = 0
    ai.money = 9999
    _setup_monopoly(game, 2, 0, [0, 1, 2])
    game._ai_decide_upgrade()
    assert game.phase != PHASE_UPGRADE


def test_ai_upgrade_hard_advances_phase(game):
    """Hard AI must not hang on PHASE_UPGRADE."""
    ai = game.players[3]
    game.current_idx = 3
    game.phase = PHASE_UPGRADE
    game._upgrade_prop_idx = 0
    ai.money = 9999
    _setup_monopoly(game, 3, 0, [0, 1, 2])
    game._ai_decide_upgrade()
    assert game.phase != PHASE_UPGRADE


def test_ai_upgrade_easy_skipped_when_no_group(game):
    """AI without full group still advances phase."""
    ai = game.players[1]
    game.current_idx = 1
    game.phase = PHASE_UPGRADE
    game._upgrade_prop_idx = 0
    ai.money = 9999
    game._ai_decide_upgrade()
    assert game.phase == PHASE_END_TURN


def test_ai_upgrade_poor_medium_skips_and_advances(game):
    """Medium AI that can't afford upgrade still advances phase."""
    ai = game.players[2]
    game.current_idx = 2
    game.phase = PHASE_UPGRADE
    game._upgrade_prop_idx = 0
    ai.money = 1
    _setup_monopoly(game, 2, 0, [0, 1, 2])
    game._ai_decide_upgrade()
    assert game.phase == PHASE_END_TURN


# ---------------------------------------------------------------------------
# Tortuga card — AI must not hang (regression for 1c/1d)
# ---------------------------------------------------------------------------

def test_tortuga_card_ai_lands_on_unowned_property(game):
    """AI draws Sail to Tortuga, lands on unowned property, must enter and resolve PHASE_BUY."""
    ai = game.players[3]
    game.current_idx = 3
    game.phase = PHASE_CARD
    ai.position = 1  # space 1 = St. Thomas (property index 0), tortuga moves +5 to space 6 = Antigua (property index 3)
    game.current_card = ('chance', 1)  # index 1 = "Sail to Tortuga"
    ai.money = 9999
    game._resolve_card()
    assert ai.position == 6, f"Expected position 6, got {ai.position}"
    assert ai.money == 9999  # no pass-GO bonus, 5 doesn't wrap
    # After Tortuga resolve_space → space 6 is property → PHASE_BUY
    # complete_ai_turn loop should handle it
    game._complete_ai_turn()
    assert game.phase != PHASE_BUY


def test_tortuga_card_ai_lands_on_owned_property(game):
    """AI draws Tortuga, lands on property owned by another player, must pay rent."""
    ai = game.players[3]
    owner = game.players[0]
    game.current_idx = 3
    ai.position = 1
    ai.money = 500
    game.properties[3] = owner  # Antigua owned by Captain
    game.current_card = ('chance', 1)
    game._resolve_card()
    assert ai.position == 6
    game._complete_ai_turn()
    assert game.phase in (PHASE_END_TURN, PHASE_GAME_OVER)


def test_tortuga_card_human_sets_buy_phase(game):
    """Human draws Tortuga, lands on unowned property, phase becomes PHASE_BUY."""
    human = game.players[0]
    game.current_idx = 0
    game.phase = PHASE_CARD
    human.position = 1
    human.money = 9999
    game.current_card = ('chance', 1)
    game._resolve_card()
    assert human.position == 6
    assert game.phase == PHASE_BUY, f"Expected PHASE_BUY, got {game.phase}"
    # Human presses Y to buy
    game._handle_buy(pg.K_y)
    assert game.properties[3] == human
    assert game.phase == PHASE_END_TURN


# ---------------------------------------------------------------------------
# All-players-bankrupt — no crash (regression for 2a)
# ---------------------------------------------------------------------------

def test_all_players_bankrupt_no_crash(game):
    """No IndexError when all players are bankrupt."""
    for p in game.players:
        p.bankrupt = True
    game._next_player()
    assert game.phase == PHASE_GAME_OVER
    assert game.winner is None


def test_last_player_bankrupt_no_crash(game):
    """Last remaining player becomes bankrupt."""
    for p in game.players:
        p.bankrupt = False
    game.players[0].bankrupt = True
    game.players[1].bankrupt = True
    game.players[2].bankrupt = True
    game.current_idx = 3
    game.phase = PHASE_END_TURN
    game.players[3].money = -100
    game._check_bankruptcy(game.players[3])
    game._next_player()
    assert game.phase == PHASE_GAME_OVER


# ---------------------------------------------------------------------------
# Mortgage prompt — picks highest value property (regression for 4b)
# ---------------------------------------------------------------------------

def test_auto_mortgage_selects_highest_value(game):
    """Auto-mortgage must pick the property with the highest cost first."""
    player = game.players[0]
    # St. Thomas costs 60, St. John costs 60, Antigua costs 100
    player.properties = [0, 1, 3]
    game.properties[0] = player
    game.properties[1] = player
    game.properties[3] = player
    game.mortgaged = [False] * len(c.PD_PROPERTIES)
    player.money = -10
    game._auto_mortgage(player)
    # Should have mortgaged property index 3 (Antigua, cost 100, highest value)
    assert game.mortgaged[3], "Expected highest-cost property (Antigua, idx 3) to be mortgaged"
    assert not game.mortgaged[0], "Cheaper property should not be mortgaged"
    assert not game.mortgaged[1], "Cheaper property should not be mortgaged"


def test_auto_mortgage_no_properties(game):
    """No crash when no unmortgaged properties available."""
    player = game.players[0]
    player.properties = []
    player.money = -10
    game._auto_mortgage(player)
    assert player.money == -10


# ---------------------------------------------------------------------------
# Rent calculation
# ---------------------------------------------------------------------------

def _setup_rent_test(game, prop_idx, owner_idx, level=0):
    game.properties[prop_idx] = game.players[owner_idx]
    game.property_levels[prop_idx] = level
    return game.players[owner_idx]


def test_rent_base_level_0(game):
    """Base rent without upgrades."""
    ai = game.players[3]
    game.current_idx = 3
    ai.position = 1
    _setup_rent_test(game, 0, 0)  # St. Thomas, rent base 4
    game._resolve_space()
    assert game.phase == PHASE_PAY_RENT


def test_rent_multiplier_level_1(game):
    """Rent at level 1 (4x multiplier)."""
    owner = game.players[0]
    prop_idx = 0  # St. Thomas, base rent 4
    _setup_rent_test(game, prop_idx, 0, level=1)  # level 1 → 4 * 4 = 16
    game._pay_rent_to(owner, prop_idx)
    assert game._rent_amount == 16


def test_rent_multiplier_level_3(game):
    """Rent at max level (30x multiplier)."""
    owner = game.players[0]
    prop_idx = 0
    _setup_rent_test(game, prop_idx, 0, level=3)  # level 3 → 4 * 30 = 120
    game._pay_rent_to(owner, prop_idx)
    assert game._rent_amount == 120


# ---------------------------------------------------------------------------
# Group monopoly bonus
# ---------------------------------------------------------------------------

def test_group_bonus_applied(game):
    """Full group ownership gives 2x rent at level 0."""
    owner = game.players[0]
    # Virgin Islands group: indices 0, 1, 2
    _setup_rent_test(game, 0, 0)  # St. Thomas
    game.properties[1] = owner
    game.properties[2] = owner
    game._pay_rent_to(owner, 0)
    assert game._rent_amount == 4 * c.PD_FULL_GROUP_BONUS  # 4 * 2 = 8


def test_group_bonus_not_applied_without_monopoly(game):
    """No bonus without full group ownership."""
    owner = game.players[0]
    _setup_rent_test(game, 0, 0)  # St. Thomas
    game.properties[1] = owner
    # Missing property 2
    game._pay_rent_to(owner, 0)
    assert game._rent_amount == 4  # base rent, no bonus


# ---------------------------------------------------------------------------
# Doubles → jail
# ---------------------------------------------------------------------------

def test_three_doubles_sends_to_jail(game):
    """Three consecutive doubles sends player to jail."""
    player = game.players[0]
    game.current_idx = 0
    game.doubles_count = 3
    game._go_to_jail(player)
    assert player.position == 9
    assert player.in_jail
    assert player.jail_attempts == 0


# ---------------------------------------------------------------------------
# Jail escape mechanics
# ---------------------------------------------------------------------------

def test_jail_escape_via_doubles(game):
    """Rolling doubles in jail sets in_jail=False."""
    player = game.players[0]
    player.in_jail = True
    player.jail_attempts = 2  # 3rd attempt would force pay, but we hit doubles
    game.current_idx = 0
    # override random to produce doubles (3,3)
    import random
    old_randint = random.randint
    random.randint = lambda a, b: 3
    try:
        game._roll_dice()
    finally:
        random.randint = old_randint
    assert not player.in_jail
    assert player.jail_attempts == 0


def test_jail_escape_via_pay(game):
    """Paying $50 sets in_jail=False and resets attempts."""
    player = game.players[0]
    player.in_jail = True
    player.jail_attempts = 2
    player.money = 500
    game._pay_jail_fine()
    assert not player.in_jail
    assert player.jail_attempts == 0
    assert player.money == 450


def test_jail_escape_via_card(game):
    """Using a Get Out of Jail Free card sets in_jail=False."""
    player = game.players[0]
    player.in_jail = True
    player.jail_attempts = 2
    player.jail_free_cards['chance'] = True
    game._use_jail_card()
    assert not player.in_jail
    assert player.jail_attempts == 0
    assert not player.jail_free_cards['chance']  # card consumed


def test_jail_player_can_roll(game):
    """Player in jail gets PHASE_ROLL instead of having turns skipped."""
    jailed = game.players[1]
    jailed.in_jail = True
    game.current_idx = 0  # _next_player will advance to 1
    game.phase = PHASE_END_TURN
    game._next_player()
    assert game.phase == PHASE_ROLL  # NOT PHASE_END_TURN (old skip behavior)


# ---------------------------------------------------------------------------
# Bankruptcy edge cases
# ---------------------------------------------------------------------------

def test_bankruptcy_at_exactly_zero(game):
    """Player with exactly 0 money does not go bankrupt."""
    player = game.players[0]
    player.money = 0
    game._check_bankruptcy(player)
    assert not player.bankrupt


def test_bankruptcy_after_mortgage_saves(game):
    """Auto-mortgage can save player from bankruptcy."""
    player = game.players[0]
    player.money = -10
    player.properties = [0]
    game.properties[0] = player
    game._check_bankruptcy(player)
    assert not player.bankrupt
    assert player.money >= 0


def test_bankruptcy_with_no_properties(game):
    """Player with debt and no properties goes bankrupt."""
    player = game.players[0]
    player.money = -10
    player.properties = []
    game._check_bankruptcy(player)
    assert player.bankrupt


# ---------------------------------------------------------------------------
# Upgrade limits
# ---------------------------------------------------------------------------

def test_max_upgrades_blocked(game):
    """Property at max upgrades does not offer further upgrade."""
    player = game.players[0]
    game.current_idx = 0
    game.properties[0] = player
    game.property_levels[0] = c.PD_MAX_UPGRADES
    _setup_monopoly(game, 0, 0, [0, 1, 2])
    game._check_upgrade(0)
    assert game.phase != PHASE_UPGRADE, "Should not enter upgrade phase at max level"


# ---------------------------------------------------------------------------
# _complete_ai_turn loop — regression for 1c/1d
# ---------------------------------------------------------------------------

def test_complete_ai_turn_loop_handles_cascade(game):
    """complete_ai_turn must handle cascading phase changes from cards."""
    ai = game.players[3]
    game.current_idx = 3
    ai.position = 1
    ai.money = 9999
    # Land on Tortuga (+5) → Antigua (unowned property)
    game.phase = PHASE_CARD
    game.current_card = ('chance', 1)
    game._complete_ai_turn()
    assert game.phase != PHASE_CARD, "Should not be stuck on PHASE_CARD"
    assert game.phase != PHASE_BUY, "Should not be stuck on PHASE_BUY"


def test_complete_ai_turn_handles_tax(game):
    """AI resolves tax space."""
    ai = game.players[3]
    game.current_idx = 3
    ai.position = 4  # Cannon Cove (tax)
    ai.money = 9999
    game.phase = PHASE_PAY_TAX
    game._complete_ai_turn()
    assert game.phase not in (PHASE_PAY_TAX,), "Tax should be resolved"


def test_complete_ai_turn_handles_rent(game):
    """AI resolves rent payment."""
    ai = game.players[3]
    owner = game.players[0]
    game.current_idx = 3
    ai.money = 500
    game._rent_amount = 50
    game._rent_owner = owner
    game._rent_prop_idx = 0
    game.phase = PHASE_PAY_RENT
    game._complete_ai_turn()
    assert game.phase != PHASE_PAY_RENT, "Rent should be resolved"


# ---------------------------------------------------------------------------
# Long-running playthrough stability
# ---------------------------------------------------------------------------

def test_doubles_count_reset_on_jail(game):
    """doubles_count must reset when player goes to jail (prevents infinite jail loop)."""
    player = game.players[0]
    game.doubles_count = 3
    game._go_to_jail(player)
    assert game.doubles_count == 0
    assert player.position == 9
    assert player.in_jail


def test_full_ai_game_simulation(audio):
    """Run a complete AI-vs-AI game to verify no crashes or stuck phases."""
    players = [
        Player(0, "AI-1", "Jolly Roger", is_ai=True, difficulty='easy'),
        Player(1, "AI-2", "Treasure Chest", is_ai=True, difficulty='medium'),
        Player(2, "AI-3", "Cannon", is_ai=True, difficulty='hard'),
    ]
    properties = [None] * len(c.PD_PROPERTIES)
    g = Gameplay(players, properties, audio)
    g.start_game()

    for _ in range(5000):
        g.update(0.1)
        if g.phase == PHASE_GAME_OVER:
            alive = [p for p in g.players if not p.bankrupt]
            assert len(alive) <= 1
            assert g.winner is None or g.winner in alive
            return
    # If not finished, verify game is still making progress (phase changes)
    # rather than stuck in an infinite loop.
    # Players in jail may stay in PHASE_ROLL for multiple rolls (doubles escape)
    # so we check progress across multiple updates.
    prev_phase = g.phase
    prev_idx = g.current_idx
    for _ in range(100):
        g.update(0.1)
        if g.phase != prev_phase or g.current_idx != prev_idx:
            break
    else:
        assert False, \
            "Game is stuck — phase and current player unchanged after 100 updates"


@pytest.fixture
def save_cleanup():
    yield
    from games.pirate_dominion import save_load
    save_load.delete_save()


def test_save_load_round_trip(game, save_cleanup):
    """Save game state, mutate everything, load back, verify all fields match."""
    from games.pirate_dominion import save_load

    game.players[0].money = 250
    game.players[0].position = 7
    game.players[0].properties = [0, 3]
    game.properties[0] = game.players[0]
    game.properties[3] = game.players[0]
    game.players[1].money = 100
    game.players[1].position = 14
    game.players[1].bankrupt = True
    game.doubles_count = 1
    game.phase = PHASE_END_TURN
    game.current_idx = 2
    game.turn_count = 12
    game.mortgaged[0] = True
    game.property_levels[3] = 2

    save_load.save_game(game.players, game.properties, game)

    game.players[0].money = 0
    game.players[0].position = 0
    game.players[0].properties = []
    game.properties[0] = None
    game.properties[3] = None
    game.players[1].bankrupt = False
    game.doubles_count = 0
    game.phase = PHASE_ROLL
    game.current_idx = 0
    game.turn_count = 0
    game.mortgaged[0] = False
    game.property_levels[3] = 0

    ok = save_load.load_game(game.players, game.properties, game)
    assert ok, "load_game returned False"

    assert game.players[0].money == 250
    assert game.players[0].position == 7
    assert game.players[0].properties == [0, 3]
    assert game.properties[0] == game.players[0]
    assert game.properties[3] == game.players[0]
    assert game.players[1].money == 100
    assert game.players[1].position == 14
    assert game.players[1].bankrupt
    assert game.doubles_count == 1
    assert game.phase == PHASE_END_TURN
    assert game.current_idx == 2
    assert game.turn_count == 12
    assert game.mortgaged[0]
    assert game.property_levels[3] == 2


def test_save_load_bankruptcy_state(game, save_cleanup):
    """Bankrupt player state persists through save/load cycle."""
    from games.pirate_dominion import save_load

    game.players[1].money = -50
    game.players[1].properties = []
    game._check_bankruptcy(game.players[1])
    assert game.players[1].bankrupt

    save_load.save_game(game.players, game.properties, game)

    game.players[1].bankrupt = False
    game.players[1].money = 500

    ok = save_load.load_game(game.players, game.properties, game)
    assert ok
    assert game.players[1].bankrupt, "Bankrupt state not restored"
    assert game.players[1].money == -50
    assert game.players[1].properties == []


def test_animation_state_reset():
    """reset_animation_state clears all module-level animation state."""
    from games.pirate_dominion import board
    board._PREV_POS[0] = 5
    board._ANIM_POS[0] = (100, 100)
    board._ANIM_PROGRESS[0] = 0.5

    board.reset_animation_state()

    assert len(board._PREV_POS) == 0
    assert len(board._ANIM_POS) == 0
    assert len(board._ANIM_PROGRESS) == 0


def test_auto_mortgage_cascade(game):
    """Auto-mortgage mortgages multiple properties when single insufficient."""
    player = game.players[0]
    player.properties = [0, 1, 2]
    for i in [0, 1, 2]:
        game.properties[i] = player
    game.mortgaged = [False] * len(c.PD_PROPERTIES)
    player.money = -70

    game._auto_mortgage(player)

    mortgaged = [i for i in [0, 1, 2] if game.mortgaged[i]]
    assert len(mortgaged) >= 2
    assert player.money >= 0 or player.bankrupt
