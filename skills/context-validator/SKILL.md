---
name: context-validator
description: >
  Read-only validation of a CBHF 0.1.0 handover folder for package structure,
  schema shape, referential integrity, and semantic-review prompts. Use when
  checking a ContextBridge package before import or distribution, or when the
  user asks to run context-validator. Does not invent validation passes or
  rewrite package knowledge.
license: Apache-2.0
metadata:
  author: contextbridge
  version: "0.1.0"
  protocol: CBHF
  protocol_version: "0.1.0"
---

# context-validator

Read-only validation of a **CBHF 0.1.0** folder package.

This Skill is **instructions first**. Deterministic Python helpers under `scripts/` support L1/L2 and **L3-A** (cross-file references). L3-B/C and L4 are not automated yet. Helpers are **not** a standalone product CLI.

Design authority: [`docs/context-validator-design.zh-CN.md`](../../docs/context-validator-design.zh-CN.md).  
Protocol / schemas: `skills/context-exporter/references/cbhf-format.md` and `spec/cbhf/v0.1.0/*.schema.json`.

Before validating, read:

1. [references/validation-rules.md](references/validation-rules.md) — L1/L2/L3 check catalog  
2. [references/report-format.md](references/report-format.md) — session report shape  
3. [references/semantic-review-boundary.md](references/semantic-review-boundary.md) — L4: never auto semantic PASS  

## When to use

- User asks to validate / check a CBHF or ContextBridge handoff package  
- User names this skill: `context-validator`  
- Before import/distribution when structural honesty matters  

Do **not** use this skill to export packages (`context-exporter`) or to import/resume work (`context-importer`).  
Do **not** rename or treat `tests/schema/v0.1.0/package_smoke_test.py` as this Skill.

## Hard rules (non-negotiable)

1. **Read-only on package knowledge.** Do not modify facts, claims, evidence, sources under `source/original/`, or other Exporter-required content while validating.  
2. **No forged results.** Never invent PASS/FAIL. If a check was not executed, mark `NOT_CHECKED`.  
3. **No semantic auto-PASS.** L4 items are `NEEDS_HUMAN_REVIEW` or `NOT_CHECKED` only — never “semantic PASS”.  
4. **No protocol invention.** Do not add CBHF fields or bump version.  
5. **Default: session report only.** Do not write `validation/validation-report.json` or flip `manifest.validation` (Phase 2 script never writes the package).  
6. **Smoke ≠ Validator.** `package_smoke_test.py` remains a developer smoke test; do not present smoke output as a formal Validator pass.  
7. **Privacy.** Prefer package basename / relative labels in reports; avoid dumping home/user absolute paths.

## Capability honesty (Phase 3B-B2)

| Layer | Defined in references? | Automated in this Phase? |
| --- | --- | --- |
| L1 Package | Yes | **Yes** — `scripts/validate_package.py` (P01–P07) |
| L2 Schema | Yes | **Yes** — same script (S01–S15), local Draft 2020-12 only |
| L3-A References | Yes | **Yes** — I01–I09, I15, I17–I19 via `_integrity.py` |
| L3-B1 Path safety / exists | Yes | **Yes** — I11, I10 |
| L3-B2 readable:false | Yes | **Yes** — I16 (Option C) |
| L3-B/C remaining | Yes | **No** — I12, I13, I14, I20 → `NOT_CHECKED` |
| L4 Semantic boundary | Yes | **Never** automated PASS — H\* → `NOT_CHECKED` |

Writing a check ID in references does **not** mean it is automated unless this table says so.

## Inputs

| Input | Required | Notes |
| --- | --- | --- |
| Package root | Yes | Directory that should contain `manifest.yaml` (CBHF folder form) |
| Protocol expectation | Default 0.1.0 | Read `manifest.cbhf_version` / `protocol` |
| Write report into package? | No | Default **no** (script cannot write) |

If the path is unreadable, stop and report. Do not fabricate a package.

