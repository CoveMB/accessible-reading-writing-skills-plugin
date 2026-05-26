from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
DOCS_ROOT = ROOT / "docs"

MAIN_SKILLS = (
    "accessibility-prose-repair",
    "accessibility-dictation-notes",
    "accessibility-reading-load-reducer",
    "accessibility-low-load-companion",
)

SHARED_DOC_REFERENCES = (
    (
        "docs/skill_operational_boundaries.md",
        DOCS_ROOT / "SKILL_OPERATIONAL_BOUNDARIES.md",
    ),
    ("docs/source_limits.md", DOCS_ROOT / "SOURCE_LIMITS.md"),
)

SHARED_DOC_PATHS = (
    DOCS_ROOT / "SKILL_OPERATIONAL_BOUNDARIES.md",
    DOCS_ROOT / "SOURCE_LIMITS.md",
    DOCS_ROOT / "AUTO_SELECTION_GUARDRAILS.md",
    DOCS_ROOT / "SKILL_INDEX.md",
)

TermGroup = tuple[str, ...]
EquivalentTermGroups = tuple[TermGroup, ...]
Contract = tuple[str, EquivalentTermGroups]


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def read_normalized(path: Path) -> str:
    return normalized_text(path.read_text(encoding="utf-8"))


def skill_path(skill_name: str) -> Path:
    return SKILLS_ROOT / skill_name / "SKILL.md"


def terms_are_present(text: str, terms: TermGroup) -> bool:
    return all(term in text for term in terms)


def concept_is_present(text: str, equivalent_term_groups: EquivalentTermGroups) -> bool:
    return any(terms_are_present(text, terms) for terms in equivalent_term_groups)


def missing_contract_names(text: str, contracts: tuple[Contract, ...]) -> list[str]:
    return [
        name
        for name, equivalent_term_groups in contracts
        if not concept_is_present(text, equivalent_term_groups)
    ]


def referenced_shared_text(skill_text: str) -> str:
    referenced_paths = [
        path
        for reference, path in SHARED_DOC_REFERENCES
        if reference in skill_text
    ]
    return "\n".join(read_normalized(path) for path in referenced_paths if path.exists())


def full_skill_contract_text(skill_name: str) -> str:
    skill_text = read_normalized(skill_path(skill_name))
    return "\n".join([skill_text, referenced_shared_text(skill_text)])


def shared_document_text() -> str:
    return "\n".join(read_normalized(path) for path in SHARED_DOC_PATHS)


# These tests are instruction guardrails only. They verify that required safety
# contracts remain documented; they do not prove model behavior preserves meaning.
SHARED_SKILL_CONTRACTS: tuple[Contract, ...] = (
    (
        "meaning preservation",
        (
            ("preserve", "meaning"),
            ("meaning-preserving",),
            ("without changing", "meaning"),
        ),
    ),
    (
        "ambiguity marked instead of guessed",
        (
            ("ambiguity", "instead of guessing"),
            ("mark ambiguity", "guessing"),
            ("ambiguous", "rather than silently"),
        ),
    ),
    (
        "no invented facts or unsupported claims",
        (
            ("do not add facts",),
            ("do not invent", "facts"),
            ("do not invent", "claims"),
            ("unsupported", "claims"),
        ),
    ),
    (
        "uncertainty remains visible",
        (
            ("uncertainty", "visible"),
            ("what remains uncertain",),
            ("do not hide uncertainty",),
        ),
    ),
    (
        "source and verification limits remain visible",
        (
            ("source basis and limits",),
            ("source access level",),
            ("verification", "limits"),
            ("docs/source_limits.md",),
        ),
    ),
    (
        "original material is not overwritten without explicit request",
        (
            ("must not overwrite", "explicit"),
            ("overwrite", "without explicit user request"),
            ("overwrite", "unless the user explicitly asks"),
        ),
    ),
)

SHARED_REFERENCE_CONTRACTS: tuple[Contract, ...] = tuple(
    (
        f"references {reference}",
        ((reference,),),
    )
    for reference, _ in SHARED_DOC_REFERENCES
)

SHARED_DOCUMENT_CONTRACTS: tuple[Contract, ...] = (
    (
        "source access levels are classified",
        (
            (
                "source access level",
                "user-provided full text",
                "excerpt only",
                "citation or metadata only",
                "model knowledge only",
                "live or current search needed",
            ),
        ),
    ),
    (
        "invented evidence is forbidden",
        (
            ("do not invent", "citations", "page numbers", "claims of having searched"),
            ("fabricated", "citations", "quotes", "page numbers"),
        ),
    ),
    (
        "facts and interpretation stay separate",
        (
            ("separate visible facts", "interpretation", "uncertainty", "recommendation"),
        ),
    ),
    (
        "unavailable source access stays unverified",
        (
            ("full text", "needed", "mark the result unverified"),
            ("missing source access", "marked clearly"),
        ),
    ),
    (
        "private material needs consent before external lookup",
        (
            ("private", "external tools", "without user consent"),
            ("confidential", "external tools", "consent"),
        ),
    ),
    (
        "shared no-overwrite rule is explicit",
        (
            ("must not overwrite source material", "without explicit user request"),
            ("must not overwrite", "original notes", "without explicit user request"),
        ),
    ),
)

