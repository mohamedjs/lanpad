#!/usr/bin/env python3
"""LAN remote mouse/keyboard for X11/Windows/macOS, controlled from a browser or app.

Run on the host machine:  python3 server.py
Then open the printed URL on the client (same WiFi).
"""
import os
import sys

# Ensure src/ is on Python search path
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from lanpad.app import main
from lanpad.bootstrap import build_container
from lanpad.modules.auth import TokenService
from lanpad.modules.input import get_input_backend
from lanpad.shared.paths import get_dist_dir, get_token_file
from lanpad.shared.protocol import KEYSYMS, MODS, unpack, ws_accept, ws_frames, ws_send

# Backward-compatible exports
_container = None


def _get_compat_container():
    global _container
    if _container is None:
        _container = build_container()
    return _container


def apply(events):
    return _get_compat_container().input_backend.apply(events)


def release_all():
    return _get_compat_container().input_backend.release_all()


def selftest():
    from lanpad.selftest import run_selftest

    return run_selftest()


DIST = str(get_dist_dir())
PORT = int(os.environ.get("LANPAD_PORT", 8765))
TOKEN = TokenService().token

if __name__ == "__main__":
    main()
