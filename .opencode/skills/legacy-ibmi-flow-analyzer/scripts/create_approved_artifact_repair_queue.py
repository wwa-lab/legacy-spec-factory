#!/usr/bin/env python3
"""Create one isolated repair prompt per failed approved-repo program.

The queue consumes a requalification report. It never edits the approved
repository and never creates a prompt for an ambiguous or untrusted artifact
root; those rows remain in ``blocked-programs.csv`` for human resolution.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import requalify_approved_program_artifacts as requalifier  # noqa: E402


QUEUE_SCHEMA_VERSION = "0.1"
PROMPT_TEMPLATE = (
    SCRIPT_DIR.parent / "templates" / "legacy-artifact-repair-prompt.md"
)


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = requalifier.BUILDER.load_yaml(path)
    if not isinstance(payload, dict):
        raise ValueError(f"report must contain a mapping: {path}")
    return payload


def _safe_filename(program: str) -> str:
    value = str(program).strip().upper()
    return requalifier.BUILDER.slugify(value) or "program"


def _csv_write(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _list_text(values: Any) -> str:
    if not isinstance(values, list):
        return "- None recorded"
    return "\n".join(f"- {str(value)}" for value in values) or "- None recorded"


def render_prompt(item: dict[str, Any], template_text: str) -> str:
    replacements = {
        "PROGRAM": item.get("program", ""),
        "STATUS": item.get("status", ""),
        "TIER": item.get("tier") or "unknown",
        "ARTIFACT_ROOT": item.get("artifact_root", ""),
        "SOURCE_INDEX_SHA256": item.get("source_index_sha256") or "missing",
        "EXECUTION_PLAN_SHA256": item.get("execution_plan_sha256") or "missing",
        "FINDING_CODES": ", ".join(item.get("finding_codes") or []) or "none",
        "FINDINGS": _list_text(item.get("findings")),
        "REPAIR_ACTIONS": _list_text(item.get("repair_actions")),
    }
    rendered = template_text
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered.rstrip() + "\n"


def build_queue(report: dict[str, Any], out_dir: Path, template_path: Path) -> dict[str, Any]:
    programs = [
        item for item in report.get("programs", [])
        if isinstance(item, dict)
    ]
    programs.sort(key=lambda item: (str(item.get("program", "")).upper(), str(item.get("artifact_root", ""))))
    prompt_items = [item for item in programs if item.get("status") not in {"final_ready", "blocked"}]
    blocked_items = [item for item in programs if item.get("status") == "blocked"]
    template_text = template_path.read_text(encoding="utf-8")
    prompt_dir = out_dir / "prompt-queue"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_paths: list[str] = []
    for item in prompt_items:
        program = str(item.get("program") or "PROGRAM")
        path = prompt_dir / f"{_safe_filename(program)}-repair.md"
        path.write_text(render_prompt(item, template_text), encoding="utf-8")
        prompt_paths.append(path.relative_to(out_dir).as_posix())

    fields = ["program", "status", "artifact_root", "tier", "finding_codes", "findings"]
    rows = [
        {
            **item,
            "finding_codes": "; ".join(item.get("finding_codes") or []),
            "findings": " | ".join(item.get("findings") or []),
        }
        for item in prompt_items
    ]
    _csv_write(out_dir / "repairable-programs.csv", rows, fields)
    _csv_write(
        out_dir / "blocked-programs.csv",
        [
            {
                **item,
                "finding_codes": "; ".join(item.get("finding_codes") or []),
                "findings": " | ".join(item.get("findings") or []),
            }
            for item in blocked_items
        ],
        fields,
    )

    status_rows = []
    for item in programs:
        status = "complete_not_queued" if item.get("status") == "final_ready" else (
            "blocked_manual_resolution" if item.get("status") == "blocked" else "queued"
        )
        status_rows.append(
            {
                "program": item.get("program"),
                "artifact_root": item.get("artifact_root"),
                "requalification_status": item.get("status"),
                "repair_status": status,
                "prompt_path": (
                    f"prompt-queue/{_safe_filename(str(item.get('program') or 'PROGRAM'))}-repair.md"
                    if item in prompt_items else None
                ),
                "finding_codes": item.get("finding_codes") or [],
            }
        )
    status_payload = {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "generated_by": "create_approved_artifact_repair_queue.py",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_report": report.get("artifact_root"),
        "programs": status_rows,
    }
    (out_dir / "repair-status.yaml").write_text(
        requalifier.BUILDER.dump_yaml(status_payload), encoding="utf-8"
    )

    summary = report.get("summary", {}) or {}
    plan_lines = [
        "# Approved Artifact Repair Plan",
        "",
        "This queue is generated from a read-only requalification report.",
        "Each repair prompt owns exactly one program artifact directory.",
        "",
        "## Safety contract",
        "",
        "- Work in an isolated repair branch or working clone; do not edit approved main in place.",
        "- Do not rescan the whole repository and do not create a program-set SME review from this queue.",
        "- Preserve exact source literals, source hashes, provenance, and existing valid evidence.",
        "- A blocked row has no prompt until its identity/trust/path ambiguity is resolved.",
        "",
        "## Inventory summary",
        "",
        f"- Total candidates: {summary.get('total_candidates', len(programs))}",
        f"- Final compatible: {summary.get('final_ready', 0)}",
        f"- Core compatible with pending work: {summary.get('core_reader_ready_pending', 0)}",
        f"- Format repairable: {summary.get('format_repairable', 0)}",
        f"- Semantic repair required: {summary.get('semantic_repair_required', 0)}",
        f"- Blocked/manual resolution: {summary.get('blocked', 0)}",
        "",
        "## Queue contents",
        "",
        f"- `prompt-queue/`: {len(prompt_items)} one-program repair prompts.",
        "- `repairable-programs.csv`: deterministic repair worklist.",
        "- `blocked-programs.csv`: rows that require human resolution before prompting.",
        "- `repair-status.yaml`: resumable status ledger; workers must update only their program row.",
        "",
    ]
    (out_dir / "repair-plan.md").write_text("\n".join(plan_lines), encoding="utf-8")
    return {
        "repair_prompts": len(prompt_items),
        "blocked_programs": len(blocked_items),
        "status_path": (out_dir / "repair-status.yaml").as_posix(),
        "prompt_paths": prompt_paths,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create one program-level repair prompt from a requalification report."
    )
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--template", type=Path, default=PROMPT_TEMPLATE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_path = args.report.resolve()
    template_path = args.template.resolve()
    if not report_path.is_file():
        raise SystemExit(f"requalification report does not exist: {report_path}")
    if not template_path.is_file():
        raise SystemExit(f"repair prompt template does not exist: {template_path}")
    result = build_queue(_load_yaml(report_path), args.out_dir.resolve(), template_path)
    print(f"Created {result['repair_prompts']} program-level repair prompts.")
    print(f"Blocked/manual rows: {result['blocked_programs']}")
    print(f"Queue: {args.out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
