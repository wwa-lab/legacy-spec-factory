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
| 0 — Evidence Intake | Any | `legacy-ibmi-evidence-intake` | Implemented v0.1.0 | Register metadata, assign `EV-*` IDs, govern redaction, and produce the manifest. The agent must not inspect unredacted sensitive content. |
| 0p — Document Evidence Intake | Format-normalize raw Office/Visio/PDF/image documents when useful | `legacy-document-evidence-intake` | Implemented v0.1.0 | Use when business/technical documents are still in `.xlsx`/`.xlsm`/`.xls`, `.docx`/`.doc`, `.pptx`/`.ppt`, `.vsdx`/`.vsd`, `.pdf`, or image/scanned form and no `document-intake/<DOCSET-SLUG>/intake.manifest.yaml` exists yet. Converts to Markdown/CSV/PDF/PNG/SVG with manifests and `DOC-*`/`FRAG-*` evidence coordinates when tooling allows. Routes unauthorized or sensitivity-unknown material to `legacy-ibmi-evidence-intake`; ready/warning/tooling-only metadata hands off to `legacy-module-context-intake`. Does not infer business rules, generate BRD/spec content, or classify facts as BRD-ready. |
| 0m — Risk-Accepted Sparse Context | Continue after source owner/SME confirms no additional document, spec, or flow input can be provided | `legacy-module-context-intake` | Implemented v0.1.7 | Context intake must preserve all gaps as low-confidence TBDs/source eligibility labels and must not route directly to module analysis or BRD generation without its own gates. |
| 0m — Module Context Intake | Normalize RAG/context package | `legacy-module-context-intake` | Implemented v0.1.7 | Use when the user has external RAG output, source snippets, dictionary mappings, contradictions, retrieval gaps, SME fragments, or human-confirmed four-view module context. Blocks on unapproved evidence and does not promote RAG/generated candidates to approved rules or BRD conclusions. |
| 0n — Module Context Ready | Produce a standard code-backed BRD / migration discovery baseline / spec input | `legacy-ibmi-inventory` | Implemented | Use when `00_context_packages/<MODULE-SLUG>/context-index.yaml` is ready but `01_inventory/object-map.md`, program analyses, or flow analyses are missing. Build the code evidence backbone first; context views remain upstream hints. |
| 0n — Module Context Ready | Produce a daily delivery BRD with exception-only approvals | earliest missing code-backed step, usually `legacy-ibmi-inventory` | Implemented | Use `mode: daily_delivery`, `review_policy: exception_only`. Automatically continue through inventory, program, flow, module, data-model, and BRD steps unless a hard gate or blocking exception appears. Final output is `status: delivery_draft` plus a consolidated daily-delivery review pack; it is not approved for spec or handoff. |
| 0n — Module Context Ready | Produce an internal POC BRD now | `legacy-brd-writer` | Implemented v0.1.9 | Use when the requester explicitly wants an early POC BRD and accepts non-approved status. Generate `status: poc_draft`, `evidence_mode: internal_poc`, low-confidence hypotheses, and approval/spec blockers. Do not route to spec/handoff from this artifact. |
| 0n — Module Context Ready | Assemble context-only module draft | `legacy-ibmi-module-analyzer` | Implemented v0.2.3 | Use only when the user explicitly accepts a context-only path for this cycle or no source/object evidence is available. Preserve open questions as TBDs, classify BRD source eligibility, and do not claim code-backed approval. |
| Program-flow seed (`Program A -> Program B -> Program C`) | Produce daily delivery BRD | `legacy-ibmi-inventory` first, then per-node `legacy-ibmi-program-analyzer`, then `legacy-ibmi-flow-analyzer` | Implemented | Treat the chain as a scope seed, not a proven transaction. Inventory all nodes and dependencies, analyze each named program, then stitch the flow from evidence. Missing trigger model, parameter semantics, dynamic calls, commit boundaries, or data mutation become `TBD-*` or exception stops. |
| 1 — Evidence Ready (IBM i) | Start reverse engineering | `legacy-ibmi-inventory` | Implemented | First call after redaction |
| 1 — Evidence Ready (COBOL) | Start reverse engineering | `legacy-cobol-inventory` | Future | Use manual fallback; produce `inventory.yaml` following the same schema as the IBM i family |
| 2a — Inventory In Progress | Continue inventory | `legacy-ibmi-inventory` | Implemented | Keep iterating; do not exit until SME decision is recorded |
| 2b — Inventory Blocked | Any downstream | `legacy-ibmi-inventory` (resume) | Implemented | **Inventory Completeness Gate fails.** Resolve `coverage_gaps[].blocking: yes` or get explicit SME waiver |
| 2c — Inventory Done | Understand program logic | `legacy-ibmi-program-analyzer` | **Implemented v0.2.5** | Run per program; produces `program-analysis-<OBJ-ID>.md` with Call Evidence, Routine Logic Details, conditioned calculation blocks, routine-local lineage/carrier rows, routine-local exception closure, source identifier + meaning fields, File I/O Purpose, dynamic-call resolution, front-loaded Validation Logic, and exception closure |
| 2c — Inventory Done | Map calls / CRUD / DSPF | (subsumed) | n/a | Call graph, file I/O, object dependencies are embedded in program-analyzer + flow-analyzer + module-analyzer outputs |
| 2c — Inventory Done | Mine runtime evidence | `legacy-ibmi-runtime-evidence-miner` | Future (deferred from MVP) | Only when runtime samples are available and redacted |
| 3a — Program Analysis In Progress | Continue | `legacy-ibmi-program-analyzer` | **Implemented v0.2.5** | Complete coverage before routing to flow-analyzer, including Call Evidence, Routine Logic Details, conditioned calculation blocks, routine-local lineage/carrier rows, routine-local exception closure, key-field meaning, File I/O Purpose, dynamic-call resolution, front-loaded Validation Logic, and exception ledgers |
| 3b — Program Analysis Done | Analyze a call chain | `legacy-ibmi-flow-analyzer` | **Implemented v0.2.2** | Required when business event spans multiple programs; supports 7 trigger models plus replay, edge Evidence Source / Resolution, lineage consuming routine-local carriers, persistence purpose, and exception-chain evidence consuming routine-local exception closure |
| 3c — Flow Analysis In Progress | Continue | `legacy-ibmi-flow-analyzer` | **Implemented v0.2.2** | Complete all in-scope flows before module synthesis, including replay / edge resolution / lineage consuming routine-local carriers / persistence / exception-chain coverage consuming routine-local exception closure |
| 3d — Flow Analysis Done | Assemble the module | `legacy-ibmi-module-analyzer` | **Implemented v0.2.3** | Produces the canonical 4-view module coverage map plus readiness, BRD source eligibility, edge-resolution, critical field, persistence purpose, routine-local evidence carry-forward, and exception summaries under `04_modules/` per `docs/module-analysis-model.md` |
| 3e — Module Analysis In Progress | Continue | `legacy-ibmi-module-analyzer` | **Implemented v0.2.3** | All four views must reach `approved` or `approved_with_non_blocking_tbd`; module readiness and BRD crosswalk must carry source eligibility, edge-resolution, data, routine-local evidence, exception, and gap coverage |
| 3f — Module Analysis Done, no approved BRD Package | Produce legacy BRD for SME / business discovery review | `legacy-brd-writer` | **Implemented v0.1.9** | One legacy-system-only BRD Package per selected `CAP-*`; sections 1-9 are required for review, 10-12 optional/evidence-backed. For standard BRDs, module analysis must be backed by `01_inventory/object-map.md`, required program analyses, and required flow analyses. For daily delivery, generate `delivery_draft` and consolidate exceptions into one review pack. For internal POC, generate `poc_draft` and keep weak/candidate rows as hypotheses, TBDs, or review questions, not BRD conclusions. |
| 3f — Approved BRD Package, post-BRD No-gap / Gap1 / follow-new-system decision | Complete discovery for that item | Stop / record disposition | Doc-only | New system remains source of truth; do not route to spec-writing or handoff |
| 3f — Approved BRD Package, post-BRD risk assessment / gap analysis open | Resolve promotion decision | Risk assessment / gap-analysis process | Doc-only | Route to named product, SME, risk, or gap-analysis owner before spec-writing |
| 3f — Approved BRD Package plus explicit post-BRD promotion / disposition decision | Produce capability spec | `legacy-spec-writer` | **Implemented v0.1.6** | One spec per promoted `CAP-*`; consumes approved BRD Package plus analyzer v0.2.5 replay / conditioned calculation blocks / routine-local lineage / persistence / error-inventory / exception evidence |
| 4 — Static Analysis | (optional supplemental artifacts) | n/a | Optional | Subsumed by program/flow/module analyses; no separate skill needed for MVP |
| 5 — Runtime Evidence Mined | Augment BRD/spec package | `legacy-brd-writer` or `legacy-spec-writer` (rerun after the applicable review and post-BRD disposition gate) | **Implemented** | Runtime evidence miner is future, but once evidence exists the BRD/spec package can consume it to improve traceability and `evidence_strength`; keep BRD discovery review and post-BRD disposition before spec approval |
| 6 — Business Rules Drafted | (subsumed) | (BR seeds live in module View 1; spec-writer formalizes) | n/a | Stage retained for backward compatibility |
| 7 — Capabilities Mapped | (subsumed) | (CAP seeds live in module-overview; spec-writer produces one spec per CAP) | n/a | Stage retained for backward compatibility |
| 8a — Spec Drafted | Expand modernization decisions (optional) | `legacy-modernization-decision-writer` | **Implemented v0.1.0** | Optional governance skill. Use when decisions are complex, cross-cutting, or need explicit architecture approval. Produces `05_decisions/` package; reconciles back to `spec.yaml`. |
| 8a — Spec Drafted | Prepare browser-friendly SME review view | `legacy-html-exporter` | **Implemented v0.1.0** | Optional companion route only when stable human-facing Markdown already exists (`spec.md`, `traceability.md`, review/question docs). Markdown remains canonical; HTML must not replace review source. |
| 8a — Spec Drafted | Validate | `legacy-spec-reviewer` | Future (deferred from MVP) | Until implemented, use spec-writer's `spec-review.md` + SME |
| 8b — Spec In Review | Promote to approved | (SME sign-off) | Doc-only | Update `spec.yaml.status: approved` once SME signs; not a skill |
| 8b — Spec In Review | Make review docs easier for SMEs to read | `legacy-html-exporter` | **Implemented v0.1.0** | Optional review ergonomics. Use for browser-readable companions during SME walkthroughs; fix Markdown first if content is wrong. |
| 8c — Spec Approved | Generate equivalence tests | `legacy-equivalence-test-generator` | Planned | Produces golden-master test pack |
| 8c — Spec Approved | Export approved human-facing package | `legacy-html-exporter` | **Implemented v0.1.0** | Optional after approval for stakeholder browsing. Does not advance the chain and does not alter `spec.yaml.status`. |
| 9 — Equivalence Pack Ready | Hand off to forward SDLC | `docs/forward-sdlc-contract.md` then `ibm-i-program-spec` / `ibm-i-code-generator` / etc. | External | **Forward Handoff Gate first.** Cross to `wwa-lab/build-agent-skill` only after gate passes |

