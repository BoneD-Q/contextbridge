# Validator report format (session-level)

Defines how `context-validator` presents results.  
**Does not freeze** a `validation-report` JSON Schema in Phase 1.  
**Default:** session report only — **do not write** into the Package.

## Privacy

- Prefer basename or relative demo path for package identity.
- Avoid absolute home/user paths in shared reports unless the user requests them.
- Do not paste secrets from excerpts into the report; cite IDs and short reasons.

## Required report sections

1. **Package identity** — privacy-safe path / package_id if known  
2. **CBHF version** — from `manifest.cbhf_version` or unresolved  
3. **Validation time** — ISO-8601 UTC or local with offset  
4. **Checker capability declaration** — honest Phase / what was actually runnable  
5. **Layer summaries** — L1 / L2 / L3 / L4 rollups  
6. **Check detail** — one row/item per executed or intentionally skipped check  
7. **Error locations** — file + JSON path / line when known  
8. **Failure reasons** — factual, not invented  
9. **Warnings**  
10. **Not checked** — with reason (tool missing, dependency failed, out of scope)  
11. **Needs human review** — L4 and any borderline item  
12. **Final package verdict** — distinct from per-check status  

## Per-check status

| Status | Meaning |
| --- | --- |
| `PASS` | Check ran and succeeded |
| `FAIL` | Check ran and found a defect |
| `WARNING` | Check ran; non-blocking concern |
| `NOT_CHECKED` | Defined but not executed, or prerequisite missing |
| `NEEDS_HUMAN_REVIEW` | Requires judgment; **never** auto-promote to semantic PASS |

## Package final status (rollup; distinct from per-check)

Preferred package-level labels (design doc §6.2):

| Package status | When |
| --- | --- |
| `invalid` | Any hard L1/L2/L3 `FAIL` |
| `structurally_valid` | No L1–L3 `FAIL`; may still have warnings / not_checked / needs_human |
| `structurally_valid_with_warnings` | No `FAIL`, but one or more `WARNING` |
| `not_fully_validated` | Important L1–L3 checks were `NOT_CHECKED` (host limits) |
| `semantically_unreviewed` | Structure OK-ish, but L4 human review not completed |

Also allowed as a coarse session label: map `invalid`↔structural FAIL, keep L4 as `NEEDS_HUMAN_REVIEW` / `NOT_CHECKED` in the layer summary — **never** package-level “semantic PASS”.

**Do not** set final structural certainty solely because smoke or schema fixtures elsewhere passed.  
**Do not** treat per-check `PASS` as “full package validation complete”.

## Suggested markdown template

```markdown
# ContextBridge validation report

- package: <privacy-safe path>
- package_id: <id or unknown>
- cbhf_version: <version or unresolved>
- validated_at: <timestamp>
- checker: context-validator Phase 2 (L1+L2 scripts; L3/L4 not automated)

## Capability declaration

- L1–L2: automated via `scripts/validate_package.py`
- L3: rules defined; **not implemented** → NOT_CHECKED
- L4: boundary + human review only; **no automatic semantic PASS**
- Package mutation: none (read-only)

## Layer summary

| Layer | Result |
| --- | --- |
| L1 Package | PASS / FAIL / WARNING / NOT_CHECKED |
| L2 Schema | ... |
| L3 Integrity | ... |
| L4 Semantic boundary | NEEDS_HUMAN_REVIEW / NOT_CHECKED (never semantic PASS) |

## Check details

| ID | Status | Location | Reason |
| --- | --- | --- | --- |
| P01 | ... | ... | ... |

## Failures

- ...

## Warnings

- ...

## Not checked

- <id>: <why>

## Needs human review

- ...

## Final package status

`<invalid | structurally_valid | structurally_valid_with_warnings | not_fully_validated | semantically_unreviewed>`

### Notes

- This report was **not** written into the Package by default.
- Do not treat this as a forged completed validation if checks were skipped.
- L4 layer must not show automatic semantic PASS.
```

## Optional machine-readable sketch (not normative)

If the user asks for JSON in-session, a non-frozen sketch may look like:

```json
{
  "report_kind": "contextbridge-validation-session",
  "cbhf_version": "0.1.0",
  "package_id": null,
  "package_label": "generated-output",
  "validated_at": "2026-11-19T00:00:00Z",
  "checker": {
    "name": "context-validator",
    "phase": "2",
    "scripts_implemented": {
      "L1_package": true,
      "L2_schema": true,
      "L3_integrity": false,
      "L4_semantic": false
    },
    "network": false
  },
  "layers": {
    "L1": "PASS",
    "L2": "PASS",
    "L3": "NOT_CHECKED",
    "L4": "NOT_CHECKED"
  },
  "checks": [],
  "final_status": "not_fully_validated",
  "wrote_to_package": false
}
```

Do not invent pass/fail rows for checks that were not run.

## Writing into Package (deferred)

Writing `validation/` or flipping `manifest.validation.present` is **out of Phase 1 default**.  
If a future phase writes reports, it must still keep knowledge/evidence/source copies immutable and must not forge results.
