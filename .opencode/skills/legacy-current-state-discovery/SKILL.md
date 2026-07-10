---
name: legacy-current-state-discovery
description: Extract evidence-backed current-state functional discovery packages from selected RAG/document evidence, SME notes, spreadsheets, and project folders. Use when a team needs a business-facing functional discovery report plus structured function, validation, calculation, interface, channel/report, accounting-impact, traceability, and gap catalogs from reviewed documents. Routes raw binary documents to legacy-document-evidence-intake, RAG packaging to legacy-module-context-intake, detailed IBM i code/program-flow analysis to legacy-ibmi-program-analyzer or legacy-ibmi-flow-analyzer, and final handoff consolidation to a downstream output generator.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy Current-State Discovery

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Converts selected documents, RAG evidence, spreadsheets, and SME notes into a current-state functional discovery package that SMEs can review and downstream skills can trace. |
| Input | Reviewed document/RAG evidence, source metadata, SME prompts, optional project folders, and optional code anchors. |
| Output | A business-facing functional discovery report plus structured catalogs for functions, project-derived features, validation, calculation, interfaces, channels/reports, accounting impact, traceability, and gaps. |
| Core prompt strategy | Index evidence first, extract candidate current-state facts with confidence labels, separate document-supported facts from code-required details, and keep gaps visible. |
| Upstream skill | `legacy-document-evidence-intake`, `legacy-module-context-intake`, external RAG retrieval, or SME-provided reviewed evidence. |
| Downstream consumer | `legacy-ibmi-program-analyzer`, `legacy-ibmi-flow-analyzer`, `legacy-brd-writer`, final output generators, and SME review workflows. |
| Validation standard | Every candidate fact has source provenance, confidence, and review status; unsupported exact formulas, thresholds, GL/IE accounts, transaction rules, and code-level behavior stay gaps. |
| Known risk | Treating high-level documents as behavior ground truth, creating section-shaped but low-value summaries, or mixing current-state functions with project-derived target features. |

## Purpose

Create a **document-first current-state discovery package** for one module,
capability, function, or business event. This skill fills the gap between raw
RAG retrieval and final handoff generation: it turns reviewed evidence into
candidate functional facts and a business-readable report without approving
business rules or replacing IBM i source analysis.

Use this skill to produce both:

- structured extraction artifacts that downstream tools can merge, validate, or
  cross-reference; and
- an SME-friendly `functional-discovery-report.md` using the business review
  shape teams expect: existing functionality, process flow, upstream/downstream
  applications, configuration, channels, reports, communications, operational
  procedure, limitations, gaps, and BRD cross-reference.

## Boundary

This skill is not the RAG retriever, code analyzer, or final output generator.

- If the source is raw Office, Visio, PDF, scanned image, or other binary
  material that has not been normalized, route first to
  `legacy-document-evidence-intake`.
- If the user only has a RAG/context bundle that needs provenance packaging,
  route first to `legacy-module-context-intake`.
- If the request depends on true program behavior, detailed authorization
  validation, message/transaction types, field-level file flow, persisted
  mutations, or exception propagation, route the code path to
  `legacy-ibmi-program-analyzer` or `legacy-ibmi-flow-analyzer`.
- If the requested output is an executive-ready consolidated handoff from
  already-created catalogs, route to the final output generator pattern.

Documents and diagrams are navigation/context evidence. Code, runtime evidence,
approved configuration exports, and SME sign-off are required for behavior
claims that affect money, customer status, regulatory control, posting, or
field-level validation.

## Required Inputs

- Module or capability slug, business name, and scope statement.
- One discovery focus: a function name, business event, process, module,
  product area, or SME question.
- Reviewed evidence set, preferably with document names, paths, sections,
  page numbers, chunk IDs, or RAG snippet IDs.
- Evidence authorization and sensitivity status for every source artifact.
- SME prompt or review intent, including whether the expected result is a
  business-facing report, structured catalogs, or both.
- Optional: project-derived feature folders, BRD references, Visio/program-flow
  diagrams, key program names, interface lists, report inventories, or
  accounting/GL/IE extracts.

## Stop and Reroute Conditions

| Condition | Action |
| --- | --- |
| Source authorization or sensitivity is unknown | Stop and route to `legacy-ibmi-evidence-intake` or the owning evidence gate. |
| Raw document format cannot be read reliably | Route to `legacy-document-evidence-intake`. |
| No selected evidence remains after retrieval | Ask for a RAG retrieval/evidence pack; do not invent a package. |
| The user asks for exact formula, status-code table, GL account, IE item, transaction type, or validation branch and documents are high-level | Mark the item as a gap and route the code path to IBM i program/flow analysis. |
| Documents contradict code-backed evidence | Preserve both, mark `contradictory`, and route to SME review. |
| The output is meant to be approved BRD/spec content | Route through BRD/spec skills after SME review; this skill emits candidates only. |

