# Output Contract: Program Analysis

This document defines the precise shape and required fields for each
`program-analysis-<OBJ-ID>.md` or standalone exploratory `program-analysis.md`
artifact produced by the analyzer.

## File Structure

Each program analysis follows this markdown structure:

```markdown
# Program Analysis: [Program Name] (OBJ-* or unlinked)

## Calculation Logic
## Validation Logic
## Exception Handling
## Message Inventory
## Metadata
## Analysis Coverage & Scope
## Program Call Map
## Routine Cards
## Routine Logic Details
## Deep Read Windows
## Entry Points & Parameters
## Object Dependencies
## Logic Decomposition Ledger
## Data Touch Map
## Key File & Field Logic
## Control Flow
## File I/O
## External Calls
## Error Handling
## Redundancy Candidate Notes
## TBDs & Blocking Status
## Review Checklist
```

---

## Calculation Logic Section

This section must appear immediately after the title, before Metadata. It is
the IT SME first-read view of the program's material calculation and assignment
logic. It is not a replacement for Routine Logic Details or the Logic
Decomposition Ledger; every row must point to deeper evidence.

```markdown
## Calculation Logic

| Calculation / Assignment | Target Field / Variable | Source Operands / Carriers | Guard / Branch | Output / Business Effect | Supporting Detail Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Approved amount derivation | `ApprovedAmount` (approved credit amount) | `RequestAmount`, `CreditLimit`, `CREDFILE` lookup | credit limit branch | returned amount and approval decision | Routine Logic Details -> CreditChk conditioned block | EV-CREDIT-CHECK-002 |
```

**Requirements:**
- Include arithmetic, derived amounts, quantity calculations,
  status/result assignments, key construction, message/status carriers,
  outbound payload fields, and persisted field updates that materially affect
  program outcome.
- Preserve source identifiers with business meanings.
- Link every row to Routine Logic Details, conditioned calculation blocks,
  Logic Decomposition Ledger rows, Key File & Field Logic, File I/O mutation
  rows, or source-backed TBDs.
- Add `Calculation logic unresolved:` when operands, precision/conversion,
  branch priority, source carriers, or output carriers are unclear.

---

## Validation Logic Section

This section must appear immediately after Calculation Logic, before Exception
Handling.
It is the IT SME first-read view of validation, status, return-code, message,
indicator-driven, and generic-handler outcomes.

```markdown
## Validation Logic

| Message / Status Code | Message Description | Validation / Error Type | Set By / Source Lines | Trigger Condition | Reverse Trigger Chain / Routine Logic Link | Output Carrier | Downstream Effect | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D | denial return literal | response_status | `DecisionCode`, lines 42-45 | request exceeds credit limit | Routine Logic Details -> CreditChk outcome reverse trace | return value | caller receives denial | confirmed |
```

**Requirements:**
- Create one row per explicit message ID, status code, return code, response
  value, SQLSTATE, CPF/MCH/RNX/CPD message, user-defined code,
  indicator-driven outcome, or generic catch-all token.
- Do not group multiple message IDs into one row.
- Include message descriptions from the best available source, or mark
  unresolved and create an Open Item.
- Link every material row back to Routine Logic Details, a conditioned
  calculation block, an outcome reverse trace, exception closure, or a
  source-backed TBD.

---

## Exception Handling Section

This section must appear immediately after Validation Logic, before Message
Inventory. It is the IT SME first-read view of how the program closes
business, parameter, I/O, external-call, system, and generic exceptions.

```markdown
## Exception Handling

| Exception / Error Path | Trigger | Detection Mechanism | Fields / Messages Set | Handling Action | Downstream Effect | Supporting Detail Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Credit file not found | `%FOUND(CREDFILE)` false | IF branch after CHAIN | return literal `D`, `ApprovedAmount=0` | RETURN | caller receives denial; no file mutation | Routine exception closure -> CreditChk; Validation Logic `D` | EV-CREDIT-CHECK-003 |
```

**Requirements:**
- Include every observed business, parameter, file I/O, SQL, external-call,
  system, and generic-handler exception path.
- State the detection mechanism, handling action, and downstream effect for
  each path.
- Do not infer specific message IDs from generic handlers.
- Link each row to Routine Logic Details, routine-local exception closure, the
  Error Handling section, the Exception Closure Ledger, Validation Logic, or a
  source-backed TBD.

---

## Message Inventory Section

This section must appear immediately after Exception Handling, before Metadata.
It is the IT SME first-read summary of observed message/code/literal meanings.
For message-dense programs, it must stay compact and link to the detailed
message sidecars rather than expanding every occurrence in the main analysis.

```markdown
## Message Inventory

| Message / Code / Literal | Short Description | Type | Occurrences | Primary Routine(s) | First Seen / Set By | Trigger / Handler Summary | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D | denial decision | response_status | 3 | CreditChk | lines 42-45 | not found or amount exceeds limit | MSG-CREDIT-001 |
```

**Requirements:**
- Create one summary row per explicit message ID, status value, return code, response
  literal, SQLSTATE, CPF/MCH/RNX/CPD message, operator message, or shop-local
  message token in the main summary. If the same token appears multiple times,
  summarize it once with occurrence count and link to details.
- Preserve exact source codes/literals and do not group message families.
- Include the best available short description. If unavailable, write
  `unresolved - message description not available` and create an Open Item.
- Approved reference packs may supply the description source. Cite them as
  `reference pack: <pack_id>/<file>#<row-or-anchor>`. Do not invent message
  rows from the catalog; the message/code/literal must first be observed in
  source, runtime evidence, or SME notes.
- Cross-reference the related Validation Logic and Exception Handling rows.
- When there are more than 10 message/code/literal rows, or when the program is
  `segmented` / `large_program`, keep this section as a summary and place full
  details in `message-inventory.md` plus machine-readable
  `message-inventory.yaml`.
- Detail IDs use `MSG-<PROGRAM>-NNN` and point to sidecar rows that include
  description source, all occurrences, routines, source lines, carrier /
  destination, trigger / handler, related Validation / Exception rows, and
  evidence status.

---

## Metadata Section

```markdown
## Metadata

- **Program ID:** OBJ-CREDIT-CHECK-003 | unlinked - inventory not provided
- **Program Name:** CREDITCHK
- **Program Type:** RPGLE | CLLE | COBOL
- **Library:** CREDITLIB or not recorded in inventory
- **Build Target:** &TGTLIB/CREDITCHK or not recorded
- **Build / Library Evidence:**
  - EV-CREDIT-CHECK-000: build member creates &TGTLIB/CREDITCHK
- **Reference Packs Used:**
  - REF-CREDIT-CHECK-001: message_catalog/control_file/field_dictionary,
    source formats xlsx/docx/pdf, normalized outputs under
    00_reference_packs/CREDIT-CHECK-CONTROL-FILES/normalized/, version
    2026-06-04, authorization approved_for_analysis
- **Document Intake Manifests:**
  - 00_context_packages/CREDIT-CHECK/document-intake/CONTROL-FILES/intake.manifest.yaml
- **Reference Lookup Coverage:**
  - Messages: 3 matched / 1 unresolved
  - Fields: 8 matched / 2 unresolved
  - Control values: 4 matched / 0 unresolved
- **Analysis Intent:** standalone_exploratory | chain_ready
- **Inventory Linkage:** linked | missing | blocked | not_applicable
- **Downstream Readiness:** ready_for_flow_after_approval | not_chain_ready | blocked_pending_source
- **Source Location:** [file path or collection ID]
- **Collection Date:** YYYY-MM-DD
- **Entry Points:** MAIN, VALIDATECREDIT
- **Files Accessed:**
  - `CREDFILE` (PF)
  - `CUSTFILE` (LF)
- **Static Calls:**
  - `GETRATE`
  - `CHECKEXPOSE`
- **Dynamic Calls:**
  - `TARGET_PGM` -> dynamic_unresolved
- **Evidence IDs:**
  - EV-CREDIT-CHECK-001 or source-range/local-reference for standalone exploratory analysis
  - EV-CREDIT-CHECK-002 or source-range/local-reference for standalone exploratory analysis
- **Status:** draft_exploratory | draft | needs_sme_review | blocked_pending_source | approved | approved_with_non_blocking_tbd | rejected
```

**Source reference portability requirements:**

- Do not emit source evidence links with `file://`, `vscode://`, `command:`,
  `javascript:`, or `vscode-resource.vscode-cdn.net` hrefs. These are
  runtime-specific and can open incorrectly from VSCode Markdown preview or
  exported HTML.
- Use repo-relative Markdown links only when the source file is packaged beside
  the artifact, for example `[CU101A.RPGLE](source/CU101A.RPGLE)`, and include
  explicit line ranges separately.
- When source is outside the artifact package, use plain source references
  such as `CU101A.RPGLE lines 120-148`, `source-index.yaml#routine-SR100`, or
  `EV-*` IDs instead of local filesystem URLs.

**Required fields:**
- Program ID:
  - `chain_ready` — `OBJ-*` must exist in approved inventory.
  - `standalone_exploratory` — may be `unlinked - inventory not provided`;
    do not fabricate `OBJ-*`.
- Program Name and Type
- Library, Build Target, and Build / Library Evidence when known. If the
  current source mixes these concepts, split them rather than storing a
  long combined value.
- Reference Packs Used, Document Intake Manifests, and Reference Lookup
  Coverage when message catalogs, control files, code tables, or data
  dictionaries are supplied. For Excel/Word/PDF/image sources, cite the
  normalized Markdown/CSV/text output and original source format.
- Analysis Intent, Inventory Linkage, and Downstream Readiness.
- At least one entry point
- Static Calls and Dynamic Calls as separate multi-line lists. Do not put
  long call lists in one bullet.
- Evidence IDs as a multi-line list or compact table. `chain_ready` uses
  resolved `EV-*`; `standalone_exploratory` may use source ranges or local
  references, but must mark the artifact `not_chain_ready`.
