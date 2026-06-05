#!/usr/bin/env python3
"""Detect local/runtime-specific links that break outside the current IDE.

The checker scans Markdown, HTML, and YAML-like artifacts for active links such
as `file://`, `vscode://`, VSCode webview CDN resources, and absolute local
filesystem paths. It ignores plain guidance text unless it is used as a link
target.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SCAN_EXTENSIONS = {".md", ".html", ".htm", ".yaml", ".yml", ".json"}
DEFAULT_IGNORES = {
    ".git",
    ".DS_Store",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
}

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
HTML_HREF_RE = re.compile(r"""\bhref\s*=\s*["']([^"']+)["']""", re.I)
YAML_URL_RE = re.compile(r"""^\s*[^#\n]+:\s*["']?([^"'\s#]+)["']?\s*(?:#.*)?$""")
JSON_VALUE_RE = re.compile(r'"[^"\n]+"\s*:\s*"([^"\n]+)"')
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
LOCAL_ABSOLUTE_RE = re.compile(r"^/(Users|home|var|tmp|private|Volumes)/")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    kind: str
    target: str


def is_unsafe_link_target(target: str) -> bool:
    value = target.strip().strip("<>")
    lowered = value.lower()
    return (
        lowered.startswith("file:")
        or lowered.startswith("vscode:")
        or lowered.startswith("command:")
        or lowered.startswith("javascript:")
        or "vscode-resource.vscode-cdn.net" in lowered
        or WINDOWS_ABSOLUTE_RE.match(value) is not None
        or LOCAL_ABSOLUTE_RE.match(value) is not None
    )


def iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in SCAN_EXTENSIONS:
                yield path
            continue
        for child in path.rglob("*"):
            if any(part in DEFAULT_IGNORES for part in child.parts):
                continue
            if child.is_file() and child.suffix.lower() in SCAN_EXTENSIONS:
                yield child


def collect_file_findings(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings

    for line_number, line in enumerate(lines, start=1):
        for match in MARKDOWN_LINK_RE.finditer(line):
            target = match.group(1).strip()
            if is_unsafe_link_target(target):
                findings.append(Finding(path, line_number, "markdown-link", target))

        for match in HTML_HREF_RE.finditer(line):
            target = match.group(1).strip()
            if is_unsafe_link_target(target):
                findings.append(Finding(path, line_number, "html-href", target))

        if path.suffix.lower() in {".yaml", ".yml"}:
            match = YAML_URL_RE.match(line)
            if match:
                target = match.group(1).strip()
                if is_unsafe_link_target(target):
                    findings.append(Finding(path, line_number, "yaml-value", target))

        if path.suffix.lower() == ".json":
            for match in JSON_VALUE_RE.finditer(line):
                target = match.group(1).strip()
                if is_unsafe_link_target(target):
                    findings.append(Finding(path, line_number, "json-value", target))

    return findings


def collect_findings(paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(paths):
        findings.extend(collect_file_findings(path))
    return findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Markdown/HTML/YAML artifacts for non-portable local links."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="Files or directories to scan; defaults to current directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    findings = collect_findings(args.paths)
    if not findings:
        print("OK: no unsafe local/runtime-specific links found")
        return 0

    print("Unsafe local/runtime-specific links found:")
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.kind}: {finding.target}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
