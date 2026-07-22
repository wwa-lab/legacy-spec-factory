# Program List Batch Status Contract

Use this reference when creating or checking the durable state files for
`legacy-ibmi-program-list-batch`.

## Files

| File | Audience | Purpose |
| --- | --- | --- |
| `program-batch-plan.md` | Operators and SMEs | Human-readable progress, next action, and blockers. |
| `program-list-status.csv` | Excel / spreadsheet users | Working copy of the program list with status columns. |
| `batch-scan-manifest.yaml` | Tools and resume logic | Machine-readable execution state and audit record. |
| `cline-serial-runner-prompt.md` | Cline operators | Default Step 2 prompt for Cline. Processes `prompt-queue/*.md` serially. |
| `kiro-parallel-runner-prompt.md` | Kiro / agent runtimes | Optional Step 2 prompt for runtimes that can launch isolated parallel workers. |
| `subagent-dispatch-plan.md` | Parent agents/operators | Optional dispatch plan for Kiro/isolated parallel worker tasks. |
| `subagent-queue/*.md` | Kiro / isolated agent workers | Optional one-program worker prompts safe for parallel fan-out. |
| `subagent-results/*.json` | Merge script | Optional per-worker result files used to update shared batch state. |

Keep the original `program-list.csv` or Excel export read-only when possible.

## Required Input Columns

Minimum useful input columns:

- `member`
- `object_type`
- `source_kind`
- `path`
- `total_lines`
- `size_tier`
- `tier_reason`

If `object_type` is not `program`, mark the row `skipped_not_program`.

## Status CSV Columns

Add these columns to `program-list-status.csv`:

| Column | Meaning |
| --- | --- |
| `batch_status` | Current row status. |
| `validator_status` | `not_run`, `deferred`, `pass`, `pass_with_warnings`, or `failed`. |
| `scaffold_status` | `not_created`, `present`, `not_applicable`, `blocked_missing_source`, or `failed_runtime`. |
| `output_dir` | Unique per-program output folder. |
| `prompt_path` | Prompt queue file for this program. |
| `subagent_prompt_path` | Optional sub-agent-safe prompt for this program. |
| `subagent_result_path` | Optional per-program result JSON path for parallel worker output. |
| `owner` | Operator or session currently working the row. |
| `session_id` | Optional Copilot Chat/session label. |
| `started_at` | ISO timestamp when work started. |
| `completed_at` | ISO timestamp when work completed, blocked, or failed. |
| `last_error` | Short failure/blocker reason. |
| `next_action` | What the next operator/session should do. |
| `handoff_path` | Path to `batch-session-handoff.md` when needed. |

## Allowed Status Values

| Status | Meaning |
| --- | --- |
| `queued` | Not started. |
| `in_progress` | Claimed by an operator/session. |
| `completed` | Scan completed and validator passed. |
| `completed_with_warnings` | Required artifacts exist, with warnings or non-blocking TBDs. |
| `scanned_unvalidated` | Batch scan artifacts exist, but final program-analysis validation is deferred; this is a resumable checkpoint, never a terminal close. |
| `blocked_missing_source` | Source path cannot be resolved. |
| `failed_validator` | Validator failed. |
| `failed_runtime` | Runtime/tooling failed before valid output. |
| `skipped_not_program` | Row is not a program. |

## Retry And Exit Budget

The batch state is the exit mechanism when Cline, the model, the network, or a
tool call cannot proceed safely. Do not keep a row `in_progress` while starting
fresh ad hoc attempts in the same chat.

- Cline may perform its own bounded Auto-Retry for model/network errors. If the
  visible Auto-Retry cycle is exhausted, or the same transient error repeats,
  stop the current program and set `batch_status=failed_runtime`.
- For Windows/Cline Python launch, try `py -3 ...` once. If the Python Launcher
  is unavailable, retry the identical command once with `python` replacing
  `py -3`. If Python starts and the script exits non-zero, record that command
  result; do not try another launcher.
