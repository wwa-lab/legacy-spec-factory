from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "legacy-document-evidence-intake"


class DocumentIntakeSkillGuidanceTests(unittest.TestCase):
    def test_model_visible_pdf_and_image_content_is_not_tooling_unavailable(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        format_text = (SKILL_DIR / "references" / "format-strategy.md").read_text(
            encoding="utf-8"
        )
        quality_text = (SKILL_DIR / "references" / "quality-gates.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Model-visible PDF/image rule", skill_text)
        self.assertIn("model-visible content must be extracted", format_text)
        self.assertIn(
            "Model-visible extracted content prevents tooling-only blocked gates",
            quality_text,
        )

    def test_python_environment_setup_is_recoverable(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Managed Python environment rule", skill_text)
        self.assertIn("recoverable setup state", skill_text)
        self.assertIn("If the user continues setup", skill_text)
        self.assertNotIn("tool_unavailable_python_environment_configuring", skill_text)
        self.assertNotIn("terminal tooling signal", skill_text)
        self.assertNotIn("or wait on interactive environment setup", skill_text)


if __name__ == "__main__":
    unittest.main()
