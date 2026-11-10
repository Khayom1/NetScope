from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

VERSION = "0.3.0"


def get_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("1.1.1.1", 80))
        return str(sock.getsockname()[0])
    except OSError:
        return "unavailable"
    finally:
        sock.close()


def dns_lookup(host: str, family: int = socket.AF_UNSPEC) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        results = socket.getaddrinfo(host, None, family, socket.SOCK_STREAM)
        addresses = sorted({item[4][0] for item in results})
        return {"host": host, "ok": bool(addresses), "addresses": addresses,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2)}
    except (socket.gaierror, OSError) as exc:
        return {"host": host, "ok": False, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2)}


def check_port(host: str, port: int, timeout: float = 3.0) -> dict[str, Any]:
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if not 0.1 <= timeout <= 30:
        raise ValueError("timeout must be between 0.1 and 30 seconds")
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"host": host, "port": port, "open": True,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2)}
    except OSError as exc:
        return {"host": host, "port": port, "open": False,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": str(exc)}


def parse_ping_output(output: str) -> dict[str, Any]:
    loss = re.search(r"([\d.]+)%\s*packet loss", output, re.IGNORECASE)
    rtt = re.search(r"(?:rtt|round-trip)\s+min/avg/max(?:/mdev)?\s*=\s*"
                    r"([\d.]+)/([\d.]+)/([\d.]+)", output, re.IGNORECASE)
    result: dict[str, Any] = {}
    if loss:
        result["packet_loss_percent"] = float(loss.group(1))
    if rtt:
        result.update({"min_ms": float(rtt.group(1)), "avg_ms": float(rtt.group(2)),
                       "max_ms": float(rtt.group(3))})
    return result


def ping_host(host: str, count: int = 4, timeout: int = 2) -> dict[str, Any]:
    if not 1 <= count <= 20 or not 1 <= timeout <= 10:
        raise ValueError("count must be 1–20 and timeout 1–10 seconds")
    command = ["ping", "-c", str(count), "-W", str(timeout), host]
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                    timeout=count * timeout + 5)
        output = (completed.stdout or completed.stderr).strip()
        return {"host": host, "ok": completed.returncode == 0,
                "returncode": completed.returncode,
                "statistics": parse_ping_output(output), "output": output}
    except FileNotFoundError:
        return {"host": host, "ok": False, "error": "ping command not found"}
    except subprocess.TimeoutExpired:
        return {"host": host, "ok": False, "error": "ping command timed out"}


def ipv6_check(host: str = "cloudflare.com", timeout: float = 3.0) -> dict[str, Any]:
    dns = dns_lookup(host, socket.AF_INET6)
    if not dns["ok"]:
        return {"host": host, "dns_available": False,
                "connectivity_available": False, "ipv6_addresses": [],
                "dns_error": dns.get("error", "No IPv6 DNS records found")}
    addresses = dns["addresses"]
    started = time.perf_counter()
    errors = []
    for address in addresses:
        try:
            with socket.create_connection((address, 443), timeout=timeout):
                return {"host": host, "dns_available": True,
                        "connectivity_available": True, "ipv6_addresses": addresses,
                        "tested_address": address, "tcp_443_reachable": True,
                        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2)}
        except OSError as exc:
            errors.append(str(exc))
    return {"host": host, "dns_available": True, "connectivity_available": False,
            "ipv6_addresses": addresses, "tcp_443_reachable": False,
            "error": errors[-1] if errors else "IPv6 connection failed"}


