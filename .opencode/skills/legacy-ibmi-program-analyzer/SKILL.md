---
name: legacy-ibmi-program-analyzer
description: Analyze individual IBM i programs (RPGLE, CLLE, COBOL) to extract control flow, file I/O, external calls, and error handling with evidence backing. Use when diving deep into one program's behavior from an approved inventory, or in standalone exploratory mode when the user only wants to inspect a skill output before BRD/spec chain readiness. Layer 1 (platform-specific) skill of the Legacy Spec Factory reverse chain.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Program Analyzer

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Creates an evidence-backed technical analysis of one RPGLE, CLLE, or COBOL program. |
| Input | One approved source program; for chain-ready output, its `OBJ-*` inventory entry; referenced DDS/copybooks; optional runtime, SME notes, and project reference packs for message catalogs, control files, or data dictionaries. |
| Output | `program-analysis-<OBJ-ID>.md` for chain-ready runs, or standalone `program-analysis.md` for exploratory inspection, covering call map, control flow, file I/O, external calls, and error handling. |
| Core prompt strategy | Extract concrete code behavior first, enrich field/message meanings from approved reference packs, tag every inference, avoid business-rule invention, and separate exploratory analysis warnings from downstream blocking gates. |
| Upstream skill | `legacy-ibmi-inventory` for chain-ready output; none required for standalone exploratory output. |
| Downstream consumer | `legacy-ibmi-flow-analyzer`, `legacy-ibmi-module-analyzer`, data-model analysis, batch digest, and spec synthesis. |
| Validation standard | Chain-ready output resolves Program ID in approved inventory; standalone exploratory output marks inventory linkage missing and uses source ranges/local evidence without claiming downstream readiness. |
| Known risk | Inferring business intent from field or routine names without SME or runtime confirmation. |
| Practical example | Analyze `ORDENTR` RPGLE to document subroutines, PF/LF I/O, display-file indicators, and calls to credit-check programs. |

## Purpose

Create a detailed analysis of one IBM i program (RPGLE, CLLE, or COBOL)
documenting its RDi-style program call map, control flow, file I/O
operations, external calls, and error handling. This skill does not infer
business rules and does not generate modernization code. It produces
evidence-backed analysis ready for SME validation and downstream spec
generation.

This skill supports two intent modes:

- **`standalone_exploratory`** — user wants to inspect one program or see the
  skill's output shape. Missing inventory/OBJ/EV linkage is a warning and a
  downstream-readiness blocker, not a current-analysis block. Produce the
  analysis from the supplied source, mark `status: draft_exploratory`, and
  state clearly that the artifact is not eligible for flow/module/BRD/spec
  handoff until inventory linkage is added.
- **`chain_ready`** — user wants an artifact that can feed
  `legacy-ibmi-flow-analyzer`, module analysis, BRD, or spec work. Require an
  approved inventory entry, canonical `OBJ-*`, evidence IDs, and normal Step
  Contract validation.

## Inputs

Accept:

- One RPGLE, CLLE, or COBOL source file (the program to analyze)
- Optional: DDS copybook definitions (DSPF, PRTF, PF, LF) referenced by the program
- Optional: SME notes on entry points, quirks, or runtime behavior
- Optional: project/company reference packs containing message catalogs,
  control files, code tables, data dictionaries, or dictionary-center mappings.
  Original files may be Markdown, CSV, Excel, Word, PDF, or normalized
  document-intake outputs. Preferred paths:
  `00_reference_packs/<PACK-SLUG>/reference-pack-index.yaml` or
  `00_context_packages/<MODULE-SLUG>/field-dictionary-context.md`.
- **Required for `chain_ready`:** Program must be referenced in an approved
  `01_inventory/inventory.yaml` via program ID (`OBJ-*`)
- **Allowed for `standalone_exploratory`:** inventory may be absent when the
  user is only evaluating a skill output or analyzing a program locally. Do not
  fabricate `OBJ-*` or `EV-*`; use source ranges/local source references and
  mark `inventory_linkage: missing`.

Stop and require clarification if:

- Program source is missing or incomplete (create a `blocked_pending_source`
  artifact or TBD routing note instead of guessing)
- Program is marked `blocked` in the inventory
- Program ID (`OBJ-*`) cannot be located in inventory **and** the user asked
  for chain-ready/downstream output
- Source contains raw, unredacted production data (require redaction review per `../../docs/data-collection-and-redaction.md`)

## Output Contract

Produce:

- `program-analysis-<OBJ-ID>.md` per program for chain-ready runs (one file
  per analysis session)
- `program-analysis.md` for standalone exploratory inspection when no
  inventory-backed `OBJ-*` exists yet

Use:

- `templates/program-analysis.md` as starting point
- `references/output-contract.md` for field definitions and evidence tagging
- `references/large-program-analysis.md` for large-program, segmented, and context-window-safe analysis
- `scripts/index_rpg_source.py` as the deterministic source-index helper when
  local file access is available:
  - Windows: try `py -3 scripts\index-rpg-source.py <source> --program <NAME> --out-dir <DIR>`, fall back to `python` if `py -3` is unavailable
  - macOS/Linux: `python3 scripts/index-rpg-source.py <source> --program <NAME> --out-dir <DIR>`
  If all launchers fail, stop and report: **"Python runtime unavailable"**.
  Do not configure PATH, install Python, or create a virtual environment.
  Apply the same launcher order to all temporary consistency checks, YAML
  readability checks, Markdown sanity checks, and one-off helper scripts run
  during this skill.
- `references/control-flow-patterns.md` for language-specific pattern recognition
- `references/error-handling-taxonomy.md` for error detection
- `references/evidence-tagging.md` for evidence strength levels and tagging methodology
- `references/reference-pack-lookup.md` for using project/company Markdown
  / CSV / Excel / Word / PDF control files, message catalogs, and data
  dictionaries
- `templates/evidence-tags.md` as a quick reference card for inline evidence annotation
- `templates/reference-pack-index.yaml` as the recommended index for
  project/company Markdown lookup packs

Follow:

- `../../docs/id-conventions.md` for stable IDs (OBJ-*, EV-*, TBD-*)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence strength labels
- `../../docs/input-readiness-rubric.md` for input readiness scoring

Examples:

