"""Unit tests for authentication and token validation."""

import tempfile
from pathlib import Path

from lanpad.modules.auth.domain import TokenService


def test_token_creation_and_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = Path(tmpdir) / "token"
        service = TokenService(token_path=token_file)
        tok = service.token
        assert len(tok) >= 8

        # File was persisted
        assert token_file.exists()
        assert token_file.read_text().strip() == tok

        # Reloading uses existing token
        service2 = TokenService(token_path=token_file)
        assert service2.token == tok


def test_token_verify():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = Path(tmpdir) / "token"
        service = TokenService(token_path=token_file)
        assert service.verify(service.token)
        assert not service.verify("invalid")
        assert not service.verify("")
        assert not service.verify(None)


def test_token_rotation():
    with tempfile.TemporaryDirectory() as tmpdir:
        token_file = Path(tmpdir) / "token"
        service = TokenService(token_path=token_file)
        first = service.token
        second = service.rotate()
        assert first != second
        assert service.verify(second)
        assert not service.verify(first)


if __name__ == "__main__":
    test_token_creation_and_persistence()
    test_token_verify()
    test_token_rotation()
    print("auth tests OK")
