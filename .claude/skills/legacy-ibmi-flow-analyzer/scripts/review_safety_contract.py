#!/usr/bin/env python3
"""Safety gates for a reader-first program-set Core Review.

Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
"""

from __future__ import annotations

import html
import re
from typing import Any, Iterable

from reader_first_markdown_contract import (
    is_markdown_table_separator,
    split_markdown_table_row,
    strip_html_tokens,
    strip_markdown_link_destinations,
)


EXACT_TOKEN_CORE_RE = re.compile(r"[A-Za-z0-9_@#$%*+]")
EXACT_TOKEN_CONNECTORS = frozenset("./:-")
SOURCE_FACT_RE = re.compile(
    r"(?<![A-Za-z0-9_@#$-])SF-[A-Za-z0-9_@#$-]+(?![A-Za-z0-9_@#$-])"
)
READER_FIRST_REVIEW_SECTIONS = (
    "Program Set Reading Summary",
    "Cross-Program Processing Overview",
    "Calculation Logic",
    "Validation Logic",
    "Exception Handling",
    "Message Inventory",
    "Message Coverage Control",
)

RELATION_CORE = (
    r"calls?|called\s+by|invokes?|invoked\s+by|"
    r"hands?\s+off(?:\s+to)?|hands?(?:\s+\S+){0,10}\s+off(?:\s+to)?|hand[- ]?off|"
    r"delegates?(?:\s+\S+){0,10}\s+to|routes?(?:\s+\S+){0,10}\s+to|"
    r"forwards?(?:\s+\S+){0,10}\s+to|transfers?(?:\s+\S+){0,10}\s+to|"
    r"dispatch(?:es)?(?:\s+\S+){0,10}\s+to|"
    r"triggers?|triggered\s+by|launches?|launched\s+by|"
    r"submits?(?:\s+\S+){0,10}\s+to|"
    r"passes?(?:\s+\S+){0,10}\s+to|sends?(?:\s+\S+){0,10}\s+to|"
    r"provides?(?:\s+\S+){0,10}\s+to|provided\s+by|"
    r"delivers?(?:\s+\S+){0,10}\s+to|delivered\s+by|"
    r"communicates?(?:\s+\S+){0,10}\s+with|"
    r"exchanges?(?:\s+\S+){0,10}\s+with|depends?\s+on|continues?\s+into|"
    r"maps?(?:\s+\S+){0,10}\s+to|populates?(?:\s+\S+){0,10}\s+for|"
    r"connects?(?:\s+\S+){0,10}\s+(?:to|with)|"
    r"suppl(?:y|ies)|suppl(?:y|ies)(?:\s+\S+){0,10}\s+(?:to|with)|"
    r"yields?(?:\s+\S+){0,10}\s+to|emits?(?:\s+\S+){0,10}\s+to|"
    r"writes?(?:\s+\S+){0,10}\s+(?:to|for)|"
    r"queues?(?:\s+\S+){0,10}\s+for|publishes?(?:\s+\S+){0,10}\s+to|"
    r"requests?(?:\s+\S+){0,10}\s+from|chains?\s+to|"
    r"returns?(?:\s+\S+){0,10}\s+to|feeds?|"
    r"receives?(?:\s+\S+){0,10}\s+from|flows?\s+(?:to|from)|"
    r"source\s+carrier\s+for|target\s+carrier\s+from|"
    r"producer|consumer|produces?|produced\s+by|consumes?|consumed\s+by|"
    r"received\s+by|routed\s+(?:to|by)|forwarded\s+(?:to|by)|"
    r"(?:uses?|reads?)(?:\s+\S+){0,10}\s+from|then|"
    r"executes?\s+(?:before|after|in\s+that\s+order)"
)
RELATION_INDICATOR_RE = re.compile(
    rf"\b(?:{RELATION_CORE})\b|(?:-{{1,2}}>|=>|→|⇒|<-{{1,2}}|<=|←|⇐)", re.I
)
_DIRECT_PROGRAM_BRIDGE_RE = re.compile(
    r"^\s*(?:starts?|runs?|precedes?|follows?)\s*$", re.I
)
_PLAUSIBLE_PROGRAM_RE = re.compile(
    r"(?<![A-Za-z0-9_@#$-])[A-Z@#$][A-Z0-9_@#$]{0,9}"
    r"(?![A-Za-z0-9_@#$-])"
)


