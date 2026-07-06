# Batch Session Handoff

## Current Status

- Batch manifest: {{batch_manifest}}
- Program status list: {{program_list_status}}
- Program list: {{program_list}}
- Reference paths: {{reference_paths}}
- Control files: {{control_files}}
- Last completed program: {{last_completed_program}}
- Last validator status: {{last_validator_status}}
- Current blocker: {{current_blocker}}

## Next Action

- Next program: {{next_program}}
- Next prompt: {{next_prompt}}
- Next routines/windows: {{next_windows}}
- Required source reads:
  - {{required_source_read}}
- Required artifact updates:
  - routine-logic-details.md / routine-logic-details.yaml for every
    normal_program, complex_normal_program, and large_extreme_program row
  - program-analysis-summary.yaml
  - message-inventory.yaml
  - batch-scan-manifest.yaml
  - program-list-status.csv
  - program-batch-plan.md

## Copy-Ready Resume Prompt

Use skill: legacy-ibmi-program-list-batch
Task: resume an interrupted program-list batch.

For the next unfinished program row, use skill: legacy-ibmi-program-analyzer.

Resume from these durable files:
- Batch manifest: {{batch_manifest}}
- Program status list: {{program_list_status}}
- Original program list: {{program_list}}
- Source root: {{source_root}}
- Output root: {{output_root}}
- Reference paths: {{reference_paths}}
- Control files: {{control_files}}

Rules:
- Do not rely on previous chat history.
- Trust only durable files and validator results.
- Continue from the next unfinished row named in this handoff.
- Do not skip a selected row only because its output directory already exists.
  When rerunning a row, overwrite that program's generated analysis artifacts
  with the current skill output.
- Update program-batch-plan.md, program-list-status.csv, and
  batch-scan-manifest.yaml after the program.
- If validation passes and this session can safely continue, proceed to the
  next bounded batch.
- If this session cannot safely continue, write a new batch-session-handoff.md.
