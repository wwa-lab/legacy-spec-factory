# Output Contract: Module Context Intake

This reference defines the required files under
`00_context_packages/<MODULE-SLUG>/`.

The context package is an intake artifact. It is not an approved module
analysis, BRD, spec, or modernization decision.

This package does not create intake flow Markdown files. The canonical
module-analysis flow files in `04_modules/<MODULE-SLUG>/` are created only by
`legacy-ibmi-module-analyzer`.

## Package Layout

```text
00_context_packages/<MODULE-SLUG>/
|-- context-index.yaml
|-- rag-evidence-map.md
|-- contradiction-log.md
`-- open-questions.md
```

## `context-index.yaml`

Required shape:

```yaml
schema_version: "0.1"
package_type: module_context_intake
module:
  slug: CREDIT-CHECK
  module_id: MODULE-CREDIT-CHECK-001
  business_name: Credit Check
  scope_statement: "SME-confirmed scope statement."
  owner: "Role or named SME"
  source_state: draft | sme_confirmed | approved_with_non_blocking_tbd

intake:
  skill: legacy-module-context-intake
  version: v0.1.12
  generated_at: "YYYY-MM-DDTHH:MM:SSZ"
  status: ready_for_module_analysis
  decision_reason: "Short reason."
  downstream_next_step: legacy-ibmi-module-analyzer

run_validation:
  structural_status: not_run
  structural_method: not_run
  validator_command: "py -3 skills/legacy-module-context-intake/scripts/validate_context_package.py 00_context_packages/CREDIT-CHECK"
  artifact_preview_status: not_requested
  artifact_preview_reason: "Preview is optional; context Markdown files and evidence maps are the canonical package."
  completion_boundary: stop_after_writeback

evidence_authorization:
  status: approved | synthetic_non_production | public | blocked | unknown
  evidence_manifest: "evidence/redacted/evidence-manifest.yaml"
  redaction_notes: "Short note."

rag_runs:
  - run_id: RAG-20260521-001
    source_path: "rag_runs/CREDIT-CHECK/RAG-20260521-001/rag-run-index.yaml"
    source_snapshot: "ibmi-export-2026-05-21"
    dictionary_version: "dict-v34"
    arcad_ref_snapshot: "arcad-ref-2026-05-21"
    sensitivity: synthetic_non_production

document_evidence_inputs:
  - docset_id: DOCSET-CREDIT-CHECK-001
    manifest_path: "00_context_packages/CREDIT-CHECK/document-intake/CREDIT-CHECK-DOCS/intake.manifest.yaml"
    gate: ready_with_warnings
    evidence_coordinates: "00_context_packages/CREDIT-CHECK/document-intake/CREDIT-CHECK-DOCS/evidence-coordinates.md"
    extraction_warnings: "00_context_packages/CREDIT-CHECK/document-intake/CREDIT-CHECK-DOCS/extraction-warnings.md"
    source_quality: partial

input_files:
  - role: flow_hydration_summary
    path: "rag_runs/.../flow-hydration-summary.md"
    required: true
    status: present

output_files:
  rag_evidence_map: rag-evidence-map.md
  contradiction_log: contradiction-log.md
  open_questions: open-questions.md

coverage:
  context_coverage_ready: true
  source_snippets_mapped: true
  dictionary_context_mapped: true
  contradictions_carried_forward: true
  open_questions_carried_forward: true
  coverage_dimensions:
    business_process: absent | partial | usable | strong
    system_interfaces: absent | partial | usable | strong
    program_anchors: absent | partial | usable | strong
    data_anchors: absent | partial | usable | strong
  technical_anchor_coverage:
    program_anchors: absent | partial | usable | strong
    data_anchors: absent | partial | usable | strong
    object_map_present: true | false
    code_backed_analysis_present: true | false
  brd_functional_analysis_hints:
    function_purpose: absent | partial | usable | strong
    business_scenarios: absent | partial | usable | strong
    channels: absent | partial | usable | strong
    user_touchpoints: absent | partial | usable | strong
    system_interfaces: absent | partial | usable | strong
    process_flow: absent | partial | usable | strong
    validation_rules: absent | partial | usable | strong
    error_handling: absent | partial | usable | strong
    dependencies: absent | partial | usable | strong
    optional_security_auth: absent | partial | usable | strong
    optional_workflow_design_notes: absent | partial | usable | strong
    optional_source_document_mapping: absent | partial | usable | strong

