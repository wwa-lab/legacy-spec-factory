#requires -version 5.1

<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
#>

# Immutable large-program deep-read execution-plan validation.  The plan is
# generated before semantic work begins, so terminal validation cannot be
# bypassed by dropping later checkpoints or replacing their RLOG assignments.

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'ProgramAnalysisContract.Common.psm1') -Force

$ExecutionPlanBatchSize = 5
$ExecutionPlanRlogPattern = '^RLOG-[A-Z0-9_#$@-]+-\d{3}$'
$ExecutionPlanWindowPattern = '^DRW-[A-Z0-9_#$@-]+-\d{3}$'

function ConvertTo-ExecutionPlanPath {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return $Value.Replace('\', '/').TrimStart([char[]]@('.', '/'))
}

function Get-ExecutionPlanRelativePath {
    param([string]$AnalysisDir, [string]$Path)

    $root = [regex]::Replace([IO.Path]::GetFullPath($AnalysisDir), '[\\/]+$', '')
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = $root + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { return '' }
    return $full.Substring($prefix.Length).Replace('\', '/')
}

function Test-ExecutionPlanRelativePath {
    param([string]$Value)

    $normalized = ConvertTo-ExecutionPlanPath $Value
    return ($normalized -ne '' -and -not [IO.Path]::IsPathRooted($normalized) -and
        -not $normalized.StartsWith('//') -and $normalized -notmatch '^[A-Za-z]:/' -and
        -not $normalized.StartsWith('../') -and $normalized -notmatch '(^|/)\.\.(/|$)')
}

function Get-BatchDetailFiles {
    param([string]$AnalysisDir)

    $filesByPath = @{}
    $summaryPath = Find-RoutineArtifactPath $AnalysisDir 'program-analysis-summary.yaml'
    if ($summaryPath) {
        $entries = Get-SidecarEntries $summaryPath
        foreach ($key in $entries.Keys) {
            $entry = $entries[$key]
            if ($key.StartsWith('routine_logic_deep_read_batch_') -and [string]$entry.path -ne '') {
                $declaredPath = Join-Path $AnalysisDir ([string]$entry.path)
                if (Test-Path -LiteralPath $declaredPath -PathType Leaf) {
                    $file = Get-Item -LiteralPath $declaredPath
                    $filesByPath[$file.FullName] = $file
                }
            }
        }
    }
    $batchDir = Join-Path $AnalysisDir 'routine-logic-details'
    if (Test-Path -LiteralPath $batchDir -PathType Container) {
        foreach ($filter in @('part-*.md', '*-part-*.md', 'deep-read-batch-*.md', '*-deep-read-batch-*.md', 'deep-batch-*.md', '*-deep-batch-*.md')) {
            foreach ($file in @(Get-ChildItem -LiteralPath $batchDir -Filter $filter -File -ErrorAction SilentlyContinue)) {
                $filesByPath[$file.FullName] = $file
            }
        }
    }
    return @($filesByPath.Values | Sort-Object @{
        Expression = { if ($_.BaseName -match '(\d+)$') { [int]$Matches[1] } else { [int]::MaxValue } }
    }, Name)
}

function Test-RequiresLargeProgramBatches {
    param(
        [string]$SummaryPath,
        [AllowNull()][string]$ExpectedSizeTier,
        [AllowNull()][string]$AnalysisDir
    )

    if ($ExpectedSizeTier -and $ExpectedSizeTier.Trim().ToLowerInvariant() -eq 'large_extreme_program') { return $true }
    if ($AnalysisDir -and $AnalysisDir.ToLowerInvariant().Contains('large_extreme_program')) { return $true }
    if ([string]::IsNullOrEmpty($SummaryPath) -or -not (Test-Path -LiteralPath $SummaryPath -PathType Leaf)) { return $false }
    $lines = Get-YamlLines $SummaryPath
    if ((Get-YamlRootScalar $lines 'program_size_tier') -eq 'large_extreme_program') { return $true }
    $parsed = 0
    if ([int]::TryParse((Get-YamlNestedScalar $lines 'counts' 'source_lines'), [ref]$parsed) -and $parsed -gt 10000) { return $true }
    $parsed = 0
    return ([int]::TryParse((Get-YamlNestedScalar $lines 'source' 'line_count'), [ref]$parsed) -and $parsed -gt 10000)
}

function Validate-LargeProgramBatches {
    param(
        [string]$AnalysisDir,
        [AllowNull()][string]$ExpectedSizeTier
    )

    $summaryPath = Find-RoutineArtifactPath $AnalysisDir 'program-analysis-summary.yaml'
    if (-not (Test-RequiresLargeProgramBatches $summaryPath $ExpectedSizeTier $AnalysisDir)) { return @() }
    $findings = New-Object System.Collections.Generic.List[string]
    $expectedLarge = $ExpectedSizeTier -and $ExpectedSizeTier.Trim().ToLowerInvariant() -eq 'large_extreme_program'
    $pathLarge = $AnalysisDir.ToLowerInvariant().Contains('large_extreme_program')
    if ($expectedLarge -or $pathLarge) {
        $declaredTier = if ($summaryPath -and (Test-Path -LiteralPath $summaryPath -PathType Leaf)) {
            Get-YamlRootScalar (Get-YamlLines $summaryPath) 'program_size_tier'
        } else { '' }
        if ($declaredTier -ne 'large_extreme_program') {
            $origin = if ($expectedLarge) { 'the expected size tier' } else { 'the canonical artifact directory path' }
            [void]$findings.Add(
                "large-program tier contract mismatch: $origin requires program-analysis-summary.yaml to declare " +
                "program_size_tier: large_extreme_program; found $(if ($declaredTier) { $declaredTier } else { 'missing' })"
            )
        }
    }
    $batches = @(Get-BatchDetailFiles $AnalysisDir)
    if ($batches.Count -eq 0) {
        [void]$findings.Add('large_extreme_program requires routine-logic-details/deep-read-batch-*.md batch checkpoint files')
        return @($findings.ToArray())
    }
    if (@($batches | Where-Object { $_.Name -match '(?:deep-read-batch|deep-batch)-0*1\.md$' }).Count -eq 0) {
        [void]$findings.Add('large_extreme_program requires a first batch checkpoint: routine-logic-details/deep-read-batch-001.md')
    }
    return @($findings.ToArray())
}

function Get-ExecutionPlanSha256 {
    param([string]$Path)

    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [IO.File]::ReadAllBytes($Path)
        return ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $hasher.Dispose()
    }
}

function Get-BatchWindowRlogPairs {
    param([string]$BatchText)

    $rows = @(Get-MarkdownTableRows (Get-H2SectionText $BatchText 'Batch Coverage Summary'))
    if ($rows.Count -eq 0) { return @{} }
    $windowColumn = -1
    $rlogColumn = -1
    for ($index = 0; $index -lt $rows[0].Cells.Count; $index++) {
        $header = ([regex]::Replace([string]$rows[0].Cells[$index], '[*_`]', '')).Trim().ToLowerInvariant()
        if ($header -in @('window id', 'deep-read window', 'deep read window')) { $windowColumn = $index }
        if ($header -in @('rlog detail', 'rlog', 'detail link')) { $rlogColumn = $index }
    }
    if ($windowColumn -lt 0 -or $rlogColumn -lt 0) { return @{} }
    $pairs = @{}
    for ($rowIndex = 1; $rowIndex -lt $rows.Count; $rowIndex++) {
        $row = $rows[$rowIndex].Cells
        if ($windowColumn -ge $row.Count -or $rlogColumn -ge $row.Count) { continue }
        $window = [regex]::Match([string]$row[$windowColumn], 'DRW-[A-Z0-9_#$@-]+-\d{3}', 'IgnoreCase')
        $rlog = [regex]::Match([string]$row[$rlogColumn], 'RLOG-[A-Z0-9_#$@-]+-\d{3}', 'IgnoreCase')
        if ($window.Success -and $rlog.Success) {
            $pairs[$window.Value.ToUpperInvariant()] = $rlog.Value.ToUpperInvariant()
        }
    }
    return $pairs
}

function Get-BatchWindowRlogDuplicateFindings {
    param([string]$BatchText, [string]$BatchPath)

    $rows = @(Get-MarkdownTableRows (Get-H2SectionText $BatchText 'Batch Coverage Summary'))
    if ($rows.Count -eq 0) { return @() }
    $windowColumn = -1
    $rlogColumn = -1
    for ($index = 0; $index -lt $rows[0].Cells.Count; $index++) {
        $header = ([regex]::Replace([string]$rows[0].Cells[$index], '[*_`]', '')).Trim().ToLowerInvariant()
        if ($header -in @('window id', 'deep-read window', 'deep read window')) { $windowColumn = $index }
        if ($header -in @('rlog detail', 'rlog', 'detail link')) { $rlogColumn = $index }
    }
    if ($windowColumn -lt 0 -or $rlogColumn -lt 0) { return @() }
    $seenWindows = @{}
    $seenRlogs = @{}
    $findings = New-Object System.Collections.ArrayList
    for ($rowIndex = 1; $rowIndex -lt $rows.Count; $rowIndex++) {
        $row = $rows[$rowIndex].Cells
        if ($windowColumn -ge $row.Count -or $rlogColumn -ge $row.Count) { continue }
        $window = [regex]::Match([string]$row[$windowColumn], 'DRW-[A-Z0-9_#$@-]+-\d{3}', 'IgnoreCase')
        $rlog = [regex]::Match([string]$row[$rlogColumn], 'RLOG-[A-Z0-9_#$@-]+-\d{3}', 'IgnoreCase')
        if (-not $window.Success -or -not $rlog.Success) { continue }
        $windowId = $window.Value.ToUpperInvariant()
        $rlogId = $rlog.Value.ToUpperInvariant()
        if ($seenWindows.ContainsKey($windowId)) {
            [void]$findings.Add("large deep-read execution plan batch $BatchPath duplicates window coverage: $windowId")
        }
        if ($seenRlogs.ContainsKey($rlogId)) {
            [void]$findings.Add("large deep-read execution plan batch $BatchPath duplicates RLOG coverage: $rlogId")
        }
        $seenWindows[$windowId] = $true
        $seenRlogs[$rlogId] = $true
    }
    return @($findings.ToArray())
}

function Get-LargeExecutionPlanEntries {
    param(
        [string]$AnalysisDir,
        [AllowNull()][string]$ExpectedSizeTier,
        [AllowNull()][string]$ExpectedSourceIndexSha256,
        [AllowNull()][string]$ExpectedExecutionPlanSha256
    )

    $summaryPath = Find-RoutineArtifactPath $AnalysisDir 'program-analysis-summary.yaml'
    if (-not (Test-RequiresLargeProgramBatches $summaryPath $ExpectedSizeTier $AnalysisDir)) {
        return [pscustomobject]@{ Entries = @(); Findings = @() }
    }
    $findings = New-Object System.Collections.ArrayList
    $summaryEntries = if ($summaryPath) { Get-SidecarEntries $summaryPath } else { @{} }
    if (-not $summaryEntries.ContainsKey('deep_read_execution_plan') -or
        [string]$summaryEntries['deep_read_execution_plan'].path -eq '') {
        return [pscustomobject]@{
            Entries = @()
            Findings = @('large_extreme_program requires a declared deep-read execution plan (<PROGRAM>-deep-read-execution-plan.yaml)')
        }
    }
    $planEntry = $summaryEntries['deep_read_execution_plan']
    if ([string]$planEntry.status -ne 'present') {
        [void]$findings.Add('large deep-read execution plan sidecar must have status present')
    }
    $declaredPlanPath = [string]$planEntry.path
    if (-not (Test-ExecutionPlanRelativePath $declaredPlanPath)) {
        [void]$findings.Add('large deep-read execution plan path must be a relative artifact path')
        return [pscustomobject]@{ Entries = @(); Findings = @($findings.ToArray()) }
    }
    $planPath = Join-Path $AnalysisDir $declaredPlanPath
    if (-not (Test-Path -LiteralPath $planPath -PathType Leaf)) {
        [void]$findings.Add('large_extreme_program requires a declared deep-read execution plan (<PROGRAM>-deep-read-execution-plan.yaml)')
        return [pscustomobject]@{ Entries = @(); Findings = @($findings.ToArray()) }
    }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedExecutionPlanSha256) -and
        $ExpectedExecutionPlanSha256.Trim().ToLowerInvariant() -ne (Get-ExecutionPlanSha256 $planPath)) {
        [void]$findings.Add('large deep-read execution plan immutable batch execution lock does not match the precreated execution-plan SHA-256')
    }
    $canonicalPlanPath = Find-RoutineArtifactPath $AnalysisDir 'deep-read-execution-plan.yaml'
    if (-not $canonicalPlanPath -or
        [IO.Path]::GetFullPath($canonicalPlanPath) -ne [IO.Path]::GetFullPath($planPath)) {
        [void]$findings.Add(
            'large deep-read execution plan path must resolve to the single canonical ' +
            '<PROGRAM>-deep-read-execution-plan.yaml artifact'
        )
    }
    $planName = Split-Path -Leaf $planPath
    $planLines = Get-YamlLines $planPath
    if ((Get-YamlRootScalar $planLines 'program_size_tier').Trim().ToLowerInvariant() -ne 'large_extreme_program') {
        [void]$findings.Add("large deep-read execution plan $planName must declare program_size_tier: large_extreme_program")
    }

    $sourceIndexPath = Find-RoutineArtifactPath $AnalysisDir 'source-index.yaml'
    if (-not $sourceIndexPath -or -not (Test-Path -LiteralPath $sourceIndexPath -PathType Leaf)) {
        [void]$findings.Add("large deep-read execution plan $planName cannot verify its source-index")
    }
    else {
        $declaredSourcePath = ConvertTo-ExecutionPlanPath (Get-YamlRootScalar $planLines 'source_index_path')
        $actualSourcePath = ConvertTo-ExecutionPlanPath (Get-ExecutionPlanRelativePath $AnalysisDir $sourceIndexPath)
        if ($declaredSourcePath -ne $actualSourcePath) {
            [void]$findings.Add("large deep-read execution plan $planName source_index_path does not match declared source index: $(if ($declaredSourcePath) { $declaredSourcePath } else { 'missing' })")
        }
        $expectedDigest = (Get-YamlRootScalar $planLines 'source_index_sha256').Trim().ToLowerInvariant()
        if ($expectedDigest -ne (Get-ExecutionPlanSha256 $sourceIndexPath)) {
            [void]$findings.Add("large deep-read execution plan $planName source-index digest does not match the declared source index")
        }
        if (-not [string]::IsNullOrWhiteSpace($ExpectedSourceIndexSha256) -and
            $ExpectedSourceIndexSha256.Trim().ToLowerInvariant() -ne (Get-ExecutionPlanSha256 $sourceIndexPath)) {
            [void]$findings.Add('large deep-read execution plan immutable batch execution lock does not match the precreated source-index SHA-256')
        }
    }

    $rawEntries = @(Get-YamlListMappings $planPath '' 'planned_deep_read')
    if ($rawEntries.Count -eq 0) {
        [void]$findings.Add("large deep-read execution plan $planName has no planned_deep_read entries")
        return [pscustomobject]@{ Entries = @(); Findings = @($findings.ToArray()) }
    }
    $entries = New-Object System.Collections.ArrayList
    $seenWindows = @{}
    $seenRlogs = @{}
    $entryNumber = 0
    foreach ($raw in $rawEntries) {
        $entryNumber++
        $batchNumber = 0
        [void]([int]::TryParse(([string]$raw.batch_number), [ref]$batchNumber))
        $entry = [pscustomobject]@{
            WindowId = ([string]$raw.window_id).Trim().ToUpperInvariant()
            Routine = ([string]$raw.routine).Trim()
            SourceLines = ([string]$raw.source_lines).Trim()
            RlogId = ([string]$raw.rlog_id).Trim().ToUpperInvariant()
            BatchNumber = $batchNumber
            BatchPath = ConvertTo-ExecutionPlanPath ([string]$raw.batch_path)
        }
        $missing = New-Object System.Collections.ArrayList
        foreach ($field in @('WindowId', 'Routine', 'SourceLines', 'RlogId', 'BatchPath')) {
            if ([string]($entry.$field) -eq '') { [void]$missing.Add($field.ToLowerInvariant()) }
        }
        if ($entry.BatchNumber -lt 1) { [void]$missing.Add('batch_number') }
        if ($missing.Count -gt 0) {
            [void]$findings.Add("large deep-read execution plan $planName entry $entryNumber is missing/invalid: $($missing -join ', ')")
            continue
        }
        if ($entry.WindowId -notmatch $ExecutionPlanWindowPattern) {
            [void]$findings.Add("large deep-read execution plan $planName entry $entryNumber has invalid window_id")
        }
        if ($entry.RlogId -notmatch $ExecutionPlanRlogPattern) {
            [void]$findings.Add("large deep-read execution plan $planName entry $entryNumber has invalid rlog_id")
        }
        if (-not (Test-ExecutionPlanRelativePath $entry.BatchPath)) {
            [void]$findings.Add("large deep-read execution plan $planName entry $entryNumber has invalid batch_path")
        }
        $expectedBatchSuffix = 'deep-read-batch-{0:D3}.md' -f $entry.BatchNumber
        if (-not $entry.BatchPath.StartsWith('routine-logic-details/') -or
            -not $entry.BatchPath.EndsWith($expectedBatchSuffix, [StringComparison]::OrdinalIgnoreCase)) {
            [void]$findings.Add(
                "large deep-read execution plan $planName entry $entryNumber batch_path " +
                "must identify batch $($entry.BatchNumber.ToString('D3')) under routine-logic-details"
            )
        }
        if ($seenWindows.ContainsKey($entry.WindowId)) {
            [void]$findings.Add("large deep-read execution plan $planName duplicates window $($entry.WindowId)")
        }
        if ($seenRlogs.ContainsKey($entry.RlogId)) {
            [void]$findings.Add("large deep-read execution plan $planName duplicates RLOG $($entry.RlogId)")
        }
        $seenWindows[$entry.WindowId] = $true
        $seenRlogs[$entry.RlogId] = $true
        [void]$entries.Add($entry)
    }

    if ($sourceIndexPath -and (Test-Path -LiteralPath $sourceIndexPath -PathType Leaf)) {
        $sourceDetails = @(Get-YamlListMappings $sourceIndexPath 'routine_logic_inventory' 'details')
        if ($sourceDetails.Count -gt 0) {
            $rlogByRoutine = @{}
            foreach ($detail in $sourceDetails) {
                $routine = ([string]$detail.routine).Trim()
                $rlogId = ([string]$detail.detail_id).Trim().ToUpperInvariant()
                if ($routine -and $rlogId) { $rlogByRoutine[$routine] = $rlogId }
            }
            $unbound = @($entries.ToArray() | Where-Object {
                -not $rlogByRoutine.ContainsKey($_.Routine) -or
                $rlogByRoutine[$_.Routine] -ne $_.RlogId
            })
            if ($unbound.Count -gt 0) {
                [void]$findings.Add(
                    "large deep-read execution plan $planName does not bind planned RLOG IDs " +
                    'to source-index routine_logic_inventory.details'
                )
            }
        }
        $sourceWindows = @(Get-YamlListMappings $sourceIndexPath '' 'deep_read_windows')
        if ($sourceWindows.Count -gt 0) {
            $expectedWindows = @{}
            foreach ($window in $sourceWindows) {
                $expectedWindows[(([string]$window.window_id).Trim().ToUpperInvariant() + '|' + ([string]$window.routine).Trim() + '|' + ([string]$window.source_lines).Trim())] = $true
            }
            $actualWindows = @{}
            foreach ($entry in @($entries.ToArray())) {
                $actualWindows[$entry.WindowId + '|' + $entry.Routine + '|' + $entry.SourceLines] = $true
            }
            $missingWindows = @($expectedWindows.Keys | Where-Object { -not $actualWindows.ContainsKey($_) })
            $unexpectedWindows = @($actualWindows.Keys | Where-Object { -not $expectedWindows.ContainsKey($_) })
            if ($missingWindows.Count -gt 0 -or $unexpectedWindows.Count -gt 0) {
                [void]$findings.Add("large deep-read execution plan $planName does not match source-index deep_read_windows")
            }
        }
    }
    return [pscustomobject]@{ Entries = @($entries.ToArray()); Findings = @($findings.ToArray()) }
}

