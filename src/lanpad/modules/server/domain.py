"""Server domain: connection metrics and rate-limited event logging."""

import time
from typing import Dict, List


class EventLogger:
    """Aggregates high-frequency input events into a single line per second.
    Prevents log flooding on 1000Hz mouse updates while retaining debugging value.
    """

    def __init__(self):
        self._window_start = 0.0
        self._count = 0
        self._kinds: Dict[str, int] = {}

    def log(self, ip: str, events: List[List]) -> None:
        now = time.time()
        self._count += 1
        for ev in events:
            if ev:
                kind = str(ev[0])
                self._kinds[kind] = self._kinds.get(kind, 0) + 1
        if now - self._window_start >= 1.0:
            kinds_summary = self._kinds or "(empty)"
            print(f"{ip}  {self._count} posts  {kinds_summary}", flush=True)
            self._window_start = now
            self._count = 0
            self._kinds = {}
