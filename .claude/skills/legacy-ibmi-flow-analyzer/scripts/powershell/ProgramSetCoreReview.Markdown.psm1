<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Native PowerShell 5.1 helpers for safely reading rendered Markdown structure.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

$script:FlowMarkdownRenderedHtmlTags = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($tag in @('a', 'abbr', 'article', 'aside', 'b', 'blockquote', 'br', 'button', 'caption', 'cite', 'code', 'col', 'colgroup', 'dd', 'del', 'details', 'dfn', 'div', 'dl', 'dt', 'em', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'i', 'img', 'input', 'ins', 'kbd', 'label', 'li', 'main', 'mark', 'nav', 'ol', 'option', 'p', 'pre', 'q', 's', 'samp', 'section', 'select', 'small', 'span', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'time', 'tr', 'u', 'ul', 'var')) { [void]$script:FlowMarkdownRenderedHtmlTags.Add($tag) }
$script:FlowMarkdownVoidHtmlTags = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($tag in @('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr')) { [void]$script:FlowMarkdownVoidHtmlTags.Add($tag) }

function Get-FlowMarkdownClosingCodeRunIndex {
    param([string]$Text, [int]$Start, [int]$RunLength)
    for ($cursor = $Start; $cursor -lt $Text.Length; $cursor++) {
        if ($Text[$cursor] -ne '`') { continue }
        $candidateLength = 1
        while ($cursor + $candidateLength -lt $Text.Length -and $Text[$cursor + $candidateLength] -eq '`') { $candidateLength++ }
        if ($candidateLength -eq $RunLength) { return $cursor }
        $cursor += $candidateLength - 1
    }
    return -1
}

function Test-FlowMarkdownClosingCodeRun {
    param([string]$Text, [int]$Start, [int]$RunLength)
    return (Get-FlowMarkdownClosingCodeRunIndex $Text $Start $RunLength) -ge 0
}

