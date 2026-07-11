#!/usr/bin/env python3
"""Initialize a Copilot Chat-friendly IBM i program-list batch."""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_COLUMNS = [
    "batch_status",
    "validator_status",
    "scaffold_status",
    "output_dir",
    "prompt_path",
    "subagent_prompt_path",
    "subagent_result_path",
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

VALIDATION_MODES = {"immediate", "deferred"}
SCAFFOLD_MODES = {"none", "precreate"}
SUBAGENT_MODES = {"none", "prepare"}


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


def read_programs_file(path: Path) -> list[str]:
    programs: list[str] = []
    seen: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-", "*")):
            line = line[1:].strip()
        for token in line.replace("=>", "->").split("->"):
            program = token.strip().strip(",;")
            if not program:
                continue
            key = program.upper()
            if key not in seen:
                seen.add(key)
                programs.append(program)
    return programs


def filter_rows_by_programs(
    rows: list[dict[str, str]],
    programs: list[str],
) -> list[dict[str, str]]:
    by_member: dict[str, dict[str, str]] = {}
    for row in rows:
        member = (row.get("member") or "").strip()
        if member:
            by_member.setdefault(member.upper(), row)

    filtered: list[dict[str, str]] = []
    missing: list[str] = []
    for program in programs:
        row = by_member.get(program.upper())
        if row is None:
            missing.append(program)
        else:
            filtered.append(row)

    if missing:
        raise SystemExit(
            "programs-file contains programs not found in program-list.csv: "
            + ", ".join(missing)
        )
    return filtered


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9@._-]+", "_", value.strip())
    return cleaned or "program"


def looks_like_windows_path(value: str) -> bool:
    return "\\" in value or bool(re.match(r"^[A-Za-z]:", value))


def join_display(root: str | None, *parts: str) -> str:
    cleaned_parts = [part.strip("/\\") for part in parts if part]
    if root:
        cleaned_root = root.rstrip("/\\")
        if looks_like_windows_path(root):
            return "\\".join([cleaned_root, *[part.replace("/", "\\") for part in cleaned_parts]])
        return "/".join([cleaned_root, *[part.replace("\\", "/") for part in cleaned_parts]])
    return "/".join(["<delivery-root>", *[part.replace("\\", "/") for part in cleaned_parts]])


def source_display(source_root: str | None, source_path: str) -> str:
    if source_root:
        return join_display(source_root, source_path)
    cleaned_source_path = source_path.strip("/\\")
    return f"<source-root>/{cleaned_source_path}"


def local_join(root: str, relative_path: str) -> Path:
    cleaned_parts = [part for part in re.split(r"[\\/]+", relative_path.strip("/\\")) if part]
    path = Path(root)
    for part in cleaned_parts:
        path = path / part
    return path


def markdown_code(value: str) -> str:
    text = value or ""
    if not text:
        return ""
    return "`" + text.replace("`", "\\`") + "`"


def bullet_list(label: str, values: list[str] | None) -> str:
    cleaned = [value.strip() for value in values or [] if value.strip()]
    if not cleaned:
        return f"- {label}: none provided"
    lines = [f"- {label}:"]
    lines.extend(f"  - {value}" for value in cleaned)
    return "\n".join(lines)


def tier_root(size_tier: str) -> str:
    return TIER_ROOTS.get(size_tier.strip(), TIER_ROOTS["normal_program"])


def validation_policy(mode: str, member: str) -> str:
    scaffold_check = (
        f"- Before writing final row status, open the generated "
        f"{member}-program-analysis.md and {member}-routine-logic-details.md "
        "and confirm they do not contain scaffold language such as `Draft wrapper "
        "seed generated`, `pending semantic deep-read`, `pending semantic detail`, "
        "`placeholder`, `not-yet-deep-read`, or `not deep-read`."
    )
    layout_check = (
        "- Always preserve the reader-first layout headings in the main file: "
        "`### Routine Index For Calculation Logic`, "
        "`### Routine Index For Validation Logic`, and "
        "`### Routine Index For Exception Handling`, in that order under their "
        "corresponding H2 sections. Deferred mode still runs this cheap "
        "structural check; only the expensive semantic validator is deferred."
    )
    if mode == "deferred":
        return "\n".join(
            [
                "- Skip the program-analysis validator in this batch prompt to keep scan throughput high.",
                "- Do not mark this row `completed` or `completed_with_warnings` in deferred mode.",
                scaffold_check,
                layout_check,
                "- If required artifacts exist and the scaffold/layout checks are clean, set "
                "`batch_status=scanned_unvalidated`, `validator_status=deferred`, and "
                "`next_action=run program-analysis validator before downstream use`.",
                "- If required artifacts are missing or scaffold/layout checks remain dirty after one targeted repair pass, "
                "mark `batch_status=failed_validator`, preserve the finding in `last_error`, and set a concrete `next_action`.",
            ]
        )
    return "\n".join(
        [
            "- Run the program-analysis validator immediately after writing this program's artifacts and before starting the next prompt.",
            "- This validation is mandatory for every program in the Cline serial batch; do not use `scanned_unvalidated` in immediate mode.",
            scaffold_check,
            layout_check,
            "- If validation passes, set `batch_status=completed` and `validator_status=pass`. "
            "Use `completed_with_warnings` only when the validator reports pass/pass_with_warnings and the warnings are non-blocking.",
        ]
    )


