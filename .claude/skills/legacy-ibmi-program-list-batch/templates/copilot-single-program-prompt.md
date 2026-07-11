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
- Analyze only this program.
- Read the listed reference and control inputs when they are relevant to this
  program's observed messages, status values, control-file lookups, field
  meanings, or validation rules. Treat them as supporting evidence only; do not
  invent behavior that is absent from source or SME-approved evidence.
- If the output directory already contains prior analysis artifacts for this
  program, overwrite this program's generated analysis artifacts with the
  current skill output. Do not skip the row solely because old artifacts exist.
- Do not import prior program source or prior chat summaries.
- Read at most 5 routine bodies per turn.
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
  only, say why and keep it concise rather than leaving it as indexed_only.
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
  complex/large tier or retained batch evidence.

Validation:
{{validation_command_block}}

Company Windows 11 / Cline note:
{{validation_launcher_note}}
- Keep Windows paths in code spans or fenced code blocks when reporting them.
  In Markdown, a raw `\@` can render as `@`, hiding the separator before
  program names such as `@CU400P`.
