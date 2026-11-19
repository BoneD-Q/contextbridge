# CBHF 0.1.0 — Folder format (working definition)

**Status:** Working definition for ContextBridge first version.  
**Machine-readable schemas:** [`spec/cbhf/v0.1.0/`](../../../spec/cbhf/v0.1.0/) (JSON Schema Draft 2020-12).

Document roles (do not fork definitions):

| Document | Authority |
| --- | --- |
| **This file (`cbhf-format.md`)** | Human-readable field semantics, layout rules, and examples |
| **`spec/cbhf/v0.1.0/*.schema.json`** | Machine-readable field shapes / enums / nullability for structured JSON (and JSON-equivalent manifest) |
| [`claim-rules.md`](claim-rules.md) | Knowledge object classification + Knowledge Status judgment |
| [`evidence-rules.md`](evidence-rules.md) | Sources, locators, evidence links, redaction practice |
| [`../SKILL.md`](../SKILL.md) | Exporter execution workflow (must not contradict this file) |

If schema and this file disagree on **field shape**, update them together; do not silently fork. Cross-file / policy checks remain Validator-stage (not fully expressible in JSON Schema). If this file is silent on **judgment policy**, claim-rules / evidence-rules win.

Do not invent alternate top-level layouts or bump the protocol version.

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

- Do not claim byte-identity unless `content_transformed: false` (known identical). If identity is unknown → `content_transformed: null` (never invent `false`).
- **Redaction** (secret/PII masking) MUST be recorded in `manifest.redaction` (`applied: true` only when redaction ran) and summarized in `manifest.limitations`.
- Other copy transforms (encoding normalization, line-ending changes, etc.) affect `content_transformed` / `transform_reason` — they do **not** by themselves set `manifest.redaction.applied`.
- Best-effort redaction ≠ complete secret/PII discovery — never claim full coverage.
- If a file cannot be packaged safely, omit it, stop that file’s ingest, and tell the user.

### Host capability boundary

Skills hosts differ in read / write / copy support.

- Only files actually **read as text/extractable content** may back knowledge or evidence excerpts.
- Only files actually **copied** may appear under `source/original/`.
- **Copyable but unreadable binaries** (e.g. PDF/DOCX/image the host can copy but cannot extract text from): may be packaged as opaque copies with `readable: false`; must **not** yield `verified` knowledge, invented locators, or fabricated excerpts; record `manifest.limitations`.
- Uncopied paths → `manifest.limitations` (and Unknowns when material).
- Do not claim processing of unread PDF, DOCX, images, or other binaries.

### Package path safety

All exporter writes MUST stay inside `<package-root>/`.

1. Treat every package-relative path as relative to `<package-root>`; resolve and reject escape.
2. **Forbid** path segments `..`, absolute paths, drive prefixes (`C:\...`), and UNC paths in any package-relative field (`package_path`, locator `path`, `integrity.files_touched`, etc.).
3. Sanitize user-derived filenames when writing under `source/original/` (replace path separators with `__`; do not preserve directory escape).
4. **Do not follow symlinks** (or equivalent host links) that resolve outside `<package-root>` when creating or overwriting package files.
5. Never use package write APIs to modify user originals or any path outside the package root.
6. On violation → refuse that write, record `manifest.limitations`, and continue only with safe paths.

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
# Knowledge Status — facts, claims, decisions, constraints, glossary terms only
KnowledgeStatus = verified | user_confirmed | inferred | unverified | unknown | disputed

# Reference Status — evidence/references.json only (NOT KnowledgeStatus)
# 0.1.0 defined portable value:
ReferenceStatus = unverified
# Do NOT put KnowledgeStatus values (verified, user_confirmed, inferred, unknown, disputed)
# on references. Expanding ReferenceStatus is an open question — do not invent ad-hoc values.

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
  "source_ref": string | null,
  "confirmation_text": string | null,  # exact user wording for THIS proposition
  "confirmed_at": string | null,       # ISO-8601 UTC if known
  "limitations": string | null         # set when exact quote cannot be retained
}