def validation_command_block(mode: str, output_dir: str) -> str:
    command = (
        "py -3 .agents\\skills\\legacy-ibmi-program-analyzer\\scripts\\"
        f"validate_program_analysis_contract.py --analysis-dir \"{output_dir}\""
    )
    if mode == "deferred":
        return "\n".join(
            [
                "Deferred in this batch prompt. Do not run this command now.",
                "Run before downstream use or final handoff:",
                command,
            ]
        )
    return command


def validation_launcher_note(mode: str) -> str:
    if mode == "deferred":
        first_line = (
            "- When final validation is run later, run the generated `py -3 ...` "
            "command first. If the Python Launcher is unavailable, run the same "
            "command again with `python` replacing `py -3`."
        )
    else:
        first_line = (
            "- Run the generated `py -3 ...` command first. If the Python Launcher "
            "is unavailable, run the same command again with `python` replacing `py -3`."
        )
    return "\n".join(
        [
            first_line,
            "- Do not replace it with PowerShell, `.cmd`, `.ps1`, shell continuations, or `py ... || python ...`.",
            "- A validator failure is a result failure, not a reason to rerun it through another route.",
        ]
    )


def scaffold_prompt_note(scaffold_status: str) -> str:
    if scaffold_status == "present":
        return (
            "- Scaffold artifacts were precreated during batch initialization. "
            "Start by reading the existing source index, routine logic YAML, and "
            "program-analysis seed in the output directory; do not rerun "
            "deterministic indexing unless the scaffold files are missing or stale."
        )
    if scaffold_status.startswith("failed"):
        return (
            "- Scaffold precreation failed during batch initialization. Inspect "
            "program-list-status.csv last_error/next_action before attempting "
            "semantic fill."
        )
    return (
        "- If scaffold artifacts do not already exist, build deterministic indexes first."
    )


