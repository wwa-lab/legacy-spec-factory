#!/usr/bin/env python3
"""Prepare and validate a controlled reader-first program-analysis merge.

The deterministic builder validates upstream program-analysis artifacts and
prepares an evidence bundle.  It never writes a synthetic SME review.  The
executing skill's LLM performs the cross-program synthesis, updates the
coverage ledger, and then invokes this module's reconciliation validator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from reader_first_merge_contract import (  # noqa: E402
    build_core_coverage as _build_core_coverage_v04,
    build_core_facts as _build_core_facts_v04,
    build_reader_first_source_pack as _build_reader_first_source_pack_v04,
    extract_source_pack_facts as _extract_source_pack_facts_v04,
)
from reader_first_markdown_contract import (  # noqa: E402
    is_markdown_table_separator as _is_markdown_table_separator_v04,
    split_markdown_table_row as _split_markdown_table_row_v04,
    structured_markdown_surface as _structured_markdown_surface_v04,
)
from review_safety_contract import (  # noqa: E402
    cross_program_relation_findings as _cross_program_relation_findings_v04,
    exact_literal_present as _exact_literal_present_v04,
    forbidden_heading_findings as _forbidden_heading_findings_v04,
    prohibited_decision_findings as _prohibited_decision_findings_v04,
    relation_supported_by_single_fact as _relation_supported_by_single_fact_v04,
    _visible_inline_text as _visible_inline_text_v04,
    _rendered_heading_label as _rendered_heading_label_v04,
    _strip_commonmark_container_prefix as _strip_container_prefix_v04,
)


CORE_READING_SECTIONS = (
    "Program Set Reading Summary",
    "Cross-Program Processing Overview",
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
)

OPTIONAL_READING_SECTIONS = ("Message Inventory",)

AUDIT_CONTROL_SECTIONS = (
    "Core Completeness Ledger",
    "Coverage Reconciliation",
    "Sources",
    "Run Profile",
    "Source Inventory Cache",
)

CORE_SECTIONS = (
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
)

READER_FIRST_SECTIONS = (
    *CORE_READING_SECTIONS,
    *OPTIONAL_READING_SECTIONS,
    *AUDIT_CONTROL_SECTIONS,
)

CORE_REVIEW_PROFILE_MINIMAL = "minimal_reader_first"
CORE_REVIEW_PROFILE_DEFAULT = "standard_reader_first"
CORE_REVIEW_PROFILE_STANDARD = "standard_reader_first"
CORE_REVIEW_PROFILES = {
    CORE_REVIEW_PROFILE_MINIMAL: {
        "name": CORE_REVIEW_PROFILE_MINIMAL,
        "core_sections": list(CORE_READING_SECTIONS),
        "include_message_inventory": False,
        "include_audit_sections": True,
    },
    CORE_REVIEW_PROFILE_STANDARD: {
        "name": CORE_REVIEW_PROFILE_STANDARD,
        "core_sections": [*CORE_READING_SECTIONS, "Message Inventory"],
        "include_message_inventory": True,
        "include_audit_sections": True,
    },
}

REVIEW_STATUS_COMPLETE = "ready_for_synthesis"
REVIEW_STATUS_PARTIAL = "blocked_artifact_readiness"
LEGACY_REVIEW_FILENAME = "program-set-sme-core-review.md"
CORE_FACTS_FILENAME = "program-set-core-facts.yaml"
SOURCE_PACK_FILENAME = "program-set-reader-first-source-pack.md"
CORE_COVERAGE_FILENAME = "program-set-core-coverage.yaml"
ARTIFACT_READINESS_FILENAME = "program-set-artifact-readiness.yaml"
PROGRAM_LIST_FILENAME = "program-list.txt"
PROGRAM_LIST_SOURCE_GENERATED = "generated_from_navigation_order"
MANIFEST_FILENAME = "program-set-core-input-manifest.yaml"
GENERATOR_VERSION = "0.4.0"
TEMPLATE_VERSION = "0.4.0"

FORBIDDEN_LEGACY_TERMS = (
    "Program-Level SME Core Review",
    "Program-Set Logic Rollup",
)

FORBIDDEN_FULL_FLOW_SECTIONS = (
    "Trigger Inventory",
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

# Readiness is intentionally narrower than the upstream *final delivery*
# contract.  Early source scans commonly have incomplete sidecars, routine
# deep-read checkpoints, or message descriptions.  Those are useful evidence
# and must remain visible as pending work, but they do not make the five
# reader-first sections unusable.  Only the primary Markdown and its five
# reader-first sections are hard readiness requirements here.
CORE_READINESS_ARTIFACTS = ("program-analysis.md",)
CORE_READINESS_SECTIONS = (
    "Program Reading Summary",
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
)
CORE_READINESS_PLACEHOLDER_RE = re.compile(
    r"\b(?:pending(?:\s+semantic)?(?:\s+deep[- ]read)?|placeholder(?:\s+content|\s+text)?|"
    r"to\s+be\s+completed|fill\s+in|reader[- ]first\s+explanation)\b",
    re.I,
)
CORE_READINESS_WORD_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_#$@/-]*|[\u4e00-\u9fff]{2,}"
)

CONDITIONAL_COMPACT_ARTIFACTS: tuple[str, ...] = ()

OPTIONAL_COMPACT_ARTIFACTS = (
    "file-io-inventory.yaml",
    "field-mutation-matrix.yaml",
    "sql-inventory.yaml",
)

ARTIFACT_SAFE_RE = re.compile(r'[\s<>:"/\\|?*]+')
PROGRAM_OBJECT_TOKEN_RE = re.compile(r"[A-Za-z@#$][A-Za-z0-9_@#$]{0,9}\Z")
PROGRAM_CSV_HEADERS = frozenset(
    {"member", "program", "program_name", "object_name", "name"}
)

RUN_ANALYZED = "analyzed_this_run"
RUN_REUSED = "reused_same_run"
RUN_ARTIFACT_REPO = "reused_artifact_repo"
RUN_PENDING = "pending_source"
RUN_BLOCKED = "blocked_missing_source"

ARTIFACT_REPO_CURRENT_RUN = "current_run"
ARTIFACT_REPO_APPROVED_DOCUMENT = "approved_document_repo"
DEFAULT_ARTIFACT_REPO_MODE = ARTIFACT_REPO_APPROVED_DOCUMENT

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
    candidate_artifact_root: str | None = None
    artifact_readiness: dict[str, Any] | None = None


@dataclass(frozen=True)
class OutputLayout:
    """Stable paths for one program-set review bundle.

    ``--output-dir`` is an output parent.  A caller may also pass the already
    resolved folder on a rerun; in that case the folder identity is not
    appended a second time.
    """

    folder_dir: Path
    program_list_path: Path
    manifest_path: Path
    readiness_path: Path
    source_pack_path: Path
    core_facts_path: Path
    coverage_path: Path
    review_path: Path
    queue_dir: Path


def _load_unique_yaml_text(text: str) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_unique_mapping(loader: Any, node: Any, deep: bool = False) -> Any:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"duplicate YAML mapping key: {key}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_unique_mapping,
    )
    return yaml.load(text, Loader=UniqueKeyLoader)


def load_yaml(path: Path) -> Any:
    return _load_unique_yaml_text(path.read_text(encoding="utf-8"))


def dump_yaml(data: Any) -> str:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "program_set_review"


def flow_identity_slug(value: str) -> str:
    """Preserve a readable flow label without collapsing distinct raw identities."""

    raw_identity = str(value)
    readable = slugify(raw_identity)[:64].rstrip("_") or "program_set_review"
    digest = hashlib.sha256(raw_identity.encode("utf-8")).hexdigest()[:8]
    return f"{readable}_{digest}"


def program_set_identity_slug(programs: list[str]) -> str:
    """Create a readable, stable slug that distinguishes program-set inputs."""
    identity_values = sorted(
        {str(program).strip().upper() for program in programs if str(program).strip()}
    )
    if not identity_values:
        return "program_set_review"
    readable = "_".join(slugify(program) for program in identity_values)
    readable = readable[:64].rstrip("_") or "programs"
    digest = hashlib.sha256("\n".join(identity_values).encode("utf-8")).hexdigest()[:8]
    return f"program_set_{readable}_{digest}"


def review_filename(folder_slug: str) -> str:
    return f"{folder_slug}--sme-core-review.md"


def resolve_output_layout(output_parent: Path, manifest: dict[str, Any]) -> OutputLayout:
    folder_slug = str(manifest.get("folder_slug") or "").strip()
    if not folder_slug:
        raise ValueError("manifest folder_slug must not be empty")
    parent = Path(output_parent)
    folder_dir = parent if parent.name == folder_slug else parent / folder_slug
    final_review_name = str(
        manifest.get("canonical_filename") or review_filename(folder_slug)
    )
    if final_review_name == LEGACY_REVIEW_FILENAME:
        final_review_name = review_filename(folder_slug)
    return OutputLayout(
        folder_dir=folder_dir,
        program_list_path=folder_dir / PROGRAM_LIST_FILENAME,
        manifest_path=folder_dir / MANIFEST_FILENAME,
        readiness_path=folder_dir / ARTIFACT_READINESS_FILENAME,
        source_pack_path=folder_dir / SOURCE_PACK_FILENAME,
        core_facts_path=folder_dir / CORE_FACTS_FILENAME,
        coverage_path=folder_dir / CORE_COVERAGE_FILENAME,
        review_path=folder_dir / final_review_name,
        queue_dir=folder_dir / "missing-program-list-batch",
    )


def read_programs_file(path: Path) -> list[str]:
    def is_comment(value: str) -> bool:
        return value.startswith(("# ", "#\t"))

    programs: list[str] = []
    if path.suffix.lower() == ".csv":
        first_record = True
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.reader(handle, strict=True):
                value = (row[0] if row else "").strip()
                if not value or is_comment(value):
                    continue
                header = value.lower().replace("-", "_").replace(" ", "_")
                if first_record and header in PROGRAM_CSV_HEADERS:
                    first_record = False
                    continue
                first_record = False
                programs.append(value)
        return programs

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        value = line.strip()
        if value and not is_comment(value):
            programs.append(value)
    return programs


def validate_normalized_program_name(program: str, *, original: str | None = None) -> str:
    if not PROGRAM_OBJECT_TOKEN_RE.fullmatch(program):
        source = f" (from {original!r})" if original is not None else ""
        raise ValueError(
            f"invalid normalized program name {program!r}{source}; expected one safe "
            "1-10 character IBM i object token starting with A-Z, a-z, @, #, or $, followed "
            "only by letters, digits, underscore, @, #, or $"
        )
    return program


def normalize_program_name(program: str, profile: dict[str, Any]) -> str:
    normalization = profile.get("program_name_normalization", {}) or {}
    normalized = program.strip()
    if normalization.get("case") == "upper":
        normalized = normalized.upper()
    return validate_normalized_program_name(normalized, original=program)


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


def resolve_core_review_profile(
    config: dict[str, Any], requested_name: str | None = None
) -> dict[str, Any]:
    configured = config.get("core_review_profiles", {}) or {}
    profiles = dict(CORE_REVIEW_PROFILES)
    if isinstance(configured, dict):
        for name, value in configured.items():
            if isinstance(value, dict):
                profiles[str(name)] = {**profiles.get(str(name), {}), **value}

    selected = (
        {"name": requested_name}
        if requested_name
        else config.get("core_review_profile", {}) or {}
    )
    if isinstance(selected, str):
        selected = {"name": selected}
    if not isinstance(selected, dict):
        selected = {}
    name = requested_name or selected.get("name") or CORE_REVIEW_PROFILE_DEFAULT
    name = str(name)
    profile = dict(profiles.get(name, profiles[CORE_REVIEW_PROFILE_DEFAULT]))
    profile.update({key: value for key, value in selected.items() if key != "name"})
    profile["name"] = name
    profile.setdefault("core_sections", list(CORE_READING_SECTIONS))
    profile.setdefault("include_message_inventory", name == CORE_REVIEW_PROFILE_STANDARD)
    profile.setdefault("include_audit_sections", True)
    profile["core_sections"] = [str(section) for section in profile["core_sections"]]
    return profile


def required_review_sections(profile: dict[str, Any]) -> tuple[str, ...]:
    sections = tuple(str(section) for section in profile.get("core_sections", []))
    if profile.get("include_message_inventory") and "Message Inventory" not in sections:
        sections = (*sections, "Message Inventory")
    if profile.get("include_audit_sections", True):
        audit_sections = AUDIT_CONTROL_SECTIONS
        if not profile.get("include_message_inventory"):
            audit_sections = (
                "Core Completeness Ledger",
                "Coverage Reconciliation",
                "Message Coverage Control",
                "Sources",
                "Run Profile",
                "Source Inventory Cache",
            )
        sections = (*sections, *audit_sections)
    return sections


def review_status_for_programs(programs: list[dict[str, Any]]) -> str:
    if any(
        entry.get("run_resolution") in {RUN_PENDING, RUN_BLOCKED}
        or (entry.get("artifact_readiness") or {}).get("status") != "ready"
        or ((entry.get("compact_artifacts") or {}).get(artifact_key("program-analysis.md"), {}) or {}).get("status")
        != "present"
        for entry in programs
    ):
        return REVIEW_STATUS_PARTIAL
    return REVIEW_STATUS_COMPLETE


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
            else "Source worktree has uncommitted changes; provide a fresh externally prepared inventory before relying on cache."
        ),
    }


def artifact_key(filename: str) -> str:
    return filename.replace("-", "_").replace(".", "_")


def artifact_program_prefix(program: str | None) -> str | None:
    if not program:
        return None
    prefix = ARTIFACT_SAFE_RE.sub("_", str(program).strip().upper())
    prefix = prefix.strip("._-")
    return prefix or None


def program_artifact_filename(program: str | None, base_filename: str) -> str:
    prefix = artifact_program_prefix(program)
    return f"{prefix}-{base_filename}" if prefix else base_filename


def program_artifact_candidates(program: str | None, base_filename: str) -> tuple[str, ...]:
    prefixed = program_artifact_filename(program, base_filename)
    if prefixed == base_filename:
        return (base_filename,)
    return (prefixed, base_filename)


def collect_artifact_statuses(
    root: Path,
    artifact_root: str | None,
    program: str | None = None,
) -> dict[str, ArtifactStatus]:
    statuses: dict[str, ArtifactStatus] = {}
    root_path = root / artifact_root if artifact_root else None
    for filename in REQUIRED_COMPACT_ARTIFACTS + CONDITIONAL_COMPACT_ARTIFACTS + OPTIONAL_COMPACT_ARTIFACTS:
        key = artifact_key(filename)
        expected_filename = program_artifact_filename(program, filename)
        if root_path is None:
            statuses[key] = ArtifactStatus(path=expected_filename, status="missing")
            continue
        candidates = [
            root_path / candidate
            for candidate in program_artifact_candidates(program, filename)
        ]
        candidate = next((path for path in candidates if path.is_file()), candidates[0])
        statuses[key] = ArtifactStatus(
            path=relative_path(root, candidate),
            status="present" if candidate.is_file() else "missing",
        )
    return statuses


_UPSTREAM_VALIDATOR: Any | None = None


def upstream_program_validator() -> Any:
    """Load the canonical program-analyzer final validator by file path."""

    global _UPSTREAM_VALIDATOR
    if _UPSTREAM_VALIDATOR is not None:
        return _UPSTREAM_VALIDATOR
    validator_path = (
        Path(__file__).resolve().parents[2]
        / "legacy-ibmi-program-analyzer"
        / "scripts"
        / "validate_program_analysis_contract.py"
    )
    spec = importlib.util.spec_from_file_location(
        "legacy_ibmi_program_analysis_contract_validator", validator_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load upstream program validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    _UPSTREAM_VALIDATOR = module
    return module


def find_program_analysis_file(analysis_dir: Path, program: str) -> Path | None:
    for candidate in program_artifact_candidates(program, "program-analysis.md"):
        path = analysis_dir / candidate
        if path.is_file():
            return path
    matches = sorted(analysis_dir.glob("*-program-analysis.md"))
    return matches[0] if len(matches) == 1 else None


def _artifact_file(analysis_dir: Path, program: str, base_filename: str) -> Path | None:
    for candidate in program_artifact_candidates(program, base_filename):
        path = analysis_dir / candidate
        if path.is_file():
            return path
    return None


def program_artifact_identity_findings(
    analysis_dir: Path, program: str
) -> list[str]:
    """Reject a structurally valid artifact set that belongs to another program."""

    findings: list[str] = []
    expected = program.strip()
    analysis_path = find_program_analysis_file(analysis_dir, program)
    if analysis_path is None:
        return findings
    markdown = analysis_path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+Program Analysis:\s*(.+?)\s*$", markdown, re.M)
    if not title_match:
        findings.append("program identity is missing from the Program Analysis H1")
    else:
        title_program = re.sub(
            r"\s+\([^)]*\)\s*$", "", title_match.group(1).strip()
        ).strip(" `")
        if title_program != expected:
            findings.append(
                "program identity mismatch in Program Analysis H1: "
                f"expected {expected}, found {title_program or 'missing'}"
            )

    metadata_match = re.search(
        r"(?ms)^##\s+Metadata\s*$\s*(.*?)(?=^##\s+|\Z)", markdown
    )
    if metadata_match:
        metadata_program = re.search(
            r"^\|\s*Program\s*\|\s*([^|]+?)\s*\|\s*$",
            metadata_match.group(1),
            re.M,
        )
        if metadata_program:
            actual = metadata_program.group(1).strip(" `")
            if actual != expected:
                findings.append(
                    "program identity mismatch in Metadata: "
                    f"expected {expected}, found {actual or 'missing'}"
                )

    for base_filename in (
        "program-analysis-summary.yaml",
        "source-index.yaml",
        "routine-logic-details.yaml",
        "message-inventory.yaml",
    ):
        path = _artifact_file(analysis_dir, program, base_filename)
        if path is None:
            continue
        payload = load_yaml(path)
        if not isinstance(payload, dict) or not payload.get("program"):
            continue
        actual = str(payload["program"]).strip()
        if actual != expected:
            findings.append(
                f"program identity mismatch in {path.name}: "
                f"expected {expected}, found {actual}"
            )
    return findings


def terminal_analysis_status_evidence(
    analysis_dir: Path, program: str
) -> tuple[str | None, list[str]]:
    """Return the selected terminal state and any cross-artifact conflicts."""

    summary_status: str | None = None
    summary_path = _artifact_file(
        analysis_dir, program, "program-analysis-summary.yaml"
    )
    if summary_path is not None:
        payload = load_yaml(summary_path)
        if isinstance(payload, dict):
            for key in ("analysis_status", "review_status", "status"):
                value = payload.get(key)
                if value:
                    summary_status = str(value).strip().lower()
                    break

    markdown_statuses: list[str] = []
    analysis_path = find_program_analysis_file(analysis_dir, program)
    if analysis_path and analysis_path.is_file():
        markdown = analysis_path.read_text(encoding="utf-8")
        markdown_statuses.extend(
            match.group(1).strip().lower()
            for match in re.finditer(
                r"^\s*\*\*Status:\*\*\s*`?([A-Za-z0-9_-]+)`?\s*$",
                markdown,
                re.M,
            )
        )
        markdown_statuses.extend(
            match.group(1).strip().lower()
            for match in re.finditer(
                r"^\|\s*Analysis Status\s*\|\s*`?([A-Za-z0-9_-]+)`?\s*\|\s*$",
                markdown,
                re.M,
            )
        )
    distinct_markdown = list(dict.fromkeys(markdown_statuses))
    findings: list[str] = []
    if len(distinct_markdown) > 1:
        findings.append(
            "conflicting program analysis terminal statuses in Markdown: "
            + ", ".join(distinct_markdown)
        )
    markdown_status = distinct_markdown[0] if distinct_markdown else None
    if summary_status and markdown_status and summary_status != markdown_status:
        findings.append(
            "conflicting program analysis terminal statuses: "
            f"summary={summary_status}, markdown={markdown_status}"
        )
    return summary_status or markdown_status, findings


def terminal_analysis_status(analysis_dir: Path, program: str) -> str | None:
    """Read the explicit program-analysis terminal state from canonical outputs."""

    status, _findings = terminal_analysis_status_evidence(analysis_dir, program)
    return status


def _core_section_block(markdown: str, section: str) -> str:
    """Return one reader-first H2 block without requiring the full upstream layout."""

    matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M))
    for index, match in enumerate(matches):
        if match.group(1).strip() != section:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        return markdown[start:end]
    return ""


def core_reader_first_findings(analysis_path: Path | None) -> list[str]:
    """Validate only the information needed to make an early scan readable.

    This is deliberately independent from the upstream final-delivery gate.
    A section may contain unresolved rows, TBDs, or pending routine detail and
    still pass as long as it has a non-placeholder reader-facing explanation.
    """

    if analysis_path is None or not analysis_path.is_file():
        return ["missing core program-analysis.md reader-first artifact"]
    markdown = analysis_path.read_text(encoding="utf-8")
    findings: list[str] = []
    for section in CORE_READINESS_SECTIONS:
        block = _core_section_block(markdown, section)
        if not block:
            if section == "Message Inventory":
                findings.append(
                    "message inventory is absent; no observed messages recorded yet"
                )
                continue
            findings.append(f"core reader-first section is missing: {section}")
            continue
        surface = _structured_markdown_surface_v04(block)
        # Keep tables as evidence, but remove formatting noise before deciding
        # whether a section is genuinely empty or only a placeholder shell.
        visible_lines = []
        for raw in surface.splitlines():
            line = raw.strip()
            if not line or line.startswith("|") and (
                set(line.replace("|", "").replace("-", "").replace(":", "").strip())
                == set()
            ):
                continue
            if line.startswith("#"):
                continue
            visible_lines.append(line)
        visible = " ".join(visible_lines)
        words = CORE_READINESS_WORD_RE.findall(visible)
        if section == "Message Inventory" and not visible:
            findings.append(
                "message inventory is empty; no observed messages recorded yet"
            )
            continue
        if not visible or CORE_READINESS_PLACEHOLDER_RE.search(visible) and len(words) < 8:
            findings.append(
                f"core reader-first section is placeholder or not meaningful: {section}"
            )
            continue
        if len(words) < 4:
            findings.append(
                f"core reader-first section is too thin to be meaningful: {section}"
            )
    return findings


def classify_readiness_finding(finding: str) -> str:
    """Return ``blocking`` for core/safety failures, else ``pending``.

    The upstream program analyzer remains strict for final program delivery.
    The merger uses this small severity boundary so early scans can enter the
    reader-first bundle while retaining every non-core defect for follow-up.
    """

    text = str(finding or "")
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in (
            "artifact trust validation failed",
            "path escapes",
            "symlink",
            "junction",
            "reparse point",
            "ambiguous program analysis artifact",
            "artifact folder resolution is ambiguous",
            "program analysis artifact directory is missing",
            "analysis directory does not exist",
            "missing core program-analysis.md",
            "program identity mismatch in program analysis h1",
            "program identity is missing from the program analysis h1",
        )
    ):
        return "blocking"
    if "core reader-first section" in lowered:
        return "blocking"
    if "missing program-analysis.md or a single program-analysis-<obj-id>.md" in lowered:
        return "blocking"
    if "program-analysis.md missing required sections:" in lowered:
        missing = lowered.split("program-analysis.md missing required sections:", 1)[1]
        hard_core_sections = tuple(
            section for section in CORE_READINESS_SECTIONS if section != "Message Inventory"
        )
        if any(section.lower() in missing for section in hard_core_sections):
            return "blocking"
    # Everything else is retained as a pending repair item: sidecar drift,
    # status/terminal gaps, pending deep reads, message descriptions, RLOG
    # coverage, and non-core layout/quality findings.
    return "pending"


def assess_artifact_readiness(
    *,
    root: Path,
    program: str,
    candidate_artifact_root: str | None,
    matches: list[str],
    compact_artifacts: dict[str, ArtifactStatus],
    expected_size_tier: str | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Apply the early-scan core gate and retain non-core defects as pending.

    The upstream validator is still executed when possible, but its strict
    final-delivery findings are split into blocking core/safety findings and
    non-blocking pending findings.  This keeps an incomplete scan useful to the
    LLM/SME without allowing an empty or misidentified core artifact through.
    """

    findings: list[str] = []
    blocking_findings: list[str] = []
    pending_findings: list[str] = []
    if not candidate_artifact_root:
        blocking_findings.append("program analysis artifact directory is missing")
    if len(matches) > 1:
        blocking_findings.append(
            "ambiguous program analysis artifact directories: " + ", ".join(matches)
        )
    missing_required = [
        program_artifact_filename(program, filename)
        for filename in REQUIRED_COMPACT_ARTIFACTS
        if compact_artifacts.get(artifact_key(filename), ArtifactStatus("", "missing")).status
        != "present"
    ]
    missing_core = [
        filename for filename in missing_required if filename in CORE_READINESS_ARTIFACTS
    ]
    missing_non_core = [
        filename for filename in missing_required if filename not in CORE_READINESS_ARTIFACTS
    ]
    if missing_core:
        blocking_findings.append(
            "missing core artifacts: "
            + ", ".join(program_artifact_filename(program, filename) for filename in missing_core)
        )
    if missing_non_core:
        pending_findings.append(
            "pending non-core artifacts: "
            + ", ".join(program_artifact_filename(program, filename) for filename in missing_non_core)
        )

    analysis_dir = root / candidate_artifact_root if candidate_artifact_root else None
    upstream_findings: list[str] = []
    upstream_ran = False
    analysis_status: str | None = None
    analysis_path = (
        find_program_analysis_file(analysis_dir, program)
        if analysis_dir and analysis_dir.is_dir() and len(matches) <= 1
        else None
    )
    for core_finding in core_reader_first_findings(analysis_path):
        if classify_readiness_finding(core_finding) == "blocking":
            blocking_findings.append(core_finding)
        else:
            pending_findings.append(core_finding)

    if analysis_dir and analysis_dir.is_dir() and analysis_path is not None and len(matches) <= 1:
        upstream_ran = True
        upstream_findings = [
            str(item)
            for item in upstream_program_validator().validate(
                analysis_dir,
                expected_size_tier=expected_size_tier,
            )
        ]
        for item in upstream_findings:
            (blocking_findings if classify_readiness_finding(item) == "blocking" else pending_findings).append(item)
        for item in program_artifact_identity_findings(analysis_dir, program):
            (blocking_findings if classify_readiness_finding(item) == "blocking" else pending_findings).append(item)
        analysis_status, status_findings = terminal_analysis_status_evidence(
            analysis_dir, program
        )
        pending_findings.extend(status_findings)
        if analysis_status not in {"approved", "approved_with_non_blocking_tbd"}:
            pending_findings.append(
                "program analysis terminal status must be approved or "
                f"approved_with_non_blocking_tbd; found {analysis_status or 'missing'}"
            )

    findings.extend(blocking_findings)
    findings.extend(pending_findings)
    if strict:
        # Final formal-review validation reuses the same resolver but restores
        # the upstream contract's fail-closed behavior.  Early preparation is
        # lenient; final handoff is not.
        blocking_findings = list(findings)
        pending_findings = list(findings)
    pending_findings = list(dict.fromkeys(pending_findings))
    blocking_findings = list(dict.fromkeys(blocking_findings))
    findings = list(dict.fromkeys(findings))

    return {
        "status": "ready" if not blocking_findings else "not_ready",
        "validator": "legacy-ibmi-program-analyzer/validate_program_analysis_contract.py",
        "validator_status": (
            "not_run"
            if not upstream_ran
            else "failed"
            if any(item in blocking_findings for item in upstream_findings)
            else "passed_with_pending"
            if pending_findings
            else "passed"
        ),
        "analysis_status": analysis_status,
        "candidate_artifact_root": candidate_artifact_root,
        "findings": findings,
        "blocking_findings": blocking_findings,
        "pending_findings": pending_findings,
        "readiness_policy": "core_reader_first_lenient",
    }


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
    validate_normalized_program_name(program)
    patterns = lookup.get("program_folder_patterns") or ["modules/*/{PROGRAM}"]
    resolved_root = root.resolve()
    matches: list[Path] = []
    for pattern in patterns:
        resolved_pattern = str(pattern).replace("{PROGRAM}", program)
        for path in root.glob(resolved_pattern):
            resolved_path = path.resolve()
            try:
                resolved_path.relative_to(resolved_root)
            except ValueError:
                continue
            if resolved_path.is_dir():
                matches.append(path)
    relative_matches = sorted({relative_path(root, path) for path in matches})
    return (relative_matches[0] if relative_matches else None, relative_matches)


