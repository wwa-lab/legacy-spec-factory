---
skill: legacy-ibmi-flow-analyzer
scorecard_version: v0.4.0
static_score: 9.51
decision: repo-ready
status: current
last_verified: 2026-07-21
runtimes_tested:
  codex: { status: synced, model: not-run, date: 2026-07-21 }
  claude_code: { status: synced, model: not-run, date: 2026-07-21 }
  opencode: { status: synced, model: not-run, date: 2026-07-21 }
evidence_source: static review + automated contract tests + adapter sync; PowerShell runtime and three-runtime prompt smoke not run
---

# Skill Review Scorecard: legacy-ibmi-flow-analyzer v0.4.0

## Metadata

- skill_name: `legacy-ibmi-flow-analyzer`
- skill_path: `skills/legacy-ibmi-flow-analyzer/`
- reviewed_version: v0.4.0
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-07-21
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

v0.4.0 replaces the historical transaction-flow reconstruction contract with
a controlled, Reader-First Program Analysis Merger. It validates a selected
set of finalized `program-analysis.md` artifacts, preserves lossless extracted
facts and coverage controls, then lets the executing LLM synthesize one
uniquely named SME/Dify Core Review.

The reviewed contract includes:

- per-program readiness at `programs[].artifact_readiness.status=ready`;
- a prepared manifest state of `review_status=ready_for_synthesis`,
  `artifact_readiness=ready`, and `merge_coverage=pending`;
- a final accepted manifest state of
  `review_status=complete_exploratory`, `artifact_readiness=ready`, and
  `merge_coverage=complete`;
- source-pack, stable-fact, thematic-anchor, coverage, naming, and stale-input
  controls;
- targeted recovery for missing or stale program artifacts without reverting
  to transaction-flow reconstruction; and
- SME/Dify-only downstream eligibility until separately governed compatibility
  migration is completed for module, BRD, and spec consumers.

## Decision

**Repo-ready, not field-pilot ready.**

The raw/static score is **9.51 / 10**. The accepted current score is capped at
**9.0 / 10** because the native Windows PowerShell path has not been executed
and the positive/negative prompt smoke has not been run in Codex, Claude Code,
and OpenCode. `synced` in this scorecard means only that the adapter copy
matches canonical source; it does not mean that the runtime loaded or executed
the skill.

## Review Evidence

- Reviewed the canonical `SKILL.md`, references, templates, examples, and
  scripts against `docs/skill-review-gate.md`.
- Confirmed that preparation, validation, readiness, blocked-queue, coverage,
  and output-layout contracts are represented by automated repository tests.
- Confirmed that final validation returns to the recorded current-run or
  explicitly approved artifact roots, re-runs per-program readiness, and
  rebuilds the expected source pack and normalized facts instead of trusting a
  coordinated edit to derived bundle files.
- Confirmed that the original SME program-list path and SHA-256 are retained as
  a final-validation trust input and reconciled against manifest order,
  normalized identities, and the sibling `program-list.txt` copy.
- Confirmed that generic material table rows and separate Supporting Detail /
  RLOG content are extracted into facts instead of disappearing behind only
  specialized Calculation, Validation, Exception, or Message parsing.
- Confirmed that included/merged facts require their ID, anchor, and typed
  values on the same visible review row; hidden comments, prose elsewhere, and
  undeclared merged groups cannot satisfy that mapping.
- Confirmed that summary/thematic mappings retain a material semantic
  fingerprint while allowing non-verbatim LLM synthesis; a generic row that
  carries only the source fact ID is rejected.
- Confirmed token-aware exact-value boundaries and evidence-backed,
  direction-sensitive cross-program relation checks across the review, not
  only in the overview section.
- Confirmed that relations to explicitly named external programs remain
  evidence-gated even for a one-program manifest, while local uses such as
  "runs validation" do not invent a cross-program edge.
- Confirmed that the lossless source pack retains the original five sections,
  while normalized facts exclude comments, hidden HTML, and structural rows
  inside fenced or indented code; escape- and code-span-aware table parsing
  preserves exact literals containing `|` without shifting later cells.
- Confirmed balanced link-target and quote-aware HTML handling, exact hidden /
  style attribute parsing, void-tag behavior, and header/separator arity checks
  prevent non-visible references or malformed tables from satisfying coverage.
- Confirmed reverse final-review reconciliation: every canonical summary/core
  row must reference known source facts, a unique visible anchor, and matching
  coverage items; invented rows and deterministic unreferenced core prose fail
  validation.
- Confirmed that duplicate YAML front-matter keys, merged self-references,
  duplicate merged IDs, and merged-ID declarations on non-merged dispositions
  fail closed.
- Confirmed that nested/case-varied forbidden full-flow headings and invented
  business-rule, service-boundary, or modernization-decision language are
  rejected.
- Confirmed that the readable flow identity is hash-suffixed, so different raw
  labels that normalize to the same first 64 characters cannot overwrite one
  another.
