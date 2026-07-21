from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


REPO_ROOT = Path(__file__).resolve().parents[1]
FLOW_SCRIPT = (
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


def load_flow():
    spec = importlib.util.spec_from_file_location("core_coverage_flow", FLOW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load flow validator: {FLOW_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["core_coverage_flow"] = module
    spec.loader.exec_module(module)
    return module


FLOW = load_flow()


SOURCE_FACTS: tuple[dict[str, Any], ...] = (
    {
        "source_fact_id": "SF-CU106-CALC-001",
        "program": "CU106",
        "section": "Calculation Logic",
        "routine": "RLOG-CU106-001 / MAIN",
        "fact_type": "calculation",
        "material": True,
        "exact_value": "CU106_APPROVED_AMOUNT",
        "logic": "Derive the approved amount from request amount and account limit.",
        "target_carrier": "CU106_APPROVED_AMOUNT",
        "source_carriers": "REQUEST_AMOUNT, ACCOUNT_LIMIT",
        "guard": "request and account validation succeeded",
        "effect": "returns the approved amount in the response payload",
        "evidence": "EV-CU106-CALC-001",
        "evidence_status": "confirmed",
    },
    {
        "source_fact_id": "SF-CU106-VAL-001",
        "program": "CU106",
        "section": "Validation Logic",
        "routine": "RLOG-CU106-001 / MAIN",
        "fact_type": "validation",
        "material": True,
        "exact_value": "00",
        "logic": "Set exact response status 00 after eligibility validation.",
        "target_carrier": "RESPONSE_STATUS",
        "source_carriers": "REQUEST_STATUS, ACCOUNT_STATUS",
        "guard": "request is present and account status is active",
        "effect": "continues to the approved response handoff",
        "evidence": "EV-CU106-VAL-001",
        "evidence_status": "confirmed",
    },
    {
        "source_fact_id": "SF-CU106-EXC-001",
        "program": "CU106",
        "section": "Exception Handling",
        "routine": "RLOG-CU106-001 / MAIN",
        "fact_type": "exception",
        "material": True,
        "exact_value": "E1",
        "logic": "Close account lookup failure with status E1 and return.",
        "target_carrier": "RESPONSE_STATUS",
        "source_carriers": "%FOUND lookup result",
        "guard": "account lookup does not find the requested key",
        "effect": "suppresses persistence and returns the failure status",
        "evidence": "EV-CU106-EXC-001",
        "evidence_status": "confirmed",
    },
    {
        "source_fact_id": "SF-CU106-MSG-001",
        "program": "CU106",
        "section": "Message Inventory",
        "routine": "RLOG-CU106-001 / MAIN",
        "fact_type": "message",
        "material": True,
        "exact_value": "UCC1061",
        "logic": "Exact message UCC1061 reports that account eligibility failed.",
        "target_carrier": "RESPONSE_MESSAGE",
        "source_carriers": "message assignment literal",
        "guard": "account eligibility validation fails",
        "effect": "returns the exact operator-reviewable message to the caller",
        "evidence": "MSG-CU106-001",
        "evidence_status": "confirmed",
    },
)


ANCHORS = {
    "SF-CU106-CALC-001": "review-cu106-calc-001",
    "SF-CU106-VAL-001": "review-cu106-val-001",
    "SF-CU106-EXC-001": "review-cu106-exc-001",
    "SF-CU106-MSG-001": "review-cu106-msg-001",
}


def coverage_items() -> list[dict[str, Any]]:
    return [
        {
            "source_fact_id": fact["source_fact_id"],
            "program": fact["program"],
            "section": fact["section"],
            "fact_type": fact["fact_type"],
            "status": "included",
            "review_anchor": ANCHORS[fact["source_fact_id"]],
            "merged_source_fact_ids": [],
            "exclusion_reason": None,
        }
        for fact in SOURCE_FACTS
    ]


def render_review(manifest: dict[str, Any]) -> str:
    program_rows = manifest["programs"]
    overview_refs = "; ".join(fact["source_fact_id"] for fact in SOURCE_FACTS)
    return f"""---
document_id: {manifest['document_id']}
flow_slug: {manifest['flow_slug']}
program_set_slug: {manifest['program_set_slug']}
programs:
  - CU106
review_status: complete_exploratory
artifact_version: {manifest['artifact_version']}
---

# SME Core Review: {manifest['folder_slug']}

## Program Set Reading Summary

This complete_exploratory review covers CU106 as an evidence-bounded program
set. It preserves calculation carriers, validation status outcomes, exception
closure, and exact message inventory values. The supplied program order is SME
navigation only and is not a confirmed execution sequence or call chain.

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
| Request setup | CU106 MAIN | Read the request carriers used by the guarded calculation. | <a id="review-overview-request"></a> review-overview-request | {overview_refs} |
| Calculation | CU106 RLOG-CU106-001 | Follow the approved amount assignment into the response payload. | <a id="review-overview-calculation"></a> review-overview-calculation | {overview_refs} |
| Validation | CU106 RLOG-CU106-001 | Confirm exact status 00 and its eligibility trigger. | <a id="review-overview-validation"></a> review-overview-validation | {overview_refs} |
| Exception and message | CU106 RLOG-CU106-001 | Confirm E1 closure and exact UCC1061 response message. | <a id="review-overview-exception"></a> review-overview-exception | {overview_refs} |

## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Derive the approved amount from request amount and account limit. | CU106 | RLOG-CU106-001 / MAIN | CU106_APPROVED_AMOUNT | REQUEST_AMOUNT, ACCOUNT_LIMIT | request and account validation succeeded | returns the approved amount in the response payload | EV-CU106-CALC-001 | confirmed | <a id="review-cu106-calc-001"></a> review-cu106-calc-001 | SF-CU106-CALC-001 |

## Validation Logic

| Message / Status / Outcome | Description | Program | Routine | Condition / Evidence | Carrier / Destination | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | Approved response status after eligibility validation. | CU106 | RLOG-CU106-001 / MAIN | request is present and account status is active | RESPONSE_STATUS | continues to the approved response handoff | EV-CU106-VAL-001 | confirmed | <a id="review-cu106-val-001"></a> review-cu106-val-001 | SF-CU106-VAL-001 |

## Exception Handling

| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Account lookup failure | CU106 | RLOG-CU106-001 / MAIN | %FOUND lookup result is false | RESPONSE_STATUS = E1 | return after setting E1 | suppresses persistence and returns the failure status | account lookup does not find the requested key; EV-CU106-EXC-001 | confirmed | <a id="review-cu106-exc-001"></a> review-cu106-exc-001 | SF-CU106-EXC-001 |

## Message Inventory

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Condition / Handler | Carrier / Destination | Effect | Detail Refs | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UCC1061 | Account eligibility failed. | message | CU106 RLOG-CU106-001 / MAIN | 1 | account eligibility validation fails | response message field | returns the exact operator-reviewable message to the caller | MSG-CU106-001 | confirmed | <a id="review-cu106-msg-001"></a> review-cu106-msg-001 | SF-CU106-MSG-001 |

## Core Completeness Ledger

{FLOW.render_completeness_table(program_rows)}

## Coverage Reconciliation

Every normalized source fact is mapped to the anchored review rows above; the
sibling coverage ledger records the machine-readable disposition and counts.

## Sources

{FLOW.render_sources_table(program_rows)}

## Run Profile

{FLOW.render_run_profile(manifest)}

## Source Inventory Cache

{FLOW.render_source_inventory(manifest)}
"""


def write_complete_bundle(root: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    artifact_root = root / "artifacts"
    write_finalized_program_artifacts(
        artifact_root / "modules" / "normal_program" / "CU106", "CU106"
    )
    config = FLOW.load_yaml(PROFILE)
    manifest = FLOW.build_manifest(
        review_name="Card Authorization",
        programs=["CU106"],
        artifact_root=artifact_root,
        config=config,
        working_branch="test-core-coverage",
    )
    folder_slug = manifest["folder_slug"]
    final_filename = f"{folder_slug}--sme-core-review.md"
    manifest = {
        **manifest,
        "document_id": manifest["review_id"],
        "canonical_filename": final_filename,
        "review_status": "complete_exploratory",
        "artifact_readiness": "ready",
        "merge_coverage": "complete",
        "programs": [dict(manifest["programs"][0])],
    }
    bundle = root / folder_slug
    bundle.mkdir(parents=True)
    manifest_path = bundle / "program-set-core-input-manifest.yaml"
    source_pack_path = bundle / "program-set-reader-first-source-pack.md"
    facts_path = bundle / "program-set-core-facts.yaml"
    coverage_path = bundle / "program-set-core-coverage.yaml"
    review_path = bundle / final_filename

    manifest_path.write_text(FLOW.dump_yaml(manifest), encoding="utf-8")
    source_pack_path.write_text(
        f"""# Program Set Reader-First Source Pack

Document ID: {manifest['document_id']}
Flow Slug: {manifest['flow_slug']}
Program Set Slug: {manifest['program_set_slug']}

## CU106

### Program Reading Summary

CU106 processes account eligibility and returns exact response carriers.

### Calculation Logic

[SF-CU106-CALC-001] Derive CU106_APPROVED_AMOUNT from request and limit carriers.

### Validation Logic

[SF-CU106-VAL-001] Set exact status 00 after eligibility validation.

### Exception Handling

[SF-CU106-EXC-001] Close account lookup failure with exact status E1.

### Message Inventory

[SF-CU106-MSG-001] Preserve exact message UCC1061.
""",
        encoding="utf-8",
    )
    facts_payload = {
        "schema_version": "0.4",
        "document_id": manifest["document_id"],
        "source_facts": list(SOURCE_FACTS),
        "programs": [
            {
                "program": "CU106",
                "source_fact_ids": [fact["source_fact_id"] for fact in SOURCE_FACTS],
                "facts": {
                    "calculation": [dict(SOURCE_FACTS[0])],
                    "validation": [dict(SOURCE_FACTS[1])],
                    "exception": [dict(SOURCE_FACTS[2])],
                    "message": [dict(SOURCE_FACTS[3])],
                },
            }
        ],
    }
    facts_path.write_text(FLOW.dump_yaml(facts_payload), encoding="utf-8")
    coverage_payload = {
        "schema_version": "0.4",
        "document_id": manifest["document_id"],
        "review_status": "complete_exploratory",
        "coverage_status": "complete",
        "allowed_statuses": [
            "included",
            "merged",
            "excluded_non_core",
            "pending",
        ],
        "coverage_counts": {
            "total_source_facts": len(SOURCE_FACTS),
            "accounted_source_facts": len(SOURCE_FACTS),
            "pending_source_facts": 0,
            "by_program": {"CU106": len(SOURCE_FACTS)},
            "by_section": {
                "Calculation Logic": 1,
                "Validation Logic": 1,
                "Exception Handling": 1,
                "Message Inventory": 1,
            },
            "routine_rlog": {},
        },
        "coverage_items": coverage_items(),
        "items": coverage_items(),
        "expected_source_fact_count": len(SOURCE_FACTS),
        "coverage_item_count": len(SOURCE_FACTS),
        "status_counts": {
            "included": len(SOURCE_FACTS),
            "merged": 0,
            "excluded_non_core": 0,
            "pending": 0,
        },
    }
    coverage_path.write_text(FLOW.dump_yaml(coverage_payload), encoding="utf-8")
    review_path.write_text(render_review(manifest), encoding="utf-8")
    return manifest_path, review_path, coverage_path, manifest


def validate_bundle(manifest_path: Path, review_path: Path) -> list[str]:
    # This older hand-shaped fixture isolates row-level reconciliation rules.
    # End-to-end v0.4 origin/readiness validation is exercised with genuinely
    # generated bundles in test_program_set_reader_first_coverage.py.
    manifest = FLOW.load_yaml(manifest_path)
    markdown = review_path.read_text(encoding="utf-8")
    bundle_dir = manifest_path.parent
    return [
        *FLOW.validate_manifest(manifest),
        *FLOW.validate_review_identity(markdown, manifest),
        *FLOW.validate_review(markdown, manifest),
        *FLOW.validate_source_bundle(
            manifest=manifest,
            markdown=markdown,
            source_pack_path=bundle_dir / FLOW.SOURCE_PACK_FILENAME,
            core_facts_path=bundle_dir / FLOW.CORE_FACTS_FILENAME,
            coverage_path=bundle_dir / FLOW.CORE_COVERAGE_FILENAME,
        ),
    ]


class ProgramSetCoreCoverageReconciliationTests(unittest.TestCase):
    def test_complete_coverage_accounts_for_every_program_fact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )

            findings = validate_bundle(manifest_path, review_path)

            self.assertEqual(findings, [])

    def test_validator_rejects_unaccounted_material_source_fact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            coverage = FLOW.load_yaml(coverage_path)
            coverage["coverage_items"][0] = {
                **coverage["coverage_items"][0],
                "status": "pending",
                "review_anchor": None,
            }
            coverage["coverage_counts"] = {
                **coverage["coverage_counts"],
                "accounted_source_facts": 3,
                "pending_source_facts": 1,
            }
            coverage_path.write_text(FLOW.dump_yaml(coverage), encoding="utf-8")
            review_path.write_text(
                "\n".join(
                    line
                    for line in review_path.read_text(encoding="utf-8").splitlines()
                    if "SF-CU106-CALC-001" not in line
                )
                + "\n",
                encoding="utf-8",
            )

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(
                    "SF-CU106-CALC-001" in finding
                    and re.search(r"pending|unaccounted", finding, re.I)
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_removed_exact_message_status_or_literal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            review = review_path.read_text(encoding="utf-8")
            self.assertIn("UCC1061", review)
            review_path.write_text(review.replace("UCC1061", "generic message"), encoding="utf-8")

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(
                    "UCC1061" in finding
                    and re.search(r"message|literal|exact", finding, re.I)
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_material_fact_id_left_only_outside_its_core_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            review = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                review.replace("CU106_APPROVED_AMOUNT", "generic output carrier"),
                encoding="utf-8",
            )

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(
                    "SF-CU106-CALC-001" in finding
                    and re.search(r"material|exact|row", finding, re.I)
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_anchor_fact_and_exact_token_without_logic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            lines = review_path.read_text(encoding="utf-8").splitlines()
            review_path.write_text(
                "\n".join(
                    "| CU106_APPROVED_AMOUNT | CU106 | + | = | + | = | = | = | = | "
                    '<a id="review-cu106-calc-001"></a> | SF-CU106-CALC-001 |'
                    if "review-cu106-calc-001" in line
                    else line
                    for line in lines
                )
                + "\n",
                encoding="utf-8",
            )

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(
                    "SF-CU106-CALC-001" in finding
                    and "link-only" in finding
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_exact_message_marked_excluded_non_core(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            coverage = FLOW.load_yaml(coverage_path)
            coverage["coverage_items"][-1] = {
                **coverage["coverage_items"][-1],
                "status": "excluded_non_core",
                "review_anchor": None,
                "exclusion_reason": "message omitted from the primary reading path",
            }
            coverage_path.write_text(FLOW.dump_yaml(coverage), encoding="utf-8")

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(
                    "SF-CU106-MSG-001" in finding
                    and "excluded_non_core" in finding
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_coverage_anchor_missing_from_final_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            coverage = FLOW.load_yaml(coverage_path)
            coverage["coverage_items"][0] = {
                **coverage["coverage_items"][0],
                "review_anchor": "review-anchor-does-not-exist",
            }
            coverage_path.write_text(FLOW.dump_yaml(coverage), encoding="utf-8")

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(
                    "review-anchor-does-not-exist" in finding
                    and re.search(r"anchor|not found|missing", finding, re.I)
                    for finding in findings
                ),
                findings,
            )

    def test_validator_rejects_coverage_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            coverage = FLOW.load_yaml(coverage_path)
            coverage["coverage_counts"] = {
                **coverage["coverage_counts"],
                "total_source_facts": 99,
            }
            coverage_path.write_text(FLOW.dump_yaml(coverage), encoding="utf-8")

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any(re.search(r"coverage count|count mismatch", finding, re.I) for finding in findings),
                findings,
            )


class ProgramSetReviewSafetyContractTests(unittest.TestCase):
    def test_validator_rejects_program_order_presented_as_confirmed_call_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )
            review = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                review.replace(
                    "The supplied program order is SME\n"
                    "navigation only and is not a confirmed execution sequence or call chain.",
                    "The SME navigation order is the source-confirmed call chain for this set.",
                ),
                encoding="utf-8",
            )

            findings = validate_bundle(manifest_path, review_path)

            self.assertTrue(
                any("navigation order" in finding and "source-confirmed call" in finding for finding in findings),
                findings,
            )

    def test_navigation_order_without_call_claim_remains_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, _manifest = write_complete_bundle(
                Path(temp_dir)
            )

            findings = validate_bundle(manifest_path, review_path)

            self.assertFalse(
                any("navigation order" in finding and "source-confirmed call" in finding for finding in findings),
                findings,
            )

    def test_validator_rejects_every_forbidden_full_flow_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path, review_path, _coverage_path, manifest = write_complete_bundle(
                Path(temp_dir)
            )
            base = review_path.read_text(encoding="utf-8")
            forbidden_sections = (
                "Trigger Inventory",
                "Nodes",
                "Edges",
                "Transaction Call Map",
                "Replay",
                "Lineage",
                "Capability Seeds",
            )
            for section in forbidden_sections:
                with self.subTest(section=section):
                    findings = FLOW.validate_review(
                        base + f"\n## {section}\n\nForbidden full-flow content.\n",
                        manifest,
                    )
                    self.assertTrue(
                        any(
                            section in finding and "forbidden full-flow section" in finding
                            for finding in findings
                        ),
                        findings,
                    )


if __name__ == "__main__":
    unittest.main()
