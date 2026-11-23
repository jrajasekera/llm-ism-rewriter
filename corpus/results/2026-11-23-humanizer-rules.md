# Corpus run for the 2.5.0 rules, 2026-11-23

The 2.5.0 detectors run on the same 48 human-written documents as the
2026-11-13 baseline, from the cache captured that day. The question was narrow:
do the four new executable rules, or the new patterns in three existing rules,
fire on prose written before November 2022? These are rates of writing-quality
signals on a named sample. They say nothing about who wrote anything.

- `RH.PHANTOM_OBJECTION`: three candidates, one each in three of the twelve
  essays. Each was alone in its document, below the threshold of two, so the
  rule produced no finding.
- `LX.GAP_SPECULATION`, `LX.PART_STANDIN`, `LX.DEPTH_SIGNAL`: no candidate in
  any register.
- `RH.APHORISM_CLOSER`, `LX.ENGAGEMENT_HOOK`, `FP.PROMPT_LEAKAGE`: counts are
  the same as the baseline, so the new patterns matched nothing.
- Findings per register are unchanged: 45, 39, 21, and 12.

The run shows the new rules are quiet on this sample. It shows nothing about
what they catch, and no threshold changed. The JSON record is
`2026-11-23-humanizer-rules.json` in this directory; the tables below are its
`--format markdown` rendering.

## Appendix: tables

| Register | Docs | Prose words | Docs with a finding | Findings | Per 1k words | Candidates | Per 1k words |
|---|---:|---:|---:|---:|---:|---:|---:|
| essay-blog | 12 | 22994 | 12 | 45 | 1.957 | 58 | 2.522 |
| general-prose | 10 | 21848 | 7 | 39 | 1.785 | 36 | 1.648 |
| legal-policy | 13 | 26146 | 6 | 21 | 0.803 | 59 | 2.257 |
| technical-docs | 13 | 17668 | 6 | 12 | 0.679 | 43 | 2.434 |

#### Rules in essay-blog

| Rule | Status | Docs with finding | Findings | Per 1k | Docs with candidate | Candidates | Per 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| `RH.PHRASE_TRIAD` | full | 10 | 35 | 1.522 | 10 | 35 | 1.522 |
| `RH.FALSE_CONTRAST` | full | 3 | 4 | 0.174 | 3 | 4 | 0.174 |
| `LX.PERFORMATIVE_HONESTY` | full | 2 | 2 | 0.087 | 2 | 2 | 0.087 |
| `FP.META_NARRATION` | full | 1 | 1 | 0.043 | 1 | 1 | 0.043 |
| `FP.UNFILLED_PLACEHOLDER` | full | 1 | 1 | 0.043 | 1 | 1 | 0.043 |
| `LX.INFLATED_SIGNIFICANCE` | full | 1 | 1 | 0.043 | 1 | 1 | 0.043 |
| `ST.FRAGMENT_RUN` | full | 1 | 1 | 0.043 | 0 | 0 | 0 |
| `LX.STOCK_VOCAB_CLUSTER` | full | 0 | 0 | 0 | 3 | 4 | 0.174 |
| `CL.WORDY_PHRASE` | skip | 0 | 0 | 0 | 3 | 3 | 0.13 |
| `LX.STOCK_VOCAB_REPEAT` | full | 0 | 0 | 0 | 3 | 3 | 0.13 |
| `RH.PHANTOM_OBJECTION` | full | 0 | 0 | 0 | 3 | 3 | 0.13 |
| `LX.STOCK_TRANSITION` | full | 0 | 0 | 0 | 1 | 1 | 0.043 |

#### Rules in general-prose

| Rule | Status | Docs with finding | Findings | Per 1k | Docs with candidate | Candidates | Per 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| `RH.PHRASE_TRIAD` | full | 5 | 25 | 1.144 | 8 | 28 | 1.282 |
| `RH.FORCED_SYMMETRY` | full | 5 | 8 | 0.366 | 0 | 0 | 0 |
| `ST.HEADING_FRAME_REPEAT` | full | 2 | 2 | 0.092 | 0 | 0 | 0 |
| `LX.INFLATED_SIGNIFICANCE` | full | 1 | 1 | 0.046 | 1 | 1 | 0.046 |
| `LX.VAGUE_AUTHORITY` | full | 1 | 1 | 0.046 | 1 | 1 | 0.046 |
| `RH.APHORISM_CLOSER` | full | 1 | 1 | 0.046 | 1 | 1 | 0.046 |
| `RH.FALSE_CONTRAST` | full | 1 | 1 | 0.046 | 1 | 1 | 0.046 |
| `CL.WORDY_PHRASE` | skip | 0 | 0 | 0 | 2 | 2 | 0.092 |
| `LX.ASSOCIATION_VAGUENESS` | full | 0 | 0 | 0 | 2 | 2 | 0.092 |

#### Rules in legal-policy

