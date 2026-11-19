# context-validator 实施方案设计（CBHF 0.1.0）

**文档类型：** 实施前设计 / 仓库审计结论  
**协议版本：** CBHF 0.1.0（不修改）  
**日期：** 2026-11-19  
**状态：** 设计稿 — **Validator 尚未实现**

本文档基于对现有仓库的实际阅读，包括 Exporter Skill、CBHF 规范与 Schema、`package_smoke_test.py`、`run_schema_tests.py`、第一次真实导出包，以及 `tests/semantic-review/v0.1.0/` 人工语义审查结果。

---

## 1. 产品定位

`context-validator` 是 ContextBridge 三个独立 Agent Skills 之一。

| 维度 | 定义 |
| --- | --- |
| 是什么 | 只读地检查 CBHF 交接包是否满足协议结构、Schema、可确定性完整性规则，并输出分层验证报告 |
| 不是什么 | 不是 Python CLI 产品主体；不是 Web/API/SaaS；不是对业务正确性的裁决器；不是 Exporter 的一部分 |
| 输入 | 已存在的 CBHF 0.1.0 文件夹包（例如 `examples/technical-proposal/generated-output/`） |
| 输出 | 验证结果报告（优先会话内呈现；可选写入包内 `validation/`，见 §7） |
| 原则 | Skills-first；Python 仅作可选确定性辅助；**只读**，不修改包内知识/证据内容 |

README 已声明：Python 仅作为 Validator 的可选辅助脚本，不作为独立应用运行时。本设计与之对齐。

---

## 2. 与 Exporter、Importer 的关系

```
原始文档 ──(context-exporter)──► CBHF 包
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            package/schema   integrity      semantic hints
            (deterministic)  (deterministic) (human / LLM assist)
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
                          context-validator 报告
                                   │
                                   ▼
                          context-importer（消费包；宜先看报告）
```

| Skill | 职责 | 与 Validator |
| --- | --- | --- |
| **context-exporter** | 生成包；可跑 smoke，但**不得**自称 Validator / 不得伪造 `validation/` | Validator 消费其输出 |
| **context-validator** | 只读校验 + 报告 | 本设计对象 |
| **context-importer** | 恢复上下文与接手报告 | 应尊重 Validator 报告中的失败/警告；不替代校验 |

协议约定（`cbhf-format.md`）：

- `validation/` 为 **Validator 可选输出**
- 缺少 `validation/` = 尚未验证，≠ 验证通过
- Exporter 必须保持 `manifest.validation.present: false`（导出时）

---

## 3. 功能边界

### 3.1 必须做

1. Package Validation（结构/解析）
2. Schema Validation（对照现有 `spec/cbhf/v0.1.0/*.schema.json`）
3. Integrity Validation（ID、双向关联、locator、摘录可匹配、路径安全、重复 ID）
4. Semantic Review Boundary（输出人工复核提示，**不**自动语义 PASS）

### 3.2 明确不做

- 修改包内 facts/claims/evidence 等业务内容
- 自动裁决冲突权威值
- 宣称脱敏已穷尽
- 把 LLM 语义判断写成确定性 `pass`
- 把 `package_smoke_test.py` 改名或冒充为 Validator
- 升级 CBHF 版本或改写现有 Schema / EXPECTED / 人工审查结论

### 3.3 与 smoke 的边界（硬规则）

现有 `tests/schema/v0.1.0/package_smoke_test.py`：

- **保留**为测试夹具 / 导出后快速结构检查
- **不得**改名为 Validator
- 其能力可被 Validator **复用思路或抽取共享库**，但产品入口必须是 Skill 工作流 + 可选 scripts，并输出分层报告

Smoke 已覆盖的能力（可迁移为 Validator L1–L3 子集）：

- 必需路径存在
- 无 `validation/`（对 Exporter 产物的期望；Validator 自身写入报告时另论）
- YAML UniqueKey + manifest Schema
- 各 JSON Schema
- 双向 evidence 链接、source_id/path、line_range 首行匹配、verified 需 evidence_ids、user_confirmed 需 confirmation 对象、conflict party 存在性
- 已知明文密钥黑名单（示例级，非通用）

