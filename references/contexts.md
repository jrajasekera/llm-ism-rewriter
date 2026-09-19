# Contexts, genres, and legitimate uses

Read this before flagging structural patterns, when the genre differs from general prose, or when deciding scope in a long file. The question is always: *would a competent writer in this genre do this on purpose?*

Context profiles are data. `references/rules.json` carries the same eight profiles the checker applies, so the agent and the script agree. A profile changes **thresholds and coverage only**. It never changes the trust boundary or the meaning-preservation invariants.

## The profiles

| Profile | Use it for | Detected from |
|---------|-----------|---------------|
| `general-prose` | The default, and the fallback whenever cues are weak or conflicting | — |
| `technical-docs` | READMEs, API references, runbooks, changelogs | Fenced code, command examples, install/usage/API headings |
| `academic-research` | Papers, abstracts, theses, literature reviews | Abstract/methods/results headings with bracketed citations |
| `marketing-product` | Landing pages, launch posts, product copy | Headline/subheadline pair, call to action |
| `essay-blog` | Essays, opinion pieces, newsletters | Byline, sustained first-person narrative |
| `social-email` | Email, chat, short posts | Salutation and sign-off |
| `legal-policy` | Contracts, terms, compliance text | Numbered obligations, defined parties, *shall*/*must* |
| `creative` | Fiction, poetry, lyrics, scripts | Dialogue, scene narration, verse |

**Guess conservatively.** A wrong implicit profile does more damage than the conservative default. Use `general-prose` unless the cues are strong, and always report which profile you applied and why, so the user can correct you. The checker reports `profile_source: explicit | auto | default` for the same reason.

## Tolerance matrix

`full` = registry thresholds unchanged. `relaxed` = thresholds doubled and evidence strength dropped one level. `skip` = not evaluated.

| Rule family | general | technical | academic | marketing | essay | social | legal | creative |
|---|---|---|---|---|---|---|---|---|
| Chat courtesy (`fingerprint`) | full | full | full | full | full | relaxed¹ | full | full |
| Tool residue, cutoff, leakage (`residue`) | full | full | full | full | full | full | full | full |
| Stock vocabulary clusters | full | relaxed | relaxed | full | full | relaxed | relaxed | skip |
| Stock transitions | full | relaxed | relaxed | full | full | relaxed | relaxed | skip |
| Inflated significance | full | full | full | full | full | full | full | skip |
| Promotional register | full | full | full | relaxed | full | relaxed | full | skip |
| Vague attribution | full | full | full | full | full | relaxed | full | skip |
| Participle tails | full | full | relaxed | full | full | relaxed | relaxed | skip |
| Hooks and canned reactions | full | full | full | full | full | relaxed | full | skip |
| Association vagueness | full | relaxed | relaxed | full | full | skip | skip | skip |
| False contrast | full | relaxed | relaxed | relaxed | full | relaxed | relaxed | skip |
| Triads | full | relaxed | relaxed | relaxed | full | relaxed | relaxed | skip |
| Forced symmetry | full | relaxed | relaxed | relaxed | relaxed | skip | relaxed | skip |
| Aphorism closers | full | full | full | full | full | relaxed | full | skip |
| Restatement | full | full | relaxed | full | full | relaxed | skip | skip |
| Generic intro/outro | full | full | relaxed | full | full | relaxed | relaxed | skip |
| Headings | full | relaxed | relaxed | relaxed | full | skip | relaxed | skip |
| Labeled bullets | full | relaxed | relaxed | full | full | skip | relaxed | skip |
| Em-dash density | full | relaxed | relaxed | relaxed | relaxed | skip | relaxed | skip |
| Cadence and fragments | full | relaxed | relaxed | full | full | skip | relaxed | skip |
| Layout and tables | full | relaxed | relaxed | full | full | skip | relaxed | skip |
| Sentence continuity | full | skip | relaxed | relaxed | full | skip | skip | skip |
| Opening identity | full | full | skip | full | relaxed | skip | skip | skip |
| Clarity edits | skip² | full | skip² | full | skip² | skip² | skip² | skip |
| Narrative construction (`narrative`) | skip | skip | skip | skip | skip | skip | skip | full³ |

¹ In email and chat, "Hope this helps" and "Let me know if…" are ordinary courtesy, so the `fingerprint` family relaxes there. Knowledge-cutoff text, leaked tool markup, unfilled placeholders, and prompt leakage live in the separate `residue` family and stay at full strength in every profile, including `creative`.
² Clarity edits are raised only when the user asked for general editing, whatever the profile.
³ Judgment-only, so the checker reports nothing for it. `full` enables the family; the prose-fiction gate below decides whether it applies to the text in hand.

## Fiction: two layers

The `creative` profile and the narrative review do separate jobs.

- **The deterministic layer** is the checker under `creative`. It reports residue and chat courtesy and skips every lexical, rhetorical, and formatting family. Fragments, anaphora, heavy punctuation, and any diction are the author's. This has not changed.
- **The narrative layer** is the agent reading for meaning under `narrative-review.md`: redundant thematic explanation, repeated emotional interpretation, decorative mirroring, over-explained closure, and information timing. It finds what no phrase list can, and it carries its own limits on what may be edited.

The narrative layer applies when the profile is `creative` **and** the material is narrative prose fiction: a short story, a chapter, a scene. Decide that from the task and the text. Poetry, lyrics, speeches, sermons, and scripts stay in `creative` without it. Memoir, narrative nonfiction, and screenplays are outside it too; the research behind the checks covers none of them, and a user who wants the review there can ask for it by name.

Respect the user's statement that a text is fiction. The checker infers `creative` only from sustained quoted dialogue, so a story told without it falls back to `general-prose` under `auto`. Pass `--profile creative` to the checker and the same profile to the validator.

The layer never travels the other way. A README, a research summary, or an incident report keeps its linear order, its explicit conclusion, and its direct statement of what matters.

## Genre norms in prose

| Genre | Normal here | Still worth flagging |
|-------|-------------|----------------------|
| Technical docs, READMEs, API references | Headings every few paragraphs; bullets; bold on flag names; short uniform sentences; "Note that…"; triads in feature lists; "Additionally" in changelogs | Promotional adjectives, inflated significance, vague authority, chatbot residue, an opening that never says what the tool is |
| Academic and scientific writing | Hedges ("suggests", "may"); "Furthermore/Moreover"; passive voice; "plays a role"; participle tails summarizing the paper's own result | "cannot be overstated", "testament to", fabricated citations, "experts agree" without a citation |
| Marketing, landing pages, product copy | Rule of three; short punchy contrasts; bold; promotional register; hooks in headlines | Stacked superlatives with no concrete claim; "not just X, but Y" more than once; invented metrics or customers |
| Journalism, essays, blog posts | Varied rhythm; a single rhetorical question; one deliberate contrast; em dashes the author uses consistently | Generic intros and outros, "experts say" without naming, aphorism closers, "Here's the thing" openers |
| Speeches, sermons, manifestos, slogans | Anaphora; triads; echo structures; "not X but Y"; short repeated sentences | Almost nothing structural. Fingerprints and stock-vocabulary clusters only. Say so in the report. |
| Prose fiction | Everything structural; fragments; any punctuation; a linear plot; an explicit theme; a direct emotion label; a lush passage | Fingerprints, plus the narrative review in `narrative-review.md`. Do not touch voice. Recommend `detect` mode when the user has not asked for edits. |
| Poetry, lyrics | Everything structural; fragments; any punctuation; repetition of every kind | Fingerprints only. Do not touch voice. Recommend `detect` mode. |
| Legal, policy, compliance | Formal connectives; repetition for precision; "in connection with"; defined-term restatement | Placeholders; marketing register |
| Chat, Slack, email | "Let me know if…", "Hope this helps", "Great question" are ordinary courtesy | Stock vocabulary clusters, false contrasts, canned significance |
| Wiki and encyclopedic prose | Neutral register; simple copulas; explicit citations | The whole catalog applies; promotional register and vague attribution are the most common problems |
| Non-native English writing | Formal connectives ("Moreover"), textbook phrases, safe vocabulary | Treat stock vocabulary and transitions with extra caution; never raise density on these alone, and never comment on the author's proficiency |

## Legitimate uses of otherwise-flagged patterns

- **False contrast** is fine when the reader plausibly holds the rejected belief and the text names it: "The bottleneck isn't the database, as the earlier profile suggested; it's serialization."
- **Rule of three** is fine when there are exactly three real items ("the CLI, the SDK, and the web console"), and when three is what the API requires.
- **Anaphora and echo** are fine when the author is clearly building rhythm in a persuasive passage.
- **"Delve", "landscape", "robust"** are fine in their literal or field-specific senses — archaeology, geography, robust standard errors.
- **Em dashes** are fine when the author uses them consistently at a sane rate throughout, including in unflagged paragraphs. Compare against the author, not an absolute.
- **Bold lead-ins on bullets** are fine in reference lists, glossaries, parameter tables, release notes, and definition lists.
- **"Note that"** is fine before a genuine caveat in documentation.
- **Discontinuous sentences** are fine in installation steps, status notes, and fact lists.
- **First-person "I think" / "we found"** is not a cliché; it is attribution. Keep it.
- **Hedges** ("may", "appears to", "in our tests") carry the author's uncertainty. Never strengthen or remove them to sound confident.
- **A shared template across files** can be deliberate house style. Report the repetition; draw no inference from it.

## Voice and register from the user

If the user names a register or supplies a style sample, read `references/voices.md`. The default is `preserve`, and a voice request applies only to spans you are already rewriting.

## Scope in files

- **Under ~300 lines, or a clearly named section:** proceed.
- **Larger, with no section named, in `rewrite` or `edit` mode:** report findings for the whole file, then ask which sections to rewrite. Do not rewrite everything on the assumption that the user wants it.
- **`detect` mode:** scan the whole file regardless of length.
- **Coverage:** say what you read. A whole-story diagnosis of closure, subplot structure, or chronology requires reading the whole supplied story, even when the edit covers one scene. When length or scope prevents that, call the diagnosis partial and name the parts it covers. An excerpt cannot show that a subplot is missing or that an unseen ending fails. A complete audit is still not authorization for a complete rewrite.
- **Multiple files:** handle each separately. Never carry a voice from one file into another. For repeated templates across files, run `$SKILL_DIR/scripts/llm_ism_project_check.py` and report the repetition as repetition.

## Things that are not signals

Correct grammar, formal tone, well-organized structure, technical vocabulary, consistent citations, absence of typos, use of Markdown, Title Case headings, neutral register, and em dashes as such. None of these indicate anything about how the text was produced, and flagging them wastes the reader's attention.
