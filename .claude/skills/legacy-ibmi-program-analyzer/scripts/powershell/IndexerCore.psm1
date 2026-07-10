<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang
Original author: Leo L Zhang
License: Apache License 2.0

Shared Windows PowerShell 5.1 parsing, YAML, Markdown, tier, and lookup helpers.
#>

Set-StrictMode -Version 2.0
function Parse-CliArguments {
    param([object[]]$Values)

    if ($Values.Count -lt 1) {
        throw 'usage: index-rpg-source.ps1 SOURCE [--program NAME] [--out-dir DIR] [--delivery-root DIR] [--delivery-profile FILE] [--force-rescan] [--rescan-reason TEXT]'
    }

    $result = [ordered]@{
        Source = [string]$Values[0]
        Program = $null
        OutDir = '.'
        DeliveryRoot = $null
        DeliveryProfile = $null
        ForceRescan = $false
        RescanReason = $null
    }
    $valueOptions = @{
        '--program' = 'Program'
        '--out-dir' = 'OutDir'
        '--delivery-root' = 'DeliveryRoot'
        '--delivery-profile' = 'DeliveryProfile'
        '--rescan-reason' = 'RescanReason'
    }
    $index = 1
    while ($index -lt $Values.Count) {
        $token = [string]$Values[$index]
        if ($token -eq '--force-rescan') {
            $result.ForceRescan = $true
            $index++
            continue
        }
        if ($valueOptions.ContainsKey($token)) {
            if (($index + 1) -ge $Values.Count) {
                throw "missing value for $token"
            }
            $result[$valueOptions[$token]] = [string]$Values[$index + 1]
            $index += 2
            continue
        }
        throw "unrecognized argument: $token"
    }
    return $result
}

function New-StringList {
    return ,(New-Object 'System.Collections.Generic.List[string]')
}

function New-ObjectList {
    return ,(New-Object 'System.Collections.Generic.List[object]')
}

function Add-UniqueString {
    param(
        [System.Collections.Generic.List[string]]$List,
        [string]$Value
    )
    if ($Value -and -not $List.Contains($Value)) {
        $List.Add($Value)
    }
}

function Get-SourceText {
    param([string]$RawLine)
    if ($RawLine.Length -gt 6 -and $RawLine.Substring(0, 6).Trim() -match '^\d+$') {
        return $RawLine.Substring(6)
    }
    return $RawLine
}

function Get-NormalizedLine {
    param([string]$RawLine)
    return (Get-SourceText $RawLine).Trim().TrimEnd(';').ToUpperInvariant()
}

function Test-RpgComment {
    param([string]$RawLine)
    $text = (Get-SourceText $RawLine).TrimStart()
    $upper = $text.ToUpperInvariant()
    return (
        -not $text -or
        $text.StartsWith('//') -or
        $text.StartsWith('*') -or
        $upper.StartsWith('C*') -or
        $upper.StartsWith('/*') -or
        $upper.StartsWith('*/')
    )
}

function Get-FixedCSpecTokens {
    param([string]$Line)
    $match = [regex]::Match(
        $Line,
        '^(?:(?:\S+\s+)?C(?!\*)|(?!EXEC\b)[A-Z0-9_#$@]+C(?!\*))\s+(.*)$',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) { return @() }
    return @($match.Groups[1].Value -split '\s+' | Where-Object { $_ })
}

function Test-FixedCComment {
    param([string]$Line)
    return [regex]::IsMatch($Line, '^(?:(?:\S+\s+)?C|[A-Z0-9_#$@]+C)\*', 'IgnoreCase')
}

function Get-FixedRoutineName {
    param([string]$Line, [string]$Opcode)
    $tokens = @(Get-FixedCSpecTokens $Line)
    for ($i = 1; $i -lt $tokens.Count; $i++) {
        if ($tokens[$i].ToUpperInvariant() -eq $Opcode) {
            $candidate = $tokens[$i - 1].ToUpperInvariant()
            if ($candidate -match '^SR[A-Z0-9_#$@]*$') { return $candidate }
        }
    }
    return $null
}

