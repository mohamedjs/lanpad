"""Authentication domain: token storage, generation, and validation."""

import os
import secrets
from pathlib import Path
from ...shared.paths import get_token_file


class TokenService:
    """Manages the authentication secret used to gate WebSocket and POST requests."""

    def __init__(self, token_path: Path = None):
        self.token_path = token_path or get_token_file()
        self._token = self._load_or_create()

    def _load_or_create(self) -> str:
        if self.token_path.exists():
            try:
                t = self.token_path.read_text(encoding="utf-8").strip()
                if t:
                    return t
            except OSError:
                pass

        t = secrets.token_urlsafe(9)
        try:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(t, encoding="utf-8")
            try:
                os.chmod(self.token_path, 0o600)
            except OSError:
                pass
        except OSError:
            pass
        return t

    @property
    def token(self) -> str:
        return self._token

    def verify(self, candidate: str) -> bool:
        """Constant-time comparison to prevent timing attacks."""
        if not candidate:
            return False
        return secrets.compare_digest(str(candidate), self._token)

    def rotate(self) -> str:
        """Generate and persist a new token."""
        self._token = secrets.token_urlsafe(9)
        self.token_path.write_text(self._token, encoding="utf-8")
        try:
            os.chmod(self.token_path, 0o600)
        except OSError:
            pass
        return self._token
