<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Safe program-list input handling shared by the native PowerShell preparer.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

function Test-FlowProgramListComment {
    param([AllowEmptyString()][string]$Value)
    return $Value.StartsWith('# ') -or $Value.StartsWith("#`t")
}

function Test-FlowProgramListHeader {
    param([AllowEmptyString()][string]$Value)
    $header = $Value.Trim().ToLowerInvariant().Replace('-', '_').Replace(' ', '_')
    return $header -in @('member', 'program', 'program_name', 'object_name', 'name')
}

function Assert-FlowInputNotReparsePoint {
    param([Parameter(Mandatory = $true)][string]$Path)
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if ((Test-Path -LiteralPath $current) -and (([IO.File]::GetAttributes($current) -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw "input trust path contains a symlink/junction/reparse point: $current" }
        $parent = [IO.Path]::GetDirectoryName($current)
        if (-not $parent -or $parent -eq $current) { break }
        $current = $parent
    }
}

function Read-FlowProgramsFileInput {
    param([Parameter(Mandatory = $true)][string]$Path)
    Assert-FlowInputNotReparsePoint $Path
    $programs = New-Object System.Collections.Generic.List[string]
    if ([IO.Path]::GetExtension($Path).Equals('.csv', [StringComparison]::OrdinalIgnoreCase)) {
        Add-Type -AssemblyName Microsoft.VisualBasic -ErrorAction Stop
        $parser = New-Object Microsoft.VisualBasic.FileIO.TextFieldParser -ArgumentList $Path
        $parser.TextFieldType = [Microsoft.VisualBasic.FileIO.FieldType]::Delimited
        $parser.SetDelimiters(',')
        $parser.HasFieldsEnclosedInQuotes = $true
        $firstRecord = $true
        try {
            while (-not $parser.EndOfData) {
                $fields = @($parser.ReadFields())
                $value = $(if ($fields.Count) { ([string]$fields[0]).Trim().TrimStart([char]0xFEFF) } else { '' })
                if (-not $value -or (Test-FlowProgramListComment $value)) { continue }
                if ($firstRecord -and (Test-FlowProgramListHeader $value)) { $firstRecord = $false; continue }
                $firstRecord = $false
                $programs.Add($value)
            }
        }
        catch { throw "invalid programs CSV '$Path': $($_.Exception.Message)" }
        finally { $parser.Close() }
        return $programs.ToArray()
    }
    foreach ($line in [IO.File]::ReadAllLines($Path)) {
        $value = $line.Trim().TrimStart([char]0xFEFF)
        if ($value -and -not (Test-FlowProgramListComment $value)) { $programs.Add($value) }
    }
    return $programs.ToArray()
}

function Assert-FlowProgramName {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Program)
    if ($Program -cnotmatch '\A[A-Za-z@#$][A-Za-z0-9_@#$]{0,9}\z') {
        throw "invalid normalized program name '$Program'; expected one safe 1-10 character IBM i object token starting with A-Z, a-z, @, #, or `$ and containing only letters, digits, underscore, @, #, or `$"
    }
    return $Program
}

function Normalize-FlowProgramNameInput {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Program, $LookupProfile)
    $normalized = $Program.Trim()
    $normalization = if ($LookupProfile -is [System.Collections.IDictionary] -and $LookupProfile.Contains('program_name_normalization')) { $LookupProfile['program_name_normalization'] } else { [ordered]@{} }
    $case = if ($normalization -is [System.Collections.IDictionary] -and $normalization.Contains('case')) { [string]$normalization['case'] } else { '' }
    if ($case -eq 'upper') {
        $normalized = $normalized.ToUpperInvariant()
    }
    return Assert-FlowProgramName $normalized
}

Export-ModuleMember -Function Read-FlowProgramsFileInput, Normalize-FlowProgramNameInput, Assert-FlowProgramName
