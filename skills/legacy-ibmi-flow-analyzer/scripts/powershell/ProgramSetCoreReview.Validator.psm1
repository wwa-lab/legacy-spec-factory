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
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Markdown.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Reconciliation.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Safety.psm1') -Force

$script:CoreReadingSections = @(
    'Program Set Reading Summary', 'Cross-Program Processing Overview',
    'Calculation Logic', 'Validation Logic', 'Exception Handling'
)
$script:CoreSections = @('Calculation Logic', 'Validation Logic', 'Exception Handling', 'Message Inventory', 'Message Coverage Control')
$script:AuditSections = @('Core Completeness Ledger', 'Coverage Reconciliation', 'Sources', 'Run Profile', 'Source Inventory Cache')
$script:ForbiddenFlowSections = @(
    'Metadata', 'Trigger Context', 'Trigger Inventory', 'Transaction Call Map', 'Nodes', 'Nodes (Programs in the Chain)',
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
$script:PlaceholderPattern = '(?m)^\s*(?:todo|tbd|placeholder|n/a)\s*[.!]?\s*$|\b(?:placeholder\s+(?:content|text|artifact\s+list)|fill\s+in|to\s+be\s+completed|artifact\s+list|reader-first explanation|programs and main routines)\b|^\s*(?:todo|tbd|placeholder)\s*[:\-]\s*(?:add|complete|describe|document|explain|fill|replace|write)\b.*$'
$script:ArtifactReferencePattern = '\b(?:program-analysis(?:-summary)?|source-index|routine-index|message-inventory|routine-logic-details|file-io-inventory|field-mutation-matrix|sql-inventory)\.(?:md|ya?ml)\b'
$script:DetailReferencePattern = '\b(?:RLOG|MSG|LINEAGE|PERSIST|DATA|EXCHAIN|TBD|EV)-[A-Za-z0-9_-]+\b'
$script:ForbiddenLegacyTerms = @('Program-Level SME Core Review', 'Program-Set Logic Rollup')

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
    param([AllowEmptyString()][string]$Line, [int]$ExpectedCellCount = 0)
    return Test-FlowMarkdownTableSeparator $Line $ExpectedCellCount
}

function Get-ReviewTableLines {
    param([AllowEmptyString()][string]$Block)
    $result = New-Object System.Collections.Generic.List[object]
    $lines = @($Block -split "`r?`n")
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $trimmed = $lines[$index].Trim()
        if ($trimmed.StartsWith('|') -and $trimmed.EndsWith('|')) {
            $cells = @(Split-FlowMarkdownTableRow $trimmed)
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
        $next = if ($line.Index + 1 -lt $line.RawLines.Count) { $line.RawLines[$line.Index + 1] } else { '' }
        if ($allFound -and (Test-ReviewTableSeparator $next ([int]$line.Cells.Count))) { return $true }
    }
    return $false
}

function Get-ReviewMatchingHeaderCells {
    param([AllowEmptyString()][string]$Block, [string[]]$RequiredHeaders)
    foreach ($line in @(Get-ReviewTableLines $Block)) {
        $normalized = @($line.Cells | ForEach-Object { $_.ToLowerInvariant() })
        $allFound = $true
        foreach ($header in $RequiredHeaders) {
            if ($normalized -notcontains $header.ToLowerInvariant()) { $allFound = $false; break }
        }
        $next = if ($line.Index + 1 -lt $line.RawLines.Count) { $line.RawLines[$line.Index + 1] } else { '' }
        if ($allFound -and (Test-ReviewTableSeparator $next ([int]$line.Cells.Count))) { return @($line.Cells) }
    }
    return @()
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
    return Remove-FlowHtmlComments $Block
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
            $cells = @(Split-FlowMarkdownTableRow $trimmed)
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
    if ($lowered -in @('todo', 'tbd', 'placeholder', 'n/a')) { return $true }
    foreach ($marker in @('placeholder content', 'placeholder text', 'reader-first explanation', 'programs and main routines', 'fill in', 'to be completed')) {
        if ($lowered.Contains($marker)) { return $true }
    }
    return $false
}

function ConvertFrom-ReviewFrontMatterScalar {
    param([AllowEmptyString()][string]$Value)
    $trimmed = $Value.Trim()
    if (($trimmed.StartsWith("'") -and $trimmed.EndsWith("'")) -or ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"'))) {
        return $trimmed.Substring(1, $trimmed.Length - 2)
    }
    return $trimmed
}

function Get-FlowReviewFrontMatter {
    param([Parameter(Mandatory = $true)][string]$Markdown)
    $match = [regex]::Match($Markdown, '\A---\r?\n(?<body>.*?)\r?\n---(?:\r?\n|\z)', 'Singleline')
    if (-not $match.Success) { return $null }
    $body = $match.Groups['body'].Value
    $seenKeys = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($line in @($body -split "`r?`n")) {
        $keyMatch = [regex]::Match($line, '^(?<key>[A-Za-z0-9_.-]+|''[^'']+''|"[^"]+")\s*:')
        if (-not $keyMatch.Success) { continue }
        $key = ConvertFrom-ReviewFrontMatterScalar $keyMatch.Groups['key'].Value
        if (-not $seenKeys.Add($key)) { return $null }
    }
    $metadata = [ordered]@{}
    foreach ($key in @('document_id', 'flow_slug', 'program_set_slug', 'review_status', 'artifact_version')) {
        $scalar = [regex]::Match($body, '(?m)^' + [regex]::Escape($key) + ':\s*(.+?)\s*$')
        if ($scalar.Success) { $metadata[$key] = ConvertFrom-ReviewFrontMatterScalar $scalar.Groups[1].Value }
    }
    $programs = New-Object System.Collections.Generic.List[string]
    $inline = [regex]::Match($body, '(?m)^programs:\s*\[(.*?)\]\s*$')
    if ($inline.Success) {
        foreach ($item in @($inline.Groups[1].Value.Split(','))) {
            $value = ConvertFrom-ReviewFrontMatterScalar $item
            if ($value) { $programs.Add($value) }
        }
    }
    else {
        $block = [regex]::Match($body, '(?ms)^programs:\s*\r?\n(?<items>(?:\s*-\s*.+(?:\r?\n|\z))+)')
        if ($block.Success) {
            foreach ($item in @([regex]::Matches($block.Groups['items'].Value, '(?m)^\s*-\s*(.+?)\s*$'))) {
                $value = ConvertFrom-ReviewFrontMatterScalar $item.Groups[1].Value
                if ($value) { $programs.Add($value) }
            }
        }
    }
    $metadata['programs'] = @($programs.ToArray())
    return $metadata
}

