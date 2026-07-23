#!/usr/bin/env python3
"""Read-only compatibility inventory for an approved IBM i artifact repository.

This command deliberately does not repair or rewrite the approved repository. It
discovers program artifact folders through the delivery profile, reuses the
flow merger's readiness checks, and emits a deterministic report that can drive
an isolated, program-level repair queue.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_flow_builder() -> Any:
    """Load the canonical builder without depending on the caller's PYTHONPATH."""

    path = SCRIPT_DIR / "program_set_core_review.py"
    spec = importlib.util.spec_from_file_location(
        "legacy_ibmi_flow_program_set_core_review", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load flow readiness builder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


BUILDER = load_flow_builder()

REPORT_SCHEMA_VERSION = "0.1"
REPORT_FILENAME = "approved-artifact-requalification.yaml"
FORMAT_CODES = {
    "hash_lock_mismatch",
    "yaml_parse_error",
    "yaml_duplicate_key",
    "yaml_reserved_scalar",
    "yaml_quote_encoding_error",
    "malformed_yaml",
}
BLOCKED_CODES = {
    "missing_artifact_root",
    "ambiguous_artifact_root",
    "artifact_trust_failure",
    "path_escape",
    "invalid_program_name",
    "program_identity_mismatch",
    "requalification_execution_error",
}


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _git_revision(root: Path) -> dict[str, Any]:
    """Return read-only revision metadata without requiring a Git repository."""

    command = ["git", "-C", str(root), "rev-parse", "--show-toplevel"]
    top = subprocess.run(command, text=True, capture_output=True, check=False)
    if top.returncode != 0:
        return {
            "type": "filesystem",
            "root": str(root.resolve()),
            "head": None,
            "dirty": None,
        }
    git_root = Path(top.stdout.strip()).resolve()
    head = subprocess.run(
        ["git", "-C", str(git_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "-C", str(git_root), "status", "--porcelain", "--", str(root.resolve())],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "type": "git",
        "root": str(git_root),
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
    }


def _profile_patterns(lookup: dict[str, Any], key: str, default: list[str]) -> list[str]:
    value = lookup.get(key)
    if not isinstance(value, list) or not value:
        return list(default)
    return [str(item) for item in value if str(item).strip()]


def _has_configured_artifact(candidate: Path, patterns: list[str]) -> bool:
    for configured in patterns:
        pattern = configured.replace("{PROGRAM}", candidate.name)
        try:
            matches = candidate.glob(pattern)
        except ValueError:
            continue
        if any(path.is_file() for path in matches):
            return True
    return False


def discover_candidates(
    root: Path,
    lookup: dict[str, Any],
) -> list[dict[str, Any]]:
    """Discover only profile-shaped program folders under the approved root."""

    root = root.resolve()
    folder_patterns = _profile_patterns(
        lookup, "program_folder_patterns", ["modules/*/{PROGRAM}"]
    )
    module_patterns = _profile_patterns(lookup, "module_roots", [])
    artifact_patterns = _profile_patterns(
        lookup, "artifact_file_patterns", ["program-analysis.md"]
    )
    allowed_module_roots: list[Path] = []
    for pattern in module_patterns:
        try:
            allowed_module_roots.extend(
                path.resolve() for path in root.glob(pattern) if path.is_dir()
            )
        except ValueError:
            continue

    candidates: dict[str, dict[str, Any]] = {}
    for configured in folder_patterns:
        if "{PROGRAM}" not in configured:
            continue
        discovery_pattern = configured.replace("{PROGRAM}", "*")
        try:
            matches = root.glob(discovery_pattern)
        except ValueError:
            continue
        for path in matches:
            resolved = path.resolve()
            if not path.is_dir() or not _inside(root, resolved):
                continue
            if any(part.startswith(".") for part in resolved.relative_to(root).parts):
                continue
            if allowed_module_roots and not any(
                resolved.parent == module_root or _inside(module_root, resolved)
                for module_root in allowed_module_roots
            ):
                continue
            if not _has_configured_artifact(path, artifact_patterns):
                continue
            key = str(resolved)
            candidates.setdefault(
                key,
                {
                    "path": path,
                    "artifact_root": _relative(root, path),
                    "raw_program": path.name,
                    "matched_patterns": [],
                },
            )
            candidates[key]["matched_patterns"].append(configured)
    return sorted(
        candidates.values(),
        key=lambda item: (str(item["raw_program"]).upper(), str(item["artifact_root"])),
    )


def _yaml_preflight(candidate: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(candidate.glob("*.yaml")) + sorted(candidate.glob("*.yml")):
        try:
            BUILDER.load_yaml(path)
        except Exception as exc:  # noqa: BLE001 - report every malformed artifact
            detail = str(exc).strip().replace("\n", " ")
            findings.append(f"YAML parse error in {path.name}: {detail}")
    return findings


def finding_code(finding: str) -> str:
    lowered = str(finding or "").lower()
    if "yaml parse error" in lowered:
        if "duplicate" in lowered:
            return "yaml_duplicate_key"
        if "@" in lowered or "reserved" in lowered or "scannererror" in lowered:
            return "yaml_reserved_scalar"
        if "&lt;" in lowered or "&#" in lowered or "html" in lowered:
            return "yaml_quote_encoding_error"
        return "yaml_parse_error"
    if any(marker in lowered for marker in ("sha256", "hash mismatch", "digest mismatch")):
        return "hash_lock_mismatch"
    if "program analysis artifact directory is missing" in lowered:
        return "missing_artifact_root"
    if "ambiguous program analysis artifact" in lowered:
        return "ambiguous_artifact_root"
    if any(marker in lowered for marker in ("path escapes", "symlink", "junction", "reparse")):
        return "artifact_trust_failure"
    if "invalid normalized program name" in lowered:
        return "invalid_program_name"
    if "program identity mismatch" in lowered or "identity is missing" in lowered:
        return "program_identity_mismatch"
    if "core reader-first section is missing" in lowered:
        return "missing_reader_first_section"
    if "placeholder" in lowered or "too thin" in lowered:
        return "placeholder_reader_first_section"
    if "missing core artifact" in lowered:
        return "missing_core_artifact"
    if "pending non-core artifacts" in lowered:
        return "missing_non_core_artifact"
    if any(marker in lowered for marker in ("deep read", "deep_read", "routine")):
        return "pending_deep_read"
    if any(marker in lowered for marker in ("message", "rlog")):
        return "message_or_rlog_evidence_pending"
    if "terminal status" in lowered or "non-terminal" in lowered:
        return "non_terminal_status"
    if "required sections" in lowered or "validator" in lowered:
        return "upstream_contract_failure"
    return "upstream_contract_failure"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value).strip()))


