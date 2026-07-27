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

## Contract coherence

Apply this coherence pass to every change that can affect plugin discovery, release identity, skill selection, runtime behavior, output shape, source or privacy limits, packaging, installation, user-facing guidance, or semantic-preservation guarantees.

1. Before editing, state the intended semantic change and identify its canonical owner.

   - `.codex-plugin/plugin.json` owns plugin identity, version, skill discovery path, and plugin-level interface metadata.
   - `.agents/plugins/marketplace.json` owns the repository marketplace representation; its plugin name must follow the manifest.
   - `skills/<skill-name>/SKILL.md` owns that skill's triggers, boundaries, procedure, and output contract.
   - `docs/ROUTING_MATRIX.md` owns automatic routing between skills.
   - `docs/SKILL_OPERATIONAL_BOUNDARIES.md` owns shared operating and safety requirements.
   - `docs/SOURCE_LIMITS.md` owns source-access, verification, privacy, consent, and external-tool boundaries.
   - `docs/AUTO_SELECTION_GUARDRAILS.md` owns automatic-selection, escalation, and suggested-next-step rules.
   - `scripts/plugin_utils.py` owns shared `agents/openai.yaml` policy values and package inclusion or exclusion rules.
   - `scripts/semantic_preservation.py` owns deterministic semantic-check behavior and fixture-schema enforcement.
   - `tests/fixtures/semantic_preservation_cases.json` owns the committed regression cases and their expected invariants.

   READMEs, the skill index, usage examples, changelog entries, agent metadata, tests, and generated package contents are consumers or representations unless a file explicitly declares otherwise.

2. Inventory every affected consumer before editing. Check, as applicable:

   - skill folder names and `SKILL.md` frontmatter
   - skill instructions and shared policy references
   - `agents/openai.yaml` descriptions, prompts, and policy blocks
   - plugin and marketplace metadata
   - `README.md`, skill READMEs, the skill index, routing docs, examples, and changelog
   - validators, packaging scripts, tests, fixtures, and CI
   - packaged and installed-plugin behavior

3. Define every affected state, precedence rule, exception, and failure boundary before changing wording or behavior. Relevant finite models include:

   - dictation, reading-load, prose-repair, and mixed-or-unclear routes
   - compact and expanded output
   - source-access levels
   - `conditional`, `route-only`, and `none` lookup policies
   - optional suggested-next-step gates
   - low-risk and escalation-required work
   - valid, invalid, packaged, installed, enabled, and stale release states

4. Update the canonical owner and all affected consumers as one coherent change. Remove superseded requirements instead of adding overlapping qualifications.

5. Keep normative definitions in their canonical owner. Consumers should link to the owner and contain only the summary, procedure, example, metadata representation, or assertion they own. A runtime-critical shared rule must be directly referenced by every `SKILL.md` that depends on it.

6. Preserve precedence explicitly:

   - user intent and meaning-preservation constraints govern edits
   - specialist skills take precedence when one clear bottleneck owns the request
   - `accessibility-low-load-companion` is only the mixed-or-unclear fallback
   - privacy and consent gates constrain external lookup
   - verification limits constrain factual or high-stakes output
   - compact output must retain decision-changing caveats

7. Put prerequisites before dependent steps. Place exceptions beside the rules they qualify, or link directly to the canonical exception.

8. After editing, search for the old and new terminology, close synonyms, route names, negations, and boundary terms such as `only`, `default`, `optional`, `must`, `must not`, `do not`, `unless`, `except`, `conditional`, `unverified`, `consent`, and `privacy`. Compare the resulting contract across every affected layer.

9. Prefer behavioral, structural, and parsed-field tests. Use exact-phrase assertions only for controlled vocabulary, stable identifiers, required headings, command interfaces, or literals intentionally owned by the contract.

10. When changing a finite state, route, policy, disposition, mode, or lifecycle, test every meaningful state, transition, precedence rule, exception, and rejected case. Semantic-preservation fixtures must include both an accepted output and a mutation or failure that demonstrates the regression is detectable.

11. Stop and ask when canonical owners conflict, ownership is unclear, documentation and runtime behavior disagree, or the intended behavior cannot satisfy all applicable meaning, privacy, source, packaging, and installation contracts.

12. Before completion:

   - run `./validate.sh`
   - confirm the full validation and test suite passes
   - confirm changed local references resolve in the packaged tree
   - inspect the final diff for stale or duplicated requirements
   - for discovery, marketplace, packaging, or runtime-loading changes, validate the staged package and do not claim installed-runtime coherence until it has been checked in a fresh Codex task or CLI session
   - request user authorization before modifying an installed plugin or other external state

## Test and evaluation economy

Optimize validation for confidence per token and minute. Token savings must never excuse a known deterministic failure.

### Validation sequence

1. Before running tests, identify:
   - the smallest targeted deterministic check;
   - the canonical full validation command;
   - any expensive, nondeterministic, live-model, visual, network, or external evaluation.
2. During implementation, run only targeted tests relevant to the changed behavior.
3. Run the canonical full suite once after the coherent implementation batch is complete.
4. Rerun the canonical suite only when the tested tree changes materially, including after conflict resolution, rebase, or merge.
5. Do not rerun an unchanged command against an unchanged tested tree. Reuse the recorded result.

### Expensive and nondeterministic evaluations

- Do not use live-model or external evaluations as an open-ended implementation loop.
- Preselect the cases, controls, acceptance criteria, and maximum attempts before starting.
- Allow at most:
  - one baseline execution; and
  - one confirmation execution after a material repair.
- An additional execution requires either:
  - a new concrete hypothesis supported by evidence;
  - a material change affecting the evaluated behavior; or
  - explicit user direction.
- If a nondeterministic evaluation fails inconsistently, rerun it at most once. If results still conflict, classify the evidence as inconclusive and report it instead of repeatedly sampling.
- Do not expand the evaluation matrix during implementation unless a newly discovered material risk requires it.

### Stop conditions

Stop implementation and validation when all of the following are true:

- targeted deterministic checks pass;
- the canonical full suite passes on the current tree;
- required structural and security validation passes;
- no material review finding remains;
- remaining limitations are explicitly documented and accepted.

Accepted evidence limitations are closed decisions. Do not reopen them without new evidence or explicit user direction.

### Delegated work

- Subagents must not run the full suite or live evaluations unless explicitly assigned.
- Use at most one bounded final reviewer for a coherent task unless that reviewer identifies a material defect.
- Reviewers should report only merge-blocking or materially beneficial findings, not style preferences.
- Do not delegate repeated reviews of unchanged code.

### Output discipline

- Prefer quiet or summary test output.
- Report the command, commit or tree identity, exit status, and test totals.
- Preserve verbose logs only when diagnosing a failure.
- Do not paste or repeatedly inspect successful verbose output.
