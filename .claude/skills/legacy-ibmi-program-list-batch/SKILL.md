---
name: legacy-ibmi-program-list-batch
description: Orchestrate IBM i program analysis from a program-list CSV or Excel export for Copilot Chat-limited environments. Use when the user has many RPGLE/SQLRPGLE/CLLE/COBOL programs to scan independently and needs one-program-per-chat prompt queues, per-program status tracking, resumable handoff, or batch manifests. Supplemental skill; delegates actual source analysis to legacy-ibmi-program-analyzer and leaves any later cross-program/program-set review to legacy-ibmi-flow-analyzer after a specific flow or program set is selected.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Program List Batch

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Turns a `program-list.csv` / Excel export into a Copilot Chat-friendly per-program scan queue with durable status files. |
| Input | Program list rows with `member`, `object_type`, `source_kind`, `path`, `total_lines`, `size_tier`, and `tier_reason`; optional source root, output root, reference paths, and control file paths. |
| Output | `program-batch-plan.md`, `program-list-status.csv`, `batch-scan-manifest.yaml`, `prompt-queue/*.md`, optional `cline-parallel-runner-prompt.md`, optional `subagent-queue/*.md`, optional `subagent-dispatch-plan.md`, optional `batch-session-handoff.md`, and per-program analyzer artifacts named `<PROGRAM>-<artifact-name>` under each program folder. |
| Core prompt strategy | Keep work isolated: one program, one prompt, one fresh chat or sub-agent, durable state in files. |
| Upstream skill | `legacy-ibmi-inventory` or repo scan output that produced the program list. |
| Downstream skill | `legacy-ibmi-program-analyzer` for each program; later `legacy-ibmi-flow-analyzer` only when a specific flow/program set should be assembled from completed program artifacts. |
| Validation standard | Every row is represented, status values are legal, completed rows have required artifacts and validator status, and output folders are unique. |
| Known risk | Treating one Copilot Chat or one shared batch-state file as a concurrent runner; this causes context contamination, write conflicts, and status drift. |

## Purpose

Use this skill to prepare and control a batch of IBM i program-analysis runs
when the available runtime is GitHub Copilot Chat or another limited chat UI.
It does not analyze source code itself. It creates a queue of small,
copy-ready prompts so each program can be analyzed in a fresh chat by
`legacy-ibmi-program-analyzer`.

The original `program-list.csv` should remain the source export. Create
`program-list-status.csv` as the working copy with status columns.

## When To Use

Use this skill when:

- The user has a program list and wants to process it row by row.
- The user has a selected program subset and wants generated prompt files only
  for those programs, in the supplied order.
- The team can only use Copilot Chat and cannot run a true agent batch worker.
- The runtime supports isolated sub-agents and the user wants to fan out
  independent program prompts in parallel.
- Context limits require one program per session.
- The team needs resumable progress across sessions.
- The user asks for a "program batch plan", status columns in CSV/Excel, prompt
  queue generation, or batch resume/handoff.

Do not use this skill for a single program. Use `legacy-ibmi-program-analyzer`
directly.

## Core Rules

- One program equals one Copilot Chat session.
- One prompt file names exactly one program.
- Do not ask one Copilot Chat session to process multiple programs
  concurrently.
- If the runtime supports isolated sub-agents, safe parallelism means one
  sub-agent per generated `subagent-queue/*.md` file.
- Do not carry source excerpts, prior program summaries, or chat history into
  the next program.
- Parallel sub-agents must not edit `program-list-status.csv`,
  `program-batch-plan.md`, or `batch-scan-manifest.yaml` directly. Each
  sub-agent writes only its program artifacts and one result JSON under
  `subagent-results/`; the parent agent merges results afterward.
- If reference packs, dictionaries, message catalogs, code tables, or control
  files are provided, include their paths in every per-program prompt so each
  fresh Copilot Chat session can inspect the same supporting inputs.
- Treat reference and control inputs as supporting evidence only. They may
  clarify messages, statuses, field meanings, and validation rules, but they
  do not replace source evidence or SME approval.
