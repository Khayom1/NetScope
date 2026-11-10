<p align="center">
  <img src="assets/netscope-banner.gif" alt="NetScope — network diagnostics" width="100%">
</p>

<h1 align="center">NetScope</h1>
<p align="center"><strong>Understand your internet connection. Fix problems with confidence.</strong></p>
<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen.svg" alt="Zero dependencies">
  <img src="https://img.shields.io/badge/platform-Android%20%7C%20Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg" alt="Platforms">
</p>

NetScope is a free, open-source, privacy-first network troubleshooting toolkit. It checks DNS, secure TCP connectivity, HTTPS reachability, ping, IPv6 and routes — then **explains what the results mean and what to try next**.

No account. No subscription. No telemetry. No root access for the core checks. Built with Python's standard library.

<p align="center"><img src="assets/netscope-preview.png" alt="NetScope interface preview" width="100%"></p>

## Start here: one-command diagnosis

The fastest way to understand a connection problem:

```bash
python -m netscope.cli diagnose example.com
```

Get machine-readable output or save a report:

```bash
python -m netscope.cli diagnose example.com --lang tg
python -m netscope.cli diagnose example.com --lang ru
python -m netscope.cli diagnose example.com --lang en
python -m netscope.cli diagnose example.com --output diagnosis.json
```

NetScope checks name resolution, TCP port 443, HTTPS response and ping (when the system provides ping). It classifies common symptoms and gives practical next steps. **Ping failure alone is not treated as proof that the internet is down** because many networks block ICMP.

## Languages

The mobile-friendly web interface supports three languages:

- **Тоҷикӣ** — Tajik (default)
- **Русский** — Russian
- **English** — English

Use the language selector in the top-right corner. Your choice is saved locally in your browser. Smart diagnosis titles, explanations and recommended actions are returned in the selected language. The CLI diagnosis command also accepts `--lang tg`, `--lang ru` or `--lang en` (Tajik is the default). No translation API, account, or internet-based language service is used.

## Features

| Tool | What it helps answer |
|---|---|
| Smart diagnosis | What failed, why it may have failed, and what to try |
| DNS lookup | Can this hostname be translated into an IP address? |
| TCP port check | Can this device reach a specific host and port? |
| Ping | What packet loss and round-trip time does ICMP report? |
| IPv6 check | Are IPv6 records present, and is IPv6 TCP connectivity usable? |
| Traceroute | Which network hops respond on the route? |
| Local reports | Can I save results as JSON or readable TXT? |
| Local web UI | Can I run diagnostics from a mobile-friendly browser page? |

## Install

### Android (Termux)

```bash
pkg update
pkg install python git
git clone https://github.com/Khayom1/NetScope.git
cd NetScope
python -m netscope.cli diagnose example.com
```

Optional route tracing:

```bash
pkg install traceroute
python -m netscope.cli trace example.com
```

### Linux, macOS and Windows

Install Python 3.10 or newer, then:

```bash
git clone https://github.com/Khayom1/NetScope.git
cd NetScope
python -m netscope.cli diagnose example.com
```

The ping and traceroute commands depend on operating-system utilities. DNS, TCP and HTTPS checks use Python's standard library.

## Mobile-friendly web interface

```bash
python -m netscope.web
```

Open **http://127.0.0.1:8765** in a browser on the same device. The server binds to loopback only; it is not a public website or LAN service.

## Individual commands

```bash
python -m netscope.cli summary
python -m netscope.cli dns github.com
python -m netscope.cli dns github.com --ipv6
python -m netscope.cli port github.com 443
python -m netscope.cli ping 1.1.1.1 --count 4
python -m netscope.cli ipv6
python -m netscope.cli trace github.com
```

Add `--json` for structured output or `--output report.json` to save a report.

## Understanding diagnosis

- **DNS failed:** check the spelling, try another network, or compare DNS settings.
- **DNS works, HTTPS fails:** check captive portals, VPN/proxy settings, firewall rules, and whether the destination is online.
- **HTTPS works, ping fails:** the destination or network may block ICMP. The internet can still be working.
- **IPv6 DNS exists but connection fails:** the network may not provide usable IPv6 routing.

These are evidence-based hints, not claims to identify every cause. Network operators, firewalls, proxies and server policies can affect results.

## Privacy by design

- Diagnostics run on your device.
- NetScope has no analytics, tracking pixels, telemetry, accounts or remote report upload.
- The web server listens on `127.0.0.1` only.
- Reports are written only to the path you choose.
- The summary report does not include your local IP address by default.
- Network checks contact the destination you enter; DNS queries go to the resolver configured on your device.

Do not publish reports without reviewing them first. They can contain hostnames, IP addresses, timing data and error messages.

## Safety and responsible use

Use NetScope to troubleshoot your own device, website, server or a network you are authorized to test. Port checks and traceroute are diagnostic requests, not a security audit or vulnerability scanner. Do not use the tool to disrupt services or probe systems without permission.

## Test locally — no paid CI required

NetScope can be tested directly on your device. No GitHub Actions, cloud runner, paid service or third-party Python package is required.

### Android (Termux)

```bash
pkg install python git
git clone https://github.com/Khayom1/NetScope.git
cd NetScope
bash scripts/test.sh
```

### Linux, macOS and Windows

With Python 3.10 or newer:

```bash
python -m compileall -q netscope tests
python -m unittest discover -s tests -v
```

See [TESTING.md](TESTING.md) for troubleshooting. No third-party Python packages are required. Contributions, bug reports, translations and accessibility improvements are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Roadmap

- [x] Dependency-free CLI diagnostics
- [x] Loopback-only mobile web interface
- [x] Plain-language smart diagnosis
- [x] JSON/TXT report export
- [ ] DNS resolver comparison with clear caveats
- [ ] Optional history stored locally on the device
- [ ] More localized explanations and accessibility improvements

## License

MIT — free to use, modify, share and build upon. See [LICENSE](LICENSE).

**Built by [Khayom1](https://github.com/Khayom1) · [Report a bug](https://github.com/Khayom1/NetScope/issues/new/choose) · [Star the project](https://github.com/Khayom1/NetScope)**
