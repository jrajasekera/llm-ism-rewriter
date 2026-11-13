#!/usr/bin/env python3
"""Measure the checker against the provenance corpus in corpus/manifest.json.

Standard library only. For every manifest document this script fetches the
source bytes into a gitignored cache if they are missing, verifies their
SHA-256, extracts the measured text with the document's recorded recipe,
verifies the SHA-256 of that text, and runs the checker's own `analyze` under
the document's register as the context profile. It then reports, per register
and per rule, how often the checker fires on this prose.

The corpus documents are human-written prose from before November 2022, so a
finding here is a candidate false positive: a place where the checker flags
prose that predates the habits it is looking for. The figures are rates of
writing-quality signals on a named sample. They say nothing about who wrote
any text, and nothing here produces a per-document score of any kind.

Exit codes: 0 measured, 1 a checksum did not match the manifest, 2 bad
arguments, missing cache in --offline mode, or a failed fetch, 3 registry or
manifest failure.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_ism_core import RegistryError, load_registry, parse_markdown, words  # noqa: E402
import llm_ism_check  # noqa: E402
import llm_ism_project_check  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
DEFAULT_MANIFEST = os.path.join(ROOT, "corpus", "manifest.json")
DEFAULT_CACHE = os.path.join(ROOT, "corpus", "cache")
USER_AGENT = ("llm-ism-rewriter-corpus/1.0 "
              "(+https://github.com/jrajasekera/llm-ism-rewriter; false-positive research)")
FORMATS = ("markdown", "text", "html", "wikitext")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
EXCERPT_CHARS = 60
QUANTILES = (("min", 0.0), ("p10", 0.10), ("p25", 0.25), ("median", 0.5),
             ("p75", 0.75), ("p90", 0.90), ("max", 1.0))
# What one observation of each metric is, as llm_ism_check.metric_observations
# reports it. The paragraph metrics only report paragraphs that have a run.
OBSERVATION_UNITS = {
    "anaphora_run_length": "paragraph whose longest same-opener run is at least 2",
    "consecutive_short_sentences": "paragraph containing at least one sentence of 5 words or fewer",
    "labeled_bullet_ratio": "section with at least min_bullets list items",
    "mirrored_sentence_pairs": "document with at least one mirrored sentence pair",
}
# Fields a measurement may copy from a manifest entry into its output. Anything
# else in the entry stays research metadata and is never read here.
OUTPUT_FIELDS = ("id", "register", "source_type", "written")


class IntegrityError(Exception):
    """Bytes on disk do not match the checksum recorded in the manifest."""


class FetchError(Exception):
    """A document is missing from the cache and could not be fetched."""


# --- Manifest and cache ------------------------------------------------------

def load_manifest(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(manifest.get("documents"), list):
        raise RegistryError(f"manifest {path} has no documents list")
    return manifest


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_file(cache_dir: str, doc_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", doc_id):
        raise RegistryError(f"document id {doc_id!r} is not a safe file name")
    return os.path.join(cache_dir, doc_id + ".raw")


_last_request: dict[str, float] = {}


def fetch(url: str, timeout: float = 60.0, pause: float = 1.0) -> bytes:
    """GET one URL politely: a descriptive User-Agent and a pause per host."""
    host = urllib.parse.urlsplit(url).netloc
    wait = _last_request.get(host, 0.0) + pause - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
    except (urllib.error.URLError, OSError) as exc:
        raise FetchError(f"cannot fetch {url}: {exc}") from exc
    finally:
        _last_request[host] = time.monotonic()
    return data


def load_source(doc: dict, cache_dir: str, offline: bool, fetcher=fetch) -> bytes:
    """Return the cached source bytes, fetching them first if allowed."""
    path = cache_file(cache_dir, doc["id"])
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return fh.read()
    if offline:
        raise FetchError(f"{doc['id']}: not in the cache ({path}) and --offline is set")
    data = fetcher(doc["source_url"])
    os.makedirs(cache_dir, exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)
    return data


def verify(doc: dict, label: str, field: str, data: bytes, record: bool) -> str:
    """Compare a checksum with the manifest. Raise on mismatch; fill a gap only
    when recording."""
    actual = sha256_hex(data)
    expected = doc.get(field)
    if expected is None and record:
        doc[field] = actual
        return actual
    if expected != actual:
        raise IntegrityError(f"{doc['id']}: {label} SHA-256 mismatch: manifest has "
                             f"{expected}, bytes on disk hash to {actual}")
    return actual


# --- Extraction --------------------------------------------------------------

def extract(raw: bytes, spec: dict) -> str:
    """Turn source bytes into the exact text that is measured.

    Deterministic: decode, convert the source format to Markdown-like text,
    drop lines matching the recorded patterns, cut between the recorded
    markers, then trim to a paragraph boundary at `max_words`.
    """
    if raw[:2] == b"\x1f\x8b":
        # Some archive snapshots hold the body exactly as the origin sent it,
        # gzip-encoded. The checksum covers those bytes; the text is inside.
        raw = gzip.decompress(raw)
    text = raw.decode(spec.get("encoding", "utf-8"), errors="strict")
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    fmt = spec.get("format", "markdown")
    if fmt not in FORMATS:
        raise RegistryError(f"unknown extract format {fmt!r}")
    # Markers apply to the source for the markup formats, where the body is
    # easiest to locate by an element or heading that conversion removes.
    text = cut(text, spec.get("source_start_after"), spec.get("source_end_before"))
    if fmt == "html":
        text = html_to_text(text, pre_as_code=spec.get("pre", "code") == "code")
    elif fmt == "wikitext":
        text = wikitext_to_markdown(text)
    if spec.get("drop_lines"):
        pats = [re.compile(p) for p in spec["drop_lines"]]
        text = "\n".join(line for line in text.split("\n")
                         if not any(p.search(line) for p in pats))
    if spec.get("quote_indented"):
        # Plain-text editions set quotations and verse off by indentation. Mark
        # them as block quotes so the checker protects them as it would in
        # Markdown, rather than counting another writer's words as prose.
        depth = int(spec["quote_indented"])
        text = "\n".join("> " + line.strip()
                         if line.strip() and len(line) - len(line.lstrip(" ")) >= depth else line
                         for line in text.split("\n"))
    if spec.get("dedent"):
        text = "\n".join(line.strip() for line in text.split("\n"))
    text = cut(text, spec.get("start_after"), spec.get("end_before"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip("\n") + "\n"
    if spec.get("max_words"):
        text = trim_words(text, int(spec["max_words"]))
    return text


def cut(text: str, start_after: str | None, end_before: str | None) -> str:
    if start_after:
        i = text.find(start_after)
        if i < 0:
            raise RegistryError(f"start marker not found: {start_after!r}")
        text = text[i + len(start_after):]
    if end_before:
        j = text.find(end_before)
        if j < 0:
            raise RegistryError(f"end marker not found: {end_before!r}")
        text = text[:j]
    return text


def trim_words(text: str, max_words: int) -> str:
    """Keep whole blank-line-separated blocks while the running word count stays
    within max_words. Never cut inside a fenced code block; always keep the
    first block."""
    blocks = text.split("\n\n")
    kept: list[str] = []
    total = 0
    in_fence = False
    for block in blocks:
        n = len(words(block))
        if kept and not in_fence and total + n > max_words:
            break
        kept.append(block)
        total += n
        for line in block.split("\n"):
            if re.match(r"^\s{0,3}(`{3,}|~{3,})", line):
                in_fence = not in_fence
    return "\n\n".join(kept).rstrip("\n") + "\n"


_DROP_BLOCKS = re.compile(r"<(script|style|head|noscript|svg|nav|footer|form)\b.*?</\1\s*>",
                          re.S | re.I)
_TAG = re.compile(r"<[^>]+>")


def _strip_tags(fragment: str) -> str:
    return html.unescape(_TAG.sub("", fragment))


def html_to_text(src: str, pre_as_code: bool = True) -> str:
    """A small, fixed HTML-to-Markdown conversion. Not a browser: it keeps
    headings, paragraphs, list items, block quotes and preformatted text, and
    discards everything else."""
    held: list[str] = []

    def hold(text: str) -> str:
        held.append(text)
        return f"\n\n\x00{len(held) - 1}\x00\n\n"

    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    src = _DROP_BLOCKS.sub("", src)

    def pre(m):
        body = _strip_tags(m.group(1)).strip("\n")
        return hold("```\n" + body + "\n```" if pre_as_code else body)

    src = re.sub(r"<pre\b[^>]*>(.*?)</pre\s*>", pre, src, flags=re.S | re.I)
    src = re.sub(r"<h([1-6])\b[^>]*>(.*?)</h\1\s*>",
                 lambda m: "\n\n" + "#" * int(m.group(1)) + " "
                 + " ".join(_strip_tags(m.group(2)).split()) + "\n\n",
                 src, flags=re.S | re.I)

    def quote(m):
        inner = html_to_text(m.group(1), pre_as_code).strip("\n")
        return hold("\n".join("> " + line if line else ">" for line in inner.split("\n")))

    while re.search(r"<blockquote\b", src, re.I):
        new = re.sub(r"<blockquote\b[^>]*>((?:(?!<blockquote\b).)*?)</blockquote\s*>", quote,
                     src, flags=re.S | re.I)
        if new == src:
            break
        src = new
    src = re.sub(r"<li\b[^>]*>", "\n\n- ", src, flags=re.I)
    src = re.sub(r"<br\s*/?>\s*<br\s*/?>", "\n\n", src, flags=re.I)
    src = re.sub(r"<br\s*/?>", "\n", src, flags=re.I)
    src = re.sub(r"</?(p|div|tr|table|ul|ol|dl|dt|dd|section|article|main|header|aside|figure)\b[^>]*>",
                 "\n\n", src, flags=re.I)
    text = _strip_tags(src).replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], text)
    return re.sub(r"\n{3,}", "\n\n", text)


def wikitext_to_markdown(src: str) -> str:
    """Reduce MediaWiki source to its running prose: templates, references,
    tables, files and categories go; links keep their visible text; headings
    and list items become Markdown."""
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    src = re.sub(r"<ref\b[^>/]*/>", "", src, flags=re.I)
    src = re.sub(r"<ref\b[^>]*>.*?</ref\s*>", "", src, flags=re.S | re.I)
    src = re.sub(r"<(gallery|math|timeline|syntaxhighlight|score)\b.*?</\1\s*>", "", src,
                 flags=re.S | re.I)

    def inline_template(m):
        # Keep the visible text of the few inline templates that carry prose,
        # so removing templates does not leave holes such as "a height of , but".
        name, *args = [a.strip() for a in m.group(1).split("|")]
        args = [a for a in args if "=" not in a]
        key = name.casefold()
        if key in ("convert", "cvt") and len(args) >= 2:
            if len(args) >= 4 and args[1] in ("to", "-", "–", "and", "or", "by", "x", "×"):
                return " ".join(args[:4])
            return f"{args[0]} {args[1]}"
        if (key in ("lang", "nowrap", "nobr", "small", "em", "transl", "math", "mvar")
                or key.startswith("lang-")) and args:
            return args[-1]
        return m.group(0)

    src = re.sub(r"\{\{([^{}|]+\|[^{}]*)\}\}", inline_template, src)
    for pattern in (r"\{\{[^{}]*\}\}", r"\{\|(?:(?!\{\|).)*?\|\}"):
        while True:
            new = re.sub(pattern, "", src, flags=re.S)
            if new == src:
                break
            src = new

    def link(m):
        body = m.group(1)
        target, _, label = body.partition("|")
        if re.match(r"\s*(file|image|category|media)\s*:", target, re.I):
            return ""
        if re.match(r"\s*[a-z]{2,3}(-[a-z]+)?\s*:", target):  # interlanguage
            return ""
        return (body.rsplit("|", 1)[-1] if label else target).strip()

    while True:
        new = re.sub(r"\[\[([^\[\]]*)\]\]", link, src)
        if new == src:
            break
        src = new
    src = re.sub(r"\[(?:https?:)?//\S+\s+([^\]]+)\]", r"\1", src)
    src = re.sub(r"\[(?:https?:)?//\S+\]", "", src)
    src = re.sub(r"'{2,5}", "", src)
    src = re.sub(r"__[A-Z]+__", "", src)
    src = re.sub(r"^[*]+\s*", "- ", src, flags=re.M)
    src = re.sub(r"^#+\s*", "1. ", src, flags=re.M)
    src = re.sub(r"^[:;]+\s*", "", src, flags=re.M)
    src = re.sub(r"^(={2,6})\s*(.*?)\s*\1\s*$",
                 lambda m: "#" * len(m.group(1)) + " " + m.group(2), src, flags=re.M)
    src = re.sub(r"</?[A-Za-z][^>]*>", "", src)
    src = html.unescape(src).replace("\xa0", " ")
    src = re.sub(r" \(\s*[,;:]?\s*\)", "", src)          # parentheses emptied above
    src = re.sub(r"[ \t]+([,.;:])", r"\1", src)
    lines = [line.rstrip() for line in src.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))


# --- Measurement -------------------------------------------------------------

def metric_rules(registry) -> list[dict]:
    return [r for r in registry.rules
            if r["detector"] == "metric" and r.get("scope") != "project"]


def metric_values(rule: dict, segments, metrics: dict, eff: dict) -> tuple[list[float], int]:
    """Observed values of a metric rule's underlying metric for one document,
    plus how many observations cross the effective threshold. Uses the
    checker's own `metric_observations` and document gates."""
    if metrics["prose_words"] < rule.get("min_words", 0):
        return [], 0
    if metrics["sentences"] < rule.get("min_sentences", 0):
        return [], 0
    values = [float(v) for v, _, _ in llm_ism_check.metric_observations(rule, segments, metrics)]
    crossing = sum(1 for v, _, _ in llm_ism_check.metric_observations(eff, segments, metrics)
                   if llm_ism_check.compare(v, eff.get("comparison", "gt"), eff["threshold"]))
    return values, crossing


