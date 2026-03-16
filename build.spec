# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

project_root = Path.cwd()

datas = [
    ("README.md", "."),
    ("PLATFORM-INSTRUCTIONS.md", "."),
]

binaries = collect_dynamic_libs("PySide6")
hiddenimports = collect_submodules("PySide6.QtMultimedia")

a = Analysis(
    ["app/app.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name="Duplicate Music Finder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Duplicate Music Finder.app",
        icon=None,
        bundle_identifier="com.stavikmusic.duplicatemusicfinder",
    )
