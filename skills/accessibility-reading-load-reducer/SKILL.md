---
name: accessibility-reading-load-reducer
description: Use when dense documents, long emails, instructions, policies, articles, source packets, reading lists, or long notes need low-load read-skim-park-skip triage, close-reading targets, extraction priorities, uncertainty labels, and next actions.
license: MIT
metadata:
  version: "1.0.0"
  category: accessible-writing-support
---
# Reading load reducer

## Purpose

Help a user decide what to read closely, skim, park, or skip when text volume is the bottleneck.

This skill reduces reading load before summarizing, synthesizing, deciding, or drafting. It does not claim factual support from unavailable material.

## When to use

Use when the user provides dense documents, long emails, instructions, policies, article excerpts, source packets, search results, bibliographies, reading lists, chapter drafts, or long notes and asks what matters, what to read first, or how to reduce reading burden.

Use `accessibility-low-load-companion` when reading load is mixed with dictation, spelling ambiguity, rough notes, or broader routing.

## Automatic selection guidance

- High-signal triggers: reading fatigue, too much to read, dense document, skim/read/skip, source triage, reading priority, reading load, close-reading target, long notes, long email, or instructions overload.
- Light-route behavior: classify material into read closely, skim, park, or skip, with short reasons and reliance limits.
- Escalation gate: use source verification or current lookup only when the user asks, source metadata is central, current facts matter, or a factual/high-stakes claim would otherwise be unsupported.
- Noise and slowdown guard: do not synthesize a field, produce a full summary, audit citations, or decide high-stakes matters when the user needs triage first.

## Do not use this skill when

- The user needs rough dictation or fragment cleanup; use `accessibility-dictation-notes`.
- The user needs spelling, grammar, punctuation, or sentence repair; use `accessibility-prose-repair`.
- The user needs broad accessibility routing across several bottlenecks; use `accessibility-low-load-companion`.
- The user asks for legal, medical, financial, or professional advice from dense material; reduce reading load and state expert-review limits.

## Inputs expected

- Documents, excerpts, abstracts, titles, search results, bibliography entries, notes, chapter drafts, policies, instructions, or reading list.
- Reading goal, decision, task, chapter, question, or reason for reading.
- Available access level: full text, excerpt only, metadata only, citation only, or unclear.
- Optional time budget, priority threshold, or output length limit.

## Source basis and limits

Use `docs/SOURCE_LIMITS.md` for verification and source-access rules. Keep source access level, what can be verified, what remains uncertain, and user verification needs visible when facts or decisions depend on the material.

If only titles, snippets, metadata, or partial excerpts are available, mark triage and skip risk as provisional.

## Compact output

Use compact output by default for low-risk reading triage, time-boxed triage, or a fast skim/read/skip decision. Compact output should use short chunks, stable labels, one source-basis line, one triage table, uncertainty and ambiguity only if access or meaning could change the decision, privacy or verification limits when relevant, and one useful next action only when it reduces friction.

## Files/folders it may read

- Shared operational boundary doc: `docs/SKILL_OPERATIONAL_BOUNDARIES.md`.
- Shared policy docs: `docs/SOURCE_LIMITS.md`, `docs/AUTO_SELECTION_GUARDRAILS.md`, `docs/ROUTING_MATRIX.md`, and `docs/SKILL_INDEX.md`.
- User-provided documents, excerpts, search results, bibliographies, drafts, notes, tasks, or constraints explicitly named in the request.

## Files/folders it may write

- None by default.
- May create or update user-requested reading triage tables, reading plans, source-priority notes, or follow-up task lists in the user-designated workspace.
- Must not overwrite source files, notes, bibliography databases, drafts, or private files unless the user explicitly asks.

## What it must not do

- Do not infer source support from title, snippet, or abstract alone.
- Do not turn provisional reading triage into verified synthesis.
- Do not claim unread material is irrelevant when access is too thin; mark it as park or needs metadata instead.
- Do not produce long summaries when the goal is reducing reading load.
- Do not make legal, medical, financial, workplace, or publication decisions for the user.

## Procedure

### 1. State the reading goal

Identify the user's task, decision, question, claim, or reason for reading. If absent, use the visible task and mark the goal as inferred.

### 2. Classify access

For each item or excerpt, mark access level:

- full text
- excerpt only
- metadata only
- citation only
- unclear

### 3. Triage the material

Before assigning `skip`, apply the access rule: title-only, citation-only, snippet-only, or unclear-access items default to `park` unless the supplied metadata makes them clearly off-scope for the current task.

Classify each item:

- read closely: likely central to the current task, claim, decision, method, case, or instruction
- skim: useful context or secondary support
- park: potentially relevant but needs metadata, source access, or later attention
- skip: off-scope for the current task based on available material

### 4. Name the reason

Give short reasons tied to the user's goal:

- decision support
- task requirement
- evidence or verification
- key concept
- counterpoint
- background context
- low relevance
- insufficient access

### 5. Build a reading plan

Suggest a short sequence that starts with the highest-return reading and names what to extract from each item. If the user supplies a time budget, spend it explicitly across read closely, skim, and park decisions.

## Output format

Default compact output:

```markdown
# Reading triage

Source basis: [one line]
How to use this result: TRIAGE ONLY - Use this only to prioritize reading; do not treat it as verification or final advice.

| Item | Access level | Decision | Why | First extraction target | Skip/park risk |

Uncertainty or ambiguity: [only if access is thin or meaning is unclear]
Privacy or verification limit: [only when relevant]
Next action: [one useful next action only when it reduces friction]
```

Expanded output:

Use expanded output when the task is high-stakes, evidence-sensitive, public-facing, workplace-sensitive, legal/medical/financial, publication-related, source-sensitive, or when the user asks for a fuller reading audit.

```markdown
# Reading load reducer

## Source basis

## Reading goal

## Triage table
| Item | Access level | Decision | Why | What to extract | Risk or uncertainty if skipped |

## Reading plan

## Close-reading targets

## Skim targets

## Park or skip

## What I can verify

## What remains uncertain

## User verification needed
```
