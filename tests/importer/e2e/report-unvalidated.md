# Receiver Understanding Report

> Gate: **structurally_unvalidated_in_this_session**
> package: `generated-output`
> package_id: `pkg_northwind_edge_gateway_proposal`
> cbhf_version: `0.1.0`
> importer: context-importer 0.1.0 (session report; package not modified)
> Validator session report: **not provided**
> Packaged `validation/validation-report.json`: **absent**

## 1. Package identity

- Path (privacy-safe): `examples/technical-proposal/generated-output/`
- Title: zh「Northwind Edge Gateway 技术方案交接包」 / en「Northwind Edge Gateway technical proposal handoff」
- protocol: CBHF · scenario: docs · package_form: folder
- generated_at: 2026-11-19T04:41:00Z · generator: context-exporter 0.1.0
- `manifest.validation.present`: false
- **Gate:** Import **allowed** with mandatory disclosure — **`structurally_unvalidated_in_this_session`**
- **Must not claim:** L1–L3 PASS, structural certification, or semantic review PASS
- No Validator FAIL/PASS ids cited (Importer did not invent results; no bound report)

## 2. Background and goals

*(Narrative — not auto-verified; structure not validated in this session.)*

Same Northwind Edge Gateway docs handoff purpose as overview/receiver-guide: continue AI-to-AI work while preserving evidence, decisions, unknowns, and conflicts.

Non-goals include resolving the prod port conflict and claiming Validator success.

## 3. Known facts (by status)

Status labels are **package KnowledgeStatus**, not Validator PASS (no bound report).

### verified

- `fact_001`: The control-plane API listens on path prefix `/v1/admin`. (`ev_001`)
- `fact_002`: Data-plane health checks use `GET /healthz` and expect HTTP 200. (`ev_002`)
- `fact_003`: Default idle timeout for upstream connections is 60 seconds. (`ev_003`)
- `fact_004`: Supported TLS versions are TLS 1.2 and TLS 1.3 only. (`ev_004`)
- `fact_005`: Configuration object id format is `cfg_<uuid>`. (`ev_005`)
- `fact_006`: Staging data-plane listen port is 8000. (`ev_006`)
- `fact_009`: In the embedded soak excerpt, CPU avg is 38%. (`ev_009`)
- `fact_010`: In the embedded soak excerpt, Conn pool wait P99 is 120 ms. (`ev_010`)

### user_confirmed

- none recorded (on facts)

### inferred

- none recorded (on facts)

### unverified

- none recorded

### unknown

- none recorded (on facts)

### disputed

- `fact_007`: Production data-plane listen port is 8080. (`ev_007`, `cfl_001`)
- `fact_008`: Production data-plane listen port is 8000. (`ev_008`, `cfl_001`)

## 4. Claims and evidence

- `claim_001` **[inferred]**: The current bottleneck is the upstream connection pool, not CPU. (`ev_009`, `ev_010`, `ev_011`) — **not** verified.

## 5. Decisions

- `dec_001` **[user_confirmed]** + confirmation (`user_authored_source` / `src_003`)
- `dec_002` **[user_confirmed]** + confirmation (`user_authored_source` / `src_003`)
- `dec_003` **[verified]** (`ev_016`)

## 6. Constraints and boundaries

- `con_001`, `con_002`, `con_003` — all packaged **verified** with evidence ids (package labels only)

## 7. Glossary

- `term_001` PoP · `term_002` Origin pool — packaged **verified**

## 8. Unknowns

- `unk_001` **OPEN — DO NOT FILL**: production replica count per PoP
- `unk_002` **OPEN — DO NOT FILL**: on-call owner for control-plane API pages
- `unk_003` **OPEN — DO NOT FILL**: `ff_http3_preview` ship state to any prod PoP

## 9. Conflicts

- `cfl_001` **unresolved**: fact_007 stance 8080 vs fact_008 stance 8000 (prod). No winner.

## 10. Open questions

- `q_001` [high]: authoritative production listen port
- `q_002` [high]: replica count + on-call ownership

## 11. Suggested next actions

- `act_001` [pending]: resolve `cfl_001` with user
- `act_002` [pending]: collect unk_001–unk_003 answers

## 12. Receiver limitations

- **`structurally_unvalidated_in_this_session`** — no bound Validator report in this run.
- **Do not claim L1–L3 PASS** or semantic PASS.
- Recommend running `context-validator` before high-stakes use.
- L4 not performed; H\* not asserted.
- Redaction best_effort; Unknowns OPEN; Conflict unresolved.
- Package not modified; no network Unknown fill.
