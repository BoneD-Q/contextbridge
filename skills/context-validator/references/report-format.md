# Validator 报告格式（会话级）

定义 `context-validator` 如何呈现结果。

**CBHF 0.1.0：** 仅**会话报告**（`validate_package.py` stdout JSON / 聊天呈现）。
包内 `validation/validation-report.json` 为协议**预留路径，写入未启用** — 不得写入 Package，不得翻转 `manifest.validation`。
`validation-report` JSON Schema **不冻结**。

实现权威：`scripts/validate_package.py` 中的 `package_final_status` 与 `_finalize_report`（Phase **3B-C2**）。

## 隐私

- 包身份优先使用基名或相对演示路径。
- 除非用户要求，共享报告中避免绝对 home/user 路径。
- 不得将摘录中的秘密粘贴进报告；引用 ID 与简短原因即可。

## 必需报告章节

1. **包身份** — 隐私安全的路径 / 已知的 package_id
2. **CBHF 版本** — 来自 `manifest.cbhf_version`，或 unresolved
3. **校验时间** — ISO-8601 UTC，或带偏移的本地时间
4. **检查器能力声明** — 诚实声明 Phase / 实际可运行项
5. **分层摘要** — L1 / L2 / L3 / L4 汇总
6. **检查明细** — 每个已执行或有意跳过的检查一行/一项
7. **错误位置** — 已知时给出文件 + JSON path / 行号
8. **失败原因** — 基于事实，不得捏造
9. **警告**
10. **未检查** — 附原因（工具缺失、依赖失败、范围外、零适用）
11. **需人工审查** — L4 及任何边界项
12. **最终包裁决** — 与逐项状态区分

## 逐项检查状态

| 状态 | 含义 |
| --- | --- |
| `PASS` | 检查已运行且成功 |
| `FAIL` | 检查已运行且发现缺陷 |
| `WARNING` | 检查已运行；非阻断性问题 |
| `NOT_CHECKED` | 已定义但未执行，或前置条件缺失 / 零适用 |
| `NEEDS_HUMAN_REVIEW` | 需要判断；**永不**自动提升为语义 PASS |

## 分层摘要状态（与逐项检查、final_status 区分）

| 层 | 汇总规则 |
| --- | --- |
| L1 / L2 | `FAIL` > `WARNING` > 全 `PASS` > 混合 PASS+NOT_CHECKED → **PASS**（历史约定） |
| L3 | `FAIL` > 任一 `NOT_CHECKED` → **NOT_CHECKED**（不完整性优先于 WARNING）> 否则 `WARNING` > 全 `PASS` |
| L4 | 永不语义 PASS；Phase 3B-C2 将 H01–H06 标为 `NOT_CHECKED` |

L3 理由：即便 L3-A/B/C 已自动化，单项仍可能 `NOT_CHECKED`（例如 I13 无 finder、I14 门控、I20 零适用 checksum）。不得因单项已执行的 WARNING（如 I19 孤儿 evidence）使该层看起来“已完成”。逐项 WARNING 仍保留在 `warnings[]`。

包级 `final_status` **独立**于分层摘要，规则见下一节。

## 包最终状态（`package_final_status`）

与逐项检查码分离。Phase 3B-C2 辅助脚本调用时固定：`l3_implemented=True`，`l4_reviewed=False`。

按序求值（先匹配先生效）：

| 包状态 | 何时（与脚本一致） |
| --- | --- |
| `invalid` | 任一 `P*` / `S*` / `I*` 检查结果为 `FAIL` |
| `not_fully_validated` | 任一 `I*` 为 `NOT_CHECKED`（**含** I20「零适用 checksum」），**或**重要 `P*`/`S*` 为 `NOT_CHECKED`，**或** `l3_implemented=False` |
| `structurally_valid_with_warnings` | 无上述 FAIL / I\* 未查；且至少一个 `P*`/`S*`/`I*` 为 `WARNING` |
| `semantically_unreviewed` | 无 FAIL、无 I\* `NOT_CHECKED`、无 WARNING；且 `l4_reviewed=False`（**Phase 3B-C2 常态**） |
| `structurally_valid` | 同上结构干净，且 `l4_reviewed=True` — 自动化辅助**达不到**（L4 永不自动审查 / 永不语义 PASS） |

