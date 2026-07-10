# Skill Review Scorecard

## Metadata

- skill_name: legacy-ibmi-program-analyzer
- skill_path: skills/legacy-ibmi-program-analyzer/
- reviewed_version: v0.2.18
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

No mandatory stop condition applies. Evidence, SME, anti-hallucination,
reader-first, output, and handoff contracts remain enforceable.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 10.0 | 1.00 |
| Workflow completeness | 12% | 9.5 | 1.14 |
| IBM i / domain correctness | 14% | 9.5 | 1.33 |
| Evidence and anti-hallucination | 12% | 10.0 | 1.20 |
| Output contract | 10% | 9.5 | 0.95 |
| Progressive disclosure | 8% | 8.5 | 0.68 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.5 | 0.95 |
| Engineering handoff value | 8% | 9.5 | 0.76 |
| Maintainability | 6% | 9.0 | 0.54 |

Raw weighted score: 9.45 / 10.

Final score: **9.0 / 10**, capped pending successful Windows PowerShell 5.1
runtime execution in CI/Cline.

## Findings

### Blocking Findings

None for repository integration.

### Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| IMP-001 | Native indexer and validator runtime cases are skipped on the macOS development host. | Require the Windows CI job to pass before field pilot. |
| IMP-002 | Static source extraction is intentionally conservative and still needs representative company-program parity evidence. | Compare Python and PowerShell artifacts for normal, complex, and large field fixtures. |

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

The native PowerShell indexer and validator use Windows PowerShell 5.1 and
built-in .NET APIs only. Field-pilot approval remains blocked until Windows CI,
artifact parity, and company Cline smoke tests pass.
