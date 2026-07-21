"""Upstream-contract-valid program-analysis artifact fixtures.

The flow-analyzer tests must exercise the same reader-first contract emitted by
``legacy-ibmi-program-analyzer``.  These helpers deliberately use the current
canonical table headers, prefixed artifact names, synchronized message data,
and complete RLOG coverage.  Negative fixtures are produced by changing one
semantic terminal condition at a time.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


REQUIRED_PROGRAM_SECTIONS = (
    "Program Reading Summary",
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
    "Metadata",
    "Analysis Coverage & Scope",
    "Program Call Map",
    "Routine Cards",
    "Routine Logic Details",
    "Deep Read Windows",
    "Entry Points & Parameters",
    "Object Dependencies",
    "Logic Decomposition Ledger",
    "Data Touch Map",
    "Key File & Field Logic",
    "Control Flow",
    "File I/O",
    "External Calls",
    "Error Handling",
    "Redundancy Candidate Notes",
    "TBDs & Blocking Status",
    "Review Checklist",
)


@dataclass(frozen=True)
class ProgramArtifactFixture:
    analysis_dir: Path
    program: str
    prefix: str
    program_analysis: Path
    summary_yaml: Path
    source_index_yaml: Path
    routine_index_markdown: Path
    routine_details_markdown: Path
    routine_details_yaml: Path
    message_inventory_yaml: Path


def artifact_prefix(program: str) -> str:
    """Apply the upstream portable artifact-prefix convention."""

    value = re.sub(r'[\s<>:"/\\|?*]+', "_", program.strip().upper())
    return value.strip("._-") or "PROGRAM"


def _write_json_yaml(path: Path, value: Mapping[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _default_calculations(program: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "logic": f"{program} derives the approved amount from the request and account limit.",
            "target": "APPROVED_AMOUNT",
            "sources": "REQUEST_AMOUNT, ACCOUNT_LIMIT",
            "guard": "request is valid and the account is active",
            "effect": "returns the approved amount in the response payload",
            "detail": f"RLOG-{artifact_prefix(program)}-001 conditioned calculation block",
            "evidence": f"EV-{artifact_prefix(program)}-CALC-001",
        },
    )


def _default_validations(program: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "code": "00",
            "description": "Approved response status after request and account validation.",
            "type": "response_status",
            "set_by": "STATUS_CODE assignment in MAIN",
            "trigger": "request is present and the account remains eligible",
            "reverse_chain": f"RLOG-{artifact_prefix(program)}-001 outcome reverse trace",
            "carrier": "response status field",
            "effect": "allows the approved response to return to the caller",
            "evidence_status": "confirmed",
        },
    )


def _default_exceptions(program: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "path": "Account lookup failure",
            "trigger": "the requested account record is not found",
            "detection": "%FOUND returns false after the keyed lookup",
            "fields": "STATUS_CODE = 'NF'",
            "action": "return the not-found response without persistence",
            "effect": "suppresses downstream update and exposes the failure to the caller",
            "detail": f"RLOG-{artifact_prefix(program)}-001 exception closure",
            "evidence": f"EV-{artifact_prefix(program)}-EXC-001",
        },
    )


def _default_messages(program: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "code": "NF",
            "description": "Requested account record was not found.",
            "type": "response_status",
            "occurrences": "1",
            "routines": "MAIN",
            "first_seen": "STATUS_CODE assignment in MAIN",
            "trigger": "account lookup does not find the requested key",
            "detail": f"MSG-{artifact_prefix(program)}-001",
        },
    )


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join((header, separator, *body))


def _rlog_rows(program: str, routines: Sequence[str], category: str) -> tuple[tuple[str, ...], ...]:
    prefix = artifact_prefix(program)
    return tuple(
        (
            f"RLOG-{prefix}-{index:03d} / `{routine}`",
            category,
            f"Source-backed {category} behavior for {routine} preserves carriers, guards, and outcomes.",
        )
        for index, routine in enumerate(routines, start=1)
    )


def _program_reading_summary(program: str, routines: Sequence[str], marker: str) -> str:
    return f"""## Program Reading Summary

{marker} {program} is a standalone exploratory account-processing program.
The reader should follow request setup, calculation, validation, exception,
message/status, and response finalization layers before consulting detailed
routine evidence. No approved OBJ or EV trace identifiers are asserted by the
fixture wrapper itself.

