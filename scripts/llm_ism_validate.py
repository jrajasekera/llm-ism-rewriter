#!/usr/bin/env python3
"""Compare an original document with its rewrite and report preservation failures.

Standard library only. A rewrite that removes every cliché but changes a claim
is a failed rewrite; this script makes that principle executable. It checks that
protected spans are byte-identical, that technical and semantic anchors survive,
and that the rewrite did not add findings.

The validator does not claim semantic equivalence. It reports likely drift for a
person or agent to review.

Exit codes: 0 passed (warnings may exist), 1 preservation failure,
2 bad arguments or unreadable input, 3 internal or registry failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_ism_core import (  # noqa: E402
    PROSE_KINDS, TOOL_VERSION, SCHEMA_VERSION, RegistryError, load_registry,
    normalize, parse_markdown, split_sentences, words,
)
import llm_ism_check  # noqa: E402

MODES = ("detect", "rewrite", "edit", "restructure")

# Policy per mode: which checks are errors, which drop to warnings.
POLICY = {
    "detect":      {"headings": "error", "order": "error", "text": "error"},
    "edit":        {"headings": "error", "order": "warn", "text": "skip"},
    "rewrite":     {"headings": "warn", "order": "warn", "text": "skip"},
    "restructure": {"headings": "info", "order": "info", "text": "skip"},
}

CONTRACTIONS = [
    (re.compile(r"\bcan't\b", re.I), "can not"), (re.compile(r"\bwon't\b", re.I), "will not"),
    (re.compile(r"\bshan't\b", re.I), "shall not"), (re.compile(r"\bcannot\b", re.I), "can not"),
    (re.compile(r"n't\b", re.I), " not"),
]

NUM_UNIT_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s?(?:%|ms|µs|us|ns|s|sec|secs|min|mins|hr|hrs|h|d|"
    r"[KMGT]i?B|kb|mb|gb|tb|km|cm|mm|kg|g|lb|px|rpm|fps|Hz|kHz|MHz|GHz|x)(?![A-Za-z0-9])")
VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-+]\w+(?:\.\w+)*)?\+?")
NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
FLAG_RE = re.compile(r"(?<![\w-])--?[A-Za-z][\w-]{1,30}\b")
ENVVAR_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)+\b")
IDENT_RE = re.compile(r"\b(?:[a-z]+(?:[A-Z][a-z0-9]+)+|[a-z]+(?:_[a-z0-9]+)+)\b")
INLINE_CODE_RE = re.compile(r"`+[^`\n]+`+")
URL_RE = re.compile(r"https?://[^\s)\"'<>]+|www\.[^\s)\"'<>]+")
PATH_RE = re.compile(r"(?<![\w~.])(?:~|\.{1,2})?/[\w.@~-]+(?:/[\w.@~-]+)+/?")
FOOTNOTE_RE = re.compile(r"\[\^[\w-]+\]")
CITEKEY_RE = re.compile(r"\[@[\w:.-]+\]|\([A-Z][A-Za-z-]+(?: et al\.)?,? \d{4}[a-z]?\)")
REFDEF_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s*(\S+)", re.M)
PROPER_RE = re.compile(r"\b[A-Z][a-z]{2,}(?:[A-Z][a-z]+)*\b")

NEGATION = frozenset("not never no without except unless neither nor none".split())
MODALITY = frozenset("may might can could must should will would shall ought".split())
QUANTIFIER = frozenset("all every some most many few several any each both only".split())
COMPARATIVE = frozenset(
    "more less fewer better worse faster slower higher lower greater smaller "
    "larger longer shorter cheaper safer".split())
FIRST_PERSON = frozenset("i we me us my our mine ours".split())
SECOND_PERSON = frozenset("you your yours".split())


@dataclass
class Result:
    level: str          # pass | warn | fail | info
    check: str
    message: str


# --- Extraction --------------------------------------------------------------

def expand(text: str) -> str:
    for pattern, repl in CONTRACTIONS:
        text = pattern.sub(repl, text)
    return text


def protected_spans(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"code": [], "frontmatter": [], "quote": [], "table": [], "html": []}
    for seg in parse_markdown(text):
        if seg.kind in out:
            body = seg.text if seg.kind != "table" else normalize(seg.text)
            out[seg.kind].append(body)
    return out


def prose_of(text: str) -> str:
    return "\n\n".join(s.text for s in parse_markdown(text) if s.kind in PROSE_KINDS)


def headings_of(text: str) -> list[tuple[int, str]]:
    return [(s.heading_level or 0, " ".join(s.text.strip().lstrip("#").split()))
            for s in parse_markdown(text) if s.kind == "heading"]


def proper_nouns(text: str) -> Counter:
    """Capitalized words that are not merely sentence-initial.

    A crude approximation, deliberately. It exists to notice a name that
    disappeared or a name that appeared from nowhere, not to parse English.
    """
    found: Counter = Counter()
    for _, sentence in split_sentences(text):
        tokens = list(PROPER_RE.finditer(sentence))
        if not tokens:
            continue
        first = sentence.lstrip()[:1]
        for m in tokens:
            initial = m.start() == len(sentence) - len(sentence.lstrip()) and first.isupper()
            if initial:
                continue
            found[m.group(0)] += 1
    return found


def token_counts(text: str, vocabulary: frozenset[str]) -> Counter:
    return Counter(w.casefold() for w in words(expand(text)) if w.casefold() in vocabulary)


def anchors(text: str) -> dict[str, Counter]:
    prose = prose_of(text)
    return {
        "inline code": Counter(INLINE_CODE_RE.findall(text)),
        "URL": Counter(URL_RE.findall(text)),
        "path": Counter(PATH_RE.findall(text)),
        "footnote": Counter(FOOTNOTE_RE.findall(text)),
        "citation": Counter(CITEKEY_RE.findall(text)),
        "reference target": Counter(REFDEF_RE.findall(text)),
        "number with unit": Counter(m.group(0).strip() for m in NUM_UNIT_RE.finditer(prose)),
        "version": Counter(VERSION_RE.findall(prose)),
        "command flag": Counter(FLAG_RE.findall(prose)),
        "environment variable": Counter(ENVVAR_RE.findall(prose)),
        "identifier": Counter(IDENT_RE.findall(prose)),
    }


# --- Checks ------------------------------------------------------------------

def missing(before: Counter, after: Counter) -> list[str]:
    return sorted(k for k in before if after[k] < before[k])


def added(before: Counter, after: Counter) -> list[str]:
    return sorted(k for k in after if before[k] < after[k])


def resolve_profile(before: str, registry, profile: str = "auto") -> tuple[str, str]:
    """Return (profile, source) for the pair, decided once from the original.

    A revision can lose the cue that identified its source's genre, such as the
    dialogue that marked a story. Detecting each side separately would then
    judge the two versions under different tolerances.
    """
    if profile != "auto":
        if profile not in registry.profile_names():
            raise RegistryError(f"unknown profile: {profile}")
        return profile, "explicit"
    name, cues = llm_ism_check.detect_profile(before, parse_markdown(before))
    return name, "auto" if cues else "default"


def validate(before: str, after: str, mode: str, registry, path_before: str,
             path_after: str, shrink_limit: float, profile: str = "auto") -> list[Result]:
    policy = POLICY[mode]
    results: list[Result] = []

    if policy["text"] == "error":
        if before != after:
            results.append(Result("fail", "detect mode", "detect mode must not change the text"))
        else:
            results.append(Result("pass", "detect mode", "text is byte-identical"))
        return results

    # 1. protected spans, exact
    pb, pa = protected_spans(before), protected_spans(after)
    for kind, label in (("code", "code blocks"), ("frontmatter", "frontmatter"),
                        ("quote", "attributed quotations"), ("table", "table cells"),
                        ("html", "raw HTML blocks")):
        if pb[kind] == pa[kind]:
            if pb[kind]:
                results.append(Result("pass", label, f"{len(pb[kind])} unchanged"))
        else:
            results.append(Result("fail", label,
                                  f"changed: {len(pb[kind])} before, {len(pa[kind])} after"))

    # 2. exact technical anchors
    ab, aa = anchors(before), anchors(after)
    exact = ("inline code", "URL", "path", "footnote", "citation", "reference target",
             "number with unit", "version", "command flag", "environment variable")
    total, kept = 0, 0
    for key in exact:
        total += sum(ab[key].values())
        kept += sum(min(v, aa[key][k]) for k, v in ab[key].items())
        gone = missing(ab[key], aa[key])
        if gone:
            results.append(Result("fail", f"{key}s",
                                  "missing from the rewrite: " + ", ".join(repr(g) for g in gone[:6])
                                  + (" …" if len(gone) > 6 else "")))
    if total and kept == total:
        results.append(Result("pass", "technical anchors", f"preserved ({kept}/{total})"))
    new_units = added(ab["number with unit"], aa["number with unit"])
    if new_units:
        results.append(Result("warn", "invented specificity",
                              "measurements not in the source: " + ", ".join(repr(g) for g in new_units[:6])))

    gone_ids = missing(ab["identifier"], aa["identifier"])
    if gone_ids:
        results.append(Result("warn", "identifiers",
                              "no longer present: " + ", ".join(repr(g) for g in gone_ids[:6])))

    # 3. semantic anchors
    for label, vocab, level in (("negation", NEGATION, "fail"),
                                ("modality", MODALITY, "warn"),
                                ("quantifier", QUANTIFIER, "warn"),
                                ("comparative", COMPARATIVE, "warn")):
        cb = token_counts(prose_of(before), vocab)
        ca = token_counts(prose_of(after), vocab)
        drift = [f"{k}={cb[k]}→{ca[k]}" for k in sorted(set(cb) | set(ca)) if cb[k] != ca[k]]
        if not drift:
            if cb:
                results.append(Result("pass", label, "unchanged"))
            continue
        lost = [k for k in cb if ca[k] < cb[k]]
        results.append(Result(level if lost else "warn", label,
                              "count changed: " + "; ".join(drift[:8])))

    # 4. proper nouns and person
    prose_b, prose_a = prose_of(before), prose_of(after)
    nb, na = proper_nouns(prose_b), proper_nouns(prose_a)
    gone_names = missing(nb, na)
    new_names = added(nb, na)
    if gone_names:
        results.append(Result("warn", "proper nouns", "removed: " + ", ".join(gone_names[:6])))
    if new_names:
        results.append(Result("warn", "proper nouns",
                              "introduced (invented specificity?): " + ", ".join(new_names[:6])))
    for label, vocab in (("first person", FIRST_PERSON), ("second person", SECOND_PERSON)):
        b = sum(token_counts(prose_b, vocab).values())
        a = sum(token_counts(prose_a, vocab).values())
        if b == 0 and a > 0:
            results.append(Result("fail", label, f"introduced where the source had none ({a} uses)"))
        elif b and abs(a - b) > max(2, 0.5 * b):
            results.append(Result("warn", label, f"use changed substantially: {b}→{a}"))

    # 5. structure
    hb, ha = headings_of(before), headings_of(after)
    if hb != ha:
        level = policy["headings"]
        detail = f"{len(hb)} before, {len(ha)} after"
        if [l for l, _ in hb] != [l for l, _ in ha]:
            detail += "; nesting changed"
        results.append(Result({"error": "fail", "warn": "warn", "info": "info"}[level],
                              "headings", detail))
    elif hb:
        results.append(Result("pass", "headings", f"{len(hb)} unchanged"))

    wb, wa = len(words(prose_b)), len(words(prose_a))
    if wb and wa / wb < shrink_limit:
        results.append(Result("warn", "length",
                              f"prose shrank {round(100 * (1 - wa / wb))}%; confirm no argument was removed"))

    para_b = [normalize(s.text) for s in parse_markdown(before) if s.kind in PROSE_KINDS]
    para_a = [normalize(s.text) for s in parse_markdown(after) if s.kind in PROSE_KINDS]
    unchanged = sum(1 for p in para_a if p in para_b)
    if para_a:
        results.append(Result("info", "untouched prose",
                              f"{unchanged}/{len(para_a)} paragraphs byte-identical to the source"))
    if sorted(para_b) == sorted(para_a) and para_b != para_a and policy["order"] != "info":
        results.append(Result({"error": "fail", "warn": "warn"}[policy["order"]],
                              "paragraph order", "paragraphs were reordered but not reworded"))

    # 6. residual findings, both versions under the one profile
    try:
        resolved, source = resolve_profile(before, registry, profile)
        rb = llm_ism_check.analyze(before, path_before, registry, resolved, False)
        ra = llm_ism_check.analyze(after, path_after, registry, resolved, False)
    except RegistryError as exc:
        results.append(Result("warn", "residual findings", f"not evaluated: {exc}"))
        return results
    results.append(Result("info", "context profile",
                          f"{resolved} ({source}); applied to both versions"))
    hi_b = sum(rb["summary"]["by_priority"][p] for p in ("P0", "P1"))
    hi_a = sum(ra["summary"]["by_priority"][p] for p in ("P0", "P1"))
    if hi_a > hi_b:
        results.append(Result("fail", "residual findings",
                              f"P0/P1 findings increased: {hi_b}→{hi_a}"))
    else:
        results.append(Result("pass", "residual findings", f"P0/P1 findings {hi_b}→{hi_a}"))
    new_rules = {rid for f in ra["findings"] for rid in f["rule_ids"]} - \
                {rid for f in rb["findings"] for rid in f["rule_ids"]}
    if new_rules:
        results.append(Result("warn", "new patterns",
                              "introduced by the rewrite: " + ", ".join(sorted(new_rules))))
    return results


def render(results: list[Result], mode: str) -> str:
    order = {"fail": 0, "warn": 1, "pass": 2, "info": 3}
    lines = [f"mode: {mode}"]
    for r in sorted(results, key=lambda r: order[r.level]):
        lines.append(f"{ {'fail': 'FAIL', 'warn': 'WARN', 'pass': 'PASS', 'info': 'INFO'}[r.level]:<4}: "
                     f"{r.check}: {r.message}")
    fails = sum(1 for r in results if r.level == "fail")
    warns = sum(1 for r in results if r.level == "warn")
    lines.append(f"verdict: {'FAILED' if fails else 'passed'} "
                 f"({fails} failure(s), {warns} warning(s) to review)")
    lines.append("Preservation checks only. This says nothing about who wrote either version.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="llm_ism_validate.py",
        description="Check that a rewrite preserved the original's protected spans, "
                    "technical anchors, and claim strength.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  llm_ism_validate.py before.md after.md\n"
               "  llm_ism_validate.py --mode edit before.md after.md\n"
               "  llm_ism_validate.py --profile creative story.md story-revised.md\n"
               "  llm_ism_validate.py --json before.md after.md\n")
    ap.add_argument("before", help="the original document")
    ap.add_argument("after", help="the rewritten document")
    ap.add_argument("--mode", default="rewrite", choices=MODES,
                    help="policy strictness (default: rewrite)")
    ap.add_argument("--profile", default="auto", metavar="NAME",
                    help="context profile for the residual-findings check, applied to both "
                         "versions; pass the one the checker ran under (default: auto, "
                         "resolved once from the original)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--shrink-limit", type=float, default=0.6, metavar="RATIO",
                    help="warn when the rewrite keeps less than this share of prose words (default: 0.6)")
    ap.add_argument("--rules", metavar="PATH", help="path to an alternate rules.json")
    ap.add_argument("--version", action="version", version=f"llm_ism_validate {TOOL_VERSION}")
    args = ap.parse_args(argv)

    try:
        registry = load_registry(args.rules)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    if args.profile != "auto" and args.profile not in registry.profile_names():
        ap.error(f"argument --profile: invalid choice: {args.profile!r} (choose from "
                 + ", ".join(["auto"] + registry.profile_names()) + ")")
    texts = []
    for path in (args.before, args.after):
        try:
            with open(path, encoding="utf-8") as fh:
                texts.append(fh.read())
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2

    try:
        profile, source = resolve_profile(texts[0], registry, args.profile)
        results = validate(texts[0], texts[1], args.mode, registry,
                           args.before, args.after, args.shrink_limit, args.profile)
    except Exception as exc:  # parser or analysis failure
        print(f"error: validation failed: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps({
            "schema_version": SCHEMA_VERSION, "tool_version": TOOL_VERSION,
            "mode": args.mode, "profile": profile, "profile_source": source,
            "before": args.before, "after": args.after,
            "results": [asdict(r) for r in results],
            "passed": not any(r.level == "fail" for r in results),
            "disclaimer": "Preservation checks only. Not evidence of authorship.",
        }, indent=2))
    else:
        print(render(results, args.mode))
    return 1 if any(r.level == "fail" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
