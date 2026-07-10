<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang
Original author: Leo L Zhang
License: Apache License 2.0

Native deterministic artifact renderers and writers.
#>

Set-StrictMode -Version 2.0
function Render-RoutineIndex {
    param([System.Collections.IDictionary]$Index)
    $routineRows = @($Index.routines | ForEach-Object {
        ,@($_.name, $_.type, ('{0}-{1}' -f $_.start_line, $_.end_line), $_.called_by, $_.calls_out, $_.data_touches, $_.state_impact, $_.coverage, $_.deep_read_reasons)
    })
    $callRows = @($Index.calls | ForEach-Object { ,@($_.caller, $_.target, $_.call_type, $_.line, $_.evidence) })
    $fileRows = @($Index.file_operations | ForEach-Object { ,@($_.routine, $_.operation, $_.object, $_.line, $_.state_impact, $_.evidence) })
    $messageRows = @($Index.messages | ForEach-Object { ,@($_.routine, $_.code, $_.line, $_.evidence) })
    return @(
        '# Routine Index: ' + $Index.program
        '## Source Size & Strategy'
        (New-MarkdownTable @('Program', 'Source Lines', 'Analysis Mode', 'Mode Reason') @(,@($Index.program, $Index.source.line_count, $Index.analysis_mode, $Index.mode_reason)))
        '## Routine Cards Seed'
        (New-MarkdownTable @('Routine', 'Type', 'Lines', 'Called By', 'Calls Out', 'Data Touches', 'State Impact', 'Coverage', 'Deep Read Reason') $routineRows)
        '## Call Evidence Seed'
        (New-MarkdownTable @('Caller', 'Callee', 'Call Type', 'Line', 'Evidence') $callRows)
        '## File Operation Seed'
        (New-MarkdownTable @('Routine', 'Operation', 'Object', 'Line', 'State Impact', 'Evidence') $fileRows)
        '## Message / Status Seed'
        (New-MarkdownTable @('Routine', 'Code', 'Line', 'Evidence') $messageRows)
    ) -join "`n`n"
}

function Render-RoutineLogicDetails {
    param([System.Collections.IDictionary]$Index)
    $summaryRows = @($Index.routine_logic_inventory.summary | ForEach-Object {
        ,@($_.routine, $_.role, $_.source_lines, $_.coverage, $(if ($_.deep_read_recommended) { 'yes' } else { 'no' }), $_.state_impact, $_.detail_ref, $_.semantic_status)
    })
    $parts = New-StringList
    $parts.Add('# Routine Logic Details: ' + $Index.program)
    $parts.Add('This sidecar preserves audit/checkpoint routine detail behind the reader-first `program-analysis.md`. Semantic logic remains `pending_deep_read` until source windows are analyzed.')
    $parts.Add('## Calculation Logic')
    $parts.Add('Pending semantic deep-read. This consolidated section must be populated before final delivery.')
    $parts.Add('## Validation Logic')
    $parts.Add('Pending semantic deep-read and message/reference-pack lookup.')
    $parts.Add('## Exception Handling')
    $parts.Add('Pending semantic deep-read.')
    $parts.Add('## Message Inventory')
    $parts.Add('See `message-inventory.yaml` for the deterministic message/status seed.')
    $parts.Add('## Routine Detail Index')
    $parts.Add((New-MarkdownTable @('Routine', 'Role', 'Source Lines', 'Coverage', 'Deep Read', 'State Impact', 'Detail ID', 'Semantic Status') $summaryRows))
    $parts.Add('## Routine Details')
    foreach ($detail in $Index.routine_logic_inventory.details) {
        $parts.Add('### {0} - {1}' -f $detail.detail_id, $detail.routine)
        $parts.Add((New-MarkdownTable @('Field', 'Value') @(
            ,@('Role', $detail.role)
            ,@('Source Lines', $detail.source_lines)
            ,@('Called By', $detail.called_by)
            ,@('Calls Out', $detail.calls_out)
            ,@('Data Touches', $detail.data_touches)
            ,@('State Impact', $detail.state_impact)
            ,@('Error Handling', $detail.error_handling)
            ,@('Semantic Status', $detail.semantic_status)
        )))
        $parts.Add('Pending semantic deep-read: execution trigger, calculations, conditioned blocks, reverse traces, field lineage, branch outcomes, and exception closure.')
    }
    $parts.Add('## Sharding Guidance')
    $parts.Add('- Large/extreme programs retain `routine-logic-details/deep-read-batch-*.md` audit checkpoints.')
    $parts.Add('- Final delivery must consolidate every RLOG into reader-first `program-analysis.md` and this audit document.')
    return ($parts.ToArray() -join "`n`n") + "`n"
}