def render_prompt(
    *,
    template: str,
    program_list: Path,
    out_dir: Path,
    row: dict[str, str],
    source_root: str | None,
    delivery_root: str | None,
    intent: str,
    validation_mode: str,
    reference_paths: list[str] | None,
    control_files: list[str] | None,
) -> str:
    member = row.get("member", "")
    output_dir = row.get("output_dir", "")
    replacements = {
        "program_list": str(program_list),
        "program_batch_plan": str(out_dir / "program-batch-plan.md"),
        "program_list_status": str(out_dir / "program-list-status.csv"),
        "batch_manifest": str(out_dir / "batch-scan-manifest.yaml"),
        "member": member,
        "source_path": source_display(source_root, row.get("path", "")),
        "source_kind": row.get("source_kind", ""),
        "size_tier": row.get("size_tier", ""),
        "intent": intent,
        "output_dir": output_dir,
        "validation_policy": validation_policy(validation_mode, member),
        "validation_command_block": validation_command_block(validation_mode, output_dir),
        "validation_launcher_note": validation_launcher_note(validation_mode),
        "scaffold_prompt_note": scaffold_prompt_note(row.get("scaffold_status", "")),
        "reference_paths": bullet_list("Reference paths", reference_paths),
        "control_files": bullet_list("Control files", control_files),
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def markdown_table_row(index: int, row: dict[str, str]) -> str:
    return (
        f"| {index} | {row.get('member', '')} | {markdown_code(row.get('path', ''))} | "
        f"{row.get('size_tier', '')} | {row.get('batch_status', '')} | "
        f"{row.get('validator_status', '')} | {row.get('owner', '')} | "
        f"{markdown_code(row.get('output_dir', ''))} | {row.get('next_action', '')} |"
    )


def render_plan(
    *,
    review_name: str,
    program_list: Path,
    out_dir: Path,
    rows: list[dict[str, str]],
    source_root: str | None,
    delivery_root: str | None,
    validation_mode: str,
    scaffold_mode: str,
    subagent_mode: str,
    max_parallel_agents: int,
    reference_paths: list[str] | None,
    control_files: list[str] | None,
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
- Cline serial runner prompt: {out_dir / "cline-serial-runner-prompt.md"}
- Source root: {source_root or ""}
- Output root: {delivery_root or ""}
- Validation mode: {validation_mode}
- Scaffold mode: {scaffold_mode}
- Sub-agent mode: {subagent_mode}
- Max parallel agents: {max_parallel_agents if subagent_mode != "none" else "not_applicable"}
- Reference paths: {", ".join(reference_paths or []) if reference_paths else "none provided"}
- Control files: {", ".join(control_files or []) if control_files else "none provided"}
- Mode: Copilot Chat-only / one program per chat

## Progress

| Status | Count |
| --- | ---: |
| queued | {counts["queued"]} |
| in_progress | {counts["in_progress"]} |
| completed | {counts["completed"]} |
| completed_with_warnings | {counts["completed_with_warnings"]} |
| scanned_unvalidated | {counts["scanned_unvalidated"]} |
| blocked | {blocked_count} |
| failed | {failed_count} |
| skipped_not_program | {counts["skipped_not_program"]} |

## Current / Next

- Current program: none
- Current owner/session: none
- Next program: {next_row.get("member", "") if next_row else "none"}
- Next prompt: {markdown_code(next_row.get("prompt_path", "")) if next_row else "none"}
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
    validation_mode: str,
    scaffold_mode: str,
    subagent_mode: str,
    max_parallel_agents: int,
    reference_paths: list[str] | None,
    control_files: list[str] | None,
) -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "batch_id": safe_filename(review_name.lower()).strip("_") or "program_list_batch",
        "review_name": review_name,
        "program_list": str(program_list),
        "status_list": str(out_dir / "program-list-status.csv"),
        "program_batch_plan": str(out_dir / "program-batch-plan.md"),
        "cline_serial_runner_prompt": str(out_dir / "cline-serial-runner-prompt.md"),
        "source_root": source_root,
        "output_root": delivery_root,
        "validation_mode": validation_mode,
        "scaffold_mode": scaffold_mode,
        "subagent_mode": subagent_mode,
        "max_parallel_agents": max_parallel_agents,
        "subagent_dispatch_plan": str(out_dir / "subagent-dispatch-plan.md") if subagent_mode != "none" else "",
        "kiro_parallel_runner_prompt": str(out_dir / "kiro-parallel-runner-prompt.md") if subagent_mode != "none" else "",
        "cline_parallel_runner_prompt": "",
        "subagent_queue": str(out_dir / "subagent-queue") if subagent_mode != "none" else "",
        "subagent_results_dir": str(out_dir / "subagent-results") if subagent_mode != "none" else "",
        "reference_paths": reference_paths or [],
        "control_files": control_files or [],
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
                "subagent_prompt_path": row.get("subagent_prompt_path", ""),
                "subagent_result_path": row.get("subagent_result_path", ""),
                "next_action": row.get("next_action", ""),
                "scaffold_status": row.get("scaffold_status", ""),
            }
            for index, row in enumerate(rows, start=1)
        ],
    }


def indexer_script_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "legacy-ibmi-program-analyzer"
        / "scripts"
        / "index_rpg_source.py"
    )


def precreate_scaffold(
    *,
    member: str,
    source_root: str | None,
    source_path: str,
    output_dir: str,
) -> tuple[str, str]:
    if not source_root:
        return "blocked_missing_source", "source_root_required_for_scaffold_precreate"
    if not output_dir or "<delivery-root>" in output_dir:
        return "failed_runtime", "delivery_root_required_for_scaffold_precreate"

    source_file = local_join(source_root, source_path)
    if not source_file.is_file():
        return "blocked_missing_source", f"source file not found: {source_file}"

    script = indexer_script_path()
    if not script.is_file():
        return "failed_runtime", f"indexer script not found: {script}"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source_file),
            "--program",
            member,
            "--out-dir",
            output_dir,
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or f"exit {result.returncode}").strip()
        return "failed_runtime", "scaffold_precreate_failed: " + message.splitlines()[-1]
    return "present", ""


def result_json_path(out_dir: Path, index: int, member: str) -> Path:
    return out_dir / "subagent-results" / f"{index:04d}-{safe_filename(member)}.result.json"


