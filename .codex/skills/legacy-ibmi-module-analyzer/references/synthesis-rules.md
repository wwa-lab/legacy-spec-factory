# Synthesis Rules: Focused Module Assembly

This document defines how `legacy-ibmi-module-analyzer` aggregates approved
flows, program analyses, inventory evidence, and reviewed module-first context
into the default module package:

- `module-overview.md`
- `03-program-flow.md`
- `04-data-flow.md`
- `module-review-checklist.md`

`01-operation-flow.md` and `02-system-flow.md` are not default outputs. Do not
generate them unless the user explicitly asks and supplies strong SME,
architecture, or interface evidence. In normal runs, operation and system
context belongs in `module-overview.md` as source-backed notes, BRD crosswalk
rows, SME questions, or `TBD-*` gaps.

---

## General Synthesis Principles

1. **Inputs are authoritative.** If an approved flow says X, the module
   package must not say not-X without an explicit SME override and an `EV-*`
   link to the override.
2. **Aggregate by union, not intersection.** Every in-scope flow appears in
   Program Flow. Every durable object, critical field, carrier, and external
   output touched by an in-scope flow appears in Data Flow.
3. **Deduplicate by stable ID.** Same `OBJ-*`, `FLOW-*`, `REPLAY-*`,
   `LINEAGE-*`, `PERSIST-*`, or `EXCHAIN-*` in multiple inputs becomes one
   module row with all source references preserved.
4. **Preserve evidence chains.** Every aggregated fact must point back to the
   source flow, program, inventory item, SME note, document coordinate, or
   context-package row.
5. **TBDs propagate up.** A blocking TBD in any in-scope flow becomes a module
   TBD unless resolved during module synthesis.
6. **Replay stays visible.** Do not replace a replayable program chain with a
   generic module summary. Preserve `REPLAY-*` paths in `03-program-flow.md`
   and summarize readiness in `module-overview.md`.
7. **Persistence and fields stay specific.** Keep object names, field names,
   operations, skipped mutations, commit/rollback/retry behavior, source
   identifiers, business meanings, and `LINEAGE-*` / `PERSIST-*` evidence.
8. **Exception chains stay closed.** `EXCHAIN-*` rows remain visible until they
   map to business outcome, persistence impact, recovery owner, message
   inventory, or a named `TBD-*`.
9. **BRD eligibility is stricter than module coverage.** A row can be useful
   for review while still being ineligible for BRD conclusions. Only
   code-backed or named SME-confirmed rows can mark BRD sections as covered.
10. **Compact artifacts are the aggregation surface.** Do not concatenate full
    flow or program Markdown. Use approved `flow-*.md` rows and compact
    program sidecars first: `program-analysis-summary.yaml`,
    `source-index.yaml`, `routine-logic-details.yaml`,
    `message-inventory.yaml`, `file-io-inventory.yaml`,
    `field-mutation-matrix.yaml`, and `sql-inventory.yaml`.

---

## Program Flow Aggregation

### Inputs

- All in-scope `flow-<FLOW-SLUG>.md` files
- Each flow's Flow Replay Path
- Each flow's edge Evidence Source / Resolution rows
- Each flow's Flow Persistence Matrix and Exception Propagation Chain where
  they affect final outcomes
- Approved compact program artifacts for every referenced program:
  `program-analysis-summary.yaml`, `source-index.yaml`,
  `routine-logic-details.yaml`, `message-inventory.yaml`,
  `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
  `sql-inventory.yaml`
- Approved inventory and object map

### Required Rows

| Field | Source | Rule |
| --- | --- | --- |
| Flow Inventory | One row per approved in-scope flow | Copy flow ID, business event, trigger, entry program, status, and evidence links. |
| Replay Coverage Summary | `REPLAY-*`, final outcomes, exception branches | One row per flow. Missing trigger, branch, persistence, response, or exception disposition creates `TBD-*` unless waived. |
| Edge Resolution Summary | Flow edge evidence | Preserve static, dynamic, command, menu, scheduler, trigger, API, and manual entry resolution evidence. |
| Cross-Flow Dependencies | Shared carriers, files, queues, DTAARAs, MSGQs, spool, IFS, external handoffs | Record only dependencies evidenced by approved flow/data evidence or named SME confirmation. |
| Shared Sub-Programs | Programs appearing in two or more flows | Sort by number of containing flows and preserve `OBJ-*` IDs. |
| Exception / Recovery Summary | `EXCHAIN-*` rows affecting flow outcomes | Preserve messages, skipped writes, rollback/retry, manual recovery, downstream notification, and unresolved gaps. |
| Mermaid Flow Diagram | Flow/program topology | Show flows, shared programs, durable/external outcomes, and exception exits before evidence tables. |

### Replay Coverage Algorithm

```text
For each in-scope flow F:
    collect REPLAY-* rows
    collect final outcomes from persistence and exception-chain rows
    mark coverage complete only if F has:
        trigger / entry path
        major decision branches
        final response or batch outcome
        durable persistence or skipped persistence outcome
        exception branch disposition
    if any required piece is missing:
        create a module TBD unless a named SME waiver exists
