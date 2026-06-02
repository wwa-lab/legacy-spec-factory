# Stage 04: Flow Analysis (one business transaction at a time)

**You are here if:** every in-scope program has an approved
`program-analysis.md` AND you want to trace one complete business
transaction end-to-end across all the programs it touches, including replay,
edge resolution, critical field lineage, persistence purpose, and exception
outcomes.

You will produce **one flow file per business transaction** (e.g. "submit
order", "post AR invoice"). A flow may cover one of seven trigger models:
batch job, interactive menu, subfile dispatch, F-key branch, DB trigger,
scheduler, API/remote.

## Need before starting

- `02_programs/<MODULE>/<OBJ>/program-analysis.md` for every program the
  flow touches (all at `approved` or `approved_with_non_blocking_tbd`;
  prefer program-analyzer v0.2.4 outputs with Routine Logic Details,
  routine-local carrier/lineage rows, routine-local exception closure,
  File I/O Purpose, source identifier + business meaning fields, and Error
  Code Inventory)
- `01_inventory/inventory.yaml` (approved)
- The trigger artifact for this flow: the menu, scheduler entry, DB trigger
  binding, API surface, or batch JOBSCDE entry
- SME contact for cross-program data flow questions

## Run

- **Skill:** `legacy-ibmi-flow-analyzer` (Implemented v0.2.2)
- **Manual fallback:** Use the flow skeleton in
  `skills/legacy-ibmi-flow-analyzer/references/` and synthesize across the
  per-program analyses

## Produce

- **Artifact:** `flow-<FLOW-SLUG>.md`
- **Save under:**
  `03_flows/<MODULE-SLUG>/flow-<FLOW-SLUG>.md`
  *(relative to your `project.root`)*
  e.g. `docs/XXX260004-demo/03_flows/CREDIT-CHECK/flow-submit-order.md`
- **Consumed by:** `legacy-ibmi-module-analyzer`

Required sections: Trigger Context, Transaction Call Map, Common Dependencies,
Flow Replay Path, Nodes, Edges, Cross-Program Data Flow, Cross-Program Field
Lineage, Branch Points, Flow Persistence Matrix, UI Surfaces, Error Propagation
& Commit Boundaries, Exception Propagation Chain, and Business-Capability Seeds
(`SEED-*`).
Edges must carry Evidence Source + Resolution when derived from upstream
program Call Evidence, and data/lineage/persistence rows must preserve source
identifier + business meaning pairs where program-analysis resolved them.
When program-analysis v0.2.4 evidence is present, Cross-Program Field Lineage
must consume routine-local carrier/lineage rows where available, and Exception
Propagation Chain must consume routine-local exception closure alongside Error
Code Inventory / Exception Closure Ledger evidence.

## Gate before advancing

- **Name:** (none specific) — advancement is gated by **flow coverage**:
  every business transaction the module supports must have an approved
  flow before module analysis is complete
- **Check:** `flow-*.md` files cover every named transaction the SME lists
  for this module, and each approved flow exposes Flow Replay Path,
  edge Evidence Source / Resolution, Cross-Program Field Lineage, Flow
  Persistence Matrix with Purpose, and Exception Propagation Chain. Where
  upstream program-analysis v0.2.4 rows exist, the flow must preserve
  routine-local carrier/lineage and exception-closure evidence or name the
  missing detail as a `TBD-*`.
- **Blocks if:** a known business transaction has no flow, OR any flow is
  at `status: draft` with money / inventory / compliance impact, OR a
  code-backed flow lacks replay / edge-resolution / lineage / persistence /
  exception-chain / routine-local evidence carry-forward coverage without a
  named waiver

## SME action

- **Required:** to confirm trigger context, commit boundaries, and which
  flows count as "the module's business"
- **Ask:** "Is this the complete replay under trigger X? Are the critical
  fields carried correctly? Which files/fields persist or skip updates? What
  happens on error after step N? Is the commit boundary at step M correct?"
- **Recorded in:** `flow-<slug>.md` → `status` and the per-step
  `review_status` columns

## Next card

[`05-module-analysis.md`](05-module-analysis.md) — once all the module's
flows are approved.
