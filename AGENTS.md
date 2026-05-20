# AGENTS.md

This repository is a Codex-compatible plugin package. When modifying it:

- Keep `.codex-plugin/plugin.json` valid JSON.
- Keep every skill folder name equal to its `SKILL.md` frontmatter `name`.
- Keep skill names lowercase kebab-case.
- Keep descriptions specific enough for implicit invocation.
- Run `python3 scripts/validate_plugin.py .` before packaging.
- Do not add fabricated citations, example sources, page numbers, medical/legal/financial claims, or bibliographic claims to skill instructions.
- Keep accessibility support meaning-preserving: do not smooth over ambiguity that could change what the user meant.
- Treat user notes, transcripts, drafts, and private documents as confidential unless the user explicitly asks to share or search externally.