gates:
  evidence_authorization_gate: pass | warning | blocked
  module_scope_gate: pass | warning | blocked
  context_coverage_gate: pass | warning | blocked
  contradiction_visibility_gate: pass | warning | blocked
  rule_promotion_gate: pass | warning | blocked

blocking_items:
  - id: TBD-CREDIT-CHECK-001
    reason: "Missing evidence authorization."
    owner: legacy-ibmi-evidence-intake
```

Rules:

- `status` must be one of:
  - `ready_for_module_analysis`
  - `ready_with_warnings`
  - `blocked_pending_evidence`
  - `blocked_pending_contradiction_review`
  - `blocked_pending_scope` (legacy compatibility only; prefer `ready_with_warnings` with scope TBDs)
- `downstream_next_step` is normally `legacy-ibmi-module-analyzer` unless
  blocked. It may be `legacy-brd-writer` only for an explicit internal POC BRD
  route where `status: ready_with_warnings` and downstream BRD status will be
  `poc_draft`.
- `run_validation.structural_status` records `pass`, `pass_with_warnings`,
  `blocked`, `not_run`, `tool_unavailable`, or
  `tool_unavailable_hosted_agent`.
- `run_validation.artifact_preview_status` records `not_requested`,
  `skipped_large_package`, `passed`, `failed`, or `timed_out`. Preview is an
  optional visual aid, not a package gate.
- `run_validation.completion_boundary: stop_after_writeback` tells the agent
  to stop after package files, validation status, and any workflow-state
  write-back are recorded.
- `blocking_items[]` is empty only when all gates pass or all remaining items
  are explicitly non-blocking.
- `document_evidence_inputs[]` is the preferred upstream record for
  document-first work. Missing OCR, missing Markdown, blocked optional
  converters, and partial extraction become low-confidence `TBD-*` items.
- `coverage.brd_functional_analysis_hints` is advisory. It tells downstream
  module analysis and BRD preparation which packaged context can feed the
  SME-required BRD sections 1-9 and optional sections 10-12. Missing or partial
  hints must stay visible as gaps; this skill must not fill them by inference.
  For internal POC BRDs, hints may become low-confidence review hypotheses only,
  never approved BRD conclusions.
- `coverage.technical_anchor_coverage` is also advisory. It tells the
  orchestrator whether the package contains IBM i program/data anchors and
  whether the code evidence backbone already exists. Program/file names in
  context are not a substitute for `01_inventory/object-map.md`, approved
  program analyses, or approved flow analyses.

## Context Coverage

Context coverage is recorded in `context-index.yaml.coverage` and in the
evidence/candidate rows of `rag-evidence-map.md`. Do not create separate
standalone flow-view intake files.

Coverage dimensions:

- **Business process**: actors, business events, BAU rhythm, manual
  intervention, exception lifecycle, candidate business-rule seeds.
- **System interfaces**: upstream/downstream systems, interfaces, integration
  patterns, synchronous/asynchronous boundaries, security/SLA notes.
- **Program anchors**: entry programs, call paths, shared programs, runtime
  trigger model, suggested program-analysis focus.
- **Data anchors**: data objects, field dictionary mappings, lifecycle,
  derivation gaps, data ownership, cross-module dependencies.

Candidate seed rules:

- `Candidate Statement` is the business-language candidate or the analysis
  action whose business meaning must be resolved.
- `Business Signal` explains the business behavior, decision, SLA, exception,
  ownership, or control affected by the candidate.
- `Evidence Basis` carries program names, file names, field names, source
  snippets, runtime observations, dictionary IDs, and RAG IDs.
- For View 3 technical candidates, name the business decision that depends on
  the program-analysis focus; do not make a program name the capability
  boundary.

## `rag-evidence-map.md`

Required sections:

```markdown
# RAG Evidence Map - <MODULE-SLUG>

## RAG Runs
| Run ID | Source Snapshot | Dictionary Version | Sensitivity | Status |

## Source Snippets
| Evidence ID | Artifact | Lines | Summary | Strength | Coverage / Consumer |

## Runtime Observations
| Evidence ID | Source | Lines | Observed Detail | Coverage / Consumer |

## Dictionary Mappings
| Standard Field ID | Legacy Reference | Meaning | Owner | Status | Coverage / Consumer |

