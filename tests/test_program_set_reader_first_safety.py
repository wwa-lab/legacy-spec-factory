from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)


def load_merger():
    spec = importlib.util.spec_from_file_location("reader_first_safety_merger", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load merger: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MERGER = load_merger()
SAFETY = sys.modules["review_safety_contract"]


def safety_manifest() -> dict[str, object]:
    return {
        "review_status": "ready_for_synthesis",
        "core_review_profile": {
            "name": "standard_reader_first",
            "core_sections": list(MERGER.CORE_READING_SECTIONS),
            "include_message_inventory": True,
            "include_audit_sections": True,
        },
        "programs": [
            {"normalized_name": "CU106", "run_resolution": "analyzed_this_run"},
            {"normalized_name": "CU101A", "run_resolution": "analyzed_this_run"},
        ],
    }


class ProgramSetReaderFirstSafetyTests(unittest.TestCase):
    def test_all_full_flow_headings_remain_forbidden(self) -> None:
        headings = (
            "Trigger Inventory",
            "Nodes",
            "Edges",
            "Transaction Call Map",
            "Replay",
            "Lineage",
            "Capability Seeds",
        )
        for heading in headings:
            with self.subTest(heading=heading):
                findings = MERGER.validate_review(
                    f"# Invalid Program Set Review\n\n## {heading}\n\nNot part of a reader-first merger.\n",
                    safety_manifest(),
                )
                self.assertTrue(
                    any(
                        "forbidden full-flow section" in finding
                        and heading in finding
                        for finding in findings
                    ),
                    findings,
                )

    def test_navigation_order_disclaimer_is_allowed_but_inferred_call_order_is_rejected(self) -> None:
        safe = (
            "The SME program list is navigation order only; no source-confirmed "
            "execution order or call relationship is asserted."
        )
        safe_findings = MERGER.validate_review(safe, safety_manifest())
        self.assertFalse(
            any("navigation order" in finding.lower() for finding in safe_findings),
            safe_findings,
        )

        claims = (
            "Because the SME listed CU106 before CU101A, CU106 calls CU101A in the confirmed execution order.",
            "Program list order confirms the call chain CU106 -> CU101A.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                findings = MERGER.validate_review(claim, safety_manifest())
                self.assertTrue(
                    any(
                        "order" in finding.lower()
                        and "call" in finding.lower()
                        for finding in findings
                    ),
                    findings,
                )

    def test_exact_literals_use_the_same_rendered_inline_normalization(self) -> None:
        for rendered in (
            "[RLOG-CU106-001](#rlog-cu106-001)",
            "[RLOG-CU106-001][rlog-detail]",
            "<span>RESULT</span>",
            "<code>E1</code>",
            "`AUTH|DECLINED`",
            r"AUTH\|RETRY",
        ):
            with self.subTest(rendered=rendered):
                self.assertTrue(MERGER._literal_present(rendered, rendered))

        self.assertTrue(
            MERGER._literal_present(
                "The exact response is `AUTH|RETRY`.", r"AUTH\|RETRY"
            )
        )

    def test_duplicate_final_front_matter_keys_fail_closed(self) -> None:
        manifest = {
            "document_id": "DOC-1",
            "review_id": "DOC-1",
            "flow_slug": "flow",
            "program_set_slug": "programs",
            "folder_slug": "flow--programs",
            "artifact_version": "0.4",
            "programs": [{"normalized_name": "CU106"}],
        }
        markdown = """---
document_id: DOC-1
document_id: DOC-1
flow_slug: flow
program_set_slug: programs
programs: [CU106]
review_status: complete_exploratory
artifact_version: '0.4'
---

# Program Set SME Core Review: flow--programs
"""

        findings = MERGER.validate_review_identity(markdown, manifest)

        self.assertTrue(
            any("front matter" in item.lower() for item in findings), findings
        )

    def test_forbidden_full_flow_heading_variants_are_rejected(self) -> None:
        for heading in (
            "Trigger Inventory:",
            "Trigger Inventory — Details",
            "1. Trigger Inventory",
            "Transaction Call Map (source-confirmed)",
            "Replay / Notes",
            "Capability Seeds 🚫",
        ):
            with self.subTest(heading=heading):
                findings = MERGER.validate_review(
                    f"## {heading}\n\nThis section must not reappear.\n",
                    safety_manifest(),
                )
                self.assertTrue(
                    any("forbidden full-flow section" in item for item in findings),
                    findings,
                )

    def test_prohibited_decision_headings_and_dash_forms_are_rejected(self) -> None:
        for markdown in (
            "## Modernization Recommendation\n\nCreate a service.\n",
            "## Architecture Decision\n\nUse a modular target.\n",
            "## Service Boundary Proposal\n\nSplit CU106.\n",
            "## Program Set Reading Summary\n\nModernization recommendation — migrate CU106.\n",
            "## Program Set Reading Summary\n\nArchitecture Decision - use a cloud target.\n",
        ):
            with self.subTest(markdown=markdown.splitlines()[0]):
                findings = MERGER.validate_review(markdown, safety_manifest())
                self.assertTrue(
                    any(
                        "modernization" in item.lower()
                        or "architecture" in item.lower()
                        or "service boundary" in item.lower()
                        for item in findings
                    ),
                    findings,
                )

    def test_direct_program_order_assertion_variants_are_rejected(self) -> None:
        for claim in (
            "The programs run in the supplied order.",
            "The first listed program precedes the next at runtime.",
            "The SME input sequence is the actual call path.",
            "The ordered list defines which program runs first and which follows.",
            "Navigation order equals runtime order.",
        ):
            with self.subTest(claim=claim):
                findings = MERGER.validate_review(
                    f"## Program Set Reading Summary\n\n{claim}\n", safety_manifest()
                )
                self.assertTrue(
                    any("order" in item.lower() or "sequence" in item.lower() for item in findings),
                    findings,
                )

    def test_pipe_inside_table_relation_claim_cannot_bypass_fact_support_gate(self) -> None:
        facts = {
            "SF-LOCAL": {
                "source_fact_id": "SF-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates the request locally.",
            }
        }
        review = """## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local calculation | CU106 | MAIN | RESULT | INPUT | valid | CU106 sends `LEFT | RIGHT` to CU101A | local evidence | confirmed | <a id="review-pipe"></a> review-pipe | SF-LOCAL |
"""

        findings = MERGER._validate_cross_program_relation_claims(
            review, facts, safety_manifest()
        )

        self.assertTrue(
            any("unsupported" in item.lower() for item in findings), findings
        )

    def test_relation_synonyms_require_single_fact_support(self) -> None:
        facts = {
            "SF-LOCAL": {
                "source_fact_id": "SF-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates the request locally.",
            }
        }
        claims = (
            "CU106 supplies input to CU101A.",
            "CU106 yields a request to CU101A.",
            "CU106 emits a record to CU101A.",
            "CU106 writes an output for CU101A.",
            "CU106 starts CU101A.",
            "CU106 runs CU101A.",
            "CU106 queues work for CU101A.",
            "CU106 publishes a request to CU101A.",
            "CU106 requests processing from CU101A.",
            "CU106 chains to CU101A.",
            "CU106 precedes CU101A at runtime.",
            "CU106 follows CU101A at runtime.",
            "CU106 supplies CU101A with INPUT-REC.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                findings = MERGER._validate_cross_program_relation_claims(
                    f"## Notes\n\n{claim} SF-LOCAL\n",
                    facts,
                    safety_manifest(),
                )
                self.assertTrue(
                    any("unsupported" in item.lower() for item in findings),
                    findings,
                )

    def test_external_and_single_manifest_program_relations_are_still_tracked(self) -> None:
        local_facts = {
            "SF-LOCAL": {
                "source_fact_id": "SF-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates locally.",
            }
        }
        for claim, manifest in (
            ("CU106 calls EXT999. SF-LOCAL", safety_manifest()),
            ("EXT999 calls CU106. SF-LOCAL", safety_manifest()),
            ("CU106 sends SECRET_PAYLOAD to EXT999. SF-LOCAL", safety_manifest()),
            (
                "CU106 calls CU101A. SF-LOCAL",
                {"programs": [{"normalized_name": "CU106"}]},
            ),
        ):
            with self.subTest(claim=claim):
                findings = MERGER._validate_cross_program_relation_claims(
                    f"## Notes\n\n{claim}\n", local_facts, manifest
                )
                self.assertTrue(
                    any("unsupported" in item.lower() for item in findings),
                    findings,
                )

        supported = {
            "SF-EXTERNAL": {
                "source_fact_id": "SF-EXTERNAL",
                "program": "CU106",
                "logic": "CU106 calls EXT999 after validation.",
            }
        }
        self.assertEqual(
            MERGER._validate_cross_program_relation_claims(
                "## Notes\n\nCU106 calls EXT999 after validation. SF-EXTERNAL\n",
                supported,
                {"programs": [{"normalized_name": "CU106"}]},
            ),
            [],
        )

    def test_local_run_word_does_not_invent_a_cross_program_relation(self) -> None:
        findings = MERGER._validate_cross_program_relation_claims(
            "## Notes\n\n"
            "CU106 runs local validation; CU101A calculates its own response. SF-LOCAL\n",
            {
                "SF-LOCAL": {
                    "source_fact_id": "SF-LOCAL",
                    "program": "CU106",
                    "logic": "CU106 runs local validation.",
                }
            },
            safety_manifest(),
        )

        self.assertEqual(findings, [])

    def test_nested_link_destinations_and_quoted_html_attributes_hide_fact_refs(
        self,
    ) -> None:
        for hidden in (
            "[trace](https://x.invalid/a_(b)/SF-FAKE)",
            '[trace](https://x.invalid/a_(b) "title ) SF-FAKE")',
            "![SF-FAKE](https://x.invalid/trace.png)",
            '<span title="x>SF-FAKE">visible</span>',
        ):
            with self.subTest(hidden=hidden):
                self.assertNotIn("SF-FAKE", SAFETY._visible_inline_text(hidden))

        markdown = """## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local calculation | CU106 | MAIN | RESULT | INPUT | valid | returns result | evidence | confirmed | <a id="review-hidden-ref"></a> review-hidden-ref | [trace](https://x.invalid/a_(b)/SF-FAKE) |
"""
        self.assertEqual(
            MERGER._visible_fact_mapping_rows(
                markdown, "Calculation Logic", "review-hidden-ref", "SF-FAKE"
            ),
            [],
        )

    def test_mismatched_separator_arity_cannot_form_a_fact_mapping_table(self) -> None:
        markdown = """## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- |
| Local calculation | CU106 | MAIN | RESULT | INPUT | valid | returns result | evidence | confirmed | <a id="review-bad-separator"></a> review-bad-separator | SF-LOCAL |
"""
        block = MERGER.h2_section_block(markdown, "Calculation Logic")

        self.assertEqual(
            MERGER.extract_markdown_table_records(
                block, MERGER._fact_row_headers("Calculation Logic")
            ),
            [],
        )
        records, findings = MERGER._canonical_review_table_records(
            block,
            "Calculation Logic",
            MERGER._fact_row_headers("Calculation Logic"),
        )
        self.assertEqual(records, [])
        self.assertTrue(any("separator" in item.lower() for item in findings), findings)

    def test_active_python_table_parsers_do_not_use_raw_pipe_split(self) -> None:
        script_dir = SCRIPT.parent
        for filename in (
            "reader_first_merge_contract.py",
            "program_set_core_review.py",
            "review_safety_contract.py",
        ):
            with self.subTest(filename=filename):
                source = (script_dir / filename).read_text(encoding="utf-8")
                self.assertNotIn('.split("|")', source)
                self.assertNotIn(".split('|')", source)


if __name__ == "__main__":
    unittest.main()
