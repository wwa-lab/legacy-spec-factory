# Program Size Tiering And Large Program Analysis

This reference defines how `legacy-ibmi-program-analyzer` classifies ordinary,
complex, and extreme IBM i programs. Most field programs are below 10,000 lines
and should follow the normal path. Large-program handling is the safety rail
for the minority of programs that are too large or too dense to understand in
one pass.

For a human-oriented explanation of the same strategy, see
`../../../docs/large-rpg-analysis-strategy.md`.

## Core Idea

Treat normal programs as concise SME review problems, complex normal programs
as targeted-evidence problems, and 20k-30k+ line RPG programs as
evidence-driven program-understanding problems, not large-text summarization
problems. The final SME artifact is still the main `program-analysis.md`;
large-program sidecars are audit, checkpoint, and machine-readable sources, not
the default reader journey.

The analyzer must first turn the source into a compact, auditable structure:
source index, Program Call Map, Logic Decomposition Ledger, Data Touch Map,
Key File & Field Logic, routine cards, deep-read windows, and coverage ledger.
Only then may it synthesize behavior into a reader-first final wrapper.

The goal is not to "read every line into context." The goal is to preserve the
program's call topology, state changes, data movement, evidence, and known gaps
so downstream flow/module/spec work can decide what is safe to use.

## Program Size Tiers

Use three SME-facing tiers:

| Tier | When to use | Default output profile |
| --- | --- | --- |
| `normal_program` | Under 10,000 lines with no density trigger; recommended deep-read windows fit in one five-routine batch. | Concise reader-first `program-analysis.md` plus core RLOG/message machine-readable artifacts. |
| `complex_normal_program` | Under large thresholds but dense in routines, file I/O, messages, SQL, field mutations, external calls, object dependencies, or recommended deep-read windows. | Reader-first SME review plus only triggered sidecars. |
| `large_extreme_program` | Above large thresholds or cannot fit safely with evidence windows. | Reader-first final `program-analysis.md`, full index, full sidecar set, coverage ledger, deep-read plan, retained `routine-logic-details/deep-read-batch-001.md` style checkpoints, and automatic five-routine loop when possible. |

## Reader-First Final Wrapper Rule

For every tier, including `normal_program`, the final `program-analysis.md`
uses the same reader-first layout. Normal programs are shorter, not structurally
different. For `large_extreme_program`, routine-dense programs, and user
requests such as "open one file and read it without detail links", this rule is
especially important: the final `program-analysis.md` must not be only a
sidecar index. It must include:

- `Program Reading Summary` immediately after the title
- `Calculation Logic`, `Validation Logic`, and `Exception Handling` with
  reader-oriented thematic overview before routine ledgers
- `Routine Index For Calculation Logic`, `Routine Index For Validation Logic`,
  and `Routine Index For Exception Handling`, each covering every RLOG declared
  in `routine-logic-details.yaml`
- `Message Inventory` synchronized with `message-inventory.yaml`
- `Routine Logic Details` in the main file with continuous, ordered
  `RLOG-<PROGRAM>-NNN` headings matching `routine-logic-details.yaml`
- No pending/placeholder Program Reading Summary, routine-index detail, or
  main-file RLOG detail; the final artifact must pass the reader-first golden
  gate in `validate_program_analysis_contract.py`

The retained sidecars still matter. They preserve audit trail, checkpoints,
machine-readable coverage, batch progress, and downstream aggregation. They do
not replace the final SME reading surface unless the user explicitly asks for a
compact wrapper.

### Normal Program Defaults

For `normal_program`, produce a concise SME-first review with the same main
layout and RLOG coverage contract as larger programs. Core artifacts are:

- `program-analysis.md`
- `program-analysis-summary.yaml`
- `source-index.yaml`
- `routine-index.md`
- `routine-logic-details.md`
- `routine-logic-details.yaml`
- `message-inventory.yaml`

Do not generate dense file I/O, mutation, SQL, message Markdown, coverage, or
deep-read planning sidecars by default. Generate them only when a trigger is
true or downstream flow/module analysis explicitly needs the extra evidence.

### Complex Normal Triggers

Use `complex_normal_program` when any of these are true:

- source length is greater than 3,000 lines but not greater than 10,000 lines
- routine count is greater than 10 but not greater than 25
- recommended deep-read windows exceed one five-routine batch
- external call count is greater than 8 but not greater than 20
- object dependency count is greater than 10 but not greater than 25
- file I/O operation count is dense, or state-changing I/O requires a sidecar
- unique message/status/code count is greater than 10
- embedded SQL statement count is dense
- field mutation/calculation chains are too dense for the main document

Optional sidecars are triggered independently:

| Sidecar | Trigger |
| --- | --- |
| `deep-read-plan.md` | More than one five-routine batch is needed, or tier is complex/large. |
| `all-routine-coverage-ledger.md` | More than one five-routine batch is needed, or tier is complex/large. |
| `message-inventory.md` | More than 10 unique message/status/code rows, or large tier. |
| `file-io-inventory.md` / `file-io-inventory.yaml` | More than 10 file operations, state-changing file I/O, commit, rollback, or large tier. |
| `field-mutation-matrix.md` / `field-mutation-matrix.yaml` | Persisted native/SQL mutation evidence is observed, or large tier. |
| `sql-inventory.md` / `sql-inventory.yaml` | Embedded SQL / SQLRPGLE evidence is observed, or large tier. |

## When To Use Large-Program Mode

Use large-program mode when any of these are true:

- source length is greater than 10,000 lines
- routine count is greater than 25 internal subroutines/procedures
- external call count is greater than 20
- file/object dependency count is greater than 25
- the analyzer cannot keep the full program, call graph, and evidence windows in
  context together

Use `complex_normal_program` for medium programs when the program is smaller
than these thresholds but still has dense call/data dependencies. Its
compatibility `analysis_mode` may remain `segmented`, but the SME-facing output
should still use the same reader-first main layout, with extra sidecars only
when a trigger requires expansion.

## Operating Rule

Do not summarize the whole program directly from raw source. First build a
structure index, then analyze semantic units, then synthesize.

The safe pipeline is:

1. Source size and structure preflight.
2. Deterministic source index.
3. Routine-level cards.
4. Program Call Map.
5. Logic Decomposition Ledger.
6. Data Touch Map.
7. Key File & Field Logic and field-level File I/O mutation matrix.
8. Exception Closure Ledger.
9. Deep-read windows for hot paths, state changers, external boundaries, and
   error handling.
10. Coverage ledger.
11. Evidence-backed synthesis.

## Source Index

The source index is a compact inventory, not a business interpretation.

When local file access is available, build the first-pass index with the
canonical helper before asking an LLM to synthesize behavior:

Windows:

```powershell
py -3 scripts\index-rpg-source.py path\to\PROGRAM.rpgle `
  --program PROGRAM `
  --out-dir path\to\PROGRAM-analysis `
  --delivery-root path\to\delivery-remote-main-snapshot `
  --delivery-profile path\to\delivery-profile.yaml
```

macOS/Linux:

```bash
python3 scripts/index-rpg-source.py path/to/PROGRAM.rpgle \
  --program PROGRAM \
  --out-dir path/to/PROGRAM-analysis \
  --delivery-root path/to/delivery-remote-main-snapshot \
  --delivery-profile path/to/delivery-profile.yaml
```

Windows launcher order: try `py -3` first, fall back to `python` if unavailable.
macOS/Linux: use `python3`. If all launchers fail, stop and report:
**"Python runtime unavailable"**. Do not configure PATH, install Python,
or create a virtual environment. Apply the same launcher order to all
temporary consistency checks, YAML readability checks, Markdown sanity checks,
and one-off helper scripts in this skill.

When `--delivery-root` is provided, the helper first checks the central
delivery remote-main snapshot/cache. If it prints
`central_lookup_result: found_on_remote_main`, stop and reuse the reported
artifact path instead of generating a new source index. If it prints
`central_lookup_result: not_found_on_remote_main`, continue with this large
program indexing flow. If the SME explicitly asks to refresh an existing
approved artifact, add `--force-rescan --rescan-reason "<why>"`; the scan will
continue and the generated metadata will record the central artifact that was
intentionally bypassed.

