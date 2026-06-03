---
name: legacy-module-context-intake
description: Package external RAG or code-knowledge-graph output, document-intake manifests, source metadata, SME fragments, and human-confirmed module context into a traceable `00_context_packages/<MODULE-SLUG>/` package. Use when a team has module-first context, document evidence intake output, source snippets, field dictionary mappings, impact scope, contradictions, retrieval gaps, reviewed module notes, or sparse source metadata and needs a safe handoff to `legacy-ibmi-module-analyzer` or BRD preparation. Blocks on unauthorized or unredacted evidence, hidden contradictions, or attempts to promote RAG candidates, generated-draft context, or sparse-context TBDs into approved business rules, BRD facts, or canonical module flows; treats rough scope and degraded context as warnings/TBDs.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy Module Context Intake

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Turns reviewed external/RAG/module context into a traceable context package for safe downstream module analysis. |
| Input | Document-intake output, source metadata, RAG/context snippets, SME fragments, owner-reviewed module context, retrieval gaps, contradictions, and scope notes. |
| Output | `00_context_packages/<MODULE-SLUG>/` package with context index, source map, readiness status, contradictions, and blocked/TBD items. |
| Core prompt strategy | Normalize context without approving it as business truth, classify source eligibility, preserve contradictions, and keep sparse/generated context from becoming hidden rules or BRD facts. |
| Upstream skill | `legacy-document-evidence-intake`, external RAG, source metadata, SME fragments, or human-confirmed module context. |
| Downstream consumer | `legacy-ibmi-module-analyzer`, `legacy-brd-writer`, and module review workflows. |
| Validation standard | Module scope, evidence authorization, context provenance, source eligibility, contradiction handling, and readiness status are explicit. |
| Known risk | Promoting RAG candidates, generated-draft context, or owner guesses into approved business rules or BRD conclusions. |
| Practical example | Package reviewed claims module context plus RAG snippets and SME fragments so module analysis can build a coverage map with visible TBDs. |

## Purpose

Turn external RAG / code knowledge graph output plus human-confirmed module
context, SME fragments, or evidence-bounded elicitation output into a portable,
evidence-tagged context package:

```text
00_context_packages/<MODULE-SLUG>/
|-- context-index.yaml
|-- rag-evidence-map.md
|-- contradiction-log.md
`-- open-questions.md
```

This skill is a **module-first intake bridge**. It makes RAG output usable by
Legacy Spec Factory, but it does not approve business rules, replace source
analysis, or bypass SME review.

Do not create intake flow Markdown files in this package. If upstream material
is organized as Operation / Business Flow, System Flow, Program Flow, and Data
Flow, carry that structure as coverage metadata, evidence-map rows, candidate
facts, and open questions. The canonical four module views are created only
under `04_modules/<MODULE-SLUG>/` by `legacy-ibmi-module-analyzer`.

This package also acts as a **BRD source-of-truth firewall**. Each carried
claim must be classified as one of:

- `confirmed_by_sme`
- `code_backed`
- `source_documented`
- `candidate_only`
- `generated_draft`
- `missing`

Only `confirmed_by_sme` and `code_backed` claims are eligible to become BRD
conclusions. `source_documented` claims may support source mapping or SME
questions until reviewed. `candidate_only`, `generated_draft`, and `missing`
items must remain `TBD-*`, coverage gaps, or review questions.

For standard code-backed BRD/spec work, this package is not enough by itself.
It must preserve any IBM i program/file/object anchors so the orchestrator can
route to `legacy-ibmi-inventory` for `object-map.md`, then program and flow
analysis, before module or BRD approval.

For internal POC BRD validation, this package may feed `legacy-brd-writer`
directly as low-confidence input when the user explicitly requests early BRD
output. The resulting BRD must use `status: poc_draft`, preserve all missing
evidence as approval/spec blockers, and must not become an approved BRD,
spec-writing input, or SDD handoff input.

## Use This Skill When

- A team supplies a business module or subsystem context, including incomplete
  SME fragments, before running the usual program-by-program reverse chain.
- External RAG output includes `rag-run-index.yaml`, source snippets, field
  dictionary mappings, impact scope, contradictions, or retrieval gaps.
- `legacy-document-evidence-intake` produced a manifest, normalized outputs,
  evidence coordinates, extraction warnings, or source metadata. Missing OCR,
  missing Markdown, or unavailable converters are allowed to continue as
  low-confidence `TBD-*` items.
- The user asks to ingest, normalize, package, or prepare a RAG output bundle
  under `00_context_packages/<MODULE-SLUG>/`.
- A BRD or module analysis should start from human-confirmed context or an
  explicit context-only review draft instead of from raw source only.
- The user explicitly asks for an early internal POC BRD and needs source
  metadata / context packaged before `legacy-brd-writer` produces
  `status: poc_draft`.

## Do Not Use This Skill When

- The user only has raw IBM i source, DDS, job logs, spool, or DB extracts with
  unknown authorization or sensitivity. Route to `legacy-ibmi-evidence-intake`.
- The user wants an approved module analysis. Route the finished context
  package to `legacy-ibmi-module-analyzer`.
- The user wants `spec.yaml` or final `BR-*` rules. Route through
  `legacy-ibmi-module-analyzer`, `legacy-brd-writer`, and
  `legacy-spec-writer`.
- The task is to build or query the external RAG system itself. This skill
  consumes file-based RAG output only.

## Required Inputs

- Module slug, business name, and scope statement.
- Human-confirmed or explicitly draft module context, document-intake output,
  source metadata, or SME fragments. Complete business process, system
  interface, program-anchor, and data-anchor coverage is preferred, but
  incomplete context is acceptable when missing coverage is carried as `TBD-*`
  and source eligibility is classified.
- RAG output bundle when available, preferably with:
  - `rag-run-index.yaml`
  - `flow-hydration-summary.md`
  - `source-snippets.md`
  - `field-dictionary-context.md`
  - `impact-scope.md`
  - `contradictions.md`
  - `retrieval-gaps.md`
- Evidence authorization signal for source/runtime content:
  - approved evidence manifest from `legacy-ibmi-evidence-intake`, or
  - explicit RAG metadata proving the bundle is synthetic, public,
    non-production, or otherwise approved for agent review.

## Stop Conditions

Stop and produce only blocking findings / requested remediation if any apply:

| Condition | Route |
| --- | --- |
| Source/runtime evidence sensitivity is unknown | `legacy-ibmi-evidence-intake` |
| Confidential evidence is present without approved redaction | `legacy-ibmi-evidence-intake` |
| Module slug, business name, or scope is missing and no provisional focus can be derived | module owner / SME clarification |
| Module context and SME fragments are absent, and there is no document-intake output, source metadata, RAG bundle, or SME clue to carry forward | requester must provide module context or route to normal inventory/program/flow chain |
| RAG contradictions are missing, blank without evaluated checks, or hidden in prose | rerun / repair RAG bundle before intake |
| RAG candidate rules are requested as approved `BR-*` | block; candidates stay `needs_sme_review` seeds only |
| Source paths, snippet IDs, or dictionary IDs cannot be traced | record `TBD-*` in `open-questions.md`; do not smooth over |

## Output Contract

Use `references/output-contract.md` for required fields and examples. Use the
templates under `templates/` as scaffolding.

Runtime tooling rule: the bundled validator is a standard-library Python script.
Run it only with an already-available Python interpreter. Do not create a
virtual environment, install packages, or wait on interactive environment
configuration. If interpreter discovery or startup remains
configuring/evaluating, record validation as `tool_unavailable`, keep the
package out of `ready_for_module_analysis`, and report the manual command to
run later.

Artifact preview guardrail: context Markdown files are the canonical review
surface. Do not open IDE, browser, Mermaid, or Markdown previews unless the
user explicitly asks for visual inspection. For large modules or four-view
packages copied from large normalization runs, record
`run_validation.artifact_preview_status: skipped_large_package` and continue
after structural validation/manual review. Never reopen the same preview or
open every view as a completion check.

GitHub Copilot hosted-agent mode is stricter: do not run Python commands,
shell probes, validators, package installs, or environment setup from this skill
unless the user explicitly confirms the runtime is already prepared. Record
validation as `tool_unavailable_hosted_agent`, keep the package out of
`ready_for_module_analysis`, and report the validator path as manual follow-up
text. The package may continue as `ready_with_warnings` / degraded context when
the warning is recorded. Do not enter or wait on Python environment setup.

For deterministic local validation outside hosted Copilot mode, run
`skills/legacy-module-context-intake/scripts/validate_context_package.py` with
an existing Python interpreter against `00_context_packages/<MODULE-SLUG>/`.

The package status in `context-index.yaml` must be one of:

- `ready_for_module_analysis`
- `ready_with_warnings`
- `blocked_pending_evidence`
- `blocked_pending_contradiction_review`
- `blocked_pending_scope` (legacy compatibility only; prefer `ready_with_warnings` with scope TBDs)

Allowed handoff:

- `ready_for_module_analysis` or `ready_with_warnings` -> route to
  `legacy-ibmi-module-analyzer`.
- `ready_with_warnings` -> may also route to `legacy-brd-writer` only for an
  explicit internal POC BRD (`status: poc_draft`, `evidence_mode:
  internal_poc`). Do not treat this as approval or spec/handoff readiness.
- Any `blocked_*` status -> do not route downstream; list exact remediation in
  `open-questions.md` and `context-index.yaml`.

## Step Contract

This skill conforms to the Legacy Spec Factory Step Contract.

### Input

- **Required**: module slug or provisional focus, module business name/scope or
  scope TBD, human context fragments, document-intake manifest/source metadata,
  a RAG hydration summary, or SME note; evidence authorization for every
  source/runtime artifact referenced; source eligibility classification for
  every carried claim.
- **Optional**: approved evidence manifest, inventory, program analyses, flow
  analyses, SME notes, architecture diagrams, dictionary export, ARCAD REF
  export, runtime sample index.
- **Input readiness scoring**:
  - `0-5 blocked`: evidence authorization unresolved, contradictions hidden, no
    usable module context fragments, and no document-intake/source metadata,
    sparse/degraded package, RAG bundle, or SME clue exists to carry forward.
  - `6 minimum_pass`: module identity, context fragments, coverage notes, RAG
    provenance when applicable, source eligibility, and explicit open questions
    are present; or document-intake/source metadata has all missing views
    carried as TBDs.
  - `7-8 usable`: source snippets, dictionary mappings, impact scope, and
    contradiction checks are traceable.
  - `9-10 strong`: approved evidence manifest, SME-reviewed four-view context,
    source/runtime snippets, dictionary ownership, and resolved high-severity
    contradictions are supplied.

### Execution

- **Procedure**: follow the Workflow below.
- **Allowed inference**: normalize and cross-link supplied context; derive
  evidence mappings from snippet tables; classify source eligibility, gaps, and
  contradictions already present in the bundle.
- **Forbidden assumptions**: inventing module boundaries, systems, actors,
  flows, data owners, dictionary meanings, normal operating frequency,
  business rules, BRD conclusions, or modernization decisions.
- **ID policy**: may mint `TBD-*` and reuse upstream `RAG-*`, `SNP-*`, `RUN-*`,
  `DD-*`, `EV-*`, `FLOW-*`, `OBJ-*`, `MODULE-*`, and `VIEW-*`. Do not mint
  final `BR-*`, `CAP-*`, `DEC-*`, `AC-*`, or `TC-*`.

### Output

- **Canonical directory**: `00_context_packages/<MODULE-SLUG>/`.
- **Required files**: the four files listed in Purpose.
- **Required gates**: evidence authorization, provenance completeness,
  contradiction visibility, source eligibility, context coverage, and
  open-question carry-forward.
- **Handoff status**: only `ready_for_module_analysis` and
  `ready_with_warnings` may feed `legacy-ibmi-module-analyzer`. For sparse
  document-intake/source-metadata input, `ready_with_warnings` means
  low-confidence context only, not approval of any missing coverage.
  `ready_with_warnings` may feed `legacy-brd-writer` only as internal POC input
  that produces a non-approved `poc_draft`.

### Validation

- **Mechanical**: all required files exist; `context-index.yaml` names every
  input bundle and output file; every contradiction/gap has an owner or
  routing destination.
- **Semantic**: no RAG candidate, generated-draft item, or context-only claim is
  promoted to an approved business rule or BRD fact; all claims preserve source
  eligibility, knowledge type, and evidence strength; contradictory evidence
  remains visible; candidate seeds explain the business signal first and keep
  program names, file names, field names, snippet IDs, and runtime object names
  in evidence context unless the view is explicitly technical; BRD functional
  analysis hints preserve which context can feed SME-required BRD areas without
  inventing channels, touchpoints, interfaces, dependencies, security, or
  source-document mappings; context-only technical anchors are not presented as
  `confirmed_from_code` and must be routed to inventory/program/flow analysis
  before standard BRD approval.
- **Sparse-input restriction**: if the upstream package or source metadata is
  sparse/degraded, preserve every missing coverage area as a `TBD-*`, mark evidence
  strength low, classify generated or candidate material as
  `candidate_only` / `generated_draft`, and do not create approved facts,
  `BR-*`, or BRD-ready claims from the sparse context alone.
- **SME / human approval**: module owner confirms business name and scope;
  data owner or dictionary owner confirms approved dictionary mappings where
  they are used as business terminology.

## Workflow

1. **Resolve module identity**
   - Confirm `MODULE-SLUG`, business name, scope statement, and module owner.
   - Normalize slug to uppercase hyphenated form without renumbering existing
     IDs.

2. **Check evidence authorization**
   - Read RAG sensitivity/provenance metadata and any evidence manifest.
   - Block if source/runtime artifacts are not approved for agent review.

3. **Inventory upstream context files**
   - Record each supplied input in `context-index.yaml`.
   - Capture run ID, source snapshot, dictionary version, ARCAD REF snapshot,
     corpus root, and generation timestamp when present.
   - If input comes from `legacy-document-evidence-intake`, record the
     `document-intake/<DOCSET-SLUG>/intake.manifest.yaml`,
     `evidence-coordinates.md`, `extraction-warnings.md`, and any normalized
     outputs or source metadata. Missing OCR/Markdown/converter output becomes
     a low-confidence `TBD-*`, not a blocker.
4. **Package context coverage and source eligibility**
   - Do not create Operation / Business Flow, System Flow, Program Flow, or
     Data Flow intake Markdown files.
   - Capture supplied context as coverage metadata in `context-index.yaml`,
     evidence rows and candidate facts in `rag-evidence-map.md`, and routed
     gaps in `open-questions.md`.
   - Every factual claim must include a source row, evidence ID, or SME note.
   - Every claim must carry one source eligibility label:
     `confirmed_by_sme`, `code_backed`, `source_documented`,
     `candidate_only`, `generated_draft`, or `missing`.
   - Keep candidate rules as candidates or seeds, never approved rules.
   - Phrase candidate seeds with business meaning first. Business-process
     candidates should speak in rule / capability / exception language;
     system, program, or data candidates must still say what business behavior
     or decision depends on the technical check.
   - Keep program names, file names, field names, node IDs, source paths, and
     raw RAG IDs in `Evidence Basis`, not as the main candidate statement.
   - For sparse/degraded document-intake or source-metadata input, create
     low-confidence coverage notes and preserve missing sequence, actor,
     system, program, and data questions as carry-forward `TBD-*`.
   - Do not upgrade a generated-draft or candidate-only item merely because it
     appears in multiple coverage areas; corroboration requires SME
     confirmation or code-backed evidence.

5. **Build evidence map**
   - Convert source snippets, runtime observations, dictionary mappings, and
     impact-scope rows into `rag-evidence-map.md`.
   - Preserve original IDs such as `SNP-*`, `RUN-*`, `DD-*`, `RAG-CAND-*`, and
     `RAG-CONFLICT-*`.

6. **Carry contradictions forward**
   - Copy every contradiction into `contradiction-log.md`.
   - If the RAG bundle says no contradictions exist, include the evaluated
     checks that justify that result.

7. **Carry gaps and assumptions forward**
   - Convert retrieval gaps, missing mappings, and non-blocking assumptions
     into `open-questions.md`.
   - Mint `TBD-*` only for questions that need Legacy Spec Factory tracking.

8. **Set handoff decision**
   - If any hard gate failed, set a `blocked_*` status and name the upstream
     owner.
   - Otherwise set `ready_for_module_analysis` or `ready_with_warnings` and
     route to `legacy-ibmi-module-analyzer`.
   - `ready_for_module_analysis` means the package is ready for module
     assembly and coverage review, not that context-only claims may feed BRD
     conclusions.
   - If the requester explicitly asks for an internal POC BRD, set
     `downstream_next_step: legacy-brd-writer` with `ready_with_warnings` and
     carry every missing view, source-eligibility gap, and weak claim as an
     approval/spec blocker.

9. **Validate**
   - In GitHub Copilot hosted-agent mode, do not run the bundled validator.
     Record `run_validation.structural_status:
     tool_unavailable_hosted_agent` in `context-index.yaml`; do not treat the
     package as structurally validated, but do allow degraded module-context or
     internal POC BRD handoff when authorization/sensitivity is clear and the
     validation gap is recorded. Report the manual validator path:
     `skills/legacy-module-context-intake/scripts/validate_context_package.py`.
   - In an already-prepared local shell only, run the bundled validator with an
     existing Python interpreter and fix every finding before handoff. Record
     the result in `context-index.yaml.run_validation`.
   - Artifact preview status is informational only; it is not a structural
     validation gate.

10. **Finalize and stop**
    - After all four package files, `context-index.yaml.run_validation`, and
      any applicable workflow-state write-back are recorded, stop the run and
      report the package path plus any manual validator or preview follow-up.
    - Do not keep re-reading the context package, repeatedly checking workflow
      status, or opening previews after write-back unless a validator finding
      names a concrete file to fix.

## Handoff To Module Analyzer

When the package is ready, tell the next agent:

```text
Use legacy-ibmi-module-analyzer with
00_context_packages/<MODULE-SLUG>/ as module-first context.
Treat RAG snippets and runtime observations as evidence context only.
Preserve contradiction-log.md and open-questions.md as TBD inputs.
Do not promote candidate rules, generated-draft context, or source-documented
claims into BRD conclusions without SME confirmation or code-backed evidence.
Preserve business-signal-first candidate seeds; do not turn evidence object
names into capability boundaries.
Generate the canonical four module views only under
04_modules/<MODULE-SLUG>/.
If the target is a standard code-backed BRD/spec and object-map/program/flow
artifacts are missing, route to legacy-ibmi-inventory first.
```

## Handoff To BRD Writer For Internal POC

When the user explicitly wants an early internal POC BRD, tell the next agent:

```text
Use legacy-brd-writer with
00_context_packages/<MODULE-SLUG>/ as low-confidence POC context.
Set brd.md status: poc_draft and evidence_mode: internal_poc.
Treat source_documented, candidate_only, generated_draft, missing, and sparse
metadata as POC hypotheses, TBDs, or review prompts only.
Do not promote any claim to an approved BRD conclusion, spec input, or SDD
handoff input until standard code-backed and SME approval gates pass.
```

## References

- `references/output-contract.md` - required file shape and field-level rules.
- `templates/` - scaffolding for the required output files.
- `examples/credit-check-rag-positive/` - frozen positive context package.
- `examples/unauthorized-evidence-negative/` - expected blocked response.
- `scripts/validate_context_package.py` - local structural validator.
- `../../docs/rag-setup-detail.md` - external RAG bundle boundary.
- `../../docs/rag-output-sample/` - compact synthetic RAG output example.
- `../../docs/module-analysis-model.md` - downstream four-view module model.
- `../../docs/evidence-and-knowledge-taxonomy.md` - knowledge type and evidence
  strength vocabulary.

## Version History

- v0.1.3 (2026-05-28): Added advisory BRD functional-analysis coverage hints
  to `context-index.yaml` so downstream module analysis can preserve channel,
  UI, interface, validation, error, and dependency gaps without inventing them.
- v0.1.4 (2026-05-29): Clarified that intake context is not the canonical
  four-view module artifact produced by `legacy-ibmi-module-analyzer`.
- v0.1.5 (2026-05-30): Added code-backed handoff guidance so context packages
  preserve technical anchors but route to inventory/object-map, program
  analysis, and flow analysis before standard BRD/spec approval.
- v0.1.6 (2026-05-31): Added artifact preview and stop-after-writeback
  guardrails so large context packages do not remain in processing after
  package files and validation status are written.
- v0.1.7 (2026-06-03): Added source eligibility classification and BRD
  source-of-truth firewall language. Context intake now accepts incomplete SME
  fragments but prevents candidate-only/generated context from becoming BRD
  conclusions without SME confirmation or code-backed evidence.
- v0.1.8 (2026-06-03): Accepted degraded sparse-context packages without
  requiring prior owner risk acceptance. Such packages proceed only as
  `ready_with_warnings` low-confidence context with all sparse gaps preserved
  as `TBD-*`.
- v0.1.9 (2026-06-03): Removed the previous separate context-preparation step
  as a required upstream path. Module context intake now accepts
  document-intake manifests, extraction warnings, source metadata, and RAG/SME
  notes directly, preserving sparse gaps as low-confidence `TBD-*`.
- v0.1.10 (2026-06-03): Added internal POC BRD handoff. `ready_with_warnings`
  context may feed `legacy-brd-writer` only as non-approved `poc_draft` input;
  approval/spec/handoff gates remain blocked until standard evidence and SME
  review pass.
- v0.1.11 (2026-06-03): Removed intake flow file generation. Context packages
  now contain only index, evidence map, contradiction log, and open questions;
  canonical four-view files are produced only by module analysis.
- v0.1.12 (2026-06-03): Retired the separate flow-context normalizer path from
  active module-context intake guidance.
- v0.1.1 (2026-05-26): Added business-signal-first candidate seed guidance so
  RAG/program/file evidence does not become the business-facing statement.
- v0.1.0 (2026-05-21): Initial module context intake skill.
