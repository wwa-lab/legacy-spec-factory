from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import (
    write_finalized_program_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MERGER_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)
UPSTREAM_VALIDATOR_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "validate_program_analysis_contract.py"
)
PROFILE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)
FACT_ID_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "reader_first_fact_identity.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


MERGER = load_module("reader_first_extraction_merger", MERGER_SCRIPT)
FACT_CONTRACT = sys.modules["reader_first_merge_contract"]
UPSTREAM_VALIDATOR = load_module(
    "reader_first_fixture_upstream_validator", UPSTREAM_VALIDATOR_SCRIPT
)


def require_public_seam(name: str):
    seam = getattr(MERGER, name, None)
    if not callable(seam):
        raise AssertionError(f"program-set merger is missing public seam {name}()")
    return seam


def h2_block(markdown: str, heading: str) -> str:
    marker = f"## {heading}"
    start = markdown.index(marker)
    next_start = markdown.find("\n## ", start + len(marker))
    return markdown[start : next_start if next_start >= 0 else len(markdown)].strip()


class ProgramSetReaderFirstExtractionTests(unittest.TestCase):
    def test_source_fact_identity_matches_fixed_cross_runtime_vectors(self) -> None:
        vectors = json.loads(FACT_ID_FIXTURE.read_text(encoding="utf-8"))["vectors"]

        for vector in vectors:
            with self.subTest(fact_type=vector["fact_type"]):
                actual = FACT_CONTRACT.stable_source_fact_id(
                    vector["program"],
                    vector["section"],
                    vector["fact_type"],
                    vector["source_text"],
                )
                self.assertEqual(actual, vector["expected_source_fact_id"])

                identified = FACT_CONTRACT._identified(
                    {
                        "program": vector["program"],
                        "section": vector["section"],
                        "fact_type": vector["fact_type"],
                        "logic": "non-identity field",
                        "source_text": vector["source_text"],
                    }
                )
                enriched = FACT_CONTRACT._identified(
                    {
                        **identified,
                        "source_fact_id": "must-not-seed-the-next-id",
                        "logic": "changed non-identity field",
                        "evidence_status": "changed",
                    }
                )
                self.assertEqual(
                    identified["source_fact_id"], enriched["source_fact_id"]
                )

    def test_source_fact_identity_uses_ordered_row_or_cells_when_text_is_absent(
        self,
    ) -> None:
        vector = json.loads(FACT_ID_FIXTURE.read_text(encoding="utf-8"))["vectors"][1]
        row = {
            "Theme": "Operator response",
            "Routines": "MAIN",
            "Reader Cue": "Read exact token.",
        }
        cells = [
            {"header": header, "value": value} for header, value in row.items()
        ]
        common = {
            "program": vector["program"],
            "section": vector["section"],
            "fact_type": vector["fact_type"],
            "logic": "Operator response",
        }

        from_row = FACT_CONTRACT._identified({**common, "source_row": row})
        from_cells = FACT_CONTRACT._identified({**common, "source_cells": cells})

        self.assertEqual(from_row["source_fact_id"], vector["expected_source_fact_id"])
        self.assertEqual(from_cells["source_fact_id"], vector["expected_source_fact_id"])
        self.assertEqual(from_row["source_text"], vector["source_text"])
        self.assertEqual(from_cells["source_text"], vector["source_text"])

    def test_source_pack_is_lossless_and_facts_cover_canonical_reader_first_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            cu106_messages = (
                {
                    "code": "NF",
                    "description": "Requested account record was not found.",
                    "type": "response_status",
                    "occurrences": "1",
                    "routines": "MAIN",
                    "first_seen": "STATUS_CODE assignment in MAIN",
                    "trigger": "account lookup does not find the requested key",
                    "detail": "MSG-CU106-001",
                },
                {
                    "code": "AUTH-DECLINED",
                    "description": "Authorization request was declined by the eligibility guard.",
                    "type": "response_literal",
                    "occurrences": "1",
                    "routines": "VALIDATE",
                    "first_seen": "RESPONSE_TEXT assignment in VALIDATE",
                    "trigger": "account is inactive or request amount exceeds the limit",
                    "detail": "MSG-CU106-002",
                },
                {
                    "code": "*PSSR",
                    "description": "Generic program exception handler token.",
                    "type": "generic_handler",
                    "occurrences": "1",
                    "routines": "*PSSR",
                    "first_seen": "generic exception handler declaration",
                    "trigger": "unhandled program exception reaches the generic handler",
                    "detail": "MSG-CU106-003",
                },
            )
            fixtures = (
                write_finalized_program_artifacts(
                    artifact_root / "modules" / "normal" / "CU106",
                    "CU106",
                    routines=("MAIN", "VALIDATE"),
                    messages=cu106_messages,
                    theme_markers={
                        "summary": "CU106-SUMMARY-THEME-MARKER",
                        "calculation": "CU106-CALCULATION-THEME-MARKER",
                        "validation": "CU106-VALIDATION-THEME-MARKER",
                        "exception": "CU106-EXCEPTION-THEME-MARKER",
                    },
                ),
                write_finalized_program_artifacts(
                    artifact_root / "modules" / "normal" / "CU101A",
                    "CU101A",
                    routines=("MAIN", "FINALIZE"),
                    theme_markers={
                        "summary": "CU101A-SUMMARY-THEME-MARKER",
                        "calculation": "CU101A-CALCULATION-THEME-MARKER",
                        "validation": "CU101A-VALIDATION-THEME-MARKER",
                        "exception": "CU101A-EXCEPTION-THEME-MARKER",
                    },
                ),
            )
            for fixture in fixtures:
                self.assertEqual(
                    UPSTREAM_VALIDATOR.validate(fixture.analysis_dir),
                    [],
                    f"fixture must satisfy the real upstream final contract: {fixture.program}",
                )

            manifest = MERGER.build_manifest(
                review_name="Reader First Extraction",
                programs=["CU106", "CU101A"],
                artifact_root=artifact_root,
                config=MERGER.load_yaml(PROFILE),
                working_branch="fixture",
                flow_slug="reader-first-extraction",
            )
            source_pack = require_public_seam("build_reader_first_source_pack")(
                manifest, artifact_root
            )

            self.assertIsInstance(source_pack, str)
            for fixture in fixtures:
                source_markdown = fixture.program_analysis.read_text(encoding="utf-8")
                for section in (
                    "Program Reading Summary",
                    "Calculation Logic",
                    "Validation Logic",
                    "Exception Handling",
                    "Message Inventory",
                ):
                    with self.subTest(program=fixture.program, section=section):
                        self.assertIn(h2_block(source_markdown, section), source_pack)
                for number in range(1, 3):
                    self.assertIn(f"RLOG-{fixture.prefix}-{number:03d}", source_pack)
            self.assertNotIn("## File I/O\n", source_pack)
            self.assertIn("AUTH-DECLINED", source_pack)

            facts = require_public_seam("build_core_facts")(manifest, artifact_root)
            repeated = require_public_seam("build_core_facts")(manifest, artifact_root)
            source_facts = facts["source_facts"]
            self.assertTrue(source_facts)
            self.assertEqual(
                [fact["source_fact_id"] for fact in source_facts],
                [fact["source_fact_id"] for fact in repeated["source_facts"]],
            )
            self.assertEqual(
                len({fact["source_fact_id"] for fact in source_facts}),
                len(source_facts),
            )
            fields_by_type = {
                "calculation": {
                    "calculation",
                    "target_carrier",
                    "source_carriers",
                    "guard",
                    "effect",
                    "supporting_detail",
                },
                "validation": {
                    "description",
                    "exact_code_status",
                    "validation_type",
                    "trigger_chain",
                    "carrier_destination",
                    "effect",
                },
                "exception": {
                    "exception_path",
                    "guard",
                    "detection_mechanism",
                    "fields_messages_set",
                    "exception_action",
                    "effect",
                    "supporting_detail",
                },
                "message": {
                    "exact_message_status_literal",
                    "description",
                    "message_type",
                    "generic_handler_token",
                    "occurrences",
                    "first_seen",
                    "trigger_handler",
                    "carrier_destination",
                    "effect",
                },
                "routine": {"routine", "category"},
                "thematic_table": {"source_headers"},
            }
            common_fields = {
                "source_fact_id",
                "program",
                "section",
                "fact_type",
                "material",
                "logic",
                "exact_value",
                "evidence",
                "evidence_reference",
                "evidence_status",
                "unresolved_reason",
                "source_artifact",
                "source_text",
            }
            for fact in source_facts:
                with self.subTest(contract_fields=fact["source_fact_id"]):
                    self.assertTrue(common_fields.issubset(fact))
                    self.assertTrue(fields_by_type.get(fact["fact_type"], set()).issubset(fact))
                    if fact["fact_type"] not in {
                        "summary_contribution",
                        "thematic_prose",
                        "unresolved_core_statement",
                    }:
                        self.assertIn("source_row", fact)
                        self.assertIn("source_cells", fact)

            by_program = {row["program"]: row for row in facts["programs"]}
            self.assertEqual(set(by_program), {"CU106", "CU101A"})
            for program, row in by_program.items():
                buckets = row["facts"]
                for bucket in (
                    "summary_contributions",
                    "calculations",
                    "validations",
                    "exceptions",
                    "messages",
                    "routines",
                ):
                    with self.subTest(program=program, bucket=bucket):
                        self.assertTrue(buckets[bucket])
                        self.assertTrue(
                            all(item.get("source_fact_id") for item in buckets[bucket])
                        )
                for bucket in ("calculations", "exceptions"):
                    self.assertTrue(
                        all(
                            item.get("evidence_status") == "evidence_present"
                            for item in buckets[bucket]
                        ),
                        "canonical Evidence IDs without an Evidence Status column are evidence-present, not unresolved facts",
                    )

            cu106_serialized = json.dumps(by_program["CU106"]["facts"], sort_keys=True)
            self.assertIn("AUTH-DECLINED", cu106_serialized)
            self.assertIn('"generic_handler_token": "*PSSR"', cu106_serialized)
            self.assertIn("Requested account record was not found", cu106_serialized)
            self.assertIn("RLOG-CU106-001", cu106_serialized)
            self.assertNotIn("call_edges", json.dumps(facts, sort_keys=True))

    def test_generic_material_tables_are_collected_from_all_five_sections_only_once(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            fixture = write_finalized_program_artifacts(
                artifact_root / "modules" / "normal" / "CU106",
                "CU106",
                routines=("MAIN",),
            )
            markdown = fixture.program_analysis.read_text(encoding="utf-8")
            markdown = markdown.replace(
                "**Calculation logic unresolved:** None.",
                """| Field | Value |
| --- | --- |
| Program | CU106 |

**Calculation logic unresolved:** None.""",
                1,
            )
            markdown = markdown.replace(
                "**Message inventory unresolved:** None.",
                """| Theme | Routines | Reader Cue |
| --- | --- | --- |
| Operator response | MAIN | Read the exact response token with its handler context. |
|  |  |  |

**Message inventory unresolved:** None.""",
                1,
            )
            fixture.program_analysis.write_text(markdown, encoding="utf-8")
            manifest = {
                "document_id": "reader-first-five-sections",
                "review_id": "reader-first-five-sections",
                "programs": [
                    {
                        "normalized_name": "CU106",
                        "artifact_root": "modules/normal/CU106",
                        "run_resolution": "analyzed_this_run",
                    }
                ],
            }

            facts = require_public_seam("build_core_facts")(manifest, artifact_root)
            thematic = [
                fact
                for fact in facts["source_facts"]
                if fact.get("fact_type") == "thematic_table"
            ]

            self.assertEqual(
                {fact["section"] for fact in thematic},
                {
                    "Program Reading Summary",
                    "Calculation Logic",
                    "Validation Logic",
                    "Exception Handling",
                    "Message Inventory",
                },
            )
            self.assertEqual(
                sum(
                    fact.get("source_row", {}).get("Theme") == "Operator response"
                    for fact in thematic
                ),
                1,
            )
            self.assertFalse(
                any(
                    fact.get("source_row", {}).get("Field") == "Program"
                    for fact in thematic
                )
            )
            self.assertTrue(all(fact.get("logic") for fact in thematic))
            self.assertFalse(
                any(
                    "RLOG / Routine" in fact.get("source_row", {})
                    or "Calculation / Assignment" in fact.get("source_row", {})
                    or "Exception / Error Path" in fact.get("source_row", {})
                    or "Message / Code / Literal" in fact.get("source_row", {})
                    for fact in thematic
                )
            )

    def test_fact_extraction_ignores_hidden_and_non_structural_source_content(
        self,
    ) -> None:
        markdown = """## Program Reading Summary

Visible summary for CU106.
<!--
HIDDEN-COMMENT-SUMMARY
## Calculation Logic
| Calculation / Assignment | Target Field / Carrier |
| --- | --- |
| HIDDEN-COMMENT-CALC | HIDDEN_COMMENT_TARGET |
-->

<div hidden>
HIDDEN-CONTAINER-SUMMARY
</div>

## Calculation Logic

Visible calculation explanation.

```markdown
## Validation Logic
| Calculation / Assignment | Target Field / Carrier |
| --- | --- |
| HIDDEN-FENCED-CALC | HIDDEN_FENCED_TARGET |
```

> ```markdown
> <template>
> HIDDEN-BLOCKQUOTE-FENCE-TEMPLATE
> </template>
> ```

    | Calculation / Assignment | Target Field / Carrier |
    | --- | --- |
    | HIDDEN-INDENTED-CALC | HIDDEN_INDENTED_TARGET |

| Calculation / Assignment | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail Link |
| --- | --- | --- | --- | --- | --- | --- |
| Set RESULT from INPUT | MAIN | RESULT | INPUT | valid request | return result | RLOG-CU106-001 |

## Validation Logic

Visible validation explanation.

## Exception Handling

Visible exception explanation.

<template>
| Exception / Error Path | Routine | Fields / Messages Set |
| --- | --- | --- |
| HIDDEN-TEMPLATE-ERROR | MAIN | HIDDEN_TEMPLATE_STATUS |
</template>

## Message Inventory

Visible message explanation.
"""

        buckets = FACT_CONTRACT._fact_buckets(
            "CU106", markdown, "modules/normal/CU106/CU106-program-analysis.md"
        )
        serialized = json.dumps(buckets, sort_keys=True)

        self.assertEqual(len(buckets["calculations"]), 1)
        self.assertEqual(buckets["calculations"][0]["target_carrier"], "RESULT")
        for hidden_marker in (
            "HIDDEN-COMMENT",
            "HIDDEN-CONTAINER",
            "HIDDEN-FENCED",
            "HIDDEN-BLOCKQUOTE-FENCE",
            "HIDDEN-INDENTED",
            "HIDDEN-TEMPLATE",
        ):
            with self.subTest(hidden_marker=hidden_marker):
                self.assertNotIn(hidden_marker, serialized)

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_root = Path(temp_dir) / "artifacts"
            analysis_dir = artifact_root / "modules" / "normal" / "CU106"
            analysis_dir.mkdir(parents=True)
            (analysis_dir / "CU106-program-analysis.md").write_text(
                markdown, encoding="utf-8"
            )
            source_pack = require_public_seam("build_reader_first_source_pack")(
                {
                    "document_id": "lossless-hidden-source",
                    "flow_slug": "lossless-hidden-source",
                    "program_set_slug": "cu106",
                    "programs": [
                        {
                            "normalized_name": "CU106",
                            "artifact_root": "modules/normal/CU106",
                        }
                    ],
                },
                artifact_root,
            )
            self.assertIn("HIDDEN-COMMENT-CALC", source_pack)
            self.assertIn("HIDDEN-FENCED-CALC", source_pack)
            self.assertIn("HIDDEN-BLOCKQUOTE-FENCE-TEMPLATE", source_pack)
            self.assertIn("HIDDEN-TEMPLATE-ERROR", source_pack)

    def test_inline_code_html_tokens_and_visible_data_attributes_do_not_hide_sections(
        self,
    ) -> None:
        markdown = """## Program Reading Summary

The source emits literal `<template>` text for documentation.
<span data-state=hidden>VISIBLE-DATA-STATE</span>
<span data-style="display:none">VISIBLE-DATA-STYLE</span>
<span title="x hidden y">VISIBLE-QUOTED-HIDDEN-WORD</span>
<span title="x style=display:none y">VISIBLE-QUOTED-STYLE-WORD</span>
<input hidden>
VISIBLE-AFTER-VOID-INPUT

## Calculation Logic

| Calculation / Assignment | Target Field / Carrier |
| --- | --- |
| Set RESULT from INPUT | RESULT |

## Validation Logic

Visible validation remains present.

## Exception Handling

Visible exception remains present.

## Message Inventory

Visible message inventory remains present.
"""

        buckets = FACT_CONTRACT._fact_buckets("CU106", markdown, "analysis.md")
        surface = FACT_CONTRACT.mask_hidden_html(markdown)

        self.assertEqual(len(buckets["calculations"]), 1)
        self.assertIn("<template>", buckets["summary_contributions"][0]["logic"])
        for visible_marker in (
            "VISIBLE-DATA-STATE",
            "VISIBLE-DATA-STYLE",
            "VISIBLE-QUOTED-HIDDEN-WORD",
            "VISIBLE-QUOTED-STYLE-WORD",
            "VISIBLE-AFTER-VOID-INPUT",
            "Visible validation remains present",
        ):
            with self.subTest(visible_marker=visible_marker):
                self.assertIn(visible_marker, surface)

    def test_fact_tables_preserve_escaped_and_code_span_pipes_without_shifting(
        self,
    ) -> None:
        markdown = r"""## Program Reading Summary

CU106 returns exact operator-visible response literals.

## Calculation Logic

Visible calculation detail.

## Validation Logic

Visible validation detail.

## Exception Handling

Visible exception detail.

## Message Inventory

| Message / Code / Literal | Short Description | Type | Occurrences | Primary Routine(s) | First Seen / Set By | Trigger / Handler Summary | Carrier / Destination | Detail Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AUTH|DECLINED` | Code span literal | response_literal | 1 | VALIDATE | assignment | rejected request | RESPONSE_TEXT | MSG-CU106-PIPE-001 |
| AUTH\|RETRY | Escaped literal | response_literal | 1 | RETRY | assignment | retry request | RESPONSE_TEXT | MSG-CU106-PIPE-002 |
"""

        buckets = FACT_CONTRACT._fact_buckets(
            "CU106", markdown, "modules/normal/CU106/CU106-program-analysis.md"
        )
        messages = buckets["messages"]

        self.assertEqual(len(messages), 2)
        self.assertEqual(
            [message["exact_message_status_literal"] for message in messages],
            ["`AUTH|DECLINED`", r"AUTH\|RETRY"],
        )
        self.assertEqual(
            [message["evidence_reference"] for message in messages],
            ["MSG-CU106-PIPE-001", "MSG-CU106-PIPE-002"],
        )
        self.assertEqual(
            [message["carrier_destination"] for message in messages],
            ["RESPONSE_TEXT", "RESPONSE_TEXT"],
        )
        source_pack = (
            "<!-- BEGIN LOSSLESS PROGRAM CU106: modules/normal/CU106/"
            "CU106-program-analysis.md -->\n"
            f"{markdown}\n"
            "<!-- END LOSSLESS PROGRAM CU106 -->\n"
        )
        reextracted = [
            fact
            for fact in FACT_CONTRACT.extract_source_pack_facts(
                source_pack, ["CU106"]
            )
            if fact.get("fact_type") == "message"
        ]
        self.assertEqual(
            [fact["source_fact_id"] for fact in reextracted],
            [fact["source_fact_id"] for fact in messages],
        )
        self.assertEqual(
            [fact["source_row"] for fact in reextracted],
            [fact["source_row"] for fact in messages],
        )

    def test_shared_table_splitter_handles_backslash_parity_and_backtick_runs(
        self,
    ) -> None:
        splitter = FACT_CONTRACT.split_markdown_table_row

        self.assertEqual(
            [cell.strip() for cell in splitter(r"| A\|B | C |")],
            [r"A\|B", "C"],
        )
        self.assertEqual(
            [cell.strip() for cell in splitter(r"| A\\| B | C |")],
            [r"A\\", "B", "C"],
        )
        self.assertEqual(
            [cell.strip() for cell in splitter("| A | ``B ` | C`` | D |")],
            ["A", "``B ` | C``", "D"],
        )
        self.assertEqual(
            [cell.strip() for cell in splitter("| A | `B | C | D |")],
            ["A", "`B", "C", "D"],
        )
        self.assertEqual(
            [cell.strip() for cell in splitter("| A &#124; B | C |")],
            ["A &#124; B", "C"],
        )
        self.assertEqual(
            [
                cell.strip()
                for cell in splitter(
                    "| [evidence](https://example.invalid/a|b(c)) | C |"
                )
            ],
            ["[evidence](https://example.invalid/a|b(c))", "C"],
        )
        self.assertEqual(
            [cell.strip() for cell in splitter("| [broken](a| B | C |")],
            ["[broken](a", "B", "C"],
        )

    def test_fact_table_rejects_extra_unescaped_cells_instead_of_truncating(
        self,
    ) -> None:
        markdown = """## Program Reading Summary

CU106 summary.

## Calculation Logic

| Calculation / Assignment | Target Field / Carrier |
| --- | --- |
| malformed | unexpected | silently-lost-tail |

## Validation Logic

Visible validation.

## Exception Handling

Visible exception.

## Message Inventory

Visible message inventory.
"""

        with self.assertRaisesRegex(ValueError, "more cells than headers"):
            FACT_CONTRACT._fact_buckets(
                "CU106", markdown, "modules/normal/CU106/CU106-program-analysis.md"
            )


if __name__ == "__main__":
    unittest.main()
