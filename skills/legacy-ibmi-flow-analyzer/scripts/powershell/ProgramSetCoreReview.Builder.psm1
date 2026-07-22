<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Native Windows PowerShell 5.1 preparation module for the controlled LLM
reader-first program-analysis merger. Deterministic code validates and packages
source material; it never creates a skeleton or formal SME core review.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'FlowYaml.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Markdown.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Identity.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Input.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Readiness.psm1') -Force

$script:RequiredArtifacts = @(
    'program-analysis.md',
    'program-analysis-summary.yaml',
    'source-index.yaml',
    'routine-index.md',
    'message-inventory.yaml',
    'routine-logic-details.md',
    'routine-logic-details.yaml'
)
$script:OptionalArtifacts = @(
    'file-io-inventory.yaml',
    'field-mutation-matrix.yaml',
    'sql-inventory.yaml'
)
$script:SourceReadingSections = @(
    'Program Reading Summary', 'Calculation Logic', 'Validation Logic',
    'Exception Handling', 'Message Inventory'
)
$script:CoreReadingSections = @(
    'Program Set Reading Summary', 'Cross-Program Processing Overview',
    'Calculation Logic', 'Validation Logic', 'Exception Handling'
)
$script:CoreFactsFilename = 'program-set-core-facts.yaml'
$script:ManifestFilename = 'program-set-core-input-manifest.yaml'
$script:ReadinessFilename = 'program-set-artifact-readiness.yaml'
$script:SourcePackFilename = 'program-set-reader-first-source-pack.md'
$script:CoverageFilename = 'program-set-core-coverage.yaml'
$script:ProgramListFilename = 'program-list.txt'
$script:GeneratorVersion = '0.4.0'
$script:TemplateVersion = '0.4.0'
$script:Utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false

function Get-FlowMapValue {
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

function Get-FlowProfileSection {
    param($Config, [Parameter(Mandatory = $true)][string]$Primary, [string]$Fallback)
    $value = Get-FlowMapValue $Config $Primary
    if ($null -eq $value -and $Fallback) { $value = Get-FlowMapValue $Config $Fallback }
    if ($null -eq $value) { return [ordered]@{} }
    return $value
}

function Get-FlowCoreReviewProfile {
    param($Config, [AllowNull()][string]$RequestedName)
    $defaultProfile = Get-FlowMapValue $Config 'core_review_profile' ([ordered]@{})
    $name = if ($RequestedName) { $RequestedName } else { [string](Get-FlowMapValue $defaultProfile 'name' 'standard_reader_first') }
    if ($name -notin @('standard_reader_first', 'minimal_reader_first')) {
        throw "unsupported core review profile: $name"
    }
    $profiles = Get-FlowMapValue $Config 'core_review_profiles' ([ordered]@{})
    $selected = Get-FlowMapValue $profiles $name $null
    if ($null -eq $selected) {
        $selected = if ($name -eq [string](Get-FlowMapValue $defaultProfile 'name' '')) { $defaultProfile } else { [ordered]@{} }
    }
    $includeMessages = [bool](Get-FlowMapValue $selected 'include_message_inventory' ($name -eq 'standard_reader_first'))
    $sections = @(Get-FlowMapValue $selected 'core_sections' @($script:CoreReadingSections))
    if ($sections.Count -eq 0) { $sections = @($script:CoreReadingSections) }
    if ($includeMessages -and $sections -notcontains 'Message Inventory') { $sections += 'Message Inventory' }
    return [ordered]@{
        name = $name
        core_sections = $sections
        include_message_inventory = $includeMessages
        include_audit_sections = [bool](Get-FlowMapValue $selected 'include_audit_sections' $true)
        message_coverage_section = [string](Get-FlowMapValue $selected 'message_coverage_section' $(if ($includeMessages) { 'Message Inventory' } else { 'Message Coverage Control' }))
        retain_all_message_facts = [bool](Get-FlowMapValue $selected 'retain_all_message_facts' $true)
    }
}

function ConvertTo-FlowArtifactKey {
    param([Parameter(Mandatory = $true)][string]$Filename)
    return $Filename.Replace('-', '_').Replace('.', '_')
}

function ConvertTo-FlowReviewSlug {
    param([Parameter(Mandatory = $true)][string]$Value)
    $slug = [regex]::Replace($Value.Trim().ToLowerInvariant(), '[^a-z0-9]+', '_').Trim('_')
    if ($slug) { return $slug }
    return 'program_set_review'
}

function Get-FlowIdentitySlug {
    param([Parameter(Mandatory = $true)][string]$Value)
    $readable = ConvertTo-FlowReviewSlug $Value
    if ($readable.Length -gt 64) { $readable = $readable.Substring(0, 64).Trim('_') }
    if (-not $readable) { $readable = 'program_set_review' }
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        $digest = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant().Substring(0, 8)
    }
    finally { $sha.Dispose() }
    return "${readable}_${digest}"
}

function Get-FlowProgramSetIdentitySlug {
    param([string[]]$Programs)
    $identityValues = @($Programs | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | ForEach-Object { ([string]$_).Trim().ToUpperInvariant() } | Sort-Object -Unique)
    if ($identityValues.Count -eq 0) { return 'program_set_review' }
    $readable = ($identityValues | ForEach-Object { ConvertTo-FlowReviewSlug $_ }) -join '_'
    if ($readable.Length -gt 64) { $readable = $readable.Substring(0, 64).Trim('_') }
    if (-not $readable) { $readable = 'programs' }
    $identity = [string]::Join("`n", $identityValues)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($identity)
        $digest = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant().Substring(0, 8)
    }
    finally { $sha.Dispose() }
    return "program_set_${readable}_${digest}"
}

function Get-FlowRelativePath {
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$Path)
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd([char[]]@('/', '\'))
    $pathFull = [IO.Path]::GetFullPath($Path)
    if ($pathFull.StartsWith($rootFull + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        return $pathFull.Substring($rootFull.Length + 1).Replace('\', '/')
    }
    if ($pathFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase)) { return '.' }
    return $pathFull.Replace('\', '/')
}

function Read-FlowProgramsFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    return @(Read-FlowProgramsFileInput $Path)
}

function Normalize-FlowProgramName {
    param([Parameter(Mandatory = $true)][string]$Program, $LookupProfile)
    return Normalize-FlowProgramNameInput $Program $LookupProfile
}

function Convert-FlowWildcardToRegex {
    param([Parameter(Mandatory = $true)][string]$Pattern)
    $escaped = [regex]::Escape($Pattern.Replace('\', '/'))
    return '^' + $escaped.Replace('\*', '[^/]*').Replace('\?', '[^/]') + '$'
}

function Find-FlowProgramArtifactRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Program,
        $LookupProfile
    )
    Assert-FlowProgramName $Program | Out-Null
    $patterns = @(Get-FlowMapValue $LookupProfile 'program_folder_patterns' @('modules/*/{PROGRAM}'))
    $directories = @()
    if (Test-Path -LiteralPath $Root -PathType Container) {
        $directories = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force -ErrorAction Stop)
    }
    $matches = New-Object System.Collections.Generic.List[string]
    foreach ($pattern in $patterns) {
        $resolved = ([string]$pattern).Replace('{PROGRAM}', $Program)
        $regex = Convert-FlowWildcardToRegex $resolved
        foreach ($directory in $directories) {
            $relative = Get-FlowRelativePath $Root $directory.FullName
            if ($relative -cmatch $regex -or $relative -match $regex) { $matches.Add($relative) }
        }
    }
    $unique = @($matches.ToArray() | Sort-Object -Unique)
    return [ordered]@{ Root = $(if ($unique.Count) { $unique[0] } else { $null }); Matches = $unique }
}

function Get-FlowArtifactStatuses {
    param([Parameter(Mandatory = $true)][string]$Root, [AllowNull()][string]$ArtifactRoot, [AllowNull()][string]$Program)
    $statuses = [ordered]@{}
    foreach ($filename in @($script:RequiredArtifacts + $script:OptionalArtifacts)) {
        $key = ConvertTo-FlowArtifactKey $filename
        $prefix = if ($Program) { ([regex]::Replace($Program.Trim().ToUpperInvariant(), '[\s<>:"/\\|?*]+', '_')).Trim('._-') + '-' } else { '' }
        if (-not $ArtifactRoot) {
            $statuses[$key] = [ordered]@{ path = $(if ($prefix) { $prefix + $filename } else { $filename }); status = 'missing' }
            continue
        }
        $artifactPath = Join-Path $Root $ArtifactRoot
        $candidates = @(
            $(if ($prefix) { Join-Path $artifactPath ($prefix + $filename) }),
            Join-Path $artifactPath $filename
        ) | Where-Object { $_ }
        $candidate = @($candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })[0]
        if (-not $candidate) { $candidate = $candidates[0] }
        $statuses[$key] = [ordered]@{
            path = Get-FlowRelativePath $Root $candidate
            status = $(if (Test-Path -LiteralPath $candidate -PathType Leaf) { 'present' } else { 'missing' })
        }
    }
    return $statuses
}

function Get-FlowArtifactAbsolutePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        $CompactArtifacts,
        [Parameter(Mandatory = $true)][string]$Filename
    )
    $artifact = Get-FlowMapValue $CompactArtifacts (ConvertTo-FlowArtifactKey $Filename) ([ordered]@{})
    if ((Get-FlowMapValue $artifact 'status' 'missing') -ne 'present') { return $null }
    $path = [string](Get-FlowMapValue $artifact 'path' '')
    if (-not $path) { return $null }
    $resolved = if ([IO.Path]::IsPathRooted($path)) { [IO.Path]::GetFullPath($path) } else { [IO.Path]::GetFullPath((Join-Path $Root $path)) }
    return Assert-ReadinessTrustedPath $Root $resolved
}
function Get-FlowArtifactReadiness {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [AllowNull()][string]$ArtifactRoot,
        [Parameter(Mandatory = $true)][string]$Program,
        $CompactArtifacts,
        [string[]]$AmbiguousMatches = @(),
        [AllowNull()][string]$ExpectedSizeTier
    )
    return Get-FlowProgramArtifactReadiness -Root $Root -ArtifactRoot $ArtifactRoot -Program $Program `
        -CompactArtifacts $CompactArtifacts -AmbiguousMatches $AmbiguousMatches `
        -ExpectedSizeTier $ExpectedSizeTier `
        -RequiredArtifacts $script:RequiredArtifacts
}
function Get-FlowProgramTier {
    param([AllowNull()][string]$ArtifactRoot, $WorkspaceProfile)
    if (-not $ArtifactRoot) { return $null }
    $tierRoots = Get-FlowMapValue $WorkspaceProfile 'program_tier_roots' ([ordered]@{})
    if ($tierRoots -is [System.Collections.IDictionary]) {
        foreach ($tier in $tierRoots.Keys) {
            $tierRoot = ([string]$tierRoots[$tier]).TrimEnd('/')
            if ($ArtifactRoot -eq $tierRoot -or $ArtifactRoot.StartsWith($tierRoot + '/')) { return [string]$tier }
        }
    }
    foreach ($tier in @('large_extreme_program', 'complex_normal_program', 'normal_program')) {
        if ($ArtifactRoot.Contains($tier)) { return $tier }
    }
    return $null
}

function New-FlowProgramEntries {
    param(
        [Parameter(Mandatory = $true)][string[]]$Programs,
        [Parameter(Mandatory = $true)][string]$ArtifactRoot,
        $Config,
        [Parameter(Mandatory = $true)][string]$ArtifactRepoMode
    )
    $lookup = Get-FlowProfileSection $Config 'program_artifact_resolution_profile' 'delivery_artifact_lookup_profile'
    $workspace = Get-FlowProfileSection $Config 'delivery_workspace_profile'
    $approved = $ArtifactRepoMode -eq 'approved_document_repo'
    $entries = New-Object System.Collections.Generic.List[object]
    $warnings = New-Object System.Collections.Generic.List[string]
    $seen = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $Programs.Count; $index++) {
        $inputName = $Programs[$index]
        $normalized = Normalize-FlowProgramName $inputName $lookup
        if ($seen.ContainsKey($normalized)) {
            $first = $seen[$normalized]
            $ready = (Get-FlowMapValue $first.artifact_readiness 'status' 'not_ready') -eq 'ready'
            $warnings.Add("Duplicate normalized program name '$normalized'; reusing the readiness decision from order $($first.order)")
            $entries.Add([ordered]@{
                input_name = $inputName
                normalized_name = $normalized
                order = $index + 1
                run_resolution = $(if ($ready) { $(if ($approved) { 'reused_artifact_repo' } else { 'reused_same_run' }) } else { $first.run_resolution })
                artifact_root = $first.artifact_root
                candidate_artifact_root = $first.candidate_artifact_root
                artifact_source = $first.artifact_source
                tier = $first.tier
                compact_artifacts = $first.compact_artifacts
                artifact_readiness = $first.artifact_readiness
                follow_up = $(if ($ready) { 'none - reused validated artifact decision' } else { $first.follow_up })
            })
            continue
        }
        $found = Find-FlowProgramArtifactRoot $ArtifactRoot $normalized $lookup
        if (@($found.Matches).Count -gt 1) {
            $warnings.Add("Program $normalized matched multiple artifact folders and is blocked until the ambiguity is resolved: " + (@($found.Matches) -join ', '))
        }
        $hasArtifact = $null -ne $found.Root
        $compactArtifacts = Get-FlowArtifactStatuses $ArtifactRoot $found.Root $normalized
        $tier = Get-FlowProgramTier $found.Root $workspace
        $readiness = Get-FlowArtifactReadiness -Root $ArtifactRoot -ArtifactRoot $found.Root -Program $normalized -CompactArtifacts $compactArtifacts -AmbiguousMatches @($found.Matches) -ExpectedSizeTier $tier
        $usableArtifact = $readiness.status -eq 'ready'
        $entry = [ordered]@{
            input_name = $inputName
            normalized_name = $normalized
            order = $index + 1
            run_resolution = $(if ($usableArtifact) { $(if ($approved) { 'reused_artifact_repo' } else { 'analyzed_this_run' }) } else { 'pending_source' })
            artifact_root = $(if ($usableArtifact) { $found.Root } else { $null })
            candidate_artifact_root = $found.Root
            artifact_source = $(if ($usableArtifact) { $(if ($approved) { 'approved_document_repo' } else { 'delivery_working_branch' }) } else { 'source_scan_required' })
            tier = $tier
            compact_artifacts = $compactArtifacts
            artifact_readiness = $readiness
            follow_up = $(if ($usableArtifact) {
                $pending = @(Get-FlowMapValue $readiness 'pending_findings' @())
                if ($pending.Count) { 'core reader-first gate passed; carry non-core readiness items as pending: ' + ($pending -join '; ') }
                else { 'none - core reader-first readiness gate passed' }
            } elseif ($hasArtifact) { 'refresh only this program analysis until core reader-first findings are resolved' } elseif ($approved) { 'add or refresh this program in the approved document repo' } else { 'scan only this program in the current run' })
        }
        $entries.Add($entry)
        $seen[$normalized] = $entry
    }
    return [ordered]@{ Entries = $entries.ToArray(); Warnings = $warnings.ToArray() }
}

function Quote-FlowProcessArgument {
    param([AllowEmptyString()][string]$Value)
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Invoke-FlowGit {
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string[]]$Arguments)
    $start = New-Object Diagnostics.ProcessStartInfo
    $start.FileName = 'git'
    $allArguments = @('-C', $Root) + $Arguments
    $start.Arguments = (@($allArguments | ForEach-Object { Quote-FlowProcessArgument ([string]$_) }) -join ' ')
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.CreateNoWindow = $true
    try {
        $process = [Diagnostics.Process]::Start($start)
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        return [ordered]@{ ExitCode = $process.ExitCode; StdOut = $stdout; StdErr = $stderr }
    }
    catch { return [ordered]@{ ExitCode = 127; StdOut = ''; StdErr = $_.Exception.Message } }
}

function Get-FlowSourceRevision {
    param([Parameter(Mandatory = $true)][string]$SourceRoot, [AllowNull()][string]$IgnorePath)
    $top = Invoke-FlowGit $SourceRoot @('rev-parse', '--show-toplevel')
    if ($top.ExitCode -ne 0) {
        $resolved = [IO.Path]::GetFullPath($SourceRoot)
        return [ordered]@{ type = 'filesystem'; root = $resolved; head = $null; short_head = $null; dirty = $null; key = "filesystem:$resolved"; freshness_note = 'No Git metadata was available; inventory freshness cannot be proven.' }
    }
    $gitRoot = $top.StdOut.Trim()
    $head = Invoke-FlowGit $gitRoot @('rev-parse', 'HEAD')
    $short = Invoke-FlowGit $gitRoot @('rev-parse', '--short=12', 'HEAD')
    if ($head.ExitCode -ne 0) {
        return [ordered]@{ type = 'git'; root = $gitRoot; head = $null; short_head = $null; dirty = $null; key = "git-unresolved:$gitRoot"; freshness_note = 'Git repository was detected, but HEAD could not be resolved.' }
    }
    $include = Get-FlowRelativePath $gitRoot $SourceRoot
    $statusArgs = @('status', '--porcelain', '--', $(if ($include -eq '.') { '.' } else { $include }))
    if ($IgnorePath) {
        $ignore = Get-FlowRelativePath $gitRoot $IgnorePath
        if (-not [IO.Path]::IsPathRooted($ignore)) { $statusArgs += ":(exclude)$ignore" }
    }
    $status = Invoke-FlowGit $gitRoot $statusArgs
    $dirty = if ($status.ExitCode -eq 0) { [bool]$status.StdOut.Trim() } else { $null }
    $fullHead = $head.StdOut.Trim()
    return [ordered]@{
        type = 'git'; root = $gitRoot; head = $fullHead
        short_head = $(if ($short.ExitCode -eq 0) { $short.StdOut.Trim() } else { $fullHead.Substring(0, [Math]::Min(12, $fullHead.Length)) })
        dirty = $dirty; key = "git:$fullHead"
        freshness_note = $(if ($dirty -eq $false) { 'Stable reuse key; inventory is fresh only when this same clean HEAD is observed.' } else { 'Source worktree has uncommitted changes; provide a fresh externally prepared inventory before relying on cache.' })
    }
}

function Get-FlowInventoryRevision {
    param($Summary)
    $revision = Get-FlowMapValue $Summary 'source_revision'
    if ($revision -is [System.Collections.IDictionary]) { return $revision }
    $key = Get-FlowMapValue $Summary 'source_revision_key'
    if ($key) { return [ordered]@{ key = $key } }
    return [ordered]@{}
}

function Get-FlowSourceInventoryStatus {
    param([object[]]$Entries, [AllowNull()][string]$SourceRoot, [AllowNull()][string]$InventoryDir, $Config)
    $profile = Get-FlowProfileSection $Config 'source_inventory_profile'
    $defaultDir = [string](Get-FlowMapValue $profile 'default_cache_dir' 'outputs/repo-scan')
    $programListName = [string](Get-FlowMapValue $profile 'program_list_filename' 'program-list.csv')
    $summaryName = [string](Get-FlowMapValue $profile 'scan_summary_filename' 'scan-summary.yaml')
    $resolved = if ($InventoryDir) { [IO.Path]::GetFullPath($InventoryDir) } elseif ($SourceRoot) { Join-Path $SourceRoot $defaultDir } else { $null }
    $programRows = @{}
    $filesPresent = $false
    $currentRevision = $null
    $inventoryRevision = [ordered]@{}
    if ($resolved) {
        $programListPath = Join-Path $resolved $programListName
        $summaryPath = Join-Path $resolved $summaryName
        $filesPresent = (Test-Path -LiteralPath $programListPath -PathType Leaf) -and (Test-Path -LiteralPath $summaryPath -PathType Leaf)
        if (Test-Path -LiteralPath $programListPath -PathType Leaf) {
            foreach ($row in @(Import-Csv -LiteralPath $programListPath)) {
                if ($row.member) { $programRows[$row.member.Trim().ToUpperInvariant()] = $row }
            }
        }
        if (Test-Path -LiteralPath $summaryPath -PathType Leaf) { $inventoryRevision = Get-FlowInventoryRevision (Read-FlowYamlFile $summaryPath) }
        if ($SourceRoot) { $currentRevision = Get-FlowSourceRevision $SourceRoot $resolved }
    }
    if (-not $resolved) { $freshness = 'not_checked'; $action = 'provide_source_root_to_check_inventory' }
    elseif (-not $filesPresent) { $freshness = 'missing'; $action = 'provide_fresh_inventory_or_exact_source_mapping' }
    elseif (-not $SourceRoot) { $freshness = 'unchecked_no_source_root'; $action = 'provide_source_root_to_compare_revision' }
    elseif ($null -eq $currentRevision -or $currentRevision.type -ne 'git') { $freshness = 'unknown_revision'; $action = 'provide_fresh_inventory_or_exact_source_mapping' }
    elseif ($currentRevision.dirty -ne $false) { $freshness = 'dirty_source'; $action = 'provide_fresh_inventory_or_exact_source_mapping' }
    elseif (-not (Get-FlowMapValue $inventoryRevision 'key')) { $freshness = 'unknown_inventory_revision'; $action = 'provide_fresh_inventory_or_exact_source_mapping' }
    elseif ((Get-FlowMapValue $inventoryRevision 'type') -eq 'git' -and (Get-FlowMapValue $inventoryRevision 'dirty') -ne $false) { $freshness = 'dirty_inventory_source'; $action = 'provide_fresh_inventory_or_exact_source_mapping' }
    elseif ((Get-FlowMapValue $inventoryRevision 'key') -eq $currentRevision.key) { $freshness = 'fresh'; $action = 'reuse_inventory' }
    else { $freshness = 'stale'; $action = 'provide_fresh_inventory_or_exact_source_mapping' }

    $statuses = New-Object System.Collections.Generic.List[object]
    foreach ($entry in $Entries) {
        if ($entry.run_resolution -in @('analyzed_this_run', 'reused_same_run', 'reused_artifact_repo')) {
            $statuses.Add([ordered]@{ program = $entry.normalized_name; run_resolution = $entry.run_resolution; inventory_status = $(if ($entry.run_resolution -eq 'reused_artifact_repo') { 'not_needed_approved_document_repo_artifact_present' } else { 'not_needed_current_artifact_present' }); source_path = $null; size_tier = $entry.tier; targeted_scan_allowed = $false })
            continue
        }
        $row = $programRows[$entry.normalized_name.ToUpperInvariant()]
        $inventoryStatus = if ($freshness -eq 'not_checked') { 'not_checked' } elseif (-not $filesPresent) { 'inventory_cache_missing' } elseif ($null -ne $row) { 'found' } else { 'missing_from_inventory' }
        $statuses.Add([ordered]@{
            program = $entry.normalized_name; run_resolution = $entry.run_resolution; inventory_status = $inventoryStatus
            source_path = $(if ($row) { $row.path } else { $null }); source_kind = $(if ($row) { $row.source_kind } else { $null })
            size_tier = $(if ($row) { $row.size_tier } else { $entry.tier }); default_output_profile = $(if ($row) { $row.default_output_profile } else { $null })
            targeted_scan_allowed = ($freshness -eq 'fresh' -and $null -ne $row)
        })
    }
    return [ordered]@{
        default_inventory_dir = $defaultDir; inventory_dir = $resolved
        program_list = [ordered]@{ path = $(if ($resolved) { Join-Path $resolved $programListName } else { $programListName }); status = $(if (-not $resolved) { 'not_checked' } elseif (Test-Path -LiteralPath (Join-Path $resolved $programListName) -PathType Leaf) { 'present' } else { 'missing' }) }
        scan_summary = [ordered]@{ path = $(if ($resolved) { Join-Path $resolved $summaryName } else { $summaryName }); status = $(if (-not $resolved) { 'not_checked' } elseif (Test-Path -LiteralPath (Join-Path $resolved $summaryName) -PathType Leaf) { 'present' } else { 'missing' }) }
        freshness = $freshness; action = $action; source_revision = $currentRevision
        inventory_revision = $(if (@($inventoryRevision.Keys).Count) { $inventoryRevision } else { $null }); programs = $statuses.ToArray()
    }
}

function New-FlowCoreReviewManifest {
    param([string]$ReviewName, [string[]]$Programs, [string]$ArtifactRoot, $Config, [AllowNull()][string]$WorkingBranch, [AllowNull()][string]$SourceRoot, [AllowNull()][string]$InventoryDir, [bool]$ProgramFirst, [string]$ArtifactRepoMode, [AllowNull()][string]$CoreReviewProfile, [AllowNull()][string]$ReviewId, [AllowNull()][string]$FlowSlug, [AllowNull()][string]$ProgramSetSlug, [AllowNull()][string]$ProgramsFile)
    $lookup = Get-FlowProfileSection $Config 'program_artifact_resolution_profile' 'delivery_artifact_lookup_profile'
    $workspace = Get-FlowProfileSection $Config 'delivery_workspace_profile'
    $built = New-FlowProgramEntries $Programs $ArtifactRoot $Config $ArtifactRepoMode
    $inventory = Get-FlowSourceInventoryStatus $built.Entries $SourceRoot $InventoryDir $Config
    $profile = Get-FlowCoreReviewProfile $Config $CoreReviewProfile
    $reviewSlug = ConvertTo-FlowReviewSlug $ReviewName
    $flowIdentity = if ($FlowSlug) { $FlowSlug } else { $ReviewName }
    $stableFlowSlug = Get-FlowIdentitySlug $flowIdentity
    $identitySlug = Get-FlowProgramSetIdentitySlug @($built.Entries | ForEach-Object { $_.normalized_name })
    $identityDigest = @($identitySlug -split '_')[-1]
    $stableProgramSetSlug = if ($ProgramSetSlug) { "$(ConvertTo-FlowReviewSlug $ProgramSetSlug)_$identityDigest" } else { $identitySlug }
    foreach ($entry in $built.Entries) {
        if ($inventory.freshness -eq 'fresh' -and $entry.run_resolution -eq 'pending_source') {
            $matchingRows = @($inventory.programs | Where-Object { $_.program -eq $entry.normalized_name })
            $row = $matchingRows[$matchingRows.Count - 1]
            if ($row.inventory_status -eq 'missing_from_inventory') {
                $entry.run_resolution = 'blocked_missing_source'; $entry.artifact_source = 'source_inventory_missing'
                $entry.follow_up = 'confirm SME program name/library/alias or provide source; fresh source inventory did not contain this program'
                $row.run_resolution = 'blocked_missing_source'; $row.targeted_scan_allowed = $false
            }
        }
    }
    $hasPending = @($built.Entries | Where-Object { (Get-FlowMapValue $_.artifact_readiness 'status' 'not_ready') -ne 'ready' }).Count -gt 0
    $reviewStatus = if ($hasPending) { 'blocked_artifact_readiness' } else { 'ready_for_synthesis' }
    $artifactReadiness = if ($hasPending) { 'not_ready' } else { 'ready' }
    $mergeCoverage = if ($hasPending) { 'blocked' } else { 'pending' }
    $folderSlug = "$stableFlowSlug--$stableProgramSetSlug"
    $stableReviewId = if ($ReviewId) { $ReviewId } else { "review-$stableFlowSlug--$stableProgramSetSlug" }
    $runProfile = [ordered]@{ repo = $(if (Get-FlowMapValue $lookup 'repo') { Get-FlowMapValue $lookup 'repo' } else { Get-FlowMapValue $workspace 'repo' }); working_branch = $WorkingBranch; artifact_root = [IO.Path]::GetFullPath($ArtifactRoot); artifact_repo_mode = $ArtifactRepoMode; program_first = $ProgramFirst; cross_run_reuse = ($ArtifactRepoMode -eq 'approved_document_repo'); reuse_policy = $(if ($ArtifactRepoMode -eq 'approved_document_repo') { 'approved_document_repo_clone' } else { 'current_run_only' }) }
    if ($ProgramsFile) { $programsPath = [IO.Path]::GetFullPath($ProgramsFile); $sha = [Security.Cryptography.SHA256]::Create(); try { $programsDigest = ([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($programsPath)))).Replace('-', '').ToLowerInvariant() } finally { $sha.Dispose() }; $runProfile.program_list_source = [ordered]@{ path = $programsPath; sha256 = $programsDigest } }
    return [ordered]@{
        schema_version = '0.4'; generated_by = 'build-program-set-core-review.ps1'; generator_version = $script:GeneratorVersion; template_version = $script:TemplateVersion; generated_at = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
        review_id = $stableReviewId; review_name = $ReviewName; review_slug = $reviewSlug
        document_id = $stableReviewId; flow_slug = $stableFlowSlug; program_set_slug = $stableProgramSetSlug; folder_slug = $folderSlug; display_name = $ReviewName
        canonical_filename = "$folderSlug--sme-core-review.md"; artifact_version = '0.4'; review_status = $reviewStatus
        artifact_readiness = $artifactReadiness; merge_coverage = $mergeCoverage; core_review_profile = $profile
        synthesis_owner = 'executing_skill_llm'; primary_synthesis_input = $script:SourcePackFilename
        run_profile = $runProfile
        program_resolution_profile = [ordered]@{ program_folder_patterns = @(Get-FlowMapValue $lookup 'program_folder_patterns' @('modules/*/{PROGRAM}')); program_name_normalization = Get-FlowMapValue $lookup 'program_name_normalization' ([ordered]@{}) }
        workspace_profile = [ordered]@{ program_set_review_parent = Get-FlowMapValue $workspace 'program_set_review_parent'; program_tier_roots = Get-FlowMapValue $workspace 'program_tier_roots' ([ordered]@{}); write_to_main = [bool](Get-FlowMapValue $workspace 'write_to_main' $false) }
        readiness_policy = 'core_reader_first_lenient'
        source_inventory = $inventory; programs = $built.Entries; warnings = $built.Warnings
    }
}

function Get-FlowH2Section {
    param([Parameter(Mandatory = $true)][string]$Markdown, [Parameter(Mandatory = $true)][string]$Section)
    $sourceLines = @($Markdown -split "`r?`n"); $visibleLines = @((Remove-FlowNonRenderedMarkdown $Markdown) -split "`r?`n")
    $start = -1; $end = $sourceLines.Count
    for ($index = 0; $index -lt $visibleLines.Count; $index++) {
        $heading = [regex]::Match($visibleLines[$index], '^[ ]{0,3}##(?!#)\s+(.+?)\s*#*\s*$')
        if (-not $heading.Success) { continue }
        if ($start -lt 0 -and $heading.Groups[1].Value.Trim() -eq $Section) { $start = $index; continue }
        if ($start -ge 0) { $end = $index; break }
    }
    if ($start -lt 0) { return '' }
    return @($sourceLines[$start..($end - 1)]) -join "`n"
}

