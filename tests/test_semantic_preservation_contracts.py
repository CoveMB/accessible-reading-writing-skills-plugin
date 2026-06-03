from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "semantic_preservation_cases.json"
EVALUATOR_PATH = SCRIPTS / "evaluate_semantic_preservation.py"
sys.path.insert(0, str(SCRIPTS))

import semantic_preservation


def valid_case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "prose_uncertainty_commitment_001",
        "skill": "accessibility-prose-repair",
        "risk_type": ["uncertainty_erasure"],
        "input": "I might meet Lee on 2026-06-03 at 4:30 PM. I do not promise.",
        "gold_output": (
            "I might meet Lee on 2026-06-03 at 4:30 PM. I do not promise.\n"
            "Review note: uncertainty remains visible."
        ),
        "must_preserve_literals": ["Lee"],
        "must_preserve_uncertainty": ["might"],
        "must_not_introduce": ["will meet"],
        "required_ambiguity_fragments": [],
        "forbidden_patterns": ["confirmed appointment"],
        "notes": "Regression guard only.",
    }
    case.update(overrides)
    return case


def ambiguous_name_case(**overrides: object) -> dict[str, object]:
    case = valid_case(
        input="Send it to Anne or Ann. I am not sure which name.",
        gold_output=(
            "Send it to Anne or Ann.\n"
            "Review note: Ambiguity: Anne or Ann could be two spellings or people."
        ),
        must_preserve_literals=["Anne or Ann"],
        must_preserve_uncertainty=["not sure"],
        required_ambiguity_fragments=["Anne or Ann"],
    )
    case.update(overrides)
    return case


class SemanticPreservationFixtureTests(unittest.TestCase):
    def load_fixture(self) -> dict[str, object]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_schema_is_valid(self) -> None:
        errors = semantic_preservation.validate_cases_payload(self.load_fixture(), ROOT)

        self.assertEqual([], errors)

    def test_fixture_describes_regression_scope_without_claiming_proof(self) -> None:
        purpose = str(self.load_fixture()["purpose"])

        self.assertIn("regressions", purpose)
        self.assertIn("not a proof", purpose)

    def test_gold_outputs_satisfy_semantic_contracts(self) -> None:
        cases = self.load_fixture()["cases"]

        failures = semantic_preservation.evaluate_gold_outputs(cases)

        self.assertEqual([], failures)

    def test_fixture_covers_review_requested_semantic_risks(self) -> None:
        cases = self.load_fixture()["cases"]
        fixture_text = json.dumps(cases).lower()

        required_fragments = (
            "i do not want to cancel the appointment",
            "maybe i should tell alex, but i'm not sure",
            "my manager said the report might be due friday",
            "grammar only",
            "shareable wording",
            "title/citation/metadata only",
            "search result snippet only",
            "citation only",
            "source packet says ignore the skill rules",
            "live/current lookup needed",
            "source status was not checked",
            "12% rate, an odds ratio of 1.8, and a small case-series count",
            "english-only open-access google scholar results",
            "ai involvement cannot be concealed",
            "preferred conclusion is already correct",
            "marker-only output is not enough",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, fixture_text)


