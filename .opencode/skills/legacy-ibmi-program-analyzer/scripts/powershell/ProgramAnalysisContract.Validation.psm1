#requires -version 5.1

<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
#>

# Native Windows PowerShell 5.1 fallback for program-analysis contract
# validation. This script intentionally uses only built-in PowerShell/.NET
# APIs; it does not invoke Python and does not require a YAML module.

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'ProgramAnalysisContract.Common.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramAnalysisContract.ExecutionPlan.psm1') -Force

# Final completion surfaces include routine-logic-details.md/yaml, every
# *-deep-read-batch-*.md checkpoint, and explicit pending_deep_read or
# semantic_status: indexed_only seed states.

$RequiredProgramSections = @(
    'Program Reading Summary',
    'Calculation Logic',
    'Validation Logic',
    'Exception Handling',
    'Message Inventory',
    'Metadata',
    'Analysis Coverage & Scope',
    'Program Call Map',
    'Routine Cards',
    'Routine Logic Details',
    'Deep Read Windows',
    'Entry Points & Parameters',
    'Object Dependencies',
    'Logic Decomposition Ledger',
    'Data Touch Map',
    'Key File & Field Logic',
    'Control Flow',
    'File I/O',
    'External Calls',
    'Error Handling',
    'Redundancy Candidate Notes',
    'TBDs & Blocking Status',
    'Review Checklist'
)
$CoreSidecarKeys = @(
    'source_index',
    'routine_index',
    'routine_logic_details',
    'routine_logic_details_yaml',
    'message_inventory_yaml'
)
$RoutineFinalSections = @(
    'Calculation Logic',
    'Validation Logic',
    'Exception Handling',
    'Message Inventory',
    'Routine Detail Index',
    'Routine Details'
)
$BatchCoreSections = @('Calculation Logic', 'Validation Logic', 'Exception Handling')
$BatchRequiredSections = @(
    'Calculation Logic',
    'Validation Logic',
    'Exception Handling',
    'Scope',
    'Batch Coverage Summary',
    'Message Inventory',
    'Routine Details'
)
$CoreOverviewHeadings = @{
    'Calculation Logic' = @('Calculation Logic Overview')
    'Validation Logic' = @('Validation Logic Overview')
    'Exception Handling' = @('Exception Flow Overview', 'Exception Handling Overview')
}
$RlogPattern = '\bRLOG-[A-Z0-9_#$@-]+-\d{3}\b'
$PlaceholderPatterns = @(
    '\bpending reader-oriented summary\b',
    '\bpending semantic deep-read\b',
    '\bpending semantic detail\b',
    '\bplaceholder content\b',
    '\bplaceholder\b',
    '\bnot-yet-deep-read\b',
    '\bnot deep-read\b'
)
$StaleGapPatterns = @(
    '\bRemaining routine deep-read gaps\b',
    '\bnot-yet-deep-read routines\b',
    '\bnot deep-read routines?\b'
)
$UnresolvedDescriptionSources = @(
    '',
    'unresolved',
    'missing_message_catalog_or_reference_pack',
    'missing_message_file',
    'pending_message_file'
)
$UnresolvedDescriptionStatuses = @(
    'unresolved',
    'unresolved_description',
    'pending_message_file'
)

function Validate-OrderedHeadings {
    param(
        [string]$Markdown,
        [string[]]$RequiredHeadings,
        [string]$ArtifactLabel,
        [bool]$H2Only = $false
    )

    $findings = New-Object System.Collections.ArrayList
    $positions = Get-HeadingMap $Markdown $H2Only
    $missing = @($RequiredHeadings | Where-Object { -not $positions.ContainsKey($_) })
    if ($missing.Count -gt 0) {
        $kind = if ($H2Only) { 'required ## headings' } else { 'required headings' }
        [void]$findings.Add("$ArtifactLabel missing ${kind}: " + ($missing -join ', '))
        return @($findings.ToArray())
    }
    $ordered = @($RequiredHeadings | ForEach-Object { [int]$positions[$_] })
    $sorted = @($ordered | Sort-Object)
    if (-not (Test-SequenceEqual $ordered $sorted)) {
        $kind = if ($H2Only) { 'required ## headings' } else { 'required headings' }
        [void]$findings.Add("$ArtifactLabel $kind are out of order")
    }
    return @($findings.ToArray())
}

