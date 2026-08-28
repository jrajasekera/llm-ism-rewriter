# Rewrite invariants

The preservation contract. `SKILL.md` cites it, `scripts/llm_ism_validate.py`
checks what can be checked, and `tests/fixtures/rewrite_pairs/` pins the cases.
One vocabulary for all three.

A rewrite that removes every cliché and changes a claim is a failed rewrite.

## Exact invariants

Byte-identical between the original and the revision, in every mode:

- fenced and indented code blocks, including their info strings and formatting
- YAML or TOML frontmatter
- attributed quotations and blockquote text
- Markdown table cell content
- inline code spans
- URLs and link targets
- file paths, POSIX and Windows
- citation keys, footnote labels, and reference-definition targets
- raw HTML blocks

An em dash or a stock word inside one of these is reported as `[Protected]`. It
is not an unfinished edit.

## Structural invariants

Stable unless the user asked for restructuring:

- heading text, level, and order
- ordered-list numbering and nesting depth
- table shape: column count and row order
- reference-definition placement

## Claim anchors

Facts the rewrite carries forward unchanged. The validator extracts these
mechanically; a reader confirms the ones it cannot.

| Anchor | Examples | Why it matters |
|--------|----------|----------------|
| Numbers with units | `50 ms`, `2.1M rows`, `12%`, `4 GB` | The measurement *is* the claim. |
| Bare numbers | `three vendors`, `2024` | May legitimately be spelled out; warning, not error. |
| Version strings | `Python 3.11+`, `v2.0.0`, `Java 17` | `3.11+` and `3.11` are different claims. |
| Identifiers | `--dry-run`, `MAX_RETRIES`, `parseConfig`, `snake_case` | Renaming one breaks the reader's search. |
| Negation | not, never, no, without, except, unless, neither | Dropping one inverts the sentence. |
| Modality | may, might, can, could, must, should, will, would, shall | `may fail` → `fails` is a stronger claim than the author made. |
| Quantifiers | all, every, some, most, many, few, only, at least, at most | Scope. |
| Comparisons | more, less, faster, slower, higher, better | Relative ranking. |
| Attribution | who said, measured, or reported it | Removing it orphans the claim. |
| Scope | which system, version, environment, population, or period | An unscoped claim is a bigger claim. |
| Proper nouns | product, person, org, and place names | Removing one loses a fact; adding one invents one. |

## What may never be added

Not by any mode, voice, or user request short of the user supplying the fact
themselves:

- names, dates, numbers, measurements, sources, or citations
- anecdotes, personal experience, or first-person claims where the source had none
- opinions, emotional reactions, humour, or stakes
- certainty the source did not express
- planted typos, slang, fragments, ellipses, or theatrical punctuation

When a cliché can only be repaired with a fact that is not in the source, the
revision keeps a `[specify: …]` marker and the report records a `[Gap]` finding.

### Two kinds of gap

- **Editorial gap** — the claim cannot stand without the missing detail
  (`Experts agree that…`). Insert the marker into the revised text.
- **Optional specificity** — the claim is complete; an example would improve it.
  Mention it in the report. Do **not** litter usable prose with markers.

## Mode policy

| Check | detect | rewrite | edit | explicit restructure |
|-------|--------|---------|------|----------------------|
| Text unchanged | error if changed | — | — | — |
| Exact invariants | n/a | error | error | error |
| Claim anchors | n/a | error | error | error |
| Heading text/level/order | n/a | warning | error | allowed |
| Paragraph order | n/a | warning | warning | allowed |
| Clean paragraphs untouched | n/a | preferred | expected | — |
| Prose shrink beyond the limit | n/a | warning | warning | warning |

## Warning-level checks

These need a reader, not a rule. The validator surfaces them; it does not decide
them.

- prose shrank past `--shrink-limit` (default 40%)
- a proper noun disappeared, or a new one appeared
- a modal, quantifier, or comparative count changed
- a heading was reworded
- paragraphs were reordered without being reworded
- an example or parenthetical qualification was dropped
- a recurring domain term was replaced by several synonyms
- first- or second-person use changed substantially
- a citation moved while remaining present

## What the validator does not claim

It does not check semantic equivalence, and it cannot. It reports likely drift.
A clean validator run means the mechanical anchors survived — not that the
rewrite is faithful, useful, or in the author's voice. Those are read, not
computed.
