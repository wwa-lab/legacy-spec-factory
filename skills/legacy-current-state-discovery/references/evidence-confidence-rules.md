# Evidence and Confidence Rules

## Operating Rule

No evidence, no fact. If a detail is not available in reviewed evidence, write
`Not found in reviewed evidence` or create a gap. Do not replace missing
evidence with product knowledge, banking assumptions, naming conventions, or
common card-system behavior.

## Discovery Confidence Labels

Use these labels consistently:

| Label | Meaning | Typical evidence |
| --- | --- | --- |
| `Confirmed` | Directly supported by reviewed source evidence. | Source document section, RAG snippet with source metadata, code-backed artifact, runtime sample, SME sign-off. |
| `Strongly Indicated` | Supported by multiple consistent references, but not directly confirmed at the field/rule level. | Several documents or a document plus diagram point to the same behavior. |
| `Inferred` | Reasonable interpretation based on reviewed evidence, but the direct source is incomplete. | A process diagram implies a step, or a feature list names a behavior without details. |
| `Gap` | The item is expected or requested, but evidence is missing or contradictory. | Missing formula, missing status-code table, missing downstream system, unclear channel. |
| `Not Reviewed` | Source exists but has not been parsed, authorized, or inspected. | Unreadable file, unreviewed spreadsheet, skipped RAG result. |

These labels do not replace the repository evidence taxonomy. Where possible,
also carry `evidence_strength` values from `docs/evidence-and-knowledge-taxonomy.md`:
`confirmed_from_code`, `observed_in_runtime`, `confirmed_by_sme`,
`strongly_inferred`, `weakly_inferred`, `needs_sme_review`, `contradictory`, or
`missing`.

## Exact Detail Gate

The following must never be stated as exact unless the evidence directly
supports them:

- formula, calculation order, rounding, rate, fee, threshold, parameter value;
- GL account, IE item, debit/credit sign, posting rule, settlement account;
- status code, reason code, response code, message type, transaction type;
- program name, file/table name, report ID, screen ID, API name;
- authentication, authorization, regulatory, or security control.

If exact evidence is missing, write one of:

- `Exact value not found in reviewed evidence.`
- `Candidate pattern only; confirm against source table, parameter table, or code.`
- `Documented at high level only; code-grounded analysis required.`
- `Contradictory evidence; SME decision required.`

## Fact vs Inference

Keep these separate:

- `observed_behavior`: what the legacy system is evidenced to do.
- `inferred_business_rule`: a possible rule or intent that needs SME review.
- `project_derived_feature`: a requested or designed change, not current-state
  behavior unless separately evidenced.
- `unknown_tbd`: missing, weak, or contradictory information.

## Conflict Handling

When sources disagree:

1. Preserve each source claim with its source ID.
2. Mark the item `contradictory`.
3. Create a gap or SME question.
4. Do not choose a winner unless authoritative code/runtime evidence or SME
   approval resolves it.

When documents and code disagree, code is ground truth for observed behavior;
SME review resolves business intent and whether code behavior is desired,
obsolete, or exceptional.