def short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= EXCERPT_CHARS else text[:EXCERPT_CHARS - 1] + "…"


def measure_document(doc: dict, text: str, registry) -> dict:
    """Run the checker on one document under its register's profile."""
    profile = doc["register"]
    report = llm_ism_check.analyze(text, doc["id"], registry, profile, False)
    segments = parse_markdown(text)
    findings_by_rule: Counter = Counter()
    finding_examples: dict[str, list[str]] = defaultdict(list)
    for f in report["findings"]:
        for rid in f["rule_ids"]:
            findings_by_rule[rid] += 1
        rule = registry.rule(f["rule_ids"][0])
        if rule["detector"] != "metric":
            finding_examples[f["rule_ids"][0]].append(short(f["excerpt"]))
    candidates_by_rule: Counter = Counter()
    protected = 0
    for c in report["candidates"]:
        if c["protected"]:
            protected += 1
        else:
            candidates_by_rule[c["rule_id"]] += 1
    metrics = report["metrics"]
    observed = {}
    for rule in metric_rules(registry):
        status = registry.family_status(profile, rule["family"])
        eff = llm_ism_check.effective_rule(rule, status, registry.relax_factor)
        values, crossing = metric_values(rule, segments, metrics, eff)
        observed[rule["id"]] = {"values": values, "crossing": crossing}
    return {
        **{k: doc[k] for k in OUTPUT_FIELDS if k in doc},
        "profile": report["document"]["profile"],
        "words_scanned": report["document"]["words_scanned"],
        "findings": len(report["findings"]),
        "findings_by_rule": dict(findings_by_rule),
        "candidates": sum(candidates_by_rule.values()),
        "candidates_by_rule": dict(candidates_by_rule),
        "protected_candidates": protected,
        "examples": {k: v[:2] for k, v in finding_examples.items()},
        "metrics": observed,
        "_text": text,
    }


