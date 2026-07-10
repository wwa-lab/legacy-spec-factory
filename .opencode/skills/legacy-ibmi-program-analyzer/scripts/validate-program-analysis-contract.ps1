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
        '[--program-analysis <FILE>]'
    )
}

function Parse-CommandLine {
    param([object[]]$CommandLine)

    $parsed = @{ AnalysisDir = $null; ProgramAnalysis = $null }
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
    $findings = @(Invoke-ContractValidation $options.AnalysisDir $options.ProgramAnalysis)
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
