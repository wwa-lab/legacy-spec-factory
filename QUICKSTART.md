# Legacy Spec Factory — Quick Start

A 10-minute walkthrough for your first PPCR. By the end you'll know how to
invoke the orchestrator, set up your project folder, walk through the
reverse-engineering chain, and resume work in the next session without
re-explaining anything.

If you just want to study a finished example, jump to
[`docs/EXAMPLE-tutorial/`](docs/EXAMPLE-tutorial/) — it's a complete
minimal project showing every artifact in the chain.

---

## Prerequisites

- Python 3.10+ with PyYAML (`pip install pyyaml`)
  - Windows (field): `py -3`  · macOS/Linux (dev): `python3`  · never bare `python`
- An LSF-aware runtime: Claude Code, OpenCode, Codex, or any runtime where
  the LSF skills are available
- An IBM i / AS400 source bundle (RPGLE / CLLE / COBOL / DDS / DB2
  metadata / job logs) that has been **redacted** of PII and trade secrets
- An SME (subject-matter expert) contact for the module under review

---

## Step 1 — Invoke the orchestrator

You don't need to remember any skill name. Just tell the runtime what
you've got and what you want:

> "我刚接了 PPCR XXX260004，要做信用检查模块的现代化"
>
> "I just inherited a legacy AS400 project, where do I start?"
>
> "I have an inventory.yaml — what's next?"

The orchestrator will trigger and respond with a **Quick Card** at the
bottom of every routing decision. That card always tells you:

- which project (`PROJECT: docs/<project-name>/`)
- which capability you're working on (`FOCUS`)
- the current stage (`YOU ARE HERE`)
- the next skill to run (`RUN NEXT`)
- the file path it should produce (`WILL PRODUCE`)
- which gate is blocking (if any) (`GATE CHECK`)
- whether the SME needs to do something (`SME ACTION`)
- where to read more (`STAGE CARD`)
- the state file (`STATE FILE`)
- manual fallback (`MANUAL FALLBACK`)

Even if the LLM is weak or your session lost context, the Quick Card +
`workflow-state.yaml` give you everything to resume.

---

## Step 2 — Name your project

The orchestrator asks for a project name. Use the **PPCR convention**:

```
<PPCR-Number>-<short-description>
```

Examples: `XXX260004-demo`, `XXX260123-credit-check`,
`XXX260200-warehouse-receipts`.

If you type something with spaces or punctuation, the orchestrator
**auto-fixes** it and asks you to confirm:

```
You typed:    XXX260004 demo
I'll use:     XXX260004-demo
Confirm? (Y/n)
```

The orchestrator creates `docs/XXX260004-demo/workflow-state.yaml` and
puts every subsequent artifact under that root.

---

## Step 3 — Prep evidence (Stage 0 → Stage 1)

Hand the orchestrator your raw evidence bundle. It will route you to
`legacy-ibmi-evidence-intake`, which:

1. Catalogs every item (source members, DDS, job logs, spool, screens)
2. Asks you to confirm sensitivity (`sensitive` / `redacted` / `safe`) per
   item — your SME signs off
3. Writes `docs/<project>/evidence/redacted/evidence-manifest.yaml`

**Gate:** the Redaction Gate blocks every downstream skill until every
item has `sensitivity ∈ {no, redacted}`. Don't try to skip it — even one
unredacted item halts the chain.

---

## Step 4 — Inventory (Stage 1 → Stage 2c)

Once redaction is approved, the orchestrator routes to
`legacy-ibmi-inventory`. It produces:

- `docs/<project>/01_inventory/inventory.yaml` — every `OBJ-*` in scope,
  typed and linked to evidence IDs
- `docs/<project>/01_inventory/object-map.md` — human-readable companion

