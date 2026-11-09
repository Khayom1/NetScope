import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from netscope.web import Handler

from netscope.cli import (
    check_port, dns_lookup, ipv6_check, parse_ping_output, save_report, traceroute_host
)


class NetScopeTests(unittest.TestCase):
    def test_dns_lookup_returns_host_and_status(self):
        with patch("netscope.cli.socket.getaddrinfo", return_value=[
            (2, 1, 6, "", ("203.0.113.10", 0))
        ]):
            result = dns_lookup("example.test")
        self.assertEqual(result["host"], "example.test")
        self.assertTrue(result["ok"])
        self.assertEqual(result["addresses"], ["203.0.113.10"])

    def test_dns_lookup_handles_failure(self):
        with patch("netscope.cli.socket.getaddrinfo", side_effect=OSError("no DNS")):
            result = dns_lookup("invalid.test")
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_port_handles_unreachable_endpoint(self):
        with patch("netscope.cli.socket.create_connection", side_effect=OSError("refused")):
            result = check_port("127.0.0.1", 9, timeout=0.1)
        self.assertFalse(result["open"])
        self.assertEqual(result["port"], 9)

    def test_ping_parser_extracts_stats(self):
        sample = "4 packets transmitted, 4 received, 0% packet loss\\nrtt min/avg/max/mdev = 10.1/20.2/30.3/2.0 ms"
        result = parse_ping_output(sample)
        self.assertEqual(result["packet_loss_percent"], 0.0)
        self.assertEqual(result["avg_ms"], 20.2)

    def test_report_can_be_saved_as_json(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "report.json"
            save_report({"ok": True}, str(target))
            self.assertIn('"ok": true', target.read_text())

    def test_traceroute_missing_is_explained(self):
        with patch("netscope.cli.shutil.which", return_value=None):
            result = traceroute_host("example.com")
        self.assertFalse(result["ok"])
        self.assertIn("pkg install traceroute", result["error"])


    def test_ipv6_dns_found_but_network_unreachable(self):
        with patch("netscope.cli.dns_lookup", return_value={
            "ok": True,
            "addresses": ["2001:db8::1"]
        }), patch(
            "netscope.cli.socket.create_connection",
            side_effect=OSError(101, "Network is unreachable")
        ):
            result = ipv6_check("example.test")

        self.assertTrue(result["dns_available"])
        self.assertFalse(result["connectivity_available"])
        self.assertEqual(result["ipv6_addresses"], ["2001:db8::1"])
        self.assertFalse(result["tcp_443_reachable"])

    def test_ipv6_connection_success(self):
        with patch("netscope.cli.dns_lookup", return_value={
            "ok": True,
            "addresses": ["2001:db8::1"]
        }), patch(
            "netscope.cli.socket.create_connection"
        ) as connection:
            connection.return_value.__enter__.return_value = None
            result = ipv6_check("example.test")

        self.assertTrue(result["dns_available"])
        self.assertTrue(result["connectivity_available"])
        self.assertTrue(result["tcp_443_reachable"])
        self.assertEqual(result["tested_address"], "2001:db8::1")

    def test_ipv6_dns_failure(self):
        with patch("netscope.cli.dns_lookup", return_value={
            "ok": False,
            "error": "No IPv6 records"
        }):
            result = ipv6_check("example.test")

        self.assertFalse(result["dns_available"])
        self.assertFalse(result["connectivity_available"])
        self.assertEqual(result["ipv6_addresses"], [])

    def test_traceroute_uses_icmp_flag(self):
        from types import SimpleNamespace

        completed = SimpleNamespace(
            returncode=0,
            stdout="trace output",
            stderr=""
        )

        with patch("netscope.cli.shutil.which", return_value="/usr/bin/traceroute"), patch(
            "netscope.cli.subprocess.run",
            return_value=completed
        ) as run:
            result = traceroute_host("example.test", 12, 2)

        command = run.call_args[0][0]
        self.assertIn("-I", command)
        self.assertEqual(command[command.index("-m") + 1], "12")
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()



class WebAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True
        )
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, body=None, extra_headers=None):
        data = None if body is None else (
            body if isinstance(body, bytes)
            else json.dumps(body).encode()
        )
        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        req = urllib.request.Request(
            self.base + path,
            data=data,
            headers=headers,
            method="GET" if body is None else "POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            with exc:
                return exc.code, json.loads(exc.read())

    def test_health_endpoint(self):
        status, data = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["name"], "NetScope")

    def test_unknown_route_returns_404(self):
        status, data = self.request("/api/missing")
        self.assertEqual(status, 404)
        self.assertFalse(data["ok"])

    def test_invalid_json_returns_400(self):
        status, data = self.request("/api/run", b"{invalid json")
        self.assertEqual(status, 400)
        self.assertFalse(data["ok"])

    def test_unknown_action_returns_400(self):
        status, data = self.request(
            "/api/run",
            {"action": "unknown", "host": "example.com"}
        )
        self.assertEqual(status, 400)
        self.assertIn("Unknown", data["error"])

    def test_invalid_host_returns_403(self):
        status, data = self.request(
            "/api/health",
            extra_headers={"Host": "evil.example"}
        )
        self.assertEqual(status, 403)
        self.assertFalse(data["ok"])

    def test_invalid_origin_returns_403(self):
        status, data = self.request(
            "/api/run",
            {"action": "unknown", "host": "example.com"},
            {"Origin": "http://evil.example"}
        )
        self.assertEqual(status, 403)
        self.assertFalse(data["ok"])

    def test_valid_local_origin_is_allowed(self):
        status, data = self.request(
            "/api/run",
            {"action": "unknown", "host": "example.com"},
            {"Origin": self.base}
        )
        self.assertEqual(status, 400)
        self.assertIn("Unknown", data["error"])

    def test_security_headers_are_present(self):
        with urllib.request.urlopen(
            self.base + "/api/health", timeout=3
        ) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(
                response.headers.get("X-Content-Type-Options"), "nosniff"
            )
            self.assertEqual(
                response.headers.get("X-Frame-Options"), "DENY"
            )
            self.assertEqual(
                response.headers.get("Cache-Control"), "no-store"
            )
            self.assertIsNotNone(
                response.headers.get("Content-Security-Policy")
            )

    def test_rate_limit_returns_429(self):
        from netscope import web

        with web._rate_lock:
            web._request_times.clear()

        with patch("netscope.web.RATE_LIMIT", 2):
            payload = {"action": "unknown", "host": "example.com"}

            first, _ = self.request("/api/run", payload)
            second, _ = self.request("/api/run", payload)
            third, data = self.request("/api/run", payload)

        self.assertEqual(first, 400)
        self.assertEqual(second, 400)
        self.assertEqual(third, 429)
        self.assertIn("Too many requests", data["error"])
