# Skill operational boundaries

This file is the shared operating policy for skill READMEs. Individual READMEs should keep only skill-specific purpose, inputs, examples, output expectations, and best next steps.

## Procedure

1. State the source basis when the task depends on provided material or facts.
2. Follow the skill's `SKILL.md` procedure instead of working from memory.
3. Keep visible facts, interpretation, uncertainty, and recommendation separate when the task is factual or decision-sensitive.
4. Preserve the user's meaning. Mark ambiguity instead of guessing when a correction could change meaning.
5. Use the smallest clear accessibility skill first; use `accessibility-low-load-companion` only for mixed or unclear bottlenecks when no smaller/specialist skill clearly owns the task.
6. For compact output, use one source-basis line when relevant, one table or revised passage, ambiguity only when it could change meaning, privacy or verification limits when relevant, and one useful next action only when it reduces friction.
7. Escalate from compact output before relying on the result for publication, external sharing, legal/medical/financial decisions, workplace obligations, citation verification, or research claims.

## Quality checks

- Meaning must be preserved.
- Missing source access must be marked clearly for factual or evidence-sensitive tasks.
- Uncertainty, privacy limits, and user verification needs must be visible when they matter.
- Output should reduce reading load without hiding risk.
- Do not shame, diagnose, or over-focus on the user's spelling or reading difficulty.

## Failure modes

- Overcorrected text that changes the user's intended meaning.
- Long prose that defeats the low-load goal.
- Fabricated citations, quotes, page numbers, policies, laws, medical guidance, financial facts, source metadata, or verification.
- Confident synthesis from partial or private material.
- Style polish that hides weak evidence, uncertainty, consent issues, or obligations.

## Files/folders it may read

- Bundled skill instructions, metadata, and assets if available, including `SKILL.md`, `README.md`, `assets/`, `references/`, and `agents/openai.yaml`.
- User-provided drafts, notes, transcripts, documents, sources, artifacts, or project files explicitly named in the request.
- Shared project documentation when it is needed for workflow, quality, or artifact compatibility.

## Agent policy metadata

Each `agents/openai.yaml` policy block is generated from shared validator policy, not hand-maintained prose.

Allowed `external_lookup_allowed` values are `conditional`, `route-only`, and `none`.

- `external_lookup_allowed: conditional` means the skill may perform lookup only when its gate, source limits, tool availability, and user consent allow it.
- `external_lookup_allowed: route-only` means the skill may route to a lookup-capable skill, but should not perform external lookup itself.
- `external_lookup_allowed: none` means the skill should not use external lookup unless the user explicitly switches to an appropriate lookup-capable skill.

## Files/folders it may write

- None by default.
- May create or update user-requested notes, drafts, reading plans, repair logs, or action tables in the user-designated project or workspace.
- Must not overwrite source material, original notes, transcripts, drafts, or private files without explicit user request.

## What it must not do

- Invent missing facts or verification.
- Treat unavailable evidence as confirmed.
- Use style polish to mask uncertainty or risk.
- Submit private material to external tools without user consent.
