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
STATUS_VALIDATOR = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-list-batch"
    / "scripts"
    / "validate_program_batch_status.py"
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
            self.assertIn("routine-logic-details.md", prompt_text)
            self.assertIn("routine-logic-details.yaml", prompt_text)
            self.assertIn(
                "py -3 .agents\\skills\\legacy-ibmi-program-analyzer\\scripts\\validate_program_analysis_contract.py "
                "--analysis-dir",
                prompt_text,
            )
            self.assertNotIn("{{python_launcher}}", prompt_text)
            self.assertNotIn("For normal_program, do not create routine-logic-details.md", prompt_text)

            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn(f"`{expected_output}`", plan_text)

    def test_programs_file_filters_prompt_queue_in_flow_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            programs_file = temp_root / "programs.txt"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CCP03,program,RPGLE,CCP03.RPGLE,300,complex_normal_program,test",
                        "@CU400P,program,CLLE,@CU400P.CLLE,100,normal_program,test",
                        "@CU400,program,RPGLE,@CU400.RPGLE,500,complex_normal_program,test",
                        "IGNORED,program,RPGLE,IGNORED.RPGLE,20,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )
            programs_file.write_text("@CU400P -> @CU400 -> CCP03\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--programs-file",
                    str(programs_file),
                    "--out-dir",
                    str(out_dir),
                    "--source-root",
                    "/tmp/source",
                    "--delivery-root",
                    "/tmp/delivery",
                    "--review-name",
                    "flow prompt queue test",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            prompt_names = sorted(path.name for path in (out_dir / "prompt-queue").glob("*.md"))
            self.assertEqual(
                prompt_names,
                ["0001-@CU400P.md", "0002-@CU400.md", "0003-CCP03.md"],
            )
            self.assertFalse((out_dir / "prompt-queue" / "0004-IGNORED.md").exists())

            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                members = [row["member"] for row in csv.DictReader(handle)]
            self.assertEqual(members, ["@CU400P", "@CU400", "CCP03"])

            flow_program_list = (out_dir / "flow-program-list.csv").read_text(encoding="utf-8")
            self.assertIn("@CU400P", flow_program_list)
            self.assertNotIn("IGNORED", flow_program_list)

    def test_programs_file_reports_missing_programs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            programs_file = temp_root / "programs.txt"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CCP03,program,RPGLE,CCP03.RPGLE,300,complex_normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )
            programs_file.write_text("MISSING\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--programs-file",
                    str(programs_file),
                    "--out-dir",
                    str(out_dir),
                    "--delivery-root",
                    "/tmp/delivery",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not found in program-list.csv: MISSING", result.stderr)

    def test_status_validator_requires_routine_details_for_normal_program(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            batch_dir = temp_root / "batch"
            output_dir = temp_root / "delivery" / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            batch_dir.mkdir()
            output_dir.mkdir(parents=True)
            (batch_dir / "batch-scan-manifest.yaml").write_text("programs: []\n", encoding="utf-8")
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason,batch_status,validator_status,output_dir,prompt_path,owner,session_id,started_at,completed_at,last_error,next_action,handoff_path",
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test,completed,pass,modules/CAP-ID-0003-normal_program/CC050,,,,,,,,",
                    ]
                ),
                encoding="utf-8",
            )
            for artifact in (
                "program-analysis.md",
                "source-index.yaml",
                "program-analysis-summary.yaml",
                "routine-index.md",
                "message-inventory.yaml",
            ):
                (output_dir / artifact).write_text("ok\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("routine-logic-details.md", result.stdout)
            self.assertIn("routine-logic-details.yaml", result.stdout)


if __name__ == "__main__":
    unittest.main()
