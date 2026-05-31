import math
import random
import pygame as pg
from pygame import gfxdraw
import constants as c
from renderer import _OVERLAY, rounded_rect_fill, rounded_rect_outline

HUD_TOP = 856
HUD_HEIGHT = 44

_HUD_CACHE = {}
_TEXT_RENDER_CACHE = {}
_WRAP_CACHE = {}
_PROP_FONT_CACHE = {}

_FLOAT_TEXTS = []
_CONFETTI = []
_last_money = {}
_last_msg = ""
_popup_anim = 1.0
_popup_anim_dt = 0.0


def _ensure_hud():
    if _HUD_CACHE:
        return
    bg = pg.Surface((c.WINDOW_WIDTH, HUD_HEIGHT))
    for y in range(HUD_HEIGHT):
        t = y / HUD_HEIGHT
        r = int(28 + t * 18)
        g = int(20 + t * 14)
        b = int(14 + t * 10)
        pg.draw.line(bg, (r, g, b), (0, y), (c.WINDOW_WIDTH, y))
    pg.draw.rect(bg, c.HUD_ACCENT, (0, 0, c.WINDOW_WIDTH, 3))
    _HUD_CACHE['bg'] = bg

    coin = pg.Surface((20, 20), pg.SRCALPHA)
    gfxdraw.filled_circle(coin, 10, 10, 8, c.GOLD)
    gfxdraw.aacircle(coin, 10, 10, 8, (200, 170, 50))
    gfxdraw.filled_circle(coin, 10, 10, 5, (230, 190, 30))
    _HUD_CACHE['coin'] = coin

    _HUD_CACHE['hud'] = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_HUD)
    _HUD_CACHE['small'] = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_SMALL)
    _HUD_CACHE['msg'] = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_INSTRUCTIONS)


def _cached_render(key, font, text, color):
    entry = _TEXT_RENDER_CACHE.get(key)
    if entry and entry[0] == text and entry[1] == color:
        return entry[2]
    surf = font.render(text, True, color)
    _TEXT_RENDER_CACHE[key] = (text, color, surf)
    return surf


def _spawn_float_text(text, color, x, y):
    _FLOAT_TEXTS.append({
        'text': text, 'color': color,
        'x': x, 'y': y,
        'timer': 1.0, 'max_timer': 1.0,
    })

def _update_float_texts(dt):
    for ft in _FLOAT_TEXTS[:]:
        ft['timer'] -= dt
        ft['y'] -= 40 * dt
        if ft['timer'] <= 0:
            _FLOAT_TEXTS.remove(ft)

def _draw_float_texts(surface):
    for ft in _FLOAT_TEXTS:
        alpha = int(255 * ft['timer'] / ft['max_timer'])
        if alpha <= 0:
            continue
        font = _HUD_CACHE.get('small', pg.font.Font(c.FONT_NAME, 18))
        surf = font.render(ft['text'], True, ft['color'])
        surf.set_alpha(min(255, alpha))
        surface.blit(surf, (int(ft['x']), int(ft['y']) - HUD_TOP))

def draw_hud(surface, players, gameplay, dt=0.016):
    _ensure_hud()
    surface.blit(_HUD_CACHE['bg'], (0, HUD_TOP))
    _update_float_texts(dt)
    player = gameplay.current_player
    hud_font = _HUD_CACHE['hud']
    small = _HUD_CACHE['small']

    x = 20
    surface.blit(_HUD_CACHE['coin'], (x, HUD_TOP + 13))

    diff_map = {'easy': 'Greenhorn', 'medium': 'Captain', 'hard': 'Admiral'}
    diff_label = diff_map.get(player.difficulty, player.difficulty.title())
    suffix = " (YOU)" if not player.is_ai else f" (AI-{diff_label})"
    display_name = player.name[:12] + suffix
    name_surf = _cached_render(('name', player.idx, player.is_ai, player.difficulty),
                               hud_font, display_name, player.color)
    surface.blit(name_surf, (x + 26, HUD_TOP + 8))
    x = 220

    global _last_money
    prev = _last_money.get(player.idx)
    if prev is not None and prev != player.money:
        delta = player.money - prev
        sign = "+" if delta > 0 else ""
        _spawn_float_text(f"{sign}${delta}", (180, 255, 150) if delta > 0 else (255, 150, 130), x + 20, HUD_TOP + 4)
    _last_money[player.idx] = player.money

    money_surf = _cached_render(('money', player.idx), hud_font, f"${player.money}", c.GOLD)
    surface.blit(money_surf, (x, HUD_TOP + 8))
    x += money_surf.get_width() + 20

    pg.draw.line(surface, (50, 40, 30), (x, HUD_TOP + 6), (x, HUD_TOP + HUD_HEIGHT - 6), 1)
    x += 10

    dice_str = gameplay.get_dice_display()
    if dice_str:
        dice_surf = _cached_render(('dice',), hud_font, f"  {dice_str}", (200, 200, 200))
        surface.blit(dice_surf, (x, HUD_TOP + 8))
        x += dice_surf.get_width() + 10

    pg.draw.line(surface, (50, 40, 30), (x, HUD_TOP + 6), (x, HUD_TOP + HUD_HEIGHT - 6), 1)
    x += 10

    turn_surf = _cached_render(('turn',), small, f"Turn {gameplay.turn_count + 1}", (160, 160, 160))
    surface.blit(turn_surf, (x, HUD_TOP + 12))
    x += turn_surf.get_width() + 20

    props_str = f"Props: {len(player.properties)}"
    props_surf = _cached_render(('props', player.idx), small, props_str, (150, 200, 150))
    surface.blit(props_surf, (x, HUD_TOP + 12))
    x += props_surf.get_width() + 20

    pg.draw.line(surface, (50, 40, 30), (x, HUD_TOP + 6), (x, HUD_TOP + HUD_HEIGHT - 6), 1)
    x += 10

    for p in players:
        short = p.name.split()[0]
        if p.bankrupt:
            label = f"{short}: MR"
            surf = _cached_render(('opp', p.idx, 'marooned'), small, label, (200, 80, 80))
        else:
            label = f"{short}: ${p.money}"
            surf = _cached_render(('opp', p.idx, 'alive'), small, label, p.color)
        surface.blit(surf, (x, HUD_TOP + 12))
        x += surf.get_width() + 16

    _draw_float_texts(surface)
    _draw_card_hint(surface, gameplay)
    _draw_message(surface, gameplay, dt)


