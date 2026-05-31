import pygame as pg
from pygame import gfxdraw
import constants as c
from games.pirate_dominion.save_load import has_save
from renderer import _ensure_gradient
import renderer

_MENU_CACHE = {}

def _ensure_menu():
    if _MENU_CACHE:
        return
    hud = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_HUD)
    inst = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_INSTRUCTIONS)
    _MENU_CACHE['hud'] = hud
    _MENU_CACHE['inst'] = inst

    _MENU_CACHE['subtitle'] = inst.render(
        "Sail the Caribbean \u2014 buy islands, build empires!", True, c.GRAY)
    lines = [
        "W/S navigate  \u2022  Left/Right adjust  \u2022  SPACE / Enter start",
        "",
        "Claim Caribbean islands and charge rival merchants tribute!",
        "Last merchant with doubloons wins.",
    ]
    _MENU_CACHE['info_lines'] = [inst.render(l, True, c.GRAY) for l in lines]
    _MENU_CACHE['hint'] = inst.render(
        "W/S navigate  \u2022  Left/Right adjust  \u2022  SPACE / Enter confirm", True, c.GRAY)

    # Pre-render ship silhouette for background
    ship = pg.Surface((800, 600), pg.SRCALPHA)
    hull_pts = [(360, 420), (440, 420), (460, 380), (340, 380)]
    gfxdraw.filled_polygon(ship, hull_pts, (40, 30, 20, 60))
    gfxdraw.aapolygon(ship, hull_pts, (60, 50, 40, 80))
    # Mast
    pg.draw.line(ship, (40, 30, 20, 60), (400, 380), (400, 150), 3)
    # Sails
    sail_pts = [(400, 150), (460, 300), (400, 350)]
    gfxdraw.filled_polygon(ship, sail_pts, (200, 190, 170, 40))
    gfxdraw.aapolygon(ship, sail_pts, (220, 210, 190, 60))
    sail2_pts = [(400, 150), (340, 300), (400, 350)]
    gfxdraw.filled_polygon(ship, sail2_pts, (180, 170, 150, 40))
    gfxdraw.aapolygon(ship, sail2_pts, (200, 190, 170, 60))
    # Flag
    flag_pts = [(400, 150), (440, 130), (400, 145)]
    gfxdraw.filled_polygon(ship, flag_pts, (100, 40, 40, 60))
    _MENU_CACHE['ship'] = ship

    # Title glow (pre-render with shadow layers)
    title_font = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_TITLE)
    _MENU_CACHE['title_font'] = title_font
    _MENU_CACHE['title'] = title_font.render("PORT ROYALE TYCOON", True, c.GOLD)
    _MENU_CACHE['title_shadow1'] = title_font.render("PORT ROYALE TYCOON", True, (50, 40, 0))
    _MENU_CACHE['title_shadow2'] = title_font.render("PORT ROYALE TYCOON", True, (30, 20, 0))


