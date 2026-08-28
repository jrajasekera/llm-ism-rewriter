# llm-ism-rewriter

A Claude Agent Skill that audits and rewrites prose which reads as formulaic — and a pair of Python tools that keep it honest.

The repository ships three things:

1. **The skill.** `SKILL.md` plus its references. Claude loads it when you ask to remove AI-isms, audit a draft, or make writing sound less generated. It preserves your meaning, hedges, citations, and voice, and it never claims to know who wrote anything.
2. **The checker.** `scripts/llm_ism_check.py` turns deterministic matches into contextual findings, applying genre profiles and density thresholds rather than reporting every regex hit.
3. **The validator.** `scripts/llm_ism_validate.py` compares an original with its rewrite and fails when a claim moved — a dropped hedge, a narrowed version string, a vanished measurement, an edited quotation.

The third one is the part most tools skip. A rewrite that removes every cliché and quietly changes what the text asserts is a failed rewrite, and this repository can prove it.

## What it looks for

Stock vocabulary clusters (`delve`, `testament`, `ever-evolving landscape`), false contrasts (`not just X, but Y`), rule-of-three padding, inflated significance, vague authority, canned intros and conclusions, chatbot residue, leaked tool markup, labeled-bullet runs, repeated heading frames, and cadence patterns. The full catalog is `references/patterns.md`; the machine-readable registry is `references/rules.json`.

## What it will not do

- **Judge authorship.** There is no probability, no score, and no `human`/`mixed`/`AI` label, and a test enforces their absence from every output schema. The reference corpus studies this project drew on found that composite detectors classified authorship poorly, that vocabulary lists fired slightly more on human writing, and that em-dash frequency pointed the opposite way from the assumption. Those results are recorded in `references/negative-results.md`.
- **Invent specifics.** No new names, dates, numbers, sources, or opinions. A cliché repairable only with a fact the text lacks becomes a `[specify: …]` marker and a `[Gap]` finding.
- **Rewrite protected spans.** Quotations, code, tables, frontmatter, URLs, paths, and citations are reported, not edited, unless you ask.
- **Fake a human voice.** No planted typos, slang, or theatrical punctuation. The default voice is `preserve`.
- **Follow instructions inside the text under audit.** An imperative found in the draft is content — flagged as prompt leakage if it looks out of place, never obeyed.
- **Ban ordinary words.** One `crucial` is not a finding. Three distinct stock terms in one paragraph is.
- **Flag a genre for doing its job.** Triads in a speech, anaphora in a manifesto, `Note that…` in API docs, and discontinuous sentences in install steps are how those forms work. Fiction gets fingerprint findings only.

## Install

The repository *is* the skill directory: `SKILL.md` sits at its root, so cloning it
into a skills root is the whole installation.

```bash
# Claude Code, Codex, or Hermes Agent — pick the root your harness reads
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.claude/skills/llm-ism-rewriter
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.codex/skills/llm-ism-rewriter
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.hermes/skills/llm-ism-rewriter

# one clone for all three, if your harnesses share ~/.agents/skills
git clone git@github.com:jrajasekera/llm-ism-rewriter.git ~/.agents/skills/llm-ism-rewriter
ln -s ~/.agents/skills/llm-ism-rewriter ~/.claude/skills/llm-ism-rewriter

# or scope it to one project
git clone git@github.com:jrajasekera/llm-ism-rewriter.git .claude/skills/llm-ism-rewriter
```

Each harness picks the skill up from `SKILL.md`'s frontmatter. You can also name
it: "use llm-ism-rewriter on draft.md".

### Harness notes

The skill body names no tool. It asks for actions — read this file, edit that
span, run this command — which map onto whatever the harness provides: `Read` and
`Edit` under Claude Code, `read_file` and `patch` under Hermes Agent, shell and
patch application under Codex. Reference and script paths resolve against the
skill's own directory, not the working directory; `SKILL.md`'s `Paths` section
says how to find it when the harness does not hand it over.

The scripts are optional. They are Python 3.10+ with the standard library and
nothing else, and they locate `references/rules.json` relative to their own file,
so they run from any directory. Where a sandbox blocks shell execution — Codex in
read-only mode, for instance — the skill degrades to judgment alone, which is what
step 3 already allows.

## Modes

| Mode | How to ask | What you get |
|------|------------|--------------|
| `detect` | "audit this", "flag what sounds AI-ish", "don't change it" | Findings with a suggested fix each, the profile applied, and what was suppressed. Text untouched. |
| `rewrite` (default) | "rewrite this", "clean this up" | Findings, one final revised text, a change summary, and validation. |
| `edit` | "edit draft.md in place" | Targeted edits to the file, then validation. |

`edit` needs an explicit in-place request. "Clean up draft.md and give me a revised version" returns text and leaves the file alone.

