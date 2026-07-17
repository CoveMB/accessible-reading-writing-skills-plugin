#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 127
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  echo "Python 3.10 or newer is required." >&2
  exit 1
fi

export PYTHONDONTWRITEBYTECODE=1

if [[ " $* " != *" --dry-run "* ]]; then
  echo "Tip: run ./install.sh --dry-run to preview marketplace registration."
fi

set +e
python3 scripts/install_codex_plugin.py "$@"
status=$?
set -e

if [[ "$status" -ne 0 ]]; then
  echo "Marketplace setup failed with exit code ${status}." >&2
  exit "$status"
fi
