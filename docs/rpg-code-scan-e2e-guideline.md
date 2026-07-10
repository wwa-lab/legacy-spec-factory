# RPG Code Scan E2E Guideline

This guide is the month-end adoption path for Legacy Spec Factory's current
focus: scanning RPG / RPGLE / SQLRPGLE code, classifying each program by size
and density, producing reviewable program analysis artifacts, and moving the
approved result into the central delivery documents repo.

中文摘要: 这份文档给内部工程师、BA、SME、以及其它部门想开始试用的 SME 使用。
目标不是一次性讲完整个 Legacy Spec Factory，而是先把当前最重要的一条简单链路
跑通: source repo code scan -> program tier -> scenario prompt ->
artifact validation -> sync to `legacy-modernization-delivery` -> PR review
and merge.

## Audience

Use this guide for:

- internal engineers starting a new RPG code scan
- IBM i / RPG SMEs reviewing one program or one module slice
- analysts who need a repeatable prompt and artifact checklist
- other departments that want to try the workflow without first learning every
  skill in the factory

Do not use this guide as a replacement for formal BRD / spec approval. Program
analysis output is evidence for downstream work; it is not an approved
modernization requirement by itself.

## 1. Overall Design理念

The current closeout message for this project should stay simple:

Legacy Spec Factory is not a direct RPG-to-Java translator. It is an
evidence-backed understanding pipeline.

The design rules are:

1. **Code proves behavior.**
   Deployed RPG / CL / DDS / SQL source is the strongest evidence for what the
   legacy system does.
2. **SME proves intent.**
   SME review decides whether an observed behavior is a real business rule, a
   workaround, a bug, or a modernization decision.
3. **RAG and AI provide context, not final truth.**
   Retrieval output helps find evidence, but it cannot promote a claim by
   itself.
4. **Unknowns stay visible.**
   Missing copybooks, unresolved message descriptions, unknown external
   program behavior, and unsupported business meaning must become `TBD-*` or
   blockers.
5. **Artifacts must be reviewable and portable.**
   `program-analysis.md` is the SME review wrapper. Compact YAML sidecars are
   for downstream flow/module/spec consumers. Runtime-specific folders are
   adapters; canonical skills live under `skills/`.
6. **Draft output is not organizational knowledge.**
   Only SME-reviewed output merged into the central delivery repo `main` branch
   becomes the accepted analysis fact layer.
7. **Central artifacts are reused before scanning.**
   Do not rerun program analysis when the central delivery repo remote `main`
   already contains an exact folder for the requested program. The source of
   truth is `legacy-modernization-delivery` GitHub remote `main`, not a random
   local checkout. Search remote-current central artifacts first, then scan only
   programs with `central_lookup_result: not_found_on_remote_main`.

## 2. Current Focus: RPG Code Scan

For the project closeout phase, the practical focus is RPG code scan:

```text
central delivery repo lookup
  -> reuse remote-main program-analysis artifacts when exact folder exists
  -> source scan only when central_lookup_result is not_found_on_remote_main
  -> source repository
  -> source inventory cache freshness check
  -> repo scan only when cache is missing or stale
  -> program tier
  -> tier-specific prompt
  -> program-analysis artifacts
  -> artifact validation
  -> central delivery repo PR
  -> SME review
  -> merge to main
```

The scan must handle different program sizes and shapes:

| Tier | When to use | Default behavior |
| --- | --- | --- |
| `normal_program` | Under 10,000 lines with no density trigger. | Keep the output lightweight and SME-first. |
| `complex_normal_program` | Under 10,000 lines but dense in routines, SQL, file I/O, messages, mutations, external calls, or multiple deep-read windows. | Generate only sidecars justified by evidence. |
| `large_extreme_program` | Over 10,000 lines, more than 25 routines, more than 20 external calls, more than 25 object dependencies, or unsafe to fit in context. | Build deterministic indexes, retain batch checkpoints, and deep-read at most five routines/windows per batch. |

For programs above 10,000 lines, do not ask the LLM to summarize the whole
source. The safe flow is:

1. Build a deterministic source index.
2. Identify routines, calls, file I/O, SQL, messages, mutations, and external
   boundaries.
