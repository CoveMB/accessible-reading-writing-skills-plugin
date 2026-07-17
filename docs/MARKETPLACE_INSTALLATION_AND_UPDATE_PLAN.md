# Marketplace installation and update plan

Status: implemented and CLI-verified  
Previous release: `1.0.0`  
Implemented release: `1.1.0`

## Purpose

Move the plugin to a conventional marketplace-based lifecycle. Codex should own plugin installation and its installed cache. The repository should own the plugin package, version, marketplace metadata, release notes, and compatibility wrappers.

The completed workflow must make these operations explicit:

- Add or refresh the marketplace.
- Install version `1.1.0` through Codex.
- Reinstall the plugin after a marketplace refresh when Codex does not offer an update action.
- Start a new task or CLI session before checking the installed skills.

This plan changes distribution and update behavior. It does not change what the accessibility skills do.

## Decision summary

- Add a repository marketplace at `.agents/plugins/marketplace.json`.
- Use `accessible-reading-writing-local` as the marketplace name.
- Point the local marketplace entry at the repository root with `source.path: "./"`.
- Bump the plugin and its four bundled skills from `1.0.0` to `1.1.0`.
- Keep `install.sh` and `install.ps1` during the `1.1.0` release as compatibility wrappers.
- Stop copying or linking files into Codex's plugin cache. Codex alone manages `~/.codex/plugins/cache`.
- Make the Codex plugin browser and `codex plugin` commands the documented installation path.
- Keep `marketplace.sample.json` for the compatibility release, but require it to match the canonical marketplace entry.
- Treat `1.0.0` as a separate legacy marketplace identity during migration and rollback.

The compatibility wrappers can be reconsidered after `1.1.0`. Removing them is outside this plan.

## Pre-1.1 state

Before this change, the repository had a valid plugin manifest and four versioned skills. Its installer validated the package, copied or linked the repository into `~/.codex/plugins`, edited the personal marketplace file, and could link the repository directly into a versioned cache directory.

That last responsibility belongs to Codex. An installed cache can lag behind the repository even when `~/.codex/plugins/accessible-reading-writing-plugin` is a symlink to the checkout. The earlier documentation also described `./install.sh` as the installation step, although the script still told the user to restart Codex and install or enable the plugin afterward.

Current Codex behavior separates the lifecycle into two parts:

| Owner | Responsibility |
|---|---|
| Repository | Plugin files, manifest version, marketplace metadata, validation, and release notes |
| Codex marketplace | Discovery and refresh of the plugin source |
| Codex plugin manager | Installation, removal, enablement, and installed cache management |
| User | Marketplace refresh, plugin reinstall when required, and starting a new task or session |

The implementation should preserve that boundary.

## Goals

1. A new user can add the repository as a local or Git marketplace and install the plugin through Codex.
2. An existing user can install and verify the `1.1.0` marketplace-qualified plugin before removing the legacy `1.0.0` installation.
3. Every public and machine-readable version surface reports `1.1.0`.
4. Existing `install.sh` and `install.ps1` entry points remain usable during the compatibility release.
5. Automated checks detect marketplace drift, version drift, and any return of direct cache manipulation.

## Out of scope

- Changing skill routing, instructions, output formats, privacy boundaries, or semantic-preservation behavior.
- Publishing to an OpenAI-curated or workspace-managed marketplace.
- Adding connectors, MCP servers, hooks, or scheduled tasks.
- Automatically pulling Git changes for the user.
- Deleting a user's marketplace, installed plugin, cache, or older draft packages.
- Removing `install.sh`, `install.ps1`, or `scripts/install_codex_plugin.py` in `1.1.0`.
- Creating a pull request, tag, release, or external marketplace entry without separate approval.

## Requirements and acceptance criteria

### R1. Bump the release to 1.1.0

Update the release version because the installation and update contract changes in a visible, backward-compatible way.

Acceptance criteria:

- `.codex-plugin/plugin.json` reports `1.1.0`.
- `README.md` reports `Version: 1.1.0`.
- Each `skills/*/SKILL.md` file reports `metadata.version: "1.1.0"`.
- `CHANGELOG.md` has a `1.1.0` entry that describes the marketplace workflow, compatibility wrappers, and removal of direct cache manipulation.
- Existing validator checks pass with the new manifest version.
- Release validation rejects longer version strings that merely begin with `1.1.0`.
- Tests use fixed sample versions only where the value is intentionally fixture data.

### R2. Add one canonical repository marketplace