function Render-ProgramAnalysis {
    param([System.Collections.IDictionary]$Index)
    $rlogRows = @($Index.routine_logic_inventory.summary | ForEach-Object {
        ,@(($_.detail_ref + ' / ' + $_.routine), $_.role, 'pending semantic deep-read; replace with reader-useful detail during final consolidation')
    })
    $messageRows = @($Index.message_inventory.summary | ForEach-Object {
        ,@($_.message, $_.short_description, 'message/status', $_.occurrence_count, $_.routines, $_.first_seen, 'pending deep read', $_.detail_ref)
    })
    if ($messageRows.Count -eq 0) { $messageRows = @(,@('-', 'no message/status tokens observed by static index', '-', 0, '-', '-', '-', '-')) }
    $sections = New-StringList
    $sections.Add('# Program Analysis: {0} (unlinked)' -f $Index.program)
    $sections.Add('Draft wrapper seed generated by `index-rpg-source.ps1`. It fixes the required reader-first layout before semantic deep-read. Do not treat pending rows as approved behavior.')
    $sections.Add('## Program Reading Summary')
    $sections.Add('Pending semantic deep-read. Use the routine index and source ranges below to build a reader-first processing summary.')
    $sections.Add('## Calculation Logic')
    $sections.Add('### Calculation Logic Overview')
    $sections.Add('Pending semantic deep-read.')
    $sections.Add('### Indexed Calculation And Assignment Paths')
    $sections.Add('Static assignment evidence has been indexed; business meaning remains unresolved.')
    $sections.Add('### Routine Index For Calculation Logic')
    $sections.Add((New-MarkdownTable @('RLOG / Routine', 'Category', 'Reader Detail') $rlogRows))
    $sections.Add('## Validation Logic')
    $sections.Add('### Validation Logic Overview')
    $sections.Add('Pending semantic deep-read and message description lookup.')
    $sections.Add('### Indexed Status And Message Paths')
    $sections.Add((New-MarkdownTable @('Message / Status', 'Description', 'Type', 'Occurrences', 'Routine(s)', 'First Seen', 'Trigger', 'Detail') $messageRows))
    $sections.Add('### Routine Index For Validation Logic')
    $sections.Add((New-MarkdownTable @('RLOG / Routine', 'Category', 'Reader Detail') $rlogRows))
    $sections.Add('## Exception Handling')
    $sections.Add('### Exception Flow Overview')
    $sections.Add('Pending semantic deep-read.')
    $sections.Add('### Indexed Error And Handler Paths')
    $sections.Add('MONITOR, ON-ERROR, MONMSG, message-send, and status evidence is retained in the source index.')
    $sections.Add('### Routine Index For Exception Handling')
    $sections.Add((New-MarkdownTable @('RLOG / Routine', 'Category', 'Reader Detail') $rlogRows))
    $sections.Add('## Message Inventory')
    $sections.Add((New-MarkdownTable @('Message / Code / Literal', 'Short Description', 'Type', 'Occurrences', 'Primary Routine(s)', 'First Seen / Set By', 'Trigger / Handler', 'Detail') $messageRows))
    foreach ($heading in @(
        'Metadata', 'Analysis Coverage & Scope', 'Program Call Map', 'Routine Cards',
        'Routine Logic Details', 'Deep Read Windows', 'Entry Points & Parameters',
        'Object Dependencies', 'Logic Decomposition Ledger', 'Data Touch Map',
        'Key File & Field Logic', 'Control Flow', 'File I/O', 'External Calls',
        'Error Handling', 'Redundancy Candidate Notes', 'TBDs & Blocking Status',
        'Review Checklist'
    )) {
        $sections.Add('## ' + $heading)
        if ($heading -eq 'Routine Logic Details') {
            foreach ($item in $Index.routine_logic_inventory.summary) {
                $sections.Add('### {0} / {1}' -f $item.detail_ref, $item.routine)
                $sections.Add('Pending semantic deep-read. Preserve this RLOG heading and replace this placeholder with reader-useful routine detail during final consolidation.')
            }
        } elseif ($heading -eq 'Review Checklist') {
            $sections.Add('- [ ] Replace all pending seed content with source-backed semantic detail.')
            $sections.Add('- [ ] Run `validate-program-analysis-contract.py --analysis-dir <DIR>` or the native PowerShell validator.')
        } else {
            $sections.Add('Pending semantic deep-read; deterministic evidence is available in `source-index.yaml` and the declared sidecars.')
        }
    }
    return ($sections.ToArray() -join "`n`n") + "`n"
}

