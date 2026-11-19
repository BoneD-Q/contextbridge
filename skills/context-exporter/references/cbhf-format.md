# CBHF 0.1.0 — 文件夹格式（工作定义）

**状态：** ContextBridge 首版工作定义。
**机器可读 schema：** [`spec/cbhf/v0.1.0/`](../../../spec/cbhf/v0.1.0/)（JSON Schema Draft 2020-12）。

文档角色（不得分叉定义）：

| 文档 | 权威性 |
| --- | --- |
| **本文件（`cbhf-format.md`）** | 人工可读字段语义、布局规则与示例 |
| **`spec/cbhf/v0.1.0/*.schema.json`** | 结构化 JSON（及 JSON 等价 manifest）的机器可读字段形态 / 枚举 / 可空性 |
| [`claim-rules.md`](claim-rules.md) | 知识对象分类 + 知识状态（Knowledge Status）判定 |
| [`evidence-rules.md`](evidence-rules.md) | 来源、定位器、证据链接、脱敏实践 |
| [`../SKILL.md`](../SKILL.md) | Exporter 执行工作流（不得与本文件冲突） |

若 schema 与本文件在**字段形态**上不一致，须一并更新；不得静默分叉。跨文件 / 策略检查仍属 Validator 阶段（无法完全用 JSON Schema 表达）。若本文件对**判定策略**沉默，则以 claim-rules / evidence-rules 为准。

不得发明替代顶层布局或抬升协议版本。

- **场景（Scenario）：** 技术文档交接（`docs`）
- **形态（Form）：** 标准文件夹（`folder`）
- **协议 id：** `CBHF`
- **协议版本：** `0.1.0`

## 包布局

### Exporter 必需树

```
<package-root>/
├── manifest.yaml
├── source/
│   ├── source-index.json
│   └── original/                 # 包内副本（并不保证与用户文件字节同一）
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

### Validator 可选树

```
<package-root>/
└── validation/                   # 可选 — 由 context-validator 在真实运行后创建
    └── validation-report.json
```

规则：

- `context-exporter` **必须**写入 Exporter 必需树。
- `context-exporter` **不得**创建 `validation/` 或捏造 `validation-report.json`。
- 缺少 `validation/` 表示“尚未校验”，而非“校验已通过”。
- `validation-report.json` 的形态由 Validator skill 拥有（延后）。Exporter 仅承认该路径预留。

所有 JSON 文件使用 UTF-8，建议 2 空格缩进。YAML 使用 UTF-8。

### 用户原件 vs `source/original/`

| 位置 | 含义 |
| --- | --- |
| 用户磁盘文件 / 聊天粘贴来源 | **只读。** Exporter 永不修改。 |
| `source/original/` | 用于交接与定位器的**包内副本**。脱敏或宿主规范化写入后可能与用户文件不同。 |

- 除非 `content_transformed: false`（已知同一），否则不得声称字节同一。若同一性未知 → `content_transformed: null`（不得捏造 `false`）。
- **脱敏**（密钥/PII 掩码）**必须**记录在 `manifest.redaction`（仅在实际脱敏时 `applied: true`），并在 `manifest.limitations` 中摘要。
- 其他副本变换（编码规范化、换行变更等）影响 `content_transformed` / `transform_reason`——它们**本身不会**设置 `manifest.redaction.applied`。
- 尽力脱敏 ≠ 完整密钥/PII 发现——不得声称全覆盖。
- 若某文件无法安全打包，省略之，停止该文件摄入，并告知用户。

### 宿主能力边界

Skills 宿主在读 / 写 / 复制支持上存在差异。

- 仅实际**作为文本/可提取内容读取**的文件可作为知识或证据摘录的依据。
- 仅实际**已复制**的文件可出现在 `source/original/` 下。
- **可复制但不可读的二进制**（例如宿主能复制但无法提取文本的 PDF/DOCX/图片）：可以不透明副本打包且 `readable: false`；**不得**产出 `verified` 知识、捏造定位器或伪造摘录；须记入 `manifest.limitations`。
- 未复制路径 → `manifest.limitations`（重要时加 Unknowns）。
- 不得声称处理了未读 PDF、DOCX、图片或其他二进制。

### 包路径安全

Exporter 的所有写入**必须**留在 `<package-root>/` 内。

1. 将每个包相对路径视为相对 `<package-root>`；解析并拒绝逃逸。
2. **禁止**在任何包相对字段（`package_path`、定位器 `path`、`integrity.files_touched` 等）中出现路径段 `..`、绝对路径、盘符前缀（`C:\...`）与 UNC 路径。
3. 写入 `source/original/` 时净化用户派生文件名（路径分隔符替换为 `__`；不保留目录逃逸）。
4. 创建或覆盖包文件时，**不得跟随**解析到 `<package-root>` 外的符号链接（或等价宿主链接）。
5. 不得用包写入 API 修改用户原件或包根外的任何路径。
6. 违规时 → 拒绝该次写入，记入 `manifest.limitations`，仅继续安全路径。

### ID 约定（0.1.0）

| 种类 | 模式 | 示例 |
| --- | --- | --- |
| 包（Package） | `pkg_<slug>` | `pkg_api_gateway_design` |
| 来源（Source） | `src_<nnn>` | `src_001` |
| 事实（Fact） | `fact_<nnn>` | `fact_014` |
| 主张（Claim） | `claim_<nnn>` | `claim_003` |
| 决策（Decision） | `dec_<nnn>` | `dec_002` |
| 约束（Constraint） | `con_<nnn>` | `con_010` |
| 术语（Term） | `term_<nnn>` | `term_004` |
| 证据（Evidence） | `ev_<nnn>` | `ev_021` |
| 引用（Reference） | `ref_<nnn>` | `ref_007` |
| 未知（Unknown） | `unk_<nnn>` | `unk_001` |
| 冲突（Conflict） | `cfl_<nnn>` | `cfl_001` |
| 问题（Question） | `q_<nnn>` | `q_003` |
| 动作（Action） | `act_<nnn>` | `act_002` |

编号在包内按种类零填充至 3 位且唯一。同一次导出中删除后不得复用 ID。

### 共享字段类型

```text
# Knowledge Status — 仅用于 facts、claims、decisions、constraints、glossary terms
KnowledgeStatus = verified | user_confirmed | inferred | unverified | unknown | disputed