function Get-RoutineStart {
    param([string]$Line)
    $proc = [regex]::Match($Line, '\bDCL-PROC\s+([A-Z0-9_#$@]+)', 'IgnoreCase')
    if ($proc.Success) {
        return [ordered]@{ Name = $proc.Groups[1].Value.ToUpperInvariant(); Type = 'procedure' }
    }
    $fixed = Get-FixedRoutineName $Line 'BEGSR'
    if ($fixed) { return [ordered]@{ Name = $fixed; Type = 'subroutine' } }
    if ((Get-FixedCSpecTokens $Line).Count -gt 0 -or (Test-FixedCComment $Line)) { return $null }
    $free = [regex]::Match($Line, '\bBEGSR\b\s+([A-Z0-9_#$@*]+)', 'IgnoreCase')
    if ($free.Success) {
        return [ordered]@{ Name = $free.Groups[1].Value.ToUpperInvariant(); Type = 'subroutine' }
    }
    return $null
}

function Test-RoutineEnd {
    param([string]$Line, [string]$ActiveName)
    if ($Line -match '\bEND-PROC\b') { return $true }
    $fixed = Get-FixedRoutineName $Line 'ENDSR'
    if ($fixed) { return ($fixed -eq $ActiveName -or $fixed -eq ($ActiveName + 'E')) }
    if ((Get-FixedCSpecTokens $Line).Count -gt 0 -or (Test-FixedCComment $Line)) { return $false }
    return ($Line -match '\bENDSR\b')
}

function Get-FixedFileName {
    param([string]$Line)
    if ((Get-FixedCSpecTokens $Line).Count -gt 0 -or (Test-FixedCComment $Line)) { return $null }
    $match = [regex]::Match($Line, '^F([A-Z0-9_#$@]{1,10})\s+', 'IgnoreCase')
    if (-not $match.Success -or ($Line -split '\s+').Count -lt 3) { return $null }
    if (($Line -split '\s+')[0] -in @('FOR', 'FROM')) { return $null }
    return $match.Groups[1].Value.ToUpperInvariant()
}

function Get-OperationImpact {
    param([string]$Operation)
    switch ($Operation) {
        'WRITE' { return 'creates' }
        'UPDATE' { return 'updates' }
        'DELETE' { return 'deletes' }
        'COMMIT' { return 'transaction boundary' }
        'ROLLBACK' { return 'transaction boundary' }
        'EXFMT' { return 'screen/report boundary' }
        { $_ -in @('CHAIN', 'SETLL', 'READE', 'READPE', 'READP', 'READ', 'OPEN', 'CLOSE') } { return 'read-only' }
        default { return 'unknown' }
    }
}

function New-Routine {
    param([string]$Name, [string]$Type, [int]$StartLine, [int]$EndLine)
    return [ordered]@{
        name = $Name
        type = $Type
        start_line = $StartLine
        end_line = $EndLine
        called_by = New-StringList
        calls_out = New-StringList
        data_touches = New-StringList
        state_impact = 'unknown'
        error_handling = 'none observed'
        coverage = 'indexed_only'
        recommended_deep_read = $false
        deep_read_reasons = New-StringList
    }
}

function Build-Statements {
    param([string[]]$Lines)
    $result = New-ObjectList
    $parts = New-StringList
    $start = 0
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if (Test-RpgComment $Lines[$i]) { continue }
        $text = (Get-SourceText $Lines[$i]).Trim()
        if (-not $text) { continue }
        if ($start -eq 0) { $start = $i + 1 }
        $clean = ($text -split '//', 2)[0].Trim()
        if ($clean) { $parts.Add($clean.TrimEnd(';')) }
        if ($text.Contains(';')) {
            $joined = (($parts.ToArray() -join ' ') -replace '\s+', ' ').Trim().ToUpperInvariant()
            if ($joined) {
                $result.Add([ordered]@{
                    start_line = $start
                    end_line = $i + 1
                    text = $joined
                    source_text = $parts.ToArray() -join ' '
                })
            }
            $parts.Clear()
            $start = 0
        }
    }
    if ($parts.Count -gt 0) {
        $result.Add([ordered]@{
            start_line = $start
            end_line = $Lines.Count
            text = (($parts.ToArray() -join ' ') -replace '\s+', ' ').Trim().ToUpperInvariant()
            source_text = $parts.ToArray() -join ' '
        })
    }
    return $result.ToArray()
}