SKILL_SPECIFIC_CONTRACTS: dict[str, tuple[Contract, ...]] = {
    "accessibility-prose-repair": (
        (
            "smoother prose must not change meaning",
            (("do not change", "meaning", "smoother"),),
        ),
        (
            "uncertainty and stable literals are preserved",
            (
                (
                    "preserve",
                    "uncertainty",
                    "qualifiers",
                    "commitments",
                    "names",
                    "terms",
                    "numbers",
                    "dates",
                ),
            ),
        ),
        (
            "uncertain names and literals are not silently fixed",
            (
                (
                    "do not silently",
                    "fix",
                    "uncertain",
                    "names",
                    "terms",
                    "citations",
                    "quotes",
                    "numbers",
                    "dates",
                ),
            ),
        ),
        (
            "facts, citations, promises, and obligations are not added",
            (("do not add", "facts", "citations", "promises", "obligations"),),
        ),
    ),
    "accessibility-dictation-notes": (
        (
            "unclear speech is not made overconfident",
            (("unclear speech", "confident factual claims"),),
        ),
        (
            "speaker and source labels are preserved when useful",
            (("preserve speaker/source labels",), ("speaker or source", "when present")),
        ),
        (
            "transcript ambiguity is marked instead of guessed",
            (("transcript", "ambiguity", "instead of guessing"),),
        ),
        (
            "emphatic repetition is not erased",
            (("do not erase repetitions", "emphasis"),),
        ),
    ),
    "accessibility-low-load-companion": (
        (
            "smallest useful next step is preferred",
            (("smallest useful", "accessibility step"), ("one small next action",)),
        ),
        (
            "routing stays narrow",
            (("do not route", "many skills", "one small next action"),),
        ),
        (
            "raw meaning, cleanup, interpretation, uncertainty, and action are separate",
            (
                (
                    "raw meaning",
                    "cleaned wording",
                    "interpretation",
                    "uncertainty",
                    "next action",
                ),
            ),
        ),
        (
            "privacy and evidence concerns stay visible",
            (("do not hide", "evidence", "privacy concerns"),),
        ),
    ),
    "accessibility-reading-load-reducer": (
        (
            "thin access is not treated as source support",
            (("do not infer source support", "title", "snippet", "abstract"),),
        ),
        (
            "access level is classified",
            (
                (
                    "classify access",
                    "access level",
                    "full text",
                    "excerpt only",
                    "metadata only",
                    "citation only",
                    "unclear",
                ),
            ),
        ),
        (
            "thin or unclear access defaults to park unless clearly off-scope",
            (
                (
                    "title-only",
                    "citation-only",
                    "snippet-only",
                    "unclear-access",
                    "park",
                    "off-scope",
                ),
            ),
        ),
        (
            "triage is not verified synthesis",
            (("do not turn", "triage", "verified synthesis"),),
        ),
    ),
}


class SkillInstructionContractTests(unittest.TestCase):
    def assertContractsPresent(
        self,
        text: str,
        contracts: tuple[Contract, ...],
        context: str,
    ) -> None:
        self.assertEqual([], missing_contract_names(text, contracts), context)

    def test_main_skill_files_exist(self) -> None:
        for skill_name in MAIN_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertTrue(skill_path(skill_name).exists())

    def test_each_skill_references_shared_contract_docs(self) -> None:
        for skill_name in MAIN_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertContractsPresent(
                    read_normalized(skill_path(skill_name)),
                    SHARED_REFERENCE_CONTRACTS,
                    f"{skill_name} should reference shared safety docs",
                )

    def test_each_skill_includes_or_references_shared_safety_contracts(self) -> None:
        for skill_name in MAIN_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertContractsPresent(
                    full_skill_contract_text(skill_name),
                    SHARED_SKILL_CONTRACTS,
                    f"{skill_name} is missing shared safety contract language",
                )

    def test_each_skill_keeps_skill_specific_safety_contracts(self) -> None:
        for skill_name, contracts in SKILL_SPECIFIC_CONTRACTS.items():
            with self.subTest(skill=skill_name):
                self.assertContractsPresent(
                    read_normalized(skill_path(skill_name)),
                    contracts,
                    f"{skill_name} is missing skill-specific safety contract language",
                )


class SharedDocumentContractTests(unittest.TestCase):
    def test_shared_docs_keep_source_privacy_and_uncertainty_limits(self) -> None:
        self.assertEqual(
            [],
            missing_contract_names(shared_document_text(), SHARED_DOCUMENT_CONTRACTS),
        )


if __name__ == "__main__":
    unittest.main()
