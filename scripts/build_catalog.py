#!/usr/bin/env python3
"""Enforce the contract between the rule registry, the prose catalog, and the code.

references/rules.json is canonical for deterministic rules. references/patterns.md
is the human-readable catalog an agent reads. scripts/llm_ism_check.py implements
a subset. Nothing stops those three from drifting apart except this script.

    build_catalog.py --check    verify the contract; exit 1 on drift
    build_catalog.py --write    regenerate the rule index inside patterns.md

Exit codes: 0 contract holds, 1 drift found, 2 bad arguments, 3 unreadable input.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_ism_core import RegistryError, load_registry  # noqa: E402
import llm_ism_check  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
PATTERNS = os.path.join(ROOT, "references", "patterns.md")
DETECTOR_MAP = os.path.join(ROOT, "references", "detector-map.md")
NEGATIVE_RESULTS = os.path.join(ROOT, "references", "negative-results.md")
SKILL = os.path.join(ROOT, "SKILL.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")

BEGIN = "<!-- BEGIN GENERATED RULE INDEX -->"
END = "<!-- END GENERATED RULE INDEX -->"

VALID_ACTIONS = {"remove", "replace", "restate", "merge", "split", "request-detail",
                 "leave", "review_in_context", "report"}
VALID_PRIORITIES = {"P0", "P1", "P2"}
VALID_STRENGTHS = {"low", "medium", "high"}
VALID_DETECTORS = {"regex", "lexicon_cluster", "repetition", "metric", "llm_judgment"}
PROJECT_METRICS = {"repeated_ngram_files"}
# Keys that make a rule executable. A judgment-only rule carrying one would look
# measurable without being measured.
EXECUTABLE_KEYS = ("patterns", "terms", "terms_from", "metric", "threshold", "comparison",
                   "threshold_status", "minimum_distinct", "minimum_occurrences",
                   "minimum_total", "min_bullets", "min_sentences", "min_words")
# Families that exist only as agent judgment, with the one profile that enables each.
JUDGMENT_FAMILIES = {"narrative": "creative"}


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def render_index(registry) -> str:
    rows = ["| Rule ID | Catalog | Tier | Family | Priority | Detector | Action |",
            "|---------|---------|------|--------|----------|----------|--------|"]
    for rule in sorted(registry.rules, key=lambda r: (r["catalog"], r["id"])):
        rows.append("| `{id}` | {catalog} | {tier} | {family} | {edit_priority} | {detector} | {action} |"
                    .format(**rule))
    return "\n".join(rows)


def check(registry) -> list[str]:
    problems: list[str] = []
    patterns_md = read(PATTERNS)
    detector_md = read(DETECTOR_MAP)
    negative_md = read(NEGATIVE_RESULTS)
    skill_md = read(SKILL)

    tiers = set(registry.raw["tiers"])
    families = {r["family"] for r in registry.rules}

    for rule in registry.rules:
        rid = rule["id"]
        for key in ("title", "catalog", "tier", "family", "edit_priority",
                    "evidence_strength", "detector", "action", "reason", "fix"):
            if key not in rule and not (key in ("evidence_strength",) and rule["detector"] == "llm_judgment"):
                problems.append(f"{rid}: missing required field {key!r}")
        if rule.get("tier") not in tiers:
            problems.append(f"{rid}: tier {rule.get('tier')!r} is not one of {sorted(tiers)}")
        if rule.get("edit_priority") not in VALID_PRIORITIES:
            problems.append(f"{rid}: edit_priority {rule.get('edit_priority')!r} is invalid")
        if rule.get("evidence_strength", "low") not in VALID_STRENGTHS:
            problems.append(f"{rid}: evidence_strength {rule.get('evidence_strength')!r} is invalid")
        if rule.get("action") not in VALID_ACTIONS:
            problems.append(f"{rid}: action {rule.get('action')!r} is not one of {sorted(VALID_ACTIONS)}")
        detector = rule.get("detector")
        if detector not in VALID_DETECTORS:
            problems.append(f"{rid}: detector {detector!r} is invalid")

        anchor = rule.get("catalog", "")
        if not re.search(rf"^#{{2,3}} {re.escape(anchor)}[.\s]", patterns_md, re.M):
            problems.append(f"{rid}: catalog anchor {anchor!r} has no heading in references/patterns.md")
        if f"`{rid}`" not in detector_md:
            problems.append(f"{rid}: not listed in references/detector-map.md")

        if detector == "regex":
            if not rule.get("patterns"):
                problems.append(f"{rid}: declared executable but has no patterns")
            for pattern in rule.get("patterns", ()):
                try:
                    re.compile(pattern)
                except re.error as exc:
                    problems.append(f"{rid}: pattern {pattern!r} does not compile: {exc}")
        elif detector == "llm_judgment":
            pretend = [k for k in EXECUTABLE_KEYS if k in rule]
            if pretend:
                problems.append(f"{rid}: judgment-only rules must not carry a pretend detector "
                                f"({', '.join(pretend)})")
            if not rule.get("judgment_prompt"):
                problems.append(f"{rid}: judgment-only rules need a judgment_prompt")
        elif detector == "metric":
            metric = rule.get("metric")
            known = llm_ism_check.IMPLEMENTED_METRICS | PROJECT_METRICS
            if metric not in known:
                problems.append(f"{rid}: metric {metric!r} has no implementation")
            if "threshold" not in rule or "comparison" not in rule:
                problems.append(f"{rid}: metric rules need a threshold and a comparison")
            if rule.get("threshold_status") == "provisional" and rid not in negative_md:
                problems.append(f"{rid}: provisional threshold is not recorded in "
                                f"references/negative-results.md")
        elif detector == "lexicon_cluster":
            if not rule.get("terms"):
                problems.append(f"{rid}: lexicon_cluster needs terms")
            if "minimum_distinct" not in rule:
                problems.append(f"{rid}: lexicon_cluster needs minimum_distinct")
        elif detector == "repetition":
            if not rule.get("terms"):
                problems.append(f"{rid}: repetition needs terms or terms_from")
            if "minimum_occurrences" not in rule:
                problems.append(f"{rid}: repetition needs minimum_occurrences")

    # judgment-only families: no executable rule, and one enabling profile
    for family, home in JUDGMENT_FAMILIES.items():
        for rule in registry.rules:
            if rule["family"] == family and rule.get("detector") != "llm_judgment":
                problems.append(f"{rule['id']}: the {family} family is judgment-only")
        for name in registry.profile_names():
            status = registry.profiles[name]["families"].get(family)
            expected = "full" if name == home else "skip"
            if status != expected:
                problems.append(f"profile {name}: family {family} must be {expected!r}, "
                                f"not {status!r}")

    # every rule id mentioned in the detector map must exist
    for rid in set(re.findall(r"`((?:FP|LX|RH|ST|CL)\.[A-Z0-9_]+)`", detector_md)):
        if rid not in registry.by_id:
            problems.append(f"references/detector-map.md names unknown rule {rid}")

    # profiles
    for name in registry.profile_names():
        covered = set(registry.profiles[name]["families"])
        if covered != families:
            problems.append(f"profile {name}: family coverage mismatch "
                            f"(missing {sorted(families - covered)}, extra {sorted(covered - families)})")
        for family, status in registry.profiles[name]["families"].items():
            if status not in ("full", "relaxed", "skip"):
                problems.append(f"profile {name}: family {family} has invalid status {status!r}")

    # tier vocabulary shared with SKILL.md
    for tier in tiers:
        if tier not in skill_md.lower():
            problems.append(f"tier {tier!r} from the registry is never named in SKILL.md")

    # versions in sync
    version = registry.raw.get("registry_version")
    if version != llm_ism_check.TOOL_VERSION:
        problems.append(f"registry_version {version} != TOOL_VERSION {llm_ism_check.TOOL_VERSION}")
    m = re.search(r"^\s*version:\s*\"?([\w.]+)\"?\s*$", skill_md, re.M)
    if not m:
        problems.append("SKILL.md frontmatter has no version")
    elif m.group(1) != version:
        problems.append(f"SKILL.md version {m.group(1)} != registry_version {version}")
    if os.path.exists(CHANGELOG):
        changelog = read(CHANGELOG)
        if f"## [{version}]" not in changelog and f"## {version}" not in changelog:
            problems.append(f"CHANGELOG.md has no entry for {version}")

    # Agent Skills packaging expectations that can be checked locally.
    fm = re.match(r"^---\n(.*?)\n---\n", skill_md, re.S)
    if not fm:
        problems.append("SKILL.md has no YAML frontmatter")
    else:
        block = fm.group(1)
        for field in ("name:", "description:", "license:"):
            if field not in block:
                problems.append(f"SKILL.md frontmatter is missing {field!r}")
        name = re.search(r"^name:\s*(\S+)\s*$", block, re.M)
        if not name:
            problems.append("SKILL.md frontmatter has no name")
        elif name.group(1) != "llm-ism-rewriter":
            problems.append(f"SKILL.md name {name.group(1)!r} does not match the skill")
        desc = re.search(r"^description:\s*(.+)$", block, re.M)
        if desc and len(desc.group(1)) > 1024:
            problems.append("SKILL.md description exceeds 1024 characters")
    body_lines = len(skill_md.splitlines())
    if body_lines > 500:
        problems.append(f"SKILL.md is {body_lines} lines; the progressive-disclosure "
                        f"budget is 500")
    for target in re.findall(r"\]\((references/[\w./-]+|scripts/[\w./-]+)\)", skill_md):
        if not os.path.exists(os.path.join(ROOT, target)):
            problems.append(f"SKILL.md links to a missing file: {target}")

    # generated index is current
    current = extract_index(patterns_md)
    if current is None:
        problems.append("references/patterns.md has no generated rule index block")
    elif current.strip() != render_index(registry).strip():
        problems.append("references/patterns.md rule index is stale; run build_catalog.py --write")
    return problems


def extract_index(text: str) -> str | None:
    m = re.search(re.escape(BEGIN) + r"\n(.*?)" + re.escape(END), text, re.S)
    return m.group(1) if m else None


def write_index(registry) -> bool:
    text = read(PATTERNS)
    block = render_index(registry)
    if BEGIN not in text or END not in text:
        raise RegistryError("references/patterns.md has no generated rule index markers")
    new = re.sub(re.escape(BEGIN) + r"\n.*?" + re.escape(END),
                 BEGIN + "\n" + block + "\n" + END, text, flags=re.S)
    if new == text:
        return False
    with open(PATTERNS, "w", encoding="utf-8") as fh:
        fh.write(new)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="build_catalog.py",
        description="Verify or regenerate the rule registry / catalog / code contract.")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="verify the contract and exit 1 on drift")
    group.add_argument("--write", action="store_true", help="regenerate the rule index in patterns.md")
    ap.add_argument("--rules", metavar="PATH", help="path to an alternate rules.json")
    args = ap.parse_args(argv)

    try:
        registry = load_registry(args.rules)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    if args.write:
        try:
            changed = write_index(registry)
        except (RegistryError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3
        print("rule index " + ("updated" if changed else "already current"))
        return 0

    try:
        problems = check(registry)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    if problems:
        print(f"catalog contract: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"catalog contract: ok ({len(registry.rules)} rules, "
          f"{len(registry.profile_names())} profiles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