function Get-SqlInventory {
    param([object[]]$Statements, [hashtable]$LineToRoutine, [string]$Program)
    $details = New-ObjectList
    foreach ($statement in $Statements) {
        if ($statement.text -notmatch '\bEXEC\s+SQL\b') { continue }
        $sql = ($statement.text -replace '^.*?\bEXEC\s+SQL\s+', '').Trim()
        $typeMatch = [regex]::Match($sql, '^(SELECT|INSERT|UPDATE|DELETE|MERGE|OPEN|FETCH|CLOSE|DECLARE|SET|CALL)\b', 'IgnoreCase')
        $statementType = if ($typeMatch.Success) { $typeMatch.Groups[1].Value.ToUpperInvariant() } else { 'OTHER' }
        $object = 'unresolved'
        $objectPattern = switch ($statementType) {
            'SELECT' { '\bFROM\s+([A-Z0-9_#$@.]+)' }
            'INSERT' { '\bINTO\s+([A-Z0-9_#$@.]+)' }
            'UPDATE' { '^UPDATE\s+([A-Z0-9_#$@.]+)' }
            'DELETE' { '\bFROM\s+([A-Z0-9_#$@.]+)' }
            'MERGE' { '\bINTO\s+([A-Z0-9_#$@.]+)' }
            default { $null }
        }
        if ($objectPattern) {
            $objectMatch = [regex]::Match($sql, $objectPattern, 'IgnoreCase')
            if ($objectMatch.Success) { $object = $objectMatch.Groups[1].Value.ToUpperInvariant() }
        }
        $hostVariables = New-StringList
        foreach ($hostMatch in [regex]::Matches($sql, ':[A-Z0-9_#$@.]+', 'IgnoreCase')) {
            Add-UniqueString $hostVariables $hostMatch.Value.ToUpperInvariant()
        }
        $routine = 'MAIN'
        if ($LineToRoutine.ContainsKey([string]$statement.start_line)) {
            $routine = $LineToRoutine[[string]$statement.start_line]
        }
        $details.Add([ordered]@{
            detail_id = ('SQL-{0}-{1:D3}' -f $Program, ($details.Count + 1))
            routine = $routine
            statement_type = $statementType
            table_or_view = $object
            source_lines = if ($statement.start_line -eq $statement.end_line) { [string]$statement.start_line } else { '{0}-{1}' -f $statement.start_line, $statement.end_line }
            host_variables = $hostVariables
            mutation = ($statementType -in @('INSERT', 'UPDATE', 'DELETE', 'MERGE'))
            evidence = 'source lines {0}-{1}' -f $statement.start_line, $statement.end_line
        })
    }
    $summary = New-ObjectList
    $groups = @($details.ToArray() | Group-Object { $_.table_or_view + '|' + $_.statement_type })
    foreach ($group in $groups) {
        $items = @($group.Group)
        $routines = New-StringList
        $variables = New-StringList
        foreach ($item in $items) {
            Add-UniqueString $routines $item.routine
            foreach ($variable in $item.host_variables) { Add-UniqueString $variables $variable }
        }
        $summary.Add([ordered]@{
            summary_id = ('SQLSUM-{0}-{1:D3}' -f $Program, ($summary.Count + 1))
            table_or_view = $items[0].table_or_view
            statement_type = $items[0].statement_type
            occurrence_count = $items.Count
            routines = $routines
            host_variables = $variables
            detail_refs = @($items | ForEach-Object { $_.detail_id })
        })
    }
    return [ordered]@{
        summary = $summary
        details = $details
        sidecar_markdown = 'sql-inventory.md'
        sidecar_yaml = 'sql-inventory.yaml'
    }
}

