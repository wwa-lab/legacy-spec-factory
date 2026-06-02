---
skill: legacy-step-validator
scorecard_version: v0.1.4
static_score: 9.55
decision: repo-ready
status: superseded_by_v0.1.5
superseded_by: docs/reviews/legacy-step-validator-v0.1.5-scorecard.md
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-step-validator v0.1.4

## Change Under Review

v0.1.4 aligns validator checks with program-analyzer v0.2.2. Program-analysis
validation now treats grouped message-ID rows and family-level Error Code
Inventory summaries as blocking when the analyzer contract requires one row per
explicit message/status code with a code-specific `Message Description` or
unresolved TBD.

## Decision

**Repo-ready, runtime smoke pending.**

The published score remains capped at 9.0 until the updated checklist content
is smoke-executed in all three target runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-step-validator/references/validation-checklists.md`.
- Updated `skills/legacy-step-validator/SKILL.md` version history.
- Ran `scripts/sync-skills.sh --skill legacy-step-validator`.
- Ran `scripts/sync-skills.sh --skill legacy-step-validator --check`.
- Ran `scripts/verify-skill-claims.py` and `git diff --check`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.4 checklist changes have not yet been
smoke-executed in Codex CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.6 | 1.15 |
| IBM i / domain correctness | 14% | 9.7 | 1.36 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.8 | 0.98 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.8 | 0.98 |
| Engineering handoff value | 8% | 9.8 | 0.78 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.55 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| STEP-VAL-040 | Medium | v0.1.4 Error Code Inventory validation has not been smoke-executed across the three target runtimes. | Run positive and blocked validations against analyzer v0.2.2 artifacts, including a blocked fixture with grouped message IDs. |
