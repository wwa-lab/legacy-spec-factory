# Stage Identification Reference

Map the user's current artifact(s) to a single canonical stage. Use the most
upstream stage that fits — do not "round up" maturity.

## Full Stage Table

| # | Stage | Identifying Input |
| ---: | --- | --- |
| 0 | Evidence Intake (pre-redaction) | Raw source members, DDS exports, job logs, spool, screen samples, or DB extracts with `sensitivity: unknown` or `sensitive: yes` and no redaction record |
| 1 | Evidence Ready | Redacted evidence bundle; every item has `sensitive: no` or a recorded redaction note; SME contact listed |
| 2a | Inventory In Progress | Partial `inventory.yaml` (some objects, no `sme_review.decision`) |
| 2b | Inventory Blocked | `inventory.yaml.sme_review.decision: blocked`, or `coverage_gaps[].blocking: yes` unresolved |
| 2c | Inventory Done | `inventory.yaml.sme_review.decision: approved` or `approved_with_non_blocking_tbd`, plus `object-map.md` |
| 3a | Program Analysis In Progress | `program-analysis-<OBJ-ID>.md` for some but not all in-scope programs |
| 3b | Program Analysis Done | `program-analysis-<OBJ-ID>.md` for all in-scope programs |
| 3c | Flow Analysis In Progress | `flow-<FLOW-SLUG>.md` for some but not all in-scope flows |
| 3d | Flow Analysis Done | `flow-<FLOW-SLUG>.md` for all in-scope flows at `status: approved` or `approved_with_non_blocking_tbd` |
| 3e | Module Analysis In Progress | `04_modules/<MODULE-SLUG>/` exists with one or more of the four views drafted |
| 3f | Module Analysis Done | `04_modules/<MODULE-SLUG>/` with all four views (Operation/System/Program/Data) approved (or approved_with_non_blocking_tbd) |
| 4a | Static Analysis Partial | One or more of `call-graph.md`, `crud-matrix.md`, `data-dictionary.md`, `screen-map.md` (optional supplemental artifacts; mostly subsumed by program/flow/module analyses) |
| 4b | Static Analysis Complete | All four Layer 1 supplemental artifacts present (optional) |
| 5 | Runtime Evidence Mined | `runtime-evidence.jsonl` plus referenced samples in `07_runtime-evidence/` (deferred from MVP) |
| 6 | Business Rules Drafted | BR seeds present in module View 1 OR a separate `business-rules.md` (BR IDs + linked evidence); typically subsumed by stage 3f |
| 7 | Capabilities Mapped | Capability seeds (`CAP-*`) listed in `module-overview.md` OR a separate `capability-map.md`; typically subsumed by stage 3f |
| 8a | Spec Drafted | `spec.yaml.status: draft` plus `spec.md` |
| 8b | Spec In Review | `spec.yaml.status: in_review` plus optional `review-report.md` |
| 8c | Spec Approved | `spec.yaml.status: approved` |
| 9 | Equivalence Pack Ready | `golden-master-tests.md` plus generated test artifacts traceable to approved rules |
| 10 | Forward Handoff Ready | Spec Approved + Equivalence Pack + redacted sample transactions |

## Disambiguation Rules

When the user has artifacts from multiple stages:

- The **earliest unmet stage** is the current stage.
- Example: user has `program-analysis.md` AND `business-rules.md` AND
  `spec.yaml (draft)`. If `program-analysis.md` covers only 2 of 5 in-scope
  programs, the current stage is **3a (Program Analysis In Progress)**, not
  8a. Downstream artifacts must be re-validated after analysis completes.

When evidence is mixed sensitivity:

- If any one item has `sensitive: yes` without redaction, the stage is **0
  (Evidence Intake)** regardless of how much other progress exists. The
  Redaction Gate is non-bypassable.

When only forward chain artifacts exist:

- If the user has only `wwa-lab/build-agent-skill`-style artifacts
  (Functional Spec, Technical Design, Program Spec) and no reverse-chain
  evidence, this orchestrator is not the right tool — point them to the
  forward repo's `ibm-i-workflow-orchestrator`.

## Stage to Output Directory

All paths below are **relative to `project.root`** (default
`docs/<project-name>/`). For a project named `XXX260004-demo`, stage 2
artifacts live at `docs/XXX260004-demo/01_inventory/`.

| Stage | Lives Under (relative to project.root) |
| --- | --- |
| 1 | `evidence/redacted/` (raw never committed) |
| 2 | `01_inventory/` |
| 3a, 3b | `02_programs/` |
| 3c, 3d | `03_flows/` |
| 3e, 3f | `04_modules/` |
| 4 | optional supplemental artifacts under the owning program / flow / module folder |
| 5 | `07_runtime-evidence/` |
| 6, 7 | `08_business-understanding/` |
| 8 | `05_specs/` |
| 9 | `06_quality/` |
| 10 | `09_forward-sdlc/` (handoff manifest) |

Subdirectories are created on demand by the writing skill — do NOT
pre-create empty stage folders. See `docs/workflow-state-contract.md` for
the full project-root resolution rules and `README.md#artifact-chain` for
the layout diagram.
