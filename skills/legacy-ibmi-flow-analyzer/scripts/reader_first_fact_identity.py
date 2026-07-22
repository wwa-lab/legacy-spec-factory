#!/usr/bin/env python3
# Legacy Spec Factory
# Copyright 2026 Leo L Zhang
#
# Original author: Leo L Zhang
# License: Apache License 2.0

"""Stable source-fact identity shared by reader-first extraction helpers."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def program_prefix(program: str) -> str:
    value = re.sub(r'[\s<>:"/\\|?*]+', "_", program.strip().upper()).strip("._-")
    return value or "PROGRAM"


def normalize_identity_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def row_text(row: dict[str, Any]) -> str:
    return "; ".join(
        f"{normalize_identity_text(header)}={normalize_identity_text(value)}"
        for header, value in row.items()
    )


def fact_source_text(fact: dict[str, Any]) -> str:
    source_text = normalize_identity_text(fact.get("source_text") or "")
    if source_text:
        return source_text
    source_row = fact.get("source_row")
    if isinstance(source_row, dict):
        return row_text(source_row)
    source_cells = fact.get("source_cells")
    if isinstance(source_cells, list):
        row = {
            str(cell.get("header") or ""): str(cell.get("value") or "")
            for cell in source_cells
            if isinstance(cell, dict) and str(cell.get("header") or "").strip()
        }
        if row:
            return row_text(row)
    return normalize_identity_text(fact.get("logic") or "")


def stable_source_fact_id(
    program: str, section: str, fact_type: str, source_text: str
) -> str:
    """Return the shared Python/PowerShell identity for one source fact."""

    program_key = program_prefix(program)
    section_key = normalize_identity_text(section)
    fact_type_key = normalize_identity_text(fact_type).lower()
    source_key = normalize_identity_text(source_text)
    identity = "\n".join((program_key, section_key, fact_type_key, source_key))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10].upper()
    kind = re.sub(r"[^A-Z0-9]+", "_", fact_type_key.upper()).strip("_") or "FACT"
    return f"SF-{program_key}-{kind}-{digest}"
