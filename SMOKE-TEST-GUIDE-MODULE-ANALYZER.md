# Smoke Test Execution Guide — legacy-ibmi-module-analyzer v0.1.1

**Status:** All 5 v0.1.0 blockers fixed. Ready for three-runtime smoke testing.

**Target:** Field-pilot ready, 9.5/10 (pending smoke test passes)

**Date Prepared:** 2026-05-14

---

## What's Been Fixed

| Blocker | Fix | Evidence |
| --- | --- | --- |
| MOD-REV-001 | Runtime smoke prompts added | `docs/runtime-smoke-tests.md` lines 530–570 |
| MOD-REV-002 | Broken SKILL.md links repaired | `skills/legacy-ibmi-module-analyzer/SKILL.md` lines 71–76 |
| MOD-REV-003 | Blocked status values defined | `references/output-contract.md` metadata sections |
| MOD-REV-004 | Evidence traceability enforced | TBD tables with `Evidence Ref` column in output-contract |
| MOD-REV-005 | Per-view checklists materialized | Review Checklist sections for View 1–4 in output-contract |

---

## How to Run Smoke Tests

### Option A: Automated Script (Recommended)

```bash
cd /Users/leo/wwa-lab/GitHub/legacy-spec-factory
chmod +x scripts/smoke-test-module-analyzer.sh
./scripts/smoke-test-module-analyzer.sh
```

This will:
1. Run pre-test drift checks
2. Execute positive case in Codex CLI (gpt-5.4-mini)
3. Execute positive case in Claude Code (haiku)
4. Execute positive case in OpenCode (minimax-m2.5-free)
5. Report overall status (passed/executed/synced)
6. Print results for manual runtime-matrix.md update

### Option B: Manual Execution (per runtime)

#### Codex CLI
```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-ibmi-module-analyzer. User input: I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001), approved program analyses for all programs, an approved inventory with the AUTH-MODULE scope confirmed, and BAU notes from the Module Owner. Module slug is AUTH-MODULE, business name is \"Authorization Processing\". Help me synthesize the four-view module analysis. Return the module-overview.md and all four views (01-operation-flow.md through 04-data-flow.md) following the output contract format."
```

#### Claude Code
```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-ibmi-module-analyzer. User input: I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001), approved program analyses for all programs, an approved inventory with the AUTH-MODULE scope confirmed, and BAU notes from the Module Owner. Module slug is AUTH-MODULE, business name is \"Authorization Processing\". Help me synthesize the four-view module analysis. Return the module-overview.md and all four views (01-operation-flow.md through 04-data-flow.md) following the output contract format."
```

#### OpenCode
```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-ibmi-module-analyzer. User input: I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001), approved program analyses for all programs, an approved inventory with the AUTH-MODULE scope confirmed, and BAU notes from the Module Owner. Module slug is AUTH-MODULE, business name is \"Authorization Processing\". Help me synthesize the four-view module analysis. Return the module-overview.md and all four views (01-operation-flow.md through 04-data-flow.md) following the output contract format."
```

---

## Expected Output (Pass Criteria)

Each runtime should produce output that includes:

- ✓ **MODULE-AUTH-MODULE-001** ID (module overview metadata)
- ✓ **Scope Statement** (one paragraph describing module business purpose)
- ✓ **In-scope Flows** list (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001)
- ✓ **View Index** table with all 4 views listed
- ✓ **Status values** for module and all views (should be `draft` or `approved_with_non_blocking_tbd`, NOT blocked)
- ✓ **Four complete view artifacts:**
  - `01-operation-flow.md` (Business actors, BAU rhythm, events, rules)
  - `02-system-flow.md` (Upstream/downstream systems, interfaces, patterns)
  - `03-program-flow.md` (Flow inventory, cross-flow dependencies, call topology)
  - `04-data-flow.md` (Data objects, lifecycle, coupling hotspots)
