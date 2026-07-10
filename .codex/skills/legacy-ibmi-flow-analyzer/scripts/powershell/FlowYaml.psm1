<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Small YAML reader/writer for the deterministic flow-review profiles and
manifests. It deliberately supports the portable YAML subset emitted here:
indent-based mappings/lists, quoted or plain scalars, nulls, booleans, numbers,
and empty []/{} values. It has no third-party module dependency.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

function Remove-FlowYamlComment {
    param([AllowEmptyString()][string]$Line)
    $single = $false
    $double = $false
    for ($index = 0; $index -lt $Line.Length; $index++) {
        $char = $Line[$index]
        if ($char -eq "'" -and -not $double) {
            if ($single -and $index + 1 -lt $Line.Length -and $Line[$index + 1] -eq "'") {
                $index++
                continue
            }
            $single = -not $single
        }
        elseif ($char -eq '"' -and -not $single) {
            $escaped = $index -gt 0 -and $Line[$index - 1] -eq '\'
            if (-not $escaped) { $double = -not $double }
        }
        elseif ($char -eq '#' -and -not $single -and -not $double) {
            if ($index -eq 0 -or [char]::IsWhiteSpace($Line[$index - 1])) {
                return $Line.Substring(0, $index).TrimEnd()
            }
        }
    }
    return $Line.TrimEnd()
}

function Split-FlowYamlKeyValue {
    param([Parameter(Mandatory = $true)][string]$Text)
    $single = $false
    $double = $false
    for ($index = 0; $index -lt $Text.Length; $index++) {
        $char = $Text[$index]
        if ($char -eq "'" -and -not $double) {
            if ($single -and $index + 1 -lt $Text.Length -and $Text[$index + 1] -eq "'") {
                $index++
                continue
            }
            $single = -not $single
        }
        elseif ($char -eq '"' -and -not $single) {
            $escaped = $index -gt 0 -and $Text[$index - 1] -eq '\'
            if (-not $escaped) { $double = -not $double }
        }
        elseif ($char -eq ':' -and -not $single -and -not $double) {
            return @($Text.Substring(0, $index).Trim(), $Text.Substring($index + 1).Trim())
        }
    }
    throw "Invalid YAML mapping line: $Text"
}

function ConvertFrom-FlowYamlScalar {
    param([AllowEmptyString()][string]$Value)
    $text = $Value.Trim()
    if ($text -eq '' -or $text -eq '~' -or $text -eq 'null') { return $null }
    if ($text -eq '{}') { return [ordered]@{} }
    if ($text -eq '[]') { return @() }
    if ($text -match '^''(.*)''$') { return $Matches[1].Replace("''", "'") }
    if ($text -match '^"(.*)"$') {
        $inner = $Matches[1]
        return [System.Text.RegularExpressions.Regex]::Unescape($inner)
    }
    if ($text -eq 'true') { return $true }
    if ($text -eq 'false') { return $false }
    $integer = 0L
    if ([long]::TryParse($text, [ref]$integer)) { return $integer }
    $number = 0.0
    if ([double]::TryParse($text, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) {
        return $number
    }
    return $text
}

function Get-FlowYamlLines {
    param([Parameter(Mandatory = $true)][string]$Text)
    $records = New-Object System.Collections.Generic.List[object]
    foreach ($raw in ($Text -split "`r?`n")) {
        $line = Remove-FlowYamlComment $raw
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith('---')) { continue }
        if ($line.Contains("`t")) { throw 'YAML indentation may not contain tabs' }
        $indent = $line.Length - $line.TrimStart(' ').Length
        $records.Add([pscustomobject]@{ Indent = $indent; Text = $line.TrimStart(' ') })
    }
    return $records.ToArray()
}

