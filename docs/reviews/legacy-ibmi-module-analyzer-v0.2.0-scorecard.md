---
skill: legacy-ibmi-module-analyzer
scorecard_version: v0.2.0
static_score: 9.56
decision: repo-ready
status: superseded
last_verified: 2026-06-01
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-01 }
  claude_code: { status: synced, model: haiku, date: 2026-06-01 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-01 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-module-analyzer v0.2.0

## Change Under Review

v0.2.0 aligns module synthesis with program-analyzer and flow-analyzer v0.2.0.
It requires code-backed module analysis to consume or explicitly waive Flow
Replay Path, Cross-Program Field Lineage, Flow Persistence Matrix, and
Exception Propagation Chain coverage, then aggregates those surfaces into
module readiness, View 3 replay coverage, View 4 persistence / lineage tables,
and the BRD crosswalk.

## Decision

**Repo-ready, runtime smoke pending.**

The static contract is field-pilot quality, but the published score remains
capped at 9.0 until Codex, Claude Code, and OpenCode smoke execution evidence
is recorded for v0.2.0.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated canonical files under `skills/legacy-ibmi-module-analyzer/`.
- Updated the positive module example to include module program-chain
  readiness, replay coverage, module persistence, critical field lineage, and
  exception-aware data risks.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-module-analyzer`.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-module-analyzer --check`;
  all runtime adapter copies reported `OK`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap still applies under the review gate:

- portability has been synced and drift-checked, but v0.2.0 has not been
  loaded or executed in Codex CLI, Claude Code, and OpenCode
- runtime-smoke execution evidence remains pending

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.6 | 1.34 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.8 | 0.98 |
| Progressive disclosure | 8% | 9.1 | 0.73 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.6 | 0.96 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.1 | 0.55 |

Final score before cap: **9.56 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For Field Pilot

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| MOD-REV-020 | Medium | v0.2.0 has not yet been smoke-executed across Codex, Claude Code, and OpenCode. | Run positive and negative module-analysis smoke for v0.2.0 and update runtime evidence. | Runtime portability, reviewability |

### Improvements Completed In v0.2.0

| ID | Finding | Change Made |
| --- | --- | --- |
| MOD-REV-021 | Module analysis could summarize flows without proving replay readiness. | Added Module Program-Chain Readiness and View 3 Replay Coverage Summary. |
| MOD-REV-022 | Module data view could stay object-level and lose critical field behavior. | Added Module Persistence Matrix and Critical Field Lineage Across Module. |
| MOD-REV-023 | Exception paths could be reduced to generic error handling. | Added Module Exception & Recovery Summary and Exception-Aware Data Risks. |
| MOD-REV-024 | Older flow artifacts could silently support code-backed conclusions. | Added input and stop conditions requiring v0.2 replay / lineage / persistence / exception-chain coverage or named waiver. |
| MOD-REV-025 | BRD crosswalk did not explicitly carry replay, lineage, persistence, and exception evidence. | Updated BRD sections 2, 6, 7, 8, and 9 source mappings. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

v0.2.0 keeps module analysis as a synthesis layer, not a re-analysis layer. It
makes the module review answer four concrete questions: can each flow be
replayed, are critical fields preserved, what durable state changes or skipped
changes occur, and how do exception chains resolve at business level.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

Adapter sync and drift checks passed on 2026-06-01. The field-pilot cap remains
because v0.2.0 has not yet been loaded and executed through all three runtimes.

## Requested Revision Prompt For Claude Code

```text
Verify legacy-ibmi-module-analyzer v0.2.0 to finish the remaining
field-pilot blocker.

Static score: 9.56/10.
Published score: 9.0/10 after runtime-testing cap.

Blocking issue:
1. Three-runtime smoke execution evidence is missing for v0.2.0.

Required changes:
- Run positive and negative no-write smoke in Codex CLI, Claude Code, and
  OpenCode.
- Verify generated module artifacts include Module Program-Chain Readiness,
  View 3 Replay Coverage Summary, View 4 Module Persistence Matrix,
  Critical Field Lineage Across Module, and Exception-Aware Data Risks.
- Update `docs/runtime-matrix.md`, `docs/skill-status-truth-table.md`, README,
  and this scorecard with exact runtime/model/date notes.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-ibmi-module-analyzer/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
