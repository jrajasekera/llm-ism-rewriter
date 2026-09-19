# Examples

Before/after pairs by category, then counterexamples, narrative-prose examples, and two worked reports. Every "after" keeps the original claim strength and adds no facts.

Examples carry stable IDs. Where an ID appears in `tests/fixtures/`, the behavior is pinned by a test rather than by this prose.

## Lexical

**EX-LX-01 — stock vocabulary cluster + inflated significance** (`LX.STOCK_VOCAB_CLUSTER`, `LX.INFLATED_SIGNIFICANCE`)
- Before: *The release marks a pivotal moment in the ever-evolving landscape of container orchestration, serving as a testament to the team's meticulous engineering.*
- After: *The release changes how the scheduler handles node failures.* — only if the text says what changed. If it does not: *The release changes scheduler behaviour [specify: in what way?]*, reported as a gap.
- Why: the sentence asserted importance without content. The fix is the content or nothing.

**EX-LX-02 — transitions** (`LX.STOCK_TRANSITION`)
- Before: *Additionally, it is important to note that retries are capped at five.*
- After: *Retries are capped at five.*

**EX-LX-03 — promotional register and copula avoidance** (`LX.PROMOTIONAL_REGISTER`, `LX.COPULA_AVOIDANCE`)
- Before: *Nestled in the Alps, the town boasts a rich heritage and serves as a hub for winter sports.*
- After: *The town is in the Alps and hosts winter-sports events.* — "rich heritage" carried no claim, so it goes.

**EX-LX-04 — vague attribution** (`LX.VAGUE_AUTHORITY`)
- Before: *Experts agree that Rust eliminates memory-safety bugs.*
- After, source in the document: *The 2024 Android security report attributes the drop in memory-safety bugs to Rust adoption.*
- After, no source: *Rust's ownership model prevents the memory-safety bugs listed above [specify: who is claiming this?].* Reported as a gap.

**EX-LX-05 — participle tail** (`LX.PARTICIPLE_TAIL`)
- Before: *Revenue rose 12%, underscoring the company's commitment to sustainable growth.*
- After: *Revenue rose 12%.*

**EX-LX-06 — hooks and reactions** (`LX.ENGAGEMENT_HOOK`)
- Before: *Great question! Here's the thing: caching isn't magic. Let's dive in.*
- After: *Caching helps only when reads outnumber writes.* — content taken from the next paragraph of the source. If there is no such content, just delete.

## Rhetorical

**EX-RH-01 — false contrast** (`RH.FALSE_CONTRAST`)
- Before: *It's not about the tools. It's about the process.*
- After: *The process matters more than the tools.* Or, if nobody claimed tools mattered: *Fix the process first.*

**EX-RH-02 — rule of three with filler** (`RH.TRIAD_DENSITY`)
- Before: *The API is fast, reliable, and intuitive.*
- After: *The API returns in under 50 ms and has had no outages this year* — only if those facts are in the text. Otherwise *The API is fast and reliable* if both are supported, or the sentence goes.

**EX-RH-03 — echo** (`RH.FORCED_SYMMETRY`)
- Before: *The parser is a state machine. The lexer is a state machine. The renderer is a state machine.*
- After: *The parser, lexer, and renderer are each state machines.*

**EX-RH-04 — aphorism closer** (`RH.APHORISM_CLOSER`)
- Before: *We shipped on Tuesday. And that matters.*
- After: *We shipped on Tuesday.*

**EX-RH-05 — restatement** (`RH.LOW_INFORMATION_RESTATEMENT`)
- Before: *Latency dropped 40% after enabling compression. In other words, compression made responses significantly faster.*
- After: *Latency dropped 40% after enabling compression.*

**EX-RH-07 — three paragraphs, one job** (`RH.LOW_INFORMATION_RESTATEMENT`, `LX.INFLATED_SIGNIFICANCE`)
- Before, three consecutive paragraphs of a release post: the first calls the release important for the platform; the second says it represents meaningful progress for teams that depend on it; the third closes by saying that this is why the release matters. No paragraph names a capability, a limitation, or a consequence, and no two share a phrase.
- After: keep whichever paragraph carries a concrete claim. If none does: delete two, keep one, and report a `[Gap]`: the post says the release matters and never says what it changes.
- Method: write down each paragraph's distinct contribution in a few words. Paragraphs that come out the same are one paragraph. Repeated words are not the test, and neither is their absence.
- Leave alone: an executive summary above a detailed section, and a teaching recap at the end of a lesson. Each repeats on purpose for a reader who needs it, and each has a job the body does not do.