- After every program, update all durable state files before starting another:
  `program-batch-plan.md`, `program-list-status.csv`, and
  `batch-scan-manifest.yaml`.
- Do not create an unbounded retry loop around Cline, model, network, tool, or
  validator failures. Cline may show its own bounded Auto-Retry cycle; once
  that visible cycle is exhausted, or the same transient error repeats, stop
  the current program and write durable failed state instead of starting a new
  ad hoc attempt.
- For Python command launch on Windows/Cline, allow only one launcher fallback:
  run `py -3 ...` first, then run the same command once with `python` only if
  `py -3` itself is unavailable. If Python starts and the script exits
  non-zero, treat that as the tool result, not a launcher problem.
- For generated artifact or validator failures, allow at most one targeted
  repair pass for the same program. If the validator still fails, mark the row
  `failed_validator`, record `last_error` and `next_action`, and move on only
  after durable state is updated.
- Use `legacy-ibmi-program-analyzer` for the actual source analysis.
- In queue initialization mode, do not invoke `legacy-ibmi-program-analyzer`,
  do not run semantic deep-read, do not run the program-analysis validator, and
  do not mark rows `completed`, `completed_with_warnings`, or
  `scanned_unvalidated`. Initialization creates queue/state files and, when
  requested, deterministic scaffolds only.
- Use validation mode deliberately:
  - `immediate` (default): run the program-analysis validator inside each
    per-program prompt before marking a row `completed`.
  - `deferred`: skip the expensive validator command during the fast batch
    scan, write `batch_status=scanned_unvalidated` and
    `validator_status=deferred`, then run final validation before downstream
    flow/spec/central-delivery use.
- Use scaffold mode deliberately:
  - `none` (default): generated prompts build deterministic indexes when each
    program prompt runs.
  - `precreate`: the initializer quickly runs the deterministic source indexer
    for each resolvable program, creates the per-program scaffold artifacts,
    writes `scaffold_status=present`, and leaves the row queued for semantic
    detail fill.
- Deterministic source indexes are pre-analysis scaffolds only. A row is not
  complete until semantic source deep-read has replaced pending/thin content in
  `<PROGRAM>-program-analysis.md` and `<PROGRAM>-routine-logic-details.md`.
- Do not mark a row `completed` or `completed_with_warnings` when the main
  analysis or routine detail file still contains scaffold wording such as
  `Draft wrapper seed generated`, `pending semantic deep-read`,
  `pending semantic detail`, `placeholder`, `not-yet-deep-read`, or
  `not deep-read`.
- Do not generate `program-set-sme-core-review.md` as part of this batch step.
  This skill only prepares, tracks, and validates independent per-program
  scans. Use `legacy-ibmi-flow-analyzer` later when an SME-provided flow or
  other explicit program set defines a meaningful cross-program boundary.
- Normal, complex, and large program rows all produce
  `<PROGRAM>-routine-logic-details.md` and
  `<PROGRAM>-routine-logic-details.yaml` as routine-level audit/checkpoint
  evidence. They do not replace the reader-first
  `<PROGRAM>-program-analysis.md`.
- Every per-program analyzer artifact under the program folder must be
  prefixed with the program/member name for RAG-friendly ingestion. Example:
  `CU219B-program-analysis.md`, `CU219B-source-index.yaml`,
  `CU219B-routine-logic-details.yaml`. Preserve IBM i member-safe characters
  such as `@`, `#`, and `$`; replace only filesystem-unsafe characters.
- A completed batch is a scan ledger, not a cross-program review. Programs in a
  repo-wide list do not need to have business-flow relationships before they
  can be scanned.

## Standard Output Layout

```text
outputs/program-list-batch/
  program-batch-plan.md
  program-list-status.csv
  batch-scan-manifest.yaml
  prompt-queue/
    0001-@CC080.md
    0002-@CC081.md
  completed/
  blocked/
  failed/
```

## Workflow