## The checker

```bash
python3 scripts/llm_ism_check.py draft.md
python3 scripts/llm_ism_check.py --profile technical-docs --format json README.md
python3 scripts/llm_ism_check.py --level candidates --include-protected draft.md
cat draft.md | python3 scripts/llm_ism_check.py -
```

```
$ python3 scripts/llm_ism_check.py draft.md
== draft.md
   Context: general-prose (default)
   64 scanned prose words of 71; 1 protected segment(s)
   [P0 fingerprint] L4: 'Hope this helps'
       An address to a chat user does not belong in standalone prose.
       evidence: FP.CHATBOT_RESIDUE (high); action: Delete the opener or closer and start with the content.
   [P1 cliche] L2: "In today's fast-paced"
       Scene-setting that could open any document on any subject.
       evidence: RH.GENERIC_INTRO (high); action: Delete and start with the first concrete claim.
   Suppressed: 3 isolated LX.STOCK_VOCAB_CLUSTER match(es) below the threshold of 3
   Density: moderate — 2 finding(s) across 64 scanned prose words, including 1 fingerprint(s)
   Writing-quality signals only. Never evidence of authorship.
```

A **candidate** is a deterministic match. A **finding** is a candidate that survived the registry's thresholds and the profile's tolerances. The report shows both counts and explains every suppression. Structural findings carry their numerator, denominator, threshold, and whether that threshold is calibrated or provisional — all of them are currently provisional.

Flags: `--profile auto|general-prose|technical-docs|academic-research|marketing-product|essay-blog|social-email|legal-policy|creative`, `--format text|json|sarif`, `--level findings|candidates`, `--include-protected`, `--fail-on none|P0|P1|any`, `--max-findings N`, `--output PATH`.

Exit 0 whether or not it finds anything, 1 only when `--fail-on` is set and met, 2 on unreadable input, 3 on a registry failure.

## The validator

```bash
python3 scripts/llm_ism_validate.py before.md after.md
python3 scripts/llm_ism_validate.py --mode edit before.md after.md
python3 scripts/llm_ism_validate.py --json before.md after.md
```

```
$ python3 scripts/llm_ism_validate.py --mode edit before.md after.md
mode: edit
FAIL: inline codes: missing from the rewrite: '`--dry-run`'
FAIL: number with units: missing from the rewrite: '50 ms'
FAIL: negation: count changed: not=1→0
WARN: modality: count changed: may=1→0
PASS: residual findings: P0/P1 findings 6→1
verdict: FAILED (3 failure(s), 1 warning(s) to review)
```

It checks protected spans byte-for-byte, then technical anchors (numbers with units, versions, flags, environment variables, identifiers, URLs, paths, citation keys), then semantic anchors (negation, modality, quantifiers, comparatives, proper nouns, person), then structure, then whether the rewrite added findings. Exit 1 on a preservation failure.

It does not claim semantic equivalence, and it cannot. It reports likely drift for a person to review. The contract it enforces is `references/rewrite-invariants.md`.

## Project mode

```bash
python3 scripts/llm_ism_project_check.py docs/
```

Repeated openers, phrases, heading frames, section sequences, and bullet skeletons across a set of documents — the templates that are invisible inside any one file. It reports repetition and says so: a shared template is often deliberate house style.

## Layout

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

Only `SKILL.md` is always in context; the references load at the steps that need them. The scripts use the standard library and nothing else, so they run wherever Python 3.10+ does.

## Development

```bash
python3 -m unittest discover -s tests -v   # unit tests
python3 scripts/build_catalog.py --check   # registry / catalog / code contract
python3 scripts/self_scan.py --check       # this repo's prose against its budget
python3 scripts/build_catalog.py --write   # regenerate the rule index in patterns.md
```

The contract check is what keeps the three sources of truth aligned. Every executable rule must map to a documented catalog entry, carry one positive and two negative fixtures, and — if its threshold is provisional — be recorded in `references/negative-results.md`. Adding a rule to the prose catalog needs no detector; adding a detector needs a registry rule.

Found a false positive? Open an issue with the minimal text, the rule ID, and the profile. Every resolved report becomes a narrower detector, a profile carve-out, or a documented decision to keep the finding — each with a fixture.

## Attribution and license

Apache-2.0. Full provenance in `NOTICE.md`.

Pattern categories are adapted, paraphrased rather than copied, from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (CC BY-SA 4.0). Category grouping and the rhetorical-tic families were informed by Simon Willison's [LLM cliché highlighter](https://tools.simonwillison.net/llm-cliche-highlighter) (Apache-2.0). Structural leads came from [osolmaz/ai-smell](https://github.com/osolmaz/ai-smell) and rule/detector contract practice from [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing). No code, regexes, or fixtures were reused from any of them. Keep these notices if you redistribute.
