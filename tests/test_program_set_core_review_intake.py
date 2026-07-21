from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE = REPO_ROOT / "scripts/prepare-program-set-core-review.py"


class ProgramSetCoreReviewIntakeTests(unittest.TestCase):
    def test_one_step_intake_prepares_one_bundle_without_fake_review_or_empty_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            write_finalized_program_artifacts(
                artifact_root / "modules" / "tier" / "CU106", "CU106"
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
            bundles = [path for path in output_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(bundles), 1)
            bundle = bundles[0]
            self.assertTrue((bundle / "program-set-core-input-manifest.yaml").is_file())
            self.assertTrue((bundle / "program-set-artifact-readiness.yaml").is_file())
            self.assertTrue((bundle / "program-set-reader-first-source-pack.md").is_file())
            self.assertTrue((bundle / "program-set-core-facts.yaml").is_file())
            self.assertTrue((bundle / "program-set-core-coverage.yaml").is_file())
            self.assertFalse(any(bundle.glob("*--sme-core-review.md")))
            manifest_text = (bundle / "program-set-core-input-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("review_name: programs", manifest_text)
            self.assertIn("review_status: ready_for_synthesis", manifest_text)
            self.assertFalse((bundle / "missing-program-list-batch").exists())
            self.assertFalse((output_dir / "program-set-core-input-manifest.yaml").exists())

            stale_queue = bundle / "missing-program-list-batch"
            stale_queue.mkdir()
            (stale_queue / "old-generated-prompt.md").write_text(
                "stale queue artifact\n", encoding="utf-8"
            )
            rerun = subprocess.run(
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
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertFalse(stale_queue.exists())


if __name__ == "__main__":
    unittest.main()
