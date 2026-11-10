from __future__ import annotations

import json
import re
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from . import cli
from .smart import diagnose

HOST = "127.0.0.1"
PORT = 8765
STATIC_DIR = Path(__file__).with_name("static")
HOST_RE = re.compile(r"^[A-Za-z0-9._:-]{1,253}$")
RATE_LIMIT = 20
RATE_WINDOW = 60
_rate_lock = Lock()
_request_times: dict[str, deque[float]] = {}


def validate_host(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Host must be text.")
    host = value.strip()
    if not host or not HOST_RE.fullmatch(host) or host.startswith("-"):
        raise ValueError("Enter a valid hostname or IP address.")
    if any(part.startswith("-") or part.endswith("-")
           for part in host.split(".") if part):
        raise ValueError("Invalid hostname.")
    return host


class Handler(BaseHTTPRequestHandler):
    server_version = "NetScope"
    sys_version = ""

    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
                         "img-src 'self' data:; object-src 'none'; base-uri 'none'; "
                         "frame-ancestors 'none'")
        self.send_header("Permissions-Policy",
                         "camera=(), microphone=(), geolocation=()")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data: dict[str, Any]) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _check_host(self) -> bool:
        try:
            parsed = urlparse("//" + self.headers.get("Host", ""))
            valid = (parsed.hostname in ("127.0.0.1", "localhost")
                     and parsed.port == self.server.server_port
                     and parsed.username is None and parsed.password is None)
        except (ValueError, TypeError):
            valid = False
        if not valid:
            self._json(403, {"ok": False, "error": "Invalid local Host."})
        return valid

    def _check_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        try:
            parsed = urlparse(origin)
            valid = (parsed.scheme == "http"
                     and parsed.hostname in ("127.0.0.1", "localhost")
                     and parsed.port == self.server.server_port
                     and not parsed.username and not parsed.password
                     and parsed.path == "" and parsed.query == ""
                     and parsed.fragment == "")
        except (ValueError, TypeError):
            valid = False
        if not valid:
            self._json(403, {"ok": False, "error": "Invalid request origin."})
        return valid

    def _allow_request(self) -> bool:
        now = time.monotonic()
        with _rate_lock:
            history = _request_times.setdefault(self.client_address[0], deque())
            while history and now - history[0] >= RATE_WINDOW:
                history.popleft()
            if len(history) >= RATE_LIMIT:
                return False
            history.append(now)
            return True

    def do_GET(self) -> None:
        if not self._check_host():
            return
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(200, {"ok": True, "name": "NetScope", "version": cli.VERSION})
            return
        if path not in ("/", "/index.html"):
            self._json(404, {"ok": False, "error": "Not found"})
            return
        try:
            page = (STATIC_DIR / "index.html").read_bytes()
        except OSError:
            self._json(500, {"ok": False, "error": "Web interface files are missing"})
            return
        self._send(200, page, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if not self._check_host() or not self._check_origin():
            return
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self._json(403, {"ok": False, "error": "Cross-site request blocked."})
            return
        if urlparse(self.path).path != "/api/run":
            self._json(404, {"ok": False, "error": "Not found"})
            return
        if not self._allow_request():
            self._json(429, {"ok": False, "error": "Too many requests. Wait one minute."})
            return
        try:
            if self.headers.get("Transfer-Encoding"):
                raise ValueError("Transfer-Encoding is not supported.")
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 16_384:
                raise ValueError("Invalid request size.")
            raw_body = self.rfile.read(length)
            if len(raw_body) != length:
                raise ValueError("Incomplete request body.")
            body = json.loads(raw_body)
            if not isinstance(body, dict):
                raise ValueError("Invalid request.")
            action = body.get("action")
            host = validate_host(body.get("host", ""))
            if action == "diagnose":
                timeout = float(body.get("timeout", 3))
                lang = body.get("lang", "en")
                if lang not in ("en", "ru", "tg"):
                    raise ValueError("Choose a supported language: en, ru or tg.")
                result = diagnose(host, timeout, lang)
            elif action == "summary":
                result = cli.build_report(host)
            elif action == "dns":
                result = cli.dns_lookup(host)
            elif action == "port":
                port, timeout = int(body.get("port", 443)), float(body.get("timeout", 3))
                if not 1 <= port <= 65535 or not 0.5 <= timeout <= 10:
                    raise ValueError("Port must be 1–65535 and timeout 0.5–10 seconds.")
                result = cli.check_port(host, port, timeout)
            elif action == "ping":
                count, timeout = int(body.get("count", 4)), int(body.get("timeout", 2))
                if not 1 <= count <= 10 or not 1 <= timeout <= 5:
                    raise ValueError("Ping count must be 1–10 and timeout 1–5 seconds.")
                result = cli.ping_host(host, count, timeout)
            elif action == "ipv6":
                result = cli.ipv6_check(host)
            elif action == "trace":
                hops, timeout = int(body.get("max_hops", 12)), int(body.get("timeout", 2))
                if not 1 <= hops <= 30 or not 1 <= timeout <= 5:
                    raise ValueError("Max hops must be 1–30 and timeout 1–5 seconds.")
                result = cli.traceroute_host(host, hops, timeout)
            else:
                raise ValueError("Unknown diagnostic action.")
            self._json(200, {"ok": True, "action": action, "result": result})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"ok": False, "error": str(exc)})
        except Exception:
            self._json(500, {"ok": False, "error": "Diagnostic failed unexpectedly."})

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[NetScope]", fmt % args)


class NetScopeServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16
    allow_reuse_address = True


def main() -> None:
    server = NetScopeServer((HOST, PORT), Handler)
    print(f"NetScope Web v{cli.VERSION}")
    print(f"Open http://{HOST}:{PORT} in your browser")
    print("Local-only server. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping NetScope Web...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
