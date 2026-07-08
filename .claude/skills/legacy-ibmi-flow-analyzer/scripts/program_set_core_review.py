#!/usr/bin/env python3
"""Build and validate program-set SME core review scaffolds.

The builder is intentionally deterministic: it reads program analysis artifact
folders from either a current-run working root or an approved local document
repository clone, writes a manifest, and renders a fixed review skeleton. It
does not fetch remote-main or silently reuse arbitrary prior-run artifacts. The
validator checks structure and coverage; it does not judge whether the
LLM-written summaries are semantically correct.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CORE_SECTIONS = (
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
)

READER_FIRST_SECTIONS = (
    "Program Set Reading Summary",
    "Cross-Program Processing Overview",
    *CORE_SECTIONS,
    "Core Completeness Ledger",
    "Sources",
    "Run Profile",
    "Source Inventory Cache",
)

AUDIT_CONTROL_SECTIONS = (
    "Core Completeness Ledger",
    "Sources",
    "Run Profile",
    "Source Inventory Cache",
)

FORBIDDEN_FULL_FLOW_SECTIONS = (
    "Metadata",
    "Trigger Context",
    "Transaction Call Map",
    "Nodes",
    "Nodes (Programs in the Chain)",
    "Edges",
    "Edges (Calls Between Nodes)",
    "Common Dependencies",
    "Cross-Program Data Flow",
    "Replay",
    "Flow Replay Path",
    "Lineage",
    "Cross-Program Field Lineage",
    "Persistence",
    "Flow Persistence Matrix",
    "Branch Points",
    "UI Surfaces",
    "Error Propagation & Commit Boundaries",
    "Exception Propagation Chain",
    "Capability Seeds",
    "Business Capability Seeds",
    "Review Checklist",
    "SME Checklist",
)

REQUIRED_COMPACT_ARTIFACTS = (
    "program-analysis.md",
    "program-analysis-summary.yaml",
    "source-index.yaml",
    "routine-index.md",
    "message-inventory.yaml",
    "routine-logic-details.md",
    "routine-logic-details.yaml",
)

CONDITIONAL_COMPACT_ARTIFACTS: tuple[str, ...] = ()

OPTIONAL_COMPACT_ARTIFACTS = (
    "file-io-inventory.yaml",
    "field-mutation-matrix.yaml",
    "sql-inventory.yaml",
)

RUN_ANALYZED = "analyzed_this_run"
RUN_REUSED = "reused_same_run"
RUN_ARTIFACT_REPO = "reused_artifact_repo"
RUN_PENDING = "pending_source"
RUN_BLOCKED = "blocked_missing_source"

ARTIFACT_REPO_CURRENT_RUN = "current_run"
ARTIFACT_REPO_APPROVED_DOCUMENT = "approved_document_repo"

DEFAULT_SOURCE_INVENTORY_DIR = Path("outputs") / "repo-scan"
DEFAULT_PROGRAM_LIST_FILENAME = "program-list.csv"
DEFAULT_SCAN_SUMMARY_FILENAME = "scan-summary.yaml"


@dataclass(frozen=True)
class ArtifactStatus:
    path: str
    status: str


@dataclass(frozen=True)
class ProgramEntry:
    input_name: str
    normalized_name: str
    order: int
    run_resolution: str
    artifact_root: str | None
    artifact_source: str
    tier: str | None
    compact_artifacts: dict[str, ArtifactStatus]
    follow_up: str


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_yaml(data: Any) -> str:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "program_set_review"


def read_programs_file(path: Path) -> list[str]:
    programs: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        programs.append(stripped)
    return programs


def normalize_program_name(program: str, profile: dict[str, Any]) -> str:
    normalization = profile.get("program_name_normalization", {}) or {}
    normalized = program.strip()
    if normalization.get("case") == "upper":
        normalized = normalized.upper()
    return normalized


def profile_lookup(config: dict[str, Any]) -> dict[str, Any]:
    if "program_artifact_resolution_profile" in config:
        value = config.get("program_artifact_resolution_profile")
        return value if isinstance(value, dict) else {}
    value = config.get("delivery_artifact_lookup_profile")
    return value if isinstance(value, dict) else {}


def profile_workspace(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("delivery_workspace_profile", {}) or {}


def profile_source_inventory(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("source_inventory_profile", {}) or {}


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def git_status_args(git_root: Path, source_root: Path, ignore_paths: list[Path] | None) -> list[str]:
    try:
        include_path = source_root.resolve().relative_to(git_root).as_posix()
    except ValueError:
        include_path = "."
    args = ["status", "--porcelain", "--", include_path or "."]
    for path in ignore_paths or []:
        try:
            relative = path.resolve().relative_to(git_root).as_posix()
        except ValueError:
            continue
        args.append(f":(exclude){relative}")
    return args


def detect_source_revision(root: Path, ignore_paths: list[Path] | None = None) -> dict[str, Any]:
    top_level = run_git(root, ["rev-parse", "--show-toplevel"])
    if top_level.returncode != 0:
        resolved = root.resolve()
        return {
            "type": "filesystem",
            "root": str(resolved),
            "head": None,
            "short_head": None,
            "dirty": None,
            "key": f"filesystem:{resolved}",
            "freshness_note": "No Git metadata was available; inventory freshness cannot be proven.",
        }

    git_root = Path(top_level.stdout.strip()).resolve()
    head = run_git(git_root, ["rev-parse", "HEAD"])
    short_head = run_git(git_root, ["rev-parse", "--short=12", "HEAD"])
    status = run_git(git_root, git_status_args(git_root, root, ignore_paths))
    if head.returncode != 0:
        return {
            "type": "git",
            "root": str(git_root),
            "head": None,
            "short_head": None,
            "dirty": None,
            "key": f"git-unresolved:{git_root}",
            "freshness_note": "Git repository was detected, but HEAD could not be resolved.",
        }

    full_head = head.stdout.strip()
    dirty = bool(status.stdout.strip()) if status.returncode == 0 else None
    return {
        "type": "git",
        "root": str(git_root),
        "head": full_head,
        "short_head": short_head.stdout.strip() if short_head.returncode == 0 else full_head[:12],
        "dirty": dirty,
        "key": f"git:{full_head}",
        "freshness_note": (
            "Stable reuse key; inventory is fresh only when this same clean HEAD is observed."
            if dirty is False
            else "Source worktree has uncommitted changes; rerun inventory before relying on cache."
        ),
    }


def artifact_key(filename: str) -> str:
    return filename.replace("-", "_").replace(".", "_")


def collect_artifact_statuses(root: Path, artifact_root: str | None) -> dict[str, ArtifactStatus]:
    statuses: dict[str, ArtifactStatus] = {}
    root_path = root / artifact_root if artifact_root else None
    for filename in REQUIRED_COMPACT_ARTIFACTS + CONDITIONAL_COMPACT_ARTIFACTS + OPTIONAL_COMPACT_ARTIFACTS:
        key = artifact_key(filename)
        if root_path is None:
            statuses[key] = ArtifactStatus(path=filename, status="missing")
            continue
        candidate = root_path / filename
        statuses[key] = ArtifactStatus(
            path=relative_path(root, candidate),
            status="present" if candidate.is_file() else "missing",
        )
    return statuses


def infer_tier(artifact_root: str | None, workspace: dict[str, Any]) -> str | None:
    if not artifact_root:
        return None
    tier_roots = workspace.get("program_tier_roots", {}) or {}
    for tier, tier_root in tier_roots.items():
        if artifact_root == tier_root or artifact_root.startswith(f"{tier_root.rstrip('/')}/"):
            return str(tier)
    if "large_extreme_program" in artifact_root:
        return "large_extreme_program"
    if "complex_normal_program" in artifact_root:
        return "complex_normal_program"
    if "normal_program" in artifact_root:
        return "normal_program"
    return None


def find_program_artifact_root(
    root: Path,
    program: str,
    lookup: dict[str, Any],
) -> tuple[str | None, list[str]]:
    patterns = lookup.get("program_folder_patterns") or ["modules/*/{PROGRAM}"]
    matches: list[Path] = []
    for pattern in patterns:
        resolved_pattern = str(pattern).replace("{PROGRAM}", program)
        matches.extend(path for path in root.glob(resolved_pattern) if path.is_dir())
    relative_matches = sorted({relative_path(root, path) for path in matches})
    return (relative_matches[0] if relative_matches else None, relative_matches)


def build_program_entries(
    programs: list[str],
    artifact_root: Path,
    config: dict[str, Any],
    artifact_repo_mode: str = ARTIFACT_REPO_CURRENT_RUN,
) -> tuple[list[ProgramEntry], list[str]]:
    lookup = profile_lookup(config)
    workspace = profile_workspace(config)
    approved_document_repo = artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT
    present_resolution = RUN_ARTIFACT_REPO if approved_document_repo else RUN_ANALYZED
    duplicate_resolution = RUN_ARTIFACT_REPO if approved_document_repo else RUN_REUSED
    present_source = "approved_document_repo" if approved_document_repo else "delivery_working_branch"
    present_follow_up = (
        "none - approved document repo artifact present"
        if approved_document_repo
        else "none - analysis artifact present in current run"
    )
    duplicate_follow_up = (
        "none - reused approved document repo artifact"
        if approved_document_repo
        else "none - reused earlier in this run"
    )
    missing_follow_up = (
        "add or refresh this program in the approved document repo"
        if approved_document_repo
        else "scan this program in current run"
    )
    entries: list[ProgramEntry] = []
    warnings: list[str] = []
    seen: dict[str, ProgramEntry] = {}
    for index, program in enumerate(programs, start=1):
        normalized = normalize_program_name(program, lookup)
        if normalized in seen:
            first = seen[normalized]
            has_current_artifact = first.artifact_root is not None
            warnings.append(
                f"Duplicate normalized program name {normalized!r}; "
                + (
                    f"reusing artifact from order {first.order}"
                    if has_current_artifact
                    else f"will resolve once from order {first.order} before reuse"
                )
            )
            entry = ProgramEntry(
                input_name=program,
                normalized_name=normalized,
                order=index,
                run_resolution=duplicate_resolution if has_current_artifact else RUN_PENDING,
                artifact_root=first.artifact_root,
                artifact_source=first.artifact_source if has_current_artifact else "source_scan_required",
                tier=first.tier,
                compact_artifacts=first.compact_artifacts,
                follow_up=duplicate_follow_up if has_current_artifact else missing_follow_up,
            )
            entries.append(entry)
            continue

        found_artifact_root, matches = find_program_artifact_root(artifact_root, normalized, lookup)
        if len(matches) > 1:
            warnings.append(
                f"Program {normalized} matched multiple artifact folders; using {found_artifact_root}: "
                + ", ".join(matches)
            )
        if found_artifact_root:
            run_resolution = present_resolution
            source = present_source
            follow_up = present_follow_up
        else:
            run_resolution = RUN_PENDING
            source = "source_scan_required"
            follow_up = missing_follow_up
        entry = ProgramEntry(
            input_name=program,
            normalized_name=normalized,
            order=index,
            run_resolution=run_resolution,
            artifact_root=found_artifact_root,
            artifact_source=source,
            tier=infer_tier(found_artifact_root, workspace),
            compact_artifacts=collect_artifact_statuses(artifact_root, found_artifact_root),
            follow_up=follow_up,
        )
        entries.append(entry)
        seen[normalized] = entry
    return entries, warnings


def configured_inventory_dir(config: dict[str, Any]) -> Path:
    source_inventory = profile_source_inventory(config)
    value = source_inventory.get("default_cache_dir") or DEFAULT_SOURCE_INVENTORY_DIR.as_posix()
    return Path(str(value))


def inventory_filenames(config: dict[str, Any]) -> tuple[str, str]:
    source_inventory = profile_source_inventory(config)
    return (
        str(source_inventory.get("program_list_filename") or DEFAULT_PROGRAM_LIST_FILENAME),
        str(source_inventory.get("scan_summary_filename") or DEFAULT_SCAN_SUMMARY_FILENAME),
    )


def resolve_inventory_dir(
    *,
    source_root: Path | None,
    inventory_dir: Path | None,
    config: dict[str, Any],
) -> Path | None:
    if inventory_dir is not None:
        return inventory_dir
    default_dir = configured_inventory_dir(config)
    if source_root is not None:
        return source_root / default_dir
    return None


def load_inventory_rows(program_list_path: Path) -> dict[str, dict[str, str]]:
    if not program_list_path.is_file():
        return {}
    with program_list_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_member: dict[str, dict[str, str]] = {}
    for row in rows:
        member = (row.get("member") or "").strip()
        if member:
            by_member[member.upper()] = row
    return by_member


def summary_revision(summary: Any) -> dict[str, Any]:
    if not isinstance(summary, dict):
        return {}
    revision = summary.get("source_revision")
    if isinstance(revision, dict):
        return revision
    key = summary.get("source_revision_key")
    return {"key": key} if key else {}


def inventory_freshness(
    *,
    files_present: bool,
    source_root: Path | None,
    current_revision: dict[str, Any] | None,
    inventory_revision: dict[str, Any],
) -> tuple[str, str]:
    if not files_present:
        return "missing", "rerun_repo_inventory_scan"
    if source_root is None:
        return "unchecked_no_source_root", "provide_source_root_to_compare_revision"
    if not current_revision:
        return "unknown_current_revision", "rerun_repo_inventory_scan"
    if current_revision.get("type") != "git":
        return "unknown_revision", "rerun_repo_inventory_scan"
    if current_revision.get("dirty") is not False:
        return "dirty_source", "rerun_repo_inventory_scan"
    if not inventory_revision.get("key"):
        return "unknown_inventory_revision", "rerun_repo_inventory_scan"
    if inventory_revision.get("type") == "git" and inventory_revision.get("dirty") is not False:
        return "dirty_inventory_source", "rerun_repo_inventory_scan"
    if inventory_revision.get("key") == current_revision.get("key"):
        return "fresh", "reuse_inventory"
    return "stale", "rerun_repo_inventory_scan"


def inventory_program_statuses(
    *,
    entries: list[ProgramEntry],
    inventory_rows: dict[str, dict[str, str]],
    files_present: bool,
    freshness: str,
) -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    targeted_scan_allowed = freshness == "fresh"
    for entry in entries:
        if entry.run_resolution in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO}:
            statuses.append(
                {
                    "program": entry.normalized_name,
                    "run_resolution": entry.run_resolution,
                    "inventory_status": (
                        "not_needed_approved_document_repo_artifact_present"
                        if entry.run_resolution == RUN_ARTIFACT_REPO
                        else "not_needed_current_artifact_present"
                    ),
                    "source_path": None,
                    "size_tier": entry.tier,
                    "targeted_scan_allowed": False,
                }
            )
            continue

        row = inventory_rows.get(entry.normalized_name.upper())
        if freshness == "not_checked":
            inventory_status = "not_checked"
        elif not files_present:
            inventory_status = "inventory_cache_missing"
        elif row:
            inventory_status = "found"
        else:
            inventory_status = "missing_from_inventory"
        statuses.append(
            {
                "program": entry.normalized_name,
                "run_resolution": entry.run_resolution,
                "inventory_status": inventory_status,
                "source_path": row.get("path") if row else None,
                "source_kind": row.get("source_kind") if row else None,
                "size_tier": row.get("size_tier") if row else entry.tier,
                "default_output_profile": row.get("default_output_profile") if row else None,
                "targeted_scan_allowed": targeted_scan_allowed and row is not None,
            }
        )
    return statuses


def build_source_inventory_status(
    *,
    entries: list[ProgramEntry],
    source_root: Path | None,
    inventory_dir: Path | None,
    config: dict[str, Any],
) -> dict[str, Any]:
    default_dir = configured_inventory_dir(config)
    resolved_inventory_dir = resolve_inventory_dir(
        source_root=source_root,
        inventory_dir=inventory_dir,
        config=config,
    )
    program_list_name, scan_summary_name = inventory_filenames(config)
    if resolved_inventory_dir is None:
        program_statuses = inventory_program_statuses(
            entries=entries,
            inventory_rows={},
            files_present=False,
            freshness="not_checked",
        )
        return {
            "default_inventory_dir": default_dir.as_posix(),
            "inventory_dir": None,
            "program_list": {"path": program_list_name, "status": "not_checked"},
            "scan_summary": {"path": scan_summary_name, "status": "not_checked"},
            "freshness": "not_checked",
            "action": "provide_source_root_to_check_inventory",
            "source_revision": None,
            "inventory_revision": None,
            "programs": program_statuses,
        }

    program_list_path = resolved_inventory_dir / program_list_name
    scan_summary_path = resolved_inventory_dir / scan_summary_name
    files_present = program_list_path.is_file() and scan_summary_path.is_file()
    current_revision = (
        detect_source_revision(source_root.resolve(), ignore_paths=[resolved_inventory_dir])
        if source_root
        else None
    )
    loaded_summary = load_yaml(scan_summary_path) if scan_summary_path.is_file() else {}
    inventory_revision = summary_revision(loaded_summary)
    freshness, action = inventory_freshness(
        files_present=files_present,
        source_root=source_root,
        current_revision=current_revision,
        inventory_revision=inventory_revision,
    )
    rows = load_inventory_rows(program_list_path)
    return {
        "default_inventory_dir": default_dir.as_posix(),
        "inventory_dir": str(resolved_inventory_dir),
        "program_list": {
            "path": str(program_list_path),
            "status": "present" if program_list_path.is_file() else "missing",
        },
        "scan_summary": {
            "path": str(scan_summary_path),
            "status": "present" if scan_summary_path.is_file() else "missing",
        },
        "freshness": freshness,
        "action": action,
        "source_revision": current_revision,
        "inventory_revision": inventory_revision or None,
        "programs": inventory_program_statuses(
            entries=entries,
            inventory_rows=rows,
            files_present=files_present,
            freshness=freshness,
        ),
    }


def apply_source_inventory_blockers(
    entries: list[ProgramEntry],
    source_inventory: dict[str, Any],
) -> list[ProgramEntry]:
    if source_inventory.get("freshness") != "fresh":
        return entries
    inventory_rows = {
        str(row.get("program") or ""): row
        for row in source_inventory.get("programs", []) or []
        if isinstance(row, dict)
    }
    updated: list[ProgramEntry] = []
    for entry in entries:
        row = inventory_rows.get(entry.normalized_name)
        if (
            entry.run_resolution == RUN_PENDING
            and row
            and row.get("inventory_status") == "missing_from_inventory"
        ):
            updated.append(
                replace(
                    entry,
                    run_resolution=RUN_BLOCKED,
                    artifact_source="source_inventory_missing",
                    follow_up=(
                        "confirm SME program name/library/alias or provide source; "
                        "fresh source inventory did not contain this program"
                    ),
                )
            )
            row["run_resolution"] = RUN_BLOCKED
            row["targeted_scan_allowed"] = False
        else:
            updated.append(entry)
    return updated


def entry_to_dict(entry: ProgramEntry) -> dict[str, Any]:
    return {
        "input_name": entry.input_name,
        "normalized_name": entry.normalized_name,
        "order": entry.order,
        "run_resolution": entry.run_resolution,
        "artifact_root": entry.artifact_root,
        "artifact_source": entry.artifact_source,
        "tier": entry.tier,
        "compact_artifacts": {
            key: {"path": status.path, "status": status.status}
            for key, status in entry.compact_artifacts.items()
        },
        "follow_up": entry.follow_up,
    }


def build_manifest(
    *,
    review_name: str,
    programs: list[str],
    artifact_root: Path,
    config: dict[str, Any],
    working_branch: str | None,
    source_root: Path | None = None,
    inventory_dir: Path | None = None,
    program_first: bool = False,
    artifact_repo_mode: str = ARTIFACT_REPO_CURRENT_RUN,
) -> dict[str, Any]:
    lookup = profile_lookup(config)
    workspace = profile_workspace(config)
    entries, warnings = build_program_entries(
        programs,
        artifact_root,
        config,
        artifact_repo_mode=artifact_repo_mode,
    )
    source_inventory = build_source_inventory_status(
        entries=entries,
        source_root=source_root,
        inventory_dir=inventory_dir,
        config=config,
    )
    entries = apply_source_inventory_blockers(entries, source_inventory)
    return {
        "schema_version": "0.1",
        "generated_by": "program_set_core_review.py",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "review_name": review_name,
        "review_slug": slugify(review_name),
        "run_profile": {
            "repo": lookup.get("repo") or workspace.get("repo"),
            "working_branch": working_branch,
            "artifact_root": str(artifact_root),
            "artifact_repo_mode": artifact_repo_mode,
            "program_first": program_first,
            "cross_run_reuse": artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT,
            "reuse_policy": (
                "approved_document_repo_clone"
                if artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT
                else "current_run_only"
            ),
        },
        "program_resolution_profile": {
            "program_folder_patterns": lookup.get("program_folder_patterns", ["modules/*/{PROGRAM}"]),
            "program_name_normalization": lookup.get("program_name_normalization", {}),
        },
        "workspace_profile": {
            "program_set_review_parent": workspace.get("program_set_review_parent"),
            "program_tier_roots": workspace.get("program_tier_roots", {}),
            "write_to_main": workspace.get("write_to_main", False),
        },
        "source_inventory": source_inventory,
        "programs": [entry_to_dict(entry) for entry in entries],
        "warnings": warnings,
    }


def artifact_summary(entry: dict[str, Any]) -> str:
    compact = entry.get("compact_artifacts", {}) or {}
    labels = []
    for filename in REQUIRED_COMPACT_ARTIFACTS:
        key = artifact_key(filename)
        status = (compact.get(key) or {}).get("status", "missing")
        labels.append(f"{filename}={status}")
    return "; ".join(labels)


def is_normal_program(entry: dict[str, Any]) -> bool:
    return entry.get("tier") == "normal_program"


def routine_detail_status(entry: dict[str, Any]) -> str:
    compact = entry.get("compact_artifacts", {}) or {}
    status = (compact.get(artifact_key("routine-logic-details.yaml")) or {}).get(
        "status", "missing"
    )
    if status == "present":
        return "present"
    return "missing_when_needed"


def routine_logic_evidence_status(entry: dict[str, Any]) -> str:
    if entry.get("run_resolution") not in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO}:
        return "N/A"
    markdown = present_missing(entry, "routine-logic-details.md")
    yaml = present_missing(entry, "routine-logic-details.yaml")
    if markdown == "present" and yaml == "present":
        return "present"
    missing = []
    if markdown != "present":
        missing.append("routine-logic-details.md")
    if yaml != "present":
        missing.append("routine-logic-details.yaml")
    return "missing: " + ", ".join(missing)


def present_missing(entry: dict[str, Any], artifact_filename: str) -> str:
    if entry.get("run_resolution") not in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO}:
        return "N/A"
    if artifact_filename == "routine-logic-details.yaml":
        status = routine_detail_status(entry)
        return "present" if status == "present" else "missing"
    status = ((entry.get("compact_artifacts", {}) or {}).get(artifact_key(artifact_filename)) or {}).get(
        "status", "missing"
    )
    return "present" if status == "present" else "missing"


def render_sources_table(programs: list[dict[str, Any]]) -> str:
    lines = [
        "| Program | Analysis Directory | Run Resolution | Tier | Compact Artifacts Used | Follow-up |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in programs:
        program = entry.get("normalized_name") or ""
        artifact_root = entry.get("artifact_root") or "pending source scan"
        resolution = entry.get("run_resolution") or "legacy_manifest_missing_run_resolution"
        tier = entry.get("tier") or "unknown"
        lines.append(
            f"| {program} | {artifact_root} | {resolution} | {tier} | {artifact_summary(entry)} | {entry.get('follow_up', '')} |"
        )
    return "\n".join(lines)


def render_completeness_table(programs: list[dict[str, Any]]) -> str:
    lines = [
        "| Program | Expected In Scope From | Run Resolution | Routine Logic Evidence | Message Inventory | Missing / Targeted Follow-up |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in programs:
        program = entry.get("normalized_name") or ""
        resolution = entry.get("run_resolution") or "legacy_manifest_missing_run_resolution"
        routine_logic = routine_logic_evidence_status(entry)
        messages = present_missing(entry, "message-inventory.yaml")
        lines.append(
            f"| {program} | SME-provided flow | {resolution} | {routine_logic} | {messages} | {entry.get('follow_up', '')} |"
        )
    return "\n".join(lines)


def render_run_profile(manifest: dict[str, Any]) -> str:
    run_profile = manifest.get("run_profile", {}) or {}
    resolution_profile = manifest.get("program_resolution_profile", {}) or {}
    workspace = manifest.get("workspace_profile", {}) or {}
    patterns = ", ".join(str(pattern) for pattern in resolution_profile.get("program_folder_patterns", []))
    return "\n".join(
        [
            "| Field | Value |",
            "| --- | --- |",
            f"| Repo | {run_profile.get('repo') or ''} |",
            f"| Working Branch | {run_profile.get('working_branch') or ''} |",
            f"| Artifact Root | {run_profile.get('artifact_root') or ''} |",
            f"| Artifact Repo Mode | {run_profile.get('artifact_repo_mode') or ARTIFACT_REPO_CURRENT_RUN} |",
            f"| Reuse Policy | {run_profile.get('reuse_policy') or 'current_run_only'} |",
            f"| Cross-Run Reuse | {str(run_profile.get('cross_run_reuse', False)).lower()} |",
            f"| Program Folder Patterns | {patterns} |",
            f"| Program Set Review Parent | {workspace.get('program_set_review_parent') or ''} |",
        ]
    )


def render_source_inventory(manifest: dict[str, Any]) -> str:
    source_inventory = manifest.get("source_inventory", {}) or {}
    program_list = source_inventory.get("program_list", {}) or {}
    scan_summary = source_inventory.get("scan_summary", {}) or {}
    program_list_label = Path(str(program_list.get("path") or DEFAULT_PROGRAM_LIST_FILENAME)).name
    scan_summary_label = Path(str(scan_summary.get("path") or DEFAULT_SCAN_SUMMARY_FILENAME)).name
    lines = [
        "| Field | Value |",
        "| --- | --- |",
        f"| Default Inventory Dir | {source_inventory.get('default_inventory_dir') or ''} |",
        f"| Inventory Dir Checked | {source_inventory.get('inventory_dir') or ''} |",
        f"| {program_list_label} | {program_list.get('status') or ''}: {program_list.get('path') or ''} |",
        f"| {scan_summary_label} | {scan_summary.get('status') or ''}: {scan_summary.get('path') or ''} |",
        f"| Freshness | {source_inventory.get('freshness') or ''} |",
        f"| Action | {source_inventory.get('action') or ''} |",
    ]

    program_rows = source_inventory.get("programs", []) or []
    if not program_rows:
        return "\n".join(lines)
    lines.extend(
        [
            "",
            "| Program | Run Resolution | Inventory Status | Source Path | Tier | Targeted Scan Allowed |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in program_rows:
        lines.append(
            "| {program} | {lookup} | {status} | {path} | {tier} | {allowed} |".format(
                program=row.get("program") or "",
                lookup=row.get("run_resolution") or "",
                status=row.get("inventory_status") or "",
                path=row.get("source_path") or "",
                tier=row.get("size_tier") or "",
                allowed="yes" if row.get("targeted_scan_allowed") else "no",
            )
        )
    return "\n".join(lines)


def render_review_skeleton(manifest: dict[str, Any]) -> str:
    programs = manifest.get("programs", []) or []
    return f"""# Program Set SME Core Review: {manifest["review_name"]}

