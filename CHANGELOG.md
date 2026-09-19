# Changelog

Semantic versioning for behavior. **Patch:** a narrower regex, corrected docs, a new
negative fixture. **Minor:** a new rule, output field, profile, or optional script.
**Major:** a schema break, renamed rule IDs, changed mode semantics, or an
incompatible CLI. `SKILL.md`'s frontmatter version, `registry_version` in
`references/rules.json`, and `TOOL_VERSION` in the scripts are kept in sync by
`scripts/build_catalog.py --check`.

## [2.2.0]

A narrative-review layer for prose fiction, and one profile for both sides of a
validation. The five new checks are editorial hypotheses adapted from Russell et
al., *StoryScope* (arXiv 2604.03136v6). No agent evaluation of them has been run;
`references/negative-results.md` records that, and what the paper does and does
not support.

### Added

- `references/narrative-review.md`. It says when the review applies (prose
  fiction, judged from the task and the text) and separates analysis scope from
  edit scope. It defines a working map of events, viewpoint, and reader
  knowledge, reviewed in three passes. Its report format for fiction adds a
  coverage line and a `[Decision]` tag for choices that belong to the author.
- Five judgment-only `structural` rules in a new `narrative` family, catalog
  section F: `ST.NARRATIVE_THEME_REDUNDANCY`, `ST.NARRATIVE_EMOTION_REDUNDANCY`,
  `ST.NARRATIVE_DECORATIVE_MIRRORING`, `ST.NARRATIVE_FORCED_CLOSURE`,
  `ST.NARRATIVE_INFORMATION_TIMING`. The family is `full` in `creative` and
  `skip` in the other seven profiles. The checker emits nothing for them.
- `llm_ism_validate.py --profile`, and a `profile` argument on `validate()`
  defaulting to `auto`. The output names the profile used: an `INFO: context
  profile` line in text, `profile` and `profile_source` in JSON.
- Narrative commitments in `references/rewrite-invariants.md`, a note on
  directness in fiction in `references/voices.md`, and examples EX-NR-01 to
  EX-NR-14 with a worked report whose outcome is an author decision and no
  structural edit. EX-RH-07 covers several differently worded paragraphs doing
  one rhetorical job in nonfiction, under the existing restatement rule.
- Agent eval cases E13 to E38, with three original long stories as inputs.
  Every assertion kind is now labeled machine-executed, agent-judged, or
  human-reviewed.

### Changed

- `SKILL.md` separates analysis scope from edit scope and routes prose fiction
  to the narrative review. The validator now receives the checker's profile.
  The second audit covers every layer used, and the acceptance gate includes
  narrative preservation.
- `references/contexts.md` splits fiction handling into the deterministic layer
  and the narrative layer, keeps poetry, lyrics, and speeches out of the second,
  and adds coverage reporting to the large-file policy.
- `build_catalog.py --check` rejects any executable key on a judgment-only rule,
  where it used to reject `patterns` alone. It also requires a judgment-only
  family to hold no executable rule and to be enabled in exactly one profile.
- `evals/evals.json` compares 2.2.0 against the 2.1.1 commit. The global "fewer
  P0/P1 findings" objective became case-specific: a no-change case and a
  narrative edit can both succeed with identical checker output.

### Fixed

- The validator ran its residual-findings check with `auto` on each version
  separately. A story without sustained quoted dialogue was judged as
  `general-prose` even when the agent had chosen `creative`, and a revision that
  lost a genre cue was judged under different rules from its source. Both sides
  now share one profile, resolved once.

## [2.1.1]

Fixes the `spec` CI job, which validates this skill against the Agent Skills
reference implementation.

### Fixed

- `version` and `author` return to `metadata`. 2.1.0 promoted them to the top
  level on the strength of one harness's authoring guide, which lists them as
  recommended top-level fields; `skills-ref validate` rejects any key outside
  `name`, `description`, `license`, `compatibility`, `metadata` and
  `allowed-tools`. The spec is the authority, and `metadata` is the open field
  the spec provides for exactly this.
- The workflow validates `$GITHUB_WORKSPACE` rather than `.`. The validator
  takes the basename of the path it is given to check against the skill name,
  and the basename of `.` is empty, so the job had been failing on every push
  since it was added — the frontmatter error in 2.1.0 was the second one.

### Added

- `tests/test_harness_compat.py` now enforces the spec allowlist directly: any
  top-level key outside those six fails, and the version must sit under
  `metadata`. This is the check that would have caught the 2.1.0 regression.

