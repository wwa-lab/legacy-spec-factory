#!/usr/bin/env python3
"""Build a program-set review and prepare a queue for missing programs.

This is the one-step intake command for SME-provided program lists. It creates
the deterministic core manifest first, then creates the targeted
missing-program queue when required artifacts are absent. It does not scan
source code itself.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BUILDER = SCRIPT_DIR / "program_set_core_review.py"
QUEUE = SCRIPT_DIR / "create_missing_program_scan_queue.py"
DEFAULT_PROFILE = SCRIPT_DIR.parent / "templates" / "delivery-profile.yaml"


def run_step(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise SystemExit(result.returncode)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-name", help="SME review name; defaults to the program-list filename")
    parser.add_argument("--programs-file", required=True, help="SME program list (.txt or CSV)")
    parser.add_argument(
        "--artifact-root",
        "--working-root",
        dest="artifact_root",
        required=True,
        help="Current delivery/artifact root containing scanned program folders",
    )
    parser.add_argument(
        "--source-root",
        required=True,
        help="Source repository root used to resolve missing programs",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Program-set review output directory",
    )
    parser.add_argument(
        "--delivery-root",
        help="Output root for targeted program scans; defaults to --artifact-root",
    )
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE), help="delivery-profile.yaml")
    parser.add_argument("--inventory-dir")
    parser.add_argument("--working-branch")
    parser.add_argument("--artifact-repo-mode", choices=["current_run", "approved_document_repo"], default="current_run")
    parser.add_argument("--core-review-profile", choices=["standard_reader_first", "minimal_reader_first"])
    parser.add_argument("--review-id")
    parser.add_argument("--flow-slug")
    parser.add_argument("--program-set-slug")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing missing-program queue")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact_root = Path(args.artifact_root).resolve()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    profile = Path(args.profile).resolve()
    programs_file = Path(args.programs_file).resolve()
    review_name = args.review_name or programs_file.stem.replace("_", " ") or "program set review"
    inventory_dir = Path(args.inventory_dir).resolve() if args.inventory_dir else None
    delivery_root = Path(args.delivery_root).resolve() if args.delivery_root else artifact_root

    for label, path in (
        ("artifact root", artifact_root),
        ("source root", source_root),
        ("profile", profile),
        ("programs file", programs_file),
    ):
        if not path.exists():
            raise SystemExit(f"{label} not found: {path}")
    if not artifact_root.is_dir() or not source_root.is_dir():
        raise SystemExit("artifact root and source root must both be directories")

    build_command = [
        sys.executable,
        str(BUILDER),
        "build",
        "--review-name",
        review_name,
        "--programs-file",
        str(programs_file),
        "--working-root",
        str(artifact_root),
        "--source-root",
        str(source_root),
        "--profile",
        str(profile),
        "--output-dir",
        str(output_dir),
        "--artifact-repo-mode",
        args.artifact_repo_mode,
    ]
    if inventory_dir:
        build_command.extend(["--inventory-dir", str(inventory_dir)])
    for option, value in (
        ("--working-branch", args.working_branch),
        ("--core-review-profile", args.core_review_profile),
        ("--review-id", args.review_id),
        ("--flow-slug", args.flow_slug),
        ("--program-set-slug", args.program_set_slug),
    ):
        if value:
            build_command.extend([option, value])
    run_step(build_command)

    queue_dir = output_dir / "missing-program-list-batch"
    queue_command = [
        sys.executable,
        str(QUEUE),
        "--manifest",
        str(output_dir / "program-set-core-input-manifest.yaml"),
        "--source-root",
        str(source_root),
        "--delivery-root",
        str(delivery_root),
        "--out-dir",
        str(queue_dir),
    ]
    if args.force:
        queue_command.append("--force")
    run_step(queue_command)
    print(f"Program-set intake prepared: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
