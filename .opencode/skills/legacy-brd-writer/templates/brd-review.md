# BRD Review Checklist: `<CAPABILITY-NAME>`

**BRD ID:** `BRD-<CAPABILITY-SLUG>-001`  
**Capability Owner (SME):** `<Name / Role>`  
**Review Date:** `<YYYY-MM-DD>`
**Mode:** `standard` | `daily_delivery` | `internal_poc` | `approved_baseline`
**Status:** `poc_draft` | `delivery_draft` | `in_review` | `approved` | `needs_revision` | `rejected`
**Evidence Mode:** `code_backed` | `daily_delivery` | `context_only` | `internal_poc`
**Review Policy:** `standard_gate` | `exception_only` | `poc_only`

---

## Reviewer Guidance

This checklist is completed by the **capability owner SME**. The reviewer must
validate that the BRD is accurate, complete, and safe to use as the
requested review target. For standard review, that target may be the
legacy-system discovery baseline. For daily delivery, it is only current
iteration acceptance. It is not an SDD handoff approval.

**What to check:**

1. Are required BRD sections 1-9 present and useful: function purpose, business
   scenarios, channels, user touchpoints, system interfaces, process flow,
   validation rules, error handling, and dependencies?
2. Is the **process flow** understandable and accurate enough for business
   discussion?
3. Are the **observed behaviors** accurate to legacy system reality?
4. Are the **inferred business rules** actually business rules (not
   implementation artifacts)?
5. Is the **scope and boundary** correct?
6. If a scope clarification is present, does it ask the right SME boundary
   question instead of describing document-analysis difficulty?
7. Are there **unspoken rules** the code doesn't show (BAU, manual procedures)?
8. Are optional sections 10-12 included only when useful and evidence-backed?
9. Are the **TBDs** correctly categorized and achievable?
10. Do the **validation scenario seeds** cover the important business cases?
11. Is the BRD ready for **legacy-system discovery decisions** without
    re-interrogating you?

---

## Author/Synthesizer Preflight

Complete this before requesting SME review. These are artifact-readiness checks;
do not copy them into `brd.md` as a `Success Criteria`, `Success Criiteria`, or
similar document-quality section.

- [ ] The BRD clearly explains the business boundary, primary actors, trigger
      events, key states, business outcomes, and major exceptions.
- [ ] Required sections 1-9 are present: Function Purpose, Business Scenarios /
      Use Cases, Channels, User Interface / User Touchpoints, System
      Interfaces, Process Flow, Validation Rules, Error Handling, Dependencies.
- [ ] Optional sections 10-12 are included only when evidence-backed or
      SME-confirmed: Security / Authentication Requirements, Supporting
      Workflow or Design Notes, Source Document Mapping.
- [ ] Input-package artifacts such as module analysis, flow diagrams,
      functional specifications, technical design notes, runtime evidence, and
      program analyses map to BRD sections or traceability entries instead of
      remaining disconnected references.
- [ ] For `code_backed` mode, `01_inventory/object-map.md`, in-scope
      `program-analysis.md`, and in-scope `flow-*.md` artifacts are present,
      approved, and cited in traceability.
- [ ] For `context_only` mode, the named risk acceptance is recorded, missing
      object-map / program / flow artifacts are `TBD-*` blockers, and this BRD
      is not marked `approved`.
- [ ] For `daily_delivery` mode, exception-only review is recorded, blocking
      exceptions are listed, non-critical findings are carried to
      `delivery-risk-summary.md`, and this BRD is not marked `approved`.
- [ ] For `internal_poc` mode, the requester/project POC owner is recorded,
      missing object-map / program / flow / SME / OCR / source-eligibility items
      are visible as approval/spec blockers, weak statements are marked as
      low-confidence hypotheses, and this BRD is not used for spec, SDD handoff,
      or delivery decisions.
- [ ] Business owners and SMEs can use the BRD to confirm initial scope and
      inferred rule direction.
- [ ] `brd.md` contains no generic document-success criteria, formal `AC-*`
      acceptance criteria, formal `TC-*` test cases, or target-platform
      decisions.
- [ ] `brd.md` contains no old-vs-new comparison, No-gap / Gap1 / Gap2
      classification, target-system disposition, or SDD handoff content.

---

## Required Functional Analysis Coverage

### Do sections 1-9 cover the SME-required functional analysis areas?

- [ ] **Yes** — function purpose, business scenarios, channels, user
      touchpoints, system interfaces, process flow, validation rules, error
      handling, and dependencies are covered
- [ ] **Partial** — one or more required areas need clarification or evidence
- [ ] **No** — the BRD is missing required functional-analysis coverage

**Reviewer Notes:**

```
<Space for SME feedback on missing or weak required sections>
```

---

## Process Flow

### Can a business reviewer discuss section 6 without relying on program names?

- [ ] **Yes** — business trigger, parties, outcomes, controls, and exceptions
      are clear
- [ ] **Partial** — directionally useful, but needs clearer business language
      or missing process context
- [ ] **No** — reads like a technical call chain or object inventory

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

## Observed Behaviors

### `BEH-<CAPABILITY-SLUG>-001`: Does this match legacy system behavior?

- [ ] **Yes** — accurate for the discovery baseline
- [ ] **Partial** — mostly correct, but needs clarification (see notes)
- [ ] **No** — inaccurate or missing key behavior (block until revised)

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

### `BEH-<CAPABILITY-SLUG>-002`: Does this match legacy system behavior?

- [ ] **Yes**
- [ ] **Partial**
- [ ] **No**

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

