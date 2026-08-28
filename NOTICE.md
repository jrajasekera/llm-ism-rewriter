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
| `SKILL.md` | Original | Written for this project. |
| `references/patterns.md` | See *Wikipedia* below | Category names and several example words paraphrased from a CC BY-SA 4.0 source. No sentences copied. |
| `references/contexts.md` | Original | Written for this project. |
| `references/examples.md` | Original | All before/after pairs written for this project. |
| `references/voices.md` | Original | Written for this project. |
| `references/rewrite-invariants.md` | Original | Written for this project. |
| `references/detector-map.md` | Original | Written for this project. |
| `references/negative-results.md` | Partly derived | Records published findings from `ai-smell` and `avoid-ai-writing` as cited leads. Summaries are paraphrased; no text copied. |
| `references/rules.json` | Original | Rule IDs, thresholds, and regexes written for this project. |
| `scripts/*.py` | Original | Independently implemented. No code from any referenced project was reused. |
| `tests/**` | Original | Fixtures written for this project. |
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

## conorbronsdon/avoid-ai-writing

<https://github.com/conorbronsdon/avoid-ai-writing> (reviewed at `40328bd2`)

An adjacent skill plus JavaScript detector. It supplied engineering
*practices* — a rule/detector contract, a preservation validator, corpus
provenance manifests, and a false-positive intake workflow — which this
repository reimplemented from scratch in Python. Its published corpus
results are summarized in `references/negative-results.md`. No code, rules,
or fixtures were copied.