- Status (`draft_exploratory` for standalone exploratory analysis; `draft` for
  chain-ready analysis before SME review)

---

## Analysis Coverage & Scope Section

This section is mandatory for every program. It records analysis mode,
coverage limits, and known gaps so partial analysis cannot masquerade as
complete understanding. Align terminology with
`references/large-program-analysis.md`.

```markdown
## Analysis Coverage & Scope

### Source Size & Strategy

- **Source Lines:** 12,840
- **Routine Count:** 42
- **External Call Count:** 27
- **Object Dependency Count:** 31
- **Analysis Mode:** standard | segmented | large_program
- **Strategy:** structure index first, then routine cards, call/data maps, deep-read windows, and synthesis

### Coverage Ledger

| Metric | Count / Percent | Notes |
| --- | --- | --- |
| Source Lines | 12,840 | full source indexed |
| Routines Found | 42 | mainline + subroutines/procedures |
| Routines Deep-Read | 18 / 43% | hot paths, state changers, external boundaries |
| Routines Indexed Only | 21 / 50% | technical utilities with no observed state impact |
| External Edges Resolved | 25 / 27 | 2 parameter contracts pending |
| Data Touches Resolved | 36 / 40 | 4 payload structures pending DDS/copybook |
| Blocking Gaps | 1 | missing called program source |
| Non-Blocking Gaps | 5 | SME review questions only |

### Routine Coverage Summary

| Routine | Coverage | Reason | Evidence / Review |
| --- | --- | --- | --- |
| MAIN | deep_read | entry path | EV-AUTH-001 |
| SR100 | deep_read | hot path and data state change | EV-AUTH-002 |
| SR900 | indexed_only | utility routine, no business state impact observed | EV-AUTH-003 |
| SR999 | blocked | referenced but source range incomplete | TBD-AUTH-004 |
```

**Requirements:**
- Count source lines, routine definitions, external calls, and object
  dependencies before synthesis.
- When a local source file is available, prefer the deterministic pre-analysis
  helper. Use the platform's existing Python launcher only:
  - Windows: try `py -3 scripts\index-rpg-source.py <source-file> --program <PROGRAM> --out-dir <analysis-dir>`, fall back to `python` if `py -3` is unavailable
  - macOS/Linux: `python3 scripts/index-rpg-source.py <source-file> --program <PROGRAM> --out-dir <analysis-dir>`
  If all launchers fail, stop and report: **"Python runtime unavailable"**.
  Do not configure PATH, install Python, or create a virtual environment.
  Apply the same launcher order to all temporary consistency checks, YAML
  readability checks, Markdown sanity checks, and one-off helper scripts in
  this skill.
  Use its `source-index.yaml`, `program-analysis-summary.yaml`,
  `routine-index.md`, `all-routine-coverage-ledger.md`,
  `deep-read-plan.md`, `routine-logic-details.md`,
  `routine-logic-details.yaml`, `message-inventory.md`, and
  `message-inventory.yaml` as seeds for this section, Routine Cards,
  Deep Read Windows, routine detail review, message review, and downstream
  flow/module aggregation.
- Select one mode: `standard`, `segmented`, or `large_program`.
- Use `segmented` or `large_program` when the source cannot safely fit
  with evidence windows, or when call/data density requires
  structure-first analysis.
- Keep the coverage ledger current as routine cards, Program Call Map,
  Data Touch Map, and deep-read windows are produced.
- Do not claim complete understanding until coverage supports it.
- Routine coverage values are only `indexed_only`, `deep_read`, and
  `blocked`. SME confirmation belongs in evidence or review fields, not
  in the coverage field.

---

## Entry Points & Parameters Section

```markdown
## Entry Points & Parameters

| Entry Point | Type | Parameters | Return | Evidence Strength |
| --- | --- | --- | --- | --- |
| MAIN | Main Program | (CustID: numeric, CreditAmt: decimal) | Result Code (0/1/-1) | confirmed_from_code |
| VALIDATECREDIT | Subroutine | (Amount: decimal, Limit: decimal) | Pass/Fail (1/0) | confirmed_from_code |

**Evidence links:**
- [EV-CREDIT-CHECK-001: Source header documentation]
- [EV-CREDIT-CHECK-002: RPGLE procedure specifications]

**Unresolved:**
- TBD-CREDIT-CHECK-001: Confirm MAIN parameter order matches call sites
```

**Requirements:**
- One table row per entry point (main program + callables)
- Columns: Entry Point name, Type (Main Program / Subroutine / Callable Procedure), Parameters (with types), Return value/status code, evidence strength
- Every parameter must be documented with direction (input/output/both) if visible in source
- Evidence links must reference EV-* IDs from inventory
- TBDs for undocumented or unclear contracts

**Evidence strength values:**
- `confirmed_from_code` — source header or procedure specification documents this
- `medium_confidence` — inferred from usage but not explicitly declared
- `needs_sme_review` — behavior visible but interpretation unclear

---

## Program Call Map Section

This section captures the RDi-style structural skeleton of the program:
which mainline, subroutine, procedure, external program, API, queue, and
service nodes call which. It is a call map, not a business-process
diagram and not a statement-level control-flow chart.

**Four required views:**

### View 1: Visual Overview

````markdown
### Visual Overview

Evidence basis: source-level flow header + derived call analysis

```text
CU101A mainline
|-- SR990 first-time initialization / parameter lists / runtime configuration
|   |-- define data areas and control values
|   |-- read package-level control
|-- SR100 preliminary validation
|   |-- SR110 amount conversion
|   |-- CHECKEXPOSE external program
|-- SR980 return / termination path
```
````

**Rules:**
- The primary `Visual Overview` must be a fenced `text` ASCII hierarchy,
  starting with `<PROGRAM> mainline` and using `|--` branch connectors.
  It should read like an RDi / source-reader call hierarchy, not a Mermaid
  graph.
- Prefer a compact hierarchy over a complete visual tangle. The full edge
  evidence table remains the source of truth.
- Include internal nodes (`EXSR`, procedure calls) and external boundary
  nodes (`CALL`, `CALLP`, API, data queue, message queue, service
  program) when they help a reader understand the program quickly.
- Mark common or hub nodes in the label when useful, but do not invent
  roles from names alone.
- If a source flow header is useful, normalize it into the same `|--`
  hierarchy and cite it through `Evidence basis`, `Evidence Source`, and
  drift TBDs. Source header entries that conflict with code-derived calls
  must not be presented as confirmed edges.

### View 2: Node Inventory

```markdown
### Node Inventory

| Node | Node Type | Defined At | Role / Notes | Evidence |
| --- | --- | --- | --- | --- |
| CU101A | Mainline | lines 100-220 | entry orchestration | EV-AUTH-ONUS-001 |
| SR100 | Subroutine | line 300 | hot path; preliminary validation | EV-AUTH-ONUS-002 |
| SR110 | Subroutine | line 410 | amount conversion | EV-AUTH-ONUS-003 |
| CHECKEXPOSE | External Program | call site line 520 | parameter contract pending SME | EV-AUTH-ONUS-004 |
```

**Node types:** `Mainline`, `Subroutine`, `Procedure`, `External
Program`, `Service Program`, `API`, `DTAQ`, `MSGQ`, `File`, `Copybook`.

**Requirements:**
- Every declared subroutine/procedure found in source is listed.
- Every external call target is listed.
- Nodes with no inbound calls are listed as orphan candidates with TBDs
  unless they are confirmed alternate entry points or callbacks.
- Nodes with many inbound calls are listed as hub/common candidates; the
  analyzer records the count and evidence, not a business interpretation.

### View 3: Call Evidence

```markdown
### Call Evidence

Evidence basis: source-level flow header + derived call analysis

| Caller | Callee | Call Type | Condition | Source Lines | Evidence Source | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| Main | SR990 | mainline | first-time-only (LR off) | line 145 | flow_header + derived_code | confirmed |
| Main | SR100 | subroutine | every call | line 152 | flow_header + derived_code | confirmed |
| SR100 | SR110 | subroutine | always | line 320 | derived_code_only | confirmed |
| SR100 | TARGET_PGM | dynamic_call | only if approved | lines 515-520 | derived_code_only | dynamic_unresolved |
```

**Rules:**
- `Call Evidence` replaces the old tree-style subsection. It is an
  auditable table, not a second visual tree.
- If the program has a source-level flow-header comment, use it as
  navigation evidence and summarize its contribution in `Evidence
  Source`; do not reproduce another tree unless preserving a short
  source excerpt is necessary for a drift TBD.
- Independently derive call relations from code. Code-derived call sites
  are authoritative for behavior facts.
- Dynamic calls must name the variable that carries the target, cite the
  assignment lines if visible, and mark `resolved`, `partially_resolved`,
  or `dynamic_unresolved`.
- `Evidence Source` values: `flow_header`, `derived_code`,
  `flow_header + derived_code`, `header_only`, `derived_code_only`.
- `Resolution` values: `confirmed`, `inferred`, `unresolved`,
  `resolved`, `partially_resolved`, `dynamic_unresolved`.

**Required columns:**
- **Caller / Callee:** subroutine, procedure, program, API, queue,
  service, variable-held target, or other node names.
- **Call Type:** `mainline`, `subroutine`, `procedure`,
  `external_call`, `dynamic_call`, `service_program`, `data_queue`,
  `batch_job`.
- **Condition:** when this call happens (`always`, `in DOWHILE loop`,
  `only if X`, `first-time only`, etc.) derived from surrounding control
  flow.
- **Source Lines:** exact source line or range for the call edge and
  target assignment if dynamic.
- **Evidence Source:** flow header and/or code-derived evidence basis.
- **Resolution:** whether the relation and target are confirmed or still
  unresolved.

### View 4: Reverse Caller Index

