# Negative results and provisional thresholds

Rules that look convincing and do not survive measurement come back every few
months unless someone writes down why they were rejected. This file is that
record. It also lists every threshold currently marked `provisional` in
`references/rules.json`, so that no number in this repository can quietly
acquire the authority of a finding.

`scripts/build_catalog.py --check` fails if a provisional threshold is not
named here.

## Standing rule

No metric in this repository is evidence of authorship. Several of the entries
below were originally proposed *as* authorship signals in the source studies and
did not hold up even there. That is the strongest available argument for the
project's framing: these are readability and editing signals, and nothing else.

## Recorded results

### Sentence-length variation does not separate authorship

- **Hypothesis:** generated prose has a lower coefficient of variation in
  sentence length than human prose.
- **Source:** `osolmaz/ai-smell` (reviewed at `cca765e3`), plus the composite
  detector results published in `conorbronsdon/avoid-ai-writing` `PROOF.md`
  (reviewed at `40328bd2`).
- **Result:** did not separate the ground-truth groups. The `ai-smell`
  ground-truth set contains eighteen documents, which is far too few to
  generalize from in either direction.
- **Decision:** **kept as a readability observation only**, as
  `ST.UNIFORM_RHYTHM`, P2, low evidence strength, `threshold_status:
  provisional`. Its `note` field says so. It must never contribute to a claim
  about how the text was produced, and the fix must never be "vary sentence
  length" applied mechanically.

### Em-dash frequency points the wrong way

- **Hypothesis:** heavy em-dash use indicates generated prose.
- **Source:** `avoid-ai-writing` `PROOF.md`, which found its em-dash signal
  behaved opposite to the project's original assumption on its own corpus.
- **Result:** rejected as a signal.
- **Decision:** **kept as `ST.DASH_DENSITY`, a punctuation-readability check
  only.** The threshold is roughly one dash per 120 words, `provisional`. The
  fix is explicitly *not* "remove em dashes"; it is to compare against the
  author's own established rate and fix stacking. A universal "target zero em
  dashes" stance is an anti-goal of this project.

### Vocabulary blacklists fire on human prose

- **Hypothesis:** a stock-vocabulary list separates generated from human text.
- **Source:** `avoid-ai-writing` `PROOF.md`, whose vocabulary tier fired
  slightly *more* often on the human writing in its dataset.
- **Result:** rejected as a classifier. Retained as an editing signal, because a
  cluster of stock terms genuinely does displace concrete explanation.
- **Decision:** `LX.STOCK_VOCAB_CLUSTER` requires **three distinct terms in one
  paragraph**, not one word anywhere. `LX.STOCK_VOCAB_REPEAT` requires three
  occurrences of the same term across a document. Single-word bans are an
  anti-goal.

### Bolted-on benefit clauses

- **Hypothesis:** trailing benefit clauses ("…, making it easier to ship")
  concentrate in generated marketing prose.
- **Source:** `ai-smell`.
- **Result:** pointed in the wrong direction on that corpus.
- **Decision:** **rejected as a standalone rule.** The overlapping, better-
  motivated case — an interpretation glued onto a sourced fact — is covered by
  `LX.PARTICIPLE_TAIL`, which is justified editorially rather than statistically.

### `while` / `whereas` contrast hinges

- **Hypothesis:** contrastive subordinators mark generated argumentation.
- **Source:** `ai-smell`.
- **Result:** too rare to measure in that corpus.
- **Decision:** **rejected.** No rule. The rhetorical pattern worth catching is
  the false contrast itself, which `RH.FALSE_CONTRAST` handles within a
  sentence or across an adjacent pair, and marks as requiring judgment.

### Embedding-based sentence cohesion

- **Hypothesis:** adjacent-sentence similarity from a sentence-embedding model
  captures the cohesion that generated prose lacks.
- **Source:** `ai-smell`, using full-sentence MiniLM embeddings.
- **Result:** did not capture the intended property there.
- **Decision:** **not adopted in the default checker**, which stays
  zero-dependency. A cheap lexical proxy ships instead as
  `ST.SENTENCE_CONTINUITY`: the share of adjacent sentence pairs sharing no
  content word and opening with no anaphoric link. It is P2, low evidence,
  document-scope, `provisional`, and skipped in `technical-docs` where fact
  lists legitimately look discontinuous. It is a review candidate, never a
  per-paragraph conviction.

