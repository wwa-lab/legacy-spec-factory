<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Creates deterministic structure-first index artifacts for RPG source.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback for index_rpg_source.py. It has no
Python or third-party module dependency. The script intentionally extracts
only structural evidence and draft review surfaces; it does not infer business
rules or claim that the generated analysis is final.

The command line mirrors the Python implementation:

  index-rpg-source.ps1 SOURCE [--program NAME] [--out-dir DIR]
    [--delivery-root DIR] [--delivery-profile FILE]
    [--force-rescan] [--rescan-reason TEXT]
#>

#requires -version 5.1
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$moduleRoot = Join-Path $PSScriptRoot 'powershell'
. (Join-Path $moduleRoot 'IndexerCore.psm1')
. (Join-Path $moduleRoot 'IndexerAnalysis.psm1')
. (Join-Path $moduleRoot 'IndexerArtifacts.psm1')

try {
    $options = Parse-CliArguments $args
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}

if ($options.ForceRescan -and -not $options.RescanReason) {
    [Console]::Error.WriteLine('rescan_reason_required: --rescan-reason is required with --force-rescan')
    exit 4
}

$program = if ($options.Program) { $options.Program.ToUpperInvariant() } else { [System.IO.Path]::GetFileNameWithoutExtension($options.Source).ToUpperInvariant() }
$lookupResult = 'not_checked'
$artifactRoot = $null
$matches = @()
if ($options.DeliveryRoot) {
    if (-not (Test-Path -LiteralPath $options.DeliveryRoot -PathType Container)) {
        [Console]::Error.WriteLine('central_lookup_result: remote_unavailable')
        [Console]::Error.WriteLine('delivery_root_unavailable: ' + $options.DeliveryRoot)
        exit 3
    }
    try {
        $matches = @(Find-CentralArtifacts $options.DeliveryRoot $program $options.DeliveryProfile)
    } catch {
        [Console]::Error.WriteLine('central_lookup_result: remote_unavailable')
        [Console]::Error.WriteLine($_.Exception.Message)
        exit 3
    }
    if ($matches.Count -gt 0) {
        $lookupResult = 'found_on_remote_main'; $artifactRoot = $matches[0]
        Write-Output 'central_lookup_result: found_on_remote_main'
        Write-Output ('artifact_root: ' + $artifactRoot)
        if ($options.ForceRescan) {
            Write-Output 'action: force_rescan_requested'; Write-Output ('rescan_reason: ' + $options.RescanReason)
        } else {
            Write-Output 'action: reuse_existing_program_artifacts'
            Write-Output 'message: program already has approved artifacts on delivery remote main; source scan skipped'
            exit 0
        }
    } else {
        $lookupResult = 'not_found_on_remote_main'
        Write-Output 'central_lookup_result: not_found_on_remote_main'
        Write-Output 'action: proceed_to_source_scan'
    }
}

if (-not (Test-Path -LiteralPath $options.Source -PathType Leaf)) {
    [Console]::Error.WriteLine('Source file not found: ' + $options.Source)
    exit 2
}

$sourcePath = (Resolve-Path -LiteralPath $options.Source).Path
$lines = [System.IO.File]::ReadAllLines($sourcePath)
$sourceIndex = Analyze-Source $lines $program $sourcePath
if ($lookupResult -ne 'not_checked') {
    $decision = if ($options.ForceRescan -and $artifactRoot) { 'force_rescan_requested' } elseif ($options.ForceRescan) { 'force_rescan_requested_no_existing_central_artifact' } else { 'source_scan_required' }
    $sourceIndex['central_artifact_reuse'] = [ordered]@{ central_lookup_result = $lookupResult; artifact_root = $artifactRoot; matched_artifact_roots = $matches; force_rescan = $options.ForceRescan; rescan_reason = $(if ($options.RescanReason) { $options.RescanReason } else { 'not_applicable' }); reuse_decision = $decision }
}

try {
    $written = Write-Artifacts $sourceIndex $options.OutDir
    foreach ($path in $written) { Write-Output $path }
} catch {
    [Console]::Error.WriteLine('index_rpg_source_failed: ' + $_.Exception.Message)
    exit 1
}
exit 0
