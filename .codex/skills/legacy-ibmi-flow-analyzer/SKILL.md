---
name: legacy-ibmi-flow-analyzer
description: Analyze a complete IBM i call chain — one business transaction end-to-end across all programs it touches. Supports seven trigger models (batch job, interactive menu, subfile dispatch, F-key branch, DB trigger, scheduler, API/remote). Produces a flow analysis covering trigger context, sequence, cross-program data flow, error propagation, commit boundaries, UI surfaces, and business-capability seeds. Use when a single program analysis is insufficient because the business event spans multiple programs. Layer 1.5 (platform-specific) skill of the Legacy Spec Factory reverse chain.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Flow Analyzer

## Purpose

Analyze one **call chain** — a complete business transaction that spans
multiple programs, from trigger to final outcome. Where
`legacy-ibmi-program-analyzer` looks inside one program, this skill looks
across programs: how they are stitched together, what data passes between
them, when they branch, and how errors propagate.

This skill does **not** re-analyze individual programs. Every program in
the flow must already have an approved
`program-analysis-<OBJ-ID>.md`; if any is missing, route back to
`legacy-ibmi-program-analyzer`.

This skill does **not** infer business rules. It captures the *structure*
of the transaction so that downstream `legacy-spec-writer` (via
`legacy-ibmi-module-analyzer`) can derive business rules with proper SME
involvement.

## Inputs

Accept:

- **Flow definition** — the entry point of the chain, declared as one of
  seven trigger types (see `references/trigger-models.md`):
  - batch job (CL + SBMJOB or direct CALL)
  - interactive menu (`*MENU` option selection)
  - subfile dispatch (option codes 1/4/5/9/etc.)
  - F-key branch (DSPF function-key handling)
  - DB trigger (file trigger program)
  - scheduler (WRKJOBSCDE entry)
  - API / remote (remote PGM call, MQ message, HTTP, IFS drop)
- **Approved program analyses** for every program in the chain
- **Approved inventory** with `relationships` populated for the involved objects
- Optional: SME notes on trigger context, BAU rhythm, known error scenarios
- Optional: DSPF / PRTF / MENU object definitions (for UI-aware flows)

Stop and require clarification if:

- Any program in the chain lacks an approved `program-analysis-<OBJ-ID>.md`
  → route to `legacy-ibmi-program-analyzer`
- Inventory `sme_review.decision` is `blocked` or `relationships` are
  incomplete → route to `legacy-ibmi-inventory`
- Trigger model cannot be identified from the entry point → require SME
  clarification (do not guess)
- Flow appears to span multiple business modules → narrow scope; one flow
  = one business transaction

## Output Contract

Produce a single artifact:

- `flow-<FLOW-SLUG>.md`

`<FLOW-SLUG>` is uppercase, hyphen-separated, business-event named (e.g.,
`ONUS-AUTH`, `BATCH-RECON`, `CHARGEBACK-INTAKE`), and stable across the
analysis chain.

Use:

- `templates/flow.md` as the starting structure
- `references/output-contract.md` for section definitions and required fields
- `references/trigger-models.md` for trigger-specific analysis guidance
- `references/data-flow-patterns.md` for cross-program data passing
- `references/error-propagation.md` for error-chain analysis

Follow:

- `../../docs/id-conventions.md` for stable IDs (`FLOW-*`, `NODE-*`, `EDGE-*`, `DATA-*`)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence strength tagging

Examples:

- `examples/batch-job-positive/` — straightforward batch chain (`CL → RPG1 → RPG2 → SQLRPG`)
- `examples/menu-flow-positive/` — interactive flow with `*MENU` + DSPF + subfile dispatch
- `examples/incomplete-flow-negative/` — flow with a missing program-analysis (must route back)

## Workflow

