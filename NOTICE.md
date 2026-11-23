# NOTICE

llm-ism-rewriter
Copyright 2026 jrajasekera

Licensed under the Apache License, Version 2.0. See `LICENSE`.

This file records the provenance of material in this repository so that
downstream users can meet the attribution terms of every upstream source.
It is a provenance record, not legal advice.

## File-level provenance

| Path | Origin | Relationship to source |
|------|--------|------------------------|
| `SKILL.md` | Original; see *declauding* and *humanizer* below | Written for this project; nonfiction workflow informed by declauding; the `embedded` output and the default-choice test follow ideas in humanizer. |
| `references/patterns.md` | See *Wikipedia* below | Category names and several example words paraphrased from a CC BY-SA 4.0 source. No sentences copied. Sections B9, C9, C10, and D6 follow pattern leads from humanizer; text and examples written for this project. |
| `references/contexts.md` | Original; see *humanizer* below | Written for this project. The informal-text section follows an idea in humanizer. |
| `references/narrative-review.md` | See *StoryScope* below | Editorial checks adapted from published research findings. All text, definitions, and examples written for this project. |
| `references/nonfiction-review.md` | See *declauding* below | Original instructions adapting purpose-first review, newcomer reading, and overcorrection checks. The reply review follows an idea in humanizer. |
| `references/examples.md` | Original | All before/after pairs written for this project. |
| `references/voices.md` | Original; see *humanizer* below | Written for this project. The list of details to keep follows an idea in humanizer. |
| `references/rewrite-invariants.md` | Original | Written for this project. |
| `references/detector-map.md` | Original | Written for this project. |
| `references/negative-results.md` | Partly derived | Records published findings from `ai-smell` and `avoid-ai-writing` as cited leads. Summaries are paraphrased; no text copied. |
| `references/rules.json` | Original | Rule IDs, thresholds, and regexes written for this project. |
| `scripts/*.py` | Original | Independently implemented. No code from any referenced project was reused. |
| `tests/**` | Original | Fixtures written for this project. |
| `evals/**` | Original | Cases and input files, the three long stories included, written for this project. No story from any research corpus is used. |
| `LICENSE` | Apache Software Foundation | Verbatim Apache License 2.0 text. |

## Wikipedia, *Signs of AI writing*

<https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>
Licensed CC BY-SA 4.0 by its contributors.

The pattern catalog in `references/patterns.md` was informed by that page:
the idea of grouping tells into fingerprints, lexical clichés, rhetorical
structures, and formatting patterns, and a subset of the example words it
lists (for instance *delve*, *tapestry*, *testament to*). Individual words
and factual observations are not themselves copyrightable, and every
explanation, tier assignment, fix, threshold, and regex in this repository
was written independently.

Because the categories are derived, keep this attribution with
`references/patterns.md` in any redistribution. If you copy prose from the
Wikipedia page itself rather than this paraphrase, CC BY-SA 4.0 share-alike
terms attach to that copied text.

## Simon Willison, LLM cliché highlighter

<https://tools.simonwillison.net/llm-cliche-highlighter> (Apache-2.0)

Informed the rhetorical-tic families and the idea of highlighting candidate
spans rather than scoring a document. No code, regexes, or word lists were
copied.

## osolmaz/ai-smell

<https://github.com/osolmaz/ai-smell> (reviewed at `cca765e3`)

A corpus study of structural features in LLM prose. It supplied research
*leads* — labeled-bullet runs, multiword phrase triads, repeated heading
frames, sentence-continuity measures — and, equally usefully, a set of
hypotheses that did not hold on its corpus. Those are recorded in
`references/negative-results.md` with their limitations. No thresholds were
adopted as production defaults on the strength of that corpus alone, and no
code was reused.

## Russell et al., *StoryScope*

Jenna Russell, Rishanth Rajendhran, Chau Minh Pham, Mohit Iyyer, and John
Wieting, *StoryScope: Investigating idiosyncrasies in AI fiction*, COLM 2026.
<https://arxiv.org/abs/2604.03136v6>

The five `ST.NARRATIVE_*` rules, the catalog's section F, and
`references/narrative-review.md` adapt reported associations from that paper
into editorial checks. The adaptation is original: the rule definitions, the
permission limits, the examples, and the eval stories were written for this
project. No research code, feature taxonomy, prompt, classifier, or data was
copied or reimplemented, and no story from the paper's corpus appears in this
repository. The paper's human stories come from Books3, and its own ethics
statement discusses that corpus's copyright status; do not import them as test
material. `references/negative-results.md` records what the paper does and does
not support.

## conorbronsdon/avoid-ai-writing

<https://github.com/conorbronsdon/avoid-ai-writing> (reviewed at `40328bd2`)

An adjacent skill plus JavaScript detector. It supplied engineering
*practices* — a rule/detector contract, a preservation validator, corpus
provenance manifests, and a false-positive intake workflow — which this
repository reimplemented from scratch in Python. Its published corpus
results are summarized in `references/negative-results.md`. No code, rules,
or fixtures were copied.

## blader/humanizer

<https://github.com/blader/humanizer> (MIT, reviewed at `a32f244`, v4.0.0)

An adjacent skill built from the same Wikipedia source. Its pattern
descriptions were the lead for six rules added in 2.5.0
(`RH.PHANTOM_OBJECTION`, `LX.GAP_SPECULATION`, `LX.PART_STANDIN`,
`LX.DEPTH_SIGNAL`, `ST.DOCUMENT_SELF_DESCRIPTION`, `RH.REDUNDANT_CONTEXT`), for
new patterns in three existing rules, and for several judgment notes in the
catalog. Its output modes informed the `embedded` output. Its treatment of informal
text and of replies informed the informal-text guard and the reply review. Its
account of why formulaic prose reads as it does informed the default-choice
test. The list of voice-carrying details in `references/voices.md` follows the
same source.

The phrase lists of `RH.PHANTOM_OBJECTION`, `LX.GAP_SPECULATION`,
`LX.PART_STANDIN`, and `LX.DEPTH_SIGNAL` are adapted from humanizer's lists:
each is a subset of the phrases it names, narrowed for this checker. Humanizer
is Copyright (c) 2025 Siqi Chen and distributed under the MIT License, whose
text is at <https://github.com/blader/humanizer/blob/main/LICENSE>. This
project's rule definitions, thresholds, instructions, examples, and fixtures
were written independently; no upstream sentence or example was copied. Four of its behaviours were deliberately not adopted because they
conflict with this project's contract: adding a detail the editor believes
true, removing every dash, returning a first draft ahead of the final text,
and dating a text to decide how it was written. `references/negative-results.md`
records the adoption and the rejections.

## Oskar Austegard, declauding

<https://github.com/oaustegard/claude-skills/releases/tag/declauding-v0.13.0>
(MIT, reviewed at tag `declauding-v0.13.0`).

The skill and its register, exceptions, preservation, and fresh-eyes references
informed the nonfiction workflow, the claim-by-claim review, and the safeguards
against over-compression. Its preservation checker supplied the idea of checking
qualifying constructions in addition to isolated words. This project's code,
instructions, examples, and eval inputs were written independently; no upstream
code, regex, prose, or fixture was copied. The adaptation retains this project's
edit-scope limits, genre profiles, and ban on authorship inference. It imports
no model profiles, API calls, embeddings, hooks, or measured performance claims.
