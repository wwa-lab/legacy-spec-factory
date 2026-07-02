# Document vs Code Routing

## Document-First Is Usually Enough For

- function purpose and business scenario;
- channel inventory and user/staff touchpoints;
- UI, report, notification, statement, and communication descriptions;
- upstream/downstream application names at a high level;
- operational procedure and manual workarounds;
- known pain points, limitations, and project-derived feature requests;
- BRD, design note, or SME-note cross-reference.

## Code-Grounded Analysis Is Required For

- detailed validation logic, pass/fail branches, and exception routing;
- message type, transaction type, response code, or field-level key definition;
- exact formula, calculation order, rounding, rates, fees, thresholds, or
  source parameter names;
- GL/IE/posting logic, debit/credit signs, settlement, suspense, or
  reconciliation behavior;
- critical file data flow, persisted mutation, commit/rollback, or retry;
- program call sequence, dynamic calls, queue/file/API handoffs, and error
  propagation;
- security/authentication controls that affect transaction approval or customer
  status.

## Routing Pattern

Use document evidence to create the discovery package and explicit code-analysis
worklist. Route only the code-dependent subset to the IBM i analyzers.

```text
RAG/documents
  -> legacy-current-state-discovery
  -> gaps requiring code evidence
  -> legacy-ibmi-program-analyzer / legacy-ibmi-flow-analyzer
  -> updated catalogs and SME review
```

## Program Flow / Visio Inputs

Treat Visio, process diagrams, program-flow documents, and SME program lists as
navigation aids. They can identify likely entry points, key programs, message
types, and validation areas, but they do not prove behavior by themselves.

When a program flow is supplied:

1. Record it in the Document Master Index.
2. Extract the business event name and SME-provided program/order hints.
3. Create code-analysis work items for the named programs and validation
   areas.
4. Route to `legacy-ibmi-flow-analyzer` for multi-program flow review or to
   `legacy-ibmi-program-analyzer` for a single key program.

## Merge Rules

After code-grounded results return:

- If document and code agree, raise confidence where appropriate.
- If code adds undocumented behavior, mark it as `code_backed` and add it to
  SME review.
- If documents describe a behavior not seen in code, keep it as
  `source_documented` and request SME/code follow-up.
- If code contradicts a document, mark `contradictory`; do not overwrite either
  side silently.
