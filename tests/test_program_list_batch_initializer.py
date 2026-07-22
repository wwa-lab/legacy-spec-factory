from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


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
STATUS_SPEC = importlib.util.spec_from_file_location(
    "program_batch_status_validator", STATUS_VALIDATOR
)
if STATUS_SPEC is None or STATUS_SPEC.loader is None:
    raise RuntimeError(f"Cannot load status validator: {STATUS_VALIDATOR}")
STATUS_MODULE = importlib.util.module_from_spec(STATUS_SPEC)
STATUS_SPEC.loader.exec_module(STATUS_MODULE)
MERGE_SUBAGENT_RESULTS = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-list-batch"
    / "scripts"
    / "merge_subagent_results.py"
)


class ProgramListBatchInitializerTests(unittest.TestCase):
    def test_retained_yaml_seed_patterns_are_key_specific(self) -> None:
        retained_patterns = STATUS_MODULE.RETAINED_SEMANTIC_PATTERNS
        for seed in (
            "semantic_status: indexed_only",
            'semantic_status: "indexed_only"',
            "execution_trigger: pending deep read",
            "execution_trigger: 'pending deep read'",
            "unresolved_routine_logic: pending deep read",
            'unresolved_routine_logic: "pending deep read"',
        ):
            with self.subTest(seed=seed):
                self.assertTrue(
                    STATUS_MODULE.scaffold_patterns_in(seed, retained_patterns), seed
                )

        self.assertEqual(
            STATUS_MODULE.scaffold_patterns_in(
                "coverage: indexed_only",
                retained_patterns,
            ),
            [],
        )
        self.assertEqual(
            STATUS_MODULE.scaffold_patterns_in(
                'coverage: "indexed_only"',
                retained_patterns,
            ),
            [],
        )
        self.assertEqual(STATUS_MODULE.scaffold_patterns_in("| PENDING |"), [])
        self.assertTrue(
            STATUS_MODULE.scaffold_patterns_in("| PENDING |", retained_patterns)
        )

    def test_retained_yaml_seed_patterns_match_multiline_artifacts(self) -> None:
        retained_patterns = STATUS_MODULE.RETAINED_SEMANTIC_PATTERNS
        for artifact in (
            "semantic_status: indexed_only\ncoverage: indexed_only\n",
            'semantic_status: "indexed_only"  # index seed\ncoverage: deep_read\n',
            "execution_trigger: pending deep read\nstep_by_step_logic:\n  - pending\n",
            (
                "unresolved_routine_logic: 'pending deep read'  # seed\n"
                "semantic_status: deep_read_complete\n"
            ),
        ):
            with self.subTest(artifact=artifact):
                self.assertTrue(
                    STATUS_MODULE.scaffold_patterns_in(artifact, retained_patterns),
                    artifact,
                )

        self.assertEqual(
            STATUS_MODULE.scaffold_patterns_in(
                'semantic_status: source_backed_complete\ncoverage: "indexed_only"\n',
                retained_patterns,
            ),
            [],
        )

    def test_large_program_prompt_requires_every_deep_read_batch_before_validation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "SS380,program,RPGLE,SS380.RPGLE,3200,large_extreme_program,test",
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
                    str(temp_root / "source"),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            prompt_text = (out_dir / "prompt-queue" / "0001-SS380.md").read_text(
                encoding="utf-8"
            )
            required_steps = [
                (
                    "Process every existing "
                    "`routine-logic-details/SS380-deep-read-batch-*.md` in natural numeric order"
                ),
                "Deep-read no more than 5 source windows per batch",
                "Persist each completed batch file before starting the next batch",
                (
                    "Update `SS380-routine-logic-details.yaml` as each batch completes: "
                    "for routines assigned to that batch, "
                    "replace `semantic_status: pending_deep_read` and "
                    "`coverage: indexed_only`"
                ),
                "`semantic_status: deep_read_complete` and `coverage: deep_read`",
                (
                    "`routine_logic_inventory.summary[]` and "
                    "`routine_logic_inventory.details[]`"
                ),
                "do not leave seed arrays empty",
                (
                    "do not perform final consolidation while later retained batches remain"
                ),
                (
                    "After every retained deep-read batch is complete, merge the full set's "
                    "semantic detail into `SS380-routine-logic-details.md`"
                ),
                (
                    "Only after every retained deep-read batch is complete and consolidated, "
                    "run the program-analysis validator"
                ),
            ]
            for step in required_steps:
                self.assertIn(step, prompt_text)

            retained_batch_loop_start = prompt_text.index(
                "- When retained deep-read batch files exist"
            )
            positions = [
                prompt_text.index(step, retained_batch_loop_start)
                for step in required_steps
            ]
            self.assertEqual(positions, sorted(positions))

    def test_large_program_prompt_has_a_tier_specific_terminal_completion_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "SIMPLE,program,RPGLE,SIMPLE.RPGLE,120,normal_program,test",
                        "SS380,program,RPGLE,SS380.RPGLE,3200,large_extreme_program,test",
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
                    str(temp_root / "source"),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            normal_prompt = (out_dir / "prompt-queue" / "0001-SIMPLE.md").read_text(
                encoding="utf-8"
            )
            large_prompt = (out_dir / "prompt-queue" / "0002-SS380.md").read_text(
                encoding="utf-8"
            )

            self.assertNotIn("## Large-program terminal completion contract", normal_prompt)
            self.assertIn("## Large-program terminal completion contract", large_prompt)
            self.assertIn(
                "A deterministic index, precreated file, or populated batch-001 file is a scaffold/checkpoint, never completion evidence.",
                large_prompt,
            )
            self.assertIn(
                "Do not write `batch_status=completed`, `completed_with_warnings`, or a passing validator status until all four conditions below are true.",
                large_prompt,
            )
            self.assertIn(
                "Every retained checkpoint is source-backed and free of indexer/pending seed content.",
                large_prompt,
            )
            self.assertIn(
                "SS380-deep-read-execution-plan.yaml",
                large_prompt,
            )
            self.assertIn(
                "do not delete, rewrite, reorder, or remap it or the source index",
                large_prompt,
            )
            self.assertIn(
                "Every `planned_deep_read` entry in the execution plan has its exact planned window-to-RLOG binding",
                large_prompt,
            )
            self.assertIn(
                "generic summary text is not completion evidence.",
                large_prompt,
            )
            self.assertIn(
                "The full program-analysis validator shown below exits successfully after the consolidation.",
                large_prompt,
            )
            self.assertIn(
                '--expected-size-tier "large_extreme_program"',
                large_prompt,
            )

    def test_terminal_status_validator_revalidates_large_program_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            batch_dir = temp_root / "batch"
            output_dir = (
                temp_root
                / "delivery"
                / "modules"
                / "CAP-ID-0001-large_extreme_program"
                / "SS380"
            )
            batch_dir.mkdir()
            fixture = write_finalized_program_artifacts(
                output_dir,
                "SS380",
                size_tier="large_extreme_program",
            )
            batch_path = output_dir / "routine-logic-details" / "SS380-deep-read-batch-001.md"
            batch_path.parent.mkdir(parents=True, exist_ok=True)
            batch_path.write_text(
                "\n\n".join(
                    [
                        "# Routine Logic Details: SS380 - Deep Read Batch 001",
                        "## Calculation Logic\n\nA generic calculation note without the source-backed batch detail.",
                        "## Validation Logic\n\nA generic validation note without the source-backed batch detail.",
                        "## Exception Handling\n\nA generic exception note without the source-backed batch detail.",
                        "## Scope\n\nOne source window is assigned to this checkpoint.",
                        "## Batch Coverage Summary\n\n| Window ID | Routine | Source Lines | RLOG Detail |\n| --- | --- | --- | --- |\n| DRW-SS380-001 | MAIN | 1-100 | RLOG-SS380-001 |",
                        "## Message Inventory\n\nNo additional message token is recorded by this checkpoint.",
                        "## Routine Details\n\n### RLOG-SS380-001 - MAIN\n\n**Semantic status:** deep_read_complete\n\n- Execution trigger: source entry.\n- Step-by-step logic: generic summary.\n- Field calculations and assignments: generic summary.\n- Conditioned calculation blocks: none observed.\n- Outcome reverse traces: generic summary.\n- Field lineage: generic summary.\n- Branch outcomes: generic summary.\n- Routine exception closure: generic summary.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "SS380,completed,pass,modules/CAP-ID-0001-large_extreme_program/SS380,,,,,",
                    ]
                )
                + "\n",
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
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("upstream program-analysis contract", result.stdout)
            self.assertIn("SS380", result.stdout)

    def test_terminal_status_validator_cannot_downgrade_a_large_batch_row(self) -> None:
        """A CSV large tier remains authoritative when summary YAML is rewritten."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            batch_dir = temp_root / "batch"
            output_dir = temp_root / "delivery" / "modules" / "normal" / "SS380"
            batch_dir.mkdir()
            # This fixture is mechanically valid as a normal program. The row
            # says large, so it must not close without retained deep-read work.
            write_finalized_program_artifacts(output_dir, "SS380")
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,size_tier,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "SS380,large_extreme_program,completed,pass,modules/normal/SS380,,,,,",
                    ]
                )
                + "\n",
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
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("large-program tier contract mismatch", result.stdout)
            self.assertIn("batch checkpoint files", result.stdout)

    def test_terminal_status_validator_requires_precreated_large_execution_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            batch_dir = temp_root / "batch"
            output_dir = (
                temp_root
                / "delivery"
                / "modules"
                / "CAP-ID-0001-large_extreme_program"
                / "SS380"
            )
            batch_dir.mkdir()
            write_finalized_program_artifacts(
                output_dir,
                "SS380",
                size_tier="large_extreme_program",
            )
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,size_tier,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "SS380,large_extreme_program,completed,pass,modules/CAP-ID-0001-large_extreme_program/SS380,,,,,",
                    ]
                )
                + "\n",
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
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("precreated immutable execution lock", result.stdout)
            self.assertIn("--scaffold-mode precreate", result.stdout)

    def test_terminal_status_validator_accepts_a_completed_upstream_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            batch_dir = temp_root / "batch"
            output_dir = (
                temp_root
                / "delivery"
                / "modules"
                / "CAP-ID-0003-normal_program"
                / "SIMPLE"
            )
            batch_dir.mkdir()
            write_finalized_program_artifacts(output_dir, "SIMPLE")
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "SIMPLE,completed,pass,modules/CAP-ID-0003-normal_program/SIMPLE,,,,,",
                    ]
                )
                + "\n",
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
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

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
            self.assertIn("## Artifact Bootstrap Gate (before semantic deep-read)", prompt_text)
            self.assertNotIn("## Flow-merge recovery context", prompt_text)
            self.assertIn("Never create an empty/placeholder core sidecar by hand", prompt_text)
            self.assertIn("index_rpg_source.py", prompt_text)
            self.assertIn("--preserve-existing", prompt_text)
            self.assertIn("If any required artifact is still missing", prompt_text)
            self.assertIn("batch_status=failed_runtime", prompt_text)
            self.assertIn("Do not stop after deterministic indexing", prompt_text)
            self.assertIn("Every RLOG declared in @CU400P-routine-logic-details.yaml", prompt_text)
            self.assertIn("Preserve the exact reader-first main-file structure", prompt_text)
            self.assertIn("Follow the `legacy-ibmi-program-analyzer` output contract", prompt_text)
            self.assertIn("## Program Reading Summary", prompt_text)
            self.assertIn("## Review Checklist", prompt_text)
            self.assertIn("### Routine Index For Calculation Logic", prompt_text)
            self.assertIn("### Routine Index For Validation Logic", prompt_text)
            self.assertIn("### Routine Index For Exception Handling", prompt_text)
            self.assertIn("immediately after writing this program's artifacts", prompt_text)
            self.assertIn("This validation is mandatory for every program", prompt_text)
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
            self.assertIn("- Validation mode: immediate", plan_text)

    def test_rejects_escaping_recovery_candidate_artifact_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason,candidate_artifact_root\n"
                "CU106,program,RPGLE,CU106.RPGLE,100,normal_program,test,../outside\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(temp_root / "batch"),
                    "--source-root",
                    str(temp_root / "source"),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("candidate_artifact_root", result.stderr)
            self.assertFalse((temp_root / "outside").exists())

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

    def test_large_precreate_records_immutable_execution_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            out_dir = temp_root / "batch"
            source_root.mkdir()
            (source_root / "SS380.RPGLE").write_text(
                "H DFTACTGRP(*NO)\n" + "\n".join("* filler" for _ in range(10001)),
                encoding="utf-8",
            )
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason",
                        "SS380,program,RPGLE,SS380.RPGLE,10002,large_extreme_program,test",
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
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                row = next(csv.DictReader(handle))
            output_dir = (
                delivery_root
                / "modules"
                / "CAP-ID-0001-large_extreme_program"
                / "SS380"
            )
            source_index = output_dir / "SS380-source-index.yaml"
            plan = output_dir / "SS380-deep-read-execution-plan.yaml"
            self.assertTrue(plan.is_file())
            self.assertEqual(
                row["source_index_sha256"],
                hashlib.sha256(source_index.read_bytes()).hexdigest(),
            )
            self.assertEqual(row["deep_read_execution_plan_path"], plan.name)
            self.assertEqual(
                row["deep_read_execution_plan_sha256"],
                hashlib.sha256(plan.read_bytes()).hexdigest(),
            )
            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn(f"source_index_sha256: {row['source_index_sha256']}", manifest_text)
            self.assertIn(
                f"deep_read_execution_plan_sha256: {row['deep_read_execution_plan_sha256']}",
                manifest_text,
            )

    def test_subagent_mode_prepares_parallel_worker_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            source_root.mkdir()
            for member in ("CC050", "CC051"):
                (source_root / f"{member}.RPGLE").write_text(
                    "H DFTACTGRP(*NO)\nC     *ENTRY        PLIST\nC                   SETON                                        LR\n",
                    encoding="utf-8",
                )
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
                    str(source_root),
                    "--delivery-root",
                    str(delivery_root),
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
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
            self.assertIn("Warning: --out-dir is not named like a dedicated program-list batch root", result.stdout)
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
            self.assertIn("只接受 `validation_mode=immediate`", serial_prompt)
            self.assertIn("立即运行 prompt 中的", serial_prompt)
            self.assertIn("不要只运行 batch status validator", serial_prompt)
            self.assertIn("不允许把 `scanned_unvalidated` 当作 Cline serial 的成功状态", serial_prompt)
            self.assertIn("Artifact Bootstrap Gate", serial_prompt)
            self.assertIn("创建空 sidecar 凑数", serial_prompt)
            self.assertIn("index_rpg_source.py ... --preserve-existing", serial_prompt)
            self.assertIn("`failed_runtime`", serial_prompt)
            self.assertIn("Routine Logic Details` -> `Deep Read Windows`", serial_prompt)
            self.assertIn("不得改成自定义简版 layout", serial_prompt)
            self.assertIn("prompt-queue", serial_prompt)
            self.assertTrue((out_dir / "subagent-results").is_dir())
            subagent_prompt = (out_dir / "subagent-queue" / "0001-CC050.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Do not edit these shared batch files directly", subagent_prompt)
            self.assertIn("program-list-status.csv", subagent_prompt)
            self.assertIn("CC050.result.json", subagent_prompt)
            self.assertIn("Embedded Per-Program Prompt", subagent_prompt)
            self.assertIn("Per-Program Validation Gate", subagent_prompt)
            self.assertIn("## Artifact Bootstrap Gate (before semantic deep-read)", subagent_prompt)
            self.assertIn("--preserve-existing", subagent_prompt)
            self.assertIn("Routine Index For Calculation Logic", subagent_prompt)
            self.assertIn("Do not write `completed/pass` until that validator passes", subagent_prompt)
            self.assertIn("parent merge will run the full validator again", subagent_prompt)
            dispatch_plan = (out_dir / "subagent-dispatch-plan.md").read_text(encoding="utf-8")
            self.assertIn(
                "py -3 .agents\\skills\\legacy-ibmi-program-list-batch\\scripts\\merge_subagent_results.py",
                dispatch_plan,
            )
            self.assertNotIn("python3 skills/", dispatch_plan)
            kiro_prompt = (out_dir / "kiro-parallel-runner-prompt.md").read_text(encoding="utf-8")
            self.assertIn(
                "py -3 .agents\\skills\\legacy-ibmi-program-list-batch\\scripts\\merge_subagent_results.py",
                kiro_prompt,
            )
            self.assertIn(
                "py -3 .agents\\skills\\legacy-ibmi-program-list-batch\\scripts\\validate_program_batch_status.py",
                kiro_prompt,
            )
            self.assertNotIn("python3 skills/", kiro_prompt)

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
            self.assertIn("只接受 `validation_mode=immediate`", kiro_prompt)
            self.assertIn("完整的 `validate_program_analysis_contract.py`", kiro_prompt)
            self.assertIn("parent gate", kiro_prompt)
            self.assertIn("validate_program_batch_status.py", kiro_prompt)
            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn("cline-serial-runner-prompt.md", plan_text)
            self.assertIn("- Sub-agent mode: prepare", plan_text)
            self.assertIn("- Max parallel agents: 2", plan_text)
            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("cline_serial_runner_prompt:", manifest_text)
            self.assertIn("kiro_parallel_runner_prompt:", manifest_text)
            self.assertIn("subagent_mode: prepare", manifest_text)
            self.assertIn("validation_mode: immediate", manifest_text)
            self.assertIn("max_parallel_agents: 2", manifest_text)
            self.assertIn("subagent_dispatch_plan:", manifest_text)
            self.assertIn('cline_parallel_runner_prompt: ""', manifest_text)

    def test_subagent_mode_rejects_deferred_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(temp_root / "batch"),
                    "--validation-mode",
                    "deferred",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires --validation-mode immediate", result.stderr)

    def test_subagent_mode_requires_precreated_scaffolds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(temp_root / "batch"),
                    "--source-root",
                    str(temp_root / "source"),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                    "--validation-mode",
                    "immediate",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires --scaffold-mode precreate", result.stderr)

    def test_merge_subagent_results_revalidates_successful_worker_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            source_root.mkdir()
            for member in ("CC050", "CC051"):
                (source_root / f"{member}.RPGLE").write_text(
                    "H DFTACTGRP(*NO)\nC     *ENTRY        PLIST\nC                   SETON                                        LR\n",
                    encoding="utf-8",
                )
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
                    "--source-root",
                    str(source_root),
                    "--delivery-root",
                    str(delivery_root),
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
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
                        "batch_status": "completed",
                        "validator_status": "pass",
                        "completed_at": "2026-07-11T00:00:00+00:00",
                        "last_error": "",
                        "next_action": "ready for downstream program-list batch validation",
                        "output_dir": str(delivery_root / "missing-output" / "CC050"),
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
            self.assertEqual(rows[0]["batch_status"], "failed_validator")
            self.assertEqual(rows[0]["validator_status"], "failed")
            self.assertIn("worker_result_output_dir_mismatch", rows[0]["last_error"])
            self.assertEqual(
                rows[0]["output_dir"],
                str(
                    delivery_root
                    / "modules"
                    / "CAP-ID-0003-normal_program"
                    / "CC050"
                ),
            )
            self.assertEqual(rows[0]["session_id"], "0001-CC050.result")
            self.assertEqual(rows[1]["batch_status"], "queued")

            plan_text = (out_dir / "program-batch-plan.md").read_text(encoding="utf-8")
            self.assertIn("| failed | 1 |", plan_text)
            manifest_text = (out_dir / "batch-scan-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("status: subagent_results_merged", manifest_text)
            self.assertIn("merged_result_count: 1", manifest_text)
            self.assertIn("batch_status: failed_validator", manifest_text)

    def test_merge_rejects_large_worker_output_redirect_and_keeps_allocated_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            source_root.mkdir()
            (source_root / "SS380.RPGLE").write_text(
                "H DFTACTGRP(*NO)\nC     *ENTRY        PLIST\nC                   SETON                                        LR\n",
                encoding="utf-8",
            )
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "SS380,program,RPGLE,SS380.RPGLE,3200,large_extreme_program,test\n",
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
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            canonical_output = (
                delivery_root
                / "modules"
                / "CAP-ID-0001-large_extreme_program"
                / "SS380"
            )
            redirected_output = (
                delivery_root
                / "modules"
                / "CAP-ID-0003-normal_program"
                / "SS380"
            )
            write_finalized_program_artifacts(redirected_output, "SS380")
            result_path = out_dir / "subagent-results" / "0001-SS380.result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "member": "SS380",
                        "batch_status": "completed",
                        "validator_status": "pass",
                        "completed_at": "2026-07-22T00:00:00+00:00",
                        "last_error": "",
                        "next_action": "ready for downstream program-list batch validation",
                        "output_dir": str(redirected_output),
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
            self.assertEqual(rows[0]["batch_status"], "failed_validator")
            self.assertEqual(rows[0]["validator_status"], "failed")
            self.assertIn("worker_result_output_dir_mismatch", rows[0]["last_error"])
            self.assertIn(str(canonical_output), rows[0]["last_error"])
            self.assertIn(str(redirected_output), rows[0]["last_error"])
            self.assertEqual(rows[0]["output_dir"], str(canonical_output))

    def test_merge_uses_preallocated_large_tier_for_recovery_output_validation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            out_dir = temp_root / "batch"
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            source_root.mkdir()
            (source_root / "SS381.RPGLE").write_text(
                "H DFTACTGRP(*NO)\nC     *ENTRY        PLIST\nC                   SETON                                        LR\n",
                encoding="utf-8",
            )
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason,candidate_artifact_root\n"
                "SS381,program,RPGLE,SS381.RPGLE,3200,large_extreme_program,test,modules/CAP-ID-0003-normal_program/SS381\n",
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
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            recovery_output = (
                delivery_root
                / "modules"
                / "CAP-ID-0003-normal_program"
                / "SS381"
            )
            write_finalized_program_artifacts(
                recovery_output,
                "SS381",
                size_tier="normal_program",
            )
            result_path = out_dir / "subagent-results" / "0001-SS381.result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "member": "SS381",
                        "batch_status": "completed",
                        "validator_status": "pass",
                        "completed_at": "2026-07-22T00:00:00+00:00",
                        "last_error": "",
                        "next_action": "ready for downstream program-list batch validation",
                        "output_dir": str(recovery_output),
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
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

            with (out_dir / "program-list-status.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["batch_status"], "failed_validator")
            self.assertEqual(rows[0]["validator_status"], "failed")
            self.assertIn("large-program tier contract mismatch", rows[0]["last_error"])
            self.assertEqual(rows[0]["output_dir"], str(recovery_output))

    def test_kiro_precreate_preserves_existing_program_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "source"
            delivery_root = temp_root / "delivery"
            source_root.mkdir()
            (source_root / "CC050.RPGLE").write_text(
                "H DFTACTGRP(*NO)\nC     *ENTRY        PLIST\nC                   SETON                                        LR\n",
                encoding="utf-8",
            )
            output_dir = delivery_root / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            output_dir.mkdir(parents=True)
            retained_analysis = "# Completed SME analysis\n\nThis reviewed analysis must be retained.\n"
            (output_dir / "CC050-program-analysis.md").write_text(
                retained_analysis,
                encoding="utf-8",
            )
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(temp_root / "batch"),
                    "--source-root",
                    str(source_root),
                    "--delivery-root",
                    str(delivery_root),
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(
                (output_dir / "CC050-program-analysis.md").read_text(encoding="utf-8"),
                retained_analysis,
            )
            for artifact in (
                "CC050-source-index.yaml",
                "CC050-program-analysis-summary.yaml",
                "CC050-routine-index.md",
                "CC050-message-inventory.yaml",
                "CC050-routine-logic-details.md",
                "CC050-routine-logic-details.yaml",
            ):
                self.assertTrue((output_dir / artifact).is_file(), artifact)

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

    def test_status_validator_require_terminal_rejects_active_rows_only_when_requested(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_dir = Path(temp_dir) / "batch"
            batch_dir.mkdir()
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text(
                "# Plan\n", encoding="utf-8"
            )
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "QUEUED,queued,not_run,,,,,run next prompt",
                        "ACTIVE,in_progress,not_run,,worker-1,,,",
                        "DEFERRED,scanned_unvalidated,deferred,,,,,run final validation",
                    ]
                ),
                encoding="utf-8",
            )

            consistency_result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(
                consistency_result.returncode,
                0,
                consistency_result.stderr + consistency_result.stdout,
            )

            terminal_result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(terminal_result.returncode, 0)
            self.assertIn("queued", terminal_result.stdout)
            self.assertIn("in_progress", terminal_result.stdout)
            self.assertIn("scanned_unvalidated", terminal_result.stdout)
            self.assertIn("terminal", terminal_result.stdout.lower())

    def test_terminal_status_validator_requires_concrete_completed_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_dir = Path(temp_dir) / "batch"
            batch_dir.mkdir()
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action",
                        "SS380,completed,pass,<delivery-root>/modules/SS380,,,,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "claimed terminal completion requires a concrete output_dir",
                result.stdout,
            )

    def test_status_validator_requires_parent_merge_for_terminal_kiro_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_dir = Path(temp_dir) / "batch"
            batch_dir.mkdir()
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "subagent_mode: prepare\nscaffold_mode: precreate\nsubagent_expected_count: 1\nstatus: initialized\nprograms: []\n",
                encoding="utf-8",
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires parent merge", result.stdout)

    def test_status_validator_rejects_legacy_kiro_batch_without_precreated_scaffolds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_dir = Path(temp_dir) / "batch"
            batch_dir.mkdir()
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "subagent_mode: prepare\nscaffold_mode: none\nstatus: subagent_results_merged\nprograms: []\n",
                encoding="utf-8",
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "member,batch_status,validator_status,output_dir,owner,session_id,last_error,next_action\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires scaffold_mode=precreate", result.stdout)

    def test_status_validator_rejects_invalid_worker_count_without_bypassing_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_dir = Path(temp_dir) / "batch"
            batch_dir.mkdir()
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "subagent_mode: prepare\nscaffold_mode: precreate\n"
                "subagent_expected_count: not-a-number\nstatus: initialized\nprograms: []\n",
                encoding="utf-8",
            )
            (batch_dir / "program-batch-plan.md").write_text("# Plan\n", encoding="utf-8")
            (batch_dir / "program-list-status.csv").write_text(
                "member,batch_status,validator_status,subagent_prompt_path,last_error,next_action\n"
                "CC050,blocked_missing_source,not_run,subagent-queue/0001-CC050.md,source missing,repair source\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid subagent_expected_count", result.stdout)
            self.assertIn("requires parent merge", result.stdout)

    def test_terminal_kiro_batch_without_dispatchable_workers_does_not_require_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            program_list = temp_root / "program-list.csv"
            program_list.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CC050,program,RPGLE,CC050.RPGLE,100,normal_program,test\n",
                encoding="utf-8",
            )
            batch_dir = temp_root / "batch"

            initialized = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    "--program-list",
                    str(program_list),
                    "--out-dir",
                    str(batch_dir),
                    "--source-root",
                    str(temp_root / "missing-source"),
                    "--delivery-root",
                    str(temp_root / "delivery"),
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
                    "--subagent-mode",
                    "prepare",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr + initialized.stdout)

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATUS_VALIDATOR),
                    "--batch-dir",
                    str(batch_dir),
                    "--require-terminal",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

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

    def test_status_validator_rejects_completed_row_with_pending_nested_deep_read_batch(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            batch_dir = temp_root / "batch"
            output_dir = (
                temp_root
                / "delivery"
                / "modules"
                / "CAP-ID-0001-large_extreme_program"
                / "SS380"
            )
            deep_read_dir = output_dir / "routine-logic-details"
            batch_dir.mkdir()
            deep_read_dir.mkdir(parents=True)
            (batch_dir / "batch-scan-manifest.yaml").write_text(
                "programs: []\n", encoding="utf-8"
            )
            (batch_dir / "program-batch-plan.md").write_text(
                "# Plan\n", encoding="utf-8"
            )
            (batch_dir / "program-list-status.csv").write_text(
                "\n".join(
                    [
                        "member,object_type,source_kind,path,total_lines,size_tier,tier_reason,batch_status,validator_status,output_dir,prompt_path,owner,session_id,started_at,completed_at,last_error,next_action,handoff_path",
                        "SS380,program,RPGLE,SS380.RPGLE,3200,large_extreme_program,test,completed,pass,modules/CAP-ID-0001-large_extreme_program/SS380,,,,,,,,",
                    ]
                ),
                encoding="utf-8",
            )
            artifact_text = {
                "SS380-program-analysis.md": (
                    "# Program Analysis: SS380\n\n"
                    "## Program Reading Summary\n\n"
                    "Reader-first processing context is filled.\n\n"
                    "## Calculation Logic\n\n"
                    "### Calculation Logic Overview\n\n"
                    "Calculation overview is source-backed.\n\n"
                    "### Routine Index For Calculation Logic\n\n"
                    "RLOG-SS380-001 calculation detail.\n\n"
                    "## Validation Logic\n\n"
                    "### Validation Logic Overview\n\n"
                    "Validation overview is source-backed.\n\n"
                    "### Routine Index For Validation Logic\n\n"
                    "RLOG-SS380-001 validation detail.\n\n"
                    "## Exception Handling\n\n"
                    "### Exception Flow Overview\n\n"
                    "Exception overview is source-backed.\n\n"
                    "### Routine Index For Exception Handling\n\n"
                    "RLOG-SS380-001 exception detail.\n"
                ),
                "SS380-routine-logic-details.md": (
                    "# Routine Logic Details: SS380\n\n"
                    "RLOG-SS380-001 contains source-backed semantic detail.\n"
                ),
                "SS380-source-index.yaml": "ok\n",
                "SS380-program-analysis-summary.yaml": "ok\n",
                "SS380-routine-index.md": "ok\n",
                "SS380-message-inventory.yaml": "ok\n",
                "SS380-routine-logic-details.yaml": "ok\n",
            }
            for artifact, text in artifact_text.items():
                (output_dir / artifact).write_text(text, encoding="utf-8")

            pending_batch = deep_read_dir / "SS380-deep-read-batch-002.md"
            pending_batch.write_text(
                "\n\n".join(
                    [
                        "# Routine Logic Details: SS380 - Deep Read Batch 002",
                        (
                            "Batch seed generated by `index_rpg_source.py`. Update this file "
                            "while deep-reading the selected source windows."
                        ),
                        "## Calculation Logic\n\nPending semantic deep-read for this batch.",
                        "## Validation Logic\n\nPending semantic deep-read for this batch.",
                        "## Exception Handling\n\nPending semantic deep-read for this batch.",
                        (
                            "## Routine Details\n\n### RLOG-SS380-001 - SR400\n\n"
                            "**Semantic status:** pending_deep_read\n\n"
                            "- Step-by-step logic: pending deep read."
                        ),
                    ]
                )
                + "\n",
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
            self.assertIn("SS380-deep-read-batch-002.md", result.stdout)
            self.assertIn("pending", result.stdout.lower())

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
                    "## Calculation Logic\n\n"
                    "### Calculation Logic Overview\n\n"
                    "Calculation overview is filled.\n\n"
                    "### Routine Index For Calculation Logic\n\n"
                    "RLOG-CC050-001 calculation detail.\n\n"
                    "## Validation Logic\n\n"
                    "### Validation Logic Overview\n\n"
                    "Validation overview is filled.\n\n"
                    "### Routine Index For Validation Logic\n\n"
                    "RLOG-CC050-001 validation detail.\n\n"
                    "## Exception Handling\n\n"
                    "### Exception Flow Overview\n\n"
                    "Exception overview is filled.\n\n"
                    "### Routine Index For Exception Handling\n\n"
                    "RLOG-CC050-001 exception detail.\n\n"
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
                "CC050-program-analysis.md": (
                    "# Program Analysis: CC050\n\n"
                    "## Program Reading Summary\n\n"
                    "Reader-first processing context is filled.\n\n"
                    "## Calculation Logic\n\n"
                    "### Calculation Logic Overview\n\n"
                    "Calculation overview is filled.\n\n"
                    "### Routine Index For Calculation Logic\n\n"
                    "RLOG-CC050-001 calculation detail.\n\n"
                    "## Validation Logic\n\n"
                    "### Validation Logic Overview\n\n"
                    "Validation overview is filled.\n\n"
                    "### Routine Index For Validation Logic\n\n"
                    "RLOG-CC050-001 validation detail.\n\n"
                    "## Exception Handling\n\n"
                    "### Exception Flow Overview\n\n"
                    "Exception overview is filled.\n\n"
                    "### Routine Index For Exception Handling\n\n"
                    "RLOG-CC050-001 exception detail.\n"
                ),
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

    def test_status_validator_rejects_scanned_unvalidated_missing_reader_first_indexes(self) -> None:
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
                "CC050-program-analysis.md": (
                    "# Program Analysis: CC050\n\n"
                    "## Program Reading Summary\n\n"
                    "Reader-first processing context is filled.\n\n"
                    "## Calculation Logic\n\n"
                    "Calculation themes are filled, but the routine index is missing.\n\n"
                    "## Validation Logic\n\n"
                    "Validation themes are filled, but the routine index is missing.\n\n"
                    "## Exception Handling\n\n"
                    "Exception themes are filled, but the routine index is missing.\n"
                ),
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

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing reader-first layout heading(s)", result.stdout)
            self.assertIn("Routine Index For Calculation Logic", result.stdout)
            self.assertIn("Routine Index For Validation Logic", result.stdout)
            self.assertIn("Routine Index For Exception Handling", result.stdout)

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
