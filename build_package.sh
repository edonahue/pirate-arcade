#!/usr/bin/env bash
set -e

echo "=== Pirate Arcade Package Builder ==="
echo ""

# Detect platform
OS="$(uname -s)"

case "$OS" in
    Linux)
        echo "Platform: Linux"
        echo ""
        echo "Building Debian package..."
        ./build_deb.sh
        echo "Done: dist/pirate-arcade_*.deb"
        ;;
    Darwin)
        echo "Platform: macOS"
        echo ""
        echo "Building macOS .app bundle with PyInstaller..."
        if ! command -v pyinstaller &> /dev/null; then
            echo "Installing PyInstaller..."
            pip install pyinstaller
        fi
        # Generate ICNS from SVG if iconutil available
        if command -v iconutil &> /dev/null; then
            echo "Generating .icns icon..."
            mkdir -p pirate-arcade.iconset
            for s in 16 32 64 128 256 512; do
                rsvg-convert icon.svg -w $s -h $s -o "pirate-arcade.iconsets/icon_${s}x${s}.png"
                rsvg-convert icon.svg -w $((s*2)) -h $((s*2)) -o "pirate-arcade.iconsets/icon_${s}x${s}@2x.png"
            done
            iconutil -c icns pirate-arcade.iconset
            rm -rf pirate-arcade.iconset
        fi
        pyinstaller pirate-arcade.spec
        echo ""
        echo "Done: dist/pirate-arcade.app/"
        echo "To create a .dmg, run:"
        echo "  hdiutil create -volname 'Pirate Arcade' -srcfolder dist/pirate-arcade.app -ov -format UDZO dist/pirate-arcade.dmg"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Platform: Windows"
        echo ""
        echo "Building Windows executable with PyInstaller..."
        pip install pyinstaller
        pyinstaller pirate-arcade.spec
        echo ""
        echo "Done: dist/pirate-arcade/"
        echo "You can zip this folder for distribution."
        ;;
    *)
        echo "Unknown platform: $OS"
        echo "Supported platforms: Linux, macOS, Windows (MINGW/MSYS/CYGWIN)"
        exit 1
        ;;
esac
