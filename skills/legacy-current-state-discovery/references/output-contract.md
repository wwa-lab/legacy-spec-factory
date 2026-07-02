# Output Contract

## Package Location

Create one package per coherent discovery focus:

```text
00_context_packages/<MODULE-SLUG>/current-state-discovery/<DISCOVERY-SLUG>/
```

`MODULE-SLUG` is the owning module or system area. `DISCOVERY-SLUG` is the
business function, process, or event under review, such as `REPORT-LOST` or
`ISSUER-AUTHORIZATION`.

## Required Files

| File | Purpose |
| --- | --- |
| `discovery-index.yaml` | Package control file, source list, status, validation summary, and handoff routing. |
| `document-master-index.md` | Human-readable index of all selected sources, including unparsed or not-reviewed items. |
| `behavior-claim-ledger.csv` | Atomic claim ledger that separates meaningful current-state behavior from source inventory, diagram labels, and code-analysis routing hints. |
| `functional-discovery-report.md` | SME/BA-facing report using the expected business review structure. |
| `function-catalog.yaml` | Structured current-state function/component candidates. |
| `project-derived-feature-index.yaml` | Features or requirements introduced by project documents, separated from legacy current state. |
| `validation-catalog.yaml` | Detailed validation rules, condition patterns, pass/fail outcomes, and gaps. |
| `calculation-catalog.yaml` | Formula, fee, rate, threshold, rounding, and calculation method evidence. |
| `interface-register.yaml` | Upstream/downstream applications, APIs, files, messages, batch jobs, and handoffs. |
| `channel-ui-report-catalog.md` | Channels, UI surfaces, reports, notifications, and customer/staff touchpoints. |
| `accounting-gl-ie-index.yaml` | Accounting, GL, IE, posting, settlement, reconciliation, and control impacts. |
| `traceability-matrix.csv` | Candidate-to-source cross-reference. |
| `open-questions-and-gaps.md` | SME questions, missing evidence, code-analysis routing, and unresolved contradictions. |

## Package Status

Use one of:

- `draft`: extraction is incomplete or not yet checked.
- `ready_for_sme_review`: required files exist and material candidates have
  traceability, but SME review is pending.
- `ready_with_warnings`: usable for downstream context with visible gaps,
  unsupported optional files, or non-blocking weak evidence.
- `blocked_pending_evidence`: no usable evidence, unknown sensitivity, missing
  source authorization, or missing source documents.
- `blocked_pending_code_analysis`: requested detail requires code/program-flow
  evidence before it can be stated.
- `blocked_pending_scope`: the discovery focus spans unrelated modules or
  cannot be named.

## Candidate Function Shape

Use `CAND-*` for draft functional candidates unless the project profile defines
a functional ID prefix. Do not mint `BR-*` from this skill.

Use these default namespaces unless a project profile defines stricter IDs:

- `BCL-*`: atomic behavior claims in `behavior-claim-ledger.csv`
- `CAND-*`: current-state function candidates
- `TBD-*`: open questions, gaps, contradictions, and code-analysis requests
- `SRC-*`, `DOC-*`, or provided source IDs: source artifacts and evidence

Do not use one generic `CLM-*` namespace for behavior claims, gaps, functions,
and sources in the same package.

Required fields for each current-state function candidate:

```yaml
- candidate_id: CAND-<CAPABILITY-SLUG>-001
  name: "<business-readable function name>"
  source_type: current_state
  domain: "<business domain>"
  region: "<region or shared>"
  behavior_claim_ids: []
  business_requirement:
    happy_path: []
    unhappy_path: []
    specific_rule_logic: []
    eligibility: []
    conditions: []
  process_flow: []
  channels:
    customer: []
    staff: []
  ui_reports_notifications: []
  upstream_downstream_applications: []
  system_configuration_parameters: []
  validations: []
  calculations: []
  interfaces: []
  accounting_gl_ie_impact: []
  exception_handling: []
  operational_procedure: []
  limitations_pain_points: []
  gap_analysis: []
  cross_reference_brd: []
  evidence_ids: []
  source_documents: []
  discovery_confidence: Confirmed | Strongly Indicated | Inferred | Gap | Not Reviewed
  review_status: draft | needs_sme_review | approved | rejected | retired
  open_questions: []
```

## Behavior Claim Ledger Header

`behavior-claim-ledger.csv` must use this exact header:

```csv
claim_id,item_type,item_id,business_area,business_meaning,trigger_condition,system_behavior,source_id,source_location,evidence_id,evidence_strength,confidence,review_status,gap_id,next_action,notes
```

Each non-gap claim must describe a behavior useful for SME review. Source
inventory facts such as a file name, program name, diagram node, or folder
membership can appear only when the row clearly routes to evidence retrieval,
SME review, or code analysis.

## Functional Report Rules

Use table-led sections for populated report content. At minimum, material
statements in `functional-discovery-report.md` must expose the related behavior
claim or candidate ID, confidence, source locator, and gap or next action.

`Gap Analysis` must be a table with these fields:

```text
Gap ID | Area | Missing / Unclear Evidence | Impact | Owner / Route | Next Action | Status
```

## Traceability Matrix Header

`traceability-matrix.csv` must use this exact header:

```csv
item_id,item_type,item_name,claim_summary,source_id,source_location,evidence_id,evidence_strength,confidence,review_status,gap_id,notes
```

## Handoff Rules

- `ready_for_sme_review` and `ready_with_warnings` may feed SME review or
  low-confidence module context.
- A package with `blocked_pending_code_analysis` must route the named programs,
  flow, fields, or transaction/message types to the IBM i analyzers before
  code-level facts are stated.
- A package with `blocked_pending_evidence` must not feed BRD or spec work.
- This skill does not approve BRD facts, business rules, acceptance criteria,
  modernization decisions, or target-system design.
