<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Validate program-list batch state and completed output folders without Python.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback for the program-list batch status
validator. Both GNU-style arguments such as --batch-dir and PowerShell-style
arguments such as -BatchDir are accepted.
#>

#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$AllowedStatuses = New-Object -TypeName 'System.Collections.Generic.HashSet[string]' -ArgumentList ([System.StringComparer]::Ordinal)
foreach ($status in @(
    "queued",
    "in_progress",
    "completed",
    "completed_with_warnings",
    "blocked_missing_source",
    "failed_validator",
    "failed_runtime",
    "skipped_not_program"
)) {
    [void]$AllowedStatuses.Add($status)
}

$RequiredArtifacts = @(
    "program-analysis.md",
    "source-index.yaml",
    "program-analysis-summary.yaml",
    "routine-index.md",
    "message-inventory.yaml",
    "routine-logic-details.md",
    "routine-logic-details.yaml"
)

$ArtifactUnsafePattern = '[\s<>:"/\\|?*]+'
$ScaffoldTextBaseNames = @(
    "program-analysis.md",
    "routine-logic-details.md"
)
$ScaffoldPatterns = @(
    '\bDraft wrapper seed generated\b',
    '\bpending reader-oriented summary\b',
    '\bpending semantic deep-read\b',
    '\bpending semantic detail\b',
    '\breplace this placeholder\b',
    '\bplaceholder content\b',
    '\bnot-yet-deep-read\b'
)

function Get-CommandLineOptions {
    param([object[]]$Arguments)

    $options = @{
        BatchDir = $null
        StatusList = $null
        DeliveryRoot = $null
    }
    $names = @{
        batchdir = "BatchDir"
        statuslist = "StatusList"
        deliveryroot = "DeliveryRoot"
    }
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $rawName = [string]$Arguments[$index]
        if (-not $rawName.StartsWith("-")) {
            throw "Unexpected positional argument: $rawName"
        }
        $normalizedName = $rawName.TrimStart([char]'-').Replace("-", "").ToLowerInvariant()
        if (-not $names.ContainsKey($normalizedName)) {
            throw "Unknown argument: $rawName"
        }
        if ($index + 1 -ge $Arguments.Count) {
            throw "Argument $rawName requires a value"
        }
        $index++
        $options[$names[$normalizedName]] = [string]$Arguments[$index]
    }
    if ([string]::IsNullOrWhiteSpace([string]$options.BatchDir)) {
        throw "Missing required argument: BatchDir"
    }
    return $options
}

function Get-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Get-FieldValue {
    param(
        [Parameter(Mandatory = $true)]$Row,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $property = $Row.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) {
        return ""
    }
    return ([string]$property.Value).Trim()
}

function Get-ArtifactProgramPrefix {
    param([AllowEmptyString()][string]$ProgramName)

    $prefix = [regex]::Replace($ProgramName.Trim().ToUpperInvariant(), $script:ArtifactUnsafePattern, "_")
    $prefix = $prefix.Trim("._-")
    if ([string]::IsNullOrEmpty($prefix)) {
        return "PROGRAM"
    }
    return $prefix
}

function Get-RequiredArtifactName {
    param(
        [Parameter(Mandatory = $true)][string]$Member,
        [Parameter(Mandatory = $true)][string]$BaseName
    )
    return "$(Get-ArtifactProgramPrefix -ProgramName $Member)-$BaseName"
}

function Find-ScaffoldPatterns {
    param([Parameter(Mandatory = $true)][string]$Text)

    $matches = New-Object System.Collections.Generic.List[string]
    foreach ($pattern in $script:ScaffoldPatterns) {
        if ($Text -match $pattern) {
            $matches.Add($pattern.Replace('\b', ''))
        }
    }
    return @($matches)
}

function Resolve-OutputDirectory {
    param(
        [AllowEmptyString()][string]$Value,
        [AllowNull()][string]$DeliveryRoot
    )
    if ([string]::IsNullOrEmpty($Value) -or $Value.Contains("<delivery-root>")) {
        return $null
    }
    if ([System.IO.Path]::IsPathRooted($Value)) {
        return $Value
    }
    if (-not [string]::IsNullOrWhiteSpace($DeliveryRoot)) {
        return Join-Path $DeliveryRoot $Value
    }
    return $Value
}