def strip_html_comments(markdown: str) -> str:
    return re.sub(r"<!--.*?-->", "", markdown, flags=re.S)


def _connector_reaches_core(text: str, index: int, step: int) -> bool:
    cursor = index
    while 0 <= cursor < len(text) and text[cursor] in EXACT_TOKEN_CONNECTORS:
        cursor += step
    return bool(
        0 <= cursor < len(text) and EXACT_TOKEN_CORE_RE.fullmatch(text[cursor])
    )


def _exact_occurrence(text: str, start: int, end: int) -> bool:
    before = start - 1
    after = end
    before_connected = bool(
        before >= 0
        and (
            EXACT_TOKEN_CORE_RE.fullmatch(text[before])
            or (
                text[before] in EXACT_TOKEN_CONNECTORS
                and _connector_reaches_core(text, before, -1)
            )
        )
    )
    after_connected = bool(
        after < len(text)
        and (
            EXACT_TOKEN_CORE_RE.fullmatch(text[after])
            or (
                text[after] in EXACT_TOKEN_CONNECTORS
                and _connector_reaches_core(text, after, 1)
            )
        )
    )
    return not before_connected and not after_connected


def exact_literal_present(
    text: str, literal: str, *, case_sensitive: bool = True
) -> bool:
    """Match an exact IBM/message token without accepting a larger identifier."""

    rendered_literal = _visible_inline_text(literal).strip()
    if not rendered_literal and literal.strip():
        rendered_literal = _strip_inline_wrappers(literal).strip()
    value = re.sub(r"\s+", " ", rendered_literal)
    if not value:
        return True
    haystack = re.sub(r"\s+", " ", _visible_inline_text(text))
    return any(
        _exact_occurrence(haystack, match.start(), match.end())
        for match in re.finditer(
            re.escape(value), haystack, 0 if case_sensitive else re.I
        )
    )


def _strip_inline_wrappers(text: str) -> str:
    """Normalize wrappers that do not change the rendered literal value."""

    visible = html.unescape(text)
    visible = re.sub(
        r"(?P<fence>`+)(?P<content>.*?)(?P=fence)",
        lambda match: match.group("content"),
        visible,
        flags=re.S,
    )
    emphasis = re.compile(
        r"(?<![A-Za-z0-9_])(?P<mark>\*{1,3}|_{1,3})(?=\S)"
        r"(?P<content>.+?)(?<=\S)(?P=mark)(?![A-Za-z0-9_])",
        re.S,
    )
    previous = None
    while previous != visible:
        previous = visible
        visible = emphasis.sub(lambda match: match.group("content"), visible)
    return visible


def _visible_inline_text(text: str) -> str:
    """Keep rendered inline text while discarding destinations and attributes."""

    code_spans: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        code_spans.append(match.group("content"))
        return f"\x00FLOWCODE{len(code_spans) - 1}\x00"

    visible = strip_html_comments(text)
    visible = re.sub(
        r"(?P<fence>`+)(?P<content>.*?)(?P=fence)",
        protect_code,
        visible,
        flags=re.S,
    )
    visible = strip_markdown_link_destinations(visible)
    visible = strip_html_tokens(visible)
    visible = html.unescape(visible)
    visible = re.sub(r"\\([\\`*{}\[\]()#+\-.!_|>~])", r"\1", visible)
    for index, code in enumerate(code_spans):
        visible = visible.replace(f"\x00FLOWCODE{index}\x00", code)
    return _strip_inline_wrappers(visible)


