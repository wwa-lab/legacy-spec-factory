---
skill: legacy-ibmi-program-analyzer
scorecard_version: v0.2.2
static_score: 9.60
decision: repo-ready
status: superseded_by_v0.2.3
superseded_by: docs/reviews/legacy-ibmi-program-analyzer-v0.2.3-scorecard.md
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-program-analyzer v0.2.2

## Change Under Review

v0.2.2 tightens `Error Code Inventory` after first-round output review. The
program contract now requires one row per explicit message ID, status code,
return code, response value, SQLSTATE, or generic catch-all token. The
inventory column is `Message Description`, and each row must carry a
code-specific description from evidence or an unresolved TBD.

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
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer --check`;
  Codex, Claude Code, OpenCode, and `.agents` runtime copies all reported `OK`.
- Ran Markdown table column consistency checks, `scripts/verify-skill-claims.py`,
  and `git diff --check`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.2.2 has not yet been smoke-executed across Codex
CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 10.0 | 1.00 |
| Progressive disclosure | 8% | 9.1 | 0.73 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.7 | 0.97 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.5 | 0.57 |

Final score before cap: **9.60 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| PROG-REV-040 | Medium | v0.2.2 Error Code Inventory precision has not been smoke-executed across the three target runtimes. | Run the program analyzer smoke protocol with a fixture containing multiple shop-local message IDs and confirm each ID is emitted as its own row with Message Description or unresolved TBD. |

## Improvements Completed In v0.2.2

| Finding | Resolution |
| --- | --- |
| PROG-REV-041 | Replaced `Meaning` with `Message Description` for Error Code Inventory rows. |
| PROG-REV-042 | Added an explicit one-row-per-message/status rule and forbade grouped rows such as `UCC0120, UCC5127` with family-level descriptions. |
| PROG-REV-043 | Required unresolved message descriptions to be marked explicitly and routed to Open Items / TBDs. |
