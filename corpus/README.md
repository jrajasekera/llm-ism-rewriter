# Corpus

A provenance-aware manifest for false-positive research and threshold
calibration. **No third-party text is committed here.** `manifest.json` records
where each document came from, its licence, and a SHA-256 of the exact bytes
that were measured, so a result can be reproduced without redistributing prose
this project has no right to redistribute.

## Why a manifest instead of the text

Licensing is the first reason: most human-written prose worth measuring is not
ours to ship. Reproducibility is the second: a README captured at an immutable
tag is a stable artifact; the same README captured from `main` a year later is
not.

## Fields

| Field | Meaning |
|-------|---------|
| `id` | Stable identifier used in results and negative-results entries |
| `register` | One of the eight context profiles; the primary analysis dimension |
| `authorship` | `human-pre-llm`, `human-post-llm`, `generated`, or `unknown` |
| `title`, `author` | What the document is and who wrote it, as the source credits it |
| `written` | When the text was written or last changed, as an ISO date or year. For `human-pre-llm` it is before November 2022 |
| `source_type` | `git-tag`, `git-commit`, `wayback-snapshot`, `wikipedia-oldid`, or `rfc` |
| `source_url` | Immutable where possible: a tag, a commit, a permalink, an archive URL |
| `licence` | The upstream licence |
| `source_sha256` | Of the bytes fetched from `source_url` |
| `sha256` | Of the exact bytes measured: the UTF-8 text that `extract` produces |
| `word_count` | Of the scanned prose, not the file, as the checker counted it when recorded |
| `captured` | The date the source bytes were fetched and their checksums recorded |
| `extract` | The recipe from source bytes to measured text; see below |
| `local_path` | Only for text this repository owns; `null` otherwise |
| `notes` | Capture conditions and anything that limits the sample |

`extract` holds a `format` (`markdown`, `text`, `html`, or `wikitext`) and
optional steps, applied in this order: `source_start_after` and
`source_end_before` cut the raw source; the format conversion runs;
`drop_lines` removes lines matching each regular expression;
`quote_indented` turns lines indented by at least that many spaces into block
quotes, because plain-text editions set quotations off that way;
`start_after` and `end_before` cut the converted text at the first match;
`max_words` keeps whole blank-line-separated blocks while the running count
stays within the limit, never cutting inside a fenced code block. A gzip body
is decompressed first. The conversions are deliberately small and live in
`scripts/corpus_measure.py`; changing one changes `sha256`, which is the point.

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

## What is collected

The manifest holds 48 human-written documents from before November 2022, in
four registers:

| Register | Documents | Sources |
|----------|----------:|---------|
| `technical-docs` | 13 | READMEs, guides, and API reference at release tags or commits from twelve projects, plus one RFC |
| `essay-blog` | 12 | Public-domain essays from Project Gutenberg, and blog essays by five authors |
| `legal-policy` | 13 | Licence texts, platform terms, a code of conduct, Federal Register rules, a UK Act, an IETF process RFC, and a Wikipedia policy |
| `general-prose` | 10 | Eight Wikipedia articles at fixed revisions and two public-domain popular-science lectures |

Sources without a pinned original are pinned through Wayback Machine snapshots
in `id_` mode, which serves the archived bytes without the archive's toolbar:
Project Gutenberg files, which are regenerated in place; personal sites with no
public source history; the UK legislation site, whose page chrome changes; and
govinfo, whose Federal Register pages carry an obfuscated email address that is
re-encoded on every response, so two fetches never match.

Still missing from the groups below: academic prose, marketing copy, email and
chat, fiction, user-contributed false-positive snippets, and every generated
sample. This repository's own prose is measured separately, through
`self-scan-budget.json`.

## Groups worth collecting

Pre-LLM technical READMEs and docs at immutable tags; pre-LLM essays and blog
posts; human-written legal and policy text with clear provenance; human-written
academic prose; user-contributed false-positive snippets where permission
allows; generated samples from several model families and prompt styles, dated;
and this repository's own prose as a self-scan set.

## Measuring

```bash
python3 scripts/corpus_measure.py                       # fetch what is missing, then report
python3 scripts/corpus_measure.py --offline             # cache only; no network
python3 scripts/corpus_measure.py --offline --format json --output corpus/results/DATE-NAME.json
python3 scripts/corpus_measure.py --offline --format markdown   # tables for a write-up
python3 scripts/corpus_measure.py --only gp-wiki-pencil         # one document
```

Fetched bytes go to `corpus/cache/`, which is gitignored. Every run verifies
both checksums for every selected document before it measures any of them, and
exits 1 with `INTEGRITY FAILURE` on a mismatch. Exit 2 means a fetch failed or
`--offline` found the cache incomplete; exit 3 means the manifest or registry
could not be used.

Each document is checked with the checker's own `analyze` under its register as
the profile. The report gives, per register and per rule, the documents scanned,
the prose words, the documents with at least one finding, findings per 1,000
words, and the same at candidate level. Candidate counts exclude protected
spans. For each metric rule it also gives the distribution of the underlying
metric and how many observations cross the threshold the profile applies.
`ST.CROSS_FILE_TEMPLATE` is measured across the unrelated documents of each
register with the project checker's defaults. A finding on this corpus is a
candidate false positive, which a person still has to read.

To add a document, add its entry with `source_sha256`, `sha256`, and
`word_count` set to `null`, then run with `--record`. Recording fills empty
fields only and never overwrites a recorded checksum. If an extraction recipe
or converter changes on purpose, clear that document's `sha256` and record
again.

## Results

Dated results live in `corpus/results/`, a JSON report beside a write-up. The
JSON is the record; tables in the write-up come from `--format markdown` on the
same run. Re-run the measurement whenever the detectors change, and add a new
dated pair rather than editing an old one.