**SME action:** the SME must confirm the scope (or reject — "you missed
the AR posting batch job"). The orchestrator surfaces SME questions and
records the decision in `inventory.yaml.sme_review.decision`.

**Gate:** the Inventory Completeness Gate. Cannot advance while any
`coverage_gaps[].blocking: yes` is unresolved.

---

## Step 5 — Program analysis (Stage 2c → Stage 3b)

For each in-scope program, run `legacy-ibmi-program-analyzer`. It
produces one file per program:

```
docs/<project>/02_programs/<MODULE>/<OBJ-PROGRAM>/program-analysis.md
```

The analysis covers entry points, control flow, file I/O, external calls,
error handling, and open questions (`TBD-*`). Every row cites an
`evidence_id`.

You will loop through programs one at a time. The orchestrator tracks
progress in `capabilities[].stage_id`: `3a Program Analysis In Progress`
while some programs remain; `3b Program Analysis Done` when all approved.

---

## Step 6 — Flow analysis (Stage 3b → Stage 3d)

Now trace one complete business transaction end-to-end across all the
programs it touches. `legacy-ibmi-flow-analyzer` handles seven trigger
models (batch, menu, subfile dispatch, F-key, DB trigger, scheduler,
API).

Output:
```
docs/<project>/03_flows/<MODULE>/flow-<FLOW-SLUG>.md
```

A flow covers trigger context, sequence, cross-program data flow, error
propagation, commit boundaries, and business-capability seeds (`CAP-*`).

---

## Step 7 — Module synthesis (Stage 3d → Stage 3f)

`legacy-ibmi-module-analyzer` synthesizes everything into the canonical
**4 views** of the module:

```
docs/<project>/04_modules/<MODULE>/
  module-overview.md
  view-1-operation-flow.md    ← Operation Flow (user perspective + BR-* seeds)
  view-2-system-flow.md       ← System Flow (system interaction)
  view-3-program-flow.md      ← Program Flow (sequencing)
  view-4-data-flow.md         ← Data Flow (lifecycle)
```

This is the last reverse-engineering step before spec writing. Business
rule seeds (`BR-*`) and capability seeds (`CAP-*`) emerge here.

---

## Step 8 — Spec writing (Stage 3f → Stage 8c)

One `spec.yaml` per capability. `legacy-spec-writer` produces:

```
docs/<project>/05_specs/<CAP-*>/
  spec.yaml         ← machine-readable contract (conforms to schemas/spec.schema.yaml)
  spec.md           ← human-readable explanation
  traceability.md   ← rule → evidence → test mapping
```

The spec progresses through three statuses:
- `8a Spec Drafted` — first draft from module analysis
- `8b Spec In Review` — SME is reviewing
- `8c Spec Approved` — SME signed off, ready for handoff

**Gate:** the Evidence Approval Gate. Every rule must have linked
evidence and (if `inferred_business_rule`) SME confirmation. Every
approved rule must have `acceptance_criteria`.

---

## Step 9 — Equivalence pack + handoff (Stage 8c → Stage 10)

`legacy-golden-master-test-planner` produces:

```
docs/<project>/06_quality/<CAP-*>/golden-master-tests.md
```

`legacy-brd-to-sdd-handoff` packages everything and validates the
Forward Handoff Gate:

```
docs/<project>/09_forward-sdlc/<CAP-*>/
```

After this, work continues in `wwa-lab/build-agent-skill` (the forward
SDLC repo). Legacy Spec Factory's reverse chain ends here.

---

## Useful commands

```bash
# Windows: py -3   macOS/Linux: python3

# Validate that workflow-state.yaml is well-formed
py -3 scripts/check-workflow-state.py docs/<project>/workflow-state.yaml

# Re-render the human-readable project snapshot
py -3 scripts/generate-status.py docs/<project>/
# → writes docs/<project>/STATUS.md

# Show every project in this repo
py -3 scripts/list-projects.py
py -3 scripts/list-projects.py --markdown   # pipe to a report
py -3 scripts/list-projects.py --json       # pipe to other tools
```

---

## Resuming in a later session

You don't have to remember anything between sessions. Just invoke the
orchestrator with any of these:

> "继续 XXX260004"
>
> "Resume the AR project"
>
> "What's next on `docs/XXX260004-demo/`?"

The orchestrator reads `docs/<project>/workflow-state.yaml` at Step 0 and
picks up exactly where you left off — same capability, same stage, same
blockers. If you have multiple projects, it shows a picker first.

---

## Switching, rolling back, or starting another capability

The orchestrator understands natural-language requests:

| You say | Orchestrator does |
| --- | --- |
| "Continue" / "下一步" | Continues current focus |
| "Switch to CAP-AR-POSTING" | Switches focus, preserves old |
| "Start CAP-NEW-FEATURE" | Creates new capability entry |
| "Redo flow-submit-order" | Rollback Protocol — stage rewound, history note appended |
| "What's in this repo?" | Scan Mode — picker of all in-flight capabilities |

See [`skills/legacy-modernization-orchestrator/references/focus-selection.md`](skills/legacy-modernization-orchestrator/references/focus-selection.md)
for the full decision tree.

---

## Where things live

```
<your-repo>/
  docs/
    XXX260004-demo/                ← one project
      workflow-state.yaml          ← machine state (orchestrator writes)
      STATUS.md                    ← human snapshot (auto-generated)
      evidence/redacted/
      01_inventory/
      02_programs/<MODULE>/<OBJ>/
      03_flows/<MODULE>/
      04_modules/<MODULE>/
      05_specs/<CAP-*>/
      06_quality/<CAP-*>/
      07_runtime-evidence/
      08_business-understanding/
      09_forward-sdlc/<CAP-*>/
    XXX260123-credit-check/        ← another project, fully isolated
      ...
```

Directories are created **on demand** by the writing skill — empty stage
folders never appear.

---

## When things go wrong

| Symptom | Look at |
| --- | --- |
| Orchestrator didn't trigger on your message | Try a more explicit phrase from Step 1 |
| Stage seems wrong | Open `STATUS.md` — if it disagrees with reality, run an orchestrator turn to re-derive |
| State file looks corrupt | `py -3 scripts/check-workflow-state.py docs/<project>/workflow-state.yaml` (macOS: `python3`) |
| Lost focus mid-session | Just say "where am I?" — orchestrator re-reads state and re-shows the Quick Card |
| SME blocked you | Open `STATUS.md` → "Open Blockers" → use the SME review email template (see `legacy-sme-review-facilitator` skill) |

---

## Further reading

- [README.md](README.md) — full project map
- [docs/workflow-state-contract.md](docs/workflow-state-contract.md) — the cross-skill state contract
- [docs/collaboration.md](docs/collaboration.md) — multi-user patterns and `workflow-state.yaml` merge rules
- [skills/legacy-modernization-orchestrator/SKILL.md](skills/legacy-modernization-orchestrator/SKILL.md) — orchestrator internals
- [skills/legacy-modernization-orchestrator/references/stage-cards/INDEX.md](skills/legacy-modernization-orchestrator/references/stage-cards/INDEX.md) — one-page card per pipeline stage
- [docs/EXAMPLE-tutorial/README.md](docs/EXAMPLE-tutorial/README.md) — fully-populated example project