Smoke **未**覆盖（Validator 需补齐或明确标为未检查）：

- 额外/意外文件策略
- JSON 重复键（Python `json` 默认静默覆盖）
- 全量 excerpt 行匹配（smoke 仅首行）
- 重复 ID 扫描（跨文件）
- `related_*_ids` / `related_ids` / `conflict_ids` / `questions` 引用存在性
- `user_authored_source` 的 `source_ref` 是否存在于 source-index
- 路径 `..` / 绝对路径 / symlink 逃逸的系统级检查
- `readable: false` 源不得支撑 verified 的确定性规则
- overview.md / receiver-guide.md 内容规范
- 语义充分性、真实确认、冲突策略、脱敏穷尽

---

## 4. 四层检查模块

### 4.1 层次总览

| 层 | 名称 | 性质 | 可否确定性自动判定 |
| --- | --- | --- | --- |
| L1 | Package Validation | 结构 / 解析 | 是 |
| L2 | Schema Validation | 字段形状 | 是（JSON Schema） |
| L3 | Integrity Validation | 跨文件一致性 / 定位可匹配 | 大部分是；部分边界需警告 |
| L4 | Semantic Review Boundary | 语义 / 业务权威 | **否** — 仅提示人工 |

单项结果码（见 §6）：`pass` | `fail` | `warn` | `not_checked` | `needs_human`

包级汇总状态 ≠ 单项状态（见 §7）。

---

## 5. 每项检查：输入、逻辑、预期结果

### 5.1 L1 Package Validation

