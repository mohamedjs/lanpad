"""Unit tests for WebSocket framing, binary packing/unpacking, and protocol constants."""

import struct
from lanpad.shared.protocol import GUID, KEYSYMS, MODS, unpack, ws_accept


def test_ws_accept_rfc6455():
    # RFC 6455 Section 1.3 test vector
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    expected = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    assert ws_accept(key) == expected, f"Expected {expected}, got {ws_accept(key)}"


def test_unpack_wire_format():
    # Move: type=1, dx=10, dy=-20
    # Button: type=2, button=1, down=1
    # Scroll: type=3, dx=0, dy=5
    wire = (
        bytes([1])
        + struct.pack("<hh", 10, -20)
        + bytes([2, 1, 1])
        + bytes([3])
        + struct.pack("<bb", 0, 5)
    )
    result = unpack(wire)
    assert result == [["m", 10, -20], ["b", 1, 1], ["s", 0, 5]]


def test_unpack_malformed_truncated():
    # Incomplete move frame (needs 5 bytes total: 1 type + 4 payload)
    truncated = bytes([1, 10, 0])
    assert unpack(truncated) == []


def test_keysyms_integrity():
    assert "Return" in KEYSYMS
    assert "Escape" in KEYSYMS
    assert "space" in KEYSYMS
    for mod in MODS:
        assert mod in KEYSYMS


if __name__ == "__main__":
    test_ws_accept_rfc6455()
    test_unpack_wire_format()
    test_unpack_malformed_truncated()
    test_keysyms_integrity()
    print("protocol tests OK")