function Invoke-Validation {
    param([Parameter(Mandatory = $true)][hashtable]$Options)

    $batchDir = Get-FullPath -Path $Options.BatchDir
    $statusPath = if ([string]::IsNullOrWhiteSpace([string]$Options.StatusList)) {
        Join-Path $batchDir "program-list-status.csv"
    }
    else {
        Get-FullPath -Path $Options.StatusList
    }
    $manifestPath = Join-Path $batchDir "batch-scan-manifest.yaml"
    $planPath = Join-Path $batchDir "program-batch-plan.md"
    $deliveryRoot = if ([string]::IsNullOrWhiteSpace([string]$Options.DeliveryRoot)) {
        $null
    }
    else {
        Get-FullPath -Path $Options.DeliveryRoot
    }

    $findings = New-Object System.Collections.Generic.List[string]
    $warnings = New-Object System.Collections.Generic.List[string]
    if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) {
        $findings.Add("Missing status CSV: $statusPath")
        $rows = @()
    }
    else {
        $rows = @(Import-Csv -LiteralPath $statusPath -Encoding UTF8)
    }
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        $findings.Add("Missing batch manifest: $manifestPath")
    }
    if (-not (Test-Path -LiteralPath $planPath -PathType Leaf)) {
        $findings.Add("Missing program batch plan: $planPath")
    }

    $seenMembers = New-Object -TypeName 'System.Collections.Generic.Dictionary[string,int]' -ArgumentList ([System.StringComparer]::Ordinal)
    $outputDirectories = New-Object -TypeName 'System.Collections.Generic.Dictionary[string,string]' -ArgumentList ([System.StringComparer]::Ordinal)
    for ($offset = 0; $offset -lt $rows.Count; $offset++) {
        $index = $offset + 1
        $row = $rows[$offset]
        $member = Get-FieldValue -Row $row -Name "member"
        $status = Get-FieldValue -Row $row -Name "batch_status"
        $validatorStatus = Get-FieldValue -Row $row -Name "validator_status"
        $outputDirectoryValue = Get-FieldValue -Row $row -Name "output_dir"

        if ([string]::IsNullOrEmpty($member)) {
            $findings.Add("Row ${index}: missing member")
        }
        elseif ($seenMembers.ContainsKey($member)) {
            $warnings.Add("Duplicate member '$member' at rows $($seenMembers[$member]) and $index")
        }
        else {
            $seenMembers.Add($member, $index)
        }

        if (-not $script:AllowedStatuses.Contains($status)) {
            $findings.Add("Row $index ${member}: invalid batch_status '$status'")
        }
        if ($status -eq "in_progress" -and
            [string]::IsNullOrEmpty((Get-FieldValue -Row $row -Name "owner")) -and
            [string]::IsNullOrEmpty((Get-FieldValue -Row $row -Name "session_id"))) {
            $warnings.Add("Row $index ${member}: in_progress without owner/session_id")
        }
        if ($status -in @("blocked_missing_source", "failed_validator", "failed_runtime")) {
            if ([string]::IsNullOrEmpty((Get-FieldValue -Row $row -Name "last_error"))) {
                $findings.Add("Row $index ${member}: $status requires last_error")
            }
            if ([string]::IsNullOrEmpty((Get-FieldValue -Row $row -Name "next_action"))) {
                $findings.Add("Row $index ${member}: $status requires next_action")
            }
        }

        $outputPath = Resolve-OutputDirectory -Value $outputDirectoryValue -DeliveryRoot $deliveryRoot
        if (-not [string]::IsNullOrEmpty($outputDirectoryValue) -and
            -not $outputDirectoryValue.Contains("<delivery-root>")) {
            if ($outputDirectories.ContainsKey($outputDirectoryValue) -and $status -ne "skipped_not_program") {
                $findings.Add("Rows for $($outputDirectories[$outputDirectoryValue]) and $member share output_dir $outputDirectoryValue")
            }
            $outputDirectories[$outputDirectoryValue] = $member
        }

        if ($status -eq "completed" -and $validatorStatus -ne "pass") {
            $findings.Add("Row $index ${member}: completed requires validator_status pass")
        }
        if ($status -eq "completed_with_warnings" -and $validatorStatus -notin @("pass", "pass_with_warnings")) {
            $findings.Add("Row $index ${member}: completed_with_warnings requires validator_status pass/pass_with_warnings")
        }
        if ($status -in @("completed", "completed_with_warnings")) {
            if ($null -eq $outputPath) {
                $warnings.Add("Row $index ${member}: cannot verify placeholder/empty output_dir '$outputDirectoryValue'")
                continue
            }
            if (-not (Test-Path -LiteralPath $outputPath -PathType Container)) {
                $findings.Add("Row $index ${member}: output_dir does not exist: $outputPath")
                continue
            }
            $requiredArtifactsForMember = @(
                $script:RequiredArtifacts |
                    ForEach-Object { Get-RequiredArtifactName -Member $member -BaseName $_ }
            )
            $missing = @(
                $requiredArtifactsForMember |
                    Where-Object { -not (Test-Path -LiteralPath (Join-Path $outputPath $_) -PathType Leaf) } |
                    Sort-Object
            )
            if ($missing.Count -gt 0) {
                $findings.Add("Row $index ${member}: missing required artifacts: $($missing -join ', ')")
            }
            foreach ($baseName in $script:ScaffoldTextBaseNames) {
                $artifactName = Get-RequiredArtifactName -Member $member -BaseName $baseName
                $artifactPath = Join-Path $outputPath $artifactName
                if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) {
                    continue
                }
                $artifactText = [System.IO.File]::ReadAllText($artifactPath, [System.Text.Encoding]::UTF8)
                $matchedPatterns = @(Find-ScaffoldPatterns -Text $artifactText)
                if ($matchedPatterns.Count -gt 0) {
                    $findings.Add(
                        "Row $index ${member}: $artifactName still appears to be a scaffold or pending deep-read artifact; " +
                        "run semantic source deep-read and replace placeholder content before marking completed. Matched: " +
                        ($matchedPatterns -join ', ')
                    )
                }
            }
        }
    }

    foreach ($warning in $warnings) {
        Write-Output "WARNING: $warning"
    }
    if ($findings.Count -gt 0) {
        foreach ($finding in $findings) {
            Write-Output "ERROR: $finding"
        }
        Write-Output "Batch status validation failed: $($findings.Count) error(s), $($warnings.Count) warning(s)"
        return 1
    }
    Write-Output "Batch status validation passed: $($rows.Count) row(s), $($warnings.Count) warning(s)"
    return 0
}

try {
    $parsedOptions = Get-CommandLineOptions -Arguments $args
    $exitCode = Invoke-Validation -Options $parsedOptions
    exit $exitCode
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