def per_k(count: int, words_: int) -> float:
    return round(count * 1000 / words_, 3) if words_ else 0.0


def quantile(values: list[float], q: float) -> float:
    """Nearest-rank on sorted values; defined for any non-empty list."""
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return round(ordered[idx], 4)


def summarize(results: list[dict], registry, cross_file: dict | None = None) -> dict:
    """Aggregate per-document results into per-register and per-rule rows."""
    by_register: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_register[r["register"]].append(r)
    registers = {}
    for name in sorted(by_register):
        docs = by_register[name]
        wc = sum(d["words_scanned"] for d in docs)
        findings = sum(d["findings"] for d in docs)
        candidates = sum(d["candidates"] for d in docs)
        rules = []
        for rule in registry.rules:
            rid = rule["id"]
            if rule["detector"] == "llm_judgment" or rule.get("scope") == "project":
                continue
            nf = sum(d["findings_by_rule"].get(rid, 0) for d in docs)
            nc = sum(d["candidates_by_rule"].get(rid, 0) for d in docs)
            if not nf and not nc:
                continue
            examples = []
            for d in docs:
                for ex in d["examples"].get(rid, []):
                    if len(examples) < 3:
                        examples.append({"document": d["id"], "excerpt": ex})
            rules.append({
                "rule_id": rid,
                "detector": rule["detector"],
                "profile_status": registry.family_status(name, rule["family"]),
                "docs_with_finding": sum(1 for d in docs if d["findings_by_rule"].get(rid)),
                "findings": nf,
                "findings_per_1k_words": per_k(nf, wc),
                "docs_with_candidate": sum(1 for d in docs if d["candidates_by_rule"].get(rid)),
                "candidates": nc,
                "candidates_per_1k_words": per_k(nc, wc),
                "examples": examples,
            })
        rules.sort(key=lambda row: (-row["findings"], -row["candidates"], row["rule_id"]))
        metric_rows = []
        for rule in metric_rules(registry):
            rid = rule["id"]
            status = registry.family_status(name, rule["family"])
            eff = llm_ism_check.effective_rule(rule, status, registry.relax_factor)
            values = [v for d in docs for v in d["metrics"].get(rid, {}).get("values", [])]
            eligible = sum(1 for d in docs if d["metrics"].get(rid, {}).get("values"))
            row = {
                "rule_id": rid,
                "metric": rule["metric"],
                "scope": rule.get("scope", "document"),
                "observation_unit": OBSERVATION_UNITS.get(
                    rule["metric"], "document meeting the rule's min_words and min_sentences"),
                "comparison": rule.get("comparison", "gt"),
                "threshold": rule["threshold"],
                "profile_status": status,
                "effective_threshold": None if status == "skip" else round(eff["threshold"], 5),
                "docs_with_observations": eligible,
                "observations": len(values),
                "crossing_effective_threshold": 0 if status == "skip" else sum(
                    d["metrics"].get(rid, {}).get("crossing", 0) for d in docs),
                "docs_crossing": 0 if status == "skip" else sum(
                    1 for d in docs if d["metrics"].get(rid, {}).get("crossing")),
                "distribution": ({k: quantile(values, q) for k, q in QUANTILES}
                                 if values else None),
            }
            metric_rows.append(row)
        registers[name] = {
            "documents": len(docs),
            "prose_words": wc,
            "docs_with_finding": sum(1 for d in docs if d["findings"]),
            "findings": findings,
            "findings_per_1k_words": per_k(findings, wc),
            "docs_with_candidate": sum(1 for d in docs if d["candidates"]),
            "candidates": candidates,
            "candidates_per_1k_words": per_k(candidates, wc),
            "protected_candidates": sum(d["protected_candidates"] for d in docs),
            "rules": rules,
            "metrics": metric_rows,
        }
        if cross_file is not None and name in cross_file:
            registers[name]["cross_file_template"] = cross_file[name]
    return registers