- For generated artifact or validator failures, perform at most one targeted
  repair pass for the same program. If validation still fails, set
  `batch_status=failed_validator`.
- Do not create temporary `_generate_*_batch.py` scripts, launcher wrappers, or
  self-retry helpers as an implicit recovery path. Use them only when the user
  explicitly approves that approach.

Examples:

| Situation | batch_status | validator_status | last_error | next_action |
| --- | --- | --- | --- | --- |
| Cline Auto-Retry exhausts on a network/model error before artifacts are stable | `failed_runtime` | `not_run` | `cline_auto_retry_exhausted: net::ERR_INCOMPLETE_CHUNKED_ENCODING` | `Resume this program in a fresh/stable Cline session; do not skip the row.` |
| Neither Windows Python route is available | `failed_runtime` | `not_run` | `python_runtime_unavailable` | `Install or expose Python 3, then rerun this program prompt.` |
| Program validator still fails after one targeted repair pass | `failed_validator` | `failed` | `program_analysis_contract_failed: <short validator finding>` | `Review validator output and rerun/repair this program only.` |
| Fast batch scan defers final validation | `scanned_unvalidated` | `deferred` | empty | `Run program-analysis validator before downstream use.` |
| Initializer precreated deterministic scaffold | `queued` | `not_run` | empty | `fill details from scaffold` |

`scaffold_status=present` means only the deterministic artifacts exist. It is
not a completion signal. The next Cline/Copilot prompt must still read source,
replace pending/thin scaffold text with semantic analysis, and then write the
final row status according to the selected validation mode.

If retained `routine-logic-details/<PROGRAM>-deep-read-batch-*.md` checkpoints
exist, semantic completion is a durable multi-checkpoint loop. Discover both
declared and actual checkpoint files, natural-sort by numeric suffix, process
at most five assigned routines/windows in each checkpoint, persist that
checkpoint and its matching routine YAML `summary[]`/`details[]` write-back,
and only then advance.
After all retained checkpoints are complete, merge the full set into the
consolidated routine detail and reader-first main analysis.

In Cline, use `cline-serial-runner-prompt.md` and process `prompt-queue/*.md`
serially. Cline must not use `subagent-queue`, must not call `use_subagents`,
and must not write `subagent-results/*.json`. Cline serial batches use
`validation_mode=immediate`: run the full program-analysis validator after
each program before starting the next. `scanned_unvalidated` is not a valid
Cline serial success state.

The Cline serial runner should not impose its own small stop limit. Continue
through every available prompt in the assigned batch while file reads/writes
and tool calls are still working. A soft context warning, verbose output, or
general concern about future quality is not a status transition. If a hard
Cline/model/network/tool/file I/O blocker prevents safe progress, write
`batch-session-handoff.md` with the exact next prompt and leave later rows
queued or in their current state; do not mark unattempted rows failed.

In `--subagent-mode prepare`, each Kiro/agent worker must write its result JSON
and avoid direct edits to shared batch state. This mode requires
`validation_mode=immediate`; deferred validation is not allowed for Kiro
parallel workers. Each worker must preserve the full reader-first analyzer
layout, retain `Routine Index For Calculation Logic`,
`Routine Index For Validation Logic`, and `Routine Index For Exception
Handling`, and run the full program-analysis validator before reporting
`completed/pass`.

Use this mode only in runtimes that can reliably launch isolated workers and
pass one complete Markdown prompt to each worker. The parent agent or operator
runs `merge_subagent_results.py` after workers finish. Before updating shared
state, that merge step re-runs the full program-analysis validator for every
worker result that claims success and converts a failed recheck to
`failed_validator/failed`. It is the only place parallel worker results should
update `program-list-status.csv`, `program-batch-plan.md`, or
`batch-scan-manifest.yaml`.

## Required Per-Program Artifacts

For `completed`, `completed_with_warnings`, and `scanned_unvalidated` rows, the
output directory should contain:

- `<PROGRAM>-program-analysis.md`
- `<PROGRAM>-source-index.yaml`
- `<PROGRAM>-program-analysis-summary.yaml`
- `<PROGRAM>-routine-index.md`
- `<PROGRAM>-message-inventory.yaml`
- `<PROGRAM>-routine-logic-details.md`
- `<PROGRAM>-routine-logic-details.yaml`

Use the exact program/member identity as the filename prefix after replacing
only filesystem-unsafe characters. Examples:
`CU219B-program-analysis.md`, `CU219B-source-index.yaml`, and
`@CU400P-routine-logic-details.yaml`.

For `normal_program`, routine detail sidecars are required as audit/checkpoint
evidence with the same reader-first coverage contract as complex and large
programs. Deep-read plans, coverage ledgers, and retained
`routine-logic-details/deep-read-batch-*.md` files are required only when the
program is promoted to `complex_normal_program`, `large_extreme_program`, or an
explicit deep-read continuation.

For `large_extreme_program`, the deterministic artifact set and the first
batch checkpoint are explicitly pre-analysis checkpoints. They never prove
completion by themselves: every retained checkpoint must be source-backed,
the duplicated routine YAML state must move to `deep_read` /
`deep_read_complete`, and the full batch set must be consolidated into the two
reader-first review surfaces before the row can claim `completed`.
The set also includes `<PROGRAM>-deep-read-execution-plan.yaml`: its complete
planned window/RLOG/batch allocation is authoritative, even when a later batch
file is absent. A terminal large-program row requires a `precreate`-captured
source-index SHA-256 and execution-plan SHA-256 in `batch-scan-manifest.yaml`.
The terminal validator uses those values as immutable locks and rejects a
self-consistent rewrite of source index + plan. If either lock is missing or
mismatched, set `failed_validator` and recreate the deterministic scaffold
from approved source rather than hand-editing a replacement plan.

## Completion Quality Guard

Deterministic source indexes create pre-analysis scaffolds. They are useful for
layout stability, source ranges, and routine inventory, but they are not final
reader-first analysis.

Before a row can stay `completed`, `completed_with_warnings`, or
`scanned_unvalidated`:

- `<PROGRAM>-program-analysis.md` must be filled with source-backed semantic
  analysis, not only the deterministic wrapper seed.
- `<PROGRAM>-routine-logic-details.md` must contain reader-useful routine
  details for the RLOG IDs declared in
  `<PROGRAM>-routine-logic-details.yaml`.
- Every retained
  `routine-logic-details/<PROGRAM>-deep-read-batch-*.md` checkpoint must be
  complete, use the required section layout, contain no more than five
  routines/windows, and be represented in the final consolidated surfaces.
- The main analysis, consolidated routine detail, and retained checkpoints may
  not still contain scaffold wording such as
  `Draft wrapper seed generated`, `pending semantic deep-read`,
  `pending semantic detail`, `placeholder`, `not-yet-deep-read`, or
  `not deep-read`.
- `<PROGRAM>-routine-logic-details.yaml` may not retain
  `semantic_status: pending_deep_read`. A routine assigned to a completed
  retained batch must move from `coverage: indexed_only` to
  `coverage: deep_read`, set `semantic_status: deep_read_complete`, and replace
  empty structured seed arrays with source-backed or explanatory values. An
  unbatched pure technical utility may retain `coverage: indexed_only` only
  when it has `semantic_status: source_backed_complete`,
  source-backed concise semantic detail, and explicit reason/evidence for
  remaining index-only.
- The main file must preserve the reader-first navigation headings, including
  `### Routine Index For Calculation Logic`,
  `### Routine Index For Validation Logic`, and
  `### Routine Index For Exception Handling`, in that order under their
  corresponding H2 sections. This is a cheap structural guard and applies even
  when the semantic validator is deferred.

If these checks fail after one targeted repair pass, mark the row
`failed_validator`, preserve the concrete finding in `last_error`, and set
`next_action` to continue semantic deep-read for that same program.