{_table(
    ("Processing Layer", "Main Routines", "What To Understand First"),
    ((
        "Request processing and response finalization",
        ", ".join(f"`{routine}`" for routine in routines),
        "Trace request carriers through guarded calculations, status outcomes, exception closure, and final response assignment.",
    ),),
)}"""


def _calculation_section(
    program: str,
    routines: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    marker: str,
) -> str:
    return f"""## Calculation Logic

### Calculation Logic Overview

{marker} The calculation path derives response fields from explicit request
and account carriers, applies source-backed guards, and preserves the resulting
business effect for SME review.

{_table(
    ("Theme", "Routine Count", "Routines", "Reader Cue"),
    (("Response derivation", str(len(routines)), ", ".join(routines), "Follow request carriers through guarded assignments into the returned response."),),
)}

### Response Derivation Theme

The response derivation theme records concrete source and target carriers,
branch conditions, resulting assignments, downstream effects, and evidence.

{_table(
    (
        "Calculation / Assignment",
        "Target Field / Variable",
        "Source Operands / Carriers",
        "Guard / Branch",
        "Output / Business Effect",
        "Supporting Detail Link",
        "Evidence",
    ),
    tuple(
        (
            row["logic"],
            row["target"],
            row["sources"],
            row["guard"],
            row["effect"],
            row["detail"],
            row["evidence"],
        )
        for row in rows
    ),
)}

**Calculation logic unresolved:** None.

### Routine Index For Calculation Logic

{_table(("RLOG / Routine", "Category", "Reader-useful Detail"), _rlog_rows(program, routines, "response calculation"))}"""


def _validation_section(
    program: str,
    routines: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    marker: str,
) -> str:
    return f"""## Validation Logic

### Validation Logic Overview

{marker} Validation checks explicit request and account state, sets exact
status values, and carries each guarded outcome into the response path.

{_table(
    ("Theme", "Routine Count", "Routines", "Reader Cue"),
    (("Request and account eligibility", str(len(routines)), ", ".join(routines), "Confirm each status trigger, carrier, and downstream response effect."),),
)}

### Eligibility Validation Theme

This validation theme retains exact codes, setting locations, trigger chains,
output carriers, downstream effects, and evidence status for each outcome.

{_table(
    (
        "Message / Status Code",
        "Message Description",
        "Validation / Error Type",
        "Set By / Source Lines",
        "Trigger Condition",
        "Reverse Trigger Chain / Routine Logic Link",
        "Output Carrier",
        "Downstream Effect",
        "Evidence Status",
    ),
    tuple(
        (
            row["code"],
            row["description"],
            row["type"],
            row["set_by"],
            row["trigger"],
            row["reverse_chain"],
            row["carrier"],
            row["effect"],
            row["evidence_status"],
        )
        for row in rows
    ),
)}

**Validation logic unresolved:** None.

### Routine Index For Validation Logic

{_table(("RLOG / Routine", "Category", "Reader-useful Detail"), _rlog_rows(program, routines, "eligibility validation"))}"""


def _exception_section(
    program: str,
    routines: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    marker: str,
) -> str:
    return f"""## Exception Handling

### Exception Flow Overview

{marker} Exception paths expose their trigger, detection mechanism, assigned
status carrier, closure action, and downstream suppression behavior.

{_table(
    ("Theme", "Routine Count", "Routines", "Reader Cue"),
    (("Lookup and response failure closure", str(len(routines)), ", ".join(routines), "Confirm failure detection and the exact action that closes each path."),),
)}

### Lookup Failure Closure Theme

This exception theme keeps source-backed failure detection and closure visible
without inferring specific errors beyond the observed status assignment.

{_table(
    (
        "Exception / Error Path",
        "Trigger",
        "Detection Mechanism",
        "Fields / Messages Set",
        "Handling Action",
        "Downstream Effect",
        "Supporting Detail Link",
        "Evidence",
    ),
    tuple(
        (
            row["path"],
            row["trigger"],
            row["detection"],
            row["fields"],
            row["action"],
            row["effect"],
            row["detail"],
            row["evidence"],
        )
        for row in rows
    ),
)}

**Exception handling unresolved:** None.

### Routine Index For Exception Handling

{_table(("RLOG / Routine", "Category", "Reader-useful Detail"), _rlog_rows(program, routines, "exception closure"))}"""


def _message_section(rows: Sequence[Mapping[str, str]]) -> str:
    return f"""## Message Inventory

