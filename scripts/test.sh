#!/usr/bin/env bash
# NetScope local test runner. No network access or third-party packages required.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: Python is not installed."
  echo "Termux: pkg install python"
  exit 1
fi
echo "== NetScope: compile check =="
python -m compileall -q netscope tests
echo
echo "== NetScope: unit tests =="
python -m unittest discover -s tests -v
echo
echo "All local checks passed."
