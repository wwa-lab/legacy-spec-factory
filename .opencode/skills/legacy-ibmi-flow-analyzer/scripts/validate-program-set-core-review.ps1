<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Validates a completed program-set SME core review.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback matching the deterministic validator's
manifest, reader-first section, completeness-ledger, and quality gates.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$moduleRoot = Join-Path $PSScriptRoot 'powershell'
Import-Module (Join-Path $moduleRoot 'ProgramSetCoreReview.Validator.psm1') -Force

function Read-ValidateArguments {
    param([object[]]$Arguments)
    $options = [ordered]@{ Manifest = $null; Review = $null }
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $raw = [string]$Arguments[$index]
        if (-not $raw.StartsWith('-')) { throw "Unexpected positional argument: $raw" }
        $name = $raw.TrimStart([char]'-').Replace('-', '').ToLowerInvariant()
        if ($name -notin @('manifest', 'review')) { throw "Unknown argument: $raw" }
        if ($index + 1 -ge $Arguments.Count) { throw "Argument $raw requires a value" }
        $index++
        if ($name -eq 'manifest') { $options.Manifest = [string]$Arguments[$index] }
        else { $options.Review = [string]$Arguments[$index] }
    }
    if (-not $options.Manifest) { throw 'Missing required argument: --manifest' }
    if (-not $options.Review) { throw 'Missing required argument: --review' }
    return $options
}

try {
    $options = Read-ValidateArguments $args
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}

try {
    $findings = @(Invoke-FlowCoreReviewValidation -ManifestPath $options.Manifest -ReviewPath $options.Review)
    if ($findings.Count) {
        foreach ($finding in $findings) { [Console]::Error.WriteLine("ERROR: $finding") }
        exit 1
    }
    Write-Output 'OK: program-set SME core review contract passed'
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
