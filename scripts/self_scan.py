#!/usr/bin/env python3
"""Scan this repository's own prose against its own catalog, under a budget.

The skill's prose is subject to the skill's rules. But `references/patterns.md`
and `references/examples.md` deliberately quote the clichés they describe, so a
raw count is meaningless. This script reports both the raw finding count and the
count after per-file exemptions, and compares the latter against a committed
budget in `self-scan-budget.json`.

A budget should move down or hold. Raising one requires editing the file and
saying why, which is the point.

Exit codes: 0 within budget, 1 over budget, 2 bad arguments, 3 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_ism_core import RegistryError, load_registry  # noqa: E402
import llm_ism_check  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
BUDGET_PATH = os.path.join(ROOT, "self-scan-budget.json")


def load_budget() -> dict:
    try:
        with open(BUDGET_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {"files": {}}
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read {BUDGET_PATH}: {exc}") from exc


def scan(registry, budget: dict) -> list[dict]:
    rows = []
    for rel, config in sorted(budget.get("files", {}).items()):
        path = os.path.join(ROOT, rel)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as exc:
            rows.append({"path": rel, "error": str(exc)})
            continue
        report = llm_ism_check.analyze(text, rel, registry, config.get("profile", "auto"), False)
        exempt = set(config.get("exempt_rules", ()))
        raw = report["findings"]
        counted = [f for f in raw if not (set(f["rule_ids"]) & exempt)]
        rows.append({
            "path": rel,
            "profile": report["document"]["profile"],
            "raw_findings": len(raw),
            "counted_findings": len(counted),
            "budget": config.get("max_findings", 0),
            "exempt_rules": sorted(exempt),
            "over": len(counted) > config.get("max_findings", 0),
            "rules": sorted({rid for f in counted for rid in f["rule_ids"]}),
            "note": config.get("note", ""),
        })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="self_scan.py",
        description="Scan this repository's prose against its own catalog and a committed budget.")
    ap.add_argument("--check", action="store_true", help="exit 1 when any file is over budget")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--update", action="store_true",
                    help="rewrite the budget file to the current counts (deliberate act; "
                         "explain the change in the commit)")
    args = ap.parse_args(argv)

    try:
        registry = load_registry()
        budget = load_budget()
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    rows = scan(registry, budget)

    if args.update:
        for row in rows:
            if "error" in row:
                continue
            budget["files"][row["path"]]["max_findings"] = row["counted_findings"]
        with open(BUDGET_PATH, "w", encoding="utf-8") as fh:
            json.dump(budget, fh, indent=2)
            fh.write("\n")
        print(f"budget updated in {os.path.relpath(BUDGET_PATH, ROOT)}")
        return 0

    if args.json:
        print(json.dumps({"files": rows}, indent=2))
    else:
        for row in rows:
            if "error" in row:
                print(f"  !! {row['path']}: {row['error']}")
                continue
            mark = "OVER" if row["over"] else "ok  "
            print(f"  {mark} {row['path']}: {row['counted_findings']} counted "
                  f"({row['raw_findings']} raw) / budget {row['budget']}"
                  + (f"  [{', '.join(row['rules'])}]" if row["rules"] else ""))
        over = [r for r in rows if r.get("over")]
        print(f"self scan: {len(rows)} file(s), {len(over)} over budget")

    return 1 if args.check and any(r.get("over") for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
