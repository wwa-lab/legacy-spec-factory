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
DCL_PI_RE = re.compile(r"\bDCL-PI\b\s*([A-Z0-9_#$@*]+)?", re.I)
DCL_PR_RE = re.compile(r"\bDCL-PR\b\s+([A-Z0-9_#$@*]+)", re.I)
DCL_DS_RE = re.compile(r"\bDCL-DS\b\s+([A-Z0-9_#$@*]+)", re.I)
DCL_S_RE = re.compile(r"\bDCL-S\b\s+([A-Z0-9_#$@*]+)", re.I)
FIXED_F_RE = re.compile(r"^F([A-Z0-9_#$@]{1,10})\s+")
PROC_BEGIN_RE = re.compile(r"\bDCL-PROC\s+([A-Z0-9_#$@]+)", re.I)
FIXED_C_SPEC_RE = re.compile(
    r"^(?:(?:\S+\s+)?C(?!\*)|(?!EXEC\b)[A-Z0-9_#$@]+C(?!\*))\s+(.*)$",
)
FIXED_C_COMMENT_RE = re.compile(r"^(?:(?:\S+\s+)?C|[A-Z0-9_#$@]+C)\*")
FIXED_SR_NAME_RE = re.compile(r"^SR[A-Z0-9_#$@]*$", re.I)
FREE_BEGSR_RE = re.compile(r"\bBEGSR\b\s+([A-Z0-9_#$@*]+)?", re.I)
FILE_OP_RE = re.compile(
    r"\b(CHAIN|SETLL|READE|READPE|READP|READ|WRITE|UPDATE|DELETE|EXFMT|"
    r"OPEN|CLOSE|COMMIT|ROLLBACK)\b\s*([A-Z0-9_#$@]+)?",
    re.I,
)
ASSIGNMENT_RE = re.compile(
    r"\b(EVAL|MOVE|MOVEL|Z-ADD|ADD|SUB|MULT|DIV|CLEAR|CAT)\b", re.I
)
FREE_ASSIGNMENT_RE = re.compile(
    r"^\s*([A-Z0-9_#$@.]+)\s*=\s*(?!=)(.+)$",
    re.I,
)
FREE_PROC_CALL_RE = re.compile(r"^\s*([A-Z][A-Z0-9_#$@]*)\s*\((.*)\)\s*$", re.I)
MESSAGE_RE = re.compile(r"\b(CPF|CPD|MCH|RNX|SQL|UCC|LCC)[A-Z0-9]{3,8}\b", re.I)
SQL_STATUS_RE = re.compile(r"\b(SQLCODE|SQLSTATE)\b", re.I)
ERROR_RE = re.compile(r"\b(MONMSG|MONITOR|ON-ERROR|%ERROR|SNDPGMMSG|SNDMSG)\b", re.I)
BRANCH_AFTER_IO_RE = re.compile(r"\b(IF|WHEN|DOW|DOU|SELECT|ELSEIF)\b|%FOUND|%EOF|%EQUAL", re.I)
OUTCOME_CARRIER_RE = re.compile(
    r"\b[A-Z0-9_#$@]*(?:STS|STAT|STATUS|RESP|RSP|RC|RET|RETURN|MSG|ERR|ERROR|"
    r"CODE|AUTH|APPR|DECL|DENY|REJ|CARD|ACCT|CUST|AMT|AMOUNT|ARPC|CRYPTO)"
    r"[A-Z0-9_#$@]*\b",
    re.I,
)

MUTATION_OPS = {"WRITE", "UPDATE", "DELETE"}
READ_OPS = {"CHAIN", "SETLL", "READE", "READPE", "READP", "READ", "OPEN", "CLOSE"}
DATA_READ_OPS = {"CHAIN", "SETLL", "READE", "READPE", "READP", "READ"}
TRANSACTION_OPS = {"COMMIT", "ROLLBACK"}
SQL_DML_OPS = {"INSERT", "UPDATE", "DELETE", "MERGE"}
FREE_F_SPEC_BLOCKERS = {"FOR", "FROM"}
FREE_ASSIGNMENT_BLOCKERS = {
    "IF",
    "WHEN",
    "DOW",
    "DOU",
    "FOR",
    "ELSEIF",
    "RETURN",
    "MONITOR",
    "ON-ERROR",
}
FREE_PROC_CALL_BLOCKERS = {
    "IF",
    "WHEN",
    "DOW",
    "DOU",
    "FOR",
    "SELECT",
    "RETURN",
    "EVAL",
}


def strip_sequence(raw_line: str) -> str:
    """Remove common IBM i sequence columns when present."""
    if len(raw_line) > 6 and raw_line[:6].strip().isdigit():
        return raw_line[6:]
    return raw_line


def normalized(raw_line: str) -> str:
    return strip_sequence(raw_line).strip().rstrip(";").upper()


def is_rpg_comment(raw_line: str) -> bool:
    text = strip_sequence(raw_line).lstrip()
    upper = text.upper()
    return (
        not text
        or text.startswith("//")
        or text.startswith("*")
        or upper.startswith("C*")
        or upper.startswith("/*")
        or upper.startswith("*/")
    )


def statement_text(raw_lines: list[str]) -> str:
    parts = []
    for raw_line in raw_lines:
        text = strip_sequence(raw_line).strip()
        if text.startswith("//"):
            continue
        if "//" in text:
            text = text.split("//", 1)[0].rstrip()
        if text:
            parts.append(text.rstrip(";"))
    return re.sub(r"\s+", " ", " ".join(parts)).strip().upper()


def build_statements(lines: list[str]) -> list[dict[str, Any]]:
    """Build conservative free-format statement spans from semicolon boundaries."""
    statements: list[dict[str, Any]] = []
    current: list[str] = []
    start_line: int | None = None

    for line_number, raw_line in enumerate(lines, start=1):
        if is_rpg_comment(raw_line):
            continue
        text = strip_sequence(raw_line).strip()
        if not text:
            continue
        if start_line is None:
            start_line = line_number
        current.append(raw_line)
        if ";" in text:
            text_value = statement_text(current)
            if text_value:
                statements.append(
                    {
                        "start_line": start_line,
                        "end_line": line_number,
                        "text": text_value,
                        "source_text": " ".join(strip_sequence(item).strip() for item in current),
                    }
                )
            current = []
            start_line = None

    if current and start_line is not None:
        text_value = statement_text(current)
        if text_value:
            statements.append(
                {
                    "start_line": start_line,
                    "end_line": len(lines),
                    "text": text_value,
                    "source_text": " ".join(strip_sequence(item).strip() for item in current),
                }
            )
    return statements


def first_token(text: str) -> str:
    match = re.match(r"\s*([A-Z0-9_#$@%-]+)", text, re.I)
    return match.group(1).upper() if match else ""


def is_free_assignment(line: str) -> bool:
    if first_token(line) in FREE_ASSIGNMENT_BLOCKERS:
        return False
    return bool(FREE_ASSIGNMENT_RE.match(line))