```

### Program Flow Anti-Hallucination

- Do not infer a dependency from similar program names.
- Do not invent replay paths for older or incomplete flow artifacts.
- Do not treat a diagram edge as BRD evidence unless it is backed by approved
  flow evidence or SME confirmation.
- Do not turn cross-flow topology into business process prose without the BRD
  crosswalk proving source eligibility.

---

## Data Flow Aggregation

### Inputs

- Every flow's Cross-Program Data Flow section
- Every flow's Cross-Program Field Lineage section
- Every flow's Flow Persistence Matrix section
- Every flow's Exception Propagation Chain when exceptions affect data,
  durable outputs, rollback, retry, partial commit, or skipped writes
- Every program's Data Touch Map and Object Dependencies sections
- Program-analyzer compact sidecars: `program-analysis-summary.yaml`,
  `source-index.yaml`, `routine-logic-details.yaml`,
  `message-inventory.yaml`, `file-io-inventory.yaml`,
  `field-mutation-matrix.yaml`, and `sql-inventory.yaml`
- Approved inventory and object map

### Required Rows

| Field | Source | Rule |
| --- | --- | --- |
| Data Objects in Scope | Flow carriers plus program Data Touch Map and Object Dependencies | One row per meaningful object/carrier with `OBJ-*`, operations, source flows, and evidence. |
| Producer / Consumer Flows | Cross-Program Data Flow and persistence rows | Producer = writer/sender/creator; Consumer = reader/receiver/downstream consumer. |
| Coupling Score | Distinct flows touching the object | Preserve as count and risk indicator, not as a modernization recommendation. |
| Data Lifecycle | Flow state impact + program operations | Created, Updated, Read, Archived, Purged, Returned, Sent, Skipped, or Unknown. |
| Module Persistence Matrix | `PERSIST-*` rows | Group by object/field/output while preserving operation, commit, rollback, retry, skipped mutation, and consumer. |
| Critical Field Lineage Across Module | `LINEAGE-*` rows | Preserve source field, carriers, transforms, persisted/output locations, consumers, and business meanings. |
| Exception-Aware Data Risks | `EXCHAIN-*` rows with data impact | Map to skipped write, rollback, retry, partial commit, manual recovery, notification, or `TBD-*`. |
| Cross-Module Data Dependencies | Objects owned or consumed outside the module | Include only evidenced external ownership/consumption, or mark as `TBD-*`. |
| Mermaid Flow Diagram | Data lifecycle / carrier movement | Show data movement and durable outcomes before evidence tables. |

### Coupling Algorithm

```text
For each object O in scope:
    coupling[O] = number of distinct flows that read, write, send, receive,
                  return, persist, or skip mutation of O

Coupling thresholds:
    1     = low
    2     = moderate
    3-5   = high
    6+    = very high
```

### Persistence Algorithm

```text
For each flow F:
    For each PERSIST-* row in F:
        group by object / field / durable output
        preserve operation, commit, rollback, retry, and recovery notes
        preserve skipped mutations and exception-driven alternate outcomes
        add producer flow F and evidenced consumers