| ID | 检查项 | 输入 | 逻辑 | 预期 |
| --- | --- | --- | --- | --- |
| P01 | 必需路径存在 | 包根目录 | 对照 Exporter-required 树（manifest、source-index、original/、knowledge/*、evidence/*、uncertainty/*、handoff/*） | 缺失 → `fail` |
| P02 | Markdown 可读 | overview.md、receiver-guide.md | 文件存在且可 UTF-8 读取 | 不可读 → `fail` |
| P03 | JSON 可解析 | 全部 `.json` | 使用**拒绝重复键**的解析器（不得用默许覆盖的 `json.loads` 作为唯一手段） | 解析失败/重复键 → `fail` |
| P04 | YAML 可解析 | manifest.yaml | UniqueKeyLoader（与现测一致） | 解析失败/重复键 → `fail` |
| P05 | 包形态 | 目录布局 | 根下应有约定顶层目录；`package_form=folder` | 明显非 folder → `fail` |
| P06 | 额外文件策略 | 全树枚举 | **建议 0.1.0：** 未知顶层目录/文件 → `warn`（不默认 fail，因协议未冻结 allowlist）；`validation/` 仅当本次 Validator 写入或已有报告时允许 | 见 Open Question Q1 |
| P07 | 只读承诺 | 运行时 | Validator 不写知识文件；若写入报告，仅限 `validation/` + 可选更新 `manifest.validation`（需用户确认策略，见 §7） | 违反 → 设计失败 |

### 5.2 L2 Schema Validation

| ID | 检查项 | 输入 | 逻辑 | 预期 |
| --- | --- | --- | --- | --- |
| S01 | Schema 加载 | `spec/cbhf/v0.1.0/*.schema.json` | Draft 2020-12 `check_schema` | 损坏 → Validator 自身错误 |
| S02 | manifest | 解析后对象 | `manifest.schema.json` | 不符 → `fail` |
| S03 | source-index | sources | `source.schema.json` | 不符 → `fail` |
| S04–S08 | facts/claims/decisions/constraints/glossary | 各文件 | 对应 schema | 不符 → `fail` |
| S09 | evidence | evidence.json | `evidence.schema.json` | 不符 → `fail` |
| S10 | references | references.json | `ReferencesDocument` fragment | 不符 → `fail` |
| S11–S14 | unknowns/conflicts/questions/actions | 各文件 | 对应 schema | 不符 → `fail` |
| S15 | 非法枚举/缺字段/类型/额外字段 | 同上 | Schema `additionalProperties` / enum / required / if-then（如 verified→evidence_ids、user_confirmed→confirmation） | 不符 → `fail` |

**依据：** 仅现有 Schema；不重新定义协议字段。

### 5.3 L3 Integrity Validation

区分四档（不得混为一谈）：

| 档 | 含义 | 自动能力 |
| --- | --- | --- |
| A. 引用存在 | ID 在目标集合中 | 确定性 |
| B. 定位有效 | path 存在、行号/页码在范围内、source_id 一致 | 确定性 |
| C. 摘录可匹配 | excerpt 文本在定位窗口内可找到 | 确定性（规范化策略需固定） |
| D. 摘录语义充分 | 是否真正支持命题 / 状态 | **非** L3 — 属 L4 |

| ID | 检查项 | 档 | 逻辑 | 预期 |
| --- | --- | --- | --- | --- |
| I01 | 重复 ID | A | 各命名空间内 id 唯一（fact_*/claim_*/ev_* 等） | 重复 → `fail` |
| I02 | evidence.supports → 知识对象存在 | A | type+id 可解析 | 缺失 → `fail` |
| I03 | knowledge.evidence_ids → evidence 存在 | A | | 缺失 → `fail` |
| I04 | 双向一致 | A | supports 与 evidence_ids 对称 | 不一致 → `fail` |
| I05 | conflict.parties 存在 | A | | 缺失 → `fail` |
| I06 | conflict.evidence_ids 存在 | A | | 缺失 → `fail` |
| I07 | related_conflict_ids / related_unknown_ids / related_ids / conflict_ids / related_fact_ids | A | 指向已存在 id | 缺失 → `fail` 或 `warn`（建议 fail） |
| I08 | confirmation.source_ref（user_authored_source） | A | 必须是 source-index 中的 source_id | 缺失/伪造 → `fail` |
| I09 | locator.source_id ∈ source-index | A | | 缺失 → `fail` |
| I10 | locator.path 存在于包内 | B | 相对包根；文件存在 | 缺失 → `fail` |
| I11 | path 安全 | B | 禁 `..`、绝对路径、盘符、UNC；解析后不得逃出包根；不跟随逃逸 symlink | 违规 → `fail` |
| I12 | line_range 边界 | B | 1-based；end≥start；不超过文件行数 | 越界 → `fail` |
| I13 | section/anchor/json_pointer/page_range | B | 类型合法；page/section 是否“找得到”在 0.1.0 可降级为 `warn`/`not_checked` 若宿主无法解析 | 见 Q2 |
| I14 | excerpt 匹配 | C | **建议：** 规范化换行后，excerpt 每一非空行 ⊆ 定位窗口文本（强于 smoke 的“首行”） | 不匹配 → `fail` |
| I15 | verified ⇒ evidence_ids 非空 | A+Schema | Schema 已约束；Integrity 再确认 | 空 → `fail` |
| I16 | readable:false 源 | A/B | 若 evidence 引用 `readable:false` 源且声称摘录文本 → `fail`；知识 `verified` 依赖该 evidence → `fail` | |
| I17 | content_transformed ∈ {true,false,null} | Schema | 已由 Schema 保证 | — |
| I18 | manifest.validation 诚实性 | — | 若包内无报告却 `present:true` → `fail`；Exporter 产物期望 false | |
| I19 | 孤儿 evidence（supports 为空） | A | 允许但 → `warn`（协议允许未指派，prefer 链接） | |
| I20 | checksum（若存在） | — | 可选：重算 package_copy 哈希；不匹配 → `warn`/`fail`（策略见 Q3） | |

### 5.4 L4 Semantic Review Boundary

以下**不得**因确定性脚本结果写成语义 `pass`：

