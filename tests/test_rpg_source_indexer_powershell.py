from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "index-rpg-source.ps1"
)
MODULE_ROOT = ENTRY.parent / "powershell"


SAMPLE_RPG = """H DFTACTGRP(*NO)
FCUSTPF    UF   E           K DISK
C                   EXSR      SR100
C                   CALL      'AUTHREQ'
C     SR100         BEGSR
C     CUSTID        CHAIN     CUSTPF
C                   IF        %FOUND(CUSTPF)
C                   EVAL      AUTHSTS = 'P'
C                   UPDATE    CUSTREC
C                   SNDPGMMSG MSGID(UCC1852)
C                   ENDIF
C     SR100E        ENDSR
"""


class PowerShellRpgSourceIndexerTests(unittest.TestCase):
    def test_native_entry_is_python_independent_and_keeps_gnu_cli(self) -> None:
        text = ENTRY.read_text(encoding="utf-8")

        self.assertIn("#requires -version 5.1", text)
        self.assertIn("IndexerCore.psm1", text)
        self.assertIn("IndexerAnalysis.psm1", text)
        self.assertIn("IndexerArtifacts.psm1", text)
        self.assertNotIn("& py ", text)
        self.assertNotIn("& python ", text)

        core = (MODULE_ROOT / "IndexerCore.psm1").read_text(encoding="utf-8")
        for option in (
            "--program",
            "--out-dir",
            "--delivery-root",
            "--delivery-profile",
            "--force-rescan",
            "--rescan-reason",
            "--preserve-existing",
            "--canonical-artifact-names",
        ):
            self.assertIn(option, core)

        artifact_writer = (MODULE_ROOT / "IndexerArtifacts.psm1").read_text(
            encoding="utf-8"
        )
        self.assertIn("CanonicalArtifactNames", artifact_writer)
        self.assertIn("PreserveExisting", artifact_writer)
        self.assertIn("Get-IndexerArtifactName", artifact_writer)

    def test_focused_modules_stay_below_repository_file_limit(self) -> None:
        for path in MODULE_ROOT.glob("Indexer*.psm1"):
            with self.subTest(path=path.name):
                self.assertLess(len(path.read_text(encoding="utf-8").splitlines()), 800)

    def test_artifact_module_declares_core_and_tiered_outputs(self) -> None:
        text = (MODULE_ROOT / "IndexerArtifacts.psm1").read_text(encoding="utf-8")
        for artifact in (
            "program-analysis.md",
            "source-index.yaml",
            "program-analysis-summary.yaml",
            "routine-index.md",
            "routine-logic-details.md",
            "routine-logic-details.yaml",
            "message-inventory.yaml",
            "file-io-inventory.yaml",
            "field-mutation-matrix.yaml",
            "sql-inventory.yaml",
            "routine-logic-details/deep-read-batch-",
            "deep-read-execution-plan.yaml",
        ):
            self.assertIn(artifact, text)
        self.assertIn("New-DeepReadExecutionPlan", text)
        self.assertIn("source_index_sha256", text)
        self.assertIn("planned_deep_read", text)

    def test_native_indexer_smoke_when_powershell_is_available(self) -> None:
        executable = shutil.which("powershell") or shutil.which("pwsh")
        if executable is None:
            self.skipTest("PowerShell runtime is unavailable on this development host")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "CU106.RPGLE"
            output = temp / "analysis"
            source.write_text(SAMPLE_RPG, encoding="utf-8")

            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-File",
                    str(ENTRY),
                    str(source),
                    "--program",
                    "CU106",
                    "--out-dir",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for artifact in (
                "program-analysis.md",
                "source-index.yaml",
                "program-analysis-summary.yaml",
                "routine-index.md",
                "routine-logic-details.md",
                "routine-logic-details.yaml",
                "message-inventory.yaml",
            ):
                self.assertTrue((output / artifact).is_file(), artifact)
            source_index = (output / "source-index.yaml").read_text(encoding="utf-8")
            self.assertIn("program: CU106", source_index)
            self.assertIn("program_size_tier: normal_program", source_index)
            self.assertIn("name: SR100", source_index)
            self.assertIn("target: AUTHREQ", source_index)
            self.assertIn("code: UCC1852", source_index)

    def test_native_indexer_uses_delivery_lookup_profile_section(self) -> None:
        executable = shutil.which("powershell") or shutil.which("pwsh")
        if executable is None:
            self.skipTest("PowerShell runtime is unavailable on this development host")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "cu106.RPGLE"
            output = temp / "analysis"
            delivery = temp / "delivery"
            wrong = delivery / "wrong" / "CU106"
            approved = delivery / "approved" / "CU106"
            wrong.mkdir(parents=True)
            approved.mkdir(parents=True)
            (approved / "program-analysis.md").write_text("approved\n", encoding="utf-8")
            source.write_text(SAMPLE_RPG, encoding="utf-8")
            profile = temp / "delivery-profile.yaml"
            profile.write_text(
                """program_artifact_resolution_profile:
  program_folder_patterns:
    - wrong/{PROGRAM}
delivery_artifact_lookup_profile:
  program_folder_patterns:
    - approved/{PROGRAM}
  program_name_normalization:
    case: upper
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    executable,
                    "-NoProfile",
                    "-File",
                    str(ENTRY),
                    str(source),
                    "--program",
                    "cu106",
                    "--out-dir",
                    str(output),
                    "--delivery-root",
                    str(delivery),
                    "--delivery-profile",
                    str(profile),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("central_lookup_result: found_on_remote_main", result.stdout)
            self.assertIn("approved/CU106", result.stdout.replace("\\", "/"))
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
