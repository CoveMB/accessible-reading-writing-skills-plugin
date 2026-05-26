# Auto-selection guardrails

Use this policy when deciding whether an accessibility skill should trigger automatically.

## Selection rules

- Prefer the smallest useful skill over a broad sequence.
- Prefer `accessibility-dictation-notes`, `accessibility-reading-load-reducer`, or `accessibility-prose-repair` when one clear bottleneck owns the request.
- Use `accessibility-low-load-companion` only when the bottleneck is mixed or unclear and no smaller/specialist skill clearly owns the task.
- Do not use `accessibility-low-load-companion` when the user only asks for grammar/prose repair, transcript/dictation cleanup, or reading triage.
- Do not expand a cleanup request into research, legal, medical, financial, workplace, or publication advice unless the user asks or the material clearly requires a verification gate.
- Do not perform external lookup when it would not reduce a concrete risk or would require private material without consent.

## General escalation gates

Escalate from simple cleanup to visible verification limits when:

- a factual claim may affect decisions or external sharing
- the text includes citations, quotes, policies, legal/medical/financial claims, or current facts
- private or identifiable people appear in the material
- a wording change could alter responsibility, consent, diagnosis, money, deadlines, obligations, evidence, or claim strength
- the user asks for publication-ready, submit-ready, send-ready, or final wording

## Suggested next step policy

The final `## Suggested next step` section is optional. Omit it by default unless it reduces a concrete risk without adding avoidable reading load.

Add the section only when all gates pass:

- A specific unresolved risk remains.
- One skill clearly reduces that named risk.
- The required input exists or can be requested.
- The suggestion does not distract from the user's immediate accessibility bottleneck.
- The explanation fits in 2-4 lines.

Required format:

```md
## Suggested next step

Use `skill-name` to [specific next action].
Why this helps: [named risk reduced].
Use only if: [condition].
Skip if: [reason it would add noise now].
```

One suggested skill max. Do not add generic skill menus.
