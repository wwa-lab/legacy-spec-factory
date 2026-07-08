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

Per-routine detail.
"""
    if core_before_rlog:
        return f"# CU650 Deep-Read Batch 001\n\n{core}{suffix}"
    return f"# CU650 Deep-Read Batch 001\n\n{suffix}{core}"


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

Per-routine detail.
"""


def write_common_artifacts(path: Path) -> None:
    (path / "program-analysis-summary.yaml").write_text(summary_yaml(), encoding="utf-8")
    (path / "source-index.yaml").write_text("program: CU650\n", encoding="utf-8")
    (path / "routine-index.md").write_text("# Routine Index\n", encoding="utf-8")
    (path / "message-inventory.yaml").write_text("program: CU650\n", encoding="utf-8")
    (path / "routine-logic-details.yaml").write_text(routine_yaml(), encoding="utf-8")


class ProgramAnalysisContractValidatorTests(unittest.TestCase):
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
