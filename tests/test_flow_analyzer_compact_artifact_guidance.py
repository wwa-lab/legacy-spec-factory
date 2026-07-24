from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FLOW_ANALYZER_DIR = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer"
PROGRAM_ANALYZER_DIR = REPO_ROOT / "skills" / "legacy-ibmi-program-analyzer"


class FlowAnalyzerReaderFirstGuidanceTests(unittest.TestCase):
    def test_flow_analyzer_is_a_program_analysis_merger(self) -> None:
        skill_text = (FLOW_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (FLOW_ANALYZER_DIR / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        template_text = (FLOW_ANALYZER_DIR / "templates" / "sme-core-review.md").read_text(
            encoding="utf-8"
        )
        partial_template_text = (
            FLOW_ANALYZER_DIR / "templates" / "partial-draft.md"
        ).read_text(encoding="utf-8")

        for text in (skill_text, contract_text, template_text, partial_template_text):
            self.assertIn("program-analysis-summary.yaml", text)
            self.assertIn("source-index.yaml", text)
            self.assertIn("routine-logic-details.yaml", text)
            self.assertIn("message-inventory.yaml", text)

        self.assertIn("Reader-First Program Analysis Merger", skill_text)
        self.assertIn("missing-program-list-batch", skill_text)
        self.assertIn("prepare_program_set_core_review.py", skill_text)
        self.assertIn("blocked_artifact_readiness", skill_text)
        self.assertIn("lossless source pack", skill_text)
        self.assertIn("Never concatenate complete program-analysis files", contract_text)
        self.assertNotIn("orchestrated", skill_text)
        self.assertNotIn("assemble_existing", skill_text)
        self.assertNotIn("seven trigger", skill_text)

    def test_program_analyzer_handoff_uses_complete_reader_first_main_input(self) -> None:
        large_program_text = (
            PROGRAM_ANALYZER_DIR / "references" / "large-program-analysis.md"
        ).read_text(encoding="utf-8")

        self.assertIn("must prefer the finalized reader-first main", large_program_text)
        self.assertIn("semantic primary input", large_program_text)
        self.assertIn("lossless source pack", large_program_text)
        self.assertIn("program-analysis-summary.yaml", large_program_text)
        self.assertIn("routine-logic-details.yaml", large_program_text)
        self.assertIn("message-inventory.yaml", large_program_text)
        self.assertIn("file-io-inventory.yaml", large_program_text)
        self.assertIn("field-mutation-matrix.yaml", large_program_text)
        self.assertIn("sql-inventory.yaml", large_program_text)
        self.assertIn("do not replace the final", large_program_text)
        self.assertIn("synthesize rather than concatenate", large_program_text)

    def test_flow_analyzer_defaults_to_standard_reader_first(self) -> None:
        skill_text = (FLOW_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (FLOW_ANALYZER_DIR / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, contract_text):
            self.assertIn("standard_reader_first", text)
            self.assertIn("Program Set Reading Summary", text)
            self.assertIn("Cross-Program Processing Overview", text)
            self.assertIn("Calculation Logic", text)
            self.assertIn("Validation Logic", text)
            self.assertIn("Exception Handling", text)
            self.assertIn("Message Inventory", text)
            self.assertIn("blocked_artifact_readiness", text)
            self.assertNotIn("orchestrated", text)
            self.assertNotIn("assemble_existing", text)

    def test_sme_core_template_has_only_merge_sections(self) -> None:
        template_text = (
            FLOW_ANALYZER_DIR / "templates" / "sme-core-review.md"
        ).read_text(encoding="utf-8")

        expected_sections = [
            "## Program Set Reading Summary",
            "## Cross-Program Processing Overview",
            "## Calculation Logic",
            "## Validation Logic",
            "## Exception Handling",
            "## Message Inventory",
            "## Core Completeness Ledger",
            "## Coverage Reconciliation",
            "## Sources",
            "## Run Profile",
            "## Source Inventory Cache",
        ]
        positions = [template_text.index(section) for section in expected_sections]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("program-analysis.md", template_text)
        self.assertIn("routine-logic-details.yaml", template_text)
        self.assertIn("No program may be omitted", template_text)
        self.assertNotIn("## Nodes", template_text)
        self.assertNotIn("## Edges", template_text)
        self.assertNotIn("## Flow Replay Path", template_text)
        self.assertNotIn("## Flow Persistence Matrix", template_text)

    def test_partial_draft_uses_the_same_reader_first_order(self) -> None:
        template_text = (
            FLOW_ANALYZER_DIR / "templates" / "partial-draft.md"
        ).read_text(encoding="utf-8")
        expected_sections = [
            "## Program Set Reading Summary",
            "## Cross-Program Processing Overview",
            "## Calculation Logic",
            "## Validation Logic",
            "## Exception Handling",
            "## Message Inventory",
            "## Core Completeness Ledger",
            "## Coverage Reconciliation",
            "## Sources",
            "## Run Profile",
            "## Source Inventory Cache",
        ]
        positions = [template_text.index(section) for section in expected_sections]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("draft_exploratory", template_text)
        self.assertIn("pending", template_text)
        self.assertNotIn("## Nodes", template_text)
        self.assertNotIn("## Edges", template_text)
        self.assertNotIn("## Transaction Call Map", template_text)


if __name__ == "__main__":
    unittest.main()
