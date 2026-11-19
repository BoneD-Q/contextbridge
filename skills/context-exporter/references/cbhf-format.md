# CBHF 0.1.0 — Folder format (working definition)

**Status:** Working definition for ContextBridge first version.  
**Canonical path (future):** `spec/cbhf/v0.1.0/` (not yet filled). Until the spec directory is published, exporters/validators/importers MUST follow this document and must not invent alternate top-level layouts or bump the protocol version.

- **Scenario:** technical document handoff (`docs`)
- **Form:** standard folder (`folder`)
- **Protocol id:** `CBHF`
- **Protocol version:** `0.1.0`

## Package layout

### Exporter-required tree

```
<package-root>/
├── manifest.yaml
├── source/
│   ├── source-index.json
│   └── original/                 # package copies (NOT a guarantee of byte-identity with user files)
├── knowledge/
│   ├── overview.md
│   ├── facts.json
│   ├── claims.json
│   ├── decisions.json
│   ├── constraints.json
│   └── glossary.json
├── evidence/
│   ├── evidence.json
│   └── references.json
├── uncertainty/
│   ├── unknowns.json
│   └── conflicts.json
└── handoff/
    ├── receiver-guide.md
    ├── questions.json
    └── recommended-actions.json
```

### Validator-optional tree

```
<package-root>/
└── validation/                   # OPTIONAL — created by context-validator after a real run
    └── validation-report.json
```

Rules:

- `context-exporter` MUST write the Exporter-required tree.
- `context-exporter` MUST NOT create `validation/` or invent `validation-report.json`.
- Absence of `validation/` means “not validated yet”, not “validation passed”.
- Shape of `validation-report.json` is owned by the Validator skill (deferred). Exporter only acknowledges the path reservation.

All JSON files use UTF-8, 2-space indent preferred. YAML uses UTF-8.

### User originals vs `source/original/`

| Location | Meaning |
| --- | --- |
| User’s file on disk / chat paste source | **Read-only.** Never modified by exporter. |
| `source/original/` | **Package copy** used for handoff and locators. May differ from the user file after redaction or host-normalized writes. |

- Do not claim the package copy is byte-identical unless you know no transform occurred (`content_transformed: false`).
- Redaction MUST be recorded in `manifest.redaction` and summarized in `manifest.limitations`.
- Best-effort redaction ≠ complete secret/PII discovery — never claim full coverage.
- If a file cannot be packaged safely, omit it, stop that file’s ingest, and tell the user.

### Host capability boundary

Skills hosts differ in read / write / copy support.

- Only files actually read may be treated as known content.
- Only files actually copied may appear under `source/original/`.
- Unreadable or uncopied paths → `manifest.limitations` (and Unknowns when material).
- Do not claim processing of unread PDF, DOCX, images, or other binaries.

### ID conventions (0.1.0)

| Kind | Pattern | Example |
| --- | --- | --- |
| Package | `pkg_<slug>` | `pkg_api_gateway_design` |
| Source | `src_<nnn>` | `src_001` |
| Fact | `fact_<nnn>` | `fact_014` |
| Claim | `claim_<nnn>` | `claim_003` |
| Decision | `dec_<nnn>` | `dec_002` |
| Constraint | `con_<nnn>` | `con_010` |
| Term | `term_<nnn>` | `term_004` |
| Evidence | `ev_<nnn>` | `ev_021` |
| Reference | `ref_<nnn>` | `ref_007` |
| Unknown | `unk_<nnn>` | `unk_001` |
| Conflict | `cfl_<nnn>` | `cfl_001` |
| Question | `q_<nnn>` | `q_003` |
| Action | `act_<nnn>` | `act_002` |

Numbers are zero-padded to 3 digits within a package, unique per kind. Do not reuse IDs after deletion in the same export run.

### Shared field types

