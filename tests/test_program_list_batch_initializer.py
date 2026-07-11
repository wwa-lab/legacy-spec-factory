from __future__ import annotations

import csv
import json
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
MERGE_SUBAGENT_RESULTS = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-list-batch"
    / "scripts"
    / "merge_subagent_results.py"
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
            self.assertIn("@CU400P-program-analysis.md", prompt_text)
            self.assertIn("@CU400P-routine-logic-details.md", prompt_text)
            self.assertIn("@CU400P-routine-logic-details.yaml", prompt_text)
            self.assertIn(
                "py -3 .agents\\skills\\legacy-ibmi-program-analyzer\\scripts\\validate_program_analysis_contract.py "
                "--analysis-dir",
                prompt_text,
            )
            self.assertIn("Retry / exit budget", prompt_text)
            self.assertIn("Deterministic indexes are pre-analysis scaffolds only", prompt_text)
            self.assertIn("Do not stop after deterministic indexing", prompt_text)
            self.assertIn("Every RLOG declared in @CU400P-routine-logic-details.yaml", prompt_text)
            self.assertIn("Cline may show its own bounded Auto-Retry", prompt_text)
            self.assertIn("batch_status=failed_runtime", prompt_text)
            self.assertIn("cline_auto_retry_exhausted", prompt_text)
            self.assertIn("batch_status=failed_validator", prompt_text)
            self.assertIn("at most one targeted repair pass", prompt_text)
            self.assertIn("Do not create ad hoc `_generate_*_batch.py`", prompt_text)
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

    def test_deferred_validation_prompt_marks_scanned_unvalidated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test",
                    ]
                ),
                encoding="utf-8",
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
                    "/tmp/source",
                    "--delivery-root",
                    "/tmp/delivery",
                    "--validation-mode",
                    "deferred",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            prompt_text = (out_dir / "prompt-queue" / "0001-CC050.md").read_text(encoding="utf-8")
            self.assertIn("Skip the program-analysis validator in this batch prompt", prompt_text)
            self.assertIn("batch_status=scanned_unvalidated", prompt_text)
            self.assertIn("validator_status=deferred", prompt_text)
            self.assertIn("Deferred in this batch prompt. Do not run this command now.", prompt_text)
            self.assertIn("Run before downstream use or final handoff", prompt_text)

            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn("- Validation mode: deferred", plan_text)
            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("validation_mode: deferred", manifest_text)

    def test_scaffold_mode_precreates_program_scaffold_before_prompt_fill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            out_dir = temp_root / "batch"
            source_root.mkdir()
            (source_root / "SIMPLE.RPGLE").write_text(
                "\n".join(
                    [
                        "H DFTACTGRP(*NO)",
                        "C     *ENTRY        PLIST",
                        "C                   EXSR      SR100",
                        "C                   SETON                                        LR",
                        "C     SR100         BEGSR",
                        "C                   EVAL      RESULT = 'Y'",
                        "C                   ENDSR",
                    ]
                ),
                encoding="utf-8",
            )
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "SIMPLE,program,RPGLE,SIMPLE.RPGLE,7,normal_program,test",
                    ]
                ),
                encoding="utf-8",
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
                    str(source_root),
                    "--delivery-root",
                    str(delivery_root),
                    "--scaffold-mode",
                    "precreate",
                    "--validation-mode",
                    "deferred",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            output_dir = delivery_root / "modules" / "CAP-ID-0003-normal_program" / "SIMPLE"
            self.assertTrue((output_dir / "SIMPLE-program-analysis.md").is_file())
            self.assertTrue((output_dir / "SIMPLE-source-index.yaml").is_file())
            self.assertTrue((output_dir / "SIMPLE-routine-logic-details.yaml").is_file())

            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["batch_status"], "queued")
            self.assertEqual(row["scaffold_status"], "present")
            self.assertEqual(row["next_action"], "fill details from scaffold")

            prompt_text = (out_dir / "prompt-queue" / "0001-SIMPLE.md").read_text(encoding="utf-8")
            self.assertIn("Scaffold artifacts were precreated during batch initialization", prompt_text)
            self.assertIn("Start by reading the existing source index", prompt_text)

            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("scaffold_mode: precreate", manifest_text)
            self.assertIn("scaffold_status: present", manifest_text)

    def test_subagent_mode_prepares_parallel_worker_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test",
                        "CC051,program,RPGLE,CC051.RPGLE,110,normal_program,test",
                        "COPY01,copybook,RPGLE,COPY01.RPGLE,20,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(out_dir),
                    "--source-root",
                    "/tmp/source",
                    "--delivery-root",
                    "/tmp/delivery",
                    "--validation-mode",
                    "deferred",
                    "--subagent-mode",
                    "prepare",
                    "--max-parallel-agents",
                    "2",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Cline serial Step 2 prompt:", result.stdout)
            self.assertIn("Kiro/agent worker prompt files: 2", result.stdout)
            self.assertIn("Kiro/agent parallel Step 2 prompt:", result.stdout)
            self.assertEqual(
                sorted(path.name for path in (out_dir / "subagent-queue").glob("*.md")),
                ["0001-CC050.md", "0002-CC051.md"],
            )
            serial_prompt = (out_dir / "cline-serial-runner-prompt.md").read_text(
                encoding="utf-8"
            )
            self.assertFalse((out_dir / "cline-parallel-runner-prompt.md").exists())
            self.assertIn("你是运行在 Cline 中的串行 batch 执行器", serial_prompt)
            self.assertIn("不要读取 `subagent-queue`", serial_prompt)
            self.assertIn("不要设置 3/5/10 个 program 之类的自我停止上限", serial_prompt)
            self.assertIn("不要仅仅因为上下文变长", serial_prompt)
            self.assertIn("只有遇到硬性阻断才允许停止", serial_prompt)
            self.assertIn("不要把尚未执行的后续 program 标记为 failed", serial_prompt)
            self.assertIn("prompt-queue", serial_prompt)
            self.assertTrue((out_dir / "subagent-results").is_dir())
            subagent_prompt = (out_dir / "subagent-queue" / "0001-CC050.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Do not edit these shared batch files directly", subagent_prompt)
            self.assertIn("program-list-status.csv", subagent_prompt)
            self.assertIn("CC050.result.json", subagent_prompt)
            self.assertIn("Embedded Per-Program Prompt", subagent_prompt)

            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                Path(rows[0]["subagent_prompt_path"]).resolve(),
                (out_dir / "subagent-queue" / "0001-CC050.md").resolve(),
            )
            self.assertEqual(
                Path(rows[0]["subagent_result_path"]).resolve(),
                (out_dir / "subagent-results" / "0001-CC050.result.json").resolve(),
            )
            self.assertEqual(rows[2]["batch_status"], "skipped_not_program")
            self.assertEqual(rows[2]["subagent_prompt_path"], "")

            dispatch_plan = (out_dir / "subagent-dispatch-plan.md").read_text(encoding="utf-8")
            self.assertIn("- Recommended max parallel workers: 2", dispatch_plan)
            self.assertIn("merge_subagent_results.py --batch-dir", dispatch_plan)
            self.assertIn("kiro-parallel-runner-prompt.md", dispatch_plan)
            self.assertIn("Do not run this plan in Cline", dispatch_plan)
            kiro_prompt = (out_dir / "kiro-parallel-runner-prompt.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("你是运行在 Kiro 或支持隔离 worker", kiro_prompt)
            self.assertIn("这个 prompt 不给 Cline 使用", kiro_prompt)
            self.assertIn("最大并发 worker 数", kiro_prompt)
            self.assertIn("subagent-queue", kiro_prompt)
            self.assertIn("merge_subagent_results.py", kiro_prompt)
            self.assertIn("validate_program_batch_status.py", kiro_prompt)
            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn("cline-serial-runner-prompt.md", plan_text)
            self.assertIn("- Sub-agent mode: prepare", plan_text)
            self.assertIn("- Max parallel agents: 2", plan_text)
            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("cline_serial_runner_prompt:", manifest_text)
            self.assertIn("kiro_parallel_runner_prompt:", manifest_text)
            self.assertIn("subagent_mode: prepare", manifest_text)
            self.assertIn("max_parallel_agents: 2", manifest_text)
            self.assertIn("subagent_dispatch_plan:", manifest_text)
            self.assertIn('cline_parallel_runner_prompt: ""', manifest_text)

    def test_merge_subagent_results_updates_status_plan_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test",
                        "CC051,program,RPGLE,CC051.RPGLE,110,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(out_dir),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                    "--validation-mode",
                    "deferred",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            result_path = out_dir / "subagent-results" / "0001-CC050.result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "member": "CC050",
                        "batch_status": "scanned_unvalidated",
                        "validator_status": "deferred",
                        "completed_at": "2026-07-11T00:00:00+00:00",
                        "last_error": "",
                        "next_action": "run program-analysis validator before downstream use",
                        "output_dir": str(temp_root / "delivery" / "modules" / "CAP-ID-0003-normal_program" / "CC050"),
                        "artifacts": ["CC050-program-analysis.md"],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(MERGE_SUBAGENT_RESULTS),
                    "--batch-dir",
                    str(out_dir),
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Merged sub-agent result files: 1", result.stdout)
            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["batch_status"], "scanned_unvalidated")
            self.assertEqual(rows[0]["validator_status"], "deferred")
            self.assertEqual(rows[0]["session_id"], "0001-CC050.result")
            self.assertEqual(rows[1]["batch_status"], "queued")

            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn("| scanned_unvalidated | 1 |", plan_text)
            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("status: subagent_results_merged", manifest_text)
            self.assertIn("merged_result_count: 1", manifest_text)
            self.assertIn("batch_status: scanned_unvalidated", manifest_text)

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
                "CC050-program-analysis.md",
                "CC050-source-index.yaml",
                "CC050-program-analysis-summary.yaml",
                "CC050-routine-index.md",
                "CC050-message-inventory.yaml",
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
            self.assertIn("CC050-routine-logic-details.md", result.stdout)
            self.assertIn("CC050-routine-logic-details.yaml", result.stdout)

    def test_status_validator_rejects_completed_placeholder_scaffold(self) -> None:
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
            artifact_text = {
                "CC050-program-analysis.md": (
                    "# Program Analysis: CC050\n\n"
                    "Draft wrapper seed generated by deterministic indexing.\n\n"
                    "## Program Reading Summary\n\n"
                    "pending semantic deep-read\n"
                ),
                "CC050-routine-logic-details.md": (
                    "# Routine Logic Details: CC050\n\n"
                    "pending semantic detail\n"
                ),
            }
            for artifact in (
                "CC050-source-index.yaml",
                "CC050-program-analysis-summary.yaml",
                "CC050-routine-index.md",
                "CC050-message-inventory.yaml",
                "CC050-routine-logic-details.yaml",
            ):
                artifact_text[artifact] = "ok\n"
            for artifact, text in artifact_text.items():
                (output_dir / artifact).write_text(text, encoding="utf-8")

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
            self.assertIn("CC050-program-analysis.md still appears to be a scaffold", result.stdout)
            self.assertIn("CC050-routine-logic-details.md still appears to be a scaffold", result.stdout)

    def test_status_validator_allows_review_checklist_placeholder_wording(self) -> None:
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
            artifact_text = {
                "CC050-program-analysis.md": (
                    "# Program Analysis: CC050\n\n"
                    "## Program Reading Summary\n\n"
                    "Reader-first processing context is filled.\n\n"
                    "## Review Checklist\n\n"
                    "- [x] Reader-first golden gate is clean: no pending/placeholder detail remains.\n"
                ),
                "CC050-routine-logic-details.md": (
                    "# Routine Logic Details: CC050\n\n"
                    "RLOG-CC050-001 contains source-backed reader detail.\n"
                ),
                "CC050-source-index.yaml": "ok\n",
                "CC050-program-analysis-summary.yaml": "ok\n",
                "CC050-routine-index.md": "ok\n",
                "CC050-message-inventory.yaml": "ok\n",
                "CC050-routine-logic-details.yaml": "ok\n",
            }
            for artifact, text in artifact_text.items():
                (output_dir / artifact).write_text(text, encoding="utf-8")

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

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_status_validator_accepts_scanned_unvalidated_deferred_row(self) -> None:
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
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test,scanned_unvalidated,deferred,modules/CAP-ID-0003-normal_program/CC050,,,,,,,run final validation",
                    ]
                ),
                encoding="utf-8",
            )
            artifact_text = {
                "CC050-program-analysis.md": "# Program Analysis: CC050\n\nreader-first analysis filled\n",
                "CC050-routine-logic-details.md": "# Routine Logic Details: CC050\n\nRLOG-CC050-001 has detail.\n",
                "CC050-source-index.yaml": "ok\n",
                "CC050-program-analysis-summary.yaml": "ok\n",
                "CC050-routine-index.md": "ok\n",
                "CC050-message-inventory.yaml": "ok\n",
                "CC050-routine-logic-details.yaml": "ok\n",
            }
            for artifact, text in artifact_text.items():
                (output_dir / artifact).write_text(text, encoding="utf-8")

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

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_status_validator_requires_deferred_status_for_scanned_unvalidated(self) -> None:
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
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test,scanned_unvalidated,not_run,modules/CAP-ID-0003-normal_program/CC050,,,,,,,run final validation",
                    ]
                ),
                encoding="utf-8",
            )

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
            self.assertIn("scanned_unvalidated requires validator_status deferred", result.stdout)

    def test_status_contract_documents_cline_retry_exit_state(self) -> None:
        contract_text = (
            REPO_ROOT
            / "skills"
            / "legacy-ibmi-program-list-batch"
            / "references"
            / "status-contract.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Retry And Exit Budget", contract_text)
        self.assertIn("Cline may perform its own bounded Auto-Retry", contract_text)
        self.assertIn("cline_auto_retry_exhausted", contract_text)
        self.assertIn("batch_status=failed_runtime", contract_text)
        self.assertIn("batch_status=failed_validator", contract_text)
        self.assertIn("one targeted", contract_text)


if __name__ == "__main__":
    unittest.main()
