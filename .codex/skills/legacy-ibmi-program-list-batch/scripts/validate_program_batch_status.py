#!/usr/bin/env python3
"""Validate program-list batch status files and completed output folders."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ALLOWED_STATUSES = {
    "queued",
    "in_progress",
    "completed",
    "completed_with_warnings",
    "blocked_missing_source",
    "failed_validator",
    "failed_runtime",
    "skipped_not_program",
}

REQUIRED_ARTIFACTS = {
    "program-analysis.md",
    "source-index.yaml",
    "program-analysis-summary.yaml",
    "routine-index.md",
    "message-inventory.yaml",
}

ROUTINE_DETAIL_REQUIRED_TIERS = {"complex_normal_program", "large_extreme_program"}
ROUTINE_DETAIL_ARTIFACTS = {
    "routine-logic-details.md",
    "routine-logic-details.yaml",
}


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
        if status in {"completed", "completed_with_warnings"}:
            if output_path is None:
                warnings.append(f"Row {index} {member}: cannot verify placeholder/empty output_dir {output_dir_value!r}")
                continue
            if not output_path.is_dir():
                findings.append(f"Row {index} {member}: output_dir does not exist: {output_path}")
                continue
            required_artifacts = set(REQUIRED_ARTIFACTS)
            if row.get("size_tier", "") in ROUTINE_DETAIL_REQUIRED_TIERS:
                required_artifacts.update(ROUTINE_DETAIL_ARTIFACTS)
            missing = sorted(name for name in required_artifacts if not (output_path / name).is_file())
            if missing:
                findings.append(f"Row {index} {member}: missing required artifacts: {', '.join(missing)}")

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
