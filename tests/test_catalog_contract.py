"""The registry, the prose catalog, and the code must not drift apart."""
from __future__ import annotations

import json
import os
import unittest

from _support import ROOT
import build_catalog
import llm_ism_check
from llm_ism_core import load_registry


class CatalogContract(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry()

    def test_contract_holds(self):
        problems = build_catalog.check(self.registry)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_rule_index_is_current(self):
        with open(os.path.join(ROOT, "references", "patterns.md"), encoding="utf-8") as fh:
            current = build_catalog.extract_index(fh.read())
        self.assertIsNotNone(current)
        self.assertEqual(current.strip(), build_catalog.render_index(self.registry).strip(),
                         "run scripts/build_catalog.py --write")

    def test_rule_ids_are_stable_and_namespaced(self):
        for rule in self.registry.rules:
            self.assertRegex(rule["id"], r"^(FP|LX|RH|ST|CL)\.[A-Z0-9_]+$")

    def test_tier_vocabulary_is_shared(self):
        tiers = set(self.registry.raw["tiers"])
        self.assertEqual(tiers, {"fingerprint", "cliche", "structural", "clarity"})
        for path in ("SKILL.md", "references/patterns.md", "references/detector-map.md"):
            with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
                text = fh.read().lower()
            for tier in tiers:
                self.assertIn(tier, text, f"{path} never names the {tier!r} tier")

    def test_no_authorship_fields_anywhere(self):
        """The one thing this project must never emit."""
        banned = ("probability_ai", "human_score", "ai_score", "ai_only",
                  "is_ai_generated", "authorship_score", "confidence_ai")
        report = llm_ism_check.analyze("A short document about queues.", "t.md",
                                       self.registry, "general-prose", False)
        blob = json.dumps(report).lower()
        for token in banned:
            self.assertNotIn(token, blob)
        with open(os.path.join(ROOT, "references", "rules.json"), encoding="utf-8") as fh:
            registry_blob = fh.read().lower()
        for token in banned:
            self.assertNotIn(token, registry_blob)

    def test_report_carries_the_disclaimer(self):
        report = llm_ism_check.analyze("Great question! Here is the answer.", "t.md",
                                       self.registry, "general-prose", False)
        self.assertIn("never evidence of authorship", report["disclaimer"].lower())
        self.assertIn("Never evidence of authorship",
                      llm_ism_check.render_text(report, "findings"))

    def test_versions_are_synchronized(self):
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as fh:
            skill = fh.read()
        self.assertIn(f'version: "{llm_ism_check.TOOL_VERSION}"', skill)
        self.assertEqual(self.registry.raw["registry_version"], llm_ism_check.TOOL_VERSION)

    def test_judgment_rules_have_no_detector(self):
        for rule in self.registry.rules:
            if rule["detector"] == "llm_judgment":
                self.assertNotIn("patterns", rule, rule["id"])
                self.assertIn("judgment_prompt", rule, rule["id"])

    def test_every_metric_rule_is_implemented(self):
        known = llm_ism_check.IMPLEMENTED_METRICS | build_catalog.PROJECT_METRICS
        for rule in self.registry.rules:
            if rule["detector"] == "metric":
                self.assertIn(rule["metric"], known, rule["id"])

    def test_scripts_import_only_the_standard_library(self):
        """Zero runtime dependencies is a portability promise, not a preference."""
        import ast
        allowed = {"__future__", "argparse", "ast", "collections", "contextlib",
                   "dataclasses", "io", "json", "math", "os", "re", "statistics",
                   "sys", "typing", "unicodedata"}
        scripts = os.path.join(ROOT, "scripts")
        local = {f[:-3] for f in os.listdir(scripts) if f.endswith(".py")}
        bad = []
        for name in sorted(os.listdir(scripts)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(scripts, name), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    mods = [(node.module or "").split(".")[0]]
                else:
                    continue
                bad += [f"{name}: {m}" for m in mods if m and m not in allowed | local]
        self.assertEqual(bad, [], "\n".join(bad))

    def test_skill_md_stays_within_the_disclosure_budget(self):
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as fh:
            skill = fh.read()
        self.assertLess(len(skill.splitlines()), 500)
        self.assertLess(len(skill), 20_000, "SKILL.md is the only always-loaded file")

    def test_every_reference_the_skill_names_exists(self):
        import re as _re
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as fh:
            skill = fh.read()
        targets = set(_re.findall(r"`((?:references|scripts)/[\w./-]+)`", skill))
        self.assertTrue(targets)
        for target in targets:
            self.assertTrue(os.path.exists(os.path.join(ROOT, target)), target)

    def test_profiles_cover_every_family(self):
        families = {r["family"] for r in self.registry.rules}
        for name in self.registry.profile_names():
            self.assertEqual(set(self.registry.profiles[name]["families"]), families, name)


if __name__ == "__main__":
    unittest.main()
