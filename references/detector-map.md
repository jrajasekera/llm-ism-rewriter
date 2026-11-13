# Detector map

What the script can decide, what it can only surface, and what it must never
pretend to measure. `references/rules.json` is canonical; this file records the
coverage contract. `scripts/build_catalog.py --check` fails if a rule here does
not exist, or if a registry rule is missing from this file.

Tier vocabulary is shared with `SKILL.md`, `references/patterns.md`, and the
checker's output: **fingerprint**, **cliche**, **structural**, **clarity**. Renaming
a tier means changing all four, and `build_catalog.py --check` will say so.

Three groups:

1. **Directly executable** — a deterministic implementation decides the finding.
2. **Partially executable** — the script surfaces a candidate; a reader decides
   whether it is a finding.
3. **Judgment-only** — requires reading for meaning. No regex approximation
   exists, and adding one would produce noise rather than signal.

## 1. Directly executable

A single match is enough, and the span is unambiguous.

| Rule | Detector | Why it can stand alone |
|------|----------|------------------------|
| `FP.CHATBOT_RESIDUE` | regex | Interface courtesy has no place in standalone prose. |
| `FP.KNOWLEDGE_CUTOFF` | regex | A training disclaimer is never the author's claim. |
| `FP.META_NARRATION` | regex | Narrating the deliverable is a response artifact. |
| `FP.PROMPT_LEAKAGE` | regex | An imperative aimed at an editor is leaked scaffolding. |
| `FP.TOOL_MARKUP` | regex | Serialization fragments are not prose. |
| `FP.UNFILLED_PLACEHOLDER` | regex | A template slot is objectively unfilled. |
| `LX.SYCOPHANCY` | regex | Praise addressed to a non-reader. |
| `CL.WORDY_PHRASE` | regex | A mechanical substitution with no semantic risk. |

`CL.WORDY_PHRASE` is executable but stays out of the boilerplate density label:
it is a clarity edit, not a signal about how the text was produced.

## 2. Partially executable

The script reports these; recurrence, genre, and literal sense decide them.

| Rule | Detector | What the script cannot decide |
|------|----------|-------------------------------|
| `LX.STOCK_VOCAB_CLUSTER` | lexicon_cluster | Whether each term is literal (*robust standard errors*) or padding. |
| `LX.STOCK_VOCAB_REPEAT` | repetition | Whether the repeated term is the document's defined term. |
| `LX.FIGURATIVE_LANDSCAPE` | regex | Whether *landscape* is geographic. |
| `LX.STOCK_TRANSITION` | regex | Whether *Note that* precedes a genuine caveat. |
| `LX.INFLATED_SIGNIFICANCE` | regex | Whether the document states the effect the clause claims. |
| `LX.PROMOTIONAL_REGISTER` | regex | Whether the register was commissioned. |
| `LX.COPULA_AVOIDANCE` | regex | Whether *serves as* is a term of art in the domain. |
| `LX.VAGUE_AUTHORITY` | regex | Whether a source appears in the next sentence or the reference list. |
| `LX.PARTICIPLE_TAIL` | regex | Whether the interpretation is supported elsewhere in the document. |
| `LX.ENGAGEMENT_HOOK` | regex | Whether a hook is the genre's job (a headline, a lede). |
| `LX.PERFORMATIVE_HONESTY` | regex | Whether the document is already first-person and candid. |
| `LX.ASSOCIATION_VAGUENESS` | regex | Whether the phrase is a legal term of art. |
| `RH.FALSE_CONTRAST` | regex | **The central judgment**: whether a reader plausibly holds the rejected belief. |
| `RH.TRIAD_DENSITY` | metric | Whether there are exactly three real items. |
| `RH.PHRASE_TRIAD` | regex | Whether the third clause carries a fact. |
| `RH.FORCED_SYMMETRY` | metric | Whether the anaphora is deliberate rhetoric. |
| `RH.MIRRORED_PAIR` | metric | Whether each half of the pair carries a fact, or the pair says one thing twice. |
| `RH.APHORISM_CLOSER` | regex | Whether the closer lands a point the paragraph earned. |
| `RH.GENERIC_INTRO` / `RH.GENERIC_OUTRO` | regex | Whether a conventional section is mandated by the genre. |
| `RH.SELF_ANSWERED_QUESTION` | regex (counted per document) | Whether the reader would genuinely ask the question, as in an FAQ. |
| `RH.ELABORATING_FRAGMENT` | regex | Whether the fragment carries a qualification the sentence could not. |
| `ST.HEADING_DENSITY` | metric | Whether the document is reference material. |
| `ST.HEADING_FRAME_REPEAT` | metric | Whether parallel headings are an intentional outline. |
| `ST.HEADING_RHETORIC` | regex | Whether the section under the heading delivers content. |
| `ST.LABELED_BULLET_RUN` | metric | Whether the items are genuinely parallel and scannable. |
| `ST.DASH_DENSITY` | metric | The author's own established punctuation habit. |
| `ST.UNIFORM_RHYTHM` | metric | Whether the uniformity follows from uniform content. |
| `ST.FRAGMENT_RUN` | metric | Whether one short sentence earns its emphasis. |
| `ST.SENTENCE_CONTINUITY` | metric | Whether the passage is a fact list, where discontinuity is correct. |
| `ST.CROSS_FILE_TEMPLATE` | metric (project mode only) | Whether the shared template is house style. |