function Test-FlowMarkdownCharacterEscaped {
    param([string]$Text, [int]$Index)
    $slashes = 0
    for ($cursor = $Index - 1; $cursor -ge 0 -and $Text[$cursor] -eq '\'; $cursor--) { $slashes++ }
    return ($slashes % 2) -eq 1
}

function Get-FlowMarkdownClosingLinkDestinationIndex {
    param([string]$Text, [int]$Start)
    $depth = 1
    for ($cursor = $Start; $cursor -lt $Text.Length; $cursor++) {
        if ($Text[$cursor] -eq '\') { $cursor++; continue }
        if ($Text[$cursor] -eq '(') { $depth++ }
        elseif ($Text[$cursor] -eq ')') { $depth--; if ($depth -eq 0) { return $cursor } }
    }
    return -1
}

function Test-FlowMarkdownClosingLinkDestination {
    param([string]$Text, [int]$Start)
    return (Get-FlowMarkdownClosingLinkDestinationIndex $Text $Start) -ge 0
}

function Split-FlowMarkdownTableRow {
    param([AllowEmptyString()][string]$Line)
    $text = $Line.Trim()
    $cells = New-Object System.Collections.Generic.List[string]
    $cell = New-Object System.Text.StringBuilder
    $codeFenceLength = 0
    $linkDestinationDepth = 0
    for ($index = 0; $index -lt $text.Length; $index++) {
        $character = $text[$index]
        if ($character -eq '\') {
            [void]$cell.Append($character)
            if ($index + 1 -lt $text.Length) { $index++; [void]$cell.Append($text[$index]) }
            continue
        }
        if ($character -eq '`') {
            $runLength = 1
            while ($index + $runLength -lt $text.Length -and $text[$index + $runLength] -eq '`') { $runLength++ }
            [void]$cell.Append($text.Substring($index, $runLength))
            if ($codeFenceLength -eq 0 -and (Test-FlowMarkdownClosingCodeRun $text ($index + $runLength) $runLength)) { $codeFenceLength = $runLength }
            elseif ($runLength -eq $codeFenceLength) { $codeFenceLength = 0 }
            $index += $runLength - 1
            continue
        }
        if ($codeFenceLength -eq 0) {
            if ($linkDestinationDepth -eq 0 -and $character -eq '(' -and $index -gt 0 -and $text[$index - 1] -eq ']' -and -not (Test-FlowMarkdownCharacterEscaped $text ($index - 1)) -and (Test-FlowMarkdownClosingLinkDestination $text ($index + 1))) { $linkDestinationDepth = 1 }
            elseif ($linkDestinationDepth -gt 0 -and $character -eq '(') { $linkDestinationDepth++ }
            elseif ($linkDestinationDepth -gt 0 -and $character -eq ')') { $linkDestinationDepth-- }
            elseif ($linkDestinationDepth -eq 0 -and $character -eq '|') {
                $cells.Add($cell.ToString().Trim()); [void]$cell.Clear(); continue
            }
        }
        [void]$cell.Append($character)
    }
    $cells.Add($cell.ToString().Trim())
    $items = @($cells.ToArray())
    if ($items.Count -and $items[0] -eq '' -and $text.StartsWith('|')) { $items = @($items | Select-Object -Skip 1) }
    if ($items.Count -and $items[$items.Count - 1] -eq '' -and $text.EndsWith('|')) { $items = @($items | Select-Object -First ($items.Count - 1)) }
    return @($items)
}

function Test-FlowMarkdownTableSeparator {
    param([AllowEmptyString()][string]$Line, [int]$ExpectedCellCount = 0)
    $trimmed = $Line.Trim()
    if (-not ($trimmed.StartsWith('|') -and $trimmed.EndsWith('|'))) { return $false }
    $cells = @(Split-FlowMarkdownTableRow $trimmed)
    return $cells.Count -gt 0 -and ($ExpectedCellCount -le 0 -or $cells.Count -eq $ExpectedCellCount) -and @($cells | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -eq 0
}

function Test-FlowMarkdownTableHeaderAndSeparator {
    param([AllowEmptyString()][string]$HeaderLine, [AllowEmptyString()][string]$SeparatorLine)
    $header = $HeaderLine.Trim()
    if (-not ($header.StartsWith('|') -and $header.EndsWith('|'))) { return $false }
    $headerCells = @(Split-FlowMarkdownTableRow $header)
    return Test-FlowMarkdownTableSeparator $SeparatorLine $headerCells.Count
}

function Remove-FlowMarkdownInlineCodeForStructure {
    param([AllowEmptyString()][string]$Text)
    if (-not $Text) { return $Text }
    $characters = $Text.ToCharArray()
    for ($index = 0; $index -lt $Text.Length; $index++) {
        if ($Text[$index] -ne '`') { continue }
        $runLength = 1
        while ($index + $runLength -lt $Text.Length -and $Text[$index + $runLength] -eq '`') { $runLength++ }
        $closing = Get-FlowMarkdownClosingCodeRunIndex $Text ($index + $runLength) $runLength
        if ($closing -lt 0) { $index += $runLength - 1; continue }
        for ($cursor = $index; $cursor -lt $closing + $runLength; $cursor++) { if ($characters[$cursor] -notin @("`r", "`n")) { $characters[$cursor] = ' ' } }
        $index = $closing + $runLength - 1
    }
    return -join $characters
}

function Get-FlowMarkdownHtmlTokens {
    param([AllowEmptyString()][string]$Text)
    $tokens = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $Text.Length; $index++) {
        if ($Text[$index] -ne '<') { continue }
        $prefix = [regex]::Match($Text.Substring($index), '^<\s*(?<closing>/)?\s*(?<name>[A-Za-z][\w:-]*)')
        if (-not $prefix.Success) { continue }
        $quote = [char]0; $end = -1
        for ($cursor = $index + $prefix.Length; $cursor -lt $Text.Length; $cursor++) {
            $character = $Text[$cursor]
            if ($quote -ne [char]0) { if ($character -eq $quote) { $quote = [char]0 }; continue }
            if ($character -in @('"', "'")) { $quote = $character; continue }
            if ($character -eq '>') { $end = $cursor + 1; break }
        }
        if ($end -lt 0) { continue }
        $raw = $Text.Substring($index, $end - $index); $name = $prefix.Groups['name'].Value
        $attributesStart = $index + $prefix.Length; $attributesLength = ($end - 1) - $attributesStart
        $attributes = if ($attributesLength -gt 0) { $Text.Substring($attributesStart, $attributesLength) } else { '' }
        $tokens.Add([pscustomobject]@{ Index = $index; End = $end; Name = $name; Closing = $prefix.Groups['closing'].Success; SelfClosing = $raw.TrimEnd().EndsWith('/>') -or $script:FlowMarkdownVoidHtmlTags.Contains($name); Attributes = $attributes; Raw = $raw })
        $index = $end - 1
    }
    return @($tokens.ToArray())
}

function Get-FlowMarkdownHtmlAttributes {
    param([AllowEmptyString()][string]$Text)
    $attributes = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $Text.Length;) {
        while ($index -lt $Text.Length -and ($Text[$index] -in @(' ', "`t", "`r", "`n", '/'))) { $index++ }
        if ($index -ge $Text.Length) { break }
        $start = $index
        while ($index -lt $Text.Length -and $Text[$index] -notin @(' ', "`t", "`r", "`n", '=', '/', '>')) { $index++ }
        if ($index -eq $start) { $index++; continue }
        $name = $Text.Substring($start, $index - $start); $value = ''
        while ($index -lt $Text.Length -and $Text[$index] -in @(' ', "`t", "`r", "`n")) { $index++ }
        if ($index -lt $Text.Length -and $Text[$index] -eq '=') {
            $index++
            while ($index -lt $Text.Length -and $Text[$index] -in @(' ', "`t", "`r", "`n")) { $index++ }
            if ($index -lt $Text.Length -and $Text[$index] -in @('"', "'")) {
                $quote = $Text[$index]; $index++; $valueStart = $index
                while ($index -lt $Text.Length -and $Text[$index] -ne $quote) { $index++ }
                $value = $Text.Substring($valueStart, $index - $valueStart)
                if ($index -lt $Text.Length) { $index++ }
            }
            else {
                $valueStart = $index
                while ($index -lt $Text.Length -and $Text[$index] -notin @(' ', "`t", "`r", "`n", '/', '>')) { $index++ }
                $value = $Text.Substring($valueStart, $index - $valueStart)
            }
        }
        $attributes.Add([pscustomobject]@{ Name = $name; Value = $value })
    }
    return @($attributes.ToArray())
}

function Remove-FlowMarkdownLinkDestinations {
    param([AllowEmptyString()][string]$Text)
    $result = New-Object System.Text.StringBuilder
    for ($index = 0; $index -lt $Text.Length; $index++) {
        if ($Text[$index] -eq '(' -and $index -gt 0 -and $Text[$index - 1] -eq ']' -and -not (Test-FlowMarkdownCharacterEscaped $Text ($index - 1))) {
            $closing = Get-FlowMarkdownClosingLinkDestinationIndex $Text ($index + 1)
            if ($closing -ge 0) { $index = $closing; continue }
        }
        [void]$result.Append($Text[$index])
    }
    return $result.ToString()
}

function Remove-FlowMarkdownHtmlTags {
    param([AllowEmptyString()][string]$Text)
    if (-not $Text) { return $Text }
    $characters = $Text.ToCharArray()
    foreach ($token in @(Get-FlowMarkdownHtmlTokens $Text)) {
        if (-not $script:FlowMarkdownRenderedHtmlTags.Contains([string]$token.Name)) { continue }
        for ($index = [int]$token.Index; $index -lt [int]$token.End; $index++) { if ($characters[$index] -notin @("`r", "`n")) { $characters[$index] = ' ' } }
    }
    return -join $characters
}

function Get-FlowMarkdownIndentationColumns {
    param([AllowEmptyString()][string]$Line)
    $columns = 0
    foreach ($character in $Line.ToCharArray()) {
        if ($character -eq ' ') { $columns++ }
        elseif ($character -eq "`t") { $columns += 4 - ($columns % 4) }
        else { break }
    }
    return $columns
}

function Get-FlowMarkdownHiddenStartTag {
    param([AllowEmptyString()][string]$Line)
    foreach ($token in @(Get-FlowMarkdownHtmlTokens $Line)) {
        if ([bool]$token.Closing) { continue }
        $tag = ([string]$token.Name).ToLowerInvariant()
        if ($tag -match '^(?:template|style|script)$') { return $tag }
        foreach ($attribute in @(Get-FlowMarkdownHtmlAttributes ([string]$token.Attributes))) {
            if ([string]::Equals([string]$attribute.Name, 'hidden', [StringComparison]::OrdinalIgnoreCase)) { return $tag }
            if ([string]::Equals([string]$attribute.Name, 'style', [StringComparison]::OrdinalIgnoreCase) -and [regex]::IsMatch([string]$attribute.Value, '(?:display\s*:\s*none|visibility\s*:\s*hidden)', 'IgnoreCase')) { return $tag }
        }
    }
    return ''
}

function Get-FlowMarkdownTagDepthDelta {
    param([AllowEmptyString()][string]$Line, [string]$Tag)
    $depth = 0
    foreach ($token in @(Get-FlowMarkdownHtmlTokens $Line)) {
        if (-not [string]::Equals([string]$token.Name, $Tag, [StringComparison]::OrdinalIgnoreCase)) { continue }
        if ([bool]$token.Closing) { $depth-- }
        elseif (-not [bool]$token.SelfClosing) { $depth++ }
    }
    return $depth
}

function ConvertTo-FlowMarkdownStructuralLine {
    param([AllowEmptyString()][string]$Line)
    $surface = $Line
    while ($true) {
        $prefix = [regex]::Match($surface, '^[ ]{0,3}(?:>\s?|[-+*]\s+|\d{1,9}[.)]\s+)')
        if (-not $prefix.Success) { return $surface }
        $surface = $surface.Substring($prefix.Length)
    }
}

function Remove-FlowNonRenderedMarkdown {
    param([AllowEmptyString()][string]$Markdown)
    $visible = $Markdown
    $comments = @([regex]::Matches($visible, '<!--.*?-->', [Text.RegularExpressions.RegexOptions]::Singleline))
    for ($index = $comments.Count - 1; $index -ge 0; $index--) {
        $replacement = [regex]::Replace($comments[$index].Value, '[^\r\n]', '')
        $visible = $visible.Remove($comments[$index].Index, $comments[$index].Length).Insert($comments[$index].Index, $replacement)
    }
    $result = New-Object System.Collections.Generic.List[string]
    $fenceCharacter = ''; $fenceLength = 0; $hiddenTag = ''; $hiddenDepth = 0
    foreach ($line in @($visible -split "`r?`n")) {
        $surface = ConvertTo-FlowMarkdownStructuralLine $line
        $structuralSurface = Remove-FlowMarkdownInlineCodeForStructure $surface
        if ($fenceCharacter) {
            $closing = [regex]::Match($surface, '^[ \t]{0,3}(?<fence>`{3,}|~{3,})[ \t]*$')
            if ($closing.Success -and $closing.Groups['fence'].Value[0] -eq $fenceCharacter -and $closing.Groups['fence'].Value.Length -ge $fenceLength) { $fenceCharacter = ''; $fenceLength = 0 }
            $result.Add(''); continue
        }
        if ($hiddenTag) {
            $hiddenDepth += Get-FlowMarkdownTagDepthDelta $structuralSurface $hiddenTag
            if ($hiddenDepth -le 0) { $hiddenTag = ''; $hiddenDepth = 0 }
            $result.Add(''); continue
        }
        $opening = [regex]::Match($surface, '^[ \t]{0,3}(?<fence>`{3,}|~{3,})')
        if ($opening.Success) { $fenceCharacter = [string]$opening.Groups['fence'].Value[0]; $fenceLength = $opening.Groups['fence'].Value.Length; $result.Add(''); continue }
        if ((Get-FlowMarkdownIndentationColumns $surface) -ge 4) { $result.Add(''); continue }
        $startTag = Get-FlowMarkdownHiddenStartTag $structuralSurface
        if ($startTag) {
            $hiddenTag = $startTag; $hiddenDepth = Get-FlowMarkdownTagDepthDelta $structuralSurface $hiddenTag
            if ($hiddenDepth -le 0) { $hiddenTag = ''; $hiddenDepth = 0 }
            $result.Add(''); continue
        }
        $result.Add($line)
    }
    return @($result.ToArray()) -join "`n"
}

Export-ModuleMember -Function Split-FlowMarkdownTableRow, Test-FlowMarkdownTableSeparator, Test-FlowMarkdownTableHeaderAndSeparator, Remove-FlowMarkdownLinkDestinations, Remove-FlowMarkdownHtmlTags, Remove-FlowNonRenderedMarkdown
