<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

.SYNOPSIS
Validate a legacy-current-state-discovery package without Python.

.DESCRIPTION
Native Windows PowerShell 5.1 fallback for the current-state discovery
package validator. It preserves the Python validator's positional package
argument, GNU-style switches, findings, and exit codes.
#>

#requires -version 5.1

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$RequiredFiles = @(
    "discovery-index.yaml",
    "document-master-index.md",
    "behavior-claim-ledger.csv",
    "functional-discovery-report.md",
    "function-catalog.yaml",
    "project-derived-feature-index.yaml",
    "validation-catalog.yaml",
    "calculation-catalog.yaml",
    "interface-register.yaml",
    "channel-ui-report-catalog.md",
    "accounting-gl-ie-index.yaml",
    "traceability-matrix.csv",
    "open-questions-and-gaps.md"
)

$TraceabilityHeader = @(
    "item_id", "item_type", "item_name", "claim_summary", "source_id",
    "source_location", "evidence_id", "evidence_strength", "confidence",
    "review_status", "gap_id", "notes"
)

$BehaviorClaimHeader = @(
    "claim_id", "item_type", "item_id", "business_area", "business_meaning",
    "trigger_condition", "system_behavior", "source_id", "source_location",
    "evidence_id", "evidence_strength", "confidence", "review_status",
    "gap_id", "next_action", "notes"
)

$WeakStandalonePhrases = @(
    "likely exists",
    "suggests one",
    "appears related",
    "diagram shows one candidate",
    "folder contains",
    "source set includes"
)

$GenericItemPrefix = "CLM-"

$ReportHeadings = @(
    "## 1. Existing Functionality",
    "## 2. Process Flow",
    "## 3. Upstream / Downstream Applications",
    "## 4. System Configuration / Parameter",
    "## 5. Channels",
    "## 6. Report",
    "## 7. Customer Communication, Triggers, and Associated Requirement",
    "## 8. Operational Procedure",
    "## 9. Current Limitation / Pain Point",
    "## 10. Gap Analysis",
    "## 11. Cross Reference BRD"
)

$YamlMarkers = [ordered]@{
    "discovery-index.yaml" = @(
        "package_type: current_state_discovery", "status:", "outputs:"
    )
    "function-catalog.yaml" = @("catalog_type: function_catalog", "functions:")
    "project-derived-feature-index.yaml" = @(
        "catalog_type: project_derived_feature_index", "features:"
    )
    "validation-catalog.yaml" = @(
        "catalog_type: validation_catalog", "validations:"
    )
    "calculation-catalog.yaml" = @(
        "catalog_type: calculation_catalog", "calculations:"
    )
    "interface-register.yaml" = @(
        "catalog_type: interface_register", "interfaces:"
    )
    "accounting-gl-ie-index.yaml" = @(
        "catalog_type: accounting_gl_ie_index", "accounting_impacts:"
    )
}

function Show-Usage {
    [Console]::Out.WriteLine(
        "usage: validate_current_state_discovery_package.ps1 " +
        "[-h] [--allow-placeholders] [--require-ready] [--quality-gate] package"
    )
}

function Get-CommandLineOptions {
    param([object[]]$Arguments)

    $options = @{
        Package = $null
        AllowPlaceholders = $false
        RequireReady = $false
        QualityGate = $false
        Help = $false
    }
    $positionalsOnly = $false
    foreach ($argument in $Arguments) {
        $token = [string]$argument
        if (-not $positionalsOnly -and $token -ceq "--") {
            $positionalsOnly = $true
        }
        elseif (-not $positionalsOnly -and ($token -ceq "-h" -or $token -ceq "--help")) {
            $options.Help = $true
        }
        elseif (-not $positionalsOnly -and $token -ceq "--allow-placeholders") {
            $options.AllowPlaceholders = $true
        }
        elseif (-not $positionalsOnly -and $token -ceq "--require-ready") {
            $options.RequireReady = $true
        }
        elseif (-not $positionalsOnly -and $token -ceq "--quality-gate") {
            $options.QualityGate = $true
        }
        elseif (-not $positionalsOnly -and $token.StartsWith("-")) {
            throw "unrecognized arguments: $token"
        }
        elseif ($null -ne $options.Package) {
            throw "unrecognized arguments: $token"
        }
        else {
            $options.Package = $token
        }
    }
    if (-not $options.Help -and [string]::IsNullOrWhiteSpace([string]$options.Package)) {
        throw "the following arguments are required: package"
    }
    return $options
}

