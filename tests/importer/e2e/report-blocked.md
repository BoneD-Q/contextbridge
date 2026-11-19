# Import blocked — fix structure first

> Gate: **blocked** (default; no force)
> package: `validator-e2e-invalid`
> package_id: `pkg_northwind_edge_gateway_proposal`
> cbhf_version: `0.1.0`
> importer: context-importer 0.1.0
> Validator session report: `tests/validator/e2e/report-invalid.json` (**bound**)

## Binding

- Report `package_id`: `pkg_northwind_edge_gateway_proposal` matches manifest.
- Report `package_label`: `validator-e2e-invalid` matches directory basename.
- Bound: **yes** (not `validation_report_unbound`)

## Gate decision

- Validator `final_status`: **`invalid`**
- Layers: L1=PASS, L2=PASS, L3=**FAIL**, L4=**NOT_CHECKED**
- L1–L3 FAIL checks:
  - **I20 FAIL** — `src_001` checksum mismatch (`digest_mismatch`) after package-copy tamper without checksum update; message includes 1 mismatch, 3 match.
  - **I10 FAIL** — `ev_001` locator.path missing: `source/original/does-not-exist-e2e.md` (`report_file_missing`)
- Related (not FAIL, not PASS success stories):
  - I11 PASS (path form still package-safe)
  - I12 **NOT_CHECKED** for `ev_001` (`i10_missing`) — **≠ PASS**
  - I14 **NOT_CHECKED** for `ev_001` (`i12_not_checked`) — **≠ PASS**
  - H01–H06 **NOT_CHECKED** — **≠ PASS**; L4 not done

## Full Receiver Understanding Report

**Withheld.** Default gate blocks complete takeover / construction-ready restore.

Do **not** treat this stub as a successful normal import.

## Recommended next steps

1. Restore or re-export `source/original/architecture-overview.md` and refresh `src_001.checksum`, **or** revert the Case A tamper.
2. Fix `ev_001.locator.path` to an existing in-package file (or remove/rebind evidence).
3. Re-run:  
   `python skills/context-validator/scripts/validate_package.py tests/validator/e2e/validator-e2e-invalid`
4. Only after structure is no longer invalid — or with **explicit** force — re-run context-importer.

## Orientation only

- Title still Northwind Edge Gateway proposal handoff (same package_id as normal sample).
- Content may still contain unknowns/conflicts, but **must not** be used as a trusted working brief while FAIL remains.
