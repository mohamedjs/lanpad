# LANpad — use the Mac's own keyboard and mouse on this Ubuntu laptop

The Mac opens a page, clicks once, and from then on its **real trackpad/mouse and
keyboard drive Ubuntu** (Pointer Lock + key forwarding). Press `Esc` to hand them back.
Nothing to install on the Mac.

## Run (on the Ubuntu laptop)

It is installed as a user service, so it starts when you log in and stops when you log
out — a logout kills the X server it drives, and a server left running past that accepts
input and silently drops it:

    systemctl --user status lanpad        # is it up?
    systemctl --user restart lanpad       # after changing server.py
    journalctl --user -u lanpad -f        # live log

To run it by hand instead, stop the service first (`systemctl --user stop lanpad`):

    python3 /var/www/html/lanpad/server.py

It prints e.g. `http://192.168.1.225:8765/#<token>` — open that in **Chrome on the Mac**.
The `#token` is the password; without it every request is 403.

## What it is

- `server.py` — stdlib HTTP + WebSocket server (hand-rolled, no library) + python-xlib
  XTEST. No dependencies, no sudo, no apt. Serves the built React app and takes input over
  one socket: pointer moves, buttons and scroll as 5- and 3-byte binary frames, keys as
  JSON (they carry names). `POST /e` still works as a fallback.
- `web/` — React (Vite). `npm install && npm run build` writes `web/dist/`, which the
  server serves. Rebuild after any change under `web/src/`.

## Trackpad gestures

- move, tap-to-click and two-finger tap (right click) come through as-is
- two-finger scroll is accumulated and converted to X11 scroll clicks, so momentum
  scrolling glides instead of jumping; horizontal swipe scrolls sideways
- pinch is sent as Ctrl+scroll, which is what Ubuntu apps read as zoom
- flip the **natural scrolling** switch if the direction feels backwards
- **two-finger flicks left/right** switch workspace (toggle **swipe ←→ workspace**).
  Up and down are scrolling only — a browser cannot count fingers on the trackpad, so a
  vertical flick and a fast scroll are the same event
- for overview and minimize without gestures, use the keys: **⌘ alone** opens the overview
  (⌘ is sent as Super), **⌘D** shows the desktop, **⌘H** minimizes. These need the tunnel
  (Keyboard Lock), otherwise macOS eats them.
- the page blocks Chrome's swipe-to-go-back and pinch-to-zoom, so a stray gesture can't
  navigate the Mac away from the session. macOS space switching is above the browser and
  can't be blocked — run the page **fullscreen** so a space swipe has nowhere to go
- **three- and four-finger gestures are eaten by macOS** — they never reach the browser,
  so no web page can forward them. To get real three-finger swipes, map them on the Mac
  to a keyboard shortcut (BetterTouchTool, or Karabiner): the browser *does* receive
  keystrokes, so whatever you map them to gets forwarded like any other key.

## Limits worth knowing before you hit them

- **macOS keeps ⌘Tab, ⌘Space and ⌘Q for itself** — they never reach the browser, so they
  can't be forwarded. No web page can fix this.
- `Esc` releases the capture instead of reaching Ubuntu, unless Chrome's Keyboard Lock is
  active — that needs a **secure context**, so it only kicks in over https or localhost.
  Over plain http on the LAN you get everything except `Esc` and `Tab`.
- Use **Chrome**. Safari's Pointer Lock is fussier and it has no Keyboard Lock.
- If the status line ever says *"cannot capture the mouse here"*, run it through an SSH
  tunnel from the Mac — `ssh -L 8765:localhost:8765 mohamed@192.168.1.225`, then open
  `http://localhost:8765/#<token>`. localhost counts as a secure context, which brings
  back Keyboard Lock (and with it `Esc` and `Tab`).
- ⌘ is sent as Ubuntu's Super by default; the dropdown can send it as Ctrl instead
  (so ⌘C = copy on Ubuntu) or Alt.
- X11 only (this laptop is X11). Wayland would need `ydotool` and a uinput permission.
- One Mac at a time; no clipboard sharing, no drag-and-drop between machines. If you want
  those plus edge-of-screen switching, that's Input Leap/Barrier — installed on both machines.

## Housekeeping

- Port: `LANPAD_PORT=9000 python3 server.py`
- Password lives at `~/.lanpad-token` (outside the web root, since Apache also serves
  `/var/www/html`). Delete it and restart to roll a new one.
- Check the input path still works: `python3 server.py --selftest` — it asserts pointer
  moves, clamping at the screen edge, and that every keysym the client can send maps to a
  real keycode.
- Stop it: `systemctl --user stop lanpad` (and `disable` to stop it starting at login).