- `examples/simple-crud-rpgle/` — straightforward CRUD program, high-confidence analysis
- `examples/complex-batch-job/` — multi-subroutine batch job, moderate complexity
- `examples/incomplete-source-negative/` — negative case: missing source, TBD handling

## Step Contract

This skill is one step in the Legacy Spec Factory reverse chain. It conforms
to the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for the full
field-level rules. The summary below is normative for this skill.

### Input

- **Required**: one RPGLE / CLLE / COBOL source program.
- **Required for chain-ready output**: the program's `OBJ-*` ID located in an
  `approved` (or `approved_with_non_blocking_tbd`)
  `01_inventory/inventory.yaml`.
- **Optional**: DDS copybook source (DSPF, PRTF, PF, LF) for files the
  program touches; SME notes on entry points, quirks, or runtime behavior;
  approved project reference packs for message descriptions, control-file
  values, field meanings, and `standard_field_id` mappings. For raw
  Excel/Word/PDF/image inputs, prefer `legacy-document-evidence-intake`
  normalized Markdown/CSV/text outputs with evidence coordinates.
- **Input readiness scoring**:
  - `0-5 blocked`: program source missing/incomplete, inventory status blocked
    for a chain-ready request, or evidence authorization unresolved.
  - `6 minimum_pass`: one current program source is present. If approved
    inventory linkage is absent, proceed only as `standalone_exploratory`.
  - `7-8 usable`: referenced DDS/copybooks and object metadata are available
    for most file and display/report interactions.
  - `9-10 strong`: runtime logs, screen/report samples, SME notes, known
    edge cases, and parameter/interface notes are also supplied.
  - Missing runtime samples or SME notes does not block static program
    analysis; it limits confidence for business meaning and exception realism.
- **Readiness checks**: source is current production (tier 1) rather than
  archival when known; evidence authorization is resolved. For `chain_ready`,
  Inventory Completeness Gate passes and the program is not marked `blocked`
  in inventory.
- **Stop conditions**: source missing or incomplete; program marked `blocked`
  in inventory for a chain-ready request; `OBJ-*` not found in inventory for a
  chain-ready request; raw unredacted production data present. Missing
  inventory alone does not stop `standalone_exploratory` analysis.

### Execution

- **Procedure**: see the Workflow section below (11 ordered steps).
- **Large-program mode**: when source is greater than 10,000 lines,
  contains more than 25 routines, contains more than 20 external calls,
  or cannot safely fit in context with evidence windows, use
  `references/large-program-analysis.md`. When the source file is accessible
  on disk, first run `scripts/index_rpg_source.py` (or the root
  `scripts/index-rpg-source.py` wrapper) to produce `source-index.yaml`,
  `program-analysis-summary.yaml`, `routine-index.md`,
  `all-routine-coverage-ledger.md`, `deep-read-plan.md`,
  `routine-logic-details.md`, `routine-logic-details.yaml`,
  `message-inventory.md`, `message-inventory.yaml`,
  `file-io-inventory.md`, `file-io-inventory.yaml`,
  `field-mutation-matrix.md`, `field-mutation-matrix.yaml`,
  `sql-inventory.md`, and `sql-inventory.yaml` for compact sidecar
  review. Windows: try `py -3`, fall back to `python`; macOS/Linux: use
  `python3`. If all launchers fail, stop and report:
  **"Python runtime unavailable"**. Do not configure PATH, install
  Python, or create a virtual environment.
  Apply the same launcher order to temporary consistency checks, YAML
  readability checks, Markdown sanity checks, and one-off helper scripts run
  during this skill.
  These are
  pre-analysis structure artifacts, not the final program analysis. Do not
  produce whole-program business narrative until the source index, routine
  cards, Program Call Map, Data Touch Map, and coverage ledger exist.
- **Allowed inference**: control flow extracted from EXSR/CALL/PERFORM;
  calculations and branch logic from source statements; file I/O from
  F-spec and I/O statements; field lineage from visible assignments,
  DDS/copybooks, and parameter lists; error paths from MONITOR/
  MONMSG/ON-ERROR or explicit return/status checks; pattern-based
  labeling tagged `strongly_inferred` or `medium_confidence` with
  explicit notes.
- **Forbidden assumptions**: inventing subroutines, file access beyond
  what I/O statements show, business meaning from field names, external
  call parameters absent from source or copybooks, error codes not
  explicitly caught or returned; reading non-redacted evidence. Reference-pack
  lookup may explain an observed identifier, but it must not create a behavior
  claim that is absent from source, runtime evidence, or SME notes.
- **TBD handling**: missing DDS → `TBD: pending_source`; undefined
  subroutine reference → `TBD: pending_source`; unclear error path →
  `TBD: pending_sme_judgment`; non-blocking gaps tagged `non_blocking`.

### Output

- **Canonical artifact**: `program-analysis-<OBJ-ID>.md` for chain-ready runs
  or `program-analysis.md` for standalone exploratory inspection (one per
  program).
- **Required sections**: `Calculation Logic`, `Validation Logic`,
  `Exception Handling`, `Message Inventory`, `Metadata`, `Analysis Coverage & Scope`,
  `Program Call Map`, `Routine Cards`, `Routine Logic Details`,
  `Deep Read Windows`, `Entry Points & Parameters`,
  `Object Dependencies`,
  `Logic Decomposition Ledger`, `Data Touch Map`,
  `Key File & Field Logic`, `Control Flow`, `File I/O`,
  `External Calls`, `Error Handling`, `Redundancy Candidate Notes`,
  `TBDs & Blocking Status`, `Review Checklist`.
- **Required IDs**: `chain_ready` output reuses `OBJ-*` and `EV-*` from
  inventory/evidence manifest. `standalone_exploratory` output must not
  fabricate `OBJ-*` or `EV-*`; it uses source ranges/local source references
  and records `inventory_linkage: missing`. Both modes may mint program-local
  `BEH-*`, `EX-*`, and `TBD-*`. Does not mint `BR-*`, `CAP-*`, `DEC-*`.
- **Reference pack metadata**: when message catalogs, control files, code
  tables, or data dictionaries are used, record pack path, pack ID/version,
  authorization status, and lookup coverage in Metadata.
- **Handoff status**: `status: draft` until SME review; `approved` or
  `approved_with_non_blocking_tbd` is required before
  `legacy-ibmi-flow-analyzer` runs against the chain that includes this
  program. `status: draft_exploratory` is never eligible for downstream
  flow/module/BRD/spec use without rerun or linkage update.

