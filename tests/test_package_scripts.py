from __future__ import annotations

import json
import io
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
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
    def marketplace_list_result(self, root: Path) -> mock.Mock:
        return mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "marketplaces": [
                        {
                            "name": install_codex_plugin.MARKETPLACE_NAME,
                            "root": str(root),
                        }
                    ]
                }
            ),
            stderr="",
        )

    def test_dry_run_does_not_invoke_codex(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.object(install_codex_plugin, "run_validation"),
            mock.patch.object(install_codex_plugin.shutil, "which", return_value="/usr/bin/codex"),
            mock.patch.object(install_codex_plugin.subprocess, "run") as run,
            redirect_stdout(output),
        ):
            status = install_codex_plugin.main(
                ["--plugin-root", str(ROOT), "--dry-run"]
            )

        self.assertEqual(0, status)
        run.assert_not_called()
        self.assertIn(f"codex plugin marketplace add {ROOT}", output.getvalue())
        self.assertIn(
            "codex plugin add "
            "accessible-reading-writing-plugin@accessible-reading-writing-local",
            output.getvalue(),
        )
        self.assertIn("Install the plugin through Codex:", output.getvalue())
        self.assertNotIn("Install or update", output.getvalue())

    def test_missing_marketplace_is_registered_through_codex(self) -> None:
        list_result = mock.Mock(returncode=0, stdout='{"marketplaces": []}', stderr="")
        add_result = mock.Mock(returncode=0, stdout="{}", stderr="")
        with (
            mock.patch.object(install_codex_plugin, "run_validation"),
            mock.patch.object(install_codex_plugin.shutil, "which", return_value="/usr/bin/codex"),
            mock.patch.object(
                install_codex_plugin.subprocess,
                "run",
                side_effect=[list_result, add_result],
            ) as run,
            redirect_stdout(io.StringIO()),
        ):
            status = install_codex_plugin.main(["--plugin-root", str(ROOT)])

        self.assertEqual(0, status)
        self.assertEqual(
            [
                ["codex", "plugin", "marketplace", "list", "--json"],
                ["codex", "plugin", "marketplace", "add", str(ROOT), "--json"],
            ],
            [call.args[0] for call in run.call_args_list],
        )

    def test_marketplace_command_failure_preserves_exit_status(self) -> None:
        list_result = mock.Mock(returncode=23, stdout="", stderr="injected failure")
        with (
            mock.patch.object(install_codex_plugin, "run_validation"),
            mock.patch.object(install_codex_plugin.shutil, "which", return_value="/usr/bin/codex"),
            mock.patch.object(
                install_codex_plugin.subprocess,
                "run",
                return_value=list_result,
            ),
            redirect_stderr(io.StringIO()),
        ):
            status = install_codex_plugin.main(["--plugin-root", str(ROOT)])

        self.assertEqual(23, status)

    def test_existing_marketplace_at_same_root_is_reused(self) -> None:
        with (
            mock.patch.object(install_codex_plugin, "run_validation"),
            mock.patch.object(install_codex_plugin.shutil, "which", return_value="/usr/bin/codex"),
            mock.patch.object(
                install_codex_plugin.subprocess,
                "run",
                return_value=self.marketplace_list_result(ROOT),
            ) as run,
            redirect_stdout(io.StringIO()),
        ):
            status = install_codex_plugin.main(["--plugin-root", str(ROOT)])

        self.assertEqual(0, status)
        self.assertEqual(1, run.call_count)

    def test_same_marketplace_name_at_different_root_is_rejected(self) -> None:
        other_root = ROOT.parent / "other-plugin"
        with (
            mock.patch.object(install_codex_plugin, "run_validation"),
            mock.patch.object(install_codex_plugin.shutil, "which", return_value="/usr/bin/codex"),
            mock.patch.object(
                install_codex_plugin.subprocess,
                "run",
                return_value=self.marketplace_list_result(other_root),
            ) as run,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            status = install_codex_plugin.main(["--plugin-root", str(ROOT)])

        self.assertEqual(1, status)
        self.assertEqual(1, run.call_count)

    def test_link_is_a_deprecated_registration_alias(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.object(install_codex_plugin, "run_validation"),
            mock.patch.object(install_codex_plugin.shutil, "which", return_value="/usr/bin/codex"),
            mock.patch.object(install_codex_plugin.subprocess, "run") as run,
            redirect_stdout(output),
        ):
            status = install_codex_plugin.main(
                ["--plugin-root", str(ROOT), "--link", "--dry-run"]
            )

        self.assertEqual(0, status)
        run.assert_not_called()
        self.assertIn("deprecated", output.getvalue().lower())
        self.assertIn("no symlink", output.getvalue().lower())

    def test_installer_does_not_manage_plugin_files_or_cache(self) -> None:
        installer_text = (SCRIPTS / "install_codex_plugin.py").read_text(encoding="utf-8")

        for forbidden_text in [
            ".codex\" / \"plugins",
            "copy_plugin",
            "link_plugin",
            "link_plugin_cache",
            "symlink_to",
        ]:
            self.assertNotIn(forbidden_text, installer_text)


class MarketplaceContractTests(unittest.TestCase):
    def test_release_versions_match(self) -> None:
        manifest = plugin_utils.load_plugin_manifest(ROOT)
        version = manifest["version"]

        self.assertEqual("1.1.0", version)
        readme_lines = {
            line.strip()
            for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        }
        changelog_lines = {
            line.strip()
            for line in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        }
        self.assertIn(f"Version: {version}", readme_lines)
        self.assertIn(f"## {version}", changelog_lines)
        for skill_path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            frontmatter = plugin_utils.parse_markdown_frontmatter(
                skill_path.read_text(encoding="utf-8")
            )
            self.assertEqual(version, frontmatter["metadata"]["version"])

    def test_repository_marketplace_matches_manifest(self) -> None:
        manifest = plugin_utils.load_plugin_manifest(ROOT)
        marketplace = plugin_utils.load_json_object(
            ROOT / ".agents" / "plugins" / "marketplace.json"
        )

        self.assertEqual("accessible-reading-writing-local", marketplace["name"])
        self.assertEqual(1, len(marketplace["plugins"]))
        entry = marketplace["plugins"][0]
        self.assertEqual(manifest["name"], entry["name"])
        self.assertEqual({"source": "local", "path": "./"}, entry["source"])
        self.assertEqual(
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            entry["policy"],
        )
        self.assertEqual("Productivity", entry["category"])

    def test_marketplace_sample_matches_canonical_entry(self) -> None:
        canonical = plugin_utils.load_json_object(
            ROOT / ".agents" / "plugins" / "marketplace.json"
        )
        sample = plugin_utils.load_json_object(ROOT / "marketplace.sample.json")

        self.assertEqual(canonical["name"], sample["name"])
        self.assertEqual(canonical["plugins"], sample["plugins"])

    def test_public_instructions_do_not_directly_mutate_codex_cache(self) -> None:
        command_pattern = re.compile(
            r"^\s*(?:cp|del|ln|mkdir|mv|rm|rmdir|Remove-Item)\b.*"
            r"\.codex[/\\]plugins[/\\]cache",
            re.IGNORECASE,
        )
        for documentation_path in [
            ROOT / "README.md",
            ROOT / "docs" / "MARKETPLACE_INSTALLATION_AND_UPDATE_PLAN.md",
        ]:
            for line in documentation_path.read_text(encoding="utf-8").splitlines():
                self.assertIsNone(command_pattern.search(line), f"{documentation_path}: {line}")

    def test_readme_documents_the_marketplace_identity_change_from_1_0(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        migration_section = readme.partition("## Upgrade from 1.0.0")[2].partition(
            "## Update"
        )[0]

        self.assertTrue(migration_section)
        self.assertIn("local-personal-plugins", migration_section)
        self.assertIn("marketplaceName", migration_section)
        self.assertIn(
            "codex plugin add "
            "accessible-reading-writing-plugin@accessible-reading-writing-local",
            migration_section,
        )
        self.assertIn(
            "codex plugin remove "
            "accessible-reading-writing-plugin@local-personal-plugins",
            migration_section,
        )
        self.assertLess(
            migration_section.index(
                "codex plugin add "
                "accessible-reading-writing-plugin@accessible-reading-writing-local"
            ),
            migration_section.index(
                "codex plugin remove "
                "accessible-reading-writing-plugin@local-personal-plugins"
            ),
        )

    def test_update_instructions_do_not_expect_an_available_entry_for_installed_plugin(
        self,
    ) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        update_section = readme.partition("## Update")[2].partition("## Roll back")[0]

        self.assertTrue(update_section)
        self.assertNotIn("--available", update_section)
        self.assertNotIn("available entry", update_section.lower())
        self.assertIn("codex plugin marketplace list --json", update_section)
        self.assertIn(".codex-plugin/plugin.json", update_section)

    def test_rollback_uses_the_verified_legacy_installer_path(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        rollback_section = readme.partition("## Roll back to 1.0.0")[2].partition(
            "## Upgrade from earlier local drafts"
        )[0]

        self.assertTrue(rollback_section)
        self.assertIn("34aafd943a285ece7c64fbbe8686f902745b0a3c", rollback_section)
        self.assertIn("git worktree add --detach", rollback_section)
        self.assertIn("./install.sh", rollback_section)
        self.assertIn(
            "codex plugin add "
            "accessible-reading-writing-plugin@local-personal-plugins",
            rollback_section,
        )
        self.assertIn(
            "codex plugin remove "
            "accessible-reading-writing-plugin@accessible-reading-writing-local",
            rollback_section,
        )
        self.assertLess(
            rollback_section.index(
                "codex plugin add "
                "accessible-reading-writing-plugin@local-personal-plugins"
            ),
            rollback_section.index(
                "codex plugin remove "
                "accessible-reading-writing-plugin@accessible-reading-writing-local"
            ),
        )


class ValidatorTests(unittest.TestCase):
    def test_release_contract_requires_exact_version_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text(
                "Version: 1.1.0-alpha\n",
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text(
                "## 1.1.0-alpha\n",
                encoding="utf-8",
            )

            errors = validate_plugin.validate_release_contract(
                root,
                {"version": "1.1.0"},
            )

            self.assertIn("README.md must report Version: 1.1.0", errors)
            self.assertIn("CHANGELOG.md must include a 1.1.0 release heading", errors)

    def test_marketplace_plugin_name_must_match_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
            marketplace_path.parent.mkdir(parents=True)
            marketplace_path.write_text(
                json.dumps(
                    {
                        "name": "accessible-reading-writing-local",
                        "interface": {
                            "displayName": "Accessible Reading and Writing Local"
                        },
                        "plugins": [
                            {
                                "name": "wrong-plugin",
                                "source": {"source": "local", "path": "./"},
                                "policy": {
                                    "installation": "AVAILABLE",
                                    "authentication": "ON_INSTALL",
                                },
                                "category": "Productivity",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "marketplace.sample.json").write_text(
                marketplace_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            errors = validate_plugin.validate_marketplace(
                root,
                {"name": "expected-plugin"},
            )

            self.assertIn(
                "marketplace plugin name must match manifest name 'expected-plugin'",
                errors,
            )

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
