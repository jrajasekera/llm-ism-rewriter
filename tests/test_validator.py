"""Preservation validator: known drift must fail, legitimate rewrites must pass."""
from __future__ import annotations

import unittest

from _support import fixture
import llm_ism_validate as V
from llm_ism_core import load_registry

REGISTRY = load_registry()
PAIRS = fixture("rewrite_pairs.json")["pairs"]


def run(pair):
    return V.validate(pair["before"], pair["after"], pair["mode"], REGISTRY,
                      "before.md", "after.md", 0.6)


class RewritePairs(unittest.TestCase):
    pass


def _make(pair):
    def test(self):
        results = run(pair)
        failed = {r.check for r in results if r.level == "fail"}
        warned = {r.check for r in results if r.level == "warn"}
        if pair["expect_pass"]:
            self.assertEqual(failed, set(), f"{pair['id']}: unexpected failures {sorted(failed)}")
        else:
            self.assertTrue(failed, f"{pair['id']}: expected a failure")
        for check in pair.get("expect_fail_checks", ()):
            self.assertIn(check, failed, f"{pair['id']}: {check} should FAIL; got {sorted(failed)}")
        for check in pair.get("expect_warn_checks", ()):
            self.assertIn(check, warned, f"{pair['id']}: {check} should WARN; got {sorted(warned)}")
    test.__doc__ = pair["id"]
    return test


for _pair in PAIRS:
    setattr(RewritePairs, "test_" + _pair["id"].lower().replace("-", "_"), _make(_pair))


class ModePolicy(unittest.TestCase):
    def test_heading_rename_is_fatal_in_edit_but_a_warning_in_rewrite(self):
        before, after = "## Retry budgets\n\nThe cap is five.", "## Retries\n\nThe cap is five."
        edit = {r.check: r.level for r in V.validate(before, after, "edit", REGISTRY, "a", "b", 0.6)}
        rewrite = {r.check: r.level for r in V.validate(before, after, "rewrite", REGISTRY, "a", "b", 0.6)}
        self.assertEqual(edit["headings"], "fail")
        self.assertEqual(rewrite["headings"], "warn")

    def test_restructure_allows_heading_changes(self):
        before, after = "## Retry budgets\n\nThe cap is five.", "## Retries\n\nThe cap is five."
        res = {r.check: r.level for r in V.validate(before, after, "restructure", REGISTRY, "a", "b", 0.6)}
        self.assertEqual(res["headings"], "info")

    def test_untouched_prose_is_reported(self):
        before = "The cap is five.\n\nThe queue drains in order."
        after = "The cap is five.\n\nThe queue drains in the order received."
        res = [r for r in V.validate(before, after, "edit", REGISTRY, "a", "b", 0.6)
               if r.check == "untouched prose"]
        self.assertTrue(res)
        self.assertIn("1/2", res[0].message)


class AnchorExtraction(unittest.TestCase):
    def test_contractions_are_expanded_before_comparison(self):
        self.assertEqual(V.expand("it doesn't and can't"), "it does not and can not")

    def test_number_with_unit(self):
        found = {m.strip() for m in V.NUM_UNIT_RE.findall("under 100 ms and 4 GB, about 12%")}
        self.assertEqual(found, {"100 ms", "4 GB", "12%"})

    def test_version_keeps_the_plus(self):
        self.assertIn("3.11+", V.VERSION_RE.findall("Requires Python 3.11+."))

    def test_protected_spans_are_extracted_by_kind(self):
        spans = V.protected_spans("---\na: 1\n---\n\ntext\n\n```\ncode\n```\n")
        self.assertEqual(len(spans["frontmatter"]), 1)
        self.assertEqual(len(spans["code"]), 1)


class CLI(unittest.TestCase):
    def test_missing_file_exits_2(self):
        self.assertEqual(V.main(["/nonexistent/a.md", "/nonexistent/b.md"]), 2)


if __name__ == "__main__":
    unittest.main()
