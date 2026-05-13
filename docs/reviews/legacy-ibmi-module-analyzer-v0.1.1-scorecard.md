# Skill Review Scorecard: legacy-ibmi-module-analyzer v0.1.1

## Metadata

- skill_name: legacy-ibmi-module-analyzer
- skill_path: skills/legacy-ibmi-module-analyzer
- reviewed_version: v0.1.1
- generated_by: Claude Code
- reviewed_by: Claude Code; corrected_by: Codex
- review_date: 2026-05-14
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

- Reviewed all five blocking findings from v0.1.0 scorecard
- Verified canonical source under `skills/legacy-ibmi-module-analyzer/`
- Checked `SKILL.md`, templates, references, examples
- Fixed broken links in SKILL.md pointing to non-existent per-view reference files
- Added `blocked_pending_source` and `blocked_pending_sme` status values
- Added per-view review checklists (View 1-4) with measurable acceptance items
- Strengthened evidence traceability with TBD ID and Evidence Ref columns
- Added positive and negative smoke test prompts to `docs/runtime-smoke-tests.md`
- Ran `scripts/sync-skills.sh --target all --check`; all runtime adapter copies reported `OK`
- Sanitized output-contract examples to use generic AUTH-MODULE placeholders
- Verified `docs/runtime-matrix.md` shows all target runtimes as `synced`
- Codex correction pass removed the premature field-pilot-ready claim because
  smoke execution evidence has not been recorded yet

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 runtime cap still applies for v0.1.1 until three-runtime smoke execution
evidence is recorded:

- All v0.1.0 review findings have been addressed
- Broken links repaired and verified (references now point to existing files)
- Blocked status values defined and documented across all views
- Per-view checklists fully materialized (not just placeholders)
- Evidence traceability strengthened with explicit TBD and Evidence Ref fields
- Smoke test prompts fully specified in `docs/runtime-smoke-tests.md`
- All three runtimes synced and ready for smoke test execution
- Output-contract examples sanitized to prevent information leakage

**Remaining condition:** three-runtime smoke test execution. Until Codex,
Claude Code, and OpenCode have recorded `executed` or `passed` evidence, this
skill is repo-ready but not field-pilot ready.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.2 | 1.10 |
| IBM i / domain correctness | 14% | 9.3 | 1.30 |
| Evidence and anti-hallucination | 12% | 9.5 | 1.14 |
| Output contract | 10% | 9.2 | 0.92 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.2 | 0.92 |
| Engineering handoff value | 8% | 9.2 | 0.74 |
| Maintainability | 6% | 9.2 | 0.55 |

Static score before runtime cap: **9.27 / 10**

Current score after runtime cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For 9.5 (v0.1.0) - STATIC FIXES RESOLVED

| ID | Finding | Resolution | Status |
| --- | --- | --- | --- |
| MOD-REV-001 | Runtime smoke prompts and execution evidence missing | Added positive and negative prompts to `docs/runtime-smoke-tests.md` with pass criteria; execution evidence still pending | PARTIAL - prompts fixed, execution pending |
| MOD-REV-002 | SKILL.md links nonexistent per-view reference files | Updated SKILL.md to reference only existing `output-contract.md` and `synthesis-rules.md` | FIXED |
| MOD-REV-003 | Blocked-module status inconsistent | Added `blocked_pending_source` and `blocked_pending_sme` to output contract and view templates | FIXED |
| MOD-REV-004 | Evidence traceability not enforceable | Added TBD ID, Evidence Ref, and Blocking columns to output contract per-view tables | FIXED |
| MOD-REV-005 | Per-view checklists not materialized | Added explicit per-view Review Checklist sections to output contract for all four views | FIXED |

### Strengths

