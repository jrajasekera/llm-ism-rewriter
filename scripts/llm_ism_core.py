#!/usr/bin/env python3
"""Shared primitives for the llm-ism-rewriter scripts.

Standard library only. Nothing in this module makes an editorial judgment or
says anything about who or what wrote a text; it segments Markdown, loads the
rule registry, and extracts the anchors the checker and validator compare.

Importable by scripts/llm_ism_check.py, scripts/llm_ism_validate.py,
scripts/llm_ism_project_check.py, and scripts/self_scan.py.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass

TOOL_VERSION = "2.2.0"
SCHEMA_VERSION = 1

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REGISTRY = os.path.join(_HERE, os.pardir, "references", "rules.json")


# --- Registry ----------------------------------------------------------------

class RegistryError(Exception):
    """The rule registry is missing, unreadable, or internally inconsistent."""


@dataclass(frozen=True)
class Registry:
    raw: dict
    rules: tuple[dict, ...]
    profiles: dict
    by_id: dict

    def rule(self, rule_id: str) -> dict:
        try:
            return self.by_id[rule_id]
        except KeyError:
            raise RegistryError(f"unknown rule id: {rule_id}") from None

    @property
    def relax_factor(self) -> float:
        return float(self.profiles.get("_meta", {}).get("relax_factor", 2))

    def profile_names(self) -> list[str]:
        return [n for n in self.profiles if n != "_meta"]

    def family_status(self, profile: str, family: str) -> str:
        prof = self.profiles.get(profile)
        if prof is None:
            raise RegistryError(f"unknown profile: {profile}")
        return prof["families"].get(family, "full")


def load_registry(path: str | None = None) -> Registry:
    path = path or DEFAULT_REGISTRY
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot load rule registry {path}: {exc}") from exc

    rules = tuple(raw.get("rules", ()))
    if not rules:
        raise RegistryError(f"rule registry {path} contains no rules")
    by_id: dict[str, dict] = {}
    for rule in rules:
        rid = rule.get("id")
        if not rid:
            raise RegistryError("a rule is missing its id")
        if rid in by_id:
            raise RegistryError(f"duplicate rule id: {rid}")
        by_id[rid] = rule
    # resolve terms_from indirection
    for rule in rules:
        src = rule.get("terms_from")
        if src:
            if src not in by_id:
                raise RegistryError(f"{rule['id']} inherits terms from unknown rule {src}")
            rule.setdefault("terms", by_id[src]["terms"])
    return Registry(raw=raw, rules=rules, profiles=raw.get("profiles", {}), by_id=by_id)


def compiled_patterns(rule: dict) -> list[re.Pattern]:
    """Compile a rule's regexes once and cache them on the rule dict."""
    cache = rule.get("_compiled")
    if cache is None:
        # MULTILINE so that `^` anchors at a line start as well as a unit start:
        # list items, callouts, and hard-wrapped prose all matter.
        cache = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in rule.get("patterns", ())]
        rule["_compiled"] = cache
    return cache


# --- Segmentation ------------------------------------------------------------

PROSE_KINDS = frozenset({"paragraph", "list_item", "callout"})
SCANNABLE_KINDS = PROSE_KINDS | {"heading"}


@dataclass(frozen=True)
class Segment:
    kind: str                       # frontmatter|code|heading|paragraph|list_item|callout|quote|table|html|break
    text: str                       # raw source text of the segment
    start_line: int                 # 1-based, inclusive
    end_line: int                   # 1-based, inclusive
    start_offset: int               # 0-based character offset into the document
    end_offset: int                 # exclusive
    protected: bool
    section_path: tuple[str, ...] = ()
    paragraph_id: int | None = None
    heading_level: int | None = None
    list_depth: int | None = None
    warnings: tuple[str, ...] = ()