def free_assignment(line: str, line_number: int, raw_line: str, routine: str) -> dict[str, Any] | None:
    if not is_free_assignment(line):
        return None
    match = FREE_ASSIGNMENT_RE.match(line)
    if not match:
        return None
    return {
        "line": line_number,
        "routine": routine,
        "target": match.group(1).upper(),
        "expression": match.group(2).strip(),
        "assignment_type": "free_format_assignment",
        "text": strip_sequence(raw_line).strip(),
        "evidence": f"source line {line_number}",
    }


def is_free_proc_call(line: str) -> bool:
    token = first_token(line)
    if token in FREE_PROC_CALL_BLOCKERS or token.startswith("%") or token.startswith("DCL-"):
        return False
    if "=" in line:
        return False
    return bool(FREE_PROC_CALL_RE.match(line))


def declaration_from_line(line: str, line_number: int) -> dict[str, Any] | None:
    for kind, pattern in (
        ("DCL-PI", DCL_PI_RE),
        ("DCL-PR", DCL_PR_RE),
        ("DCL-DS", DCL_DS_RE),
        ("DCL-S", DCL_S_RE),
    ):
        match = pattern.search(line)
        if match:
            return {
                "kind": kind,
                "name": (match.group(1) or "*N").upper(),
                "line": line_number,
                "evidence": f"source line {line_number}",
            }
    return None


def sql_text_from_statement(statement: dict[str, Any]) -> str | None:
    text = statement["text"]
    if "EXEC SQL" in text:
        return text.split("EXEC SQL", 1)[1].strip()
    if re.match(r"^(SELECT|INSERT|UPDATE|DELETE|MERGE|DECLARE|OPEN|FETCH|CLOSE)\b", text):
        return text
    return None


def sql_statement_type(sql_text: str) -> str:
    match = re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|MERGE|DECLARE|OPEN|FETCH|CLOSE)\b", sql_text)
    return match.group(1).upper() if match else "UNKNOWN"


def sql_table_or_view(sql_text: str, statement_type: str) -> str:
    patterns = {
        "SELECT": r"\bFROM\s+([A-Z0-9_#$@./]+)",
        "INSERT": r"\bINTO\s+([A-Z0-9_#$@./]+)",
        "UPDATE": r"\bUPDATE\s+([A-Z0-9_#$@./]+)",
        "DELETE": r"\bDELETE\s+FROM\s+([A-Z0-9_#$@./]+)",
        "MERGE": r"\bMERGE\s+INTO\s+([A-Z0-9_#$@./]+)",
        "DECLARE": r"\bFROM\s+([A-Z0-9_#$@./]+)",
    }
    pattern = patterns.get(statement_type)
    if not pattern:
        return "unresolved"
    match = re.search(pattern, sql_text)
    return match.group(1).upper() if match else "unresolved"


def build_sql_inventory(
    statements: list[dict[str, Any]],
    program_name: str,
    line_to_routine: dict[int, str],
) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    for number, statement in enumerate(statements, start=1):
        sql_text = sql_text_from_statement(statement)
        if not sql_text:
            continue
        statement_type = sql_statement_type(sql_text)
        detail_id = f"SQL-{program_name.upper()}-{len(details) + 1:03d}"
        host_variables = sorted({item.upper() for item in re.findall(r":[A-Z0-9_#$@.]+", sql_text, re.I)})
        details.append(
            {
                "detail_id": detail_id,
                "statement_type": statement_type,
                "table_or_view": sql_table_or_view(sql_text, statement_type),
                "routine": line_to_routine.get(statement["start_line"], "unknown"),
                "source_lines": f"{statement['start_line']}-{statement['end_line']}",
                "host_variables": host_variables,
                "sql_text": sql_text,
                "state_impact": "mutates persistent state" if statement_type in SQL_DML_OPS else "read/query or cursor",
                "status_handling": "check SQLCODE/SQLSTATE near this statement",
                "evidence": f"source lines {statement['start_line']}-{statement['end_line']}",
            }
        )

    summary: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for detail in details:
        grouped.setdefault((detail["statement_type"], detail["table_or_view"]), []).append(detail)
    for number, ((statement_type, table_or_view), group) in enumerate(grouped.items(), start=1):
        routines: list[str] = []
        host_variables: list[str] = []
        for detail in group:
            add_unique(routines, detail["routine"])
            for host_variable in detail["host_variables"]:
                add_unique(host_variables, host_variable)
        summary.append(
            {
                "summary_id": f"SQLSUM-{program_name.upper()}-{number:03d}",
                "statement_type": statement_type,
                "table_or_view": table_or_view,
                "occurrence_count": len(group),
                "routines": routines,
                "host_variables": host_variables,
                "detail_refs": [detail["detail_id"] for detail in group],
            }
        )

    return {
        "summary": summary,
        "details": details,
        "sidecar_markdown": "sql-inventory.md",
        "sidecar_yaml": "sql-inventory.yaml",
    }


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


def fixed_c_spec_tokens(line: str) -> list[str]:
    match = FIXED_C_SPEC_RE.match(line)
    if not match:
        return []
    return match.group(1).split()


def fixed_file_name_from_line(line: str) -> str | None:
    if fixed_c_spec_tokens(line) or is_fixed_c_comment(line):
        return None
    match = FIXED_F_RE.search(line)
    if not match:
        return None
    first = first_token(line)
    if first in FREE_F_SPEC_BLOCKERS:
        return None
    if len(line.split()) < 3:
        return None
    return match.group(1).upper()


def is_fixed_c_comment(line: str) -> bool:
    return bool(FIXED_C_COMMENT_RE.match(line))


def fixed_routine_name_for_opcode(line: str, opcode: str) -> str | None:
    tokens = fixed_c_spec_tokens(line)
    for index, token in enumerate(tokens):
        if token.upper() == opcode and index > 0:
            candidate = tokens[index - 1].upper()
            if FIXED_SR_NAME_RE.fullmatch(candidate):
                return candidate
    return None


def begin_routine(line: str) -> tuple[str, str] | None:
    proc = PROC_BEGIN_RE.search(line)
    if proc:
        return proc.group(1).upper(), "procedure"
    fixed = fixed_routine_name_for_opcode(line, "BEGSR")
    if fixed:
        return fixed, "subroutine"
    if fixed_c_spec_tokens(line) or is_fixed_c_comment(line):
        return None
    free = FREE_BEGSR_RE.search(line)
    if free and free.group(1):
        return free.group(1).upper(), "subroutine"
    return None


def ends_routine(line: str, active_name: str) -> bool:
    fixed = fixed_routine_name_for_opcode(line, "ENDSR")
    if fixed:
        return fixed in {active_name, f"{active_name}E"}
    if fixed_c_spec_tokens(line) or is_fixed_c_comment(line):
        return False
    return bool(re.search(r"\bENDSR\b", line, re.I))


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


