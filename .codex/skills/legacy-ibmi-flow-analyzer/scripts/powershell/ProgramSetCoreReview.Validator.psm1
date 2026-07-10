<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Native structural validator for program-set SME core reviews. This module is
compatible with Windows PowerShell 5.1 and uses no third-party modules.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'FlowYaml.psm1') -Force

$script:CoreSections = @('Calculation Logic', 'Validation Logic', 'Exception Handling', 'Message Inventory')
$script:ReaderFirstSections = @(
    'Program Set Reading Summary', 'Cross-Program Processing Overview',
    'Calculation Logic', 'Validation Logic', 'Exception Handling', 'Message Inventory',
    'Core Completeness Ledger', 'Sources', 'Run Profile', 'Source Inventory Cache'
)
$script:ForbiddenFlowSections = @(
    'Metadata', 'Trigger Context', 'Transaction Call Map', 'Nodes', 'Nodes (Programs in the Chain)',
    'Edges', 'Edges (Calls Between Nodes)', 'Common Dependencies', 'Cross-Program Data Flow',
    'Replay', 'Flow Replay Path', 'Lineage', 'Cross-Program Field Lineage', 'Persistence',
    'Flow Persistence Matrix', 'Branch Points', 'UI Surfaces', 'Error Propagation & Commit Boundaries',
    'Exception Propagation Chain', 'Capability Seeds', 'Business Capability Seeds',
    'Review Checklist', 'SME Checklist'
)
$script:RequiredCompactArtifacts = @(
    'program-analysis.md', 'program-analysis-summary.yaml', 'source-index.yaml',
    'routine-index.md', 'message-inventory.yaml', 'routine-logic-details.md',
    'routine-logic-details.yaml'
)
$script:PlaceholderPattern = '\b(todo|tbd|pending|placeholder|fill\s+in|to\s+be\s+completed|artifact\s+list|reader-first explanation|programs and main routines)\b'
$script:ArtifactReferencePattern = '\b(?:program-analysis(?:-summary)?|source-index|routine-index|message-inventory|routine-logic-details|file-io-inventory|field-mutation-matrix|sql-inventory)\.(?:md|ya?ml)\b'
$script:DetailReferencePattern = '\b(?:RLOG|MSG|LINEAGE|PERSIST|DATA|EXCHAIN|TBD|EV)-[A-Za-z0-9_-]+\b'

function Get-ReviewMapValue {
    param($Map, [Parameter(Mandatory = $true)][string]$Key, $Default = $null)
    if ($null -eq $Map) { return $Default }
    if ($Map -is [System.Collections.IDictionary]) {
        if ($Map.Contains($Key)) { return $Map[$Key] }
        return $Default
    }
    $property = $Map.PSObject.Properties[$Key]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Get-ReviewArtifactKey {
    param([string]$Filename)
    return $Filename.Replace('-', '_').Replace('.', '_')
}

function Get-ReviewH2Positions {
    param([Parameter(Mandatory = $true)][string]$Markdown)
    $positions = @{}
    foreach ($match in [regex]::Matches($Markdown, '^##\s+(.+?)\s*$', [Text.RegularExpressions.RegexOptions]::Multiline)) {
        $name = $match.Groups[1].Value.Trim()
        if (-not $positions.ContainsKey($name)) { $positions[$name] = $match.Index }
    }
    return $positions
}

function Get-ReviewH2Block {
    param([Parameter(Mandatory = $true)][string]$Markdown, [Parameter(Mandatory = $true)][string]$Section)
    $matches = @([regex]::Matches($Markdown, '^##\s+(.+?)\s*$', [Text.RegularExpressions.RegexOptions]::Multiline))
    for ($index = 0; $index -lt $matches.Count; $index++) {
        if ($matches[$index].Groups[1].Value.Trim() -ne $Section) { continue }
        $start = $matches[$index].Index + $matches[$index].Length
        $end = if ($index + 1 -lt $matches.Count) { $matches[$index + 1].Index } else { $Markdown.Length }
        return $Markdown.Substring($start, $end - $start)
    }
    return ''
}

function Test-ReviewTableSeparator {
    param([AllowEmptyString()][string]$Line)
    $trimmed = $Line.Trim()
    if (-not ($trimmed.StartsWith('|') -and $trimmed.EndsWith('|'))) { return $false }
    $cells = @($trimmed.Trim([char]'|').Split('|') | ForEach-Object { $_.Trim() })
    if ($cells.Count -eq 0) { return $false }
    foreach ($cell in $cells) { if ($cell -notmatch '^:?-{3,}:?$') { return $false } }
    return $true
}

function Get-ReviewTableLines {
    param([AllowEmptyString()][string]$Block)
    $result = New-Object System.Collections.Generic.List[object]
    $lines = @($Block -split "`r?`n")
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $trimmed = $lines[$index].Trim()
        if ($trimmed.StartsWith('|') -and $trimmed.EndsWith('|')) {
            $cells = @($trimmed.Trim([char]'|').Split('|') | ForEach-Object { $_.Trim() })
            $result.Add([ordered]@{ Index = $index; Cells = $cells; RawLines = $lines })
        }
    }
    return @($result.ToArray())
}

