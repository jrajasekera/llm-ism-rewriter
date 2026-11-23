# Design: ideas adopted from blader/humanizer (target 2.5.0)

Status: draft for approval. Nothing in the skill has changed yet.

## Intent

`llm-ism-rewriter` and [blader/humanizer](https://github.com/blader/humanizer)
(MIT, v4.0.0 at commit `a32f244`) both descend from Wikipedia's "Signs of AI
writing". Humanizer has since named several patterns our catalog does not
reach and has three process ideas we lack. This change adopts those, in our
own wording and under our existing contract, so the skill catches more
formulaic prose without loosening what it preserves.

## Goals

1. Cover the patterns listed under "New and extended rules".
2. Give the agent a short test for formula that no listed rule reaches.
3. Stop over-editing informal text, and review replies for repeated context.
4. Let another task use the skill and get back only the final text.

## Non-goals

- No new stock-vocabulary terms. Word lists drift with each model release.
- No rule for hyphenated compound modifiers, curly quotes, or passive voice.
- No agent eval runs and no new eval cases. The eval harness is postponed;
  this change is covered by unit and contract tests. `evals/evals.json` gets
  only the version edit that `tests/test_evals_manifest.py` requires (my
  call; say so if you want unrun cases written for `embedded`, replies, and
  informal text).
- No new context profile.

## Anti-goals

These humanizer behaviours contradict our contract and must not arrive by
accident, in a rule, an example, or a fix line:

- Adding a detail the editor "knows to be true", or a reaction the writer
  "would" have. `No invented specifics` stands.
- A ban on em dashes. D3 and `negative-results.md` stand.
- Showing a first draft before the final text.
- Any statement about when or by what a text was written.
- Acting on a single sighting of a pattern a careful writer uses on purpose.

## Constraints

- `rules.json` stays canonical. Each executable rule needs one positive and
  two negative fixtures in `tests/fixtures/cases.json`, a catalog anchor, and
  a row in `detector-map.md`.
- Each new threshold is `provisional` and recorded in `negative-results.md`.
  Each new rule is also recorded there as an unvalidated hypothesis.
- A judgment-only rule carries a `judgment_prompt` and no pattern, term,
  metric, or threshold. The two new ones join the existing `layout` and
  `restatement` families, so no family is added and profile coverage is
  unchanged. They inherit those families' settings: `layout` is `skip` in
  `social-email` and `creative`, `restatement` in `legal-policy` and
  `creative`.
- `SKILL.md` stays under 500 lines and under 20,000 characters (it is at
  16,948; `tests/test_catalog_contract.py` enforces both), and names no
  harness-specific tool. The additions to it have about 3,000 characters to
  share, so detail goes in the references.
- Versions move together to 2.5.0: `SKILL.md` frontmatter, `registry_version`,
  `TOOL_VERSION`, and a `CHANGELOG.md` entry.
- Humanizer is credited in `NOTICE.md`, the `SKILL.md` attribution section and
  `metadata.sources`, the header of `patterns.md`, and the attribution bullet
  in `CLAUDE.md`. No wording, example, or watch list is copied; the examples
  below are written for this project.
- `scripts/self_scan.py --check` passes with no budget raised. New rule IDs
  may be added to the `exempt_rules` of `patterns.md` and `examples.md`, which
  quote the phrases they describe.

## Approaches

**A. Judgment-first, detectors for the clear phrases (chosen).** Every pattern
enters the catalog. A regex rule exists only where the phrase is unambiguous
enough to count, and it reports on recurrence. Shapes that plain writing also
uses stay judgment-only. This matches how C1 already treats plain
`not X but Y`.

**B. Catalog only.** No checker change and no new threshold. Smallest change,
but the checker surfaces none of the new patterns, so a long document gets no
candidates for them.

**C. A detector for everything a regex can reach.** Most coverage. It would
flag `The table below lists the flags` in every README and
`rather than` in every comparison, and each false positive then needs a
carve-out and a test.

The user chose A.

## New and extended rules

IDs and catalog anchors are proposals; the builder may adjust names before
they ship, since a rule ID is stable afterwards.

### New executable rules (regex, counted per document)

| Rule | Catalog | Family | What it matches | Threshold |
|------|---------|--------|-----------------|-----------|
| `RH.PHANTOM_OBJECTION` | new C9 | `contrast` | A defence against an objection or option nobody raised: `a tempting approach would be`, `one might be tempted to`, `it would be easy to just`, `don't get me wrong`, `this is not to say`, `I'm not saying` | 2 per document |
| `LX.GAP_SPECULATION` | new B9 | `attribution` | A statement that no source was found, in the stock wording: `while specific details are limited`, `not widely documented`, `based on available information`, `maintains a low profile`, `keeps personal details private` | 1 per document |
| `LX.PART_STANDIN` | B7 | `hooks` | `the hard part is`, `the part that matters`, `the part worth …` used to stage a point or stand in for a thing the text never names | 2 per document |
| `LX.DEPTH_SIGNAL` | B7 | `hooks` | `the real question is`, `what really matters`, `the deeper issue`, `the heart of the matter` | 2 per document |

All four are tier `cliche`, P1, low evidence, `scope: "document"` with
`minimum_occurrences` as shown. The action is `review_in_context` for three
and `request-detail` for `LX.GAP_SPECULATION`. All carry the `quoted_example`
exception. `RH.PHANTOM_OBJECTION` and `LX.PART_STANDIN` also carry
`established_first_person_voice` and `dialogue`.

Decisions inside these rules:

- `to be clear` is not matched. It is too common in ordinary writing.
- `not publicly available` is not matched. Reporting uses it literally
  (`The figures are not publicly available`).
- `LX.GAP_SPECULATION` matches the disclaimer. The guess that follows it
  (`she likely grew up…`) is the reader's judgment; the catalog says to look
  for it. Fix: state what the source does not show, or cut the sentence. Never
  fill the gap. A removed guess is reported as a `[Gap]`.
- `LX.PART_STANDIN` does not match a literal part (`one part of a multipart
  upload`); the patterns require the definite article plus an evaluative
  adjective or a `that`/`worth` clause.
- Fix for `RH.PHANTOM_OBJECTION`: remove the defence and keep any real claim
  inside it. Keep an objection the text attributes or answers in full.

### Extended executable rules

- `RH.APHORISM_CLOSER`: add standalone `Read that again.`,
  `That distinction matters.`, and `That is the real win.` forms.
- `LX.ENGAGEMENT_HOOK`: add stop-separated emphasis of three or more
  single lowercase words (`every. single. day.`). The capitalised form splits
  into three sentences before any pattern sees it; it is left to
  `ST.FRAGMENT_RUN` and the reader, and the catalog says so.
- `FP.PROMPT_LEAKAGE`: add a mid-line stray closing tag such as `</skill>` or
  `</system>`, and a line addressed from a claimed `system message`,
  `operator`, or `admin`. A tag that opens a line is segmented as protected
  HTML and is not matched. The trust boundary in `SKILL.md` names both forms,
  so the agent handles the one the checker cannot see.

Each extension needs its own positive and negative fixtures. The segmenter
and sentence splitter do not change (my call: the narrowed coverage is
documented in `detector-map.md`, and a segmenter change would put every
existing fixture at risk for two rare shapes).

### New judgment-only rules

| Rule | Catalog | Family | Question |
|------|---------|--------|----------|
| `ST.DOCUMENT_SELF_DESCRIPTION` | new D6 | `layout` | Does this sentence describe the document (what it replaced, how it was assembled, a layout the reader can see) where the reader needed its subject? |
| `RH.REDUNDANT_CONTEXT` | new C10 | `restatement` | In a reply, does the text rebuild background the visible conversation already contains before it reaches the answer? |

`ST.DOCUMENT_SELF_DESCRIPTION` keeps change history in release notes,
migration guides, incident timelines, and PR descriptions, as
`nonfiction-review.md` already says. It keeps a source credit a reader can
follow and a caveat that changes what the reader should do.

### Catalog text with no new rule

- **C1** gains two judgment-only shapes: the clipped negative tail
  (`…, no guessing`) and the reversed `X rather than Y` where X was never
  proposed. Neither gets a pattern. `detector-map.md` records why.
- **C4** gains the manufactured aphorism (`X is the language of Y`,
  `X becomes a trap`) as a judgment note. `English is the language of
  aviation` is a fact, so no pattern.
- **C5** and the `RH.LOW_INFORMATION_RESTATEMENT` judgment prompt gain the
  sentence that names what an example just showed (`It was a lesson in
  patience.`). Keep it when it adds a consequence the example does not show.
- **B5** notes the prestige list (`featured in` followed by a run of outlets)
  alongside the unnamed expert.

## The default-choice test

A short section in `SKILL.md`, before the workflow. Formulaic prose makes the
choice that would suit any reader and any subject; a writer with one reader
and one subject makes specific ones. Two questions follow from that, for use
on a passage no rule names:

- Would this sentence fit unchanged in a document on a different subject?
- Does it give the reader something they did not already have, from earlier
  in the text or from the conversation around it?

The section describes prose, never its origin, and says so. A "yes" then "no"
is a reason to read closely, reported under an existing rule
(`RH.LOW_INFORMATION_RESTATEMENT` in most cases), with the span. It creates no
new finding type and no licence to rebuild.

## Informal text

`contexts.md` gains a section, and the `social-email` row of the genre table
points to it. For chat messages, comments, rants, and angry reviews:

- Lowercase, abbreviations, fragments, and emphatic stops are the register.
  They are never findings.
- One candidate outside the `residue` family is not a finding. Two unrelated
  findings are needed before any edit.
- With no finding, return the text unchanged.
- `RH.REDUNDANT_CONTEXT` on an informal reply follows the same rule: alone,
  it is reported and nothing is deleted.

`rewrite-invariants.md` gains one invariant: strength of feeling is preserved.
An edit does not soften or sharpen an evaluative word, and does not make a
reported action sound more or less complete than the source did.

No registry change: `social-email` already relaxes or skips these families.

## Replies

`nonfiction-review.md` gains a section for `RH.REDUNDANT_CONTEXT`.

- It applies only when the surrounding conversation is visible, or the text
  is plainly a reply. Otherwise it is not raised.
- Report where the answer sits and which sentences repeat what the other
  person wrote or agreed to.
- In `rewrite` and `edit`, the agent may delete a sentence that duplicates
  the visible conversation, and reports each deletion in Findings. Moving the
  answer to the front is reordering: it is reported as a `[Decision]` with the
  suggested lead, and done only with restructuring authority. (My call, to
  keep in-place authority and restructuring authority separate.)
- Evidence, a query, or figures that the thread does not contain are unique
  information. They stay unless the user asks for a shorter reply.

## Output: `embedded`

`embedded` is an output setting on `rewrite`, not a fourth mode. It applies
when another task or skill uses this one to produce an artifact such as a
commit message, a PR description, or a section of a document, or when the user
asks for the text alone.

- The whole workflow runs, including validation and the second audit.
- The output is the final text and nothing else: no findings, no summary, no
  validation block.
- The final text carries no `[specify: …]` marker. Where a fix would need a
  fact the source lacks, the source wording stays.
- If a validator `FAIL` cannot be resolved, the affected span keeps its
  source wording. The calling task receives usable text either way.

`SKILL.md` documents it in the Modes and Report format sections. No existing
test pins a report format, so this adds a small new contract test: `SKILL.md`
names `embedded` in both sections and states that its output carries no
report and no `[specify: …]` marker.

## In-place edits

In `edit` mode, read the current file from disk before editing, even when the
same session wrote it. The `## Validation` block names the sections reviewed
and any that were not.

## Voice

`voices.md`, under `preserve`, gains a short list of details that carry the
author and survive an edit unless they damage the meaning: an odd specific
detail, a stated mixed feeling or unresolved tension, a dated or in-group
reference, a first-person choice the author explains, and an aside or
self-correction. These are things to keep. The universal limit against adding
any of them stays as written.

## Files touched

`SKILL.md` · `references/rules.json` · `references/patterns.md` (text, plus
the regenerated index) · `references/detector-map.md` · `references/contexts.md`
· `references/nonfiction-review.md` · `references/rewrite-invariants.md` ·
`references/voices.md` · `references/examples.md` (one before/after pair and
one counterexample per new rule) · `references/negative-results.md` ·
`tests/fixtures/cases.json` and the contract tests · `NOTICE.md` ·
`CHANGELOG.md` · `evals/evals.json` (version fields only) · `README.md` if it lists rule counts or modes · `CLAUDE.md`
(attribution bullet) · `self-scan-budget.json` (exemptions only) ·
`TOOL_VERSION` in the scripts.

No change to the checker's logic is expected: the four new rules use the
existing regex detector with per-document counting, as
`RH.SELF_ANSWERED_QUESTION` does. If a rule needs logic the detector lacks,
that is a scope change to raise before building it.

## Left to the builder

- Final rule IDs, catalog anchors, and regex wording.
- Whether the committed human-prose baseline in `corpus/` can measure the four
  new rules with `scripts/corpus_measure.py`. If it can, record the rates in
  `negative-results.md`; they inform the provisional thresholds and are never
  thresholds themselves.
- Example sentences, written fresh.

## Verification

```
python3 -m unittest discover -s tests -v
python3 scripts/build_catalog.py --check
python3 scripts/self_scan.py --check
```

All three pass, and the checker run on `README.md` and `SKILL.md` reports no
new finding from the new rules.