3. Create a deep-read plan.
4. Process at most five routines/windows per batch.
5. Retain `routine-logic-details/deep-read-batch-*.md` checkpoints.
6. Consolidate into final `routine-logic-details.md`.
7. Keep `program-analysis.md` compact and SME-readable.

Reference docs:

- [`repo-scan-mode-guideline.md`](repo-scan-mode-guideline.md)
- [`large-rpg-analysis-strategy.md`](large-rpg-analysis-strategy.md)
- [`sme-ibmi-program-flow-module-guideline.md`](sme-ibmi-program-flow-module-guideline.md)
- [`sme-ibmi-program-analyzer-normal-guideline.md`](sme-ibmi-program-analyzer-normal-guideline.md)
- [`sme-ibmi-program-analyzer-complex-guideline.md`](sme-ibmi-program-analyzer-complex-guideline.md)
- [`sme-ibmi-program-analyzer-large-guideline.md`](sme-ibmi-program-analyzer-large-guideline.md)
- [`sme-ibmi-analysis-prompts.md`](sme-ibmi-analysis-prompts.md)

## 3. E2E Guideline For SME / Other Users

The recommended onboarding path for another SME or department is one program
first, not a whole system.

### What The User Needs To Provide

- source repo or source export location
- target program or rough module/capability scope
- any known entry point, menu option, batch job, or transaction path
- copybooks/includes if they are outside the scanned root
- message file/catalog/reference pack when message IDs appear
- SME business question, such as "What does this program validate before
  posting?" or "Which files does this program update?"
- confirmation that material is redacted or approved for agent review

### What The Assistant / Engineer Provides

- central delivery repo lookup result
- repo scan outputs only for programs not found on remote `main`
- tier classification
- the right prompt card
- program analysis artifacts
- validation findings
- central delivery repo PR
- SME review checklist

### What The SME Reviews

The SME should focus on:

- whether the program scope is correct
- whether calculation logic matches the business understanding
- whether validation/reject paths are complete
- whether exception and message behavior is realistic
- whether file I/O / SQL state changes are correct
- which claims are real business rules, workarounds, bugs, or TBDs

The SME does not need to review raw generated files one by one at first. Start
with `program-analysis.md`, then inspect `routine-logic-details.md` only where
the main analysis links to `RLOG-*` details.

## 4. Simple RPG Code Scan Flow

### 4.1 Check Central Delivery Repo Before Scanning

Before running a source repo scan, check the central delivery documents repo
remote `main` for an exact program folder for the requested program or program
flow. For the current lending-card setup, the default delivery repo is
`CH-WPS-LENDING-CARDS/legacy-modernization-delivery`, and the latest accepted
state is the GitHub remote `main` branch.

If you have a local checkout of `legacy-modernization-delivery`, treat it as a
cache only. Fetch and verify it against `origin/main` before lookup. Do not
use a stale local checkout, feature branch, or private working copy to conclude
that an artifact does not exist. Use Git method 2 for remote lookup:
`git ls-remote` plus a temporary shallow clone / sparse checkout, or an
already-fresh verified cache. Do not use GitHub API tooling.

Read-only Git lookup:

```bash
git ls-remote <delivery-repo-url> main
git clone --depth 1 --branch main --filter=blob:none \
  --sparse <delivery-repo-url> <tmp-delivery-dir>
git -C <tmp-delivery-dir> sparse-checkout set "modules"
```

Then inspect the configured `program_folder_patterns`. Delete the temporary
checkout after lookup if it is not a managed cache.

#### Delivery Artifact Lookup Profile

Use a configurable lookup profile instead of hardcoding one repo name or one
folder depth.

Default profile for the current lending-card setup. Teams should start from
`skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml` and edit the
repo/folder/branch values once instead of asking SMEs to configure them each
run:

```yaml
delivery_artifact_lookup_profile:
  repo: CH-WPS-LENDING-CARDS/legacy-modernization-delivery
  branch: main
  module_roots:
    - modules/*
  program_folder_patterns:
    - modules/*/{PROGRAM}
  artifact_file_patterns:
    - program-analysis.md
    - program-analysis-*.md
    - program-analysis-summary.yaml
  program_name_normalization:
    case: upper
    preserve_prefixes: ["@"]
    exact_folder_name_match: true
```

