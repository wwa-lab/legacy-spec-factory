#!/usr/bin/env python3
"""Convenience wrapper for the canonical IBM i repository scanner."""

from __future__ import annotations

import runpy
from pathlib import Path


SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "legacy-ibmi-inventory"
    / "scripts"
    / "scan_ibmi_repo.py"
)


if __name__ == "__main__":
    runpy.run_path(str(SKILL_SCRIPT), run_name="__main__")
