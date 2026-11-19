# 接收方理解报告 — context-importer

接收方智能体在成功（或受限）导入后产出的会话级报告。**默认落点：仅当前聊天/会话。**
**不得**将本文件写入 Package。

配套规则：

- [import-rules.md](import-rules.md) — 门禁、加载、路径
- [trust-boundaries.md](trust-boundaries.md) — 状态、Unknown、Conflict

---

## 1. 输出规则

1. 按顺序包含下方 **全部 12 个必需章节**。
2. 使用隐私安全的包标签（basename / `package_id`）；避免家目录路径。
3. 引用包对象 ids（`fact_001`、`ev_007`、`unk_001`、`cfl_001`、…）。
4. 按 **KnowledgeStatus** 分桶 facts（及其他知识）— 不得在无标签时把 `inferred`
   混入“已确认事实”列表。
5. 若集合为 `NOT_LOADED`，如实说明；**不得**捏造行。
6. 若集合已加载且为空数组，写“无记录”。
7. 受限 force 导入时，在标题与各节标题前加前缀
   **`UNTRUSTED_STRUCTURE`**。
8. 语言：报告可为中文、英文或双语。转述时 **不得**改变源语言
   `statement.text` / `summary.text` / `definition.text` 的含义。对关键原子优先引用源语言文本，需要时将译文放在括号中或旁注 `i18n`。
9. 不得粘贴摘录中的密钥；引用 evidence ids 与简短非机密片段。

---

## 2. 必需章节（冻结）

### 1) Package 基本信息 / Package identity

- 隐私安全路径或 basename
- `package_id`、标题（若有 `zh`/`en`）
- `cbhf_version`、`protocol`、`scenario`、`package_form`
- `generated_at`、若有则含生成器 skill/version
- 校验门禁结果：normal / unvalidated / blocked / restricted
- 可用时的已绑定 Validator **会话**摘要：`final_status`、分层汇总、FAIL ids（0.1.0 不以包内 `validation/` 为权威）
- 标志：按适用情况写入 `structurally_unvalidated_in_this_session`、`validation_report_unbound`、
  `UNTRUSTED_STRUCTURE`

### 2) 项目背景与目标 / Background and goals

- 压缩自 `knowledge/overview.md` 与 receiver-guide 目的
- 标为 **叙事**（非自动 verified 知识）
- overview 中有范围 / 非目标时纳入

### 3) 已知事实 / Known facts (by status)

来自 `knowledge/facts.json`，按 `status` 分组：

- `verified`
- `user_confirmed`（含 confirmation 摘要）
- `inferred`
- `unverified`
- `unknown`
- `disputed`（指向 Conflicts）

每项：`fact_id`、statement 文本（+ lang）、`evidence_ids`、`conflict_ids`、
可选 `context`。

### 4) 关键主张及证据 / Claims and evidence

来自 `knowledge/claims.json`：

- `claim_id`、若有则 `kind`、statement、status、notes（尤其 Inference:）
- 关联 `evidence_ids` 及按 `evidence_id` 的关键摘录引用
- 若有则 `related_fact_ids`

### 5) 决策 / Decisions

来自 `knowledge/decisions.json`：

- `decision_id`、summary、status、date、rationale、`supersedes`、evidence、conflicts

### 6) 约束与边界 / Constraints and boundaries

来自 `knowledge/constraints.json`：

- `constraint_id`、statement、status、`priority`、evidence、conflicts

### 7) 术语表 / Glossary

来自 `knowledge/glossary.json`：

- `term_id`、term、definition、status、aliases、evidence

提醒：列出术语 ≠ verified。

### 8) Unknowns

来自 `uncertainty/unknowns.json`：

- 每个 `unknown_id` 含 question + why_it_matters
- 标注 **OPEN — DO NOT FILL**
- `suggested_owner`、相关 ids、notes

### 9) Conflicts

来自 `uncertainty/conflicts.json`：

- 每个 `conflict_id` 含 summary 与 `shared_context`
- 各方：type、id、stance
- `resolution` 值或 **unresolved**
- 明确：未解决时不得选胜方

### 10) 待确认问题 / Open questions

来自 `handoff/questions.json`：