```

### Data Flow Anti-Hallucination

- Do not assume archival or purge behavior without SME confirmation or a
  visible archive/purge job.
- Do not assert DB relationships without DDS, DDL, SQL, or inventory evidence.
- Do not prescribe coupling-hotspot mitigation in module analysis.
- Do not collapse field-level behavior into file-level summaries when a field
  mutation changes validation, output, persistence, or downstream behavior.
- Do not omit exception-state data behavior.

---

## Module Overview Synthesis

`module-overview.md` is the first-read SME and BRD intake artifact. It should
make the useful module context visible without forcing weak Operation/System
views into standalone files.

### Required Overview Content

| Section | Rule |
| --- | --- |
| Module Identity | Include `MODULE-*`, business name, scope, owner, status, and evidence mode. |
| In-Scope Flows | List every in-scope `FLOW-*`, status, trigger, entry point, and evidence link. |
| Evidence View Index | List only the default Program Flow and Data Flow artifacts unless optional user-requested views exist. |
| Program-Chain Readiness | Summarize replay, edge resolution, missing dynamic calls, unresolved branches, and waivers. |
| Persistence & Critical Field Summary | Summarize objects, fields, persistence, lineage, skipped mutation, and data-risk hotspots. |
| Exception & Recovery Summary | Summarize messages, exception chains, recovery owners, rollback/retry, skipped writes, and unresolved business intent. |
| Optional Source-Backed Context Notes | Capture SME-confirmed BAU notes, source-backed interface context, or operational context that does not justify standalone 01/02 files. |
| Capability Seeds | List `CAP-*` seeds with source eligibility and review status. |
| BRD Source Eligibility Crosswalk | Classify each BRD input area as covered, partial, missing, or questions-only based on eligible evidence. |
| Module Review Checklist | Name required reviewers and approval decisions for overview, Program Flow, Data Flow, and BRD crosswalk. |

---

## BRD Source Eligibility

When writing the crosswalk, classify each row:

| Input Class | BRD Eligibility | Handling |
| --- | --- | --- |
| Approved flow/program/inventory evidence | `brd_conclusion_allowed` | May support observed behavior, process flow, dependencies, validation, data, or error handling. |
| Named SME confirmation | `brd_conclusion_allowed` | May support business context, BAU rhythm, manual process, or rule intent. |
| Source document or RAG snippet without SME/code corroboration | `needs_sme_review` | May support review prompts; do not write as final BRD prose. |
| AI-organized context, sparse context package, or generated-draft diagram | `questions_only` | Convert to `TBD-*` or SME question. |
| Missing evidence | `questions_only` | Carry a `TBD-*` with resolver. |

Coverage rules:

- `covered` requires at least one `brd_conclusion_allowed` source.
- `partial` may include eligible evidence plus review gaps.
- `missing` or `questions_only` means the BRD writer must create questions or
  TBDs instead of writing a conclusion.

### BRD Crosswalk Source Mapping

| BRD Area | Preferred Module Sources | Gap Handling |
| --- | --- | --- |
| Function Purpose | Scope statement, module owner notes, capability seeds, SME-confirmed purpose | If purpose is only a program label, create `TBD-*`. |
| Business Scenarios / Use Cases | In-scope flows, replay summaries, SME scenario notes | Missing scenario owner, replay path, or outcome becomes `TBD-*`. |
| Channels | Flow trigger context, source-backed interface notes, screen/report analyzer outputs | Do not infer channels from object names. |
| User Interface / Touchpoints | Screen/report analyzer outputs, flow UI surfaces, SME-confirmed manual touchpoints | If UI evidence is required but absent, block or carry source TBD. |
| System Interfaces | Flow external calls, durable external outputs, source-backed interface notes | Keep interface purpose business-readable; do not invent SLA/auth/security boundaries. |
| Process Flow | Flow inventory and replay coverage summary | Convert flows to business phases only where evidence supports that framing. |
| Validation Rules | Program Validation Logic, flow branch points, field lineage, exception-chain seeds, SME-confirmed rules | Seeds remain review questions until approved. |
| Error Handling | Program Exception Handling, Message Inventory, flow Exception Propagation Chain, module Exception & Recovery Summary | Unclear intent, message ownership, or recovery procedure becomes SME `TBD-*`. |
| Dependencies | Cross-flow dependencies, data dependencies, approved external handoffs | Do not prescribe mitigations; list business role and risk only. |

Optional BRD sections 10-12 must be marked `not_evidenced` unless real security,
authentication, workflow/design, or source-document mapping exists.

---

## Evidence-View Consistency Check

Run these checks before marking the module package approved:

| Check | Rule |
| --- | --- |
| Flow -> Program Flow | Every in-scope flow appears in `03-program-flow.md`. |
| Flow -> Data Flow | Every flow with durable or carrier behavior has corresponding rows in `04-data-flow.md`. |
| Replay -> Overview | Every incomplete replay path appears in Program-Chain Readiness or has a waiver. |
| Persistence -> Data Flow | Every durable `PERSIST-*` and skipped mutation appears in Data Flow. |
| Lineage -> Data Flow | Every module-critical `LINEAGE-*` row appears in Data Flow. |
| Exception -> Overview/Data | Every material `EXCHAIN-*` maps to exception summary, data-risk row, recovery owner, or `TBD-*`. |
| Capability -> Crosswalk | Every `CAP-*` seed has a source eligibility status and downstream BRD handling. |
| Optional Context -> Eligibility | SME/source notes in overview are marked eligible, needs review, or questions-only. |

Mismatches create module TBDs that must be resolved or explicitly waived before
approval.

---

## Handling BAU With No Code Trace

Some BAU procedures exist only in human practice, such as "Finance reviews the
spool every morning and emails the auth team if exceptions are found." This has
no code path.

Record this in `module-overview.md` under Optional Source-Backed Context Notes
with `evidence_strength: confirmed_by_sme` and a named SME note. Do not force it
into Program Flow or Data Flow. If it affects BRD or future spec behavior, add a
crosswalk row and a BRD/source eligibility status so reviewers decide whether it
is legacy context, a candidate rule, or a target-system requirement.
