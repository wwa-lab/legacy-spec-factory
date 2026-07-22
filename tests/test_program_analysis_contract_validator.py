from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


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
        program_reading_summary_section() if section == "Program Reading Summary"
        else routine_logic_section() if section == "Routine Logic Details"
        else message_inventory_section() if section == "Message Inventory"
        else routine_index_section(section) if section in {
            "Calculation Logic",
            "Validation Logic",
            "Exception Handling",
        }
        else f"## {section}\n\nPlaceholder content."
        for section in VALIDATOR.REQUIRED_PROGRAM_SECTIONS
    )
    return f"# Program Analysis: CU650 (unlinked)\n\n{sections}\n"


def program_reading_summary_section() -> str:
    return """## Program Reading Summary

CU650 is a standalone exploratory RPG program analysis for account-cycle
processing. The reader should start with the source-loading, validation,
calculation, message/status, and persistence layers before drilling into
routine-level RLOG notes in this same file.

This artifact remains `standalone_exploratory` and does not assert approved
`OBJ-*` or `EV-*` IDs.

| Processing Layer | Main Routines | What To Understand First |
| --- | --- | --- |
| Account setup and source loading | `SR001` - `SR010` | Loads account, statement, card, and control carriers before downstream logic reads working state. |
| Validation and message/status routing | `SR011` - `SR040` | Applies file prerequisites, business-state gates, helper returns, and status-code decisions. |
| Calculation and persistence outputs | `SR041` - `SR093` | Derives account values, prepares final writes, and records message or exception outcomes. |
"""


def message_inventory_section() -> str:
    return """## Message Inventory

| Message / Code / Literal | Short Description | Type | Occurrences | Primary Routine(s) | First Seen / Set By | Trigger / Handler Summary | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UCC1852 | Authorization amount exceeds configured card control threshold | message/status | 1 | MAIN | source line 42 | threshold branch | MSG-CU650-001 |
"""


def overview_heading(section: str) -> str:
    if section == "Exception Handling":
        return "Exception Flow Overview"
    return f"{section} Overview"


def theme_heading(section: str) -> str:
    if section == "Calculation Logic":
        return "Account-Cycle Calculation Theme"
    if section == "Validation Logic":
        return "Business-State Validation Theme"
    return "File And Helper Failure Theme"


def routine_index_section(
    section: str,
    *,
    start: int = 1,
    end: int = 93,
    include_theme_sections: bool = True,
) -> str:
    rows = "\n".join(
        f"| RLOG-CU650-{index:03d} / SR{index:03d} | category | {section} reader-useful detail |"
        for index in range(start, end + 1)
    )
    themed_intro = ""
    if include_theme_sections:
        themed_intro = f"""
### {overview_heading(section)}

Reader-oriented overview by processing theme for SME first-pass navigation.

| Theme | Routine Count | Routines | Reader Cue |
| --- | --- | --- | --- |
| Account-cycle processing | {end - start + 1} | `SR{start:03d}` - `SR{end:03d}` | Follow this theme before routine-level detail to understand the program behavior. |

### {theme_heading(section)}

This theme groups routines that share account-cycle behavior, validation
outcomes, exception closure, and downstream state effects for reviewer
navigation before the complete RLOG index.
"""
    return f"""## {section}

{themed_intro or "Reader-oriented overview by theme."}

### Routine Index For {section}

| RLOG / Routine | Category | Reader-useful Detail |
| --- | --- | --- |
{rows}
"""


def routine_logic_section(*, start: int = 1, end: int = 93) -> str:
    rows = "\n".join(
        f"""### RLOG-CU650-{index:03d} - SR{index:03d}

- Purpose: SR{index:03d} contributes account-cycle processing for the CU650 review path.
- Inputs / carriers: Reads source fields, working storage carriers, and prior routine state needed by this routine.
- Processing summary: Normalizes the routine branch behavior, source-line intent, and downstream state changes for SME review.
- Validation / exception summary: Records any message, status, return, or tolerated path connected to this routine.
- Evidence / status: Detail is normalized for the final reader-first wrapper and aligned to RLOG-CU650-{index:03d}.
"""
        for index in range(start, end + 1)
    )
    return f"""## Routine Logic Details

{rows}
"""


def program_analysis_without_main_rlog_detail() -> str:
    return full_program_analysis().replace(
        """### RLOG-CU650-042 - SR042

- Purpose: SR042 contributes account-cycle processing for the CU650 review path.
- Inputs / carriers: Reads source fields, working storage carriers, and prior routine state needed by this routine.
- Processing summary: Normalizes the routine branch behavior, source-line intent, and downstream state changes for SME review.
- Validation / exception summary: Records any message, status, return, or tolerated path connected to this routine.
- Evidence / status: Detail is normalized for the final reader-first wrapper and aligned to RLOG-CU650-042.
""",
        "",
    )


def program_analysis_missing_validation_index_row() -> str:
    return full_program_analysis().replace(
        "| RLOG-CU650-017 / SR017 | category | Validation Logic reader-useful detail |\n",
        "",
        1,
    )


