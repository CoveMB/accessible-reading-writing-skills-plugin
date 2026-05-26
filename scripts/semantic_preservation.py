"""Deterministic semantic-preservation regression checks.

This module is a regression guard, not a proof that no meaning loss can happen.
It checks explicit invariants that are cheap and deterministic: protected
literals, uncertainty markers, ambiguity flags, negation, dates/times/numbers,
source-limit wording, and forbidden additions.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STABLE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*_[0-9]{3}$")
REQUIRED_CASE_FIELDS = ("id", "skill", "risk_type", "input", "gold_output")
STRING_LIST_FIELDS = (
    "risk_type",
    "must_preserve_literals",
    "must_preserve_uncertainty",
    "must_preserve_uncertainty_scope",
    "must_preserve_negation_scope",
    "must_not_introduce",
    "required_ambiguity_fragments",
    "required_source_basis_fragments",
    "required_source_limit_fragments",
    "prohibited_verification_claims",
    "forbidden_patterns",
)
SUPPORTED_CASE_FIELDS = {
    *REQUIRED_CASE_FIELDS,
    *STRING_LIST_FIELDS,
    "allowed_transforms",
    "required_access_level",
    "requires_triage_only_warning",
    "max_output_chars",
    "max_output_lines",
    "notes",
}

CITATION_MARKER_RE = re.compile(
    r"\[[0-9]{1,3}\]"
    r"|\([A-Z][A-Za-z]+(?: et al\.)?,\s*(?:19|20)[0-9]{2}\)"
    r"|\b[A-Z][A-Za-z]+(?: et al\.)?\s+(?:19|20)[0-9]{2}\b"
    r"|\bdoi:\s*10\.\S+",
    re.IGNORECASE,
)
PAGE_MARKER_RE = re.compile(
    r"\b(?:p\.|pp\.|page|pages)\s*[0-9]+(?:\s*[-/]\s*[0-9]+)?\b",
    re.IGNORECASE,
)
PROTECTED_LITERAL_PATTERNS = (
    re.compile(r"(?<!\w)[$€£]\s?[0-9][0-9,]*(?:\.[0-9]+)?"),
    re.compile(r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b"),
    re.compile(r"\b[0-9]{1,2}/[0-9]{1,2}(?:/[0-9]{2,4})?\b"),
    re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+[0-9]{1,2}(?:,\s*[0-9]{4})?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[0-9]{1,2}:[0-9]{2}\s*(?:a\.m\.|p\.m\.|am|pm)?\b", re.IGNORECASE),
    re.compile(r"\b[0-9]{1,2}\s*(?:a\.m\.|p\.m\.|am|pm)\b", re.IGNORECASE),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?%\b"),
    re.compile(r"\b[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?\b"),
    re.compile(r"\b[0-9]+\.[0-9]+\b"),
    re.compile(r"\b[0-9]+\b"),
)
NEGATION_PATTERNS = (
    re.compile(
        r"\b(?:do|does|did|is|are|was|were|have|has|had|can|could|should|"
        r"would|will|must)\s+not\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:don't|doesn't|didn't|isn't|aren't|wasn't|weren't|haven't|"
        r"hasn't|hadn't|can't|cannot|couldn't|shouldn't|wouldn't|won't|mustn't)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:not|no|never|without)\b", re.IGNORECASE),
)
NEGATION_EQUIVALENTS = {
    "can't": ("cannot", "can not"),
    "cannot": ("can't", "can not"),
    "can not": ("can't", "cannot"),
    "don't": ("do not",),
    "do not": ("don't",),
    "doesn't": ("does not",),
    "does not": ("doesn't",),
    "didn't": ("did not",),
    "did not": ("didn't",),
    "won't": ("will not",),
    "will not": ("won't",),
    "isn't": ("is not",),
    "is not": ("isn't",),
    "aren't": ("are not",),
    "are not": ("aren't",),
    "wasn't": ("was not",),
    "was not": ("wasn't",),
    "weren't": ("were not",),
    "were not": ("weren't",),
}
UNCERTAINTY_RE = re.compile(
    r"\b(?:might|may|maybe|possibly|possible|uncertain|uncertainty|not sure|"
    r"not confirmed|tentative|conditional|depends|unclear|unverified)\b"
    r"|\bif\b",
    re.IGNORECASE,
)
AMBIGUITY_OR_REVIEW_RE = re.compile(
    r"\b(?:ambiguity|ambiguous|review note|user check|question|unclear|"
    r"verify|verification|confirm|unverified|source basis)\b",
    re.IGNORECASE,
)
AMBIGUITY_RESOLUTION_RE = re.compile(
    r"\b(?:no ambiguity|ambiguity resolved|clearly means|must mean|"
    r"the intended (?:meaning|name|word) is|correct (?:name|word|spelling) is|"
    r"recipient is)\b",
    re.IGNORECASE,
)
AMBIGUITY_MARKER_WINDOW_CHARS = 180
SPECIFIC_UNCERTAINTY_RE = re.compile(
    r"\b(?:unclear|uncertain|unsure|not sure|not confirmed|unconfirmed|"
    r"unverified|not verified|not checked|needs? checking|needs? to be checked|"
    r"needs? verification|user verification needed|review needed|verify|verification|"
    r"check|tentative|provisional|conditional|depends|may have|could be|not firm)\b",
    re.IGNORECASE,
)
CONDITIONAL_UNCERTAINTY_RE = re.compile(
    r"\b(?:if|only if|depends|conditional|condition|provided that|unless|before treating)\b",
    re.IGNORECASE,
)
TRIAGE_ONLY_RE = re.compile(r"\bTRIAGE ONLY\b", re.IGNORECASE)
VERIFICATION_CLAIM_PHRASES = (
    "I verified",
    "I reviewed",
    "I validated",
    "I confirmed",
    "I searched",
    "I checked",
    "I looked up",
    "I found",
    "official source says",
    "official source states",
    "source confirms",
    "source validates",
    "source verifies",
    "the source confirms",
    "the source states",
    "the source says",
    "confirmed by the source",
    "confirmed in the source",
    "according to the full text",
    "verified source support",
    "full text confirms",
    "abstract shows",
    "the abstract shows",
    "article demonstrates",
    "the article demonstrates",
    "study demonstrates",
    "the study demonstrates",
    "policy confirms",
    "the policy confirms",
    "policy states",
    "the policy states",
    "evidence proves",
    "evidence shows",
    "research shows",
)
VERIFICATION_CLAIM_PATTERNS = (
    re.compile(
        r"\b(?:paper|article|source|study|policy|law|rule|research|evidence)\b"
        r"[^.\n|]{0,80}\b(?<!not )(?<!does not )(?<!do not )"
        r"(?:establishes?|shows?|proves?|states?|says?|demonstrates?|"
        r"confirms?|validates?)\b[^.\n|]{0,80}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:doctor|clinician|provider|medical professional)\b.{0,80}"
        r"\b(?:advis(?:e|ed|es|ing)|instruct(?:ed|s|ing)?|"
        r"recommend(?:ed|s|ing)?|cleared|approved)\b.{0,80}"
        r"\b(?:meds?|medication|dose|dosage|treatment|start|stop|stopping|"
        r"discontinu(?:e|ed|ing)|safe)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:meds?|medication|dose|dosage|treatment)\b.{0,80}"
        r"\b(?:is|are|was|were)\s+(?:safe|approved|clinically proven|recommended)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:you|user|patient|client)\b.{0,80}"
        r"\b(?:should|must|need(?:s)? to|can safely|can)\b.{0,80}"
        r"\b(?:start|stop|change|increase|decrease|take|avoid|"
        r"discontinu(?:e|ed|ing))\b.{0,80}"
        r"\b(?:meds?|medication|dose|dosage|treatment)\b",
        re.IGNORECASE,
    ),
)
HIGH_STAKES_INPUT_RE = re.compile(
    r"\b(?:legal|law|policy|contract|medical|doctor|diagnosis|meds|medication|"
    r"clinical|financial|finance|budget|refund|tax|loan|insurance)\b|[$€£]\s?[0-9]",
    re.IGNORECASE,
)
PRIVACY_SENSITIVE_INPUT_RE = re.compile(
    r"\b(?:private|confidential|hr|human resources|diagnosis|health|address|"
    r"manager|payroll|external tool|search|share|sharing|consent|permission)\b",
    re.IGNORECASE,
)
HIGH_STAKES_CLAIM_PATTERNS = (
    re.compile(
        r"\b(?:policy|law|rule|contract|insurance|insurer|bank|source|"
        r"article|study|paper)\b[^.\n|]{0,80}"
        r"\b(?:guarantees?|authorizes?|approves?|allows?|requires?|confirms?|"
        r"verifies?|establishes?)\b[^.\n|]{0,80}"
        r"\b(?:eligib(?:le|ility)|refund|coverage|legal|safe|required|"
        r"authorized|approved|claim|right|obligation|notice|tax|loan|payment)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:you|user|client|patient|tenant|employee)\b[^.\n|]{0,50}"
        r"\b(?:qualif(?:y|ies)|eligible|approved|authorized|guaranteed|"
        r"covered|entitled|owed|has\s+(?:a\s+)?right)\b[^.\n|]{0,80}"
        r"\b(?:refund|coverage|tax|loan|benefit|medication|claim|payment)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:refund|coverage|tax credit|loan|benefit|medication|claim|payment)\b"
        r"[^.\n|]{0,50}\b(?:is|are|was|were|has been|have been|will be)\s+"
        r"(?:guaranteed|approved|authorized|covered|confirmed|verified|owed)\b",
        re.IGNORECASE,
    ),
)
PRIVACY_CLAIM_PATTERNS = (
    re.compile(
        r"\b(?:safe to (?:share|paste|send)|shareable summary|shareable update|"
        r"permission confirmed|consent confirmed|authorized sharing|"
        r"(?:can|may) be shared)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:can|may|should|okay to|ok to|safe to|allowed to)\s+"
        r"(?:include|send|share|disclose|post)\b[^.\n|]{0,80}"
        r"\b(?:diagnosis|health|address|hr note|private|confidential)\b"
        r"[^.\n|]{0,80}\b(?:team|update|external|search|manager|public)\b",
        re.IGNORECASE,
    ),
)
CLAIM_LIMITER_RE = re.compile(
    r"\b(?:not|no|cannot|can't|does not|do not|without|whether|uncertain|"
    r"unclear|unverified|not verified|not guaranteed|not enough|cannot establish|"
    r"does not show|do not treat)\b",
    re.IGNORECASE,
)
CONTRAST_CONNECTOR_RE = re.compile(
    r"\b(?:although|though|even though|despite|but|however|nevertheless|yet)\b",
    re.IGNORECASE,
)
NEGATED_FRAGMENT_PREFIX_RE = re.compile(
    r"\b(?:not|no|never|without|not actually|not really)\s+(?:[\w/-]+\s+){0,3}$",
    re.IGNORECASE,
)


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_cases_payload(payload: Any, root: Path = ROOT) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload: expected JSON object"]

    errors: list[str] = []
    if payload.get("version") != 1:
        errors.append("version: expected 1")
    if not non_empty_string(payload.get("purpose")):
        errors.append("purpose: expected non-empty string")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases: expected non-empty list")
        return errors

    seen_ids: set[str] = set()
    for index, case in enumerate(cases):
        errors.extend(validate_case_schema(case, index, seen_ids, root))
    return errors


def validate_case_schema(
    case: Any,
    index: int,
    seen_ids: set[str],
    root: Path,
) -> list[str]:
    if not isinstance(case, dict):
        return [f"cases[{index}]: expected object"]

    case_id = case.get("id") if isinstance(case.get("id"), str) else f"cases[{index}]"
    label = str(case_id)
    errors: list[str] = []

    errors.extend(validate_supported_fields(case, label))
    errors.extend(validate_required_fields(case, label))
    errors.extend(validate_case_id(case, label, seen_ids))
    errors.extend(validate_skill_reference(case, label, root))
    errors.extend(validate_string_list_fields(case, label))
    errors.extend(validate_allowed_transforms(case, label))
    errors.extend(validate_reading_load_source_limit_fields(case, label))
    errors.extend(validate_output_length_fields(case, label))
    errors.extend(validate_risk_type_invariants(case, label))
    errors.extend(validate_forbidden_patterns(case, label))
    if "notes" in case and not isinstance(case["notes"], str):
        errors.append(f"{label}: notes: expected string")
    return errors


def validate_supported_fields(case: dict[str, Any], label: str) -> list[str]:
    return [
        f"{label}: {field_name}: unsupported field"
        for field_name in case
        if field_name not in SUPPORTED_CASE_FIELDS
    ]


def validate_required_fields(case: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field_name in ("id", "skill", "input", "gold_output"):
        if not non_empty_string(case.get(field_name)):
            errors.append(f"{label}: {field_name}: expected non-empty string")
    if not non_empty_string_list(case.get("risk_type")):
        errors.append(f"{label}: risk_type: expected non-empty list of strings")
    return errors


def validate_case_id(
    case: dict[str, Any],
    label: str,
    seen_ids: set[str],
) -> list[str]:
    case_id = case.get("id")
    if not isinstance(case_id, str):
        return []

    errors: list[str] = []
    if case_id in seen_ids:
        errors.append(f"{label}: id is duplicated")
    else:
        seen_ids.add(case_id)
    if not STABLE_ID_RE.fullmatch(case_id):
        errors.append(
            f"{label}: id must match stable pattern "
            "<lowercase_words>_<three_digits>"
        )
    return errors


def validate_skill_reference(case: dict[str, Any], label: str, root: Path) -> list[str]:
    skill = case.get("skill")
    if not isinstance(skill, str) or not skill.strip():
        return []
    skill_path = root / "skills" / skill / "SKILL.md"
    if skill_path.exists():
        return []
    return [f"{label}: skill: expected existing skill folder, got {skill}"]


def validate_string_list_fields(case: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field_name in STRING_LIST_FIELDS:
        if field_name in case and not string_list(case[field_name]):
            errors.append(f"{label}: {field_name}: expected list of strings")
    return errors


def validate_allowed_transforms(case: dict[str, Any], label: str) -> list[str]:
    if "allowed_transforms" not in case:
        return []
    transforms = case["allowed_transforms"]
    if not isinstance(transforms, dict):
        return [f"{label}: allowed_transforms: expected object mapping strings to lists"]

    errors: list[str] = []
    for original, replacements in transforms.items():
        if not isinstance(original, str) or not original:
            errors.append(f"{label}: allowed_transforms: expected non-empty string keys")
            continue
        if not string_list(replacements):
            errors.append(
                f"{label}: allowed_transforms.{original}: expected list of strings"
            )
    return errors


def validate_reading_load_source_limit_fields(
    case: dict[str, Any],
    label: str,
) -> list[str]:
    errors: list[str] = []
    if case.get("skill") == "accessibility-reading-load-reducer":
        if not non_empty_string_list(case.get("required_source_basis_fragments")):
            errors.append(
                f"{label}: required_source_basis_fragments: expected non-empty list for reading-load cases"
            )
        if not non_empty_string_list(case.get("required_source_limit_fragments")):
            errors.append(
                f"{label}: required_source_limit_fragments: expected non-empty list for reading-load cases"
            )
        if not non_empty_string(case.get("required_access_level")):
            errors.append(
                f"{label}: required_access_level: expected non-empty string for reading-load cases"
            )
        if case.get("requires_triage_only_warning") is not True:
            errors.append(
                f"{label}: requires_triage_only_warning: expected true for reading-load cases"
            )
    if "required_access_level" in case and not non_empty_string(
        case["required_access_level"]
    ):
        errors.append(f"{label}: required_access_level: expected non-empty string")
    if "requires_triage_only_warning" in case and not isinstance(
        case["requires_triage_only_warning"],
        bool,
    ):
        errors.append(f"{label}: requires_triage_only_warning: expected boolean")
    return errors


def validate_output_length_fields(case: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field_name in ("max_output_chars", "max_output_lines"):
        if field_name in case and not positive_int(case[field_name]):
            errors.append(f"{label}: {field_name}: expected positive integer")
    return errors


def validate_risk_type_invariants(case: dict[str, Any], label: str) -> list[str]:
    risk_types = case.get("risk_type")
    if not string_list(risk_types):
        return []
    if not has_risk_label(risk_types, "negation"):
        return []
    if non_empty_string_list(case.get("must_preserve_negation_scope")):
        return []
    return [
        f"{label}: must_preserve_negation_scope: expected non-empty list for negation risk"
    ]


def has_risk_label(risk_types: list[str], keyword: str) -> bool:
    return any(keyword in risk_type.casefold() for risk_type in risk_types)


def validate_forbidden_patterns(case: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for pattern in case.get("forbidden_patterns", []):
        try:
            re.compile(pattern)
        except re.error as exc:
            errors.append(
                f"{label}: forbidden_patterns: expected valid regex for {pattern}: {exc}"
            )
    return errors


def evaluate_gold_outputs(cases: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for case in cases:
        failures.extend(evaluate_case(case, str(case.get("gold_output", ""))))
    return failures


def evaluate_reference_outputs(cases: list[dict[str, Any]]) -> list[str]:
    return evaluate_gold_outputs(cases)


def evaluate_case(case: dict[str, Any], output: str | None = None) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    input_text = str(case.get("input", ""))
    candidate_output = str(case.get("gold_output", "") if output is None else output)
    if not candidate_output.strip():
        return [failure(case_id, "output", "non-empty string")]

    transforms = normalized_allowed_transforms(case.get("allowed_transforms", {}))
    return [
        *must_preserve_literal_failures(case, candidate_output, transforms),
        *must_preserve_uncertainty_failures(case, candidate_output),
        *must_preserve_uncertainty_scope_failures(case, candidate_output, transforms),
        *must_preserve_negation_scope_failures(case, candidate_output, transforms),
        *must_not_introduce_failures(case, candidate_output),
        *forbidden_pattern_failures(case, candidate_output),
        *required_ambiguity_fragment_failures(case, candidate_output, transforms),
        *ambiguity_resolution_failures(case, candidate_output, transforms),
        *required_source_basis_fragment_failures(case, candidate_output, transforms),
        *required_source_limit_fragment_failures(case, candidate_output, transforms),
        *required_access_level_failures(case, candidate_output, transforms),
        *source_fragment_polarity_failures(case, candidate_output, transforms),
        *triage_only_warning_failures(case, candidate_output),
        *output_length_failures(case, candidate_output),
        *prohibited_verification_claim_failures(case, candidate_output),
        *auto_protected_literal_failures(case_id, input_text, candidate_output, transforms),
        *auto_negation_failures(case_id, input_text, candidate_output, transforms),
        *new_source_marker_failures(case_id, input_text, candidate_output),
        *invented_verification_claim_failures(case_id, input_text, candidate_output),
        *invented_verification_pattern_failures(case_id, input_text, candidate_output),
        *invented_high_stakes_claim_pattern_failures(case_id, input_text, candidate_output),
        *invented_privacy_claim_pattern_failures(case_id, input_text, candidate_output),
    ]


def must_preserve_literal_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    return [
        failure(case_id, "must_preserve_literals", f"literal preserved exactly: {literal}")
        for literal in case.get("must_preserve_literals", [])
        if not literal_or_transform_present(str(literal), output, transforms)
    ]


def must_preserve_uncertainty_failures(
    case: dict[str, Any],
    output: str,
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    return [
        failure(
            case_id,
            "must_preserve_uncertainty",
            f"uncertainty marker preserved or represented: {marker}",
        )
        for marker in case.get("must_preserve_uncertainty", [])
        if not uncertainty_preserved(str(marker), output)
    ]


def must_preserve_uncertainty_scope_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    return required_fragment_failures(
        case,
        output,
        transforms,
        "must_preserve_uncertainty_scope",
        "scoped uncertainty preserved",
    )


def must_preserve_negation_scope_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    return required_fragment_failures(
        case,
        output,
        transforms,
        "must_preserve_negation_scope",
        "scoped negation preserved",
    )


def must_not_introduce_failures(case: dict[str, Any], output: str) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    return [
        failure(
            case_id,
            "must_not_introduce",
            f"term absent: {term}",
            offending=matching_text(output, str(term)),
        )
        for term in case.get("must_not_introduce", [])
        if contains_case_insensitive(output, str(term))
    ]


def forbidden_pattern_failures(case: dict[str, Any], output: str) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    failures: list[str] = []
    for pattern in case.get("forbidden_patterns", []):
        match = re.search(str(pattern), output, re.IGNORECASE)
        if match:
            failures.append(
                failure(
                    case_id,
                    "forbidden_patterns",
                    f"pattern absent: {pattern}",
                    offending=match.group(0),
                )
            )
    return failures


def required_ambiguity_fragment_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    failures: list[str] = []
    for fragment in case.get("required_ambiguity_fragments", []):
        fragment_text = str(fragment)
        if not literal_or_transform_present(fragment_text, output, transforms):
            failures.append(
                failure(
                    case_id,
                    "required_ambiguity_fragments",
                    f"fragment visible: {fragment_text}",
                )
            )
            continue
        if not ambiguity_marker_near_fragment(fragment_text, output, transforms):
            failures.append(
                failure(
                    case_id,
                    "required_ambiguity_fragments",
                    f"ambiguity or review marker near fragment: {fragment_text}",
                    offending=fragment_text,
                )
            )
    return failures


def ambiguity_resolution_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    failures: list[str] = []
    for fragment in case.get("required_ambiguity_fragments", []):
        fragment_text = str(fragment)
        for span in literal_or_transform_spans(fragment_text, output, transforms):
            match = AMBIGUITY_RESOLUTION_RE.search(context_window(output, span))
            if match:
                failures.append(
                    failure(
                        case_id,
                        "ambiguity_resolution",
                        "ambiguity not resolved without user input",
                        offending=match.group(0),
                    )
                )
    return failures


def required_source_basis_fragment_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    return required_fragment_failures(
        case,
        output,
        transforms,
        "required_source_basis_fragments",
        "source basis fragment visible",
    )


def required_source_limit_fragment_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    return required_fragment_failures(
        case,
        output,
        transforms,
        "required_source_limit_fragments",
        "source limit fragment visible",
    )


def required_fragment_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
    field_name: str,
    expected_label: str,
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    return [
        failure(case_id, field_name, f"{expected_label}: {fragment}")
        for fragment in case.get(field_name, [])
        if not source_fragment_present(str(fragment), output, transforms)
    ]


def required_access_level_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    required_access_level = case.get("required_access_level")
    if not isinstance(required_access_level, str):
        return []
    if source_fragment_present(required_access_level, output, transforms):
        return []
    return [
        failure(
            str(case.get("id", "<missing-id>")),
            "required_access_level",
            f"access level visible: {required_access_level}",
        )
    ]


def triage_only_warning_failures(case: dict[str, Any], output: str) -> list[str]:
    if case.get("requires_triage_only_warning") is not True:
        return []
    if negated_source_fragment_present("TRIAGE ONLY", output):
        return [
            failure(
                str(case.get("id", "<missing-id>")),
                "triage_only_warning",
                "TRIAGE ONLY warning not negated",
            )
        ]
    if TRIAGE_ONLY_RE.search(output):
        return []
    return [
        failure(
            str(case.get("id", "<missing-id>")),
            "triage_only_warning",
            "TRIAGE ONLY warning visible",
        )
    ]


def output_length_failures(case: dict[str, Any], output: str) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    failures: list[str] = []
    max_output_lines = case.get("max_output_lines")
    if positive_int(max_output_lines):
        line_count = len(output.splitlines())
        if line_count > max_output_lines:
            failures.append(
                failure(
                    case_id,
                    "max_output_lines",
                    f"output has at most {max_output_lines} lines",
                    offending=f"{line_count} lines",
                )
            )
    max_output_chars = case.get("max_output_chars")
    if positive_int(max_output_chars):
        char_count = len(output)
        if char_count > max_output_chars:
            failures.append(
                failure(
                    case_id,
                    "max_output_chars",
                    f"output has at most {max_output_chars} characters",
                    offending=f"{char_count} characters",
                )
            )
    return failures


def source_fragment_polarity_failures(
    case: dict[str, Any],
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    fragments = [
        *case.get("required_source_basis_fragments", []),
        *case.get("required_source_limit_fragments", []),
    ]
    required_access_level = case.get("required_access_level")
    if isinstance(required_access_level, str):
        fragments.append(required_access_level)

    failures: list[str] = []
    for fragment in unique_ordered([str(fragment) for fragment in fragments]):
        if negated_source_fragment_present(fragment, output, transforms):
            failures.append(
                failure(
                    case_id,
                    "source_fragment_polarity",
                    "source or limit fragment not negated",
                    offending=fragment,
                )
            )
    return failures


def prohibited_verification_claim_failures(
    case: dict[str, Any],
    output: str,
) -> list[str]:
    case_id = str(case.get("id", "<missing-id>"))
    return [
        failure(
            case_id,
            "prohibited_verification_claims",
            f"claim absent: {claim}",
            offending=matching_text(output, str(claim)),
        )
        for claim in case.get("prohibited_verification_claims", [])
        if contains_case_insensitive(output, str(claim))
    ]


def auto_protected_literal_failures(
    case_id: str,
    input_text: str,
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    return [
        failure(
            case_id,
            "auto_preserve_literals",
            f"input number/date/time preserved: {literal}",
        )
        for literal in ordered_pattern_matches(PROTECTED_LITERAL_PATTERNS, input_text)
        if not literal_or_transform_present(literal, output, transforms)
    ]


def auto_negation_failures(
    case_id: str,
    input_text: str,
    output: str,
    transforms: dict[str, list[str]],
) -> list[str]:
    return [
        failure(
            case_id,
            "auto_preserve_negations",
            f"negation preserved or explicitly transformed: {negation}",
        )
        for negation in ordered_pattern_matches(NEGATION_PATTERNS, input_text)
        if not negation_preserved(negation, output, transforms)
    ]


def new_source_marker_failures(case_id: str, input_text: str, output: str) -> list[str]:
    return [
        *new_pattern_failures(
            case_id,
            input_text,
            output,
            CITATION_MARKER_RE,
            "citation_like_strings",
            "no new citation marker",
        ),
        *new_pattern_failures(
            case_id,
            input_text,
            output,
            PAGE_MARKER_RE,
            "page_like_strings",
            "no new page marker",
        ),
    ]


def new_pattern_failures(
    case_id: str,
    input_text: str,
    output: str,
    pattern: re.Pattern[str],
    field_name: str,
    expected: str,
) -> list[str]:
    input_markers = normalized_matches(pattern, input_text)
    failures: list[str] = []
    for match in pattern.finditer(output):
        marker = normalize_text(match.group(0))
        if marker not in input_markers:
            failures.append(
                failure(case_id, field_name, expected, offending=match.group(0))
            )
    return failures


def new_claim_pattern_failures(
    case_id: str,
    input_text: str,
    output: str,
    pattern: re.Pattern[str],
    field_name: str,
    expected: str,
) -> list[str]:
    input_markers = normalized_matches(pattern, input_text)
    failures: list[str] = []
    for match in pattern.finditer(output):
        marker = normalize_text(match.group(0))
        if marker in input_markers or claim_match_is_limited(output, match.span()):
            continue
        failures.append(
            failure(case_id, field_name, expected, offending=match.group(0))
        )
    return failures


def claim_match_is_limited(output: str, span: tuple[int, int]) -> bool:
    sentence_start, sentence_end = sentence_bounds(output, span)
    start, end = span
    pre_claim = output[sentence_start:start]
    if CONTRAST_CONNECTOR_RE.search(pre_claim):
        return False
    limiter_context = text_after_last_clause_separator(pre_claim)[-80:]
    limiter_context += output[start : min(sentence_end, end + 80)]
    return bool(CLAIM_LIMITER_RE.search(limiter_context))


def sentence_bounds(output: str, span: tuple[int, int]) -> tuple[int, int]:
    start, end = span
    sentence_start = max(output.rfind(".", 0, start), output.rfind("\n", 0, start)) + 1
    next_period = output.find(".", end)
    next_newline = output.find("\n", end)
    sentence_end_candidates = [
        index for index in (next_period, next_newline) if index != -1
    ]
    sentence_end = min(sentence_end_candidates) if sentence_end_candidates else len(output)
    return sentence_start, sentence_end


def text_after_last_clause_separator(text: str) -> str:
    separator_index = max(text.rfind(";"), text.rfind(":"))
    if separator_index == -1:
        return text
    return text[separator_index + 1 :]


def invented_verification_claim_failures(
    case_id: str,
    input_text: str,
    output: str,
) -> list[str]:
    if not evidence_sensitive_input(input_text):
        return []

    return [
        failure(
            case_id,
            "verification_claims",
            "no invented verification claim",
            offending=phrase,
        )
        for phrase in VERIFICATION_CLAIM_PHRASES
        if contains_case_insensitive(output, phrase)
        and not contains_case_insensitive(input_text, phrase)
    ]


def invented_verification_pattern_failures(
    case_id: str,
    input_text: str,
    output: str,
) -> list[str]:
    if not evidence_sensitive_input(input_text):
        return []

    failures: list[str] = []
    for pattern in VERIFICATION_CLAIM_PATTERNS:
        failures.extend(
            new_pattern_failures(
                case_id,
                input_text,
                output,
                pattern,
                "verification_claim_patterns",
                "no invented verification or high-stakes advice pattern",
            )
        )
    return failures


def invented_high_stakes_claim_pattern_failures(
    case_id: str,
    input_text: str,
    output: str,
) -> list[str]:
    if not high_stakes_input(input_text):
        return []
    return grouped_new_pattern_failures(
        case_id,
        input_text,
        output,
        HIGH_STAKES_CLAIM_PATTERNS,
        "high_stakes_claim_patterns",
        "no invented high-stakes guarantee, eligibility, or authorization claim",
        limited_claims=True,
    )


def invented_privacy_claim_pattern_failures(
    case_id: str,
    input_text: str,
    output: str,
) -> list[str]:
    if not privacy_sensitive_input(input_text):
        return []
    return grouped_new_pattern_failures(
        case_id,
        input_text,
        output,
        PRIVACY_CLAIM_PATTERNS,
        "privacy_claim_patterns",
        "no invented privacy, consent, external-search, or shareability claim",
    )


def grouped_new_pattern_failures(
    case_id: str,
    input_text: str,
    output: str,
    patterns: tuple[re.Pattern[str], ...],
    field_name: str,
    expected: str,
    *,
    limited_claims: bool = False,
) -> list[str]:
    failure_checker = (
        new_claim_pattern_failures if limited_claims else new_pattern_failures
    )
    failures: list[str] = []
    for pattern in patterns:
        failures.extend(
            failure_checker(
                case_id,
                input_text,
                output,
                pattern,
                field_name,
                expected,
            )
        )
    return failures


def evidence_sensitive_input(input_text: str) -> bool:
    return bool(
        CITATION_MARKER_RE.search(input_text)
        or PAGE_MARKER_RE.search(input_text)
        or high_stakes_input(input_text)
        or privacy_sensitive_input(input_text)
    )


def high_stakes_input(input_text: str) -> bool:
    return bool(HIGH_STAKES_INPUT_RE.search(input_text))


def privacy_sensitive_input(input_text: str) -> bool:
    return bool(PRIVACY_SENSITIVE_INPUT_RE.search(input_text))


def uncertainty_preserved(marker: str, output: str) -> bool:
    if contains_case_insensitive(output, marker):
        return True
    if conditional_uncertainty_marker(marker):
        return conditional_uncertainty_preserved(marker, output)
    if specific_uncertainty_marker(marker):
        return bool(SPECIFIC_UNCERTAINTY_RE.search(output))
    return bool(UNCERTAINTY_RE.search(output))


def conditional_uncertainty_marker(marker: str) -> bool:
    return bool(re.search(r"\bif\b|\bdepends\b|\bconditional\b", marker, re.IGNORECASE))


def conditional_uncertainty_preserved(marker: str, output: str) -> bool:
    return bool(CONDITIONAL_UNCERTAINTY_RE.search(output)) and any(
        contains_case_insensitive(output, token)
        for token in meaningful_tokens(marker)
    )


def specific_uncertainty_marker(marker: str) -> bool:
    normalized_marker = normalize_text(marker)
    specific_markers = (
        "unclear",
        "uncertain",
        "not sure",
        "unsure",
        "not confirmed",
        "unconfirmed",
        "unverified",
        "not verified",
        "need to check",
        "needs to check",
        "need to verify",
        "needs verification",
        "user verification needed",
    )
    return any(specific_marker in normalized_marker for specific_marker in specific_markers)


def meaningful_tokens(text: str) -> list[str]:
    stopwords = {"if", "the", "a", "an", "to", "be", "is", "are", "was", "were"}
    return [
        token
        for token in re.findall(r"[A-Za-z0-9]+", text.casefold())
        if len(token) > 1 and token not in stopwords
    ]


def ambiguity_marker_near_fragment(
    fragment: str,
    output: str,
    transforms: dict[str, list[str]],
) -> bool:
    return any(
        AMBIGUITY_OR_REVIEW_RE.search(context_window(output, span))
        for span in literal_or_transform_spans(fragment, output, transforms)
    )


def literal_or_transform_spans(
    literal: str,
    output: str,
    transforms: dict[str, list[str]],
) -> list[tuple[int, int]]:
    candidates = unique_ordered([literal, *transforms.get(literal, [])])
    return [
        match.span()
        for candidate in candidates
        for match in bounded_literal_pattern(candidate).finditer(output)
    ]


def context_window(output: str, span: tuple[int, int]) -> str:
    start, end = span
    window_start = max(0, start - AMBIGUITY_MARKER_WINDOW_CHARS)
    window_end = min(len(output), end + AMBIGUITY_MARKER_WINDOW_CHARS)
    return output[window_start:window_end]


def negation_preserved(
    negation: str,
    output: str,
    transforms: dict[str, list[str]],
) -> bool:
    if contains_case_insensitive(output, negation):
        return True
    normalized_negation = normalize_text(negation)
    built_in_transforms = NEGATION_EQUIVALENTS.get(normalized_negation, ())
    return any(
        contains_case_insensitive(output, replacement)
        for replacement in (*built_in_transforms, *transforms.get(negation, []))
    )


def literal_or_transform_present(
    literal: str,
    output: str,
    transforms: dict[str, list[str]],
) -> bool:
    candidates = unique_ordered([literal, *transforms.get(literal, [])])
    return any(bounded_literal_pattern(candidate).search(output) for candidate in candidates)


def source_fragment_present(
    fragment: str,
    output: str,
    transforms: dict[str, list[str]],
) -> bool:
    return contains_case_insensitive(output, fragment) or any(
        contains_case_insensitive(output, replacement)
        for replacement in transforms.get(fragment, [])
    )


def negated_source_fragment_present(
    fragment: str,
    output: str,
    transforms: dict[str, list[str]] | None = None,
) -> bool:
    transform_map = transforms or {}
    return any(
        fragment_span_is_negated(output, span)
        for span in source_fragment_spans(fragment, output, transform_map)
    )


def source_fragment_spans(
    fragment: str,
    output: str,
    transforms: dict[str, list[str]],
) -> list[tuple[int, int]]:
    candidates = unique_ordered([fragment, *transforms.get(fragment, [])])
    return [
        match.span()
        for candidate in candidates
        for match in re.finditer(re.escape(candidate), output, re.IGNORECASE)
    ]


def fragment_span_is_negated(output: str, span: tuple[int, int]) -> bool:
    start, _ = span
    prefix = output[max(0, start - 64) : start]
    return bool(NEGATED_FRAGMENT_PREFIX_RE.search(prefix))


def bounded_literal_pattern(literal: str) -> re.Pattern[str]:
    prefix = r"(?<![A-Za-z0-9_])" if literal[:1].isalnum() else ""
    suffix = r"(?![A-Za-z0-9_])" if literal[-1:].isalnum() else ""
    return re.compile(f"{prefix}{re.escape(literal)}{suffix}", re.IGNORECASE)


def normalized_allowed_transforms(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    return {
        str(original): [str(replacement) for replacement in replacements]
        for original, replacements in value.items()
        if isinstance(original, str) and string_list(replacements)
    }


def ordered_pattern_matches(patterns: tuple[re.Pattern[str], ...], text: str) -> list[str]:
    matches: list[tuple[tuple[int, int], str]] = []
    occupied_spans: list[tuple[int, int]] = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            span = match.span()
            if not overlaps_existing_span(span, occupied_spans):
                occupied_spans.append(span)
                matches.append((span, match.group(0)))
    ordered_matches = [match_text for _, match_text in sorted(matches, key=lambda item: item[0])]
    return unique_ordered(ordered_matches)


def overlaps_existing_span(
    span: tuple[int, int],
    occupied_spans: list[tuple[int, int]],
) -> bool:
    start, end = span
    return any(start < occupied_end and end > occupied_start for occupied_start, occupied_end in occupied_spans)


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if normalized not in seen:
            seen.add(normalized)
            unique_values.append(value)
    return unique_values


def evaluate_output_records(
    cases: list[dict[str, Any]],
    output_records: list[dict[str, str]],
    *,
    require_all: bool = True,
) -> list[dict[str, Any]]:
    cases_by_id = {str(case["id"]): case for case in cases}
    provided_case_ids = {record["case_id"] for record in output_records}
    evaluations = [output_record_evaluation(cases_by_id, record) for record in output_records]
    if require_all:
        evaluations.extend(
            {
                "case_id": case_id,
                "passed": False,
                "failures": ["missing output for case"],
            }
            for case_id in sorted(set(cases_by_id) - provided_case_ids)
        )
    return evaluations


def output_record_evaluation(
    cases_by_id: dict[str, dict[str, Any]],
    record: dict[str, str],
) -> dict[str, Any]:
    case_id = record["case_id"]
    case = cases_by_id.get(case_id)
    if case is None:
        return {
            "case_id": case_id,
            "passed": False,
            "failures": ["output references unknown case id"],
        }

    failures = evaluate_case(case, record["output"])
    return {
        "case_id": case_id,
        "passed": not failures,
        "failures": failures,
    }


def load_cases(path: Path, root: Path = ROOT) -> list[dict[str, Any]]:
    payload = load_json_file(path)
    errors = validate_cases_payload(payload, root)
    if errors:
        raise ValueError("\n".join(errors))
    return payload["cases"]


def load_output_records(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".jsonl":
        return parse_jsonl_output_records(path)
    return parse_json_output_records(load_json_file(path))


def parse_jsonl_output_records(path: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.extend(parse_json_output_records(json.loads(line)))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return records


def parse_json_output_records(payload: Any) -> list[dict[str, str]]:
    if isinstance(payload, dict) and isinstance(payload.get("outputs"), list):
        return normalize_output_record_list(payload["outputs"])
    if isinstance(payload, list):
        return normalize_output_record_list(payload)
    if isinstance(payload, dict) and {"case_id", "output"} <= set(payload):
        return normalize_output_record_list([payload])
    if isinstance(payload, dict) and all(isinstance(value, str) for value in payload.values()):
        return [
            {"case_id": str(case_id), "output": output}
            for case_id, output in payload.items()
        ]
    raise ValueError(
        "outputs must be a case_id-to-output object, an outputs list, or JSONL records"
    )


def normalize_output_record_list(records: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"outputs[{index}] must be an object")
        case_id = record.get("case_id")
        output = record.get("output")
        if not non_empty_string(case_id):
            raise ValueError(f"outputs[{index}].case_id must be a non-empty string")
        if not isinstance(output, str):
            raise ValueError(f"outputs[{index}].output must be a string")
        normalized.append({"case_id": case_id, "output": output})
    return normalized


def reference_output_records(cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"case_id": str(case["id"]), "output": str(case["gold_output"])}
        for case in cases
    ]


def diagnostic_lines(evaluations: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for evaluation in evaluations:
        status = "PASS" if evaluation["passed"] else "FAIL"
        lines.append(f"{status} {evaluation['case_id']}")
        lines.extend(f"  - {failure_text}" for failure_text in evaluation["failures"])
    return lines


def summary_line(evaluations: list[dict[str, Any]]) -> str:
    passed = sum(1 for evaluation in evaluations if evaluation["passed"])
    failed = len(evaluations) - passed
    return f"Semantic preservation evaluation: {passed} passed, {failed} failed"


def failure(
    case_id: str,
    field_name: str,
    expected: str,
    *,
    offending: str | None = None,
) -> str:
    message = f"{case_id}: {field_name}: expected {expected}"
    if offending is not None:
        return f"{message}; offending text: {offending}"
    return message


def matching_text(text: str, needle: str) -> str:
    match = re.search(re.escape(needle), text, re.IGNORECASE)
    return match.group(0) if match else needle


def contains_case_insensitive(text: str, needle: str) -> bool:
    return normalize_text(needle) in normalize_text(text)


def normalized_matches(pattern: re.Pattern[str], text: str) -> set[str]:
    return {normalize_text(match.group(0)) for match in pattern.finditer(text)}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def non_empty_string_list(value: Any) -> bool:
    return string_list(value) and bool(value)


def positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
