#!/usr/bin/env python3
"""Validate a local skills plugin package.

Checks:
- .codex-plugin/plugin.json exists and points to skills
- every skills/<name>/SKILL.md has valid frontmatter
- skill name matches folder name
- required name/description fields are present
- names satisfy Agent Skills naming constraints
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_utils import (
    agent_policy_fields,
    load_json_object_result,
    MIN_SHARED_DESCRIPTION_TERMS,
    is_generated_path,
    nested_mapping,
    nested_string,
    parse_markdown_frontmatter,
    parse_simple_yaml_mapping,
    significant_description_terms,
)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
MARKETPLACE_NAME = "accessible-reading-writing-local"
MARKETPLACE_DISPLAY_NAME = "Accessible Reading and Writing Local"
MARKETPLACE_RELATIVE_PATH = Path(".agents/plugins/marketplace.json")
MARKETPLACE_SAMPLE_RELATIVE_PATH = Path("marketplace.sample.json")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
BACKTICK_REFERENCE_RE = re.compile(r"`([^`\n]+)`")
LOCAL_REFERENCE_PREFIXES = (
    ".codex-plugin/",
    "assets/",
    "docs/",
    "examples/",
    "references/",
    "scripts/",
    "shared/",
    "skills/",
)
LOCAL_REFERENCE_ROOT_FILES = {
    "AGENTS.md",
    "CHANGELOG.md",
    "LICENSE",
    "MODE_REGISTRY.md",
    "README.md",
    "marketplace.sample.json",
    "validate.sh",
}
REFERENCE_FILE_SUFFIXES = {".md", ".yaml", ".yml"}


def is_external_reference(reference: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", reference))


def is_path_like_reference(reference: str) -> bool:
    if not reference or any(token in reference for token in [" ", "*", "<", ">", "|"]):
        return False
    if reference in {"assets/", "references/", "scripts/"}:
        return False
    if reference.startswith(("/", "~", "#")) or is_external_reference(reference):
        return False
    return (
        reference.startswith(("./", "../"))
        or reference.startswith(LOCAL_REFERENCE_PREFIXES)
        or reference in LOCAL_REFERENCE_ROOT_FILES
    )


def reference_candidates(root: Path, path: Path, reference: str) -> list[Path]:
    return [
        (path.parent / reference).resolve(),
        (root / reference).resolve(),
    ]


def reference_exists_inside_root(root: Path, candidates: list[Path]) -> tuple[bool, bool]:
    escaped = False
    for candidate in candidates:
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            escaped = True
            continue
        if candidate.exists():
            return True, False
    return False, escaped


def clean_reference(reference: str) -> str:
    return reference.strip().split("#", 1)[0]


def broken_references_from_values(root: Path, path: Path, label: str, references: list[str]) -> list[str]:
    errors: list[str] = []
    for reference in references:
        normalized = clean_reference(reference)
        if not is_path_like_reference(normalized):
            continue
        exists, escaped = reference_exists_inside_root(
            root,
            reference_candidates(root, path, normalized),
        )
        if escaped:
            errors.append(f"{label}: local reference escapes plugin root: {normalized}")
            continue
        if not exists:
            errors.append(f"{label}: broken local reference: {normalized}")
    return errors


def broken_local_references(root: Path, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    references = [*MARKDOWN_LINK_RE.findall(text), *BACKTICK_REFERENCE_RE.findall(text)]
    return broken_references_from_values(root, path, path.name, references)


def string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in string_values(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in string_values(child)]
    return []


def broken_manifest_references(root: Path, manifest_path: Path, manifest: dict[str, Any]) -> list[str]:
    return broken_references_from_values(root, manifest_path, "plugin.json", string_values(manifest))


def broken_yaml_references(root: Path, path: Path) -> list[str]:
    try:
        data = parse_simple_yaml_mapping(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return broken_references_from_values(root, path, path.name, string_values(data))


def broken_reference_file_errors(root: Path, path: Path) -> list[str]:
    errors = broken_local_references(root, path)
    if path.suffix in {".yaml", ".yml"}:
        errors.extend(broken_yaml_references(root, path))
    return errors


def skill_reference_files(skill_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in skill_dir.rglob("*")
        if path.is_file() and path.suffix in REFERENCE_FILE_SUFFIXES
    )


def skill_name_terms(skill_name: str) -> set[str]:
    return significant_description_terms(skill_name.replace("-", " "))


def manifest_errors(root: Path) -> tuple[dict | None, Path, list[str]]:
    errors: list[str] = []
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        return None, root / "skills", ["Missing .codex-plugin/plugin.json"]

    manifest, error = load_json_object_result(manifest_path)
    if error is not None:
        return None, root / "skills", [error]
    assert manifest is not None

    for field in ["name", "version", "description", "skills"]:
        if field not in manifest:
            errors.append(f"plugin.json missing required/recommended field: {field}")
    if not NAME_RE.match(str(manifest.get("name", ""))):
        errors.append("plugin.json name should be kebab-case lowercase")
    if not SEMVER_RE.match(str(manifest.get("version", ""))):
        errors.append("plugin.json version must use semantic versioning")

    skills_value = manifest.get("skills", "skills")
    if not isinstance(skills_value, str) or not skills_value.strip():
        errors.append("plugin.json skills must be a non-empty relative path")
        return manifest, root / "skills", errors
    skills_path = Path(skills_value)
    if skills_path.is_absolute():
        errors.append("plugin.json skills must be a relative path")
        return manifest, root / "skills", errors

    skills_dir = (root / skills_path).resolve()
    try:
        skills_dir.relative_to(root)
    except ValueError:
        errors.append("plugin.json skills path must stay inside plugin root")
    if not skills_dir.exists():
        errors.append(f"plugin.json skills path does not exist: {skills_value}")
    errors.extend(broken_manifest_references(root, manifest_path, manifest))
    return manifest, skills_dir, errors


def validate_release_contract(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    version = str(manifest.get("version", ""))
    readme_path = root / "README.md"
    changelog_path = root / "CHANGELOG.md"
    readme_lines = (
        {line.strip() for line in readme_path.read_text(encoding="utf-8").splitlines()}
        if readme_path.exists()
        else set()
    )
    changelog_lines = (
        {line.strip() for line in changelog_path.read_text(encoding="utf-8").splitlines()}
        if changelog_path.exists()
        else set()
    )
    if f"Version: {version}" not in readme_lines:
        errors.append(f"README.md must report Version: {version}")
    if f"## {version}" not in changelog_lines:
        errors.append(f"CHANGELOG.md must include a {version} release heading")
    return errors


def marketplace_entry_errors(entry: object, expected_plugin_name: str) -> list[str]:
    if not isinstance(entry, dict):
        return ["marketplace plugin entry must be an object"]
    errors: list[str] = []
    if entry.get("name") != expected_plugin_name:
        errors.append(
            f"marketplace plugin name must match manifest name {expected_plugin_name!r}"
        )
    if entry.get("source") != {"source": "local", "path": "./"}:
        errors.append("marketplace source must be the repository root: local ./")
    if entry.get("policy") != {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }:
        errors.append("marketplace policy must use AVAILABLE and ON_INSTALL")
    if entry.get("category") != "Productivity":
        errors.append("marketplace category must be Productivity")
    return errors


def validate_marketplace(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    marketplace_path = root / MARKETPLACE_RELATIVE_PATH
    marketplace, marketplace_error = load_json_object_result(marketplace_path)
    if marketplace_error is not None:
        return [marketplace_error]
    assert marketplace is not None

    if marketplace.get("name") != MARKETPLACE_NAME:
        errors.append(f"marketplace name must be {MARKETPLACE_NAME!r}")
    interface = marketplace.get("interface")
    if not isinstance(interface, dict) or interface.get("displayName") != MARKETPLACE_DISPLAY_NAME:
        errors.append(f"marketplace displayName must be {MARKETPLACE_DISPLAY_NAME!r}")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        errors.append("marketplace must contain exactly one plugin entry")
    else:
        errors.extend(marketplace_entry_errors(plugins[0], str(manifest.get("name", ""))))

    sample_path = root / MARKETPLACE_SAMPLE_RELATIVE_PATH
    sample, sample_error = load_json_object_result(sample_path)
    if sample_error is not None:
        errors.append(sample_error)
    elif sample is not None and (
        sample.get("name") != marketplace.get("name")
        or sample.get("interface") != marketplace.get("interface")
        or sample.get("plugins") != marketplace.get("plugins")
    ):
        errors.append("marketplace.sample.json must match the canonical marketplace")
    return errors


def validate_agent_metadata(
    skill_dir: Path,
    skill_name: str,
    skill_description: str,
) -> tuple[str, list[str]]:
    errors: list[str] = []
    agent_path = skill_dir / "agents" / "openai.yaml"
    if not agent_path.exists():
        return "", [f"{skill_name}: missing agents/openai.yaml"]
    text = agent_path.read_text(encoding="utf-8")
    metadata = parse_simple_yaml_mapping(text)
    interface = nested_mapping(metadata, "interface")
    policy = nested_mapping(metadata, "policy")
    display_name = nested_string(interface, "display_name")
    short_description = nested_string(interface, "short_description")
    default_prompt = nested_string(interface, "default_prompt")
    if not short_description:
        errors.append(f"{skill_name}: agents/openai.yaml missing interface.short_description")
    if not default_prompt:
        errors.append(f"{skill_name}: agents/openai.yaml missing interface.default_prompt")
    if not display_name:
        errors.append(f"{skill_name}: agents/openai.yaml missing interface.display_name")
    elif not (skill_name_terms(skill_name) & significant_description_terms(display_name)):
        errors.append(f"{skill_name}: agents/openai.yaml display_name appears stale")
    if not isinstance(policy.get("allow_implicit_invocation"), bool):
        errors.append(
            f"{skill_name}: agents/openai.yaml policy.allow_implicit_invocation must be boolean"
        )
    for field_name, expected_value in agent_policy_fields(skill_name).items():
        value = policy.get(field_name)
        if value != expected_value:
            errors.append(
                f"{skill_name}: agents/openai.yaml policy.{field_name} must be {expected_value!r}"
            )
    if short_description and skill_description:
        shared_terms = significant_description_terms(short_description) & significant_description_terms(
            skill_description
        )
        if len(shared_terms) < MIN_SHARED_DESCRIPTION_TERMS:
            errors.append(
                f"{skill_name}: agents/openai.yaml short_description appears stale "
                f"({len(shared_terms)} shared significant terms)"
            )
    return default_prompt, errors


def validate_skill_dir(
    root: Path,
    skill_dir: Path,
    seen_names: set[str],
    expected_version: str,
) -> tuple[str, str, list[str]]:
    errors: list[str] = []
    skill_name = skill_dir.name
    skill_path = skill_dir / "SKILL.md"
    readme_path = skill_dir / "README.md"

    if not skill_path.exists():
        return skill_name, "", [f"{skill_name}: missing SKILL.md"]

    if not readme_path.exists():
        errors.append(f"{skill_name}: missing README.md")

    try:
        frontmatter = parse_markdown_frontmatter(skill_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return skill_name, "", [*errors, f"{skill_name}: frontmatter error: {exc}"]

    name = nested_string(frontmatter, "name")
    description = nested_string(frontmatter, "description")
    if not name:
        errors.append(f"{skill_name}: missing name")
    if not description:
        errors.append(f"{skill_name}: missing description")
    if len(description) > 1024:
        errors.append(f"{skill_name}: description exceeds 1024 characters")
    metadata_version = nested_string(nested_mapping(frontmatter, "metadata"), "version")
    if metadata_version and expected_version and metadata_version != expected_version:
        errors.append(
            f"{skill_name}: metadata.version {metadata_version!r} must match plugin version "
            f"{expected_version!r}"
        )
    if name != skill_name:
        errors.append(f"{skill_name}: frontmatter name '{name}' does not match folder")
    if not NAME_RE.match(name):
        errors.append(f"{skill_name}: invalid skill name '{name}'")
    if name in seen_names:
        errors.append(f"duplicate skill name: {name}")
    seen_names.add(name)

    default_prompt, agent_errors = validate_agent_metadata(skill_dir, skill_name, description)
    errors.extend(agent_errors)
    for path in skill_reference_files(skill_dir):
        errors.extend(f"{skill_name}: {error}" for error in broken_reference_file_errors(root, path))
    return skill_name, default_prompt, errors


def validate_project_references(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or path.is_dir() or path.is_symlink():
            continue
        relative_path = path.relative_to(root)
        if is_generated_path(relative_path):
            continue
        if relative_path.parts[:1] == ("skills",):
            continue
        if path.suffix in {".md", ".yaml", ".yml"}:
            errors.extend(
                f"{relative_path}: {error}"
                for error in broken_local_references(root, path)
            )
    return errors


def validate_skills(root: Path, skills_dir: Path, expected_version: str) -> list[str]:
    errors: list[str] = []
    if not skills_dir.exists():
        return ["Missing skills/ directory"]

    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not skill_dirs:
        return ["skills/ directory contains no skill folders"]

    seen_names: set[str] = set()
    seen_prompts: dict[str, str] = {}
    for skill_dir in skill_dirs:
        skill_name, default_prompt, skill_errors = validate_skill_dir(
            root,
            skill_dir,
            seen_names,
            expected_version,
        )
        errors.extend(skill_errors)
        if default_prompt:
            previous_skill = seen_prompts.get(default_prompt)
            if previous_skill is not None:
                errors.append(f"duplicate default_prompt in {previous_skill} and {skill_name}")
            seen_prompts[default_prompt] = skill_name
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local skills plugin package.")
    parser.add_argument(
        "plugin_root",
        nargs="?",
        default=".",
        help="Plugin root to validate. Defaults to the current directory.",
    )
    args = parser.parse_args()

    root = Path(args.plugin_root).expanduser().resolve()
    manifest, skills_dir, errors = manifest_errors(root)
    expected_version = str(manifest.get("version", "")) if manifest else ""
    if manifest is not None:
        errors.extend(validate_release_contract(root, manifest))
        errors.extend(validate_marketplace(root, manifest))
    errors.extend(validate_skills(root, skills_dir, expected_version))
    errors.extend(validate_project_references(root))

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"Validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