def build_message_inventory(messages: list[dict[str, Any]], program_name: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for message in messages:
        grouped.setdefault(message["code"], []).append(message)

    details: list[dict[str, Any]] = []
    for index, (code, occurrences) in enumerate(grouped.items(), start=1):
        routines: list[str] = []
        for occurrence in occurrences:
            add_unique(routines, occurrence["routine"])
        detail_id = f"MSG-{program_name.upper()}-{index:03d}"
        details.append(
            {
                "detail_id": detail_id,
                "message": code,
                "short_description": "unresolved - message description not available",
                "description_source": "unresolved",
                "occurrence_count": len(occurrences),
                "routines": routines,
                "first_seen": f"source line {occurrences[0]['line']}",
                "emitted_or_set_by": "source token observed; semantic trigger pending deep read",
                "trigger_or_handler": "pending deep read",
                "carrier_or_destination": "pending deep read",
                "related_validation_or_exception": "pending program-analysis trace",
                "evidence_status": "unresolved",
                "occurrences": occurrences,
            }
        )

    summary = [
        {
            "message": detail["message"],
            "short_description": detail["short_description"],
            "description_source": detail["description_source"],
            "occurrence_count": detail["occurrence_count"],
            "routines": detail["routines"],
            "first_seen": detail["first_seen"],
            "detail_ref": detail["detail_id"],
            "evidence_status": detail["evidence_status"],
        }
        for detail in details
    ]

    return {
        "summary": summary,
        "details": details,
        "sidecar_markdown": "message-inventory.md",
        "sidecar_yaml": "message-inventory.yaml",
    }


def routine_role(routine: dict[str, Any]) -> str:
    reasons = set(routine["deep_read_reasons"])
    if routine["name"] == "MAIN":
        return "entry dispatch"
    if "state-changing file operation" in reasons:
        return "state-changing routine"
    if "external call boundary" in reasons:
        return "external boundary"
    if "message/status handling" in reasons or "outcome/status carrier assignment" in reasons:
        return "validation/message routine"
    if "read-conditioned branch" in reasons:
        return "read-conditioned branch"
    if routine["recommended_deep_read"]:
        return "deep-read candidate"
    return "indexed utility"


def build_routine_logic_inventory(index: dict[str, Any]) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    for number, routine in enumerate(index["routines"], start=1):
        detail_id = f"RLOG-{index['program']}-{number:03d}"
        details.append(
            {
                "detail_id": detail_id,
                "routine": routine["name"],
                "role": routine_role(routine),
                "source_lines": f"{routine['start_line']}-{routine['end_line']}",
                "called_by": routine["called_by"],
                "calls_out": routine["calls_out"],
                "data_touches": routine["data_touches"],
                "state_impact": routine["state_impact"],
                "error_handling": routine["error_handling"],
                "coverage": routine["coverage"],
                "deep_read_recommended": routine["recommended_deep_read"],
                "deep_read_reasons": routine["deep_read_reasons"],
                "semantic_status": "pending_deep_read",
                "execution_trigger": "pending deep read",
                "step_by_step_logic": [],
                "field_calculations": [],
                "conditioned_calculation_blocks": [],
                "outcome_reverse_traces": [],
                "field_lineage": [],
                "branch_outcomes": [],
                "routine_exception_closure": [],
                "unresolved_routine_logic": "pending deep read",
            }
        )

    summary = [
        {
            "routine": detail["routine"],
            "role": detail["role"],
            "source_lines": detail["source_lines"],
            "coverage": detail["coverage"],
            "deep_read_recommended": detail["deep_read_recommended"],
            "deep_read_reasons": detail["deep_read_reasons"],
            "state_impact": detail["state_impact"],
            "detail_ref": detail["detail_id"],
            "semantic_status": detail["semantic_status"],
        }
        for detail in details
    ]
    return {
        "summary": summary,
        "details": details,
        "sidecar_markdown": "routine-logic-details.md",
        "sidecar_yaml": "routine-logic-details.yaml",
        "sharding_guidance": {
            "main_document_limit": "summarize only when routines > 25",
            "part_files_required_when": "routines > 80 or source lines > 10000",
            "part_file_front_matter": (
                "Each routine-logic-details/part-*.md file must start with "
                "batch-scoped Calculation Logic, Validation Logic, Exception "
                "Handling, and Message Inventory sections before per-routine "
                "detail. Message Inventory must list every exact "
                "message/status/literal observed in that batch."
            ),
            "final_consolidation_required": (
                "After batch deep-read, merge all part files into one final "
                "routine-logic-details.md SME review document with whole-program "
                "Calculation Logic, Validation Logic, Exception Handling, "
                "Message Inventory, Routine Detail Index, and all Routine "
                "Details. Part files are working shards, not the final SME "
                "review surface."
            ),
            "part_file_examples": [
                "routine-logic-details/part-01-mainline-and-dispatch.md",
                "routine-logic-details/part-02-state-changing-routines.md",
                "routine-logic-details/part-03-validation-and-message-routines.md",
                "routine-logic-details/part-04-external-boundaries.md",
                "routine-logic-details/part-05-indexed-utility-routines.md",
            ],
        },
    }


def build_file_io_inventory(file_operations: list[dict[str, Any]], program_name: str) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    for number, operation in enumerate(file_operations, start=1):
        detail_id = f"FIO-{program_name.upper()}-{number:03d}"
        details.append(
            {
                "detail_id": detail_id,
                "routine": operation["routine"],
                "operation": operation["operation"],
                "object": operation["object"],
                "line": operation["line"],
                "state_impact": operation["state_impact"],
                "recent_assignments": operation.get("recent_assignments", []),
                "evidence": operation["evidence"],
            }
        )

    grouped: dict[str, list[dict[str, Any]]] = {}
    for detail in details:
        grouped.setdefault(detail["object"], []).append(detail)

    summary: list[dict[str, Any]] = []
    for number, (obj, group) in enumerate(grouped.items(), start=1):
        operations: list[str] = []
        routines: list[str] = []
        impacts: list[str] = []
        for detail in group:
            add_unique(operations, detail["operation"])
            add_unique(routines, detail["routine"])
            add_unique(impacts, detail["state_impact"])
        summary.append(
            {
                "summary_id": f"FIOSUM-{program_name.upper()}-{number:03d}",
                "object": obj,
                "operations": operations,
                "routines": routines,
                "occurrence_count": len(group),
                "state_impact_summary": impacts,
                "detail_refs": [detail["detail_id"] for detail in group],
            }
        )

    return {
        "summary": summary,
        "details": details,
        "sidecar_markdown": "file-io-inventory.md",
        "sidecar_yaml": "file-io-inventory.yaml",
    }


def build_field_mutation_inventory(
    file_operations: list[dict[str, Any]],
    sql_inventory: dict[str, Any],
    program_name: str,
) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    for operation in file_operations:
        if operation["operation"] not in MUTATION_OPS:
            continue
        details.append(
            {
                "detail_id": f"MUT-{program_name.upper()}-{len(details) + 1:03d}",
                "mutation_source": "native_file_operation",
                "routine": operation["routine"],
                "operation": operation["operation"],
                "object": operation["object"],
                "source_lines": str(operation["line"]),
                "recent_assignments": operation.get("recent_assignments", []),
                "host_variables": [],
                "commit_or_rollback": "pending deep read",
                "evidence": operation["evidence"],
            }
        )

    for sql_detail in sql_inventory["details"]:
        if sql_detail["statement_type"] not in SQL_DML_OPS:
            continue
        details.append(
            {
                "detail_id": f"MUT-{program_name.upper()}-{len(details) + 1:03d}",
                "mutation_source": "embedded_sql",
                "routine": sql_detail["routine"],
                "operation": f"SQL {sql_detail['statement_type']}",
                "object": sql_detail["table_or_view"],
                "source_lines": sql_detail["source_lines"],
                "recent_assignments": [],
                "host_variables": sql_detail["host_variables"],
                "commit_or_rollback": "pending deep read",
                "evidence": sql_detail["evidence"],
            }
        )

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for detail in details:
        grouped.setdefault((detail["object"], detail["operation"]), []).append(detail)

    summary: list[dict[str, Any]] = []
    for number, ((obj, operation), group) in enumerate(grouped.items(), start=1):
        routines: list[str] = []
        for detail in group:
            add_unique(routines, detail["routine"])
        summary.append(
            {
                "summary_id": f"MUTSUM-{program_name.upper()}-{number:03d}",
                "object": obj,
                "operation": operation,
                "occurrence_count": len(group),
                "routines": routines,
                "detail_refs": [detail["detail_id"] for detail in group],
            }
        )

    return {
        "summary": summary,
        "details": details,
        "sidecar_markdown": "field-mutation-matrix.md",
        "sidecar_yaml": "field-mutation-matrix.yaml",
    }


def detect_program_profile(
    lines: list[str],
    source_path: Path | None,
    statements: list[dict[str, Any]],
    declarations: list[dict[str, Any]],
) -> dict[str, Any]:
    suffix = source_path.suffix.upper().lstrip(".") if source_path else ""
    full_text = "\n".join(strip_sequence(line) for line in lines).upper()
    statement_texts = " ".join(statement["text"] for statement in statements)
    has_exec_sql = "EXEC SQL" in full_text or any(sql_text_from_statement(stmt) for stmt in statements)
    has_free_marker = "**FREE" in full_text or "/FREE" in full_text
    has_free_declaration = any(declaration["kind"].startswith("DCL-") for declaration in declarations)
    has_fixed_specs = any(
        fixed_c_spec_tokens(normalized(line)) or fixed_file_name_from_line(normalized(line))
        for line in lines
    )

    if suffix == "SQLRPGLE" or has_exec_sql:
        program_type = "SQLRPGLE"
    elif suffix in {"RPGLE", "RPG"} or has_free_marker or has_free_declaration:
        program_type = "RPGLE"
    else:
        program_type = suffix or "unknown"

    if (has_free_marker or has_free_declaration) and has_fixed_specs:
        syntax_mode = "mixed"
    elif has_free_marker or has_free_declaration:
        syntax_mode = "free_format"
    elif has_fixed_specs:
        syntax_mode = "fixed_format"
    else:
        syntax_mode = "unknown"

    api_tokens = ("REQUEST", "RESPONSE", "JSON", "XML", "HTTP", "REST", "IWS", "API")
    if any(token in statement_texts or token in full_text for token in api_tokens):
        interface_profile = "api_remote"
    elif any(declaration["kind"] == "DCL-PI" for declaration in declarations):
        interface_profile = "callable_program"
    elif "SBMJOB" in full_text or "JOB" in full_text:
        interface_profile = "batch_worker"
    else:
        interface_profile = "unknown"

    return {
        "program_type": program_type,
        "syntax_mode": syntax_mode,
        "interface_profile": interface_profile,
        "source_suffix": suffix or "unknown",
        "has_embedded_sql": has_exec_sql,
        "declaration_count": len(declarations),
        "statement_count": len(statements),
    }


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


def program_size_tier(
    *,
    line_count: int,
    routine_count: int,
    external_count: int,
    object_count: int,
    file_operation_count: int,
    field_mutation_count: int,
    sql_statement_count: int,
    unique_message_count: int,
    recommended_deep_read_count: int,
) -> dict[str, Any]:
    """Return the SME-facing output tier without changing legacy analysis_mode."""
    if line_count > 10000:
        return {
            "tier": "large_extreme_program",
            "reason": "source length exceeds 10,000 lines",
            "default_output_profile": "full_index_and_batched_deep_read",
        }
    if routine_count > 25:
        return {
            "tier": "large_extreme_program",
            "reason": "routine count exceeds 25",
            "default_output_profile": "full_index_and_batched_deep_read",
        }
    if external_count > 20:
        return {
            "tier": "large_extreme_program",
            "reason": "external call count exceeds 20",
            "default_output_profile": "full_index_and_batched_deep_read",
        }
    if object_count > 25:
        return {
            "tier": "large_extreme_program",
            "reason": "object dependency count exceeds 25",
            "default_output_profile": "full_index_and_batched_deep_read",
        }

    complex_reasons: list[str] = []
    if line_count > 3000:
        complex_reasons.append("source length exceeds normal-program comfort threshold")
    if routine_count > 10:
        complex_reasons.append("routine count exceeds normal-program comfort threshold")
    if external_count > 8:
        complex_reasons.append("external call count exceeds normal-program comfort threshold")
    if object_count > 10:
        complex_reasons.append("object dependency count exceeds normal-program comfort threshold")
    if file_operation_count > 20:
        complex_reasons.append("file I/O operation count is dense")
    if field_mutation_count > 20:
        complex_reasons.append("field mutation count is dense")
    if sql_statement_count > 10:
        complex_reasons.append("embedded SQL statement count is dense")
    if unique_message_count > 10:
        complex_reasons.append("message/status inventory is dense")
    if recommended_deep_read_count > 5:
        complex_reasons.append("recommended deep-read windows exceed one five-routine batch")

    if complex_reasons:
        return {
            "tier": "complex_normal_program",
            "reason": "; ".join(complex_reasons),
            "default_output_profile": "light_review_plus_triggered_sidecars",
        }

    return {
        "tier": "normal_program",
        "reason": "normal-size program; default to lightweight SME review",
        "default_output_profile": "lightweight_program_review",
    }


def optional_sidecar_triggers(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    counts = index["counts"]
    analysis_tier = index["program_size_tier"]
    full = analysis_tier == "large_extreme_program"
    complex_normal = analysis_tier == "complex_normal_program"
    return {
        "deep_read_plan": {
            "write": full or complex_normal or counts["recommended_deep_read_windows"] > 5,
            "reason": (
                "large/complex tier or more than one five-routine batch"
                if full or complex_normal or counts["recommended_deep_read_windows"] > 5
                else "not needed for lightweight normal review"
            ),
        },
        "coverage_ledger": {
            "write": full or complex_normal or counts["recommended_deep_read_windows"] > 5,
            "reason": (
                "large/complex tier or batched routine coverage required"
                if full or complex_normal or counts["recommended_deep_read_windows"] > 5
                else "not needed for lightweight normal review"
            ),
        },
        "file_io_inventory": {
            "write": full or counts["file_operations"] > 10 or any(
                operation["operation"] in {"WRITE", "UPDATE", "DELETE", "COMMIT", "ROLLBACK"}
                for operation in index["file_operations"]
            ),
            "reason": (
                "dense or state-changing file I/O observed"
                if counts["file_operations"] > 10
                or any(
                    operation["operation"] in {"WRITE", "UPDATE", "DELETE", "COMMIT", "ROLLBACK"}
                    for operation in index["file_operations"]
                )
                else "file I/O can remain summarized in program-analysis.md"
            ),
        },
        "field_mutation_matrix": {
            "write": full or counts["field_mutations"] > 0,
            "reason": (
                "persisted native or SQL mutation evidence observed"
                if counts["field_mutations"] > 0
                else "no persisted mutation detail observed"
            ),
        },
        "sql_inventory": {
            "write": full or counts["sql_statements"] > 0,
            "reason": (
                "embedded SQL / SQLRPGLE evidence observed"
                if counts["sql_statements"] > 0
                else "no embedded SQL observed"
            ),
        },
        "message_inventory_markdown": {
            "write": full or counts["unique_messages"] > 10,
            "reason": (
                "message inventory is dense"
                if counts["unique_messages"] > 10
                else "message-inventory.yaml is enough for lightweight review"
            ),
        },
    }


def analyze_source(lines: list[str], program_name: str, source_path: Path | None = None) -> dict[str, Any]:
    statements = build_statements(lines)
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
    assignments: list[dict[str, Any]] = []
    declarations: list[dict[str, Any]] = []
    assignment_buffer: list[dict[str, Any]] = []
    line_to_routine: dict[int, str] = {}
    recent_read_by_routine: dict[str, int] = {}
    read_branch_routines: set[str] = set()
    screen_boundary_routines: set[str] = set()
    error_routines: set[str] = set()
    outcome_assignment_routines: set[str] = set()

    active_name = "MAIN"
    active_start = 1
    active_type = "mainline"
    first_routine_line: int | None = None

    for line_number, raw_line in enumerate(lines, start=1):
        line = normalized(raw_line)
        if not line:
            continue
        line_to_routine[line_number] = active_name

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

        if active_name != "MAIN" and ends_routine(line, active_name):
            routines[active_name]["end_line"] = line_number
            active_name = "MAIN"
        elif "END-PROC" in line and active_name != "MAIN":
            routines[active_name]["end_line"] = line_number
            active_name = "MAIN"

        if is_fixed_c_comment(line):
            continue

        declaration = declaration_from_line(line, line_number)
        if declaration:
            declarations.append(declaration)

        dcl_file = DCL_F_RE.search(line)
        fixed_file = fixed_file_name_from_line(line)
        if dcl_file or fixed_file:
            file_name = dcl_file.group(1).upper() if dcl_file else fixed_file
            declared_files[file_name] = {
                "name": file_name,
                "declared_at": line_number,
                "source": "DCL-F" if dcl_file else "F-spec",
            }

        if ASSIGNMENT_RE.search(line):
            assignment = {
                "line": line_number,
                "routine": active_name,
                "target": "pending deep read",
                "expression": "legacy opcode assignment",
                "assignment_type": "fixed_or_opcode_assignment",
                "text": strip_sequence(raw_line).strip(),
                "evidence": f"source line {line_number}",
            }
            assignments.append(assignment)
            assignment_buffer.append({"line": line_number, "text": strip_sequence(raw_line).strip()})
            assignment_buffer = assignment_buffer[-12:]
            if OUTCOME_CARRIER_RE.search(line):
                outcome_assignment_routines.add(active_name)

        free_assignment_item = free_assignment(line, line_number, raw_line, active_name)
        if free_assignment_item:
            assignments.append(free_assignment_item)
            assignment_buffer.append(
                {
                    "line": line_number,
                    "text": strip_sequence(raw_line).strip(),
                    "target": free_assignment_item["target"],
                }
            )
            assignment_buffer = assignment_buffer[-12:]
            if OUTCOME_CARRIER_RE.search(free_assignment_item["target"]) or OUTCOME_CARRIER_RE.search(line):
                outcome_assignment_routines.add(active_name)

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

        if is_free_proc_call(line):
            proc_call = FREE_PROC_CALL_RE.match(line)
            if proc_call:
                calls.append(
                    {
                        "caller": active_name,
                        "target": proc_call.group(1).upper(),
                        "call_type": "procedure_call",
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
            if operation in DATA_READ_OPS:
                recent_read_by_routine[active_name] = line_number
            if operation == "EXFMT":
                screen_boundary_routines.add(active_name)

        recent_read_line = recent_read_by_routine.get(active_name)
        if (
            recent_read_line is not None
            and line_number - recent_read_line <= 8
            and BRANCH_AFTER_IO_RE.search(line)
        ):
            read_branch_routines.add(active_name)

        for message_match in MESSAGE_RE.finditer(line):
            messages.append(
                {
                    "routine": active_name,
                    "code": message_match.group(0).upper(),
                    "line": line_number,
                    "source_text": strip_sequence(raw_line).strip(),
                    "evidence": f"source line {line_number}",
                }
            )

        for status_match in SQL_STATUS_RE.finditer(line):
            messages.append(
                {
                    "routine": active_name,
                    "code": status_match.group(1).upper(),
                    "line": line_number,
                    "source_text": strip_sequence(raw_line).strip(),
                    "evidence": f"source line {line_number}",
                }
            )

        if ERROR_RE.search(line):
            routines[active_name]["error_handling"] = "message/error path observed"
            error_routines.add(active_name)

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
    entry_dispatch_routines = {
        call["target"]
        for call in calls
        if call["caller"] == "MAIN" and call["target"] in routine_names and call["target"] != "MAIN"
    }
    mutation_routines = {
        operation["routine"]
        for operation in file_operations
        if operation["operation"] in MUTATION_OPS or operation["operation"] in TRANSACTION_OPS
    }

    for routine in routines.values():
        if routine["name"] == "MAIN":
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("entry path")
        if routine["name"] in entry_dispatch_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("mainline dispatch target")
        if routine["name"] in mutation_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("state-changing file operation")
        if routine["name"] in read_branch_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("read-conditioned branch")
        if routine["name"] in screen_boundary_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("screen/report boundary")
        if routine["name"] in external_call_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("external call boundary")
        if routine["name"] in message_routines or routine["name"] in error_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("message/status handling")
            routine["error_handling"] = "message/error path observed"
        if routine["name"] in outcome_assignment_routines:
            routine["recommended_deep_read"] = True
            routine["deep_read_reasons"].append("outcome/status carrier assignment")
        if not routine["called_by"] and routine["name"] != "MAIN":
            routine["called_by"] = ["not observed in source index"]

    object_names = {
        item["name"] for item in declared_files.values()
    } | {op["object"] for op in file_operations if op["object"] != "unresolved"}
    sql_inventory = build_sql_inventory(statements, program_name, line_to_routine)
    sql_routines = {detail["routine"] for detail in sql_inventory["details"]}
    for routine_name in sql_routines:
        if routine_name in routines:
            routines[routine_name]["recommended_deep_read"] = True
            add_unique(routines[routine_name]["deep_read_reasons"], "sql data access")
            if any(detail["statement_type"] in SQL_DML_OPS for detail in sql_inventory["details"] if detail["routine"] == routine_name):
                routines[routine_name]["state_impact"] = "updates"
    file_io_inventory = build_file_io_inventory(file_operations, program_name)
    field_mutation_inventory = build_field_mutation_inventory(file_operations, sql_inventory, program_name)
    program_profile = detect_program_profile(lines, source_path, statements, declarations)
    message_inventory = build_message_inventory(messages, program_name)
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
    mode, reason = analysis_mode(
        len(lines),
        len(routines),
        len(external_calls),
        len(object_names),
    )
    size_tier = program_size_tier(
        line_count=len(lines),
        routine_count=len(routines),
        external_count=len(external_calls),
        object_count=len(object_names),
        file_operation_count=len(file_operations),
        field_mutation_count=len(field_mutation_inventory["details"]),
        sql_statement_count=len(sql_inventory["details"]),
        unique_message_count=len(message_inventory["summary"]),
        recommended_deep_read_count=len(deep_read_windows),
    )

    source_index = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": program_name.upper(),
        "source": {
            "path": str(source_path) if source_path else "stdin",
            "line_count": len(lines),
        },
        "analysis_mode": mode,
        "mode_reason": reason,
        "program_size_tier": size_tier["tier"],
        "tier_reason": size_tier["reason"],
        "default_output_profile": size_tier["default_output_profile"],
        "counts": {
            "routines": len(routines),
            "external_calls": len(external_calls),
            "object_dependencies": len(object_names),
            "file_operations": len(file_operations),
            "file_io_objects": len(file_io_inventory["summary"]),
            "field_mutations": len(field_mutation_inventory["details"]),
            "sql_statements": len(sql_inventory["details"]),
            "free_format_assignments": len(
                [assignment for assignment in assignments if assignment["assignment_type"] == "free_format_assignment"]
            ),
            "messages": len(messages),
            "unique_messages": len(message_inventory["summary"]),
            "recommended_deep_read_windows": len(deep_read_windows),
        },
        "program_profile": program_profile,
        "statements": statements,
        "declarations": declarations,
        "assignments": assignments,
        "declared_files": list(declared_files.values()),
        "routines": list(routines.values()),
        "calls": calls,
        "external_calls": external_calls,
        "file_operations": file_operations,
        "file_io_inventory": file_io_inventory,
        "field_mutation_inventory": field_mutation_inventory,
        "sql_inventory": sql_inventory,
        "messages": messages,
        "message_inventory": message_inventory,
        "deep_read_windows": deep_read_windows,
        "contract_note": (
            "This structure index is pre-analysis evidence. It is not a "
            "business summary and does not make downstream-ready claims."
        ),
    }
    source_index["optional_sidecar_triggers"] = optional_sidecar_triggers(source_index)
    source_index["routine_logic_inventory"] = build_routine_logic_inventory(source_index)
    return source_index


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


def render_message_inventory(index: dict[str, Any]) -> str:
    summary_rows = [
        [
            item["message"],
            item["short_description"],
            item["description_source"],
            item["occurrence_count"],
            item["routines"],
            item["first_seen"],
            item["detail_ref"],
            item["evidence_status"],
        ]
        for item in index["message_inventory"]["summary"]
    ]
    if not summary_rows:
        summary_rows = [["-", "no message/status tokens observed by static index", "-", 0, "-", "-", "-", "-"]]

    sections = [
        f"# Message Inventory: {index['program']}",
        "This sidecar keeps detailed observed message/status evidence out of the "
        "front-loaded `program-analysis.md` summary. Descriptions remain unresolved "
        "until matched to an approved reference pack, runtime evidence, source "
        "comment, or SME confirmation.",
        "## Summary",
        markdown_table(
            [
                "Message / Code / Literal",
                "Short Description",
                "Description Source",
                "Occurrences",
                "Routines",
                "First Seen",
                "Detail ID",
                "Evidence Status",
            ],
            summary_rows,
        ),
    ]

    for detail in index["message_inventory"]["details"]:
        occurrence_rows = [
            [
                occurrence["routine"],
                occurrence["line"],
                occurrence.get("source_text", ""),
                occurrence["evidence"],
            ]
            for occurrence in detail["occurrences"]
        ]
        sections.extend(
            [
                f"## {detail['detail_id']} - {detail['message']}",
                markdown_table(
                    ["Field", "Value"],
                    [
                        ["Short Description", detail["short_description"]],
                        ["Description Source", detail["description_source"]],
                        ["Emitted / Set By", detail["emitted_or_set_by"]],
                        ["Trigger / Handler", detail["trigger_or_handler"]],
                        ["Carrier / Destination", detail["carrier_or_destination"]],
                        ["Related Validation / Exception", detail["related_validation_or_exception"]],
                        ["Evidence Status", detail["evidence_status"]],
                    ],
                ),
                "### Occurrences",
                markdown_table(["Routine", "Line", "Source Text", "Evidence"], occurrence_rows),
            ]
        )

    return "\n\n".join(sections) + "\n"


def render_message_inventory_yaml(index: dict[str, Any]) -> str:
    payload = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": index["program"],
        "source": index["source"],
        "message_inventory": index["message_inventory"],
        "contract_note": (
            "Descriptions are unresolved until populated from approved reference "
            "packs, runtime evidence, source comments, or SME confirmation."
        ),
    }
    return to_yaml(payload) + "\n"


def render_file_io_inventory(index: dict[str, Any]) -> str:
    summary_rows = [
        [
            item["object"],
            item["operations"],
            item["routines"],
            item["occurrence_count"],
            item["state_impact_summary"],
            item["detail_refs"],
        ]
        for item in index["file_io_inventory"]["summary"]
    ]
    if not summary_rows:
        summary_rows = [["-", "no file I/O observed by static index", "-", 0, "-", "-"]]

    detail_rows = [
        [
            detail["detail_id"],
            detail["routine"],
            detail["operation"],
            detail["object"],
            detail["line"],
            detail["state_impact"],
            detail["recent_assignments"],
            detail["evidence"],
        ]
        for detail in index["file_io_inventory"]["details"]
    ]
    if not detail_rows:
        detail_rows = [["-", "-", "-", "-", "-", "-", "-", "-"]]

    return "\n\n".join(
        [
            f"# File I/O Inventory: {index['program']}",
            "This sidecar keeps dense file operation evidence out of the "
            "front-loaded `program-analysis.md` summary while preserving every "
            "observed read, write, update, delete, screen, and transaction boundary.",
            "## Summary",
            markdown_table(
                ["Object", "Operations", "Routines", "Occurrences", "State Impact", "Detail IDs"],
                summary_rows,
            ),
            "## Details",
            markdown_table(
                [
                    "Detail ID",
                    "Routine",
                    "Operation",
                    "Object",
                    "Line",
                    "State Impact",
                    "Recent Assignments",
                    "Evidence",
                ],
                detail_rows,
            ),
        ]
    ) + "\n"


def render_file_io_inventory_yaml(index: dict[str, Any]) -> str:
    payload = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": index["program"],
        "source": index["source"],
        "file_io_inventory": index["file_io_inventory"],
        "contract_note": (
            "Observed file I/O is inventory evidence only. Business meaning, "
            "record format semantics, and DDS joins require deep read or SME confirmation."
        ),
    }
    return to_yaml(payload) + "\n"


def render_field_mutation_inventory(index: dict[str, Any]) -> str:
    summary_rows = [
        [
            item["object"],
            item["operation"],
            item["occurrence_count"],
            item["routines"],
            item["detail_refs"],
        ]
        for item in index["field_mutation_inventory"]["summary"]
    ]
    if not summary_rows:
        summary_rows = [["-", "no persistent mutation observed by static index", 0, "-", "-"]]

    detail_rows = [
        [
            detail["detail_id"],
            detail["mutation_source"],
            detail["routine"],
            detail["operation"],
            detail["object"],
            detail["source_lines"],
            detail["recent_assignments"],
            detail["host_variables"],
            detail["commit_or_rollback"],
            detail["evidence"],
        ]
        for detail in index["field_mutation_inventory"]["details"]
    ]
    if not detail_rows:
        detail_rows = [["-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]]

    return "\n\n".join(
        [
            f"# Field Mutation Matrix: {index['program']}",
            "This sidecar seeds mutation review for native RPG file operations "
            "and embedded SQL DML. Field-level calculations remain pending until "
            "routine deep read cites source ranges.",
            "## Summary",
            markdown_table(
                ["Object", "Operation", "Occurrences", "Routines", "Detail IDs"],
                summary_rows,
            ),
            "## Details",
            markdown_table(
                [
                    "Detail ID",
                    "Source",
                    "Routine",
                    "Operation",
                    "Object",
                    "Source Lines",
                    "Recent Assignments",
                    "Host Variables",
                    "Commit / Rollback",
                    "Evidence",
                ],
                detail_rows,
            ),
        ]
    ) + "\n"


def render_field_mutation_inventory_yaml(index: dict[str, Any]) -> str:
    payload = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": index["program"],
        "source": index["source"],
        "field_mutation_inventory": index["field_mutation_inventory"],
        "contract_note": (
            "This matrix identifies mutation locations. Approved calculation "
            "logic still belongs in `program-analysis.md` after semantic deep read."
        ),
    }
    return to_yaml(payload) + "\n"


def render_sql_inventory(index: dict[str, Any]) -> str:
    summary_rows = [
        [
            item["statement_type"],
            item["table_or_view"],
            item["occurrence_count"],
            item["routines"],
            item["host_variables"],
            item["detail_refs"],
        ]
        for item in index["sql_inventory"]["summary"]
    ]
    if not summary_rows:
        summary_rows = [["-", "no embedded SQL observed by static index", 0, "-", "-", "-"]]

    detail_rows = [
        [
            detail["detail_id"],
            detail["routine"],
            detail["statement_type"],
            detail["table_or_view"],
            detail["source_lines"],
            detail["host_variables"],
            detail["state_impact"],
            detail["status_handling"],
            detail["evidence"],
        ]
        for detail in index["sql_inventory"]["details"]
    ]
    if not detail_rows:
        detail_rows = [["-", "-", "-", "-", "-", "-", "-", "-", "-"]]

    return "\n\n".join(
        [
            f"# SQL Inventory: {index['program']}",
            "This sidecar keeps embedded SQL statements and host-variable evidence "
            "separate from SME-facing logic sections. SQL behavior is not approved "
            "until tied back to calculation, validation, exception, or message logic.",
            "## Summary",
            markdown_table(
                ["Type", "Table / View", "Occurrences", "Routines", "Host Variables", "Detail IDs"],
                summary_rows,
            ),
            "## Details",
            markdown_table(
                [
                    "Detail ID",
                    "Routine",
                    "Type",
                    "Table / View",
                    "Source Lines",
                    "Host Variables",
                    "State Impact",
                    "Status Handling",
                    "Evidence",
                ],
                detail_rows,
            ),
        ]
    ) + "\n"


def render_sql_inventory_yaml(index: dict[str, Any]) -> str:
    payload = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": index["program"],
        "source": index["source"],
        "sql_inventory": index["sql_inventory"],
        "contract_note": (
            "Embedded SQL inventory is source evidence. Approved data behavior "
            "requires source-range citation, runtime evidence, or SME confirmation."
        ),
    }
    return to_yaml(payload) + "\n"


def render_routine_logic_details(index: dict[str, Any]) -> str:
    summary_rows = [
        [
            item["routine"],
            item["role"],
            item["source_lines"],
            item["coverage"],
            "yes" if item["deep_read_recommended"] else "no",
            item["state_impact"],
            item["detail_ref"],
            item["semantic_status"],
        ]
        for item in index["routine_logic_inventory"]["summary"]
    ]
    if not summary_rows:
        summary_rows = [["-", "no routines observed by static index", "-", "-", "-", "-", "-", "-"]]

    sections = [
        f"# Routine Logic Details: {index['program']}",
        "This sidecar keeps per-routine logic detail out of the front-loaded "
        "`program-analysis.md` summary. The static index seeds routine IDs, "
        "line ranges, call/data evidence, and deep-read priorities; semantic "
        "logic remains `pending_deep_read` until source windows are analyzed.",
        "## Summary",
        markdown_table(
            [
                "Routine",
                "Role",
                "Source Lines",
                "Coverage",
                "Deep Read",
                "State Impact",
                "Detail ID",
                "Semantic Status",
            ],
            summary_rows,
        ),
        "## Sharding Guidance",
        "- If routines <= 25, the main `program-analysis.md` may include full Routine Logic Details.",
        "- If routines > 25, keep `program-analysis.md` as a summary and use this sidecar for details.",
        "- If routines > 80 or source lines > 10,000, split semantic details into `routine-logic-details/part-*.md` working files.",
        "- Each `routine-logic-details/part-*.md` file must start with batch-scoped `## Calculation Logic`, `## Validation Logic`, `## Exception Handling`, and `## Message Inventory` before per-routine detail.",
        "- In part files, `## Message Inventory` must list every exact message/status/literal observed in that batch as its own row.",
        "- After batch deep-read, merge all part files into this final consolidated `routine-logic-details.md` SME review document with all routine detail.",
    ]

    for detail in index["routine_logic_inventory"]["details"]:
        sections.extend(
            [
                f"## {detail['detail_id']} - {detail['routine']}",
                markdown_table(
                    ["Field", "Value"],
                    [
                        ["Role", detail["role"]],
                        ["Source Lines", detail["source_lines"]],
                        ["Called By", detail["called_by"]],
                        ["Calls Out", detail["calls_out"]],
                        ["Data Touches", detail["data_touches"]],
                        ["State Impact", detail["state_impact"]],
                        ["Error Handling", detail["error_handling"]],
                        ["Coverage", detail["coverage"]],
                        ["Deep Read Recommended", "yes" if detail["deep_read_recommended"] else "no"],
                        ["Deep Read Reasons", detail["deep_read_reasons"]],
                        ["Semantic Status", detail["semantic_status"]],
                    ],
                ),
                "### Pending Semantic Detail",
                "- Execution trigger: pending deep read.",
                "- Step-by-step logic: pending deep read.",
                "- Field calculations and assignments: pending deep read.",
                "- Conditioned calculation blocks: pending deep read.",
                "- Outcome reverse traces: pending deep read.",
                "- Routine field lineage / carriers: pending deep read.",
                "- Branch outcomes: pending deep read.",
                "- Routine exception closure: pending deep read.",
            ]
        )

    return "\n\n".join(sections) + "\n"


def render_routine_logic_details_yaml(index: dict[str, Any]) -> str:
    payload = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": index["program"],
        "source": index["source"],
        "routine_logic_inventory": index["routine_logic_inventory"],
        "contract_note": (
            "This is a pre-analysis routine detail seed. Detailed routine logic "
            "must be populated only after semantic deep read cites source ranges."
        ),
    }
    return to_yaml(payload) + "\n"