def classify_status(
    *,
    readiness_status: str,
    findings: list[str],
    codes: list[str],
    preflight_failed: bool,
) -> str:
    if not findings:
        return "final_ready"
    if any(code in BLOCKED_CODES for code in codes):
        return "blocked"
    if preflight_failed or (codes and set(codes).issubset(FORMAT_CODES)):
        return "format_repairable"
    if readiness_status == "ready":
        return "core_reader_ready_pending"
    return "semantic_repair_required"


def repair_actions(status: str, codes: list[str]) -> list[str]:
    actions: list[str] = []
    code_set = set(codes)
    if status == "format_repairable":
        actions.append("Apply a syntax-only deterministic YAML repair and preserve exact scalar values.")
        if "hash_lock_mismatch" in code_set:
            actions.append("Regenerate source-index, deep-read plan, and batch locks atomically; never edit a hash by hand.")
    if status in {"semantic_repair_required", "core_reader_ready_pending"}:
        actions.append("Run a targeted legacy-ibmi-program-analyzer repair for this program only.")
    if "missing_reader_first_section" in code_set or "placeholder_reader_first_section" in code_set:
        actions.append("Complete the source-backed Program Reading Summary and reader-first sections.")
    if "pending_deep_read" in code_set:
        actions.append("Resume or complete retained routine deep-read batches and update their terminal coverage.")
    if "message_or_rlog_evidence_pending" in code_set:
        actions.append("Resolve message/RLOG evidence from source or approved control inputs; do not invent meanings.")
    if "non_terminal_status" in code_set:
        actions.append("Obtain the terminal approved or approved_with_non_blocking_tbd status after validation.")
    if status == "blocked":
        actions.append("Resolve the artifact identity, trust, path, or ambiguity before any repair prompt is executed.")
    return _unique(actions)