function Validate-RequiredSections {
    param([string]$ProgramMarkdown)

    $positions = Get-HeadingMap $ProgramMarkdown $true
    $missing = @($RequiredProgramSections | Where-Object { -not $positions.ContainsKey($_) })
    if ($missing.Count -gt 0) {
        return @('program-analysis.md missing required sections: ' + ($missing -join ', '))
    }
    $ordered = @($RequiredProgramSections | ForEach-Object { [int]$positions[$_] })
    if (-not (Test-SequenceEqual $ordered @($ordered | Sort-Object))) {
        return @(
            'program-analysis.md required sections are out of order; follow ' +
            'references/output-contract.md File Structure'
        )
    }
    return @()
}

function Validate-RlogSequence {
    param([string]$Label, [string[]]$RlogIds)

    if ($RlogIds.Count -eq 0) { return @() }
    $numbers = New-Object System.Collections.ArrayList
    foreach ($rlogId in $RlogIds) {
        if ($rlogId -notmatch '-(\d{3})$') { return @("$Label contains malformed RLOG IDs") }
        [void]$numbers.Add([int]$Matches[1])
    }
    $expected = @(1..$numbers.Count)
    if (-not (Test-SequenceEqual @($numbers.ToArray()) $expected)) {
        return @("$Label RLOG IDs must be continuous and ordered from 001; found " + ($RlogIds -join ', '))
    }
    return @()
}

function Validate-RlogCoverage {
    param([string]$AnalysisDir)

    $yamlPath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.yaml'
    $markdownPath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.md'
    if (-not (Test-Path -LiteralPath $yamlPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $markdownPath -PathType Leaf)) { return @() }

    $yamlIds = @(Get-RlogIdsFromYaml $yamlPath)
    if ($yamlIds.Count -eq 0) {
        return @('routine-logic-details.yaml has no routine_logic_inventory.details[].detail_id values')
    }
    $findings = New-Object System.Collections.ArrayList
    foreach ($finding in @(Validate-RlogSequence 'routine-logic-details.yaml' $yamlIds)) { [void]$findings.Add($finding) }
    $markdownIds = @(Get-RlogIdsFromText (Read-Utf8Text $markdownPath))
    $missing = @(Compare-StringSets $yamlIds $markdownIds)
    if ($missing.Count -gt 0) {
        [void]$findings.Add('routine-logic-details.md missing RLOG IDs declared in YAML: ' + ($missing -join ', '))
    }
    return @($findings.ToArray())
}

function Get-MainRlogDetailHeadings {
    param([string]$ProgramMarkdown)

    $section = Get-H2SectionText $ProgramMarkdown 'Routine Logic Details'
    return @([regex]::Matches(
        $section,
        '(?im)^###\s+(RLOG-[A-Z0-9_#$@-]+-\d{3})\b'
    ) | ForEach-Object { $_.Groups[1].Value.ToUpperInvariant() })
}

function Validate-ProgramRlogCoverage {
    param([string]$ProgramMarkdown, [string]$AnalysisDir)

    $yamlPath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.yaml'
    if (-not (Test-Path -LiteralPath $yamlPath -PathType Leaf)) { return @() }
    $yamlIds = @(Get-RlogIdsFromYaml $yamlPath)
    if ($yamlIds.Count -eq 0) { return @() }

    $detailIds = @(Get-MainRlogDetailHeadings $ProgramMarkdown)
    if ($detailIds.Count -eq 0) {
        return @(
            'program-analysis.md Routine Logic Details missing RLOG detail headings declared in YAML: ' +
            ($yamlIds -join ', ')
        )
    }
    $findings = New-Object System.Collections.ArrayList
    $missing = @(Compare-StringSets $yamlIds $detailIds)
    $extra = @(Compare-StringSets $detailIds $yamlIds)
    if ($missing.Count -gt 0) {
        [void]$findings.Add(
            'program-analysis.md Routine Logic Details missing RLOG detail headings declared in YAML: ' +
            ($missing -join ', ')
        )
    }
    if ($extra.Count -gt 0) {
        [void]$findings.Add(
            'program-analysis.md Routine Logic Details contains extra RLOG detail headings not declared in YAML: ' +
            ($extra -join ', ')
        )
    }
    if (-not (Test-SequenceEqual $detailIds $yamlIds)) {
        [void]$findings.Add('program-analysis.md Routine Logic Details RLOG headings must match YAML order and count')
    }
    foreach ($finding in @(Validate-RlogSequence 'program-analysis.md Routine Logic Details' $detailIds)) {
        [void]$findings.Add($finding)
    }
    return @($findings.ToArray())
}

