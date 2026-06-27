# Program Flow Map Export Contract

This document defines the expected handoff from the upstream Neo4j Program Flow
Map repository into Atlas Phoenix Lens / Legacy Spec Factory.

The upstream repository is still a company-internal dependency. This contract is
intentionally implementation-neutral: it describes the minimum artifacts and
fields downstream skills need in order to scan source code and produce
structured modernization evidence.

## Purpose

The Program Flow Map export is navigation evidence. It helps downstream skills
decide which programs to scan, which call edges to preserve, and which fields or
files may need deeper inspection.

It is **not** final business truth. Source scanning and SME review are still
required before business rules or modernization decisions are approved.

## Recommended Package Shape

```text
program-flow-export/
  manifest.yaml
  program-list.csv
  call-edges.csv
  source-member-map.csv
  field-trace.csv              # optional
  review-notes.md              # optional
```

## `manifest.yaml`

```yaml
export_id: FLOW-CARD-STATUS-UPDATE-20260627
flow_id: FLOW-CARD-STATUS-UPDATE
flow_name: Card account status update
business_area: Card servicing
source_system: IBM i / AS400
upstream_repo: "TBD: internal Neo4j Program Flow Map repo"
exported_at: "2026-06-27T00:00:00Z"
source_snapshot:
  arcad_xref_export: "TBD"
  source_repo: "TBD"
  source_ref: "TBD"
confidence:
  call_edges: high
  field_trace: medium
notes:
  - Synthetic example. Replace with real export metadata.
```

## `program-list.csv`

| Field | Required | Description |
| --- | --- | --- |
| `flow_id` | Yes | Stable flow identifier |
| `program_name` | Yes | Program or module name |
| `program_type` | Recommended | RPGLE, CLLE, COBOL, SQLRPGLE, DSPF, PRTF, service program, etc. |
| `role` | Recommended | Entry, validation, persistence, audit, report, batch, API, unknown |
| `sequence` | Recommended | Approximate replay order when known |
| `source_hint` | Recommended | Library/source-file/member/path/repo location when known |
| `scan_priority` | Recommended | High, medium, low |
| `notes` | Optional | Human-readable context |

Example:

```csv
flow_id,program_name,program_type,role,sequence,source_hint,scan_priority,notes
FLOW-CARD-STATUS-UPDATE,AMHMAIN,RPGLE,entry,1,QRPGLESRC/AMHMAIN,high,Receives account maintenance request
```

## `call-edges.csv`

| Field | Required | Description |
| --- | --- | --- |
| `flow_id` | Yes | Stable flow identifier |
| `caller` | Yes | Calling program/object |
| `callee` | Yes | Called program/object |
| `relationship_type` | Yes | CALLS, SUBMITS, UPDATES, READS, WRITES, DISPLAYS, PRINTS, UNKNOWN |
| `evidence_ref` | Recommended | ARCAD / XREF / graph evidence identifier |
| `confidence` | Recommended | High, medium, low |
| `notes` | Optional | Human-readable context |

Example:

```csv
flow_id,caller,callee,relationship_type,evidence_ref,confidence,notes
FLOW-CARD-STATUS-UPDATE,AMHVALR,AMHUPDR,CALLS,ARCAD-XREF-0002,high,Validation passes approved update forward
```

## `source-member-map.csv`

| Field | Required | Description |
| --- | --- | --- |
| `program_name` | Yes | Program or object name |
| `library` | Optional | IBM i library |
| `source_file` | Optional | Source physical file |
| `member` | Optional | Source member |
| `repo_path` | Optional | Path in extracted source repository |
| `language` | Recommended | RPGLE, CLLE, COBOL, DDS, SQL, unknown |
| `lookup_status` | Recommended | Found, missing, ambiguous, not_applicable |
| `notes` | Optional | Lookup details |

## `field-trace.csv` Optional

| Field | Required | Description |
| --- | --- | --- |
| `flow_id` | Yes | Stable flow identifier |
| `program_name` | Yes | Program where field is observed |
| `field_name` | Yes | Field, column, data structure, or externally named value |
| `file_or_table` | Optional | File/table where relevant |
| `operation` | Recommended | READ, WRITE, UPDATE, MOVE, VALIDATE, CALCULATE, UNKNOWN |
| `source_identifier` | Optional | Line/routine/evidence reference |
| `business_hint` | Optional | Human or dictionary-provided meaning |
| `confidence` | Recommended | High, medium, low |

## `review-notes.md` Optional

Use this file for:

- unresolved calls
- missing source members
- ambiguous object names
- suspected technical utilities
- SME hints
- data dictionary or business glossary notes
- known exclusions

## Downstream Consumption Rules

Downstream skills should:

- Treat the export as navigation evidence.
- Analyze each distinct source program fresh in the current run.
- Preserve upstream evidence IDs in generated artifacts.
- Mark missing or ambiguous programs as `TBD-*` instead of inventing behavior.
- Promote observed behavior to business rules only after SME review.
- Keep Program Flow Map assumptions separate from source-backed findings.

## Minimum Ready Checklist

Before a Program Flow Map export is used downstream:

- `manifest.yaml` exists and names the flow.
- `program-list.csv` includes all known programs for the selected flow.
- `call-edges.csv` includes caller/callee relationships and evidence refs.
- Source-member hints are present or missing members are explicitly noted.
- Any optional field trace is marked with confidence.
- Known gaps and assumptions are captured in `review-notes.md` or equivalent.
