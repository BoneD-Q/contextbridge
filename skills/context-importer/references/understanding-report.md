# Receiver Understanding Report — context-importer

Session-level report the receiving agent produces after a successful (or
restricted) import. **Default destination: current chat/session only.**  
Do **not** write this file into the Package.

Companion rules:

- [import-rules.md](import-rules.md) — gates, loads, paths  
- [trust-boundaries.md](trust-boundaries.md) — statuses, Unknown, Conflict  

---

## 1. Output rules

1. Include **all 12 required sections** below, in order.  
2. Use privacy-safe package labels (basename / `package_id`); avoid home-directory paths.  
3. Cite package object ids (`fact_001`, `ev_007`, `unk_001`, `cfl_001`, …).  
4. Bucket facts (and other knowledge) by **KnowledgeStatus** — never mix `inferred`
   into a “confirmed facts” list without a label.  
5. If a collection is `NOT_LOADED`, say so; do **not** invent rows.  
6. If a collection loaded with empty arrays, write “none recorded”.  
7. On restricted force-import, prefix the title and each section heading with
   **`UNTRUSTED_STRUCTURE`**.  
8. Language: the report may be zh, en, or bilingual. Do **not** change the meaning
   of source-language `statement.text` / `summary.text` / `definition.text` when
   paraphrasing. Prefer quoting source-language text for critical atoms and put
   translations in parentheses or beside `i18n` when helpful.  
9. Do not paste secrets from excerpts; cite evidence ids and short non-secret fragments.

---

## 2. Required sections (frozen)

### 1) Package 基本信息 / Package identity

- Privacy-safe path or basename  
- `package_id`, title (`zh`/`en` if present)  
- `cbhf_version`, `protocol`, `scenario`, `package_form`  
- `generated_at`, generator skill/version if present  
- Validation gate outcome: normal / unvalidated / blocked / restricted  
- Bound Validator summary when available: `final_status`, layer rollups, FAIL ids  
- Flags: `structurally_unvalidated_in_this_session`, `validation_report_unbound`,
  `UNTRUSTED_STRUCTURE` as applicable  

### 2) 项目背景与目标 / Background and goals

- Condensed from `knowledge/overview.md` and receiver-guide purpose  
- Mark as **narrative** (not automatically verified knowledge)  
- Include scope / non-goals when present in overview  

### 3) 已知事实 / Known facts (by status)

From `knowledge/facts.json`, group by `status`:

- `verified`  
- `user_confirmed` (include confirmation summary)  
- `inferred`  
- `unverified`  
- `unknown`  
- `disputed` (point to Conflicts)  

For each item: `fact_id`, statement text (+ lang), `evidence_ids`, `conflict_ids`,
optional `context`.

### 4) 关键主张及证据 / Claims and evidence

From `knowledge/claims.json`:

- `claim_id`, `kind` if present, statement, status, notes (esp. Inference:)  
- Linked `evidence_ids` and key excerpt references by `evidence_id`  
- `related_fact_ids` when present  

### 5) 决策 / Decisions

From `knowledge/decisions.json`:

- `decision_id`, summary, status, date, rationale, `supersedes`, evidence, conflicts  

### 6) 约束与边界 / Constraints and boundaries

From `knowledge/constraints.json`:

- `constraint_id`, statement, status, `priority`, evidence, conflicts  

### 7) 术语表 / Glossary

From `knowledge/glossary.json`:

- `term_id`, term, definition, status, aliases, evidence  

Remind: listing a term ≠ verified.

### 8) Unknowns

From `uncertainty/unknowns.json`:

- Every `unknown_id` with question + why_it_matters  
- Label **OPEN — DO NOT FILL**  
- `suggested_owner`, related ids, notes  

### 9) Conflicts

From `uncertainty/conflicts.json`:

- Every `conflict_id` with summary and `shared_context`  
- Each party: type, id, stance  
- `resolution` value or **unresolved**  
- Explicit: do not choose a winner when unresolved  