def _sidecar_digests(root: Path, artifact_root: str, program: str) -> dict[str, str | None]:
    candidate = root / artifact_root
    source_candidates = list(BUILDER.program_artifact_candidates(program, "source-index.yaml"))
    source_path = next((candidate / name for name in source_candidates if (candidate / name).is_file()), None)
    plan_paths = sorted(candidate.glob("*-deep-read-execution-plan.yaml"))
    if not plan_paths:
        plan_paths = sorted(candidate.glob("deep-read-execution-plan.yaml"))
    return {
        "source_index_sha256": _sha256(source_path) if source_path else None,
        "execution_plan_sha256": _sha256(plan_paths[0]) if plan_paths else None,
    }


def requalify_program(
    *,
    root: Path,
    candidate: dict[str, Any],
    lookup: dict[str, Any],
    workspace: dict[str, Any],
) -> dict[str, Any]:
    path = Path(candidate["path"])
    raw_program = str(candidate["raw_program"])
    invalid_name: str | None = None
    try:
        program = BUILDER.normalize_program_name(raw_program, lookup)
    except ValueError as exc:
        program = raw_program
        invalid_name = str(exc)

    artifact_root = str(candidate["artifact_root"])
    tier = BUILDER.infer_tier(artifact_root, workspace)
    compact = BUILDER.collect_artifact_statuses(root, artifact_root, program)
    preflight_findings = _yaml_preflight(path)
    readiness: dict[str, Any]
    if invalid_name:
        readiness = {
            "status": "not_ready",
            "validator": "not_run",
            "validator_status": "not_run",
            "analysis_status": None,
            "findings": [f"invalid normalized program name: {invalid_name}"],
            "blocking_findings": [f"invalid normalized program name: {invalid_name}"],
            "pending_findings": [],
        }
    elif preflight_findings:
        readiness = {
            "status": "not_ready",
            "validator": "not_run",
            "validator_status": "not_run",
            "analysis_status": None,
            "findings": [],
            "blocking_findings": [],
            "pending_findings": [],
        }
    else:
        matches = [artifact_root]
        try:
            readiness = BUILDER.assess_artifact_readiness(
                root=root,
                program=program,
                candidate_artifact_root=artifact_root,
                matches=matches,
                compact_artifacts=compact,
                expected_size_tier=tier,
            )
        except Exception as exc:  # noqa: BLE001 - one bad legacy folder cannot abort inventory
            readiness = {
                "status": "not_ready",
                "validator": "runtime_error",
                "validator_status": "not_run",
                "analysis_status": None,
                "findings": [f"requalification execution error: {type(exc).__name__}: {exc}"],
                "blocking_findings": [],
                "pending_findings": [],
            }

    raw_findings = _unique(preflight_findings + list(readiness.get("findings") or []))
    codes = _unique([finding_code(item) for item in raw_findings])
    if invalid_name:
        codes.insert(0, "invalid_program_name")
        codes = _unique(codes)
    if readiness.get("validator") == "runtime_error":
        codes.append("requalification_execution_error")
        codes = _unique(codes)
    status = classify_status(
        readiness_status=str(readiness.get("status") or "not_ready"),
        findings=raw_findings,
        codes=codes,
        preflight_failed=bool(preflight_findings),
    )
    digests = _sidecar_digests(root, artifact_root, program)
    return {
        "program": program,
        "raw_folder_name": raw_program,
        "artifact_root": artifact_root,
        "tier": tier,
        "matched_folder_patterns": _unique(candidate.get("matched_patterns") or []),
        "status": status,
        "core_reader_first_compatible": readiness.get("status") == "ready" and not preflight_findings,
        "final_contract_compatible": status == "final_ready",
        "validator": readiness.get("validator"),
        "validator_status": readiness.get("validator_status"),
        "analysis_status": readiness.get("analysis_status"),
        "finding_codes": codes,
        "findings": raw_findings,
        "blocking_findings": _unique(list(readiness.get("blocking_findings") or []) + preflight_findings),
        "pending_findings": _unique(readiness.get("pending_findings") or []),
        "repair_actions": repair_actions(status, codes),
        "source_index_sha256": digests["source_index_sha256"],
        "execution_plan_sha256": digests["execution_plan_sha256"],
    }