### Validation

- **Mechanical**: in `chain_ready`, every non-trivial behavior has ≥1 `EV-*`
  link and every call/object reference resolves against inventory. In
  `standalone_exploratory`, every non-trivial behavior has source-range/local
  evidence and unresolved inventory/object/evidence mappings are listed as
  downstream-readiness gaps, not current-analysis blockers. In both modes,
  every TBD has a blocking-status tag and required sections are present.
  Reference-pack facts must cite the pack/file/row or anchor used.
- **AI semantic**: behaviors are consistent with the linked source lines;
  no invented subroutines, fields, files, field mutations, message IDs,
  or error codes; evidence strength not overstated (no
  `weakly_inferred` posing as `confirmed_from_code`); front-loaded
  Calculation Logic, Validation Logic, Exception Handling, and Message
  Inventory reconcile against routine-level evidence and ledgers; flow header (if
  present) reconciled against the code-derived program call map. Dictionary or
  control-file meanings enrich observed identifiers; they do not override code
  behavior. Contradictions become TBDs.
- **Report quality**: Program Call Map uses compact `Visual Overview`
  plus auditable `Call Evidence`; key fields and variables preserve
  `FIELD_NAME` (business meaning) and `VARIABLE_NAME` (business meaning)
  [direction]; external/dynamic calls and error codes carry resolution
  status; unresolved items are centralized in TBDs / Open Items.
- **SME / human approval**: SME signs entry points, parameter contracts,
  file I/O semantics, external interface contracts, and error handling
  realism. Required when the program affects money, inventory,
  compliance, or customer status; recommended otherwise.
- **Blocking conditions**: any `BEH-*` without source evidence; any invented
  IBM i fact; any unresolved `pending_source` TBD on a section that is
  load-bearing for the next flow analysis; SME absence when SME is required by
  the program's risk class. Missing inventory blocks only `chain_ready` /
  downstream promotion, not standalone exploration.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with
status `pass`, `pass_with_warnings`, or `blocked` when reporting upward
to the orchestrator.

## Workflow

1. **Size & Structure Preflight**
   - Count approximate source lines, routine definitions, external calls,
     and object dependencies before writing business summary prose
   - If local source file access is available, run:
     - Windows: try `py -3 scripts\index-rpg-source.py <source-file> --program <PROGRAM> --out-dir <analysis-dir>`, fall back to `python` if `py -3` is unavailable
     - macOS/Linux: `python3 scripts/index-rpg-source.py <source-file> --program <PROGRAM> --out-dir <analysis-dir>`
     If all launchers fail, stop and report: **"Python runtime unavailable"**.
     Do not configure PATH, install Python, or create a virtual environment.
     Use the same launcher order for all temporary consistency checks, YAML
     readability checks, Markdown sanity checks, and one-off helper scripts.
   - Use `source-index.yaml`, `program-analysis-summary.yaml`,
     `routine-index.md`, `all-routine-coverage-ledger.md`,
     `deep-read-plan.md`, `routine-logic-details.md`,
     `routine-logic-details.yaml`, `message-inventory.md`,
     `message-inventory.yaml`, `file-io-inventory.md`,
     `file-io-inventory.yaml`, `field-mutation-matrix.md`,
     `field-mutation-matrix.yaml`, `sql-inventory.md`, and
     `sql-inventory.yaml` as the deterministic pre-analysis index
   - For SQLRPGLE and free-format RPGLE, use statement-level indexing for
     `DCL-PI`, `DCL-PR`, `DCL-DS`, `DCL-S`, `DCL-PROC`, procedure calls,
     assignments, `EXEC SQL` blocks, host variables, `SQLCODE`, and
     `SQLSTATE`. Do not split multi-line SQL statements or free-format
     calculation chains into fixed line chunks.
   - Select analysis mode: `standard`, `segmented`, or `large_program`
   - For `segmented` or `large_program`, build the structure index before
     any business summary prose
   - Create Analysis Coverage & Scope and initialize the coverage ledger
   - Prevent claims of complete understanding until coverage supports
     them with indexed routines, deep-read windows, resolved call/data
     edges, and explicit gaps

2. **Select Program & Resolve Analysis Intent**
   - Determine whether the user wants `standalone_exploratory` or
     `chain_ready` output. If the user says they only want to inspect/analyze a
     program, see skill output, run a test, or are not producing BRD/spec,
     default to `standalone_exploratory`.
   - Accept program ID (OBJ-*) from approved `01_inventory/inventory.yaml` when available
   - Confirm program name, type (RPGLE / CLLE / COBOL), and library
   - Stop if program is marked `blocked` or inventory is not approved for a
     `chain_ready` request
   - If inventory is missing in `standalone_exploratory`, continue analysis,
     mark `inventory_linkage: missing`, and create a downstream-readiness gap
     instead of `blocked_pending_source`
   - Document source location and collection date

2a. **Load Approved Reference Packs (Optional)**
   - If the user, inventory, or context package provides company control files,
     message catalogs, code tables, data dictionaries, or dictionary-center
     mappings, resolve them through
     `references/reference-pack-lookup.md`.
   - Prefer `00_reference_packs/<PACK-SLUG>/reference-pack-index.yaml` for
     enterprise/shared packs and
     `00_context_packages/<MODULE-SLUG>/field-dictionary-context.md` for
     module-specific dictionary context.
   - Confirm authorization status is `approved_for_analysis`,
     `internal_reference`, or `synthetic` before using content. If status is
     unknown, do not silently consume the files; ask for approval or create a
     reference-pack TBD.
   - For Excel, Word, PDF, image, or scanned inputs, prefer normalized
     Markdown/CSV/text outputs and coordinates from
     `legacy-document-evidence-intake`. If only raw files are supplied and
     they are not directly readable in the current runtime, route to
     `legacy-document-evidence-intake` or create a reference-pack readability
     TBD. Do not treat conversion/tooling failure as evidence that the lookup
     entry does not exist.
   - Build a lookup index from exact identifiers only: message ID, status code,
     return code, SQLSTATE, CPF/MCH/RNX/CPD ID, file name, record format,
     field name, alias, `standard_field_id`, control-file field, and
     control-file value.
   - Record the pack path, pack ID/version, owner, source format, normalized
     output path, document-intake manifest when available, and lookup coverage
     in Metadata. Reference packs are explanation evidence for observed
     identifiers; they do not prove that a branch, call, file mutation, or
     exception path exists.