{_table(
    (
        "Message / Code / Literal",
        "Short Description",
        "Type",
        "Occurrences",
        "Primary Routine(s)",
        "First Seen / Set By",
        "Trigger / Handler Summary",
        "Detail",
    ),
    tuple(
        (
            row["code"],
            row["description"],
            row["type"],
            row["occurrences"],
            row["routines"],
            row["first_seen"],
            row["trigger"],
            row["detail"],
        )
        for row in rows
    ),
)}

**Message inventory unresolved:** None."""


def _metadata_section(program: str) -> str:
    return f"""## Metadata

| Field | Value |
| --- | --- |
| Program | {program} |
| Analysis Status | approved |
| Review Intent | standalone_exploratory |

**Status:** approved
"""


def _routine_logic_section(program: str, routines: Sequence[str]) -> str:
    prefix = artifact_prefix(program)
    details = "\n\n".join(
        f"""### RLOG-{prefix}-{index:03d} - {routine}

This source-backed routine detail explains the execution trigger, ordered
branch behavior, field assignments, carrier movement, validation outcome,
downstream response effect, and local exception closure for {routine}."""
        for index, routine in enumerate(routines, start=1)
    )
    return f"## Routine Logic Details\n\n{details}"


def render_program_analysis(
    program: str,
    *,
    routines: Sequence[str],
    calculations: Sequence[Mapping[str, str]],
    validations: Sequence[Mapping[str, str]],
    exceptions: Sequence[Mapping[str, str]],
    messages: Sequence[Mapping[str, str]],
    theme_markers: Mapping[str, str],
) -> str:
    specialized = {
        "Program Reading Summary": _program_reading_summary(
            program, routines, theme_markers["summary"]
        ),
        "Calculation Logic": _calculation_section(
            program, routines, calculations, theme_markers["calculation"]
        ),
        "Validation Logic": _validation_section(
            program, routines, validations, theme_markers["validation"]
        ),
        "Exception Handling": _exception_section(
            program, routines, exceptions, theme_markers["exception"]
        ),
        "Message Inventory": _message_section(messages),
        "Metadata": _metadata_section(program),
        "Routine Logic Details": _routine_logic_section(program, routines),
    }
    sections = tuple(
        specialized.get(
            section,
            f"## {section}\n\nSource-backed fixture content records the {section.lower()} review surface for {program}.",
        )
        for section in REQUIRED_PROGRAM_SECTIONS
    )
    return f"# Program Analysis: {program} (unlinked)\n\n" + "\n\n".join(sections) + "\n"


def _routine_details_markdown(program: str, routines: Sequence[str]) -> str:
    prefix = artifact_prefix(program)
    index_rows = tuple(
        (f"RLOG-{prefix}-{index:03d}", routine, "source-backed complete")
        for index, routine in enumerate(routines, start=1)
    )
    details = "\n\n".join(
        f"""### RLOG-{prefix}-{index:03d} - {routine}

Completed semantic detail describes the execution trigger, branch behavior,
field effects, exception closure, carrier lineage, and downstream outcome for
the source-backed {routine} routine."""
        for index, routine in enumerate(routines, start=1)
    )
    return f"""# Routine Logic Details: {program}

## Calculation Logic

Whole-program calculation behavior is complete and source backed.

## Validation Logic

Whole-program validation behavior is complete and source backed.

## Exception Handling

Whole-program exception closure is complete and source backed.

## Message Inventory

Whole-program exact message and status coverage is complete.

## Routine Detail Index

{_table(("RLOG", "Routine", "Semantic Status"), index_rows)}

## Routine Details