def render_program_analysis_summary_yaml(index: dict[str, Any]) -> str:
    payload = {
        "schema_version": "0.1",
        "generated_by": "index_rpg_source.py",
        "program": index["program"],
        "source": index["source"],
        "analysis_mode": index["analysis_mode"],
        "mode_reason": index["mode_reason"],
        "program_size_tier": index["program_size_tier"],
        "tier_reason": index["tier_reason"],
        "default_output_profile": index["default_output_profile"],
        "counts": index["counts"],
        "program_profile": index["program_profile"],
        "routine_summary": index["routine_logic_inventory"]["summary"],
        "message_summary": index["message_inventory"]["summary"],
        "file_io_summary": index["file_io_inventory"]["summary"],
        "field_mutation_summary": index["field_mutation_inventory"]["summary"],
        "sql_summary": index["sql_inventory"]["summary"],
        "external_calls": index["external_calls"],
        "declared_files": index["declared_files"],
        "deep_read_windows": index["deep_read_windows"],
        "optional_sidecar_triggers": index["optional_sidecar_triggers"],
        "sidecars": {
            "source_index": {"path": "source-index.yaml", "status": "present"},
            "routine_index": {"path": "routine-index.md", "status": "present"},
            "routine_logic_details": {"path": "routine-logic-details.md", "status": "present"},
            "routine_logic_details_yaml": {"path": "routine-logic-details.yaml", "status": "present"},
            "message_inventory_yaml": {"path": "message-inventory.yaml", "status": "present"},
            "message_inventory": {
                "path": "message-inventory.md",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["message_inventory_markdown"]["write"]
                    else "not_written_by_default"
                ),
            },
            "coverage_ledger": {
                "path": "all-routine-coverage-ledger.md",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["coverage_ledger"]["write"]
                    else "not_written_by_default"
                ),
            },
            "deep_read_plan": {
                "path": "deep-read-plan.md",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["deep_read_plan"]["write"]
                    else "not_written_by_default"
                ),
            },
            "file_io_inventory": {
                "path": "file-io-inventory.md",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["file_io_inventory"]["write"]
                    else "not_written_by_default"
                ),
            },
            "file_io_inventory_yaml": {
                "path": "file-io-inventory.yaml",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["file_io_inventory"]["write"]
                    else "not_written_by_default"
                ),
            },
            "field_mutation_matrix": {
                "path": "field-mutation-matrix.md",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["field_mutation_matrix"]["write"]
                    else "not_written_by_default"
                ),
            },
            "field_mutation_matrix_yaml": {
                "path": "field-mutation-matrix.yaml",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["field_mutation_matrix"]["write"]
                    else "not_written_by_default"
                ),
            },
            "sql_inventory": {
                "path": "sql-inventory.md",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["sql_inventory"]["write"]
                    else "not_written_by_default"
                ),
            },
            "sql_inventory_yaml": {
                "path": "sql-inventory.yaml",
                "status": (
                    "optional_triggered"
                    if index["optional_sidecar_triggers"]["sql_inventory"]["write"]
                    else "not_written_by_default"
                ),
            },
        },
        "contract_note": (
            "Flow-level analysis should prefer this compact summary and present "
            "sidecar YAML files instead of concatenating large program-analysis "
            "Markdown. Optional sidecars can be generated on demand when their "
            "trigger is true or downstream evidence needs them."
        ),
    }
    return to_yaml(payload) + "\n"