def program_analysis_with_placeholder_reading_summary() -> str:
    return full_program_analysis().replace(
        program_reading_summary_section(),
        "## Program Reading Summary\n\nPending reader-oriented summary.\n",
    )


def program_analysis_with_placeholder_core_index_detail() -> str:
    return full_program_analysis().replace(
        "| RLOG-CU650-017 / SR017 | category | Validation Logic reader-useful detail |\n",
        "| RLOG-CU650-017 / SR017 | pending | pending semantic deep-read |\n",
        1,
    )


def program_analysis_without_core_theme_section() -> str:
    return full_program_analysis().replace(
        routine_index_section("Calculation Logic"),
        routine_index_section("Calculation Logic", include_theme_sections=False),
    )


def program_analysis_with_placeholder_main_rlog_detail() -> str:
    original = """### RLOG-CU650-042 - SR042

- Purpose: SR042 contributes account-cycle processing for the CU650 review path.
- Inputs / carriers: Reads source fields, working storage carriers, and prior routine state needed by this routine.
- Processing summary: Normalizes the routine branch behavior, source-line intent, and downstream state changes for SME review.
- Validation / exception summary: Records any message, status, return, or tolerated path connected to this routine.
- Evidence / status: Detail is normalized for the final reader-first wrapper and aligned to RLOG-CU650-042.
"""
    return full_program_analysis().replace(
        original,
        "### RLOG-CU650-042 - SR042\n\nPending semantic deep-read.\n",
    )


def program_analysis_with_stale_gap_wording() -> str:
    return full_program_analysis().replace(
        "## Analysis Coverage & Scope\n\nPlaceholder content.",
        (
            "## Analysis Coverage & Scope\n\n"
            "Remaining routine deep-read gaps: SR030, SR310. "
            "Some not-yet-deep-read routines remain."
        ),
    )


def compressed_program_analysis() -> str:
    return """# Program Analysis: CU650 (unlinked)

## Program Reading Summary

Compressed wrapper only.

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


def summary_yaml(
    optional_file_io_status: str = "not_written_by_default",
    program_size_tier: str = "normal_program",
    line_count: int = 100,
    routine_detail_status: str = "present",
) -> str:
    return f"""schema_version: "0.1"
generated_by: index_rpg_source.py
program: CU650
source:
  line_count: {line_count}
program_size_tier: {program_size_tier}
sidecars:
  program_analysis:
    path: program-analysis.md
    status: present
  source_index:
    path: source-index.yaml
    status: present
  routine_index:
    path: routine-index.md
    status: present
  routine_logic_details:
    path: routine-logic-details.md
    status: {routine_detail_status}
  routine_logic_details_yaml:
    path: routine-logic-details.yaml
    status: {routine_detail_status}
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


def routine_yaml_with_pending_semantic_seed(start: int = 1, end: int = 93) -> str:
    details = "\n".join(
        f"""    -
      detail_id: RLOG-CU650-{index:03d}
      routine: SR{index:03d}
      semantic_status: pending_deep_read
      execution_trigger: pending deep read
      step_by_step_logic: []
      field_calculations: []
      conditioned_calculation_blocks: []
      outcome_reverse_traces: []
      field_lineage: []
      branch_outcomes: []
      routine_exception_closure: []
      unresolved_routine_logic: pending deep read
"""
        for index in range(start, end + 1)
    )
    return f"""schema_version: "0.1"
program: CU650
routine_logic_inventory:
  details:
{details}"""


def routine_yaml_with_completed_indexed_utilities(start: int = 1, end: int = 93) -> str:
    details = "\n".join(
        f"""    -
      detail_id: RLOG-CU650-{index:03d}
      routine: SR{index:03d}
      semantic_status: source_backed_complete
      coverage: indexed_only
      execution_trigger: Called only by the source-backed formatting path.
      unresolved_routine_logic: none
"""
        for index in range(start, end + 1)
    )
    return f"""schema_version: "0.1"
program: CU650
routine_logic_inventory:
  details:
{details}"""


def routine_yaml_with_pending_summary_and_completed_details(
    start: int = 1,
    end: int = 93,
) -> str:
    completed = routine_yaml_with_completed_indexed_utilities(start, end)
    return completed.replace(
        "routine_logic_inventory:\n",
        """routine_logic_inventory:
  summary:
    - routine: SR001
      detail_ref: RLOG-CU650-001
      semantic_status: pending_deep_read
      coverage: indexed_only
""",
        1,
    )


