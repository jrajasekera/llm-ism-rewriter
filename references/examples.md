# Examples

Before/after pairs by category, then a full worked report. Every "after" keeps the original claim strength and adds no facts.

## Lexical

**B1 stock vocabulary + B3 inflated significance**
- Before: *The release marks a pivotal moment in the ever-evolving landscape of container orchestration, serving as a testament to the team's meticulous engineering.*
- After: *The release changes how the scheduler handles node failures.* (only if the text says what changed; otherwise: *This release is the first to change scheduler behavior.* → still unsupported → leave `[specify: what changed?]` and report the gap.)
- Why: the sentence asserted importance without content. The fix is either the content or nothing.

**B2 transitions**
- Before: *Additionally, it is important to note that retries are capped at five.*
- After: *Retries are capped at five.*

**B4 promotional register / copula avoidance**
- Before: *Nestled in the Alps, the town boasts a rich heritage and serves as a hub for winter sports.*
- After: *The town is in the Alps and hosts winter-sports events.* (Kept only what the source established; "rich heritage" carried no claim.)

**B5 vague attribution**
- Before: *Experts agree that Rust eliminates memory-safety bugs.*
- After (source in doc): *The 2024 Android security report attributes the drop in memory-safety bugs to Rust adoption.*
- After (no source): *Rust's ownership model prevents the memory-safety bugs listed above [specify: who is claiming this?].* Reported as a gap.

**B6 participle tail**
- Before: *Revenue rose 12%, underscoring the company's commitment to sustainable growth.*
- After: *Revenue rose 12%.*

**B7 hooks and reactions**
- Before: *Great question! Here's the thing: caching isn't magic. Let's dive in.*
- After: *Caching helps only when reads outnumber writes.* (Content taken from the next paragraph of the source; if no such content, just delete.)

## Rhetorical

**C1 false contrast**
- Before: *It's not about the tools. It's about the process.*
- After: *The process matters more than the tools.* Or, if no one claimed tools mattered: *Fix the process first.*

**C2 rule of three with filler**
- Before: *The API is fast, reliable, and intuitive.*
- After: *The API returns in under 50 ms and has had no outages this year.* (Only if those facts appear in the text; otherwise *The API is fast and reliable* if both are supported, or the sentence is deleted.)

**C3 echo**
- Before: *The parser is a state machine. The lexer is a state machine. The renderer is a state machine.*
- After: *The parser, lexer, and renderer are each state machines.*

**C4 aphorism closer**
- Before: *We shipped on Tuesday. And that matters.*
- After: *We shipped on Tuesday.*

**C5 restatement**
- Before: *Latency dropped 40% after enabling compression. In other words, compression made responses significantly faster.*
- After: *Latency dropped 40% after enabling compression.*

**C6 generic intro/outro**
- Before (intro): *In today's fast-paced digital world, monitoring has become increasingly important for organizations of all sizes.*
- After: delete; begin with the first specific sentence.
- Before (outro): *In conclusion, monitoring is essential. Despite these challenges, the future looks bright.*
- After: delete, or end on the last concrete recommendation already in the piece.

## Structural

**D2 bullets with bold lead-ins (in a narrative blog post)**
- Before:
  - **Speed:** The new build is faster.
  - **Size:** The bundle is smaller.
  - **DX:** Developers like it.
- After: *The new build is faster and the bundle is smaller; the two developers who tried it preferred it.* (The "two developers" must come from the text; otherwise *developers who tried it preferred it*.)

**D3 em-dash density**
- Before: *Caching—when done right—cuts latency—but it adds complexity—and complexity has a cost.*
- After: *Done right, caching cuts latency, but it adds complexity, and complexity has a cost.*

**D4 uniform rhythm**
- Before: five consecutive 16-word sentences.
- After: merge two into one 30-word sentence; leave one 6-word sentence standing. No content change.

## What a good rewrite does *not* do

- Before: *The migration completed successfully with no data loss.*
- Bad after: *Honestly? The migration just… worked. No drama, no data loss. Wild.* (fake candor, fragments, theatrical punctuation)
- Bad after: *The migration completed on March 3 with zero errors across 2.1M rows.* (invented specifics)
- Bad after: *The migration completed, though some data may have been lost.* (changed the claim)
- Good after: unchanged. The sentence was fine.

## Worked example: `rewrite` mode

Input (excerpt):

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
- [Cliché] ¶1: "ever-evolving landscape", "delve" — stock vocabulary cluster (B1) with generic intro (C6); cut.
- [Cliché] ¶1: "isn't just a nice-to-have—it's a necessity" — false contrast (C1) + em dash (D3); restated plainly.
- [Gap] ¶1: "Experts argue" — no source in text (B5); marked [specify: who?].
- [Protected] ¶2: blockquote left unchanged.
- [Cliché] ¶3: "Here's the twist" — hook (B7); deleted. "That's not a tooling problem, it's a culture problem" — contrast (C1); kept, because the paragraph argues against the tooling explanation.
- [Fingerprint] ¶4: "Hope this helps!" — chatbot residue (A1); deleted.
- [Cliché] ¶4: "In conclusion… testament to" — generic outro (C6) + inflated significance (B3); deleted.

## Revised text
Observability is a necessity for distributed systems. Teams without tracing face several challenges [specify: according to whom?].

> "Logs are the first thing I check and the last thing I trust." — an SRE I worked with

Most teams already collect the data. They just can't correlate it. That's not a tooling problem, it's a culture problem.

## Notes
Second audit: the revised ¶1 opened "Observability matters because…" in draft; changed to a direct statement to avoid a new generic opener. Density: moderate. Not evidence of authorship.
```

Note what stayed: the SRE quote, the author's contrast that carried a real argument, the claim strength ("necessity"), and the hedge-free tone of the original. Note what was not added: a named expert, a statistic, a joke.