3. **Extract Entry Points & Parameters**
   - Identify main entry point (program parameter list, return value or status code)
   - Identify callable sub-procedures:
     - RPGLE procedures: Fixed-form `P ... B` / `P ... E` or free-form `dcl-proc` / `end-proc`; both callable via CALL statement
     - RPGLE subroutines: `BEGSR` / `ENDSR` blocks (internal subroutines, callable only from within same program)
     - CLLE: `SUBR` label blocks and `CALLSUBR` invocations (internal subroutines); external procedures via CALL
     - COBOL: ENTRY statements, PERFORM … UNTIL / VARYING
   - Document parameter types, expected ranges, and direction (input/output/both)
   - Tag with evidence: `confirmed_from_code` (from source headers or RPGLE specifications)
   - Create TBD if parameter contract is undocumented or unclear

4. **Trace Main Control Flow & Logic Ledger**
   - Document procedure call sequence (what calls what, in what order)
   - For every load-bearing mainline segment, subroutine, procedure, or
     paragraph, add **Routine Logic Details**. Load-bearing means the routine
     performs field calculation, validation, downstream-affecting branching,
     file mutation, external handoff, error/status assignment, display/report
     output, or queue/message interaction.
   - For routine-dense programs, keep `program-analysis.md` compact:
     - `routine_count <= 25`: full Routine Logic Details may live in the main
       analysis.
     - `routine_count > 25`: the main analysis must contain a Routine Logic
       Details summary table with `RLOG-<PROGRAM>-NNN` detail IDs, while full
       details live in `routine-logic-details.md` and
       `routine-logic-details.yaml`.
     - `routine_count > 80` or source lines > 10,000: split human-authored
       semantic detail into `routine-logic-details/part-*.md` files by
       mainline/dispatch, state-changing routines, validation/message routines,
       external boundaries, and indexed utilities.
   - In Routine Logic Details, explain each routine's execution trigger,
     step-by-step logic, field calculations/assignments, branch outcomes,
     exits, and evidence. Do not summarize a routine as "validation logic" or
     "amount calculation" without target fields, operands, expressions,
     branch guards, precision/conversion notes, and business effect.
   - Within each Routine Logic Details subsection, add **Conditioned
     calculation blocks** for every guard-scoped calculation chain that affects
     money, percentage, quantity, status, return value, message/error code,
     persisted field, display/report field, queue payload, or downstream
     branch. In fixed-format RPG this includes conditioning indicators,
     named/numbered condition groups, result indicators, `IFxx` / `ELSE` /
     `ENDIF`, `CASxx`, `DO` scopes, and operation-level indicators. A block
     such as "Condition 5" must be analyzed as its own source-backed unit: list
     the guard, all guarded statements in order, each target assignment,
     intermediate variables, final output/error effect, and source line range.
     Do not hide these chains in a generic branch outcome or only in the
     Logic Decomposition Ledger.
   - Within each Routine Logic Details subsection, add **Outcome reverse
     traces** for every material message ID, status code, return code,
     response value, indicator-driven outcome, or error field produced by the
     routine. Start from the visible outcome (for example `UCC1852` or
     `W0BUR`), walk backwards to the exact branch/guard that sets or emits it,
     then continue backwards through the conditioned calculation block,
     comparison threshold, intermediate variables, and source operands/carriers
     that make the outcome true. A result such as `UCC1852` must not be left as
     "warning/reject condition" if the source shows a trigger chain such as
     `CAACOS/CAACCM/CATTHD/CATCAM/CAACLT -> WOOVAM -> WOACLT -> WOOVPE ->
     BBLSOP -> UCC1852`.
   - Within each Routine Logic Details subsection, connect calculated or
     assigned fields back to data carriers: source file/parameter/queue/screen
     field, intermediate work variables, output or persisted carrier, and the
     related Field Lineage / Field Mutation Matrix row when one exists.
   - Within each Routine Logic Details subsection, close routine-local
     exceptions: trigger, error/status/message fields, handling action,
     downstream skip/rollback/output, Validation Logic row, and evidence.
     If no exception path is observed for a routine, state `none observed`
     rather than leaving the closure implicit.
   - Identify conditional branching:
     - RPGLE: IF, SELECT, indicator-driven branching
     - CLLE: IF, ELSE, GOTO
     - COBOL: IF, EVALUATE, PERFORM … UNTIL
   - Identify loops and exit conditions (DO, DOWHILE, PERFORM, VARYING)
   - Build the **Logic Decomposition Ledger** for rules that must not be
     compressed into generic prose:
     - arithmetic operations (`ADD`, `SUB`, `MULT`, `DIV`, `EVAL`
       expressions) with source operands, result fields, and rounding or
       precision behavior
     - string construction (`CAT`, `MOVE`, substring operations) where it
       creates business identifiers, keys, or external payload fields
     - constants and literals used in limits, status values, rates,
       return codes, message IDs, flags, or branch decisions
     - single-condition, compound-condition, nested-condition, `SELECT` /
       `CASE`, and loop rules with explicit branch priority
   - Preserve condition order and nesting when it changes behavior. Do
     not flatten mutually exclusive tiers or fallback branches into
     unrelated bullet points.
   - Build a front-loaded **Calculation Logic** section immediately after
     the title and before Metadata. It must summarize the whole program's
     material calculation and assignment chains for IT SME first-read
     review, including arithmetic, derived amounts, status/result
     assignments, key construction, message/status carriers, outbound
     payload fields, and persisted field updates. Every row must link back
     to Routine Logic Details, a conditioned calculation block, the Logic
     Decomposition Ledger, Key File & Field Logic, or a Field Mutation row.
     Do not leave a critical calculation only in a later routine-local
     subsection or ledger.
   - Add **Routine / Window Data Flow** for every load-bearing routine or
     deep-read window: purpose, input variables, transformation logic,
     output variables, side effects, source lines, and evidence. Use
     `VARIABLE_NAME` (business meaning) [direction], and mark inferred or
     unresolved meanings explicitly.
   - Document handled vs. unhandled paths
   - Tag each non-trivial control structure: `confirmed_from_code` or `medium_confidence` if inferred
   - Create TBD for unclear program flow (missing subroutines, undefined labels)

