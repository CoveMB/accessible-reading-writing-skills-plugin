#!/usr/bin/env python3
"""Package this plugin directory as a zip."""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_utils import (
    copy_package_tree,
    package_files as included_package_files,
    plugin_version,
)


VALIDATION_SCRIPT = Path(__file__).resolve().parent / "validate_plugin.py"
DEFAULT_PACKAGE_STEM = "accessible-reading-writing-plugin"


def package_output_files(root: Path, output_path: Path, temporary_output_path: Path) -> list[Path]:
    return [
        path
        for path in included_package_files(root)
        if path.resolve() not in {output_path.resolve(), temporary_output_path.resolve()}
    ]


def write_package(root: Path, output_path: Path) -> None:
    temporary_output_path = output_path.with_suffix(output_path.suffix + ".tmp")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if temporary_output_path.exists():
        temporary_output_path.unlink()
    with TemporaryDirectory(prefix="accessible-reading-writing-package-") as temporary_directory:
        staged_root = Path(temporary_directory) / root.name
        copy_package_tree(root, staged_root)
        if run_validation(staged_root) != 0:
            raise RuntimeError("staged package validation failed")
        try:
            with zipfile.ZipFile(
                temporary_output_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                for path in package_output_files(
                    staged_root,
                    output_path,
                    temporary_output_path,
                ):
                    archive.write(
                        path,
                        root.name + "/" + str(path.relative_to(staged_root)),
                    )
            temporary_output_path.replace(output_path)
        finally:
            if temporary_output_path.exists():
                temporary_output_path.unlink()


def default_output_path(root: Path) -> Path:
    return Path(f"{DEFAULT_PACKAGE_STEM}-v{plugin_version(root)}.zip")


def run_validation(root: Path) -> int:
    result = subprocess.run(
        [sys.executable, str(VALIDATION_SCRIPT), str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Package this plugin directory as a zip.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Plugin root to package. Defaults to this repository root.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help=f"Zip file to write. Defaults to {DEFAULT_PACKAGE_STEM}-v<manifest-version>.zip.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    out = (args.out if args.out is not None else default_output_path(root)).resolve()
    validation_status = run_validation(root)
    if validation_status != 0:
        return validation_status
    try:
        write_package(root, out)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
