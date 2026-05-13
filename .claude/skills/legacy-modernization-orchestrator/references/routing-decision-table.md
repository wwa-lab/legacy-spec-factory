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
| 2c — Inventory Done | Understand program logic | `legacy-ibmi-program-analyzer` | **Implemented v0.1.0** | Run per program; produces `program-analysis-<OBJ-ID>.md` |
| 2c — Inventory Done | Map calls / CRUD / DSPF | (subsumed) | n/a | Call graph, file I/O, object dependencies are embedded in program-analyzer + flow-analyzer + module-analyzer outputs |
| 2c — Inventory Done | Mine runtime evidence | `legacy-ibmi-runtime-evidence-miner` | Future (deferred from MVP) | Only when runtime samples are available and redacted |
| 3a — Program Analysis In Progress | Continue | `legacy-ibmi-program-analyzer` | **Implemented v0.1.0** | Complete coverage before routing to flow-analyzer |
| 3b — Program Analysis Done | Analyze a call chain | `legacy-ibmi-flow-analyzer` | **Implemented v0.1.0** | Required when business event spans multiple programs; supports 7 trigger models (batch / menu / subfile / F-key / DB trigger / scheduler / API) |
| 3c — Flow Analysis In Progress | Continue | `legacy-ibmi-flow-analyzer` | **Implemented v0.1.0** | Complete all in-scope flows before module synthesis |
| 3d — Flow Analysis Done | Synthesize the module | `legacy-ibmi-module-analyzer` | **Implemented v0.1.0** | Produces 4-view analysis (Operation/System/Program/Data) per `docs/module-analysis-model.md` |
| 3e — Module Analysis In Progress | Continue | `legacy-ibmi-module-analyzer` | **Implemented v0.1.0** | All four views must reach `approved` or `approved_with_non_blocking_tbd` |
| 3f — Module Analysis Done | Produce capability spec | `legacy-spec-writer` | **Implemented v0.1.0** | One spec per `CAP-*` seed from `module-overview.md` |
| 4 — Static Analysis | (optional supplemental artifacts) | n/a | Optional | Subsumed by program/flow/module analyses; no separate skill needed for MVP |
| 5 — Runtime Evidence Mined | Augment specs | `legacy-spec-writer` (rerun) | Future | Improves `evidence_strength` on weak rules |
| 6 — Business Rules Drafted | (subsumed) | (BR seeds live in module View 1; spec-writer formalizes) | n/a | Stage retained for backward compatibility |
| 7 — Capabilities Mapped | (subsumed) | (CAP seeds live in module-overview; spec-writer produces one spec per CAP) | n/a | Stage retained for backward compatibility |
| 8a — Spec Drafted | Validate | `legacy-spec-reviewer` | Future (deferred from MVP) | Until implemented, use spec-writer's `spec-review.md` + SME |
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
