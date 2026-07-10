<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Runs program analyzer tools from an installed skill directory on Windows.

.DESCRIPTION
Portable Windows PowerShell 5.1 launcher. It tries `py -3`, then a Python 3
`python` command, then the sibling native PowerShell implementation.
#>
#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('IndexRpgSource', 'ValidateProgramAnalysis')]
    [string]$Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$definitions = @{
    IndexRpgSource = @{
        Python = 'index_rpg_source.py'
        PowerShell = 'index-rpg-source.ps1'
    }
    ValidateProgramAnalysis = @{
        Python = 'validate_program_analysis_contract.py'
        PowerShell = 'validate-program-analysis-contract.ps1'
    }
}

$definition = $definitions[$Tool]
$pythonScript = Join-Path $PSScriptRoot $definition.Python
$powerShellScript = Join-Path $PSScriptRoot $definition.PowerShell
$requiresYaml = $Tool -eq 'ValidateProgramAnalysis'
if ($Tool -eq 'IndexRpgSource') {
    $requiresYaml = @($ToolArguments | Where-Object {
        $_ -in @('--delivery-profile', '-delivery-profile', '-DeliveryProfile')
    }).Count -gt 0
}
$pythonProbe = if ($requiresYaml) {
    'import sys, yaml; raise SystemExit(0 if sys.version_info.major == 3 else 1)'
} else {
    'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)'
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $pythonProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        & py -3 $pythonScript @ToolArguments
        exit $LASTEXITCODE
    }
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c $pythonProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        & python $pythonScript @ToolArguments
        exit $LASTEXITCODE
    }
}

if (Test-Path -LiteralPath $powerShellScript -PathType Leaf) {
    $global:LASTEXITCODE = 0
    & $powerShellScript @ToolArguments
    exit $LASTEXITCODE
}

Write-Error "No runnable implementation for $Tool in installed skill directory: $PSScriptRoot"
exit 127