| Rule | Status | Docs with finding | Findings | Per 1k | Docs with candidate | Candidates | Per 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| `RH.PHRASE_TRIAD` | relaxed | 3 | 12 | 0.459 | 10 | 25 | 0.956 |
| `RH.TRIAD_DENSITY` | relaxed | 3 | 3 | 0.115 | 0 | 0 | 0 |
| `RH.APHORISM_CLOSER` | full | 2 | 2 | 0.076 | 2 | 2 | 0.076 |
| `RH.FORCED_SYMMETRY` | relaxed | 2 | 2 | 0.076 | 0 | 0 | 0 |
| `FP.META_NARRATION` | full | 1 | 1 | 0.038 | 1 | 1 | 0.038 |
| `FP.UNFILLED_PLACEHOLDER` | full | 1 | 1 | 0.038 | 1 | 1 | 0.038 |
| `LX.ASSOCIATION_VAGUENESS` | skip | 0 | 0 | 0 | 6 | 19 | 0.727 |
| `CL.WORDY_PHRASE` | skip | 0 | 0 | 0 | 5 | 6 | 0.229 |
| `LX.STOCK_TRANSITION` | relaxed | 0 | 0 | 0 | 2 | 2 | 0.076 |
| `RH.FALSE_CONTRAST` | relaxed | 0 | 0 | 0 | 2 | 2 | 0.076 |
| `LX.COPULA_AVOIDANCE` | full | 0 | 0 | 0 | 1 | 1 | 0.038 |

#### Rules in technical-docs

| Rule | Status | Docs with finding | Findings | Per 1k | Docs with candidate | Candidates | Per 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| `CL.WORDY_PHRASE` | full | 2 | 7 | 0.396 | 2 | 7 | 0.396 |
| `FP.META_NARRATION` | full | 2 | 2 | 0.113 | 2 | 2 | 0.113 |
| `ST.HEADING_FRAME_REPEAT` | relaxed | 2 | 2 | 0.113 | 0 | 0 | 0 |
| `FP.UNFILLED_PLACEHOLDER` | full | 1 | 1 | 0.057 | 1 | 1 | 0.057 |
| `RH.PHRASE_TRIAD` | relaxed | 0 | 0 | 0 | 5 | 10 | 0.566 |
| `LX.STOCK_TRANSITION` | relaxed | 0 | 0 | 0 | 5 | 7 | 0.396 |
| `LX.STOCK_VOCAB_CLUSTER` | relaxed | 0 | 0 | 0 | 5 | 5 | 0.283 |
| `LX.STOCK_VOCAB_REPEAT` | relaxed | 0 | 0 | 0 | 5 | 5 | 0.283 |
| `RH.FALSE_CONTRAST` | relaxed | 0 | 0 | 0 | 3 | 3 | 0.17 |
| `LX.ASSOCIATION_VAGUENESS` | relaxed | 0 | 0 | 0 | 2 | 2 | 0.113 |
| `LX.COPULA_AVOIDANCE` | full | 0 | 0 | 0 | 1 | 1 | 0.057 |

#### Metric distributions

