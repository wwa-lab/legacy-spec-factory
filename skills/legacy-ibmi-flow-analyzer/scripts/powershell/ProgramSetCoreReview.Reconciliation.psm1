<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Native PowerShell 5.1 reconciliation helpers for reader-first merge validation.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'FlowYaml.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Markdown.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Builder.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Input.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Readiness.psm1') -Force

$script:ExactTokenCharacterClass = '[A-Za-z0-9_@#$%*+]'
$script:ExactTokenConnectors = './:-'
$script:SourceFactIdPattern = '(?<![A-Za-z0-9_@#$-])SF-[A-Za-z0-9_@#$-]+(?![A-Za-z0-9_@#$-])'
$script:RequiredCompactArtifacts = @(
    'program-analysis.md', 'program-analysis-summary.yaml', 'source-index.yaml',
    'routine-index.md', 'message-inventory.yaml', 'routine-logic-details.md',
    'routine-logic-details.yaml'
)
$script:SummarySemanticStopWords = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($word in @('about', 'after', 'also', 'analysis', 'approved', 'artifact', 'asserted', 'available', 'before', 'complete', 'confirmed', 'consulting', 'context', 'contribution', 'detail', 'details', 'evidence', 'exploratory', 'fact', 'fixture', 'follow', 'itself', 'local', 'marker', 'overview', 'program', 'reader', 'reading', 'review', 'routine', 'routines', 'source', 'standalone', 'summary', 'thematic', 'trace', 'understand', 'wrapper', 'with', 'without', 'would', 'your', 'from', 'into', 'that', 'this', 'these', 'those', 'their', 'then', 'than', 'when', 'where', 'which', 'while', 'should', 'could', 'must', 'will', 'have', 'has', 'does', 'using', 'used', 'identifiers', 'obj')) { [void]$script:SummarySemanticStopWords.Add($word) }

