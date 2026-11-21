# -*- mode: python ; coding: utf-8 -*-
import sys
# Space Werewolf cross-platform build configuration
# Entry point is the multiplayer lobby; the same executable starts the game with --game.
# Bundle pictures/ for the Morse-code and body-scan tasks.


a = Analysis(
    ['multiplayer.py'],
    pathex=[],
    binaries=[],
    datas=[('pictures', 'pictures')],
    hiddenimports=['main_gui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Space Werewolf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2' if sys.platform == 'darwin' else None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Space Werewolf',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Space Werewolf.app',
        icon=None,
        bundle_identifier='com.songandy39.space-werewolf',
    )
