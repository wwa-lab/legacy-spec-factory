#!/usr/bin/env python3
"""Build a program-set review and prepare recovery actions for blocked programs.

This is the one-step intake command for SME-provided program lists. It creates
the deterministic core manifest first, then creates the targeted
recovery queue when required artifacts or semantic readiness are not ready. It
does not scan source code itself.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BUILDER = SCRIPT_DIR / "program_set_core_review.py"
QUEUE = SCRIPT_DIR / "create_missing_program_scan_queue.py"
DEFAULT_PROFILE = SCRIPT_DIR.parent / "templates" / "delivery-profile.yaml"


def run_step(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise SystemExit(result.returncode)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result


def load_yaml(path: Path) -> dict[str, object]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required for program-set intake") from exc
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(f"manifest is not a YAML mapping: {path}")
    return payload


def clear_ready_recovery_queue(queue_dir: Path) -> None:
    """Remove only a generated recovery package after a successful rerun.

    A recovery directory can contain analyst notes or evidence gathered between
    runs.  Reuse the queue generator's allow-list cleanup rather than deleting
    the directory recursively, and fail closed when it contains anything the
    generator did not create.
    """

    if queue_dir.is_symlink():
        raise SystemExit(
            "refusing to clear a recovery queue through a symlink: "
            f"{queue_dir}. Replace it with a real generated queue directory first."
        )
    spec = importlib.util.spec_from_file_location(
        "legacy_ibmi_flow_recovery_queue_cleanup",
        QUEUE,
    )
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load recovery queue cleanup helper: {QUEUE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    try:
        module.clear_generated_queue_artifacts(queue_dir)
    except ValueError as exc:
        raise SystemExit(
            f"{exc}. Preserve or archive the manual recovery evidence, then remove "
            "it from the generated queue directory before rerunning."
        ) from exc
    if queue_dir.exists():
        try:
            queue_dir.rmdir()
        except OSError as exc:
            raise SystemExit(
                "recovery queue still contains unrecognized artifacts after generated "
                f"cleanup: {queue_dir}. Preserve or archive them before rerunning."
            ) from exc


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
    output_location = parser.add_mutually_exclusive_group(required=True)
    output_location.add_argument(
        "--project-root",
        help="Delivery project root; writes the stable review bundle under <project-root>/outputs/",
    )
    output_location.add_argument(
        "--output-dir",
        help="Explicit output parent; the stable flow/program-set folder is appended once",
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
    parser.add_argument(
        "--recovery-runner",
        choices=["cline_serial", "kiro_parallel"],
        default="cline_serial",
        help=(
            "Recovery queue execution surface: cline_serial creates the serial prompt; "
            "kiro_parallel additionally precreates scaffolds and generates isolated worker prompts"
        ),
    )
    parser.add_argument(
        "--recovery-max-parallel-agents",
        type=int,
        default=4,
        help="Maximum isolated Kiro recovery workers when --recovery-runner kiro_parallel",
    )
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing missing-program queue")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact_root = Path(args.artifact_root).resolve()
    source_root = Path(args.source_root).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else None
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
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
    if project_root is not None and not project_root.is_dir():
        raise SystemExit(f"project root not found or not a directory: {project_root}")
    if not artifact_root.is_dir() or not source_root.is_dir():
        raise SystemExit("artifact root and source root must both be directories")
    if args.recovery_max_parallel_agents < 1:
        raise SystemExit("--recovery-max-parallel-agents must be at least 1")

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
        "--artifact-repo-mode",
        args.artifact_repo_mode,
    ]
    if project_root is not None:
        build_command.extend(["--project-root", str(project_root)])
    else:
        assert output_dir is not None
        build_command.extend(["--output-dir", str(output_dir)])
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
    build_result = run_step(build_command)
    match = re.search(r"^OUTPUT_DIR=(.+)$", build_result.stdout, re.M)
    if not match:
        raise SystemExit("builder did not report the resolved OUTPUT_DIR")
    bundle_dir = Path(match.group(1).strip())
    manifest_path = bundle_dir / "program-set-core-input-manifest.yaml"
    manifest = load_yaml(manifest_path)

    if manifest.get("review_status") == "blocked_artifact_readiness":
        queue_dir = bundle_dir / "missing-program-list-batch"
        queue_command = [
            sys.executable,
            str(QUEUE),
            "--manifest",
            str(manifest_path),
            "--source-root",
            str(source_root),
            "--delivery-root",
            str(delivery_root),
            "--out-dir",
            str(queue_dir),
        ]
        if args.recovery_runner == "kiro_parallel":
            queue_command.extend(
                [
                    "--validation-mode",
                    "immediate",
                    "--scaffold-mode",
                    "precreate",
                    "--subagent-mode",
                    "prepare",
                    "--max-parallel-agents",
                    str(args.recovery_max_parallel_agents),
                ]
            )
        if args.force:
            queue_command.append("--force")
        run_step(queue_command)
    else:
        queue_dir = bundle_dir / "missing-program-list-batch"
        if queue_dir.exists():
            clear_ready_recovery_queue(queue_dir)
    print(f"Program-set intake prepared: {bundle_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
