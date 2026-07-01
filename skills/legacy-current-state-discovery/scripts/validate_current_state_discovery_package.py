#!/usr/bin/env python3
"""Validate a legacy-current-state-discovery package structure.

This validator intentionally performs mechanical checks only. It does not
approve functional claims, evidence quality, or SME decisions.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REQUIRED_FILES = [
    "discovery-index.yaml",
    "document-master-index.md",
    "functional-discovery-report.md",
    "function-catalog.yaml",
    "project-derived-feature-index.yaml",
    "validation-catalog.yaml",
    "calculation-catalog.yaml",
    "interface-register.yaml",
    "channel-ui-report-catalog.md",
    "accounting-gl-ie-index.yaml",
    "traceability-matrix.csv",
    "open-questions-and-gaps.md",
]

TRACEABILITY_HEADER = [
    "item_id",
    "item_type",
    "item_name",
    "claim_summary",
    "source_id",
    "source_location",
    "evidence_id",
    "evidence_strength",
    "confidence",
    "review_status",
    "gap_id",
    "notes",
]

REPORT_HEADINGS = [
    "## 1. Existing Functionality",
    "## 2. Process Flow",
    "## 3. Upstream / Downstream Applications",
    "## 4. System Configuration / Parameter",
    "## 5. Channels",
    "## 6. Report",
    "## 7. Customer Communication, Triggers, and Associated Requirement",
    "## 8. Operational Procedure",
    "## 9. Current Limitation / Pain Point",
    "## 10. Gap Analysis",
    "## 11. Cross Reference BRD",
]

YAML_MARKERS = {
    "discovery-index.yaml": ["package_type: current_state_discovery", "status:", "outputs:"],
    "function-catalog.yaml": ["catalog_type: function_catalog", "functions:"],
    "project-derived-feature-index.yaml": ["catalog_type: project_derived_feature_index", "features:"],
    "validation-catalog.yaml": ["catalog_type: validation_catalog", "validations:"],
    "calculation-catalog.yaml": ["catalog_type: calculation_catalog", "calculations:"],
    "interface-register.yaml": ["catalog_type: interface_register", "interfaces:"],
    "accounting-gl-ie-index.yaml": ["catalog_type: accounting_gl_ie_index", "accounting_impacts:"],
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def check_required_files(package: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for name in REQUIRED_FILES:
        path = package / name
        if not path.exists():
            errors.append(f"missing required file: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file: {name}")
    if not errors:
        warnings.append("all required files are present")
    return errors, warnings


def check_yaml_markers(package: Path) -> list[str]:
    errors: list[str] = []
    for name, markers in YAML_MARKERS.items():
        path = package / name
        if not path.exists():
            continue
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                errors.append(f"{name} missing marker: {marker}")
    return errors


def check_report(package: Path) -> list[str]:
    errors: list[str] = []
    path = package / "functional-discovery-report.md"
    if not path.exists():
        return errors
    text = read_text(path)
    for heading in REPORT_HEADINGS:
        if heading not in text:
            errors.append(f"functional-discovery-report.md missing heading: {heading}")
    return errors


def check_traceability(package: Path) -> list[str]:
    errors: list[str] = []
    path = package / "traceability-matrix.csv"
    if not path.exists():
        return errors
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            errors.append("traceability-matrix.csv is empty")
            return errors
    if header != TRACEABILITY_HEADER:
        errors.append(
            "traceability-matrix.csv header mismatch: "
            f"expected {','.join(TRACEABILITY_HEADER)}"
        )
    return errors


def check_placeholders(package: Path, allow_placeholders: bool) -> list[str]:
    if allow_placeholders:
        return []
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = package / name
        if not path.exists() or path.suffix not in {".md", ".yaml", ".csv"}:
            continue
        text = read_text(path)
        if "<" in text and ">" in text:
            errors.append(f"{name} still appears to contain template placeholders")
    return errors


def check_ready_status(package: Path, require_ready: bool) -> list[str]:
    if not require_ready:
        return []
    path = package / "discovery-index.yaml"
    if not path.exists():
        return []
    text = read_text(path)
    allowed = ("status: ready_for_sme_review", "status: ready_with_warnings")
    if not any(marker in text for marker in allowed):
        return ["discovery-index.yaml status is not ready_for_sme_review or ready_with_warnings"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", help="Path to current-state discovery package")
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow template placeholders such as <MODULE-SLUG>",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Require package status ready_for_sme_review or ready_with_warnings",
    )
    args = parser.parse_args()

    package = Path(args.package)
    errors: list[str] = []
    warnings: list[str] = []

    if not package.exists() or not package.is_dir():
        print(f"ERROR: package path is not a directory: {package}", file=sys.stderr)
        return 2

    file_errors, file_warnings = check_required_files(package)
    errors.extend(file_errors)
    warnings.extend(file_warnings)
    errors.extend(check_yaml_markers(package))
    errors.extend(check_report(package))
    errors.extend(check_traceability(package))
    errors.extend(check_placeholders(package, args.allow_placeholders))
    errors.extend(check_ready_status(package, args.require_ready))

    for warning in warnings:
        print(f"OK: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"FAILED: {len(errors)} issue(s)", file=sys.stderr)
        return 1
    print("PASS: current-state discovery package structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
