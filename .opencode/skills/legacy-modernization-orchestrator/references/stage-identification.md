# Stage Identification Reference

Map the user's current artifact(s) to a single canonical stage. Use the most
upstream stage that fits — do not "round up" maturity.

## Full Stage Table

| # | Stage | Identifying Input |
| ---: | --- | --- |
| 0 | Evidence Intake (authorization pending) | Raw source members, DDS exports, job logs, spool, screen samples, or DB extracts with `sensitivity: unknown`, missing source-path authorization, or required redaction not approved |
| 0p | Document Evidence Intake | Business/technical documents are still in raw Office / Visio / PDF / image form (`.xlsx`/`.xlsm`/`.xls`, `.docx`/`.doc`, `.pptx`/`.ppt`, `.vsdx`/`.vsd`, `.pdf`, `.png`/`.jpg`/`.tif`, scanned pages), authorized and with known sensitivity, but not yet normalized to Markdown/CSV/PDF/PNG/SVG with `document-intake/<DOCSET-SLUG>/intake.manifest.yaml`. Sensitivity-unknown or unauthorized material is stage **0**, not 0p. |
| 0d | Legacy Flow Context Artifact | Existing legacy `flow-normalization/flow-context-index.yaml` package with `normalization.status: triage_needs_source_enrichment` or `draft_needs_sme_review`; do not create this package for new default runs |
| 0m | Module Context Intake | External RAG / code-knowledge-graph output, source snippets, dictionary mappings, contradictions, retrieval gaps, SME fragments, or human-confirmed four-view module context not yet normalized into `00_context_packages/<MODULE-SLUG>/` with source eligibility |
| 0n | Module Context Ready | `00_context_packages/<MODULE-SLUG>/context-index.yaml` with `intake.status: ready_for_module_analysis` or `ready_with_warnings` |
| 1 | Evidence Ready | Approved evidence manifest; every item has known sensitivity and either `source_path_verified: true` or completed required redaction |
| 2a | Inventory In Progress | Partial `inventory.yaml` (some objects, no `sme_review.decision`) |
| 2b | Inventory Blocked | `inventory.yaml.sme_review.decision: blocked`, or `coverage_gaps[].blocking: yes` unresolved |
| 2c | Inventory Done | `inventory.yaml.sme_review.decision: approved` or `approved_with_non_blocking_tbd`, plus `object-map.md` |
| 3a | Program Analysis In Progress | `program-analysis-<OBJ-ID>.md` for some but not all in-scope programs |
| 3b | Program Analysis Done | `program-analysis-<OBJ-ID>.md` for all in-scope programs **AND** all triggered companion artifacts (`screen-report-analysis.md` per triggered DSPF/PRTF/menu; `04_modules/<MODULE>/data-model/dictionary.md` if data-model trigger fires). Triggers declared in `inventory.yaml.sme_review.downstream_required`; see `skills/legacy-ibmi-inventory/references/downstream-triggers.md`. |
| 3c | Flow Analysis In Progress | `flow-<FLOW-SLUG>.md` for some but not all in-scope flows |
| 3d | Flow Analysis Done | `flow-<FLOW-SLUG>.md` for all in-scope flows at `status: approved` or `approved_with_non_blocking_tbd` |
| 3e | Module Analysis In Progress | `04_modules/<MODULE-SLUG>/` exists with one or more of the four views drafted |
| 3f | Module Analysis Done | `04_modules/<MODULE-SLUG>/` with all four views (Operation/System/Program/Data) approved (or approved_with_non_blocking_tbd) and a BRD Source Eligibility Crosswalk. For standard code-backed BRD/spec work, the views must be backed by approved inventory, in-scope program analyses, and in-scope flow analyses; context-only views with missing source coverage remain 3e/in review unless an explicit non-approved context-only draft path is recorded. If no approved BRD Package exists for the selected capability, the next route remains BRD discovery writing / review, not spec writing. |
| 5a | BRD Discovery In Review | `05_brds/<CAPABILITY-SLUG>/brd.md` exists with `status: poc_draft`, `status: draft`, or `status: in_review`, or BRD review/sign-off is incomplete |
| 5b | BRD Discovery Approved | `05_brds/<CAPABILITY-SLUG>/brd.md` exists with `status: approved`; route to spec only if a separate post-BRD promotion / disposition decision exists |
| 5c | Post-BRD Comparison / Disposition Open | Approved BRD exists, but old-vs-new comparison, risk assessment, gap analysis, or promotion decision is still pending outside the BRD Package |
| 4a | Static Analysis Partial | One or more of `call-graph.md`, `crud-matrix.md`, `data-dictionary.md`, `screen-map.md` (optional supplemental artifacts; mostly subsumed by program/flow/module analyses) |
| 4b | Static Analysis Complete | All four Layer 1 supplemental artifacts present (optional) |
| 5 | Runtime Evidence Mined | `runtime-evidence.jsonl` plus referenced samples in `07_runtime-evidence/` (deferred from MVP) |
| 6 | Business Rules Drafted | BR seeds present in module View 1 OR a separate `business-rules.md` (BR IDs + linked evidence); typically subsumed by stage 3f |
| 7 | Capabilities Mapped | Capability seeds (`CAP-*`) listed in `module-overview.md` OR a separate `capability-map.md`; typically subsumed by stage 3f |
| 8a | Spec Drafted | `spec.yaml.status: draft` plus `spec.md` |
| 8b | Spec In Review | `spec.yaml.status: in_review` plus optional `review-report.md` |
| 8c | Spec Approved | `spec.yaml.status: approved` |
| 9 | Equivalence Pack Ready | `golden-master-tests.md` plus generated test artifacts traceable to approved rules |
| 10 | Forward Handoff Ready | Spec Approved + Equivalence Pack + redacted sample transactions |