def build_report(artifact_root: Path, profile_path: Path) -> dict[str, Any]:
    config = BUILDER.load_yaml(profile_path)
    if not isinstance(config, dict):
        raise ValueError(f"profile must contain a mapping: {profile_path}")
    lookup = BUILDER.profile_lookup(config)
    workspace = BUILDER.profile_workspace(config)
    root = artifact_root.resolve()
    candidates = discover_candidates(root, lookup)
    programs = [
        requalify_program(
            root=root,
            candidate=candidate,
            lookup=lookup,
            workspace=workspace,
        )
        for candidate in candidates
    ]
    programs.sort(key=lambda item: (str(item["program"]).upper(), str(item["artifact_root"])))
    by_program: dict[str, list[dict[str, Any]]] = {}
    for item in programs:
        by_program.setdefault(str(item["program"]).upper(), []).append(item)
    for normalized, matches in by_program.items():
        if len(matches) < 2:
            continue
        roots = ", ".join(str(item["artifact_root"]) for item in matches)
        for item in matches:
            item["status"] = "blocked"
            item["core_reader_first_compatible"] = False
            item["final_contract_compatible"] = False
            item["finding_codes"] = _unique(
                list(item.get("finding_codes") or []) + ["ambiguous_artifact_root"]
            )
            item["findings"] = _unique(
                list(item.get("findings") or [])
                + [f"ambiguous normalized program {normalized}: {roots}"]
            )
            item["repair_actions"] = repair_actions("blocked", item["finding_codes"])
    counts = {status: 0 for status in (
        "final_ready",
        "core_reader_ready_pending",
        "format_repairable",
        "semantic_repair_required",
        "blocked",
    )}
    for item in programs:
        counts[str(item["status"])] = counts.get(str(item["status"]), 0) + 1
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_by": "requalify_approved_program_artifacts.py",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "artifact_repo_mode": "approved_document_repo",
        "artifact_root": str(root),
        "profile": {
            "path": str(profile_path.resolve()),
            "sha256": _sha256(profile_path),
            "program_folder_patterns": lookup.get("program_folder_patterns", []),
            "module_roots": lookup.get("module_roots", []),
        },
        "repo_revision": _git_revision(root),
        "summary": {
            "total_candidates": len(programs),
            **counts,
            "repairable": counts["format_repairable"]
            + counts["semantic_repair_required"]
            + counts["core_reader_ready_pending"],
        },
        "programs": programs,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only requalification inventory for approved IBM i program artifacts."
    )
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument(
        "--profile",
        type=Path,
        default=SCRIPT_DIR.parent / "templates" / "delivery-profile.yaml",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report-name", default=REPORT_FILENAME)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    artifact_root = args.artifact_root.resolve()
    profile_path = args.profile.resolve()
    if not artifact_root.is_dir():
        raise SystemExit(f"artifact root does not exist or is not a directory: {artifact_root}")
    if not profile_path.is_file():
        raise SystemExit(f"profile does not exist: {profile_path}")
    report = build_report(artifact_root, profile_path)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / str(args.report_name)
    report_path.write_text(BUILDER.dump_yaml(report), encoding="utf-8")
    print(f"Requalified {report['summary']['total_candidates']} program artifact folders.")
    print(f"Report: {report_path}")
    for key, value in report["summary"].items():
        if key != "repairable":
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