```markdown
### Reverse Caller Index

| Node | Called By | Notes |
| --- | --- | --- |
| SR990 | Main [line 145] | dead code after first call (LR-gated) |
| SR100 | Main [line 152] | hot path: called every invocation |
| SR110 | SR100 [line 320] | only callsite |
| SR111 | SR110 [line 410] | LCY branch only |
| SR112 | SR110 [line 422] | non-ATMP branch |
| SR113 | SR110 [line 434] | ATMP branch |
| (no callers) | — | dead subroutine (flag with TBD) |
```

**Why these views:**
- **Visual Overview** -> gives an RDi-like first read of the program.
- **Node Inventory** -> ensures every routine and external boundary is
  accounted for.
- **Call Evidence** -> captures caller, callee, condition, source lines,
  evidence source, and resolution status in an auditable table.
- **Reverse Caller Index** -> exposes orphaned subroutines (declared but
  never called -> dead code TBD) and hotspots (one node called from many
  sites).

### Source-Level Flow Header Handling

If the source has a flow-header comment block (common in IBM i shops),
the analyzer uses it as documented intent and navigation evidence in
`Visual Overview` and `Call Evidence`. The displayed `Visual Overview`
remains the required compact fenced `text` ASCII hierarchy. The header is
useful for orientation and SME comparison, but it is not authoritative
when it disagrees with actual EXSR/CALL/PERFORM/CALLP/CALLPRC call sites.

**Then** independently derive a Program Call Map from code. Actual call
sites are authoritative for behavior facts and code-derived call edges.
Compare:

| Header vs. Code | Action |
| --- | --- |
| Match exactly | Cite both the header and code-derived call sites; behavior facts remain supported by the code-derived call sites. |
| Header has subroutine not in code | TBD: comment drift (likely subroutine renamed/removed) |
| Code has subroutine not in header | TBD: comment drift (likely subroutine added without updating header) |
| Header parent-child order differs from code | TBD: comment may reflect old structure |
| No header present | Derive from code only; note absence. |

When header and code conflict, use the code-derived Program Call Map for
call edges and create a TBD for the mismatch. Matching header and code
may cite both sources, but EXSR/CALL/PERFORM/CALLP/CALLPRC statements
support `confirmed_from_code` behavior facts.

---

## Routine Cards Section

Routine cards are required for `segmented` and `large_program` mode and
recommended for standard mode when routines have meaningful state
impact. Each card summarizes one semantic unit before whole-program
synthesis.

```markdown
## Routine Cards

### MAIN

| Field | Value |
| --- | --- |
| Routine | MAIN |
| Location | lines 100-240 |
| Called By | external program entry |
| Calls Out | SR100, SR200, CHECKEXPOSE |
| Data Touches | CUSTMSTR, AUTHLOG, CHECKEXPOSE parameter list |
| State Impact | external handoff |
| Error Handling | checks return code from CHECKEXPOSE |
| Evidence | EV-AUTH-001, EV-AUTH-002 |
| Coverage | deep_read |
| Open Questions | Confirm caller parameter order with SME |
```

**Required fields:**
- Routine: subroutine, procedure, paragraph, or mainline segment
- Location: source line range
- Called By: immediate inbound callers
- Calls Out: internal and external calls made by this routine
- Data Touches: files, queues, screens, reports, parameters, and
  critical fields
- State Impact: `read-only`, `creates`, `updates`, `deletes`,
  `external handoff`, or `unknown`
- Error Handling: local monitor, indicator checks, message writes, or
  propagated status
- Evidence: source evidence IDs and line ranges
- Coverage: `indexed_only`, `deep_read`, or `blocked`
- Open Questions: source gaps, SME questions, or contradiction
  references

SME confirmation belongs in evidence or review fields, not the coverage
field.

---

## Routine Logic Details Section

Routine Logic Details are required for every load-bearing routine, procedure,
paragraph, or mainline segment with observed business logic, field
calculation, state mutation, external handoff, error/status assignment, display
message, report output, or branch that changes downstream behavior. Routine
Cards summarize coverage; Routine Logic Details explain what the routine
actually does.

For routine-dense programs, this section must remain compact in
`program-analysis.md` and link to sidecar detail instead of expanding every
routine inline:

- `routine_count <= 25`: full Routine Logic Details may appear in the main
  analysis.
- `routine_count > 25`: the main analysis contains a summary table and the full
  detail lives in `routine-logic-details.md` plus machine-readable
  `routine-logic-details.yaml`.
- `routine_count > 80` or source lines > 10,000: human-authored semantic detail
  must be split into `routine-logic-details/part-*.md` shard files by
  mainline/dispatch, state-changing routines, validation/message routines,
  external boundaries, and indexed utilities.

```markdown
## Routine Logic Details

| Routine | Role | Source Lines | Coverage | Deep Read Status | State Impact | Detail |
| --- | --- | --- | --- | --- | --- | --- |
| MAIN | entry dispatch | 1-3084 | deep_read | completed | control flow | RLOG-AUTH-001 |
| SR120 | validation/message routine | 520-780 | deep_read | completed | response status | RLOG-AUTH-017 |

### SR120 ValidateExposure

**Execution trigger:** Called from MAIN after customer record is found and
transaction amount is loaded.

**Step-by-step logic:**
1. Read `TRAN_AMT` (transaction amount) and `CUST_BAL` (customer balance).
2. Calculate `TMP_CUST_AMT = CUST_BAL - TRAN_AMT`.
3. If `TMP_CUST_AMT < 0`, set denial fields and return before the update path.
4. Otherwise leave `TMP_CUST_AMT` available for the later CUST_MAST update.

**Field calculations and assignments:**

| Target Field / Variable | Calculation / Assignment | Source Operands | Branch / Guard | Precision / Conversion | Business Effect | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `TMP_CUST_AMT` (post-transaction balance) | `CUST_BAL - TRAN_AMT` | `CUST_BAL` (customer balance), `TRAN_AMT` (transaction amount) | always before denial check | packed decimal 9P2 to 9P2; no rounding observed | feeds insufficient-balance branch and later persisted balance | EV-CREDIT-CHECK-014 |
| `ERR_CD` (error code) | literal `D003` | constant `D003` | `TMP_CUST_AMT < 0` | N/A | returned denial message code | EV-CREDIT-CHECK-015 |
| `APPROVED_AMT` (approved amount) | `TRAN_AMT` | `TRAN_AMT` (transaction amount) | `TMP_CUST_AMT >= 0` | same scale as input | authorizes requested amount | EV-CREDIT-CHECK-016 |

**Conditioned calculation blocks:**

| Block / Guard | Guard Type | Source Range | Guarded Statement Order | Calculation Chain | Final Output / Error Effect | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `IF TMP_CUST_AMT < 0` | IF branch | lines 120-126 | 1. compare `TMP_CUST_AMT`; 2. set `ERR_FLAG`; 3. set `ERR_CD`; 4. return | `CUST_BAL - TRAN_AMT -> TMP_CUST_AMT -> ERR_CD='D003'` | returns denial and skips CUST_MAST update | EV-CREDIT-CHECK-014, EV-CREDIT-CHECK-015 |

**Outcome reverse traces:**

| Outcome Code / Field | Reverse Trigger Chain | Guard / Conditioned Block | Source Operands / Carriers | Downstream Effect | Cross-References | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `D003` / `ERR_CD` | `CUST_MAST.CUST_BAL - TRAN_AMT -> TMP_CUST_AMT < 0 -> ERR_CD='D003'` | conditioned block `IF TMP_CUST_AMT < 0` | `CUST_MAST.CUST_BAL`, `TRAN_AMT`, `TMP_CUST_AMT` | returns denial and skips CUST_MAST update | Validation Logic `D003`; Exception Closure insufficient balance | EV-CREDIT-CHECK-014, EV-CREDIT-CHECK-015 |

**Routine field lineage / carriers:**

| Target Field / Variable | Source Carrier / Field | Intermediate Variables | Output / Persisted Carrier | Related Lineage / Mutation | Evidence |
| --- | --- | --- | --- | --- | --- |
| `TMP_CUST_AMT` (post-transaction balance) | `CUST_MAST.CUST_BAL` (customer balance), `TRAN_AMT` parameter | `TMP_CUST_AMT` | `CUST_MAST.CUST_BAL` update in SR210 | LIN-CREDIT-CHECK-004 / CUST_MAST mutation row | EV-CREDIT-CHECK-014 |
| `ERR_CD` (error code) | literal `D003` | `ERR_CD` | return parameter / message field | Validation Logic row `D003` | EV-CREDIT-CHECK-015 |
| `APPROVED_AMT` (approved amount) | `TRAN_AMT` parameter | `APPROVED_AMT` | return parameter | LIN-CREDIT-CHECK-005 | EV-CREDIT-CHECK-016 |

**Branch outcomes:**

| Branch / Condition | Fields Set / Actions | Exit / Next Step | Evidence |
| --- | --- | --- | --- |
| `TMP_CUST_AMT < 0` | `ERR_FLAG='Y'`, `ERR_CD='D003'` | RETURN; skips CUST_MAST update | EV-CREDIT-CHECK-015 |
| `TMP_CUST_AMT >= 0` | no error fields set | continue to SR210 update path | EV-CREDIT-CHECK-016 |

**Routine exception closure:**

| Exception / Guard | Trigger | Fields / Messages Set | Handling Action | Downstream Skip / Rollback / Output | Validation Logic Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| insufficient balance business guard | `TMP_CUST_AMT < 0` | `ERR_FLAG='Y'`, `ERR_CD='D003'`, `ERR_MSG='balance insufficient'` | RETURN | skips CUST_MAST update and downstream posting | `D003` | EV-CREDIT-CHECK-015 |
| no exception observed on approved branch | `TMP_CUST_AMT >= 0` | none | continue | update path remains eligible | N/A | EV-CREDIT-CHECK-016 |

**Unresolved routine logic:** None.
```

