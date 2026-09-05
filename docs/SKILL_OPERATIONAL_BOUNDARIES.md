# Skill operational boundaries

This file is the shared operating policy for the skills. Individual READMEs should keep only skill-specific purpose, inputs, examples, output expectations, and best next steps.

Apply `docs/SOURCE_LIMITS.md` as a prerequisite. It owns source access,
verification, privacy, consent, external-tool payloads, source-contained
instructions, currentness and source-status limits, and legal, medical,
financial, or other high-stakes reliance boundaries.

## Procedure

1. Follow the skill's `SKILL.md` procedure instead of working from memory.
2. Preserve the user's meaning. Mark ambiguity instead of guessing when a correction could change meaning.
3. Keep qualifiers and negations attached to the same subject, action, and object. A disclaimer or uncertainty marker elsewhere does not preserve scope or polarity.
4. If a request contains a false premise, state the premise gap and give the strongest supportable wording or next action instead of smoothing the premise into the result.
5. Use the smallest clear accessibility skill first; use `accessibility-low-load-companion` only for mixed or unclear bottlenecks when no smaller/specialist skill clearly owns the task.
6. For compact output, use one source-basis line when relevant, one table or revised passage, ambiguity only when it could change meaning, privacy or verification limits when relevant, and one useful next action only when it reduces friction. Compact output must not remove decision-changing caveats.
7. Escalate from compact output before relying on the result for publication, external sharing, legal/medical/financial decisions, workplace obligations, citation verification, or research claims.

## Quality checks

- Meaning must be preserved.
- Uncertainty and decision-changing caveats must be visible when they matter.
- Output should reduce reading load without hiding risk.
- Marker-only compliance is not enough. Required headings with empty or generic substance still fail when blockers, source basis, uncertainty, privacy limits, or next actions are missing.
- Do not shame, diagnose, or over-focus on the user's spelling or reading difficulty.

## Failure modes

- Overcorrected text that changes the user's intended meaning.
- Long prose that defeats the low-load goal.
- Style polish that hides uncertainty, obligations, or other decision-changing caveats.
- False premise smoothing that turns an unsupported premise into clean wording.
- Marker-only output that includes headings but hides missing substance.

## Files/folders it may read

- Bundled skill instructions, metadata, and assets if available, including `SKILL.md`, `README.md`, `assets/`, `references/`, and `agents/openai.yaml`.
- User-provided drafts, notes, transcripts, documents, sources, artifacts, or project files explicitly named in the request.
- Shared project documentation when it is needed for workflow, quality, or artifact compatibility.

## Agent policy metadata

Shared policy values are defined in `scripts/plugin_utils.py`. Each committed `agents/openai.yaml` policy block must match them; `scripts/validate_plugin.py` checks this but does not generate or rewrite the file.

Allowed `external_lookup_allowed` values are `conditional`, `route-only`, and `none`.

- `external_lookup_allowed: conditional` means the skill may perform lookup only when its gate, source limits, tool availability, and user consent allow it.
- `external_lookup_allowed: route-only` means the skill may route to a lookup-capable skill, but should not perform external lookup itself.
- `external_lookup_allowed: none` means the skill should not use external lookup unless the user explicitly switches to an appropriate lookup-capable skill.

## Files/folders it may write

- None by default.
- May create or update user-requested notes, drafts, reading plans, repair logs, or action tables in the user-designated project or workspace.
- Must not overwrite source material, original notes, transcripts, drafts, or private files without explicit user request.

## What it must not do

- Use style polish to mask uncertainty or risk.
