/legacy-ibmi-program-analyzer

If this slash command is unavailable in the current Copilot Chat environment,
follow skills/legacy-ibmi-program-analyzer/SKILL.md.

Task: analyze one IBM i program from a program-list batch.

Do not rely on previous chat history.
This is a fresh Copilot Chat session for one program only.

Program list: `{{program_list}}`
Program batch plan: `{{program_batch_plan}}`
Program status list: `{{program_list_status}}`
Batch manifest: `{{batch_manifest}}`

Program: {{member}}
Source path: `{{source_path}}`
Language: {{source_kind}}
Initial size tier: {{size_tier}}
Intent: {{intent}}
Output directory: `{{output_dir}}`

Reference and control inputs:
{{reference_paths}}
{{control_files}}

Rules:
- Build deterministic indexes first.
{{scaffold_prompt_note}}
- Deterministic indexes are pre-analysis scaffolds only. The generated
  {{member}}-program-analysis.md seed, source index, and routine sidecars are
  not final analysis until semantic deep-read replaces pending/thin content
  with source-backed reader-first detail.
- Do not stop after deterministic indexing. Read the generated
  {{member}}-source-index.yaml, {{member}}-routine-logic-details.yaml, and the
  source routine bodies; then fill {{member}}-program-analysis.md and
  {{member}}-routine-logic-details.md with the actual calculation,
  validation, exception, data movement, and outcome-trace details.
- Preserve the exact reader-first main-file structure while filling semantic
  detail. Do not delete, rename, demote, or replace these required headings:
  `## Program Reading Summary`, `## Calculation Logic`,
  `### Calculation Logic Overview`,
  `### Routine Index For Calculation Logic`, `## Validation Logic`,
  `### Validation Logic Overview`,
  `### Routine Index For Validation Logic`, `## Exception Handling`,
  `### Exception Flow Overview` (or `### Exception Handling Overview`), and
  `### Routine Index For Exception Handling`. Put source-backed theme
  subsections before each Routine Index and keep one reader-useful Routine
  Index row for every RLOG in {{member}}-routine-logic-details.yaml.
- Follow the `legacy-ibmi-program-analyzer` output contract and its exact main
  H2 order. The final `{{member}}-program-analysis.md` must contain, in order:
  `## Program Reading Summary`, `## Calculation Logic`, `## Validation Logic`,
  `## Exception Handling`, `## Message Inventory`, `## Metadata`,
  `## Analysis Coverage & Scope`, `## Program Call Map`, `## Routine Cards`,
  `## Routine Logic Details`, `## Deep Read Windows`,
  `## Entry Points & Parameters`, `## Object Dependencies`,
  `## Logic Decomposition Ledger`, `## Data Touch Map`,
  `## Key File & Field Logic`, `## Control Flow`, `## File I/O`,
  `## External Calls`, `## Error Handling`, `## Redundancy Candidate Notes`,
  `## TBDs & Blocking Status`, and `## Review Checklist`.
- Do not produce a simplified summary-only file, a theme-only file, or a
  latest-batch/delta-only file. Use the analyzer template and
  `references/output-contract.md` as the structure source of truth; sidecars
  supplement the main file and do not replace its reader-first sections.
- Analyze only this program.
- Read the listed reference and control inputs when they are relevant to this
  program's observed messages, status values, control-file lookups, field
  meanings, or validation rules. Treat them as supporting evidence only; do not
  invent behavior that is absent from source or SME-approved evidence.
- If the output directory already contains prior analysis artifacts for this
  program, overwrite this program's generated analysis artifacts with the
  current skill output. Do not skip the row solely because old artifacts exist.
