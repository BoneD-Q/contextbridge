# Validation rules catalog (CBHF 0.1.0)

Authority: `docs/context-validator-design.zh-CN.md` + `spec/cbhf/v0.1.0/*.schema.json` + exporter references.  
**Do not invent protocol fields.**

## Result codes (per check)

`PASS` | `FAIL` | `WARNING` | `NOT_CHECKED` | `NEEDS_HUMAN_REVIEW`

## Capability note (Phase 3B-B2)

All checks below are **defined**. Automation status:

| Layer | Automation |
| --- | --- |
| L1 (P01–P07) | Implemented in `scripts/validate_package.py` |
| L2 (S01–S15) | Implemented in `scripts/validate_package.py` |
| L3-A (I01–I09, I15, I17–I19) | Implemented in `scripts/_integrity.py` |
| L3-B1 (I11, I10) | Implemented in `scripts/_integrity.py` |
| L3-B2 (I16) | Implemented in `scripts/_integrity.py` (Option C) |
| L3-B/C remaining (I12, I13, I14, I20) | **Not** implemented — report `NOT_CHECKED` |
| L4 (H01–H06) | **Not** automated — never semantic PASS |

Anything not actually executed → `NOT_CHECKED`.  
`tests/schema/v0.1.0/package_smoke_test.py` is **not** this catalog’s automation.

## Tier reminder (L3)

| Tier | Meaning | Layer |
| --- | --- | --- |
| A | Reference ID exists | L3 |
| B | Locator path/range valid | L3 |
| C | Excerpt text matchable in window | L3 |
| D | Excerpt semantically adequate for proposition/status | **L4 only** |

File exists ≠ parseable ≠ schema-valid ≠ reference exists ≠ locator valid ≠ excerpt matchable ≠ semantically adequate.

---

## L1 — Package Validation

### P01 — Required paths exist

| Field | Content |
| --- | --- |
| Object | Package root |
| Input | Directory listing |
| Logic | Require Exporter-required tree: `manifest.yaml`, `source/source-index.json`, `source/original/`, `knowledge/overview.md`, `knowledge/facts.json`, `knowledge/claims.json`, `knowledge/decisions.json`, `knowledge/constraints.json`, `knowledge/glossary.json`, `evidence/evidence.json`, `evidence/references.json`, `uncertainty/unknowns.json`, `uncertainty/conflicts.json`, `handoff/receiver-guide.md`, `handoff/questions.json`, `handoff/recommended-actions.json` |
| PASS | All present |
| FAIL | Any missing |
| NOT_CHECKED | Cannot list directory |
| Output | List missing paths |

### P02 — Markdown readable

| Field | Content |
| --- | --- |
| Object | `knowledge/overview.md`, `handoff/receiver-guide.md` |
| Input | File bytes |
| Logic | UTF-8 readable text |
| PASS | Both readable |
| FAIL | Unreadable / missing after P01 |
| NOT_CHECKED | Host cannot read files |
| Output | Which file failed |

### P03 — JSON parseable (reject duplicate keys)

| Field | Content |
| --- | --- |
| Object | All package `.json` files |
| Input | File text |
| Logic | Parse as JSON; **duplicate keys must FAIL** (silent overwrite parsers are insufficient alone) |
| PASS | All parse; no duplicate keys detected |
| FAIL | Syntax error or duplicate key |
| NOT_CHECKED | No duplicate-key-aware parser available |
| Output | File + parse error |

### P04 — YAML parseable (reject duplicate keys)

| Field | Content |
| --- | --- |
| Object | `manifest.yaml` |
| Input | File text |
| Logic | Parse YAML with unique-key enforcement |
| PASS | Parses; no duplicate keys |
| FAIL | Syntax / duplicate key |
| NOT_CHECKED | No unique-key YAML loader |
| Output | Error detail |

### P05 — Package form

| Field | Content |
| --- | --- |
| Object | Layout + manifest `package_form` / `scenario` when readable |
| Input | Tree + parsed manifest if available |
| Logic | Expect folder package; `package_form` should be `folder`, `scenario` `docs` for 0.1.0 docs scenario |
| PASS | Folder layout consistent |
| FAIL | Clearly not a CBHF folder root |
| NOT_CHECKED | Manifest unreadable |
| Output | Observed form |

### P06 — Extra / unexpected entries

| Field | Content |
| --- | --- |
| Object | Top-level and notable extras |
| Input | Tree enum |
| Logic | Unknown top-level → **WARNING** (allowlist not frozen — Open Question Q1). `validation/` allowed only if a prior/explicit Validator write exists |
| PASS | No unexpected top-level |
| WARNING | Unexpected extras |
| FAIL | (reserved; not default in 0.1.0) |
| NOT_CHECKED | Cannot enumerate |
| Output | Extra paths |

### P07 — Read-only commitment

