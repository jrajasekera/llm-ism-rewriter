# Nonfiction review

Use this for a nonfiction draft with several paragraphs, or when a short passage
depends on context the reader may not have. It supplements the existing catalog;
it adds no detector, threshold, or permission to restructure. For fiction, use
`narrative-review.md` instead. A reference page can serve several lookup tasks
without making a single argument.

## Establish the purpose

Read the supplied piece, or the relevant section and its dependencies, before
editing individual sentences. Privately state what the reader should learn or
be able to do. For reference material, name the lookup task. Trace that purpose
to the text; do not supply a thesis the author did not write.

If the point is unclear, identify the competing claims or missing connection
with source spans. Report a `[Gap]` for missing information, or a `[Decision]`
when the author must choose the purpose or arrangement. Continue independent
local fixes where possible. Do not turn uncertainty about the point into a
license to delete sections. The patch/rebuild conditions and edit scope in
`SKILL.md` still apply.

On a repetitive draft, note each paragraph's contribution. A definition,
example, qualification, and application can discuss the same subject while
doing different work. Flag duplication under `RH.LOW_INFORMATION_RESTATEMENT`
only when the passages add no distinct content or reader function.

## Read the places a scan can miss

Inspect the title and headings against the sections they introduce. Read the
opening and each paragraph's final sentence, then isolated short paragraphs.
Keep their surrounding context visible: a closer can carry a limitation that
looks expendable on its own. Include supplied captions and subtitles; report
coverage limits for material you cannot inspect.

Use existing catalog rules to explain a finding. A reveal can postpone the
subject without using a stock phrase; a final sentence can merely announce
significance. Ask what information the sentence contributes before cutting it.
Keep a short factual conclusion, a useful recap, and an intentional rhetorical
turn. A checker report with no findings does not replace this reading.

For headings, test whether a reader can locate the needed information. If a
slogan becomes an abstract label that is just as unhelpful, the edit has failed.
A conventional topic label can work well in reference material. Heading edits
remain subject to the structural invariants; report a suggestion when the
current mode does not permit the change.

## Read documentation as a new reader

For a README, guide, or explanation of current behavior, read the final text
without relying on the earlier draft, implementation history, or the editing
conversation. Check whether the reader can identify the actor and the action,
resolve references such as `here` and `the other option`, and follow the steps
from information the document actually supplies.

Compare related sections for conflicting descriptions. Report both spans as a
`[Decision]` and leave the disputed facts unchanged unless the user supplies
authoritative evidence or separately requests verification. A prose edit does
not establish which statement is true. Do not invent an instruction to bridge
a missing step.

Keep change history when it serves the requested genre: release notes, migration
guides, incident timelines, and PR descriptions need before/after context.
Neither `now` nor `previously` is a finding by itself.

A separate reader can help when the stakes justify it and delegation is
authorized. Give that reader the current text and intended audience, without
the change history or a proposed diagnosis. If you review your own rewrite,
describe it as a self-review; do not claim independent validation.

## Check the revision for new problems

Read revised sentences for effort as well as length. Restore a preposition or
`that` when it makes a relationship clear. Move a long intervening list after
the main clause when that is within scope. Expand a newly invented noun stack
or verb if the reader has to reconstruct its meaning. Keep established terms
and familiar short clauses. Broader clarity editing still requires the user's
request; repairing a readability problem introduced by this rewrite does not.

Check confidence words and compressed claims of verification against the
evidence already in the source. Preserve a technical term such as
`byte-identical` when it describes the actual check. Do not replace a flourish
with an unsupported universal claim, remove a real qualification, or invent a
method that would make the claim true. Missing evidence is a reported gap.

Finally, compare each edited claim with its source under
`rewrite-invariants.md`. Check what the qualifiers modify, as well as whether
the words survived. Report the passages reviewed and any unresolved decisions;
do not print the working map unless it explains a finding.
