# AI-Assisted Legacy BRD Discovery from IBM i / AS400 Source

## Slide 1 - Executive Message

**AI-assisted, evidence-backed BRD discovery for legacy modernization**

We are not using AI to produce a one-click final BRD.

We are using AI to turn IBM i / AS400 legacy evidence, historical documents, RAG/code graph output, and SME fragments into a reviewable BRD draft that SMEs and Business stakeholders can validate, correct, and approve.

**Core message:** AI accelerates discovery and structures legacy knowledge. Human experts remain the authority.

---

## Slide 2 - The Current Discovery Pain

Legacy modernization discovery is slow because critical business knowledge is spread across:

- RPGLE, CLLE, COBOL, SQL, DDS, DB2 for i metadata
- program call relationships, batch jobs, schedulers, job logs, spool files
- screens, reports, control tables, exception handling, operational workarounds
- historical specs, data dictionaries, RAG/code graph output, and SME memory

Manual BRD creation often becomes a long reverse-engineering exercise with weak traceability and uneven coverage.

**Business impact:** discovery takes too long, rules are hard to confirm, gaps surface late, and downstream modernization teams inherit uncertainty.

---

## Slide 3 - What We Are Proposing

An AI-assisted BRD draft generation method that is:

- **Evidence-backed:** key claims link to source evidence or SME confirmation
- **Reviewable:** uncertain items become explicit open questions
- **Traceable:** rules, behaviors, scenarios, and gaps carry stable IDs
- **Source-gated:** generated or candidate context becomes TBDs/questions, not BRD facts
- **Governed:** each stage has input, output, and validation gates
- **Human-approved:** final BRD approval remains with SME and Business owners

The output is a **legacy-system BRD Package**, not a target-system design and not a Java/cloud implementation plan.

---

## Slide 4 - Method at a Glance

The Legacy Spec Factory approach is module-first, program-grounded, and capability-output.

```text
Legacy evidence + historical docs + RAG/code graph + SME fragments
  -> four-view coverage, gaps, and SME questions
  -> observed behavior
  -> inferred business rule seeds
  -> validation scenario seeds
  -> BRD section + traceability
  -> SME / Business review
  -> approved legacy BRD baseline
```

The workflow avoids sending an entire system or 30,000-line program into one large prompt. It uses specialized skills and structured artifacts at each step.

---

## Slide 5 - How the Repo Supports This

The repo already contains a skill-based pipeline for legacy understanding:

- `legacy-ibmi-evidence-intake`: registers source, DDS, logs, spool, reports, sample transactions
- `legacy-document-evidence-intake`: converts Office, Visio, PDF, and image evidence into source-coordinate packages
- `legacy-flow-context-normalizer`: organizes scattered docs/RAG/SME notes into four-view coverage, gaps, and SME questions; it is not a flow generator
- `legacy-module-context-intake`: packages reviewed context and classifies every carried claim for BRD source eligibility
- `legacy-ibmi-inventory`: identifies programs, files, screens, reports, and object relationships
- `legacy-ibmi-program-analyzer`: extracts program behavior, calls, I/O, errors, and coverage
- `legacy-ibmi-flow-analyzer`: connects programs into business transaction flows
- `legacy-ibmi-module-analyzer`: assembles four-view module coverage plus a BRD Source Eligibility Crosswalk
- `legacy-brd-writer`: drafts the capability-level legacy BRD Package
- `legacy-sme-review-facilitator`: records SME review decisions and sign-off
- `legacy-step-validator` and `legacy-traceability-packager`: enforce validation and traceability

This is a pipeline, not one master prompt.

---

## Slide 6 - BRD Package Output

The near-term output is a reviewable BRD Package:

```text
05_brds/<CAPABILITY-SLUG>/
  brd.md
  brd-review.md
  validation-scenarios.md
  traceability.md
  review-decision.yaml
```

The BRD covers the current legacy system only:

- function purpose and business scenarios
- channels, touchpoints, system interfaces
- process flow, validation rules, error handling, dependencies
- observed behaviors, inferred rule seeds, open questions, and evidence links

It does not include old-vs-new gap classification, target architecture, acceptance criteria, or formal test cases.

---

## Slide 7 - SME Review Experience

SMEs do not review a black-box AI answer.

They review focused questions with evidence:

- What behavior did the legacy system demonstrate?
- Which source, job log, spool file, screen, or SME note supports it?
- Is this claim code-backed, SME-confirmed, source-documented, candidate-only, generated-draft, or missing?
- Is the inferred rule really business policy, or only a technical workaround?
- Is the open question blocking or non-blocking?
- Should the rule be confirmed, rejected, deferred, or routed for more evidence?

