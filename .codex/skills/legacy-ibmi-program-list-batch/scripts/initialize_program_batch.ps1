<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Initialize a Copilot Chat-friendly IBM i program-list batch without Python.

.DESCRIPTION
This is the native Windows PowerShell 5.1 fallback for
initialize_program_batch.py. It accepts both PowerShell-style parameters such
as -ProgramList and the GNU-style arguments forwarded by the shared runtime
router, such as --program-list.
#>

#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$StatusColumns = @(
    "batch_status",
    "validator_status",
    "scaffold_status",
    "output_dir",
    "prompt_path",
    "owner",
    "session_id",
    "started_at",
    "completed_at",
    "last_error",
    "next_action",
    "handoff_path"
)

$TierRoots = @{
    normal_program = "modules/CAP-ID-0003-normal_program"
    complex_normal_program = "modules/CAP-ID-0002-complex_normal_program"
    large_extreme_program = "modules/CAP-ID-0001-large_extreme_program"
}

$Utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false

function Get-CommandLineOptions {
    param([object[]]$Arguments)

    $options = @{
        ProgramList = $null
        ProgramsFile = $null
        OutDir = $null
        SourceRoot = $null
        DeliveryRoot = $null
        ReferencePath = @()
        ControlFile = @()
        ReviewName = "program list batch"
        Intent = "standalone_exploratory"
        ValidationMode = "immediate"
        ScaffoldMode = "none"
        Force = $false
    }
    $names = @{
        programlist = "ProgramList"
        programsfile = "ProgramsFile"
        outdir = "OutDir"
        sourceroot = "SourceRoot"
        deliveryroot = "DeliveryRoot"
        referencepath = "ReferencePath"
        controlfile = "ControlFile"
        reviewname = "ReviewName"
        intent = "Intent"
        validationmode = "ValidationMode"
        scaffoldmode = "ScaffoldMode"
        pythonlauncher = "IgnoredValue"
        force = "Force"
        deliveryprofile = "IgnoredValue"
        deliverymainsnapshot = "IgnoredValue"
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
        $optionName = $names[$normalizedName]
        if ($optionName -eq "Force") {
            $options.Force = $true
            continue
        }
        if ($index + 1 -ge $Arguments.Count) {
            throw "Argument $rawName requires a value"
        }
        $index++
        $value = [string]$Arguments[$index]
        if ($optionName -eq "ReferencePath" -or $optionName -eq "ControlFile") {
            $options[$optionName] = @($options[$optionName]) + @($value)
        }
        elseif ($optionName -ne "IgnoredValue") {
            $options[$optionName] = $value
        }
    }

    foreach ($required in @("ProgramList", "OutDir")) {
        if ([string]::IsNullOrWhiteSpace([string]$options[$required])) {
            throw "Missing required argument: $required"
        }
    }
    if ($options.ValidationMode -notin @("immediate", "deferred")) {
        throw "Invalid ValidationMode '$($options.ValidationMode)'. Expected immediate or deferred."
    }
    if ($options.ScaffoldMode -notin @("none", "precreate")) {
        throw "Invalid ScaffoldMode '$($options.ScaffoldMode)'. Expected none or precreate."
    }
    return $options
}

function Get-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Write-Utf8Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowEmptyString()][string]$Text
    )
    [System.IO.File]::WriteAllText($Path, $Text, $script:Utf8NoBom)
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
    return [string]$property.Value
}

function ConvertTo-NormalizedRow {
    param(
        [Parameter(Mandatory = $true)]$Row,
        [Parameter(Mandatory = $true)][string[]]$FieldNames
    )
    $values = [ordered]@{}
    foreach ($fieldName in $FieldNames) {
        $values[$fieldName] = (Get-FieldValue -Row $Row -Name $fieldName).Trim()
    }
    return [pscustomobject]$values
}

function ConvertTo-SafeFilename {
    param([AllowEmptyString()][string]$Value)
    $cleaned = [System.Text.RegularExpressions.Regex]::Replace($Value.Trim(), "[^\p{L}\p{N}@._-]+", "_")
    if ([string]::IsNullOrEmpty($cleaned)) {
        return "program"
    }
    return $cleaned
}

