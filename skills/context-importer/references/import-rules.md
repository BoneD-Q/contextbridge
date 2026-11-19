# Import rules (CBHF 0.1.0) — context-importer

Authority for **how** the receiving agent loads a folder package, applies
validation gates, and stays path-safe.

- Trust / status semantics → [trust-boundaries.md](trust-boundaries.md)  
- Report shape → [understanding-report.md](understanding-report.md)  
- Field names / layout → `skills/context-exporter/references/cbhf-format.md` + `spec/cbhf/v0.1.0/*.schema.json`  

Do **not** redefine KnowledgeStatus here. Do **not** invent CBHF fields.

---

## 1. Package root

Importer input is a **directory** that is a CBHF folder package root:

- Must contain `manifest.yaml` at the root.  
- Expected Exporter-required tree (presence checked during load):

```
<package-root>/
├── manifest.yaml
├── source/source-index.json
├── source/original/
├── knowledge/overview.md
├── knowledge/facts.json
├── knowledge/claims.json
├── knowledge/decisions.json
├── knowledge/constraints.json
├── knowledge/glossary.json
├── evidence/evidence.json
├── evidence/references.json
├── uncertainty/unknowns.json
├── uncertainty/conflicts.json
└── handoff/
    ├── receiver-guide.md
    ├── questions.json
    └── recommended-actions.json
```

Optional (Validator-owned reservation; Exporter must not invent it):

```
<package-root>/validation/validation-report.json
```

Absence of `validation/` means **not validated yet**, not “validation passed”
(`cbhf-format.md`).

---

## 2. Read order

1. `manifest.yaml` — protocol, ids, limitations, redaction, `validation.present`  
2. Validation gate inputs (session report and/or packaged report) — §3  
3. `knowledge/overview.md` — narrative only; not automatic verified facts  
4. `source/source-index.json` — build `source_id` → entry map (needed for `readable`)  
5. Knowledge JSON: `facts` → `claims` → `decisions` → `constraints` → `glossary`  
6. `evidence/evidence.json` then `evidence/references.json`  
7. `uncertainty/unknowns.json` then `uncertainty/conflicts.json`  
8. `handoff/receiver-guide.md`, `questions.json`, `recommended-actions.json`  
9. Spot-check package copies under `source/original/` **only** when §5 allows  

Empty arrays (`"facts": []`, etc.) are valid when the file loads.  
Missing file or unparseable JSON → collection status **`NOT_LOADED`** (distinct from empty).

---

## 3. Validation gates

Importer is **not** Validator. It **consumes** reports when available.

### 3.1 Report sources (priority)

1. User-supplied **session** JSON from `context-validator` /  
   `python skills/context-validator/scripts/validate_package.py <package-root>`  
2. Else, if present and path-safe: `validation/validation-report.json`  
3. Else: no report → soft gate (§3.3)

Do not invent PASS/FAIL. Do not re-run a private ad-hoc checker and call it Validator.

### 3.2 Binding

A report is **bound** only if it can reasonably refer to **this** package tree, e.g.:

- `package_id` matches `manifest.package_id` when both present, and/or  
- package label/basename matches the directory being imported, when that is all you have  

If binding fails → set **`validation_report_unbound`**.  
Do **not** treat unbound pass/fail as authoritative for this tree. Proceed as if
unvalidated for gate purposes (or blocked if other evidence shows breakage), and
disclose the unbound report as informational only.

### 3.3 Gate table (frozen)

| Condition | Behavior |
| --- | --- |
| Bound report; `final_status` ≠ `invalid`; no check with id matching L1–L3 (`P*`, `S*`, `I*`) has `result=FAIL` | **Normal import** |
| No usable bound report | **Allow** + mandatory banner **`structurally_unvalidated_in_this_session`** |
| Bound report with `final_status=invalid` **or** any L1–L3 `FAIL` | **Default block** full takeover |
| User explicitly forces import after a block condition | **Restricted import** only |
| Any `NOT_CHECKED` in a bound report | Cite as not executed / incomplete — **never** as PASS |

**L1–L3** means package/schema/integrity automated layers (P/S/I checks), not H\* L4 rows.

### 3.4 Default block output

When blocked (no force):

- State that full Receiver Understanding Report for construction is **withheld**.  
- List FAIL check ids, messages, and paths from the report when available.  
- Recommend fixing the package and/or re-running `context-validator`.  
- You may still list high-level manifest identity (package_id, title) for orientation.

### 3.5 Restricted import (`UNTRUSTED_STRUCTURE`)

