"""Input backend interface and base definition."""

from typing import List, Protocol, Tuple


class InputBackend(Protocol):
    """Protocol implemented by platform-specific mouse and keyboard controllers."""

    def apply(self, events: List[List]) -> None:
        """Process a list of input events."""
        ...

    def release_all(self) -> None:
        """Release any currently held keys or mouse buttons."""
        ...

    def get_pointer_pos(self) -> Tuple[int, int]:
        """Return the current cursor (x, y) coordinates."""
        ...

    def get_screen_size(self) -> Tuple[int, int]:
        """Return the screen dimensions (width, height) in pixels."""
        ...

    def selftest(self) -> None:
        """Verify the input backend functions correctly on this system."""
        ...
