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


FICTION = ("Mara closed the shop at six and walked to the harbour. Additionally, the "
           "tide was out. Furthermore, the boats sat on the mud. Moreover, nobody "
           "was about. She counted the moorings twice and went home.")


def dialogue_story(lines: int = 5) -> str:
    """Long enough, with enough quoted paragraph openers, to auto-detect as creative."""
    filler = " ".join(["The lamp burned low and the wind kept on at the shutters."] * 30)
    talk = "\n\n".join(f'"Line {n}," she said, and turned the page.' for n in range(lines))
    return filler + "\n\n" + talk + "\n"


class ProfileConsistency(unittest.TestCase):
    """The residual check must judge both versions under one profile."""

    def residual(self, before, after, profile=None):
        args = (before, after, "rewrite", REGISTRY, "a", "b", 0.6)
        results = V.validate(*args) if profile is None else V.validate(*args, profile=profile)
        return {r.check: r for r in results}

    def test_default_invocation_is_unchanged(self):
        res = self.residual(FICTION, FICTION)
        self.assertEqual(res["residual findings"].level, "pass")
        self.assertIn("general-prose", res["context profile"].message)

    def test_explicit_profile_reaches_both_residual_checks(self):
        """Fiction with no sustained dialogue falls back to general-prose under
        auto, where the stock transitions count. Under creative they are skipped
        on both sides, so the fourth one is not a residual failure there."""
        after = FICTION.replace("She counted", "Additionally, she counted")
        auto = self.residual(FICTION, after)
        creative = self.residual(FICTION, after, profile="creative")
        self.assertIn("(explicit)", creative["context profile"].message)
        self.assertEqual(auto["residual findings"].level, "fail")
        self.assertIn("3→4", auto["residual findings"].message)
        self.assertEqual(creative["residual findings"].level, "pass")
        self.assertIn("0→0", creative["residual findings"].message)

    def test_auto_is_resolved_from_the_original_and_reused(self):
        """A revision that loses the dialogue cue must not be re-detected as
        general-prose and judged under stricter rules than its source."""
        before = dialogue_story()
        after = before.replace('"Line 3," she said', 'Line 3, she said') \
                      .replace('"Line 4," she said', 'Line 4, she said') \
            + "\nAdditionally, it rained. Furthermore, it was cold. Moreover, it was late.\n"
        self.assertEqual(V.resolve_profile(before, REGISTRY), ("creative", "auto"))
        self.assertEqual(V.resolve_profile(after, REGISTRY)[0], "general-prose")
        res = self.residual(before, after)
        self.assertIn("creative (auto)", res["context profile"].message)
        self.assertEqual(res["residual findings"].level, "pass")
        self.assertNotIn("new patterns", res)

    def test_unknown_profile_is_a_registry_error(self):
        from llm_ism_core import RegistryError
        with self.assertRaises(RegistryError):
            V.resolve_profile(FICTION, REGISTRY, "screenplay")


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


class ClaimQualifications(unittest.TestCase):
    def check_pair(self, before, after):
        results = V.validate(before, after, "rewrite", REGISTRY, "a", "b", 0.6)
        return [r for r in results if r.check == "claim qualifications"]

    def test_losses_and_additions_warn_without_changing_exit_policy(self):
        pairs = [
            ("The shortest queue is selected.", "The short queue is selected."),
            ("The nodes commit simultaneously.", "The nodes commit."),
            ("The cache refreshes only if the client asks.",
             "Only the cache refreshes if the client asks."),
            ("It holds at least five entries.", "It holds at most five entries."),
        ]
        for before, after in pairs:
            for source, revision in ((before, after), (after, before)):
                with self.subTest(source=source, revision=revision):
                    results = self.check_pair(source, revision)
                    self.assertEqual([r.level for r in results], ["warn"])

    def test_soft_wrapping_and_case_do_not_change_a_condition(self):
        result = self.check_pair("Only\nif the flag is set, proceed.",
                                 "Proceed only if the flag is set.")
        self.assertEqual([r.level for r in result], ["pass"])

    def test_supported_simultaneity_paraphrase_keeps_the_marker(self):
        result = self.check_pair("The nodes commit simultaneously.",
                                 "The nodes commit at the same time.")
        self.assertEqual([r.level for r in result], ["pass"])

    def test_different_superlatives_do_not_cancel(self):
        result = self.check_pair("The shortest queue wins.", "The longest queue wins.")
        self.assertEqual([r.level for r in result], ["warn"])
        self.assertIn("shortest=1→0", result[0].message)

    def test_ordinary_words_do_not_match_by_suffix_or_substring(self):
        self.assertEqual(V.qualification_counts(
            "The latest_record contains a forest inventory. The festival starts soon."), {})

    def test_protected_material_does_not_supply_claim_markers(self):
        text = ('---\ntitle: shortest\n---\n\n> "only if" — the manual\n\n'
                '```text\nsimultaneously\n```\n\n'
                '| term | meaning |\n|---|---|\n| fastest | rank |\n\n'
                'Use `shortest` and [docs](https://example.com/fastest).\n')
        self.assertEqual(V.qualification_counts(text), {})

    def test_markers_do_not_join_across_paragraphs_or_sentences(self):
        for text in ("It is the only\n\nIf needed, proceed.",
                     "It is the only. If needed, proceed.",
                     "Only `a long example` if asked."):
            with self.subTest(text=text):
                self.assertNotIn("only if", V.qualification_counts(text))

    def test_same_marker_can_still_modify_a_different_claim(self):
        # Document counts cannot establish attachment. This is a documented
        # blind spot for the manual claim-by-claim review, not a passing edit.
        result = self.check_pair(
            "The shortest queue wins. The oldest job waits.",
            "The oldest queue wins. The shortest job waits.")
        self.assertEqual([r.level for r in result], ["pass"])
        self.assertIn("attachment", result[0].message)


class CLI(unittest.TestCase):
    def test_missing_file_exits_2(self):
        self.assertEqual(V.main(["/nonexistent/a.md", "/nonexistent/b.md"]), 2)

    def run_json(self, before, after, *flags):
        import contextlib, io, json, os, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name, text in (("before.md", before), ("after.md", after)):
                paths.append(os.path.join(tmp, name))
                with open(paths[-1], "w", encoding="utf-8") as fh:
                    fh.write(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = V.main(["--json", *flags, *paths])
        return code, json.loads(out.getvalue())

    def test_json_records_the_selected_profile(self):
        code, report = self.run_json(FICTION, FICTION, "--profile", "creative")
        self.assertEqual(code, 0)
        self.assertEqual(report["profile"], "creative")
        self.assertEqual(report["profile_source"], "explicit")
        code, report = self.run_json(FICTION, FICTION)
        self.assertEqual((report["profile"], report["profile_source"]), ("general-prose", "default"))

    def test_preservation_failure_still_exits_1_under_a_profile(self):
        code, report = self.run_json("She did not go.", "She went.", "--profile", "creative")
        self.assertEqual(code, 1)
        self.assertFalse(report["passed"])

    def test_qualification_warning_is_visible_in_json_and_nonfatal(self):
        code, report = self.run_json("The nodes commit simultaneously.",
                                     "The nodes commit.")
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        self.assertTrue(any(r["check"] == "claim qualifications" and r["level"] == "warn"
                            for r in report["results"]))


if __name__ == "__main__":
    unittest.main()
