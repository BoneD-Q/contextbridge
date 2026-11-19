---
name: context-validator
description: >
  只读校验 CBHF 0.1.0 交接包的包结构、Schema 形态、引用完整性与语义审查提示。用于在导入或分发前检查 ContextBridge 包，或用户要求运行 context-validator。不得捏造验证通过，不得改写包内知识。
license: Apache-2.0
metadata:
  author: contextbridge
  version: "0.1.0"
  protocol: CBHF
  protocol_version: "0.1.0"
---

# context-validator

只读校验 **CBHF 0.1.0** 文件夹包。

本 Skill **以说明为先**。`scripts/` 下的确定性 Python 辅助覆盖 L1/L2、**L3-A**、**L3-B1–B4**、**L3-C1 I14**（line_range 摘录字面匹配）与 **L3-C2 I20**（可选 package_copy SHA-256）。**L4 不做自动化**。辅助脚本**不是**独立产品 CLI。

设计权威：[`docs/context-validator-design.zh-CN.md`](../../docs/context-validator-design.zh-CN.md)。
协议 / Schema：`skills/context-exporter/references/cbhf-format.md` 与 `spec/cbhf/v0.1.0/*.schema.json`。

校验前请阅读：

1. [references/validation-rules.md](references/validation-rules.md) — L1/L2/L3 检查目录
2. [references/report-format.md](references/report-format.md) — 会话报告形态
3. [references/semantic-review-boundary.md](references/semantic-review-boundary.md) — L4：永不自动语义 PASS

## 何时使用

- 用户要求校验 / 检查 CBHF 或 ContextBridge 交接包
- 用户点名本 skill：`context-validator`
- 导入/分发前，需要结构诚实性时

**不得**用本 skill 导出包（`context-exporter`）或导入/接手工作（`context-importer`）。
**不得**将 `tests/schema/v0.1.0/package_smoke_test.py` 改名或当作本 Skill。

## 硬性规则（不可协商）

1. **对包内知识只读。** 校验过程中不得修改 facts、claims、evidence、`source/original/` 下内容，或其他 Exporter 要求的内容。
2. **不得伪造结果。** 不得捏造 PASS/FAIL。若某项检查未执行，标记为 `NOT_CHECKED`。
3. **不得语义自动 PASS。** L4 项仅可为 `NEEDS_HUMAN_REVIEW` 或 `NOT_CHECKED`——永不为“语义 PASS”。
4. **不得发明协议。** 不得新增 CBHF 字段或抬升版本。
5. **0.1.0：仅会话报告。** 向 stdout / 会话呈现结果。**不得**写入 `validation/validation-report.json`，**不得**翻转 `manifest.validation`。包内 `validation/` 为协议预留路径，**本版本写入未启用**（脚本永不写包）。
6. **Smoke ≠ Validator。** `package_smoke_test.py` 仍是开发者烟雾测试；不得把 smoke 输出呈现为正式 Validator 通过。
7. **隐私。** 报告中优先使用包基名 / 相对标签；避免倾倒 home/user 绝对路径。

## 能力诚实声明（Phase 3B-C2）

| 层 | 是否在 references 中定义？ | 本 Phase 是否自动化？ |
| --- | --- | --- |
| L1 包结构 | 是 | **是** — `scripts/validate_package.py`（P01–P07） |
| L2 Schema | 是 | **是** — 同一脚本（S01–S15），仅本地 Draft 2020-12 |
| L3-A 引用 | 是 | **是** — I01–I09、I15、I17–I19，经 `_integrity.py` |
| L3-B1 路径安全 / 存在 | 是 | **是** — I11、I10 |
| L3-B2 readable:false | 是 | **是** — I16（Option C） |
| L3-B3 line_range 边界 | 是 | **是** — I12 |
| L3-B4 其他定位器 | 是 | **是** — I13（Option B，无 finders） |
| L3-C I14 摘录匹配 | 是 — 冻结于 `validation-rules.md` | **是** — `_integrity.check_i14`（仅字面窗口匹配） |
| L3-C I20 校验和 | 是 — 规则冻结于 `validation-rules.md` | **是** — `_integrity.check_i20`（package_copy SHA-256；可选） |
| L4 语义边界 | 是 | **永不**自动化 PASS — H\* → `NOT_CHECKED` |

在 references 中写下检查 ID **并不**等于已自动化，除非本表声明如此。
**不得**把 L4 语义判断呈现为 I14 结果。**I14 PASS ≠ 语义充分性。**

## 输入

| 输入 | 必需 | 说明 |
| --- | --- | --- |
| 包根目录 | 是 | 应包含 `manifest.yaml` 的目录（CBHF 文件夹形态） |
| 协议期望 | 默认 0.1.0 | 读取 `manifest.cbhf_version` / `protocol` |
| 是否写入包内报告？ | 否 | **否** — 0.1.0 未启用；仅会话 JSON |

若路径不可读，停止并报告。不得伪造包。

## 识别协议版本

