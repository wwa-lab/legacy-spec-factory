#!/usr/bin/env python3
"""Convenience wrapper for the canonical program analysis contract validator."""

from __future__ import annotations

import runpy
from pathlib import Path


SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "validate_program_analysis_contract.py"
)


if __name__ == "__main__":
    runpy.run_path(str(SKILL_SCRIPT), run_name="__main__")
