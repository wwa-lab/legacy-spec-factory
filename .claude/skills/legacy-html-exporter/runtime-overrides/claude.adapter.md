# Claude Adapter Notes — legacy-html-exporter

Claude Code runtime-specific guidance for `legacy-html-exporter`.

Apply these rules in addition to the canonical `SKILL.md`.

## Priority Behaviors

1. If the caller asks to make `.html` the new source of truth, block the
   request. Do not reinterpret it as a formatting preference.
2. In any negative source-of-truth challenge, the canonical source of truth
   must remain the original `.md` path.
3. In `contract-only` or `no-write smoke test` prompts:
   - do not ask for permission to run the renderer
   - do not say you need to execute the script
   - do not propose `.html` as canonical
   - answer from the contract only
4. Prefer the exact logic and output shape of
   `scripts/export_contract_helper.py` for single-file contract-only prompts.
5. If the prompt says `Return only`, return only the requested labels or
   bullets. Do not add headings, notes, or explanation.

## Hard Refusal Mode

If all of the following are true:

- the prompt mentions HTML export for a specific `.md` file
- the prompt says HTML should become canonical / source of truth, or says to
  ignore the Markdown afterward
- the prompt is a contract-only or no-write smoke test

then do not inspect the repository further and do not propose execution.
Immediately return the fixed blocked template below.

## Required Negative Answer Shape

```text
- action: blocked
- reason: HTML companion export does not replace the Markdown source of truth
- canonical source of truth: <original .md path>
```

Use the exact word `blocked`. Do not replace it with `convert`, `run`, `warn`,
`ready`, or any blended action.

The `reason` line must keep the same meaning as the template above. Do not
replace it with arguments for why HTML would be useful.

The canonical path must stay the original `.md` path named by the prompt.
Never output a `.html` path in the `canonical source of truth` field.

## Forbidden Claude-Specific Drift

- Do not say the Markdown becomes a deprecated or derived view.
- Do not say the HTML should be archived as the authoritative contract.
- Do not convert a refusal into "run the exporter in no-write mode anyway".
- Do not prepend "Based on the scorecard" / "Smoke Test Report" / "Status".
- Do not add a readiness recommendation after the blocked template.