说明：

- **`structurally_valid` 不允许**夹带未执行的重要 `I*` `NOT_CHECKED`。任何 `I*` `NOT_CHECKED` 都压成 `not_fully_validated`。
- 因此：无 checksum 的包（I20 → `NOT_CHECKED`）即使 L1–L3 其余全 PASS，包级仍为 `not_fully_validated`。这是刻意诚实，不是失败。
- 有 WARNING 的干净 L3 走 `structurally_valid_with_warnings`，**不会**再标成 `semantically_unreviewed`。
- **永不**出现包级“语义 PASS”。L4 层保持 `NOT_CHECKED` / `NEEDS_HUMAN_REVIEW`。

**不得**仅因 smoke 或 schema 夹具通过，就设定最终结构确定性。
**不得**将逐项 `PASS` 视为“完整包校验已完成”。

## 建议 Markdown 模板

```markdown
# ContextBridge 校验报告

- package: <隐私安全路径>
- package_id: <id 或 unknown>
- cbhf_version: <版本或 unresolved>
- validated_at: <时间戳>
- checker: context-validator Phase 3B-C2（L1+L2+L3-A+B1–B4+I14+I20；L4 未自动化）

## 能力声明

- L1–L2：经 `scripts/validate_package.py` 自动化（P01–P07，S01–S15）
- L3-A：已自动化（I01–I09, I15, I17–I19）
- L3-B1–B4：已自动化（I11/I10, I16, I12, I13）
- L3-C：已自动化（I14 字面摘录匹配；I20 可选 package_copy SHA-256）
- L4：仅边界；H01–H06 → `NOT_CHECKED`；**无自动语义 PASS**
- 包变更：无（只读；**不**写入 `validation/`）

## 分层摘要

| 层 | 结果 |
| --- | --- |
| L1 Package | PASS / FAIL / WARNING / NOT_CHECKED |
| L2 Schema | ... |
| L3 Integrity | PASS / FAIL / WARNING / NOT_CHECKED |
| L4 Semantic boundary | NOT_CHECKED（永不语义 PASS） |

## 检查明细

| ID | 状态 | 位置 | 原因 |
| --- | --- | --- | --- |
| P01 | ... | ... | ... |

## 失败

- ...

## 警告

- ...

## 未检查

- <id>: <原因>（例：I20 零适用 checksum）

## 需人工审查

- ...

## 最终包状态

`<invalid | structurally_valid | structurally_valid_with_warnings | not_fully_validated | semantically_unreviewed>`

### 说明

- 本报告为**会话级**；0.1.0 **未**写入 Package（`validation/` 预留未启用）。
- 若检查被跳过 / `NOT_CHECKED`，不得将本报告当作伪造的完整校验。
- L4 层不得显示自动语义 PASS。
- I14/I20 PASS ≠ 语义充分性。
```

## 可选机器可读草图（非规范）

会话 JSON 由脚本打印；非冻结草图可类似：

```json
{
  "report_kind": "contextbridge-validation-session",
  "cbhf_version": "0.1.0",
  "package_id": null,
  "package_label": "generated-output",
  "validated_at": "2026-11-19T00:00:00Z",
  "checker": {
    "name": "context-validator",
    "phase": "3B-C2",
    "scripts_implemented": {
      "L1_package": true,
      "L2_schema": true,
      "L3_A_references": true,
      "L3_B_locators": true,
      "L3_C_excerpts": true,
      "L3_C_checksum": true,
      "L4_semantic": false
    },
    "network": false,
    "writes_package": false
  },
  "layers": {
    "L1": "PASS",
    "L2": "PASS",
    "L3": "NOT_CHECKED",
    "L4": "NOT_CHECKED"
  },
  "checks": [],
  "final_status": "not_fully_validated",
  "wrote_to_package": false
}
```

不得为未运行的检查捏造 pass/fail 行。`wrote_to_package` 在 0.1.0 必须为 `false`。

## 写入 Package（0.1.0：未启用）

写入 `validation/` 或翻转 `manifest.validation.present` **不在 CBHF 0.1.0 范围内**（路径仅预留）。
若未来阶段启用包内报告，仍必须保持 knowledge/evidence/source 副本不可变，且不得伪造结果。
