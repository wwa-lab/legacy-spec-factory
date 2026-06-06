from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_ANALYZER_DIR = REPO_ROOT / "skills" / "legacy-ibmi-module-analyzer"


class ModuleAnalyzerCompactArtifactGuidanceTests(unittest.TestCase):
    def test_module_analyzer_consumes_flow_and_program_compact_artifacts(self) -> None:
        skill_text = (MODULE_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (MODULE_ANALYZER_DIR / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        overview_template = (MODULE_ANALYZER_DIR / "templates" / "module-overview.md").read_text(
            encoding="utf-8"
        )
        view_template = (MODULE_ANALYZER_DIR / "templates" / "view-template.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, contract_text, overview_template, view_template):
            self.assertIn("program-analysis-summary.yaml", text)
            self.assertIn("source-index.yaml", text)
            self.assertIn("routine-logic-details.yaml", text)
            self.assertIn("message-inventory.yaml", text)
            self.assertIn("file-io-inventory.yaml", text)
            self.assertIn("field-mutation-matrix.yaml", text)
            self.assertIn("sql-inventory.yaml", text)

        self.assertIn("legacy-ibmi-flow-analyzer` v0.2.3", skill_text)
        self.assertIn("Do not concatenate", skill_text)
        self.assertIn("Do not concatenate", contract_text)
        self.assertIn("Do not concatenate", view_template)
        self.assertIn("Flow Artifact Set", overview_template)


if __name__ == "__main__":
    unittest.main()
