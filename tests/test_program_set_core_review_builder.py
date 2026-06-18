from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)
BUILD_WRAPPER = REPO_ROOT / "scripts" / "build-program-set-core-review.py"
VALIDATE_WRAPPER = REPO_ROOT / "scripts" / "validate-program-set-core-review.py"
PROFILE_TEMPLATE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)


def load_program_set_builder():
    spec = importlib.util.spec_from_file_location("program_set_core_review", CANONICAL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load builder: {CANONICAL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["program_set_core_review"] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_program_set_builder()


def write_compact_artifacts(artifact_root: Path, missing: set[str] | None = None) -> None:
    missing = missing or set()
    artifact_root.mkdir(parents=True)
    all_artifacts = BUILDER.REQUIRED_COMPACT_ARTIFACTS + BUILDER.OPTIONAL_COMPACT_ARTIFACTS
    for filename in all_artifacts:
        if filename in missing:
            continue
        (artifact_root / filename).write_text(
            f"schema_version: '0.1'\nartifact: {filename}\n",
            encoding="utf-8",
        )


def run_git(root: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=True,
    )


def init_clean_git_source_root(source_root: Path) -> None:
    source_root.mkdir(parents=True)
    (source_root / "QRPGLESRC").mkdir()
    (source_root / "QRPGLESRC" / "CU257F.RPGLE").write_text(
        "\n".join(["H DFTACTGRP(*NO)", "C                   EVAL      RESULT = 'Y'"]),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=source_root, text=True, capture_output=True, check=True)
    run_git(source_root, ["config", "user.email", "test@example.com"])
    run_git(source_root, ["config", "user.name", "Test User"])
    run_git(source_root, ["add", "QRPGLESRC/CU257F.RPGLE"])
    run_git(source_root, ["commit", "-m", "test source"])


def write_inventory_cache(source_root: Path, source_revision_key: str | None = None) -> Path:
    inventory_dir = source_root / "outputs" / "repo-scan"
    inventory_dir.mkdir(parents=True)
    program_list = inventory_dir / "program-list.csv"
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
    with program_list.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "member": "CU257F",
                "object_type": "program",
                "source_kind": "RPGLE",
                "path": "QRPGLESRC/CU257F.RPGLE",
                "total_lines": "2",
                "nonblank_lines": "2",
                "comment_lines": "0",
                "code_lines": "2",
                "size_tier": "complex_normal_program",
                "tier_reason": "test fixture",
                "default_output_profile": "light_review_plus_triggered_sidecars",
                "classification_source": "legacy-ibmi-program-analyzer",
                "routine_count": "1",
                "external_call_count": "0",
                "object_dependency_count": "0",
                "file_operation_count": "0",
                "sql_statement_count": "0",
                "recommended_deep_read_count": "0",
            }
        )
    revision = BUILDER.detect_source_revision(source_root, ignore_paths=[inventory_dir])
    if source_revision_key is not None:
        revision = {**revision, "key": source_revision_key}
    (inventory_dir / "scan-summary.yaml").write_text(
        BUILDER.dump_yaml(
            {
                "schema_version": "0.1",
                "generated_by": "scan_ibmi_repo.py",
                "root": str(source_root),
                "source_revision": revision,
                "source_revision_key": revision["key"],
            }
        ),
        encoding="utf-8",
    )
    return inventory_dir


def build_review_fixture(temp_root: Path) -> tuple[Path, Path, dict[str, object]]:
    delivery_root = temp_root / "delivery-main"
    output_dir = temp_root / "delivery-work" / "modules" / "CAP-ID-0004-program_set_reviews" / "card_auth"
    programs_file = temp_root / "programs.txt"

    write_compact_artifacts(
        delivery_root / "modules" / "CAP-ID-0001-large_extreme_program" / "@CU118"
    )
    write_compact_artifacts(
        delivery_root / "modules" / "CAP-ID-0003-normal_program" / "CC050",
        missing={"routine-logic-details.yaml"},
    )
    programs_file.write_text("@CU118\nCU118\nCC050\nCU257F\n", encoding="utf-8")

    config = BUILDER.load_yaml(PROFILE_TEMPLATE)
    manifest = BUILDER.build_manifest(
        review_name="Card Auth Posting Core Review",
        programs=BUILDER.read_programs_file(programs_file),
        delivery_root=delivery_root,
        config=config,
        working_branch="develop-leo",
    )
    manifest_path, review_path = BUILDER.write_build_outputs(manifest, output_dir)
    return manifest_path, review_path, manifest