The helper writes core artifacts for every tier and optional sidecars only
when their triggers are true. Large/extreme programs write the full set.

Core artifacts:

| Artifact | Purpose |
| --- | --- |
| `program-analysis.md` | Stable SME review wrapper seed with all required sections in contract order. The seed starts as pending/draft and is filled during semantic deep-read. |
| `source-index.yaml` | Machine-readable structure inventory: program profile, free-format statements, declarations, assignments, routines, calls, declared files, file operations, SQL, messages, recommended deep-read windows, and mode selection. |
| `program-analysis-summary.yaml` | Compact machine-readable program summary for flow/module analyzers; prefer this over concatenating large Markdown analyses. |
| `routine-index.md` | Reviewer-readable seed for Routine Cards, Call Evidence, File Operation seed, and Message / Status seed. |
| `routine-logic-details.md` | Reviewer-readable sidecar seed for routine-level detail IDs, line ranges, call/data evidence, deep-read priority, and pending semantic detail. |
| `routine-logic-details.yaml` | Machine-readable routine logic inventory for downstream flow/module/spec consumers and later semantic enrichment. |
| `message-inventory.yaml` | Machine-readable detailed message inventory for downstream flow/module/spec consumers and reference-pack enrichment. |

Optional artifacts:

| Artifact | Purpose |
| --- | --- |
| `all-routine-coverage-ledger.md` | Initial coverage ledger showing every routine as `indexed_only` until semantic deep read proves stronger claims. |
| `deep-read-plan.md` | Recommended semantic windows for entry paths, state changers, external calls, transaction boundaries, and message/error paths. |
| `message-inventory.md` | Reviewer-readable detailed sidecar for every observed message/code/literal, including description status, occurrence count, routines, source lines, and unresolved lookup gaps. |
| `file-io-inventory.md` | Reviewer-readable detailed sidecar for every observed native file operation, screen/report boundary, and transaction boundary. |
| `file-io-inventory.yaml` | Machine-readable file I/O inventory for downstream flow/module/spec consumers. |
| `field-mutation-matrix.md` | Reviewer-readable mutation sidecar for native WRITE/UPDATE/DELETE and embedded SQL DML. |
| `field-mutation-matrix.yaml` | Machine-readable field mutation matrix for downstream flow/module/spec consumers. |
| `sql-inventory.md` | Reviewer-readable embedded SQL sidecar for SQLRPGLE/free-format statements, host variables, table/view targets, and status-handling seeds. |
| `sql-inventory.yaml` | Machine-readable embedded SQL inventory for downstream flow/module/spec consumers. |

Large/extreme artifacts:

| Artifact | Purpose |
| --- | --- |
| `routine-logic-details/deep-read-batch-001.md` | Required first retained checkpoint for large/extreme batched deep-read. Additional batches continue as `deep-read-batch-002.md`, `deep-read-batch-003.md`, and so on, with at most five routines/windows per batch. |

These files are allowed intermediate artifacts. They do not replace
`program-analysis.md`, and they must not be treated as business conclusions.

Capture:

- source line count
- declared files and F-spec / DCL-F entries
- copybooks and `/COPY` directives
- mainline range
- `BEGSR` / `ENDSR` subroutines
- procedures and prototype definitions
- SQLRPGLE / free-format declarations: `DCL-PI`, `DCL-PR`, `DCL-DS`,
  `DCL-S`, and `DCL-PROC`
- free-format statement spans, procedure calls, and assignments
- `EXSR`, `CALL`, `CALLP`, `CALLPRC`, `PERFORM`, and CL `CALLSUBR` sites
- file operations: `CHAIN`, `SETLL`, `READE`, `READ`, `WRITE`, `UPDATE`,
  `DELETE`
- embedded SQL / SQLRPGLE: `EXEC SQL` statements, cursor statements, DML,
  host variables, table/view targets, `SQLCODE`, and `SQLSTATE`
- assignments immediately before `WRITE`, `UPDATE`, `DELETE`, or SQL DML so
  persisted field mutations can be reconstructed
