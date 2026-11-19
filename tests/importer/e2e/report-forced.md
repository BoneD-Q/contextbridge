# UNTRUSTED_STRUCTURE — Receiver Understanding Report

> Gate: **UNTRUSTED_STRUCTURE** (explicit force import authorized by acceptance Test D)
> package: `validator-e2e-invalid`
> package_id: `pkg_northwind_edge_gateway_proposal`
> cbhf_version: `0.1.0`
> importer: context-importer 0.1.0 (session report; package not modified)
> Validator: `tests/validator/e2e/report-invalid.json` bound → `final_status=invalid`

**This is not a normal, trusted, or structurally verified import.**

## UNTRUSTED_STRUCTURE — 1. Package identity

- Path: `tests/validator/e2e/validator-e2e-invalid/`
- Same package_id/title as the technical-proposal sample; **tree has known defects**
- Validator: L1=PASS, L2=PASS, L3=**FAIL**, L4=**NOT_CHECKED**
- **Structural defects (must disclose):**
  - **I20 FAIL:** `src_001` `digest_mismatch` (package copy bytes changed; checksum not updated)
  - **I10 FAIL:** `ev_001` path `source/original/does-not-exist-e2e.md` missing
- Cascades: I12/I14 **NOT_CHECKED** for `ev_001` (≠ PASS)
- H01–H06 **NOT_CHECKED** (≠ PASS); no semantic PASS

## UNTRUSTED_STRUCTURE — 2. Background and goals

*(Narrative only; structure untrusted.)*

Package still presents Northwind Edge Gateway handoff intent from overview/receiver-guide. Because of FAIL checks, treat all restored knowledge as **provisional under broken structure**.

## UNTRUSTED_STRUCTURE — 3. Known facts (by status)

Statuses below are **package labels**, not a clean Validator endorsement.

### verified (package label; tree untrusted)

- `fact_002` … `fact_006`, `fact_009`, `fact_010` — evidence ids retained from package JSON.
- **`fact_001`:** packaged as verified with `ev_001`, but **`ev_001` locator file is missing** → evidence **cannot be used as valid support** in this import. Do not treat `fact_001` as structurally backed in this tree.

### disputed

- `fact_007` / `fact_008` → `cfl_001` (8080 vs 8000) still open

### user_confirmed / inferred / unverified / unknown (facts)

- none recorded on facts

## UNTRUSTED_STRUCTURE — 4. Claims and evidence

- `claim_001` **[inferred]**: bottleneck is upstream connection pool, not CPU (`ev_009`, `ev_010`, `ev_011`).
- Remains **inferred** — not upgraded to verified.
- Note: soak-related evidence paths still present; still under UNTRUSTED_STRUCTURE because package integrity failed elsewhere (I20 on `src_001`).

## UNTRUSTED_STRUCTURE — 5. Decisions

- `dec_001` / `dec_002` **[user_confirmed]** with confirmation objects (`user_authored_source` / `src_003`) — objects preserved, **not forged**; authenticity still L4 / human under untrusted structure.
- `dec_003` **[verified]** label as packaged (`ev_016`)

## UNTRUSTED_STRUCTURE — 6. Constraints and boundaries

- `con_001`, `con_002`, `con_003` as packaged — provisional only

## UNTRUSTED_STRUCTURE — 7. Glossary

- `term_001` PoP · `term_002` Origin pool — packaged labels only

## UNTRUSTED_STRUCTURE — 8. Unknowns

- `unk_001` **OPEN — DO NOT FILL**: production replica count per PoP (still unknown; not invented)
- `unk_002` **OPEN — DO NOT FILL**: on-call owner
- `unk_003` **OPEN — DO NOT FILL**: `ff_http3_preview` prod ship state

## UNTRUSTED_STRUCTURE — 9. Conflicts

- `cfl_001` **unresolved**: `fact_007` stance 8080 vs `fact_008` stance 8000 — **no auto winner**

## UNTRUSTED_STRUCTURE — 10. Open questions

- `q_001` [high]: authoritative production listen port
- `q_002` [high]: replica count + on-call

## UNTRUSTED_STRUCTURE — 11. Suggested next actions

- Prefer repairing I20/I10 before acting on package content.
- Packaged `act_001` / `act_002` remain **pending** (not completed by Importer)

## UNTRUSTED_STRUCTURE — 12. Receiver limitations

- Forced import of **invalid** package — not “validated”, not “trusted”, not “ready”.
- I20 checksum mismatch and I10 missing evidence path are **not** concealed.
- Missing `ev_001` file ⇒ not usable as valid evidence for `fact_001`.
- NOT_CHECKED items are incomplete — **not** PASS.
- L4 not done; no semantic PASS.
- Unknowns remain OPEN; Conflict unresolved.
- Package not modified by Importer; no network Unknown fill.
- After repair, re-validate and re-import without force for a normal gate.
