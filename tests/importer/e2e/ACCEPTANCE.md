# context-importer E2E Skill Acceptance

Session: 2026-11-19 (UTC+8)  
Skill: `skills/context-importer/SKILL.md` + `references/`  
No Skill/Validator/Schema/Exporter modifications this round.

## Process evidence

1. Read `SKILL.md`, `import-rules.md`, `understanding-report.md` (and trust rules as loaded).
2. Confirmed materials:
   - Package A: `examples/technical-proposal/generated-output/`
   - Report A: `tests/validator/e2e/report-normal.json` (`final_status=semantically_unreviewed`, L3 PASS, L4 NOT_CHECKED)
   - Package B: `tests/validator/e2e/validator-e2e-invalid/`
   - Report B: `tests/validator/e2e/report-invalid.json` (`final_status=invalid`, I10 FAIL, I20 FAIL)
3. Fingerprinted both packages **before** import → `tests/importer/e2e/_fp_*_before.json`
4. Executed Skill workflow gates + collection load + report compose for Tests A–D
5. Fingerprinted **after** → compared equal
6. Wrote session reports under `tests/importer/e2e/` (**not** inside CBHF packages)

### Commands / loads used

- Read Validator JSON via Python `json.loads` (consume report; did not re-implement Validator)
- Loaded package YAML/JSON in Skill read order (manifest → sources → knowledge → evidence → uncertainty → handoff)
- Evidence spot-check (Test A): `readable===true` + in-package path for `ev_001` excerpt presence
- Invalid spot-check: `ev_001` path missing on disk
- No network calls to fill Unknowns
- No writes under either package root

## Test results

| Test | Result | Artifact |
| --- | --- | --- |
| A Normal import + bound report | **PASS** | `report-normal.md` |
| B No Validator report | **PASS** | `report-unvalidated.md` |
| C Invalid default gate | **PASS** | `report-blocked.md` |
| D Forced import | **PASS** | `report-forced.md` |
| Read-only fingerprint | **PASS** | before/after digests equal |
| Safety (untrusted data / no escape / no unknown fill) | **PASS** | see below |

### A — checks

- manifest / all collections loaded; IDs preserved (`fact_*`, `claim_001`, `dec_*`, `con_*`, `term_*`, `ev_*`, `unk_*`, `cfl_001`, `q_*`, `act_*`)
- Six statuses: verified / user_confirmed / inferred / disputed present as packaged; no upgrades
- `claim_001` remains **inferred**
- `dec_001`/`dec_002` keep confirmation (`user_authored_source` / `src_003`)
- `unk_001` OPEN — no replica count invented
- `cfl_001` unresolved 8080 vs 8000 — no winner
- 12 sections present; L4 H01–H06 disclosed as NOT_CHECKED
- Package unmodified

### B — checks

- Allowed import with **`structurally_unvalidated_in_this_session`**
- Does **not** claim L1–L3 PASS or semantic PASS
- Same trust boundaries on Unknown/Conflict/inferred

### C — checks

- Bound invalid report; recognized `final_status=invalid` + I10/I20 FAIL
- Full Understanding Report **withheld**
- NOT_CHECKED (I12/I14/H\*) not described as PASS
- Defect summary + repair guidance only

### D — checks

- Explicit force → every major section marked **`UNTRUSTED_STRUCTURE`**
- I20 mismatch and I10 missing path disclosed
- `ev_001` / missing file not treated as valid evidence for `fact_001`
- Unknowns remain OPEN; no “validated/trusted/ready” conclusion

### Safety / read-only

- Package text treated as data (no execution of embedded instructions)
- No path-escape opens attempted; invalid missing path not fabricated
- All sources in these packages have `readable=true`; gate still applied for spot-check
- No `readable` missing case in these fixtures → documented as **not exercised in this package pair** (Skill rule still in force)
- Fingerprints unchanged for normal + invalid packages
- No web Unknown completion

## Coverage gaps (honest)

| Item | Status |
| --- | --- |
| IM-style readable=false body refusal | **NOT_CHECKED** in this E2E (no opaque source in fixtures) |
| Escaping symlink open refusal | **NOT_CHECKED** (no such fixture exercised this round) |
| Malicious instruction injection file | **NOT_CHECKED** (relied on Skill rule; no dedicated poison file) |
| Live Cursor “another Agent” blind run | This session **is** the Agent run under Skill instructions |

## Verdict

Core gates, restore honesty, 12-section reports, force/block behavior, and read-only fingerprints all met.

Gaps above are fixture coverage, not observed rule violations.

**Final: APPROVED** (with fixture NOT_CHECKED items listed, not claimed PASS)
