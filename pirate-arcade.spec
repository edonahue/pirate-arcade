# -*- mode: python ; coding: utf-8 -*-
import sys
import platform

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('games', 'games'),
        ('constants.py', '.'),
        ('launcher.py', '.'),
        ('renderer.py', '.'),
        ('audio.py', '.'),
        ('highscores.py', '.'),
        ('util.py', '.'),
        ('icon.svg', '.'),
        ('icon.ico', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'pygame',
        'pygame.gfxdraw',
        'numpy',
        'games',
        'games.pong',
        'games.pong.game',
        'games.pong.menu',
        'games.pong.gameplay',
        'games.pong.paddle',
        'games.pong.ball',
        'games.pong.powerup',
        'games.pong.ai',
        'games.breakout',
        'games.breakout.game',
        'games.breakout.gameplay',
        'games.breakout.paddle',
        'games.breakout.ball',
        'games.breakout.brick',
        'games.asteroids',
        'games.asteroids.game',
        'games.asteroids.gameplay',
        'games.asteroids.ship',
        'games.asteroids.barrel',
        'games.asteroids.cannonball',
        'games.asteroids.treasure',
        'games.pirate_dominion',
        'games.pirate_dominion.game',
        'games.pirate_dominion.menu',
        'games.pirate_dominion.gameplay',
        'games.pirate_dominion.board',
        'games.pirate_dominion.ui',
        'games.pirate_dominion.player',
        'games.pirate_dominion.save_load',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'tkinter.*',
        'test',
        'unittest',
        'pytest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pirate-arcade',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if platform.system() == 'Darwin':
    app = BUNDLE(
        exe,
        name='pirate-arcade.app',
        icon=None,
        bundle_identifier='com.pirate-arcade.app',
        info_plist={
            'CFBundleShortVersionString': '2.0.0',
            'CFBundleVersion': '2.0.0',
            'NSHighResolutionCapable': True,
        },
    )
elif platform.system() == 'Windows':
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='pirate-arcade',
    )