function Read-FlowYamlBlock {
    param(
        [Parameter(Mandatory = $true)][object[]]$Lines,
        [Parameter(Mandatory = $true)][ref]$Index,
        [Parameter(Mandatory = $true)][int]$Indent
    )
    if ($Index.Value -ge $Lines.Count) { return $null }
    $isList = ([string]$Lines[$Index.Value].Text) -match '^-(?:\s|$)'
    if ($isList) {
        $items = New-Object System.Collections.Generic.List[object]
        while ($Index.Value -lt $Lines.Count) {
            $line = $Lines[$Index.Value]
            if ($line.Indent -lt $Indent) { break }
            if ($line.Indent -ne $Indent -or ([string]$line.Text) -notmatch '^-(?:\s|$)') { break }
            $remainder = ([string]$line.Text).Substring(1).Trim()
            $Index.Value++
            if ($remainder -eq '') {
                if ($Index.Value -lt $Lines.Count -and $Lines[$Index.Value].Indent -gt $Indent) {
                    $items.Add((Read-FlowYamlBlock -Lines $Lines -Index $Index -Indent $Lines[$Index.Value].Indent))
                }
                else { $items.Add($null) }
                continue
            }
            if ($remainder -match '^[^:]+:') {
                $item = [ordered]@{}
                $pair = Split-FlowYamlKeyValue $remainder
                $key = [string](ConvertFrom-FlowYamlScalar $pair[0])
                if ($pair[1] -ne '') { $item[$key] = ConvertFrom-FlowYamlScalar $pair[1] }
                elseif ($Index.Value -lt $Lines.Count -and $Lines[$Index.Value].Indent -gt $Indent) {
                    $item[$key] = Read-FlowYamlBlock -Lines $Lines -Index $Index -Indent $Lines[$Index.Value].Indent
                }
                else { $item[$key] = $null }
                while ($Index.Value -lt $Lines.Count -and $Lines[$Index.Value].Indent -gt $Indent) {
                    $childIndent = $Lines[$Index.Value].Indent
                    $childText = [string]$Lines[$Index.Value].Text
                    if ($childText -match '^-(?:\s|$)') { break }
                    $childPair = Split-FlowYamlKeyValue $childText
                    $Index.Value++
                    $childKey = [string](ConvertFrom-FlowYamlScalar $childPair[0])
                    if ($childPair[1] -ne '') { $item[$childKey] = ConvertFrom-FlowYamlScalar $childPair[1] }
                    elseif ($Index.Value -lt $Lines.Count -and $Lines[$Index.Value].Indent -gt $childIndent) {
                        $item[$childKey] = Read-FlowYamlBlock -Lines $Lines -Index $Index -Indent $Lines[$Index.Value].Indent
                    }
                    else { $item[$childKey] = $null }
                }
                $items.Add($item)
            }
            else { $items.Add((ConvertFrom-FlowYamlScalar $remainder)) }
        }
        return @($items.ToArray())
    }

    $mapping = [ordered]@{}
    while ($Index.Value -lt $Lines.Count) {
        $line = $Lines[$Index.Value]
        if ($line.Indent -lt $Indent) { break }
        if ($line.Indent -ne $Indent) { throw "Unexpected YAML indentation near: $($line.Text)" }
        if (([string]$line.Text) -match '^-(?:\s|$)') { break }
        $pair = Split-FlowYamlKeyValue ([string]$line.Text)
        $Index.Value++
        $key = [string](ConvertFrom-FlowYamlScalar $pair[0])
        if ($pair[1] -ne '') { $mapping[$key] = ConvertFrom-FlowYamlScalar $pair[1] }
        elseif (
            $Index.Value -lt $Lines.Count -and (
                $Lines[$Index.Value].Indent -gt $Indent -or
                ($Lines[$Index.Value].Indent -eq $Indent -and ([string]$Lines[$Index.Value].Text) -match '^-(?:\s|$)')
            )
        ) {
            # PyYAML emits "indentless" sequences immediately below a mapping
            # key (for example programs:\n- input_name: ...). Accept that
            # portable form as well as conventionally indented lists.
            $mapping[$key] = Read-FlowYamlBlock -Lines $Lines -Index $Index -Indent $Lines[$Index.Value].Indent
        }
        else { $mapping[$key] = $null }
    }
    return $mapping
}

