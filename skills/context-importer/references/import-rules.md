# 导入规则（CBHF 0.1.0）— context-importer

规定接收方智能体 **如何** 加载目录包、应用校验门禁，并保持路径安全。

- 信任 / 状态语义 → [trust-boundaries.md](trust-boundaries.md)
- 报告形态 → [understanding-report.md](understanding-report.md)
- 字段名 / 布局 → `skills/context-exporter/references/cbhf-format.md` + `spec/cbhf/v0.1.0/*.schema.json`

**不得**在此重定义 KnowledgeStatus。**不得**发明 CBHF 字段。

---

## 1. 包根

Importer 输入是作为 CBHF 目录包根的 **目录**：

- 根目录必须包含 `manifest.yaml`。
- 期望的 Exporter 必需树（加载时检查是否存在）：

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

可选（Validator 保留区；Exporter 不得发明）：

```
<package-root>/validation/validation-report.json
```

缺少 `validation/` 表示 **尚未校验**，不是“校验已通过”
（`cbhf-format.md`）。

---

## 2. 读取顺序

1. `manifest.yaml` — 协议、ids、局限、脱敏、`validation.present`
2. 校验门禁输入（会话报告和/或包内报告）— §3
3. `knowledge/overview.md` — 仅叙事；非自动 verified 事实
4. `source/source-index.json` — 构建 `source_id` → 条目映射（`readable` 所需）
5. 知识 JSON：`facts` → `claims` → `decisions` → `constraints` → `glossary`
6. `evidence/evidence.json` 然后 `evidence/references.json`
7. `uncertainty/unknowns.json` 然后 `uncertainty/conflicts.json`
8. `handoff/receiver-guide.md`、`questions.json`、`recommended-actions.json`
9. **仅当** §5 允许时，抽查 `source/original/` 下的包内副本

空数组（如 `"facts": []`）在文件成功加载时有效。
缺失文件或无法解析的 JSON → 集合状态 **`NOT_LOADED`**（与空集合不同）。

---

## 3. 校验门禁

Importer **不是** Validator。有报告时 **消费** 报告。

### 3.1 报告来源（优先级）

1. 用户提供的 **会话** JSON，来自 `context-validator` /
   `python skills/context-validator/scripts/validate_package.py <package-root>`
2. 否则，若存在且路径安全：`validation/validation-report.json`
3. 否则：无报告 → 软门禁（§3.3）

不得捏造 PASS/FAIL。不得私自跑临时检查器并称之为 Validator。

### 3.2 绑定

仅当报告可合理指向 **本** 包树时视为 **已绑定**，例如：

- 两者均存在时 `package_id` 匹配 `manifest.package_id`，和/或
- 仅有目录信息时，包标签/basename 匹配正在导入的目录

绑定失败 → 设 **`validation_report_unbound`**。
**不得**将未绑定报告的通过/失败视为对本树权威。门禁上按未校验处理（若有其他证据表明破损则可阻止），并将未绑定报告仅作信息性披露。

### 3.3 门禁表（冻结）

| 条件 | 行为 |
| --- | --- |
| 已绑定报告；`final_status` ≠ `invalid`；无 id 匹配 L1–L3（`P*`、`S*`、`I*`）的检查 `result=FAIL` | **正常导入** |
| 无可用已绑定报告 | **允许** + 强制横幅 **`structurally_unvalidated_in_this_session`** |
| 已绑定报告 `final_status=invalid` **或** 任一 L1–L3 `FAIL` | **默认阻止** 完整接管 |
| 用户在阻止条件后明确强制导入 | **仅受限导入** |
| 已绑定报告中任一 `NOT_CHECKED` | 引用为未执行 / 不完整 — **永不**当作 PASS |

**L1–L3** 指包/schema/完整性自动化层（P/S/I 检查），不是 H\* L4 行。

### 3.4 默认阻止时的输出

阻止且无 force 时：

- 说明面向施工的完整接收方理解报告 **已扣留**。
- 在可用时列出报告中的 FAIL 检查 id、消息与路径。
- 建议修复包和/或重新运行 `context-validator`。
- 仍可列出高层 manifest 身份（package_id、title）以便定向。

### 3.5 受限导入（`UNTRUSTED_STRUCTURE`）

仅当用户 **明确** 要求在 FAIL/invalid 下强制 / 继续：

- 产出 12 节报告模板，但在文档与各主要章节前加前缀 **`UNTRUSTED_STRUCTURE`**。
- 仍须遵守 trust-boundaries（不得填补 Unknown、不得选出冲突胜方、不得升级状态）。
- 仍只读；仍路径安全。

