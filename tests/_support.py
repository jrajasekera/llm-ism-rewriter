"""Shared test helpers: path wiring and fixture loading."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
SCRIPTS = os.path.join(ROOT, "scripts")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def fixture(name: str):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


def case_text(case: dict) -> str:
    return case["text"] * case.get("repeat", 1)