### Composite "AI probability" scores

- **Hypothesis:** a weighted composite of surface features classifies
  authorship.
- **Source:** `avoid-ai-writing` `PROOF.md`, on its own published corpus.
- **Result:** weak classification performance.
- **Decision:** **permanently rejected.** No `probability_ai`, `human_score`,
  `AI_ONLY`, or 0–100 field appears in any output schema in this repository.
  The JSON schema is checked for their absence in `tests/test_catalog_contract.py`.

### First corpus baseline: human prose written before November 2022

- **Hypothesis:** the provisional thresholds, set against this repository's own
  prose, stay quiet on human prose that predates the habits they target.
- **Corpus:** 48 documents, 88,656 scanned prose words, captured 2026-11-13:
  13 `technical-docs`, 12 `essay-blog`, 13 `legal-policy`, 10 `general-prose`.
  Provenance and checksums are in `corpus/manifest.json`. Eight of the ten
  general-prose documents are Wikipedia articles. There is no academic,
  marketing, creative, or generated sample.
- **Implementation:** `scripts/corpus_measure.py`, run on the 2.4.0 detectors.
  Full tables and example spans are in `corpus/results/2026-11-13-baseline.md`.
- **Result:** findings per 1,000 words were 1.96 in essays, 1.79 in general
  prose, 0.80 in legal text, and 0.68 in technical documentation.
  `RH.PHRASE_TRIAD` produced 72 of the 117 findings; its trigger of two per
  document was met by 26 of the 48 documents. `ST.HEADING_DENSITY`,
  `ST.DASH_DENSITY`, `ST.UNIFORM_RHYTHM`, and `ST.SENTENCE_CONTINUITY` crossed
  no threshold. The three rules added in 2.4.0 produced no candidate, which
  shows they are quiet on this sample and nothing about what they catch.
- **Known false positives:** serial clauses under `RH.PHRASE_TRIAD`; a
  sentence-opening `Of course,` under `FP.META_NARRATION` at P0, in four
  documents; the `period.` pattern of `RH.APHORISM_CLOSER`, a noun in all three
  matches; template syntax such as `{{ page.title }}` under
  `FP.UNFILLED_PLACEHOLDER`; runs of sentences opening with `The` under
  `RH.FORCED_SYMMETRY` in five of ten general-prose documents; and FAQ or API
  sibling headings under `ST.HEADING_FRAME_REPEAT`.
- **Decision:** **no threshold changed, 2026-11-13, version 2.4.0.** No
  register reaches the 50 documents asked for below, so every threshold stays
  `provisional`. The false positives above are open: each needs a narrower
  detector with a test, a profile carve-out with a test, or a recorded decision
  to keep it. The write-up recommends tightening `RH.PHRASE_TRIAD`,
  `RH.FORCED_SYMMETRY` in general prose, and the `ST.HEADING_FRAME_REPEAT`
  detector, and holding the rest.

## Unvalidated editorial hypotheses

Rules adopted on an editorial argument, with a research association behind them
and no measurement of their own. They are not failed experiments, because no
experiment on this skill has been run. They are not findings either.

### Narrative checks adapted from StoryScope

- **Rules:** `ST.NARRATIVE_THEME_REDUNDANCY`, `ST.NARRATIVE_EMOTION_REDUNDANCY`,
  `ST.NARRATIVE_DECORATIVE_MIRRORING`, `ST.NARRATIVE_FORCED_CLOSURE`,
  `ST.NARRATIVE_INFORMATION_TIMING`. Judgment-only, low evidence strength, with
  no threshold of any kind.
- **Motivation:** Russell et al., *StoryScope: Investigating idiosyncrasies in AI
  fiction* (arXiv 2604.03136v6). On a parallel corpus built from 10,272
  published stories and generations from five model versions, narrative-only
  features gave a binary macro-F1 of 93.2, against 96.0 with style features
  added. On 278 stories edited span by span, the same measure moved from 95.5
  to 93.9. Macro-F1 is a classifier statistic over a corpus. It is not a
  per-document probability, and it is not a measurement of this skill, which
  the study never tested.
- **Associations the checks draw on** (model-assigned prevalence, generated
  versus published): narratorial thematic commentary 77% versus 52%;
  philosophical dialogue 59% versus 34%; embodied emotional expression 81%
  versus 38%; explicit emotion labels 8% versus 29%; olfactory detail 82%
  versus 57%; no subplot 79% versus 57%; resolution by internal understanding
  47% versus 27%.