| ID | 主题 | Validator 行为 |
| --- | --- | --- |
| H01 | Evidence 是否真正支持命题 | 输出 `needs_human` 清单（对象 id、摘录、命题） |
| H02 | verified 是否合理 | 仅确认结构门槛（有 evidence + 可匹配）；合理性 → `needs_human` |
| H03 | user_confirmed 是否真实确认 | 结构上有 confirmation；真实性 → `needs_human`（对照 semantic-review 经验：fixture vs 现场会话） |
| H04 | disputed / conflict 是否真冲突 | 可检查 same_subject / context_alignment 字段自洽；业务真冲突 → `needs_human` |
| H05 | 脱敏是否穷尽 | 可选：已知模式/黑名单 → `warn`；穷尽 → `not_checked` |
| H06 | 哪个配置权威 | 永不自动裁决；`needs_human` |

可复用人工审查模板：`tests/semantic-review/v0.1.0/`（checklist / csv），作为 Skill references 中的审查指引，而不是自动 PASS 引擎。

---

## 6. 错误级别设计

### 6.1 单项检查结果

| 码 | 含义 |
| --- | --- |
| `pass` | 该项确定性检查通过 |
| `fail` | 该项确定性检查失败 |
| `warn` | 可疑但不构成协议硬失败（或策略未冻结） |
| `not_checked` | 本运行未执行或无法执行 |
| `needs_human` | 超出确定性范围，需人工/另一 Agent 按指南复核 |

### 6.2 包级汇总状态（与单项分离）

| 包级状态 | 条件（建议） |
| --- | --- |
| `invalid` | 任一 L1/L2/L3 硬性 `fail` |
| `structurally_valid` | L1–L3 无 `fail`；可有 `warn`/`not_checked`/`needs_human` |
| `structurally_valid_with_warnings` | 无 `fail`，但有 `warn` |
| `not_fully_validated` | 关键 L3 子集 `not_checked`（宿主能力不足） |
| `semantically_unreviewed` | 结构有效，但 L4 均未人工完成 |

**禁止：** 因 L4 未做就把整包标为语义 PASS。  
**禁止：** 把单项 `pass` 说成“包已通过完整验证”。

---

## 7. 验证报告设计

### 7.1 原则

- 报告是 **Validator 自身格式**（实施前不新增 CBHF Schema）。
- 是否写入包内 `validation/validation-report.json`：**可选**；默认建议：
  - **会话输出**（始终）
  - **包内写入**（用户明确要求时）——写入后可更新 `manifest.validation.present=true` 与 `report_path`（此为 Validator 允许的清单字段更新，不是改写知识）
- 未写入时：不得把缺失报告解释为“已通过”。

### 7.2 建议报告结构（Validator-owned，非正式 Schema）

```text
ValidationReport {
  report_version: "0.1.0-validator-draft"   # 非 CBHF 协议版本
  cbhf_version: "0.1.0"
  package_path: string
  generated_at: ISO-8601
  validator: { skill: "context-validator", skill_version: string }
  read_only: true
  package_status: invalid | structurally_valid | structurally_valid_with_warnings | not_fully_validated
  layers: {
    package:  { status, checks: CheckResult[] }
    schema:   { status, checks: CheckResult[] }
    integrity:{ status, checks: CheckResult[] }
    semantic: { status: "needs_human" | "not_checked", prompts: SemanticPrompt[] }
  }
  summary: { pass, fail, warn, not_checked, needs_human }
  limitations: string[]   # 宿主限制、未跑检查等
}

CheckResult {
  id: string            # 如 P01, S02, I14
  name: string
  result: pass|fail|warn|not_checked|needs_human
  message: string
  path?: string         # 相关文件/对象 id
}

SemanticPrompt {
  id: string            # H01...
  object_refs: string[]
  question: string
  suggested_method: "human_review" | "semantic_review_template"
}
```

正式 `validation-report.json` 的 CBHF Schema 仍属协议 Open Question #8；**本阶段不写入 `spec/cbhf/v0.1.0/`**。