class Menu:
    def __init__(self):
        _ensure_menu()
        self.title_font = _MENU_CACHE['title_font']
        self.hud_font = _MENU_CACHE['hud']
        self.inst_font = _MENU_CACHE['inst']
        self.player_count = 2
        self.ai_difficulties = ['medium'] * 3
        self.selection = 0
        self.menu_items = 5

    def draw(self, surface):
        _ensure_gradient()
        surface.blit(renderer._DARK_GRADIENT, (0, 0))

        ship = _MENU_CACHE['ship']
        surface.blit(ship, (c.WINDOW_WIDTH // 2 - ship.get_width() // 2,
                            c.WINDOW_HEIGHT // 2 - ship.get_height() // 2 + 40))

        title = _MENU_CACHE['title']
        sh1 = _MENU_CACHE['title_shadow1']
        sh2 = _MENU_CACHE['title_shadow2']
        tx = c.WINDOW_WIDTH // 2 - title.get_width() // 2
        surface.blit(sh2, (tx + 4, 64))
        surface.blit(sh1, (tx + 2, 62))
        surface.blit(title, (tx, 60))

        surface.blit(_MENU_CACHE['subtitle'],
                     (c.WINDOW_WIDTH // 2 - _MENU_CACHE['subtitle'].get_width() // 2, 140))

        y = 220
        for surf in _MENU_CACHE['info_lines']:
            surface.blit(surf, (c.WINDOW_WIDTH // 2 - surf.get_width() // 2, y))
            y += 28

        items = self._get_items()

        # Scroll panel
        panel_w = 440
        item_count = len(items)
        panel_h = item_count * 52 + 30
        panel_x = c.WINDOW_WIDTH // 2 - panel_w // 2
        panel_y = 330

        panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        r = 14
        gfxdraw.filled_circle(panel, r, r, r, (25, 22, 30, 200))
        gfxdraw.filled_circle(panel, panel_w - r - 1, r, r, (25, 22, 30, 200))
        gfxdraw.filled_circle(panel, r, panel_h - r - 1, r, (25, 22, 30, 200))
        gfxdraw.filled_circle(panel, panel_w - r - 1, panel_h - r - 1, r, (25, 22, 30, 200))
        pg.draw.rect(panel, (25, 22, 30, 200), (r, 0, panel_w - 2 * r, panel_h))
        pg.draw.rect(panel, (25, 22, 30, 200), (0, r, panel_w, panel_h - 2 * r))
        gfxdraw.aacircle(panel, r, r, r, (60, 50, 40, 200))
        gfxdraw.aacircle(panel, panel_w - r - 1, r, r, (60, 50, 40, 200))
        gfxdraw.aacircle(panel, r, panel_h - r - 1, r, (60, 50, 40, 200))
        gfxdraw.aacircle(panel, panel_w - r - 1, panel_h - r - 1, r, (60, 50, 40, 200))
        pg.draw.line(panel, (60, 50, 40, 200), (r, 0), (panel_w - r - 1, 0))
        pg.draw.line(panel, (60, 50, 40, 200), (r, panel_h - 1), (panel_w - r - 1, panel_h - 1))
        pg.draw.line(panel, (60, 50, 40, 200), (0, r), (0, panel_h - r - 1))
        pg.draw.line(panel, (60, 50, 40, 200), (panel_w - 1, r), (panel_w - 1, panel_h - r - 1))
        surface.blit(panel, (panel_x, panel_y))

        pg.draw.rect(surface, c.PANEL_ACCENT, (panel_x + 10, panel_y + 8, panel_w - 20, 3))

        y = panel_y + 18
        for i, (label, value) in enumerate(items):
            is_sel = (i == self.selection)
            color = c.GOLD if is_sel else c.WHITE
            prefix = "\u25b8 " if is_sel else "  "
            text = self.hud_font.render(f"{prefix}{label}  {value}", True, color)
            surface.blit(text, (c.WINDOW_WIDTH // 2 - text.get_width() // 2, y))
            y += 52

        surface.blit(_MENU_CACHE['hint'],
                     (c.WINDOW_WIDTH // 2 - _MENU_CACHE['hint'].get_width() // 2,
                      c.WINDOW_HEIGHT - 60))

    def _get_items(self):
        items = []
        items.append(("Players", f"{self.player_count}"))
        labels = ["First Mate", "Gunner", "Quartermaster"]
        diff_map = {'easy': 'GREENHORN', 'medium': 'CAPTAIN', 'hard': 'ADMIRAL'}
        for i in range(self.player_count - 1):
            diff = diff_map.get(self.ai_difficulties[i], self.ai_difficulties[i].upper())
            items.append((labels[i], f"AI ({diff})"))
        items.append(("START", ""))
        if has_save():
            items.append(("LOAD GAME", ""))
        items.append(("BACK", ""))
        return items

    def handle_key(self, key):
        items = self._get_items()
        count = len(items)
        if key in (pg.K_w, pg.K_UP):
            self.selection = (self.selection - 1) % count
            return None
        if key in (pg.K_s, pg.K_DOWN):
            self.selection = (self.selection + 1) % count
            return None

        if key in (pg.K_LEFT, pg.K_RIGHT):
            self._adjust(key)
            return None

        if key in (pg.K_SPACE, pg.K_RETURN):
            label = items[self.selection][0]
            if label == "START":
                return ('start', self.player_count, self.ai_difficulties)
            if label == "LOAD GAME":
                return ('load',)
            if label == "BACK":
                return 'back'

        return None

    def _adjust(self, key):
        delta = -1 if key == pg.K_LEFT else 1
        if self.selection == 0:
            self.player_count = max(2, min(4, self.player_count + delta))
            count = len(self._get_items())
            if self.selection >= count:
                self.selection = count - 1
        elif 1 <= self.selection <= self.player_count - 1:
            idx = self.selection - 1
            diffs = c.PD_AI_DIFFICULTIES
            cur = diffs.index(self.ai_difficulties[idx]) if self.ai_difficulties[idx] in diffs else 1
            self.ai_difficulties[idx] = diffs[(cur + delta) % len(diffs)]
