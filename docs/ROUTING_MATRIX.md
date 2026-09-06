# Routing matrix

Use this as the canonical route table for accessibility skill selection. Choose the smallest useful skill.

## Primary routes

### Voice, dictation, or transcript first

Route: `accessibility-dictation-notes`.

Use for voice transcripts, dictated thoughts, meeting notes, rambling spoken fragments, auto-caption text, or "I talked this out" notes.

### Reading volume first

Route: `accessibility-reading-load-reducer`.

Use for dense documents, long emails, articles, policies, instructions, source packets, reading lists, too much to read, skim/read/skip decisions, or close-reading targets.

### Existing prose repair first

Route: `accessibility-prose-repair`.

Use for spelling repair, grammar cleanup, dysorthographic prose, sentence-boundary repair, punctuation repair, paragraph breaks, typo-heavy passages, or meaning-preserving edits of existing prose.

### Mixed or unclear bottleneck

Route: `accessibility-low-load-companion`.

Use only when the accessibility bottleneck is mixed or unclear and no smaller/specialist skill clearly owns the task, such as overlapping dictation plus reading load, spelling ambiguity plus rough notes, or "choose the smallest low-load next step."

Do not use `accessibility-low-load-companion` when the user only asks for grammar/prose repair, transcript/dictation cleanup, or reading triage.

Suggested-next-step gates—including the default no-suggestion state and
one-skill maximum—are owned by
[Auto-selection guardrails](AUTO_SELECTION_GUARDRAILS.md); apply them after
selecting the primary route above.
