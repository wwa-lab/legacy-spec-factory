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
    MODULE_DIR / "ProgramAnalysisContract.ExecutionPlan.psm1",
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


def write_completed_batch_artifacts(path: Path) -> Path:
    write_passing_artifacts(path)
    (path / "routine-logic-details.md").write_text(
        fixtures.final_routine_markdown(), encoding="utf-8"
    )
    (path / "routine-logic-details.yaml").write_text(
        fixtures.routine_yaml_with_completed_first_batch(), encoding="utf-8"
    )
    batch_dir = path / "routine-logic-details"
    batch_dir.mkdir()
    batch_path = batch_dir / "CU650-deep-read-batch-001.md"
    batch_path.write_text(fixtures.deep_read_batch(), encoding="utf-8")
    return batch_path


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

    def test_detects_pending_consolidated_routine_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.md").write_text(
                fixtures.final_routine_markdown_with_pending_semantic_detail(),
                encoding="utf-8",
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("routine-logic-details.md", result.stderr)
        self.assertIn("pending", result.stderr.lower())

    def test_detects_pending_prefixed_retained_deep_read_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.md").write_text(
                fixtures.final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                fixtures.indexer_pending_deep_read_batch(), encoding="utf-8"
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("CU650-deep-read-batch-001.md", result.stderr)
        self.assertIn("pending", result.stderr.lower())

    def test_detects_pending_semantic_state_in_routine_yaml(self) -> None:
        yaml_cases = (
            (
                "pending_deep_read",
                fixtures.routine_yaml().replace(
                    "      routine: SR001\n",
                    (
                        "      routine: SR001\n"
                        "      semantic_status: pending_deep_read\n"
                    ),
                    1,
                ),
            ),
            (
                "indexed_only",
                fixtures.routine_yaml().replace(
                    "      routine: SR001\n",
                    (
                        "      routine: SR001\n"
                        "      semantic_status: indexed_only\n"
                    ),
                    1,
                ),
            ),
        )
        for marker, yaml_text in yaml_cases:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as temp_dir:
                analysis_dir = Path(temp_dir)
                write_passing_artifacts(analysis_dir)
                (analysis_dir / "routine-logic-details.yaml").write_text(
                    yaml_text, encoding="utf-8"
                )
                result = self.run_validator("--analysis-dir", str(analysis_dir))

                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("routine-logic-details.yaml", result.stderr)
                self.assertIn(marker, result.stderr)

    def test_allows_source_backed_utility_with_indexed_only_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_passing_artifacts(analysis_dir)
            completed_utility_yaml = fixtures.routine_yaml().replace(
                "      routine: SR001\n",
                (
                    "      routine: SR001\n"
                    "      semantic_status: source_backed_complete\n"
                    "      coverage: indexed_only\n"
                    "      execution_trigger: Called from the mainline after input validation.\n"
                    "      unresolved_routine_logic: none\n"
                ),
                1,
            )
            (analysis_dir / "routine-logic-details.yaml").write_text(
                completed_utility_yaml, encoding="utf-8"
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_passes_completed_deep_read_batch_and_structured_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_completed_batch_artifacts(analysis_dir)
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_non_deep_read_state_for_batch_assigned_rlog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_completed_batch_artifacts(analysis_dir)
            yaml_text = fixtures.routine_yaml_with_completed_first_batch()
            yaml_text = yaml_text.replace(
                "semantic_status: deep_read_complete",
                "semantic_status: source_backed_complete",
                2,
            ).replace("coverage: deep_read", "coverage: indexed_only", 2)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                yaml_text, encoding="utf-8"
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("semantic_status: deep_read_complete", result.stderr)
        self.assertIn("coverage: deep_read", result.stderr)

    def test_rejects_summary_details_semantic_state_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_completed_batch_artifacts(analysis_dir)
            yaml_text = fixtures.routine_yaml_with_completed_first_batch().replace(
                "semantic_status: deep_read_complete",
                "semantic_status: source_backed_complete",
                1,
            )
            (analysis_dir / "routine-logic-details.yaml").write_text(
                yaml_text, encoding="utf-8"
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("summary[] and details[] semantic state disagree", result.stderr)

    def test_rejects_batch_with_more_than_five_assigned_windows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            batch_path = write_completed_batch_artifacts(analysis_dir)
            extra_rows = "\n".join(
                f"| DRW-CU650-{number:03d} | MAIN | 1-100 | RLOG-CU650-001 |"
                for number in range(2, 7)
            )
            batch_path.write_text(
                fixtures.deep_read_batch().replace(
                    "| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |",
                    "| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |\n"
                    + extra_rows,
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("more than 5 deep-read routines/windows", result.stderr)

    def test_coverage_notes_cross_references_do_not_expand_batch_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            batch_path = write_completed_batch_artifacts(analysis_dir)
            references = ", ".join(
                f"RLOG-CU650-{number:03d} / DRW-CU650-{number:03d}"
                for number in range(2, 7)
            )
            batch_path.write_text(
                fixtures.deep_read_batch().replace(
                    """| Window ID | Routine | Source Lines | RLOG Detail |
| --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |""",
                    f"""| Window ID | Routine | Source Lines | Why Selected | RLOG Detail |
| --- | --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | Related: {references} | RLOG-CU650-001 |""",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator("--analysis-dir", str(analysis_dir))

        self.assertEqual(result.returncode, 0, result.stderr)


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

    def test_validation_module_covers_retained_semantic_completion_surfaces(self) -> None:
        text = MODULE_PATHS[1].read_text(encoding="utf-8")

        self.assertIn("routine-logic-details.md", text)
        self.assertIn("routine-logic-details.yaml", text)
        self.assertIn("*-deep-read-batch-*.md", text)
        self.assertIn("pending_deep_read", text)
        self.assertIn("indexed_only", text)
        self.assertIn("Get-BatchAssignedWindowIds", text)
        self.assertIn("Get-BatchAssignedRlogIds", text)

    def test_prefixed_artifact_resolution_rejects_decoys_and_mixed_sets(self) -> None:
        common_text = MODULE_PATHS[0].read_text(encoding="utf-8")
        validation_text = MODULE_PATHS[1].read_text(encoding="utf-8")

        self.assertIn("Get-ProgramArtifactResolutionFindings", common_text)
        self.assertIn("both generic", common_text)
        self.assertIn("multiple canonical prefixed artifacts", common_text)
        self.assertIn("legacy suffix artifact(s)", common_text)
        self.assertIn("canonical program artifact prefix mismatch", common_text)
        self.assertIn("mixes prefixed and generic completion artifacts", common_text)
        for artifact in (
            "program-analysis.md",
            "program-analysis-summary.yaml",
            "routine-logic-details.md",
            "routine-logic-details.yaml",
            "message-inventory.yaml",
        ):
            self.assertIn(artifact, common_text)
        self.assertRegex(
            validation_text,
            r"(?s)Get-ProgramArtifactResolutionFindings\s+\$AnalysisDir\s+\$ProgramAnalysis",
        )
        self.assertIn("Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.yaml'", validation_text)
        self.assertIn("Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.md'", validation_text)
        self.assertIn("Find-RoutineArtifactPath $AnalysisDir 'message-inventory.yaml'", validation_text)

    def test_immutable_large_execution_plan_covers_all_planned_batches(self) -> None:
        common_text = MODULE_PATHS[0].read_text(encoding="utf-8")
        validation_text = MODULE_PATHS[1].read_text(encoding="utf-8")
        execution_plan_text = MODULE_PATHS[2].read_text(encoding="utf-8")

        self.assertIn("ProgramAnalysisContract.ExecutionPlan.psm1", validation_text)
        self.assertIn("Validate-LargeExecutionPlanCoverage", validation_text)
        self.assertIn("PlannedRlogIds", validation_text)
        self.assertIn("ExpectedRlogIds", validation_text)
        self.assertIn("Get-YamlListMappings", common_text)
        for required in (
            "deep_read_execution_plan",
            "deep-read-execution-plan.yaml",
            "source_index_sha256",
            "planned_deep_read",
            "Get-BatchWindowRlogPairs",
            "Get-BatchWindowRlogDuplicateFindings",
            "source-index routine_logic_inventory.details",
            "batch is missing",
            "retained batch file(s) not in plan",
            "ExpectedSourceIndexSha256",
            "ExpectedExecutionPlanSha256",
            "immutable batch execution lock",
        ):
            self.assertIn(required, execution_plan_text)
        self.assertIn("--expected-source-index-sha256", (REPO_ROOT / "skills/legacy-ibmi-program-analyzer/scripts/validate-program-analysis-contract.ps1").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