1. **Initialize the batch**
   - Read the input program list.
   - Preserve original columns.
   - Create `program-list-status.csv` with status columns.
   - Create `program-batch-plan.md` as the human-readable queue.
   - Create `batch-scan-manifest.yaml` as the durable machine state.
   - Create `prompt-queue/*.md` per `object_type = program` row.
   - In `--scaffold-mode precreate`, also create each program's deterministic
     scaffold artifacts up front and set the row's `next_action` to
     `fill details from scaffold`.
   - In `--subagent-mode prepare`, also create `subagent-queue/*.md`,
     `subagent-results/`, `subagent-dispatch-plan.md`, and
     `cline-parallel-runner-prompt.md` for runtimes that can launch isolated
     parallel workers.
   - Carry any provided reference paths and control file paths into the batch
     plan, manifest, and every generated prompt.
   - Stop after initialization. Do not start semantic program scans in this
     step. Program rows should remain `queued` unless they are blocked or
     skipped; scaffolded rows use `scaffold_status=present`.

2. **Run one program in Copilot Chat or one sub-agent**
   - Open a fresh chat.
   - Paste the next prompt file, or give one `subagent-queue/*.md` file to one
     isolated sub-agent.
   - Let `legacy-ibmi-program-analyzer` analyze only that program.
   - If the row has `scaffold_status=present`, start from the precreated
     source index, routine index, and routine logic YAML. Fill the reader-first
     semantic details from source instead of spending the prompt turn on
     deterministic scaffold generation again.
   - If the program output directory already contains artifacts from an older
     run, overwrite that program's generated analysis artifacts with the
     current skill output. Do not treat old artifacts as a cache.
   - In `immediate` validation mode, validate the output directory before
     marking it complete.
   - In `deferred` validation mode, do not run the expensive program-analysis
     validator in this prompt. Perform the scaffold/artifact guard and mark the
     row `scanned_unvalidated` / `deferred` so final validation can happen when
     the artifacts are actually consumed.
   - Update the plan, status CSV, and manifest.
   - If Cline/model/network/tool execution is interrupted after its visible
     Auto-Retry cycle, mark this row `failed_runtime`,
     `validator_status=not_run`, record the exact error in `last_error`, and
     set `next_action` to resume the same program after the environment is
     stable. Do not generate temporary `_generate_*_batch.py` scripts or other
     self-retry helpers unless the user explicitly asks for that recovery
     path.

3. **Merge parallel sub-agent results**
   - When sub-agent mode is used, each worker writes one
     `subagent-results/*.json` file.
   - Run `merge_subagent_results.py` after the workers finish.
   - The merge step updates `program-list-status.csv`,
     `program-batch-plan.md`, and `batch-scan-manifest.yaml` from the result
     JSON files.

4. **Resume safely**
   - In any new session, read durable files first.
   - Continue from the first row with `queued`, `in_progress`,
     `failed_runtime`, `failed_validator`, or a now-resolved blocker.
   - A `completed` row may be rerun intentionally when the operator wants the
     current skill behavior; reruns overwrite that program's generated
     artifacts and must pass validation again before staying `completed`.

5. **Finish the batch**
   - Validate status consistency.
   - Treat the batch as complete when every requested row is classified as
     `completed`, `completed_with_warnings`, `skipped_not_program`,
     `blocked_missing_source`, `failed_validator`, or `failed_runtime`.
   - Report completed, warning, skipped, blocked, and failed rows with paths to
     the durable state files and per-program artifact folders.
   - Do not build a repo-wide `program-set-sme-core-review.md` from the whole
     batch. If a later SME flow/list or call-flow discovery identifies a
     meaningful program set, hand the relevant completed program artifacts to
     `legacy-ibmi-flow-analyzer`.

## Scripts

Use direct Python commands in Windows/Cline. Do not use PowerShell, `.cmd`
launchers, `.ps1` launchers, shell continuations, or `py ... || python ...`
fallback chains.

- Windows / company Cline environment: run the `py -3 ...` command first. If
  the Python Launcher is unavailable, run the same command again with `python`
  replacing `py -3`.
