<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Native PowerShell 5.1 safety gates for the reader-first Core Review.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Markdown.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'ProgramSetCoreReview.Reconciliation.psm1') -Force

$script:RelationCorePattern = 'calls?|called\s+by|invokes?|invoked\s+by|hands?\s+off(?:\s+to)?|hands?(?:\s+\S+){0,10}\s+off(?:\s+to)?|hand[- ]?off|delegates?(?:\s+\S+){0,10}\s+to|routes?(?:\s+\S+){0,10}\s+to|forwards?(?:\s+\S+){0,10}\s+to|transfers?(?:\s+\S+){0,10}\s+to|dispatch(?:es)?(?:\s+\S+){0,10}\s+to|triggers?|triggered\s+by|launches?|launched\s+by|submits?(?:\s+\S+){0,10}\s+to|passes?(?:\s+\S+){0,10}\s+to|sends?(?:\s+\S+){0,10}\s+to|returns?(?:\s+\S+){0,10}\s+to|provides?|provided\s+by|supplies?|supplied\s+by|yields?|yielded\s+by|emits?|emitted\s+by|writes?|written\s+by|starts?|started\s+by|runs?|run\s+by|queues?|queued\s+by|publishes?|published\s+by|requests?|requested\s+by|chains?|chained\s+by|precedes?|follows?|delivers?|delivered\s+by|exchanges?|communicates?|depends?\s+(?:on|upon)|maps?|mapped\s+by|populates?|populated\s+by|connects?|connected\s+(?:to|with|by)|continues?\s+(?:into|to)|feeds?|receives?(?:\s+\S+){0,10}\s+from|flows?\s+(?:to|from)|source\s+carrier\s+for|target\s+carrier\s+from|producer|consumer|produces?|produced\s+by|consumes?|consumed\s+by|received\s+by|routed\s+(?:to|by)|forwarded\s+(?:to|by)|(?:uses?|reads?)(?:\s+\S+){0,10}\s+from|then|executes?\s+(?:before|after|in\s+that\s+order)'
$script:RelationIndicatorPattern = '\b(?:' + $script:RelationCorePattern + ')\b|(?:-{1,2}>|=>|→|⇒|<-{1,2}|<=|←|⇐)'
$script:ReverseRelationPattern = '\b(?:called\s+by|invoked\s+by|triggered\s+by|launched\s+by|delegated\s+by|routed\s+by|forwarded\s+by|provided\s+by|supplied\s+by|yielded\s+by|emitted\s+by|written\s+by|started\s+by|run\s+by|queued\s+by|published\s+by|requested\s+by|requests?(?:\s+.{0,80}?)?\s+from|chained\s+by|delivered\s+by|mapped\s+by|populated\s+by|connected\s+by|receives?(?:\s+.{0,80}?)?\s+from|flows?\s+from|target\s+carrier\s+from|consumer\s+of|consumes?(?:\s+.{0,80}?)?(?:\s+(?:from|produced\s+by))?|(?:uses?|reads?)(?:\s+.{0,80}?)?\s+from|produced\s+by)\b|(?:<-{1,2}|<=|←|⇐)'
$script:NegativeRelationPattern = '\b(?:not|never|cannot|can''t|doesn''t|isn''t|aren''t|wasn''t|weren''t|no)\b'
$script:ExactTokenCorePattern = '[A-Za-z0-9_@#$%*+]'
$script:ExactTokenConnectors = './:-'
$script:SourceFactPattern = '(?<![A-Za-z0-9_@#$-])SF-[A-Za-z0-9_@#$-]+(?![A-Za-z0-9_@#$-])'
$script:ReaderFirstReviewSections = @(
    'Program Set Reading Summary', 'Cross-Program Processing Overview',
    'Calculation Logic', 'Validation Logic', 'Exception Handling',
    'Message Inventory', 'Message Coverage Control'
)

function Test-FlowRelationBridge {
    param([AllowEmptyString()][string]$Text)
    if ([regex]::IsMatch($Text, '^\s*(?:starts?|runs?|precedes?|follows?)\s*$', 'IgnoreCase')) { return $true }
    $surface = [regex]::Replace($Text, '\b(?:starts?|runs?|precedes?|follows?)\b(?!\s+by\b)', ' ', 'IgnoreCase')
    return [regex]::IsMatch($surface, $script:RelationIndicatorPattern, 'IgnoreCase')
}

