#requires -version 5.1

<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
#>

# Small, dependency-free readers used by the native PowerShell contract
# validator. The YAML reader intentionally supports the generated sidecar
# subset needed by this skill; it is not a general-purpose YAML parser.

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$RlogPattern = '\bRLOG-[A-Z0-9_#$@-]+-\d{3}\b'
$PlaceholderPatterns = @(
    '\bpending reader-oriented summary\b',
    '\bpending semantic deep-read\b',
    '\bpending semantic detail\b',
    '\bplaceholder content\b',
    '\bplaceholder\b',
    '\bnot-yet-deep-read\b',
    '\bnot deep-read\b'
)

function Read-Utf8Text {
    param([string]$Path)
    return [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8)
}

function ConvertFrom-SimpleYamlScalar {
    param([string]$Value)

    if ($null -eq $Value) { return '' }
    $clean = $Value.Trim()
    if ($clean.Length -ge 2) {
        if ($clean[0] -eq '"' -and $clean[$clean.Length - 1] -eq '"') {
            $clean = $clean.Substring(1, $clean.Length - 2)
            $clean = $clean.Replace('\"', '"').Replace('\\', '\')
        }
        elseif ($clean[0] -eq "'" -and $clean[$clean.Length - 1] -eq "'") {
            $clean = $clean.Substring(1, $clean.Length - 2).Replace("''", "'")
        }
    }
    return $clean
}

function Get-YamlLines {
    param([string]$Path)
    return @(Read-Utf8Text $Path -split "`r?`n")
}

function Get-Indent {
    param([string]$Line)
    return $Line.Length - $Line.TrimStart(' ').Length
}

function Find-YamlSection {
    param(
        [string[]]$Lines,
        [string]$Key,
        [int]$StartIndex = 0,
        [int]$EndIndex = -1
    )

    if ($EndIndex -lt 0) { $EndIndex = $Lines.Count }
    for ($index = $StartIndex; $index -lt $EndIndex; $index++) {
        if ($Lines[$index] -match ('^\s*' + [regex]::Escape($Key) + ':\s*(?:#.*)?$')) {
            $indent = Get-Indent $Lines[$index]
            $sectionEnd = $EndIndex
            for ($cursor = $index + 1; $cursor -lt $EndIndex; $cursor++) {
                $candidate = $Lines[$cursor]
                if ($candidate.Trim().Length -eq 0 -or $candidate.TrimStart().StartsWith('#')) { continue }
                if ((Get-Indent $candidate) -le $indent) {
                    $sectionEnd = $cursor
                    break
                }
            }
            return [pscustomobject]@{ Start = $index; End = $sectionEnd; Indent = $indent }
        }
    }
    return $null
}

function Get-YamlRootScalar {
    param([string[]]$Lines, [string]$Key)

    foreach ($line in $Lines) {
        if ((Get-Indent $line) -eq 0 -and $line -match ('^' + [regex]::Escape($Key) + ':\s*(.*?)\s*$')) {
            return ConvertFrom-SimpleYamlScalar $Matches[1]
        }
    }
    return ''
}

function Get-YamlNestedScalar {
    param([string[]]$Lines, [string]$ParentKey, [string]$Key)

    $parent = Find-YamlSection $Lines $ParentKey
    if ($null -eq $parent) { return '' }
    for ($index = $parent.Start + 1; $index -lt $parent.End; $index++) {
        $line = $Lines[$index]
        if ($line -match ('^\s*' + [regex]::Escape($Key) + ':\s*(.*?)\s*$')) {
            return ConvertFrom-SimpleYamlScalar $Matches[1]
        }
    }
    return ''
}

function Get-SidecarEntries {
    param([string]$SummaryPath)

    $entries = @{}
    $lines = Get-YamlLines $SummaryPath
    $sidecars = Find-YamlSection $lines 'sidecars'
    if ($null -eq $sidecars) { return $entries }
    $entryIndent = $sidecars.Indent + 2
    $currentKey = $null
    for ($index = $sidecars.Start + 1; $index -lt $sidecars.End; $index++) {
        $line = $lines[$index]
        if ($line.Trim().Length -eq 0 -or $line.TrimStart().StartsWith('#')) { continue }
        $indent = Get-Indent $line
        if ($indent -eq $entryIndent -and $line -match '^\s*([A-Za-z0-9_-]+):\s*$') {
            $currentKey = $Matches[1]
            $entries[$currentKey] = @{ path = ''; status = '' }
            continue
        }
        if ($null -ne $currentKey -and $indent -gt $entryIndent -and $line -match '^\s*(path|status):\s*(.*?)\s*$') {
            $entries[$currentKey][$Matches[1]] = ConvertFrom-SimpleYamlScalar $Matches[2]
        }
    }
    return $entries
}

function Get-YamlListMappings {
    param([string]$Path, [string]$RootKey, [string]$ListKey)

    $lines = Get-YamlLines $Path
    $root = Find-YamlSection $lines $RootKey
    if ($null -eq $root) { return @() }
    $list = Find-YamlSection $lines $ListKey ($root.Start + 1) $root.End
    if ($null -eq $list) { return @() }

    $entries = New-Object System.Collections.ArrayList
    $current = $null
    $entryIndent = $list.Indent + 2
    for ($index = $list.Start + 1; $index -lt $list.End; $index++) {
        $line = $lines[$index]
        if ($line.Trim().Length -eq 0 -or $line.TrimStart().StartsWith('#')) { continue }
        $indent = Get-Indent $line
        if ($indent -eq $entryIndent -and $line -match '^\s*-\s*(.*)$') {
            if ($null -ne $current) { [void]$entries.Add($current) }
            $current = @{}
            $inline = $Matches[1]
            if ($inline -match '^([A-Za-z0-9_-]+):\s*(.*?)\s*$') {
                $current[$Matches[1]] = ConvertFrom-SimpleYamlScalar $Matches[2]
            }
            continue
        }
        if ($null -ne $current -and $indent -gt $entryIndent -and $line -match '^\s*([A-Za-z0-9_-]+):\s*(.*?)\s*$') {
            $key = $Matches[1]
            $value = $Matches[2]
            if ($value -ne '') { $current[$key] = ConvertFrom-SimpleYamlScalar $value }
        }
    }
    if ($null -ne $current) { [void]$entries.Add($current) }
    return @($entries.ToArray())
}

function Get-RlogIdsFromYaml {
    param([string]$Path)

    $ids = New-Object System.Collections.ArrayList
    foreach ($detail in @(Get-YamlListMappings $Path 'routine_logic_inventory' 'details')) {
        if ($detail.ContainsKey('detail_id') -and [string]$detail.detail_id -ne '') {
            [void]$ids.Add(([string]$detail.detail_id).ToUpperInvariant())
        }
    }
    return @($ids.ToArray())
}

function Get-MessageEntries {
    param([string]$Path)

    $details = @(Get-YamlListMappings $Path 'message_inventory' 'details')
    if ($details.Count -gt 0) { return $details }
    return @(Get-YamlListMappings $Path 'message_inventory' 'summary')
}

function Get-HeadingMatches {
    param([string]$Markdown, [bool]$H2Only = $false)
    $pattern = if ($H2Only) { '(?m)^##\s+(.+?)\s*$' } else { '(?m)^#{2,6}\s+(.+?)\s*$' }
    return @([regex]::Matches($Markdown, $pattern))
}

function Get-HeadingMap {
    param([string]$Markdown, [bool]$H2Only = $false)

    $positions = @{}
    foreach ($match in @(Get-HeadingMatches $Markdown $H2Only)) {
        $heading = $match.Groups[1].Value.Trim()
        if (-not $positions.ContainsKey($heading)) { $positions[$heading] = $match.Index }
    }
    return $positions
}

function Get-H2SectionText {
    param([string]$Markdown, [string]$Heading)

    $matches = @(Get-HeadingMatches $Markdown $true)
    for ($index = 0; $index -lt $matches.Count; $index++) {
        if ($matches[$index].Groups[1].Value.Trim() -ne $Heading) { continue }
        $start = $matches[$index].Index + $matches[$index].Length
        $end = if ($index + 1 -lt $matches.Count) { $matches[$index + 1].Index } else { $Markdown.Length }
        return $Markdown.Substring($start, $end - $start)
    }
    return ''
}

function Get-H3Blocks {
    param([string]$SectionText)

    $matches = @([regex]::Matches($SectionText, '(?m)^###\s+(.+?)\s*$'))
    $blocks = New-Object System.Collections.ArrayList
    for ($index = 0; $index -lt $matches.Count; $index++) {
        $start = $matches[$index].Index + $matches[$index].Length
        $end = if ($index + 1 -lt $matches.Count) { $matches[$index + 1].Index } else { $SectionText.Length }
        [void]$blocks.Add([pscustomobject]@{
            Heading = $matches[$index].Groups[1].Value.Trim()
            Position = $matches[$index].Index
            Body = $SectionText.Substring($start, $end - $start)
        })
    }
    return @($blocks.ToArray())
}

function Test-ReaderFirstPlaceholder {
    param([string]$Text)
    foreach ($pattern in $PlaceholderPatterns) {
        if ([regex]::IsMatch($Text, $pattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)) { return $true }
    }
    return $false
}

function Get-MeaningfulWordCount {
    param([string]$Text)

    $cleaned = [regex]::Replace($Text, '`[^`]*`', ' ')
    $cleaned = [regex]::Replace($cleaned, $RlogPattern, ' ', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $cleaned = [regex]::Replace($cleaned, '\bSR\d{3,}\b', ' ', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    return [regex]::Matches($cleaned, '[A-Za-z0-9][A-Za-z0-9_#$@/-]*|[\u4e00-\u9fff]{2,}').Count
}

function Get-TableCellsOrLine {
    param([string]$Line)

    $stripped = $Line.Trim()
    if ($stripped -eq '') { return @() }
    if ($stripped.StartsWith('|') -and $stripped.EndsWith('|')) {
        $cells = New-Object System.Collections.ArrayList
        foreach ($cell in $stripped.Trim('|').Split('|')) {
            $value = $cell.Trim()
            if ($value -ne '' -and $value -notmatch '^:?-{3,}:?$') { [void]$cells.Add($value) }
        }
        return @($cells.ToArray())
    }
    return @($stripped)
}

function Get-MarkdownTableRows {
    param([string]$SectionText)

    $rows = New-Object System.Collections.ArrayList
    foreach ($line in ($SectionText -split "`r?`n")) {
        $stripped = $line.Trim()
        if (-not ($stripped.StartsWith('|') -and $stripped.EndsWith('|'))) { continue }
        $cells = @($stripped.Trim('|').Split('|') | ForEach-Object { $_.Trim() })
        $separator = $cells.Count -gt 0
        foreach ($cell in $cells) {
            if ($cell -notmatch '^:?-{3,}:?$') { $separator = $false; break }
        }
        if (-not $separator) {
            [void]$rows.Add([pscustomobject]@{ Cells = $cells })
        }
    }
    return @($rows.ToArray())
}

function Get-RlogIdsFromText {
    param([string]$Text)
    return @([regex]::Matches($Text, $RlogPattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase) |
        ForEach-Object { $_.Value.ToUpperInvariant() })
}

function Get-UniqueSorted {
    param([object[]]$Values)
    return @($Values | Sort-Object -Unique)
}

function Compare-StringSets {
    param([string[]]$Left, [string[]]$Right)
    return @(Get-UniqueSorted @($Left | Where-Object { $Right -notcontains $_ }))
}

function Test-SequenceEqual {
    param([object[]]$Left, [object[]]$Right)
    if ($Left.Count -ne $Right.Count) { return $false }
    for ($index = 0; $index -lt $Left.Count; $index++) {
        if ([string]$Left[$index] -ne [string]$Right[$index]) { return $false }
    }
    return $true
}

Export-ModuleMember -Function @(
    'Read-Utf8Text',
    'Get-YamlLines',
    'Get-YamlRootScalar',
    'Get-YamlNestedScalar',
    'Get-SidecarEntries',
    'Get-RlogIdsFromYaml',
    'Get-MessageEntries',
    'Get-HeadingMap',
    'Get-H2SectionText',
    'Get-H3Blocks',
    'Test-ReaderFirstPlaceholder',
    'Get-MeaningfulWordCount',
    'Get-TableCellsOrLine',
    'Get-MarkdownTableRows',
    'Get-RlogIdsFromText',
    'Get-UniqueSorted',
    'Compare-StringSets',
    'Test-SequenceEqual'
)
