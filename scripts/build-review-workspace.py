#!/usr/bin/env python3
"""Build a human-review workspace from Legacy Spec Factory artifacts.

The review workspace is a derived read model that turns reverse-engineering
artifacts into queueable "review items" for humans. It is intentionally
evidence-first: every item must cite artifacts and evidence IDs, and blocked or
SME-dependent items are surfaced before already-approved content.

Usage:
  python3 scripts/build-review-workspace.py docs/<project-name>/
  python3 scripts/build-review-workspace.py docs/<project-name>/workflow-state.yaml

Outputs:
  docs/<project>/08_review_workspace/review-items.json
  docs/<project>/08_review_workspace/index.html

Optional manual input:
  docs/<project>/08_review_workspace/review-items.manual.yaml

Dependencies:
  - PyYAML
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


STATUS_ORDER = [
    "blocked",
    "contradicted",
    "needs_sme_review",
    "needs_review",
    "ready_to_approve",
    "approved",
    "deferred",
]

STATUS_GROUPS = {
    "blocked": "Must Resolve",
    "contradicted": "Must Resolve",
    "needs_sme_review": "Needs SME",
    "needs_review": "Needs Review",
    "ready_to_approve": "Ready To Approve",
    "approved": "Closed",
    "deferred": "Closed",
}

VALID_ACTIONS = {
    "mark_blocked",
    "route_to_sme",
    "request_more_evidence",
    "approve",
    "defer",
    "reopen",
}


@dataclass
class ArtifactSet:
    root: Path
    spec_path: Path
    traceability_path: Path | None
    module_overview_path: Path | None
    flow_paths: list[Path]
    program_paths: list[Path]
    evidence_manifest_path: Path | None


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat") and value.__class__.__name__ in {"date", "datetime"}:
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def rel_to(root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    return path.relative_to(root).as_posix()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Project directory or workflow-state.yaml path")
    return parser.parse_args()


def resolve_project_root(project_arg: str) -> Path:
    path = Path(project_arg).resolve()
    if path.is_file():
        if path.name != "workflow-state.yaml":
            raise SystemExit(f"Expected workflow-state.yaml, got: {path}")
        return path.parent
    return path


def git_commit(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def load_artifacts(project_root: Path) -> ArtifactSet:
    spec_paths = sorted(project_root.glob("05_specs/*/spec.yaml"))
    if not spec_paths:
        raise SystemExit(f"No spec.yaml found under {project_root}/05_specs")
    spec_path = spec_paths[0]
    cap_dir = spec_path.parent
    spec = load_yaml(spec_path).get("spec") or {}
    source_artifacts = spec.get("source_artifacts") or {}

    traceability_path = cap_dir / "traceability.md"
    if not traceability_path.exists():
        traceability_path = None

    module_overview_path = None
    module_rel = source_artifacts.get("module_overview")
    if module_rel:
        candidate = project_root / module_rel
        if candidate.exists():
            module_overview_path = candidate

    flow_paths: list[Path] = []
    for flow_rel in source_artifacts.get("flows") or []:
        candidate = project_root / flow_rel
        if candidate.exists():
            flow_paths.append(candidate)

    program_paths: list[Path] = []
    for program_rel in source_artifacts.get("programs") or []:
        candidate = project_root / program_rel
        if candidate.exists():
            program_paths.append(candidate)

    evidence_manifest_path = None
    manifest_rel = source_artifacts.get("evidence_manifest")
    if manifest_rel:
        candidate = project_root / manifest_rel
        if candidate.exists():
            evidence_manifest_path = candidate

    return ArtifactSet(
        root=project_root,
        spec_path=spec_path,
        traceability_path=traceability_path,
        module_overview_path=module_overview_path,
        flow_paths=flow_paths,
        program_paths=program_paths,
        evidence_manifest_path=evidence_manifest_path,
    )


def section_map(text: str) -> dict[str, str]:
    pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[match.group(1).strip()] = text[start:end].strip()
    return sections


def parse_markdown_table(block: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    tables: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("|"):
            current.append(line)
        elif current:
            tables.extend([current])
            current = []
    if current:
        tables.extend([current])
    if not tables:
        return []
    table = tables[0]
    if len(table) < 2:
        return []
    headers = [cell.strip() for cell in table[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for raw in table[2:]:
        cells = [cell.strip() for cell in raw.strip("|").split("|")]
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        rows.append(dict(zip(headers, cells)))
    return rows


def parse_checklist_items(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def split_ids(value: str) -> list[str]:
    ids = re.findall(r"\b[A-Z]{2,}-[A-Z0-9-]+\b", value or "")
    return ids


def status_from_review_status(review_status: str | None, has_blocker: bool = False) -> str:
    if has_blocker:
        return "blocked"
    normalized = (review_status or "").strip().lower()
    if normalized == "approved":
        return "approved"
    if normalized == "approved_with_non_blocking_tbd":
        return "ready_to_approve"
    if normalized in {"needs_sme_review", "in_review"}:
        return "needs_sme_review"
    if normalized in {"draft", "blocked_pending_source", "blocked_pending_sme"}:
        return "needs_review"
    return "needs_review"


def action_for_status(status: str) -> str:
    return {
        "blocked": "mark_blocked",
        "contradicted": "route_to_sme",
        "needs_sme_review": "route_to_sme",
        "needs_review": "request_more_evidence",
        "ready_to_approve": "approve",
        "approved": "approve",
        "deferred": "defer",
    }[status]


def confidence_for_status(status: str, evidence_count: int) -> str:
    if status == "approved":
        return "confirmed"
    if evidence_count >= 2:
        return "high"
    if evidence_count == 1:
        return "medium"
    return "low"


def decision_basis(evidence_ids: list[str], evidence_index: dict[str, dict[str, Any]]) -> str:
    types = {str((evidence_index.get(ev_id) or {}).get("type", "unknown")) for ev_id in evidence_ids}
    if {"source", "sme_note"} <= types:
        return "source_plus_sme"
    if {"source", "runtime"} <= types:
        return "source_plus_runtime"
    if {"source", "runtime", "sme_note"} <= types:
        return "source_runtime_sme"
    if "sme_note" in types and len(types) == 1:
        return "runtime_plus_sme" if "runtime" in types else "source_plus_sme"
    if "source" in types:
        return "source_only"
    if "runtime" in types:
        return "runtime_only"
    return "source_only"


TEXT_EXTS = {".md", ".yaml", ".yml", ".json", ".txt", ".csv"}
MAX_EXCERPT_LINES = 40


def extract_evidence_excerpt(rel_path: str | None, project_root: Path, max_lines: int = MAX_EXCERPT_LINES) -> dict[str, Any]:
    """Read a evidence file and return a preview excerpt with metadata."""
    if not rel_path:
        return {"available": False, "reason": "no path recorded", "lines": [], "truncated": False}
    file_path = project_root / rel_path
    if not file_path.exists():
        return {"available": False, "reason": f"file not found ({rel_path})", "lines": [], "truncated": False}

    try:
        raw_lines = file_path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return {"available": False, "reason": f"read error: {exc}", "lines": [], "truncated": False}

    ext = file_path.suffix.lower()
    is_text = ext in TEXT_EXTS
    truncated = len(raw_lines) > max_lines
    lines = raw_lines[:max_lines]
    return {
        "available": True,
        "is_text": is_text,
        "file_type": ext.lstrip(".") or "unknown",
        "total_lines": len(raw_lines),
        "lines": lines,
        "truncated": truncated,
        "truncated_note": f"... {len(raw_lines) - max_lines} more lines" if truncated else "",
    }


def evidence_cards(
    evidence_ids: list[str],
    evidence_index: dict[str, dict[str, Any]],
    supports: str,
    project_root: Path,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for ev_id in evidence_ids:
        meta = evidence_index.get(ev_id, {})
        rel_path = meta.get("relative_path") or meta.get("source_path")
        excerpt_info = extract_evidence_excerpt(rel_path, project_root)
        cards.append(
            {
                "id": ev_id,
                "type": meta.get("type", "unknown"),
                "title": meta.get("member") or meta.get("note") or ev_id,
                "supports": supports,
                "source": rel_path or "source not indexed",
                "strength": meta.get("strength", "approved_evidence"),
                "artifact_path": rel_path,
                "approval": (meta.get("sme_approval") or {}).get("decision"),
                "excerpt": excerpt_info,
            }
        )
    return cards


def load_evidence_index(manifest_path: Path | None) -> dict[str, dict[str, Any]]:
    if manifest_path is None:
        return {}
    manifest = load_yaml(manifest_path)
    index: dict[str, dict[str, Any]] = {}
    for item in manifest.get("items") or []:
        item = dict(item)
        if item.get("type") == "spool_or_report":
            item["type"] = "runtime"
        index[item["evidence_id"]] = item
    return index


def rule_question(title: str, statement: str) -> str:
    lower = f"{title} {statement}".lower()
    if "formula" in lower or "round" in lower:
        return "Should the pricing formula, discount order, and rounding behavior be accepted as the legacy truth?"
    if "promo" in lower or "silent" in lower:
        return "How should promo code handling behave, and is the silent fallback intentional?"
    return f'Should the legacy rule "{title}" be accepted as stated?'


def error_question(condition: str) -> str:
    return f"How should the legacy system behave when {condition}?"


def normalize_conclusion(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def evidence_basis_text(evidence_ids: list[str], evidence_index: dict[str, dict[str, Any]]) -> str:
    if not evidence_ids:
        return "No evidence ID is linked yet; reviewer must request stronger evidence before approval."
    pieces: list[str] = []
    for ev_id in evidence_ids:
        meta = evidence_index.get(ev_id) or {}
        ev_type = meta.get("type", "unknown")
        title = meta.get("member") or meta.get("note") or meta.get("relative_path") or meta.get("source_path") or ev_id
        approval = (meta.get("sme_approval") or {}).get("decision")
        suffix = f", {approval}" if approval else ""
        pieces.append(f"{ev_id}: {ev_type} evidence ({title}{suffix})")
    return "; ".join(pieces)


def evidence_basis_from_cards(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "No evidence cards recorded yet; reviewer must request stronger evidence before approval."
    pieces: list[str] = []
    for card in cards:
        title = card.get("title") or card.get("source") or card.get("id") or "evidence"
        ev_type = card.get("type", "unknown")
        approval = card.get("approval")
        suffix = f", {approval}" if approval else ""
        pieces.append(f"{card.get('id', 'EV-UNKNOWN')}: {ev_type} evidence ({title}{suffix})")
    return "; ".join(pieces)


def rule_business_signal(rule: dict[str, Any]) -> str:
    explicit = rule.get("business_signal")
    if explicit:
        return normalize_conclusion(str(explicit))
    title = rule.get("title") or rule.get("id") or "Business rule"
    statement = normalize_conclusion(rule.get("statement", ""))
    if statement:
        return f"{title}: {statement}"
    return str(title)


def default_sme_questions(rule_id: str, acceptance: list[str], has_trace_row: bool, conclusion: str) -> list[str]:
    questions = [
        f"Does {rule_id} describe the business behavior SMEs expect users or operations to rely on?",
        "Is the evidence basis sufficient to promote this conclusion downstream?",
    ]
    if not acceptance:
        questions.append("What observable scenario would prove this behavior is preserved?")
    if not has_trace_row:
        questions.append("Which source or runtime evidence should be linked before approval?")
    if "silent" in conclusion.lower():
        questions.append("Is silent fallback intentional business behavior, historical tolerance, or a defect to redesign?")
    return questions


def ensure_review_item_review_fields(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in items:
        item.setdefault(
            "business_signal",
            item.get("question") or item.get("current_conclusion") or "No business signal recorded.",
        )
        item.setdefault("evidence_basis", evidence_basis_from_cards(item.get("evidence") or []))
        item.setdefault(
            "sme_questions",
            item.get("sub_questions") or [item.get("question") or "What should the SME decide?"],
        )
    return items


def parse_traceability_rows(traceability_path: Path | None) -> tuple[dict[str, dict[str, str]], list[str]]:
    if traceability_path is None:
        return {}, []
    sections = section_map(read_text(traceability_path))
    rows = parse_markdown_table(sections.get("Rule → Evidence → Test", ""))
    indexed = {row.get("Rule ID", ""): row for row in rows if row.get("Rule ID")}
    coverage_notes = parse_checklist_items(sections.get("Coverage check", ""))
    return indexed, coverage_notes


def parse_program_support(program_paths: list[Path]) -> dict[str, dict[str, list[str]]]:
    support: dict[str, dict[str, list[str]]] = {
        "error_conditions": defaultdict(list),
        "open_questions": defaultdict(list),
    }
    for path in program_paths:
        sections = section_map(read_text(path))
        error_rows = parse_markdown_table(sections.get("Error Handling", ""))
        for row in error_rows:
            support["error_conditions"][row.get("Condition", "")].append(path.relative_to(path.parents[3]).as_posix())
        question_rows = parse_markdown_table(sections.get("Open Questions", ""))
        for row in question_rows:
            question = row.get("Question", "")
            resolution = (row.get("Resolution") or "").lower()
            if "resolved" in resolution:
                continue
            support["open_questions"][question].append(path.relative_to(path.parents[3]).as_posix())
    return support


def parse_flow_support(flow_paths: list[Path]) -> dict[str, Any]:
    support: dict[str, Any] = {"open_questions": [], "review_statuses": {}}
    for path in flow_paths:
        text = read_text(path)
        sections = section_map(text)
        support["review_statuses"][path.relative_to(path.parents[2]).as_posix()] = extract_metadata_value(
            sections.get("Metadata", ""), "review_status"
        )
        open_questions = sections.get("Open Questions", "")
        if open_questions and "(none" not in open_questions.lower():
            support["open_questions"].append(
                {
                    "artifact": path.relative_to(path.parents[2]).as_posix(),
                    "question": normalize_conclusion(open_questions),
                }
            )
    return support


def extract_metadata_value(block: str, key: str) -> str | None:
    pattern = re.compile(rf"-\s+{re.escape(key)}:\s*(.+)")
    match = pattern.search(block)
    if match:
        return match.group(1).strip()
    return None


def build_rule_items(
    artifacts: ArtifactSet,
    spec: dict[str, Any],
    evidence_index: dict[str, dict[str, Any]],
    trace_rows: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    capability_id = spec["capability_id"]
    spec_rel = rel_to(artifacts.root, artifacts.spec_path) or artifacts.spec_path.as_posix()
    trace_rel = rel_to(artifacts.root, artifacts.traceability_path)

    ordinal = 1
    for rule in spec.get("rules") or []:
        rule_id = rule["id"]
        review_status = rule.get("review_status")
        status = status_from_review_status(review_status, has_blocker=not bool(rule.get("evidence_ids")))
        trace_row = trace_rows.get(rule_id, {})
        question = rule_question(rule.get("title", rule_id), rule.get("statement", ""))
        evidence_ids = list(rule.get("evidence_ids") or [])
        conclusion = normalize_conclusion(rule.get("statement", ""))
        acceptance = list(rule.get("acceptance_criteria") or [])
        gaps: list[str] = []
        if not acceptance:
            gaps.append(f"{rule_id} has no acceptance criteria in spec.yaml.")
        if not trace_row:
            gaps.append(f"{rule_id} is missing a Rule → Evidence → Test trace row.")
        sub_questions = [
            f"Does evidence support {rule_id} exactly as written?",
            "Are the acceptance criteria specific enough to verify the legacy behavior?",
        ]
        if "silent" in conclusion.lower():
            sub_questions.append("Is the silent fallback an intentional business rule or a defensive implementation detail?")
        sme_questions = list(rule.get("sme_questions") or []) or default_sme_questions(
            rule_id,
            acceptance,
            bool(trace_row),
            conclusion,
        )
        items.append(
            {
                "id": f"RI-{capability_id}-{ordinal:03d}",
                "capability_id": capability_id,
                "type": "rule_review",
                "theme": rule.get("title", rule_id),
                "question": question,
                "sub_questions": sub_questions,
                "status": status,
                "priority": "high" if review_status != "approved" else "medium",
                "confidence": confidence_for_status(status, len(evidence_ids)),
                "decision_basis": decision_basis(evidence_ids, evidence_index),
                "business_signal": rule_business_signal(rule),
                "evidence_basis": rule.get("evidence_basis")
                or evidence_basis_text(evidence_ids, evidence_index),
                "sme_questions": sme_questions,
                "current_conclusion": conclusion,
                "evidence": evidence_cards(evidence_ids, evidence_index, rule.get("title", rule_id), artifacts.root),
                "contradictions": [],
                "gaps": gaps,
                "impacts": [rule_id],
                "review_action": action_for_status(status),
                "source_artifacts": [spec_rel] + ([trace_rel] if trace_rel else []),
                "source_excerpt": {
                    "trace_row": trace_row.get("Source artifact rows", ""),
                    "acceptance_tests": trace_row.get("Acceptance test", ""),
                },
                "updated_at": iso_now(),
            }
        )
        ordinal += 1

    for error in spec.get("error_conditions") or []:
        error_id = error["id"]
        evidence_ids = split_ids(error.get("legacy_behavior", "")) or [
            ev_id
            for rule in spec.get("rules") or []
            for ev_id in (rule.get("evidence_ids") or [])
            if ev_id.startswith("EV-")
        ][:1]
        status = "approved" if error.get("acceptance_criteria") else "needs_review"
        items.append(
            {
                "id": f"RI-{capability_id}-{ordinal:03d}",
                "capability_id": capability_id,
                "type": "error_behavior_review",
                "theme": error_id,
                "question": error_question(error.get("condition", error_id)),
                "sub_questions": [
                    "Is the returned status or error outcome explicit enough for downstream implementation?",
                    "Is there enough evidence to preserve this failure behavior without reinterpretation?",
                ],
                "status": status,
                "priority": "high",
                "confidence": confidence_for_status(status, len(evidence_ids)),
                "decision_basis": decision_basis(evidence_ids, evidence_index),
                "business_signal": f"Failure behavior for {error.get('condition', error_id)}",
                "evidence_basis": evidence_basis_text(evidence_ids, evidence_index),
                "sme_questions": [
                    "Should this failure behavior be preserved exactly in the modern system?",
                    "Who owns the business decision when this condition occurs?",
                ],
                "current_conclusion": normalize_conclusion(error.get("legacy_behavior", "")),
                "evidence": evidence_cards(evidence_ids, evidence_index, error.get("condition", error_id), artifacts.root),
                "contradictions": [],
                "gaps": [] if error.get("acceptance_criteria") else [f"{error_id} has no acceptance criteria."],
                "impacts": [error_id],
                "review_action": action_for_status(status),
                "source_artifacts": [spec_rel],
                "source_excerpt": {
                    "acceptance_criteria": "; ".join(error.get("acceptance_criteria") or []),
                },
                "updated_at": iso_now(),
            }
        )
        ordinal += 1
    return items


def build_traceability_item(
    artifacts: ArtifactSet,
    spec: dict[str, Any],
    evidence_index: dict[str, dict[str, Any]],
    coverage_notes: list[str],
    trace_rows: dict[str, dict[str, str]],
) -> dict[str, Any]:
    capability_id = spec["capability_id"]
    trace_rel = rel_to(artifacts.root, artifacts.traceability_path) or "05_specs/.../traceability.md"
    negative_markers = ("✗", "missing", "blocked", "fail", "warning", "orphan", "gap", "uncovered")
    gaps = [note for note in coverage_notes if any(marker in note.lower() for marker in negative_markers)]
    status = "approved" if not gaps else "needs_review"
    all_evidence = sorted({ev for row in trace_rows.values() for ev in split_ids(row.get("Evidence", ""))})
    return {
        "id": f"RI-{capability_id}-900",
        "capability_id": capability_id,
        "type": "traceability_review",
        "theme": "Traceability coverage",
        "question": "Is every approved rule traceable to evidence and a reviewable verification path?",
        "sub_questions": [
            "Does each approved rule have at least one evidence link?",
            "Does each approved rule point to a verification path reviewers can audit?",
            "Are there any open coverage gaps or orphaned references?",
        ],
        "status": status,
        "priority": "high",
        "confidence": confidence_for_status(status, len(all_evidence)),
        "decision_basis": decision_basis(all_evidence, evidence_index),
        "business_signal": "Approved rules have complete evidence and verification coverage.",
        "evidence_basis": evidence_basis_text(all_evidence, evidence_index),
        "sme_questions": [
            "Can reviewers follow each approved rule from business conclusion to evidence and verification?",
            "Are any evidence links too technical or ambiguous for SME review?",
        ],
        "current_conclusion": "Coverage checks in traceability.md are complete." if not gaps else "Traceability coverage has unresolved gaps.",
        "evidence": evidence_cards(all_evidence, evidence_index, "Traceability coverage", artifacts.root),
        "contradictions": [],
        "gaps": gaps,
        "impacts": [row_id for row_id in trace_rows.keys()],
        "review_action": action_for_status(status),
        "source_artifacts": [trace_rel],
        "source_excerpt": {"coverage_check": " | ".join(coverage_notes)},
        "updated_at": iso_now(),
    }


def build_open_question_items(
    artifacts: ArtifactSet,
    spec: dict[str, Any],
    evidence_index: dict[str, dict[str, Any]],
    program_support: dict[str, dict[str, list[str]]],
    flow_support: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    capability_id = spec["capability_id"]
    ordinal = 950

    for tbd in spec.get("open_tbds") or []:
        ordinal += 1
        items.append(
            {
                "id": f"RI-{capability_id}-{ordinal}",
                "capability_id": capability_id,
                "type": "open_question_review",
                "theme": tbd.get("id", "Open TBD"),
                "question": tbd.get("question") or f"What decision is required for {tbd.get('id', 'this TBD')}?",
                "sub_questions": ["What evidence is still missing?", "Who owns the next decision?"],
                "status": "needs_sme_review" if not tbd.get("blocking") else "blocked",
                "priority": "high",
                "confidence": "low",
                "decision_basis": "source_only",
                "business_signal": tbd.get("question") or "An unresolved business decision blocks or qualifies downstream use.",
                "evidence_basis": "Open TBD recorded in spec.yaml; no approving evidence is linked yet.",
                "sme_questions": [tbd.get("question", "What decision should the SME make?")],
                "current_conclusion": tbd.get("resolution") or "Open question remains unresolved.",
                "evidence": [],
                "contradictions": [],
                "gaps": [tbd.get("question", "Unresolved TBD")],
                "impacts": [tbd.get("id")] if tbd.get("id") else [],
                "review_action": "mark_blocked" if tbd.get("blocking") else "route_to_sme",
                "source_artifacts": [rel_to(artifacts.root, artifacts.spec_path) or artifacts.spec_path.as_posix()],
                "source_excerpt": {"owner": tbd.get("owner", "")},
                "updated_at": iso_now(),
            }
        )

    for question, sources in program_support.get("open_questions", {}).items():
        if "resolved" in question.lower():
            continue
        ordinal += 1
        items.append(
            {
                "id": f"RI-{capability_id}-{ordinal}",
                "capability_id": capability_id,
                "type": "open_question_review",
                "theme": "Program open question",
                "question": question,
                "sub_questions": ["Does source code answer this already?", "Is SME confirmation still required?"],
                "status": "needs_sme_review",
                "priority": "medium",
                "confidence": "low",
                "decision_basis": "source_plus_sme",
                "business_signal": "Program analysis found a question that still affects business interpretation.",
                "evidence_basis": "Open question came from program analysis; source artifacts are listed for reviewer follow-up.",
                "sme_questions": [question],
                "current_conclusion": "Program analysis still requires explicit review resolution.",
                "evidence": [],
                "contradictions": [],
                "gaps": [question],
                "impacts": [],
                "review_action": "route_to_sme",
                "source_artifacts": sources,
                "source_excerpt": {},
                "updated_at": iso_now(),
            }
        )

    for item in flow_support.get("open_questions", []):
        ordinal += 1
        items.append(
            {
                "id": f"RI-{capability_id}-{ordinal}",
                "capability_id": capability_id,
                "type": "open_question_review",
                "theme": "Flow open question",
                "question": item["question"],
                "sub_questions": ["Does the flow need SME clarification before downstream use?"],
                "status": "needs_sme_review",
                "priority": "medium",
                "confidence": "low",
                "decision_basis": "source_plus_sme",
                "business_signal": "Flow analysis found an unresolved meaning or routing question.",
                "evidence_basis": f"Open question came from {item['artifact']}.",
                "sme_questions": [item["question"]],
                "current_conclusion": "Flow analysis still has unresolved meaning or routing questions.",
                "evidence": [],
                "contradictions": [],
                "gaps": [item["question"]],
                "impacts": [],
                "review_action": "route_to_sme",
                "source_artifacts": [item["artifact"]],
                "source_excerpt": {},
                "updated_at": iso_now(),
            }
        )

    return items


def merge_manual_items(
    project_root: Path,
    generated_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manual_path = project_root / "08_review_workspace" / "review-items.manual.yaml"
    if not manual_path.exists():
        return generated_items
    manual = load_yaml(manual_path)
    items_by_id = {item["id"]: item for item in generated_items}
    for override in manual.get("overrides") or []:
        if override.get("id") in items_by_id:
            items_by_id[override["id"]].update(override)
    for extra in manual.get("items") or []:
        items_by_id[extra["id"]] = extra
    return list(items_by_id.values())


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status_rank = {status: idx for idx, status in enumerate(STATUS_ORDER)}
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        items,
        key=lambda item: (
            status_rank.get(item["status"], 99),
            priority_rank.get(item.get("priority", "low"), 99),
            item["question"].lower(),
        ),
    )


def summary_payload(items: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(item["status"] for item in items)
    group_counts = Counter(STATUS_GROUPS[item["status"]] for item in items)
    action_counts = Counter(item["review_action"] for item in items)
    evidence_count = sum(len(item.get("evidence", [])) for item in items)
    return {
        "item_count": len(items),
        "status_counts": dict(status_counts),
        "group_counts": dict(group_counts),
        "action_counts": dict(action_counts),
        "evidence_cards": evidence_count,
    }


def render_html(payload: dict[str, Any]) -> str:
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(f"Review Workspace — {payload['project']['name']}")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --line: #d7dfeb;
      --text: #172033;
      --muted: #5f6b85;
      --accent: #2158d6;
      --blocked: #b42318;
      --needs: #b54708;
      --ready: #175cd3;
      --approved: #027a48;
      --shadow: 0 10px 30px rgba(18, 27, 53, 0.08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
    }}
    .shell {{
      display: grid;
      grid-template-rows: auto 1fr;
      min-height: 100vh;
    }}
    .hero {{
      padding: 24px 28px 20px;
      background: linear-gradient(135deg, #1b3c86, #3557b7 60%, #5080f2);
      color: white;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.2;
    }}
    .hero p {{
      margin: 0;
      max-width: 980px;
      color: rgba(255, 255, 255, 0.88);
    }}
    .hero-meta {{
      margin-top: 16px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .chip {{
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.14);
      color: white;
      font-size: 13px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 20px;
    }}
    .summary-card {{
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 10px;
      padding: 14px 16px;
      min-height: 84px;
    }}
    .summary-card .label {{
      display: block;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .summary-card strong {{
      font-size: 24px;
      line-height: 1;
    }}
    .workspace {{
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      padding: 20px 24px 24px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: var(--shadow);
    }}
    .queue {{
      padding: 16px;
      position: sticky;
      top: 16px;
    }}
    .queue h2, .detail h2 {{
      margin: 0 0 12px;
      font-size: 16px;
    }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }}
    button.filter {{
      border: 1px solid var(--line);
      background: white;
      color: var(--muted);
      border-radius: 999px;
      padding: 7px 11px;
      font-size: 12px;
      cursor: pointer;
    }}
    button.filter.active {{
      background: #eef4ff;
      border-color: #a9c0f4;
      color: var(--accent);
    }}
    .queue-list {{
      display: grid;
      gap: 10px;
    }}
    .queue-item {{
      width: 100%;
      text-align: left;
      border: 1px solid var(--line);
      background: white;
      border-radius: 10px;
      padding: 12px;
      cursor: pointer;
    }}
    .queue-item.active {{
      border-color: #9bb8ff;
      box-shadow: 0 0 0 2px #dce8ff;
    }}
    .queue-item .queue-meta {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .queue-item .queue-question {{
      font-size: 14px;
      line-height: 1.45;
    }}
    .detail {{
      padding: 20px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 600;
      margin-right: 8px;
      margin-bottom: 8px;
    }}
    .status-blocked, .status-contradicted {{ background: #fee4e2; color: var(--blocked); }}
    .status-needs_sme_review, .status-needs_review {{ background: #fff0dc; color: var(--needs); }}
    .status-ready_to_approve {{ background: #e9f2ff; color: var(--ready); }}
    .status-approved, .status-deferred {{ background: #dcfae6; color: var(--approved); }}
    .detail-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
      gap: 18px;
      margin-top: 16px;
    }}
    .detail-block {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
      background: #fcfdff;
    }}
    .detail-block h3 {{
      margin: 0 0 10px;
      font-size: 14px;
    }}
    .detail-block p, .detail-block li {{
      font-size: 14px;
      line-height: 1.5;
      color: var(--text);
    }}
    .detail-block ul {{
      margin: 0;
      padding-left: 18px;
    }}
    .business-signal {{
      grid-column: 1 / -1;
      background: #fffaf0;
      border-color: #f3d08f;
    }}
    .business-signal p {{
      font-size: 16px;
      line-height: 1.55;
      margin: 0;
    }}
    .evidence-list {{
      display: grid;
      gap: 12px;
    }}
    .evidence-card {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: white;
    }}
    .evidence-card strong {{
      display: block;
      margin-bottom: 6px;
    }}
    .evidence-card .meta {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    .link-list a {{
      display: inline-block;
      margin: 0 8px 8px 0;
      font-size: 13px;
      color: var(--accent);
      text-decoration: none;
    }}
    .link-list a:hover {{ text-decoration: underline; }}
    .empty {{
      color: var(--muted);
      font-size: 14px;
    }}
    .evidence-card {{ position: relative; }}
    .evidence-preview-btn {{
      display: block;
      width: 100%;
      margin-top: 10px;
      padding: 7px 10px;
      border: 1px solid var(--line);
      background: #f0f4ff;
      color: var(--accent);
      border-radius: 7px;
      font-size: 12px;
      cursor: pointer;
      text-align: left;
      font-family: inherit;
    }}
    .evidence-preview-btn:hover {{ background: #e4ecff; }}
    .evidence-preview {{
      display: none;
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .evidence-preview.open {{ display: block; }}
    .evidence-preview-header {{
      padding: 6px 12px;
      background: #eef1f8;
      border-bottom: 1px solid var(--line);
      font-size: 11px;
      color: var(--muted);
    }}
    .evidence-preview pre {{
      margin: 0;
      padding: 12px;
      overflow-x: auto;
      font-size: 12px;
      line-height: 1.65;
      max-height: 320px;
      overflow-y: auto;
      background: #fafbfd;
    }}
    .evidence-preview .not-available {{
      padding: 12px;
      color: var(--muted);
      font-style: italic;
      font-size: 13px;
    }}
    .evidence-file-link {{
      font-size: 11px;
      color: var(--muted);
      text-decoration: none;
      float: right;
    }}
    .evidence-file-link:hover {{
      text-decoration: underline;
      color: var(--accent);
    }}
    @media (max-width: 1080px) {{
      .workspace, .detail-grid, .summary {{ grid-template-columns: 1fr; }}
      .queue {{ position: static; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header class="hero">
      <h1>{title}</h1>
      <p>Evidence-first review workspace. The queue is organized for human decisions: what is blocked, what needs SME input, what is ready to approve, and what has already closed cleanly.</p>
      <div class="hero-meta" id="hero-meta"></div>
      <section class="summary" id="summary"></section>
    </header>
    <main class="workspace">
      <aside class="panel queue">
        <h2>Review Queue</h2>
        <div class="filters" id="filters"></div>
        <div class="queue-list" id="queue-list"></div>
      </aside>
      <section class="panel detail">
        <h2>Current Review Item</h2>
        <div id="detail-root" class="empty">No review items available.</div>
      </section>
    </main>
  </div>
  <script id="review-data" type="application/json">{data_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById("review-data").textContent);
    const filters = ["all", "blocked", "contradicted", "needs_sme_review", "needs_review", "ready_to_approve", "approved", "deferred"];
    let activeFilter = "all";
    let activeId = payload.review_items[0] ? payload.review_items[0].id : null;

    function statusLabel(status) {{
      return status.replaceAll("_", " ");
    }}

    function escapeHtml(value) {{
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }}

    function buildElement(tagName, attributes, textContent) {{
      const element = document.createElement(tagName);
      for (const [key, value] of Object.entries(attributes || {{}})) {{
        if (key === "className") {{
          element.className = value;
        }} else if (key === "dataset") {{
          for (const [dataKey, dataValue] of Object.entries(value)) {{
            element.dataset[dataKey] = dataValue;
          }}
        }} else {{
          element.setAttribute(key, value);
        }}
      }}
      if (textContent !== undefined) {{
        element.textContent = textContent;
      }}
      return element;
    }}

    function appendTextBlock(parent, className, text) {{
      parent.appendChild(buildElement("div", {{ className }}, text));
    }}

    function renderSummary() {{
      const meta = document.getElementById("hero-meta");
      meta.innerHTML = "";
      [
        `Source commit ${{payload.project.source_commit}}`,
        `Generated ${{payload.project.generated_at}}`,
        `${{payload.summary.item_count}} review items`,
        `${{payload.project.project_root}}`
      ].forEach(text => {{
        const span = document.createElement("span");
        span.className = "chip";
        span.textContent = text;
        meta.appendChild(span);
      }});

      const summary = document.getElementById("summary");
      summary.innerHTML = "";
      const cards = [
        ["Must Resolve", payload.summary.group_counts["Must Resolve"] || 0],
        ["Needs SME", payload.summary.group_counts["Needs SME"] || 0],
        ["Ready To Approve", payload.summary.status_counts["ready_to_approve"] || 0],
        ["Closed", payload.summary.group_counts["Closed"] || 0],
      ];
      for (const [label, value] of cards) {{
        const card = document.createElement("article");
        card.className = "summary-card";
        card.innerHTML = `<span class="label">${{escapeHtml(label)}}</span><strong>${{escapeHtml(value)}}</strong>`;
        summary.appendChild(card);
      }}
    }}

    function renderFilters() {{
      const root = document.getElementById("filters");
      root.innerHTML = "";
      for (const filter of filters) {{
        const button = document.createElement("button");
        button.className = `filter ${{filter === activeFilter ? "active" : ""}}`;
        button.textContent = filter === "all" ? "all" : statusLabel(filter);
        button.onclick = () => {{
          activeFilter = filter;
          const visible = filteredItems();
          if (!visible.find(item => item.id === activeId)) {{
            activeId = visible[0] ? visible[0].id : null;
          }}
          renderFilters();
          renderQueue();
          renderDetail();
        }};
        root.appendChild(button);
      }}
    }}

    function filteredItems() {{
      return payload.review_items.filter(item => activeFilter === "all" || item.status === activeFilter);
    }}

    function renderQueue() {{
      const root = document.getElementById("queue-list");
      root.innerHTML = "";
      const items = filteredItems();
      if (!items.length) {{
        root.innerHTML = `<div class="empty">No items for this filter.</div>`;
        return;
      }}
      for (const item of items) {{
        const button = document.createElement("button");
        button.className = `queue-item ${{item.id === activeId ? "active" : ""}}`;
        button.onclick = () => {{
          activeId = item.id;
          renderQueue();
          renderDetail();
        }};
        const evidenceCount = item.evidence ? item.evidence.length : 0;
        const gapCount = item.gaps ? item.gaps.length : 0;
        button.innerHTML = `
          <div class="queue-meta">
            <span>${{escapeHtml(statusLabel(item.status))}}</span>
            <span>${{escapeHtml(item.priority)}} priority</span>
          </div>
          <div class="queue-question">${{escapeHtml(item.question)}}</div>
          <div class="queue-meta">
            <span>${{escapeHtml(evidenceCount)}} evidence card${{evidenceCount === 1 ? "" : "s"}}</span>
            <span>${{escapeHtml(gapCount)}} gap${{gapCount === 1 ? "" : "s"}}</span>
          </div>
        `;
        root.appendChild(button);
      }}
    }}

    function artifactLink(path) {{
      if (!path) return "";
      const href = encodeURI(`../${{path}}`);
      return `<a href="${{escapeHtml(href)}}" target="_blank" rel="noopener">${{escapeHtml(path)}}</a>`;
    }}

    function evidenceFileHref(source) {{
      if (!source || source === "source not indexed") return null;
      return "../" + source;
    }}

    function renderEvidenceCard(card) {{
      const article = buildElement("article", {{ className: "evidence-card" }});
      const href = evidenceFileHref(card.source);
      if (href) {{
        article.appendChild(buildElement("a", {{ className: "evidence-file-link", href, target: "_blank", rel: "noopener" }}, "open file"));
      }} else {{
        article.appendChild(buildElement("span", {{ className: "evidence-file-link" }}, "file not available"));
      }}

      article.appendChild(buildElement("strong", {{}}, `${{card.id}} — ${{card.title || card.type || ""}}`));
      appendTextBlock(
        article,
        "meta",
        `${{card.type || "unknown"}} · ${{card.strength || "evidence"}} · ${{card.approval || "approval not recorded"}}`,
      );
      appendTextBlock(article, "", card.supports || "");

      const button = buildElement(
        "button",
        {{ className: "evidence-preview-btn", type: "button", dataset: {{ previewToggle: "true" }} }},
        "▼ show evidence preview",
      );
      article.appendChild(button);

      const preview = buildElement("div", {{ className: "evidence-preview" }});
      const excerpt = card.excerpt || {{}};
      const lines = excerpt.lines || [];
      const headerInfo = excerpt.available
        ? `${{excerpt.file_type || "file"}} · ${{excerpt.total_lines || lines.length}} lines · ${{card.source}}`
        : card.source;
      preview.appendChild(buildElement("div", {{ className: "evidence-preview-header" }}, headerInfo));

      if (excerpt.available === false) {{
        appendTextBlock(preview, "not-available", excerpt.reason || "preview not available");
      }} else if (lines.length === 0) {{
        appendTextBlock(preview, "not-available", "(empty file)");
      }} else {{
        const pre = document.createElement("pre");
        for (let index = 0; index < lines.length; index += 1) {{
          const line = lines[index];
          if (excerpt.is_text) {{
            pre.appendChild(buildElement("div", {{ className: "line-text" }}, line));
          }} else {{
            const row = buildElement("div", {{ className: "code-line" }});
            row.appendChild(buildElement("span", {{ className: "line-num" }}, String(index + 1)));
            row.appendChild(buildElement("span", {{ className: "line-text" }}, line));
            pre.appendChild(row);
          }}
        }}
        preview.appendChild(pre);
        if (excerpt.truncated_note) {{
          preview.appendChild(buildElement("div", {{ className: "truncated-note" }}, excerpt.truncated_note));
        }}
      }}

      article.appendChild(preview);
      button.addEventListener("click", () => {{
        preview.classList.toggle("open");
        button.textContent = preview.classList.contains("open") ? "▲ collapse preview" : "▼ show evidence preview";
      }});
      return article;
    }}

    function renderList(values, emptyMessage) {{
      if (!values || values.length === 0) {{
        return buildElement("div", {{ className: "empty" }}, emptyMessage);
      }}
      const list = document.createElement("ul");
      for (const value of values) {{
        list.appendChild(buildElement("li", {{}}, value));
      }}
      return list;
    }}

    function appendDetailBlock(parent, title, child) {{
      const block = buildElement("div", {{ className: "detail-block" }});
      block.appendChild(buildElement("h3", {{}}, title));
      block.appendChild(child);
      parent.appendChild(block);
      return block;
    }}

    function appendBusinessSignalBlock(parent, text) {{
      const paragraph = document.createElement("p");
      paragraph.textContent = text || "No business signal recorded.";
      const block = appendDetailBlock(parent, "Business Signal", paragraph);
      block.classList.add("business-signal");
    }}

    function appendTextDetailBlock(parent, title, text) {{
      const paragraph = document.createElement("p");
      paragraph.textContent = text;
      appendDetailBlock(parent, title, paragraph);
    }}

    function renderDetail() {{
      const root = document.getElementById("detail-root");
      const item = payload.review_items.find(candidate => candidate.id === activeId);
      if (!item) {{
        root.className = "empty";
        root.textContent = "No review item selected.";
        return;
      }}
      root.className = "";
      root.innerHTML = "";

      const badges = document.createElement("div");
      for (const value of [statusLabel(item.status), item.review_action, item.confidence]) {{
        badges.appendChild(buildElement("span", {{ className: `badge status-${{item.status}}` }}, value));
      }}
      root.appendChild(badges);

      const heading = buildElement("h3", {{}}, item.question || "Untitled review item");
      heading.style.margin = "6px 0 10px";
      heading.style.fontSize = "24px";
      heading.style.lineHeight = "1.3";
      root.appendChild(heading);

      const meta = buildElement(
        "p",
        {{}},
        `Theme: ${{item.theme || "n/a"}} · Basis: ${{item.decision_basis || "n/a"}} · Type: ${{item.type || "n/a"}}`,
      );
      meta.style.margin = "0 0 14px";
      meta.style.color = "var(--muted)";
      root.appendChild(meta);

      const grid = buildElement("div", {{ className: "detail-grid" }});
      appendBusinessSignalBlock(grid, item.business_signal);
      appendTextDetailBlock(grid, "Evidence Basis", item.evidence_basis || "No evidence basis recorded.");
      appendDetailBlock(grid, "SME Questions", renderList(item.sme_questions || [], "No SME questions recorded."));
      appendTextDetailBlock(grid, "Current Conclusion", item.current_conclusion || "No conclusion recorded.");
      appendTextDetailBlock(
        grid,
        "Decision Needed Now",
        `${{item.review_action}} — reviewer should decide whether this item can move forward, needs stronger evidence, or must route to SME.`,
      );
      appendDetailBlock(grid, "Sub-Questions", renderList(item.sub_questions || [], "No sub-questions recorded."));
      appendDetailBlock(grid, "Impact", renderList(item.impacts || [], "No impacted IDs recorded."));

      const evidenceList = buildElement("div", {{ className: "evidence-list" }});
      const evidenceCards = item.evidence || [];
      if (!evidenceCards.length) {{
        evidenceList.appendChild(buildElement("div", {{ className: "empty" }}, "No evidence cards recorded."));
      }} else {{
        for (const card of evidenceCards) {{
          evidenceList.appendChild(renderEvidenceCard(card));
        }}
      }}
      appendDetailBlock(grid, "Evidence", evidenceList);

      const gapsBlock = document.createElement("div");
      gapsBlock.appendChild(renderList(item.gaps || [], "No gaps recorded."));
      gapsBlock.appendChild(buildElement("h3", {{}}, "Contradictions"));
      gapsBlock.lastChild.style.marginTop = "18px";
      gapsBlock.appendChild(renderList(item.contradictions || [], "No contradictions recorded."));
      appendDetailBlock(grid, "Gaps", gapsBlock);

      const sourceBlock = buildElement("div", {{ className: "detail-block" }});
      sourceBlock.style.gridColumn = "1 / -1";
      sourceBlock.appendChild(buildElement("h3", {{}}, "Source Artifacts"));
      const linkList = buildElement("div", {{ className: "link-list" }});
      const sourceArtifacts = item.source_artifacts || [];
      if (!sourceArtifacts.length) {{
        linkList.appendChild(buildElement("span", {{ className: "empty" }}, "No source artifacts recorded."));
      }} else {{
        for (const path of sourceArtifacts) {{
          if (!path) continue;
          const href = encodeURI(`../${{path}}`);
          linkList.appendChild(buildElement("a", {{ href, target: "_blank", rel: "noopener" }}, path));
        }}
      }}
      sourceBlock.appendChild(linkList);
      const sourceHeading = buildElement("h3", {{}}, "Source Excerpt");
      sourceHeading.style.marginTop = "18px";
      sourceBlock.appendChild(sourceHeading);
      const sourcePre = buildElement("pre", {{}}, JSON.stringify(item.source_excerpt || {{}}, null, 2));
      sourcePre.style.whiteSpace = "pre-wrap";
      sourcePre.style.margin = "0";
      sourcePre.style.fontSize = "13px";
      sourcePre.style.color = "var(--muted)";
      sourceBlock.appendChild(sourcePre);
      grid.appendChild(sourceBlock);

      root.appendChild(grid);
    }}

    renderSummary();
    renderFilters();
    renderQueue();
    renderDetail();
  </script>
</body>
</html>
"""