function Get-ReconciliationMapValue {
    param($Map, [string]$Key, $Default = $null)
    if ($null -eq $Map) { return $Default }
    if ($Map -is [Collections.IDictionary]) {
        if ($Map.Contains($Key)) { return $Map[$Key] }
        return $Default
    }
    $property = $Map.PSObject.Properties[$Key]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Test-FlowConnectorReachesCore {
    param([string]$Text, [int]$Index, [int]$Step)
    $cursor = $Index
    while ($cursor -ge 0 -and $cursor -lt $Text.Length -and $script:ExactTokenConnectors.Contains([string]$Text[$cursor])) {
        $cursor += $Step
    }
    return $cursor -ge 0 -and $cursor -lt $Text.Length -and [regex]::IsMatch([string]$Text[$cursor], '^' + $script:ExactTokenCharacterClass + '$')
}

function Test-FlowExactLiteral {
    param([AllowEmptyString()][string]$Text, [AllowEmptyString()][string]$Literal, [switch]$IgnoreCase)
    $value = [regex]::Replace((ConvertTo-FlowVisibleInlineText $Literal).Trim(), '\s+', ' ')
    if (-not $value) { return $true }
    $haystack = [regex]::Replace((ConvertTo-FlowVisibleInlineText $Text), '\s+', ' ')
    $options = if ($IgnoreCase) { [Text.RegularExpressions.RegexOptions]::IgnoreCase } else { [Text.RegularExpressions.RegexOptions]::None }
    foreach ($match in @([regex]::Matches($haystack, [regex]::Escape($value), $options))) {
        $before = $match.Index - 1
        $after = $match.Index + $match.Length
        $beforeConnected = $before -ge 0 -and (
            [regex]::IsMatch([string]$haystack[$before], '^' + $script:ExactTokenCharacterClass + '$') -or
            ($script:ExactTokenConnectors.Contains([string]$haystack[$before]) -and (Test-FlowConnectorReachesCore $haystack $before -1))
        )
        $afterConnected = $after -lt $haystack.Length -and (
            [regex]::IsMatch([string]$haystack[$after], '^' + $script:ExactTokenCharacterClass + '$') -or
            ($script:ExactTokenConnectors.Contains([string]$haystack[$after]) -and (Test-FlowConnectorReachesCore $haystack $after 1))
        )
        if (-not $beforeConnected -and -not $afterConnected) { return $true }
    }
    return $false
}

function ConvertTo-FlowVisibleInlineText {
    param([AllowEmptyString()][string]$Text)
    $visible = [regex]::Replace($Text, '<!--.*?-->', '', [Text.RegularExpressions.RegexOptions]::Singleline)
    $codeSpans = New-Object System.Collections.Generic.List[string]
    $codePattern = [regex]'(?s)(?<fence>`+)(?<content>.*?)\k<fence>'
    while ($true) {
        $codeMatch = $codePattern.Match($visible)
        if (-not $codeMatch.Success) { break }
        $index = $codeSpans.Count
        $codeSpans.Add($codeMatch.Groups['content'].Value)
        $placeholder = ([char]1) + "FLOWCODE$index" + ([char]2)
        $visible = $visible.Remove($codeMatch.Index, $codeMatch.Length).Insert($codeMatch.Index, $placeholder)
    }
    $visible = Remove-FlowMarkdownLinkDestinations $visible
    $visible = [regex]::Replace($visible, '!?\[(?<label>[^\]]*)\](?:\[[^\]]*\])?', '${label}')
    $visible = Remove-FlowMarkdownHtmlTags $visible
    $visible = [Net.WebUtility]::HtmlDecode($visible)
    for ($index = 0; $index -lt $codeSpans.Count; $index++) { $visible = $visible.Replace(([char]1) + "FLOWCODE$index" + ([char]2), $codeSpans[$index]) }
    return ConvertTo-FlowInlineLiteral $visible
}

function ConvertTo-FlowInlineLiteral {
    param([AllowEmptyString()][string]$Text)
    $visible = [Net.WebUtility]::HtmlDecode($Text)
    $visible = [regex]::Replace($visible, '(?s)(?<fence>`+)(?<content>.*?)\k<fence>', '${content}')
    $emphasis = '(?s)(?<![A-Za-z0-9_])(?<mark>\*{1,3}|_{1,3})(?=\S)(?<content>.+?)(?<=\S)\k<mark>(?![A-Za-z0-9_])'
    do {
        $previous = $visible
        $visible = [regex]::Replace($visible, $emphasis, '${content}')
    } while ($visible -cne $previous)
    $visible = [regex]::Replace($visible, '\\([\\`*{}\[\]()#+.!_|<>-])', '$1')
    return $visible
}

function Remove-FlowInlineCodeMarkup {
    param([AllowEmptyString()][string]$Markdown)
    return [regex]::Replace($Markdown, '(?s)(?<ticks>`+).*?\k<ticks>', '')
}

function Copy-ReconciliationMap {
    param($Map)
    $copy = [ordered]@{}
    if ($Map -is [Collections.IDictionary]) {
        foreach ($key in $Map.Keys) { $copy[[string]$key] = $Map[$key] }
    }
    elseif ($null -ne $Map) {
        foreach ($property in $Map.PSObject.Properties) { $copy[$property.Name] = $property.Value }
    }
    return $copy
}

function Test-FlowOrdinalSequence {
    param($Left, $Right)
    $leftItems = @($Left); $rightItems = @($Right)
    if ($leftItems.Count -ne $rightItems.Count) { return $false }
    for ($index = 0; $index -lt $leftItems.Count; $index++) { if (-not [string]::Equals([string]$leftItems[$index], [string]$rightItems[$index], [StringComparison]::Ordinal)) { return $false } }
    return $true
}

function Test-FlowProgramListSnapshot {
    param([string]$ManifestPath, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $localPath = Join-Path ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($ManifestPath))) 'program-list.txt'
    if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) { return @("missing preserved program-list snapshot: $localPath") }
    try { $localPrograms = @(Read-FlowProgramsFileInput $localPath) }
    catch { return @("cannot read preserved program-list snapshot ${localPath}: $($_.Exception.Message)") }
    $entries = @(Get-ReconciliationMapValue $Manifest 'programs' @())
    $manifestInputs = @($entries | ForEach-Object { $inputName = [string](Get-ReconciliationMapValue $_ 'input_name' ''); if ($inputName) { $inputName } else { [string](Get-ReconciliationMapValue $_ 'normalized_name' '') } })
    if (-not (Test-FlowOrdinalSequence $localPrograms $manifestInputs)) { $findings.Add('preserved program-list.txt does not match the ordered manifest program inputs') }
    $profile = Get-ReconciliationMapValue $Manifest 'program_resolution_profile' ([ordered]@{}); $normalization = Get-ReconciliationMapValue $profile 'program_name_normalization' ([ordered]@{})
    try { $normalizedLocal = @($localPrograms | ForEach-Object { Normalize-FlowProgramNameInput ([string]$_) ([ordered]@{ program_name_normalization = $normalization }) }) }
    catch { $findings.Add("preserved program-list.txt contains an invalid program: $($_.Exception.Message)"); $normalizedLocal = @() }
    $manifestNormalized = @($entries | ForEach-Object { [string](Get-ReconciliationMapValue $_ 'normalized_name' '') })
    if ($normalizedLocal.Count -and -not (Test-FlowOrdinalSequence $normalizedLocal $manifestNormalized)) { $findings.Add('preserved program-list.txt normalized identities/order do not match manifest programs') }
    $runProfile = Get-ReconciliationMapValue $Manifest 'run_profile' ([ordered]@{}); $source = Get-ReconciliationMapValue $runProfile 'program_list_source' $null
    $sourcePath = [string](Get-ReconciliationMapValue $source 'path' ''); $expectedDigest = ([string](Get-ReconciliationMapValue $source 'sha256' '')).Trim().ToLowerInvariant()
    if (-not $sourcePath -or -not $expectedDigest) { $findings.Add('run_profile.program_list_source requires absolute path and sha256'); return @($findings.ToArray()) }
    if (-not [IO.Path]::IsPathRooted($sourcePath)) { $findings.Add('original program-list source path must be absolute'); return @($findings.ToArray()) }
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { $findings.Add("original program-list source is unavailable: $sourcePath"); return @($findings.ToArray()) }
    $sha = [Security.Cryptography.SHA256]::Create(); try { $actualDigest = ([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($sourcePath)))).Replace('-', '').ToLowerInvariant() } finally { $sha.Dispose() }
    if ($actualDigest -cne $expectedDigest) { $findings.Add('original program-list source sha256 has changed') }
    try { $originalPrograms = @(Read-FlowProgramsFileInput $sourcePath); if (-not (Test-FlowOrdinalSequence $originalPrograms $localPrograms)) { $findings.Add('preserved program-list.txt differs from the original SME program list') } }
    catch { $findings.Add("cannot read original program-list source ${sourcePath}: $($_.Exception.Message)") }
    return @($findings.ToArray())
}