def routine_yaml_with_completed_first_batch(start: int = 1, end: int = 93) -> str:
    summary = "\n".join(
        f"""    -
      routine: SR{index:03d}
      detail_ref: RLOG-CU650-{index:03d}
      semantic_status: {"deep_read_complete" if index == 1 else "source_backed_complete"}
      coverage: {"deep_read" if index == 1 else "indexed_only"}
"""
        for index in range(start, end + 1)
    )
    details: list[str] = []
    for index in range(start, end + 1):
        semantic_status = "deep_read_complete" if index == 1 else "source_backed_complete"
        coverage = "deep_read" if index == 1 else "indexed_only"
        structured_fields = ""
        if index == 1:
            structured_fields = """      step_by_step_logic:
        - Reads the entry state and evaluates the source-backed dispatch branch.
      field_calculations:
        - No arithmetic occurs; the routine assigns the documented status carrier.
      conditioned_calculation_blocks:
        - The assignment runs only when the entry validation guard succeeds.
      outcome_reverse_traces:
        - The success status traces back to the validated entry branch.
      field_lineage:
        - Entry parameter to working status to returned outcome.
      branch_outcomes:
        - Success continues; failure returns the documented error status.
      routine_exception_closure:
        - No local exception; failure is returned through the status carrier.
"""
        details.append(
            f"""    -
      detail_id: RLOG-CU650-{index:03d}
      routine: SR{index:03d}
      semantic_status: {semantic_status}
      coverage: {coverage}
      execution_trigger: Called from the source-backed entry dispatch path.
{structured_fields}      unresolved_routine_logic: none
"""
        )
    return f"""schema_version: "0.1"
program: CU650
routine_logic_inventory:
  summary:
{summary}
  details:
{"".join(details)}"""


def message_yaml(
    *,
    message: str = "UCC1852",
    description: str = "unresolved - message description not available",
    description_source: str = "missing_message_catalog_or_reference_pack",
    evidence_status: str = "unresolved_description",
) -> str:
    return f"""schema_version: "0.1"
program: CU650
message_inventory:
  summary:
    -
      message: {message}
      short_description: "{description}"
      description_source: "{description_source}"
      evidence_status: {evidence_status}
      occurrence_count: 1
      routines:
        - MAIN
      first_seen: source line 42
      detail_ref: MSG-CU650-001
  details:
    -
      detail_id: MSG-CU650-001
      message: {message}
      short_description: "{description}"
      description_source: "{description_source}"
      evidence_status: {evidence_status}
      occurrence_count: 1
      routines:
        - MAIN
      first_seen: source line 42
      occurrences: []
"""


def routine_markdown(start: int = 1, end: int = 93) -> str:
    sections = "\n\n".join(
        f"""## RLOG-CU650-{index:03d} - SR{index:03d}

Completed semantic detail describes the execution trigger, branch behavior,
field effects, exception closure, and downstream outcome for this routine."""
        for index in range(start, end + 1)
    )
    return f"# Routine Logic Details: CU650\n\n{sections}\n"


