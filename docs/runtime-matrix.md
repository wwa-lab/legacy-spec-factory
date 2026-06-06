# Runtime Matrix

Track where each canonical skill has been synced and tested across Codex,
Claude Code, and OpenCode.

**Single source of truth for reviewed readiness**:
[`docs/skill-status-truth-table.md`](skill-status-truth-table.md). This file
is the runtime-status view of that table, and it may list a newer synced
canonical skill version only when the row explicitly says the updated
scorecard is pending. Run `scripts/verify-skill-claims.py` to confirm they
agree.

Any change to `skills/` must update this matrix in the same PR or commit.

## Schema

| Column | Meaning |
| --- | --- |
| Skill | Canonical skill name |
| Version | Canonical version under test |
| Codex / Claude Code / OpenCode | Status enum: `not tested`, `synced`, `loaded`, `executed`, `passed`, `failed` |
| Evidence | Path to current scorecard with smoke-test record |
| Last Verified | Most recent date the runtime status was confirmed |
| Notes | Free-text outcome summary |

## Status Values

| Status | Meaning |
| --- | --- |
| `not tested` | adapter sync not yet attempted |
| `synced` | adapter folder exists, content matches canonical |
| `loaded` | runtime discovered the skill but did not complete the scenario |
| `executed` | runtime completed the scenario with the right shape |
| `passed` | runtime completed the scenario and met every pass criterion |
| `failed` | runtime could not discover the skill or violated a hard gate |

A skill is **field-pilot ready** only when all three runtimes are at `passed`
AND the scorecard records sign-off. Any non-`passed` row caps the published
score at 9.0.

## Models Used

| Runtime | Model |
| --- | --- |
| Codex CLI | `gpt-5.4-mini` (read-only ephemeral) |
| Claude Code | `haiku` (Read-only tools) |
| OpenCode | `minimax-m2.5-free` |

## Matrix