## Disambiguation Rules

When the user has artifacts from multiple stages:

- The **earliest unmet stage** is the current stage.
- Example: user has `program-analysis.md` AND `business-rules.md` AND
  `spec.yaml (draft)`. If `program-analysis.md` covers only 2 of 5 in-scope
  programs, the current stage is **3a (Program Analysis In Progress)**, not
  8a. Downstream artifacts must be re-validated after analysis completes.

When evidence authorization is incomplete:

- If any one item has `sensitivity: unknown`, lacks source-path authorization,
  or requires redaction without approval, the stage is **0 (Evidence Intake)**
  regardless of how much other progress exists. The Evidence Authorization Gate
  is non-bypassable.

When legacy flow-normalization output is sparse:

- `triage_needs_source_enrichment` remains stage **0d**, not stage 0m or 0n.
  Route to source-owner supplement collection or SME clarification before
  `legacy-module-context-intake`.
- `ready_with_warnings` with `quality_level: L1 sparse` and
  `risk_acceptance.status: accepted` remains stage **0d** for identification,
  but its next route is `legacy-module-context-intake` with low-confidence
  carry-forward TBDs.
- `draft_needs_sme_review` remains stage **0d** until SME review confirms the
  package or explicitly accepts non-blocking gaps.
  Do not round it up to module context ready.
- Generated-draft or candidate-only flow context remains stage **0d** or **0m**
  until `legacy-module-context-intake` records source eligibility. It must not
  be treated as BRD-ready flow evidence.

When documents are still in raw Office/Visio/PDF/image form:

- If the source material is authorized with known sensitivity but has not yet
  been normalized to Markdown/CSV/PDF/PNG/SVG (no `document-intake/<DOCSET-SLUG>/intake.manifest.yaml`),
  the stage is **0p (Document Evidence Intake)**. Route to
  `legacy-document-evidence-intake` first when tooling is available; otherwise
  preserve source metadata and continue to `legacy-module-context-intake` in
  degraded mode.
- Once an `intake.manifest.yaml` exists with gate `ready` or
  `ready_with_warnings`, the stage advances to **0m/0n** and routes to
  `legacy-module-context-intake`.
