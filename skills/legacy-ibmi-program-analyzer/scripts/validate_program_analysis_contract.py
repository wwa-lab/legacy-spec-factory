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

RLOG_RE = re.compile(r"\bRLOG-[A-Z0-9_#$@-]+-\d{3}\b", re.I)


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

    missing = sorted(set(yaml_ids) - set(markdown_ids))
    if missing:
        findings.append(
            "routine-logic-details.md missing RLOG IDs declared in YAML: "
            + ", ".join(missing)
        )

    return findings


def batch_detail_files(analysis_dir: Path) -> list[Path]:
    batch_dir = analysis_dir / "routine-logic-details"
    if not batch_dir.is_dir():
        return []
    patterns = ("part-*.md", "deep-read-batch-*.md")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(batch_dir.glob(pattern))
    return sorted(set(files))


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
            validate_ordered_headings(
                batch_text,
                BATCH_CORE_SECTIONS,
                batch_label,
            )
        )
        positions = heading_positions(batch_text)
        first_core_position = min(positions[heading] for heading in BATCH_CORE_SECTIONS if heading in positions)
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


def validate(analysis_dir: Path, program_analysis: Path | None = None) -> list[str]:
    findings: list[str] = []
    if not analysis_dir.is_dir():
        return [f"Analysis directory does not exist: {analysis_dir}"]

    program_path = find_program_analysis_path(analysis_dir, program_analysis)
    if program_path is None or not program_path.is_file():
        findings.append("Missing program-analysis.md or a single program-analysis-<OBJ-ID>.md")
    else:
        findings.extend(validate_required_sections(read_text(program_path)))

    findings.extend(validate_sidecar_set(analysis_dir))
    findings.extend(validate_rlog_coverage(analysis_dir))
    findings.extend(validate_routine_detail_review_surfaces(analysis_dir))
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
