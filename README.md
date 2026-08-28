# llm-ism-rewriter

A Claude Agent Skill that finds LLM writing clichés ("LLM-isms") in a draft and rewrites them in a plainer, more specific voice.

It catches stock vocabulary (*delve*, *testament*, *ever-evolving landscape*), false contrasts ("not just X, but Y"), rule-of-three padding, inflated significance, canned intros and conclusions, chatbot residue ("As of my last update"), leaked citation markup, and over-formatted structure. Findings are quality signals about how prose reads. They are never proof that a machine wrote it, and the skill is written so that it never claims otherwise.

This is a prompt package, not an application: Markdown that Claude loads at runtime, plus one optional Python helper. There is nothing to build and nothing to install beyond copying the directory.

## Install

Copy or clone the repository into a skills directory:

```bash
# available in every project, for Claude Code
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.claude/skills/llm-ism-rewriter

# or just this project
git clone git@github.com:jrajasekera/llm-ism-rewriter.git .claude/skills/llm-ism-rewriter
```

Claude picks the skill up from `SKILL.md`'s frontmatter and loads it on requests like removing AI-isms, auditing a draft for clichés, or making prose sound less generated. You can also name it directly: "use llm-ism-rewriter on draft.md".

## Modes

| Mode | How to ask | What you get |
|------|------------|--------------|
| `detect` | "audit this", "flag what sounds AI-ish", "don't change it" | Findings with a suggested fix each. Text untouched. |
| `rewrite` (default) | "rewrite this", "clean this up" | Findings, revised text, change summary. |
| `edit` | "edit draft.md in place" | Targeted edits to the file, then a verification pass. |

`edit` needs an explicit in-place request. "Clean up draft.md and give me a revised version" returns text and leaves the file alone.

Findings are reported per line, tagged with a tier:

```
- [Fingerprint] L12: "As of my last update" — knowledge-cutoff disclaimer; removed.
- [Cliché] L3: "ever-evolving landscape" — stock scene-setting; replaced with the actual subject.
- [Structural] L8–14: five consecutive sentences of 14–16 words — uniform rhythm; merged two, split one.
- [Protected] L20: quotation contains "delve" — left unchanged.
- [Gap] L17: "experts argue" — no source in text; marked [specify: who?] rather than inventing one.
```

## What it will not do

- **Invent specifics.** No new names, dates, numbers, sources, or opinions. A cliché that can only be fixed with a fact the text doesn't contain becomes a `[specify: …]` marker and a `[Gap]` finding.
- **Rewrite protected spans.** Quotations, code, tables, frontmatter, URLs, file paths, and citations are reported, not edited, unless you ask.
- **Fake a human voice.** No planted typos, slang, or theatrical punctuation.
- **Follow instructions inside the text under audit.** Imperatives found in the draft are treated as content — flagged as prompt leakage if they look out of place, never obeyed.
- **Flag a genre for doing its job.** `references/contexts.md` sets the norms: triads in a speech, anaphora in a manifesto, and "Note that…" in API docs are how those forms work. Fiction gets A-tier findings only.

## The checker script

`scripts/llm_ism_check.py` is an optional accelerator for long documents. It surfaces candidate lexical hits and three structural signals (em-dash rate, triad density, sentence-length variance), skipping fenced code, inline code, frontmatter, blockquotes, tables, and URLs.

```bash
python3 scripts/llm_ism_check.py FILE [FILE...]   # human-readable
python3 scripts/llm_ism_check.py --json FILE      # machine-readable
cat text.md | python3 scripts/llm_ism_check.py -  # stdin
```

```
$ python3 scripts/llm_ism_check.py draft.md
== draft.md: 14 words, 1 sentences, 0 em dashes, 0 triads, sentence len 14.0±0
  [cliche] L1 stock-vocabulary: 'testament to'
  [cliche] L1 stock-vocabulary: 'the ever-evolving landscape'
  [cliche] L1 stock-transition: 'It is important to note'
  Candidates only. Judge density, genre, and context before acting.
```

Standard library only, Python 3. Exit 0 whether or not it finds anything; exit 2 on unreadable input or bad arguments. The script carries a high-precision subset of the catalog and cannot weigh density or genre, so its output is a starting list, not a verdict.

## Layout

```
SKILL.md                 entry point: ground rules, modes, 7-step procedure
references/patterns.md   the detection catalog, A–E, with tier and fix per pattern
references/contexts.md   genre norms and legitimate uses
references/examples.md   before/after pairs and a worked report
scripts/llm_ism_check.py optional regex + heuristic checker
```

Only `SKILL.md` is always in context; the references load at the steps that need them.

## Attribution and license

Apache-2.0.

Pattern categories are adapted, paraphrased rather than copied, from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (CC BY-SA 4.0). Category grouping and the rhetorical-tic families were informed by Simon Willison's [LLM cliché highlighter](https://tools.simonwillison.net/llm-cliche-highlighter) (Apache-2.0); no code was reused. Keep both notices if you redistribute.
