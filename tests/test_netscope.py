import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from netscope.cli import (
    check_port, dns_lookup, parse_ping_output, save_report, traceroute_host
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


if __name__ == "__main__":
    unittest.main()
