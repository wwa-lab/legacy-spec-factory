from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "validate_program_analysis_contract.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("program_analysis_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def full_program_analysis() -> str:
    sections = "\n\n".join(
        f"## {section}\n\nPlaceholder content."
        for section in VALIDATOR.REQUIRED_PROGRAM_SECTIONS
    )
    return f"# Program Analysis: CU650 (unlinked)\n\n{sections}\n"


def compressed_program_analysis() -> str:
    return """# Program Analysis: CU650 (unlinked)

## Calculation Logic

Compressed wrapper only.

## Validation Logic

Compressed wrapper only.

## Exception Handling

Compressed wrapper only.

## Message Inventory

Compressed wrapper only.

## File I/O / SQL

Compressed wrapper only.

## TBDs & Blocking Status

Compressed wrapper only.
"""


def summary_yaml(optional_file_io_status: str = "not_written_by_default") -> str:
    return f"""schema_version: "0.1"
generated_by: index_rpg_source.py
program: CU650
sidecars:
  source_index:
    path: source-index.yaml
    status: present
  routine_index:
    path: routine-index.md
    status: present
  routine_logic_details:
    path: routine-logic-details.md
    status: present
  routine_logic_details_yaml:
    path: routine-logic-details.yaml
    status: present
  message_inventory_yaml:
    path: message-inventory.yaml
    status: present
  file_io_inventory:
    path: file-io-inventory.md
    status: {optional_file_io_status}
"""


def routine_yaml(start: int = 1, end: int = 93) -> str:
    details = "\n".join(
        f"""    -
      detail_id: RLOG-CU650-{index:03d}
      routine: SR{index:03d}
"""
        for index in range(start, end + 1)
    )
    return f"""schema_version: "0.1"
program: CU650
routine_logic_inventory:
  details:
{details}"""


def routine_markdown(start: int = 1, end: int = 93) -> str:
    sections = "\n\n".join(
        f"## RLOG-CU650-{index:03d} - SR{index:03d}\n\nPending semantic detail."
        for index in range(start, end + 1)
    )
    return f"# Routine Logic Details: CU650\n\n{sections}\n"


def final_routine_markdown(start: int = 1, end: int = 93) -> str:
    detail_sections = "\n\n".join(
        f"### RLOG-CU650-{index:03d} - SR{index:03d}\n\nCompleted semantic detail."
        for index in range(start, end + 1)
    )
    return f"""# Routine Logic Details: CU650

## Calculation Logic

Whole-program calculation summary.

## Validation Logic

Whole-program validation summary.

## Exception Handling

Whole-program exception summary.

## Message Inventory

Whole-program message summary.

## Routine Detail Index

All routines are indexed here.

## Routine Details

{detail_sections}
"""


def deep_read_batch(include_exception: bool = True, core_before_rlog: bool = True) -> str:
    core = """## SME Core Logic Snapshot

### Calculation Logic

Batch calculation summary.

### Validation Logic

Batch validation summary.

"""
    if include_exception:
        core += """### Exception Handling

Batch exception summary.

"""
    detail = """## RLOG-CU650-001 - MAIN

Per-routine detail.
"""
    if core_before_rlog:
        return f"# CU650 Deep-Read Batch 001\n\n{core}{detail}"
    return f"# CU650 Deep-Read Batch 001\n\n{detail}{core}"


def write_common_artifacts(path: Path) -> None:
    (path / "program-analysis-summary.yaml").write_text(summary_yaml(), encoding="utf-8")
    (path / "source-index.yaml").write_text("program: CU650\n", encoding="utf-8")
    (path / "routine-index.md").write_text("# Routine Index\n", encoding="utf-8")
    (path / "message-inventory.yaml").write_text("program: CU650\n", encoding="utf-8")
    (path / "routine-logic-details.yaml").write_text(routine_yaml(), encoding="utf-8")


class ProgramAnalysisContractValidatorTests(unittest.TestCase):
    def test_passes_complete_wrapper_and_rlog_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_passes_deep_read_batch_with_front_loaded_core_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "deep-read-batch-001.md").write_text(
                deep_read_batch(),
                encoding="utf-8",
            )

            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_fails_compressed_program_analysis_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                compressed_program_analysis(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("missing required sections" in finding for finding in findings))
        self.assertTrue(any("Metadata" in finding for finding in findings))
        self.assertTrue(any("Program Call Map" in finding for finding in findings))

    def test_fails_last_batch_only_routine_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(
                routine_markdown(start=81, end=93),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("missing RLOG IDs" in finding for finding in findings))
        self.assertTrue(any("RLOG-CU650-001" in finding for finding in findings))
        self.assertTrue(any("RLOG-CU650-080" in finding for finding in findings))

    def test_fails_deep_read_batch_missing_exception_core(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "deep-read-batch-001.md").write_text(
                deep_read_batch(include_exception=False),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("deep-read-batch-001.md missing required headings" in finding for finding in findings))
        self.assertTrue(any("Exception Handling" in finding for finding in findings))

    def test_fails_deep_read_batch_that_buries_core_after_rlog_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "deep-read-batch-001.md").write_text(
                deep_read_batch(core_before_rlog=False),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("core logic before per-routine RLOG detail" in finding for finding in findings))

    def test_fails_triggered_sidecar_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis-summary.yaml").write_text(
                summary_yaml(optional_file_io_status="optional_triggered"),
                encoding="utf-8",
            )
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("file_io_inventory" in finding for finding in findings))
        self.assertTrue(any("file-io-inventory.md" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