def render_subagent_prompt(
    *,
    row: dict[str, str],
    prompt_text: str,
    result_path: Path,
    validation_mode: str,
) -> str:
    if validation_mode != "immediate":
        raise ValueError(
            "Kiro/parallel sub-agent prompts require validation_mode=immediate"
        )
    member = row.get("member", "")
    return f"""# Sub-Agent Program Task: {member}

You are one parallel worker for one IBM i program-analysis task.

## Ownership

- Program: {member}
- Output directory: `{row.get("output_dir", "")}`
- Per-program prompt path: `{row.get("prompt_path", "")}`
- Result JSON path: `{result_path}`

Do not work on any other program. Other sub-agents may be running in parallel,
so keep your writes inside this program's output directory and the single
result JSON file above.

## Shared State Rule

Do not edit these shared batch files directly:

- `program-list-status.csv`
- `program-batch-plan.md`
- `batch-scan-manifest.yaml`

The main agent will merge your result JSON into those shared files after all
parallel workers finish. If the embedded per-program prompt asks you to update
shared batch state, follow the artifact/quality intent but write the row result
to the JSON file instead.

## Per-Program Validation Gate

- This Kiro/parallel batch uses `validation_mode=immediate`.
- Follow the embedded per-program analyzer prompt's full reader-first layout.
  Do not replace the main analysis with a summary-only document or a reduced
  custom layout.
- The main analysis must retain all three required structure headings:
  `Routine Index For Calculation Logic`, `Routine Index For Validation Logic`,
  and `Routine Index For Exception Handling`.
- After writing the semantic artifacts, run the full
  `validate_program_analysis_contract.py` command from the embedded prompt.
  Do not write `completed/pass` until that validator passes.
- If validation fails, make at most one targeted repair. If it still fails,
  write `failed_validator/failed` with the validator finding.
- The parent merge will run the full validator again before accepting any
  successful result. A worker-reported pass is not sufficient by itself.

## Result JSON Contract

Always write `{result_path}` before finishing, even for blocked or failed work.
Use strict JSON with this shape:

```json
{{
  "member": "{member}",
  "batch_status": "completed",
  "validator_status": "pass",
  "completed_at": "<ISO-8601 UTC timestamp>",
  "last_error": "",
  "next_action": "ready for downstream program-list batch validation",
  "output_dir": "{row.get("output_dir", "")}",
  "artifacts": [
    "{member}-program-analysis.md",
    "{member}-source-index.yaml",
    "{member}-program-analysis-summary.yaml",
    "{member}-routine-index.md",
    "{member}-message-inventory.yaml",
    "{member}-routine-logic-details.md",
    "{member}-routine-logic-details.yaml"
  ]
}}
```

If source is missing, use `batch_status=blocked_missing_source`,
`validator_status=not_run`, and a concrete `last_error` / `next_action`.
If tool/model/runtime execution fails before stable artifacts exist, use
`batch_status=failed_runtime`. If artifact quality or validation fails after
one targeted repair pass, use `batch_status=failed_validator`.

## Embedded Per-Program Prompt

Follow this prompt for the actual analysis work, except for the shared-state
override above.

---

{prompt_text}
"""


def render_subagent_dispatch_plan(
    *,
    out_dir: Path,
    rows: list[dict[str, str]],
    max_parallel_agents: int,
) -> str:
    runnable_rows = [
        row for row in rows
        if row.get("batch_status") == "queued" and row.get("subagent_prompt_path")
    ]
    queue_rows = "\n".join(
        f"| {index} | {row.get('member', '')} | {markdown_code(row.get('subagent_prompt_path', ''))} | "
        f"{markdown_code(row.get('output_dir', ''))} | {markdown_code(row.get('subagent_result_path', ''))} |"
        for index, row in enumerate(runnable_rows, start=1)
    )
    if not queue_rows:
        queue_rows = "|  |  |  |  |  |"
    return f"""# Kiro / Agent Parallel Dispatch Plan

## Batch

- Batch directory: {out_dir}
- Per-task prompt queue: {out_dir / "subagent-queue"}
- Result directory: {out_dir / "subagent-results"}
- Kiro/agent parallel runner prompt: {out_dir / "kiro-parallel-runner-prompt.md"}
- Recommended max parallel workers: {max_parallel_agents}
- Merge command: `python3 skills/legacy-ibmi-program-list-batch/scripts/merge_subagent_results.py --batch-dir {out_dir}`

## Launch Rules

- Do not run this plan in Cline. Cline should use `cline-serial-runner-prompt.md`.
- Use this plan only in Kiro or another runtime that can reliably launch
  isolated workers and pass one complete Markdown prompt to each worker.
- Start at most {max_parallel_agents} workers at the same time.
- Give each worker exactly one complete file from `subagent-queue/`.
- Do not assign the same prompt file to two workers.
- Worker tasks must not edit shared batch state files directly.
- This Kiro/parallel batch requires `validation_mode=immediate`; do not create
  or dispatch deferred worker prompts.
- After all worker tasks finish, run the merge command above. The merge command
  re-runs the full per-program analyzer validator for every worker result that
  claims success, converts any failure to `failed_validator`, and only then
  updates shared state. Run the batch status validator after that merge.

## Queue

| # | Program | Sub-agent prompt | Output | Result JSON |
| ---: | --- | --- | --- | --- |
{queue_rows}
"""


