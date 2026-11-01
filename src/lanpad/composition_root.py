"""Composition root for LANpad: the ONLY module where dependencies are wired."""

from pathlib import Path
from typing import Optional

from .modules.auth import TokenService
from .modules.input import InputBackend, get_input_backend
from .modules.server import LanpadServer
from .shared.events import EventBus
from .shared.paths import get_dist_dir


class Container:
    """Dependency injection container holding initialized services."""

    def __init__(
        self,
        token_service: TokenService,
        input_backend: InputBackend,
        event_bus: EventBus,
        server: LanpadServer,
    ):
        self.token_service = token_service
        self.input_backend = input_backend
        self.event_bus = event_bus
        self.server = server


def build_container(
    port: int = 8765,
    tls: bool = False,
    dist_dir: Optional[Path] = None,
    force_mock_backend: bool = False,
) -> Container:
    """Wire and return the modular monolith container."""
    event_bus = EventBus()
    token_service = TokenService()
    input_backend = get_input_backend(force_mock=force_mock_backend)
    dist = dist_dir or get_dist_dir()

    server = LanpadServer(
        token_service=token_service,
        input_backend=input_backend,
        dist_dir=dist,
        port=port,
        tls=tls,
    )

    return Container(
        token_service=token_service,
        input_backend=input_backend,
        event_bus=event_bus,
        server=server,
    )
