# Vendor BRD AI POC — SME Review Report

## 1. Review conclusion

**Review outcome: Conditional / not ready for formal BRD approval.**

The POC demonstrates a useful reverse-engineering workbench for RPG/COBOL-style
legacy batch applications. It can organize source-derived evidence into
candidate business objects, persistent entities, interfaces, tasks, rules,
branches, process views, clarification questions, and a generated BRS/FRS-like
document.

However, the demonstration does not yet prove that the generated content is an
approved business requirements baseline. The current output mixes at least
four different artifact layers:

1. legacy technical analysis;
2. inferred business concepts and rules;
3. SME clarification material; and
4. BRD/FRS, role matrix, interface, and acceptance-test content.

This creates a material risk that a polished document will be treated as
business truth even when the underlying statement is only an AI inference or a
candidate extracted from code.

**Recommended disposition:** accept as an internal analysis POC and continue to
a controlled pilot; do not use the current output as an approved BRD, formal
specification, target-system design, audit baseline, or SDD handoff.

## 2. Review scope and information boundaries

| Review dimension | Observable scope |
|---|---|
| Automated modeling | Persistent entities, interfaces, task fields, evidence interfaces, business-object candidates, and rule/branch views |
| Process modeling | Task detail, task relationships, BPMN preview, and semantic dialogue |
| Clarification | Automated question lists and answer/evidence panels; some clarification items remain incomplete |
| Generated document | A multi-section structured draft covering business description, source/evidence, roles, process flow, data/interface tables, and acceptance-test-style tables |

This review assesses only the functions and outputs observable during the POC
presentation. The review team did not independently inspect the source
repository, extraction manifest, model prompts, intermediate JSON, complete BRD
package, evidence coordinates, evaluation set, or SME decision log. The claims
below are therefore review findings about observable capability and governance
risk, not validation of the vendor's underlying implementation.

## 3. What is strong in the POC

### 3.1 Good analysis-to-review workflow direction

The flow from program/source analysis to task, data, rule, process, question,
and document views is directionally sound. It gives SMEs a place to inspect
specific candidates instead of reviewing an unstructured long-form AI answer.

### 3.2 Evidence awareness is visible

The POC presents source lines, program/object identifiers, evidence-interface
counts, and source/evidence columns. The generated document also attempts to
carry source references and an evidence grade. This is the right foundation for
an auditable reverse-engineering process.

### 3.3 Human clarification is included

The automated requirements-clarification view is a valuable feature. The POC
recognizes that code cannot fully establish business intent and that questions
must be sent back to a human reviewer.

### 3.4 The output is operationally useful as a draft

The demonstrated output includes business-facing sections, process steps,
roles, interfaces, data objects, and acceptance-test-style rows. With clear
status labels and evidence links, these could accelerate discovery and review.

## 4. Material SME findings

