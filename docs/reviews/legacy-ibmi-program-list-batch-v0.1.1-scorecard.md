# Skill Review Scorecard

## Metadata

- skill_name: legacy-ibmi-program-list-batch
- skill_path: skills/legacy-ibmi-program-list-batch/
- reviewed_version: v0.1.1
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-07-10
- target_runtime:
  - [x] Codex
  - [x] Claude Code
  - [x] OpenCode
- decision:
  - [ ] reject
  - [ ] revise
  - [x] repo-ready
  - [ ] field-pilot ready

## Mandatory Stop Conditions

No mandatory stop condition applies. Canonical source, authorship, trigger,
output contract, SME/evidence controls, and adapters remain present.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 10.0 | 1.00 |
| Workflow completeness | 12% | 9.5 | 1.14 |
| IBM i / domain correctness | 14% | 9.0 | 1.26 |
| Evidence and anti-hallucination | 12% | 9.0 | 1.08 |
| Output contract | 10% | 9.5 | 0.95 |
| Progressive disclosure | 8% | 9.0 | 0.72 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.0 | 0.90 |
| Engineering handoff value | 8% | 9.0 | 0.72 |
| Maintainability | 6% | 9.0 | 0.54 |

Raw weighted score: 9.21 / 10.

Final score: **9.0 / 10**, capped pending successful Windows PowerShell 5.1
runtime execution in CI/Cline.

## Findings

### Blocking Findings

None for repository integration.

### Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| IMP-001 | Native PowerShell tests are defined but skipped on the macOS development host. | Require the Windows CI job to pass before field pilot. |
| IMP-002 | Field Cline shell integration and corporate execution policy remain environment-specific. | Run the prompt dry-run plan on the company Windows 11 image. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter synced
- [x] OpenCode adapter synced
- [x] Codex adapter synced
- [x] runtime-specific behavior implemented as portable repository scripts

The native PowerShell initializer and validator use Windows PowerShell 5.1
built-ins only. Field-pilot approval remains blocked until the Windows runtime
job and company Cline smoke test pass.
