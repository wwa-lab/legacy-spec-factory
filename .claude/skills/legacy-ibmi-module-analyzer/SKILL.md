---
name: legacy-ibmi-module-analyzer
description: Synthesize a complete IBM i business module from multiple flow analyses and BAU notes, producing the canonical 4-view module analysis (Operation Flow, System Flow, Program Flow, Data Flow). Use when multiple flows belong to the same business module and you need cross-flow synthesis to feed `legacy-spec-writer`. Layer 1.5 (platform-specific) skill. Implements the model defined in `docs/module-analysis-model.md`.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Module Analyzer

## Purpose

Synthesize multiple flow analyses, BAU (Business As Usual) notes, and SME
context into one **business module** analysis covering four standard
views: Operation Flow, System Flow, Program Flow, Data Flow.

This skill is the **last platform-specific layer** before `legacy-spec-writer`.
It does not re-analyze flows or programs; it aggregates and synthesizes
what flow-analyzer and program-analyzer produced.

The canonical model is documented in `../../docs/module-analysis-model.md` —
read that first if you have not already.

## Inputs

Accept:

- **Module definition** — module slug, business name, scope statement,
  the list of flows that belong to this module
- **Approved flow analyses** for every flow in scope
  (`flow-<FLOW-SLUG>.md`)
- **Approved program analyses** for every program referenced by those flows
- **Approved inventory** with module scope confirmed
- **BAU notes from SME** — operational rhythm, manual processes,
  exception handling, business context not in code
- **Optional:** architecture diagrams (for System Flow), data lineage
  documents, regulatory references

Stop and require clarification if:

- Any in-scope flow lacks an approved `flow-<FLOW-SLUG>.md` → route to
  `legacy-ibmi-flow-analyzer`
- Module boundary is ambiguous (does flow X belong here or in another
  module?) → SME-only decision
- No SME has confirmed the business name and scope of the module
- BAU notes are absent; the Operation Flow view requires SME input that
  cannot be derived from code alone

## Output Contract

Produce a directory `02_modules/<MODULE-SLUG>/`:

```
02_modules/<MODULE-SLUG>/
├── module-overview.md          ← summary, 4-view index, blocking TBDs, sign-off
├── 01-operation-flow.md        ← View 1: Business view + BAU
├── 02-system-flow.md           ← View 2: Integration view
├── 03-program-flow.md          ← View 3: Application/program view (aggregates flows)
├── 04-data-flow.md             ← View 4: Data view (aggregates Object Dependencies)
└── module-review-checklist.md  ← SME sign-off for the whole module
```

Use:

- `templates/module-overview.md`, `templates/view-*.md` as scaffolding
- `references/output-contract.md` for each view's required fields
- `references/synthesis-rules.md` for how to aggregate across flows
- `references/view-1-operation-flow.md` through `references/view-4-data-flow.md`
  for per-view methodology
- `../../docs/module-analysis-model.md` for the canonical model

Follow:

- `../../docs/id-conventions.md` for stable IDs
  (`MODULE-*`, `VIEW-*`, `BR-*`, `ACTOR-*`, `SYS-*`, `DATA-*`)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence tagging

Examples:

- `examples/module-positive/` — complete CARD-AUTH module with all 4 views
- `examples/incomplete-module-negative/` — module with missing flow / SME gap

## Workflow

1. **Confirm Module Scope**
   - Validate the module slug, business name, and scope statement with SME
   - List in-scope flows; check every one has an approved analysis
   - Confirm no in-scope flow actually belongs to a different module
   - Assign `MODULE-<SLUG>-001`

2. **Aggregate Inventory of Programs & Objects**
   - List every program touched by any flow in scope (from each flow's
     Nodes section)
   - List every object touched (from each program's Object Dependencies
     section)
   - Cross-check against `01_inventory/inventory.yaml`; create
     `pending_source` TBDs for gaps

3. **Build View 1 — Operation Flow / Business Background**
   - See `references/view-1-operation-flow.md`
   - **Primary source: SME interviews + BAU notes.** Code is secondary.
   - Capture: business scope, actors, business events, BAU rhythm,
     manual intervention points, exception lifecycle, business-rule seeds
   - Do **not** derive business rules from field names
   - Output: `01-operation-flow.md`

4. **Build View 2 — System Flow**
   - See `references/view-2-system-flow.md`
   - **Primary source: architecture diagrams, integration specs, SME.**
     Code (especially API/MQ/IFS code in flows) confirms.
   - Capture: upstream systems, downstream systems, external interfaces,
     integration patterns, sync/async boundaries, SLA constraints,
     security boundaries
   - Output: `02-system-flow.md`

