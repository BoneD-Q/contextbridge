# Semantic review report — technical-proposal first export

**Package:** `examples/technical-proposal/generated-output/`  
**Reviewer role:** Manual CBHF 0.1.0 semantic review  
**Not equivalent to:** `context-validator` / `validation-report.json`  
**Date:** 2026-11-19  

Supporting artifacts:

- `review-checklist.md`
- `evidence-review.csv` (22/22)
- `status-review.csv`
- `conflict-review.md`

Deterministic assist (not semantic judgment): `_check_excerpts.py` confirmed every evidence excerpt line appears at the stated package-copy locator (0 missing lines).

---

## 1. Evidence adequacy

| Metric | Value |
| --- | --- |
| Evidence reviewed | 22 / 22 |
| Locatable in package copy | 22 |
| Faithful excerpts | 22 |
| Truly supports linked proposition | 22 (for current statuses) |
| Context gaps material enough to FAIL | 0 |

**Area result: PASS**

Notes:

- Adequacy judged against **linked proposition + status**, not mere ID/locator presence.
- `ev_011` is adequate for **`inferred`** claim_001 because the source labels the bottleneck sentence as interpretation; it would be inadequate as sole support for `verified`.
- `ev_005` / `fact_005`: statement is a narrowed subset of a longer sentence — still entailed; recorded as minor context narrowing, still PASS.
- No evidence row was accepted solely because an ID existed.

---

## 2. Status accuracy

| Status | Count in package | Review |
| --- | --- | --- |
| verified | 14 | All have adequate excerpts; none appear invented |
| user_confirmed | 2 | confirmation objects present; quotes match `src_003` |
| inferred | 1 | claim_001 notes + premises OK |
| disputed | 2 | fact_007 / fact_008 tied to true conflict |
| unverified | 0 | none present |
| unknown (on knowledge rows) | 0 | gaps correctly placed in `unknowns.json` |

**Area result: PASS**

No automatic status changes were applied. No suggested downgrades required for protocol compliance on this fixture.

Optional future polish (not FAIL): add `confirmation.limitations` noting fixture/meta origin of user-authored confirmations when exporting synthetic corpora.

---

## 3. Confirmation

| Object | Quote present | Matches source | Specific proposition | Result |
| --- | --- | --- | --- | --- |
| dec_001 | yes | yes (`We confirmed we will not ship…`) | no standalone Web UI | PASS |
| dec_002 | yes | yes (`就按文件夹交接…`) | folder handoff form | PASS |

`source_type` is `user_authored_source` with `source_ref: src_003` for both — allowed by claim-rules.

**Live session confirmation authenticity:** **NOT CHECKED** (these texts come from the synthetic decision-record fixture that instructs exporters to treat them as confirmation; they were not re-confirmed in a live chat during this review).

**Area result: PASS** (protocol / fixture).  
**Live-user authenticity beyond fixture:** **NOT CHECKED**.

---

## 4. Conflict

See `conflict-review.md`.

| Check | Result |
| --- | --- |
| Same subject | PASS |
| Same prod environment | PASS |
| Staging 8000 not wrongly included | PASS |
| Dual evidence | PASS |
| No auto-resolution | PASS |
| Which port is correct | NEEDS HUMAN DECISION |

**Area result: PASS** (conflict recording).  
**Resolution:** NEEDS HUMAN DECISION.

---

## 5. Redaction

| Check | Result |
| --- | --- |
| Known plaintext secrets from input absent in generated-output | PASS (scan: token / password / ReplaceMeToken) |
| Input originals still contain drill secrets (untouched) | PASS |
| Package copies show `[REDACTED:…]` | PASS |
| Evidence excerpts for knowledge do not require restored secrets | PASS |
| Redaction damaged verified support | PASS (no verified item depended on secret values) |
| Exhaustive discovery of all possible secrets/PII | NOT CHECKED (best-effort; manifest claims same) |
| Input secrets are fictional test values | PASS for corpus intent — input README states **synthetic/fictional**; architecture labels **redaction drills** / example. **NOT CHECKED** whether identical strings exist in other real systems outside this repo. |

**Area result: PASS** (for known drill secrets + package consistency).  
Do **not** claim all sensitive information was found.

---

## 6. Alignment with EXPECTED.md

Compared without modifying EXPECTED.md:

| EXPECTED expectation | Package | Match |
| --- | --- | --- |
| Exporter-required tree; no validation-report | present; no `validation/` | yes |
| Redaction of known secrets | applied | yes |
| Verified facts for admin/health/timeout/TLS/staging port | present | yes |
| Prod 8080 & 8000 disputed + conflict | present | yes |
| Staging vs prod not conflict | observed | yes |
| Inferred bottleneck claim | claim_001 | yes |
| user_confirmed folder handoff | dec_002 | yes |
| Unknowns (replicas / on-call / ff flag) | unk_001–003 | yes |
| Questions/actions pending | present | yes |

---

## 7. Minimal fix suggestions (optional; protocol unchanged)

1. Optionally set `confirmation.limitations` on fixture-sourced `user_confirmed` rows: e.g. “Confirmation text from packaged synthetic decision-record, not live session.”
2. When Validator exists: automate excerpt↔locator equivalence checks (already smoke-covered for this package).
3. Do not resolve `cfl_001` without user input.

No protocol field changes recommended from this review.

---

## 8. NOT CHECKED (explicit)

- Formal `context-validator` execution and `validation-report.json`
- Evidence adequacy under adversarial / incomplete OCR / unread binary scenarios (N/A here)
- Exhaustive secret/PII discovery beyond known drill strings
- Live chat confirmation independent of packaged fixture text
- Whether synthetic secret strings collide with real credentials elsewhere
- Full bilingual translation fidelity audit of every `i18n` string
- Semantic completeness of extraction (e.g. unused soak row “Handler time P99” intentionally omitted — not a defect)

---

## 9. Final conclusion

### 人工语义审查有条件通过

Conditions / caveats:

1. This review is **not** a formal Validator pass.
2. `user_confirmed` authenticity beyond the packaged synthetic decision-record was **NOT CHECKED**.
3. Secret discovery remains **best-effort**; only known drill secrets were verified absent from the package.
4. Production port authority remains **NEEDS HUMAN DECISION**.

Within those bounds: Evidence adequacy **PASS**, Status accuracy **PASS**, Confirmation (protocol) **PASS**, Conflict recording **PASS**, Redaction (known drills) **PASS**.
