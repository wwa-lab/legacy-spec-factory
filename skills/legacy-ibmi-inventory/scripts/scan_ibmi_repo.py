#!/usr/bin/env python3
"""Scan a repository for IBM i source members and rank large programs.

This scanner is intentionally structure-first. It inventories source files,
counts lines, applies simple IBM i source classification, and writes review
artifacts. It does not infer business behavior.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROGRAM_EXTENSIONS = {
    ".RPG": "RPG",
    ".RPGLE": "RPGLE",
    ".SQLRPGLE": "SQLRPGLE",
    ".CL": "CL",
    ".CLLE": "CLLE",
    ".CBL": "COBOL",
    ".CBLE": "COBOL",
    ".COBOL": "COBOL",
}
DDS_EXTENSIONS = {
    ".DDS": "DDS",
    ".PF": "DDS_PF",
    ".LF": "DDS_LF",
    ".DSPF": "DDS_DSPF",
    ".PRTF": "DDS_PRTF",
}
SOURCE_EXTENSIONS = PROGRAM_EXTENSIONS | DDS_EXTENSIONS
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".DS_Store",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}
ANALYZER_PROGRAM_KINDS = {"RPG", "RPGLE", "SQLRPGLE"}
REPO_ROOT = Path(__file__).resolve().parents[3]
PROGRAM_ANALYZER_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "index_rpg_source.py"
)
_PROGRAM_ANALYZER: Any | None = None


@dataclass(frozen=True)
class SourceMember:
    member: str
    object_type: str
    source_kind: str
    path: str
    total_lines: int
    nonblank_lines: int
    comment_lines: int
    code_lines: int
    size_tier: str
    tier_reason: str
    default_output_profile: str
    classification_source: str
    routine_count: int
    external_call_count: int
    object_dependency_count: int
    file_operation_count: int
    sql_statement_count: int
    recommended_deep_read_count: int


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
    safe = all(ch.isalnum() or ch in "_./:@#$%+*-, " for ch in text)
    if safe and text.lower() not in {"true", "false", "null"}:
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


def source_kind_for(path: Path) -> str | None:
    return SOURCE_EXTENSIONS.get(path.suffix.upper())


def object_type_for(source_kind: str) -> str:
    if source_kind in PROGRAM_EXTENSIONS.values():
        return "program"
    return "dds_object"


def load_program_analyzer() -> Any:
    global _PROGRAM_ANALYZER
    if _PROGRAM_ANALYZER is not None:
        return _PROGRAM_ANALYZER
    spec = importlib.util.spec_from_file_location("index_rpg_source", PROGRAM_ANALYZER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load program analyzer: {PROGRAM_ANALYZER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["index_rpg_source"] = module
    spec.loader.exec_module(module)
    _PROGRAM_ANALYZER = module
    return module


def is_rpg_comment(line: str) -> bool:
    text = strip_sequence(line).lstrip()
    upper = text.upper()
    return (
        text.startswith("*")
        or text.startswith("//")
        or upper.startswith("C*")
        or upper.startswith("/*")
        or upper.startswith("*/")
    )


def is_cl_comment(line: str) -> bool:
    return line.lstrip().startswith("/*") or line.lstrip().startswith("//")


def is_cobol_comment(line: str) -> bool:
    return len(line) > 6 and line[6] in {"*", "/"}


def is_dds_comment(line: str) -> bool:
    text = strip_sequence(line).lstrip()
    return text.startswith("*") or text.upper().startswith("A*")


def strip_sequence(line: str) -> str:
    if len(line) > 6 and line[:6].strip().isdigit():
        return line[6:]
    return line


def is_comment_line(line: str, source_kind: str) -> bool:
    if source_kind in {"RPG", "RPGLE", "SQLRPGLE"}:
        return is_rpg_comment(line)
    if source_kind in {"CL", "CLLE"}:
        return is_cl_comment(line)
    if source_kind == "COBOL":
        return is_cobol_comment(line)
    if source_kind.startswith("DDS"):
        return is_dds_comment(line)
    return False


def fallback_program_tier(total_lines: int, large_threshold: int) -> dict[str, Any]:
    if total_lines >= large_threshold:
        return {
            "size_tier": "large_extreme_program",
            "tier_reason": (
                f"total_lines >= configured threshold {large_threshold}; "
                "RPG-specific routine/call/object density unavailable for this source kind"
            ),
            "default_output_profile": "full_index_and_batched_deep_read",
            "classification_source": "repo_scanner_line_count_fallback",
            "counts": {},
        }
    if total_lines >= 3000:
        return {
            "size_tier": "complex_normal_program",
            "tier_reason": (
                "source length exceeds normal-program comfort threshold; "
                "RPG-specific routine/call/object density unavailable for this source kind"
            ),
            "default_output_profile": "light_review_plus_triggered_sidecars",
            "classification_source": "repo_scanner_line_count_fallback",
            "counts": {},
        }
    return {
        "size_tier": "normal_program",
        "tier_reason": "normal-size program; default to lightweight SME review",
        "default_output_profile": "lightweight_program_review",
        "classification_source": "repo_scanner_line_count_fallback",
        "counts": {},
    }


def dds_tier() -> dict[str, Any]:
    return {
        "size_tier": "non_program_source",
        "tier_reason": "DDS/source object is inventoried but not classified by program analyzer tiers",
        "default_output_profile": "inventory_only",
        "classification_source": "repo_scanner_non_program_source",
        "counts": {},
    }


def analyzer_program_tier(lines: list[str], program_name: str, path: Path) -> dict[str, Any]:
    analyzer = load_program_analyzer()
    index = analyzer.analyze_source(lines, program_name=program_name, source_path=path)
    return {
        "size_tier": index["program_size_tier"],
        "tier_reason": index["tier_reason"],
        "default_output_profile": index["default_output_profile"],
        "classification_source": "legacy-ibmi-program-analyzer",
        "counts": index["counts"],
    }


def classify_source(
    lines: list[str],
    source_kind: str,
    program_name: str,
    path: Path,
    large_threshold: int,
) -> dict[str, Any]:
    if source_kind in ANALYZER_PROGRAM_KINDS:
        return analyzer_program_tier(lines, program_name, path)
    if source_kind in PROGRAM_EXTENSIONS.values():
        return fallback_program_tier(len(lines), large_threshold)
    return dds_tier()


def analyze_file(path: Path, root: Path, large_threshold: int) -> SourceMember | None:
    source_kind = source_kind_for(path)
    if source_kind is None:
        return None

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    nonblank = [line for line in lines if line.strip()]
    comments = [line for line in nonblank if is_comment_line(line, source_kind)]
    classification = classify_source(
        lines=lines,
        source_kind=source_kind,
        program_name=path.stem.upper(),
        path=path,
        large_threshold=large_threshold,
    )
    counts = classification["counts"]
    rel_path = path.relative_to(root).as_posix()
    return SourceMember(
        member=path.stem.upper(),
        object_type=object_type_for(source_kind),
        source_kind=source_kind,
        path=rel_path,
        total_lines=len(lines),
        nonblank_lines=len(nonblank),
        comment_lines=len(comments),
        code_lines=max(0, len(nonblank) - len(comments)),
        size_tier=classification["size_tier"],
        tier_reason=classification["tier_reason"],
        default_output_profile=classification["default_output_profile"],
        classification_source=classification["classification_source"],
        routine_count=counts.get("routines", 0),
        external_call_count=counts.get("external_calls", 0),
        object_dependency_count=counts.get("object_dependencies", 0),
        file_operation_count=counts.get("file_operations", 0),
        sql_statement_count=counts.get("sql_statements", 0),
        recommended_deep_read_count=counts.get("recommended_deep_read_windows", 0),
    )


def should_skip_dir(path: Path, root: Path, exclude_dirs: set[str]) -> bool:
    if path == root:
        return False
    return any(part in exclude_dirs for part in path.relative_to(root).parts)


def discover_sources(root: Path, exclude_dirs: set[str]) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if should_skip_dir(path.parent, root, exclude_dirs):
            continue
        if source_kind_for(path):
            paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(root).as_posix().lower())


def scan_repository(root: Path, large_threshold: int, exclude_dirs: set[str]) -> list[SourceMember]:
    return [
        member
        for path in discover_sources(root, exclude_dirs)
        if (member := analyze_file(path, root, large_threshold)) is not None
    ]


def member_to_row(member: SourceMember) -> dict[str, Any]:
    return {
        "member": member.member,
        "object_type": member.object_type,
        "source_kind": member.source_kind,
        "path": member.path,
        "total_lines": member.total_lines,
        "nonblank_lines": member.nonblank_lines,
        "comment_lines": member.comment_lines,
        "code_lines": member.code_lines,
        "size_tier": member.size_tier,
        "tier_reason": member.tier_reason,
        "default_output_profile": member.default_output_profile,
        "classification_source": member.classification_source,
        "routine_count": member.routine_count,
        "external_call_count": member.external_call_count,
        "object_dependency_count": member.object_dependency_count,
        "file_operation_count": member.file_operation_count,
        "sql_statement_count": member.sql_statement_count,
        "recommended_deep_read_count": member.recommended_deep_read_count,
    }


def write_csv(members: list[SourceMember], path: Path) -> None:
    fieldnames = [
        "member",
        "object_type",
        "source_kind",
        "path",
        "total_lines",
        "nonblank_lines",
        "comment_lines",
        "code_lines",
        "size_tier",
        "tier_reason",
        "default_output_profile",
        "classification_source",
        "routine_count",
        "external_call_count",
        "object_dependency_count",
        "file_operation_count",
        "sql_statement_count",
        "recommended_deep_read_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for member in sorted(members, key=lambda item: (-item.total_lines, item.member, item.path)):
            writer.writerow(member_to_row(member))


def table_cell(value: Any) -> str:
    text = str(value) if value not in (None, "") else "-"
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(table_cell(value) for value in row) + " |")
    return "\n".join(output)


def render_large_candidates(members: list[SourceMember], large_threshold: int) -> str:
    programs = [member for member in members if member.object_type == "program"]
    large = [member for member in programs if member.size_tier == "large_extreme_program"]
    complex_normal = [
        member
        for member in programs
        if member.size_tier == "complex_normal_program"
    ]
    normal = [
        member
        for member in programs
        if member.size_tier == "normal_program"
    ]

    large_rows = [
        [
            member.member,
            member.source_kind,
            member.total_lines,
            member.code_lines,
            member.routine_count,
            member.external_call_count,
            member.object_dependency_count,
            member.path,
            member.tier_reason,
        ]
        for member in sorted(large, key=lambda item: (-item.total_lines, item.member))
    ]
    if not large_rows:
        large_rows = [["-", "-", 0, 0, 0, 0, 0, "-", "no large_extreme_program entries found"]]

    complex_rows = [
        [
            member.member,
            member.source_kind,
            member.total_lines,
            member.code_lines,
            member.routine_count,
            member.external_call_count,
            member.object_dependency_count,
            member.path,
            member.tier_reason,
        ]
        for member in sorted(complex_normal, key=lambda item: (-item.total_lines, item.member))[:50]
    ]
    if not complex_rows:
        complex_rows = [["-", "-", 0, 0, 0, 0, 0, "-", "no complex_normal_program entries found"]]

    normal_rows = [
        [
            member.member,
            member.source_kind,
            member.total_lines,
            member.code_lines,
            member.path,
            member.tier_reason,
        ]
        for member in sorted(normal, key=lambda item: (-item.total_lines, item.member))[:50]
    ]
    if not normal_rows:
        normal_rows = [["-", "-", 0, 0, "-", "no normal_program entries found"]]

    return "\n\n".join(
        [
            "# Program Tier Report",
            "This report uses the same three program tiers as `legacy-ibmi-program-analyzer`: "
            "`normal_program`, `complex_normal_program`, and `large_extreme_program`. "
            "For RPG/RPGLE/SQLRPGLE, classification comes from the program analyzer. "
            "For CL/COBOL, scanner line-count fallback is used until a language-specific analyzer exists.",
            "## Summary",
            markdown_table(
                ["Metric", "Value"],
                [
                    ["Program source members", len(programs)],
                    ["Configured fallback large threshold", large_threshold],
                    ["large_extreme_program", len(large)],
                    ["complex_normal_program", len(complex_normal)],
                    ["normal_program", len(normal)],
                ],
            ),
            "## large_extreme_program",
            markdown_table(
                [
                    "Member",
                    "Kind",
                    "Total Lines",
                    "Code Lines",
                    "Routines",
                    "External Calls",
                    "Objects",
                    "Path",
                    "Reason",
                ],
                large_rows,
            ),
            "## complex_normal_program",
            markdown_table(
                [
                    "Member",
                    "Kind",
                    "Total Lines",
                    "Code Lines",
                    "Routines",
                    "External Calls",
                    "Objects",
                    "Path",
                    "Reason",
                ],
                complex_rows,
            ),
            "## normal_program",
            markdown_table(
                ["Member", "Kind", "Total Lines", "Code Lines", "Path", "Reason"],
                normal_rows,
            ),
            "## Recommended Next Step",
            "\n".join(
                [
                    "- Run full `legacy-ibmi-program-analyzer` artifacts for `large_extreme_program` entries first.",
                    "- Review `complex_normal_program` entries for dependency centrality and SME criticality.",
                    "- Add call graph, file dependency count, and SME criticality before final prioritization.",
                    "- Use normal-program flow packages for SME review after the large-program pilot is stable.",
                ]
            ),
        ]
    ) + "\n"


def build_summary(root: Path, members: list[SourceMember], large_threshold: int) -> dict[str, Any]:
    programs = [member for member in members if member.object_type == "program"]
    dds_objects = [member for member in members if member.object_type == "dds_object"]
    large_programs = [member for member in programs if member.size_tier == "large_extreme_program"]
    complex_programs = [member for member in programs if member.size_tier == "complex_normal_program"]
    normal_programs = [member for member in programs if member.size_tier == "normal_program"]
    by_kind: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    for member in members:
        by_kind[member.source_kind] = by_kind.get(member.source_kind, 0) + 1
        by_tier[member.size_tier] = by_tier.get(member.size_tier, 0) + 1
    return {
        "schema_version": "0.1",
        "generated_by": "scan_ibmi_repo.py",
        "root": str(root),
        "fallback_large_threshold": large_threshold,
        "counts": {
            "source_members": len(members),
            "programs": len(programs),
            "dds_objects": len(dds_objects),
            "large_extreme_program": len(large_programs),
            "complex_normal_program": len(complex_programs),
            "normal_program": len(normal_programs),
        },
        "by_source_kind": dict(sorted(by_kind.items())),
        "by_size_tier": dict(sorted(by_tier.items())),
        "largest_programs": [
            member_to_row(member)
            for member in sorted(programs, key=lambda item: (-item.total_lines, item.member))[:20]
        ],
        "contract_note": (
            "RPG/RPGLE/SQLRPGLE tiering reuses legacy-ibmi-program-analyzer. "
            "Business behavior, dependency centrality, and SME criticality still require downstream analysis."
        ),
    }


def write_outputs(members: list[SourceMember], root: Path, out_dir: Path, large_threshold: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    program_list = out_dir / "program-list.csv"
    large_candidates = out_dir / "large-program-candidates.md"
    scan_summary = out_dir / "scan-summary.yaml"
    write_csv(members, program_list)
    large_candidates.write_text(render_large_candidates(members, large_threshold), encoding="utf-8")
    scan_summary.write_text(to_yaml(build_summary(root, members, large_threshold)) + "\n", encoding="utf-8")
    return [program_list, large_candidates, scan_summary]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a repository for IBM i source members and large-program candidates."
    )
    parser.add_argument("root", type=Path, help="Repository or source-export root to scan")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("outputs") / "repo-scan",
        help="Directory for generated scanner artifacts",
    )
    parser.add_argument(
        "--large-threshold",
        type=int,
        default=10000,
        help="Total-line threshold for large program candidates",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude; can be provided multiple times",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    if not root.exists() or not root.is_dir():
        print(f"Scan root not found or not a directory: {root}", file=sys.stderr)
        return 2
    if args.large_threshold <= 0:
        print("--large-threshold must be a positive integer", file=sys.stderr)
        return 2

    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir)
    members = scan_repository(root, args.large_threshold, exclude_dirs)
    written = write_outputs(members, root, args.out_dir, args.large_threshold)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
