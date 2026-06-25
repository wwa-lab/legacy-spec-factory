# Flow Analysis Resume Guideline

Use this guide when a program-flow run is interrupted because the LLM session
context is full, the IDE closes, the agent stops, or another analyst needs to
continue the work.

The rule is simple: do not depend on chat history. Resume from durable files in
the delivery repo.

## Resume Model

A program-flow core review is resumable when three checkpoint layers exist:

1. Per-program analysis artifacts
2. Program-set manifest
3. Program-set run state

The session may disappear. These files should not.

## Durable Checkpoints

### 1. Per-Program Artifacts

Each resolved program must have a program artifact folder. The folder may come
from approved delivery remote `main` reuse or from the current delivery working
branch.

Minimum artifacts:

```text
program-analysis.md
program-analysis-summary.yaml
source-index.yaml
routine-logic-details.md
routine-logic-details.yaml
message-inventory.yaml
```

When triggered by evidence or program size, also keep:

```text
file-io-inventory.yaml
field-mutation-matrix.yaml
sql-inventory.yaml
deep-read-plan.md
all-routine-coverage-ledger.md
routine-logic-details/deep-read-batch-001.md
routine-logic-details/deep-read-batch-002.md
```

For complex or large programs, retained deep-read batch files are the handoff
surface. A new session should continue from the next incomplete batch instead
of re-reading the whole source member.

### 2. Program-Set Manifest

The deterministic builder writes:

```text
modules/CAP-ID-0004-program_set_reviews/{review_slug}/
  program-set-core-input-manifest.yaml
```

The manifest is the control input for assembly. It records:

- SME-provided program order
- normalized program identity
- `central_lookup_result`
- artifact root
- artifact source
- compact artifact availability
- source inventory cache freshness/action

If `program-set-run-state.yaml` and the manifest disagree, the manifest controls
program list, program order, and artifact paths. The run state controls progress
notes and next action.

### 3. Program-Set Run State

Add this file beside the manifest:

```text
modules/CAP-ID-0004-program_set_reviews/{review_slug}/
  program-set-run-state.yaml
```

Recommended shape:

```yaml
schema_version: "0.1"
review_name: "Process Bulk Cancellation Master File"
review_slug: "process_bulk_cancellation_master_file"
flow_mode: "program_evidence_first"
updated_at: "2026-06-23T10:30:00Z"
updated_by: "codex"

paths:
  delivery_working_checkout: "C:/path/to/legacy-modernization-delivery"
  source_repo: "C:/path/to/source-repo"
  review_folder: "modules/CAP-ID-0004-program_set_reviews/process_bulk_cancellation_master_file"
  manifest: "program-set-core-input-manifest.yaml"
  review: "program-set-sme-core-review.md"

phase: "program_analysis"
last_completed:
  - "remote_main_lookup"
  - "source_inventory_check"

programs:
  "@CU400P":
    status: "resolved_remote_main"
    central_lookup_result: "found_on_remote_main"
    artifact_root: "modules/CAP-ID-0003-normal_program/@CU400P"
    next_action: "none"
  "@CU400":
    status: "deep_read_in_progress"
    central_lookup_result: "not_found_on_remote_main"
    artifact_root: "modules/CAP-ID-0002-complex_normal_program/@CU400"
    current_batch: "routine-logic-details/deep-read-batch-002.md"
    next_action: "continue deep-read batch 002"
  "CCP03":
    status: "pending_source"
    central_lookup_result: "not_found_on_remote_main"
    artifact_root: null
    next_action: "locate source via program-list.csv and run program analyzer"

assembly:
  manifest_built: true
  review_skeleton_built: true
  review_filled: false
  validator_status: "not_run"

blocked: false
blockers: []
next_action: "continue unresolved program analysis before assembly"
```

## Status Values

Use these status values consistently:

| Status | Meaning | Next action |
| --- | --- | --- |
| `resolved_remote_main` | Approved remote-main program artifact is reused. | None unless artifact is later found incomplete. |
| `analysis_complete` | Working-branch program analysis is complete enough for assembly. | Use in program-set review. |
| `deep_read_in_progress` | Program analysis is mid-batch. | Continue from retained batch files. |
| `pending_source` | Source path or inventory lookup is still needed. | Use source inventory or rerun repo inventory. |
| `pending_force_rescan` | SME requested refresh of a reusable artifact. | Run program analyzer with force-rescan reason. |
| `blocked_missing_evidence` | Required copybook, DDS, message catalog, or source evidence is missing. | Stop and request the missing evidence. |
| `ready_for_assembly` | All programs have usable evidence. | Build/fill program-set review. |
| `assembly_in_progress` | Review is being filled. | Continue from the first incomplete core section. |
| `validation_failed` | Validator failed. | Fix review structure/content and rerun validator. |
| `validation_passed` | Review is structurally safe for SME handoff. | Prepare SME handoff / PR summary. |