def build_program_entries(
    programs: list[str],
    artifact_root: Path,
    config: dict[str, Any],
    artifact_repo_mode: str = DEFAULT_ARTIFACT_REPO_MODE,
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
            is_ready = (
                first.artifact_root is not None
                and (first.artifact_readiness or {}).get("status") == "ready"
            )
            warnings.append(
                f"Duplicate normalized program name {normalized!r}; "
                + (
                    f"reusing artifact from order {first.order}"
                    if is_ready
                    else f"will resolve once from order {first.order} before reuse"
                )
            )
            entry = ProgramEntry(
                input_name=program,
                normalized_name=normalized,
                order=index,
                run_resolution=duplicate_resolution if is_ready else RUN_PENDING,
                artifact_root=first.artifact_root,
                artifact_source=first.artifact_source if is_ready else "source_scan_required",
                tier=first.tier,
                compact_artifacts=first.compact_artifacts,
                follow_up=duplicate_follow_up if is_ready else first.follow_up,
                candidate_artifact_root=first.candidate_artifact_root,
                artifact_readiness=first.artifact_readiness,
            )
            entries.append(entry)
            continue

        found_artifact_root, matches = find_program_artifact_root(artifact_root, normalized, lookup)
        if len(matches) > 1:
            warnings.append(
                f"Program {normalized} matched multiple artifact folders and is blocked: "
                + ", ".join(matches)
            )
        compact_artifacts = collect_artifact_statuses(
            artifact_root,
            found_artifact_root,
            normalized,
        )
        detected_tier = infer_tier(found_artifact_root, workspace)
        readiness = assess_artifact_readiness(
            root=artifact_root,
            program=normalized,
            candidate_artifact_root=found_artifact_root,
            matches=matches,
            compact_artifacts=compact_artifacts,
            expected_size_tier=detected_tier,
        )
        if readiness["status"] == "ready":
            run_resolution = present_resolution
            source = present_source
            pending = readiness.get("pending_findings") or []
            follow_up = (
                present_follow_up
                if not pending
                else "core reader-first gate passed; carry non-core readiness items as pending: "
                + "; ".join(str(item) for item in pending)
            )
            resolved_artifact_root = found_artifact_root if len(matches) == 1 else None
        elif found_artifact_root:
            run_resolution = RUN_PENDING
            source = "source_scan_required"
            follow_up = "refresh program analysis until readiness passes: " + "; ".join(
                str(item) for item in readiness["findings"]
            )
            # Keep the candidate directory available for the scan-result merge
            # path.  It is not trusted for formal SME handoff while readiness
            # is pending, but its existing scan output is still useful input
            # for an explicitly labelled exploratory draft.
            resolved_artifact_root = found_artifact_root
        else:
            run_resolution = RUN_PENDING
            source = "source_scan_required"
            follow_up = missing_follow_up
            resolved_artifact_root = None
        entry = ProgramEntry(
            input_name=program,
            normalized_name=normalized,
            order=index,
            run_resolution=run_resolution,
            artifact_root=resolved_artifact_root,
            artifact_source=source,
            tier=detected_tier,
            compact_artifacts=compact_artifacts,
            follow_up=follow_up,
            candidate_artifact_root=found_artifact_root,
            artifact_readiness=readiness,
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
    blocked_action = "provide_fresh_inventory_or_exact_source_mapping"
    if not files_present:
        return "missing", blocked_action
    if source_root is None:
        return "unchecked_no_source_root", "provide_source_root_to_compare_revision"
    if not current_revision:
        return "unknown_current_revision", blocked_action
    if current_revision.get("type") != "git":
        return "unknown_revision", blocked_action
    if current_revision.get("dirty") is not False:
        return "dirty_source", blocked_action
    if not inventory_revision.get("key"):
        return "unknown_inventory_revision", blocked_action
    if inventory_revision.get("type") == "git" and inventory_revision.get("dirty") is not False:
        return "dirty_inventory_source", blocked_action
    if inventory_revision.get("key") == current_revision.get("key"):
        return "fresh", "reuse_inventory"
    return "stale", blocked_action


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
        "candidate_artifact_root": entry.candidate_artifact_root,
        "artifact_source": entry.artifact_source,
        "tier": entry.tier,
        "compact_artifacts": {
            key: {"path": status.path, "status": status.status}
            for key, status in entry.compact_artifacts.items()
        },
        "artifact_readiness": entry.artifact_readiness
        or {
            "status": "not_ready",
            "findings": ["artifact readiness was not evaluated"],
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
    artifact_repo_mode: str = DEFAULT_ARTIFACT_REPO_MODE,
    core_review_profile: str | None = None,
    review_id: str | None = None,
    flow_slug: str | None = None,
    program_set_slug: str | None = None,
    programs_file: Path | None = None,
) -> dict[str, Any]:
    lookup = profile_lookup(config)
    workspace = profile_workspace(config)
    review_slug = slugify(review_name)
    flow_identity = flow_slug if flow_slug else review_name
    resolved_flow_slug = flow_identity_slug(flow_identity)
    resolved_profile = resolve_core_review_profile(config, core_review_profile)
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
    normalized_programs = [entry.normalized_name for entry in entries]
    identity_slug = program_set_identity_slug(normalized_programs)
    if program_set_slug:
        identity_digest = identity_slug.rsplit("_", 1)[-1]
        resolved_program_set_slug = f"{slugify(program_set_slug)}_{identity_digest}"
    else:
        resolved_program_set_slug = identity_slug
    entry_dicts = [entry_to_dict(entry) for entry in entries]
    review_status = review_status_for_programs(entry_dicts)
    artifact_readiness = (
        "ready" if review_status == REVIEW_STATUS_COMPLETE else "not_ready"
    )
    merge_coverage = (
        "pending" if review_status == REVIEW_STATUS_COMPLETE else "blocked"
    )
    stable_review_id = review_id or f"review-{resolved_flow_slug}--{resolved_program_set_slug}"
    folder_slug = f"{resolved_flow_slug}--{resolved_program_set_slug}"
    run_profile: dict[str, Any] = {
        "repo": lookup.get("repo") or workspace.get("repo"),
        "working_branch": working_branch,
        "artifact_root": str(artifact_root.resolve()),
        "artifact_repo_mode": artifact_repo_mode,
        "program_first": program_first,
        "cross_run_reuse": artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT,
        "reuse_policy": (
            "approved_document_repo_clone"
            if artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT
            else "current_run_only"
        ),
    }
    if programs_file is not None:
        resolved_programs_file = programs_file.resolve()
        run_profile["program_list_source"] = {
            "path": str(resolved_programs_file),
            "sha256": hashlib.sha256(resolved_programs_file.read_bytes()).hexdigest(),
        }
    return {
        "schema_version": "0.4",
        "generated_by": "program_set_core_review.py",
        "generator_version": GENERATOR_VERSION,
        "template_version": TEMPLATE_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "review_id": stable_review_id,
        "document_id": stable_review_id,
        "review_name": review_name,
        "review_slug": review_slug,
        "flow_slug": resolved_flow_slug,
        "program_set_slug": resolved_program_set_slug,
        "folder_slug": folder_slug,
        "display_name": review_name,
        "canonical_filename": review_filename(folder_slug),
        "artifact_version": "0.4",
        "review_status": review_status,
        "artifact_readiness": artifact_readiness,
        "merge_coverage": merge_coverage,
        "core_review_profile": resolved_profile,
        "run_profile": run_profile,
        "program_resolution_profile": {
            "program_folder_patterns": lookup.get("program_folder_patterns", ["modules/*/{PROGRAM}"]),
            "program_name_normalization": lookup.get("program_name_normalization", {}),
        },
        "workspace_profile": {
            "program_set_review_parent": workspace.get("program_set_review_parent"),
            "program_tier_roots": workspace.get("program_tier_roots", {}),
            "write_to_main": workspace.get("write_to_main", False),
        },
        "readiness_policy": "core_reader_first_lenient",
        "source_inventory": source_inventory,
        "programs": entry_dicts,
        "warnings": warnings,
    }


def artifact_summary(entry: dict[str, Any]) -> str:
    compact = entry.get("compact_artifacts", {}) or {}
    program = entry.get("normalized_name")
    labels = []
    for filename in REQUIRED_COMPACT_ARTIFACTS:
        key = artifact_key(filename)
        status = (compact.get(key) or {}).get("status", "missing")
        labels.append(f"{program_artifact_filename(program, filename)}={status}")
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
        missing.append(program_artifact_filename(entry.get("normalized_name"), "routine-logic-details.md"))
    if yaml != "present":
        missing.append(program_artifact_filename(entry.get("normalized_name"), "routine-logic-details.yaml"))
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
    artifact_repo_mode = run_profile.get("artifact_repo_mode") or DEFAULT_ARTIFACT_REPO_MODE
    reuse_policy = run_profile.get("reuse_policy") or (
        "approved_document_repo_clone"
        if artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT
        else "current_run_only"
    )
    cross_run_reuse = run_profile.get(
        "cross_run_reuse", artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT
    )
    return "\n".join(
        [
            "| Field | Value |",
            "| --- | --- |",
            f"| Repo | {run_profile.get('repo') or ''} |",
            f"| Working Branch | {run_profile.get('working_branch') or ''} |",
            f"| Artifact Root | {run_profile.get('artifact_root') or ''} |",
            f"| Artifact Repo Mode | {artifact_repo_mode} |",
            f"| Reuse Policy | {reuse_policy} |",
            f"| Cross-Run Reuse | {str(cross_run_reuse).lower()} |",
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


def _fact_value(row: dict[str, str], *names: str) -> str:
    normalized = {key.strip().lower(): value.strip() for key, value in row.items()}
    for name in names:
        value = normalized.get(name.strip().lower())
        if value:
            return value
    return ""


def extract_markdown_table_records(block: str, required_headers: tuple[str, ...]) -> list[dict[str, str]]:
    """Extract only explicitly tabulated facts from an analyzer artifact."""
    raw_lines = block.splitlines()
    records: list[dict[str, str]] = []
    index = 0
    while index < len(raw_lines):
        line = raw_lines[index].strip()
        if not (line.startswith("|") and line.endswith("|")):
            index += 1
            continue
        headers = [cell.strip() for cell in _split_markdown_table_row_v04(line)]
        normalized_headers = {header.lower() for header in headers}
        if not all(header.lower() in normalized_headers for header in required_headers):
            index += 1
            continue
        if index + 1 >= len(raw_lines) or not is_table_separator(raw_lines[index + 1]):
            index += 1
            continue
        separator_cells = _split_markdown_table_row_v04(raw_lines[index + 1].strip())
        if len(separator_cells) != len(headers):
            index += 1
            continue
        index += 2
        while index < len(raw_lines):
            data_line = raw_lines[index].strip()
            if not (data_line.startswith("|") and data_line.endswith("|")):
                break
            if is_table_separator(data_line):
                index += 1
                continue
            cells = [
                cell.strip() for cell in _split_markdown_table_row_v04(data_line)
            ]
            if len(cells) > len(headers):
                index += 1
                continue
            if len(cells) < len(headers):
                cells.extend([""] * (len(headers) - len(cells)))
            records.append(dict(zip(headers, cells)))
            index += 1
    return records


def extract_first_markdown_table_records(
    block: str, header_options: tuple[tuple[str, ...], ...]
) -> list[dict[str, str]]:
    for headers in header_options:
        records = extract_markdown_table_records(block, headers)
        if records:
            return records
    return []


def fact_unresolved_reason(evidence_status: str, *values: str) -> str | None:
    if evidence_status and evidence_status.lower() in {"confirmed", "confirmed_from_code", "present"}:
        return None
    joined = " ".join(value for value in values if value).lower()
    if any(marker in joined for marker in ("unresolved", "pending", "missing", "tbd", "not available")):
        return "source artifact marks this fact unresolved or pending"
    return "evidence status is not source-confirmed"


def _fact_from_calculation(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    evidence_status = _fact_value(row, "Evidence Status", "Status") or "unresolved"
    return {
        "program": program,
        "routine": _fact_value(row, "Routine"),
        "calculation": _fact_value(row, "Calculation / Assignment", "Calculation", "Assignment"),
        "target_carrier": _fact_value(row, "Target Field / Carrier", "Target Field / Variable", "Target Field", "Target Carrier"),
        "source_carrier": _fact_value(row, "Source Operands / Carriers", "Source Carrier", "Source Operands"),
        "guard": _fact_value(row, "Guard / Branch", "Guard", "Branch"),
        "effect": _fact_value(row, "Effect", "Output / Business Effect"),
        "evidence_reference": _fact_value(row, "Supporting Detail", "Supporting Detail Link", "Evidence Reference", "Evidence", "Detail Refs") or source,
        "evidence_status": evidence_status,
        "unresolved_reason": fact_unresolved_reason(evidence_status, *row.values()),
    }


def _fact_from_validation(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    evidence_status = _fact_value(row, "Evidence Status", "Status") or "unresolved"
    return {
        "program": program,
        "routine": _fact_value(row, "Routine"),
        "exact_code_status": _fact_value(row, "Message / Status / Outcome", "Exact Message / Status / Outcome", "Message / Status Code", "Message", "Status"),
        "trigger_chain": _fact_value(row, "Trigger Chain", "Trigger Condition", "Trigger"),
        "carrier_destination": _fact_value(row, "Carrier / Destination", "Output Carrier", "Carrier", "Destination"),
        "effect": _fact_value(row, "Effect", "Downstream Effect"),
        "evidence_reference": _fact_value(row, "Supporting Detail", "Supporting Detail Link", "Evidence Reference", "Evidence", "Detail Refs") or source,
        "evidence_status": evidence_status,
        "unresolved_reason": fact_unresolved_reason(evidence_status, *row.values()),
    }


def _fact_from_exception(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    evidence_status = _fact_value(row, "Evidence Status", "Status") or "unresolved"
    return {
        "program": program,
        "routine": _fact_value(row, "Routine"),
        "detection_mechanism": _fact_value(row, "Detection Mechanism", "Detection"),
        "fields_messages_set": _fact_value(row, "Fields / Messages Set", "Fields / Messages", "Messages Set"),
        "exception_action": _fact_value(row, "Handling Action", "Action"),
        "flow_level_effect": _fact_value(row, "Flow-Level Effect", "Downstream Effect", "Effect"),
        "evidence_reference": _fact_value(row, "Supporting Detail", "Supporting Detail Link", "Evidence Reference", "Evidence", "Detail Refs") or source,
        "evidence_status": evidence_status,
        "unresolved_reason": fact_unresolved_reason(evidence_status, *row.values()),
    }


def _fact_from_message(program: str, row: dict[str, str], source: str) -> dict[str, Any]:
    evidence_status = _fact_value(row, "Evidence Status", "Status") or "unresolved"
    return {
        "program": program,
        "routine": _fact_value(row, "Routine", "Program / Routine Sources", "Program / Routine"),
        "exact_message_status_literal": _fact_value(row, "Message / Status / Literal", "Message", "Status", "Literal"),
        "description": _fact_value(row, "Description"),
        "trigger_handler": _fact_value(row, "Trigger / Handler", "Trigger", "Handler"),
        "effect": _fact_value(row, "Effect"),
        "evidence_reference": _fact_value(row, "Detail Refs", "Evidence Reference", "Supporting Detail") or source,
        "evidence_status": evidence_status,
        "unresolved_reason": fact_unresolved_reason(evidence_status, *row.values()),
    }


def _build_core_facts_legacy(manifest: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    """Build a bounded intermediate from explicit compact-artifact evidence.

    This deliberately reads rows that already exist in program-analysis
    artifacts. It never creates business rules, modernization decisions, or
    cross-program call edges from program order.
    """
    programs: list[dict[str, Any]] = []
    for entry in manifest.get("programs", []) or []:
        program = str(entry.get("normalized_name") or "")
        artifact_relative = entry.get("artifact_root")
        artifact_dir = artifact_root / str(artifact_relative) if artifact_relative else None
        source_status = (
            "complete"
            if entry.get("run_resolution") in {RUN_ANALYZED, RUN_REUSED, RUN_ARTIFACT_REPO}
            else "pending"
        )
        program_facts: dict[str, list[dict[str, Any]]] = {
            "calculations": [],
            "validations": [],
            "exceptions": [],
            "messages": [],
        }
        source_files: list[str] = []
        if artifact_dir and artifact_dir.is_dir():
            analysis_name = program_artifact_filename(program, "program-analysis.md")
            analysis_path = next(
                (
                    artifact_dir / candidate
                    for candidate in program_artifact_candidates(program, "program-analysis.md")
                    if (artifact_dir / candidate).is_file()
                ),
                artifact_dir / analysis_name,
            )
            if analysis_path.is_file():
                source_files.append(relative_path(artifact_root, analysis_path))
                markdown = analysis_path.read_text(encoding="utf-8")
                program_facts["calculations"] = [
                    _fact_from_calculation(program, row, relative_path(artifact_root, analysis_path))
                    for row in extract_first_markdown_table_records(
                        h2_section_block(markdown, "Calculation Logic"),
                        (
                            ("Routine", "Target Field / Carrier", "Effect"),
                            ("Target Field / Variable", "Output / Business Effect", "Evidence"),
                        ),
                    )
                ]
                program_facts["validations"] = [
                    _fact_from_validation(program, row, relative_path(artifact_root, analysis_path))
                    for row in extract_first_markdown_table_records(
                        h2_section_block(markdown, "Validation Logic"),
                        (
                            ("Routine", "Trigger Chain", "Effect"),
                            ("Message / Status Code", "Trigger Condition", "Output Carrier", "Downstream Effect", "Evidence Status"),
                        ),
                    )
                ]
                program_facts["exceptions"] = [
                    _fact_from_exception(program, row, relative_path(artifact_root, analysis_path))
                    for row in extract_first_markdown_table_records(
                        h2_section_block(markdown, "Exception Handling"),
                        (
                            ("Routine", "Handling Action", "Effect"),
                            ("Exception / Error Path", "Detection Mechanism", "Handling Action", "Downstream Effect", "Evidence"),
                        ),
                    )
                ]
                program_facts["messages"] = [
                    _fact_from_message(program, row, relative_path(artifact_root, analysis_path))
                    for row in extract_markdown_table_records(
                        h2_section_block(markdown, "Message Inventory"),
                        ("Message / Status / Literal", "Description", "Effect"),
                    )
                ]
        unresolved_reason = None
        if source_status != "complete":
            unresolved_reason = "program-analysis compact artifacts are unavailable for this manifest program"
        elif not source_files:
            unresolved_reason = "required program-analysis.md artifact was not found"
        programs.append(
            {
                "program": program,
                "run_resolution": entry.get("run_resolution"),
                "source_status": source_status,
                "source_files": source_files,
                "facts": program_facts,
                "unresolved_reason": unresolved_reason,
            }
        )

    return {
        "schema_version": "0.1",
        "generated_by": "program_set_core_review.py",
        "generator_version": GENERATOR_VERSION,
        "review_id": manifest.get("review_id"),
        "review_status": manifest.get("review_status"),
        "review_profile": manifest.get("core_review_profile"),
        "flow_slug": manifest.get("flow_slug"),
        "program_set_slug": manifest.get("program_set_slug"),
        "folder_slug": manifest.get("folder_slug"),
        "programs": programs,
        "evidence_boundary": (
            "Facts are copied only from explicit rows in program-analysis.md; "
            "program order is not a source-confirmed call edge."
        ),
    }


def build_reader_first_source_pack(manifest: dict[str, Any], artifact_root: Path) -> str:
    return _build_reader_first_source_pack_v04(manifest, artifact_root)


def build_core_facts(manifest: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    return _build_core_facts_v04(manifest, artifact_root)


def build_core_coverage(
    core_facts: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    return _build_core_coverage_v04(core_facts, manifest)


def assert_output_identity_compatible(
    manifest_path: Path, manifest: dict[str, Any]
) -> None:
    """Refuse to overwrite a bundle that belongs to another review identity."""
    if not manifest_path.is_file():
        return
    existing = load_yaml(manifest_path)
    if not isinstance(existing, dict):
        raise ValueError(
            f"existing bundle manifest is not a YAML mapping: {manifest_path}"
        )

    def identity(payload: dict[str, Any]) -> dict[str, Any]:
        programs = sorted(
            {
                str(entry.get("normalized_name") or "")
                for entry in payload.get("programs", []) or []
                if isinstance(entry, dict) and entry.get("normalized_name")
            }
        )
        return {
            "document_id": payload.get("document_id") or payload.get("review_id"),
            "flow_slug": payload.get("flow_slug"),
            "program_set_slug": payload.get("program_set_slug"),
            "canonical_filename": payload.get("canonical_filename"),
            "programs": programs,
        }

    existing_identity = identity(existing)
    requested_identity = identity(manifest)
    if existing_identity != requested_identity:
        raise ValueError(
            "existing bundle manifest identity does not match the requested "
            f"flow/program set: existing={existing_identity!r}, "
            f"requested={requested_identity!r}"
        )


def write_build_outputs(manifest: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    layout = resolve_output_layout(output_dir, manifest)
    assert_output_identity_compatible(layout.manifest_path, manifest)
    if layout.review_path.is_file():
        raise ValueError(
            "existing formal review must be explicitly archived before rebuilding "
            f"the preparation bundle: {layout.review_path}"
        )
    layout.folder_dir.mkdir(parents=True, exist_ok=True)
    program_list_text = (
        "\n".join(
            str(entry.get("input_name") or entry.get("normalized_name") or "")
            for entry in manifest.get("programs", []) or []
        ).rstrip()
        + "\n"
    )
    layout.program_list_path.write_text(program_list_text, encoding="utf-8")
    output_manifest = dict(manifest)
    output_run_profile = dict(manifest.get("run_profile") or {})
    if "program_list_source" not in output_run_profile:
        output_run_profile["program_list_source"] = {
            "kind": PROGRAM_LIST_SOURCE_GENERATED,
            "sha256": hashlib.sha256(
                program_list_text.encode("utf-8")
            ).hexdigest(),
        }
    output_manifest["run_profile"] = output_run_profile
    manifest = output_manifest
    layout.manifest_path.write_text(dump_yaml(manifest), encoding="utf-8")
    distinct_readiness_programs: list[dict[str, Any]] = []
    seen_readiness_programs: set[str] = set()
    for entry in manifest.get("programs", []) or []:
        program = str(entry.get("normalized_name") or "")
        if not program or program in seen_readiness_programs:
            continue
        seen_readiness_programs.add(program)
        distinct_readiness_programs.append(
            {
                "program": program,
                "run_resolution": entry.get("run_resolution"),
                "candidate_artifact_root": entry.get("candidate_artifact_root"),
                "artifact_root": entry.get("artifact_root"),
                "artifact_readiness": entry.get("artifact_readiness"),
            }
        )
    readiness = {
        "schema_version": "0.4",
        "document_id": manifest.get("document_id") or manifest.get("review_id"),
        "overall_status": (
            "ready"
            if manifest.get("review_status") == REVIEW_STATUS_COMPLETE
            else "not_ready"
        ),
        "programs": distinct_readiness_programs,
    }
    layout.readiness_path.write_text(dump_yaml(readiness), encoding="utf-8")

    has_candidate_scan_results = any(
        str(entry.get("artifact_root") or "").strip()
        for entry in manifest.get("programs", []) or []
    )
    if manifest.get("review_status") == REVIEW_STATUS_COMPLETE or has_candidate_scan_results:
        artifact_root = Path(str(manifest["run_profile"]["artifact_root"]))
        source_pack = build_reader_first_source_pack(manifest, artifact_root)
        facts = build_core_facts(manifest, artifact_root)
        coverage = build_core_coverage(facts, manifest)
        layout.source_pack_path.write_text(source_pack, encoding="utf-8")
        layout.core_facts_path.write_text(dump_yaml(facts), encoding="utf-8")
        layout.coverage_path.write_text(dump_yaml(coverage), encoding="utf-8")
    else:
        for stale_ready_artifact in (
            layout.source_pack_path,
            layout.core_facts_path,
        ):
            if stale_ready_artifact.is_file() or stale_ready_artifact.is_symlink():
                stale_ready_artifact.unlink()
        blocked_coverage = {
            "schema_version": "0.4",
            "document_id": manifest.get("document_id") or manifest.get("review_id"),
            "review_status": REVIEW_STATUS_PARTIAL,
            "coverage_status": "blocked_artifact_readiness",
            "coverage_counts": {
                "total_source_facts": 0,
                "accounted_source_facts": 0,
                "pending_source_facts": 0,
                "by_program": {},
                "by_section": {},
                "routine_rlog": {},
            },
            "coverage_items": [],
            "items": [],
        }
        layout.coverage_path.write_text(dump_yaml(blocked_coverage), encoding="utf-8")
    return layout.manifest_path, layout.review_path


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
        cells = [cell.strip() for cell in _split_markdown_table_row_v04(stripped)]
        if not cells or not cells[0] or cells[0] == "Program":
            continue
        if set(cells[0]) <= {"-"}:
            continue
        rows[cells[0]] = cells
    return rows


def strip_markdown_comments(block: str) -> str:
    """Remove content that Markdown/HTML renderers do not expose to an SME."""
    return _structured_markdown_surface_v04(block)


def is_table_separator(line: str) -> bool:
    return _is_markdown_table_separator_v04(line)


def table_lines(block: str) -> list[tuple[int, list[str]]]:
    lines: list[tuple[int, list[str]]] = []
    for index, line in enumerate(block.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in _split_markdown_table_row_v04(stripped)]
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
    r"^\s*(?:todo|tbd|placeholder|n/a)\s*[.!]?\s*$|"
    r"\b(?:placeholder\s+(?:content|text|artifact\s+list)|fill\s+in|"
    r"to\s+be\s+completed|artifact\s+list|reader-first explanation|"
    r"programs and main routines)\b|"
    r"^\s*(?:todo|tbd|placeholder)\s*[:\-]\s*"
    r"(?:add|complete|describe|document|explain|fill|replace|write)\b.*$",
    re.I | re.M,
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
            cells = [cell.strip() for cell in _split_markdown_table_row_v04(stripped)]
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
    if lowered in {"todo", "tbd", "placeholder", "n/a"}:
        return True
    return any(
        marker in lowered
        for marker in (
            "placeholder content",
            "placeholder text",
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
    profile = resolve_core_review_profile(
        manifest if isinstance(manifest, dict) else {},
        str((manifest.get("core_review_profile") or {}).get("name"))
        if isinstance(manifest.get("core_review_profile"), dict)
        else None,
    )
    folder_slug = str(manifest.get("folder_slug") or "")
    expected_filename = review_filename(folder_slug) if folder_slug else ""
    if not folder_slug:
        findings.append("manifest folder_slug must not be empty")
    if manifest.get("canonical_filename") != expected_filename:
        findings.append(
            f"manifest canonical_filename must be the unique review name {expected_filename}"
        )
    if str(manifest.get("document_id") or "") != str(manifest.get("review_id") or ""):
        findings.append("manifest document_id must match review_id")
    expected_folder_slug = (
        f"{manifest.get('flow_slug')}--{manifest.get('program_set_slug')}"
        if manifest.get("flow_slug") and manifest.get("program_set_slug")
        else ""
    )
    if expected_folder_slug and folder_slug != expected_folder_slug:
        findings.append(
            "manifest folder_slug must match flow_slug--program_set_slug identity"
        )
    review_status = manifest.get("review_status")
    if review_status not in {
        None,
        REVIEW_STATUS_COMPLETE,
        REVIEW_STATUS_PARTIAL,
        "complete_exploratory",
        "standalone_exploratory",
        "draft",
        "chain_ready",
    }:
        findings.append(f"manifest has invalid review_status: {review_status}")
    schema_version = str(manifest.get("schema_version") or "")
    if schema_version == "0.4":
        for key, expected in (
            ("generator_version", GENERATOR_VERSION),
            ("template_version", TEMPLATE_VERSION),
            ("artifact_version", "0.4"),
        ):
            if str(manifest.get(key) or "") != expected:
                findings.append(
                    f"manifest {key} must be {expected} for schema_version 0.4"
                )
        artifact_readiness = manifest.get("artifact_readiness")
        merge_coverage = manifest.get("merge_coverage")
        if artifact_readiness not in {"ready", "not_ready"}:
            findings.append(
                "manifest artifact_readiness must be ready or not_ready"
            )
        if merge_coverage not in {"pending", "blocked", "complete"}:
            findings.append(
                "manifest merge_coverage must be pending, blocked, or complete"
            )
        expected_state = {
            REVIEW_STATUS_COMPLETE: ("ready", "pending"),
            REVIEW_STATUS_PARTIAL: ("not_ready", "blocked"),
            "complete_exploratory": ("ready", "complete"),
        }.get(str(review_status))
        if expected_state and (
            artifact_readiness,
            merge_coverage,
        ) != expected_state:
            findings.append(
                "manifest artifact_readiness/merge_coverage do not match "
                f"review_status {review_status}: expected "
                f"{expected_state[0]}/{expected_state[1]}"
            )
    for key in ("review_id", "review_slug", "flow_slug", "program_set_slug"):
        if manifest.get(key) is not None and not str(manifest.get(key)).strip():
            findings.append(f"manifest {key} must not be empty")
    if not isinstance(profile.get("core_sections"), list) or not profile.get("core_sections"):
        findings.append("manifest core_review_profile has no core_sections")
    run_profile = manifest.get("run_profile", {}) or {}
    artifact_repo_mode = run_profile.get("artifact_repo_mode") or DEFAULT_ARTIFACT_REPO_MODE
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in programs:
        name = str(entry.get("normalized_name") or "")
        if not name:
            findings.append("program entry missing normalized_name")
            continue
        by_name.setdefault(name, []).append(entry)
        if "run_resolution" not in entry and "central_lookup_result" in entry:
            findings.append(
                f"{name} uses legacy central_lookup_result; rebuild the manifest with an explicit artifact repo mode"
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
        if artifact_repo_mode == ARTIFACT_REPO_APPROVED_DOCUMENT and resolution in {
            RUN_ANALYZED,
            RUN_REUSED,
        }:
            findings.append(
                f"{name} {resolution} requires artifact_repo_mode {ARTIFACT_REPO_CURRENT_RUN}"
            )
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
                program_artifact_filename(name, filename)
                for filename in REQUIRED_COMPACT_ARTIFACTS
                if (compact.get(artifact_key(filename)) or {}).get("status") != "present"
            ]
            if missing_artifacts:
                findings.append(
                    f"{name} {resolution} missing required compact artifacts: "
                    + ", ".join(missing_artifacts)
                )
        readiness = entry.get("artifact_readiness")
        readiness_status = (
            readiness.get("status") if isinstance(readiness, dict) else readiness
        )
        if schema_version == "0.4" and readiness_status not in {"ready", "not_ready"}:
            findings.append(
                f"{name} has invalid artifact_readiness.status: {readiness_status}"
            )
        if review_status in {REVIEW_STATUS_COMPLETE, "complete_exploratory"} and (
            readiness_status != "ready"
        ):
            findings.append(
                f"{name} must be artifact-ready before synthesis or completion"
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
    normalized_names = [
        str(entry.get("normalized_name") or "")
        for entry in programs
        if isinstance(entry, dict) and entry.get("normalized_name")
    ]
    if normalized_names and manifest.get("program_set_slug"):
        identity_digest = program_set_identity_slug(normalized_names).rsplit("_", 1)[-1]
        if not str(manifest["program_set_slug"]).endswith(f"_{identity_digest}"):
            findings.append(
                "manifest program_set_slug does not match the normalized program-set identity"
            )
    return findings


def validate_program_list_snapshot(
    manifest_path: Path, manifest: dict[str, Any]
) -> list[str]:
    """Reconcile the final manifest with the preserved and original SME list."""

    findings: list[str] = []
    local_path = manifest_path.parent / PROGRAM_LIST_FILENAME
    if not local_path.is_file():
        return [f"missing preserved program-list snapshot: {local_path}"]
    try:
        local_programs = read_programs_file(local_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f"cannot read preserved program-list snapshot {local_path}: {exc}"]

    entries = [
        entry
        for entry in (manifest.get("programs", []) or [])
        if isinstance(entry, dict)
    ]
    manifest_inputs = [
        str(entry.get("input_name") or entry.get("normalized_name") or "")
        for entry in entries
    ]
    if local_programs != manifest_inputs:
        findings.append(
            "preserved program-list.txt does not match the ordered manifest program inputs"
        )

    normalization = (
        (manifest.get("program_resolution_profile") or {}).get(
            "program_name_normalization", {}
        )
        if isinstance(manifest.get("program_resolution_profile"), dict)
        else {}
    )
    try:
        normalized_local = [
            normalize_program_name(
                program,
                {"program_name_normalization": normalization or {}},
            )
            for program in local_programs
        ]
    except ValueError as exc:
        findings.append(f"preserved program-list.txt contains an invalid program: {exc}")
        normalized_local = []
    manifest_normalized = [str(entry.get("normalized_name") or "") for entry in entries]
    if normalized_local and normalized_local != manifest_normalized:
        findings.append(
            "preserved program-list.txt normalized identities/order do not match manifest programs"
        )

    run_profile = manifest.get("run_profile") or {}
    source = (
        run_profile.get("program_list_source")
        if isinstance(run_profile, dict)
        else None
    )
    requires_original_source = (
        str(manifest.get("schema_version") or "") == "0.4"
        and str(manifest.get("review_status") or "") == "complete_exploratory"
    )
    if requires_original_source and not isinstance(source, dict):
        findings.append(
            "v0.4 final validation requires run_profile.program_list_source trust metadata"
        )
        return findings
    if isinstance(source, dict) and source:
        source_kind = str(source.get("kind") or "").strip()
        source_path_text = str(source.get("path") or "").strip()
        expected_digest = str(source.get("sha256") or "").strip().lower()
        if source_kind == PROGRAM_LIST_SOURCE_GENERATED:
            if not expected_digest:
                findings.append(
                    "generated program-list source metadata requires sha256"
                )
            elif hashlib.sha256(local_path.read_bytes()).hexdigest() != expected_digest:
                findings.append("generated program-list.txt sha256 has changed")
            return findings
        if not source_path_text or not expected_digest:
            findings.append(
                "run_profile.program_list_source requires absolute path and sha256"
            )
        else:
            source_path = Path(source_path_text)
            if not source_path.is_absolute():
                findings.append("original program-list source path must be absolute")
            elif not source_path.is_file():
                findings.append(f"original program-list source is unavailable: {source_path}")
            else:
                actual_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                if actual_digest != expected_digest:
                    findings.append("original program-list source sha256 has changed")
                try:
                    original_programs = read_programs_file(source_path)
                except (OSError, UnicodeError, csv.Error) as exc:
                    findings.append(
                        f"cannot read original program-list source {source_path}: {exc}"
                    )
                else:
                    if original_programs != local_programs:
                        findings.append(
                            "preserved program-list.txt differs from the original SME program list"
                        )
    return findings


def validate_review(markdown: str, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    markdown = strip_markdown_comments(markdown)
    manifest_profile = manifest.get("core_review_profile", {}) or {}
    profile_name = (
        str(manifest_profile.get("name"))
        if isinstance(manifest_profile, dict) and manifest_profile.get("name")
        else CORE_REVIEW_PROFILE_DEFAULT
    )
    profile = resolve_core_review_profile({"core_review_profile": manifest_profile}, profile_name)
    required_sections = required_review_sections(profile)
    positions = h2_positions(markdown)
    rendered_h2_counts: dict[str, int] = {}
    heading_surface = "\n".join(
        _strip_container_prefix_v04(line) for line in markdown.splitlines()
    )
    h2_candidates = [
        match.group(1)
        for match in re.finditer(r"^##(?!#)\s+(.+?)\s*#*\s*$", heading_surface, re.M)
    ]
    h2_candidates.extend(
        match.group(1)
        for match in re.finditer(
            r"^([^\n|]+?)\s*\n-+\s*$", heading_surface, re.M
        )
    )
    h2_candidates.extend(
        match.group(1)
        for match in re.finditer(
            r"<h2\b[^>]*>(.*?)</h2\s*>", markdown, re.I | re.S
        )
    )
    for candidate in h2_candidates:
        label = _rendered_heading_label_v04(candidate).casefold()
        rendered_h2_counts[label] = rendered_h2_counts.get(label, 0) + 1
    missing_sections = [section for section in required_sections if section not in positions]
    if missing_sections:
        findings.append(
            "program-set review missing required reader-first ## sections: "
            + ", ".join(missing_sections)
        )
    else:
        ordered = [positions[section] for section in required_sections]
        if ordered != sorted(ordered):
            findings.append(
                "program-set review reader-first core sections must appear before audit/control sections"
            )
    controlled_sections = {
        *READER_FIRST_SECTIONS,
        "Message Coverage Control",
    }
    for section in controlled_sections:
        count = rendered_h2_counts.get(section.casefold(), 0)
        if count > 1:
            findings.append(
                f"program-set review controlled section must appear exactly once: "
                f"{section} (found {count})"
            )
    findings.extend(
        _forbidden_heading_findings_v04(markdown, FORBIDDEN_FULL_FLOW_SECTIONS)
    )
    findings.extend(_prohibited_decision_findings_v04(markdown))
    for term in FORBIDDEN_LEGACY_TERMS:
        if re.search(rf"^#{{2,6}}\s+{re.escape(term)}(?:\s+#+)?\s*$", markdown, re.M | re.I) or re.search(
            rf"\b{re.escape(term)}\b", markdown, re.I
        ):
            findings.append(f"program-set review contains forbidden legacy form: {term}")
    order_context = re.compile(
        r"\b(?:programs?|program\s+list|list|navigation|input|SME|supplied|listed|ordered)\b",
        re.I,
    )
    order_marker = re.compile(r"\b(?:order|list|listed|ordered)\b", re.I)
    order_target = re.compile(
        r"\b(?:call|execution|runtime)\s+(?:chain|order|sequence)\b|"
        r"\bexecutes?\s+in\s+(?:the\s+)?listed\s+order\b",
        re.I,
    )
    order_assertion = re.compile(
        r"\b(?:represents?|reflects?|proves?|establishes?|shows?|confirms?|"
        r"means?|is|are|executes?|listed)\b",
        re.I,
    )
    order_disclaimer = re.compile(
        r"\b(?:not|never|cannot)\b.{0,60}"
        r"(?:call|execution|runtime)\s+(?:chain|order|sequence)\b|"
        r"\bno\b.{0,60}(?:call|execution|runtime)\s+(?:chain|order|sequence)\b|"
        r"\bdoes\s+not\s+(?:represent|reflect|prove|establish|show|confirm)\b",
        re.I,
    )
    direct_order_assertion = re.compile(
        r"\bprograms?\s+(?:run|runs|execute|executes|process|processes)\s+in\s+"
        r"(?:the\s+)?(?:supplied|listed|input|navigation)\s+order\b|"
        r"\bfirst\s+listed\s+program\b.{0,80}\bprecedes?\b.{0,80}"
        r"\bnext\b.{0,30}\bruntime\b|"
        r"\bSME\s+input\s+sequence\b.{0,60}\bactual\s+call\s+path\b|"
        r"\bordered\s+list\b.{0,80}\bdefines?\b.{0,100}"
        r"\bruns?\s+first\b.{0,80}\bfollows?\b|"
        r"\bnavigation\s+order\s+(?:equals?|defines?|=)\s+runtime\s+order\b",
        re.I | re.S,
    )
    direct_order_negation = re.compile(
        r"\b(?:not|never|cannot|does\s+not|do\s+not|is\s+not)\b.{0,100}"
        r"(?:run|execute|process|precede|follow|equal|define|actual\s+call\s+path)",
        re.I | re.S,
    )
    unsafe_order = any(
        direct_order_assertion.search(sentence)
        and not direct_order_negation.search(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", markdown)
    )
    order_spans = re.split(
        r"(?<=[.!?])\s+|[;:—–]|"
        r"\b(?:but|however|although|though|nevertheless|yet|and|then)\b|"
        r",\s*(?=(?:the\b|it\b|we\b|programs?\b|list\b|order\b))",
        markdown,
        flags=re.I,
    )
    prior_context = False
    prior_marker = False
    for clause in order_spans:
        if unsafe_order:
            break
        local_context = bool(order_context.search(clause))
        local_marker = bool(order_marker.search(clause))
        if (
            (local_context or prior_context)
            and (local_marker or prior_marker)
            and order_target.search(clause)
            and order_assertion.search(clause)
            and not order_disclaimer.search(clause)
        ):
            unsafe_order = True
            break
        prior_context = local_context
        prior_marker = local_marker
    if unsafe_order:
        findings.append(
            "program list/navigation order must not be treated as a source-confirmed call chain or runtime execution sequence"
        )

    summary_block = h2_section_block(markdown, "Program Set Reading Summary")
    if summary_block:
        summary_detail = prose_and_table_detail(summary_block)
        layer_terms = sum(
            1
            for term in (
                "calculation",
                "validation",
                "exception",
                "message",
                "outcome",
            )
            if re.search(rf"\b{term}\b", summary_detail, re.I)
        )
        has_status = re.search(
            r"\b(complete|complete_exploratory|ready_for_synthesis|standalone_exploratory|chain_ready|draft)\b",
            summary_detail,
            re.I,
        )
        if (
            not has_reader_useful_detail(summary_block, minimum_words=25)
            or layer_terms < 2
            or not has_status
            or ARTIFACT_REF_RE.search(summary_detail)
        ):
            findings.append(
                "Program Set Reading Summary is placeholder/artifact-only or missing reader-useful program-set context"
            )
        if manifest.get("review_status") == REVIEW_STATUS_PARTIAL and not re.search(
            r"\b(partial|pending|unresolved|missing|blocked|source\s+scan)\b",
            summary_detail,
            re.I,
        ):
            findings.append("partial_pending_program review summary must state the missing or pending program")

    overview_block = h2_section_block(markdown, "Cross-Program Processing Overview")
    if overview_block:
        required_headers = (
            "Processing Layer",
            "Programs / Main Routines",
            "What To Understand First",
            "Review Row ID",
            "Source Fact Refs",
        )
        if not table_has_headers(overview_block, required_headers):
            findings.append("Cross-Program Processing Overview missing required table headers")
        overview_rows = table_data_rows(overview_block)
        if len(overview_rows) < 4:
            findings.append("Cross-Program Processing Overview must include processing-layer rows")
        for row in overview_rows:
            if len(row) < 5 or any(is_placeholder_cell(cell or "") for cell in row[:5]):
                findings.append("Cross-Program Processing Overview has placeholder processing-layer detail")
                break

    section_headers: dict[str, tuple[str, ...]] = {
        "Calculation Logic": (
            "Calculation / Assignment",
            "Program",
            "Routine",
            "Target Field / Carrier",
            "Source Operands / Carriers",
            "Guard / Branch",
            "Effect",
            "Supporting Detail",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Validation Logic": (
            "Message / Status / Outcome",
            "Program",
            "Routine",
            "Condition / Evidence",
            "Carrier / Destination",
            "Effect",
            "Supporting Detail",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Exception Handling": (
            "Exception / Error Path",
            "Program",
            "Routine",
            "Detection Mechanism",
            "Fields / Messages Set",
            "Handling Action",
            "Effect",
            "Supporting Detail",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Message Inventory": (
            "Message / Status / Literal",
            "Description",
            "Type",
            "Program / Routine Sources",
            "Occurrences",
            "Condition / Handler",
            "Carrier / Destination",
            "Effect",
            "Detail Refs",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Message Coverage Control": (
            "Message / Status / Literal",
            "Description",
            "Type",
            "Program / Routine Sources",
            "Occurrences",
            "Condition / Handler",
            "Carrier / Destination",
            "Effect",
            "Detail Refs",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
    }
    core_programs: dict[str, set[str]] = {}
    all_core_text: list[str] = []
    for section, required_headers in section_headers.items():
        block = h2_section_block(markdown, section)
        is_required = section in required_sections
        if not block:
            if is_required:
                findings.append(f"{section} lacks reader-useful detail")
            continue
        records = extract_markdown_table_records(block, required_headers)
        if not records:
            if is_required:
                findings.append(
                    f"{section} lacks reader-useful detail: missing required row columns or data rows"
                )
            continue
        distinct_programs: set[str] = set()
        section_text: list[str] = []
        for record in records:
            values = list(record.values())
            section_text.extend(values)
            program = _fact_value(record, "Program")
            if not program:
                program = _fact_value(record, "Program / Routine Sources")
            if program:
                distinct_programs.add(program)
            for header in required_headers:
                value = _fact_value(record, header)
                if is_placeholder_cell(value):
                    findings.append(f"{section} row has missing required column: {header}")
                    break
            semantic_text = " ".join(
                str(value)
                for header, value in record.items()
                if header
                not in {
                    "Program",
                    "Routine",
                    "Program / Routine Sources",
                    "Supporting Detail",
                    "Detail Refs",
                    "Evidence Status",
                    "Review Row ID",
                    "Source Fact Refs",
                }
            )
            if len(reader_words(semantic_text)) < 5:
                findings.append(
                    f"{section} row is link-only and lacks reader-useful logic"
                )
            detail = " ".join(values)
            if not has_reader_useful_detail(detail, minimum_words=3) and not re.search(
                r"\b(unresolved|pending|missing|not available|tbd)\b", detail, re.I
            ):
                findings.append(f"{section} contains link-only or summary-only row")
        if distinct_programs:
            core_programs[section] = distinct_programs
        all_core_text.extend(section_text)
        if is_required and not has_reader_useful_detail(block):
            findings.append(f"{section} lacks reader-useful detail")

    manifest_program_names = {
        str(entry.get("normalized_name") or "")
        for entry in manifest.get("programs", []) or []
        if entry.get("normalized_name")
    }
    if len(manifest_program_names) >= 2 and not any(
        len(programs) >= 2 for programs in core_programs.values()
    ):
        findings.append("at least one core section must contain rows for two or more programs")
    if manifest_program_names and not re.search(
        r"\b(carrier|return\s*(?:status|code)|queue|file|output|handoff)\b",
        " ".join(all_core_text),
        re.I,
    ):
        findings.append("at least one core row must show a carrier, return status, queue, file, or output handoff")

    for section in required_sections:
        if section in {"Program Set Reading Summary", "Cross-Program Processing Overview"}:
            continue
        if section not in section_headers:
            continue
        block = h2_section_block(markdown, section)
        if not block:
            continue
        if ARTIFACT_REF_RE.search(prose_and_table_detail(block)) and not extract_markdown_table_records(
            block, section_headers[section]
        ):
            findings.append(f"{section} cannot be artifact-link-only")

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
        uses_new_partial_contract = bool(
            re.search(r"\bpartial_pending_program\b", summary_block, re.I)
        )
        if resolution in {RUN_PENDING, RUN_BLOCKED} and uses_new_partial_contract:
            ledger_detail = " ".join(ledger_rows.get(program, []))
            if not re.search(r"\b(pending|unresolved|missing|blocked|scan)\b", ledger_detail, re.I):
                findings.append(f"{program} missing program must remain explicitly pending/unresolved")
            unresolved_core_row = any(
                program in programs and re.search(
                    r"\b(unresolved|pending|missing|not available|tbd)\b",
                    " ".join(
                        value
                        for record in extract_markdown_table_records(
                            h2_section_block(markdown, section),
                            section_headers.get(section, ()),
                        )
                        for value in record.values()
                    ),
                    re.I,
                )
                for section, programs in core_programs.items()
            )
            if not unresolved_core_row:
                findings.append(f"{program} missing program requires an explicit unresolved core row")
    return findings


def _front_matter(markdown: str) -> dict[str, Any]:
    if not markdown.startswith("---\n"):
        return {}
    end = markdown.find("\n---", 4)
    if end < 0:
        return {}
    try:
        payload = _load_unique_yaml_text(markdown[4:end])
    except Exception:  # pragma: no cover - surfaced as a validation finding
        return {}
    return payload if isinstance(payload, dict) else {}


def _anchor_present(markdown: str, anchor: str) -> bool:
    markdown = _anchor_markup_surface(markdown)
    escaped = re.escape(anchor)
    return bool(
        re.search(rf"(?<!\\)<a\s+(?:[^>]*\s)?id=[\"']{escaped}[\"'][^>]*>", markdown, re.I)
        or re.search(rf"(?<!\\)\{{#{escaped}\}}", markdown)
        or re.search(rf"^(?<!\\)<[^>]+\s+id=[\"']{escaped}[\"']", markdown, re.M | re.I)
    )


def _anchor_definition_count(markdown: str, anchor: str) -> int:
    markdown = _anchor_markup_surface(markdown)
    escaped = re.escape(anchor)
    return len(
        re.findall(
            rf"(?<!\\)<a\s+(?:[^>]*\s)?id=[\"']{escaped}[\"'][^>]*>",
            markdown,
            re.I,
        )
    ) + len(re.findall(rf"(?<!\\)\{{#{escaped}\}}", markdown))


def _anchor_markup_surface(markdown: str) -> str:
    visible = strip_markdown_comments(markdown)
    return re.sub(
        r"(?P<fence>`+).*?(?P=fence)", "", visible, flags=re.S
    )


def _literal_present(text: str, literal: str, *, case_sensitive: bool = True) -> bool:
    return _exact_literal_present_v04(
        text, literal, case_sensitive=case_sensitive
    )


def _required_fact_semantics(fact: dict[str, Any]) -> list[tuple[str, str]]:
    fact_type = str(fact.get("fact_type") or "")
    if fact_type in {"summary_contribution", "thematic_prose"}:
        return []
    if fact_type == "thematic_table":
        source_row = fact.get("source_row")
        if not isinstance(source_row, dict):
            return []
        values: list[tuple[str, str]] = []
        seen: set[str] = set()
        for header, raw_value in source_row.items():
            value = str(raw_value or "").strip()
            if not value or value.lower() in {
                "-",
                "--",
                "---",
                "—",
                "none",
                "n/a",
                "not applicable",
            } or value in seen:
                continue
            seen.add(value)
            values.append((f"source_row.{str(header).strip()}", value))
        return values
    common = ("program", "routine", "evidence_reference", "evidence_status")
    by_type = {
        "calculation": (
            "calculation",
            "target_carrier",
            "source_carriers",
            "guard",
            "effect",
            "supporting_detail",
        ),
        "validation": (
            "description",
            "validation_type",
            "trigger_chain",
            "carrier_destination",
            "effect",
        ),
        "exception": (
            "exception_path",
            "guard",
            "detection_mechanism",
            "fields_messages_set",
            "exception_action",
            "effect",
            "supporting_detail",
        ),
        "message": (
            "description",
            "message_type",
            "generic_handler_token",
            "occurrences",
            "first_seen",
            "trigger_handler",
            "carrier_destination",
            "effect",
        ),
        "routine": ("category", "logic"),
        "unresolved_core_statement": ("logic", "unresolved_reason"),
    }
    keys = (*common, *by_type.get(fact_type, ()))
    values: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key in keys:
        value = str(fact.get(key) or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append((key, value))
    return values


_SUMMARY_SEMANTIC_STOP_WORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "analysis",
        "approved",
        "artifact",
        "asserted",
        "available",
        "before",
        "complete",
        "confirmed",
        "consulting",
        "context",
        "contribution",
        "detail",
        "details",
        "evidence",
        "exploratory",
        "fact",
        "fixture",
        "follow",
        "itself",
        "local",
        "marker",
        "overview",
        "program",
        "reader",
        "reading",
        "review",
        "routine",
        "routines",
        "source",
        "standalone",
        "summary",
        "thematic",
        "trace",
        "understand",
        "wrapper",
        "with",
        "without",
        "would",
        "your",
        "from",
        "into",
        "that",
        "this",
        "these",
        "those",
        "their",
        "then",
        "than",
        "when",
        "where",
        "which",
        "while",
        "should",
        "could",
        "must",
        "will",
        "have",
        "has",
        "does",
        "using",
        "used",
        "identifiers",
        "obj",
    }
)


def _summary_semantic_terms(text: str, program: str) -> set[str]:
    visible = _visible_inline_text_v04(text)
    visible = DETAIL_REF_RE.sub(" ", ARTIFACT_REF_RE.sub(" ", visible))
    excluded = _SUMMARY_SEMANTIC_STOP_WORDS | {program.casefold(), "sf"}
    return {
        match.group(0).casefold()
        for match in re.finditer(r"[A-Za-z][A-Za-z0-9]{2,}", visible)
        if match.group(0).casefold() not in excluded
    }


def _summary_semantics_preserved(
    fact: dict[str, Any], mapped_texts: list[str]
) -> bool:
    source_text = str(
        fact.get("logic") or fact.get("source_text") or fact.get("description") or ""
    ).strip()
    if not source_text:
        return True
    program = str(fact.get("program") or "").strip()
    source_terms = _summary_semantic_terms(source_text, program)
    mapped_terms = _summary_semantic_terms(" ".join(mapped_texts), program)
    if not source_terms:
        return bool(mapped_terms)
    required_overlap = min(4, max(1, (len(source_terms) + 4) // 5))
    return len(source_terms & mapped_terms) >= required_overlap


def _validate_cross_program_relation_claims(
    markdown: str,
    fact_map: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> list[str]:
    return _cross_program_relation_findings_v04(
        strip_markdown_comments(markdown), fact_map, manifest
    )


def _validate_overview_evidence(
    markdown: str, fact_map: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> list[str]:
    findings: list[str] = []
    block = h2_section_block(markdown, "Cross-Program Processing Overview")
    headers = (
        "Processing Layer",
        "Programs / Main Routines",
        "What To Understand First",
        "Review Row ID",
        "Source Fact Refs",
    )
    records = extract_markdown_table_records(block, headers)
    relation_claim = re.compile(
        r"\b(?:calls?|invokes?|producer|consumer)\b|"
        r"\b(?:always\s+)?executes?\s+(?:before|after|in\s+that\s+order)\b|"
        r"\b(?:confirmed|actual|source[- ]confirmed)\s+"
        r"(?:call|execution)\s+(?:chain|order|sequence)\b",
        re.I,
    )
    sequence_claim = re.compile(
        r"\b(?:always\s+)?executes?\s+(?:before|after|in\s+that\s+order)\b|"
        r"\b(?:confirmed|actual|source[- ]confirmed)\s+execution\s+"
        r"(?:order|sequence)\b",
        re.I,
    )
    known_programs = {
        str(entry.get("normalized_name") or "")
        for entry in manifest.get("programs", []) or []
        if entry.get("normalized_name")
    }
    for record in records:
        refs = set(
            re.findall(
                r"\bSF-[A-Za-z0-9_@#$-]+\b",
                _visible_inline_text_v04(_fact_value(record, "Source Fact Refs")),
            )
        )
        if not refs:
            findings.append(
                "Cross-Program Processing Overview row lacks source fact references"
            )
        for fact_id in sorted(refs - set(fact_map)):
            findings.append(
                f"Cross-Program Processing Overview references unknown source fact {fact_id}"
            )
        row_id = _fact_value(record, "Review Row ID")
        row_anchor_surface = _anchor_markup_surface(row_id)
        anchor_match = re.search(
            r"(?<!\\)(?:id=[\"'](?P<html>[^\"']+)[\"']|\{#(?P<attr>[^}]+)\})",
            row_anchor_surface,
            re.I,
        )
        anchor = (
            (anchor_match.group("html") or anchor_match.group("attr"))
            if anchor_match
            else ""
        )
        if (
            not anchor
            or not _anchor_present(row_id, anchor)
            or _anchor_definition_count(markdown, anchor) != 1
        ):
            findings.append(
                "Cross-Program Processing Overview row requires one unique review anchor"
            )
        claim_text = " ".join(
            (
                _fact_value(record, "Processing Layer"),
                _fact_value(record, "Programs / Main Routines"),
                _fact_value(record, "What To Understand First"),
            )
        )
        if sequence_claim.search(claim_text):
            findings.append(
                "Cross-Program Processing Overview must not assert execution order or sequence"
            )
        elif relation_claim.search(claim_text):
            referenced_text = " ".join(
                json.dumps(fact_map[fact_id], sort_keys=True, default=str)
                for fact_id in refs
                if fact_id in fact_map
            )
            mentioned = {program for program in known_programs if program in claim_text}
            evidence_mentions = all(program in referenced_text for program in mentioned)
            evidence_has_relation = bool(relation_claim.search(referenced_text))
            if not refs or not evidence_mentions or not evidence_has_relation:
                findings.append(
                    "Cross-Program Processing Overview contains an unsupported call/producer-consumer claim"
                )
    prose_lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip()
        and not line.lstrip().startswith(("#", "|", "<!--"))
    ]
    if relation_claim.search(" ".join(prose_lines)):
        findings.append(
            "Cross-Program Processing Overview prose contains an untracked call/sequence claim"
        )
    findings.extend(
        _validate_cross_program_relation_claims(markdown, fact_map, manifest)
    )
    return findings


def validate_review_identity(markdown: str, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    metadata = _front_matter(markdown)
    if not metadata:
        return ["final review missing valid YAML front matter"]
    expected = {
        "document_id": manifest.get("document_id") or manifest.get("review_id"),
        "flow_slug": manifest.get("flow_slug"),
        "program_set_slug": manifest.get("program_set_slug"),
        "artifact_version": manifest.get("artifact_version"),
    }
    for key, value in expected.items():
        if str(metadata.get(key) or "") != str(value or ""):
            findings.append(f"final review front matter {key} does not match manifest")
    if str(metadata.get("review_status") or "") != "complete_exploratory":
        findings.append("final review front matter review_status must be complete_exploratory")
    expected_programs = {
        str(entry.get("normalized_name") or "")
        for entry in manifest.get("programs", []) or []
        if entry.get("normalized_name")
    }
    actual_programs = metadata.get("programs") or []
    if isinstance(actual_programs, str):
        actual_programs = [actual_programs]
    if {str(value) for value in actual_programs} != expected_programs:
        findings.append("final review front matter programs do not match manifest")
    folder_slug = str(manifest.get("folder_slug") or "")
    visible_markdown = strip_markdown_comments(markdown)
    h1_matches = list(
        re.finditer(r"^[ ]{0,3}#(?!#)\s+(.+?)\s*#*\s*$", visible_markdown, re.M)
    )
    if len(h1_matches) != 1:
        findings.append("final review must contain exactly one canonical H1 title")
    rendered_h1 = (
        _visible_inline_text_v04(h1_matches[0].group(1)) if len(h1_matches) == 1 else ""
    )
    if not _literal_present(rendered_h1, folder_slug, case_sensitive=False):
        findings.append("final review H1 must include the flow/program-set folder identity")
    return findings


def _safe_manifest_relative_path(
    root: Path, value: Any, *, label: str
) -> tuple[str | None, str | None]:
    """Resolve one manifest path without allowing an absolute or escaping path."""

    text = str(value or "").strip()
    if not text:
        return None, f"{label} is missing"
    relative = Path(text)
    if relative.is_absolute():
        return None, f"{label} must be relative to run_profile.artifact_root"
    try:
        resolved = (root / relative).resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None, f"{label} escapes run_profile.artifact_root"
    return resolved.relative_to(root).as_posix(), None


def _compact_artifact_containment_findings(
    *,
    root: Path,
    artifact_root: str,
    compact_artifacts: dict[str, ArtifactStatus],
    program: str,
) -> list[str]:
    """Keep every resolved compact artifact inside its program directory."""

    findings: list[str] = []
    try:
        program_dir = (root / artifact_root).resolve(strict=True)
    except (OSError, RuntimeError):
        return [
            f"final input readiness {program} program artifact directory is unavailable"
        ]
    for status in compact_artifacts.values():
        if status.status != "present":
            continue
        relative = Path(status.path)
        if relative.is_absolute():
            findings.append(
                f"final input readiness {program} compact artifact path must be relative"
            )
            continue
        try:
            resolved = (root / relative).resolve(strict=True)
            resolved.relative_to(root)
            resolved.relative_to(program_dir)
        except (OSError, RuntimeError, ValueError):
            findings.append(
                f"final input readiness {program} compact artifact {status.path} "
                "escapes the program artifact directory"
            )
    return findings


def revalidate_manifest_program_inputs(
    manifest: dict[str, Any],
) -> tuple[list[str], dict[str, Any] | None, Path | None]:
    """Re-resolve and revalidate every distinct final-synthesis input.

    The stored readiness result is evidence from preparation time, not a trust
    decision for final validation.  This gate derives paths again from the
    run root and resolution profile, then reruns the complete upstream
    readiness contract before any prepared bundle is regenerated.
    """

    findings: list[str] = []
    run_profile = manifest.get("run_profile")
    if not isinstance(run_profile, dict):
        return ["final input readiness requires manifest run_profile"], None, None

    mode = str(run_profile.get("artifact_repo_mode") or "")
    if mode not in {ARTIFACT_REPO_CURRENT_RUN, ARTIFACT_REPO_APPROVED_DOCUMENT}:
        findings.append(
            "final input readiness requires artifact_repo_mode current_run or "
            "approved_document_repo"
        )
    approved_repo = mode == ARTIFACT_REPO_APPROVED_DOCUMENT
    expected_cross_run = approved_repo
    if run_profile.get("cross_run_reuse") is not expected_cross_run:
        findings.append(
            "manifest run_profile cross_run_reuse does not match artifact_repo_mode"
        )
    expected_policy = (
        "approved_document_repo_clone" if approved_repo else "current_run_only"
    )
    if str(run_profile.get("reuse_policy") or "") != expected_policy:
        findings.append(
            "manifest run_profile reuse_policy does not match artifact_repo_mode"
        )

    root_text = str(run_profile.get("artifact_root") or "").strip()
    if not root_text:
        return [*findings, "final input readiness requires run_profile.artifact_root"], None, None
    try:
        artifact_root = Path(root_text).resolve(strict=True)
    except (OSError, RuntimeError):
        return [*findings, f"final input readiness artifact root is unavailable: {root_text}"], None, None
    if not artifact_root.is_dir():
        return [*findings, f"final input readiness artifact root is not a directory: {artifact_root}"], None, None

    resolution_profile = manifest.get("program_resolution_profile")
    if not isinstance(resolution_profile, dict):
        findings.append(
            "final input readiness requires manifest program_resolution_profile"
        )
        return findings, None, artifact_root
    patterns = resolution_profile.get("program_folder_patterns")
    if not isinstance(patterns, list) or not patterns:
        findings.append(
            "final input readiness requires non-empty program_folder_patterns"
        )
        return findings, None, artifact_root
    for pattern in patterns:
        text = str(pattern or "")
        probe = Path(text.replace("{PROGRAM}", "PROGRAM"))
        if not text or "{PROGRAM}" not in text or probe.is_absolute() or ".." in probe.parts:
            findings.append(
                f"unsafe program artifact resolution pattern in manifest: {text or '<empty>'}"
            )
    if findings:
        return findings, None, artifact_root

    programs = manifest.get("programs")
    if not isinstance(programs, list) or not programs:
        return ["final input readiness requires manifest programs[]"], None, artifact_root

    workspace_profile = manifest.get("workspace_profile")
    if not isinstance(workspace_profile, dict):
        workspace_profile = {}

    trusted_entries: list[dict[str, Any]] = []
    resolved_by_program: dict[str, str] = {}
    for entry in programs:
        if not isinstance(entry, dict):
            findings.append("final input readiness found a non-mapping program entry")
            continue
        program = str(entry.get("normalized_name") or "")
        try:
            validate_normalized_program_name(program)
        except ValueError as exc:
            findings.append(f"final input readiness: {exc}")
            continue

        is_duplicate = program in resolved_by_program
        expected_resolution = (
            RUN_ARTIFACT_REPO
            if approved_repo
            else RUN_REUSED
            if is_duplicate
            else RUN_ANALYZED
        )
        expected_source = (
            "approved_document_repo" if approved_repo else "delivery_working_branch"
        )
        if str(entry.get("run_resolution") or "") != expected_resolution:
            findings.append(
                f"final input readiness {program} must use run_resolution "
                f"{expected_resolution} for artifact_repo_mode {mode}"
            )
        if str(entry.get("artifact_source") or "") != expected_source:
            findings.append(
                f"final input readiness {program} must use artifact_source {expected_source}"
            )

        if is_duplicate:
            resolved_artifact_root = resolved_by_program[program]
            manifest_relative, path_finding = _safe_manifest_relative_path(
                artifact_root,
                entry.get("artifact_root"),
                label=f"{program} duplicate artifact_root",
            )
            if path_finding:
                findings.append(path_finding)
            elif manifest_relative != resolved_artifact_root:
                findings.append(
                    f"final input readiness {program} duplicate artifact_root differs "
                    "from the first occurrence"
                )
            continue

        try:
            resolved_artifact_root, matches = find_program_artifact_root(
                artifact_root, program, resolution_profile
            )
        except (OSError, RuntimeError, ValueError, NotImplementedError) as exc:
            findings.append(
                f"final input readiness cannot resolve {program} artifact path: {exc}"
            )
            continue
        if not resolved_artifact_root or len(matches) != 1:
            detail = ", ".join(matches) if matches else "no contained match"
            findings.append(
                f"final input readiness {program} requires exactly one contained "
                f"artifact directory; found {detail}"
            )
            continue

        for key, label in (
            ("artifact_root", "artifact_root"),
            ("candidate_artifact_root", "candidate_artifact_root"),
        ):
            manifest_relative, path_finding = _safe_manifest_relative_path(
                artifact_root,
                entry.get(key),
                label=f"{program} {label}",
            )
            if path_finding:
                findings.append(path_finding)
            elif manifest_relative != resolved_artifact_root:
                findings.append(
                    f"final input readiness {program} {label} was replaced or no "
                    "longer matches the resolved artifact directory"
                )

        compact_artifacts = collect_artifact_statuses(
            artifact_root, resolved_artifact_root, program
        )
        detected_tier = infer_tier(resolved_artifact_root, workspace_profile)
        expected_compact = {
            key: {"path": status.path, "status": status.status}
            for key, status in compact_artifacts.items()
        }
        if entry.get("compact_artifacts") != expected_compact:
            findings.append(
                f"final input readiness {program} compact artifact inventory differs "
                "from the current artifact root"
            )

        containment_findings = _compact_artifact_containment_findings(
            root=artifact_root,
            artifact_root=resolved_artifact_root,
            compact_artifacts=compact_artifacts,
            program=program,
        )
        findings.extend(containment_findings)
        readiness = (
            {
                "status": "not_ready",
                "validator_status": "not_run",
                "analysis_status": None,
                "candidate_artifact_root": resolved_artifact_root,
                "findings": containment_findings,
            }
            if containment_findings
            else assess_artifact_readiness(
                root=artifact_root,
                program=program,
                candidate_artifact_root=resolved_artifact_root,
                matches=matches,
                compact_artifacts=compact_artifacts,
                expected_size_tier=detected_tier,
                strict=True,
            )
        )
        if readiness.get("status") != "ready":
            reasons = "; ".join(
                str(item) for item in readiness.get("findings", []) or []
            )
            findings.append(
                f"final input readiness for {program} is not ready: "
                f"{reasons or 'readiness contract failed'}"
            )
        stored_readiness = entry.get("artifact_readiness")
        if not isinstance(stored_readiness, dict) or stored_readiness.get("status") != "ready":
            findings.append(
                f"final input readiness {program} manifest preparation status is not ready"
            )

        resolved_by_program[program] = resolved_artifact_root
        trusted_entries.append(
            {
                **entry,
                "run_resolution": expected_resolution,
                "artifact_root": resolved_artifact_root,
                "candidate_artifact_root": resolved_artifact_root,
                "artifact_source": expected_source,
                "tier": detected_tier,
                "compact_artifacts": expected_compact,
                "artifact_readiness": readiness,
            }
        )

    if findings:
        return findings, None, artifact_root
    trusted_manifest = {
        **manifest,
        "run_profile": {**run_profile, "artifact_root": str(artifact_root)},
        "programs": trusted_entries,
    }
    return [], trusted_manifest, artifact_root


def validate_prepared_bundle_integrity(
    *,
    manifest: dict[str, Any],
    artifact_root: Path,
    source_pack_path: Path,
    core_facts_path: Path,
) -> list[str]:
    """Compare prepared artifacts with a fresh build from revalidated inputs."""

    findings: list[str] = []
    if not source_pack_path.is_file() or not core_facts_path.is_file():
        return findings
    try:
        expected_source_pack = build_reader_first_source_pack(manifest, artifact_root)
        expected_facts = build_core_facts(manifest, artifact_root)
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        return [
            "cannot regenerate reader-first preparation bundle from current "
            f"validated program-analysis inputs: {exc}"
        ]

    actual_source_pack = source_pack_path.read_text(encoding="utf-8")
    normalize_newlines = lambda value: value.replace("\r\n", "\n").replace("\r", "\n")
    if normalize_newlines(actual_source_pack) != normalize_newlines(expected_source_pack):
        findings.append(
            "source pack differs from the current validated program-analysis inputs"
        )

    actual_facts = load_yaml(core_facts_path)
    if not isinstance(actual_facts, dict):
        findings.append("core facts artifact is not a YAML mapping")
        return findings

    def immutable_preparation(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in payload.items()
            if key != "review_status"
        }

    if immutable_preparation(actual_facts) != immutable_preparation(expected_facts):
        findings.append(
            "normalized core facts differ from the current validated program-analysis inputs"
        )

    expected_by_id = {
        str(fact.get("source_fact_id") or ""): fact
        for fact in expected_facts.get("source_facts", []) or []
        if isinstance(fact, dict) and fact.get("source_fact_id")
    }
    actual_by_id = {
        str(fact.get("source_fact_id") or ""): fact
        for fact in actual_facts.get("source_facts", []) or []
        if isinstance(fact, dict) and fact.get("source_fact_id")
    }
    for fact_id in sorted(set(expected_by_id) - set(actual_by_id)):
        findings.append(
            f"source-pack fact {fact_id} is missing from normalized core facts"
        )
    for fact_id in sorted(set(actual_by_id) - set(expected_by_id)):
        findings.append(
            f"normalized core fact {fact_id} is not derivable from the current "
            "validated program-analysis inputs"
        )
    for fact_id in sorted(set(expected_by_id) & set(actual_by_id)):
        if expected_by_id[fact_id] != actual_by_id[fact_id]:
            findings.append(
                f"normalized core fact {fact_id} differs from the current "
                "validated program-analysis inputs"
            )
    return findings


def _coverage_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("coverage_items")
    if not isinstance(items, list):
        items = payload.get("items")
    return [item for item in (items or []) if isinstance(item, dict)]


def _source_pack_program_block(source_pack: str, program: str) -> str:
    marker = re.search(
        rf"^<!-- BEGIN LOSSLESS PROGRAM {re.escape(program)}(?::.*?)? -->\s*$",
        source_pack,
        re.M,
    )
    if marker:
        end = re.search(
            rf"^<!-- END LOSSLESS PROGRAM {re.escape(program)} -->\s*$",
            source_pack[marker.end() :],
            re.M,
        )
        stop = marker.end() + end.end() if end else len(source_pack)
        return source_pack[marker.start() : stop]
    heading = re.search(
        rf"^(?:# Program:\s*|##\s+){re.escape(program)}\s*$",
        source_pack,
        re.M,
    )
    if not heading:
        return ""
    next_program = re.search(
        r"^(?:# Program:\s*|##\s+)[@A-Za-z0-9_$#.-]+\s*$",
        source_pack[heading.end() :],
        re.M,
    )
    stop = heading.end() + next_program.start() if next_program else len(source_pack)
    return source_pack[heading.start() : stop]


def _review_section_for_fact(
    fact: dict[str, Any], manifest: dict[str, Any]
) -> str:
    section = str(fact.get("section") or "")
    if section == "Program Reading Summary":
        return "Program Set Reading Summary"
    profile = manifest.get("core_review_profile") or {}
    if section == "Message Inventory" and not bool(
        profile.get("include_message_inventory", True)
    ):
        return "Message Coverage Control"
    return section


_SUMMARY_FACT_ROW_HEADERS = (
    "Program",
    "Scope / Reader-First Contribution",
    "Artifact Readiness",
    "Coverage",
    "Review Row ID",
    "Source Fact Refs",
)

_CORE_FACT_ROW_HEADERS: dict[str, tuple[str, ...]] = {
    "Calculation Logic": (
        "Calculation / Assignment",
        "Program",
        "Routine",
        "Target Field / Carrier",
        "Source Operands / Carriers",
        "Guard / Branch",
        "Effect",
        "Supporting Detail",
        "Evidence Status",
        "Review Row ID",
        "Source Fact Refs",
    ),
    "Validation Logic": (
        "Message / Status / Outcome",
        "Description",
        "Program",
        "Routine",
        "Condition / Evidence",
        "Carrier / Destination",
        "Effect",
        "Supporting Detail",
        "Evidence Status",
        "Review Row ID",
        "Source Fact Refs",
    ),
    "Exception Handling": (
        "Exception / Error Path",
        "Program",
        "Routine",
        "Detection Mechanism",
        "Fields / Messages Set",
        "Handling Action",
        "Effect",
        "Supporting Detail",
        "Evidence Status",
        "Review Row ID",
        "Source Fact Refs",
    ),
    "Message Inventory": (
        "Message / Status / Literal",
        "Description",
        "Type",
        "Program / Routine Sources",
        "Occurrences",
        "Condition / Handler",
        "Carrier / Destination",
        "Effect",
        "Detail Refs",
        "Evidence Status",
        "Review Row ID",
        "Source Fact Refs",
    ),
    "Message Coverage Control": (
        "Message / Status / Literal",
        "Description",
        "Type",
        "Program / Routine Sources",
        "Occurrences",
        "Condition / Handler",
        "Carrier / Destination",
        "Effect",
        "Detail Refs",
        "Evidence Status",
        "Review Row ID",
        "Source Fact Refs",
    ),
}


def _fact_row_headers(review_section: str) -> tuple[str, ...]:
    if review_section == "Program Set Reading Summary":
        return _SUMMARY_FACT_ROW_HEADERS
    return _CORE_FACT_ROW_HEADERS.get(review_section, ())


def _visible_fact_mapping_rows(
    visible_markdown: str,
    review_section: str,
    anchor: str,
    fact_id: str,
) -> list[dict[str, str]]:
    visible_markdown = strip_markdown_comments(visible_markdown)
    headers = _fact_row_headers(review_section)
    if not headers:
        return []
    block = h2_section_block(visible_markdown, review_section)
    matches: list[dict[str, str]] = []
    for record in extract_markdown_table_records(block, headers):
        row_id = _fact_value(record, "Review Row ID")
        refs = set(
            re.findall(
                r"\bSF-[A-Za-z0-9_@#$-]+\b",
                _visible_inline_text_v04(_fact_value(record, "Source Fact Refs")),
            )
        )
        if anchor and _anchor_present(row_id, anchor) and fact_id in refs:
            matches.append(record)
    return matches


def _visible_anchored_prose_lines(
    visible_markdown: str,
    review_section: str,
    anchor: str,
    fact_id: str,
) -> list[str]:
    block = h2_section_block(visible_markdown, review_section)
    return [
        line.strip()
        for line in block.splitlines()
        if line.strip()
        and not line.lstrip().startswith(("#", "|"))
        and anchor
        and fact_id in _visible_inline_text_v04(line)
        and _anchor_present(line, anchor)
        and _mapped_line_word_count(line, fact_id, "") >= 7
    ]


def _fact_row_text(record: dict[str, str]) -> str:
    return " | ".join(str(value) for value in record.values())


def _canonical_review_table_records(
    block: str, section: str, required_headers: tuple[str, ...]
) -> tuple[list[dict[str, str]], list[str]]:
    """Read canonical rows without silently accepting shifted/truncated cells."""

    lines = block.splitlines()
    records: list[dict[str, str]] = []
    findings: list[str] = []
    consumed_rows: set[int] = set()
    index = 0
    required = {header.casefold() for header in required_headers}
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (
            header_line.startswith("|")
            and header_line.endswith("|")
            and is_table_separator(separator_line)
        ):
            index += 1
            continue
        headers = [
            cell.strip() for cell in _split_markdown_table_row_v04(header_line)
        ]
        if not required.issubset({header.casefold() for header in headers}):
            index += 1
            continue
        separator_cells = _split_markdown_table_row_v04(separator_line)
        if len(separator_cells) != len(headers):
            findings.append(
                f"{section} canonical fact table separator has "
                f"{len(separator_cells)} cells; expected exactly {len(headers)}"
            )
            index += 2
            while index < len(lines):
                malformed_row = lines[index].strip()
                if not (
                    malformed_row.startswith("|")
                    and malformed_row.endswith("|")
                ):
                    break
                consumed_rows.add(index)
                index += 1
            continue
        if tuple(headers) != required_headers:
            findings.append(
                f"{section} canonical fact table headers must match the required order exactly"
            )
        index += 2
        while index < len(lines):
            row_line = lines[index].strip()
            if not (row_line.startswith("|") and row_line.endswith("|")):
                break
            if is_table_separator(row_line):
                index += 1
                continue
            cells = [
                cell.strip() for cell in _split_markdown_table_row_v04(row_line)
            ]
            if len(cells) != len(headers):
                findings.append(
                    f"{section} canonical fact row has {len(cells)} cells; "
                    f"expected exactly {len(headers)}"
                )
                index += 1
                continue
            records.append(dict(zip(headers, cells)))
            consumed_rows.add(index)
            index += 1
    for row_index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if (
            row_index in consumed_rows
            or not stripped.startswith("|")
            or not stripped.endswith("|")
            or is_table_separator(stripped)
        ):
            continue
        cells = [cell.strip() for cell in _split_markdown_table_row_v04(stripped)]
        if tuple(cells) == required_headers or required.issubset(
            {cell.casefold() for cell in cells}
        ):
            continue
        if len(cells) == len(required_headers):
            findings.append(
                f"{section} canonical-looking fact row is outside its required table"
            )
            records.append(dict(zip(required_headers, cells)))
    return records, findings


def _review_row_anchor(record: dict[str, str]) -> str:
    row_id = _anchor_markup_surface(_fact_value(record, "Review Row ID"))
    match = re.search(
        r"(?<!\\)(?:id=[\"'](?P<html>[^\"']+)[\"']|\{#(?P<attr>[^}]+)\})",
        row_id,
        re.I,
    )
    return (match.group("html") or match.group("attr")) if match else ""


def _reverse_review_row_findings(
    markdown: str,
    fact_map: dict[str, dict[str, Any]],
    coverage_by_id: dict[str, list[dict[str, Any]]],
    manifest: dict[str, Any],
) -> list[str]:
    """Require every visible canonical fact row to resolve back to coverage."""

    findings: list[str] = []
    visible = strip_markdown_comments(markdown)
    message_section = (
        "Message Inventory"
        if bool((manifest.get("core_review_profile") or {}).get("include_message_inventory", True))
        else "Message Coverage Control"
    )
    sections = (
        "Program Set Reading Summary",
        "Calculation Logic",
        "Validation Logic",
        "Exception Handling",
        message_section,
    )
    for section in sections:
        headers = _fact_row_headers(section)
        records, shape_findings = _canonical_review_table_records(
            h2_section_block(visible, section), section, headers
        )
        findings.extend(shape_findings)
        for row_number, record in enumerate(records, start=1):
            row_label = f"{section} canonical fact row {row_number}"
            refs = set(
                re.findall(
                    r"\bSF-[A-Za-z0-9_@#$-]+\b",
                    _visible_inline_text_v04(_fact_value(record, "Source Fact Refs")),
                )
            )
            if not refs:
                findings.append(f"{row_label} requires visible source fact references")
            anchor = _review_row_anchor(record)
            if not anchor:
                findings.append(f"{row_label} requires one visible review anchor")
            elif _anchor_definition_count(markdown, anchor) != 1:
                findings.append(
                    f"{row_label} review anchor {anchor} must be defined exactly once"
                )
            for fact_id in sorted(refs):
                fact = fact_map.get(fact_id)
                if fact is None:
                    findings.append(
                        f"{row_label} references unknown source fact {fact_id}"
                    )
                    continue
                expected_section = _review_section_for_fact(fact, manifest)
                if expected_section != section:
                    findings.append(
                        f"{row_label} maps {fact_id} from {expected_section} into the wrong section"
                    )
                entries = coverage_by_id.get(fact_id, [])
                if len(entries) != 1:
                    findings.append(
                        f"{row_label} source fact {fact_id} must have exactly one coverage item"
                    )
                    continue
                item = entries[0]
                if str(item.get("status") or "") not in {"included", "merged"}:
                    findings.append(
                        f"{row_label} source fact {fact_id} is not included or merged"
                    )
                if not anchor or str(item.get("review_anchor") or "") != anchor:
                    findings.append(
                        f"{row_label} anchor does not match coverage for source fact {fact_id}"
                    )
    return findings


def _unmapped_core_prose_findings(
    markdown: str, manifest: dict[str, Any]
) -> list[str]:
    """Keep deterministic core claims inside mechanically mapped fact rows."""

    visible = strip_markdown_comments(markdown)
    programs = [
        str(entry.get("normalized_name") or "")
        for entry in manifest.get("programs", []) or []
        if entry.get("normalized_name")
    ]
    message_section = (
        "Message Inventory"
        if bool((manifest.get("core_review_profile") or {}).get("include_message_inventory", True))
        else "Message Coverage Control"
    )
    material_action = re.compile(
        r"\b(?:always|whenever|sets?|assigns?|calculates?|derives?|validates?|"
        r"rejects?|returns?|writes?|updates?|persists?|suppresses?|emits?|queues?|"
        r"calls?|invokes?|starts?|runs?|supplies?|yields?|publishes?)\b",
        re.I,
    )
    findings: list[str] = []
    for section in (
        "Calculation Logic",
        "Validation Logic",
        "Exception Handling",
        message_section,
    ):
        block = h2_section_block(visible, section)
        prose_lines: list[str] = []
        for line in block.splitlines():
            surface = _strip_container_prefix_v04(line).strip()
            prose_lines.append(
                surface
                if surface and not surface.startswith(("#", "|"))
                else ""
            )
        for paragraph in re.split(r"\n\s*\n", "\n".join(prose_lines)):
            claim = re.sub(r"\s+", " ", paragraph).strip()
            if not claim or not material_action.search(claim):
                continue
            if not any(_literal_present(claim, program) for program in programs):
                continue
            findings.append(
                f"{section} contains deterministic program prose outside a canonical "
                "source-mapped fact table row"
            )
    return findings


def _required_fact_column_semantics(
    fact: dict[str, Any], review_section: str
) -> list[tuple[str, str, tuple[str, ...]]]:
    """Bind typed source semantics to their canonical reader-facing columns."""

    fact_type = str(fact.get("fact_type") or "")
    if review_section == "Program Set Reading Summary":
        field_headers: dict[str, tuple[str, ...]] = {"program": ("Program",)}
    elif review_section in {"Message Inventory", "Message Coverage Control"}:
        field_headers = {
            "program": ("Program / Routine Sources",),
            "routine": ("Program / Routine Sources",),
            "description": ("Description",),
            "message_type": ("Type",),
            "generic_handler_token": ("Condition / Handler",),
            "occurrences": ("Occurrences",),
            "first_seen": ("Detail Refs",),
            "trigger_handler": ("Condition / Handler",),
            "carrier_destination": ("Carrier / Destination",),
            "effect": ("Effect",),
            "evidence_reference": ("Detail Refs",),
            "evidence_status": ("Evidence Status",),
            "exact_value": ("Message / Status / Literal",),
        }
    else:
        field_headers = {
            "program": ("Program",),
            "routine": ("Routine",),
        }
        if fact_type in {
            "calculation",
            "validation",
            "exception",
            "routine",
            "unresolved_core_statement",
        }:
            field_headers["evidence_status"] = ("Evidence Status",)
        field_headers.update(
            {
                "calculation": ("Calculation / Assignment",),
                "target_carrier": ("Target Field / Carrier",),
                "source_carriers": ("Source Operands / Carriers",),
                "guard": ("Guard / Branch",),
                "effect": ("Effect",),
                "supporting_detail": ("Supporting Detail",),
            }
            if fact_type == "calculation"
            else {}
        )
        field_headers.update(
            {
                "description": ("Description",),
                "validation_type": ("Description", "Supporting Detail"),
                "trigger_chain": ("Condition / Evidence",),
                "carrier_destination": ("Carrier / Destination",),
                "effect": ("Effect",),
            }
            if fact_type == "validation"
            else {}
        )
        field_headers.update(
            {
                "exception_path": ("Exception / Error Path",),
                "guard": ("Detection Mechanism", "Supporting Detail"),
                "detection_mechanism": ("Detection Mechanism",),
                "fields_messages_set": ("Fields / Messages Set",),
                "exception_action": ("Handling Action",),
                "effect": ("Effect",),
                "supporting_detail": ("Supporting Detail",),
            }
            if fact_type == "exception"
            else {}
        )

    exact_headers = {
        "calculation": ("Target Field / Carrier", "Calculation / Assignment"),
        "validation": ("Message / Status / Outcome",),
        "exception": ("Fields / Messages Set", "Exception / Error Path"),
        "routine": ("Routine",),
    }
    if fact_type in exact_headers:
        field_headers["exact_value"] = exact_headers[fact_type]

    required: list[tuple[str, str, tuple[str, ...]]] = []
    for field, headers in field_headers.items():
        value = str(fact.get(field) or "").strip()
        usable_headers = tuple(header for header in headers if header)
        if value and usable_headers:
            required.append((field, value, usable_headers))
    return required


def _mapped_line_word_count(line: str, fact_id: str, exact: str) -> int:
    detail = re.sub(r"<[^>]+>", " ", line).replace(fact_id, " ")
    if exact:
        detail = detail.replace(exact, " ")
    return len(reader_words(detail))


def validate_source_bundle(
    *,
    manifest: dict[str, Any],
    markdown: str,
    source_pack_path: Path,
    core_facts_path: Path,
    coverage_path: Path,
) -> list[str]:
    findings: list[str] = []
    required_paths = (source_pack_path, core_facts_path, coverage_path)
    for path in required_paths:
        if not path.is_file():
            findings.append(f"missing merger control artifact: {path}")
    if findings:
        return findings

    source_pack = source_pack_path.read_text(encoding="utf-8")
    facts_payload = load_yaml(core_facts_path)
    coverage_payload = load_yaml(coverage_path)
    if not isinstance(facts_payload, dict):
        findings.append("core facts artifact is not a YAML mapping")
        return findings
    if not isinstance(coverage_payload, dict):
        findings.append("core coverage artifact is not a YAML mapping")
        return findings
    if str(facts_payload.get("schema_version") or "") != "0.4":
        findings.append("formal review validation requires core facts schema_version 0.4")
    if str(coverage_payload.get("schema_version") or "") != "0.4":
        findings.append("formal review validation requires core coverage schema_version 0.4")

    expected_document_id = str(
        manifest.get("document_id") or manifest.get("review_id") or ""
    )
    for label, payload in (("facts", facts_payload), ("coverage", coverage_payload)):
        actual_document_id = str(
            payload.get("document_id") or payload.get("review_id") or ""
        )
        if actual_document_id != expected_document_id:
            findings.append(
                f"{label} document identity does not match manifest"
            )
    for label, value in (
        ("Document ID", expected_document_id),
        ("Flow Slug", str(manifest.get("flow_slug") or "")),
        ("Program Set Slug", str(manifest.get("program_set_slug") or "")),
    ):
        if not re.search(rf"^{re.escape(label)}:\s*{re.escape(value)}\s*$", source_pack, re.M):
            findings.append(f"source pack {label.lower()} does not match manifest")

    source_facts = [
        fact
        for fact in facts_payload.get("source_facts", []) or []
        if isinstance(fact, dict)
    ]
    fact_ids = [str(fact.get("source_fact_id") or "") for fact in source_facts]
    if not source_facts or any(not fact_id for fact_id in fact_ids):
        findings.append("core facts must contain non-empty source_facts with source_fact_id")
    if len(fact_ids) != len(set(fact_ids)):
        findings.append("core facts contain duplicate source_fact_id values")

    manifest_programs = {
        str(entry.get("normalized_name") or "")
        for entry in manifest.get("programs", []) or []
        if entry.get("normalized_name")
    }
    has_lossless_markers = "<!-- BEGIN LOSSLESS PROGRAM " in source_pack
    if has_lossless_markers:
        for program in manifest_programs:
            begin_count = len(
                re.findall(
                    rf"^<!-- BEGIN LOSSLESS PROGRAM {re.escape(program)}(?::.*?)? -->\s*$",
                    source_pack,
                    re.M,
                )
            )
            end_count = len(
                re.findall(
                    rf"^<!-- END LOSSLESS PROGRAM {re.escape(program)} -->\s*$",
                    source_pack,
                    re.M,
                )
            )
            if begin_count != 1 or end_count != 1:
                findings.append(
                    f"source pack must contain exactly one complete lossless block for {program}"
                )
        expected_source_facts = _extract_source_pack_facts_v04(
            source_pack, sorted(manifest_programs)
        )
        expected_fact_map = {
            str(fact.get("source_fact_id") or ""): fact
            for fact in expected_source_facts
        }
        actual_fact_map = {
            str(fact.get("source_fact_id") or ""): fact for fact in source_facts
        }
        for fact_id in sorted(set(expected_fact_map) - set(actual_fact_map)):
            findings.append(
                f"source-pack fact {fact_id} is missing from normalized core facts"
            )
        for fact_id in sorted(set(actual_fact_map) - set(expected_fact_map)):
            findings.append(
                f"normalized core fact {fact_id} is not derivable from the source pack"
            )
        for fact_id in sorted(set(expected_fact_map) & set(actual_fact_map)):
            if expected_fact_map[fact_id] != actual_fact_map[fact_id]:
                findings.append(
                    f"normalized core fact {fact_id} content differs from the source pack"
                )

    fact_programs = {str(fact.get("program") or "") for fact in source_facts}
    for program in manifest_programs - fact_programs:
        findings.append(f"core facts missing source facts for manifest program {program}")
    for program in manifest_programs:
        program_block = _source_pack_program_block(source_pack, program)
        if not program_block:
            findings.append(f"source pack missing reader-first content for program {program}")
            continue
        for section in (
            "Program Reading Summary",
            "Calculation Logic",
            "Validation Logic",
            "Exception Handling",
            "Message Inventory",
        ):
            if not re.search(rf"^##[#]?\s+{re.escape(section)}\s*$", program_block, re.M):
                findings.append(
                    f"source pack program {program} missing complete reader-first section: {section}"
                )
        for fact in (item for item in source_facts if str(item.get("program") or "") == program):
            exact = str(fact.get("exact_value") or "").strip()
            if (
                exact
                and fact.get("fact_type")
                in {"calculation", "validation", "exception", "message", "routine"}
                and not _literal_present(program_block, exact)
            ):
                findings.append(
                    f"core fact {fact.get('source_fact_id')} exact value is absent from the {program} source-pack block"
                )

    if str(facts_payload.get("schema_version") or "") == "0.4":
        program_fact_entries = [
            entry
            for entry in facts_payload.get("programs", []) or []
            if isinstance(entry, dict)
        ]
        for program in manifest_programs:
            matches = [
                entry
                for entry in program_fact_entries
                if str(entry.get("program") or "") == program
            ]
            if len(matches) != 1:
                findings.append(
                    f"normalized core facts must contain one program inventory for {program}"
                )
                continue
            entry = matches[0]
            expected_ids = {
                str(fact.get("source_fact_id") or "")
                for fact in source_facts
                if str(fact.get("program") or "") == program
            }
            declared_ids = {
                str(value) for value in entry.get("source_fact_ids", []) or []
            }
            nested_payload = entry.get("facts")
            if not isinstance(nested_payload, dict):
                nested_payload = {}
                findings.append(
                    f"normalized core facts program inventory lacks fact buckets for {program}"
                )
            nested_facts = [
                fact
                for bucket in nested_payload.values()
                if isinstance(bucket, list)
                for fact in bucket
                if isinstance(fact, dict)
            ]
            nested_ids = [
                str(fact.get("source_fact_id") or "") for fact in nested_facts
            ]
            if (
                declared_ids != expected_ids
                or set(nested_ids) != expected_ids
                or len(nested_ids) != len(set(nested_ids))
            ):
                findings.append(
                    f"normalized core facts program inventory differs from source_facts for {program}"
                )
            for nested_fact in nested_facts:
                nested_id = str(nested_fact.get("source_fact_id") or "")
                canonical_fact = next(
                    (
                        fact
                        for fact in source_facts
                        if str(fact.get("source_fact_id") or "") == nested_id
                    ),
                    None,
                )
                if canonical_fact is not None and nested_fact != canonical_fact:
                    findings.append(
                        f"normalized core facts nested fact {nested_id} differs "
                        "from source_facts"
                    )

    raw_coverage_items = coverage_payload.get("coverage_items")
    raw_items = coverage_payload.get("items")
    if str(coverage_payload.get("schema_version") or "") == "0.4":
        if not isinstance(raw_coverage_items, list) or not isinstance(raw_items, list):
            findings.append("v0.4 coverage must contain both items and coverage_items")
        elif raw_coverage_items != raw_items:
            findings.append("coverage items and coverage_items mirrors differ")
    items = _coverage_items(coverage_payload)
    by_id: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_id.setdefault(str(item.get("source_fact_id") or ""), []).append(item)
    for fact_id in fact_ids:
        matches = by_id.get(fact_id, [])
        if not matches:
            findings.append(f"source fact {fact_id} is unaccounted in coverage")
        elif len(matches) > 1:
            findings.append(f"source fact {fact_id} has duplicate coverage items")
    for extra in sorted(set(by_id) - set(fact_ids) - {""}):
        findings.append(f"coverage references unknown source fact {extra}")

    allowed = {"included", "merged", "excluded_non_core", "pending"}
    fact_map = {str(fact.get("source_fact_id")): fact for fact in source_facts}
    findings.extend(_validate_overview_evidence(markdown, fact_map, manifest))
    visible_markdown = strip_markdown_comments(markdown)
    anchor_mappings: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for fact_id, entries in by_id.items():
        if not fact_id or len(entries) != 1:
            continue
        item = entries[0]
        status = str(item.get("status") or "")
        fact = fact_map.get(fact_id, {})
        for dimension in ("program", "section", "fact_type"):
            actual_dimension = str(item.get(dimension) or "")
            expected_dimension = str(fact.get(dimension) or "")
            if actual_dimension != expected_dimension:
                findings.append(
                    f"coverage item {fact_id} {dimension} differs from normalized "
                    f"source fact: {actual_dimension!r} != {expected_dimension!r}"
                )
        if status not in allowed:
            findings.append(f"source fact {fact_id} has invalid coverage status {status}")
            continue
        raw_merged_ids = item.get("merged_source_fact_ids", [])
        if raw_merged_ids is None:
            raw_merged_ids = []
        if not isinstance(raw_merged_ids, list):
            findings.append(
                f"source fact {fact_id} merged_source_fact_ids must be a list"
            )
            merged_ids: list[str] = []
        else:
            merged_ids = [str(value) for value in raw_merged_ids]
        if status != "merged" and merged_ids:
            findings.append(
                f"source fact {fact_id} non-merged coverage must not declare "
                "merged_source_fact_ids"
            )
        if status == "pending":
            findings.append(f"source fact {fact_id} remains pending/unaccounted")
            continue
        if status == "excluded_non_core":
            if fact.get("material") is not False or fact.get("fact_type") in {"message", "routine"}:
                findings.append(
                    f"source fact {fact_id} cannot be excluded_non_core because it is material/message/RLOG evidence"
                )
            if not str(item.get("exclusion_reason") or "").strip():
                findings.append(f"source fact {fact_id} excluded_non_core requires exclusion_reason")
            continue
        anchor = str(item.get("review_anchor") or "")
        if not anchor:
            findings.append(f"source fact {fact_id} {status} coverage is missing a review anchor")
        else:
            anchor_mappings.setdefault(anchor, []).append((fact_id, status, item))
        review_section = _review_section_for_fact(fact, manifest)
        section_block = h2_section_block(visible_markdown, review_section)
        mapped_rows = _visible_fact_mapping_rows(
            visible_markdown, review_section, anchor, fact_id
        )
        mapped_texts = [_fact_row_text(record) for record in mapped_rows]
        prose_eligible = str(fact.get("fact_type") or "") in {
            "summary_contribution",
            "thematic_prose",
        }
        mapped_prose = (
            _visible_anchored_prose_lines(
                visible_markdown, review_section, anchor, fact_id
            )
            if prose_eligible
            else []
        )
        mapped_texts.extend(mapped_prose)
        if not section_block:
            findings.append(
                f"final review is missing source section {review_section} for {fact_id}"
            )
        elif not mapped_texts and prose_eligible:
            findings.append(
                f"final review row/anchor for {fact_id} must map to exactly one visible "
                f"required-header data row or reader-useful anchored prose line inside "
                f"{review_section}"
            )
        elif not mapped_rows and not prose_eligible:
            findings.append(
                f"final review row/anchor for {fact_id} must map to exactly one visible "
                f"required-header data row inside {review_section}"
            )
        elif len(mapped_texts) != 1:
            findings.append(
                f"final review must map source fact {fact_id} to exactly one visible "
                "anchored mapping"
            )
        elif all(
            _mapped_line_word_count(
                line, fact_id, str(fact.get("exact_value") or "")
            )
            < 7
            for line in mapped_texts
        ):
            findings.append(
                f"final review row/anchor for {fact_id} is link-only and lacks reader-useful logic"
            )
        required_semantics = (
            _required_fact_semantics(fact)
            if str(facts_payload.get("schema_version") or "") == "0.4"
            else []
        )
        for field, value in required_semantics:
            if not mapped_texts or not any(
                _literal_present(line, value, case_sensitive=False)
                for line in mapped_texts
            ):
                findings.append(
                    f"final review material row for {fact_id} is missing source {field}: {value}"
                )
        if (
            str(fact.get("fact_type") or "")
            in {"summary_contribution", "thematic_prose"}
            and mapped_texts
            and not _summary_semantics_preserved(fact, mapped_texts)
        ):
            findings.append(
                f"final review mapping for {fact_id} does not preserve source "
                "summary semantics"
            )
        if mapped_rows:
            for field, value, destination_headers in _required_fact_column_semantics(
                fact, review_section
            ):
                if not any(
                    any(
                        _literal_present(
                            _fact_value(record, header),
                            value,
                            case_sensitive=False,
                        )
                        for header in destination_headers
                    )
                    for record in mapped_rows
                ):
                    findings.append(
                        f"final review row for {fact_id} is missing source {field}: "
                        f"{value} in canonical column(s) {', '.join(destination_headers)}"
                    )
        elif mapped_prose:
            program = str(fact.get("program") or "").strip()
            if program and not any(
                _literal_present(line, program, case_sensitive=False)
                for line in mapped_prose
            ):
                findings.append(
                    f"final review anchored prose for {fact_id} is missing source "
                    f"program: {program}"
                )
        if status == "merged":
            if not merged_ids:
                findings.append(f"source fact {fact_id} merged coverage lacks merged_source_fact_ids")
            if fact_id in merged_ids:
                findings.append(
                    f"source fact {fact_id} must not self-merge in merged_source_fact_ids"
                )
            if len(merged_ids) != len(set(merged_ids)):
                findings.append(
                    f"source fact {fact_id} has duplicate merged_source_fact_ids"
                )
            for merged_id in merged_ids:
                if merged_id not in fact_map:
                    findings.append(f"source fact {fact_id} merges unknown source fact {merged_id}")
                elif not any(_literal_present(line, merged_id) for line in mapped_texts):
                    findings.append(
                        f"final review merged row for {fact_id} omits {merged_id}"
                    )
                peer_entries = by_id.get(merged_id, [])
                if len(peer_entries) != 1:
                    findings.append(
                        f"source fact {fact_id} merged peer {merged_id} must have "
                        "exactly one coverage item"
                    )
                else:
                    peer = peer_entries[0]
                    if (
                        str(peer.get("status") or "") != "merged"
                        or str(peer.get("review_anchor") or "") != anchor
                    ):
                        findings.append(
                            f"source fact {fact_id} merged peer {merged_id} must be "
                            "merged at the same review anchor"
                        )
        exact = str(fact.get("exact_value") or "").strip()
        exact_fact_types = {"calculation", "validation", "exception", "message", "routine"}
        if fact.get("fact_type") in exact_fact_types and exact and not any(
            _literal_present(line, exact) and fact_id in line for line in mapped_texts
        ):
            findings.append(
                f"final review material row for {fact_id} is missing exact value {exact}"
            )

    for anchor, mappings in anchor_mappings.items():
        definition_count = _anchor_definition_count(markdown, anchor)
        if definition_count != 1:
            findings.append(
                f"coverage anchor {anchor} must be defined exactly once; found {definition_count}"
            )
        if len(mappings) <= 1:
            continue
        ids = {fact_id for fact_id, _status, _item in mappings}
        if any(status != "merged" for _fact_id, status, _item in mappings):
            findings.append(
                f"coverage anchor {anchor} is reused by non-merged source facts"
            )
            continue
        for fact_id, _status, item in mappings:
            declared_group = {
                str(value)
                for value in item.get("merged_source_fact_ids", []) or []
            }
            expected_group = ids - {fact_id}
            if declared_group != expected_group:
                findings.append(
                    f"coverage anchor {anchor} merged group for {fact_id} must declare "
                    "exactly every other source fact mapped to that anchor"
                )

    findings.extend(
        _reverse_review_row_findings(markdown, fact_map, by_id, manifest)
    )
    findings.extend(_unmapped_core_prose_findings(markdown, manifest))

    counts = coverage_payload.get("coverage_counts") or {}
    expected_total = len(source_facts)
    actual_accounted = sum(
        1
        for item in items
        if str(item.get("status") or "") in {"included", "merged", "excluded_non_core"}
    )
    actual_pending = sum(
        1 for item in items if str(item.get("status") or "") == "pending"
    )
    for key, expected in (
        ("total_source_facts", expected_total),
        ("accounted_source_facts", actual_accounted),
        ("pending_source_facts", actual_pending),
    ):
        if counts.get(key) != expected:
            findings.append(
                f"coverage count mismatch for {key}: declared {counts.get(key)}, actual {expected}"
            )
    by_program: dict[str, int] = {}
    by_section: dict[str, int] = {}
    routine_rlog: dict[str, int] = {}
    for fact in source_facts:
        program = str(fact.get("program") or "")
        section = str(fact.get("section") or "")
        by_program[program] = by_program.get(program, 0) + 1
        by_section[section] = by_section.get(section, 0) + 1
        if fact.get("fact_type") == "routine":
            routine_rlog[program] = routine_rlog.get(program, 0) + 1
    declared_by_program = counts.get("by_program")
    if not isinstance(declared_by_program, dict):
        findings.append("coverage counts missing required by_program mapping")
    elif declared_by_program != by_program:
        findings.append("coverage count mismatch for by_program")
    declared_by_section = counts.get("by_section")
    if not isinstance(declared_by_section, dict):
        findings.append("coverage counts missing required by_section mapping")
    elif declared_by_section != by_section:
        findings.append("coverage count mismatch for by_section")
    declared_routine_rlog = counts.get("routine_rlog")
    if not isinstance(declared_routine_rlog, dict):
        findings.append("coverage counts missing required routine_rlog mapping")
    elif declared_routine_rlog != routine_rlog:
        findings.append("coverage count mismatch for routine_rlog")

    if str(coverage_payload.get("review_status") or "") != "complete_exploratory":
        findings.append("coverage review_status must be complete_exploratory")
    if str(coverage_payload.get("schema_version") or "") == "0.4":
        if coverage_payload.get("allowed_statuses") != [
            "included",
            "merged",
            "excluded_non_core",
            "pending",
        ]:
            findings.append("coverage allowed_statuses must match the v0.4 contract")
        if str(coverage_payload.get("coverage_status") or "") != "complete":
            findings.append("coverage coverage_status must be complete")
        if coverage_payload.get("expected_source_fact_count") != expected_total:
            findings.append("coverage expected_source_fact_count mismatch")
        if coverage_payload.get("coverage_item_count") != len(items):
            findings.append("coverage coverage_item_count mismatch")
        actual_status_counts = {
            status: sum(
                1 for item in items if str(item.get("status") or "") == status
            )
            for status in ("included", "merged", "excluded_non_core", "pending")
        }
        if coverage_payload.get("status_counts") != actual_status_counts:
            findings.append("coverage status_counts mismatch")
    return findings


def validate(
    manifest_path: Path,
    review_path: Path,
    source_pack_path: Path | None = None,
    core_facts_path: Path | None = None,
    coverage_path: Path | None = None,
) -> list[str]:
    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        return ["manifest is not a YAML mapping"]
    findings = validate_manifest(manifest)
    findings.extend(validate_program_list_snapshot(manifest_path, manifest))
    if manifest.get("review_status") == REVIEW_STATUS_PARTIAL:
        findings.append("formal review is blocked by artifact readiness")
    if not review_path.is_file():
        findings.append(f"missing review artifact: {review_path}")
        return findings
    if manifest.get("review_status") != "complete_exploratory":
        findings.append(
            "formal review validation requires manifest review_status complete_exploratory"
        )
    if manifest.get("artifact_readiness") != "ready":
        findings.append(
            "formal review validation requires manifest artifact_readiness ready"
        )
    if manifest.get("merge_coverage") != "complete":
        findings.append(
            "formal review validation requires manifest merge_coverage complete"
        )
    expected_name = str(manifest.get("canonical_filename") or "")
    folder_slug = str(manifest.get("folder_slug") or "")
    manifest_resolved = manifest_path.resolve(strict=False)
    review_resolved = review_path.resolve(strict=False)
    if manifest_path.name != MANIFEST_FILENAME:
        findings.append(f"manifest filename must be {MANIFEST_FILENAME}")
    if manifest_resolved.parent.name != folder_slug:
        findings.append(
            "manifest parent directory must match the flow/program-set folder_slug"
        )
    if review_resolved.parent != manifest_resolved.parent:
        findings.append("review and manifest must be canonical sibling artifacts")
    if review_path.name != expected_name:
        findings.append(
            f"review filename must match manifest canonical_filename {expected_name}"
        )
    markdown = review_path.read_text(encoding="utf-8")
    findings.extend(validate_review_identity(markdown, manifest))
    findings.extend(validate_review(markdown, manifest))
    bundle_dir = manifest_path.parent
    resolved_source_pack_path = source_pack_path or bundle_dir / SOURCE_PACK_FILENAME
    resolved_core_facts_path = core_facts_path or bundle_dir / CORE_FACTS_FILENAME
    resolved_coverage_path = coverage_path or bundle_dir / CORE_COVERAGE_FILENAME
    for label, path, expected_basename in (
        ("source pack", resolved_source_pack_path, SOURCE_PACK_FILENAME),
        ("core facts", resolved_core_facts_path, CORE_FACTS_FILENAME),
        ("core coverage", resolved_coverage_path, CORE_COVERAGE_FILENAME),
    ):
        resolved = path.resolve(strict=False)
        if path.name != expected_basename or resolved.parent != manifest_resolved.parent:
            findings.append(
                f"{label} must be the canonical sibling artifact {expected_basename}"
            )
    if manifest.get("review_status") == "complete_exploratory":
        if str(manifest.get("schema_version") or "") != "0.4":
            findings.append(
                "formal review validation requires manifest schema_version 0.4"
            )
        else:
            readiness_findings, trusted_manifest, artifact_root = (
                revalidate_manifest_program_inputs(manifest)
            )
            findings.extend(readiness_findings)
            if trusted_manifest is not None and artifact_root is not None:
                findings.extend(
                    validate_prepared_bundle_integrity(
                        manifest=trusted_manifest,
                        artifact_root=artifact_root,
                        source_pack_path=resolved_source_pack_path,
                        core_facts_path=resolved_core_facts_path,
                    )
                )
    findings.extend(
        validate_source_bundle(
            manifest=manifest,
            markdown=markdown,
            source_pack_path=resolved_source_pack_path,
            core_facts_path=resolved_core_facts_path,
            coverage_path=resolved_coverage_path,
        )
    )
    return findings


def build_command(args: argparse.Namespace) -> int:
    config = load_yaml(args.profile)
    if not isinstance(config, dict):
        raise SystemExit("delivery profile must be a YAML mapping")
    if args.programs_file is not None:
        try:
            programs = read_programs_file(args.programs_file)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise SystemExit(f"cannot read programs file {args.programs_file}: {exc}") from None
    else:
        programs = [str(program).strip() for program in (args.programs or []) if str(program).strip()]
    if not programs:
        raise SystemExit("program input has no program names")
    if args.force_rescan_file is not None:
        raise SystemExit(
            "--force-rescan-file is no longer supported for program-flow core review. "
            "Use --artifact-repo-mode current_run explicitly when analyzing the program in the current run."
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
    if args.project_root is not None:
        if not args.project_root.is_dir():
            raise SystemExit(f"project root not found or not a directory: {args.project_root}")
        output_dir = args.project_root / "outputs"
    else:
        output_dir = args.output_dir
    try:
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
            core_review_profile=args.core_review_profile,
            review_id=args.review_id,
            flow_slug=args.flow_slug,
            program_set_slug=args.program_set_slug,
            programs_file=args.programs_file,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    manifest_path, review_path = write_build_outputs(manifest, output_dir)
    layout = resolve_output_layout(output_dir, manifest)
    print(f"Prepared {manifest_path}")
    print(f"Reserved final LLM review path {review_path}")
    print(f"OUTPUT_DIR={layout.folder_dir}")
    return 0


def validate_command(args: argparse.Namespace) -> int:
    findings = validate(
        args.manifest,
        args.review,
        args.source_pack,
        args.core_facts,
        args.coverage,
    )
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    print("OK: program-set SME core review contract passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser(
        "build", help="Validate inputs and prepare the reader-first synthesis bundle"
    )
    build.add_argument("--review-name", required=True)
    program_input = build.add_mutually_exclusive_group(required=True)
    program_input.add_argument(
        "--programs-file",
        type=Path,
        help="External program list (.txt or CSV); retained for backward compatibility",
    )
    program_input.add_argument(
        "--program",
        dest="programs",
        action="append",
        metavar="PROGRAM",
        help="Program in SME navigation order; repeat once per program",
    )
    build.add_argument("--working-root", type=Path, help="Delivery working checkout, approved document repo clone, or artifact root")
    build.add_argument("--output-root", type=Path, help="Alias for artifact root")
    build.add_argument(
        "--artifact-repo-mode",
        choices=[ARTIFACT_REPO_CURRENT_RUN, ARTIFACT_REPO_APPROVED_DOCUMENT],
        default=DEFAULT_ARTIFACT_REPO_MODE,
        help=(
            "Use approved_document_repo by default when --working-root is a local clone "
            "containing SME-reviewed artifacts. Pass current_run explicitly for active "
            "scan branches."
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
            "program-evidence first and approved-document-repo based. For an active scan "
            "branch, pass --artifact-repo-mode current_run explicitly."
        ),
    )
    build.add_argument("--profile", type=Path, required=True)
    output_location = build.add_mutually_exclusive_group(required=True)
    output_location.add_argument(
        "--project-root",
        type=Path,
        help="Delivery project root; writes the stable review bundle under <project-root>/outputs/",
    )
    output_location.add_argument(
        "--output-dir",
        type=Path,
        help="Explicit output parent; the stable flow/program-set folder is appended once",
    )
    build.add_argument("--working-branch")
    build.add_argument(
        "--core-review-profile",
        choices=[CORE_REVIEW_PROFILE_DEFAULT, CORE_REVIEW_PROFILE_MINIMAL],
        help="Select standard_reader_first (default) or minimal_reader_first.",
    )
    build.add_argument("--review-id")
    build.add_argument("--flow-slug")
    build.add_argument("--program-set-slug")
    build.set_defaults(func=build_command)

    validate_parser = subparsers.add_parser("validate", help="Validate a completed review")
    validate_parser.add_argument("--manifest", type=Path, required=True)
    validate_parser.add_argument("--review", type=Path, required=True)
    validate_parser.add_argument("--source-pack", type=Path)
    validate_parser.add_argument("--core-facts", type=Path)
    validate_parser.add_argument("--coverage", type=Path)
    validate_parser.set_defaults(func=validate_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