- display/report operations: `EXFMT`, `WRITE` to DSPF/PRTF, printer overflow
- commit and rollback operations
- message/data-queue/API operations
- constants, literals, arithmetic, string construction, precision conversion,
  `IF`, `SELECT` / `CASE`, loops, and branch fallback order
- indicators and error handlers that affect branching or I/O outcome
- observed message IDs, error codes, return/status codes, and generic catch-all
  handlers

For large or message-dense programs, keep the front-loaded `Message Inventory`
inside `program-analysis.md` as a compact summary. Store per-occurrence message
details in `message-inventory.md` and machine-readable details in
`message-inventory.yaml`; link summary rows to stable `MSG-<PROGRAM>-NNN`
detail IDs instead of expanding every occurrence in the main analysis.
Observed message/status/code values without descriptions are not meaningful
SME review output. If descriptions are missing, mark each row unresolved and
create a blocking message-description TBD; do not pass final validation until a
message file/catalog/reference pack, source literal/comment, runtime evidence,
or SME-approved description source resolves the row.

For routine-dense programs, keep `Routine Logic Details` inside
`program-analysis.md` table-led and reader-friendly, but include every RLOG
declared in `routine-logic-details.yaml` as a continuous, ordered main-file
heading. Store duplicate/audit per-routine semantic detail in
`routine-logic-details.md` and machine-readable detail in
`routine-logic-details.yaml`. When a program has more than 80 routines or more
than 10,000 source lines, split human-authored semantic detail into
`routine-logic-details/deep-read-batch-*.md` retained checkpoint files by
five-routine/window batches, or `routine-logic-details/part-*.md` files by
semantic shard such as mainline/dispatch,
state-changing routines, validation/message routines, external boundaries, and
indexed utilities.

Each part or batch file must be SME-first and must use the same top-level `##`
layout: `Calculation Logic`, `Validation Logic`, `Exception Handling`,
`Scope`, `Batch Coverage Summary`, `Message Inventory`, `Routine Details`.
The core sections summarize only the routines in that shard and link each row
to the relevant `RLOG-*` detail, conditioned calculation block, outcome reverse
trace, exception closure, message detail, or TBD. `Message Inventory` must list
every exact message/status/literal observed in that batch as its own row; do
not make SME reviewers scroll through routine subsections to find the batch's
core calculations, validations, exception paths, or messages. Do not paste
source code into the batch core sections; use identifiers, normalized logic,
source ranges, evidence IDs, and `RLOG-*` links instead.

The retained batch/shard files must be consolidated after batch deep-read. The
final `program-analysis.md` is the primary SME review document and the final
`routine-logic-details.md` is the consolidated audit/checkpoint document for all
routine detail, even for very large programs. Both must cover every RLOG from
`routine-logic-details.yaml`. The routine detail sidecar must contain whole-program
`## Calculation Logic`, `## Validation Logic`, `## Exception Handling`,
`## Message Inventory`, `## Routine Detail Index`, and `## Routine Details`
sections, with every routine included and every exact message/status/literal
listed. Keep the main file readable; do not force SMEs to review only by
sidecar, batch, or part files. Keep the batch files as checkpoints so reviewers can audit
what was processed in each five-routine/window pass.

For large and segmented programs, the final `program-analysis.md` is still the
contracted SME wrapper. It may stay table-led, but it must include every
required section from `references/output-contract.md`, include reader-oriented
core logic before routine ledgers, include the complete RLOG and message
coverage required by the output contract, and pass the Program Artifact
Finalization Gate. Each `routine-logic-details/part-*.md` or
`routine-logic-details/deep-read-batch-*.md` checkpoint file must front-load SME
core logic (`Calculation Logic`, `Validation Logic`, and `Exception Handling`)
before per-routine detail, and the core logic must not contain fenced code
blocks or copied RPG/CL/COBOL/SQL source snippets. Do not replace the wrapper with a compressed
latest-batch summary or sidecar table of contents. Before delivery, run:

```text
Windows: py -3 scripts\validate-program-analysis-contract.py --analysis-dir <DIR>
macOS/Linux: python3 scripts/validate-program-analysis-contract.py --analysis-dir <DIR>
```