def _draw_card_hint(surface, gameplay):
    if gameplay.last_card_timer <= 0 or not gameplay.last_card_text:
        return
    text = gameplay.last_card_text
    short = text[:32] + "..." if len(text) > 35 else text
    small = _HUD_CACHE['small']
    has_harbor = "pay 50" in text
    if "collect" in text.lower() or any(w in text for w in ["Advance", "Sail", "Gold", "found",
                                                              "reward", "captured", "sold"]):
        color = (180, 255, 150)
    elif "pay" in text.lower() or "lose" in text.lower() or has_harbor:
        color = (255, 150, 130)
    else:
        color = (200, 200, 200)
    surf = small.render(f"Last card: {short}", True, color)
    sx = c.WINDOW_WIDTH - surf.get_width() - 16
    surface.blit(surf, (sx, HUD_TOP + 6))
    alpha = min(255, int(255 * (gameplay.last_card_timer / 3.0)))
    if alpha < 255:
        fade = pg.Surface(surf.get_size(), pg.SRCALPHA)
        fade.blit(surf, (0, 0))
        fade.set_alpha(alpha)
        surface.blit(fade, (sx, HUD_TOP + 6))


def _draw_message(surface, gameplay, dt=0.016):
    global _last_msg, _popup_anim, _popup_anim_dt
    msg = gameplay.get_message()
    if not msg:
        _popup_anim = 1.0
        _popup_anim_dt = 0.0
        _last_msg = ""
        return

    if msg != _last_msg:
        _last_msg = msg
        _popup_anim = 0.0
        _popup_anim_dt = 0.0

    _popup_anim_dt += dt
    _popup_anim = min(1.0, _popup_anim_dt / 0.3)
    t = _popup_anim
    ease = 1 - (1 - t) * (1 - t) * (1 - t)

    msg_font = _HUD_CACHE['msg']
    lines = _wrap_text(msg, msg_font, 480)

    header_text = None
    if "Merchant's Charter" in msg:
        header_text = "\u2693 MERCHANT'S CHARTER"
    elif "Admiralty Orders" in msg:
        header_text = "\u2693 ADMIRALTY ORDERS"
    elif "(Y/N)" in msg:
        header_text = "PROPERTY OFFER"
    elif "Upgrade" in msg:
        header_text = "UPGRADE"

    panel_w = 520
    line_h = 28
    header_h = 32 if header_text else 0
    content_h = len(lines) * line_h
    panel_h = 20 + header_h + content_h + 20

    panel_x = c.WINDOW_WIDTH // 2 - panel_w // 2
    panel_y = int(200 + (250 - 200) * (1 - ease))

    shadow = pg.Surface((panel_w + 8, panel_h + 8), pg.SRCALPHA)
    rounded_rect_fill(shadow, (0, 0, 0, 40), (4, 4, panel_w, panel_h), c.PANEL_RADIUS)
    surface.blit(shadow, (panel_x - 4, panel_y))

    panel = pg.Surface((panel_w + 4, panel_h + 4), pg.SRCALPHA)
    rounded_rect_fill(panel, c.PANEL_FILL, (0, 0, panel_w, panel_h), c.PANEL_RADIUS)
    rounded_rect_outline(panel, c.PANEL_OUTLINE, (0, 0, panel_w, panel_h), c.PANEL_RADIUS)
    pg.draw.rect(panel, c.PANEL_ACCENT, (10, 8, panel_w - 20, 3))
    surface.blit(panel, (panel_x - 2, panel_y - 2))

    y = panel_y + 16
    if header_text:
        hdr = _cached_render(('popup_hdr', header_text), msg_font, header_text, c.GOLD)
        surface.blit(hdr, (c.WINDOW_WIDTH // 2 - hdr.get_width() // 2, y))
        y += header_h

    for line in lines:
        line_color = (255, 240, 200) if not header_text else (220, 220, 220)
        line_surf = _cached_render(('popup_msg', line), msg_font, line, line_color)
        surface.blit(line_surf, (c.WINDOW_WIDTH // 2 - line_surf.get_width() // 2, y))
        y += line_h


def _wrap_text(text, font, max_width):
    key = (text, max_width)
    cached = _WRAP_CACHE.get(key)
    if cached is not None:
        return cached
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + (" " if current else "") + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    result = lines if lines else [text]
    _WRAP_CACHE[key] = result
    return result


_go_surfs = {}

_CONFETTI_INIT = False
_CONFETTI_COLORS = [
    c.GOLD, (255, 80, 80), (80, 180, 255),
    (80, 255, 100), (255, 220, 50), (255, 255, 255),
]

def _init_confetti():
    global _CONFETTI_INIT
    if _CONFETTI_INIT:
        return
    _CONFETTI_INIT = True
    for _ in range(80):
        _CONFETTI.append(_new_confetti_particle())

def _new_confetti_particle():
    return {
        'x': random.randint(0, c.WINDOW_WIDTH),
        'y': random.randint(-200, -20),
        'vx': random.uniform(-30, 30),
        'vy': random.uniform(80, 200),
        'color': random.choice(_CONFETTI_COLORS),
        'size': random.randint(4, 8),
        'rot': random.uniform(0, 360),
        'rot_speed': random.uniform(-200, 200),
        'life': random.uniform(2.0, 4.0),
        'max_life': random.uniform(2.0, 4.0),
    }

def _update_confetti(dt):
    SH = c.WINDOW_HEIGHT
    for p in _CONFETTI:
        p['life'] -= dt
        p['vy'] += 80 * dt
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        p['rot'] += p['rot_speed'] * dt
        if p['life'] <= 0 or p['y'] > SH + 20:
            p.update(_new_confetti_particle())

def _draw_confetti(surface):
    for p in _CONFETTI:
        alpha = int(255 * min(p['life'] / p['max_life'] * 2, 1.0))
        if alpha <= 0:
            continue
        s = p['size']
        half = s // 2
        cos_a = math.cos(math.radians(p['rot']))
        sin_a = math.sin(math.radians(p['rot']))
        pts = [
            (p['x'] + (-half * cos_a - (-half) * sin_a),
             p['y'] + (-half * sin_a + (-half) * cos_a)),
            (p['x'] + (half * cos_a - (-half) * sin_a),
             p['y'] + (half * sin_a + (-half) * cos_a)),
            (p['x'] + (half * cos_a - half * sin_a),
             p['y'] + (half * sin_a + half * cos_a)),
            (p['x'] + (-half * cos_a - half * sin_a),
             p['y'] + (-half * sin_a + half * cos_a)),
        ]
        r, g, b = p['color']
        gfxdraw.filled_polygon(surface, pts, (r, g, b, min(255, alpha)))

def draw_game_over_screen(surface, players, winner, gameplay, dt=0):
    if not _CONFETTI:
        _init_confetti()
    _update_confetti(dt)
    _draw_confetti(surface)
    surface.blit(_OVERLAY, (0, 0))
    if not _go_surfs:
        _go_surfs['title'] = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_TITLE)
        _go_surfs['hud'] = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_HUD)
        _go_surfs['inst'] = pg.font.Font(c.FONT_NAME, c.FONT_SIZE_INSTRUCTIONS)
    title_font = _go_surfs['title']
    hud_font = _go_surfs['hud']
    inst_font = _go_surfs['inst']
    if winner:
        text = title_font.render(f"{winner.name} WINS!", True, c.GOLD)
        shadow = title_font.render(f"{winner.name} WINS!", True, (30, 20, 0))
        surface.blit(shadow, (c.WINDOW_WIDTH // 2 - shadow.get_width() // 2 + 2,
                              c.WINDOW_HEIGHT // 2 - 118))
        surface.blit(text, (c.WINDOW_WIDTH // 2 - text.get_width() // 2,
                            c.WINDOW_HEIGHT // 2 - 120))
        worth_surf = hud_font.render(
            f"Net Worth: ${winner.net_worth}  |  {gameplay.turn_count + 1} turns",
            True, (200, 200, 200))
        surface.blit(worth_surf, (c.WINDOW_WIDTH // 2 - worth_surf.get_width() // 2,
                                  c.WINDOW_HEIGHT // 2 - 60))
    y = c.WINDOW_HEIGHT // 2
    for p in sorted(players, key=lambda x: x.net_worth, reverse=True):
        status = "MAROONED" if p.bankrupt else f"${p.net_worth}"
        color = p.color if not p.bankrupt else (100, 60, 60)
        line = f"{p.name}: {status}  ({len(p.properties)} properties)"
        surf = hud_font.render(line, True, color)
        surface.blit(surf, (c.WINDOW_WIDTH // 2 - surf.get_width() // 2, y))
        y += 36
    prompt = inst_font.render("Press SPACE to continue  |  ESC to menu", True, c.GRAY)
    surface.blit(prompt, (c.WINDOW_WIDTH // 2 - prompt.get_width() // 2,
                          c.WINDOW_HEIGHT - 60))


def _get_prop_font(size):
    f = _PROP_FONT_CACHE.get(size)
    if f is None:
        f = pg.font.Font(c.FONT_NAME, size)
        _PROP_FONT_CACHE[size] = f
    return f


def draw_properties_popup(surface, players, gameplay):
    overlay = pg.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT), pg.SRCALPHA)
    overlay.fill((0, 0, 0, c.PANEL_DIM_ALPHA))
    surface.blit(overlay, (0, 0))

    panel_w = 700
    panel_h = 520
    px = c.WINDOW_WIDTH // 2 - panel_w // 2
    py = c.WINDOW_HEIGHT // 2 - panel_h // 2

    shadow = pg.Surface((panel_w + 8, panel_h + 8), pg.SRCALPHA)
    rounded_rect_fill(shadow, (0, 0, 0, 40), (4, 4, panel_w, panel_h), c.PANEL_RADIUS)
    surface.blit(shadow, (px - 4, py))

    panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
    rounded_rect_fill(panel, c.PANEL_FILL, (0, 0, panel_w, panel_h), c.PANEL_RADIUS)
    rounded_rect_outline(panel, c.PANEL_OUTLINE, (0, 0, panel_w, panel_h), c.PANEL_RADIUS)
    pg.draw.rect(panel, c.PANEL_ACCENT, (10, 8, panel_w - 20, 3))
    surface.blit(panel, (px, py))

    title_font = _get_prop_font(c.FONT_SIZE_HUD)
    inst_font = _get_prop_font(c.FONT_SIZE_INSTRUCTIONS)
    prop_font = _get_prop_font(c.FONT_SIZE_SMALL)
    small_font = _get_prop_font(c.FONT_SIZE_TINY)

    title = title_font.render("PROPERTIES", True, c.GOLD)
    surface.blit(title, (c.WINDOW_WIDTH // 2 - title.get_width() // 2, py + 18))

    left_col_x = px + 24
    right_col_x = px + panel_w // 2 + 16
    col_y = [py + 56, py + 56]

    for col, p in enumerate(p for p in players if not p.bankrupt):
        col_idx = col % 2
        cx = left_col_x if col_idx == 0 else right_col_x
        cy = col_y[col_idx]

        player_label = f"{p.name}  (${p.money}, {len(p.properties)} props)"
        pl_surf = small_font.render(player_label, True, p.color)
        surface.blit(pl_surf, (cx, cy))
        cy += 26

        if not p.properties:
            empty_surf = small_font.render("  No properties", True, (120, 120, 120))
            surface.blit(empty_surf, (cx, cy))
            cy += 24
        else:
            for prop_idx in p.properties:
                name, group, cost, _, _ = c.PD_PROPERTIES[prop_idx]
                level = gameplay.property_levels[prop_idx]
                mortgaged = gameplay.mortgaged[prop_idx]

                stars = "\u2605" * level if level > 0 else ""
                mg = " [M]" if mortgaged else ""
                group_color = c.PD_GROUP_COLORS[group]

                line = f"  {name:<18}  ${cost:>3}{mg}"
                lp_surf = prop_font.render(line, True, group_color)
                surface.blit(lp_surf, (cx, cy))

                if stars:
                    st_surf = small_font.render(stars, True, c.GOLD)
                    surface.blit(st_surf, (cx + lp_surf.get_width() + 4, cy))
                cy += 22

        cy += 8
        col_y[col_idx] = cy

    prompt = inst_font.render("Press any key to close", True, (160, 160, 160))
    surface.blit(prompt, (c.WINDOW_WIDTH // 2 - prompt.get_width() // 2,
                          py + panel_h - 36))
