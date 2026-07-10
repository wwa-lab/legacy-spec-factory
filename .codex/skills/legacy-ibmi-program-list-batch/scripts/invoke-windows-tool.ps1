<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Runs program-list batch tools from an installed skill directory on Windows.

.DESCRIPTION
Portable Windows PowerShell 5.1 launcher. It tries `py -3`, then a Python 3
`python` command, then the sibling native PowerShell implementation. Keep this
launcher inside the skill so `.agents`, `.claude`, `.codex`, and `.opencode`
copies do not depend on a repository-root script.
#>
#requires -version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('InitializeProgramBatch', 'ValidateProgramBatch')]
    [string]$Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$definitions = @{
    InitializeProgramBatch = @{
        Python = 'initialize_program_batch.py'
        PowerShell = 'initialize_program_batch.ps1'
    }
    ValidateProgramBatch = @{
        Python = 'validate_program_batch_status.py'
        PowerShell = 'validate_program_batch_status.ps1'
    }
}

$definition = $definitions[$Tool]
$pythonScript = Join-Path $PSScriptRoot $definition.Python
$powerShellScript = Join-Path $PSScriptRoot $definition.PowerShell
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
