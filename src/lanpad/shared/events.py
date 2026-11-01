"""Typed in-process EventBus for emitting past-tense domain facts."""

from collections import defaultdict
from typing import Any, Callable, Dict, List


class EventBus:
    """Synchronous in-process event bus.
    Emits past-tense facts ('device.connected', 'pointer.moved'), never commands.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Any], None]) -> None:
        self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[Any], None]) -> None:
        if handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    def emit(self, event_name: str, data: Any = None) -> None:
        for handler in list(self._subscribers.get(event_name, [])):
            try:
                handler(data)
            except Exception as e:
                print(f"[EventBus] Error in handler for '{event_name}': {e}")