1. **Identify Trigger Model & Entry Point**
   - Determine which of the seven trigger models applies (see
     `references/trigger-models.md`). If unsure, ask the SME — do not guess.
   - Document the trigger object:
     - batch job → CL program + SBMJOB statement, or scheduler entry
     - menu → `*MENU` object name + option number
     - subfile dispatch → DSPF subfile + option-code table
     - F-key → DSPF + function-key handler
     - DB trigger → file name + trigger program + event (insert/update/delete)
     - scheduler → WRKJOBSCDE entry + frequency
     - API / remote → remote-call mechanism + parameter contract
   - Assign `FLOW-<SLUG>-<NNN>` ID.
   - Capture the **business event name** the SME uses for this flow
     (e.g., "Customer authorization request", not "RPG1 call").

2. **Enumerate Nodes (Programs in the Chain)**
   - List every program the flow touches, in call order.
   - For each node:
     - assign `NODE-<SLUG>-<NN>` (sequence-numbered)
     - reference the program's `OBJ-*` (from inventory) and approved
       `program-analysis-<OBJ-ID>.md`
     - record the program's role in the flow (entry / orchestrator /
       worker / data-access / reporter / exit)
   - If a node has no approved `program-analysis`, **stop** and create
     `TBD-<SLUG>-<NNN>: pending_source` routing back to
     `legacy-ibmi-program-analyzer`.

3. **Trace Edges (Calls Between Nodes)**
   - For every call between two nodes, document an edge:
     - `EDGE-<SLUG>-<NN>: NODE-A → NODE-B`
     - Call type (CALL, CALLP, CALLPRC, EXSR-not-applicable-cross-program,
       SBMJOB, remote-call)
     - Call site (source program + line number) — from the caller's
       `program-analysis`
     - Call condition (always / conditional / loop / error path)
   - Build the **sequence diagram** (see `references/output-contract.md`
     for format).

4. **Cross-Program Data Flow**
   - For each edge, document what data passes (see
     `references/data-flow-patterns.md`):
     - parameters passed in the CALL
     - shared data area (`*DTAARA`) updates / reads
     - data queue (`*DTAQ`) messages
     - shared file writes/reads (program A writes, program B reads)
     - temporary work files / spool / IFS files
     - signal flags (return codes, indicators, error fields)
   - Assign `DATA-<SLUG>-<NN>` for each distinct data exchange.
   - Tag evidence; cross-reference to source line numbers via EV-\*.

5. **Branch Points & Decision Nodes**
   - Identify points where the flow forks (subfile option, F-key,
     conditional CALL, trigger event).
   - For each branch point:
     - the deciding artifact (which field / which key / which condition)
     - the alternatives and which target node each leads to
     - whether unhandled options/keys exist (silently dropped vs. error)

6. **UI Surfaces (interactive flows only)**
   - List every DSPF / PRTF / MENU the user sees during the flow.
   - For each:
     - object name + `OBJ-*`
     - which node displays it
     - key fields shown / entered
     - F-keys handled
     - branch destination per F-key / option
   - For non-interactive flows (batch, trigger, scheduler, API), this
     section may be `N/A — non-interactive flow`.

7. **Error Propagation**
   - For each node, summarise (from its `program-analysis` Error Handling
     section) what happens when each error condition occurs.
   - Trace propagation: does the error abort the whole flow, roll back to
     a checkpoint, log-and-continue, or branch to an error handler?
   - Identify **commit boundaries**: where does the flow consider work
     "committed" vs "rolled back"?
   - Identify **unhandled error windows**: nodes where an unhandled
     error would crash the entire flow without recovery (create TBD).
   - See `references/error-propagation.md`.

