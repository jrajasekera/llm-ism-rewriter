# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A single Claude Agent Skill, `llm-ism-rewriter`. It is a prompt/reference package that another Claude instance loads at runtime to detect and rewrite LLM writing clichés, not an application. There is no build, no dependency manifest, and no test suite. The product is `SKILL.md` plus its `references/`; the only executable is one standard-library Python 3 helper.

## Commands

```bash
python3 scripts/llm_ism_check.py FILE [FILE...]   # human-readable candidates
python3 scripts/llm_ism_check.py --json FILE      # machine-readable
cat text.md | python3 scripts/llm_ism_check.py -  # stdin
```

Exit 0 whether or not findings exist; exit 2 on unreadable input or bad arguments. No third-party packages — keep it that way so the skill runs anywhere Python 3 does.

To sanity-check a change to the checker, run it against the repo's own prose (`references/patterns.md`, `references/examples.md`) — those files deliberately contain example clichés inside code spans and quoted "Before:" lines, so they exercise the protected-span skipping.

## Architecture

Four files carry the whole skill, loaded progressively rather than all at once:

- **`SKILL.md`**: the entry point and the only file always in context. Holds the frontmatter (`name`, `description` — these determine when the skill triggers), the ground rules, the three modes, and a 7-step procedure. It *points to* the references rather than inlining them; keep it short.
- **`references/patterns.md`**: the detection catalog, organized A–E: A fingerprints, B lexical clichés, C rhetorical structures, D structural/formatting, E clarity. Every pattern carries tier, what it looks like, why it reads as boilerplate, and a fix. Loaded at procedure step 3.
- **`references/contexts.md`**: genre norms and legitimate uses, so structural patterns aren't flagged in speeches, fiction, or marketing where a competent writer uses them on purpose. Loaded at step 1.
- **`references/examples.md`**: before/after pairs per category plus a worked report. Loaded at step 5.

`scripts/llm_ism_check.py` is an *optional accelerator*, not the source of truth. It mirrors a high-precision subset of the catalog in `FINGERPRINTS` / `CLICHES` regex dicts plus three structural heuristics (em-dash rate, triad density, sentence-length stdev). `prose_lines()` strips frontmatter, fenced code, inline code, blockquotes, tables, headings, URLs, and paths before matching. It reports candidates only and never judges severity.

### Invariants to preserve when editing

- **Tier vocabulary is shared.** `SKILL.md`, `patterns.md`, and the script's `tier` field all use fingerprint / cliché / structural / clarity. Renaming a tier means changing all three.
- **The script is a subset, not a mirror.** Adding a pattern to `patterns.md` does not require a regex; regexes must be high-precision because the script can't weigh density. Adding a regex does require the category to exist in `patterns.md`.
- **Protected spans** (quotations, code, tables, frontmatter, URLs, paths, citations) are report-only in the skill and skipped in the script. Any new pattern must respect both.
- **Signals, not verdicts.** No wording anywhere may imply that a detection proves AI authorship. The script's output ends with an explicit "candidates only" caveat; keep an equivalent.
- **No invented specifics.** The rewrite rules forbid adding names, dates, numbers, or sources; gaps get a `[specify: …]` marker and a `[Gap]` finding instead.
- **Attribution.** The header of `references/patterns.md` and the Attribution section of `SKILL.md` credit Wikipedia's "Signs of AI writing" (CC BY-SA 4.0, paraphrased) and Simon Willison's llm-cliché-highlighter (Apache-2.0, no code reused). Preserve both notices in any redistribution or restructuring.

### Report format

Findings are emitted as `- [Tier] Lnn: "span" — reason; action.`, followed by revised text (rewrite mode) or edits-plus-verification (edit mode), then a Notes density line. The canonical example is at the end of `references/examples.md`; change the format there and in `SKILL.md` together.

## Writing style for this repo

The skill's own prose is subject to its own catalog. Before committing changes to any Markdown here, run `python3 scripts/llm_ism_check.py` over the edited file and clear anything that isn't a deliberate example.
