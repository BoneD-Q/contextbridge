# Importer E2E materials

Acceptance artifacts for **context-importer** Skill runs (Agent-guided). Reports are saved **outside** CBHF packages.

## Goal

Verify the Importer workflow:

- restores ids/statuses without upgrading trust,
- applies validation gates (normal / unvalidated / blocked / forced),
- emits a Receiver Understanding Report in session form.

## Inputs

| Material | Role |
| --- | --- |
| `examples/technical-proposal/generated-output/` | Normal package |
| `../validator/e2e/report-normal.json` | Bound Validator session report for the normal package |
| `../validator/e2e/validator-e2e-invalid/` | Broken package |
| `../validator/e2e/report-invalid.json` | Bound Validator session report for the broken package |

## Reports in this folder

| File | Test |
| --- | --- |
| `report-normal.md` | A — normal import with Validator report |
| `report-unvalidated.md` | B — same package, **no** Validator report (`structurally_unvalidated_in_this_session`) |
| `report-blocked.md` | C — invalid package, default block (full report withheld) |
| `report-forced.md` | D — invalid package with explicit force (`UNTRUSTED_STRUCTURE`) |
| `ACCEPTANCE.md` | Overall pass/fail notes |

Fingerprint helpers (`_fp_*.json`) record read-only checks; they are not user-facing docs.

## How to read results

- Check the **gate banner** at the top of each Markdown report.
- Confirm Unknowns stay **OPEN** and Conflicts stay **unresolved** unless the package says otherwise.
- `NOT_CHECKED` must not be narrated as PASS.
- Forced reports must keep structural FAIL disclosures (e.g. I10 / I20).

These files are **not** CBHF protocol artifacts and must not be copied into `validation/` as a fake pass.
