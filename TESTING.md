# Testing NetScope without paid services

NetScope intentionally does not require GitHub Actions, cloud runners, external CI services, API keys, accounts, or third-party Python packages.

## Android (Termux)

```bash
pkg update
pkg install python git
git clone https://github.com/Khayom1/NetScope.git
cd NetScope
bash scripts/test.sh
```

If you already cloned the repository:

```bash
cd NetScope
git pull
bash scripts/test.sh
```

## Linux, macOS, Windows

Use Python 3.10 or newer:

```bash
python -m compileall -q netscope tests
python -m unittest discover -s tests -v
```

On systems where the Python launcher is `python3`, replace `python` with `python3`.

## What the test command does

1. Compiles the package and tests to detect syntax errors.
2. Runs the standard-library `unittest` test suite.
3. Exits with a non-zero status if a check fails.

Most tests use mocks and do not need a working internet connection. A passing unit-test suite does not replace manual checks on each supported operating system.

## Optional network smoke test

After the unit tests pass and you have an internet connection:

```bash
python -m netscope.cli diagnose example.com
python -m netscope.web
```

Open `http://127.0.0.1:8765` on the same device. Network smoke tests contact the host you specify; use a host you are allowed to test.

## Cost policy

- No paid CI is required to contribute or use NetScope.
- No mandatory cloud service or paid API.
- No external dependency installation for the test suite.
- Local tests run on the user's own device.