# source_type meanings:
#   conversation         — user affirmed in the current agent session / chat
#   user_authored_source — affirmation text lives in a packaged user-authored file
#   other                — affirmation is attributed to the user but arrived via a
#                          channel that is neither this session nor a packaged
#                          user-authored source (e.g. user forwards their own prior
#                          note, paste from an external ticket without packaging it).
#                          MUST explain the channel in confirmation.limitations.
#                          MUST NOT invent a fake source_id.

# source_ref by source_type:
#   conversation         → null, or a non-sensitive host message id if available
#   user_authored_source → MUST be a source_id that exists in source-index.json
#   other                → null, or a short non-src_* label of the channel;
#                          MUST NOT be a source_id that does not exist;
#                          prefer null + limitations over a fabricated src_* id

Locator = {
  "source_id": string,
  "path": string,                # package-relative; usually source/original/...; no .. escape
  "locator_type": "line_range" | "section" | "json_pointer" | "anchor" | "page_range",
  "start": string | number | null,   # type depends on locator_type (see table below)
  "end": string | number | null,
  "excerpt": string              # short quote; redacted; <= 500 chars recommended
}
```

#### Locator `start` / `end` by `locator_type`

| `locator_type` | `start` | `end` |
| --- | --- | --- |
| `line_range` | number (1-based line) or null | number (1-based line) or null |
| `section` | **single** heading `string` or `null` | **single** heading `string` or `null` |
| `json_pointer` | JSON Pointer `string` or null | null (unused) or same pointer |
| `anchor` | anchor id `string` or null | null or end anchor `string` |
| `page_range` | number (page) or null | number (page) or null |

For `section`: do **not** use arrays, comma-joined multi-heading lists, or free-form path expressions in `start`/`end`. One heading string per field. If only a start heading is known, set `end: null`.

**Open point:** whether `page_range` is required for PDFs. Until decided: `line_range` for text; `page_range` when pages known; else `section` + excerpt. Unreadable / non-extractable PDFs must not back `verified` knowledge.

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
  # Optional inventory of package-relative paths the exporter wrote or intended to write.
  # NOT a checksum pass, NOT validator success, NOT proof of package completeness.
  files_touched: []
limitations:                         # REQUIRED — honest gaps / host limits
  - "design.pdf copied as opaque binary; text not extracted; readable=false."
  - "Redaction is best-effort; complete secret/PII discovery is not claimed."
redaction:
  applied: true                      # true ONLY if secret/PII redaction was performed
  policy: "default_secrets_and_pii"
  completeness: "best_effort"        # NEVER use a value that implies full coverage
  notes: "Masked token-like strings in src_001 copy and excerpts."
validation:
  present: false                     # exporter always leaves false / omits report
  report_path: null                  # set only by validator when validation/ exists
```

`manifest.redaction.applied`:

- `true` — exporter performed secret/PII redaction on one or more package texts/copies.
- `false` — no redaction pass was performed.
- Does **not** mean “any file transform occurred”. Encoding normalization or other non-redaction changes belong in `content_transformed` / `transform_reason`, not here.

`integrity.files_touched`:

- Optional list of package-relative paths written during export.
- Presence of paths does **not** mean integrity verification passed, hashes matched, or Validator ran.

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
    },
    {
      "source_id": "src_002",
      "original_name": "architecture.pdf",
      "user_path": null,
      "package_path": "source/original/architecture.pdf",
      "media_type": "application/pdf",
      "language": "und",
      "role": "supporting",
      "received_from": "user",
      "content_transformed": false,
      "transform_reason": "none",
      "readable": false,
      "notes": "Opaque binary copy only; text not extracted by host.",
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
| `original_name` | yes | User-facing filename (basename preferred) |
| `user_path` | no | Privacy-limited pointer to the user file; see below |
| `package_path` | yes | Safe path inside package (no `..` / absolute / symlink escape) |
| `media_type` | yes | Best-effort MIME |
| `language` | no | `zh` / `en` / `mixed` / `und` |
| `role` | yes | `primary` \| `supporting` \| `reference_material` |
| `received_from` | yes | `user` \| `workspace` \| `other` |
| `content_transformed` | yes | `true` \| `false` \| `null` — see below |
| `transform_reason` | no | e.g. `redaction`, `encoding_normalization`, `none`, `unknown` |
| `readable` | yes | `true` only if exporter extracted usable content; opaque binary copies use `false` |
| `checksum` | no | Prefer hashing the **package copy**; set `of: package_copy` |

#### `content_transformed`

| Value | When to use |
| --- | --- |
| `true` | Known: package copy bytes differ from the user file (e.g. redaction, normalization) |
| `false` | Known: package copy is byte-identical to the user file |
| `null` | **Unknown** whether bytes match — host cannot compare, copy path unclear, or comparison not performed. **Do not invent `false`.** |

`content_transformed` is about byte identity of the package copy vs the user file. It is independent of `manifest.redaction.applied` (though redaction usually implies `true` when redaction changed the copy).

#### `user_path` privacy

- Optional. Prefer `null` when the path adds little value.
- Prefer workspace-relative paths over absolute home paths.
- Do **not** store paths that embed secrets, tokens, personal directories you can avoid, or customer-sensitive folder names when a basename (`original_name`) suffices.
- If a path segment is sensitive, redact it or set `user_path` to `null` and note the limitation.
- `user_path` never authorizes modifying the user file.

#### Copyable but unreadable binaries

Allowed in `source/original/` when the host can copy bytes but cannot extract text:

- `readable: false`
- No evidence excerpts / line locators pretending to quote inner text
- No KnowledgeStatus `verified` derived from that file’s unread content
- `manifest.limitations` MUST mention the opaque packaging

Skipped / not-copied user files do **not** get a fake packaged entry; record them in `manifest.limitations` instead (optional future: a `skipped_sources` list — not required in 0.1.0).

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

`facts`, `claims`, `decisions`, `constraints`, and `glossary` terms **all** carry KnowledgeStatus `status`.  
Writing a row does **not** make it `verified`. Allowed statuses and judgment rules: [claim-rules.md](claim-rules.md).

When `status` is `user_confirmed`, `confirmation` is **required** (see `Confirmation` shared type above).

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

#### ReferenceStatus (independent of KnowledgeStatus)

| Value (0.1.0) | Meaning |
| --- | --- |
| `unverified` | Citation recorded as stated in sources; the referenced work was **not** obtained/checked inside this package. **Default and only defined portable value in 0.1.0.** |

Rules:

1. `references[].status` uses **ReferenceStatus**, not KnowledgeStatus.
2. Do **not** assign `verified`, `user_confirmed`, `inferred`, `unknown`, or `disputed` to a reference — those are KnowledgeStatus values and would be ambiguous here.
3. A real-looking URL does **not** upgrade ReferenceStatus.
4. Even if the user later packages the cited work as a source, knowledge claims still need their own evidence; do not overload ReferenceStatus to mean knowledge `verified` (additional ReferenceStatus values are an open question — do not invent them in exporters).

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
| 1 | Where is the normative schema published? | Human semantics: this file; machine shapes: `spec/cbhf/v0.1.0/*.schema.json` |
| 2 | Bilingual storage | Single files; `i18n.zh` / `i18n.en` + narrative bilingual sections |
| 3 | Fact vs Claim boundary | Facts = descriptive atoms; Claims = assertive/interpretive; prefer one canonical record |
| 4 | Checksum required? | Optional; hash package copy when available |
| 5 | PDF locators | `page_range` when known; else `section` + excerpt; unread/opaque PDF → `readable: false` + limitation |
| 6 | Confirmation without retained quote | Allowed with `confirmation_text: null` + `limitations` explaining why |
| 7 | Package root naming | User-chosen directory; stable id is `package_id` |
| 8 | `validation-report.json` schema | Deferred to Validator skill |
| 9 | `skipped_sources` formal list | Optional future; use `limitations` for now |
| 10 | Expand `ReferenceStatus` beyond `unverified`? | Deferred — do not invent ad-hoc values |
| 11 | Host message-id format for `confirmation.source_ref` | Optional opaque string; privacy-safe; else `null` |
| 12 | Closed enum for handoff `priority` (`questions` / `recommended-actions`)? | Example uses `high` only; Schema keeps `string` until enum is ratified |