| Field | Content |
| --- | --- |
| Object | Validator runtime behavior |
| Input | Process intent |
| Logic | Must not modify knowledge/evidence/source copies. Phase 1: do not write package reports by default |
| PASS | No package mutation |
| FAIL | Package knowledge mutated during validation |
| NOT_CHECKED | Cannot verify filesystem mtimes/hashes |
| Output | Mutation evidence if any |

---

## L2 — Schema Validation

Schemas live under `spec/cbhf/v0.1.0/` (Draft 2020-12).

### S01 — Load schemas

| Field | Content |
| --- | --- |
| Object | `*.schema.json` |
| Input | Spec directory |
| Logic | Load + `check_schema` |
| PASS | All load |
| FAIL | Schema files corrupt (Validator tooling error) |
| NOT_CHECKED | Spec path unavailable |
| Output | Schema load errors |

Common fields for **S02–S14** (each is a separate check):

| Field | Content |
| --- | --- |
| Input | Parsed JSON/YAML object from L1 |
| Logic | Validate against listed Draft 2020-12 schema (no invented fields) |
| PASS | Instance validates |
| FAIL | Any schema error |
| NOT_CHECKED | Schema engine unavailable, S01 failed, or L1 parse failed |
| Output | File path + schema `$id` + error paths/messages |

| ID | Object | Schema |
| --- | --- | --- |
| S02 | `manifest.yaml` (parsed) | `manifest.schema.json` |
| S03 | `source/source-index.json` | `source.schema.json` |
| S04 | `knowledge/facts.json` | `fact.schema.json` |
| S05 | `knowledge/claims.json` | `claim.schema.json` |
| S06 | `knowledge/decisions.json` | `decision.schema.json` |
| S07 | `knowledge/constraints.json` | `constraint.schema.json` |
| S08 | `knowledge/glossary.json` | `glossary.schema.json` |
| S09 | `evidence/evidence.json` | `evidence.schema.json` |
| S10 | `evidence/references.json` | `evidence.schema.json#/$defs/ReferencesDocument` |
| S11 | `uncertainty/unknowns.json` | `unknown.schema.json` |
| S12 | `uncertainty/conflicts.json` | `conflict.schema.json` |
| S13 | `handoff/questions.json` | `questions.schema.json` |
| S14 | `handoff/recommended-actions.json` | `recommended-actions.schema.json` |

### S15 — Enum / required / type / additionalProperties / if-then

| Field | Content |
| --- | --- |
| Object | All schema-validated instances |
| Input | Same as S02–S14 (rollup of keyword-level failures) |
| Logic | Covered by schema keywords (e.g. KnowledgeStatus enums, `verified`→`evidence_ids` minItems, `user_confirmed`→non-null `confirmation`, ReferenceStatus=`unverified` only) |
| PASS | No schema violations beyond those already reported under S02–S14 |
| FAIL | Illegal enum, missing required, wrong type, forbidden extras, failed if-then |
| NOT_CHECKED | Schema engine unavailable |
| Output | JSON Pointer-like paths when possible |  

---

## L3 — Integrity Validation

### I01 — Duplicate IDs (tier A)

| Field | Content |
| --- | --- |
| Object | All typed IDs (`source_id`, `fact_id`, `claim_id`, `decision_id`, `constraint_id`, `term_id`, `evidence_id`, `reference_id`, `unknown_id`, `conflict_id`, `question_id`, `action_id`, `package_id`) |
| Logic | Unique **within each kind** (cross-kind identical strings allowed) |
| PASS | Every applicable id collection loaded and checked; no within-kind duplicates |
| FAIL | Duplicate confirmed in any **loaded** kind (even if other collections are missing) |
| NOT_CHECKED | No confirmed duplicate, but one or more applicable collections not loaded / not schema-ok |
| Output | Duplicated ids |

### I02 — evidence.supports → knowledge exists (A)

| Logic | Each `supports[{type,id}]` resolves |
| PASS/FAIL/NOT_CHECKED | as usual |

### I03 — knowledge.evidence_ids → evidence exists (A)

| Logic | Each evidence_id in facts/claims/decisions/constraints/terms exists in evidence.json |

### I04 — Bidirectional consistency (A)

| Logic | If A lists ev_X and ev_X.supports includes A (matching type), and converse |
| FAIL | One-way link |

### I05 — conflict.parties exist (A)

| Logic | party type+id resolves to knowledge object |

### I06 — conflict.evidence_ids exist (A)

| Logic | Each id in evidence.json |

### I07 — Cross related_* ids (A)

| Object | `related_conflict_ids`, `related_unknown_ids`, `related_ids`, `conflict_ids`, `related_fact_ids` |
| Logic | Targets exist; **FAIL** if missing (design recommendation) |
| WARNING | Only if policy later softens (Open Question) |

### I08 — confirmation.source_ref for user_authored_source (A)

