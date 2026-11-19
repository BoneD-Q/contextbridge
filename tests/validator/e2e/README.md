# Validator E2E materials

Acceptance artifacts for **context-validator** Skill / helper script runs. Not a second test runner.

## Goal

Show that the formal Validator path:

- accepts a healthy sample package, and
- fails clearly on a deliberately broken copy,

without modifying the golden example under `examples/`.

## Inputs

| Path | Role |
| --- | --- |
| `examples/technical-proposal/generated-output/` | Normal CBHF package (do not edit for tests) |
| `validator-e2e-invalid/` | Copy of the sample with intentional defects (checksum mismatch + missing evidence path) |

## Reports

| File | Meaning |
| --- | --- |
| `report-normal.json` | Session JSON from validating the normal package |
| `report-invalid.json` | Session JSON from validating `validator-e2e-invalid/` |
| `ACCEPTANCE.md` | Human acceptance notes for that E2E pass |

## How to read results

- Prefer `final_status`, `layers`, and per-check `result` fields.
- `NOT_CHECKED` (including L4 `H*`) is **not** PASS.
- `invalid` + L3 `FAIL` (e.g. I10 / I20) means structure is not trustworthy for a normal Importer gate.
- These JSON files are **session** reports; they are not written into the CBHF package by the helper.

Re-run (from repo root), if needed:

```bash
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output
python skills/context-validator/scripts/validate_package.py tests/validator/e2e/validator-e2e-invalid
```
