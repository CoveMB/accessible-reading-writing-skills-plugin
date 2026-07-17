# Accessible Reading and Writing

Version: 1.0.0

Accessible Reading and Writing is a local plugin for reducing reading and writing load across everyday, work, learning, and research contexts. It handles rough notes, voice transcripts, dense documents, typo-heavy passages, dyslexic or dysorthographic writing friction, and mixed or unclear accessibility bottlenecks.

The package prioritizes meaning preservation. It can clean, segment, simplify structure, and identify next actions, but it should not change the user's intent or turn uncertain material into confident claims.

The package name is `accessible-reading-writing-plugin`. Its skill names use the `accessibility-*` prefix so this plugin can be enabled beside Research Book Skills without shadowing skills such as `reading-load-reducer`.

## Source

Public repository: [CoveMB/accessible-reading-writing-skills-plugin](https://github.com/CoveMB/accessible-reading-writing-skills-plugin).

## Install through a marketplace

Choose one marketplace source.

For a local checkout:

```bash
git clone https://github.com/CoveMB/accessible-reading-writing-skills-plugin.git
cd accessible-reading-writing-skills-plugin
codex plugin marketplace add .
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

For a Git-backed marketplace managed by Codex:

```bash
codex plugin marketplace add CoveMB/accessible-reading-writing-skills-plugin --ref main
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

The ChatGPT desktop app and the Codex CLI `/plugins` browser can install the same marketplace entry. Plugins are not available in Chat mode, the IDE extension, or mobile. Start a new task or CLI session after installation so Codex loads the four bundled skills.

## Update

For a Git-backed marketplace, refresh the repository snapshot:

```bash
codex plugin marketplace upgrade accessible-reading-writing-local --json
```

For a local checkout, update the checkout:

```bash
git pull --ff-only
```

Confirm that Codex still resolves the marketplace and plugin:

```bash
codex plugin marketplace list --json
codex plugin list --marketplace accessible-reading-writing-local --json
```

Open `.codex-plugin/plugin.json` under the marketplace source root and confirm that its `version` is the release you intend to install. Stop if the refresh fails, the marketplace is missing, the manifest still reports the old version, or marketplace policy blocks installation.

Use the plugin browser's update action when available. Otherwise, reinstall the plugin through Codex:

```bash
codex plugin remove accessible-reading-writing-plugin@accessible-reading-writing-local
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

Run `codex plugin list --json` and confirm that the installed entry reports the intended version, `"marketplaceName": "accessible-reading-writing-local"`, and `"enabled": true`. Start a new task or CLI session before testing the skills.

Do not edit or delete `~/.codex/plugins/cache`. Codex owns that directory.

## Skills

- `accessibility-low-load-companion`: use when the bottleneck is mixed or unclear and no smaller/specialist skill clearly owns the task.
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

Compact output is the default for low-risk tasks: one source-basis line when relevant, one table or revised passage, ambiguity only when it could change meaning, privacy or verification limits when relevant, and one useful next action only when it reduces friction. Ask for expanded output when the task is high-stakes, evidence-sensitive, public-facing, workplace-sensitive, legal/medical/financial, publication-related, or source-sensitive.

## Verification and privacy limits

The skills can reduce load from the material available in the conversation. They should not claim to verify facts, citations, page numbers, source support, legal obligations, medical guidance, financial facts, or current information unless the needed source access and tools were actually used.

Private notes, drafts, transcripts, and sensitive documents should not be sent to external lookup tools without explicit user consent. When a task affects external sharing, workplace decisions, research claims, legal/medical/financial decisions, or publication, the output should keep verification gaps visible.

## Validate

```bash
./validate.sh
```

The full package check also runs unittest discovery, including
semantic-preservation regression tests for meaning-changing deformations such as
lost uncertainty, dropped negation, changed numbers or dates, hidden privacy
risk, and overstated source access. See
[`docs/SEMANTIC_PRESERVATION_TESTING.md`](docs/SEMANTIC_PRESERVATION_TESTING.md)
for how the fixtures and deterministic invariants work, and for their limits.

## Uninstall

Remove the installed plugin through Codex:

```bash
codex plugin remove accessible-reading-writing-plugin@accessible-reading-writing-local
```

If this repository marketplace is no longer needed, remove its registration:

```bash
codex plugin marketplace remove accessible-reading-writing-local
```

These commands let Codex clean up its own configuration and cache.

## License

[MIT](LICENSE)