function Get-ProgramTier {
    param([System.Collections.IDictionary]$Counts)
    if ($Counts.line_count -gt 10000) { return @('large_extreme_program', 'source length exceeds 10,000 lines', 'full_index_and_batched_deep_read') }
    if ($Counts.routines -gt 25) { return @('large_extreme_program', 'routine count exceeds 25', 'full_index_and_batched_deep_read') }
    if ($Counts.external_calls -gt 20) { return @('large_extreme_program', 'external call count exceeds 20', 'full_index_and_batched_deep_read') }
    if ($Counts.object_dependencies -gt 25) { return @('large_extreme_program', 'object dependency count exceeds 25', 'full_index_and_batched_deep_read') }

    $reasons = New-StringList
    if ($Counts.line_count -gt 3000) { $reasons.Add('source length exceeds normal-program comfort threshold') }
    if ($Counts.routines -gt 10) { $reasons.Add('routine count exceeds normal-program comfort threshold') }
    if ($Counts.external_calls -gt 8) { $reasons.Add('external call count exceeds normal-program comfort threshold') }
    if ($Counts.object_dependencies -gt 10) { $reasons.Add('object dependency count exceeds normal-program comfort threshold') }
    if ($Counts.file_operations -gt 20) { $reasons.Add('file I/O operation count is dense') }
    if ($Counts.field_mutations -gt 20) { $reasons.Add('field mutation count is dense') }
    if ($Counts.sql_statements -gt 10) { $reasons.Add('embedded SQL statement count is dense') }
    if ($Counts.unique_messages -gt 10) { $reasons.Add('message/status inventory is dense') }
    if ($Counts.recommended_deep_read_windows -gt 5) { $reasons.Add('recommended deep-read windows exceed one five-routine batch') }
    if ($reasons.Count -gt 0) {
        return @('complex_normal_program', ($reasons.ToArray() -join '; '), 'reader_first_plus_triggered_sidecars')
    }
    return @('normal_program', 'normal-size program; default to concise reader-first SME review', 'reader_first_lightweight_review')
}

function Get-YamlScalar {
    param($Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { if ($Value) { return 'true' } else { return 'false' } }
    if ($Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or $Value -is [int64] -or $Value -is [decimal] -or $Value -is [double]) {
        return [string]$Value
    }
    $text = [string]$Value
    if ($text.Length -eq 0) { return '""' }
    if ($text -match '^[A-Za-z0-9_./:@#$%+][A-Za-z0-9_./:@#$%+*-]*$' -and $text.ToLowerInvariant() -notin @('true', 'false', 'null')) {
        return $text
    }
    return '"' + $text.Replace('\', '\\').Replace('"', '\"').Replace("`r", '').Replace("`n", '\n') + '"'
}

function ConvertTo-YamlLines {
    param($Value, [int]$Indent = 0)
    $lines = New-StringList
    $pad = ' ' * $Indent
    if ($Value -is [System.Collections.IDictionary]) {
        foreach ($key in $Value.Keys) {
            $item = $Value[$key]
            $isMap = $item -is [System.Collections.IDictionary]
            $isList = ($item -is [System.Collections.IEnumerable] -and -not ($item -is [string]) -and -not $isMap)
            if ($isMap -or $isList) {
                $items = @($item)
                if ($item -is [System.Collections.IDictionary]) { $items = @($item.Keys) }
                if ($items.Count -eq 0) {
                    $empty = if ($isMap) { '{}' } else { '[]' }
                    $lines.Add("$pad$key`: $empty")
                } else {
                    $lines.Add("$pad$key`:")
                    foreach ($child in @(ConvertTo-YamlLines $item ($Indent + 2))) { $lines.Add($child) }
                }
            } else {
                $lines.Add("$pad$key`: $(Get-YamlScalar $item)")
            }
        }
    } elseif ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        foreach ($item in $Value) {
            $isComplex = ($item -is [System.Collections.IDictionary]) -or ($item -is [System.Collections.IEnumerable] -and -not ($item -is [string]))
            if ($isComplex) {
                $lines.Add("$pad-")
                foreach ($child in @(ConvertTo-YamlLines $item ($Indent + 2))) { $lines.Add($child) }
            } else {
                $lines.Add("$pad- $(Get-YamlScalar $item)")
            }
        }
    } else {
        $lines.Add("$pad$(Get-YamlScalar $Value)")
    }
    return $lines.ToArray()
}

function ConvertTo-YamlText {
    param($Value)
    return (@(ConvertTo-YamlLines $Value 0) -join "`n") + "`n"
}

function ConvertTo-TableCell {
    param($Value)
    if ($null -eq $Value) { return '-' }
    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        $items = @($Value)
        $text = if ($items.Count -eq 0) { '-' } else { $items -join ', ' }
    } else {
        $text = [string]$Value
        if (-not $text) { $text = '-' }
    }
    return $text.Replace('|', '\|').Replace("`r", '').Replace("`n", ' ')
}