- The four-view synthesis model remains well-aligned with `docs/module-analysis-model.md`
- Stop conditions are clear: missing flow analyses, ambiguous module boundary, missing SME confirmation, missing BAU notes all properly block synthesis
- Anti-hallucination language is specific: business actors, BAU rhythm, system interfaces, regulatory claims, and business-rule seeds require SME or source evidence
- Cross-view consistency checks create useful handoff pressure before `legacy-spec-writer` consumes capability seeds
- Per-view checklists now enforce measurable acceptance criteria (actor completeness, evidence linking, SLA accuracy, etc.)
- Blocked status values clarify when module-overview-only (incomplete) is the correct output
- Evidence columns force explicit linking to EV-*, OBJ-*, FLOW-*, or SME note IDs
- Output contract examples now use generic AUTH-MODULE placeholders for security

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required (now enforceable via table columns)
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward

Notes:

The skill correctly treats SMEs as the authority for module boundaries, BAU rhythm, manual procedures, operational exception handling, integration intent, and approval. Per-view checklists now provide a practical verification tool for each SME reviewer to confirm artifact correctness before sign-off.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

All three runtime adapters synced and verified with `scripts/sync-skills.sh --target all --check`. No drift detected. Output-contract placeholders are sanitized in all synced copies for security compliance.

**Smoke testing status:** Positive and negative test prompts ready in `docs/runtime-smoke-tests.md`. Three runtimes are at `synced` status only. Smoke test execution must confirm `loaded`, `executed`, and preferably `passed` status before the runtime cap can be lifted.

## Adversarial Pass

| Scenario | Expected Behavior | v0.1.0 Result | v0.1.1 Status |
| --- | --- | --- | --- |
| One in-scope flow lacks approved analysis | Stop, produce blocked overview, route to flow-analyzer | Covered by negative example | Now explicitly tested in smoke prompts |
| SME owner / BAU notes missing | Stop, do not invent Operation Flow | Covered | Unchanged |
| Blocked status handling | Emit blocked_pending_source or _sme, not all four views | Referenced but inconsistent across files | Status values now defined and enforced |
| Per-view methodology reference | Follow links to per-view guidance | Broken links; files did not exist | Links repaired; references real files |
| Per-view evidence requirement | Every claim links to evidence ID | Generic prose; not enforceable | Evidence Ref column enforces linking |
| Per-view acceptance criteria | Reviewers know when view is complete | Placeholder checklist references | Explicit measurable checklist items |
| Cross-view consistency | All actors, systems, rules, data objects linked | Covered by SKILL.md logic | Unchanged |
| Runtime adapter following SKILL.md | Agent correctly loads and interprets skill | Structurally sound but untested | Ready for smoke test validation |

## Requested Revision Prompt (v0.1.0) - COMPLETED

All items from v0.1.0's revision prompt have been addressed:

1. Added `legacy-ibmi-module-analyzer` positive and negative prompts to `docs/runtime-smoke-tests.md`
2. Fixed progressive-disclosure links in SKILL.md
3. Added `blocked_pending_source` and `blocked_pending_sme` to output contract and templates
4. Added required `evidence_ids`, TBD references, and review-status fields to output contract
5. Added measurable per-view review checklist sections to output contract and template
6. Ran `scripts/sync-skills.sh --target all` and verified `--check` passes
7. Smoke protocol ready in three runtimes (execution pending)

## Next Steps

1. **Run smoke tests** in Codex CLI, Claude Code, and OpenCode using positive case prompt
2. **Update `docs/runtime-matrix.md`** with runtime status (`loaded`, `executed`, or `passed`) and exact model/date
3. **Confirm all pass criteria** for positive (4-view synthesis complete, all fields populated, evidence tagged) and negative (blocked status, no partial synthesis)
4. **Re-score the skill** and lift the runtime cap only if smoke evidence supports it

**Expected outcome after successful smoke evidence:** v0.1.1 can be considered
for field-pilot readiness and a 9.5+ score.

## Sign-Off

- **Review Status:** Post-revision, repo-ready, awaiting smoke test confirmation
- **Ready for Smoke Testing:** YES
- **Expected Score Post-Smoke:** 9.5/10 target, subject to actual smoke results
- **Date Completed:** 2026-05-14
