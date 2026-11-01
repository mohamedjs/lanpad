"""Windows input backend using user32.dll SendInput via ctypes."""

import ctypes
import sys
import threading
from typing import List, Set, Tuple

from ...shared.errors import InputBackendError

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_MAP = {
    "Shift_L": 0xA0,
    "Shift_R": 0xA1,
    "Control_L": 0xA2,
    "Control_R": 0xA3,
    "Alt_L": 0x12,
    "Alt_R": 0x12,
    "Super_L": 0x5B,
    "Super_R": 0x5C,
    "Return": 0x0D,
    "Escape": 0x1B,
    "BackSpace": 0x08,
    "Tab": 0x09,
    "space": 0x20,
    "Caps_Lock": 0x14,
    "Delete": 0x2E,
    "Insert": 0x2D,
    "minus": 0xBD,
    "equal": 0xBB,
    "bracketleft": 0xDB,
    "bracketright": 0xDD,
    "backslash": 0xDC,
    "semicolon": 0xBA,
    "apostrophe": 0xDE,
    "comma": 0xBC,
    "period": 0xBE,
    "slash": 0xBF,
    "grave": 0xC0,
    "Up": 0x26,
    "Down": 0x28,
    "Left": 0x25,
    "Right": 0x27,
    "Home": 0x24,
    "End": 0x23,
    "Prior": 0x21,
    "Next": 0x22,
    "Num_Lock": 0x90,
    "KP_Divide": 0x6F,
    "KP_Multiply": 0x6A,
    "KP_Subtract": 0x6D,
    "KP_Add": 0x6B,
    "KP_Decimal": 0x6E,
}
for i in range(1, 13):
    VK_MAP[f"F{i}"] = 0x70 + (i - 1)
for i in range(10):
    VK_MAP[f"KP_{i}"] = 0x60 + i

# Ctypes structures
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", _INPUT_UNION),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class WindowsInputBackend:
    """Windows implementation of InputBackend using SendInput."""

    def __init__(self):
        if not sys.platform.startswith("win"):
            raise InputBackendError("WindowsInputBackend requires Windows OS")
        self.user32 = ctypes.windll.user32
        self.lock = threading.Lock()
        self.held: Set[str] = set()
        self.w = self.user32.GetSystemMetrics(0)
        self.h = self.user32.GetSystemMetrics(1)

    def get_screen_size(self) -> Tuple[int, int]:
        return (self.user32.GetSystemMetrics(0), self.user32.GetSystemMetrics(1))

    def get_pointer_pos(self) -> Tuple[int, int]:
        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def _send_input(self, inp: INPUT) -> None:
        self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _mouse_event(self, flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> None:
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dx = dx
        inp.union.mi.dy = dy
        inp.union.mi.dwFlags = flags
        inp.union.mi.mouseData = data
        self._send_input(inp)

    def _key_event(self, vk: int, down: bool, extended: bool = False) -> None:
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = vk
        flags = 0
        if not down:
            flags |= KEYEVENTF_KEYUP
        if extended:
            flags |= KEYEVENTF_EXTENDEDKEY
        inp.union.ki.dwFlags = flags
        self._send_input(inp)

    def _tap_char(self, ch: str) -> None:
        # Unicode keyboard event
        for down in (True, False):
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = 0
            inp.union.ki.wScan = ord(ch)
            inp.union.ki.dwFlags = KEYEVENTF_UNICODE | (0 if down else KEYEVENTF_KEYUP)
            self._send_input(inp)

    def release_all(self) -> None:
        with self.lock:
            for name in list(self.held):
                vk = VK_MAP.get(name)
                if vk:
                    self._key_event(vk, False)
            self.held.clear()
            # Release mouse buttons
            self._mouse_event(MOUSEEVENTF_LEFTUP)
            self._mouse_event(MOUSEEVENTF_RIGHTUP)
            self._mouse_event(MOUSEEVENTF_MIDDLEUP)

    def apply(self, events: List[List]) -> None:
        with self.lock:
            for ev in events:
                if not ev:
                    continue
                kind = ev[0]
                if kind == "m":
                    self._mouse_event(MOUSEEVENTF_MOVE, dx=int(ev[1]), dy=int(ev[2]))
                elif kind == "b":
                    btn = int(ev[1])
                    down = bool(ev[2])
                    if btn == 1:
                        self._mouse_event(MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP)
                    elif btn == 2:
                        self._mouse_event(MOUSEEVENTF_MIDDLEDOWN if down else MOUSEEVENTF_MIDDLEUP)
                    elif btn == 3:
                        self._mouse_event(MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP)
                elif kind == "s":
                    dx = int(ev[1])
                    dy = int(ev[2])
                    if dy != 0:
                        # 120 is WHEEL_DELTA in Windows
                        self._mouse_event(MOUSEEVENTF_WHEEL, data=int(-dy * 120))
                    if dx != 0:
                        self._mouse_event(MOUSEEVENTF_HWHEEL, data=int(dx * 120))
                elif kind == "k":
                    name = str(ev[1])
                    down = bool(ev[2])
                    vk = VK_MAP.get(name)
                    if vk:
                        self._key_event(vk, down)
                        if down:
                            self.held.add(name)
                        else:
                            self.held.discard(name)
                elif kind == "tap":
                    name = str(ev[1])
                    vk = VK_MAP.get(name)
                    if vk:
                        self._key_event(vk, True)
                        self._key_event(vk, False)
                    elif len(name) == 1:
                        self._tap_char(name)
                elif kind == "type":
                    for ch in ev[1]:
                        self._tap_char(ch)
                elif kind == "rel":
                    self.release_all()

    def selftest(self) -> None:
        w, h = self.get_screen_size()
        assert w > 0 and h > 0, "Invalid screen dimensions on Windows"
        x, y = self.get_pointer_pos()
        assert isinstance(x, int) and isinstance(y, int)