This matches folders like `modules/CAP-ID-0001-large_extreme_program/@CU118`
and `modules/CAP-ID-0001-large_extreme_program/CC050` by exact program
identity. `@CU118` and `CU118` are different programs: scanning `CU118` must
not reuse `@CU118`, and scanning `@CU118` must not reuse `CU118`, unless a
department-specific profile explicitly defines aliases.

Other departments can override `repo`, `branch`, `module_roots`,
`program_folder_patterns`, artifact filenames, and normalization rules. For
example, another team could use `delivery-docs`, `capabilities/*/{PROGRAM}`, or
`apps/*/programs/{PROGRAM}` without changing the skill logic.

For new scan output, keep lookup and write paths separate:

```yaml
delivery_workspace_profile:
  branch_mode: use_or_create_provided
  working_branch_pattern: develop-{PERSON}
  allowed_branch_patterns:
    - develop-*
  create_from: origin/main
  write_to_main: false
  program_set_review_parent: modules/CAP-ID-0004-program_set_reviews
```

At runtime the SME or engineer provides `Delivery working branch:
develop-<person>`, such as `develop-leo`. If the branch does not exist, create
it from `origin/main`; if it exists, update it before writing. Reuse lookup
still reads remote `main` only.

Use these lookup keys when available:

- `OBJ-*`
- program/member name
- module or `CAP-*`
- source library/member
- source ref, source collection date, or source fingerprint recorded in
  `program-analysis-summary.yaml` or module metadata

Do not rerun program analysis when an exact program folder exists on remote
`main`. Remote `main` is already PR-reviewed, so this is a lookup routing
result, not a second approval gate.

Lookup result values:

| central_lookup_result | Use when | Next action |
| --- | --- | --- |
| `found_on_remote_main` | Exact program folder exists on delivery repo remote `main`. | Tell the user this program has already been scanned and provide the central path. Do not scan source. |
| `not_found_on_remote_main` | No exact program folder exists on remote `main`. | Run source scan for that program. |
| `remote_unavailable` | Remote `main` could not be checked. | Ask for access/context; do not assume missing. |

For SME-provided program flows, build one row per program with its
`central_lookup_result` before scanning anything. The expected outcome is that
programs found on central repo remote `main` are reused, and only true
`not_found_on_remote_main` gaps are scanned.

For direct single-program analyzer runs, pass the same remote-main snapshot to
the program analyzer helper. This makes the single-program path self-gating,
not dependent on the flow builder:

Windows:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-program-analyzer\scripts\invoke-windows-tool.ps1 IndexRpgSource <source-file> `
  --program <PROGRAM> `
  --out-dir <analysis-dir> `
  --delivery-root <tmp-delivery-dir-or-fresh-cache> `
  --delivery-profile <delivery-profile.yaml>
```

macOS/Linux:

```bash
python3 scripts/index-rpg-source.py <source-file> \
  --program <PROGRAM> \
  --out-dir <analysis-dir> \
  --delivery-root <tmp-delivery-dir-or-fresh-cache> \
  --delivery-profile <delivery-profile.yaml>
```

If the helper prints `central_lookup_result: found_on_remote_main`, stop and
reuse the reported `artifact_root`. It will not write new
`source-index.yaml` or `program-analysis.md` files. If it prints
`central_lookup_result: not_found_on_remote_main`, continue the normal source
analysis path.

If the SME is not satisfied with the approved artifact on remote `main`, or a
large source/business change makes a refresh necessary, make that an explicit
override instead of silently rescanning:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-program-analyzer\scripts\invoke-windows-tool.ps1 IndexRpgSource <source-file> `
  --program <PROGRAM> `
  --out-dir <analysis-dir> `
  --delivery-root <tmp-delivery-dir-or-fresh-cache> `
  --delivery-profile <delivery-profile.yaml> `
  --force-rescan `
  --rescan-reason "SME requested refresh after major source or rule change"
```

Forced rescans still print the central lookup result. The generated
`source-index.yaml` and `program-analysis-summary.yaml` include
`central_artifact_reuse` metadata with the prior central artifact path and the
rescan reason.