function Test-FlowTableSeparator {
    param([string]$Line)
    return $Line -and (Test-FlowMarkdownTableSeparator $Line)
}

function Get-FlowMarkdownTables {
    param([Parameter(Mandatory = $true)][string]$SectionText)
    $tables = New-Object System.Collections.Generic.List[object]
    $lines = @($SectionText -split "`r?`n")
    for ($index = 0; $index + 1 -lt $lines.Count; $index++) {
        if (-not (Test-FlowMarkdownTableHeaderAndSeparator $lines[$index] $lines[$index + 1])) { continue }
        $headers = @(Split-FlowMarkdownTableRow $lines[$index])
        $rows = New-Object System.Collections.Generic.List[object]
        $cursor = $index + 2
        while ($cursor -lt $lines.Count -and $lines[$cursor].Trim().StartsWith('|') -and $lines[$cursor].Trim().EndsWith('|')) {
            $cells = @(Split-FlowMarkdownTableRow $lines[$cursor])
            if (-not (Test-FlowTableSeparator $lines[$cursor])) {
                $row = [ordered]@{}
                for ($column = 0; $column -lt $headers.Count; $column++) { $row[$headers[$column]] = $(if ($column -lt $cells.Count) { $cells[$column] } else { '' }) }
                $rows.Add($row)
            }
            $cursor++
        }
        $tables.Add([pscustomobject]@{ Headers = $headers; Rows = $rows.ToArray() })
        $index = $cursor - 1
    }
    return @($tables.ToArray())
}