```text
Status = verified | user_confirmed | inferred | unverified | unknown | disputed

BilingualText = {
  "zh": string,    # Chinese; may be "" if not produced
  "en": string     # English; may be "" if not produced
}

LocalizedString = {
  "text": string,
  "lang": "zh" | "en" | "mixed" | "und",
  "i18n": BilingualText   # optional; default yes for bilingual packaging
}

# Optional but recommended on facts/claims/decisions/constraints when env/version matters.
KnowledgeContext = {
  "environment": "prod" | "staging" | "test" | "dev" | "local" | "unspecified" | null,
  "version": string | null,
  "time_range": string | null,   # free text / ISO interval if known
  "scope": string | null         # e.g. "api-gateway", "eu-region"
}

# REQUIRED when status == user_confirmed on any knowledge object.
Confirmation = {
  "confirmed_by": "user",
  "source_type": "conversation" | "user_authored_source" | "other",
  "source_ref": string | null,         # e.g. source_id, or null for live chat
  "confirmation_text": string | null,  # exact user wording for THIS proposition
  "confirmed_at": string | null,       # ISO-8601 UTC if known
  "limitations": string | null         # set when exact quote cannot be retained
}

Locator = {
  "source_id": string,
  "path": string,                # usually source/original/...
  "locator_type": "line_range" | "section" | "json_pointer" | "anchor" | "page_range",
  "start": string | number | null,
  "end": string | number | null,
  "excerpt": string              # short quote; redacted; <= 500 chars recommended
}
```

**Open point:** whether `page_range` is required for PDFs. Until decided: `line_range` for text; `page_range` when pages known; else `section` + excerpt. Unreadable PDFs must not be described as verified content.

---

## `manifest.yaml`

Required keys:

```yaml
cbhf_version: "0.1.0"
protocol: CBHF
package_id: pkg_example
title:
  zh: "示例交接包"
  en: "Example handoff package"
scenario: docs
package_form: folder
generated_at: "2026-11-19T03:00:00Z"   # ISO-8601 UTC
generator:
  skill: context-exporter
  skill_version: "0.1.0"
locale:
  narratives: ["zh", "en"]
  primary_source_lang: zh            # or en / mixed
sources_summary:
  count: 2
  source_ids: ["src_001", "src_002"]
integrity:
  files_touched: []                  # optional list of relative paths written
limitations:                         # REQUIRED — honest gaps / host limits
  - "design.pdf unread: host cannot extract text; not packaged as verified content."
  - "Redaction is best-effort; complete secret/PII discovery is not claimed."
redaction:
  applied: true                      # false if no transforms
  policy: "default_secrets_and_pii"
  completeness: "best_effort"        # NEVER use a value that implies full coverage
  notes: "Masked token-like strings in src_001 copy and excerpts."
validation:
  present: false                     # exporter always leaves false / omits report
  report_path: null                  # set only by validator when validation/ exists
```

Optional keys: `owners`, `tags`, `related_packages`, `notes`, `host_capabilities_notes`.  
Avoid unknown top-level keys — use `notes` until the formal spec freezes them.

---

## `source/source-index.json`

```json
{
  "sources": [
    {
      "source_id": "src_001",
      "original_name": "design.md",
      "user_path": "docs/design.md",
      "package_path": "source/original/design.md",
      "media_type": "text/markdown",
      "language": "zh",
      "role": "primary",
      "received_from": "user",
      "content_transformed": true,
      "transform_reason": "redaction",
      "readable": true,
      "notes": "Package copy redacted; user file left untouched.",
      "checksum": {
        "alg": "sha256",
        "value": null,
        "of": "package_copy"
      }
    }
  ]
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `source_id` | yes | Stable id |
| `original_name` | yes | User-facing filename |
| `user_path` | no | Path of the user file if known (not modified) |
| `package_path` | yes | Path inside package |
| `media_type` | yes | Best-effort MIME |
| `language` | no | `zh` / `en` / `mixed` / `und` |
| `role` | yes | `primary` \| `supporting` \| `reference_material` |
| `received_from` | yes | `user` \| `workspace` \| `other` |
| `content_transformed` | yes | `true` if package copy ≠ user bytes (redaction/normalization) |
| `transform_reason` | no | e.g. `redaction`, `encoding_normalization`, `none` |
| `readable` | yes | Whether exporter actually read content |
| `checksum` | no | Prefer hashing the **package copy**; set `of: package_copy` |

Skipped / unreadable user files do **not** get a fake packaged entry; record them in `manifest.limitations` instead (optional future: a `skipped_sources` list — not required in 0.1.0).

---

## `knowledge/overview.md`

Markdown, bilingual sections required:

```markdown
# Overview / 概览