# Reference Status — 仅用于 evidence/references.json（不是 KnowledgeStatus）
# 0.1.0 已定义的可移植值：
ReferenceStatus = unverified
# 不得将 KnowledgeStatus 值（verified、user_confirmed、inferred、unknown、disputed）
# 写到 references 上。扩展 ReferenceStatus 属开放问题 — 不得发明临时值。

BilingualText = {
  "zh": string,    # 中文；未产出时可为 ""
  "en": string     # 英文；未产出时可为 ""
}

LocalizedString = {
  "text": string,
  "lang": "zh" | "en" | "mixed" | "und",
  "i18n": BilingualText   # 可选；双语打包时默认有
}

# 当环境/版本相关时，facts/claims/decisions/constraints 上可选但建议填写。
KnowledgeContext = {
  "environment": "prod" | "staging" | "test" | "dev" | "local" | "unspecified" | null,
  "version": string | null,
  "time_range": string | null,   # 自由文本 / 已知时用 ISO interval
  "scope": string | null         # 例如 "api-gateway"、"eu-region"
}

# 任一知识对象 status == user_confirmed 时必需。
Confirmation = {
  "confirmed_by": "user",
  "source_type": "conversation" | "user_authored_source" | "other",
  "source_ref": string | null,
  "confirmation_text": string | null,  # 针对本命题的用户原话
  "confirmed_at": string | null,       # 已知时为 ISO-8601 UTC
  "limitations": string | null         # 无法保留原话时设置
}

# source_type 含义：
#   conversation         — 用户在当前 agent 会话 / 聊天中肯定
#   user_authored_source — 肯定文本位于已打包的用户撰写文件
#   other                — 肯定归属于用户，但渠道既非本会话也非已打包
#                          用户撰写来源（例如用户转发自己的旧笔记，或从外部
#                          工单粘贴且未打包该工单）。
#                          必须在 confirmation.limitations 中说明渠道。
#                          不得捏造假 source_id。

# 按 source_type 的 source_ref：
#   conversation         → null，或可用时的非敏感宿主消息 id
#   user_authored_source → 必须是 source-index.json 中存在的 source_id
#   other                → null，或渠道的短非 src_* 标签；
#                          不得为不存在的 source_id；
#                          优先 null + limitations，而非伪造 src_* id