## Program Set Reading Summary

<!-- Replace this placeholder with a SME-readable summary of what this program
set does, which processing layers it covers, and whether the review is
standalone_exploratory, draft, or chain_ready. Do not leave an artifact list as
the summary. -->

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First |
| --- | --- | --- |
| Entry / dispatch | [programs and main routines] | [reader-first explanation] |
| Calculation | [programs and main routines] | [reader-first explanation] |
| Validation | [programs and main routines] | [reader-first explanation] |
| Exception / message | [programs and main routines] | [reader-first explanation] |
| Persistence / finalization | [programs and main routines] | [reader-first explanation] |

## Calculation Logic

<!-- Self-contained SME view: write the actual calculation/assignment logic here.
Use Supporting Detail for traceability only, not as a substitute for the explanation. -->

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Validation Logic

<!-- Self-contained SME view: write the actual validation condition, status/code, carrier, and outcome here.
Use Supporting Detail for traceability only, not as a substitute for the explanation. -->

| Message / Status / Outcome | Description | Program | Routine | Trigger Chain | Carrier / Destination | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Exception Handling

<!-- Self-contained SME view: write the actual error path, detection, handling action, and outcome here.
Use Supporting Detail for traceability only, not as a substitute for the explanation. -->

| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Message Inventory

<!-- Self-contained SME view: include exact message/status/literal text and meaning here.
Use Detail Refs for traceability only, not as a substitute for the explanation. -->

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Trigger / Handler | Effect | Detail Refs | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Core Completeness Ledger