def render_cline_serial_runner_prompt(
    *,
    out_dir: Path,
) -> str:
    return f"""你是运行在 Cline 中的串行 batch 执行器。

目标：
读取已经生成好的 program prompt queue，并按顺序一次处理一个 program。
每个 program 写完 artifact 后，必须先运行该 program 的
`validate_program_analysis_contract.py`；只有验证通过，才可以开始下一个
program。

Cline 执行边界：
- Cline 中只做串行，不做并行。
- 不要调用 `use_subagents`。
- 不要读取 `subagent-queue`，不要生成 `subagent-results`。
- 每次只执行一个 `prompt-queue/*.md` 的完整内容。
- 本 Step 2 的目标是处理完当前 `prompt-queue` 中所有可处理的 program；不要设置 3/5/10 个 program 之类的自我停止上限。
- 不要仅仅因为上下文变长、输出很多、或者担心后续质量不稳定就提前停止。
- 不要在 chat 里复述完整 source、完整 artifact 或历史分析；每个 program 完成后只输出一行 ledger 摘要，然后继续下一个 prompt。
- 这个 serial runner 只接受 `validation_mode=immediate`。如果
  `batch-scan-manifest.yaml` 是 `deferred`，停止处理并要求重新初始化 batch，
  使用 `--validation-mode immediate` 生成新的 prompt queue。
- 不允许把 `scanned_unvalidated` 当作 Cline serial 的成功状态。每个 program
  必须是 `completed` / `completed_with_warnings`，或因验证失败进入
  `failed_validator`。
- serial runner 不是第二套分析模板；每个 per-program prompt 必须完整遵循
  `legacy-ibmi-program-analyzer` 的主文件 H2 顺序、reader-first sections、
  三组 `Routine Index For ...` 和 RLOG coverage contract。
- 主文件 H2 顺序必须是：`Program Reading Summary` -> `Calculation Logic` ->
  `Validation Logic` -> `Exception Handling` -> `Message Inventory` ->
  `Metadata` -> `Analysis Coverage & Scope` -> `Program Call Map` ->
  `Routine Cards` -> `Routine Logic Details` -> `Deep Read Windows` ->
  `Entry Points & Parameters` -> `Object Dependencies` ->
  `Logic Decomposition Ledger` -> `Data Touch Map` ->
  `Key File & Field Logic` -> `Control Flow` -> `File I/O` ->
  `External Calls` -> `Error Handling` -> `Redundancy Candidate Notes` ->
  `TBDs & Blocking Status` -> `Review Checklist`。不得改成自定义简版 layout。

Batch directory:
`{out_dir}`

Program prompt directory:
`{out_dir / "prompt-queue"}`

Batch status file:
`{out_dir / "program-list-status.csv"}`

Batch manifest:
`{out_dir / "batch-scan-manifest.yaml"}`

执行规则：
1. 先读取 `program-batch-plan.md`、`program-list-status.csv` 和 `batch-scan-manifest.yaml`，确认当前 batch 状态。
2. 按文件名自然排序处理 `prompt-queue/*.md`。
3. 每次只处理一个 prompt 文件。
4. 每个 prompt 只对应一个 program；不要把多个 program 合并到一次分析。
5. 处理当前 program 时，完整执行该 prompt 的内容。
6. 当前 program 完成、blocked 或 failed，并且 durable state 已更新后，才开始下一个 prompt。
7. 不要并行启动多个 task，也不要在同一个上下文里同时分析多个 program。
8. 如果某个 program 遇到 Cline/model/network/tool 错误，不要无限重试；按该 prompt 的 retry / exit budget 写入 `failed_runtime`、`last_error` 和 `next_action`，然后继续下一个可处理 prompt。
9. 每个 program 生成必需 artifact 后，立即运行 prompt 中的
   `validate_program_analysis_contract.py`，检查完整 analyzer layout、sidecars、
   RLOG coverage 和 message inventory；不要只运行 batch status validator。
10. 如果 validator 失败，最多做一次 targeted repair；仍失败则写入
    `failed_validator`、`last_error` 和 `next_action`，再继续下一个可处理 prompt。
11. 每完成一个 program，都必须更新：
    - `program-list-status.csv`
    - `program-batch-plan.md`
    - `batch-scan-manifest.yaml`
12. 每完成一个 program，只在 chat 里报告：program、status、validator_status、关键 artifact 路径、下一条 prompt；不要粘贴大段分析内容。
13. 只要工具仍能读写文件并执行下一个 prompt，就必须继续处理下一个 program。
14. 只有遇到硬性阻断才允许停止，例如 Cline/model/network/tool Auto-Retry 用尽、文件读写失败、当前 session 已无法安全读取或写入下一个 prompt。
15. 如果发生硬性阻断，停在当前 program 边界，写好 durable state 和 `batch-session-handoff.md`，报告精确的下一个待处理 prompt。不要把尚未执行的后续 program 标记为 failed。

建议处理顺序：
1. 列出 `prompt-queue/*.md` 文件清单。
2. 找到第一个尚未完成的 program prompt。
3. 读取该 prompt 的完整内容。
4. 执行该 prompt。
5. 更新 batch state。
6. 输出一行 ledger 摘要，不输出完整 artifact 内容。
7. 继续下一个 prompt，直到所有 program 都被分类为 completed、completed_with_warnings、skipped_not_program、blocked_missing_source、failed_validator 或 failed_runtime，或遇到硬性阻断并已写好 handoff。

全部处理完成后，运行 batch status validator：

```text
python3 skills/legacy-ibmi-program-list-batch/scripts/validate_program_batch_status.py --batch-dir "{out_dir}"
```

现在开始：读取 batch 状态和 prompt queue，列出待处理 prompt 文件，然后从第一个未完成 program 开始串行处理。
"""