Locator = {
  "source_id": string,
  "path": string,                # 包相对；通常 source/original/...；无 .. 逃逸
  "locator_type": "line_range" | "section" | "json_pointer" | "anchor" | "page_range",
  "start": string | number | null,   # 类型取决于 locator_type（见下表）
  "end": string | number | null,
  "excerpt": string              # 短引用；已脱敏；建议 <= 500 字符
}
```

#### 定位器 `start` / `end` 按 `locator_type`

| `locator_type` | `start` | `end` |
| --- | --- | --- |
| `line_range` | number（1-based 行号）或 null | number（1-based 行号）或 null |
| `section` | **单个**标题 `string` 或 `null` | **单个**标题 `string` 或 `null` |
| `json_pointer` | JSON Pointer `string` 或 null | null（未用）或同一 pointer |
| `anchor` | 锚点 id `string` 或 null | null 或结束锚点 `string` |
| `page_range` | number（页码）或 null | number（页码）或 null |

对 `section`：**不要**在 `start`/`end` 中使用数组、逗号拼接的多标题列表或自由路径表达式。每个字段一个标题字符串。若仅知起始标题，设 `end: null`。

**开放点：** `page_range` 是否对 PDF 必需。在决定前：文本用 `line_range`；页码已知时用 `page_range`；否则 `section` + excerpt。不可读 / 不可提取的 PDF 不得支撑 `verified` 知识。

---

## `manifest.yaml`

必需键：

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
  primary_source_lang: zh            # 或 en / mixed
sources_summary:
  count: 2
  source_ids: ["src_001", "src_002"]
integrity:
  # 可选：Exporter 已写入或打算写入的包相对路径清单。
  # 不是 checksum 通过，不是 validator 成功，也不是包完整性证明。
  files_touched: []
limitations:                         # 必需 — 诚实的缺口 / 宿主限制
  - "design.pdf 以不透明二进制复制；未提取文本；readable=false。"
  - "脱敏为尽力而为；不声称已完整发现密钥/PII。"
redaction:
  applied: true                      # 仅在实际执行了密钥/PII 脱敏时为 true
  policy: "default_secrets_and_pii"
  completeness: "best_effort"        # 切勿使用暗示全覆盖的值
  notes: "已在 src_001 副本与摘录中掩码类令牌字符串。"
validation:
  present: false                     # exporter 始终为 false / 省略 report
  report_path: null                  # 仅在 validation/ 存在时由 validator 设置
```

`manifest.redaction.applied`：

- `true` — Exporter 对一份或多份包内文本/副本执行了密钥/PII 脱敏。
- `false` — 未执行脱敏遍。
- **不**表示“发生了任何文件变换”。编码规范化或其他非脱敏变更属于 `content_transformed` / `transform_reason`，不在此处。

`integrity.files_touched`：

- 导出期间写入的包相对路径可选列表。
- 路径存在**不**表示完整性核验通过、哈希匹配或 Validator 已运行。

