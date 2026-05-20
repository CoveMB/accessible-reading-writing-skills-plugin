#!/usr/bin/env python3
"""Run package validation checks for the accessibility plugin."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INSTALL_CHECKS = (("scripts/validate_plugin.py", "."),)
UNIT_TEST_CHECKS = (("-m", "unittest", "discover", "-s", "tests"),)
FULL_CHECKS = (*INSTALL_CHECKS, *UNIT_TEST_CHECKS)

PackageCheck = tuple[str, ...]


def checks_for_scope(scope: str) -> tuple[PackageCheck, ...]:
    checks_by_scope = {
        "install": INSTALL_CHECKS,
        "full": FULL_CHECKS,
    }
    return checks_by_scope[scope]


def command_with_python(check: PackageCheck) -> list[str]:
    return [sys.executable, *check]


def run_check(check: PackageCheck, root: Path) -> int:
    result = subprocess.run(
        command_with_python(check),
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    return result.returncode


def run_checks(scope: str, root: Path) -> int:
    for check in checks_for_scope(scope):
        returncode = run_check(check, root)
        if returncode != 0:
            return returncode
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["install", "full"], default="full")
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return run_checks(args.scope, args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