function ConvertTo-FlowFactIdentityText {
    param([AllowEmptyString()][string]$Value)
    return [regex]::Replace(([string]$Value).Trim(), '\s+', ' ')
}

function Get-FlowRowValue {
    param($Row, [string[]]$Names)
    foreach ($name in $Names) { foreach ($key in @($Row.Keys)) { if ([string]::Equals(([string]$key).Trim(), $name.Trim(), [StringComparison]::OrdinalIgnoreCase)) { $value = ([string]$Row[$key]).Trim(); if ($value) { return $value } } } }
    return ''
}

function ConvertTo-FlowRowText {
    param($Row)
    return (@($Row.Keys) | ForEach-Object { "$(ConvertTo-FlowFactIdentityText ([string]$_))=$(ConvertTo-FlowFactIdentityText ([string]$Row[$_]))" }) -join '; '
}

function Get-FlowStableFactId {
    param([string]$Program, [string]$Section, [string]$FactType, [string]$SourceText)
    $programKey = [regex]::Replace($Program.Trim().ToUpperInvariant(), '[\s<>:"/\\|?*]+', '_').Trim([char[]]'._-')
    if (-not $programKey) { $programKey = 'PROGRAM' }
    $sectionKey = ConvertTo-FlowFactIdentityText $Section
    $factTypeKey = (ConvertTo-FlowFactIdentityText $FactType).ToLowerInvariant()
    $sourceKey = ConvertTo-FlowFactIdentityText $SourceText
    $identity = "$programKey`n$sectionKey`n$factTypeKey`n$sourceKey"
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $digest = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($identity)))).Replace('-', '').Substring(0, 10).ToUpperInvariant() }
    finally { $sha.Dispose() }
    $factTypeSlug = [regex]::Replace($factTypeKey.ToUpperInvariant(), '[^A-Z0-9]+', '_').Trim('_')
    if (-not $factTypeSlug) { $factTypeSlug = 'FACT' }
    return "SF-$programKey-$factTypeSlug-$digest"
}