function Read-Utf8Text {
    param([string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    return [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Test-HasUtf8Bom {
    param([string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    return (
        $bytes.Length -ge 3 -and
        $bytes[0] -eq 0xEF -and
        $bytes[1] -eq 0xBB -and
        $bytes[2] -eq 0xBF
    )
}

function Test-ContainsOrdinal {
    param([string]$Text, [string]$Value)

    return $Text.IndexOf($Value, [System.StringComparison]::Ordinal) -ge 0
}

function Get-CsvHeader {
    param([string]$Path)

    [string]$text = Read-Utf8Text $Path
    if ($text.Length -eq 0) {
        return @()
    }
    $fields = @()
    $field = New-Object System.Text.StringBuilder
    $insideQuotes = $false
    $recordHasSyntax = $false
    for ($index = 0; $index -lt $text.Length; $index++) {
        $character = $text[$index]
        if ($character -eq [char]'"') {
            $recordHasSyntax = $true
            if ($insideQuotes -and $index + 1 -lt $text.Length -and
                $text[$index + 1] -eq [char]'"') {
                [void]$field.Append('"')
                $index++
            }
            else {
                $insideQuotes = -not $insideQuotes
            }
        }
        elseif (-not $insideQuotes -and $character -eq [char]',') {
            $recordHasSyntax = $true
            $fields += $field.ToString()
            [void]$field.Clear()
        }
        elseif (-not $insideQuotes -and
            ($character -eq [char]"`r" -or $character -eq [char]"`n")) {
            break
        }
        else {
            $recordHasSyntax = $true
            [void]$field.Append($character)
        }
    }
    if (-not $recordHasSyntax -and $fields.Count -eq 0 -and $field.Length -eq 0) {
        return @()
    }
    $fields += $field.ToString()
    return @($fields)
}

function Test-HeadersEqual {
    param([object[]]$Actual, [object[]]$Expected)

    if ($Actual.Count -ne $Expected.Count) {
        return $false
    }
    for ($index = 0; $index -lt $Expected.Count; $index++) {
        if (-not [string]::Equals(
            [string]$Actual[$index],
            [string]$Expected[$index],
            [System.StringComparison]::Ordinal
        )) {
            return $false
        }
    }
    return $true
}

function Get-CsvRows {
    param([string]$Path)

    if ((Get-Item -LiteralPath $Path).Length -eq 0) {
        return @{ Rows = @(); FirstHeaderHasBom = $false }
    }
    return @{
        Rows = @(Import-Csv -LiteralPath $Path -Encoding UTF8)
        FirstHeaderHasBom = (Test-HasUtf8Bom $Path)
    }
}

function Get-RowField {
    param([object]$Row, [string]$Name)

    $property = $null
    foreach ($candidate in $Row.PSObject.Properties) {
        if ([string]::Equals(
            [string]$candidate.Name,
            $Name,
            [System.StringComparison]::Ordinal
        )) {
            $property = $candidate
            break
        }
    }
    if ($null -eq $property -or $null -eq $property.Value) {
        return ""
    }
    return ([string]$property.Value).Trim()
}

function Test-RequiredFiles {
    param([string]$Package)

    $errors = @()
    foreach ($name in $RequiredFiles) {
        $path = Join-Path $Package $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            $errors += "missing required file: $name"
        }
        elseif ((Get-Item -LiteralPath $path).Length -eq 0) {
            $errors += "empty required file: $name"
        }
    }
    $warnings = @()
    if ($errors.Count -eq 0) {
        $warnings += "all required files are present"
    }
    return @{ Errors = @($errors); Warnings = @($warnings) }
}

function Test-YamlMarkers {
    param([string]$Package)

    $errors = @()
    foreach ($name in $YamlMarkers.Keys) {
        $path = Join-Path $Package $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            continue
        }
        $text = Read-Utf8Text $path
        foreach ($marker in $YamlMarkers[$name]) {
            if (-not (Test-ContainsOrdinal $text $marker)) {
                $errors += "$name missing marker: $marker"
            }
        }
    }
    return @($errors)
}

function Test-Report {
    param([string]$Package)

    $errors = @()
    $path = Join-Path $Package "functional-discovery-report.md"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return @()
    }
    $text = Read-Utf8Text $path
    foreach ($heading in $ReportHeadings) {
        if (-not (Test-ContainsOrdinal $text $heading)) {
            $errors += "functional-discovery-report.md missing heading: $heading"
        }
    }
    return @($errors)
}

function Test-CsvHeader {
    param([string]$Package, [string]$Name, [object[]]$Expected)

    $errors = @()
    $path = Join-Path $Package $Name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return @()
    }
    $header = @(Get-CsvHeader $path)
    if ((Get-Item -LiteralPath $path).Length -eq 0) {
        $errors += "$Name is empty"
        return @($errors)
    }
    if (-not (Test-HeadersEqual $header $Expected)) {
        $errors += "$Name header mismatch: expected $($Expected -join ',')"
    }
    return @($errors)
}

function Test-Placeholders {
    param([string]$Package, [bool]$AllowPlaceholders)

    if ($AllowPlaceholders) {
        return @()
    }
    $errors = @()
    foreach ($name in $RequiredFiles) {
        $path = Join-Path $Package $name
        $extension = [System.IO.Path]::GetExtension($name)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
            @(".md", ".yaml", ".csv") -cnotcontains $extension) {
            continue
        }
        $text = Read-Utf8Text $path
        if ((Test-ContainsOrdinal $text "<") -and (Test-ContainsOrdinal $text ">")) {
            $errors += "$name still appears to contain template placeholders"
        }
    }
    return @($errors)
}

function Test-ReadyStatus {
    param([string]$Package, [bool]$RequireReady)

    if (-not $RequireReady) {
        return @()
    }
    $path = Join-Path $Package "discovery-index.yaml"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return @()
    }
    $text = Read-Utf8Text $path
    if (-not (Test-ContainsOrdinal $text "status: ready_for_sme_review") -and
        -not (Test-ContainsOrdinal $text "status: ready_with_warnings")) {
        return @(
            "discovery-index.yaml status is not ready_for_sme_review or ready_with_warnings"
        )
    }
    return @()
}

