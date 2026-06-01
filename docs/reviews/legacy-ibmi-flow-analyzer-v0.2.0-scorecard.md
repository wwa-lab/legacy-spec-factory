---
skill: legacy-ibmi-flow-analyzer
scorecard_version: v0.2.0
static_score: 9.58
decision: repo-ready
status: current
last_verified: 2026-06-01
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-01 }
  claude_code: { status: synced, model: haiku, date: 2026-06-01 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-01 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-flow-analyzer v0.2.0

## Change Under Review

v0.2.0 hardens flow analysis from call-chain stitching into replayable
program-chain analysis. It adds required sections for Flow Replay Path,
Cross-Program Field Lineage, Flow Persistence Matrix, and Exception
Propagation Chain, and requires the flow analyzer to consume the
program-analyzer v0.2.0 ledgers where available.

## Decision

**Repo-ready, runtime smoke pending.**

The static contract is field-pilot quality, but the published score remains
capped at 9.0 until Codex, Claude Code, and OpenCode smoke execution evidence
is recorded for v0.2.0.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated canonical files under `skills/legacy-ibmi-flow-analyzer/`.
- Updated positive batch and menu examples to include replay, lineage,
  persistence, and exception-chain sections.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-flow-analyzer`.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-flow-analyzer --check`;
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
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.6 | 1.34 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.8 | 0.98 |
| Progressive disclosure | 8% | 9.1 | 0.73 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.6 | 0.96 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.2 | 0.55 |

Final score before cap: **9.58 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For Field Pilot

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| FLOW-REV-020 | Medium | v0.2.0 has not yet been smoke-executed across Codex, Claude Code, and OpenCode. | Run positive and negative no-write smoke for v0.2.0 and update runtime evidence. | Runtime portability, reviewability |

### Improvements Completed In v0.2.0

| ID | Finding | Change Made |
| --- | --- | --- |
| FLOW-REV-021 | Flow analysis could remain a call-chain summary. | Added required Flow Replay Path from trigger to final outcome. |
| FLOW-REV-022 | Cross-program field semantics were too carrier-level. | Added Cross-Program Field Lineage stitched through `DATA-*`, carriers, and upstream program field lineage. |
| FLOW-REV-023 | Transaction-level persistence outcomes were implicit. | Added Flow Persistence Matrix for writes, updates, deletes, skipped mutations, queues, spool, checkpoints, and commit/rollback impact. |
| FLOW-REV-024 | Error propagation did not force message/error/RC chains. | Added Exception Propagation Chain that carries message IDs, error codes, RCs, skipped edges, persistence impact, and final outcome. |
| FLOW-REV-025 | Program-analyzer v0.2.0 output could be ignored by flow. | Required consumption or waiver of Logic Decomposition Ledger, Key File & Field Logic, Field Mutation Matrix, Exception Closure Ledger, and Redundancy Candidate Notes. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

v0.2.0 makes the flow review more concrete: SMEs can now validate whether a
transaction can be replayed from trigger to final outcome, whether critical
fields preserve lineage across programs, whether durable state changes are
complete, and whether exception chains match production recovery.

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
Verify legacy-ibmi-flow-analyzer v0.2.0 to finish the remaining field-pilot
blocker.

Static score: 9.58/10.
Published score: 9.0/10 after runtime-testing cap.

Blocking issue:
1. Three-runtime smoke execution evidence is missing for v0.2.0.

Required changes:
- Run positive and negative no-write smoke in Codex CLI, Claude Code, and
  OpenCode.
- Verify generated flow artifacts include Flow Replay Path, Cross-Program Field
  Lineage, Flow Persistence Matrix, and Exception Propagation Chain.
- Update `docs/runtime-matrix.md`, `docs/skill-status-truth-table.md`, README,
  and this scorecard with exact runtime/model/date notes.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-ibmi-flow-analyzer/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