def render_kiro_parallel_runner_prompt(
    *,
    out_dir: Path,
    max_parallel_agents: int,
) -> str:
    return f"""你是运行在 Kiro 或支持隔离 worker 的 agent runtime 中的并行 batch 执行器。

目标：
读取已经生成好的 subagent queue，并并行启动多个独立 worker 来处理每个 program。

重要边界：
- 这个 prompt 不给 Cline 使用。Cline 请使用 `cline-serial-runner-prompt.md`。
- 只有当 Kiro/agent runtime 能可靠启动隔离 worker，并能把一个完整 Markdown prompt 交给一个 worker 时，才使用本 prompt。
- 如果 runtime 不能保证 worker 隔离，停止并改用 Cline serial prompt。

Batch directory:
`{out_dir}`

Dispatch plan:
`{out_dir / "subagent-dispatch-plan.md"}`

Per-task prompt directory:
`{out_dir / "subagent-queue"}`

Result directory:
`{out_dir / "subagent-results"}`

最大并发 worker 数：
`{max_parallel_agents}`

执行规则：
1. 先读取 `subagent-dispatch-plan.md`，确认待处理的 `subagent-queue/*.md` 文件清单。
2. 按文件名自然排序处理 `subagent-queue/*.md`。
3. 最多同时启动 `{max_parallel_agents}` 个独立 worker。
4. 每个 worker 只能接收一个 `subagent-queue/*.md` 文件的完整内容。
5. 每个 worker 只处理该 prompt 中指定的一个 program。
6. 不要把多个 program 合并到一个 worker。
7. 不要把同一个 prompt 文件分配给两个 worker。
8. 每个 worker 只能写自己的 program output directory 和自己的 result JSON。
9. worker 不允许直接修改这些共享文件：
   - `program-list-status.csv`
   - `program-batch-plan.md`
   - `batch-scan-manifest.yaml`
10. worker 必须在结束前写出 prompt 中指定的 `subagent-results/*.result.json`。
11. 如果某个 worker 失败，不要无限重试；让该 worker 写出 `failed_runtime` 或 `failed_validator` result JSON。如果 worker 无法写 JSON，由父执行器为该 program 写一个 failed result JSON，记录具体错误。
12. 一个 worker 完成后，再从队列中启动下一个，直到所有 `subagent-queue/*.md` 都处理完。
13. 这个 Kiro batch 只接受 `validation_mode=immediate`。如果 manifest 是
    `deferred`，不要启动 worker；要求重新运行 initializer 并使用
    `--validation-mode immediate`。
14. 每个 worker 必须遵循 embedded per-program prompt 的完整 analyzer layout，
    保留三组 `Routine Index For ...` 结构标题，并在写 success result JSON 前
    运行完整的 `validate_program_analysis_contract.py`。

所有 worker 完成后，运行 merge：

```text
python3 skills/legacy-ibmi-program-list-batch/scripts/merge_subagent_results.py --batch-dir "{out_dir}"
```

merge 会对每个 worker 报告成功的 output directory 再运行一次完整的
`validate_program_analysis_contract.py`；只有 merge 通过这道 parent gate 后，
才运行 batch status validator：

```text
python3 skills/legacy-ibmi-program-list-batch/scripts/validate_program_batch_status.py --batch-dir "{out_dir}"
```

如果当前 runtime 不能可靠启动隔离 worker：
- 不要尝试在一个上下文里处理多个 program。
- 停止并报告：当前 runtime 不支持隔离并行 worker。
- 改用 `{out_dir / "cline-serial-runner-prompt.md"}` 在 Cline 中串行处理。

现在开始：读取 dispatch plan，列出将处理的 prompt 文件和并发计划，然后启动第一批 worker。
"""


