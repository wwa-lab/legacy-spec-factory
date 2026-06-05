# Large Program Analysis

This reference defines how `legacy-ibmi-program-analyzer` handles large IBM i
programs when the full source cannot safely fit in model context.

For a human-oriented explanation of the same strategy, see
`../../../docs/large-rpg-analysis-strategy.md`.

## Core Idea

Treat a 20k-30k+ line RPG program as an evidence-driven program-understanding
problem, not as a large-text summarization problem.

The analyzer must first turn the source into a compact, auditable structure:
source index, Program Call Map, Logic Decomposition Ledger, Data Touch Map,
Key File & Field Logic, routine cards, deep-read windows, and coverage ledger.
Only then may it synthesize behavior.

The goal is not to "read every line into context." The goal is to preserve the
program's call topology, state changes, data movement, evidence, and known gaps
so downstream flow/module/spec work can decide what is safe to use.

## When To Use Large-Program Mode

Use large-program mode when any of these are true:

- source length is greater than 10,000 lines
- routine count is greater than 25 internal subroutines/procedures
- external call count is greater than 20
- file/object dependency count is greater than 25
- the analyzer cannot keep the full program, call graph, and evidence windows in
  context together

Use segmented mode for medium programs when the program is smaller than these
thresholds but still has dense call/data dependencies. Segmented mode is a
structure-first mode for medium-sized or dense programs where the full source
may fit, but safe analysis still requires routine/call/data segmentation.

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
  --out-dir path\to\PROGRAM-analysis
```

macOS/Linux:

```bash
python3 scripts/index-rpg-source.py path/to/PROGRAM.rpgle \
  --program PROGRAM \
  --out-dir path/to/PROGRAM-analysis
```

Windows launcher order: try `py -3` first, fall back to `python` if unavailable.
macOS/Linux: use `python3`. If all launchers fail, stop and report:
**"Python runtime unavailable"**. Do not configure PATH, install Python,
or create a virtual environment. Apply the same launcher order to all
temporary consistency checks, YAML readability checks, Markdown sanity checks,
and one-off helper scripts in this skill.

The helper writes:

| Artifact | Purpose |
| --- | --- |
| `source-index.yaml` | Machine-readable structure inventory: routines, calls, declared files, file operations, messages, message inventory summary, recommended deep-read windows, and mode selection. |
| `program-analysis-summary.yaml` | Compact machine-readable program summary for flow/module analyzers; prefer this over concatenating large Markdown analyses. |
| `routine-index.md` | Reviewer-readable seed for Routine Cards, Call Evidence, File Operation seed, and Message / Status seed. |
| `all-routine-coverage-ledger.md` | Initial coverage ledger showing every routine as `indexed_only` until semantic deep read proves stronger claims. |
| `deep-read-plan.md` | Recommended semantic windows for entry paths, state changers, external calls, transaction boundaries, and message/error paths. |
| `routine-logic-details.md` | Reviewer-readable sidecar seed for routine-level detail IDs, line ranges, call/data evidence, deep-read priority, and pending semantic detail. |
| `routine-logic-details.yaml` | Machine-readable routine logic inventory for downstream flow/module/spec consumers and later semantic enrichment. |
| `message-inventory.md` | Reviewer-readable detailed sidecar for every observed message/code/literal, including description status, occurrence count, routines, source lines, and unresolved lookup gaps. |
| `message-inventory.yaml` | Machine-readable detailed message inventory for downstream flow/module/spec consumers and reference-pack enrichment. |

These files are allowed intermediate artifacts. They do not replace
`program-analysis.md`, and they must not be treated as business conclusions.

Capture:

- source line count
- declared files and F-spec / DCL-F entries
- copybooks and `/COPY` directives
- mainline range
- `BEGSR` / `ENDSR` subroutines
- procedures and prototype definitions
- `EXSR`, `CALL`, `CALLP`, `CALLPRC`, `PERFORM`, and CL `CALLSUBR` sites
- file operations: `CHAIN`, `SETLL`, `READE`, `READ`, `WRITE`, `UPDATE`,
  `DELETE`
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

For routine-dense programs, keep front-loaded `Routine Logic Details` inside
`program-analysis.md` as a compact summary. Store per-routine semantic detail in
`routine-logic-details.md` and machine-readable detail in
`routine-logic-details.yaml`; link summary rows to stable `RLOG-<PROGRAM>-NNN`
detail IDs. When a program has more than 80 routines or more than 10,000 source
lines, split human-authored semantic detail into
`routine-logic-details/part-*.md` files by mainline/dispatch, state-changing
routines, validation/message routines, external boundaries, and indexed
utilities.

Downstream flow/module analyzers must prefer `program-analysis-summary.yaml`,
`source-index.yaml`, `routine-logic-details.yaml`, and
`message-inventory.yaml` when aggregating multiple programs. They should not
concatenate multiple full `program-analysis.md` files; human-readable Markdown
is for targeted clarification only.

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
procedure, copybook, object cluster, or call/data-flow path.