{render_completeness_table(programs)}

## Sources

{render_sources_table(programs)}

## Run Profile

{render_run_profile(manifest)}

## Source Inventory Cache

{render_source_inventory(manifest)}
"""


def write_build_outputs(manifest: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "program-set-core-input-manifest.yaml"
    review_path = output_dir / "program-set-sme-core-review.md"
    manifest_path.write_text(dump_yaml(manifest), encoding="utf-8")
    review_path.write_text(render_review_skeleton(manifest), encoding="utf-8")
    return manifest_path, review_path


def h2_positions(markdown: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    for match in re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M):
        positions.setdefault(match.group(1).strip(), match.start())
    return positions


def h2_section_block(markdown: str, section: str) -> str:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M))
    for index, match in enumerate(matches):
        if match.group(1).strip() != section:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        return markdown[start:end]
    return ""


def text_between(markdown: str, start_label: str, end_label: str | None = None) -> str:
    start = markdown.find(start_label)
    if start == -1:
        return ""
    start += len(start_label)
    if end_label is None:
        end = len(markdown)
    else:
        end = markdown.find(end_label, start)
        if end == -1:
            end = len(markdown)
    return markdown[start:end]


def markdown_table_rows_by_first_column(block: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or not cells[0] or cells[0] == "Program":
            continue
        if set(cells[0]) <= {"-"}:
            continue
        rows[cells[0]] = cells
    return rows


def strip_markdown_comments(block: str) -> str:
    return re.sub(r"<!--.*?-->", "", block, flags=re.S)


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def table_lines(block: str) -> list[tuple[int, list[str]]]:
    lines: list[tuple[int, list[str]]] = []
    for index, line in enumerate(block.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        lines.append((index, cells))
    return lines


def table_data_rows(block: str) -> list[list[str]]:
    raw_lines = block.splitlines()
    data_rows: list[list[str]] = []
    for index, cells in table_lines(block):
        if is_table_separator(raw_lines[index]):
            continue
        next_line = raw_lines[index + 1] if index + 1 < len(raw_lines) else ""
        if is_table_separator(next_line):
            continue
        data_rows.append(cells)
    return data_rows


def table_has_headers(block: str, required_headers: tuple[str, ...]) -> bool:
    for _index, cells in table_lines(block):
        normalized = {cell.strip().lower() for cell in cells}
        if all(header.lower() in normalized for header in required_headers):
            return True
    return False


PLACEHOLDER_RE = re.compile(
    r"\b(todo|tbd|pending|placeholder|fill\s+in|to\s+be\s+completed|"
    r"artifact\s+list|reader-first explanation|programs and main routines)\b",
    re.I,
)

ARTIFACT_REF_RE = re.compile(
    r"\b(?:program-analysis(?:-summary)?|source-index|routine-index|"
    r"message-inventory|routine-logic-details|file-io-inventory|"
    r"field-mutation-matrix|sql-inventory)\.(?:md|ya?ml)\b",
    re.I,
)

DETAIL_REF_RE = re.compile(
    r"\b(?:RLOG|MSG|LINEAGE|PERSIST|DATA|EXCHAIN|TBD|EV)-[A-Za-z0-9_-]+\b"
)


def reader_words(text: str) -> list[str]:
    without_refs = DETAIL_REF_RE.sub(" ", ARTIFACT_REF_RE.sub(" ", text))
    without_status_noise = re.sub(r"\b(?:confirmed|inferred|unresolved|present|missing|n/a)\b", " ", without_refs, flags=re.I)
    return re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", without_status_noise)


def prose_and_table_detail(block: str) -> str:
    clean = strip_markdown_comments(block)
    raw_lines = clean.splitlines()
    details: list[str] = []
    for index, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            if is_table_separator(stripped):
                continue
            next_line = raw_lines[index + 1] if index + 1 < len(raw_lines) else ""
            if is_table_separator(next_line):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            details.append(" ".join(cells))
            continue
        details.append(stripped)
    return "\n".join(details)


def has_reader_useful_detail(block: str, *, minimum_words: int = 18) -> bool:
    detail = prose_and_table_detail(block)
    if not detail.strip():
        return False
    if PLACEHOLDER_RE.search(detail):
        return False
    return len(reader_words(detail)) >= minimum_words


def is_placeholder_cell(value: str) -> bool:
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        return True
    if re.fullmatch(r"\[[^\]]+\]", stripped):
        return True
    if lowered in {"todo", "tbd", "pending", "placeholder", "n/a"}:
        return True
    return any(
        marker in lowered
        for marker in (
            "reader-first explanation",
            "programs and main routines",
            "fill in",
            "to be completed",
        )
    )


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    programs = manifest.get("programs")
    if not isinstance(programs, list) or not programs:
        return ["manifest has no programs[] entries"]
    run_profile = manifest.get("run_profile", {}) or {}
    artifact_repo_mode = run_profile.get("artifact_repo_mode") or ARTIFACT_REPO_CURRENT_RUN
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in programs:
        name = str(entry.get("normalized_name") or "")
        if not name:
            findings.append("program entry missing normalized_name")
            continue
        by_name.setdefault(name, []).append(entry)
        if "run_resolution" not in entry and "central_lookup_result" in entry:
            findings.append(
                f"{name} uses legacy central_lookup_result; rebuild the manifest with the no-cross-run-reuse builder"
            )
            continue
        resolution = entry.get("run_resolution")
        if resolution not in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO, RUN_PENDING, RUN_BLOCKED}:
            findings.append(f"{name} has invalid run_resolution: {resolution}")
        if resolution in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO} and not entry.get("artifact_root"):
            findings.append(f"{name} {resolution} missing artifact_root")
        if resolution == RUN_ANALYZED and entry.get("artifact_source") != "delivery_working_branch":
            findings.append(f"{name} analyzed_this_run must use artifact_source delivery_working_branch")
        if resolution == RUN_REUSED and entry.get("artifact_source") != "delivery_working_branch":
            findings.append(f"{name} reused_same_run has invalid artifact_source")
        if resolution == RUN_ARTIFACT_REPO:
            if artifact_repo_mode != ARTIFACT_REPO_APPROVED_DOCUMENT:
                findings.append(
                    f"{name} reused_artifact_repo requires artifact_repo_mode {ARTIFACT_REPO_APPROVED_DOCUMENT}"
                )
            if entry.get("artifact_source") != "approved_document_repo":
                findings.append(f"{name} reused_artifact_repo must use artifact_source approved_document_repo")
        if resolution in {RUN_PENDING, RUN_BLOCKED} and entry.get("artifact_root"):
            findings.append(f"{name} {resolution} must not have artifact_root")
        if resolution in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO}:
            compact = entry.get("compact_artifacts", {}) or {}
            missing_artifacts = [
                filename
                for filename in REQUIRED_COMPACT_ARTIFACTS
                if (compact.get(artifact_key(filename)) or {}).get("status") != "present"
            ]
            if missing_artifacts:
                findings.append(
                    f"{name} {resolution} missing required compact artifacts: "
                    + ", ".join(missing_artifacts)
                )
    for name, duplicates in by_name.items():
        if len(duplicates) <= 1:
            continue
        first = duplicates[0]
        first_resolution = first.get("run_resolution")
        first_artifact_root = first.get("artifact_root")
        for duplicate in duplicates[1:]:
            resolution = duplicate.get("run_resolution")
            artifact_root = duplicate.get("artifact_root")
            if first_artifact_root:
                expected_duplicate = RUN_ARTIFACT_REPO if first.get("run_resolution") == RUN_ARTIFACT_REPO else RUN_REUSED
                if resolution != expected_duplicate:
                    findings.append(f"{name} duplicate with artifact must use {expected_duplicate}")
                if artifact_root != first_artifact_root:
                    findings.append(f"{name} duplicate artifact_root must match the first artifact")
            elif first_resolution in {RUN_PENDING, RUN_BLOCKED}:
                if resolution not in {RUN_PENDING, RUN_BLOCKED}:
                    findings.append(f"{name} duplicate without a current-run artifact must remain pending/blocked")
                if artifact_root:
                    findings.append(f"{name} duplicate pending/blocked entry must not have artifact_root")
    return findings


def validate_review(markdown: str, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    positions = h2_positions(markdown)
    missing_sections = [section for section in READER_FIRST_SECTIONS if section not in positions]
    if missing_sections:
        findings.append(
            "program-set review missing required reader-first ## sections: "
            + ", ".join(missing_sections)
        )
    else:
        ordered = [positions[section] for section in READER_FIRST_SECTIONS]
        if ordered != sorted(ordered):
            findings.append(
                "program-set review reader-first core sections must appear before audit/control sections"
            )
    for section in FORBIDDEN_FULL_FLOW_SECTIONS:
        if re.search(rf"^##\s+{re.escape(section)}\s*$", markdown, re.M):
            findings.append(f"program-set review contains forbidden full-flow section: {section}")

    summary_block = h2_section_block(markdown, "Program Set Reading Summary")
    if summary_block:
        summary_detail = prose_and_table_detail(summary_block)
        layer_terms = sum(
            1
            for term in (
                "entry",
                "dispatch",
                "calculation",
                "validation",
                "exception",
                "message",
                "persistence",
                "finalization",
            )
            if re.search(rf"\b{term}\b", summary_detail, re.I)
        )
        has_status = re.search(r"\b(standalone_exploratory|chain_ready|draft)\b", summary_detail, re.I)
        if (
            not has_reader_useful_detail(summary_block, minimum_words=25)
            or layer_terms < 2
            or not has_status
            or ARTIFACT_REF_RE.search(summary_detail)
        ):
            findings.append(
                "Program Set Reading Summary is placeholder/artifact-only or missing reader-useful flow context"
            )

    overview_block = h2_section_block(markdown, "Cross-Program Processing Overview")
    if overview_block:
        required_headers = (
            "Processing Layer",
            "Programs / Main Routines",
            "What To Understand First",
        )
        if not table_has_headers(overview_block, required_headers):
            findings.append("Cross-Program Processing Overview missing required table headers")
        overview_rows = table_data_rows(overview_block)
        if len(overview_rows) < 4:
            findings.append("Cross-Program Processing Overview must include processing-layer rows")
        for row in overview_rows:
            if len(row) < 3 or any(is_placeholder_cell(cell or "") for cell in row[:3]):
                findings.append("Cross-Program Processing Overview has placeholder processing-layer detail")
                break

    for section in CORE_SECTIONS:
        block = h2_section_block(markdown, section)
        if block and not has_reader_useful_detail(block):
            findings.append(f"{section} lacks reader-useful detail")

    sources_block = h2_section_block(markdown, "Sources")
    ledger_block = h2_section_block(markdown, "Core Completeness Ledger")
    source_rows = markdown_table_rows_by_first_column(sources_block)
    ledger_rows = markdown_table_rows_by_first_column(ledger_block)
    for entry in manifest.get("programs", []) or []:
        program = str(entry.get("normalized_name") or "")
        if not program:
            continue
        if program not in source_rows:
            findings.append(f"{program} missing from Sources table")
        if program not in ledger_rows:
            findings.append(f"{program} missing from Core Completeness Ledger")
        resolution = str(entry.get("run_resolution") or "")
        if resolution and program in ledger_rows and resolution not in ledger_rows[program]:
            findings.append(f"{program} run_resolution {resolution} missing from Core Completeness Ledger")
    return findings


def validate(manifest_path: Path, review_path: Path) -> list[str]:
    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        return ["manifest is not a YAML mapping"]
    findings = validate_manifest(manifest)
    if not review_path.is_file():
        findings.append(f"missing review artifact: {review_path}")
        return findings
    findings.extend(validate_review(review_path.read_text(encoding="utf-8"), manifest))
    return findings


def build_command(args: argparse.Namespace) -> int:
    config = load_yaml(args.profile)
    if not isinstance(config, dict):
        raise SystemExit("delivery profile must be a YAML mapping")
    programs = read_programs_file(args.programs_file)
    if not programs:
        raise SystemExit("programs file has no program names")
    if args.force_rescan_file is not None:
        raise SystemExit(
            "--force-rescan-file is no longer supported for program-flow core review. "
            "Rebuild with no cross-run reuse and analyze the program in the current run."
        )
    if args.delivery_root is not None:
        raise SystemExit(
            "--delivery-root is no longer supported for program-flow core review. "
            "Use --working-root <delivery-working-checkout> as the current-run artifact root."
        )
    artifact_root = args.working_root or args.output_root or args.delivery_root
    if artifact_root is None:
        raise SystemExit("provide --working-root or --output-root for program artifacts")
    if not artifact_root.is_dir():
        raise SystemExit(f"artifact root not found or not a directory: {artifact_root}")
    if args.source_root is not None and not args.source_root.is_dir():
        raise SystemExit(f"source root not found or not a directory: {args.source_root}")
    manifest = build_manifest(
        review_name=args.review_name,
        programs=programs,
        artifact_root=artifact_root,
        config=config,
        working_branch=args.working_branch,
        source_root=args.source_root,
        inventory_dir=args.inventory_dir,
        program_first=args.program_first,
        artifact_repo_mode=args.artifact_repo_mode,
    )
    manifest_path, review_path = write_build_outputs(manifest, args.output_dir)
    print(f"Wrote {manifest_path}")
    print(f"Wrote {review_path}")
    return 0


def validate_command(args: argparse.Namespace) -> int:
    findings = validate(args.manifest, args.review)
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    print("OK: program-set SME core review contract passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build manifest and review skeleton")
    build.add_argument("--review-name", required=True)
    build.add_argument("--programs-file", type=Path, required=True)
    build.add_argument("--working-root", type=Path, help="Delivery working checkout, approved document repo clone, or artifact root")
    build.add_argument("--output-root", type=Path, help="Alias for artifact root")
    build.add_argument(
        "--artifact-repo-mode",
        choices=[ARTIFACT_REPO_CURRENT_RUN, ARTIFACT_REPO_APPROVED_DOCUMENT],
        default=ARTIFACT_REPO_CURRENT_RUN,
        help=(
            "Use current_run for active scan branches. Use approved_document_repo when "
            "--working-root is a local clone containing approved all-program scan artifacts."
        ),
    )
    build.add_argument(
        "--delivery-root",
        type=Path,
        help="Deprecated; no longer supported for program-flow core review",
    )
    build.add_argument(
        "--force-rescan-file",
        type=Path,
        help="Deprecated; no longer supported for program-flow core review",
    )
    build.add_argument("--source-root", type=Path)
    build.add_argument("--inventory-dir", type=Path)
    build.add_argument(
        "--program-first",
        action="store_true",
        help=(
            "Compatibility marker recorded in run_profile; the default workflow is already "
            "program-evidence first. For approved document repo reuse, pass "
            "--artifact-repo-mode approved_document_repo."
        ),
    )
    build.add_argument("--profile", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, required=True)
    build.add_argument("--working-branch")
    build.set_defaults(func=build_command)

    validate_parser = subparsers.add_parser("validate", help="Validate a completed review")
    validate_parser.add_argument("--manifest", type=Path, required=True)
    validate_parser.add_argument("--review", type=Path, required=True)
    validate_parser.set_defaults(func=validate_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
