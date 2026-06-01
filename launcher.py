import pygame as pg
import constants as c
import math
import highscores as hs
import renderer as rd
from util import toggle_fullscreen

GAMES = [
    {
        'id': 'pong',
        'title': 'CANNONBALL CLASH',
        'desc': 'Naval cannon duel — first to 11 hits!',
        'accent': c.PIRATE_TEAL,
    },
    {
        'id': 'breakout',
        'title': 'TREASURE COVE',
        'desc': 'Smash through fort defenses to reach the loot!',
        'accent': c.PIRATE_ORANGE,
    },
    {
        'id': 'asteroids',
        'title': "KRAKEN'S WAKE",
        'desc': 'Navigate treacherous waters and blast sea monsters!',
        'accent': c.PIRATE_TAN_DARK,
    },
    {
        'id': 'pirate_dominion',
        'title': 'PORT ROYALE TYCOON',
        'desc': 'Buy ports, build trade empires, rule the seas!',
        'accent': c.PIRATE_GOLD,
    },
    {
        'id': 'highscores',
        'title': 'HIGH SCORES',
        'desc': 'View best records',
        'accent': c.PIRATE_GOLD,
    },
    {
        'id': 'quit',
        'title': 'QUIT',
        'desc': 'Exit to desktop',
        'accent': c.GRAY,
    },
]

TITLE_FONT = None
CARD_FONT = None
DESC_FONT = None
HINT_FONT = None
PRESS_FONT = None

def _init_fonts():
    global TITLE_FONT, CARD_FONT, DESC_FONT, HINT_FONT, PRESS_FONT
    TITLE_FONT = pg.font.Font(c.FONT_NAME, 80)
    CARD_FONT = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_TITLE)
    DESC_FONT = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_INSTRUCTIONS)
    HINT_FONT = pg.font.Font(c.FONT_NAME, 20)
    PRESS_FONT = pg.font.Font(c.FONT_NAME, 36)

_CARD_GLOWS = {}

def _ensure_card_glows():
    if _CARD_GLOWS:
        return
    for game in GAMES:
        color = game['accent']
        key = tuple(color[:3])
        if key in _CARD_GLOWS:
            continue
        pad = 8
        w = 640 + pad * 2
        h = 90 + pad * 2
        surf = pg.Surface((w, h), pg.SRCALPHA)
        for i in range(pad, 0, -1):
            alpha = max(0, 60 - (pad - i) * 8)
            r = pg.Rect(i, i, w - i * 2, h - i * 2)
            pg.draw.rect(surf, (*color, alpha), r, border_radius=8)
        _CARD_GLOWS[key] = surf