### 10) 待确认问题 / Open questions

From `handoff/questions.json`:

- `question_id`, ask, priority, related unknown/conflict ids, notes  

### 11) 建议下一步 / Suggested next actions

From `handoff/recommended-actions.json`:

- Prefer `status: pending`  
- Include blocked/cancelled only with their status visible  
- Do not mark actions done  

### 12) 接收方理解限制 / Receiver limitations

Must include as applicable:

- Package not modified (read-only import)  
- Structure unvalidated / unbound report / UNTRUSTED_STRUCTURE  
- Validator NOT_CHECKED items (especially H01–H06) — not PASS  
- L4 semantic review not completed; no semantic PASS claimed  
- Redaction best-effort / incompleteness from `manifest.redaction` + `limitations`  
- Opaque sources (`readable: false`) unread  
- Collections `NOT_LOADED`  
- I14/I20 (if mentioned via Validator) are structural only  
- Unknowns remain open; Conflicts unresolved unless package says otherwise  

---

## 3. Markdown template

Copy and fill. Delete instructional comments.

```markdown
# Receiver Understanding Report

> Gate: <normal | structurally_unvalidated_in_this_session | blocked | UNTRUSTED_STRUCTURE>
> package: <basename-or-label>
> package_id: <id>
> cbhf_version: <0.1.0>
> importer: context-importer 0.1.0 (session report; package not modified)

## 1. Package identity

- …
- Validator (if bound): final_status=…; L1=…; L2=…; L3=…; L4=…
- FAIL ids: …
- NOT_CHECKED (do not treat as PASS): …

## 2. Background and goals

(Narrative from overview / receiver-guide — not auto-verified.)

## 3. Known facts (by status)

### verified
- `fact_…`: … (evidence: `ev_…`)

### user_confirmed
- …

### inferred
- …

### unverified
- …

### unknown
- …

### disputed
- … → see Conflicts (`cfl_…`)

## 4. Claims and evidence

- `claim_…` [status]: …  
  - evidence: `ev_…` …

## 5. Decisions

- `dec_…` [status]: …

## 6. Constraints and boundaries

- `con_…` [status] [priority]: …

## 7. Glossary

- `term_…` [status]: …

## 8. Unknowns

- `unk_…` **OPEN — DO NOT FILL**: …
  - why it matters: …

## 9. Conflicts

- `cfl_…` (context: …) **unresolved**  
  - party A: … stance …  
  - party B: … stance …  
  - Do not auto-select a winner.

## 10. Open questions

- `q_…`: …

## 11. Suggested next actions

- `act_…` [pending]: …

## 12. Receiver limitations

- …
```

---

## 4. Blocked-import stub (no force)

When gates block full takeover, use a short stub instead of the 12-section construction report:

```markdown
# Import blocked — fix structure first

- package: …
- package_id: …
- reason: final_status=invalid and/or L1–L3 FAIL
- FAIL summary: …
- Next: repair package and/or run context-validator; re-import
- Note: full Receiver Understanding Report withheld (no force requested)
```

---

## 5. Relationship to `handoff/receiver-guide.md`

| Artifact | Role |
| --- | --- |
| `receiver-guide.md` | Packaged, bilingual standing instructions from Exporter |
| Receiver Understanding Report | **This session’s** restored working brief for the next agent |

The Understanding Report SHOULD incorporate guide trust warnings; it MUST still
include structured sections backed by JSON collections, not guide prose alone.

---

## 6. Acceptance ties

| ID | This file |
| --- | --- |
| IM-01 | Full 12-section template |
| IM-02 | Gate banner in §1 / template |
| IM-03 | §4 blocked stub |
| IM-04 | `UNTRUSTED_STRUCTURE` rules |
| IM-05–IM-07 | Sections 3/8/9 + trust-boundaries |
| IM-12 | Section 12 + Validator honesty |
| IM-14 | §1 language rules |
