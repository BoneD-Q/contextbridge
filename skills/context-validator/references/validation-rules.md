# Validation rules catalog (CBHF 0.1.0)

Authority: `docs/context-validator-design.zh-CN.md` + `spec/cbhf/v0.1.0/*.schema.json` + exporter references.  
**Do not invent protocol fields.**

## Result codes (per check)

`PASS` | `FAIL` | `WARNING` | `NOT_CHECKED` | `NEEDS_HUMAN_REVIEW`

## Capability note (Phase 3B-C1)

All checks below are **defined**. Automation status:

| Layer | Automation |
| --- | --- |
| L1 (P01–P07) | Implemented in `scripts/validate_package.py` |
| L2 (S01–S15) | Implemented in `scripts/validate_package.py` |
| L3-A (I01–I09, I15, I17–I19) | Implemented in `scripts/_integrity.py` |
| L3-B1 (I11, I10) | Implemented in `scripts/_integrity.py` |
| L3-B2 (I16) | Implemented in `scripts/_integrity.py` (Option C) |
| L3-B3 (I12) | Implemented in `scripts/_integrity.py` (line_range bounds) |
| L3-B4 (I13) | Implemented in `scripts/_integrity.py` (Option B — no finders) |
| L3-C I14 | **Rules frozen** and **automated** in `scripts/_integrity.py` (line_range excerpt match) |
| L3-C I20 | **Not** implemented — report `NOT_CHECKED` |
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

Frozen semantics (**L3-B3 / I12**). Does not implement I13 findability or I14 excerpt match. Does not invent Schema fields.

| Field | Content |
| --- | --- |
| Scope | Only evidence items with `locator_type == "line_range"` among **loaded** evidence. Non-`line_range` locators are **skipped** here (I13). |
| Evidence FAIL | For each applicable item, after I11/I10 gates (below): `start` and `end` must each be non-null, finite, and integer-valued numbers; `start >= 1`; `end >= start`; `end <=` file line count. Any unmet condition → FAIL (including either `start` or `end` being `null` — **no** coalescing `end=null` to `start`). |
| Line count | `path.read_text(encoding="utf-8").splitlines()` then `len(lines)` — same definition as package smoke’s line_range check. Successful reads are retained as an **in-memory text snapshot** (per evidence_id) for I14; snapshots are **not** written to the validation report or error messages. |
| Gates (do not read path) | If I11 classifies the locator.path as unsafe or unresolved → this item is NOT_CHECKED (no file read). If I10 does not confirm the path exists as a package file → this item is NOT_CHECKED (no file read). |
| Read failures | UTF-8 decode failure or other read error after gates → this item NOT_CHECKED (not FAIL for bounds); no snapshot for that evidence. |
| PASS | Evidence is loaded; there is no FAIL item; and there is no applicable item left NOT_CHECKED. Includes: loaded evidence with **zero** `line_range` items (empty applicable set) → PASS. |
| NOT_CHECKED | Evidence not loaded; **or** no FAIL but at least one applicable `line_range` item was gated/unread (I11/I10/read failure). Non-`line_range` items do **not** by themselves make I12 NOT_CHECKED. |
| Rollup | Per check: **FAIL > NOT_CHECKED > PASS**. Partial skips must retain per-item NOT_CHECKED reasons in `errors` (or equivalent detail). Must **not** report overall PASS when any applicable item remained unchecked. |
| Notes | Schema may still allow `null` start/end for `line_range`; I12 FAIL on null is intentional (closes plan item L3-RQ2 as FAIL). Unknown path safety remains I11; existence I10. Automated in Phase 3B-B3. |

### I13 — Other locator types (B)

Frozen semantics (**Option B**, L3-B4 / I13). Does not invent Schema fields. Does not implement finders. Does not judge excerpt↔window match (I14) or semantic adequacy (L4).

| Field | Content |
| --- | --- |
| Scope | Loaded evidence with `locator_type` in `{section, json_pointer, anchor, page_range}` only. **`line_range` is out of scope** (I12). |
| FAIL | **None for target findability in 0.1.0.** Do not re-FAIL locator shape (L2 Schema), line_range bounds (I12), path safety (I11), or path existence (I10). |
| PASS | Evidence collection is fully loaded **and** there are **zero** I13-applicable items (e.g. only `line_range`, or empty evidence array). |
| NOT_CHECKED | Evidence not loaded; **or** one or more I13-applicable items exist and 0.1.0 has **no** deterministic finder for them; **or** an applicable item is gated by I11 unsafe/unresolved / I10 missing / read-or-parse conditions that prevent reliable checking. Legal locator field shape alone must **not** be treated as “findable”. |
| Gates | Same as I12: I11 unsafe/unresolved → item NOT_CHECKED, do not read; I10 does not confirm file exists → item NOT_CHECKED, do not read; no out-of-package reads; no new path-resolution policy beyond I11/I10. |
| Rollup | **FAIL > NOT_CHECKED > PASS**. Retain per-item detail. Must not report overall PASS while any applicable item remains NOT_CHECKED. |
| WARNING | **Not** used as an I13 check result in 0.1.0. Inability to confirm targets → `NOT_CHECKED` (reasons/limitations may explain why; do not extend report Schema). |
| Semantic boundary | Heading/anchor/page/JSON node “correctness” for the claim, and whether excerpt supports the proposition, are **not** I13 auto-PASS (I14 / L4). |
| Notes | Q2 findability depth remains open for *future* finder strength; 0.1.0 freezes Option B (empty applicable → PASS; any applicable without finder → NOT_CHECKED). Automated in Phase 3B-B4 (no finders). |