**Requirements:**
- Include one summary row for each load-bearing routine, procedure, paragraph,
  or mainline segment in `program-analysis.md`. Load-bearing means it performs
  field calculation, validation, branching that changes downstream behavior,
  file mutation, external handoff, error/status assignment, display/report
  output, or queue/message interaction.
- In routine-dense programs, full `### <routine>` subsections belong in the
  routine sidecar, not inline in the main analysis. Summary rows must link to
  stable `RLOG-<PROGRAM>-NNN` detail IDs.
- Technical utility routines may be omitted only when Routine Cards mark them
  `indexed_only` and Open Items / Limitations explain why no business/state
  claims depend on them.
- Step-by-step logic must preserve branch order, nested conditions, loop
  scope, early exits, fallback paths, and calls that change behavior.
- Field calculations and assignments must list each critical target field or
  variable, its exact expression or literal assignment, source operands,
  branch/guard, precision/conversion behavior when visible, business effect,
  and evidence.
- Conditioned calculation blocks must list every material guard-scoped
  calculation chain that affects money, percentage, quantity, status, return
  value, message/error code, persisted field, display/report field, queue
  payload, or downstream branch. Include RPG fixed-format conditioning
  indicators, named/numbered condition groups, result indicators, `IFxx` /
  `ELSE` / `ENDIF`, `CASxx`, `DO` scopes, operation-level indicators, CL
  labels/GOTO guards, and COBOL IF/EVALUATE branches when they guard
  calculations or assignments. Each block must preserve guarded statement
  order, source range, target fields, intermediate variables, final
  output/error effect, and evidence.
- If a shop or analyzer labels a source window as `Condition 5`, `C5`, an
  indicator combination, or another condition group, keep that label and
  analyze the guarded statements inside the matching routine. Do not leave it
  only in Logic Decomposition Ledger, Branch Outcomes, or a prose summary.
- Outcome reverse traces must start from each material message ID, status
  code, return code, response value, indicator-driven outcome, or error field
  and walk backwards to the branch/guard, conditioned calculation block,
  comparison threshold, intermediate variables, and source operands/carriers
  that make the outcome true. If the trigger chain cannot be fully traced,
  keep the outcome row and name the missing operand, branch, or source window
  as a `TBD-*`.
- A generic outcome explanation such as "warning/reject condition",
  "validation failed", or "product/group control check" is invalid when source
  code exposes calculated intermediates, thresholds, or operands. The reverse
  trace must show those fields and the guarded calculation order.
- Routine field lineage / carriers must connect calculated or assigned fields
  to source carriers, intermediate variables, output/persisted carriers, and
  the matching Field Lineage / Field Mutation Matrix row where one exists. If a
  field is local-only or not persisted, state `N/A-no persistence`; do not omit
  the carrier relationship.
- Routine exception closure must capture each business, parameter, I/O,
  external-call, return-code, indicator, or generic handler path visible inside
  the routine. Include trigger, error/status/message fields, handling action,
  skipped downstream write/call/output or rollback behavior, Validation Logic
  link, and evidence. If a routine has no observed exception path,
  write one `none observed` row with evidence or mark the gap as TBD.
- Do not use generic descriptions such as "calculates amount", "validates
  fields", or "sets status" without target fields, operands, conditions, and
  evidence.
- If the expression, operand meaning, constant meaning, precision behavior, or
  branch priority is unclear, keep the row and mark the unresolved part with a
  TBD instead of omitting the calculation.

---

## Validation Logic Section

Validation Logic is a front-loaded inventory of the program's validation,
status, return-code, response, message, and generic-handler outcomes. It must
appear immediately after top-of-document `Calculation Logic` and before
`Exception Handling` so IT SMEs can find outcome logic without hunting through
late error-handling prose. Do not duplicate this table later under
`Error Handling`.

```markdown
## Validation Logic

| Message / Status Code | Message Description | Validation / Error Type | Set By / Source Lines | Trigger Condition | Reverse Trigger Chain / Routine Logic Link | Output Carrier | Downstream Effect | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D003 | Balance would become negative; transaction is blocked | validation_error | `ERR_CD` assignment, SR120 lines 520-525 | TMP_CUST_AMT < 0 | Routine Logic Details `SR120 ValidateExposure` -> outcome reverse trace `D003`; `CUST_BAL - TRAN_AMT -> TMP_CUST_AMT < 0 -> D003` | return parameter / message field | blocks account update and downstream posting | confirmed |
| E501 | Customer master update failed | file_io_error | `TRANS_ERR_CD` assignment after UPDATE, lines 610-640 | %ERROR after UPDATE CUST_MAST | Exception Closure Ledger `CUST_MAST update failure`; no arithmetic chain | status field | caller receives transaction error; no further writes observed | confirmed |
| CPF4101 | File not found or file open failed | file_io_error | ON-ERROR CPF4101, SR900 lines 900-930 | OPEN CREDFILE failure | Exception Closure Ledger `File not found during open`; no arithmetic chain | display/message API | stops processing before reads | confirmed |
| *ANY / generic | Generic catch-all handler; exact message ID unresolved | unresolved | MONMSG MSGID(*ANY) or bare ON-ERROR | unexpected system exception | generic handler only; exact triggering code unresolved -> TBD-CREDIT-CHECK-006 | exception-log path or return parameter | generic coverage only; exact message ID unresolved | unresolved |

**Validation logic unresolved:** status/message fields were detected, but
literal code assignments were not fully traced.
```

**Requirements:**
- Validation Logic must be placed immediately after `Calculation Logic`, before
  `Exception Handling`, not buried inside `Error Handling`.
- Create one row per observed explicit message ID, error code, status code,
  response code, return code, SQLSTATE, CPF/MCH/RNX/CPD message,
  indicator-driven error branch, exception/log output code, data queue response
  status value, or generic catch-all token.
- Do not group multiple message IDs into one row. A row containing
  `UCC0120, UCC5127, UCC5135` with a family-level description such as
  "validation messages" is invalid; create separate rows and duplicate the
  branch/source context as needed.
- Each row must include a `Message Description` for that specific code. The
  description must come from a message file, approved reference pack, source
  literal, source comment, runtime evidence, vendor reference, or SME note. If
  no description is available, write
  `unresolved - message description not available`, mark Evidence Status
  `unresolved`, and create an Open Item / TBD.
- Columns: Message / Status Code, Message Description, Validation / Error Type,
  Set By / Source Lines, Trigger Condition, Reverse Trigger Chain / Routine
  Logic Link, Output Carrier, Downstream Effect, Evidence Status.
- Include all observed message families: `CPF*`, `CPD*`, `MCH*`,
  `RNX*`, `SQL*`, shop-local `UCC*` / `LCC*`, literal business error
  codes, return/status codes visible in source, and message/status
  fields assigned during validation or file I/O failures.
- Validation / Error Type values: `validation_error`, `file_io_error`,
  `business_rule_error`, `external_call_error`, `data_queue_error`,
  `response_status`, `exception_log`, `unresolved`.
- Output Carrier examples: response DS, message field, status field,
  data queue message, exception/log file, return parameter, display/message
  API.
- Reverse Trigger Chain / Routine Logic Link must point to the Routine Logic
  Details subsection, conditioned calculation block, outcome reverse trace,
  exception closure row, or source-backed TBD that explains why the code is
  set. When source exposes intermediates or thresholds, this column must show
  the field chain instead of a generic family label.
- Do not limit extraction to shop-local prefixes.
- Generic handlers (`*ANY`, bare `ON-ERROR`, generic error paragraphs)
  must be marked as generic coverage and must not be expanded into
  specific message IDs without source evidence.
- If validation logic cannot be fully traced, add an explicit
  **Validation logic unresolved:** sentence explaining the gap.

---

## Deep Read Windows Section

Deep-read windows document the exact source windows used for semantic
analysis when the whole program cannot safely stay in context.

```markdown
## Deep Read Windows

| Window ID | Routine / Path | Source Lines | Why Selected | Coverage Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| DRW-AUTH-001 | MAIN -> SR100 -> SR110 | 100-520 | hot path and approval decision | deep_read | EV-AUTH-001 |
| DRW-AUTH-002 | SR800 | 2100-2260 | writes AUTHLOG | deep_read | EV-AUTH-006 |
```

**Selection priorities:**
- Entry mainline and trigger handling
- Routines on hot call paths
- Routines with external calls
- Routines that write, update, delete, commit, roll back, send messages,
  or send queue payloads
- Routines touching money, account/customer IDs, inventory,
  approval/decline state, posting flags, audit IDs, or error/return
  codes
- Routines involved in contradictions or flow-header drift

Do not deep-read every technical utility routine if it is structurally
indexed and has no business state impact.

---

## Control Flow Section

```markdown
## Control Flow

### Main Entry Point
1. Accept input parameters [EV-CREDIT-CHECK-001]
2. Call VALIDATECREDIT subroutine with (Amount, Limit) → [evidence_strength]
3. Branch on validation result:
   - If validation PASS (result = 1): proceed to step 4
   - If validation FAIL (result = 0): jump to step 5
4. Call CHECKEXPOSE program (Amount, CustID) → [evidence_strength]
   - If CHECKEXPOSE returns APPROVED: set result code = 1, go to step 6
   - If CHECKEXPOSE returns DENIED: set result code = -1, go to step 5
5. Write error message to QSYSOPR message queue, return result code
6. Return result code to caller

**Control structures:**
- Conditional: SELECT statement on validation result (lines 120–150)
- Loop: READE on CUSTFILE for validation iterations (lines 160–180)
- External call: CALLP CHECKEXPOSE (line 175)

**Evidence links:**
- [EV-CREDIT-CHECK-001: Source lines 100–210]

### VALIDATECREDIT Subroutine
1. Compare input Amount parameter vs. CREDLIMIT value from CREDFILE
2. If Amount ≤ CREDLIMIT: return 1 (pass)
3. Else: return 0 (fail)

**No error handling observed.** [evidence_strength: confirmed_from_code]
```

