<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Native Windows PowerShell 5.1 builder for the program-set core-review
manifest and reader-first skeleton.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'FlowYaml.psm1') -Force

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
$script:CoreReadingSections = @(
    'Program Set Reading Summary', 'Cross-Program Processing Overview',
    'Calculation Logic', 'Validation Logic', 'Exception Handling'
)
$script:AuditSections = @('Core Completeness Ledger', 'Sources', 'Run Profile', 'Source Inventory Cache')
$script:CanonicalReviewFilename = 'program-set-sme-core-review.md'
$script:CoreFactsFilename = 'program-set-core-facts.yaml'
$script:GeneratorVersion = '0.3.0'
$script:TemplateVersion = '0.3.0'
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
    $selected = Get-FlowMapValue $Config 'core_review_profile' ([ordered]@{})
    $name = if ($RequestedName) { $RequestedName } else { [string](Get-FlowMapValue $selected 'name' 'standard_reader_first') }
    $includeMessages = $name -eq 'standard_reader_first'
    if ($selected -is [System.Collections.IDictionary]) {
        if (Get-FlowMapValue $selected 'include_message_inventory' $null) { $includeMessages = [bool](Get-FlowMapValue $selected 'include_message_inventory') }
    }
    $sections = @($script:CoreReadingSections)
    if ($includeMessages) { $sections += 'Message Inventory' }
    return [ordered]@{
        name = $name
        core_sections = $sections
        include_message_inventory = $includeMessages
        include_audit_sections = [bool](Get-FlowMapValue $selected 'include_audit_sections' $true)
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
    $programs = New-Object System.Collections.Generic.List[string]
    foreach ($line in [IO.File]::ReadAllLines($Path)) {
        $value = $line.Trim()
        if ($value -and -not $value.StartsWith('#')) { $programs.Add($value) }
    }
    return $programs.ToArray()
}