Use the deterministic program-set builder after the remote-main snapshot is
prepared:

Windows:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-flow-analyzer\scripts\invoke-windows-tool.ps1 BuildProgramSetCoreReview `
  --review-name "<review name>" `
  --programs-file <programs.txt> `
  --delivery-root <tmp-delivery-dir-or-fresh-cache> `
  --working-root <delivery-working-branch-checkout> `
  --source-root <source-repo> `
  --profile <delivery-profile.yaml> `
  --working-branch develop-<person> `
  --output-dir <delivery-worktree>\modules\CAP-ID-0004-program_set_reviews\{review_slug}
```

macOS/Linux:

```bash
python3 scripts/build-program-set-core-review.py \
  --review-name "<review name>" \
  --programs-file <programs.txt> \
  --delivery-root <tmp-delivery-dir-or-fresh-cache> \
  --working-root <delivery-working-branch-checkout> \
  --source-root <source-repo> \
  --profile <delivery-profile.yaml> \
  --working-branch develop-<person> \
  --output-dir <delivery-worktree>/modules/CAP-ID-0004-program_set_reviews/{review_slug}
```

This writes `program-set-core-input-manifest.yaml` and
`program-set-sme-core-review.md`. Fill only Calculation Logic, Validation
Logic, Exception Handling, and Message Inventory from manifest-listed compact
artifacts. Omit `--working-root` only for the first preflight before missing
programs are scanned; include it for the final build so newly scanned working
branch artifacts can join remote-main reused artifacts. Then validate before
SME handoff:

Windows:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-flow-analyzer\scripts\invoke-windows-tool.ps1 ValidateProgramSetCoreReview `
  --manifest <output-dir>\program-set-core-input-manifest.yaml `
  --review <output-dir>\program-set-sme-core-review.md
```

macOS/Linux:

```bash
python3 scripts/validate-program-set-core-review.py \
  --manifest <output-dir>/program-set-core-input-manifest.yaml \
  --review <output-dir>/program-set-sme-core-review.md
```

### 4.2 Use Skill To Scan Code In Source Repo

Before running repo scan, check the default source inventory cache:

```text
<source-repo>/outputs/repo-scan/program-list.csv
<source-repo>/outputs/repo-scan/scan-summary.yaml
```

If both files exist and `scan-summary.yaml.source_revision_key` matches the
current clean Git source HEAD, reuse `program-list.csv` to locate the missing
program's source path and `size_tier`. If either file is missing, the revision
is stale, or source code has uncommitted changes, rerun repo scan from the
legacy source repo or source export root.

macOS / Linux:

```bash
python3 skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py . \
  --out-dir outputs/repo-scan
```

Windows:

```powershell
py -3 skills\legacy-ibmi-inventory\scripts\scan_ibmi_repo.py . `
  --out-dir outputs\repo-scan
```

Expected output:

```text
outputs/repo-scan/program-list.csv
outputs/repo-scan/large-program-candidates.md
outputs/repo-scan/scan-summary.yaml
```

Review `program-list.csv` first. It tells you which members were detected,
their `source_kind`, line counts, `size_tier`, `tier_reason`,
`default_output_profile`, and whether classification came from
`legacy-ibmi-program-analyzer` or a fallback scanner rule.

`scan-summary.yaml` records `source_revision` and `source_revision_key`.
Downstream flow/program routing should treat `program-list.csv` as reusable
only when that key still matches the current clean source revision.

### 4.3 Identify Source Tier And Use Different Prompt

Use the `size_tier` column in `program-list.csv`.

| `size_tier` | Prompt / guideline |
| --- | --- |
| `normal_program` | Use [`sme-ibmi-program-analyzer-normal-guideline.md`](sme-ibmi-program-analyzer-normal-guideline.md). |
| `complex_normal_program` | Use [`sme-ibmi-program-analyzer-complex-guideline.md`](sme-ibmi-program-analyzer-complex-guideline.md). |
| `large_extreme_program` | Use [`sme-ibmi-program-analyzer-large-guideline.md`](sme-ibmi-program-analyzer-large-guideline.md). |
| `non_program_source` | Route DDS/screen/report objects to data-model or screen/report analysis when needed. |

Copy-ready starter prompt:

```text
Use legacy-ibmi-program-analyzer.

