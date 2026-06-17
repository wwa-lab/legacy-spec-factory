from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FLOW_ANALYZER_DIR = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer"
PROGRAM_ANALYZER_DIR = REPO_ROOT / "skills" / "legacy-ibmi-program-analyzer"


class FlowAnalyzerCompactArtifactGuidanceTests(unittest.TestCase):
    def test_flow_analyzer_supports_orchestrated_and_existing_assembly_modes(self) -> None:
        skill_text = (FLOW_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (FLOW_ANALYZER_DIR / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        template_text = (FLOW_ANALYZER_DIR / "templates" / "flow.md").read_text(encoding="utf-8")

        for text in (skill_text, contract_text, template_text):
            self.assertIn("orchestrated", text)
            self.assertIn("assemble_existing", text)
            self.assertIn("program-analysis-summary.yaml", text)
            self.assertIn("source-index.yaml", text)
            self.assertIn("routine-logic-details.yaml", text)
            self.assertIn("message-inventory.yaml", text)
            self.assertIn("file-io-inventory.yaml", text)
            self.assertIn("field-mutation-matrix.yaml", text)
            self.assertIn("sql-inventory.yaml", text)

        self.assertIn("Do not concatenate", skill_text)
        self.assertIn("Do not concatenate", template_text)
        self.assertIn("missing_program_artifact", contract_text)

    def test_program_analyzer_handoff_prefers_compact_flow_inputs(self) -> None:
        large_program_text = (
            PROGRAM_ANALYZER_DIR / "references" / "large-program-analysis.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Downstream flow/module analyzers must prefer", large_program_text)
        self.assertIn("program-analysis-summary.yaml", large_program_text)
        self.assertIn("routine-logic-details.yaml", large_program_text)
        self.assertIn("message-inventory.yaml", large_program_text)
        self.assertIn("file-io-inventory.yaml", large_program_text)
        self.assertIn("field-mutation-matrix.yaml", large_program_text)
        self.assertIn("sql-inventory.yaml", large_program_text)
        self.assertIn("should not", large_program_text)
        self.assertIn("concatenate", large_program_text)

    def test_flow_analyzer_front_loads_sme_review_sections_and_defaults_standalone(self) -> None:
        skill_text = (FLOW_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (FLOW_ANALYZER_DIR / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        template_text = (FLOW_ANALYZER_DIR / "templates" / "flow.md").read_text(encoding="utf-8")

        expected_order = [
            "## Calculation Logic",
            "## Validation Logic",
            "## Exception Handling",
            "## Message Inventory",
            "## Metadata",
        ]
        for text in (contract_text, template_text):
            positions = [text.index(section) for section in expected_order]
            self.assertEqual(positions, sorted(positions))

        self.assertIn("standalone_exploratory", skill_text)
        self.assertIn("default", skill_text)
        self.assertIn("chain_ready", skill_text)
        self.assertIn("downstream-readiness gaps", skill_text)
        self.assertIn("draft_exploratory", contract_text)
        self.assertIn("Downstream-Readiness Gap", contract_text)
        self.assertIn("Analysis Intent", template_text)

    def test_flow_analyzer_has_compact_multi_program_sme_core_review_view(self) -> None:
        skill_text = (FLOW_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (FLOW_ANALYZER_DIR / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        template_text = (
            FLOW_ANALYZER_DIR / "templates" / "sme-core-review.md"
        ).read_text(encoding="utf-8")

        for text in (skill_text, contract_text):
            self.assertIn("program-set-sme-core-review.md", text)
            self.assertIn("templates/sme-core-review.md", text)
            self.assertIn("Do not produce `flow-<FLOW-SLUG>.md`", text)

        self.assertNotIn("flow-sme-core-review.md", contract_text)

        expected_sections = [
            "## Calculation Logic",
            "## Validation Logic",
            "## Exception Handling",
            "## Message Inventory",
        ]
        positions = [template_text.index(section) for section in expected_sections]
        self.assertEqual(positions, sorted(positions))

        self.assertIn("program-analysis-summary.yaml", template_text)
        self.assertIn("routine-logic-details.yaml", template_text)
        self.assertIn("message-inventory.yaml", template_text)
        self.assertIn("Message Inventory must list every exact", template_text)
        self.assertIn("Do not include Nodes, Edges", template_text)
        self.assertNotIn("## Nodes", template_text)
        self.assertNotIn("## Edges", template_text)
        self.assertNotIn("## Flow Replay Path", template_text)
        self.assertNotIn("## Flow Persistence Matrix", template_text)


if __name__ == "__main__":
    unittest.main()
