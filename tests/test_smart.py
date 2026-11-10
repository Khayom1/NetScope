import unittest
from unittest.mock import patch

from netscope.smart import diagnose


class SmartDiagnosisTests(unittest.TestCase):
    @patch("netscope.smart.cli.ping_host", return_value={"ok": False, "error": "blocked"})
    @patch("netscope.smart.urlopen")
    @patch("netscope.smart.cli.check_port", return_value={"open": True, "port": 443})
    @patch("netscope.smart.cli.dns_lookup", return_value={"ok": True, "addresses": ["192.0.2.1"]})
    def test_healthy_https_even_when_ping_blocked(self, dns, port, urlopen, ping):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        result = diagnose("example.com")
        self.assertEqual(result["status"], "healthy")
        self.assertTrue(any("secure connection" in item["title"].lower()
                            for item in result["findings"]))

    @patch("netscope.smart.cli.ping_host", return_value={"ok": False, "error": "blocked"})
    @patch("netscope.smart.urlopen", side_effect=OSError("offline"))
    @patch("netscope.smart.cli.check_port", return_value={"open": False})
    @patch("netscope.smart.cli.dns_lookup", return_value={"ok": False, "error": "no dns"})
    def test_dns_failure_is_explained(self, dns, port, urlopen, ping):
        result = diagnose("bad.invalid")
        self.assertEqual(result["status"], "problem")
        self.assertIn("DNS", result["findings"][0]["title"])

    def test_timeout_is_bounded(self):
        with self.assertRaises(ValueError):
            diagnose("example.com", timeout=99)


if __name__ == "__main__":
    unittest.main()
