<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Runs a Legacy Spec Factory tool on Windows with Python-first fallback routing.

.DESCRIPTION
Launcher order is `py -3`, then `python` when it is Python 3, then the native
Windows PowerShell implementation. Once a tool implementation starts, its exit
code is returned directly; validation or processing failures are never retried
with another implementation.
#>
#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        'InitializeProgramBatch',
        'ValidateProgramBatch',
        'IndexRpgSource',
        'ValidateProgramAnalysis',
        'BuildProgramSetCoreReview',
        'ValidateProgramSetCoreReview',
        'ValidateCurrentStateDiscovery'
    )]
    [string]$Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$ToolDefinitions = @{
    InitializeProgramBatch = @{
        Python = 'skills\legacy-ibmi-program-list-batch\scripts\initialize_program_batch.py'
        PowerShell = 'skills\legacy-ibmi-program-list-batch\scripts\initialize_program_batch.ps1'
    }
    ValidateProgramBatch = @{
        Python = 'skills\legacy-ibmi-program-list-batch\scripts\validate_program_batch_status.py'
        PowerShell = 'skills\legacy-ibmi-program-list-batch\scripts\validate_program_batch_status.ps1'
    }
    IndexRpgSource = @{
        Python = 'skills\legacy-ibmi-program-analyzer\scripts\index_rpg_source.py'
        PowerShell = 'skills\legacy-ibmi-program-analyzer\scripts\index-rpg-source.ps1'
    }
    ValidateProgramAnalysis = @{
        Python = 'skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py'
        PowerShell = 'skills\legacy-ibmi-program-analyzer\scripts\validate-program-analysis-contract.ps1'
    }
    BuildProgramSetCoreReview = @{
        Python = 'skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py'
        PythonPrefix = @('build')
        PowerShell = 'skills\legacy-ibmi-flow-analyzer\scripts\build-program-set-core-review.ps1'
    }
    ValidateProgramSetCoreReview = @{
        Python = 'skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py'
        PythonPrefix = @('validate')
        PowerShell = 'skills\legacy-ibmi-flow-analyzer\scripts\validate-program-set-core-review.ps1'
    }
    ValidateCurrentStateDiscovery = @{
        Python = 'skills\legacy-current-state-discovery\scripts\validate_current_state_discovery_package.py'
        PowerShell = 'skills\legacy-current-state-discovery\scripts\validate_current_state_discovery_package.ps1'
    }
}

$Definition = $ToolDefinitions[$Tool]
$PythonScript = Join-Path $RepositoryRoot $Definition.Python
$PowerShellScript = Join-Path $RepositoryRoot $Definition.PowerShell
$PythonPrefix = if ($Definition.ContainsKey('PythonPrefix')) { @($Definition.PythonPrefix) } else { @() }
$PythonArguments = @($PythonPrefix) + @($ToolArguments)
$RequiresYaml = $Tool -in @(
    'ValidateProgramAnalysis',
    'BuildProgramSetCoreReview',
    'ValidateProgramSetCoreReview'
)
if ($Tool -eq 'IndexRpgSource') {
    $RequiresYaml = @($ToolArguments | Where-Object {
        $_ -in @('--delivery-profile', '-delivery-profile', '-DeliveryProfile')
    }).Count -gt 0
}
$PythonProbe = if ($RequiresYaml) {
    'import sys, yaml; raise SystemExit(0 if sys.version_info.major == 3 else 1)'
} else {
    'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)'
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $PythonProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        & py -3 $PythonScript @PythonArguments
        exit $LASTEXITCODE
    }
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c $PythonProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        & python $PythonScript @PythonArguments
        exit $LASTEXITCODE
    }
}

if (Test-Path -LiteralPath $PowerShellScript -PathType Leaf) {
    $global:LASTEXITCODE = 0
    & $PowerShellScript @ToolArguments
    exit $LASTEXITCODE
}

Write-Error (
    "No runnable implementation for {0}: py -3 and python 3 are unavailable, " +
    "and the native PowerShell script is missing: {1}" -f $Tool, $PowerShellScript
)
exit 127