`ST.CROSS_FILE_TEMPLATE` is evaluated only by
`scripts/llm_ism_project_check.py`. `scripts/llm_ism_check.py` skips it, because
a single file carries no evidence for it.

## 3. Judgment-only

These have no detector and must never acquire a broad regex.

| Rule | Question a reader has to answer |
|------|--------------------------------|
| `FP.FABRICATION_TELL` | Does every attributed source exist and resolve? |
| `RH.LOW_INFORMATION_RESTATEMENT` | What does this paragraph add that the last one did not? |
| `ST.OPENING_IDENTITY` | Does the opening say what the thing *is*? |
| `ST.TABLE_MISUSE` | Is this table holding tabular data or reformatted prose? |
| `CL.SEMANTIC_EDIT` | Does naming the actor make the sentence clearer without changing the claim? |
| `ST.NARRATIVE_THEME_REDUNDANCY` | Does this passage explain a meaning the story already made explicit, and add nothing? |
| `ST.NARRATIVE_EMOTION_REDUNDANCY` | Are several descriptions doing one piece of emotional work? |
| `ST.NARRATIVE_DECORATIVE_MIRRORING` | Does the description restate one emotional reading, or carry place, action, or a clue? |
| `ST.NARRATIVE_FORCED_CLOSURE` | Does narration after the ending only explain it again, or override the story's uncertainty? |
| `ST.NARRATIVE_INFORMATION_TIMING` | Does this explanation repeat or pre-empt what the reader learns elsewhere? |

The five `ST.NARRATIVE_*` rules form the `narrative` family. They apply to prose
fiction alone, under `references/narrative-review.md`, and the registry sets the
family to `full` in `creative` and `skip` in the other seven profiles. No word
list can stand in for them: "realized", "lesson", "rain", and "fear" appear in
repetition and in development alike. The checker emits nothing for them, and the
validator does not run them; narrative preservation is an agent review.

Related judgments with no rule at all, because they are properties of the
*rewrite* rather than of the source:

- Whether a hedge carries real uncertainty or is padding.
- Whether the author's first-person voice should stay (it should, by default).
- Whether two paragraphs could be reordered without breaking the argument.
- Whether a technical word is being used literally or promotionally.
- Whether the revision compresses a relationship until it is harder to read.
- Whether a qualifier now modifies a different claim despite unchanged counts.
- Whether a plain "not X but Y" corrects a belief someone held. `RH.FALSE_CONTRAST`
  matches the negated reframe and a short list of stock idioms; a bare
  correction is ordinary English, and a broad pattern would flag every one.
- Whether a short-form post is built from setup-and-punchline paragraphs, or
  opens on a canned personal hook. No pattern reaches either without also
  reaching the plain writing it imitates.

`nonfiction-review.md` applies the existing catalog to document purpose and to
headings, openings, and closers in context. Its newcomer reading and contradiction
review require the current text; no phrase list determines whether the reader
has enough context. These are review procedures, not new checker rules.

## The contract

- Adding a rule to `references/patterns.md` does **not** require a detector.
- Adding a detector **does** require a registry rule and a catalog anchor.
- A rule whose `detector` is `regex`, `lexicon_cluster`, `repetition`, or
  `metric` must have a working implementation, positive fixtures, and at least
  two negative fixtures under `tests/fixtures/`.
- A rule whose `detector` is `llm_judgment` must carry a `judgment_prompt` and
  must not carry `patterns`, `terms`, a `metric`, or any threshold.
- A judgment-only family holds no executable rule, and exactly one profile
  enables it.
- A `threshold_status` of `provisional` must be recorded in
  `references/negative-results.md` with its corpus limitations.

`scripts/build_catalog.py --check` enforces every item on that list.
