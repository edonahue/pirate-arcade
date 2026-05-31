import pygame as pg
import constants as c
import random
from games.pirate_dominion.board import spawn_particles, trigger_purchase_flash, trigger_shake, get_space_center

PHASE_ROLL = 0
PHASE_RESOLVE = 1
PHASE_BUY = 2
PHASE_UPGRADE = 3
PHASE_CARD = 4
PHASE_PAY_TAX = 5
PHASE_PAY_RENT = 6
PHASE_END_TURN = 7
PHASE_GAME_OVER = 8
PHASE_ANNOUNCE = 9
PHASE_MORTGAGE = 10
PHASE_UNMORTGAGE = 11
PHASE_AUCTION = 12

class Gameplay:
    def __init__(self, players, properties, audio):
        self.players = players
        self.properties = properties
        self.audio = audio
        self.hud_font = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_HUD)
        self.inst_font = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_INSTRUCTIONS)
        self.phase = PHASE_ROLL
        self.current_idx = 0
        self.dice = (0, 0)
        self.doubles_count = 0
        self.message = ""
        self.message_timer = 0.0
        self.announce_timer = 0.0
        self.current_card = None
        self.last_card_text = ""
        self.last_card_timer = 0.0
        self.turn_count = 0
        self.winner = None
        self.mortgaged = [False] * len(c.PD_PROPERTIES)
        self.property_levels = [0] * len(c.PD_PROPERTIES)
        self.shuffled_chance = []
        self.shuffled_chest = []
        self._mortgage_list = []
        self._mortgage_cursor = 0
        self._mortgage_prop_idx = 0
        self._unmortgage_list = []
        self._unmortgage_cursor = 0
        self._unmortgage_prop_idx = 0
        self._auction_prop_idx = 0
        self._auction_bidder_idx = 0
        self._auction_start_idx = 0
        self._init_decks()

    def _init_decks(self):
        self.shuffled_chance = list(range(len(c.PD_CHANCE_CARDS)))
        self.shuffled_chest = list(range(len(c.PD_CHEST_CARDS)))
        random.shuffle(self.shuffled_chance)
        random.shuffle(self.shuffled_chest)
        self.chance_ptr = 0
        self.chest_ptr = 0

    def _next_chance(self):
        card = self.shuffled_chance[self.chance_ptr]
        self.chance_ptr = (self.chance_ptr + 1) % len(self.shuffled_chance)
        return card

    def _next_chest(self):
        card = self.shuffled_chest[self.chest_ptr]
        self.chest_ptr = (self.chest_ptr + 1) % len(self.shuffled_chest)
        return card

    @property
    def current_player(self):
        return self.players[self.current_idx]

    def start_game(self):
        self.current_idx = 0
        self.phase = PHASE_ROLL
        self.turn_count = 0
        self._set_message(f"{self.current_player.name}, roll the Dice!")

    def _set_message(self, msg):
        self.message = msg
        self.message_timer = 3.0

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt
        if self.last_card_timer > 0:
            self.last_card_timer -= dt
        if self.phase == PHASE_ROLL and self.current_player.is_ai:
            self._roll_dice()
            self._complete_ai_turn()
        if self.phase == PHASE_ANNOUNCE:
            self.announce_timer -= dt
            if self.announce_timer <= 0:
                self.phase = PHASE_END_TURN
        if self.phase == PHASE_END_TURN:
            self._next_player()

    def handle_key(self, key):
        if self.phase == PHASE_ROLL:
            if key in (pg.K_SPACE, pg.K_RETURN):
                self._roll_dice()
            elif key == pg.K_m and not self.current_player.in_jail:
                self._start_manual_mortgage()
            elif key == pg.K_u and not self.current_player.in_jail:
                self._start_manual_unmortgage()
            elif key == pg.K_5 and self.current_player.in_jail:
                self._pay_jail_fine()
            elif key == pg.K_c and self.current_player.in_jail:
                self._use_jail_card()
            return True
        if self.phase == PHASE_BUY:
            return self._handle_buy(key)
        if self.phase == PHASE_UPGRADE:
            return self._handle_upgrade(key)
        if self.phase == PHASE_CARD:
            if key in (pg.K_SPACE, pg.K_RETURN):
                self._resolve_card()
            return True
        if self.phase == PHASE_PAY_TAX:
            if key in (pg.K_SPACE, pg.K_RETURN):
                self._resolve_tax()
            return True
        if self.phase == PHASE_PAY_RENT:
            if key in (pg.K_SPACE, pg.K_RETURN):
                self._resolve_rent()
            return True
        if self.phase == PHASE_MORTGAGE:
            if key == pg.K_y:
                self._confirm_mortgage()
            elif key == pg.K_n:
                self._next_mortgage()
            return True
        if self.phase == PHASE_UNMORTGAGE:
            if key == pg.K_y:
                self._confirm_unmortgage()
            elif key == pg.K_n:
                self._next_unmortgage()
            return True
        if self.phase == PHASE_AUCTION:
            if key == pg.K_y:
                self._accept_auction()
            elif key == pg.K_n:
                self._next_auction_bidder()
            return True
        if self.phase == PHASE_END_TURN:
            return True
        return False

    def _roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.dice = (d1, d2)
        self.audio.play('dice_roll')
        player = self.current_player
        if player.in_jail:
            self._handle_jail_roll(d1, d2, player)
            return
        total = d1 + d2
        if d1 == d2:
            self.doubles_count += 1
            if self.doubles_count >= 3:
                self._go_to_jail(player)
                return
        else:
            self.doubles_count = 0
        old_pos = player.position
        player.position = (player.position + total) % c.PD_BOARD_SIZE
        if player.position < old_pos and player.position != 0:
            self._collect_pass_go(player)
        self._resolve_space()

    def _resolve_space(self):
        player = self.current_player
        space = c.PD_BOARD[player.position]
        stype = space[0]
        if stype == 0:
            self._set_message(f"{player.name} passes START — collect {c.PD_PASS_GO} doubloons!")
            player.money += c.PD_PASS_GO
            cx, cy = get_space_center(player.position)
            spawn_particles(cx, cy, 10, c.GOLD, spread=100, speed=80)
            self.audio.play('coin_jingle')
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
        elif stype == 1:
            prop_idx = space[1]
            owner = self.properties[prop_idx]
            if owner is None:
                self.phase = PHASE_BUY
                self._buy_prop_idx = prop_idx
                name = c.PD_PROPERTIES[prop_idx][0]
                cost = c.PD_PROPERTIES[prop_idx][2]
                self._set_message(f"{name} — ${cost}. Purchase? (Y/N)")
            elif owner == player:
                self._check_upgrade(prop_idx)
            else:
                self._pay_rent_to(owner, prop_idx)
        elif stype == 2:
            self.phase = PHASE_CARD
            card_idx = self._next_chance()
            self.current_card = ('chance', card_idx)
            self._set_message("Merchant's Charter! Draw a card.")
        elif stype == 3:
            self.phase = PHASE_CARD
            card_idx = self._next_chest()
            self.current_card = ('chest', card_idx)
            self._set_message("Admiralty Orders! Draw a card.")
        elif stype == 4:
            self.phase = PHASE_PAY_TAX
            self._set_message(f"Port Authority! Pay {c.PD_TAX_AMOUNT} doubloons in port fees.")
            trigger_shake(6, 0.3)
            cx, cy = get_space_center(player.position)
            spawn_particles(cx, cy, 8, (255, 100, 80), spread=80, speed=60)
        elif stype == 5:
            self._set_message(f"{player.name} is visiting Davey Jones' Locker.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
        elif stype == 6:
            self._set_message(f"{player.name} rests at Shipwreck Cove.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
        elif stype == 7:
            self._go_to_jail(player)
            trigger_shake(10, 0.4)

    def _handle_buy(self, key):
        if key == pg.K_y:
            prop_idx = self._buy_prop_idx
            name, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
            player = self.current_player
            if player.money >= cost:
                player.money -= cost
                self.properties[prop_idx] = player
                player.properties.append(prop_idx)
                self.audio.play('coin_jingle')
                trigger_purchase_flash(prop_idx, 0.4)
                cx, cy = get_space_center(player.position)
                spawn_particles(cx, cy, 12, c.GOLD, spread=120, speed=80)
                self._set_message(f"{player.name} buys {name} for ${cost}")
                self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            else:
                self._set_message(f"Not enough doubloons! {name} costs ${cost}")
                self._start_auction(prop_idx)
        elif key == pg.K_n:
            self._start_auction(self._buy_prop_idx)
        return True

    def _handle_upgrade(self, key):
        if key == pg.K_y:
            self._upgrade_property()
        elif key == pg.K_n:
            pass
        self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
        return True

    def _check_upgrade(self, prop_idx):
        player = self.current_player
        name, group, _, _, upgrade_cost = c.PD_PROPERTIES[prop_idx]
        group_props = [i for i in range(len(c.PD_PROPERTIES))
                       if c.PD_PROPERTIES[i][1] == group]
        owns_all = all(self.properties[i] == player for i in group_props)
        if not owns_all:
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        if self.property_levels[prop_idx] >= c.PD_MAX_UPGRADES:
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        min_level = min(self.property_levels[i] for i in group_props)
        if self.property_levels[prop_idx] > min_level:
            self._set_message("Build evenly! Other properties in group need upgrades first.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        self._upgrade_prop_idx = prop_idx
        self.phase = PHASE_UPGRADE
        level = self.property_levels[prop_idx]
        self._set_message(f"Upgrade {name} to level {level + 1}? (${upgrade_cost}) (Y/N)")

    def _upgrade_property(self):
        player = self.current_player
        prop_idx = self._upgrade_prop_idx
        _, _, _, _, upgrade_cost = c.PD_PROPERTIES[prop_idx]
        if player.money < upgrade_cost:
            self._set_message("Not enough doubloons!")
            return
        self.property_levels[prop_idx] += 1
        player.money -= upgrade_cost
        self.audio.play('coin_jingle')
        trigger_purchase_flash(prop_idx, 0.5)
        cx, cy = get_space_center(player.position)
        spawn_particles(cx, cy, 10, c.GOLD, spread=120, speed=90)
        name = c.PD_PROPERTIES[prop_idx][0]
        self._set_message(f"{name} upgraded to level {self.property_levels[prop_idx]}!")

    def _pay_rent_to(self, owner, prop_idx):
        _player = self.current_player
        if self.mortgaged[prop_idx]:
            self._set_message(f"{c.PD_PROPERTIES[prop_idx][0]} is mortgaged — no tribute due.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        name, group, _, rent_base, _ = c.PD_PROPERTIES[prop_idx]
        level = self.property_levels[prop_idx]
        rent = rent_base * c.PD_RENT_MULTIPLIERS[level]
        if level == 0:
            group_props = [i for i in range(len(c.PD_PROPERTIES))
                           if c.PD_PROPERTIES[i][1] == group]
            owns_all = all(self.properties[i] == owner for i in group_props)
            if owns_all:
                rent *= c.PD_FULL_GROUP_BONUS
        rent = max(rent, 1)
        self._rent_amount = rent
        self._rent_owner = owner
        self._rent_prop_idx = prop_idx
        self.phase = PHASE_PAY_RENT
        self._set_message(f"Pay ${rent} tribute to {owner.name} for {name} (SPACE)")

    def _resolve_rent(self):
        player = self.current_player
        owner = self._rent_owner
        amount = self._rent_amount
        if player.money < amount and player.is_ai:
            self._auto_mortgage_target(player, amount)
        player.money -= amount
        owner.money += amount
        self.audio.play('coin_jingle')
        cx, cy = get_space_center(player.position)
        spawn_particles(cx, cy, 6, (255, 100, 80), spread=80, speed=50)
        ox, oy = get_space_center(owner.position)
        spawn_particles(ox, oy, 6, c.GOLD, spread=80, speed=60)
        if amount >= 100:
            trigger_shake(5, 0.25)
        self._set_message(f"{player.name} pays ${amount} to {owner.name}")
        if player.money < 0:
            self._check_bankruptcy(player)
        if not player.bankrupt:
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN

    def _resolve_tax(self):
        player = self.current_player
        amount = c.PD_TAX_AMOUNT
        if player.money < amount and player.is_ai:
            self._auto_mortgage_target(player, amount)
        player.money -= amount
        self.audio.play('coin_jingle')
        cx, cy = get_space_center(player.position)
        spawn_particles(cx, cy, 6, (255, 180, 100), spread=80, speed=50)
        self._set_message(f"{player.name} pays {amount} doubloons in port fees")
        if player.money < 0:
            self._check_bankruptcy(player)
        if not player.bankrupt:
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN

    def _resolve_card(self):
        deck, card_idx = self.current_card
        player = self.current_player
        if deck == 'chance':
            text = c.PD_CHANCE_CARDS[card_idx]
        else:
            text = c.PD_CHEST_CARDS[card_idx]
        self._set_message(text)
        self.last_card_text = text
        self.last_card_timer = 10.0
        if "Get Out of Jail Free" in text:
            player.jail_free_cards[deck] = True
            self.audio.play('card_shuffle')
            self.current_card = None
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        if "Go to Davey Jones' Locker" in text:
            self._go_to_jail(player)
            self.current_card = None
            return
        amount = self._parse_card_amount(text)
        if text.startswith("Advance to START"):
            player.position = 0
        elif text.startswith("Advance 5 spaces"):
            old_pos = player.position
            player.position = (player.position + 5) % c.PD_BOARD_SIZE
            if player.position < old_pos:
                player.money += c.PD_PASS_GO
            self._resolve_space()
            if self.phase != PHASE_CARD:
                self.current_card = None
            if self.phase == PHASE_ROLL:
                if self.doubles_count == 0:
                    self.phase = PHASE_END_TURN
            return
        elif text.startswith("Rough seas"):
            player.skip_turns = 1
        elif "lose a turn" in text.lower():
            player.skip_turns = 1
        elif text.startswith("Harbor tax"):
            amount = -50 * len([p for p in player.properties])
        player.money += amount
        self.audio.play('card_shuffle')
        if amount > 0:
            cx, cy = get_space_center(player.position)
            spawn_particles(cx, cy, 8, c.GOLD, spread=100, speed=70)
        elif amount < 0:
            cx, cy = get_space_center(player.position)
            spawn_particles(cx, cy, 6, (255, 100, 80), spread=80, speed=50)
        self.current_card = None
        if player.money < 0:
            self._check_bankruptcy(player)
        if not player.bankrupt:
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN

    def _parse_card_amount(self, text):
        import re
        m = re.search(r'(-?\d+)', text)
        if m:
            val = int(m.group(1))
            if "pay" in text.lower() or "lose" in text.lower():
                return -val
            return val
        return 0

    def _go_to_jail(self, player):
        player.position = 9
        player.in_jail = True
        player.jail_attempts = 0
        self.doubles_count = 0
        self._set_message(f"{player.name} goes to Davey Jones' Locker!")
        trigger_shake(8, 0.4)
        cx, cy = get_space_center(player.position)
        spawn_particles(cx, cy, 15, (100, 100, 140), spread=80, speed=60)
        self.phase = PHASE_END_TURN

    def _check_bankruptcy(self, player):
        if player.money < 0:
            self._auto_mortgage(player)
        if player.money < 0:
            player.bankrupt = True
            self._release_properties(player)
            trigger_shake(10, 0.5)
            cx, cy = get_space_center(player.position)
            spawn_particles(cx, cy, 20, (200, 50, 50), spread=150, speed=100)
            self._set_message(f"{player.name} is MAROONED! All properties released.")
            self.audio.play('life_lost')
            self.phase = PHASE_END_TURN

    def _mortgage_value(self, prop_idx):
        _, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        return int(cost * c.PD_MORTGAGE_RATE)

    def _auto_mortgage(self, player):
        while player.money < 0:
            best = self._pick_mortgage(player)
            if best is None:
                break
            self.mortgaged[best] = True
            player.money += self._mortgage_value(best)

    def _auto_mortgage_target(self, player, target):
        needed = target - player.money
        while needed > 0:
            best = self._pick_mortgage(player)
            if best is None:
                break
            self.mortgaged[best] = True
            val = self._mortgage_value(best)
            player.money += val
            needed -= val

    def _pick_mortgage(self, player):
        best = None
        best_val = 0
        for prop_idx in player.properties:
            if self.mortgaged[prop_idx]:
                continue
            val = self._mortgage_value(prop_idx)
            if val > best_val:
                best_val = val
                best = prop_idx
        return best

    def _release_properties(self, player):
        for i in range(len(c.PD_PROPERTIES)):
            if self.properties[i] == player:
                self.properties[i] = None
                self.property_levels[i] = 0
                self.mortgaged[i] = False
        player.properties = []

    def _collect_pass_go(self, player):
        player.money += c.PD_PASS_GO
        cx, cy = get_space_center(player.position)
        spawn_particles(cx, cy, 6, c.GOLD, spread=80, speed=60)
        self.audio.play('coin_jingle')

    def _handle_jail_roll(self, d1, d2, player):
        if d1 == d2:
            player.in_jail = False
            player.jail_attempts = 0
            self.audio.play('coin_jingle')
            self._set_message("Doubles! You escaped from the Locker!")
            total = d1 + d2
            old_pos = player.position
            player.position = (player.position + total) % c.PD_BOARD_SIZE
            if player.position < old_pos and player.position != 0:
                self._collect_pass_go(player)
            self._resolve_space()
            return
        player.jail_attempts += 1
        if player.jail_attempts >= 3:
            self._forced_jail_escape(player, d1, d2)
        else:
            self._set_message(f"No doubles. Attempt {player.jail_attempts}/3.")
            self.phase = PHASE_END_TURN

    def _forced_jail_escape(self, player, d1, d2):
        if player.jail_free_cards['chance'] or player.jail_free_cards['chest']:
            deck = 'chance' if player.jail_free_cards['chance'] else 'chest'
            player.jail_free_cards[deck] = False
            player.in_jail = False
            player.jail_attempts = 0
            self._set_message("Used a Get Out of Jail Free card!")
        elif player.money >= c.PD_JAIL_COST or player.properties:
            if player.money < c.PD_JAIL_COST:
                self._auto_mortgage_target(player, c.PD_JAIL_COST - player.money)
            player.money -= c.PD_JAIL_COST
            player.in_jail = False
            player.jail_attempts = 0
            self._set_message(f"Paid ${c.PD_JAIL_COST} to leave jail.")
        else:
            self._set_message("Can't pay! Stay in Davey Jones' Locker.")
            self.phase = PHASE_END_TURN
            return
        old_pos = player.position
        player.position = (player.position + d1 + d2) % c.PD_BOARD_SIZE
        if player.position < old_pos and player.position != 0:
            self._collect_pass_go(player)
        self._resolve_space()

    def _pay_jail_fine(self):
        player = self.current_player
        if player.money >= c.PD_JAIL_COST:
            player.money -= c.PD_JAIL_COST
            player.in_jail = False
            player.jail_attempts = 0
            self.doubles_count = 0
            self._set_message(f"Paid ${c.PD_JAIL_COST} to leave jail.")
        else:
            self._set_message(f"Only have ${player.money}. Need ${c.PD_JAIL_COST}.")

    def _use_jail_card(self):
        player = self.current_player
        for deck in ('chance', 'chest'):
            if player.jail_free_cards[deck]:
                player.jail_free_cards[deck] = False
                player.in_jail = False
                player.jail_attempts = 0
                self.doubles_count = 0
                self._set_message("Used a Get Out of Jail Free card!")
                return
        self._set_message("No Get Out of Jail Free card!")

    def _start_manual_mortgage(self):
        player = self.current_player
        unmortgaged = [i for i in player.properties if not self.mortgaged[i]]
        if not unmortgaged:
            self._set_message("No properties to mortgage!")
            return
        self._mortgage_list = unmortgaged
        self._mortgage_cursor = 0
        self.phase = PHASE_MORTGAGE
        self._show_mortgage_prompt()

    def _show_mortgage_prompt(self):
        if self._mortgage_cursor >= len(self._mortgage_list):
            self._set_message("No more properties to mortgage.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        prop_idx = self._mortgage_list[self._mortgage_cursor]
        name = c.PD_PROPERTIES[prop_idx][0]
        val = self._mortgage_value(prop_idx)
        self._mortgage_prop_idx = prop_idx
        self._set_message(f"Mortgage {name} for ${val}? (Y/N)")

    def _confirm_mortgage(self):
        player = self.current_player
        prop_idx = self._mortgage_prop_idx
        self.mortgaged[prop_idx] = True
        val = self._mortgage_value(prop_idx)
        player.money += val
        name = c.PD_PROPERTIES[prop_idx][0]
        self.audio.play('coin_jingle')
        self._set_message(f"{name} mortgaged for ${val}")
        self._mortgage_cursor += 1
        self._show_mortgage_prompt()

    def _next_mortgage(self):
        self._mortgage_cursor += 1
        self._show_mortgage_prompt()

    def _start_manual_unmortgage(self):
        player = self.current_player
        mortgaged = [i for i in player.properties if self.mortgaged[i]]
        if not mortgaged:
            self._set_message("No mortgaged properties!")
            return
        self._unmortgage_list = mortgaged
        self._unmortgage_cursor = 0
        self.phase = PHASE_UNMORTGAGE
        self._show_unmortgage_prompt()

    def _show_unmortgage_prompt(self):
        if self._unmortgage_cursor >= len(self._unmortgage_list):
            self._set_message("All processed.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        prop_idx = self._unmortgage_list[self._unmortgage_cursor]
        name, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        val = int(cost * c.PD_UNMORTGAGE_RATE)
        self._unmortgage_prop_idx = prop_idx
        self._set_message(f"Unmortgage {name} for ${val}? (Y/N)")

    def _confirm_unmortgage(self):
        player = self.current_player
        prop_idx = self._unmortgage_prop_idx
        name, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        val = int(cost * c.PD_UNMORTGAGE_RATE)
        if player.money >= val:
            player.money -= val
            self.mortgaged[prop_idx] = False
            self.audio.play('coin_jingle')
            self._set_message(f"{name} unmortgaged for ${val}")
        else:
            self._set_message(f"Not enough! Need ${val}")
        self._unmortgage_cursor += 1
        self._show_unmortgage_prompt()

    def _next_unmortgage(self):
        self._unmortgage_cursor += 1
        self._show_unmortgage_prompt()

    def _start_auction(self, prop_idx):
        self._auction_prop_idx = prop_idx
        self._auction_bidder_idx = (self.current_idx + 1) % len(self.players)
        while self.players[self._auction_bidder_idx].bankrupt or self._auction_bidder_idx == self.current_idx:
            self._auction_bidder_idx = (self._auction_bidder_idx + 1) % len(self.players)
            if self._auction_bidder_idx == self.current_idx:
                self._set_message("Nobody wants it.")
                self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
                return
        self._auction_start_idx = self._auction_bidder_idx
        self.phase = PHASE_AUCTION
        self._show_auction_prompt()

    def _show_auction_prompt(self):
        name, _, cost, _, _ = c.PD_PROPERTIES[self._auction_prop_idx]
        bidder = self.players[self._auction_bidder_idx]
        self._set_message(f"{bidder.name}: Buy {name} for ${cost}? (Y/N)")

    def _accept_auction(self):
        player = self.players[self._auction_bidder_idx]
        prop_idx = self._auction_prop_idx
        name, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        if player.money >= cost:
            player.money -= cost
            self.properties[prop_idx] = player
            player.properties.append(prop_idx)
            self.audio.play('coin_jingle')
            cx, cy = get_space_center(player.position)
            spawn_particles(cx, cy, 10, c.GOLD, spread=100, speed=70)
            self._set_message(f"{player.name} buys {name} for ${cost}")
        else:
            self._set_message(f"{player.name} can't afford it!")
        self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN

    def _next_auction_bidder(self):
        self._auction_bidder_idx = (self._auction_bidder_idx + 1) % len(self.players)
        while self.players[self._auction_bidder_idx].bankrupt or self._auction_bidder_idx == self.current_idx:
            self._auction_bidder_idx = (self._auction_bidder_idx + 1) % len(self.players)
            if self._auction_bidder_idx == self._auction_start_idx:
                self._set_message("Nobody bought it.")
                self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
                return
        if self._auction_bidder_idx == self._auction_start_idx:
            self._set_message("Nobody bought it.")
            self.phase = PHASE_ROLL if self.doubles_count > 0 else PHASE_END_TURN
            return
        self._show_auction_prompt()

    def _next_player(self):
        alive = [p for p in self.players if not p.bankrupt]
        if len(alive) == 0:
            self.phase = PHASE_GAME_OVER
            self.winner = None
            self._set_message("Game over! All players bankrupt. Press ESC.")
            return
        if len(alive) == 1:
            self.phase = PHASE_GAME_OVER
            self.winner = alive[0]
            self._set_message(f"{self.winner.name} wins! Press ESC.")
            return
        self.turn_count += 1
        self.current_idx = (self.current_idx + 1) % len(self.players)
        while self.players[self.current_idx].bankrupt:
            self.current_idx = (self.current_idx + 1) % len(self.players)
        player = self.current_player
        if player.skip_turns > 0:
            player.skip_turns -= 1
            self._set_message(f"{player.name} skips a turn (rough seas)")
            self.phase = PHASE_END_TURN
            return
        self.phase = PHASE_ROLL
        if player.in_jail:
            self._set_message(f"{player.name} is in the Locker — roll, $50, or C for card")
        elif player.is_ai:
            self._set_message(f"{player.name}'s turn (AI)")
        else:
            self._set_message(f"{player.name}, roll the Dice! (SPACE)")

    def _complete_ai_turn(self):
        steps = 0
        while steps < 50:
            steps += 1
            if self.phase == PHASE_BUY:
                self._ai_decide_buy()
            elif self.phase == PHASE_UPGRADE:
                self._ai_decide_upgrade()
            elif self.phase == PHASE_CARD:
                self._resolve_card()
            elif self.phase == PHASE_PAY_TAX:
                self._resolve_tax()
            elif self.phase == PHASE_PAY_RENT:
                self._resolve_rent()
            elif self.phase == PHASE_AUCTION:
                self._ai_decide_auction()
            elif self.phase == PHASE_ROLL:
                if self.doubles_count > 0:
                    break
                p = self.current_player
                if p.in_jail and p.jail_attempts >= 2:
                    self._pay_jail_fine()
                    self._roll_dice()
                else:
                    break
            else:
                break

    def _ai_decide_buy(self):
        player = self.current_player
        prop_idx = self._buy_prop_idx
        _, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        if player.difficulty == 'easy':
            if player.money - cost > 500:
                self._handle_buy(pg.K_y)
            else:
                self._handle_buy(pg.K_n)
        elif player.difficulty == 'medium':
            if player.money - cost > 300:
                self._handle_buy(pg.K_y)
            else:
                self._handle_buy(pg.K_n)
        else:
            if player.money >= cost:
                self._handle_buy(pg.K_y)
            else:
                self._handle_buy(pg.K_n)

    def _ai_decide_upgrade(self):
        player = self.current_player
        prop_idx = self._upgrade_prop_idx
        _, _, _, _, upgrade_cost = c.PD_PROPERTIES[prop_idx]
        if player.difficulty == 'hard':
            if player.money >= upgrade_cost * 2:
                self._upgrade_property()
                self.phase = PHASE_END_TURN
                return
        elif player.difficulty == 'medium':
            if player.money >= upgrade_cost * 3:
                self._upgrade_property()
                self.phase = PHASE_END_TURN
                return
        self.phase = PHASE_END_TURN

    def _ai_decide_auction(self):
        player = self.players[self._auction_bidder_idx]
        prop_idx = self._auction_prop_idx
        _, _, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        if player.difficulty == 'hard':
            if player.money >= cost:
                self._accept_auction()
                return
        elif player.difficulty == 'medium':
            if player.money - cost > 200:
                self._accept_auction()
                return
        else:  # easy
            if player.money - cost > 300:
                self._accept_auction()
                return
        self._next_auction_bidder()

    def get_message(self):
        return self.message

    def get_dice_display(self):
        if self.dice == (0, 0):
            return ""
        return f"{self.dice[0]} + {self.dice[1]}"