function Test-FlowMaterialTableRow {
    param([string[]]$Headers, $Row)
    $empty = @('', '-', '--', '---', '—', 'none', 'n/a', 'not applicable')
    $values = @($Headers | ForEach-Object { ([string](Get-FlowMapValue $Row $_ '')).Trim() })
    if (@($values | Where-Object { $_.ToLowerInvariant() -notin $empty }).Count -eq 0) { return $false }
    $sameAsHeaders = $true
    for ($i = 0; $i -lt $Headers.Count; $i++) { if (-not [string]::Equals($Headers[$i].Trim(), $values[$i], [StringComparison]::OrdinalIgnoreCase)) { $sameAsHeaders = $false; break } }
    if ($sameAsHeaders) { return $false }
    if ($Headers.Count -eq 2 -and $Headers[1].Trim().ToLowerInvariant() -in @('value', 'setting')) {
        $labels = @('analysis status', 'artifact version', 'document id', 'flow slug', 'generated at', 'generated by', 'program', 'program name', 'program set slug', 'review intent', 'schema version', 'source artifact')
        if ($Headers[0].Trim().ToLowerInvariant() -in @('metadata', 'property') -or $values[0].ToLowerInvariant() -in $labels) { return $false }
    }
    return $true
}

function Test-FlowSpecializedTable {
    param([string]$Section, [string[]]$Headers)
    $normalized = @($Headers | ForEach-Object { $_.Trim().ToLowerInvariant() })
    if ($normalized -contains 'rlog / routine' -and $normalized -contains 'category' -and $normalized -contains 'reader-useful detail') { return $true }
    if ($Section -eq 'Calculation Logic' -and $normalized -contains 'calculation / assignment') { return $true }
    if ($Section -eq 'Validation Logic' -and @($normalized | Where-Object { $_ -in @('message / status code', 'message / status / outcome') }).Count) { return $true }
    if ($Section -eq 'Exception Handling' -and $normalized -contains 'exception / error path') { return $true }
    return $Section -eq 'Message Inventory' -and @($normalized | Where-Object { $_ -in @('message / code / literal', 'message / status / literal') }).Count -gt 0
}

function Get-FlowEvidenceInfo {
    param($Row, [string]$Source, [string[]]$ReferenceNames)
    $status = Get-FlowRowValue $Row @('Evidence Status', 'Status'); $reference = Get-FlowRowValue $Row $ReferenceNames
    $normalized = if ($status) { $status.ToLowerInvariant() } elseif ($reference) { 'evidence_present' } else { 'unresolved' }
    $allowed = @('confirmed', 'confirmed_from_code', 'evidence_present', 'present', 'source_backed_complete')
    return [ordered]@{ status = $normalized; reference = $(if ($reference) { $reference } else { $Source }); unresolved = $(if ($normalized -in $allowed) { $null } else { 'evidence status is not source-confirmed' }) }
}

