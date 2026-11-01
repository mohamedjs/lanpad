"""Selftest routine for LANpad."""

import struct
import sys

from .bootstrap import build_container
from .shared.protocol import KEYSYMS, unpack


def run_selftest(force_mock: bool = False) -> int:
    """Run comprehensive diagnostics for input backend, protocol, and token service."""
    container = build_container(force_mock_backend=force_mock)

    # 1. Test binary wire format unpack
    wire = (
        bytes([1])
        + struct.pack("<hh", -3, 7)
        + bytes([2, 1, 1])
        + bytes([3])
        + struct.pack("<bb", 0, -2)
    )
    unpacked = unpack(wire)
    expected = [["m", -3, 7], ["b", 1, 1], ["s", 0, -2]]
    assert unpacked == expected, f"Unpack failed: {unpacked} != {expected}"

    # Truncated frame must not crash
    assert unpack(bytes([1, 5])) == [], "Truncated frame should return empty list"

    # 2. Test token verification
    token = container.token_service.token
    assert container.token_service.verify(token), "Token verification failed for correct token"
    assert not container.token_service.verify("wrong-token"), "Token verification succeeded for invalid token"

    # 3. Test input backend
    backend = container.input_backend
    backend.selftest()

    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(run_selftest())