function Read-FlowYamlFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "YAML file not found: $Path" }
    $lines = @(Get-FlowYamlLines ([System.IO.File]::ReadAllText($Path)))
    if ($lines.Count -eq 0) { return $null }
    $index = 0
    $value = Read-FlowYamlBlock -Lines $lines -Index ([ref]$index) -Indent $lines[0].Indent
    if ($index -ne $lines.Count) {
        throw "Unexpected trailing YAML content near: $($lines[$index].Text)"
    }
    return $value
}

function Test-FlowYamlMapping {
    param($Value)
    return $Value -is [System.Collections.IDictionary] -or $Value -is [pscustomobject]
}

function Get-FlowYamlEntries {
    param($Value)
    if ($Value -is [System.Collections.IDictionary]) {
        foreach ($key in $Value.Keys) { [pscustomobject]@{ Key = [string]$key; Value = $Value[$key] } }
        return
    }
    foreach ($property in $Value.PSObject.Properties) {
        [pscustomobject]@{ Key = $property.Name; Value = $property.Value }
    }
}

function ConvertTo-FlowYamlScalar {
    param($Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { return $(if ($Value) { 'true' } else { 'false' }) }
    if ($Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or $Value -is [int64] -or $Value -is [decimal] -or $Value -is [double]) {
        return [Convert]::ToString($Value, [Globalization.CultureInfo]::InvariantCulture)
    }
    $text = [string]$Value
    return "'" + $text.Replace("'", "''") + "'"
}

function ConvertTo-FlowYamlLines {
    param($Value, [int]$Indent = 0)
    $pad = ' ' * $Indent
    $lines = New-Object System.Collections.Generic.List[string]
    if (Test-FlowYamlMapping $Value) {
        $entries = @(Get-FlowYamlEntries $Value)
        if ($entries.Count -eq 0) { $lines.Add("${pad}{}") }
        foreach ($entry in $entries) {
            $key = if ($entry.Key -match '^[A-Za-z0-9_.-]+$') { $entry.Key } else { ConvertTo-FlowYamlScalar $entry.Key }
            $child = $entry.Value
            if (Test-FlowYamlMapping $child) {
                if (@(Get-FlowYamlEntries $child).Count -eq 0) { $lines.Add("${pad}${key}: {}") }
                else {
                    $lines.Add("${pad}${key}:")
                    foreach ($childLine in @(ConvertTo-FlowYamlLines $child ($Indent + 2))) { $lines.Add($childLine) }
                }
            }
            elseif ($child -is [System.Collections.IEnumerable] -and $child -isnot [string]) {
                $children = @($child)
                if ($children.Count -eq 0) { $lines.Add("${pad}${key}: []") }
                else {
                    $lines.Add("${pad}${key}:")
                    foreach ($item in $children) {
                        if (Test-FlowYamlMapping $item -or ($item -is [System.Collections.IEnumerable] -and $item -isnot [string])) {
                            $lines.Add((' ' * ($Indent + 2)) + '-')
                            foreach ($childLine in @(ConvertTo-FlowYamlLines $item ($Indent + 4))) { $lines.Add($childLine) }
                        }
                        else { $lines.Add((' ' * ($Indent + 2)) + '- ' + (ConvertTo-FlowYamlScalar $item)) }
                    }
                }
            }
            else { $lines.Add("${pad}${key}: $(ConvertTo-FlowYamlScalar $child)") }
        }
    }
    elseif ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        foreach ($item in @($Value)) { $lines.Add("${pad}- $(ConvertTo-FlowYamlScalar $item)") }
    }
    else { $lines.Add("${pad}$(ConvertTo-FlowYamlScalar $Value)") }
    return $lines.ToArray()
}

function ConvertTo-FlowYamlText {
    param([Parameter(Mandatory = $true)]$Value)
    return (@(ConvertTo-FlowYamlLines $Value) -join "`n") + "`n"
}

Export-ModuleMember -Function Read-FlowYamlFile, ConvertTo-FlowYamlText
