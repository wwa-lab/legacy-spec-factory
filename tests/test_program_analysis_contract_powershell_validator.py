from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_MODULE_PATH = REPO_ROOT / "tests" / "test_program_analysis_contract_validator.py"
FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "program_analysis_contract_fixtures", FIXTURE_MODULE_PATH
)
if FIXTURE_SPEC is None or FIXTURE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load fixture module: {FIXTURE_MODULE_PATH}")
fixtures = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(fixtures)

SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "validate-program-analysis-contract.ps1"
)
MODULE_DIR = SCRIPT_PATH.parent / "powershell"
MODULE_PATHS = (
    MODULE_DIR / "ProgramAnalysisContract.Common.psm1",
    MODULE_DIR / "ProgramAnalysisContract.Validation.psm1",
)
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


def write_passing_artifacts(path: Path) -> None:
    fixtures.write_common_artifacts(path)
    (path / "program-analysis.md").write_text(
        fixtures.full_program_analysis(), encoding="utf-8"
    )
    (path / "routine-logic-details.md").write_text(
        fixtures.routine_markdown(), encoding="utf-8"
    )


@unittest.skipUnless(POWERSHELL, "PowerShell runtime is not installed")
class ProgramAnalysisPowerShellValidatorRuntimeTests(unittest.TestCase):
    def run_validator(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(POWERSHELL),
                "-NoProfile",
                "-File",
                str(SCRIPT_PATH),
                *arguments,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_passes_existing_complete_fixture_with_gnu_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Program analysis contract validation passed.", result.stdout)

    def test_reports_existing_unresolved_message_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            (analysis_dir / "message-inventory.yaml").write_text(
                fixtures.message_yaml(), encoding="utf-8"
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("message descriptions unresolved", result.stderr)
        self.assertIn("UCC1852", result.stderr)

    def test_missing_required_argument_is_runtime_usage_error(self) -> None:
        result = self.run_validator()

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("--analysis-dir is required", result.stderr)

    def test_existing_negative_fixture_matrix_matches_contract_gates(self) -> None:
        cases = (
            (
                "placeholder reading summary",
                fixtures.program_analysis_with_placeholder_reading_summary,
                "Program Reading Summary",
            ),
            (
                "missing core theme",
                fixtures.program_analysis_without_core_theme_section,
                "theme subsection",
            ),
            (
                "missing main RLOG",
                fixtures.program_analysis_without_main_rlog_detail,
                "RLOG-CU650-042",
            ),
            (
                "placeholder main RLOG",
                fixtures.program_analysis_with_placeholder_main_rlog_detail,
                "reader-useful detail",
            ),
            (
                "stale gap wording",
                fixtures.program_analysis_with_stale_gap_wording,
                "stale deep-read gap wording",
            ),
        )
        for label, program_factory, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                analysis_dir = Path(temp_dir)
                write_passing_artifacts(analysis_dir)
                (analysis_dir / "program-analysis.md").write_text(
                    program_factory(), encoding="utf-8"
                )
                result = self.run_validator("--analysis-dir", str(analysis_dir))

                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(expected, result.stderr)

    def test_detects_triggered_sidecar_and_large_batch_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            (analysis_dir / "program-analysis-summary.yaml").write_text(
                fixtures.summary_yaml(
                    optional_file_io_status="optional_triggered",
                    program_size_tier="large_extreme_program",
                    line_count=12001,
                ),
                encoding="utf-8",
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("file_io_inventory", result.stderr)
        self.assertIn("large_extreme_program requires", result.stderr)

    def test_detects_batch_source_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.md").write_text(
                fixtures.final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "deep-read-batch-001.md").write_text(
                fixtures.deep_read_batch_with_code_snippet(), encoding="utf-8"
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("must not contain fenced source/code blocks", result.stderr)
        self.assertIn("source-code-like snippet", result.stderr)


class ProgramAnalysisPowerShellValidatorStaticTests(unittest.TestCase):
    def test_entry_and_modules_are_present_and_powershell_51_compatible(self) -> None:
        for path in (SCRIPT_PATH, *MODULE_PATHS):
            text = path.read_text(encoding="utf-8")
            self.assertIn("#requires -version 5.1", text, path)
            self.assertLessEqual(len(text.splitlines()), 800, path)

    def test_entry_accepts_router_gnu_argument_names(self) -> None:
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("--analysis-dir", text)
        self.assertIn("--program-analysis", text)
        self.assertIn("ProgramAnalysisContract.Validation.psm1", text)

    def test_native_fallback_does_not_execute_python(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (SCRIPT_PATH, *MODULE_PATHS)
        )
        python_command = re.compile(
            r"^\s*(?:&\s*)?(?:py|python)(?:\.exe)?\b", re.IGNORECASE | re.MULTILINE
        )
        self.assertIsNone(python_command.search(combined))
        self.assertNotIn("ConvertFrom-Yaml", combined)


if __name__ == "__main__":
    unittest.main()
