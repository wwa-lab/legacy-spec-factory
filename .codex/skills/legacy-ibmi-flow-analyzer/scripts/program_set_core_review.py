#!/usr/bin/env python3
"""Build and validate program-set SME core review scaffolds.

The builder is intentionally deterministic: it discovers program artifact
folders from a delivery repo remote-main checkout/cache, writes a manifest, and
renders a fixed review skeleton. The validator checks structure and coverage;
it does not judge whether the LLM-written summaries are semantically correct.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CORE_SECTIONS = (
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
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
    "Flow Replay Path",
    "Cross-Program Field Lineage",
    "Flow Persistence Matrix",
    "Branch Points",
    "UI Surfaces",
    "Error Propagation & Commit Boundaries",
    "Exception Propagation Chain",
    "Business Capability Seeds",
    "Review Checklist",
    "SME Checklist",
)

REQUIRED_COMPACT_ARTIFACTS = (
    "program-analysis-summary.yaml",
    "routine-logic-details.yaml",
    "message-inventory.yaml",
)

OPTIONAL_COMPACT_ARTIFACTS = (
    "source-index.yaml",
    "file-io-inventory.yaml",
    "field-mutation-matrix.yaml",
    "sql-inventory.yaml",
)

LOOKUP_FOUND = "found_on_remote_main"
LOOKUP_NOT_FOUND = "not_found_on_remote_main"
LOOKUP_REMOTE_UNAVAILABLE = "remote_unavailable"

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
    central_lookup_result: str
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
    return config.get("delivery_artifact_lookup_profile", {}) or {}


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


def collect_artifact_statuses(delivery_root: Path, artifact_root: str | None) -> dict[str, ArtifactStatus]:
    statuses: dict[str, ArtifactStatus] = {}
    root_path = delivery_root / artifact_root if artifact_root else None
    for filename in REQUIRED_COMPACT_ARTIFACTS + OPTIONAL_COMPACT_ARTIFACTS:
        key = artifact_key(filename)
        if root_path is None:
            statuses[key] = ArtifactStatus(path=filename, status="missing")
            continue
        candidate = root_path / filename
        statuses[key] = ArtifactStatus(
            path=relative_path(delivery_root, candidate),
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
    delivery_root: Path,
    program: str,
    lookup: dict[str, Any],
) -> tuple[str | None, list[str]]:
    patterns = lookup.get("program_folder_patterns") or ["modules/*/{PROGRAM}"]
    matches: list[Path] = []
    for pattern in patterns:
        resolved_pattern = str(pattern).replace("{PROGRAM}", program)
        matches.extend(path for path in delivery_root.glob(resolved_pattern) if path.is_dir())
    relative_matches = sorted({relative_path(delivery_root, path) for path in matches})
    return (relative_matches[0] if relative_matches else None, relative_matches)


def build_program_entries(
    programs: list[str],
    delivery_root: Path,
    config: dict[str, Any],
    working_root: Path | None = None,
) -> tuple[list[ProgramEntry], list[str]]:
    lookup = profile_lookup(config)
    workspace = profile_workspace(config)
    entries: list[ProgramEntry] = []
    warnings: list[str] = []
    seen: dict[str, str] = {}
    for index, program in enumerate(programs, start=1):
        normalized = normalize_program_name(program, lookup)
        if normalized in seen:
            warnings.append(
                f"Duplicate normalized program name {normalized!r} from {seen[normalized]!r} and {program!r}"
            )
        seen[normalized] = program
        artifact_root, matches = find_program_artifact_root(delivery_root, normalized, lookup)
        if len(matches) > 1:
            warnings.append(
                f"Program {normalized} matched multiple artifact folders; using {artifact_root}: "
                + ", ".join(matches)
            )
        if artifact_root:
            result = LOOKUP_FOUND
            source = "remote_main"
            follow_up = "none"
            artifact_status_root = delivery_root
        elif working_root:
            artifact_root, working_matches = find_program_artifact_root(working_root, normalized, lookup)
            if len(working_matches) > 1:
                warnings.append(
                    f"Program {normalized} matched multiple working-branch artifact folders; "
                    f"using {artifact_root}: " + ", ".join(working_matches)
                )
            if artifact_root:
                result = LOOKUP_NOT_FOUND
                source = "delivery_working_branch"
                follow_up = "none - source scan completed in working branch"
                artifact_status_root = working_root
            else:
                result = LOOKUP_NOT_FOUND
                source = "source_scan_required"
                follow_up = "scan this program"
                artifact_status_root = delivery_root
        else:
            result = LOOKUP_NOT_FOUND
            source = "source_scan_required"
            follow_up = "scan this program"
            artifact_status_root = delivery_root
        entries.append(
            ProgramEntry(
                input_name=program,
                normalized_name=normalized,
                order=index,
                central_lookup_result=result,
                artifact_root=artifact_root,
                artifact_source=source,
                tier=infer_tier(artifact_root, workspace),
                compact_artifacts=collect_artifact_statuses(artifact_status_root, artifact_root),
                follow_up=follow_up,
            )
        )
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
        if entry.central_lookup_result == LOOKUP_FOUND:
            statuses.append(
                {
                    "program": entry.normalized_name,
                    "central_lookup_result": entry.central_lookup_result,
                    "inventory_status": "not_needed_remote_main_reuse",
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
                "central_lookup_result": entry.central_lookup_result,
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


def entry_to_dict(entry: ProgramEntry) -> dict[str, Any]:
    return {
        "input_name": entry.input_name,
        "normalized_name": entry.normalized_name,
        "order": entry.order,
        "central_lookup_result": entry.central_lookup_result,
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
    delivery_root: Path,
    config: dict[str, Any],
    working_branch: str | None,
    working_root: Path | None = None,
    source_root: Path | None = None,
    inventory_dir: Path | None = None,
) -> dict[str, Any]:
    entries, warnings = build_program_entries(programs, delivery_root, config, working_root)
    lookup = profile_lookup(config)
    workspace = profile_workspace(config)
    source_inventory = build_source_inventory_status(
        entries=entries,
        source_root=source_root,
        inventory_dir=inventory_dir,
        config=config,
    )
    return {
        "schema_version": "0.1",
        "generated_by": "program_set_core_review.py",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "review_name": review_name,
        "review_slug": slugify(review_name),
        "delivery_repo": {
            "repo": lookup.get("repo") or workspace.get("repo"),
            "lookup_branch": lookup.get("branch", "main"),
            "working_branch": working_branch,
            "working_root_used": working_root is not None,
        },
        "lookup_profile": {
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


def present_missing(entry: dict[str, Any], artifact_filename: str) -> str:
    if entry.get("central_lookup_result") != LOOKUP_FOUND:
        return "N/A"
    status = ((entry.get("compact_artifacts", {}) or {}).get(artifact_key(artifact_filename)) or {}).get(
        "status", "missing"
    )
    return "present" if status == "present" else "missing"


def render_sources_table(programs: list[dict[str, Any]]) -> str:
    lines = [
        "| Program | Analysis Directory | Central Lookup Result | Tier | Compact Artifacts Used | Follow-up |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in programs:
        program = entry["normalized_name"]
        artifact_root = entry.get("artifact_root") or "pending source scan"
        result = entry["central_lookup_result"]
        tier = entry.get("tier") or "unknown"
        lines.append(
            f"| {program} | {artifact_root} | {result} | {tier} | {artifact_summary(entry)} | {entry.get('follow_up', '')} |"
        )
    return "\n".join(lines)


def render_completeness_table(programs: list[dict[str, Any]]) -> str:
    lines = [
        "| Program | Expected In Scope From | Central Lookup Result | Calculation Logic | Validation Logic | Exception Handling | Message Inventory | Missing / Targeted Follow-up |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in programs:
        program = entry["normalized_name"]
        result = entry["central_lookup_result"]
        logic = present_missing(entry, "routine-logic-details.yaml")
        validation = present_missing(entry, "routine-logic-details.yaml")
        exception = present_missing(entry, "routine-logic-details.yaml")
        messages = present_missing(entry, "message-inventory.yaml")
        lines.append(
            f"| {program} | SME-provided flow | {result} | {logic} | {validation} | {exception} | {messages} | {entry.get('follow_up', '')} |"
        )
    return "\n".join(lines)


def render_lookup_profile(manifest: dict[str, Any]) -> str:
    delivery_repo = manifest.get("delivery_repo", {}) or {}
    lookup = manifest.get("lookup_profile", {}) or {}
    workspace = manifest.get("workspace_profile", {}) or {}
    patterns = ", ".join(str(pattern) for pattern in lookup.get("program_folder_patterns", []))
    return "\n".join(
        [
            "| Field | Value |",
            "| --- | --- |",
            f"| Repo | {delivery_repo.get('repo') or ''} |",
            f"| Lookup Branch | {delivery_repo.get('lookup_branch') or 'main'} |",
            f"| Working Branch | {delivery_repo.get('working_branch') or ''} |",
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
            "| Program | Central Lookup Result | Inventory Status | Source Path | Tier | Targeted Scan Allowed |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in program_rows:
        lines.append(
            "| {program} | {lookup} | {status} | {path} | {tier} | {allowed} |".format(
                program=row.get("program") or "",
                lookup=row.get("central_lookup_result") or "",
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

Lookup Profile:

{render_lookup_profile(manifest)}

Source Inventory Cache:

{render_source_inventory(manifest)}

Sources:

{render_sources_table(programs)}

Core Completeness Ledger:

{render_completeness_table(programs)}

## Calculation Logic

<!-- Fill from manifest-listed compact artifacts only. Keep rows by Program and Routine. -->

| Program | Routine | Calculation / Assignment | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Validation Logic

<!-- Fill from manifest-listed compact artifacts only. Preserve exact statuses, return codes, and messages. -->

| Program | Routine | Message / Status / Outcome | Description | Trigger Chain | Carrier / Destination | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Exception Handling

<!-- Fill from manifest-listed compact artifacts only. Preserve local exception closure and program outcome. -->

| Program | Routine | Exception / Error Path | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Message Inventory

<!-- Include every exact message/status/literal observed across participating program analyses. -->

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Trigger / Handler | Effect | Detail Refs | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
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


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    programs = manifest.get("programs")
    if not isinstance(programs, list) or not programs:
        return ["manifest has no programs[] entries"]
    seen: set[str] = set()
    for entry in programs:
        name = str(entry.get("normalized_name") or "")
        if not name:
            findings.append("program entry missing normalized_name")
            continue
        if name in seen:
            findings.append(f"duplicate normalized program in manifest: {name}")
        seen.add(name)
        result = entry.get("central_lookup_result")
        if result not in {LOOKUP_FOUND, LOOKUP_NOT_FOUND, LOOKUP_REMOTE_UNAVAILABLE}:
            findings.append(f"{name} has invalid central_lookup_result: {result}")
        if result == LOOKUP_FOUND and not entry.get("artifact_root"):
            findings.append(f"{name} found_on_remote_main missing artifact_root")
        if result == LOOKUP_FOUND and entry.get("artifact_source") != "remote_main":
            findings.append(f"{name} found_on_remote_main must use artifact_source remote_main")
        if result == LOOKUP_NOT_FOUND and entry.get("artifact_root"):
            if entry.get("artifact_source") != "delivery_working_branch":
                findings.append(
                    f"{name} not_found_on_remote_main with artifact_root must use "
                    "artifact_source delivery_working_branch"
                )
    return findings


def validate_review(markdown: str, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    positions = h2_positions(markdown)
    missing_sections = [section for section in CORE_SECTIONS if section not in positions]
    if missing_sections:
        findings.append("program-set review missing required ## sections: " + ", ".join(missing_sections))
    else:
        ordered = [positions[section] for section in CORE_SECTIONS]
        if ordered != sorted(ordered):
            findings.append("program-set review core ## sections are out of order")
    for section in FORBIDDEN_FULL_FLOW_SECTIONS:
        if re.search(rf"^##\s+{re.escape(section)}\s*$", markdown, re.M):
            findings.append(f"program-set review contains forbidden full-flow section: {section}")
    if "Sources:" not in markdown:
        findings.append("program-set review missing Sources table")
    if "Core Completeness Ledger:" not in markdown:
            findings.append("program-set review missing Core Completeness Ledger")
    sources_block = text_between(markdown, "Sources:", "Core Completeness Ledger:")
    ledger_block = text_between(markdown, "Core Completeness Ledger:", "## Calculation Logic")
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
        result = str(entry.get("central_lookup_result") or "")
        if result and program in ledger_rows and result not in ledger_rows[program]:
            findings.append(f"{program} lookup result {result} missing from Core Completeness Ledger")
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
    if args.source_root is not None and not args.source_root.is_dir():
        raise SystemExit(f"source root not found or not a directory: {args.source_root}")
    manifest = build_manifest(
        review_name=args.review_name,
        programs=programs,
        delivery_root=args.delivery_root,
        config=config,
        working_branch=args.working_branch,
        working_root=args.working_root,
        source_root=args.source_root,
        inventory_dir=args.inventory_dir,
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
    build.add_argument("--delivery-root", type=Path, required=True)
    build.add_argument("--working-root", type=Path)
    build.add_argument("--source-root", type=Path)
    build.add_argument("--inventory-dir", type=Path)
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