function Get-LargeExecutionPlanValidationResult {
    param(
        [string]$AnalysisDir,
        [AllowNull()][string]$ExpectedSizeTier,
        [AllowNull()][string]$ExpectedSourceIndexSha256,
        [AllowNull()][string]$ExpectedExecutionPlanSha256
    )

    $loaded = Get-LargeExecutionPlanEntries $AnalysisDir $ExpectedSizeTier $ExpectedSourceIndexSha256 $ExpectedExecutionPlanSha256
    $findings = New-Object System.Collections.ArrayList
    foreach ($finding in @($loaded.Findings)) { [void]$findings.Add($finding) }
    $entries = @($loaded.Entries)
    if ($entries.Count -eq 0) {
        return [pscustomobject]@{ Findings = @($findings.ToArray()); PlannedRlogIds = @() }
    }
    $expectedByBatch = @{}
    foreach ($entry in $entries) {
        if (-not $expectedByBatch.ContainsKey($entry.BatchPath)) {
            $expectedByBatch[$entry.BatchPath] = New-Object System.Collections.ArrayList
        }
        [void]$expectedByBatch[$entry.BatchPath].Add($entry)
    }
    $actualByBatch = @{}
    foreach ($batch in @(Get-BatchDetailFiles $AnalysisDir)) {
        $relative = ConvertTo-ExecutionPlanPath (Get-ExecutionPlanRelativePath $AnalysisDir $batch.FullName)
        if ($relative) { $actualByBatch[$relative] = $batch }
    }
    foreach ($batchPath in $expectedByBatch.Keys) {
        if (-not $actualByBatch.ContainsKey($batchPath)) {
            [void]$findings.Add("large deep-read execution plan batch is missing: $batchPath")
            continue
        }
        $batchText = Read-Utf8Text $actualByBatch[$batchPath].FullName
        $actualPairs = Get-BatchWindowRlogPairs $batchText
        foreach ($finding in @(Get-BatchWindowRlogDuplicateFindings $batchText $batchPath)) {
            [void]$findings.Add($finding)
        }
        $expectedPairs = @{}
        foreach ($entry in @($expectedByBatch[$batchPath])) { $expectedPairs[$entry.WindowId] = $entry.RlogId }
        if ($actualPairs.Count -eq 0) {
            [void]$findings.Add("large deep-read execution plan batch $batchPath has no window-to-RLOG coverage")
            continue
        }
        $missingWindows = @($expectedPairs.Keys | Where-Object { -not $actualPairs.ContainsKey($_) } | Sort-Object)
        $unexpectedWindows = @($actualPairs.Keys | Where-Object { -not $expectedPairs.ContainsKey($_) } | Sort-Object)
        $wrongPairs = @($expectedPairs.Keys | Where-Object { $actualPairs.ContainsKey($_) -and $actualPairs[$_] -ne $expectedPairs[$_] } | Sort-Object)
        if ($missingWindows.Count -gt 0 -or $unexpectedWindows.Count -gt 0 -or $wrongPairs.Count -gt 0) {
            $detail = New-Object System.Collections.ArrayList
            if ($missingWindows.Count -gt 0) { [void]$detail.Add('missing ' + ($missingWindows -join ', ')) }
            if ($unexpectedWindows.Count -gt 0) { [void]$detail.Add('unexpected ' + ($unexpectedWindows -join ', ')) }
            if ($wrongPairs.Count -gt 0) { [void]$detail.Add('wrong RLOG mapping for ' + ($wrongPairs -join ', ')) }
            [void]$findings.Add("large deep-read execution plan batch $batchPath coverage does not match plan: $($detail -join '; ')")
        }
        if ($actualPairs.Count -gt $ExecutionPlanBatchSize) {
            [void]$findings.Add("large deep-read execution plan batch $batchPath exceeds $ExecutionPlanBatchSize windows")
        }
    }
    $unexpectedBatches = @($actualByBatch.Keys | Where-Object { -not $expectedByBatch.ContainsKey($_) } | Sort-Object)
    if ($unexpectedBatches.Count -gt 0) {
        [void]$findings.Add('large deep-read execution plan has retained batch file(s) not in plan: ' + ($unexpectedBatches -join ', '))
    }
    return [pscustomobject]@{
        Findings = @($findings.ToArray())
        PlannedRlogIds = @($entries | ForEach-Object { $_.RlogId })
    }
}

Export-ModuleMember -Function @(
    'Get-BatchDetailFiles',
    'Test-RequiresLargeProgramBatches',
    'Validate-LargeProgramBatches',
    'Get-LargeExecutionPlanValidationResult'
)