- `question_id`、ask、priority、相关 unknown/conflict ids、notes

### 11) 建议下一步 / Suggested next actions

来自 `handoff/recommended-actions.json`：

- 优先 `status: pending`
- 纳入 blocked/cancelled 时须可见其 status
- 不得将行动标为已完成

### 12) 接收方理解限制 / Receiver limitations

按适用情况必须包含：

- Package 未修改（只读导入）
- 结构未校验 / 未绑定报告 / UNTRUSTED_STRUCTURE
- Validator NOT_CHECKED 项（尤其 H01–H06）— 不是 PASS
- L4 语义评审未完成；未声称语义 PASS
- 脱敏尽力而为 / 不完整，来自 `manifest.redaction` + `limitations`
- 不透明源（`readable: false`）未读
- 集合 `NOT_LOADED`
- I14/I20（若经 Validator 提及）仅为结构
- Unknowns 仍开放；Conflicts 未解决，除非包另有说明

---

## 3. Markdown 模板

复制并填写。删除指导性注释。

```markdown
# 接收方理解报告 / Receiver Understanding Report

> 门禁: <normal | structurally_unvalidated_in_this_session | blocked | UNTRUSTED_STRUCTURE>
> package: <basename-or-label>
> package_id: <id>
> cbhf_version: <0.1.0>
> importer: context-importer 0.1.0（会话报告；未修改 Package）

## 1. Package 基本信息 / Package identity

- …
- Validator（若已绑定）: final_status=…; L1=…; L2=…; L3=…; L4=…
- FAIL ids: …
- NOT_CHECKED（不得当作 PASS）: …

## 2. 项目背景与目标 / Background and goals

（来自 overview / receiver-guide 的叙事 — 非自动 verified。）

## 3. 已知事实 / Known facts (by status)

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
- … → 见 Conflicts（`cfl_…`）

## 4. 关键主张及证据 / Claims and evidence

- `claim_…` [status]: …
  - evidence: `ev_…` …

## 5. 决策 / Decisions

- `dec_…` [status]: …

## 6. 约束与边界 / Constraints and boundaries

- `con_…` [status] [priority]: …

## 7. 术语表 / Glossary

- `term_…` [status]: …

## 8. Unknowns

- `unk_…` **OPEN — DO NOT FILL**: …
  - 为何重要（why_it_matters）: …

## 9. Conflicts

- `cfl_…` (context: …) **unresolved**
  - 当事方 A: … stance …
  - 当事方 B: … stance …
  - 不得自动选出胜方。

## 10. 待确认问题 / Open questions

- `q_…`: …

## 11. 建议下一步 / Suggested next actions

- `act_…` [pending]: …

## 12. 接收方理解限制 / Receiver limitations

- …
```

---

## 4. 阻止导入存根（无 force）

门禁阻止完整接管时，用短存根代替 12 节施工报告：

```markdown
# 导入已阻止 — 请先修复结构 / Import blocked — fix structure first

- package: …
- package_id: …
- reason: final_status=invalid and/or L1–L3 FAIL
- FAIL summary: …
- Next: 修复包和/或运行 context-validator 后重新导入
- Note: 完整接收方理解报告已扣留（用户未请求 force）
```

---

## 5. 与 `handoff/receiver-guide.md` 的关系

| 产物 | 角色 |
| --- | --- |
| `receiver-guide.md` | 包内、Exporter 提供的双语常设说明 |
| 接收方理解报告 | **本会话** 为下一任智能体恢复的工作简报 |

理解报告 **应当** 纳入 guide 中的信任警告；仍 **必须**
包含由 JSON 集合支撑的结构化章节，而非仅 guide 散文。

---

## 6. 验收关联

| ID | 本文件 |
| --- | --- |
| IM-01 | 完整 12 节模板 |
| IM-02 | §1 / 模板中的门禁横幅 |
| IM-03 | §4 阻止存根 |
| IM-04 | `UNTRUSTED_STRUCTURE` 规则 |
| IM-05–IM-07 | 第 3/8/9 节 + trust-boundaries |
| IM-12 | 第 12 节 + Validator 诚实 |
| IM-14 | §1 语言规则 |
