#!/usr/bin/env python3
# Legacy Spec Factory
# Copyright 2026 Leo L Zhang
#
# Original author: Leo L Zhang
# License: Apache License 2.0

"""Shared Markdown structure helpers for reader-first evidence contracts."""

from __future__ import annotations

import re
from collections.abc import Iterable


_TAG_NAME_RE = re.compile(r"^<\s*(?P<closing>/)?\s*(?P<name>[A-Za-z][\w:-]*)", re.S)
_HIDDEN_TAGS = frozenset({"template", "style", "script"})
_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


def _blank_character(character: str) -> str:
    return character if character in "\r\n" else " "


def _blank_range(characters: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        characters[index] = _blank_character(characters[index])


def _html_tag_end(text: str, start: int) -> int | None:
    quote = ""
    index = start + 1
    while index < len(text):
        character = text[index]
        if quote:
            if character == quote:
                quote = ""
        elif character in {'"', "'"}:
            quote = character
        elif character == ">":
            return index + 1
        index += 1
    return None


def _balanced_markdown_end(
    text: str, start: int, opener: str, closer: str
) -> int | None:
    depth = 1
    quote = ""
    index = start
    while index < len(text):
        character = text[index]
        if character == "\\" and index + 1 < len(text):
            index += 2
            continue
        if quote:
            if character == quote:
                quote = ""
        elif opener == "(" and character in {'"', "'"}:
            quote = character
        elif character == opener:
            depth += 1
        elif character == closer:
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return None


def strip_markdown_link_destinations(text: str) -> str:
    """Retain rendered labels while dropping balanced inline/reference targets."""

    result: list[str] = []
    index = 0
    while index < len(text):
        is_image = text[index : index + 2] == "!["
        label_open = index + 1 if is_image else index
        if label_open >= len(text) or text[label_open] != "[":
            result.append(text[index])
            index += 1
            continue
        label_end = _balanced_markdown_end(text, label_open + 1, "[", "]")
        if label_end is None:
            result.append(text[index])
            index += 1
            continue
        target_end: int | None = None
        if label_end < len(text) and text[label_end] == "(":
            target_end = _balanced_markdown_end(text, label_end + 1, "(", ")")
        elif label_end < len(text) and text[label_end] == "[":
            target_end = _balanced_markdown_end(text, label_end + 1, "[", "]")
        if target_end is None:
            result.append(text[index])
            index += 1
            continue
        if not is_image:
            result.append(text[label_open + 1 : label_end - 1])
        index = target_end
    return "".join(result)


def strip_html_tokens(text: str) -> str:
    """Drop tag/autolink bytes without exposing quoted attributes."""

    result: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "<":
            result.append(text[index])
            index += 1
            continue
        end = _html_tag_end(text, index)
        if end is None:
            result.append(text[index])
            index += 1
            continue
        token = text[index:end]
        if not re.match(
            r"^</?[A-Za-z][\w:-]*(?:\s|/?>)|^<(?:https?://|mailto:)",
            token,
            re.I,
        ):
            result.append(text[index])
            index += 1
            continue
        result.append(" ")
        index = end
    return "".join(result)


def _tag_details(token: str) -> tuple[str, bool, bool] | None:
    match = _TAG_NAME_RE.match(token)
    if not match:
        return None
    name = match.group("name").casefold()
    return (
        name,
        bool(match.group("closing")),
        token.rstrip().endswith("/>") or name in _VOID_TAGS,
    )


def _html_attributes(token: str) -> list[tuple[str, str]]:
    match = _TAG_NAME_RE.match(token)
    if not match:
        return []
    attributes: list[tuple[str, str]] = []
    index = match.end()
    while index < len(token):
        while index < len(token) and token[index].isspace():
            index += 1
        if index >= len(token) or token[index] == ">" or token.startswith("/>", index):
            break
        name_start = index
        while (
            index < len(token)
            and not token[index].isspace()
            and token[index] not in {"=", "/", ">", '"', "'"}
        ):
            index += 1
        attribute_name = token[name_start:index].casefold()
        if not attribute_name:
            index += 1
            continue
        while index < len(token) and token[index].isspace():
            index += 1
        value = ""
        if index < len(token) and token[index] == "=":
            index += 1
            while index < len(token) and token[index].isspace():
                index += 1
            if index < len(token) and token[index] in {'"', "'"}:
                quote = token[index]
                index += 1
                value_start = index
                while index < len(token) and token[index] != quote:
                    index += 1
                value = token[value_start:index]
                if index < len(token):
                    index += 1
            else:
                value_start = index
                while (
                    index < len(token)
                    and not token[index].isspace()
                    and token[index] not in "/>"
                ):
                    index += 1
                value = token[value_start:index]
        attributes.append((attribute_name, value))
    return attributes


def _starts_hidden_container(name: str, token: str) -> bool:
    if name in _HIDDEN_TAGS:
        return True
    attributes = _html_attributes(token)
    if any(attribute_name == "hidden" for attribute_name, _value in attributes):
        return True
    return any(
        attribute_name == "style"
        and re.search(
            r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", value, re.I
        )
        for attribute_name, value in attributes
    )


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _commonmark_container_surface(line: str) -> str:
    surface = line
    prefix = re.compile(
        r"^[ ]{0,3}(?:>[ \t]?|(?:[-+*]|\d{1,9}[.)])[ \t]+)"
    )
    while True:
        match = prefix.match(surface)
        if not match:
            return surface
        surface = surface[match.end() :]


def _markdown_code_positions(markdown: str) -> list[bool]:
    """Mark fenced, indented, and balanced inline-code source positions."""

    protected = [False] * len(markdown)
    fence_character = ""
    fence_length = 0
    offset = 0
    for line in markdown.splitlines(keepends=True):
        line_end = offset + len(line)
        surface = _commonmark_container_surface(line)
        if fence_character:
            protected[offset:line_end] = [True] * len(line)
            closing = re.match(
                r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*(?:\r?\n)?$", surface
            )
            if (
                closing
                and closing.group(1)[0] == fence_character
                and len(closing.group(1)) >= fence_length
            ):
                fence_character = ""
                fence_length = 0
        else:
            opening = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", surface)
            if opening:
                fence_character = opening.group(1)[0]
                fence_length = len(opening.group(1))
                protected[offset:line_end] = [True] * len(line)
            elif _indentation_columns(surface) >= 4:
                protected[offset:line_end] = [True] * len(line)
        offset = line_end

    index = 0
    while index < len(markdown):
        if protected[index] or markdown[index] != "`" or _is_escaped(markdown, index):
            index += 1
            continue
        stop = index
        while stop < len(markdown) and markdown[stop] == "`":
            stop += 1
        run_length = stop - index
        closing_re = re.compile(rf"(?<!`)`{{{run_length}}}(?!`)")
        closing = closing_re.search(markdown, stop)
        while closing and any(protected[stop : closing.end()]):
            closing = closing_re.search(markdown, closing.end())
        if closing is None:
            index = stop
            continue
        end = closing.end()
        protected[index:end] = [True] * (end - index)
        index = end
    return protected


def mask_hidden_html(markdown: str) -> str:
    """Blank non-rendered HTML while preserving character and line positions."""

    characters = list(markdown)
    code_positions = _markdown_code_positions(markdown)
    hidden_tag = ""
    hidden_depth = 0
    index = 0
    while index < len(markdown):
        if code_positions[index] and not hidden_tag:
            index += 1
            continue
        if markdown.startswith("<!--", index):
            stop = markdown.find("-->", index + 4)
            end = len(markdown) if stop < 0 else stop + 3
            _blank_range(characters, index, end)
            index = end
            continue
        if markdown[index] == "<":
            end = _html_tag_end(markdown, index)
            if end is not None:
                token = markdown[index:end]
                details = _tag_details(token)
                if hidden_tag:
                    _blank_range(characters, index, end)
                    if details and details[0] == hidden_tag:
                        _name, closing, self_closing = details
                        if closing:
                            hidden_depth -= 1
                        elif not self_closing:
                            hidden_depth += 1
                        if hidden_depth <= 0:
                            hidden_tag = ""
                            hidden_depth = 0
                    index = end
                    continue
                if details:
                    name, closing, self_closing = details
                    if not closing and _starts_hidden_container(name, token):
                        _blank_range(characters, index, end)
                        if not self_closing:
                            hidden_tag = name
                            hidden_depth = 1
                        index = end
                        continue
                index = end
                continue
        if hidden_tag:
            characters[index] = _blank_character(characters[index])
        index += 1
    return "".join(characters)


def _indentation_columns(line: str) -> int:
    columns = 0
    for character in line:
        if character == " ":
            columns += 1
        elif character == "\t":
            columns += 4 - (columns % 4)
        else:
            break
    return columns


def _blank_line(line: str) -> str:
    return "".join(_blank_character(character) for character in line)


def structured_markdown_surface(markdown: str) -> str:
    """Return visible Markdown with fenced/indented code made non-structural."""

    visible = mask_hidden_html(markdown)
    result: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in visible.splitlines(keepends=True):
        surface = _commonmark_container_surface(line)
        if fence_character:
            closing = re.match(
                r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*(?:\r?\n)?$", surface
            )
            if (
                closing
                and closing.group(1)[0] == fence_character
                and len(closing.group(1)) >= fence_length
            ):
                fence_character = ""
                fence_length = 0
            result.append(_blank_line(line))
            continue
        opening = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", surface)
        if opening:
            fence_character = opening.group(1)[0]
            fence_length = len(opening.group(1))
            result.append(_blank_line(line))
        elif _indentation_columns(surface) >= 4:
            result.append(_blank_line(line))
        else:
            result.append(line)
    return "".join(result)


def reader_section_blocks(
    markdown: str, section_names: Iterable[str]
) -> dict[str, str]:
    """Extract real H2 blocks while retaining their original lossless bytes."""

    names = {str(name): str(name) for name in section_names}
    raw_lines = markdown.splitlines(keepends=True)
    structural_lines = structured_markdown_surface(markdown).splitlines(keepends=True)
    blocks: dict[str, list[str]] = {name: [] for name in names}
    current = ""
    for raw_line, structural_line in zip(raw_lines, structural_lines):
        heading = re.match(
            r"^[ ]{0,3}##(?!#)\s+(.+?)\s*#*\s*(?:\r?\n)?$",
            structural_line,
        )
        if heading:
            label = heading.group(1).strip()
            current = names.get(label, "")
        if current:
            blocks[current].append(raw_line)
    return {
        name: "".join(lines).strip()
        for name, lines in blocks.items()
    }


def _has_matching_backtick_run(text: str, start: int, length: int) -> bool:
    pattern = re.compile(rf"(?<!`)`{{{length}}}(?!`)")
    return pattern.search(text, start) is not None


def _has_balanced_link_destination(text: str, start: int) -> bool:
    depth = 1
    index = start
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            index += 2
            continue
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return True
        index += 1
    return False


def split_markdown_table_row(line: str) -> list[str]:
    """Split only unescaped pipes outside balanced inline-code spans."""

    text = line.strip()
    cells: list[str] = []
    current: list[str] = []
    code_run_length = 0
    link_destination_depth = 0
    index = 0
    while index < len(text):
        character = text[index]
        if character == "`":
            stop = index
            while stop < len(text) and text[stop] == "`":
                stop += 1
            run_length = stop - index
            current.append(text[index:stop])
            if code_run_length == run_length:
                code_run_length = 0
            elif not code_run_length and _has_matching_backtick_run(
                text, stop, run_length
            ):
                code_run_length = run_length
            index = stop
            continue
        if not code_run_length and character == "\\" and index + 1 < len(text):
            current.extend((character, text[index + 1]))
            index += 2
            continue
        if not code_run_length:
            if (
                not link_destination_depth
                and character == "("
                and index > 0
                and text[index - 1] == "]"
                and _has_balanced_link_destination(text, index + 1)
            ):
                link_destination_depth = 1
            elif link_destination_depth and character == "(":
                link_destination_depth += 1
            elif link_destination_depth and character == ")":
                link_destination_depth -= 1
        if not code_run_length and not link_destination_depth and character == "|":
            cells.append("".join(current))
            current = []
        else:
            current.append(character)
        index += 1
    cells.append("".join(current))
    if cells and not cells[0]:
        cells = cells[1:]
    if cells and not cells[-1]:
        cells = cells[:-1]
    return cells


def is_markdown_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in split_markdown_table_row(line)]
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells
    )
