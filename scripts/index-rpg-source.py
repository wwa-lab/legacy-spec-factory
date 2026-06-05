#!/usr/bin/env python3
"""Convenience wrapper for the canonical RPG source indexer."""

from __future__ import annotations

import runpy
from pathlib import Path


SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "index_rpg_source.py"
)


if __name__ == "__main__":
    runpy.run_path(str(SKILL_SCRIPT), run_name="__main__")
