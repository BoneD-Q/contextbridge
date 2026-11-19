# CBHF 0.1.0 Semantic Review Checklist

**Package:** `examples/technical-proposal/generated-output/`  
**Inputs:** `examples/technical-proposal/input/`  
**Expected guide:** `examples/technical-proposal/expected-output/EXPECTED.md`  
**Review type:** Manual semantic review — **not** `context-validator`  
**Date:** 2026-11-19  

## Scope

| Area | Artifact |
| --- | --- |
| Evidence adequacy | `evidence-review.csv` (22 rows) |
| Status accuracy | `status-review.csv` |
| Conflict | `conflict-review.md` |
| Redaction | section in `review-report.md` |
| Overall | `review-report.md` |

## Checklist

- [x] Read all input documents
- [x] Read generated package knowledge / evidence / uncertainty / handoff / manifest
- [x] Compare against EXPECTED.md (do not edit EXPECTED.md)
- [x] Locate every evidence excerpt in package copies
- [x] Judge whether excerpts support linked propositions
- [x] Review KnowledgeStatus for every knowledge object
- [x] Review confirmation objects for `user_confirmed`
- [x] Review conflict `cfl_001` (prod 8080 vs 8000)
- [x] Scan package for known plaintext secrets from input
- [x] Confirm input originals still contain drill secrets (untouched)
- [ ] Formal `context-validator` run — **NOT CHECKED** (out of scope)
- [ ] Exhaustive unknown-secret discovery — **NOT CHECKED** (best-effort only)
- [ ] Live chat confirmation authenticity beyond packaged fixture text — **NOT CHECKED**

## Result codes

`PASS` | `FAIL` | `NEEDS HUMAN DECISION` | `NOT CHECKED`