{details}
"""


def write_finalized_program_artifacts(
    analysis_dir: Path,
    program: str,
    *,
    routines: Sequence[str] = ("MAIN",),
    calculations: Sequence[Mapping[str, str]] | None = None,
    validations: Sequence[Mapping[str, str]] | None = None,
    exceptions: Sequence[Mapping[str, str]] | None = None,
    messages: Sequence[Mapping[str, str]] | None = None,
    theme_markers: Mapping[str, str] | None = None,
    size_tier: str = "normal_program",
) -> ProgramArtifactFixture:
    """Write a terminal reader-first artifact set that passes upstream validation."""

    if not routines:
        raise ValueError("at least one routine is required")
    prefix = artifact_prefix(program)
    calculations = tuple(calculations or _default_calculations(program))
    validations = tuple(validations or _default_validations(program))
    exceptions = tuple(exceptions or _default_exceptions(program))
    messages = tuple(messages or _default_messages(program))
    markers = {
        "summary": f"SUMMARY-THEME-{prefix}",
        "calculation": f"CALCULATION-THEME-{prefix}",
        "validation": f"VALIDATION-THEME-{prefix}",
        "exception": f"EXCEPTION-THEME-{prefix}",
        **dict(theme_markers or {}),
    }

    analysis_dir.mkdir(parents=True, exist_ok=True)
    fixture = ProgramArtifactFixture(
        analysis_dir=analysis_dir,
        program=program,
        prefix=prefix,
        program_analysis=analysis_dir / f"{prefix}-program-analysis.md",
        summary_yaml=analysis_dir / f"{prefix}-program-analysis-summary.yaml",
        source_index_yaml=analysis_dir / f"{prefix}-source-index.yaml",
        routine_index_markdown=analysis_dir / f"{prefix}-routine-index.md",
        routine_details_markdown=analysis_dir / f"{prefix}-routine-logic-details.md",
        routine_details_yaml=analysis_dir / f"{prefix}-routine-logic-details.yaml",
        message_inventory_yaml=analysis_dir / f"{prefix}-message-inventory.yaml",
    )

    fixture.program_analysis.write_text(
        render_program_analysis(
            program,
            routines=routines,
            calculations=calculations,
            validations=validations,
            exceptions=exceptions,
            messages=messages,
            theme_markers=markers,
        ),
        encoding="utf-8",
    )
    fixture.routine_details_markdown.write_text(
        _routine_details_markdown(program, routines), encoding="utf-8"
    )
    fixture.routine_index_markdown.write_text(
        f"# Routine Index: {program}\n\n"
        + _table(
            ("Routine", "RLOG", "Status"),
            tuple(
                (routine, f"RLOG-{prefix}-{index:03d}", "source-backed complete")
                for index, routine in enumerate(routines, start=1)
            ),
        )
        + "\n",
        encoding="utf-8",
    )

    _write_json_yaml(
        fixture.source_index_yaml,
        {
            "schema_version": "0.1",
            "program": program,
            "analysis_status": "approved",
            "source": {"line_count": 200},
        },
    )
    routine_summary = tuple(
        {
            "routine": routine,
            "detail_ref": f"RLOG-{prefix}-{index:03d}",
            "semantic_status": "source_backed_complete",
            "coverage": "indexed_only",
        }
        for index, routine in enumerate(routines, start=1)
    )
    routine_details = tuple(
        {
            "detail_id": f"RLOG-{prefix}-{index:03d}",
            "routine": routine,
            "semantic_status": "source_backed_complete",
            "coverage": "indexed_only",
            "execution_trigger": "Called from the source-backed request processing path.",
            "unresolved_routine_logic": "none",
        }
        for index, routine in enumerate(routines, start=1)
    )
    _write_json_yaml(
        fixture.routine_details_yaml,
        {
            "schema_version": "0.1",
            "program": program,
            "routine_logic_inventory": {
                "summary": routine_summary,
                "details": routine_details,
            },
        },
    )

    message_entries = tuple(
        {
            "detail_id": row["detail"],
            "message": row["code"],
            "short_description": row["description"],
            "description_source": "source literal and source-backed fixture evidence",
            "evidence_status": "confirmed",
            "occurrence_count": int(row["occurrences"]),
            "routines": tuple(part.strip() for part in row["routines"].split(",")),
            "first_seen": row["first_seen"],
            "occurrences": (),
        }
        for row in messages
    )
    _write_json_yaml(
        fixture.message_inventory_yaml,
        {
            "schema_version": "0.1",
            "program": program,
            "message_inventory": {
                "summary": message_entries,
                "details": message_entries,
            },
        },
    )
    _write_json_yaml(
        fixture.summary_yaml,
        {
            "schema_version": "0.1",
            "generated_by": "program_analysis_artifacts.py",
            "program": program,
            "source": {"line_count": 200},
            "program_size_tier": size_tier,
            "sidecars": {
                "program_analysis": {
                    "path": fixture.program_analysis.name,
                    "status": "present",
                },
                "source_index": {
                    "path": fixture.source_index_yaml.name,
                    "status": "present",
                },
                "routine_index": {
                    "path": fixture.routine_index_markdown.name,
                    "status": "present",
                },
                "routine_logic_details": {
                    "path": fixture.routine_details_markdown.name,
                    "status": "present",
                },
                "routine_logic_details_yaml": {
                    "path": fixture.routine_details_yaml.name,
                    "status": "present",
                },
                "message_inventory_yaml": {
                    "path": fixture.message_inventory_yaml.name,
                    "status": "present",
                },
            },
        },
    )
    return fixture


def mark_pending_deep_read(fixture: ProgramArtifactFixture) -> None:
    """Make one routine semantically non-terminal while keeping all files present."""

    payload = json.loads(fixture.routine_details_yaml.read_text(encoding="utf-8"))
    inventory = payload["routine_logic_inventory"]
    summary = tuple(inventory["summary"])
    details = tuple(inventory["details"])
    pending_summary = ({**summary[0], "semantic_status": "pending_deep_read"}, *summary[1:])
    pending_details = (
        {
            **details[0],
            "semantic_status": "pending_deep_read",
            "execution_trigger": "pending deep read",
            "unresolved_routine_logic": "pending deep read",
        },
        *details[1:],
    )
    _write_json_yaml(
        fixture.routine_details_yaml,
        {
            **payload,
            "routine_logic_inventory": {
                **inventory,
                "summary": pending_summary,
                "details": pending_details,
            },
        },
    )


def add_nonterminal_deep_read_batch(fixture: ProgramArtifactFixture) -> Path:
    """Add a retained batch checkpoint that still contains deterministic seed text."""

    batch_dir = fixture.analysis_dir / "routine-logic-details"
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_path = batch_dir / f"{fixture.prefix}-deep-read-batch-001.md"
    batch_path.write_text(
        f"""# Routine Logic Details: {fixture.program} - Deep Read Batch 001

