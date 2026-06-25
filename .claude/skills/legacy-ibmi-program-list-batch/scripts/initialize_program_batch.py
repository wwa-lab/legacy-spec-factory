#!/usr/bin/env python3
"""Initialize a Copilot Chat-friendly IBM i program-list batch."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_COLUMNS = [
    "batch_status",
    "validator_status",
    "output_dir",
    "prompt_path",
    "owner",
    "session_id",
    "started_at",
    "completed_at",
    "last_error",
    "next_action",
    "handoff_path",
]

TIER_ROOTS = {
    "normal_program": "modules/CAP-ID-0003-normal_program",
    "complex_normal_program": "modules/CAP-ID-0002-complex_normal_program",
    "large_extreme_program": "modules/CAP-ID-0001-large_extreme_program",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def scalar_to_yaml(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    safe = all(ch.isalnum() or ch in "_./:@#$%+*-, <>[]" for ch in text)
    if safe and text.lower() not in {"true", "false", "null"}:
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_yaml(value: Any, indent: int = 0) -> str:
    pad = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {scalar_to_yaml(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {scalar_to_yaml(item)}")
    else:
        lines.append(f"{pad}{scalar_to_yaml(value)}")
    return "\n".join(lines)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: value for key, value in row.items() if key is not None} for row in reader]
        return list(reader.fieldnames or []), rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9@._-]+", "_", value.strip())
    return cleaned or "program"


def join_display(root: str | None, *parts: str) -> str:
    if root:
        return str(Path(root, *parts))
    return "/".join(["<delivery-root>", *parts])


def source_display(source_root: str | None, source_path: str) -> str:
    if source_root:
        return str(Path(source_root, source_path))
    return f"<source-root>/{source_path}"


def tier_root(size_tier: str) -> str:
    return TIER_ROOTS.get(size_tier.strip(), TIER_ROOTS["normal_program"])


def render_prompt(
    *,
    template: str,
    program_list: Path,
    out_dir: Path,
    row: dict[str, str],
    source_root: str | None,
    delivery_root: str | None,
    intent: str,
    python_launcher: str,
) -> str:
    replacements = {
        "program_list": str(program_list),
        "program_batch_plan": str(out_dir / "program-batch-plan.md"),
        "program_list_status": str(out_dir / "program-list-status.csv"),
        "batch_manifest": str(out_dir / "batch-scan-manifest.yaml"),
        "member": row.get("member", ""),
        "source_path": source_display(source_root, row.get("path", "")),
        "source_kind": row.get("source_kind", ""),
        "size_tier": row.get("size_tier", ""),
        "intent": intent,
        "output_dir": row.get("output_dir", ""),
        "python_launcher": python_launcher,
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def markdown_table_row(index: int, row: dict[str, str]) -> str:
    return (
        f"| {index} | {row.get('member', '')} | {row.get('path', '')} | "
        f"{row.get('size_tier', '')} | {row.get('batch_status', '')} | "
        f"{row.get('validator_status', '')} | {row.get('owner', '')} | "
        f"{row.get('output_dir', '')} | {row.get('next_action', '')} |"
    )


def render_plan(
    *,
    review_name: str,
    program_list: Path,
    out_dir: Path,
    rows: list[dict[str, str]],
    source_root: str | None,
    delivery_root: str | None,
) -> str:
    counts = Counter(row.get("batch_status", "") for row in rows)
    blocked_count = sum(counts[value] for value in counts if value.startswith("blocked_"))
    failed_count = sum(counts[value] for value in counts if value.startswith("failed_"))
    next_row = next((row for row in rows if row.get("batch_status") == "queued"), None)
    queue_rows = "\n".join(markdown_table_row(index, row) for index, row in enumerate(rows, start=1))
    blockers = [
        f"| {row.get('member', '')} | {row.get('last_error', '')} | {row.get('next_action', '')} |"
        for row in rows
        if row.get("batch_status", "").startswith(("blocked_", "failed_"))
    ]
    blocker_rows = "\n".join(blockers) if blockers else "|  |  |  |"
    return f"""# Program Batch Plan

## Batch

- Review name: {review_name}
- Program list: {program_list}
- Status list: {out_dir / "program-list-status.csv"}
- Manifest: {out_dir / "batch-scan-manifest.yaml"}
- Source root: {source_root or ""}
- Output root: {delivery_root or ""}
- Mode: Copilot Chat-only / one program per chat

## Progress

| Status | Count |
| --- | ---: |
| queued | {counts["queued"]} |
| in_progress | {counts["in_progress"]} |
| completed | {counts["completed"]} |
| completed_with_warnings | {counts["completed_with_warnings"]} |
| blocked | {blocked_count} |
| failed | {failed_count} |
| skipped_not_program | {counts["skipped_not_program"]} |

## Current / Next

- Current program: none
- Current owner/session: none
- Next program: {next_row.get("member", "") if next_row else "none"}
- Next prompt: {next_row.get("prompt_path", "") if next_row else "none"}
- Next action: {next_row.get("next_action", "none") if next_row else "none"}

## Program Queue

| # | Program | Source | Tier | Status | Validator | Owner | Output | Next action |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
{queue_rows}

## Blockers