def forbidden_heading_findings(
    markdown: str, forbidden_names: Iterable[str]
) -> list[str]:
    """Reject forbidden full-flow names at any nested deliverable heading."""

    forbidden = {str(name).strip().casefold(): str(name) for name in forbidden_names}
    findings: list[str] = []
    heading_surface = "\n".join(
        _strip_commonmark_container_prefix(line) for line in markdown.splitlines()
    )
    candidates = [
        match.group(1)
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", heading_surface, re.M)
    ]
    candidates.extend(
        match.group(1)
        for match in re.finditer(
            r"^([^\n|]+?)\s*\n(?:=+|-+)\s*$",
            heading_surface,
            re.M,
        )
    )
    candidates.extend(
        match.group(1)
        for match in re.finditer(
            r"<h[1-6]\b[^>]*>(.*?)</h[1-6]\s*>", markdown, re.I | re.S
        )
    )
    for candidate in candidates:
        name = _rendered_heading_label(candidate)
        normalized = re.sub(
            r"^\s*(?:\d+(?:\.\d+)*[.)]?|[A-Za-z][.)])\s+",
            "",
            name,
        ).casefold()
        canonical = next(
            (
                original
                for phrase, original in sorted(
                    forbidden.items(), key=lambda item: len(item[0]), reverse=True
                )
                if re.search(
                    rf"(?<![\w]){re.escape(phrase)}(?![\w])", normalized
                )
            ),
            None,
        )
        if canonical:
            findings.append(
                f"program-set review contains forbidden full-flow section: {canonical}"
            )
    return findings


def _strip_commonmark_container_prefix(line: str) -> str:
    """Expose heading content nested in block quotes or list items."""

    surface = line
    prefix = re.compile(
        r"^[ ]{0,3}(?:>[ \t]?|(?:[-+*]|\d{1,9}[.)])[ \t]+)"
    )
    while True:
        match = prefix.match(surface)
        if not match:
            break
        surface = surface[match.end() :]
    return re.sub(r"^[ ]{0,3}", "", surface)


def _rendered_heading_label(value: str) -> str:
    label = _visible_inline_text(value)
    label = re.sub(r"\s*\{[^}]*\}\s*$", "", label)
    label = re.sub(r"^[*_~]+|[*_~]+$", "", label.strip())
    return re.sub(r"\s+", " ", label).strip()


def prohibited_decision_findings(markdown: str) -> list[str]:
    """Reject high-confidence outputs owned by later modernization workflows."""

    findings: list[str] = []
    visible = strip_html_comments(markdown)
    patterns = (
        (
            "modernization decision/recommendation",
            re.compile(
                r"\bmoderni[sz]ation\s+(?:decision|recommendation|proposal)\b",
                re.I,
            ),
        ),
        (
            "service boundary decision/recommendation",
            re.compile(
                r"\bservice\s+boundary\s+(?:decision|recommendation|proposal)\b",
                re.I,
            ),
        ),
        (
            "business rule output",
            re.compile(
                r"\bbusiness\s+rules?\b|\bBR-[A-Za-z0-9_@#$-]+\b",
                re.I,
            ),
        ),
        (
            "architecture decision/recommendation",
            re.compile(
                r"\barchitecture\s+(?:decision|recommendation|proposal)\b|"
                r"\barchitecture\s*[:—–-]",
                re.I,
            ),
        ),
    )
    migration = re.compile(
        r"\b(?:extract|rewrite|replace|migrate|moderni[sz]e|convert|carve|"
        r"create|split|move|become|recommend)\b.{0,100}"
        r"\b(?:microservice|cloud\s+service|service\s+boundary)\b",
        re.I,
    )
    negation = re.compile(
        r"\b(?:must|should|do|does|did|will|would|is|are|was|were|has|have)\s+not\b|"
        r"\bno\s+(?:plan|decision|recommendation|proposal|business\s+rules?)\b|"
        r"\bwithout\s+(?:recommending|creating|defining|inferring|proposing)\b|"
        r"\bout\s+of\s+scope\b|\bdoes\s+not\s+(?:define|recommend|infer)\b",
        re.I,
    )
    seen: set[str] = set()
    implementation = re.compile(
        r"\b(?:extract|rewrite|replace|migrate|moderni[sz]e|convert|carve|"
        r"create|split|move|become|recommend)\b",
        re.I,
    )
    boundary_term = re.compile(
        r"\b(?:microservice|cloud\s+service|service\s+boundar(?:y|ies))\b",
        re.I,
    )
    for raw_line in visible.splitlines():
        line_has_boundary = bool(boundary_term.search(raw_line))
        clauses = re.split(
            r"(?<=[.!?;])\s+|;\s*|[—–]|"
            r"\b(?:but|however|although|though|nevertheless|yet)\b|"
            r",\s*(?=(?:we\b|it\b|will\b|would\b|must\b|should\b|"
            r"convert\b|moderni[sz]e\b|migrate\b|carve\b|create\b|"
            r"split\b|move\b|recommend\b))",
            raw_line,
            flags=re.I,
        )
        clauses = [
            span
            for clause in clauses
            for span in re.split(
                r"\b(?:and|then)\b(?=\s+[^.!?;]{0,100}"
                r"(?:\b(?:recommend|migrate|moderni[sz]e|convert|carve|create|"
                r"split|move|become|should|must|will|would)\b|"
                r"\bBR-[A-Za-z0-9_@#$-]+\s*:))",
                clause,
                flags=re.I,
            )
        ]
        for clause in clauses:
            line = clause.strip()
            if not line:
                continue
            is_negated = bool(negation.search(line))
            for label, pattern in patterns:
                if pattern.search(line) and not is_negated and label not in seen:
                    findings.append(f"program-set review contains prohibited {label}")
                    seen.add(label)
            if migration.search(line) and not is_negated:
                label = "modernization implementation recommendation"
                if label not in seen:
                    findings.append(f"program-set review contains prohibited {label}")
                    seen.add(label)
            if re.search(
                r"\b(?:microservice|cloud\s+service|service\s+boundar(?:y|ies))\b",
                line,
                re.I,
            ) and not is_negated:
                label = "service boundary decision/recommendation"
                if label not in seen:
                    findings.append(f"program-set review contains prohibited {label}")
                    seen.add(label)
            if (
                line_has_boundary
                and implementation.search(line)
                and (boundary_term.search(line) or re.search(r"\b(?:one|it)\b", line, re.I))
                and not is_negated
            ):
                label = "service boundary decision/recommendation"
                if label not in seen:
                    findings.append(f"program-set review contains prohibited {label}")
                    seen.add(label)
    return findings


