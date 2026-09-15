# LANpad — use the Mac's own keyboard and mouse on this Ubuntu laptop

The Mac opens a page, clicks once, and from then on its **real trackpad/mouse and
keyboard drive Ubuntu** (Pointer Lock + key forwarding). Press `Esc` to hand them back.
Nothing to install on the Mac.

## Run (on the Ubuntu laptop, as your own user, inside the desktop session)

    python3 /var/www/html/lanpad/server.py

It prints e.g. `http://192.168.1.225:8765/#<token>` — open that in **Chrome on the Mac**.
The `#token` is the password; without it every request is 403.

## What it is

- `server.py` — stdlib HTTP server + python-xlib XTEST. No dependencies, no sudo, no apt.
  Serves the built React app and takes batched input events on `POST /e`.
- `web/` — React (Vite). `npm install && npm run build` writes `web/dist/`, which the
  server serves. Rebuild after any change under `web/src/`.

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
- Stop it: `pgrep -af 'server\.py'` then `kill <pid>`.
