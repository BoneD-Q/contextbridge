# 语义审查边界（L4）

L4 是**人工判断**层。
`context-validator` 可以**呈现**候选与问题。对下列各项，**不得**发出自动语义 `PASS`。

## 绝对禁止：自动语义 PASS

| ID | 主题 | 自动语义 PASS？ | Validator 行为 |
| --- | --- | --- | --- |
| H01 | Evidence 是否真正支撑命题 | **永不** | 列出对象 id、摘录、命题 → `NEEDS_HUMAN_REVIEW` |
| H02 | `verified` 是否有充分依据 | **永不** | 结构（evidence + 匹配）可为 L3；合理性 → 人工 |
| H03 | `user_confirmed` 是否为真实现场确认 | **永不** | confirmation 对象可 schema-valid；真实性 → 人工 |
| H04 | `disputed` / Conflict 是否为真实冲突 | **永不** | Party ID 可解析；业务真相 → 人工 |
| H05 | 脱敏是否覆盖全部敏感材料 | **永不** | 仅可对已知模式发可选 WARNING；完整性 → 人工 / `NOT_CHECKED` |
| H06 | 哪个配置值具有权威性 | **永不** | 呈现候选；不得挑选赢家 |

**不得**对 H01–H06 任一自动 PASS。使用 `NEEDS_HUMAN_REVIEW`（若未执行 L4 则为 `NOT_CHECKED`）。可附带保留不确定性的审查**建议**。

## L3 仍可做的事（≠ L4 PASS）

| 自动化 / 结构性 | 不等于 |
| --- | --- |
| 引用 ID 存在（A） | Evidence 支撑命题 |
| Locator 路径/范围有效（B） | 摘录对主张充分 |
| 摘录文本可匹配（C） | 语义充分性（D） |
| Schema 允许 `verified` + evidence_ids | `verified` 诚实 |
| `user_confirmed` 存在 `confirmation` 对象 | 确认事件真实发生 |
| Conflict parties 可解析 | Conflict 在业务上真实 |
| `redaction.applied` 布尔存在 | 脱敏覆盖完整 |

档 D（语义充分性）**仅属 L4**。

## 如何报告 L4

- 状态：`NEEDS_HUMAN_REVIEW` 或 `NOT_CHECKED`
- 永不：自动语义 `PASS`
- 可引用既有**人工**审查产物（如 `tests/semantic-review/v0.1.0/`）作为**人工**结论 — 不得将其重新标为 Validator 自动 PASS
- 设计或运行 L4 提示时，**不得**更改历史人工语义审查结论

## 审查建议模式（保留不确定性）

```text
候选: <id>
结构性说明: <已知的 A/B/C 结果>
待裁决: <人工必须决定的事项>
不确定性: 在接收方/负责人裁决前仍然存在
建议问题: <非约束性>
```

---

## 来自首次真实导出的示例（不得推翻既有人工结论）

这些示例取自技术提案首次导出 + 人工语义审查。
它们说明**边界**，不是新裁决。

### 示例 1 — 22 条 Evidence：定位 vs 充分性

- **结构性（L3）：** 许多 evidence 可在 A/B/C 上 PASS（ID 可解析、路径存在、摘录匹配窗口）。
- **语义性（L4）：** 文本匹配**并不**证明摘录足以支撑每个关联命题或状态。
- **报告：** L3 可 PASS 匹配检查；L4 → 对证据集支撑充分性给出 `NEEDS_HUMAN_REVIEW`。
- **不得：** “因摘录匹配，22/22 evidence 语义 PASS。”

### 示例 2 — fixture 来源的 `user_confirmed`

- **结构性：** Schema 可 PASS：status `user_confirmed` + 非 null `confirmation`。
- **语义性：** 确认可能来自**示例/夹具**材料，而非真实利益相关方确认。
- **报告：** `NEEDS_HUMAN_REVIEW` — “此确认是真实的还是演示编写的？”
- **不得：** 自动 PASS “现场已用户确认。”

### 示例 3 — 生产端口 8080 vs 8000

- **结构性：** 两者均可作为 schema-valid 的 facts/claims 带 evidence 出现；Conflict 对象可能编码也可能未编码。
- **语义性：** 生产环境哪个端口权威是**业务**决策。
- **报告：** 呈现两种读法；`NEEDS_HUMAN_REVIEW` / conflict 跟进。保留不确定性。
- **不得：** 将 8080 或 8000 选为 Validator 真相。

### 示例 4 — 尽力而为的脱敏

- **结构性：** `redaction.applied` true/false 与变换可 schema 检查；若策略规定，对**可检测**残留可在完整性层 WARNING/FAIL。
- **语义性：** 敏感信息覆盖完整性不能仅由 Skill 认证。
- **报告：** `NEEDS_HUMAN_REVIEW` — “脱敏为尽力而为；残留风险未知。”
- **不得：** 自动 PASS “已无敏感数据残留。”

---

## 与首次人工语义审查的对齐

首次人工审查大致结论为**有条件通过**，并留下未决问题（确认真实性、端口冲突、脱敏完整性、证据充分性）。

L4 说明必须：

- 将这些议题保持为可见的人工决策
- **不得**升级为 Validator 语义 PASS
- **不得**改写或否定已存人工审查报告的结论

若新校验运行发现**新的**结构性 FAIL，在 L1–L3 下报告；不得静默改写既往 L4 人工文本文件。
