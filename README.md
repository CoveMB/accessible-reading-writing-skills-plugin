# Accessible Reading and Writing

Version: 1.0.0

Accessible Reading and Writing is a local plugin for reducing reading and writing load across everyday, work, learning, and research contexts. It handles rough notes, voice transcripts, dense documents, typo-heavy passages, dyslexic or dysorthographic writing friction, and mixed accessibility bottlenecks.

The package prioritizes meaning preservation. It can clean, segment, simplify structure, and identify next actions, but it should not change the user's intent or turn uncertain material into confident claims.

The package name is `accessible-reading-writing-plugin`. Its skill names use the `accessibility-*` prefix so this plugin can be enabled beside Research Book Skills without shadowing skills such as `reading-load-reducer`.

## Source

Public repository: [CoveMB/accessible-reading-writing-skills-plugin](https://github.com/CoveMB/accessible-reading-writing-skills-plugin).

To install from a fresh checkout:

```bash
git clone https://github.com/CoveMB/accessible-reading-writing-skills-plugin.git
cd accessible-reading-writing-skills-plugin
./install.sh
```

## Install

From this folder:

```bash
./install.sh
```

The installer validates the package, copies it to `~/.codex/plugins/accessible-reading-writing-plugin`, and updates `~/.agents/plugins/marketplace.json`.

Preview the install first:

```bash
./install.sh --dry-run
```

For live local development, symlink this folder into both the local plugin directory and the installed plugin cache:

```bash
./install.sh --link
```

On Windows PowerShell:

```powershell
.\install.ps1
```

## Upgrade from earlier local drafts

Earlier local drafts used the package names `accessibility-plugin` and `low-load-accessibility-plugin`. The first draft also included an unprefixed `reading-load-reducer` skill. If either draft was installed, install this renamed package, then remove the old marketplace entry and matching folder only after confirming the new `accessible-reading-writing-plugin` entry appears.

## Skills

- `accessibility-low-load-companion`: use when the bottleneck is mixed or unclear.
- `accessibility-dictation-notes`: use for voice transcripts, spoken fragments, meeting notes, or rambling dictated ideas.
- `accessibility-reading-load-reducer`: use for dense material, long documents, source packets, instructions, policies, or reading lists.
- `accessibility-prose-repair`: use for spelling, grammar, punctuation, sentence boundary, paragraph, and typo repair while preserving meaning.

## Example prompts

For fuller usage contexts and prompt patterns, see `docs/SKILL_USAGE_EXAMPLES.md`.

```text
Use accessibility-low-load-companion. I have rough notes, a transcript fragment, and too much to read. Choose the smallest useful next step.
```

```text
Use accessibility-dictation-notes. Turn this voice note into cleaned notes, open questions, and next actions.
```

```text
Use accessibility-reading-load-reducer. Tell me what to read closely, skim, park, or skip in this long document.
```

```text
Use accessibility-prose-repair. Fix spelling and sentence boundaries without changing my meaning.
```

Add "use compact output" when you want one source-basis line, one table or revised passage, ambiguity only when it could change meaning, and one next action.

## Verification and privacy limits

The skills can reduce load from the material available in the conversation. They should not claim to verify facts, citations, page numbers, source support, legal obligations, medical guidance, financial facts, or current information unless the needed source access and tools were actually used.

Private notes, drafts, transcripts, and sensitive documents should not be sent to external lookup tools without explicit user consent. When a task affects external sharing, workplace decisions, research claims, legal/medical/financial decisions, or publication, the output should keep verification gaps visible.

## Validate

```bash
./validate.sh
```

## Uninstall

Remove `~/.codex/plugins/accessible-reading-writing-plugin`, then remove the `accessible-reading-writing-plugin` entry from `~/.agents/plugins/marketplace.json`.

## License

[MIT](LICENSE)