function Test-QualityGate {
    param([string]$Package)

    $errors = @()
    $path = Join-Path $Package "behavior-claim-ledger.csv"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return @()
    }
    $csvData = Get-CsvRows $path
    $rows = @($csvData.Rows)
    if ($rows.Count -eq 0) {
        return @("behavior-claim-ledger.csv has no claim rows")
    }

    $substantiveRows = @()
    for ($offset = 0; $offset -lt $rows.Count; $offset++) {
        $row = $rows[$offset]
        $rowNumber = $offset + 2
        $claimId = if ($csvData.FirstHeaderHasBom) {
            ""
        }
        else {
            Get-RowField $row "claim_id"
        }
        $itemId = Get-RowField $row "item_id"
        $gapId = Get-RowField $row "gap_id"
        $sourceLocation = Get-RowField $row "source_location"

        if ($claimId.StartsWith($GenericItemPrefix, [System.StringComparison]::Ordinal)) {
            $errors += (
                "behavior-claim-ledger.csv row $rowNumber uses generic CLM-* " +
                "claim_id; use BCL-* for behavior claims"
            )
        }
        if ($itemId.StartsWith($GenericItemPrefix, [System.StringComparison]::Ordinal)) {
            $errors += (
                "behavior-claim-ledger.csv row $rowNumber uses generic CLM-* " +
                "item_id; use CAND-* or TBD-* as appropriate"
            )
        }
        if ($gapId.StartsWith($GenericItemPrefix, [System.StringComparison]::Ordinal)) {
            $errors += (
                "behavior-claim-ledger.csv row $rowNumber uses generic CLM-* " +
                "gap_id; use TBD-* for gaps/questions"
            )
        }

        $confidence = Get-RowField $row "confidence"
        if ($confidence -ceq "Gap" -or $confidence -ceq "Not Reviewed") {
            if ([string]::IsNullOrEmpty($gapId)) {
                $errors += "behavior-claim-ledger.csv row $rowNumber gap row missing gap_id"
            }
            if ([string]::IsNullOrEmpty((Get-RowField $row "next_action"))) {
                $errors += "behavior-claim-ledger.csv row $rowNumber gap row missing next_action"
            }
            continue
        }

        $missing = @()
        foreach ($field in @(
            "business_meaning", "trigger_condition", "system_behavior",
            "source_id", "source_location", "evidence_id"
        )) {
            if ([string]::IsNullOrEmpty((Get-RowField $row $field))) {
                $missing += $field
            }
        }
        if ($missing.Count -gt 0) {
            $errors += (
                "behavior-claim-ledger.csv row $rowNumber non-gap claim missing: " +
                ($missing -join ", ")
            )
            continue
        }

        if (@("", "<section/page/chunk>", "unknown", "n/a", "N/A") -ccontains
            $sourceLocation) {
            $errors += (
                "behavior-claim-ledger.csv row $rowNumber non-gap claim lacks " +
                "a concrete source_location"
            )
        }

        $combined = @(
            Get-RowField $row "business_meaning"
            Get-RowField $row "trigger_condition"
            Get-RowField $row "system_behavior"
        ) -join " "
        $combined = $combined.ToLowerInvariant()
        $weakHits = @()
        foreach ($phrase in $WeakStandalonePhrases) {
            if (Test-ContainsOrdinal $combined $phrase) {
                $weakHits += $phrase
            }
        }
        if ($weakHits.Count -gt 0 -and
            [string]::IsNullOrEmpty((Get-RowField $row "next_action"))) {
            $errors += (
                "behavior-claim-ledger.csv row $rowNumber weak evidence wording " +
                "without next_action: $($weakHits -join ', ')"
            )
        }
        $substantiveRows += $row
    }

    if ($substantiveRows.Count -eq 0) {
        $errors += (
            "behavior-claim-ledger.csv has no non-gap behavior claims; keep status " +
            "blocked/ready_with_warnings and route retrieval, SME review, or code analysis"
        )
    }

    $reportPath = Join-Path $Package "functional-discovery-report.md"
    if (Test-Path -LiteralPath $reportPath -PathType Leaf) {
        $reportText = Read-Utf8Text $reportPath
        if (Test-ContainsOrdinal $reportText $GenericItemPrefix) {
            $errors += (
                "functional-discovery-report.md uses generic CLM-* IDs; " +
                "use BCL-* for behavior claims, CAND-* for functions, and TBD-* for gaps"
            )
        }
        $expectedGapHeader = (
            "| Gap ID | Area | Missing / Unclear Evidence | Impact | " +
            "Owner / Route | Next Action | Status |"
        )
        if (-not (Test-ContainsOrdinal $reportText $expectedGapHeader)) {
            $errors += (
                "functional-discovery-report.md Gap Analysis missing the " +
                "required actionable gap table header"
            )
        }
    }
    return @($errors)
}

