# LANpad — Cross-Platform LAN Trackpad & Keyboard Remote Control

Use your Mac trackpad, Windows/Linux PC, iPhone, or Android device to drive your computer's real mouse and keyboard with native fluid gestures and zero lag.

- **Nothing to install on the client**: Open the browser link in Chrome, click once to lock the pointer, and your trackpad and keyboard drive the host machine.
- **Dedicated Mobile App (Expo 58)**: Fullscreen touch trackpad, two-finger scroll, tap-to-click, and remote typing for iOS and Android.
- **Cross-Platform Host Support**: Runs on Linux (X11 / XTEST), Windows (user32 `SendInput`), and macOS (CoreGraphics).

---

## Quick Start

### Linux (Debian / Ubuntu)
Install from the `.deb` package or run from source:
```bash
# From package
sudo apt install ./lanpad_1.0.0_amd64.deb

# Or from source:
./install.sh
```

### Windows
Download and run `LANpad-Setup-1.0.0.exe` from GitHub Releases.

### macOS
```bash
brew install --cask mohamedjs/lanpad/lanpad
# Or download and unpack lanpad-macos-arm64-1.0.0.tar.gz
```

### Mobile App (iOS & Android — Expo 58)
```bash
cd mobile
npm install
npx expo start
```
Scan the QR code with Expo Go on your iPhone or Android device.

---

## Usage

When LANpad starts, it prints the connection URL on your local Wi-Fi:
```
  Open on your Mac/Client:  http://192.168.1.225:8765/#<secret-token>
```
Open that link in Chrome on your client device. The `#token` is the authentication secret; without it all requests return 403.

### CLI Commands
```bash
lanpad                  # Start server (or python3 server.py)
lanpad --tls            # Enable HTTPS (unlocks Chrome Keyboard Lock for Esc & Tab)
lanpad --port 9000      # Custom port (or LANPAD_PORT=9000)
lanpad --selftest       # Run full self-diagnostics
lanpad token            # Print current auth token
lanpad rotate-token     # Roll a new auth token
lanpad url              # Print client connection URL
```

### Linux Background Service
Installed as a per-user systemd service:
```bash
systemctl --user status lanpad        # check status
systemctl --user restart lanpad       # restart service
journalctl --user -u lanpad -f        # view live log
```

---

## Architecture (Modular Monolith)

LANpad follows a clean modular monolith architecture inspired by Lura:

```
src/lanpad/
├── app.py            ── CLI presentation layer
├── bootstrap.py      ── Composition root: wires modules and dependencies
├── selftest.py       ── Comprehensive diagnostics
├── shared/           ── Cross-platform kernel (paths, network, protocol, errors)
└── modules/
    ├── auth/         ── TokenService: constant-time validation & rotation
    ├── input/        ── Cross-platform mouse & keyboard controllers:
    │                    ├── linux.py   (X11 Xlib + XTEST)
    │                    ├── windows.py (ctypes user32 SendInput)
    │                    └── macos.py   (CoreGraphics / Quartz)
    └── server/       ── High-performance HTTP & WebSocket server
```

- **Zero-lag binary wire protocol**: Mouse movement transmits in 5-byte packed binary frames (`dx:i16 dy:i16`) instead of ~30 bytes of JSON.
- **Wi-Fi radio keepalive**: A 1-byte heartbeat is sent every 16ms during active capture so laptop Wi-Fi power-save never parks the radio mid-drag.
- **Sub-pixel pointer accumulation**: Sub-pixel trackpad remainders carry into the next tick to prevent pointer drift on slow movements.

---

## Landing Page

The project includes a public, bilingual (English & Arabic) responsive landing page in `site/`:
```bash
./site/build.sh
```
Builds into `_site/` and deploys automatically via `.github/workflows/pages.yml`.

---

## Packaging

Packaging definitions live in `packaging/`:
- `packaging/pyinstaller/lanpad.spec`: Multi-OS PyInstaller spec
- `packaging/linux/`: Debian `.deb`, desktop entry, and systemd service
- `packaging/windows/lanpad.iss`: Inno Setup installer
- `packaging/homebrew/lanpad.rb.tmpl`: macOS Homebrew cask formula
- `packaging/icons/`: High-resolution SVG, PNG, and ICO app icons

---

## License

MIT License. Crafted with precision by Mohamed.