function Get-SafetyMapValue {
    param($Map, [string]$Key, $Default = $null)
    if ($null -eq $Map) { return $Default }
    if ($Map -is [Collections.IDictionary]) {
        if ($Map.Contains($Key)) { return $Map[$Key] }
        return $Default
    }
    $property = $Map.PSObject.Properties[$Key]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Remove-FlowSafetyComments {
    param([AllowEmptyString()][string]$Markdown)
    return Remove-FlowHtmlComments $Markdown
}

function Get-FlowSafetyH2Block {
    param([string]$Markdown, [string]$Section)
    $pattern = '(?ms)^##\s+' + [regex]::Escape($Section) + '\s*$.*?(?=^##\s+|\z)'
    $match = [regex]::Match($Markdown, $pattern)
    if ($match.Success) { return $match.Value }
    return ''
}

function Get-FlowForbiddenHeadingFindings {
    param([string]$Markdown, [string[]]$ForbiddenNames)
    $findings = New-Object System.Collections.Generic.List[string]
    $names = @($ForbiddenNames | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $visible = ConvertTo-FlowUnquotedMarkdownSurface (Remove-FlowSafetyComments $Markdown)
    $candidates = New-Object System.Collections.Generic.List[string]
    foreach ($match in @([regex]::Matches($visible, '(?m)^[ ]{0,3}#{1,6}\s+(.+?)\s*#*\s*$'))) { $candidates.Add($match.Groups[1].Value) }
    foreach ($match in @([regex]::Matches($visible, '(?m)^[ ]{0,3}([^\n|]+?)\s*\n[ ]{0,3}(?:=+|-+)\s*$'))) { $candidates.Add($match.Groups[1].Value) }
    foreach ($match in @([regex]::Matches($visible, '(?is)<h[1-6]\b[^>]*>(.*?)</h[1-6]\s*>'))) { $candidates.Add($match.Groups[1].Value) }
    foreach ($candidate in @($candidates.ToArray())) {
        $name = ConvertTo-FlowRenderedHeadingLabel $candidate
        $name = [regex]::Replace($name, '^\s*\d{1,9}[.)]\s*', '')
        foreach ($forbidden in $names) {
            if (-not $name.StartsWith($forbidden, [StringComparison]::OrdinalIgnoreCase)) { continue }
            $suffix = $name.Substring($forbidden.Length)
            if (-not $suffix -or [regex]::IsMatch($suffix, '^\s*(?:[:;,.!?/()\[\]{}—–-]|[\p{So}\p{Sk}\p{Cs}])')) {
                $findings.Add("program-set review contains forbidden full-flow section: $forbidden")
                break
            }
        }
    }
    return @($findings.ToArray())
}

function ConvertTo-FlowUnquotedMarkdownSurface {
    param([AllowEmptyString()][string]$Markdown)
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($rawLine in @($Markdown -split "`r?`n")) {
        $line = $rawLine
        while ($true) {
            $match = [regex]::Match($line, '^[ ]{0,3}(?:>\s?|[-+*]\s+|\d{1,9}[.)]\s+)')
            if (-not $match.Success) { break }
            $line = $line.Substring($match.Length)
        }
        $lines.Add($line)
    }
    return @($lines.ToArray()) -join "`n"
}

function ConvertTo-FlowRenderedHeadingLabel {
    param([AllowEmptyString()][string]$Value)
    $label = ConvertTo-FlowVisibleInlineText $Value
    $label = [regex]::Replace($label, '\s*\{[^}]*\}\s*$', '')
    $label = [regex]::Replace($label.Trim(), '^[*_~]+|[*_~]+$', '')
    return [regex]::Replace($label, '\s+', ' ').Trim()
}

function Get-FlowDuplicateH2Findings {
    param([AllowEmptyString()][string]$Markdown, [string[]]$ControlledSections)
    $visible = Remove-FlowSafetyComments $Markdown
    $findings = New-Object System.Collections.Generic.List[string]
    foreach ($section in @($ControlledSections | Select-Object -Unique)) {
        $count = @([regex]::Matches($visible, '(?m)^[ ]{0,3}##\s+' + [regex]::Escape($section) + '\s*#*\s*$')).Count
        if ($count -gt 1) { $findings.Add("program-set review contains duplicate controlled ## section: $section") }
    }
    return @($findings.ToArray())
}

function Get-FlowProhibitedContentFindings {
    param([string]$Markdown)
    $findings = New-Object System.Collections.Generic.List[string]
    $seen = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
    $visible = Remove-FlowSafetyComments $Markdown
    foreach ($rawLine in @($visible -split "`r?`n")) {
      $rawLine = ConvertTo-FlowVisibleInlineText $rawLine
      $lineHasBoundary = [regex]::IsMatch($rawLine, '\b(?:microservice|cloud\s+service|service\s+boundar(?:y|ies))\b', 'IgnoreCase')
      $affirmativeContinuation = '(?:recommend\w*|convert\w*|moderni[sz]\w*|migrat\w*|carv\w*|creat\w*|split\w*|mov\w*|extract\w*|rewrit\w*|replac\w*|BR-[A-Za-z0-9_@#$-]+|(?:it|we|[A-Z@#$][A-Z0-9_@#$-]*)\s+(?:should|must|will|would|is|are)\b)'
      $clausePattern = '(?<=[.!?;])\s+|;\s*|[—–]|\b(?:but|however|although|though|nevertheless|yet)\b|,\s*(?=(?:then\b|we\b|it\b|will\b|would\b|must\b|should\b|convert\b|moderni[sz]e\b|migrat\w*\b|carve\b|create\b|split\b|move\b|recommend\b))|\b(?:and|then)\b(?=\s+' + $affirmativeContinuation + ')'
      foreach ($rawClause in @([regex]::Split($rawLine, $clausePattern, 'IgnoreCase'))) {
        $line = $rawClause.Trim()
        if (-not $line) { continue }
        $checks = @(
            [pscustomobject]@{ Label = 'modernization decision/recommendation'; Pattern = '\bmoderni[sz]ation\s+(?:decision|recommendation|proposal)\s*(?::|[—–-]|$)' },
            [pscustomobject]@{ Label = 'service boundary decision/recommendation'; Pattern = '\bservice\s+boundary\s+(?:decision|recommendation|proposal)\s*(?::|[—–-]|$)' },
            [pscustomobject]@{ Label = 'business rule output'; Pattern = '\bbusiness\s+rules?\b|\bBR-[A-Za-z0-9_@#$-]+\b' },
            [pscustomobject]@{ Label = 'architecture decision/recommendation'; Pattern = '\barchitecture(?:\s+(?:decision|recommendation|proposal))?\s*(?::|[—–-]|$)' }
        )
        $negation = '\b(?:must|should|do|does|did|will|would|is|are|was|were|has|have)\s+not\b|\bno\s+(?:plan|decision|recommendation|proposal|business\s+rules?)\b|\bwithout\s+(?:recommending|creating|defining|inferring|proposing)\b|\bout\s+of\s+scope\b|\bdoes\s+not\s+(?:define|recommend|infer)\b'
        $isNegated = [regex]::IsMatch($line, $negation, 'IgnoreCase')
        foreach ($check in $checks) {
            if ([regex]::IsMatch($line, $check.Pattern, 'IgnoreCase') -and -not $isNegated -and $seen.Add($check.Label)) {
                $findings.Add("program-set review contains prohibited $($check.Label)")
            }
        }
        $implementation = '\b(?:extract(?:s|ed|ing)?|rewrit(?:e|es|ten|ing)|replac(?:e|es|ed|ing)|migrat(?:e|es|ed|ing)|moderni[sz](?:e|es|ed|ing)|convert(?:s|ed|ing)?|carv(?:e|es|ed|ing)|creat(?:e|es|ed|ing)|split(?:s|ting)?|mov(?:e|es|ed|ing)|becom(?:e|es|ing)|recommend(?:s|ed|ing)?)\b'
        $migration = $implementation + '.{0,100}\b(?:microservice|cloud\s+service|service\s+boundary)\b'
        $boundaryTerm = '\b(?:microservice|cloud\s+service|service\s+boundar(?:y|ies))\b'
        if ([regex]::IsMatch($line, $migration, 'IgnoreCase') -and -not $isNegated -and $seen.Add('modernization implementation recommendation')) {
            $findings.Add('program-set review contains prohibited modernization implementation recommendation')
        }
        if ([regex]::IsMatch($line, $boundaryTerm, 'IgnoreCase') -and -not $isNegated -and $seen.Add('service boundary decision/recommendation')) {
            $findings.Add('program-set review contains prohibited service boundary decision/recommendation')
        }
        if ($lineHasBoundary -and [regex]::IsMatch($line, $implementation, 'IgnoreCase') -and ([regex]::IsMatch($line, $boundaryTerm, 'IgnoreCase') -or [regex]::IsMatch($line, '\b(?:one|it)\b', 'IgnoreCase')) -and -not $isNegated -and $seen.Add('service boundary decision/recommendation')) { $findings.Add('program-set review contains prohibited service boundary decision/recommendation') }
      }
    }
    return @($findings.ToArray())
}

function Get-FlowProgramOrderFindings {
    param([AllowEmptyString()][string]$Markdown)
    $context = '\b(?:programs?|program\s+list|list|navigation|input|SME|supplied|listed|ordered|sequence|first|next)\b'
    $marker = '\b(?:order|list|listed|ordered|sequence|first|next|precedes?|follows?)\b'
    $target = '\b(?:call|execution|runtime|run)\s+(?:chain|path|order|sequence)\b|\bactual\s+call\s+path\b|\bruns?\s+first\b|\b(?:precedes?|follows?)\b.{0,40}\b(?:runtime|run|program)\b|\bexecutes?\s+in\s+(?:the\s+)?(?:listed|supplied)\s+order\b'
    $assertion = '\b(?:represents?|reflects?|proves?|establishes?|shows?|confirms?|means?|defines?|equals?|is|are|runs?|executes?|listed|precedes?|follows?)\b'
    $disclaimer = '\b(?:not|never|cannot)\b.{0,80}(?:call|execution|runtime|run)\s+(?:chain|path|order|sequence)\b|\bno\b.{0,80}(?:call|execution|runtime|run)\s+(?:chain|path|order|sequence)\b|\b(?:do|does|did|is|are)\s+not\b.{0,60}\b(?:run|precede|follow|define|equal)|\bdoes\s+not\s+(?:represent|reflect|prove|establish|show|confirm|define|equal)\b'
    $directClaim = '\bprograms?\b.{0,50}\bruns?\b.{0,30}\bsupplied\s+order\b|\bfirst\s+listed\b.{0,40}\bprecedes?\b.{0,40}\bnext\b.{0,40}\bruntime\b|\bSME\s+input\s+sequence\b.{0,30}\bactual\s+call\s+path\b|\bordered\s+list\b.{0,30}\bdefines?\b.{0,50}\b(?:runs?\s+first|follows?)\b|\bnavigation\s+order\b.{0,30}\bequals?\b.{0,30}\bruntime\s+order\b'
    $spanPattern = '(?<=[.!?])\s+|[;:—–]|\b(?:but|however|although|though|nevertheless|yet)\b|,\s*(?=(?:the\b|it\b|we\b|programs?\b|list\b|order\b))|\b(?:and|then)\b(?=\s+(?:it\s+)?(?:represents?|reflects?|proves?|establishes?|shows?|confirms?|means?|is|are|executes?|listed|ordered)\b)'
    $priorContext = $false; $priorMarker = $false
    $surface = @((Remove-FlowSafetyComments $Markdown) -split "`r?`n" | ForEach-Object { ConvertTo-FlowVisibleInlineText $_ }) -join "`n"
    foreach ($clause in @([regex]::Split($surface, $spanPattern, 'IgnoreCase'))) {
        $localContext = [regex]::IsMatch($clause, $context, 'IgnoreCase')
        $localMarker = [regex]::IsMatch($clause, $marker, 'IgnoreCase')
        $assertsOrder = [regex]::IsMatch($clause, $directClaim, 'IgnoreCase') -or (($localContext -or $priorContext) -and ($localMarker -or $priorMarker) -and [regex]::IsMatch($clause, $target, 'IgnoreCase') -and [regex]::IsMatch($clause, $assertion, 'IgnoreCase'))
        if ($assertsOrder -and -not [regex]::IsMatch($clause, $disclaimer, 'IgnoreCase')) {
            return @('program list/navigation order must not be treated as a source-confirmed call chain or runtime execution sequence')
        }
        $priorContext = $localContext; $priorMarker = $localMarker
    }
    return @()
}

function Get-FlowUnmappedCoreProseFindings {
    param([AllowEmptyString()][string]$Markdown, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $visible = Remove-FlowSafetyComments $Markdown
    $programs = @(@(Get-SafetyMapValue $Manifest 'programs' @()) | ForEach-Object { [string](Get-SafetyMapValue $_ 'normalized_name' '') } | Where-Object { $_ })
    $profile = Get-SafetyMapValue $Manifest 'core_review_profile' ([ordered]@{})
    $messageSection = if ([bool](Get-SafetyMapValue $profile 'include_message_inventory' $true)) { 'Message Inventory' } else { 'Message Coverage Control' }
    $materialAction = '\b(?:always|whenever|sets?|assigns?|calculates?|derives?|validates?|rejects?|returns?|writes?|updates?|persists?|suppresses?|emits?|queues?|calls?|invokes?|starts?|runs?|supplies?|yields?|publishes?)\b'
    foreach ($section in @('Calculation Logic', 'Validation Logic', 'Exception Handling', $messageSection)) {
        $block = Get-FlowSafetyH2Block $visible $section; if (-not $block) { continue }; $block = ConvertTo-FlowUnquotedMarkdownSurface $block
        $proseLines = New-Object System.Collections.Generic.List[string]
        foreach ($line in @($block -split "`r?`n")) {
            $trimmed = $line.TrimStart()
            if ($trimmed -and -not ($trimmed.StartsWith('#') -or $trimmed.StartsWith('|'))) { $proseLines.Add($line) } else { $proseLines.Add('') }
        }
        foreach ($paragraph in @([regex]::Split(($proseLines -join "`n"), "`n\s*`n"))) {
            $claim = [regex]::Replace((ConvertTo-FlowVisibleInlineText $paragraph).Trim(), '\s+', ' ')
            if (-not $claim -or -not [regex]::IsMatch($claim, $materialAction, 'IgnoreCase')) { continue }
            if (@($programs | Where-Object { Test-FlowExactLiteral $claim ([string]$_) }).Count) { $findings.Add("$section contains deterministic program prose outside a canonical source-mapped fact table row") }
        }
    }
    return @($findings.ToArray())
}

function Test-FlowSafetyConnectorReachesCore {
    param([string]$Text, [int]$Index, [int]$Step)
    $cursor = $Index
    while ($cursor -ge 0 -and $cursor -lt $Text.Length -and $script:ExactTokenConnectors.Contains([string]$Text[$cursor])) {
        $cursor += $Step
    }
    return $cursor -ge 0 -and $cursor -lt $Text.Length -and [regex]::IsMatch([string]$Text[$cursor], '^' + $script:ExactTokenCorePattern + '$')
}

function Test-FlowSafetyExactOccurrence {
    param([string]$Text, [int]$Start, [int]$End)
    $before = $Start - 1
    $after = $End
    $beforeConnected = $before -ge 0 -and (
        [regex]::IsMatch([string]$Text[$before], '^' + $script:ExactTokenCorePattern + '$') -or
        ($script:ExactTokenConnectors.Contains([string]$Text[$before]) -and (Test-FlowSafetyConnectorReachesCore $Text $before -1))
    )
    $afterConnected = $after -lt $Text.Length -and (
        [regex]::IsMatch([string]$Text[$after], '^' + $script:ExactTokenCorePattern + '$') -or
        ($script:ExactTokenConnectors.Contains([string]$Text[$after]) -and (Test-FlowSafetyConnectorReachesCore $Text $after 1))
    )
    return -not $beforeConnected -and -not $afterConnected
}

function Get-FlowProgramOccurrences {
    param([string]$Text, [string[]]$Programs)
    $occurrences = New-Object System.Collections.Generic.List[object]
    foreach ($program in $Programs) {
        foreach ($match in @([regex]::Matches($Text, [regex]::Escape($program), 'IgnoreCase'))) {
            if (Test-FlowSafetyExactOccurrence $Text $match.Index ($match.Index + $match.Length)) {
                $occurrences.Add([pscustomobject]@{ Index = $match.Index; End = $match.Index + $match.Length; Program = $program })
            }
        }
    }
    return @($occurrences.ToArray() | Sort-Object Index, End)
}

function Get-FlowProgramMentions {
    param([string]$Text, [string[]]$Programs)
    return @(Get-FlowProgramOccurrences $Text $Programs | ForEach-Object { $_.Program })
}

function Get-FlowRelationProgramCandidates {
    param([string]$Claim, [string[]]$KnownPrograms)
    $programs = New-Object System.Collections.Generic.List[string]
    $seen = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($program in @($KnownPrograms)) { if ($program -and $seen.Add([string]$program)) { $programs.Add([string]$program) } }
    $candidateStopWords = @('API', 'CARRIER', 'DB', 'ERROR', 'FACT', 'IBM', 'INPUT', 'IO', 'MAIN', 'MESSAGE', 'OUTPUT', 'PROGRAM', 'REQUEST', 'RESPONSE', 'RESULT', 'REVIEW', 'RPG', 'ROUTINE', 'SME', 'SOURCE', 'SQL', 'STATUS', 'TARGET', 'UI')
    $occurrences = @([regex]::Matches($Claim, '(?<![A-Za-z0-9_@#$-])[A-Z@#$][A-Z0-9_@#$]{0,9}(?![A-Za-z0-9_@#$-])') | Where-Object { $_.Value.ToUpperInvariant() -notin $candidateStopWords } | ForEach-Object { [pscustomobject]@{ Index = $_.Index; End = $_.Index + $_.Length; Value = $_.Value } })
    for ($leftIndex = 0; $leftIndex -lt $occurrences.Count; $leftIndex++) {
        $left = $occurrences[$leftIndex]
        for ($rightIndex = $leftIndex + 1; $rightIndex -lt $occurrences.Count; $rightIndex++) {
            $right = $occurrences[$rightIndex]; $betweenLength = [int]$right.Index - [int]$left.End
            if ($betweenLength -gt 180) { break }; $between = $Claim.Substring([int]$left.End, $betweenLength)
            if (-not (Test-FlowRelationBridge $between)) { continue }
            foreach ($value in @([string]$left.Value, [string]$right.Value)) { if ($seen.Add($value)) { $programs.Add($value) } }
            $previous = $right
            foreach ($continuation in @($occurrences | Select-Object -Skip ($rightIndex + 1))) {
                $continuationBetween = $Claim.Substring([int]$previous.End, [int]$continuation.Index - [int]$previous.End)
                if (-not [regex]::IsMatch($continuationBetween, '^\s*(?:,|;|&|and|or|and/or|as\s+well\s+as)+\s*$', 'IgnoreCase')) { break }
                if ($seen.Add([string]$continuation.Value)) { $programs.Add([string]$continuation.Value) }; $previous = $continuation
            }
            break
        }
    }
    return @($programs.ToArray())
}

function Get-FlowRelationPairs {
    param([string]$Claim, [string[]]$KnownPrograms)
    $occurrences = @(Get-FlowProgramOccurrences $Claim $KnownPrograms)
    $pairs = New-Object System.Collections.Generic.List[object]
    $seen = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    $lastSource = ''; $lastTarget = ''; $lastPolarity = ''
    for ($index = 0; $index + 1 -lt $occurrences.Count; $index++) {
        $left = $occurrences[$index]
        $right = $occurrences[$index + 1]
        if ($left.Program -eq $right.Program) { continue }
        $betweenLength = [int]$right.Index - [int]$left.End
        if ($betweenLength -lt 0 -or $betweenLength -gt 180) { continue }
        $between = $Claim.Substring([int]$left.End, $betweenLength)
        $source = ''; $target = ''; $polarity = ''
        if (Test-FlowRelationBridge $between) {
            $source = [string]$left.Program
            $target = [string]$right.Program
            if ([regex]::IsMatch($between, $script:ReverseRelationPattern, 'IgnoreCase')) {
                $source = [string]$right.Program
                $target = [string]$left.Program
            }
            $polarity = if ([regex]::IsMatch($between, $script:NegativeRelationPattern, 'IgnoreCase')) { 'negative' } else { 'positive' }
        }
        elseif ($lastSource -and $lastTarget -eq [string]$left.Program -and [regex]::IsMatch($between, '^\s*(?:,\s*|(?:,\s*)?(?:and|or)(?:\s+then)?\s+)(?:both\s*)?$', 'IgnoreCase')) {
            $source = $lastSource
            $target = [string]$right.Program
            $polarity = $lastPolarity
        }
        if (-not $source -or -not $target) { continue }
        $key = "${source}`t${target}`t${polarity}"
        if ($seen.Add($key)) { $pairs.Add([pscustomobject]@{ Source = $source; Target = $target; Polarity = $polarity; Key = $key }) }
        $lastSource = $source; $lastTarget = $target; $lastPolarity = $polarity
    }
    return @($pairs.ToArray())
}

function Get-FlowMaterialRelationTokens {
    param([string]$Claim, [string[]]$KnownPrograms)
    $surface = [regex]::Replace($Claim, $script:SourceFactPattern, ' ')
    $programLookup = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($program in $KnownPrograms) { [void]$programLookup.Add([string]$program) }
    $stop = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($word in @('A', 'AN', 'THE', 'AND', 'OR', 'BOTH', 'TO', 'FROM', 'BY', 'VIA', 'WITH', 'OF', 'FOR', 'AS', 'IS', 'ARE', 'WAS', 'WERE', 'NOT', 'NO', 'NEVER', 'CANNOT', 'CALL', 'CALLS', 'CALLED', 'INVOKE', 'INVOKES', 'INVOKED', 'HANDOFF', 'HANDS', 'OFF', 'DELEGATE', 'DELEGATES', 'ROUTE', 'ROUTES', 'ROUTED', 'FORWARD', 'FORWARDS', 'FORWARDED', 'TRANSFER', 'TRANSFERS', 'DISPATCH', 'DISPATCHES', 'TRIGGER', 'TRIGGERS', 'TRIGGERED', 'LAUNCH', 'LAUNCHES', 'LAUNCHED', 'SUBMIT', 'SUBMITS', 'PASS', 'PASSES', 'SEND', 'SENDS', 'RETURN', 'RETURNS', 'PROVIDE', 'PROVIDES', 'PROVIDED', 'SUPPLY', 'SUPPLIES', 'SUPPLIED', 'YIELD', 'YIELDS', 'YIELDED', 'EMIT', 'EMITS', 'EMITTED', 'WRITE', 'WRITES', 'WRITTEN', 'START', 'STARTS', 'STARTED', 'RUN', 'RUNS', 'QUEUE', 'QUEUES', 'QUEUED', 'PUBLISH', 'PUBLISHES', 'PUBLISHED', 'REQUEST', 'REQUESTS', 'REQUESTED', 'CHAIN', 'CHAINS', 'CHAINED', 'PRECEDE', 'PRECEDES', 'FOLLOW', 'FOLLOWS', 'DELIVER', 'DELIVERS', 'DELIVERED', 'EXCHANGE', 'EXCHANGES', 'COMMUNICATE', 'COMMUNICATES', 'DEPEND', 'DEPENDS', 'MAP', 'MAPS', 'MAPPED', 'POPULATE', 'POPULATES', 'POPULATED', 'CONNECT', 'CONNECTS', 'CONNECTED', 'CONTINUE', 'CONTINUES', 'RECEIVE', 'RECEIVES', 'RECEIVED', 'FLOW', 'FLOWS', 'PRODUCER', 'PRODUCES', 'PRODUCED', 'CONSUMER', 'CONSUMES', 'CONSUMED', 'USE', 'USES', 'READ', 'READS', 'THEN', 'BEFORE', 'AFTER', 'EXECUTE', 'EXECUTES', 'SOURCE', 'TARGET', 'CARRIER', 'MAIN', 'SME', 'IBM')) { [void]$stop.Add($word) }
    foreach ($word in @('IN', 'THAT', 'ORDER', 'PROGRAM', 'PROGRAMS', 'REQUEST', 'RESPONSE', 'STATUS', 'MESSAGE', 'RPG', 'SQL', 'API', 'UI', 'DB', 'IO', 'CAN', 'DOES')) { [void]$stop.Add($word) }
    $tokens = New-Object System.Collections.Generic.List[string]
    $seen = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::Ordinal)
    foreach ($match in @([regex]::Matches($surface, '(?<![A-Za-z0-9_@#$%*+-])[A-Z@#$%*+][A-Z0-9_@#$%*+-]{1,}(?![A-Za-z0-9_@#$%*+-])'))) {
        $token = $match.Value
        $isEvidenceId = [regex]::IsMatch($token, '^(?:SF|RLOG|MSG|EV|DATA|TBD|EXCHAIN|LINEAGE|PERSIST)-')
        if (-not $programLookup.Contains($token) -and -not $stop.Contains($token) -and -not $isEvidenceId -and $seen.Add($token)) { $tokens.Add($token) }
    }
    return @($tokens.ToArray())
}

function Get-FlowFactRelationSegments {
    param($Fact)
    $program = [string](Get-SafetyMapValue $Fact 'program' '')
    $segments = New-Object System.Collections.Generic.List[string]
    foreach ($key in @('source_text', 'logic', 'calculation', 'description', 'exception_path', 'guard', 'trigger_chain', 'effect', 'supporting_detail')) {
        $text = [string](Get-SafetyMapValue $Fact $key '')
        if (-not $text.Trim()) { continue }
        if ($program -and -not [regex]::IsMatch($text, [regex]::Escape($program), 'IgnoreCase')) { $text = "$program $text" }
        $segments.Add($text)
    }
    foreach ($key in @('source_row', 'source_cells')) {
        $value = Get-SafetyMapValue $Fact $key $null
        $items = @()
        if ($value -is [Collections.IDictionary]) { $items = @($value.Values) }
        elseif ($value -is [Collections.IEnumerable] -and $value -isnot [string]) { $items = @($value) }
        if ($items.Count) {
            $text = @($items | ForEach-Object { [string]$_ } | Where-Object { $_.Trim() }) -join ' '
            if ($program -and -not [regex]::IsMatch($text, [regex]::Escape($program), 'IgnoreCase')) { $text = "$program $text" }
            if ($text) { $segments.Add($text) }
        }
    }
    return @($segments.ToArray() | Sort-Object -Unique)
}

function Test-FlowRelationSupportedBySingleFact {
    param([string]$Claim, [string[]]$Refs, $FactById, [string[]]$KnownPrograms)
    $KnownPrograms = @(Get-FlowRelationProgramCandidates $Claim $KnownPrograms)
    $claimedPairs = @(Get-FlowRelationPairs $Claim $KnownPrograms)
    if (-not $claimedPairs.Count) { return $false }
    $mentioned = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($program in @(Get-FlowProgramMentions $Claim $KnownPrograms)) { [void]$mentioned.Add([string]$program) }
    $covered = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
    foreach ($pair in $claimedPairs) { [void]$covered.Add([string]$pair.Source); [void]$covered.Add([string]$pair.Target) }
    if (-not $covered.SetEquals($mentioned)) { return $false }
    $materialTokens = @(Get-FlowMaterialRelationTokens $Claim $KnownPrograms)
    foreach ($ref in $Refs) {
        if (-not $FactById.ContainsKey($ref)) { continue }
        foreach ($segment in @(Get-FlowFactRelationSegments $FactById[$ref])) {
            $segmentPairKeys = New-Object System.Collections.Generic.HashSet[string]([StringComparer]::OrdinalIgnoreCase)
            foreach ($pair in @(Get-FlowRelationPairs $segment $KnownPrograms)) { [void]$segmentPairKeys.Add([string]$pair.Key) }
            $missingPair = @($claimedPairs | Where-Object { -not $segmentPairKeys.Contains([string]$_.Key) }).Count -gt 0
            $missingToken = @($materialTokens | Where-Object { -not (Test-FlowSafetyExactLiteral $segment ([string]$_)) }).Count -gt 0
            if (-not $missingPair -and -not $missingToken) { return $true }
        }
    }
    return $false
}

function Test-FlowClaimHasRelation {
    param([string]$Claim, [string[]]$KnownPrograms)
    $surface = [regex]::Replace($Claim, '\b(?:starts?|runs?|precedes?|follows?)\b(?!\s+by\b)', ' ', 'IgnoreCase')
    if ([regex]::IsMatch($surface, $script:RelationIndicatorPattern, 'IgnoreCase')) { return $true }
    return @(Get-FlowRelationPairs $Claim $KnownPrograms).Count -gt 0
}

function Test-FlowSafetyExactLiteral {
    param([string]$Text, [string]$Literal)
    foreach ($match in @([regex]::Matches($Text, [regex]::Escape($Literal)))) {
        if (Test-FlowSafetyExactOccurrence $Text $match.Index ($match.Index + $match.Length)) { return $true }
    }
    return $false
}

function Test-FlowSafetyTableSeparator {
    param([string]$Line)
    return Test-FlowMarkdownTableSeparator $Line
}

function Get-FlowTableRelationClaimUnits {
    param([string]$Block, [string[]]$KnownPrograms)
    $units = New-Object System.Collections.Generic.List[object]
    $lines = @($Block -split "`r?`n")
    for ($index = 0; $index + 1 -lt $lines.Count; $index++) {
        $headerLine = $lines[$index].Trim()
        if (-not ($headerLine.StartsWith('|') -and $headerLine.EndsWith('|') -and (Test-FlowSafetyTableSeparator $lines[$index + 1]))) { continue }
        $headers = @(Split-FlowMarkdownTableRow $headerLine)
        $separatorCells = @(Split-FlowMarkdownTableRow $lines[$index + 1])
        if ($separatorCells.Count -ne $headers.Count) {
            $cursor = $index + 2
            while ($cursor -lt $lines.Count -and $lines[$cursor].Trim().StartsWith('|') -and $lines[$cursor].Trim().EndsWith('|')) {
                $rowLine = $lines[$cursor].Trim(); $claim = ConvertTo-FlowVisibleInlineText $rowLine
                $refs = @([regex]::Matches($claim, $script:SourceFactPattern) | ForEach-Object { $_.Value } | Select-Object -Unique)
                $units.Add([pscustomobject]@{ Claim = $claim; Refs = $refs; RequiresExplicitPair = $false }); $cursor++
            }
            $index = $cursor - 1; continue
        }
        if (-not (Test-FlowMarkdownTableHeaderAndSeparator $headerLine $lines[$index + 1])) { continue }
        $normalized = @($headers | ForEach-Object { $_.ToLowerInvariant() })
        $subjectIndex = [Array]::IndexOf($normalized, 'program')
        $overviewProgramsIndex = [Array]::IndexOf($normalized, 'programs / main routines')
        for ($cursor = $index + 2; $cursor -lt $lines.Count; $cursor++) {
            $rowLine = $lines[$cursor].Trim()
            if (-not ($rowLine.StartsWith('|') -and $rowLine.EndsWith('|'))) { break }
            $cells = @(Split-FlowMarkdownTableRow $rowLine)
            $refs = @([regex]::Matches((ConvertTo-FlowVisibleInlineText $rowLine), $script:SourceFactPattern) | ForEach-Object { $_.Value } | Select-Object -Unique)
            if ($cells.Count -gt $headers.Count) { $units.Add([pscustomobject]@{ Claim = (ConvertTo-FlowVisibleInlineText ($cells -join ' ')); Refs = $refs; RequiresExplicitPair = $false }) }
            $subject = if ($subjectIndex -ge 0 -and $subjectIndex -lt $cells.Count) { ConvertTo-FlowVisibleInlineText ([string]$cells[$subjectIndex]) } else { '' }
            $overviewPrograms = if ($overviewProgramsIndex -ge 0 -and $overviewProgramsIndex -lt $cells.Count) { ConvertTo-FlowVisibleInlineText ([string]$cells[$overviewProgramsIndex]) } else { '' }
            $requiresExplicitPair = @(Get-FlowProgramMentions $overviewPrograms $KnownPrograms | Select-Object -Unique).Count -ge 2
            for ($cellIndex = 0; $cellIndex -lt $headers.Count -and $cellIndex -lt $cells.Count; $cellIndex++) {
                $header = $normalized[$cellIndex]
                if ($header -in @('program', 'routine', 'program / routine sources', 'programs / main routines', 'review row id', 'source fact refs')) { continue }
                $claim = ConvertTo-FlowVisibleInlineText ([string]$cells[$cellIndex])
                if ($subject.Trim() -and -not (Test-FlowExactLiteral $claim $subject -IgnoreCase)) { $claim = "$subject $claim" }
                $claimPrograms = @(Get-FlowRelationProgramCandidates $claim $KnownPrograms)
                if (-not (Test-FlowClaimHasRelation $claim $claimPrograms)) { continue }
                $units.Add([pscustomobject]@{ Claim = $claim; Refs = $refs; RequiresExplicitPair = $requiresExplicitPair })
            }
        }
    }
    return @($units.ToArray())
}

function Get-FlowProseRelationClaimUnits {
    param([string]$Block)
    $proseLines = New-Object System.Collections.Generic.List[string]
    foreach ($line in @($Block -split "`r?`n")) {
        $trimmed = $line.TrimStart()
        if ($trimmed.StartsWith('|')) { continue }
        if ([regex]::IsMatch($trimmed, '^#{1,6}\s+')) { $trimmed = [regex]::Replace($trimmed, '^#{1,6}\s+|\s+#+\s*$', '') }
        $proseLines.Add($trimmed)
    }
    $units = New-Object System.Collections.Generic.List[object]
    foreach ($paragraph in @([regex]::Split(($proseLines -join "`n"), "`n\s*`n"))) {
        $refs = @([regex]::Matches((ConvertTo-FlowVisibleInlineText $paragraph), $script:SourceFactPattern) | ForEach-Object { $_.Value } | Select-Object -Unique)
        $rendered = [regex]::Replace((ConvertTo-FlowVisibleInlineText $paragraph).Trim(), '\s+', ' ')
        foreach ($clause in @([regex]::Split($rendered, '(?<=[.!?;])\s+|;\s*'))) {
            $claim = $clause.Trim(); if (-not $claim) { continue }
            $units.Add([pscustomobject]@{ Claim = $claim; Refs = $refs; RequiresExplicitPair = $false })
        }
    }
    return @($units.ToArray())
}

function Get-FlowCrossProgramRelationFindings {
    param([string]$Markdown, $FactById, $Manifest)
    $findings = New-Object System.Collections.Generic.List[string]
    $known = @(@(Get-SafetyMapValue $Manifest 'programs' @()) | ForEach-Object { [string](Get-SafetyMapValue $_ 'normalized_name' '') } | Where-Object { $_ } | Select-Object -Unique)
    $visible = Remove-FlowSafetyComments $Markdown
    $units = @((Get-FlowTableRelationClaimUnits $visible $known)) + @((Get-FlowProseRelationClaimUnits $visible))
    foreach ($unit in $units) {
        $claim = [string]$unit.Claim
        if (-not $claim) { continue }
        $claimPrograms = @(Get-FlowRelationProgramCandidates $claim $known)
        if (-not (Test-FlowClaimHasRelation $claim $claimPrograms)) { continue }
        $claimedPairs = @(Get-FlowRelationPairs $claim $claimPrograms)
        if (-not $claimedPairs.Count) {
            $mentionedPrograms = @(Get-FlowProgramMentions $claim $claimPrograms | Select-Object -Unique)
            if ([bool]$unit.RequiresExplicitPair -or $mentionedPrograms.Count -ge 2) {
                $findings.Add('final review contains an unsupported cross-program relation/sequence claim')
            }
            continue
        }
        $refs = @($unit.Refs)
        if (-not $refs.Count -or -not (Test-FlowRelationSupportedBySingleFact $claim $refs $FactById $claimPrograms)) {
            $findings.Add('final review contains an unsupported cross-program relation/sequence claim')
        }
    }
    return @($findings.ToArray())
}

Export-ModuleMember -Function Get-FlowForbiddenHeadingFindings, Get-FlowDuplicateH2Findings, Get-FlowProhibitedContentFindings, Get-FlowProgramOrderFindings, Get-FlowUnmappedCoreProseFindings, Test-FlowRelationSupportedBySingleFact, Get-FlowCrossProgramRelationFindings
