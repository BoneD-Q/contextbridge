# Conflict review — `cfl_001`

**Subject under review:** Production edge data-plane listen port **8080 vs 8000**  
**Package object:** `uncertainty/conflicts.json` → `cfl_001`  
**Review type:** Manual semantic — not Validator  

## Questions

| Question | Finding | Code |
| --- | --- | --- |
| Do both statements describe the same subject? | Yes — production **data-plane listen port** for edge processes. | PASS |
| Same production environment? | Yes — both labeled `environment: prod` / production in `ops-runbook-excerpt.md`. Package `shared_context.environment=prod`, `scope=edge-data-plane`. | PASS |
| Time or version difference that would dissolve the conflict? | One side notes a systemd review date `2026-10-02` for the 8080 statement; the 8000 statement has no alternate version/time. No supersession language. Treat as same-context contradiction as authored. | PASS |
| Does each evidence support its party? | `ev_007` → fact_007 (8080); `ev_008` → fact_008 (8000); both locatable and faithful. | PASS |
| Was staging 8000 wrongly pulled into the conflict? | No. `fact_006` (staging 8000) is separate; conflict notes explicitly exclude it; parties are only fact_007/fact_008. | PASS |
| Was a winner chosen? | `resolution: null`; statuses remain `disputed`. | PASS |
| Should reviewer decide the correct port? | No — left for user. | NEEDS HUMAN DECISION |

## Alignment with EXPECTED.md

EXPECTED requires one conflict with `same_subject: true`, `context_alignment: same`, prod shared context, parties 8080 vs 8000, `resolution: null`. Package matches.

## Staging vs production (non-conflict control)

Staging port 8000 vs production 8080 is **not** recorded as a conflict — correct under claim-rules (different environments).

## Outcome

**Conflict result: PASS** (structure and semantics).  
**Port authority: NEEDS HUMAN DECISION** (do not auto-resolve).
