# Synthesis Rules: How to Aggregate Across Flows and Programs

This document defines the aggregation rules for each of the four views.
The module-analyzer does not re-analyze code or flows; it composes
existing analyses. These rules tell it how.

---

## General Synthesis Principles

1. **Inputs are authoritative.** If a flow analysis says X, the module
   analysis must not say not-X without explicit SME override (and an
   `EV-` link to the override).
2. **Aggregation is union, not intersection.** Every object touched by any
   flow appears in View 4. Every actor referenced in any flow appears
   in View 1. Coverage is broader at the module level.
3. **Deduplicate by stable ID.** Same OBJ-* in two flows → one row in
   View 4 with both flows listed.
4. **Preserve evidence chains.** Every aggregated fact must retain
   pointers to the source flow / program / SME note.
5. **TBDs propagate up.** A blocking TBD in any flow becomes a blocking
   TBD at the module level (unless resolved during module synthesis).
6. **Replay stays visible.** Do not replace a replayable program chain with a
   generic module summary. Preserve `REPLAY-*` paths through View 3 and the
   overview readiness table.
7. **Persistence and fields stay specific.** Module aggregation may group
   related rows, but it must preserve critical field names, file/object names,
   operations, skipped mutations, and `LINEAGE-*` / `PERSIST-*` evidence.
8. **Exception chains stay closed.** `EXCHAIN-*` rows remain visible until they
   map to business outcome, persistence impact, recovery owner, or named TBD.
9. **BRD eligibility is stricter than view coverage.** A four-view row may be
   useful for review while still being ineligible for BRD conclusions. Only
   code-backed or named SME-confirmed rows can mark BRD sections as covered.
   Candidate-only, generated-draft, missing, or unreviewed source-documented
   rows become questions/TBDs.

---

## View 1 — Operation Flow / Business Background

### Inputs
- All in-scope `flow-<FLOW-SLUG>.md` (specifically their Trigger Context,
  Flow Replay Path, Business Capability Seeds, and Exception Propagation Chain
  operational notes)
- SME-provided BAU notes
- SME interview transcripts (if available)
- Business documentation, ops manuals

### Aggregation Rules

| Field | Source | Rule |
| --- | --- | --- |
| Business Actors | SME notes; not from code | Union; deduplicate by role |
| Business Events | Each in-scope flow contributes one event (its business event name) plus replay path | One row per flow; cite `REPLAY-*` where available |
| BAU Rhythm | SME notes; cross-checked against scheduler entries in flows | Cadence comes from SME; scheduler entries confirm |
| Manual Intervention Points | SME notes; cross-checked against operational outcomes in each flow's Exception Propagation Chain | Union; preserve `EXCHAIN-*` where it explains recovery |
| Exception Lifecycle | SME description; cross-checked against `EXCHAIN-*` rows in flows | SME-led, but every material code-observed exception outcome must be mapped or carried as TBD |
| Business Rule Seeds | Union of all flows' SEED-* | Deduplicate by candidate-rule wording; combine references |

### Anti-Hallucination

- **No actor inferred from code.** A program named "MGRAPPRV" does not
  imply a "manager" actor unless SME confirms.
- **No BAU rhythm from log file inspection.** Cut-off times must come
  from SME or scheduler entry, not from observed timestamps.
- **No exception procedure from comments in code.** Comments rot; SME
  is authoritative.
- **No generic exception closure.** Message IDs, return codes, skipped writes,
  and retry/rollback behavior from `EXCHAIN-*` cannot be replaced by "error
  handled" unless the details are immaterial and SME waives them.

---

## View 2 — System Flow

### Inputs
- Each flow's Trigger Context (for inbound systems) and External Calls
  (for outbound systems / interfaces)
- Each flow's Flow Persistence Matrix for durable files, queues, spool, IFS,
  response payloads, and external handoffs
- Each flow's Exception Propagation Chain when exceptions notify external
  systems or produce manual/operational outputs
- Architecture diagrams, integration specifications, SME

### Aggregation Rules

| Field | Source | Rule |
| --- | --- | --- |
| Upstream Systems | Trigger Context of API/Remote and Menu flows | One per distinct source system |
| Downstream Systems | Flow nodes that write external interface files / send remote calls, plus durable outputs from `PERSIST-*` rows | One per distinct target system or manual consumer |
| Integration Patterns | Each upstream/downstream relationship has one pattern | Capture per relationship |
| SLA | SME / integration spec | Per interface |
| Auth | SME / integration spec | Per interface |
| Security Boundaries | Architecture diagram + SME | Document at module level |