**EX-RH-06 — generic intro and outro** (`RH.GENERIC_INTRO`, `RH.GENERIC_OUTRO`)
- Before, intro: *In today's fast-paced digital world, monitoring has become increasingly important for organizations of all sizes.*
- After: delete; begin with the first specific sentence.
- Before, outro: *In conclusion, monitoring is essential. Despite these challenges, the future looks bright.*
- After: delete, or end on the last concrete recommendation already in the piece.

## Structural

**EX-ST-01 — labeled bullets in a narrative post** (`ST.LABELED_BULLET_RUN`)
- Before:
  - **Speed:** The new build is faster.
  - **Size:** The bundle is smaller.
  - **DX:** Developers like it.
- After: *The new build is faster and the bundle is smaller; the two developers who tried it preferred it.* — "two developers" must come from the text; otherwise *developers who tried it preferred it*.

**EX-ST-02 — em-dash density** (`ST.DASH_DENSITY`)
- Before: *Caching—when done right—cuts latency—but it adds complexity—and complexity has a cost.*
- After: *Done right, caching cuts latency, but it adds complexity, and complexity has a cost.*

**EX-ST-03 — uniform rhythm** (`ST.UNIFORM_RHYTHM`)
- Before: five consecutive 16-word sentences.
- After: merge two into one 30-word sentence; leave one 6-word sentence standing. No content change, and no fragments planted elsewhere to "balance" it.

**EX-ST-04 — phrase triad** (`RH.PHRASE_TRIAD`)
- Before: *You can define workflows as graphs, trigger them during a run, and inspect their state live.*
- After, if all three are real capabilities: unchanged. This is an enumeration, not padding.
- After, if the third is filler: *You can define workflows as graphs and trigger them during a run.*
- The rule surfaces the shape. Whether the third clause carries a fact is a judgment.

## No-change examples

The correct output is byte-identical text. A rewrite here is a failure.

**EX-NC-01 — already direct**
> The migration completed successfully with no data loss.

**EX-NC-02 — a hedge that carries real uncertainty**
> In our tests the cache reduced p99 latency, though we did not isolate the effect of the concurrent index change.

**EX-NC-03 — three real items**
> The release ships the CLI, the SDK, and the web console.

**EX-NC-04 — first person as attribution**
> I think the retry budget is too generous, but I have not measured it.

## False positives to leave alone

**EX-FP-01 — literal senses** (`LX.STOCK_VOCAB_CLUSTER`)
> The survey used robust standard errors, and the excavation delved two metres into the alluvial landscape.
> Three matches, zero findings. Every one is literal.

**EX-FP-02 — documentation caveat** (`LX.STOCK_TRANSITION`)
> Note that `--force` skips the integrity check.
> A genuine caveat in a technical document. Relaxed by the profile and left alone.

**EX-FP-03 — a real prior belief** (`RH.FALSE_CONTRAST`)
> The bottleneck isn't the database, as the earlier profile suggested; it's serialization.
> The rejected belief is named and was actually held. Keep the contrast; say why in the report.

**EX-FP-04 — legal term of art** (`LX.ASSOCIATION_VAGUENESS`)
> Liability arising in connection with the Services shall be limited as set out in Section 8.
> Skipped in `legal-policy`.

**EX-FP-05 — a reference list** (`ST.LABELED_BULLET_RUN`)
> - **`--dry-run`:** Report the changes without applying them.
> - **`--profile`:** Select a context profile.
> A parameter list is exactly what labeled bullets are for.

**EX-FP-06 — a speech** (`RH.FORCED_SYMMETRY`, `RH.TRIAD_DENSITY`)
> We will not yield. We will not retreat. We will not forget.
> `creative` and speech contexts skip structural rules entirely. Fingerprints only.

## Overlapping evidence

**EX-OV-01 — one span, several rules, one finding**
> The release marks a pivotal moment in the ever-evolving landscape—serving as a testament to the team's meticulous work.

This matches `LX.STOCK_VOCAB_CLUSTER`, `LX.INFLATED_SIGNIFICANCE`, `LX.FIGURATIVE_LANDSCAPE`, and contributes to `ST.DASH_DENSITY`. The reader gets **one** finding:

```
[P1 cliche] L4: "marks a pivotal moment in the ever-evolving landscape—serving as a testament to"
    Inflated significance and a stock-vocabulary cluster on one span.
    evidence: LX.INFLATED_SIGNIFICANCE, LX.FIGURATIVE_LANDSCAPE, LX.STOCK_VOCAB_CLUSTER (high)
    action: replace the significance claim with the stated effect, or remove it if no effect is supplied.
```

