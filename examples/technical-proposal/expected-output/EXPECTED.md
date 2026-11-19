# Expected CBHF outcomes (specification checklist)

> **Not an exporter artifact.** This file describes what a **correct** CBHF 0.1.0 package *should* contain after a future `context-exporter` run over `../input/`. It was written by hand for test planning. Do **not** treat it as proof that an exporter already ran or passed validation.

## Package form

- Protocol: CBHF `0.1.0`
- Scenario: `docs`
- Form: `folder`
- Exporter-required tree present; **no** fabricated `validation/validation-report.json`

## Sources

Packaged copies under `source/original/` for at least:

- `architecture-overview.md`
- `ops-runbook-excerpt.md`
- `decision-record.md`
- `open-questions.md`

`source-index.json`:

- Each entry has `content_transformed` ∈ {true, false, null}
- After secret redaction on copies/excerpts → likely `content_transformed: true` for affected files
- User originals outside the package remain untouched

## Redaction

`manifest.redaction.applied: true` if tokens/passwords/webhook secrets were masked.

Must **not** leave plaintext:

- `EDGE_BOOTSTRAP_TOKEN=...`
- `DB_PASSWORD=...`
- pager webhook token URL secrets

Use placeholders such as `[REDACTED:token]` / `[REDACTED:password]`.

`completeness: best_effort` — do not claim complete secret discovery.

## Knowledge expectations (illustrative ids)

### Facts (examples)

| Topic | Expected status | Notes |
| --- | --- | --- |
| Admin API prefix `/v1/admin` | `verified` if located | architecture-overview |
| Health check `GET /healthz` → 200 | `verified` if located | |
| Idle timeout 60s | `verified` if located | |
| TLS 1.2/1.3 only | `verified` if located | |
| Staging listen port 8000 (`environment: staging`) | `verified` if located | ops-runbook |
| Prod listen port 8080 (`environment: prod`) | `disputed` | conflicts with other prod 8000 |
| Prod listen port 8000 (`environment: prod`) | `disputed` | same context as above |

Staging 8000 vs prod 8080 must **not** be a Conflict by itself (different environments).

### Claims

| Topic | Expected status | Notes |
| --- | --- | --- |
| Bottleneck is upstream connection pool | `inferred` | interpretation of soak table; notes should mark Inference |

### Decisions

| Topic | Expected status | Notes |
| --- | --- | --- |
| No standalone Web UI in v1 | `verified` or `user_confirmed` | decision-record wording |
| Folder handoff (not single JSON) | `user_confirmed` | requires `confirmation` with quote 「就按文件夹交接…」 |

### Constraints

| Topic | Expected status | Priority hint |
| --- | --- | --- |
| No standalone public Web UI in v1 | `verified` | `must` / aligned with DEC-01 |
| No raw customer bodies in edge logs by default | `verified` | |
| Prod deploy needs change ticket annotation | `verified` | |

### Glossary

Terms such as PoP / Origin pool with status earned from spans — **not** auto-`verified` merely by listing.

## Uncertainty

### Conflict (required)

One Conflict where:

- `same_subject: true`
- `context_alignment: same`
- `shared_context.environment: prod`
- parties: prod listen **8080** vs prod listen **8000**
- `resolution: null`

### Unknowns

At least the open-questions items (replica count, on-call owner, `ff_http3_preview` ship state).

### Questions / actions

- Question asking which production port statement is authoritative (related to the conflict).
- Recommended action `status: pending` only (never `completed`) to confirm the prod port with the user; `related_ids` may include `q_*` / `cfl_*` / `unk_*`.

## Manifest honesty

- `validation.present: false`
- `limitations` mention redaction best-effort and any unread/uncopied files
- `integrity.files_touched` if present is **not** an integrity pass

## Out of scope for this expected-output file

- Concrete filled JSON/YAML package files
- Claiming Validator success
- Resolving the production port conflict