---

## 8. Skills 与可选脚本的职责划分

| 组件 | 职责 |
| --- | --- |
| `skills/context-validator/SKILL.md` | 工作流：何时校验、如何调用脚本、如何解读四层结果、如何向用户报告、禁止语义伪 PASS |
| `skills/context-validator/references/` | 检查清单、与 semantic-review 模板的映射、错误码说明 |
| `skills/context-validator/scripts/` | 可选确定性辅助：parse、schema、integrity、path safety、excerpt match；stdout/JSON 报告 |
| `tests/schema/v0.1.0/package_smoke_test.py` | **测试专用 smoke**；保持名称与定位；可抽取共享函数供 scripts 引用，但不改名为 validator |
| Agent（宿主） | 执行 Skill；在 L4 按 references 提问/人工审查；不把模型感觉写成 fail/pass 硬结果 |

Python 脚本约束：

- 无网络补全事实
- 无数据库 / FastAPI / Web UI
- 退出码可表示 `invalid` vs `structurally_valid`，但不等于产品“发布通过”

---

## 9. 测试策略

| 阶段 | 内容 |
| --- | --- |
| T0 保持 | 现有 `run_schema_tests.py` 38 项不回归 |
| T1 包夹具 | 以 `generated-output` 为 golden structurally_valid 样本 |
| T2 负例包 | 最小坏包：缺文件、坏 YAML、重复键、断链、excerpt 不匹配、path `..`、verified 无 evidence |
| T3 与 smoke 对照 | 同一包上 smoke 与 Validator L1–L3 结果一致或 Validator ⊆ 超集 |
| T4 语义 | 不测自动语义 PASS；测“是否发出 needs_human 提示” |
| T5 只读 | 运行前后知识文件哈希不变（仅允许可选 validation/ 写入场景的差分白名单） |

---

## 10. 已知限制

1. JSON Schema 无法表达跨文件引用与摘录充分性（已在 cbhf-format 写明）。
2. `section`/`page_range` 的“找得到”依赖宿主解析能力。
3. 摘录匹配对空白/Markdown 强调标记敏感，需固定规范化规则。
4. 脱敏检查只能是启发式。
5. `handoff.priority` 无封闭枚举（协议 Open Question #12）。
6. README.zh-CN 仍写“v0 骨架”，与仓库现状不完全同步（文档债，非协议）。
7. 第一次导出的人工审查为**有条件通过**——Validator 不得吞掉这些条件。

---

## 11. Open Questions（只记录，不改协议）

| ID | 问题 | 建议（不实施协议变更） |
| --- | --- | --- |
| Q1 | 未知额外文件是 `fail` 还是 `warn`？ | 0.1.0 默认 `warn` |
| Q2 | section/page_range 找不到时？ | `warn` 或 `not_checked`，勿假装已验证 |
| Q3 | checksum 不匹配严重级别？ | 有 checksum 则 `fail`；无则 `not_checked` |
| Q4 | 是否默认写入包内 `validation/`？ | 默认否；用户显式要求才写 |
| Q5 | 写入报告时是否更新 `manifest.validation`？ | 若写包内报告，则应更新 present/report_path；属 Validator 清单字段 |
| Q6 | validation-report 的 CBHF Schema 何时冻结？ | 等 Validator MVP 稳定后再进 `spec/`（协议 Q#8） |
| Q7 | JSON 重复键检测库选型？ | scripts 内实现 object_pairs_hook；不改协议 |
| Q8 | 与 Importer 的门禁：invalid 包是否拒绝导入？ | Importer 设计时再定；建议硬 fail 阻断 |

---

## 12. 推荐实施顺序（最小可行）

1. **V0 — Skill 骨架补全**  
   重写 `skills/context-validator/SKILL.md` 工作流；添加 references：检查清单、结果码、与 smoke/semantic-review 的边界说明。  
   *不改协议 / Schema / EXPECTED / 人工审查结论 / 输入原文。*

