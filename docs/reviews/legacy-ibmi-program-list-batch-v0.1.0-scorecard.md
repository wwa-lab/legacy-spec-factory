---
skill: legacy-ibmi-program-list-batch
scorecard_version: v0.1.0
static_score: 9.34
decision: repo-ready
status: current
last_verified: 2026-06-25
runtimes_tested:
  codex: { status: synced, model: gpt-5.4, date: 2026-06-25 }
  claude_code: { status: synced, model: not-run, date: 2026-06-25 }
  opencode: { status: synced, model: not-run, date: 2026-06-25 }
evidence_source: static review + adapter drift checks + local script smoke tests
---

# Skill Review Scorecard: legacy-ibmi-program-list-batch v0.1.0

## Change Under Review

New supplemental skill for Copilot Chat-limited IBM i program-list batch
operations. It converts a `program-list.csv` / Excel export into a one-program
prompt queue, durable status CSV, human-readable batch plan, machine-readable
manifest, and handoff model. It deliberately delegates source analysis to
`legacy-ibmi-program-analyzer` and final program-set review scaffolding to the
existing flow/program-set tools.

## Decision

**Repo-ready, not field-pilot ready.**

The skill is structurally sound, portable, synced to runtime adapter folders,
and smoke-tested locally for queue initialization and status validation. The
published score remains capped at 9.0 until prompt-driven smoke is executed in
the company Copilot Chat environment and, later, across Codex, Claude Code, and
OpenCode if the team wants field-pilot status.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Created canonical skill under `skills/legacy-ibmi-program-list-batch/`.
- Added references for status contracts and Copilot Chat operating constraints.
- Added templates for single-program prompts, batch plans, and session handoff.
- Added scripts:
  - `initialize_program_batch.py`
  - `validate_program_batch_status.py`
- Updated field-facing examples for the company Windows 11 environment where
  `py -3` is the only approved Python launcher.
- Ran Python compile checks for both scripts.
- Ran `quick_validate.py` against the skill folder.
- Ran local smoke test with mixed `program` and non-program rows.
- Ran adapter sync and drift check for `.claude`, `.opencode`, `.agents`, and
  `.codex` copies.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because Copilot Chat prompt-driven smoke has not yet been
executed in the company runtime, and three-runtime execution smoke has not
been completed.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.4 | 1.13 |
| IBM i / domain correctness | 14% | 9.1 | 1.27 |
| Evidence and anti-hallucination | 12% | 9.2 | 1.10 |
| Output contract | 10% | 9.5 | 0.95 |
| Progressive disclosure | 8% | 9.4 | 0.75 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.5 | 0.95 |
| Engineering handoff value | 8% | 9.6 | 0.77 |
| Maintainability | 6% | 9.3 | 0.56 |

Final score before cap: **9.34 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| PLB-REV-010 | Medium | Prompt-driven smoke has not yet been executed in the company Copilot Chat environment. | Run `docs/program-list-batch-prompt-test-plan.md` with 3-5 representative programs and capture outputs/status files. |
| PLB-REV-020 | Medium | The skill initializes and validates queue state, but does not yet update status files after a Copilot Chat program run automatically. | Keep this as a manual operator step for v0.1.0; consider a future status-update helper after internal dry-run feedback. |
| PLB-REV-030 | Low | Final program-set review generation is described as a handoff to existing tools, not wrapped in this skill's script. | Keep boundary for v0.1.0; consider adding a convenience wrapper only if operators repeatedly miss the final review step. |

## Strengths

- Strong separation of responsibilities: batch orchestration does not dilute
  the one-program contract of `legacy-ibmi-program-analyzer`.
- Explicit Copilot Chat constraints prevent unsafe single-chat concurrency.
- Durable state files make interruption and fresh-session resume mechanical.
- Scripts provide deterministic initialization and consistency checks.
- Canonical skill is synced across runtime adapter folders.

## SME / Governance Review

- SME governance is preserved by keeping program analysis and business meaning
  in downstream `legacy-ibmi-program-analyzer` artifacts.
- The skill does not mint `BR-*`, `CAP-*`, `DEC-*`, or business-rule IDs.
- It records operational status only: queued, in-progress, completed, blocked,
  failed, skipped, or reused.
- It requires validator status before marking a program complete.

## Runtime Portability Review

- Canonical source exists under `skills/legacy-ibmi-program-list-batch/`.
- Runtime copies synced under `.claude/skills`, `.opencode/skills`,
  `.agents/skills`, and `.codex/skills`.
- Runtime-specific Copilot Chat limitations are documented as an operating
  model, not encoded as a private folder convention.
- Python scripts use standard library only.

## Verification Commands Run

```bash
python3 -m py_compile \
  skills/legacy-ibmi-program-list-batch/scripts/initialize_program_batch.py \
  skills/legacy-ibmi-program-list-batch/scripts/validate_program_batch_status.py

python3 /Users/leo/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/legacy-ibmi-program-list-batch

python3 skills/legacy-ibmi-program-list-batch/scripts/initialize_program_batch.py \
  --program-list <tmp>/program-list.csv \
  --out-dir <tmp>/batch \
  --source-root <tmp>/source \
  --delivery-root <tmp>/delivery \
  --review-name "smoke batch"

python3 skills/legacy-ibmi-program-list-batch/scripts/validate_program_batch_status.py \
  --batch-dir <tmp>/batch

scripts/sync-skills.sh --skill legacy-ibmi-program-list-batch
scripts/sync-skills.sh --skill legacy-ibmi-program-list-batch --check
```

Field Windows 11 equivalent:

```powershell
py -3 skills\legacy-ibmi-program-list-batch\scripts\initialize_program_batch.py `
  --program-list <program-list.csv> `
  --out-dir outputs\program-list-batch-test `
  --source-root <source-root> `
  --delivery-root <delivery-root> `
  --review-name "copilot prompt dry run"

py -3 skills\legacy-ibmi-program-list-batch\scripts\validate_program_batch_status.py `
  --batch-dir outputs\program-list-batch-test
```

## Blocking For 9.5

| ID | Finding | Required Change | Affects |
| --- | --- | --- | --- |
| PLB-950-010 | No prompt-driven company Copilot Chat smoke evidence yet. | Execute the prompt test plan with a small real or redacted program list and archive outputs. | Runtime confidence |
| PLB-950-020 | No three-runtime execution smoke. | Run Codex, Claude Code, and OpenCode scenarios once the Copilot workflow stabilizes. | Field-pilot label |