| Logic | When `source_type=user_authored_source`, `source_ref` must be a real `source_id` |
| FAIL | Missing / unknown source_id |

### I09 — locator.source_id in index (A)

| Logic | Every evidence locator.source_id ∈ source-index |

### I10 — locator.path exists (B)

| Logic | Path relative to package root; file exists |
| FAIL | Missing file |

### I11 — Path safety (B)

| Logic | Reject `..`, absolute paths, drive letters, UNC; resolved path must stay under package root; do not follow escaping symlinks |
| FAIL | Escape / forbidden form |
| NOT_CHECKED | Cannot resolve symlinks on host |

### I12 — line_range bounds (B)

| Logic | For `locator_type=line_range`: 1-based; end≥start; within file line count |
| FAIL | Out of bounds / invalid numbers |
| NOT_CHECKED | Non-line locator types |

### I13 — Other locator types (B)

| Logic | `section` start/end are string\|null; `page_range` numbers\|null; etc. per schema. Whether heading/page is findable → often `WARNING` or `NOT_CHECKED` if host cannot resolve (Open Question Q2) |
| PASS | Type-consistent and host verified findable |
| WARNING/NOT_CHECKED | Cannot verify findability |

### I14 — Excerpt text match (C)

| Logic | Normalize newlines; every non-empty excerpt line appears in the locator window text (stricter than smoke “first line only”) |
| PASS | All lines match |
| FAIL | Any line missing |
| NOT_CHECKED | Locator type without text window / unread binary |
| Note | **Does not** prove semantic adequacy (tier D / L4) |

### I15 — verified ⇒ non-empty evidence_ids (A)

| Logic | Re-check after load (schema also enforces) |
| FAIL | verified with empty/missing evidence_ids |

### I16 — readable:false sources (A/B)

Frozen semantics (**Option C**). Does not judge excerpt↔window match (I14) or semantic adequacy (L4).

| Field | Content |
| --- | --- |
| Object | `source-index` `readable` + evidence `locator.source_id` / `locator.excerpt` + knowledge `status` / `evidence_ids` |
| Evidence FAIL | Evidence whose `locator.source_id` resolves to a source with `readable: false`, **and** `strip(excerpt) != ""` (non-empty after strip). Empty or whitespace-only `excerpt` does **not** FAIL under the Evidence quoting clause alone. |
| Knowledge FAIL | Any knowledge object with `status: verified` whose `evidence_ids` includes an evidence item whose `locator.source_id` resolves to `readable: false` — **regardless** of that evidence’s excerpt emptiness. |
| PASS | Required collections are loaded (see NOT_CHECKED), and neither Evidence FAIL nor Knowledge FAIL applies. Empty evidence / knowledge sets with no violations → PASS. |
| NOT_CHECKED | `source-index` not loaded and/or `evidence` not loaded (cannot evaluate either branch). If those are loaded but knowledge collections needed for the verified branch are not loaded → NOT_CHECKED (must not report PASS). |
| Notes | Unknown `locator.source_id` is I09’s concern; I16 only applies when the source_id resolves and `readable` is false. Does not invent protocol fields. Automated in Phase 3B-B2. |

### I17 — content_transformed shape

| Logic | Covered by Schema (`true`\|`false`\|`null`) — record PASS under S03 or NOT_CHECKED if schema not run |
| Note | Listed for catalog completeness |

### I18 — manifest.validation honesty

| Field | Content |
| --- | --- |
| Logic | Depends on S02 PASS. If `validation.present=true`, the effective report path must exist **inside** the package (explicit `report_path` after strip, else default `validation/validation-report.json`). Reject absolute/`..`/UNC/drive/symlink escape. Explicit path missing must not be masked by a default file. |
| PASS | `present` is not true (normal unvalidated exporter package), or `present=true` and the authoritative report path exists safely |
| FAIL | `present=true` with missing/unsafe report path |
| NOT_CHECKED | S02 not PASS / manifest not loaded |
| Notes | Report messages use reason codes + package-relative paths only (no host absolute paths). Does not judge report content semantics. |

### I19 — Orphan evidence (supports empty) (A)

| Logic | Allowed by protocol preference to link; empty supports → **WARNING** |

### I20 — Checksum (optional)

| Logic | If checksum.value present, recompute package copy hash when possible |
| PASS | Match |
| FAIL/WARNING | Mismatch (severity Open Question Q3; recommend FAIL when value present) |
| NOT_CHECKED | No checksum or cannot hash |

---

## L4

See [semantic-review-boundary.md](semantic-review-boundary.md). L4 checks are **never** automated semantic PASS.

---

## Open Questions (record only)

- Q1 Extra files: warn vs fail  
- Q2 section/page findability depth  
- Q3 checksum mismatch severity  
- Q4/Q5 package write of report (deferred; Phase 1 session-only)  
- handoff `priority` string vs future enum (cbhf-format #12)  