## Output Package

Create the package under:

```text
00_context_packages/<MODULE-SLUG>/current-state-discovery/<DISCOVERY-SLUG>/
```

Use `references/output-contract.md` and the files under `templates/`.

Required files:

- `discovery-index.yaml`
- `document-master-index.md`
- `behavior-claim-ledger.csv`
- `functional-discovery-report.md`
- `function-catalog.yaml`
- `project-derived-feature-index.yaml`
- `validation-catalog.yaml`
- `calculation-catalog.yaml`
- `interface-register.yaml`
- `channel-ui-report-catalog.md`
- `accounting-gl-ie-index.yaml`
- `traceability-matrix.csv`
- `open-questions-and-gaps.md`

Package status values:

- `draft`
- `ready_for_sme_review`
- `ready_with_warnings`
- `blocked_pending_evidence`
- `blocked_pending_code_analysis`
- `blocked_pending_scope`

## Workflow

1. **Confirm Scope and Route**
   - Name the module/capability, discovery focus, source set, and expected
     deliverables.
   - Decide whether this run is document-first only or needs a code-grounded
     branch. Use `references/document-vs-code-routing.md`.
   - Keep one package focused on one coherent function, business event, or
     module slice. Do not merge unrelated functional areas.

2. **Build the Document Master Index**
   - Register every selected source, including documents not parsed or not used.
   - Capture source ID, title/path, evidence type, retrieval query/chunk when
     available, candidate domain, parse/review status, and notes.
   - Mark unparsed or unsupported sources as `Not Reviewed`; do not silently
     omit them.

3. **Extract Atomic Behavior Claims**
   - Before writing the report, build `behavior-claim-ledger.csv`.
   - Use separate ID namespaces: `BCL-*` for behavior claims, `CAND-*`
     for function candidates, `TBD-*` for gaps/questions, and `SRC-*` or
     provided source IDs for evidence sources. Do not use one generic `CLM-*`
     namespace for claims, gaps, sources, and functions.
   - Each non-gap row must state the business meaning, trigger or condition,
     system behavior, source coordinate, evidence ID, confidence, and review
     route.
   - A source discovery fact such as "folder contains CU101A" or "diagram has
     node CUG39" is not a functional behavior by itself. It may support a route
     to code analysis, but it must not be promoted to Existing Functionality
     unless the evidence also describes behavior.
   - If the evidence only shows a diagram node, filename, program name, heading,
     or document inventory item, record it as `Gap`, `Not Reviewed`, or
     `blocked_pending_code_analysis` with a specific next action.

4. **Extract Current-State Functional Candidates**
   - Identify functions/components as business capabilities or user/system
     behaviors, not as isolated fields or screens.
   - For each candidate, capture purpose, happy/unhappy paths, rules,
     eligibility, conditions, process flow, channels, UI/report/notification,
     applications, configuration, operational procedure, limitations, evidence,
     confidence, and gaps.
   - Use `CAND-*` IDs for draft function candidates unless a project profile
     defines a different functional ID namespace.
   - Populate candidates from behavior claims, not directly from file names,
     diagram labels, or broad RAG snippets.

5. **Separate Project-Derived Features**
   - Put project changes, new features, migration requirements, and future-state
     design ideas in `project-derived-feature-index.yaml`.
   - Do not mix them into current-state functionality unless evidence proves the
     legacy system already behaves that way.

6. **Extract Supporting Catalogs**
   - Create validation, calculation, interface, channel/UI/report, accounting,
     and gap artifacts from the same evidence set.
   - Exact formulas, rates, thresholds, status codes, GL accounts, IE items,
     posting rules, and transaction definitions must cite evidence. If exact
     details are absent, record only a candidate pattern plus the missing source.

7. **Apply Confidence and Evidence Rules**
   - Use the shared labels `Confirmed`, `Strongly Indicated`, `Inferred`,
     `Gap`, and `Not Reviewed`.
   - Map labels to evidence strength without treating confidence as approval.
     See `references/evidence-confidence-rules.md`.
   - Every material claim needs source coordinates or an explicit gap.

8. **Write the Business-Facing Report**
   - Use `templates/functional-discovery-report.md`.
   - Keep the report readable for SMEs and BAs; detailed catalogs carry the
     machine-oriented fields.
   - Do not hide gaps under polished prose.
   - Prefer tables for populated sections. Every material statement must show
     the related `BCL-*` or `CAND-*`, confidence, source locator, and gap or
     next action.
   - Avoid standalone statements like "likely exists", "suggests a flow", or
     "appears related" unless the sentence also explains the missing evidence
     and review route.
   - Gap Analysis must be actionable, with gap ID, area, missing evidence,
     impact, owner/route, next action, and status.

