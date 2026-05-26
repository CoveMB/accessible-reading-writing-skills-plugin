# Semantic preservation testing

This repository has a deterministic semantic-preservation regression layer for
the accessibility skills. It is designed to catch common meaning-changing
deformations in skill instructions, fixtures, and future output samples.

These tests are guardrails. They do not prove that meaning, intent, voice, or
"essence" is always preserved. They check specific documented invariants that
can be evaluated without model calls, external services, or private data.
This layer reduces known risks in sampled cases, but it does not guarantee
perfect preservation of essence/meaning.

## How to run

Run the normal unittest discovery command:

```bash
python3 -m unittest discover -s tests
```

Run the full package check used by CI:

```bash
python3 scripts/run_package_checks.py --scope full
```

The full check runs plugin validation and unittest discovery. `./validate.sh`
is a shell wrapper for the same full package check. CI uses the same full
package check from `.github/workflows/skill-tests.yml`, so semantic tests do
not need a separate CI command.

To evaluate an outputs file against the same fixture cases:

```bash
python3 scripts/evaluate_semantic_preservation.py --cases tests/fixtures/semantic_preservation_cases.json --outputs path/to/outputs.json
```

Use `--allow-missing` when the outputs file intentionally covers only a subset
of cases. If `--outputs` is omitted, the evaluator checks the fixture
`gold_output` values.

## Test layers

Instruction-contract tests live in `tests/test_skill_instruction_contracts.py`.
They verify that skill instructions and shared docs still contain required
safety contracts such as meaning preservation, visible uncertainty, source
limits, privacy limits, and no invented facts. They test the written
instructions, not model behavior.

Deterministic invariant tests live in
`tests/test_semantic_preservation_contracts.py` and use
`tests/fixtures/semantic_preservation_cases.json`. They evaluate fixture
outputs and candidate outputs with deterministic rules from
`scripts/semantic_preservation.py`. These rules check preserved literals,
uncertainty markers, scoped negation phrases, ambiguity notes, source-limit
wording, negations, numbers, dates, times, citation-like strings,
page-like strings, and forbidden additions.
Literal checks use boundary-aware matching so a protected value such as `1450`
does not pass merely because it appears inside a changed value such as
`11450`.

Future real-output behavioral tests can reuse the same fixtures by collecting
actual model or skill outputs into a JSON or JSONL file and running
`scripts/evaluate_semantic_preservation.py`. Those results are behavioral
evidence for the sampled outputs only; they are not a general guarantee about
all future outputs.

Human or user review is still required when wording changes could affect
identity, consent, privacy, citation support, source interpretation,
publication, external sharing, workplace decisions, or legal, medical, or
financial outcomes. The tests make some risks visible, but they cannot decide
all context-sensitive meaning questions.

## What the tests check

The fixture cases focus on high-risk deformations, including:

- uncertainty changed into certainty
- maybe changed into a promise
- negation dropped or reversed
- numbers, dates, times, or money amounts changed
- names, terms, or citations silently corrected
- source access overstated
- legal, medical, or financial advice invented
- privacy risk hidden or made shareable
- title-only, citation-only, snippet-only, abstract-only, or headings-only
  source access treated as verified evidence

The invariant checker is intentionally conservative and literal. It is useful
for regression testing, but it cannot understand every paraphrase, intent
boundary, synonym, or context-specific risk.

## What the tests do not prove

The suite does not prove that an output preserves all meaning. It does not
prove that a future model will follow the instructions. It does not verify
facts, citations, source support, page numbers, laws, medical guidance,
financial facts, privacy permissions, or current information. It also does not
replace human review for high-stakes or ambiguous text.

A passing result means the checked output satisfied the explicit deterministic
contracts for the fixture cases. It does not mean the output is complete,
correct, safe to publish, safe to share externally, or safe to rely on for
legal, medical, financial, workplace, research, or citation decisions.

## Fixture cases

Fixture cases are stored in
`tests/fixtures/semantic_preservation_cases.json`.

Each case contains:

- `id`: stable lowercase case id ending in a three-digit number.
- `skill`: skill folder the case belongs to.
- `risk_type`: list of risk labels for the deformation being guarded.
- `input`: source text or user request fragment.
- `gold_output`: reference output that must satisfy the invariants.
- `must_preserve_literals`: exact text that must remain visible unless an
  explicit allowed transform is provided.
- `must_preserve_uncertainty`: uncertainty markers that must remain visible or
  be represented by uncertainty language.
- `must_preserve_uncertainty_scope`: exact uncertainty-bearing claim, condition,
  or tentative action that must remain visible when a loose uncertainty marker
  elsewhere would be too weak.
- `must_preserve_negation_scope`: exact negated claim or permission boundary
  that must remain visible when keeping a loose `not` somewhere else would be
  too weak.
- `must_not_introduce`: terms or claims that must not appear in the output.
- `must_not_introduce_unless_limited`: terms or claims that must not appear as
  unsupported claims, but may appear in clear limiting or negating disclaimers.
- `required_ambiguity_fragments`: true ambiguity fragments where choosing one
  possible name, word, source, speaker, or context would change meaning; these
  must stay visible with a nearby ambiguity or review marker.
- `forbidden_patterns`: regular expressions for prohibited output patterns.
- `allowed_transforms`: optional map from a source literal to acceptable
  replacements, such as `cant promise` to `can't promise`.
- `required_source_basis_fragments`: source-basis wording that must appear for
  source-sensitive reading cases.
- `required_source_limit_fragments`: source-limit wording that must appear for
  source-sensitive reading cases.
- `required_access_level`: access-level wording that must remain visible.
- `prohibited_verification_claims`: explicit claims that must not be introduced.
- `requires_triage_only_warning`: boolean requiring visible `TRIAGE ONLY`
  wording.
- `max_output_lines` / `max_output_chars`: optional compactness limits for
  cases where low-load brevity is part of the safety contract.
- `notes`: short human explanation of the case risk.

## Risk-label schema requirements

`risk_type` labels are not just descriptive tags. Some labels require stronger
invariants so future cases cannot pass schema validation with only loose
keyword preservation.

Negation, permission, privacy, consent, disclosure, and sharing labels require a
strong boundary guard. For labels containing `negation`, use
`must_preserve_negation_scope`, such as `do not share Morgan's diagnosis with
the team` or `not authorized payroll to share my address`. For related
permission or privacy labels, use a scoped negation guard when there is one, or
use targeted `must_not_introduce` / `forbidden_patterns` entries such as
`diagnosis can be shared`, `permission confirmed`, or `safe to paste`.

Uncertainty, commitment, and conditional labels require
`must_preserve_uncertainty` plus at least one scoped or claim-level guard:
`must_preserve_uncertainty_scope`, `forbidden_patterns`, or
`must_not_introduce`. For example, `uncertainty_erasure` should protect a claim
like `policy might be old`, not just preserve an unrelated `maybe` elsewhere.
For `commitment_inflation` or other commitment labels, include a targeted
commitment guard such as `I will attend`, `promise to reply`,
`meeting is confirmed`, or `refund approved`.

Source, verification, and citation labels require a source or verification
guard: `required_source_basis_fragments`, `required_source_limit_fragments`,
`prohibited_verification_claims`, or `forbidden_patterns`. For example,
`source_overclaim`, `title_only_access`, `snippet_only_access`,
`abstract_only_access`, `headings_only_access`, and `citation_only_access`
should keep visible what material was available or block claims such as
`full text confirms` and `source verifies`.

Medical, legal, financial, insurance, and tax labels require at least one
targeted overclaim guard: `must_not_introduce`,
`must_not_introduce_unless_limited`, `prohibited_verification_claims`, or
`forbidden_patterns`. Good examples include `you should stop meds`,
`legal advice`, `coverage guaranteed`, `eligible for refund`, or
`tax credit confirmed`.

For `accessibility-reading-load-reducer`, keep the stronger reading-load rule:
source-sensitive cases require source basis, source limit, access level, and a
triage-only warning. The general source-risk rule does not replace that
stronger contract.