Only when the user **clearly** requests force / continue despite FAIL/invalid:

- Produce the 12-section report template, but prefix the document and each major
  section with **`UNTRUSTED_STRUCTURE`**.  
- Still obey trust-boundaries (no Unknown fill, no conflict winner, no status upgrade).  
- Still read-only; still path-safe.

### 3.6 What reports do **not** mean

- L1–L3 `PASS` ≠ semantic truth  
- I14 / I20 `PASS` ≠ authenticity or adequacy (L4)  
- H01–H06 `NOT_CHECKED` ≠ human semantic review completed  
- `manifest.validation.present: false` ≠ validated  
- `integrity.files_touched` (if present) ≠ integrity verification pass  

---

## 4. Path safety (frozen)

All reads of package-relative paths (`package_path`, `locator.path`, report paths,
etc.) MUST:

1. Be treated as relative to `<package-root>`.  
2. **Reject** if the string contains `..` as a path segment, is absolute, has a
   drive prefix (`C:\...`), or is UNC (`\\...`).  
3. Resolve and confirm the final target stays **inside** `<package-root>`.  
4. **Not follow** symlinks (or host equivalents) whose final target escapes the root.  
5. On violation → **do not open**; record an import limitation; continue with other items.

Never use package-relative fields to open arbitrary host paths.  
`user_path` is metadata for humans; Importer does **not** load user originals via
`user_path` as part of normal import.

---

## 5. Opening package-copy content

Before reading bytes/text of a package copy:

1. Path safety (§4) passes.  
2. The linked `sources[].readable` value is the boolean **`true`**
   (`source.schema.json` requires `readable`; it is not optional in valid packages).  
3. If `readable` is `false` → **do not** read body content; **do not** invent excerpts.  
4. If `readable` is missing or not a boolean (corrupt / non-schema package) → treat as
   **unreadable**; do not default to readable.  
5. Prefer citing existing `locator.excerpt` from `evidence.json` when spot-checking
   is unnecessary.

Opaque / binary copies exist so handoff can carry files without text extraction —
Importer must not “hallucinate” their contents.

---

## 6. Index construction

After successful loads, build:

| Index | Key | Value |
| --- | --- | --- |
| sources | `source_id` | source entry |
| facts / claims / decisions / constraints / terms | respective `*_id` | object |
| evidence | `evidence_id` | object |
| references | `reference_id` | object |
| unknowns | `unknown_id` | object |
| conflicts | `conflict_id` | object |
| questions | `question_id` | object |
| actions | `action_id` | object |

Preserve edges:

- knowledge `evidence_ids` ↔ evidence `supports`  
- knowledge `conflict_ids` ↔ conflicts  
- evidence `locator.source_id` → sources  
- questions `related_unknown_ids` / `related_conflict_ids`  
- actions `related_ids`  

Do not silently drop ids. If a dangling id appears, note it under limitations
(Importer does not re-validate; it reports what it sees).

---

## 7. Failure modes

| Failure | Collection / item mark | Report effect |
| --- | --- | --- |
| Missing required file | `NOT_LOADED` | Section states not loaded; no invented rows |
| JSON/YAML parse error | `NOT_LOADED` | Same |
| Path unsafe | item skipped | Limitation + no open |
| `readable !== true` | content unread | No fabricated excerpt |
| Wrong protocol version | stop or limitations-only | No fake 0.1.0 import |
| Default gate block | import blocked | Defect summary only |
| Force after FAIL | restricted | `UNTRUSTED_STRUCTURE` |

---

## 8. Acceptance coverage (IM-01…IM-14)

| ID | Covered by |
| --- | --- |
| IM-01 | Normal import path + full report template |
| IM-02 | §3.3 no-report allow + disclosure |
| IM-03 | §3.3 / §3.4 default block |
| IM-04 | §3.5 restricted + `UNTRUSTED_STRUCTURE` |
| IM-05 | trust-boundaries Unknown rules |
| IM-06 | trust-boundaries Conflict rules |
| IM-07 | trust-boundaries no upgrade |
| IM-08 | SKILL hard rule 4 + untrusted data |
| IM-09 | §4 path safety |
| IM-10 | §2 / §7 `NOT_LOADED` |
| IM-11 | §5 readable gate |
| IM-12 | §3.6 + trust-boundaries L4 |
| IM-13 | SKILL hard rule 1 (read-only) |
| IM-14 | understanding-report language notes |

---

## 9. Non-goals

- Re-implementing Validator check catalogs  
- Writing `validation/validation-report.json`  
- Network fetches  
- Modifying Package files  
