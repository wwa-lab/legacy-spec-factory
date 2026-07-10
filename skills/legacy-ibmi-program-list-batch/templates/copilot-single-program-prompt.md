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
  routine-logic-details.md and routine-logic-details.yaml as routine-level
  audit/checkpoint evidence.
- Do not create deep-read-plan.md or retained batch deep-read files for a
  normal_program unless density triggers promote it to complex_normal_program /
  large_extreme_program or the user explicitly asks for deep-read.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Write required artifacts to the output directory.
- Run the program-analysis validator before marking complete.
- Update program-batch-plan.md, program-list-status.csv, and
  batch-scan-manifest.yaml with scanned, blocked, or failed status.
- Do not generate or refresh program-set-sme-core-review.md in this
  single-program chat. Program-set review is a later flow-analyzer step only
  after a specific flow or program set is selected.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- message-inventory.yaml
- routine-logic-details.md
- routine-logic-details.yaml

Conditional output:
- deep-read-plan.md, all-routine-coverage-ledger.md, and
  routine-logic-details/deep-read-batch-*.md only when triggered by
  complex/large tier or retained batch evidence.

Validation:
py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py --analysis-dir "{{output_dir}}"

Company Windows 11 / Cline note:
- Run the generated `py -3 ...` command first. If the Python Launcher is
  unavailable, run the same command again with `python` replacing `py -3`.
- Do not replace it with PowerShell, `.cmd`, `.ps1`, shell continuations, or
  `py ... || python ...`.
- A validator failure is a result failure, not a reason to rerun it through
  another route.
- Keep Windows paths in code spans or fenced code blocks when reporting them.
  In Markdown, a raw `\@` can render as `@`, hiding the separator before
  program names such as `@CU400P`.
