# Pirate Arcade

[![CI](https://github.com/edonahue/pirate-arcade/actions/workflows/ci.yml/badge.svg)](https://github.com/edonahue/pirate-arcade/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A pirate-themed collection of four classic arcade games built with Python and Pygame. Features a custom arcade-style launcher with CRT scanlines, neon marquee, and cabinet bezel aesthetic.

## Games

| Game | Original Inspiration | Description |
|------|-------------------|-------------|
| **Cannonball Clash** | Pong | A pirate ship cannonball duel. First ship to 11 hits wins! |
| **Treasure Cove** | Breakout | Smash through fort defenses to secure the loot. |
| **Kraken's Wake** | Asteroids | Sail the Kraken's Wake and sink enemy ships to advance waves. |
| **Port Royale Tycoon** | Property-trading board game | Build a shipping empire. Buy properties, collect port fees, and outmaneuver rival captains. |

## Features

- Unified pirate aesthetic (colors, sounds, nautical ship names)
- Arcade-style launcher with CRT scanlines, neon marquee, and cabinet bezel
- Save/load support for Port Royale Tycoon
- High-score tracking across all games
- Configurable difficulty, fullscreen mode, and FPS counter
- Smooth 60 FPS rendering with glow effects, particles, and screen shake
- Pure-Pygame rendering — no external assets required
- Cross-platform (Linux, Windows, macOS)

## Installation

### From source (any platform)

```bash
git clone https://github.com/edonahue/pirate-arcade.git
cd pirate-arcade
pip install -r requirements.txt
python main.py
```

### Debian package (Linux)

Download the latest `.deb` from the [Releases](https://github.com/edonahue/pirate-arcade/releases) page and install:

```bash
sudo apt install ./pirate-arcade_*.deb
```

### Windows

Download the latest `pirate-arcade.exe` from the [Releases](https://github.com/edonahue/pirate-arcade/releases) page or build from source:

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller pirate-arcade.spec
```

The executable will be in `dist/pirate-arcade/`.

### macOS

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller pirate-arcade.spec
```

The app bundle will be in `dist/pirate-arcade/`.

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
| F | Toggle FPS counter |

Refer to in-game help for game-specific controls.

## Building packages

### Debian package (Linux)

```bash
./build_deb.sh
```

Produces `dist/pirate-arcade_<version>_all.deb`.

### Windows / macOS standalone binary

```bash
pip install pyinstaller
pyinstaller pirate-arcade.spec
```

The spec file auto-detects your platform and produces a standalone executable.

## Continuous Integration

This project uses GitHub Actions to run tests on Ubuntu, macOS, and Windows on every push and pull request. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for details.

## Testing

```bash
pytest -v
```

Run with coverage:

```bash
pip install pytest-cov
pytest --cov=. --cov-report=term
```

## Screenshots

*Screenshots coming soon.*

## License

Distributed under the MIT License. See `LICENSE` for details.