function New-MarkdownTable {
    param([string[]]$Headers, [object[]]$Rows)
    $output = New-StringList
    $output.Add('| ' + ($Headers -join ' | ') + ' |')
    $output.Add('| ' + (@($Headers | ForEach-Object { '---' }) -join ' | ') + ' |')
    foreach ($row in $Rows) {
        $cells = @($row | ForEach-Object { ConvertTo-TableCell $_ })
        $output.Add('| ' + ($cells -join ' | ') + ' |')
    }
    return $output.ToArray() -join "`n"
}

function Write-TextFile {
    param([string]$Path, [string]$Content)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Get-SidecarDeclarations {
    param([System.Collections.IDictionary]$Index)
    $trigger = $Index.optional_sidecar_triggers
    $sidecars = [ordered]@{
        program_analysis = [ordered]@{ path = 'program-analysis.md'; status = 'present' }
        source_index = [ordered]@{ path = 'source-index.yaml'; status = 'present' }
        routine_index = [ordered]@{ path = 'routine-index.md'; status = 'present' }
        routine_logic_details = [ordered]@{ path = 'routine-logic-details.md'; status = 'present' }
        routine_logic_details_yaml = [ordered]@{ path = 'routine-logic-details.yaml'; status = 'present' }
        message_inventory_yaml = [ordered]@{ path = 'message-inventory.yaml'; status = 'present' }
        message_inventory = [ordered]@{ path = 'message-inventory.md'; status = $(if ($trigger.message_inventory_markdown.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        coverage_ledger = [ordered]@{ path = 'all-routine-coverage-ledger.md'; status = $(if ($trigger.coverage_ledger.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        deep_read_plan = [ordered]@{ path = 'deep-read-plan.md'; status = $(if ($trigger.deep_read_plan.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        file_io_inventory = [ordered]@{ path = 'file-io-inventory.md'; status = $(if ($trigger.file_io_inventory.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        file_io_inventory_yaml = [ordered]@{ path = 'file-io-inventory.yaml'; status = $(if ($trigger.file_io_inventory.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        field_mutation_matrix = [ordered]@{ path = 'field-mutation-matrix.md'; status = $(if ($trigger.field_mutation_matrix.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        field_mutation_matrix_yaml = [ordered]@{ path = 'field-mutation-matrix.yaml'; status = $(if ($trigger.field_mutation_matrix.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        sql_inventory = [ordered]@{ path = 'sql-inventory.md'; status = $(if ($trigger.sql_inventory.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
        sql_inventory_yaml = [ordered]@{ path = 'sql-inventory.yaml'; status = $(if ($trigger.sql_inventory.write) { 'optional_triggered' } else { 'not_written_by_default' }) }
    }
    if ($Index.program_size_tier -eq 'large_extreme_program') {
        $batchCount = [Math]::Max(1, [Math]::Ceiling($Index.deep_read_windows.Count / 5.0))
        for ($i = 1; $i -le $batchCount; $i++) {
            $sidecars[('routine_logic_deep_read_batch_{0:D3}' -f $i)] = [ordered]@{
                path = 'routine-logic-details/deep-read-batch-{0:D3}.md' -f $i
                status = 'present'
            }
        }
    }
    return $sidecars
}
