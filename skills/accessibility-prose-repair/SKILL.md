---
name: accessibility-prose-repair
description: Use when existing prose needs meaning-preserving spelling, grammar, punctuation, sentence-boundary, paragraph-break, typo, or local readability repair for dyslexic, dysorthographic, low-load, or accessibility-focused writing support.
license: MIT
metadata:
  version: "1.1.0"
  category: accessible-writing-support
---
# Accessible prose repair

## Purpose

Make existing prose easier to read, review, and use without changing the user's meaning.

This skill focuses on meaning-preserving repair: spelling, grammar, punctuation, sentence boundaries, paragraph breaks, and local readability. It keeps uncertainty, responsibility, evidence limits, and user intent visible.

## When to use

Use when the user provides an existing paragraph, email, message, form response, note, draft, abstract, proposal passage, chapter excerpt, or other prose and asks for spelling repair, grammar cleanup, sentence repair, dyslexia-friendly editing, dysorthographic cleanup, or a meaning-preserving edit.

Use this instead of `accessibility-dictation-notes` when the input is already prose. Use `accessibility-low-load-companion` when prose repair is mixed with dictation, reading load, or unclear next-step friction.

## Automatic selection guidance

- High-signal triggers: spelling repair, grammar cleanup, dyslexia-friendly edit, dysorthographic edit, sentence boundaries, punctuation repair, paragraph breaks, typo-heavy prose, meaning-preserving edit, or correction log.
- Light-route behavior: revise only the supplied prose, preserve meaning, and provide a brief change summary only when useful.
- Escalation gate: add verification, evidence, privacy, or expert-review limits when the prose includes factual claims, citations, quotes, policy obligations, legal/medical/financial claims, publication, external sharing, or commitments.
- Noise and slowdown guard: do not turn surface repair into style rewriting, argument restructuring, research synthesis, or advice beyond the user's request.

## Do not use this skill when

- The user provides voice notes or fragments that are not yet prose; use `accessibility-dictation-notes`.
- The user needs dense document triage; use `accessibility-reading-load-reducer`.
- The user needs broad accessibility routing across several bottlenecks; use `accessibility-low-load-companion`.
- The user asks for a persuasive rewrite, content strategy, legal advice, medical advice, financial advice, or fact verification; state limits or route appropriately.

## Inputs expected

- Existing prose passage, message, email, note, form response, draft paragraph, proposal section, or chapter excerpt.
- Desired repair level: Level 1 / minimal correction, Level 2 / local clarity, or Level 3 / rewrite.
- Terms, names, quotes, technical phrases, numbers, obligations, and claims that must not change.
- Optional source basis if claims or citations should be flagged.

## Source basis and limits

Use `docs/SOURCE_LIMITS.md` for verification and source-access rules when the prose includes factual claims, citations, current facts, external-sharing stakes, legal/medical/financial details, or source support.

Treat spelling and grammar cleanup as surface repair. If a correction could change meaning, keep the original wording visible and mark the ambiguity.

## Compact output

Use compact output by default for low-risk prose repair, minimal correction, or fast prose cleanup. Compact output should provide the revised passage, one source-basis line when relevant, uncertainty and ambiguity only if meaning could change, privacy or verification limits when relevant, changed phrases only when review is needed, and one useful next action only when it reduces friction.

Compact repair must keep caveats that affect claim strength, consent, responsibility, obligations, AI involvement, source support, currentness, venue policy, publication or release status, and privacy. Shorter output must not make an uncertain or unsupported claim look settled.

## Files/folders it may read

- Shared operational boundary doc: `docs/SKILL_OPERATIONAL_BOUNDARIES.md`.
- Shared policy docs: `docs/SOURCE_LIMITS.md`, `docs/AUTO_SELECTION_GUARDRAILS.md`, `docs/ROUTING_MATRIX.md`, and `docs/SKILL_INDEX.md`.
- User-provided passages, drafts, documents, style constraints, citation notes, or artifacts explicitly named in the request.

## Files/folders it may write

- None by default.
- May create or update user-requested revised passages, correction notes, or edit logs in the user-designated workspace.
- Must not overwrite original manuscripts, notes, drafts, source files, or private files unless the user explicitly asks.

## What it must not do

- Do not change the user's meaning to make prose smoother.
- Do not erase uncertainty, qualifiers, commitments, consent language, or evidence limits.
- Do not silently "fix" names, terms, citations, quotes, numbers, dates, diagnoses, policy language, or technical language when uncertain.
- Do not add facts, examples, citations, promises, obligations, or source claims.
- If the user request contains a false premise, do not smooth it into better prose; preserve or flag the unsupported premise and provide the strongest supportable wording.
- Do not conceal AI involvement. Venue policy is unverified unless the policy text is provided or a permitted lookup checks it.
- Do not shame or foreground the user's spelling difficulty.

## Procedure

### 1. Select repair level

Default to Level 1 unless the user asks for stronger editing:

- Level 1 / minimal correction: spelling, punctuation, grammar, and sentence boundaries only; no tone/style/claim-strength changes.
- Level 2 / local clarity: only when the user asks for local clarity, clearer sentence flow, or light restructuring. It adds light sentence-local restructuring only when meaning is clear.
- Level 3 / rewrite: only when explicitly requested. It may adapt tone/audience/structure, but it must still preserve facts, uncertainty, limits, and source boundaries.

### 2. Protect meaning

Identify terms, claims, quotes, citations, names, numbers, dates, commitments, diagnoses, policy phrases, and qualifiers that must remain stable.

If a correction may change meaning, keep it in the ambiguity table rather than silently editing.

### 3. Repair the prose

Fix spelling, grammar, punctuation, sentence boundaries, paragraph breaks, and local readability. Keep the user's voice where possible.

Do not add new factual claims or commitments. If a repair requires adding explanation, label it as optional.

### 4. Summarize changes compactly

Report only what helps the user review the edit:

- meaning preserved
- new factual claims introduced
- ambiguous corrections
- changed phrases that deserve quick user review
- claims or commitments needing verification

### 5. Route only when needed

If the repaired prose reveals a concrete next-step risk, suggest one skill:

- rough idea structure still unclear: `accessibility-dictation-notes` or `accessibility-low-load-companion`
- dense material needs triage before editing: `accessibility-reading-load-reducer`

For source, legal, medical, financial, or publication verification, state the need for appropriate source access or expert review instead of pretending the edit verifies the content.

For AI disclosure, authorship, source-support, currentness, causal, statistical, venue-policy, or method claims, preserve the visible uncertainty unless the user provides verification and explicitly asks for stronger wording. AI involvement must not be concealed, and venue policy remains unverified without policy text or lookup.

## Output format

Default compact output:

```markdown
# Prose repair

Source basis: [one line when relevant]
Repair level: Level 1 / minimal correction unless the user requested more

[Revised passage]

Review note: [uncertainty, ambiguity, privacy, or verification limit only if it could change meaning or risk]
Next action: [one useful next action only when it reduces friction]
```

Expanded output:

Use expanded output when the task is high-stakes, evidence-sensitive, public-facing, workplace-sensitive, legal/medical/financial, publication-related, source-sensitive, or when the user asks for a fuller edit log.

```markdown
# Prose repair

## Source basis

## Repair level

## Revised passage

## Meaning preserved

## New factual claims introduced

## Changed phrases to review
| Original | Revised | Why changed | User check needed |

## Ambiguous corrections
| Original | Possible correction | Why it matters | User check |

## Claims or commitments needing verification

## What I can verify

## What remains uncertain

## User verification needed
```