function New-FlowSourceFact {
    param([string]$Program, [string]$Section, $Row, [string]$Source)
    $keys = @($Row.Keys); $firstKey = if ($keys.Count) { [string]$keys[0] } else { '' }; $firstValue = if ($firstKey) { [string]$Row[$firstKey] } else { '' }
    $synthetic = $firstKey -in @('ReaderFirstNarrative', 'UnresolvedStatement')
    $sourceText = ConvertTo-FlowFactIdentityText $(if ($synthetic) { $firstValue } else { ConvertTo-FlowRowText $Row })
    $factType = if ($firstKey -eq 'ReaderFirstNarrative') { $(if ($Section -eq 'Program Reading Summary') { 'summary_contribution' } else { 'thematic_prose' }) }
        elseif ($firstKey -eq 'UnresolvedStatement') { 'unresolved_core_statement' }
        elseif ($firstKey -eq 'RLOG / Routine') { 'routine' }
        elseif ($Section -eq 'Calculation Logic' -and $firstKey -eq 'Calculation / Assignment') { 'calculation' }
        elseif ($Section -eq 'Validation Logic' -and $firstKey -match '^Message / Status') { 'validation' }
        elseif ($Section -eq 'Exception Handling' -and $firstKey -eq 'Exception / Error Path') { 'exception' }
        elseif ($Section -eq 'Message Inventory' -and $firstKey -match '^Message / (?:Code|Status) / Literal$') { 'message' }
        else { 'thematic_table' }
    $exact = ''; $logic = $firstValue; $evidenceInfo = $null
    if ($factType -eq 'calculation') { $exact = Get-FlowRowValue $Row @('Target Field / Carrier', 'Target Field / Variable', 'Target Field'); $evidenceInfo = Get-FlowEvidenceInfo $Row $Source @('Evidence', 'Evidence ID', 'Evidence Reference', 'Supporting Detail Link', 'Supporting Detail', 'Detail Refs') }
    elseif ($factType -eq 'validation') { $exact = Get-FlowRowValue $Row @('Message / Status Code', 'Message / Status / Outcome', 'Status'); $description = Get-FlowRowValue $Row @('Message Description', 'Description'); $logic = $(if ($description) { $description } else { "Validation outcome $exact" }); $evidenceInfo = Get-FlowEvidenceInfo $Row $Source @('Evidence', 'Supporting Detail Link', 'Reverse Trigger Chain / Routine Logic Link', 'Detail Refs') }
    elseif ($factType -eq 'exception') { $exact = Get-FlowRowValue $Row @('Fields / Messages Set', 'Fields / Messages'); $evidenceInfo = Get-FlowEvidenceInfo $Row $Source @('Evidence', 'Evidence ID', 'Evidence Reference', 'Supporting Detail Link', 'Supporting Detail', 'Detail Refs') }
    elseif ($factType -eq 'message') { $exact = Get-FlowRowValue $Row @('Message / Code / Literal', 'Message / Status / Literal', 'Message'); $description = Get-FlowRowValue $Row @('Short Description', 'Description'); $logic = $(if ($description) { $description } else { "Exact observed message/status $exact" }); $evidenceInfo = Get-FlowEvidenceInfo $Row $Source @('Evidence', 'Detail', 'Detail Refs', 'Supporting Detail') }
    elseif ($factType -eq 'routine') { $exact = $firstValue; $logic = Get-FlowRowValue $Row @('Reader-useful Detail') }
    elseif ($factType -eq 'thematic_table') { $logic = [string](@($Row.Values | Where-Object { ([string]$_).Trim().ToLowerInvariant() -notin @('', '-', '--', '---', '—', 'none', 'n/a', 'not applicable') })[0]) }
    $fact = [ordered]@{ source_fact_id = Get-FlowStableFactId $Program $Section $factType $sourceText; program = $Program; section = $Section; fact_type = $factType; material = $true; logic = $logic; exact_value = $exact; evidence = $Source; evidence_reference = $Source; evidence_status = 'confirmed'; unresolved_reason = $null; source_artifact = $Source; source_text = $sourceText }
    if (-not $synthetic) { $fact.source_row = $Row; $fact.source_cells = @($keys | ForEach-Object { [ordered]@{ header = [string]$_; value = [string]$Row[$_] } }) }
    if ($evidenceInfo) { $fact.evidence = $evidenceInfo.reference; $fact.evidence_reference = $evidenceInfo.reference; $fact.evidence_status = $evidenceInfo.status; $fact.unresolved_reason = $evidenceInfo.unresolved }
    if ($factType -eq 'calculation') { $fact.routine = Get-FlowRowValue $Row @('Routine'); $fact.calculation = $firstValue; $fact.target_carrier = $exact; $fact.source_carriers = Get-FlowRowValue $Row @('Source Operands / Carriers', 'Source Operands'); $fact.guard = Get-FlowRowValue $Row @('Guard / Branch', 'Guard'); $fact.effect = Get-FlowRowValue $Row @('Effect', 'Output / Business Effect'); $fact.supporting_detail = Get-FlowRowValue $Row @('Supporting Detail Link', 'Supporting Detail', 'Detail Refs') }
    elseif ($factType -eq 'validation') { $fact.routine = Get-FlowRowValue $Row @('Routine', 'Set By / Source Lines'); $fact.description = $description; $fact.exact_code_status = $exact; $fact.validation_type = Get-FlowRowValue $Row @('Validation / Error Type', 'Type'); $fact.trigger_chain = Get-FlowRowValue $Row @('Trigger Condition', 'Trigger Chain', 'Condition / Evidence'); $fact.carrier_destination = Get-FlowRowValue $Row @('Output Carrier', 'Carrier / Destination'); $fact.effect = Get-FlowRowValue $Row @('Downstream Effect', 'Effect') }
    elseif ($factType -eq 'exception') { $fact.routine = Get-FlowRowValue $Row @('Routine'); $fact.exception_path = $firstValue; $fact.guard = Get-FlowRowValue $Row @('Trigger', 'Condition'); $fact.detection_mechanism = Get-FlowRowValue $Row @('Detection Mechanism', 'Detection'); $fact.fields_messages_set = $exact; $fact.exception_action = Get-FlowRowValue $Row @('Handling Action', 'Action'); $fact.effect = Get-FlowRowValue $Row @('Downstream Effect', 'Flow-Level Effect', 'Effect'); $fact.supporting_detail = Get-FlowRowValue $Row @('Supporting Detail Link', 'Supporting Detail', 'Detail Refs') }
    elseif ($factType -eq 'message') { $fact.routine = Get-FlowRowValue $Row @('Primary Routine(s)', 'Program / Routine Sources', 'Routine'); $fact.exact_message_status_literal = $exact; $fact.description = $description; $fact.message_type = Get-FlowRowValue $Row @('Type'); $fact.generic_handler_token = $(if ($fact.message_type.ToLowerInvariant().Contains('generic_handler')) { $exact } else { '' }); $fact.occurrences = Get-FlowRowValue $Row @('Occurrences'); $fact.first_seen = Get-FlowRowValue $Row @('First Seen / Set By'); $fact.trigger_handler = Get-FlowRowValue $Row @('Trigger / Handler Summary', 'Condition / Handler', 'Trigger / Handler'); $fact.carrier_destination = Get-FlowRowValue $Row @('Carrier / Destination', 'Output Carrier', 'Carrier', 'Destination'); $fact.effect = Get-FlowRowValue $Row @('Effect') }
    elseif ($factType -eq 'routine') { $fact.routine = $firstValue; $fact.category = Get-FlowRowValue $Row @('Category'); $fact.evidence = $(if ($firstValue) { $firstValue } else { $Source }); $fact.evidence_reference = $fact.evidence }
    elseif ($factType -eq 'thematic_table') { $refs = @($keys | Where-Object { $_ -match '(?i)evidence|supporting detail|detail refs|rlog' } | ForEach-Object { [string]$Row[$_] } | Where-Object { $_ } | Select-Object -Unique); $status = Get-FlowRowValue $Row @('Evidence Status'); $fact.source_headers = @($keys); $fact.evidence_reference = $(if ($refs.Count) { $refs -join '; ' } else { $Source }); $fact.evidence = $fact.evidence_reference; $fact.evidence_status = $(if ($status) { $status.ToLowerInvariant() } elseif ($refs.Count) { 'evidence_present' } else { 'source_backed' }); if ($fact.evidence_status -notin @('confirmed', 'confirmed_from_code', 'evidence_present', 'present', 'source_backed', 'source_backed_complete')) { $fact.unresolved_reason = 'evidence status is not source-confirmed' } }
    elseif ($factType -eq 'unresolved_core_statement') { $fact.evidence_status = 'unresolved_non_blocking'; $fact.unresolved_reason = $firstValue }
    return $fact
}