| Rule | Register | Status | Threshold (effective) | n | Min | P25 | Median | P75 | P90 | Max | Crossing (docs) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `RH.TRIAD_DENSITY` | essay-blog | full | gt 0.25 | 12 | 0.0074 | 0.0217 | 0.033 | 0.0414 | 0.0545 | 0.0568 | 0 (0) |
| `RH.TRIAD_DENSITY` | general-prose | full | gt 0.25 | 10 | 0.069 | 0.082 | 0.0854 | 0.1321 | 0.1398 | 0.1408 | 0 (0) |
| `RH.TRIAD_DENSITY` | legal-policy | relaxed | gt 0.5 | 13 | 0.1 | 0.1477 | 0.1915 | 0.3939 | 0.5882 | 0.6222 | 3 (3) |
| `RH.TRIAD_DENSITY` | technical-docs | relaxed | gt 0.5 | 12 | 0 | 0.0102 | 0.0183 | 0.0303 | 0.0909 | 0.3696 | 0 (0) |
| `RH.FORCED_SYMMETRY` | essay-blog | relaxed | gte 6 | 34 | 2 | 2 | 2 | 2 | 3 | 5 | 0 (0) |
| `RH.FORCED_SYMMETRY` | general-prose | full | gte 3 | 53 | 2 | 2 | 2 | 2 | 3 | 4 | 8 (5) |
| `RH.FORCED_SYMMETRY` | legal-policy | relaxed | gte 6 | 30 | 2 | 2 | 2 | 2 | 3 | 12 | 2 (2) |
| `RH.FORCED_SYMMETRY` | technical-docs | relaxed | gte 6 | 16 | 2 | 2 | 2 | 2 | 3 | 3 | 0 (0) |
| `RH.MIRRORED_PAIR` | essay-blog | relaxed | gte 4 | 0 | - | - | - | - | - | - | 0 (0) |
| `RH.MIRRORED_PAIR` | general-prose | full | gte 2 | 0 | - | - | - | - | - | - | 0 (0) |
| `RH.MIRRORED_PAIR` | legal-policy | relaxed | gte 4 | 0 | - | - | - | - | - | - | 0 (0) |
| `RH.MIRRORED_PAIR` | technical-docs | relaxed | gte 4 | 0 | - | - | - | - | - | - | 0 (0) |
| `ST.HEADING_DENSITY` | essay-blog | full | lt 60 | 3 | 371.4 | 371.4 | 450 | 759 | 759 | 759 | 0 (0) |
| `ST.HEADING_DENSITY` | general-prose | full | lt 60 | 8 | 81.4 | 175.3 | 253.8 | 297 | 345.3 | 419.8 | 0 (0) |
| `ST.HEADING_DENSITY` | legal-policy | relaxed | lt 30 | 6 | 54.8 | 87.7 | 119 | 222.4 | 222.4 | 223.3 | 0 (0) |
| `ST.HEADING_DENSITY` | technical-docs | relaxed | lt 30 | 10 | 49.6 | 92.9 | 126.9 | 262.4 | 312 | 379.5 | 0 (0) |
| `ST.HEADING_FRAME_REPEAT` | essay-blog | full | gte 3 | 12 | 0 | 0 | 0 | 0 | 1 | 2 | 0 (0) |
| `ST.HEADING_FRAME_REPEAT` | general-prose | full | gte 3 | 10 | 0 | 1 | 1 | 2 | 4 | 6 | 2 (2) |
| `ST.HEADING_FRAME_REPEAT` | legal-policy | relaxed | gte 6 | 13 | 0 | 0 | 0 | 1 | 2 | 3 | 0 (0) |
| `ST.HEADING_FRAME_REPEAT` | technical-docs | relaxed | gte 6 | 11 | 0 | 1 | 2 | 5 | 9 | 12 | 2 (2) |
| `ST.LABELED_BULLET_RUN` | essay-blog | full | gt 0.5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 (0) |
| `ST.LABELED_BULLET_RUN` | general-prose | full | gt 0.5 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 (0) |
| `ST.LABELED_BULLET_RUN` | legal-policy | relaxed | gt 1 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 (0) |
| `ST.LABELED_BULLET_RUN` | technical-docs | relaxed | gt 1 | 18 | 0 | 0 | 0 | 0 | 0 | 0.5 | 0 (0) |
| `ST.DASH_DENSITY` | essay-blog | relaxed | gt 0.01666 | 12 | 0 | 0 | 0.002 | 0.0024 | 0.0034 | 0.0042 | 0 (0) |
| `ST.DASH_DENSITY` | general-prose | full | gt 0.00833 | 10 | 0 | 0 | 0.0004 | 0.0016 | 0.003 | 0.0069 | 0 (0) |
| `ST.DASH_DENSITY` | legal-policy | relaxed | gt 0.01666 | 13 | 0 | 0 | 0.0004 | 0.0016 | 0.0034 | 0.0082 | 0 (0) |
| `ST.DASH_DENSITY` | technical-docs | relaxed | gt 0.01666 | 12 | 0 | 0 | 0 | 0 | 0 | 0.0138 | 0 (0) |
| `ST.UNIFORM_RHYTHM` | essay-blog | full | lt 4 | 12 | 6.8 | 10.1 | 11.5 | 12.8 | 14.1 | 16.5 | 0 (0) |
| `ST.UNIFORM_RHYTHM` | general-prose | full | lt 4 | 10 | 9 | 10.2 | 11.1 | 14.8 | 17.8 | 23.5 | 0 (0) |
| `ST.UNIFORM_RHYTHM` | legal-policy | relaxed | lt 2 | 13 | 13.3 | 18.8 | 28.8 | 35.5 | 45.5 | 51.5 | 0 (0) |
| `ST.UNIFORM_RHYTHM` | technical-docs | relaxed | lt 2 | 11 | 9.7 | 10.7 | 14.9 | 17.5 | 23.6 | 28.8 | 0 (0) |
| `ST.FRAGMENT_RUN` | essay-blog | full | gte 3 | 41 | 1 | 1 | 1 | 1 | 2 | 3 | 1 (1) |
| `ST.FRAGMENT_RUN` | general-prose | full | gte 3 | 10 | 1 | 1 | 1 | 1 | 1 | 1 | 0 (0) |
| `ST.FRAGMENT_RUN` | legal-policy | relaxed | gte 6 | 29 | 1 | 1 | 1 | 1 | 1 | 2 | 0 (0) |
| `ST.FRAGMENT_RUN` | technical-docs | relaxed | gte 6 | 14 | 1 | 1 | 1 | 1 | 3 | 3 | 0 (0) |
| `ST.SENTENCE_CONTINUITY` | essay-blog | full | gt 0.75 | 12 | 0.349 | 0.396 | 0.418 | 0.563 | 0.616 | 0.638 | 0 (0) |
| `ST.SENTENCE_CONTINUITY` | general-prose | full | gt 0.75 | 10 | 0.243 | 0.286 | 0.308 | 0.333 | 0.35 | 0.394 | 0 (0) |
| `ST.SENTENCE_CONTINUITY` | legal-policy | skip | gt - | 13 | 0.043 | 0.172 | 0.256 | 0.295 | 0.342 | 0.35 | 0 (0) |
| `ST.SENTENCE_CONTINUITY` | technical-docs | skip | gt - | 11 | 0.171 | 0.291 | 0.372 | 0.432 | 0.451 | 0.606 | 0 (0) |