5. **Build Program Call Map**
   - Treat the call map as the default entry view for every program,
     regardless of size. It should resemble an IBM RDi call-hierarchy
     view: routines and external boundaries connected by call edges,
     not a statement-level flowchart.
   - **First, look for a source-level flow header** at the top of the program. Many IBM i shops embed an ASCII tree comment like:
     ```
     Main line                Main flow control
     |-- SR990                First time initialization
     |-- SR100                Card validation
     |    |-- SR110           Currency conversion
     |    |    |-- SR111      Convert transaction amount
     ```
     If present, use it as documented intent and navigation evidence
     (tier 3 evidence per `../../docs/code-as-ground-truth.md`) and render
     the `Visual Overview` as a normalized fenced `text` hierarchy using
     `|--` branches. Preserve useful author labels, but reconcile the tree
     against actual EXSR/CALL statements before presenting it as the program
     call map. The header is **not authoritative** when it disagrees with
     actual EXSR/CALL statements.
   - **Independently derive a program call map from code** by scanning
     for EXSR / CALLP / CALL / PERFORM / CALLPRC statements and
     BEGSR-ENDSR / BEGPR-ENDPR / paragraph definitions.
   - **Compare header vs. code-derived graph:**
     - If they match → tag `confirmed_from_code` (with source-level flow header as evidence)
     - If header exists but code differs → create TBD (comment drift, dead code, or missing subroutine)
     - If no header exists → use code-derived graph, tag `confirmed_from_code` (from EXSR/CALL/PERFORM statements)
   - Produce the required views (see `references/output-contract.md`):
     - **Visual overview** (RDi-style fenced `text` hierarchy using
       `|--` branches; compact by design but detailed enough to orient
       SMEs; not Mermaid)
     - **Node inventory** (mainline, internal routines, procedures, external programs, APIs, queues, services)
     - **Call Evidence** (caller, callee, call type, condition, source
       lines, evidence source, and resolution status)
     - **Reverse caller index** (for each node, who calls it)
   - Use the wording `Evidence basis: source-level flow header + derived
     call analysis` when header and code-derived evidence are both used.
   - Treat dynamic calls as unresolved until a concrete target is proven
     from source, runtime evidence, inventory, or SME notes. Capture the
     target variable and assignment lines when available.
   - Identify hub/common candidates and orphaned routines. A hub/common
     label is structural only; do not promote it into a business service
     or modernization boundary without flow/module evidence and SME
     confirmation.

6. **List Object Dependencies (flat reference inventory)**
   - Match the shop's `F5-OBJREF TREE` output format: enumerate **every external object** referenced by the program, regardless of how it is used.
   - Object types to cover:
     - Files: PF (physical), LF (logical), DSPF (display), PRTF (printer)
     - Data: \*DTAARA (data area), \*DTAQ (data queue), \*MSGF (message file)
     - Programs: \*PGM (called program), \*SRVPGM (bound service program)
     - Source-level: Copybooks / `/COPY` directives, data-structure includes
   - Capture columns: object name, type, version (if shop tracks one), description, inventory ID (OBJ-\*), evidence
   - Cross-reference each entry against `01_inventory/inventory.yaml`:
     - If a matching OBJ-\* exists → link it
     - If not → create TBD: inventory gap (the inventory missed this object)
   - This section is the **flat parent list**; deeper per-object analysis happens in steps 7 (Data Touch Map + File I/O) and 8 (External Calls).
   - Tag: `confirmed_from_code` (visible in F-spec, D-spec, /COPY, or CALL statement)

7. **Document Data Touch Map, Key Fields & File I/O**
   - Build a program-local **Data Touch Map** before the detailed File
     I/O table. This is the data companion to the Program Call Map: it
     shows which routines touch which data carriers and where state
     enters, changes, leaves, or persists.
   - Track object / record / critical-field level movement. Do **not**
     enumerate every temporary RPG work variable.
   - Critical fields include money/amount fields, account/customer IDs,
     inventory quantities, approval/decline decisions, posting flags,
     status fields, return codes, error codes, audit IDs, and external
     message payload fields.
   - For every data carrier, capture:
     - carrier/object (PF, LF, DSPF, PRTF, `*DTAARA`, `*DTAQ`, `*MSGQ`,
       CALL parameter list, copybook/data structure, IFS file)
     - routine/procedure touching it
     - operation (read, write, update, delete, send, receive, parameter
       in/out/inout)
     - key/payload fields
     - state impact (`read-only`, `creates`, `updates`, `deletes`,
       `async send`, `async receive`, `external handoff`)
     - evidence and TBDs for unclear payload structure or direction
   - Build the **Key File & Field Logic** section:
     - classify each key file as driver, lookup/reference, state update,
       transaction/detail insert, audit/log, screen/report, queue/message,
       or parameter/data-structure carrier
     - classify each key field by role: access key, input, derived value,
       calculation operand/result, branch condition, status/flag,
       return/error code, message ID, external parameter, persisted field,
       or audit/output field
     - show field lineage for critical fields as
       `physical/source field -> alias/data structure -> work variable ->
       calculation/condition -> write-back alias -> persisted field`
     - preserve source identifiers and business meaning together:
       `FIELD_NAME` (business meaning). If one side is unresolved, write
       `field unresolved` (business meaning) or `FIELD_NAME` (meaning
       unresolved); mark inferred meanings inline.
     - preserve variable flow as `VARIABLE_NAME` (business meaning)
       [input/output/input-output/local/control]
     - when an approved reference pack maps a field, include
       `standard_field_id`, reference-pack file/row, dictionary version, and
       owner/steward when available
     - if a control-file/code-table lookup gives a value meaning, cite it as
       reference-pack evidence while keeping the condition and assignment
       source-backed
     - if dictionary/control-file meaning conflicts with code behavior, keep
       both facts visible and create a contradiction TBD instead of selecting
       one silently
     - create TBDs when DDS/copybook metadata is missing, physical-field
       mapping is unclear, or a variable participates in a critical path
       but its source cannot be proven
   - For each file from step 6 (PF / LF / DSPF / PRTF), classify operations:
     - Sequential read: READ (next record), READP / READPE (read previous)
     - Random read: SETLL (set lower limit), READE (read equal), CHAIN (random access)
     - Write operations: WRITE (add new record), UPDATE (modify record), DELETE
     - Display file: EXFMT (format + read interaction with DSPF for menus, input screens)
     - Embedded SQL / SQLRPGLE: EXEC SQL blocks, cursor operations, SQLCODE / SQLSTATE error handling
     - Note key fields used in each operation (e.g., CHAIN on CUSTID)
   - For every WRITE / UPDATE / DELETE / SQL mutation, produce a
     field-level mutation row that names:
     - record format and access key
     - branch condition that permits the mutation
     - fields assigned immediately before the mutation
     - source value, literal, expression, or copied field used for each
       persisted field
     - indicators, `%FOUND`, `%ERROR`, `SQLCODE`, `SQLSTATE`, or return
       codes checked before and after the mutation
     - a File Access Summary purpose using an action verb that explains
       why the file is accessed; do not use Purpose as a substitute for
       field descriptions
   - For file-I/O-dense or SQLRPGLE programs, keep the main `File I/O`
     section as a SME-readable summary. Store complete observed I/O evidence
     in `file-io-inventory.md` / `file-io-inventory.yaml`, persisted native
     and SQL mutations in `field-mutation-matrix.md` /
     `field-mutation-matrix.yaml`, and embedded SQL details in
     `sql-inventory.md` / `sql-inventory.yaml`. Link main-table rows to
     stable `FIO-*`, `MUT-*`, and `SQL-*` detail IDs instead of expanding
     every operation inline.
   - Reference file definitions from inventory via evidence ID (EV-\*)
   - Tag evidence: `confirmed_from_code` (from file specifications or I/O statements)
   - Create TBD if DDS is missing, key field unclear, or SQL schema is not documented