function Get-FlowSectionFacts {
    param([string]$Program, [string]$Section, [string]$SectionText, [string]$Source)
    $facts = New-Object System.Collections.Generic.List[object]; $seenFactIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $SectionText = Remove-FlowNonRenderedMarkdown $SectionText
    if ($Section -ne 'Message Inventory') {
        $withoutComments = [regex]::Replace($SectionText, '<!--.*?-->', '', [Text.RegularExpressions.RegexOptions]::Singleline); $proseLines = New-Object System.Collections.Generic.List[string]
        foreach ($raw in @($withoutComments -split "`r?`n")) { $line = $raw.Trim(); if ($line -and -not $line.StartsWith('#') -and -not $line.StartsWith('|') -and $line -notmatch '^\*\*.+unresolved:\*\*') { $proseLines.Add($line) } }
        $prose = ConvertTo-FlowFactIdentityText ($proseLines -join ' '); if ($prose) { $fact = New-FlowSourceFact $Program $Section ([ordered]@{ ReaderFirstNarrative = $prose }) $Source; if ($seenFactIds.Add($fact.source_fact_id)) { $facts.Add($fact) } }
    }
    foreach ($match in @([regex]::Matches($SectionText, '(?im)^\*\*(.+?unresolved):\*\*\s*(.+)$'))) { $value = $match.Groups[2].Value.Trim(); if ($value.ToLowerInvariant().TrimEnd([char]'.') -notin @('none', 'no', 'n/a', 'not applicable')) { $fact = New-FlowSourceFact $Program $Section ([ordered]@{ UnresolvedStatement = "$($match.Groups[1].Value): $value" }) $Source; if ($seenFactIds.Add($fact.source_fact_id)) { $facts.Add($fact) } } }
    foreach ($table in @(Get-FlowMarkdownTables $SectionText)) {
        $specialized = Test-FlowSpecializedTable $Section @($table.Headers)
        foreach ($row in @($table.Rows)) { if (-not (Test-FlowMaterialTableRow @($table.Headers) $row)) { continue }; $fact = New-FlowSourceFact $Program $Section $row $Source; if (($specialized -and $fact.fact_type -eq 'thematic_table') -or (-not $specialized -and $fact.fact_type -ne 'thematic_table')) { continue }; if ($seenFactIds.Add($fact.source_fact_id)) { $facts.Add($fact) } }
    }
    return @($facts.ToArray())
}

function New-FlowReaderFirstBundle {
    param($Manifest)
    $root = [string]$Manifest.run_profile.artifact_root
    $sourcePack = New-Object System.Collections.Generic.List[string]
    $sourcePack.Add("# Reader-First Program Analysis Source Pack: $($Manifest.review_name)")
    $sourcePack.Add('')
    $sourcePack.Add("Document ID: $($Manifest.document_id)"); $sourcePack.Add("Flow Slug: $($Manifest.flow_slug)"); $sourcePack.Add("Program Set Slug: $($Manifest.program_set_slug)")
    $sourcePack.Add(''); $sourcePack.Add('Program list order is navigation order only; it is not a source-confirmed call chain or execution order.')
    $allFacts = New-Object System.Collections.Generic.List[object]
    $programFacts = New-Object System.Collections.Generic.List[object]
    $seenPrograms = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
    foreach ($entry in @($Manifest.programs)) {
        $program = [string]$entry.normalized_name
        if (-not $seenPrograms.Add($program)) { continue }
        $programAnalysis = Get-FlowArtifactAbsolutePath $root $entry.compact_artifacts 'program-analysis.md'
        if (-not $programAnalysis) { throw "ready program has no program-analysis path: $program" }
        $markdown = [IO.File]::ReadAllText($programAnalysis)
        $buckets = [ordered]@{ summary_contributions = @(); thematic_contributions = @(); calculations = @(); validations = @(); exceptions = @(); messages = @(); routines = @(); unresolved_core_statements = @() }
        $sourceRelative = Get-FlowRelativePath $root $programAnalysis
        $sourcePack.Add('')
        $sourcePack.Add("<!-- BEGIN LOSSLESS PROGRAM ${program}: $sourceRelative -->")
        $sourcePack.Add("# Program: $program")
        $sourcePack.Add('')
        $sourcePack.Add("Source: $sourceRelative")
        foreach ($section in $script:SourceReadingSections) {
            $block = Get-FlowH2Section $markdown $section
            if (-not $block) { throw "$program program-analysis is missing reader-first section: $section" }
            $sourcePack.Add(''); $sourcePack.Add($block)
            $sectionFacts = @(Get-FlowSectionFacts $program $section $block $sourceRelative)
            $buckets.summary_contributions += @($sectionFacts | Where-Object { $_.fact_type -eq 'summary_contribution' })
            $buckets.thematic_contributions += @($sectionFacts | Where-Object { $_.fact_type -in @('thematic_prose', 'thematic_table') })
            $buckets.routines += @($sectionFacts | Where-Object { $_.fact_type -eq 'routine' }); $buckets.unresolved_core_statements += @($sectionFacts | Where-Object { $_.fact_type -eq 'unresolved_core_statement' })
            if ($section -eq 'Calculation Logic') { $buckets.calculations = @($sectionFacts | Where-Object { $_.fact_type -eq 'calculation' }) }
            elseif ($section -eq 'Validation Logic') { $buckets.validations = @($sectionFacts | Where-Object { $_.fact_type -eq 'validation' }) }
            elseif ($section -eq 'Exception Handling') { $buckets.exceptions = @($sectionFacts | Where-Object { $_.fact_type -eq 'exception' }) }
            elseif ($section -eq 'Message Inventory') { $buckets.messages = @($sectionFacts | Where-Object { $_.fact_type -eq 'message' }) }
        }
        $sourcePack.Add('')
        $sourcePack.Add("<!-- END LOSSLESS PROGRAM $program -->")
        $flattened = @($buckets.Values | ForEach-Object { $_ }); foreach ($fact in $flattened) { $allFacts.Add($fact) }
        $programFacts.Add([ordered]@{
            program = $program; run_resolution = $entry.run_resolution; source_status = 'complete'; source_files = @($sourceRelative)
            facts = $buckets; source_fact_ids = @($flattened | ForEach-Object { $_.source_fact_id }); unresolved_reason = $null
        })
    }
    $factsDocument = [ordered]@{
        schema_version = '0.4'; generated_by = 'build-program-set-core-review.ps1'; generator_version = $script:GeneratorVersion
        document_id = $Manifest.document_id; review_id = $Manifest.review_id; review_status = $Manifest.review_status
        flow_slug = $Manifest.flow_slug; program_set_slug = $Manifest.program_set_slug; folder_slug = $Manifest.folder_slug
        source_facts = @($allFacts.ToArray()); programs = @($programFacts.ToArray())
        evidence_boundary = 'Program list order is navigation only. Call relationships require source evidence and are never inferred from input order.'
    }
    return [ordered]@{ SourcePack = ($sourcePack.ToArray() -join "`n") + "`n"; Facts = $factsDocument }
}