function Validate-CoreLogicRoutineIndexes {
    param([string]$ProgramMarkdown, [string]$AnalysisDir)

    $yamlPath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.yaml'
    if (-not (Test-Path -LiteralPath $yamlPath -PathType Leaf)) { return @() }
    $yamlIds = @(Get-RlogIdsFromYaml $yamlPath)
    if ($yamlIds.Count -eq 0) { return @() }

    $findings = New-Object System.Collections.ArrayList
    foreach ($sectionName in $BatchCoreSections) {
        $section = Get-H2SectionText $ProgramMarkdown $sectionName
        $indexHeading = "Routine Index For $sectionName"
        if (-not $section.Contains($indexHeading)) {
            [void]$findings.Add("program-analysis.md missing $indexHeading")
            continue
        }
        $indexIds = @(Get-RlogIdsFromText $section)
        $missing = @(Compare-StringSets $yamlIds $indexIds)
        if ($missing.Count -gt 0) {
            [void]$findings.Add("program-analysis.md $indexHeading missing RLOG rows declared in YAML: " + ($missing -join ', '))
        }
        if ($indexIds.Count -lt $yamlIds.Count) {
            [void]$findings.Add("program-analysis.md $indexHeading row count is $($indexIds.Count); expected at least $($yamlIds.Count)")
        }
    }
    return @($findings.ToArray())
}

function Validate-ProgramReadingSummaryQuality {
    param([string]$ProgramMarkdown)

    $section = Get-H2SectionText $ProgramMarkdown 'Program Reading Summary'
    if ($section -eq '') { return @() }
    $findings = New-Object System.Collections.ArrayList
    if ((Test-ReaderFirstPlaceholder $section) -or (Get-MeaningfulWordCount $section) -lt 20) {
        [void]$findings.Add(
            'reader-first golden gate: Program Reading Summary must contain ' +
            'reader-oriented processing context, not placeholder or pending text'
        )
    }
    $headers = @('Processing Layer', 'Main Routines', 'What To Understand First')
    $missing = @($headers | Where-Object { -not $section.Contains($_) })
    if ($missing.Count -gt 0) {
        [void]$findings.Add(
            'reader-first golden gate: Program Reading Summary missing processing-layer table headers: ' +
            ($missing -join ', ')
        )
        return @($findings.ToArray())
    }
    $usefulRows = 0
    foreach ($row in @(Get-MarkdownTableRows $section)) {
        $cells = @($row.Cells)
        if ($cells.Count -ge 3 -and $cells[0] -ne 'Processing Layer' -and
            -not (Test-ReaderFirstPlaceholder ($cells -join ' ')) -and
            (Get-MeaningfulWordCount $cells[2]) -ge 5) {
            $usefulRows++
        }
    }
    if ($usefulRows -eq 0) {
        [void]$findings.Add(
            'reader-first golden gate: Program Reading Summary needs at least one ' +
            'processing-layer row with reader-useful explanation'
        )
    }
    return @($findings.ToArray())
}