function Normalize-FlowProgramName {
    param([Parameter(Mandatory = $true)][string]$Program, $LookupProfile)
    $normalized = $Program.Trim()
    $normalization = Get-FlowMapValue $LookupProfile 'program_name_normalization' ([ordered]@{})
    if ((Get-FlowMapValue $normalization 'case') -eq 'upper') {
        # Preserve exact prefixes such as @; only case normalization is applied.
        $normalized = $normalized.ToUpperInvariant()
    }
    return $normalized
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
    # PowerShell literal hashtables compare string keys case-insensitively.
    # The canonical implementation preserves case-sensitive program identity
    # whenever the selected profile does not request uppercase normalization.
    $seen = [System.Collections.Hashtable]::new([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $Programs.Count; $index++) {
        $inputName = $Programs[$index]
        $normalized = Normalize-FlowProgramName $inputName $lookup
        if ($seen.ContainsKey($normalized)) {
            $first = $seen[$normalized]
            $hasArtifact = $null -ne $first.artifact_root
            $warnings.Add("Duplicate normalized program name '$normalized'; " + $(if ($hasArtifact) { "reusing artifact from order $($first.order)" } else { "will resolve once from order $($first.order) before reuse" }))
            $entries.Add([ordered]@{
                input_name = $inputName
                normalized_name = $normalized
                order = $index + 1
                run_resolution = $(if ($hasArtifact) { $(if ($approved) { 'reused_artifact_repo' } else { 'reused_same_run' }) } else { 'pending_source' })
                artifact_root = $first.artifact_root
                artifact_source = $(if ($hasArtifact) { $first.artifact_source } else { 'source_scan_required' })
                tier = $first.tier
                compact_artifacts = $first.compact_artifacts
                follow_up = $(if ($hasArtifact) { $(if ($approved) { 'none - reused approved document repo artifact' } else { 'none - reused earlier in this run' }) } elseif ($approved) { 'add or refresh this program in the approved document repo' } else { 'scan this program in current run' })
            })
            continue
        }
        $found = Find-FlowProgramArtifactRoot $ArtifactRoot $normalized $lookup
        if (@($found.Matches).Count -gt 1) {
            $warnings.Add("Program $normalized matched multiple artifact folders; using $($found.Root): " + (@($found.Matches) -join ', '))
        }
        $hasArtifact = $null -ne $found.Root
        $compactArtifacts = Get-FlowArtifactStatuses $ArtifactRoot $found.Root $normalized
        $missingRequired = @($script:RequiredArtifacts | Where-Object {
            $artifact = Get-FlowMapValue $compactArtifacts (ConvertTo-FlowArtifactKey $_) ([ordered]@{})
            (Get-FlowMapValue $artifact 'status' 'missing') -ne 'present'
        })
        $usableArtifact = $hasArtifact -and $missingRequired.Count -eq 0
        $entry = [ordered]@{
            input_name = $inputName
            normalized_name = $normalized
            order = $index + 1
            run_resolution = $(if ($usableArtifact) { $(if ($approved) { 'reused_artifact_repo' } else { 'analyzed_this_run' }) } else { 'pending_source' })
            artifact_root = $(if ($usableArtifact) { $found.Root } else { $null })
            artifact_source = $(if ($usableArtifact) { $(if ($approved) { 'approved_document_repo' } else { 'delivery_working_branch' }) } else { 'source_scan_required' })
            tier = Get-FlowProgramTier $found.Root $workspace
            compact_artifacts = $compactArtifacts
            follow_up = $(if ($usableArtifact) { $(if ($approved) { 'none - approved document repo artifact present' } else { 'none - analysis artifact present in current run' }) } elseif ($hasArtifact) { 'refresh missing required artifacts: ' + ($missingRequired -join ', ') } elseif ($approved) { 'add or refresh this program in the approved document repo' } else { 'scan this program in current run' })
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
        freshness_note = $(if ($dirty -eq $false) { 'Stable reuse key; inventory is fresh only when this same clean HEAD is observed.' } else { 'Source worktree has uncommitted changes; rerun inventory before relying on cache.' })
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
    elseif (-not $filesPresent) { $freshness = 'missing'; $action = 'rerun_repo_inventory_scan' }
    elseif (-not $SourceRoot) { $freshness = 'unchecked_no_source_root'; $action = 'provide_source_root_to_compare_revision' }
    elseif ($null -eq $currentRevision -or $currentRevision.type -ne 'git') { $freshness = 'unknown_revision'; $action = 'rerun_repo_inventory_scan' }
    elseif ($currentRevision.dirty -ne $false) { $freshness = 'dirty_source'; $action = 'rerun_repo_inventory_scan' }
    elseif (-not (Get-FlowMapValue $inventoryRevision 'key')) { $freshness = 'unknown_inventory_revision'; $action = 'rerun_repo_inventory_scan' }
    elseif ((Get-FlowMapValue $inventoryRevision 'type') -eq 'git' -and (Get-FlowMapValue $inventoryRevision 'dirty') -ne $false) { $freshness = 'dirty_inventory_source'; $action = 'rerun_repo_inventory_scan' }
    elseif ((Get-FlowMapValue $inventoryRevision 'key') -eq $currentRevision.key) { $freshness = 'fresh'; $action = 'reuse_inventory' }
    else { $freshness = 'stale'; $action = 'rerun_repo_inventory_scan' }

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
    param([string]$ReviewName, [string[]]$Programs, [string]$ArtifactRoot, $Config, [AllowNull()][string]$WorkingBranch, [AllowNull()][string]$SourceRoot, [AllowNull()][string]$InventoryDir, [bool]$ProgramFirst, [string]$ArtifactRepoMode, [AllowNull()][string]$CoreReviewProfile, [AllowNull()][string]$ReviewId, [AllowNull()][string]$FlowSlug, [AllowNull()][string]$ProgramSetSlug)
    $lookup = Get-FlowProfileSection $Config 'program_artifact_resolution_profile' 'delivery_artifact_lookup_profile'
    $workspace = Get-FlowProfileSection $Config 'delivery_workspace_profile'
    $built = New-FlowProgramEntries $Programs $ArtifactRoot $Config $ArtifactRepoMode
    $inventory = Get-FlowSourceInventoryStatus $built.Entries $SourceRoot $InventoryDir $Config
    $profile = Get-FlowCoreReviewProfile $Config $CoreReviewProfile
    $reviewSlug = ConvertTo-FlowReviewSlug $ReviewName
    $stableFlowSlug = if ($FlowSlug) { ConvertTo-FlowReviewSlug $FlowSlug } else { $reviewSlug }
    $stableProgramSetSlug = if ($ProgramSetSlug) { ConvertTo-FlowReviewSlug $ProgramSetSlug } else { Get-FlowProgramSetIdentitySlug @($built.Entries | ForEach-Object { $_.normalized_name }) }
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
    $hasPending = @($built.Entries | Where-Object { $_.run_resolution -in @('pending_source', 'blocked_missing_source') }).Count -gt 0
    $reviewStatus = if ($hasPending) { 'partial_pending_program' } else { 'complete_exploratory' }
    return [ordered]@{
        schema_version = '0.2'; generated_by = 'program_set_core_review.py'; generator_version = $script:GeneratorVersion; template_version = $script:TemplateVersion; generated_at = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
        review_id = $(if ($ReviewId) { $ReviewId } else { "review-$stableFlowSlug--$stableProgramSetSlug" }); review_name = $ReviewName; review_slug = $reviewSlug
        flow_slug = $stableFlowSlug; program_set_slug = $stableProgramSetSlug; folder_slug = "$stableFlowSlug--$stableProgramSetSlug"; display_name = $ReviewName
        canonical_filename = $script:CanonicalReviewFilename; artifact_version = '0.2'; review_status = $reviewStatus; core_review_profile = $profile
        run_profile = [ordered]@{
            repo = $(if (Get-FlowMapValue $lookup 'repo') { Get-FlowMapValue $lookup 'repo' } else { Get-FlowMapValue $workspace 'repo' })
            working_branch = $WorkingBranch; artifact_root = [IO.Path]::GetFullPath($ArtifactRoot); artifact_repo_mode = $ArtifactRepoMode
            program_first = $ProgramFirst; cross_run_reuse = ($ArtifactRepoMode -eq 'approved_document_repo')
            reuse_policy = $(if ($ArtifactRepoMode -eq 'approved_document_repo') { 'approved_document_repo_clone' } else { 'current_run_only' })
        }
        program_resolution_profile = [ordered]@{ program_folder_patterns = @(Get-FlowMapValue $lookup 'program_folder_patterns' @('modules/*/{PROGRAM}')); program_name_normalization = Get-FlowMapValue $lookup 'program_name_normalization' ([ordered]@{}) }
        workspace_profile = [ordered]@{ program_set_review_parent = Get-FlowMapValue $workspace 'program_set_review_parent'; program_tier_roots = Get-FlowMapValue $workspace 'program_tier_roots' ([ordered]@{}); write_to_main = [bool](Get-FlowMapValue $workspace 'write_to_main' $false) }
        source_inventory = $inventory; programs = $built.Entries; warnings = $built.Warnings
    }
}

function Get-FlowArtifactSummary {
    param($Entry)
    $labels = foreach ($filename in $script:RequiredArtifacts) {
        $status = Get-FlowMapValue (Get-FlowMapValue $Entry.compact_artifacts (ConvertTo-FlowArtifactKey $filename) ([ordered]@{})) 'status' 'missing'
        "$filename=$status"
    }
    return $labels -join '; '
}

function Get-FlowPresentMissing {
    param($Entry, [string]$Filename)
    if ($Entry.run_resolution -notin @('analyzed_this_run', 'reused_same_run', 'reused_artifact_repo')) { return 'N/A' }
    $artifact = Get-FlowMapValue $Entry.compact_artifacts (ConvertTo-FlowArtifactKey $Filename) ([ordered]@{})
    return $(if ((Get-FlowMapValue $artifact 'status' 'missing') -eq 'present') { 'present' } else { 'missing' })
}

function Get-FlowReviewTables {
    param($Manifest)
    $sources = @('| Program | Analysis Directory | Run Resolution | Tier | Compact Artifacts Used | Follow-up |', '| --- | --- | --- | --- | --- | --- |')
    $ledger = @('| Program | Expected In Scope From | Run Resolution | Routine Logic Evidence | Message Inventory | Missing / Targeted Follow-up |', '| --- | --- | --- | --- | --- | --- |')
    foreach ($entry in @($Manifest.programs)) {
        $artifactRoot = if ($entry.artifact_root) { $entry.artifact_root } else { 'pending source scan' }
        $tier = if ($entry.tier) { $entry.tier } else { 'unknown' }
        $sources += "| $($entry.normalized_name) | $artifactRoot | $($entry.run_resolution) | $tier | $(Get-FlowArtifactSummary $entry) | $($entry.follow_up) |"
        $routineMd = Get-FlowPresentMissing $entry 'routine-logic-details.md'; $routineYaml = Get-FlowPresentMissing $entry 'routine-logic-details.yaml'
        $routine = if ($routineMd -eq 'present' -and $routineYaml -eq 'present') { 'present' } elseif ($routineMd -eq 'N/A') { 'N/A' } else { "missing: " + (@($(if ($routineMd -ne 'present') { 'routine-logic-details.md' }), $(if ($routineYaml -ne 'present') { 'routine-logic-details.yaml' })) | Where-Object { $_ }) -join ', ' }
        $ledger += "| $($entry.normalized_name) | SME-provided flow | $($entry.run_resolution) | $routine | $(Get-FlowPresentMissing $entry 'message-inventory.yaml') | $($entry.follow_up) |"
    }
    return [ordered]@{ Sources = $sources -join "`n"; Ledger = $ledger -join "`n" }
}

function ConvertTo-FlowCoreReviewSkeleton {
    param($Manifest)
    $tables = Get-FlowReviewTables $Manifest
    $run = $Manifest.run_profile; $resolution = $Manifest.program_resolution_profile; $workspace = $Manifest.workspace_profile; $inventory = $Manifest.source_inventory
    $profile = $Manifest.core_review_profile
    $messageSection = if ([bool]$profile.include_message_inventory) {
@"
## Message Inventory

<!-- Standard profile only: include every exact message/status/literal row. -->

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Condition / Handler | Effect | Detail Refs | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
"@
    } else { '' }
    $patterns = @($resolution.program_folder_patterns) -join ', '
    $runTable = @('| Field | Value |', '| --- | --- |', "| Repo | $($run.repo) |", "| Working Branch | $($run.working_branch) |", "| Artifact Root | $($run.artifact_root) |", "| Artifact Repo Mode | $($run.artifact_repo_mode) |", "| Reuse Policy | $($run.reuse_policy) |", "| Cross-Run Reuse | $(([string]$run.cross_run_reuse).ToLowerInvariant()) |", "| Program Folder Patterns | $patterns |", "| Program Set Review Parent | $($workspace.program_set_review_parent) |") -join "`n"
    $programListLabel = [IO.Path]::GetFileName([string]$inventory.program_list.path); $summaryLabel = [IO.Path]::GetFileName([string]$inventory.scan_summary.path)
    $inventoryLines = @('| Field | Value |', '| --- | --- |', "| Default Inventory Dir | $($inventory.default_inventory_dir) |", "| Inventory Dir Checked | $($inventory.inventory_dir) |", "| $programListLabel | $($inventory.program_list.status): $($inventory.program_list.path) |", "| $summaryLabel | $($inventory.scan_summary.status): $($inventory.scan_summary.path) |", "| Freshness | $($inventory.freshness) |", "| Action | $($inventory.action) |")
    if (@($inventory.programs).Count) {
        $inventoryLines += ''; $inventoryLines += '| Program | Run Resolution | Inventory Status | Source Path | Tier | Targeted Scan Allowed |'; $inventoryLines += '| --- | --- | --- | --- | --- | --- |'
        foreach ($row in @($inventory.programs)) { $inventoryLines += "| $($row.program) | $($row.run_resolution) | $($row.inventory_status) | $($row.source_path) | $($row.size_tier) | $(if ($row.targeted_scan_allowed) { 'yes' } else { 'no' }) |" }
    }
    return @"
# Program Set SME Core Review: $($Manifest.review_name)

## Program Set Reading Summary

<!-- Replace this placeholder with a SME-readable summary of what this program
set covers, what the merged core sections show, and whether the review is
complete_exploratory or partial_pending_program. Do not leave an artifact list
as the summary. -->

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First |
| --- | --- | --- |
| Program scope | [programs and main routines] | [what this set covers] |
| Calculation | [programs and main routines] | [reader-first explanation] |
| Validation | [programs and main routines] | [reader-first explanation] |
| Exception / message | [programs and main routines] | [reader-first explanation] |

## Calculation Logic

<!-- Self-contained SME view: write the actual calculation/assignment logic here.
Use Supporting Detail for traceability only, not as a substitute for the explanation. -->

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Validation Logic

<!-- Self-contained SME view: write the actual validation condition, status/code, carrier, and outcome here.
Use Supporting Detail for traceability only, not as a substitute for the explanation. -->

| Message / Status / Outcome | Description | Program | Routine | Condition / Evidence | Carrier / Destination | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Exception Handling

<!-- Self-contained SME view: write the actual error path, detection, handling action, and outcome here.
Use Supporting Detail for traceability only, not as a substitute for the explanation. -->

| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

$messageSection

## Core Completeness Ledger

$($tables.Ledger)

## Sources

$($tables.Sources)

## Run Profile

$runTable

## Source Inventory Cache

$($inventoryLines -join "`n")
"@
}

function Write-FlowCoreReviewOutputs {
    param($Manifest, [Parameter(Mandatory = $true)][string]$OutputDirectory)
    [IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
    $manifestPath = Join-Path $OutputDirectory 'program-set-core-input-manifest.yaml'
    $factsPath = Join-Path $OutputDirectory $script:CoreFactsFilename
    $reviewPath = Join-Path $OutputDirectory $script:CanonicalReviewFilename
    $factPrograms = foreach ($entry in @($Manifest.programs)) {
        $complete = $entry.run_resolution -in @('analyzed_this_run', 'reused_same_run', 'reused_artifact_repo')
        [ordered]@{
            program = $entry.normalized_name
            run_resolution = $entry.run_resolution
            source_status = $(if ($complete) { 'complete' } else { 'pending' })
            source_files = @()
            facts = [ordered]@{ calculations = @(); validations = @(); exceptions = @(); messages = @() }
            unresolved_reason = $(if ($complete) { 'PowerShell fallback does not synthesize facts; use explicit compact-artifact rows only.' } else { 'program-analysis compact artifacts are unavailable for this manifest program' })
        }
    }
    $facts = [ordered]@{
        schema_version = '0.1'; generated_by = 'program_set_core_review.py'; generator_version = $script:GeneratorVersion
        review_id = $Manifest.review_id; review_status = $Manifest.review_status; review_profile = $Manifest.core_review_profile
        flow_slug = $Manifest.flow_slug; program_set_slug = $Manifest.program_set_slug; folder_slug = $Manifest.folder_slug
        programs = @($factPrograms)
        evidence_boundary = 'Facts are copied only from explicit compact-artifact rows; program order is not a source-confirmed call edge.'
    }
    [IO.File]::WriteAllText($manifestPath, (ConvertTo-FlowYamlText $Manifest), $script:Utf8NoBom)
    [IO.File]::WriteAllText($factsPath, (ConvertTo-FlowYamlText $facts), $script:Utf8NoBom)
    [IO.File]::WriteAllText($reviewPath, (ConvertTo-FlowCoreReviewSkeleton $Manifest), $script:Utf8NoBom)
    return @($manifestPath, $factsPath, $reviewPath)
}

Export-ModuleMember -Function Read-FlowProgramsFile, New-FlowCoreReviewManifest, Write-FlowCoreReviewOutputs
