import pygame as pg
import constants as c
import highscores as hs
from games.pirate_dominion.menu import Menu
from games.pirate_dominion.player import Player
from games.pirate_dominion.gameplay import Gameplay
from games.pirate_dominion import save_load
from renderer import _VIGNETTE, _ensure_gradient
from util import toggle_fullscreen

class PirateDominion:
    def __init__(self, surface, audio):
        self.surface = surface
        self.audio = audio
        self.menu = Menu()
        self.state = 'menu'
        self.player_count = 2
        self.ai_difficulties = ['medium'] * 3
        self.players = []
        self.properties = [None] * len(c.PD_PROPERTIES)
        self.gameplay = None
        self.winner = None
        self.target_fps = 60
        self.paused = False
        self.pause_selection = 0
        self.showing_props = False
        self._elapsed = 0.0
        self._turn_transition_timer = 0.0
        self._last_turn_idx = 0
        self._init_fonts()

    def _init_fonts(self):
        self.title_font = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_TITLE)
        self.hud_font = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_HUD)
        self.inst_font = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_INSTRUCTIONS)
        self._init_pause_assets()

    def _init_pause_assets(self):
        PAUSE_ITEMS = ["Resume", "Save Game", "View Properties", "Quit to Menu"]
        self._pause_title_surf = self.title_font.render("PAUSED", True, c.GOLD)
        self._pause_items = []
        for item in PAUSE_ITEMS:
            normal = self.hud_font.render(f"   {item}", True, (200, 200, 200))
            selected = self.hud_font.render(f"\u25b8 {item}", True, c.GOLD)
            self._pause_items.append((normal, selected))

    def run(self):
        clock = pg.time.Clock()
        fullscreen = False

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return 'quit'
                if event.type == pg.KEYDOWN and event.key == pg.K_F11:
                    self.surface, fullscreen = toggle_fullscreen(self.surface, fullscreen)
                    pg.display.set_caption("PORT ROYALE TYCOON")
                elif event.type == pg.KEYDOWN:
                    result = self._handle_key(event.key)
                    if result == 'menu':
                        self._auto_save()
                        return 'menu'
                    elif result == 'quit':
                        return 'quit'

            dt = clock.tick(self.target_fps) / 1000.0
            self._dt = dt
            self._update(dt)
            self._draw()
            pg.display.flip()

    def _handle_key(self, key):
        if self.state == 'playing':
            if self.showing_props:
                self.showing_props = False
                return None
            if self.paused:
                if key in (pg.K_w, pg.K_UP):
                    self.pause_selection = (self.pause_selection - 1) % len(self._pause_items)
                elif key in (pg.K_s, pg.K_DOWN):
                    self.pause_selection = (self.pause_selection + 1) % len(self._pause_items)
                elif key in (pg.K_SPACE, pg.K_RETURN):
                    if self.pause_selection == 0:
                        self.paused = False
                    elif self.pause_selection == 1:
                        self._save_game()
                    elif self.pause_selection == 2:
                        self.showing_props = True
                    elif self.pause_selection == 3:
                        return 'menu'
                elif key == pg.K_ESCAPE:
                    self.paused = False
                return None
            if key == pg.K_ESCAPE:
                self.paused = True
                self.pause_selection = 0
            elif key == pg.K_v:
                self.showing_props = True
            elif key == pg.K_F5:
                self._save_game()
            elif key == pg.K_F9:
                self._load_game()
            elif self.gameplay:
                self.gameplay.handle_key(key)
                if self.gameplay.phase == 8:
                    self.state = 'game_over'
                    self.winner = self.gameplay.winner
                    if self.winner:
                        hs.submit_pirate_dominion(
                            self.winner.name, self.winner.net_worth, self.gameplay.turn_count)
        elif self.state == 'menu':
            if key == pg.K_ESCAPE:
                return 'menu'
            result = self.menu.handle_key(key)
            if result:
                if result[0] == 'start':
                    _, self.player_count, self.ai_difficulties = result
                    self._start_game()
                    self.state = 'playing'
                elif result[0] == 'load':
                    if self._load_game_from_menu():
                        self.state = 'playing'
                elif result == 'back':
                    return 'menu'
        elif self.state == 'game_over':
            if key in (pg.K_SPACE, pg.K_RETURN):
                self.state = 'menu'
                return 'menu'
            if key == pg.K_ESCAPE:
                return 'menu'
        return None

    def _start_game(self):
        self.players = []
        self.properties = [None] * len(c.PD_PROPERTIES)
        for i in range(self.player_count):
            is_ai = i > 0
            diff = self.ai_difficulties[i - 1] if is_ai else None
            name = ["Captain", "First Mate", "Gunner", "Quartermaster"][i]
            token = c.PD_PLAYER_TOKENS[i]
            self.players.append(Player(i, name, token, is_ai, diff))
        self.gameplay = Gameplay(self.players, self.properties, self.audio)
        self.gameplay.start_game()
        from games.pirate_dominion.board import reset_animation_state
        reset_animation_state()

    def _auto_save(self):
        if self.state == 'playing' and self.gameplay is not None:
            save_load.save_game(self.players, self.properties, self.gameplay)

    def _save_game(self):
        if self.gameplay is None:
            return
        save_load.save_game(self.players, self.properties, self.gameplay)
        self.gameplay.message = "Game saved! (F9 to load)"
        self.gameplay.message_timer = 2.0

    def _load_game(self):
        if self.gameplay is None:
            return
        ok = save_load.load_game(self.players, self.properties, self.gameplay)
        if ok:
            self.gameplay.message = "Game loaded!"
            self.gameplay.message_timer = 2.0
        else:
            self.gameplay.message = "No save found or incompatible save."
            self.gameplay.message_timer = 3.0

    def _load_game_from_menu(self):
        info = save_load.peek_save()
        if info is None:
            return False
        pc = info['player_count']
        self.player_count = pc
        self.ai_difficulties = ['medium'] * max(0, pc - 1)
        self._start_game()
        ok = save_load.load_game(self.players, self.properties, self.gameplay)
        if not ok:
            self.players = []
            self.properties = [None] * len(c.PD_PROPERTIES)
            self.gameplay = None
            return False
        return True

    def _update(self, dt):
        self._elapsed += dt
        if self._turn_transition_timer > 0:
            self._turn_transition_timer -= dt
        if self.state == 'playing' and self.gameplay:
            if self.paused or self.showing_props:
                return
            cur = self.gameplay.current_idx
            if cur != self._last_turn_idx and self.gameplay.phase == 0:
                self._turn_transition_timer = 0.4
            self._last_turn_idx = cur
            self.gameplay.update(dt)
            if self.gameplay.phase == 8:
                self.state = 'game_over'
                self.winner = self.gameplay.winner
                if self.winner:
                    hs.submit_pirate_dominion(
                        self.winner.name, self.winner.net_worth, self.gameplay.turn_count)

    def _draw(self):
        if self.state == 'menu':
            _ensure_gradient()
            self.menu.draw(self.surface)
            self.surface.blit(_VIGNETTE, (0, 0))
        elif self.state == 'playing':
            self._draw_playing()
            if self.paused:
                self._draw_pause()
            if self.showing_props:
                self._draw_properties_view()
        elif self.state == 'game_over':
            self._draw_game_over()
            self.surface.blit(_VIGNETTE, (0, 0))

    def _draw_playing(self):
        from games.pirate_dominion.board import draw_board
        from games.pirate_dominion.ui import draw_hud
        draw_board(self.surface, self.properties, self.players, self.gameplay.property_levels,
                   dt=self._dt,                    time=self._elapsed,
                   dice=self.gameplay.dice if self.gameplay else (0, 0))
        self.surface.blit(_VIGNETTE, (0, 0))
        draw_hud(self.surface, self.players, self.gameplay, dt=self._dt)
        if self._turn_transition_timer > 0 and self.gameplay:
            self._draw_turn_transition()

    def _draw_turn_transition(self):
        t = self._turn_transition_timer
        dur = 0.4
        midpoint = dur / 2
        if t > midpoint:
            alpha = int(255 * (1 - (t - midpoint) / midpoint))
        else:
            alpha = int(255 * t / midpoint)
        alpha = max(0, min(255, alpha))
        overlay = pg.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.surface.blit(overlay, (0, 0))
        if alpha > 10:
            player = self.gameplay.current_player
            label = f"{player.name}'s Turn"
            color = player.color
            surf = self.title_font.render(label, True, color)
            shadow = self.title_font.render(label, True, (0, 0, 0))
            tx = c.WINDOW_WIDTH // 2 - surf.get_width() // 2
            ty = c.WINDOW_HEIGHT // 2 - surf.get_height() // 2
            self.surface.blit(shadow, (tx + 2, ty + 2))
            self.surface.blit(surf, (tx, ty))

    def _draw_game_over(self):
        from games.pirate_dominion.ui import draw_game_over_screen
        draw_game_over_screen(self.surface, self.players, self.winner, self.gameplay, dt=self._dt)

    def _draw_pause(self):
        overlay = pg.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, c.PANEL_DIM_ALPHA))
        self.surface.blit(overlay, (0, 0))

        panel_w = 400
        item_h = 44
        panel_h = 60 + len(self._pause_items) * item_h + 30
        px = c.WINDOW_WIDTH // 2 - panel_w // 2
        py = c.WINDOW_HEIGHT // 2 - panel_h // 2

        shadow = pg.Surface((panel_w + 8, panel_h + 8), pg.SRCALPHA)
        from renderer import rounded_rect_fill, rounded_rect_outline
        rounded_rect_fill(shadow, (0, 0, 0, 40), (4, 4, panel_w, panel_h), c.PANEL_RADIUS)
        self.surface.blit(shadow, (px - 4, py))

        panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        rounded_rect_fill(panel, c.PANEL_FILL, (0, 0, panel_w, panel_h), c.PANEL_RADIUS)
        rounded_rect_outline(panel, c.PANEL_OUTLINE, (0, 0, panel_w, panel_h), c.PANEL_RADIUS)
        pg.draw.rect(panel, c.PANEL_ACCENT, (10, 8, panel_w - 20, 3))
        self.surface.blit(panel, (px, py))

        tx = c.WINDOW_WIDTH // 2 - self._pause_title_surf.get_width() // 2
        self.surface.blit(self._pause_title_surf, (tx, py + 16))

        y = py + 60
        for i, (normal, selected) in enumerate(self._pause_items):
            surf = selected if i == self.pause_selection else normal
            self.surface.blit(surf, (px + 40, y))
            y += item_h

        hint = self.inst_font.render("W/S navigate  |  SPACE select  |  ESC resume", True, (140, 140, 140))
        hx = c.WINDOW_WIDTH // 2 - hint.get_width() // 2
        self.surface.blit(hint, (hx, py + panel_h - 28))

    def _draw_properties_view(self):
        from games.pirate_dominion.ui import draw_properties_popup
        draw_properties_popup(self.surface, self.players, self.gameplay)