| ID | Severity | Finding | SME implication | Required treatment |
|---|---|---|---|---|
| SME-001 | **Blocker** | Evidence provenance is not yet demonstrated at claim level. The document shows broad sources such as a semantic snapshot or `businessFunctionLogicDigest`, but not a deterministic evidence coordinate for every business statement. | SMEs cannot efficiently verify whether a statement came from source code, runtime evidence, a document, or AI inference. | Every `BEH`, rule, data object, flow step, question, and test row must link to stable evidence IDs plus program/member/line or document/page coordinates. |
| SME-002 | **Blocker** | Observed behavior and inferred business intent are visually mixed. Candidate business objects, persistent entities, rule branches, and generated prose can look equally authoritative. | A legacy implementation detail or defect may be mistaken for an approved business rule. | Use mandatory knowledge/status labels: `observed`, `inferred`, `candidate`, `SME-confirmed`, `contradicted`, `unresolved`, and `not evidenced`. |
| SME-003 | **Blocker** | The clarification loop is not shown as a governed decision process. The presented question-and-answer flow does not establish answer author, role, date, scope, evidence attachment, disposition, or write-back history. | An answer cannot be treated as SME approval, and later reviewers cannot reconstruct who confirmed what. | Persist one decision record per question/rule with SME identity, role, date, response, evidence, disposition, and re-review history. |
| SME-004 | **High** | BRD, FRS, technical analysis, interface catalog, role matrix, and acceptance-test content are combined in one generated document. | The document may be used for a downstream purpose it was not actually designed to satisfy. | Generate separate artifacts or explicit sections with separate status/gates: legacy BRD, technical evidence appendix, open-question ledger, and formal test/spec outputs. |
| SME-005 | **High** | The demonstrated process model is primarily a source-derived task/call-flow view. It does not prove complete business scenarios, actors, triggers, normal path, exception path, restart path, or business outcome. | A readable flow diagram may still omit operationally important behavior. | Require scenario completeness checks for trigger, actor, preconditions, inputs, decisions, outputs, exceptions, retries/restarts, control totals, and completion criteria. |
| SME-006 | **High** | Persistent-entity recommendations and business-object candidates are presented as useful domain abstractions, but no business ownership, lifecycle, identity, or authoritative-system confirmation is shown. | Technical structures may be promoted prematurely into target domain entities. | Keep them as candidate abstractions until an SME confirms business meaning, ownership, lifecycle, identifier, and source-of-truth boundary. |
| SME-007 | **High** | Role and permission tables include operational roles and permissions, but the demonstration does not show evidence for actual authorization, separation of duties, emergency access, or approval policy. | Generated access rules could be interpreted as security requirements. | Mark role/security content as observed, inferred, or open; require security-owner confirmation before approval. |
| SME-008 | **High** | The generated acceptance-test-style rows appear to contain expected outcomes, while no runtime samples, golden-master comparison, or test execution evidence is shown. | A plausible expected result can be mistaken for a verified legacy outcome. | Keep these as scenario seeds until runtime evidence or SME-approved expected behavior exists; do not call them formal acceptance criteria yet. |
| SME-009 | **Medium** | The system appears to support counts and candidate approval, but completeness and coverage metrics are not defined. | “117 evidence interfaces” or “631 task fields” describes volume, not quality or coverage. | Report extraction coverage, unresolved ratio, contradiction count, source coverage, question closure rate, and sampled precision/recall against a labeled benchmark. |
| SME-010 | **Medium** | The generated draft contains repeated “open question” placeholders for document control and scope fields. | The document is clearly still a draft, but its visual polish may obscure that status. | Add a prominent non-approval watermark/status, owner, review scope, version, evidence snapshot hash, and blocking-TBD count. |
| SME-011 | **Medium** | The POC does not demonstrate contradiction handling, version drift, rerun reproducibility, or source snapshot immutability. | Results may change silently when code, prompts, models, or source indexes change. | Store source/model/prompt/version metadata and produce a diff plus impact report for every regeneration. |
| SME-012 | **Medium** | Security and data-handling controls are not demonstrated. Source code, business data, logs, and potentially personal or financial fields may be sent to an AI service. | The POC cannot yet be cleared for production or sensitive client data. | Provide hosting/data-flow diagram, retention policy, access control, redaction rules, tenant isolation, model-training opt-out, and audit logs. |

## 5. BRD-specific assessment

| BRD capability | Assessment | Comment |
|---|---|---|
| Function purpose and scope | Partial | The generated document has a purpose section, but scope fields remain open and the business boundary is not independently confirmed. |
| Business scenarios / use cases | Partial to weak | Program/task descriptions are present; end-to-end business scenarios and exception scenarios are not sufficiently demonstrated. |
| Channels and touchpoints | Not proven | Batch scheduler, operator console, downstream files/APIs, reports, and manual intervention may be visible in code but are not shown as a governed BRD section with evidence. |
| System interfaces | Partial | Interface and data tables are useful, but contract ownership, direction, timing, failure semantics, versioning, and reconciliation are not established. |
| Process flow | Partial | BPMN/task flow is a useful starting point; restart/recovery, control points, and business outcomes need explicit review. |
| Validation rules | Partial | Rules and branches are surfaced, but rule status and business intent are not separated consistently. |
| Error handling | Weak / not proven | The demo does not show a complete error taxonomy, operator action, retry/restart behavior, partial-success handling, or escalation path. |
| Dependencies | Partial | Program/object relationships are shown; business, operational, scheduling, data, and external dependency ownership is not fully demonstrated. |
| Traceability | Partial | IDs and source columns exist, but end-to-end bidirectional traceability is not proven. |
| SME approval gate | Not proven | A question screen is not equivalent to a named, dated, scoped SME sign-off. |