def cross_file_baseline(results: list[dict]) -> dict:
    """ST.CROSS_FILE_TEMPLATE across unrelated documents of one register, using
    the project checker's defaults (5-word phrases, at least 3 files). Unrelated
    authors share no house style, so what recurs here is ordinary phrasing."""
    by_register: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_register[r["register"]][r["id"]] = llm_ism_project_check.document_features(r["_text"])
    out = {}
    for name, files in sorted(by_register.items()):
        report = llm_ism_project_check.analyze(files, 5, 3)
        out[name] = {
            "files": len(files),
            "ngram_size": 5,
            "minimum_files": 3,
            "repeated_phrases": len(report["repeated_phrases"]),
            "top_phrases": [{"phrase": p["phrase"], "file_count": p["file_count"]}
                            for p in report["repeated_phrases"][:5]],
            "repeated_openings": len(report["repeated_openings"]),
            "repeated_heading_frames": len(report["repeated_heading_frames"]),
        }
    return out


def run(manifest: dict, registry, cache_dir: str, offline: bool, record: bool,
        only: set[str] | None = None, fetcher=fetch) -> tuple[list[dict], list[str]]:
    """Load, verify and measure every selected document. Verification of every
    document happens before any measurement, so a mismatch stops the run."""
    warnings: list[str] = []
    texts: list[tuple[dict, str]] = []
    for doc in manifest["documents"]:
        if only and doc["id"] not in only:
            continue
        if doc["register"] not in registry.profile_names():
            raise RegistryError(f"{doc['id']}: register {doc['register']!r} is not a profile")
        raw = load_source(doc, cache_dir, offline, fetcher)
        verify(doc, "source", "source_sha256", raw, record)
        text = extract(raw, doc.get("extract", {}))
        verify(doc, "measured text", "sha256", text.encode("utf-8"), record)
        texts.append((doc, text))
    results = []
    for doc, text in texts:
        result = measure_document(doc, text, registry)
        recorded = doc.get("word_count")
        if recorded is None and record:
            doc["word_count"] = result["words_scanned"]
        elif recorded != result["words_scanned"]:
            warnings.append(f"{doc['id']}: manifest word_count {recorded} but the current "
                            f"checker scans {result['words_scanned']} prose words")
        results.append(result)
    return results, warnings


