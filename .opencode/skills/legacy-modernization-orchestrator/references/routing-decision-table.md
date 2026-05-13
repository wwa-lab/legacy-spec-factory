# Routing Decision Table

The complete current-stage × desired-outcome → next-skill table for the
reverse chain.

Skill statuses:

- **Implemented**: SKILL.md exists, scored ≥ 9.0
- **Planned**: in the README target list, not yet built
- **Future**: aspirational (other-platform Layer 1)
- **Doc-only**: not a skill — a documented gate or process
- **External**: handoff to `wwa-lab/build-agent-skill`

## Full Decision Table

| Current Stage | Desired Outcome | Route To | Skill Status | Note |
| --- | --- | --- | --- | --- |
| 0 — Evidence Intake | Any | `docs/data-collection-and-redaction.md` | Doc-only | **Redaction Gate first.** No skill may consume unredacted evidence. |
| 1 — Evidence Ready (IBM i) | Start reverse engineering | `legacy-ibmi-inventory` | Implemented | First call after redaction |
| 1 — Evidence Ready (COBOL) | Start reverse engineering | `legacy-cobol-inventory` | Future | Use manual fallback; produce `inventory.yaml` following the same schema as the IBM i family |
| 2a — Inventory In Progress | Continue inventory | `legacy-ibmi-inventory` | Implemented | Keep iterating; do not exit until SME decision is recorded |
| 2b — Inventory Blocked | Any downstream | `legacy-ibmi-inventory` (resume) | Implemented | **Inventory Completeness Gate fails.** Resolve `coverage_gaps[].blocking: yes` or get explicit SME waiver |
| 2c — Inventory Done | Understand program logic | `legacy-ibmi-program-analyzer` | Planned | Required before rule mining per program |
| 2c — Inventory Done | Map calls | `legacy-ibmi-call-graph-analyzer` | Planned | Can run in parallel with program-analyzer |
| 2c — Inventory Done | Map CRUD usage | `legacy-ibmi-crud-matrix-analyzer` | Planned | Can run in parallel |
| 2c — Inventory Done | Analyze DDS files / screens / reports | `legacy-ibmi-dds-schema-analyzer` | Planned | Required before data model in `spec.yaml` |
| 2c — Inventory Done | Mine runtime evidence | `legacy-ibmi-runtime-evidence-miner` | Planned | Only when runtime samples are available and redacted |
| 3a — Program Analysis In Progress | Continue | `legacy-ibmi-program-analyzer` | Planned | Complete coverage before routing downstream |
| 3b — Program Analysis Done | Mine runtime evidence | `legacy-ibmi-runtime-evidence-miner` | Planned | Recommended for business-critical paths |
| 3b — Program Analysis Done | Skip runtime, mine rules from code only | `legacy-business-rule-miner` | Planned | Allowed only when rule will be tagged `evidence_strength: confirmed_from_code` and SME accepts |
| 4 — Static Analysis | Complete static picture | `legacy-ibmi-call-graph-analyzer` / `legacy-ibmi-crud-matrix-analyzer` / `legacy-ibmi-dds-schema-analyzer` | Planned | Run whichever artifact is missing |
| 5 — Runtime Evidence Mined | Extract business rules | `legacy-business-rule-miner` | Planned | Layer 2 entry |
| 6 — Business Rules Drafted | SME review | (human gate) | Doc-only | Use `inventory-review-checklist.md` pattern for rule review |
| 6 — Business Rules Drafted | Group into capabilities | `legacy-capability-mapper` | Planned | After SME confirms rules |
| 7 — Capabilities Mapped | Produce spec | `legacy-spec-writer` | Planned | Layer 2 synthesis to `spec.yaml` + `spec.md` |
| 8a — Spec Drafted | Validate | `legacy-spec-reviewer` | Planned | Required before SME approval |
| 8b — Spec In Review | Promote to approved | (SME sign-off) | Doc-only | Update `spec.yaml.status: approved` once SME signs; not a skill |
| 8c — Spec Approved | Generate equivalence tests | `legacy-equivalence-test-generator` | Planned | Produces golden-master test pack |
| 9 — Equivalence Pack Ready | Hand off to forward SDLC | `docs/forward-sdlc-contract.md` then `ibm-i-program-spec` / `ibm-i-code-generator` / etc. | External | **Forward Handoff Gate first.** Cross to `wwa-lab/build-agent-skill` only after gate passes |

## Special Routes

### "Where am I?" requests

When the user just asks what they have without a clear outcome, run Step 1
(stage identification), report the stage, and list the 2-3 most useful next
moves with their gate requirements.

### "Skip ahead" requests

When the user wants to jump several stages forward:

1. Identify what substance the skipped stages would have contributed
2. Check whether the current artifact already contains that substance
3. If yes, allow the jump and document the substitution
4. If no, refuse and route to the earliest unmet prerequisite

### "Multi-program slice" requests

When the slice contains multiple programs:

- Inventory must cover all of them before any program-analyzer runs
- Program-analyzer can run per-program in parallel
- Rule-miner aggregates across programs — do not invoke until at least the
  business-critical programs are analyzed

### "Already approved spec, want to regenerate" requests

When the user has an approved `spec.yaml` and wants to redo something:

- Do not retire approved rule IDs; mark them `status: retired` and create new
  IDs per `docs/id-conventions.md`
- Re-run `legacy-spec-reviewer` after any material change
- Re-run Forward Handoff Gate before re-crossing to the forward chain

## Cross-Chain Notes

- This orchestrator never invokes a forward-chain skill. It tells the user to
  cross over once the Forward Handoff Gate passes.
- The forward chain's `ibm-i-workflow-orchestrator` does not know about the
  reverse chain. Forward chain users with only existing source (no CR) should
  use this orchestrator, not theirs.
