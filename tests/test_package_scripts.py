from __future__ import annotations

import json
import io
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_codex_plugin
import package_plugin
import plugin_utils
import run_package_checks
import validate_plugin


UNIT_TEST_CHECK = ("-m", "unittest", "discover", "-s", "tests")
SKILL_VALIDATION_CHECK = ("scripts/validate_plugin.py", ".")
CI_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "skill-tests.yml"
FULL_PACKAGE_CHECK_COMMAND = "python3 scripts/run_package_checks.py --scope full"


def write_plugin_manifest(root: Path, plugin_name: str) -> None:
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps({"name": plugin_name}), encoding="utf-8")


class PackageCheckTests(unittest.TestCase):
    def test_full_scope_runs_skill_validation(self) -> None:
        self.assertIn(
            SKILL_VALIDATION_CHECK,
            run_package_checks.checks_for_scope("full"),
        )

    def test_full_scope_runs_unit_tests(self) -> None:
        self.assertIn(UNIT_TEST_CHECK, run_package_checks.checks_for_scope("full"))


class ContinuousIntegrationTests(unittest.TestCase):
    def test_skill_test_workflow_runs_full_package_checks(self) -> None:
        self.assertTrue(CI_WORKFLOW_PATH.exists())
        workflow_text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn(FULL_PACKAGE_CHECK_COMMAND, workflow_text)


class PackageArchiveSafetyTests(unittest.TestCase):
    def test_staged_validation_rejects_source_only_reference_and_preserves_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source = temporary_root / "source-plugin"
            shutil.copytree(
                ROOT,
                source,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    "*.zip",
                ),
            )
            references = source / "references"
            references.mkdir()
            (references / "development.md").write_text(
                "# Development reference\n",
                encoding="utf-8",
            )
            with (source / "README.md").open("a", encoding="utf-8") as readme:
                readme.write("\n[Development reference](references/development.md)\n")
            output = temporary_root / "plugin.zip"
            output.write_bytes(b"existing archive")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, package_plugin.run_validation(source))

            with redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, "staged package validation failed"):
                    package_plugin.write_package(source, output)

            self.assertEqual(b"existing archive", output.read_bytes())
            self.assertFalse(output.with_suffix(".zip.tmp").exists())

    def test_archive_write_failure_preserves_archive_and_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "plugin.zip"
            output.write_bytes(b"existing archive")

            with redirect_stdout(io.StringIO()):
                with mock.patch.object(
                    zipfile.ZipFile,
                    "write",
                    autospec=True,
                    side_effect=OSError("injected archive write failure"),
                ):
                    with self.assertRaisesRegex(OSError, "injected archive write failure"):
                        package_plugin.write_package(ROOT, output)

            self.assertEqual(b"existing archive", output.read_bytes())
            self.assertFalse(output.with_suffix(".zip.tmp").exists())

    def test_archive_membership_is_unchanged_and_extracted_package_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            output = temporary_root / "plugin.zip"

            with redirect_stdout(io.StringIO()):
                package_plugin.write_package(ROOT, output)

            expected_members = {
                f"{ROOT.name}/{path.relative_to(ROOT)}"
                for path in plugin_utils.package_files(ROOT)
            }
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(expected_members, set(archive.namelist()))
                extract_root = temporary_root / "extracted"
                archive.extractall(extract_root)

            packaged_root = extract_root / ROOT.name
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, run_package_checks.run_checks("install", packaged_root))


class InstallerSafetyTests(unittest.TestCase):
    def test_dry_run_copy_does_not_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source-plugin"
            destination = root / "example-plugin"
            source.mkdir()
            write_plugin_manifest(source, "example-plugin")

            with redirect_stdout(io.StringIO()):
                install_codex_plugin.copy_plugin(source, destination, dry_run=True)

            self.assertFalse(destination.exists())

    def test_dry_run_link_does_not_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source-plugin"
            destination = root / "example-plugin"
            source.mkdir()
            write_plugin_manifest(source, "example-plugin")

            with redirect_stdout(io.StringIO()):
                install_codex_plugin.link_plugin(source, destination, dry_run=True)

            self.assertFalse(destination.exists())

    def test_link_plugin_creates_destination_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source-plugin"
            destination = root / "example-plugin"
            source.mkdir()
            write_plugin_manifest(source, "example-plugin")

            with redirect_stdout(io.StringIO()):
                install_codex_plugin.link_plugin(source, destination, dry_run=False)

            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), source.resolve())

    def test_link_plugin_cache_creates_version_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source-plugin"
            destination = root / "cache" / "example-plugin" / "1.0.0"
            source.mkdir()
            write_plugin_manifest(source, "example-plugin")
            manifest_path = source / ".codex-plugin" / "plugin.json"
            manifest_path.write_text(
                json.dumps({"name": "example-plugin", "version": "1.0.0"}),
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()):
                install_codex_plugin.link_plugin_cache(source, destination, dry_run=False)

            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), source.resolve())

    def test_link_plugin_cache_rejects_unexpected_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source-plugin"
            destination = root / "cache" / "other-plugin" / "1.0.0"
            source.mkdir()
            write_plugin_manifest(source, "example-plugin")
            manifest_path = source / ".codex-plugin" / "plugin.json"
            manifest_path.write_text(
                json.dumps({"name": "example-plugin", "version": "1.0.0"}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                install_codex_plugin.link_plugin_cache(source, destination, dry_run=False)

    def test_destination_with_unrelated_content_is_not_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "example-plugin"
            destination.mkdir()
            (destination / "notes.txt").write_text("keep this file", encoding="utf-8")

            self.assertFalse(
                install_codex_plugin.is_safe_destination(destination, "example-plugin")
            )

    def test_marketplace_entry_replacement_preserves_other_plugins(self) -> None:
        existing = {
            "name": "local-personal-plugins",
            "interface": {"displayName": "Local Personal Plugins"},
            "plugins": [
                {"name": "other-plugin", "source": {"path": "./other"}},
                {"name": "example-plugin", "source": {"path": "./old"}},
            ],
        }
        entry = install_codex_plugin.marketplace_entry("example-plugin", "./new")

        updated = install_codex_plugin.replace_marketplace_entry(existing, entry)

        self.assertEqual(
            [plugin["name"] for plugin in updated["plugins"]],
            ["other-plugin", "example-plugin"],
        )
        self.assertEqual(updated["plugins"][1]["source"]["path"], "./new")


class ValidatorTests(unittest.TestCase):
    def test_skill_frontmatter_name_must_match_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            skill_dir = root / "skills" / "example-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "README.md").write_text("# example-skill\n", encoding="utf-8")
            (skill_dir / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: different-skill",
                        "description: Use when example material needs validation coverage.",
                        "metadata:",
                        '  version: "1.0.0"',
                        "---",
                    ]
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_plugin.validate_skill_dir(
                root,
                skill_dir,
                seen_names=set(),
                expected_version="1.0.0",
            )

            self.assertIn(
                "example-skill: frontmatter name 'different-skill' does not match folder",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