8. **Identify External Calls**
   - List all external program calls:
     - RPGLE: CALL, CALLP (procedure call)
     - CLLE: CALL, CALLPRC
     - COBOL: CALL, CICS, MQ, REST
   - List external service program calls (binding)
   - List external interfaces: IFS, HTTP, message queues, data queues
   - Document parameter contract if visible in source (call statement, copybook)
   - For dynamic calls, document the target variable, source lines where
     the target is assigned, parameters, resolution status (`resolved`,
     `partially_resolved`, `dynamic_unresolved`, `inferred`, `confirmed`),
     and any evidence gap.
   - Tag: `confirmed_from_code` (source statement visible) or `needs_sme_review` (undocumented)
   - Create TBD if external interface is unknown or network-dependent

9. **Document Error Handling**
   - List monitored errors:
     - RPGLE: MONITOR / ON-ERROR block, escape messages
     - CLLE: MONMSG (monitor message)
     - COBOL: ON ERROR, error flag checking
   - Document error codes and recovery paths (retry, log, return error)
   - Document logged errors or message writes (DSPLY, message queue, spool)
   - Document unhandled exceptions (crash, abort)
   - Build an **Exception Closure Ledger** that covers every observed
     business, parameter, and system I/O exception path. Each row must
     include trigger condition, message ID / error code / return code,
     detection mechanism, fields set, handling action (`RETURN`, `GOTO`,
     rollback, skip write, log, send message, continue), and downstream
     impact.
   - Build a front-loaded **Validation Logic** section immediately after
     Calculation Logic and before Exception Handling. It must list every
     validation, status, response, return-code, message, indicator-driven
     outcome, and generic handler outcome observed in source or message-file
     references, including `CPF*`, `CPD*`, `MCH*`, `RNX*`, `SQL*`, shop-local
     `UCC*` / `LCC*`, and literal business error codes. Do not limit the
     inventory to shop-local message prefixes or bury it inside Error
     Handling.
   - Populate Validation Logic with Message / Status Code, Message
     Description, Validation / Error Type, Set By / Source Lines, Trigger
     Condition, Reverse Trigger Chain / Routine Logic Link, Output Carrier,
     Downstream Effect, and Evidence Status.
     Include status codes, response codes, indicator-driven error branches,
     exception/log output codes, data queue response status values, and
     message/status fields assigned during validation or file I/O failures.
   - Create one Validation Logic row per explicit message ID, status code, return
     code, response value, SQLSTATE, CPF/MCH/RNX/CPD message, user-defined
     code, or generic catch-all token. Do not group multiple message IDs into
     one row and do not replace individual descriptions with summary labels
     such as "validation messages" or "call-specific message IDs".
   - Populate Message Description from message files, approved reference-pack
     message catalogs/control files/code tables, source literals, comments,
     runtime evidence, vendor references, or SME notes. If the description is
     not available, write
     `unresolved - message description not available`, mark the row
     unresolved, and create a TBD / Open Item.
   - If literal code assignments cannot be fully traced, state
     `Validation logic unresolved:` with the concrete tracing gap.
   - For every material Validation Logic row, populate Reverse Trigger
     Chain / Routine Logic Link. This must point to the Routine Logic Details
     subsection, conditioned calculation block, outcome reverse trace, or
     source-backed TBD that explains why the code is set. Generic triggers such
     as "validation failed", "warning/reject condition", or "product/group
     control check" are not sufficient when source operands, comparisons, or
     intermediate calculations are visible.
   - When a catch-all handler is present (`MONMSG MSGID(*ANY)`, bare
     `ON-ERROR`, generic exception paragraph), mark it as generic
     coverage and still list the specific observed messages handled
     elsewhere. Do not infer specific message IDs from a generic handler.
   - Build a front-loaded **Exception Handling** section immediately after
     Validation Logic and before Message Inventory. It must summarize every
     observed business, parameter, file I/O, SQL, external-call, system, and
     generic-handler exception path with trigger, detection mechanism,
     fields/messages set, handling action, downstream effect, supporting detail
     link, and evidence. Every path must show whether it closes through return,
     rollback, skip, continue, abort, log/message output, or downstream
     suppression.
   - Build a front-loaded **Message Inventory** section immediately after
     Exception Handling and before Metadata. It must create one summary row per exact
     message ID, status value, return code, response literal, SQLSTATE,
     CPF/MCH/RNX/CPD message, operator message, or shop-local message token
     observed in the program. Preserve exact codes/literals, include the best
     available short description, occurrence count, primary routines, first
     seen/set-by location, trigger/handler summary, and detail ID.
     For message-dense, segmented, or large programs, keep the main section
     compact and store full per-occurrence detail in `message-inventory.md`
     and `message-inventory.yaml`.
     When a message/control value is found in an approved reference pack, set
     Message Source to `reference pack: <pack_id>/<file>#<row-or-anchor>` and
     still trace Emitted / Set By and Trigger / Handler from source in the
     sidecar detail.
     If no description is available, write
     `unresolved - message description not available` and create an Open Item.
   - Tag: `confirmed_from_code` (explicit error block) or `strongly_inferred` (pattern-based)
   - Create TBD if error handling is unclear or context-dependent