In `deferred` validation mode, the prompt skips the expensive semantic
validator command inside the Cline batch run, but the batch status validator
still checks required reader-first navigation headings. It writes
`batch_status=scanned_unvalidated` with `validator_status=deferred`. This is a
throughput optimization only. Any
downstream flow review, BRD/spec generation, SME signoff, or central delivery
handoff must run the program-analysis validator first and promote the row to
`completed` / `pass` only after the validator succeeds.

## Update Rules

- Update state files after every program before starting another.
- In sub-agent/manual worker mode, update shared state by merging worker result
  JSON files; do not let parallel workers edit the shared status CSV or
  manifest directly.
- If a selected row's output directory already exists, overwrite that
  program's generated analysis artifacts with the current skill output. Do not
  mark the row complete from old files alone.
- Do not mark a row `completed` unless the validator passed.
- Do not mark a row `completed_with_warnings` unless required artifacts exist.
- Do not treat `scanned_unvalidated` as terminal or downstream-ready; it
  requires final validator execution and promotion to `completed` / `pass`
  before reuse or batch close.
- Put missing source in `blocked_missing_source`, not `failed_runtime`.
- Put validator failures in `failed_validator`, not `completed_with_warnings`.
- Record `last_error` and `next_action` for every blocked or failed row.
- Do not leave a row `in_progress` after the retry budget is exhausted.
- Treat `@CC080` and `CC080` as different program identities unless a reviewed
  delivery profile defines aliases.

## Batch Completion Boundary

This contract completes the independent program-scan batch only. A batch is
ready to close when every requested row is classified as `completed`,
`completed_with_warnings`, `skipped_not_program`,
`blocked_missing_source`, `failed_validator`, or `failed_runtime`. Validated
rows must satisfy the required per-program artifact and validator rules.
`scanned_unvalidated` remains an open deferred-validation checkpoint until
final validation passes.

Use the batch validator in two distinct modes:

- Resume-safe progress check (default):
  `validate_program_batch_status.py --batch-dir <batch-dir>`. This validates
  state and completed artifact consistency while allowing rows that are still
  `queued` or `in_progress`.
- Final batch close:
  `validate_program_batch_status.py --batch-dir <batch-dir> --require-terminal`.
  This rejects `queued`, `in_progress`, and `scanned_unvalidated` rows. Every
  claimed `completed` / `completed_with_warnings` row must have a concrete,
  resolvable `output_dir`; the validator reruns the canonical program-analysis
  contract with the CSV `size_tier` as immutable input. Therefore a row
  classified as `large_extreme_program` cannot bypass retained deep-read
  batches by rewriting its summary as normal, and a generic large-program shell
  cannot pass simply because literal `pending` text was removed. Large terminal
  rows additionally require the precreated execution locks; use
  `--scaffold-mode precreate` before worker dispatch. Use it before reporting
  the batch finished.

Do not require `program-set-core-input-manifest.yaml`,
`program-set-sme-core-review.md`, or the program-set validator for this batch
completion gate. Those artifacts belong to `legacy-ibmi-flow-analyzer` after a
specific SME flow, call-flow discovery, or other meaningful program set is
selected.

## Plan Markdown Shape

`program-batch-plan.md` should include:

- Batch metadata.
- Progress counts by status.
- Current program and next program.
- Program queue table.
- Blockers table.
- Links to status CSV, manifest, and prompt queue.

## Manifest Shape

`batch-scan-manifest.yaml` should record:

- `batch_id`
- `review_name`
- `program_list`
- `status_list`
- `source_root`
- `output_root`
- `validation_mode`
- `scaffold_mode`
- `subagent_mode`
- `max_parallel_agents`
- `cline_serial_runner_prompt`
- `kiro_parallel_runner_prompt`
- `subagent_dispatch_plan`
- `subagent_queue`
- `subagent_results_dir`
- `reference_paths`
- `control_files`
- `created_at`
- `updated_at`
- `status`
- `programs[]`

Each `programs[]` row should mirror the status CSV enough to resume without
opening Excel, including `scaffold_status`, `subagent_prompt_path`, and
`subagent_result_path` when present.
