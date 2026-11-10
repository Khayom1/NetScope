"""Plain-language, dependency-free connection diagnostics."""
from __future__ import annotations

import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import cli


def diagnose(host: str = "example.com", timeout: float = 3.0) -> dict[str, Any]:
    """Run bounded DNS, TCP, HTTPS and optional ping checks for one host."""
    if not 0.5 <= timeout <= 10:
        raise ValueError("timeout must be between 0.5 and 10 seconds")

    started = time.perf_counter()
    dns = cli.dns_lookup(host)
    tcp = cli.check_port(host, 443, timeout)
    https: dict[str, Any] = {"checked": True, "ok": False}
    try:
        request = Request("https://" + host + "/", method="HEAD",
                          headers={"User-Agent": "NetScope/0.3.0"})
        with urlopen(request, timeout=timeout) as response:
            https.update({"ok": 200 <= response.status < 500,
                          "status_code": response.status})
    except HTTPError as exc:
        # An HTTP response, even 4xx/5xx, proves DNS/TCP/TLS/HTTP worked.
        https.update({"ok": True, "status_code": exc.code,
                      "note": "The server returned an HTTP error status."})
    except (URLError, OSError, TimeoutError) as exc:
        https["error"] = str(getattr(exc, "reason", exc))[:240]

    ping = cli.ping_host(host, count=3, timeout=max(1, int(timeout)))
    checks = {"dns": dns, "tcp_443": tcp, "https": https, "ping": ping}
    findings: list[dict[str, str]] = []

    if not dns.get("ok"):
        status = "problem"
        findings.append({
            "title": "DNS: the hostname could not be resolved",
            "why": "DNS did not return an address for this host.",
            "action": "Check the hostname, try another network, or compare DNS settings."
        })
    elif not tcp.get("open") and not https.get("ok"):
        status = "limited"
        findings.append({
            "title": "The secure connection could not be established",
            "why": "DNS worked, but TCP port 443 or the HTTPS request failed.",
            "action": "Check firewall, VPN, captive portal, carrier restrictions, and whether the host is online."
        })
    else:
        status = "healthy"
        findings.append({
            "title": "The secure connection is reachable",
            "why": "NetScope resolved the host and received a successful HTTPS response or HTTP status.",
            "action": "If an app still fails, check that app's own server, account, proxy, or configuration."
        })

    if ping.get("ok"):
        stats = ping.get("statistics", {})
        loss = stats.get("packet_loss_percent")
        avg = stats.get("avg_ms")
        if loss is not None and loss > 0:
            findings.append({
                "title": "Packet loss was reported by ping",
                "why": f"{loss}% packet loss can cause delays or interruptions.",
                "action": "Repeat the test; compare Wi-Fi/mobile data and move closer to the access point."
            })
        if avg is not None and avg > 150:
            findings.append({
                "title": "Ping latency is high",
                "why": f"Average round-trip time was {avg} ms.",
                "action": "Try a closer server, pause large downloads, or compare another network."
            })
    else:
        findings.append({
            "title": "Ping was unavailable or blocked",
            "why": ping.get("error", "The ping command did not receive replies."),
            "action": "This alone does not mean the internet is down; some networks block ICMP. Use the DNS, TCP and HTTPS results."
        })

    return {
        "tool": "NetScope",
        "version": cli.VERSION,
        "host": host,
        "status": status,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "checks": checks,
        "findings": findings,
        "privacy": "Results are generated locally and are not uploaded by NetScope."
    }