**Requirements:**
- Document main entry point control flow first, then each callable subroutine
- Use numbered steps with brief descriptions
- Identify control structures: conditionals, loops, external calls, error handling
- Tag evidence for each non-trivial step
- Note line numbers if available
- Create TBD for unclear branching logic or missing subroutines

**Format guidelines:**
- Steps should be executable (SME can predict program behavior from steps alone)
- Subroutine flow should be self-contained (independent of caller context)
- Loops and branches should show all paths (happy path + error paths)
- External calls should name the called program and parameters

---

## Object Dependencies Section

This section is the **flat reference inventory** — every external object the program touches, in one table. It matches the shop's `F5-OBJREF TREE` tool output so SMEs can compare side-by-side.

**Why this section exists separately from File I/O / External Calls:**
- Object Dependencies = **what is referenced** (flat list, all types)
- File I/O = **how files are read/written** (deep dive on PF/LF/DSPF/PRTF only)
- External Calls = **how programs are invoked** (deep dive on \*PGM / \*SRVPGM only)

An object listed in Object Dependencies that is a file should also appear in File I/O with operation details; if it is a called program, in External Calls. Data areas, copybooks, data structures appear only here.

### Format

```markdown
## Object Dependencies

Source: shop F5-OBJREF TREE tool output | derived-from-code | both (matched)

### Uses (forward dependencies)

| Object        | Type      | Version  | Description                                  | Inventory ID         | Evidence            |
| ---           | ---       | ---      | ---                                          | ---                  | ---                 |
| HSSDTAR002    | *DTAARA   | 01.00.00 | Batch Run Date-Related Parameters Data Area  | OBJ-AUTH-ONUS-014    | confirmed_from_code |
| HSSDTAR100    | *DTAARA   | —        | (description not in tool output)             | OBJ-AUTH-ONUS-015    | confirmed_from_code |
| @CU176D       | PF (DS)   | 01.00.00 | @CU176 Program Parameter Data Structure      | OBJ-AUTH-ONUS-016    | confirmed_from_code |
| ADEALTP       | PF        | 01.00.00 | ATM Deal Number Table                        | OBJ-AUTH-ONUS-017    | confirmed_from_code |
| AUTHTPDS      | PF        | 25.K.23A | DS for Segment ID AUTHTP IN CCAUSGP/HP       | OBJ-AUTH-ONUS-018    | confirmed_from_code |
| CC030D        | PF (DS)   | 01.00.00 | CC030 Program Parameter Data Structure       | OBJ-AUTH-ONUS-019    | confirmed_from_code |
| CC040D        | PF (DS)   | 01.00.00 | CC040 Program Parameter Data Structure       | OBJ-AUTH-ONUS-020    | confirmed_from_code |
| HCCDTAR001    | Copybook  | —        | (D-spec include)                             | TBD-AUTH-ONUS-NNN    | confirmed_from_code |
| HCCDTAR115    | Copybook  | —        | (D-spec include)                             | TBD-AUTH-ONUS-NNN    | confirmed_from_code |
| CHECKEXPOSE   | *PGM      | —        | Credit exposure check (external program)     | OBJ-AUTH-ONUS-030    | confirmed_from_code |

### Used By (reverse dependencies)

Drawn from `01_inventory/inventory.yaml` `relationships` section.

| Caller      | Type   | Notes                              | Evidence                          |
| ---         | ---    | ---                                | ---                               |
| ORDENTR     | *PGM   | Calls CU101A on online auth flow   | from inventory relationships      |
| CU101B      | *PGM   | Calls CU101A after batch staging   | from inventory relationships      |
```

### Required Columns

| Column | Source / Meaning |
| --- | --- |
| Object | Object name as it appears in source code (uppercase, IBM i naming) |
| Type | `PF`, `LF`, `DSPF`, `PRTF`, `*DTAARA`, `*DTAQ`, `*MSGF`, `*PGM`, `*SRVPGM`, `Copybook`, `PF (DS)` |
| Version | Shop-tracked version if available (e.g., `01.00.00`, `25.K.23A`); `—` if not tracked |
| Description | Business description from the shop tool, source comment, or inventory |
| Inventory ID | Matching `OBJ-*` from `01_inventory/inventory.yaml`; or `TBD-*` if inventory has no entry |
| Evidence | `confirmed_from_code` (F-spec, D-spec, /COPY, CALL statement) or `needs_sme_review` |

### Object-Type Recognition Hints

- **`H`-prefix** in shop conventions often = **header / D-spec include** (copybook); confirm against `/COPY` directives in source
- **`@`-prefix** often = **data-structure copybook** (parameter DS); confirm against `D` specs
- **`HSS`-prefix** in this shop = data areas (`HSSDTAR…` = SSDTAR data area family)
- **`HCC`-prefix** in this shop = copybooks (`HCCDTAR…` = CCDTAR family copybooks)
- These conventions are **shop-specific** — verify with the SME and add to a shop-conventions reference rather than hard-coding into the analysis.

### Inventory Cross-Check Rule

For every object in this table:
- If `01_inventory/inventory.yaml` has a matching `OBJ-*` → use that ID
- If not → create `TBD-<SLUG>-NNN: inventory gap, object [NAME] used by [PROGRAM] not in inventory`
  - Blocking: `pending_source` (inventory is incomplete)
  - This is a signal back to the inventory skill that its scope needs widening.

### Source Comparison Rule

If the shop's `F5-OBJREF TREE` output is provided as input:
- Reproduce its rows verbatim in the "Uses" table
- Independently re-derive the list from source code (F-specs, D-specs, /COPY directives, CALL statements)
- Mark "Source: both (matched)" if identical
- If shop tool has objects not in code or vice versa → create TBD (tool drift / dead reference / missing source)

---

## Logic Decomposition Ledger Section

The Logic Decomposition Ledger preserves rule-bearing code before it is
compressed into narrative. It exists because phrases like "amount
calculation", "validation", or "status processing" are not enough for
equivalent replay.

```markdown
## Logic Decomposition Ledger

| Logic ID | Routine / Lines | Logic Type | Source Inputs / Constants | Operation / Condition | Result Field / Action | Branch Priority / Loop Scope | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LOG-AUTH-001 | SR110 lines 410-418 | arithmetic | AMT_PRIN, AMT_INTR, AMT_FEE | ADD principal + interest, SUB fee | AMT_TOTAL | executes before limit comparison | EV-AUTH-041 |
| LOG-AUTH-002 | SR130 lines 520-545 | nested IF | TRANAMT, RATE_FEE literals | tiered amount comparison | RATE_FEE assigned | mutually exclusive tiers; final ELSE fallback | EV-AUTH-042 |
| LOG-AUTH-003 | SR160 lines 700-735 | file loop | TRANFIL, TRANTYP='01' | READ/DOW + IF filter | VALID_TOTAL accumulated | loop until %EOF(TRANFIL) | EV-AUTH-043 |

### Routine / Window Data Flow

| Routine / Window | Purpose | Input Variables | Transformation Logic | Output Variables | Side Effects | Source Lines | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SR110 | Convert requested amount into billing amount | `P0HCCM` (request card number) [input]<br>`WQCHNT` (channel) [input] | Maps request fields to lookup key; validates card master; sets response status/message | `WRTTNC` (process status) [output]<br>`WRMSG` (response message) [output] | CHAIN `CCCDMSP`; CALL dynamic `CU138` | lines 410-455 | EV-AUTH-044; inferred field meanings marked inline |
```

### Required Coverage

Capture every observed rule-bearing instance of:

- arithmetic and expression operations (`ADD`, `SUB`, `MULT`, `DIV`,
  `EVAL`, SQL expressions)
- precision behavior (`ZONED`, rounding, truncation, scale conversion,
  packed/zoned movement when it changes value shape)
- string construction (`CAT`, substring, concatenation, generated
  numbers, message or queue payload assembly)
- constants and literals used for limits, rates, status values,
  return/error codes, message IDs, flags, branch decisions, or persisted
  values
- single-condition, compound-condition, nested-condition, `SELECT` /
  `CASE`, and fallback branches
- loops and file scans that affect totals, selection, reporting,
  posting, deletes, or downstream calls
- variable-level data flow for each routine/window that drives calls,
  file I/O, field mutation, response status, error handling, or external
  payloads

### Branch-Preservation Rule

Do not flatten nested or mutually exclusive logic into unrelated rows
when priority affects behavior. The ledger must preserve ordering,
fallback, and loop scope. If priority is unclear because source windows
or copybooks are missing, create a TBD rather than invent a simplified
rule.

### Routine / Window Data Flow Requirements

- Show input variables, transformed variables, output variables, side
  effects, source lines, and evidence for every load-bearing routine or
  deep-read window.
- Variable format is `VARIABLE_NAME` (business meaning) [direction].
- Direction values: `input`, `output`, `input-output`, `local`,
  `control`.
- If the variable name is unresolved but meaning is known, use
  `variable unresolved` (business meaning) [direction].
- If the variable name is known but meaning is unresolved, use
  `VARIABLE_NAME` (meaning unresolved) [direction].
- If meaning is inferred, mark it inline:
  `VARIABLE_NAME` (business meaning; inferred) [direction].

---

## Data Touch Map Section

The Data Touch Map is the program-local data movement and state-change
view. It answers: "Which routine touches which data carrier, with what
operation, and what state impact?"

It is not a full field lineage report. Track object-level, record-level,
and critical-field-level movement only.

### Format

