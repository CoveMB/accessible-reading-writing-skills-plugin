from __future__ import annotations

import json
import io
import re
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

import package_plugin
import plugin_utils
import run_package_checks
import validate_plugin


UNIT_TEST_CHECK = ("-m", "unittest", "discover", "-s", "tests")
SKILL_VALIDATION_CHECK = ("scripts/validate_plugin.py", ".")
CI_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "skill-tests.yml"
FULL_PACKAGE_CHECK_COMMAND = "python3 scripts/run_package_checks.py --scope full"


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


class MarketplaceContractTests(unittest.TestCase):
    def test_public_instructions_do_not_directly_mutate_codex_cache(self) -> None:
        command_pattern = re.compile(
            r"^\s*(?:cp|del|ln|mkdir|mv|rm|rmdir|Remove-Item)\b.*"
            r"\.codex[/\\]plugins[/\\]cache",
            re.IGNORECASE,
        )
        documentation_path = ROOT / "README.md"
        for line in documentation_path.read_text(encoding="utf-8").splitlines():
            self.assertIsNone(command_pattern.search(line), f"{documentation_path}: {line}")

    def test_update_instructions_do_not_expect_an_available_entry_for_installed_plugin(
        self,
    ) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        update_section = readme.partition("## Update")[2].partition("## Skills")[0]

        self.assertTrue(update_section)
        self.assertNotIn("--available", update_section)
        self.assertNotIn("available entry", update_section.lower())
        self.assertIn("codex plugin marketplace list --json", update_section)
        self.assertIn(".codex-plugin/plugin.json", update_section)


class ValidatorTests(unittest.TestCase):
    def test_release_contract_requires_exact_version_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text(
                "Version: 1.0.0-alpha\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text(
                "## 1.0.0-alpha\n",
                encoding="utf-8",
            )

            errors = validate_plugin.validate_release_contract(
                root,
                {"version": "1.0.0"},
            )

            self.assertIn("README.md must report Version: 1.0.0", errors)
            self.assertIn("CHANGELOG.md must include a 1.0.0 release heading", errors)

    def test_skill_metadata_version_states(self) -> None:
        cases = (
            (
                "valid",
                ("metadata:", '  version: "1.0.0"'),
                None,
            ),
            (
                "missing",
                (),
                "example-skill: missing metadata.version",
            ),
            (
                "empty",
                ("metadata:", '  version: ""'),
                "example-skill: missing metadata.version",
            ),
            (
                "non-string",
                ("metadata:", "  version: true"),
                "example-skill: metadata.version must be a string",
            ),
            (
                "mismatch",
                ("metadata:", '  version: "2.0.0"'),
                (
                    "example-skill: metadata.version '2.0.0' "
                    "must match plugin version '1.0.0'"
                ),
            ),
        )

        for case_name, metadata_lines, expected_error in cases:
            with self.subTest(case=case_name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                skill_dir = root / "skills" / "example-skill"
                skill_dir.mkdir(parents=True)
                (skill_dir / "README.md").write_text(
                    "# example-skill\n",
                    encoding="utf-8",
                )
                (skill_dir / "SKILL.md").write_text(
                    "\n".join(
                        (
                            "---",
                            "name: example-skill",
                            "description: Use when example material needs validation.",
                            *metadata_lines,
                            "---",
                        )
                    ),
                    encoding="utf-8",
                )

                _, _, errors = validate_plugin.validate_skill_dir(
                    root,
                    skill_dir,
                    seen_names=set(),
                    expected_version="1.0.0",
                )

                metadata_errors = [
                    error for error in errors if "metadata.version" in error
                ]
                if expected_error is None:
                    self.assertEqual([], metadata_errors)
                else:
                    self.assertEqual([expected_error], metadata_errors)

    def test_marketplace_validator_states(self) -> None:
        valid_marketplace = {
            "name": "accessible-reading-writing-local",
            "interface": {
                "displayName": "Accessible Reading and Writing Local",
            },
            "plugins": [
                {
                    "name": "expected-plugin",
                    "source": {"source": "local", "path": "./"},
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        }
        cases = (
            ("valid", None, None, None),
            (
                "marketplace-name",
                ("name",),
                "wrong-marketplace",
                "marketplace name must be 'accessible-reading-writing-local'",
            ),
            (
                "display-name",
                ("interface", "displayName"),
                "Wrong display name",
                (
                    "marketplace displayName must be "
                    "'Accessible Reading and Writing Local'"
                ),
            ),
            (
                "entry-cardinality",
                ("plugins",),
                [],
                "marketplace must contain exactly one plugin entry",
            ),
            (
                "plugin-name",
                ("plugins", 0, "name"),
                "wrong-plugin",
                "marketplace plugin name must match manifest name 'expected-plugin'",
            ),
            (
                "source",
                ("plugins", 0, "source"),
                {"source": "local", "path": "./wrong"},
                "marketplace source must be the repository root: local ./",
            ),
            (
                "policy",
                ("plugins", 0, "policy"),
                {"installation": "AVAILABLE", "authentication": "NONE"},
                "marketplace policy must use AVAILABLE and ON_INSTALL",
            ),
            (
                "category",
                ("plugins", 0, "category"),
                "Other",
                "marketplace category must be Productivity",
            ),
        )

        for case_name, mutation_path, value, expected_error in cases:
            with self.subTest(case=case_name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
                marketplace_path.parent.mkdir(parents=True)

                payload = json.loads(json.dumps(valid_marketplace))
                if mutation_path is not None:
                    target = payload
                    for key in mutation_path[:-1]:
                        target = target[key]
                    target[mutation_path[-1]] = value

                marketplace_path.write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )
                errors = validate_plugin.validate_marketplace(
                    root,
                    {"name": "expected-plugin"},
                )

                if expected_error is None:
                    self.assertEqual([], errors)
                else:
                    self.assertEqual([expected_error], errors)

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
