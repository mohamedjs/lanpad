#!/usr/bin/env bash
# Package the PyInstaller folder (dist/lanpad) as a .deb for Debian/Ubuntu.
#   packaging/linux/build-deb.sh 1.0.0 [amd64]
set -euo pipefail

VERSION="${1:-1.0.0}"
ARCH="${2:-amd64}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
DIST="$ROOT/dist/lanpad"

[ -x "$DIST/lanpad" ] || { echo "Build first: pyinstaller packaging/pyinstaller/lanpad.spec" >&2; exit 1; }

PKG="$(mktemp -d)/lanpad_${VERSION}_${ARCH}"
mkdir -p "$PKG/DEBIAN" "$PKG/opt" "$PKG/usr/bin" "$PKG/usr/share/applications" \
         "$PKG/usr/share/icons/hicolor/512x512/apps" "$PKG/usr/lib/systemd/user" \
         "$PKG/usr/share/doc/lanpad"

cp -a "$DIST" "$PKG/opt/lanpad"
ln -s /opt/lanpad/lanpad "$PKG/usr/bin/lanpad"
install -m644 "$HERE/lanpad.desktop" "$PKG/usr/share/applications/lanpad.desktop"
install -m644 "$HERE/lanpad.service" "$PKG/usr/lib/systemd/user/lanpad.service"
install -m644 "$ROOT/packaging/icons/lanpad.png" "$PKG/usr/share/icons/hicolor/512x512/apps/lanpad.png"

SIZE="$(du -sk "$PKG" | cut -f1)"
cat > "$PKG/DEBIAN/control" <<CONTROL
Package: lanpad
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Installed-Size: $SIZE
Maintainer: Mohamed <mohamed@tripklik.com>
Homepage: https://github.com/mohamedjs/lanpad
Depends: libc6, libxtst6, libx11-6
Description: Zero-lag LAN remote trackpad and keyboard
 Use your Mac, Windows, Linux, iOS or Android device to drive your computer's
 real mouse and keyboard with smooth gestures, pointer lock, and low-latency WebSockets.
CONTROL

cat > "$PKG/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q /usr/share/icons/hicolor || true
for u in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
  systemctl --user -M "$u@" daemon-reload 2>/dev/null || true
  systemctl --user -M "$u@" try-restart lanpad.service 2>/dev/null || true
done
echo "LANpad is installed. Run: lanpad or open it from your applications menu."
POSTINST

chmod 755 "$PKG/DEBIAN/postinst"

mkdir -p "$ROOT/dist"
dpkg-deb --build --root-owner-group "$PKG" "$ROOT/dist/lanpad_${VERSION}_${ARCH}.deb"
echo "Built dist/lanpad_${VERSION}_${ARCH}.deb"
