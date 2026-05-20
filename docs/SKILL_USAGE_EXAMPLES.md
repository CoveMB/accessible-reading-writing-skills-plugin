# Skill usage examples

Use this guide when the task is mostly clear but the prompt needs better wording. If the right skill is still unclear, start with `docs/ROUTING_MATRIX.md`.

The examples are synthetic. Replace bracketed placeholders with user-provided material. Keep private notes, transcripts, drafts, and documents private unless the user explicitly asks to share or search externally.

## Before you prompt

Include the details that change the result:

- the skill name
- the source material or where to find it
- the user's goal
- constraints that protect meaning, privacy, terms, names, dates, commitments, or citations
- whether compact output is preferred

Use `compact output` when the user needs the shortest useful result. Compact output still needs to show ambiguity, verification gaps, privacy limits, and user checks when those details affect meaning or risk.

## `accessibility-low-load-companion`

Use this when several accessibility problems overlap and the first useful step is not obvious.

Helpful context:

- what feels blocked: reading load, dictation cleanup, typo ambiguity, reply drafting, task capture, or planning
- what output would help first: route, cleaned note, action table, reading plan, or repaired passage
- whether the user wants one next action instead of a full menu

Example prompts:

```text
Use accessibility-low-load-companion. I have a rough voice note, a dense instruction excerpt, and a draft reply. Choose the smallest useful next step and keep the output compact.

[paste material]
```

```text
Use accessibility-low-load-companion. I am not sure whether this needs dictation cleanup, reading triage, or prose repair. Give me the route, why, and the first action only.

[paste material]
```

```text
Use accessibility-low-load-companion. Turn this mixed note into a short action table. Mark any wording that could change meaning instead of guessing.

[paste material]
```

Skip this skill when one smaller skill clearly owns the request.

## `accessibility-dictation-notes`

Use this when spoken or speech-to-text material needs structure before it becomes prose, tasks, or a plan.

Helpful context:

- transcript type: voice memo, meeting transcript, auto-caption, spoken fragment, or rough dictated idea
- transcript quality: clean, noisy, partial, or unclear
- intended use: tasks, follow-up email, learning notes, planning, research notes, or meeting record
- speaker labels, timecodes, names, and terms that must stay unchanged

Example prompts:

```text
Use accessibility-dictation-notes. Turn this voice memo into cleaned notes, open questions, and next actions. Preserve uncertainty and do not turn unclear speech into facts.

[paste voice memo transcript]
```

```text
Use accessibility-dictation-notes. Segment this meeting transcript into decisions, tasks, questions, ambiguities, and follow-up. Keep speaker labels where they matter.

[paste transcript]
```

```text
Use accessibility-dictation-notes with compact output. This auto-caption text is noisy. Clean only obvious transcription noise and list phrases that need my check.

[paste auto-caption text]
```

Use `accessibility-prose-repair` instead when the input is already prose and only needs spelling, grammar, punctuation, or paragraph repair.

## `accessibility-reading-load-reducer`

Use this when text volume is the bottleneck and the user needs read, skim, park, or skip triage before synthesis or drafting.

Helpful context:

- reading goal, decision, question, or task
- access level: full text, excerpt only, metadata only, citation only, or unclear
- time budget or priority threshold
- what the user needs to extract: claims, tasks, risks, definitions, methods, obligations, or counterpoints

Example prompts:

```text
Use accessibility-reading-load-reducer. I have 12 abstracts and 30 minutes. Classify each as read closely, skim, park, or skip for this goal: [goal]. Source access: abstracts only.

[paste abstracts]
```

```text
Use accessibility-reading-load-reducer. This email thread is too long. Tell me what I must answer today, what I can skim, and what I should park. Do not decide obligations that are not visible in the text.

[paste email thread]
```

```text
Use accessibility-reading-load-reducer with compact output. Triage these instructions into read closely, skim, park, or skip. Mark anything that needs source or policy verification.

[paste instructions]
```

Do not use this skill to claim facts are verified from titles, snippets, citations, or partial excerpts alone.

## `accessibility-prose-repair`

Use this when existing prose needs meaning-preserving repair: spelling, grammar, punctuation, sentence boundaries, paragraph breaks, typos, or local readability.

Helpful context:

- desired repair level: minimal correction, local sentence repair, paragraph repair, or issue-list cleanup
- terms, names, numbers, dates, quotes, citations, commitments, and claims that must not change
- whether the output is private, external, workplace, publication, legal, medical, or financial
- whether the user wants a correction log or only the revised passage

Example prompts:

```text
Use accessibility-prose-repair. Fix spelling, grammar, punctuation, and sentence boundaries without changing my meaning. Keep all dates, names, and commitments unchanged.

[paste passage]
```

```text
Use accessibility-prose-repair. Clean this email for readability, but do not add apologies, promises, or new obligations. Mark any correction that could change meaning.

[paste email draft]
```

```text
Use accessibility-prose-repair with compact output. Repair paragraph breaks and local sentence flow only. Do not verify or strengthen the claims.

[paste draft]
```

Do not use this skill to rewrite arguments, add evidence, invent citations, or make factual claims stronger.

## Mixed workflow examples

Suggest only one follow-on skill, and only when it reduces a named risk.

```text
Use accessibility-low-load-companion. Choose whether this first needs dictation cleanup, reading triage, or prose repair. After that, suggest at most one next skill.
```

```text
Use accessibility-dictation-notes first. After the cleaned notes are stable, suggest prose repair only if there is a concrete draft passage to repair.
```

```text
Use accessibility-reading-load-reducer first. Do not summarize or rewrite until the read, skim, park, and skip choices are clear.
```
