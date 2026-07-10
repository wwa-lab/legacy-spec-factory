from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-current-state-discovery"
    / "scripts"
    / "validate_current_state_discovery_package.py"
)

REQUIRED_FILES = (
    "discovery-index.yaml",
    "document-master-index.md",
    "behavior-claim-ledger.csv",
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
)

BEHAVIOR_HEADER = (
    "claim_id,item_type,item_id,business_area,business_meaning,trigger_condition,"
    "system_behavior,source_id,source_location,evidence_id,evidence_strength,"
    "confidence,review_status,gap_id,next_action,notes"
)

TRACEABILITY_HEADER = (
    "item_id,item_type,item_name,claim_summary,source_id,source_location,"
    "evidence_id,evidence_strength,confidence,review_status,gap_id,notes"
)

REPORT_HEADINGS = (
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
)


def write_valid_package(package: Path) -> None:
    package.mkdir(parents=True, exist_ok=True)
    contents = {
        "discovery-index.yaml": "\n".join(
            (
                "package_type: current_state_discovery",
                "status: ready_for_sme_review",
                "outputs:",
                "  report: functional-discovery-report.md",
            )
        ),
        "document-master-index.md": "# Document Master Index\n",
        "behavior-claim-ledger.csv": "\n".join(
            (
                BEHAVIOR_HEADER,
                "BCL-PAY-001,function,CAND-PAY-001,Payments,Accept a payment,"
                "Customer submits a payment,The system records the payment,"
                "DOC-PAY-001,Guide section 2,EV-PAY-001,documented,Confirmed,"
                "needs_sme_review,,,",
            )
        ),
        "functional-discovery-report.md": "\n".join(
            (
                "# Functional Discovery Report",
                *REPORT_HEADINGS,
                "| Gap ID | Area | Missing / Unclear Evidence | Impact | "
                "Owner / Route | Next Action | Status |",
            )
        ),
        "function-catalog.yaml": "catalog_type: function_catalog\nfunctions: []\n",
        "project-derived-feature-index.yaml": (
            "catalog_type: project_derived_feature_index\nfeatures: []\n"
        ),
        "validation-catalog.yaml": (
            "catalog_type: validation_catalog\nvalidations: []\n"
        ),
        "calculation-catalog.yaml": (
            "catalog_type: calculation_catalog\ncalculations: []\n"
        ),
        "interface-register.yaml": (
            "catalog_type: interface_register\ninterfaces: []\n"
        ),
        "channel-ui-report-catalog.md": "# Channel Catalog\n",
        "accounting-gl-ie-index.yaml": (
            "catalog_type: accounting_gl_ie_index\naccounting_impacts: []\n"
        ),
        "traceability-matrix.csv": "\n".join(
            (
                TRACEABILITY_HEADER,
                "CAND-PAY-001,function,Payment,Records payment,DOC-PAY-001,"
                "Guide section 2,EV-PAY-001,documented,Confirmed,"
                "needs_sme_review,,",
            )
        ),
        "open-questions-and-gaps.md": "# Open Questions and Gaps\n",
    }
    for name in REQUIRED_FILES:
        (package / name).write_text(contents[name], encoding="utf-8")


def run_python_validator(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class CurrentStateDiscoveryPythonValidatorTests(unittest.TestCase):
    def test_complete_package_passes_strict_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            write_valid_package(package)
            result = run_python_validator(
                "--quality-gate", "--require-ready", str(package)
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "OK: all required files are present",
                "PASS: current-state discovery package structure is valid",
            ],
        )
        self.assertEqual(result.stderr, "")

    def test_invalid_package_path_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            result = run_python_validator(str(missing))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr.strip(),
            f"ERROR: package path is not a directory: {missing}",
        )

    def test_strict_options_report_placeholders_status_and_quality_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            write_valid_package(package)
            (package / "discovery-index.yaml").write_text(
                "package_type: current_state_discovery\n"
                "status: draft\noutputs:\n  report: <REPORT>\n",
                encoding="utf-8",
            )
            (package / "behavior-claim-ledger.csv").write_text(
                "\n".join(
                    (
                        BEHAVIOR_HEADER,
                        "CLM-001,function,CLM-002,Payments,Folder contains a program,"
                        ",,DOC-001,unknown,EV-001,weak,Gap,needs_sme_review,CLM-003,,",
                    )
                ),
                encoding="utf-8",
            )
            result = run_python_validator(
                "--quality-gate", "--require-ready", str(package)
            )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), "OK: all required files are present")
        self.assertIn(
            "ERROR: discovery-index.yaml still appears to contain template placeholders",
            result.stderr,
        )
        self.assertIn(
            "ERROR: discovery-index.yaml status is not ready_for_sme_review or "
            "ready_with_warnings",
            result.stderr,
        )
        self.assertIn("uses generic CLM-* claim_id", result.stderr)
        self.assertIn("uses generic CLM-* item_id", result.stderr)
        self.assertIn("uses generic CLM-* gap_id", result.stderr)
        self.assertIn("gap row missing next_action", result.stderr)
        self.assertIn("has no non-gap behavior claims", result.stderr)
        self.assertTrue(result.stderr.rstrip().endswith("FAILED: 7 issue(s)"))

    def test_allow_placeholders_suppresses_only_placeholder_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            write_valid_package(package)
            report = package / "document-master-index.md"
            report.write_text("# Document Master Index\n<MODULE-SLUG>\n", encoding="utf-8")
            result = run_python_validator("--allow-placeholders", str(package))

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
