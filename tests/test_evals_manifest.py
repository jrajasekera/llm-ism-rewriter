"""The agent-eval manifest is data nobody executes here, so it rots quietly.

These tests do not run an eval. They check that every case points at a real
input, that every assertion kind is declared with who evaluates it, and that a
quoted span an assertion depends on is really in the input.
"""
from __future__ import annotations

import json
import os
import unittest

from _support import ROOT
import llm_ism_check
import llm_ism_validate
from llm_ism_core import load_registry

EVALS = os.path.join(ROOT, "evals")
EVALUATORS = ("machine", "agent_judge", "human")
NARRATIVE_FIRST = 13
NARRATIVE_LAST = 38


def load():
    with open(os.path.join(EVALS, "evals.json"), encoding="utf-8") as fh:
        return json.load(fh)


def source(case) -> str:
    with open(os.path.join(EVALS, case["file"]), encoding="utf-8") as fh:
        return fh.read()


def number(case) -> int:
    return int(case["id"][1:3])


class Manifest(unittest.TestCase):
    def setUp(self):
        self.manifest = load()
        self.cases = self.manifest["cases"]
        self.kinds = {kind: evaluator for evaluator in EVALUATORS
                      for kind in self.manifest["assertion_kinds"][evaluator]}

    def test_ids_are_unique_and_inputs_exist(self):
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.cases:
            self.assertTrue(os.path.exists(os.path.join(EVALS, case["file"])), case["id"])

    def test_every_assertion_kind_is_declared_with_an_evaluator(self):
        declared = sum(len(self.manifest["assertion_kinds"][e]) for e in EVALUATORS)
        self.assertEqual(declared, len(self.kinds), "a kind is declared under two evaluators")
        for case in self.cases:
            for assertion in case["assertions"]:
                self.assertIn(assertion["kind"], self.kinds, case["id"])

    def test_quoted_spans_exist_in_the_input(self):
        for case in self.cases:
            if os.path.isdir(os.path.join(EVALS, case["file"])):
                continue
            text = source(case)
            for assertion in case["assertions"]:
                if assertion["kind"] not in ("substrings_preserved", "substring_removed",
                                             "removed_or_deferred", "number_with_unit_preserved"):
                    continue
                for value in assertion.get("values", [assertion.get("value")]):
                    self.assertIn(value, text, f"{case['id']}: {value!r} is not in {case['file']}")

    def test_reported_rules_exist(self):
        registry = load_registry()
        for case in self.cases:
            for assertion in case["assertions"]:
                rule = assertion.get("rule") or (assertion["kind"] == "reports_rule" and assertion["value"])
                if rule:
                    self.assertIn(rule, registry.by_id, case["id"])

    def test_baseline_is_the_released_version_before_this_one(self):
        self.assertEqual(self.manifest["version_under_test"], llm_ism_check.TOOL_VERSION)
        self.assertNotEqual(self.manifest["baseline"], self.manifest["version_under_test"])
        self.assertRegex(self.manifest["baseline_commit"], r"^[0-9a-f]{40}$")

    def test_checker_counts_are_not_a_global_objective(self):
        """A no-change case and a narrative edit both succeed with the checker's
        output unchanged, so a falling count can only be a per-case assertion."""
        rules = " ".join(self.manifest["objective_assertions"]["rules"])
        self.assertNotIn("has fewer P0/P1 findings than the source", rules)
        users = [c["id"] for c in self.cases
                 if any(a["kind"] == "findings_decrease" for a in c["assertions"])]
        self.assertEqual(users, ["E02-dense-product-copy"])


class NarrativeCases(unittest.TestCase):
    def setUp(self):
        self.cases = [c for c in load()["cases"] if NARRATIVE_FIRST <= number(c) <= NARRATIVE_LAST]
        self.registry = load_registry()

    def test_inputs_are_editable_prose(self):
        """A story supplied as a blockquote would exercise the protected path
        and nothing else. Only the epigraph case may contain one."""
        for case in self.cases:
            quoted = [line for line in source(case).splitlines() if line.startswith(">")]
            allowed = 1 if case["id"].startswith("E34") else 0
            self.assertEqual(len(quoted), allowed, case["id"])

    def test_the_checker_cannot_see_the_planted_problems(self):
        """If a regex could find them, the case would not test the narrative layer."""
        for case in self.cases:
            if case["id"].startswith(("E33", "E34")):
                continue
            report = llm_ism_check.analyze(source(case), case["file"], self.registry,
                                           "creative", False)
            self.assertEqual(report["findings"], [], case["id"])

    def test_no_change_cases_validate_against_themselves(self):
        for case in self.cases:
            text = source(case)
            results = llm_ism_validate.validate(text, text, "rewrite", self.registry,
                                                "a", "b", 0.6, "creative")
            self.assertFalse([r for r in results if r.level == "fail"], case["id"])

    def test_positive_cases_have_counterexamples(self):
        """At least two leave-alone cases for every case that plants a problem."""
        planted = [c for c in self.cases
                   if any(a["kind"] == "identifies_semantic_duplication" for a in c["assertions"])]
        untouched = [c for c in self.cases
                     if any(a["kind"] == "text_unchanged"
                            or (a["kind"] == "max_changed_paragraphs" and a["value"] == 0)
                            for a in c["assertions"])]
        self.assertGreaterEqual(len(untouched), 2 * len(planted),
                                f"{len(planted)} planted, {len(untouched)} leave-alone")

    def test_long_stories_are_long(self):
        for name in ("story-plain-long.md", "story-ornate-long.md", "story-clean-nonlinear.md"):
            with open(os.path.join(EVALS, "files", name), encoding="utf-8") as fh:
                self.assertGreater(len(fh.read().split()), 2000, name)


if __name__ == "__main__":
    unittest.main()
