# NetScope

Lightweight network diagnostics for Android Termux and desktop Python. Standard library only; no root access required.

## Features in v0.2.0

- Local outbound IPv4 address
- DNS lookup (IPv4/IPv6 records)
- TCP port connectivity checks
- Ping with packet-loss and RTT statistics parsing
- IPv6 DNS and connectivity check
- Optional traceroute support
- Save reports as JSON or TXT

## Install on Termux

```bash
pkg update
pkg install python git unzip
```

Extract the release ZIP, enter its directory, then run:

```bash
python -m netscope.cli --help
```

## Commands

```bash
# Quick report
python -m netscope.cli summary

# DNS lookup
python -m netscope.cli dns github.com

# IPv6-only DNS lookup
python -m netscope.cli dns github.com --ipv6

# Check TCP port
python -m netscope.cli port github.com 443

# Ping with parsed statistics
python -m netscope.cli ping 1.1.1.1 -c 4

# Check IPv6 connectivity
python -m netscope.cli ipv6

# Optional route trace (install traceroute first)
pkg install traceroute
python -m netscope.cli trace github.com

# Save a report
python -m netscope.cli summary --output report.txt
python -m netscope.cli summary --output report.json
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Privacy and limitations

NetScope only performs checks requested by the user. It does not scan local networks, enumerate devices, collect credentials, or upload results. TCP reachability can be affected by firewalls and mobile carriers. IPv6 DNS records do not prove IPv6 connectivity; the `ipv6` command separately tests a TCP connection to Cloudflare's public IPv6 resolver. Traceroute requires the optional system package and may be filtered by the network.

## License

MIT — see [LICENSE](LICENSE).
