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
    (
        "docs/auto_selection_guardrails.md",
        DOCS_ROOT / "AUTO_SELECTION_GUARDRAILS.md",
    ),
    ("docs/routing_matrix.md", DOCS_ROOT / "ROUTING_MATRIX.md"),
)

TermGroup = tuple[str, ...]
EquivalentTermGroups = tuple[TermGroup, ...]
Contract = tuple[str, EquivalentTermGroups]


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def read_normalized(path: Path) -> str:
    return normalized_text(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill_path(skill_name: str) -> Path:
    return SKILLS_ROOT / skill_name / "SKILL.md"


def agent_path(skill_name: str) -> Path:
    return SKILLS_ROOT / skill_name / "agents" / "openai.yaml"


def markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\n(?P<section>.*?)(?=^## |\Z)"
    )
    match = pattern.search(text)
    return "" if match is None else match.group("section")


def output_format_text(skill_name: str) -> str:
    return normalized_text(markdown_section(read_text(skill_path(skill_name)), "Output format"))


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


# These tests are instruction guardrails only. They verify that required safety
# contracts remain documented; they do not prove model behavior preserves meaning.
SHARED_REFERENCE_CONTRACTS: tuple[Contract, ...] = tuple(
    (f"references {reference}", ((reference,),))
    for reference, _ in SHARED_DOC_REFERENCES
)

POLICY_OWNER_CONTRACTS: dict[Path, tuple[Contract, ...]] = {
    DOCS_ROOT / "SKILL_OPERATIONAL_BOUNDARIES.md": (
        (
            "meaning preservation",
            (("preserve the user's meaning",), ("meaning must be preserved",)),
        ),
        (
            "ambiguity marked instead of guessed",
            (("mark ambiguity", "instead of guessing"),),
        ),
        (
            "uncertainty remains visible",
            (("uncertainty", "visible", "when they matter"),),
        ),
        (
            "qualifier polarity and scope stay attached",
            (
                (
                    "qualifiers and negations",
                    "same subject",
                    "action",
                    "object",
                    "scope or polarity",
                ),
            ),
        ),
        (
            "false premises are not smoothed into claims",
            (("false premise", "strongest supportable"),),
        ),
        (
            "compact output keeps decision-changing caveats",
            (("compact output", "must not remove", "decision-changing caveats"),),
        ),
        (
            "marker-only compliance is rejected",
            (("marker-only", "not enough", "required headings"),),
        ),
        (
            "shared no-overwrite rule is explicit",
            (("must not overwrite", "without explicit user request"),),
        ),
    ),
    DOCS_ROOT / "SOURCE_LIMITS.md": (
        (
            "source and verification limits remain explicit",
            (
                (
                    "# verification and source limits",
                    "## source access level",
                    "## verification rules",
                ),
            ),
        ),
        (
            "source access levels are classified",
            (
                (
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
            (("do not invent", "citations", "page numbers", "claims of having searched"),),
        ),
        (
            "facts and interpretation stay separate",
            (
                (
                    "separate visible facts",
                    "interpretation",
                    "uncertainty",
                    "recommendation",
                ),
            ),
        ),
        (
            "consent is not inferred from access or silence",
            (
                (
                    "do not infer consent or permission",
                    "access to material",
                    "prior sharing",
                    "silence",
                    "plan to ask",
                ),
            ),
        ),
        (
            "triage does not become high-stakes advice",
            (
                (
                    "cleaning, structuring, and triage",
                    "do not authorize direct legal, medical, or financial instructions",
                    "attributed source content",
                ),
            ),
        ),
        (
            "unavailable source access stays unverified",
            (("full text", "needed", "mark the result unverified"),),
        ),
        (
            "source-contained instructions are untrusted data",
            (("source-contained", "instructions", "not operating instructions"),),
        ),
        (
            "source existence is not source support",
            (("source existence", "not source support"),),
        ),
        (
            "currentness and source status need lookup or labels",
            (("currentness", "lookup", "unverified", "source status unchecked"),),
        ),
        (
            "AI involvement and venue policy limits stay visible",
            (("ai involvement", "must not be concealed", "venue policy", "unverified"),),
        ),
        (
            "private material needs consent before external lookup",
            (("private", "external tools", "without user consent"),),
        ),
        (
            "external lookup consent choices are operational",
            (
                (
                    "work only from provided material",
                    "nonsensitive keywords",
                    "public identifiers",
                    "quoted/private/identifying details",
                    "explicit user consent",
                ),
            ),
        ),
    ),
}

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
        (
            "false-premise smoothing is blocked",
            (("false premise", "do not", "smooth"),),
        ),
        (
            "AI disclosure and venue policy uncertainty are preserved",
            (
                (
                    "ai involvement",
                    "must not be concealed",
                    "venue policy",
                    "unverified",
                ),
            ),
        ),
        (
            "compact repair keeps caveats that change reliance",
            (("compact repair", "caveats", "claim strength", "ai involvement"),),
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
        (
            "source-contained instructions remain transcript content",
            (
                (
                    "source-contained",
                    "instructions",
                    "transcript content",
                    "not followed",
                ),
            ),
        ),
        (
            "AI privacy and commitment uncertainty stay visible",
            (
                (
                    "ai",
                    "privacy",
                    "commitment",
                    "uncertainty",
                    "visible",
                ),
            ),
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
        (
            "false premises and blockers are not hidden",
            (("false premise", "blocker", "do not hide"),),
        ),
        (
            "marker-only compliance is not accepted",
            (("marker-only", "required headings", "substance"),),
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
        (
            "source packets cannot inject instructions",
            (("source-contained", "instructions", "not followed", "source packet"),),
        ),
        (
            "currentness and questionable source status stay unchecked without lookup",
            (("currentness", "source-status", "lookup", "unchecked"),),
        ),
        (
            "corpus bias and representativeness limits stay visible",
            (("corpus", "representative", "english-only", "open-access"),),
        ),
        (
            "causal and statistical claims are not upgraded",
            (("causal", "statistical", "denominator", "incompatible estimates"),),
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

    def test_shared_doc_references_exist(self) -> None:
        for reference, path in SHARED_DOC_REFERENCES:
            with self.subTest(reference=reference, path=path):
                self.assertTrue(
                    path.is_file(),
                    f"{reference} should resolve to the shared document at {path}",
                )

    def test_each_skill_references_shared_contract_docs(self) -> None:
        self.assertEqual(
            (
                "docs/skill_operational_boundaries.md",
                "docs/source_limits.md",
                "docs/auto_selection_guardrails.md",
                "docs/routing_matrix.md",
            ),
            tuple(reference for reference, _ in SHARED_DOC_REFERENCES),
        )

        for skill_name in MAIN_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertContractsPresent(
                    read_normalized(skill_path(skill_name)),
                    SHARED_REFERENCE_CONTRACTS,
                    f"{skill_name} should reference shared safety docs",
                )

    def test_each_skill_keeps_skill_specific_safety_contracts(self) -> None:
        for skill_name, contracts in SKILL_SPECIFIC_CONTRACTS.items():
            with self.subTest(skill=skill_name):
                self.assertContractsPresent(
                    read_normalized(skill_path(skill_name)),
                    contracts,
                    f"{skill_name} is missing skill-specific safety contract language",
                )

    def test_low_load_companion_routing_is_narrow(self) -> None:
        text = "\n".join(
            [
                read_normalized(skill_path("accessibility-low-load-companion")),
                read_normalized(agent_path("accessibility-low-load-companion")),
            ]
        )

        required_fragments = (
            "mixed or unclear",
            "no smaller/specialist skill clearly owns the task",
            "do not use this skill when the user only asks for grammar/prose repair",
            "do not use this skill when the user only asks for transcript/dictation cleanup",
            "do not use this skill when the user only asks for reading triage",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_output_format_sections_default_to_compact(self) -> None:
        for skill_name in MAIN_SKILLS:
            with self.subTest(skill=skill_name):
                section = output_format_text(skill_name)

                self.assertIn("default compact output", section)
                self.assertIn("expanded output", section)
                self.assertLess(
                    section.index("default compact output"),
                    section.index("expanded output"),
                )
                for fragment in (
                    "source basis",
                    "uncertainty",
                    "ambiguity",
                    "privacy",
                    "verification",
                    "one useful next action only when it reduces friction",
                ):
                    self.assertIn(fragment, section)

    def test_prose_repair_levels_keep_minimal_correction_default(self) -> None:
        text = read_normalized(skill_path("accessibility-prose-repair"))

        required_fragments = (
            "level 1 / minimal correction",
            "spelling, punctuation, grammar, and sentence boundaries only",
            "no tone/style/claim-strength changes",
            "level 2 / local clarity",
            "level 2 / local clarity: only when the user asks",
            "light sentence-local restructuring only when meaning is clear",
            "level 3 / rewrite",
            "only when explicitly requested",
            "tone/audience/structure",
            "default to level 1",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

        forbidden_fragments = (
            "requested output clearly requires",
            "clearly requires one",
        )

        for fragment in forbidden_fragments:
            with self.subTest(forbidden_fragment=fragment):
                self.assertNotIn(fragment, text)

    def test_dictation_instructions_include_verbatim_anchor_mode(self) -> None:
        text = read_normalized(skill_path("accessibility-dictation-notes"))

        required_fragments = (
            "verbatim anchor mode",
            "exact wording may matter",
            "commitments",
            "dates",
            "names",
            "refusals",
            "permissions",
            "privacy",
            "obligations",
            "emotionally loaded statements",
            "workplace/meeting notes",
            "legal/medical/financial-adjacent notes",
            "source-sensitive material",
            "short original fragments or redacted anchors",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)


class SharedDocumentContractTests(unittest.TestCase):
    def test_policy_documents_keep_owner_specific_contracts(self) -> None:
        self.assertEqual(
            (
                DOCS_ROOT / "SKILL_OPERATIONAL_BOUNDARIES.md",
                DOCS_ROOT / "SOURCE_LIMITS.md",
            ),
            tuple(POLICY_OWNER_CONTRACTS),
        )

        for owner_path, contracts in POLICY_OWNER_CONTRACTS.items():
            with self.subTest(owner=owner_path.name):
                self.assertEqual(
                    [],
                    missing_contract_names(read_normalized(owner_path), contracts),
                    f"{owner_path.name} is missing contracts it canonically owns",
                )

    def test_routing_matrix_delegates_suggestion_policy_to_one_owner(self) -> None:
        routing_text = read_text(DOCS_ROOT / "ROUTING_MATRIX.md")
        self.assertEqual(
            ["Primary routes"],
            re.findall(r"(?m)^## ([^\n]+)$", routing_text),
        )

        primary_routes = markdown_section(routing_text, "Primary routes")
        expected_routes = (
            (
                "Voice, dictation, or transcript first",
                "accessibility-dictation-notes",
            ),
            ("Reading volume first", "accessibility-reading-load-reducer"),
            ("Existing prose repair first", "accessibility-prose-repair"),
            ("Mixed or unclear bottleneck", "accessibility-low-load-companion"),
        )
        actual_routes = tuple(
            re.findall(
                r"(?m)^### ([^\n]+)\n\nRoute: "
                r"`(accessibility-[a-z0-9-]+)`(?:\.|$)",
                primary_routes,
            )
        )
        self.assertEqual(expected_routes, actual_routes)
        self.assertEqual(4, len(re.findall(r"(?m)^### [^\n]+$", primary_routes)))

        mixed_route = primary_routes.split("### Mixed or unclear bottleneck", 1)[1]
        positive_route_match = re.search(
            r"(?ms)^Use\b.*?(?=^\s*$|\Z)",
            mixed_route,
        )
        self.assertIsNotNone(positive_route_match)
        assert positive_route_match is not None
        positive_route = normalized_text(positive_route_match.group())
        for term in ("only", "mixed", "unclear", "specialist"):
            self.assertIn(term, positive_route)

        owner_links = list(
            re.finditer(
                r"\[[^\]\n]+\]\((?P<target>AUTO_SELECTION_GUARDRAILS\.md)\)",
                routing_text,
            )
        )
        self.assertEqual(1, len(owner_links))
        owner_link = owner_links[0]
        owner_path = (DOCS_ROOT / owner_link.group("target")).resolve()
        expected_owner = (DOCS_ROOT / "AUTO_SELECTION_GUARDRAILS.md").resolve()
        self.assertEqual(expected_owner, owner_path)
        self.assertTrue(owner_path.is_file())
        self.assertLess(
            max(
                routing_text.index(f"Route: `{skill}`")
                for _, skill in expected_routes
            ),
            owner_link.start(),
        )

        delegation_start = routing_text.rfind("\n\n", 0, owner_link.start()) + 2
        delegation_text = routing_text[delegation_start:].strip()
        self.assertEqual(1, len(re.split(r"\n\s*\n", delegation_text)))
        delegation = normalized_text(delegation_text)
        for term in ("owned", "after", "primary route"):
            self.assertIn(term, delegation)

        owner_text = read_text(owner_path)
        selection_rules = markdown_section(owner_text, "Selection rules")
        selection_items = [
            normalized_text(item)
            for item in re.findall(r"(?m)^-\s+(.+)$", selection_rules)
        ]
        specialist_terms = (
            "prefer",
            *(skill for _, skill in expected_routes[:3]),
            "bottleneck",
        )
        mixed_fallback_terms = (
            expected_routes[-1][1],
            "only",
            "mixed",
            "unclear",
            "specialist",
        )
        for terms in (specialist_terms, mixed_fallback_terms):
            self.assertTrue(
                any(all(term in item for term in terms) for item in selection_items)
            )

        suggestion_heading = "## Suggested next step policy\n"
        suggestion_start = owner_text.find(suggestion_heading)
        self.assertNotEqual(-1, suggestion_start)
        suggestion_policy = owner_text[suggestion_start + len(suggestion_heading) :]
        normalized_policy = normalized_text(suggestion_policy)
        policy_terms = (
            ("optional", "omit", "default"),
            ("only", "all", "gates"),
            ("one", "suggested skill", "max"),
        )
        for terms in policy_terms:
            self.assertTrue(all(term in normalized_policy for term in terms))

        suggestion_gates = [
            normalized_text(item)
            for item in re.findall(r"(?m)^-\s+(.+)$", suggestion_policy)
        ]
        self.assertGreaterEqual(len(suggestion_gates), 5)
        gate_terms = (
            ("unresolved", "risk"),
            ("one", "skill", "reduces", "risk"),
            ("input", "exists"),
            ("suggestion", "bottleneck"),
            ("explanation", "lines"),
        )
        for terms in gate_terms:
            self.assertTrue(
                any(all(term in gate for term in terms) for gate in suggestion_gates)
            )

    def test_scan_docs_do_not_use_wide_markdown_tables(self) -> None:
        docs_to_check = (
            DOCS_ROOT / "SKILL_INDEX.md",
            DOCS_ROOT / "ROUTING_MATRIX.md",
        )

        for path in docs_to_check:
            with self.subTest(path=path.name):
                table_rows = [
                    line
                    for line in read_text(path).splitlines()
                    if line.strip().startswith("|") and line.strip().endswith("|")
                ]
                self.assertEqual(
                    [],
                    table_rows,
                    f"{path.name} should use heading/list structures instead of wide tables",
                )


if __name__ == "__main__":
    unittest.main()