### 3.6 报告 **不** 意味着什么

- L1–L3 `PASS` ≠ 语义真值
- I14 / I20 `PASS` ≠ 真实性或充分性（L4）
- H01–H06 `NOT_CHECKED` ≠ 已完成人类语义评审
- `manifest.validation.present: false` ≠ 已校验
- `integrity.files_touched`（若存在）≠ 完整性校验通过

---

## 4. 路径安全（冻结）

所有对包相对路径（`package_path`、`locator.path`、报告路径等）的读取 **必须**：

1. 视为相对于 `<package-root>`。
2. 若字符串含作为路径段的 `..`、为绝对路径、带盘符前缀（`C:\...`）或为 UNC（`\\...`）→ **拒绝**。
3. 解析并确认最终目标仍在 `<package-root>` **之内**。
4. **不得跟随** 最终目标逃出根的符号链接（或主机等价物）。
5. 违规时 → **不得打开**；记录导入局限；继续处理其他项。

不得用包相对字段打开任意主机路径。
`user_path` 供人类作元数据；Importer 在正常导入中 **不** 经由 `user_path` 加载用户原文。

---

## 5. 打开包内副本内容

在读取包内副本字节/文本之前：

1. 路径安全（§4）通过。
2. 关联的 `sources[].readable` 值为布尔 **`true`**
   （`source.schema.json` 要求 `readable`；有效包中不可选）。
3. 若 `readable` 为 `false` → **不得**读取正文；**不得**捏造摘录。
4. 若 `readable` 缺失或非布尔（损坏 / 非 schema 包）→ 视为
   **不可读**；不得默认当作可读。
5. 无需抽查时，优先引用 `evidence.json` 中已有的 `locator.excerpt`。

不透明 / 二进制副本存在是为了交接可携带文件而不做文本抽取——
Importer 不得“幻觉”其内容。

---

## 6. 索引构建

成功加载后构建：

| 索引 | 键 | 值 |
| --- | --- | --- |
| sources | `source_id` | source 条目 |
| facts / claims / decisions / constraints / terms | 各自 `*_id` | 对象 |
| evidence | `evidence_id` | 对象 |
| references | `reference_id` | 对象 |
| unknowns | `unknown_id` | 对象 |
| conflicts | `conflict_id` | 对象 |
| questions | `question_id` | 对象 |
| actions | `action_id` | 对象 |

保留边：

- 知识 `evidence_ids` ↔ evidence `supports`
- 知识 `conflict_ids` ↔ conflicts
- evidence `locator.source_id` → sources
- questions `related_unknown_ids` / `related_conflict_ids`
- actions `related_ids`

不得静默丢弃 ids。若出现悬空 id，在局限中注明
（Importer 不重校验；报告所见）。

---

## 7. 失败模式

| 失败 | 集合 / 条目标记 | 报告效果 |
| --- | --- | --- |
| 缺失必需文件 | `NOT_LOADED` | 章节说明未加载；不得捏造行 |
| JSON/YAML 解析错误 | `NOT_LOADED` | 同上 |
| 路径不安全 | 跳过该条目 | 局限 + 不得打开 |
| `readable !== true` | 内容未读 | 不得捏造摘录 |
| 错误协议版本 | 停止或仅局限 | 不得伪造 0.1.0 导入 |
| 默认门禁阻止 | 导入被阻止 | 仅缺陷摘要 |
| FAIL 后 force | 受限 | `UNTRUSTED_STRUCTURE` |

---

## 8. 验收覆盖（IM-01…IM-14）

| ID | 由何覆盖 |
| --- | --- |
| IM-01 | 正常导入路径 + 完整报告模板 |
| IM-02 | §3.3 无报告允许 + 披露 |
| IM-03 | §3.3 / §3.4 默认阻止 |
| IM-04 | §3.5 受限 + `UNTRUSTED_STRUCTURE` |
| IM-05 | trust-boundaries Unknown 规则 |
| IM-06 | trust-boundaries Conflict 规则 |
| IM-07 | trust-boundaries 不得升级 |
| IM-08 | SKILL 硬性规则 4 + 不可信数据 |
| IM-09 | §4 路径安全 |
| IM-10 | §2 / §7 `NOT_LOADED` |
| IM-11 | §5 readable 门禁 |
| IM-12 | §3.6 + trust-boundaries L4 |
| IM-13 | SKILL 硬性规则 1（只读） |
| IM-14 | understanding-report 语言说明 |

---

## 9. 非目标

- 重实现 Validator 检查目录
- 写入 `validation/validation-report.json`
- 网络抓取
- 修改 Package 文件
