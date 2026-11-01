"""Cross-platform configuration, cache, and asset paths for LANpad."""

import os
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """Return the configuration directory for the current platform."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        p = Path(base) / "lanpad"
    elif sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "lanpad"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        p = Path(xdg) / "lanpad" if xdg else Path.home() / ".config" / "lanpad"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_token_file() -> Path:
    """Return the path to the auth token file.
    Preserves backward compatibility with ~/.lanpad-token on Linux/Unix.
    """
    legacy = Path.home() / ".lanpad-token"
    if legacy.exists():
        return legacy
    return get_config_dir() / "token"


def get_cert_file() -> Path:
    """Return the path to the TLS certificate file."""
    legacy = Path.home() / ".lanpad-cert.pem"
    if legacy.exists():
        return legacy
    return get_config_dir() / "cert.pem"


def get_dist_dir() -> Path:
    """Return the path to the built web client assets."""
    # PyInstaller bundled assets
    if hasattr(sys, "_MEIPASS"):
        meipass_dist = Path(sys._MEIPASS) / "lanpad" / "web" / "dist"
        if meipass_dist.is_dir():
            return meipass_dist
        meipass_direct = Path(sys._MEIPASS) / "web" / "dist"
        if meipass_direct.is_dir():
            return meipass_direct

    # Development or source checkout
    root = Path(__file__).resolve().parents[3]  # src/lanpad/shared/paths.py -> root
    dist = root / "web" / "dist"
    if dist.is_dir():
        return dist

    alt = Path(__file__).resolve().parent.parent / "web" / "dist"
    if alt.is_dir():
        return alt

    return dist