- **Why none of these is a threshold:** every feature is common in the
  published stories too. Half of them carry thematic commentary and more than
  half have no subplot, and both groups score high on thematic unity. The study
  measures association with a source; it does not show that reversing a feature
  improves a story or keeps its author's intent.
- **Corpus limits:** published English fiction against generations from
  reverse-engineered prompts, with no comparable drafting and revision on the
  generated side. Features were assigned mostly by models; the human validation
  covers 240 story-feature items across 12 stories and two annotators. The
  study's rarity measure is defined inside its own feature space and is no
  measure of quality or originality. Nothing here transfers on that evidence to
  business prose, other languages, poetry, memoir, or heavily revised
  collaborative fiction.
- **Decision:** **adopted as editorial hypotheses, 2026-09-18, version 2.2.0.**
  Each check asks whether a passage repeats work the story has already done,
  which is an editing question with or without the study. The agent cases in
  `evals/evals.json` (E13 onward) exist to test them and have not been run. A
  check that over-edits, misreads intentional style, or costs more than its
  findings are worth gets narrowed or removed, and the result is recorded here.

### Interpretations of StoryScope rejected outright

- **Sensory-word limits.** No count of smell words and no ceiling on sensory
  modalities. A smell can be the clue.
- **Universal ambiguity.** No pushing endings toward the unresolved, the
  cynical, or the abrupt. An earned reconciliation is an ending.
- **Forced nonlinear structure.** No flashback, delayed reveal, or subplot
  recommended because a story lacks one. Most published stories in the study
  were linear enough to lack them too.
- **Named-reference insertion.** No title, author, brand, or place added to
  resemble the published corpus. That would be an invented fact.
- **Emotion-label quotas.** No conversion of bodily expression into labels, or
  of labels into bodily expression, as a policy in either direction.
- **Per-model corrective presets.** The study covers particular model versions,
  and an attribution feature is not an editing instruction. The skill does not
  infer a model and does not apply a recipe for one.
- **The classifier itself.** No StoryScope classifier, embedding model,
  feature export, or "humanness" score, here or as a release gate for the evals.
- **Cross-story template analysis.** Deferred. `ST.CROSS_FILE_TEMPLATE` compares
  surface n-grams and is not a narrative-diversity measure.

### Lessons from declauding v0.13.0

- **Source:** the tagged skill and its register, exceptions, preservation, and
  fresh-eyes references in `oaustegard/claude-skills`, reviewed 2026-11-11.
- **Adopted:** a nonfiction purpose check, contextual review beyond regex
  matches, a reading of current documentation without its change history, and
  explicit review of qualifiers and over-compression. These extend the existing
  editorial workflow; they introduce no detection threshold.
- **Observed locally:** version 2.2.0 emitted no warning when a superlative was
  weakened, simultaneous timing was dropped, or `only` moved away from `if`
  while preserving token counts. Version 2.3.0 adds limited qualification
  warnings, with regression cases for those losses and controls for protected
  text and legitimate rewrites.
- **Limits:** marker counts cannot establish what a qualifier modifies. The
  regression suite includes that blind spot. The new agent eval cases have no
  comparative run against the baseline, so improved editing quality is not yet
  established. Upstream measurements were not reproduced here.
- **Not adopted:** automatic in-place edits from a file mention, automatic
  restructuring, model-specific corrective presets, authorship implications,
  vocabulary bans, embeddings, API dependencies, and mandatory review hooks.
  Those would change this project's scope or portability without evidence from
  its own evals. The new workflow uses reader comprehension as its criterion.

### Short-form register devices (2.4.0)

- **Rules:** `RH.SELF_ANSWERED_QUESTION`, `RH.MIRRORED_PAIR`,
  `RH.ELABORATING_FRAGMENT`, and new patterns in `LX.ENGAGEMENT_HOOK`
  (`the more I sit with it`, a verbless announced count), `LX.PERFORMATIVE_HONESTY`
  (the question form), `RH.APHORISM_CLOSER` (`It's that simple`,
  `That changes everything`), and `RH.FALSE_CONTRAST` (a closed list of stock
  idioms).
