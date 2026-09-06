#!/usr/bin/env python3
"""Run package validation checks for the accessibility plugin."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CHECKS_BY_SCOPE = {
    "install": (("scripts/validate_plugin.py", "."),),
    "full": (
        ("scripts/validate_plugin.py", "."),
        ("-m", "unittest", "discover", "-s", "tests"),
    ),
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["install", "full"], default="full")
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    for check in CHECKS_BY_SCOPE[args.scope]:
        result = subprocess.run(
            [sys.executable, *check],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(
                result.stderr,
                file=sys.stderr,
                end="" if result.stderr.endswith("\n") else "\n",
            )
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