def build_payload(project_root: Path) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parent.parent
    artifacts = load_artifacts(project_root)
    spec_doc = load_yaml(artifacts.spec_path)
    spec = spec_doc.get("spec") or {}
    evidence_index = load_evidence_index(artifacts.evidence_manifest_path)
    trace_rows, coverage_notes = parse_traceability_rows(artifacts.traceability_path)
    program_support = parse_program_support(artifacts.program_paths)
    flow_support = parse_flow_support(artifacts.flow_paths)

    items = build_rule_items(artifacts, spec, evidence_index, trace_rows)
    items.append(build_traceability_item(artifacts, spec, evidence_index, coverage_notes, trace_rows))
    items.extend(build_open_question_items(artifacts, spec, evidence_index, program_support, flow_support))
    items = merge_manual_items(project_root, items)
    items = ensure_review_item_review_fields(items)
    items = sort_items(items)

    return {
        "schema_version": "0.1",
        "project": {
            "name": project_root.name,
            "project_root": rel_to(repo_root, project_root) or project_root.as_posix(),
            "capability_id": spec.get("capability_id"),
            "status": spec.get("status"),
            "source_commit": git_commit(repo_root),
            "generated_at": iso_now(),
        },
        "summary": summary_payload(items),
        "review_items": items,
        "evidence_index": evidence_index,
    }


def write_outputs(project_root: Path, payload: dict[str, Any]) -> None:
    output_dir = project_root / "08_review_workspace"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "review-items.json"
    html_path = output_dir / "index.html"

    safe_payload = json_safe(payload)
    json_path.write_text(json.dumps(safe_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    html_path.write_text(render_html(safe_payload), encoding="utf-8")


def main() -> int:
    args = parse_args()
    project_root = resolve_project_root(args.project)
    payload = build_payload(project_root)
    write_outputs(project_root, payload)
    print(f"OK: review workspace generated for {project_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
