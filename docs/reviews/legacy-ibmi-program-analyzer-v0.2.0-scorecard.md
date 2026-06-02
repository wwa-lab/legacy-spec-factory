---
skill: legacy-ibmi-program-analyzer
scorecard_version: v0.2.0
static_score: 9.55
decision: repo-ready
status: superseded
last_verified: 2026-06-01
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-01 }
  claude_code: { status: synced, model: haiku, date: 2026-06-01 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-01 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-program-analyzer v0.2.0

## Metadata

- skill_name: legacy-ibmi-program-analyzer
- skill_path: skills/legacy-ibmi-program-analyzer
- reviewed_version: v0.2.0
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-06-01
- target_runtime:
  - [x] Codex
  - [x] Claude Code
  - [x] OpenCode
- decision:
  - [ ] reject
  - [ ] revise
  - [x] repo-ready
  - [ ] field-pilot ready

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Checked canonical source under `skills/legacy-ibmi-program-analyzer/`.
- Updated `SKILL.md`, `templates/program-analysis.md`,
  `references/output-contract.md`, `references/error-handling-taxonomy.md`,
  `references/large-program-analysis.md`, `templates/evidence-tags.md`, and
  positive examples.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer`.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer --check`;
  Codex, Claude Code, OpenCode, and `.agents` runtime copies all reported `OK`.
- Ran `git diff --check`; no whitespace errors.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap still applies under the review gate:

- portability has been synced and drift-checked, but the skill has not been
  loaded or executed in Codex CLI, Claude Code, and OpenCode after the v0.2.0
  contract change
- runtime-smoke execution evidence remains pending

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.7 | 1.16 |
| IBM i / domain correctness | 14% | 9.6 | 1.34 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.8 | 0.98 |
| Progressive disclosure | 8% | 9.1 | 0.73 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.5 | 0.95 |
| Engineering handoff value | 8% | 9.8 | 0.78 |
| Maintainability | 6% | 9.3 | 0.56 |

Final score before cap: **9.55 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For Field Pilot

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| PROG-REV-020 | Medium | v0.2.0 has not yet been smoke-executed across Codex, Claude Code, and OpenCode. | Run the positive and negative no-write smoke protocol for v0.2.0 and update runtime evidence. | Runtime portability, reviewability |

### Improvements Completed In v0.2.0

| ID | Finding | Change Made |
| --- | --- | --- |
| PROG-REV-021 | Program analysis could still collapse calculations and branches into prose. | Added required `Logic Decomposition Ledger` for arithmetic, string construction, precision, constants, IF/SELECT/CASE, and loop rules. |
| PROG-REV-022 | Key file / key field logic was implicit in Data Touch Map. | Added required `Key File & Field Logic` with Key Files, Key Fields, and Field Lineage tables. |
| PROG-REV-023 | File I/O did not force field-level persisted mutation evidence. | Reworked File I/O into File Access Summary plus Field Mutation Matrix with assignment source, condition, and error/rollback columns. |
| PROG-REV-024 | Error handling could be reduced to partial local message prefixes. | Added Exception Closure Ledger and Message / Error Code Inventory requiring every observed `CPF*`, `CPD*`, `MCH*`, `RNX*`, `SQL*`, shop-local code, literal error code, return code, and generic handler. |
| PROG-REV-025 | Redundancy handling lacked a conservative marking surface. | Added Redundancy Candidate Notes and explicit no-delete / no-suppress rule. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

v0.2.0 materially improves SME reviewability. A reviewer can now reject output
when calculations, branch priority, key-field lineage, persisted field updates,
message IDs, generic handlers, or redundancy decisions are missing or invented.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

Adapter sync and drift checks passed on 2026-06-01. The field-pilot cap remains
because v0.2.0 has not yet been loaded and executed through all three runtimes.

## Adversarial Pass

| Scenario | Expected Behavior | Result |
| --- | --- | --- |
| Calculation compressed into "amount processing" | Reject or expand into Logic Decomposition Ledger | Covered |
| Critical field moves through alias and work variables | Require Field Lineage or create DDS/copybook TBD | Covered |
| `UPDATE` exists but assigned fields are not listed | Reject until Field Mutation Matrix names persisted fields and source values | Covered |
| `MONMSG *ANY` or bare `ON-ERROR` appears | Mark generic coverage only; do not invent specific message IDs | Covered |
| Only `UCC*` / `LCC*` messages are extracted | Reject; all observed message/error/RC families must be inventoried | Covered |
| Declared file or temporary variable looks unused | Mark conservative redundancy candidate, not deletion | Covered |

## Requested Revision Prompt For Claude Code

```text
Revise or verify legacy-ibmi-program-analyzer v0.2.0 to finish the remaining
field-pilot blocker.

Current score: 9.0/10 after the runtime-testing cap.
Static score: 9.55/10.
Target score: 9.5+/10 published.

Blocking issue:
1. Three-runtime smoke execution evidence is missing for v0.2.0.

Required changes:
- Run the positive and negative no-write smoke protocol in Codex CLI, Claude
  Code, and OpenCode.
- Verify the generated program-analysis artifact includes Logic Decomposition
  Ledger, Key File & Field Logic, Field Mutation Matrix, Exception Closure
  Ledger, and conservative Redundancy Candidate Notes.
- Update `docs/runtime-matrix.md`, `docs/skill-status-truth-table.md`, README,
  and this scorecard with exact runtime/model/date notes.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-ibmi-program-analyzer/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
