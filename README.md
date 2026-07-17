# Accessible Reading and Writing

Version: 1.1.0

Accessible Reading and Writing is a local plugin for reducing reading and writing load across everyday, work, learning, and research contexts. It handles rough notes, voice transcripts, dense documents, typo-heavy passages, dyslexic or dysorthographic writing friction, and mixed or unclear accessibility bottlenecks.

The package prioritizes meaning preservation. It can clean, segment, simplify structure, and identify next actions, but it should not change the user's intent or turn uncertain material into confident claims.

The package name is `accessible-reading-writing-plugin`. Its skill names use the `accessibility-*` prefix so this plugin can be enabled beside Research Book Skills without shadowing skills such as `reading-load-reducer`.

## Source

Public repository: [CoveMB/accessible-reading-writing-skills-plugin](https://github.com/CoveMB/accessible-reading-writing-skills-plugin).

## Install through a marketplace

Choose one marketplace source. For a local checkout:

```bash
git clone https://github.com/CoveMB/accessible-reading-writing-skills-plugin.git
cd accessible-reading-writing-skills-plugin
codex plugin marketplace add .
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

To let Codex maintain a Git-backed marketplace snapshot instead:

```bash
codex plugin marketplace add CoveMB/accessible-reading-writing-skills-plugin --ref main
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

The ChatGPT desktop app and the Codex CLI `/plugins` browser can install the same marketplace entry. Plugins are not available in Chat mode, the IDE extension, or mobile. Start a new task or CLI session after installation so Codex loads the four bundled skills.

### Compatibility setup commands

The shell and PowerShell commands remain available for the `1.1.0` compatibility release. They validate the repository and register its local marketplace. They do not copy the plugin or modify Codex's installed-plugin cache.

`marketplace.sample.json` mirrors the canonical `.agents/plugins/marketplace.json` entry as a compatibility reference. The file under `.agents/plugins/` is the source of truth.

From this folder:

```bash
./install.sh
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

Preview the install first:

```bash
./install.sh --dry-run
```

`--link` remains as a deprecated alias for local marketplace registration. It creates no symlink:

```bash
./install.sh --link
```

On Windows PowerShell:

```powershell
.\install.ps1
```

## Upgrade from 1.0.0

Version `1.0.0` used a personal marketplace instead of the repository marketplace introduced in `1.1.0`. Its default marketplace name was `local-personal-plugins`, although the installer kept another name if the personal marketplace already had one.

Register the `1.1.0` repository marketplace without removing the working `1.0.0` installation:

```bash
./install.sh
codex plugin list --json
```

In the JSON output, find the installed `accessible-reading-writing-plugin` entry with version `1.0.0` and note its `marketplaceName`. Keep that value until the migration is complete.

Because the `1.1.0` marketplace entry is not installed yet, it should appear in the `available` array here:

```bash
codex plugin list --marketplace accessible-reading-writing-local --available --json
```

Stop if the entry is missing, disabled, or does not report version `1.1.0`. Otherwise, install it and verify the new marketplace-qualified entry:

```bash
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
codex plugin list --json
```

The output should now include an enabled `1.1.0` entry whose `marketplaceName` is `accessible-reading-writing-local`. Codex may temporarily list both versions. After the `1.1.0` entry is confirmed, remove the legacy installation. This is the command for the default `1.0.0` marketplace:

```bash
codex plugin remove accessible-reading-writing-plugin@local-personal-plugins
```

If the recorded `marketplaceName` differs, use that value after `@` instead. Do not remove the legacy entry if the new marketplace registration or installation failed. Start a new task or CLI session after removal and confirm that the four bundled skills are available.

Removing the legacy installation does not remove its personal marketplace entry or copied source. The `1.0.0` entry may continue to appear under `available`. Leave that shared marketplace in place unless you have confirmed that removing its entry will not affect other plugins.

If marketplace registration reports that `accessible-reading-writing-local` already points somewhere else, stop without removing `1.0.0`. Resolve the marketplace-name conflict before continuing.

## Update

This section applies after the plugin is installed through `accessible-reading-writing-local`.

For a Git-backed marketplace, refresh its snapshot and confirm that Codex still resolves the marketplace:

```bash
codex plugin marketplace upgrade accessible-reading-writing-local --json
codex plugin marketplace list --json
codex plugin list --marketplace accessible-reading-writing-local --json
```

For a local checkout, update the checkout first:

```bash
git pull --ff-only
codex plugin marketplace list --json
codex plugin list --marketplace accessible-reading-writing-local --json
```

The marketplace-list output includes the source `root`. Open `.codex-plugin/plugin.json` under that root and confirm that its `version` is the release you intend to install. This checks the refreshed marketplace source. The installed entry from `codex plugin list --json` continues to report the installed version until the update is installed.

Stop before removal if refresh fails, the marketplace is missing, the source manifest still reports the old version, or the marketplace policy disables installation. Use the plugin browser's update action when the current client provides one. Otherwise, reinstall through Codex:

```bash
codex plugin remove accessible-reading-writing-plugin@accessible-reading-writing-local
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

Check the installed version:

```bash
codex plugin list --json
```

The installed entry should report `"version": "1.1.0"`, `"marketplaceName": "accessible-reading-writing-local"`, and `"enabled": true`. Start a new task or CLI session before testing the skills.

Do not edit or delete `~/.codex/plugins/cache` during installation or update. Codex owns that directory.

## Roll back to 1.0.0

Version `1.0.0` predates the repository marketplace, so it cannot be installed by pointing `accessible-reading-writing-local` at the old commit. The verified rollback uses the legacy installer from commit `34aafd943a285ece7c64fbbe8686f902745b0a3c` in a separate worktree. Run these commands from a full clone of the repository. If the plugin was installed only through a Git-backed marketplace, clone the repository first.

```bash
git worktree add --detach ../accessible-reading-writing-1.0 34aafd943a285ece7c64fbbe8686f902745b0a3c
cd ../accessible-reading-writing-1.0
./install.sh
```

On Windows PowerShell, run `.\install.ps1` in that worktree instead. The legacy installer copies the `1.0.0` package into its personal plugin directory and restores its marketplace entry. It does not remove the installed `1.1.0` plugin.

Inspect the legacy entry before installing it:

```bash
codex plugin list --available --json
```

Note the `marketplaceName` on the available `1.0.0` entry. The default command is:

```bash
codex plugin add accessible-reading-writing-plugin@local-personal-plugins
codex plugin list --json
```

If the marketplace name differs, replace `local-personal-plugins` with the reported value. Confirm that the `1.0.0` entry is installed and enabled before removing `1.1.0`:

```bash
codex plugin remove accessible-reading-writing-plugin@accessible-reading-writing-local
```

If the legacy entry cannot be installed, keep `1.1.0` and stop. After a successful rollback, start a new task or CLI session and confirm that the four bundled skills are available. The registered `1.1.0` marketplace may continue to show that version under `available`; this is expected. This procedure returns the plugin to the legacy `1.0.0` installation lifecycle.

## Upgrade from earlier local drafts

Earlier local drafts used the package names `accessibility-plugin` and `low-load-accessibility-plugin`. The first draft also included an unprefixed `reading-load-reducer` skill. If either draft was installed, install this renamed package through `accessible-reading-writing-local`. Remove the old marketplace entry and matching folder only after `codex plugin list --json` confirms the new plugin is installed and enabled.

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
