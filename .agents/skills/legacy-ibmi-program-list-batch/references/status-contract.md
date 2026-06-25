# Program List Batch Status Contract

Use this reference when creating or checking the durable state files for
`legacy-ibmi-program-list-batch`.

## Files

| File | Audience | Purpose |
| --- | --- | --- |
| `program-batch-plan.md` | Operators and SMEs | Human-readable progress, next action, and blockers. |
| `program-list-status.csv` | Excel / spreadsheet users | Working copy of the program list with status columns. |
| `batch-scan-manifest.yaml` | Tools and resume logic | Machine-readable execution state and audit record. |

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
| `central_lookup_result` | `not_checked`, `found_on_remote_main`, `not_found_on_remote_main`, or `remote_unavailable`. |
| `validator_status` | `not_run`, `pass`, `pass_with_warnings`, or `failed`. |
| `output_dir` | Unique per-program output folder. |
| `prompt_path` | Prompt queue file for this program. |
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
| `reused_remote_main` | Accepted central artifact was reused. |
| `completed` | Scan completed and validator passed. |
| `completed_with_warnings` | Required artifacts exist, with warnings or non-blocking TBDs. |
| `blocked_missing_source` | Source path cannot be resolved. |
| `blocked_remote_unavailable` | Remote-main lookup cannot be verified. |
| `failed_validator` | Validator failed. |
| `failed_runtime` | Runtime/tooling failed before valid output. |
| `skipped_not_program` | Row is not a program. |

## Required Per-Program Artifacts

For `completed` and `completed_with_warnings` rows, the output directory should
contain:

- `program-analysis.md`
- `source-index.yaml`
- `program-analysis-summary.yaml`
- `routine-index.md`
- `routine-logic-details.md`
- `routine-logic-details.yaml`
- `message-inventory.yaml`

## Update Rules

- Update state files after every program before starting another.
- Do not mark a row `completed` unless the validator passed.
- Do not mark a row `completed_with_warnings` unless required artifacts exist.
- Put missing source in `blocked_missing_source`, not `failed_runtime`.
- Put validator failures in `failed_validator`, not `completed_with_warnings`.
- Record `last_error` and `next_action` for every blocked or failed row.
- Treat `@CC080` and `CC080` as different program identities unless a reviewed
  delivery profile defines aliases.

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
- `delivery_working_root`
- `delivery_remote_main_snapshot`
- `delivery_profile`
- `created_at`
- `updated_at`
- `status`
- `programs[]`

Each `programs[]` row should mirror the status CSV enough to resume without
opening Excel.
