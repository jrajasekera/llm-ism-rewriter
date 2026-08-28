# llm-ism-rewriter

A Claude Agent Skill that audits and rewrites prose which reads as formulaic, plus two Python tools that keep the rewrite honest.

The repository ships three things:

1. **The skill.** `SKILL.md` and its references. An agent loads it when you ask to remove AI-isms, audit a draft, or make writing sound less generated. It preserves your meaning, hedges, citations, and voice.
2. **The checker.** `scripts/llm_ism_check.py` turns deterministic matches into contextual findings, applying genre profiles and density thresholds rather than reporting every regex hit.
3. **The validator.** `scripts/llm_ism_validate.py` compares an original with its rewrite and fails when a claim has moved: a dropped hedge, a narrowed version string, a vanished measurement, an edited quotation.

The validator is the part most tools skip. A rewrite that removes every cliché and quietly changes what the text asserts is a failed rewrite, and this repository can prove it.

Nothing here judges authorship. See [Why there is no authorship score](#why-there-is-no-authorship-score).

- **New here?** Start with [Try it](#try-it).
- **Want to get something done?** See the [task guides](#task-guides).
- **Looking up a flag or an exit code?** See [Reference](#reference).
- **Wondering why it behaves this way?** See [Design notes](#design-notes).

## Install

The repository *is* the skill directory. `SKILL.md` sits at its root, so cloning it into a skills root is the whole installation. Pick the root your harness reads:

```bash
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.claude/skills/llm-ism-rewriter
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.codex/skills/llm-ism-rewriter
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.hermes/skills/llm-ism-rewriter
```

One clone can serve several harnesses if they share `~/.agents/skills`:

```bash
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.agents/skills/llm-ism-rewriter
ln -s ~/.agents/skills/llm-ism-rewriter ~/.claude/skills/llm-ism-rewriter
```

To scope it to one project instead:

```bash
git clone git@github.com:jrajasekera/llm-ism-rewriter.git .claude/skills/llm-ism-rewriter
```

Each harness picks the skill up from `SKILL.md`'s frontmatter. You can also name it directly: "use llm-ism-rewriter on draft.md".

The scripts need Python 3.10+ and the standard library. They are optional; the skill works without them.

## Try it

This walkthrough takes about two minutes and changes nothing outside a scratch directory. It uses the checker and the validator on a small file so you can see what each one reports. The commands assume you cloned into `~/.claude/skills/llm-ism-rewriter`; substitute your own path if you chose a different root.

**1. Write a draft with something to find.**

```bash
mkdir /tmp/ism-demo && cd /tmp/ism-demo
cat > draft.md <<'EOF'
# Notes

In today's fast-paced engineering environment, observability is not just a tool,
but a fundamental cornerstone of modern practice. It is crucial to delve into the
ever-evolving landscape of telemetry.

> Studies show that teams with tracing resolve incidents faster.

Hope this helps!
EOF
```

**2. Run the checker.**

```bash
python3 ~/.claude/skills/llm-ism-rewriter/scripts/llm_ism_check.py draft.md
```

The report looks like this:

```
== draft.md
   Context: general-prose (default)
   41 scanned prose words of 42; 0 protected segment(s)
   [P0 fingerprint] L9: 'Hope this helps'
       An address to a chat user does not belong in standalone prose.
       evidence: FP.CHATBOT_RESIDUE (high); action: Delete the opener or closer and start with the content.
   [P1 cliche] L3-5: 'crucial, delve, ever-evolving'
       Three or more stock terms in one paragraph usually stand in for the concrete claim.
       evidence: LX.STOCK_VOCAB_CLUSTER, RH.GENERIC_INTRO (high); action: Use the plain word, or name the thing the term is gesturing at. Fix the terms that obscure the claim, not all of them.
   [P1 cliche] L5: 'ever-evolving'
       Scene-setting metaphor substituted for the subject itself.
       evidence: LX.FIGURATIVE_LANDSCAPE (high); action: Name the actual set of things: the three vendors, the two APIs, the field as the author defines it.
   [P1 cliche] L7: 'Studies show'
       Borrows authority from a source the text never names.
       evidence: LX.VAGUE_AUTHORITY (high); action: Name the source if the document has it. Otherwise mark `[specify: who?]`. Never invent one.
   Density: heavy — 4 finding(s) across 41 scanned prose words, including 1 fingerprint(s)
   Writing-quality signals only. Never evidence of authorship.
```

Each finding carries a rule ID, a priority, and an action. Nothing carries a score.

**3. Write a rewrite that goes too far, on purpose.**

```bash
cat > after.md <<'EOF'
# Notes

Observability matters. Teams that trace requests resolve incidents faster.

> Studies show that teams with tracing resolve incidents faster.
EOF
```

**4. Run the validator on the pair.**

```bash
python3 ~/.claude/skills/llm-ism-rewriter/scripts/llm_ism_validate.py draft.md after.md
```

```
mode: rewrite
FAIL: negation: count changed: not=1→0
WARN: comparative: count changed: faster=1→2
WARN: length: prose shrank 56%; confirm no argument was removed
PASS: headings: 1 unchanged
PASS: residual findings: P0/P1 findings 4→1
INFO: untouched prose: 1/2 paragraphs byte-identical to the source
verdict: FAILED (1 failure(s), 2 warning(s) to review)
Preservation checks only. This says nothing about who wrote either version.
```

The rewrite reads better and the validator still rejects it: the original said observability is *not just* a tool, and the rewrite dropped that negation. Exit status is 1, so the check can gate a commit.

**5. Clean up.**

```bash
cd .. && rm -rf /tmp/ism-demo
```

You have now seen the two halves of the tool: the checker finds patterns, and the validator guards the meaning while you fix them. To use the skill itself, ask an agent to "audit draft.md for AI-isms" and read [Task guides](#task-guides).

## Task guides

### Audit a draft without changing it

Ask the agent to "audit this", "flag what sounds AI-ish", or "don't change it". You get findings with a suggested fix for each, the profile applied, and a list of what was suppressed. The text is untouched.

To do the same from the shell:

```bash
python3 scripts/llm_ism_check.py draft.md
cat draft.md | python3 scripts/llm_ism_check.py -
```

### Rewrite a draft

Ask to "rewrite this" or "clean this up". This is the default mode. You get findings, one final revised text, a change summary, and validation.

Naming a file is not an in-place request. "Clean up draft.md and give me a revised version" returns text and leaves the file where it is.

### Edit a file in place

Say so explicitly: "edit draft.md in place", "apply the changes to the file". The agent makes targeted edits and then validates them.

### Match the genre

The checker infers a profile from strong cues and otherwise falls back to `general-prose`. Override it when you know better:

```bash
python3 scripts/llm_ism_check.py --profile technical-docs README.md
python3 scripts/llm_ism_check.py --profile academic-research paper.md
```

Profiles change what counts. Triads in a speech, anaphora in a manifesto, `Note that…` in API docs, and discontinuous sentences in install steps are how those forms work, so the matching profile tolerates them. `creative` reports fingerprint findings only.

### Gate a commit or a CI job

```bash
python3 scripts/llm_ism_check.py --fail-on P0 --format sarif --output ism.sarif docs/*.md
python3 scripts/llm_ism_validate.py --mode edit before.md after.md
```

The checker exits 0 by default whatever it finds, so `--fail-on` is what makes it block. The validator exits 1 on a preservation failure without any flag.

### Find templates repeated across a docs set

```bash
python3 scripts/llm_ism_project_check.py docs/
python3 scripts/llm_ism_project_check.py --min-files 4 --json posts/*.md
```

This reports repeated openers, phrases, heading frames, section sequences, and bullet skeletons across a set of documents: the templates that are invisible inside any one file. It reports the repetition and stops there, because a shared template is often deliberate house style.

### Report a false positive

Open an issue with the minimal text, the rule ID, and the profile. Every resolved report becomes a narrower detector, a profile carve-out, or a documented decision to keep the finding, each with a fixture.

### Work on the repository

```bash
python3 -m unittest discover -s tests -v   # unit tests
python3 scripts/build_catalog.py --check   # registry / catalog / code contract
python3 scripts/self_scan.py --check       # this repo's prose against its budget
python3 scripts/build_catalog.py --write   # regenerate the rule index in patterns.md
```

The contract check keeps the three sources of truth aligned. Every executable rule must map to a documented catalog entry, carry one positive and two negative fixtures, and, if its threshold is provisional, be recorded in `references/negative-results.md`. Adding a rule to the prose catalog needs no detector; adding a detector needs a registry rule.

## Reference

### Modes

| Mode | How to ask | What you get |
|------|------------|--------------|
| `detect` | "audit this", "flag what sounds AI-ish", "don't change it" | Findings with a suggested fix each, the profile applied, and what was suppressed. Text untouched. |
| `rewrite` (default) | "rewrite this", "clean this up" | Findings, one final revised text, a change summary, and validation. |
| `edit` | "edit draft.md in place" | Targeted edits to the file, then validation. |

### What the rules cover

Stock vocabulary clusters (`delve`, `testament`, `ever-evolving landscape`), false contrasts (`not just X, but Y`), rule-of-three padding, inflated significance, vague authority, canned intros and conclusions, chatbot residue, leaked tool markup, labeled-bullet runs, repeated heading frames, and cadence patterns.

The human-readable catalog is `references/patterns.md`. The machine-readable registry is `references/rules.json`: 41 rules across 8 context profiles, canonical for every threshold the checker applies.

### Limits

- **No authorship judgement.** No probability, no score, no `human`/`mixed`/`AI` label. A test enforces their absence from every output schema.
- **No invented specifics.** No new names, dates, numbers, sources, or opinions. A cliché repairable only with a fact the text lacks becomes a `[specify: …]` marker and a `[Gap]` finding.
- **No edits to protected spans.** Quotations, code, tables, frontmatter, URLs, paths, and citations are reported, not edited, unless you ask.
- **No faked human voice.** No planted typos, slang, or theatrical punctuation. The default voice is `preserve`.
- **No instruction-following inside the text under audit.** An imperative found in the draft is content. It is flagged as prompt leakage if it looks out of place, and never obeyed.
- **No banned words.** One `crucial` is not a finding. Three distinct stock terms in one paragraph is.

### `llm_ism_check.py`

```
llm_ism_check.py [options] FILE [FILE...]     # '-' reads stdin
```

Arguments are files, not directories. Use a shell glob to scan a tree. Only `llm_ism_project_check.py` walks directories.

| Flag | Values | Default |
|------|--------|---------|
| `--profile` | `auto`, `general-prose`, `technical-docs`, `academic-research`, `marketing-product`, `essay-blog`, `social-email`, `legal-policy`, `creative` | `auto`, falling back to `general-prose` |
| `--format` | `text`, `json`, `sarif` | `text` |
| `--level` | `findings`, `candidates` | `findings` |
| `--include-protected` | flag; also reports matches inside quotations, code, tables, and frontmatter | off |
| `--fail-on` | `none`, `P0`, `P1`, `any` | `none` |
| `--max-findings N` | summarize after N findings per file; `0` for no limit | `0` |
| `--rules PATH` | an alternate `rules.json` | the bundled registry |
| `--output PATH` | write here instead of stdout | stdout |

Exit codes: `0` whether or not it finds anything, `1` only when `--fail-on` is set and met, `2` on unreadable input, `3` on a registry failure.

### `llm_ism_validate.py`

```
llm_ism_validate.py [options] BEFORE AFTER
```

| Flag | Values | Default |
|------|--------|---------|
| `--mode` | `detect`, `rewrite`, `edit`, `restructure` | `rewrite` |
| `--json` | flag; emit JSON instead of text | off |
| `--shrink-limit RATIO` | warn below this share of retained prose words | `0.6` |
| `--rules PATH` | an alternate `rules.json` | the bundled registry |

Checks run in this order: protected spans byte-for-byte, then technical anchors (numbers with units, versions, flags, environment variables, identifiers, URLs, paths, citation keys), then semantic anchors (negation, modality, quantifiers, comparatives, proper nouns, person), then structure, then whether the rewrite added findings.

Exit codes: `0` on pass, `1` on a preservation failure.

### `llm_ism_project_check.py`

```
llm_ism_project_check.py [options] PATH [PATH...]
```

| Flag | Values | Default |
|------|--------|---------|
| `--ngram N` | phrase length in words, 4–10 | `5` |
| `--min-files N` | report a pattern present in at least N files | `3` |
| `--ext EXT` | comma-separated file extensions to walk | `.md,.markdown,.txt` |
| `--ignore SUBSTRING` | skip paths containing this substring; repeatable | none |
| `--json` | flag; emit JSON | off |
| `--fail-on-repetition` | flag; exit 1 when any repetition is reported | off |

### Repository layout

```
SKILL.md                          entry point: trust boundary, modes, 8-step procedure
references/patterns.md            the catalog, A-E, with rule IDs, tiers, and fixes
references/rules.json             canonical registry: 41 rules, 8 context profiles
references/contexts.md            genre profiles, legitimate uses, large-file policy
references/rewrite-invariants.md  the preservation contract
references/voices.md              bounded voice profiles, default `preserve`
references/examples.md            before/after pairs, counterexamples, a worked report
references/detector-map.md        executable / partly executable / judgment-only
references/negative-results.md    rejected hypotheses and provisional thresholds
scripts/llm_ism_core.py           Markdown segmentation, registry, masking, sentences
scripts/llm_ism_check.py          candidates and contextual findings
scripts/llm_ism_validate.py       original-versus-rewrite preservation
scripts/llm_ism_project_check.py  cross-file template repetition
scripts/build_catalog.py          the registry/catalog/code anti-drift contract
scripts/self_scan.py              this repository's prose against a committed budget
tests/                            unit tests and fixtures
evals/                            agent evals against the previous version
```

## Design notes

### Why there is no authorship score

The reference corpus this project drew on found that composite detectors classified authorship poorly, that vocabulary lists fired slightly more often on human writing than on generated writing, and that em-dash frequency pointed the opposite way from the common assumption. A tool built on those signals can report how prose reads. It cannot report who wrote it, and a number attached to the output would invite readers to believe otherwise.

So the output has no probability, no score, and no label, and a test asserts their absence from every output schema. The rejected hypotheses and the measurements behind them are in `references/negative-results.md`.

### Candidates and findings are different things

A **candidate** is a deterministic match: a regex fired. A **finding** is a candidate that survived the registry's thresholds and the active profile's tolerances. Most candidates never become findings, which is the point. Every report shows both counts and explains each suppression, so you can see what was held back and disagree with it.

Structural findings carry their numerator, denominator, threshold, and whether that threshold is calibrated or provisional. All of them are currently provisional, and `references/negative-results.md` says so for each one.

### What the validator can and cannot promise

It does not claim semantic equivalence, and it cannot. It reports likely drift for a person to review: a hedge that disappeared, a quantifier that hardened, a measurement that changed units. The contract it enforces is written out in `references/rewrite-invariants.md`.

### Running on any harness

The skill body names no tool. It asks for actions — read this file, edit that span, run this command — which map onto whatever the harness provides: `Read` and `Edit` under Claude Code, `read_file` and `patch` under Hermes Agent, shell and patch application under Codex.

Reference and script paths resolve against the skill's own directory rather than the working directory, and `SKILL.md`'s `Paths` section says how to find that directory when the harness does not hand it over. The scripts locate `references/rules.json` relative to their own file, so they run from anywhere.

Where a sandbox blocks shell execution, such as Codex in read-only mode, the skill degrades to judgment alone, which step 3 of the procedure already allows.

### Progressive disclosure

Only `SKILL.md` is always in context. The references load at the steps that need them, which is why the catalog, the profiles, and the invariants live in separate files rather than in one document.

## Attribution and license

Apache-2.0. Full provenance in `NOTICE.md`.

Pattern categories are adapted, paraphrased rather than copied, from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (CC BY-SA 4.0). Category grouping and the rhetorical-tic families were informed by Simon Willison's [LLM cliché highlighter](https://tools.simonwillison.net/llm-cliche-highlighter) (Apache-2.0). Structural leads came from [osolmaz/ai-smell](https://github.com/osolmaz/ai-smell) and rule/detector contract practice from [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing). No code, regexes, or fixtures were reused from any of them. Keep these notices if you redistribute.