## Adding a new case

1. Add one focused object to `tests/fixtures/semantic_preservation_cases.json`.
2. Use a stable `id` like `prose_negation_loss_010`; do not reuse ids.
3. Set `skill` to an existing folder in `skills/`.
4. Keep the `input` small enough that the risk is easy to inspect.
5. Write `gold_output` as the desired safe shape, not as a model transcript.
6. Add only invariants that matter for the risk. Prefer targeted guards over
   broad lists.
7. Use `allowed_transforms` only for meaning-preserving surface repairs that
   should be accepted.
8. Add `required_ambiguity_fragments` only when a phrase should stay visible
   because choosing between possible interpretations would change meaning.
   Examples: `Anne or Ann`, `affect/effect`, `Morgan or Megan`, `meat meet`,
   unclear pronoun references, or unclear speaker/source identity.
9. Do not use `required_ambiguity_fragments` as a generic review-note or
   make-this-visible field. Put tentative claims in
   `must_preserve_uncertainty_scope`, permission/privacy/refusal boundaries in
   `must_preserve_negation_scope`, source access limits in
   `required_source_basis_fragments` or `required_source_limit_fragments`, and
   plain protected terms in `must_preserve_literals`.
10. For source-sensitive cases, add source-basis, source-limit, access-level,
   and triage-only fields when relevant.
11. Run `python3 -m unittest discover -s tests`.

If a new case needs a new deterministic invariant, add a failing test in
`tests/test_semantic_preservation_contracts.py` first, then update
`scripts/semantic_preservation.py`.

## Invariant meanings

`must_preserve_literals` protects names, terms, citations, source labels, and
other user-provided wording that should not be silently corrected or replaced.
Use `allowed_transforms` for explicit safe changes.

`must_preserve_uncertainty` protects words such as maybe, might, not sure,
unclear, tentative, conditional, and unverified. The checker accepts either the
specific marker or other visible uncertainty language in the output. Specific
markers such as `unclear`, `not sure`, and `unverified` require a closer
uncertainty equivalent; an unrelated `maybe` elsewhere is not enough.

`must_preserve_uncertainty_scope` protects the clause governed by uncertainty,
such as `policy might be old`, `cannot attend unless the appointment is moved`,
or `not checked the policy`. Use it when preserving a generic `maybe`, `might`,
or `unclear` somewhere else would allow the important claim to become certain.
Use `allowed_transforms` only for explicit, meaning-preserving rewrites of that
same scoped uncertainty.

`must_preserve_negation_scope` protects the negated claim, permission boundary,
or refusal when a generic negation check would be too weak. Use it for wording
such as `do not share Morgan's diagnosis with the team` or `not authorized
payroll to share my address`, where moving `not` onto another clause could
reverse privacy, consent, legal, or financial meaning. Fixture cases with a
negation-related `risk_type` must include a scoped negation guard so they do
not pass merely because some unrelated `not` remains visible.

`must_not_introduce` blocks high-risk words, claims, commitments, advice, or
facts that were not present in the input. It is strict: if the term appears, the
check fails even when the surrounding sentence negates or limits the term. Use
it for concrete invented claims such as `refund approved`, `policy confirms`,
`you should stop meds`, or `safe to share`.

`must_not_introduce_unless_limited` blocks the same kind of risk only when the
term is introduced as an unsupported claim. It allows the term when the nearby
sentence or clause clearly limits or negates it, such as `not legal advice`,
`not medical advice`, `not financial advice`, `do not treat this as legal
advice`, `this does not confirm coverage`, or `not verified source support`.
Use it for broad disclaimer-like phrases where the safe output may need to name
the risk in order to limit it. Do not use it for concrete claim bans that should
fail whenever present.