## Optional Detours

### Modernization Decision Expansion (After Spec Draft)

When routing from "Spec Drafted" to approval, consider whether the spec's
`modernization_decisions[]` should be expanded into a separate decision package.

**Trigger the optional `legacy-modernization-decision-writer` if**:

- Spec has 3+ `DEC-*` records
- Decisions are cross-cutting (affect multiple capabilities)
- Decisions are high-risk or require explicit architecture/product approval
- Spec review identifies unresolved platform, data, API, compatibility, or
  error-handling questions
- Decision authority (architecture owner) is separate from SME authority

**Skip `legacy-modernization-decision-writer` if**:

- Simple decisions that fit inline in `spec.yaml`
- All required SME and architecture/product approvals are already captured in
  the spec review package
- Forward SDLC handoff is not blocked by unresolved decisions

When using the decision-writer:

1. Feed it the draft `spec.yaml` + module/flow/program analyses
2. Decision-writer produces `05_decisions/<CAP-SLUG>/` package
3. Once approved, decision-writer reconciles approved `DEC-*` back to
   `spec.yaml`
4. Resume normal spec approval workflow

---

## Special Routes

### "Where am I?" requests

When the user just asks what they have without a clear outcome, run Step 1
(stage identification), report the stage, and list the 2-3 most useful next
moves with their gate requirements.

