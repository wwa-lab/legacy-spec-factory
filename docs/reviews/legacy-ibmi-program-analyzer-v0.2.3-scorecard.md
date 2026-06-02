---
skill: legacy-ibmi-program-analyzer
scorecard_version: v0.2.3
static_score: 9.62
decision: repo-ready
status: superseded_by_v0.2.4
superseded_by: docs/reviews/legacy-ibmi-program-analyzer-v0.2.4-scorecard.md
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-program-analyzer v0.2.3

## Change Under Review

v0.2.3 tightens `program-analysis.md` so every load-bearing routine,
subroutine, procedure, paragraph, or mainline segment has Routine Logic Details.
The new section requires execution trigger, step-by-step logic, field
calculation / assignment rows, branch outcomes, exits, evidence, and TBDs for
unresolved operands, precision, or branch priority.

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

A 9.0 cap applies because v0.2.3 has not yet been smoke-executed across Codex
CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.9 | 1.19 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 10.0 | 1.00 |
| Progressive disclosure | 8% | 9.2 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.8 | 0.98 |
| Engineering handoff value | 8% | 10.0 | 0.80 |
| Maintainability | 6% | 9.5 | 0.57 |

Final score before cap: **9.62 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| PROG-REV-050 | Medium | v0.2.3 Routine Logic Details have not been smoke-executed across the three target runtimes. | Run the program analyzer smoke protocol with a multi-subroutine fixture and confirm every load-bearing routine includes field calculation / assignment details. |

## Improvements Completed In v0.2.3

| Finding | Resolution |
| --- | --- |
| PROG-REV-051 | Added required Routine Logic Details between Routine Cards and Deep Read Windows. |
| PROG-REV-052 | Required field calculation / assignment rows with target field, expression, operands, branch guard, precision/conversion, business effect, and evidence. |
| PROG-REV-053 | Updated examples so per-routine logic is not reduced to generic "validation" or "calculation" summaries. |
