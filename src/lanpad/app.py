"""CLI presentation layer and lifecycle entrypoint for LANpad."""

import argparse
import os
import shutil
import socket
import sys
from pathlib import Path

from . import __version__
from .composition_root import build_container
from .modules.window import launch_native_window
from .selftest import run_selftest
from .shared.network import get_lan_ip
from .shared.paths import get_config_dir, get_dist_dir


def run_doctor() -> int:
    """Verify OS dependencies, permissions, display, and network requirements."""
    checks = []

    # 1. Python version
    py_ok = sys.version_info >= (3, 9)
    checks.append(
        (
            f"Python {sys.version_info.major}.{sys.version_info.minor}",
            py_ok,
            "Install Python 3.9 or newer",
        )
    )

    # 2. Display / OS subsystem
    if sys.platform.startswith("linux"):
        disp = os.environ.get("DISPLAY")
        xlib_ok = False
        try:
            import Xlib  # noqa: F401
            xlib_ok = True
        except ImportError:
            pass
        checks.append(("X11 DISPLAY set", bool(disp), "Export DISPLAY=:0"))
        checks.append(("python-xlib installed", xlib_ok, "pip install python-xlib"))
    elif sys.platform.startswith("win"):
        checks.append(("Windows user32 SendInput", True, "N/A"))
    elif sys.platform == "darwin":
        checks.append(("macOS CoreGraphics framework", True, "N/A"))

    # 3. Web client build
    dist = get_dist_dir()
    index_ok = (dist / "index.html").is_file()
    checks.append(
        ("Web client assets (web/dist/index.html)", index_ok, "cd web && npm install && npm run build")
    )

    # 4. Port availability
    port = int(os.environ.get("LANPAD_PORT", 8765))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", port))
        port_ok = True
    except OSError:
        port_ok = False
    finally:
        s.close()
    checks.append(
        (
            f"TCP Port {port} available",
            port_ok,
            f"Port {port} is in use (service is already active, or check PID with lsof -i :{port})",
        )
    )

    print("LANpad Doctor System Diagnostics:\n")
    all_ok = True
    for name, ok, fix in checks:
        status = "\033[1;32m[PASS]\033[0m" if ok else "\033[1;31m[FAIL]\033[0m"
        print(f"  {status} {name}")
        if not ok:
            print(f"         Fix: {fix}")
            all_ok = False

    print()
    return 0 if all_ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lanpad",
        description="LANpad — Cross-platform LAN trackpad & keyboard remote control",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"lanpad {__version__}",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("LANPAD_PORT", 8765)),
        help="Port to listen on (default: 8765 or LANPAD_PORT env)",
    )
    parser.add_argument(
        "--tls",
        action="store_true",
        default=os.environ.get("LANPAD_TLS") == "1",
        help="Enable self-signed HTTPS/WSS (enables Chrome Keyboard Lock)",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Do not open native window when starting service",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run self diagnostics and exit",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "serve", "dashboard", "window", "doctor", "selftest", "token", "url", "rotate-token"],
        help="Command to run (default: run)",
    )

    args = parser.parse_args()

    if args.selftest or args.command == "selftest":
        sys.exit(run_selftest())

    if args.command == "doctor":
        sys.exit(run_doctor())

    container = build_container(port=args.port, tls=args.tls)

    proto = "https" if args.tls else "http"
    ip = get_lan_ip()
    client_url = f"{proto}://{ip}:{args.port}/#{container.token_service.token}"

    if args.command == "token":
        print(container.token_service.token)
        sys.exit(0)

    if args.command == "rotate-token":
        new_token = container.token_service.rotate()
        print(f"New token: {new_token}")
        sys.exit(0)

    if args.command == "url":
        print(client_url)
        sys.exit(0)

    if args.command in ("dashboard", "window"):
        print(f"Opening LANpad native window: {client_url}")
        launch_native_window(client_url, get_config_dir())
        sys.exit(0)

    # Validate web/dist assets exist
    dist = get_dist_dir()
    if not (dist / "index.html").is_file():
        sys.exit(
            f"web/dist is missing — run: cd {dist.parent} && npm install && npm run build"
        )

    if not args.no_window and args.command == "run":
        # Launch window in background if on desktop
        try:
            launch_native_window(client_url, get_config_dir())
        except Exception:
            pass

    container.server.start()


if __name__ == "__main__":
    main()