The repo's SME review workflow batches 3-7 questions at a time and writes decisions back into review artifacts.

---

## Slide 8 - Business Review Experience

Business stakeholders receive a business-readable current-state BRD draft:

- process narrative in business language, not program-by-program walkthroughs
- visible confidence and review status
- open questions instead of hidden assumptions
- validation scenario seeds for happy path, exception path, and boundary review
- clear separation between "what the old system does" and "what should happen in the future"

The method helps Business confirm current behavior, identify missing rules, and prepare for later old-vs-new comparison.

---

## Slide 9 - Risk Control: Hallucination and Context Drift

Risk controls already designed in the repo:

- source reference binding through `EV-*`, `BEH-*`, `BR-*`, `TBD-*`, `VAL-*`
- evidence strength labels such as `confirmed_from_code`, `observed_in_runtime`, `confirmed_by_sme`, `needs_sme_review`, `contradictory`, and `missing`
- BRD source eligibility labels that keep `candidate_only`, `generated_draft`, and `questions_only` out of factual BRD prose
- explicit knowledge types: observed behavior, inferred business rule, modernization decision, unknown/TBD
- Step Contract with input, execution, output, and validation rules
- mechanical validation, AI semantic review, and SME/human approval gates
- anti-hallucination rules requiring unsupported claims to become open questions

**Principle:** if code, SME approval, or explicitly approved source evidence cannot confirm it, the BRD must not state it as fact.

---

## Slide 10 - Risk Control: Very Large Programs

For 20,000-30,000+ line RPG programs, the repo defines large-program mode:

- do not split source into fixed chunks and summarize each chunk independently
- first build a source index, routine cards, program call map, logic decomposition ledger, data touch map, and coverage ledger
- deep-read high-risk windows: state changers, external calls, money/customer/status fields, error handling, commits/rollbacks
- mark uncovered or unresolved areas as `indexed_only`, `deep_read`, or `blocked`

This keeps the analysis tied to call topology, data movement, and coverage instead of plausible free-form summaries.

---

## Slide 11 - Risk Control: Repeatability and Governance

Existing repo controls:

- canonical skill source under `skills/`
- versioned skill scorecards and runtime matrix
- workflow-state contract for cross-session stage tracking
- stable IDs across evidence, objects, behaviors, rules, questions, scenarios, specs, and handoff packages
- idempotency guidance in the Step Contract
- synthetic fixtures for repeatable internal pilot testing

Proposed enhancements:

- standardized run metadata for every execution
- input hash and evidence bundle version
- skill version and model version recorded in each output package
- output diff comparison across reruns
- reproducibility dashboard for pilots and production runs

---

## Slide 12 - Why This Is Valuable

For SMEs:

- less time starting from raw source
- more time validating evidence-backed findings
- clearer view of ambiguity, contradictions, and missing evidence

For Business:

- faster current-state understanding
- clearer business process and rule confirmation
- visible open questions and exception scenarios

For Management / Delivery Leads:

- reduced discovery cost and cycle time
- scalable, repeatable workflow across more legacy programs
- stronger governance before downstream spec generation and Java/cloud modernization

---

## Slide 13 - Current Boundaries

This method does not:

- guarantee AI accuracy without review
- replace IBM i SMEs or Business owners
- produce a one-click final BRD
- decide whether every legacy behavior should be preserved
- perform old-vs-new gap classification inside the BRD
- generate target Java/cloud implementation directly from raw code
- require SMEs to provide four complete flows before discovery can start
- turn AI-organized coverage or RAG candidates into BRD facts

The approved BRD is a human-reviewed legacy baseline. Later spec generation, gap analysis, golden-master tests, and SDD handoff require separate gates.

---

## Slide 14 - Recommended Next Steps

1. Select one representative business capability with manageable scope.
2. Prepare authorized, redacted evidence: source, DDS, DB2 metadata, call relationships, logs, spool, screens/reports, historical docs, RAG/code graph output, and SME fragments.
3. Run the skill-based pipeline on synthetic and pilot evidence, starting with coverage/question normalization when reviewed context is incomplete.
4. Conduct SME review using evidence-linked question batches.
5. Capture Business confirmation and open questions.
6. Measure cycle time, coverage, unresolved gaps, and rerun consistency.
7. Add proposed governance enhancements for run metadata, hashes, model versions, and output diffs.

**Decision ask:** approve a controlled pilot to validate speed, traceability, and review quality before scaling.
