from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = (
    REPO_ROOT / "skills" / "legacy-ibmi-program-list-batch" / "scripts"
)
INITIALIZER = SCRIPT_DIR / "initialize_program_batch.ps1"
STATUS_VALIDATOR = SCRIPT_DIR / "validate_program_batch_status.ps1"
ROUTER = REPO_ROOT / "scripts" / "invoke-windows-tool.ps1"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


def run_powershell(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    if POWERSHELL is None:
        raise RuntimeError("PowerShell runtime unavailable")
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *arguments,
        ],
        text=True,
        capture_output=True,
    )


class ProgramListBatchPowerShellContractTests(unittest.TestCase):
    def test_native_scripts_exist_and_do_not_delegate_to_python(self) -> None:
        for script in (INITIALIZER, STATUS_VALIDATOR):
            self.assertTrue(script.is_file(), script)
            text = script.read_text(encoding="utf-8")
            self.assertIn("#requires -version 5.1", text.lower())
            self.assertNotIn("invoke-windows-python", text.lower())
            self.assertIsNone(re.search(r"(?im)^\s*&\s*(?:py|python)\b", text))
            self.assertNotIn("start-process python", text.lower())

        initializer_text = INITIALIZER.read_text(encoding="utf-8")
        self.assertIn("exit 0", initializer_text)
        self.assertIn("scaffoldmode", initializer_text.lower())
        self.assertIn("scaffold_status", initializer_text)
        self.assertIn("index-rpg-source.ps1", initializer_text)

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_router_uses_native_fallback_when_both_python_launchers_fail(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command shims require a Windows host")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shims = root / "shims"
            shims.mkdir()
            for command in ("py.cmd", "python.cmd"):
                (shims / command).write_text("@exit /b 9009\r\n", encoding="ascii")
            program_list = root / "program-list.csv"
            out_dir = root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment["PATH"] = str(shims) + os.pathsep + environment.get("PATH", "")

            result = subprocess.run(
                [
                    str(POWERSHELL),
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROUTER),
                    "InitializeProgramBatch",
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(out_dir),
                ],
                text=True,
                capture_output=True,
                env=environment,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("Initialized program batch:", result.stdout)
            self.assertTrue((out_dir / "program-list-status.csv").is_file())

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_initializer_generates_resumable_batch_without_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            program_list = root / "program-list.csv"
            programs_file = root / "programs.txt"
            out_dir = root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CCP03,program,RPGLE,CCP03.RPGLE,300,complex_normal_program,test",
                        "@CU400P,program,CLLE,@CU400P.CLLE,100,normal_program,test",
                        "COPY01,copybook,RPGLE,COPY01.RPGLE,20,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )
            programs_file.write_text("@CU400P -> CCP03\n", encoding="utf-8")

            result = run_powershell(
                INITIALIZER,
                "--program-list",
                str(program_list),
                "--programs-file",
                str(programs_file),
                "--out-dir",
                str(out_dir),
                "--source-root",
                r"C:\source",
                "--delivery-root",
                r"C:\delivery",
                "--reference-path",
                r"C:\evidence\messages.csv",
                "--control-file",
                r"C:\evidence\codes.csv",
                "--review-name",
                "PowerShell fallback test",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("Initialized program batch:", result.stdout)
            self.assertEqual(
                sorted(path.name for path in (out_dir / "prompt-queue").glob("*.md")),
                ["0001-@CU400P.md", "0002-CCP03.md"],
            )
            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["member"] for row in rows], ["@CU400P", "CCP03"])
            self.assertEqual(rows[0]["batch_status"], "queued")
            self.assertEqual(rows[0]["validator_status"], "not_run")
            self.assertEqual(
                rows[0]["output_dir"],
                r"C:\delivery\modules\CAP-ID-0003-normal_program\@CU400P",
            )
            prompt = (out_dir / "prompt-queue" / "0001-@CU400P.md").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn(r"C:\evidence\messages.csv", prompt)
            self.assertIn(r"C:\evidence\codes.csv", prompt)
            manifest = (out_dir / "batch-scan-manifest.yaml").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("status: initialized", manifest)
            self.assertIn("member: @CU400P", manifest)

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_initializer_supports_deferred_validation_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            program_list = root / "program-list.csv"
            out_dir = root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_powershell(
                INITIALIZER,
                "--program-list",
                str(program_list),
                "--out-dir",
                str(out_dir),
                "--delivery-root",
                r"C:\delivery",
                "--validation-mode",
                "deferred",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            prompt = (out_dir / "prompt-queue" / "0001-CC050.md").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("Skip the program-analysis validator in this batch prompt", prompt)
            self.assertIn("batch_status=scanned_unvalidated", prompt)
            self.assertIn("validator_status=deferred", prompt)
            self.assertIn("Deferred in this batch prompt. Do not run this command now.", prompt)
            manifest = (out_dir / "batch-scan-manifest.yaml").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("validation_mode: deferred", manifest)

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_initializer_supports_scaffold_precreate_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            delivery_root = root / "delivery"
            out_dir = root / "batch"
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
            program_list = root / "program-list.csv"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "SIMPLE,program,RPGLE,SIMPLE.RPGLE,7,normal_program,test",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_powershell(
                INITIALIZER,
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
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            output_dir = delivery_root / "modules" / "CAP-ID-0003-normal_program" / "SIMPLE"
            self.assertTrue((output_dir / "SIMPLE-program-analysis.md").is_file())
            self.assertTrue((output_dir / "SIMPLE-source-index.yaml").is_file())
            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["batch_status"], "queued")
            self.assertEqual(row["scaffold_status"], "present")
            self.assertEqual(row["next_action"], "fill details from scaffold")
            prompt = (out_dir / "prompt-queue" / "0001-SIMPLE.md").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("Scaffold artifacts were precreated during batch initialization", prompt)
            manifest = (out_dir / "batch-scan-manifest.yaml").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("scaffold_mode: precreate", manifest)
            self.assertIn("scaffold_status: present", manifest)

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_status_validator_enforces_completed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch_dir = root / "batch"
            output_dir = root / "delivery" / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            batch_dir.mkdir()
            output_dir.mkdir(parents=True)
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "CC050,completed,pass,modules/CAP-ID-0003-normal_program/CC050,,,,",
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

            result = run_powershell(
                STATUS_VALIDATOR,
                "-BatchDir",
                str(batch_dir),
                "-DeliveryRoot",
                str(root / "delivery"),
            )

            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("CC050-routine-logic-details.md", result.stdout)
            self.assertIn("CC050-routine-logic-details.yaml", result.stdout)

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_status_validator_rejects_completed_placeholder_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch_dir = root / "batch"
            output_dir = root / "delivery" / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            batch_dir.mkdir()
            output_dir.mkdir(parents=True)
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "CC050,completed,pass,modules/CAP-ID-0003-normal_program/CC050,,,,",
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
                "CC050-source-index.yaml": "ok\n",
                "CC050-program-analysis-summary.yaml": "ok\n",
                "CC050-routine-index.md": "ok\n",
                "CC050-message-inventory.yaml": "ok\n",
                "CC050-routine-logic-details.yaml": "ok\n",
            }
            for artifact, text in artifact_text.items():
                (output_dir / artifact).write_text(text, encoding="utf-8")

            result = run_powershell(
                STATUS_VALIDATOR,
                "-BatchDir",
                str(batch_dir),
                "-DeliveryRoot",
                str(root / "delivery"),
            )

            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("CC050-program-analysis.md still appears to be a scaffold", result.stdout)
            self.assertIn("CC050-routine-logic-details.md still appears to be a scaffold", result.stdout)

    @unittest.skipIf(POWERSHELL is None, "PowerShell is not installed on this host")
    def test_status_validator_accepts_scanned_unvalidated_deferred_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch_dir = root / "batch"
            output_dir = root / "delivery" / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            batch_dir.mkdir()
            output_dir.mkdir(parents=True)
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "CC050,scanned_unvalidated,deferred,modules/CAP-ID-0003-normal_program/CC050,,,,run final validation",
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

            result = run_powershell(
                STATUS_VALIDATOR,
                "-BatchDir",
                str(batch_dir),
                "-DeliveryRoot",
                str(root / "delivery"),
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
