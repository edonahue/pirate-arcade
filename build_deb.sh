#!/usr/bin/env bash
set -e

VERSION="2.0.0"
PKG="pirate-arcade"
BUILD_DIR="build/${PKG}"
DIST_DIR="dist"

rm -rf "build" "${DIST_DIR}"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILD_DIR}/usr/share/${PKG}"

# Copy game source
cp -r main.py launcher.py highscores.py constants.py renderer.py audio.py util.py requirements.txt "${BUILD_DIR}/usr/share/${PKG}/"
cp -r games "${BUILD_DIR}/usr/share/${PKG}/games"
find "${BUILD_DIR}" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Bundle AVX2-optimized pygame if available
if [ -f /tmp/python3-pygame_2.5.2-2_amd64.deb ]; then
    cp /tmp/python3-pygame_2.5.2-2_amd64.deb "${BUILD_DIR}/usr/share/${PKG}/"
fi

# Icon
cp icon.svg "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/${PKG}.svg"

# Convert SVG to PNG for non-SVG-capable environments
if command -v convert &> /dev/null; then
    convert icon.svg -resize 256x256 "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps/${PKG}.png"
elif command -v rsvg-convert &> /dev/null; then
    rsvg-convert icon.svg -w 256 -h 256 -o "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps/${PKG}.png"
else
    echo "Warning: No SVG-to-PNG converter found. Skip PNG icon — SVG will be used."
fi

cat > "${BUILD_DIR}/usr/share/applications/${PKG}.desktop" << EOF
[Desktop Entry]
Name=Pirate Arcade
Comment=A pirate-themed arcade game collection: Cannonball Clash, Treasure Cove, Kraken's Wake, and Port Royale Tycoon
Exec=/usr/bin/${PKG}
Type=Application
Categories=Game;ArcadeGame;
Keywords=Arcade;Game;Pirate;Pong;Breakout;Asteroids;Monopoly;
Icon=${PKG}
Terminal=false
EOF

cat > "${BUILD_DIR}/usr/bin/${PKG}" << 'EOF'
#!/bin/bash
cd /usr/share/pirate-arcade
exec python3 main.py "$@"
EOF
chmod +x "${BUILD_DIR}/usr/bin/${PKG}"

SIZE=$(du -s "${BUILD_DIR}/usr" | cut -f1)

cat > "${BUILD_DIR}/DEBIAN/control" << EOF
Package: ${PKG}
Version: ${VERSION}
Section: games
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-pygame (>= 2.5.0), python3-numpy
Maintainer: Erich Donahue <edonahue@users.noreply.github.com>
Description: Pirate Arcade — a pirate-themed arcade game collection
 A collection of pirate-themed arcade games including Cannonball Clash
 (paddle ball), Treasure Cove (brick breaker), Kraken's Wake (space shooter),
 and Port Royale Tycoon (Monopoly-style strategy), optimized for modern
 hardware with glow effects, particles, and smooth rendering at high
 refresh rates.
Installed-Size: ${SIZE}
Homepage: https://github.com/edonahue/pirate-arcade
EOF

cat > "${BUILD_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/sh
set -e

AVX2_DEB="/usr/share/pirate-arcade/python3-pygame_2.5.2-2_amd64.deb"
if [ -f "$AVX2_DEB" ]; then
    dpkg -i "$AVX2_DEB" 2>/dev/null || true
fi

if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database
fi
if [ -x /usr/sbin/update-icon-caches ]; then
    update-icon-caches /usr/share/icons/hicolor
fi
exit 0
EOF
chmod +x "${BUILD_DIR}/DEBIAN/postinst"

mkdir -p "${DIST_DIR}"
dpkg-deb --build "${BUILD_DIR}" "${DIST_DIR}/${PKG}_${VERSION}_all.deb"
echo "Built: ${DIST_DIR}/${PKG}_${VERSION}_all.deb"