## English
...

## 中文
...

## Scope / 范围
...

## Non-goals / 非目标
...

## How to read this package / 如何阅读本交接包
...
```

Do not put disputed resolutions here. Link to unknowns/conflicts by id in prose if helpful. State that `source/original/` are package copies.

---

## Status field (all structured knowledge)

`facts`, `claims`, `decisions`, `constraints`, and `glossary` terms **all** carry `status`.  
Writing a row does **not** make it `verified`. Allowed statuses and judgment rules: [claim-rules.md](claim-rules.md).

When `status` is `user_confirmed`, `confirmation` is **required**.

Optional `context` (`KnowledgeContext`) SHOULD be filled when environment/version/time/scope affects meaning or conflict detection.

---

## `knowledge/facts.json`

```json
{
  "facts": [
    {
      "fact_id": "fact_001",
      "statement": {
        "text": "生产环境服务默认监听 8080 端口。",
        "lang": "zh",
        "i18n": {
          "zh": "生产环境服务默认监听 8080 端口。",
          "en": "In production, the service listens on port 8080 by default."
        }
      },
      "context": {
        "environment": "prod",
        "version": null,
        "time_range": null,
        "scope": "api-gateway"
      },
      "status": "verified",
      "evidence_ids": ["ev_001"],
      "confirmation": null,
      "conflict_ids": [],
      "tags": ["runtime"],
      "notes": ""
    }
  ]
}
```

Facts must not contain prescriptions (“should”, “must”) — those belong in `constraints` or `decisions`.

---

## `knowledge/claims.json`

```json
{
  "claims": [
    {
      "claim_id": "claim_001",
      "statement": {
        "text": "当前瓶颈在数据库连接池。",
        "lang": "zh",
        "i18n": {
          "zh": "当前瓶颈在数据库连接池。",
          "en": "The current bottleneck is the DB connection pool."
        }
      },
      "context": {
        "environment": "unspecified",
        "version": null,
        "time_range": null,
        "scope": null
      },
      "status": "inferred",
      "kind": "interpretation",
      "evidence_ids": ["ev_004"],
      "related_fact_ids": ["fact_010"],
      "confirmation": null,
      "conflict_ids": [],
      "notes": "Inference: derived from latency table; not explicitly stated."
    }
  ]
}
```

`kind`: `assertion` | `interpretation` | `prediction` | `requirement_claim` | `other`.

---

## `knowledge/decisions.json`

```json
{
  "decisions": [
    {
      "decision_id": "dec_001",
      "summary": {
        "text": "采用文件夹交接而非单一 JSON 包。",
        "lang": "zh",
        "i18n": {
          "zh": "采用文件夹交接而非单一 JSON 包。",
          "en": "Use a folder handoff instead of a single JSON bundle."
        }
      },
      "context": {
        "environment": null,
        "version": "0.1.0",
        "time_range": null,
        "scope": "contextbridge"
      },
      "status": "user_confirmed",
      "confirmation": {
        "confirmed_by": "user",
        "source_type": "conversation",
        "source_ref": null,
        "confirmation_text": "就按文件夹交接，不要做成单个 JSON 包。",
        "confirmed_at": null,
        "limitations": null
      },
      "rationale": {
        "text": "便于保留原始文件与分段阅读。",
        "lang": "zh",
        "i18n": {
          "zh": "便于保留原始文件与分段阅读。",
          "en": "Easier to keep originals and read in sections."
        }
      },
      "evidence_ids": [],
      "conflict_ids": [],
      "date": null,
      "supersedes": [],
      "notes": ""
    }
  ]
}
```

---

## `knowledge/constraints.json`

```json
{
  "constraints": [
    {
      "constraint_id": "con_001",
      "statement": {
        "text": "不得引入独立 Web 服务。",
        "lang": "zh",
        "i18n": {
          "zh": "不得引入独立 Web 服务。",
          "en": "Must not introduce a standalone web service."
        }
      },
      "context": {
        "environment": null,
        "version": "0.1.0",
        "time_range": null,
        "scope": "contextbridge"
      },
      "status": "verified",
      "priority": "must",
      "evidence_ids": ["ev_003"],
      "confirmation": null,
      "conflict_ids": [],
      "notes": ""
    }
  ]
}
```

`priority`: `must` | `should` | `may` | `must_not` | `unspecified`.

---

## `knowledge/glossary.json`

Terms also require `status`. Listing a term does **not** mean it is `verified`.

```json
{
  "terms": [
    {
      "term_id": "term_001",
      "term": "CBHF",
      "definition": {
        "text": "ContextBridge Handoff Format",
        "lang": "en",
        "i18n": {
          "zh": "ContextBridge 交接格式",
          "en": "ContextBridge Handoff Format"
        }
      },
      "status": "verified",
      "aliases": ["ContextBridge Handoff Format"],
      "evidence_ids": ["ev_012"],
      "confirmation": null,
      "conflict_ids": [],
      "notes": ""
    }
  ]
}
```

If a definition is exporter-synthesized without a source span → `inferred` or `unverified`, never `verified`.

---

## `evidence/evidence.json`

```json
{
  "evidence": [
    {
      "evidence_id": "ev_001",
      "kind": "excerpt",
      "locator": {
        "source_id": "src_001",
        "path": "source/original/design.md",
        "locator_type": "line_range",
        "start": 42,
        "end": 45,
        "excerpt": "生产环境服务默认监听 8080 端口。"
      },
      "supports": [
        { "type": "fact", "id": "fact_001" }
      ],
      "redaction_applied": false,
      "notes": ""
    }
  ]
}
```

`kind`: `excerpt` | `table_cell` | `figure_caption` | `metadata` | `user_message` | `other`.  
`supports[].type`: `fact` | `claim` | `decision` | `constraint` | `term`.

Bidirectional consistency required between `evidence_ids` and `supports`.

If `redaction_applied` (or package-copy redaction) damages meaning/locatability → downgrade supported objects; do not keep `verified`.

---

## `evidence/references.json`

```json
{
  "references": [
    {
      "reference_id": "ref_001",
      "title": "RFC 9110",
      "raw_citation": "RFC 9110 HTTP Semantics",
      "url": null,
      "mentioned_in": ["src_001"],
      "status": "unverified",
      "notes": "Listed in source; not fetched."
    }
  ]
}
```

Reference `status` here means citation-check status (usually `unverified`), **not** knowledge verification by URL shape alone.

---

## `uncertainty/unknowns.json`

```json
{
  "unknowns": [
    {
      "unknown_id": "unk_001",
      "question": {
        "text": "生产环境的实际副本数是多少？",
        "lang": "zh",
        "i18n": {
          "zh": "生产环境的实际副本数是多少？",
          "en": "What is the actual production replica count?"
        }
      },
      "why_it_matters": {
        "text": "影响容量与故障切换描述。",
        "lang": "zh",
        "i18n": {
          "zh": "影响容量与故障切换描述。",
          "en": "Affects capacity and failover description."
        }
      },
      "related_ids": ["claim_008"],
      "suggested_owner": "user",
      "notes": ""
    }
  ]
}
```

Use Unknowns (and/or questions) when two statements **might** conflict but context alignment is unclear — do **not** emit a definitive Conflict in that case.

---

## `uncertainty/conflicts.json`

Create a Conflict **only if all** are true:

1. Same subject / object of discourse  
2. Context (environment, version, time, scope, …) is the same or explicitly identical  
3. The two statements cannot both be true  

Otherwise: question / unknown — not a conflict.

```json
{
  "conflicts": [
    {
      "conflict_id": "cfl_001",
      "summary": {
        "text": "同一生产环境下监听端口互斥：8080 vs 8000。",
        "lang": "zh",
        "i18n": {
          "zh": "同一生产环境下监听端口互斥：8080 vs 8000。",
          "en": "Mutually exclusive production listen ports: 8080 vs 8000."
        }
      },
      "same_subject": true,
      "context_alignment": "same",
      "shared_context": {
        "environment": "prod",
        "version": null,
        "time_range": null,
        "scope": "api-gateway"
      },
      "parties": [
        { "type": "fact", "id": "fact_001", "stance": "8080" },
        { "type": "fact", "id": "fact_002", "stance": "8000" }
      ],
      "evidence_ids": ["ev_001", "ev_009"],
      "resolution": null,
      "notes": "Do not auto-resolve."
    }
  ]
}
```

`context_alignment`: `same` | `different` | `uncertain`.  
Only `same` (with `same_subject: true` and mutual exclusion) yields a Conflict row.  
If `uncertain` → do not write this file entry; use `questions.json` / `unknowns.json` instead.

`resolution` remains `null` unless the user explicitly resolves it; then follow claim-rules for status updates. Exporter never invents a resolution.

**Non-example:** test port `8000` vs prod port `8080` → `context_alignment: different` → **no** Conflict.

---

## `handoff/receiver-guide.md`

Bilingual operator guide. Must include:

1. Package purpose  
2. Trust boundaries (`verified` vs `user_confirmed` vs `inferred`, etc.)  
3. User originals are untouched; `source/original/` are package copies  
4. How to use unknowns/conflicts (and that env mismatches ≠ conflicts)  
5. Limitations / redaction best-effort caveat  
6. That missing `validation/` means not yet validated  

Structure with `## English` and `## 中文` sections.