可选键：`owners`、`tags`、`related_packages`、`notes`、`host_capabilities_notes`。
避免未知顶层键——正式规范冻结前放入 `notes`。

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
      "notes": "包内副本已脱敏；用户原件未动。",
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
      "notes": "仅不透明二进制副本；宿主未提取文本。",
      "checksum": {
        "alg": "sha256",
        "value": null,
        "of": "package_copy"
      }
    }
  ]
}
```

| 字段 | 必需 | 含义 |
| --- | --- | --- |
| `source_id` | 是 | 稳定 id |
| `original_name` | 是 | 面向用户的文件名（优先 basename） |
| `user_path` | 否 | 指向用户文件的隐私受限指针；见下文 |
| `package_path` | 是 | 包内安全路径（无 `..` / 绝对路径 / 符号链接逃逸） |
| `media_type` | 是 | 尽力 MIME |
| `language` | 否 | `zh` / `en` / `mixed` / `und` |
| `role` | 是 | `primary` \| `supporting` \| `reference_material` |
| `received_from` | 是 | `user` \| `workspace` \| `other` |
| `content_transformed` | 是 | `true` \| `false` \| `null` — 见下文 |
| `transform_reason` | 否 | 例如 `redaction`、`encoding_normalization`、`none`、`unknown` |
| `readable` | 是 | 仅当 Exporter 提取了可用内容时为 `true`；不透明二进制副本用 `false` |
| `checksum` | 否 | 可选。为与 CBHF 0.1.0 Validator I20 对齐而出现时：`alg` 必须恰好为 `sha256`（无默认）；`of` 必须恰好为 `package_copy`（无默认）；`value` 为 `null`/省略/空（**无适用校验和**）或恰好 **64 位十六进制**字符（A–F/a–f；比较时小写）。对 `package_path` 处包内副本文件的**精确原始字节**哈希。缺失/不支持的 `alg` 或 `of` **不得**静默默认。宿主**不**被要求发出校验和。 |

#### `content_transformed`

| 取值 | 何时使用 |
| --- | --- |
| `true` | 已知：包内副本字节与用户文件不同（例如脱敏、规范化） |
| `false` | 已知：包内副本与用户文件字节同一 |
| `null` | **未知**字节是否匹配——宿主无法比较、复制路径不清或未做比较。**不得捏造 `false`。** |

`content_transformed` 关乎包内副本相对用户文件的字节同一性。它独立于 `manifest.redaction.applied`（尽管脱敏在改变副本时通常意味着 `true`）。

#### `user_path` 隐私

- 可选。路径增值很小时优先 `null`。
- 优先工作区相对路径，而非绝对家目录路径。
- **不要**存储嵌入密钥、令牌、可避免的个人目录，或在 basename（`original_name`）已足够时仍写入客户敏感文件夹名。
- 若某路径段敏感，脱敏之或将 `user_path` 设为 `null` 并注明 limitation。
- `user_path` 永不授权修改用户文件。

#### 可复制但不可读的二进制

当宿主能复制字节但无法提取文本时，允许放入 `source/original/`：

- `readable: false`
- 无假装引用内部文本的证据摘录 / 行定位器
- 无源自该文件未读内容的 KnowledgeStatus `verified`
- `manifest.limitations` **必须**提及不透明打包

跳过 / 未复制的用户文件**不要**伪造已打包条目；改为记入 `manifest.limitations`（可选未来：`skipped_sources` 列表——0.1.0 不要求）。

---

## `knowledge/overview.md`

Markdown，双语章节必需：

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

不要在此写入争议裁决。若有帮助，可在正文中按 id 链接 unknowns/conflicts。说明 `source/original/` 是包内副本。

---

## 状态字段（全部结构化知识）

`facts`、`claims`、`decisions`、`constraints` 与 `glossary` 术语**都**携带 KnowledgeStatus `status`。
写入一行**不会**使其成为 `verified`。允许的状态与判定规则：[claim-rules.md](claim-rules.md)。

当 `status` 为 `user_confirmed` 时，`confirmation` **必需**（见上文共享类型 `Confirmation`）。

当环境/版本/时间/范围影响含义或冲突检测时，可选 `context`（`KnowledgeContext`）**应当**填写。

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

事实不得含规范用语（“应当”“必须”）——那些属于 `constraints` 或 `decisions`。

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
      "notes": "Inference: 由延迟表推导；非原文明确陈述。"
    }
  ]
}
```

`kind`：`assertion` | `interpretation` | `prediction` | `requirement_claim` | `other`。

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

`priority`：`must` | `should` | `may` | `must_not` | `unspecified`。

---

## `knowledge/glossary.json`

术语也需要 `status`。列出术语**并不**意味着它是 `verified`。

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

若定义由 Exporter 综合且无来源片段 → `inferred` 或 `unverified`，绝非 `verified`。

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

`kind`：`excerpt` | `table_cell` | `figure_caption` | `metadata` | `user_message` | `other`。
`supports[].type`：`fact` | `claim` | `decision` | `constraint` | `term`。

`evidence_ids` 与 `supports` 之间要求双向一致。

