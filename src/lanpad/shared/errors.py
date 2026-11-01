"""Exceptions for LANpad."""


class LanpadError(Exception):
    """Base exception for all LANpad errors."""


class AuthError(LanpadError):
    """Raised when authentication fails."""


class InputBackendError(LanpadError):
    """Raised when the input backend fails to initialize or dispatch an event."""


class ServerError(LanpadError):
    """Raised when the HTTP/WebSocket server experiences an error."""