Do not report it four times, and do not treat four matches as four times the severity.

## The same text in three modes

Source: *In conclusion, the parser is robust, fast, and reliable. Hope this helps!*

- **`detect`:** two findings (`RH.GENERIC_OUTRO`, `FP.CHATBOT_RESIDUE`), one candidate suppressed (`RH.TRIAD_DENSITY`, single triad below threshold). Text untouched. No revised version offered unless asked.
- **`rewrite`:** returns *The parser is fast and has not crashed in production* — only if the source supports both claims; otherwise *The parser is fast and reliable.* Plus findings, change summary, and validation.
- **`edit`:** the two flagged spans change in the file. Any adjacent clean paragraph stays byte-identical, and the report says so.

## Context changes the answer

**EX-CX-01 — a triad in a keynote**
> We build for speed, for scale, and for the people who ship at 2 a.m.
> `creative`/speech: not a finding. Report that structural rules were skipped and why.

**EX-CX-02 — the same shape repeated through product copy**
> Fast, reliable, and secure. Simple, powerful, and flexible. Built for speed, scale, and safety.
> `marketing-product`: triads are relaxed, not skipped. Three in a row clears even the relaxed threshold. The fix is to keep the one triad that names real capabilities.

## Voice

**EX-VO-01 — `preserve` (default)**
- Before: *We shipped it Tuesday and it's held up fine, though we haven't load-tested the new path.*
- After: unchanged. Contractions, first person, and the hedge are the author's.

**EX-VO-02 — explicitly requested `blunt`**
- Before: *It is worth noting that, in our view, the retry budget may possibly be somewhat too generous.*
- After: *In our view the retry budget may be too generous.*
- Kept: "in our view" (attribution), "may" (real uncertainty). Cut: the windup and the stacked hedges. Blunt does not mean certain.

**EX-VO-03 — requested `casual`, done wrong**
- Bad after: *Honestly? The retry budget is just… way too chill. Wild.*
- Fake candor, planted fragments, theatrical punctuation, and an opinion the source hedged. Every one of these is prohibited regardless of the requested voice.

## Narrative prose

For prose fiction under `narrative-review.md`. Each example gives the context the judgment depends on; a narrative finding made without context is a guess. Examples set in italics or blockquotes here are presentation. Anyone turning one into a test supplies the underlying prose as plain editable text, so that the test does not exercise the protected-blockquote path by accident.

**EX-NR-01 — a second explanation, removed; the position, kept** (`ST.NARRATIVE_THEME_REDUNDANCY`)
- Before: *Mira stayed until the last box was packed. To her, loyalty meant staying when leaving would have been easier. In other words, she understood loyalty as remaining when departure offered the easier choice.*
- After: *Mira stayed until the last box was packed. To her, loyalty meant staying when leaving would have been easier.*
- Why: the third sentence restates a belief the second already made explicit. The second stays because it carries the belief and attributes it to Mira. Deleting both explanatory sentences would be a much stronger editorial choice, and nothing in a clean-up request authorizes it.

**EX-NR-02 — a feeling named once and explained twice** (`ST.NARRATIVE_EMOTION_REDUNDANCY`)
- Before: *Tomas was ashamed of the letter. Shame was what he felt when he looked at it, a deep sense of being ashamed of what he had written. He put it back in the drawer.*
- After: *Tomas was ashamed of the letter. He put it back in the drawer.*
- Bad after: *Tomas's face burned as he looked at the letter. He put it back in the drawer.* The source has no burning face. This invents a bodily reaction and deletes a label that was doing its job.

**EX-NR-03 — the gloss goes, the weather stays** (`ST.NARRATIVE_DECORATIVE_MIRRORING`)
- Before: *Rain had come in off the estuary since noon, and the lane to the farm was under a hand of water. The rain seemed to grieve with her. In the kitchen the stove had gone out and the window over the sink had fogged, as if the house too were mourning. Even the yard looked sorrowful, in sympathy with what she felt.*
- After: *Rain had come in off the estuary since noon, and the lane to the farm was under a hand of water. The rain seemed to grieve with her. In the kitchen the stove had gone out and the window over the sink had fogged.*
- Why: three glosses gave one reading. The first stays. The flooded lane, the dead stove, and the fogged window are facts of the scene and all survive. The yard sentence held nothing else.

