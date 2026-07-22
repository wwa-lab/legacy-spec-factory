from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


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


def write_compact_artifacts(
    artifact_root: Path,
    missing: set[str] | None = None,
    program: str | None = None,
) -> None:
    missing = missing or set()
    program = program or artifact_root.name
    large = "large_extreme_program" in artifact_root.as_posix()
    fixture = write_finalized_program_artifacts(
        artifact_root,
        program,
        size_tier="large_extreme_program" if large else "normal_program",
    )
    if large:
        source_index_payload = json.loads(
            fixture.source_index_yaml.read_text(encoding="utf-8")
        )
        source_index_payload["deep_read_windows"] = [
            {
                "window_id": f"DRW-{fixture.prefix}-001",
                "routine": "MAIN",
                "source_lines": "1-100",
                "why_selected": "fixture large-program checkpoint",
                "coverage_outcome": "selected_for_deep_read",
                "evidence": "source-index",
            }
        ]
        source_index_text = json.dumps(source_index_payload, indent=2) + "\n"
        fixture.source_index_yaml.write_text(source_index_text, encoding="utf-8")
        plan_path = artifact_root / f"{fixture.prefix}-deep-read-execution-plan.yaml"
        plan_path.write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "generated_by": "index_rpg_source.py",
                    "program": program,
                    "program_size_tier": "large_extreme_program",
                    "source_index_path": fixture.source_index_yaml.name,
                    "source_index_sha256": hashlib.sha256(
                        source_index_text.encode("utf-8")
                    ).hexdigest(),
                    "planned_deep_read": [
                        {
                            "window_id": f"DRW-{fixture.prefix}-001",
                            "routine": "MAIN",
                            "source_lines": "1-100",
                            "rlog_id": f"RLOG-{fixture.prefix}-001",
                            "batch_number": 1,
                            "batch_path": "routine-logic-details/"
                            f"{fixture.prefix}-deep-read-batch-001.md",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        summary_payload = json.loads(fixture.summary_yaml.read_text(encoding="utf-8"))
        summary_payload["sidecars"]["deep_read_execution_plan"] = {
            "path": plan_path.name,
            "status": "present",
        }
        fixture.summary_yaml.write_text(
            json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8"
        )
        routine_payload = json.loads(fixture.routine_details_yaml.read_text(encoding="utf-8"))
        inventory = routine_payload["routine_logic_inventory"]
        for entry in inventory["summary"]:
            entry.update(
                {
                    "semantic_status": "deep_read_complete",
                    "coverage": "deep_read",
                }
            )
        for entry in inventory["details"]:
            entry.update(
                {
                    "semantic_status": "deep_read_complete",
                    "coverage": "deep_read",
                    "step_by_step_logic": "Reads the entry state and follows the source-backed dispatch branch.",
                    "field_calculations": "Assigns the documented status carrier from the evaluated source condition.",
                    "conditioned_calculation_blocks": "Runs the assignment only when the source validation guard succeeds.",
                    "outcome_reverse_traces": "The returned outcome traces to the confirmed source-backed branch.",
                    "field_lineage": "Entry parameter flows through working status to the returned outcome.",
                    "branch_outcomes": "Success continues and failure returns the documented error status.",
                    "routine_exception_closure": "No local exception is observed; failure returns through the status carrier.",
                }
            )
        fixture.routine_details_yaml.write_text(
            json.dumps(routine_payload, indent=2) + "\n", encoding="utf-8"
        )
        batch_path = (
            artifact_root
            / "routine-logic-details"
            / f"{fixture.prefix}-deep-read-batch-001.md"
        )
        batch_path.parent.mkdir(parents=True, exist_ok=True)
        batch_path.write_text(
            "\n\n".join(
                [
                    f"# Routine Logic Details: {program} - Deep Read Batch 001",
                    "## Calculation Logic\n\nSource-backed calculation evidence is consolidated for this batch.",
                    "## Validation Logic\n\nSource-backed validation outcomes are consolidated for this batch.",
                    "## Exception Handling\n\nSource-backed exception closure is consolidated for this batch.",
                    "## Scope\n\nOne source-backed window is covered by this checkpoint.",
                    f"## Batch Coverage Summary\n\n| Window ID | Routine | Source Lines | RLOG Detail |\n| --- | --- | --- | --- |\n| DRW-{fixture.prefix}-001 | MAIN | 1-100 | RLOG-{fixture.prefix}-001 |",
                    "## Message Inventory\n\nNo additional message or status token is observed in this checkpoint.",
                    f"## Routine Details\n\n### RLOG-{fixture.prefix}-001 - MAIN\n\n- Source lines: 1-100.\n- Source-backed routine detail explains the entry trigger, branch decisions, field assignments, validation outcome, side effects, and exception closure.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    for filename in missing:
        path = artifact_root / BUILDER.program_artifact_filename(program, filename)
        if path.exists():
            path.unlink()
    for filename in BUILDER.OPTIONAL_COMPACT_ARTIFACTS:
        if filename not in missing:
            path = artifact_root / BUILDER.program_artifact_filename(program, filename)
            path.write_text("schema_version: '0.1'\n", encoding="utf-8")


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
    working_root = temp_root / "delivery-work"
    output_dir = temp_root / "delivery-work" / "modules" / "CAP-ID-0004-program_set_reviews" / "card_auth"
    programs_file = temp_root / "programs.txt"

    write_compact_artifacts(
        working_root / "modules" / "CAP-ID-0001-large_extreme_program" / "@CU118"
    )
    write_compact_artifacts(
        working_root / "modules" / "CAP-ID-0001-large_extreme_program" / "CU118"
    )
    write_compact_artifacts(
        working_root / "modules" / "CAP-ID-0003-normal_program" / "CC050"
    )
    write_compact_artifacts(
        working_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
    )
    programs_file.write_text("@CU118\nCU118\nCC050\nCU257F\n", encoding="utf-8")

    config = BUILDER.load_yaml(PROFILE_TEMPLATE)
    manifest = BUILDER.build_manifest(
        review_name="Card Auth Posting Core Review",
        programs=BUILDER.read_programs_file(programs_file),
        artifact_root=working_root,
        config=config,
        working_branch="develop-leo",
        artifact_repo_mode=BUILDER.ARTIFACT_REPO_CURRENT_RUN,
        programs_file=programs_file,
    )
    manifest_path, review_path = BUILDER.write_build_outputs(manifest, output_dir)
    write_reader_first_review(review_path, manifest)
    return manifest_path, review_path, manifest


def write_reader_first_review(review_path: Path, manifest: dict[str, object]) -> None:
    programs = manifest["programs"]  # type: ignore[index]
    manifest["review_status"] = "complete_exploratory"
    manifest["merge_coverage"] = "complete"
    (review_path.parent / "program-set-core-input-manifest.yaml").write_text(
        BUILDER.dump_yaml(manifest), encoding="utf-8"
    )
    coverage_path = review_path.parent / "program-set-core-coverage.yaml"
    facts_path = review_path.parent / "program-set-core-facts.yaml"
    coverage = BUILDER.load_yaml(coverage_path)
    facts = BUILDER.load_yaml(facts_path)
    items = [
        {
            **item,
            "status": "included",
            "review_anchor": f"review-test-{index:03d}",
            "merged_source_fact_ids": [],
            "exclusion_reason": None,
        }
        for index, item in enumerate(coverage.get("coverage_items", []), start=1)
    ]
    coverage["coverage_items"] = items
    coverage["items"] = [dict(item) for item in items]
    coverage["coverage_status"] = "complete"
    coverage["review_status"] = "complete_exploratory"
    coverage["coverage_counts"] = {
        **coverage.get("coverage_counts", {}),
        "total_source_facts": len(items),
        "accounted_source_facts": len(items),
        "pending_source_facts": 0,
    }
    coverage["expected_source_fact_count"] = len(items)
    coverage["coverage_item_count"] = len(items)
    coverage["status_counts"] = {
        "included": len(items),
        "merged": 0,
        "excluded_non_core": 0,
        "pending": 0,
    }
    coverage_path.write_text(BUILDER.dump_yaml(coverage), encoding="utf-8")
    fact_map = {
        str(fact["source_fact_id"]): fact for fact in facts.get("source_facts", [])
    }
    all_fact_refs = "; ".join(fact_map)
    program_names = [str(entry["normalized_name"]) for entry in programs]
    front_programs = "\n".join(
        f"  - {json.dumps(program)}" for program in program_names
    )

    section_headers = {
        "Program Set Reading Summary": (
            "Program",
            "Scope / Reader-First Contribution",
            "Artifact Readiness",
            "Coverage",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Calculation Logic": (
            "Calculation / Assignment",
            "Program",
            "Routine",
            "Target Field / Carrier",
            "Source Operands / Carriers",
            "Guard / Branch",
            "Effect",
            "Supporting Detail",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Validation Logic": (
            "Message / Status / Outcome",
            "Description",
            "Program",
            "Routine",
            "Condition / Evidence",
            "Carrier / Destination",
            "Effect",
            "Supporting Detail",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Exception Handling": (
            "Exception / Error Path",
            "Program",
            "Routine",
            "Detection Mechanism",
            "Fields / Messages Set",
            "Handling Action",
            "Effect",
            "Supporting Detail",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
        "Message Inventory": (
            "Message / Status / Literal",
            "Description",
            "Type",
            "Program / Routine Sources",
            "Occurrences",
            "Condition / Handler",
            "Carrier / Destination",
            "Effect",
            "Detail Refs",
            "Evidence Status",
            "Review Row ID",
            "Source Fact Refs",
        ),
    }

    def clean_cell(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).replace("|", "/").strip()

    def fact_mapping_table(review_section: str) -> str:
        source_section = {
            "Program Set Reading Summary": "Program Reading Summary",
        }.get(review_section, review_section)
        headers = section_headers[review_section]
        rows: list[str] = []
        for item in items:
            if item.get("section") != source_section:
                continue
            fact = fact_map[str(item["source_fact_id"])]
            semantic_values = [
                clean_cell(fact.get("logic")),
                clean_cell(fact.get("exact_value")),
                *(
                    clean_cell(value)
                    for _field, value in BUILDER._required_fact_semantics(fact)
                ),
                "Source-backed reader-first evidence retained for focused SME review",
            ]
            detail = "; ".join(
                dict.fromkeys(value for value in semantic_values if value)
            )
            program = clean_cell(fact.get("program")) or "source program"
            routine = clean_cell(fact.get("routine")) or "program-wide context"
            exact = clean_cell(fact.get("exact_value"))
            values = {
                "Program": program,
                "Scope / Reader-First Contribution": detail,
                "Artifact Readiness": "ready",
                "Coverage": "included",
                "Calculation / Assignment": clean_cell(fact.get("calculation")) or detail,
                "Routine": routine,
                "Target Field / Carrier": clean_cell(fact.get("target_carrier")) or exact or "source-backed carrier",
                "Source Operands / Carriers": clean_cell(fact.get("source_carriers")) or "source-backed operands",
                "Guard / Branch": clean_cell(fact.get("guard")) or "source-backed branch context",
                "Message / Status / Outcome": exact or clean_cell(fact.get("description")) or detail,
                "Condition / Evidence": clean_cell(fact.get("trigger_chain")) or clean_cell(fact.get("guard")) or "source-backed condition",
                "Carrier / Destination": clean_cell(fact.get("carrier_destination")) or clean_cell(fact.get("target_carrier")) or "source-backed destination",
                "Exception / Error Path": clean_cell(fact.get("exception_path")) or detail,
                "Detection Mechanism": clean_cell(fact.get("detection_mechanism")) or "source-backed detection",
                "Fields / Messages Set": clean_cell(fact.get("fields_messages_set")) or exact or "source-backed outcome carrier",
                "Handling Action": clean_cell(fact.get("exception_action")) or "source-backed handling action",
                "Message / Status / Literal": exact or detail,
                "Description": clean_cell(fact.get("description")) or detail,
                "Type": clean_cell(fact.get("message_type")) or clean_cell(fact.get("fact_type")) or "source evidence",
                "Program / Routine Sources": f"{program} {routine}",
                "Occurrences": clean_cell(fact.get("occurrences")) or "source-backed occurrence",
                "Condition / Handler": clean_cell(fact.get("trigger_handler")) or "source-backed handler",
                "Effect": clean_cell(fact.get("effect")) or detail,
                "Detail Refs": detail,
                "Supporting Detail": detail,
                "Evidence Status": clean_cell(fact.get("evidence_status")) or "source_backed",
                "Review Row ID": f'<a id="{item["review_anchor"]}"></a> {item["review_anchor"]}',
                "Source Fact Refs": clean_cell(item["source_fact_id"]),
            }
            rows.append("| " + " | ".join(values[header] for header in headers) + " |")
        header = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        return "\n".join((header, separator, *rows))

    review_text = f"""---
document_id: {manifest.get("document_id") or manifest["review_id"]}
flow_slug: {manifest["flow_slug"]}
program_set_slug: {manifest["program_set_slug"]}
programs:
{front_programs}
review_status: complete_exploratory
artifact_version: '{manifest["artifact_version"]}'
---

# Program Set SME Core Review: {manifest["folder_slug"]}

## Program Set Reading Summary

This standalone_exploratory draft covers the SME-requested card authorization
program set in the order supplied for review: @CU118, CU118, CC050, and CU257F.
The set is meant to help the SME read the cross-program processing path before
checking audit details. Current evidence covers entry/dispatch handoff,
calculation of posting response fields, validation of account/status outcomes,
exception/message handling, and persistence/finalization follow-up for programs
that still need source scan.

{fact_mapping_table("Program Set Reading Summary")}

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
| Entry / dispatch | @CU118 MAIN; CU118 MAIN | Read each program's source-backed entry contribution without inferring runtime order. | <a id="review-overview-entry"></a> review-overview-entry | {all_fact_refs} |
| Calculation | @CU118 MAIN; CC050 MAIN | Posting response fields retain their source-backed carriers and guarded outcomes. | <a id="review-overview-calculation"></a> review-overview-calculation | {all_fact_refs} |
| Validation | @CU118 MAIN; CC050 MAIN | Account status and request completeness retain their exact response outcomes. | <a id="review-overview-validation"></a> review-overview-validation | {all_fact_refs} |
| Exception / message | @CU118 MAIN; CC050 MAIN | Message values remain exact where validation or file access fails. | <a id="review-overview-exception"></a> review-overview-exception | {all_fact_refs} |
| Persistence / finalization | CC050 MAIN; CU257F MAIN | Review source-backed update effects without asserting an execution sequence. | <a id="review-overview-finalization"></a> review-overview-finalization | {all_fact_refs} |

## Calculation Logic

{fact_mapping_table("Calculation Logic")}

## Validation Logic

{fact_mapping_table("Validation Logic")}

## Exception Handling

{fact_mapping_table("Exception Handling")}

## Message Inventory

{fact_mapping_table("Message Inventory")}

## Core Completeness Ledger

{BUILDER.render_completeness_table(programs)}

## Coverage Reconciliation

All normalized source facts are included at the stable anchors declared in
this review and reconciled in the sibling coverage control.

## Sources

{BUILDER.render_sources_table(programs)}

## Run Profile

{BUILDER.render_run_profile(manifest)}

## Source Inventory Cache

{BUILDER.render_source_inventory(manifest)}
"""
    review_path.write_text(review_text, encoding="utf-8")


class ProgramSetCoreReviewBuilderTests(unittest.TestCase):
    def test_builder_uses_current_run_artifacts_and_preserves_program_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, manifest = build_review_fixture(Path(temp_dir))

            programs = {
                str(entry["normalized_name"]): entry
                for entry in manifest["programs"]  # type: ignore[index]
            }

            self.assertEqual(programs["@CU118"]["run_resolution"], "analyzed_this_run")
            self.assertEqual(programs["@CU118"]["artifact_source"], "delivery_working_branch")
            self.assertEqual(
                programs["@CU118"]["artifact_root"],
                "modules/CAP-ID-0001-large_extreme_program/@CU118",
            )
            self.assertEqual(programs["@CU118"]["tier"], "large_extreme_program")

            self.assertEqual(programs["CU118"]["run_resolution"], "analyzed_this_run")
            self.assertEqual(
                programs["CU118"]["artifact_root"],
                "modules/CAP-ID-0001-large_extreme_program/CU118",
            )

            self.assertEqual(programs["CC050"]["run_resolution"], "analyzed_this_run")
            self.assertEqual(programs["CC050"]["tier"], "normal_program")
            self.assertEqual(
                programs["CC050"]["compact_artifacts"]["routine_logic_details_yaml"]["status"],
                "present",
            )
            self.assertEqual(programs["CU257F"]["run_resolution"], "analyzed_this_run")

            review_text = review_path.read_text(encoding="utf-8")
            expected_order = [
                "## Program Set Reading Summary",
                "## Cross-Program Processing Overview",
                "## Calculation Logic",
                "## Validation Logic",
                "## Exception Handling",
                "## Message Inventory",
                "## Core Completeness Ledger",
                "## Coverage Reconciliation",
                "## Sources",
                "## Run Profile",
                "## Source Inventory Cache",
            ]
            positions = [review_text.index(section) for section in expected_order]
            self.assertEqual(positions, sorted(positions))
            self.assertIn("| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |", review_text)
            self.assertIn("Routine Logic Evidence", review_text)
            self.assertIn("| Cross-Run Reuse | false |", review_text)
            self.assertIn("| @CU118 |", review_text)
            self.assertIn("| CU118 |", review_text)
            self.assertIn("@CU118-routine-logic-details.yaml=present", review_text)
            self.assertIn("CC050-routine-logic-details.yaml=present", review_text)
            self.assertNotIn("optional_not_required", review_text)
            self.assertNotIn(
                "| Program | Expected In Scope From | Run Resolution | Calculation Logic | Validation Logic | Exception Handling |",
                review_text,
            )
            self.assertNotIn("central_lookup_result", BUILDER.dump_yaml(manifest))
            self.assertNotIn("found_on_remote_main", review_text)
            self.assertIn("## Calculation Logic", review_text)
            self.assertIn("## Validation Logic", review_text)
            self.assertIn("## Exception Handling", review_text)
            self.assertIn("## Message Inventory", review_text)
            self.assertNotIn("## Nodes", review_text)
            self.assertNotIn("## Edges", review_text)
            self.assertNotIn("flow-<FLOW-SLUG>.md", review_text)

            self.assertEqual(BUILDER.validate(manifest_path, review_path), [])

    def test_builder_defaults_to_approved_document_repo_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            document_repo = temp_root / "legacy-modernization-delivery"
            write_compact_artifacts(
                document_repo / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            )
            programs_file = temp_root / "approved-programs.txt"
            programs_file.write_text("CC050\n", encoding="utf-8")

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CC050"],
                artifact_root=document_repo,
                config=config,
                working_branch="main",
                programs_file=programs_file,
            )

            entry = manifest["programs"][0]  # type: ignore[index]
            self.assertEqual(entry["run_resolution"], "reused_artifact_repo")
            self.assertEqual(entry["artifact_source"], "approved_document_repo")
            self.assertEqual(
                manifest["run_profile"]["artifact_repo_mode"],  # type: ignore[index]
                "approved_document_repo",
            )
            self.assertEqual(
                manifest["run_profile"]["reuse_policy"],  # type: ignore[index]
                "approved_document_repo_clone",
            )

    def test_current_run_remains_an_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, _review_path, manifest = build_review_fixture(Path(temp_dir))

            self.assertEqual(
                manifest["run_profile"]["artifact_repo_mode"],  # type: ignore[index]
                "current_run",
            )
            self.assertEqual(
                manifest["programs"][0]["run_resolution"],  # type: ignore[index]
                "analyzed_this_run",
            )
            self.assertEqual(
                BUILDER.validate_manifest(manifest),
                [],
            )

    def test_builder_can_reuse_approved_document_repo_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            document_repo = temp_root / "legacy-modernization-delivery"
            output_dir = document_repo / "modules" / "CAP-ID-0004-program_set_reviews" / "card_auth"
            write_compact_artifacts(
                document_repo / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            )
            programs_file = temp_root / "approved-programs.txt"
            programs_file.write_text("CC050\n", encoding="utf-8")

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CC050"],
                artifact_root=document_repo,
                config=config,
                working_branch="main",
                artifact_repo_mode=BUILDER.ARTIFACT_REPO_APPROVED_DOCUMENT,
                programs_file=programs_file,
            )
            manifest_path, review_path = BUILDER.write_build_outputs(manifest, output_dir)
            write_reader_first_review(review_path, manifest)

            entry = manifest["programs"][0]  # type: ignore[index]
            self.assertEqual(entry["run_resolution"], "reused_artifact_repo")
            self.assertEqual(entry["artifact_source"], "approved_document_repo")
            self.assertEqual(
                entry["artifact_root"],
                "modules/CAP-ID-0003-normal_program/CC050",
            )
            self.assertEqual(
                manifest["run_profile"]["artifact_repo_mode"],  # type: ignore[index]
                "approved_document_repo",
            )
            self.assertEqual(
                manifest["run_profile"]["reuse_policy"],  # type: ignore[index]
                "approved_document_repo_clone",
            )
            self.assertEqual(
                manifest["source_inventory"]["programs"][0]["inventory_status"],  # type: ignore[index]
                "not_needed_approved_document_repo_artifact_present",
            )

            findings = BUILDER.validate(manifest_path, review_path)
            self.assertEqual(findings, [])

    def test_validator_rejects_artifact_repo_reuse_without_mode(self) -> None:
        manifest = {
            "run_profile": {"artifact_repo_mode": "current_run"},
            "programs": [
                {
                    "normalized_name": "CC050",
                    "run_resolution": "reused_artifact_repo",
                    "artifact_root": "modules/CAP-ID-0003-normal_program/CC050",
                    "artifact_source": "approved_document_repo",
                    "compact_artifacts": {
                        BUILDER.artifact_key(filename): {"status": "present", "path": filename}
                        for filename in BUILDER.REQUIRED_COMPACT_ARTIFACTS
                    },
                }
            ],
        }

        findings = BUILDER.validate_manifest(manifest)

        self.assertTrue(
            any("requires artifact_repo_mode approved_document_repo" in finding for finding in findings),
            findings,
        )

    def test_builder_prepares_reader_first_bundle_but_never_writes_final_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-work"
            output_dir = temp_root / "review-output"
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CC050"],
                artifact_root=working_root,
                config=config,
                working_branch="develop-leo",
            )
            manifest_path, review_path = BUILDER.write_build_outputs(manifest, output_dir)

            self.assertFalse(review_path.exists())
            self.assertTrue((manifest_path.parent / "program-set-reader-first-source-pack.md").is_file())
            self.assertTrue((manifest_path.parent / "program-set-core-facts.yaml").is_file())
            self.assertTrue((manifest_path.parent / "program-set-core-coverage.yaml").is_file())

            findings = BUILDER.validate(manifest_path, review_path)

            self.assertTrue(
                any("missing review artifact" in finding for finding in findings),
                findings,
            )

    def test_ready_to_blocked_rebuild_removes_stale_ready_only_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-work"
            output_dir = temp_root / "review-output"
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            )
            manifest = BUILDER.build_manifest(
                review_name="Ready Then Blocked",
                programs=["CC050"],
                artifact_root=working_root,
                config=BUILDER.load_yaml(PROFILE_TEMPLATE),
                working_branch="fixture",
            )
            manifest_path, _review_path = BUILDER.write_build_outputs(
                manifest, output_dir
            )
            source_pack = manifest_path.parent / BUILDER.SOURCE_PACK_FILENAME
            facts = manifest_path.parent / BUILDER.CORE_FACTS_FILENAME
            self.assertTrue(source_pack.is_file())
            self.assertTrue(facts.is_file())

            blocked_entry = {
                **manifest["programs"][0],
                "run_resolution": BUILDER.RUN_PENDING,
                "artifact_root": None,
                "artifact_source": "source_scan_required",
                "artifact_readiness": {
                    "status": "not_ready",
                    "findings": ["fixture forces a blocked rebuild"],
                },
            }
            blocked = {
                **manifest,
                "review_status": "blocked_artifact_readiness",
                "artifact_readiness": "not_ready",
                "merge_coverage": "blocked",
                "programs": [blocked_entry],
            }
            BUILDER.write_build_outputs(blocked, output_dir)

            self.assertFalse(source_pack.exists())
            self.assertFalse(facts.exists())
            self.assertTrue(
                (manifest_path.parent / BUILDER.CORE_COVERAGE_FILENAME).is_file()
            )

    def test_validator_rejects_missing_program_set_reading_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _manifest = build_review_fixture(Path(temp_dir))
            review_text = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                review_text.replace("## Program Set Reading Summary\n\n", "", 1),
                encoding="utf-8",
            )

            findings = BUILDER.validate(manifest_path, review_path)

            self.assertTrue(
                any("missing required reader-first ## sections: Program Set Reading Summary" in finding for finding in findings),
                findings,
            )

    def test_validator_rejects_placeholder_summary_and_missing_processing_overview_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _manifest = build_review_fixture(Path(temp_dir))
            review_text = review_path.read_text(encoding="utf-8")
            bad_review = review_text.replace(
                "This standalone_exploratory draft covers the SME-requested card authorization\n"
                "program set in the order supplied for review: @CU118, CU118, CC050, and CU257F.\n"
                "The set is meant to help the SME read the cross-program processing path before\n"
                "checking audit details. Current evidence covers entry/dispatch handoff,\n"
                "calculation of posting response fields, validation of account/status outcomes,\n"
                "exception/message handling, and persistence/finalization follow-up for programs\n"
                "that still need source scan.",
                "Pending placeholder artifact list: program-analysis-summary.yaml; message-inventory.yaml.",
                1,
            )
            bad_review = bad_review.replace(
                "| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |\n"
                "| --- | --- | --- | --- | --- |\n",
                "| Layer | Refs |\n| --- | --- |\n",
                1,
            )
            review_path.write_text(bad_review, encoding="utf-8")

            findings = BUILDER.validate(manifest_path, review_path)

            self.assertTrue(
                any("Program Set Reading Summary is placeholder/artifact-only" in finding for finding in findings),
                findings,
            )
            self.assertTrue(
                any("Cross-Program Processing Overview missing required table headers" in finding for finding in findings),
                findings,
            )

    def test_validator_rejects_core_sections_with_only_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _manifest = build_review_fixture(Path(temp_dir))
            review_text = review_path.read_text(encoding="utf-8")
            calculation_block = BUILDER.h2_section_block(
                review_text, "Calculation Logic"
            )
            calculation_lines = calculation_block.splitlines()
            for index, line in enumerate(calculation_lines):
                if not line.startswith("|") or BUILDER.is_table_separator(line):
                    continue
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if cells and cells[0] == "Calculation / Assignment":
                    continue
                for cell_index in (0, 2, 3, 4, 5, 6, 7):
                    cells[cell_index] = "RLOG-AUTH-REF"
                calculation_lines[index] = "| " + " | ".join(cells) + " |"
            bad_review = review_text.replace(
                calculation_block, "\n".join(calculation_lines), 1
            )
            review_path.write_text(bad_review, encoding="utf-8")

            findings = BUILDER.validate(manifest_path, review_path)

            self.assertTrue(
                any(
                    "Calculation Logic" in finding
                    and ("reader-useful detail" in finding or "link-only" in finding)
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_audit_sections_before_reader_first_core(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _manifest = build_review_fixture(Path(temp_dir))
            review_text = review_path.read_text(encoding="utf-8")
            run_profile = review_text[
                review_text.index("## Run Profile") : review_text.index("## Source Inventory Cache")
            ]
            bad_review = review_text.replace(run_profile, "", 1)
            bad_review = bad_review.replace(
                "## Program Set Reading Summary",
                run_profile + "\n\n## Program Set Reading Summary",
                1,
            )
            review_path.write_text(bad_review, encoding="utf-8")

            findings = BUILDER.validate(manifest_path, review_path)

            self.assertTrue(
                any("reader-first core sections must appear before audit/control sections" in finding for finding in findings),
                findings,
            )

    def test_builder_keeps_missing_normal_program_routine_logic_as_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-work"
            output_dir = temp_root / "review-output"
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0003-normal_program" / "CC050",
                missing={"routine-logic-details.md", "routine-logic-details.yaml"},
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Normal Program Missing Routine Detail",
                programs=["CC050"],
                artifact_root=working_root,
                config=config,
                working_branch="develop-leo",
                artifact_repo_mode=BUILDER.ARTIFACT_REPO_CURRENT_RUN,
            )
            manifest_path, review_path = BUILDER.write_build_outputs(manifest, output_dir)

            entry = manifest["programs"][0]
            self.assertEqual(manifest["review_status"], "ready_for_synthesis")
            self.assertEqual(entry["run_resolution"], "analyzed_this_run")
            self.assertIsNotNone(entry["artifact_root"])
            self.assertEqual(entry["artifact_readiness"]["status"], "ready")
            self.assertTrue(entry["artifact_readiness"]["pending_findings"])
            self.assertFalse(review_path.exists())
            self.assertTrue((manifest_path.parent / "program-set-core-facts.yaml").exists())

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

    def test_builder_marks_duplicate_program_as_reused_same_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-working"
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F", "CU257F"],
                artifact_root=working_root,
                config=config,
                working_branch="develop-leo",
                artifact_repo_mode=BUILDER.ARTIFACT_REPO_CURRENT_RUN,
            )
            first, second = manifest["programs"]  # type: ignore[index]

            self.assertEqual(first["run_resolution"], "analyzed_this_run")
            self.assertEqual(second["run_resolution"], "reused_same_run")
            self.assertEqual(
                second["artifact_root"],
                "modules/CAP-ID-0002-complex_normal_program/CU257F",
            )
            self.assertIn("Duplicate normalized program name", manifest["warnings"][0])  # type: ignore[index]

    def test_builder_keeps_duplicate_pending_when_no_current_run_artifact_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-working"

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F", "CU257F"],
                artifact_root=working_root,
                config=config,
                working_branch="develop-leo",
            )
            first, second = manifest["programs"]  # type: ignore[index]

            self.assertEqual(first["run_resolution"], "pending_source")
            self.assertEqual(second["run_resolution"], "pending_source")
            self.assertIsNone(second["artifact_root"])
            self.assertEqual(second["artifact_source"], "source_scan_required")
            self.assertIn("will resolve once", manifest["warnings"][0])  # type: ignore[index]

    def test_validator_reports_legacy_manifest_without_keyerror(self) -> None:
        manifest = {
            "programs": [
                {
                    "normalized_name": "CU257F",
                    "central_lookup_result": "found_on_remote_main",
                }
            ]
        }

        findings = BUILDER.validate_manifest(manifest)

        self.assertTrue(
            any("legacy central_lookup_result" in finding for finding in findings),
            findings,
        )

    def test_validator_rejects_invalid_duplicate_program_resolution(self) -> None:
        manifest = {
            "programs": [
                {
                    "normalized_name": "CU257F",
                    "run_resolution": "analyzed_this_run",
                    "artifact_root": "modules/CAP-ID-0002-complex_normal_program/CU257F",
                    "artifact_source": "delivery_working_branch",
                },
                {
                    "normalized_name": "CU257F",
                    "run_resolution": "pending_source",
                    "artifact_root": None,
                    "artifact_source": "source_scan_required",
                },
            ]
        }

        findings = BUILDER.validate_manifest(manifest)

        self.assertTrue(
            any(
                "duplicate with artifact must use reused_same_run" in finding
                for finding in findings
            ),
            findings,
        )

    def test_validator_rejects_duplicate_reuse_with_different_artifact_root(self) -> None:
        manifest = {
            "programs": [
                {
                    "normalized_name": "CU257F",
                    "run_resolution": "analyzed_this_run",
                    "artifact_root": "modules/CAP-ID-0002-complex_normal_program/CU257F",
                    "artifact_source": "delivery_working_branch",
                },
                {
                    "normalized_name": "CU257F",
                    "run_resolution": "reused_same_run",
                    "artifact_root": "modules/CAP-ID-0003-normal_program/CU257F",
                    "artifact_source": "same_run_previous_program",
                },
            ]
        }

        findings = BUILDER.validate_manifest(manifest)

        self.assertTrue(
            any("duplicate artifact_root must match" in finding for finding in findings),
            findings,
        )

    def test_program_first_uses_only_current_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-working"
            write_compact_artifacts(
                working_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CC050"
            )

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F", "CC050"],
                artifact_root=working_root,
                config=config,
                working_branch="develop-leo",
                artifact_repo_mode=BUILDER.ARTIFACT_REPO_CURRENT_RUN,
                program_first=True,
            )
            programs = {
                str(entry["normalized_name"]): entry
                for entry in manifest["programs"]  # type: ignore[index]
            }

            self.assertEqual(programs["CU257F"]["run_resolution"], "pending_source")
            self.assertEqual(programs["CU257F"]["artifact_source"], "source_scan_required")
            self.assertIsNone(programs["CU257F"]["artifact_root"])
            self.assertEqual(programs["CC050"]["run_resolution"], "analyzed_this_run")
            self.assertEqual(programs["CC050"]["artifact_source"], "delivery_working_branch")
            self.assertEqual(
                programs["CC050"]["artifact_root"],
                "modules/CAP-ID-0002-complex_normal_program/CC050",
            )
            self.assertTrue(manifest["run_profile"]["program_first"])  # type: ignore[index]

    def test_builder_reuses_fresh_source_inventory_cache_for_missing_programs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-working"
            source_root = temp_root / "source"
            init_clean_git_source_root(source_root)
            write_inventory_cache(source_root)

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F"],
                artifact_root=working_root,
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
            self.assertEqual(source_inventory["programs"][0]["run_resolution"], "pending_source")
            self.assertEqual(source_inventory["programs"][0]["source_path"], "QRPGLESRC/CU257F.RPGLE")
            self.assertEqual(source_inventory["programs"][0]["size_tier"], "complex_normal_program")
            self.assertTrue(source_inventory["programs"][0]["targeted_scan_allowed"])

    def test_builder_blocks_program_missing_from_fresh_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            document_repo = temp_root / "legacy-modernization-delivery"
            source_root = temp_root / "source"
            init_clean_git_source_root(source_root)
            write_inventory_cache(source_root)

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["MISSINGPGM"],
                artifact_root=document_repo,
                source_root=source_root,
                config=config,
                working_branch="main",
                artifact_repo_mode=BUILDER.ARTIFACT_REPO_APPROVED_DOCUMENT,
            )

            entry = manifest["programs"][0]  # type: ignore[index]
            source_inventory = manifest["source_inventory"]  # type: ignore[index]

            self.assertEqual(entry["run_resolution"], "blocked_missing_source")
            self.assertEqual(entry["artifact_source"], "source_inventory_missing")
            self.assertIn("confirm SME program name", entry["follow_up"])
            self.assertEqual(source_inventory["programs"][0]["inventory_status"], "missing_from_inventory")
            self.assertEqual(source_inventory["programs"][0]["run_resolution"], "blocked_missing_source")
            self.assertFalse(source_inventory["programs"][0]["targeted_scan_allowed"])

    def test_builder_marks_inventory_stale_when_source_revision_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-working"
            source_root = temp_root / "source"
            init_clean_git_source_root(source_root)
            write_inventory_cache(source_root, source_revision_key="git:old")

            config = BUILDER.load_yaml(PROFILE_TEMPLATE)
            manifest = BUILDER.build_manifest(
                review_name="Card Auth Posting Core Review",
                programs=["CU257F"],
                artifact_root=working_root,
                source_root=source_root,
                config=config,
                working_branch="develop-leo",
            )

            source_inventory = manifest["source_inventory"]  # type: ignore[index]
            self.assertEqual(source_inventory["freshness"], "stale")
            self.assertEqual(
                source_inventory["action"],
                "provide_fresh_inventory_or_exact_source_mapping",
            )
            self.assertEqual(source_inventory["programs"][0]["inventory_status"], "found")
            self.assertFalse(source_inventory["programs"][0]["targeted_scan_allowed"])

    def test_root_wrapper_prepares_nested_bundle_and_reserves_review_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            delivery_root = temp_root / "delivery-main"
            output_dir = temp_root / "review-output"
            programs_file = temp_root / "programs.txt"
            write_compact_artifacts(
                delivery_root / "modules" / "CAP-ID-0001-large_extreme_program" / "@CU118"
            )
            programs_file.write_text("@CU118\nCU257F\n", encoding="utf-8")

            build_result = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_WRAPPER),
                    "--review-name",
                    "Card Auth Posting Core Review",
                    "--programs-file",
                    str(programs_file),
                    "--working-root",
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

            match = re.search(r"^OUTPUT_DIR=(.+)$", build_result.stdout, re.M)
            self.assertIsNotNone(match, build_result.stdout)
            bundle = Path(match.group(1))
            manifest_path = bundle / "program-set-core-input-manifest.yaml"
            manifest = BUILDER.load_yaml(manifest_path)
            review_path = bundle / manifest["canonical_filename"]
            self.assertFalse(review_path.exists())
            self.assertFalse((output_dir / "program-set-core-input-manifest.yaml").exists())

            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATE_WRAPPER),
                    "--manifest",
                    str(manifest_path),
                    "--review",
                    str(review_path),
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing review artifact", result.stderr)

    def test_build_wrapper_rejects_missing_working_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            output_dir = temp_root / "review-output"
            programs_file = temp_root / "programs.txt"
            programs_file.write_text("CU257F\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_WRAPPER),
                    "--review-name",
                    "Card Auth Posting Core Review",
                    "--programs-file",
                    str(programs_file),
                    "--working-root",
                    str(temp_root / "missing-working-root"),
                    "--profile",
                    str(PROFILE_TEMPLATE),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("artifact root not found", result.stderr)

    def test_build_wrapper_rejects_deprecated_delivery_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            output_dir = temp_root / "review-output"
            programs_file = temp_root / "programs.txt"
            programs_file.write_text("CU257F\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_WRAPPER),
                    "--review-name",
                    "Card Auth Posting Core Review",
                    "--programs-file",
                    str(programs_file),
                    "--delivery-root",
                    str(temp_root / "delivery-main"),
                    "--profile",
                    str(PROFILE_TEMPLATE),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--delivery-root is no longer supported", result.stderr)

    def test_build_wrapper_rejects_deprecated_force_rescan_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            working_root = temp_root / "delivery-working"
            output_dir = temp_root / "review-output"
            programs_file = temp_root / "programs.txt"
            rescan_file = temp_root / "rescan.txt"
            working_root.mkdir()
            programs_file.write_text("CU257F\n", encoding="utf-8")
            rescan_file.write_text("CU257F\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_WRAPPER),
                    "--review-name",
                    "Card Auth Posting Core Review",
                    "--programs-file",
                    str(programs_file),
                    "--working-root",
                    str(working_root),
                    "--force-rescan-file",
                    str(rescan_file),
                    "--profile",
                    str(PROFILE_TEMPLATE),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--force-rescan-file is no longer supported", result.stderr)


if __name__ == "__main__":
    unittest.main()
