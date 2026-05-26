# Skill index

Use this file when you already know the rough shape of the work and need the right skill. Use `docs/ROUTING_MATRIX.md` for canonical automatic routing.

For concrete prompt examples and usage contexts, see `docs/SKILL_USAGE_EXAMPLES.md`.

## Skill folders

### `accessibility-low-load-companion`

Display name: Accessibility Companion.

Use for mixed or unclear accessibility bottlenecks when rough notes, dictation, reading load, spelling ambiguity, or next-step friction overlap and no smaller/specialist skill clearly owns the task.

### `accessibility-dictation-notes`

Display name: Dictation to Notes.

Use for dictated thoughts, voice transcripts, speech-to-text output, meeting notes, or rambling spoken fragments that need structured notes, decisions, questions, ambiguities, and next actions without changing meaning.

### `accessibility-reading-load-reducer`

Display name: Reading Load Reducer.

Use for dense documents, source excerpts, search results, policies, instructions, long emails, reading lists, or long notes that need read/skim/park/skip triage, extraction targets, uncertainties, and next actions.

### `accessibility-prose-repair`

Display name: Accessible Prose Repair.

Use for spelling, grammar, punctuation, sentence boundaries, paragraph breaks, and local readability repair while preserving meaning, voice, uncertainty, and important limits.

## Accessibility entry points

Use one of these when text friction blocks the next action:

1. `accessibility-dictation-notes` when spoken or transcript material is the first bottleneck
2. `accessibility-reading-load-reducer` when dense material or document volume is the first bottleneck
3. `accessibility-prose-repair` when existing prose needs meaning-preserving repair
4. `accessibility-low-load-companion` when the bottleneck is mixed or unclear and no smaller/specialist skill clearly owns the task

## Compact output support

Compact output is an output shape, not a route mode. It should reduce reading load without hiding uncertainty, verification gaps, privacy risks, or meaning-changing ambiguity.

Compact triage or capture results should include `How to use this result: TRIAGE ONLY - [full sentence]` when the output could be mistaken for verified advice. Compact revised-passage results may omit it when there is no factual, privacy, or decision risk.