def _h2_block(markdown: str, section: str) -> str:
    match = re.search(rf"^##\s+{re.escape(section)}\s*$", markdown, re.M)
    if not match:
        return ""
    end = re.search(r"^##\s+.+$", markdown[match.end() :], re.M)
    stop = match.end() + end.start() if end else len(markdown)
    return markdown[match.start() : stop]


def _program_occurrences(
    text: str, programs: Iterable[str]
) -> list[tuple[int, int, str]]:
    positions: list[tuple[int, int, str]] = []
    for program in programs:
        token = str(program)
        for match in re.finditer(re.escape(token), text, re.I):
            if _exact_occurrence(text, match.start(), match.end()):
                positions.append((match.start(), match.end(), token))
    return sorted(positions)


def _program_mentions(text: str, programs: Iterable[str]) -> list[str]:
    return [program for _start, _end, program in _program_occurrences(text, programs)]


def _relation_bridge_present(text: str) -> bool:
    return bool(
        RELATION_INDICATOR_RE.search(text)
        or _DIRECT_PROGRAM_BRIDGE_RE.fullmatch(text)
    )


def _relation_program_candidates(
    claim: str, known_programs: Iterable[str]
) -> list[str]:
    """Add contextual IBM i program identifiers absent from the manifest."""

    candidates = list(
        dict.fromkeys(str(value) for value in known_programs if str(value).strip())
    )
    occurrences = [
        (match.start(), match.end(), match.group(0))
        for match in _PLAUSIBLE_PROGRAM_RE.finditer(claim)
        if match.group(0).upper() not in _RELATION_MATERIAL_STOP_WORDS
        and match.group(0).upper()
        not in {"ERROR", "FACT", "INPUT", "OUTPUT", "RESULT", "REVIEW", "ROUTINE"}
    ]
    for left_index, left in enumerate(occurrences):
        _left_start, left_end, left_value = left
        for right_index in range(left_index + 1, len(occurrences)):
            right_start, _right_end, right_value = occurrences[right_index]
            between = claim[left_end:right_start]
            if len(between) > 180:
                break
            if not _relation_bridge_present(between):
                continue
            for value in (left_value, right_value):
                if value not in candidates:
                    candidates.append(value)
            previous = occurrences[right_index]
            for continuation in occurrences[right_index + 1 :]:
                continuation_between = claim[previous[1] : continuation[0]]
                if not re.fullmatch(
                    r"\s*(?:,|;|&|and|or|and/or|as\s+well\s+as)+\s*",
                    continuation_between,
                    re.I,
                ):
                    break
                if continuation[2] not in candidates:
                    candidates.append(continuation[2])
                previous = continuation
            break
    return candidates