function New-FlowCoverageControl {
    param($Manifest, [object[]]$SourceFacts = @())
    $items = foreach ($fact in @($SourceFacts)) {
        [ordered]@{
            source_fact_id = $fact.source_fact_id; program = $fact.program; section = $fact.section; fact_type = $fact.fact_type
            status = 'pending'; review_anchor = $null; merged_source_fact_ids = @(); exclusion_reason = $null
        }
    }
    $byProgram = [ordered]@{}; $bySection = [ordered]@{}; $routineRlog = [ordered]@{}
    foreach ($fact in @($SourceFacts)) {
        $program = [string]$fact.program; $section = [string]$fact.section
        $byProgram[$program] = [int](Get-FlowMapValue $byProgram $program 0) + 1
        $bySection[$section] = [int](Get-FlowMapValue $bySection $section 0) + 1
        if ($fact.fact_type -eq 'routine') { $routineRlog[$program] = [int](Get-FlowMapValue $routineRlog $program 0) + 1 }
    }
    $counts = [ordered]@{
        total_source_facts = @($SourceFacts).Count; accounted_source_facts = 0; pending_source_facts = @($SourceFacts).Count
        by_program = $byProgram; by_section = $bySection; routine_rlog = $routineRlog
    }
    return [ordered]@{
        schema_version = '0.4'; generated_by = 'build-program-set-core-review.ps1'; document_id = $Manifest.document_id; review_id = $Manifest.review_id
        review_status = $(if ($Manifest.review_status -eq 'ready_for_synthesis') { 'pending_synthesis' } else { 'blocked_artifact_readiness' })
        coverage_status = $(if ($Manifest.review_status -eq 'ready_for_synthesis') { 'pending' } else { 'blocked_artifact_readiness' })
        allowed_statuses = @('included', 'merged', 'excluded_non_core', 'pending'); coverage_counts = $counts
        expected_source_fact_count = @($SourceFacts).Count; coverage_item_count = @($items).Count
        status_counts = [ordered]@{ included = 0; merged = 0; excluded_non_core = 0; pending = @($items).Count }
        items = @($items); coverage_items = @($items)
    }
}

function Resolve-FlowOutputDirectory {
    param([Parameter(Mandatory = $true)][string]$OutputParent, [Parameter(Mandatory = $true)][string]$FolderSlug)
    $resolvedParent = [IO.Path]::GetFullPath($OutputParent)
    if ($resolvedParent -ne [IO.Path]::GetPathRoot($resolvedParent)) { $resolvedParent = $resolvedParent.TrimEnd([char[]]@('/', '\')) }
    if ([IO.Path]::GetFileName($resolvedParent).Equals($FolderSlug, [StringComparison]::OrdinalIgnoreCase)) { return $resolvedParent }
    return Join-Path $resolvedParent $FolderSlug
}

function Write-FlowCoreReviewOutputs {
    param($Manifest, [Parameter(Mandatory = $true)][string]$OutputDirectory)
    $folder = Resolve-FlowOutputDirectory $OutputDirectory ([string]$Manifest.folder_slug)
    $programListPath = Join-Path $folder $script:ProgramListFilename
    $manifestPath = Join-Path $folder $script:ManifestFilename
    $readinessPath = Join-Path $folder $script:ReadinessFilename
    $coveragePath = Join-Path $folder $script:CoverageFilename
    Assert-FlowOutputIdentityCompatible -ManifestPath $manifestPath -Manifest $Manifest
    Assert-FlowFormalReviewAbsent -ReviewPath (Join-Path $folder ([string]$Manifest.canonical_filename))
    [IO.Directory]::CreateDirectory($folder) | Out-Null
    $readinessPrograms = New-Object System.Collections.Generic.List[object]
    $seenReadinessPrograms = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
    foreach ($entry in @($Manifest.programs)) {
        $program = [string](Get-FlowMapValue $entry 'normalized_name' '')
        if (-not $program -or -not $seenReadinessPrograms.Add($program)) { continue }
        $readinessPrograms.Add([ordered]@{
            program = $entry.normalized_name; run_resolution = $entry.run_resolution
            candidate_artifact_root = $entry.candidate_artifact_root; artifact_root = $entry.artifact_root
            artifact_readiness = $entry.artifact_readiness
        })
    }
    $readiness = [ordered]@{
        schema_version = '0.4'; review_id = $Manifest.review_id; overall_status = $(if ($Manifest.review_status -eq 'ready_for_synthesis') { 'ready' } else { 'not_ready' })
        upstream_validator = 'legacy-ibmi-program-analyzer/Invoke-ContractValidation'; programs = @($readinessPrograms.ToArray())
    }
    [IO.File]::WriteAllText(
        $programListPath,
        ((@($Manifest.programs) | ForEach-Object {
            $inputName = [string](Get-FlowMapValue $_ 'input_name' '')
            if ($inputName) { $inputName } else { [string](Get-FlowMapValue $_ 'normalized_name' '') }
        }) -join "`n") + "`n",
        $script:Utf8NoBom
    )
    [IO.File]::WriteAllText($manifestPath, (ConvertTo-FlowYamlText $Manifest), $script:Utf8NoBom)
    [IO.File]::WriteAllText($readinessPath, (ConvertTo-FlowYamlText $readiness), $script:Utf8NoBom)
    $written = New-Object System.Collections.Generic.List[string]
    foreach ($path in @($programListPath, $manifestPath, $readinessPath)) { $written.Add($path) }
    if ($Manifest.review_status -eq 'ready_for_synthesis') {
        $bundle = New-FlowReaderFirstBundle $Manifest
        $sourcePackPath = Join-Path $folder $script:SourcePackFilename
        $factsPath = Join-Path $folder $script:CoreFactsFilename
        [IO.File]::WriteAllText($sourcePackPath, $bundle.SourcePack, $script:Utf8NoBom)
        [IO.File]::WriteAllText($factsPath, (ConvertTo-FlowYamlText $bundle.Facts), $script:Utf8NoBom)
        $coverage = New-FlowCoverageControl -Manifest $Manifest -SourceFacts @($bundle.Facts.source_facts)
        [IO.File]::WriteAllText($coveragePath, (ConvertTo-FlowYamlText $coverage), $script:Utf8NoBom)
        foreach ($path in @($sourcePackPath, $factsPath, $coveragePath)) { $written.Add($path) }
    }
    else {
        Remove-FlowStaleReadyArtifacts -Folder $folder -Filenames @($script:SourcePackFilename, $script:CoreFactsFilename)
        $coverage = New-FlowCoverageControl -Manifest $Manifest -SourceFacts @()
        [IO.File]::WriteAllText($coveragePath, (ConvertTo-FlowYamlText $coverage), $script:Utf8NoBom)
        $written.Add($coveragePath)
    }
    return @($written.ToArray())
}
Export-ModuleMember -Function Read-FlowProgramsFile, New-FlowCoreReviewManifest, Write-FlowCoreReviewOutputs, Resolve-FlowOutputDirectory, New-FlowReaderFirstBundle, Find-FlowProgramArtifactRoot, Get-FlowArtifactStatuses, Get-FlowArtifactReadiness