def build_report(results: list[dict], registry, warnings: list[str], manifest: dict) -> dict:
    registers = summarize(results, registry, cross_file_baseline(results))
    return {
        "tool_version": llm_ism_check.TOOL_VERSION,
        "registry_version": registry.raw.get("registry_version"),
        "manifest_schema_version": manifest.get("schema_version"),
        "capture_dates": sorted({d.get("captured") for d in manifest["documents"]
                                 if d.get("captured")}),
        "documents_measured": len(results),
        "prose_words_measured": sum(r["words_scanned"] for r in results),
        "registers": registers,
        "documents": [{k: v for k, v in r.items()
                       if k in OUTPUT_FIELDS + ("words_scanned", "findings", "candidates",
                                                "findings_by_rule")}
                      for r in results],
        "warnings": warnings,
        "disclaimer": ("Rates of writing-quality signals on a named sample of human-written "
                       "prose from before November 2022. Never evidence of authorship."),
    }


# --- Rendering ---------------------------------------------------------------

def _fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def render_text(report: dict) -> str:
    out = [f"corpus measurement: {report['documents_measured']} document(s), "
           f"{report['prose_words_measured']} prose words; checker {report['tool_version']}, "
           f"registry {report['registry_version']}; captured {', '.join(report['capture_dates'])}"]
    for name, reg in report["registers"].items():
        out.append("")
        out.append(f"== {name}: {reg['documents']} docs, {reg['prose_words']} prose words")
        out.append(f"   findings: {reg['findings']} ({reg['findings_per_1k_words']:g}/1k words), "
                   f"in {reg['docs_with_finding']}/{reg['documents']} docs")
        out.append(f"   candidates: {reg['candidates']} ({reg['candidates_per_1k_words']:g}/1k words), "
                   f"in {reg['docs_with_candidate']}/{reg['documents']} docs; "
                   f"{reg['protected_candidates']} more inside protected spans")
        out.append(f"   {'rule':32} {'status':8} {'docs_f':>6} {'find':>5} {'f/1k':>7} "
                   f"{'docs_c':>6} {'cand':>5} {'c/1k':>7}")
        for row in reg["rules"]:
            out.append(f"   {row['rule_id']:32} {row['profile_status']:8} "
                       f"{row['docs_with_finding']:>6} {row['findings']:>5} "
                       f"{row['findings_per_1k_words']:>7g} {row['docs_with_candidate']:>6} "
                       f"{row['candidates']:>5} {row['candidates_per_1k_words']:>7g}")
        out.append("   metric distributions (observations; effective threshold; crossings):")
        for m in reg["metrics"]:
            dist = m["distribution"]
            spread = (" ".join(f"{k}={_fmt(v)}" for k, v in dist.items()) if dist else "no observations")
            out.append(f"   {m['rule_id']:26} {m['profile_status']:8} n={m['observations']:<4} "
                       f"{m['comparison']} {_fmt(m['effective_threshold'])}; "
                       f"crossing {m['crossing_effective_threshold']} in {m['docs_crossing']} docs; "
                       f"{spread}")
        cf = reg.get("cross_file_template")
        if cf:
            out.append(f"   ST.CROSS_FILE_TEMPLATE baseline: {cf['repeated_phrases']} "
                       f"{cf['ngram_size']}-word phrase(s) in >= {cf['minimum_files']} of "
                       f"{cf['files']} unrelated files")
    for w in report["warnings"]:
        out.append(f"warning: {w}")
    out.append(report["disclaimer"])
    return "\n".join(out)