function Get-FlowRevalidatedManifest {
    param($Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $manifestCopy = Copy-ReconciliationMap $Manifest
    $runProfile = Get-ReconciliationMapValue $Manifest 'run_profile' ([ordered]@{})
    $root = [string](Get-ReconciliationMapValue $runProfile 'artifact_root' '')
    if (-not $root -or -not (Test-Path -LiteralPath $root -PathType Container)) {
        return [ordered]@{
            Manifest = $manifestCopy
            Findings = @('current program-analysis readiness cannot run: manifest artifact root is missing or unavailable')
        }
    }
    $root = [IO.Path]::GetFullPath($root)
    $mode = [string](Get-ReconciliationMapValue $runProfile 'artifact_repo_mode' 'current_run')
    if ($mode -notin @('current_run', 'approved_document_repo')) {
        $findings.Add("current program-analysis readiness has invalid artifact repo mode: $mode")
    }
    else {
        $expectedCrossRunReuse = $mode -eq 'approved_document_repo'
        $crossRunReuse = Get-ReconciliationMapValue $runProfile 'cross_run_reuse' $null
        if (($crossRunReuse -isnot [bool]) -or (([bool]$crossRunReuse) -ne $expectedCrossRunReuse)) {
            $findings.Add('run_profile cross_run_reuse does not match artifact repo mode')
        }
        $expectedReusePolicy = if ($expectedCrossRunReuse) { 'approved_document_repo_clone' } else { 'current_run_only' }
        $reusePolicy = [string](Get-ReconciliationMapValue $runProfile 'reuse_policy' '')
        if ($reusePolicy -ne $expectedReusePolicy) {
            $findings.Add('run_profile reuse_policy does not match artifact repo mode')
        }
    }
    $lookup = Get-ReconciliationMapValue $Manifest 'program_resolution_profile' ([ordered]@{})
    $resolvedByProgram = [Collections.Hashtable]::new([StringComparer]::Ordinal)
    $rebuiltEntries = New-Object System.Collections.Generic.List[object]
    foreach ($entry in @(Get-ReconciliationMapValue $Manifest 'programs' @())) {
        $program = [string](Get-ReconciliationMapValue $entry 'normalized_name' '')
        if (-not $program) { continue }
        $resolution = [string](Get-ReconciliationMapValue $entry 'run_resolution' '')
        $source = [string](Get-ReconciliationMapValue $entry 'artifact_source' '')
        if ($mode -eq 'approved_document_repo') {
            if ($resolution -ne 'reused_artifact_repo' -or $source -ne 'approved_document_repo') {
                $findings.Add("current program-analysis readiness mode/resolution mismatch for $program")
            }
        }
        elseif ($resolution -notin @('analyzed_this_run', 'reused_same_run') -or $source -ne 'delivery_working_branch') {
            $findings.Add("current program-analysis readiness mode/resolution mismatch for $program")
        }
        if (-not $resolvedByProgram.ContainsKey($program)) {
            try {
                $found = Find-FlowProgramArtifactRoot -Root $root -Program $program -LookupProfile $lookup
                $artifactRoot = [string](Get-ReconciliationMapValue $found 'Root' '')
                $matches = @(Get-ReconciliationMapValue $found 'Matches' @())
                $compact = Get-FlowArtifactStatuses -Root $root -ArtifactRoot $artifactRoot -Program $program
                $readiness = Get-FlowArtifactReadiness -Root $root -ArtifactRoot $artifactRoot `
                    -Program $program -CompactArtifacts $compact -AmbiguousMatches $matches
                $resolvedByProgram[$program] = [ordered]@{
                    ArtifactRoot = $artifactRoot
                    CompactArtifacts = $compact
                    Readiness = $readiness
                }
                if ([string](Get-ReconciliationMapValue $readiness 'status' 'not_ready') -ne 'ready') {
                    $details = @((Get-ReconciliationMapValue $readiness 'findings' @()) | ForEach-Object { [string]$_ }) -join '; '
                    $findings.Add("current program-analysis readiness failed for ${program}: $details")
                }
            }
            catch {
                $findings.Add("current program-analysis readiness failed for ${program}: $($_.Exception.Message)")
                $resolvedByProgram[$program] = [ordered]@{
                    ArtifactRoot = $null
                    CompactArtifacts = [ordered]@{}
                    Readiness = [ordered]@{ status = 'not_ready'; findings = @($_.Exception.Message) }
                }
            }
        }
        $resolved = $resolvedByProgram[$program]
        $resolvedRoot = [string](Get-ReconciliationMapValue $resolved 'ArtifactRoot' '')
        $resolvedCompact = Get-ReconciliationMapValue $resolved 'CompactArtifacts' ([ordered]@{})
        $storedRoot = [string](Get-ReconciliationMapValue $entry 'artifact_root' '')
        $storedCompact = Get-ReconciliationMapValue $entry 'compact_artifacts' ([ordered]@{})
        if (-not $storedRoot.Equals($resolvedRoot, [StringComparison]::Ordinal)) {
            $findings.Add("current program-analysis readiness path differs from manifest for $program")
        }
        if ((ConvertTo-FlowYamlText $storedCompact) -cne (ConvertTo-FlowYamlText $resolvedCompact)) {
            $findings.Add("current program-analysis compact artifact inventory differs from manifest for $program")
        }
        $entryCopy = Copy-ReconciliationMap $entry
        $entryCopy['artifact_root'] = $resolvedRoot
        $entryCopy['candidate_artifact_root'] = $resolvedRoot
        $entryCopy['compact_artifacts'] = $resolvedCompact
        $entryCopy['artifact_readiness'] = Get-ReconciliationMapValue $resolved 'Readiness' ([ordered]@{})
        $rebuiltEntries.Add($entryCopy)
    }
    $manifestCopy['programs'] = @($rebuiltEntries.ToArray())
    return [ordered]@{ Manifest = $manifestCopy; Findings = @($findings.ToArray()) }
}

function Test-FlowCurrentProgramReadiness {
    param($Manifest)
    $result = Get-FlowRevalidatedManifest $Manifest
    return @(Get-ReconciliationMapValue $result 'Findings' @())
}

function Get-FlowAnchorDefinitionCount {
    param([string]$Markdown, [string]$Anchor)
    $escaped = [regex]::Escape($Anchor)
    $visibleMarkdown = Remove-FlowInlineCodeMarkup (Remove-FlowHtmlComments $Markdown)
    return @([regex]::Matches($visibleMarkdown, '(?<!\\)<a\s+(?:[^>]*\s)?id=["'']' + $escaped + '["''][^>]*>', 'IgnoreCase')).Count + @([regex]::Matches($visibleMarkdown, '(?<!\\)\{#' + $escaped + '\}')).Count
}

function Get-FlowVisibleAnchorIds {
    param([AllowEmptyString()][string]$Markdown)
    $surface = Remove-FlowInlineCodeMarkup (Remove-FlowHtmlComments $Markdown)
    $ids = New-Object System.Collections.Generic.List[string]
    foreach ($match in @([regex]::Matches($surface, '(?<!\\)<a\s+(?:[^>]*\s)?id=["''](?<id>[^"'']+)["''][^>]*>', 'IgnoreCase'))) { $ids.Add($match.Groups['id'].Value) }
    foreach ($match in @([regex]::Matches($surface, '(?<!\\)\{#(?<id>[^}]+)\}'))) { $ids.Add($match.Groups['id'].Value) }
    return @($ids.ToArray())
}

function Get-FlowH1IdentityFindings {
    param([AllowEmptyString()][string]$Markdown, [string]$FolderSlug)
    $visible = Remove-FlowHtmlComments $Markdown
    $headings = @([regex]::Matches($visible, '(?m)^[ ]{0,3}#(?!#)\s+(.+?)\s*#*\s*$'))
    if ($headings.Count -ne 1) { return @("final review must contain exactly one canonical H1; found $($headings.Count)") }
    $rendered = ConvertTo-FlowVisibleInlineText $headings[0].Groups[1].Value
    if (-not $FolderSlug -or -not (Test-FlowExactLiteral $rendered $FolderSlug)) { return @('final review H1 must include the rendered flow/program-set folder identity') }
    return @()
}

function Test-FlowBundleLayout {
    param([string]$ManifestPath, [string]$ReviewPath, [string]$SourcePackPath, [string]$FactsPath, [string]$CoveragePath, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $manifestFull = [IO.Path]::GetFullPath($ManifestPath); $bundle = [IO.Path]::GetDirectoryName($manifestFull)
    if ([IO.Path]::GetFileName($manifestFull) -cne 'program-set-core-input-manifest.yaml') { $findings.Add('manifest basename must be program-set-core-input-manifest.yaml') }
    $folderSlug = [string](Get-ReconciliationMapValue $Manifest 'folder_slug' '')
    if ([IO.Path]::GetFileName($bundle) -cne $folderSlug) { $findings.Add('manifest parent directory must equal folder_slug') }
    $targets = @(
        [pscustomobject]@{ Path = $ReviewPath; Name = [string](Get-ReconciliationMapValue $Manifest 'canonical_filename' '') },
        [pscustomobject]@{ Path = $SourcePackPath; Name = 'program-set-reader-first-source-pack.md' },
        [pscustomobject]@{ Path = $FactsPath; Name = 'program-set-core-facts.yaml' },
        [pscustomobject]@{ Path = $CoveragePath; Name = 'program-set-core-coverage.yaml' }
    )
    foreach ($target in $targets) {
        $full = [IO.Path]::GetFullPath([string]$target.Path)
        if (-not [string]::Equals([IO.Path]::GetDirectoryName($full), $bundle, [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($full) -cne [string]$target.Name) { $findings.Add("bundle artifact must be canonical sibling: $($target.Name)") }
    }
    return @($findings.ToArray())
}

function Get-FlowFactSemanticValues {
    param($Fact)
    $type = [string](Get-ReconciliationMapValue $Fact 'fact_type' '')
    if (-not $type) { return @() }
    $values = New-Object System.Collections.Generic.List[string]
    $seen = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($value in @((Get-ReconciliationMapValue $Fact 'program' ''))) {
        foreach ($item in @($value)) { $text = [string]$item; if ($text -and $seen.Add($text)) { $values.Add($text) } }
    }
    if ($type -in @('summary_contribution', 'thematic_prose')) { return @($values.ToArray()) }
    foreach ($value in @((Get-ReconciliationMapValue $Fact 'evidence_reference' @()), (Get-ReconciliationMapValue $Fact 'evidence_status' ''))) {
        foreach ($item in @($value)) { $text = [string]$item; if ($text -and $seen.Add($text)) { $values.Add($text) } }
    }
    $row = Get-ReconciliationMapValue $Fact 'source_row' $null
    if ($row -is [Collections.IDictionary]) {
        foreach ($key in @($row.Keys)) { $text = [string]$row[$key]; if ($text -and $seen.Add($text)) { $values.Add($text) } }
    }
    return @($values.ToArray())
}

function Get-FlowSummarySemanticTerms {
    param([AllowEmptyString()][string]$Text, [AllowEmptyString()][string]$Program)
    $visible = ConvertTo-FlowVisibleInlineText $Text
    $visible = [regex]::Replace($visible, '\b(?:program-analysis(?:-summary)?|source-index|routine-index|message-inventory|routine-logic-details|file-io-inventory|field-mutation-matrix|sql-inventory)\.(?:md|ya?ml)\b', ' ', 'IgnoreCase')
    $visible = [regex]::Replace($visible, '\b(?:RLOG|MSG|LINEAGE|PERSIST|DATA|EXCHAIN|TBD|EV)-[A-Za-z0-9_-]+\b', ' ')
    $terms = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($match in @([regex]::Matches($visible, '[A-Za-z][A-Za-z0-9]{2,}'))) {
        $term = $match.Value
        if (-not [string]::Equals($term, $Program, [StringComparison]::OrdinalIgnoreCase) -and -not [string]::Equals($term, 'SF', [StringComparison]::OrdinalIgnoreCase) -and -not $script:SummarySemanticStopWords.Contains($term)) { [void]$terms.Add($term) }
    }
    return @($terms.ToArray())
}

function Test-FlowSummarySemanticsPreserved {
    param($Fact, [string[]]$MappedTexts)
    $source = [string](Get-ReconciliationMapValue $Fact 'logic' '')
    if (-not $source.Trim()) { $source = [string](Get-ReconciliationMapValue $Fact 'source_text' '') }
    if (-not $source.Trim()) { $source = [string](Get-ReconciliationMapValue $Fact 'description' '') }
    if (-not $source.Trim()) { return $true }
    $program = [string](Get-ReconciliationMapValue $Fact 'program' '')
    $sourceTerms = @(Get-FlowSummarySemanticTerms $source $program); $mappedTerms = @(Get-FlowSummarySemanticTerms (@($MappedTexts) -join ' ') $program)
    if (-not $sourceTerms.Count) { return $mappedTerms.Count -gt 0 }
    $mapped = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase); foreach ($term in $mappedTerms) { [void]$mapped.Add([string]$term) }
    $overlap = @($sourceTerms | Where-Object { $mapped.Contains([string]$_) }).Count
    $required = [Math]::Min(4, [Math]::Max(1, [int][Math]::Floor(($sourceTerms.Count + 4) / 5)))
    return $overlap -ge $required
}

function Get-FlowFactTypedSemanticRequirements {
    param($Fact)
    $type = [string](Get-ReconciliationMapValue $Fact 'fact_type' '')
    $requirements = New-Object System.Collections.Generic.List[object]
    $seen = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    function Add-Requirement {
        param([string]$Field, [string[]]$Headers)
        $value = [string](Get-ReconciliationMapValue $Fact $Field '')
        if (-not $value.Trim() -or $value.Trim().ToLowerInvariant() -in @('-', '--', '---', '—', 'none', 'n/a', 'not applicable')) { return }
        $key = "$Field`t$value"
        if ($seen.Add($key)) { $requirements.Add([pscustomobject]@{ Field = $Field; Value = $value; Headers = @($Headers) }) }
    }
    Add-Requirement 'program' @('Program', 'Program / Routine Sources')
    if ($type -notin @('summary_contribution', 'thematic_prose', 'thematic_table')) {
        Add-Requirement 'routine' @('Routine', 'Program / Routine Sources')
        Add-Requirement 'evidence_status' @('Evidence Status')
    }
    switch ($type) {
        'calculation' {
            Add-Requirement 'calculation' @('Calculation / Assignment')
            Add-Requirement 'target_carrier' @('Target Field / Carrier')
            Add-Requirement 'source_carriers' @('Source Operands / Carriers')
            Add-Requirement 'guard' @('Guard / Branch')
            Add-Requirement 'effect' @('Effect')
            Add-Requirement 'supporting_detail' @('Supporting Detail')
        }
        'validation' {
            Add-Requirement 'description' @('Description')
            if ([string](Get-ReconciliationMapValue $Fact 'trigger_chain' '')) { Add-Requirement 'trigger_chain' @('Condition / Evidence') } else { Add-Requirement 'guard' @('Condition / Evidence') }
            Add-Requirement 'carrier_destination' @('Carrier / Destination')
            Add-Requirement 'effect' @('Effect')
            Add-Requirement 'supporting_detail' @('Supporting Detail')
        }
        'exception' {
            Add-Requirement 'exception_path' @('Exception / Error Path')
            if ([string](Get-ReconciliationMapValue $Fact 'detection_mechanism' '')) { Add-Requirement 'detection_mechanism' @('Detection Mechanism') } else { Add-Requirement 'guard' @('Detection Mechanism') }
            Add-Requirement 'fields_messages_set' @('Fields / Messages Set')
            Add-Requirement 'exception_action' @('Handling Action')
            Add-Requirement 'effect' @('Effect')
            Add-Requirement 'supporting_detail' @('Supporting Detail')
        }
        'message' {
            Add-Requirement 'description' @('Description')
            Add-Requirement 'message_type' @('Type')
            Add-Requirement 'occurrences' @('Occurrences')
            Add-Requirement 'first_seen' @('Detail Refs')
            if ([string](Get-ReconciliationMapValue $Fact 'trigger_handler' '')) { Add-Requirement 'trigger_handler' @('Condition / Handler') } else { Add-Requirement 'generic_handler_token' @('Condition / Handler') }
            Add-Requirement 'carrier_destination' @('Carrier / Destination')
            Add-Requirement 'effect' @('Effect')
        }
    }
    return @($requirements.ToArray())
}

function Get-FlowFactTypedSemanticFindings {
    param($Fact, [object[]]$MappingRows)
    $findings = New-Object System.Collections.Generic.List[string]
    foreach ($requirement in @(Get-FlowFactTypedSemanticRequirements $Fact)) {
        $matched = $false
        foreach ($mapping in @($MappingRows)) {
            $headers = @($mapping.Headers); $cells = @($mapping.Cells)
            foreach ($header in @($requirement.Headers)) {
                $index = [Array]::IndexOf($headers, [string]$header)
                if ($index -ge 0 -and $index -lt $cells.Count -and (Test-FlowExactLiteral ([string]$cells[$index]) ([string]$requirement.Value) -IgnoreCase)) { $matched = $true; break }
            }
            if ($matched) { break }
        }
        if (-not $matched) { $findings.Add("missing source $($requirement.Field) from its typed review column: $($requirement.Value)") }
    }
    return @($findings.ToArray())
}

function Remove-FlowHtmlComments {
    param([AllowEmptyString()][string]$Markdown)
    return Remove-FlowNonRenderedMarkdown $Markdown
}

function Get-FlowVisibleH2Block {
    param([string]$Markdown, [string]$Section)
    $matches = @([regex]::Matches($Markdown, '^##\s+(.+?)\s*$', [Text.RegularExpressions.RegexOptions]::Multiline))
    for ($index = 0; $index -lt $matches.Count; $index++) {
        if ($matches[$index].Groups[1].Value.Trim() -ne $Section) { continue }
        $start = $matches[$index].Index + $matches[$index].Length
        $end = if ($index + 1 -lt $matches.Count) { $matches[$index + 1].Index } else { $Markdown.Length }
        return $Markdown.Substring($start, $end - $start)
    }
    return ''
}

function Get-FlowFactRowHeaders {
    param([string]$Section)
    switch ($Section) {
        'Program Set Reading Summary' { return @('Program', 'Scope / Reader-First Contribution', 'Artifact Readiness', 'Coverage', 'Review Row ID', 'Source Fact Refs') }
        'Calculation Logic' { return @('Calculation / Assignment', 'Program', 'Routine', 'Target Field / Carrier', 'Source Operands / Carriers', 'Guard / Branch', 'Effect', 'Supporting Detail', 'Evidence Status', 'Review Row ID', 'Source Fact Refs') }
        'Validation Logic' { return @('Message / Status / Outcome', 'Description', 'Program', 'Routine', 'Condition / Evidence', 'Carrier / Destination', 'Effect', 'Supporting Detail', 'Evidence Status', 'Review Row ID', 'Source Fact Refs') }
        'Exception Handling' { return @('Exception / Error Path', 'Program', 'Routine', 'Detection Mechanism', 'Fields / Messages Set', 'Handling Action', 'Effect', 'Supporting Detail', 'Evidence Status', 'Review Row ID', 'Source Fact Refs') }
        { $_ -in @('Message Inventory', 'Message Coverage Control') } { return @('Message / Status / Literal', 'Description', 'Type', 'Program / Routine Sources', 'Occurrences', 'Condition / Handler', 'Carrier / Destination', 'Effect', 'Detail Refs', 'Evidence Status', 'Review Row ID', 'Source Fact Refs') }
        default { return @() }
    }
}

function Test-FlowTableSeparatorLine {
    param([AllowEmptyString()][string]$Line)
    return Test-FlowMarkdownTableSeparator $Line
}

function Get-FlowFactMappingRows {
    param([string]$VisibleMarkdown, [string]$Section, [string]$Anchor, [string]$FactId)
    $required = @(Get-FlowFactRowHeaders $Section)
    if (-not $required.Count -or -not $Anchor -or -not $FactId) { return @() }
    $block = Get-FlowVisibleH2Block $VisibleMarkdown $Section
    $lines = @($block -split "`r?`n")
    $matches = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index + 1 -lt $lines.Count; $index++) {
        $headerLine = $lines[$index].Trim()
        if (-not (Test-FlowMarkdownTableHeaderAndSeparator $headerLine $lines[$index + 1])) { continue }
        $headers = @(Split-FlowMarkdownTableRow $headerLine)
        $normalized = @($headers | ForEach-Object { (ConvertTo-FlowVisibleInlineText $_).ToLowerInvariant() })
        if (@($required | Where-Object { $normalized -notcontains $_.ToLowerInvariant() }).Count) { continue }
        $anchorIndex = [Array]::IndexOf($normalized, 'review row id'); $refsIndex = [Array]::IndexOf($normalized, 'source fact refs')
        for ($cursor = $index + 2; $cursor -lt $lines.Count; $cursor++) {
            $rowLine = $lines[$cursor].Trim()
            if (-not ($rowLine.StartsWith('|') -and $rowLine.EndsWith('|'))) { break }
            if (Test-FlowTableSeparatorLine $rowLine) { continue }
            $cells = @(Split-FlowMarkdownTableRow $rowLine)
            if ($cells.Count -ne $headers.Count) { continue }
            $anchorCell = [string]$cells[$anchorIndex]; $refsCell = [string]$cells[$refsIndex]
            $refs = @([regex]::Matches((ConvertTo-FlowVisibleInlineText $refsCell), $script:SourceFactIdPattern) | ForEach-Object { $_.Value })
            if ((Get-FlowAnchorDefinitionCount $anchorCell $Anchor) -gt 0 -and $refs -ccontains $FactId) {
                $matches.Add([pscustomobject]@{ Text = ($cells -join ' | '); Headers = $headers; Cells = $cells })
            }
        }
    }
    return @($matches.ToArray())
}

function Get-FlowVisibleAnchoredProseLines {
    param([string]$VisibleMarkdown, [string]$Section, [string]$Anchor, [string]$FactId)
    $block = Get-FlowVisibleH2Block $VisibleMarkdown $Section
    return @($block -split "`r?`n" | Where-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#') -or $line.StartsWith('|')) { return $false }
        if (-not (Test-FlowExactLiteral $line $FactId) -or (Get-FlowAnchorDefinitionCount $line $Anchor) -lt 1) { return $false }
        $detail = [regex]::Replace($line, '<[^>]+>', ' ').Replace($FactId, ' ')
        return @([regex]::Matches($detail, '[A-Za-z][A-Za-z0-9_-]{2,}')).Count -ge 7
    })
}

function Get-FlowCanonicalReviewRows {
    param([string]$Block, [string]$Section, [string[]]$Required)
    $rows = New-Object System.Collections.Generic.List[object]; $findings = New-Object System.Collections.Generic.List[string]
    $consumed = [Collections.Generic.HashSet[int]]::new(); $lines = @($Block -split "`r?`n"); $requiredLower = @($Required | ForEach-Object { $_.ToLowerInvariant() })
    for ($index = 0; $index + 1 -lt $lines.Count; $index++) {
        $headerLine = $lines[$index].Trim()
        if (-not ($headerLine.StartsWith('|') -and $headerLine.EndsWith('|') -and (Test-FlowTableSeparatorLine $lines[$index + 1]))) { continue }
        $headers = @(Split-FlowMarkdownTableRow $headerLine); $rendered = @($headers | ForEach-Object { ConvertTo-FlowVisibleInlineText $_ }); $normalized = @($rendered | ForEach-Object { $_.ToLowerInvariant() })
        if (@($requiredLower | Where-Object { $normalized -notcontains $_ }).Count) { continue }
        $separatorCells = @(Split-FlowMarkdownTableRow $lines[$index + 1])
        if ($separatorCells.Count -ne $headers.Count) {
            $findings.Add("$Section canonical fact table separator has $($separatorCells.Count) cells; expected exactly $($headers.Count)")
            $cursor = $index + 2
            while ($cursor -lt $lines.Count -and $lines[$cursor].Trim().StartsWith('|') -and $lines[$cursor].Trim().EndsWith('|')) { [void]$consumed.Add($cursor); $cursor++ }
            $index = $cursor - 1; continue
        }
        if (-not (Test-FlowOrdinalSequence $rendered $Required)) { $findings.Add("$Section canonical fact table headers must match the required order exactly") }
        for ($cursor = $index + 2; $cursor -lt $lines.Count; $cursor++) {
            $rowLine = $lines[$cursor].Trim(); if (-not ($rowLine.StartsWith('|') -and $rowLine.EndsWith('|'))) { break }
            if (Test-FlowTableSeparatorLine $rowLine) { continue }
            $cells = @(Split-FlowMarkdownTableRow $rowLine)
            if ($cells.Count -ne $headers.Count) { $findings.Add("$Section canonical fact row must have exactly $($headers.Count) cells"); continue }
            [void]$consumed.Add($cursor); $rows.Add([pscustomobject]@{ Headers = $headers; Cells = $cells })
        }
        $index = $cursor - 1
    }
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $rowLine = $lines[$index].Trim()
        if ($consumed.Contains($index) -or -not ($rowLine.StartsWith('|') -and $rowLine.EndsWith('|')) -or (Test-FlowTableSeparatorLine $rowLine)) { continue }
        $cells = @(Split-FlowMarkdownTableRow $rowLine); $normalized = @($cells | ForEach-Object { (ConvertTo-FlowVisibleInlineText $_).ToLowerInvariant() })
        if ((Test-FlowOrdinalSequence $normalized $requiredLower) -or @($requiredLower | Where-Object { $normalized -notcontains $_ }).Count -eq 0) { continue }
        if ($cells.Count -eq $Required.Count) { $findings.Add("$Section canonical-looking fact row is outside its required table"); $rows.Add([pscustomobject]@{ Headers = $Required; Cells = $cells }) }
    }
    return [pscustomobject]@{ Rows = @($rows.ToArray()); Findings = @($findings.ToArray()) }
}

