from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-list-batch"
    / "scripts"
    / "initialize_program_batch.py"
)


class ProgramListBatchInitializerTests(unittest.TestCase):
    def test_windows_output_dir_preserves_separator_before_at_program(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "@CU400P,program,CLLE,@CU400P.CLLE,100,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )

            delivery_root = r"C:\sandbox\project\legacy-modernization-delivery"
            expected_output = (
                r"C:\sandbox\project\legacy-modernization-delivery"
                r"\modules\CAP-ID-0003-normal_program\@CU400P"
            )

            subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(out_dir),
                    "--source-root",
                    r"C:\sandbox\project\source-repo",
                    "--delivery-root",
                    delivery_root,
                    "--review-name",
                    "at program path test",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                row = next(csv.DictReader(handle))

            self.assertEqual(row["output_dir"], expected_output)
            self.assertNotIn("normal_program@CU400P", row["output_dir"])

            prompt_text = (out_dir / "prompt-queue" / "0001-@CU400P.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(f"Output directory: `{expected_output}`", prompt_text)

            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn(f"`{expected_output}`", plan_text)


if __name__ == "__main__":
    unittest.main()