def _fact_segments(fact: dict[str, Any]) -> list[str]:
    program = str(fact.get("program") or "").strip()
    segments: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            text = re.sub(r"\s+", " ", value.strip())
            segments.append(
                text
                if not program or re.search(re.escape(program), text, re.I)
                else f"{program} {text}"
            )
        elif isinstance(value, dict):
            add(" ".join(str(item) for item in value.values() if str(item).strip()))
        elif isinstance(value, (list, tuple)):
            add(" ".join(str(item) for item in value if str(item).strip()))

    for key in (
        "source_text",
        "logic",
        "calculation",
        "description",
        "exception_path",
        "guard",
        "trigger_chain",
        "effect",
        "supporting_detail",
        "source_row",
        "source_cells",
    ):
        add(fact.get(key))
    return list(dict.fromkeys(segments))


def _relation_pairs(
    claim: str, known_programs: Iterable[str]
) -> list[tuple[str, str, str]]:
    programs = list(dict.fromkeys(str(value) for value in known_programs if str(value)))
    occurrences = _program_occurrences(claim, programs)
    pairs: list[tuple[str, str, str]] = []
    reverse_relation = re.compile(
        r"\b(?:called\s+by|invoked\s+by|triggered\s+by|launched\s+by|"
        r"delegated\s+by|routed\s+by|forwarded\s+by|"
        r"provided\s+by|delivered\s+by|"
        r"receives?(?:\s+.{0,80}?)?\s+from|"
        r"flows?\s+from|target\s+carrier\s+from|consumer(?:\s+of)?|"
        r"consumes?(?:\s+.{0,80}?)?(?:\s+(?:from|produced\s+by))?|"
        r"(?:uses?|reads?)(?:\s+.{0,80}?)?\s+from|produced\s+by)\b|"
        r"(?:<-{1,2}|<=|←|⇐)",
        re.I | re.S,
    )
    negative_relation = re.compile(
        r"\b(?:not|never|cannot|can't|doesn't|isn't|aren't|wasn't|weren't|no)\b",
        re.I,
    )
    last_source = ""
    last_target = ""
    last_polarity = "positive"
    for left, right in zip(occurrences, occurrences[1:]):
        _left_start, left_end, left_program = left
        right_start, _right_end, right_program = right
        if left_program == right_program:
            continue
        between = claim[left_end:right_start]
        if len(between) > 180:
            continue
        if _relation_bridge_present(between):
            directed_pair = (
                (right_program, left_program)
                if reverse_relation.search(between)
                else (left_program, right_program)
            )
            polarity = "negative" if negative_relation.search(between) else "positive"
            last_source, last_target = directed_pair
            last_polarity = polarity
        elif (
            last_source
            and left_program.casefold() == last_target.casefold()
            and re.fullmatch(
                r"\s*(?:,|;|&|and|or|and/or|as\s+well\s+as)+\s*",
                between,
                re.I,
            )
        ):
            directed_pair = (last_source, right_program)
            polarity = last_polarity
            last_target = right_program
        else:
            continue
        pair = (*directed_pair, polarity)
        if pair not in pairs:
            pairs.append(pair)
    return pairs


def _claim_has_relation(claim: str, known_programs: Iterable[str]) -> bool:
    return bool(
        RELATION_INDICATOR_RE.search(claim)
        or _relation_pairs(claim, known_programs)
    )