| Program | Blocker | Needed to unblock |
| --- | --- | --- |
{blocker_rows}
"""


def build_manifest(
    *,
    review_name: str,
    program_list: Path,
    out_dir: Path,
    rows: list[dict[str, str]],
    source_root: str | None,
    delivery_root: str | None,
) -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "batch_id": safe_filename(review_name.lower()).strip("_") or "program_list_batch",
        "review_name": review_name,
        "program_list": str(program_list),
        "status_list": str(out_dir / "program-list-status.csv"),
        "program_batch_plan": str(out_dir / "program-batch-plan.md"),
        "source_root": source_root,
        "output_root": delivery_root,
        "created_at": timestamp,
        "updated_at": timestamp,
        "status": "initialized",
        "programs": [
            {
                "order": index,
                "member": row.get("member", ""),
                "object_type": row.get("object_type", ""),
                "source_kind": row.get("source_kind", ""),
                "source_path": row.get("path", ""),
                "initial_size_tier": row.get("size_tier", ""),
                "tier_reason": row.get("tier_reason", ""),
                "batch_status": row.get("batch_status", ""),
                "validator_status": row.get("validator_status", ""),
                "output_dir": row.get("output_dir", ""),
                "prompt_path": row.get("prompt_path", ""),
                "next_action": row.get("next_action", ""),
            }
            for index, row in enumerate(rows, start=1)
        ],
    }


def initialize(args: argparse.Namespace) -> None:
    program_list = Path(args.program_list).resolve()
    out_dir = Path(args.out_dir).resolve()
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        raise SystemExit(f"Output directory is not empty. Use --force to overwrite generated files: {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir = out_dir / "prompt-queue"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "completed").mkdir(exist_ok=True)
    (out_dir / "blocked").mkdir(exist_ok=True)
    (out_dir / "failed").mkdir(exist_ok=True)

    fieldnames, rows = read_csv(program_list)
    if "member" not in fieldnames:
        raise SystemExit("program-list.csv must include a 'member' column")

    status_fieldnames = list(fieldnames)
    for column in STATUS_COLUMNS:
        if column not in status_fieldnames:
            status_fieldnames.append(column)

    template_path = Path(__file__).resolve().parents[1] / "templates" / "copilot-single-program-prompt.md"
    prompt_template = template_path.read_text(encoding="utf-8")

    status_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        normalized = {key: (value or "").strip() for key, value in row.items()}
        member = normalized.get("member", "")
        object_type = normalized.get("object_type", "")
        size_tier = normalized.get("size_tier", "")
        is_program = object_type.lower() == "program"
        output_dir = join_display(args.delivery_root, tier_root(size_tier), member) if member and is_program else ""
        prompt_path = ""
        if is_program:
            prompt_path = str(prompt_dir / f"{index:04d}-{safe_filename(member)}.md")
            batch_status = "queued"
            next_action = "start scan"
        else:
            batch_status = "skipped_not_program"
            next_action = "none - row is not a program"
        normalized.update(
            {
                "batch_status": batch_status,
                "validator_status": "not_run",
                "output_dir": output_dir,
                "prompt_path": prompt_path,
                "owner": "",
                "session_id": "",
                "started_at": "",
                "completed_at": "",
                "last_error": "",
                "next_action": next_action,
                "handoff_path": "",
            }
        )
        status_rows.append(normalized)
        if prompt_path:
            Path(prompt_path).write_text(
                render_prompt(
                    template=prompt_template,
                    program_list=program_list,
                    out_dir=out_dir,
                    row=normalized,
                    source_root=args.source_root,
                    delivery_root=args.delivery_root,
                    intent=args.intent,
                    python_launcher=args.python_launcher,
                ),
                encoding="utf-8",
            )

    write_csv(out_dir / "program-list-status.csv", status_fieldnames, status_rows)
    (out_dir / "program-batch-plan.md").write_text(
        render_plan(
            review_name=args.review_name,
            program_list=program_list,
            out_dir=out_dir,
            rows=status_rows,
            source_root=args.source_root,
            delivery_root=args.delivery_root,
        ),
        encoding="utf-8",
    )
    manifest = build_manifest(
        review_name=args.review_name,
        program_list=program_list,
        out_dir=out_dir,
        rows=status_rows,
        source_root=args.source_root,
        delivery_root=args.delivery_root,
    )
    (out_dir / "batch-scan-manifest.yaml").write_text(to_yaml(manifest) + "\n", encoding="utf-8")
    print(f"Initialized program batch: {out_dir}")
    print(f"Prompt files: {len(list(prompt_dir.glob('*.md')))}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program-list", required=True, help="Input program-list.csv")
    parser.add_argument("--out-dir", required=True, help="Output batch directory")
    parser.add_argument("--source-root", help="Source repository root")
    parser.add_argument("--delivery-root", help="Output root for generated per-program artifacts; no checkout is required")
    parser.add_argument("--delivery-profile", help=argparse.SUPPRESS)
    parser.add_argument("--delivery-main-snapshot", help=argparse.SUPPRESS)
    parser.add_argument("--review-name", default="program list batch", help="Human-readable batch name")
    parser.add_argument("--intent", default="standalone_exploratory")
    parser.add_argument("--python-launcher", default="py -3")
    parser.add_argument("--force", action="store_true", help="Overwrite generated files in an existing output directory")
    return parser


if __name__ == "__main__":
    initialize(build_parser().parse_args())
