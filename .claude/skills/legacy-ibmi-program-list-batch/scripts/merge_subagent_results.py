#!/usr/bin/env python3
"""Merge parallel sub-agent result JSON files into batch state."""

from __future__ import annotations

import argparse
import json
import subprocess
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


def analyzer_validator_path() -> Path:
    return (
        SCRIPT_DIR.parent.parent
        / "legacy-ibmi-program-analyzer"
        / "scripts"
        / "validate_program_analysis_contract.py"
    )


def resolve_output_dir(value: str, output_root: Any) -> Path:
    output_path = Path(value)
    if output_path.is_absolute():
        return output_path
    if output_root:
        return Path(str(output_root)) / output_path
    return output_path


def run_program_validator(output_dir: Path) -> tuple[bool, str]:
    validator = analyzer_validator_path()
    if not validator.is_file():
        return False, f"program_analysis_validator_not_found: {validator}"
    if not output_dir.is_dir():
        return False, f"program_output_directory_missing: {output_dir}"

    result = subprocess.run(
        [sys.executable, str(validator), "--analysis-dir", str(output_dir)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr or result.stdout or f"exit {result.returncode}").strip()
    detail = "\n".join(detail.splitlines()[-20:])
    return False, detail


def apply_parent_validation_gate(
    result: dict[str, Any],
    *,
    validation_mode: str,
    output_root: Any,
) -> dict[str, Any]:
    """Revalidate successful worker outputs before merging shared state."""

    if validation_mode != "immediate":
        return result
    if result.get("batch_status") in {
        "blocked_missing_source",
        "failed_runtime",
        "failed_validator",
        "skipped_not_program",
    }:
        return result

    result = dict(result)
    claimed_status = str(result.get("batch_status") or "")
    claimed_validator = str(result.get("validator_status") or "")
    if claimed_status == "scanned_unvalidated" or claimed_validator not in {
        "pass",
        "pass_with_warnings",
    }:
        result["batch_status"] = "failed_validator"
        result["validator_status"] = "failed"
        result["last_error"] = (
            "parallel_merge_validator_failed: worker did not report an immediate "
            f"validator pass (batch_status={claimed_status}, "
            f"validator_status={claimed_validator})"
        )
        result["next_action"] = "Repair this program and rerun the Kiro worker before merging."
        return result

    output_value = str(result.get("output_dir") or "").strip()
    if not output_value:
        passed, detail = False, "worker_result_missing_output_dir"
    else:
        passed, detail = run_program_validator(
            resolve_output_dir(output_value, output_root)
        )
    if not passed:
        result["batch_status"] = "failed_validator"
        result["validator_status"] = "failed"
        result["last_error"] = "parallel_merge_validator_failed: " + detail
        result["next_action"] = "Repair this program and rerun the Kiro worker before merging."
    return result


def merge_results(batch_dir: Path, results_dir: Path) -> int:
    status_path = batch_dir / "program-list-status.csv"
    manifest_path = batch_dir / "batch-scan-manifest.yaml"
    if not status_path.is_file():
        raise SystemExit(f"Missing status CSV: {status_path}")
    if not results_dir.is_dir():
        raise SystemExit(f"Missing sub-agent results directory: {results_dir}")

    metadata = read_manifest_metadata(manifest_path)
    validation_mode = str(metadata.get("validation_mode") or "immediate")
    subagent_mode = str(metadata.get("subagent_mode") or "prepare")
    output_root = metadata.get("output_root")
    if subagent_mode == "prepare" and validation_mode != "immediate":
        raise SystemExit(
            "Kiro/parallel sub-agent merge requires validation_mode=immediate. "
            "Reinitialize the batch with --validation-mode immediate."
        )

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
        result = apply_parent_validation_gate(
            load_result(result_path),
            validation_mode=validation_mode,
            output_root=output_root,
        )
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

    review_name = str(metadata.get("review_name") or "program list batch")
    program_list = Path(str(metadata.get("program_list") or batch_dir / "program-list.csv"))
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
