#!/usr/bin/env python3
"""Surface candidate LLM-isms in Markdown or plain text.

Standard library only. Reports lexical hits (stock phrases, chatbot residue,
leaked citation markup), and structural signals (triad density, em-dash rate,
sentence-length uniformity). It skips fenced code, inline code, frontmatter,
blockquotes, tables, and URLs.

Output is a list of *candidates*. Severity in context is a judgment call the
caller must make; see SKILL.md and references/patterns.md.

Usage:
    llm_ism_check.py [--json] FILE [FILE ...]
    llm_ism_check.py [--json] -          # read stdin
Exit codes: 0 ran successfully (findings or not), 2 bad input/arguments.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, asdict

# --- Catalog -----------------------------------------------------------------
# tier: fingerprint | cliche | structural
# Phrases are paraphrased category examples; keep them few and high-precision.

FINGERPRINTS = {
    "chatbot-residue": [
        r"\bas an ai\b", r"\bas of my (?:last|latest) (?:update|training)\b",
        r"\bknowledge cutoff\b", r"\bi hope this helps\b", r"\bhope this helps\b",
        r"\bgreat question\b", r"\blet me know if you(?:'d| would)? like\b",
        r"^\s*certainly[!,]", r"\bignore (?:the|all|any) (?:(?:previous|above|prior) )?instructions(?: (?:above|below))?\b",
        r"\bi (?:cannot|can't) browse\b",
    ],
    "citation-markup": [
        r"oaicite", r"contentReference", r"\bturn\d+(?:search|view|file)\d+\b",
        r"\[cite:\s*\d+\]", r"attached_file", r"ppl-ai-file-upload", r"【[^】]{0,40}】",
        r"\[(?:citation needed|insert [^\]]{1,40})\]", r"\{\{[^}]{1,40}\}\}",
    ],
}

CLICHES = {
    "stock-vocabulary": [
        r"\bdelv(?:e|es|ed|ing)\b", r"\btapestry\b", r"\btestament to\b",
        r"\bever-evolving\b", r"\b(?:the|this|today's) [\w-]+ landscape\b",
        r"\bmultifaceted\b", r"\binterplay\b", r"\bgame-?changer\b",
        r"\bseamless(?:ly)?\b", r"\bleverag(?:e|es|ed|ing)\b", r"\bunderscor(?:e|es|ed|ing)\b",
        r"\bpivotal\b", r"\bcrucial\b", r"\bvibrant\b", r"\bmeticulous(?:ly)?\b",
        r"\bfoster(?:s|ed|ing)?\b", r"\bunlock(?:s|ed|ing)? (?:insights|potential|value)\b",
        r"\bnavigat(?:e|es|ed|ing) the\b", r"\bin the realm of\b", r"\bembark(?:s|ed|ing)? on\b",
    ],
    "stock-transition": [
        r"^\s*(?:additionally|furthermore|moreover),", r"\bit(?:'s| is) (?:important|worth) (?:to note|noting)\b",
        r"\bin today's [\w-]+ world\b", r"\bat its core\b", r"\bin essence\b",
        r"^\s*(?:ultimately|overall|in conclusion|in summary),", r"\bthat being said\b",
    ],
    "inflated-significance": [
        r"\bpivotal moment\b", r"\bcannot be overstated\b", r"\bplays? a (?:vital|crucial|key|critical) role\b",
        r"\bindelible mark\b", r"\bdeeply rooted\b", r"\bmarks? a (?:significant|major) (?:shift|milestone)\b",
        r"\bshaping the future of\b", r"\breflect(?:s|ing) (?:a )?broader\b",
    ],
    "promotional": [
        r"\bboasts?\b", r"\bnestled\b", r"\bworld-class\b", r"\bcutting-edge\b", r"\bstate-of-the-art\b",
        r"\brich (?:heritage|history|tapestry)\b", r"\bdiverse array\b", r"\bunparalleled\b",
        r"\bcommitment to excellence\b", r"\b(?:serves|stands|functions) as an?\b",
    ],
    "vague-authority": [
        r"\bexperts (?:agree|argue|say|believe|suggest)\b", r"\bindustry reports?\b",
        r"\b(?:critics|observers|analysts) have (?:noted|pointed|argued)\b", r"\bmany (?:believe|argue)\b",
        r"\bit is widely (?:recognized|accepted|known)\b", r"\bstudies (?:show|suggest)\b",
    ],
    "participle-tail": [
        r",\s*(?:highlighting|underscoring|emphasizing|reflecting|showcasing|demonstrating|ensuring|fostering) (?:the|its|their|a|an)\b",
    ],
    "engagement-hook": [
        r"\bhere(?:'s| is) the (?:thing|twist|kicker|catch)\b", r"\bthe punchline is\b",
        r"\blet(?:'s| us) dive in\b", r"\bbuckle up\b", r"\bpicture this\b", r"\bsit with that\b",
        r"\blet that sink in\b", r"\byou already know\b", r"\bhave you ever wondered\b",
        r"\bthat's the part\b", r"\bis dead\.", r"^\s*honestly,", r"\byou're absolutely right\b",
    ],
    "false-contrast": [
        r"\bnot (?:just|only|merely|simply) [^.;:!?]{1,60}?,? but(?: also)?\b",
        r"\b(?:it|this|that)(?:(?:'s| is) ?not|(?:'s| is)n't|isn't) (?:about |a )?[^.;:!?]{1,50}?[.;:,—-]\s*(?:it|this|that)(?:'s| is) (?:about )?",
        r"\bisn(?:'t|ot) (?:just )?a [^.;:!?]{1,40}?[—-]\s*it(?:'s| is)\b",
    ],
}

TRIAD_RE = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? (?:and|or) [\w'-]+(?: [\w'-]+){0,2}\b")
EM_DASH_RE = re.compile(r"[—]|(?<=\w)--(?=\w)")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
WORD_RE = re.compile(r"[\w'-]+")


@dataclass
class Finding:
    file: str
    line: int
    tier: str
    category: str
    text: str
    note: str = ""


# --- Preprocessing -----------------------------------------------------------

def prose_lines(text: str):
    """Yield (line_no, line) for lines that are prose, skipping protected spans."""
    lines = text.splitlines()
    i = 0
    n = len(lines)
    if n and lines[0].strip() in ("---", "+++"):
        fence = lines[0].strip()
        j = 1
        while j < n and lines[j].strip() != fence:
            j += 1
        i = j + 1
    in_code = False
    for idx in range(i, n):
        raw = lines[idx]
        s = raw.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if s.startswith(">") or s.startswith("|") or (s.count("|") >= 2 and set(s) <= set("|-: ")):
            continue
        if s.startswith("#"):
            continue
        # scrub inline code, URLs, and paths
        cleaned = re.sub(r"`[^`]*`", " ", raw)
        cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)
        cleaned = re.sub(r"(?<!\w)(?:~|\.{1,2})?/[\w./-]+", " ", cleaned)
        if cleaned.strip():
            yield idx + 1, cleaned


# --- Analysis ----------------------------------------------------------------

def scan(text: str, fname: str) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    kept = list(prose_lines(text))
    for lineno, line in kept:
        low = line.lower()
        for cat, pats in FINGERPRINTS.items():
            for p in pats:
                for m in re.finditer(p, low, flags=re.I | re.M):
                    findings.append(Finding(fname, lineno, "fingerprint", cat, line[m.start():m.end()].strip()))
        for cat, pats in CLICHES.items():
            for p in pats:
                for m in re.finditer(p, low, flags=re.I | re.M):
                    findings.append(Finding(fname, lineno, "cliche", cat, line[m.start():m.end()].strip()))

    prose = " ".join(l for _, l in kept)
    words = WORD_RE.findall(prose)
    wc = len(words)
    sentences = [s for s in SENT_SPLIT_RE.split(prose) if WORD_RE.search(s)]
    lengths = [len(WORD_RE.findall(s)) for s in sentences]
    triads = len(TRIAD_RE.findall(prose))
    dashes = len(EM_DASH_RE.findall(prose))
    stats = {
        "words": wc,
        "sentences": len(sentences),
        "triads": triads,
        "em_dashes": dashes,
        "em_dashes_per_100_words": round(100 * dashes / wc, 2) if wc else 0,
        "mean_sentence_len": round(statistics.fmean(lengths), 1) if lengths else 0,
        "sentence_len_stdev": round(statistics.pstdev(lengths), 1) if len(lengths) > 1 else 0,
    }
    if wc >= 80:
        if dashes / wc > 1 / 120:
            findings.append(Finding(fname, 0, "structural", "em-dash-density",
                                    f"{dashes} em dashes in {wc} words", "more than ~1 per 120 words"))
        if triads / max(len(sentences), 1) > 0.25:
            findings.append(Finding(fname, 0, "structural", "triad-density",
                                    f"{triads} 'X, Y, and Z' lists in {len(sentences)} sentences", "rule-of-three run"))
        if len(lengths) >= 8 and stats["sentence_len_stdev"] < 4:
            findings.append(Finding(fname, 0, "structural", "uniform-rhythm",
                                    f"stdev {stats['sentence_len_stdev']} over {len(lengths)} sentences",
                                    "sentence lengths nearly identical"))
    return findings, stats


def render(findings: list[Finding], stats: dict, fname: str) -> str:
    out = [f"== {fname}: {stats['words']} words, {stats['sentences']} sentences, "
           f"{stats['em_dashes']} em dashes, {stats['triads']} triads, "
           f"sentence len {stats['mean_sentence_len']}±{stats['sentence_len_stdev']}"]
    if not findings:
        out.append("  no candidates")
    for f in sorted(findings, key=lambda f: (f.tier != "fingerprint", f.line)):
        loc = f"L{f.line}" if f.line else "doc"
        note = f"  ({f.note})" if f.note else ""
        out.append(f"  [{f.tier}] {loc} {f.category}: {f.text!r}{note}")
    out.append("  Candidates only. Judge density, genre, and context before acting.")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="files to scan, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    results = []
    for path in args.files:
        try:
            if path == "-":
                text = sys.stdin.read()
            else:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read {path}: {e}", file=sys.stderr)
            return 2
        findings, stats = scan(text, path)
        results.append((path, findings, stats))

    if args.json:
        json.dump([{"file": p, "stats": s, "findings": [asdict(f) for f in fs]} for p, fs, s in results],
                  sys.stdout, indent=2)
        print()
    else:
        print("\n\n".join(render(fs, s, p) for p, fs, s in results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
