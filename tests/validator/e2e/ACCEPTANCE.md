# context-validator E2E Skill Acceptance

validated_at_session: 2026-11-19T11:02:12Z / 2026-11-19T11:02:13Z  
checker: context-validator Phase 3B-C2 via `skills/context-validator/SKILL.md`

## Skill process evidence

1. Read `skills/context-validator/SKILL.md`
2. Read `references/report-format.md` and `references/semantic-review-boundary.md` (partial)
3. Inspected normal package tree + `manifest.yaml` (`cbhf_version: 0.1.0`, `protocol: CBHF`)
4. Copied normal package to `tests/validator/e2e/validator-e2e-invalid/` (did not modify normal sample)
5. Applied Case A/B mutations on the copy only; Case C uses existing `unk_001`
6. Ran formal helper exactly as Skill specifies:

```text
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output
python skills/context-validator/scripts/validate_package.py tests/validator/e2e/validator-e2e-invalid
```

Session JSON saved to `report-normal.json` / `report-invalid.json`.

---

## Normal package report

1. **Package path:** `examples/technical-proposal/generated-output/` (label `generated-output`)
2. **Validator / how:** Skill `context-validator` → `scripts/validate_package.py` (session JSON stdout; no package write)
3. **Layers:** L1 `PASS` | L2 `PASS` | L3 `PASS` | L4 `NOT_CHECKED`
4. **Key checks:**
   - I20 `PASS` — all 4 applicable package_copy SHA-256 match
   - I11 `PASS` — locator paths package-safe
   - I10 `PASS` — all 22 safe locator.path files exist
   - I12/I14 `PASS` — line_range bounds + literal excerpt match
   - P07 `PASS` — digests unchanged (`read_only: true`)
5. **Not checked:** H01–H06 only — L4 semantic review not automated (`never auto semantic PASS`)
6. **L4:** `NOT_CHECKED` — not human-reviewed in this session; **not** a semantic PASS
7. **final_status:** `semantically_unreviewed`
8. **Issues / next steps:** Structural L1–L3 automated checks passed. Still need human L4 review before import/distribution claims of semantic adequacy. I20 PASS ≠ source authenticity.

### Case C (unknown retention) — normal package

From `uncertainty/unknowns.json`, **`unk_001`** remains unknown:

- Question: “What is the actual production replica count per PoP?”
- Notes: listed in open-questions.md; not answered in sources
- Agent interpretation: this item is still **unknown**; must **not** invent a replica count from common sense; must **not** promote to `verified` or `user_confirmed`

---

## Invalid package report

1. **Package path:** `tests/validator/e2e/validator-e2e-invalid/` (copy of normal; mutations only here)
2. **Validator / how:** same Skill command as above
3. **Layers:** L1 `PASS` | L2 `PASS` | L3 `FAIL` | L4 `NOT_CHECKED`
4. **Key failures / cascade:**
   - **Case A / I20 `FAIL`:** `src_001` checksum mismatch (`digest_mismatch`) after package-copy content tamper without checksum update; 3 other sources still match
   - **Case B / I10 `FAIL`:** `ev_001` locator.path `source/original/does-not-exist-e2e.md` missing (`report_file_missing`)
   - I11 `PASS` — path form still package-safe (relative, no escape); missing file is I10, not I11 FAIL
   - I12 `NOT_CHECKED` for `ev_001` — gated by `i10_missing` (not treated as valid evidence)
   - I14 `NOT_CHECKED` for `ev_001` — gated by `i12_not_checked`
5. **Not checked:** I12, I14 (dependency gates for missing path) + H01–H06 (L4)
6. **L4:** `NOT_CHECKED` — still no automated semantic PASS
7. **final_status:** `invalid`
8. **Issues / remediation:**
   - Restore or re-export `architecture-overview.md` and refresh `src_001.checksum`, **or** revert Case A tamper
   - Fix `ev_001.locator.path` to an existing package file (or remove/rebind evidence)
   - Keep `unk_001` as unknown until answered by an authoritative source; do not auto-fill

### Case C (unknown retention) — invalid package

Same `unk_001` present in the copy. Structural FAILs do **not** authorize inventing the replica count or converting the unknown into verified/user_confirmed knowledge.

---

## Honesty constraints applied

- PASS = only that specific automated rule passed
- NOT_CHECKED ≠ PASS and ≠ FAIL
- I20 PASS ≠ authenticity / truth of upstream sources
- L1–L3 PASS ≠ L4 semantic adequacy
- unknown stays unknown
- No invented evidence, confirmations, or test outcomes

## Acceptance verdict

See chat delivery for APPROVED / CONDITIONAL / REJECTED.