_FENCE_RE = re.compile(r"^(\s{0,3})(`{3,}|~{3,})(.*)$")
_ATX_RE = re.compile(r"^(\s{0,3})(#{1,6})\s+(.*?)\s*#*\s*$")
_SETEXT_RE = re.compile(r"^\s{0,3}(=+|-{2,})\s*$")
_LIST_RE = re.compile(r"^(\s*)(?:[-*+]|\d{1,9}[.)])\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
_TABLE_DELIM_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
_BREAK_RE = re.compile(r"^\s{0,3}(?:\*\s*){3,}$|^\s{0,3}(?:-\s*){3,}$|^\s{0,3}(?:_\s*){3,}$")
_HTML_OPEN_RE = re.compile(r"^\s{0,3}<(!--|/?[A-Za-z][\w-]*)")
_ADMONITION_RE = re.compile(r"^\s*\[!\w+\]")
_ATTRIBUTION_RE = re.compile(r"(?:^|\n)\s*(?:—|--|–)\s*\S|(?:\bsaid\b|\bwrote\b|\baccording to\b)", re.IGNORECASE)


def parse_markdown(text: str) -> list[Segment]:
    """Split a Markdown document into typed segments.

    A disciplined line-state parser, not a CommonMark implementation. Where the
    structure is ambiguous the segment is marked protected and carries a
    warning, so an uncertain span is never rewritten on a guess.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    # character offset of the start of each line
    offsets: list[int] = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    segments: list[Segment] = []
    section: list[str] = []
    para_counter = 0
    i = 0
    n = len(lines)

    def emit(kind, first, last, protected, **kw):
        nonlocal para_counter
        start_off = offsets[first]
        end_off = offsets[last] + len(lines[last])
        body = "\n".join(lines[first:last + 1])
        pid = None
        if kind in PROSE_KINDS:
            para_counter += 1
            pid = para_counter
        segments.append(Segment(
            kind=kind, text=body, start_line=first + 1, end_line=last + 1,
            start_offset=start_off, end_offset=end_off, protected=protected,
            section_path=tuple(section), paragraph_id=pid, **kw))

    # frontmatter, only at the very beginning
    if n and lines[0].strip() in ("---", "+++"):
        marker = lines[0].strip()
        j = 1
        while j < n and lines[j].strip() != marker:
            j += 1
        if j < n:
            emit("frontmatter", 0, j, True)
            i = j + 1
        # an unterminated opener is a thematic break, not frontmatter; fall through

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(2)
            char, length = marker[0], len(marker)
            j = i + 1
            closed = False
            while j < n:
                m = _FENCE_RE.match(lines[j])
                if m and m.group(2)[0] == char and len(m.group(2)) >= length and not m.group(3).strip():
                    closed = True
                    break
                j += 1
            last = j if closed else n - 1
            emit("code", i, last, True,
                 warnings=() if closed else ("unclosed code fence; span protected",))
            i = last + 1
            continue

        atx = _ATX_RE.match(line)
        if atx:
            level = len(atx.group(2))
            title = atx.group(3).strip()
            del section[level - 1:]
            while len(section) < level - 1:
                section.append("")
            section.append(title)
            emit("heading", i, i, False, heading_level=level)
            i += 1
            continue

        if _BREAK_RE.match(line):
            emit("break", i, i, True)
            i += 1
            continue

        if _HTML_OPEN_RE.match(line):
            j = i
            while j < n and lines[j].strip():
                j += 1
            emit("html", i, j - 1, True)
            i = j
            continue

        if _QUOTE_RE.match(line):
            j = i
            while j < n and (_QUOTE_RE.match(lines[j]) or (lines[j].strip() and not _is_block_start(lines[j]))):
                j += 1
            body = "\n".join(_QUOTE_RE.sub(r"\1", ln) if _QUOTE_RE.match(ln) else ln
                             for ln in lines[i:j])
            admonition = bool(_ADMONITION_RE.match(body.lstrip()))
            attributed = bool(_ATTRIBUTION_RE.search(body)) or '"' in body or "“" in body
            if attributed and not admonition:
                emit("quote", i, j - 1, True)
            else:
                emit("callout", i, j - 1, False)
            i = j
            continue

        # table: a pipe row followed by a delimiter row
        if "|" in line and i + 1 < n and _TABLE_DELIM_RE.match(lines[i + 1]):
            j = i + 2
            while j < n and lines[j].strip() and "|" in lines[j]:
                j += 1
            emit("table", i, j - 1, True)
            i = j
            continue

        lst = _LIST_RE.match(line)
        if lst:
            depth = len(lst.group(1)) // 2
            j = i + 1
            while j < n and lines[j].strip() and not _is_block_start(lines[j]):
                j += 1
            emit("list_item", i, j - 1, False, list_depth=depth)
            i = j
            continue

        # paragraph, possibly closed by a setext underline
        j = i + 1
        while j < n and lines[j].strip() and not _is_block_start(lines[j]):
            if _SETEXT_RE.match(lines[j]) and j == i + 1:
                break
            j += 1
        if j < n and j == i + 1 and _SETEXT_RE.match(lines[j]) and i + 1 < n:
            level = 1 if lines[j].strip().startswith("=") else 2
            title = lines[i].strip()
            del section[level - 1:]
            while len(section) < level - 1:
                section.append("")
            section.append(title)
            emit("heading", i, j, False, heading_level=level)
            i = j + 1
            continue
        emit("paragraph", i, j - 1, False)
        i = j

    return segments


def _is_block_start(line: str) -> bool:
    return bool(
        _FENCE_RE.match(line) or _ATX_RE.match(line) or _LIST_RE.match(line)
        or _QUOTE_RE.match(line) or _BREAK_RE.match(line) or _HTML_OPEN_RE.match(line)
    )


# --- Inline masking ----------------------------------------------------------

_MASKS = (
    re.compile(r"`+[^`\n]*`+"),                       # inline code
    re.compile(r"!?\[[^\]\n]*\]\([^)\n]*\)"),         # markdown links/images (target and label)
    re.compile(r"\[[^\]\n]*\]\[[^\]\n]*\]"),          # reference links
    re.compile(r"^\s*\[[^\]\n]+\]:\s*\S+.*$", re.M),  # link definitions
    re.compile(r"<[^>\s]+@[^>\s]+>|<https?://[^>\s]+>"),
    re.compile(r"https?://\S+|www\.\S+"),
    re.compile(r"(?<![\w~.])(?:~|\.{1,2})?/[\w.@~-]+(?:/[\w.@~-]+)+/?"),  # posix paths
    re.compile(r"(?<![\w\\])[A-Za-z]:\\[\w\\.$-]+"),  # windows paths
    re.compile(r"\[[^\]\n]{1,40}\]\s*\(?\d{4}\)?"),   # citation keys
    re.compile(r"\[\^[\w-]+\]"),                      # footnote markers
)


_QUOTE_MARKER_RE = re.compile(r"^(\s{0,3})(>\s?)", re.M)


def mask_quote_markers(text: str) -> str:
    """Blank blockquote markers so a callout's first word is sentence-initial."""
    return _QUOTE_MARKER_RE.sub(lambda m: m.group(1) + " " * len(m.group(2)), text)


def mask_inline(text: str) -> str:
    """Blank out spans that must never be matched, preserving every offset.

    Replacement is space-for-character, so a column reported against the masked
    text points at the same column of the source.
    """
    out = list(text)
    for pattern in _MASKS:
        for m in pattern.finditer(text):
            for k in range(m.start(), m.end()):
                if out[k] != "\n":
                    out[k] = " "
    return "".join(out)


# --- Sentences and words -----------------------------------------------------

LABELED_BULLET_RE = re.compile(
    r"^\s*(?:[-*+]|\d{1,9}[.)])\s+"
    r"(?:(?:\*\*|__)[^*_\n]{1,40}[:：](?:\*\*|__)"      # **Label:**
    r"|(?:\*\*|__)[^*_\n]{1,40}(?:\*\*|__)\s*[:：]"     # **Label**:
    r"|[A-Z][\w /-]{1,30}[:：])"                          # Label:
    r"\s+\S")

WORD_RE = re.compile(r"[A-Za-z0-9][\w'’-]*")

_ABBREVIATIONS = frozenset("""
e.g. i.e. etc. vs. cf. al. fig. dr. mr. mrs. ms. prof. inc. ltd. co. corp.
jr. sr. st. approx. ch. sec. eq. p. pp. vol. ed. eds. dept. est. min. max. ref.
u.s. u.k. e.u. a.m. p.m. ph.d. b.c. a.d. resp. incl. cf
""".split())

_BOUNDARY_RE = re.compile(r"[.!?]['\"’”)\]]*(\s+)(?=[\"'“(\[]?[A-Z0-9])")

# Ambiguous abbreviations: "No." abbreviates *number* only when a figure follows,
# but "…said no. Then…" is an ordinary sentence end.
_NUMBERED_ABBREV = frozenset({"no.", "nos.", "fig.", "figs.", "eq.", "sec.", "ch.", "vol.", "p.", "pp."})


def split_sentences(text: str) -> list[tuple[int, str]]:
    """Split into (offset, sentence) pairs.

    Protects abbreviations, decimals, version strings, single-letter initials,
    and ellipses so that `Python 3.11.` or `e.g. this` does not become two
    sentences.
    """
    out: list[tuple[int, str]] = []
    start = 0
    for m in _BOUNDARY_RE.finditer(text):
        cut = m.start()
        before = text[max(0, cut - 12):cut + 1]
        if _protected_period(text, cut, before):
            continue
        end = m.start(1)
        piece = text[start:end]
        if piece.strip():
            out.append((start, piece))
        start = m.end(1)
    tail = text[start:]
    if tail.strip():
        out.append((start, tail))
    return out


def _protected_period(text: str, cut: int, before: str) -> bool:
    if text[cut] != ".":
        return False
    # decimal or version: digit before and after the dot
    nxt = text[cut + 1:cut + 2]
    if before[-2:-1].isdigit() and nxt.isdigit():
        return True
    if text[cut:cut + 3] == "...":
        return True
    token = re.search(r"[\w.'-]+\.$", before)
    if token:
        word = token.group(0).lower()
        if word in _NUMBERED_ABBREV:
            return bool(re.match(r"\s*\d", text[cut + 1:cut + 4]))
        if word in _ABBREVIATIONS:
            return True
        if len(word) == 2 and word[0].isalpha():       # single-letter initial
            return True
        if re.fullmatch(r"v?\d+(\.\d+)*\.", word):     # version string
            return True
    return False


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def normalize(text: str) -> str:
    """Casefold, strip accents and collapse whitespace, for repetition counts."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().casefold()


def line_col(offsets: list[int], offset: int) -> tuple[int, int]:
    """Map a document character offset to a 1-based (line, column)."""
    lo, hi = 0, len(offsets) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if offsets[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1, offset - offsets[lo] + 1


def line_offsets(text: str) -> list[int]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("﻿"):
        text = text[1:]
    out, pos = [], 0
    for line in text.split("\n"):
        out.append(pos)
        pos += len(line) + 1
    return out
