#!/usr/bin/env python3
"""Create deterministic structure-first index artifacts for RPG source.

The indexer is intentionally conservative. It extracts code structure,
call/file/message evidence, and recommended deep-read windows, but it does not
write business summaries or infer business rules.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


INTERNAL_CALL_RE = re.compile(r"\bEXSR\b\s+([A-Z0-9_#$@]+)", re.I)
CALLPRC_RE = re.compile(r"\bCALLPRC\b\s+['\"]?([A-Z0-9_#$@]+)['\"]?", re.I)
CALLP_RE = re.compile(r"\bCALLP\b\s+['\"]?([A-Z0-9_#$@]+)['\"]?", re.I)
CALL_RE = re.compile(r"\bCALL\b\s+['\"]?([A-Z0-9_#$@]+)['\"]?", re.I)
DCL_F_RE = re.compile(r"\bDCL-F\s+([A-Z0-9_#$@]+)", re.I)
FIXED_F_RE = re.compile(r"^F([A-Z0-9_#$@]{1,10})\s+")
PROC_BEGIN_RE = re.compile(r"\bDCL-PROC\s+([A-Z0-9_#$@]+)", re.I)
FIXED_BEGSR_RE = re.compile(r"^C\s+([A-Z0-9_#$@]+)\s+BEGSR\b", re.I)
FREE_BEGSR_RE = re.compile(r"\bBEGSR\b\s+([A-Z0-9_#$@]+)?", re.I)
FILE_OP_RE = re.compile(
    r"\b(CHAIN|SETLL|READE|READPE|READP|READ|WRITE|UPDATE|DELETE|EXFMT|"
    r"OPEN|CLOSE|COMMIT|ROLLBACK)\b\s*([A-Z0-9_#$@]+)?",
    re.I,
)
ASSIGNMENT_RE = re.compile(
    r"\b(EVAL|MOVE|MOVEL|Z-ADD|ADD|SUB|MULT|DIV|CLEAR|CAT)\b", re.I
)
MESSAGE_RE = re.compile(r"\b(CPF|CPD|MCH|RNX|SQL|UCC|LCC)[A-Z0-9]{3,8}\b", re.I)
ERROR_RE = re.compile(r"\b(MONMSG|MONITOR|ON-ERROR|%ERROR|SNDPGMMSG|SNDMSG)\b", re.I)

MUTATION_OPS = {"WRITE", "UPDATE", "DELETE"}
READ_OPS = {"CHAIN", "SETLL", "READE", "READPE", "READP", "READ", "OPEN", "CLOSE"}
TRANSACTION_OPS = {"COMMIT", "ROLLBACK"}


def strip_sequence(raw_line: str) -> str:
    """Remove common IBM i sequence columns when present."""
    if len(raw_line) > 6 and raw_line[:6].strip().isdigit():
        return raw_line[6:]
    return raw_line


def normalized(raw_line: str) -> str:
    return strip_sequence(raw_line).strip().rstrip(";").upper()


def scalar_to_yaml(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_./:@#$%+*-]+", text) and text.lower() not in {
        "true",
        "false",
        "null",
    }:
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_yaml(value: Any, indent: int = 0) -> str:
    pad = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict | list):
                if not item:
                    lines.append(f"{pad}{key}: []" if isinstance(item, list) else f"{pad}{key}: {{}}")
                else:
                    lines.append(f"{pad}{key}:")
                    lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {scalar_to_yaml(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict | list):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {scalar_to_yaml(item)}")
    else:
        lines.append(f"{pad}{scalar_to_yaml(value)}")
    return "\n".join(lines)


def table_cell(value: Any) -> str:
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value) if value else "-"
    else:
        text = str(value) if value not in (None, "") else "-"
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(table_cell(value) for value in row) + " |")
    return "\n".join(out)


def begin_routine(line: str) -> tuple[str, str] | None:
    proc = PROC_BEGIN_RE.search(line)
    if proc:
        return proc.group(1).upper(), "procedure"
    fixed = FIXED_BEGSR_RE.search(line)
    if fixed:
        return fixed.group(1).upper(), "subroutine"
    free = FREE_BEGSR_RE.search(line)
    if free and free.group(1):
        return free.group(1).upper(), "subroutine"
    return None


def operation_impact(operation: str) -> str:
    if operation in MUTATION_OPS:
        return {"WRITE": "creates", "UPDATE": "updates", "DELETE": "deletes"}[operation]
    if operation in TRANSACTION_OPS:
        return "transaction boundary"
    if operation == "EXFMT":
        return "screen/report boundary"
    if operation in READ_OPS:
        return "read-only"
    return "unknown"


def add_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def analysis_mode(line_count: int, routine_count: int, external_count: int, object_count: int) -> tuple[str, str]:
    if line_count > 10000:
        return "large_program", "source length exceeds 10,000 lines"
    if routine_count > 25:
        return "large_program", "routine count exceeds 25"
    if external_count > 20:
        return "large_program", "external call count exceeds 20"
    if object_count > 25:
        return "large_program", "object dependency count exceeds 25"
    if line_count > 3000 or routine_count > 10 or external_count > 8 or object_count > 10:
        return "segmented", "medium-size or dense source benefits from structure-first analysis"
    return "standard", "source is below large-program thresholds"


def analyze_source(lines: list[str], program_name: str, source_path: Path | None = None) -> dict[str, Any]:
    routines: dict[str, dict[str, Any]] = {
        "MAIN": {
            "name": "MAIN",
            "type": "mainline",
            "start_line": 1,
            "end_line": len(lines),
            "called_by": ["external program entry"],
            "calls_out": [],
            "data_touches": [],
            "state_impact": "unknown",
            "error_handling": "none observed",
            "coverage": "indexed_only",
            "recommended_deep_read": False,
            "deep_read_reasons": [],
        }
    }
    calls: list[dict[str, Any]] = []
    file_operations: list[dict[str, Any]] = []
    declared_files: dict[str, dict[str, Any]] = {}
    messages: list[dict[str, Any]] = []
    assignment_buffer: list[dict[str, Any]] = []

    active_name = "MAIN"
    active_start = 1
    active_type = "mainline"
    first_routine_line: int | None = None

    for line_number, raw_line in enumerate(lines, start=1):
        line = normalized(raw_line)
        if not line:
            continue

        maybe_begin = begin_routine(line)
        if maybe_begin:
            if active_name != "MAIN":
                routines[active_name]["end_line"] = line_number - 1
            elif first_routine_line is None:
                first_routine_line = line_number
                routines["MAIN"]["end_line"] = max(1, line_number - 1)
            active_name, active_type = maybe_begin
            active_start = line_number
            routines[active_name] = {
                "name": active_name,
                "type": active_type,
                "start_line": active_start,
                "end_line": line_number,
                "called_by": [],
                "calls_out": [],
                "data_touches": [],
                "state_impact": "unknown",
                "error_handling": "none observed",
                "coverage": "indexed_only",
                "recommended_deep_read": False,
                "deep_read_reasons": [],
            }

        if "ENDSR" in line and active_name != "MAIN":
            routines[active_name]["end_line"] = line_number
            active_name = "MAIN"
        elif "END-PROC" in line and active_name != "MAIN":
            routines[active_name]["end_line"] = line_number
            active_name = "MAIN"

        dcl_file = DCL_F_RE.search(line)
        fixed_file = FIXED_F_RE.search(line)
        if dcl_file or fixed_file:
            file_name = (dcl_file or fixed_file).group(1).upper()
            declared_files[file_name] = {
                "name": file_name,
                "declared_at": line_number,
                "source": "DCL-F" if dcl_file else "F-spec",
            }

        if ASSIGNMENT_RE.search(line):
            assignment_buffer.append({"line": line_number, "text": strip_sequence(raw_line).strip()})
            assignment_buffer = assignment_buffer[-12:]

        for call_type, pattern in (
            ("internal_subroutine", INTERNAL_CALL_RE),
            ("external_program", CALLPRC_RE),
            ("external_program", CALLP_RE),
            ("external_program", CALL_RE),
        ):
            for match in pattern.finditer(line):
                target = match.group(1).upper()
                calls.append(
                    {
                        "caller": active_name,
                        "target": target,
                        "call_type": call_type,
                        "line": line_number,
                        "evidence": f"source line {line_number}",
                    }
                )

        for match in FILE_OP_RE.finditer(line):
            operation = match.group(1).upper()
            obj = (match.group(2) or "").upper()
            if operation == "OPEN" and obj == "":
                continue
            file_operations.append(
                {
                    "routine": active_name,
                    "operation": operation,
                    "object": obj or "unresolved",
                    "line": line_number,
                    "state_impact": operation_impact(operation),
                    "recent_assignments": assignment_buffer[-8:] if operation in MUTATION_OPS else [],
                    "evidence": f"source line {line_number}",
                }
            )

        for message_match in MESSAGE_RE.finditer(line):
            messages.append(
                {
                    "routine": active_name,
                    "code": message_match.group(0).upper(),
                    "line": line_number,
                    "evidence": f"source line {line_number}",
                }
            )

        if ERROR_RE.search(line):
            routines[active_name]["error_handling"] = "message/error path observed"

    if active_name != "MAIN":
        routines[active_name]["end_line"] = len(lines)

    routine_names = set(routines)
    external_calls: list[dict[str, Any]] = []
    for call in calls:
        caller = call["caller"]
        target = call["target"]
        add_unique(routines[caller]["calls_out"], target)
        if target in routine_names:
            add_unique(routines[target]["called_by"], f"{caller} line {call['line']}")
            if call["call_type"] != "internal_subroutine":
                call["call_type"] = "internal_procedure"
        else:
            external_calls.append(call)

    for operation in file_operations:
        routine = routines[operation["routine"]]
        add_unique(routine["data_touches"], f"{operation['operation']} {operation['object']}")
        current = routine["state_impact"]
        impact = operation["state_impact"]
        if current == "unknown" or impact != "read-only":
            routine["state_impact"] = impact

    message_routines = {message["routine"] for message in messages}
    external_call_routines = {call["caller"] for call in external_calls}
    mutation_routines = {
        operation["routine"]
        for operation in file_operations
        if operation["operation"] in MUTATION_OPS or operation["operation"] in TRANSACTION_OPS
    }

    for routine in routines.values():
        if routine["name"] == "MAIN":
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("entry path")
        if routine["name"] in mutation_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("state-changing file operation")
        if routine["name"] in external_call_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("external call boundary")
        if routine["name"] in message_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("message/status handling")
            routine["error_handling"] = "message/error path observed"
        if not routine["called_by"] and routine["name"] != "MAIN":
            routine["called_by"] = ["not observed in source index"]

    object_names = {
        item["name"] for item in declared_files.values()
    } | {op["object"] for op in file_operations if op["object"] != "unresolved"}
    mode, reason = analysis_mode(
        len(lines),
        len(routines),
        len(external_calls),
        len(object_names),
    )
    deep_read_windows = [
        {
            "window_id": f"DRW-{program_name.upper()}-{index:03d}",
            "routine": routine["name"],
            "source_lines": f"{routine['start_line']}-{routine['end_line']}",
            "why_selected": "; ".join(routine["deep_read_reasons"]),
            "coverage_outcome": "selected_for_deep_read",
            "evidence": "source-index",
        }
        for index, routine in enumerate(routines.values(), start=1)
        if routine["recommended_deep_read"]
    ]

    return {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": program_name.upper(),
        "source": {
            "path": str(source_path) if source_path else "stdin",
            "line_count": len(lines),
        },
        "analysis_mode": mode,
        "mode_reason": reason,
        "counts": {
            "routines": len(routines),
            "external_calls": len(external_calls),
            "object_dependencies": len(object_names),
            "file_operations": len(file_operations),
            "messages": len(messages),
            "recommended_deep_read_windows": len(deep_read_windows),
        },
        "declared_files": list(declared_files.values()),
        "routines": list(routines.values()),
        "calls": calls,
        "external_calls": external_calls,
        "file_operations": file_operations,
        "messages": messages,
        "deep_read_windows": deep_read_windows,
        "contract_note": (
            "This structure index is pre-analysis evidence. It is not a "
            "business summary and does not make downstream-ready claims."
        ),
    }


def render_routine_index(index: dict[str, Any]) -> str:
    routine_rows = [
        [
            routine["name"],
            routine["type"],
            f"{routine['start_line']}-{routine['end_line']}",
            routine["called_by"],
            routine["calls_out"],
            routine["data_touches"],
            routine["state_impact"],
            routine["coverage"],
            routine["deep_read_reasons"],
        ]
        for routine in index["routines"]
    ]
    call_rows = [
        [
            call["caller"],
            call["target"],
            call["call_type"],
            call["line"],
            call["evidence"],
        ]
        for call in index["calls"]
    ]
    file_rows = [
        [
            op["routine"],
            op["operation"],
            op["object"],
            op["line"],
            op["state_impact"],
            op["evidence"],
        ]
        for op in index["file_operations"]
    ]
    message_rows = [
        [message["routine"], message["code"], message["line"], message["evidence"]]
        for message in index["messages"]
    ]

    return "\n\n".join(
        [
            f"# Routine Index: {index['program']}",
            "## Source Size & Strategy",
            markdown_table(
                ["Program", "Source Lines", "Analysis Mode", "Mode Reason"],
                [
                    [
                        index["program"],
                        index["source"]["line_count"],
                        index["analysis_mode"],
                        index["mode_reason"],
                    ]
                ],
            ),
            "## Routine Cards Seed",
            markdown_table(
                [
                    "Routine",
                    "Type",
                    "Lines",
                    "Called By",
                    "Calls Out",
                    "Data Touches",
                    "State Impact",
                    "Coverage",
                    "Deep Read Reason",
                ],
                routine_rows,
            ),
            "## Call Evidence Seed",
            markdown_table(["Caller", "Callee", "Call Type", "Line", "Evidence"], call_rows),
            "## File Operation Seed",
            markdown_table(["Routine", "Operation", "Object", "Line", "State Impact", "Evidence"], file_rows),
            "## Message / Status Seed",
            markdown_table(["Routine", "Code", "Line", "Evidence"], message_rows),
        ]
    ) + "\n"


def render_coverage_ledger(index: dict[str, Any]) -> str:
    counts = index["counts"]
    routine_rows = [
        [
            routine["name"],
            routine["coverage"],
            "yes" if routine["recommended_deep_read"] else "no",
            routine["deep_read_reasons"],
            "pre-analysis index only",
        ]
        for routine in index["routines"]
    ]
    return "\n\n".join(
        [
            f"# All Routine Coverage Ledger: {index['program']}",
            "## Coverage Metrics",
            markdown_table(
                ["Metric", "Count / Value", "Notes"],
                [
                    ["Source Lines", index["source"]["line_count"], "full source indexed"],
                    ["Analysis Mode", index["analysis_mode"], index["mode_reason"]],
                    ["Routines Found", counts["routines"], "mainline + detected routines/procedures"],
                    ["Routines Deep-Read", "0", "script selects windows but does not perform semantic deep read"],
                    ["Routines Indexed Only", counts["routines"], "all routines remain indexed_only until LLM/human deep read"],
                    ["External Edges Resolved", counts["external_calls"], "targets extracted from visible call sites"],
                    ["Data Touches Resolved", counts["file_operations"], "objects are source tokens; DDS mapping may still be pending"],
                    ["Blocking Gaps", "0", "not evaluated by source indexer"],
                    ["Non-Blocking Gaps", "0", "not evaluated by source indexer"],
                ],
            ),
            "## Routine Coverage Summary",
            markdown_table(
                ["Routine", "Coverage", "Deep Read Recommended", "Reason", "Evidence / Review"],
                routine_rows,
            ),
        ]
    ) + "\n"


def render_deep_read_plan(index: dict[str, Any]) -> str:
    rows = [
        [
            window["routine"],
            window["source_lines"],
            window["why_selected"],
            window["coverage_outcome"],
            window["evidence"],
        ]
        for window in index["deep_read_windows"]
    ]
    if not rows:
        rows = [["-", "-", "no high-risk window selected by static index", "-", "-"]]
    return "\n\n".join(
        [
            f"# Deep Read Plan: {index['program']}",
            "Use these windows as semantic units for large-program analysis. "
            "Do not synthesize business behavior from this plan alone.",
            markdown_table(
                ["Routine", "Source Lines", "Why Selected", "Coverage Outcome", "Evidence"],
                rows,
            ),
            "## Next Step Contract",
            "- Populate `Routine Logic Details` only after the listed window is deep-read.",
            "- Keep routines as `indexed_only` until semantic analysis cites source ranges.",
            "- Record unresolved DDS, dynamic call, message text, and SME questions as TBDs.",
        ]
    ) + "\n"


def write_artifacts(index: dict[str, Any], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [
        (out_dir / "source-index.yaml", to_yaml(index) + "\n"),
        (out_dir / "routine-index.md", render_routine_index(index)),
        (out_dir / "all-routine-coverage-ledger.md", render_coverage_ledger(index)),
        (out_dir / "deep-read-plan.md", render_deep_read_plan(index)),
    ]
    written: list[Path] = []
    for path, content in files:
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build source-index artifacts for RPG/RPGLE large-program analysis."
    )
    parser.add_argument("source", type=Path, help="RPG/RPGLE source member text file")
    parser.add_argument("--program", help="Program/member name; defaults to source stem")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="Directory for generated artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.source.exists():
        print(f"Source file not found: {args.source}", file=sys.stderr)
        return 2
    text = args.source.read_text(encoding="utf-8", errors="replace")
    program = args.program or args.source.stem
    index = analyze_source(text.splitlines(), program_name=program, source_path=args.source)
    written = write_artifacts(index, args.out_dir)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