function Get-ReviewTableDataRows {
    param([AllowEmptyString()][string]$Block)
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($line in @(Get-ReviewTableLines $Block)) {
        if (Test-ReviewTableSeparator $line.RawLines[$line.Index]) { continue }
        $next = if ($line.Index + 1 -lt $line.RawLines.Count) { $line.RawLines[$line.Index + 1] } else { '' }
        if (Test-ReviewTableSeparator $next) { continue }
        # Wrap the cell array so pipeline enumeration cannot flatten one table
        # row into unrelated scalar outputs.
        $rows.Add([pscustomobject]@{ Cells = $line.Cells })
    }
    return @($rows.ToArray())
}

function Test-ReviewTableHeaders {
    param([AllowEmptyString()][string]$Block, [string[]]$RequiredHeaders)
    foreach ($line in @(Get-ReviewTableLines $Block)) {
        $normalized = @($line.Cells | ForEach-Object { $_.ToLowerInvariant() })
        $allFound = $true
        foreach ($header in $RequiredHeaders) {
            if ($normalized -notcontains $header.ToLowerInvariant()) { $allFound = $false; break }
        }
        if ($allFound) { return $true }
    }
    return $false
}

function Get-ReviewRowsByFirstColumn {
    param([AllowEmptyString()][string]$Block)
    $rows = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    foreach ($line in @(Get-ReviewTableLines $Block)) {
        $cells = $line.Cells
        if ($cells.Count -eq 0 -or -not $cells[0] -or $cells[0] -eq 'Program') { continue }
        if ($cells[0] -match '^-+$') { continue }
        $rows[$cells[0]] = $cells
    }
    return $rows
}

function Remove-ReviewMarkdownComments {
    param([AllowEmptyString()][string]$Block)
    return [regex]::Replace($Block, '<!--.*?-->', '', [Text.RegularExpressions.RegexOptions]::Singleline)
}

function Get-ReviewProseAndTableDetail {
    param([AllowEmptyString()][string]$Block)
    $clean = Remove-ReviewMarkdownComments $Block
    $lines = @($clean -split "`r?`n")
    $details = New-Object System.Collections.Generic.List[string]
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $trimmed = $lines[$index].Trim()
        if (-not $trimmed) { continue }
        if ($trimmed.StartsWith('|') -and $trimmed.EndsWith('|')) {
            if (Test-ReviewTableSeparator $trimmed) { continue }
            $next = if ($index + 1 -lt $lines.Count) { $lines[$index + 1] } else { '' }
            if (Test-ReviewTableSeparator $next) { continue }
            $cells = @($trimmed.Trim([char]'|').Split('|') | ForEach-Object { $_.Trim() })
            $details.Add($cells -join ' ')
        }
        else { $details.Add($trimmed) }
    }
    return $details -join "`n"
}

