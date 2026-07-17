# Changelog

## 1.1.0

- Added a repository marketplace for local and Git-backed Codex installation.
- Replaced direct plugin copying and cache symlinks with Codex marketplace registration.
- Kept the shell and PowerShell setup commands as compatibility wrappers for the marketplace flow.
- Documented the marketplace-identity migration from `1.0.0`, verified update checks, plugin reinstall, and legacy rollback.

## 1.0.0

- Initial standalone Accessible Reading and Writing plugin.
- Added low-load accessibility routing, `accessibility-dictation-notes`, `accessibility-reading-load-reducer`, and `accessibility-prose-repair` skills.
- Uses package name `accessible-reading-writing-plugin` and `accessibility-*` skill names to avoid collisions with research-book skills.
- Added local validation, packaging, and install scripts.
