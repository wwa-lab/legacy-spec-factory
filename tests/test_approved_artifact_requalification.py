from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "requalify_approved_program_artifacts.py"
)
QUEUE_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "create_approved_artifact_repair_queue.py"
)
PROFILE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)


def load_requalifier():
    spec = importlib.util.spec_from_file_location("requalify_approved_program_artifacts", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


REQUALIFIER = load_requalifier()


class ApprovedArtifactRequalificationTests(unittest.TestCase):
    def make_artifact(self, root: Path, program: str, tier: str = "normal_program"):
        return write_finalized_program_artifacts(
            root / "modules" / "CAP-ID-0003-normal_program" / program,
            program,
            size_tier=tier,
        )

    def report(self, root: Path):
        return REQUALIFIER.build_report(root, PROFILE)

    def test_discovers_profile_shaped_programs_and_marks_final_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "approved"
            self.make_artifact(root, "CU106")
            (root / "modules" / "not-a-program").mkdir(parents=True)
            (root / "modules" / "not-a-program" / "README.md").write_text("notes", encoding="utf-8")
            (root / "outputs" / "CU999").mkdir(parents=True)
            (root / "outputs" / "CU999" / "program-analysis.md").write_text("not in profile", encoding="utf-8")

            report = self.report(root)

            self.assertEqual(report["summary"]["total_candidates"], 1)
            self.assertEqual(report["summary"]["final_ready"], 1)
            self.assertEqual(report["programs"][0]["program"], "CU106")
            self.assertTrue(report["programs"][0]["final_contract_compatible"])

    def test_invalid_yaml_is_format_repairable_without_aborting_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "approved"
            fixture = self.make_artifact(root, "CU101A")
            fixture.source_index_yaml.write_text("- @CU176\n", encoding="utf-8")

            report = self.report(root)
            item = report["programs"][0]

            self.assertEqual(item["status"], "format_repairable")
            self.assertIn("yaml_reserved_scalar", item["finding_codes"])
            self.assertFalse(item["final_contract_compatible"])

    def test_core_missing_section_requires_semantic_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "approved"
            fixture = self.make_artifact(root, "CU101A")
            markdown = fixture.program_analysis.read_text(encoding="utf-8")
            fixture.program_analysis.write_text(
                markdown.replace("## Validation Logic", "## Removed Validation Logic", 1),
                encoding="utf-8",
            )

            item = self.report(root)["programs"][0]

            self.assertEqual(item["status"], "semantic_repair_required")
            self.assertIn("missing_reader_first_section", item["finding_codes"])

    def test_duplicate_normalized_programs_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "approved"
            self.make_artifact(root, "CU106")
            second = root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU106"
            write_finalized_program_artifacts(second, "CU106", size_tier="normal_program")

            report = self.report(root)

            self.assertEqual(report["summary"]["blocked"], 2)
            self.assertTrue(
                all(item["status"] == "blocked" for item in report["programs"])
            )
            self.assertTrue(
                all("ambiguous_artifact_root" in item["finding_codes"] for item in report["programs"])
            )

    def test_queue_has_one_prompt_per_repairable_program(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "approved"
            self.make_artifact(root, "CU106")
            broken = self.make_artifact(root, "CU101A")
            broken.source_index_yaml.write_text("- @CU176\n", encoding="utf-8")
            report_dir = Path(temp_dir) / "report"
            report_dir.mkdir()
            report_path = report_dir / "approved-artifact-requalification.yaml"
            report_path.write_text(REQUALIFIER.BUILDER.dump_yaml(self.report(root)), encoding="utf-8")
            queue_dir = Path(temp_dir) / "queue"

            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--report",
                    str(report_path),
                    "--out-dir",
                    str(queue_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            prompts = sorted((queue_dir / "prompt-queue").glob("*.md"))
            self.assertEqual(len(prompts), 1)
            prompt = prompts[0].read_text(encoding="utf-8")
            self.assertIn("CU101A", prompt)
            self.assertIn("one program only", prompt)
            self.assertNotIn("CU106", prompt)
            self.assertTrue((queue_dir / "repair-status.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
