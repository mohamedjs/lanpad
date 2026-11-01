"""Wire protocol, framing, and key mapping definitions for LANpad."""

import base64
import hashlib
import struct
from typing import Iterator, List, Tuple

# RFC 6455 handshake GUID
GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

MODS = ["Shift_L", "Control_L", "Alt_L", "Super_L"]

KEYSYMS = (
    MODS
    + [
        "Shift_R",
        "Control_R",
        "Alt_R",
        "Super_R",
        "Return",
        "Escape",
        "BackSpace",
        "Tab",
        "space",
        "Caps_Lock",
        "Delete",
        "Insert",
        "minus",
        "equal",
        "bracketleft",
        "bracketright",
        "backslash",
        "semicolon",
        "apostrophe",
        "comma",
        "period",
        "slash",
        "grave",
        "less",
        "Up",
        "Down",
        "Left",
        "Right",
        "Home",
        "End",
        "Prior",
        "Next",
        "Num_Lock",
        "KP_Divide",
        "KP_Multiply",
        "KP_Subtract",
        "KP_Add",
        "KP_Decimal",
    ]
    + [f"F{i}" for i in range(1, 13)]
    + [f"KP_{i}" for i in range(10)]
)


def ws_accept(key: str) -> str:
    """Calculate the Sec-WebSocket-Accept header value."""
    return base64.b64encode(hashlib.sha1(key.encode() + GUID).digest()).decode()


def ws_frames(rfile) -> Iterator[Tuple[int, bytes]]:
    """Yield (opcode, payload) from a WebSocket client.
    Client frames must be masked according to RFC 6455.
    """
    while True:
        hdr = rfile.read(2)
        if len(hdr) < 2:
            return
        op = hdr[0] & 0x0F
        n = hdr[1] & 0x7F
        if not (hdr[1] & 0x80):
            # Unmasked client frame is a protocol violation
            return
        if n == 126:
            ext = rfile.read(2)
            if len(ext) < 2:
                return
            n = struct.unpack(">H", ext)[0]
        elif n == 127:
            ext = rfile.read(8)
            if len(ext) < 8:
                return
            n = struct.unpack(">Q", ext)[0]

        mask = rfile.read(4)
        if len(mask) < 4:
            return
        data = bytearray(rfile.read(n))
        if len(data) < n:
            return

        for i in range(n):
            data[i] ^= mask[i & 3]

        if op == 8:  # Close frame
            return
        if op in (1, 2):  # 1 = text, 2 = binary
            yield op, bytes(data)


def unpack(buf: bytes) -> List[List]:
    """Unpack compact binary frames from the pointer hot path.

    Wire format:
      Type 1 (5 bytes): 1 dx:int16 dy:int16
      Type 2 (3 bytes): 2 button:uint8 down:uint8
      Type 3 (3 bytes): 3 dx:int8 dy:int8
    """
    ev = []
    i = 0
    n = len(buf)
    while i < n:
        t = buf[i]
        if t == 1 and i + 5 <= n:
            ev.append(["m", *struct.unpack_from("<hh", buf, i + 1)])
            i += 5
        elif t == 2 and i + 3 <= n:
            ev.append(["b", buf[i + 1], buf[i + 2]])
            i += 3
        elif t == 3 and i + 3 <= n:
            ev.append(["s", *struct.unpack_from("<bb", buf, i + 1)])
            i += 3
        else:
            break
    return ev


def ws_send(wfile, text: str) -> None:
    """Send an unfragmented UTF-8 text frame."""
    b = text.encode("utf-8")
    length = len(b)
    if length < 126:
        wfile.write(bytes([0x81, length]) + b)
    elif length < 65536:
        wfile.write(bytes([0x81, 126]) + struct.pack(">H", length) + b)
    else:
        wfile.write(bytes([0x81, 127]) + struct.pack(">Q", length) + b)
    wfile.flush()
