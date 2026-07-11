#!/usr/bin/env python3
"""Merge parallel sub-agent result JSON files into batch state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from initialize_program_batch import (  # noqa: E402
    build_manifest,
    read_csv,
    render_plan,
    to_yaml,
    write_csv,
)


ALLOWED_BATCH_STATUSES = {
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

ALLOWED_VALIDATOR_STATUSES = {
    "not_run",
    "deferred",
    "pass",
    "pass_with_warnings",
    "failed",
}


def unquote_scalar(value: str) -> Any:
    text = value.strip()
    if text == "null":
        return None
    if text == '""':
        return ""
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if text.isdigit():
        return int(text)
    return text


def read_manifest_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    current_list_key: str | None = None
    if not path.is_file():
        return metadata

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if not raw_line.startswith(" ") and ":" in line:
            key, raw_value = line.split(":", 1)
            key = key.strip()
            value = raw_value.strip()
            if key == "programs":
                current_list_key = None
                break
            if value:
                metadata[key] = unquote_scalar(value)
                current_list_key = None
            else:
                metadata[key] = []
                current_list_key = key
            continue
        if current_list_key and raw_line.startswith("  - "):
            metadata.setdefault(current_list_key, []).append(unquote_scalar(raw_line[4:]))
    return metadata


def load_result(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid result JSON {path}: {error}") from error
    if not isinstance(result, dict):
        raise SystemExit(f"Invalid result JSON {path}: root must be an object")
    member = str(result.get("member", "")).strip()
    if not member:
        raise SystemExit(f"Invalid result JSON {path}: missing member")
    batch_status = str(result.get("batch_status", "")).strip()
    validator_status = str(result.get("validator_status", "")).strip()
    if batch_status not in ALLOWED_BATCH_STATUSES:
        raise SystemExit(f"Invalid result JSON {path}: unsupported batch_status {batch_status!r}")
    if validator_status not in ALLOWED_VALIDATOR_STATUSES:
        raise SystemExit(
            f"Invalid result JSON {path}: unsupported validator_status {validator_status!r}"
        )
    return result


def merge_results(batch_dir: Path, results_dir: Path) -> int:
    status_path = batch_dir / "program-list-status.csv"
    manifest_path = batch_dir / "batch-scan-manifest.yaml"
    if not status_path.is_file():
        raise SystemExit(f"Missing status CSV: {status_path}")
    if not results_dir.is_dir():
        raise SystemExit(f"Missing sub-agent results directory: {results_dir}")

    fieldnames, rows = read_csv(status_path)
    for column in (
        "batch_status",
        "validator_status",
        "subagent_result_path",
        "owner",
        "session_id",
        "completed_at",
        "last_error",
        "next_action",
    ):
        if column not in fieldnames:
            fieldnames.append(column)

    by_member = {
        (row.get("member") or "").strip().upper(): row
        for row in rows
        if (row.get("member") or "").strip()
    }
    result_paths = sorted(results_dir.glob("*.json"))
    if not result_paths:
        raise SystemExit(f"No sub-agent result JSON files found in {results_dir}")

    merged_count = 0
    for result_path in result_paths:
        result = load_result(result_path)
        member_key = str(result["member"]).strip().upper()
        row = by_member.get(member_key)
        if row is None:
            raise SystemExit(
                f"Result {result_path} names member {result['member']!r}, "
                "but that member is not present in program-list-status.csv"
            )
        row["batch_status"] = str(result["batch_status"])
        row["validator_status"] = str(result["validator_status"])
        row["completed_at"] = str(result.get("completed_at") or "")
        row["last_error"] = str(result.get("last_error") or "")
        row["next_action"] = str(result.get("next_action") or "")
        row["subagent_result_path"] = str(result_path)
        row["owner"] = str(result.get("owner") or "subagent")
        row["session_id"] = str(result.get("session_id") or result_path.stem)
        if result.get("output_dir"):
            row["output_dir"] = str(result["output_dir"])
        merged_count += 1

    write_csv(status_path, fieldnames, rows)

    metadata = read_manifest_metadata(manifest_path)
    review_name = str(metadata.get("review_name") or "program list batch")
    program_list = Path(str(metadata.get("program_list") or batch_dir / "program-list.csv"))
    validation_mode = str(metadata.get("validation_mode") or "immediate")
    scaffold_mode = str(metadata.get("scaffold_mode") or "none")
    subagent_mode = str(metadata.get("subagent_mode") or "prepare")
    max_parallel_agents = int(metadata.get("max_parallel_agents") or 4)
    source_root = metadata.get("source_root")
    output_root = metadata.get("output_root")
    reference_paths = [str(item) for item in metadata.get("reference_paths", [])]
    control_files = [str(item) for item in metadata.get("control_files", [])]

    plan = render_plan(
        review_name=review_name,
        program_list=program_list,
        out_dir=batch_dir,
        rows=rows,
        source_root=None if source_root is None else str(source_root),
        delivery_root=None if output_root is None else str(output_root),
        validation_mode=validation_mode,
        scaffold_mode=scaffold_mode,
        subagent_mode=subagent_mode,
        max_parallel_agents=max_parallel_agents,
        reference_paths=reference_paths,
        control_files=control_files,
    )
    (batch_dir / "program-batch-plan.md").write_text(plan, encoding="utf-8")

    manifest = build_manifest(
        review_name=review_name,
        program_list=program_list,
        out_dir=batch_dir,
        rows=rows,
        source_root=None if source_root is None else str(source_root),
        delivery_root=None if output_root is None else str(output_root),
        validation_mode=validation_mode,
        scaffold_mode=scaffold_mode,
        subagent_mode=subagent_mode,
        max_parallel_agents=max_parallel_agents,
        reference_paths=reference_paths,
        control_files=control_files,
    )
    if metadata.get("created_at"):
        manifest["created_at"] = metadata["created_at"]
    manifest["status"] = "subagent_results_merged"
    manifest["merged_result_count"] = merged_count
    manifest["subagent_results_dir"] = str(results_dir)
    manifest_path.write_text(to_yaml(manifest) + "\n", encoding="utf-8")
    return merged_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", required=True, help="Program-list batch directory")
    parser.add_argument(
        "--results-dir",
        help="Sub-agent results directory. Defaults to <batch-dir>/subagent-results",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    batch_dir = Path(args.batch_dir).resolve()
    results_dir = Path(args.results_dir).resolve() if args.results_dir else batch_dir / "subagent-results"
    merged_count = merge_results(batch_dir, results_dir)
    print(f"Merged sub-agent result files: {merged_count}")
    print(f"Updated status CSV: {batch_dir / 'program-list-status.csv'}")
    print(f"Updated manifest: {batch_dir / 'batch-scan-manifest.yaml'}")


if __name__ == "__main__":
    main()