### "HTML / browser view / SME-readable export" requests

When the user asks for HTML, a browser view, a web-readable package, or easier
SME/user review:

1. Confirm the source is human-facing Markdown (`*.md`) or a directory
   containing Markdown review docs.
2. If the Markdown exists and is stable enough for review, route to
   `legacy-html-exporter`.
3. If the Markdown is missing, blocked, draft content that still needs upstream
   correction, or the request targets `spec.yaml` / JSON / YAML machine
   artifacts, route back to the producing skill or gate first.
4. If the user asks to make HTML the canonical artifact, block the request:
   Markdown remains canonical for human-facing docs, and `spec.yaml` remains
   canonical for automation.

Do not treat HTML export as a stage advancement. It is a supplemental read
view for review ergonomics.

### "Skip ahead" requests

When the user wants to jump several stages forward:

1. Identify what substance the skipped stages would have contributed
2. Check whether the current artifact already contains that substance
3. If yes, allow the jump and document the substitution
4. If no, refuse and route to the earliest unmet prerequisite

For document-first or RAG-first runs, `00_context_packages/` is not a
substitute for the code evidence backbone. If the user wants an approvable
legacy BRD, route first to inventory (`object-map.md`), program analysis, and
flow analysis. A context-only BRD draft is allowed only with named owner risk
acceptance and must remain non-approved. An internal POC BRD draft is allowed
when the requester explicitly asks for early POC output; it must use
`status: poc_draft`, list approval/spec blockers, and remain barred from
spec/handoff.

