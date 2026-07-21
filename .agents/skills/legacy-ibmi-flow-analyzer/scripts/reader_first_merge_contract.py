#!/usr/bin/env python3
# Legacy Spec Factory
# Copyright 2026 Leo L Zhang
#
# Original author: Leo L Zhang
# License: Apache License 2.0

"""Lossless reader-first source-pack, fact, and coverage preparation helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from reader_first_fact_identity import (
    fact_source_text as _fact_source_text,
    normalize_identity_text as _normalize_identity_text,
    program_prefix as _prefix,
    row_text as _row_text,
    stable_source_fact_id,
)
from reader_first_markdown_contract import (
    is_markdown_table_separator,
    mask_hidden_html,
    reader_section_blocks,
    split_markdown_table_row,
    structured_markdown_surface,
)


SOURCE_SECTIONS = (
    "Program Reading Summary",
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
)


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _analysis_path(analysis_dir: Path, program: str) -> Path | None:
    candidates = (
        analysis_dir / f"{_prefix(program)}-program-analysis.md",
        analysis_dir / "program-analysis.md",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    matches = sorted(analysis_dir.glob("*-program-analysis.md"))
    return matches[0] if len(matches) == 1 else None


def _h2_block(markdown: str, section: str) -> str:
    return reader_section_blocks(markdown, (section,))[section]


def _is_separator(line: str) -> bool:
    return is_markdown_table_separator(line)


def _markdown_tables(block: str) -> list[tuple[tuple[str, ...], list[dict[str, str]]]]:
    lines = structured_markdown_surface(block).splitlines()
    tables: list[tuple[tuple[str, ...], list[dict[str, str]]]] = []
    index = 0
    while index + 1 < len(lines):
        line = lines[index].strip()
        if not (line.startswith("|") and line.endswith("|") and _is_separator(lines[index + 1])):
            index += 1
            continue
        headers = tuple(cell.strip() for cell in split_markdown_table_row(line))
        separator_cells = split_markdown_table_row(lines[index + 1].strip())
        if len(separator_cells) != len(headers):
            raise ValueError(
                "malformed reader-first Markdown table separator has a different "
                "cell count from its header"
            )
        records: list[dict[str, str]] = []
        index += 2
        while index < len(lines):
            row_line = lines[index].strip()
            if not (row_line.startswith("|") and row_line.endswith("|")):
                break
            if _is_separator(row_line):
                index += 1
                continue
            cells = [cell.strip() for cell in split_markdown_table_row(row_line)]
            if len(cells) > len(headers):
                raise ValueError(
                    "malformed reader-first Markdown table row has more cells than headers"
                )
            cells.extend([""] * max(0, len(headers) - len(cells)))
            records.append(dict(zip(headers, cells)))
            index += 1
        tables.append((headers, records))
    return tables


def _headers_match(
    headers: tuple[str, ...], required_header_options: tuple[tuple[str, ...], ...]
) -> bool:
    normalized = {header.lower() for header in headers}
    return any(
        all(required.lower() in normalized for required in required_headers)
        for required_headers in required_header_options
    )


def _table_records(
    block: str, required_header_options: tuple[tuple[str, ...], ...]
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for headers, table_records in _markdown_tables(block):
        if _headers_match(headers, required_header_options):
            records.extend(table_records)
    return records


def _value(row: dict[str, str], *names: str) -> str:
    normalized = {key.strip().lower(): str(value).strip() for key, value in row.items()}
    for name in names:
        value = normalized.get(name.strip().lower())
        if value:
            return value
    return ""


def _row_cells(row: dict[str, str]) -> list[dict[str, str]]:
    return [{"header": header, "value": value} for header, value in row.items()]


def _prose(block: str) -> str:
    lines: list[str] = []
    for raw in structured_markdown_surface(block).splitlines():
        line = raw.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("|")
            or re.match(r"^(?:`{3,}|~{3,})", line)
            or re.match(r"^\*\*.+unresolved:\*\*", line, re.I)
        ):
            continue
        lines.append(line)
    return " ".join(lines)


def _unresolved_statements(block: str) -> list[str]:
    statements: list[str] = []
    for raw in structured_markdown_surface(block).splitlines():
        match = re.match(r"^\*\*(.+?unresolved):\*\*\s*(.+)$", raw.strip(), re.I)
        if not match:
            continue
        value = match.group(2).strip()
        if value.lower().rstrip(".") not in {"none", "no", "n/a", "not applicable"}:
            statements.append(f"{match.group(1)}: {value}")
    return statements


def _evidence(row: dict[str, str], source: str, *names: str) -> tuple[str, str, str | None]:
    status = _value(row, "Evidence Status", "Status")
    reference = _value(row, *names)
    if status:
        normalized = status.lower()
    elif reference:
        normalized = "evidence_present"
    else:
        normalized = "unresolved"
    unresolved = None
    if normalized not in {
        "confirmed",
        "confirmed_from_code",
        "evidence_present",
        "present",
        "source_backed_complete",
    }:
        unresolved = "evidence status is not source-confirmed"
    return normalized, reference or source, unresolved


def _identified(fact: dict[str, Any]) -> dict[str, Any]:
    source_text = _fact_source_text(fact)
    identified_fact = {
        key: value for key, value in fact.items() if key != "source_fact_id"
    }
    return {
        "source_fact_id": stable_source_fact_id(
            str(fact["program"]),
            str(fact["section"]),
            str(fact["fact_type"]),
            source_text,
        ),
        **identified_fact,
        "source_text": source_text,
    }


def _base_fact(
    program: str,
    section: str,
    fact_type: str,
    logic: str,
    source: str,
    *,
    exact_value: str = "",
) -> dict[str, Any]:
    return {
        "program": program,
        "section": section,
        "fact_type": fact_type,
        "material": True,
        "logic": logic,
        "exact_value": exact_value,
        "evidence": source,
        "evidence_reference": source,
        "evidence_status": "confirmed",
        "unresolved_reason": None,
        "source_artifact": source,
    }


def _calculation(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    supporting_detail = _value(
        row, "Supporting Detail Link", "Supporting Detail", "Detail Refs"
    )
    status, evidence, unresolved = _evidence(
        row,
        source,
        "Evidence",
        "Evidence ID",
        "Evidence Reference",
        "Supporting Detail Link",
        "Supporting Detail",
        "Detail Refs",
    )
    logic = _value(row, "Calculation / Assignment", "Calculation", "Assignment")
    target = _value(row, "Target Field / Carrier", "Target Field / Variable", "Target Field")
    return _identified(
        {
            **_base_fact(program, "Calculation Logic", "calculation", logic, source, exact_value=target),
            "routine": _value(row, "Routine"),
            "calculation": logic,
            "target_carrier": target,
            "source_carriers": _value(row, "Source Operands / Carriers", "Source Operands"),
            "guard": _value(row, "Guard / Branch", "Guard"),
            "effect": _value(row, "Effect", "Output / Business Effect"),
            "supporting_detail": supporting_detail,
            "evidence": evidence,
            "evidence_reference": evidence,
            "evidence_status": status,
            "unresolved_reason": unresolved,
            "source_text": _row_text(row),
            "source_row": dict(row),
            "source_cells": _row_cells(row),
        }
    )


def _validation(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    status, evidence, unresolved = _evidence(
        row,
        source,
        "Evidence",
        "Supporting Detail Link",
        "Reverse Trigger Chain / Routine Logic Link",
        "Detail Refs",
    )
    exact = _value(row, "Message / Status Code", "Message / Status / Outcome", "Status")
    description = _value(row, "Message Description", "Description")
    return _identified(
        {
            **_base_fact(
                program,
                "Validation Logic",
                "validation",
                description or f"Validation outcome {exact}",
                source,
                exact_value=exact,
            ),
            "routine": _value(row, "Routine", "Set By / Source Lines"),
            "description": description,
            "exact_code_status": exact,
            "validation_type": _value(row, "Validation / Error Type", "Type"),
            "trigger_chain": _value(row, "Trigger Condition", "Trigger Chain", "Condition / Evidence"),
            "carrier_destination": _value(row, "Output Carrier", "Carrier / Destination"),
            "effect": _value(row, "Downstream Effect", "Effect"),
            "evidence": evidence,
            "evidence_reference": evidence,
            "evidence_status": status,
            "unresolved_reason": unresolved,
            "source_text": _row_text(row),
            "source_row": dict(row),
            "source_cells": _row_cells(row),
        }
    )


def _exception(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    supporting_detail = _value(
        row, "Supporting Detail Link", "Supporting Detail", "Detail Refs"
    )
    status, evidence, unresolved = _evidence(
        row,
        source,
        "Evidence",
        "Evidence ID",
        "Evidence Reference",
        "Supporting Detail Link",
        "Supporting Detail",
        "Detail Refs",
    )
    path = _value(row, "Exception / Error Path", "Exception", "Error Path")
    fields = _value(row, "Fields / Messages Set", "Fields / Messages")
    return _identified(
        {
            **_base_fact(program, "Exception Handling", "exception", path, source, exact_value=fields),
            "routine": _value(row, "Routine"),
            "exception_path": path,
            "guard": _value(row, "Trigger", "Condition"),
            "detection_mechanism": _value(row, "Detection Mechanism", "Detection"),
            "fields_messages_set": fields,
            "exception_action": _value(row, "Handling Action", "Action"),
            "effect": _value(row, "Downstream Effect", "Flow-Level Effect", "Effect"),
            "supporting_detail": supporting_detail,
            "evidence": evidence,
            "evidence_reference": evidence,
            "evidence_status": status,
            "unresolved_reason": unresolved,
            "source_text": _row_text(row),
            "source_row": dict(row),
            "source_cells": _row_cells(row),
        }
    )


def _message(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    status, evidence, unresolved = _evidence(
        row, source, "Evidence", "Detail", "Detail Refs", "Supporting Detail"
    )
    exact = _value(row, "Message / Code / Literal", "Message / Status / Literal", "Message")
    description = _value(row, "Short Description", "Description")
    message_type = _value(row, "Type")
    return _identified(
        {
            **_base_fact(
                program,
                "Message Inventory",
                "message",
                description or f"Exact observed message/status {exact}",
                source,
                exact_value=exact,
            ),
            "routine": _value(row, "Primary Routine(s)", "Program / Routine Sources", "Routine"),
            "exact_message_status_literal": exact,
            "description": description,
            "message_type": message_type,
            "generic_handler_token": (
                exact if "generic_handler" in message_type.lower() else ""
            ),
            "occurrences": _value(row, "Occurrences"),
            "first_seen": _value(row, "First Seen / Set By"),
            "trigger_handler": _value(
                row, "Trigger / Handler Summary", "Condition / Handler", "Trigger / Handler"
            ),
            "carrier_destination": _value(
                row, "Carrier / Destination", "Output Carrier", "Carrier", "Destination"
            ),
            "effect": _value(row, "Effect"),
            "evidence": evidence,
            "evidence_reference": evidence,
            "evidence_status": status,
            "unresolved_reason": unresolved,
            "source_text": _row_text(row),
            "source_row": dict(row),
            "source_cells": _row_cells(row),
        }
    )


def _routines(program: str, section: str, block: str, source: str) -> list[dict[str, Any]]:
    records = _table_records(
        block, (("RLOG / Routine", "Category", "Reader-useful Detail"),)
    )
    return [
        _identified(
            {
                **_base_fact(
                    program,
                    section,
                    "routine",
                    _value(row, "Reader-useful Detail"),
                    source,
                    exact_value=_value(row, "RLOG / Routine"),
                ),
                "routine": _value(row, "RLOG / Routine"),
                "category": _value(row, "Category"),
                "evidence": _value(row, "RLOG / Routine") or source,
                "evidence_reference": _value(row, "RLOG / Routine") or source,
                "source_text": _row_text(row),
                "source_row": dict(row),
                "source_cells": _row_cells(row),
            }
        )
        for row in records
    ]


_EMPTY_TABLE_VALUES = {"", "-", "--", "---", "—", "none", "n/a", "not applicable"}
_METADATA_LABELS = {
    "analysis status",
    "artifact version",
    "document id",
    "flow slug",
    "generated at",
    "generated by",
    "program",
    "program name",
    "program set slug",
    "review intent",
    "schema version",
    "source artifact",
}


def _material_table_row(headers: tuple[str, ...], row: dict[str, str]) -> bool:
    values = [str(value).strip() for value in row.values()]
    material_values = [
        value for value in values if value.lower() not in _EMPTY_TABLE_VALUES
    ]
    if not material_values:
        return False
    normalized_headers = tuple(header.strip().lower() for header in headers)
    if tuple(value.lower() for value in values) == normalized_headers:
        return False
    if len(normalized_headers) == 2 and normalized_headers[1] in {"value", "setting"}:
        first_header = normalized_headers[0]
        first_value = values[0].strip().lower() if values else ""
        if first_header in {"metadata", "property"} or first_value in _METADATA_LABELS:
            return False
    return True


def _specialized_table(section: str, headers: tuple[str, ...]) -> bool:
    if _headers_match(
        headers, (("RLOG / Routine", "Category", "Reader-useful Detail"),)
    ):
        return True
    signatures: dict[str, tuple[tuple[str, ...], ...]] = {
        "Calculation Logic": (("Calculation / Assignment",),),
        "Validation Logic": (
            ("Message / Status Code",),
            ("Message / Status / Outcome",),
        ),
        "Exception Handling": (("Exception / Error Path",),),
        "Message Inventory": (
            ("Message / Code / Literal",),
            ("Message / Status / Literal",),
        ),
    }
    return _headers_match(headers, signatures.get(section, ()))


def _thematic_table(
    program: str, section: str, row: dict[str, str], source: str
) -> dict[str, Any]:
    source_text = _row_text(row)
    values = [str(value).strip() for value in row.values()]
    logic = next((value for value in values if value.lower() not in _EMPTY_TABLE_VALUES), "")
    evidence_values: list[str] = []
    explicit_status = ""
    for header, value in row.items():
        normalized_header = header.strip().lower()
        normalized_value = str(value).strip()
        if "evidence status" in normalized_header:
            explicit_status = normalized_value
        elif re.search(r"evidence|supporting detail|detail refs|rlog", normalized_header):
            if normalized_value:
                evidence_values.append(normalized_value)
    evidence_reference = "; ".join(dict.fromkeys(evidence_values)) or source
    evidence_status = (
        explicit_status.lower()
        if explicit_status
        else "evidence_present" if evidence_values else "source_backed"
    )
    unresolved = None
    if evidence_status not in {
        "confirmed",
        "confirmed_from_code",
        "evidence_present",
        "present",
        "source_backed",
        "source_backed_complete",
    }:
        unresolved = "evidence status is not source-confirmed"
    return _identified(
        {
            **_base_fact(program, section, "thematic_table", logic, source),
            "evidence": evidence_reference,
            "evidence_reference": evidence_reference,
            "evidence_status": evidence_status,
            "unresolved_reason": unresolved,
            "source_text": source_text,
            "source_headers": list(row),
            "source_row": dict(row),
            "source_cells": _row_cells(row),
        }
    )


def _thematic_tables(
    program: str, section: str, block: str, source: str
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    seen_rows: set[str] = set()
    for headers, rows in _markdown_tables(block):
        if _specialized_table(section, headers):
            continue
        for row in rows:
            source_text = _row_text(row)
            if source_text in seen_rows or not _material_table_row(headers, row):
                continue
            seen_rows.add(source_text)
            facts.append(_thematic_table(program, section, row, source))
    return facts


def build_reader_first_source_pack(manifest: dict[str, Any], artifact_root: Path) -> str:
    """Copy all five complete H2 blocks for each distinct ready program."""

    lines = [
        "# Program Set Reader-First Source Pack",
        "",
        f"Document ID: {manifest.get('document_id') or manifest.get('review_id')}",
        f"Flow Slug: {manifest.get('flow_slug')}",
        f"Program Set Slug: {manifest.get('program_set_slug')}",
        "",
        "This lossless preparation artifact is the primary LLM synthesis input.",
        "Program-list order is navigation only, not a source-confirmed call chain.",
    ]
    seen: set[tuple[str, str]] = set()
    for entry in manifest.get("programs", []) or []:
        program = str(entry.get("normalized_name") or "")
        relative_root = str(entry.get("artifact_root") or "")
        identity = (program, relative_root)
        if not program or not relative_root or identity in seen:
            continue
        seen.add(identity)
        path = _analysis_path(artifact_root / relative_root, program)
        if not path:
            continue
        markdown = path.read_text(encoding="utf-8")
        lines.extend(
            [
                "",
                f"<!-- BEGIN LOSSLESS PROGRAM {program}: {_relative(artifact_root, path)} -->",
                f"# Program: {program}",
                "",
            ]
        )
        blocks = reader_section_blocks(markdown, SOURCE_SECTIONS)
        for section in SOURCE_SECTIONS:
            block = blocks[section]
            if block:
                lines.extend((block, ""))
        lines.append(f"<!-- END LOSSLESS PROGRAM {program} -->")
    return "\n".join(lines).rstrip() + "\n"


def _fact_buckets(
    program: str, markdown: str, source: str
) -> dict[str, list[dict[str, Any]]]:
    """Extract the normalized reader-first facts from one complete main file."""
    facts: dict[str, list[dict[str, Any]]] = {
        "summary_contributions": [],
        "thematic_contributions": [],
        "calculations": [],
        "validations": [],
        "exceptions": [],
        "messages": [],
        "routines": [],
        "unresolved_core_statements": [],
    }
    blocks = reader_section_blocks(markdown, SOURCE_SECTIONS)
    summary_text = _prose(blocks["Program Reading Summary"])
    if summary_text:
        facts["summary_contributions"].append(
            _identified(
                _base_fact(
                    program,
                    "Program Reading Summary",
                    "summary_contribution",
                    summary_text,
                    source,
                )
            )
        )
    for section in ("Calculation Logic", "Validation Logic", "Exception Handling"):
        prose = _prose(blocks[section])
        if prose:
            facts["thematic_contributions"].append(
                _identified(
                    _base_fact(program, section, "thematic_prose", prose, source)
                )
            )
    for section in SOURCE_SECTIONS:
        facts["thematic_contributions"].extend(
            _thematic_tables(program, section, blocks[section], source)
        )
    for section in SOURCE_SECTIONS:
        for statement in _unresolved_statements(blocks[section]):
            facts["unresolved_core_statements"].append(
                _identified(
                    {
                        **_base_fact(
                            program,
                            section,
                            "unresolved_core_statement",
                            statement,
                            source,
                        ),
                        "evidence_status": "unresolved_non_blocking",
                        "unresolved_reason": statement,
                    }
                )
            )
    facts["calculations"] = [
        _calculation(program, row, source)
        for row in _table_records(
            blocks["Calculation Logic"], (("Calculation / Assignment",),)
        )
    ]
    facts["validations"] = [
        _validation(program, row, source)
        for row in _table_records(
            blocks["Validation Logic"],
            (("Message / Status Code",), ("Message / Status / Outcome",)),
        )
    ]
    facts["exceptions"] = [
        _exception(program, row, source)
        for row in _table_records(
            blocks["Exception Handling"], (("Exception / Error Path",),)
        )
    ]
    facts["messages"] = [
        _message(program, row, source)
        for row in _table_records(
            blocks["Message Inventory"],
            (("Message / Code / Literal",), ("Message / Status / Literal",)),
        )
    ]
    for section in SOURCE_SECTIONS:
        facts["routines"].extend(_routines(program, section, blocks[section], source))
    return facts


def extract_source_pack_facts(
    source_pack: str, programs: list[str]
) -> list[dict[str, Any]]:
    """Re-extract expected facts from the lossless pack for reverse coverage."""
    extracted: list[dict[str, Any]] = []
    for program in dict.fromkeys(programs):
        marker = re.search(
            rf"^<!-- BEGIN LOSSLESS PROGRAM {re.escape(program)}: (?P<source>.+?) -->\s*$",
            source_pack,
            re.M,
        )
        if not marker:
            continue
        end = re.search(
            rf"^<!-- END LOSSLESS PROGRAM {re.escape(program)} -->\s*$",
            source_pack[marker.end() :],
            re.M,
        )
        stop = marker.end() + end.start() if end else len(source_pack)
        markdown = source_pack[marker.end() : stop]
        buckets = _fact_buckets(program, markdown, marker.group("source").strip())
        extracted.extend(fact for bucket in buckets.values() for fact in bucket)
    return extracted


def build_core_facts(manifest: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    programs: list[dict[str, Any]] = []
    source_facts: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for entry in manifest.get("programs", []) or []:
        program = str(entry.get("normalized_name") or "")
        relative_root = str(entry.get("artifact_root") or "")
        identity = (program, relative_root)
        if not program or identity in seen:
            continue
        seen.add(identity)
        facts: dict[str, list[dict[str, Any]]] = _fact_buckets(program, "", "")
        source_files: list[str] = []
        path = _analysis_path(artifact_root / relative_root, program) if relative_root else None
        if path:
            source = _relative(artifact_root, path)
            source_files.append(source)
            markdown = path.read_text(encoding="utf-8")
            facts = _fact_buckets(program, markdown, source)
        flattened = [fact for bucket in facts.values() for fact in bucket]
        source_facts.extend(flattened)
        programs.append(
            {
                "program": program,
                "run_resolution": entry.get("run_resolution"),
                "source_status": "complete" if path else "pending",
                "source_files": source_files,
                "facts": facts,
                "source_fact_ids": [fact["source_fact_id"] for fact in flattened],
                "unresolved_reason": None if path else "ready program-analysis.md is unavailable",
            }
        )
    return {
        "schema_version": "0.4",
        "generated_by": "program_set_core_review.py",
        "generator_version": "0.4.0",
        "document_id": manifest.get("document_id") or manifest.get("review_id"),
        "review_id": manifest.get("review_id"),
        "review_status": manifest.get("review_status"),
        "review_profile": manifest.get("core_review_profile"),
        "flow_slug": manifest.get("flow_slug"),
        "program_set_slug": manifest.get("program_set_slug"),
        "folder_slug": manifest.get("folder_slug"),
        "source_facts": source_facts,
        "programs": programs,
        "evidence_boundary": (
            "Facts and prose come only from the five complete reader-first sections; "
            "program order is not a source-confirmed call edge."
        ),
    }


def build_core_coverage(core_facts: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    source_facts = [
        fact for fact in core_facts.get("source_facts", []) or [] if isinstance(fact, dict)
    ]
    items = [
        {
            "source_fact_id": fact.get("source_fact_id"),
            "program": fact.get("program"),
            "section": fact.get("section"),
            "fact_type": fact.get("fact_type"),
            "status": "pending",
            "review_anchor": None,
            "merged_source_fact_ids": [],
            "exclusion_reason": None,
        }
        for fact in source_facts
    ]
    by_program: dict[str, int] = {}
    by_section: dict[str, int] = {}
    routine_rlog: dict[str, int] = {}
    for fact in source_facts:
        program = str(fact.get("program") or "")
        section = str(fact.get("section") or "")
        by_program[program] = by_program.get(program, 0) + 1
        by_section[section] = by_section.get(section, 0) + 1
        if fact.get("fact_type") == "routine":
            routine_rlog[program] = routine_rlog.get(program, 0) + 1
    counts = {
        "total_source_facts": len(source_facts),
        "accounted_source_facts": 0,
        "pending_source_facts": len(source_facts),
        "by_program": by_program,
        "by_section": by_section,
        "routine_rlog": routine_rlog,
    }
    return {
        "schema_version": "0.4",
        "document_id": manifest.get("document_id") or manifest.get("review_id"),
        "review_status": "pending_synthesis",
        "coverage_status": "pending",
        "allowed_statuses": ["included", "merged", "excluded_non_core", "pending"],
        "coverage_counts": counts,
        "expected_source_fact_count": len(source_facts),
        "coverage_item_count": len(items),
        "status_counts": {
            "included": 0,
            "merged": 0,
            "excluded_non_core": 0,
            "pending": len(items),
        },
        "coverage_items": items,
        "items": [dict(item) for item in items],
    }
