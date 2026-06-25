/legacy-ibmi-program-analyzer

If this slash command is unavailable in the current Copilot Chat environment,
follow skills/legacy-ibmi-program-analyzer/SKILL.md.

Task: analyze one IBM i program from a program-list batch.

Do not rely on previous chat history.
This is a fresh Copilot Chat session for one program only.

Program list: {{program_list}}
Program batch plan: {{program_batch_plan}}
Program status list: {{program_list_status}}
Batch manifest: {{batch_manifest}}

Program: {{member}}
Source path: {{source_path}}
Language: {{source_kind}}
Initial size tier: {{size_tier}}
Intent: {{intent}}
Output directory: {{output_dir}}

Rules:
- Build deterministic indexes first.
- Analyze only this program.
- If the output directory already contains prior analysis artifacts for this
  program, overwrite this program's generated analysis artifacts with the
  current skill output. Do not skip the row solely because old artifacts exist.
- Do not import prior program source or prior chat summaries.
- Read at most 5 routine bodies per turn.
- Keep normal_program output lightweight unless density triggers appear.
- For normal_program, do not create routine-logic-details.md,
  routine-logic-details.yaml, deep-read-plan.md, or batch deep-read files.
  Write the concise analysis and stop once required artifacts validate.
- Create routine-logic-details.md and routine-logic-details.yaml only when a
  density trigger changes the tier to complex_normal_program or
  large_extreme_program, or when the user explicitly asks for deep-read.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Write required artifacts to the output directory.
- Run the program-analysis validator before marking complete.
- Update program-batch-plan.md, program-list-status.csv, and
  batch-scan-manifest.yaml with scanned, blocked, or failed status.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- message-inventory.yaml

Conditional output:
- routine-logic-details.md and routine-logic-details.yaml only for
  complex_normal_program, large_extreme_program, or explicit deep-read
  continuation.
- deep-read-plan.md, all-routine-coverage-ledger.md, and
  routine-logic-details/deep-read-batch-*.md only when triggered by
  complex/large tier or retained batch evidence.

Validation:
{{python_launcher}} scripts/validate-program-analysis-contract.py --analysis-dir "{{output_dir}}"

Company Windows 11 note:
- Use `py -3` as the Python launcher.
- Do not fall back to `python` unless the team explicitly allows it for this
  run.