The gate checks required wrapper sections, declared sidecar files, RLOG coverage
from `routine-logic-details.yaml` to both `program-analysis.md` and
`routine-logic-details.md`, core logic routine-index coverage, stale deep-read
gap wording, and message inventory synchronization.

For file-I/O-dense or SQLRPGLE programs, keep `File I/O` and `Key File & Field
Logic` inside `program-analysis.md` as SME-readable summaries. Store complete
operation detail in `file-io-inventory.md` / `file-io-inventory.yaml`,
persisted native and SQL mutations in `field-mutation-matrix.md` /
`field-mutation-matrix.yaml`, and embedded SQL detail in `sql-inventory.md` /
`sql-inventory.yaml`. Link main analysis rows to stable `FIO-*`, `MUT-*`, and
`SQL-*` detail IDs instead of expanding every operation or host variable inline.

Downstream flow/module analyzers must prefer `program-analysis-summary.yaml`,
`source-index.yaml`, `routine-logic-details.yaml`, and
`message-inventory.yaml`, `file-io-inventory.yaml`,
`field-mutation-matrix.yaml`, and `sql-inventory.yaml` when aggregating
multiple programs. They should not concatenate multiple full
`program-analysis.md` files; human-readable Markdown is for targeted
clarification only.

## Routine Card

Each routine card records one semantic unit:

| Field | Meaning |
| --- | --- |
| Routine | Subroutine, procedure, paragraph, or mainline segment |
| Location | Source line range |
| Called By | Immediate inbound callers |
| Calls Out | Internal and external calls made by this routine |
| Data Touches | Files, queues, screens, reports, parameters, and critical fields |
| State Impact | `read-only`, `creates`, `updates`, `deletes`, `external handoff`, `unknown` |
| Error Handling | Local monitor, indicator checks, message IDs/error codes, message writes, propagated status |
| Evidence | Source evidence IDs and line ranges |
| Coverage | `indexed_only`, `deep_read`, or `blocked` |
| Open Questions | Source gaps, SME questions, or contradiction references |

SME confirmation belongs in evidence or review fields, not the coverage field.

## Deep-Read Window Selection

Deep-read windows should prioritize:

- entry mainline and trigger handling
- routines directly dispatched from the mainline
- routines on hot call paths
- routines with external calls
- routines that write, update, delete, commit, roll back, send messages, or send
  queue payloads
- routines with file reads followed by `%FOUND`, `%EOF`, `%EQUAL`, `IF`,
  `WHEN`, `DOW`, `DOU`, or similar branch logic
- display/report boundaries such as `EXFMT`
- explicit error handlers such as `MONITOR`, `ON-ERROR`, `%ERROR`, `MONMSG`,
  `SNDPGMMSG`, or `SNDMSG`
- routines assigning outcome/status carriers such as response, return code,
  approval/decline, card/account/customer, amount, ARPC, or cryptogram fields
- routines touching money, account/customer IDs, inventory, approval/decline
  state, posting flags, audit IDs, or error/return codes
- routines involved in contradictions or flow-header drift

Do not deep-read every technical utility routine if it is structurally indexed
and has no business state impact.

## Coverage Ledger

The coverage ledger prevents partial analysis from masquerading as full
understanding. It is a required output subsection in `Analysis Coverage &
Scope`, not merely an internal note.

Required fields:

| Metric | Meaning |
| --- | --- |
| Source Lines | Total source lines analyzed |
| Routines Found | Count from source index |
| Routines Deep-Read | Count and percentage |
| Routines Indexed Only | Count and reason |
| External Edges Resolved | Count and percentage |
| Data Touches Resolved | Count and percentage |
| Blocking Gaps | Source gaps that block flow/spec use |
| Non-Blocking Gaps | Known gaps that can proceed with warning |

## Forbidden Pattern

Do not split a 30k-line RPG program into fixed line chunks and summarize each
chunk independently. Fixed chunks destroy call relationships, state transitions,
and cross-routine data flow.

If chunking is required, chunk by semantic unit: mainline segment, routine,
procedure, copybook, object cluster, SQL statement/cursor scope, or
call/data-flow path. A multi-line free-format calculation or SQL statement must
stay in one semantic window.
