# Corpus

A provenance-aware manifest for false-positive research and threshold
calibration. **No third-party text is committed here.** `manifest.json` records
where each document came from, its licence, and a SHA-256 of the exact bytes
that were measured, so a result can be reproduced without redistributing prose
this project has no right to redistribute.

## Why a manifest instead of the text

Two reasons. Licensing: most human-written prose worth measuring is not ours to
ship. Reproducibility: a README captured at an immutable tag is a stable
artifact; the same README captured from `main` a year later is not.

## Fields

| Field | Meaning |
|-------|---------|
| `id` | Stable identifier used in results and negative-results entries |
| `register` | One of the eight context profiles; the primary analysis dimension |
| `authorship` | `human-pre-llm`, `human-post-llm`, `generated`, or `unknown` |
| `source_url` | Immutable where possible — a tag, a permalink, an archive URL |
| `licence` | The upstream licence |
| `sha256` | Of the exact bytes measured |
| `word_count` | Of the scanned prose, not the file |
| `local_path` | Only for text this repository owns; `null` otherwise |
| `notes` | Capture conditions and anything that limits the sample |

## Rules for using it

- **Register is a primary dimension, not a footnote.** An aggregate
  false-positive rate hides that a rule is harmless in essays and noisy in
  documentation. Report per register.
- **`authorship` is metadata for research, never an output.** No script reads
  it, and no report may cite it.
- **State the sample size and the date.** A generated sample is a sample of one
  model on one day with one prompt style.
- **A tiny or register-mismatched sample supports no published claim.** The
  reference projects' own results, recorded in
  `references/negative-results.md`, are the argument for that rule.

## Groups worth collecting

Pre-LLM technical READMEs and docs at immutable tags; pre-LLM essays and blog
posts; human-written legal and policy text with clear provenance; human-written
academic prose; user-contributed false-positive snippets where permission
allows; generated samples from several model families and prompt styles, dated;
and this repository's own prose as a self-scan set.

The self-scan set is the only group currently populated, through
`self-scan-budget.json` rather than this manifest.
