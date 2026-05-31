# Pirate Arcade

A pirate-themed collection of four classic arcade games built with Python and Pygame. Features a custom arcade-style launcher with CRT scanlines, neon marquee, and cabinet bezel aesthetic.

## Games

| Game | Original Inspiration | Description |
|------|-------------------|-------------|
| **Cannonball Clash** | Pong | A pirate ship cannonball duel. First ship to 11 hits wins! |
| **Treasure Cove** | Breakout | Smash through fort defenses to secure the loot. |
| **Kraken's Wake** | Asteroids | Sail the Kraken's Wake and sink enemy ships to advance waves. |
| **Port Royale Tycoon** | Monopoly | Build a shipping empire. Buy properties, collect port fees, and outmaneuver rival captains. |

## Features

- Unifi ed pirate aesthetic (colors, sounds, nautical ship names)
- Arcade-style launcher with CRT scanlines, neon marquee, and cabinet bezel
- Save/load support for Port Royale Tycoon
- High-score tracking across all games
- Configurable difficulty, fullscreen mode, and FPS counter
- Smooth 60 FPS rendering with glow effects, particles, and screen shake
- Pure-Pygame rendering — no external assets required

## Installation

### From source (any platform)

```bash
git clone https://github.com/yourusername/pirate-arcade.git
cd pirate-arcade
pip install -r requirements.txt
python main.py
```

### Debian package (Linux)

Download the latest `.deb` from the [Releases](https://github.com/yourusername/pirate-arcade/releases) page and install:

```bash
sudo apt install ./pirate-arcade_*.deb
```

## Requirements

- Python 3.10+
- Pygame 2.5.0+
- NumPy

## Controls

| Key | Action |
|-----|--------|
| W / S / Up / Down | Navigate launcher menu |
| Space / Enter | Select game / Fire |
| Escape | Back / Pause / Quit |
| F11 | Toggle fullscreen |
| F1 | Toggle FPS counter |

Refer to in-game help for game-specific controls.

## Building the Debian package

```bash
./build_deb.sh
```

Produces `dist/pirate-arcade_<version>_all.deb`.

## Testing

```bash
pytest tests/test_pirate_dominion.py -v
```

## Screenshots

*Screenshots coming soon.*

## License

Distributed under the MIT License. See `LICENSE` for details.
