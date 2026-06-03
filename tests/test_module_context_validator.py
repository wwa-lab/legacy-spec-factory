from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-module-context-intake"
    / "scripts"
    / "validate_context_package.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_context_package", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def write_package(package_dir: Path) -> None:
    package_dir.mkdir()
    (package_dir / "context-index.yaml").write_text(
        """
schema_version: "0.1"
package_type: module_context_intake

intake:
  status: ready_with_warnings

output_files:
  rag_evidence_map: "rag-evidence-map.md"
  contradiction_log: "contradiction-log.md"
  open_questions: "open-questions.md"
""".lstrip(),
        encoding="utf-8",
    )
    (package_dir / "rag-evidence-map.md").write_text(
        """
# RAG Evidence Map - CREDIT-CHECK

## Candidate Facts

| Candidate ID | Statement | Business Signal | Evidence Basis | Promotion Status | Required Review |
| --- | --- | --- | --- | --- | --- |
| RAG-CAND-CREDIT-CHECK-001 | Candidate only. | Business signal. | SNP-CREDIT-CHECK-001 | needs_sme_review | SME |
""".lstrip(),
        encoding="utf-8",
    )
    (package_dir / "contradiction-log.md").write_text(
        """
# Contradiction Log - CREDIT-CHECK

## Summary

- status: none_found
- evaluated_checks_present: true

## Evaluated Checks

| Check | Result | Notes |
| --- | --- | --- |
| RAG contradiction pass | none_found | Synthetic fixture. |
""".lstrip(),
        encoding="utf-8",
    )
    (package_dir / "open-questions.md").write_text(
        """
# Open Questions - CREDIT-CHECK

## Recommended Next Prompt

```text
Use legacy-ibmi-module-analyzer with
00_context_packages/CREDIT-CHECK/ as module-first context.
```
""".lstrip(),
        encoding="utf-8",
    )


class ModuleContextValidatorTests(unittest.TestCase):
    def test_validates_package_without_intake_flow_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "CREDIT-CHECK"
            write_package(package_dir)

            findings = VALIDATOR.validate(package_dir, allow_blocked=False)

            self.assertEqual(findings, [])
            self.assertFalse((package_dir / "01-operation-business-flow.md").exists())
            self.assertFalse((package_dir / "02-system-flow.md").exists())
            self.assertFalse((package_dir / "03-program-flow.md").exists())
            self.assertFalse((package_dir / "04-data-flow.md").exists())

    def test_fails_when_required_non_flow_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp) / "CREDIT-CHECK"
            write_package(package_dir)
            (package_dir / "rag-evidence-map.md").unlink()

            findings = VALIDATOR.validate(package_dir, allow_blocked=False)

            self.assertEqual(
                findings,
                ["Missing required files: rag-evidence-map.md"],
            )


if __name__ == "__main__":
    unittest.main()