function Render-SimpleInventoryMarkdown {
    param([string]$Title, [object[]]$Details, [string[]]$Columns)
    $rows = @($Details | ForEach-Object {
        $row = @()
        foreach ($column in $Columns) { $row += $_[$column] }
        ,$row
    })
    return '# ' + $Title + "`n`n" + (New-MarkdownTable $Columns $rows) + "`n"
}

function Render-DeepReadPlan {
    param([System.Collections.IDictionary]$Index)
    $rows = @($Index.deep_read_windows | ForEach-Object { ,@($_.routine, $_.window_id, $_.source_lines, $_.why_selected, $_.coverage_outcome) })
    return '# Deep Read Plan: ' + $Index.program + "`n`n" + (New-MarkdownTable @('Routine', 'Window', 'Source Lines', 'Reason', 'Coverage') $rows) + "`n"
}

function Render-CoverageLedger {
    param([System.Collections.IDictionary]$Index)
    $rows = @($Index.routine_logic_inventory.summary | ForEach-Object { ,@($_.routine, $_.source_lines, $_.coverage, $_.deep_read_recommended, $_.deep_read_reasons, $_.detail_ref) })
    return '# All-Routine Coverage Ledger: ' + $Index.program + "`n`n" + (New-MarkdownTable @('Routine', 'Lines', 'Coverage', 'Deep Read', 'Reason', 'RLOG') $rows) + "`n"
}

function Render-BatchCheckpoint {
    param([System.Collections.IDictionary]$Index, [int]$BatchNumber, [object[]]$Windows)
    $rows = @($Windows | ForEach-Object { ,@($_.window_id, $_.routine, $_.source_lines, $_.why_selected) })
    return @(
        '# Routine Logic Details: {0} - Deep Read Batch {1:D3}' -f $Index.program, $BatchNumber
        'Batch seed generated by `index-rpg-source.ps1`. Keep this file as an audit checkpoint and merge completed detail into the reader-first `program-analysis.md` and consolidated `routine-logic-details.md` audit document.'
        '## Calculation Logic'
        'Pending semantic deep-read; core logic must not contain pasted source-code snippets.'
        '## Validation Logic'
        'Pending semantic deep-read; must list every exact message/status/literal for this batch.'
        '## Exception Handling'
        'Pending semantic deep-read.'
        '## Scope'
        'This batch covers at most five routine/window seeds.'
        '## Batch Coverage Summary'
        (New-MarkdownTable @('Window ID', 'Routine', 'Source Lines', 'Why Selected') $rows)
        '## Message Inventory'
        'Populate one row per exact observed message/status/literal.'
        '## Routine Details'
        'Populate reader-useful detail for every YAML RLOG in this batch.'
    ) -join "`n`n"
}

function Get-YamlIndent {
    param([string]$Line)
    return $Line.Length - $Line.TrimStart().Length
}

function Get-DeliveryLookupProfile {
    param([string]$ProfilePath)
    $result = [ordered]@{
        ProgramFolderPatterns = @('modules/*/{PROGRAM}')
        ProgramNameCase = 'upper'
    }
    if (-not $ProfilePath) { return $result }
    if (-not (Test-Path -LiteralPath $ProfilePath -PathType Leaf)) { throw "delivery profile not found: $ProfilePath" }

    $lines = [System.IO.File]::ReadAllLines((Resolve-Path -LiteralPath $ProfilePath).Path)
    $sectionStart = -1
    $sectionIndent = -1
    for ($index = 0; $index -lt $lines.Count; $index++) {
        if ($lines[$index] -match '^\s*delivery_artifact_lookup_profile\s*:') {
            $sectionStart = $index + 1
            $sectionIndent = Get-YamlIndent $lines[$index]
            break
        }
    }
    $scopeStart = if ($sectionStart -ge 0) { $sectionStart } else { 0 }
    $scopeEnd = $lines.Count
    if ($sectionStart -ge 0) {
        for ($index = $scopeStart; $index -lt $lines.Count; $index++) {
            $trimmed = $lines[$index].Trim()
            if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
            if ((Get-YamlIndent $lines[$index]) -le $sectionIndent) {
                $scopeEnd = $index
                break
            }
        }
    }

    $patterns = New-StringList
    $patternIndent = -1
    $normalizationIndent = -1
    for ($index = $scopeStart; $index -lt $scopeEnd; $index++) {
        $line = $lines[$index]
        $indent = Get-YamlIndent $line
        if ($line -match '^\s*program_folder_patterns\s*:') {
            $patternIndent = $indent
            continue
        }
        if ($patternIndent -ge 0) {
            if ($line -match '^\s*-\s*["'']?([^"''#]+?)["'']?\s*(?:#.*)?$' -and $indent -gt $patternIndent) {
                $patterns.Add($Matches[1].Trim())
                continue
            }
            if ($line.Trim() -and -not $line.TrimStart().StartsWith('#') -and $indent -le $patternIndent) {
                $patternIndent = -1
            }
        }
        if ($line -match '^\s*program_name_normalization\s*:') {
            $normalizationIndent = $indent
            continue
        }
        if ($normalizationIndent -ge 0 -and $indent -gt $normalizationIndent -and
            $line -match '^\s*case\s*:\s*["'']?([^"''#\s]+)') {
            $result.ProgramNameCase = $Matches[1].Trim().ToLowerInvariant()
        }
    }
    if ($patterns.Count -gt 0) { $result.ProgramFolderPatterns = $patterns.ToArray() }
    return $result
}