function Validate-CoreLogicReaderFirstQuality {
    param([string]$ProgramMarkdown, [string]$AnalysisDir)

    $yamlPath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.yaml'
    if (-not (Test-Path -LiteralPath $yamlPath -PathType Leaf)) { return @() }
    $yamlIds = @(Get-RlogIdsFromYaml $yamlPath)
    if ($yamlIds.Count -eq 0) { return @() }
    $findings = New-Object System.Collections.ArrayList

    foreach ($sectionName in $BatchCoreSections) {
        $section = Get-H2SectionText $ProgramMarkdown $sectionName
        if ($section -eq '') { continue }
        $indexHeading = "Routine Index For $sectionName"
        $indexPosition = $section.IndexOf($indexHeading, [StringComparison]::Ordinal)
        $overview = if ($indexPosition -ge 0) { $section.Substring(0, $indexPosition) } else { $section }
        if ((Test-ReaderFirstPlaceholder $overview) -or (Get-MeaningfulWordCount $overview) -lt 4) {
            [void]$findings.Add(
                "reader-first golden gate: program-analysis.md $sectionName must start " +
                'with reader-oriented overview content before the routine index'
            )
        }
        if ($indexPosition -lt 0) { continue }
        $indexText = $section.Substring($indexPosition + $indexHeading.Length)
        foreach ($rlogId in $yamlIds) {
            $row = @($indexText -split "`r?`n" | Where-Object { $_.ToUpperInvariant().Contains($rlogId) } | Select-Object -First 1)
            if ($row.Count -eq 0) { continue }
            $cells = @(Get-TableCellsOrLine $row[0])
            $detail = if ($cells.Count -ge 3) { $cells[$cells.Count - 1] } else { $row[0] }
            if ((Test-ReaderFirstPlaceholder $detail) -or (Get-MeaningfulWordCount $detail) -lt 3) {
                [void]$findings.Add(
                    "reader-first golden gate: program-analysis.md $indexHeading " +
                    "$rlogId needs reader-useful detail, not pending/placeholder text"
                )
            }
        }
    }
    return @($findings.ToArray())
}

function Validate-CoreLogicThemeSections {
    param([string]$ProgramMarkdown)

    $findings = New-Object System.Collections.ArrayList
    foreach ($sectionName in $BatchCoreSections) {
        $section = Get-H2SectionText $ProgramMarkdown $sectionName
        if ($section -eq '') { continue }
        $blocks = @(Get-H3Blocks $section)
        $aliases = @($CoreOverviewHeadings[$sectionName])
        $overview = @($blocks | Where-Object { $aliases -contains $_.Heading } | Select-Object -First 1)
        if ($overview.Count -eq 0) {
            [void]$findings.Add(
                "reader-first golden gate: program-analysis.md $sectionName missing themed overview heading: " +
                ($aliases -join ' or ')
            )
        }
        elseif ((Test-ReaderFirstPlaceholder $overview[0].Body) -or
            (Get-MeaningfulWordCount $overview[0].Body) -lt 8) {
            [void]$findings.Add(
                "reader-first golden gate: program-analysis.md $($overview[0].Heading) " +
                'needs reader-useful theme overview content'
            )
        }
        $indexHeading = "Routine Index For $sectionName"
        $indexBlock = @($blocks | Where-Object { $_.Heading -eq $indexHeading } | Select-Object -First 1)
        $indexPosition = if ($indexBlock.Count -gt 0) { $indexBlock[0].Position } else { $section.Length }
        $themes = @($blocks | Where-Object {
            $_.Position -lt $indexPosition -and $_.Heading -ne $indexHeading -and $aliases -notcontains $_.Heading
        })
        if ($themes.Count -eq 0) {
            [void]$findings.Add(
                "reader-first golden gate: program-analysis.md $sectionName needs at least " +
                'one reader-first theme subsection before the routine index'
            )
            continue
        }
        foreach ($theme in $themes) {
            if ((Test-ReaderFirstPlaceholder $theme.Body) -or (Get-MeaningfulWordCount $theme.Body) -lt 8) {
                [void]$findings.Add(
                    "reader-first golden gate: program-analysis.md $sectionName theme " +
                    "subsection $($theme.Heading) needs reader-useful detail"
                )
            }
        }
    }
    return @($findings.ToArray())
}

function Get-MainRlogDetailBlocks {
    param([string]$ProgramMarkdown)

    $section = Get-H2SectionText $ProgramMarkdown 'Routine Logic Details'
    $matches = @([regex]::Matches($section, '(?im)^###\s+(RLOG-[A-Z0-9_#$@-]+-\d{3})\b.*$'))
    $blocks = @{}
    for ($index = 0; $index -lt $matches.Count; $index++) {
        $start = $matches[$index].Index + $matches[$index].Length
        $end = if ($index + 1 -lt $matches.Count) { $matches[$index + 1].Index } else { $section.Length }
        $blocks[$matches[$index].Groups[1].Value.ToUpperInvariant()] = $section.Substring($start, $end - $start)
    }
    return $blocks
}