---

## `handoff/questions.json`

```json
{
  "questions": [
    {
      "question_id": "q_001",
      "ask": {
        "text": "两处端口描述是否针对同一环境？若是，以哪份文档为准？",
        "lang": "zh",
        "i18n": {
          "zh": "两处端口描述是否针对同一环境？若是，以哪份文档为准？",
          "en": "Do the two port statements refer to the same environment? If so, which document is authoritative?"
        }
      },
      "priority": "high",
      "related_conflict_ids": [],
      "related_unknown_ids": ["unk_002"],
      "notes": "Context alignment uncertain — not recorded as a conflict."
    }
  ]
}
```

---

## `handoff/recommended-actions.json`

```json
{
  "actions": [
    {
      "action_id": "act_001",
      "action": {
        "text": "请用户确认两处端口是否同一环境；若是，确认权威值。",
        "lang": "zh",
        "i18n": {
          "zh": "请用户确认两处端口是否同一环境；若是，确认权威值。",
          "en": "Ask the user whether both port statements share one environment; if so, confirm the authoritative value."
        }
      },
      "priority": "high",
      "status": "pending",
      "related_ids": ["q_001", "unk_002"],
      "notes": "Not performed by exporter."
    }
  ]
}
```

Action `status`: `pending` | `blocked` | `cancelled`. Never mark export-time suggestions completed.  
Do not use action status values from knowledge `Status`.