def traceroute_host(host: str, max_hops: int = 12, timeout: int = 2) -> dict[str, Any]:
    if not 1 <= max_hops <= 30 or not 1 <= timeout <= 5:
        raise ValueError("max_hops must be 1–30 and timeout 1–5 seconds")
    executable = shutil.which("traceroute")
    if not executable:
        return {"host": host, "ok": False,
                "error": "traceroute not installed; run: pkg install traceroute"}
    try:
        completed = subprocess.run([executable, "-I", "-m", str(max_hops),
                                     "-w", str(timeout), host],
                                   capture_output=True, text=True,
                                   timeout=max_hops * timeout + 5)
        output = (completed.stdout or completed.stderr).strip()
        return {"host": host, "ok": completed.returncode == 0, "output": output}
    except subprocess.TimeoutExpired:
        return {"host": host, "ok": False, "error": "traceroute timed out"}


def build_report(host: str = "example.com") -> dict[str, Any]:
    return {"tool": "NetScope", "version": VERSION, "system": platform.system(),
            "python": platform.python_version(), "dns": dns_lookup(host),
            "https_1_1_1_1": check_port("1.1.1.1", 443)}


def save_report(data: dict[str, Any], filename: str, as_json: bool = False) -> None:
    path = Path(filename).expanduser()
    if as_json or path.suffix.lower() == ".json":
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    else:
        content = "NetScope Report\n" + "=" * 40 + "\n" + json.dumps(
            data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(content, encoding="utf-8")


def print_result(data: dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    print("\nNetScope — Network Diagnostics\n" + "=" * 34)
    for key, value in data.items():
        print(f"\n{key.upper()}:")
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                print(f"  {subkey}: {subvalue}")
        else:
            print(f"  {value}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="netscope", description="Privacy-first network diagnostics. No root required.")
    sub = parser.add_subparsers(dest="command")
    summary = sub.add_parser("summary", help="show a quick network report")
    summary.add_argument("--host", default="example.com")
    dns = sub.add_parser("dns", help="resolve a hostname")
    dns.add_argument("host")
    dns.add_argument("--ipv6", action="store_true")
    port = sub.add_parser("port", help="test a TCP port")
    port.add_argument("host")
    port.add_argument("port", type=int)
    port.add_argument("--timeout", type=float, default=3.0)
    ping = sub.add_parser("ping", help="measure packet loss and latency")
    ping.add_argument("host")
    ping.add_argument("-c", "--count", type=int, default=4)
    ping.add_argument("-W", "--timeout", type=int, default=2)
    ipv6 = sub.add_parser("ipv6", help="check IPv6 DNS and connectivity")
    ipv6.add_argument("--host", default="cloudflare.com")
    trace = sub.add_parser("trace", help="trace route to a host")
    trace.add_argument("host")
    trace.add_argument("--max-hops", type=int, default=12)
    trace.add_argument("--timeout", type=int, default=2)
    diagnose = sub.add_parser("diagnose", help="explain common connection problems")
    diagnose.add_argument("host", nargs="?", default="example.com")
    diagnose.add_argument("--timeout", type=float, default=3.0)
    for command in (summary, dns, port, ping, ipv6, trace, diagnose):
        command.add_argument("--json", action="store_true")
        command.add_argument("--output", help="save report to a JSON or TXT file")

    args = parser.parse_args()
    if args.command in (None, "summary"):
        data = build_report(getattr(args, "host", "example.com"))
    elif args.command == "dns":
        data = dns_lookup(args.host, socket.AF_INET6 if args.ipv6 else socket.AF_UNSPEC)
    elif args.command == "port":
        data = check_port(args.host, args.port, args.timeout)
    elif args.command == "ping":
        data = ping_host(args.host, args.count, args.timeout)
    elif args.command == "ipv6":
        data = ipv6_check(args.host)
    elif args.command == "trace":
        data = traceroute_host(args.host, args.max_hops, args.timeout)
    elif args.command == "diagnose":
        from .smart import diagnose as run_diagnosis
        data = run_diagnosis(args.host, args.timeout)
    else:
        parser.print_help()
        return

    print_result(data, getattr(args, "json", False))
    output = getattr(args, "output", None)
    if output:
        save_report(data, output, output.lower().endswith(".json"))
        print(f"Saved report: {output}")


if __name__ == "__main__":
    main()
