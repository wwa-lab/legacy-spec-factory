<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Builds a program-set core-review manifest and reader-first skeleton.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback for the deterministic flow-review
builder. It accepts the same GNU-style options as the existing wrapper and has
no external runtime or third-party module dependency.

CLI contract:
  --review-name --programs-file --working-root --output-root
  --artifact-repo-mode --delivery-root --force-rescan-file --source-root
  --inventory-dir --program-first --profile --output-dir --working-branch
#>
#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$moduleRoot = Join-Path $PSScriptRoot 'powershell'
Import-Module (Join-Path $moduleRoot 'ProgramSetCoreReview.Builder.psm1') -Force

function Read-BuildArguments {
    param([object[]]$Arguments)
    $options = [ordered]@{
        ReviewName = $null; ProgramsFile = $null; WorkingRoot = $null; OutputRoot = $null
        ArtifactRepoMode = 'current_run'; DeliveryRoot = $null; ForceRescanFile = $null
        SourceRoot = $null; InventoryDir = $null; ProgramFirst = $false; Profile = $null
        OutputDir = $null; WorkingBranch = $null
    }
    $names = @{
        reviewname = 'ReviewName'; programsfile = 'ProgramsFile'; workingroot = 'WorkingRoot'
        outputroot = 'OutputRoot'; artifactrepomode = 'ArtifactRepoMode'; deliveryroot = 'DeliveryRoot'
        forcerescanfile = 'ForceRescanFile'; sourceroot = 'SourceRoot'; inventorydir = 'InventoryDir'
        programfirst = 'ProgramFirst'; profile = 'Profile'; outputdir = 'OutputDir'; workingbranch = 'WorkingBranch'
    }
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $raw = [string]$Arguments[$index]
        if (-not $raw.StartsWith('-')) { throw "Unexpected positional argument: $raw" }
        $key = $raw.TrimStart([char]'-').Replace('-', '').ToLowerInvariant()
        if (-not $names.ContainsKey($key)) { throw "Unknown argument: $raw" }
        $name = $names[$key]
        if ($name -eq 'ProgramFirst') { $options[$name] = $true; continue }
        if ($index + 1 -ge $Arguments.Count) { throw "Argument $raw requires a value" }
        $index++; $options[$name] = [string]$Arguments[$index]
    }
    foreach ($required in @('ReviewName', 'ProgramsFile', 'Profile', 'OutputDir')) {
        if ([string]::IsNullOrWhiteSpace([string]$options[$required])) { throw "Missing required argument: --$($required.ToLowerInvariant())" }
    }
    if ($options.ArtifactRepoMode -notin @('current_run', 'approved_document_repo')) {
        throw '--artifact-repo-mode must be current_run or approved_document_repo'
    }
    return $options
}

try {
    $options = Read-BuildArguments $args
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}

try {
    if ($options.ForceRescanFile) {
        throw '--force-rescan-file is no longer supported for program-flow core review. Rebuild with no cross-run reuse and analyze the program in the current run.'
    }
    if ($options.DeliveryRoot) {
        throw '--delivery-root is no longer supported for program-flow core review. Use --working-root <delivery-working-checkout> as the current-run artifact root.'
    }
    $artifactRoot = if ($options.WorkingRoot) { $options.WorkingRoot } else { $options.OutputRoot }
    if (-not $artifactRoot) { throw 'provide --working-root or --output-root for program artifacts' }
    if (-not (Test-Path -LiteralPath $artifactRoot -PathType Container)) { throw "artifact root not found or not a directory: $artifactRoot" }
    if (-not (Test-Path -LiteralPath $options.ProgramsFile -PathType Leaf)) { throw "programs file not found: $($options.ProgramsFile)" }
    if (-not (Test-Path -LiteralPath $options.Profile -PathType Leaf)) { throw "delivery profile not found: $($options.Profile)" }
    if ($options.SourceRoot -and -not (Test-Path -LiteralPath $options.SourceRoot -PathType Container)) { throw "source root not found or not a directory: $($options.SourceRoot)" }
    $programs = @(Read-FlowProgramsFile $options.ProgramsFile)
    if ($programs.Count -eq 0) { throw 'programs file has no program names' }
    $config = Read-FlowYamlFile $options.Profile
    if ($config -isnot [System.Collections.IDictionary]) { throw 'delivery profile must be a YAML mapping' }
    $manifest = New-FlowCoreReviewManifest -ReviewName $options.ReviewName -Programs $programs -ArtifactRoot ([IO.Path]::GetFullPath($artifactRoot)) -Config $config -WorkingBranch $options.WorkingBranch -SourceRoot $options.SourceRoot -InventoryDir $options.InventoryDir -ProgramFirst ([bool]$options.ProgramFirst) -ArtifactRepoMode $options.ArtifactRepoMode
    $paths = @(Write-FlowCoreReviewOutputs -Manifest $manifest -OutputDirectory ([IO.Path]::GetFullPath($options.OutputDir)))
    foreach ($path in $paths) { Write-Output "Wrote $path" }
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