def final_routine_markdown(start: int = 1, end: int = 93) -> str:
    detail_sections = "\n\n".join(
        f"""### RLOG-CU650-{index:03d} - SR{index:03d}

Completed semantic detail describes the execution trigger, branch behavior,
field effects, exception closure, and downstream outcome for this routine."""
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


def final_routine_markdown_with_pending_semantic_detail() -> str:
    return final_routine_markdown().replace(
        """Completed semantic detail describes the execution trigger, branch behavior,
field effects, exception closure, and downstream outcome for this routine.""",
        "Pending semantic detail.",
        1,
    )


def deep_read_batch(include_exception: bool = True, core_before_rlog: bool = True) -> str:
    core = """## Calculation Logic

Batch calculation summary.

## Validation Logic

Batch validation summary.

"""
    if include_exception:
        core += """## Exception Handling

Batch exception summary.

"""
    suffix = """## Scope

Batch routines/windows covered and excluded.

## Batch Coverage Summary

| Window ID | Routine | Source Lines | RLOG Detail |
| --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |

## Message Inventory

No message/status tokens observed in this batch.

## Routine Details

### RLOG-CU650-001 - MAIN

Source-backed routine detail explains the entry trigger, branch decisions,
field assignments, validation outcome, side effects, and exception closure.
"""
    if core_before_rlog:
        return f"# CU650 Deep-Read Batch 001\n\n{core}{suffix}"
    return f"# CU650 Deep-Read Batch 001\n\n{suffix}{core}"


def indexer_pending_deep_read_batch() -> str:
    return """# Routine Logic Details: CU650 - Deep Read Batch 001

Batch seed generated by `index_rpg_source.py`. Update this file while
deep-reading the selected source windows, then merge completed semantic detail
into `routine-logic-details.md`. Keep this batch file as an audit checkpoint.

## Calculation Logic

Pending semantic deep-read for this batch.

| Logic / Calculation | Routine | Target Field / Variable | Source Operands | Guard / Condition | Output / Effect | Detail Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pending | MAIN | pending | pending | pending | pending | RLOG pending | source-index.yaml |

## Validation Logic

Pending semantic deep-read for this batch.

| Message / Status / Outcome | Routine | Trigger Chain | Carrier / Destination | Downstream Effect | Detail Link | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- |
| pending | MAIN | pending | pending | pending | RLOG pending | pending |

## Exception Handling

Pending semantic deep-read for this batch.

| Exception / Error Path | Routine | Trigger / Detection | Fields / Messages Set | Handling Action | Downstream Effect | Detail Link | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pending | MAIN | pending | pending | pending | pending | RLOG pending | pending |

## Scope

This batch covers at most five routine/window seeds.

## Batch Coverage Summary

| Window ID | Routine | Source Lines | Why Selected | RLOG Detail |
| --- | --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | entry/mainline | RLOG-CU650-001 |

## Message Inventory

| Message / Status / Literal | Description | Type | Routine | First Seen / Set By | Trigger / Handler | Related Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| - | no message/status tokens observed in this batch seed | - | - | - | - | - | - |

## Routine Details

### RLOG-CU650-001 - MAIN

**Source lines:** 1-100

**Deep-read reason:** entry/mainline

**Semantic status:** pending_deep_read

- Execution trigger: pending deep read.
- Step-by-step logic: pending deep read.
- Field calculations and assignments: pending deep read.
- Conditioned calculation blocks: pending deep read.
- Outcome reverse traces: pending deep read.
- Routine field lineage / carriers: pending deep read.
- Routine exception closure: pending deep read.
"""


def deep_read_batch_with_code_snippet() -> str:
    return """# CU650 Deep-Read Batch 001

## Calculation Logic

```rpgle
C                   EVAL      AUTHSTS = 'P'
```

## Validation Logic

Batch validation summary.

## Exception Handling

Batch exception summary.

## Scope

Batch routines/windows covered and excluded.

## Batch Coverage Summary

| Window ID | Routine | Source Lines | RLOG Detail |
| --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |

## Message Inventory

No message/status tokens observed in this batch.

## Routine Details

### RLOG-CU650-001 - MAIN

Source-backed routine detail explains the entry trigger, branch decisions,
field assignments, validation outcome, side effects, and exception closure.
"""


def write_common_artifacts(path: Path) -> None:
    (path / "program-analysis-summary.yaml").write_text(summary_yaml(), encoding="utf-8")
    (path / "source-index.yaml").write_text("program: CU650\n", encoding="utf-8")
    (path / "routine-index.md").write_text("# Routine Index\n", encoding="utf-8")
    (path / "message-inventory.yaml").write_text("program: CU650\n", encoding="utf-8")
    (path / "routine-logic-details.yaml").write_text(routine_yaml(), encoding="utf-8")


def write_large_execution_plan(
    path: Path,
    *,
    windows: tuple[tuple[str, str, str, str, int], ...],
) -> None:
    """Write the deterministic deep-read plan used by large-program tests.

    Tuple members are ``window_id, routine, source_lines, rlog_id, batch_number``.
    The production contract will bind the plan to the source-index bytes so
    deleting later batches cannot make an incomplete large analysis appear done.
    """

    source_index = "program: CU650\ndeep_read_windows:\n" + "".join(
        (
            f"  - window_id: {window_id}\n"
            f"    routine: {routine}\n"
            f"    source_lines: {source_lines}\n"
            "    why_selected: state-changing source path\n"
            "    coverage_outcome: selected_for_deep_read\n"
            "    evidence: source-index\n"
        )
        for window_id, routine, source_lines, _rlog_id, _batch_number in windows
    )
    source_index_path = path / "source-index.yaml"
    source_index_path.write_text(source_index, encoding="utf-8")
    source_digest = hashlib.sha256(source_index.encode("utf-8")).hexdigest()
    plan_name = "CU650-deep-read-execution-plan.yaml"
    plan_lines = [
        'schema_version: "0.1"',
        "generated_by: index_rpg_source.py",
        "program: CU650",
        "program_size_tier: large_extreme_program",
        "source_index_path: source-index.yaml",
        f"source_index_sha256: {source_digest}",
        "planned_deep_read:",
    ]
    for window_id, routine, source_lines, rlog_id, batch_number in windows:
        plan_lines.extend(
            [
                f"  - window_id: {window_id}",
                f"    routine: {routine}",
                f"    source_lines: {source_lines}",
                f"    rlog_id: {rlog_id}",
                f"    batch_number: {batch_number}",
                "    batch_path: routine-logic-details/"
                f"CU650-deep-read-batch-{batch_number:03d}.md",
            ]
        )
    (path / plan_name).write_text("\n".join(plan_lines) + "\n", encoding="utf-8")
    summary_path = path / "program-analysis-summary.yaml"
    summary = summary_yaml(
        program_size_tier="large_extreme_program",
        line_count=12001,
    ).replace(
        "  file_io_inventory:\n",
        "  deep_read_execution_plan:\n"
        f"    path: {plan_name}\n"
        "    status: present\n"
        "  file_io_inventory:\n",
        1,
    )
    summary_path.write_text(summary, encoding="utf-8")


class ProgramAnalysisContractValidatorTests(unittest.TestCase):
    def test_batch_discovery_unions_declared_and_actual_files_in_natural_order(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (analysis_dir / "program-analysis-summary.yaml").write_text(
                summary_yaml().replace(
                    "  file_io_inventory:\n",
                    """  routine_logic_deep_read_batch_001:
    path: routine-logic-details/CU650-deep-read-batch-1.md
    status: optional_triggered
  file_io_inventory:
""",
                    1,
                ),
                encoding="utf-8",
            )
            for number in (1, 10, 2):
                (batch_dir / f"CU650-deep-read-batch-{number}.md").write_text(
                    f"batch {number}\n", encoding="utf-8"
                )

            discovered = VALIDATOR.batch_detail_files(analysis_dir)

        self.assertEqual(
            [path.name for path in discovered],
            [
                "CU650-deep-read-batch-1.md",
                "CU650-deep-read-batch-2.md",
                "CU650-deep-read-batch-10.md",
            ],
        )

    def test_batch_discovery_keeps_declared_custom_checkpoint_without_batch_dir(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            checkpoint_dir = analysis_dir / "custom-checkpoints"
            checkpoint_dir.mkdir()
            checkpoint = checkpoint_dir / "semantic-window-7.md"
            checkpoint.write_text("checkpoint\n", encoding="utf-8")
            (analysis_dir / "program-analysis-summary.yaml").write_text(
                summary_yaml().replace(
                    "  file_io_inventory:\n",
                    """  routine_logic_deep_read_batch_007:
    path: custom-checkpoints/semantic-window-7.md
    status: optional_triggered
  file_io_inventory:
""",
                    1,
                ),
                encoding="utf-8",
            )

            discovered = VALIDATOR.batch_detail_files(analysis_dir)

        self.assertEqual(discovered, [checkpoint])

    def test_fails_normal_without_routine_detail_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            (analysis_dir / "program-analysis-summary.yaml").write_text(
                summary_yaml(routine_detail_status="not_written_by_default"),
                encoding="utf-8",
            )
            (analysis_dir / "source-index.yaml").write_text("program: CU650\n", encoding="utf-8")
            (analysis_dir / "routine-index.md").write_text("# Routine Index\n", encoding="utf-8")
            (analysis_dir / "message-inventory.yaml").write_text("program: CU650\n", encoding="utf-8")
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("routine_logic_details" in finding for finding in findings))
        self.assertTrue(any("routine_logic_details_yaml" in finding for finding in findings))

    def test_passes_complete_wrapper_and_rlog_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_fails_placeholder_program_reading_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_with_placeholder_reading_summary(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Program Reading Summary" in finding for finding in findings))
        self.assertTrue(any("reader-first golden gate" in finding for finding in findings))

    def test_fails_placeholder_core_logic_index_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_with_placeholder_core_index_detail(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Routine Index For Validation Logic" in finding for finding in findings))
        self.assertTrue(any("RLOG-CU650-017" in finding for finding in findings))
        self.assertTrue(any("reader-useful detail" in finding for finding in findings))

    def test_fails_core_logic_without_theme_subsection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_without_core_theme_section(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                routine_markdown(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Calculation Logic" in finding for finding in findings))
        self.assertTrue(any("theme subsection" in finding for finding in findings))

    def test_fails_placeholder_main_rlog_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_with_placeholder_main_rlog_detail(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Routine Logic Details" in finding for finding in findings))
        self.assertTrue(any("RLOG-CU650-042" in finding for finding in findings))
        self.assertTrue(any("reader-useful detail" in finding for finding in findings))

    def test_passes_deep_read_batch_with_front_loaded_core_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
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

    def test_fails_batch_rlog_without_deep_read_yaml_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_indexed_utilities(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                deep_read_batch(), encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "RLOG-CU650-001" in finding
                and ("coverage: deep_read" in finding or "structured semantic" in finding)
                for finding in findings
            ),
            findings,
        )

    def test_fails_batch_rlog_when_yaml_summary_and_details_disagree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            mismatched_yaml = routine_yaml_with_completed_first_batch().replace(
                "semantic_status: deep_read_complete\n      coverage: deep_read",
                "semantic_status: source_backed_complete\n      coverage: indexed_only",
                1,
            )
            (analysis_dir / "routine-logic-details.yaml").write_text(
                mismatched_yaml, encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                deep_read_batch(), encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("RLOG-CU650-001" in finding and "summary" in finding for finding in findings),
            findings,
        )

    def test_fails_deep_read_batch_with_more_than_five_windows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            extra_rows = "\n".join(
                f"| DRW-CU650-{number:03d} | MAIN | 1-100 | RLOG-CU650-001 |"
                for number in range(2, 7)
            )
            batch_text = deep_read_batch().replace(
                "| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |",
                "| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |\n" + extra_rows,
                1,
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("more than 5" in finding and "window" in finding for finding in findings),
            findings,
        )

    def test_fails_deep_read_batch_with_more_than_five_rlogs_without_window_ids(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            coverage_rows = "\n".join(
                f"| - | SR{number:03d} | {number}-{number + 1} | RLOG-CU650-{number:03d} |"
                for number in range(1, 7)
            )
            detail_blocks = "\n\n".join(
                f"""### RLOG-CU650-{number:03d} - SR{number:03d}

Source-backed routine detail explains the trigger, branch decisions, field
assignments, validation outcome, side effects, and exception closure."""
                for number in range(1, 7)
            )
            batch_text = deep_read_batch().replace(
                "| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |",
                coverage_rows,
                1,
            ).replace(
                """### RLOG-CU650-001 - MAIN

Source-backed routine detail explains the entry trigger, branch decisions,
field assignments, validation outcome, side effects, and exception closure.""",
                detail_blocks,
                1,
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("more than 5" in finding and "window" in finding for finding in findings),
            findings,
        )

    def test_fails_when_coverage_summary_rlog_has_no_batch_detail_or_yaml_deep_read(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_text = deep_read_batch().replace(
                "| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |",
                """| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |
| DRW-CU650-002 | SR002 | 101-140 | RLOG-CU650-002 |""",
                1,
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "RLOG-CU650-002" in finding
                and "missing reader-useful detail" in finding
                for finding in findings
            ),
            findings,
        )
        self.assertTrue(
            any(
                "RLOG-CU650-002" in finding and "coverage: deep_read" in finding
                for finding in findings
            ),
            findings,
        )

    def test_coverage_notes_cross_reference_is_not_treated_as_assigned_rlog(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_text = deep_read_batch().replace(
                """| Window ID | Routine | Source Lines | RLOG Detail |
| --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |""",
                """| Window ID | Routine | Source Lines | Why Selected | RLOG Detail |
| --- | --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | Called by RLOG-CU650-099 | RLOG-CU650-001 |""",
                1,
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )
            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_coverage_notes_window_cross_references_do_not_expand_batch_scope(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            cross_references = ", ".join(
                f"DRW-CU650-{number:03d}" for number in range(2, 7)
            )
            batch_text = deep_read_batch().replace(
                """| Window ID | Routine | Source Lines | RLOG Detail |
| --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | RLOG-CU650-001 |""",
                f"""| Window ID | Routine | Source Lines | Why Selected | RLOG Detail |
| --- | --- | --- | --- | --- |
| DRW-CU650-001 | MAIN | 1-100 | Related windows: {cross_references} | RLOG-CU650-001 |""",
                1,
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_fails_indexer_pending_deep_read_batch_with_valid_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                indexer_pending_deep_read_batch(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "CU650-deep-read-batch-001.md" in finding
                and "pending" in finding.lower()
                for finding in findings
            ),
            findings,
        )

    def test_fails_consolidated_routine_detail_with_pending_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown_with_pending_semantic_detail(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "routine-logic-details.md" in finding
                and "pending" in finding.lower()
                for finding in findings
            ),
            findings,
        )

    def test_fails_thin_consolidated_routine_body_without_seed_words(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            thin_markdown = final_routine_markdown().replace(
                """Completed semantic detail describes the execution trigger, branch behavior,
field effects, exception closure, and downstream outcome for this routine.""",
                "Done.",
                1,
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                thin_markdown, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "routine-logic-details.md" in finding
                and "RLOG-CU650-001" in finding
                and "reader-useful" in finding
                for finding in findings
            ),
            findings,
        )

    def test_fails_thin_last_consolidated_rlog_before_later_h2_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            detail = """Completed semantic detail describes the execution trigger, branch behavior,
field effects, exception closure, and downstream outcome for this routine."""
            complete = final_routine_markdown()
            last_detail = complete.rfind(detail)
            thin_markdown = (
                complete[:last_detail]
                + "Done."
                + complete[last_detail + len(detail) :]
                + """

## Sharding Guidance

This later section contains many explanatory words but is not semantic detail
for the preceding routine and must not inflate that RLOG's quality score.
"""
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                thin_markdown, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "RLOG-CU650-093" in finding and "reader-useful" in finding
                for finding in findings
            ),
            findings,
        )

    def test_fails_routine_yaml_retaining_indexer_pending_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_pending_semantic_seed(),
                encoding="utf-8",
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "routine-logic-details.yaml" in finding
                and (
                    "pending_deep_read" in finding.lower()
                    or "pending deep read" in finding.lower()
                )
                for finding in findings
            ),
            findings,
        )

    def test_fails_when_routine_yaml_summary_remains_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_pending_summary_and_completed_details(),
                encoding="utf-8",
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "routine-logic-details.yaml" in finding
                and "pending_deep_read" in finding
                for finding in findings
            ),
            findings,
        )

    def test_allows_completed_utility_with_indexed_only_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_indexed_utilities(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )

            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_fails_isolated_pending_deep_read_status_in_batch_rlog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            batch_text = deep_read_batch().replace(
                "Source-backed routine detail explains",
                "**Semantic status:** pending_deep_read\n\nSource-backed routine detail explains",
                1,
            )
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("pending_deep_read" in finding for finding in findings), findings
        )

    def test_fails_exact_pending_cell_in_batch_core_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            batch_text = deep_read_batch().replace(
                "Batch calculation summary.",
                """| Calculation | Routine | Effect |
| --- | --- | --- |
| pending | MAIN | Source-backed effect description |""",
                1,
            )
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("pending table cell" in finding for finding in findings), findings
        )

    def test_fails_thin_batch_rlog_body_after_seed_words_are_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            batch_text = deep_read_batch().replace(
                """Source-backed routine detail explains the entry trigger, branch decisions,
field assignments, validation outcome, side effects, and exception closure.""",
                "Done.",
                1,
            )
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                batch_text, encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("RLOG-CU650-001" in finding and "reader-useful" in finding for finding in findings),
            findings,
        )

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

    def test_fails_when_main_program_analysis_missing_embedded_rlog_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_without_main_rlog_detail(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("program-analysis.md Routine Logic Details missing RLOG detail headings" in finding for finding in findings))
        self.assertTrue(any("RLOG-CU650-042" in finding for finding in findings))

    def test_fails_when_core_logic_routine_index_does_not_cover_rlog_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_missing_validation_index_row(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Routine Index For Validation Logic" in finding for finding in findings))
        self.assertTrue(any("RLOG-CU650-017" in finding for finding in findings))

    def test_fails_stale_deep_read_gap_wording(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis.md").write_text(
                program_analysis_with_stale_gap_wording(),
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("stale deep-read gap wording" in finding for finding in findings))

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

        self.assertTrue(any("deep-read-batch-001.md missing required ## headings" in finding for finding in findings))
        self.assertTrue(any("Exception Handling" in finding for finding in findings))

    def test_fails_deep_read_batch_missing_required_layout_sections(self) -> None:
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
                """# CU650 Deep-Read Batch 001

## Calculation Logic

Batch calculation summary.

## Validation Logic

Batch validation summary.

## Exception Handling

Batch exception summary.

## Routine Details

### RLOG-CU650-001 - MAIN

Per-routine detail.
""",
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Scope" in finding for finding in findings))
        self.assertTrue(any("Batch Coverage Summary" in finding for finding in findings))
        self.assertTrue(any("Message Inventory" in finding for finding in findings))

    def test_fails_deep_read_batch_core_with_source_code_snippet(self) -> None:
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
                deep_read_batch_with_code_snippet(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("must not contain fenced source/code blocks" in finding for finding in findings))
        self.assertTrue(any("source-code-like snippet" in finding for finding in findings))

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

    def test_fails_large_extreme_program_missing_batch_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "program-analysis-summary.yaml").write_text(
                summary_yaml(program_size_tier="large_extreme_program", line_count=12001),
                encoding="utf-8",
            )
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("large_extreme_program requires" in finding for finding in findings))
        self.assertTrue(any("deep-read-batch" in finding for finding in findings))

    def test_fails_large_program_when_later_planned_batch_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            write_large_execution_plan(
                analysis_dir,
                windows=(
                    ("DRW-CU650-001", "MAIN", "1-100", "RLOG-CU650-001", 1),
                    ("DRW-CU650-002", "SR002", "101-140", "RLOG-CU650-002", 1),
                    ("DRW-CU650-003", "SR003", "141-180", "RLOG-CU650-003", 1),
                    ("DRW-CU650-004", "SR004", "181-220", "RLOG-CU650-004", 1),
                    ("DRW-CU650-005", "SR005", "221-260", "RLOG-CU650-005", 1),
                    ("DRW-CU650-006", "SR006", "261-300", "RLOG-CU650-006", 2),
                ),
            )
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                deep_read_batch(), encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any(
                "large deep-read execution plan" in finding.lower()
                and "batch-002" in finding
                for finding in findings
            ),
            findings,
        )

    def test_fails_large_program_when_plan_source_index_digest_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            write_large_execution_plan(
                analysis_dir,
                windows=(
                    ("DRW-CU650-001", "MAIN", "1-100", "RLOG-CU650-001", 1),
                ),
            )
            (analysis_dir / "source-index.yaml").write_text(
                "program: CU650\ndeep_read_windows: []\n",
                encoding="utf-8",
            )
            (analysis_dir / "routine-logic-details.yaml").write_text(
                routine_yaml_with_completed_first_batch(), encoding="utf-8"
            )
            (analysis_dir / "program-analysis.md").write_text(
                full_program_analysis(), encoding="utf-8"
            )
            (analysis_dir / "routine-logic-details.md").write_text(
                final_routine_markdown(), encoding="utf-8"
            )
            batch_dir = analysis_dir / "routine-logic-details"
            batch_dir.mkdir()
            (batch_dir / "CU650-deep-read-batch-001.md").write_text(
                deep_read_batch(), encoding="utf-8"
            )

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(
            any("source-index digest" in finding.lower() for finding in findings),
            findings,
        )

    def test_immutable_execution_lock_rejects_self_consistent_plan_rewrite(self) -> None:
        """A worker cannot shrink a large allocation by rewriting both local files."""

        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            fixture = write_finalized_program_artifacts(
                analysis_dir,
                "CU650",
                routines=("MAIN", "SR002", "SR003", "SR004", "SR005", "SR006"),
                size_tier="large_extreme_program",
            )
            original_source_lock = hashlib.sha256(
                fixture.source_index_yaml.read_bytes()
            ).hexdigest()
            plan_path = analysis_dir / "CU650-deep-read-execution-plan.yaml"
            original_plan_lock = hashlib.sha256(plan_path.read_bytes()).hexdigest()

            source_index = json.loads(fixture.source_index_yaml.read_text(encoding="utf-8"))
            source_index["deep_read_windows"] = source_index["deep_read_windows"][:-1]
            source_text = json.dumps(source_index, indent=2) + "\n"
            fixture.source_index_yaml.write_text(source_text, encoding="utf-8")

            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["source_index_sha256"] = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            plan["planned_deep_read"] = plan["planned_deep_read"][:-1]
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            (analysis_dir / "routine-logic-details" / "CU650-deep-read-batch-002.md").unlink()

            findings = VALIDATOR.validate(
                analysis_dir,
                expected_size_tier="large_extreme_program",
                expected_source_index_sha256=original_source_lock,
                expected_execution_plan_sha256=original_plan_lock,
            )

        self.assertTrue(
            any("immutable batch execution lock" in finding for finding in findings),
            findings,
        )

    def test_plan_cannot_remap_rlogs_away_from_source_index_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            fixture = write_finalized_program_artifacts(
                analysis_dir,
                "CU650",
                routines=("MAIN", "SR002"),
                size_tier="large_extreme_program",
            )
            source_index = json.loads(fixture.source_index_yaml.read_text(encoding="utf-8"))
            source_index["routine_logic_inventory"] = {
                "details": [
                    {"routine": "MAIN", "detail_id": "RLOG-CU650-001"},
                    {"routine": "SR002", "detail_id": "RLOG-CU650-002"},
                ]
            }
            source_text = json.dumps(source_index, indent=2) + "\n"
            fixture.source_index_yaml.write_text(source_text, encoding="utf-8")

            plan_path = analysis_dir / "CU650-deep-read-execution-plan.yaml"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["source_index_sha256"] = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            plan["planned_deep_read"][0]["rlog_id"] = "RLOG-CU650-002"
            plan["planned_deep_read"][1]["rlog_id"] = "RLOG-CU650-001"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

            batch_path = analysis_dir / "routine-logic-details" / "CU650-deep-read-batch-001.md"
            batch_text = batch_path.read_text(encoding="utf-8")
            batch_text = batch_text.replace("RLOG-CU650-001", "RLOG-CU650-TEMP")
            batch_text = batch_text.replace("RLOG-CU650-002", "RLOG-CU650-001")
            batch_path.write_text(
                batch_text.replace("RLOG-CU650-TEMP", "RLOG-CU650-002"),
                encoding="utf-8",
            )

            findings = VALIDATOR.validate(
                analysis_dir,
                expected_size_tier="large_extreme_program",
            )

        self.assertTrue(
            any("routine_logic_inventory requires" in finding for finding in findings),
            findings,
        )

    def test_fails_unresolved_message_descriptions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "message-inventory.yaml").write_text(message_yaml(), encoding="utf-8")
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("message descriptions unresolved" in finding for finding in findings))
        self.assertTrue(any("UCC1852" in finding for finding in findings))
        self.assertTrue(any("message file/catalog/reference pack" in finding for finding in findings))

    def test_passes_resolved_message_descriptions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "message-inventory.yaml").write_text(
                message_yaml(
                    description="Authorization amount exceeds configured card control threshold",
                    description_source="reference pack: REF-AUTH-MSG/catalog#UCC1852",
                    evidence_status="confirmed",
                ),
                encoding="utf-8",
            )
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            self.assertEqual(VALIDATOR.validate(analysis_dir), [])

    def test_fails_when_message_inventory_yaml_code_is_missing_from_main_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_dir = Path(temp_dir)
            write_common_artifacts(analysis_dir)
            (analysis_dir / "message-inventory.yaml").write_text(
                message_yaml(
                    message="W1ERCD",
                    description="Late-round token maintenance error",
                    description_source="reference pack: REF-AUTH-MSG/catalog#W1ERCD",
                    evidence_status="confirmed",
                ),
                encoding="utf-8",
            )
            (analysis_dir / "program-analysis.md").write_text(full_program_analysis(), encoding="utf-8")
            (analysis_dir / "routine-logic-details.md").write_text(routine_markdown(), encoding="utf-8")

            findings = VALIDATOR.validate(analysis_dir)

        self.assertTrue(any("Message Inventory missing observed YAML message/code values" in finding for finding in findings))
        self.assertTrue(any("W1ERCD" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
