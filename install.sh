#!/usr/bin/env bash
# Install LANpad from source on Linux as a per-user background service.
# Safe to re-run: upgrades in place and leaves existing configuration and tokens intact.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

say() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\n\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Run this as yourself, not root. It installs into your user space."

say "Checking system packages"
NEEDED=()
python3 -c 'import Xlib' 2>/dev/null || NEEDED+=("python3-xlib")
command -v node >/dev/null || NEEDED+=("nodejs")
command -v npm >/dev/null || NEEDED+=("npm")

if [ ${#NEEDED[@]} -gt 0 ]; then
  echo "Installing dependencies with apt:"
  printf '  - %s\n' "${NEEDED[@]}"
  sudo apt-get update
  sudo apt-get install -y "${NEEDED[@]}"
else
  echo "All system dependencies present."
fi

say "Building web client"
if [ -d "$HERE/web" ]; then
  cd "$HERE/web"
  npm install --silent
  npm run build
  cd "$HERE"
fi

say "Verifying LANpad selftest"
PYTHONPATH="$HERE/src" python3 -m lanpad.selftest

say "Installing user systemd service"
mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/lanpad.service" <<SERVICE
[Unit]
Description=LANpad — Cross-platform keyboard and mouse remote service
After=graphical-session.target

[Service]
Type=simple
Environment=PYTHONPATH=$HERE/src
ExecStart=/usr/bin/python3 $HERE/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=graphical-session.target
SERVICE

systemctl --user daemon-reload
systemctl --user enable lanpad.service >/dev/null
systemctl --user restart lanpad.service

say "LANpad service is up and running!"
systemctl --user --no-pager --lines=5 status lanpad.service || true
