# PyInstaller spec for LANpad across platforms: `pyinstaller packaging/pyinstaller/lanpad.spec`
# -*- mode: python -*-
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve().parents[1]
SRC = ROOT / "src"
DIST_WEB = ROOT / "web" / "dist"
ICON_PNG = ROOT / "packaging" / "icons" / "lanpad.png"
ICON_ICO = ROOT / "packaging" / "icons" / "lanpad.ico"

datas = []
if DIST_WEB.exists():
    datas.append((str(DIST_WEB), "lanpad/web/dist"))

binaries = []
hidden = collect_submodules("lanpad")

if sys.platform.startswith("linux"):
    for pkg in ("Xlib",):
        try:
            d, b, h = collect_all(pkg)
            datas += d
            binaries += b
            hidden += h
        except Exception:
            pass

a = Analysis(
    [str(Path(SPECPATH) / "entry.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="lanpad",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(ICON_ICO if sys.platform.startswith("win") else ICON_PNG),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="lanpad",
)
