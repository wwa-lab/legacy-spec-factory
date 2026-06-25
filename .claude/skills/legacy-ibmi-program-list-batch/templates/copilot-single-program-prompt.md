Use skill: legacy-ibmi-program-analyzer
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
- Do not import prior program source or prior chat summaries.
- Read at most 5 routine bodies per turn.
- Keep normal_program output lightweight unless density triggers appear.
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
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

Validation:
{{python_launcher}} scripts/validate-program-analysis-contract.py --analysis-dir "{{output_dir}}"

Company Windows 11 note:
- Use `py -3` as the Python launcher.
- Do not fall back to `python` unless the team explicitly allows it for this
  run.
