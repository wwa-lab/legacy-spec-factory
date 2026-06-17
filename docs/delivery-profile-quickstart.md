# Delivery Profile Quickstart

Use this guide when a team wants to scan source code from one repo and store
reviewed scan artifacts in a separate delivery repo.

## Two Repos

Use the source repo as the read-only code evidence source.

Use the delivery repo for generated analysis artifacts, SME reviews, PR review,
and future reuse. Only delivery repo remote `main` is treated as the approved
central artifact source.

## One Profile

Start from:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

Edit these team-owned values once:

```yaml
delivery_artifact_lookup_profile:
  repo: CH-WPS-LENDING-CARDS/legacy-modernization-delivery
  branch: main
  program_folder_patterns:
    - modules/*/{PROGRAM}

delivery_workspace_profile:
  branch_mode: use_or_create_provided
  working_branch_pattern: develop-{PERSON}
  write_to_main: false
  program_set_review_parent: modules/CAP-ID-0004-program_set_reviews
  program_tier_roots:
    large_extreme_program: modules/CAP-ID-0001-large_extreme_program
    complex_normal_program: modules/CAP-ID-0002-complex_normal_program
    normal_program: modules/CAP-ID-0003-normal_program
```

## Runtime Inputs

The SME or engineer should provide only the work-specific values:

```text
Delivery working branch: develop-leo
Review name: card auth posting core review
Programs:
- @CU118
- CU257F
- CC050
```

The tool may create `develop-leo` from `origin/main` if it does not exist.
New outputs are written to `develop-leo`, never directly to `main`.

## Routing Rules

Lookup always reads delivery repo remote `main`:

```text
found_on_remote_main      -> read compact artifacts from remote-main checkout
not_found_on_remote_main  -> scan source repo and write output to develop-*
remote_unavailable        -> stop for access/context
```

Program artifacts are stored by tier:

```text
modules/CAP-ID-0001-large_extreme_program/<PROGRAM>/
modules/CAP-ID-0002-complex_normal_program/<PROGRAM>/
modules/CAP-ID-0003-normal_program/<PROGRAM>/
```

Program-set reviews are cross-tier and stored under one configured parent:

```text
modules/CAP-ID-0004-program_set_reviews/<review_slug>/
  program-set-core-input-manifest.yaml
  program-set-sme-core-review.md
```

## Invariants

- `@CU118` and `CU118` are different program identities unless the profile
  explicitly defines aliases.
- A working branch such as `develop-leo` is draft output only; it is not an
  approved reuse source.
- PR merge to `main` promotes artifacts into the central reusable snapshot.
