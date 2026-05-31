import math
import random
import pygame as pg
from pygame import gfxdraw
import constants as c
from renderer import rounded_rect_fill, rounded_rect_outline

_FONT_CACHE = {}
_TEXT_CACHE = {}

def _get_font(size):
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pg.font.Font(c.FONT_NAME, size)
    return _FONT_CACHE[size]

# ---- Rendering utilities ----



_SHADOW_CACHE = {}
def _get_tile_shadow(x, y, w, h, r):
    w, h = int(w), int(h)
    key = (w, h, r)
    if key not in _SHADOW_CACHE:
        subj = pg.Surface((w + 6, h + 6), pg.SRCALPHA)
        rounded_rect_fill(subj, (0, 0, 0, 55), (0, 0, w, h), r)
        shadow = pg.Surface((w + 6, h + 6), pg.SRCALPHA)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                shadow.blit(subj, (dx + 3, dy + 3))
        shadow.set_alpha(50)
        _SHADOW_CACHE[key] = shadow
    return _SHADOW_CACHE[key], x - 3, y + 4

# ---- Color band position ----

def _band_rect(idx, x, y, w, h):
    if 1 <= idx <= 8:
        bh = max(int(h * 0.28), 28)
        return (x, y + h - bh, w, bh)
    if 10 <= idx <= 17:
        bw = max(int(w * 0.28), 24)
        return (x + w - bw, y, bw, h)
    if 19 <= idx <= 26:
        bh = max(int(h * 0.28), 28)
        return (x, y, w, bh)
    if 28 <= idx <= 35:
        bw = max(int(w * 0.28), 24)
        return (x, y, bw, h)
    return (x, y, w, max(1, h // 4))

# ---- Pre-rendered icons ----

_ICON_CACHE = {}
def _ensure_icons():
    if _ICON_CACHE:
        return
    sz = 64
    half = sz // 2

    # Treasure chest — START space
    chest = pg.Surface((sz, sz), pg.SRCALPHA)
    gfxdraw.filled_circle(chest, half, half, half - 2, (180, 140, 60))
    gfxdraw.aacircle(chest, half, half, half - 2, (220, 190, 80))
    body = (half - 18, half - 8, 36, 22)
    pg.draw.rect(chest, (220, 190, 80, 255), body, 1)
    pg.draw.rect(chest, c.GOLD, (half - 18, half - 8, 36, 4))
    gfxdraw.aacircle(chest, half, half - 4, 6, c.GOLD)
    gfxdraw.filled_circle(chest, half, half - 4, 6, c.GOLD)
    _ICON_CACHE['start'] = chest

    # Skull — LOCKER space
    skull = pg.Surface((sz, sz), pg.SRCALPHA)
    gfxdraw.filled_circle(skull, half, half - 2, 18, (200, 200, 210))
    gfxdraw.aacircle(skull, half, half - 2, 18, (230, 230, 240))
    gfxdraw.filled_circle(skull, half - 8, half - 8, 4, (10, 10, 10))
    gfxdraw.aacircle(skull, half - 8, half - 8, 4, (10, 10, 10))
    gfxdraw.filled_circle(skull, half + 8, half - 8, 4, (10, 10, 10))
    gfxdraw.aacircle(skull, half + 8, half - 8, 4, (10, 10, 10))
    mouth_pts = [(half - 12, half + 2), (half + 12, half + 2), (half + 8, half + 14), (half - 8, half + 14)]
    gfxdraw.filled_polygon(skull, mouth_pts, (20, 20, 30))
    gfxdraw.aapolygon(skull, mouth_pts, (20, 20, 30))
    for dx in (-6, 0, 6):
        pg.draw.line(skull, (200, 200, 210), (half + dx, half + 2), (half + dx, half + 10))
    _ICON_CACHE['jail'] = skull

    # Ship wheel — COVE space
    wheel = pg.Surface((sz, sz), pg.SRCALPHA)
    gfxdraw.filled_circle(wheel, half, half, 8, (100, 160, 100))
    gfxdraw.aacircle(wheel, half, half, 8, (140, 200, 140))
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        ex = int(half + math.cos(rad) * 18)
        ey = int(half + math.sin(rad) * 18)
        gfxdraw.line(wheel, half, half, ex, ey, (100, 160, 100))
    gfxdraw.filled_circle(wheel, half, half, 6, (60, 100, 60))
    _ICON_CACHE['free'] = wheel

    # Crossbones — GO TO TORTUGA space
    cross = pg.Surface((sz, sz), pg.SRCALPHA)
    gfxdraw.filled_circle(cross, half, half, 18, (180, 70, 70))
    gfxdraw.aacircle(cross, half, half, 18, (220, 100, 100))
    pg.draw.line(cross, (255, 255, 255), (half - 14, half - 14), (half + 14, half + 14), 4)
    pg.draw.line(cross, (255, 255, 255), (half + 14, half - 14), (half - 14, half + 14), 4)
    _ICON_CACHE['gotojail'] = cross

    # Chance / Chest card badges
    chance = pg.Surface((38, 38), pg.SRCALPHA)
    gfxdraw.filled_circle(chance, 19, 19, 17, (60, 45, 25))
    gfxdraw.aacircle(chance, 19, 19, 17, (140, 100, 40))
    q = _get_font(24).render("?", True, (255, 200, 80))
    chance.blit(q, (19 - q.get_width() // 2, 19 - q.get_height() // 2))
    _ICON_CACHE['chance'] = chance

    chest_icon = pg.Surface((38, 38), pg.SRCALPHA)
    gfxdraw.filled_circle(chest_icon, 19, 19, 17, (25, 45, 60))
    gfxdraw.aacircle(chest_icon, 19, 19, 17, (50, 100, 140))
    a = _get_font(22).render("\u2693", True, (150, 200, 255))
    chest_icon.blit(a, (19 - a.get_width() // 2, 19 - a.get_height() // 2))
    _ICON_CACHE['chest'] = chest_icon

    # Tax badge — coins
    tax = pg.Surface((38, 38), pg.SRCALPHA)
    gfxdraw.filled_circle(tax, 19, 19, 17, (55, 25, 25))
    gfxdraw.aacircle(tax, 19, 19, 17, (140, 50, 50))
    d = _get_font(16).render("$", True, (255, 180, 100))
    tax.blit(d, (19 - d.get_width() // 2, 19 - d.get_height() // 2))
    _ICON_CACHE['tax'] = tax


_PLAYER_DOTS = [None, None, None, None]

def _ensure_dots():
    if _PLAYER_DOTS[0] is not None:
        return
    for i, color in enumerate(c.PD_PLAYER_COLORS):
        dot = pg.Surface((12, 12), pg.SRCALPHA)
        gfxdraw.filled_circle(dot, 6, 6, 5, color)
        gfxdraw.aacircle(dot, 6, 6, 5, (255, 255, 255))
        _PLAYER_DOTS[i] = dot

_UPGRADE_STARS = [None, None, None]

def _ensure_stars():
    if _UPGRADE_STARS[0] is not None:
        return
    star_font = _get_font(14)
    for i in range(3):
        _UPGRADE_STARS[i] = star_font.render("★" * (i + 1), True, c.GOLD)

# ---- Pre-rendered player tokens ----

_TOKEN_SURFS = {}

def _ensure_tokens():
    if _TOKEN_SURFS:
        return
    sz = 36
    half = sz // 2

    _TOKEN_SURFS['_shadow'] = pg.Surface((sz, sz), pg.SRCALPHA)
    gfxdraw.filled_circle(_TOKEN_SURFS['_shadow'], half, half, half - 2, (0, 0, 0, 80))

    flag = pg.Surface((sz, sz), pg.SRCALPHA)
    skull_pts = [(half, 4), (half - 6, 10), (half - 4, 20), (half + 4, 20), (half + 6, 10)]
    gfxdraw.filled_polygon(flag, skull_pts, (200, 200, 210))
    gfxdraw.aapolygon(flag, skull_pts, (230, 230, 240))
    gfxdraw.filled_circle(flag, half - 3, 10, 2, (0, 0, 0))
    gfxdraw.filled_circle(flag, half + 3, 10, 2, (0, 0, 0))
    gfxdraw.filled_circle(flag, half, 14, 2, (0, 0, 0))
    pg.draw.line(flag, (0, 0, 0), (half - 3, 11), (half + 3, 11), 1)
    pg.draw.line(flag, (0, 0, 0), (half, 4), (half, 24), 1)
    _TOKEN_SURFS['Jolly Roger'] = flag

    chest_s = pg.Surface((sz, sz), pg.SRCALPHA)
    pg.draw.rect(chest_s, (180, 140, 60), (half - 9, half - 4, 18, 14))
    pg.draw.rect(chest_s, c.GOLD, (half - 9, half - 4, 18, 4))
    gfxdraw.aacircle(chest_s, half, half - 2, 4, c.GOLD)
    gfxdraw.filled_circle(chest_s, half, half - 2, 4, c.GOLD)
    pg.draw.rect(chest_s, (100, 70, 30, 255), (half - 9, half - 4, 18, 14), 1)
    _TOKEN_SURFS['Treasure Chest'] = chest_s

    cann = pg.Surface((sz, sz), pg.SRCALPHA)
    gfxdraw.filled_ellipse(cann, half, half, 10, 5, (100, 100, 110))
    gfxdraw.aaellipse(cann, half, half, 10, 5, (140, 140, 150))
    pg.draw.rect(cann, (120, 120, 130), (half - 7, half - 6, 14, 4))
    pg.draw.rect(cann, (60, 60, 70), (half + 4, half - 7, 4, 6))
    gfxdraw.filled_circle(cann, half - 5, half + 1, 2, (30, 30, 30))
    _TOKEN_SURFS['Cannon'] = cann

    anc = pg.Surface((sz, sz), pg.SRCALPHA)
    pg.draw.line(anc, (180, 180, 190), (half, 2), (half, 22), 3)
    gfxdraw.arc(anc, half - 8, 16, 10, 180, 360, (180, 180, 190))
    gfxdraw.arc(anc, half - 2, 16, 10, 0, 180, (180, 180, 190))
    gfxdraw.filled_circle(anc, half, 22, 3, (180, 180, 190))
    pg.draw.line(anc, (180, 180, 190), (half - 13, 8), (half + 13, 8), 2)
    _TOKEN_SURFS['Anchor'] = anc

    glow = pg.Surface((sz + 12, sz + 12), pg.SRCALPHA)
    gfxdraw.aacircle(glow, (sz + 12) // 2, (sz + 12) // 2, half + 4, (255, 255, 200, 100))
    _TOKEN_SURFS['_glow'] = glow

def _ensure_glow_frames():
    if _GLOW_FRAMES:
        return
    sz = 48
    half = sz // 2
    for i in range(16):
        alpha = 60 + int(i * 140 / 15)
        frame = pg.Surface((sz, sz), pg.SRCALPHA)
        gfxdraw.aacircle(frame, half, half, half - 2, (255, 255, 200, alpha))
        _GLOW_FRAMES.append(frame)

def _ensure_dice():
    if _DICE_FACES:
        return
    sz = 36
    half = sz // 2
    pip_positions = [
        [],                          # 0 (unused)
        [(half, half)],              # 1
        [(half - 7, half - 7), (half + 7, half + 7)],  # 2
        [(half - 7, half - 7), (half, half), (half + 7, half + 7)],  # 3
        [(half - 7, half - 7), (half + 7, half - 7),
         (half - 7, half + 7), (half + 7, half + 7)],  # 4
        [(half - 7, half - 7), (half + 7, half - 7),
         (half, half), (half - 7, half + 7), (half + 7, half + 7)],  # 5
        [(half - 7, half - 7), (half + 7, half - 7), (half, half - 7),
         (half - 7, half + 7), (half + 7, half + 7), (half, half + 7)],  # 6
    ]
    for val in range(1, 7):
        surf = pg.Surface((sz, sz), pg.SRCALPHA)
        rounded_rect_fill(surf, (240, 240, 245), (1, 1, sz - 2, sz - 2), 6)
        rounded_rect_outline(surf, (180, 180, 190), (1, 1, sz - 2, sz - 2), 6)
        for px, py in pip_positions[val]:
            gfxdraw.filled_circle(surf, px, py, 3, (40, 40, 50))
            gfxdraw.aacircle(surf, px, py, 3, (40, 40, 50))
        _DICE_FACES.append(surf)

# ---- Text caching ----

def _cache_static_text():
    if _TEXT_CACHE:
        return
    f36 = _get_font(36)
    f14 = _get_font(14)
    f13 = _get_font(13)
    f12 = _get_font(12)
    f11 = _get_font(11)

    _TEXT_CACHE['sea_label'] = f36.render("CARIBBEAN SEA", True, c.GOLD)
    _TEXT_CACHE['sea_label_shadow'] = f36.render("CARIBBEAN SEA", True, (20, 20, 40))
    _TEXT_CACHE['start'] = f14.render("START", True, (255, 200, 80))
    _TEXT_CACHE['jail'] = f12.render("LOCKER", True, (200, 200, 220))
    _TEXT_CACHE['free'] = f13.render("COVE", True, (140, 220, 140))
    _TEXT_CACHE['goto'] = f11.render("TO", True, (255, 120, 120))
    _TEXT_CACHE['jail2'] = f11.render("TORTUGA", True, (255, 120, 120))

    for idx, (name, group, cost, *_) in enumerate(c.PD_PROPERTIES):
        tw = _get_tile_width(idx)
        short = name if _get_font(12).size(name)[0] < tw - 10 else name.split()[0]
        _TEXT_CACHE[f'pname_{idx}'] = _get_font(12).render(short, True, (240, 240, 240))
        _TEXT_CACHE[f'pcost_{idx}'] = _get_font(11).render(f"${cost}", True, c.GOLD)

# ---- Board geometry ----

BOARD_LEFT = 100
BOARD_TOP = 80
BOARD_RIGHT = 1500
BOARD_BOTTOM = 820
BOARD_W = BOARD_RIGHT - BOARD_LEFT
BOARD_H = BOARD_BOTTOM - BOARD_TOP
CORNER = 130

TILE_MID_W = (BOARD_W - 2 * CORNER) / 8
TILE_MID_H = (BOARD_H - 2 * CORNER) / 8

_board_space_rects = [None] * c.PD_BOARD_SIZE

def _build_space_rects():
    _board_space_rects[0] = (BOARD_LEFT, BOARD_BOTTOM - CORNER, CORNER, CORNER)
    for i in range(8):
        x = BOARD_LEFT + CORNER + i * TILE_MID_W
        _board_space_rects[1 + i] = (x, BOARD_BOTTOM - CORNER, TILE_MID_W, CORNER)
    _board_space_rects[9] = (BOARD_RIGHT - CORNER, BOARD_BOTTOM - CORNER, CORNER, CORNER)
    for i in range(8):
        y = BOARD_BOTTOM - CORNER - (i + 1) * TILE_MID_H
        _board_space_rects[10 + i] = (BOARD_RIGHT - CORNER, y, CORNER, TILE_MID_H)
    _board_space_rects[18] = (BOARD_RIGHT - CORNER, BOARD_TOP, CORNER, CORNER)
    for i in range(8):
        x = BOARD_RIGHT - CORNER - (i + 1) * TILE_MID_W
        _board_space_rects[19 + i] = (x, BOARD_TOP, TILE_MID_W, CORNER)
    _board_space_rects[27] = (BOARD_LEFT, BOARD_TOP, CORNER, CORNER)
    for i in range(8):
        y = BOARD_TOP + CORNER + i * TILE_MID_H
        _board_space_rects[28 + i] = (BOARD_LEFT, y, CORNER, TILE_MID_H)

def _get_tile_width(idx):
    _, _, w, _ = _board_space_rects[idx]
    return w

_build_space_rects()
_cache_static_text()
_ensure_icons()
_ensure_tokens()

CENTER_LEFT = BOARD_LEFT + CORNER
CENTER_TOP = BOARD_TOP + CORNER
CENTER_W = BOARD_W - 2 * CORNER
CENTER_H = BOARD_H - 2 * CORNER

ISLAND_CENTERS = [
    (0.20, 0.65), (0.22, 0.60), (0.18, 0.55),
    (0.35, 0.70), (0.38, 0.65), (0.42, 0.60),
    (0.55, 0.75), (0.58, 0.70), (0.62, 0.65),
    (0.50, 0.50), (0.52, 0.45), (0.48, 0.40),
    (0.60, 0.40), (0.58, 0.35), (0.55, 0.30),
    (0.70, 0.55), (0.72, 0.50), (0.75, 0.45),
    (0.80, 0.35), (0.82, 0.30), (0.78, 0.25),
    (0.85, 0.60), (0.88, 0.55), (0.90, 0.50),
]

# ---- Center map ----

_map_cache = None

def _build_map():
    global _map_cache
    if _map_cache:
        return _map_cache
    surf = pg.Surface((CENTER_W, CENTER_H), pg.SRCALPHA)
    surf.fill((20, 32, 55))

    # Wave pattern
    for row in range(0, CENTER_H, 14):
        base_alpha = 12
        pts = []
        for col in range(0, CENTER_W, 6):
            y_offset = int(math.sin((col + row * 0.7) * 0.04) * 4)
            pts.append((col, row + y_offset))
        if len(pts) > 2:
            alpha = base_alpha + random.randint(0, 8)
            wave_color = (60, 120, 200, alpha)
            if len(pts) >= 3:
                pg.draw.lines(surf, wave_color, False, pts, 1)

    # Islands — organic shapes
    for fx, fy in ISLAND_CENTERS:
        ix = int(fx * CENTER_W)
        iy = int(fy * CENTER_H)
        r = random.randint(10, 16)
        pts = []
        n = 7
        for j in range(n):
            angle = 2 * math.pi * j / n + random.uniform(-0.2, 0.2)
            dist = r * random.uniform(0.7, 1.2)
            pts.append((ix + int(math.cos(angle) * dist), iy + int(math.sin(angle) * dist)))
        gfxdraw.filled_polygon(surf, pts, (45, 100, 55))
        gfxdraw.aapolygon(surf, pts, (60, 130, 70))
        # Palm tree trunk (small line)
        pg.draw.line(surf, (80, 60, 30), (ix, iy - 2), (ix, iy - 10), 2)
        # Palm fronds
        for angle in (-0.5, 0, 0.5):
            fx2 = ix + int(math.cos(angle) * 6)
            fy2 = iy - 10 + int(math.sin(angle) * 6)
            pg.draw.line(surf, (50, 130, 50), (ix, iy - 10), (fx2, fy2), 1)

    # Compass rose (top-right area)
    crx, cry = CENTER_W - 70, 70
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        length = 24 if angle % 90 == 0 else 14
        ex = int(crx + math.cos(rad) * length)
        ey = int(cry + math.sin(rad) * length)
        gfxdraw.line(surf, crx, cry, ex, ey, (200, 180, 120, 200))
        gfxdraw.filled_circle(surf, ex, ey, 2, (200, 180, 120))
    gfxdraw.aacircle(surf, crx, cry, 24, (200, 180, 120, 150))
    gfxdraw.aacircle(surf, crx, cry, 14, (200, 180, 120, 100))
    # N label
    nlabel = _get_font(10).render("N", True, (220, 200, 140))
    surf.blit(nlabel, (crx - nlabel.get_width() // 2, cry - 30))

    # Ship silhouette (center-right area)
    sx, sy = CENTER_W * 3 // 4, CENTER_H // 2
    hull_pts = [(sx - 20, sy + 6), (sx + 20, sy + 6), (sx + 14, sy - 2), (sx - 14, sy - 2)]
    gfxdraw.filled_polygon(surf, hull_pts, (60, 50, 40))
    gfxdraw.aapolygon(surf, hull_pts, (80, 70, 60))
    pg.draw.line(surf, (80, 70, 60), (sx, sy - 2), (sx, sy - 20), 2)
    sail_pts = [(sx, sy - 20), (sx + 12, sy - 6), (sx, sy - 6)]
    gfxdraw.filled_polygon(surf, sail_pts, (200, 200, 210, 180))
    gfxdraw.aapolygon(surf, sail_pts, (220, 220, 230, 200))

    # Glowing dots (distant ships / treasure markers)
    for _ in range(6):
        dx = random.randint(30, CENTER_W - 30)
        dy = random.randint(30, CENTER_H - 30)
        gfxdraw.filled_circle(surf, dx, dy, 1, (*c.GOLD, 100))

    _map_cache = surf
    return surf

def _build_wave_frames():
    if _WAVE_FRAMES:
        return
    n_frames = 60
    for frame in range(n_frames):
        phase = frame / n_frames * 2 * math.pi
        surf = pg.Surface((CENTER_W, CENTER_H), pg.SRCALPHA)
        for row in range(0, CENTER_H, 14):
            pts = []
            for col in range(0, CENTER_W, 6):
                y_offset = int(math.sin((col + row * 0.7) * 0.04 + phase) * 4)
                pts.append((col, row + y_offset))
            if len(pts) > 2:
                alpha = 6 + (frame % 5)
                pg.draw.lines(surf, (60, 120, 200, alpha), False, pts, 1)
        _WAVE_FRAMES.append(surf)

def _draw_animated_waves(surface):
    if not _WAVE_FRAMES:
        return
    idx = int(_WAVE_TIMER * 30) % len(_WAVE_FRAMES)
    surface.blit(_WAVE_FRAMES[idx], (CENTER_LEFT, CENTER_TOP))

# ---- Tile rendering ----

def _draw_static_space(surface, idx):
    rect = _board_space_rects[idx]
    x, y, w, h = rect
    space_type = c.PD_BOARD[idx]
    r = min(8, w // 2, h // 2)
    cr = min(10, w // 2, h // 2)

    shadow_surf, sx, sy = _get_tile_shadow(x, y, w, h, cr)
    surface.blit(shadow_surf, (sx, sy))

    if space_type[0] == 1:
        prop_idx = space_type[1]
        _, group, cost, _, _ = c.PD_PROPERTIES[prop_idx]
        color = c.PD_GROUP_COLORS[group]

        rounded_rect_fill(surface, (30, 30, 42), rect, cr)
        bx, by, bw, bh = _band_rect(idx, x, y, w, h)
        rounded_rect_fill(surface, color, (bx, by, bw, bh), min(6, cr))
        rounded_rect_outline(surface, (60, 60, 75), rect, cr)

        name_surf = _TEXT_CACHE[f'pname_{prop_idx}']
        cost_surf = _TEXT_CACHE[f'pcost_{prop_idx}']

        if 10 <= idx <= 17 or 28 <= idx <= 35:
            nx = x + w // 2 - name_surf.get_width() // 2
            ny = y + h // 2 - name_surf.get_height() // 2
            surface.blit(name_surf, (nx, ny - 6))
            surface.blit(cost_surf, (x + w // 2 - cost_surf.get_width() // 2, y + h - 14))
        else:
            nx = x + w // 2 - name_surf.get_width() // 2
            ny = y + 10
            surface.blit(name_surf, (nx, ny))
            surface.blit(cost_surf, (x + w // 2 - cost_surf.get_width() // 2, y + h - 14))

    elif space_type[0] == 0:
        rounded_rect_fill(surface, (50, 45, 30), rect, cr)
        rounded_rect_outline(surface, (100, 85, 40), rect, cr, 2)
        icon = _ICON_CACHE['start']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2 - 4))
        label = _TEXT_CACHE['start']
        surface.blit(label, (x + w // 2 - label.get_width() // 2, y + h - 14))

    elif space_type[0] == 2:
        rounded_rect_fill(surface, (50, 38, 22), rect, r)
        rounded_rect_outline(surface, (120, 80, 30), rect, r)
        icon = _ICON_CACHE['chance']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2))

    elif space_type[0] == 3:
        rounded_rect_fill(surface, (28, 42, 55), rect, r)
        rounded_rect_outline(surface, (50, 100, 140), rect, r)
        icon = _ICON_CACHE['chest']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2))

    elif space_type[0] == 4:
        rounded_rect_fill(surface, (55, 25, 25), rect, r)
        rounded_rect_outline(surface, (140, 50, 50), rect, r)
        icon = _ICON_CACHE['tax']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2))

    elif space_type[0] == 5:
        rounded_rect_fill(surface, (30, 30, 40), rect, cr)
        rounded_rect_outline(surface, (80, 80, 100), rect, cr, 2)
        icon = _ICON_CACHE['jail']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2 - 4))
        label = _TEXT_CACHE['jail']
        surface.blit(label, (x + w // 2 - label.get_width() // 2, y + h - 14))

    elif space_type[0] == 6:
        rounded_rect_fill(surface, (30, 45, 30), rect, cr)
        rounded_rect_outline(surface, (80, 100, 80), rect, cr, 2)
        icon = _ICON_CACHE['free']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2 - 4))
        label = _TEXT_CACHE['free']
        surface.blit(label, (x + w // 2 - label.get_width() // 2, y + h - 14))

    elif space_type[0] == 7:
        rounded_rect_fill(surface, (45, 28, 28), rect, cr)
        rounded_rect_outline(surface, (130, 55, 55), rect, cr, 2)
        icon = _ICON_CACHE['gotojail']
        surface.blit(icon, (x + w // 2 - icon.get_width() // 2, y + h // 2 - icon.get_height() // 2 - 4))
        surface.blit(_TEXT_CACHE['goto'], (x + w // 2 - _TEXT_CACHE['goto'].get_width() // 2, y + 4))
        surface.blit(_TEXT_CACHE['jail2'], (x + w // 2 - _TEXT_CACHE['jail2'].get_width() // 2, y + h - 14))


# ---- Public API ----

_PREV_POS = {}
_ANIM_POS = {}
_ANIM_PROGRESS = {}

_PARTICLES = []
_SHAKE_MAG = 0
_SHAKE_TIMER = 0.0
_GLOW_FRAMES = []
_DICE_FACES = []
_WAVE_FRAMES = []
_WAVE_TIMER = 0.0
_GLOW_TIMER = 0.0
_PURCHASE_FLASHES = []
_BOUNCE_DATA = {}

def trigger_shake(mag, dur):
    global _SHAKE_MAG, _SHAKE_TIMER
    _SHAKE_MAG = max(_SHAKE_MAG, mag)
    _SHAKE_TIMER = max(_SHAKE_TIMER, dur)

def spawn_particles(bx, by, count, color, spread=120, speed=100):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        spd = random.uniform(speed * 0.5, speed)
        _PARTICLES.append({
            'x': float(bx), 'y': float(by),
            'vx': math.cos(angle) * spd,
            'vy': math.sin(angle) * spd - speed * 0.3,
            'life': random.uniform(0.6, 1.0),
            'max_life': random.uniform(0.6, 1.0),
            'color': color,
        })

def trigger_purchase_flash(space_idx, duration=0.4):
    _PURCHASE_FLASHES.append([space_idx, duration, duration])

def trigger_token_bounce(player_idx):
    _BOUNCE_DATA[player_idx] = {'t': 0.0, 'A': 5.0}

def _update_vfx(dt, players):
    global _SHAKE_MAG, _SHAKE_TIMER, _WAVE_TIMER, _GLOW_TIMER
    _WAVE_TIMER += dt
    _GLOW_TIMER += dt
    if _SHAKE_TIMER > 0:
        _SHAKE_TIMER -= dt
        if _SHAKE_TIMER <= 0:
            _SHAKE_MAG = 0
        else:
            _SHAKE_MAG *= 0.9 ** (dt * 60)

    for p in _PARTICLES[:]:
        p['life'] -= dt
        if p['life'] <= 0:
            _PARTICLES.remove(p)
            continue
        p['vy'] += 200 * dt
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt

    for flash in _PURCHASE_FLASHES[:]:
        flash[1] -= dt
        if flash[1] <= 0:
            _PURCHASE_FLASHES.remove(flash)

    for idx in list(_BOUNCE_DATA.keys()):
        bd = _BOUNCE_DATA[idx]
        bd['t'] += dt * 12
        if bd['t'] >= 1.0:
            del _BOUNCE_DATA[idx]

def get_space_rect(idx):
    return _board_space_rects[idx]

def get_space_center(idx):
    x, y, w, h = _board_space_rects[idx]
    return (x + w // 2, y + h // 2)


_board_bg = None

def _build_board_bg():
    global _board_bg
    if _board_bg is not None:
        return
    _board_bg = pg.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT))
    _board_bg.fill((0, 0, 0))
    surf = _build_map()
    _board_bg.blit(surf, (CENTER_LEFT, CENTER_TOP))

    label = _TEXT_CACHE['sea_label']
    label_shadow = _TEXT_CACHE['sea_label_shadow']
    tx = CENTER_LEFT + CENTER_W // 2 - label.get_width() // 2
    ty = CENTER_TOP + CENTER_H // 2 - label.get_height() // 2
    _board_bg.blit(label_shadow, (tx + 2, ty + 2))
    _board_bg.blit(label, (tx, ty))

    for i in range(c.PD_BOARD_SIZE):
        _draw_static_space(_board_bg, i)


def draw_board(surface, properties, players, property_levels=None, dt=0, time=0, dice=(0, 0)):
    _build_board_bg()
    _ensure_dots()
    _ensure_stars()
    _ensure_glow_frames()
    _ensure_dice()
    _build_wave_frames()

    _update_vfx(dt, players)

    if _SHAKE_TIMER > 0:
        ox = random.randint(-int(_SHAKE_MAG), int(_SHAKE_MAG))
        oy = random.randint(-int(_SHAKE_MAG), int(_SHAKE_MAG))
    else:
        ox = oy = 0

    surface.blit(_board_bg, (ox, oy))
    _draw_animated_waves(surface)
    _draw_particles(surface, ox, oy)
    _draw_dice(surface, players, dice, time)

    for i in range(c.PD_BOARD_SIZE):
        st = c.PD_BOARD[i]
        if st[0] == 1:
            prop_idx = st[1]
            owner = properties[prop_idx]
            if owner is not None:
                _draw_property_overlay(surface, i, prop_idx, owner, property_levels)
                _draw_purchase_flash(surface, i, ox, oy)

    for p in players:
        idx = p.idx
        old = _PREV_POS.get(idx)
        if old != p.position:
            if old is not None and idx not in _ANIM_PROGRESS:
                _ANIM_POS[idx] = get_space_center(old)
                _ANIM_PROGRESS[idx] = 0.0
                trigger_token_bounce(idx)
            elif idx not in _ANIM_POS:
                _ANIM_POS[idx] = get_space_center(p.position)
            _PREV_POS[idx] = p.position
    _update_token_animations(dt, players)
    _draw_player_tokens(surface, players, time)


_OVERLAY_CACHE = {}

def _draw_property_overlay(surface, space_idx, prop_idx, owner, property_levels):
    rect = _board_space_rects[space_idx]
    x, y, w, h = rect
    level = property_levels[prop_idx] if property_levels else 0
    key = (space_idx, owner.idx, level)
    cached = _OVERLAY_CACHE.get(key)
    if cached is not None:
        surface.blit(cached, (x, y))
        return

    _, group, _, _, _ = c.PD_PROPERTIES[prop_idx]
    cr = min(8, w // 2, h // 2)
    r, g, b = owner.color
    overlay_color = (r, g, b, 120)

    overlay = pg.Surface((w, h), pg.SRCALPHA)
    rounded_rect_fill(overlay, overlay_color, (0, 0, w, h), cr)
    rounded_rect_outline(overlay, owner.color, (0, 0, w, h), cr, 2)

    bx, by, bw, bh = _band_rect(space_idx, 0, 0, w, h)
    band_color = c.PD_GROUP_COLORS[group]
    band = pg.Surface((bw, bh), pg.SRCALPHA)
    rounded_rect_fill(band, band_color, (0, 0, bw, bh), min(6, cr))
    overlay.blit(band, (bx, by))

    name_surf = _TEXT_CACHE[f'pname_{prop_idx}']
    cost_surf = _TEXT_CACHE[f'pcost_{prop_idx}']

    if 10 <= space_idx <= 17 or 28 <= space_idx <= 35:
        nx = w // 2 - name_surf.get_width() // 2
        ny = h // 2 - name_surf.get_height() // 2
        overlay.blit(name_surf, (nx, ny - 6))
        overlay.blit(cost_surf, (w // 2 - cost_surf.get_width() // 2, h - 14))
    else:
        overlay.blit(name_surf, (w // 2 - name_surf.get_width() // 2, 10))
        overlay.blit(cost_surf, (w // 2 - cost_surf.get_width() // 2, h - 14))

    overlay.blit(_PLAYER_DOTS[owner.idx], (4, h - 12))
    if property_levels:
        level = property_levels[prop_idx]
        if level > 0:
            star_surf = _UPGRADE_STARS[level - 1]
            overlay.blit(star_surf, (w - star_surf.get_width() - 4, h - 16))

    _OVERLAY_CACHE[key] = overlay
    surface.blit(overlay, (x, y))


def _draw_particles(surface, ox=0, oy=0):
    for p in _PARTICLES:
        alpha = int(255 * p['life'] / p['max_life'])
        if alpha <= 0:
            continue
        r, g, b = p['color']
        pos = (int(p['x'] + ox), int(p['y'] + oy))
        sz = max(2, int(4 * p['life'] / p['max_life']))
        gfxdraw.filled_circle(surface, pos[0], pos[1], sz, (r, g, b, min(255, alpha)))
        gfxdraw.aacircle(surface, pos[0], pos[1], sz, (r, g, b, min(255, alpha)))


def _draw_dice(surface, players, dice, time):
    if dice == (0, 0):
        return
    d1, d2 = dice
    if d1 < 1 or d1 > 6 or d2 < 1 or d2 > 6:
        return
    pos = 0
    for p in players:
        if not p.bankrupt:
            pos = p.position
            break
    cx, cy = get_space_center(pos)
    die_w = 36
    gap = 6
    total_w = die_w * 2 + gap
    dx = cx - total_w // 2
    dy = cy - die_w - 20
    shadow_surf = _TOKEN_SURFS.get('_shadow')
    for die_surf in (_DICE_FACES[d1 - 1], _DICE_FACES[d2 - 1]):
        if shadow_surf:
            surface.blit(shadow_surf, (int(dx + 2), int(dy + 3)))
        surface.blit(die_surf, (int(dx), int(dy)))
        dx += die_w + gap


def _draw_purchase_flash(surface, space_idx, ox=0, oy=0):
    for flash in _PURCHASE_FLASHES:
        if flash[0] != space_idx:
            continue
        timer, dur = flash[1], flash[2]
        if timer <= 0:
            return
        alpha = int(180 * timer / dur)
        alpha = max(0, min(255, alpha))
        rect = _board_space_rects[space_idx]
        x, y, w, h = rect
        flash_surf = pg.Surface((w, h), pg.SRCALPHA)
        rounded_rect_fill(flash_surf, (255, 255, 255, alpha), (0, 0, w, h), min(8, w // 2, h // 2))
        surface.blit(flash_surf, (x + ox, y + oy))


def _update_token_animations(dt, players):
    for p in players:
        idx = p.idx
        if idx in _ANIM_PROGRESS:
            _ANIM_PROGRESS[idx] += dt * 3.5
            if _ANIM_PROGRESS[idx] >= 1.0:
                _ANIM_PROGRESS[idx] = 1.0
                cx, cy = get_space_center(p.position)
                _ANIM_POS[idx] = (cx, cy)
                del _ANIM_PROGRESS[idx]
            else:
                t = _ANIM_PROGRESS[idx]
                sx, sy = _ANIM_POS[idx]
                ex, ey = get_space_center(p.position)
                t = t * t * (3 - 2 * t)
                cx = int(sx + (ex - sx) * t)
                cy = int(sy + (ey - sy) * t)
                _ANIM_POS[idx] = (cx, cy)

def _draw_player_tokens(surface, players, time=0):
    small_font = _get_font(10)
    current_idx = players[0].idx if players else 0
    for player in players:
        if player.bankrupt:
            continue
        ax, ay = _ANIM_POS.get(player.idx, get_space_center(player.position))
        ox, oy = _token_offset(player.idx)
        px = ax + ox
        py = ay + oy

        bounce = _BOUNCE_DATA.get(player.idx)
        if bounce:
            by = int(bounce['A'] * math.exp(-bounce['t'] * 4) * math.sin(bounce['t'] * 12))
            py -= by

        shadow_surf = _TOKEN_SURFS.get('_shadow')
        if shadow_surf:
            surface.blit(shadow_surf, (px - shadow_surf.get_width() // 2 + 2,
                                       py - shadow_surf.get_height() // 2 + 3))

        if player.idx == current_idx and _GLOW_FRAMES:
            glow_idx = int(_GLOW_TIMER * 3) % len(_GLOW_FRAMES)
            glow_surf = _GLOW_FRAMES[glow_idx]
        else:
            glow_surf = _TOKEN_SURFS.get('_glow')
        if glow_surf:
            gx = px - glow_surf.get_width() // 2
            gy = py - glow_surf.get_height() // 2
            surface.blit(glow_surf, (gx, gy))

        token_surf = _TOKEN_SURFS.get(player.token)
        if token_surf:
            tcx = px - token_surf.get_width() // 2
            tcy = py - token_surf.get_height() // 2
            surface.blit(token_surf, (tcx, tcy))

        name_key = f'tokname_{player.idx}'
        name_surf = _TEXT_CACHE.get(name_key)
        if name_surf is None:
            name_surf = small_font.render(player.name[:6], True, (220, 220, 220))
            _TEXT_CACHE[name_key] = name_surf
        surface.blit(name_surf, (px - name_surf.get_width() // 2, py - 18))

def _token_offset(player_idx):
    offsets = [(-18, -18), (18, -18), (-18, 18), (18, 18)]
    return offsets[player_idx] if player_idx < 4 else (0, 0)

def reset_animation_state():
    _PREV_POS.clear()
    _ANIM_POS.clear()
    _ANIM_PROGRESS.clear()
    _PARTICLES.clear()
    _PURCHASE_FLASHES.clear()
    _BOUNCE_DATA.clear()
    _OVERLAY_CACHE.clear()
    global _SHAKE_MAG, _SHAKE_TIMER, _WAVE_TIMER, _GLOW_TIMER
    _SHAKE_MAG = 0
    _SHAKE_TIMER = 0.0
    _WAVE_TIMER = 0.0
    _GLOW_TIMER = 0.0
