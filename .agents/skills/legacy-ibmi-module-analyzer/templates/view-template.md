# View [N]: [View Name] — [Module Name]

## Status: draft | needs_sme_review | approved | approved_with_non_blocking_tbd | blocked_pending_source | blocked_pending_sme | rejected

## Mermaid Flow Diagram

```mermaid
flowchart TD
  VIEW_<SLUG>_001["<View-specific flow node or TBD placeholder>"]
```

Diagram rules:
- Use `flowchart TD` unless the reviewed source flow is explicitly
  left-to-right.
- Place this section before evidence, inventory, or traceability tables.
- Treat the diagram as a sourced coverage/review surface, not independent
  evidence.
- Rendered Mermaid preview is optional. Do not block completion on IDE or
  browser preview when this fenced Mermaid source is present and structurally
  reviewed.
- Program Flow should show flow entry points, replay paths, entry programs, shared
  programs, exit programs, persisted outcomes, exception branches, and
  external response or batch outcomes.
- Data Flow should show data movement, critical field lineage, persistence
  effects, and exception-state impacts across flows and objects, with edge
  labels such as `creates`, `updates`, `reads`, `hands off`, `skips write`,
  `rolls back`, `archives`, or `purges`.
- Use stable node IDs that mirror `ACTOR-*`, `EVENT-*`, `SYS-*`, `IF-*`,
  `FLOW-*`, `PGM-*`, `DATA-*`, `OBJ-*`, `BR-*`, or `TBD-*`, replacing hyphens
  with underscores.
- Do not add diagram nodes or edges unless they are backed by the evidence /
  traceability sections below or by a named `TBD-*`. Candidate-only or
  generated-draft context must be labeled as review material and cannot make a
  BRD section covered.

## [View-specific sections, per `references/output-contract.md`]

For Program Flow: Flow Inventory / Replay Coverage Summary /
Cross-Flow Dependencies / Shared Sub-Programs / Overall Call Topology

For Data Flow: Data Objects / Lifecycle / Module Persistence Matrix /
Critical Field Lineage Across Module / Exception-Aware Data Risks / Coupling
Hotspots / Critical Data Trails / DB Relationships / Cross-Module Dependencies

## TBDs

### Pending Source
- TBD-[SLUG]-[NNN]: ...

### Pending SME Judgment
- TBD-[SLUG]-[NNN]: ...

### Non-Blocking
- TBD-[SLUG]-[NNN]: ...

## Review Checklist

Before sign-off, the reviewer must verify all items in the per-view checklist for
this view in `references/output-contract.md`:

- For **Program Flow:** All flows in scope, replay coverage, persisted outcomes, exception branches, cross-flow dependencies, shared sub-programs, call topology, and evidence linking
- For **Data Flow:** Data lifecycle, critical field lineage, module persistence matrix, exception-aware data risks, coupling hotspots, cross-module dependencies, DB relationships, and evidence linking

## SME Sign-Off
- **Reviewer:** ____
- **Review Date:** ____
- **Decision:** ____
- **Notes:** ____