### "Multi-program slice" requests

When the slice contains multiple programs:

- Inventory must cover all of them before any program-analyzer runs
- Program-analyzer can run per-program in parallel
- Rule-miner aggregates across programs — do not invoke until at least the
  business-critical programs are analyzed

If the slice is supplied as a program-flow seed (`Program A -> Program B ->
Program C`) and the user asks for daily delivery, keep moving after each
mechanical pass. Do not require separate human approval for each node before the
next node starts. Stop only for hard evidence gates, missing source that changes
the requested flow, unresolved trigger model, or high-risk contradiction.

### "Daily delivery" requests

When the user asks for BRD delivery and does not explicitly ask for an approved
baseline, audit-ready package, customer acceptance, spec writing, SDD handoff,
or trusted knowledge publication, default to daily delivery. Also use this path
when the user asks for daily delivery, day-to-day BRD, fewer approvals, or
exception-only review:

1. Set `delivery_mode: daily_delivery`.
2. Keep Evidence Authorization Gate non-bypassable.
3. Route to the earliest missing evidence step, then continue automatically
   through inventory, program, flow, module, data-model, and BRD generation.
4. Convert non-critical review gaps into `TBD-*`, warnings, or
   `delivery-risk-summary.md` rows.
5. Produce `status: delivery_draft` and a consolidated
   `07_sme_reviews/<CAPABILITY>/daily-delivery-review-v1/` pack.
6. Refuse spec writing, SDD handoff, audit baseline, or knowledge publication
   until the BRD is promoted through the approved-baseline path.

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