Analyze one IBM i RPG program for SME review.

Program: <PROGRAM_NAME>
Source path: <source file path>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <program analysis output directory>

Rules:
- Build deterministic indexes first.
- Classify the program tier before writing the final narrative.
- Do not deep-read more than 5 routine bodies in one turn.
- Do not paste long source excerpts into the output.
- Mark missing message descriptions, copybooks, external program semantics, or
  SME-only meanings as TBD.

Required output:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
```

For `large_extreme_program`, add:

```text
Large-program rules:
- Do not read the whole source into context.
- Create deep-read-plan.md and all-routine-coverage-ledger.md.
- Create retained checkpoints under routine-logic-details/deep-read-batch-*.md.
- Each batch may process at most 5 routines/windows.
- Keep program-analysis.md compact and SME-first.
- Do not mark chain_ready until approved inventory/evidence linkage exists.
```

### 4.4 Validate Key Files

The two key human-review files are:

```text
program-analysis.md
routine-logic-details.md
```

The key machine-readable support files are:

```text
program-analysis-summary.yaml
source-index.yaml
routine-logic-details.yaml
message-inventory.yaml
```

When local scripts are available, validate the program analysis contract.

macOS / Linux:

```bash
python3 scripts/validate-program-analysis-contract.py \
  --analysis-dir <program-analysis-output-dir>
```

Windows:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-program-analyzer\scripts\invoke-windows-tool.ps1 ValidateProgramAnalysis `
  --analysis-dir <program-analysis-output-dir>
```

Manual validation checklist:

- `program-analysis.md` has SME-first sections for calculation logic,
  validation logic, exception handling, message inventory, file I/O / SQL, and
  open TBDs.
- `program-analysis.md` stays compact. It should not become a pasted source
  dump.
- `routine-logic-details.md` includes `RLOG-*` IDs and agrees with
  `routine-logic-details.yaml`.
- Claims based only on `indexed_only` routines are not promoted to confirmed
  behavior.
- Any `deep_read` claim links to source ranges, routine IDs, evidence IDs, or
  SME-approved notes.
- Observed message/status/code values are not ID-only. If descriptions are
  missing, mark them unresolved and block final-ready status.
- For large programs, `routine-logic-details/deep-read-batch-*.md` checkpoint
  files exist, and each batch covers no more than five routines/windows.
- `program-analysis-summary.yaml` lists sidecars and statuses accurately.

If validation fails, fix the analysis artifacts before syncing to the central
delivery repo.

### 4.5 Sync Result To Central Documents Repo

The central delivery documents repo is `legacy-modernization-delivery`. It is
the project-specific delivery repo. It stores reviewed module delivery
documents, evidence ledgers, source-generated outputs, approval records, and
handoff packages.

Default rule:

```text
Copy the source repo generated output folder unchanged into:

legacy-modernization-delivery/modules/<CAP-ID>/output/source-output/
```

Do not copy raw production evidence, unredacted source, secrets, or private
runtime data into tracked paths.

Example local workflow from this repo's sibling checkout:

```bash
cd ../legacy-modernization-delivery

git switch -c analysis/<CAP-ID>-rpg-code-scan

mkdir -p modules/<CAP-ID>/output/source-output
cp -R /path/to/source-repo/<program-analysis-output-dir>/ \
  modules/<CAP-ID>/output/source-output/
```

If this is the first time the module is being registered, initialize the module
folder using the delivery repo templates:

```bash
mkdir -p modules/<CAP-ID>/input modules/<CAP-ID>/evidence
cp templates/module.yaml modules/<CAP-ID>/module.yaml
cp templates/sme-input-index.md modules/<CAP-ID>/input/sme-input-index.md
cp templates/evidence-ledger.yaml modules/<CAP-ID>/evidence/evidence-ledger.yaml
```

Update `modules/<CAP-ID>/module.yaml` at minimum:

```yaml
module_id: "<CAP-ID>"
capability_slug: "<CAPABILITY-SLUG>"
title: "<business-readable title>"
status: "needs_sme_review"
owner: "<delivery owner>"
sme_contacts:
  - "<SME name or role>"