function Get-FlowReviewRowReconciliationFindings {
    param([string]$Markdown, $FactById, $ItemById, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]; $visible = Remove-FlowHtmlComments $Markdown
    $profile = Get-ReconciliationMapValue $Manifest 'core_review_profile' ([ordered]@{}); $messageSection = if ([bool](Get-ReconciliationMapValue $profile 'include_message_inventory' $true)) { 'Message Inventory' } else { 'Message Coverage Control' }
    foreach ($section in @('Program Set Reading Summary', 'Calculation Logic', 'Validation Logic', 'Exception Handling', $messageSection)) {
        $required = @(Get-FlowFactRowHeaders $section); $scan = Get-FlowCanonicalReviewRows (Get-FlowVisibleH2Block $visible $section) $section $required
        foreach ($finding in @($scan.Findings)) { $findings.Add($finding) }; $rowNumber = 0
        foreach ($record in @($scan.Rows)) {
            $rowNumber++; $headers = @($record.Headers); $cells = @($record.Cells); $normalized = @($headers | ForEach-Object { (ConvertTo-FlowVisibleInlineText $_).ToLowerInvariant() }); $label = "$section canonical fact row $rowNumber"
            $anchorIndex = [Array]::IndexOf($normalized, 'review row id'); $refsIndex = [Array]::IndexOf($normalized, 'source fact refs')
            $rawRefs = @([regex]::Matches((ConvertTo-FlowVisibleInlineText ([string]$cells[$refsIndex])), $script:SourceFactIdPattern) | ForEach-Object { $_.Value }); $refs = @($rawRefs | Select-Object -Unique)
            if (-not $refs.Count) { $findings.Add("$label requires visible source fact references") }
            if ($refs.Count -ne $rawRefs.Count) { $findings.Add("$label repeats a source fact reference") }
            $anchors = @(Get-FlowVisibleAnchorIds ([string]$cells[$anchorIndex])); $anchor = if ($anchors.Count -eq 1) { $anchors[0] } else { '' }
            if (-not $anchor) { $findings.Add("$label requires one visible review anchor") } elseif ((Get-FlowAnchorDefinitionCount $visible $anchor) -ne 1) { $findings.Add("$label review anchor $anchor must be defined exactly once") }
            foreach ($factId in $refs) {
                if (-not $FactById.ContainsKey($factId)) { $findings.Add("$label references unknown source fact $factId"); continue }
                $fact = $FactById[$factId]; $sourceSection = [string](Get-ReconciliationMapValue $fact 'section' ''); $expectedSection = if ($sourceSection -eq 'Program Reading Summary') { 'Program Set Reading Summary' } elseif ($sourceSection -eq 'Message Inventory') { $messageSection } else { $sourceSection }
                if ($expectedSection -cne $section) { $findings.Add("$label maps $factId from $expectedSection into the wrong section") }
                if (-not $ItemById.ContainsKey($factId)) { $findings.Add("$label source fact $factId has no coverage mapping"); continue }
                $item = $ItemById[$factId]; $status = [string](Get-ReconciliationMapValue $item 'status' '')
                if ($status -notin @('included', 'merged')) { $findings.Add("$label source fact $factId is not included or merged") }
                if (-not $anchor -or -not [string]::Equals([string](Get-ReconciliationMapValue $item 'review_anchor' ''), $anchor, [StringComparison]::Ordinal)) { $findings.Add("$label anchor does not match coverage for source fact $factId") }
            }
        }
    }
    return @($findings.ToArray())
}