function Test-FlowReviewIdentity {
    param([Parameter(Mandatory = $true)][string]$Markdown, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $metadata = Get-FlowReviewFrontMatter $Markdown
    if ($null -eq $metadata) { return @('final review missing valid YAML front matter') }
    foreach ($key in @('document_id', 'flow_slug', 'program_set_slug', 'artifact_version')) {
        $expected = if ($key -eq 'document_id') { [string](Get-ReviewMapValue $Manifest $key (Get-ReviewMapValue $Manifest 'review_id' '')) } else { [string](Get-ReviewMapValue $Manifest $key '') }
        if ([string](Get-ReviewMapValue $metadata $key '') -ne $expected) { $findings.Add("final review front matter $key does not match manifest") }
    }
    if ([string](Get-ReviewMapValue $metadata 'review_status' '') -ne 'complete_exploratory') { $findings.Add('final review front matter review_status must be complete_exploratory') }
    $expectedPrograms = @(@(Get-ReviewMapValue $Manifest 'programs' @()) | ForEach-Object { [string](Get-ReviewMapValue $_ 'normalized_name' '') } | Where-Object { $_ } | Sort-Object -Unique)
    $actualPrograms = @(@(Get-ReviewMapValue $metadata 'programs' @()) | ForEach-Object { [string]$_ } | Where-Object { $_ } | Sort-Object -Unique)
    if (($expectedPrograms -join "`n") -cne ($actualPrograms -join "`n")) { $findings.Add('final review front matter programs do not match manifest') }
    $folderSlug = [string](Get-ReviewMapValue $Manifest 'folder_slug' '')
    foreach ($finding in @(Get-FlowH1IdentityFindings $Markdown $folderSlug)) { $findings.Add($finding) }
    return @($findings.ToArray())
}

function Test-FlowCoreReviewManifest {
    param($Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $folderSlug = [string](Get-ReviewMapValue $Manifest 'folder_slug' '')
    $canonical = [string](Get-ReviewMapValue $Manifest 'canonical_filename' '')
    $expectedCanonical = if ($folderSlug) { "$folderSlug--sme-core-review.md" } else { '' }
    if ($canonical -and $expectedCanonical -and $canonical -ne $expectedCanonical) { $findings.Add("manifest canonical_filename must be $expectedCanonical") }
    if ($canonical -eq 'program-set-sme-core-review.md') { $findings.Add('manifest must use the unique <folder_slug>--sme-core-review.md filename') }
    $reviewStatus = [string](Get-ReviewMapValue $Manifest 'review_status' '')
    if ($reviewStatus -and $reviewStatus -notin @('ready_for_synthesis', 'blocked_artifact_readiness', 'complete_exploratory')) { $findings.Add("manifest has invalid review_status: $reviewStatus") }
    if ($reviewStatus -eq 'blocked_artifact_readiness') { $findings.Add('formal review validation is blocked until every program artifact is ready') }
    $schemaVersion = [string](Get-ReviewMapValue $Manifest 'schema_version' '')
    if ($schemaVersion -ne '0.4') { $findings.Add('formal review validation requires manifest schema_version 0.4') }
    foreach ($versionRequirement in @(
        [pscustomobject]@{ Field = 'generator_version'; Expected = '0.4.0' },
        [pscustomobject]@{ Field = 'template_version'; Expected = '0.4.0' },
        [pscustomobject]@{ Field = 'artifact_version'; Expected = '0.4' }
    )) {
        if ([string](Get-ReviewMapValue $Manifest $versionRequirement.Field '') -ne $versionRequirement.Expected) { $findings.Add("formal review validation requires manifest $($versionRequirement.Field) $($versionRequirement.Expected)") }
    }
    if ($schemaVersion -eq '0.4') {
        $artifactReadiness = [string](Get-ReviewMapValue $Manifest 'artifact_readiness' '')
        $mergeCoverage = [string](Get-ReviewMapValue $Manifest 'merge_coverage' '')
        if ($artifactReadiness -notin @('ready', 'not_ready')) { $findings.Add('manifest artifact_readiness must be ready or not_ready') }
        if ($mergeCoverage -notin @('pending', 'blocked', 'complete')) { $findings.Add('manifest merge_coverage must be pending, blocked, or complete') }
        $expected = switch ($reviewStatus) {
            'ready_for_synthesis' { @('ready', 'pending') }
            'blocked_artifact_readiness' { @('not_ready', 'blocked') }
            'complete_exploratory' { @('ready', 'complete') }
            default { @() }
        }
        if ($expected.Count -eq 2 -and ($artifactReadiness -ne $expected[0] -or $mergeCoverage -ne $expected[1])) {
            $findings.Add("manifest artifact_readiness/merge_coverage do not match review_status $reviewStatus")
        }
    }
    foreach ($key in @('review_id', 'document_id', 'review_slug', 'flow_slug', 'program_set_slug', 'folder_slug')) {
        $value = [string](Get-ReviewMapValue $Manifest $key '')
        if ($null -ne (Get-ReviewMapValue $Manifest $key $null) -and -not $value.Trim()) { $findings.Add("manifest $key must not be empty") }
    }
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
        $readiness = Get-ReviewMapValue $entry 'artifact_readiness' ([ordered]@{})
        $readinessStatus = [string](Get-ReviewMapValue $readiness 'status' '')
        if ($readinessStatus -notin @('ready', 'not_ready')) { $findings.Add("$name has invalid artifact_readiness.status: $readinessStatus") }
        if ($reviewStatus -in @('ready_for_synthesis', 'complete_exploratory') -and $readinessStatus -ne 'ready') { $findings.Add("$name must be artifact-ready before synthesis or completion") }
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
    $Markdown = Remove-FlowHtmlComments $Markdown
    $profile = Get-ReviewMapValue $Manifest 'core_review_profile' ([ordered]@{})
    $requiredSections = @($script:CoreReadingSections)
    if ([bool](Get-ReviewMapValue $profile 'include_message_inventory' $false)) { $requiredSections += 'Message Inventory' }
    if ([bool](Get-ReviewMapValue $profile 'include_audit_sections' $true)) {
        if ([bool](Get-ReviewMapValue $profile 'include_message_inventory' $false)) { $requiredSections += $script:AuditSections }
        else { $requiredSections += @('Core Completeness Ledger', 'Coverage Reconciliation', 'Message Coverage Control', 'Sources', 'Run Profile', 'Source Inventory Cache') }
    }
    foreach ($finding in @(Get-FlowDuplicateH2Findings $Markdown ($requiredSections + $script:CoreReadingSections + $script:CoreSections + $script:AuditSections))) { $findings.Add($finding) }
    $positions = Get-ReviewH2Positions $Markdown
    $missingSections = @($requiredSections | Where-Object { -not $positions.ContainsKey($_) })
    if ($missingSections.Count) { $findings.Add('program-set review missing required reader-first ## sections: ' + ($missingSections -join ', ')) }
    else {
        $ordered = @($requiredSections | ForEach-Object { [int]$positions[$_] })
        $sorted = @($ordered | Sort-Object)
        if (($ordered -join ',') -ne ($sorted -join ',')) { $findings.Add('program-set review reader-first core sections must appear before audit/control sections') }
    }
    foreach ($finding in @(Get-FlowForbiddenHeadingFindings $Markdown $script:ForbiddenFlowSections)) { $findings.Add($finding) }
    foreach ($finding in @(Get-FlowProhibitedContentFindings $Markdown)) { $findings.Add($finding) }
    foreach ($term in $script:ForbiddenLegacyTerms) {
        if ([regex]::IsMatch($Markdown, '\b' + [regex]::Escape($term) + '\b', 'IgnoreCase')) { $findings.Add("program-set review contains forbidden legacy form: $term") }
    }
    foreach ($finding in @(Get-FlowProgramOrderFindings $Markdown)) { $findings.Add($finding) }
    foreach ($finding in @(Get-FlowUnmappedCoreProseFindings $Markdown $Manifest)) { $findings.Add($finding) }
    $summaryBlock = Get-ReviewH2Block $Markdown 'Program Set Reading Summary'
    if ($summaryBlock) {
        $summaryDetail = Get-ReviewProseAndTableDetail $summaryBlock
        $layerTerms = 0
        foreach ($term in @('calculation', 'validation', 'exception', 'message', 'outcome')) { if ([regex]::IsMatch($summaryDetail, "\b$term\b", 'IgnoreCase')) { $layerTerms++ } }
        $hasStatus = [regex]::IsMatch($summaryDetail, '\b(complete|complete_exploratory|standalone_exploratory|ready_for_synthesis)\b', 'IgnoreCase')
        if (-not (Test-ReviewReaderUsefulDetail $summaryBlock 25) -or $layerTerms -lt 2 -or -not $hasStatus -or [regex]::IsMatch($summaryDetail, $script:ArtifactReferencePattern, 'IgnoreCase')) {
            $findings.Add('Program Set Reading Summary is placeholder/artifact-only or missing reader-useful program-set context')
        }
    }
    $visibleMarkdown = Remove-FlowHtmlComments $Markdown
    $overview = Get-ReviewH2Block $visibleMarkdown 'Cross-Program Processing Overview'
    if ($overview) {
        if (-not (Test-ReviewTableHeaders $overview @('Processing Layer', 'Programs / Main Routines', 'What To Understand First', 'Review Row ID', 'Source Fact Refs'))) { $findings.Add('Cross-Program Processing Overview missing required table headers') }
        $rows = @(Get-ReviewTableDataRows $overview)
        if ($rows.Count -lt 4) { $findings.Add('Cross-Program Processing Overview must include processing-layer rows') }
        foreach ($rowRecord in $rows) {
            $row = @($rowRecord.Cells)
            if ($row.Count -lt 5 -or @($row[0..4] | Where-Object { Test-ReviewPlaceholderCell $_ }).Count) { $findings.Add('Cross-Program Processing Overview has placeholder processing-layer detail'); break }
        }
        $overviewProse = (@($overview -split "`r?`n" | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('|') -and -not $_.Trim().StartsWith('#') }) -join ' ')
        if ([regex]::IsMatch($overviewProse, '\b[A-Z@#$][A-Z0-9@#$]*\s+(?:calls?|invokes?)\s+[A-Z@#$][A-Z0-9@#$]*\b|\b(?:always\s+)?executes?\s+(?:before|after|in\s+that\s+order)\b', 'IgnoreCase')) { $findings.Add('Cross-Program Processing Overview prose contains an untracked call/sequence claim') }
    }
    $sectionHeaders = [ordered]@{
        'Calculation Logic' = @('Calculation / Assignment', 'Program', 'Routine', 'Target Field / Carrier', 'Source Operands / Carriers', 'Guard / Branch', 'Effect', 'Supporting Detail', 'Evidence Status', 'Review Row ID', 'Source Fact Refs')
        'Validation Logic' = @('Message / Status / Outcome', 'Description', 'Program', 'Routine', 'Condition / Evidence', 'Carrier / Destination', 'Effect', 'Supporting Detail', 'Evidence Status', 'Review Row ID', 'Source Fact Refs')
        'Exception Handling' = @('Exception / Error Path', 'Program', 'Routine', 'Detection Mechanism', 'Fields / Messages Set', 'Handling Action', 'Effect', 'Supporting Detail', 'Evidence Status', 'Review Row ID', 'Source Fact Refs')
        'Message Inventory' = @('Message / Status / Literal', 'Description', 'Type', 'Program / Routine Sources', 'Occurrences', 'Condition / Handler', 'Carrier / Destination', 'Effect', 'Detail Refs', 'Evidence Status', 'Review Row ID', 'Source Fact Refs')
        'Message Coverage Control' = @('Message / Status / Literal', 'Description', 'Type', 'Program / Routine Sources', 'Occurrences', 'Condition / Handler', 'Carrier / Destination', 'Effect', 'Detail Refs', 'Evidence Status', 'Review Row ID', 'Source Fact Refs')
    }
    $allCoreDetail = New-Object System.Collections.Generic.List[string]
    $coreProgramSets = New-Object System.Collections.Generic.List[object]
    foreach ($section in $script:CoreSections) {
        $block = Get-ReviewH2Block $Markdown $section
        if (-not $block) { continue }
        $requiredHeaders = @($sectionHeaders[$section])
        $headers = @(Get-ReviewMatchingHeaderCells $block $requiredHeaders)
        if ($headers.Count -eq 0) {
            if ($section -in $requiredSections) { $findings.Add("$section lacks reader-useful detail: missing required row columns or data rows") }
            continue
        }
        $rows = @(Get-ReviewTableDataRows $block)
        if ($rows.Count -eq 0) { $findings.Add("$section lacks reader-useful detail: missing required row columns or data rows"); continue }
        $programIndex = [Array]::IndexOf($headers, 'Program')
        $programs = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
        foreach ($rowRecord in $rows) {
            $row = @($rowRecord.Cells)
            $allCoreDetail.Add(($row -join ' '))
            if ($programIndex -ge 0 -and $programIndex -lt $row.Count -and $row[$programIndex]) { $programs.Add([string]$row[$programIndex]) | Out-Null }
            foreach ($header in $requiredHeaders) {
                $columnIndex = [Array]::IndexOf($headers, $header)
                if ($columnIndex -ge $row.Count -or (Test-ReviewPlaceholderCell $row[$columnIndex])) { $findings.Add("$section row has missing required column: $header"); break }
            }
            $semanticCells = for ($columnIndex = 0; $columnIndex -lt $headers.Count -and $columnIndex -lt $row.Count; $columnIndex++) {
                if ($headers[$columnIndex] -notin @('Program', 'Routine', 'Program / Routine Sources', 'Supporting Detail', 'Detail Refs', 'Evidence Status', 'Review Row ID', 'Source Fact Refs')) { $row[$columnIndex] }
            }
            if (@(Get-ReviewReaderWords ($semanticCells -join ' ')).Count -lt 5) { $findings.Add("$section row is link-only and lacks reader-useful logic") }
        }
        $coreProgramSets.Add($programs)
        if ($section -in $requiredSections -and -not (Test-ReviewReaderUsefulDetail $block)) { $findings.Add("$section lacks reader-useful detail") }
    }
    $manifestPrograms = @((Get-ReviewMapValue $Manifest 'programs' @()) | ForEach-Object { [string](Get-ReviewMapValue $_ 'normalized_name' '') } | Where-Object { $_ })
    if ($manifestPrograms.Count -ge 2 -and -not (@($coreProgramSets | Where-Object { $_.Count -ge 2 }).Count)) { $findings.Add('at least one core section must contain rows for two or more programs') }
    if ($manifestPrograms.Count -and -not [regex]::IsMatch(($allCoreDetail -join ' '), '\b(carrier|return\s*(status|code)|queue|file|output|handoff)\b', 'IgnoreCase')) { $findings.Add('at least one core row must show a carrier, return status, queue, file, or output handoff') }
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

function Resolve-ReviewBundlePath {
    param([string]$ManifestPath, [AllowNull()][string]$ExplicitPath, [string]$Filename)
    if ($ExplicitPath) { return [IO.Path]::GetFullPath($ExplicitPath) }
    return Join-Path ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($ManifestPath))) $Filename
}

