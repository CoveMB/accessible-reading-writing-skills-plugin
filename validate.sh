#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 127
fi

export PYTHONDONTWRITEBYTECODE=1

python3 scripts/run_package_checks.py --scope full