## [2.1.0]

Portability across harnesses. No rule, threshold, schema, or editorial judgment changed.

### Added

- A `Paths` section in `SKILL.md`: reference and script paths resolve against the
  skill's own directory, with a fallback that locates it under any of the four
  install roots. The scripts already found their registry from `__file__`; the
  documented commands now match.
- Frontmatter fields the agentskills.io base spec expects at the top level:
  `version` and `author` move out of `metadata`, `license` becomes a bare SPDX
  identifier, and `compatibility` names the harnesses.
- `tests/test_harness_compat.py`: frontmatter fields, the directory-name match,
  the 500-character `compatibility` limit, no runnable command that assumes the
  working directory, and no harness-specific tool name in the skill or its
  references.
- Install instructions for Codex and Hermes Agent, and for the shared
  `~/.agents/skills` root, in `README.md`.

## [2.0.0]

A quality-engineering layer around the same conservative skill. The editorial
position did not change; everything that enforces it is new.

### Added

- `references/rules.json`: a canonical registry of 41 rules with stable IDs,
  tiers, edit priorities, evidence strengths, actions, thresholds, and eight
  context profiles. The checker reads it rather than hard-coding constants.
- `references/detector-map.md`: the coverage contract — directly executable,
  partially executable, and judgment-only rules, with what the script cannot decide.
- `references/rewrite-invariants.md`: the preservation contract, shared by the
  skill, the validator, and the fixtures.
- `references/voices.md`: seven bounded voice profiles, defaulting to `preserve`.
- `references/negative-results.md`: rejected hypotheses and every provisional
  threshold, with what would be needed to calibrate it.
- `scripts/llm_ism_core.py`: shared Markdown segmentation, registry loading,
  inline masking, and sentence splitting.
- `scripts/llm_ism_validate.py`: original-versus-rewrite preservation validator.
- `scripts/llm_ism_project_check.py`: templates repeated across several documents.
- `scripts/build_catalog.py`: the anti-drift contract check and rule-index generator.
- `scripts/self_scan.py`: scans this repository's prose against a committed budget.
- `tests/`: 207 unit tests over fixtures, including a coverage contract requiring
  one positive and two negative fixtures per executable rule.
- `evals/evals.json`: agent evals comparing this version against 1.0.0.
- `corpus/manifest.json`: provenance-aware corpus manifest.
- CI, a false-positive issue template, `LICENSE`, and `NOTICE.md`.
- New structural rules: `ST.LABELED_BULLET_RUN`, `RH.PHRASE_TRIAD`,
  `ST.HEADING_FRAME_REPEAT`, `ST.HEADING_RHETORIC`, `ST.FRAGMENT_RUN`,
  `ST.SENTENCE_CONTINUITY`, `ST.OPENING_IDENTITY`, `ST.CROSS_FILE_TEMPLATE`.

### Changed

- The checker separates raw **candidates** from contextual **findings**, applies
  the registry's thresholds and the profile's tolerances, groups overlapping
  matches into one finding, and reports what it suppressed and why.
- Markdown parsing is a typed segment model: fence character and length are
  tracked, tilde fences and unclosed fences are handled, frontmatter is
  recognized only at the top, headings are scanned rather than skipped,
  unattributed callouts are scanned while attributed quotes stay protected,
  tables with and without leading pipes are recognized, and paragraph and
  section boundaries survive into the metrics.
- Sentence splitting protects abbreviations, decimals, versions, and initials.
- Findings carry exact start and end line and column, rule IDs, evidence
  strength, and, for metrics, the numerator, denominator, threshold, and
  threshold status.
- Output: `--format text|json|sarif`, `--level findings|candidates`,
  `--profile`, `--include-protected`, `--fail-on`, `--max-findings`, `--output`.
  JSON carries `schema_version` and `tool_version`.
- `SKILL.md` is a tighter eight-step procedure with a validation gate and a
  single canonical final text; `preserve` is the documented default voice.
- Density is reported with its counts and denominators instead of a bare label.

### Not added, deliberately

No AI-probability score, no `human`/`mixed`/`AI` classification, no universal
word bans, and no "target zero em dashes" rule. See
`references/negative-results.md` for the measurements behind each of those
decisions, and the anti-goals in `README.md`.

## [1.0.0]

Initial release: `SKILL.md`, a three-file reference set, and a single regex
checker.
