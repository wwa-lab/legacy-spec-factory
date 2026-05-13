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
| 3a | Program Analysis In Progress | `program-analysis.md` for some but not all in-scope programs |
| 3b | Program Analysis Done | `program-analysis.md` for all in-scope programs |
| 4a | Static Analysis Partial | One or more of `call-graph.md`, `crud-matrix.md`, `data-dictionary.md`, `screen-map.md` |
| 4b | Static Analysis Complete | All four Layer 1 static-analysis artifacts present |
| 5 | Runtime Evidence Mined | `runtime-evidence.jsonl` plus referenced samples in `03_runtime-evidence/` |
| 6 | Business Rules Drafted | `business-rules.md` (draft) with BR IDs and linked evidence |
| 7 | Capabilities Mapped | `capability-map.md` grouping rules into capability units |
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

| Stage | Lives Under |
| --- | --- |
| 1 | `evidence/redacted/` (raw never committed) |
| 2 | `01_inventory/` |
| 3, 4 | `02_static-analysis/` |
| 5 | `03_runtime-evidence/` |
| 6, 7 | `04_business-understanding/` |
| 8 | `05_specs/` |
| 9 | `06_quality/` |
| 10 | `07_forward-sdlc/` (handoff manifest) |

See [README artifact chain](../../../README.md#artifact-chain) for the full
directory layout.
