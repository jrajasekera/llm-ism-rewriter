"""The corpus measurement script and the manifest it reads.

Nothing here touches the network: fetches go through an injected fetcher, and
every document is synthetic text written for these tests.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from _support import ROOT, SCRIPTS
import corpus_measure as CM
from llm_ism_core import load_registry

MANIFEST = os.path.join(ROOT, "corpus", "manifest.json")
REQUIRED = ("id", "register", "authorship", "title", "author", "written", "source_type",
            "source_url", "licence", "source_sha256", "sha256", "word_count", "captured",
            "extract", "local_path", "notes")
AUTHORSHIP_VALUES = {"human-pre-llm", "human-post-llm", "generated", "unknown"}
BANNED = ("probability_ai", "human_score", "ai_score", "ai_only", "is_ai_generated",
          "authorship_score", "confidence_ai", "authorship")

PLAIN = ("Queues hold work until a worker is free. A worker takes one item, finishes it, "
         "and asks for the next. When the queue is empty the worker waits.\n")
RESIDUE = "Great question! Here is the answer you asked for.\n\n" + PLAIN


def entry(doc_id: str, text: str, register: str = "general-prose", **extra) -> dict:
    raw = text.encode("utf-8")
    doc = {"id": doc_id, "register": register, "source_url": f"https://example.invalid/{doc_id}",
           "source_sha256": CM.sha256_hex(raw), "sha256": CM.sha256_hex(raw),
           "word_count": None, "extract": {"format": "text"}}
    doc.update(extra)
    return doc


def no_network(url):  # pragma: no cover - a test fails if this is reached
    raise AssertionError(f"unexpected fetch of {url}")


class Checksums(unittest.TestCase):
    def test_matching_bytes_pass(self):
        doc = {"id": "x", "source_sha256": CM.sha256_hex(b"abc")}
        self.assertEqual(CM.verify(doc, "source", "source_sha256", b"abc", False),
                         CM.sha256_hex(b"abc"))

    def test_mismatch_raises(self):
        doc = {"id": "x", "source_sha256": CM.sha256_hex(b"abc")}
        with self.assertRaises(CM.IntegrityError):
            CM.verify(doc, "source", "source_sha256", b"abd", False)

    def test_missing_checksum_is_a_mismatch_unless_recording(self):
        doc = {"id": "x", "source_sha256": None}
        with self.assertRaises(CM.IntegrityError):
            CM.verify(doc, "source", "source_sha256", b"abc", False)
        CM.verify(doc, "source", "source_sha256", b"abc", True)
        self.assertEqual(doc["source_sha256"], CM.sha256_hex(b"abc"))

    def test_recording_never_overwrites(self):
        doc = {"id": "x", "source_sha256": CM.sha256_hex(b"old")}
        with self.assertRaises(CM.IntegrityError):
            CM.verify(doc, "source", "source_sha256", b"new", True)
        self.assertEqual(doc["source_sha256"], CM.sha256_hex(b"old"))


class Cache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_offline_without_cache_fails(self):
        with self.assertRaises(CM.FetchError):
            CM.load_source({"id": "a", "source_url": "https://example.invalid/a"},
                           self.cache, True, no_network)

    def test_fetches_once_then_reads_the_cache(self):
        calls = []

        def fetcher(url):
            calls.append(url)
            return b"bytes"

        doc = {"id": "a", "source_url": "https://example.invalid/a"}
        self.assertEqual(CM.load_source(doc, self.cache, False, fetcher), b"bytes")
        self.assertEqual(CM.load_source(doc, self.cache, True, no_network), b"bytes")
        self.assertEqual(len(calls), 1)

    def test_unsafe_id_is_rejected(self):
        with self.assertRaises(CM.RegistryError):
            CM.cache_file(self.cache, "../escape")


class Extraction(unittest.TestCase):
    def test_markers_cut_the_body(self):
        raw = b"HEADER\nSTART\nBody text here.\nEND\nlicence\n"
        self.assertEqual(CM.extract(raw, {"format": "text", "start_after": "START\n",
                                          "end_before": "END"}), "Body text here.\n")

    def test_missing_marker_fails(self):
        with self.assertRaises(CM.RegistryError):
            CM.extract(b"abc", {"format": "text", "start_after": "nope"})

    def test_trim_keeps_whole_blocks(self):
        text = "one two three\n\nfour five six\n\nseven eight nine\n"
        self.assertEqual(CM.trim_words(text, 7), "one two three\n\nfour five six\n")
        self.assertEqual(CM.trim_words(text, 1), "one two three\n")

    def test_trim_never_cuts_inside_a_fence(self):
        text = "intro words\n\n```\ncode a\n\ncode b\n```\n\ntail words\n"
        out = CM.trim_words(text, 4)
        self.assertEqual(out.count("```"), 2)

    def test_drop_lines_and_quote_indented(self):
        raw = b"Prose line.\n[Page 3]\n     Quoted by someone else.\nMore prose.\n"
        out = CM.extract(raw, {"format": "text", "drop_lines": [r"^\[Page \d+\]$"],
                               "quote_indented": 4})
        self.assertNotIn("[Page 3]", out)
        self.assertIn("> Quoted by someone else.", out)

    def test_gzip_bodies_are_decoded(self):
        self.assertEqual(CM.extract(gzip.compress(b"Hello.\n"), {"format": "text"}), "Hello.\n")

    def test_crlf_is_normalized(self):
        self.assertEqual(CM.extract(b"a\r\nb\r\n", {"format": "text"}), "a\nb\n")

    def test_html_keeps_structure(self):
        src = ("<html><head><title>t</title></head><body><nav>menu</nav><h2>Title</h2>"
               "<p>First &amp; second.</p><blockquote><p>Quoted.</p></blockquote>"
               "<pre>x = 1</pre><ul><li>item</li></ul><script>var a;</script></body></html>")
        out = CM.html_to_text(src)
        self.assertIn("## Title", out)
        self.assertIn("First & second.", out)
        self.assertIn("> Quoted.", out)
        self.assertIn("```\nx = 1\n```", out)
        self.assertIn("- item", out)
        for gone in ("menu", "var a", "<p>"):
            self.assertNotIn(gone, out)
        self.assertIn("x = 1", CM.html_to_text("<pre>x = 1</pre>", pre_as_code=False))
        self.assertNotIn("```", CM.html_to_text("<pre>x = 1</pre>", pre_as_code=False))

    def test_wikitext_reduces_to_prose(self):
        src = ("'''Widget''' ({{IPAc-en|w|i}}) is a [[tool]] for [[Gadget|gadgets]].<ref>cite</ref> "
               "It is {{convert|3|m|ft}} long.\n[[File:W.jpg|thumb|A [[widget]]]]\n"
               "{| class=wikitable\n|-\n| cell\n|}\n== History ==\n* first\n[[Category:Tools]]\n")
        out = CM.wikitext_to_markdown(src)
        self.assertIn("Widget is a tool for gadgets.", out)
        self.assertIn("It is 3 m long.", out)
        self.assertIn("## History", out)
        self.assertIn("- first", out)
        for gone in ("cite", "File:", "cell", "Category", "{{", "'''", "()"):
            self.assertNotIn(gone, out)


class Aggregation(unittest.TestCase):
    registry = load_registry()

    def result(self, doc_id, register, words, findings, candidates):
        return {"id": doc_id, "register": register, "words_scanned": words,
                "findings": sum(findings.values()), "findings_by_rule": findings,
                "candidates": sum(candidates.values()), "candidates_by_rule": candidates,
                "protected_candidates": 0, "examples": {}, "metrics": {}}

    def test_rates_are_per_register_and_per_thousand_words(self):
        results = [
            self.result("a", "essay-blog", 1000, {"RH.FALSE_CONTRAST": 2}, {"RH.FALSE_CONTRAST": 3}),
            self.result("b", "essay-blog", 3000, {}, {"RH.FALSE_CONTRAST": 1}),
            self.result("c", "legal-policy", 500, {"RH.FALSE_CONTRAST": 1}, {"RH.FALSE_CONTRAST": 1}),
        ]
        regs = CM.summarize(results, self.registry)
        essay = regs["essay-blog"]
        self.assertEqual((essay["documents"], essay["prose_words"]), (2, 4000))
        self.assertEqual(essay["docs_with_finding"], 1)
        self.assertEqual(essay["findings_per_1k_words"], 0.5)
        self.assertEqual(essay["candidates_per_1k_words"], 1.0)
        row = essay["rules"][0]
        self.assertEqual(row["rule_id"], "RH.FALSE_CONTRAST")
        self.assertEqual((row["docs_with_finding"], row["docs_with_candidate"]), (1, 2))
        self.assertEqual(regs["legal-policy"]["findings_per_1k_words"], 2.0)

    def test_quantiles_on_small_samples(self):
        self.assertEqual(CM.quantile([5.0], 0.9), 5.0)
        self.assertEqual(CM.quantile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5), 3.0)
        self.assertEqual(CM.quantile([3.0, 1.0, 2.0], 0.0), 1.0)

    def test_grouped_findings_count_every_rule(self):
        doc = {"id": "g", "register": "general-prose"}
        result = CM.measure_document(doc, RESIDUE, self.registry)
        self.assertGreaterEqual(result["findings"], 1)
        self.assertEqual(sum(result["findings_by_rule"].values()) >= result["findings"], True)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = os.path.join(self.tmp.name, "cache")
        os.makedirs(self.cache)
        docs = [entry("doc-plain", PLAIN), entry("doc-residue", RESIDUE),
                entry("doc-legal", PLAIN, register="legal-policy")]
        for d in docs:
            text = PLAIN if d["id"] != "doc-residue" else RESIDUE
            with open(os.path.join(self.cache, d["id"] + ".raw"), "wb") as fh:
                fh.write(text.encode("utf-8"))
            d["authorship"] = "human-pre-llm"
        self.manifest_path = os.path.join(self.tmp.name, "manifest.json")
        self.write({"schema_version": 1, "documents": docs})

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, manifest):
        with open(self.manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)

    def run_main(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = CM.main(["--manifest", self.manifest_path, "--cache", self.cache,
                            "--offline", *extra], fetcher=no_network)
        return code, out.getvalue(), err.getvalue()

    def test_json_report_per_register(self):
        code, out, _ = self.run_main("--format", "json")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(set(report["registers"]), {"general-prose", "legal-policy"})
        self.assertEqual(report["registers"]["general-prose"]["documents"], 2)
        self.assertGreaterEqual(report["registers"]["general-prose"]["findings"], 1)
        self.assertIn("never evidence of authorship", report["disclaimer"].lower())

    def test_output_carries_no_authorship_field_or_score(self):
        for fmt in ("json", "text", "markdown"):
            code, out, _ = self.run_main("--format", fmt)
            self.assertEqual(code, 0)
            low = out.lower().replace("never evidence of authorship", "")
            for token in BANNED:
                self.assertNotIn(token, low, f"{token} in {fmt} output")
            self.assertNotIn("human-pre-llm", low)

    def test_checksum_mismatch_fails_loudly_before_measuring(self):
        with open(os.path.join(self.cache, "doc-legal.raw"), "wb") as fh:
            fh.write(b"tampered\n")
        code, out, err = self.run_main("--format", "json")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("INTEGRITY FAILURE", err)
        self.assertIn("doc-legal", err)

    def test_offline_with_missing_cache_exits_2(self):
        os.remove(os.path.join(self.cache, "doc-plain.raw"))
        code, _, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn("--offline", err)

    def test_unknown_register_is_a_manifest_error(self):
        with open(self.manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        manifest["documents"][0]["register"] = "blog"
        self.write(manifest)
        self.assertEqual(self.run_main()[0], 3)


class ScriptBoundary(unittest.TestCase):
    def test_script_never_reads_the_authorship_field(self):
        with open(os.path.join(SCRIPTS, "corpus_measure.py"), encoding="utf-8") as fh:
            self.assertIsNone(re.search(r"[\"']authorship[\"']", fh.read()))


class ManifestIntegrity(unittest.TestCase):
    """The committed manifest: provenance fields, real profiles, pinned URLs."""

    @classmethod
    def setUpClass(cls):
        with open(MANIFEST, encoding="utf-8") as fh:
            cls.manifest = json.load(fh)
        cls.docs = cls.manifest["documents"]
        cls.registry = load_registry()

    def test_required_fields(self):
        for d in self.docs:
            missing = [k for k in REQUIRED if k not in d]
            self.assertEqual(missing, [], d.get("id"))

    def test_ids_are_unique_and_safe(self):
        ids = [d["id"] for d in self.docs]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertRegex(i, r"^[a-z0-9][a-z0-9._-]*$")

    def test_register_is_a_real_profile(self):
        profiles = set(self.registry.profile_names())
        for d in self.docs:
            self.assertIn(d["register"], profiles, d["id"])

    def test_checksums_are_sha256_hex(self):
        for d in self.docs:
            self.assertRegex(d["source_sha256"] or "", CM.SHA_RE, d["id"])
            self.assertRegex(d["sha256"] or "", CM.SHA_RE, d["id"])
            self.assertIsInstance(d["word_count"], int, d["id"])

    def test_no_local_path_for_third_party_text(self):
        for d in self.docs:
            if d["source_url"].startswith(("http://", "https://")):
                self.assertIsNone(d["local_path"], d["id"])

    def test_authorship_vocabulary_and_date(self):
        for d in self.docs:
            self.assertIn(d["authorship"], AUTHORSHIP_VALUES, d["id"])
            if d["authorship"] == "human-pre-llm":
                self.assertLess(d["written"], "2022-11", d["id"])
            self.assertRegex(d["captured"], r"^\d{4}-\d{2}-\d{2}$")

    def test_extract_recipe_is_known(self):
        for d in self.docs:
            self.assertIn(d["extract"].get("format"), CM.FORMATS, d["id"])

    def test_source_urls_are_pinned(self):
        """A branch name or a live page is not a reproducible source."""
        for d in self.docs:
            url = d["source_url"]
            self.assertTrue(url.startswith("https://"), d["id"])
            if url.startswith("https://raw.githubusercontent.com/"):
                ref = url.split("/")[5]
                self.assertNotIn(ref, ("main", "master", "trunk", "develop", "gh-pages"), d["id"])
                self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", ref) or re.search(r"\d", ref), d["id"])
            elif "web.archive.org" in url:
                self.assertRegex(url, r"/web/\d{14}id_/", d["id"])
            elif "wikipedia.org" in url:
                self.assertRegex(url, r"[?&]oldid=\d+", d["id"])
            elif "rfc-editor.org" in url:
                self.assertRegex(url, r"/rfc/rfc\d+\.txt$", d["id"])
            else:
                self.fail(f"{d['id']}: no pinning rule for {url}")

    def test_register_coverage(self):
        counts = {}
        for d in self.docs:
            counts[d["register"]] = counts.get(d["register"], 0) + 1
        self.assertGreaterEqual(sum(1 for n in counts.values() if n >= 10), 3, counts)


if __name__ == "__main__":
    unittest.main()
