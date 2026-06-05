from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "index_rpg_source.py"
)
WRAPPER_SCRIPT_PATH = REPO_ROOT / "scripts" / "index-rpg-source.py"


def load_indexer():
    spec = importlib.util.spec_from_file_location("index_rpg_source", CANONICAL_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load indexer: {CANONICAL_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SAMPLE_RPG = """H DFTACTGRP(*NO)
FCUSTPF    UF   E           K DISK
FAUTHLOG   O    E             DISK
DCL-F MSGDSPF WORKSTN;
C                   EXSR      SR100
C                   CALL      'AUTHREQ'
C                   SETON                                        LR
C     SR100         BEGSR
C     CUSTID        CHAIN     CUSTPF
C                   IF        %FOUND(CUSTPF)
C                   EVAL      AUTHSTS = 'P'
C                   UPDATE    CUSTREC
C                   ENDIF
C                   ENDSR
DCL-PROC SR200;
  SNDPGMMSG MSGID(UCC1852);
END-PROC;
"""


class RpgSourceIndexerTests(unittest.TestCase):
    def test_analyze_source_extracts_structure_without_business_summary(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            SAMPLE_RPG.splitlines(),
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        self.assertEqual(source_index["program"], "CU106")
        self.assertEqual(source_index["source"]["line_count"], 17)
        self.assertIn("SR100", {routine["name"] for routine in source_index["routines"]})
        self.assertIn("SR200", {routine["name"] for routine in source_index["routines"]})
        self.assertIn("AUTHREQ", {call["target"] for call in source_index["external_calls"]})
        self.assertIn("CUSTPF", {operation["object"] for operation in source_index["file_operations"]})
        self.assertIn("UCC1852", {message["code"] for message in source_index["messages"]})

        sr100 = next(routine for routine in source_index["routines"] if routine["name"] == "SR100")
        self.assertEqual(sr100["coverage"], "indexed_only")
        self.assertTrue(sr100["recommended_deep_read"])
        self.assertIn("state-changing file operation", sr100["deep_read_reasons"])

    def test_cli_writes_large_program_artifacts(self) -> None:
        large_source = SAMPLE_RPG + "\n".join("* filler" for _ in range(10000))

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_path = tmp_path / "CU106.rpgle"
            output_dir = tmp_path / "analysis"
            source_path.write_text(large_source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(WRAPPER_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU106",
                    "--out-dir",
                    str(output_dir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in (
                "source-index.yaml",
                "routine-index.md",
                "all-routine-coverage-ledger.md",
                "deep-read-plan.md",
            ):
                self.assertTrue((output_dir / name).exists(), name)

            source_index = (output_dir / "source-index.yaml").read_text(encoding="utf-8")
            self.assertIn("analysis_mode: large_program", source_index)
            self.assertIn("program: CU106", source_index)

            deep_read_plan = (output_dir / "deep-read-plan.md").read_text(encoding="utf-8")
            self.assertIn("| SR100 |", deep_read_plan)
            self.assertIn("state-changing file operation", deep_read_plan)


if __name__ == "__main__":
    unittest.main()
