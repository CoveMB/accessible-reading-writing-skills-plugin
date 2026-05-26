from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_PATH_PARTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }
)
GENERATED_SUFFIXES = frozenset({".pyc", ".pyo", ".pyd"})
GENERATED_FILE_NAMES = frozenset({".DS_Store"})
REQUIRED_GITIGNORE_PATTERNS = frozenset(
    {
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".DS_Store",
    }
)


def committable_repository_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        text=False,
    )
    path_names = result.stdout.decode("utf-8").split("\0")
    return sorted(
        Path(path_name)
        for path_name in path_names
        if path_name and (root / path_name).exists()
    )


def is_generated_cache_path(path: Path) -> bool:
    return (
        bool(GENERATED_PATH_PARTS.intersection(path.parts))
        or path.suffix in GENERATED_SUFFIXES
        or path.name in GENERATED_FILE_NAMES
    )


def format_generated_paths(paths: list[Path]) -> str:
    return "\n".join(f"- {path.as_posix()}" for path in paths)


def gitignore_patterns(root: Path) -> frozenset[str]:
    gitignore_path = root / ".gitignore"
    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip())


class RepositoryHygieneTests(unittest.TestCase):
    def test_common_generated_artifacts_are_ignored(self) -> None:
        missing_patterns = sorted(
            REQUIRED_GITIGNORE_PATTERNS.difference(gitignore_patterns(ROOT))
        )

        if missing_patterns:
            self.fail(
                "Missing generated/cache ignore patterns:\n"
                + "\n".join(f"- {pattern}" for pattern in missing_patterns)
            )

    def test_generated_cache_artifacts_are_not_committable(self) -> None:
        generated_paths = [
            path
            for path in committable_repository_paths(ROOT)
            if is_generated_cache_path(path)
        ]

        if generated_paths:
            self.fail(
                "Generated/cache artifacts must not be tracked or left unignored:\n"
                f"{format_generated_paths(generated_paths)}"
            )


if __name__ == "__main__":
    unittest.main()
