from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE = REPO_ROOT / "scripts/prepare-program-set-core-review.py"


REQUIRED_ARTIFACTS = (
    "program-analysis.md",
    "program-analysis-summary.yaml",
    "source-index.yaml",
    "routine-index.md",
    "message-inventory.yaml",
    "routine-logic-details.md",
    "routine-logic-details.yaml",
)


class ProgramSetCoreReviewIntakeTests(unittest.TestCase):
    def test_one_step_intake_creates_manifest_review_and_queue_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            program_folder = artifact_root / "modules" / "tier" / "CU106"
            program_folder.mkdir(parents=True)
            for filename in REQUIRED_ARTIFACTS:
                (program_folder / f"CU106-{filename}").write_text(
                    "schema_version: '0.1'\n", encoding="utf-8"
                )
            source_root = root / "source"
            source_root.mkdir()
            programs_file = root / "programs.txt"
            programs_file.write_text("CU106\n", encoding="utf-8")
            output_dir = root / "review"

            result = subprocess.run(
                [
                    sys.executable,
                    str(INTAKE),
                    "--programs-file",
                    str(programs_file),
                    "--artifact-root",
                    str(artifact_root),
                    "--source-root",
                    str(source_root),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "program-set-core-input-manifest.yaml").is_file())
            self.assertTrue((output_dir / "program-set-core-facts.yaml").is_file())
            self.assertTrue((output_dir / "program-set-sme-core-review.md").is_file())
            manifest_text = (output_dir / "program-set-core-input-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("review_name: programs", manifest_text)
            queue_state = output_dir / "missing-program-list-batch" / "program-set-scan-queue.yaml"
            self.assertTrue(queue_state.is_file())
            self.assertIn("no_missing_programs", queue_state.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
