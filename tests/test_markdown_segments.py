"""Parser edge cases. Ambiguous structure must fail closed, not rewrite on a guess."""
from __future__ import annotations

import unittest

from _support import ROOT  # noqa: F401  (path wiring)
from llm_ism_core import (
    mask_inline, parse_markdown, split_sentences, line_col, line_offsets, words,
)


def kinds(text):
    return [s.kind for s in parse_markdown(text)]


class Fences(unittest.TestCase):
    def test_backtick_fence(self):
        self.assertEqual(kinds("a\n\n```\ncode\n```\n\nb"), ["paragraph", "code", "paragraph"])

    def test_tilde_fence(self):
        self.assertEqual(kinds("a\n\n~~~\ncode\n~~~\n\nb"), ["paragraph", "code", "paragraph"])

    def test_longer_fence_contains_shorter(self):
        text = "````\n```\nstill code\n```\n````\n\nafter"
        segs = parse_markdown(text)
        self.assertEqual([s.kind for s in segs], ["code", "paragraph"])
        self.assertIn("still code", segs[0].text)

    def test_tilde_fence_not_closed_by_backticks(self):
        segs = parse_markdown("~~~\n```\ncode\n~~~\n\nafter")
        self.assertEqual([s.kind for s in segs], ["code", "paragraph"])

    def test_unclosed_fence_is_protected_and_warns(self):
        segs = parse_markdown("intro\n\n```\nnever closed\n")
        code = [s for s in segs if s.kind == "code"][0]
        self.assertTrue(code.protected)
        self.assertTrue(code.warnings)


class Frontmatter(unittest.TestCase):
    def test_yaml_frontmatter(self):
        segs = parse_markdown("---\ntitle: x\n---\n\nbody")
        self.assertEqual(segs[0].kind, "frontmatter")
        self.assertTrue(segs[0].protected)

    def test_toml_frontmatter(self):
        self.assertEqual(parse_markdown("+++\ntitle = 'x'\n+++\n\nbody")[0].kind, "frontmatter")

    def test_thematic_break_is_not_frontmatter(self):
        segs = parse_markdown("---\n\nbody")
        self.assertNotEqual(segs[0].kind, "frontmatter")

    def test_frontmatter_only_at_the_top(self):
        segs = parse_markdown("body\n\n---\ntitle: x\n---\n")
        self.assertNotIn("frontmatter", [s.kind for s in segs])


class Headings(unittest.TestCase):
    def test_atx(self):
        seg = parse_markdown("## Why retries\n\nbody")[0]
        self.assertEqual(seg.kind, "heading")
        self.assertEqual(seg.heading_level, 2)

    def test_setext(self):
        seg = parse_markdown("Title\n=====\n\nbody")[0]
        self.assertEqual((seg.kind, seg.heading_level), ("heading", 1))

    def test_headings_are_scanned_not_skipped(self):
        """Regression: headings used to be dropped before matching."""
        segs = parse_markdown("## In today's fast-paced world\n\nbody")
        self.assertFalse(segs[0].protected)

    def test_section_path_tracks_ancestry(self):
        segs = parse_markdown("# A\n\n## B\n\ntext")
        para = [s for s in segs if s.kind == "paragraph"][0]
        self.assertEqual(para.section_path, ("A", "B"))


class Quotes(unittest.TestCase):
    def test_attributed_quote_is_protected(self):
        seg = parse_markdown('> "Logs lie." — an SRE\n')[0]
        self.assertEqual(seg.kind, "quote")
        self.assertTrue(seg.protected)

    def test_admonition_is_a_scannable_callout(self):
        seg = parse_markdown("> [!NOTE]\n> Eviction is lazy.\n")[0]
        self.assertEqual(seg.kind, "callout")
        self.assertFalse(seg.protected)

    def test_unattributed_callout_is_scanned(self):
        seg = parse_markdown("> In conclusion, the queue drains in order.\n")[0]
        self.assertFalse(seg.protected)


class Tables(unittest.TestCase):
    def test_leading_pipe_table(self):
        self.assertIn("table", kinds("| a | b |\n|---|---|\n| 1 | 2 |\n"))

    def test_table_without_leading_pipe(self):
        self.assertIn("table", kinds("a | b\n---|---\n1 | 2\n"))

    def test_table_is_protected(self):
        table = [s for s in parse_markdown("| a | b |\n|---|---|\n| 1 | 2 |\n") if s.kind == "table"][0]
        self.assertTrue(table.protected)


class Lists(unittest.TestCase):
    def test_bullets_and_ordered(self):
        self.assertEqual(kinds("- one\n- two\n"), ["list_item", "list_item"])
        self.assertEqual(kinds("1. one\n2. two\n"), ["list_item", "list_item"])

    def test_nested_depth(self):
        segs = parse_markdown("- one\n  - nested\n")
        self.assertEqual(segs[0].list_depth, 0)


class Masking(unittest.TestCase):
    def test_masking_preserves_offsets(self):
        text = "run `--delve` now"
        self.assertEqual(len(mask_inline(text)), len(text))
        self.assertNotIn("delve", mask_inline(text))

    def test_url_is_masked_but_link_text_survives(self):
        masked = mask_inline("see [the pivotal report](https://example.com/delve)")
        self.assertNotIn("example.com", masked)

    def test_bare_url_masked(self):
        self.assertNotIn("delve", mask_inline("https://example.com/delve/landscape"))

    def test_posix_and_windows_paths_masked(self):
        self.assertNotIn("delve", mask_inline("open /var/log/delve/app.log"))
        self.assertNotIn("delve", mask_inline(r"open C:\logs\delve\app.log"))

    def test_newlines_survive_masking(self):
        text = "`a`\n`b`"
        self.assertEqual(mask_inline(text).count("\n"), 1)


class Sentences(unittest.TestCase):
    def test_abbreviations_do_not_split(self):
        self.assertEqual(len(split_sentences("Use e.g. this form. Then stop.")), 2)

    def test_decimals_do_not_split(self):
        self.assertEqual(len(split_sentences("It costs 3.50 today. Tomorrow more.")), 2)

    def test_versions_do_not_split(self):
        self.assertEqual(len(split_sentences("Requires Python 3.11.2 exactly. Nothing else.")), 2)

    def test_initials_do_not_split(self):
        self.assertEqual(len(split_sentences("A. Turing wrote it. Others followed.")), 2)

    def test_ellipsis_does_not_split(self):
        self.assertEqual(len(split_sentences("She paused... then continued to the end.")), 1)

    def test_quoted_sentence_end_splits(self):
        self.assertEqual(len(split_sentences('He said "stop." Then he left.')), 2)

    def test_ambiguous_abbreviation_depends_on_what_follows(self):
        self.assertEqual(len(split_sentences("See No. 5 for the exception.")), 1)
        self.assertEqual(len(split_sentences("The answer was no. Then he left.")), 2)


class Encoding(unittest.TestCase):
    def test_crlf(self):
        self.assertEqual(kinds("a\r\n\r\n```\r\ncode\r\n```\r\n"), ["paragraph", "code"])

    def test_bom(self):
        self.assertEqual(parse_markdown("\ufeff# Title\n")[0].kind, "heading")

    def test_line_col_round_trip(self):
        text = "alpha\nbeta gamma\n"
        offsets = line_offsets(text)
        self.assertEqual(line_col(offsets, text.index("gamma")), (2, 6))


class WordCounting(unittest.TestCase):
    def test_hyphens_and_apostrophes(self):
        self.assertEqual(words("state-of-the-art doesn't fail"), ["state-of-the-art", "doesn't", "fail"])


if __name__ == "__main__":
    unittest.main()