def initialize(args: argparse.Namespace) -> None:
    if args.subagent_mode == "prepare" and args.validation_mode != "immediate":
        raise SystemExit(
            "Kiro/parallel sub-agent mode requires --validation-mode immediate. "
            "Reinitialize the batch with --validation-mode immediate."
        )
    program_list = Path(args.program_list).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir_name = out_dir.name.lower()
    out_dir_warning = ""
    if "program-list-batch" not in out_dir_name:
        suggested_name = f"{safe_filename(args.review_name) or 'program'}-program-list-batch"
        out_dir_warning = (
            "Warning: --out-dir is not named like a dedicated program-list batch root. "
            f"Recommended convention: {out_dir.parent / suggested_name}"
        )
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        raise SystemExit(f"Output directory is not empty. Use --force to overwrite generated files: {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir = out_dir / "prompt-queue"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    subagent_dir = out_dir / "subagent-queue"
    result_dir = out_dir / "subagent-results"
    if args.subagent_mode != "none":
        subagent_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "completed").mkdir(exist_ok=True)
    (out_dir / "blocked").mkdir(exist_ok=True)
    (out_dir / "failed").mkdir(exist_ok=True)

    fieldnames, rows = read_csv(program_list)
    if "member" not in fieldnames:
        raise SystemExit("program-list.csv must include a 'member' column")
    if args.programs_file:
        requested_programs = read_programs_file(Path(args.programs_file).resolve())
        if not requested_programs:
            raise SystemExit("programs file has no program names")
        rows = filter_rows_by_programs(rows, requested_programs)
        program_list = out_dir / "flow-program-list.csv"
        write_csv(program_list, fieldnames, rows)

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
            scaffold_status = "not_created"
            last_error = ""
            if args.scaffold_mode == "precreate":
                scaffold_status, scaffold_error = precreate_scaffold(
                    member=member,
                    source_root=args.source_root,
                    source_path=normalized.get("path", ""),
                    output_dir=output_dir,
                )
                if scaffold_status == "present":
                    next_action = "fill details from scaffold"
                elif scaffold_status == "blocked_missing_source":
                    batch_status = "blocked_missing_source"
                    next_action = "fix source root/path, then regenerate scaffold"
                    last_error = scaffold_error
                else:
                    batch_status = "failed_runtime"
                    next_action = "fix scaffold precreation issue, then rerun initializer for this program"
                    last_error = scaffold_error
        else:
            batch_status = "skipped_not_program"
            next_action = "none - row is not a program"
            scaffold_status = "not_applicable"
            last_error = ""
        normalized.update(
            {
                "batch_status": batch_status,
                "validator_status": "not_run",
                "output_dir": output_dir,
                "prompt_path": prompt_path,
                "subagent_prompt_path": "",
                "subagent_result_path": "",
                "owner": "",
                "session_id": "",
                "started_at": "",
                "completed_at": "",
                "last_error": last_error,
                "next_action": next_action,
                "handoff_path": "",
                "scaffold_status": scaffold_status,
            }
        )
        status_rows.append(normalized)
        if prompt_path:
            prompt_text = render_prompt(
                template=prompt_template,
                program_list=program_list,
                out_dir=out_dir,
                row=normalized,
                source_root=args.source_root,
                delivery_root=args.delivery_root,
                intent=args.intent,
                validation_mode=args.validation_mode,
                reference_paths=args.reference_path,
                control_files=args.control_file,
            )
            Path(prompt_path).write_text(prompt_text, encoding="utf-8")
            if args.subagent_mode == "prepare" and normalized["batch_status"] == "queued":
                subagent_prompt_path = subagent_dir / f"{index:04d}-{safe_filename(member)}.md"
                result_path = result_json_path(out_dir, index, member)
                normalized["subagent_prompt_path"] = str(subagent_prompt_path)
                normalized["subagent_result_path"] = str(result_path)
                subagent_prompt_path.write_text(
                    render_subagent_prompt(
                        row=normalized,
                        prompt_text=prompt_text,
                        result_path=result_path,
                        validation_mode=args.validation_mode,
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
            validation_mode=args.validation_mode,
            scaffold_mode=args.scaffold_mode,
            subagent_mode=args.subagent_mode,
            max_parallel_agents=args.max_parallel_agents,
            reference_paths=args.reference_path,
            control_files=args.control_file,
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
        validation_mode=args.validation_mode,
        scaffold_mode=args.scaffold_mode,
        subagent_mode=args.subagent_mode,
        max_parallel_agents=args.max_parallel_agents,
        reference_paths=args.reference_path,
        control_files=args.control_file,
    )
    (out_dir / "batch-scan-manifest.yaml").write_text(to_yaml(manifest) + "\n", encoding="utf-8")
    (out_dir / "cline-serial-runner-prompt.md").write_text(
        render_cline_serial_runner_prompt(out_dir=out_dir),
        encoding="utf-8",
    )
    if args.subagent_mode == "prepare":
        (out_dir / "subagent-dispatch-plan.md").write_text(
            render_subagent_dispatch_plan(
                out_dir=out_dir,
                rows=status_rows,
                max_parallel_agents=args.max_parallel_agents,
            ),
            encoding="utf-8",
        )
        (out_dir / "kiro-parallel-runner-prompt.md").write_text(
            render_kiro_parallel_runner_prompt(
                out_dir=out_dir,
                max_parallel_agents=args.max_parallel_agents,
            ),
            encoding="utf-8",
        )
    print(f"Initialized program batch: {out_dir}")
    if out_dir_warning:
        print(out_dir_warning)
    print(f"Prompt files: {len(list(prompt_dir.glob('*.md')))}")
    print(f"Cline serial Step 2 prompt: {out_dir / 'cline-serial-runner-prompt.md'}")
    if args.subagent_mode != "none":
        print(f"Kiro/agent worker prompt files: {len(list(subagent_dir.glob('*.md')))}")
        print(f"Kiro/agent parallel Step 2 prompt: {out_dir / 'kiro-parallel-runner-prompt.md'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program-list", required=True, help="Input program-list.csv")
    parser.add_argument(
        "--programs-file",
        help=(
            "Optional SME program flow/list. When provided, generate prompt queue "
            "only for these distinct programs in the supplied order."
        ),
    )
    parser.add_argument("--out-dir", required=True, help="Output batch directory")
    parser.add_argument("--source-root", help="Source repository root")
    parser.add_argument("--delivery-root", help="Output root for generated per-program artifacts; no checkout is required")
    parser.add_argument(
        "--reference-path",
        action="append",
        default=[],
        help="Reference pack, dictionary, message catalog, or other supporting context path to include in every prompt",
    )
    parser.add_argument(
        "--control-file",
        action="append",
        default=[],
        help="Control file, code table, or lookup file path to include in every prompt",
    )
    parser.add_argument("--delivery-profile", help=argparse.SUPPRESS)
    parser.add_argument("--delivery-main-snapshot", help=argparse.SUPPRESS)
    parser.add_argument("--review-name", default="program list batch", help="Human-readable batch name")
    parser.add_argument("--intent", default="standalone_exploratory")
    parser.add_argument(
        "--validation-mode",
        choices=sorted(VALIDATION_MODES),
        default="immediate",
        help=(
            "immediate runs program-analysis validation inside each prompt; "
            "deferred skips that expensive step and marks rows scanned_unvalidated"
        ),
    )
    parser.add_argument(
        "--scaffold-mode",
        choices=sorted(SCAFFOLD_MODES),
        default="none",
        help=(
            "none only generates prompt/status files; precreate also runs the "
            "deterministic source indexer for each program to create scaffold artifacts"
        ),
    )
    parser.add_argument(
        "--subagent-mode",
        choices=sorted(SUBAGENT_MODES),
        default="none",
        help=(
            "none only generates the normal prompt queue; prepare also writes "
            "subagent-queue prompts, result JSON targets, and a Kiro/agent "
            "parallel dispatch plan for isolated per-program worker tasks"
        ),
    )
    parser.add_argument(
        "--max-parallel-agents",
        type=int,
        default=4,
        help="Maximum manual parallel worker tasks recommended in the generated dispatch plan",
    )
    parser.add_argument("--python-launcher", help=argparse.SUPPRESS)
    parser.add_argument("--force", action="store_true", help="Overwrite generated files in an existing output directory")
    return parser


if __name__ == "__main__":
    parsed_args = build_parser().parse_args()
    if parsed_args.max_parallel_agents < 1:
        raise SystemExit("--max-parallel-agents must be at least 1")
    initialize(parsed_args)