10. **Mark Redundancy Candidates Conservatively**
   - Do not delete or suppress code during program analysis.
   - Mark a move, assignment, temporary variable, branch, or routine as
     `candidate_redundancy: yes` only when it is not observed in any
     calculation, condition, file mutation, log/message, exception path,
     external output, parameter handoff, or persisted field lineage.
   - Use `candidate_redundancy: unknown` when downstream source,
     copybooks, DDS, or called-program behavior is missing.
   - Preserve the trace that proves the decision.

11. **Prepare for SME Review**
   - Consolidate all TBDs created in steps 3–10 with clear blocking status:
     - `pending_source` — missing DDS, incomplete source
     - `pending_sme_judgment` — behavior unclear from source alone
     - `non_blocking` — known gaps that don't affect downstream analysis
   - Add or preserve a centralized **Open Items / Limitations** table
     with Open Item, Impact, Evidence Gap, and Suggested Follow-up.
   - Generate review checklist for SME validation
   - Mark analysis as `blocked_pending_source` when missing or incomplete
     source prevents safe analysis; otherwise mark as `draft` (ready for
     review)
   - Gate: Analysis artifact is ready when every non-TBD behavior has an evidence_strength of `confirmed_from_code`, `strongly_inferred`, or `medium_confidence` (the latter two only when an SME review note is attached)

## Workflow State Write-Back

At the end of a program-analysis run, update
`<project-root>/workflow-state.yaml` per
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md).
Template: [`skills/legacy-modernization-orchestrator/references/state-writeback-snippet.md`](../legacy-modernization-orchestrator/references/state-writeback-snippet.md).

**Stage this skill produces:**

- `3b Program Analysis Done` when **every** in-scope program in
  `inventory.yaml` has an approved `program-analysis.md`
- `3a Program Analysis In Progress` when one or more in-scope programs
  still lack an analysis

**Last artifact path pattern:**
`02_programs/<MODULE-SLUG>/<OBJ-PROGRAM>/program-analysis.md`

**Writes per run:**

1. Overwrite `capabilities[<CAP-* from current_focus>]` with stage id,
   the path of the analysis you just saved, `last_skill:
   legacy-ibmi-program-analyzer`, and blocking IDs (`tbds`, `sme_pending`
   for any money / inventory / compliance branch awaiting SME).
2. Append one `history[]` entry with `note` naming the program analyzed
   (e.g. `"analyzed ORDENTR"`).
3. Overwrite `project.last_updated_at` / `project.last_updated_by`.

