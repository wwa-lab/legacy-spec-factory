# Daily Delivery Mode

`daily_delivery` is the default lightweight operating mode for day-to-day BRD
delivery. It runs the same evidence-producing chain as the standard path, but
changes the approval pattern from per-skill stop points to exception-only
review plus one final delivery review.

Default rule: if a user asks for BRD delivery and does not explicitly ask for
approved baseline, audit-ready package, customer acceptance, spec writing, SDD
handoff, or trusted knowledge publication, route the request as
`daily_delivery`.

## Intent

Use `daily_delivery` when the team needs a useful BRD iteration for business
review, SOW discussion, scope alignment, or delivery planning without waiting
for every intermediate artifact to receive separate formal approval.

Do not use it as a shortcut to spec approval, SDD handoff, audit baseline, or
source-of-truth publication. Those still require the standard approved-baseline
path.

## Workflow Shape

```text
authorized scope / context / program-flow seed
  -> context and evidence packaging when useful
  -> inventory
  -> per-program analysis
  -> flow analysis
  -> module analysis
  -> BRD writer
  -> daily-delivery review pack
  -> accepted_for_daily_delivery or blocked
```

If the input is a program-flow seed such as `Program A -> Program B ->
Program C`, treat it as a scope seed, not as a proven flow. The pipeline should
automatically expand inventory, run program analysis for each named node, and
then run flow analysis. Missing source, ambiguous dynamic calls, unresolved
parameters, and unclear trigger context become `TBD-*` items or exception
stops.

## Approval Policy

Daily delivery uses `review_policy: exception_only`.

Hard stops remain:

- evidence authorization, sensitivity, or redaction is unresolved
- the requested scope is unknown or crosses unrelated modules
- a critical source artifact is missing and no owner accepts a draft-only
  limitation
- contradictory evidence affects money, inventory, compliance, customer status,
  posting, or other high-risk business outcomes
- the user asks to promote the result to spec, SDD handoff, formal baseline, or
  approved organizational knowledge

Everything else should flow forward as visible warnings, `TBD-*` items,
question-pack entries, or delivery-risk-summary rows.

## Output Semantics

Daily BRD packages use:

```yaml
mode: daily_delivery
status: delivery_draft
evidence_mode: daily_delivery
review_policy: exception_only
```

After the consolidated review, `review-decision.yaml` may record:

```yaml
daily_delivery:
  decision: accepted_for_daily_delivery
  not_allowed_for:
    - spec_approval
    - sdd_handoff
    - audit_baseline
```

`accepted_for_daily_delivery` means the BRD is acceptable for the current
delivery iteration. It is not the same as `approved`, and it does not pass the
BRD Discovery Gate for spec writing or SDD handoff.

## Review Pack

Instead of requiring separate human approval for every intermediate skill, the
SME review facilitator should create one consolidated pack:

```text
07_sme_reviews/<CAPABILITY-SLUG>/daily-delivery-review-v1/
  review-session.md
  question-pack.md
  sme-decision-log.yaml
  sme-signoff.md
  follow-up-findings.yaml
  delivery-risk-summary.md

05_brds/<CAPABILITY-SLUG>/
  review-decision.yaml
```

The pack should prioritize blocking `TBD-*`, contradictions, low-confidence
business rules, boundary uncertainty, high-risk validation scenarios, and
downstream blockers. It should not ask humans to rubber-stamp every generated
inventory, program, flow, module, or data-model artifact when there is no
exception.

## Promotion

To promote a daily-delivery BRD into the formal chain:

1. Resolve or waive daily `TBD-*` items that block approval.
2. Re-check Code-Backed Analysis Gate and BRD Discovery Gate.
3. Run the normal SME review/sign-off path.
4. Change BRD status only through the approved-baseline route.

Until that happens, downstream spec writing and SDD handoff must treat the
daily BRD as review material, not an approved baseline.