## 6. Key risks if adopted without controls

1. **False business certainty:** code patterns are converted into requirements
   without separating implementation behavior from business intent.
2. **Approval laundering:** a well-formatted document gives inferred content the
   appearance of SME-approved truth.
3. **Incomplete batch behavior:** restart, rerun, recovery, control totals,
   scheduling windows, and operational exceptions are easy to miss in a static
   source-derived model.
4. **Traceability breakage:** a source name or digest is not sufficient to
   reproduce the exact evidence behind a claim.
5. **Downstream contamination:** draft BRD content may be reused as FRS,
   acceptance criteria, target design, or migration scope before review gates
   are cleared.
6. **Sensitive-data exposure:** code and production-like extracts may cross
   tenant or model boundaries without an approved data-handling design.

## 7. Minimum acceptance criteria for a controlled pilot

The vendor should demonstrate the following on one bounded capability, using a
known labeled sample and a named SME:

- A source/evidence manifest with immutable snapshot ID, authorization,
  sensitivity, redaction status, and exact coordinates.
- Claim-level links for at least 20 sampled behaviors/rules/flows, with an SME
  able to navigate from document statement to source evidence in one or two
  steps.
- Separate rendering of observed behavior, inferred rule, candidate object,
  open question, and SME-approved decision.
- Question workflow with assignee, SME role, response, evidence, date, decision
  status, and audit history.
- Contradiction and missing-evidence handling that blocks approval rather than
  silently choosing one answer.
- Reproducible rerun using the same source snapshot, model/prompt version, and
  configuration, plus a machine-readable diff when any of them changes.
- Explicit batch controls: trigger, scheduling, restart/recovery, retry,
  duplicate handling, partial failure, control totals, reconciliation, and
  operator intervention.
- A BRD package with sections for purpose, scenarios, channels/touchpoints,
  interfaces, process, validation, error handling, and dependencies; each
  section must show evidence coverage and unresolved TBDs.
- A formal sign-off record naming the SME, role, date, scope, and limitations;
  no AI-generated content may be promoted to approved without that record.
- Security/data-processing evidence for source code, logs, extracts, prompts,
  model hosting, retention, and access control.

## 8. Recommended pilot scope and review method

Use one bounded batch capability with:

- 5–10 programs;
- one normal path and at least three exception paths;
- at least one external interface and one persistent data structure;
- available source-line evidence and a small set of runtime samples;
- one business SME, one IBM i technical SME, and one operations/security
  reviewer.

Review a stratified sample rather than only the best-looking screens:

1. five high-confidence observed behaviors;
2. five inferred rules;
3. five candidate data/business objects;
4. five process or exception paths;
5. all unresolved or contradictory items.

The pilot should measure precision, evidence-link success, SME correction rate,
question closure rate, reproducibility, and time saved. Completion should be
based on these measures, not on the number of generated pages or extracted
objects.

## 9. Final SME recommendation

**Recommendation: Proceed with conditions.**

The POC is worth continuing because it addresses a real discovery bottleneck:
turning difficult legacy source analysis into reviewable visual and document
artifacts. The vendor should first harden the evidence and governance layer,
then validate semantic accuracy on a bounded capability.

Until SME-002, SME-003, SME-004, and SME-008 are closed, the output should be
labeled:

> Internal POC draft — source-derived analysis and AI-assisted hypotheses; not
> an approved BRD, formal requirement, acceptance baseline, or target design.

This review does not constitute approval of any generated business rule,
business object, role/permission, interface contract, acceptance criterion, or
modernization decision.