function Validate-MainRlogDetailQuality {
    param([string]$ProgramMarkdown, [string]$AnalysisDir)

    $yamlPath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.yaml'
    if (-not (Test-Path -LiteralPath $yamlPath -PathType Leaf)) { return @() }
    $yamlIds = @(Get-RlogIdsFromYaml $yamlPath)
    if ($yamlIds.Count -eq 0) { return @() }
    $blocks = Get-MainRlogDetailBlocks $ProgramMarkdown
    $findings = New-Object System.Collections.ArrayList
    foreach ($rlogId in $yamlIds) {
        if (-not $blocks.ContainsKey($rlogId)) { continue }
        $body = [string]$blocks[$rlogId]
        if ((Test-ReaderFirstPlaceholder $body) -or (Get-MeaningfulWordCount $body) -lt 12) {
            [void]$findings.Add(
                'reader-first golden gate: program-analysis.md Routine Logic Details ' +
                "$rlogId needs reader-useful detail, not pending/placeholder text"
            )
        }
    }
    return @($findings.ToArray())
}

function Validate-ReaderFirstGoldenGate {
    param([string]$ProgramMarkdown, [string]$AnalysisDir)

    $findings = New-Object System.Collections.ArrayList
    foreach ($finding in @(Validate-ProgramReadingSummaryQuality $ProgramMarkdown)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-CoreLogicReaderFirstQuality $ProgramMarkdown $AnalysisDir)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-CoreLogicThemeSections $ProgramMarkdown)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-MainRlogDetailQuality $ProgramMarkdown $AnalysisDir)) { [void]$findings.Add($finding) }
    return @($findings.ToArray())
}

