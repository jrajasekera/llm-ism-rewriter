#!/usr/bin/env python3
"""Surface candidate LLM-isms in Markdown or plain text, then judge them in context.

Standard library only. The pipeline is: read, segment and protect, produce raw
candidates, measure structural metrics, aggregate candidates into findings
using references/rules.json and the active context profile, group overlapping
evidence, and emit text, JSON, or SARIF.

A *candidate* is a deterministic match. A *finding* is a candidate that survived
the registry's thresholds and the profile's tolerances. Neither is evidence
about who or what wrote the text; both are writing-quality signals a person or
agent still has to read in context.

Exit codes: 0 ran successfully, 1 --fail-on threshold met, 2 bad input or
arguments, 3 internal or registry failure.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_ism_core import (  # noqa: E402
    LABELED_BULLET_RE, PROSE_KINDS, SCHEMA_VERSION, TOOL_VERSION, Registry,
    RegistryError, Segment, compiled_patterns, line_col, line_offsets,
    load_registry, mask_inline, mask_quote_markers, parse_markdown, split_sentences,
    words,
)

# Metric names this script knows how to compute. scripts/build_catalog.py --check
# fails when the registry names a metric that is not in this set.
IMPLEMENTED_METRICS = frozenset({
    "triads_per_sentence", "em_dashes_per_word", "sentence_len_stdev",
    "words_per_heading", "repeated_heading_frames", "low_continuity_ratio",
    "labeled_bullet_ratio", "anaphora_run_length", "consecutive_short_sentences",
})

STRENGTH_ORDER = ("low", "medium", "high")
PRIORITY_ORDER = ("P0", "P1", "P2")

TRIAD_RE = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? (?:and|or) [\w'-]+(?: [\w'-]+){0,2}\b")
EM_DASH_RE = re.compile(r"—|(?<=\w)--(?=\w)")
LABELED_BULLET_RE = re.compile(
    r"^\s*(?:[-*+]|\d{1,9}[.)])\s+"
    r"(?:(?:\*\*|__)[^*_\n]{1,40}[:：](?:\*\*|__)"      # **Label:**
    r"|(?:\*\*|__)[^*_\n]{1,40}(?:\*\*|__)\s*[:：]"     # **Label**:
    r"|[A-Z][\w /-]{1,30}[:：])"                          # Label:
    r"\s+\S")
ANAPHORIC_OPENERS = frozenset("this that these those it they so but however instead meanwhile therefore then there here".split())
STOPWORDS = frozenset("""
a an the and or but if then than that this these those of in on at to for from by with
is are was were be been being as it its it's they them their we our you your i he she his
her not no do does did can could may might must shall should will would have has had
""".split())


# --- Records -----------------------------------------------------------------

@dataclass
class Candidate:
    rule_id: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    excerpt: str
    segment_kind: str
    paragraph_id: int | None
    protected: bool
    evidence: dict = field(default_factory=dict)


@dataclass
class Finding:
    id: str
    rule_ids: list[str]
    tier: str
    edit_priority: str
    evidence_strength: str
    action: str
    title: str
    reason: str
    suggested_action: str
    location: dict
    excerpt: str
    segment_kind: str
    protected: bool
    evidence: dict = field(default_factory=dict)


# --- Profile detection -------------------------------------------------------

def detect_profile(text: str, segments: list[Segment]) -> tuple[str, list[str]]:
    """Return (profile, cues). Only strong cues move off `general-prose`."""
    cues: list[str] = []
    low = text.lower()
    heads = [s.text.strip("# \n").lower() for s in segments if s.kind == "heading"]
    code = sum(1 for s in segments if s.kind == "code")
    prose_words = sum(len(words(s.text)) for s in segments if s.kind in PROSE_KINDS)

    if any(h.startswith(("dear ", "hi ", "hello ", "hey ")) for h in heads) or \
            re.search(r"^\s*(?:dear|hi|hello|hey)\s+[A-Z][\w.]*,\s*$", text, re.M | re.I):
        if re.search(r"^\s*(?:thanks|best|regards|cheers|sincerely|best regards)[,!]?\s*$", text, re.M | re.I):
            cues.append("salutation and sign-off")
            return "social-email", cues

    if any(h in ("abstract", "methods", "methodology", "results", "discussion", "references")
           for h in heads) and re.search(r"\(\w+(?: et al\.)?,? \d{4}\)|\[\d+\]", text):
        cues.append("abstract/methods/results headings with citations")
        return "academic-research", cues

    if re.search(r"\b(?:shall|must)\b", low) and \
            re.search(r"\b(?:party|parties|licensee|licensor|the services|agreement)\b", low) and \
            re.search(r"^\s*\d+(\.\d+)+\s+\S", text, re.M):
        cues.append("numbered obligations and defined parties")
        return "legal-policy", cues

    if code >= 2 or re.search(r"^\s*(?:\$|>>>)\s+\S", text, re.M) or \
            any(h in ("installation", "install", "usage", "api", "api reference", "options", "parameters",
                      "quick start", "getting started", "configuration") for h in heads):
        cues.append("fenced code, command examples, or install/usage headings")
        return "technical-docs", cues

    if re.search(r"\b(?:sign up|get started free|book a demo|start your free trial|try it free)\b", low):
        cues.append("call to action")
        return "marketing-product", cues

    if prose_words >= 300 and len(re.findall(r"^\s*(?:\"|“)", text, re.M)) >= 4:
        cues.append("sustained dialogue")
        return "creative", cues

    return "general-prose", cues


# --- Threshold resolution ----------------------------------------------------

def effective_rule(rule: dict, status: str, relax: float) -> dict:
    out = dict(rule)
    if status != "relaxed":
        return out
    for key in ("minimum_occurrences", "minimum_distinct", "minimum_total", "min_bullets"):
        if key in out:
            out[key] = int(math.ceil(out[key] * relax))
    if "threshold" in out:
        cmp_ = out.get("comparison", "gt")
        out["threshold"] = out["threshold"] / relax if cmp_ == "lt" else out["threshold"] * relax
    idx = STRENGTH_ORDER.index(out.get("evidence_strength", "low"))
    out["evidence_strength"] = STRENGTH_ORDER[max(0, idx - 1)]
    out["_relaxed"] = True
    return out


def compare(value: float, comparison: str, threshold: float) -> bool:
    return {"gt": value > threshold, "gte": value >= threshold,
            "lt": value < threshold, "lte": value <= threshold}[comparison]


# --- Candidate detection -----------------------------------------------------

def collect_candidates(segments: list[Segment], text: str, registry: Registry) -> list[Candidate]:
    offsets = line_offsets(text)
    out: list[Candidate] = []
    regex_rules = [r for r in registry.rules if r["detector"] == "regex"]
    for seg in segments:
        if seg.kind in ("break", "html"):
            continue
        masked = mask_quote_markers(mask_inline(seg.text))
        # Sentence-scope rules anchor `^` at each sentence, not just each line.
        units = ([(0, masked)] if seg.kind == "heading"
                 else split_sentences(masked) or [(0, masked)])
        for rule in regex_rules:
            scope = rule.get("scope")
            if scope == "heading":
                if seg.kind != "heading":
                    continue
                targets = [(0, masked)]
            else:
                if seg.kind == "heading":
                    targets = [(0, masked.lstrip("# ").rjust(len(masked)))]
                else:
                    targets = units
            for base, unit in targets:
                for pattern in compiled_patterns(rule):
                    for m in pattern.finditer(unit):
                        if not m.group(0).strip():
                            continue
                        sl, sc = line_col(offsets, seg.start_offset + base + m.start())
                        el, ec = line_col(offsets, seg.start_offset + base + m.end())
                        out.append(Candidate(
                            rule_id=rule["id"], start_line=sl, start_column=sc,
                            end_line=el, end_column=ec,
                            excerpt=" ".join(
                                seg.text[base + m.start():base + m.end()].split()),
                            segment_kind=seg.kind, paragraph_id=seg.paragraph_id,
                            protected=seg.protected))
    # lexicon clusters, per prose segment
    for rule in registry.rules:
        if rule["detector"] != "lexicon_cluster":
            continue
        terms = {t.casefold() for t in rule.get("terms", ())}
        for seg in segments:
            if seg.kind not in PROSE_KINDS:
                continue
            found = [w for w in words(mask_inline(seg.text)) if w.casefold() in terms]
            if not found:
                continue
            sl, sc = line_col(offsets, seg.start_offset)
            el, ec = line_col(offsets, seg.end_offset)
            out.append(Candidate(
                rule_id=rule["id"], start_line=sl, start_column=sc, end_line=el, end_column=ec,
                excerpt=", ".join(sorted(set(found))), segment_kind=seg.kind,
                paragraph_id=seg.paragraph_id, protected=seg.protected,
                evidence={"terms": sorted(set(t.casefold() for t in found)),
                          "distinct": len({t.casefold() for t in found}), "total": len(found)}))
    # document-scope repetition
    for rule in registry.rules:
        if rule["detector"] != "repetition":
            continue
        terms = {t.casefold() for t in rule.get("terms", ())}
        hits: dict[str, list[Candidate]] = defaultdict(list)
        for seg in segments:
            if seg.kind not in PROSE_KINDS or seg.protected:
                continue
            masked = mask_inline(seg.text)
            for m in re.finditer(r"[A-Za-z][\w'-]*", masked):
                if m.group(0).casefold() in terms:
                    sl, sc = line_col(offsets, seg.start_offset + m.start())
                    el, ec = line_col(offsets, seg.start_offset + m.end())
                    hits[m.group(0).casefold()].append(Candidate(
                        rule_id=rule["id"], start_line=sl, start_column=sc,
                        end_line=el, end_column=ec, excerpt=m.group(0),
                        segment_kind=seg.kind, paragraph_id=seg.paragraph_id,
                        protected=False, evidence={"term": m.group(0).casefold()}))
        for term, cands in hits.items():
            first = cands[0]
            first.evidence = {"term": term, "occurrences": len(cands),
                              "lines": sorted({c.start_line for c in cands})}
            out.append(first)
    return out


# --- Metrics -----------------------------------------------------------------

def compute_metrics(segments: list[Segment], text: str) -> dict:
    prose_segs = [s for s in segments if s.kind in PROSE_KINDS and not s.protected]
    prose_text = "\n\n".join(mask_inline(s.text) for s in prose_segs)
    prose_words = words(prose_text)
    sentences = [s for _, s in split_sentences(prose_text) if words(s)]
    lengths = [len(words(s)) for s in sentences]
    headings = [s for s in segments if s.kind == "heading"]
    bullets = [s for s in segments if s.kind == "list_item"]
    labeled = [s for s in bullets if LABELED_BULLET_RE.match(s.text)]

    m = {
        "words_total": len(words(text)),
        "prose_words": len(prose_words),
        "sentences": len(sentences),
        "headings": len(headings),
        "bullets": len(bullets),
        "labeled_bullets": len(labeled),
        "triads": len(TRIAD_RE.findall(prose_text)),
        "em_dashes": len(EM_DASH_RE.findall(prose_text)),
        "protected_segments": sum(1 for s in segments if s.protected),
    }
    wc = max(len(prose_words), 1)
    sc = max(len(sentences), 1)
    m["triads_per_sentence"] = round(m["triads"] / sc, 4)
    m["em_dashes_per_word"] = round(m["em_dashes"] / wc, 5)
    m["mean_sentence_len"] = round(statistics.fmean(lengths), 1) if lengths else 0.0
    m["sentence_len_stdev"] = round(statistics.pstdev(lengths), 1) if len(lengths) > 1 else 0.0
    m["words_per_heading"] = round(len(prose_words) / len(headings), 1) if headings else None
    m["labeled_bullet_ratio"] = round(len(labeled) / len(bullets), 3) if bullets else 0.0
    m["repeated_heading_frames"] = _heading_frames(headings)
    m["low_continuity_ratio"] = _continuity(sentences)
    return m


def _heading_frames(headings: list[Segment]) -> int:
    by_level: dict[int, Counter] = defaultdict(Counter)
    for h in headings:
        title = h.text.strip().lstrip("#").strip()
        toks = [t.casefold() for t in words(title)]
        if len(toks) >= 2:
            by_level[h.heading_level or 0][toks[0]] += 1
    return max((c.most_common(1)[0][1] for c in by_level.values() if c), default=0)


def _continuity(sentences: list[str]) -> float:
    if len(sentences) < 2:
        return 0.0
    breaks = 0
    prev = {w.casefold() for w in words(sentences[0])} - STOPWORDS
    for s in sentences[1:]:
        toks = words(s)
        cur = {w.casefold() for w in toks} - STOPWORDS
        opener = toks[0].casefold() if toks else ""
        if not (cur & prev) and opener not in ANAPHORIC_OPENERS:
            breaks += 1
        prev = cur
    return round(breaks / (len(sentences) - 1), 3)


def _paragraph_runs(segments: list[Segment]):
    """Yield (segment, sentences) for unprotected prose segments."""
    for seg in segments:
        if seg.kind in PROSE_KINDS and not seg.protected:
            sents = [s for _, s in split_sentences(mask_inline(seg.text)) if words(s)]
            if sents:
                yield seg, sents


def metric_observations(rule: dict, segments: list[Segment], metrics: dict) -> list[tuple[float, dict, Segment | None]]:
    """Return (value, evidence, anchor_segment) triples for one metric rule."""
    name = rule["metric"]
    if name == "labeled_bullet_ratio":
        out = []
        by_section: dict[tuple, list[Segment]] = defaultdict(list)
        for s in segments:
            if s.kind == "list_item":
                by_section[s.section_path].append(s)
        for section, items in by_section.items():
            if len(items) < rule.get("min_bullets", 4):
                continue
            labeled = [s for s in items if LABELED_BULLET_RE.match(s.text)]
            ratio = len(labeled) / len(items)
            out.append((ratio, {"labeled_bullets": len(labeled), "all_bullets": len(items),
                                "ratio": round(ratio, 3),
                                "scope": "section: " + (section[-1] if section else "(document)")},
                        labeled[0] if labeled else items[0]))
        return out
    if name == "anaphora_run_length":
        out = []
        for seg, sents in _paragraph_runs(segments):
            best, run, prev = 1, 1, None
            for s in sents:
                toks = words(s)
                first = toks[0].casefold() if toks else ""
                run = run + 1 if first and first == prev else 1
                best = max(best, run)
                prev = first
            if best >= 2 and len(words(seg.text)) >= rule.get("min_words", 0):
                out.append((best, {"run_length": best, "sentences": len(sents),
                                   "scope": f"paragraph {seg.paragraph_id}"}, seg))
        return out
    if name == "consecutive_short_sentences":
        out = []
        for seg, sents in _paragraph_runs(segments):
            best, run = 0, 0
            for s in sents:
                run = run + 1 if len(words(s)) <= 5 else 0
                best = max(best, run)
            if best and len(words(seg.text)) >= rule.get("min_words", 0):
                out.append((best, {"run_length": best, "sentences": len(sents),
                                   "scope": f"paragraph {seg.paragraph_id}"}, seg))
        return out
    value = metrics.get(name)
    if value is None:
        return []
    evidence = {"value": value, "scope": "document"}
    for extra in ("triads", "sentences", "em_dashes", "prose_words", "headings",
                  "labeled_bullets", "bullets"):
        if extra in metrics:
            evidence[extra] = metrics[extra]
    return [(value, evidence, None)]


# --- Aggregation -------------------------------------------------------------

def aggregate(candidates: list[Candidate], metrics: dict, segments: list[Segment], text: str,
              registry: Registry, profile: str, include_protected: bool) -> tuple[list[Finding], int, list[str]]:
    offsets = line_offsets(text)
    relax = registry.relax_factor
    findings: list[Finding] = []
    suppressed = 0
    notes: list[str] = []
    counter = 0

    def new_id():
        nonlocal counter
        counter += 1
        return f"finding-{counter}"

    by_rule: dict[str, list[Candidate]] = defaultdict(list)
    for c in candidates:
        by_rule[c.rule_id].append(c)

    for rule in registry.rules:
        rid = rule["id"]
        status = registry.family_status(profile, rule["family"])
        cands = by_rule.get(rid, [])
        if status == "skip":
            suppressed += len(cands)
            if cands:
                notes.append(f"{len(cands)} {rid} candidate(s) skipped by the {profile} profile")
            continue
        eff = effective_rule(rule, status, relax)

        if rule["detector"] == "regex":
            visible = [c for c in cands if include_protected or not c.protected]
            suppressed += len(cands) - len(visible)
            scoped: dict[object, list[Candidate]] = defaultdict(list)
            for c in visible:
                key = c.paragraph_id if eff.get("scope") == "paragraph" else "doc"
                scoped[key].append(c)
            for group in scoped.values():
                need = eff.get("minimum_occurrences", 1)
                if len(group) < need:
                    suppressed += len(group)
                    if group:
                        notes.append(
                            f"{len(group)} isolated {rid} match(es) below the "
                            f"{'relaxed ' if eff.get('_relaxed') else ''}threshold of {need}")
                    continue
                for c in group:
                    findings.append(Finding(
                        id=new_id(), rule_ids=[rid], tier=rule["tier"],
                        edit_priority=eff["edit_priority"], evidence_strength=eff["evidence_strength"],
                        action=rule["action"], title=rule["title"], reason=rule["reason"],
                        suggested_action=rule["fix"],
                        location={"start_line": c.start_line, "start_column": c.start_column,
                                  "end_line": c.end_line, "end_column": c.end_column},
                        excerpt=c.excerpt, segment_kind=c.segment_kind, protected=c.protected,
                        evidence={"occurrences": len(group), **c.evidence}))

        elif rule["detector"] == "lexicon_cluster":
            for c in cands:
                if c.protected and not include_protected:
                    suppressed += 1
                    continue
                ev = c.evidence
                if ev.get("distinct", 0) < eff.get("minimum_distinct", 3) or \
                        ev.get("total", 0) < eff.get("minimum_total", 3):
                    suppressed += 1
                    continue
                findings.append(Finding(
                    id=new_id(), rule_ids=[rid], tier=rule["tier"],
                    edit_priority=eff["edit_priority"], evidence_strength=eff["evidence_strength"],
                    action=rule["action"], title=rule["title"], reason=rule["reason"],
                    suggested_action=rule["fix"],
                    location={"start_line": c.start_line, "start_column": c.start_column,
                              "end_line": c.end_line, "end_column": c.end_column},
                    excerpt=c.excerpt, segment_kind=c.segment_kind, protected=c.protected,
                    evidence={**ev, "minimum_distinct": eff.get("minimum_distinct")}))

        elif rule["detector"] == "repetition":
            for c in cands:
                need = eff.get("minimum_occurrences", 3)
                if c.evidence.get("occurrences", 0) < need:
                    suppressed += 1
                    continue
                findings.append(Finding(
                    id=new_id(), rule_ids=[rid], tier=rule["tier"],
                    edit_priority=eff["edit_priority"], evidence_strength=eff["evidence_strength"],
                    action=rule["action"], title=rule["title"], reason=rule["reason"],
                    suggested_action=rule["fix"],
                    location={"start_line": c.start_line, "start_column": c.start_column,
                              "end_line": c.end_line, "end_column": c.end_column},
                    excerpt=c.excerpt, segment_kind=c.segment_kind, protected=False,
                    evidence={**c.evidence, "minimum_occurrences": need}))

        elif rule["detector"] == "metric":
            if rule.get("scope") == "project":
                continue
            if metrics["prose_words"] < eff.get("min_words", 0):
                continue
            if metrics["sentences"] < eff.get("min_sentences", 0):
                continue
            for value, evidence, anchor in metric_observations(eff, segments, metrics):
                if not compare(value, eff.get("comparison", "gt"), eff["threshold"]):
                    continue
                loc = ({"start_line": anchor.start_line, "start_column": 1,
                        "end_line": anchor.end_line, "end_column": 1} if anchor else
                       {"start_line": 0, "start_column": 0, "end_line": 0, "end_column": 0})
                findings.append(Finding(
                    id=new_id(), rule_ids=[rid], tier=rule["tier"],
                    edit_priority=eff["edit_priority"], evidence_strength=eff["evidence_strength"],
                    action=rule["action"], title=rule["title"], reason=rule["reason"],
                    suggested_action=rule["fix"],
                    location=loc,
                    excerpt=anchor.text.strip().splitlines()[0][:120] if anchor else rule["metric"],
                    segment_kind=anchor.kind if anchor else "document", protected=False,
                    evidence={**evidence, "metric": rule["metric"], "threshold": eff["threshold"],
                              "comparison": eff.get("comparison", "gt"),
                              "threshold_status": rule.get("threshold_status", "provisional")}))
        # llm_judgment rules never produce a finding here; see references/detector-map.md

    return group_overlaps(findings), suppressed, notes


def group_overlaps(findings: list[Finding]) -> list[Finding]:
    """Merge findings whose spans overlap into one finding with several rule IDs."""
    spans = [f for f in findings if f.location["start_line"] > 0]
    docwide = [f for f in findings if f.location["start_line"] == 0]
    spans.sort(key=lambda f: (f.location["start_line"], f.location["start_column"],
                              -f.location["end_column"]))
    merged: list[Finding] = []
    for f in spans:
        target = None
        for g in merged:
            if g.location["start_line"] != f.location["start_line"]:
                continue
            a0, a1 = g.location["start_column"], g.location["end_column"]
            b0, b1 = f.location["start_column"], f.location["end_column"]
            overlap = min(a1, b1) - max(a0, b0)
            if overlap > 0 and overlap >= 0.5 * min(a1 - a0, b1 - b0):
                target = g
                break
        if target is None:
            merged.append(f)
            continue
        if f.rule_ids[0] not in target.rule_ids:
            target.rule_ids.append(f.rule_ids[0])
        if PRIORITY_ORDER.index(f.edit_priority) < PRIORITY_ORDER.index(target.edit_priority):
            target.edit_priority = f.edit_priority
        if STRENGTH_ORDER.index(f.evidence_strength) > STRENGTH_ORDER.index(target.evidence_strength):
            target.evidence_strength = f.evidence_strength
        target.location["end_column"] = max(target.location["end_column"], f.location["end_column"])
        target.location["end_line"] = max(target.location["end_line"], f.location["end_line"])
        target.evidence.setdefault("grouped", []).append({"rule_id": f.rule_ids[0], "excerpt": f.excerpt})
    return sorted(merged + docwide,
                  key=lambda f: (PRIORITY_ORDER.index(f.edit_priority),
                                 f.location["start_line"], f.location["start_column"]))


def density_label(findings: list[Finding], prose_words: int) -> tuple[str, str]:
    counted = [f for f in findings if f.tier != "clarity" and not f.protected]
    fingerprints = sum(1 for f in counted if f.tier == "fingerprint")
    n = len(counted)
    per = (n / prose_words * 1000) if prose_words else 0
    if n == 0:
        label = "none"
    elif fingerprints >= 2 or per > 10:
        label = "heavy"
    elif fingerprints >= 1 or per >= 3.33:
        label = "moderate"
    else:
        label = "light"
    detail = (f"{n} finding(s) across {prose_words} scanned prose words"
              + (f", including {fingerprints} fingerprint(s)" if fingerprints else ""))
    return label, detail


# --- Report ------------------------------------------------------------------

def analyze(text: str, path: str, registry: Registry, profile_arg: str,
            include_protected: bool) -> dict:
    segments = parse_markdown(text)
    if profile_arg == "auto":
        profile, cues = detect_profile(text, segments)
        source = "auto" if cues else "default"
    else:
        profile, cues, source = profile_arg, [], "explicit"
    if profile not in registry.profile_names():
        raise RegistryError(f"unknown profile: {profile}")

    candidates = collect_candidates(segments, text, registry)
    metrics = compute_metrics(segments, text)
    findings, suppressed, notes = aggregate(
        candidates, metrics, segments, text, registry, profile, include_protected)
    label, detail = density_label(findings, metrics["prose_words"])
    warnings = [w for s in segments for w in s.warnings]

    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "registry_version": registry.raw.get("registry_version"),
        "document": {
            "path": path,
            "profile": profile,
            "profile_source": source,
            "profile_cues": cues,
            "words_total": metrics["words_total"],
            "words_scanned": metrics["prose_words"],
            "protected_segments": metrics["protected_segments"],
        },
        "summary": {
            "findings": len(findings),
            "candidates": len(candidates),
            "candidates_suppressed": suppressed,
            "by_priority": {p: sum(1 for f in findings if f.edit_priority == p) for p in PRIORITY_ORDER},
            "by_tier": {t: sum(1 for f in findings if f.tier == t)
                        for t in ("fingerprint", "cliche", "structural", "clarity")},
            "density": label,
            "density_evidence": detail,
        },
        "findings": [asdict(f) for f in findings],
        "candidates": [asdict(c) for c in candidates],
        "metrics": metrics,
        "suppression_notes": notes,
        "warnings": warnings,
        "disclaimer": "Writing-quality signals only. Never evidence of authorship.",
    }


def render_text(report: dict, level: str) -> str:
    doc, summ = report["document"], report["summary"]
    out = [f"== {doc['path']}",
           f"   Context: {doc['profile']} ({doc['profile_source']}"
           + (f": {'; '.join(doc['profile_cues'])}" if doc["profile_cues"] else "") + ")",
           f"   {doc['words_scanned']} scanned prose words of {doc['words_total']}; "
           f"{doc['protected_segments']} protected segment(s)"]
    rows = report["candidates"] if level == "candidates" else report["findings"]
    if not rows:
        out.append("   no " + level)
    elif level == "candidates":
        for c in rows:
            tag = " [protected]" if c["protected"] else ""
            out.append(f"   {c['rule_id']} L{c['start_line']}:{c['start_column']} "
                       f"{c['excerpt']!r}{tag}")
    else:
        for f in rows:
            loc = f"L{f['location']['start_line']}" if f["location"]["start_line"] else "doc"
            if f["location"]["end_line"] > f["location"]["start_line"]:
                loc += f"-{f['location']['end_line']}"
            tag = " [Protected]" if f["protected"] else ""
            ev = ", ".join(f["rule_ids"])
            out.append(f"   [{f['edit_priority']} {f['tier']}]{tag} {loc}: {f['excerpt']!r}")
            out.append(f"       {f['reason']}")
            out.append(f"       evidence: {ev} ({f['evidence_strength']}); action: {f['suggested_action']}")
    if report["suppression_notes"]:
        out.append("   Suppressed: " + "; ".join(report["suppression_notes"][:6])
                   + (" …" if len(report["suppression_notes"]) > 6 else ""))
    if report["warnings"]:
        out.append("   Parser warnings: " + "; ".join(report["warnings"]))
    out.append(f"   Density: {summ['density']} — {summ['density_evidence']}")
    out.append("   " + report["disclaimer"])
    return "\n".join(out)


def render_sarif(reports: list[dict], registry: Registry) -> str:
    used = {rid for r in reports for f in r["findings"] for rid in f["rule_ids"]}
    rules = [{
        "id": rid,
        "name": registry.rule(rid)["title"],
        "shortDescription": {"text": registry.rule(rid)["title"]},
        "fullDescription": {"text": registry.rule(rid)["reason"]},
        "help": {"text": registry.rule(rid)["fix"]},
        "properties": {"tier": registry.rule(rid)["tier"],
                       "family": registry.rule(rid)["family"]},
    } for rid in sorted(used)]
    results = []
    for r in reports:
        for f in r["findings"]:
            level = {"P0": "error", "P1": "warning", "P2": "note"}[f["edit_priority"]]
            region = {"startLine": max(f["location"]["start_line"], 1),
                      "startColumn": max(f["location"]["start_column"], 1),
                      "endLine": max(f["location"]["end_line"], 1),
                      "endColumn": max(f["location"]["end_column"], 1)}
            results.append({
                "ruleId": f["rule_ids"][0], "level": level,
                "message": {"text": f"{f['reason']} {f['suggested_action']}"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": r["document"]["path"]},
                    "region": region}}],
                "properties": {"rule_ids": f["rule_ids"], "tier": f["tier"],
                               "evidence_strength": f["evidence_strength"]},
            })
    return json.dumps({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "llm-ism-check", "version": TOOL_VERSION,
                                      "informationUri": "https://github.com/jrajasekera/llm-ism-rewriter",
                                      "rules": rules}},
                  "results": results}],
    }, indent=2)


# --- CLI ---------------------------------------------------------------------

def build_parser(registry_profiles: list[str]) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="llm_ism_check.py",
        description="Report candidate and contextual LLM-ism findings in prose. "
                    "Signals about how text reads, never about who wrote it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  llm_ism_check.py draft.md\n"
               "  llm_ism_check.py --profile technical-docs --format json README.md\n"
               "  cat draft.md | llm_ism_check.py -\n"
               "  llm_ism_check.py --level candidates --include-protected draft.md\n")
    ap.add_argument("files", nargs="+", help="files to scan, or '-' to read stdin")
    ap.add_argument("--profile", default="auto", choices=["auto"] + registry_profiles,
                    help="context profile (default: auto, falling back to general-prose)")
    ap.add_argument("--format", default="text", choices=["text", "json", "sarif"],
                    help="output format (default: text)")
    ap.add_argument("--level", default="findings", choices=["findings", "candidates"],
                    help="report contextual findings or raw candidates (default: findings)")
    ap.add_argument("--include-protected", action="store_true",
                    help="also report matches inside quotations, code, tables, and frontmatter")
    ap.add_argument("--fail-on", default="none", choices=["none", "P0", "P1", "any"],
                    help="exit 1 when a finding at this priority or higher exists (default: none)")
    ap.add_argument("--max-findings", type=int, default=0, metavar="N",
                    help="summarize after N findings per file (0 = no limit)")
    ap.add_argument("--rules", metavar="PATH", help="path to an alternate rules.json")
    ap.add_argument("--output", metavar="PATH", default="-", help="write to PATH instead of stdout")
    ap.add_argument("--json", action="store_true", help=argparse.SUPPRESS)  # back-compat alias
    ap.add_argument("--version", action="version", version=f"llm_ism_check {TOOL_VERSION}")
    return ap


def main(argv=None) -> int:
    try:
        probe = load_registry(None)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    ap = build_parser(probe.profile_names())
    args = ap.parse_args(argv)
    if args.json:
        args.format = "json"
    try:
        registry = load_registry(args.rules) if args.rules else probe
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.files.count("-") and len(args.files) > 1:
        print("error: '-' cannot be combined with file paths", file=sys.stderr)
        return 2

    reports = []
    for path in args.files:
        try:
            text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        try:
            reports.append(analyze(text, "<stdin>" if path == "-" else path,
                                   registry, args.profile, args.include_protected))
        except RegistryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3

    if args.max_findings:
        for r in reports:
            extra = len(r["findings"]) - args.max_findings
            if extra > 0:
                r["findings"] = r["findings"][:args.max_findings]
                r["summary"]["truncated"] = extra

    if args.format == "json":
        payload = json.dumps(reports if len(reports) > 1 else reports[0], indent=2)
    elif args.format == "sarif":
        payload = render_sarif(reports, registry)
    else:
        payload = "\n\n".join(render_text(r, args.level) for r in reports)

    if args.output == "-":
        print(payload)
    else:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(payload + "\n")
        except OSError as exc:
            print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2

    if args.fail_on != "none":
        worst = {"P0": ("P0",), "P1": ("P0", "P1"), "any": PRIORITY_ORDER}[args.fail_on]
        if any(f["edit_priority"] in worst for r in reports for f in r["findings"]):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