- If any document has `sensitivity: unknown` or missing/`unauthorized`
  authorization, the stage is **0 (Evidence Intake)**, not 0p — route to
  `legacy-ibmi-evidence-intake`.

When module analysis is complete but BRD review is missing:

- Keep the canonical stage at **3f Module Analysis Done** for workflow-state
  compatibility, but attach `stage-cards/05a-brd-writing.md` and route to
  `legacy-brd-writer`.
- Do not identify the capability as **8a Spec Drafted** merely because a
  `spec.md` or `spec.yaml` was generated early. If the approved BRD Package is
  missing, the current unmet gate is the BRD Discovery Gate.

When a module or BRD was generated from `00_context_packages/` only:

- If the user expects a production / internal-use BRD, migration discovery
  baseline, spec, or SDD handoff input, identify the earliest missing
  code-backed stage instead of rounding up to module or BRD maturity.
- If the user explicitly asks for an internal POC BRD, identify the route as
  BRD Discovery In Review with `status: poc_draft` once `05_brds/` exists, but
  keep the earliest missing code-backed stage visible as an approval/spec
  blocker.
- Missing `01_inventory/object-map.md` means the current unmet stage is
  **2a/2c Inventory** depending on whether a partial `inventory.yaml` exists.
- Missing `02_programs/<MODULE>/<OBJ>/program-analysis.md` for in-scope
  programs means the current unmet stage is **3a Program Analysis In
  Progress**, even if `04_modules/` or `05_brds/` exists.
- Missing `03_flows/<MODULE>/flow-<FLOW-SLUG>.md` for known business
  transactions means the current unmet stage is **3c Flow Analysis In
  Progress**.
- A context-only module or BRD may remain as draft review material only when a
  named owner risk acceptance says source/object evidence is unavailable for
  this cycle. It must not be treated as **3f Module Analysis Done** or **5b BRD
  Discovery Approved** for code-backed downstream routing.
- An internal POC BRD may remain as `poc_draft` review material when the
  requester wants early validation. It must not be treated as **5b BRD
  Discovery Approved** or as spec/handoff-ready.
- If the module overview's BRD Source Eligibility Crosswalk marks required BRD
  sections as `questions_only`, `candidate_only`, `generated_draft`, missing,
  or unreviewed `source_documented`, those rows can only advance as BRD review
  questions/TBDs. They do not make the BRD section covered.

When only forward chain artifacts exist:

- If the user has only `wwa-lab/build-agent-skill`-style **target-system**
  artifacts and wants to generate or modify IBM i code, point them to the
  forward repo's `ibm-i-workflow-orchestrator`.
- If the user has legacy Function Specs, Technical Designs, Program Specs,
  File Specs, interface specs, or data dictionaries as historical evidence for
  understanding the existing system, keep them in this reverse chain and route
  to Flow Context Normalization.

## Stage to Output Directory

All paths below are **relative to `project.root`** (default
`docs/<project-name>/`). For a project named `XXX260004-demo`, stage 2
artifacts live at `docs/XXX260004-demo/01_inventory/`.

| Stage | Lives Under (relative to project.root) |
| --- | --- |
| 0p, 0d, 0m, 0n | `00_context_packages/` |
| 1 | `evidence/redacted/` (raw never committed) |
| 2 | `01_inventory/` |
| 3a, 3b | `02_programs/` |
| 3c, 3d | `03_flows/` |
| 3e, 3f | `04_modules/` |
| 3f + BRD Discovery Gate / 5a–5c | `05_brds/` |
| 4 | optional supplemental artifacts under the owning program / flow / module folder |
| 5 | `07_runtime-evidence/` |
| 6, 7 | `08_business-understanding/` |
| 8 | `05_specs/` |
| 9 | `06_quality/` |
| 10 | `09_forward-sdlc/` (handoff manifest) |

Subdirectories are created on demand by the writing skill — do NOT
pre-create empty stage folders. See `docs/workflow-state-contract.md` for
the full project-root resolution rules and `README.md#artifact-chain` for
the layout diagram.
