#!/usr/bin/env python3
"""Validate program-list batch status files and completed output folders."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


ALLOWED_STATUSES = {
    "queued",
    "in_progress",
    "completed",
    "completed_with_warnings",
    "scanned_unvalidated",
    "blocked_missing_source",
    "failed_validator",
    "failed_runtime",
    "skipped_not_program",
}

REQUIRED_ARTIFACT_BASE_NAMES = {
    "program-analysis.md",
    "source-index.yaml",
    "program-analysis-summary.yaml",
    "routine-index.md",
    "message-inventory.yaml",
    "routine-logic-details.md",
    "routine-logic-details.yaml",
}

ARTIFACT_REQUIRED_STATUSES = {"completed", "completed_with_warnings", "scanned_unvalidated"}
ARTIFACT_SAFE_RE = re.compile(r'[\s<>:"/\\|?*]+')
SCAFFOLD_TEXT_BASE_NAMES = ("program-analysis.md", "routine-logic-details.md")
SCAFFOLD_PATTERNS = (
    re.compile(r"\bDraft wrapper seed generated\b", re.I),
    re.compile(r"\bpending reader-oriented summary\b", re.I),
    re.compile(r"\bpending semantic deep-read\b", re.I),
    re.compile(r"\bpending semantic detail\b", re.I),
    re.compile(r"\breplace this placeholder\b", re.I),
    re.compile(r"\bplaceholder content\b", re.I),
    re.compile(r"\bnot-yet-deep-read\b", re.I),
)


def artifact_program_prefix(program_name: str) -> str:
    prefix = ARTIFACT_SAFE_RE.sub("_", program_name.strip().upper())
    prefix = prefix.strip("._-")
    return prefix or "PROGRAM"


def required_artifacts_for_member(member: str) -> set[str]:
    prefix = artifact_program_prefix(member)
    return {f"{prefix}-{base_name}" for base_name in REQUIRED_ARTIFACT_BASE_NAMES}


def required_artifact_for_member(member: str, base_name: str) -> str:
    return f"{artifact_program_prefix(member)}-{base_name}"


def scaffold_patterns_in(text: str) -> list[str]:
    return [pattern.pattern.replace("\\b", "") for pattern in SCAFFOLD_PATTERNS if pattern.search(text)]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in csv.DictReader(handle)
        ]


def resolve_output_dir(value: str, delivery_root: Path | None) -> Path | None:
    if not value or "<delivery-root>" in value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    if delivery_root:
        return delivery_root / path
    return path


def validate(args: argparse.Namespace) -> int:
    batch_dir = Path(args.batch_dir).resolve()
    status_path = Path(args.status_list).resolve() if args.status_list else batch_dir / "program-list-status.csv"
    manifest_path = batch_dir / "batch-scan-manifest.yaml"
    plan_path = batch_dir / "program-batch-plan.md"
    delivery_root = Path(args.delivery_root).resolve() if args.delivery_root else None

    findings: list[str] = []
    warnings: list[str] = []

    if not status_path.is_file():
        findings.append(f"Missing status CSV: {status_path}")
        rows: list[dict[str, str]] = []
    else:
        rows = read_csv(status_path)

    if not manifest_path.is_file():
        findings.append(f"Missing batch manifest: {manifest_path}")
    if not plan_path.is_file():
        findings.append(f"Missing program batch plan: {plan_path}")

    seen_members: dict[str, int] = {}
    output_dirs: dict[str, str] = {}
    for index, row in enumerate(rows, start=1):
        member = row.get("member", "")
        status = row.get("batch_status", "")
        validator_status = row.get("validator_status", "")
        output_dir_value = row.get("output_dir", "")
        if not member:
            findings.append(f"Row {index}: missing member")
        elif member in seen_members:
            warnings.append(f"Duplicate member {member!r} at rows {seen_members[member]} and {index}")
        else:
            seen_members[member] = index

        if status not in ALLOWED_STATUSES:
            findings.append(f"Row {index} {member}: invalid batch_status {status!r}")

        if status == "in_progress" and not row.get("owner") and not row.get("session_id"):
            warnings.append(f"Row {index} {member}: in_progress without owner/session_id")

        if status in {"blocked_missing_source", "failed_validator", "failed_runtime"}:
            if not row.get("last_error"):
                findings.append(f"Row {index} {member}: {status} requires last_error")
            if not row.get("next_action"):
                findings.append(f"Row {index} {member}: {status} requires next_action")

        output_path = resolve_output_dir(output_dir_value, delivery_root)
        if output_dir_value and "<delivery-root>" not in output_dir_value:
            if output_dir_value in output_dirs and status not in {"skipped_not_program"}:
                findings.append(
                    f"Rows for {output_dirs[output_dir_value]} and {member} share output_dir {output_dir_value}"
                )
            output_dirs[output_dir_value] = member

        if status == "completed" and validator_status != "pass":
            findings.append(f"Row {index} {member}: completed requires validator_status pass")
        if status == "completed_with_warnings" and validator_status not in {"pass", "pass_with_warnings"}:
            findings.append(
                f"Row {index} {member}: completed_with_warnings requires validator_status pass/pass_with_warnings"
            )
        if status == "scanned_unvalidated" and validator_status != "deferred":
            findings.append(f"Row {index} {member}: scanned_unvalidated requires validator_status deferred")
        if status == "scanned_unvalidated" and not row.get("next_action"):
            findings.append(f"Row {index} {member}: scanned_unvalidated requires next_action for final validation")
        if status in ARTIFACT_REQUIRED_STATUSES:
            if output_path is None:
                warnings.append(f"Row {index} {member}: cannot verify placeholder/empty output_dir {output_dir_value!r}")
                continue
            if not output_path.is_dir():
                findings.append(f"Row {index} {member}: output_dir does not exist: {output_path}")
                continue
            expected_artifacts = required_artifacts_for_member(member)
            missing = sorted(name for name in expected_artifacts if not (output_path / name).is_file())
            if missing:
                findings.append(f"Row {index} {member}: missing required artifacts: {', '.join(missing)}")
            for base_name in SCAFFOLD_TEXT_BASE_NAMES:
                artifact_name = required_artifact_for_member(member, base_name)
                artifact_path = output_path / artifact_name
                if not artifact_path.is_file():
                    continue
                text = artifact_path.read_text(encoding="utf-8-sig")
                matches = scaffold_patterns_in(text)
                if matches:
                    findings.append(
                        f"Row {index} {member}: {artifact_name} still appears to be a scaffold "
                        "or pending deep-read artifact; run semantic source deep-read and replace "
                        "placeholder content before marking completed. Matched: "
                        + ", ".join(matches)
                    )

    for warning in warnings:
        print(f"WARNING: {warning}")
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}")
        print(f"Batch status validation failed: {len(findings)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"Batch status validation passed: {len(rows)} row(s), {len(warnings)} warning(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", required=True, help="Program batch directory")
    parser.add_argument("--status-list", help="Override path to program-list-status.csv")
    parser.add_argument("--delivery-root", help="Resolve relative output_dir values under this root")
    return parser


if __name__ == "__main__":
    sys.exit(validate(build_parser().parse_args()))
