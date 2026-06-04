# Stage 05: Module Analysis (focused synthesis)

**You are here if:** every flow in scope for this module has an approved
`flow-<slug>.md` with replay, field-lineage, persistence, and exception-chain
coverage, or a ready `00_context_packages/<MODULE-SLUG>/` package is being
used as module-first context, AND you need to synthesize the module's
evidence-backed overview, Program Flow, and Data Flow before BRD writing and
review.

This is the **last reverse-engineering step** before BRD writing. Business
rule seeds and capability seeds emerge here, then the BRD Package becomes the
business / SME review artifact before any spec is produced.

## Need before starting

- `03_flows/<MODULE-SLUG>/flow-*.md` for every flow (all approved, preferably
  flow-analyzer v0.2.2 with Flow Replay Path, edge Evidence Source /
  Resolution, Cross-Program Field Lineage consuming routine-local carrier
  evidence, Flow Persistence Matrix, and Exception Propagation Chain consuming
  routine-local exception closure)
- `02_programs/<MODULE-SLUG>/<OBJ>/program-analysis.md` for every program
  (preferably program-analyzer v0.2.5 with Call Evidence, Routine Logic
  Details, conditioned calculation blocks, routine-local carrier/lineage rows,
  routine-local exception closure, key file/field source identifiers plus
  meanings, File I/O Purpose, dynamic-call resolution, Validation Logic,
  and exception closure)
- `01_inventory/inventory.yaml` (approved)
- SME-confirmed BAU notes for the module (any operational quirks,
  workarounds, undocumented rules)

## Run

- **Skill:** `legacy-ibmi-module-analyzer` (Implemented v0.2.4)
- **Manual fallback:** Build the focused module package by hand following
  `docs/module-analysis-model.md` and the templates in
  `skills/legacy-ibmi-module-analyzer/references/`

## Produce

- **Artifact:** focused module package
  - `module-overview.md` — module identity, in-scope flows, program-chain
    readiness, edge-resolution coverage, persistence / critical field summary,
    exception / recovery summary, capability seeds (`CAP-*`), and BRD crosswalk
  - `03-program-flow.md` — program-level sequencing + replay coverage
  - `04-data-flow.md` — data lifecycle, persistence matrix, critical field
    lineage, and exception-aware data risks
  - `module-review-checklist.md` — module package sign-off
- **Save under:** `04_modules/<MODULE-SLUG>/` *(relative to your
  `project.root`, e.g. `docs/XXX260004-demo/04_modules/CREDIT-CHECK/`)*
- **Consumed by:** `legacy-brd-writer` first; `legacy-spec-writer` only after
  the selected capability has an approved BRD Package or an explicit
  technical-spec-only bypass.

## Gate before advancing

- **Name:** Module synthesis completeness (informal)
- **Check:** `module-overview.md`, `03-program-flow.md`, `04-data-flow.md`,
  and `module-review-checklist.md` present AND `module-overview.md` lists at least one
  `CAP-*` capability seed AND module replay / lineage / persistence /
  exception-chain coverage is summarized or waived
- **Blocks if:** overview, Program Flow, Data Flow, or checklist is missing;
  no capability seeds; any covered BRD crosswalk row lacks eligible evidence;
  or a code-backed module lacks replay / lineage /
  edge-resolution / persistence / exception-chain coverage without named
  `TBD-*` gaps

## SME action

- **Required:** yes — every `inferred_business_rule` must be SME-confirmed
  before the Evidence Approval Gate at spec-writing time
- **Ask:** "For each BR-* marked `inferred`: is this rule correct? Are the
  replay paths complete? Are critical fields and persistence outcomes correct?
  What exceptions exist? Should it be modernized as-is or changed?"
- **Recorded in:** `module-overview.md` BRD crosswalk/review blocks plus
  Program Flow and Data Flow review statuses

## Next card

[`05a-brd-writing.md`](05a-brd-writing.md) — once the focused module package
is approved, produce the BRD Package for the selected `CAP-*` before moving to
spec writing.