- If Python starts and the script exits non-zero, treat that as the tool result
  and do not retry with another launcher.
- macOS/Linux: use `python3`.
- If both Windows Python routes are unavailable, stop and report the runtime
  issue.

Initialize a Copilot Chat queue:

```text
py -3 .agents\skills\legacy-ibmi-program-list-batch\scripts\initialize_program_batch.py --program-list outputs\repo-scan\program-list.csv --programs-file programs.txt --out-dir outputs\program-list-batch --source-root C:\path\to\source-repo --delivery-root C:\path\to\delivery-work --reference-path C:\path\to\reference-pack.md --reference-path C:\path\to\message-catalog.csv --control-file C:\path\to\status-code-table.csv --review-name "normal program batch" --scaffold-mode precreate --validation-mode deferred --subagent-mode prepare --max-parallel-agents 4
```

Step 1 queue-only prompt for Cline must be short and command-oriented. It
should tell Cline to run the initializer and stop. It must not include the
per-program analyzer contract, required per-program analysis outputs, or
validator instructions; those belong to generated Step 2 prompts.

Recommended fast two-phase mode:

1. Run the initializer with `--scaffold-mode precreate --validation-mode
   deferred --subagent-mode prepare`. This creates the prompt queue, optional
   sub-agent queue, status files, manifest, and deterministic per-program
   scaffold artifacts quickly.
2. In a manual Cline/Copilot workflow, paste generated prompt files one by one.
   In a sub-agent-capable Cline runtime, paste
   `cline-parallel-runner-prompt.md`; it tells Cline to launch up to
   `--max-parallel-agents` isolated workers using `subagent-queue/*.md`.
3. Each prompt starts from the scaffold and fills semantic analysis details.
   Final validator execution is deferred until the artifacts are consumed
   downstream or prepared for handoff.
4. After parallel workers finish, merge result JSON files:

```text
py -3 .agents\skills\legacy-ibmi-program-list-batch\scripts\merge_subagent_results.py --batch-dir outputs\program-list-batch
```

Use `--validation-mode immediate` or omit the option when every per-program
prompt should run the full validator before completion. Use
`--validation-mode deferred` for faster Cline batch scans; deferred rows are
not downstream-ready until the validator is run later and passes.

Use `--scaffold-mode precreate` when source paths are available locally and the
goal is to avoid spending every Cline prompt on deterministic scaffold
generation. Use `--scaffold-mode none` or omit the option when prompts should
do all work themselves.

Use `--subagent-mode prepare` when the runtime can launch isolated workers.
This mode prepares `cline-parallel-runner-prompt.md`, `subagent-queue/*.md`
prompts, and a dispatch plan; it does not make Copilot Chat itself concurrent.

`--programs-file` is optional. Use it when an operator or SME provides a
selected program list, such as `PROGRAM-A -> PROGRAM-B -> PROGRAM-C`, and you
want generated prompt files only for those distinct programs. Without it, the
initializer creates prompts for every `object_type = program` row in the input
`program-list.csv`.

Validate batch state:

```text
py -3 .agents\skills\legacy-ibmi-program-list-batch\scripts\validate_program_batch_status.py --batch-dir outputs\program-list-batch
```

## References

- Read `references/status-contract.md` when creating, updating, or validating
  `program-batch-plan.md`, `program-list-status.csv`, or
  `batch-scan-manifest.yaml`.
- Read `references/copilot-chat-operating-model.md` when the user asks about
  Copilot Chat limitations, concurrency, clean sessions, or resuming after
  context exhaustion.
- Use `../../docs/program-list-batch-prompt-test-plan.md` for company
  Copilot Chat prompt-driven dry-run testing before field pilot.

## Templates

- Use `templates/copilot-single-program-prompt.md` for each prompt queue item.
- Use `templates/program-batch-plan.md` for the human-readable batch plan.
- Use `templates/batch-session-handoff.md` when a session must stop and hand
  the next action to a new chat.

## Acceptance Checklist