**EX-NR-04 — a duplicate explanation and a unique assertion** (`ST.NARRATIVE_FORCED_CLOSURE`)
- Context: across the story Anneke cannot decide whether she forgives her late husband, and the scene before the last ends with her saying she may never know.
- Before, the final paragraphs: *She signed the papers and slid the keys across the desk. Outside, she did not look back at the house.* Then: *In letting the house go she had let go of him too. Selling it had been her way of releasing him, and with the keys went the last of her hold on the past. She had forgiven him.*
- After: the second commentary sentence is removed. It restates the first. Nothing else changes.
- Reported as `[Decision]` and left in place: *She had forgiven him.* It is the only statement of forgiveness in the story, and it settles a question the previous scene held open. Cutting it changes the ending, and so does keeping it. That is the author's call.

**EX-NR-05 — a timing question, reported and not acted on** (`ST.NARRATIVE_INFORMATION_TIMING`)
- Source structure: the first paragraph names the thief. A later scene takes the detective, step by step, to the same name.
- Report: both readings, with their locations. The early disclosure may be dramatic irony, with the reader watching the detective catch up. It may also undercut a mystery the later scene is staged as. Nothing moves. Relocating the first paragraph needs restructuring authority, and the research this check draws on is no reason to prefer a delayed reveal.

### Narrative no-change examples

The correct output is the source, unchanged.

**EX-NR-06 — a plain emotion label**
> I was afraid. I locked the door and waited.
> No racing pulse, no tight throat, no description of the room. Each would be invented.

**EX-NR-07 — a symptom with a plot function**
> His hands shook so badly that he dropped the key into the drain. The shaking had begun before he entered the house.
> The symptom causes an event, and its timing is unexplained on purpose. An emotion label here would delete a fact and impose a reading.

**EX-NR-08 — an ambiguity the story keeps**
> He laughed when the verdict came. Later, nobody agreed on what the laugh had meant.
> Do not call the laugh relief, bitterness, or triumph. The open question is the content.

**EX-NR-09 — an unspecified reference**
> The novel on her desk reminded her of home.
> Leave the novel unnamed. A title, an author, or a brand would be an invented fact. Optional specificity can be offered in the report and nowhere else.

**EX-NR-10 — a linear story in one place with no subplot.** Told in order, in a single kitchen, with two characters and one question. Nothing to report. Order, unity of place, and a single plot line are choices.

**EX-NR-11 — an earned happy ending.** The sisters reconcile in the last scene, after three scenes in which each gives something up. No added doubt, no cynical coda, no external event to "complicate" it.

**EX-NR-12 — the moral of a fable.** A closing line that states the lesson is the form doing its work. It is a finding only when the fable states it twice.

**EX-NR-13 — reader address the author chose.** A narrator who has said "you" since the first page keeps saying it, and a narrator who never has does not start.

**EX-NR-14 — a conclusion outside fiction**
> The rollback restored service. We have not identified the cause of the connection leak.
> An incident report states its outcome and its open question directly. No narrative rule applies to it.

### Worked report: an author decision and no structural edit

Request: "Make the ending of this story less formulaic." The whole story was supplied. The ending is EX-NR-04.

```
## Findings
- [P1 structural] Sc6 ¶41: "Selling it had been her way of releasing him, and with the keys went
  the last of her hold on the past" restates ¶41's first sentence (ST.NARRATIVE_FORCED_CLOSURE,
  RH.LOW_INFORMATION_RESTATEMENT). Removed.
- [Decision] Sc6 ¶41: "She had forgiven him." The only statement of forgiveness in the story. Sc5
  ends with Anneke saying she may never know, so this sentence settles what the story held open.
  Requires an author decision; left in place, and no structural edit made.
- [Leave] Sc6 ¶40: "she did not look back at the house" is the substantive ending, an action.
  Unchanged.

## Validation
Mechanical checks: passed under --profile creative (no protected spans; negation and modality
counts unchanged).
Narrative preservation: reviewed. Events, viewpoint, and the order in which the reader learns
things are unchanged. The open question from Sc5 is exactly as open or closed as the author left it.
Second audit: the revision adds no new interpretation, reaction, or resolution.

Coverage: whole story read (6 scenes, 41 paragraphs). Edited: Sc6 only, as requested.
Context: creative, prose fiction (stated by the user). Voice: preserve.
Not evidence of authorship.
```

One sentence changed. The most useful part of the report is the decision it hands back.

## Validation failures

Rewrites that read cleaner and fail `scripts/llm_ism_validate.py`.

**EX-VF-01 — hedge dropped**
- Before: *The service may fail when the queue exceeds 50 ms of lag.*
- After: *The service fails when the queue exceeds lag.*
- `FAIL: negation/modality` — "may" is gone, and so is "50 ms". Two claims changed.

**EX-VF-02 — version narrowed**
- Before: *Requires Python 3.11+.* → After: *Requires Python 3.11.*
- `FAIL: versions` — a different claim about compatibility.