function Test-FlowPreparedBundleIntegrity {
    param($Facts, [string]$SourcePack, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $revalidated = Get-FlowRevalidatedManifest $Manifest
    foreach ($finding in @(Get-ReconciliationMapValue $revalidated 'Findings' @())) { $findings.Add($finding) }
    $trustedManifest = Get-ReconciliationMapValue $revalidated 'Manifest' $Manifest
    try { $expected = New-FlowReaderFirstBundle $trustedManifest }
    catch { return @("cannot regenerate reader-first preparation bundle: $($_.Exception.Message)") }
    $expectedPack = ([string]$expected.SourcePack).Replace("`r`n", "`n")
    if ($expectedPack -cne $SourcePack.Replace("`r`n", "`n")) { $findings.Add('source pack differs from the current validated program-analysis inputs') }
    $expectedById = [Collections.Hashtable]::new([StringComparer]::Ordinal)
    foreach ($fact in @($expected.Facts.source_facts)) { $expectedById[[string]$fact.source_fact_id] = $fact }
    $actualById = [Collections.Hashtable]::new([StringComparer]::Ordinal)
    foreach ($fact in @(Get-ReconciliationMapValue $Facts 'source_facts' @())) {
        $id = [string](Get-ReconciliationMapValue $fact 'source_fact_id' '')
        if ($id) { $actualById[$id] = $fact }
    }
    $nestedCounts = [Collections.Hashtable]::new([StringComparer]::Ordinal)
    foreach ($programEntry in @(Get-ReconciliationMapValue $Facts 'programs' @())) {
        $outerProgram = [string](Get-ReconciliationMapValue $programEntry 'program' '')
        $buckets = Get-ReconciliationMapValue $programEntry 'facts' $null
        if ($buckets -isnot [Collections.IDictionary]) { $findings.Add("normalized facts program $outerProgram has no facts bucket mapping"); continue }
        foreach ($bucketName in @($buckets.Keys)) {
            foreach ($nestedFact in @($buckets[$bucketName])) {
                $nestedId = [string](Get-ReconciliationMapValue $nestedFact 'source_fact_id' '')
                if (-not $nestedId) { $findings.Add("normalized facts program $outerProgram has a nested fact without source_fact_id"); continue }
                $nestedCounts[$nestedId] = [int](Get-ReconciliationMapValue $nestedCounts $nestedId 0) + 1
                if (-not $actualById.ContainsKey($nestedId)) { $findings.Add("nested normalized fact $nestedId is absent from canonical source_facts"); continue }
                if ([string](Get-ReconciliationMapValue $nestedFact 'program' '') -cne $outerProgram) { $findings.Add("nested normalized fact $nestedId does not match its programs[] identity") }
                if ((ConvertTo-FlowYamlText $nestedFact) -cne (ConvertTo-FlowYamlText $actualById[$nestedId])) { $findings.Add("nested normalized fact $nestedId differs from canonical source_facts") }
            }
        }
    }
    foreach ($id in $actualById.Keys) {
        $nestedCount = [int](Get-ReconciliationMapValue $nestedCounts $id 0)
        if ($nestedCount -ne 1) { $findings.Add("canonical source fact $id must occur exactly once in programs[].facts; found $nestedCount") }
    }
    foreach ($id in $expectedById.Keys) {
        if (-not $actualById.ContainsKey($id)) { $findings.Add("source-pack fact $id is missing from normalized core facts"); continue }
        if ((ConvertTo-FlowYamlText $expectedById[$id]) -cne (ConvertTo-FlowYamlText $actualById[$id])) { $findings.Add("normalized core fact $id differs from the validated source input") }
    }
    foreach ($id in $actualById.Keys) { if (-not $expectedById.ContainsKey($id)) { $findings.Add("normalized core fact $id is not derivable from the validated source input") } }
    return @($findings.ToArray())
}

Export-ModuleMember -Function Test-FlowExactLiteral, ConvertTo-FlowVisibleInlineText, Get-FlowAnchorDefinitionCount, Get-FlowVisibleAnchorIds, Get-FlowH1IdentityFindings, Test-FlowBundleLayout, Get-FlowFactSemanticValues, Test-FlowSummarySemanticsPreserved, Get-FlowFactTypedSemanticFindings, Remove-FlowHtmlComments, Get-FlowFactMappingRows, Get-FlowVisibleAnchoredProseLines, Get-FlowReviewRowReconciliationFindings, Test-FlowProgramListSnapshot, Test-FlowCurrentProgramReadiness, Test-FlowPreparedBundleIntegrity