```markdown
## Data Touch Map

### Data Touches

| Data Object / Carrier | Mechanism | Operation | Routine / Procedure | Key / Payload | Critical Fields Touched | State Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CUSTMSTR | PF | CHAIN | SR100 | key=CustID | CustID, Status, RiskCode | read-only lookup | EV-AUTH-001 |
| AUTHLOG | PF | WRITE | SR800 | AuthNo | Amount, Decision, RC | creates audit/transaction row | EV-AUTH-002 |
| HSSDTAR002 | *DTAARA | IN / OUT | SR990 | BatchRunDate + completion flag | BatchRunDate, CompleteFlag | reads and updates shared state | EV-AUTH-003 |
| QRCVDTAQ | *DTAQ | QRCVDTAQ | SR980 | inbound fixed-format message | AccountNo, Amount, TranType | async receive | EV-AUTH-004 |
| PA196 | CALL parameters | inout | SR300 | AccountNo, Amount, Decision, RC | Decision, RC | external program boundary | EV-AUTH-005 |

### Critical Field Watchlist

| Field / Data Structure | Object / Carrier | Why It Matters | Observed Operations | Evidence |
| --- | --- | --- | --- | --- |
| Decision | PA196 parameter list | approval / decline outcome | passed out, tested by caller | EV-AUTH-005 |
| Amount | AUTHLOG / PA196 | money movement | compared, written, passed to external program | EV-AUTH-002 |
```

### Required Columns

| Column | Source / Meaning |
| --- | --- |
| Data Object / Carrier | File, data area, data queue, message queue, call parameter list, copybook/data structure, DSPF/PRTF, or IFS file |
| Mechanism | `PF`, `LF`, `DSPF`, `PRTF`, `*DTAARA`, `*DTAQ`, `*MSGQ`, `CALL parameters`, `Copybook/DS`, `IFS` |
| Operation | `READ`, `CHAIN`, `READE`, `WRITE`, `UPDATE`, `DELETE`, `EXFMT`, `IN`, `OUT`, `SNDDTAQ`, `RCVDTAQ`, `CALL in/out/inout`, etc. |
| Routine / Procedure | Internal node from the Program Call Map that performs the operation |
| Key / Payload | Key fields, message format, parameter list, or record format used |
| Critical Fields Touched | Important fields only: money, status, customer/account, inventory, posting, approval, return/error codes, audit IDs |
| State Impact | `read-only`, `creates`, `updates`, `deletes`, `async send`, `async receive`, `external handoff`, `unknown` |
| Evidence | EV-* link to source statements / DDS / copybook / interface docs |

### Granularity Rule

Default to object / record / critical-field granularity. Do not document
every RPG work variable. Escalate to field-level detail only when the
field affects money, inventory, customer/account status, posting,
approval/decline, compliance, auditability, external payloads, or error
outcomes.

### Relationship to File I/O and External Calls

- Data Touch Map = where data enters, changes, persists, or leaves this
  program.
- File I/O = detailed file access mechanics for PF/LF/DSPF/PRTF.
- External Calls = detailed program/interface invocation contracts.

The same evidence may appear in all three sections from different
angles. For example, `CALL PA196` appears as a Program Call Map edge, a
Data Touch row for parameter movement, and an External Calls row for
interface contract.

---

## Key File & Field Logic Section

This section turns the Data Touch Map into a replayable field story. It
answers: "Which files and fields are load-bearing, why, where do values
come from, and where do they land?"

Every key field, critical field, and important variable must preserve the
source identifier and business meaning when resolvable:

- Preferred field format: `FIELD_NAME` (business meaning)
- Preferred variable format: `VARIABLE_NAME` (business meaning)
  [direction]
- Known meaning, unresolved source name: `field unresolved` (business meaning)
- Known source name, unresolved meaning: `FIELD_NAME` (meaning unresolved)
- Inferred meaning: `FIELD_NAME` (business meaning; inferred)

### Format

```markdown
## Key File & Field Logic

### Key Files

| File / Carrier | Role in Program | Routines | Access / Mutation Pattern | Key Fields | Critical Persisted / Output Fields | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| CUST_PHY | state-update | SR210 | CHAIN then UPDATE when %FOUND | `CUST_NO` (customer number) | `PHY_CUST_AMT` (customer balance), `CUST_TRAN_FLG` (transaction flag) | EV-AUTH-051 |
| TRAN_DTL | detail-insert | SR240 | WRITE when ERR_FLAG='N' and TRAN_AMT>0 | `DTL_SNO` (detail sequence number) | `DTL_CUSTNO` (customer number), `DTL_AMT` (transaction amount), `DTL_TYP` (transaction type), `DTL_STS` (transaction status) | EV-AUTH-052 |
| ERRMSGQ | queue-message | SR900 | SNDPGMMSG on validation failure | `MSGID` (message identifier), `ERR_CD` (error code) | `ERR_MSG` (error message payload) | EV-AUTH-053 |

### Key Fields

| Field / Data Structure | Source Object / Carrier | Role | Used In | Values / Domain Observed | Downstream Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `CUST_NO` (customer number) | input parameter / CUST_PHY key | access-key | CHAIN CUST_PHY; CALL SUBPGM02 | copied from parameter | determines account row updated and downstream handoff | EV-AUTH-054 |
| `TMP_CUST_AMT` (temporary customer balance) | work variable | calculation-result / branch-condition | balance deduction and insufficient-balance IF | derived from BUSI_AMT - TRAN_AMT | blocks write when < 0; otherwise persisted back | EV-AUTH-055 |
| `ERR_CD` (error code) | work variable / return payload | error-code | validation failure paths | 'D003', 'E501' | returned to caller and logged | EV-AUTH-056 |

### Field Lineage

| Lineage ID | Source / Physical Field | Alias / Data Structure | Work Variables | Calculation / Condition | Write-Back Alias | Persisted / Output Field | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIN-AUTH-001 | `CUST_PHY.PHY_CUST_AMT` (customer balance) | `VIEW_CUST_BAL` (view customer balance) | `BUSI_AMT` (business amount), `TMP_CUST_AMT` (temporary customer balance) | SUB TRAN_AMT; IF TMP_CUST_AMT < 0 | `VIEW_CUST_BAL` (view customer balance) | `CUST_PHY.PHY_CUST_AMT` (customer balance) | EV-AUTH-057 |
```

### Key File Roles

Use one or more of these role labels:

- `driver`: source of the main loop or primary transaction selection
- `lookup/reference`: read-only source used to validate, enrich, or
  calculate
- `state-update`: existing record whose state is changed
- `detail-insert`: new detail, journal, staging, or transaction row
- `audit-log`: persistent event, error, report, spool, or journal output
- `screen-report`: DSPF/PRTF interaction
- `queue-message`: message queue or data queue payload carrier
- `parameter-DS`: call parameter data structure or copybook carrier

### Key Field Roles

Use one or more of these role labels:

- `access-key`
- `input`
- `derived`
- `calculation-operand`
- `calculation-result`
- `branch-condition`
- `status-flag`
- `return-code`
- `error-code`
- `message-id`
- `external-parameter`
- `persisted-field`
- `audit-output`

### Lineage Requirements

- Every field involved in money, inventory, customer/account status,
  posting, approval/decline, compliance, auditability, external
  payloads, or error outcomes must appear either in Key Fields or in a
  Field Lineage row.
- A Field Lineage row must connect the most concrete source available
  to the final persisted/output field. If the physical field is hidden
  behind a DDS/copybook alias, include the alias and create a TBD if the
  physical mapping is missing.
- Work variables are included when they carry or transform critical
  values. Do not enumerate unrelated temporary variables.
- Do not infer a key-file role or field role from a name alone. Use
  source evidence, DDS/copybook metadata, runtime evidence, or SME
  confirmation.
- Do not output only a business description such as "card number", and
  do not output only a source name such as `K0CRNO` when meaning is
  resolvable. Use `K0CRNO` (card number).

---

## File I/O Section

```markdown
## File I/O

### File Access Summary

| File | Record Format | Type | Operations | Key Fields | Purpose | Read / Mutation Conditions | Indicators / Status Checks | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CREDFILE | CREDR | PF | CHAIN | `CUSTID` (customer identifier) | Validate customer credit record existence before approval logic. | before validation branch | *IN99 / %FOUND | EV-CREDIT-CHECK-002 |
| CUSTFILE | CUSTR | LF | READE | `CUSTID` (customer identifier) | Read matching customer records for validation scope. | loop until EOF | EOF indicator / %EOF | EV-CREDIT-CHECK-003 |
| CUST_MAST | CUSTMR | PF | CHAIN, UPDATE | `CUST_NO` (customer number), `CUSTSTS` (customer status) | Validate customer record and persist transaction flag changes. | only when ERR_FLAG='N' and %FOUND | %FOUND, %ERROR | EV-CREDIT-CHECK-004 |

### Field Mutation Matrix

| File | Operation | Routine / Lines | Access Key / Record Condition | Field Mutated / Persisted | Source Value / Expression | Assignment Evidence | Error / Rollback Handling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CUST_MAST | UPDATE | SR210 lines 610-640 | key=(`CUST_NO` (customer number), `CUSTSTS` (customer status)), %FOUND(CUST_MAST) | `CUST_BAL` (customer balance) | CUST_BAL - TRAN_AMT | EV-CREDIT-CHECK-012 | %ERROR -> TRANS_ERR='Y', TRANS_ERR_CD='E501', RETURN |
| CUST_MAST | UPDATE | SR210 lines 610-640 | key=(`CUST_NO` (customer number), `CUSTSTS` (customer status)), %FOUND(CUST_MAST) | `CUST_TRAN_FLG` (customer transaction flag) | literal 'Y' | EV-CREDIT-CHECK-013 | same UPDATE handler |

**Operation details:**

- **CREDFILE / CHAIN on CUSTID:** Validate customer credit record existence. Key field: `CUSTID` (customer identifier). Result: populated *IN99 (not found indicator).
- **CUSTFILE / READE on CUSTID:** Read all matching customer records for validation scope. Key field: `CUSTID` (customer identifier). Continue until EOF or error.
- **CUST_MAST / UPDATE after CHAIN:** Persist fields assigned before the update; handler sets transaction error fields if `%ERROR` is observed.

**Evidence links:**
- [EV-CREDIT-CHECK-002: DB2 for i table definitions]
- [EV-CREDIT-CHECK-003: RPGLE F-specs and I/O statements]

**Unresolved:**
- TBD-CREDIT-CHECK-002: Confirm whether CUSTFILE includes historical records or active only
```

