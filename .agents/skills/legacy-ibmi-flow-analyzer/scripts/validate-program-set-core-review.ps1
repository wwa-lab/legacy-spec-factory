<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Validates a completed program-set SME core review.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback matching the controlled merger's
manifest, source-pack, normalized-fact, coverage, and reader-first review gates.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$moduleRoot = Join-Path $PSScriptRoot 'powershell'
Import-Module (Join-Path $moduleRoot 'ProgramSetCoreReview.Validator.psm1') -Force

function Read-ValidateArguments {
    param([object[]]$Arguments)
    $options = [ordered]@{ Manifest = $null; Review = $null; SourcePack = $null; CoreFacts = $null; Coverage = $null }
    $names = @{
        manifest = 'Manifest'; review = 'Review'; sourcepack = 'SourcePack'
        corefacts = 'CoreFacts'; coverage = 'Coverage'
    }
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $raw = [string]$Arguments[$index]
        if (-not $raw.StartsWith('-')) { throw "Unexpected positional argument: $raw" }
        $name = $raw.TrimStart([char]'-').Replace('-', '').ToLowerInvariant()
        if (-not $names.ContainsKey($name)) { throw "Unknown argument: $raw" }
        if ($index + 1 -ge $Arguments.Count) { throw "Argument $raw requires a value" }
        $index++
        $options[$names[$name]] = [string]$Arguments[$index]
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
    $findings = @(Invoke-FlowCoreReviewValidation -ManifestPath $options.Manifest -ReviewPath $options.Review -SourcePackPath $options.SourcePack -CoreFactsPath $options.CoreFacts -CoveragePath $options.Coverage)
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