Never touch `current_focus`, other capabilities' entries, or past
`history[]` rows. A re-run on the same program is allowed; a re-run that
would lower `stage_id` requires the orchestrator's Rollback Protocol.

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md` for
the full principle. When source code disagrees with comments,
source-level flow headers, shop tool outputs, or SME recollection,
**the code wins** for behavioral claims. The disagreement itself
becomes a TBD asking the SME to confirm whether the secondary source
is stale or the code drifted from intent — but until then, the
analysis describes what the code actually does.

**Do NOT invent:**

- **Subroutine entry points** not directly visible in source (no inventing BEGPR blocks or subroutine labels)
- **File access** beyond what I/O statements (SETLL, READE, CHAIN, WRITE, UPDATE, DELETE) directly show
- **Business logic** from field names alone (e.g., a field named CREDLIMIT does not explain *why* the limit exists or how it's used)
- **External call parameters** if not visible in source headers, copybooks, or CALL statements
- **Error codes** if not explicitly caught or returned
- **Key-file roles, field lineage, or field mutations** when the source
  only proves a generic file reference
- **Message IDs** from generic handlers or message prefix conventions
  alone

**Instead:**

- If DDS is missing, create `TBD-<SLUG>-NNN: Confirm field meaning from [file-name] DDS`
- If subroutine is referenced but undefined, create `TBD-<SLUG>-NNN: Locate subroutine definition [name]`
- If error handling is unclear, tag `needs_sme_review` instead of inventing error recovery
- If external interface parameters are unknown, create `TBD-<SLUG>-NNN: Confirm parameter contract for [program-name]`

**Evidence minimum:**

- Every non-trivial behavior must have ≥1 evidence link, even if evidence_strength is low
- Do not document "likely" behavior without explicit evidence tag
- TBD questions count as evidence of a gap, not coverage

## SME Review Questions

The generated `program-analysis-<OBJ-ID>.md` must include a checklist. Before approval, SME must validate:

- [ ] Entry points are correct and complete (no missing callable subroutines)
- [ ] Program Call Map keeps a compact ASCII hierarchy Visual Overview and a traceable Call Evidence table
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] Routine Logic Details summarize every load-bearing routine/subroutine/procedure in the main analysis and route routine-dense detail to `routine-logic-details.md` / `routine-logic-details.yaml` with stable `RLOG-*` IDs
- [ ] Routine Logic Details or sidecar detail explain field calculations, carrier/lineage ties, routine-local exception closure, branch outcomes, exits, and evidence for each deep-read load-bearing routine
- [ ] Routine Logic Details or sidecar detail break out every material conditioned calculation block, including RPG conditioning indicators / condition groups such as `Condition 5`, with guarded statements, calculation order, target fields, intermediate variables, final output/error effect, and source evidence
- [ ] Routine Logic Details or sidecar detail include outcome reverse traces from every material message/status/error/return outcome back to the branch guard, conditioned calculation block, comparison threshold, intermediate variables, and source operands/carriers that make the outcome true
- [ ] Calculation Logic is front-loaded immediately after the title, summarizes the whole program's material calculations/assignments, and links every row to Routine Logic Details, Logic Decomposition, Key File & Field Logic, or Field Mutation evidence
- [ ] Logic Decomposition Ledger preserves calculations, constants, branch priority, loops, and CASE/SELECT behavior
- [ ] Routine / Window Data Flow shows variable-level input, transformation, output, side effects, source lines, and evidence
- [ ] Data Touch Map captures critical carriers, keys, payloads, and state impacts
- [ ] Key File & Field Logic preserves source identifiers with business meanings for key fields, aliases, work variables, calculations/conditions, and persisted fields
- [ ] File I/O Key Fields preserve source identifiers plus business meanings, and Purpose describes file access behavior
- [ ] File I/O field mutation matrix names which files and fields are written, updated, deleted, or skipped, and dense I/O/SQL detail is routed to `file-io-inventory.md` / `file-io-inventory.yaml`, `field-mutation-matrix.md` / `field-mutation-matrix.yaml`, and `sql-inventory.md` / `sql-inventory.yaml`
- [ ] External and dynamic calls include caller routine, source lines, parameters, resolution status, purpose, and evidence
- [ ] Validation Logic is front-loaded immediately after Calculation Logic, has one row per message/status/return/response/generic outcome with message descriptions and reverse trigger chains, and Error Handling closes each exception path through return, rollback, skip, log, or downstream impact
- [ ] Exception Handling is front-loaded immediately after Validation Logic, covers every observed business/parameter/I/O/external/system/generic exception path, and links each row to closure evidence
- [ ] Message Inventory is front-loaded immediately after Exception Handling, has one summary row per explicit message/code/literal, links message-dense details to `message-inventory.md` / `message-inventory.yaml`, and preserves description source, carrier/destination, trigger/handler, related Validation/Exception row, and evidence status in the summary or sidecar
- [ ] Inferred and unresolved calls, fields, variable meanings, and error codes are explicitly marked
- [ ] Code identifiers remain intact and readable in rendered tables/lists
- [ ] Redundancy candidates are conservative and do not remove hidden rules
- [ ] TBDs are non-blocking or properly flagged for follow-up
- [ ] Analysis contains no invented subroutines or undocumented file access

## Runtime Portability

Canonical source: `skills/legacy-ibmi-program-analyzer/SKILL.md`

Runtime adapters are synced via `scripts/sync-skills.sh`:

- Codex: `.codex/skills/legacy-ibmi-program-analyzer/SKILL.md`
- Claude Code: `.claude/skills/legacy-ibmi-program-analyzer/SKILL.md`
- OpenCode: `.opencode/skills/legacy-ibmi-program-analyzer/SKILL.md`

No runtime-specific assumptions are embedded in the canonical version.

## Version History

- v0.1.0 (2026-05-14): Initial release
  - 10-step workflow for RPGLE, CLLE, COBOL (with Program Call Map extraction and flat object-dependency listing)
  - Entry point extraction, control flow tracing, file I/O documentation
  - External call and error handling detection
  - Evidence tagging and TBD handling
  - SME review checklist
  - Positive and negative examples
- v0.2.0 (2026-06-01): Program-chain readiness tightening
  - Added Logic Decomposition Ledger, Key File & Field Logic, field-level File I/O mutation matrix, Exception Closure Ledger, and conservative redundancy candidate notes
  - Required every observed message ID / error code and every critical field lineage or mutation to carry evidence or a TBD
- v0.2.1 (2026-06-02): Evidence-first report format tightening
  - Renamed the Program Call Map tree-style subsection to auditable `Call Evidence`
  - Required source identifier + business meaning for key fields and variables
  - Added File I/O Purpose, external/dynamic call resolution status, Error Code Inventory, Routine / Window Data Flow, and centralized Open Items / Limitations
- v0.2.2 (2026-06-02): Error Code Inventory precision tightening
  - Required one Error Code Inventory row per explicit message ID, status code, return code, response value, SQLSTATE, or generic catch-all token
  - Renamed the inventory description column to `Message Description` and required description evidence or an unresolved TBD
  - Explicitly forbids grouped message-family summaries such as "validation messages" in place of per-message rows
- v0.2.3 (2026-06-02): Per-routine logic detail tightening
  - Added required Routine Logic Details for each load-bearing routine, subroutine, procedure, paragraph, or mainline segment
  - Required field calculation / assignment rows with target fields, expressions, operands, branch guards, precision/conversion notes, business effect, and evidence
  - Forbids compressing subroutine logic into generic summaries such as "validation logic" or "amount calculation"
- v0.2.4 (2026-06-02): Routine-local lineage and exception closure tightening
  - Added routine-local field lineage / carrier rows so calculations connect source carrier, intermediate variables, output/persisted carrier, and lineage/mutation references
  - Added routine-local exception closure rows for trigger, error/status/message fields, handling action, downstream skip/rollback/output, and Error Code Inventory link
  - Tightened subroutine output to match the program-single to program-chain principles for data-source preservation and exception closure
- v0.2.5 (2026-06-02): Conditioned calculation and outcome reverse-trace tightening
  - Required Routine Logic Details to break out material guard-scoped calculation chains, including fixed-format RPG conditioning indicators / named condition groups such as `Condition 5`
  - Requires guarded statement order, target assignments, intermediate variables, final output/error effect, source line range, and evidence for each material conditioned calculation block
  - Requires outcome reverse traces from material message/status/error outcomes back to branch guards, conditioned calculation blocks, comparison thresholds, intermediate variables, and source operands/carriers
  - Renamed the current output section from `Error Code Inventory` to front-loaded `Validation Logic`, placed immediately after Routine Logic Details
  - Forbids hiding condition-scoped calculation chains only in generic branch outcomes, Validation Logic summaries, or the Logic Decomposition Ledger
- v0.2.6 (2026-06-04): IT SME first-read core logic front-loading
  - Added top-of-document `Calculation Logic` immediately after the title
  - Moved `Validation Logic` to immediately follow `Calculation Logic`
  - Requires both top sections to summarize whole-program core behavior while linking back to routine-level evidence and ledgers
- v0.2.7 (2026-06-04): IT SME first-read exception and message front-loading
  - Added top-of-document `Exception Handling` immediately after Validation Logic
  - Added top-of-document `Message Inventory` immediately after Exception Handling
  - Requires exception paths and every observed message/code/literal to be reviewable before Metadata while still linking back to detailed closure evidence
- v0.2.8 (2026-06-05): Program Call Map visual format tightening
  - Required `Visual Overview` to remain a compact fenced `text` ASCII hierarchy
  - Standardized the tree shape around `PROGRAM mainline` plus `|--` branch connectors
  - Requires source flow headers to be reconciled against code-derived Call Evidence before use as the visual map
