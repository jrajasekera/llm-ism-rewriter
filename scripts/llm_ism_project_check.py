#!/usr/bin/env python3
"""Find repeated prose templates across a set of documents.

Standard library only. Within one file a shared skeleton is invisible; across a
directory of READMEs or posts it is the most visible pattern there is. This
script reports repetition — repeated openers, phrases, heading frames, section
sequences, and labeled-bullet skeletons. Repetition is not authorship evidence.
A shared template is often deliberate house style; the report says what recurs
and leaves the judgment to a reader.

Exit codes: 0 ran successfully, 1 --fail-on-repetition and repetition found,
2 bad arguments or unreadable input, 3 internal failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_ism_core import (  # noqa: E402
    LABELED_BULLET_RE, PROSE_KINDS, TOOL_VERSION, SCHEMA_VERSION, mask_inline, normalize,
    parse_markdown, split_sentences, words,
)

SCAFFOLDING = frozenset(normalize(p) for p in (
    "table of contents", "getting started", "see also", "license", "contributing",
    "installation", "usage", "api reference", "changelog", "code of conduct",
    "all rights reserved", "licensed under the apache license", "mit license",
    "back to top", "read the docs", "pull requests are welcome",
))
STOPWORDS = frozenset("""
a an the and or but if then than that this these those of in on at to for from by with
is are was were be been being as it its they them their we our you your i not no do does
did can could may might must shall should will would have has had there here so such
""".split())


def collect(paths: list[str], extensions: tuple[str, ...], ignore: list[str]) -> list[str]:
    out: list[str] = []
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs
                           if not d.startswith(".") and d not in ("node_modules", "__pycache__")]
                for name in sorted(files):
                    if name.lower().endswith(extensions):
                        out.append(os.path.join(root, name))
        else:
            out.append(path)
    return [p for p in out if not any(pat in p for pat in ignore)]


def document_features(text: str) -> dict:
    segments = parse_markdown(text)
    prose = [mask_inline(s.text) for s in segments if s.kind in PROSE_KINDS and not s.protected]
    sentences = [s.strip() for block in prose for _, s in split_sentences(block) if words(s)]
    headings = [(s.heading_level or 0, " ".join(s.text.strip().lstrip("#").split()))
                for s in segments if s.kind == "heading"]
    bullets = [s.text for s in segments if s.kind == "list_item"]
    return {
        "sentences": sentences,
        "opening": normalize(sentences[0]) if sentences else "",
        "closing": normalize(sentences[-1]) if sentences else "",
        "heading_sequence": tuple(normalize(h) for lvl, h in headings if lvl <= 2),
        "heading_first_words": [normalize(h).split(" ")[0] for lvl, h in headings if h],
        "labeled_bullets": sum(1 for b in bullets if LABELED_BULLET_RE.match(b)),
        "bullets": len(bullets),
        "words": sum(len(words(p)) for p in prose),
    }


def ngrams(sentences: list[str], n: int):
    for sentence in sentences:
        toks = [w.casefold() for w in words(sentence)]
        for i in range(len(toks) - n + 1):
            gram = toks[i:i + n]
            if all(t in STOPWORDS for t in gram):
                continue
            phrase = " ".join(gram)
            if phrase in SCAFFOLDING:
                continue
            yield phrase


def analyze(files: dict[str, dict], n: int, min_files: int) -> dict:
    phrase_files: dict[str, set[str]] = defaultdict(set)
    for path, feat in files.items():
        for gram in set(ngrams(feat["sentences"], n)):
            phrase_files[gram].add(path)
    repeated_phrases = sorted(
        ({"phrase": p, "files": sorted(fs), "file_count": len(fs)}
         for p, fs in phrase_files.items() if len(fs) >= min_files),
        key=lambda d: (-d["file_count"], d["phrase"]))

    openings: dict[str, list[str]] = defaultdict(list)
    closings: dict[str, list[str]] = defaultdict(list)
    sequences: dict[tuple, list[str]] = defaultdict(list)
    frames: Counter = Counter()
    frame_files: dict[str, set[str]] = defaultdict(set)
    for path, feat in files.items():
        if feat["opening"]:
            openings[feat["opening"]].append(path)
        if feat["closing"]:
            closings[feat["closing"]].append(path)
        if feat["heading_sequence"]:
            sequences[feat["heading_sequence"]].append(path)
        for word in set(feat["heading_first_words"]):
            frame_files[word].add(path)
            frames[word] += 1

    def repeated(mapping):
        return sorted(({"value": k if isinstance(k, str) else list(k),
                        "files": sorted(v), "file_count": len(v)}
                       for k, v in mapping.items() if len(v) >= min_files),
                      key=lambda d: -d["file_count"])

    skeletons = [
        {"path": p, "labeled_bullets": f["labeled_bullets"], "bullets": f["bullets"],
         "ratio": round(f["labeled_bullets"] / f["bullets"], 3)}
        for p, f in files.items() if f["bullets"] >= 4 and f["labeled_bullets"] / f["bullets"] > 0.5]

    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "rule_id": "ST.CROSS_FILE_TEMPLATE",
        "files_scanned": len(files),
        "ngram_size": n,
        "minimum_files": min_files,
        "repeated_phrases": repeated_phrases[:50],
        "repeated_openings": repeated(openings),
        "repeated_closings": repeated(closings),
        "repeated_heading_sequences": repeated(sequences),
        "repeated_heading_frames": [
            {"first_word": w, "files": sorted(fs), "file_count": len(fs)}
            for w, fs in sorted(frame_files.items(), key=lambda kv: -len(kv[1]))
            if len(fs) >= min_files],
        "labeled_bullet_skeletons": sorted(skeletons, key=lambda d: -d["ratio"]),
        "disclaimer": "Repetition, not authorship. A shared template may be deliberate house style.",
    }


def render(report: dict) -> str:
    out = [f"== {report['files_scanned']} files, {report['ngram_size']}-word phrases "
           f"repeated in {report['minimum_files']}+ files"]

    def section(title, rows, fmt):
        if not rows:
            return
        out.append(f"   {title}:")
        for row in rows[:12]:
            out.append("     " + fmt(row))
        if len(rows) > 12:
            out.append(f"     … and {len(rows) - 12} more")

    section("repeated phrases", report["repeated_phrases"],
            lambda r: f"{r['phrase']!r} in {r['file_count']} files")
    section("repeated openings", report["repeated_openings"],
            lambda r: f"{r['value'][:70]!r} in {r['file_count']} files")
    section("repeated closings", report["repeated_closings"],
            lambda r: f"{r['value'][:70]!r} in {r['file_count']} files")
    section("repeated heading sequences", report["repeated_heading_sequences"],
            lambda r: f"{' > '.join(r['value'][:5])} in {r['file_count']} files")
    section("repeated heading frames", report["repeated_heading_frames"],
            lambda r: f"headings starting {r['first_word']!r} in {r['file_count']} files")
    section("labeled-bullet skeletons", report["labeled_bullet_skeletons"],
            lambda r: f"{r['path']}: {r['labeled_bullets']}/{r['bullets']} bullets labeled")
    if len(out) == 1:
        out.append("   no cross-file repetition above the threshold")
    out.append("   " + report["disclaimer"])
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="llm_ism_project_check.py",
        description="Report prose templates repeated across several documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  llm_ism_project_check.py docs/\n"
               "  llm_ism_project_check.py --min-files 4 --json posts/*.md\n")
    ap.add_argument("paths", nargs="+", help="files or directories to scan")
    ap.add_argument("--ngram", type=int, default=5, metavar="N",
                    help="phrase length in words, 4-10 (default: 5)")
    ap.add_argument("--min-files", type=int, default=3, metavar="N",
                    help="report a pattern present in at least N files (default: 3)")
    ap.add_argument("--ext", default=".md,.markdown,.txt",
                    help="comma-separated file extensions to walk (default: .md,.markdown,.txt)")
    ap.add_argument("--ignore", action="append", default=[], metavar="SUBSTRING",
                    help="skip paths containing this substring (repeatable)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--fail-on-repetition", action="store_true",
                    help="exit 1 when any repetition is reported")
    ap.add_argument("--version", action="version", version=f"llm_ism_project_check {TOOL_VERSION}")
    args = ap.parse_args(argv)

    if not 4 <= args.ngram <= 10:
        print("error: --ngram must be between 4 and 10", file=sys.stderr)
        return 2
    if args.min_files < 2:
        print("error: --min-files must be at least 2", file=sys.stderr)
        return 2

    extensions = tuple(e if e.startswith(".") else "." + e for e in args.ext.split(","))
    paths = collect(args.paths, extensions, args.ignore)
    if not paths:
        print("error: no files matched", file=sys.stderr)
        return 2

    files = {}
    for path in paths:
        try:
            files[path] = document_features(open(path, encoding="utf-8").read())
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2

    report = analyze(files, args.ngram, args.min_files)
    print(json.dumps(report, indent=2) if args.json else render(report))

    if args.fail_on_repetition and any(report[k] for k in (
            "repeated_phrases", "repeated_openings", "repeated_closings",
            "repeated_heading_sequences")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