| Skill | Version | Codex | Claude Code | OpenCode | Evidence | Last Verified | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `legacy-modernization-orchestrator` | v0.2.14 | synced | synced | synced | [scorecard](reviews/legacy-modernization-orchestrator-v0.2.11-scorecard.md) | 2026-06-04 | v0.2.14 aligns routing with module-analyzer v0.2.4 focused package; updated scorecard pending and expanded-route execution still needed. |
| `legacy-module-context-intake` | v0.1.12 | synced | synced | synced | [scorecard](reviews/legacy-module-context-intake-v0.1.7-scorecard.md) | 2026-06-05 | v0.1.12 retires the separate flow-context normalizer path; reviewed v0.1.7 scorecard remains the current readiness record; updated scorecard pending and execution smoke pending. |
| `legacy-document-evidence-intake` | v0.1.5 | synced | synced | synced | [scorecard](reviews/legacy-document-evidence-intake-v0.1.0-scorecard.md) | 2026-06-05 | v0.1.5 adds managed-Python setup recovery and model-visible PDF/image visual-review fallback; reviewed v0.1.0 scorecard remains the current readiness record; updated scorecard pending and execution smoke pending. |
| `legacy-ibmi-evidence-intake` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-ibmi-evidence-intake-v0.1.0-scorecard.md) | 2026-05-15 | Full positive and negative smoke rerun. Claude Code initially hung in default Codex sandbox (EPERM on Claude config); rerun with auth/config/network access passed. |
| `legacy-ibmi-inventory` | v0.3.1 | synced | synced | synced | [scorecard](reviews/legacy-ibmi-inventory-v0.1.0-scorecard.md) | 2026-06-05 | v0.3.1 clarifies normalized document/context packages as evidence sources; reviewed v0.1.0 scorecard remains the current readiness record; updated scorecard pending and execution smoke pending. |
| `legacy-ibmi-runtime-evidence-miner` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-ibmi-runtime-evidence-miner-v0.1.0-scorecard.md) | 2026-05-16 | Positive and negative no-write smoke passed in Codex CLI (`gpt-5.4-mini`), Claude Code (`haiku`), and OpenCode (`opencode/minimax-m2.5-free`) in a disposable temp copy. Frontmatter/discoverability fixed; single-run runtime evidence stays below high confidence and does not become a schedule claim. |
| `legacy-ibmi-program-analyzer` | v0.2.7 | synced | synced | synced | [scorecard](reviews/legacy-ibmi-program-analyzer-v0.2.5-scorecard.md) | 2026-06-04 | v0.2.7 front-loads Calculation Logic, Validation Logic, Exception Handling, and Message Inventory before Metadata for IT SME first-read review; updated scorecard pending. |
| `legacy-ibmi-data-model-analyzer` | v0.1.0 | passed | synced | passed | [scorecard](reviews/legacy-ibmi-data-model-analyzer-v0.1.0-scorecard.md) | 2026-05-16 | Codex and OpenCode passed positive/negative no-write smoke. Claude Code blocked by `Not logged in - Please run /login`; field-pilot remains blocked. |
| `legacy-ibmi-screen-report-analyzer` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-ibmi-screen-report-analyzer-v0.1.0-scorecard.md) | 2026-05-16 | Positive no-write DSPF smoke passed in all three runtimes. Returned canonical artifact `screen-report-analysis-OBJ-ORDER-ENTRY-003.md`; kept `BR-*`/`CAP-*`/`DEC-*` forbidden; handoff non-approved (no SME sign-off evidence). |
| `legacy-ibmi-flow-analyzer` | v0.2.2 | synced | synced | synced | [scorecard](reviews/legacy-ibmi-flow-analyzer-v0.2.2-scorecard.md) | 2026-06-02 | v0.2.2 consumes program-analyzer v0.2.5 Routine Logic Details, routine-local carrier/lineage rows, and routine-local exception closure for flow lineage and exception propagation; three-runtime execution evidence pending. |
| `legacy-ibmi-module-analyzer` | v0.2.4 | synced | synced | synced | [scorecard](reviews/legacy-ibmi-module-analyzer-v0.2.3-scorecard.md) | 2026-06-04 | v0.2.4 removes default Operation/System outputs and keeps the module package focused on `module-overview.md`, `03-program-flow.md`, `04-data-flow.md`, and `module-review-checklist.md`; updated scorecard and three-runtime execution evidence pending. |
| `legacy-brd-writer` | v0.1.10 | synced | synced | synced | [scorecard](reviews/legacy-brd-writer-v0.1.8-scorecard.md) | 2026-06-05 | v0.1.10 adds daily delivery BRD mode while keeping delivery drafts barred from spec/SDD handoff; reviewed v0.1.8 scorecard remains the current readiness record; updated scorecard pending and three-runtime smoke pending. |
| `legacy-spec-writer` | v0.1.6 | synced | synced | synced | [scorecard](reviews/legacy-spec-writer-v0.1.6-scorecard.md) | 2026-06-02 | v0.1.6 preserves Routine Logic Details, routine-local carrier/lineage rows, and routine-local exception closure in observed behaviors, data fields, outputs, and exceptions; three-runtime smoke pending. |
| `legacy-modernization-decision-writer` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-modernization-decision-writer-v0.1.0-scorecard.md) | 2026-05-16 | Positive returned canonical `05_decisions/ORDERS/` four-file package, approved DEC. Negative blocked invented PostgreSQL/Kafka DEC with missing BR/BEH/EV grounding. |
| `legacy-sme-review-facilitator` | v0.1.4 | synced | synced | synced | [scorecard](reviews/legacy-sme-review-facilitator-v0.1.2-scorecard.md) | 2026-06-05 | v0.1.4 adds daily delivery review support for `delivery_draft` artifacts; reviewed v0.1.2 scorecard remains the current readiness record; updated scorecard pending and three-runtime chat-review smoke pending. |
| `legacy-brd-to-sdd-handoff` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-brd-to-sdd-handoff-v0.1.0-scorecard.md) | 2026-05-16 | Positive returned five required package files. Negative refused missing `spec.yaml`, routed to `legacy-spec-writer`. |
| `legacy-traceability-packager` | v0.1.1 | passed | passed | passed | [scorecard](reviews/legacy-traceability-packager-v0.1.1-scorecard.md) | 2026-05-16 | Positive returned `pass` with the four required files. Negative blocked dangling `AC-* -> BR-*`, refused to mint missing `BR-*`. |
| `legacy-runtime-matrix-tester` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-runtime-matrix-tester-v0.1.0-scorecard.md) | 2026-05-16 | Positive returned six-cell matrix row with lowercase statuses, `field-pilot ready` decision. Negative refused false `passed`, kept unavailable adapter at `synced`. |
| `legacy-golden-master-test-planner` | v0.1.0 | passed | passed | passed | [scorecard](reviews/legacy-golden-master-test-planner-v0.1.0-scorecard.md) | 2026-05-16 | Positive returned five `06_quality/CREDIT-LIMIT/` files with `TC-*` IDs. Negative blocked missing-customer rejection without observed expected-output evidence. |
| `legacy-step-contract` | v0.1.2 | passed | passed | passed | [scorecard](reviews/legacy-step-contract-v0.1.2-scorecard.md) | 2026-05-29 | Terminology-only update aligned scattered context with the module-context boundary. Prior positive and negative smoke passed across all three runtimes. |
| `legacy-step-validator` | v0.1.10 | synced | synced | synced | [scorecard](reviews/legacy-step-validator-v0.1.8-scorecard.md) | 2026-06-04 | v0.1.10 validates program-analysis top-of-document Exception Handling and Message Inventory placement plus closure/evidence links; updated scorecard pending. |
| `legacy-html-exporter` | v0.1.0 | passed | failed | passed | [scorecard](reviews/legacy-html-exporter-v0.1.0-scorecard.md) | 2026-05-19 | Codex passed positive and negative no-write smoke after quoting the frontmatter description for YAML safety. Claude Code still violates the negative source-of-truth guardrail. OpenCode now passes the positive contract-only smoke by invoking `export_contract_helper.py` and returning the exact sibling `.html` path while keeping Markdown canonical. |

## Verification

Run:

```bash
py -3 scripts/verify-skill-claims.py          # Windows
python3 scripts/verify-skill-claims.py        # macOS/Linux
```

The script checks that:

1. Every row has a current scorecard with frontmatter
2. The runtime status in this table matches the scorecard `runtimes_tested:`
3. The truth table (`docs/skill-status-truth-table.md`) agrees with this matrix,
   allowing newer synced versions only when marked scorecard-pending
4. README's "Current Skill Scores" table also agrees

The script exits non-zero if drift is detected.
