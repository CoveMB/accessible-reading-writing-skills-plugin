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

## Suggested next step gates

Use these gates only when a follow-on skill reduces a named risk.

### Spoken material hides decisions, claims, questions, or tasks

Allowed next skill: `accessibility-dictation-notes`.

Blocked early suggestion: prose polishing before spoken ideas are segmented.

### Dense material or document volume blocks action

Allowed next skill: `accessibility-reading-load-reducer`.

Blocked early suggestion: summary or synthesis before read/skim/park/skip triage.

### Existing prose has spelling, grammar, punctuation, or sentence-boundary friction

Allowed next skill: `accessibility-prose-repair`.

Blocked early suggestion: broad rewriting before meaning-preserving repair.

### Mixed bottlenecks block the next useful action

Allowed next skill: `accessibility-low-load-companion`.

Blocked early suggestion: long menus or comprehensive review before the immediate bottleneck is clear.

### No unresolved accessibility risk remains

Allowed next skill: no suggestion.

Blocked early suggestion: any skill promotion.
