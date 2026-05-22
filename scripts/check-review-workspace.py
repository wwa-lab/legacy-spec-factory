#!/usr/bin/env python3
"""Validate a generated review workspace against source artifacts.

Checks:
- `08_review_workspace/review-items.json` exists and parses
- every review item has stable required fields
- statuses and actions come from the allowed enums
- evidence IDs referenced by review items exist in the evidence manifest
- impacted IDs exist in the spec or traceability layer
- every approved rule or error condition has at least one review item

Usage:
  python3 scripts/check-review-workspace.py docs/<project-name>/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


VALID_STATUSES = {
    "blocked",
    "contradicted",
    "needs_sme_review",
    "needs_review",
    "ready_to_approve",
    "approved",
    "deferred",
}

VALID_ACTIONS = {
    "mark_blocked",
    "route_to_sme",
    "request_more_evidence",
    "approve",
    "defer",
    "reopen",
}


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check-review-workspace.py docs/<project-name>/", file=sys.stderr)
        return 2

    project_root = Path(sys.argv[1]).resolve()
    review_path = project_root / "08_review_workspace" / "review-items.json"
    if not review_path.exists():
        print(f"Missing generated review workspace: {review_path}", file=sys.stderr)
        return 1

    payload = json.loads(review_path.read_text(encoding="utf-8"))
    items = payload.get("review_items") or []
    errors: list[str] = []

    spec_candidates = sorted(project_root.glob("05_specs/*/spec.yaml"))
    spec_path = spec_candidates[0] if spec_candidates else None
    if spec_path is None:
        errors.append("No spec.yaml found under 05_specs/")
        spec = {}
    else:
        spec = (load_yaml(spec_path).get("spec") or {})

    manifest_path = None
    evidence_manifest_rel = ((spec.get("source_artifacts") or {}).get("evidence_manifest"))
    if evidence_manifest_rel:
        candidate = project_root / evidence_manifest_rel
        if candidate.exists():
            manifest_path = candidate
    evidence_ids = set()
    if manifest_path:
        manifest = load_yaml(manifest_path)
        evidence_ids = {item.get("evidence_id") for item in manifest.get("items") or [] if item.get("evidence_id")}

    valid_impacts = {rule.get("id") for rule in spec.get("rules") or [] if rule.get("id")}
    valid_impacts.update({err.get("id") for err in spec.get("error_conditions") or [] if err.get("id")})
    valid_impacts.update({spec.get("capability_id")} if spec.get("capability_id") else set())

    seen_ids: set[str] = set()
    covered_impacts: set[str] = set()

    for item in items:
        item_id = item.get("id")
        if not item_id:
            errors.append("Review item missing id")
            continue
        if item_id in seen_ids:
            errors.append(f"Duplicate review item id: {item_id}")
        seen_ids.add(item_id)

        if item.get("status") not in VALID_STATUSES:
            errors.append(f"{item_id}: invalid status {item.get('status')!r}")
        if item.get("review_action") not in VALID_ACTIONS:
            errors.append(f"{item_id}: invalid review_action {item.get('review_action')!r}")
        if not item.get("question"):
            errors.append(f"{item_id}: missing question")
        if not item.get("current_conclusion"):
            errors.append(f"{item_id}: missing current_conclusion")

        for artifact in item.get("source_artifacts") or []:
            if not (project_root / artifact).exists():
                errors.append(f"{item_id}: missing source artifact {artifact}")

        for evidence in item.get("evidence") or []:
            ev_id = evidence.get("id")
            if ev_id and evidence_ids and ev_id not in evidence_ids:
                errors.append(f"{item_id}: evidence id not found in manifest: {ev_id}")

        for impacted in item.get("impacts") or []:
            if impacted in valid_impacts:
                covered_impacts.add(impacted)
            elif impacted.startswith(("BR-", "ERR-", "CAP-")):
                errors.append(f"{item_id}: impacted id not found in spec/traceability scope: {impacted}")

        if item.get("status") == "blocked" and item.get("review_action") not in {"mark_blocked", "request_more_evidence", "route_to_sme"}:
            errors.append(f"{item_id}: blocked items must route to blocking actions")

    for rule in spec.get("rules") or []:
        if rule.get("review_status") == "approved" and rule.get("id") not in covered_impacts:
            errors.append(f"Approved rule missing from review workspace: {rule.get('id')}")
    for err in spec.get("error_conditions") or []:
        if err.get("id") not in covered_impacts:
            errors.append(f"Error condition missing from review workspace: {err.get('id')}")

    if errors:
        print("Review workspace validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        "OK: review workspace valid "
        f"({len(items)} items, {len(covered_impacts)} impacted IDs, {len(evidence_ids)} evidence IDs indexed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