2. **V1 — 确定性脚本 MVP（L1+L2）**  
   `skills/context-validator/scripts/validate_package.py`（名称示意）：必需文件、YAML/JSON（拒重复键）、全部现有 Schema。  
   会话输出分层报告；默认不写包内。

3. **V2 — Integrity MVP（L3 A/B/C）**  
   双向链接、重复 ID、related_*、path 安全、line_range、全量 excerpt 匹配、readable:false 规则。  
   负例夹具测试。

4. **V3 — Semantic prompts（L4）**  
   仅生成 `needs_human` 提示；挂接 semantic-review 模板路径；明确禁止自动语义 PASS。

5. **V4 — 可选包内报告**  
   用户确认后写入 `validation/validation-report.json`（Validator-owned 格式）并更新 manifest.validation；仍不冻结 CBHF Schema。

6. **V5 — 文档同步**  
   更新 README 状态描述；链到本设计文档。

---

## 13. 文件变更建议

### 建议新增（实施阶段，非本审计任务编码）

| 路径 | 用途 |
| --- | --- |
| `skills/context-validator/SKILL.md` | 完整工作流（替换 skeleton） |
| `skills/context-validator/references/check-catalog.md` | 检查项 ID 目录 |
| `skills/context-validator/references/result-codes.md` | 结果码与包级状态 |
| `skills/context-validator/references/semantic-prompts.md` | L4 提示模板 |
| `skills/context-validator/scripts/validate_*.py` | 确定性辅助 |
| `tests/validator/`（未来） | 正/负例包与脚本测试 |
| `docs/context-validator-design.zh-CN.md` | **本文件（本任务已创建）** |

### 建议保持不变

| 路径 | 原因 |
| --- | --- |
| `spec/cbhf/v0.1.0/*.schema.json` | 协议机器形状权威 |
| `skills/context-exporter/references/*` | 不改抽取规则与协议叙述 |
| `examples/.../EXPECTED.md` | 测试期望不被迁就 |
| `tests/semantic-review/v0.1.0/*` | 人工结论不被改写 |
| `examples/.../input/*` | 原件只读 |
| `tests/schema/v0.1.0/package_smoke_test.py` 名称与定位 | 禁止冒充 Validator |
| CBHF 0.1.0 版本号 | 不升级 |

### 可选后续（非阻塞）

- README.zh-CN / README.md 状态段落与仓库现实对齐  
- 从 smoke 抽取共享库供 Validator scripts 与 tests 共用（保持两个入口语义分离）

---

## 14. 审计摘要（审查结果）

### 已有能力

- 完整 CBHF 0.1.0 人读规范 + 13 个 JSON Schema  
- Exporter Skill 可执行工作流 + 真实导出包  
- Schema 回归测试 38/38；package smoke 34/34  
- 人工语义审查（有条件通过）及可复用模板  
- 协议已预留 `validation/` 与 manifest.validation 字段  
- context-validator 目录骨架存在（SKILL skeleton）

### 缺失能力

- context-validator Skill 正式指令与 references  
- Validator 确定性脚本与分层报告  
- JSON 重复键硬失败、全量 excerpt 匹配、重复 ID、related_* 完整性、path/symlink 逃逸等 L3 缺口  
- L4 提示自动化（非自动 PASS）  
- validation-report 的冻结 Schema（有意延后）  
- Importer 与 Validator 的门禁策略

### 协议歧义（Open Questions）

见 §11（额外文件策略、section/page 定位深度、checksum 级别、是否写包内报告、report Schema 冻结时机、Importer 门禁等）。**均不在本阶段改协议。**

### 最小可行实施顺序

见 §12：Skill 文档 → L1+L2 脚本 → L3 → L4 提示 → 可选包内报告 → README 同步。

---

**结论：本任务完成的是 context-validator 的仓库审计与实施方案设计。Validator 尚未实现；不得将本文档或现有 smoke/人工审查结果表述为“Validator 已实现”或“包已通过正式校验”。**
