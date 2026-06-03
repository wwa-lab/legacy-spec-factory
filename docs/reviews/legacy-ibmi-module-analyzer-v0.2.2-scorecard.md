---
skill: legacy-ibmi-module-analyzer
scorecard_version: v0.2.2
static_score: 9.60
decision: repo-ready
status: superseded_by_v0.2.3
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-module-analyzer v0.2.2

## Change Under Review

v0.2.2 aligns module synthesis with program-analyzer v0.2.4 and
flow-analyzer v0.2.2. View 4 and readiness checks now preserve routine-local
carrier/lineage and exception closure evidence when it explains critical field
calculations, persistence, rollback/skipped work, or exception-aware data risks.

## Decision

**Repo-ready, runtime smoke pending.**

The published score remains capped at 9.0 until the updated module contract is
smoke-executed in all three target runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-ibmi-module-analyzer/SKILL.md`.
- Updated `references/synthesis-rules.md`.
- Ran sync, skill-claim, Markdown table, and whitespace checks.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.2.2 has not yet been smoke-executed across Codex
CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 9.8 | 0.98 |
| Progressive disclosure | 8% | 9.2 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.8 | 0.98 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.60 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| MOD-REV-040 | Medium | v0.2.2 routine-local evidence carry-forward has not been smoke-executed across the three target runtimes. | Run module smoke with flow/program evidence containing routine-local lineage and exception rows. |