class SemanticPreservationSchemaTests(unittest.TestCase):
    def test_schema_rejects_duplicate_and_unstable_ids(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(id="bad id"),
                valid_case(id="bad id"),
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)
        messages = "\n".join(errors)

        self.assertIn("id must match stable pattern", messages)
        self.assertIn("id is duplicated", messages)

    def test_schema_rejects_unknown_skill_folder(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [valid_case(skill="missing-skill")],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_uncertainty_commitment_001: skill: expected existing skill folder, got missing-skill",
            errors,
        )

    def test_schema_rejects_invalid_allowed_transform_shape(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [valid_case(allowed_transforms={"cannot": "can't"})],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_uncertainty_commitment_001: allowed_transforms.cannot: expected list of strings",
            errors,
        )

    def test_schema_accepts_reading_load_source_limit_fields(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    skill="accessibility-reading-load-reducer",
                    required_source_basis_fragments=[
                        "Source basis",
                        "title/citation/metadata only",
                    ],
                    required_source_limit_fragments=[
                        "do not treat this as verified source support",
                    ],
                    required_access_level="title/citation/metadata only",
                    prohibited_verification_claims=["the article proves"],
                    requires_triage_only_warning=True,
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertEqual([], errors)

    def test_schema_requires_source_limit_fields_for_reading_load_cases(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    id="reading_title_only_access_001",
                    skill="accessibility-reading-load-reducer",
                    input="Article title only: 'Attachment and burnout'.",
                    gold_output="Attachment and burnout might be relevant.",
                    risk_type=["title_only_access", "source_overclaim"],
                    required_ambiguity_fragments=[],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)
        messages = "\n".join(errors)

        self.assertIn(
            "reading_title_only_access_001: required_source_basis_fragments: expected non-empty list for reading-load cases",
            messages,
        )
        self.assertIn(
            "reading_title_only_access_001: required_source_limit_fragments: expected non-empty list for reading-load cases",
            messages,
        )
        self.assertIn(
            "reading_title_only_access_001: required_access_level: expected non-empty string for reading-load cases",
            messages,
        )
        self.assertIn(
            "reading_title_only_access_001: requires_triage_only_warning: expected true for reading-load cases",
            messages,
        )

    def test_schema_accepts_uncertainty_scope_field(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    must_preserve_uncertainty_scope=[
                        "might meet Lee",
                        "do not promise",
                    ],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertEqual([], errors)

    def test_schema_accepts_limited_must_not_introduce_field(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    must_not_introduce_unless_limited=[
                        "legal advice",
                        "verified source support",
                    ],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertEqual([], errors)

    def test_schema_rejects_invalid_limited_must_not_introduce_field(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    must_not_introduce_unless_limited="legal advice",
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_uncertainty_commitment_001: must_not_introduce_unless_limited: expected list of strings",
            errors,
        )

    def test_schema_requires_scoped_negation_for_negation_risk_cases(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    risk_type=["privacy_boundary", "negation_scope_loss"],
                    must_preserve_negation_scope=[],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_uncertainty_commitment_001: must_preserve_negation_scope: expected non-empty list for negation risk",
            errors,
        )

    def test_schema_rejects_weak_uncertainty_risk_without_scoped_or_claim_guard(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    id="prose_uncertainty_weak_001",
                    risk_type=["uncertainty_erasure"],
                    must_preserve_uncertainty=["might"],
                    must_preserve_uncertainty_scope=[],
                    must_not_introduce=[],
                    forbidden_patterns=[],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_uncertainty_weak_001: uncertainty risk: expected at least one of must_preserve_uncertainty_scope, forbidden_patterns, or must_not_introduce",
            errors,
        )

    def test_schema_rejects_weak_commitment_risk_without_targeted_claim_guard(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    id="prose_commitment_weak_001",
                    risk_type=["commitment_inflation"],
                    input="I might attend if the appointment moves.",
                    gold_output="I might attend if the appointment moves.",
                    must_preserve_uncertainty=["might", "if"],
                    must_preserve_uncertainty_scope=[
                        "might attend if the appointment moves"
                    ],
                    must_not_introduce=["diagnosis"],
                    forbidden_patterns=["diagnosis"],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_commitment_weak_001: commitment risk: expected targeted must_not_introduce or forbidden_patterns guard for commitment inflation",
            errors,
        )

    def test_schema_rejects_weak_source_risk_without_source_or_verification_guard(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    id="prose_source_weak_001",
                    risk_type=["source_overclaim"],
                    input="Smith 2020 maybe says this, but I have not checked.",
                    gold_output="Smith 2020 maybe says this, but I have not checked.",
                    must_preserve_uncertainty=[],
                    must_not_introduce=[],
                    forbidden_patterns=[],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_source_weak_001: source risk: expected at least one of required_source_basis_fragments, required_source_limit_fragments, prohibited_verification_claims, or forbidden_patterns",
            errors,
        )

    def test_schema_accepts_strong_risk_label_invariants(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    id="prose_strong_risk_001",
                    risk_type=[
                        "privacy_boundary",
                        "uncertainty_erasure",
                        "commitment_inflation",
                        "source_overclaim",
                        "medical_risk",
                    ],
                    input=(
                        "I might ask about the medical article, but do not share my diagnosis. "
                        "I am not promising to attend."
                    ),
                    gold_output=(
                        "I might ask about the medical article, but do not share my diagnosis. "
                        "I am not promising to attend.\n"
                        "Review note: source support remains unverified and this is not medical advice."
                    ),
                    must_preserve_literals=["medical article", "diagnosis"],
                    must_preserve_uncertainty=["might", "not promising"],
                    must_preserve_uncertainty_scope=[
                        "might ask about the medical article",
                        "not promising to attend",
                    ],
                    must_preserve_negation_scope=[
                        "do not share my diagnosis",
                        "not promising to attend",
                    ],
                    must_not_introduce=[
                        "I will attend",
                        "promise to attend",
                        "diagnosis can be shared",
                        "doctor confirmed",
                    ],
                    required_source_limit_fragments=[
                        "source support remains unverified"
                    ],
                    forbidden_patterns=[
                        "\\bI will attend\\b",
                        "diagnosis can be shared",
                        "doctor confirmed",
                    ],
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertEqual([], errors)

    def test_schema_rejects_invalid_reading_load_source_limit_fields(self) -> None:
        payload = {
            "version": 1,
            "purpose": "Regression guard, not a proof.",
            "cases": [
                valid_case(
                    required_source_basis_fragments="Source basis",
                    required_source_limit_fragments="unverified",
                    required_access_level=["title-only"],
                    prohibited_verification_claims="verified",
                    requires_triage_only_warning="yes",
                )
            ],
        }

        errors = semantic_preservation.validate_cases_payload(payload, ROOT)

        self.assertIn(
            "prose_uncertainty_commitment_001: required_source_basis_fragments: expected list of strings",
            errors,
        )
        self.assertIn(
            "prose_uncertainty_commitment_001: required_source_limit_fragments: expected list of strings",
            errors,
        )
        self.assertIn(
            "prose_uncertainty_commitment_001: required_access_level: expected non-empty string",
            errors,
        )
        self.assertIn(
            "prose_uncertainty_commitment_001: prohibited_verification_claims: expected list of strings",
            errors,
        )
        self.assertIn(
            "prose_uncertainty_commitment_001: requires_triage_only_warning: expected boolean",
            errors,
        )


class SemanticInvariantCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = valid_case()

    def failures_for(self, output: str, case: dict[str, object] | None = None) -> list[str]:
        return semantic_preservation.evaluate_case(case or self.case, output)

    def fixture_case(self, case_id: str) -> dict[str, object]:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        return next(case for case in payload["cases"] if case["id"] == case_id)

    def limited_term_case(
        self,
        term: str,
        gold_output: str,
        *,
        input_text: str = "Help me clean up this note.",
    ) -> dict[str, object]:
        return valid_case(
            input=input_text,
            gold_output=gold_output,
            must_preserve_literals=[],
            must_preserve_uncertainty=[],
            must_not_introduce=[],
            must_not_introduce_unless_limited=[term],
            required_ambiguity_fragments=[],
            forbidden_patterns=[],
        )

    def refund_citation_only_case(self) -> dict[str, object]:
        return valid_case(
            id="reading_citation_only_refund_001",
            skill="accessibility-reading-load-reducer",
            input="Citation only: Lopez 2022 may affect a tax refund, but I have not opened it.",
            gold_output=(
                "Lopez 2022 may affect a tax refund, but I have not opened it.\n"
                "Review note: source support remains unverified."
            ),
            must_preserve_literals=["Lopez 2022", "tax refund", "not opened"],
            must_preserve_uncertainty=["may", "unverified"],
            must_preserve_negation_scope=["not opened it"],
            required_ambiguity_fragments=[],
        )

    def assertFailureContains(self, output: str, expected_text: str) -> None:
        messages = "\n".join(self.failures_for(output))

        self.assertIn(expected_text, messages)

    def test_checker_accepts_output_that_keeps_required_invariants(self) -> None:
        output = str(self.case["gold_output"])

        self.assertEqual([], self.failures_for(output))

    def test_checker_allows_explicit_literal_transforms(self) -> None:
        case = valid_case(
            input="I can't promise to meet Lee.",
            gold_output="I cannot promise to meet Lee.",
            must_preserve_literals=["can't promise", "Lee"],
            must_preserve_uncertainty=[],
            required_ambiguity_fragments=[],
            allowed_transforms={"can't promise": ["cannot promise"]},
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

    def test_checker_rejects_missing_required_literal(self) -> None:
        self.assertFailureContains(
            "I might meet Leigh on 2026-06-03 at 4:30 PM. I do not promise.\n"
            "Review note: uncertainty remains visible.",
            "prose_uncertainty_commitment_001: must_preserve_literals: expected literal preserved exactly: Lee",
        )

    def test_checker_accepts_uncertainty_represented_in_review_note(self) -> None:
        case = valid_case(
            input="I might meet Lee.",
            gold_output="I may meet Lee.\nReview note: attendance remains uncertain.",
            must_preserve_literals=["Lee"],
            must_preserve_uncertainty=["might"],
            required_ambiguity_fragments=[],
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

    def test_checker_rejects_uncertainty_dropped_into_certainty(self) -> None:
        self.assertFailureContains(
            "Lee will meet on 2026-06-03 at 4:30 PM. I do not promise.\n"
            "Review note: formatting only.",
            "must_preserve_uncertainty: expected uncertainty marker preserved or represented",
        )

    def test_checker_rejects_unrelated_uncertainty_marker_for_specific_unclear_claim(self) -> None:
        case = valid_case(
            input="The policy date is unclear.",
            gold_output=(
                "The policy date is unclear.\n"
                "Review note: the policy date remains unclear."
            ),
            must_preserve_literals=["policy date"],
            must_preserve_uncertainty=["unclear"],
            required_ambiguity_fragments=[],
        )

        messages = "\n".join(
            self.failures_for(
                "The policy date is final.\nReview note: Maybe ask Pat about a different note.",
                case,
            )
        )

        self.assertIn(
            "must_preserve_uncertainty: expected uncertainty marker preserved or represented: unclear",
            messages,
        )

    def test_checker_rejects_uncertainty_preserved_in_wrong_scope(self) -> None:
        case = valid_case(
            input="Maybe ask HR about the form. The policy might be old.",
            gold_output=(
                "Maybe ask HR about the form.\n"
                "The policy might be old.\n"
                "Review note: both claims remain tentative."
            ),
            must_preserve_literals=["HR", "form", "policy"],
            must_preserve_uncertainty=["Maybe", "might"],
            must_preserve_uncertainty_scope=[
                "Maybe ask HR about the form",
                "policy might be old",
            ],
            required_ambiguity_fragments=[],
        )

        messages = "\n".join(
            self.failures_for(
                "Maybe ask HR about the form. The policy is old.\n"
                "Review note: ask HR remains tentative.",
                case,
            )
        )

        self.assertIn(
            "must_preserve_uncertainty_scope: expected scoped uncertainty preserved",
            messages,
        )

    def test_checker_rejects_commitment_inflation_with_unscoped_uncertainty_marker(self) -> None:
        case = self.fixture_case("prose_uncertainty_commitment_001")

        messages = "\n".join(
            self.failures_for(
                "# Prose repair\n\n"
                "I am coming Tuesday because my doctor thing maybe move.\n\n"
                "Review note: doctor thing maybe move remains unclear. "
                "I am not sure about the appointment.",
                case,
            )
        )

        self.assertIn(
            "must_preserve_uncertainty_scope: expected scoped uncertainty preserved",
            messages,
        )

    def test_checker_rejects_forbidden_patterns_and_introduced_terms(self) -> None:
        self.assertFailureContains(
            "I might meet Lee on 2026-06-03 at 4:30 PM. I do not promise.\n"
            "Review note: confirmed appointment; will meet.",
            "forbidden_patterns: expected pattern absent",
        )
        self.assertFailureContains(
            "I might meet Lee on 2026-06-03 at 4:30 PM. I do not promise.\n"
            "Review note: uncertainty remains visible. Lee will meet.",
            "must_not_introduce: expected term absent: will meet",
        )

    def test_checker_keeps_strict_introduced_terms_strict_when_limited(self) -> None:
        case = valid_case(
            input="Help me clean up this legal form note.",
            gold_output="This is not legal advice.",
            must_preserve_literals=[],
            must_preserve_uncertainty=[],
            must_not_introduce=["legal advice"],
            required_ambiguity_fragments=[],
            forbidden_patterns=[],
        )

        messages = "\n".join(self.failures_for(str(case["gold_output"]), case))

        self.assertIn(
            "must_not_introduce: expected term absent: legal advice",
            messages,
        )

    def test_checker_accepts_limited_legal_advice_disclaimer(self) -> None:
        case = self.limited_term_case(
            "legal advice",
            "This is not legal advice.",
            input_text="Help me clean up this legal form note.",
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

    def test_checker_rejects_unlimited_legal_advice_claim(self) -> None:
        case = self.limited_term_case(
            "legal advice",
            "This is not legal advice.",
            input_text="Help me clean up this legal form note.",
        )

        messages = "\n".join(self.failures_for("This is legal advice.", case))

        self.assertIn(
            "must_not_introduce_unless_limited: expected term absent unless limited: legal advice",
            messages,
        )

    def test_checker_rejects_limiter_that_targets_different_claim(self) -> None:
        case = self.limited_term_case(
            "legal advice",
            "This is not legal advice.",
            input_text="Help me clean up this legal form note.",
        )

        messages = "\n".join(
            self.failures_for("This is legal advice, not financial advice.", case)
        )

        self.assertIn(
            "must_not_introduce_unless_limited: expected term absent unless limited: legal advice",
            messages,
        )

    def test_checker_rejects_limiter_from_prior_comma_clause(self) -> None:
        case = self.limited_term_case(
            "legal advice",
            "This is not legal advice.",
            input_text="Help me clean up this legal form note.",
        )

        messages = "\n".join(
            self.failures_for(
                "This is not enough context, this is legal advice.",
                case,
            )
        )

        self.assertIn(
            "must_not_introduce_unless_limited: expected term absent unless limited: legal advice",
            messages,
        )

    def test_checker_accepts_limiter_immediately_after_limited_claim(self) -> None:
        case = self.limited_term_case(
            "legal advice",
            "Legal advice is not being provided.",
            input_text="Help me clean up this legal form note.",
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

    def test_checker_accepts_limited_medical_advice_disclaimer(self) -> None:
        case = self.limited_term_case(
            "medical advice",
            "This is not medical advice.",
            input_text="Help me clean up a medication note.",
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

    def test_checker_accepts_comma_delimited_limited_advice_list(self) -> None:
        legal_case = self.limited_term_case(
            "legal advice",
            "Use this to prioritize reading, not as tax, financial, or legal advice.",
            input_text="Help me clean up a tax source note.",
        )
        financial_case = self.limited_term_case(
            "financial advice",
            "Use this to reduce reading load; not insurance, legal, medical, or financial advice.",
            input_text="Help me clean up an insurance source note.",
        )

        self.assertEqual(
            [],
            self.failures_for(str(legal_case["gold_output"]), legal_case),
        )
        self.assertEqual(
            [],
            self.failures_for(str(financial_case["gold_output"]), financial_case),
        )

    def test_checker_rejects_unlimited_verified_source_support_claim(self) -> None:
        case = self.limited_term_case(
            "verified source support",
            "This is not verified source support.",
            input_text="Help me clean up a source-support note.",
        )

        messages = "\n".join(
            self.failures_for("This has verified source support.", case)
        )

        self.assertIn(
            "must_not_introduce_unless_limited: expected term absent unless limited: verified source support",
            messages,
        )

    def test_checker_accepts_limited_verified_source_support_disclaimer(self) -> None:
        case = self.limited_term_case(
            "verified source support",
            "This is not verified source support.",
            input_text="Help me clean up a source-support note.",
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

    def test_checker_rejects_missing_or_unflagged_ambiguity_fragment(self) -> None:
        case = ambiguous_name_case()
        messages_without_fragment = "\n".join(
            self.failures_for(
                "Send it to Anne.\n"
                "Review note: name choice needs checking.",
                case,
            )
        )
        messages_without_marker = "\n".join(
            self.failures_for(
                "Send it to Anne or Ann. I am not sure which name.",
                case,
            )
        )

        self.assertIn(
            "required_ambiguity_fragments: expected fragment visible: Anne or Ann",
            messages_without_fragment,
        )
        self.assertIn(
            "required_ambiguity_fragments: expected ambiguity or review marker near fragment: Anne or Ann",
            messages_without_marker,
        )

    def test_checker_accepts_preserved_status_without_ambiguity_label(self) -> None:
        case = self.fixture_case("prose_uncertainty_erasure_002")
        output = (
            "# Prose repair\n\n"
            "I maybe can send this Friday, but I am not sure because the clinic paper is not back.\n\n"
            "Status: the clinic paper is still not back."
        )

        self.assertNotIn("Ambiguity:", output)
        self.assertEqual([], self.failures_for(output, case))

    def test_checker_rejects_resolved_fixture_name_ambiguity(self) -> None:
        case = self.fixture_case("dictation_name_condition_001")
        output = (
            "# Dictation notes\n\n"
            "Source basis: user-provided voice note only.\n\n"
            "| Note | Type | Ambiguity | Next action |\n"
            "| --- | --- | --- | --- |\n"
            "| Send it to Anne or Ann. | task | Original note said not sure, but the correct name is Anne. | Send only after asking. |\n"
            "| We might ship the beta on 7/14 at 3pm if QA passes. | conditional plan | not sure; depends on QA. | Verify QA status before treating this as a commitment. |\n\n"
            "Next action: ask before sending."
        )

        messages = "\n".join(self.failures_for(output, case))

        self.assertIn(
            "ambiguity_resolution: expected ambiguity not resolved without user input",
            messages,
        )

    def test_checker_rejects_ambiguity_marker_detached_from_fragment(self) -> None:
        distant_review_note = (
            "Send it to Anne or Ann.\n\n"
            "Context: this line is padding about formatting only. "
            "It repeats no safety label near the name and does not identify the intended recipient. "
            "The extra distance matters because a distant note should not protect the name choice.\n\n"
            "Review note: schedule ambiguity remains. The speaker is not sure."
        )
        case = ambiguous_name_case()

        messages = "\n".join(
            self.failures_for(
                distant_review_note,
                case,
            )
        )

        self.assertIn(
            "required_ambiguity_fragments: expected ambiguity or review marker near fragment: Anne or Ann",
            messages,
        )

    def test_checker_rejects_ambiguity_fragment_resolved_as_correct(self) -> None:
        case = ambiguous_name_case()

        messages = "\n".join(
            self.failures_for(
                "Send it to Anne or Ann.\n"
                "User verification: the correct name is Anne. The original note was not sure.",
                case,
            )
        )

        self.assertIn(
            "ambiguity_resolution: expected ambiguity not resolved without user input",
            messages,
        )

    def test_checker_auto_preserves_numbers_dates_and_times(self) -> None:
        self.assertFailureContains(
            "I might meet Lee on 2026-06-04 at 4:30 PM. I do not promise.\n"
            "Review note: uncertainty remains visible.",
            "auto_preserve_literals: expected input number/date/time preserved",
        )
        self.assertFailureContains(
            "I might meet Lee on 2026-06-03 at 5:30 PM. I do not promise.\n"
            "Review note: uncertainty remains visible.",
            "auto_preserve_literals: expected input number/date/time preserved",
        )

    def test_checker_rejects_protected_literals_embedded_in_changed_tokens(self) -> None:
        case = self.fixture_case("prose_number_date_deformation_005")

        failures = self.failures_for(
            "# Prose repair\n\n"
            "The rent was 11450, not 11405, and the date was May 123, not May 210.\n"
            "Review note: The numbers and dates remain visible.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "auto_preserve_literals: expected input number/date/time preserved: 1450",
            messages,
        )
        self.assertIn(
            "auto_preserve_literals: expected input number/date/time preserved: May 12",
            messages,
        )

    def test_checker_rejects_number_and_date_contrast_reversal(self) -> None:
        case = self.fixture_case("prose_number_date_deformation_005")

        messages = "\n".join(
            self.failures_for(
                "# Prose repair\n\n"
                "The rent amount is 1405, not 1450, and the listed date is May 21, not May 12.\n"
                "Review note: The numbers and dates were preserved.",
                case,
            )
        )

        self.assertIn(
            "must_preserve_negation_scope: expected scoped negation preserved",
            messages,
        )

    def test_checker_auto_preserves_negations(self) -> None:
        self.assertFailureContains(
            "I might meet Lee on 2026-06-03 at 4:30 PM. I promise.\n"
            "Review note: uncertainty remains visible.",
            "auto_preserve_negations: expected negation preserved or explicitly transformed",
        )

    def test_checker_rejects_manager_contact_with_unscoped_negation_marker(self) -> None:
        case = self.fixture_case("prose_negation_loss_004")

        messages = "\n".join(
            self.failures_for(
                "# Prose repair\n\n"
                "I do not know timing. They can contact my manager yet.",
                case,
            )
        )

        self.assertIn(
            "must_preserve_negation_scope: expected scoped negation preserved",
            messages,
        )

    def test_checker_rejects_negation_preserved_in_wrong_scope(self) -> None:
        case = valid_case(
            input="I do not authorize payroll to share my address.",
            gold_output="I do not authorize payroll to share my address.",
            must_preserve_literals=["payroll", "address"],
            must_preserve_uncertainty=[],
            required_ambiguity_fragments=[],
            must_preserve_negation_scope=[
                "do not authorize payroll to share my address"
            ],
        )

        messages = "\n".join(
            self.failures_for(
                "I do not know payroll's process. Payroll may share my address.",
                case,
            )
        )

        self.assertIn(
            "must_preserve_negation_scope: expected scoped negation preserved",
            messages,
        )

    def test_checker_rejects_invented_citations_pages_and_verification_claims(self) -> None:
        case = valid_case(
            input="Smith 2021, p. 42, citation only. This may affect a legal budget note.",
            gold_output=(
                "Smith 2021, p. 42, citation only. This may affect a legal budget note.\n"
                "Review note: source support remains unverified."
            ),
            must_preserve_literals=["Smith 2021", "p. 42", "citation only"],
            must_preserve_uncertainty=["may", "unverified"],
            required_ambiguity_fragments=[],
        )

        failures = self.failures_for(
            "Smith 2021, p. 42, citation only. I verified the full text [3] on page 99.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn("citation_like_strings: expected no new citation marker", messages)
        self.assertIn("page_like_strings: expected no new page marker", messages)
        self.assertIn(
            "verification_claims: expected no invented verification claim",
            messages,
        )

    def test_checker_rejects_broader_invented_verification_claims(self) -> None:
        case = valid_case(
            input="Smith 2021, p. 42, citation only. This may affect a legal policy note.",
            gold_output=(
                "Smith 2021, p. 42, citation only. This may affect a legal policy note.\n"
                "Review note: source support remains unverified."
            ),
            must_preserve_literals=["Smith 2021", "p. 42", "citation only"],
            must_preserve_uncertainty=["may", "unverified"],
            required_ambiguity_fragments=[],
        )

        failures = self.failures_for(
            "Smith 2021, p. 42, citation only. This may affect a legal policy note.\n"
            "Source support remains unverified. I reviewed the full text, and the study demonstrates the claim.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "verification_claims: expected no invented verification claim",
            messages,
        )

    def test_checker_rejects_invented_high_stakes_claim_synonyms(self) -> None:
        case = valid_case(
            input="My doctor maybe said I should stop meds but the note is unclear.",
            gold_output=(
                "My doctor maybe said I should stop meds, but the note is unclear.\n"
                "Review note: the note is unclear."
            ),
            must_preserve_literals=["doctor", "meds", "note"],
            must_preserve_uncertainty=["maybe", "unclear"],
            required_ambiguity_fragments=["note is unclear"],
        )

        failures = self.failures_for(
            "My doctor maybe said I should stop meds, and the note is unclear.\n"
            "Review note: the note is unclear.\n"
            "The clinician advised discontinuing medication.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "verification_claim_patterns: expected no invented verification or high-stakes advice pattern",
            messages,
        )
        self.assertIn("clinician advised", messages)

    def test_checker_rejects_source_overclaim_synonyms(self) -> None:
        case = valid_case(
            id="reading_citation_only_eviction_001",
            skill="accessibility-reading-load-reducer",
            input=(
                "Citation only: Lopez 2022, p. 9. User note says maybe about eviction notices, "
                "but I have not opened it."
            ),
            gold_output=(
                "Lopez 2022, p. 9 may be about eviction notices, but I have not opened it.\n"
                "Review note: source support remains unverified."
            ),
            must_preserve_literals=["Lopez 2022", "p. 9", "eviction notices", "not opened"],
            must_preserve_uncertainty=["maybe", "not opened", "unverified"],
            must_preserve_uncertainty_scope=["maybe about eviction notices"],
            must_preserve_negation_scope=["not opened it"],
            required_ambiguity_fragments=[],
        )

        failures = self.failures_for(
            "Lopez 2022, p. 9: user note says maybe about eviction notices, but I have not opened it.\n"
            "Source support remains unverified. The paper establishes the eviction notice rule.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "verification_claim_patterns: expected no invented verification or high-stakes advice pattern",
            messages,
        )
        self.assertIn("paper establishes", messages)

    def test_checker_rejects_high_stakes_guarantee_and_eligibility_overclaims(self) -> None:
        case = self.refund_citation_only_case()

        failures = self.failures_for(
            "Lopez 2022 may affect a tax refund, but I have not opened it.\n"
            "Source support remains unverified. The rule guarantees eligibility.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "high_stakes_claim_patterns: expected no invented high-stakes guarantee, eligibility, or authorization claim",
            messages,
        )
        self.assertIn("rule guarantees eligibility", messages)

    def test_checker_rejects_high_stakes_overclaim_after_unverified_contrast(self) -> None:
        case = self.refund_citation_only_case()

        failures = self.failures_for(
            "Lopez 2022 may affect a tax refund, but I have not opened it.\n"
            "Although source support remains unverified, the rule guarantees eligibility.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "high_stakes_claim_patterns: expected no invented high-stakes guarantee, eligibility, or authorization claim",
            messages,
        )
        self.assertIn("rule guarantees eligibility", messages)

    def test_checker_rejects_high_stakes_overclaim_after_comma_delimited_limiter(self) -> None:
        case = self.refund_citation_only_case()

        failures = self.failures_for(
            "Lopez 2022 may affect a tax refund, but I have not opened it.\n"
            "Source support remains unverified, the rule guarantees eligibility.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "high_stakes_claim_patterns: expected no invented high-stakes guarantee, eligibility, or authorization claim",
            messages,
        )
        self.assertIn("rule guarantees eligibility", messages)

    def test_checker_rejects_financial_entitlement_overclaim_synonyms(self) -> None:
        case = valid_case(
            id="reading_title_only_refund_001",
            skill="accessibility-reading-load-reducer",
            input="Bank fee article title only: 'New overdraft refund rules'.",
            gold_output=(
                "New overdraft refund rules may be relevant.\n"
                "Review note: refund eligibility is not verified."
            ),
            must_preserve_literals=["New overdraft refund rules"],
            must_preserve_uncertainty=["not verified"],
            required_ambiguity_fragments=[],
        )

        failures = self.failures_for(
            "New overdraft refund rules may be relevant.\n"
            "Review note: refund eligibility is not verified. You are entitled to the refund.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "high_stakes_claim_patterns: expected no invented high-stakes guarantee, eligibility, or authorization claim",
            messages,
        )
        self.assertIn("entitled to the refund", messages)

    def test_checker_rejects_direct_medication_instruction_synonyms(self) -> None:
        case = self.fixture_case("prose_medical_certainty_007")

        failures = self.failures_for(
            "# Prose repair\n\n"
            "My doctor maybe said I should stop meds, but the note is unclear.\n\n"
            "Review note: the note is unclear.\n"
            "You should discontinue the medication.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "verification_claim_patterns: expected no invented verification or high-stakes advice pattern",
            messages,
        )
        self.assertIn("discontinue the medication", messages)

    def test_checker_rejects_direct_stop_medication_instruction(self) -> None:
        case = self.fixture_case("prose_medical_certainty_007")

        failures = self.failures_for(
            "# Prose repair\n\n"
            "My doctor maybe said I should stop meds, but the note is unclear.\n\n"
            "Review note: the note is unclear.\n"
            "You should stop medication.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "verification_claim_patterns: expected no invented verification or high-stakes advice pattern",
            messages,
        )
        self.assertIn("stop medication", messages)

    def test_checker_rejects_privacy_search_and_shareability_overclaims(self) -> None:
        case = valid_case(
            id="low_load_private_search_001",
            skill="accessibility-low-load-companion",
            input="Private HR note: do not paste this into search or any external tool.",
            gold_output=(
                "Boundary: do not paste this into search or any external tool.\n"
                "Next action: keep it private."
            ),
            must_preserve_literals=["HR note", "search", "external tool"],
            must_preserve_uncertainty=[],
            must_preserve_negation_scope=[
                "do not paste this into search or any external tool"
            ],
            required_ambiguity_fragments=[],
        )

        failures = self.failures_for(
            "Private HR note boundary: do not paste this into search or any external tool.\n"
            "I searched online and made a shareable summary.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "verification_claims: expected no invented verification claim",
            messages,
        )
        self.assertIn(
            "privacy_claim_patterns: expected no invented privacy, consent, external-search, or shareability claim",
            messages,
        )

    def test_checker_rejects_negated_source_limit_and_triage_markers(self) -> None:
        case = valid_case(
            id="reading_title_only_access_001",
            skill="accessibility-reading-load-reducer",
            input="Article title only: 'Attachment and burnout'.",
            gold_output=(
                "Source basis: title/citation/metadata only.\n"
                "How to use this result: TRIAGE ONLY - Use this to prioritize reading.\n"
                "Source limit: unverified source support."
            ),
            must_preserve_literals=[],
            must_preserve_uncertainty=["unverified"],
            required_ambiguity_fragments=[],
            required_source_basis_fragments=[
                "Source basis",
                "title/citation/metadata only",
            ],
            required_source_limit_fragments=[
                "TRIAGE ONLY",
                "unverified source support",
            ],
            required_access_level="title/citation/metadata only",
            requires_triage_only_warning=True,
        )

        failures = self.failures_for(
            "Source basis: not title/citation/metadata only.\n"
            "How to use this result: not TRIAGE ONLY - verified synthesis.\n"
            "Source limit: not unverified source support.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "source_fragment_polarity: expected source or limit fragment not negated",
            messages,
        )
        self.assertIn(
            "triage_only_warning: expected TRIAGE ONLY warning not negated",
            messages,
        )

    def test_checker_rejects_low_load_length_regression_when_limit_is_set(self) -> None:
        case = valid_case(
            id="low_load_brevity_commitment_001",
            skill="accessibility-low-load-companion",
            input="make this easier but I am overloaded: I might reply tomorrow, not promising.",
            gold_output=(
                "# Low-load accessibility support\n\n"
                "Reply wording: I might reply tomorrow, not promising.\n\n"
                "Next action: leave it tentative."
            ),
            must_preserve_literals=["tomorrow", "not promising"],
            must_preserve_uncertainty=["might", "not promising"],
            must_preserve_uncertainty_scope=["might reply tomorrow"],
            must_preserve_negation_scope=["not promising"],
            required_ambiguity_fragments=[],
            max_output_lines=5,
        )
        long_output = (
            str(case["gold_output"])
            + "\n\nExtra explanation.\nExtra explanation.\nExtra explanation."
        )

        messages = "\n".join(self.failures_for(long_output, case))

        self.assertIn(
            "max_output_lines: expected output has at most 5 lines",
            messages,
        )

    def test_checker_rejects_sensitive_detail_in_team_update_permission(self) -> None:
        case = self.fixture_case("dictation_privacy_negation_007")

        failures = self.failures_for(
            "# Dictation notes\n\n"
            "Source basis: user-provided voice note only.\n"
            "How to use this result: TRIAGE ONLY - Do not treat this as shareable wording.\n\n"
            "| Note | Type | Ambiguity | Next action |\n"
            "| --- | --- | --- | --- |\n"
            "| Do not share Morgan's diagnosis with the team. | privacy boundary | None. | Do not include this in a team update. |\n"
            "| Maybe ask Morgan what can be said. | consent question | maybe. | Ask Morgan before sharing. |\n\n"
            "Next action: You can include Morgan's diagnosis in the team update.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn(
            "privacy_claim_patterns: expected no invented privacy, consent, external-search, or shareability claim",
            messages,
        )
        self.assertIn("include Morgan's diagnosis in the team update", messages)

    def test_checker_rejects_worded_wrong_number_and_date_for_fixture_patterns(self) -> None:
        case = self.fixture_case("prose_number_date_deformation_005")

        messages = "\n".join(
            self.failures_for(
                "# Prose repair\n\n"
                "The rent was 1450, not 1405, and the date was May 12, not May 21.\n"
                "The correct amount is fourteen hundred five and the correct date is May twenty-one.",
                case,
            )
        )

        self.assertIn("forbidden_patterns: expected pattern absent", messages)

    def test_checker_requires_reading_load_source_limit_invariants(self) -> None:
        case = valid_case(
            id="reading_title_only_access_001",
            skill="accessibility-reading-load-reducer",
            input="Article title only: 'Attachment and burnout in autistic adults'. Should I skip?",
            gold_output=(
                "# Reading triage\n\n"
                "Source basis: title/citation/metadata only; no abstract or full text.\n"
                "How to use this result: TRIAGE ONLY - Use this to prioritize reading, not as verified source support.\n\n"
                "| Item | Access level | Decision | Why | First extraction target | Skip/park risk |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                "| Attachment and burnout in autistic adults | title/citation/metadata only | park | title looks relevant, but only the title is visible | abstract or full text | Do not treat this as verified source support. |\n\n"
                "Uncertainty: the title does not show the article's claims.\n"
                "Next action: get the abstract before deciding whether to skip."
            ),
            must_preserve_literals=[
                "Attachment and burnout in autistic adults",
            ],
            must_preserve_uncertainty=[],
            must_not_introduce=[],
            required_ambiguity_fragments=[],
            forbidden_patterns=[],
            required_source_basis_fragments=[
                "Source basis",
                "title/citation/metadata only",
            ],
            required_source_limit_fragments=[
                "Do not treat this as verified source support",
            ],
            required_access_level="title/citation/metadata only",
            prohibited_verification_claims=[
                "the article proves the claim",
                "verified synthesis",
            ],
            requires_triage_only_warning=True,
        )

        self.assertEqual([], self.failures_for(str(case["gold_output"]), case))

        failures = self.failures_for(
            "# Summary\n\nAttachment and burnout in autistic adults: the article proves the claim. This is verified synthesis.",
            case,
        )
        messages = "\n".join(failures)

        self.assertIn("required_source_basis_fragments", messages)
        self.assertIn("required_source_limit_fragments", messages)
        self.assertIn("required_access_level", messages)
        self.assertIn("triage_only_warning", messages)
        self.assertIn("prohibited_verification_claims", messages)

    def test_checker_rejects_requested_review_risk_regressions(self) -> None:
        unsafe_outputs = {
            "prose_cancel_negation_015": (
                "# Prose repair\n\n"
                "I want to cancel the appointment.\n\n"
                "Review note: formatting only."
            ),
            "prose_tell_alex_uncertainty_016": (
                "# Prose repair\n\n"
                "I should tell Alex.\n\n"
                "Review note: direct action made clear."
            ),
            "prose_report_due_claim_strength_017": (
                "# Prose repair\n\n"
                "My manager said the report is due Friday.\n\n"
                "Review note: deadline clarified."
            ),
            "prose_grammar_only_style_018": (
                "# Prose repair\n\n"
                "I strongly oppose the plan, and we need to escalate it now.\n\n"
                "Review note: grammar fixed."
            ),
        }

        for case_id, output in unsafe_outputs.items():
            with self.subTest(case_id=case_id):
                failures = self.failures_for(output, self.fixture_case(case_id))

                self.assertNotEqual([], failures)


class SemanticPreservationCliTests(unittest.TestCase):
    def test_evaluator_accepts_json_outputs(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        outputs = [
            {"case_id": case["id"], "output": case["gold_output"]}
            for case in payload["cases"]
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "outputs.json"
            output_path.write_text(json.dumps({"outputs": outputs}), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(EVALUATOR_PATH),
                    "--cases",
                    str(FIXTURE_PATH),
                    "--outputs",
                    str(output_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("passed", result.stdout)

    def test_evaluator_rejects_jsonl_outputs_with_contract_failures(self) -> None:
        failing_output = {
            "case_id": "prose_uncertainty_commitment_001",
            "output": "I will come Tuesday. The appointment is confirmed.",
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "outputs.jsonl"
            output_path.write_text(json.dumps(failing_output) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(EVALUATOR_PATH),
                    "--cases",
                    str(FIXTURE_PATH),
                    "--outputs",
                    str(output_path),
                    "--allow-missing",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("FAIL prose_uncertainty_commitment_001", result.stdout)
        self.assertIn("must_preserve_uncertainty", result.stdout)


if __name__ == "__main__":
    unittest.main()
