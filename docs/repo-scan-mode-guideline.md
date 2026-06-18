# IBM i Repo Scan Mode Guideline

This guideline explains how to use Legacy Spec Factory's repo scan mode when
the skills are copied into another GitHub repository, including GitHub Copilot
or a customer source repository.

Repo scan mode is owned by `legacy-ibmi-inventory`. Its purpose is to create a
first-pass program inventory and tier report. It does not produce approved
business logic, program flow, BRD, or spec artifacts.

## When To Use

Use repo scan mode when you need to:

- scan a GitHub repository or source export for IBM i source members
- produce a program list with line counts
- classify RPG/RPGLE/SQLRPGLE programs into the same tiers used by
  `legacy-ibmi-program-analyzer`
- identify `large_extreme_program` entries before assigning detailed analysis
  work
- prepare an initial triage package for engineering leads, SMEs, or managers

Do not treat repo scan output as final modernization evidence. It is a triage
input for deciding what to analyze next.

Before running repo scan for a named program or SME-provided program flow,
check the central delivery documents repo remote `main` for an exact existing
program-analysis folder. Use a configurable `delivery_artifact_lookup_profile`;
the current lending-card default is
`CH-WPS-LENDING-CARDS/legacy-modernization-delivery` with exact program folders
under `modules/*/{PROGRAM}`. Leading `@` is part of the program identity, so
`@CU118` and `CU118` do not cross-match. Use Git method 2:
`git ls-remote` plus a temporary shallow clone / sparse checkout, or an
already-fresh local cache verified against `origin/main`. Repo scan is needed
only when the exact program folder is `not_found_on_remote_main`. If the remote
cannot be checked, treat the result as `remote_unavailable`, not as missing.

## Required Skill Folders

When running outside the `legacy-spec-factory` repository, copy the relevant
skill folders into the target repository.

Minimum required layout:

```text
skills/
  legacy-ibmi-inventory/
    SKILL.md
    scripts/
      scan_ibmi_repo.py

  legacy-ibmi-program-analyzer/
    SKILL.md
    scripts/
      index_rpg_source.py
```

`legacy-ibmi-inventory` provides the repo scanner. The scanner reuses
`legacy-ibmi-program-analyzer/scripts/index_rpg_source.py` so that
RPG/RPGLE/SQLRPGLE tier classification stays consistent with individual
program analysis.

The root-level convenience wrapper in this repository:

```text
scripts/scan-ibmi-repo.py
```

is not required when skills are copied into another repository. Use the skill
script directly.

## How To Run

From the target repository root on Windows:

```powershell
py -3 skills\legacy-ibmi-inventory\scripts\scan_ibmi_repo.py . --out-dir outputs\repo-scan
```

From the target repository root on macOS or Linux:

```bash
python3 skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py . --out-dir outputs/repo-scan
```

To scan a different source root on Windows:

```powershell
py -3 skills\legacy-ibmi-inventory\scripts\scan_ibmi_repo.py C:\path\to\source-root --out-dir outputs\repo-scan
```

macOS/Linux:

```bash
python3 skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py /path/to/source-root --out-dir outputs/repo-scan
```

Optional threshold override on Windows:

```powershell
py -3 skills\legacy-ibmi-inventory\scripts\scan_ibmi_repo.py . --out-dir outputs\repo-scan --large-threshold 10000
```

macOS/Linux:

```bash
python3 skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py . --out-dir outputs/repo-scan --large-threshold 10000
```

`--large-threshold` is a fallback threshold for source kinds that do not yet
have a language-specific analyzer. RPG/RPGLE/SQLRPGLE classification comes
from `legacy-ibmi-program-analyzer`.

## Outputs

The scanner writes:

```text
outputs/repo-scan/program-list.csv
outputs/repo-scan/large-program-candidates.md
outputs/repo-scan/scan-summary.yaml
```

The Markdown report is currently written to `large-program-candidates.md` for
compatibility, but its content is a full program tier report.

## CSV Columns

`program-list.csv` contains one row per discovered IBM i source member.

Important columns:

| Column | Meaning |
| --- | --- |
| `member` | Source member or file stem, uppercased. |
| `object_type` | `program` or `dds_object`. |
| `source_kind` | Detected source kind, such as `RPGLE`, `SQLRPGLE`, `CLLE`, `DDS_PF`, or `DDS_DSPF`. |
| `path` | Path relative to the scanned root. |
| `total_lines` | Total physical source lines. |
| `nonblank_lines` | Nonblank physical source lines. |
| `comment_lines` | Comment lines detected by source-kind rules. |
| `code_lines` | Nonblank lines minus comment lines. |
| `size_tier` | `normal_program`, `complex_normal_program`, `large_extreme_program`, or `non_program_source`. |
| `tier_reason` | Reason for the tier decision. |
| `default_output_profile` | Recommended analysis profile for the tier. |
| `classification_source` | `legacy-ibmi-program-analyzer`, `repo_scanner_line_count_fallback`, or `repo_scanner_non_program_source`. |
| `routine_count` | Routine count from the RPG source indexer when available. |
| `external_call_count` | External call count from the RPG source indexer when available. |
| `object_dependency_count` | Object dependency count from the RPG source indexer when available. |
| `file_operation_count` | File operation count from the RPG source indexer when available. |
| `sql_statement_count` | Embedded SQL statement count from the RPG source indexer when available. |
| `recommended_deep_read_count` | Number of deep-read windows recommended by the RPG source indexer. |

Example:

```csv
member,object_type,source_kind,path,total_lines,nonblank_lines,comment_lines,code_lines,size_tier,tier_reason,default_output_profile,classification_source,routine_count,external_call_count,object_dependency_count,file_operation_count,sql_statement_count,recommended_deep_read_count
ORDERHDR,program,RPGLE,QRPGLESRC/ORDERHDR.RPGLE,12450,11870,580,11290,large_extreme_program,"source length exceeds 10,000 lines",full_index_and_batched_deep_read,legacy-ibmi-program-analyzer,42,18,31,96,0,17
ARRECON,program,SQLRPGLE,QRPGLESRC/ARRECON.SQLRPGLE,4200,3905,295,3610,complex_normal_program,source length exceeds normal-program comfort threshold,light_review_plus_triggered_sidecars,legacy-ibmi-program-analyzer,12,4,9,24,6,8
```

## Markdown Layout

The Markdown report groups programs by tier.

```text
# Program Tier Report

## Summary
  - program count
  - fallback large threshold
  - count of large_extreme_program
  - count of complex_normal_program
  - count of normal_program

## large_extreme_program
  - highest priority for full program analysis

## complex_normal_program
  - review for call/data centrality and SME criticality

## normal_program
  - suitable for lightweight flow or SME review packages

## Recommended Next Step
  - action guidance for large, complex, and normal programs
```

## Tier Meaning

### `large_extreme_program`

These programs should be prioritized for full `legacy-ibmi-program-analyzer`
output and batched deep-read planning.

Typical reasons include:

- source length exceeds 10,000 lines
- routine count exceeds the analyzer threshold
- external call count is very high
- object dependency count is very high

### `complex_normal_program`

These programs are not extreme, but they are dense enough to deserve closer
triage before being treated as normal.

Typical reasons include:

- source length exceeds the normal-program comfort threshold
- routine count is elevated
- external calls, object dependencies, file operations, field mutations, SQL,
  messages, or deep-read windows are dense

### `normal_program`

These programs can usually start with lightweight SME review or program flow
output. They may still be promoted if SME criticality, call centrality, or data
impact is high.

### `non_program_source`

DDS and related source objects are inventoried but are not assigned program
analysis tiers.

## Recommended Workflow

1. Check the central delivery repo remote `main` for exact program-analysis
   folders using Git method 2.
2. Run `legacy-ibmi-inventory` repo scan mode against the source repository
   only for programs with `central_lookup_result: not_found_on_remote_main`.
3. Review `program-list.csv` and the Markdown tier report.
4. Assign `large_extreme_program` entries to full `legacy-ibmi-program-analyzer`
   processing first.
5. Review `complex_normal_program` entries using call graph, file dependency,
   and SME criticality.
6. Use lightweight flow or SME review packages for `normal_program` entries.
7. Promote any normal program if downstream analysis shows high business or
   data risk.

## Suggested Copilot Prompt

Use this prompt in a target GitHub repository after the skill folders are
copied in:

```text
Use legacy-ibmi-inventory repo scan mode.

Run skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py against the current
repository root and write outputs to outputs/repo-scan.

Then summarize:
- count of source members
- count of normal_program, complex_normal_program, and large_extreme_program
- top large_extreme_program entries and their tier_reason
- any source kinds that used repo_scanner_line_count_fallback
```

## Important Limits

- Repo scan mode is not evidence approval.
- Repo scan mode is not business-rule extraction.
- Repo scan mode is not program flow analysis.
- Repo scan mode does not replace SME review.
- For formal delivery, downstream artifacts still need the normal evidence,
  inventory, program analysis, flow analysis, and approval gates.
