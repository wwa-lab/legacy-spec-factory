#requires -version 5.1

<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
#>

# Native Windows PowerShell 5.1 fallback entry point. All contract checks use
# built-in PowerShell/.NET APIs and do not invoke Python or third-party modules.

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Show-Usage {
    [Console]::Error.WriteLine(
        'Usage: validate-program-analysis-contract.ps1 --analysis-dir <DIR> ' +
        '[--program-analysis <FILE>] [--expected-size-tier <TIER>] ' +
        '[--expected-source-index-sha256 <HEX>] [--expected-execution-plan-sha256 <HEX>]'
    )
}

function Parse-CommandLine {
    param([object[]]$CommandLine)

    $parsed = @{
        AnalysisDir = $null
        ProgramAnalysis = $null
        ExpectedSizeTier = $null
        ExpectedSourceIndexSha256 = $null
        ExpectedExecutionPlanSha256 = $null
    }
    for ($index = 0; $index -lt $CommandLine.Count; $index++) {
        $token = [string]$CommandLine[$index]
        if (@('--analysis-dir', '-analysis-dir', '-AnalysisDir') -contains $token) {
            if ($index + 1 -ge $CommandLine.Count) { throw "Missing value for $token" }
            $index++
            $parsed.AnalysisDir = [string]$CommandLine[$index]
        }
        elseif (@('--program-analysis', '-program-analysis', '-ProgramAnalysis') -contains $token) {
            if ($index + 1 -ge $CommandLine.Count) { throw "Missing value for $token" }
            $index++
            $parsed.ProgramAnalysis = [string]$CommandLine[$index]
        }
        elseif (@('--expected-size-tier', '-expected-size-tier', '-ExpectedSizeTier') -contains $token) {
            if ($index + 1 -ge $CommandLine.Count) { throw "Missing value for $token" }
            $index++
            $parsed.ExpectedSizeTier = [string]$CommandLine[$index]
        }
        elseif (@('--expected-source-index-sha256', '-expected-source-index-sha256', '-ExpectedSourceIndexSha256') -contains $token) {
            if ($index + 1 -ge $CommandLine.Count) { throw "Missing value for $token" }
            $index++
            $parsed.ExpectedSourceIndexSha256 = [string]$CommandLine[$index]
        }
        elseif (@('--expected-execution-plan-sha256', '-expected-execution-plan-sha256', '-ExpectedExecutionPlanSha256') -contains $token) {
            if ($index + 1 -ge $CommandLine.Count) { throw "Missing value for $token" }
            $index++
            $parsed.ExpectedExecutionPlanSha256 = [string]$CommandLine[$index]
        }
        elseif (@('--help', '-help', '-h', '/?') -contains $token) {
            $parsed.Help = $true
        }
        else {
            throw "Unknown argument: $token"
        }
    }
    return $parsed
}

try {
    $options = Parse-CommandLine @($args)
    if ($options.ContainsKey('Help') -and $options.Help) {
        Show-Usage
        exit 0
    }
    if (-not $options.AnalysisDir) {
        Show-Usage
        [Console]::Error.WriteLine('ERROR: --analysis-dir is required')
        exit 2
    }

    $modulePath = Join-Path (Join-Path $PSScriptRoot 'powershell') 'ProgramAnalysisContract.Validation.psm1'
    Import-Module $modulePath -Force
    $findings = @(Invoke-ContractValidation $options.AnalysisDir $options.ProgramAnalysis $options.ExpectedSizeTier $options.ExpectedSourceIndexSha256 $options.ExpectedExecutionPlanSha256)
    if ($findings.Count -gt 0) {
        foreach ($finding in $findings) { [Console]::Error.WriteLine("ERROR: $finding") }
        exit 1
    }
    [Console]::Out.WriteLine('Program analysis contract validation passed.')
    exit 0
}
catch {
    [Console]::Error.WriteLine("ERROR: $($_.Exception.Message)")
    exit 2
}