### I14 — Excerpt text match (C)

Historical intent (unchanged): normalize newlines; every non-empty excerpt line appears in the locator window text (stricter than smoke “first line only”); PASS if all such lines match; FAIL if any line is missing; NOT_CHECKED when there is no text window / unread binary; **does not** prove semantic adequacy (tier D / L4).

Frozen semantics (**L3-C / I14**). Does not invent Schema fields. Does not implement finders for non-`line_range` types. Does **not** judge whether the excerpt adequately supports a claim or knowledge status (L4). **Rules frozen; automated in Phase 3B-C1.**

| Field | Content |
| --- | --- |
| Scope | Loaded evidence. **Match** only for `locator_type == "line_range"` (`evidence[].locator.excerpt`). |
| Out of scope (per-item NOT_CHECKED) | `section`, `json_pointer`, `anchor`, `page_range`: **no** finder, **no** text-window match. Each such item is recorded as NOT_CHECKED (`out_of_scope_type`) and **does** participate in rollup (so a package with only these types → overall NOT_CHECKED). Do not re-check I13 findability. |
| Window (must match I12 line numbering) | Only after per-item I12 status is `pass`. Use the **I12 in-memory UTF-8 text snapshot** for that evidence (same bytes I12 used for line count). `lines = text.splitlines()`; `window = "\n".join(lines[start - 1:end])`. **Do not** call `read_text` again for the match window. |
| Newline normalize (excerpt only, before split) | `\r\n` → `\n`; bare `\r` → `\n`. **No** Unicode NFC/NFD; **no** case folding; **no** fuzzy or semantic match. |
| Empty lines | After normalize+split: a line with `line.strip() == ""` is empty and **skipped** (does not participate in match). |
| Non-empty line match | Keep the line **un-stripped** (no extra strip, no internal whitespace collapse). Require `excerpt_line in window` (literal substring). Order / contiguity / adjacency of excerpt lines within the window is **not** required. |
| Gates (do not build a trusted window) | Consume **per-evidence** I12 status (`pass`/`fail`/`not_checked`) and I12 text snapshots; do not re-derive bounds independently to override I12. I12 `fail` → item NOT_CHECKED (`i12_failed`). I12 `not_checked` → item NOT_CHECKED (may refine to `i11_unsafe` / `i11_unresolved`). I12 `pass` but snapshot missing → NOT_CHECKED (`snapshot_missing`); **must not** re-read the file to recover. Source-index not loaded or `source_id` not resolvable → NOT_CHECKED (`source_readable_unresolved`) — do not PASS; do not re-implement I09. Source `readable: false` → NOT_CHECKED. No out-of-package reads; no network; do not modify the package. Snapshots must not appear in the validation report or error messages. |
| PASS | Evidence collection is fully loaded; there is no FAIL item; and **no** item remains NOT_CHECKED. Includes: (a) every `line_range` item matched (or had no non-empty excerpt lines) after I12 `pass` + readable OK; (b) loaded evidence with **zero** items (empty array). |
| FAIL | At least one `line_range` item has a trusted window and at least one non-empty excerpt line that is **not** a literal substring of that window. |
| NOT_CHECKED | Evidence not loaded; **or** no FAIL but at least one item was NOT_CHECKED (out-of-scope type, I12 gate, readable gate, read failure, etc.). |
| Rollup | **FAIL > NOT_CHECKED > PASS**. Retain per-item detail. Must not report overall PASS while any item remained NOT_CHECKED. Unloaded evidence must **not** be treated as an empty-array PASS. |
| WARNING | **Not** used as an I14 check result in 0.1.0. |
| NEEDS_HUMAN_REVIEW | **Not** used as an I14 check result; semantic judgment stays L4. Do not add report statuses. |
| Semantic boundary | I14 PASS means only that every non-empty excerpt line is findable as a literal substring in the `line_range` window. It does **not** mean semantic adequacy, claim support, evidence authenticity, correct `verified` status, conflict resolution, or completed human L4 review. |
| Notes | Closes plan items L3-RQ3 (no Unicode normalize) and L3-RQ4 (empty excerpt → PASS, no WARNING). Stricter than package smoke’s “first excerpt line only”. Does not re-FAIL I10/I11/I12/I13/I16 concerns. Automated in Phase 3B-C1. |

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
- Q2 section/page findability depth — **0.1.0 I13 Option B frozen:** no finder; applicable items → `NOT_CHECKED` (not WARNING); empty applicable → PASS. Deeper finders / FAIL-on-missing remain future Q2 work, not claimed verified.  
- Q3 checksum mismatch severity  
- Q4/Q5 package write of report (deferred; Phase 1 session-only)  
- handoff `priority` string vs future enum (cbhf-format #12)  