try {
    $options = Get-CommandLineOptions @($args)
    if ($options.Help) {
        Show-Usage
        exit 0
    }

    $package = [string]$options.Package
    if (-not (Test-Path -LiteralPath $package -PathType Container)) {
        [Console]::Error.WriteLine("ERROR: package path is not a directory: $package")
        exit 2
    }

    $errors = @()
    $required = Test-RequiredFiles $package
    $errors += @($required.Errors)
    $warnings = @($required.Warnings)
    $errors += @(Test-YamlMarkers $package)
    $errors += @(Test-Report $package)
    $errors += @(Test-CsvHeader $package "traceability-matrix.csv" $TraceabilityHeader)
    $errors += @(
        Test-CsvHeader $package "behavior-claim-ledger.csv" $BehaviorClaimHeader
    )
    $errors += @(Test-Placeholders $package ([bool]$options.AllowPlaceholders))
    $errors += @(Test-ReadyStatus $package ([bool]$options.RequireReady))
    if ($options.QualityGate) {
        $errors += @(Test-QualityGate $package)
    }

    foreach ($warning in $warnings) {
        [Console]::Out.WriteLine("OK: $warning")
    }
    foreach ($finding in $errors) {
        [Console]::Error.WriteLine("ERROR: $finding")
    }
    if ($errors.Count -gt 0) {
        [Console]::Error.WriteLine("FAILED: $($errors.Count) issue(s)")
        exit 1
    }
    [Console]::Out.WriteLine("PASS: current-state discovery package structure is valid")
    exit 0
}
catch {
    [Console]::Error.WriteLine("ERROR: $($_.Exception.Message)")
    exit 2
}