function Find-CentralArtifacts {
    param([string]$DeliveryRoot, [string]$Program, [string]$ProfilePath)
    $matches = New-StringList
    $rootPath = (Resolve-Path -LiteralPath $DeliveryRoot).Path
    $profile = Get-DeliveryLookupProfile $ProfilePath
    $normalizedProgram = $Program.Trim()
    if ($profile.ProgramNameCase -eq 'upper') { $normalizedProgram = $normalizedProgram.ToUpperInvariant() }
    foreach ($pattern in @($profile.ProgramFolderPatterns)) {
        $relative = $pattern.Replace('{PROGRAM}', $normalizedProgram).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
        foreach ($path in @(Get-ChildItem -Path (Join-Path $rootPath $relative) -Directory -ErrorAction SilentlyContinue)) {
            $candidate = $path.FullName.Substring($rootPath.Length).TrimStart('\', '/').Replace('\', '/')
            Add-UniqueString $matches $candidate
        }
    }
    return @($matches.ToArray() | Sort-Object)
}


function Write-Artifacts {
    param([System.Collections.IDictionary]$Index, [string]$OutputDirectory)
    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    $written = New-StringList
    $sidecars = Get-SidecarDeclarations $Index
    $summary = [ordered]@{
        schema_version = '0.1'; generated_by = 'index-rpg-source.ps1'; program = $Index.program; source = $Index.source
        analysis_mode = $Index.analysis_mode; mode_reason = $Index.mode_reason; program_size_tier = $Index.program_size_tier
        tier_reason = $Index.tier_reason; default_output_profile = $Index.default_output_profile; counts = $Index.counts
        program_profile = $Index.program_profile; routine_summary = $Index.routine_logic_inventory.summary
        message_summary = $Index.message_inventory.summary; file_io_summary = $Index.file_io_inventory.summary
        field_mutation_summary = $Index.field_mutation_inventory.summary; sql_summary = $Index.sql_inventory.summary
        external_calls = $Index.external_calls; declared_files = $Index.declared_files; deep_read_windows = $Index.deep_read_windows
        optional_sidecar_triggers = $Index.optional_sidecar_triggers; sidecars = $sidecars
        contract_note = 'Flow-level analysis should prefer this compact summary and present sidecar YAML files. Before delivery, validate the main wrapper sections, declared sidecars, and RLOG coverage.'
    }
    if ($Index.Contains('central_artifact_reuse')) { $summary['central_artifact_reuse'] = $Index.central_artifact_reuse }
    $core = [ordered]@{
        'program-analysis.md' = (Render-ProgramAnalysis $Index)
        'source-index.yaml' = (ConvertTo-YamlText $Index)
        'program-analysis-summary.yaml' = (ConvertTo-YamlText $summary)
        'routine-index.md' = (Render-RoutineIndex $Index) + "`n"
        'routine-logic-details.md' = (Render-RoutineLogicDetails $Index)
        'routine-logic-details.yaml' = (ConvertTo-YamlText ([ordered]@{ schema_version = '0.1'; generated_by = 'index-rpg-source.ps1'; program = $Index.program; source = $Index.source; routine_logic_inventory = $Index.routine_logic_inventory; contract_note = 'This is a pre-analysis routine detail seed.' }))
        'message-inventory.yaml' = (ConvertTo-YamlText ([ordered]@{ schema_version = '0.1'; generated_by = 'index-rpg-source.ps1'; program = $Index.program; message_inventory = $Index.message_inventory }))
    }
    foreach ($name in $core.Keys) { $path = Join-Path $OutputDirectory $name; Write-TextFile $path $core[$name]; $written.Add($path) }
    $trigger = $Index.optional_sidecar_triggers
    if ($trigger.coverage_ledger.write) { $path = Join-Path $OutputDirectory 'all-routine-coverage-ledger.md'; Write-TextFile $path (Render-CoverageLedger $Index); $written.Add($path) }
    if ($trigger.deep_read_plan.write) { $path = Join-Path $OutputDirectory 'deep-read-plan.md'; Write-TextFile $path (Render-DeepReadPlan $Index); $written.Add($path) }
    if ($trigger.message_inventory_markdown.write) { $path = Join-Path $OutputDirectory 'message-inventory.md'; Write-TextFile $path (Render-SimpleInventoryMarkdown ('Message Inventory: ' + $Index.program) $Index.message_inventory.details @('detail_id', 'message', 'short_description', 'occurrence_count', 'routines', 'first_seen', 'evidence_status')); $written.Add($path) }
    if ($trigger.file_io_inventory.write) {
        $path = Join-Path $OutputDirectory 'file-io-inventory.md'; Write-TextFile $path (Render-SimpleInventoryMarkdown ('File I/O Inventory: ' + $Index.program) $Index.file_io_inventory.details @('detail_id', 'routine', 'operation', 'object', 'line', 'state_impact', 'evidence')); $written.Add($path)
        $path = Join-Path $OutputDirectory 'file-io-inventory.yaml'; Write-TextFile $path (ConvertTo-YamlText ([ordered]@{ schema_version = '0.1'; generated_by = 'index-rpg-source.ps1'; program = $Index.program; file_io_inventory = $Index.file_io_inventory })); $written.Add($path)
    }
    if ($trigger.field_mutation_matrix.write) {
        $path = Join-Path $OutputDirectory 'field-mutation-matrix.md'; Write-TextFile $path (Render-SimpleInventoryMarkdown ('Field Mutation Matrix: ' + $Index.program) $Index.field_mutation_inventory.details @('detail_id', 'mutation_source', 'routine', 'operation', 'object', 'source_lines', 'evidence')); $written.Add($path)
        $path = Join-Path $OutputDirectory 'field-mutation-matrix.yaml'; Write-TextFile $path (ConvertTo-YamlText ([ordered]@{ schema_version = '0.1'; generated_by = 'index-rpg-source.ps1'; program = $Index.program; field_mutation_inventory = $Index.field_mutation_inventory })); $written.Add($path)
    }
    if ($trigger.sql_inventory.write) {
        $path = Join-Path $OutputDirectory 'sql-inventory.md'; Write-TextFile $path (Render-SimpleInventoryMarkdown ('SQL Inventory: ' + $Index.program) $Index.sql_inventory.details @('detail_id', 'routine', 'statement_type', 'table_or_view', 'source_lines', 'host_variables', 'evidence')); $written.Add($path)
        $path = Join-Path $OutputDirectory 'sql-inventory.yaml'; Write-TextFile $path (ConvertTo-YamlText ([ordered]@{ schema_version = '0.1'; generated_by = 'index-rpg-source.ps1'; program = $Index.program; sql_inventory = $Index.sql_inventory })); $written.Add($path)
    }
    if ($Index.program_size_tier -eq 'large_extreme_program') {
        $windows = @($Index.deep_read_windows)
        if ($windows.Count -eq 0) { $windows = @([ordered]@{ window_id = 'DRW-' + $Index.program + '-001'; routine = 'MAIN'; source_lines = '1-' + $Index.source.line_count; why_selected = 'fallback first routine window' }) }
        $batchNumber = 1
        for ($offset = 0; $offset -lt $windows.Count; $offset += 5) {
            $last = [Math]::Min($offset + 4, $windows.Count - 1)
            $batch = @($windows[$offset..$last])
            $relative = 'routine-logic-details/deep-read-batch-{0:D3}.md' -f $batchNumber
            $path = Join-Path $OutputDirectory $relative
            Write-TextFile $path (Render-BatchCheckpoint $Index $batchNumber $batch)
            $written.Add($path); $batchNumber++
        }
    }
    return $written.ToArray()
}
