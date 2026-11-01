"""Linux input backend driving X11 via python-xlib and XTEST extension."""

import os
import threading
from typing import List, Set, Tuple

os.environ.setdefault("DISPLAY", ":0")

try:
    from Xlib import X, XK, display
    from Xlib.ext import xtest
except ImportError:
    display = None
    X = None
    XK = None
    xtest = None

from ...shared.errors import InputBackendError
from ...shared.protocol import KEYSYMS, MODS


class LinuxX11InputBackend:
    """Linux X11 implementation of InputBackend."""

    def __init__(self):
        if display is None or xtest is None:
            raise InputBackendError("python-xlib is not installed. Run: pip install python-xlib")
        try:
            self.disp = display.Display()
            self.screen = self.disp.screen()
            self.w = self.screen.width_in_pixels
            self.h = self.screen.height_in_pixels
        except Exception as e:
            raise InputBackendError(f"Could not connect to X11 display: {e}")

        self.lock = threading.Lock()
        self.held: Set[str] = set()

    def get_screen_size(self) -> Tuple[int, int]:
        return (self.w, self.h)

    def get_pointer_pos(self) -> Tuple[int, int]:
        p = self.screen.root.query_pointer()
        return (p.root_x, p.root_y)

    def keycode(self, name_or_char: str) -> Tuple[int, bool]:
        """Return (keycode, needs_shift) or (0, False)."""
        if len(name_or_char) == 1 and 0x20 <= ord(name_or_char) <= 0x7E:
            ks = ord(name_or_char)
        else:
            ks = XK.string_to_keysym(name_or_char)
        if not ks:
            return 0, False
        kc = self.disp.keysym_to_keycode(ks)
        if not kc:
            return 0, False
        return kc, self.disp.keycode_to_keysym(kc, 0) != ks

    def _key(self, kc: int, down: bool) -> None:
        xtest.fake_input(self.disp, X.KeyPress if down else X.KeyRelease, kc)

    def _tap(self, name_or_char: str) -> None:
        kc, shift = self.keycode(name_or_char)
        if not kc:
            return
        skc = self.disp.keysym_to_keycode(XK.string_to_keysym("Shift_L")) if shift else 0
        if skc:
            self._key(skc, True)
        self._key(kc, True)
        self._key(kc, False)
        if skc:
            self._key(skc, False)

    def release_all(self) -> None:
        with self.lock:
            for name in list(self.held):
                kc, _ = self.keycode(name)
                if kc:
                    self._key(kc, False)
            self.held.clear()
            for b in (1, 2, 3):
                xtest.fake_input(self.disp, X.ButtonRelease, b)
            self.disp.sync()

    def apply(self, events: List[List]) -> None:
        with self.lock:
            p = self.screen.root.query_pointer()
            x, y = p.root_x, p.root_y
            for ev in events:
                if not ev:
                    continue
                kind = ev[0]
                if kind == "m":  # relative motion
                    x = min(self.w - 1, max(0, x + int(ev[1])))
                    y = min(self.h - 1, max(0, y + int(ev[2])))
                    xtest.fake_input(self.disp, X.MotionNotify, x=x, y=y)
                elif kind == "b":  # button press / release
                    xtest.fake_input(self.disp, X.ButtonPress if ev[2] else X.ButtonRelease, int(ev[1]))
                elif kind == "s":  # scroll ticks
                    for b, n in (
                        (5 if ev[2] > 0 else 4, abs(int(ev[2]))),
                        (7 if ev[1] > 0 else 6, abs(int(ev[1]))),
                    ):
                        for _ in range(min(n, 10)):
                            xtest.fake_input(self.disp, X.ButtonPress, b)
                            xtest.fake_input(self.disp, X.ButtonRelease, b)
                elif kind == "k":  # hold / release a named key
                    kc, _ = self.keycode(ev[1])
                    if kc:
                        self._key(kc, bool(ev[2]))
                        if ev[2]:
                            self.held.add(ev[1])
                        else:
                            self.held.discard(ev[1])
                elif kind == "tap":  # tap a named key
                    self._tap(ev[1])
                elif kind == "type":  # literal text
                    for ch in ev[1]:
                        self._tap(ch)
                elif kind == "rel":
                    self.release_all()
            self.disp.sync()

    def selftest(self) -> None:
        p0 = self.screen.root.query_pointer()
        self.apply([["m", 50, 50]])
        p1 = self.screen.root.query_pointer()
        assert (p1.root_x, p1.root_y) == (
            min(self.w - 1, p0.root_x + 50),
            min(self.h - 1, p0.root_y + 50),
        ), "pointer move failed"
        self.apply([["m", -50, -50]])
        for c in range(0x20, 0x7F):
            assert self.keycode(chr(c))[0], f"no keycode for {chr(c)!r}"
        for name in KEYSYMS:
            assert self.keycode(name)[0], f"no keycode for {name}"
        self.apply([["m", self.w * 2, self.h * 2]])
        assert self.screen.root.query_pointer().root_x == self.w - 1
        self.apply([["m", -self.w * 2, -self.h * 2]])
