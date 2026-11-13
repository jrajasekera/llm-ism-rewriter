"""Cross-file repetition: ST.CROSS_FILE_TEMPLATE's only implementation."""
from __future__ import annotations

import os
import unittest

from _support import FIXTURES
import llm_ism_project_check as P

PROJECT = os.path.join(FIXTURES, "project")


def report(min_files=3, ngram=5):
    paths = P.collect([PROJECT], (".md",), [])
    files = {p: P.document_features(open(p, encoding="utf-8").read()) for p in paths}
    return P.analyze(files, ngram, min_files)


class Repetition(unittest.TestCase):
    def test_finds_the_shared_opener(self):
        rows = report()["repeated_phrases"]
        phrases = {r["phrase"] for r in rows}
        self.assertTrue(any("getting started with this" in p for p in phrases), sorted(phrases)[:5])

    def test_reports_which_files_share_it(self):
        rows = [r for r in report()["repeated_phrases"] if r["file_count"] >= 3]
        self.assertTrue(rows)
        self.assertEqual(rows[0]["file_count"], 3)

    def test_the_unique_document_is_not_implicated(self):
        for row in report()["repeated_phrases"]:
            self.assertNotIn("unique.md", " ".join(row["files"]))

    def test_scaffolding_is_excluded(self):
        self.assertNotIn("table of contents", {r["phrase"] for r in report(min_files=2)["repeated_phrases"]})

    def test_apostrophe_style_does_not_split_a_template(self):
        files = {f"{i}.md": P.document_features(text) for i, text in enumerate((
            "It's worth checking the retry budget before every release.",
            "It\u2019s worth checking the retry budget before every release.",
        ))}
        phrases = {r["phrase"] for r in P.analyze(files, 5, 2)["repeated_phrases"]}
        self.assertIn("it's worth checking the retry", phrases)
        self.assertEqual(len({f["opening"] for f in files.values()}), 1)

    def test_stopword_only_phrases_are_excluded(self):
        for row in report(min_files=2)["repeated_phrases"]:
            self.assertFalse(all(t in P.STOPWORDS for t in row["phrase"].split()))

    def test_report_says_repetition_not_authorship(self):
        text = P.render(report())
        self.assertIn("Repetition, not authorship", text)
        self.assertNotIn("generated", text.lower())

    def test_labeled_bullet_skeletons_are_listed(self):
        files = {"x.md": P.document_features(
            "## F\n\n- **A:** one\n- **B:** two\n- **C:** three\n- **D:** four\n")}
        self.assertTrue(P.analyze(files, 5, 2)["labeled_bullet_skeletons"])


class CLI(unittest.TestCase):
    def test_rejects_a_bad_ngram(self):
        self.assertEqual(P.main(["--ngram", "2", PROJECT]), 2)

    def test_rejects_min_files_below_two(self):
        self.assertEqual(P.main(["--min-files", "1", PROJECT]), 2)

    def test_missing_path_exits_2(self):
        self.assertEqual(P.main(["/nonexistent/dir-that-is-not-there.md"]), 2)


if __name__ == "__main__":
    unittest.main()
