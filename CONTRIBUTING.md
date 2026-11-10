# Contributing to NetScope

Thanks for helping make network troubleshooting easier for everyone.

## Before opening a change
- Search existing issues and pull requests.
- For bugs, include the operating system, Python version, command, expected result and sanitized output.
- Never include passwords, tokens, public IPs you do not want shared, or private hostnames.

## Development
NetScope uses only the Python standard library.

```bash
python -m unittest discover -s tests -v
python -m netscope.cli diagnose example.com
python -m netscope.web
```

## Pull requests
- Keep changes focused and explain the user problem they solve.
- Add or update tests for behavior changes.
- Preserve support for Python 3.10+.
- Do not add telemetry, analytics, mandatory accounts, paid APIs or remote report uploads.
- Keep network tests bounded by explicit timeouts.
- Document platform-specific limitations, especially Android/Termux behavior.

By contributing, you agree that your contributions are provided under the repository's MIT license.