**EX-VF-03 — flag removed for smoothness**
- Before: *Run `--dry-run` first.* → After: *Run it first.*
- `FAIL: inline code, command flags`.

**EX-VF-04 — negation inverted**
- Before: *Traffic did not increase after the rollout.* → After: *Traffic increased after the rollout.*
- `FAIL: negation`.

**EX-VF-05 — a "helpfully" reformatted code block**
- Reindenting or reflowing a fenced block is a `FAIL: code blocks`, even when the code is equivalent.

**EX-VF-06 — quoted wording polished**
- Editing a word inside an attributed blockquote is a `FAIL: attributed quotations`, even to fix a cliché in it.

### Surface changes that should pass

- *five* ↔ *5* — warning only; the claim is unchanged.
- *does not* ↔ *doesn't* — the validator expands contractions before comparing.
- Splitting or merging sentences while every anchor survives.
- Reordering adjectives with no factual change.
- Straight ↔ curly quotes, when the user asked for that normalization.

## What a good rewrite does *not* do

- Before: *The migration completed successfully with no data loss.*
- Bad: *Honestly? The migration just… worked. No drama, no data loss. Wild.* — fake candor, fragments, theatrical punctuation.
- Bad: *The migration completed on March 3 with zero errors across 2.1M rows.* — invented specifics.
- Bad: *The migration completed, though some data may have been lost.* — changed the claim.
- Good: unchanged. The sentence was fine.

## Worked example: `rewrite` mode

Input:

> In today's ever-evolving landscape of distributed systems, observability isn't just a nice-to-have—it's a necessity. Experts argue that teams without tracing face several challenges. Let's delve into why.
>
> > "Logs are the first thing I check and the last thing I trust." — an SRE I worked with
>
> Here's the twist: most teams already collect the data. They just can't correlate it. That's not a tooling problem, it's a culture problem.
>
> In conclusion, observability is a testament to engineering maturity. Hope this helps!

Report:

```
## Findings
- [P1 cliche] ¶1: "In today's ever-evolving landscape" + "delve" — stock-vocabulary cluster and
  generic intro (LX.FIGURATIVE_LANDSCAPE, RH.GENERIC_INTRO, LX.STOCK_VOCAB_CLUSTER). Cut.
- [P1 cliche] ¶1: "isn't just a nice-to-have—it's a necessity" — false contrast on a belief
  nobody holds, plus an em dash doing a colon's work (RH.FALSE_CONTRAST). Restated plainly.
- [Gap] ¶1: "Experts argue" — no source in the text (LX.VAGUE_AUTHORITY). Marked
  [specify: who?] rather than inventing one.
- [Protected] ¶2: blockquote left unchanged; it contains no finding requiring action.
- [P1 cliche] ¶3: "Here's the twist" — engagement hook (LX.ENGAGEMENT_HOOK). Deleted.
- [Leave] ¶3: "That's not a tooling problem, it's a culture problem" — false contrast kept.
  The paragraph argues against the tooling explanation, so the rejected belief is real.
- [P0 fingerprint] ¶4: "Hope this helps!" — chatbot residue (FP.CHATBOT_RESIDUE). Deleted.
- [P1 cliche] ¶4: "In conclusion… a testament to" — generic outro and inflated significance
  (RH.GENERIC_OUTRO, LX.INFLATED_SIGNIFICANCE). Deleted; the source supplies no effect.

## Revised text
Observability is a necessity for distributed systems. Teams without tracing face several
challenges [specify: according to whom?].

> "Logs are the first thing I check and the last thing I trust." — an SRE I worked with

Most teams already collect the data. They just can't correlate it. That's not a tooling
problem, it's a culture problem.

## Change summary
Four spans removed, one restated, one kept with a reason, one gap marked. The quote,
the author's real contrast, the claim strength ("necessity"), and the hedge-free tone
are unchanged.

## Validation
Protected content: quotation byte-identical. Claim anchors: no numbers, versions, or
identifiers in the source; negation and modality counts unchanged. Second audit: the
first draft of ¶1 opened "Observability matters because…", a new generic opener; replaced
with a direct statement before reporting. No new pattern in the final text.

Context: general-prose (default). Voice: preserve.
Density: moderate — 6 findings across 96 scanned prose words, including one fingerprint.
Not evidence of authorship.
```

Note what stayed: the SRE quote, the author's contrast that carried a real argument, the claim strength, and the tone. Note what was not added: a named expert, a statistic, a joke. Note that only one version of the text appears — the second audit ran before the report, not after it.
