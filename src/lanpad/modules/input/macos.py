"""macOS input backend using ApplicationServices / CoreGraphics via ctypes."""

import ctypes
import sys
import threading
from typing import List, Set, Tuple

from ...shared.errors import InputBackendError

# macOS Virtual Keycodes
MAC_VK = {
    "Return": 0x24,
    "Tab": 0x30,
    "space": 0x31,
    "BackSpace": 0x33,
    "Escape": 0x35,
    "Super_L": 0x37,
    "Super_R": 0x36,
    "Shift_L": 0x38,
    "Shift_R": 0x3C,
    "Caps_Lock": 0x39,
    "Alt_L": 0x3A,
    "Alt_R": 0x3D,
    "Control_L": 0x3B,
    "Control_R": 0x3E,
    "Left": 0x7B,
    "Right": 0x7C,
    "Down": 0x7D,
    "Up": 0x7E,
    "Delete": 0x75,
    "Home": 0x73,
    "End": 0x77,
    "Prior": 0x74,  # Page Up
    "Next": 0x79,   # Page Down
    "F1": 0x7A,
    "F2": 0x78,
    "F3": 0x63,
    "F4": 0x76,
    "F5": 0x60,
    "F6": 0x61,
    "F7": 0x62,
    "F8": 0x64,
    "F9": 0x65,
    "F10": 0x6D,
    "F11": 0x67,
    "F12": 0x6F,
}

# Letter and number keycodes on standard US layout
_CHARS = "asdfhgzxcv"
for idx, ch in enumerate(_CHARS):
    MAC_VK[ch] = idx
MAC_VK["b"] = 11
MAC_VK["q"] = 12
MAC_VK["w"] = 13
MAC_VK["e"] = 14
MAC_VK["r"] = 15
MAC_VK["y"] = 16
MAC_VK["t"] = 17
MAC_VK["1"] = 18
MAC_VK["2"] = 19
MAC_VK["3"] = 20
MAC_VK["4"] = 21
MAC_VK["6"] = 22
MAC_VK["5"] = 23
MAC_VK["equal"] = 24
MAC_VK["9"] = 25
MAC_VK["7"] = 26
MAC_VK["minus"] = 27
MAC_VK["8"] = 28
MAC_VK["0"] = 29
MAC_VK["bracketright"] = 30
MAC_VK["o"] = 31
MAC_VK["u"] = 32
MAC_VK["bracketleft"] = 33
MAC_VK["i"] = 34
MAC_VK["p"] = 35
MAC_VK["l"] = 37
MAC_VK["j"] = 38
MAC_VK["apostrophe"] = 39
MAC_VK["k"] = 40
MAC_VK["semicolon"] = 41
MAC_VK["backslash"] = 42
MAC_VK["comma"] = 43
MAC_VK["slash"] = 44
MAC_VK["n"] = 45
MAC_VK["m"] = 46
MAC_VK["period"] = 47
MAC_VK["grave"] = 50


class CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class MacOSInputBackend:
    """macOS implementation of InputBackend using CoreGraphics."""

    def __init__(self):
        if sys.platform != "darwin":
            raise InputBackendError("MacOSInputBackend requires macOS")
        try:
            self.cg = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
            )
        except OSError as e:
            raise InputBackendError(f"Failed to load ApplicationServices: {e}")

        # Set argtypes and restypes for CoreGraphics functions
        self.cg.CGMainDisplayID.restype = ctypes.c_uint32
        self.cg.CGDisplayPixelsWide.restype = ctypes.c_size_t
        self.cg.CGDisplayPixelsWide.argtypes = [ctypes.c_uint32]
        self.cg.CGDisplayPixelsHigh.restype = ctypes.c_size_t
        self.cg.CGDisplayPixelsHigh.argtypes = [ctypes.c_uint32]

        self.cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        self.cg.CGEventCreateMouseEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            CGPoint,
            ctypes.c_uint32,
        ]

        self.cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        self.cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]

        self.cg.CGEventCreateScrollWheelEvent2.restype = ctypes.c_void_p
        self.cg.CGEventCreateScrollWheelEvent2.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_int32,
        ]

        self.cg.CGEventPost.restype = None
        self.cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]

        self.cg.CFRelease.restype = None
        self.cg.CFRelease.argtypes = [ctypes.c_void_p]

        self.lock = threading.Lock()
        self.held: Set[str] = set()

    def get_screen_size(self) -> Tuple[int, int]:
        main_id = self.cg.CGMainDisplayID()
        return (self.cg.CGDisplayPixelsWide(main_id), self.cg.CGDisplayPixelsHigh(main_id))

    def get_pointer_pos(self) -> Tuple[int, int]:
        # Fallback to center or current tracked pos
        w, h = self.get_screen_size()
        return (w // 2, h // 2)

    def _post_event(self, event_ref: int) -> None:
        if event_ref:
            # kCGHIDEventTap = 0
            self.cg.CGEventPost(0, event_ref)
            self.cg.CFRelease(event_ref)

    def _mouse_event(self, event_type: int, x: float, y: float, button: int = 0) -> None:
        pt = CGPoint(x, y)
        ev = self.cg.CGEventCreateMouseEvent(None, event_type, pt, button)
        self._post_event(ev)

    def _key_event(self, keycode: int, down: bool) -> None:
        ev = self.cg.CGEventCreateKeyboardEvent(None, keycode, down)
        self._post_event(ev)

    def release_all(self) -> None:
        with self.lock:
            for name in list(self.held):
                kc = MAC_VK.get(name)
                if kc is not None:
                    self._key_event(kc, False)
            self.held.clear()

    def apply(self, events: List[List]) -> None:
        with self.lock:
            w, h = self.get_screen_size()
            for ev in events:
                if not ev:
                    continue
                kind = ev[0]
                if kind == "m":
                    dx = float(ev[1])
                    dy = float(ev[2])
                    # Delta move on macOS: kCGEventMouseMoved = 5
                    # Can specify delta with CGEventSetIntegerValueField
                    pt = CGPoint(0, 0)
                    ev_ref = self.cg.CGEventCreateMouseEvent(None, 5, pt, 0)
                    if ev_ref:
                        # kCGMouseEventDeltaX = 4, kCGMouseEventDeltaY = 5
                        self.cg.CGEventSetIntegerValueField(ev_ref, 4, int(dx))
                        self.cg.CGEventSetIntegerValueField(ev_ref, 5, int(dy))
                        self._post_event(ev_ref)
                elif kind == "b":
                    btn = int(ev[1])
                    down = bool(ev[2])
                    # 1: Left (down=1, up=2)
                    # 2: Middle (down=25, up=26)
                    # 3: Right (down=3, up=4)
                    ev_type = 1 if btn == 1 and down else 2 if btn == 1 else 3 if btn == 3 and down else 4
                    pt = CGPoint(0, 0)
                    ev_ref = self.cg.CGEventCreateMouseEvent(None, ev_type, pt, 0 if btn == 1 else 1 if btn == 3 else 2)
                    self._post_event(ev_ref)
                elif kind == "s":
                    dx = int(ev[1])
                    dy = int(ev[2])
                    ev_ref = self.cg.CGEventCreateScrollWheelEvent2(None, 0, 2, -dy, dx)
                    self._post_event(ev_ref)
                elif kind == "k":
                    name = str(ev[1])
                    down = bool(ev[2])
                    kc = MAC_VK.get(name)
                    if kc is not None:
                        self._key_event(kc, down)
                        if down:
                            self.held.add(name)
                        else:
                            self.held.discard(name)
                elif kind == "tap":
                    name = str(ev[1])
                    kc = MAC_VK.get(name)
                    if kc is not None:
                        self._key_event(kc, True)
                        self._key_event(kc, False)
                elif kind == "type":
                    for ch in ev[1]:
                        kc = MAC_VK.get(ch.lower())
                        if kc is not None:
                            self._key_event(kc, True)
                            self._key_event(kc, False)
                elif kind == "rel":
                    self.release_all()

    def selftest(self) -> None:
        w, h = self.get_screen_size()
        assert w > 0 and h > 0, "Invalid screen dimensions on macOS"
