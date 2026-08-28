# Evals

`tests/` verifies that the deterministic code does what it says. These evals
verify that an agent following the skill behaves better than one following the
previous version. Both are needed; neither substitutes for the other.

## How to run

Point your eval harness at `evals.json`. Each case names an input under
`files/`, a prompt, an expected behavior in prose, and machine-checkable
assertions. Several assertion kinds are implemented directly by
`scripts/llm_ism_validate.py` — `validator_passes`, `code_blocks_identical`,
`frontmatter_identical`, `table_identical`, `inline_code_preserved`,
`number_with_unit_preserved`, `modality_count_unchanged`, `no_new_proper_noun`,
`no_new_first_person`, `findings_decrease` — so a harness can shell out to it
rather than reimplementing the checks:

```bash
python3 scripts/llm_ism_validate.py --json --mode rewrite before.md after.md
```

The remaining assertions read the agent's response text rather than the
rewritten document.

## What to compare

Run the current version against the `baseline` version on the same cases, at
least `runs_per_case` times each, and compare:

- preservation failures (should go down)
- unnecessary changes to clean passages (should go down)
- true editorial fixes (should not go down)
- token cost per case (should be justified by the first three)

A single impressive output is not a result. Neither is a rule that fires more
often.

## Trigger testing

`trigger_cases` is tested separately from output quality. Run each prompt
several times in the target agent and record the activation rate. Revise the
description in `SKILL.md` if it misses legitimate phrasing, or if it activates
for ordinary copyediting or for authorship accusations — the skill must not
engage the last of these at all.

## Turning a review into a fixture

Every concrete comment from the human rubric should become either a new eval
assertion or a fixture in `tests/fixtures/`. A finding nobody can reproduce is
not a finding.