---

## `validation/validation-report.json`

- **Optional** path reserved for `context-validator`.  
- Not an Exporter output.  
- Schema deferred until Validator work begins.  
- Exporter must set `manifest.validation.present: false` (or equivalent honesty in limitations) and must not claim a full validation pass.

---

## Empty collections

If a category has no items, write the file with an empty array under its standard key, e.g. `{ "conflicts": [] }`. Do not omit Exporter-required files. Omit `validation/` entirely when not validated.

## Open questions (do not fork the layout)

| # | Ambiguity | Recommendation for 0.1.0 |
| --- | --- | --- |
| 1 | Where is the normative schema published? | This file until mirrored into `spec/cbhf/v0.1.0/` |
| 2 | Bilingual storage | Single files; `i18n.zh` / `i18n.en` + narrative bilingual sections |
| 3 | Fact vs Claim boundary | Facts = descriptive atoms; Claims = assertive/interpretive; prefer one canonical record |
| 4 | Checksum required? | Optional; hash package copy when available |
| 5 | PDF locators | `page_range` when known; else `section` + excerpt; unread PDF → limitation |
| 6 | Confirmation without retained quote | Allowed with `confirmation_text: null` + `limitations` explaining why |
| 7 | Package root naming | User-chosen directory; stable id is `package_id` |
| 8 | `validation-report.json` schema | Deferred to Validator skill |
| 9 | `skipped_sources` formal list | Optional future; use `limitations` for now |