function Get-ReviewReaderWords {
    param([AllowEmptyString()][string]$Text)
    $withoutRefs = [regex]::Replace([regex]::Replace($Text, $script:ArtifactReferencePattern, ' ', 'IgnoreCase'), $script:DetailReferencePattern, ' ')
    $withoutNoise = [regex]::Replace($withoutRefs, '\b(?:confirmed|inferred|unresolved|present|missing|n/a)\b', ' ', 'IgnoreCase')
    return @([regex]::Matches($withoutNoise, '[A-Za-z][A-Za-z0-9_-]{2,}') | ForEach-Object { $_.Value })
}

function Test-ReviewReaderUsefulDetail {
    param([AllowEmptyString()][string]$Block, [int]$MinimumWords = 18)
    $detail = Get-ReviewProseAndTableDetail $Block
    if (-not $detail.Trim()) { return $false }
    if ([regex]::IsMatch($detail, $script:PlaceholderPattern, 'IgnoreCase')) { return $false }
    return @(Get-ReviewReaderWords $detail).Count -ge $MinimumWords
}

function Test-ReviewPlaceholderCell {
    param([AllowEmptyString()][string]$Value)
    $trimmed = $Value.Trim(); $lowered = $trimmed.ToLowerInvariant()
    if (-not $trimmed -or $trimmed -match '^\[[^\]]+\]$') { return $true }
    if ($lowered -in @('todo', 'tbd', 'pending', 'placeholder', 'n/a')) { return $true }
    foreach ($marker in @('reader-first explanation', 'programs and main routines', 'fill in', 'to be completed')) {
        if ($lowered.Contains($marker)) { return $true }
    }
    return $false
}