8. **Business Capability Seeds**
   - Extract `BR-*` candidates (business rule seeds) that this flow
     plausibly enforces — **without inventing rules**.
   - Each seed is a *question* for SME review (e.g., "Does the rule
     'credit limit must not be exceeded' live in this flow?"), with
     pointers to the program(s) and field(s) that suggest it.
   - The spec-writer skill will resolve seeds into approved rules; the
     flow analyzer never approves rules itself.

9. **Prepare for SME Review**
   - Consolidate all TBDs grouped by blocking status (`pending_source` /
     `pending_sme_judgment` / `non_blocking`).
   - Confirm every node's `program-analysis` is approved.
   - Generate the flow review checklist (see `templates/trigger-checklist.md`).
   - Mark flow as `draft` and route to SME.
   - **Gate:** the flow is ready for module-analyzer when:
     - all 9 sections populated
     - every node has an approved `program-analysis`
     - no blocking TBDs (or SME has explicitly waived them)
     - SME has signed off on the trigger model + business event name +
       capability seeds

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md`. Every
edge in this flow must trace to a CALL / CALLP / CALLPRC / SBMJOB / trigger
registration / MQ config statement in actual source code. Shop documentation,
prior architecture diagrams, and SME recollection are navigation aids; they
do not become evidence until tier-1 source confirmation exists. If SME claims
a flow path the code does not contain, both observations are recorded and a
TBD blocks the flow until SME reconciles them.

**Do NOT invent:**

- **Calls** not visible in any program's `program-analysis` External Calls section
- **Data flow** that requires guessing parameter semantics (use only what
  source explicitly shows or SME confirms)
- **Branch destinations** for F-keys / options not visible in DSPF
  definitions
- **Trigger conditions** for DB triggers without seeing the trigger
  configuration
- **Commit boundaries** if neither code nor SME has confirmed them
- **Business capabilities or rules** — these are seeds (questions), not
  facts; spec-writer resolves them

**Instead:**

- If a node's `program-analysis` is missing → `TBD: pending_source` →
  route to `legacy-ibmi-program-analyzer`
- If a trigger model is ambiguous → `TBD: pending_sme_judgment`
- If the SME cannot name the business event → stop and request a name
  (do not autogenerate from program names)
- If error propagation is unclear → tag `needs_sme_review`; do not assume
  commit / rollback behavior

**Evidence minimum:**

- Every edge must trace to a CALL/CALLP/CALLPRC/SBMJOB/trigger-config
  statement in some program's source.
- Every data exchange must trace to a parameter list, data area, data
  queue, or file in source.
- Every UI surface must trace to a DSPF / PRTF / MENU object that exists
  in inventory.

## SME Review Questions

The generated `flow-<FLOW-SLUG>.md` must include a review checklist
covering:

- [ ] Trigger model correctly identified (batch / menu / subfile /
      F-key / trigger / scheduler / API)
- [ ] Business event name accurately reflects what the business calls this
      transaction
- [ ] All nodes (programs) in scope are correct; no missing programs and
      no extra programs
- [ ] All edges (calls) reflect actual production behavior
- [ ] Cross-program data flow is complete (no undocumented shared files
      or data areas)
- [ ] Branch points correctly capture user-visible decision points
- [ ] UI surfaces match production screens (interactive flows only)
- [ ] Error propagation matches operational reality (what actually
      happens when this fails in prod)
- [ ] Commit boundaries are correct (one transaction vs. multiple)
- [ ] Capability seeds are reasonable questions, not invented rules

## Runtime Portability

Canonical source: `skills/legacy-ibmi-flow-analyzer/SKILL.md`

Runtime adapters are synced via `scripts/sync-skills.sh`:

- Codex: `.codex/skills/legacy-ibmi-flow-analyzer/SKILL.md`
- Claude Code: `.claude/skills/legacy-ibmi-flow-analyzer/SKILL.md`
- OpenCode: `.opencode/skills/legacy-ibmi-flow-analyzer/SKILL.md`
- Agents: `.agents/skills/legacy-ibmi-flow-analyzer/SKILL.md`

No runtime-specific assumptions are embedded in the canonical source.

## Version History

- v0.1.0 (2026-05-14): Initial release
  - 9-step workflow
  - 7 trigger-model support (batch / menu / subfile / F-key / trigger /
    scheduler / API)
  - Cross-program data flow analysis
  - Error propagation and commit boundary detection
  - UI-surface mapping for interactive flows
  - Business capability seed extraction (no rule invention)
  - Feedback loop to `legacy-ibmi-program-analyzer` and
    `legacy-ibmi-inventory`
  - Examples: batch positive, menu positive, incomplete-flow negative
