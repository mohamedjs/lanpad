# LANpad Mobile App (Expo 58)

Cross-platform mobile remote control app for iOS and Android. Turns your smartphone or tablet into a fluid touchpad and wireless keyboard for your desktop.

## Features
- **Fluid Trackpad Surface**: Single-finger move with acceleration and tap-to-click.
- **Two-Finger Gestures**: Two-finger tap for right-click and two-finger vertical/horizontal scrolling.
- **Dedicated Buttons**: Left Click and Right Click tactile buttons.
- **Direct Keystroke Typing**: Instant keyboard input forwarded to the host desktop.
- **Zero Configuration Discovery**: Connect via LAN IP, port, and security token.
- **Sub-millisecond RTT**: Real-time round-trip latency indicator.

## Running with Expo 58

### Prerequisites
- Node.js 18+
- [Expo Go](https://expo.dev/go) app installed on your iPhone or Android device.

### Development
```bash
cd mobile
npm install
npx expo start
```
Scan the QR code displayed in the terminal with your phone's camera (iOS) or the Expo Go app (Android).

## Building Standalone Binaries (EAS Build)
To build standalone `.apk` for Android or `.ipa` for iOS:
```bash
npm install -g eas-cli
eas login
eas build -p android --profile preview
eas build -p ios --profile preview
```
