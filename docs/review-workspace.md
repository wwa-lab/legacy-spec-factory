# Review Workspace

The review workspace is the **human-review surface** for Legacy Spec Factory.
It is not another artifact in the reverse chain. It is a derived read model
built from the chain's existing artifacts so reviewers can make decisions
without reading every source document linearly.

## Purpose

The reverse chain already produces rich artifacts:

- `program-analysis.md`
- `flow-*.md`
- `module-overview.md`
- `spec.yaml` / `spec.md`
- `traceability.md`
- golden-master quality packages

Those files are good source material, but they are not optimized for the
reviewer's core loop:

1. What is blocked right now?
2. Which conclusions still need SME judgment?
3. Which findings have contradictory evidence?
4. Which conclusions are stable enough to approve?

The review workspace answers those questions directly.

## Derived Output

Per project:

```text
docs/<project>/
  08_review_workspace/
    review-items.json
    index.html
    review-items.manual.yaml   # optional manual overrides / additions
```

`review-items.json` is the canonical machine-readable output.
`index.html` is the human-facing review workspace.

## Review Item Model

Every reviewable conclusion is normalized into one `Review Item`.

Required fields:

```json
{
  "id": "RI-CAPABILITY-001",
  "question": "Business-facing review question",
  "status": "blocked | contradicted | needs_sme_review | needs_review | ready_to_approve | approved | deferred",
  "priority": "high | medium | low",
  "confidence": "low | medium | high | confirmed",
  "decision_basis": "source_only | runtime_only | source_plus_runtime | source_plus_sme | source_runtime_sme",
  "business_signal": "Business-facing meaning reviewers should judge first",
  "evidence_basis": "Why the current conclusion is supported or still weak",
  "sme_questions": ["Concrete questions for SME / business review"],
  "current_conclusion": "Current best conclusion",
  "evidence": [],
  "gaps": [],
  "contradictions": [],
  "impacts": [],
  "review_action": "mark_blocked | route_to_sme | request_more_evidence | approve | defer | reopen",
  "source_artifacts": []
}
```

The workspace is deliberately question-first and business-signal-first. It
should not read like a file tree or object inventory. `business_signal`,
`evidence_basis`, and `sme_questions` are the primary human review surface;
technical source paths and previews support those fields.

## First-Pass Extraction Sources

The initial builder favors **clear, auditable sources** over aggressive NLP:

| Source | Extraction focus |
| --- | --- |
| `spec.yaml` | approved rules, error conditions, missing ACs, open TBDs |
| `traceability.md` | rule → evidence → verification closure, coverage gaps |
| `program-analysis.md` | unresolved open questions, error behaviors |
| `flow-*.md` | unresolved flow open questions |
| evidence manifest | evidence type, approval, artifact paths |

This is intentional. Without enough real project examples, the best first step
is a **half-automatic review surface**, not a brittle full-auto semantic
classifier.

## Optional Manual Augmentation

`review-items.manual.yaml` can add or override items when the generator cannot
yet infer a business question correctly.

Suggested shape:

```yaml
overrides:
  - id: RI-CAP-001
    question: "Sharper reviewer-facing wording"
    status: needs_sme_review

items:
  - id: RI-CAP-MANUAL-001
    capability_id: CAP-EXAMPLE
    type: meaning_review
    theme: "Manual business question"
    question: "Does approval count as opening the account?"
    status: contradicted
    priority: high
    confidence: medium
    decision_basis: source_plus_sme
    business_signal: "Opening an account may mean application approval in code, but activation in SME language."
    evidence_basis: "Source and SME note disagree; both must stay visible until resolved."
    sme_questions:
      - "When does the business consider the account open?"
      - "Should the modern workflow preserve approval and activation as separate states?"
    current_conclusion: "Code and SME language disagree."
    evidence: []
    contradictions:
      - "Code writes status early; SME says activation is the true opening event."
    gaps: []
    impacts: [BR-EXAMPLE-001]
    review_action: route_to_sme
    source_artifacts:
      - 05_specs/EXAMPLE/spec.yaml
```

## Tooling

Generate the workspace:

```bash
python3 scripts/build-review-workspace.py docs/EXAMPLE-tutorial/
```

Validate the generated output:

```bash
python3 scripts/check-review-workspace.py docs/EXAMPLE-tutorial/
```

The validator checks both `review-items.json` and `index.html`: required review
fields, evidence references, impacted IDs, embedded HTML payload consistency,
and the presence of the business-signal review sections.

Open the static HTML review surface directly:

```text
docs/EXAMPLE-tutorial/08_review_workspace/index.html
```

No dev server is required; the generated page is self-contained.

## Design Rules

- The workspace **must not invent facts**. If evidence is weak or absent, the
  item becomes `needs_review`, `needs_sme_review`, or `blocked`.
- The workspace **must cite source artifacts** and evidence IDs.
- The workspace **must privilege review order over source order**. Blockers and
  contradictions appear before already-approved material.
- The workspace **must stay downstream of the reverse chain**. Fix factual
  mistakes in source artifacts, then rebuild the workspace.
