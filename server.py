#!/usr/bin/env python3
"""LAN remote mouse/keyboard for X11, controlled from a browser on another machine.

Run on the Ubuntu laptop:  python3 server.py
Then open the printed URL on the Mac (same WiFi).
"""
import json, os, secrets, socket, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("DISPLAY", ":0")

from Xlib import X, XK, display
from Xlib.ext import xtest

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "web", "dist")          # built React app (npm run build in web/)
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
        ".svg": "image/svg+xml", ".json": "application/json", ".ico": "image/x-icon"}
PORT = int(os.environ.get("LANPAD_PORT", 8765))

TOKEN_FILE = os.path.expanduser("~/.lanpad-token")   # outside the web root: Apache also serves this folder
if os.path.exists(TOKEN_FILE):
    TOKEN = open(TOKEN_FILE).read().strip()
else:
    TOKEN = secrets.token_urlsafe(9)
    open(TOKEN_FILE, "w").write(TOKEN)
    os.chmod(TOKEN_FILE, 0o600)

DISP = display.Display()
SCREEN = DISP.screen()
W, H = SCREEN.width_in_pixels, SCREEN.height_in_pixels
LOCK = threading.Lock()

MODS = ["Shift_L", "Control_L", "Alt_L", "Super_L"]

# Keysym names the React client sends (mirrors web/src/keymap.js — keep the two in step).
KEYSYMS = MODS + [
    "Shift_R", "Control_R", "Alt_R", "Super_R", "Return", "Escape", "BackSpace", "Tab",
    "space", "Caps_Lock", "Delete", "Insert", "minus", "equal", "bracketleft",
    "bracketright", "backslash", "semicolon", "apostrophe", "comma", "period", "slash",
    "grave", "less", "Up", "Down", "Left", "Right", "Home", "End", "Prior", "Next",
    "Num_Lock", "KP_Divide", "KP_Multiply", "KP_Subtract", "KP_Add", "KP_Decimal",
] + ["F%d" % i for i in range(1, 13)] + ["KP_%d" % i for i in range(10)]
_held = set()


def _keycode(name_or_char):
    """Return (keycode, needs_shift) or (0, False)."""
    if len(name_or_char) == 1 and 0x20 <= ord(name_or_char) <= 0x7E:
        ks = ord(name_or_char)  # ASCII printables are their own keysyms
    else:
        ks = XK.string_to_keysym(name_or_char)
    if not ks:
        return 0, False
    kc = DISP.keysym_to_keycode(ks)
    if not kc:
        return 0, False
    return kc, DISP.keycode_to_keysym(kc, 0) != ks


def _key(kc, down):
    xtest.fake_input(DISP, X.KeyPress if down else X.KeyRelease, kc)


def _tap(name_or_char):
    kc, shift = _keycode(name_or_char)
    if not kc:
        return
    skc = DISP.keysym_to_keycode(XK.string_to_keysym("Shift_L")) if shift else 0
    if skc:
        _key(skc, True)
    _key(kc, True)
    _key(kc, False)
    if skc:
        _key(skc, False)


def release_all():
    for name in list(_held):
        kc, _ = _keycode(name)
        if kc:
            _key(kc, False)
    _held.clear()
    for b in (1, 2, 3):
        xtest.fake_input(DISP, X.ButtonRelease, b)
    DISP.sync()


def apply(events):
    with LOCK:
        p = SCREEN.root.query_pointer()
        x, y = p.root_x, p.root_y
        for ev in events:
            kind = ev[0]
            if kind == "m":                                   # relative move
                x = min(W - 1, max(0, x + int(ev[1])))
                y = min(H - 1, max(0, y + int(ev[2])))
                xtest.fake_input(DISP, X.MotionNotify, x=x, y=y)
            elif kind == "b":                                 # button 1/2/3
                xtest.fake_input(DISP, X.ButtonPress if ev[2] else X.ButtonRelease, int(ev[1]))
            elif kind == "s":                                 # scroll ticks
                for b, n in ((5 if ev[2] > 0 else 4, abs(int(ev[2]))),
                             (7 if ev[1] > 0 else 6, abs(int(ev[1])))):
                    for _ in range(min(n, 10)):
                        xtest.fake_input(DISP, X.ButtonPress, b)
                        xtest.fake_input(DISP, X.ButtonRelease, b)
            elif kind == "k":                                 # hold/release a named key
                kc, _ = _keycode(ev[1])
                if kc:
                    _key(kc, bool(ev[2]))
                    _held.add(ev[1]) if ev[2] else _held.discard(ev[1])
            elif kind == "tap":                               # one named key, e.g. Return
                _tap(ev[1])
            elif kind == "type":                              # literal text, char by char
                for ch in ev[1]:
                    _tap(ch)
            elif kind == "rel":
                release_all()
        DISP.sync()


GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"    # RFC 6455 handshake constant


def ws_accept(key):
    import base64, hashlib
    return base64.b64encode(hashlib.sha1(key.encode() + GUID).digest()).decode()


def ws_frames(rfile):
    """Yield text payloads from a client. Client frames are always masked."""
    import struct
    while True:
        hdr = rfile.read(2)
        if len(hdr) < 2:
            return
        op, n = hdr[0] & 0x0F, hdr[1] & 0x7F
        if not hdr[1] & 0x80:                       # unmasked client frame: protocol error
            return
        if n == 126:
            n = struct.unpack(">H", rfile.read(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", rfile.read(8))[0]
        mask = rfile.read(4)
        data = bytearray(rfile.read(n))
        for i in range(n):
            data[i] ^= mask[i & 3]
        if op == 8:                                 # close
            return
        if op in (1, 2):                            # text / binary
            yield op, bytes(data)


def unpack(buf):
    """Compact wire format for the hot path — one byte of type, then the numbers.
    5 bytes for a move against ~30 for the JSON equivalent.
        1 dx:i16 dy:i16   move
        2 button:u8 down:u8
        3 dx:i8 dy:i8     scroll
    Keys stay JSON: they carry names, and they are rare."""
    import struct
    ev, i, n = [], 0, len(buf)
    while i < n:
        t = buf[i]
        if t == 1 and i + 5 <= n:
            ev.append(["m", *struct.unpack_from("<hh", buf, i + 1)]); i += 5
        elif t == 2 and i + 3 <= n:
            ev.append(["b", buf[i + 1], buf[i + 2]]); i += 3
        elif t == 3 and i + 3 <= n:
            ev.append(["s", *struct.unpack_from("<bb", buf, i + 1)]); i += 3
        else:
            break                                   # malformed: keep what parsed
    return ev


def ws_send(wfile, text):
    b = text.encode()
    wfile.write(bytes([0x81, len(b)]) + b)          # short unfragmented text frame
    wfile.flush()


_seen = [0.0, 0, {}]                                # [window start, posts, event kinds]


def log(ip, events):
    """One aggregate line per second — enough to debug, not enough to flood."""
    import time
    now = time.time()
    _seen[1] += 1
    for ev in events:
        _seen[2][ev[0]] = _seen[2].get(ev[0], 0) + 1
    if now - _seen[0] >= 1:
        print("%s  %d posts  %s" % (ip, _seen[1], _seen[2] or "(empty)"), flush=True)
        _seen[0], _seen[1], _seen[2] = now, 0, {}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True          # TCP_NODELAY: without it every reply waits ~40ms

    def log_message(self, *a):
        pass

    def _send(self, code, body=b"", ctype="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("Upgrade", "").lower() == "websocket":
            return self.websocket()
        path = self.path.split("?")[0].split("#")[0]
        rel = "index.html" if path == "/" else path.lstrip("/")
        f = os.path.normpath(os.path.join(DIST, rel))
        if not f.startswith(DIST) or not os.path.isfile(f):
            return self._send(404)
        ctype = MIME.get(os.path.splitext(f)[1], "application/octet-stream")
        if rel == "index.html":
            print("%s  loaded the page" % self.client_address[0], flush=True)
        self._send(200, open(f, "rb").read(), ctype)

    def websocket(self):
        """One long-lived connection, events streamed in, nothing sent back per event —
        no request/response round trip is what makes this feel immediate."""
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            return self._send(400)
        self.close_connection = True
        self.wfile.write(b"HTTP/1.1 101 Switching Protocols\r\n"
                         b"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                         b"Sec-WebSocket-Accept: " + ws_accept(key).encode() + b"\r\n\r\n")
        self.wfile.flush()
        ip, authed = self.client_address[0], False
        try:
            for op, payload in ws_frames(self.rfile):
                if op == 2:                         # binary: pointer events only
                    if not authed:
                        return
                    ev = unpack(payload)
                    log(ip, ev)
                    apply(ev)
                    continue
                try:
                    msg = json.loads(payload.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if "p" in msg:                      # latency probe: echo it straight back
                    ws_send(self.wfile, payload.decode())
                    continue
                if not authed:                      # first frame must be the token
                    if not secrets.compare_digest(str(msg.get("t", "")), TOKEN):
                        print("%s  ws bad token" % ip, flush=True)
                        ws_send(self.wfile, '{"error":"bad token"}')
                        return
                    authed = True
                    print("%s  ws connected" % ip, flush=True)
                    ws_send(self.wfile, '{"ok":true}')
                    continue
                log(ip, msg.get("ev", []))
                apply(msg.get("ev", []))
        except (OSError, ValueError):
            pass
        finally:
            release_all()                           # a dropped socket must not leave keys held
            print("%s  ws closed" % ip, flush=True)

    def do_POST(self):
        if self.path != "/e":
            return self._send(404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            msg = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._send(400)
        if not secrets.compare_digest(str(msg.get("t", "")), TOKEN):
            print("%s  403 bad token %r" % (self.client_address[0], str(msg.get("t", ""))[:12]), flush=True)
            return self._send(403, b"bad token")
        try:
            log(self.client_address[0], msg.get("ev", []))
            apply(msg.get("ev", []))
        except Exception as e:                      # never let one bad event kill the server
            return self._send(500, str(e).encode())
        self._send(204)


CERT = os.path.expanduser("~/.lanpad-cert.pem")


def tls_context(ip):
    """Self-signed cert, made once. Chrome warns about it, but once you click through,
    the page counts as a secure context — which is what switches on Keyboard Lock
    (Esc, Tab and the ⌘ combos stop being swallowed by macOS)."""
    import ssl, subprocess
    if not os.path.exists(CERT):
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", CERT, "-out", CERT, "-days", "3650",
                        "-subj", "/CN=lanpad",
                        "-addext", "subjectAltName=IP:%s,IP:127.0.0.1,DNS:localhost" % ip],
                       check=True, capture_output=True)
        os.chmod(CERT, 0o600)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT)
    return ctx


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def selftest():
    p0 = SCREEN.root.query_pointer()
    apply([["m", 50, 50]])
    p1 = SCREEN.root.query_pointer()
    assert (p1.root_x, p1.root_y) == (min(W - 1, p0.root_x + 50), min(H - 1, p0.root_y + 50)), "move failed"
    apply([["m", -50, -50]])
    for c in range(0x20, 0x7F):
        assert _keycode(chr(c))[0], "no keycode for %r" % chr(c)
    for name in KEYSYMS:                            # every name web/src/keymap.js can emit
        assert _keycode(name)[0], "no keycode for %s" % name
    import struct
    wire = (bytes([1]) + struct.pack("<hh", -3, 7) + bytes([2, 1, 1]) + bytes([3]) +
            struct.pack("<bb", 0, -2))
    assert unpack(wire) == [["m", -3, 7], ["b", 1, 1], ["s", 0, -2]], unpack(wire)
    assert unpack(bytes([1, 5])) == []              # truncated frame must not raise

    apply([["m", W * 2, H * 2]])                    # clamp must not crash or wedge
    assert SCREEN.root.query_pointer().root_x == W - 1
    apply([["m", -W * 2, -H * 2]])
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    if not os.path.isfile(os.path.join(DIST, "index.html")):
        sys.exit("web/dist is missing — run:  cd %s && npm install && npm run build" % os.path.join(HERE, "web"))
    ip, tls = lan_ip(), "--tls" in sys.argv or os.environ.get("LANPAD_TLS") == "1"
    print("\n  Open on your Mac:  %s://%s:%d/#%s\n" % ("https" if tls else "http", ip, PORT, TOKEN))
    if tls:
        print("  Chrome will warn about the certificate — Advanced, then Proceed.")
        print("  That unlocks Esc, Tab and the Cmd keys, which macOS otherwise keeps.\n")
    try:
        httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
        if tls:
            httpd.socket = tls_context(ip).wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    except OSError as e:
        sys.exit("port %d busy — it's probably already running (%s)" % (PORT, e))
    except KeyboardInterrupt:
        release_all()
        print("bye")
