---
skill: legacy-ibmi-program-analyzer
scorecard_version: v0.2.1
static_score: 9.58
decision: repo-ready
status: current
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-program-analyzer v0.2.1

## Metadata

- skill_name: legacy-ibmi-program-analyzer
- skill_path: skills/legacy-ibmi-program-analyzer
- reviewed_version: v0.2.1
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-06-02
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
- Updated canonical `skills/legacy-ibmi-program-analyzer/` first.
- Updated `SKILL.md`, `templates/program-analysis.md`,
  `references/output-contract.md`, and positive examples.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer`.
- Ran `scripts/sync-skills.sh --skill legacy-ibmi-program-analyzer --check`;
  Codex, Claude Code, OpenCode, and `.agents` runtime copies all reported `OK`.
- Scanned canonical and runtime copies for retired report headings/table
  shapes; no old call-tree, call-edge, external-call, File I/O, or message
  inventory headings remain.
- Ran a Markdown table column consistency check for the canonical template,
  output contract, and examples; passed.
- Ran `git diff --check`; no whitespace errors.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap still applies under the review gate:

- v0.2.1 has been synced and statically checked, but has not yet been
  smoke-executed across Codex CLI, Claude Code, and OpenCode.
- Runtime smoke execution evidence remains pending.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.7 | 1.36 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.9 | 0.99 |
| Progressive disclosure | 8% | 9.1 | 0.73 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.6 | 0.96 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.4 | 0.56 |

Final score before cap: **9.58 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For Field Pilot

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| PROG-REV-030 | Medium | v0.2.1 has not yet been smoke-executed across Codex, Claude Code, and OpenCode. | Run the positive and negative no-write smoke protocol for v0.2.1 and update runtime evidence. | Runtime portability, reviewability |

### Improvements Completed In v0.2.1

| ID | Finding | Change Made |
| --- | --- | --- |
| PROG-REV-031 | Program Call Map repeated a visual tree and did not force auditable call evidence. | Replaced the tree-style subsection with `Call Evidence` including caller, callee, call type, condition, source lines, evidence source, and resolution. |
| PROG-REV-032 | Field output could drop source identifiers or business meaning. | Required `FIELD_NAME` (business meaning) and `VARIABLE_NAME` (business meaning) [direction], with explicit inferred/unresolved patterns. |
| PROG-REV-033 | File I/O mixed field meaning into purpose text. | Added File Access Summary `Purpose` and required key fields to retain source identifier plus business meaning. |
| PROG-REV-034 | Dynamic and external calls lacked resolution status. | Added caller routine, source lines, parameters, purpose, evidence, and resolution status for external/dynamic calls. |
| PROG-REV-035 | Error handling could still summarize instead of inventorying codes. | Replaced message/code inventory with `Error Code Inventory` covering code, meaning, type, source lines, trigger, carrier, downstream effect, and evidence status. |
| PROG-REV-036 | Open items were scattered through the report. | Added centralized `Open Items / Limitations` table under `TBDs & Blocking Status`. |
| PROG-REV-037 | Routine descriptions did not force variable-level data flow. | Added `Routine / Window Data Flow` with inputs, transformations, outputs, side effects, source lines, and evidence. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags and resolution labels are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

v0.2.1 improves SME reviewability by making every important conclusion trace
back to source identifiers, business meaning, source lines or evidence basis,
and confirmed / inferred / unresolved status.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

Adapter sync and drift checks passed on 2026-06-02. The field-pilot cap remains
because v0.2.1 has not yet been loaded and executed through all three runtimes.

## Adversarial Pass

| Scenario | Expected Behavior | Result |
| --- | --- | --- |
| Output lists "card number" without `K0CRNO` | Reject or rewrite with source identifier + business meaning | Covered |
| Dynamic call target comes from a variable | Mark `dynamic_unresolved` unless target assignment is proven | Covered |
| File I/O Purpose says only "lookup" while Key Fields hold business descriptions | Reject; Purpose must state file access behavior and Key Fields must hold identifiers + meanings | Covered |
| Error handling says "errors are handled" without code inventory | Reject; Error Code Inventory is required | Covered |
| Routine summary omits input/output variables | Reject or expand Routine / Window Data Flow | Covered |
| Long identifiers render broken in tables | Use backticks, explicit line breaks, or summary/detail split | Covered |

## Requested Revision Prompt For Claude Code

```text
Verify legacy-ibmi-program-analyzer v0.2.1 with three-runtime smoke execution.

Current score: 9.0/10 after the runtime-testing cap.
Static score: 9.58/10.
Target score: 9.5+/10 published.

Blocking issue:
1. Three-runtime smoke execution evidence is missing for v0.2.1.

Required changes:
- Run the positive and negative no-write smoke protocol in Codex CLI, Claude
  Code, and OpenCode.
- Verify the generated program-analysis artifact includes Call Evidence,
  field/variable source identifiers with business meanings, File I/O Purpose,
  external/dynamic call resolution status, Error Code Inventory,
  Routine / Window Data Flow, and Open Items / Limitations.
- Update `docs/runtime-matrix.md`, `docs/skill-status-truth-table.md`, README,
  and this scorecard with exact runtime/model/date notes.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-ibmi-program-analyzer/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
