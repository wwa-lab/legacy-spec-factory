from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tests.fixtures.program_analysis_artifacts import (
    write_finalized_program_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)
PROFILE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)


def load_merger():
    spec = importlib.util.spec_from_file_location("reader_first_coverage_merger", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load merger: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MERGER = load_merger()


def require_public_seam(name: str):
    seam = getattr(MERGER, name, None)
    if not callable(seam):
        raise AssertionError(f"program-set merger is missing public seam {name}()")
    return seam


def reconcile_counts(payload: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "total": len(items),
        "included": sum(item.get("status") == "included" for item in items),
        "merged": sum(item.get("status") == "merged" for item in items),
        "excluded_non_core": sum(
            item.get("status") == "excluded_non_core" for item in items
        ),
        "pending": sum(item.get("status") == "pending" for item in items),
    }
    result = {**payload, "items": items}
    if "coverage_items" in result:
        result["coverage_items"] = items
    for summary_key in ("summary", "counts", "coverage_summary"):
        summary = result.get(summary_key)
        if not isinstance(summary, dict):
            continue
        updated = dict(summary)
        for key in updated:
            normalized = key.lower()
            if "excluded" in normalized:
                updated[key] = counts["excluded_non_core"]
            elif "included" in normalized:
                updated[key] = counts["included"]
            elif "merged" in normalized:
                updated[key] = counts["merged"]
            elif "pending" in normalized:
                updated[key] = counts["pending"]
            elif "total" in normalized:
                updated[key] = counts["total"]
        result[summary_key] = updated
    return result


def completed_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    items = [
        {
            **item,
            "status": "included",
            "review_anchor": f"review-row-{index:03d}",
            "merged_source_fact_ids": [],
            "exclusion_reason": None,
        }
        for index, item in enumerate(payload["items"], start=1)
    ]
    result = reconcile_counts(payload, items)
    for key in ("status", "coverage_status", "merge_coverage_status"):
        if key in result:
            result[key] = "complete"
    result["review_status"] = "complete_exploratory"
    result["coverage_counts"] = {
        **result.get("coverage_counts", {}),
        "total_source_facts": len(items),
        "accounted_source_facts": len(items),
        "pending_source_facts": 0,
    }
    result["expected_source_fact_count"] = len(items)
    result["coverage_item_count"] = len(items)
    result["status_counts"] = {
        "included": len(items),
        "merged": 0,
        "excluded_non_core": 0,
        "pending": 0,
    }
    return result


def render_review(
    manifest: dict[str, Any], coverage: dict[str, Any], facts: dict[str, Any]
) -> str:
    items = coverage["items"]
    fact_map = {
        str(fact["source_fact_id"]): fact for fact in facts.get("source_facts", [])
    }

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

    def fact_detail(fact: dict[str, Any]) -> str:
        values = [
            str(fact.get("logic") or "").strip(),
            str(fact.get("exact_value") or "").strip(),
            *(
                value
                for _field, value in MERGER._required_fact_semantics(fact)
            ),
        ]
        return "; ".join(dict.fromkeys(value for value in values if value))

    def fact_row(
        item: dict[str, Any], fact: dict[str, Any], headers: tuple[str, ...]
    ) -> str:
        detail = fact_detail(fact)
        program = str(fact.get("program") or "source program")
        routine = str(fact.get("routine") or "program-wide reader-first context")
        status = str(fact.get("evidence_status") or "source_backed")
        exact = str(fact.get("exact_value") or "")
        values = {
            "Scope / Reader-First Contribution": detail,
            "Artifact Readiness": "ready",
            "Coverage": "included",
            "Calculation / Assignment": str(fact.get("calculation") or detail),
            "Target Field / Carrier": str(
                fact.get("target_carrier") or exact or detail
            ),
            "Source Operands / Carriers": str(fact.get("source_carriers") or detail),
            "Guard / Branch": str(fact.get("guard") or detail),
            "Message / Status / Outcome": exact or detail,
            "Description": str(fact.get("description") or detail),
            "Condition / Evidence": str(
                fact.get("trigger_chain") or fact.get("guard") or detail
            ),
            "Carrier / Destination": str(
                fact.get("carrier_destination") or fact.get("target_carrier") or detail
            ),
            "Exception / Error Path": str(fact.get("exception_path") or detail),
            "Detection Mechanism": str(fact.get("detection_mechanism") or detail),
            "Fields / Messages Set": str(fact.get("fields_messages_set") or exact or detail),
            "Handling Action": str(fact.get("exception_action") or detail),
            "Message / Status / Literal": exact or detail,
            "Type": str(fact.get("message_type") or fact.get("fact_type") or detail),
            "Program / Routine Sources": f"{program} {routine}",
            "Occurrences": str(fact.get("occurrences") or "source-backed occurrence"),
            "Condition / Handler": str(fact.get("trigger_handler") or detail),
            "Effect": str(fact.get("effect") or detail),
            "Detail Refs": detail,
            "Supporting Detail": detail,
            "Program": program,
            "Routine": routine,
            "Evidence Status": status,
            "Review Row ID": (
                f'<a id="{item["review_anchor"]}"></a> {item["review_anchor"]}'
            ),
            "Source Fact Refs": str(item["source_fact_id"]),
        }
        cells = [re.sub(r"\s+", " ", values[header]).strip() for header in headers]
        return "| " + " | ".join(cells) + " |"

    def fact_table(section: str) -> str:
        source_section = {
            "Program Set Reading Summary": "Program Reading Summary",
            "Message Coverage Control": "Message Inventory",
        }.get(section, section)
        header_key = (
            "Message Inventory" if section == "Message Coverage Control" else section
        )
        headers = section_headers[header_key]
        rows = [
            fact_row(item, fact_map[str(item["source_fact_id"])], headers)
            for item in items
            if item.get("section") == source_section
        ]
        header = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        return "\n".join((header, separator, *rows))

    refs = "; ".join(str(item["source_fact_id"]) for item in items)
    programs = list(
        dict.fromkeys(str(entry["normalized_name"]) for entry in manifest["programs"])
    )
    program_label = ", ".join(programs)
    front_programs = ", ".join(programs)
    folder_slug = str(manifest["folder_slug"])
    document_id = str(manifest.get("document_id") or manifest["review_id"])
    include_message_inventory = bool(
        manifest["core_review_profile"].get("include_message_inventory")
    )
    message_heading = (
        "Message Inventory"
        if include_message_inventory
        else "Message Coverage Control"
    )
    message_block = f"""## {message_heading}

{fact_table(message_heading)}
"""
    primary_message_block = message_block if include_message_inventory else ""
    control_message_block = "" if include_message_inventory else message_block
    return f"""---
document_id: {document_id}
flow_slug: {manifest['flow_slug']}
program_set_slug: {manifest['program_set_slug']}
programs: [{front_programs}]
review_status: complete_exploratory
artifact_version: '0.4'
---

# Program Set SME Core Review: {folder_slug}

## Program Set Reading Summary

This complete reader-first review covers {program_label} and preserves every material
calculation, validation, exception, exact message/status, routine, carrier,
guard, evidence, and outcome contributions. Inputs were ready_for_synthesis;
coverage reconciliation is complete and the result is suitable for SME review.

{fact_table("Program Set Reading Summary")}

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
| Program scope | {program_label} MAIN | Each requested program contributes source-backed request and response behavior. | <a id="review-overview-scope"></a> review-overview-scope | {refs} |
| Calculation | {program_label} main routines | Request and account carriers determine the approved response amount. | <a id="review-overview-calculation"></a> review-overview-calculation | {refs} |
| Validation | {program_label} main routines | Eligibility guards set exact response status values on the response carrier. | <a id="review-overview-validation"></a> review-overview-validation | {refs} |
| Exception / message | {program_label} main routines | Lookup failure sets the exact NF status and suppresses persistence. | <a id="review-overview-exception"></a> review-overview-exception | {refs} |

## Calculation Logic

{fact_table("Calculation Logic")}

## Validation Logic

{fact_table("Validation Logic")}

## Exception Handling

{fact_table("Exception Handling")}

{primary_message_block}

## Core Completeness Ledger

{MERGER.render_completeness_table(manifest['programs'])}

## Coverage Reconciliation

All normalized source facts are included at the stable anchors declared above.

{control_message_block}

## Sources

{MERGER.render_sources_table(manifest['programs'])}

## Run Profile

{MERGER.render_run_profile(manifest)}

## Source Inventory Cache

{MERGER.render_source_inventory(manifest)}
"""


class ProgramSetReaderFirstCoverageTests(unittest.TestCase):
    def build_valid_bundle(
        self,
        root: Path,
        profile: str | None = None,
        programs: tuple[str, ...] = ("CU106",),
        artifact_repo_mode: str = "current_run",
    ):
        artifact_root = root / "artifacts"
        for program in programs:
            write_finalized_program_artifacts(
                artifact_root / "modules" / "normal" / program,
                program,
                routines=("MAIN",),
            )
        programs_file = root / "requested-programs.txt"
        programs_file.write_text("\n".join(programs) + "\n", encoding="utf-8")
        manifest = MERGER.build_manifest(
            review_name="Coverage Reconciliation",
            programs=list(programs),
            artifact_root=artifact_root,
            config=MERGER.load_yaml(PROFILE),
            working_branch="fixture",
            flow_slug="coverage-reconciliation",
            core_review_profile=profile,
            artifact_repo_mode=artifact_repo_mode,
            programs_file=programs_file,
        )
        manifest = {
            **manifest,
            "review_status": "complete_exploratory",
            "artifact_readiness": "ready",
            "merge_coverage": "complete",
        }
        layout = require_public_seam("resolve_output_layout")(root / "outputs", manifest)
        layout.folder_dir.mkdir(parents=True)
        source_pack = require_public_seam("build_reader_first_source_pack")(
            manifest, artifact_root
        )
        facts = require_public_seam("build_core_facts")(manifest, artifact_root)
        coverage = completed_coverage(
            require_public_seam("build_core_coverage")(facts, manifest)
        )
        layout.program_list_path.write_text(
            "\n".join(programs) + "\n", encoding="utf-8"
        )
        layout.manifest_path.write_text(MERGER.dump_yaml(manifest), encoding="utf-8")
        layout.source_pack_path.write_text(source_pack, encoding="utf-8")
        layout.core_facts_path.write_text(MERGER.dump_yaml(facts), encoding="utf-8")
        layout.coverage_path.write_text(MERGER.dump_yaml(coverage), encoding="utf-8")
        layout.review_path.write_text(
            render_review(manifest, coverage, facts), encoding="utf-8"
        )
        return layout, manifest, facts, coverage

    def validate(self, layout) -> list[str]:
        return MERGER.validate(
            layout.manifest_path,
            layout.review_path,
            source_pack_path=layout.source_pack_path,
            core_facts_path=layout.core_facts_path,
            coverage_path=layout.coverage_path,
        )

    def assert_finding_words(self, findings: list[str], *words: str) -> None:
        serialized = "\n".join(findings).lower()
        self.assertTrue(
            all(word.lower() in serialized for word in words),
            findings,
        )

    def test_valid_bundle_passes_before_single_fault_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir)
            )
            self.assertEqual(self.validate(layout), [])

    def test_typed_fact_mapping_in_table_external_prose_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "calculation"
            )
            target_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == target_id
            )
            review = layout.review_path.read_text(encoding="utf-8")
            target_row = next(
                line
                for line in review.splitlines()
                if target_id in line and anchor in line and line.startswith("|")
            )
            external_prose = target_row.strip().strip("|").replace(" | ", "; ")
            review = review.replace(target_row + "\n", "", 1).replace(
                "\n## Validation Logic",
                f"\n{external_prose}\n\n## Validation Logic",
                1,
            )
            layout.review_path.write_text(review, encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, target_id, "visible", "required-header data row"
            )

    def test_visible_summary_prose_exception_passes_but_hidden_comment_does_not(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "summary_contribution"
            )
            target_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == target_id
            )
            original = layout.review_path.read_text(encoding="utf-8")
            target_row = next(
                line
                for line in original.splitlines()
                if target_id in line and anchor in line and line.startswith("|")
            )
            visible_prose = target_row.strip().strip("|").replace(" | ", "; ")
            visible_review = original.replace(target_row + "\n", "", 1).replace(
                "\n## Cross-Program Processing Overview",
                f"\n{visible_prose}\n\n## Cross-Program Processing Overview",
                1,
            )
            layout.review_path.write_text(visible_review, encoding="utf-8")
            self.assertEqual(self.validate(layout), [])

            hidden_review = visible_review.replace(
                visible_prose, f"<!-- {visible_prose} -->", 1
            )
            layout.review_path.write_text(hidden_review, encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, target_id, "visible", "anchored prose"
            )

    def test_summary_mapping_must_name_its_source_program_in_program_cell_or_prose(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(
                Path(temp_dir), programs=("CU106", "CU101A")
            )
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "summary_contribution"
                and fact.get("program") == "CU106"
            )
            target_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == target_id
            )
            review = layout.review_path.read_text(encoding="utf-8")
            target_row = next(
                line
                for line in review.splitlines()
                if target_id in line and anchor in line and line.startswith("|")
            )
            cells = [cell.strip() for cell in target_row.strip("|").split("|")]
            cells[0] = "CU101A"
            wrong_row = "| " + " | ".join(cells) + " |"
            layout.review_path.write_text(
                review.replace(target_row, wrong_row, 1), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, target_id, "program", "CU106")

            prose = (
                "CU101A provides detailed validation context and response outcomes "
                f"for SME review. <a id=\"{anchor}\"></a> {target_id}"
            )
            layout.review_path.write_text(
                review.replace(target_row + "\n", "", 1).replace(
                    "\n## Cross-Program Processing Overview",
                    f"\n{prose}\n\n## Cross-Program Processing Overview",
                    1,
                ),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, target_id, "program", "CU106")

    def test_typed_semantics_must_remain_in_their_destination_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "calculation"
                and fact.get("target_carrier")
            )
            target_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == target_id
            )
            review = layout.review_path.read_text(encoding="utf-8")
            target_row = next(
                line
                for line in review.splitlines()
                if target_id in line and anchor in line and line.startswith("|")
            )
            cells = [cell.strip() for cell in target_row.strip("|").split("|")]
            self.assertIn(str(target["target_carrier"]), cells[3])
            self.assertIn(str(target["target_carrier"]), cells[7])
            cells[3] = "WRONG_TARGET"
            wrong_row = "| " + " | ".join(cells) + " |"
            layout.review_path.write_text(
                review.replace(target_row, wrong_row, 1), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings,
                target_id,
                "target_carrier",
                "Target Field / Carrier",
            )

    def test_merged_anchor_group_rejects_declared_fact_outside_the_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            calculation_facts = [
                fact
                for fact in facts["source_facts"]
                if fact.get("section") == "Calculation Logic"
            ]
            first, second, outside = calculation_facts[:3]
            first_id = str(first["source_fact_id"])
            second_id = str(second["source_fact_id"])
            outside_id = str(outside["source_fact_id"])
            items = [copy.deepcopy(item) for item in coverage["items"]]
            first_item = next(item for item in items if item["source_fact_id"] == first_id)
            second_item = next(item for item in items if item["source_fact_id"] == second_id)
            shared_anchor = str(first_item["review_anchor"])
            second_anchor = str(second_item["review_anchor"])
            first_item.update(
                status="merged",
                merged_source_fact_ids=[second_id, outside_id],
            )
            second_item.update(
                status="merged",
                review_anchor=shared_anchor,
                merged_source_fact_ids=[first_id, outside_id],
            )
            broken = {
                **coverage,
                "items": items,
                "coverage_items": [copy.deepcopy(item) for item in items],
                "status_counts": {
                    "included": len(items) - 2,
                    "merged": 2,
                    "excluded_non_core": 0,
                    "pending": 0,
                },
            }
            layout.coverage_path.write_text(MERGER.dump_yaml(broken), encoding="utf-8")

            review_lines = layout.review_path.read_text(encoding="utf-8").splitlines()
            first_row = next(
                line for line in review_lines if first_id in line and shared_anchor in line
            )
            second_row = next(
                line for line in review_lines if second_id in line and second_anchor in line
            )
            second_detail = "; ".join(
                dict.fromkeys(
                    value
                    for value in (
                        str(second.get("logic") or ""),
                        str(second.get("exact_value") or ""),
                        *(
                            semantic
                            for _field, semantic in MERGER._required_fact_semantics(
                                second
                            )
                        ),
                    )
                    if value
                )
            )
            merged_row = first_row.replace(
                f' | <a id="{shared_anchor}"',
                f"; {second_detail} | <a id=\"{shared_anchor}\"",
                1,
            ).replace(
                f"| {first_id} |",
                f"| {first_id}; {second_id}; {outside_id} |",
                1,
            )
            layout.review_path.write_text(
                "\n".join(
                    merged_row
                    if line == first_row
                    else line
                    for line in review_lines
                    if line != second_row
                )
                + "\n",
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, shared_anchor, "merged group", "exactly"
            )

    def test_merged_fact_requires_peer_status_and_same_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            calculation_facts = [
                fact
                for fact in facts["source_facts"]
                if fact.get("section") == "Calculation Logic"
            ]
            first_id = str(calculation_facts[0]["source_fact_id"])
            second_id = str(calculation_facts[1]["source_fact_id"])
            items = [copy.deepcopy(item) for item in coverage["items"]]
            first_item = next(item for item in items if item["source_fact_id"] == first_id)
            first_item.update(status="merged", merged_source_fact_ids=[second_id])
            broken = reconcile_counts(coverage, items)
            broken["coverage_items"] = [copy.deepcopy(item) for item in items]
            layout.coverage_path.write_text(
                MERGER.dump_yaml(broken), encoding="utf-8"
            )
            review = layout.review_path.read_text(encoding="utf-8")
            first_row = next(
                line
                for line in review.splitlines()
                if first_id in line
                and str(first_item["review_anchor"]) in line
                and line.startswith("|")
            )
            layout.review_path.write_text(
                review.replace(f"| {first_id} |", f"| {first_id}; {second_id} |", 1),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, first_id, second_id, "merged", "same review anchor"
            )

    def test_merged_coverage_rejects_self_duplicate_and_nonmerged_declarations(
        self,
    ) -> None:
        cases = (
            ("merged", lambda fact_id: [fact_id], ("self", "merge")),
            ("merged", lambda fact_id: [fact_id, fact_id], ("duplicate", "merged")),
            ("pending", lambda fact_id: [fact_id], ("non-merged", "merged_source_fact_ids")),
            (
                "excluded_non_core",
                lambda fact_id: [fact_id],
                ("non-merged", "merged_source_fact_ids"),
            ),
        )
        for status, merged_ids, expected_words in cases:
            with self.subTest(status=status, expected=expected_words), tempfile.TemporaryDirectory() as temp_dir:
                layout, _manifest, _facts, coverage = self.build_valid_bundle(
                    Path(temp_dir)
                )
                items = [copy.deepcopy(item) for item in coverage["items"]]
                target = items[0]
                fact_id = str(target["source_fact_id"])
                target.update(
                    status=status,
                    merged_source_fact_ids=merged_ids(fact_id),
                    exclusion_reason=(
                        "non-core fixture" if status == "excluded_non_core" else None
                    ),
                )
                broken = reconcile_counts(coverage, items)
                broken["coverage_items"] = [copy.deepcopy(item) for item in items]
                broken["status_counts"] = {
                    "included": sum(item["status"] == "included" for item in items),
                    "merged": sum(item["status"] == "merged" for item in items),
                    "excluded_non_core": sum(
                        item["status"] == "excluded_non_core" for item in items
                    ),
                    "pending": sum(item["status"] == "pending" for item in items),
                }
                layout.coverage_path.write_text(
                    MERGER.dump_yaml(broken), encoding="utf-8"
                )

                findings = self.validate(layout)

                self.assert_finding_words(findings, fact_id, *expected_words)

    def test_approved_document_repo_bundle_passes_final_rereadiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir), artifact_repo_mode="approved_document_repo"
            )

            self.assertEqual(
                manifest["programs"][0]["run_resolution"],
                "reused_artifact_repo",
            )
            self.assertEqual(self.validate(layout), [])

    def test_final_validation_rejects_replaced_manifest_program_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir)
            )
            replaced = copy.deepcopy(manifest)
            replaced["programs"][0]["artifact_root"] = "modules/replaced/CU106"
            replaced["programs"][0]["candidate_artifact_root"] = (
                "modules/replaced/CU106"
            )
            layout.manifest_path.write_text(
                MERGER.dump_yaml(replaced), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, "readiness", "replaced")

    def test_final_validation_rejects_compact_artifact_symlink_outside_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(root)
            summary_path = (
                root
                / "artifacts"
                / "modules"
                / "normal"
                / "CU106"
                / "CU106-program-analysis-summary.yaml"
            )
            outside_path = root / "outside-program-analysis-summary.yaml"
            summary_path.replace(outside_path)
            summary_path.symlink_to(outside_path)

            findings = self.validate(layout)

            self.assert_finding_words(
                findings,
                "readiness",
                "escapes",
                "program artifact directory",
            )

    def test_final_validation_rejects_manifest_schema_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir)
            )
            layout.manifest_path.write_text(
                MERGER.dump_yaml({**manifest, "schema_version": "0.3"}),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, "schema_version", "0.4")

    def test_final_validation_rejects_manifest_version_metadata_downgrade(self) -> None:
        for key, value in (
            ("generator_version", "0.1.0"),
            ("template_version", "0.1.0"),
            ("artifact_version", "0.1"),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp_dir:
                layout, manifest, _facts, _coverage = self.build_valid_bundle(
                    Path(temp_dir)
                )
                layout.manifest_path.write_text(
                    MERGER.dump_yaml({**manifest, key: value}), encoding="utf-8"
                )

                findings = self.validate(layout)

                self.assert_finding_words(findings, key, "must be")

    def test_final_review_h1_identity_must_be_visibly_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, manifest, _facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            original = layout.review_path.read_text(encoding="utf-8")
            original_h1 = next(
                line for line in original.splitlines() if line.startswith("# ")
            )
            folder_slug = str(manifest["folder_slug"])
            for fake_h1 in (
                f"# Review <!-- {folder_slug} -->",
                f'# Review <span data-id="{folder_slug}"></span>',
                f"# [Review]({folder_slug})",
            ):
                with self.subTest(fake_h1=fake_h1):
                    layout.review_path.write_text(
                        original.replace(original_h1, fake_h1, 1), encoding="utf-8"
                    )
                    findings = self.validate(layout)
                    self.assert_finding_words(
                        findings, "H1", "flow/program-set", "identity"
                    )

    def test_final_validation_rejects_bundle_outside_folder_slug_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            wrong_bundle = layout.folder_dir.parent / "wrong-bundle-name"
            layout.folder_dir.rename(wrong_bundle)

            findings = MERGER.validate(
                wrong_bundle / MERGER.MANIFEST_FILENAME,
                wrong_bundle / layout.review_path.name,
                source_pack_path=wrong_bundle / MERGER.SOURCE_PACK_FILENAME,
                core_facts_path=wrong_bundle / MERGER.CORE_FACTS_FILENAME,
                coverage_path=wrong_bundle / MERGER.CORE_COVERAGE_FILENAME,
            )

            self.assert_finding_words(
                findings, "parent directory", "folder_slug"
            )

    def test_final_validation_rejects_facts_or_coverage_schema_downgrade(self) -> None:
        for artifact_name in ("facts", "coverage"):
            with self.subTest(artifact=artifact_name), tempfile.TemporaryDirectory() as temp_dir:
                layout, _manifest, facts, coverage = self.build_valid_bundle(
                    Path(temp_dir)
                )
                if artifact_name == "facts":
                    layout.core_facts_path.write_text(
                        MERGER.dump_yaml({**facts, "schema_version": "0.3"}),
                        encoding="utf-8",
                    )
                else:
                    layout.coverage_path.write_text(
                        MERGER.dump_yaml({**coverage, "schema_version": "0.3"}),
                        encoding="utf-8",
                    )

                findings = self.validate(layout)

                self.assert_finding_words(
                    findings, artifact_name, "schema_version", "0.4"
                )

    def test_minimal_profile_keeps_message_facts_in_coverage_control(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir), "minimal_reader_first"
            )
            review = layout.review_path.read_text(encoding="utf-8")
            self.assertIn("## Message Coverage Control", review)
            self.assertNotIn("## Message Inventory", review)
            self.assertEqual(self.validate(layout), [])

    def test_cu106_and_cu101a_every_source_fact_is_accounted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(
                Path(temp_dir), programs=("CU106", "CU101A")
            )
            self.assertEqual(
                {fact["program"] for fact in facts["source_facts"]},
                {"CU106", "CU101A"},
            )
            self.assertEqual(
                {item["status"] for item in coverage["items"]}, {"included"}
            )
            self.assertEqual(self.validate(layout), [])

    def test_missing_source_fact_coverage_item_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            missing_id = coverage["items"][0]["source_fact_id"]
            broken = reconcile_counts(coverage, coverage["items"][1:])
            layout.coverage_path.write_text(MERGER.dump_yaml(broken), encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(findings, "coverage", str(missing_id))

    def test_coverage_item_dimensions_must_match_normalized_source_fact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            items = [copy.deepcopy(item) for item in coverage["items"]]
            target_id = str(items[0]["source_fact_id"])
            items[0].update(
                program="WRONG",
                section="Wrong Section",
                fact_type="wrong",
            )
            broken = {
                **coverage,
                "items": items,
                "coverage_items": [copy.deepcopy(item) for item in items],
            }
            layout.coverage_path.write_text(
                MERGER.dump_yaml(broken), encoding="utf-8"
            )

            findings = self.validate(layout)

            for dimension in ("program", "section", "fact_type"):
                self.assert_finding_words(findings, target_id, dimension, "differs")

    def test_source_fact_deleted_only_from_final_review_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            missing_id = str(coverage["items"][0]["source_fact_id"])
            review_lines = layout.review_path.read_text(encoding="utf-8").splitlines()
            layout.review_path.write_text(
                "\n".join(line for line in review_lines if missing_id not in line) + "\n",
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, missing_id, "anchor")

    def test_extra_canonical_fact_row_with_unknown_source_ref_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir)
            )
            review = layout.review_path.read_text(encoding="utf-8")
            invented_row = (
                "| Always set INTERNAL-FLAG to X9 | CU106 | MAIN | INTERNAL-FLAG | "
                "AMOUNT | amount is positive | return X9 | invented detail | confirmed | "
                '<a id="review-invented"></a> review-invented | SF-FAKE |'
            )
            layout.review_path.write_text(
                review.replace(
                    "\n## Validation Logic",
                    f"\n{invented_row}\n\n## Validation Logic",
                    1,
                ),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, "Calculation Logic", "unknown", "SF-FAKE"
            )

    def test_unreferenced_deterministic_core_prose_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir)
            )
            review = layout.review_path.read_text(encoding="utf-8")
            invented = (
                "CU106 always sets INTERNAL-FLAG to X9 whenever amount is positive; "
                "this deterministic rule is confirmed."
            )
            layout.review_path.write_text(
                review.replace(
                    "\n## Validation Logic",
                    f"\n{invented}\n\n## Validation Logic",
                    1,
                ),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, "Calculation Logic", "prose", "canonical", "table"
            )

    def test_blockquoted_deterministic_core_prose_is_rejected(self) -> None:
        findings = MERGER._unmapped_core_prose_findings(
            "## Calculation Logic\n\n"
            "> **Observed:** CU106 always sets SECRET_FLAG to X9.\n",
            {
                "programs": [{"normalized_name": "CU106"}],
                "core_review_profile": {"include_message_inventory": True},
            },
        )

        self.assert_finding_words(
            findings, "Calculation Logic", "prose", "canonical", "table"
        )

    def test_summary_mapping_must_retain_material_source_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "summary_contribution"
            )
            fact_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == fact_id
            )
            review = layout.review_path.read_text(encoding="utf-8")
            target_row = next(
                line
                for line in review.splitlines()
                if line.startswith("|") and fact_id in line and anchor in line
            )
            cells = MERGER._split_markdown_table_row_v04(target_row)
            cells[1] = (
                "Generic reader-facing overview confirms local context and "
                "available evidence."
            )
            generic_row = "| " + " | ".join(cell.strip() for cell in cells) + " |"
            layout.review_path.write_text(
                review.replace(target_row, generic_row, 1), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, fact_id, "source", "summary", "semantics"
            )

    def test_summary_mapping_allows_material_nonverbatim_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "summary_contribution"
            )
            fact_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == fact_id
            )
            review = layout.review_path.read_text(encoding="utf-8")
            target_row = next(
                line
                for line in review.splitlines()
                if line.startswith("|") and fact_id in line and anchor in line
            )
            cells = MERGER._split_markdown_table_row_v04(target_row)
            cells[1] = (
                "For CU106, SME navigation follows request calculation, validation, "
                "exception, and response outcomes without copying the source wording."
            )
            synthesized_row = "| " + " | ".join(
                cell.strip() for cell in cells
            ) + " |"
            layout.review_path.write_text(
                review.replace(target_row, synthesized_row, 1), encoding="utf-8"
            )

            self.assertEqual(self.validate(layout), [])

    def test_nested_program_fact_mirror_must_equal_canonical_source_fact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            broken = copy.deepcopy(facts)
            bucket = next(
                values
                for values in broken["programs"][0]["facts"].values()
                if values
            )
            nested = bucket[0]
            target_id = str(nested["source_fact_id"])
            bucket[0] = {**nested, "program": "WRONG"}
            layout.core_facts_path.write_text(
                MERGER.dump_yaml(broken), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, "nested fact", target_id, "differs", "source_facts"
            )

    def test_missing_exact_message_or_status_literal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            review = layout.review_path.read_text(encoding="utf-8")
            layout.review_path.write_text(review.replace("NF", "TOKEN-REMOVED"), encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(findings, "NF", "message")

    def test_coverage_item_pointing_to_missing_review_anchor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            items = [dict(item) for item in coverage["items"]]
            items[0]["review_anchor"] = "review-anchor-does-not-exist"
            broken = reconcile_counts(coverage, items)
            layout.coverage_path.write_text(MERGER.dump_yaml(broken), encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(findings, "anchor", "does-not-exist")

    def test_source_pack_fact_cannot_be_deleted_from_all_downstream_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "calculation"
            )
            target_id = str(target["source_fact_id"])
            remaining_facts = [
                fact for fact in facts["source_facts"] if fact is not target
            ]
            broken_facts = {**facts, "source_facts": remaining_facts}
            for entry in broken_facts["programs"]:
                entry["source_fact_ids"] = [
                    value
                    for value in entry.get("source_fact_ids", [])
                    if value != target_id
                ]
                for bucket, values in entry.get("facts", {}).items():
                    entry["facts"][bucket] = [
                        fact
                        for fact in values
                        if fact.get("source_fact_id") != target_id
                    ]
            remaining_items = [
                item
                for item in coverage["items"]
                if item.get("source_fact_id") != target_id
            ]
            by_program: dict[str, int] = {}
            by_section: dict[str, int] = {}
            routine_rlog: dict[str, int] = {}
            for fact in remaining_facts:
                program = str(fact["program"])
                section = str(fact["section"])
                by_program[program] = by_program.get(program, 0) + 1
                by_section[section] = by_section.get(section, 0) + 1
                if fact.get("fact_type") == "routine":
                    routine_rlog[program] = routine_rlog.get(program, 0) + 1
            broken_coverage = {
                **coverage,
                "items": remaining_items,
                "coverage_items": [dict(item) for item in remaining_items],
                "expected_source_fact_count": len(remaining_facts),
                "coverage_item_count": len(remaining_items),
                "status_counts": {
                    "included": len(remaining_items),
                    "merged": 0,
                    "excluded_non_core": 0,
                    "pending": 0,
                },
                "coverage_counts": {
                    "total_source_facts": len(remaining_facts),
                    "accounted_source_facts": len(remaining_items),
                    "pending_source_facts": 0,
                    "by_program": by_program,
                    "by_section": by_section,
                    "routine_rlog": routine_rlog,
                },
            }
            layout.core_facts_path.write_text(
                MERGER.dump_yaml(broken_facts), encoding="utf-8"
            )
            layout.coverage_path.write_text(
                MERGER.dump_yaml(broken_coverage), encoding="utf-8"
            )
            review = layout.review_path.read_text(encoding="utf-8")
            layout.review_path.write_text(
                "\n".join(
                    line.replace(target_id, "")
                    for line in review.splitlines()
                    if not (
                        target_id in line
                        and line.lstrip().startswith('<a id="review-row-')
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, "source-pack fact", target_id)

    def test_material_row_cannot_be_deleted_from_source_pack_and_all_downstream_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "calculation"
            )
            target_id = str(target["source_fact_id"])
            target_logic = str(target["calculation"])
            target_item = next(
                item
                for item in coverage["items"]
                if item.get("source_fact_id") == target_id
            )

            source_pack = layout.source_pack_path.read_text(encoding="utf-8")
            self.assertIn(target_logic, source_pack)
            layout.source_pack_path.write_text(
                "\n".join(
                    line
                    for line in source_pack.splitlines()
                    if target_logic not in line
                )
                + "\n",
                encoding="utf-8",
            )

            broken_facts = copy.deepcopy(facts)
            broken_facts["source_facts"] = [
                fact
                for fact in broken_facts["source_facts"]
                if fact.get("source_fact_id") != target_id
            ]
            for entry in broken_facts["programs"]:
                entry["source_fact_ids"] = [
                    value
                    for value in entry.get("source_fact_ids", [])
                    if value != target_id
                ]
                for bucket, values in entry.get("facts", {}).items():
                    entry["facts"][bucket] = [
                        fact
                        for fact in values
                        if fact.get("source_fact_id") != target_id
                    ]

            remaining_items = [
                item
                for item in coverage["items"]
                if item.get("source_fact_id") != target_id
            ]
            by_program: dict[str, int] = {}
            by_section: dict[str, int] = {}
            routine_rlog: dict[str, int] = {}
            for fact in broken_facts["source_facts"]:
                program = str(fact["program"])
                section = str(fact["section"])
                by_program[program] = by_program.get(program, 0) + 1
                by_section[section] = by_section.get(section, 0) + 1
                if fact.get("fact_type") == "routine":
                    routine_rlog[program] = routine_rlog.get(program, 0) + 1
            broken_coverage = {
                **coverage,
                "items": remaining_items,
                "coverage_items": [dict(item) for item in remaining_items],
                "expected_source_fact_count": len(broken_facts["source_facts"]),
                "coverage_item_count": len(remaining_items),
                "status_counts": {
                    "included": len(remaining_items),
                    "merged": 0,
                    "excluded_non_core": 0,
                    "pending": 0,
                },
                "coverage_counts": {
                    "total_source_facts": len(broken_facts["source_facts"]),
                    "accounted_source_facts": len(remaining_items),
                    "pending_source_facts": 0,
                    "by_program": by_program,
                    "by_section": by_section,
                    "routine_rlog": routine_rlog,
                },
            }

            layout.core_facts_path.write_text(
                MERGER.dump_yaml(broken_facts), encoding="utf-8"
            )
            layout.coverage_path.write_text(
                MERGER.dump_yaml(broken_coverage), encoding="utf-8"
            )
            review = layout.review_path.read_text(encoding="utf-8")
            target_anchor = str(target_item["review_anchor"])
            review = "\n".join(
                line
                for line in review.splitlines()
                if target_anchor not in line
            ).replace(target_id, "")
            layout.review_path.write_text(review + "\n", encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(
                findings,
                "source pack",
                "current validated program-analysis inputs",
            )

    def test_final_validation_reruns_readiness_after_upstream_status_regresses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(root)
            summary_path = (
                root
                / "artifacts"
                / "modules"
                / "normal"
                / "CU106"
                / "CU106-program-analysis-summary.yaml"
            )
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary_path.write_text(
                json.dumps(
                    {**summary, "analysis_status": "pending_deep_read"},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, "readiness", "pending_deep_read")

    def test_material_theme_table_row_is_normalized_and_cannot_be_deleted_from_source_pack(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            theme_facts = [
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "thematic_table"
                and fact.get("section") == "Calculation Logic"
                and fact.get("source_row", {}).get("Theme") == "Response derivation"
            ]

            self.assertEqual(len(theme_facts), 1, facts["source_facts"])
            target = theme_facts[0]
            self.assertEqual(target["logic"], "Response derivation")
            self.assertEqual(target["source_row"]["Routine Count"], "1")
            self.assertEqual(target["source_row"]["Routines"], "MAIN")
            self.assertIn(
                "Follow request carriers through guarded assignments",
                target["source_row"]["Reader Cue"],
            )
            self.assertIn("Theme=Response derivation", target["source_text"])
            self.assertEqual(target["evidence_status"], "source_backed")
            self.assertTrue(target["evidence_reference"])
            self.assertTrue(target["source_artifact"])

            repeated = require_public_seam("build_core_facts")(
                _manifest, Path(_manifest["run_profile"]["artifact_root"])
            )
            repeated_ids = {
                fact["source_fact_id"]
                for fact in repeated["source_facts"]
                if fact.get("fact_type") == "thematic_table"
            }
            self.assertIn(target["source_fact_id"], repeated_ids)

            thematic_rows = [
                fact.get("source_row", {})
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "thematic_table"
            ]
            self.assertFalse(
                any("Calculation / Assignment" in row for row in thematic_rows)
            )
            self.assertFalse(any("RLOG / Routine" in row for row in thematic_rows))

            source_pack = layout.source_pack_path.read_text(encoding="utf-8")
            source_row = (
                "| Response derivation | 1 | MAIN | Follow request carriers through "
                "guarded assignments into the returned response. |"
            )
            self.assertIn(source_row, source_pack)
            layout.source_pack_path.write_text(
                source_pack.replace(source_row + "\n", "", 1), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings,
                "normalized core fact",
                str(target["source_fact_id"]),
                "not derivable",
            )

    def test_thematic_table_anchor_must_preserve_key_source_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "thematic_table"
                and fact.get("section") == "Calculation Logic"
                and fact.get("source_row", {}).get("Theme") == "Response derivation"
            )
            target_id = str(target["source_fact_id"])
            anchor = next(
                str(item["review_anchor"])
                for item in coverage["items"]
                if item["source_fact_id"] == target_id
            )
            reader_cue = str(target["source_row"]["Reader Cue"])
            lines = layout.review_path.read_text(encoding="utf-8").splitlines()
            matching_lines = [
                line for line in lines if anchor in line and target_id in line
            ]
            self.assertEqual(len(matching_lines), 1)
            self.assertIn(str(target["source_row"]["Theme"]), matching_lines[0])
            self.assertIn(str(target["source_row"]["Routines"]), matching_lines[0])
            self.assertIn(reader_cue, matching_lines[0])
            layout.review_path.write_text(
                "\n".join(
                    line.replace(reader_cue, "reader cue removed")
                    if anchor in line and target_id in line
                    else line
                    for line in lines
                )
                + "\n",
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, target_id, "source_row.reader cue", "missing source"
            )

    def test_calculation_and_exception_anchors_require_supporting_detail_as_well_as_evidence(
        self,
    ) -> None:
        for fact_type in ("calculation", "exception"):
            with self.subTest(fact_type=fact_type), tempfile.TemporaryDirectory() as temp_dir:
                layout, _manifest, facts, coverage = self.build_valid_bundle(
                    Path(temp_dir)
                )
                target = next(
                    fact
                    for fact in facts["source_facts"]
                    if fact.get("fact_type") == fact_type
                )
                target_id = str(target["source_fact_id"])
                supporting_detail = str(target.get("supporting_detail") or "")
                evidence_reference = str(target.get("evidence_reference") or "")
                self.assertIn(f"RLOG-{target['program']}-", supporting_detail)
                self.assertIn(f"EV-{target['program']}-", evidence_reference)
                self.assertNotEqual(supporting_detail, evidence_reference)
                anchor = next(
                    str(item["review_anchor"])
                    for item in coverage["items"]
                    if item["source_fact_id"] == target_id
                )
                lines = layout.review_path.read_text(encoding="utf-8").splitlines()
                matching_lines = [
                    line for line in lines if anchor in line and target_id in line
                ]
                self.assertEqual(len(matching_lines), 1)
                self.assertIn(supporting_detail, matching_lines[0])
                self.assertIn(evidence_reference, matching_lines[0])
                layout.review_path.write_text(
                    "\n".join(
                        line.replace(supporting_detail, "supporting detail removed")
                        if anchor in line and target_id in line
                        else line
                        for line in lines
                    )
                    + "\n",
                    encoding="utf-8",
                )

                findings = self.validate(layout)

                self.assert_finding_words(
                    findings, target_id, "supporting_detail", "missing source"
                )

    def test_exact_status_is_not_accepted_as_a_substring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "validation"
                and fact.get("exact_value") == "00"
            )
            review = layout.review_path.read_text(encoding="utf-8")
            layout.review_path.write_text(
                re.sub(r"(?<![A-Za-z0-9_])00(?![A-Za-z0-9_])", "100", review),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(
                findings, str(target["source_fact_id"]), "exact value 00"
            )

    def test_included_facts_cannot_share_or_redefine_an_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            items = [dict(item) for item in coverage["items"]]
            shared_anchor = str(items[0]["review_anchor"])
            old_anchor = str(items[1]["review_anchor"])
            items[1]["review_anchor"] = shared_anchor
            broken = {**coverage, "items": items, "coverage_items": [dict(item) for item in items]}
            layout.coverage_path.write_text(MERGER.dump_yaml(broken), encoding="utf-8")
            review = layout.review_path.read_text(encoding="utf-8")
            layout.review_path.write_text(
                review.replace(old_anchor, shared_anchor), encoding="utf-8"
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, shared_anchor, "exactly once")
            self.assert_finding_words(findings, shared_anchor, "non-merged")

    def test_material_row_must_preserve_guard_carrier_effect_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, facts, _coverage = self.build_valid_bundle(Path(temp_dir))
            target = next(
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "validation"
            )
            target_id = str(target["source_fact_id"])
            lines = layout.review_path.read_text(encoding="utf-8").splitlines()
            layout.review_path.write_text(
                "\n".join(
                    f'<a id="{next(item["review_anchor"] for item in _coverage["items"] if item["source_fact_id"] == target_id)}"></a> '
                    f"{target_id} 00 unconditional execution writes an unrelated audit sink and blocks every approved response."
                    if target_id in line and line.lstrip().startswith("|")
                    else line
                    for line in lines
                )
                + "\n",
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assert_finding_words(findings, target_id, "missing source")
            self.assertTrue(
                any(
                    any(field in finding for field in ("trigger_chain", "carrier_destination", "effect", "evidence"))
                    for finding in findings
                    if target_id in finding
                ),
                findings,
            )

    def test_overview_rejects_untracked_cross_program_call_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, _coverage = self.build_valid_bundle(
                Path(temp_dir), programs=("CU106", "CU101A")
            )
            review = layout.review_path.read_text(encoding="utf-8")
            layout.review_path.write_text(
                review.replace(
                    "\n## Calculation Logic",
                    "\nCU106 calls CU101A and control always executes in that order.\n\n## Calculation Logic",
                    1,
                ),
                encoding="utf-8",
            )

            findings = self.validate(layout)

            self.assertTrue(
                any("untracked call/sequence" in finding for finding in findings),
                findings,
            )

    def test_v04_coverage_requires_complete_status_and_identical_mirrors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            broken = {
                **coverage,
                "coverage_status": "pending",
                "items": coverage["items"][1:],
            }
            layout.coverage_path.write_text(MERGER.dump_yaml(broken), encoding="utf-8")

            findings = self.validate(layout)

            self.assert_finding_words(findings, "coverage_status", "complete")
            self.assert_finding_words(findings, "mirrors", "differ")

    def test_v04_coverage_requires_dimension_counts_and_allowed_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout, _manifest, _facts, coverage = self.build_valid_bundle(Path(temp_dir))
            counts = {
                key: value
                for key, value in coverage["coverage_counts"].items()
                if key not in {"by_program", "by_section", "routine_rlog"}
            }
            broken = {
                **coverage,
                "coverage_counts": counts,
                "allowed_statuses": ["included"],
            }
            layout.coverage_path.write_text(
                MERGER.dump_yaml(broken), encoding="utf-8"
            )

            findings = self.validate(layout)

            for dimension in ("by_program", "by_section", "routine_rlog"):
                self.assert_finding_words(findings, "missing", dimension)
            self.assert_finding_words(findings, "allowed_statuses", "v0.4")


if __name__ == "__main__":
    unittest.main()