_RELATION_MATERIAL_STOP_WORDS = frozenset(
    {
        "A", "AN", "THE", "AND", "OR", "BOTH", "AS", "WELL", "TO", "FROM",
        "BY", "OF", "FOR", "WITH", "VIA", "THEN", "BEFORE", "AFTER", "IN",
        "THAT", "ORDER", "CALL", "CALLS", "CALLED", "INVOKE", "INVOKES",
        "INVOKED", "SEND", "SENDS", "SENT", "PASS", "PASSES", "RETURN",
        "RETURNS", "RECEIVE", "RECEIVES", "RECEIVED", "ROUTE", "ROUTES",
        "ROUTED", "FORWARD", "FORWARDS", "FORWARDED", "DELEGATE", "DELEGATES",
        "TRANSFER", "TRANSFERS", "DISPATCH", "DISPATCHES", "HANDOFF", "HAND",
        "OFF", "PRODUCE", "PRODUCES", "PRODUCED", "CONSUME", "CONSUMES",
        "CONSUMED", "FLOW", "FLOWS", "SOURCE", "TARGET", "CARRIER", "PROGRAM",
        "PROVIDE", "PROVIDES", "PROVIDED", "DELIVER", "DELIVERS", "DELIVERED",
        "COMMUNICATE", "COMMUNICATES", "EXCHANGE", "EXCHANGES", "DEPEND", "DEPENDS",
        "CONTINUE", "CONTINUES", "MAP", "MAPS", "POPULATE", "POPULATES",
        "CONNECT", "CONNECTS", "SUPPLY", "SUPPLIES", "YIELD", "YIELDS",
        "EMIT", "EMITS", "WRITE", "WRITES", "START", "STARTS", "RUN", "RUNS",
        "QUEUE", "QUEUES", "PUBLISH", "PUBLISHES", "REQUEST", "REQUESTS",
        "CHAIN", "CHAINS", "PRECEDE", "PRECEDES", "FOLLOW", "FOLLOWS",
        "PROGRAMS", "REQUEST", "RESPONSE", "STATUS", "MESSAGE", "SME", "IBM",
        "RPG", "SQL", "API", "UI", "DB", "IO", "MAIN", "RLOG", "SF", "NOT",
        "NO", "NEVER", "CANNOT", "CAN", "DOES", "IS", "ARE", "WAS", "WERE",
    }
)


def _material_relation_tokens(
    claim: str, known_programs: Iterable[str]
) -> list[str]:
    without_refs = SOURCE_FACT_RE.sub(" ", claim)
    programs = {str(value).casefold() for value in known_programs}
    tokens: list[str] = []
    for match in re.finditer(r"(?<![A-Za-z0-9_@#$-])[A-Z@#$][A-Z0-9_@#$-]+", without_refs):
        token = match.group(0)
        if token.casefold() in programs or token.upper() in _RELATION_MATERIAL_STOP_WORDS:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens


def relation_supported_by_single_fact(
    claim: str,
    refs: Iterable[str],
    fact_map: dict[str, dict[str, Any]],
    known_programs: Iterable[str],
) -> bool:
    """Require every claimed directional pair in one referenced source fact."""

    programs = list(known_programs)
    pairs = _relation_pairs(claim, programs)
    if not pairs:
        return False
    mentioned = {value.casefold() for value in _program_mentions(claim, programs)}
    covered = {
        value.casefold()
        for source, target, _polarity in pairs
        for value in (source, target)
    }
    if not mentioned.issubset(covered):
        return False
    material_tokens = _material_relation_tokens(claim, programs)
    for ref in refs:
        if ref not in fact_map:
            continue
        for segment in _fact_segments(fact_map[ref]):
            segment_pairs = _relation_pairs(segment, programs)
            if all(pair in segment_pairs for pair in pairs) and all(
                exact_literal_present(segment, token) for token in material_tokens
            ):
                return True
    return False