## Inferred Business Rules

### `BR-<CAPABILITY-SLUG>-001`: Is this a real business rule?

- [ ] **Yes** — this is a business rule; mark for promotion in spec phase
- [ ] **No** — this is implementation artifact, not a rule (remove or clarify)
- [ ] **Unclear** — needs more evidence or discussion (block until resolved)

**Reviewer Decision:** `approve` | `reject` | `needs_evidence`

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

### `BR-<CAPABILITY-SLUG>-002`: Is this a real business rule?

- [ ] **Yes**
- [ ] **No**
- [ ] **Unclear**

**Reviewer Decision:** `approve` | `reject` | `needs_evidence`

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

## Scope & Boundaries

### Is the capability scope correct?

- [ ] **Yes** — in_scope and out_of_scope are accurate
- [ ] **Partial** — some items are mis-categorized (see notes)
- [ ] **No** — boundary is wrong or contested

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

### Is any scope clarification framed as a business boundary question?

- [ ] **Yes** — the clarification asks for SME confirmation of actors,
      triggers, state transitions, handoffs, or in/out-of-scope boundaries
- [ ] **Not applicable** — no scope clarification is needed
- [ ] **No** — the section reads like source-document analysis, technical
      coupling, or delivery rework risk instead of a SME decision point

**Reviewer Notes:**

```
<Space for SME feedback>
```

---

### Are there unspoken business rules or BAU procedures not captured in the BRD?

- [ ] **No** — everything material is captured
- [ ] **Yes** — there are gaps (describe below)

**Gaps Identified:**

```
<Space for SME to list missing business context>
```

---

## Validation Scenario Seeds

### Do the `VAL-*` scenarios cover the important business cases for this BRD?

- [ ] **Yes** — happy path, exception, boundary, and manual-review scenarios are
      sufficient for SME discovery review and later planning if a gap is
      promoted
- [ ] **Partial** — coverage is directionally right, but scenarios need
      additions or clarification (see notes)
- [ ] **No** — scenario coverage misses material business behavior

**Reviewer Notes:**

```
<Space for SME feedback on validation scenario coverage>
```

### Are any scenarios overstated as formal tests?

- [ ] **No** — scenarios are business validation seeds only
- [ ] **Yes** — remove or rewrite formal acceptance criteria, formal test case
      language, target implementation detail, or invented expected output

**Reviewer Notes:**

```
<Space for SME feedback on scenario boundaries>
```

---

## Open Questions (TBDs)

### Are the TBDs correctly categorized and achievable?

- [ ] **All TBDs are valid** — correctly categorized, achievable, appropriately
      blocking/non-blocking
- [ ] **Some TBDs need refinement** — description or resolver needs clarity
      (see notes)
- [ ] **TBD handling is blocked** — cannot move forward until resolved

**Reviewer Notes:**

```
<Space for SME feedback on TBDs>
```

---

## Completeness & Discovery Readiness

### Is the BRD ready to use as the migration-discovery baseline?

- [ ] **Yes** — all legacy facts validated, no silent gaps, migration
      stakeholders can use it later as input to a separate comparison process
- [ ] **Almost** — minor gaps (see notes); recommend minor revision before
      using as the baseline
- [ ] **No** — major issues (see notes); block until resolved

**Readiness Assessment:**

```
<Space for overall SME judgment>
```

---

## Final Decision

### BRD Status Transition

**Current Status:** `in_review`

**Final Status:**

- [ ] `approved` — Use as the legacy-system discovery baseline
- [ ] `approved_with_non_blocking_tbd` — Use as discovery baseline; carry
      non-blocking TBDs listed below
- [ ] `accepted_for_daily_delivery` — Use for the current daily delivery
      iteration only; standard BRD approval, spec writing, SDD handoff, audit
      baseline, and knowledge publication remain blocked
- [ ] `poc_draft` — Use only for internal POC discussion; standard BRD approval,
      spec writing, SDD handoff, and delivery decisions remain blocked until
      listed approval/spec blockers are resolved
- [ ] `needs_revision` — Return to author with specific feedback
- [ ] `rejected` — Do not use as migration-discovery baseline

**Non-Blocking TBDs (if approved_with_non_blocking_tbd):**

```
<List any non-blocking TBDs that later comparison, gap analysis, or
spec-writing should carry forward>
```

**Daily Delivery Risk Summary (if accepted_for_daily_delivery):**

```
<Reference 07_sme_reviews/<CAPABILITY-SLUG>/daily-delivery-review-v1/delivery-risk-summary.md
and list any accepted delivery risks, owner, and follow-up date.>
```

---

## Sign-Off

**Capability Owner (SME):**

- **Name:** `<Full name>`
- **Role:** `<Title>`
- **Date:** `<YYYY-MM-DD>`
- **Signature / Approval:** `<Electronic or written sign-off>`

**Author/Synthesizer:**

- **Name:** `<Claude Code or Agent name>`
- **Date:** `<YYYY-MM-DD>`

---

## Next Steps

If `approved` or `approved_with_non_blocking_tbd`:
- Use the BRD as the legacy-system discovery baseline
- Run old-vs-new comparison only after new-system context is available; record
  No-gap / Gap1 / Gap2 disposition outside the BRD Package
- Route to `legacy-spec-writer` only for items explicitly promoted beyond
  discovery; spec-writer will generate formal `AC-*` and `DEC-*`

If `needs_revision`:
- Author revises BRD based on feedback
- SME re-reviews before approval

If `rejected`:
- Escalate to product/architecture leadership for path forward
