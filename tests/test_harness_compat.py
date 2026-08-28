"""The skill has to load and run under any harness that reads SKILL.md.

Claude Code, Codex and Hermes Agent all install a skill as a directory with
SKILL.md at its root, and all of them run it from the user's working directory
rather than the skill's own. These tests hold that boundary.
"""
from __future__ import annotations

import os
import re
import unittest

from _support import ROOT

SKILL = os.path.join(ROOT, "SKILL.md")
REFERENCES = os.path.join(ROOT, "references")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def frontmatter(text: str) -> dict:
    """Top-level scalar keys only. Enough for the base agentskills.io fields."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md has no frontmatter"
    fields = {}
    for line in m.group(1).splitlines():
        if line[:1].isspace() or not line.strip():
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields


class Frontmatter(unittest.TestCase):
    def setUp(self):
        self.fields = frontmatter(read(SKILL))

    def test_required_and_recommended_fields_are_top_level(self):
        for key in ("name", "description", "license", "version", "compatibility"):
            self.assertIn(key, self.fields, f"{key} must be a top-level frontmatter key")

    def test_name_follows_the_naming_rules(self):
        """Installers require the directory to be named after this field, so the
        field itself has to be a legal directory name: lowercase, hyphenated, no
        leading, trailing or doubled hyphen, at most 64 characters. The checkout
        directory is not checked — a worktree or fork may be named anything."""
        self.assertRegex(self.fields["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertLessEqual(len(self.fields["name"]), 64)

    def test_field_limits(self):
        self.assertLessEqual(len(self.fields["description"]), 1024)
        self.assertLessEqual(len(self.fields["compatibility"]), 500)

    def test_license_is_a_bare_spdx_identifier(self):
        self.assertEqual(self.fields["license"], "Apache-2.0")


class PortablePaths(unittest.TestCase):
    """A command that assumes the working directory is the skill root fails
    everywhere except a shell opened inside this repository."""

    def files(self):
        yield SKILL
        for name in sorted(os.listdir(REFERENCES)):
            if name.endswith(".md"):
                yield os.path.join(REFERENCES, name)

    def test_skill_states_the_path_rule(self):
        self.assertIn("SKILL_DIR", read(SKILL))

    def test_no_command_assumes_the_working_directory(self):
        bare = re.compile(r"(?<![\w/$\"])(?:python3?\s+)?scripts/llm_ism_\w+\.py")
        offenders = []
        for path in self.files():
            for lineno, line in enumerate(read(path).splitlines(), 1):
                if "python" not in line and not line.lstrip().startswith("python"):
                    # A bare mention inside backticks names the file; only a
                    # runnable command has to carry $SKILL_DIR.
                    if not re.search(r"run\s+`scripts/", line):
                        continue
                if bare.search(line):
                    offenders.append(f"{os.path.relpath(path, ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "\n".join(offenders))


class HarnessNeutralProse(unittest.TestCase):
    """Naming one harness's tool makes the instruction unusable on the others."""

    BANNED = ("TodoWrite", "apply_patch", "str_replace_editor", "delegate_task",
              "spawn_agent", "wait_agent", "skill_view", "the Read tool",
              "the Edit tool", "the Bash tool", "the Task tool")

    def test_no_harness_specific_tool_names(self):
        offenders = []
        for name in ["SKILL.md"] + [f"references/{f}" for f in sorted(os.listdir(REFERENCES))
                                    if f.endswith(".md")]:
            text = read(os.path.join(ROOT, name))
            offenders += [f"{name}: {token}" for token in self.BANNED if token in text]
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
