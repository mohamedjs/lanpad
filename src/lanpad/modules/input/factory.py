"""Input backend factory and mock backend for automated tests and headless environments."""

import sys
from typing import List, Optional, Set, Tuple

from ...shared.protocol import KEYSYMS
from .backend import InputBackend
from .linux import LinuxX11InputBackend
from .macos import MacOSInputBackend
from .windows import WindowsInputBackend


class MockInputBackend:
    """Mock backend that tracks events in memory without system calls.
    Used for unit testing and headless CI.
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        self.w = width
        self.h = height
        self.x = width // 2
        self.y = height // 2
        self.events: List[List] = []
        self.held: Set[str] = set()

    def get_screen_size(self) -> Tuple[int, int]:
        return (self.w, self.h)

    def get_pointer_pos(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def release_all(self) -> None:
        self.held.clear()
        self.events.append(["rel"])

    def apply(self, events: List[List]) -> None:
        for ev in events:
            if not ev:
                continue
            self.events.append(ev)
            kind = ev[0]
            if kind == "m":
                self.x = min(self.w - 1, max(0, self.x + int(ev[1])))
                self.y = min(self.h - 1, max(0, self.y + int(ev[2])))
            elif kind == "k":
                if ev[2]:
                    self.held.add(ev[1])
                else:
                    self.held.discard(ev[1])
            elif kind == "rel":
                self.held.clear()

    def selftest(self) -> None:
        p0 = self.get_pointer_pos()
        self.apply([["m", 50, 50]])
        p1 = self.get_pointer_pos()
        assert p1 == (p0[0] + 50, p0[1] + 50)
        self.apply([["m", -50, -50]])


def get_input_backend(force_mock: bool = False) -> InputBackend:
    """Instantiate and return the appropriate InputBackend for the current operating system."""
    if force_mock:
        return MockInputBackend()

    if sys.platform.startswith("linux"):
        try:
            return LinuxX11InputBackend()
        except Exception:
            return MockInputBackend()
    elif sys.platform.startswith("win"):
        try:
            return WindowsInputBackend()
        except Exception:
            return MockInputBackend()
    elif sys.platform == "darwin":
        try:
            return MacOSInputBackend()
        except Exception:
            return MockInputBackend()

    return MockInputBackend()