1. 确认包根存在 `manifest.yaml`。
2. 读取 `cbhf_version` 与 `protocol`。
3. 对本 Skill 版本，仅 **CBHF `0.1.0`** 在范围内。
4. 若版本缺失/不受支持 → 包级结果偏向 `invalid` / 识别检查失败；不得在未注明不匹配的情况下假装套用 0.1.0 规则。

## 工作流

按顺序执行。不得通过捏造 PASS 跳过层级。

### 0. 计划（只读）

- 解析包根。
- 打开上文所列 references。
- 声明 Phase 3B-C2 边界：L1+L2+L3-A+B1–B4+I14+I20 自动化；L4 未实现。

### 1. 运行确定性辅助（优先）

在仓库根（或任意 cwd）调用：

```text
python skills/context-validator/scripts/validate_package.py <package-root>
```

可选：`--schema-dir` 指向**本地** `spec/cbhf/v0.1.0` 副本——永不下载 Schema。

脚本向 stdout 打印**会话 JSON 报告**，并且：

- 不修改包
- **不**创建 / 写入 `validation/`（0.1.0 预留未启用）
- 不跟随逃逸符号链接进入包树外
- 将未实现检查（L4）标为 `NOT_CHECKED`；零适用校验和的 I20 也报告 `NOT_CHECKED`（包级常为 `not_fully_validated`）

用 [report-format.md](references/report-format.md) 解释 JSON。

若脚本无法运行，回退到手工 L1/L2 检查，并将不可用项标为 `NOT_CHECKED`。

### 2. L1 — 包校验

遵循 [validation-rules.md](references/validation-rules.md) 中的 **P01–P07**。优先采用脚本结果。

### 3. L2 — Schema 校验

遵循 **S01–S15**。优先对照 `spec/cbhf/v0.1.0/` 的脚本结果。

若某文件在 L1 解析/存在性上失败，依赖该文件的 S\* 检查必须为 `NOT_CHECKED`（不得为 PASS）。

### 4. L3 — 完整性校验

- **L3-A（已实现）：** I01–I09、I15、I17–I19 — 使用脚本结果。
- **L3-B1（已实现）：** I11 路径安全、I10 路径存在。
- **L3-B2（已实现）：** I16 readable:false（Option C）— 使用脚本结果。
- **L3-B3（已实现）：** I12 line_range 边界 — 使用脚本结果。
- **L3-B4（已实现）：** I13 其他定位器（Option B，无 finders）— 使用脚本结果。
- **L3-C I14（已实现）：** line_range 摘录 ↔ 窗口字面匹配 — 使用脚本结果。
- **L3-C I20（已实现）：** 可选 package_copy SHA-256 — 使用脚本结果；零适用 → `NOT_CHECKED`。
不得将 L3 PASS、I14 PASS 或 I20 PASS 视为语义充分性（L4）。

### 5. L4 — 语义审查边界

若用户需要人工提示，遵循 [semantic-review-boundary.md](references/semantic-review-boundary.md)。
Phase 2 脚本将 H01–H06 留为 `NOT_CHECKED`。
**永不**得出“语义验证已通过”的结论。

### 6. 组成会话报告

使用脚本 JSON 和/或 [report-format.md](references/report-format.md)：

- 逐项检查结果
- 分层摘要
- 包级状态（与逐项检查分离）
- 限制 / NOT_CHECKED 列表

### 7. 收尾

- 确认包内知识文件未被修改。
- 不得声称 L4 已自动化。I14/I20 PASS ≠ 语义充分性。
- 仅在用户接受结构风险与剩余 NOT_CHECKED 项后，再建议 Importer。

## 结果处理

包级 `final_status` 由 `package_final_status` 汇总（权威说明：[report-format.md](references/report-format.md)）：

| 情形 | 包级状态 |
| --- | --- |
| 任一 L1/L2/L3（`P*`/`S*`/`I*`）`FAIL` | `invalid` |
| 任一 `I*` 为 `NOT_CHECKED`（含 I20 零适用），或重要 `P*`/`S*` 未查 | `not_fully_validated` |
| 无上述 FAIL/未查，但有 `P*`/`S*`/`I*` `WARNING` | `structurally_valid_with_warnings` |
| 无 FAIL/未查/WARNING，且 L4 未人工审查（Phase 3B-C2 常态） | `semantically_unreviewed` |
| 无 FAIL/未查/WARNING，且 L4 已人工审查 | `structurally_valid`（自动化辅助**达不到**；L4 永不自动 PASS） |
| 用户要求写入 `validation/` | **拒绝** — 0.1.0 包内报告未启用 |

**永不**出现包级“语义 PASS”。

## 本 Skill 版本范围外

- L4 自动语义裁决
- 写入包内 `validation/` 或翻转 `manifest.validation`（路径预留未启用）
- CLI / Web / DB / MCP 产品
- 更改 CBHF Schema 或 Exporter 规则
- 编辑 `EXPECTED.md`、`generated-output`、输入，或既有语义审查结论
- 冻结 validation-report Schema
- 将 smoke 测试改名为 Validator