### Anti-Hallucination

- **No "system" inferred from a CALL** unless the called program is
  outside this module and at the boundary (e.g., a CALL to GLINTERFACE
  is a system call; a CALL to ORDVAL inside the same module is not).
- **No SLA assumed from "the program runs fast"** — must come from a
  documented contract or SME assertion.

---

## View 3 — Program Flow

### Inputs
- All in-scope flow analyses
- Each flow's Flow Replay Path
- Each flow's Flow Persistence Matrix and Exception Propagation Chain where
  they affect final outcomes
- Programs are referenced by ID; not re-analyzed

### Aggregation Rules

| Field | Source | Rule |
| --- | --- | --- |
| Flow Inventory | One row per `flow-<FLOW-SLUG>.md` | direct copy of metadata |
| Replay Coverage Summary | Each flow's `REPLAY-*`, key decision paths, exception branches, persisted outcomes | One row per flow; missing replay / lineage / persistence coverage creates `TBD-*` unless waived |
| Cross-Flow Dependencies | Computed by scanning each flow's Cross-Program Data Flow section for shared carriers (files / DTAARAs / DTAQs / MSGQs / spool / IFS / external handoffs) | Where producer flow ≠ consumer flow, that's a cross-flow dependency |
| Shared Sub-Programs | Computed by scanning each flow's Nodes; any program appearing in ≥2 flows is shared | Sort by number of containing flows |
| Overall Call Topology | Top-level Mermaid synthesis showing flows side-by-side, shared programs, final outcomes, and exception exits | Manual / SME-reviewed; do not use ASCII tree as primary topology |

### Computing Replay Coverage (Algorithm)

```
For each in-scope flow F:
    Collect all REPLAY-* rows from F.
    Collect final outcomes from Flow Persistence Matrix and Exception
    Propagation Chain.
    Mark coverage complete only if F has:
        trigger / entry path,
        major decision branches,
        final response or batch outcome,
        durable persistence / skipped persistence outcome,
        exception branch disposition.
    If any piece is missing:
        record the missing surface in Replay Coverage Summary and create
        TBD-* unless a named SME waiver exists.
```

### Computing Cross-Flow Dependencies (Algorithm)

```
For each pair of flows (A, B):
    For each data exchange in A's Cross-Program Data Flow section:
        If exchange mechanism is "Shared file" / "Shared DTAARA" /
           "Shared DTAQ" / "Shared work file":
            Look for matching object in B's Cross-Program Data Flow.
            If found and roles complement (A produces, B consumes):
                Record cross-flow dependency A→B via that object.
```

### Anti-Hallucination

- **No dependency inferred** beyond what data-flow sections explicitly
  show. If A writes X and B reads X but the flows don't note it, do not
  invent the dependency — confirm with SME or treat as TBD.
- **No "shared utility"** inferred just because two programs have similar
  names. Must appear as a node in both flows.
- **No replay path invented** for older flow artifacts. Refresh the flow
  analysis or carry a source TBD / waiver.
- **No BRD coverage from generated topology.** A diagram edge drawn only to make
  the topology easier to discuss is `questions_only` until backed by flow
  analysis or SME confirmation.

---

## View 4 — Data Flow

### Inputs
- Every flow's Cross-Program Data Flow section
- Every flow's Cross-Program Field Lineage section
- Every flow's Flow Persistence Matrix section
- Every flow's Exception Propagation Chain when exceptions affect data,
  durable outputs, rollback, retry, or skipped writes
- Every program's Data Touch Map and Object Dependencies sections (from
  each `program-analysis-<OBJ-ID>.md`)
- Every program's Key File & Field Logic, File I/O Purpose, Field Mutation
  Matrix, Validation Logic, and Routine Logic Details routine-local
  conditioned calculation blocks, carrier/lineage, and exception closure rows
  where supplied by program-analyzer v0.2.5; preserve source identifiers plus
  business meanings for critical fields
- inventory.yaml (for cross-reference)

### Aggregation Rules