function Get-FlowSourcePackProgramBlock {
    param([string]$SourcePack, [string]$Program)
    $escaped = [regex]::Escape($Program)
    $marked = [regex]::Match($SourcePack, '(?ms)^<!-- BEGIN LOSSLESS PROGRAM ' + $escaped + '(?::.*?)? -->\s*$.*?^<!-- END LOSSLESS PROGRAM ' + $escaped + ' -->\s*$')
    if ($marked.Success) { return $marked.Value }
    $fallback = [regex]::Match($SourcePack, '(?ms)^# Program:\s*' + $escaped + '\s*$.*?(?=^# Program:\s*|\z)')
    if ($fallback.Success) { return $fallback.Value }
    return ''
}

function Test-FlowReaderFirstSourcePack {
    param([string]$SourcePack, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $identityFields = [ordered]@{
        'Document ID' = [string](Get-ReviewMapValue $Manifest 'document_id' (Get-ReviewMapValue $Manifest 'review_id' ''))
        'Flow Slug' = [string](Get-ReviewMapValue $Manifest 'flow_slug' '')
        'Program Set Slug' = [string](Get-ReviewMapValue $Manifest 'program_set_slug' '')
    }
    foreach ($label in $identityFields.Keys) {
        if (-not [regex]::IsMatch($SourcePack, '(?m)^' + [regex]::Escape($label) + ':\s*' + [regex]::Escape([string]$identityFields[$label]) + '\s*$')) { $findings.Add("source pack $($label.ToLowerInvariant()) does not match manifest") }
    }
    $programs = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
    foreach ($entry in @(Get-ReviewMapValue $Manifest 'programs' @())) {
        $program = [string](Get-ReviewMapValue $entry 'normalized_name' '')
        if (-not $program) { continue }
        if (-not $programs.Add($program)) { continue }
        $programBlock = Get-FlowSourcePackProgramBlock $SourcePack $program
        if (-not $programBlock) {
            $findings.Add("source pack missing complete program block: $program")
            continue
        }
        foreach ($section in @('Program Reading Summary', 'Calculation Logic', 'Validation Logic', 'Exception Handling', 'Message Inventory')) {
            if (-not [regex]::IsMatch($programBlock, '(?m)^##\s+' + [regex]::Escape($section) + '\s*$')) {
                $findings.Add("source pack missing $program reader-first section: $section")
            }
        }
    }
    if ($SourcePack -notmatch '(?i)navigation order only') { $findings.Add('source pack must state that program list order is navigation only') }
    return @($findings.ToArray())
}

function Test-FlowCoreCoverage {
    param($Facts, $Coverage, [string]$Markdown, [string]$SourcePack, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $visibleMarkdown = Remove-FlowHtmlComments $Markdown
    if ([string](Get-ReviewMapValue $Facts 'schema_version' '') -ne '0.4') { $findings.Add('formal review validation requires core facts schema_version 0.4') }
    if ([string](Get-ReviewMapValue $Coverage 'schema_version' '') -ne '0.4') { $findings.Add('formal review validation requires core coverage schema_version 0.4') }
    foreach ($finding in @(Test-FlowPreparedBundleIntegrity $Facts $SourcePack $Manifest)) { $findings.Add($finding) }
    $expectedDocumentId = [string](Get-ReviewMapValue $Manifest 'document_id' (Get-ReviewMapValue $Manifest 'review_id' ''))
    foreach ($artifact in @($Facts, $Coverage)) {
        $artifactDocumentId = [string](Get-ReviewMapValue $artifact 'document_id' (Get-ReviewMapValue $artifact 'review_id' ''))
        if ($artifactDocumentId -ne $expectedDocumentId) { $findings.Add('facts/coverage document identity does not match manifest') }
    }
    $sourceFacts = @(Get-ReviewMapValue $Facts 'source_facts' @())
    $itemsValue = Get-ReviewMapValue $Coverage 'items' $null
    $coverageItemsValue = Get-ReviewMapValue $Coverage 'coverage_items' $null
    if ([string](Get-ReviewMapValue $Coverage 'schema_version' '') -eq '0.4') {
        if ($null -eq $itemsValue -or $null -eq $coverageItemsValue) { $findings.Add('v0.4 coverage must contain both items and coverage_items') }
        elseif ((ConvertTo-FlowYamlText @($itemsValue)) -cne (ConvertTo-FlowYamlText @($coverageItemsValue))) { $findings.Add('coverage items and coverage_items mirrors differ') }
    }
    if ($null -eq $itemsValue) { $itemsValue = @($coverageItemsValue) }
    $items = @($itemsValue)
    $factById = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    foreach ($fact in $sourceFacts) {
        $factId = [string](Get-ReviewMapValue $fact 'source_fact_id' '')
        if (-not $factId) { $findings.Add('normalized fact missing source_fact_id'); continue }
        if ($factById.ContainsKey($factId)) { $findings.Add("duplicate normalized source_fact_id: $factId") }
        else { $factById[$factId] = $fact }
        $program = [string](Get-ReviewMapValue $fact 'program' '')
        $programBlock = Get-FlowSourcePackProgramBlock $SourcePack $program
        $exactInSource = [string](Get-ReviewMapValue $fact 'exact_value' '')
        if (-not $programBlock) { $findings.Add("source pack missing fact program block: $program") }
        elseif ($exactInSource -and -not (Test-FlowExactLiteral $programBlock $exactInSource)) { $findings.Add("source pack missing exact source value for ${factId}: $exactInSource") }
    }
    $factPrograms = @($sourceFacts | ForEach-Object { [string](Get-ReviewMapValue $_ 'program' '') } | Where-Object { $_ } | Sort-Object -Unique)
    foreach ($program in @(@(Get-ReviewMapValue $Manifest 'programs' @()) | ForEach-Object { [string](Get-ReviewMapValue $_ 'normalized_name' '') } | Where-Object { $_ } | Sort-Object -Unique)) {
        if ($factPrograms -cnotcontains $program) { $findings.Add("normalized facts missing manifest program: $program") }
    }
    $overview = Get-ReviewH2Block $Markdown 'Cross-Program Processing Overview'
    $overviewHeaders = @(Get-ReviewMatchingHeaderCells $overview @('Processing Layer', 'Programs / Main Routines', 'What To Understand First', 'Review Row ID', 'Source Fact Refs'))
    if ($overviewHeaders.Count) {
        $anchorIndex = [Array]::IndexOf($overviewHeaders, 'Review Row ID'); $refsIndex = [Array]::IndexOf($overviewHeaders, 'Source Fact Refs')
        foreach ($rowRecord in @(Get-ReviewTableDataRows $overview)) {
            $row = @($rowRecord.Cells); if ($row.Count -le [Math]::Max($anchorIndex, $refsIndex)) { continue }
            $refs = @([regex]::Matches((ConvertTo-FlowVisibleInlineText ([string]$row[$refsIndex])), '(?<![A-Za-z0-9_@#$-])SF-[A-Za-z0-9_@#$-]+(?![A-Za-z0-9_@#$-])') | ForEach-Object { $_.Value } | Sort-Object -Unique)
            if (-not $refs.Count) { $findings.Add('Cross-Program Processing Overview row lacks source fact references') }
            foreach ($id in $refs) { if (-not $factById.ContainsKey($id)) { $findings.Add("Cross-Program Processing Overview references unknown source fact $id") } }
            $rowAnchorIds = @(Get-FlowVisibleAnchorIds ([string]$row[$anchorIndex]))
            if ($rowAnchorIds.Count -ne 1 -or (Get-FlowAnchorDefinitionCount $visibleMarkdown $rowAnchorIds[0]) -ne 1) { $findings.Add('Cross-Program Processing Overview row requires one unique visible review anchor') }
            $claim = @($row[0..2]) -join ' '
            if ([regex]::IsMatch($claim, '\b(?:always\s+)?executes?\s+(?:before|after|in\s+that\s+order)\b|\b(?:confirmed|actual|source[- ]confirmed)\s+execution\s+(?:order|sequence)\b', 'IgnoreCase')) { $findings.Add('Cross-Program Processing Overview must not assert execution order or sequence') }
        }
    }
    foreach ($finding in @(Get-FlowCrossProgramRelationFindings $visibleMarkdown $factById $Manifest)) { $findings.Add($finding) }
    $itemById = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    $anchorMappings = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    $actualCounts = [ordered]@{ included = 0; merged = 0; excluded_non_core = 0; pending = 0 }
    foreach ($item in $items) {
        $factId = [string](Get-ReviewMapValue $item 'source_fact_id' '')
        if (-not $factId) { $findings.Add('coverage item missing source_fact_id'); continue }
        if ($itemById.ContainsKey($factId)) { $findings.Add("duplicate coverage item: $factId"); continue }
        $itemById[$factId] = $item
        $status = [string](Get-ReviewMapValue $item 'status' '')
        $declaredMergedIds = @(Get-ReviewMapValue $item 'merged_source_fact_ids' @())
        if ($status -notin @('included', 'merged', 'excluded_non_core', 'pending')) {
            $findings.Add("$factId has invalid coverage status: $status")
            continue
        }
        if ($status -ne 'merged' -and $declaredMergedIds.Count) { $findings.Add("$factId non-merged coverage must not declare merged_source_fact_ids") }
        $actualCounts[$status] = [int]$actualCounts[$status] + 1
        if ($status -eq 'pending') { $findings.Add("$factId remains pending in core coverage") }
        $fact = if ($factById.ContainsKey($factId)) { $factById[$factId] } else { $null }
        if ($null -eq $fact) { $findings.Add("coverage item has no normalized fact: $factId"); continue }
        foreach ($identityField in @('program', 'section', 'fact_type')) {
            $coverageValue = [string](Get-ReviewMapValue $item $identityField '')
            $factValue = [string](Get-ReviewMapValue $fact $identityField '')
            if (-not [string]::Equals($coverageValue, $factValue, [StringComparison]::Ordinal)) { $findings.Add("$factId coverage $identityField does not match normalized source fact") }
        }
        $section = [string](Get-ReviewMapValue $fact 'section' '')
        if ($status -eq 'excluded_non_core') {
            if (-not [string](Get-ReviewMapValue $item 'exclusion_reason' '')) { $findings.Add("$factId excluded_non_core requires exclusion_reason") }
            $factType = [string](Get-ReviewMapValue $fact 'fact_type' '')
            if ([bool](Get-ReviewMapValue $fact 'material' $false) -or $factType -in @('message', 'routine')) {
                $findings.Add("$factId is material/message/RLOG evidence and cannot be excluded_non_core")
            }
            continue
        }
        $anchor = [string](Get-ReviewMapValue $item 'review_anchor' '')
        $reviewSection = $section
        if ($section -eq 'Program Reading Summary') { $reviewSection = 'Program Set Reading Summary' }
        elseif ($section -eq 'Message Inventory' -and -not [bool](Get-ReviewMapValue (Get-ReviewMapValue $Manifest 'core_review_profile' ([ordered]@{})) 'include_message_inventory' $true)) { $reviewSection = 'Message Coverage Control' }
        $reviewBlock = Get-ReviewH2Block $visibleMarkdown $reviewSection
        $mappingRows = @(Get-FlowFactMappingRows $visibleMarkdown $reviewSection $anchor $factId)
        $mappingTexts = @($mappingRows | ForEach-Object { [string]$_.Text })
        $factType = [string](Get-ReviewMapValue $fact 'fact_type' '')
        $proseEligible = $factType -in @('summary_contribution', 'thematic_prose')
        if ($proseEligible) {
            $mappingTexts += @(Get-FlowVisibleAnchoredProseLines $visibleMarkdown $reviewSection $anchor $factId)
        }
        if ($anchor) {
            if (-not $anchorMappings.ContainsKey($anchor)) { $anchorMappings[$anchor] = New-Object System.Collections.Generic.List[object] }
            $anchorMappings[$anchor].Add([pscustomobject]@{ FactId = $factId; Status = $status; Item = $item })
        }
        if (-not $reviewBlock) { $findings.Add("final review is missing source section $reviewSection for $factId") }
        elseif (-not $mappingTexts.Count -and $proseEligible) { $findings.Add("$factId must map to exactly one visible required-header data row or reader-useful anchored prose line inside ${reviewSection}: $anchor") }
        elseif (-not $mappingRows.Count -and -not $proseEligible) { $findings.Add("$factId must map to exactly one visible required-header data row inside ${reviewSection}: $anchor") }
        elseif ($mappingTexts.Count -ne 1) { $findings.Add("$factId must map to exactly one visible anchored mapping") }
        elseif (-not @($mappingTexts | Where-Object {
            $detail = [regex]::Replace($_, '<[^>]+>', ' ').Replace($factId, ' ')
            $exactDetail = [string](Get-ReviewMapValue $fact 'exact_value' '')
            if ($exactDetail) { $detail = $detail.Replace($exactDetail, ' ') }
            @(Get-ReviewReaderWords $detail).Count -ge 7
        }).Count) { $findings.Add("$factId review anchor/fact row is link-only and lacks reader-useful logic") }
        foreach ($value in @(Get-FlowFactSemanticValues $fact)) {
            if (-not $mappingTexts.Count -or -not @($mappingTexts | Where-Object { Test-FlowExactLiteral $_ ([string]$value) -IgnoreCase }).Count) { $findings.Add("$factId material row is missing source semantic value: $value") }
        }
        if ($factType -in @('summary_contribution', 'thematic_prose') -and $mappingTexts.Count -and -not (Test-FlowSummarySemanticsPreserved $fact $mappingTexts)) { $findings.Add("$factId mapping does not preserve source summary semantics") }
        if ($factType -in @('summary_contribution', 'thematic_prose', 'thematic_table')) {
            $factProgram = [string](Get-ReviewMapValue $fact 'program' '')
            if ($factProgram -and (-not $mappingTexts.Count -or -not @($mappingTexts | Where-Object { Test-FlowExactLiteral $_ $factProgram }).Count)) { $findings.Add("$factId summary/thematic mapping is missing exact fact.program: $factProgram") }
        }
        if ([string](Get-ReviewMapValue $Facts 'schema_version' '') -eq '0.4' -and $mappingRows.Count) {
            foreach ($typedFinding in @(Get-FlowFactTypedSemanticFindings $fact $mappingRows)) { $findings.Add("$factId $typedFinding") }
        }
        if ($status -eq 'merged') {
            $mergedIds = $declaredMergedIds
            if ($mergedIds.Count -eq 0) { $findings.Add("$factId merged coverage lacks merged_source_fact_ids") }
            foreach ($mergedId in $mergedIds) {
                if (-not $factById.ContainsKey([string]$mergedId)) { $findings.Add("$factId references unknown merged_source_fact_id: $mergedId") }
                elseif (-not @($mappingTexts | Where-Object { Test-FlowExactLiteral $_ ([string]$mergedId) }).Count) { $findings.Add("$factId merged review row omits source fact: $mergedId") }
            }
        }
        if ($factType -in @('calculation', 'validation', 'exception', 'message', 'routine')) {
            $token = [string](Get-ReviewMapValue $fact 'exact_value' '')
            if (-not $token) { $token = [string](Get-ReviewMapValue $fact 'review_exact_token' '') }
            if ($token -and -not @($mappingTexts | Where-Object { Test-FlowExactLiteral $_ $token }).Count) { $findings.Add("$factId exact value is missing from its formal review row: $token") }
        }
    }
    foreach ($item in $items) {
        if ([string](Get-ReviewMapValue $item 'status' '') -ne 'merged') { continue }
        $factId = [string](Get-ReviewMapValue $item 'source_fact_id' '')
        $anchor = [string](Get-ReviewMapValue $item 'review_anchor' '')
        $seenMergedIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($mergedId in @(Get-ReviewMapValue $item 'merged_source_fact_ids' @())) {
            $mergedKey = [string]$mergedId
            if (-not $seenMergedIds.Add($mergedKey)) { $findings.Add("$factId repeats merged_source_fact_id $mergedKey"); continue }
            if ($mergedKey -ceq $factId) { $findings.Add("$factId must not merge itself"); continue }
            if (-not $itemById.ContainsKey($mergedKey)) { $findings.Add("$factId merged_source_fact_id $mergedKey has no unique coverage item"); continue }
            $peer = $itemById[$mergedKey]
            if ([string](Get-ReviewMapValue $peer 'status' '') -ne 'merged') { $findings.Add("$factId merged_source_fact_id $mergedKey must have coverage status merged") }
            if (-not [string]::Equals([string](Get-ReviewMapValue $peer 'review_anchor' ''), $anchor, [StringComparison]::Ordinal)) { $findings.Add("$factId merged_source_fact_id $mergedKey must use the same review_anchor") }
        }
    }
    foreach ($anchor in $anchorMappings.Keys) {
        $mappings = @($anchorMappings[$anchor]); $definitions = Get-FlowAnchorDefinitionCount $visibleMarkdown $anchor
        if ($definitions -ne 1) { $findings.Add("coverage anchor $anchor must be defined exactly once; found $definitions") }
        if ($mappings.Count -le 1) { continue }
        if (@($mappings | Where-Object { $_.Status -ne 'merged' }).Count) {
            $findings.Add("coverage anchor $anchor is reused by non-merged source facts")
            continue
        }
        $groupIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($mapping in $mappings) { [void]$groupIds.Add([string]$mapping.FactId) }
        foreach ($mapping in $mappings) {
            $expectedIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            foreach ($groupId in $groupIds) { if ($groupId -ne [string]$mapping.FactId) { [void]$expectedIds.Add($groupId) } }
            $declaredIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            foreach ($mergedId in @(Get-ReviewMapValue $mapping.Item 'merged_source_fact_ids' @())) { [void]$declaredIds.Add([string]$mergedId) }
            if (-not $declaredIds.SetEquals($expectedIds)) {
                $findings.Add("coverage anchor $anchor merged group for $($mapping.FactId) must declare exactly every other source fact mapped to that anchor")
            }
        }
    }
    foreach ($finding in @(Get-FlowReviewRowReconciliationFindings $visibleMarkdown $factById $itemById $Manifest)) { $findings.Add($finding) }
    foreach ($factId in $factById.Keys) { if (-not $itemById.ContainsKey($factId)) { $findings.Add("normalized fact missing from coverage: $factId") } }
    $coverageCounts = Get-ReviewMapValue $Coverage 'coverage_counts' ([ordered]@{})
    $expectedFactCount = Get-ReviewMapValue $Coverage 'expected_source_fact_count' (Get-ReviewMapValue $coverageCounts 'total_source_facts' $sourceFacts.Count)
    $declaredItemCount = Get-ReviewMapValue $Coverage 'coverage_item_count' $items.Count
    if ([int]$expectedFactCount -ne $sourceFacts.Count) { $findings.Add("coverage expected_source_fact_count mismatch: declared=$expectedFactCount actual=$($sourceFacts.Count)") }
    if ([int]$declaredItemCount -ne $items.Count) { $findings.Add("coverage coverage_item_count mismatch: declared=$declaredItemCount actual=$($items.Count)") }
    if ($sourceFacts.Count -ne $items.Count) { $findings.Add("normalized fact/coverage item count mismatch: facts=$($sourceFacts.Count) items=$($items.Count)") }
    $declaredCounts = Get-ReviewMapValue $Coverage 'status_counts' $null
    if ($null -ne $declaredCounts) {
        foreach ($status in @('included', 'merged', 'excluded_non_core', 'pending')) {
            if ([int](Get-ReviewMapValue $declaredCounts $status 0) -ne [int]$actualCounts[$status]) {
                $findings.Add("coverage status_counts.$status mismatch")
            }
        }
    }
    $actualPending = [int]$actualCounts.pending
    $actualAccounted = $items.Count - $actualPending
    $declaredPending = Get-ReviewMapValue $coverageCounts 'pending_source_facts' $actualPending
    $declaredAccounted = Get-ReviewMapValue $coverageCounts 'accounted_source_facts' $actualAccounted
    if ([int]$declaredPending -ne $actualPending) { $findings.Add('coverage_counts.pending_source_facts mismatch') }
    if ([int]$declaredAccounted -ne $actualAccounted) { $findings.Add('coverage_counts.accounted_source_facts mismatch') }
    $actualByProgram = [ordered]@{}; $actualBySection = [ordered]@{}; $actualRoutineRlog = [ordered]@{}
    foreach ($fact in $sourceFacts) {
        $program = [string](Get-ReviewMapValue $fact 'program' '')
        $section = [string](Get-ReviewMapValue $fact 'section' '')
        $actualByProgram[$program] = [int](Get-ReviewMapValue $actualByProgram $program 0) + 1
        $actualBySection[$section] = [int](Get-ReviewMapValue $actualBySection $section 0) + 1
        if ([string](Get-ReviewMapValue $fact 'fact_type' '') -eq 'routine') { $actualRoutineRlog[$program] = [int](Get-ReviewMapValue $actualRoutineRlog $program 0) + 1 }
    }
    $dimensions = @(
        [pscustomobject]@{ Name = 'by_program'; Actual = $actualByProgram },
        [pscustomobject]@{ Name = 'by_section'; Actual = $actualBySection },
        [pscustomobject]@{ Name = 'routine_rlog'; Actual = $actualRoutineRlog }
    )
    foreach ($dimension in $dimensions) {
        $declared = Get-ReviewMapValue $coverageCounts $dimension.Name $null
        if ($declared -isnot [Collections.IDictionary]) { $findings.Add("coverage counts missing required $($dimension.Name) mapping"); continue }
        $actual = $dimension.Actual
        if (@($declared.Keys).Count -ne @($actual.Keys).Count) { $findings.Add("coverage_counts.$($dimension.Name) mismatch"); continue }
        foreach ($key in $actual.Keys) {
            if ([int](Get-ReviewMapValue $declared $key -1) -ne [int]$actual[$key]) { $findings.Add("coverage_counts.$($dimension.Name) mismatch"); break }
        }
    }
    $coverageReviewStatus = [string](Get-ReviewMapValue $Coverage 'review_status' '')
    if ($coverageReviewStatus -ne 'complete_exploratory') { $findings.Add('coverage review_status must be complete_exploratory') }
    if ([string](Get-ReviewMapValue $Coverage 'schema_version' '') -eq '0.4') {
        $requiredStatuses = @('included', 'merged', 'excluded_non_core', 'pending'); $allowedStatuses = @(Get-ReviewMapValue $Coverage 'allowed_statuses' @())
        if (($requiredStatuses -join "`n") -cne ($allowedStatuses -join "`n")) { $findings.Add('coverage allowed_statuses must match the v0.4 contract') }
        if ([string](Get-ReviewMapValue $Coverage 'coverage_status' '') -ne 'complete') { $findings.Add('coverage coverage_status must be complete') }
    }
    return @($findings.ToArray())
}

function Invoke-FlowCoreReviewValidation {
    param(
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [Parameter(Mandatory = $true)][string]$ReviewPath,
        [AllowNull()][string]$SourcePackPath,
        [AllowNull()][string]$CoreFactsPath,
        [AllowNull()][string]$CoveragePath
    )
    $manifest = Read-FlowYamlFile $ManifestPath
    if ($manifest -isnot [System.Collections.IDictionary]) { return @('manifest is not a YAML mapping') }
    $findings = New-Object System.Collections.Generic.List[string]
    foreach ($finding in @(Test-FlowCoreReviewManifest $manifest)) { $findings.Add($finding) }
    foreach ($finding in @(Test-FlowProgramListSnapshot $ManifestPath $manifest)) { $findings.Add($finding) }
    $resolvedSourcePack = Resolve-ReviewBundlePath $ManifestPath $SourcePackPath 'program-set-reader-first-source-pack.md'
    $resolvedFacts = Resolve-ReviewBundlePath $ManifestPath $CoreFactsPath 'program-set-core-facts.yaml'
    $resolvedCoverage = Resolve-ReviewBundlePath $ManifestPath $CoveragePath 'program-set-core-coverage.yaml'
    foreach ($finding in @(Test-FlowBundleLayout $ManifestPath $ReviewPath $resolvedSourcePack $resolvedFacts $resolvedCoverage $manifest)) { $findings.Add($finding) }
    foreach ($bundlePath in @($resolvedSourcePack, $resolvedFacts, $resolvedCoverage)) {
        if (-not (Test-Path -LiteralPath $bundlePath -PathType Leaf)) { $findings.Add("missing merger bundle artifact: $bundlePath") }
    }
    if (-not (Test-Path -LiteralPath $ReviewPath -PathType Leaf)) {
        $findings.Add("missing review artifact: $ReviewPath")
        return @($findings.ToArray())
    }
    if ([string](Get-ReviewMapValue $manifest 'review_status' '') -ne 'complete_exploratory') { $findings.Add('formal review validation requires manifest review_status complete_exploratory') }
    if ([string](Get-ReviewMapValue $manifest 'artifact_readiness' '') -ne 'ready') { $findings.Add('formal review validation requires manifest artifact_readiness ready') }
    if ([string](Get-ReviewMapValue $manifest 'merge_coverage' '') -ne 'complete') { $findings.Add('formal review validation requires manifest merge_coverage complete') }
    $canonical = [string](Get-ReviewMapValue $manifest 'canonical_filename' '')
    if ($canonical -and [IO.Path]::GetFileName($ReviewPath) -ne $canonical) { $findings.Add("formal review filename must be $canonical") }
    $markdown = [IO.File]::ReadAllText($ReviewPath)
    foreach ($finding in @(Test-FlowReviewIdentity $markdown $manifest)) { $findings.Add($finding) }
    foreach ($finding in @(Test-FlowCoreReviewMarkdown $markdown $manifest)) { $findings.Add($finding) }
    $sourcePackText = ''
    if (Test-Path -LiteralPath $resolvedSourcePack -PathType Leaf) {
        $sourcePackText = [IO.File]::ReadAllText($resolvedSourcePack)
        foreach ($finding in @(Test-FlowReaderFirstSourcePack $sourcePackText $manifest)) { $findings.Add($finding) }
    }
    if ((Test-Path -LiteralPath $resolvedFacts -PathType Leaf) -and (Test-Path -LiteralPath $resolvedCoverage -PathType Leaf)) {
        $facts = Read-FlowYamlFile $resolvedFacts
        $coverage = Read-FlowYamlFile $resolvedCoverage
        if ($facts -isnot [System.Collections.IDictionary]) { $findings.Add('core facts artifact is not a YAML mapping') }
        elseif ($coverage -isnot [System.Collections.IDictionary]) { $findings.Add('core coverage artifact is not a YAML mapping') }
        else { foreach ($finding in @(Test-FlowCoreCoverage $facts $coverage $markdown $sourcePackText $manifest)) { $findings.Add($finding) } }
    }
    return @($findings.ToArray())
}

Export-ModuleMember -Function Invoke-FlowCoreReviewValidation
