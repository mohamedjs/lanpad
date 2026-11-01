"""Network helpers: IP address detection and TLS certificate generation."""

import os
import socket
import ssl
import subprocess
from pathlib import Path

from .paths import get_cert_file


def get_lan_ip() -> str:
    """Return the primary LAN IPv4 address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually transmit packets, just picks routing interface
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def get_tls_context(ip: str) -> ssl.SSLContext:
    """Create or load a self-signed certificate and return an SSLContext.

    A secure context (HTTPS) is necessary for modern browsers to unlock
    the Keyboard Lock API (preventing Esc, Tab, and Cmd combos from being eaten).
    """
    cert_path = get_cert_file()
    if not cert_path.exists():
        cert_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(cert_path),
            "-out",
            str(cert_path),
            "-days",
            "3650",
            "-subj",
            "/CN=lanpad",
            "-addext",
            f"subjectAltName=IP:{ip},IP:127.0.0.1,DNS:localhost",
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        try:
            os.chmod(cert_path, 0o600)
        except OSError:
            pass

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert_path))
    return ctx
