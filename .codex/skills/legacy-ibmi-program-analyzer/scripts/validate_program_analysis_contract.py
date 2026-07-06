#!/usr/bin/env python3
"""Validate program-analyzer artifact contract completeness.

This checker is intentionally mechanical. It does not judge whether the
analysis is semantically correct; it catches compressed or partial wrapper
outputs that omit required sections, declared sidecars, or RLOG coverage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_PROGRAM_SECTIONS = (
    "Program Reading Summary",
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
    "Metadata",
    "Analysis Coverage & Scope",
    "Program Call Map",
    "Routine Cards",
    "Routine Logic Details",
    "Deep Read Windows",
    "Entry Points & Parameters",
    "Object Dependencies",
    "Logic Decomposition Ledger",
    "Data Touch Map",
    "Key File & Field Logic",
    "Control Flow",
    "File I/O",
    "External Calls",
    "Error Handling",
    "Redundancy Candidate Notes",
    "TBDs & Blocking Status",
    "Review Checklist",
)

CORE_SIDECAR_KEYS = (
    "source_index",
    "routine_index",
    "routine_logic_details",
    "routine_logic_details_yaml",
    "message_inventory_yaml",
)

ROUTINE_FINAL_SECTIONS = (
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
    "Routine Detail Index",
    "Routine Details",
)

BATCH_CORE_SECTIONS = (
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
)

BATCH_REQUIRED_SECTIONS = (
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Scope",
    "Batch Coverage Summary",
    "Message Inventory",
    "Routine Details",
)

RLOG_RE = re.compile(r"\bRLOG-[A-Z0-9_#$@-]+-\d{3}\b", re.I)
FENCED_CODE_RE = re.compile(r"```")
FIXED_FORMAT_SOURCE_RE = re.compile(
    r"^\s*(?:[A-Z0-9_#$@]{1,10}\s+)?C\s{2,}.*\b"
    r"(EXSR|BEGSR|ENDSR|CHAIN|SETLL|READE|READP?E?|READ|WRITE|UPDATE|"
    r"DELETE|EXFMT|CALLP?|CALLPRC|EVAL|MOVE|MOVEL|Z-ADD|ADD|SUB|MULT|DIV|"
    r"MONITOR|ON-ERROR|MONMSG|SNDPGMMSG)\b",
    re.I,
)
FREE_FORMAT_SOURCE_RE = re.compile(
    r"^\s*(IF|WHEN|DOW|DOU|FOR|SELECT|MONITOR|ON-ERROR|RETURN|EVAL|"
    r"EXEC\s+SQL|CHAIN|SETLL|READE|READP?E?|READ|WRITE|UPDATE|DELETE|"
    r"CALLP?|EXSR|DCL-[A-Z]+)\b.+;\s*$",
    re.I,
)
SQL_SOURCE_RE = re.compile(
    r"^\s*(SELECT|UPDATE|INSERT|DELETE|MERGE)\s+.+\b(FROM|SET|INTO|WHERE)\b.*;?\s*$",
    re.I,
)
UNRESOLVED_MESSAGE_DESCRIPTION = "unresolved - message description not available"
UNRESOLVED_DESCRIPTION_SOURCES = {
    "",
    "unresolved",
    "missing_message_catalog_or_reference_pack",
    "missing_message_file",
    "pending_message_file",
}
UNRESOLVED_DESCRIPTION_STATUSES = {
    "unresolved",
    "unresolved_description",
    "pending_message_file",
}
STALE_DEEP_READ_GAP_PATTERNS = (
    re.compile(r"\bRemaining routine deep-read gaps\b", re.I),
    re.compile(r"\bnot-yet-deep-read routines\b", re.I),
    re.compile(r"\bnot deep-read routines?\b", re.I),
)
READER_FIRST_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bpending reader-oriented summary\b", re.I),
    re.compile(r"\bpending semantic deep-read\b", re.I),
    re.compile(r"\bpending semantic detail\b", re.I),
    re.compile(r"\bplaceholder content\b", re.I),
    re.compile(r"\bplaceholder\b", re.I),
    re.compile(r"\bnot-yet-deep-read\b", re.I),
    re.compile(r"\bnot deep-read\b", re.I),
)
MEANINGFUL_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_#$@/-]*|[\u4e00-\u9fff]{2,}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError(
            "PyYAML is required to validate YAML sidecar declarations. "
            "Install with: pip install pyyaml"
        ) from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def find_program_analysis_path(analysis_dir: Path, explicit_path: Path | None) -> Path | None:
    if explicit_path is not None:
        return explicit_path
    default_path = analysis_dir / "program-analysis.md"
    if default_path.is_file():
        return default_path
    matches = sorted(analysis_dir.glob("program-analysis-*.md"))
    if len(matches) == 1:
        return matches[0]
    return None


def h2_positions(markdown: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    for match in re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M):
        heading = match.group(1).strip()
        positions.setdefault(heading, match.start())
    return positions


def heading_positions(markdown: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    for match in re.finditer(r"^#{2,6}\s+(.+?)\s*$", markdown, re.M):
        heading = match.group(1).strip()
        positions.setdefault(heading, match.start())
    return positions


def heading_spans(markdown: str) -> dict[str, tuple[int, int]]:
    matches = list(re.finditer(r"^(#{2,6})\s+(.+?)\s*$", markdown, re.M))
    spans: dict[str, tuple[int, int]] = {}
    for index, match in enumerate(matches):
        heading = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        spans.setdefault(heading, (start, end))
    return spans


def h2_section_text(markdown: str, heading: str) -> str:
    pattern = re.compile(r"^##\s+(.+?)\s*$", re.M)
    matches = list(pattern.finditer(markdown))
    for index, match in enumerate(matches):
        if match.group(1).strip() != heading:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        return markdown[start:end]
    return ""


def validate_ordered_headings(
    markdown: str,
    required_headings: tuple[str, ...],
    artifact_label: str,
) -> list[str]:
    findings: list[str] = []
    positions = heading_positions(markdown)
    missing = [heading for heading in required_headings if heading not in positions]
    if missing:
        findings.append(f"{artifact_label} missing required headings: " + ", ".join(missing))
        return findings
    ordered_positions = [positions[heading] for heading in required_headings]
    if ordered_positions != sorted(ordered_positions):
        findings.append(f"{artifact_label} required headings are out of order")
    return findings


def validate_ordered_h2_headings(
    markdown: str,
    required_headings: tuple[str, ...],
    artifact_label: str,
) -> list[str]:
    findings: list[str] = []
    positions = h2_positions(markdown)
    missing = [heading for heading in required_headings if heading not in positions]
    if missing:
        findings.append(f"{artifact_label} missing required ## headings: " + ", ".join(missing))
        return findings
    ordered_positions = [positions[heading] for heading in required_headings]
    if ordered_positions != sorted(ordered_positions):
        findings.append(f"{artifact_label} required ## headings are out of order")
    return findings


def table_cells_or_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped:
        return []
    if stripped.startswith("|") and stripped.endswith("|"):
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        return [
            cell
            for cell in cells
            if cell and not re.fullmatch(r":?-{3,}:?", cell)
        ]
    return [stripped]


def has_reader_first_placeholder(text: str) -> bool:
    return any(pattern.search(text) for pattern in READER_FIRST_PLACEHOLDER_PATTERNS)


def meaningful_word_count(text: str) -> int:
    cleaned = re.sub(r"`[^`]*`", " ", text)
    cleaned = RLOG_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\bSR\d{3,}\b", " ", cleaned, flags=re.I)
    return len(MEANINGFUL_WORD_RE.findall(cleaned))


def is_markdown_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def markdown_table_rows(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if is_markdown_separator_row(cells):
            continue
        rows.append(cells)
    return rows


def strip_inline_code_marks(text: str) -> str:
    return text.replace("`", "").strip()


def looks_like_source_snippet(text: str) -> bool:
    candidate = strip_inline_code_marks(text)
    if not candidate:
        return False
    if FIXED_FORMAT_SOURCE_RE.search(candidate):
        return True
    if FREE_FORMAT_SOURCE_RE.search(candidate):
        return True
    if SQL_SOURCE_RE.search(candidate):
        return True
    return False


def validate_batch_core_has_no_source_snippets(
    batch_text: str,
    batch_label: str,
) -> list[str]:
    findings: list[str] = []
    spans = heading_spans(batch_text)
    for section in BATCH_CORE_SECTIONS:
        span = spans.get(section)
        if span is None:
            continue
        section_text = batch_text[span[0] : span[1]]
        if FENCED_CODE_RE.search(section_text):
            findings.append(
                f"{batch_label} {section} core logic must not contain fenced source/code blocks"
            )
        for line_number, line in enumerate(section_text.splitlines(), start=1):
            for cell in table_cells_or_line(line):
                if looks_like_source_snippet(cell):
                    findings.append(
                        f"{batch_label} {section} core logic contains a source-code-like snippet "
                        f"near section line {line_number}: {cell[:80]}"
                    )
                    break
    return findings


def validate_required_sections(program_markdown: str) -> list[str]:
    findings: list[str] = []
    positions = h2_positions(program_markdown)
    missing = [section for section in REQUIRED_PROGRAM_SECTIONS if section not in positions]
    if missing:
        findings.append("program-analysis.md missing required sections: " + ", ".join(missing))
        return findings

    ordered_positions = [positions[section] for section in REQUIRED_PROGRAM_SECTIONS]
    if ordered_positions != sorted(ordered_positions):
        findings.append(
            "program-analysis.md required sections are out of order; follow "
            "references/output-contract.md File Structure"
        )
    return findings


def extract_rlog_ids_from_yaml(path: Path) -> list[str]:
    payload = load_yaml(path)
    inventory = (payload or {}).get("routine_logic_inventory", {})
    details = inventory.get("details", []) if isinstance(inventory, dict) else []
    ids: list[str] = []
    for detail in details:
        if isinstance(detail, dict) and detail.get("detail_id"):
            ids.append(str(detail["detail_id"]).upper())
    return ids


def extract_rlog_ids_from_markdown(path: Path) -> list[str]:
    return [match.group(0).upper() for match in RLOG_RE.finditer(read_text(path))]


def extract_main_rlog_detail_headings(program_markdown: str) -> list[str]:
    section_text = h2_section_text(program_markdown, "Routine Logic Details")
    return [
        match.group(1).upper()
        for match in re.finditer(r"^###\s+(RLOG-[A-Z0-9_#$@-]+-\d{3})\b", section_text, re.I | re.M)
    ]


def rlog_suffix_number(rlog_id: str) -> int | None:
    match = re.search(r"-(\d{3})$", rlog_id)
    if match is None:
        return None
    return int(match.group(1))


def validate_rlog_sequence(label: str, rlog_ids: list[str]) -> list[str]:
    findings: list[str] = []
    if not rlog_ids:
        return findings
    numbers = [rlog_suffix_number(rlog_id) for rlog_id in rlog_ids]
    if any(number is None for number in numbers):
        findings.append(f"{label} contains malformed RLOG IDs")
        return findings
    normalized_numbers = [number for number in numbers if number is not None]
    expected = list(range(1, len(normalized_numbers) + 1))
    if normalized_numbers != expected:
        findings.append(
            f"{label} RLOG IDs must be continuous and ordered from 001; found "
            + ", ".join(rlog_ids)
        )
    return findings


def validate_rlog_coverage(analysis_dir: Path) -> list[str]:
    findings: list[str] = []
    yaml_path = analysis_dir / "routine-logic-details.yaml"
    markdown_path = analysis_dir / "routine-logic-details.md"
    if not yaml_path.is_file() or not markdown_path.is_file():
        return findings

    yaml_ids = extract_rlog_ids_from_yaml(yaml_path)
    markdown_ids = extract_rlog_ids_from_markdown(markdown_path)
    if not yaml_ids:
        findings.append("routine-logic-details.yaml has no routine_logic_inventory.details[].detail_id values")
        return findings

    findings.extend(validate_rlog_sequence("routine-logic-details.yaml", yaml_ids))

    missing = sorted(set(yaml_ids) - set(markdown_ids))
    if missing:
        findings.append(
            "routine-logic-details.md missing RLOG IDs declared in YAML: "
            + ", ".join(missing)
        )

    return findings


def validate_program_rlog_coverage(program_markdown: str, analysis_dir: Path) -> list[str]:
    yaml_path = analysis_dir / "routine-logic-details.yaml"
    if not yaml_path.is_file():
        return []

    yaml_ids = extract_rlog_ids_from_yaml(yaml_path)
    if not yaml_ids:
        return []

    findings: list[str] = []
    detail_heading_ids = extract_main_rlog_detail_headings(program_markdown)
    if not detail_heading_ids:
        findings.append(
            "program-analysis.md Routine Logic Details missing RLOG detail headings declared in YAML: "
            + ", ".join(yaml_ids)
        )
        return findings

    missing = sorted(set(yaml_ids) - set(detail_heading_ids))
    extra = sorted(set(detail_heading_ids) - set(yaml_ids))
    if missing:
        findings.append(
            "program-analysis.md Routine Logic Details missing RLOG detail headings declared in YAML: "
            + ", ".join(missing)
        )
    if extra:
        findings.append(
            "program-analysis.md Routine Logic Details contains extra RLOG detail headings not declared in YAML: "
            + ", ".join(extra)
        )
    if detail_heading_ids != yaml_ids:
        findings.append(
            "program-analysis.md Routine Logic Details RLOG headings must match YAML order and count"
        )
    findings.extend(validate_rlog_sequence("program-analysis.md Routine Logic Details", detail_heading_ids))
    return findings


def validate_core_logic_routine_indexes(program_markdown: str, analysis_dir: Path) -> list[str]:
    yaml_path = analysis_dir / "routine-logic-details.yaml"
    if not yaml_path.is_file():
        return []

    yaml_ids = extract_rlog_ids_from_yaml(yaml_path)
    if not yaml_ids:
        return []

    findings: list[str] = []
    for section in BATCH_CORE_SECTIONS:
        section_text = h2_section_text(program_markdown, section)
        index_heading = f"Routine Index For {section}"
        if index_heading not in section_text:
            findings.append(f"program-analysis.md missing {index_heading}")
            continue
        index_ids = [match.group(0).upper() for match in RLOG_RE.finditer(section_text)]
        missing = sorted(set(yaml_ids) - set(index_ids))
        if missing:
            findings.append(
                f"program-analysis.md {index_heading} missing RLOG rows declared in YAML: "
                + ", ".join(missing)
            )
        if len(index_ids) < len(yaml_ids):
            findings.append(
                f"program-analysis.md {index_heading} row count is {len(index_ids)}; "
                f"expected at least {len(yaml_ids)}"
            )
    return findings


def validate_program_reading_summary_quality(program_markdown: str) -> list[str]:
    section_text = h2_section_text(program_markdown, "Program Reading Summary")
    if not section_text:
        return []

    findings: list[str] = []
    if has_reader_first_placeholder(section_text) or meaningful_word_count(section_text) < 20:
        findings.append(
            "reader-first golden gate: Program Reading Summary must contain "
            "reader-oriented processing context, not placeholder or pending text"
        )

    required_headers = ("Processing Layer", "Main Routines", "What To Understand First")
    missing_headers = [header for header in required_headers if header not in section_text]
    if missing_headers:
        findings.append(
            "reader-first golden gate: Program Reading Summary missing processing-layer "
            "table headers: "
            + ", ".join(missing_headers)
        )
        return findings

    rows = markdown_table_rows(section_text)
    data_rows = [
        cells
        for cells in rows
        if cells
        and cells[0] != "Processing Layer"
        and len(cells) >= 3
        and not has_reader_first_placeholder(" ".join(cells))
        and meaningful_word_count(cells[2]) >= 5
    ]
    if not data_rows:
        findings.append(
            "reader-first golden gate: Program Reading Summary needs at least one "
            "processing-layer row with reader-useful explanation"
        )
    return findings


def validate_core_logic_reader_first_quality(
    program_markdown: str,
    analysis_dir: Path,
) -> list[str]:
    yaml_path = analysis_dir / "routine-logic-details.yaml"
    if not yaml_path.is_file():
        return []

    yaml_ids = extract_rlog_ids_from_yaml(yaml_path)
    if not yaml_ids:
        return []

    findings: list[str] = []
    for section in BATCH_CORE_SECTIONS:
        section_text = h2_section_text(program_markdown, section)
        if not section_text:
            continue

        index_heading = f"Routine Index For {section}"
        overview_text = section_text.split(index_heading, 1)[0]
        if has_reader_first_placeholder(overview_text) or meaningful_word_count(overview_text) < 4:
            findings.append(
                f"reader-first golden gate: program-analysis.md {section} must start "
                "with reader-oriented overview content before the routine index"
            )

        if index_heading not in section_text:
            continue
        index_text = section_text.split(index_heading, 1)[1]
        for rlog_id in yaml_ids:
            row = next(
                (line for line in index_text.splitlines() if rlog_id in line.upper()),
                "",
            )
            if not row:
                continue
            cells = table_cells_or_line(row)
            detail = cells[-1] if len(cells) >= 3 else row
            if has_reader_first_placeholder(detail) or meaningful_word_count(detail) < 3:
                findings.append(
                    f"reader-first golden gate: program-analysis.md {index_heading} "
                    f"{rlog_id} needs reader-useful detail, not pending/placeholder text"
                )
    return findings


def extract_main_rlog_detail_blocks(program_markdown: str) -> dict[str, str]:
    section_text = h2_section_text(program_markdown, "Routine Logic Details")
    matches = list(
        re.finditer(
            r"^###\s+(RLOG-[A-Z0-9_#$@-]+-\d{3})\b.*$",
            section_text,
            re.I | re.M,
        )
    )
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_text)
        blocks[match.group(1).upper()] = section_text[start:end]
    return blocks


def validate_main_rlog_detail_quality(
    program_markdown: str,
    analysis_dir: Path,
) -> list[str]:
    yaml_path = analysis_dir / "routine-logic-details.yaml"
    if not yaml_path.is_file():
        return []

    yaml_ids = extract_rlog_ids_from_yaml(yaml_path)
    if not yaml_ids:
        return []

    findings: list[str] = []
    blocks = extract_main_rlog_detail_blocks(program_markdown)
    for rlog_id in yaml_ids:
        body = blocks.get(rlog_id, "")
        if not body:
            continue
        if has_reader_first_placeholder(body) or meaningful_word_count(body) < 12:
            findings.append(
                "reader-first golden gate: program-analysis.md Routine Logic Details "
                f"{rlog_id} needs reader-useful detail, not pending/placeholder text"
            )
    return findings


def validate_reader_first_golden_gate(program_markdown: str, analysis_dir: Path) -> list[str]:
    findings: list[str] = []
    findings.extend(validate_program_reading_summary_quality(program_markdown))
    findings.extend(validate_core_logic_reader_first_quality(program_markdown, analysis_dir))
    findings.extend(validate_main_rlog_detail_quality(program_markdown, analysis_dir))
    return findings


def validate_no_stale_gap_wording(program_markdown: str) -> list[str]:
    findings: list[str] = []
    for pattern in STALE_DEEP_READ_GAP_PATTERNS:
        if pattern.search(program_markdown):
            findings.append(
                "program-analysis.md contains stale deep-read gap wording: "
                + pattern.pattern.replace("\\b", "")
            )
    return findings


def batch_detail_files(analysis_dir: Path) -> list[Path]:
    batch_dir = analysis_dir / "routine-logic-details"
    if not batch_dir.is_dir():
        return []
    patterns = ("part-*.md", "deep-read-batch-*.md", "deep-batch-*.md")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(batch_dir.glob(pattern))
    return sorted(set(files))


def summary_payload(analysis_dir: Path) -> dict[str, Any]:
    summary_path = analysis_dir / "program-analysis-summary.yaml"
    if not summary_path.is_file():
        return {}
    payload = load_yaml(summary_path)
    return payload if isinstance(payload, dict) else {}


def requires_large_program_batches(payload: dict[str, Any]) -> bool:
    if payload.get("program_size_tier") == "large_extreme_program":
        return True
    counts = payload.get("counts", {})
    if isinstance(counts, dict) and int(counts.get("source_lines", 0) or 0) > 10000:
        return True
    source = payload.get("source", {})
    if isinstance(source, dict) and int(source.get("line_count", 0) or 0) > 10000:
        return True
    return False


def validate_large_program_batches(analysis_dir: Path) -> list[str]:
    payload = summary_payload(analysis_dir)
    if not payload or not requires_large_program_batches(payload):
        return []

    findings: list[str] = []
    batches = batch_detail_files(analysis_dir)
    if not batches:
        findings.append(
            "large_extreme_program requires routine-logic-details/deep-read-batch-*.md "
            "batch checkpoint files"
        )
        return findings

    canonical_first = analysis_dir / "routine-logic-details" / "deep-read-batch-001.md"
    alias_first = analysis_dir / "routine-logic-details" / "deep-batch-001.md"
    if not canonical_first.is_file() and not alias_first.is_file():
        findings.append(
            "large_extreme_program requires a first batch checkpoint: "
            "routine-logic-details/deep-read-batch-001.md"
        )
    return findings


def validate_routine_detail_review_surfaces(analysis_dir: Path) -> list[str]:
    findings: list[str] = []
    batches = batch_detail_files(analysis_dir)
    if not batches:
        return findings

    routine_markdown_path = analysis_dir / "routine-logic-details.md"
    if routine_markdown_path.is_file():
        findings.extend(
            validate_ordered_headings(
                read_text(routine_markdown_path),
                ROUTINE_FINAL_SECTIONS,
                "routine-logic-details.md",
            )
        )

    for batch_path in batches:
        batch_text = read_text(batch_path)
        batch_label = str(batch_path.relative_to(analysis_dir))
        findings.extend(
            validate_ordered_h2_headings(
                batch_text,
                BATCH_REQUIRED_SECTIONS,
                batch_label,
            )
        )
        findings.extend(validate_batch_core_has_no_source_snippets(batch_text, batch_label))
        positions = heading_positions(batch_text)
        if not all(heading in positions for heading in BATCH_CORE_SECTIONS):
            continue
        first_core_position = min(positions[heading] for heading in BATCH_CORE_SECTIONS)
        rlog_match = RLOG_RE.search(batch_text)
        if rlog_match and first_core_position > rlog_match.start():
            findings.append(
                f"{batch_label} must put Calculation/Validation/Exception core logic before per-routine RLOG detail"
            )
    return findings


def sidecar_entries(summary_path: Path) -> dict[str, dict[str, str]]:
    payload = load_yaml(summary_path)
    sidecars = (payload or {}).get("sidecars", {})
    if not isinstance(sidecars, dict):
        return {}
    entries: dict[str, dict[str, str]] = {}
    for key, value in sidecars.items():
        if not isinstance(value, dict):
            continue
        entries[str(key)] = {
            "path": str(value.get("path", "")),
            "status": str(value.get("status", "")),
        }
    return entries


def validate_sidecar_set(analysis_dir: Path) -> list[str]:
    findings: list[str] = []
    summary_path = analysis_dir / "program-analysis-summary.yaml"
    if not summary_path.is_file():
        findings.append("Missing required file: program-analysis-summary.yaml")
        return findings

    entries = sidecar_entries(summary_path)
    for key in CORE_SIDECAR_KEYS:
        entry = entries.get(key)
        if not entry:
            findings.append(f"program-analysis-summary.yaml missing sidecar declaration: {key}")
            continue
        rel_path = entry.get("path")
        status = entry.get("status")
        if status != "present":
            findings.append(f"core sidecar {key} must have status present, found {status or 'missing'}")
        if rel_path and not (analysis_dir / rel_path).is_file():
            findings.append(f"declared core sidecar file is missing: {rel_path}")

    for key, entry in entries.items():
        status = entry.get("status", "")
        rel_path = entry.get("path", "")
        if status in {"present", "optional_triggered"} and rel_path and not (analysis_dir / rel_path).is_file():
            findings.append(f"declared sidecar {key} is {status} but file is missing: {rel_path}")

    return findings


def message_inventory_payload(analysis_dir: Path) -> dict[str, Any]:
    path = analysis_dir / "message-inventory.yaml"
    if not path.is_file():
        return {}
    payload = load_yaml(path)
    inventory = (payload or {}).get("message_inventory", {})
    return inventory if isinstance(inventory, dict) else {}


def message_entries(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    details = inventory.get("details", [])
    if isinstance(details, list) and details:
        return [entry for entry in details if isinstance(entry, dict)]
    summary = inventory.get("summary", [])
    if isinstance(summary, list):
        return [entry for entry in summary if isinstance(entry, dict)]
    return []


def has_unresolved_message_description(entry: dict[str, Any]) -> bool:
    description = str(
        entry.get("short_description")
        or entry.get("message_description")
        or entry.get("description")
        or ""
    ).strip().lower()
    description_source = str(entry.get("description_source") or "").strip().lower()
    evidence_status = str(entry.get("evidence_status") or "").strip().lower()
    if description == UNRESOLVED_MESSAGE_DESCRIPTION:
        return True
    if description_source in UNRESOLVED_DESCRIPTION_SOURCES:
        return True
    if evidence_status in UNRESOLVED_DESCRIPTION_STATUSES:
        return True
    return False


def validate_message_descriptions(analysis_dir: Path) -> list[str]:
    inventory = message_inventory_payload(analysis_dir)
    if not inventory:
        return []
    unresolved = [
        str(entry.get("message") or entry.get("message_code") or entry.get("code") or "unknown")
        for entry in message_entries(inventory)
        if has_unresolved_message_description(entry)
    ]
    unresolved = sorted(set(unresolved))
    if not unresolved:
        return []
    return [
        "message descriptions unresolved for observed message/status/code values: "
        + ", ".join(unresolved)
        + ". Provide message file/catalog/reference pack, source literal/comment, "
        "runtime evidence, or SME-approved descriptions before final delivery."
    ]


def observed_message_codes(analysis_dir: Path) -> list[str]:
    inventory = message_inventory_payload(analysis_dir)
    if not inventory:
        return []
    codes: list[str] = []
    for entry in message_entries(inventory):
        value = entry.get("message") or entry.get("message_code") or entry.get("code")
        if value:
            codes.append(str(value))
    return sorted(set(codes))


def validate_message_inventory_sync(program_markdown: str, analysis_dir: Path) -> list[str]:
    codes = observed_message_codes(analysis_dir)
    if not codes:
        return []

    message_section = h2_section_text(program_markdown, "Message Inventory")
    missing = [code for code in codes if code not in message_section]
    if not missing:
        return []
    return [
        "program-analysis.md Message Inventory missing observed YAML message/code values: "
        + ", ".join(missing)
    ]


def validate(analysis_dir: Path, program_analysis: Path | None = None) -> list[str]:
    findings: list[str] = []
    if not analysis_dir.is_dir():
        return [f"Analysis directory does not exist: {analysis_dir}"]

    program_path = find_program_analysis_path(analysis_dir, program_analysis)
    if program_path is None or not program_path.is_file():
        findings.append("Missing program-analysis.md or a single program-analysis-<OBJ-ID>.md")
    else:
        program_markdown = read_text(program_path)
        findings.extend(validate_required_sections(program_markdown))
        findings.extend(validate_program_rlog_coverage(program_markdown, analysis_dir))
        findings.extend(validate_core_logic_routine_indexes(program_markdown, analysis_dir))
        findings.extend(validate_reader_first_golden_gate(program_markdown, analysis_dir))
        findings.extend(validate_no_stale_gap_wording(program_markdown))
        findings.extend(validate_message_inventory_sync(program_markdown, analysis_dir))

    findings.extend(validate_sidecar_set(analysis_dir))
    findings.extend(validate_rlog_coverage(analysis_dir))
    findings.extend(validate_large_program_batches(analysis_dir))
    findings.extend(validate_routine_detail_review_surfaces(analysis_dir))
    findings.extend(validate_message_descriptions(analysis_dir))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate legacy-ibmi-program-analyzer artifact contract completeness."
    )
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--program-analysis", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        findings = validate(args.analysis_dir, args.program_analysis)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1

    print("Program analysis contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