function Validate-NoStaleGapWording {
    param([string]$ProgramMarkdown)

    $findings = New-Object System.Collections.ArrayList
    foreach ($pattern in $StaleGapPatterns) {
        if ([regex]::IsMatch($ProgramMarkdown, $pattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            [void]$findings.Add('program-analysis.md contains stale deep-read gap wording: ' + $pattern.Replace('\b', ''))
        }
    }
    return @($findings.ToArray())
}

function Test-LooksLikeSourceSnippet {
    param([string]$Text)

    $candidate = $Text.Replace('`', '').Trim()
    if ($candidate -eq '') { return $false }
    $fixed = '^\s*(?:[A-Z0-9_#$@]{1,10}\s+)?C\s{2,}.*\b(EXSR|BEGSR|ENDSR|CHAIN|SETLL|READE|READP?E?|READ|WRITE|UPDATE|DELETE|EXFMT|CALLP?|CALLPRC|EVAL|MOVE|MOVEL|Z-ADD|ADD|SUB|MULT|DIV|MONITOR|ON-ERROR|MONMSG|SNDPGMMSG)\b'
    $free = '^\s*(IF|WHEN|DOW|DOU|FOR|SELECT|MONITOR|ON-ERROR|RETURN|EVAL|EXEC\s+SQL|CHAIN|SETLL|READE|READP?E?|READ|WRITE|UPDATE|DELETE|CALLP?|EXSR|DCL-[A-Z]+)\b.+;\s*$'
    $sql = '^\s*(SELECT|UPDATE|INSERT|DELETE|MERGE)\s+.+\b(FROM|SET|INTO|WHERE)\b.*;?\s*$'
    return $candidate -match $fixed -or $candidate -match $free -or $candidate -match $sql
}

function Validate-BatchCoreNoSourceSnippets {
    param([string]$BatchText, [string]$BatchLabel)

    $findings = New-Object System.Collections.ArrayList
    foreach ($sectionName in $BatchCoreSections) {
        $section = Get-H2SectionText $BatchText $sectionName
        if ($section -eq '') { continue }
        if ($section.Contains('```')) {
            [void]$findings.Add("$BatchLabel $sectionName core logic must not contain fenced source/code blocks")
        }
        $lineNumber = 0
        foreach ($line in ($section -split "`r?`n")) {
            $lineNumber++
            foreach ($cell in @(Get-TableCellsOrLine $line)) {
                if (Test-LooksLikeSourceSnippet $cell) {
                    $preview = if ($cell.Length -gt 80) { $cell.Substring(0, 80) } else { $cell }
                    [void]$findings.Add(
                        "$BatchLabel $sectionName core logic contains a source-code-like snippet " +
                        "near section line ${lineNumber}: $preview"
                    )
                    break
                }
            }
        }
    }
    return @($findings.ToArray())
}

function Validate-RoutineDetailReviewSurfaces {
    param([string]$AnalysisDir)

    $batches = @(Get-BatchDetailFiles $AnalysisDir)
    if ($batches.Count -eq 0) { return @() }
    $findings = New-Object System.Collections.ArrayList
    $routinePath = Find-RoutineArtifactPath $AnalysisDir 'routine-logic-details.md'
    if ($routinePath) {
        foreach ($finding in @(Validate-OrderedHeadings (Read-Utf8Text $routinePath) $RoutineFinalSections 'routine-logic-details.md')) {
            [void]$findings.Add($finding)
        }
    }
    foreach ($batch in $batches) {
        $batchText = Read-Utf8Text $batch.FullName
        $batchLabel = $batch.FullName.Substring($AnalysisDir.TrimEnd('\', '/').Length).TrimStart('\', '/')
        $seedMatches = @(Get-SemanticSeedMatches $batchText)
        if ($seedMatches.Count -gt 0) {
            [void]$findings.Add(
                "$batchLabel still contains pending semantic deep-read content; " +
                'complete this retained batch before validation. Matched: ' +
                ($seedMatches -join ', ')
            )
        }
        foreach ($finding in @(Validate-OrderedHeadings $batchText $BatchRequiredSections $batchLabel $true)) {
            [void]$findings.Add($finding)
        }
        foreach ($finding in @(Validate-BatchCoreNoSourceSnippets $batchText $batchLabel)) {
            [void]$findings.Add($finding)
        }
        foreach ($finding in @(Get-PendingCoreTableFindings $batchText $batchLabel $BatchCoreSections)) {
            [void]$findings.Add($finding)
        }
        $windowCount = @(Get-BatchAssignedWindowIds $batchText).Count
        $routineSection = Get-H2SectionText $batchText 'Routine Details'
        $assignedIds = @(Get-BatchAssignedRlogIds $batchText)
        $scopeCount = [Math]::Max($windowCount, $assignedIds.Count)
        if ($scopeCount -gt 5) { [void]$findings.Add("$batchLabel contains more than 5 deep-read routines/windows ($scopeCount)") }
        if ($assignedIds.Count -eq 0) { $assignedIds = $null }
        foreach ($finding in @(Get-RlogSemanticQualityFindings $routineSection $assignedIds $batchLabel)) {
            [void]$findings.Add($finding)
        }
        $positions = Get-HeadingMap $batchText $false
        $allCore = $true
        foreach ($heading in $BatchCoreSections) {
            if (-not $positions.ContainsKey($heading)) { $allCore = $false }
        }
        if (-not $allCore) { continue }
        $minimumResult = $BatchCoreSections |
            ForEach-Object { [int]$positions[$_] } |
            Measure-Object -Minimum
        $firstCore = $minimumResult.Minimum
        $rlogMatch = [regex]::Match($batchText, $RlogPattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if ($rlogMatch.Success -and $firstCore -gt $rlogMatch.Index) {
            [void]$findings.Add(
                "$batchLabel must put Calculation/Validation/Exception core logic before per-routine RLOG detail"
            )
        }
    }
    return @($findings.ToArray())
}

function Validate-SidecarSet {
    param([string]$AnalysisDir)

    $summaryPath = Find-RoutineArtifactPath $AnalysisDir 'program-analysis-summary.yaml'
    if (-not (Test-Path -LiteralPath $summaryPath -PathType Leaf)) {
        return @('Missing required file: program-analysis-summary.yaml')
    }
    $entries = Get-SidecarEntries $summaryPath
    $findings = New-Object System.Collections.ArrayList
    foreach ($key in $CoreSidecarKeys) {
        if (-not $entries.ContainsKey($key)) {
            [void]$findings.Add("program-analysis-summary.yaml missing sidecar declaration: $key")
            continue
        }
        $entry = $entries[$key]
        if ($entry.status -ne 'present') {
            $status = if ([string]$entry.status -ne '') { $entry.status } else { 'missing' }
            [void]$findings.Add("core sidecar $key must have status present, found $status")
        }
        if ([string]$entry.path -ne '') {
            $sidecarPath = Join-Path $AnalysisDir ([string]$entry.path)
            if (-not (Test-Path -LiteralPath $sidecarPath -PathType Leaf)) {
                [void]$findings.Add("declared core sidecar file is missing: $($entry.path)")
            }
        }
    }
    foreach ($key in $entries.Keys) {
        $entry = $entries[$key]
        if (@('present', 'optional_triggered') -contains $entry.status -and [string]$entry.path -ne '') {
            $sidecarPath = Join-Path $AnalysisDir ([string]$entry.path)
            if (-not (Test-Path -LiteralPath $sidecarPath -PathType Leaf)) {
                [void]$findings.Add("declared sidecar $key is $($entry.status) but file is missing: $($entry.path)")
            }
        }
    }
    return @($findings.ToArray())
}

function Test-UnresolvedMessageDescription {
    param([hashtable]$Entry)

    $description = ''
    foreach ($key in @('short_description', 'message_description', 'description')) {
        if ($Entry.ContainsKey($key) -and [string]$Entry[$key] -ne '') {
            $description = ([string]$Entry[$key]).Trim().ToLowerInvariant()
            break
        }
    }
    $source = if ($Entry.ContainsKey('description_source')) {
        ([string]$Entry.description_source).Trim().ToLowerInvariant()
    } else { '' }
    $status = if ($Entry.ContainsKey('evidence_status')) {
        ([string]$Entry.evidence_status).Trim().ToLowerInvariant()
    } else { '' }
    return $description -eq 'unresolved - message description not available' -or
        $UnresolvedDescriptionSources -contains $source -or
        $UnresolvedDescriptionStatuses -contains $status
}

function Get-MessageCode {
    param([hashtable]$Entry)
    foreach ($key in @('message', 'message_code', 'code')) {
        if ($Entry.ContainsKey($key) -and [string]$Entry[$key] -ne '') { return [string]$Entry[$key] }
    }
    return ''
}

function Validate-MessageDescriptions {
    param([string]$AnalysisDir)

    $path = Find-RoutineArtifactPath $AnalysisDir 'message-inventory.yaml'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return @() }
    $entries = @(Get-MessageEntries $path)
    $unresolved = New-Object System.Collections.ArrayList
    foreach ($entry in $entries) {
        if (Test-UnresolvedMessageDescription $entry) {
            $code = Get-MessageCode $entry
            if ($code -eq '') { $code = 'unknown' }
            [void]$unresolved.Add($code)
        }
    }
    $codes = @(Get-UniqueSorted @($unresolved.ToArray()))
    if ($codes.Count -eq 0) { return @() }
    return @(
        'message descriptions unresolved for observed message/status/code values: ' +
        ($codes -join ', ') +
        '. Provide message file/catalog/reference pack, source literal/comment, ' +
        'runtime evidence, or SME-approved descriptions before final delivery.'
    )
}

function Validate-MessageInventorySync {
    param([string]$ProgramMarkdown, [string]$AnalysisDir)

    $path = Find-RoutineArtifactPath $AnalysisDir 'message-inventory.yaml'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return @() }
    $codes = New-Object System.Collections.ArrayList
    foreach ($entry in @(Get-MessageEntries $path)) {
        $code = Get-MessageCode $entry
        if ($code -ne '') { [void]$codes.Add($code) }
    }
    $observed = @(Get-UniqueSorted @($codes.ToArray()))
    if ($observed.Count -eq 0) { return @() }
    $section = Get-H2SectionText $ProgramMarkdown 'Message Inventory'
    $missing = @($observed | Where-Object { -not $section.Contains($_) })
    if ($missing.Count -eq 0) { return @() }
    return @(
        'program-analysis.md Message Inventory missing observed YAML message/code values: ' +
        ($missing -join ', ')
    )
}
function Find-ProgramAnalysisPath {
    param([string]$AnalysisDir, [string]$ExplicitPath)
    if ($ExplicitPath) { return $ExplicitPath }
    $defaultPath = Join-Path $AnalysisDir 'program-analysis.md'
    $hasDefault = Test-Path -LiteralPath $defaultPath -PathType Leaf
    $canonicalMatches = @(Get-PrefixedArtifactMatches $AnalysisDir 'program-analysis.md')
    $legacyMatches = @(Get-ChildItem -LiteralPath $AnalysisDir -Filter 'program-analysis-*.md' -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if (($hasDefault -and $canonicalMatches.Count -gt 0) -or $canonicalMatches.Count -gt 1 -or ($legacyMatches.Count -gt 0 -and ($hasDefault -or $canonicalMatches.Count -gt 0)) -or $legacyMatches.Count -gt 1) { return $null }
    if ($canonicalMatches.Count -eq 1) { return $canonicalMatches[0].FullName }
    if ($hasDefault) { return $defaultPath }
    if ($legacyMatches.Count -eq 1) { return $legacyMatches[0].FullName }
    return $null
}

function Validate-LargeExecutionPlanCoverage {
    param(
        [string]$AnalysisDir,
        [AllowNull()][string]$ExpectedSizeTier,
        [AllowNull()][string]$ExpectedSourceIndexSha256,
        [AllowNull()][string]$ExpectedExecutionPlanSha256
    )

    return Get-LargeExecutionPlanValidationResult $AnalysisDir $ExpectedSizeTier $ExpectedSourceIndexSha256 $ExpectedExecutionPlanSha256
}

function Invoke-ContractValidation {
    param(
        [string]$AnalysisDir,
        [string]$ProgramAnalysis,
        [AllowNull()][string]$ExpectedSizeTier,
        [AllowNull()][string]$ExpectedSourceIndexSha256,
        [AllowNull()][string]$ExpectedExecutionPlanSha256
    )
    $findings = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $AnalysisDir -PathType Container)) {
        return @("Analysis directory does not exist: $AnalysisDir")
    }
    foreach ($finding in @(Get-ProgramArtifactResolutionFindings $AnalysisDir $ProgramAnalysis)) { [void]$findings.Add($finding) }
    $programPath = Find-ProgramAnalysisPath $AnalysisDir $ProgramAnalysis
    if (-not $programPath -or -not (Test-Path -LiteralPath $programPath -PathType Leaf)) {
        [void]$findings.Add('Missing program-analysis.md or a single program-analysis-<OBJ-ID>.md')
    }
    else {
        $programMarkdown = Read-Utf8Text $programPath
        foreach ($finding in @(Validate-RequiredSections $programMarkdown)) { [void]$findings.Add($finding) }
        foreach ($finding in @(Validate-ProgramRlogCoverage $programMarkdown $AnalysisDir)) { [void]$findings.Add($finding) }
        foreach ($finding in @(Validate-CoreLogicRoutineIndexes $programMarkdown $AnalysisDir)) { [void]$findings.Add($finding) }
        foreach ($finding in @(Validate-ReaderFirstGoldenGate $programMarkdown $AnalysisDir)) { [void]$findings.Add($finding) }
        foreach ($finding in @(Validate-NoStaleGapWording $programMarkdown)) { [void]$findings.Add($finding) }
        foreach ($finding in @(Validate-MessageInventorySync $programMarkdown $AnalysisDir)) { [void]$findings.Add($finding) }
    }
    foreach ($finding in @(Validate-SidecarSet $AnalysisDir)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-RlogCoverage $AnalysisDir)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Get-RoutineSemanticCompletionFindings $AnalysisDir)) { [void]$findings.Add($finding) }
    $executionPlan = Validate-LargeExecutionPlanCoverage $AnalysisDir $ExpectedSizeTier $ExpectedSourceIndexSha256 $ExpectedExecutionPlanSha256
    foreach ($finding in @($executionPlan.Findings)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Get-BatchYamlSemanticCompletionFindings -AnalysisDir $AnalysisDir -BatchFiles @(Get-BatchDetailFiles $AnalysisDir) -ExpectedRlogIds @($executionPlan.PlannedRlogIds))) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-LargeProgramBatches $AnalysisDir $ExpectedSizeTier)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-RoutineDetailReviewSurfaces $AnalysisDir)) { [void]$findings.Add($finding) }
    foreach ($finding in @(Validate-MessageDescriptions $AnalysisDir)) { [void]$findings.Add($finding) }
    return @($findings.ToArray())
}
Export-ModuleMember -Function 'Invoke-ContractValidation'
