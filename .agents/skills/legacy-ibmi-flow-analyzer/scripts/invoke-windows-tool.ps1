<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Runs program-set flow tools from an installed skill directory on Windows.

.DESCRIPTION
Portable Windows PowerShell 5.1 launcher. It tries `py -3`, then a Python 3
`python` command, then the sibling native PowerShell implementation.
#>
#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('BuildProgramSetCoreReview', 'ValidateProgramSetCoreReview')]
    [string]$Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$definitions = @{
    BuildProgramSetCoreReview = @{
        Python = 'program_set_core_review.py'
        PythonPrefix = @('build')
        PowerShell = 'build-program-set-core-review.ps1'
    }
    ValidateProgramSetCoreReview = @{
        Python = 'program_set_core_review.py'
        PythonPrefix = @('validate')
        PowerShell = 'validate-program-set-core-review.ps1'
    }
}

$definition = $definitions[$Tool]
$pythonScript = Join-Path $PSScriptRoot $definition.Python
$powerShellScript = Join-Path $PSScriptRoot $definition.PowerShell
$pythonArguments = @($definition.PythonPrefix) + @($ToolArguments)
$pythonProbe = 'import sys, yaml; raise SystemExit(0 if sys.version_info.major == 3 else 1)'

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $pythonProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        & py -3 $pythonScript @pythonArguments
        exit $LASTEXITCODE
    }
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c $pythonProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        & python $pythonScript @pythonArguments
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