- **Motivation:** two short posts, written in a punchy opinion register,
  produced only false-contrast candidates under 2.3.1 although nearly every
  paragraph used one of these devices. That is an editorial observation about
  two texts. It is not a measurement, and it says nothing about who writes
  this way: every device here is ordinary in speeches, columns, and FAQs.
- **Basis:** editorial argument only. No corpus measurement has been run for
  any of these rules. A register-balanced measurement is being prepared
  separately; until its results are recorded here, the rules are unvalidated
  hypotheses.
- **Precision measures taken instead:** the question and mirror rules count
  recurrence across a document rather than firing on one use; the creative
  profile skips all three new rules; the patterns exclude FAQ shapes
  (question-word and auxiliary openers, bolded labels, question headings,
  `Q:`/`A:` transcripts), parallel sentences that report different facts, list
  items, single fragments, and plain "not X but Y" corrections. Each exclusion
  has a negative fixture. Over this repository's Markdown and the 39 eval
  input files that predate 2.4.0, the 2.4.0 checker produced no candidate from the
  new rules or patterns, under the detected profile or under forced
  `general-prose`. The new short-form controls under `evals/files/short-form/`
  produce no finding from them either; a test holds that.
- **Rejected:** a bare "not X but Y" detector, which would flag ordinary
  corrections; lowering `ST.FRAGMENT_RUN`'s 40-word paragraph floor, which would
  start flagging terse status notes and steps; and any count of question marks
  or short sentences per post.
- **Decision:** **adopted as editorial hypotheses, 2026-11-13, version 2.4.0.**
  The agent cases E47–E51 in `evals/evals.json` exist to test them and have not
  been run. A rule that over-flags a register gets narrowed, relaxed in that
  profile, or removed, and the result is recorded here.

## Provisional thresholds currently shipping

Every number below is a starting policy calibrated against this repository's own
prose and the fixtures in `tests/fixtures/`, not against a register-balanced
corpus. Each is marked `"threshold_status": "provisional"` in the registry.

| Rule | Threshold | Basis | What would make it calibrated |
|------|-----------|-------|-------------------------------|
| `RH.TRIAD_DENSITY` | > 0.25 triads per sentence | Editorial judgment | Rates across ≥ 50 documents in ≥ 3 registers |
| `RH.PHRASE_TRIAD` | ≥ 2 per document | Lead from `ai-smell` | Same, plus a human-labeled filler/not-filler set |
| `RH.FORCED_SYMMETRY` | ≥ 3 consecutive same-opener sentences | Editorial judgment | Speech and marketing controls |
| `RH.MIRRORED_PAIR` | ≥ 2 mirrored pairs per document; echo halves 3–12 words and equal length, half the positions shared; negated replies ≤ 20 words | Editorial judgment | Speech, essay, and documentation controls; a labeled device/not-device set |
| `RH.SELF_ANSWERED_QUESTION` | ≥ 2 per document; question of 1–3 words after a determiner or conjunction | Editorial judgment | FAQ, tutorial, column, and transcript controls |
| `ST.HEADING_DENSITY` | < 60 prose words per heading | Editorial judgment | Reference-doc controls |
| `ST.HEADING_FRAME_REPEAT` | ≥ 3 same-level headings sharing a first word | Lead from `ai-smell` | Same-level sibling sampling across doc sets |
| `ST.LABELED_BULLET_RUN` | > 0.5 labeled bullets per section, ≥ 4 bullets | Lead from `ai-smell` | Glossary and API-reference controls |
| `ST.DASH_DENSITY` | > 1 per 120 words | Style-guide convention | Author-relative baseline, not an absolute |
| `ST.UNIFORM_RHYTHM` | stdev < 4 words, ≥ 8 sentences | Editorial judgment | See the negative result above |
| `ST.FRAGMENT_RUN` | ≥ 3 consecutive sentences of ≤ 5 words | Editorial judgment | Creative and chat controls |
| `ST.SENTENCE_CONTINUITY` | > 0.75 of adjacent pairs discontinuous | Cheap proxy | See the negative result above |
| `ST.CROSS_FILE_TEMPLATE` | phrase in ≥ 3 files | Editorial judgment | Corpus of intentional house styles |

## Recording a new result

Add an entry with: hypothesis, motivation, corpus and register composition,
implementation, result, known false positives, decision (adopt / revise / defer
/ reject), and the date and commit. A rejected hypothesis stays in this file; do
not delete an entry because the rule was removed.