5. **Build View 3 — Program Flow (Aggregate)**
   - See `references/view-3-program-flow.md`
   - **Primary source: all `flow-<FLOW-SLUG>.md` documents.**
   - Aggregate per-flow summaries; identify cross-flow dependencies and
     shared sub-programs
   - Do **not** re-derive control flow; reference the flow / program
     analyses
   - Output: `03-program-flow.md`

6. **Build View 4 — Data Flow (Aggregate)**
   - See `references/view-4-data-flow.md`
   - **Primary source: every program's Object Dependencies section,
     aggregated.**
   - Compute data lifecycle per object (created / updated / read /
     archived / purged) by walking flows
   - Compute coupling score (number of flows touching each object)
   - Identify coupling hotspots, cross-module data dependencies, DB
     table relationships
   - Output: `04-data-flow.md`

7. **Cross-View Consistency Check**
   - Every business actor in View 1 should map to at least one entry node
     in View 3 (or be tagged "manual actor — no code path")
   - Every upstream/downstream system in View 2 should appear at least
     once in View 3 as a trigger or external call
   - Every business-rule seed in View 1 must reference at least one
     program / file in View 3 / View 4
   - Every data object in View 4 must trace to at least one flow / program
     in View 3
   - Mismatches → cross-view TBDs

8. **Write module-overview.md**
   - 4-view index with status per view
   - Top blocking TBDs surfaced from any view
   - Module-level capability seeds (which capabilities live in this module,
     to be developed by `legacy-spec-writer`)
   - Module-level review checklist

9. **Prepare for SME Review**
   - Each view independently goes to its appropriate SME (business owner
     for View 1, integration architect for View 2, dev lead for View 3,
     data analyst for View 4)
   - Module is approved only when **all four views** are at least
     `approved_with_non_blocking_tbd`

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md`.
View 1 (Operation Flow) and View 2 (System Flow) **necessarily** rely on
SME and integration documentation (tier 2/3) because business "why" and
architectural intent live outside code. However, any tier-2 claim that
contradicts tier-1 evidence (e.g., SME says "we no longer use path X"
but code still has the path; SME says "every transaction is logged" but
the log write is conditional in code) **does not override the code**.
The spec records what code does; the SME claim becomes a TBD requiring
SME to confirm whether the code is dead, drifted, or correct.

Views 3 and 4 are tier-1-grounded by construction (they aggregate
code-derived flow / program analyses).

**Do NOT invent:**

- **Business actors** not named by SME (no inferring "the marketing team
  uses this" from code)
- **Upstream/downstream systems** not visible in any flow's Trigger
  Context or External Calls section
- **BAU rhythm** (cut-off times, peak hours) — must come from SME
- **Regulatory requirements** — must come from SME or referenced doc
- **Manual intervention procedures** — must come from SME
- **Cross-module data dependencies** without seeing the consuming module's
  inventory or SME confirmation
- **Business rules** — only seeds (questions); the spec-writer resolves
  them with SME

**Instead:**

- If View 1 needs business context not in BAU notes → TBD: pending_sme_judgment
- If View 2 needs integration detail not in any flow → TBD: pending_source
  (request integration spec) or pending_sme
- If a flow seems to belong to multiple modules → TBD: pending_sme_judgment
  on module boundary
- If a data object's lifecycle is incomplete → TBD: pending_sme
  (who archives / purges this?)

**Evidence minimum:**

- Every claim in every view must trace to either source (flow / program /
  inventory) or to a named SME / SME note.
- "Confirmed by SME [name] on [date]" is valid evidence; "common knowledge"
  is not.

## SME Review Questions

Per view:

**View 1 (Operation Flow):**
- Are the business actors complete? Any missing roles?
- Is the BAU rhythm correct? Cut-off times, peak hours, seasonal patterns?
- Are exception-handling procedures accurate?
- Are the business-rule seeds reasonable questions?

**View 2 (System Flow):**
- All upstream and downstream systems listed?
- Integration patterns correct?
- SLAs accurate?

**View 3 (Program Flow):**
- All flows in scope? Any missing or extra flows?
- Cross-flow dependencies correct?
- Shared sub-programs correctly identified?

**View 4 (Data Flow):**
- Data lifecycle correct for each major object?
- Coupling hotspots match operational reality (which files are "scary
  to change")?
- Cross-module data dependencies correctly identified?

## Runtime Portability

Canonical source: `skills/legacy-ibmi-module-analyzer/SKILL.md`

Synced via `scripts/sync-skills.sh` to all four runtime adapters.

## Version History

- v0.1.0 (2026-05-14): Initial release
  - 9-step workflow
  - 4-view synthesis (Operation / System / Program / Data)
  - Cross-view consistency checks
  - Module-level capability seeds (for spec-writer)
  - Feedback loops to flow-analyzer, program-analyzer, inventory
  - Examples: complete module (CARD-AUTH), incomplete module (missing flow)