## Identify protocol version

1. Confirm `manifest.yaml` exists at package root.  
2. Read `cbhf_version` and `protocol`.  
3. For this Skill version, only **CBHF `0.1.0`** is in scope.  
4. If version missing/unsupported → package-level outcome biased to `invalid` / fail identification checks; do not pretend 0.1.0 rules apply blindly without noting the mismatch.

## Workflow

Execute in order. Do not skip layers by inventing PASS.

### 0. Plan (read-only)

- Resolve package root.  
- Open references listed above.  
- Declare Phase 3B-B2 limits: L1+L2+L3-A+B1+B2 (I16) automated; I12/I13/I14/I20 and L4 not implemented.

### 1. Run deterministic helper (preferred)

From the repository root (or any cwd), invoke:

```text
python skills/context-validator/scripts/validate_package.py <package-root>
```

Optional: `--schema-dir` pointing at a **local** `spec/cbhf/v0.1.0` copy — never download schemas.

The script prints a **session JSON report** to stdout and:

- Does not modify the package  
- Does not create `validation/`  
- Does not follow escaping symlinks into package trees  
- Marks L3/L4 checks `NOT_CHECKED`  

Interpret the JSON using [report-format.md](references/report-format.md).

If the script cannot run, fall back to manual L1/L2 inspection and mark unavailable checks `NOT_CHECKED`.

### 2. L1 — Package Validation

Follow **P01–P07** in [validation-rules.md](references/validation-rules.md). Prefer the script results.

### 3. L2 — Schema Validation

Follow **S01–S15**. Prefer the script results against `spec/cbhf/v0.1.0/`.

If a file failed L1 parse/existence, dependent S\* checks must be `NOT_CHECKED` (not PASS).

### 4. L3 — Integrity Validation

- **L3-A (implemented):** I01–I09, I15, I17–I19 — use script results.  
- **L3-B1 (implemented):** I11 path safety, I10 path exists.  
- **L3-B2 (implemented):** I16 readable:false (Option C) — use script results.  
- **L3-B/C remaining:** I12, I13, I14, I20 → `NOT_CHECKED`.  
Do not invent line_range / I14 excerpt-match PASS/FAIL yet. Do not treat L3 PASS as semantic adequacy.

### 5. L4 — Semantic Review Boundary

Follow [semantic-review-boundary.md](references/semantic-review-boundary.md) if the user asks for human prompts.  
Phase 2 script leaves H01–H06 as `NOT_CHECKED`.  
**Never** conclude “semantic validation passed”.

### 6. Compose session report

Use script JSON and/or [report-format.md](references/report-format.md):

- Per-check results  
- Layer summaries  
- Package-level status (separate from per-check)  
- Limitations / NOT_CHECKED list  

### 7. Finish

- Confirm package knowledge files were not modified.  
- Do not claim L3/L4 automation.  
- Suggest Importer only after the user accepts structural risks and remaining NOT_CHECKED items.

## Handling outcomes

| Situation | Package-level status (see report-format) |
| --- | --- |
| Any L1/L2 `FAIL` | `invalid` — list failures with locations |
| L1/L2 complete with only `WARNING` but L3 not run | Prefer `not_fully_validated` (Phase 2 honesty) |
| Important L1/L2 checks `NOT_CHECKED` | `not_fully_validated` |
| L1/L2 OK, L3/L4 unfinished | `not_fully_validated` / `semantically_unreviewed` as appropriate — **never** semantic PASS |
| User wants package write | Refuse writing formal report into package in Phase 2 |

## Out of scope (Phase 2)

- L3 Integrity automation  
- L4 automatic semantic judgment  
- CLI / Web / DB / MCP products  
- Changing CBHF schemas or Exporter rules  
- Editing `EXPECTED.md`, `generated-output`, inputs, or prior semantic-review conclusions  
- Freezing validation-report Schema  
- Renaming smoke test to Validator  