- Do not import prior program source or prior chat summaries.
- When retained deep-read batch files exist (including every complex/large scaffold), complete this loop without stopping after the first batch:
  1. Process every existing `routine-logic-details/{{member}}-deep-read-batch-*.md` in natural numeric order.
     Also include checkpoint paths declared by the summary sidecar and supported `*-part-*.md`, `*-deep-batch-*.md`, and unprefixed aliases; de-duplicate them and apply the same natural numeric ordering.
  2. Deep-read no more than 5 source windows per batch, using that batch's Scope and Batch Coverage Summary to select the exact source windows.
  3. Persist each completed batch file before starting the next batch; replace every pending table cell, pending semantic field, and pending RLOG body with source-backed detail.
  4. Update `{{member}}-routine-logic-details.yaml` as each batch completes: for routines assigned to that batch, replace `semantic_status: pending_deep_read` and `coverage: indexed_only` with `semantic_status: deep_read_complete` and `coverage: deep_read`; atomically synchronize both `routine_logic_inventory.summary[]` and `routine_logic_inventory.details[]`, and fill each detail's trigger, logic, calculations, outcomes, lineage, and exception closure with explicit source-backed values (use an explanatory `none observed` entry when a category truly does not apply; do not leave seed arrays empty).
  5. Keep `{{member}}-all-routine-coverage-ledger.md` synchronized when that ledger exists, but do not perform final consolidation while later retained batches remain.
  6. After every retained deep-read batch is complete, merge the full set's semantic detail into `{{member}}-routine-logic-details.md` and `{{member}}-program-analysis.md`. Only after every retained deep-read batch is complete and consolidated, run the program-analysis validator.
- For normal programs without retained batch files, deep-read no more than 5 routine bodies per source-reading turn and continue until every declared RLOG is complete.
- Keep normal_program output reader-first and compact, but still create
  {{member}}-routine-logic-details.md and
  {{member}}-routine-logic-details.yaml as routine-level audit/checkpoint
  evidence.
- Do not create deep-read-plan.md or retained batch deep-read files for a
  normal_program unless density triggers promote it to complex_normal_program /
  large_extreme_program or the user explicitly asks for deep-read.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Every RLOG declared in {{member}}-routine-logic-details.yaml must have
  reader-useful detail in both {{member}}-program-analysis.md and
  {{member}}-routine-logic-details.md before this row can be marked complete.
  At minimum, include trigger, guard/condition, key assignments/calculations,
  validation or message/status outcomes, file or external side effects,
  exception closure, and source-line evidence. If a routine is truly utility
  only and was not assigned to a retained batch, it may keep
  `coverage: indexed_only` only with
  `semantic_status: source_backed_complete`, a concise source-backed
  explanation, reason, and evidence.
- Write required artifacts to the output directory.
{{validation_policy}}
- Update program-batch-plan.md, program-list-status.csv, and
  batch-scan-manifest.yaml with scanned, blocked, or failed status.
- Do not generate or refresh program-set-sme-core-review.md in this
  single-program chat. Program-set review is a later flow-analyzer step only
  after a specific flow or program set is selected.

Retry / exit budget:
- Cline may show its own bounded Auto-Retry for model/network errors. Do not
  add your own unbounded retry loop.
- If a model, network, tool-call, or edit interruption persists after Cline's
  visible Auto-Retry cycle, stop this program. Update
  program-list-status.csv with `batch_status=failed_runtime`,
  `validator_status=not_run`, a short `last_error` such as
  `cline_auto_retry_exhausted: <error>`, and a `next_action` telling the next
  operator to resume this same program after Cline/network stability returns.
- For Python launch, run the `py -3 ...` command once. If the Python Launcher
  is unavailable, rerun the same command once with `python` replacing `py -3`.
  If Python starts and the script exits non-zero, treat that as the tool
  result, not a launcher failure.
- If the validator fails after artifacts are generated, perform at most one targeted repair pass for this program. If validation still fails, mark
  `batch_status=failed_validator`, preserve the validator error in
  `last_error`, and set `next_action` for a later manual or SME-assisted
  follow-up.
- Do not create ad hoc `_generate_*_batch.py` scripts, launcher wrappers, or
  self-retry helpers to bypass these limits unless the user explicitly asks.

Required output:
- {{member}}-program-analysis.md
- {{member}}-source-index.yaml
- {{member}}-program-analysis-summary.yaml
- {{member}}-routine-index.md
- {{member}}-message-inventory.yaml
- {{member}}-routine-logic-details.md
- {{member}}-routine-logic-details.yaml

Conditional output:
- {{member}}-deep-read-plan.md, {{member}}-all-routine-coverage-ledger.md,
  and routine-logic-details/{{member}}-deep-read-batch-*.md only when triggered by
  complex/large tier or retained batch evidence. Once these files exist, they
  are mandatory completion surfaces and must not retain indexer pending seeds.

Validation:
{{validation_command_block}}

Company Windows 11 / Cline note:
{{validation_launcher_note}}
- Keep Windows paths in code spans or fenced code blocks when reporting them.
  In Markdown, a raw `\@` can render as `@`, hiding the separator before
  program names such as `@CU400P`.