class ProgramSetCoreReviewBuilderTests(unittest.TestCase):
    def test_builder_reuses_remote_main_artifacts_and_preserves_program_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, manifest = build_review_fixture(Path(temp_dir))

            programs = {
                str(entry["normalized_name"]): entry
                for entry in manifest["programs"]  # type: ignore[index]
            }

            self.assertEqual(programs["@CU118"]["central_lookup_result"], "found_on_remote_main")
            self.assertEqual(programs["@CU118"]["artifact_source"], "remote_main")
            self.assertEqual(
                programs["@CU118"]["artifact_root"],
                "modules/CAP-ID-0001-large_extreme_program/@CU118",
            )
            self.assertEqual(programs["@CU118"]["tier"], "large_extreme_program")

            self.assertEqual(programs["CU118"]["central_lookup_result"], "not_found_on_remote_main")
            self.assertIsNone(programs["CU118"]["artifact_root"])
            self.assertEqual(programs["CU118"]["follow_up"], "scan this program")

            self.assertEqual(programs["CC050"]["central_lookup_result"], "found_on_remote_main")
            self.assertEqual(programs["CC050"]["tier"], "normal_program")
            self.assertEqual(
                programs["CC050"]["compact_artifacts"]["routine_logic_details_yaml"]["status"],
                "missing",
            )
            self.assertEqual(programs["CU257F"]["central_lookup_result"], "not_found_on_remote_main")

            review_text = review_path.read_text(encoding="utf-8")
            self.assertIn("Lookup Profile:", review_text)
            self.assertIn("Source Inventory Cache:", review_text)
            self.assertIn("Core Completeness Ledger:", review_text)
            self.assertIn("| @CU118 |", review_text)
            self.assertIn("| CU118 |", review_text)
            self.assertIn("routine-logic-details.yaml=missing", review_text)
            self.assertIn("## Calculation Logic", review_text)
            self.assertIn("## Validation Logic", review_text)
            self.assertIn("## Exception Handling", review_text)
            self.assertIn("## Message Inventory", review_text)
            self.assertNotIn("## Nodes", review_text)
            self.assertNotIn("## Edges", review_text)
            self.assertNotIn("flow-<FLOW-SLUG>.md", review_text)

            self.assertEqual(BUILDER.validate(manifest_path, review_path), [])

    def test_validator_rejects_missing_program_rows_and_full_flow_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _manifest = build_review_fixture(Path(temp_dir))
            review_text = review_path.read_text(encoding="utf-8")
            bad_review = review_text.replace(
                "| @CU118 | modules/CAP-ID-0001-large_extreme_program/@CU118 |",
                "| CU999 | modules/CAP-ID-0001-large_extreme_program/@CU118 |",
                1,
            )
            bad_review = bad_review + "\n## Nodes\n\nThis belongs only in a full flow artifact.\n"
            review_path.write_text(bad_review, encoding="utf-8")

            findings = BUILDER.validate(manifest_path, review_path)

            self.assertTrue(
                any("@CU118 missing from Sources table" in finding for finding in findings),
                findings,
            )
            self.assertTrue(
                any("forbidden full-flow section: Nodes" in finding for finding in findings),
                findings,
            )

    def test_builder_uses_working_root_for_newly_scanned_programs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            working_root = temp_root / "delivery-working"
            write_compact_artifacts(
                delivery_root / "modules" / "CAP-ID-0001-large_extreme_program" / "@CU118"
            )
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["@CU118", "CU257F"],
                delivery_root=delivery_root,
                working_root=working_root,
                config=config,
                working_branch="develop-leo",
            )
            programs = {
                str(entry["normalized_name"]): entry
                for entry in manifest["programs"]  # type: ignore[index]
            }

            self.assertEqual(programs["@CU118"]["central_lookup_result"], "found_on_remote_main")
            self.assertEqual(programs["@CU118"]["artifact_source"], "remote_main")
            self.assertEqual(programs["CU257F"]["central_lookup_result"], "not_found_on_remote_main")
            self.assertEqual(programs["CU257F"]["artifact_source"], "delivery_working_branch")
            self.assertEqual(
                programs["CU257F"]["artifact_root"],
                "modules/CAP-ID-0002-complex_normal_program/CU257F",
            )
            self.assertEqual(programs["CU257F"]["tier"], "complex_normal_program")
            self.assertEqual(programs["CU257F"]["follow_up"], "none - source scan completed in working branch")
            self.assertTrue(manifest["delivery_repo"]["working_root_used"])  # type: ignore[index]

    def test_builder_force_rescan_bypasses_remote_main_until_working_artifact_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            source_root = temp_root / "source"
            init_clean_git_source_root(source_root)
            write_inventory_cache(source_root)
            write_compact_artifacts(
                delivery_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F"],
                delivery_root=delivery_root,
                source_root=source_root,
                config=config,
                working_branch="develop-leo",
                force_rescan_requests={"CU257F": "SME requested refresh"},
            )
            program = manifest["programs"][0]  # type: ignore[index]
            inventory_program = manifest["source_inventory"]["programs"][0]  # type: ignore[index]

            self.assertEqual(program["central_lookup_result"], "found_on_remote_main")
            self.assertTrue(program["force_rescan"])
            self.assertEqual(program["artifact_source"], "source_scan_required")
            self.assertIsNone(program["artifact_root"])
            self.assertEqual(
                program["remote_main_artifact_root"],
                "modules/CAP-ID-0002-complex_normal_program/CU257F",
            )
            self.assertEqual(program["follow_up"], "force rescan requested - scan this program")
            self.assertEqual(inventory_program["inventory_status"], "found")
            self.assertTrue(inventory_program["targeted_scan_allowed"])

    def test_builder_force_rescan_uses_working_root_after_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            working_root = temp_root / "delivery-working"
            output_dir = temp_root / "review-output"
            write_compact_artifacts(
                delivery_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            )
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F"],
                delivery_root=delivery_root,
                working_root=working_root,
                config=config,
                working_branch="develop-leo",
                force_rescan_requests={"CU257F": "SME requested refresh"},
            )
            manifest_path, review_path = BUILDER.write_build_outputs(manifest, output_dir)
            program = manifest["programs"][0]  # type: ignore[index]

            self.assertEqual(program["central_lookup_result"], "found_on_remote_main")
            self.assertTrue(program["force_rescan"])
            self.assertEqual(program["artifact_source"], "delivery_working_branch")
            self.assertEqual(
                program["artifact_root"],
                "modules/CAP-ID-0002-complex_normal_program/CU257F",
            )
            self.assertEqual(program["follow_up"], "none - forced rescan completed in working branch")
            self.assertEqual(BUILDER.validate(manifest_path, review_path), [])
            self.assertIn(
                "| CU257F | modules/CAP-ID-0002-complex_normal_program/CU257F | found_on_remote_main | complex_normal_program | yes: SME requested refresh |",
                review_path.read_text(encoding="utf-8"),
            )

    def test_builder_reuses_fresh_source_inventory_cache_for_missing_programs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            source_root = temp_root / "source"
            init_clean_git_source_root(source_root)
            write_inventory_cache(source_root)

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F"],
                delivery_root=delivery_root,
                source_root=source_root,
                config=config,
                working_branch="develop-leo",
            )

            source_inventory = manifest["source_inventory"]  # type: ignore[index]
            self.assertEqual(source_inventory["freshness"], "fresh")
            self.assertEqual(source_inventory["action"], "reuse_inventory")
            self.assertEqual(source_inventory["program_list"]["status"], "present")
            self.assertEqual(source_inventory["scan_summary"]["status"], "present")
            self.assertEqual(source_inventory["programs"][0]["inventory_status"], "found")
            self.assertEqual(source_inventory["programs"][0]["source_path"], "QRPGLESRC/CU257F.RPGLE")
            self.assertEqual(source_inventory["programs"][0]["size_tier"], "complex_normal_program")
            self.assertTrue(source_inventory["programs"][0]["targeted_scan_allowed"])

    def test_builder_marks_inventory_stale_when_source_revision_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            source_root = temp_root / "source"
            init_clean_git_source_root(source_root)
            write_inventory_cache(source_root, source_revision_key="git:old")

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F"],
                delivery_root=delivery_root,
                source_root=source_root,
                config=config,
                working_branch="develop-leo",
            )

            source_inventory = manifest["source_inventory"]  # type: ignore[index]
            self.assertEqual(source_inventory["freshness"], "stale")
            self.assertEqual(source_inventory["action"], "rerun_repo_inventory_scan")
            self.assertEqual(source_inventory["programs"][0]["inventory_status"], "found")
            self.assertFalse(source_inventory["programs"][0]["targeted_scan_allowed"])

    def test_root_wrappers_build_and_validate_program_set_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            output_dir = temp_root / "review-output"
            programs_file = temp_root / "programs.txt"
            write_compact_artifacts(
                delivery_root / "modules" / "CAP-ID-0001-large_extreme_program" / "@CU118"
            )
            programs_file.write_text("@CU118\nCU257F\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_WRAPPER),
                    "--review-name",
                    "Card Auth Posting Core Review",
                    "--programs-file",
                    str(programs_file),
                    "--delivery-root",
                    str(delivery_root),
                    "--profile",
                    str(PROFILE_TEMPLATE),
                    "--output-dir",
                    str(output_dir),
                    "--working-branch",
                    "develop-leo",
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            subprocess.run(
                [
                    sys.executable,
                    str(VALIDATE_WRAPPER),
                    "--manifest",
                    str(output_dir / "program-set-core-input-manifest.yaml"),
                    "--review",
                    str(output_dir / "program-set-sme-core-review.md"),
                ],
                check=True,
                text=True,
                capture_output=True,
            )


if __name__ == "__main__":
    unittest.main()
