# Evals

`tests/` verifies that the deterministic code does what it says. These evals
verify that an agent following the skill behaves better than one following the
previous version. Both are needed; neither substitutes for the other.

## Status

No results are recorded here. Cases E01 to E12 came with 2.0.0. Cases E13 to E38
came with 2.2.0 and test the narrative review for prose fiction. Neither set has
a recorded run against the pinned baseline, `2.1.1` at the commit named in
`evals.json`. Until one exists, the narrative checks are hypotheses, and
`references/negative-results.md` says so.

## How to run

Point your eval harness at `evals.json`. Each case names an input under
`files/`, a prompt, an expected behavior in prose, and a list of assertions. No
harness ships in this repository, so `assertion_kinds` in the manifest declares
every kind under the evaluator it needs:

- **`machine`** — computed from the validator's JSON or from a plain comparison
  of the source and the revised text. The manifest gives the computation for
  each. Pass the case's profile so both versions are judged alike:

  ```bash
  python3 scripts/llm_ism_validate.py --json --profile creative --mode rewrite before.md after.md
  ```

- **`agent_judge`** — a yes/no question, written out in the manifest, put to a
  judge model or a reviewer who sees the source, the response, and the case's
  `expected` text. Record the judge model and its prompt with the results.
- **`human`** — needs a blind reviewer. Do not substitute a judge model.

An assertion name in the manifest proves nothing until something has evaluated
it. `tests/test_evals_manifest.py` checks only that the manifest is coherent:
inputs exist, kinds are declared, quoted spans occur in their input, and the
checker cannot see the problems the narrative cases plant.

## The narrative cases

The short inputs under `files/narrative/` each test one local decision. Three
complete stories of about 2,500 words test what a short input cannot: coverage
of a whole story, a theme restated across scenes, an ending, and a voice that
has to survive. One is plain, one is ornate, and one is a clean nonlinear
control whose correct result is no change. All of it was written for this
project. Do not add stories from a research corpus or any other source you do
not hold the rights to.

Two leave-alone cases exist for every case that plants a problem, and a test
holds that ratio. A change that finds more problems and damages the controls is
a regression.

Two planted cuts, in E13 and E22, remove a sentence containing a negation, which
the validator counts as lost. Those cases accept either outcome the skill allows: a wording
that validates, or the sentence left in place with the cut reported as deferred.

`hard_failures` in the manifest lists what fails a run outright. `protocol`
covers pinning, partitions, blind review, and cost.

## What to compare

Run the current version against the `baseline` version on the same cases, at
least `runs_per_case` times each, and compare:

- preservation failures (should go down)
- unnecessary changes to clean passages (should go down)
- true editorial fixes (should not go down)
- on fiction: findings that cite the passage, decisions handed back to the
  author, and controls left alone
- token cost per case (should be justified by the first three)

A single impressive output is not a result. Neither is a rule that fires more
often, and neither is a lower checker count: a narrative edit can succeed with
identical checker output. Do not gate on an authorship detector or any
"humanness" score.

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