## Resume Rules

- Never restart completed program analysis unless the SME requests force refresh
  or the artifact fails the required-file / evidence-depth gate.
- Reuse approved remote-main artifacts when `central_lookup_result:
  found_on_remote_main` and required core files are present.
- Use working-branch artifacts for `not_found_on_remote_main` programs that
  were analyzed in the current run.
- Do not assemble `program-set-sme-core-review.md` while any in-scope program is
  only `pending_source`, `deep_read_in_progress`, or placeholder-only.
- If `program-set-run-state.yaml` is missing, reconstruct it from the manifest,
  artifact folders, validator result, and visible core review sections.
- If both manifest and run state are missing, start by recreating the manifest
  from the SME program list before doing any assembly.

## Resume Prompt

Use this in a new session:

```text
Use legacy-ibmi-flow-analyzer.

Resume this program-evidence-first Single Flow Core Review from existing
delivery artifacts. Do not restart completed program analysis.

Delivery working checkout: <path-to-legacy-modernization-delivery>
Source repo: <path-to-source-repo>
Review folder:
modules/CAP-ID-0004-program_set_reviews/<review_slug>/

First read, in this order:
1. program-set-run-state.yaml if present
2. program-set-core-input-manifest.yaml if present
3. program-set-sme-core-review.md if present
4. each manifest-listed program artifact folder
5. <source-root>/outputs/repo-scan/program-list.csv and scan-summary.yaml if a
   program still needs source analysis

Continue from the first incomplete gate:
- remote-main reuse / source inventory resolution
- unresolved program analysis
- complex or large program deep-read batch
- program-set assembly
- validator repair

Rules:
- Reuse approved remote-main artifacts when complete/current.
- Use working-branch artifacts for newly analyzed or force-refreshed programs.
- Do not assemble or finalize program-set-sme-core-review.md until every
  program has complete or approved reusable program-analysis evidence.
- If context is about to fill again, update program-set-run-state.yaml before
  stopping.

Report:
- what was resumed
- what was skipped because it was already complete
- current phase
- next action
- blockers, if any
- validator result, if completed
```

## 中文 Resume Prompt

```text
请使用 legacy-ibmi-flow-analyzer。

请从已有 delivery artifacts 继续这个 program-evidence-first Single Flow Core
Review。不要重做已经完成的 program analysis。

Delivery working checkout: <legacy-modernization-delivery 路径>
Source repo: <source repo 路径>
Review folder:
modules/CAP-ID-0004-program_set_reviews/<review_slug>/

请按顺序先读取:
1. program-set-run-state.yaml，如果存在
2. program-set-core-input-manifest.yaml，如果存在
3. program-set-sme-core-review.md，如果存在
4. manifest 中列出的每个 program artifact folder
5. 如果还有 program 需要 source analysis，再读取
   <source-root>/outputs/repo-scan/program-list.csv 和 scan-summary.yaml

从第一个未完成 gate 继续:
- remote-main reuse / source inventory resolution
- unresolved program analysis
- complex 或 large program 的 deep-read batch
- program-set assembly
- validator repair

规则:
- remote main 上 complete/current 的 approved artifact 要复用。
- 本次 newly analyzed 或 force-refreshed program 使用 working-branch artifacts。
- 任何 program 还没有 complete 或 approved reusable program-analysis evidence
  时，不要 finalize program-set-sme-core-review.md。
- 如果上下文快满了，停止前先更新 program-set-run-state.yaml。

Report:
- 这次从哪里恢复
- 哪些工作因为已经完成而跳过
- 当前 phase
- 下一步动作
- blockers，如有
- validator result，如果已完成
```

## When To Update Run State

Update `program-set-run-state.yaml` after each durable transition:

- remote-main lookup completed
- source inventory checked or refreshed
- one program analysis completed
- one complex/large deep-read batch completed
- manifest rebuilt
- review skeleton built
- one core review section filled
- validator failed or passed
- blocker discovered

Before stopping because context is nearly full, update run state first. A short
state file is more valuable than a long chat summary.