- Confirmed that Python and PowerShell share fixed fact-identity/parity vectors
  and equivalent static contract gates. This is static evidence only; native
  PowerShell execution remains unobserved.
- Confirmed that the canonical contract does not ask the merger to reconstruct
  a transaction flow or invent cross-program edges.
- Confirmed that observed facts, inferred synthesis, SME approval, and
  downstream modernization decisions remain distinct.
- Confirmed that runtime adapters are derived from the canonical skill and are
  recorded as `synced`, not `passed`.
- Did **not** execute the Windows PowerShell runtime.
- Did **not** execute three-runtime prompt smoke.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions apply:

- [ ] no valid `SKILL.md`
- [ ] missing or weak `name` / `description` frontmatter
- [ ] no copyright / author notice
- [ ] not portable across Codex, Claude Code, and OpenCode
- [ ] runtime-specific assumptions mixed into canonical skill
- [ ] no clear trigger conditions
- [ ] no clear output contract
- [ ] no SME review or evidence governance for IBM i reverse engineering
- [ ] hallucination-prone instructions

The 9.0 runtime-test cap applies because portability has been designed and the
adapters are synchronized, but the PowerShell runtime and all three target
runtime prompt scenarios remain unexecuted.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.9 | 0.99 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.7 | 1.36 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 9.9 | 0.99 |
| Progressive disclosure | 8% | 9.0 | 0.72 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 10.0 | 1.00 |
| Engineering handoff value | 8% | 9.5 | 0.76 |
| Maintainability | 6% | 7.0 | 0.42 |

Final raw/static score before cap: **9.51 / 10**

Final accepted score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking Findings

No finding blocks repository acceptance. The following findings block the
field-pilot label.

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| FLOW-040-RT-001 | Medium | Native Windows PowerShell 5.1 build and validation paths have not been executed. | Run the PowerShell runtime suite on a supported Windows host and compare its outputs and exit behavior with the Python path. | Runtime portability |
| FLOW-040-RT-002 | Medium | Positive and negative prompt smoke has not been executed in Codex, Claude Code, and OpenCode. | Run the v0.4.0 prompt protocol in all three runtimes and record contract-compliant outputs without upgrading a runtime above the observed result. | Field-pilot readiness |

### Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| FLOW-040-GOLD-003 | The active ready and blocked examples document the contract, while a frozen end-to-end generated golden bundle is not yet approved. | Add one representative generated bundle and SME review record before field pilot. |
| FLOW-040-MIG-004 | Module, BRD, and spec consumers have not been migrated to the v0.4.0 merger contract. | Keep output eligibility limited to SME/Dify review until each downstream consumer has an explicit compatibility contract and regression evidence. |
| FLOW-040-DISC-005 | Historical transaction-flow references remain for migration context, increasing the surface a maintainer must distinguish from the active contract. | Retire or archive the historical surfaces after dependent documentation and consumers complete migration. |
| FLOW-040-MAINT-006 | `scripts/program_set_core_review.py` remains over 4,600 lines, well above the repository's 800-line file guideline, even after identity, Markdown, reader-first, and review-safety helpers were extracted. | Continue splitting preparation, trust-root revalidation, fact extraction, and final reconciliation behind the stable CLI; add focused tests at each module boundary. |

## Strengths

- The skill has a sharply bounded purpose: merge finalized reader-first
  program analyses without pretending to rediscover the transaction path.
- Readiness and final-completion states are explicit and machine-checkable.
- Lossless source facts, stable IDs, thematic coverage, and SME review controls
  make omissions and unsupported synthesis visible.
- Missing/stale recovery is targeted: only fresh exact mappings enter the
  scan queue, while unresolved rows stay in the blocked CSV.
- Unique flow-plus-program-set identity prevents unrelated selected sets from
  overwriting one another.
- Final validation re-resolves current/approved artifacts and re-runs
  readiness; source-pack/fact/coverage edits cannot silently redefine the
  trusted input set.
- Generic thematic content and supporting detail retain visible same-row
  coverage, while strict token and relation gates reject substring or
  wrong-direction evidence laundering.

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes: the final artifact is exploratory and requires selected program-set
review. It is eligible for SME/Dify review, not automatic BRD/spec approval or
a modernization decision.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes: all adapters are recorded as `synced`. No adapter is recorded as
`loaded`, `executed`, or `passed`. The PowerShell runtime and three-runtime
prompt smoke were not run for this review.

## Requested Field-Pilot Hardening

1. Run the native Windows PowerShell build and validation scenarios, including
   ready, blocked, stale, partial-draft, and zero-pending final validation.
2. Run positive and negative prompt smoke in Codex, Claude Code, and OpenCode.
3. Freeze one generated ready bundle and one blocked recovery bundle, then
   obtain SME review evidence.
4. Re-score only after the runtime matrix contains observed execution results;
   never infer `passed` from adapter sync or static tests.
