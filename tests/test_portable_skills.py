from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plugin_utils
import validate_plugin


class PortableSkillTests(unittest.TestCase):
    def export(self, root: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(root / "scripts/export_skills.py"),
             "--root", str(root), "--out", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_exported_skills_remain_complete_when_moved_individually(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            output = base / "export"
            result = self.export(ROOT, output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            skills = sorted((ROOT / "skills").iterdir())
            self.assertEqual(sorted(path.name for path in output.iterdir()),
                             [path.name for path in skills])
            for source in skills:
                with self.subTest(skill=source.name):
                    isolated = base / "isolated" / source.name
                    isolated.parent.mkdir(exist_ok=True)
                    shutil.move(str(output / source.name), isolated)
                    original = plugin_utils.parse_markdown_frontmatter(
                        (source / "SKILL.md").read_text())
                    exported = plugin_utils.parse_markdown_frontmatter(
                        (isolated / "SKILL.md").read_text())
                    self.assertEqual(exported, original)
                    _, _, errors = validate_plugin.validate_skill_dir(
                        isolated, isolated, set(), plugin_utils.plugin_version(ROOT))
                    self.assertEqual(errors, [])
                    for document in isolated.rglob("*.md"):
                        for target in validate_plugin.MARKDOWN_LINK_RE.findall(
                            document.read_text()
                        ):
                            if validate_plugin.is_external_reference(target):
                                continue
                            resolved = (document.parent / target).resolve()
                            self.assertTrue(resolved.is_relative_to(isolated.resolve()))
                            self.assertTrue(resolved.is_file(), (document, target))
                    for document in (isolated / "references").iterdir():
                        self.assertEqual(document.read_bytes(),
                                         (ROOT / "docs" / document.name).read_bytes())
                    self.assertEqual((isolated / "LICENSE").read_bytes(),
                                     (ROOT / "LICENSE").read_bytes())

    def test_existing_destinations_are_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            original = base / "original"
            original.write_text("keep me")
            directory = base / "directory"
            directory.mkdir()
            link = base / "link"
            link.symlink_to(original)
            broken = base / "broken"
            broken.symlink_to(base / "missing")
            for output in (original, directory, link, broken):
                with self.subTest(output=output.name):
                    result = self.export(ROOT, output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("already exists", result.stderr)
            self.assertEqual(original.read_text(), "keep me")
            self.assertEqual(list(directory.iterdir()), [])
            self.assertTrue(link.is_symlink())
            self.assertTrue(broken.is_symlink())

    def test_missing_dependency_does_not_publish_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            plugin_utils.copy_package_tree(ROOT, source)
            (source / "docs/SOURCE_LIMITS.md").unlink()
            output = base / "export"
            result = self.export(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_shared_lookup_table_matches_policy_metadata(self) -> None:
        document = (ROOT / "docs/SKILL_OPERATIONAL_BOUNDARIES.md").read_text()
        rows = dict(re.findall(r"\| `(accessibility-[a-z-]+)` \| `(conditional|route-only|none)` \|", document))
        skills = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(set(rows), skills)
        for name, policy in rows.items():
            with self.subTest(skill=name):
                self.assertEqual(policy, plugin_utils.agent_lookup_policy(name))

    def test_export_excludes_unrelated_and_symlinked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            plugin_utils.copy_package_tree(ROOT, source)
            skill = next((source / "skills").iterdir())
            (skill / "private-notes.txt").write_text("private sentinel")
            (skill / "private-link").symlink_to(skill / "private-notes.txt")
            output = base / "export"
            result = self.export(source, output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            expected = {"SKILL.md", "README.md", "LICENSE", "agents/openai.yaml"}
            expected.update(f"references/{name}" for name in (
                "SKILL_OPERATIONAL_BOUNDARIES.md", "SOURCE_LIMITS.md",
                "AUTO_SELECTION_GUARDRAILS.md", "ROUTING_MATRIX.md"))
            for exported in output.iterdir():
                self.assertEqual(
                    {str(path.relative_to(exported)) for path in exported.rglob("*")
                     if path.is_file()}, expected)
                self.assertFalse(any(path.is_symlink() for path in exported.rglob("*")))

    def test_required_symlinked_resource_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            plugin_utils.copy_package_tree(ROOT, source)
            limits = source / "docs/SOURCE_LIMITS.md"
            outside = base / "limits.md"
            limits.rename(outside)
            limits.symlink_to(outside)
            output = base / "export"
            result = self.export(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_unbundled_link_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            plugin_utils.copy_package_tree(ROOT, source)
            skill = next((source / "skills").iterdir())
            (skill / "extra.md").write_text("Source-only dependency")
            with (skill / "SKILL.md").open("a") as instructions:
                instructions.write("\nRead [extra instructions](extra.md).\n")
            output = base / "export"
            result = self.export(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("extra.md", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
