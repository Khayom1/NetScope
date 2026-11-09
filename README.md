NetScope

Lightweight network diagnostics for Android Termux and desktop Python.

NetScope is a small, dependency-free Python tool for checking DNS resolution, TCP connectivity, ping statistics, IPv6 connectivity, and network routes.

It uses Python's standard library and does not require root access.

Features

- Network summary — inspect basic outbound network information.
- DNS lookup — resolve IPv4 and IPv6 records.
- TCP connectivity — test whether a host and port are reachable.
- Ping analysis — inspect packet loss and round-trip time (RTT).
- IPv6 diagnostics — check IPv6 DNS records and connectivity separately.
- Traceroute — optionally inspect network routing paths.
- Report export — save diagnostic results as JSON or TXT.

Requirements

- Python 3.10 or newer
- Android Termux or desktop Python environment
- Internet connection for network checks
- Optional: "traceroute" system utility

Installation

Android Termux

Install the required packages:

pkg update
pkg install python git

Clone the repository:

git clone https://github.com/Khayom1/NetScope.git
cd NetScope

Check the available commands:

python -m netscope.cli --help

Desktop

Clone the repository and enter its directory:

git clone https://github.com/Khayom1/NetScope.git
cd NetScope

Run NetScope with Python:

python -m netscope.cli --help

Usage

Network summary

python -m netscope.cli summary

DNS lookup

python -m netscope.cli dns github.com

IPv6 DNS lookup:

python -m netscope.cli dns github.com --ipv6

TCP port check

python -m netscope.cli port github.com 443

Ping diagnostics

python -m netscope.cli ping 1.1.1.1 -c 4

IPv6 connectivity

python -m netscope.cli ipv6

Traceroute

Install the optional utility on Termux:

pkg install traceroute

Then run:

python -m netscope.cli trace github.com

Export reports

Save results as JSON:

python -m netscope.cli summary --output report.json

Save results as TXT:

python -m netscope.cli summary --output report.txt

Running tests

Run the unit test suite:

python -m unittest discover -s tests -v

Privacy and security

NetScope performs network checks requested by the user.

- It does not scan local networks or enumerate devices.
- It does not collect credentials.
- It does not upload diagnostic reports to a remote server.
- Reports are saved locally when requested.

Only test systems and network services that you own or have permission to examine.

Limitations

Network results may vary depending on firewalls, DNS configuration, mobile carriers, and internet connectivity.

An IPv6 DNS record does not guarantee that IPv6 connectivity is available. The IPv6 command performs a separate connectivity check.

Traceroute is optional and may be blocked or filtered by some networks.

Project

- Repository: https://github.com/Khayom1/NetScope
- Version: 0.2.0
- License: MIT

License

This project is licensed under the MIT License. See "LICENSE" (LICENSE).

---

Contributions, bug reports, and suggestions are welcome.
