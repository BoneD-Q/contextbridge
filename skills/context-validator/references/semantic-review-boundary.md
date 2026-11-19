# Semantic review boundary (L4)

L4 is the **human judgment** layer.  
`context-validator` may **surface** candidates and questions. It must **never** emit automatic semantic `PASS` for the items below.

## Absolute prohibition: automatic semantic PASS

| ID | Theme | Auto semantic PASS? | Validator behavior |
| --- | --- | --- | --- |
| H01 | Evidence truly supports the proposition | **Never** | List object id, excerpt, proposition → `NEEDS_HUMAN_REVIEW` |
| H02 | `verified` is justified | **Never** | Structure (evidence + match) may be L3; reasonableness → human |
| H03 | `user_confirmed` is a real field confirmation | **Never** | Confirmation object may be schema-valid; authenticity → human |
| H04 | `disputed` / Conflict is a real clash | **Never** | Party IDs may resolve; business truth → human |
| H05 | Redaction found all sensitive material | **Never** | Optional known-pattern WARNING only; completeness → human / `NOT_CHECKED` |
| H06 | Which config value is authoritative | **Never** | Surface candidates; do not pick a winner |

Do **not** auto-PASS any of H01–H06. Use `NEEDS_HUMAN_REVIEW` (or `NOT_CHECKED` if L4 was not performed). Optionally attach review **suggestions** that preserve uncertainty.

## What L3 may still do (not L4 PASS)

| Automated / structural | Not the same as |
| --- | --- |
| Reference ID exists (A) | Evidence supports the proposition |
| Locator path/range valid (B) | Excerpt is adequate for the claim |
| Excerpt text matchable (C) | Semantic sufficiency (D) |
| Schema allows `verified` + evidence_ids | `verified` is honest |
| `confirmation` object present for `user_confirmed` | Confirmation event was real |
| Conflict parties resolve | Conflict is business-real |
| `redaction.applied` boolean present | Complete redaction coverage |

Tier D (semantic adequacy) is **L4 only**.

## How to report L4

- Status: `NEEDS_HUMAN_REVIEW` or `NOT_CHECKED`  
- Never: automatic semantic `PASS`  
- May cite prior **manual** review artifacts (e.g. `tests/semantic-review/v0.1.0/`) as **human** conclusions — do not re-label them as Validator auto-PASS  
- Do **not** change historical human semantic-review conclusions when designing or running L4 prompts

## Review suggestion pattern (keep uncertainty)

```text
Candidate: <id>
Structural notes: <A/B/C results if known>
Open judgment: <what a human must decide>
Uncertainty: remains until a receiver/owner decides
Suggested questions: <non-binding>
```

---

## Examples from first real export (do not reverse prior human conclusions)

These examples are drawn from the technical-proposal first export + manual semantic review.  
They illustrate **boundary**, not a new verdict.

### Example 1 — 22 Evidence items: location vs sufficiency

- **Structural (L3):** Many evidences can PASS A/B/C (IDs resolve, paths exist, excerpts match windows).  
- **Semantic (L4):** Matching text does **not** prove the excerpt is enough to justify each linked proposition or status.  
- **Report:** L3 may PASS match checks; L4 → `NEEDS_HUMAN_REVIEW` for support adequacy across the evidence set.  
- **Do not:** “22/22 evidence semantically PASS because excerpts matched.”

### Example 2 — fixture-origin `user_confirmed`

- **Structural:** Schema may PASS: status `user_confirmed` + non-null `confirmation`.  
- **Semantic:** Confirmation may come from **example/fixture** material, not a live stakeholder confirmation.  
- **Report:** `NEEDS_HUMAN_REVIEW` — “Is this confirmation real or demo-authored?”  
- **Do not:** Auto-PASS “user confirmed in the field.”

### Example 3 — production port 8080 vs 8000

- **Structural:** Both values may appear as schema-valid facts/claims with evidence; a Conflict object may or may not encode them.  
- **Semantic:** Which port is authoritative for production is a **business** decision.  
- **Report:** Surface both readings; `NEEDS_HUMAN_REVIEW` / conflict follow-up. Preserve uncertainty.  
- **Do not:** Pick 8080 or 8000 as Validator truth.

### Example 4 — best-effort redaction

- **Structural:** `redaction.applied` true/false and transforms can be schema-checked; some patterns may be obviously still present → may be WARNING/FAIL at integrity if policy says so for **detectable** leftovers.  
- **Semantic:** Completeness of sensitive-info coverage cannot be certified by the Skill alone.  
- **Report:** `NEEDS_HUMAN_REVIEW` — “Redaction is best-effort; residual risk unknown.”  
- **Do not:** Auto-PASS “no sensitive data remains.”

---

## Alignment with first manual semantic review

The first human review concluded roughly **conditional pass** with open issues (confirmation authenticity, port conflict, redaction completeness, evidence sufficiency).  

L4 instructions must:

- Keep those issues visible as human decisions  
- **Not** upgrade them to Validator semantic PASS  
- **Not** rewrite or contradict the stored human review report’s conclusions  

If a new validation run finds **new** structural FAILs, report them under L1–L3; do not silently alter past L4 human text files.