**Requirements:**
- One File Access Summary row per file accessed
- One Field Mutation Matrix row per persisted field touched by `WRITE`,
  `UPDATE`, `DELETE`, or SQL DML. For `DELETE`, use the deleted record
  or selection predicate as the persisted mutation.
- File Access Summary columns: File name, record format, Type (PF / LF / DSPF / PRTF), Operations, Key fields, Purpose, read/mutation conditions, indicators/status checks, Evidence link
- Field Mutation Matrix columns: File, operation, routine/line range, access key or record condition, field mutated/persisted, source value or expression, assignment evidence, error/rollback handling
- Key Fields must use `FIELD_NAME` (business meaning) whenever
  resolvable. If an approved dictionary/reference pack supplies a
  `standard_field_id`, include it inline or in the row note. If unresolved, use
  `field unresolved` (business meaning) or `FIELD_NAME` (meaning unresolved).
- Field and control-value meanings from reference packs must cite the
  pack/file/row or anchor used. If reference-pack meaning conflicts with code
  behavior, preserve both and create a contradiction TBD.
- Purpose must describe why the file is accessed with an action verb
  such as validate, read, detect, write, send, or log. Purpose must not
  replace field descriptions.
- Supported operations:
  - Sequential: READ (next record), READP / READPE (read previous)
  - Random: SETLL (set lower limit), READE (read equal), CHAIN (random access)
  - Write: WRITE (add new record), UPDATE (modify record), DELETE (remove record)
  - Display: EXFMT (formatted I/O on DSPF, used for menus and interactive input screens)
  - SQL: EXEC SQL blocks, cursor operations, SQLCODE / SQLSTATE error handling
- For each operation, document:
  - Key fields used in access (e.g., CHAIN on CUSTID)
  - Indicators set (e.g., *IN99 for not found) or status variables (SQLCODE)
  - Expected record count or iteration scope
  - Branch condition that permits `WRITE`, `UPDATE`, `DELETE`, or SQL DML
  - Every field assignment that feeds a persisted write/update, including
    literals, source fields, expressions, copied aliases, and calculated values
  - Pre-mutation checks (`%FOUND`, indicators, validation flags) and
    post-mutation checks (`%ERROR`, `SQLCODE`, `SQLSTATE`, return codes)
- Reference file definitions from inventory (EV-*) and DDS / SQL schema where available
- Tag evidence as `confirmed_from_code` or `needs_sme_review`
- Create TBD for missing DDS, unclear key fields, unknown record formats,
  SQL schema not documented, undocumented access patterns, or a persisted
  field whose source assignment cannot be proven

---

## External Calls Section

```markdown
## External Calls

| Program | Call Type | Caller Routine | Source Lines | Parameters | Resolution Status | Purpose | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GETRATE | service_program | SR100 | line 175 | `RateCode` (rate code) [input] -> `Rate` (interest rate) [output] | resolved | Fetch interest rate by code. | EV-CREDIT-CHECK-005 |
| CHECKEXPOSE | external_call | SR120 | line 210 | `Amount` (credit amount) [input], `CustID` (customer identifier) [input] -> `Decision` (exposure decision) [output] | confirmed | Check credit exposure limits. | EV-CREDIT-CHECK-006 |
| TARGET_PGM -> UPDATEJNL | dynamic_call | SR900 | lines 300-312 | `JournalCode` (journal code) [input], `Timestamp` (event timestamp) [input], `RC` (return code) [output] | partially_resolved | Write to audit journal; target assigned from TARGET_PGM. | EV-CREDIT-CHECK-007 |

**Call details:**

- **GETRATE:** CALLP GETRATE(RateCode), returns RATE field. Error handling: if call fails, MONITOR catches and logs error.
- **CHECKEXPOSE:** CALL CHECKEXPOSE (Amount, CustID, Decision). Synchronous, blocks until return.
- **TARGET_PGM -> UPDATEJNL:** dynamic CALL through TARGET_PGM. TARGET_PGM is assigned to UPDATEJNL before the call; called only if audit flag is set.

**Parameter contracts:**
- GETRATE expects RateCode to match RATE_TABLE key (uppercase, 3 chars). Undocumented → TBD-CREDIT-CHECK-003
- CHECKEXPOSE returns Decision: 'A' (approved), 'D' (denied), 'U' (unknown). Confirmed from source comments.
- UPDATEJNL RC values: 0 (success), 1 (journal full), -1 (system error). Confirmed from called program documentation.

**Unresolved:**
- TBD-CREDIT-CHECK-003: Confirm GETRATE parameter validation and error codes
- TBD-CREDIT-CHECK-004: Confirm CHECKEXPOSE network timeout behavior (call fails or returns default?)
```

**Requirements:**
- One table row per external call (program call, service program call,
  dynamic call, remote interface, service program, data queue, batch job)
- Columns: Program, Call Type, Caller Routine, Source Lines, Parameters,
  Resolution Status, Purpose, Evidence
- For each call, document:
  - Parameter types and expected ranges
  - Return value or status code
  - Synchronous vs. asynchronous
  - Error handling (if monitored)
  - When the call is made (conditional or always)
  - Dynamic target variable, assignment source lines, and resolution
    status when a target is built from a variable
- Reference evidence links (EV-*)
- Resolution Status values: `resolved`, `partially_resolved`,
  `dynamic_unresolved`, `inferred`, `confirmed`
- Dynamic calls must not be marked `confirmed` unless the concrete target
  is actually resolved from code or other evidence.
- Tag evidence as `confirmed_from_code` or `needs_sme_review`
- Create TBD for undocumented parameters, missing documentation, unclear
  network behavior, or unresolved dynamic targets

---

## Error Handling Section

```markdown
## Error Handling

### Exception Closure Ledger

| Exception / Error Condition | Trigger / Source | Message ID / Error Code / RC | Detected By | Fields Set / Messages Sent | Handling Action | Downstream Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Balance would become negative | TMP_CUST_AMT < 0 | D003 | IF validation branch | ERR_FLAG='Y', ERR_CD='D003', ERR_MSG=literal text | RETURN | blocks account update and downstream posting | EV-CREDIT-CHECK-010 |
| CUST_MAST update failure | UPDATE CUST_MAST then %ERROR | E501 | %ERROR after UPDATE | TRANS_ERR='Y', TRANS_ERR_CD='E501' | RETURN | caller receives transaction error; no further writes observed | EV-CREDIT-CHECK-011 |
| File not found during open | OPEN CREDFILE | CPF4101 | ON-ERROR CPF4101 | ERR_CD='F001', SNDPGMMSG | GOTO ERRHANDLR | stops processing before reads | EV-CREDIT-CHECK-012 |
| Unexpected system exception | MONITOR protected block | generic / *ANY | bare ON-ERROR | ERR_CD='9999' | log and RETURN | generic coverage only; exact message ID not inferred | EV-CREDIT-CHECK-013 |

### Validation Logic Cross-Reference

Validation/status/message code rows are front-loaded in `## Validation Logic`.
Every exception row with a message, status, return code, response value, or
generic handler must cross-reference that section through the visible code,
carrier, or source-backed TBD.

**Unhandled exceptions:**
- CUSTFILE READE fails with I/O error: no MONITOR block → Program will abnormally terminate → TBD-CREDIT-CHECK-005: Confirm error handling intent

**Generic handlers:**
- MONMSG `MSGID(*ANY)` / bare `ON-ERROR` / generic error paragraphs are recorded as generic coverage. They do not prove that any specific CPF/CPD/MCH/RNX/SQL/shop-local message is handled unless that message ID is explicitly named elsewhere.

**Logged errors:**
- Error messages written to QSYSOPR (message queue)
- Error codes logged if UPDATEJNL succeeds
- No persistent error table observed

**Evidence links:**
- [EV-CREDIT-CHECK-008: RPGLE MONITOR blocks]
- [EV-CREDIT-CHECK-009: CALL error handling]
```

**Requirements:**
- One Exception Closure Ledger row per observed business, parameter,
  file I/O, SQL, call, queue/message, display/report, or system
  exception path.
- Columns: exception/error condition, trigger/source, message ID/error
  code/return code, detection mechanism, fields set/messages sent,
  handling action, downstream impact, evidence.
- Cross-reference the front-loaded `Validation Logic` row for every observed
  message/status/return/response/generic outcome. Do not duplicate the
  Validation Logic table inside Error Handling.
- Separate section for unhandled exceptions (errors NOT caught)
- Note which errors log messages and where
- State downstream impact: continue, return, skip write, rollback,
  abort, call downstream, suppress downstream call, or unknown
- Reference evidence links
- Tag evidence strength
- Create TBD for unclear error codes, missing error handling,
  context-dependent behavior, generic-only coverage that is not
  production-realistic, or any error branch whose downstream impact is
  unknown

---

## Redundancy Candidate Notes Section

This section is optional only when no plausible redundancy candidates are
observed. It is a marking surface, not a deletion instruction.

```markdown
## Redundancy Candidate Notes