output_location: "modules/<CAP-ID>/output/source-output/"
```

If the output contains unresolved findings, keep status as `needs_sme_review`
or `draft`. Do not mark `approved` before SME review.

### 4.6 Create PR And Merge To Main Branch

Open a PR in `legacy-modernization-delivery` after the output is copied and the
module metadata is updated.

PR title:

```text
analysis: add RPG code scan for <CAP-ID> / <PROGRAM>
```

PR body checklist:

```markdown
## Scope

- CAP-ID:
- Program(s):
- Source repo / source ref:
- Output folder:

## Tier Result

- normal_program:
- complex_normal_program:
- large_extreme_program:
- Key blockers / TBDs:

## SME Review Focus

- Calculation logic:
- Validation logic:
- Exception handling:
- Message inventory:
- File I/O / SQL state changes:

## Validation

- [ ] `program-analysis.md` present
- [ ] `routine-logic-details.md` present
- [ ] `program-analysis-summary.yaml` present
- [ ] `routine-logic-details.yaml` present
- [ ] `message-inventory.yaml` present
- [ ] Contract validation run or manual validation completed
- [ ] No raw / unredacted production evidence committed

## Decision Needed

- [ ] SME approve
- [ ] SME request changes
- [ ] SME mark TBD / non-blocking
- [ ] Delivery lead merge after approval
```

The PR is the control surface for SME comments, requested changes, approval,
and merge. After merge to `main`, the central delivery repo `main` branch is
the accepted analysis snapshot.

## 5. Internal Adoption Guidance

For internal teams, encourage small usage first:

1. Pick one representative program.
2. Check `legacy-modernization-delivery` remote `main` for an exact program
   folder.
3. Reuse the central artifact when found. For
   `central_lookup_result: not_found_on_remote_main`, check
   `outputs/repo-scan` cache before rerunning repo scan.
4. Rerun repo scan only when the cache is missing, stale, or dirty.
5. Use the tier-specific prompt.
6. Validate `program-analysis.md` and `routine-logic-details.md`.
7. Sync new or refreshed artifacts to `legacy-modernization-delivery`.
8. Open a PR and invite one RPG / IBM i SME.
9. Merge only after SME review.

Recommended first pilot size:

- one module or capability
- one to three representative programs
- at least one `normal_program`
- at most one `large_extreme_program` unless the SME has enough time

Do not start by scanning the whole source repo into a formal delivery package.
Whole-repo scan is useful for triage, but program analysis should be reviewed
incrementally.

## 6. Guidance For Other Department SMEs

When sharing with another department, keep the message practical:

- They do not need to learn all Legacy Spec Factory skills first.
- They can start with one RPG program and one SME question.
- They should provide redacted or approved source access.
- The assistant/engineer can run the scan and prepare the PR.
- The SME's job is to review behavior, meaning, and open questions.
- Their approval happens in the central delivery repo PR, not in a private chat
  alone.

Suggested short introduction:

```text
We are using Legacy Spec Factory to scan IBM i RPG programs and produce
evidence-backed review artifacts. The output is not treated as approved
knowledge until an IBM i / business SME reviews it in the delivery repo PR.

For the first run, please pick one program and one business question. We will
scan the source, classify the program as normal / complex / large, produce
program-analysis.md and routine-logic-details.md, and ask you to confirm or
correct the key calculation, validation, exception, message, and file I/O
findings.
```

## 7. Closeout Checklist

Use this as the project closeout checklist:

- [ ] README links to this E2E code scan guide.
- [ ] Repo scan mode works and explains its limits.
- [ ] Normal / complex / large program guidelines are available.
- [ ] Large-program path handles 10,000+ line RPG members through index +
      five-routine batches.
- [ ] Central delivery repo lookup happens before any new source scan.
- [ ] `program-analysis.md` and `routine-logic-details.md` validation is
      documented.
- [ ] Central delivery repo sync path is documented.
- [ ] PR review / merge-to-main model is documented.
- [ ] Internal adoption message is ready.
- [ ] Other-department SME guidance is ready.
- [ ] Known gaps remain visible: unresolved message descriptions, missing
      copybooks, external program semantics, adapter drift, and runtime smoke
      gaps must not be hidden.