function Test-FlowCoreReviewManifest {
    param($Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $programsValue = Get-ReviewMapValue $Manifest 'programs'
    $programs = @($programsValue)
    if ($null -eq $programsValue -or $programs.Count -eq 0) { return @('manifest has no programs[] entries') }
    $runProfile = Get-ReviewMapValue $Manifest 'run_profile' ([ordered]@{})
    $repoMode = [string](Get-ReviewMapValue $runProfile 'artifact_repo_mode' 'current_run')
    # Preserve case-sensitive identity for profiles that intentionally keep
    # program-name case instead of normalizing it to uppercase.
    $byName = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    foreach ($entry in $programs) {
        $name = [string](Get-ReviewMapValue $entry 'normalized_name' '')
        if (-not $name) { $findings.Add('program entry missing normalized_name'); continue }
        if (-not $byName.ContainsKey($name)) { $byName[$name] = New-Object System.Collections.Generic.List[object] }
        $byName[$name].Add($entry)
        $resolution = Get-ReviewMapValue $entry 'run_resolution'
        if ($null -eq $resolution -and $null -ne (Get-ReviewMapValue $entry 'central_lookup_result')) {
            $findings.Add("$name uses legacy central_lookup_result; rebuild the manifest with the no-cross-run-reuse builder")
            continue
        }
        if ($resolution -notin @('analyzed_this_run', 'reused_same_run', 'reused_artifact_repo', 'pending_source', 'blocked_missing_source')) { $findings.Add("$name has invalid run_resolution: $resolution") }
        $artifactRoot = Get-ReviewMapValue $entry 'artifact_root'
        $artifactSource = Get-ReviewMapValue $entry 'artifact_source'
        if ($resolution -in @('analyzed_this_run', 'reused_same_run', 'reused_artifact_repo') -and -not $artifactRoot) { $findings.Add("$name $resolution missing artifact_root") }
        if ($resolution -eq 'analyzed_this_run' -and $artifactSource -ne 'delivery_working_branch') { $findings.Add("$name analyzed_this_run must use artifact_source delivery_working_branch") }
        if ($resolution -eq 'reused_same_run' -and $artifactSource -ne 'delivery_working_branch') { $findings.Add("$name reused_same_run has invalid artifact_source") }
        if ($resolution -eq 'reused_artifact_repo') {
            if ($repoMode -ne 'approved_document_repo') { $findings.Add("$name reused_artifact_repo requires artifact_repo_mode approved_document_repo") }
            if ($artifactSource -ne 'approved_document_repo') { $findings.Add("$name reused_artifact_repo must use artifact_source approved_document_repo") }
        }
        if ($resolution -in @('pending_source', 'blocked_missing_source') -and $artifactRoot) { $findings.Add("$name $resolution must not have artifact_root") }
        if ($resolution -in @('analyzed_this_run', 'reused_same_run', 'reused_artifact_repo')) {
            $compact = Get-ReviewMapValue $entry 'compact_artifacts' ([ordered]@{})
            $missing = New-Object System.Collections.Generic.List[string]
            foreach ($filename in $script:RequiredCompactArtifacts) {
                $status = Get-ReviewMapValue (Get-ReviewMapValue $compact (Get-ReviewArtifactKey $filename) ([ordered]@{})) 'status' 'missing'
                if ($status -ne 'present') { $missing.Add($filename) }
            }
            if ($missing.Count) { $findings.Add("$name $resolution missing required compact artifacts: " + ($missing.ToArray() -join ', ')) }
        }
    }
    foreach ($name in $byName.Keys) {
        $duplicates = @($byName[$name].ToArray())
        if ($duplicates.Count -le 1) { continue }
        $first = $duplicates[0]; $firstRoot = Get-ReviewMapValue $first 'artifact_root'; $firstResolution = Get-ReviewMapValue $first 'run_resolution'
        foreach ($duplicate in $duplicates[1..($duplicates.Count - 1)]) {
            $resolution = Get-ReviewMapValue $duplicate 'run_resolution'; $artifactRoot = Get-ReviewMapValue $duplicate 'artifact_root'
            if ($firstRoot) {
                $expected = if ($firstResolution -eq 'reused_artifact_repo') { 'reused_artifact_repo' } else { 'reused_same_run' }
                if ($resolution -ne $expected) { $findings.Add("$name duplicate with artifact must use $expected") }
                if ($artifactRoot -ne $firstRoot) { $findings.Add("$name duplicate artifact_root must match the first artifact") }
            }
            elseif ($firstResolution -in @('pending_source', 'blocked_missing_source')) {
                if ($resolution -notin @('pending_source', 'blocked_missing_source')) { $findings.Add("$name duplicate without a current-run artifact must remain pending/blocked") }
                if ($artifactRoot) { $findings.Add("$name duplicate pending/blocked entry must not have artifact_root") }
            }
        }
    }
    return @($findings.ToArray())
}

function Test-FlowCoreReviewMarkdown {
    param([Parameter(Mandatory = $true)][string]$Markdown, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $positions = Get-ReviewH2Positions $Markdown
    $missingSections = @($script:ReaderFirstSections | Where-Object { -not $positions.ContainsKey($_) })
    if ($missingSections.Count) { $findings.Add('program-set review missing required reader-first ## sections: ' + ($missingSections -join ', ')) }
    else {
        $ordered = @($script:ReaderFirstSections | ForEach-Object { [int]$positions[$_] })
        $sorted = @($ordered | Sort-Object)
        if (($ordered -join ',') -ne ($sorted -join ',')) { $findings.Add('program-set review reader-first core sections must appear before audit/control sections') }
    }
    foreach ($section in $script:ForbiddenFlowSections) {
        if ([regex]::IsMatch($Markdown, '^##\s+' + [regex]::Escape($section) + '\s*$', 'Multiline')) { $findings.Add("program-set review contains forbidden full-flow section: $section") }
    }
    $summaryBlock = Get-ReviewH2Block $Markdown 'Program Set Reading Summary'
    if ($summaryBlock) {
        $summaryDetail = Get-ReviewProseAndTableDetail $summaryBlock
        $layerTerms = 0
        foreach ($term in @('entry', 'dispatch', 'calculation', 'validation', 'exception', 'message', 'persistence', 'finalization')) { if ([regex]::IsMatch($summaryDetail, "\b$term\b", 'IgnoreCase')) { $layerTerms++ } }
        $hasStatus = [regex]::IsMatch($summaryDetail, '\b(standalone_exploratory|chain_ready|draft)\b', 'IgnoreCase')
        if (-not (Test-ReviewReaderUsefulDetail $summaryBlock 25) -or $layerTerms -lt 2 -or -not $hasStatus -or [regex]::IsMatch($summaryDetail, $script:ArtifactReferencePattern, 'IgnoreCase')) {
            $findings.Add('Program Set Reading Summary is placeholder/artifact-only or missing reader-useful flow context')
        }
    }
    $overview = Get-ReviewH2Block $Markdown 'Cross-Program Processing Overview'
    if ($overview) {
        if (-not (Test-ReviewTableHeaders $overview @('Processing Layer', 'Programs / Main Routines', 'What To Understand First'))) { $findings.Add('Cross-Program Processing Overview missing required table headers') }
        $rows = @(Get-ReviewTableDataRows $overview)
        if ($rows.Count -lt 4) { $findings.Add('Cross-Program Processing Overview must include processing-layer rows') }
        foreach ($rowRecord in $rows) {
            $row = @($rowRecord.Cells)
            if ($row.Count -lt 3 -or (Test-ReviewPlaceholderCell $row[0]) -or (Test-ReviewPlaceholderCell $row[1]) -or (Test-ReviewPlaceholderCell $row[2])) { $findings.Add('Cross-Program Processing Overview has placeholder processing-layer detail'); break }
        }
    }
    foreach ($section in $script:CoreSections) {
        $block = Get-ReviewH2Block $Markdown $section
        if ($block -and -not (Test-ReviewReaderUsefulDetail $block)) { $findings.Add("$section lacks reader-useful detail") }
    }
    $sourceRows = Get-ReviewRowsByFirstColumn (Get-ReviewH2Block $Markdown 'Sources')
    $ledgerRows = Get-ReviewRowsByFirstColumn (Get-ReviewH2Block $Markdown 'Core Completeness Ledger')
    foreach ($entry in @(Get-ReviewMapValue $Manifest 'programs' @())) {
        $program = [string](Get-ReviewMapValue $entry 'normalized_name' '')
        if (-not $program) { continue }
        if (-not $sourceRows.ContainsKey($program)) { $findings.Add("$program missing from Sources table") }
        if (-not $ledgerRows.ContainsKey($program)) { $findings.Add("$program missing from Core Completeness Ledger") }
        $resolution = [string](Get-ReviewMapValue $entry 'run_resolution' '')
        if ($resolution -and $ledgerRows.ContainsKey($program) -and $ledgerRows[$program] -notcontains $resolution) { $findings.Add("$program run_resolution $resolution missing from Core Completeness Ledger") }
    }
    return @($findings.ToArray())
}

function Invoke-FlowCoreReviewValidation {
    param([Parameter(Mandatory = $true)][string]$ManifestPath, [Parameter(Mandatory = $true)][string]$ReviewPath)
    $manifest = Read-FlowYamlFile $ManifestPath
    if ($manifest -isnot [System.Collections.IDictionary]) { return @('manifest is not a YAML mapping') }
    $findings = New-Object System.Collections.Generic.List[string]
    foreach ($finding in @(Test-FlowCoreReviewManifest $manifest)) { $findings.Add($finding) }
    if (-not (Test-Path -LiteralPath $ReviewPath -PathType Leaf)) {
        $findings.Add("missing review artifact: $ReviewPath")
        return @($findings.ToArray())
    }
    $markdown = [IO.File]::ReadAllText($ReviewPath)
    foreach ($finding in @(Test-FlowCoreReviewMarkdown $markdown $manifest)) { $findings.Add($finding) }
    return @($findings.ToArray())
}

Export-ModuleMember -Function Invoke-FlowCoreReviewValidation
