"""CLI contracts: exit codes, stream discipline, and output formats."""
from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr

from _support import FIXTURES, ROOT
import llm_ism_check as C
import self_scan

SAMPLE = os.path.join(FIXTURES, "project", "alpha.md")
DIRTY = os.path.join(FIXTURES, "dirty.md")


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = C.main(argv)
    return code, out.getvalue(), err.getvalue()


class ExitCodes(unittest.TestCase):
    def test_findings_alone_do_not_fail(self):
        code, _, _ = run([DIRTY])
        self.assertEqual(code, 0)

    def test_fail_on_p0(self):
        self.assertEqual(run(["--fail-on", "P0", DIRTY])[0], 1)

    def test_fail_on_p0_passes_on_clean_input(self):
        self.assertEqual(run(["--fail-on", "P0", SAMPLE])[0], 0)

    def test_unreadable_input_exits_2(self):
        code, _, err = run(["/nonexistent/nope.md"])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_stdin_cannot_be_mixed_with_paths(self):
        code, _, err = run(["-", SAMPLE])
        self.assertEqual(code, 2)
        self.assertIn("cannot be combined", err)


class Streams(unittest.TestCase):
    def test_diagnostics_go_to_stderr_and_data_to_stdout(self):
        _, out, err = run(["/nonexistent/nope.md"])
        self.assertEqual(out, "")
        self.assertTrue(err)

    def test_json_stdout_is_parseable(self):
        _, out, _ = run(["--format", "json", DIRTY])
        payload = json.loads(out)
        self.assertEqual(payload["schema_version"], C.SCHEMA_VERSION)
        self.assertEqual(payload["tool_version"], C.TOOL_VERSION)


class Formats(unittest.TestCase):
    def test_json_has_locations_and_rule_ids(self):
        _, out, _ = run(["--format", "json", DIRTY])
        finding = json.loads(out)["findings"][0]
        for key in ("rule_ids", "tier", "edit_priority", "evidence_strength",
                    "location", "excerpt", "reason", "suggested_action"):
            self.assertIn(key, finding)
        for key in ("start_line", "start_column", "end_line", "end_column"):
            self.assertIn(key, finding["location"])

    def test_sarif_shape(self):
        _, out, _ = run(["--format", "sarif", DIRTY])
        sarif = json.loads(out)
        self.assertEqual(sarif["version"], "2.1.0")
        run_ = sarif["runs"][0]
        self.assertTrue(run_["tool"]["driver"]["rules"])
        self.assertTrue(run_["results"])
        region = run_["results"][0]["locations"][0]["physicalLocation"]["region"]
        self.assertGreaterEqual(region["startLine"], 1)

    def test_candidates_level_shows_more_than_findings(self):
        _, findings, _ = run(["--level", "findings", DIRTY])
        _, candidates, _ = run(["--level", "candidates", DIRTY])
        self.assertNotEqual(findings, candidates)

    def test_max_findings_truncates_and_says_so(self):
        _, out, _ = run(["--format", "json", "--max-findings", "1", DIRTY])
        payload = json.loads(out)
        self.assertEqual(len(payload["findings"]), 1)
        self.assertIn("truncated", payload["summary"])

    def test_output_to_a_file(self):
        target = os.path.join(FIXTURES, "_cli_out.json")
        try:
            code, out, _ = run(["--format", "json", "--output", target, DIRTY])
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            with open(target, encoding="utf-8") as fh:
                self.assertTrue(json.load(fh)["findings"])
        finally:
            if os.path.exists(target):
                os.remove(target)


class Help(unittest.TestCase):
    def test_help_is_non_interactive_and_documents_the_flags(self):
        out = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(out):
            C.main(["--help"])
        text = out.getvalue()
        for flag in ("--profile", "--format", "--level", "--include-protected",
                     "--fail-on", "--max-findings", "--output"):
            self.assertIn(flag, text)


class SelfScan(unittest.TestCase):
    def test_repository_prose_is_within_budget(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = self_scan.main(["--check"])
        self.assertEqual(code, 0, out.getvalue())

    def test_budget_covers_the_shipped_prose(self):
        budget = self_scan.load_budget()["files"]
        for path in ("README.md", "SKILL.md", "references/patterns.md",
                     "references/contexts.md", "references/examples.md"):
            self.assertIn(path, budget)
            self.assertTrue(os.path.exists(os.path.join(ROOT, path)))


if __name__ == "__main__":
    unittest.main()
