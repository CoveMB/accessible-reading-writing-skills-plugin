#!/usr/bin/env python3
"""Validate the plugin and register its repository marketplace with Codex."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_utils import load_plugin_manifest, plugin_manifest_path

MARKETPLACE_NAME = "accessible-reading-writing-local"
VALIDATION_RUNNER = Path(__file__).resolve().parent / "run_package_checks.py"


class InstallPlan(NamedTuple):
    root: Path
    plugin_name: str
    plugin_selector: str


class CodexCommandError(ValueError):
    def __init__(self, message: str, returncode: int):
        super().__init__(message)
        self.returncode = returncode


def plugin_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_validation(root: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATION_RUNNER), "--scope", "install", "--root", str(root)],
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def build_install_plan(plugin_root: Path) -> InstallPlan:
    root = plugin_root.expanduser().resolve()
    if not plugin_manifest_path(root).exists():
        raise ValueError(f"Not a plugin root: {root}")
    try:
        plugin_name = str(load_plugin_manifest(root)["name"])
    except Exception as exc:
        raise ValueError(f"Unable to read plugin manifest: {exc}") from exc
    return InstallPlan(
        root=root,
        plugin_name=plugin_name,
        plugin_selector=f"{plugin_name}@{MARKETPLACE_NAME}",
    )


def run_codex(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True)


def parse_marketplace_list(output: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Codex returned invalid marketplace JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("marketplaces"), list):
        raise ValueError("Codex marketplace list did not contain a marketplaces array")
    return [entry for entry in payload["marketplaces"] if isinstance(entry, dict)]


def matching_marketplace(marketplaces: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (entry for entry in marketplaces if entry.get("name") == MARKETPLACE_NAME),
        None,
    )


def same_path(first: Path, second: Path) -> bool:
    return first.expanduser().resolve() == second.expanduser().resolve()


def register_marketplace(plan: InstallPlan) -> None:
    list_command = ["codex", "plugin", "marketplace", "list", "--json"]
    list_result = run_codex(list_command)
    if list_result.returncode != 0:
        detail = list_result.stderr.strip() or list_result.stdout.strip() or "unknown error"
        raise CodexCommandError(
            f"Unable to list Codex marketplaces: {detail}",
            list_result.returncode,
        )

    existing = matching_marketplace(parse_marketplace_list(list_result.stdout))
    if existing is not None:
        existing_root = existing.get("root")
        if not isinstance(existing_root, str) or not same_path(Path(existing_root), plan.root):
            raise ValueError(
                f"Marketplace {MARKETPLACE_NAME!r} is already registered at "
                f"{existing_root!r}; refusing to replace it with {str(plan.root)!r}"
            )
        print(f"Marketplace already registered: {MARKETPLACE_NAME} -> {plan.root}")
        return

    add_command = [
        "codex",
        "plugin",
        "marketplace",
        "add",
        str(plan.root),
        "--json",
    ]
    add_result = run_codex(add_command)
    if add_result.returncode != 0:
        detail = add_result.stderr.strip() or add_result.stdout.strip() or "unknown error"
        raise CodexCommandError(
            f"Unable to register the Codex marketplace: {detail}",
            add_result.returncode,
        )
    print(f"Registered marketplace: {MARKETPLACE_NAME} -> {plan.root}")


def print_next_steps(plan: InstallPlan) -> None:
    print("Install the plugin through Codex:")
    print(f"codex plugin add {plan.plugin_selector}")
    print("For an existing installation, follow the README update or 1.0 migration steps.")
    print("Start a new Codex task or CLI session after installation.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register the Accessible Reading and Writing repository marketplace."
    )
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=plugin_root_from_script(),
        help="Plugin and marketplace root. Defaults to this repository root.",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Deprecated alias for local marketplace registration; no symlink is created.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the marketplace and plugin commands without running Codex.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = build_install_plan(args.plugin_root)
        run_validation(plan.root)
        if shutil.which("codex") is None:
            raise ValueError("The codex command is required but was not found")
        if args.link:
            print("Warning: --link is deprecated; the marketplace uses the checkout directly and no symlink is created.")
        if args.dry_run:
            print("Dry run: no Codex configuration will be changed.")
            print(f"codex plugin marketplace add {plan.root}")
            print_next_steps(plan)
            return 0
        register_marketplace(plan)
        print_next_steps(plan)
        return 0
    except CodexCommandError as exc:
        print(f"Marketplace setup failed: {exc}", file=sys.stderr)
        return exc.returncode
    except ValueError as exc:
        print(f"Marketplace setup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
