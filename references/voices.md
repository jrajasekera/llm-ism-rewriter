# Voice profiles

Read this **only** when the user names a voice or supplies a style sample.
Otherwise the voice is `preserve` and this file stays unread.

Voice is a separate axis from context. `references/contexts.md` decides which
patterns count as findings in this genre; voice decides how the spans you are
already rewriting should sound. Voice never widens the edit: a clean paragraph
stays clean regardless of the requested voice, unless the user explicitly asks
for a full revoice of the document.

## The default: `preserve`

Match the source's own contractions, sentence cadence, first- and second-person
use, formality, terminology, and punctuation habits. Do not normalize the
document toward any house style, including a "clean professional" one. If the
source uses "doesn't" and semicolons, so does the revision.

`preserve` is the default because the most common failure of a "humanizer" is
not leaving a cliché behind. It is quietly replacing the author with a
generically competent narrator.

## The bounded profiles

Every profile below is bounded by the same rule: **it may change how the source
says something; it may never change what the source says or knows.**

| Voice | Does | Does not |
|-------|------|----------|
| `plain` | Shorter constructions, direct verbs, common words. | Remove technical terms that carry meaning, or soften a claim. |
| `formal` | Complete sentences, controlled register, consistent terminology. | Add *furthermore*/*moreover*, nominalizations, passive voice, or inflated vocabulary. Formality is not ornament. |
| `casual` | Contractions **if the source already supports them**, simpler syntax, plainer words. | Add slang, jokes, fake candor, interjections, fragments, or typos. |
| `technical` | Explicit subjects, exact verbs, stable terminology, imperative instructions. | Replace a repeated technical term with a synonym for variety. |
| `warm` | Keep existing acknowledgment and reader orientation; second person if the source uses it. | Add performative empathy, praise, or reassurance the source did not offer. |
| `blunt` | Lead with the claim, cut the windup, put the conclusion first. | Remove hedges that carry real uncertainty, or become rude. Blunt is not staccato. |

## Universal limits

No voice profile may:

- add first person, anecdotes, humour, opinions, emotional reactions, or stakes
- add certainty the source did not express, or remove uncertainty it did
- add or change facts, names, dates, numbers, or sources
- "roughen" prose with planted typos, slang, fragments, or punctuation tricks
- override a user-supplied house style or style guide
- re-voice sentences that were not otherwise being edited

The last one is the one most often broken. A voice request is not a licence to
rewrite the document.

## Style-sample calibration

When the user supplies a sample of their own writing, read observable properties
from it *before* editing, and state what you read:

```json
{
  "contraction_rate": 0.62,
  "first_person": true,
  "median_sentence_words": 14,
  "short_sentence_share": 0.21,
  "paragraph_median_sentences": 3,
  "em_dash_per_1000": 1.8,
  "preferred_terms": ["use", "build", "problem"],
  "avoided_terms": ["leverage"]
}
```

These are targets, not quotas. Never contort a sentence to hit a statistic, and
never report a match against one as if it were a measure of success.

Copy the sample's *habits*, never its content. Do not reuse its phrases,
examples, opinions, or subject matter. A style sample is evidence about how the
author writes, not material to write with.

## Conflicts

If the requested voice conflicts with the document's established voice, say so
in one sentence, apply the request to the spans you are rewriting, and leave the
rest alone. The user's request wins; the rest of the document is not collateral.
