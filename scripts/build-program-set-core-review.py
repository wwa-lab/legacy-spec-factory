#!/usr/bin/env python3
"""Convenience wrapper for the program-set core review builder."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)


if __name__ == "__main__":
    sys.argv.insert(1, "build")
    runpy.run_path(str(SKILL_SCRIPT), run_name="__main__")
