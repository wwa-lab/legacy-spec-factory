from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-document-evidence-intake"
    / "scripts"
    / "validate_document_intake_package.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("document_intake_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_package(
    package_dir: Path,
    *,
    manifest_conversion_tool: str = "libreoffice",
    manifest_conversion_result: str = "succeeded",
    include_document_manifest: bool = True,
    include_normalized_output: bool = True,
) -> None:
    package_dir.mkdir(parents=True)
    normalized_path = package_dir / "documents" / "SALES-SPEC" / "normalized" / "sales-spec.md"

    (package_dir / "intake.manifest.yaml").write_text(
        f'''schema_version: "0.1"
package_type: document_evidence_intake

module_slug: "SALES-ORDERS"
docset_slug: "SALES-ORDERS-DOCS"
gate: "ready_with_warnings"

documents:
  - doc_id: "DOC-SALES-ORDERS-001"
    title: "Sales Spec"
    path: "authorized/sales-spec.xls"
    family: "excel"
    file_type: "xls"
    size_bytes: 128
    sha256: "abc123"
    owner: "Sales Ops"
    sensitivity: "internal"
    authorization_status: "authorized"
    conversion:
      required: true
      tool: "{manifest_conversion_tool}"
      from: "xls"
      to: "xlsx"
      result: "{manifest_conversion_result}"
    security_review_required: false
    document_gate: "ready_with_warnings"
    normalized_outputs:
      - "documents/SALES-SPEC/normalized/sales-spec.md"

outputs:
  - "intake.manifest.yaml"
  - "conversion-log.md"
  - "extraction-quality.yaml"
  - "extraction-warnings.md"
  - "evidence-coordinates.md"
''',
        encoding="utf-8",
    )
    (package_dir / "conversion-log.md").write_text(
        f"""# Conversion Log

| Doc ID | From | To | Tool | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| DOC-SALES-ORDERS-001 | .xls | .xlsx | {manifest_conversion_tool} | {manifest_conversion_result} | test |
""",
        encoding="utf-8",
    )
    (package_dir / "extraction-quality.yaml").write_text(
        """schema_version: "0.1"
documents:
  - doc_id: "DOC-SALES-ORDERS-001"
    macro:
      executed: false
""",
        encoding="utf-8",
    )
    (package_dir / "extraction-warnings.md").write_text("# Extraction Warnings\n", encoding="utf-8")
    (package_dir / "evidence-coordinates.md").write_text(
        "| Fragment ID | Doc ID |\n| --- | --- |\n| FRAG-SALES-ORDERS-001 | DOC-SALES-ORDERS-001 |\n",
        encoding="utf-8",
    )

    if include_document_manifest:
        doc_dir = package_dir / "documents" / "SALES-SPEC"
        doc_dir.mkdir(parents=True)
        (doc_dir / "document.manifest.yaml").write_text(
            """schema_version: "0.1"
doc_id: "DOC-SALES-ORDERS-001"
family: "excel"
file_type: "xls"
structure:
  sheets: []
fragments:
  - fragment_id: "FRAG-SALES-ORDERS-001"
    coordinate: "workbook/Sheet1/A1:B2"
    extraction_method: "deterministic"
    confidence: "high"
    promotion: "open"
document_gate: "ready_with_warnings"
""",
            encoding="utf-8",
        )

    if include_normalized_output:
        normalized_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_path.write_text("# Sales Spec\n", encoding="utf-8")


class DocumentIntakeValidatorTests(unittest.TestCase):
    def test_accepts_structurally_complete_ready_package(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "00_context_packages" / "SALES-ORDERS" / "document-intake" / "DOCS"
            write_package(package_dir)

            self.assertEqual(validator.validate(package_dir, allow_blocked=False), [])

    def test_requires_document_manifest_for_each_registered_document(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "00_context_packages" / "SALES-ORDERS" / "document-intake" / "DOCS"
            write_package(package_dir, include_document_manifest=False)

            findings = validator.validate(package_dir, allow_blocked=False)

            self.assertIn(
                "document DOC-SALES-ORDERS-001 missing documents/<DOC-SLUG>/document.manifest.yaml",
                findings,
            )

    def test_rejects_successful_conversion_without_a_tool(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "00_context_packages" / "SALES-ORDERS" / "document-intake" / "DOCS"
            write_package(package_dir, manifest_conversion_tool="none")

            findings = validator.validate(package_dir, allow_blocked=False)

            self.assertIn(
                "document DOC-SALES-ORDERS-001 records conversion succeeded without a real tool",
                findings,
            )

    def test_rejects_missing_normalized_output_for_ready_document(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "00_context_packages" / "SALES-ORDERS" / "document-intake" / "DOCS"
            write_package(package_dir, include_normalized_output=False)

            findings = validator.validate(package_dir, allow_blocked=False)

            self.assertIn(
                "document DOC-SALES-ORDERS-001 normalized output missing: documents/SALES-SPEC/normalized/sales-spec.md",
                findings,
            )


if __name__ == "__main__":
    unittest.main()
