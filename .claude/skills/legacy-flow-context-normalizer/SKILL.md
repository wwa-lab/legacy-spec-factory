---
name: legacy-flow-context-normalizer
description: "Legacy/manual optional flow-normalization skill. Do not use in the default Legacy Spec Factory chain; route scattered documents, document-intake manifests, source metadata, RAG output, and SME notes directly to legacy-module-context-intake unless the user explicitly asks to create a flow-normalization package. When explicitly requested, normalize scattered Visio, Word, Excel, PDF, PowerPoint, exported diagrams, RAG summaries, SME notes, Function Specs, Technical Designs, Program Specs, File Specs, interface specs, and data dictionaries into evidence-bounded four-view elicitation and coverage files. Treat unreadable files, missing Markdown, OCR/tool limits, sparse sources, and incomplete views as warnings/TBDs rather than workflow blockers. Hard-stop only on evidence authorization/redaction safety or attempts to treat AI-organized context as approved rules, BRD facts, or canonical module flows."
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy Flow Context Normalizer

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Turns scattered docs, diagrams, RAG notes, and SME fragments into four-view evidence slots, gaps, and SME questions that can be reviewed safely. |
| Input | Normalized documents, exported diagrams, RAG summaries, SME notes, specs, data dictionaries, and known contradictions. |
| Output | Evidence-bounded L3/L2 context coverage views or L1 source-quality triage with readiness status. |
| Core prompt strategy | Preserve contradictions, separate confirmed facts from candidate-only context, avoid generating missing flow logic, and route low-quality inputs to triage. |
| Upstream skill | `legacy-document-evidence-intake` or external RAG / document discovery. |
| Downstream consumer | `legacy-module-context-intake`, `legacy-ibmi-module-analyzer`, and BRD preparation. |
| Validation standard | Module scope is explicit, evidence is authorized, every view item has a source classification, and candidate-only content cannot feed BRD conclusions. |
| Known risk | Treating a plausible AI-organized diagram or RAG summary as an approved module flow or BRD fact. |
| Practical example | Normalize a Function Spec, Visio export, and SME notes into operation/system/program/data coverage views, open questions, and source-backed review prompts. |

## Purpose

Turn scattered historical documentation and specs into an **evidence-linked
four-view elicitation and coverage package**:

```text
00_context_packages/<MODULE-SLUG>/flow-normalization/
|-- flow-context-index.yaml
|-- source-document-index.yaml
|-- 01-operation-business-flow.md
|-- 02-system-flow.md
|-- 03-program-flow.md
|-- 04-data-flow.md
|-- evidence-map.md
|-- contradiction-log.md
|-- open-questions.md
`-- sme-review-pack.md
```

This skill is the upstream bridge for teams whose knowledge is trapped in
Visio, Word, Excel, PDF, PowerPoint, exported screenshots, Function Specs,
Technical Designs, Program Specs, File Specs, interface specs, data dictionary
extracts, old process decks, runbooks, or SME notes. The four context views are
elicitation slots and coverage checks, not a requirement that the SME already
knows all four views and not permission for the model to invent them. This
skill makes the material reviewable, but it does **not** approve context, mint
final `BR-*` rules, generate missing flow sequences, or generate a BRD.

These files are context coverage views under `00_context_packages/`, not the
canonical module-analysis artifacts under `04_modules/`. When reporting this
step to a user, call them **context coverage views**, an **elicitation
package**, or a **flow-normalization package**. Do not say this step created
the final four module flows or BRD-ready process facts. The canonical
`01-operation-flow.md` / `02-system-flow.md` / `03-program-flow.md` /
`04-data-flow.md` module artifacts are produced later by
`legacy-ibmi-module-analyzer`.

## Boundary

Use this skill only when the user explicitly asks for a
`flow-normalization/` package or when maintaining an existing legacy
`flow-normalization/` package. It is not part of the default chain; for normal
document-first work, route document-intake outputs, source metadata, RAG notes,
or SME fragments directly to `legacy-module-context-intake`.

Do not use it as a replacement for:

- `legacy-ibmi-evidence-intake` when raw source/runtime evidence authorization
  or redaction is unresolved.
- `legacy-module-context-intake` when the four context views are already
  SME-reviewed or explicitly supplied as human-confirmed context.
- `legacy-ibmi-flow-analyzer` when the task is source-backed call-chain
  analysis across IBM i programs.
- `legacy-brd-writer` when the user wants the BRD; BRD generation requires
  approved module context first.

## Required Inputs

- Module slug, business name, draft scope statement, and owner or SME role.
- One or more source documents, specs, exported readable forms, source
  metadata, or SME-provided scope clues. Markdown, text, CSV, modern Office
  text exports, normalized document-intake packages, or pasted SME notes are
  helpful but not required. Raw binary Office/Visio files, scanned images, and
  OCR/converter-dependent sources are common in enterprise environments; if
  they cannot be read without tooling, register them as low-confidence inputs,
  add explicit `TBD-*` supplement requests, and continue with whatever source
  metadata or readable clues exist:
  - Visio / diagram exports (`.vsdx`, PDF, SVG, PNG, or image export)
  - Word / runbook / procedure docs
  - Excel / CSV process, application, interface, data dictionary, or CRUD lists
  - PDF / PPT / PPTX decks
  - Function Specs / Functional Specs / requirement catalogues
  - Technical Designs / architecture or integration designs
  - Program Specs / job specs / screen-report specs
  - File Specs / record layouts / table specs / field dictionaries
  - Interface Specs / batch layout specs / API message specs
  - RAG or code-knowledge summaries
  - SME notes, meeting notes, or annotated screenshots
- Evidence authorization signal for every source:
  - approved evidence manifest,
  - synthetic / non-production / public classification, or
  - explicit owner approval for agent review.

## Safety Stop Conditions

Context normalization quality should not stop the modernization workflow. Stop
and produce only blocking findings if a safety or truthfulness condition applies:

| Condition | Route |
| --- | --- |
| Any source/runtime evidence has unknown sensitivity or missing authorization | `legacy-ibmi-evidence-intake` |
| Confidential or production evidence needs redaction and no approved redaction exists | `legacy-ibmi-evidence-intake` |
| Contradictions are found but the user asks to hide or smooth them over | block; keep `contradiction-log.md` visible |
| Draft flows are requested as approved rules, approved module context, or BRD input without SME review | block; route through SME review first |

Missing one or more of the four standard context views is **not** a stop
condition. Create the missing view file with a placeholder coverage node, a
`TBD-*` question, and `coverage.<view>: absent` or `partial`. If no flow can be
safely supported by supplied evidence, produce a source-quality triage package
instead of inventing a sequence and allow downstream work to continue in
degraded mode. The goal is to improve user experience by making incomplete
inputs reviewable while preventing downstream steps from treating AI-organized
context as BRD facts.

Unreadable binary/OCR/converter-dependent sources are also **not** a stop
condition. Add the unreadable source to `source-document-index.yaml` with
`readable_status: manual_export_required`, `skipped_optional_binary`,
`tool_unavailable`, or equivalent notes, set its evidence strength to low, add
a `TBD-*` asking for a readable export or SME visual summary, and continue
with a triage/degraded package. Do not invoke `legacy-document-evidence-intake`
automatically just to process optional binaries in hosted-agent mode.

If module slug, business name, or scope is incomplete, use a provisional
module identity derived from the project, document set, or user's stated focus
when possible, record `module_scope_gate: warning`, and carry a `TBD-*` for
SME boundary confirmation. If documents appear to cover multiple modules and no
boundary can be proposed, produce a multi-module triage package or one package
per obvious candidate instead of halting the workflow.

## Input Quality Ladder

Classify the input set before drafting coverage views:

| Level | Signal | Required response |
| --- | --- | --- |
| `L3 strong` | The documents support all four views with visible evidence. | Produce four substantive coverage view files with source-linked statements, supported diagram edges only where evidence supplies sequence, candidate seeds, and SME questions. |
| `L2 partial` | The documents support one to three views. | Produce substantive coverage views where evidence exists; create placeholders and `TBD-*` questions for missing views; route to SME review. |
| `L1 sparse` | Documents are authorized but too sparse, unreadable in the current runtime, non-Markdown, OCR/tool-constrained, or limited to source/scope clues. | Produce the same ten-file package as a source-quality triage artifact: all four view files use placeholders, `open-questions.md` lists the minimum supplement request, `normalization.status` is `triage_needs_source_enrichment`, and downstream may continue with low-confidence restrictions. |
| `L0 safety_stop` | Evidence authorization/redaction is unresolved, or the user asks to hide contradictions / treat candidate coverage as approved. | Stop with blocking findings and route to evidence intake or SME review; do not read unauthorized content or promote candidate facts. |

`L1 sparse` is still useful output. It should identify what was found, why no
flow should be inferred, which source types would unlock the next pass, and
which SME questions can resolve the gap fastest.

If the team has already attempted supplement collection and the source owner
or SME confirms that no additional document, spec, or flow input can be
provided, do not loop forever asking for more. Record an explicit
risk-acceptance decision when available. A named accountable owner may convert
`triage_needs_source_enrichment` to `ready_with_warnings`, but this conversion
is no longer required just to continue the chain. A triage package may proceed
to downstream context intake as low-confidence review material; it must remain
`quality_level: L1 sparse`, carry every missing view as `TBD-*`, and tell
downstream skills not to treat anything from the package as confirmed facts.

## Output Contract

Use `references/output-contract.md` for required fields and examples. Start
from the templates under `templates/`.

Runtime tooling rule: the bundled Python helpers are standard-library scripts
and optional execution aids, not environment setup triggers. Run them only with
an already-available Python interpreter. Do not create a virtual environment,
install packages, or wait on interactive environment configuration. If
interpreter discovery or startup remains in a configuring/evaluating state,
record Python as `tool_unavailable` for this run, continue with manual package
drafting where possible, and list the exact remediation in `open-questions.md`
and `flow-context-index.yaml`.

Mermaid preview guardrail: Mermaid source blocks are required; IDE, browser, or
extension-rendered Mermaid previews are optional. Do not open diagram previews
as part of this skill unless the user explicitly asks for visual preview. For
large modules, large document sets, or diagrams with more than about 80
nodes/edges, mark `run_validation.mermaid_preview_status` as
`skipped_large_module` and continue after structural validation. Never open the
same preview repeatedly. If one explicitly requested preview attempt takes more
than about 30 seconds, record `timed_out` or `skipped_large_module`, report the
manual preview path, and finish the run.

GitHub Copilot hosted-agent mode is stricter: do not run Python commands,
shell probes, Excel helpers, validators, package installs, or environment setup
from this skill unless the user explicitly confirms the runtime is already
prepared. Draft the four context-view files manually from readable supplied
content, record validation/helper execution as `tool_unavailable_hosted_agent`,
and report the validator/helper script paths as manual follow-up text. Do not
enter or wait on Python environment setup.

For deterministic local validation outside hosted Copilot mode, run
`skills/legacy-flow-context-normalizer/scripts/validate_flow_context_package.py`
with an existing Python interpreter against
`00_context_packages/<MODULE-SLUG>/flow-normalization`.

For multi-sheet Excel intake, generate an initial `source-document-index.yaml`
fragment draft manually in hosted Copilot mode. Outside hosted Copilot mode,
the optional helper path is
`skills/legacy-flow-context-normalizer/scripts/extract_excel_fragments.py`; run
it only with an existing Python interpreter and explicit workbook/package
arguments.

The package status in `flow-context-index.yaml` must be one of:

- `draft_needs_sme_review`
- `triage_needs_source_enrichment`
- `ready_for_context_intake`
- `ready_with_warnings`
- `blocked_pending_evidence`
- `blocked_pending_contradiction_review`
- `blocked_pending_scope` (legacy compatibility only; prefer `triage_needs_source_enrichment`)
- `blocked_pending_readable_source` (legacy compatibility only; prefer `triage_needs_source_enrichment`)

Allowed handoff:

- `draft_needs_sme_review` -> SME review or `legacy-sme-review-facilitator`
- `triage_needs_source_enrichment` -> source owner / SME supplement request
  **or** `legacy-module-context-intake` in degraded mode with all gaps carried
  forward as low-confidence TBDs
- `ready_for_context_intake` / `ready_with_warnings` -> `legacy-module-context-intake`
- safety `blocked_*` statuses -> do not read or promote unsafe content; record
  exact remediation in `open-questions.md` and `flow-context-index.yaml`.
  Do not use `blocked_pending_readable_source` or `blocked_pending_scope` for
  ordinary context quality gaps; use `triage_needs_source_enrichment` instead.

## Step Contract

This skill conforms to the Legacy Spec Factory Step Contract.

### Input

- **Required**: module identity or provisional focus, source document list or
  source metadata, and evidence authorization. Readable content is preferred
  but not mandatory; when content cannot be read in the current environment,
  create an L1 sparse triage package rather than blocking the workflow.
- **Optional**: existing RAG output, Function Specs, Technical Designs,
  Program Specs, File Specs, interface specs, ARCAD / application inventory
  extracts, data dictionary exports, screen/report samples, meeting notes,
  known SME owner, and reviewed module glossary.
- **Technical-anchor supplements for View 3 / View 4**: API IDs, journey IDs,
  menu IDs, screen IDs, and business data labels are not enough to draw IBM i
  program or data views. For a substantive View 3, request at least one
  AS400 / IBM i program, job, service program, CL/RPG object, or explicit
  API/menu-to-program mapping. For a substantive View 4, request at least one
  AS400 / IBM i PF/LF, SQL table, data area, data queue, printer/display file,
  file spec, DDS/DDL extract, CRUD matrix, or explicit business-data-to-file
  mapping.
- **Input readiness scoring**:
  - `0-5 safety_stop`: evidence authorization/redaction unresolved, or the
    requested output would promote candidate context as approved facts.
  - `6 minimum_pass`: module identity, authorized readable documents, and at
    least one module-relevant clue are present; if no flow can be evidenced,
    emit `triage_needs_source_enrichment`.
  - `6 degraded_pass`: module identity or provisional focus and authorized
    source metadata are present, but source files are unreadable/non-Markdown
    or OCR/tool-constrained. Emit `triage_needs_source_enrichment` and continue
    downstream with warnings.
  - `7-8 usable`: documents cover one or more views with visible source
    provenance, gaps, and contradictions; missing views are represented as
    explicit `TBD-*` questions rather than blockers.
  - `9-10 strong`: each view has multiple corroborating sources, View 3 has
    IBM i program/job anchors, View 4 has IBM i file/table/data-object anchors,
    data dictionary or interface context is present, and SME owner is assigned.

### Execution

- **Procedure**: follow the Workflow below.
- **Allowed inference**: classify document fragments into the four views;
  normalize labels; preserve supplied source order when explicit; connect
  repeated system, program, file, and actor names across sources when evidence
  is visible.
- **Forbidden assumptions**: inventing actors, systems, programs, file names,
  field meanings, sequence order, trigger timing, exception handling, manual
  workarounds, business rules, SLAs, BRD facts, or modernization decisions. Do not
  promote API IDs, journey IDs, menu IDs, screen IDs, or business labels into
  AS400 program names or file names.
- **ID policy**: may mint `DOC-*`, `FRAG-*`, `STEP-*`, `SYS-*`, `PGM-*`,
  `DATA-*`, `CAND-*`, `CONFLICT-*`, and `TBD-*` within the draft
  package. Do not mint final `BR-*`, `CAP-*`, `DEC-*`, `AC-*`, or `TC-*`.

### Output

- **Canonical directory**:
  `00_context_packages/<MODULE-SLUG>/flow-normalization/`.
- **Required files**: the ten files listed in Purpose.
- **Required gates**: evidence authorization, readable source, module scope,
  four-view coverage, contradiction visibility, source classification, SME
  review, and no rule or BRD-fact promotion.
- **Handoff status**: `ready_for_context_intake`, `ready_with_warnings`, and
  `triage_needs_source_enrichment` may feed `legacy-module-context-intake`.
  A triage handoff is degraded: all absent views remain `TBD-*`, all context is
  low-confidence, and downstream skills must not convert the package into
  approved BRD facts, `BR-*`, modernization decisions, or canonical module
  flows without later SME/code/runtime corroboration.

### Validation

- **Mechanical**: all required files exist; the index lists every input and
  output; every view file has status, summary, source-linked context items,
  candidate seeds, and gaps; every evidence ID referenced by a view appears in
  `evidence-map.md`.
- **Semantic**: no AI-organized context or candidate coverage is presented as approved
  or BRD-ready; contradictions are not hidden; View 1 uses business language
  first; View 2 captures system and integration behavior only where sourced;
  View 3 captures application/program/job behavior only where anchored; View 4
  captures data movement and ownership questions only where anchored; View 3
  uses IBM i program/job anchors when available and otherwise carries a
  supplement TBD; View 4 uses IBM i file/table/data-object anchors when
  available and otherwise carries a supplement TBD; BRD functional analysis
  hints record which extracted fragments can become SME questions or source
  mapping, not BRD conclusions.
- **SME / human approval**: SME or accountable owner confirms module boundary,
  flow sequence, missing or obsolete documents, exception behavior, manual
  steps, and which contradictions block context intake.
- **Blocking conditions**: authorization/redaction gaps, hidden contradiction,
  missing evidence links for major flow steps that are stated as facts, or
  absent SME decision when package claims `ready_for_context_intake`. No
  readable source, non-Markdown documents, missing OCR, missing four-view
  coverage, and rough module scope are warning/degraded conditions, not
  workflow blockers. Use `triage_needs_source_enrichment` rather than a
  blocked status and carry all gaps forward as low-confidence `TBD-*` items.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with status
`pass`, `pass_with_warnings`, or `blocked` when reporting upward to the
orchestrator. Context-quality gaps should normally report
`pass_with_warnings`; reserve `blocked` for safety/truthfulness stops.

## Workflow

1. **Resolve module identity**
   - Confirm `MODULE-SLUG`, business name, scope statement, owner, and SME role.
   - If one document bundle covers multiple modules, split or block until SME
     assigns boundaries.

2. **Gate evidence authorization**
   - Check source sensitivity, redaction, and owner approval before reading
     content.
   - If **any** source has unknown authorization, route the entire package to
     `legacy-ibmi-evidence-intake`. Do not proceed with only the authorized
     subset; authorization must be resolved for every document before
     normalization begins.
   - Exception: if an unauthorized document is clearly out of scope and the
     owner explicitly confirms it can be excluded, set its `readable_status` to
     `not_needed`, record the exclusion in `open-questions.md`, and proceed
     with the remaining authorized documents.

3. **Inventory source documents**
   - Create `source-document-index.yaml`.
   - Assign stable `DOC-*` IDs and record path, format, source document role,
     readable extraction method, sensitivity, owner, date, and confidence.
   - Keep `format` (file type such as `.xlsx` or `.docx`) separate from
     `source_type` (document role such as `function_spec`, `technical_design`,
     `program_spec`, `file_spec`, `interface_spec`, or `flow_diagram`).
   - Follow `references/source-classification.md` for format-specific notes.

4. **Extract candidate fragments**
   - Extract only enough content needed for flow normalization.
   - Mint `FRAG-*` IDs for relevant diagram nodes, table rows, paragraphs,
     slide elements, or SME notes.
   - Preserve page, sheet, slide, row, shape, or section references.
   - For `.xlsx` workbooks, prefer the bundled
     `scripts/extract_excel_fragments.py` helper. It enumerates every sheet,
     treats the first non-empty row as headers, emits one `FRAG-*` per
     non-empty data row, and classifies fragments by sheet/header keywords into
     Operation / Business, System, Program, Data, or `cross_view`. Sheet names
     such as `Function Spec`, `Technical Design`, `Program Spec`, and
     `File Spec` are classification signals, not mandatory sheets.

5. **Classify input quality**
   - Set `quality_level` to `L3 strong`, `L2 partial`, `L1 sparse`, or
     `L0 safety_stop`.
   - Record the reason in `flow-context-index.yaml.normalization.
     decision_reason`.
   - For `L1 sparse`, do not invent sequence or edges. Continue to create the
     ten-file package as a triage artifact with all four views marked
     `absent`, placeholder coverage nodes, and prioritized supplement requests.

6. **Classify fragments into four views**
   - Operation / Business Flow: actors, BAU sequence, approvals, manual steps,
     exceptions, customer or operational outcome.
   - System Flow: upstream/downstream systems, interfaces, batches, queues,
     files, schedules, security/SLA hints.
   - Program Flow: IBM i programs, jobs, service programs, CL/RPG objects,
     call hints, trigger points, and technical branching. API IDs, journey
     IDs, menu IDs, and screen IDs may appear only as trigger or boundary
     context unless the source explicitly maps them to IBM i programs.
   - Data Flow: IBM i files/tables, PF/LF objects, SQL tables, data areas,
     data queues, display/printer files, fields, CRUD direction, derivation,
     retention, and ownership. Business data labels may appear only as
     descriptions unless mapped to concrete IBM i objects.

7. **Draft each coverage view**
   - Use `templates/view-template.md`.
   - Include a `Mermaid Flow Diagram` in every view only as a sourced review
     surface. The evidence table remains the traceability surface, and
     unsupported edges must be replaced by `TBD-*` nodes/questions.
   - Run the View 3 / View 4 technical-anchor gate before drawing diagrams:
     - If View 3 evidence has API/menu/journey/screen labels but no IBM i
       program/job/object names, do **not** draw those labels as program nodes.
       Create a placeholder node and `TBD-*` asking for API/menu-to-program
       mapping, inventory, ARCAD export, DSPPGMREF/call graph, program spec,
       or SME confirmation.
     - If View 4 evidence has business data labels but no IBM i file/table/
       data-object names, do **not** draw those labels as data nodes. Create a
       placeholder node and `TBD-*` asking for file specs, DDS/DDL, data
       dictionary, CRUD matrix, File I/O map, or SME mapping.
   - Draw Mermaid edges only when the source evidence or SME note supports the
     sequence. Mark uncertain nodes as `(needs SME review)` or `candidate_only`
     instead of making the diagram look approved.
   - Keep every major step evidence-linked and marked `needs_sme_review`.
   - Put technical names in `Evidence Basis` when the view is business-facing.
   - If a view has no usable source fragments, still create the view file with
     one Mermaid placeholder node, one evidence-linked placeholder row pointing
     to the available source set or `TBD-*`, and a blocking or non-blocking SME
     question. Mark coverage as `absent`, not `blocked`, unless the package
     would otherwise invent facts.

8. **Build evidence map**
   - Use `templates/evidence-map.md`.
   - Map every `DOC-*` / `FRAG-*` / source row to the views that use it.

9. **Carry contradictions and gaps**
   - Use `templates/contradiction-log.md` and `templates/open-questions.md`.
   - Keep obsolete-document signals visible rather than deleting them.
   - Ask SME to decide whether a contradiction is blocking, obsolete, or a real
     alternate path.

10. **Prepare SME review package**
   - Use `templates/sme-review-pack.md`.
   - Group questions by view and prioritize blockers first.
   - Include explicit approval choices; do not ask SME to review raw dumps.

11. **Set handoff status**
    - `draft_needs_sme_review` when flow content is usable but SME decision is
      not recorded.
    - `triage_needs_source_enrichment` when authorized documents are sparse,
      unreadable in the current runtime, non-Markdown, OCR/tool-constrained,
      or module-relevant but no flow sequence is evidenced. Route to source
      owner / SME supplement request and allow `legacy-module-context-intake`
      to continue in degraded mode; do not route directly to approved BRD
      claims.
    - Convert `triage_needs_source_enrichment` to `ready_with_warnings` when a
      named SME/source owner records that no additional document, spec, or flow
      input can be provided and accepts carrying the gaps forward. Preserve
      `quality_level: L1 sparse`; do not upgrade coverage or confidence.
    - `ready_for_context_intake` only when SME review confirms all four
      context views for intake. This status still does not make the context
      eligible as a BRD fact source by itself.
    - `ready_with_warnings` only when unresolved items are explicitly
      non-blocking and carried into `open-questions.md`; this is the preferred
      status for SME-accepted partial packages.
    - `blocked_*` only for safety/truthfulness stops: unresolved authorization
      or redaction, hidden contradictions, or a request to promote candidate
      context as approved facts. If a downstream skill would need to invent
      facts, keep the package as `triage_needs_source_enrichment` and force the
      downstream skill to carry `TBD-*` gaps instead.

12. **Validate**
    - In GitHub Copilot hosted-agent mode, do not run the bundled validator.
      Record validation as `tool_unavailable_hosted_agent`, keep the package
      out of `ready_for_context_intake`, and report the validator script path:
      `skills/legacy-flow-context-normalizer/scripts/validate_flow_context_package.py`.
    - In an already-prepared local shell only, run the bundled validator with
      an existing Python interpreter; do not create a virtual environment or
      install dependencies.
    - Fix every reported finding, then re-run until the validator outputs
      `OK: flow context package is structurally valid`.
    - If no Python interpreter is available, or startup remains
      configuring/evaluating for more than about 30 seconds, record validation
      as `tool_unavailable`, keep the package out of
      `ready_for_context_intake`, and report the exact command to run manually.
    - Record the result in `flow-context-index.yaml.run_validation`. Mermaid
      preview status is informational only; it is not a structural validation
      gate.
    - Do not claim `ready_for_context_intake` until the validator passes or a
      manual structural review is recorded. A hosted-agent or tool-unavailable
      run may still continue to SME/source-owner review or
      `legacy-module-context-intake` as a degraded draft/triage package when
      validation status and manual follow-up are recorded.

13. **Finalize and stop**
    - After all ten files are written, `flow-context-index.yaml` is updated,
      workflow state is written back if applicable, and validation status is
      recorded, stop the run and report the package path plus any manual
      validator or preview follow-up.
    - Do not keep re-reading the module directory, repeatedly checking workflow
      status, or reopening Mermaid previews after write-back. Additional
      checks are allowed only when the validator returns a specific finding
      that names a file to fix.

## Handoff

After SME approval, run `legacy-module-context-intake` with:

- the four context-view files from this package,
- `evidence-map.md`,
- `contradiction-log.md`,
- `open-questions.md`,
- `sme-review-pack.md` or the recorded SME decision log,
- evidence authorization metadata.

Do not hand this package directly to `legacy-brd-writer`.

If the user wants a standard code-backed BRD or spec, also tell the
orchestrator that this package is only a context input. Any IBM i programs,
jobs, files, PF/LF, DSPF, PRTF, DDS/DDL, ARCAD, DSPPGMREF, or source snippets
found here must be converted into the code evidence backbone by
`legacy-ibmi-inventory` (`object-map.md`), then `legacy-ibmi-program-analyzer`,
then `legacy-ibmi-flow-analyzer` before BRD approval.

For sparse packages that are `triage_needs_source_enrichment` or were
owner-accepted as `ready_with_warnings`, tell
`legacy-module-context-intake`:

- this is `quality_level: L1 sparse`,
- missing flows are accepted carry-forward TBDs, not confirmed absence,
- no candidate may become an approved fact, `BR-*`, or BRD claim from this
  package alone,
- downstream module analysis must keep confidence low until corroborated by
  source, runtime evidence, or SME decision.

## Version

- v0.1.0 (2026-05-27): Initial document-to-four-view-context normalization skill.
- v0.1.1 (2026-05-27): Added deterministic multi-sheet `.xlsx` extraction
  helper that emits `DOC-*` and `FRAG-*` rows for `source-document-index.yaml`.
- v0.1.2 (2026-05-27): Required Mermaid flow diagrams in every normalized
  view while keeping evidence tables as the traceability source of truth.
- v0.1.3 (2026-05-27): Softened missing-flow handling so partial four-view
  packages can proceed as drafts or SME-accepted warnings instead of blocking.
- v0.1.4 (2026-05-27): Added an input quality ladder and
  `triage_needs_source_enrichment` status for authorized sparse inputs where no
  flow can be safely generated.
- v0.1.5 (2026-05-27): Added the owner risk-acceptance path for cases where
  additional flow input cannot be provided; sparse triage may proceed as
  `ready_with_warnings` only with explicit sign-off and low-confidence
  downstream restrictions.
- v0.1.6 (2026-05-28): Expanded raw input coverage beyond existing flow
  artifacts to Function Specs, Technical Designs, Program Specs, File Specs,
  interface specs, and data dictionaries while keeping all such sources
  optional and evidence-linked.
- v0.1.7 (2026-05-28): Added advisory BRD functional-analysis hints so raw
  flow/context fragments can surface likely inputs for BRD sections 1-9 and
  optional sections 10-12 without making absent facts look confirmed.
- v0.1.8 (2026-05-29): Clarified canonical timing: this skill creates draft
  context views under `00_context_packages/`, while final module four-view
  artifacts are produced only by `legacy-ibmi-module-analyzer`.
- v0.1.9 (2026-05-29): Added View 3 / View 4 technical-anchor gates so API,
  journey, menu, screen, and business data labels are not substituted for IBM i
  program names or file names. Sparse technical evidence now produces explicit
  supplement TBDs instead of misleading diagrams.
- v0.1.10 (2026-05-30): Added handoff guidance that document-normalized
  technical anchors are context only; standard BRD/spec routing must still run
  inventory/object-map, program analysis, and flow analysis before approval.
- v0.1.11 (2026-05-31): Added a large-module Mermaid preview guardrail and a
  stop-after-writeback completion boundary so generated context packages do not
  remain in processing after structural outputs are written.
- v0.1.12 (2026-06-03): Recast flow normalization as evidence-bounded
  elicitation and coverage. AI-organized context may create source-linked
  review surfaces and `TBD-*` questions, but must not generate missing flow
  logic or feed BRD conclusions without SME confirmation or code-backed
  evidence.
- v0.1.13 (2026-06-03): Recast context normalization quality gaps as
  non-blocking degraded handoffs. Missing Markdown, unreadable/OCR-limited
  documents, sparse source sets, rough scope, and missing views now produce
  `triage_needs_source_enrichment` warnings/TBDs that may continue to
  downstream context intake; only authorization/redaction and truthfulness
  violations hard-stop the chain.
- v0.1.14 (2026-06-03): Marked this skill as legacy/manual optional and removed
  it from the default orchestrated chain. New document-first runs should route
  directly from document intake/source metadata to `legacy-module-context-intake`
  unless the user explicitly asks for a `flow-normalization/` package.