`required_ambiguity_fragments` requires truly ambiguous wording from the input
to remain visible and accompanied nearby by ambiguity, review, verification,
question, or source-basis language. Use this when the safe behavior is to mark
an unresolved choice instead of choosing an interpretation, such as uncertain
names, homophones, ambiguous typo corrections, pronoun references, context
alternatives, noisy phrases with multiple plausible readings, or unclear
speaker/source identity.
The checker also rejects known resolution phrases near these fragments, such as
claims that the ambiguity is resolved or that one spelling/name/meaning is
correct, because that can falsely pass as a review note while still guessing.
Do not use this field for ordinary status, uncertainty, negation, privacy, or
source-limit visibility. For example, `clinic paper is not back`, `do not share
diagnosis`, `policy has not been checked`, `title-only access`, and `source
support remains unverified` need preservation, but they are not by themselves
ambiguity fragments.

`forbidden_patterns` blocks regular-expression patterns that would indicate a
known unsafe deformation, such as a tentative plan turned into a confirmed one.

`allowed_transforms` documents intentional surface edits that preserve meaning.
Use it narrowly. It should not hide a real decision, guess, or correction.

`required_source_basis_fragments` requires the output to state what material was
available, such as title-only, citation-only, snippet-only, abstract-only,
headings-only, or user-provided full text.

`required_source_limit_fragments` requires the output to keep limits visible,
such as unverified support, triage-only use, missing full text, or need for user
verification.
Required source and limit fragments must not appear only in negated form, such
as `not TRIAGE ONLY` or `not title/citation/metadata only`.

`required_access_level` requires a specific access-level phrase to appear.

`prohibited_verification_claims` blocks case-specific unsupported claims that
the source, full text, policy, article, or citation verifies something.

`requires_triage_only_warning` requires visible `TRIAGE ONLY` wording when an
output could otherwise be mistaken for verified synthesis or advice.
The warning must be affirmative; negated warning text does not satisfy the
contract.

`max_output_lines` and `max_output_chars` protect low-load cases where a verbose
answer can hide the risk even if the key words remain present. Use these fields
sparingly for compact-output fixtures, not as a general style preference.

The checker also automatically guards numbers, dates, times, money amounts,
negations, citation-like strings, page-like strings, and a fixed set of known
verification/advice, high-stakes guarantee, eligibility, authorization,
privacy, external-search, consent, and shareability claim phrases and patterns
for evidence-sensitive or privacy-sensitive inputs. Those phrase and pattern
checks reduce common overclaim risks; they are not an exhaustive synonym
detector and do not prove that every unsafe wording will be caught.

## Ambiguity markers

Use ambiguity markers when a cleanup, summary, triage decision, or note could
change meaning if the system guesses between possible meanings. Good markers
name the exact fragment and the decision the user or reviewer must make.

Use ambiguity markers for cases such as uncertain names, homophones, noisy
dictation with multiple plausible readings, ambiguous typo corrections, unclear
pronoun references, context alternatives, and unclear speaker/source
attribution.

Do not use ambiguity markers as filler or as a generic review-note requirement.
Tentative commitments belong in `must_preserve_uncertainty_scope`; negated
statuses, refusals, consent limits, and privacy boundaries belong in
`must_preserve_negation_scope`; title-only, citation-only, snippet-only,
abstract-only, and headings-only access limits belong in source-basis and
source-limit fields. If the output can preserve meaning without a visible
`Ambiguity:` label, the case should not use `required_ambiguity_fragments`.

## No LLM or API calls in CI

CI runs without external services. The semantic layer is deterministic so it
can run quickly, privately, and reproducibly in pull requests and local package
checks. This avoids leaking private fixture-like material, depending on model
availability, or turning network/API issues into package failures.

Actual model outputs can still be evaluated later by saving them locally as
JSON or JSONL records and running the optional evaluator. Keep those generated
outputs out of CI unless there is an explicit, privacy-reviewed reason to add
them.

Accepted output file shapes include:

```json
{
  "outputs": [
    {
      "case_id": "prose_uncertainty_commitment_001",
      "output": "candidate output text"
    }
  ]
}
```

or a case-id-to-output object:

```json
{
  "prose_uncertainty_commitment_001": "candidate output text"
}
```

JSONL files may contain one output record per line with `case_id` and `output`.
