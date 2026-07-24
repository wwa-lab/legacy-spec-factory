# Active Example: Blocked Reader-First Merge

This is the active negative contract walkthrough for the v0.4.0 Program
Analysis Merger. It demonstrates semantic readiness blocking and targeted
recovery. Its paths are symbolic; executable fixtures live in the repository
test suite.

## Request

```text
Review name: Credit check
Artifact repo mode: approved_document_repo
Programs:
1. CU106
2. CU404
```

CU106 passes readiness. CU404 has files, but its upstream validator reports an
unfinished retained deep-read batch and an unresolved message description.
File presence does not make CU404 ready.

## Required Result

The manifest records `review_status: blocked_artifact_readiness`,
`artifact_readiness: not_ready`, and `merge_coverage: blocked`; CU404's program
row records `artifact_readiness.status: not_ready` with the validator findings.
Preparation may write control artifacts needed for recovery, but it must not
create:

```text
<FLOW-SLUG>--<PROGRAM-SET-SLUG>--sme-core-review.md
```

It must not create the old generic review filename either. A partial CU106
review is not an acceptable substitute.

If fresh source inventory maps CU404 to an exact member path, create a targeted
queue containing CU404 only:

```text
<FLOW-SLUG>--<PROGRAM-SET-SLUG>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md  # available sections + pending markers
  program-set-core-facts.yaml              # facts from available scan results
  program-set-core-coverage.yaml       # pending; draft merge not yet reconciled
  missing-program-list-batch/
    program-list.csv                 # CU404 only
    prompt-queue/
```

Do not queue CU106 and do not rescan the whole repository. If inventory is
missing/stale or CU404 is absent, the adapter instead writes only:

```text
missing-program-list-batch/
  blocked-programs.csv               # CU404; no guessed source path
```

In that case it writes no `program-list.csv` and no `prompt-queue/`. When all
programs are ready, the adapter is not run and
`missing-program-list-batch/` does not exist.

While blocked, the source pack and core facts may be present when candidate
scan results exist. They are valid only for an explicitly labelled
`draft_exploratory` scan-result merge. Every formal review filename must be
absent.

After CU404 is completed and its upstream validator passes, rerun preparation
from the original two-program list. Only then may the executing skill LLM read
the complete source pack and write the unique formal review.

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang
Original author: Leo L Zhang
License: Apache License 2.0
-->