- `program-list-status.csv` exists and preserves original program-list fields.
- `program-batch-plan.md` shows progress, current/next action, queue, and
  blockers.
- `batch-scan-manifest.yaml` records every row.
- Every prompt file names exactly one program.
- No two active rows share the same output directory.
- In scaffold precreate mode, queued program rows with available source have
  `scaffold_status=present` and `next_action=fill details from scaffold`.
- In sub-agent mode, each generated sub-agent prompt writes to one unique
  result JSON file, and shared batch state is updated only by the merge script.
- Completed rows have required per-program artifacts and validator status.
- Fast-scan rows may use `scanned_unvalidated` only when artifacts exist,
  scaffold text is gone, and `validator_status=deferred`.
- Blocked and failed rows have `last_error` and `next_action`.
- Completed rows must not contain deterministic scaffold or pending deep-read
  text in `<PROGRAM>-program-analysis.md` or
  `<PROGRAM>-routine-logic-details.md`.

Required per-program artifacts use the `<PROGRAM>-<artifact-name>` pattern,
for example `CU219B-program-analysis.md`, not shared generic names.

## Version History

- v0.1.9 (2026-07-11): Parallel sub-agent dispatch preparation
  - Added `--subagent-mode prepare` to generate sub-agent-safe per-program
    prompts, a dispatch plan, and result JSON locations.
  - Added `cline-parallel-runner-prompt.md` as the copy-ready second prompt
    for Cline to fan out generated per-program prompts.
  - Added `merge_subagent_results.py` so parallel workers avoid shared-state
    write conflicts and the parent agent can merge results after fan-out.

- v0.1.8 (2026-07-11): Two-phase scaffold precreate mode
  - Added `--scaffold-mode precreate` so batch initialization can quickly
    generate the prompt queue plus deterministic per-program scaffolds.
  - Kept semantic source analysis as the second phase: each prompt starts from
    the scaffold and fills reader-first details before deferred/final
    validation.

- v0.1.7 (2026-07-11): Deferred validation mode
  - Added `--validation-mode deferred` for faster Cline batch scans.
  - Introduced `scanned_unvalidated` / `validator_status=deferred` as a
    durable state that keeps scan throughput high without pretending final
    validation passed.

- v0.1.6 (2026-07-11): Reader-first completion guard
  - Strengthened generated per-program prompts so deterministic indexes are
    treated as scaffolds, not final analysis.
  - Updated batch status validators to reject completed rows whose main
    analysis or routine detail artifacts still contain scaffold / pending
    deep-read wording.

- v0.1.5 (2026-07-11): RAG-friendly per-program artifact names
  - Required per-program analyzer outputs to use `<PROGRAM>-<artifact-name>`
    filenames while keeping the existing program folder structure.
  - Updated generated Copilot/Cline prompts and batch status validation to
    expect program-prefixed artifacts.

- v0.1.4 (2026-07-11): Cline retry exit budget
  - Added a task-level retry budget so Cline/model/network interruptions,
    launcher failures, and validator failures exit into durable batch state
    instead of causing unbounded retries.
  - Limited semantic repair after a validator failure to one targeted pass
    before marking the row `failed_validator`.

- v0.1.2 (2026-07-10): Installed-skill Windows router
  - Moved the Cline execution entry point into the skill's own `scripts/`
    directory so synced `.agents` copies do not depend on a repository-root
    launcher.
  - Prohibited `py -3 ... || python ...` fallback chains under Windows
    PowerShell 5.1.

- v0.1.3 (2026-07-11): Python-only Windows/Cline launcher
  - Standardized Cline commands as direct `py -3 <script.py> ...` calls with a
    manual `python <script.py> ...` fallback only when `py -3` is unavailable.
  - Removed PowerShell and `.cmd` launchers from generated Cline commands.

- v0.1.1 (2026-07-10): Superseded native Windows fallback experiment
  - Historical experiment only; current Cline guidance is Python-only via
    direct `py -3`, then direct `python`.
  - Do not use non-Python launchers for batch initialization or status
    validation.
