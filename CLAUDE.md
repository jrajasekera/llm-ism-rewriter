# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

A Claude Agent Skill, `llm-ism-rewriter`, plus the quality-engineering layer that
keeps it honest. The product is `SKILL.md` and its `references/`; the scripts are
optional accelerators and checks. There is no application, no build step, and no
runtime dependency beyond Python 3.10+ and its standard library — keep it that
way, because the skill has to run wherever it is copied.

## Commands

```bash
python3 -m unittest discover -s tests -v          # unit tests
python3 scripts/build_catalog.py --check          # registry / catalog / code contract
python3 scripts/build_catalog.py --write          # regenerate the rule index in patterns.md
python3 scripts/self_scan.py --check              # this repo's prose against its budget

python3 scripts/llm_ism_check.py FILE [FILE...]           # candidates and findings
python3 scripts/llm_ism_check.py --format json FILE       # machine-readable
python3 scripts/llm_ism_validate.py before.md after.md    # preservation validator
python3 scripts/llm_ism_validate.py --profile creative before.md after.md   # same profile as the checker
python3 scripts/llm_ism_project_check.py docs/            # cross-file templates
```

Checker exits: 0 always unless `--fail-on` is set, 1 when it is met, 2 on
unreadable input, 3 on a registry failure. Validator exits 1 on a preservation
failure. Both print diagnostics to stderr and structured output to stdout.

## Architecture

Progressive disclosure: `SKILL.md` is the only always-loaded file and points at
references rather than inlining them.

- **`SKILL.md`** — frontmatter (`name`, `description` decide when the skill
  triggers), the trust boundary, the three modes, an 8-step procedure, the report
  formats, and an acceptance gate. Keep it under 500 lines; a test enforces that.
- **`references/rules.json`** — **canonical** for deterministic rules: stable IDs,
  tier, family, edit priority, evidence strength, action, detector, thresholds,
  exceptions, and the eight context profiles. The checker reads it; nothing is
  hard-coded.
- **`references/patterns.md`** — the human-readable catalog, A–F, that the agent
  works from. Every registry rule carries a `catalog` anchor into it. The rule
  index at the bottom is generated.
- **`references/detector-map.md`** — the coverage contract: directly executable,
  partially executable, judgment-only.
- **`references/contexts.md`**, **`voices.md`**, **`rewrite-invariants.md`**,
  **`examples.md`**, **`negative-results.md`** — loaded at the steps that need them.
- **`references/narrative-review.md`** — prose fiction only. Analysis scope versus
  edit scope, the working map, and the five judgment-only `ST.NARRATIVE_*` checks
  (catalog F). The scripts never run these.
- **`scripts/llm_ism_core.py`** — shared segmentation, registry loading, inline
  masking, sentence splitting. Imported by every other script so the two
  checkers cannot drift.
- **`scripts/llm_ism_check.py`** — read, segment and protect, produce candidates,
  measure metrics, aggregate under profile thresholds, group overlaps, emit
  text/JSON/SARIF.
- **`scripts/llm_ism_validate.py`** — protected spans exact, technical anchors,
  semantic anchors, structure, residual findings.

## The contract

These are enforced by `scripts/build_catalog.py --check` and
`tests/test_catalog_contract.py`. Breaking one fails CI.

- **`rules.json` is canonical.** Adding a rule to `patterns.md` needs no
  detector. Adding a detector needs a registry rule *and* a catalog anchor.
- **Rule IDs are stable and namespaced** `FP|LX|RH|ST|CL` + `.UPPER_SNAKE`.
  Renaming one is a major version change.
- **Tier vocabulary is shared** across `SKILL.md`, `patterns.md`,
  `detector-map.md`, and the registry: `fingerprint`, `cliche`, `structural`,
  `clarity`. Renaming a tier means changing all four.
- **Four fields do separate jobs**: tier (what kind), edit priority (how
  urgent), evidence strength (how supported), action (what to do). Do not
  collapse them.
- **Every executable rule needs** one positive and two negative fixtures in
  `tests/fixtures/cases.json`.
- **Judgment-only rules** carry a `judgment_prompt` and must never acquire a
  regex, a term list, a metric, or a threshold. See `detector-map.md` for why
  each one is there.
- **The `narrative` family is judgment-only**, `full` in `creative` and `skip` in
  the other seven profiles. A corpus prevalence figure is never a threshold, and
  the absence of a narrative feature is never a finding.
- **Analysis scope is not edit scope.** The narrative review may read a whole
  story; it adds no events, motives, references, ambiguity, or restructuring the
  user did not ask for. In-place authority and restructuring authority are
  separate.
- **Provisional thresholds** must be recorded in `negative-results.md`. All of
  them currently are provisional. Research-informed rules with no measurement of
  their own are recorded there too, as unvalidated hypotheses.
- **Versions stay in sync**: `SKILL.md` frontmatter, `registry_version`,
  `TOOL_VERSION`, and a `CHANGELOG.md` entry.
- **Protected spans** (quotations, code, tables, frontmatter, URLs, paths,
  citations) are report-only in the skill and excluded from findings in the
  script unless `--include-protected`. Any new pattern must respect both.
- **Signals, not verdicts.** No wording anywhere may imply a detection proves
  authorship. A test asserts that no output schema contains a probability, score,
  or `human`/`mixed`/`AI` field.
- **No invented specifics.** Rewrite rules forbid adding names, dates, numbers,
  or sources; gaps get a `[specify: …]` marker and a `[Gap]` finding.
- **The skill runs on any harness.** `SKILL.md` and the references name no
  harness-specific tool, and every `references/` or `scripts/` path resolves
  against the skill's own directory rather than the working directory.
  `tests/test_harness_compat.py` enforces both, plus the agentskills.io
  frontmatter fields Claude Code, Codex, and Hermes Agent read.
- **Attribution.** `NOTICE.md` carries file-level provenance for the Wikipedia
  CC BY-SA source, Simon Willison's highlighter, `ai-smell`,
  `avoid-ai-writing`, and the StoryScope paper. Preserve it and the header of `references/patterns.md` in
  any redistribution or restructuring.

## Changing things

- **Unit tests and evals are different.** `tests/` verifies the code; `evals/`
  verifies that an agent following the skill behaves better than one following
  the previous version. A change to rules or wording wants both.
- **Changes to `SKILL.md`, an output schema, a rule ID, a profile, or validator
  policy** require the matching contract test and a changelog entry.
- **A research finding is not a production threshold** until it has been
  measured across the registers named in `negative-results.md`. Record the
  decision there either way, including rejections.
- **A false positive becomes** a narrower detector plus a test, a profile
  carve-out plus a test, or a documented decision to keep the finding with a
  negative fixture. Never a silent close.
- **Self-scan budgets move down or hold.** Raising one needs a commit that says
  why. Prefer fixing the prose.

## Writing style for this repo

The skill's own prose is subject to its own catalog. Before committing changes
to any Markdown here, run `python3 scripts/self_scan.py --check`. Put
illustrative clichés inside code spans, quotations, or an exempted file so they
are protected rather than counted; if a finding is real, fix the prose rather
than the budget.
