from __future__ import annotations

import csv
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
    / "legacy-ibmi-inventory"
    / "scripts"
    / "scan_ibmi_repo.py"
)
WRAPPER_SCRIPT_PATH = REPO_ROOT / "scripts" / "scan-ibmi-repo.py"


def load_scanner():
    spec = importlib.util.spec_from_file_location("scan_ibmi_repo", CANONICAL_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load scanner: {CANONICAL_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["scan_ibmi_repo"] = module
    spec.loader.exec_module(module)
    return module


class IbmiRepoScannerTests(unittest.TestCase):
    def test_scan_repository_counts_programs_and_large_candidates(self) -> None:
        scanner = load_scanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "QRPGLESRC").mkdir()
            (root / "QDDSSRC").mkdir()
            (root / ".git").mkdir()
            (root / "QRPGLESRC" / "SMALL.RPGLE").write_text(
                "\n".join(
                    [
                        "H DFTACTGRP(*NO)",
                        "C                   EVAL      RESULT = 'Y'",
                        "C* comment",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "QRPGLESRC" / "BIG.SQLRPGLE").write_text(
                "\n".join(["**free", "exec sql select * from CUSTMAST;"] + ["// filler"] * 10000),
                encoding="utf-8",
            )
            (root / "QDDSSRC" / "CUSTPF.PF").write_text(
                "\n".join(["A          R CUSTREC", "A            CUSTNO         10A"]),
                encoding="utf-8",
            )
            (root / ".git" / "IGNORED.RPGLE").write_text("C EVAL X = Y\n", encoding="utf-8")

            members = scanner.scan_repository(root, large_threshold=10, exclude_dirs=scanner.DEFAULT_EXCLUDE_DIRS)
            by_member = {member.member: member for member in members}

            self.assertEqual(set(by_member), {"SMALL", "BIG", "CUSTPF"})
            self.assertEqual(by_member["BIG"].size_tier, "large_extreme_program")
            self.assertEqual(by_member["BIG"].classification_source, "legacy-ibmi-program-analyzer")
            self.assertEqual(by_member["BIG"].default_output_profile, "full_index_and_batched_deep_read")
            self.assertIn("source length exceeds 10,000 lines", by_member["BIG"].tier_reason)
            self.assertEqual(by_member["BIG"].object_type, "program")
            self.assertEqual(by_member["CUSTPF"].object_type, "dds_object")
            self.assertEqual(by_member["CUSTPF"].size_tier, "non_program_source")
            self.assertEqual(by_member["SMALL"].code_lines, 2)
            self.assertEqual(by_member["SMALL"].comment_lines, 1)

    def test_wrapper_cli_writes_program_list_and_candidate_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "source"
            out_dir = Path(temp_dir) / "out"
            root.mkdir()
            (root / "ORDER.RPGLE").write_text("\n".join(["H DFTACTGRP(*NO)"] * 10001), encoding="utf-8")
            (root / "SUPPORT.CLLE").write_text("PGM\nENDPGM\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(WRAPPER_SCRIPT_PATH),
                    str(root),
                    "--out-dir",
                    str(out_dir),
                    "--large-threshold",
                    "10",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("program-list.csv", result.stdout)
            self.assertTrue((out_dir / "program-list.csv").exists())
            self.assertTrue((out_dir / "large-program-candidates.md").exists())
            self.assertTrue((out_dir / "scan-summary.yaml").exists())

            with (out_dir / "program-list.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["member"] for row in rows], ["ORDER", "SUPPORT"])
            self.assertEqual(rows[0]["size_tier"], "large_extreme_program")
            self.assertEqual(rows[0]["classification_source"], "legacy-ibmi-program-analyzer")
            self.assertEqual(rows[1]["size_tier"], "normal_program")
            self.assertEqual(rows[1]["classification_source"], "repo_scanner_line_count_fallback")

            report = (out_dir / "large-program-candidates.md").read_text(encoding="utf-8")
            self.assertIn("# Program Tier Report", report)
            self.assertIn("## large_extreme_program", report)
            self.assertIn("source length exceeds 10,000 lines", report)
            summary = (out_dir / "scan-summary.yaml").read_text(encoding="utf-8")
            self.assertIn("large_extreme_program: 1", summary)
            self.assertIn("normal_program: 1", summary)
            self.assertIn("source_revision:", summary)
            self.assertIn("source_revision_key:", summary)
            self.assertIn("type: filesystem", summary)


if __name__ == "__main__":
    unittest.main()