Create `.agents/plugins/marketplace.json` as the source of truth for local and Git-backed discovery.

Required marketplace values:

```json
{
  "name": "accessible-reading-writing-local",
  "interface": {
    "displayName": "Accessible Reading and Writing Local"
  },
  "plugins": [
    {
      "name": "accessible-reading-writing-plugin",
      "source": {
        "source": "local",
        "path": "./"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

Acceptance criteria:

- The marketplace JSON parses successfully.
- Its plugin name matches `.codex-plugin/plugin.json`.
- `source.path` is relative, begins with `./`, and stays inside the marketplace root.
- `marketplace.sample.json` contains the same plugin entry and is marked as a compatibility example in the README.
- Validation fails when the canonical marketplace and manifest disagree.

### R3. Make marketplace-based installation canonical

Document the Codex plugin manager as the installer. Support both a local checkout and the public Git repository.

Local development flow:

```bash
codex plugin marketplace add .
codex plugin marketplace list
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

Git-backed user flow:

```bash
codex plugin marketplace add CoveMB/accessible-reading-writing-skills-plugin --ref main
codex plugin marketplace list
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

The ChatGPT desktop app and Codex CLI plugin browser remain supported alternatives. After installation, the user starts a new task or CLI session before invoking a bundled skill.

Acceptance criteria:

- The README leads with the marketplace flow rather than direct copying.
- The commands use the same marketplace and plugin names as the JSON files.
- Documentation distinguishes adding a marketplace from installing a plugin.
- Documentation states that plugins are unavailable in unsupported Codex surfaces when that limitation remains in the current official guidance.
- Installation instructions never ask the user to write inside `~/.codex/plugins/cache`.

### R4. Define reliable migration, update, and reinstall flows

The `1.0.0` installer used a personal marketplace. Its default name was `local-personal-plugins`, but it preserved another existing personal marketplace name. The `1.1.0` repository marketplace is a different plugin identity because Codex qualifies installed plugins by marketplace.

The `1.0.0` migration must therefore:

1. Register `accessible-reading-writing-local` without removing the legacy plugin.
2. Read `codex plugin list --json` and record the installed `1.0.0` entry's actual `marketplaceName`.
3. Confirm that the uninstalled `1.1.0` entry appears under `available` for `accessible-reading-writing-local`.
4. Install and verify the `1.1.0` marketplace-qualified entry.
5. Remove the legacy selector only after the new entry is installed and enabled.

Updates after `1.1.0` must handle Git-backed marketplaces, local checkouts, and clients that do not expose a direct update action. After refresh, `codex plugin marketplace list --json` provides the marketplace source root. The user checks `.codex-plugin/plugin.json` under that root before removing the installed version. `codex plugin list --json` is still used for the installed version and installation policy.

Use the plugin browser's update action when the current client exposes one. Otherwise reinstall through the stable CLI commands:

```bash
codex plugin remove accessible-reading-writing-plugin@accessible-reading-writing-local
codex plugin add accessible-reading-writing-plugin@accessible-reading-writing-local
```

Acceptance criteria:

- The README has separate `Upgrade from 1.0.0` and `Update` sections.
- The migration records the legacy `marketplaceName`, installs and verifies `1.1.0`, then removes the legacy selector.
- The normal update sequence refreshes the marketplace and verifies its source manifest before reinstalling the plugin.
- The normal update section does not expect an installed plugin to appear in the `available` array.
- The documented fallback uses `codex plugin remove` followed by `codex plugin add`.
- The instructions require a new task or CLI session after installation.
- The user can verify through `codex plugin list --json` that the installed plugin reports `1.1.0`, then confirm in a new task that all four bundled skills are available.
- Failure guidance covers a missing marketplace, stale source version, disabled installation, and marketplace-name conflict.

### R5. Preserve the installer entry points as compatibility wrappers

Keep the existing shell and PowerShell commands for one release. Their responsibility changes from managing files to delegating to the official marketplace workflow.

Required behavior:

- Validate the repository before registration.
- Confirm that the `codex` command is available.
- Add the repository root as a local marketplace through `codex plugin marketplace add`.
- Treat an existing registration at the same repository root as success. If the marketplace name points somewhere else, report the conflict without overwriting it.
- Label `codex plugin add` as installation, print the exact command, and direct existing users to the migration or update instructions.
- Preserve `--dry-run` as a no-write preview.
- Accept `--link` as a deprecated compatibility alias for local marketplace registration. Print a concise warning that no cache symlink is created.
- Return the delegated command's nonzero status.

The wrappers must not:

- Edit `~/.agents/plugins/marketplace.json` directly.
- Copy the plugin into `~/.codex/plugins`.
- Read, create, replace, link, or delete anything below `~/.codex/plugins/cache`.
- Uninstall or reinstall an existing plugin without an explicit user command.

Acceptance criteria:

- `scripts/install_codex_plugin.py` contains no cache-path construction or cache-link helpers.
- Tests confirm that `--dry-run` performs no external writes.
- Tests mock the Codex subprocess and assert the marketplace command, arguments, and exit-code handling.
- Tests cover repeated registration and a same-name marketplace conflict.
- Tests cover the deprecated `--link` alias without creating a symlink.
- Existing users can still run `./install.sh` or `.\install.ps1` to register the local marketplace.

### R6. Keep update operations safe and reversible

The documented and scripted workflow must avoid destructive cache operations.

Acceptance criteria:

- No implementation step uses `rm`, `rmdir`, `unlink`, or direct cache replacement against Codex-managed cache paths.
- Reinstall uses `codex plugin remove`, which owns its config and cache cleanup.
- Marketplace refresh and plugin reinstall remain separate commands so a user can inspect the refreshed source manifest before installation.
- Documentation tells users to stop after a failed marketplace refresh rather than reinstalling from an unverified snapshot.
- Rollback to `1.0.0` uses the verified legacy installer from commit `34aafd943a285ece7c64fbbe8686f902745b0a3c` because that revision has no repository marketplace.
- Rollback installs and verifies the legacy marketplace-qualified entry before removing `1.1.0`.

### R7. Add drift and regression checks

Extend validation around the new public contract.

Acceptance criteria:

- A test checks version agreement across the manifest, README, changelog, and all four skill frontmatter blocks.
- A negative test rejects README or changelog versions that only begin with the manifest version.
- A test checks the canonical marketplace name, plugin name, local source path, installation policy, authentication policy, and category.
- A test keeps `marketplace.sample.json` synchronized with the canonical plugin entry during the compatibility release.
- A test rejects installer code or public instructions that target `~/.codex/plugins/cache`.
- Tests preserve the marketplace-identity ordering for `1.0.0` migration and rollback.
- Existing destination-safety tests are removed only when their corresponding copy or link behavior is removed.
- Package validation and semantic-preservation tests continue to pass unchanged.

## Affected files

| File | Planned change |
|---|---|
| `.agents/plugins/marketplace.json` | Add the canonical repository marketplace. |
| `.codex-plugin/plugin.json` | Bump the plugin version to `1.1.0`. |
| `skills/*/SKILL.md` | Bump all bundled skill metadata to `1.1.0`. |
| `README.md` | Replace direct-copy installation with marketplace install, `1.0.0` migration, update, verification, legacy rollback, and compatibility guidance. |
| `CHANGELOG.md` | Add the `1.1.0` release entry. |
| `marketplace.sample.json` | Synchronize it with the canonical marketplace and identify it as a compatibility example. |
| `scripts/install_codex_plugin.py` | Convert it into a validation and marketplace-registration wrapper; remove copy and cache-link logic; label `plugin add` as installation. |
| `install.sh` | Keep the entry point and delegate to the compatibility wrapper. |
| `install.ps1` | Keep the entry point and delegate to the compatibility wrapper. |
| `scripts/validate_plugin.py` | Validate the canonical marketplace and exact cross-file version contract. |
| `scripts/plugin_utils.py` | Remove package-copy helpers only if no remaining packaging code uses them. Keep shared helpers that still serve packaging. |
| `tests/test_package_scripts.py` | Replace copy and cache-link tests with marketplace, subprocess, exact-version, lifecycle-documentation, and no-cache-write tests. |
| `docs/MARKETPLACE_INSTALLATION_AND_UPDATE_PLAN.md` | Keep this plan as the implementation and review reference. |

## Implementation sequence

### 1. Lock the baseline

1. Confirm `main` matches `origin/main` and the worktree contains no unexpected changes.
2. Run the current full test suite and plugin validator.
3. Record any pre-existing failures before editing.

### 2. Add marketplace metadata and bump the version

1. Add `.agents/plugins/marketplace.json` with the fixed values in R2.
2. Change the manifest and four skill metadata blocks to `1.1.0`.
3. Update the README version and add the changelog entry.
4. Synchronize `marketplace.sample.json`.
5. Add version and marketplace drift checks before changing the installer.

### 3. Convert the compatibility wrappers

1. Replace direct personal-marketplace edits with `codex plugin marketplace add <repository-root>`.
2. Remove plugin copying, plugin-directory symlinks, cache-path calculation, and cache symlinks.
3. Preserve validation, `--dry-run`, cross-platform entry points, and nonzero exit propagation.
4. Translate `--link` into the deprecated local-registration alias described in R5.
5. Replace obsolete tests with subprocess and no-write coverage.

### 4. Rewrite public installation and update documentation

1. Put marketplace installation before the compatibility wrappers.
2. Separate local checkout, Git-backed installation, `1.0.0` migration, later updates, rollback, and uninstall instructions.
3. Keep the earlier-draft package-name migration note separate from the released `1.0.0` marketplace-identity migration.
4. Run the Humanizer checklist while preserving every command, path, version, and product term.

### 5. Verify in an isolated Codex home

Use a temporary `CODEX_HOME` so verification does not modify the user's active plugins.

1. Run the committed `1.0.0` installer to create its default personal marketplace and install the legacy plugin through Codex.
2. Register the repository as `accessible-reading-writing-local` and confirm Codex reports `1.0.0` under `installed` and `1.1.0` under `available`.
3. Install `1.1.0`, verify both marketplace-qualified entries, then remove only the legacy selector.
4. Reinstall the legacy selector, verify `1.0.0`, then remove only the `1.1.0` selector to exercise rollback.
5. Confirm that normal marketplace list output reports the expected source root.
6. Confirm the compatibility wrapper's dry run produces the same marketplace selector and plugin selector without calling Codex.

The isolated migration and rollback sequence passed with Codex CLI `0.144.5` on 2026-07-17. It used temporary `HOME` and `CODEX_HOME` directories and did not alter the active plugin configuration.

Removing an installed selector does not remove its marketplace source. This is intentional: a personal marketplace can contain other plugins, and the repository marketplace remains useful for a later upgrade.

Do the final desktop-app check manually. Verify the marketplace appears, install the plugin, start a new task, and confirm the four `accessibility-*` skills are available.

## Verification commands

Run the repository checks:

```bash
python3 scripts/run_package_checks.py --scope full
python3 scripts/validate_plugin.py .
```

Exercise the compatibility preview:

```bash
./install.sh --dry-run
```

On Windows PowerShell:

```powershell
.\install.ps1 --dry-run
```

Inspect the marketplace and plugin through Codex:

```bash
codex plugin marketplace list --json
codex plugin list --marketplace accessible-reading-writing-local --json
```

Use `--available --json` only when checking a marketplace-qualified plugin that is not installed yet, such as `1.1.0` during migration from the legacy `1.0.0` marketplace.

## Rollback to 1.0.0

The `1.0.0` commit does not contain `.agents/plugins/marketplace.json`, so the new marketplace cannot refresh to that revision. The verified rollback is:

1. Stop before deleting any cache directory.
2. Create a detached worktree at commit `34aafd943a285ece7c64fbbe8686f902745b0a3c`.
3. Run the legacy installer in that worktree to restore the personal marketplace entry and copied `1.0.0` package.
4. Read the available legacy entry's `marketplaceName` and install that exact selector through `codex plugin add`.
5. Confirm that `1.0.0` is installed and enabled before removing `accessible-reading-writing-plugin@accessible-reading-writing-local`.
6. Start a new task or CLI session and confirm the four bundled skills are available.

If the legacy entry cannot be installed, leave `1.1.0` installed. If marketplace registration itself fails, do not replace the user's complete marketplace configuration.

## Review checklist

- The plugin package name remains `accessible-reading-writing-plugin`.
- The marketplace name remains `accessible-reading-writing-local`.
- The target version is `1.1.0` everywhere it represents the release.
- Cross-file validation requires exact version lines rather than version prefixes.
- The four skill names and their behavior remain unchanged.
- No code or documentation manipulates Codex's cache directly.
- Marketplace refresh happens before plugin reinstall.
- Migration installs and verifies `1.1.0` before removing the actual legacy marketplace-qualified selector.
- Rollback installs and verifies the legacy selector before removing `1.1.0`.
- Reinstall uses Codex commands rather than filesystem deletion.
- The compatibility wrappers remain available and clearly deprecated as installers.
- The full validation suite passes.
- A manual check confirms that a new task sees all four installed skills.

## Source basis

This plan follows the current Codex separation between marketplace management and plugin installation. The implementation should recheck the command help and official documentation immediately before release because plugin workflows can change.

- [Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Use and install plugins](https://learn.chatgpt.com/docs/plugins)
