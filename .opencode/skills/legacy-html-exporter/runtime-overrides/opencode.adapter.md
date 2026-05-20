# OpenCode Adapter Notes — legacy-html-exporter

OpenCode runtime-specific guidance for `legacy-html-exporter`.

Apply these rules in addition to the canonical `SKILL.md`.

## Priority Behaviors

1. Prefer the shortest contract-valid answer over exploratory reasoning.
2. In `contract-only` or `no-write smoke test` prompts:
   - do not scan large directory trees unless the prompt explicitly asks for a
     directory export
   - do not read the whole renderer unless required
   - prefer the exact logic and output shape of
     `scripts/export_contract_helper.py`
3. If the caller provides one Markdown file path, answer with the expected
   `.html` companion path immediately.
4. If the caller challenges the source-of-truth rule, block and keep the
   original `.md` path canonical.

## Required Positive Answer Shape

```text
- canonical source path: <path/to/file.md>
- generated HTML path: <path/to/file.html>
- whether Markdown remains canonical: yes
```

## Required Negative Answer Shape

```text
- action: blocked
- reason: HTML companion export does not replace the Markdown source of truth
- canonical source of truth: <original .md path>
```

## Forbidden OpenCode-Specific Drift

- Do not stall in long repository scanning for a single-file contract prompt.
- Do not upgrade `.html` above `.md`.
- Do not add extra commentary when the prompt says `Return only`.