| Candidate | Location | Candidate Redundancy | Reason | Trace / Last Observed Use | Evidence | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| TMP_CUST_AMT | lines 520-545 | no | participates in deduction, insufficient-balance branch, and write-back lineage | VIEW_CUST_BAL -> BUSI_AMT -> TMP_CUST_AMT -> CUST_PHY.PHY_CUST_AMT | EV-AUTH-061 | preserve |
| MOVE WORK_A WORK_B | lines 760-761 | unknown | downstream called program source missing | WORK_A -> WORK_B -> CALL SUBPGM02 parameter | EV-AUTH-062 | pending_source |
```

### Conservative Marking Rule

Mark `candidate_redundancy: yes` only when the candidate is not observed
in any:

- calculation or precision conversion
- branch condition, loop control, CASE/SELECT, or return decision
- file write/update/delete or SQL DML
- log, message, spool, report, screen, data queue, or message queue
- exception handling, rollback, skip, return, or error-code path
- external program parameter handoff
- field lineage from source to persisted/output field

If source is missing or cross-program use is unclear, mark `unknown` and
create a TBD. The analysis never removes code facts.

---

## TBDs & Blocking Status Section

```markdown
## TBDs & Blocking Status

### Open Items / Limitations

| Open Item | Impact | Evidence Gap | Suggested Follow-up |
| --- | --- | --- | --- |
| Dynamic call target unresolved | May miss downstream dependency | Target built from runtime field | Review target assignment source and runtime values |
| Field meaning unresolved | Weakens business interpretation | DDS/reference field missing | Review DDS or SME notes |
| Error code assignments incomplete | May miss response behavior | Literal assignments not fully traced | Trace status/message fields |

### Pending Source
- **TBD-CREDIT-CHECK-002:** Confirm CUSTFILE includes historical records or active only
  - Blocking: pending_source — missing CUSTFILE DDS field documentation
  - Related: [OBJ-CREDIT-CHECK-001], [EV-CREDIT-CHECK-003]

### Pending SME Judgment
- **TBD-CREDIT-CHECK-001:** Confirm MAIN parameter order matches call sites
  - Blocking: pending_sme_judgment — source header ambiguous
  - Related: [EV-CREDIT-CHECK-001]

- **TBD-CREDIT-CHECK-003:** Confirm GETRATE parameter validation and error codes
  - Blocking: pending_sme_judgment — external program undocumented
  - Related: [OBJ-CREDIT-CHECK-005]

- **TBD-CREDIT-CHECK-005:** Confirm error handling intent for CUSTFILE I/O failures
  - Blocking: pending_sme_judgment — unhandled exception possible
  - Related: [OBJ-CREDIT-CHECK-001]

### Non-Blocking
- **TBD-CREDIT-CHECK-004:** Confirm CHECKEXPOSE network timeout behavior
  - Blocking: non_blocking — call has error handling, timeout path defined
  - Related: [OBJ-CREDIT-CHECK-006]
```

**Requirements:**
- Group TBDs by blocking status:
  - `pending_source` — missing DDS, incomplete source
  - `pending_sme_judgment` — behavior unclear from source alone
  - `non_blocking` — known gaps that don't affect downstream analysis
- Keep `Open Items / Limitations` as the centralized unresolved-item
  summary for reviewers. Do not scatter unresolved dynamic calls, field
  meanings, or error-code gaps only inside earlier sections.
- For each TBD, include:
  - Question statement
  - Blocking status
  - Related object/evidence IDs
- No TBD should be vague ("something is unclear")
- Every TBD must map to a concrete gap or ambiguity

---

## Review Checklist Section

```markdown
## Review Checklist

Before approval, SME must validate:

- [ ] Entry points are correct and complete (no missing callable subroutines)
- [ ] Program Call Map keeps Visual Overview compact and uses Call Evidence for auditable caller/callee evidence
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] Routine Logic Details summarize every load-bearing routine in the main analysis and route routine-dense detail to `routine-logic-details.md` / `routine-logic-details.yaml` with stable `RLOG-*` IDs
- [ ] Routine Logic Details or sidecar detail explain field calculations, conditioned calculation blocks, carrier/lineage ties, routine-local exception closure, branch outcomes, source lines, evidence, and outcome reverse traces for each deep-read load-bearing routine
- [ ] Calculation Logic is front-loaded immediately after the title, covers material whole-program calculations/assignments, and links every row to routine-level or ledger evidence
- [ ] Logic Decomposition Ledger preserves calculations, constants, branch priority, loops, and CASE/SELECT behavior
- [ ] Routine / Window Data Flow shows input variables, transformation logic, output variables, side effects, source lines, and evidence
- [ ] Data Touch Map captures critical carriers, keys, payloads, and state impacts
- [ ] Key File & Field Logic preserves `FIELD_NAME` (business meaning) and `VARIABLE_NAME` (business meaning) [direction] for every resolvable key field or variable
- [ ] File I/O Key Fields preserve source identifiers plus business meaning, and Purpose describes file access behavior
- [ ] Reference-pack lookups, if used, cite pack ID/version/file/row and do not override source-backed behavior
- [ ] File I/O field mutation matrix names which files and fields are written, updated, deleted, or skipped
- [ ] External and dynamic calls include caller routine, source lines, parameters, resolution status, purpose, and evidence
- [ ] Validation Logic is front-loaded immediately after Calculation Logic, has one row per message/status/return/response/generic outcome with reverse trigger chains / Routine Logic links, and Error Handling closes each exception path through return, rollback, skip, log, or downstream impact
- [ ] Exception Handling is front-loaded immediately after Validation Logic, covers every observed business/parameter/I/O/external/system/generic exception path, and links each row to closure evidence
- [ ] Message Inventory is front-loaded immediately after Exception Handling, has one summary row per explicit message/code/literal, links message-dense details to `message-inventory.md` / `message-inventory.yaml`, and preserves description source, carrier/destination, trigger/handler, related Validation/Exception row, and evidence status in the summary or sidecar
- [ ] Inferred and unresolved meanings, calls, fields, and error codes are explicitly marked
- [ ] Code identifiers remain intact and readable; long lists use intentional line breaks
- [ ] Redundancy candidates are conservative and do not remove hidden rules
- [ ] TBDs are non-blocking or properly flagged for follow-up
- [ ] No invented subroutines or undocumented file access
- [ ] Evidence linkage matches analysis intent: `chain_ready` references
  existing inventory items (`OBJ-*`, `EV-*`); `standalone_exploratory` uses
  source ranges/local references, marks inventory linkage as missing, and does
  not fabricate `OBJ-*` or `EV-*`
- [ ] Status field is set correctly (`draft` → `needs_sme_review` /
  `draft_exploratory` / `blocked_pending_source` → `approved` /
  `approved_with_non_blocking_tbd` / `rejected`)

**SME sign-off:**

- Reviewer: ________________
- Review Date: ________________
- Decision: approved | approved_with_non_blocking_tbd | rejected
- Notes: [free-form]
```

---

## Evidence Strength Taxonomy

Every claim (entry point, logic rule, field lineage, field mutation,
control flow step, file I/O, external call, error handling, redundancy
candidate) must carry one evidence strength:

| Strength | Meaning | Example |
| --- | --- | --- |
| `confirmed_from_code` | Source code directly shows this (visible in procedure spec, F-spec, I/O statement, MONITOR block) | RPGLE procedure header declares parameter types |
| `medium_confidence` | Inferred from usage pattern but not explicitly declared (e.g., indicator logic implies condition) | A field is assigned only in one IF branch → likely purpose of the field |
| `strongly_inferred` | Multiple evidence points support this (call site + default behavior) | External call always preceded by data validation → likely required validation |
| `needs_sme_review` | Evidence present but interpretation ambiguous (multiple possible meanings) | Error code returned but undocumented; could mean multiple things |
| `missing` | Evidence required but not available (DDS missing, source incomplete) | File accessed but DDS not in inventory → TBD |

## Evidence Source / Resolution Labels

Use these labels consistently when marking call targets, field meanings,
file roles, routine/window data flow, external call parameters, dynamic
calls, and error-code meanings:

| Label | Use When |
| --- | --- |
| `confirmed` | Evidence directly proves the conclusion. |
| `inferred` | Evidence suggests the conclusion but does not fully prove it. |
| `unresolved` | Evidence is insufficient; reviewer follow-up is required. |
| `flow_header` | Source-level flow header contributes evidence. |
| `derived_code` | Source statements or code-derived analysis contributes evidence. |
| `flow_header + derived_code` | Header and code-derived evidence agree. |
| `header_only` | Only the flow header supports the item; create a TBD if behavior matters. |
| `derived_code_only` | Only code-derived evidence supports the item. |
| `partially_resolved` | Some target/meaning details are known, but material details remain open. |
| `dynamic_unresolved` | Dynamic target is built at runtime and concrete target is not resolved. |

## Rendering Requirements

Generated `program-analysis.md` artifacts must remain readable in
Markdown and HTML export:

- Wrap code identifiers in backticks.
- Do not allow file names, field names, program names, routine names, or
  variable names to be split vertically or across arbitrary line breaks.
- Use one identifier per line, `<br>`, or a short detail list for long
  file/field/call lists.
- Prefer summary tables plus detail bullets when a table becomes too
  wide.
- Do not put long call lists, evidence lists, or field lists in one
  bullet.
- Purpose text must be allowed to wrap naturally; source identifiers
  must remain visually intact.

---

## Review Status Values

- **draft_exploratory** — standalone source-grounded analysis for inspection,
  skill testing, or early understanding. It is complete enough to review the
  analyzer output, but `Downstream Readiness` must remain `not_chain_ready`
  until inventory/object/evidence linkage is added.
- **draft** — initial analysis, ready for SME review
- **needs_sme_review** — waiting for SME validation (has blocking TBDs or ambiguities)
- **blocked_pending_source** — source incomplete or unavailable, or a
  `chain_ready` run is missing required inventory/object/evidence linkage.
  Analyzer stops instead of guessing. Missing inventory alone does not block
  `standalone_exploratory`; it marks downstream readiness as `not_chain_ready`.
- **approved** — SME confirmed all behaviors and resolved TBDs
- **approved_with_non_blocking_tbd** — SME approved despite non-blocking TBDs (e.g., undocumented call without impact on this program's behavior)
- **rejected** — SME found serious errors or inconsistencies
