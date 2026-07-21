#!/usr/bin/env python3
"""Create a program-list batch queue for missing flow-review programs.

This is an intake adapter only. It does not scan source or build the SME
review. It reads the flow manifest, selects programs whose required compact
artifacts are missing, and delegates queue/state generation to the canonical
legacy-ibmi-program-list-batch initializer.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import shutil
import sys
from pathlib import Path, PureWindowsPath
from types import ModuleType, SimpleNamespace
from typing import Any


REQUIRED_ARTIFACTS = (
    "program-analysis.md",
    "program-analysis-summary.yaml",
    "source-index.yaml",
    "routine-index.md",
    "message-inventory.yaml",
    "routine-logic-details.md",
    "routine-logic-details.yaml",
)
QUEUE_STATUS_FILE = "program-set-scan-queue.yaml"
BLOCKED_FILE = "blocked-programs.csv"
GENERATED_QUEUE_FILES = (
    "program-list.csv",
    "flow-program-list.csv",
    "program-list-status.csv",
    "program-batch-plan.md",
    "batch-scan-manifest.yaml",
    "cline-serial-runner-prompt.md",
    "subagent-dispatch-plan.md",
    "kiro-parallel-runner-prompt.md",
    "batch-session-handoff.md",
    QUEUE_STATUS_FILE,
    BLOCKED_FILE,
)
GENERATED_QUEUE_DIRS = (
    "prompt-queue",
    "subagent-queue",
    "subagent-results",
    "completed",
    "blocked",
    "failed",
)


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_batch_initializer() -> ModuleType:
    scripts_root = Path(__file__).resolve().parents[2]
    path = scripts_root / "legacy-ibmi-program-list-batch" / "scripts" / "initialize_program_batch.py"
    if not path.is_file():
        raise RuntimeError(f"program-list-batch initializer not found: {path}")
    return load_module("legacy_ibmi_program_list_batch_initializer", path)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required to read the program-set manifest") from exc
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be a YAML mapping: {path}")
    return value


def write_yaml(path: Path, value: dict[str, Any], batch: ModuleType) -> None:
    path.write_text(batch.to_yaml(value) + "\n", encoding="utf-8")


def artifact_key(filename: str) -> str:
    return filename.replace("-", "_").replace(".", "_")


def missing_artifacts(entry: dict[str, Any]) -> list[str]:
    compact = entry.get("compact_artifacts") or {}
    return [
        filename
        for filename in REQUIRED_ARTIFACTS
        if ((compact.get(artifact_key(filename)) or {}).get("status") != "present")
    ]


def readiness_status(entry: dict[str, Any]) -> str:
    readiness = entry.get("artifact_readiness")
    if isinstance(readiness, dict):
        return str(readiness.get("status") or "not_ready")
    if isinstance(readiness, str):
        return readiness
    if entry.get("run_resolution") in {
        "analyzed_this_run",
        "reused_same_run",
        "reused_artifact_repo",
    } and not missing_artifacts(entry):
        return "ready"
    return "not_ready"


def readiness_reason(entry: dict[str, Any]) -> str:
    readiness = entry.get("artifact_readiness")
    if not isinstance(readiness, dict):
        return "artifact readiness did not pass"
    findings = [str(item) for item in readiness.get("findings", []) or []]
    return "; ".join(findings) or "artifact readiness did not pass"


def inventory_source_path_block_reason(source_root: Path, source_path: str) -> str:
    raw_path = source_path.strip()
    try:
        platform_path = Path(raw_path)
        windows_path = PureWindowsPath(raw_path)
        if platform_path.is_absolute() or windows_path.drive or windows_path.root:
            return "source path must be relative to source root; absolute paths are not allowed"
        candidate = (source_root / Path(raw_path.replace("\\", "/"))).resolve()
        candidate.relative_to(source_root.resolve())
    except (OSError, RuntimeError, ValueError):
        return "source path escapes source root after resolution"
    if not candidate.is_file():
        return "source path does not exist or is not a file under source root"
    return ""


def clear_generated_queue_artifacts(output_dir: Path) -> None:
    for dirname in GENERATED_QUEUE_DIRS:
        generated_dir = output_dir / dirname
        if generated_dir.is_symlink() or generated_dir.is_file():
            generated_dir.unlink()
        elif generated_dir.is_dir():
            shutil.rmtree(generated_dir)
    for filename in GENERATED_QUEUE_FILES:
        path = output_dir / filename
        if path.is_file() or path.is_symlink():
            path.unlink()
    unknown = list(output_dir.iterdir()) if output_dir.is_dir() else []
    if unknown:
        raise ValueError(
            "refusing to replace a queue directory containing unrecognized artifacts: "
            + ", ".join(path.name for path in unknown)
        )


def inventory_rows_from_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    inventory = manifest.get("source_inventory") or {}
    rows: dict[str, dict[str, str]] = {}
    for item in inventory.get("programs", []) or []:
        if not isinstance(item, dict):
            continue
        program = str(item.get("program") or "").strip()
        if program:
            rows[program.upper()] = {
                key: str(value or "") for key, value in item.items()
            }

    # v0.4 freezes the fresh inventory rows into the signed-off preparation
    # manifest. Reopening the mutable CSV here would create a TOCTOU path swap
    # between preparation and targeted queue generation.
    if str(manifest.get("schema_version") or "") == "0.4":
        return rows

    program_list = inventory.get("program_list") or {}
    raw_path = str(program_list.get("path") or "").strip()
    if raw_path:
        path = Path(raw_path)
        if path.is_file():
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for item in csv.DictReader(handle):
                    program = (item.get("member") or "").strip()
                    if program:
                        rows[program.upper()] = {
                            key: str(value or "") for key, value in item.items()
                        }
    return rows


def select_missing_programs(
    manifest: dict[str, Any],
    source_root: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    inventory = manifest.get("source_inventory") or {}
    freshness = str(inventory.get("freshness") or "not_checked")
    inventory_rows = inventory_rows_from_manifest(manifest)
    queued: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    seen: set[str] = set()

    for entry in manifest.get("programs", []) or []:
        if not isinstance(entry, dict):
            continue
        program = str(entry.get("normalized_name") or "").strip()
        key = program.upper()
        if not program or key in seen:
            continue
        seen.add(key)
        missing = missing_artifacts(entry)
        readiness = readiness_status(entry)
        if readiness == "ready":
            continue

        inventory_row = inventory_rows.get(key, {})
        source_path = str(inventory_row.get("source_path") or inventory_row.get("path") or "").strip()
        source_kind = str(inventory_row.get("source_kind") or "unknown").strip()
        size_tier = str(inventory_row.get("size_tier") or entry.get("tier") or "normal_program").strip()
        inventory_status = str(inventory_row.get("inventory_status") or "not_found").strip()
        targeted = str(inventory_row.get("targeted_scan_allowed") or "").lower() == "true"
        reason = ""
        if freshness != "fresh":
            reason = (
                f"source inventory is {freshness}; provide a fresh inventory or an "
                "exact approved source mapping (no repository-wide scan is triggered)"
            )
        elif inventory_status not in {"found", ""} and not source_path:
            reason = "program not found in fresh source inventory; confirm program name or source mapping"
        elif not source_path:
            reason = "source path is missing from source inventory; provide a source mapping"
        elif inventory_row.get("targeted_scan_allowed") is not None and not targeted:
            reason = "targeted source scan is not allowed by the current inventory freshness gate"
        else:
            reason = inventory_source_path_block_reason(source_root, source_path)

        base = {
            "member": program,
            "object_type": "program",
            "source_kind": source_kind,
            "path": source_path,
            "total_lines": str(inventory_row.get("total_lines") or ""),
            "size_tier": size_tier,
            "tier_reason": str(inventory_row.get("tier_reason") or "missing flow artifact refresh"),
            "missing_artifacts": (
                ", ".join(missing)
                if missing
                else "semantic readiness: " + readiness_reason(entry)
            ),
            "inventory_status": inventory_status,
        }
        if reason:
            base["reason"] = reason
            blocked.append(base)
        else:
            queued.append(base)
    return queued, blocked


def write_program_list(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["member", "object_type", "source_kind", "path", "total_lines", "size_tier", "tier_reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_blocked(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "member",
        "source_kind",
        "path",
        "size_tier",
        "missing_artifacts",
        "inventory_status",
        "reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_batch_args(
    *,
    batch: ModuleType,
    program_list: Path,
    output_dir: Path,
    source_root: Path,
    delivery_root: str,
    manifest: dict[str, Any],
    args: argparse.Namespace,
) -> SimpleNamespace:
    workspace = manifest.get("workspace_profile") or {}
    configured_tier_roots = workspace.get("program_tier_roots") or {}
    return SimpleNamespace(
        program_list=str(program_list),
        programs_file=None,
        out_dir=str(output_dir),
        source_root=str(source_root),
        delivery_root=delivery_root,
        reference_path=args.reference_path,
        control_file=args.control_file,
        review_name=args.review_name,
        intent=args.intent,
        validation_mode=args.validation_mode,
        scaffold_mode=args.scaffold_mode,
        subagent_mode=args.subagent_mode,
        max_parallel_agents=args.max_parallel_agents,
        force=True,
        tier_roots=configured_tier_roots or batch.TIER_ROOTS,
    )


def create_queue(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.out_dir).resolve()
    if not manifest_path.is_file():
        raise SystemExit(f"manifest not found: {manifest_path}")
    if not source_root.is_dir():
        raise SystemExit(f"source root not found or not a directory: {source_root}")
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        raise SystemExit(f"output directory is not empty; use --force: {output_dir}")

    manifest = load_yaml(manifest_path)
    review_name = args.review_name or str(manifest.get("review_name") or "program set")
    args.review_name = review_name
    queued, blocked = select_missing_programs(manifest, source_root)
    if args.force:
        clear_generated_queue_artifacts(output_dir)
    if not queued and not blocked:
        print("Missing-program queue status: no_missing_programs")
        return 0
    output_dir.mkdir(parents=True, exist_ok=True)
    program_list = output_dir / "program-list.csv"
    if queued:
        write_program_list(program_list, queued)

    batch = load_batch_initializer()
    if queued:
        batch.initialize(
            build_batch_args(
                batch=batch,
                program_list=program_list,
                output_dir=output_dir,
                source_root=source_root,
                delivery_root=args.delivery_root,
                manifest=manifest,
                args=args,
            )
        )
    if blocked:
        write_blocked(output_dir / BLOCKED_FILE, blocked)

    inventory = manifest.get("source_inventory") or {}
    status = (
        "queue_created_with_blocked_programs"
        if queued and blocked
        else "queue_created"
        if queued
        else "blocked_missing_source"
        if blocked
        else "no_missing_programs"
    )
    queue_manifest = {
        "schema_version": "0.4",
        "queue_type": "missing_program_scan",
        "status": status,
        "review_id": manifest.get("review_id"),
        "review_name": review_name,
        "core_manifest": str(manifest_path),
        "source_root": str(source_root),
        "delivery_root": args.delivery_root,
        "batch_dir": str(output_dir) if queued else None,
        "source_inventory_freshness": inventory.get("freshness"),
        "queued_programs": [row["member"] for row in queued],
        "blocked_programs": [row["member"] for row in blocked],
        "next_action": (
            "run prompt-queue, then rebuild the program-set review"
            if queued
            else "provide a fresh externally prepared inventory or exact source mapping before creating prompts"
            if blocked
            else "rebuild or validate the program-set review"
        ),
    }
    write_yaml(output_dir / QUEUE_STATUS_FILE, queue_manifest, batch)
    print(f"Missing-program queue status: {status}")
    if queued:
        print(f"Prompt files: {len(queued)} under {output_dir / 'prompt-queue'}")
    if blocked:
        print(f"Blocked program list: {output_dir / BLOCKED_FILE}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="program-set-core-input-manifest.yaml")
    parser.add_argument("--source-root", required=True, help="Source repository root")
    parser.add_argument("--delivery-root", required=True, help="Delivery working root for program artifacts")
    parser.add_argument("--out-dir", required=True, help="Missing-program batch output directory")
    parser.add_argument("--review-name", help="Override the batch review name")
    parser.add_argument("--intent", default="standalone_exploratory")
    parser.add_argument("--validation-mode", choices=["immediate", "deferred"], default="immediate")
    parser.add_argument("--scaffold-mode", choices=["none", "precreate"], default="none")
    parser.add_argument("--subagent-mode", choices=["none", "prepare"], default="none")
    parser.add_argument("--max-parallel-agents", type=int, default=4)
    parser.add_argument("--reference-path", action="append", default=[])
    parser.add_argument("--control-file", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    return parser


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    if parsed.max_parallel_agents < 1:
        raise SystemExit("--max-parallel-agents must be at least 1")
    raise SystemExit(create_queue(parsed))
