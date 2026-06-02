---
skill: legacy-ibmi-program-analyzer
scorecard_version: v0.2.4
static_score: 9.64
decision: repo-ready
status: superseded_by_v0.2.5
superseded_by: docs/reviews/legacy-ibmi-program-analyzer-v0.2.5-scorecard.md
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-program-analyzer v0.2.4

## Change Under Review

v0.2.4 tightens `Routine Logic Details` so each load-bearing routine connects
field calculations to source/output carriers and Field Lineage / Mutation
evidence, while also closing routine-local exception paths. This aligns the
program-analysis output with the program-single to program-chain principles for
data-source preservation and exception closure.

## Decision

**Repo-ready, runtime smoke pending.**

The published score remains capped at 9.0 until the updated analyzer is
smoke-executed in all three target runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated canonical `skills/legacy-ibmi-program-analyzer/` first.
- Updated `SKILL.md`, `templates/program-analysis.md`,
  `references/output-contract.md`, and positive examples.
- Updated validator checklist expectations and runtime smoke criteria.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer`.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer --check`.
- Ran Markdown table column consistency checks, `scripts/verify-skill-claims.py`,
  and `git diff --check`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.2.4 has not yet been smoke-executed across Codex
CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.8 | 0.98 |
| Workflow completeness | 12% | 10.0 | 1.20 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 10.0 | 1.00 |
| Progressive disclosure | 8% | 9.2 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.9 | 0.99 |
| Engineering handoff value | 8% | 10.0 | 0.80 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.64 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| PROG-REV-060 | Medium | v0.2.4 routine-local lineage and exception closure has not been smoke-executed across the three target runtimes. | Run the program analyzer smoke protocol with a multi-subroutine fixture that includes field aliasing, persistence, return-code paths, and I/O exceptions. |

## Improvements Completed In v0.2.4

| Finding | Resolution |
| --- | --- |
| PROG-REV-061 | Added routine-local field lineage / carrier rows linking source carrier, intermediate variables, output/persisted carrier, and lineage/mutation evidence. |
| PROG-REV-062 | Added routine-local exception closure rows for triggers, error/status/message fields, handling action, downstream skip/rollback/output, Error Code Inventory link, and evidence. |
| PROG-REV-063 | Updated examples so subroutine logic preserves data-source and exception-closure principles inside the routine, not only in global sections. |