def write_artifacts(index: dict[str, Any], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [
        (out_dir / "source-index.yaml", to_yaml(index) + "\n"),
        (out_dir / "program-analysis-summary.yaml", render_program_analysis_summary_yaml(index)),
        (out_dir / "routine-index.md", render_routine_index(index)),
        (out_dir / "routine-logic-details.md", render_routine_logic_details(index)),
        (out_dir / "routine-logic-details.yaml", render_routine_logic_details_yaml(index)),
        (out_dir / "message-inventory.yaml", render_message_inventory_yaml(index)),
    ]
    triggers = index["optional_sidecar_triggers"]
    if triggers["coverage_ledger"]["write"]:
        files.append((out_dir / "all-routine-coverage-ledger.md", render_coverage_ledger(index)))
    if triggers["deep_read_plan"]["write"]:
        files.append((out_dir / "deep-read-plan.md", render_deep_read_plan(index)))
    if triggers["message_inventory_markdown"]["write"]:
        files.append((out_dir / "message-inventory.md", render_message_inventory(index)))
    if triggers["file_io_inventory"]["write"]:
        files.extend(
            [
                (out_dir / "file-io-inventory.md", render_file_io_inventory(index)),
                (out_dir / "file-io-inventory.yaml", render_file_io_inventory_yaml(index)),
            ]
        )
    if triggers["field_mutation_matrix"]["write"]:
        files.extend(
            [
                (out_dir / "field-mutation-matrix.md", render_field_mutation_inventory(index)),
                (out_dir / "field-mutation-matrix.yaml", render_field_mutation_inventory_yaml(index)),
            ]
        )
    if triggers["sql_inventory"]["write"]:
        files.extend(
            [
                (out_dir / "sql-inventory.md", render_sql_inventory(index)),
                (out_dir / "sql-inventory.yaml", render_sql_inventory_yaml(index)),
            ]
        )
    written: list[Path] = []
    for path, content in files:
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build source-index artifacts for RPG/RPGLE program analysis."
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
