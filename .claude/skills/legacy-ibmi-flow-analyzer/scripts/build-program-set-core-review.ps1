<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Prepares the controlled inputs for an LLM reader-first program-set merger.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback for the deterministic preparation step.
It validates every program-analysis artifact and writes only merger inputs and
coverage controls. It never writes a draft or formal SME core review; the
executing skill's LLM owns that synthesis step.

CLI contract:
  --review-name --programs-file|--program --working-root --output-root
  --artifact-repo-mode --delivery-root --force-rescan-file --source-root
  --inventory-dir --program-first --profile --project-root|--output-dir --working-branch
#>
#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$moduleRoot = Join-Path $PSScriptRoot 'powershell'
Import-Module (Join-Path $moduleRoot 'FlowYaml.psm1') -Force
Import-Module (Join-Path $moduleRoot 'ProgramSetCoreReview.Builder.psm1') -Force

function Read-BuildArguments {
    param([object[]]$Arguments)
    $options = [ordered]@{
        ReviewName = $null; ProgramsFile = $null; Programs = @(); WorkingRoot = $null; OutputRoot = $null
        ArtifactRepoMode = 'approved_document_repo'; DeliveryRoot = $null; ForceRescanFile = $null
        SourceRoot = $null; InventoryDir = $null; ProgramFirst = $false; Profile = $null
        ProjectRoot = $null; OutputDir = $null; WorkingBranch = $null; CoreReviewProfile = $null; ReviewId = $null
        FlowSlug = $null; ProgramSetSlug = $null
    }
    $names = @{
        reviewname = 'ReviewName'; programsfile = 'ProgramsFile'; program = 'Program'; workingroot = 'WorkingRoot'
        outputroot = 'OutputRoot'; artifactrepomode = 'ArtifactRepoMode'; deliveryroot = 'DeliveryRoot'
        forcerescanfile = 'ForceRescanFile'; sourceroot = 'SourceRoot'; inventorydir = 'InventoryDir'
        programfirst = 'ProgramFirst'; profile = 'Profile'; projectroot = 'ProjectRoot'; outputdir = 'OutputDir'; workingbranch = 'WorkingBranch'
        corereviewprofile = 'CoreReviewProfile'; reviewid = 'ReviewId'; flowslug = 'FlowSlug'; programsetslug = 'ProgramSetSlug'
    }
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $raw = [string]$Arguments[$index]
        if (-not $raw.StartsWith('-')) { throw "Unexpected positional argument: $raw" }
        $key = $raw.TrimStart([char]'-').Replace('-', '').ToLowerInvariant()
        if (-not $names.ContainsKey($key)) { throw "Unknown argument: $raw" }
        $name = $names[$key]
        if ($name -eq 'ProgramFirst') { $options[$name] = $true; continue }
        if ($index + 1 -ge $Arguments.Count) { throw "Argument $raw requires a value" }
        $index++
        if ($name -eq 'Program') { $options.Programs += [string]$Arguments[$index] }
        else { $options[$name] = [string]$Arguments[$index] }
    }
    foreach ($required in @('ReviewName', 'Profile')) {
        if ([string]::IsNullOrWhiteSpace([string]$options[$required])) { throw "Missing required argument: --$($required.ToLowerInvariant())" }
    }
    if ($options.ProgramsFile -and $options.Programs.Count -gt 0) { throw 'provide exactly one of --programs-file or --program' }
    if (-not $options.ProgramsFile -and $options.Programs.Count -eq 0) { throw 'Missing required argument: --programs-file or --program' }
    if ($options.ProjectRoot -and $options.OutputDir) { throw 'provide exactly one of --project-root or --output-dir' }
    if (-not $options.ProjectRoot -and -not $options.OutputDir) { throw 'Missing required argument: --project-root or --output-dir' }
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
        throw '--force-rescan-file is no longer supported for program-flow core review. Use --artifact-repo-mode current_run explicitly when analyzing the program in the current run.'
    }
    if ($options.DeliveryRoot) {
        throw '--delivery-root is no longer supported for program-flow core review. Use --working-root <delivery-working-checkout> as the current-run artifact root.'
    }
    $artifactRoot = if ($options.WorkingRoot) { $options.WorkingRoot } else { $options.OutputRoot }
    if (-not $artifactRoot) { throw 'provide --working-root or --output-root for program artifacts' }
    if (-not (Test-Path -LiteralPath $artifactRoot -PathType Container)) { throw "artifact root not found or not a directory: $artifactRoot" }
    if ($options.ProgramsFile -and -not (Test-Path -LiteralPath $options.ProgramsFile -PathType Leaf)) { throw "programs file not found: $($options.ProgramsFile)" }
    if (-not (Test-Path -LiteralPath $options.Profile -PathType Leaf)) { throw "delivery profile not found: $($options.Profile)" }
    if ($options.SourceRoot -and -not (Test-Path -LiteralPath $options.SourceRoot -PathType Container)) { throw "source root not found or not a directory: $($options.SourceRoot)" }
    if ($options.ProjectRoot -and -not (Test-Path -LiteralPath $options.ProjectRoot -PathType Container)) { throw "project root not found or not a directory: $($options.ProjectRoot)" }
    $programs = if ($options.ProgramsFile) { @(Read-FlowProgramsFile $options.ProgramsFile) } else { @($options.Programs | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ }) }
    if ($programs.Count -eq 0) { throw 'program input has no program names' }
    $config = Read-FlowYamlFile $options.Profile
    if ($config -isnot [System.Collections.IDictionary]) { throw 'delivery profile must be a YAML mapping' }
    $programsFilePath = if ($options.ProgramsFile) { [IO.Path]::GetFullPath($options.ProgramsFile) } else { $null }
    $manifest = New-FlowCoreReviewManifest -ReviewName $options.ReviewName -Programs $programs -ArtifactRoot ([IO.Path]::GetFullPath($artifactRoot)) -Config $config -WorkingBranch $options.WorkingBranch -SourceRoot $options.SourceRoot -InventoryDir $options.InventoryDir -ProgramFirst ([bool]$options.ProgramFirst) -ArtifactRepoMode $options.ArtifactRepoMode -CoreReviewProfile $options.CoreReviewProfile -ReviewId $options.ReviewId -FlowSlug $options.FlowSlug -ProgramSetSlug $options.ProgramSetSlug -ProgramsFile $programsFilePath
    $outputDirectory = if ($options.ProjectRoot) { Join-Path ([IO.Path]::GetFullPath($options.ProjectRoot)) 'outputs' } else { [IO.Path]::GetFullPath($options.OutputDir) }
    $paths = @(Write-FlowCoreReviewOutputs -Manifest $manifest -OutputDirectory $outputDirectory)
    if ($paths.Count) { Write-Output "OUTPUT_DIR=$([IO.Path]::GetDirectoryName([string]$paths[0]))" }
    foreach ($path in $paths) { Write-Output "Wrote $path" }
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
