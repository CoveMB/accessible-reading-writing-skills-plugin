#!/usr/bin/env python3
"""Export self-contained Agent Skills to a new directory without installing them."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from package_plugin import run_validation
from plugin_utils import (
    PORTABLE_SHARED_DOCUMENTS,
    PORTABLE_SKILL_FILES,
    load_plugin_manifest,
)
from validate_plugin import MARKDOWN_LINK_RE, is_external_reference, validate_skill_dir


def read_resource(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Portable resource must not be a symlink: {relative}")
    if not path.is_file():
        raise ValueError(f"Missing portable resource: {relative}")
    return path.read_text(encoding="utf-8")


def validate_portable_links(skill: Path) -> None:
    for document in skill.rglob("*.md"):
        for reference in MARKDOWN_LINK_RE.findall(document.read_text(encoding="utf-8")):
            if is_external_reference(reference):
                continue
            target = (document.parent / reference).resolve()
            if not target.is_relative_to(skill.resolve()) or not target.is_file():
                raise ValueError(f"Unbundled portable reference in {skill.name}/{document.name}: {reference}")


def export_skills(root: Path, output: Path) -> int:
    if output.exists() or output.is_symlink():
        raise ValueError(f"Export destination already exists: {output}")
    if run_validation(root) != 0:
        raise ValueError("Source validation failed; no skills exported")

    manifest = load_plugin_manifest(root)
    skills_root = root / manifest["skills"]
    shared_documents = {
        name: read_resource(root, root / "docs" / name)
        for name in PORTABLE_SHARED_DOCUMENTS
    }
    license_text = read_resource(root, root / "LICENSE")
    with TemporaryDirectory(prefix="accessible-reading-writing-export-") as temporary:
        staged = Path(temporary) / "skills"
        staged.mkdir()
        for skill in sorted(skills_root.iterdir()):
            if not skill.is_dir():
                continue
            target = staged / skill.name
            for relative in PORTABLE_SKILL_FILES:
                content = read_resource(root, skill / relative)
                if relative.endswith(".md"):
                    for name in shared_documents:
                        content = content.replace(f"../../docs/{name}", f"references/{name}")
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            for name, content in shared_documents.items():
                destination = target / "references" / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            (target / "LICENSE").write_text(license_text, encoding="utf-8")
            _, _, errors = validate_skill_dir(
                target, target, set(), manifest["version"]
            )
            if errors:
                raise ValueError("Invalid portable skill:\n" + "\n".join(errors))
            validate_portable_links(target)

        # copytree refuses an existing directory, file, or dangling symlink.
        # Publish only after every independently movable skill has validated.
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, output)
        return len(list(staged.iterdir()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, required=True, help="New export directory; must not exist.")
    args = parser.parse_args()
    try:
        count = export_skills(args.root.resolve(), args.out.absolute())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Exported {count} skills to {args.out.absolute()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
