<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang
Original author: Leo L Zhang
License: Apache License 2.0

Native RPG/RPGLE/SQLRPGLE deterministic source analysis.
#>

Set-StrictMode -Version 2.0
function Analyze-Source {
    param([string[]]$Lines, [string]$Program, [string]$SourcePath)
    $statements = @(Build-Statements $Lines)
    $routines = [ordered]@{}
    $routines.MAIN = New-Routine 'MAIN' 'mainline' 1 $Lines.Count
    $routines.MAIN.called_by.Add('external program entry')
    $calls = New-ObjectList
    $fileOperations = New-ObjectList
    $declaredFiles = [ordered]@{}
    $messages = New-ObjectList
    $assignments = New-ObjectList
    $declarations = New-ObjectList
    $lineToRoutine = @{}
    $recentReads = @{}
    $readBranch = @{}
    $screenBoundary = @{}
    $errorRoutines = @{}
    $outcomeRoutines = @{}
    $assignmentBuffer = New-ObjectList
    $active = 'MAIN'
    $firstRoutineLine = 0

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $lineNumber = $i + 1
        $raw = $Lines[$i]
        $line = Get-NormalizedLine $raw
        if (-not $line) { continue }

        $start = Get-RoutineStart $line
        if ($null -ne $start) {
            if ($active -ne 'MAIN') { $routines[$active].end_line = $lineNumber - 1 }
            elseif ($firstRoutineLine -eq 0) { $firstRoutineLine = $lineNumber; $routines.MAIN.end_line = [Math]::Max(1, $lineNumber - 1) }
            $active = $start.Name
            $routines[$active] = New-Routine $active $start.Type $lineNumber $lineNumber
        }
        $lineToRoutine[[string]$lineNumber] = $active

        if ($active -ne 'MAIN' -and (Test-RoutineEnd $line $active)) {
            $routines[$active].end_line = $lineNumber
            $activeForLine = $active
            $active = 'MAIN'
        } else { $activeForLine = $active }
        if (Test-FixedCComment $line) { continue }

        foreach ($declPattern in @(
            ,@('DCL-PI', '\bDCL-PI\b\s*([A-Z0-9_#$@*]+)?')
            ,@('DCL-PR', '\bDCL-PR\b\s+([A-Z0-9_#$@*]+)')
            ,@('DCL-DS', '\bDCL-DS\b\s+([A-Z0-9_#$@*]+)')
            ,@('DCL-S', '\bDCL-S\b\s+([A-Z0-9_#$@*]+)')
        )) {
            $match = [regex]::Match($line, $declPattern[1], 'IgnoreCase')
            if ($match.Success) {
                $declarations.Add([ordered]@{ kind = $declPattern[0]; name = $(if ($match.Groups.Count -gt 1 -and $match.Groups[1].Value) { $match.Groups[1].Value.ToUpperInvariant() } else { '*N' }); line = $lineNumber; evidence = "source line $lineNumber" })
            }
        }

        $dclFile = [regex]::Match($line, '\bDCL-F\s+([A-Z0-9_#$@]+)', 'IgnoreCase')
        $fixedFile = Get-FixedFileName $line
        if ($dclFile.Success -or $fixedFile) {
            $fileName = if ($dclFile.Success) { $dclFile.Groups[1].Value.ToUpperInvariant() } else { $fixedFile }
            $declaredFiles[$fileName] = [ordered]@{ name = $fileName; declared_at = $lineNumber; source = $(if ($dclFile.Success) { 'DCL-F' } else { 'F-spec' }) }
        }

        if ($line -match '\b(EVAL|MOVE|MOVEL|Z-ADD|ADD|SUB|MULT|DIV|CLEAR|CAT)\b') {
            $item = [ordered]@{ line = $lineNumber; routine = $activeForLine; target = 'pending deep read'; expression = 'legacy opcode assignment'; assignment_type = 'fixed_or_opcode_assignment'; text = (Get-SourceText $raw).Trim(); evidence = "source line $lineNumber" }
            $assignments.Add($item); $assignmentBuffer.Add($item)
            if ($line -match '(STS|STAT|STATUS|RESP|RSP|RC|RET|RETURN|MSG|ERR|ERROR|CODE|AUTH|APPR|DECL|DENY|REJ|CARD|ACCT|CUST|AMT|AMOUNT)') { $outcomeRoutines[$activeForLine] = $true }
        }
        $freeAssign = [regex]::Match($line, '^\s*([A-Z0-9_#$@.]+)\s*=\s*(?!=)(.+)$', 'IgnoreCase')
        if ($freeAssign.Success -and $freeAssign.Groups[1].Value -notin @('IF', 'WHEN', 'DOW', 'DOU', 'FOR', 'ELSEIF', 'RETURN', 'MONITOR', 'ON-ERROR')) {
            $target = $freeAssign.Groups[1].Value.ToUpperInvariant()
            $item = [ordered]@{ line = $lineNumber; routine = $activeForLine; target = $target; expression = $freeAssign.Groups[2].Value.Trim(); assignment_type = 'free_format_assignment'; text = (Get-SourceText $raw).Trim(); evidence = "source line $lineNumber" }
            $assignments.Add($item); $assignmentBuffer.Add($item)
            if ($target -match '(STS|STAT|STATUS|RESP|RSP|RC|RET|RETURN|MSG|ERR|ERROR|CODE|AUTH|APPR|DECL|DENY|REJ|CARD|ACCT|CUST|AMT|AMOUNT)') { $outcomeRoutines[$activeForLine] = $true }
        }
        while ($assignmentBuffer.Count -gt 12) { $assignmentBuffer.RemoveAt(0) }

        foreach ($callSpec in @(
            ,@('internal_subroutine', '\bEXSR\b\s+([A-Z0-9_#$@]+)')
            ,@('external_program', '\bCALLPRC\b\s+[''\"]?([A-Z0-9_#$@]+)')
            ,@('external_program', '\bCALLP\b\s+[''\"]?([A-Z0-9_#$@]+)')
            ,@('external_program', '\bCALL\b\s+[''\"]?([A-Z0-9_#$@]+)')
        )) {
            foreach ($match in [regex]::Matches($line, $callSpec[1], 'IgnoreCase')) {
                $calls.Add([ordered]@{ caller = $activeForLine; target = $match.Groups[1].Value.ToUpperInvariant(); call_type = $callSpec[0]; line = $lineNumber; evidence = "source line $lineNumber" })
            }
        }
        $procCall = [regex]::Match($line, '^\s*([A-Z][A-Z0-9_#$@]*)\s*\((.*)\)\s*$', 'IgnoreCase')
        if ($procCall.Success -and $procCall.Groups[1].Value -notin @('IF', 'WHEN', 'DOW', 'DOU', 'FOR', 'SELECT', 'RETURN', 'EVAL')) {
            $calls.Add([ordered]@{ caller = $activeForLine; target = $procCall.Groups[1].Value.ToUpperInvariant(); call_type = 'procedure_call'; line = $lineNumber; evidence = "source line $lineNumber" })
        }

        foreach ($match in [regex]::Matches($line, '\b(CHAIN|SETLL|READE|READPE|READP|READ|WRITE|UPDATE|DELETE|EXFMT|OPEN|CLOSE|COMMIT|ROLLBACK)\b\s*([A-Z0-9_#$@]+)?', 'IgnoreCase')) {
            $operation = $match.Groups[1].Value.ToUpperInvariant()
            $object = $match.Groups[2].Value.ToUpperInvariant()
            if ($operation -eq 'OPEN' -and -not $object) { continue }
            if (-not $object) { $object = 'unresolved' }
            $recent = @()
            if ($operation -in @('WRITE', 'UPDATE', 'DELETE')) { $recent = @($assignmentBuffer.ToArray() | Select-Object -Last 8) }
            $fileOperations.Add([ordered]@{ routine = $activeForLine; operation = $operation; object = $object; line = $lineNumber; state_impact = (Get-OperationImpact $operation); recent_assignments = $recent; evidence = "source line $lineNumber" })
            if ($operation -in @('CHAIN', 'SETLL', 'READE', 'READPE', 'READP', 'READ')) { $recentReads[$activeForLine] = $lineNumber }
            if ($operation -eq 'EXFMT') { $screenBoundary[$activeForLine] = $true }
        }
        if ($recentReads.ContainsKey($activeForLine) -and ($lineNumber - $recentReads[$activeForLine]) -le 8 -and $line -match '\b(IF|WHEN|DOW|DOU|SELECT|ELSEIF)\b|%FOUND|%EOF|%EQUAL') {
            $readBranch[$activeForLine] = $true
        }
        foreach ($match in [regex]::Matches($line, '\b(CPF|CPD|MCH|RNX|SQL|UCC|LCC)[A-Z0-9]{3,8}\b', 'IgnoreCase')) {
            $messages.Add([ordered]@{ routine = $activeForLine; code = $match.Value.ToUpperInvariant(); line = $lineNumber; source_text = (Get-SourceText $raw).Trim(); evidence = "source line $lineNumber" })
        }
        foreach ($match in [regex]::Matches($line, '\b(SQLCODE|SQLSTATE)\b', 'IgnoreCase')) {
            $messages.Add([ordered]@{ routine = $activeForLine; code = $match.Value.ToUpperInvariant(); line = $lineNumber; source_text = (Get-SourceText $raw).Trim(); evidence = "source line $lineNumber" })
        }
        if ($line -match '\b(MONMSG|MONITOR|ON-ERROR|%ERROR|SNDPGMMSG|SNDMSG)\b') {
            $routines[$activeForLine].error_handling = 'message/error path observed'; $errorRoutines[$activeForLine] = $true
        }
    }

    if ($active -ne 'MAIN') { $routines[$active].end_line = $Lines.Count }
    $externalCalls = New-ObjectList
    foreach ($call in $calls) {
        Add-UniqueString $routines[$call.caller].calls_out $call.target
        if ($routines.Contains($call.target)) {
            Add-UniqueString $routines[$call.target].called_by ('{0} line {1}' -f $call.caller, $call.line)
            if ($call.call_type -ne 'internal_subroutine') { $call.call_type = 'internal_procedure' }
        } else { $externalCalls.Add($call) }
    }
    foreach ($operation in $fileOperations) {
        Add-UniqueString $routines[$operation.routine].data_touches ($operation.operation + ' ' + $operation.object)
        if ($routines[$operation.routine].state_impact -eq 'unknown' -or $operation.state_impact -ne 'read-only') { $routines[$operation.routine].state_impact = $operation.state_impact }
    }
    $entryTargets = @{}
    foreach ($call in $calls) { if ($call.caller -eq 'MAIN' -and $routines.Contains($call.target) -and $call.target -ne 'MAIN') { $entryTargets[$call.target] = $true } }
    foreach ($routine in $routines.Values) {
        if ($routine.name -eq 'MAIN') { $routine.recommended_deep_read = $true; $routine.deep_read_reasons.Add('entry path') }
        if ($entryTargets.ContainsKey($routine.name)) { $routine.recommended_deep_read = $true; $routine.deep_read_reasons.Add('mainline dispatch target') }
        if (@($fileOperations | Where-Object { $_.routine -eq $routine.name -and $_.operation -in @('WRITE', 'UPDATE', 'DELETE', 'COMMIT', 'ROLLBACK') }).Count -gt 0) { $routine.recommended_deep_read = $true; Add-UniqueString $routine.deep_read_reasons 'state-changing file operation' }
        if ($readBranch.ContainsKey($routine.name)) { $routine.recommended_deep_read = $true; Add-UniqueString $routine.deep_read_reasons 'read-conditioned branch' }
        if ($screenBoundary.ContainsKey($routine.name)) { $routine.recommended_deep_read = $true; Add-UniqueString $routine.deep_read_reasons 'screen/report boundary' }
        if (@($externalCalls | Where-Object { $_.caller -eq $routine.name }).Count -gt 0) { $routine.recommended_deep_read = $true; Add-UniqueString $routine.deep_read_reasons 'external call boundary' }
        if ($errorRoutines.ContainsKey($routine.name) -or @($messages | Where-Object { $_.routine -eq $routine.name }).Count -gt 0) { $routine.recommended_deep_read = $true; Add-UniqueString $routine.deep_read_reasons 'message/status handling'; $routine.error_handling = 'message/error path observed' }
        if ($outcomeRoutines.ContainsKey($routine.name)) { $routine.recommended_deep_read = $true; Add-UniqueString $routine.deep_read_reasons 'outcome/status carrier assignment' }
        if ($routine.name -ne 'MAIN' -and $routine.called_by.Count -eq 0) { $routine.called_by.Add('not observed in source index') }
    }

    $sqlInventory = Get-SqlInventory $statements $lineToRoutine $Program
    foreach ($sql in $sqlInventory.details) {
        if ($routines.Contains($sql.routine)) {
            $routines[$sql.routine].recommended_deep_read = $true; Add-UniqueString $routines[$sql.routine].deep_read_reasons 'sql data access'
            if ($sql.mutation) { $routines[$sql.routine].state_impact = 'updates' }
        }
    }

    $messageDetails = New-ObjectList
    foreach ($group in @($messages | Group-Object code)) {
        $occurrences = @($group.Group); $routineNames = New-StringList
        foreach ($occurrence in $occurrences) { Add-UniqueString $routineNames $occurrence.routine }
        $number = $messageDetails.Count + 1
        $messageDetails.Add([ordered]@{
            detail_id = 'MSG-{0}-{1:D3}' -f $Program, $number
            message = $group.Name
            short_description = 'unresolved - message description not available'
            description_source = 'missing_message_catalog_or_reference_pack'
            description_required = $true
            description_tbd = 'TBD-{0}-MSG-{1:D3}: provide message file/catalog/reference pack or SME-approved text for {2}' -f $Program, $number, $group.Name
            occurrence_count = $occurrences.Count
            routines = $routineNames
            first_seen = 'source line ' + $occurrences[0].line
            emitted_or_set_by = 'source token observed; semantic trigger pending deep read'
            trigger_or_handler = 'pending deep read'
            carrier_or_destination = 'pending deep read'
            related_validation_or_exception = 'pending program-analysis trace'
            evidence_status = 'unresolved_description'
            occurrences = $occurrences
        })
    }
    $messageSummary = New-ObjectList
    foreach ($detail in $messageDetails) {
        $messageSummary.Add([ordered]@{ message = $detail.message; short_description = $detail.short_description; description_source = $detail.description_source; description_required = $detail.description_required; description_tbd = $detail.description_tbd; occurrence_count = $detail.occurrence_count; routines = $detail.routines; first_seen = $detail.first_seen; detail_ref = $detail.detail_id; evidence_status = $detail.evidence_status })
    }

    $fileDetails = New-ObjectList
    foreach ($operation in $fileOperations) {
        $fileDetails.Add([ordered]@{ detail_id = 'FIO-{0}-{1:D3}' -f $Program, ($fileDetails.Count + 1); routine = $operation.routine; operation = $operation.operation; object = $operation.object; line = $operation.line; state_impact = $operation.state_impact; recent_assignments = $operation.recent_assignments; evidence = $operation.evidence })
    }
    $fileSummary = New-ObjectList
    foreach ($group in @($fileDetails | Group-Object object)) {
        $items = @($group.Group); $ops = New-StringList; $rs = New-StringList; $impacts = New-StringList
        foreach ($item in $items) { Add-UniqueString $ops $item.operation; Add-UniqueString $rs $item.routine; Add-UniqueString $impacts $item.state_impact }
        $fileSummary.Add([ordered]@{ summary_id = 'FIOSUM-{0}-{1:D3}' -f $Program, ($fileSummary.Count + 1); object = $group.Name; operations = $ops; routines = $rs; occurrence_count = $items.Count; state_impact_summary = $impacts; detail_refs = @($items | ForEach-Object { $_.detail_id }) })
    }

    $mutationDetails = New-ObjectList
    foreach ($operation in $fileOperations) {
        if ($operation.operation -notin @('WRITE', 'UPDATE', 'DELETE')) { continue }
        $mutationDetails.Add([ordered]@{ detail_id = 'MUT-{0}-{1:D3}' -f $Program, ($mutationDetails.Count + 1); mutation_source = 'native_file_operation'; routine = $operation.routine; operation = $operation.operation; object = $operation.object; source_lines = [string]$operation.line; recent_assignments = $operation.recent_assignments; host_variables = @(); commit_or_rollback = 'pending deep read'; evidence = $operation.evidence })
    }
    foreach ($sql in $sqlInventory.details) {
        if (-not $sql.mutation) { continue }
        $mutationDetails.Add([ordered]@{ detail_id = 'MUT-{0}-{1:D3}' -f $Program, ($mutationDetails.Count + 1); mutation_source = 'embedded_sql'; routine = $sql.routine; operation = 'SQL ' + $sql.statement_type; object = $sql.table_or_view; source_lines = $sql.source_lines; recent_assignments = @(); host_variables = $sql.host_variables; commit_or_rollback = 'pending deep read'; evidence = $sql.evidence })
    }
    $mutationSummary = New-ObjectList
    foreach ($group in @($mutationDetails | Group-Object { $_.object + '|' + $_.operation })) {
        $items = @($group.Group); $rs = New-StringList; foreach ($item in $items) { Add-UniqueString $rs $item.routine }
        $mutationSummary.Add([ordered]@{ summary_id = 'MUTSUM-{0}-{1:D3}' -f $Program, ($mutationSummary.Count + 1); object = $items[0].object; operation = $items[0].operation; occurrence_count = $items.Count; routines = $rs; detail_refs = @($items | ForEach-Object { $_.detail_id }) })
    }

    $deepWindows = New-ObjectList
    foreach ($routine in $routines.Values) {
        if (-not $routine.recommended_deep_read) { continue }
        $deepWindows.Add([ordered]@{ window_id = 'DRW-{0}-{1:D3}' -f $Program, ($deepWindows.Count + 1); routine = $routine.name; source_lines = '{0}-{1}' -f $routine.start_line, $routine.end_line; why_selected = $routine.deep_read_reasons.ToArray() -join '; '; coverage_outcome = 'selected_for_deep_read'; evidence = 'source-index' })
    }

    $objects = New-StringList
    foreach ($name in $declaredFiles.Keys) { Add-UniqueString $objects $name }
    foreach ($operation in $fileOperations) { if ($operation.object -ne 'unresolved') { Add-UniqueString $objects $operation.object } }
    $counts = [ordered]@{
        line_count = $Lines.Count
        routines = $routines.Count
        external_calls = $externalCalls.Count
        object_dependencies = $objects.Count
        file_operations = $fileOperations.Count
        file_io_objects = $fileSummary.Count
        field_mutations = $mutationDetails.Count
        sql_statements = $sqlInventory.details.Count
        free_format_assignments = @($assignments | Where-Object { $_.assignment_type -eq 'free_format_assignment' }).Count
        messages = $messages.Count
        unique_messages = $messageSummary.Count
        recommended_deep_read_windows = $deepWindows.Count
    }
    $tier = Get-ProgramTier $counts
    $analysisMode = 'standard'; $modeReason = 'source is below large-program thresholds'
    if ($tier[0] -eq 'large_extreme_program') { $analysisMode = 'large_program'; $modeReason = $tier[1] }
    elseif ($tier[0] -eq 'complex_normal_program' -and ($Lines.Count -gt 3000 -or $routines.Count -gt 10 -or $externalCalls.Count -gt 8 -or $objects.Count -gt 10)) { $analysisMode = 'segmented'; $modeReason = 'medium-size or dense source benefits from structure-first analysis' }

    $routineDetails = New-ObjectList
    $routineSummary = New-ObjectList
    foreach ($routine in $routines.Values) {
        $number = $routineDetails.Count + 1
        $role = 'indexed utility'
        if ($routine.name -eq 'MAIN') { $role = 'entry dispatch' }
        elseif ($routine.deep_read_reasons.Contains('state-changing file operation')) { $role = 'state-changing routine' }
        elseif ($routine.deep_read_reasons.Contains('external call boundary')) { $role = 'external boundary' }
        elseif ($routine.deep_read_reasons.Contains('message/status handling') -or $routine.deep_read_reasons.Contains('outcome/status carrier assignment')) { $role = 'validation/message routine' }
        elseif ($routine.deep_read_reasons.Contains('read-conditioned branch')) { $role = 'read-conditioned branch' }
        elseif ($routine.recommended_deep_read) { $role = 'deep-read candidate' }
        $detail = [ordered]@{ detail_id = 'RLOG-{0}-{1:D3}' -f $Program, $number; routine = $routine.name; role = $role; source_lines = '{0}-{1}' -f $routine.start_line, $routine.end_line; called_by = $routine.called_by; calls_out = $routine.calls_out; data_touches = $routine.data_touches; state_impact = $routine.state_impact; error_handling = $routine.error_handling; coverage = $routine.coverage; deep_read_recommended = $routine.recommended_deep_read; deep_read_reasons = $routine.deep_read_reasons; semantic_status = 'pending_deep_read'; execution_trigger = 'pending deep read'; step_by_step_logic = @(); field_calculations = @(); conditioned_calculation_blocks = @(); outcome_reverse_traces = @(); field_lineage = @(); branch_outcomes = @(); routine_exception_closure = @(); unresolved_routine_logic = 'pending deep read' }
        $routineDetails.Add($detail)
        $routineSummary.Add([ordered]@{ routine = $detail.routine; role = $detail.role; source_lines = $detail.source_lines; coverage = $detail.coverage; deep_read_recommended = $detail.deep_read_recommended; deep_read_reasons = $detail.deep_read_reasons; state_impact = $detail.state_impact; detail_ref = $detail.detail_id; semantic_status = $detail.semantic_status })
    }

    $sourceSuffix = [System.IO.Path]::GetExtension($SourcePath).TrimStart('.').ToUpperInvariant()
    $fullText = ($Lines -join "`n").ToUpperInvariant()
    $hasSql = $sqlInventory.details.Count -gt 0
    $hasFree = $fullText.Contains('**FREE') -or $fullText.Contains('/FREE') -or $declarations.Count -gt 0
    $hasFixed = @($Lines | Where-Object { (Get-FixedCSpecTokens (Get-NormalizedLine $_)).Count -gt 0 }).Count -gt 0
    $programType = if ($sourceSuffix -eq 'SQLRPGLE' -or $hasSql) { 'SQLRPGLE' } elseif ($sourceSuffix -in @('RPGLE', 'RPG') -or $hasFree) { 'RPGLE' } elseif ($sourceSuffix) { $sourceSuffix } else { 'unknown' }
    $syntax = if ($hasFree -and $hasFixed) { 'mixed' } elseif ($hasFree) { 'free_format' } elseif ($hasFixed) { 'fixed_format' } else { 'unknown' }
    $interface = if ($fullText -match '\b(REQUEST|RESPONSE|JSON|XML|HTTP|REST|IWS|API)\b') { 'api_remote' } elseif (@($declarations | Where-Object { $_.kind -eq 'DCL-PI' }).Count -gt 0) { 'callable_program' } elseif ($fullText -match '\b(SBMJOB|JOB)\b') { 'batch_worker' } else { 'unknown' }

    $index = [ordered]@{
        schema_version = '0.1'
        generated_by = 'index-rpg-source.ps1'
        program = $Program
        source = [ordered]@{ path = $SourcePath; line_count = $Lines.Count }
        analysis_mode = $analysisMode
        mode_reason = $modeReason
        program_size_tier = $tier[0]
        tier_reason = $tier[1]
        default_output_profile = $tier[2]
        counts = [ordered]@{ routines = $counts.routines; external_calls = $counts.external_calls; object_dependencies = $counts.object_dependencies; file_operations = $counts.file_operations; file_io_objects = $counts.file_io_objects; field_mutations = $counts.field_mutations; sql_statements = $counts.sql_statements; free_format_assignments = $counts.free_format_assignments; messages = $counts.messages; unique_messages = $counts.unique_messages; recommended_deep_read_windows = $counts.recommended_deep_read_windows }
        program_profile = [ordered]@{ program_type = $programType; syntax_mode = $syntax; interface_profile = $interface; source_suffix = $(if ($sourceSuffix) { $sourceSuffix } else { 'unknown' }); has_embedded_sql = $hasSql; declaration_count = $declarations.Count; statement_count = $statements.Count }
        statements = $statements
        declarations = $declarations
        assignments = $assignments
        declared_files = @($declaredFiles.Values)
        routines = @($routines.Values)
        calls = $calls
        external_calls = $externalCalls
        file_operations = $fileOperations
        file_io_inventory = [ordered]@{ summary = $fileSummary; details = $fileDetails; sidecar_markdown = 'file-io-inventory.md'; sidecar_yaml = 'file-io-inventory.yaml' }
        field_mutation_inventory = [ordered]@{ summary = $mutationSummary; details = $mutationDetails; sidecar_markdown = 'field-mutation-matrix.md'; sidecar_yaml = 'field-mutation-matrix.yaml' }
        sql_inventory = $sqlInventory
        messages = $messages
        message_inventory = [ordered]@{ summary = $messageSummary; details = $messageDetails; sidecar_markdown = 'message-inventory.md'; sidecar_yaml = 'message-inventory.yaml' }
        deep_read_windows = $deepWindows
        contract_note = 'This structure index is pre-analysis evidence. It is not a business summary and does not make downstream-ready claims.'
    }
    $isFull = $tier[0] -eq 'large_extreme_program'
    $isComplex = $tier[0] -eq 'complex_normal_program'
    $hasStateChangingIo = @($fileOperations | Where-Object { $_.operation -in @('WRITE', 'UPDATE', 'DELETE', 'COMMIT', 'ROLLBACK') }).Count -gt 0
    $index['optional_sidecar_triggers'] = [ordered]@{
        deep_read_plan = [ordered]@{ write = ($isFull -or $isComplex -or $deepWindows.Count -gt 5); reason = $(if ($isFull -or $isComplex -or $deepWindows.Count -gt 5) { 'large/complex tier or more than one five-routine batch' } else { 'not needed for concise normal review' }) }
        coverage_ledger = [ordered]@{ write = ($isFull -or $isComplex -or $deepWindows.Count -gt 5); reason = $(if ($isFull -or $isComplex -or $deepWindows.Count -gt 5) { 'large/complex tier or batched routine coverage required' } else { 'not needed for concise normal review' }) }
        file_io_inventory = [ordered]@{ write = ($isFull -or $fileOperations.Count -gt 10 -or $hasStateChangingIo); reason = $(if ($fileOperations.Count -gt 10 -or $hasStateChangingIo) { 'dense or state-changing file I/O observed' } else { 'file I/O can remain summarized in program-analysis.md' }) }
        field_mutation_matrix = [ordered]@{ write = ($isFull -or $mutationDetails.Count -gt 0); reason = $(if ($mutationDetails.Count -gt 0) { 'persisted native or SQL mutation evidence observed' } else { 'no persisted mutation detail observed' }) }
        sql_inventory = [ordered]@{ write = ($isFull -or $sqlInventory.details.Count -gt 0); reason = $(if ($sqlInventory.details.Count -gt 0) { 'embedded SQL / SQLRPGLE evidence observed' } else { 'no embedded SQL observed' }) }
        message_inventory_markdown = [ordered]@{ write = ($isFull -or $messageSummary.Count -gt 10); reason = $(if ($messageSummary.Count -gt 10) { 'message inventory is dense' } else { 'message-inventory.yaml is enough for concise reader-first review' }) }
    }
    $index['routine_logic_inventory'] = [ordered]@{
        summary = $routineSummary
        details = $routineDetails
        sidecar_markdown = 'routine-logic-details.md'
        sidecar_yaml = 'routine-logic-details.yaml'
        sharding_guidance = [ordered]@{
            main_document_limit = 'for routines > 25, keep program-analysis.md table-led but include continuous ordered RLOG headings and reader-useful detail for every YAML RLOG'
            batch_files_required_when = 'program_size_tier is large_extreme_program; canonical seed files use routine-logic-details/deep-read-batch-001.md and continue in five-window batches'
            final_consolidation_required = 'Batch files are retained audit surfaces; merge them into the reader-first program-analysis.md and consolidated routine-logic-details.md audit document.'
        }
    }
    return $index
}