class Launcher:
    def __init__(self, surface):
        self.surface = surface
        self.selection = 0
        self.title_pulse = 0
        self.showing_scores = False
        self._scores_data = None
        self._scores_cache = []
        _init_fonts()
        _ensure_card_glows()
        rd._ensure_gradient()
        rd._ensure_scanlines()
        self._cache_texts()

    def _cache_texts(self):
        self._card_title_surfs = []
        self._card_desc_surfs = []
        for game in GAMES:
            self._card_title_surfs.append({
                'sel': CARD_FONT.render("▸ " + game['title'], True, c.WHITE),
                'unsel': CARD_FONT.render("  " + game['title'], True, c.GRAY),
            })
            self._card_desc_surfs.append(DESC_FONT.render(game['desc'], True, c.GRAY))
        self._nav_hint = HINT_FONT.render(
            "▲ ▼ SELECT     ●     SPACE / ENTER PLAY", True, (120, 120, 140))
        self._back_hint = HINT_FONT.render(
            "ESC / SPACE / Enter to go back", True, (120, 120, 140))
        self._highscores_title = TITLE_FONT.render("HIGH SCORES", True, c.WHITE)

        self._cache_title_glow()
        self._press_start = PRESS_FONT.render("▶  PRESS START  ◀", True, c.WHITE)
        self._coin_label = HINT_FONT.render("INSERT COIN", True, c.NEON_CYAN)
        self._credit_label = HINT_FONT.render("CREDIT  1", True, (100, 255, 100))

    def _cache_title_glow(self):
        self._title_frames = []
        glow_colors = [c.NEON_CYAN, c.NEON_MAGENTA, c.GOLD]
        base = TITLE_FONT.render("PIRATE ARCADE", True, c.WHITE)
        tw, th = base.get_width(), base.get_height()

        shadows = [TITLE_FONT.render("PIRATE ARCADE", True, color) for color in glow_colors]

        for i in range(8):
            t = i / 7
            pulse = 0.85 + 0.15 * t

            surf = pg.Surface((tw + 20, th + 20), pg.SRCALPHA)

            for radius in [4, 3]:
                a = int(25 * pulse * (1 - radius / 5))
                if a <= 0:
                    continue
                for shadow in shadows:
                    shadow.set_alpha(a)
                    for dx, dy in [(radius, 0), (-radius, 0), (0, radius), (0, -radius),
                                   (radius, radius), (-radius, -radius),
                                   (radius, -radius), (-radius, radius)]:
                        surf.blit(shadow, (10 + dx, 10 + dy))

            for radius in [2, 1]:
                a = int(45 * pulse * (1 - radius / 3))
                for shadow in shadows:
                    shadow.set_alpha(a)
                    for dx, dy in [(radius, 0), (-radius, 0), (0, radius), (0, -radius)]:
                        surf.blit(shadow, (10 + dx, 10 + dy))

            base_pulse = int(255 * pulse)
            main = TITLE_FONT.render("PIRATE ARCADE", True, (base_pulse, base_pulse, base_pulse))
            surf.blit(main, (10, 10))

            self._title_frames.append(surf)

    def run(self):
        clock = pg.time.Clock()
        fullscreen = False

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return 'quit'
                if event.type == pg.KEYDOWN and event.key == pg.K_F11:
                    self.surface, fullscreen = toggle_fullscreen(self.surface, fullscreen)
                    pg.display.set_caption("PIRATE ARCADE")
                    rd._ensure_gradient()
                    rd._ensure_scanlines()
                elif event.type == pg.KEYDOWN:
                    if self.showing_scores:
                        if event.key in (pg.K_ESCAPE, pg.K_SPACE, pg.K_RETURN):
                            self.showing_scores = False
                            self._scores_data = None
                            self._scores_cache = []
                        continue
                    if event.key in (pg.K_w, pg.K_UP):
                        self.selection = (self.selection - 1) % len(GAMES)
                    elif event.key in (pg.K_s, pg.K_DOWN):
                        self.selection = (self.selection + 1) % len(GAMES)
                    elif event.key in (pg.K_SPACE, pg.K_RETURN):
                        choice = GAMES[self.selection]
                        if choice['id'] == 'highscores':
                            self.showing_scores = True
                        elif choice['id'] == 'quit':
                            return 'quit'
                        else:
                            return choice['id']
                    elif event.key == pg.K_ESCAPE:
                        return 'quit'

            dt = clock.tick(c.FPS) / 1000.0
            self.title_pulse += dt * 2
            if self.showing_scores:
                self._draw_scores()
            else:
                self._draw()
            pg.display.flip()

    def _draw_bezel(self):
        pg.draw.line(self.surface, c.NEON_CYAN, (0, 3), (c.WINDOW_WIDTH, 3), 2)
        pg.draw.line(self.surface, c.NEON_MAGENTA, (0, 1), (c.WINDOW_WIDTH, 1), 1)

        bracket = c.NEON_CYAN
        bl = 35
        for cx, cy, sx, sy in [(10, 8, 1, 1), (c.WINDOW_WIDTH - 10, 8, -1, 1)]:
            pg.draw.line(self.surface, bracket, (cx, cy), (cx + sx * bl, cy), 3)
            pg.draw.line(self.surface, bracket, (cx, cy), (cx, cy + sy * bl), 3)

        vent = (40, 35, 55)
        for vx, sign in [(12, 1), (c.WINDOW_WIDTH - 32, -1)]:
            for vy in range(180, c.WINDOW_HEIGHT - 160, 10):
                pg.draw.line(self.surface, vent, (vx, vy), (vx + sign * 12, vy), 2)

        slot_y = c.WINDOW_HEIGHT - 65
        slot_w, slot_h = 50, 28
        spacing = 160
        cx = c.WINDOW_WIDTH // 2

        for side in (-1, 1):
            sx = cx + side * spacing // 2 - slot_w // 2
            slot_rect = pg.Rect(sx, slot_y, slot_w, slot_h)
            pg.draw.rect(self.surface, (15, 12, 25), slot_rect, border_radius=4)
            pg.draw.rect(self.surface, c.NEON_CYAN, slot_rect, 1, border_radius=4)
            inner = pg.Rect(sx + 8, slot_y + 6, slot_w - 16, slot_h - 12)
            pg.draw.rect(self.surface, (5, 0, 10), inner, border_radius=2)
            cl_x = sx + slot_w // 2 - self._coin_label.get_width() // 2
            self.surface.blit(self._coin_label, (cl_x, slot_y - 18))

        led_x = cx
        led_y = slot_y + 3
        led_a = int(180 + 75 * math.sin(self.title_pulse * 2))
        pg.draw.circle(self.surface, (0, led_a, 0), (led_x, led_y), 3)
        pg.draw.circle(self.surface, (0, 60, 0), (led_x, led_y), 3, 1)

        cl = cx - self._credit_label.get_width() // 2
        self.surface.blit(self._credit_label, (cl, slot_y + slot_h + 6))

    def _draw(self):
        self.surface.blit(rd._DARK_GRADIENT, (0, 0))

        idx = round((math.sin(self.title_pulse) * 0.5 + 0.5) * 7)
        idx = max(0, min(7, idx))
        title = self._title_frames[idx]
        tx = c.WINDOW_WIDTH // 2 - title.get_width() // 2
        self.surface.blit(title, (tx, 50))

        self._draw_bezel()

        card_start_y = 185
        card_spacing = 105

        for i, game in enumerate(GAMES):
            y = card_start_y + i * card_spacing
            is_selected = (i == self.selection)
            self._draw_card(i, game, y, is_selected)

        sel = GAMES[self.selection]
        if sel['id'] not in ('highscores', 'quit'):
            card_bottom = card_start_y + self.selection * card_spacing + 90
            ps_alpha = int(180 + 75 * math.sin(self.title_pulse * 2))
            ps = self._press_start.copy()
            ps.set_alpha(ps_alpha)
            ps_x = c.WINDOW_WIDTH // 2 - ps.get_width() // 2
            self.surface.blit(ps, (ps_x, card_bottom + 6))

        hx = c.WINDOW_WIDTH // 2 - self._nav_hint.get_width() // 2
        self.surface.blit(self._nav_hint, (hx, c.WINDOW_HEIGHT - 120))

        self.surface.blit(rd._SCANLINES, (0, 0))
        self.surface.blit(rd._VIGNETTE, (0, 0))

    def _draw_scores(self):
        self.surface.blit(rd._DARK_GRADIENT, (0, 0))
        self.surface.blit(self._highscores_title,
                          (c.WINDOW_WIDTH // 2 - self._highscores_title.get_width() // 2, 60))

        self._draw_bezel()

        data = hs.get_all()
        if data != self._scores_data:
            self._scores_data = data
            self._scores_cache = []
            y = 280
            if data and 'pong' in data:
                label = "CANNONBALL CLASH  —  " + str(data['pong']['score'])
                extra = data['pong'].get('label', '')
                if extra:
                    label += "  (" + extra + ")"
                self._scores_cache.append((y, CARD_FONT.render(label, True, c.GOLD)))
                y += 60
            if data and 'breakout' in data:
                label = "TREASURE COVE  —  " + str(data['breakout']['score'])
                self._scores_cache.append((y, CARD_FONT.render(label, True, c.GOLD)))
                y += 60
            if data and 'asteroids' in data:
                label = "KRAKEN'S WAKE  —  " + str(data['asteroids']['score'])
                self._scores_cache.append((y, CARD_FONT.render(label, True, c.GOLD)))
                y += 60
            if not data:
                self._scores_cache.append((y, DESC_FONT.render(
                    "No scores yet — play a game!", True, c.GRAY)))

        for y, surf in self._scores_cache:
            self.surface.blit(surf,
                              (c.WINDOW_WIDTH // 2 - surf.get_width() // 2, y))

        self.surface.blit(self._back_hint,
                          (c.WINDOW_WIDTH // 2 - self._back_hint.get_width() // 2, c.WINDOW_HEIGHT - 120))
        self.surface.blit(rd._SCANLINES, (0, 0))
        self.surface.blit(rd._VIGNETTE, (0, 0))

    def _draw_card(self, gi, game, y, selected):
        card_w = 640
        card_h = 90
        x = (c.WINDOW_WIDTH - card_w) // 2
        card_rect = pg.Rect(x, y, card_w, card_h)

        if selected:
            glow_key = tuple(game['accent'][:3])
            if glow_key in _CARD_GLOWS:
                self.surface.blit(_CARD_GLOWS[glow_key], (x - 8, y - 8))
            fill = (30, 25, 45)
            border_width = 3
        else:
            fill = (18, 15, 25)
            border_width = 1

        pg.draw.rect(self.surface, fill, card_rect, border_radius=8)

        border_color = game['accent'] if selected else (50, 40, 70)
        pg.draw.rect(self.surface, border_color, card_rect, border_width, border_radius=8)

        accent_w = 8 if selected else 5
        accent_rect = pg.Rect(x, y, accent_w, card_h)
        if selected:
            pg.draw.rect(self.surface, game['accent'], accent_rect,
                         border_top_left_radius=8, border_bottom_left_radius=8)
        else:
            dim_accent = tuple(max(0, v - 80) for v in game['accent'][:3])
            pg.draw.rect(self.surface, dim_accent, accent_rect,
                         border_top_left_radius=8, border_bottom_left_radius=8)

        self.surface.blit(self._card_title_surfs[gi]['sel' if selected else 'unsel'], (x + 25, y + 8))
        self.surface.blit(self._card_desc_surfs[gi], (x + 30, y + 58))
