# Program Batch Plan

## Batch

- Review name: {{review_name}}
- Program list: {{program_list}}
- Status list: {{program_list_status}}
- Manifest: {{batch_manifest}}
- Source root: {{source_root}}
- Output root: {{output_root}}
- Reference paths: {{reference_paths}}
- Control files: {{control_files}}
- Mode: Copilot Chat-only / one program per chat

## Progress

| Status | Count |
| --- | ---: |
| queued | {{queued_count}} |
| in_progress | {{in_progress_count}} |
| completed | {{completed_count}} |
| completed_with_warnings | {{completed_with_warnings_count}} |
| blocked | {{blocked_count}} |
| failed | {{failed_count}} |
| skipped_not_program | {{skipped_not_program_count}} |

## Current / Next

- Current program: {{current_program}}
- Current owner/session: {{current_owner}}
- Next program: {{next_program}}
- Next prompt: {{next_prompt}}
- Next action: {{next_action}}

## Program Queue

| # | Program | Source | Tier | Status | Validator | Owner | Output | Next action |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
{{program_queue_rows}}

## Blockers

| Program | Blocker | Needed to unblock |
| --- | --- | --- |
{{blocker_rows}}
