<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Runs current-state discovery validation from an installed skill directory.

.DESCRIPTION
Portable Windows PowerShell 5.1 launcher. It tries `py -3`, then a Python 3
`python` command, then the sibling native PowerShell implementation.
#>
#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('ValidateCurrentStateDiscovery')]
    [string]$Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pythonScript = Join-Path $PSScriptRoot 'validate_current_state_discovery_package.py'
$powerShellScript = Join-Path $PSScriptRoot 'validate_current_state_discovery_package.ps1'
$pythonProbe = 'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)'

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
