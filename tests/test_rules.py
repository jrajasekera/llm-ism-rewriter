"""Fixture-driven rule behavior, plus the coverage contract from detector-map.md."""
from __future__ import annotations

import unittest
from collections import defaultdict

from _support import case_text, fixture
import llm_ism_check
from llm_ism_core import load_registry

REGISTRY = load_registry()
CASES = fixture("cases.json")["cases"]
EXECUTABLE = {"regex", "lexicon_cluster", "repetition", "metric"}
# Evaluated only by scripts/llm_ism_project_check.py; covered by test_project_check.py.
PROJECT_ONLY = {"ST.CROSS_FILE_TEMPLATE"}


def rules_fired(case: dict) -> set[str]:
    report = llm_ism_check.analyze(case_text(case), case["id"], REGISTRY,
                                   case.get("profile", "auto"),
                                   case.get("include_protected", False))
    return {rid for f in report["findings"] for rid in f["rule_ids"]}


class RuleFixtures(unittest.TestCase):
    pass


def _make(case):
    def test(self):
        fired = rules_fired(case)
        for rid in case.get("expect_present", ()):
            self.assertIn(rid, fired, f"{case['id']}: expected {rid}; fired {sorted(fired)}")
        for rid in case.get("expect_absent", ()):
            self.assertNotIn(rid, fired, f"{case['id']}: {rid} should not fire")
    test.__doc__ = case.get("note") or case["id"]
    return test


for _case in CASES:
    setattr(RuleFixtures, "test_" + _case["id"].lower().replace("-", "_"), _make(_case))


class CoverageContract(unittest.TestCase):
    """Every executable rule needs a positive and two negative fixtures."""

    def setUp(self):
        self.positive = defaultdict(int)
        self.negative = defaultdict(int)
        for case in CASES:
            for rid in case.get("expect_present", ()):
                self.positive[rid] += 1
            for rid in case.get("expect_absent", ()):
                self.negative[rid] += 1

    def test_every_executable_rule_has_a_positive_fixture(self):
        for rule in REGISTRY.rules:
            if rule["detector"] in EXECUTABLE and rule["id"] not in PROJECT_ONLY:
                self.assertGreaterEqual(self.positive[rule["id"]], 1,
                                        f"{rule['id']} has no positive fixture")

    def test_every_executable_rule_has_two_negative_fixtures(self):
        for rule in REGISTRY.rules:
            if rule["detector"] in EXECUTABLE and rule["id"] not in PROJECT_ONLY:
                self.assertGreaterEqual(self.negative[rule["id"]], 2,
                                        f"{rule['id']} has fewer than two negative fixtures")

    def test_fixtures_reference_real_rules(self):
        for case in CASES:
            for rid in list(case.get("expect_present", ())) + list(case.get("expect_absent", ())):
                self.assertIn(rid, REGISTRY.by_id, f"{case['id']} names unknown rule {rid}")


class Aggregation(unittest.TestCase):
    def test_candidates_and_findings_are_separate(self):
        text = "The cache warms on boot. Note that eviction is lazy."
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        self.assertGreater(report["summary"]["candidates"], 0)
        self.assertEqual(report["summary"]["findings"], 0)
        self.assertGreater(report["summary"]["candidates_suppressed"], 0)

    def test_suppression_is_explained(self):
        text = "The cache warms on boot. Note that eviction is lazy."
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        self.assertTrue(report["suppression_notes"])

    def test_overlapping_rules_become_one_finding(self):
        text = ("The release marks a pivotal moment in the ever-evolving landscape, "
                "serving as a testament to the team's meticulous and seamless work.")
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        spans = [f for f in report["findings"] if f["location"]["start_line"] == 1]
        multi = [f for f in spans if len(f["rule_ids"]) > 1]
        self.assertTrue(multi, "overlapping matches on one span should group")

    def test_protected_matches_are_hidden_by_default_and_shown_on_request(self):
        text = "Intro.\n\n```\nGreat question!\n```\n"
        hidden = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        shown = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", True)
        self.assertEqual(hidden["summary"]["findings"], 0)
        self.assertTrue(any(f["protected"] for f in shown["findings"]))

    def test_structural_findings_show_their_arithmetic(self):
        text = ("Caching—when done right—cuts latency, but it adds complexity, and complexity "
                "has a cost the on-call rota eventually pays for in pages and confusion.\n\n") * 5
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        dash = [f for f in report["findings"] if "ST.DASH_DENSITY" in f["rule_ids"]]
        self.assertTrue(dash)
        evidence = dash[0]["evidence"]
        for key in ("value", "threshold", "comparison", "threshold_status", "scope"):
            self.assertIn(key, evidence)
        self.assertEqual(evidence["threshold_status"], "provisional")

    def test_density_label_reports_its_counts(self):
        report = llm_ism_check.analyze("Great question! In conclusion, we shipped.",
                                       "t.md", REGISTRY, "general-prose", False)
        self.assertIn("scanned prose words", report["summary"]["density_evidence"])

    def test_curly_match_reports_the_source_characters_and_columns(self):
        text = "Fine.\n\nWe ship it. It\u2019s not a bug \u2014 it\u2019s a feature."
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        hit = [c for c in report["candidates"] if c["rule_id"] == "RH.FALSE_CONTRAST"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["excerpt"], "It\u2019s not a bug \u2014 it\u2019s")
        self.assertEqual((hit[0]["start_line"], hit[0]["start_column"]), (3, 13))

    def test_cross_sentence_contrast_stays_a_judgment_call(self):
        text = "The 2019 postmortem argued the outage was not about load. It was about a stale cache."
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        hit = [f for f in report["findings"] if "RH.FALSE_CONTRAST" in f["rule_ids"]]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["action"], "review_in_context")
        self.assertEqual(hit[0]["evidence_strength"], "medium")
        self.assertEqual((hit[0]["location"]["start_line"], hit[0]["location"]["end_line"]), (1, 1))

    def test_one_sentence_contrast_is_one_candidate(self):
        text = "This isn't about productivity; it's about autonomy."
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "general-prose", False)
        self.assertEqual(sum(c["rule_id"] == "RH.FALSE_CONTRAST" for c in report["candidates"]), 1)

    def test_clarity_findings_do_not_raise_density(self):
        text = "In order to rebuild the index, run the migration. " * 3
        report = llm_ism_check.analyze(text, "t.md", REGISTRY, "technical-docs", False)
        self.assertTrue(any(f["tier"] == "clarity" for f in report["findings"]))
        self.assertEqual(report["summary"]["density"], "none")


if __name__ == "__main__":
    unittest.main()
