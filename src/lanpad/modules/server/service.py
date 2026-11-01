"""HTTP and WebSocket server service for LANpad."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from ...shared.network import get_lan_ip, get_tls_context
from ...shared.paths import get_dist_dir
from ...shared.protocol import unpack, ws_accept, ws_frames, ws_send
from ..auth.domain import TokenService
from ..input.backend import InputBackend
from .domain import EventLogger

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".woff2": "font/woff2",
}


def make_handler_class(token_service: TokenService, input_backend: InputBackend, dist_dir: Path):
    event_logger = EventLogger()

    class LanpadHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        disable_nagle_algorithm = True  # TCP_NODELAY: prevents ~40ms packet delay

        def log_message(self, *args):
            pass  # Suppress default noisy stdlib HTTP logging

        def _send(self, code: int, body: bytes = b"", ctype: str = "text/plain") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.headers.get("Upgrade", "").lower() == "websocket":
                return self.websocket()

            path = self.path.split("?")[0].split("#")[0]
            rel = "index.html" if path in ("/", "") else path.lstrip("/")
            file_path = (dist_dir / rel).resolve()

            # Security check: ensure path does not escape dist_dir
            if not str(file_path).startswith(str(dist_dir.resolve())) or not file_path.is_file():
                return self._send(404, b"Not Found")

            ext = file_path.suffix.lower()
            ctype = MIME.get(ext, "application/octet-stream")
            if rel == "index.html":
                print(f"{self.client_address[0]}  loaded the page", flush=True)

            try:
                data = file_path.read_bytes()
                self._send(200, data, ctype)
            except OSError:
                self._send(500, b"Error reading file")

        def websocket(self) -> None:
            key = self.headers.get("Sec-WebSocket-Key")
            if not key:
                return self._send(400, b"Missing Sec-WebSocket-Key")

            self.close_connection = True
            accept_token = ws_accept(key)
            self.wfile.write(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                b"Sec-WebSocket-Accept: " + accept_token.encode() + b"\r\n\r\n"
            )
            self.wfile.flush()

            ip = self.client_address[0]
            authed = False

            try:
                for op, payload in ws_frames(self.rfile):
                    if op == 2:  # Binary frame: packed pointer events
                        if not authed:
                            return
                        events = unpack(payload)
                        event_logger.log(ip, events)
                        input_backend.apply(events)
                        continue

                    try:
                        msg = json.loads(payload.decode("utf-8", "replace"))
                    except ValueError:
                        continue

                    if "p" in msg:
                        # Latency probe: echo payload straight back immediately
                        ws_send(self.wfile, payload.decode("utf-8", "replace"))
                        continue

                    if not authed:
                        cand = str(msg.get("t", ""))
                        if not token_service.verify(cand):
                            print(f"{ip}  ws bad token", flush=True)
                            ws_send(self.wfile, '{"error":"bad token"}')
                            return
                        authed = True
                        print(f"{ip}  ws connected", flush=True)
                        ws_send(self.wfile, '{"ok":true}')
                        continue

                    evs = msg.get("ev", [])
                    event_logger.log(ip, evs)
                    input_backend.apply(evs)
            except (OSError, ValueError):
                pass
            finally:
                input_backend.release_all()  # A dropped connection must not leave keys held
                print(f"{ip}  ws closed", flush=True)

        def do_POST(self) -> None:
            if self.path != "/e":
                return self._send(404, b"Not Found")

            length = int(self.headers.get("Content-Length", 0))
            try:
                body = self.rfile.read(length) if length > 0 else b"{}"
                msg = json.loads(body.decode("utf-8", "replace"))
            except ValueError:
                return self._send(400, b"Invalid JSON")

            cand = str(msg.get("t", ""))
            if not token_service.verify(cand):
                print(f"{self.client_address[0]}  403 bad token", flush=True)
                return self._send(403, b"bad token")

            try:
                evs = msg.get("ev", [])
                event_logger.log(self.client_address[0], evs)
                input_backend.apply(evs)
            except Exception as e:
                return self._send(500, str(e).encode())

            self._send(204)

    return LanpadHandler


class LanpadServer:
    """HTTP & WebSocket server for LANpad."""

    def __init__(
        self,
        token_service: TokenService,
        input_backend: InputBackend,
        dist_dir: Optional[Path] = None,
        port: int = 8765,
        tls: bool = False,
    ):
        self.token_service = token_service
        self.input_backend = input_backend
        self.dist_dir = dist_dir or get_dist_dir()
        self.port = port
        self.tls = tls
        self.ip = get_lan_ip()
        self.httpd: Optional[ThreadingHTTPServer] = None

    def start(self) -> None:
        handler_cls = make_handler_class(self.token_service, self.input_backend, self.dist_dir)
        try:
            self.httpd = ThreadingHTTPServer(("0.0.0.0", self.port), handler_cls)
            if self.tls:
                ctx = get_tls_context(self.ip)
                self.httpd.socket = ctx.wrap_socket(self.httpd.socket, server_side=True)
        except OSError as e:
            sys.exit(f"Port {self.port} busy — LANpad is probably already running ({e})")

        proto = "https" if self.tls else "http"
        print(f"\n  Open on your Mac/Client:  {proto}://{self.ip}:{self.port}/#{self.token_service.token}\n")
        if self.tls:
            print("  Chrome will warn about the certificate — Advanced, then Proceed.")
            print("  That unlocks Esc, Tab and the Cmd keys, which macOS otherwise keeps.\n")

        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            self.input_backend.release_all()
            print("\nShutting down LANpad.")
        finally:
            if self.httpd:
                self.httpd.server_close()
