from __future__ import annotations

import importlib.util
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "scripts"
PYTHON_SCRIPT = SCRIPT_DIR / "program_set_core_review.py"
POWERSHELL_WRAPPER = SCRIPT_DIR / "build-program-set-core-review.ps1"
POWERSHELL_MODULE_DIR = SCRIPT_DIR / "powershell"


def load_merger():
    spec = importlib.util.spec_from_file_location(
        "program_set_release_hardening_merger", PYTHON_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load merger: {PYTHON_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MERGER = load_merger()


def overview_markdown(
    claim: str,
    refs: str = "SF-CALL; SF-TARGET",
    programs_cell: str = "CU106, CU101A",
) -> str:
    return f"""## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
| Navigation | {programs_cell} | {claim} | <a id="overview-relation"></a> overview-relation | {refs} |
"""


class ProgramSetReleaseHardeningTests(unittest.TestCase):
    def test_native_wrapper_imports_yaml_module_in_its_own_scope(self) -> None:
        wrapper = POWERSHELL_WRAPPER.read_text(encoding="utf-8")
        self.assertRegex(
            wrapper,
            r"Import-Module\s+.*FlowYaml\.psm1",
            "the wrapper calls Read-FlowYamlFile and must import its defining module",
        )

    def test_powershell_final_gate_rechecks_readiness_and_strict_tokens(self) -> None:
        reconciliation = (
            POWERSHELL_MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")
        markdown = (
            POWERSHELL_MODULE_DIR / "ProgramSetCoreReview.Markdown.psm1"
        ).read_text(encoding="utf-8")
        rendered_surface = reconciliation + markdown
        self.assertIn("ProgramSetCoreReview.Readiness.psm1", reconciliation)
        self.assertIn("Find-FlowProgramArtifactRoot", reconciliation)
        self.assertIn("Get-FlowArtifactStatuses", reconciliation)
        self.assertIn("Get-FlowArtifactReadiness", reconciliation)
        self.assertIn("current program-analysis readiness", reconciliation)
        self.assertIn("ExactTokenCharacterClass", reconciliation)
        self.assertIn("ExactTokenConnectors", reconciliation)
        self.assertIn("Test-FlowConnectorReachesCore", reconciliation)
        self.assertIn("display\\s*:\\s*none", rendered_surface)
        self.assertIn("template|style|script", rendered_surface)
        self.assertIn("fence", rendered_surface)
        self.assertIn("Get-FlowMarkdownIndentationColumns", rendered_surface)

    def test_powershell_relation_and_nested_heading_gates_are_explicit(self) -> None:
        validator = (
            POWERSHELL_MODULE_DIR / "ProgramSetCoreReview.Validator.psm1"
        ).read_text(encoding="utf-8")
        safety = (
            POWERSHELL_MODULE_DIR / "ProgramSetCoreReview.Safety.psm1"
        ).read_text(encoding="utf-8")
        self.assertIn("ProgramSetCoreReview.Safety.psm1", validator)
        self.assertIn("Get-FlowCrossProgramRelationFindings", validator)
        self.assertIn("Test-FlowRelationSupportedBySingleFact", safety)
        self.assertIn("hands?\\s+off", safety)
        self.assertIn("then", safety)
        self.assertIn("#{1,6}", safety)
        self.assertIn("[A-Za-z0-9_@#$-]+", safety)

    def test_exact_literal_rejects_ibmi_token_superstrings(self) -> None:
        for haystack, exact in (
            ("X*PSSR", "*PSSR"),
            ("AUTH-DECLINED-X", "AUTH-DECLINED"),
            ("X-1", "-1"),
        ):
            with self.subTest(haystack=haystack, exact=exact):
                self.assertFalse(MERGER._literal_present(haystack, exact))

        self.assertTrue(MERGER._literal_present("handler `*PSSR`", "*PSSR"))
        self.assertTrue(
            MERGER._literal_present("status AUTH-DECLINED returned", "AUTH-DECLINED")
        )
        self.assertTrue(MERGER._literal_present("status E1.", "E1"))
        self.assertTrue(MERGER._literal_present("message UCC1061.", "UCC1061"))
        for rendered in ("**E1**", "*E1*", "_E1_", "`E1`"):
            with self.subTest(rendered=rendered):
                self.assertTrue(MERGER._literal_present(rendered, "E1"))
        self.assertTrue(
            MERGER._literal_present("status `<ERROR>` returned", "<ERROR>")
        )
        self.assertFalse(
            MERGER._literal_present('<span data-code="<ERROR>">details</span>', "<ERROR>")
        )
        for nonrendered in (
            '<span title="E1">details</span>',
            '<a data-code="E1">details</a>',
            '<img alt="status" data-code="E1">',
            "![E1](https://x.invalid/status.png)",
            "[details](https://x.invalid/?code=E1)",
        ):
            with self.subTest(nonrendered=nonrendered):
                self.assertFalse(MERGER._literal_present(nonrendered, "E1"))

    def test_summary_mapping_headers_match_the_canonical_template(self) -> None:
        template = (
            REPO_ROOT
            / "skills"
            / "legacy-ibmi-flow-analyzer"
            / "templates"
            / "sme-core-review.md"
        ).read_text(encoding="utf-8")
        for header in MERGER._fact_row_headers("Program Set Reading Summary"):
            self.assertIn(f"| {header} ", template)

    def test_nonrendered_tables_and_anchors_cannot_satisfy_coverage(self) -> None:
        header = (
            "| Calculation / Assignment | Program | Routine | "
            "Target Field / Carrier | Source Operands / Carriers | Guard / Branch | "
            "Effect | Supporting Detail | Evidence Status | Review Row ID | "
            "Source Fact Refs |"
        )
        separator = "| " + " | ".join("---" for _ in range(11)) + " |"
        row = (
            "| Set RESULT from INPUT. | CU106 | MAIN | RESULT | INPUT | valid | "
            "returns RESULT | EV-CU106-001 | confirmed | "
            '<a id="review-hidden"></a> review-hidden | SF-CU106-CALC-001 |'
        )
        table = "\n".join((header, separator, row))
        cases = (
            f"```markdown\n{table}\n```",
            "\n".join(
                f"> {line}" for line in ("```markdown", *table.splitlines(), "```")
            ),
            f"```markdown\n```~\n{table}\n```",
            f"```markdown\n`~~\n{table}\n```",
            "\n".join(f"    {line}" for line in table.splitlines()),
            "\n".join(f" \t{line}" for line in table.splitlines()),
            "\n".join(f"  \t{line}" for line in table.splitlines()),
            "\n".join(f"   \t{line}" for line in table.splitlines()),
            f'<div hidden>\n{table}\n</div>',
            f'<div style="display: none">\n{table}\n</div>',
            f'<div style=display:none>\n{table}\n</div>',
            f"<template>\n{table}\n</template>",
            f"<div hidden>\n<div>preface</div>\n{table}\n</div>",
            f'<div style="display:none">\n<div>preface</div>\n{table}\n</div>',
            f"<template>\n<template>preface</template>\n{table}\n</template>",
            f"<details hidden>\n<details>preface</details>\n{table}\n</details>",
        )
        for hidden in cases:
            with self.subTest(container=hidden.splitlines()[0]):
                markdown = f"## Calculation Logic\n\n{hidden}\n"
                self.assertEqual(
                    MERGER._visible_fact_mapping_rows(
                        markdown,
                        "Calculation Logic",
                        "review-hidden",
                        "SF-CU106-CALC-001",
                    ),
                    [],
                )
                self.assertEqual(
                    MERGER._anchor_definition_count(markdown, "review-hidden"), 0
                )

    def test_nonvisible_source_fact_refs_cannot_satisfy_mapping_or_relations(self) -> None:
        header = (
            "| Calculation / Assignment | Program | Routine | "
            "Target Field / Carrier | Source Operands / Carriers | Guard / Branch | "
            "Effect | Supporting Detail | Evidence Status | Review Row ID | "
            "Source Fact Refs |"
        )
        separator = "| " + " | ".join("---" for _ in range(11)) + " |"
        for hidden_ref in (
            '<span data-ref="SF-CU106-CALC-001"></span>',
            "[trace](https://x.invalid/SF-CU106-CALC-001)",
        ):
            row = (
                "| Set RESULT from INPUT. | CU106 | MAIN | RESULT | INPUT | valid | "
                "returns RESULT | source-backed detail for focused SME review | confirmed | "
                '<a id="review-ref"></a> review-ref | '
                f"{hidden_ref} |"
            )
            markdown = f"## Calculation Logic\n\n{header}\n{separator}\n{row}\n"
            with self.subTest(hidden_ref=hidden_ref):
                self.assertEqual(
                    MERGER._visible_fact_mapping_rows(
                        markdown,
                        "Calculation Logic",
                        "review-ref",
                        "SF-CU106-CALC-001",
                    ),
                    [],
                )

        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 calls CU101A.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        markdown = overview_markdown(
            "CU106 calls CU101A.",
            refs='<span data-ref="SF-CALL"></span>',
        )
        findings = MERGER._validate_overview_evidence(markdown, facts, manifest)
        self.assertTrue(any("unsupported" in item.lower() for item in findings), findings)

    def test_literal_or_escaped_anchor_markup_cannot_satisfy_coverage(self) -> None:
        for fake in (
            '`<a id="row-a"></a>` row-a',
            '\\<a id="row-a"></a> row-a',
            '`{#row-a}` row-a',
            '\\{#row-a} row-a',
        ):
            with self.subTest(fake=fake):
                self.assertFalse(MERGER._anchor_present(fake, "row-a"))
                self.assertEqual(MERGER._anchor_definition_count(fake, "row-a"), 0)

    def test_final_gate_reconciles_manifest_with_original_program_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            bundle.mkdir()
            manifest_path = bundle / "program-set-core-input-manifest.yaml"
            local_list = bundle / "program-list.txt"
            original_list = Path(temp_dir) / "requested-programs.txt"
            requested = "CU106\nCU101A\n"
            local_list.write_text(requested, encoding="utf-8")
            original_list.write_text(requested, encoding="utf-8")
            manifest = {
                "program_resolution_profile": {
                    "program_name_normalization": {"case": "upper"}
                },
                "run_profile": {
                    "program_list_source": {
                        "path": str(original_list),
                        "sha256": hashlib.sha256(
                            original_list.read_bytes()
                        ).hexdigest(),
                    }
                },
                "programs": [
                    {"input_name": "CU106", "normalized_name": "CU106"},
                    {"input_name": "CU101A", "normalized_name": "CU101A"},
                ],
            }
            self.assertEqual(
                MERGER.validate_program_list_snapshot(manifest_path, manifest), []
            )

            missing_source = {
                **manifest,
                "run_profile": {},
                "schema_version": "0.4",
                "review_status": "complete_exploratory",
            }
            findings = MERGER.validate_program_list_snapshot(
                manifest_path, missing_source
            )
            self.assertTrue(
                any("program_list_source" in finding for finding in findings),
                findings,
            )

            manifest["programs"] = manifest["programs"][:1]
            findings = MERGER.validate_program_list_snapshot(manifest_path, manifest)
            self.assertTrue(
                any("program-list" in finding.lower() for finding in findings),
                findings,
            )

    def test_forbidden_full_flow_names_are_rejected_at_nested_headings(self) -> None:
        for level in (3, 4, 5, 6):
            with self.subTest(level=level):
                findings = MERGER.validate_review(
                    f"{'#' * level} Transaction Call Map\n\nUnsupported map.\n",
                    {"programs": []},
                )
                self.assertTrue(
                    any(
                        "forbidden full-flow section: Transaction Call Map" in finding
                        for finding in findings
                    ),
                    findings,
                )
        findings = MERGER.validate_review(
            "### transaction call map ###\n\nUnsupported map.\n",
            {"programs": []},
        )
        self.assertTrue(
            any(
                "forbidden full-flow section: Transaction Call Map" in finding
                for finding in findings
            ),
            findings,
        )
        for heading in (
            "# Trigger Inventory",
            "   ## Trigger Inventory",
            "> ## Trigger Inventory",
            "- ## Trigger Inventory",
            "1. ## Trigger Inventory",
            "> - ## Trigger Inventory",
            "Trigger Inventory\n=================",
            "   Trigger Inventory\n   =",
            "Trigger Inventory\n-",
            "> Trigger Inventory\n> =",
            "<h1>Trigger Inventory</h1>",
            "## **Trigger Inventory**",
            "Trigger Inventory\n-----------------",
            "<h2>Trigger Inventory</h2>",
            "## Trigger Inventory {#trigger}",
            "## Trigger&nbsp;Inventory",
            "## **Transaction Call Map**",
        ):
            with self.subTest(heading=heading):
                findings = MERGER.validate_review(
                    f"{heading}\n\nUnsupported map.\n", {"programs": []}
                )
                self.assertTrue(
                    any("forbidden full-flow section" in item for item in findings),
                    findings,
                )

    def test_visible_nested_heading_relation_claims_are_evidence_checked(self) -> None:
        facts = {
            "SF-LOCAL": {
                "source_fact_id": "SF-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates a local request.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        for heading in (
            "### CU106 calls CU101A. SF-LOCAL",
            "#### CU106 → CU101A handoff. SF-LOCAL",
            "##### CU106 sends PAYLOAD to CU101A. SF-LOCAL",
            "###### CU101A is called by CU106. SF-LOCAL",
            "### CU106 then CU101A. SF-LOCAL",
        ):
            with self.subTest(heading=heading):
                findings = MERGER._validate_cross_program_relation_claims(
                    f"## Program Set Reading Summary\n\n{heading}\n",
                    facts,
                    manifest,
                )
                self.assertTrue(
                    any("unsupported" in finding.lower() for finding in findings),
                    findings,
                )

    def test_multi_target_relation_claim_requires_every_named_pair(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "P1",
                "logic": "P1 calls P2.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "P1"},
                {"normalized_name": "P2"},
                {"normalized_name": "P3"},
            ]
        }
        for claim in (
            "P1 calls P2 and P3.",
            "P1 sends PAYLOAD to P2 and P3.",
            "P1 delegates to both P2 and P3.",
            "P1 routes the request to P2, P3.",
            "P1 calls P2 or P3.",
        ):
            with self.subTest(claim=claim):
                findings = MERGER._validate_overview_evidence(
                    overview_markdown(
                        claim,
                        refs="SF-CALL",
                        programs_cell="P1, P2, P3",
                    ),
                    facts,
                    manifest,
                )
                self.assertTrue(
                    any("unsupported" in finding.lower() for finding in findings),
                    findings,
                )

    def test_relation_claim_material_carriers_must_exist_in_same_fact(self) -> None:
        facts = {
            "SF-SEND": {
                "source_fact_id": "SF-SEND",
                "program": "CU106",
                "logic": "CU106 sends APPROVED_FLAG to CU101A via OUT_PARM.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        for invented in (
            "CUSTOMER_PASSWORD",
            "SECRET_QUEUE",
            "DECLINED_FLAG",
            "ADMIN_OVERRIDE",
            "ACCOUNT_BALANCE",
        ):
            with self.subTest(invented=invented):
                claim = f"CU106 sends {invented} to CU101A via OUT_PARM."
                findings = MERGER._validate_overview_evidence(
                    overview_markdown(claim, refs="SF-SEND"),
                    facts,
                    manifest,
                )
                self.assertTrue(
                    any("unsupported" in finding.lower() for finding in findings),
                    findings,
                )

        self.assertEqual(
            MERGER._validate_overview_evidence(
                overview_markdown(
                    "CU106 sends APPROVED_FLAG to CU101A via OUT_PARM.",
                    refs="SF-SEND",
                ),
                facts,
                manifest,
            ),
            [],
        )

    def test_cross_program_relation_requires_one_fact_with_the_same_pair(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 calls EXT001 after validation.",
            },
            "SF-TARGET": {
                "source_fact_id": "SF-TARGET",
                "program": "CU101A",
                "logic": "CU101A handles its own request.",
            },
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }

        findings = MERGER._validate_overview_evidence(
            overview_markdown("CU106 calls CU101A after validation."),
            facts,
            manifest,
        )

        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

    def test_symbolic_and_synonym_sequences_cannot_bypass_relation_gate(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 validates a local request.",
            },
            "SF-TARGET": {
                "source_fact_id": "SF-TARGET",
                "program": "CU101A",
                "logic": "CU101A calculates a local response.",
            },
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        for claim in (
            "CU106 -> CU101A",
            "CU106 hands off to CU101A",
            "CU106 delegates to CU101A",
            "CU106 routes the payload to CU101A",
            "CU106 forwards the request to CU101A",
            "CU106 hands the request off to CU101A",
            "CU106 transfers control to CU101A",
            "CU106 dispatches to CU101A",
            "CU106 then CU101A",
            "CU106 passes the request carrier to CU101A",
            "CU106 returns the response status to CU101A",
            "CU106 produces a source carrier for CU101A",
            "CU106 flows to CU101A",
            "CU106 provides PAYLOAD to CU101A",
            "CU106 delivers PAYLOAD to CU101A",
            "CU106 communicates with CU101A",
            "CU106 exchanges PAYLOAD with CU101A",
            "CU106 depends on CU101A",
            "CU106 continues into CU101A",
            "CU106 maps PAYLOAD to CU101A",
            "CU106 populates INPUT for CU101A",
            "CU106 connects to CU101A",
        ):
            with self.subTest(claim=claim):
                findings = MERGER._validate_overview_evidence(
                    overview_markdown(claim), facts, manifest
                )
                self.assertTrue(
                    any("unsupported" in finding.lower() for finding in findings),
                    findings,
                )

    def test_reverse_direction_fact_cannot_support_a_relation_claim(self) -> None:
        facts = {
            "SF-REVERSE": {
                "source_fact_id": "SF-REVERSE",
                "program": "CU101A",
                "logic": "CU101A calls CU106 after its local validation.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }

        findings = MERGER._validate_overview_evidence(
            overview_markdown(
                "CU106 calls CU101A after validation.", refs="SF-REVERSE"
            ),
            facts,
            manifest,
        )

        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

    def test_passive_producer_consumer_direction_cannot_be_reversed(self) -> None:
        facts = {
            "SF-OPPOSITE": {
                "source_fact_id": "SF-OPPOSITE",
                "program": "CU101A",
                "logic": "CU101A sends the payload to CU106.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        findings = MERGER._validate_overview_evidence(
            overview_markdown(
                "CU101A consumes the payload produced by CU106.",
                refs="SF-OPPOSITE",
            ),
            facts,
            manifest,
        )
        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

        opposite_facts = {
            "SF-OPPOSITE": {
                "source_fact_id": "SF-OPPOSITE",
                "program": "CU106",
                "logic": "CU106 sends the payload to CU101A.",
            }
        }
        for claim in (
            "CU101A output is consumed by CU106",
            "CU101A payload is received by CU106",
            "CU101A payload is routed to CU106",
            "CU101A payload is forwarded to CU106",
            "CU106 consumes CU101A output",
        ):
            with self.subTest(claim=claim):
                findings = MERGER._validate_overview_evidence(
                    overview_markdown(claim, refs="SF-OPPOSITE"),
                    opposite_facts,
                    manifest,
                )
                self.assertTrue(
                    any("unsupported" in finding.lower() for finding in findings),
                    findings,
                )

    def test_negative_relation_claim_requires_negative_source_evidence(self) -> None:
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        positive_facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 calls CU101A.",
            }
        }
        for claim in (
            "CU106 does not call CU101A",
            "CU106 never calls CU101A",
            "CU106 cannot call CU101A",
            "CU106 calls no CU101A",
            "CU101A is not called by CU106",
            "CU101A is never called by CU106",
        ):
            with self.subTest(claim=claim):
                findings = MERGER._validate_overview_evidence(
                    overview_markdown(claim, refs="SF-CALL"),
                    positive_facts,
                    manifest,
                )
                self.assertTrue(
                    any("unsupported" in finding.lower() for finding in findings),
                    findings,
                )

        negative_facts = {
            "SF-NO-CALL": {
                "source_fact_id": "SF-NO-CALL",
                "program": "CU106",
                "logic": "CU106 does not call CU101A; it only validates locally.",
            }
        }
        self.assertEqual(
            MERGER._validate_overview_evidence(
                overview_markdown(
                    "CU106 does not call CU101A", refs="SF-NO-CALL"
                ),
                negative_facts,
                manifest,
            ),
            [],
        )

    def test_navigation_program_cell_cannot_reverse_the_claim_direction(self) -> None:
        facts = {
            "SF-REVERSE": {
                "source_fact_id": "SF-REVERSE",
                "program": "CU101A",
                "logic": "CU101A calls CU106 after its local validation.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        findings = MERGER._validate_overview_evidence(
            overview_markdown(
                "CU106 calls CU101A after validation.",
                refs="SF-REVERSE",
                programs_cell="CU101A, CU106",
            ),
            facts,
            manifest,
        )
        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

    def test_overview_row_requires_its_own_active_anchor_definition(self) -> None:
        facts = {
            "SF-LOCAL": {
                "source_fact_id": "SF-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates locally.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        markdown = overview_markdown(
            "Read each program's local evidence.", refs="SF-LOCAL"
        ).replace(
            '<a id="overview-relation"></a>',
            '`<a id="overview-relation"></a>`',
        )
        markdown += '\n<a id="overview-relation"></a> unrelated anchor\n'

        findings = MERGER._validate_overview_evidence(markdown, facts, manifest)

        self.assertTrue(
            any("requires one unique review anchor" in item for item in findings),
            findings,
        )

    def test_multi_program_overview_relation_must_name_the_supported_pair(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 validates a local request.",
            },
            "SF-TARGET": {
                "source_fact_id": "SF-TARGET",
                "program": "CU101A",
                "logic": "CU101A calculates a local response.",
            },
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        findings = MERGER._validate_overview_evidence(
            overview_markdown("Hands off the request to the next program."),
            facts,
            manifest,
        )
        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

    def test_evidence_identifiers_do_not_create_program_relation_mentions(self) -> None:
        facts = {
            "SF-CU106-LOCAL": {
                "source_fact_id": "SF-CU106-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates a local request.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        markdown = """## Program Set Reading Summary

The consumer remains local; evidence SF-CU106-LOCAL then records RLOG-CU101A-001.
"""
        self.assertEqual(
            MERGER._validate_cross_program_relation_claims(markdown, facts, manifest),
            [],
        )

    def test_multiline_prose_relation_is_checked_as_one_claim(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 validates a local request.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        markdown = """## Program Set Reading Summary

CU106 passes the request carrier
to CU101A. Source fact: SF-CALL.
"""
        findings = MERGER._validate_cross_program_relation_claims(
            markdown, facts, manifest
        )
        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

    def test_explicit_single_fact_relation_can_be_used_for_navigation(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 calls CU101A after validation.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }

        findings = MERGER._validate_overview_evidence(
            overview_markdown(
                "CU106 calls CU101A after validation.", refs="SF-CALL"
            ),
            facts,
            manifest,
        )

        self.assertEqual(findings, [])

    def test_relation_claims_are_checked_outside_the_overview(self) -> None:
        facts = {
            "SF-CALL": {
                "source_fact_id": "SF-CALL",
                "program": "CU106",
                "logic": "CU106 validates a local request.",
            },
            "SF-TARGET": {
                "source_fact_id": "SF-TARGET",
                "program": "CU101A",
                "logic": "CU101A calculates a local response.",
            },
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        markdown = """## Program Set Reading Summary

CU106 calls CU101A and produces its request carrier.

## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local calculation with no cross-program evidence. | CU106 | MAIN | RESULT | INPUT | valid | returns output carrier | RLOG-CU106-001 | confirmed | <a id="calc-local"></a> calc-local | SF-CALL; SF-TARGET |
"""

        findings = MERGER._validate_cross_program_relation_claims(
            markdown, facts, manifest
        )

        self.assertTrue(
            any("unsupported" in finding.lower() for finding in findings), findings
        )

    def test_relation_claims_are_checked_in_all_visible_review_sections(self) -> None:
        facts = {
            "SF-LOCAL": {
                "source_fact_id": "SF-LOCAL",
                "program": "CU106",
                "logic": "CU106 validates locally.",
            }
        }
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        for section in (
            "Sources",
            "Core Completeness Ledger",
            "Coverage Reconciliation",
            "Run Profile",
            "Source Inventory Cache",
            "Notes",
        ):
            with self.subTest(section=section):
                findings = MERGER._validate_cross_program_relation_claims(
                    f"## {section}\n\nCU106 calls CU101A. SF-LOCAL\n",
                    facts,
                    manifest,
                )
                self.assertTrue(
                    any("unsupported" in item.lower() for item in findings), findings
                )

    def test_duplicate_controlled_sections_are_rejected(self) -> None:
        markdown = """## Calculation Logic

First visible section.

## Calculation Logic

Second visible section.
"""
        findings = MERGER.validate_review(markdown, {"programs": []})
        self.assertTrue(
            any(
                "controlled section must appear exactly once: Calculation Logic"
                in item
                for item in findings
            ),
            findings,
        )

    def test_generic_program_order_cannot_be_declared_as_runtime_sequence(self) -> None:
        manifest = {
            "programs": [
                {"normalized_name": "CU106"},
                {"normalized_name": "CU101A"},
            ]
        }
        for claim in (
            "The program list order represents the actual call sequence.",
            "Programs are listed in execution order.",
            "The supplied order is the confirmed call chain.",
            "The ordered program list shows the actual execution sequence.",
            "The SME order proves the call chain.",
            "The navigation order reflects runtime sequence.",
            "Input order establishes runtime sequence.",
            "Program order establishes the execution chain.",
            "The programs execute in the listed order.",
            "The program list order is navigation only, but it represents the actual call sequence.",
            "The program order is not merely navigation; it is the confirmed call chain.",
            "This is not an unconfirmed sequence: programs execute in listed order.",
            "Although order is navigation only, the programs execute in the listed order.",
            "The list does not merely guide navigation—it shows runtime sequence.",
            "The program list does not represent a call chain and it represents the runtime execution order.",
            "The program list does not confirm call order, then it proves the runtime sequence.",
            "The list is not a call chain and the listed order shows runtime execution sequence.",
        ):
            with self.subTest(claim=claim):
                findings = MERGER.validate_review(
                    f"## Program Set Reading Summary\n\n{claim}\n", manifest
                )
                self.assertTrue(
                    any(
                        "navigation order" in finding.lower()
                        or "program order" in finding.lower()
                        for finding in findings
                    ),
                    findings,
                )

        allowed = MERGER.validate_review(
            "## Program Set Reading Summary\n\n"
            "The program list order is navigation only and is not a confirmed "
            "call chain or runtime sequence.\n",
            manifest,
        )
        self.assertFalse(
            any("navigation order" in finding.lower() for finding in allowed),
            allowed,
        )

    def test_modernization_and_service_boundary_decisions_are_rejected(self) -> None:
        for claim in (
            "Modernization decision: extract CU106 as a new microservice service boundary.",
            "Service boundary recommendation: replace CU106 with a cloud service.",
            "Business Rule BR-CU106-001: always migrate this logic to a microservice.",
            "CU106 should become an independent service boundary.",
            "Recommendation: create a microservice around CU106.",
            "The business rule is to decline negative balances.",
            "Convert CU106 into a microservice.",
            "Modernize CU106 as a cloud service.",
            "Architecture recommendation: leave CU106 on IBM i.",
            "BR-CU106-001: decline negative balances.",
            "Carve CU106 into its own microservice.",
            "No uncertainty remains; convert CU106 into a microservice.",
            "Without delay, convert CU106 into a microservice.",
            "This review does not define business rules; convert CU106 into a microservice.",
            "CU106 should not remain monolithic; migrate it to a cloud service.",
            "No business rules are defined. Modernize CU106 as a cloud service.",
            "This review does not recommend a service boundary, but CU106 should become one.",
            "Without proposing a migration, we will convert CU106 into a cloud service.",
            "CU106 should not remain monolithic, but will become a microservice.",
            "There is no recommendation—modernize CU106 as a cloud service.",
            "We do not infer service boundaries and recommend CU106 become a microservice.",
            "This is out of scope and CU106 should be migrated to a cloud service.",
            "We do not define business rules and BR-001: reject inactive accounts.",
            "We do not recommend it, then migrate CU106 to a cloud service.",
        ):
            with self.subTest(claim=claim):
                findings = MERGER.validate_review(
                    f"## Program Set Reading Summary\n\n{claim}\n",
                    {"programs": [{"normalized_name": "CU106"}]},
                )
                self.assertTrue(
                    any(
                        "modernization" in finding.lower()
                        or "architecture" in finding.lower()
                        or "service boundary" in finding.lower()
                        or "business rule" in finding.lower()
                        for finding in findings
                    ),
                    findings,
                )

        findings = MERGER.validate_review(
            "## Program Set Reading Summary\n\n"
            "This review does not define business rules or recommend a service boundary.\n",
            {"programs": [{"normalized_name": "CU106"}]},
        )
        self.assertFalse(
            any("prohibited" in finding.lower() for finding in findings), findings
        )


if __name__ == "__main__":
    unittest.main()
