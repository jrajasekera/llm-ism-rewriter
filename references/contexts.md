# Contexts, genres, and legitimate uses

Read this before flagging structural patterns (D-tier) or when the text's genre differs from general prose. The question is always: *would a competent writer in this genre do this on purpose?*

## Genre norms

| Genre | Patterns that are normal here | Still worth flagging |
|-------|-------------------------------|----------------------|
| Technical docs, READMEs, API references | Headings every few paragraphs; bullets; bold on option/flag names; short uniform sentences; "Note that…"; triads in feature lists; "Additionally" in changelogs | Promotional adjectives (B4), inflated significance (B3), vague authority (B5), chatbot residue (A1) |
| Academic and scientific writing | Hedges ("suggests", "may"); "Furthermore/Moreover"; passive voice; "plays a role"; participle tails when they summarize the paper's own result | "cannot be overstated", "testament to", fake citations (A3), "experts agree" without citation |
| Marketing, landing pages, product copy | Rule of three; short punchy contrasts; bold; some promotional register; engagement hooks in headlines | Stacked superlatives with no concrete claim; "not just X, but Y" more than once; "seamless/robust/leverage" clusters |
| Journalism, essays, blog posts | Varied rhythm; a single rhetorical question; one deliberate contrast; em dashes used consistently by the author | Generic intros/outros (C6), "experts say" without naming (B5), aphorism closers (C4), "Here's the thing" openers (B7) |
| Speeches, sermons, manifestos, ad slogans | Anaphora; triads; echo structures; "not X but Y"; short repeated sentences | Almost nothing structural. Only fingerprints (A) and stock vocabulary clusters (B1). Say so in the report. |
| Fiction, poetry, lyrics | Everything structural; fragments; any punctuation | Only A-tier. Do not touch voice. Recommend `detect` mode. |
| Legal, policy, compliance text | Formal connectives; repetition for precision; "in connection with"; defined-term restatement | Placeholders (A2); marketing register (B4) |
| Chat replies, Slack, email | "Let me know if…", "Hope this helps", "Great question" are ordinary courtesy | Stock vocabulary clusters, false contrasts, canned significance |
| Wiki/encyclopedic prose | Neutral register; simple copulas; explicit citations | The entire Wikipedia catalog applies; promotional register and vague attribution are the most common problems |
| Non-native English writing | Formal connectives ("Moreover"), textbook phrases, safe vocabulary | Treat B1/B2 with extra caution; do not raise density on these alone. Never comment on the author's proficiency. |

## Legitimate uses of otherwise-flagged patterns

- **False contrast (C1)** is fine when the reader plausibly holds the rejected belief and the text names it: "The bottleneck isn't the database, as the earlier profile suggested; it's serialization."
- **Rule of three (C2)** is fine when there are exactly three real items ("the CLI, the SDK, and the web console").
- **Anaphora/echo (C3)** is fine when the author is clearly building rhythm in a persuasive passage.
- **"Delve", "landscape", "robust"** are fine in their literal or field-specific senses (archaeology, geography, statistics: "robust standard errors").
- **Em dashes (D3)** are fine when the author uses them consistently and at a sane rate throughout, including in unflagged paragraphs.
- **Bold lead-ins on bullets (D2)** are fine in reference lists, glossaries, and option tables.
- **"Note that" (B2)** is fine before a genuine caveat in documentation.
- **First-person "I think" / "we found"** is not a cliché; it is attribution. Keep it.
- **Hedges** ("may", "appears to", "in our tests") preserve the author's uncertainty. Never strengthen or remove them to sound "confident".

## Voice and register constraints from the user

If the user specifies a register (plain, formal, casual, technical, warm, terse):
- Apply it only to sentences you are already rewriting. Do not re-voice clean sentences.
- "Casual" never means slang, typos, fragments, or interjections. It means shorter sentences, contractions if the document already uses them, and plainer words.
- "Formal" never means adding "Furthermore/Moreover" or copula avoidance.
- If the document's existing voice conflicts with the requested register, note it and follow the user's request for the rewritten spans only.

## Scope in files

- Under ~300 lines or a clearly named section: proceed.
- Larger, with no section named, in `rewrite` or `edit` mode: report findings for the whole file, then ask which section(s) to rewrite. Do not rewrite everything on the assumption that the user wants it.
- Multiple files: handle each separately; never carry a "voice" from one file into another.

## Things that are not signals (don't flag)

Correct grammar, formal tone, a well-organized structure, technical vocabulary, consistent citations, absence of typos, use of Markdown, neutral register. None of these indicate anything about how the text was produced, and flagging them wastes the reader's attention.