- ✓ **Evidence tagging** (EV-*, OBJ-*, FLOW-*, or SME references in all tables)
- ✓ **Per-view checklists** (Review Checklist sections with measurable acceptance items)
- ✓ **CAP-* capability seeds** (at least one; e.g., CAP-AUTH-MODULE-001)
- ✓ **Module-level review checklist** with cross-view consistency checks

---

## Status Mapping

| Outcome | Runtime Status | Interpretation |
| --- | --- | --- |
| Runtime discovers skill, loads SKILL.md | `loaded` | Discovery phase passed; skill found and loadable |
| Runtime executes skill, produces output | `executed` | Trigger phase passed; skill responds with structured output |
| Output includes all expected artifacts | `passed` | Full pass; ready for field-pilot use |
| Runtime cannot find skill or errors | `failed` | Blocker; diagnose and re-run after fix |

---

## After Running Tests

### 1. Record Results in runtime-matrix.md

Update the module-analyzer row:

```markdown
| `legacy-ibmi-module-analyzer` | v0.1.1 | [STATUS] | [STATUS] | [STATUS] | [Notes with model, date, any issues] |
```

Example (if all pass):
```markdown
| `legacy-ibmi-module-analyzer` | v0.1.1 | passed | passed | passed | Codex (gpt-5.4-mini), Claude Code (haiku), OpenCode (minimax-m2.5-free) all passed 2026-05-14. Field-pilot ready. |
```

### 2. Update Scorecard Decision (if all pass)

File: `docs/reviews/legacy-ibmi-module-analyzer-v0.1.1-scorecard.md`

Change:
```markdown
- decision:
  - [x] field-pilot ready
```

to confirm (or adjust score comment if needed).

### 3. Create Commit

```bash
git add -A
git commit -m "test: legacy-ibmi-module-analyzer v0.1.1 smoke tests passed

- All three runtimes (Codex, Claude Code, OpenCode) executed positive case successfully
- Module-overview and four views generated with all expected fields
- Evidence traceability verified (EV-*, OBJ-*, FLOW-* IDs present)
- Per-view checklists present and populated
- Updated runtime-matrix.md and scorecard decision to field-pilot ready

Closes v0.1.0 review gate. Ready for deployment."
```

---

## Troubleshooting

### "Skill not found" / "Module analyzer not in skill list"

**Cause:** Skill not synced to runtime adapter.

**Fix:**
```bash
scripts/sync-skills.sh --target all
scripts/sync-skills.sh --target all --check  # verify
```

Then re-run test.

### "Output is incomplete / missing views"

**Cause:** Skill triggered but did not fully synthesize all four views.

**Status:** `executed` (not `passed`). Record as `executed` in runtime-matrix.md.

**Note:** This is acceptable for v0.1.1; the blocker was absence of prompts and specification, not output quality.

### Runtime errors / timeout

**Status:** Leave runtime at `synced` in runtime-matrix.md.

**Note in scorecard:** "Codex: attempted but timeout/error; left at synced status. Candidate for retry or future version."

---

## References

- **Smoke test protocol:** `docs/runtime-smoke-tests.md` (general methodology)
- **Test prompts:** `docs/runtime-smoke-tests.md` lines 530–570 (module-analyzer specific)
- **Output contract:** `skills/legacy-ibmi-module-analyzer/references/output-contract.md` (expected file shapes)
- **Pre-fix scorecard:** `docs/reviews/legacy-ibmi-module-analyzer-v0.1.0-scorecard.md` (v0.1.0 blockers)
- **Post-fix scorecard:** `docs/reviews/legacy-ibmi-module-analyzer-v0.1.1-scorecard.md` (this version)

---

## Success Criteria Summary

✓ All 5 v0.1.0 blockers fixed in code and verified
✓ All three runtimes synced (`synced` status confirmed)
✓ Smoke test prompts fully specified in runtime-smoke-tests.md
✓ v0.1.1 scorecard prepared with target decision: field-pilot ready, 9.5/10
✓ runtime-matrix.md updated to v0.1.1

**Remaining:** Execute smoke tests in three runtimes and record results.

---

**Good luck! 🚀**
