# Security Policy

## Supported versions
Security fixes target the latest version on the `main` branch.

## Reporting a vulnerability
Please do not publish exploitable details in a public issue. Use GitHub's private vulnerability reporting feature for this repository if available. If it is unavailable, contact the maintainer through the contact method listed on the GitHub profile.

Include the affected version, impact, reproduction steps and a proposed mitigation where possible. Do not include real credentials or other people's private data.

## Scope and design
NetScope is a local diagnostic utility, not a vulnerability scanner. The web server is intended to bind only to loopback (`127.0.0.1`), validates local Host/Origin headers, limits request size and rate, and does not upload reports. Keep these boundaries intact.
