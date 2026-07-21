from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import (
    write_finalized_program_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "scripts"
BUILD_SCRIPT = SCRIPT_DIR / "build-program-set-core-review.ps1"
VALIDATE_SCRIPT = SCRIPT_DIR / "validate-program-set-core-review.ps1"
MODULE_DIR = SCRIPT_DIR / "powershell"
PYTHON_SCRIPT = SCRIPT_DIR / "program_set_core_review.py"
PROFILE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)
FACT_ID_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "reader_first_fact_identity.json"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
ROUTER = REPO_ROOT / "scripts" / "invoke-windows-tool.ps1"


def load_python_builder():
    spec = importlib.util.spec_from_file_location("flow_core_review", PYTHON_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Python parity implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules["flow_core_review"] = module
    spec.loader.exec_module(module)
    return module


PYTHON_BUILDER = load_python_builder()


def write_artifacts(root: Path) -> None:
    write_finalized_program_artifacts(root, root.name)


def bundle_artifact(output_parent: Path, filename: str) -> Path:
    matches = list(output_parent.glob(f"*--*/{filename}"))
    if len(matches) != 1:
        raise AssertionError(f"expected one {filename} below {output_parent}, got {matches}")
    return matches[0]


class ProgramSetCoreReviewPowerShellTests(unittest.TestCase):
    def test_native_scripts_and_focused_modules_are_present(self) -> None:
        self.assertTrue(BUILD_SCRIPT.is_file())
        self.assertTrue(VALIDATE_SCRIPT.is_file())
        expected = {
            "FlowYaml.psm1",
            "ProgramSetCoreReview.Builder.psm1",
            "ProgramSetCoreReview.Identity.psm1",
            "ProgramSetCoreReview.Input.psm1",
            "ProgramSetCoreReview.Markdown.psm1",
            "ProgramSetCoreReview.Readiness.psm1",
            "ProgramSetCoreReview.Reconciliation.psm1",
            "ProgramSetCoreReview.Safety.psm1",
            "ProgramSetCoreReview.Validator.psm1",
        }
        self.assertTrue(expected.issubset({path.name for path in MODULE_DIR.glob("*.psm1")}))

        for path in [BUILD_SCRIPT, VALIDATE_SCRIPT, *MODULE_DIR.glob("*.psm1")]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("Copyright 2026 Leo L Zhang", text)
            self.assertLessEqual(len(text.splitlines()), 800, path)
            self.assertNotRegex(text, r"(?i)(?:^|[&\s])(py(?:thon)?(?:\.exe)?)(?:\s|$)")
            self.assertNotIn("ConvertFrom-Yaml", text)

    def test_cli_contract_and_identity_rules_are_explicit(self) -> None:
        build = BUILD_SCRIPT.read_text(encoding="utf-8")
        validator = VALIDATE_SCRIPT.read_text(encoding="utf-8")
        builder_module = (MODULE_DIR / "ProgramSetCoreReview.Builder.psm1").read_text(
            encoding="utf-8"
        )
        for option in (
            "review-name",
            "programs-file",
            "working-root",
            "output-root",
            "artifact-repo-mode",
            "source-root",
            "inventory-dir",
            "program-first",
            "profile",
            "output-dir",
            "working-branch",
            "delivery-root",
            "force-rescan-file",
        ):
            self.assertIn(option, build + builder_module)
        self.assertIn("manifest", validator)
        self.assertIn("review", validator)
        self.assertIn("ToUpperInvariant", builder_module)
        self.assertNotIn("TrimStart('@')", builder_module)
        self.assertIn("StringComparer]::Ordinal", builder_module)

    def test_native_preparer_is_reader_first_and_never_writes_a_review(self) -> None:
        build = BUILD_SCRIPT.read_text(encoding="utf-8")
        builder = (MODULE_DIR / "ProgramSetCoreReview.Builder.psm1").read_text(
            encoding="utf-8"
        )
        readiness = (MODULE_DIR / "ProgramSetCoreReview.Readiness.psm1").read_text(
            encoding="utf-8"
        )
        native_preparer = builder + readiness
        validator = (MODULE_DIR / "ProgramSetCoreReview.Validator.psm1").read_text(
            encoding="utf-8"
        )
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")

        self.assertIn("Invoke-ContractValidation", native_preparer)
        self.assertIn("ProgramAnalysisContract.Validation.psm1", native_preparer)
        self.assertIn("approved_with_non_blocking_tbd", native_preparer)
        self.assertIn("validator_status", native_preparer)
        self.assertIn("analysis_status", native_preparer)
        self.assertIn("conflicting", native_preparer)
        self.assertIn("program identity", native_preparer.lower())
        self.assertIn("ready_for_synthesis", builder)
        self.assertIn("blocked_artifact_readiness", builder)
        self.assertIn("artifact_readiness = $artifactReadiness", builder)
        self.assertIn("merge_coverage = $mergeCoverage", builder)
        self.assertIn("core_review_profiles", builder)
        self.assertIn("Resolve-FlowOutputDirectory", builder)
        self.assertIn('canonical_filename = "$folderSlug--sme-core-review.md"', builder)
        for artifact in (
            "program-list.txt",
            "program-set-core-input-manifest.yaml",
            "program-set-artifact-readiness.yaml",
            "program-set-reader-first-source-pack.md",
            "program-set-core-facts.yaml",
            "program-set-core-coverage.yaml",
        ):
            self.assertIn(artifact, builder)

        self.assertNotIn("ConvertTo-FlowCoreReviewSkeleton", builder)
        self.assertNotRegex(builder, r"WriteAllText\([^\n]*sme-core-review\.md")
        self.assertIn("never writes a draft or formal SME core review", build)
        self.assertIn(
            "existing formal review must be explicitly archived before rebuilding",
            (MODULE_DIR / "ProgramSetCoreReview.Identity.psm1").read_text(
                encoding="utf-8"
            ),
        )

        for coverage_gate in (
            "source_fact_id",
            "review_anchor",
            "review_exact_token",
            "expected_source_fact_count",
            "coverage_item_count",
            "status_counts",
            "excluded_non_core",
            "remains pending",
        ):
            self.assertIn(coverage_gate, validator)
        self.assertIn("Trigger Inventory", validator)
        self.assertIn("navigation order", validator)
        placeholder_pattern = validator.split("$script:PlaceholderPattern", 1)[
            1
        ].split("\n", 1)[0].lower()
        self.assertNotIn("|pending", placeholder_pattern)
        self.assertNotIn("(?:placeholder|", placeholder_pattern)
        placeholder_cell = validator.split(
            "function Test-ReviewPlaceholderCell", 1
        )[1].split("function ", 1)[0].lower()
        self.assertNotIn("'pending'", placeholder_cell)
        for parity_gate in (
            "complete_exploratory",
            "Test-FlowReviewIdentity",
            "Get-FlowSourcePackProgramBlock",
            "Message Coverage Control",
            "Coverage Reconciliation",
            "review anchor/fact row",
            "link-only",
            "routine_rlog",
            "Carrier / Destination",
            "coverage items and coverage_items mirrors differ",
            "coverage coverage_status must be complete",
            "Cross-Program Processing Overview row lacks source fact references",
        ):
            self.assertIn(parity_gate, validator)
        for reconciliation_gate in (
            "source pack differs from the current validated program-analysis inputs",
            "source-pack fact",
            "Test-FlowExactLiteral",
            "Get-FlowAnchorDefinitionCount",
            "Get-FlowFactSemanticValues",
        ):
            self.assertIn(reconciliation_gate, reconciliation)

    def test_validator_cli_accepts_the_complete_merger_bundle(self) -> None:
        validator = VALIDATE_SCRIPT.read_text(encoding="utf-8")
        for option in ("sourcepack", "corefacts", "coverage"):
            self.assertIn(option, validator)

    def test_reconciliation_requires_thematic_table_source_cells(self) -> None:
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")
        semantic_function = reconciliation.split(
            "function Get-FlowFactSemanticValues", 1
        )[1].split("function ", 1)[0]
        early_return = next(
            line
            for line in semantic_function.splitlines()
            if "return @()" in line
        )

        self.assertNotIn("thematic_table", early_return)
        self.assertIn("source_row", semantic_function)
        self.assertIn("row.Keys", semantic_function)

    def test_powershell_coverage_requires_visible_same_row_fact_bindings(self) -> None:
        validator = (
            MODULE_DIR / "ProgramSetCoreReview.Validator.psm1"
        ).read_text(encoding="utf-8")
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")

        self.assertIn("function Remove-FlowHtmlComments", reconciliation)
        self.assertIn("function Get-FlowFactMappingRows", reconciliation)
        self.assertIn("Review Row ID", reconciliation)
        self.assertIn("Source Fact Refs", reconciliation)
        self.assertIn("[A-Za-z0-9_@#$-]+", reconciliation)
        self.assertIn("visible required-header data row", validator)
        self.assertIn("SetEquals", validator)

    def test_native_flow_identity_and_run_mode_checks_match_python_contract(self) -> None:
        builder = (
            MODULE_DIR / "ProgramSetCoreReview.Builder.psm1"
        ).read_text(encoding="utf-8")
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")

        identity_function = builder.split(
            "function Get-FlowIdentitySlug", 1
        )[1].split("function ", 1)[0]
        self.assertIn("ConvertTo-FlowReviewSlug $Value", identity_function)
        self.assertIn("Substring(0, 64)", identity_function)
        self.assertIn("[Text.Encoding]::UTF8.GetBytes($Value)", identity_function)
        self.assertIn("[Security.Cryptography.SHA256]::Create()", identity_function)
        self.assertIn("Substring(0, 8)", identity_function)
        self.assertIn("Get-FlowIdentitySlug $flowIdentity", builder)
        self.assertIn(
            "$flowIdentity = if ($FlowSlug) { $FlowSlug } else { $ReviewName }",
            builder,
        )

        readiness_function = reconciliation.split(
            "function Get-FlowRevalidatedManifest", 1
        )[1].split("function ", 1)[0]
        for contract_token in (
            "cross_run_reuse",
            "reuse_policy",
            "approved_document_repo_clone",
            "current_run_only",
            "does not match artifact repo mode",
        ):
            self.assertIn(contract_token, readiness_function)

    def test_native_fact_extraction_matches_python_identity_and_field_contract(
        self,
    ) -> None:
        builder = (
            MODULE_DIR / "ProgramSetCoreReview.Builder.psm1"
        ).read_text(encoding="utf-8")
        identity_function = builder.split(
            "function Get-FlowStableFactId", 1
        )[1].split("function ", 1)[0]
        fact_function = builder.split(
            "function New-FlowSourceFact", 1
        )[1].split("function ", 1)[0]
        section_function = builder.split(
            "function Get-FlowSectionFacts", 1
        )[1].split("function ", 1)[0]

        for token in (
            "$FactType",
            "ConvertTo-FlowFactIdentityText",
            '"$programKey`n$sectionKey`n$factTypeKey`n$sourceKey"',
            "Substring(0, 10)",
            "ToUpperInvariant()",
            '"SF-$programKey-$factTypeSlug-$digest"',
        ):
            self.assertIn(token, identity_function)
        for field in (
            "source_artifact",
            "source_text",
            "source_row",
            "source_cells",
            "calculation",
            "target_carrier",
            "source_carriers",
            "exact_code_status",
            "validation_type",
            "exception_path",
            "fields_messages_set",
            "exact_message_status_literal",
            "message_type",
            "generic_handler_token",
            "source_headers",
        ):
            self.assertIn(field, fact_function)
        for extraction_gate in (
            "Test-FlowMaterialTableRow",
            "Test-FlowSpecializedTable",
            "thematic_table",
            "RLOG / Routine",
            "metadata",
            "not applicable",
            "seenFactIds",
        ):
            self.assertIn(extraction_gate, section_function + builder)
        self.assertNotIn("review_exact_token =", fact_function)

        vectors = json.loads(FACT_ID_FIXTURE.read_text(encoding="utf-8"))["vectors"]
        self.assertTrue(vectors)
        self.assertTrue(
            all(
                re.fullmatch(r"SF-[A-Z0-9_@#$.-]+-[A-Z0-9_]+-[A-F0-9]{10}", row["expected_source_fact_id"])
                for row in vectors
            )
        )

    def test_native_program_list_trust_root_is_preserved_and_reconciled(self) -> None:
        wrapper = BUILD_SCRIPT.read_text(encoding="utf-8")
        builder = (
            MODULE_DIR / "ProgramSetCoreReview.Builder.psm1"
        ).read_text(encoding="utf-8")
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")
        validator = (
            MODULE_DIR / "ProgramSetCoreReview.Validator.psm1"
        ).read_text(encoding="utf-8")

        self.assertIn("-ProgramsFile ([IO.Path]::GetFullPath($options.ProgramsFile))", wrapper)
        manifest_function = builder.split(
            "function New-FlowCoreReviewManifest", 1
        )[1].split("function ", 1)[0]
        for token in (
            "[AllowNull()][string]$ProgramsFile",
            "program_list_source",
            "[IO.Path]::GetFullPath($ProgramsFile)",
            "SHA256",
            "sha256",
        ):
            self.assertIn(token, manifest_function)

        snapshot_function = reconciliation.split(
            "function Test-FlowProgramListSnapshot", 1
        )[1].split("function ", 1)[0]
        for token in (
            "program-list.txt",
            "input_name",
            "normalized_name",
            "program_list_source",
            "IsPathRooted",
            "SHA256",
            "original SME program list",
            "ordered manifest program inputs",
        ):
            self.assertIn(token, snapshot_function)
        self.assertIn(
            "Test-FlowProgramListSnapshot $ManifestPath $manifest", validator
        )

    def test_native_markdown_parity_gates_are_shared_and_fail_closed(self) -> None:
        markdown = (
            MODULE_DIR / "ProgramSetCoreReview.Markdown.psm1"
        ).read_text(encoding="utf-8")
        builder = (
            MODULE_DIR / "ProgramSetCoreReview.Builder.psm1"
        ).read_text(encoding="utf-8")
        validator = (
            MODULE_DIR / "ProgramSetCoreReview.Validator.psm1"
        ).read_text(encoding="utf-8")
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")
        safety = (
            MODULE_DIR / "ProgramSetCoreReview.Safety.psm1"
        ).read_text(encoding="utf-8")

        self.assertIn("function Split-FlowMarkdownTableRow", markdown)
        self.assertIn("function Test-FlowMarkdownClosingCodeRun", markdown)
        self.assertIn("function Test-FlowMarkdownClosingLinkDestination", markdown)
        self.assertIn("$codeFenceLength", markdown)
        self.assertIn("$linkDestinationDepth", markdown)
        self.assertIn("function Remove-FlowNonRenderedMarkdown", markdown)
        self.assertIn("Remove-FlowNonRenderedMarkdown $SectionText", builder)
        self.assertIn("Assert-ReadinessTrustedPath $Root $resolved", builder)
        self.assertNotIn(".Split('|')", builder + validator + reconciliation + safety)
        self.assertIn("$seenKeys.Add($key)", validator)
        self.assertIn("function Get-FlowReviewRowReconciliationFindings", reconciliation)
        self.assertIn("canonical-looking fact row", reconciliation)
        self.assertIn("into the wrong section", reconciliation)
        self.assertIn("function Get-FlowUnmappedCoreProseFindings", safety)
        for relation in ("supplies?", "yields?", "emits?", "writes?", "queues?", "publishes?", "requests?", "chains?", "precedes?", "follows?"):
            self.assertIn(relation, safety)
        self.assertIn(
            "Get-FlowReviewRowReconciliationFindings $visibleMarkdown $factById $itemById $Manifest",
            validator,
        )

    def test_native_final_reader_first_audit_guards_are_explicit(self) -> None:
        markdown = (MODULE_DIR / "ProgramSetCoreReview.Markdown.psm1").read_text(
            encoding="utf-8"
        )
        builder = (MODULE_DIR / "ProgramSetCoreReview.Builder.psm1").read_text(
            encoding="utf-8"
        )
        reconciliation = (
            MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
        ).read_text(encoding="utf-8")
        safety = (MODULE_DIR / "ProgramSetCoreReview.Safety.psm1").read_text(
            encoding="utf-8"
        )
        validator = (MODULE_DIR / "ProgramSetCoreReview.Validator.psm1").read_text(
            encoding="utf-8"
        )

        for scanner in (
            "Get-FlowMarkdownClosingLinkDestinationIndex",
            "Get-FlowMarkdownHtmlTokens",
            "Get-FlowMarkdownHtmlAttributes",
            "Remove-FlowMarkdownLinkDestinations",
            "Remove-FlowMarkdownHtmlTags",
            "Remove-FlowMarkdownInlineCodeForStructure",
            "ConvertTo-FlowMarkdownStructuralLine",
        ):
            self.assertIn(f"function {scanner}", markdown)
        self.assertIn("FlowMarkdownVoidHtmlTags", markdown)
        self.assertIn("[string]$attribute.Name, 'hidden'", markdown)
        self.assertIn("[string]$attribute.Name, 'style'", markdown)
        self.assertIn("function Test-FlowMarkdownTableHeaderAndSeparator", markdown)
        for consumer in (builder, reconciliation, safety):
            self.assertIn("Test-FlowMarkdownTableHeaderAndSeparator", consumer)
        self.assertIn("canonical fact table separator has", reconciliation)
        self.assertIn("expected exactly", reconciliation)
        semantic_function = reconciliation.split(
            "function Test-FlowSummarySemanticsPreserved", 1
        )[1].split("function ", 1)[0]
        self.assertIn("'logic'", semantic_function)
        self.assertIn("'source_text'", semantic_function)
        self.assertIn("Get-FlowSummarySemanticTerms", semantic_function)
        self.assertIn("source summary semantics", validator)
        self.assertIn("function Get-FlowRelationProgramCandidates", safety)
        self.assertIn("function Test-FlowRelationBridge", safety)
        self.assertIn("function Test-FlowClaimHasRelation", safety)
        candidate_function = safety.split(
            "function Get-FlowRelationProgramCandidates", 1
        )[1].split("function ", 1)[0]
        self.assertIn("candidateStopWords", candidate_function)
        self.assertIn("'MAIN'", candidate_function)
        self.assertIn("'SME'", candidate_function)
        cross_program = safety.split(
            "function Get-FlowCrossProgramRelationFindings", 1
        )[1].split("function ", 1)[0]
        self.assertNotIn("$known.Count -lt 2", cross_program)
        self.assertIn("$claimPrograms", cross_program)
        self.assertIn("ConvertTo-FlowUnquotedMarkdownSurface $block", safety)
        self.assertIn("ExpectedCellCount", validator)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_native_markdown_tokenizer_literal_and_front_matter_guards(self) -> None:
        probe = r'''
Import-Module $env:MARKDOWN_MODULE -Force
Import-Module $env:RECONCILIATION_MODULE -Force
Import-Module $env:SAFETY_MODULE -Force
Import-Module $env:VALIDATOR_MODULE -Force
$cells = @(Split-FlowMarkdownTableRow '| `AUTH|DECLINED` | AUTH\|DECLINED | [evidence](https://example.invalid/a|b) |')
if ($cells.Count -ne 3) { throw "table tokenizer returned $($cells.Count) cells" }
$unmatchedCode = @(Split-FlowMarkdownTableRow '| `AUTH|DECLINED | next |')
if ($unmatchedCode.Count -ne 3) { throw 'unmatched code opener swallowed table delimiters' }
$unmatchedLink = @(Split-FlowMarkdownTableRow '| [evidence](https://example.invalid/a|b | next |')
if ($unmatchedLink.Count -ne 3) { throw 'unmatched link destination swallowed table delimiters' }
if (-not (Test-FlowExactLiteral '**AUTH\|DECLINED**' 'AUTH|DECLINED')) { throw 'rendered literal normalization diverged' }
if (-not (Test-FlowExactLiteral '`<ERROR>`' '<ERROR>')) { throw 'code-span literal content was lost' }
foreach ($hiddenRef in @('[trace](https://x.invalid/a_(b)/SF-FAKE)', '<span title="x>SF-FAKE">visible</span>')) {
    if ((ConvertTo-FlowVisibleInlineText $hiddenRef).Contains('SF-FAKE')) { throw "hidden inline ref leaked: $hiddenRef" }
}
$visibleHtml = @'
Literal `<template>` remains.
<span data-state=hidden>VISIBLE-DATA-STATE</span>
<span data-style="display:none">VISIBLE-DATA-STYLE</span>
<span title="x hidden y">VISIBLE-QUOTED-HIDDEN</span>
<span title="x style=display:none y">VISIBLE-QUOTED-STYLE</span>
<input hidden>
VISIBLE-AFTER-VOID-INPUT
'@
$visibleSurface = Remove-FlowNonRenderedMarkdown $visibleHtml
foreach ($marker in @('<template>', 'VISIBLE-DATA-STATE', 'VISIBLE-DATA-STYLE', 'VISIBLE-QUOTED-HIDDEN', 'VISIBLE-QUOTED-STYLE', 'VISIBLE-AFTER-VOID-INPUT')) {
    if (-not $visibleSurface.Contains($marker)) { throw "visible Markdown was hidden: $marker" }
}
$nestedFences = @'
> ```html
> <template>HIDDEN-BLOCKQUOTE-TEMPLATE</template>
> ```
- ~~~html
  <template>HIDDEN-LIST-TEMPLATE</template>
  ~~~
VISIBLE-AFTER-NESTED-FENCES
'@
$nestedSurface = Remove-FlowNonRenderedMarkdown $nestedFences
if ($nestedSurface.Contains('HIDDEN-BLOCKQUOTE-TEMPLATE') -or $nestedSurface.Contains('HIDDEN-LIST-TEMPLATE') -or -not $nestedSurface.Contains('VISIBLE-AFTER-NESTED-FENCES')) { throw 'container-nested fenced code affected visible structure' }
if (Test-FlowMarkdownTableHeaderAndSeparator '| A | B |' '| --- |') { throw 'mismatched table separator arity passed' }
$summaryFact = [ordered]@{ fact_type = 'summary_contribution'; program = 'PGM1'; logic = 'PGM1 preserves AUTH_STATUS semantics.'; source_text = 'PGM1 preserves AUTH_STATUS semantics.' }
if (-not (Test-FlowSummarySemanticsPreserved $summaryFact @('PGM1 keeps AUTH_STATUS visible for the reader.'))) { throw 'material summary semantics were rejected' }
if (Test-FlowSummarySemanticsPreserved $summaryFact @('PGM1 has generic reader-facing context and available evidence.')) { throw 'generic prose satisfied summary semantics' }
$validator = Get-Module ProgramSetCoreReview.Validator
$duplicate = "---`ndocument_id: expected`ndocument_id: attacker`nprograms:`n  - PGM1`n---`n# Review"
$metadata = & $validator { param($text) Get-FlowReviewFrontMatter $text } $duplicate
if ($null -ne $metadata) { throw 'duplicate front-matter key was accepted' }
$forbidden = @('Trigger Inventory', 'Transaction Call Map', 'Replay', 'Capability Seeds')
foreach ($heading in @('## Trigger Inventory:', '## 1. Trigger Inventory', '## Transaction Call Map (source-confirmed)', '## Replay / Notes', '## Capability Seeds 🌱')) {
    if (-not @(Get-FlowForbiddenHeadingFindings $heading $forbidden).Count) { throw "forbidden heading variant passed: $heading" }
}
foreach ($decision in @('## Modernization Recommendation', '## Architecture Decision', 'Modernization recommendation — migrate it')) {
    if (-not @(Get-FlowProhibitedContentFindings $decision).Count) { throw "prohibited decision passed: $decision" }
}
foreach ($claim in @('Programs run in supplied order.', 'First listed precedes next at runtime.', 'SME input sequence is actual call path.', 'The ordered list defines what runs first and follows.', 'Navigation order equals runtime order.')) {
    if (-not @(Get-FlowProgramOrderFindings $claim).Count) { throw "program-order claim passed: $claim" }
}
$relationManifest = [ordered]@{ programs = @([ordered]@{ normalized_name = 'PGM1' }, [ordered]@{ normalized_name = 'PGM2' }) }
$relationFacts = [Collections.Hashtable]::new([StringComparer]::Ordinal)
foreach ($claim in @('PGM1 supplies PGM2.', 'PGM1 yields PGM2.', 'PGM1 emits PGM2.', 'PGM1 writes output for PGM2.', 'PGM1 starts PGM2.', 'PGM1 runs PGM2.', 'PGM1 queues work for PGM2.', 'PGM1 publishes to PGM2.', 'PGM1 requests processing from PGM2.', 'PGM1 chains to PGM2.', 'PGM1 precedes PGM2.', 'PGM1 follows PGM2.')) {
    if (-not @(Get-FlowCrossProgramRelationFindings $claim $relationFacts $relationManifest).Count) { throw "relation synonym passed: $claim" }
}
$proseManifest = [ordered]@{ programs = @([ordered]@{ normalized_name = 'PGM1' }); core_review_profile = [ordered]@{ include_message_inventory = $true } }
$unmapped = "## Calculation Logic`n`nPGM1 always sets INTERNAL-FLAG to X9 whenever amount is positive."
if (-not @(Get-FlowUnmappedCoreProseFindings $unmapped $proseManifest).Count) { throw 'unreferenced deterministic core prose passed' }
$quotedUnmapped = "## Calculation Logic`n`n> **Observed:** PGM1 always sets SECRET_FLAG to X9."
if (-not @(Get-FlowUnmappedCoreProseFindings $quotedUnmapped $proseManifest).Count) { throw 'blockquoted deterministic core prose passed' }
$singleManifest = [ordered]@{ programs = @([ordered]@{ normalized_name = 'PGM1' }) }
$externalFacts = [Collections.Hashtable]::new([StringComparer]::Ordinal)
$externalFacts['SF-EXT'] = [ordered]@{ source_fact_id = 'SF-EXT'; program = 'PGM1'; logic = 'PGM1 calls EXT999 after validation.' }
if (@(Get-FlowCrossProgramRelationFindings "PGM1 calls EXT999. SF-LOCAL" $relationFacts $singleManifest).Count -eq 0) { throw 'unsupported external relation passed' }
if (@(Get-FlowCrossProgramRelationFindings "PGM1 calls EXT999 after validation. SF-EXT" $externalFacts $singleManifest).Count) { throw 'source-backed external relation failed' }
$localManifest = [ordered]@{ programs = @([ordered]@{ normalized_name = 'PGM1' }, [ordered]@{ normalized_name = 'PGM2' }) }
$localFacts = [Collections.Hashtable]::new([StringComparer]::Ordinal); $localFacts['SF-LOCAL'] = [ordered]@{ source_fact_id = 'SF-LOCAL'; program = 'PGM1'; logic = 'PGM1 runs local validation.' }
if (@(Get-FlowCrossProgramRelationFindings "PGM1 runs local validation; PGM2 calculates its own response. SF-LOCAL" $localFacts $localManifest).Count) { throw 'local run invented a cross-program relation' }
if (@(Get-FlowCrossProgramRelationFindings "PGM1 runs local validation while PGM2 calculates its own response. SF-LOCAL" $localFacts $localManifest).Count) { throw 'local run clause invented a cross-program relation' }
if (@(Get-FlowCrossProgramRelationFindings "PGM1 MAIN records each local trigger for SME review. SF-LOCAL" $localFacts $singleManifest).Count) { throw 'MAIN or SME was treated as an external program' }
$hidden = @'
```text
| Fake | Row |
| --- | --- |
| AUTH | DECLINED |
```
    ## Fake Heading
<div hidden>
| Hidden | Row |
</div>
visible
'@
$surface = Remove-FlowNonRenderedMarkdown $hidden
if ($surface.Contains('AUTH') -or $surface.Contains('Fake Heading') -or $surface.Contains('Hidden')) { throw 'non-rendered source content leaked' }
$invented = @'
## Program Set Reading Summary
| Program | Scope / Reader-First Contribution | Artifact Readiness | Coverage | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- |
| PGM1 | Reader-useful calculation validation exception details | ready | complete | <a id="invented-row"></a> invented-row | SF-FAKE |
'@
$facts = [Collections.Hashtable]::new([StringComparer]::Ordinal)
$items = [Collections.Hashtable]::new([StringComparer]::Ordinal)
$reverseFindings = @(Get-FlowReviewRowReconciliationFindings $invented $facts $items ([ordered]@{}))
if (-not @($reverseFindings | Where-Object { $_ -match 'unknown source fact SF-FAKE' }).Count) { throw 'invented review row passed reverse reconciliation' }
$badSeparator = $invented.Replace('| --- | --- | --- | --- | --- | --- |', '| --- |')
$separatorFindings = @(Get-FlowReviewRowReconciliationFindings $badSeparator $facts $items ([ordered]@{}))
if (-not @($separatorFindings | Where-Object { $_ -match 'separator has 1 cells; expected exactly 6' }).Count) { throw 'mismatched separator lacked a canonical finding' }
'''
        environment = {
            **os.environ,
            "MARKDOWN_MODULE": str(
                MODULE_DIR / "ProgramSetCoreReview.Markdown.psm1"
            ),
            "RECONCILIATION_MODULE": str(
                MODULE_DIR / "ProgramSetCoreReview.Reconciliation.psm1"
            ),
            "SAFETY_MODULE": str(
                MODULE_DIR / "ProgramSetCoreReview.Safety.psm1"
            ),
            "VALIDATOR_MODULE": str(
                MODULE_DIR / "ProgramSetCoreReview.Validator.psm1"
            ),
        }
        result = subprocess.run(
            [POWERSHELL, "-NoProfile", "-Command", probe],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_native_fact_identity_matches_fixed_vectors(self) -> None:
        vectors = json.loads(FACT_ID_FIXTURE.read_text(encoding="utf-8"))["vectors"]
        probe = """
Import-Module $env:FACT_BUILDER_MODULE -Force
$module = Get-Module ProgramSetCoreReview.Builder
& $module {
    Get-FlowStableFactId $env:FACT_PROGRAM $env:FACT_SECTION $env:FACT_TYPE $env:FACT_SOURCE
}
"""
        for vector in vectors:
            environment = {
                **os.environ,
                "FACT_BUILDER_MODULE": str(
                    MODULE_DIR / "ProgramSetCoreReview.Builder.psm1"
                ),
                "FACT_PROGRAM": vector["program"],
                "FACT_SECTION": vector["section"],
                "FACT_TYPE": vector["fact_type"],
                "FACT_SOURCE": vector["source_text"],
            }
            result = subprocess.run(
                [POWERSHELL, "-NoProfile", "-Command", probe],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), vector["expected_source_fact_id"])

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_preserves_case_sensitive_identity_for_custom_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            working = temp / "delivery"
            output = temp / "review"
            programs = temp / "programs.txt"
            profile = temp / "delivery-profile.yaml"
            working.mkdir()
            programs.write_text("abc\nABC\n", encoding="utf-8")
            profile.write_text(
                PROFILE.read_text(encoding="utf-8").replace(
                    "case: upper", "case: preserve"
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(BUILD_SCRIPT),
                    "--review-name",
                    "Case-sensitive identity",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(working),
                    "--profile",
                    str(profile),
                    "--output-dir",
                    str(output),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = PYTHON_BUILDER.load_yaml(
                bundle_artifact(output, "program-set-core-input-manifest.yaml")
            )
            self.assertEqual(
                [entry["normalized_name"] for entry in manifest["programs"]],
                ["abc", "ABC"],
            )
            self.assertEqual(
                [entry["run_resolution"] for entry in manifest["programs"]],
                ["pending_source", "pending_source"],
            )

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_router_falls_back_to_native_builder_without_python(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command shims require a Windows host")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            shims = temp / "shims"
            shims.mkdir()
            for command in ("py.cmd", "python.cmd"):
                (shims / command).write_text("@exit /b 9009\r\n", encoding="ascii")
            working = temp / "delivery"
            output = temp / "review"
            programs = temp / "programs.txt"
            write_artifacts(
                working / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            )
            programs.write_text("CC050\n", encoding="utf-8")
            environment = dict(os.environ)
            environment["PATH"] = str(shims) + os.pathsep + environment.get("PATH", "")

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROUTER),
                    "BuildProgramSetCoreReview",
                    "--review-name",
                    "Router fallback",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(working),
                    "--profile",
                    str(PROFILE),
                    "--output-dir",
                    str(output),
                    "--program-first",
                ],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(
                bundle_artifact(output, "program-set-core-input-manifest.yaml").is_file()
            )

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_router_passes_build_prefix_to_py_launcher(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command shims require a Windows host")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            shims = temp / "shims"
            shims.mkdir()
            log = temp / "py-arguments.log"
            (shims / "py.cmd").write_text(
                '@echo %*>>"%ROUTER_LOG%"\r\n@exit /b 0\r\n',
                encoding="ascii",
            )
            environment = dict(os.environ)
            environment["PATH"] = str(shims) + os.pathsep + environment.get(
                "PATH", ""
            )
            environment["ROUTER_LOG"] = str(log)

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROUTER),
                    "BuildProgramSetCoreReview",
                    "--review-name",
                    "Prefix probe",
                ],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            invocations = log.read_text(encoding="ascii").splitlines()
            self.assertGreaterEqual(len(invocations), 2)
            self.assertIn("program_set_core_review.py build --review-name", invocations[-1])

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_matches_python_manifest_contract_without_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            working = temp / "delivery"
            output = temp / "review"
            programs = temp / "programs.txt"
            write_artifacts(
                working / "modules" / "CAP-ID-0003-normal_program" / "@CU118"
            )
            programs.write_text("@cu118\nCU118\n@cu118\n", encoding="utf-8")

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(BUILD_SCRIPT),
                    "--review-name",
                    "Card Auth",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(working),
                    "--profile",
                    str(PROFILE),
                    "--output-dir",
                    str(output),
                    "--working-branch",
                    "develop-leo",
                    "--program-first",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest_path = bundle_artifact(
                output, "program-set-core-input-manifest.yaml"
            )
            manifest = PYTHON_BUILDER.load_yaml(manifest_path)
            entries = manifest["programs"]
            source = manifest["run_profile"]["program_list_source"]
            self.assertEqual(Path(source["path"]), programs.resolve())
            self.assertEqual(
                source["sha256"],
                hashlib.sha256(programs.read_bytes()).hexdigest(),
            )
            self.assertEqual(entries[0]["normalized_name"], "@CU118")
            self.assertEqual(entries[0]["run_resolution"], "analyzed_this_run")
            self.assertEqual(entries[1]["normalized_name"], "CU118")
            self.assertEqual(entries[1]["run_resolution"], "pending_source")
            self.assertEqual(entries[2]["run_resolution"], "reused_same_run")
            self.assertTrue(manifest["run_profile"]["program_first"])
            bundle = manifest_path.parent
            readiness = PYTHON_BUILDER.load_yaml(
                bundle / "program-set-artifact-readiness.yaml"
            )
            self.assertEqual(
                [entry["program"] for entry in readiness["programs"]],
                ["@CU118", "CU118"],
            )
            self.assertEqual(
                readiness["programs"][0]["artifact_readiness"]["validator_status"],
                "passed",
            )
            self.assertEqual(
                readiness["programs"][0]["artifact_readiness"]["analysis_status"],
                "approved",
            )
            self.assertEqual(
                readiness["programs"][1]["artifact_readiness"]["validator_status"],
                "not_run",
            )
            self.assertFalse((bundle / manifest["canonical_filename"]).exists())
            self.assertFalse((bundle / "program-set-sme-core-review.md").exists())
            self.assertTrue((bundle / "program-set-core-coverage.yaml").is_file())

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_blocks_wrong_identity_and_summary_status_conflict(self) -> None:
        for case in ("wrong_identity", "status_conflict"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                working = temp / "delivery"
                output = temp / "review"
                programs = temp / "programs.txt"
                analysis_dir = working / "modules" / "normal" / "CU106"
                fixture = write_finalized_program_artifacts(
                    analysis_dir,
                    "CU999" if case == "wrong_identity" else "CU106",
                    routines=("MAIN",),
                )
                if case == "wrong_identity":
                    for source, target in {
                        fixture.program_analysis: analysis_dir / "program-analysis.md",
                        fixture.summary_yaml: analysis_dir / "program-analysis-summary.yaml",
                        fixture.source_index_yaml: analysis_dir / "source-index.yaml",
                        fixture.routine_index_markdown: analysis_dir / "routine-index.md",
                        fixture.message_inventory_yaml: analysis_dir / "message-inventory.yaml",
                        fixture.routine_details_markdown: analysis_dir / "routine-logic-details.md",
                        fixture.routine_details_yaml: analysis_dir / "routine-logic-details.yaml",
                    }.items():
                        source.rename(target)
                    summary_path = analysis_dir / "program-analysis-summary.yaml"
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
                    summary["sidecars"] = {
                        key: {
                            **value,
                            "path": Path(str(value["path"])).name.removeprefix(
                                "CU999-"
                            ),
                        }
                        for key, value in summary["sidecars"].items()
                    }
                else:
                    summary_path = fixture.summary_yaml
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
                    summary["analysis_status"] = "draft"
                summary_path.write_text(
                    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
                )
                programs.write_text("CU106\n", encoding="utf-8")

                result = subprocess.run(
                    [
                        POWERSHELL,
                        "-NoProfile",
                        "-File",
                        str(BUILD_SCRIPT),
                        "--review-name",
                        "Readiness conflict",
                        "--programs-file",
                        str(programs),
                        "--working-root",
                        str(working),
                        "--profile",
                        str(PROFILE),
                        "--output-dir",
                        str(output),
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = PYTHON_BUILDER.load_yaml(
                    bundle_artifact(output, "program-set-core-input-manifest.yaml")
                )
                readiness = manifest["programs"][0]["artifact_readiness"]
                self.assertEqual(readiness["status"], "not_ready")
                serialized = json.dumps(readiness).lower()
                if case == "wrong_identity":
                    self.assertIn("program identity", serialized)
                    self.assertIn("cu999", serialized)
                else:
                    self.assertIn("conflicting", serialized)
                    self.assertEqual(readiness["analysis_status"], "draft")

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_validator_exit_and_findings_match_python(self) -> None:
        from tests.test_program_set_core_review_builder import build_review_fixture

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest, review, _ = build_review_fixture(Path(temp_dir))
            valid = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATE_SCRIPT), "--manifest", str(manifest), "--review", str(review)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertIn("OK: program-set SME core review contract passed", valid.stdout)

            review.write_text(review.read_text(encoding="utf-8") + "\n## Nodes\n\nForbidden.\n", encoding="utf-8")
            invalid = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATE_SCRIPT), "--manifest", str(manifest), "--review", str(review)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(invalid.returncode, 1)
            self.assertIn("forbidden full-flow section: Nodes", invalid.stderr)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_validator_rejects_trailing_yaml_and_classifies_runtime_errors(self) -> None:
        from tests.test_program_set_core_review_builder import build_review_fixture

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest, review, _ = build_review_fixture(Path(temp_dir))
            manifest.write_text(
                manifest.read_text(encoding="utf-8") + "\n- unexpected-root-item\n",
                encoding="utf-8",
            )
            malformed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(VALIDATE_SCRIPT),
                    "--manifest",
                    str(manifest),
                    "--review",
                    str(review),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(malformed.returncode, 1)
            self.assertIn("Unexpected trailing YAML content", malformed.stderr)

            usage = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATE_SCRIPT)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(usage.returncode, 2)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_preserves_git_inventory_freshness_and_approved_repo_mode(self) -> None:
        from tests.test_program_set_core_review_builder import (
            init_clean_git_source_root,
            write_inventory_cache,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            document_repo = temp / "document-repo"
            document_repo.mkdir()
            source = temp / "source"
            output = temp / "review"
            programs = temp / "programs.txt"
            init_clean_git_source_root(source)
            write_inventory_cache(source)
            programs.write_text("CU257F\nMISSINGPGM\nMISSINGPGM\n", encoding="utf-8")

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(BUILD_SCRIPT),
                    "--review-name",
                    "Inventory Review",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(document_repo),
                    "--source-root",
                    str(source),
                    "--profile",
                    str(PROFILE),
                    "--output-dir",
                    str(output),
                    "--artifact-repo-mode",
                    "approved_document_repo",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = PYTHON_BUILDER.load_yaml(
                bundle_artifact(output, "program-set-core-input-manifest.yaml")
            )
            self.assertEqual(manifest["source_inventory"]["freshness"], "fresh")
            self.assertEqual(
                manifest["source_inventory"]["programs"][0]["inventory_status"],
                "found",
            )
            self.assertTrue(
                manifest["source_inventory"]["programs"][0]["targeted_scan_allowed"]
            )
            self.assertEqual(
                manifest["programs"][1]["run_resolution"],
                "blocked_missing_source",
            )
            self.assertEqual(
                manifest["programs"][2]["run_resolution"],
                "blocked_missing_source",
            )
            self.assertEqual(
                manifest["source_inventory"]["programs"][-1]["run_resolution"],
                "blocked_missing_source",
            )
            self.assertEqual(
                manifest["run_profile"]["artifact_repo_mode"],
                "approved_document_repo",
            )


if __name__ == "__main__":
    unittest.main()