## Calculation Logic

Pending semantic deep-read for this batch.

## Validation Logic

Pending semantic deep-read for this batch.

## Exception Handling

Pending semantic deep-read for this batch.

## Scope

One source-backed window is assigned to this checkpoint.

## Batch Coverage Summary

| Window ID | Routine | Source Lines | RLOG Detail |
| --- | --- | --- | --- |
| DRW-{fixture.prefix}-001 | MAIN | 1-100 | RLOG-{fixture.prefix}-001 |

## Message Inventory

No additional message token is recorded by this pending checkpoint.

## Routine Details

### RLOG-{fixture.prefix}-001 - MAIN

Semantic status: pending_deep_read. Pending semantic detail must be replaced
with source-backed execution, branch, carrier, outcome, and exception closure.
""",
        encoding="utf-8",
    )
    summary = json.loads(fixture.summary_yaml.read_text(encoding="utf-8"))
    sidecars = summary["sidecars"]
    _write_json_yaml(
        fixture.summary_yaml,
        {
            **summary,
            "sidecars": {
                **sidecars,
                "routine_logic_deep_read_batch_001": {
                    "path": str(batch_path.relative_to(fixture.analysis_dir)),
                    "status": "optional_triggered",
                },
            },
        },
    )
    return batch_path


def mark_program_analysis_placeholder(fixture: ProgramArtifactFixture) -> None:
    """Replace the reader entry with a placeholder while preserving the file set."""

    markdown = fixture.program_analysis.read_text(encoding="utf-8")
    start = markdown.index("## Program Reading Summary")
    end = markdown.index("## Calculation Logic")
    replacement = "## Program Reading Summary\n\nPending reader-oriented summary.\n\n"
    fixture.program_analysis.write_text(
        markdown[:start] + replacement + markdown[end:], encoding="utf-8"
    )


def mark_unresolved_message_description(fixture: ProgramArtifactFixture) -> None:
    """Leave an observed token without the description required for finalization."""

    unresolved = "unresolved - message description not available"
    markdown = fixture.program_analysis.read_text(encoding="utf-8").replace(
        "Requested account record was not found.", unresolved
    )
    fixture.program_analysis.write_text(markdown, encoding="utf-8")
    payload = json.loads(fixture.message_inventory_yaml.read_text(encoding="utf-8"))
    inventory = payload["message_inventory"]
    for bucket in ("summary", "details"):
        inventory[bucket] = [
            {
                **entry,
                "short_description": unresolved,
                "description_source": "missing",
                "evidence_status": "unresolved",
            }
            for entry in inventory[bucket]
        ]
    _write_json_yaml(fixture.message_inventory_yaml, payload)