def _table_claim_units(
    block: str, known_programs: Iterable[str]
) -> list[tuple[str, list[str], bool]]:
    lines = block.splitlines()
    units: list[tuple[str, list[str], bool]] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (
            header_line.startswith("|")
            and header_line.endswith("|")
            and separator_line.startswith("|")
            and separator_line.endswith("|")
            and is_markdown_table_separator(separator_line)
        ):
            index += 1
            continue
        headers = [cell.strip() for cell in split_markdown_table_row(header_line)]
        separator_cells = split_markdown_table_row(separator_line)
        if len(separator_cells) != len(headers):
            index += 2
            while index < len(lines):
                malformed_row = lines[index].strip()
                if not (
                    malformed_row.startswith("|")
                    and malformed_row.endswith("|")
                ):
                    break
                malformed_programs = _relation_program_candidates(
                    malformed_row, known_programs
                )
                if _claim_has_relation(malformed_row, malformed_programs):
                    units.append(
                        (
                            malformed_row,
                            SOURCE_FACT_RE.findall(
                                _visible_inline_text(malformed_row)
                            ),
                            False,
                        )
                    )
                index += 1
            continue
        normalized = [header.casefold() for header in headers]
        index += 2
        while index < len(lines):
            row_line = lines[index].strip()
            if not (row_line.startswith("|") and row_line.endswith("|")):
                break
            cells = [cell.strip() for cell in split_markdown_table_row(row_line)]
            if len(cells) > len(headers):
                combined_claim = " ".join(cells)
                combined_programs = _relation_program_candidates(
                    combined_claim, known_programs
                )
                if _claim_has_relation(combined_claim, combined_programs):
                    units.append(
                        (
                            combined_claim,
                            SOURCE_FACT_RE.findall(_visible_inline_text(row_line)),
                            False,
                        )
                    )
            cells.extend([""] * max(0, len(headers) - len(cells)))
            refs = SOURCE_FACT_RE.findall(_visible_inline_text(row_line))
            subject = ""
            if "program" in normalized:
                subject = cells[normalized.index("program")]
            overview_programs = ""
            if "programs / main routines" in normalized:
                overview_programs = cells[normalized.index("programs / main routines")]
            requires_explicit_pair = (
                len(_program_mentions(overview_programs, known_programs)) >= 2
            )
            excluded_headers = {
                "program",
                "routine",
                "program / routine sources",
                "programs / main routines",
                "review row id",
                "source fact refs",
            }
            for header, cell in zip(normalized, cells):
                if header in excluded_headers:
                    continue
                claim = cell
                if len(_program_mentions(claim, subject.split())) < 1 and subject:
                    claim = f"{subject} {claim}"
                claim_programs = _relation_program_candidates(claim, known_programs)
                if not _claim_has_relation(claim, claim_programs):
                    continue
                units.append((claim, refs, requires_explicit_pair))
            index += 1
    return units


def _prose_claim_units(block: str) -> list[tuple[str, list[str], bool]]:
    prose_lines: list[str] = []
    for line in block.splitlines():
        stripped = line.lstrip()
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", stripped)
        if heading:
            prose_lines.extend((_rendered_heading_label(heading.group(1)), ""))
        elif not stripped.startswith("|"):
            prose_lines.append(line)
    prose = "\n".join(prose_lines)
    return [
        (
            re.sub(r"\s+", " ", paragraph).strip(),
            SOURCE_FACT_RE.findall(_visible_inline_text(paragraph)),
            False,
        )
        for paragraph in re.split(r"\n\s*\n", prose)
        if paragraph.strip()
    ]


def cross_program_relation_findings(
    markdown: str,
    fact_map: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> list[str]:
    """Validate relation/sequence claims in every reader-first review section."""

    known_programs = list(
        dict.fromkeys(
            str(entry.get("normalized_name") or "")
            for entry in manifest.get("programs", []) or []
            if entry.get("normalized_name")
        )
    )
    findings: list[str] = []
    block = strip_html_comments(markdown)
    for claim, refs, requires_explicit_pair in (
        *_table_claim_units(block, known_programs),
        *_prose_claim_units(block),
    ):
        if not claim:
            continue
        claim_programs = _relation_program_candidates(claim, known_programs)
        if not _claim_has_relation(claim, claim_programs):
            continue
        claimed_pairs = _relation_pairs(claim, claim_programs)
        if not claimed_pairs:
            if requires_explicit_pair:
                findings.append(
                    "final review contains an unsupported cross-program "
                    "relation/sequence claim"
                )
            continue
        if not refs or not relation_supported_by_single_fact(
            claim, refs, fact_map, claim_programs
        ):
            findings.append(
                "final review contains an unsupported cross-program "
                "relation/sequence claim"
            )
    return findings