function Test-WindowsDisplayPath {
    param([AllowEmptyString()][string]$Value)
    return $Value.Contains("\") -or $Value -match "^[A-Za-z]:"
}

function Join-DisplayPath {
    param(
        [AllowNull()][AllowEmptyString()][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Parts
    )
    $cleanedParts = @(
        foreach ($part in $Parts) {
            if (-not [string]::IsNullOrEmpty($part)) {
                $part.Trim([char[]]@('/', '\'))
            }
        }
    )
    if (-not [string]::IsNullOrWhiteSpace($Root)) {
        $cleanedRoot = $Root.TrimEnd([char[]]@('/', '\'))
        if (Test-WindowsDisplayPath -Value $Root) {
            $windowsParts = @($cleanedRoot) + @($cleanedParts | ForEach-Object { $_.Replace('/', '\') })
            return $windowsParts -join "\"
        }
        $unixParts = @($cleanedRoot) + @($cleanedParts | ForEach-Object { $_.Replace('\', '/') })
        return $unixParts -join "/"
    }
    $placeholderParts = @("<delivery-root>") + @($cleanedParts | ForEach-Object { $_.Replace('\', '/') })
    return $placeholderParts -join "/"
}

function Join-LocalPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [AllowEmptyString()][string]$RelativePath
    )
    $cleanedRelative = $RelativePath.Trim([char[]]@('/', '\'))
    if ([string]::IsNullOrEmpty($cleanedRelative)) {
        return $Root
    }
    return Join-Path $Root $cleanedRelative
}

function Get-SourceDisplay {
    param(
        [AllowNull()][AllowEmptyString()][string]$SourceRoot,
        [AllowEmptyString()][string]$SourcePath
    )
    if (-not [string]::IsNullOrWhiteSpace($SourceRoot)) {
        return Join-DisplayPath -Root $SourceRoot -Parts @($SourcePath)
    }
    return "<source-root>/{0}" -f $SourcePath.Trim([char[]]@('/', '\'))
}

function Get-TierRoot {
    param([AllowEmptyString()][string]$SizeTier)
    $key = $SizeTier.Trim()
    if ($script:TierRoots.ContainsKey($key)) {
        return $script:TierRoots[$key]
    }
    return $script:TierRoots.normal_program
}

function Format-BulletList {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [AllowNull()][string[]]$Values
    )
    $cleaned = @($Values | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() })
    if ($cleaned.Count -eq 0) {
        return "- ${Label}: none provided"
    }
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("- ${Label}:")
    foreach ($value in $cleaned) {
        $lines.Add("  - $value")
    }
    return $lines -join "`n"
}

function Format-MarkdownCode {
    param([AllowEmptyString()][string]$Value)
    if ([string]::IsNullOrEmpty($Value)) {
        return ""
    }
    return [string]::Concat('`', $Value.Replace('`', '\`'), '`')
}

function Get-ValidationPolicy {
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$Member
    )
    $scaffoldCheck = "- Before writing final row status, open the generated ${Member}-program-analysis.md and ${Member}-routine-logic-details.md and confirm they do not contain scaffold language such as ``Draft wrapper seed generated``, ``pending semantic deep-read``, ``pending semantic detail``, ``placeholder``, ``not-yet-deep-read``, or ``not deep-read``."
    $layoutCheck = "- Always preserve the reader-first layout headings in the main file: ``### Routine Index For Calculation Logic``, ``### Routine Index For Validation Logic``, and ``### Routine Index For Exception Handling``, in that order under their corresponding H2 sections. Deferred mode still runs this cheap structural check; only the expensive semantic validator is deferred."
    if ($Mode -eq "deferred") {
        return @(
            "- Skip the program-analysis validator in this batch prompt to keep scan throughput high.",
            "- Do not mark this row ``completed`` or ``completed_with_warnings`` in deferred mode.",
            $scaffoldCheck,
            $layoutCheck,
            "- If required artifacts exist and the scaffold/layout checks are clean, set ``batch_status=scanned_unvalidated``, ``validator_status=deferred``, and ``next_action=run program-analysis validator before downstream use``.",
            "- If required artifacts are missing or scaffold/layout checks remain dirty after one targeted repair pass, mark ``batch_status=failed_validator``, preserve the finding in ``last_error``, and set a concrete ``next_action``."
        ) -join "`n"
    }
    return @(
        "- Run the program-analysis validator immediately after writing this program's artifacts and before starting the next prompt.",
        "- This validation is mandatory for every program in the Cline serial batch; do not use ``scanned_unvalidated`` in immediate mode.",
        $scaffoldCheck,
        $layoutCheck,
        "- If validation passes, set ``batch_status=completed`` and ``validator_status=pass``. Use ``completed_with_warnings`` only when the validator reports pass/pass_with_warnings and the warnings are non-blocking."
    ) -join "`n"
}

function Get-ValidationCommandBlock {
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$OutputDirectory
    )
    $command = "py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py --analysis-dir `"$OutputDirectory`""
    if ($Mode -eq "deferred") {
        return @(
            "Deferred in this batch prompt. Do not run this command now.",
            "Run before downstream use or final handoff:",
            $command
        ) -join "`n"
    }
    return $command
}

function Get-ValidationLauncherNote {
    param([Parameter(Mandatory = $true)][string]$Mode)
    if ($Mode -eq "deferred") {
        $firstLine = "- When final validation is run later, run the generated ``py -3 ...`` command first. If the Python Launcher is unavailable, run the same command again with ``python`` replacing ``py -3``."
    }
    else {
        $firstLine = "- Run the generated ``py -3 ...`` command first. If the Python Launcher is unavailable, run the same command again with ``python`` replacing ``py -3``."
    }
    return @(
        $firstLine,
        "- Do not replace it with PowerShell, ``.cmd``, ``.ps1``, shell continuations, or ``py ... || python ...``.",
        "- A validator failure is a result failure, not a reason to rerun it through another route."
    ) -join "`n"
}

function Get-ScaffoldPromptNote {
    param([AllowEmptyString()][string]$ScaffoldStatus)
    if ($ScaffoldStatus -eq "present") {
        return @(
            "- Scaffold artifacts were precreated during batch initialization.",
            "- Start by reading the existing source index, routine index, and routine logic YAML in the output directory.",
            "- Fill semantic details from source; do not rerun deterministic indexing unless the scaffold files are missing or stale."
        ) -join "`n"
    }
    if ($ScaffoldStatus.StartsWith("failed")) {
        return "- Scaffold precreation failed for this row. Resolve the recorded batch blocker before attempting semantic fill."
    }
    return "- If scaffold artifacts do not already exist, build deterministic indexes first."
}

function Get-IndexerScriptPath {
    $skillRoot = Split-Path -Parent $PSScriptRoot
    $skillsRoot = Split-Path -Parent $skillRoot
    return Join-Path (Join-Path (Join-Path $skillsRoot "legacy-ibmi-program-analyzer") "scripts") "index-rpg-source.ps1"
}

function Get-CurrentPowerShellExecutable {
    $processPath = (Get-Process -Id $PID).Path
    if (-not [string]::IsNullOrWhiteSpace($processPath) -and
        (Test-Path -LiteralPath $processPath -PathType Leaf)) {
        return $processPath
    }
    $coreCandidate = Join-Path $PSHOME "pwsh.exe"
    if (Test-Path -LiteralPath $coreCandidate -PathType Leaf) {
        return $coreCandidate
    }
    $windowsCandidate = Join-Path $PSHOME "powershell.exe"
    if (Test-Path -LiteralPath $windowsCandidate -PathType Leaf) {
        return $windowsCandidate
    }
    $command = Get-Command powershell -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    $command = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    throw "powershell_runtime_unavailable_for_scaffold_precreate"
}

function New-ProgramScaffold {
    param(
        [Parameter(Mandatory = $true)][string]$Member,
        [AllowNull()][AllowEmptyString()][string]$SourceRoot,
        [AllowEmptyString()][string]$SourcePath,
        [AllowEmptyString()][string]$OutputDirectory
    )
    if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
        return [pscustomobject]@{ Status = "blocked_missing_source"; Error = "source_root_required_for_scaffold_precreate" }
    }
    if ([string]::IsNullOrWhiteSpace($OutputDirectory) -or $OutputDirectory.StartsWith("<delivery-root>")) {
        return [pscustomobject]@{ Status = "failed_runtime"; Error = "delivery_root_required_for_scaffold_precreate" }
    }

    $sourceFile = Join-LocalPath -Root $SourceRoot -RelativePath $SourcePath
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        return [pscustomobject]@{ Status = "blocked_missing_source"; Error = "source_file_not_found_for_scaffold_precreate: $sourceFile" }
    }

    $indexer = Get-IndexerScriptPath
    if (-not (Test-Path -LiteralPath $indexer -PathType Leaf)) {
        return [pscustomobject]@{ Status = "failed_runtime"; Error = "indexer_script_not_found: $indexer" }
    }

    $powerShellExe = Get-CurrentPowerShellExecutable
    $output = & $powerShellExe "-NoProfile" "-NonInteractive" "-ExecutionPolicy" "Bypass" "-File" $indexer $sourceFile "--program" $Member "--out-dir" $OutputDirectory 2>&1
    if ($LASTEXITCODE -ne 0) {
        $message = ($output | ForEach-Object { [string]$_ }) -join "`n"
        if ([string]::IsNullOrWhiteSpace($message)) {
            $message = "exit_code_$LASTEXITCODE"
        }
        $lastLine = @($message -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 1)
        if ($lastLine.Count -gt 0) {
            $message = $lastLine[0]
        }
        return [pscustomobject]@{ Status = "failed_runtime"; Error = "scaffold_precreate_failed: $message" }
    }
    return [pscustomobject]@{ Status = "present"; Error = "" }
}

function Write-CsvFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$FieldNames,
        [AllowEmptyCollection()][object[]]$Rows
    )
    $lines = New-Object System.Collections.Generic.List[string]
    $header = @($FieldNames | ForEach-Object { '"' + $_.Replace('"', '""') + '"' }) -join ','
    $lines.Add($header)
    foreach ($row in @($Rows)) {
        $fields = foreach ($fieldName in $FieldNames) {
            $value = Get-FieldValue -Row $row -Name $fieldName
            '"' + $value.Replace('"', '""') + '"'
        }
        $lines.Add(($fields -join ','))
    }
    [System.IO.File]::WriteAllLines($Path, $lines, $script:Utf8NoBom)
}

function Read-ProgramsFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    $programs = New-Object System.Collections.Generic.List[string]
    $seen = @{}
    foreach ($rawLine in [System.IO.File]::ReadAllLines($Path, $script:Utf8NoBom)) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrEmpty($line) -or $line.StartsWith("#")) {
            continue
        }
        if ($line.StartsWith("-") -or $line.StartsWith("*")) {
            $line = $line.Substring(1).Trim()
        }
        foreach ($rawProgram in [regex]::Split($line, "(?:=>|->)")) {
            $program = $rawProgram.Trim().Trim([char[]]@(',', ';'))
            if ([string]::IsNullOrEmpty($program)) {
                continue
            }
            $key = $program.ToUpperInvariant()
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                $programs.Add($program)
            }
        }
    }
    return @($programs)
}

function Select-RequestedRows {
    param(
        [Parameter(Mandatory = $true)][object[]]$Rows,
        [Parameter(Mandatory = $true)][string[]]$Programs
    )
    $byMember = @{}
    foreach ($row in $Rows) {
        $member = (Get-FieldValue -Row $row -Name "member").Trim()
        if (-not [string]::IsNullOrEmpty($member) -and -not $byMember.ContainsKey($member.ToUpperInvariant())) {
            $byMember[$member.ToUpperInvariant()] = $row
        }
    }
    $selected = New-Object System.Collections.Generic.List[object]
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($program in $Programs) {
        $key = $program.ToUpperInvariant()
        if ($byMember.ContainsKey($key)) {
            $selected.Add($byMember[$key])
        }
        else {
            $missing.Add($program)
        }
    }
    if ($missing.Count -gt 0) {
        throw "programs-file contains programs not found in program-list.csv: $($missing -join ', ')"
    }
    return @($selected)
}

function ConvertTo-YamlScalar {
    param([AllowNull()]$Value)
    if ($null -eq $Value) {
        return "null"
    }
    if ($Value -is [bool]) {
        if ($Value) { return "true" }
        return "false"
    }
    if ($Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or
        $Value -is [int64] -or $Value -is [single] -or $Value -is [double] -or
        $Value -is [decimal]) {
        return [string]$Value
    }
    $text = [string]$Value
    if ($text.Length -eq 0) {
        return '""'
    }
    $isSafe = $text -match '^[\p{L}\p{N}_./:@#$%+*, <>\[\]-]+$'
    if ($isSafe -and $text.ToLowerInvariant() -notin @("true", "false", "null")) {
        return $text
    }
    return '"' + $text.Replace('\', '\\').Replace('"', '\"') + '"'
}

function ConvertTo-Yaml {
    param(
        [AllowNull()]$Value,
        [int]$Indent = 0
    )
    $pad = " " * $Indent
    $lines = New-Object System.Collections.Generic.List[string]
    if ($Value -is [System.Collections.IDictionary]) {
        foreach ($key in $Value.Keys) {
            $item = $Value[$key]
            $isCollection = $item -is [System.Collections.IDictionary] -or
                (($item -is [System.Collections.IEnumerable]) -and -not ($item -is [string]))
            if ($isCollection) {
                $lines.Add("${pad}${key}:")
                $nested = ConvertTo-Yaml -Value $item -Indent ($Indent + 2)
                if (-not [string]::IsNullOrEmpty($nested)) {
                    $lines.Add($nested)
                }
            }
            else {
                $lines.Add("${pad}${key}: $(ConvertTo-YamlScalar -Value $item)")
            }
        }
    }
    elseif (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
        foreach ($item in $Value) {
            if ($item -is [System.Collections.IDictionary]) {
                $lines.Add("${pad}-")
                $lines.Add((ConvertTo-Yaml -Value $item -Indent ($Indent + 2)))
            }
            else {
                $lines.Add("${pad}- $(ConvertTo-YamlScalar -Value $item)")
            }
        }
    }
    else {
        $lines.Add("${pad}$(ConvertTo-YamlScalar -Value $Value)")
    }
    return $lines -join "`n"
}

function Render-Prompt {
    param(
        [Parameter(Mandatory = $true)][string]$Template,
        [Parameter(Mandatory = $true)][string]$ProgramList,
        [Parameter(Mandatory = $true)][string]$OutDir,
        [Parameter(Mandatory = $true)]$Row,
        [AllowNull()][string]$SourceRoot,
        [AllowNull()][string]$DeliveryRoot,
        [Parameter(Mandatory = $true)][string]$Intent,
        [Parameter(Mandatory = $true)][string]$ValidationMode,
        [Parameter(Mandatory = $true)][string]$ScaffoldMode,
        [AllowNull()][string[]]$ReferencePaths,
        [AllowNull()][string[]]$ControlFiles
    )
    $member = Get-FieldValue -Row $Row -Name "member"
    $outputDirectory = Get-FieldValue -Row $Row -Name "output_dir"
    $replacements = [ordered]@{
        program_list = $ProgramList
        program_batch_plan = Join-Path $OutDir "program-batch-plan.md"
        program_list_status = Join-Path $OutDir "program-list-status.csv"
        batch_manifest = Join-Path $OutDir "batch-scan-manifest.yaml"
        member = $member
        source_path = Get-SourceDisplay -SourceRoot $SourceRoot -SourcePath (Get-FieldValue -Row $Row -Name "path")
        source_kind = Get-FieldValue -Row $Row -Name "source_kind"
        size_tier = Get-FieldValue -Row $Row -Name "size_tier"
        intent = $Intent
        output_dir = $outputDirectory
        validation_policy = Get-ValidationPolicy -Mode $ValidationMode -Member $member
        validation_command_block = Get-ValidationCommandBlock -Mode $ValidationMode -OutputDirectory $outputDirectory
        validation_launcher_note = Get-ValidationLauncherNote -Mode $ValidationMode
        scaffold_prompt_note = Get-ScaffoldPromptNote -ScaffoldStatus (Get-FieldValue -Row $Row -Name "scaffold_status")
        reference_paths = Format-BulletList -Label "Reference paths" -Values $ReferencePaths
        control_files = Format-BulletList -Label "Control files" -Values $ControlFiles
    }
    $rendered = $Template
    foreach ($key in $replacements.Keys) {
        $rendered = $rendered.Replace("{{$key}}", [string]$replacements[$key])
    }
    return $rendered
}

function Render-MarkdownTableRow {
    param(
        [Parameter(Mandatory = $true)][int]$Index,
        [Parameter(Mandatory = $true)]$Row
    )
    return "| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} |" -f @(
        $Index,
        (Get-FieldValue -Row $Row -Name "member"),
        (Format-MarkdownCode -Value (Get-FieldValue -Row $Row -Name "path")),
        (Get-FieldValue -Row $Row -Name "size_tier"),
        (Get-FieldValue -Row $Row -Name "batch_status"),
        (Get-FieldValue -Row $Row -Name "validator_status"),
        (Get-FieldValue -Row $Row -Name "owner"),
        (Format-MarkdownCode -Value (Get-FieldValue -Row $Row -Name "output_dir")),
        (Get-FieldValue -Row $Row -Name "next_action")
    )
}

function Get-StatusCount {
    param(
        [Parameter(Mandatory = $true)][object[]]$Rows,
        [Parameter(Mandatory = $true)][string]$Status
    )
    return @($Rows | Where-Object { (Get-FieldValue -Row $_ -Name "batch_status") -eq $Status }).Count
}

function Render-Plan {
    param(
        [Parameter(Mandatory = $true)][string]$ReviewName,
        [Parameter(Mandatory = $true)][string]$ProgramList,
        [Parameter(Mandatory = $true)][string]$OutDir,
        [Parameter(Mandatory = $true)][object[]]$Rows,
        [AllowNull()][string]$SourceRoot,
        [AllowNull()][string]$DeliveryRoot,
        [Parameter(Mandatory = $true)][string]$ValidationMode,
        [Parameter(Mandatory = $true)][string]$ScaffoldMode,
        [AllowNull()][string[]]$ReferencePaths,
        [AllowNull()][string[]]$ControlFiles
    )
    $blockedCount = @($Rows | Where-Object { (Get-FieldValue -Row $_ -Name "batch_status").StartsWith("blocked_") }).Count
    $failedCount = @($Rows | Where-Object { (Get-FieldValue -Row $_ -Name "batch_status").StartsWith("failed_") }).Count
    $nextRow = $Rows | Where-Object { (Get-FieldValue -Row $_ -Name "batch_status") -eq "queued" } | Select-Object -First 1
    $queueLines = New-Object System.Collections.Generic.List[string]
    for ($index = 0; $index -lt $Rows.Count; $index++) {
        $queueLines.Add((Render-MarkdownTableRow -Index ($index + 1) -Row $Rows[$index]))
    }
    $blockerLines = @(
        foreach ($row in $Rows) {
            $status = Get-FieldValue -Row $row -Name "batch_status"
            if ($status.StartsWith("blocked_") -or $status.StartsWith("failed_")) {
                "| {0} | {1} | {2} |" -f @(
                    (Get-FieldValue -Row $row -Name "member"),
                    (Get-FieldValue -Row $row -Name "last_error"),
                    (Get-FieldValue -Row $row -Name "next_action")
                )
            }
        }
    )
    if ($blockerLines.Count -eq 0) {
        $blockerLines = @("|  |  |  |")
    }
    $nextMember = "none"
    $nextPrompt = "none"
    $nextAction = "none"
    if ($null -ne $nextRow) {
        $nextMember = Get-FieldValue -Row $nextRow -Name "member"
        $nextPrompt = Format-MarkdownCode -Value (Get-FieldValue -Row $nextRow -Name "prompt_path")
        $nextAction = Get-FieldValue -Row $nextRow -Name "next_action"
    }
    $referenceText = if (@($ReferencePaths).Count -gt 0) { @($ReferencePaths) -join ", " } else { "none provided" }
    $controlText = if (@($ControlFiles).Count -gt 0) { @($ControlFiles) -join ", " } else { "none provided" }

    return @"
# Program Batch Plan

## Batch

- Review name: $ReviewName
- Program list: $ProgramList
- Status list: $(Join-Path $OutDir "program-list-status.csv")
- Manifest: $(Join-Path $OutDir "batch-scan-manifest.yaml")
- Source root: $SourceRoot
- Output root: $DeliveryRoot
- Validation mode: $ValidationMode
- Scaffold mode: $ScaffoldMode
- Reference paths: $referenceText
- Control files: $controlText
- Mode: Copilot Chat-only / one program per chat

## Progress

| Status | Count |
| --- | ---: |
| queued | $(Get-StatusCount -Rows $Rows -Status "queued") |
| in_progress | $(Get-StatusCount -Rows $Rows -Status "in_progress") |
| completed | $(Get-StatusCount -Rows $Rows -Status "completed") |
| completed_with_warnings | $(Get-StatusCount -Rows $Rows -Status "completed_with_warnings") |
| scanned_unvalidated | $(Get-StatusCount -Rows $Rows -Status "scanned_unvalidated") |
| blocked | $blockedCount |
| failed | $failedCount |
| skipped_not_program | $(Get-StatusCount -Rows $Rows -Status "skipped_not_program") |

## Current / Next

- Current program: none
- Current owner/session: none
- Next program: $nextMember
- Next prompt: $nextPrompt
- Next action: $nextAction

## Program Queue

| # | Program | Source | Tier | Status | Validator | Owner | Output | Next action |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
$($queueLines -join "`n")

## Blockers

| Program | Blocker | Needed to unblock |
| --- | --- | --- |
$($blockerLines -join "`n")
"@
}

function Invoke-Initializer {
    param([Parameter(Mandatory = $true)][hashtable]$Options)

    $programListPath = Get-FullPath -Path $Options.ProgramList
    $outDirPath = Get-FullPath -Path $Options.OutDir
    if ((Test-Path -LiteralPath $outDirPath -PathType Container) -and
        @(Get-ChildItem -LiteralPath $outDirPath -Force | Select-Object -First 1).Count -gt 0 -and
        -not $Options.Force) {
        throw "Output directory is not empty. Use --force to overwrite generated files: $outDirPath"
    }

    [System.IO.Directory]::CreateDirectory($outDirPath) | Out-Null
    $promptDir = Join-Path $outDirPath "prompt-queue"
    foreach ($directory in @($promptDir, (Join-Path $outDirPath "completed"), (Join-Path $outDirPath "blocked"), (Join-Path $outDirPath "failed"))) {
        [System.IO.Directory]::CreateDirectory($directory) | Out-Null
    }

    $rows = @(Import-Csv -LiteralPath $programListPath -Encoding UTF8)
    $headerLine = [System.IO.File]::ReadLines($programListPath) | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($headerLine)) {
        throw "program-list.csv must include a 'member' column"
    }
    $fieldNames = @($headerLine.Split(',') | ForEach-Object { $_.Trim([char]0xFEFF).Trim().Trim('"') })
    if ($fieldNames -cnotcontains "member") {
        throw "program-list.csv must include a 'member' column"
    }

    if (-not [string]::IsNullOrWhiteSpace([string]$Options.ProgramsFile)) {
        $programsPath = Get-FullPath -Path $Options.ProgramsFile
        $requestedPrograms = @(Read-ProgramsFile -Path $programsPath)
        if ($requestedPrograms.Count -eq 0) {
            throw "programs file has no program names"
        }
        $rows = @(Select-RequestedRows -Rows $rows -Programs $requestedPrograms)
        $programListPath = Join-Path $outDirPath "flow-program-list.csv"
        Write-CsvFile -Path $programListPath -FieldNames $fieldNames -Rows $rows
    }

    $statusFieldNames = New-Object System.Collections.Generic.List[string]
    foreach ($fieldName in $fieldNames) { $statusFieldNames.Add($fieldName) }
    foreach ($column in $script:StatusColumns) {
        if (-not $statusFieldNames.Contains($column)) {
            $statusFieldNames.Add($column)
        }
    }

    $templatePath = Join-Path (Split-Path -Parent $PSScriptRoot) "templates/copilot-single-program-prompt.md"
    $promptTemplate = [System.IO.File]::ReadAllText($templatePath, $script:Utf8NoBom)
    $statusRows = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $rows.Count; $index++) {
        $inputRow = ConvertTo-NormalizedRow -Row $rows[$index] -FieldNames $fieldNames
        $member = Get-FieldValue -Row $inputRow -Name "member"
        $objectType = Get-FieldValue -Row $inputRow -Name "object_type"
        $sizeTier = Get-FieldValue -Row $inputRow -Name "size_tier"
        $isProgram = $objectType.ToLowerInvariant() -eq "program"
        $outputDirectory = ""
        $promptPath = ""
        if ($isProgram) {
            if (-not [string]::IsNullOrEmpty($member)) {
                $outputDirectory = Join-DisplayPath -Root $Options.DeliveryRoot -Parts @((Get-TierRoot -SizeTier $sizeTier), $member)
            }
            $promptPath = Join-Path $promptDir ("{0:D4}-{1}.md" -f ($index + 1), (ConvertTo-SafeFilename -Value $member))
            $batchStatus = "queued"
            $nextAction = "start scan"
            $lastError = ""
            $scaffoldStatus = "not_created"
            if ($Options.ScaffoldMode -eq "precreate") {
                $scaffoldResult = New-ProgramScaffold `
                    -Member $member `
                    -SourceRoot $Options.SourceRoot `
                    -SourcePath (Get-FieldValue -Row $inputRow -Name "path") `
                    -OutputDirectory $outputDirectory
                $scaffoldStatus = $scaffoldResult.Status
                if ($scaffoldStatus -eq "present") {
                    $nextAction = "fill details from scaffold"
                }
                elseif ($scaffoldStatus -eq "blocked_missing_source") {
                    $batchStatus = "blocked_missing_source"
                    $nextAction = "fix source root/path, then regenerate scaffold"
                    $lastError = $scaffoldResult.Error
                }
                else {
                    $batchStatus = "failed_runtime"
                    $nextAction = "fix scaffold precreation issue, then rerun initializer for this program"
                    $lastError = $scaffoldResult.Error
                }
            }
        }
        else {
            $batchStatus = "skipped_not_program"
            $nextAction = "none - row is not a program"
            $lastError = ""
            $scaffoldStatus = "not_applicable"
        }

        $statusValues = [ordered]@{}
        foreach ($fieldName in $fieldNames) {
            $statusValues[$fieldName] = Get-FieldValue -Row $inputRow -Name $fieldName
        }
        $statusValues.batch_status = $batchStatus
        $statusValues.validator_status = "not_run"
        $statusValues.scaffold_status = $scaffoldStatus
        $statusValues.output_dir = $outputDirectory
        $statusValues.prompt_path = $promptPath
        $statusValues.owner = ""
        $statusValues.session_id = ""
        $statusValues.started_at = ""
        $statusValues.completed_at = ""
        $statusValues.last_error = $lastError
        $statusValues.next_action = $nextAction
        $statusValues.handoff_path = ""
        $statusRow = [pscustomobject]$statusValues
        $statusRows.Add($statusRow)

        if (-not [string]::IsNullOrEmpty($promptPath)) {
            $promptText = Render-Prompt `
                -Template $promptTemplate `
                -ProgramList $programListPath `
                -OutDir $outDirPath `
                -Row $statusRow `
                -SourceRoot $Options.SourceRoot `
                -DeliveryRoot $Options.DeliveryRoot `
                -Intent $Options.Intent `
                -ValidationMode $Options.ValidationMode `
                -ScaffoldMode $Options.ScaffoldMode `
                -ReferencePaths $Options.ReferencePath `
                -ControlFiles $Options.ControlFile
            Write-Utf8Text -Path $promptPath -Text $promptText
        }
    }

    Write-CsvFile -Path (Join-Path $outDirPath "program-list-status.csv") -FieldNames @($statusFieldNames) -Rows @($statusRows)
    $plan = Render-Plan `
        -ReviewName $Options.ReviewName `
        -ProgramList $programListPath `
        -OutDir $outDirPath `
        -Rows @($statusRows) `
        -SourceRoot $Options.SourceRoot `
        -DeliveryRoot $Options.DeliveryRoot `
        -ValidationMode $Options.ValidationMode `
        -ScaffoldMode $Options.ScaffoldMode `
        -ReferencePaths $Options.ReferencePath `
        -ControlFiles $Options.ControlFile
    Write-Utf8Text -Path (Join-Path $outDirPath "program-batch-plan.md") -Text $plan

    $timestamp = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:sszzz")
    $batchId = (ConvertTo-SafeFilename -Value $Options.ReviewName.ToLowerInvariant()).Trim('_')
    if ([string]::IsNullOrEmpty($batchId)) { $batchId = "program_list_batch" }
    $manifestPrograms = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $statusRows.Count; $index++) {
        $row = $statusRows[$index]
        $manifestPrograms.Add([ordered]@{
            order = $index + 1
            member = Get-FieldValue -Row $row -Name "member"
            object_type = Get-FieldValue -Row $row -Name "object_type"
            source_kind = Get-FieldValue -Row $row -Name "source_kind"
            source_path = Get-FieldValue -Row $row -Name "path"
            initial_size_tier = Get-FieldValue -Row $row -Name "size_tier"
            tier_reason = Get-FieldValue -Row $row -Name "tier_reason"
            batch_status = Get-FieldValue -Row $row -Name "batch_status"
            validator_status = Get-FieldValue -Row $row -Name "validator_status"
            scaffold_status = Get-FieldValue -Row $row -Name "scaffold_status"
            output_dir = Get-FieldValue -Row $row -Name "output_dir"
            prompt_path = Get-FieldValue -Row $row -Name "prompt_path"
            next_action = Get-FieldValue -Row $row -Name "next_action"
        })
    }
    $manifest = [ordered]@{
        batch_id = $batchId
        review_name = $Options.ReviewName
        program_list = $programListPath
        status_list = Join-Path $outDirPath "program-list-status.csv"
        program_batch_plan = Join-Path $outDirPath "program-batch-plan.md"
        source_root = $Options.SourceRoot
        output_root = $Options.DeliveryRoot
        validation_mode = $Options.ValidationMode
        scaffold_mode = $Options.ScaffoldMode
        reference_paths = @($Options.ReferencePath)
        control_files = @($Options.ControlFile)
        created_at = $timestamp
        updated_at = $timestamp
        status = "initialized"
        programs = @($manifestPrograms)
    }
    Write-Utf8Text -Path (Join-Path $outDirPath "batch-scan-manifest.yaml") -Text ((ConvertTo-Yaml -Value $manifest) + "`n")

    Write-Output "Initialized program batch: $outDirPath"
    $promptCount = @(Get-ChildItem -LiteralPath $promptDir -Filter "*.md" -File).Count
    Write-Output "Prompt files: $promptCount"
}

try {
    $parsedOptions = Get-CommandLineOptions -Arguments $args
    Invoke-Initializer -Options $parsedOptions
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