def render_markdown(report: dict) -> str:
    """Tables only, for pasting into a dated results write-up."""
    out = ["| Register | Docs | Prose words | Docs with a finding | Findings | Per 1k words "
           "| Candidates | Per 1k words |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, reg in report["registers"].items():
        out.append(f"| {name} | {reg['documents']} | {reg['prose_words']} | "
                   f"{reg['docs_with_finding']} | {reg['findings']} | "
                   f"{reg['findings_per_1k_words']:g} | {reg['candidates']} | "
                   f"{reg['candidates_per_1k_words']:g} |")
    for name, reg in report["registers"].items():
        out += ["", f"#### Rules in {name}", "",
                "| Rule | Status | Docs with finding | Findings | Per 1k | Docs with candidate "
                "| Candidates | Per 1k |",
                "|---|---|---:|---:|---:|---:|---:|---:|"]
        for row in reg["rules"]:
            out.append(f"| `{row['rule_id']}` | {row['profile_status']} | "
                       f"{row['docs_with_finding']} | {row['findings']} | "
                       f"{row['findings_per_1k_words']:g} | {row['docs_with_candidate']} | "
                       f"{row['candidates']} | {row['candidates_per_1k_words']:g} |")
    out += ["", "#### Metric distributions", "",
            "| Rule | Register | Status | Threshold (effective) | n | Min | P25 | Median "
            "| P75 | P90 | Max | Crossing (docs) |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    rule_ids = []
    for reg in report["registers"].values():
        for m in reg["metrics"]:
            if m["rule_id"] not in rule_ids:
                rule_ids.append(m["rule_id"])
    for rid in rule_ids:
        for name, reg in report["registers"].items():
            m = next(x for x in reg["metrics"] if x["rule_id"] == rid)
            d = m["distribution"] or {}
            out.append(f"| `{rid}` | {name} | {m['profile_status']} | "
                       f"{m['comparison']} {_fmt(m['effective_threshold'])} | {m['observations']} | "
                       + " | ".join(_fmt(d.get(k)) for k in ("min", "p25", "median", "p75", "p90", "max"))
                       + f" | {m['crossing_effective_threshold']} ({m['docs_crossing']}) |")
    return "\n".join(out)


# --- CLI ---------------------------------------------------------------------

def main(argv=None, fetcher=fetch) -> int:
    ap = argparse.ArgumentParser(
        prog="corpus_measure.py",
        description="Measure the checker's finding rates on the provenance corpus, per register.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  corpus_measure.py\n"
               "  corpus_measure.py --offline --format json --output results.json\n"
               "  corpus_measure.py --only gp-wiki-pencil --format text\n")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST, help="manifest path")
    ap.add_argument("--cache", default=DEFAULT_CACHE,
                    help="cache directory for fetched bytes (default: corpus/cache, gitignored)")
    ap.add_argument("--offline", action="store_true",
                    help="never fetch; fail if a document is missing from the cache")
    ap.add_argument("--format", default="text", choices=["text", "json", "markdown"])
    ap.add_argument("--output", default="-", metavar="PATH", help="write to PATH instead of stdout")
    ap.add_argument("--only", action="append", metavar="ID", help="measure only this document (repeatable)")
    ap.add_argument("--record", action="store_true",
                    help="fill missing source_sha256, sha256 and word_count fields in the manifest; "
                         "never overwrites a recorded checksum")
    args = ap.parse_args(argv)

    try:
        registry = load_registry()
        manifest = load_manifest(args.manifest)
        results, warnings = run(manifest, registry, args.cache, args.offline, args.record,
                                set(args.only) if args.only else None, fetcher)
    except IntegrityError as exc:
        print(f"INTEGRITY FAILURE: {exc}", file=sys.stderr)
        print("The cached or fetched bytes differ from what the manifest recorded. "
              "Delete the cache entry to refetch; if the source itself changed, the "
              "document needs a new immutable URL.", file=sys.stderr)
        return 1
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (RegistryError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.record:
        with open(args.manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"recorded checksums and word counts in {args.manifest}", file=sys.stderr)

    report = build_report(results, registry, warnings, manifest)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if args.format == "json":
        payload = json.dumps(report, indent=2, ensure_ascii=False)
    elif args.format == "markdown":
        payload = render_markdown(report)
    else:
        payload = render_text(report)
    if args.output == "-":
        print(payload)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
