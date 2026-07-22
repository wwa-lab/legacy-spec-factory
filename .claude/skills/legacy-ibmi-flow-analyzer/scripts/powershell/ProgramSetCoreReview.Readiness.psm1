<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Artifact readiness gates for the native Windows PowerShell 5.1 preparer.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'FlowYaml.psm1') -Force

$skillsRoot = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$upstreamValidationModule = Join-Path $skillsRoot 'legacy-ibmi-program-analyzer/scripts/powershell/ProgramAnalysisContract.Validation.psm1'
if (-not (Test-Path -LiteralPath $upstreamValidationModule -PathType Leaf)) {
    throw "Upstream program-analysis validator module not found: $upstreamValidationModule"
}
Import-Module $upstreamValidationModule -Force

function Get-ReadinessMapValue {
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

function Get-ReadinessArtifactKey {
    param([Parameter(Mandatory = $true)][string]$Filename)
    return $Filename.Replace('-', '_').Replace('.', '_')
}

function Assert-ReadinessTrustedPath {
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$Path)
    $rootFull = [IO.Path]::GetFullPath($Root)
    if ($rootFull -ne [IO.Path]::GetPathRoot($rootFull)) { $rootFull = $rootFull.TrimEnd([char[]]@('/', '\')) }
    $pathFull = [IO.Path]::GetFullPath($Path)
    $rootBoundary = if ($rootFull.EndsWith([string][IO.Path]::DirectorySeparatorChar)) { $rootFull } else { $rootFull + [IO.Path]::DirectorySeparatorChar }
    if (-not ($pathFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase) -or $pathFull.StartsWith($rootBoundary, [StringComparison]::OrdinalIgnoreCase))) { throw "artifact path escapes the configured root: $pathFull" }
    $relative = if ($pathFull.Length -eq $rootFull.Length) { '' } else { $pathFull.Substring($rootBoundary.Length) }
    $current = $rootFull
    $parts = @('') + @($relative -split '[\\/]' | Where-Object { $_ })
    foreach ($part in $parts) {
        if ($part) { $current = Join-Path $current $part }
        if ((Test-Path -LiteralPath $current) -and (([IO.File]::GetAttributes($current) -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw "artifact trust path contains a symlink/junction/reparse point: $current" }
    }
    return $pathFull
}

function Get-ReadinessArtifactPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        $CompactArtifacts,
        [Parameter(Mandatory = $true)][string]$Filename
    )
    $artifact = Get-ReadinessMapValue $CompactArtifacts (Get-ReadinessArtifactKey $Filename) ([ordered]@{})
    if ((Get-ReadinessMapValue $artifact 'status' 'missing') -ne 'present') { return $null }
    $path = [string](Get-ReadinessMapValue $artifact 'path' '')
    if (-not $path) { return $null }
    $resolved = if ([IO.Path]::IsPathRooted($path)) { [IO.Path]::GetFullPath($path) } else { [IO.Path]::GetFullPath((Join-Path $Root $path)) }
    return Assert-ReadinessTrustedPath $Root $resolved
}

function Get-ReadinessRelativePath {
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$Path)
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd([char[]]@('/', '\'))
    $pathFull = [IO.Path]::GetFullPath($Path)
    if ($pathFull.StartsWith($rootFull + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        return $pathFull.Substring($rootFull.Length + 1).Replace('\', '/')
    }
    if ($pathFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase)) { return '.' }
    return $pathFull.Replace('\', '/')
}

function Read-ReadinessStructuredFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    $text = [IO.File]::ReadAllText($Path)
    if ($text.TrimStart().StartsWith('{')) { return $text | ConvertFrom-Json }
    return Read-FlowYamlFile $Path
}

function Get-ReadinessProgramIdentityFindings {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Program,
        $CompactArtifacts
    )
    $findings = New-Object System.Collections.Generic.List[string]
    $analysisPath = Get-ReadinessArtifactPath $Root $CompactArtifacts 'program-analysis.md'
    if (-not $analysisPath) { return @() }
    $markdown = [IO.File]::ReadAllText($analysisPath)
    $title = [regex]::Match($markdown, '(?m)^#\s+Program Analysis:\s*(.+?)\s*$')
    if (-not $title.Success) {
        $findings.Add('program identity is missing from the Program Analysis H1')
    }
    else {
        $actual = [regex]::Replace($title.Groups[1].Value.Trim(), '\s+\([^)]*\)\s*$', '').Trim([char[]]@(' ', '`'))
        if (-not $actual.Equals($Program, [StringComparison]::Ordinal)) {
            $findings.Add("program identity mismatch in Program Analysis H1: expected $Program, found $(if ($actual) { $actual } else { 'missing' })")
        }
    }

    $metadata = [regex]::Match($markdown, '(?ms)^##\s+Metadata\s*$\s*(.*?)(?=^##\s+|\z)')
    if ($metadata.Success) {
        $metadataProgram = [regex]::Match($metadata.Groups[1].Value, '(?m)^\|\s*Program\s*\|\s*([^|]+?)\s*\|\s*$')
        if ($metadataProgram.Success) {
            $actual = $metadataProgram.Groups[1].Value.Trim([char[]]@(' ', '`'))
            if (-not $actual.Equals($Program, [StringComparison]::Ordinal)) {
                $findings.Add("program identity mismatch in Metadata: expected $Program, found $(if ($actual) { $actual } else { 'missing' })")
            }
        }
    }

    foreach ($filename in @('program-analysis-summary.yaml', 'source-index.yaml', 'routine-logic-details.yaml', 'message-inventory.yaml')) {
        $path = Get-ReadinessArtifactPath $Root $CompactArtifacts $filename
        if (-not $path) { continue }
        $payload = Read-ReadinessStructuredFile $path
        $actualValue = Get-ReadinessMapValue $payload 'program' $null
        if ($null -eq $actualValue -or -not ([string]$actualValue).Trim()) { continue }
        $actual = ([string]$actualValue).Trim()
        if (-not $actual.Equals($Program, [StringComparison]::Ordinal)) {
            $findings.Add("program identity mismatch in $([IO.Path]::GetFileName($path)): expected $Program, found $actual")
        }
    }
    return @($findings.ToArray())
}

function Get-ReadinessTerminalStatusEvidence {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        $CompactArtifacts
    )
    $summaryStatus = $null
    $summaryPath = Get-ReadinessArtifactPath $Root $CompactArtifacts 'program-analysis-summary.yaml'
    if ($summaryPath) {
        $payload = Read-ReadinessStructuredFile $summaryPath
        foreach ($key in @('analysis_status', 'review_status', 'status')) {
            $value = Get-ReadinessMapValue $payload $key $null
            if ($null -ne $value -and ([string]$value).Trim()) {
                $summaryStatus = ([string]$value).Trim().ToLowerInvariant()
                break
            }
        }
    }

    $statuses = New-Object System.Collections.Generic.List[string]
    $seenStatuses = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
    $analysisPath = Get-ReadinessArtifactPath $Root $CompactArtifacts 'program-analysis.md'
    if ($analysisPath) {
        $markdown = [IO.File]::ReadAllText($analysisPath)
        foreach ($pattern in @(
            '(?m)^\s*\*\*Status:\*\*\s*`?([A-Za-z0-9_-]+)`?\s*$',
            '(?m)^\|\s*Analysis Status\s*\|\s*`?([A-Za-z0-9_-]+)`?\s*\|\s*$'
        )) {
            foreach ($match in [regex]::Matches($markdown, $pattern)) {
                $value = $match.Groups[1].Value.Trim().ToLowerInvariant()
                if ($seenStatuses.Add($value)) { $statuses.Add($value) }
            }
        }
    }

    $findings = New-Object System.Collections.Generic.List[string]
    if ($statuses.Count -gt 1) {
        $findings.Add('conflicting program analysis terminal statuses in Markdown: ' + (@($statuses.ToArray()) -join ', '))
    }
    $markdownStatus = if ($statuses.Count) { $statuses[0] } else { $null }
    if ($summaryStatus -and $markdownStatus -and $summaryStatus -ne $markdownStatus) {
        $findings.Add("conflicting program analysis terminal statuses: summary=$summaryStatus, markdown=$markdownStatus")
    }
    return [ordered]@{
        analysis_status = $(if ($summaryStatus) { $summaryStatus } else { $markdownStatus })
        findings = @($findings.ToArray())
    }
}

function Get-FlowProgramArtifactReadiness {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [AllowNull()][string]$ArtifactRoot,
        [Parameter(Mandatory = $true)][string]$Program,
        $CompactArtifacts,
        [string[]]$AmbiguousMatches = @(),
        [AllowNull()][string]$ExpectedSizeTier,
        [Parameter(Mandatory = $true)][string[]]$RequiredArtifacts
    )
    $findings = New-Object System.Collections.Generic.List[string]
    if (-not $ArtifactRoot) { $findings.Add('program analysis artifact directory is missing') }
    if (@($AmbiguousMatches).Count -gt 1) {
        $findings.Add('artifact folder resolution is ambiguous: ' + (@($AmbiguousMatches) -join ', '))
    }
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($filename in $RequiredArtifacts) {
        $artifact = Get-ReadinessMapValue $CompactArtifacts (Get-ReadinessArtifactKey $filename) ([ordered]@{})
        if ((Get-ReadinessMapValue $artifact 'status' 'missing') -ne 'present') { $missing.Add($filename) }
    }
    if ($missing.Count) { $findings.Add('missing required artifacts: ' + (@($missing.ToArray()) -join ', ')) }

    $pathsTrusted = $true; $trustedArtifactRoot = $null
    if ($ArtifactRoot) {
        try {
            $candidateRoot = if ([IO.Path]::IsPathRooted($ArtifactRoot)) { $ArtifactRoot } else { Join-Path $Root $ArtifactRoot }
            $trustedArtifactRoot = Assert-ReadinessTrustedPath $Root $candidateRoot
            foreach ($filename in $RequiredArtifacts) { [void](Get-ReadinessArtifactPath $Root $CompactArtifacts $filename) }
        }
        catch { $pathsTrusted = $false; $findings.Add("artifact trust validation failed: $($_.Exception.Message)") }
    }
    $programAnalysis = if ($pathsTrusted) { Get-ReadinessArtifactPath $Root $CompactArtifacts 'program-analysis.md' } else { $null }
    $analysisStatus = $null
    $upstreamRan = $false
    $upstreamFindings = New-Object System.Collections.Generic.List[string]
    if ($ArtifactRoot -and $programAnalysis -and $missing.Count -eq 0 -and @($AmbiguousMatches).Count -le 1) {
        $upstreamRan = $true
        $analysisDirectory = $trustedArtifactRoot
        try {
            foreach ($finding in @(Invoke-ContractValidation $analysisDirectory $programAnalysis $ExpectedSizeTier)) {
                $upstreamFindings.Add([string]$finding)
                $findings.Add("upstream validator: $finding")
            }
        }
        catch {
            $upstreamFindings.Add($_.Exception.Message)
            $findings.Add("upstream validator execution failed: $($_.Exception.Message)")
        }
        foreach ($finding in @(Get-ReadinessProgramIdentityFindings $Root $Program $CompactArtifacts)) { $findings.Add($finding) }
        $statusEvidence = Get-ReadinessTerminalStatusEvidence $Root $CompactArtifacts
        $analysisStatus = Get-ReadinessMapValue $statusEvidence 'analysis_status' $null
        foreach ($finding in @(Get-ReadinessMapValue $statusEvidence 'findings' @())) { $findings.Add([string]$finding) }
        if ($analysisStatus -notin @('approved', 'approved_with_non_blocking_tbd')) {
            $foundStatus = if ($analysisStatus) { $analysisStatus } else { 'missing' }
            $findings.Add("program analysis terminal status must be approved or approved_with_non_blocking_tbd; found $foundStatus")
        }
        $markdown = [IO.File]::ReadAllText($programAnalysis)
        if ([regex]::IsMatch($markdown, '(?im)\b(?:pending_deep_read|batch_status\s*[:|]\s*(?:pending|in_progress)|validator_status\s*[:|]\s*(?:pending|failed))\b')) {
            $findings.Add('program analysis contains a non-terminal deep-read or validator status')
        }
    }

    $ready = $ArtifactRoot -and $programAnalysis -and $findings.Count -eq 0
    return [ordered]@{
        status = $(if ($ready) { 'ready' } else { 'not_ready' })
        validator = 'legacy-ibmi-program-analyzer/Invoke-ContractValidation'
        validator_status = $(if (-not $upstreamRan) { 'not_run' } elseif ($upstreamFindings.Count) { 'failed' } else { 'passed' })
        analysis_status = $analysisStatus
        candidate_artifact_root = $ArtifactRoot
        validated_program_analysis = $(if ($programAnalysis) { Get-ReadinessRelativePath $Root $programAnalysis } else { $null })
        findings = @($findings.ToArray())
    }
}

Export-ModuleMember -Function Get-FlowProgramArtifactReadiness, Assert-ReadinessTrustedPath