| Field | Source | Rule |
| --- | --- | --- |
| Data Objects in Scope | Union of every flow `DATA-*` carrier plus every program Data Touch Map / Object Dependencies entry | One row per meaningful data object / carrier |
| Producer Flows / Consumer Flows | Determined by each flow's Cross-Program Data Flow section | Producer = flow with writer/sender/creator node; Consumer = flow with reader/receiver node |
| Coupling Score | Number of flows touching the object | Integer |
| Data Lifecycle | Union of all flow `State Impact` values and program Data Touch operations | Created (first write) / Updated (subsequent writes) / Read / Archived / Purged |
| Module Persistence Matrix | Union of all flow `PERSIST-*` outcomes, grouped by object / field / output | Preserve operation, field, commit/rollback/retry, skipped mutation, and consumer |
| Critical Field Lineage Across Module | Union of module-critical `LINEAGE-*` rows | Preserve source field, carriers, transforms, persisted locations, output locations, and consumers |
| Exception-Aware Data Risks | `EXCHAIN-*` rows with data or persistence impact | Map to skipped write, rollback, retry, partial commit, manual recovery, or TBD |
| Critical Data Trails | Flow critical trails plus SME review; trace key business records end-to-end | Evidence-backed, SME-confirmed for business meaning |
| DB Table Relationships | From DDS / SQL definitions in inventory | Direct mapping |
| Cross-Module Data Dependencies | Objects in this view owned by another module OR consumed by another module | Boundary detection |

### Computing Coupling Score

```
For each object O in scope:
    coupling[O] = number of distinct flows that touch O (read or write)

Coupling thresholds:
    1     - low (single-flow private object)
    2     - moderate (shared between 2 flows)
    3-5   - high (module-level shared)
    6+    - very high (hot path; modernization risk)
```

### Computing Data Lifecycle Stages

```
For each object O:
    Created: earliest-running flow that has a WRITE/INSERT to O without
             a prior CHAIN/SELECT (creation, not update)
    Updated: any flow with UPDATE on O
    Read:    any flow with CHAIN/READE/SELECT on O
    Archived: typically a separate archival job/flow (often out of module)
    Purged:  typically a separate purge job (often out of module)
```

Archived and Purged are often "out of module" → mark as `external` and
create a non-blocking TBD if not in scope of this module.

### Computing Module Persistence Matrix

```
For each flow F:
    For each PERSIST-* row in F:
        Group by object / field / durable output.
        Preserve the operation (write/update/delete/queue/spool/response/etc.).
        Preserve commit, rollback, retry, and recovery notes.
        Preserve skipped mutations and exception-driven alternate outcomes.
        Add producer flow F and all consumers named by F or View 2.
```

### Computing Critical Field Lineage

```
For each LINEAGE-* row in each flow:
    If the field is business-critical, persisted, returned to an external
    party, used in a decision, or consumed by another module:
        Add or merge it into Critical Field Lineage Across Module.
        Preserve source field, intermediate carriers, transformations,
        persistence/output locations, consumers, and evidence IDs.
    If a program boundary or transform is missing:
        record TBD-*; do not infer the missing mapping.
```

### Anti-Hallucination

- **No archival/purge** assumed without SME confirmation or a visible
  archive job in inventory.
- **No DB relationship** asserted without DDS / SQL evidence.
- **No coupling-hotspot mitigation** prescribed without SME consultation.
- **No file-level shortcut** when a field-level update changes downstream
  behavior. Preserve the field and operation from `LINEAGE-*` / `PERSIST-*`.
- **No exception-state omission.** If an exception path skips, rolls back,
  retries, or partially commits data, it belongs in View 4.

---

## BRD Source Eligibility

When writing `module-overview.md`, classify each BRD crosswalk row:

| Input Class | BRD Eligibility | Handling |
| --- | --- | --- |
| Approved flow/program/inventory evidence | `brd_conclusion_allowed` | May support observed behavior, process flow, dependencies, validation, or error handling |
| Named SME confirmation | `brd_conclusion_allowed` | May support business context, BAU rhythm, manual process, or rule intent |
| Source document or RAG snippet without SME/code corroboration | `needs_sme_review` | May support source mapping or review prompts; do not write as final BRD prose |
| AI-organized context, sparse normalizer output, or generated-draft diagram | `questions_only` | Convert to `TBD-*` or SME question |
| Missing evidence | `questions_only` | Carry a `TBD-*` with resolver |

Coverage rules:

- `covered` requires at least one `brd_conclusion_allowed` source.
- `partial` may include a mix of eligible evidence and `needs_sme_review` /
  `questions_only` gaps.
- `missing` or `questions_only` means the BRD writer must create questions or
  TBDs instead of writing a conclusion.

---

## Cross-View Consistency Check

After all four views are built, run these checks:

| Check | Rule |
| --- | --- |
| Actor → Code Path | Every ACTOR-* in View 1 must map to at least one entry node in View 3 OR be tagged `manual_actor: yes`. |
| System → Flow | Every SYS-* in View 2 must appear in View 3 as the source/target of at least one flow. |
| Rule Seed → Evidence | Every BR-* in View 1 must reference evidence from View 3, View 4, or SME notes; do not frame the rule around program/file names unless the technical object is itself the business term. |
| Replay → Business Event | Every `REPLAY-*` in View 3 maps to a View 1 business event, exception outcome, or named `TBD-*`. |
| Persistence → System / Data | Every external or durable `PERSIST-*` output maps to View 2 system/manual consumers or View 4 objects / outputs. |
| Exception Chain → Operation / BRD | Every material `EXCHAIN-*` maps to View 1 exception lifecycle and BRD Error Handling crosswalk coverage, or carries a named `TBD-*`. |
| Lineage / Persistence → Data View | Every module-critical `LINEAGE-*` and durable `PERSIST-*` claim appears in View 4. |
| Data Object → Flow | Every object row in View 4 must reference at least one flow in View 3. |
| Flow → Data | Every flow in View 3 should touch at least one object in View 4 (otherwise the flow is pure compute — possible but unusual). |

Mismatches create cross-view TBDs that must be resolved (or explicitly
waived by SME) before the module is approved.

## BRD Functional Analysis Crosswalk

After the four views pass cross-view consistency, populate
`module-overview.md` with a BRD Functional Analysis Input Crosswalk. The goal
is to make `legacy-brd-writer` deterministic: it should copy and synthesize
from named view rows and evidence links, not infer missing BRD sections from
program names.

| BRD Area | Module Sources | Gap Handling |
| --- | --- | --- |
| Function Purpose | Scope Statement + View 1 Business Scope | If business purpose is only a program label, create `TBD-*`. |
| Business Scenarios / Use Cases | View 1 Business Events, BAU Rhythm, Manual Intervention Points, Flow Replay Path | Missing scenario owner, replay path, or outcome becomes `TBD-*`. |
| Channels | Flow Trigger Context + View 2 Upstream Systems + View 1 Actors | Do not infer channels from object names; mark missing as `TBD-*`. |
| User Interface / Touchpoints | View 1 manual points + screen/report analyzer outputs + flow UI surfaces | If triggered screen/report analysis is required but absent, block or carry a source TBD per trigger rules. |
| System Interfaces | View 2 systems, interfaces, integration patterns | Keep interface purpose business-readable; leave protocol details as evidence. |
| Process Flow | View 1 events + View 3 flow inventory + Replay Coverage Summary | Convert flows to business phases; do not copy call topology as BRD process. |
| Validation Rules | View 1 BR seeds + flow branch points + field lineage + exception-chain seeds | Seeds remain review questions; BRD does not promote them to approved rules. |
| Error Handling | View 1 Exception Lifecycle + flow Exception Propagation Chain | Unclear business intent, message ownership, or recovery procedure becomes SME `TBD-*`. |
| Dependencies | View 2 integrations + View 3 cross-flow dependencies + View 4 data / persistence dependencies | Do not prescribe mitigations; list business role and risk only. |

Optional BRD sections 10-12 must be marked `not_evidenced` unless real security
/ authentication evidence, workflow or design notes, or source document mapping
exists in the input package. Optional coverage is allowed to be absent; do not
pad it with plausible text.

---

## How to Handle BAU That Has No Code Trace

Some BAU procedures exist only in human practice — e.g., "Finance reviews
the spool every morning before 09:00 and emails the auth team if exceptions
are found." This has no code path.

**Rule:** Document it in View 1 (manual intervention point) with
`evidence_strength: confirmed_by_sme` and link to a named SME note.
Do not try to map it to View 3 (no code). Tag the associated business
rule seed as "BAU-driven, not enforced by code" — this is critical
information for `legacy-brd-writer` to capture the business choice first, and
for later spec-writing to decide whether the target system should encode this
rule programmatically or preserve the manual process.