## Impact Scope
| Target | Impact Type | Evidence | Confidence | Coverage / Consumer |

## Candidate Facts
| Candidate ID | Statement | Business Signal | Evidence Basis | Promotion Status | Required Review |
| --- | --- | --- | --- | --- | --- |
```

Rules:

- Preserve original RAG IDs. Do not rename `SNP-*`, `RUN-*`, `DD-*`,
  `RAG-CAND-*`, or `RAG-CONFLICT-*`.
- `Candidate Facts` may not use `approved` as `Promotion Status`; use
  `needs_sme_review`, `blocked`, or `deferred`.
- Program names, files, fields, and source snippets belong in `Evidence Basis`.
  The `Statement` and `Business Signal` columns must remain readable without
  knowing the raw object names.
- If a view cites an evidence ID, that ID must appear here.

## `contradiction-log.md`

Required sections:

```markdown
# Contradiction Log - <MODULE-SLUG>

## Summary
- status: none_found | open_contradictions | blocked
- evaluated_checks_present: true | false

## Open Contradictions
| Conflict ID | Type | Summary | Evidence A | Evidence B | Owner | Blocking |

## Evaluated Checks
| Check | Result | Notes |

## Routing
[What must happen before module analysis or BRD writing.]
```

Rules:

- "No contradictions found" is valid only when `Evaluated Checks` is present.
- Blocking contradictions set `context-index.yaml.intake.status` to
  `blocked_pending_contradiction_review`.
- Contradictions are never silently resolved by this skill.

## `open-questions.md`

Required sections:

```markdown
# Open Questions - <MODULE-SLUG>

## Carry-Forward Questions
| TBD ID | Source ID | Question | Owner | Route To | Needed Before Approval |

## Non-Blocking Questions
| TBD ID | Source ID | Question | Owner | Carry Forward To |

## Non-Blocking Assumptions
| Assumption ID | Statement | Evidence | Review Status |

## Recommended Next Prompt
[Prompt for the next skill.]
```

Rules:

- Mint `TBD-*` for unresolved questions that need Legacy Spec Factory tracking.
- Preserve RAG gap IDs as `Source ID`; do not replace them with TBD IDs.
- Use `blocking: yes` only when the next step would invent facts without the
  answer.

## Promotion Rules

Allowed:

- RAG candidates -> `Candidate Seeds` or `Candidate Facts`
- Retrieval gaps -> `TBD-*` open questions
- Contradictions -> `contradiction-log.md`
- Source snippets/runtime observations -> evidence map entries
- Approved dictionary terms -> terminology context

Forbidden:

- RAG candidates -> approved `BR-*`
- Dictionary terms -> source-proven behavior without code/runtime evidence
- One runtime sample -> normal operating frequency
- No contradiction found -> approval
- `ready_with_warnings` -> downstream approval
- `ready_with_warnings` -> approved BRD/spec/handoff readiness
- Owner-accepted sparse context -> approved facts, approved `BR-*`, or BRD
  claims without later corroboration

## Local Validation

Use the bundled validator for package-level checks only outside GitHub Copilot
hosted-agent mode. In hosted-agent mode, do not run Python, do not create a
virtual environment, and do not wait on environment setup; record validation as
`tool_unavailable_hosted_agent` and report the validator script path as manual
follow-up text.

Manual validator path:
`skills/legacy-module-context-intake/scripts/validate_context_package.py` with
package argument `00_context_packages/<MODULE-SLUG>/`.

The validator uses only Python's standard library. Run it only with an
already-available Python interpreter; do not create a virtual environment,
install dependencies, or wait on interactive environment configuration. If
interpreter startup remains configuring/evaluating, record validation as
`tool_unavailable`, keep the package out of `ready_for_module_analysis`, and
report the manual command above. The package may continue as
`ready_with_warnings` when the warning and carry-forward TBDs are recorded.

It checks required files, status vocabulary, output-file references, view-to
evidence-map linkage, contradiction-log completeness, and RAG candidate
promotion status. It is a structural guard only; SME approval and semantic
review are still required downstream.

Previewing generated context Markdown is not part of local validation. Do not
open IDE, browser, Mermaid, or Markdown previews unless the user explicitly
asks. For large modules, set `run_validation.artifact_preview_status:
skipped_large_package` or `not_requested`, then stop after
`completion_boundary: stop_after_writeback` is recorded.
