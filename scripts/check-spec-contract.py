#!/usr/bin/env python3
"""Verify the spec schema guide and the spec template stay in sync.

Rules:
- Every name in `required_top_level_fields` must appear as a key in the
  schema's `spec:` block and as a top-level key in `templates/spec.yaml`.
- Every top-level key in `templates/spec.yaml` must appear in the schema's
  `spec:` block (either required or optional).
- Every name in `optional_top_level_fields` must appear in the `spec:` block.

Exit 0 on alignment, 1 on drift.

Standalone: only depends on PyYAML.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "PyYAML is required. Install with: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    schema_path = root / "schemas" / "spec.schema.yaml"
    template_path = root / "templates" / "spec.yaml"

    with schema_path.open() as f:
        schema = yaml.safe_load(f) or {}
    with template_path.open() as f:
        template = yaml.safe_load(f) or {}

    required = set(schema.get("required_top_level_fields") or [])
    optional = set(schema.get("optional_top_level_fields") or [])
    spec_block_keys = set((schema.get("spec") or {}).keys())
    template_keys = set(template.keys())

    errors: list[str] = []

    missing_required_in_spec_block = required - spec_block_keys
    if missing_required_in_spec_block:
        errors.append(
            "required_top_level_fields not defined under `spec:` block: "
            f"{sorted(missing_required_in_spec_block)}"
        )

    missing_optional_in_spec_block = optional - spec_block_keys
    if missing_optional_in_spec_block:
        errors.append(
            "optional_top_level_fields not defined under `spec:` block: "
            f"{sorted(missing_optional_in_spec_block)}"
        )

    missing_required_in_template = required - template_keys
    if missing_required_in_template:
        errors.append(
            "required_top_level_fields missing from templates/spec.yaml: "
            f"{sorted(missing_required_in_template)}"
        )

    extras_in_template = template_keys - spec_block_keys
    if extras_in_template:
        errors.append(
            "templates/spec.yaml has keys not declared in schema `spec:` block: "
            f"{sorted(extras_in_template)}"
        )

    overlap = required & optional
    if overlap:
        errors.append(
            "fields listed as both required and optional: "
            f"{sorted(overlap)}"
        )

    if errors:
        print("Spec contract drift detected:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        "OK: spec contract aligned "
        f"({len(required)} required, {len(optional)} optional, "
        f"{len(spec_block_keys)} defined in schema, "
        f"{len(template_keys)} in template)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
