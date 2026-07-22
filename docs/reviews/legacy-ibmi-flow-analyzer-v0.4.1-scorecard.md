---
skill: legacy-ibmi-flow-analyzer
scorecard_version: v0.4.1
static_score: 9.58
decision: repo-ready
status: current
last_verified: 2026-07-22
runtimes_tested:
  codex: { status: synced, model: not-run, date: 2026-07-22 }
  claude_code: { status: synced, model: not-run, date: 2026-07-22 }
  opencode: { status: synced, model: not-run, date: 2026-07-22 }
evidence_source: static review + 384 automated tests + adapter sync check; native PowerShell and three-runtime prompt smoke not run
---

# Skill Review Scorecard: legacy-ibmi-flow-analyzer v0.4.1

## Metadata

- skill_name: `legacy-ibmi-flow-analyzer`
- skill_path: `skills/legacy-ibmi-flow-analyzer/`
- reviewed_version: v0.4.1
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-07-22
- target_runtime:
  - [x] Codex
  - [x] Claude Code
  - [x] OpenCode
- decision:
  - [ ] reject
  - [ ] revise
  - [x] repo-ready
  - [ ] field-pilot ready

## Change Under Review

v0.4.1 hardens the upstream large-program path used by the merger. Normal and
complex programs retain the shared reader-first contract; `large_extreme_program`
receives an explicit deep-read execution contract. Deterministic indexing and
precreated files are scaffolds only. A frozen execution plan allocates every
source window, RLOG, and retained batch, and terminal batch validation requires
all planned work to be source-backed, semantically complete, consolidated, and
covered by the program-analysis validator.

The batch initializer records source-index and execution-plan SHA-256 locks in
the manifest. Python and PowerShell validators compare those locks, verify
window-to-RLOG mappings and source inventory bindings, reject missing/extra/
duplicate batches, and reject pending or generic filler. The flow merger still
blocks until every distinct program is ready and its source facts have complete
coverage; missing programs receive a targeted recovery queue.

## Decision

**Repo-ready, not field-pilot ready.**

The raw/static score is **9.58 / 10**. The accepted score is capped at **9.0 /
10** because this macOS host has no native Windows PowerShell runtime and no
positive/negative prompt smoke has been executed in all three target runtimes.
Adapter sync is evidence of parity only, not evidence that a runtime loaded or
executed the skill.

## Mandatory Stop Conditions

No mandatory 8.0 cap condition applies. The canonical source has valid
frontmatter, author notice, explicit triggers and outputs, IBM i SME governance,
and portable runtime adapters.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.9 | 0.99 |
| Workflow completeness | 12% | 9.9 | 1.18 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 9.9 | 0.99 |
| Progressive disclosure | 8% | 9.2 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 10.0 | 1.00 |
| Engineering handoff value | 8% | 9.6 | 0.77 |
| Maintainability | 6% | 7.5 | 0.45 |

Final raw/static score: **9.58 / 10**

Final accepted score after runtime cap: **9.0 / 10**

## Review Evidence

- `python3 -m unittest discover -s tests -q` passed: **384 tests**, **47
  skipped** because native PowerShell/runtime smoke is unavailable here.
- Large-program negative tests cover deleted later batches, source/plan
  co-tampering, RLOG remapping, generic filler, pending seed state, unsafe
  declared paths, duplicate coverage, and missing terminal locks.
- Large-program prompt generation is tier-specific in both Python and
  PowerShell: it requires the immutable plan, exact batch/window/RLOG coverage,
  source-line citations, consolidation, and a passing validator.
- Python and PowerShell indexers emit the canonical deep-read execution plan;
  the plan and source-index hashes are frozen during `precreate` batch setup.
- Flow readiness and final revalidation call the upstream program validator and
  block partial/pending large programs; recovery output contains targeted next
  actions instead of silently accepting a shell.
- `scripts/sync-skills.sh --target all --check` passed for
  `legacy-ibmi-flow-analyzer`, `legacy-ibmi-program-analyzer`, and
  `legacy-ibmi-program-list-batch` across all four adapter directories.
- `git diff --check` passed after the final edits.

## Blocking Findings

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| FLOW-041-RT-001 | Medium | Native Windows PowerShell 5.1 execution was not available on this host. | Run the initializer, worker/merge, terminal status validator, and upstream validator on a supported Windows host. | Runtime portability |
| FLOW-041-RT-002 | Medium | Positive and negative prompt smoke was not executed in Codex, Claude Code, and OpenCode. | Run the runtime smoke protocol and record observed results before field-pilot approval. | Field-pilot readiness |

No code-level blocker remains for repository acceptance.

## Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| FLOW-041-GOLD-001 | No frozen, SME-approved large-program golden bundle is stored in the repository. | Add one complete multi-batch ready bundle and one blocked recovery bundle before field pilot. |
| FLOW-041-MAINT-002 | Several legacy compatibility scripts remain large. | Continue splitting stable CLI boundaries into focused modules while preserving current contracts. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Large-program semantic completion remains evidence-backed and SME-reviewable;
an index, checkpoint, or model self-declaration cannot promote a row to ready.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter defined and synchronized
- [x] OpenCode adapter defined and synchronized
- [x] Codex adapter defined and synchronized
- [x] runtime-specific metadata isolated from canonical skill

Native PowerShell and target-runtime prompt execution remain unobserved, so the
scorecard does not claim field-pilot readiness.

## Requested Field-Pilot Hardening

1. Execute the Windows PowerShell matrix, including ready, pending, deleted
   batch, plan/source mismatch, remapped RLOG, and terminal-lock failures.
2. Run positive and negative prompt smoke in Codex, Claude Code, and OpenCode.
3. Freeze a representative complete large-program bundle and its SME review.
4. Re-score only from observed runtime evidence; never infer execution from
   adapter sync or static tests.
