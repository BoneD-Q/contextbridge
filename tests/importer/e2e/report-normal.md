# Receiver Understanding Report

> Gate: **normal** (Validator session report bound)
> package: `generated-output`
> package_id: `pkg_northwind_edge_gateway_proposal`
> cbhf_version: `0.1.0`
> importer: context-importer 0.1.0 (session report; package not modified)
> receiver task: continue Northwind Edge Gateway proposal handoff

## 1. Package identity

- Path (privacy-safe): `examples/technical-proposal/generated-output/`
- Title: zh「Northwind Edge Gateway 技术方案交接包」 / en「Northwind Edge Gateway technical proposal handoff」
- protocol: CBHF · scenario: docs · package_form: folder
- generated_at: 2026-11-19T04:41:00Z · generator: context-exporter 0.1.0
- `manifest.validation.present`: false (no packaged `validation/`; session report supplied instead)
- **Validator binding:** session `tests/validator/e2e/report-normal.json`
  - `package_id` match: `pkg_northwind_edge_gateway_proposal`
  - label: `generated-output` matches basename
  - Bound: **yes** (not `validation_report_unbound`)
- Validator summary: `final_status=semantically_unreviewed`
  - layers: L1=PASS, L2=PASS, L3=PASS, L4=**NOT_CHECKED**
  - L1–L3 FAIL ids: none
  - NOT_CHECKED (≠ PASS): H01–H06 (L4 not automated)
- Gate outcome: **normal import** allowed
- Structure PASS ≠ semantic adequacy; I14/I20 PASS (in Validator) ≠ authenticity

## 2. Background and goals

*(Narrative from `knowledge/overview.md` / `handoff/receiver-guide.md` — not auto-verified.)*

Continue work on the fictional **Northwind Edge Gateway** technical proposal without losing evidence, decisions, unknowns, or conflicts.

Scope: docs handoff of the input set under `examples/technical-proposal/input/` (user originals not modified; locators use `source/original/` copies).

Non-goals (from overview): resolving the production listen-port conflict; claiming Validator success; fetching external references.

## 3. Known facts (by status)

### verified

- `fact_001`: The control-plane API listens on path prefix `/v1/admin`. (evidence: `ev_001`)
- `fact_002`: Data-plane health checks use `GET /healthz` and expect HTTP 200. (`ev_002`)
- `fact_003`: Default idle timeout for upstream connections is 60 seconds. (`ev_003`)
- `fact_004`: Supported TLS versions are TLS 1.2 and TLS 1.3 only. (`ev_004`)
- `fact_005`: Configuration object id format is `cfg_<uuid>`. (`ev_005`)
- `fact_006`: Staging data-plane listen port is 8000. (`ev_006`) — staging env; not part of `cfl_001`
- `fact_009`: In the embedded soak excerpt, CPU avg is 38%. (`ev_009`)
- `fact_010`: In the embedded soak excerpt, Conn pool wait P99 is 120 ms. (`ev_010`)

### user_confirmed

- none recorded (on facts)

### inferred

- none recorded (on facts)

### unverified

- none recorded

### unknown

- none recorded (on facts; see Unknowns section for `unk_*`)

### disputed

- `fact_007`: Production data-plane listen port is 8080. (`ev_007`, conflict_ids: `cfl_001`)
- `fact_008`: Production data-plane listen port is 8000. (`ev_008`, conflict_ids: `cfl_001`)  
  → see Conflicts; **do not pick a winner**

Spot-check: `src_001.readable === true`; `ev_001` excerpt located in `source/original/architecture-overview.md` (path-safe).

## 4. Claims and evidence

- `claim_001` **[inferred]**: The current bottleneck is the upstream connection pool, not CPU.
  - notes: Inference: source labels this as an interpretation of soak numbers (high conn-pool wait with CPU under 40%), not a verbatim measurement label.
  - evidence: `ev_009`, `ev_010`, `ev_011`
  - **Not upgraded to verified.**

## 5. Decisions

- `dec_001` **[user_confirmed]**: v1 ships API + CLI only; no standalone public Web UI.
  - evidence: `ev_012`, `ev_013`
  - confirmation: `source_type=user_authored_source`, `source_ref=src_003`, text includes “We confirmed we will not ship a standalone Web UI in v1.” (not forged)
- `dec_002` **[user_confirmed]**: Use CBHF folder package form for AI-to-AI handoff of this proposal set.
  - evidence: `ev_014`, `ev_015`
  - confirmation: `source_type=user_authored_source`, `source_ref=src_003`, text「就按文件夹交接，不要做成单个 JSON 包。」
- `dec_003` **[verified]**: Allow TLS 1.2 and TLS 1.3 only at the edge terminator. (`ev_016`)

## 6. Constraints and boundaries

- `con_001` **[verified]** `must_not`: Must not introduce a standalone public Web UI in v1 (API and CLI only). (`ev_017`)
- `con_002` **[verified]** `must_not`: Must not store raw customer request bodies in edge logs by default. (`ev_018`)
- `con_003` **[verified]** `must`: Production changes require a change ticket id in the deploy annotation. (`ev_019`, `ev_020`)

## 7. Glossary

- `term_001` **[verified]**: PoP — Point of Presence — an edge location running gateway instances. (`ev_021`)
- `term_002` **[verified]**: Origin pool — Set of regional backends selected by routing policy. (`ev_022`)  
  Listing a term ≠ automatic truth beyond packaged status/evidence.

## 8. Unknowns

- `unk_001` **OPEN — DO NOT FILL**: What is the actual production replica count per PoP?
  - why it matters: Affects capacity and failover wording.
  - suggested_owner: user · notes: Listed in open-questions.md; not answered in sources.
- `unk_002` **OPEN — DO NOT FILL**: Who is the on-call owner for control-plane API pages?
  - why it matters: Needed for operational handoff ownership.
- `unk_003` **OPEN — DO NOT FILL**: Has feature flag `ff_http3_preview` shipped to any prod PoP?
  - why it matters: Affects whether HTTP/3 preview behavior should be assumed in prod.

No replica count invented.

## 9. Conflicts

- `cfl_001` (shared_context: environment=prod, scope=edge-data-plane) **unresolved** (`resolution=null`)
  - party A: fact `fact_007` stance **8080**
  - party B: fact `fact_008` stance **8000**
  - evidence: `ev_007`, `ev_008`
  - notes: Staging port 8000 (`fact_006`) is a different environment and is **not** this conflict.
  - **Do not auto-select a winner.**

## 10. Open questions

- `q_001` [high]: Which production data-plane listen port is authoritative: 8080 or 8000?
- `q_002` [high]: What is the production replica count per PoP, and who owns control-plane on-call?

## 11. Suggested next actions

- `act_001` [pending]: Ask the user which production listen port is authoritative and record resolution for `cfl_001`.
- `act_002` [pending]: Collect production replica count, on-call owner, and `ff_http3_preview` ship state.

## 12. Receiver limitations

- Package not modified (read-only import).
- L4 semantic review **not** completed: H01–H06 are **NOT_CHECKED** (≠ PASS); no semantic PASS claimed.
- Validator L1–L3 PASS / I14 / I20 PASS ≠ authenticity or semantic adequacy.
- Redaction: `manifest.redaction.applied=true`, completeness **best_effort** — do not assume all secrets found.
- All four sources `readable=true` in this package; no opaque-body fabrication needed.
- Unknowns remain OPEN; Conflict `cfl_001` unresolved.
- `manifest.validation.present=false` does not mean “validation passed”; a **session** report was bound for this import.
- No network fill of Unknowns performed.