9. **Run the Meaningful Output Gate**
   - Check that the package contains specific behavior, not just a list of
     artifacts discovered.
   - For each populated section, ask: "Can an SME decide whether this is right,
     wrong, incomplete, or needs code verification?" If not, rewrite it as a
     gap or drill into the evidence.
   - Do not mark a package `ready_for_sme_review` if the only confirmed facts
     are source inventory, diagram nodes, or program names.
   - A useful document-first package may still be mostly gaps, but the gaps must
     be precise enough to drive retrieval, code analysis, or SME review.

10. **Prepare Handoff**
   - If code-grounded analysis is required, list exact programs, flows, fields,
     files, or transaction/message types needed by the IBM i analyzers.
   - If SME approval is required, list review questions and candidate IDs.
   - If the package is strong enough for downstream context, route to
     `legacy-module-context-intake` or BRD preparation as low-confidence input
     unless SME approval upgrades it.

## Anti-Hallucination Rules

- No evidence, no fact.
- Do not invent exact production values, formulas, account numbers, IE codes,
  status codes, thresholds, transaction types, file layouts, program names,
  report IDs, or security controls.
- Do not convert document wording into approved business rules. Use candidate
  statements and SME questions.
- Do not promote RAG snippets, generated drafts, or project documents to legacy
  current-state facts without source provenance and confidence labels.
- Do not treat Visio/program-flow diagrams as behavior ground truth; use them
  to navigate code-grounded analysis.
- Preserve contradictions and unresolved gaps as first-class outputs.

## Validation

Before handoff, verify:

- all required files exist or are explicitly marked not produced with a reason;
- `behavior-claim-ledger.csv` contains atomic behavior claims or explicit gaps,
  not only discovered filenames, diagram nodes, or vague summaries;
- ID namespaces are separated (`BCL-*`, `CAND-*`, `TBD-*`, source IDs) rather
  than collapsed into one generic claim namespace;
- every candidate function has evidence, confidence, and review status;
- current-state and project-derived features are separate;
- exact formulas, GL/IE mappings, thresholds, and transaction definitions are
  either evidenced or marked as gaps;
- documents not reviewed are visible in the Document Master Index;
- code-required items are routed to the IBM i program/flow analyzers;
- the SME-facing report matches the structured catalogs and does not add new
  unsupported facts.

On Windows/Cline, run the validator through the installed current-state skill
router. It tries `py -3`, then `python`, then the native Windows PowerShell 5.1
validator. Do not construct `py ... || python ...` commands in PowerShell 5.1:

```powershell
powershell -NoProfile -File .agents\skills\legacy-current-state-discovery\scripts\invoke-windows-tool.ps1 `
  ValidateCurrentStateDiscovery `
  00_context_packages\<MODULE-SLUG>\current-state-discovery\<DISCOVERY-SLUG>
```

On macOS/Linux, run:

```bash
python3 skills/legacy-current-state-discovery/scripts/validate_current_state_discovery_package.py \
  00_context_packages/<MODULE-SLUG>/current-state-discovery/<DISCOVERY-SLUG>
```

Use the stricter gate before SME review:

Windows/Cline:

```powershell
powershell -NoProfile -File .agents\skills\legacy-current-state-discovery\scripts\invoke-windows-tool.ps1 `
  ValidateCurrentStateDiscovery `
  --quality-gate --require-ready `
  00_context_packages\<MODULE-SLUG>\current-state-discovery\<DISCOVERY-SLUG>
```

macOS/Linux:

```bash
python3 skills/legacy-current-state-discovery/scripts/validate_current_state_discovery_package.py \
  --quality-gate \
  --require-ready \
  00_context_packages/<MODULE-SLUG>/current-state-discovery/<DISCOVERY-SLUG>
```

## Runtime Portability

Canonical source: `skills/legacy-current-state-discovery/SKILL.md`

Runtime adapters are synced via `scripts/sync-skills.sh`:

- Codex: `.codex/skills/legacy-current-state-discovery/SKILL.md`
- Claude Code: `.claude/skills/legacy-current-state-discovery/SKILL.md`
- OpenCode: `.opencode/skills/legacy-current-state-discovery/SKILL.md`
- Agents: `.agents/skills/legacy-current-state-discovery/SKILL.md`

No runtime-specific assumptions are embedded in the canonical source.

## Version History

- v0.1.1 (2026-07-10): Python-first Windows PowerShell fallback
  - Added native Windows PowerShell 5.1 package validation for machines
    without Python.
  - Standardized Windows/Cline routing as `py -3`, then `python`, then native
    PowerShell while preserving strict quality-gate behavior.

- v0.1.2 (2026-07-10): Installed-skill Windows router
  - Added a skill-local Windows launcher so synced `.agents`, `.claude`,
    `.codex`, and `.opencode` installs do not depend on a repository-root
    `scripts\invoke-windows-tool.ps1`.
  - Prohibited `py -3 ... || python ...` fallback chains under Windows
    PowerShell 5.1.