若 `redaction_applied`（或包内副本脱敏）损害含义/可定位性 → 降级被支撑对象；不得保留 `verified`。

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
      "notes": "来源中列出；未获取原文。"
    }
  ]
}
```

#### ReferenceStatus（独立于 KnowledgeStatus）

| 取值 (0.1.0) | 含义 |
| --- | --- |
| `unverified` | 按来源所述记录引用；被引作品**未**在本包内获取/核验。**0.1.0 中默认且唯一已定义的可移植值。** |

规则：

1. `references[].status` 使用 **ReferenceStatus**，而非 KnowledgeStatus。
2. **不要**给引用赋 `verified`、`user_confirmed`、`inferred`、`unknown` 或 `disputed`——那些是 KnowledgeStatus 值，在此会歧义。
3. 看起来真实的 URL **不会**提升 ReferenceStatus。
4. 即便用户稍后将被引作品打包为来源，知识主张仍需各自证据；不要用 ReferenceStatus 兼指知识 `verified`（额外 ReferenceStatus 值属开放问题——Exporter 不得发明）。

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

当两条陈述**可能**冲突但上下文对齐不清时，使用 Unknowns（和/或 questions）——此时**不要**发出确定性 Conflict。

---

## `uncertainty/conflicts.json`

**仅当全部**成立时创建 Conflict：

1. 同一主体 / 话语对象
2. 上下文（环境、版本、时间、范围等）相同或明确同一
3. 两条陈述不能同真

否则：question / unknown——不是冲突。

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
      "notes": "不得自动裁决。"
    }
  ]
}
```

`context_alignment`：`same` | `different` | `uncertain`。
仅 `same`（且 `same_subject: true` 与互斥）产生 Conflict 行。
若 `uncertain` → 不要写此文件条目；改用 `questions.json` / `unknowns.json`。

除非用户明确裁决，`resolution` 保持 `null`；之后按 claim-rules 更新状态。Exporter 永不捏造裁决。

**反例：** 测试端口 `8000` vs 生产端口 `8080` → `context_alignment: different` → **无** Conflict。

---

## `handoff/receiver-guide.md`

双语操作指南。必须包含：

1. 包目的
2. 信任边界（`verified` vs `user_confirmed` vs `inferred` 等）
3. 用户原件未动；`source/original/` 是包内副本
4. 如何使用 unknowns/conflicts（以及环境不匹配 ≠ 冲突）
5. Limitations / 尽力脱敏注意事项
6. 缺少 `validation/` 表示尚未校验

用 `## English` 与 `## 中文` 分节。

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
      "notes": "上下文对齐不确定 — 未记为冲突。"
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
      "notes": "Exporter 未执行该动作。"
    }
  ]
}
```

动作 `status`：`pending` | `blocked` | `cancelled`。切勿将导出时建议标为已完成。
不要使用知识 `Status` 的动作状态值。

---

## `validation/validation-report.json`

- 为 `context-validator` **预留**的可选路径。
- 不是 Exporter 输出。
- Schema 延至 Validator 工作开始。
- Exporter 必须设置 `manifest.validation.present: false`（或在 limitations 中等价诚实），且不得声称完整校验通过。

---

## 空集合

若某类别无条目，在标准键下写空数组，例如 `{ "conflicts": [] }`。不得省略 Exporter 必需文件。未校验时完全省略 `validation/`。

## 开放问题（不得分叉布局）

| # | 歧义 | 0.1.0 建议 |
| --- | --- | --- |
| 1 | 规范性 schema 发布在何处？ | 人工语义：本文件；机器形态：`spec/cbhf/v0.1.0/*.schema.json` |
| 2 | 双语存储 | 单文件；`i18n.zh` / `i18n.en` + 叙述双语章节 |
| 3 | Fact vs Claim 边界 | Facts = 描述性原子；Claims = 断言/诠释；优先一条规范记录 |
| 4 | 校验和是否必需？ | 可选。0.1.0 发出时：`alg=sha256`，`of=package_copy`，对包内副本**原始字节**哈希；见 Validator I20 冻结规则 |
| 5 | PDF 定位器 | 已知时用 `page_range`；否则 `section` + excerpt；未读/不透明 PDF → `readable: false` + limitation |
| 6 | 无保留原文的确认 | 允许 `confirmation_text: null` + 说明原因的 `limitations` |
| 7 | 包根命名 | 用户自选目录；稳定 id 为 `package_id` |
| 8 | `validation-report.json` schema | 延至 Validator skill |
| 9 | `skipped_sources` 正式列表 | 可选未来；当前用 `limitations` |
| 10 | 将 `ReferenceStatus` 扩展到 `unverified` 之外？ | 延后——不得发明临时值 |
| 11 | `confirmation.source_ref` 的宿主 message-id 格式 | 可选不透明字符串；隐私安全；否则 `null` |
| 12 | handoff `priority`（`questions` / `recommended-actions`）封闭枚举？ | 示例仅用 `high`；Schema 在枚举批准前保持 `string` |
