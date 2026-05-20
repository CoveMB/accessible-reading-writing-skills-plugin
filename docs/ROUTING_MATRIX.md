# Routing matrix

Use this as the canonical route table for accessibility skill selection. Choose the smallest useful skill.

| Scenario | Route |
|---|---|
| Voice transcript, dictated thought, meeting note, rambling spoken fragment, auto-caption text, or "I talked this out" notes | `accessibility-dictation-notes` |
| Dense document, long email, article, policy, instructions, source packet, reading list, too much to read, skim/read/skip decisions, or close-reading targets | `accessibility-reading-load-reducer` |
| Spelling repair, grammar cleanup, dysorthographic prose, sentence-boundary repair, punctuation repair, paragraph breaks, typo-heavy passage, or meaning-preserving edit of existing prose | `accessibility-prose-repair` |
| Mixed or unclear accessibility bottleneck, broad dyslexia or dysorthographia support request, overlapping dictation plus reading load, spelling ambiguity plus rough notes, or "choose the smallest low-load next step" | `accessibility-low-load-companion` |

## Suggested next step gates

Use this table only when a follow-on skill reduces a named risk.

| Risk or prerequisite | Allowed next skill | Blocked early suggestion |
|---|---|---|
| Spoken material hides decisions, claims, questions, or tasks | `accessibility-dictation-notes` | Prose polishing before spoken ideas are segmented |
| Dense material or document volume blocks action | `accessibility-reading-load-reducer` | Summary or synthesis before read/skim/park/skip triage |
| Existing prose has spelling, grammar, punctuation, or sentence-boundary friction | `accessibility-prose-repair` | Broad rewriting before meaning-preserving repair |
| Mixed bottlenecks block the next useful action | `accessibility-low-load-companion` | Long menus or comprehensive review before the immediate bottleneck is clear |
| No unresolved accessibility risk remains | No suggestion | Any skill promotion |
