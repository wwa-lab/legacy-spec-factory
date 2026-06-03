# Skill Card Index

This is the quick navigation layer for the Skill Cards embedded in the Legacy
Spec Factory canonical `skills/legacy-*/SKILL.md` files.

Use this page when explaining the whole system. Use the per-skill card as the
source of truth for that skill's input, output, prompt strategy, dependencies,
validation standard, risks, and example. Status, score, and runtime maturity
remain in [`skill-status-truth-table.md`](skill-status-truth-table.md).

## How to Read

- **Stage / family** shows where the skill sits in the operating model.
- **Skill Card** links to the card inside the canonical skill.
- **Use it for** is the one-line explanation to say out loud.
- **Upstream / downstream** shows the handoff shape without duplicating the
  full card.
- **Primary risk** is the risk to remember when deciding whether to call it.

## Legacy Spec Factory Cards

| Stage / family | Skill Card | Use it for | Upstream | Downstream | Key output | Primary risk |
| --- | --- | --- | --- | --- | --- | --- |
| Routing | [`legacy-modernization-orchestrator`](../skills/legacy-modernization-orchestrator/SKILL.md#skill-card) | Pick the safest next skill and gate. | None | Any Legacy Spec Factory skill | Routing decision | Doing downstream analysis inside the router. |
| Module-first context intake | [`legacy-document-evidence-intake`](../skills/legacy-document-evidence-intake/SKILL.md#skill-card) | Convert Office, Visio, PDF, image, or scanned docs into evidence-coordinate packages. | Orchestrator or raw document collection | Module context intake or IBM i evidence intake | Document intake package | Losing provenance or passing sensitive data downstream. |
| Module-first context intake | [`legacy-module-context-intake`](../skills/legacy-module-context-intake/SKILL.md#skill-card) | Package reviewed module-first context and source eligibility into `00_context_packages/`. | Document intake, source metadata, RAG, SME fragments, or reviewed module context | Module analyzer, BRD writer | Traceable context package | Promoting sparse, generated, or RAG-derived candidates into approved rules or BRD conclusions. |
| Layer 1 IBM i extraction | [`legacy-ibmi-evidence-intake`](../skills/legacy-ibmi-evidence-intake/SKILL.md#skill-card) | Register, classify, authorize, and redact IBM i evidence before analysis. | Orchestrator or raw IBM i evidence collection | Inventory, runtime miner, and all extraction skills | Evidence manifest and redaction log | Letting unauthorized production data enter analysis. |
| Layer 1 IBM i extraction | [`legacy-ibmi-inventory`](../skills/legacy-ibmi-inventory/SKILL.md#skill-card) | Build the object map and baseline inventory. | IBM i evidence intake | Program, flow, module, data, screen/report, runtime skills | `inventory.yaml` and object map | Missing assets that later invalidate analysis. |
| Layer 1 IBM i extraction | [`legacy-ibmi-runtime-evidence-miner`](../skills/legacy-ibmi-runtime-evidence-miner/SKILL.md#skill-card) | Extract structured observed-runtime facts from approved job logs and spool/report files. | IBM i evidence intake and inventory | Program, flow, module, spec, golden-master planning | `runtime-evidence.jsonl` | Treating one runtime sample as exhaustive. |
| Layer 1 IBM i extraction | [`legacy-ibmi-program-analyzer`](../skills/legacy-ibmi-program-analyzer/SKILL.md#skill-card) | Analyze one RPGLE, CLLE, or COBOL program. | Inventory | Flow analyzer, module analyzer, data model, batch digest, spec synthesis | `program-analysis-<OBJ-ID>.md` | Inferring business meaning from names alone. |
| Layer 1 IBM i extraction | [`legacy-ibmi-flow-analyzer`](../skills/legacy-ibmi-flow-analyzer/SKILL.md#skill-card) | Explain one end-to-end IBM i transaction across programs and data movement. | Program analyzer and inventory | Module analyzer, BRD writer, spec preparation | Flow analysis | Over-connecting related-looking programs into one transaction. |
| Layer 1 IBM i extraction | [`legacy-ibmi-data-model-analyzer`](../skills/legacy-ibmi-data-model-analyzer/SKILL.md#skill-card) | Reconstruct the domain data model from DDS, DB2 metadata, DDL, and usage evidence. | Inventory plus program/flow evidence | Module analyzer, spec writer, data architects | Data model package | Misreading logical files or historical fields as current business relationships. |
| Layer 1 IBM i extraction | [`legacy-ibmi-screen-report-analyzer`](../skills/legacy-ibmi-screen-report-analyzer/SKILL.md#skill-card) | Document DSPF, PRTF, menu, subfile, screen, and report behavior. | Evidence intake and inventory | Program/flow/module analysts, BRD writer, golden-master planner | Screen/report analysis | Treating labels or columns as full business rules. |
| Layer 1 IBM i extraction | [`legacy-ibmi-module-analyzer`](../skills/legacy-ibmi-module-analyzer/SKILL.md#skill-card) | Assemble flows or module-first context into the canonical four-view coverage map and BRD eligibility crosswalk. | Flow analyzer or module context intake | BRD writer, spec writer, SME review | Four-view module coverage | Polished diagrams hiding unresolved gaps or BRD-ineligible rows. |
| Supplemental review | [`legacy-ibmi-batch-digest`](../skills/legacy-ibmi-batch-digest/SKILL.md#skill-card) | Condense many program analyses into one SME-friendly review table. | Program analyzer | SME review facilitator, SMEs, module reviewers | `programs-batch-digest.md` | Oversimplifying critical programs or hiding TBDs. |
| Layer 2 synthesis | [`legacy-brd-writer`](../skills/legacy-brd-writer/SKILL.md#skill-card) | Turn confirmed/code-backed legacy evidence into a stakeholder-readable old-system BRD. | Module analyzer or accepted module-first context | SMEs, gap analysis, spec writer, decision writer | Legacy BRD Package | Treating generated/candidate context as BRD conclusion or old-system description as target-system mandate. |
| Layer 2 synthesis | [`legacy-spec-writer`](../skills/legacy-spec-writer/SKILL.md#skill-card) | Promote approved discovery into platform-agnostic capability specs. | BRD writer after BRD review and disposition | Golden-master planner, traceability packager, SDD handoff | `spec.yaml`, `spec.md`, `traceability.md` | Letting speculative gaps or target preferences become requirements. |
| Layer 2 synthesis | [`legacy-modernization-decision-writer`](../skills/legacy-modernization-decision-writer/SKILL.md#skill-card) | Capture material modernization decisions as structured `DEC-*` records. | BRD writer or spec writer | Spec writer, SDD handoff, architects, governance reviewers | Decision package | Unofficially overriding approved scope or architecture. |
| Bridge / handoff | [`legacy-traceability-packager`](../skills/legacy-traceability-packager/SKILL.md#skill-card) | Seal or block capability traceability across evidence, analyses, BRD, spec, and handoff. | Spec writer and earlier evidence/analysis steps | Auditors, SDD handoff reviewers, governance teams | Traceability package or blocked findings | Polished package implying approval despite broken links. |
| Bridge / handoff | [`legacy-brd-to-sdd-handoff`](../skills/legacy-brd-to-sdd-handoff/SKILL.md#skill-card) | Package approved BRD and spec into an Atlas-compatible SDD handoff. | Spec writer after BRD approval and disposition | Atlas / forward SDLC agents, architecture/design teams | SDD handoff bundle | Packaging unapproved discovery as implementation-ready. |
| Verification | [`legacy-golden-master-test-planner`](../skills/legacy-golden-master-test-planner/SKILL.md#skill-card) | Plan old-vs-new equivalence cases from approved behavior and runtime evidence. | Spec writer plus approved runtime evidence | QA, forward SDLC, implementation validators | Golden master test plan | Inventing expected outputs without evidence. |
| Governance | [`legacy-step-contract`](../skills/legacy-step-contract/SKILL.md#skill-card) | Define the shared INPUT -> EXECUTION -> OUTPUT -> VALIDATION contract. | None | All Legacy Spec Factory skills, step validator | Step contract guidance | Treating the contract as optional prose. |
| Governance | [`legacy-step-validator`](../skills/legacy-step-validator/SKILL.md#skill-card) | Validate a produced artifact against the step contract. | Step contract plus producing skill | Artifact owner, SME review, downstream gates | Validation report | Mistaking contract readiness for SME approval. |
| Governance | [`legacy-sme-review-facilitator`](../skills/legacy-sme-review-facilitator/SKILL.md#skill-card) | Run guided SME review and write back scoped decisions. | BRD, spec, module analysis, or other artifact needing SME validation | Artifact owners, spec writer, validators, approval gates | SME review artifacts | Treating informal chat as full approval. |
| Governance | [`legacy-runtime-matrix-tester`](../skills/legacy-runtime-matrix-tester/SKILL.md#skill-card) | Verify skill portability across Codex, Claude Code, and OpenCode. | Any changed skill plus sync output | Skill maintainers and release readiness | Runtime smoke-test evidence | Passing shallow smoke tests while adapter assumptions remain hidden. |
| Governance / publishing | [`legacy-html-exporter`](../skills/legacy-html-exporter/SKILL.md#skill-card) | Export stakeholder-facing Markdown artifacts into standalone HTML companions. | Any stakeholder-facing Markdown artifact | SMEs, pilot reviewers, business sign-off sessions | `.html` companions | Stakeholders treating HTML as canonical. |

## Maintenance Rule

When a new Legacy Spec Factory skill is added or a skill card changes
materially:

1. Update the card in `skills/<skill-name>/SKILL.md`.
2. Update this index with only the navigation-level summary.
3. Run `scripts/sync-skills.sh` if any canonical skill file changed.
4. Run `scripts/sync-skills.sh --check` to confirm adapter copies are aligned.
