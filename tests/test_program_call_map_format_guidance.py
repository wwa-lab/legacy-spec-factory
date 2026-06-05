from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ANALYZER_DIR = REPO_ROOT / "skills" / "legacy-ibmi-program-analyzer"


class ProgramCallMapFormatGuidanceTests(unittest.TestCase):
    def test_visual_overview_guidance_requires_ascii_hierarchy_not_mermaid(self) -> None:
        skill_text = (PROGRAM_ANALYZER_DIR / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (
            PROGRAM_ANALYZER_DIR / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        template_text = (
            PROGRAM_ANALYZER_DIR / "templates" / "program-analysis.md"
        ).read_text(encoding="utf-8")
        example_texts = [
            (
                PROGRAM_ANALYZER_DIR
                / "examples"
                / "complex-batch-job"
                / "program-analysis.md"
            ).read_text(encoding="utf-8"),
            (
                PROGRAM_ANALYZER_DIR
                / "examples"
                / "simple-crud-rpgle"
                / "program-analysis.md"
            ).read_text(encoding="utf-8"),
        ]

        self.assertIn("normalized fenced `text` hierarchy", skill_text)
        self.assertIn("`|--` branches", skill_text)
        self.assertIn("not Mermaid", skill_text)
        self.assertIn(
            "The primary `Visual Overview` must be a fenced `text` ASCII hierarchy",
            contract_text,
        )
        self.assertIn(
            "starting with `<PROGRAM> mainline` and using `|--` branch connectors",
            contract_text,
        )
        self.assertIn("```text\n[PROGRAM] mainline\n|--", template_text)
        self.assertNotIn("```mermaid", template_text)
        self.assertIn("compact ASCII hierarchy Visual Overview", template_text)
        for example_text in example_texts:
            self.assertNotIn("```mermaid", example_text)
            self.assertIn("```text", example_text)
            self.assertIn("|--", example_text)


if __name__ == "__main__":
    unittest.main()
