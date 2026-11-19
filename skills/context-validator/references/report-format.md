# Validator 报告格式（会话级）

定义 `context-validator` 如何呈现结果。
Phase 1 **不冻结** `validation-report` JSON Schema。
**默认：** 仅会话报告 — **不得写入** Package。

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
10. **未检查** — 附原因（工具缺失、依赖失败、范围外）
11. **需人工审查** — L4 及任何边界项
12. **最终包裁决** — 与逐项状态区分

## 逐项检查状态

| 状态 | 含义 |
| --- | --- |
| `PASS` | 检查已运行且成功 |
| `FAIL` | 检查已运行且发现缺陷 |
| `WARNING` | 检查已运行；非阻断性问题 |
| `NOT_CHECKED` | 已定义但未执行，或前置条件缺失 |
| `NEEDS_HUMAN_REVIEW` | 需要判断；**永不**自动提升为语义 PASS |

## 分层摘要状态（与逐项检查、final_status 区分）

| 层 | 汇总规则 |
| --- | --- |
| L1 / L2 | `FAIL` > `WARNING` > 全 `PASS` > 混合 PASS+NOT_CHECKED → **PASS**（历史约定） |
| L3 | `FAIL` > 任一 `NOT_CHECKED` → **NOT_CHECKED**（不完整性优先于 WARNING）> 否则 `WARNING` > 全 `PASS` |
| L4 | 永不语义 PASS；通常为 `NOT_CHECKED` / `NEEDS_HUMAN_REVIEW` |

L3 理由：延迟检查（如 L3-B/C）不得因单项已执行的 WARNING（如孤儿 evidence）使该层看起来“已完成”。逐项 WARNING 仍保留在 `warnings[]`。包级 `final_status` 独立，且已将重要 I\* `NOT_CHECKED` 视为 `not_fully_validated`。

## 包最终状态（汇总；与逐项检查区分）

优先包级标签（设计文档 §6.2）：

| 包状态 | 何时 |
| --- | --- |
| `invalid` | 任一硬性 L1/L2/L3 `FAIL` |
| `structurally_valid` | 无 L1–L3 `FAIL`；仍可有 warnings / not_checked / needs_human |
| `structurally_valid_with_warnings` | 无 `FAIL`，但有一项或多项 `WARNING` |
| `not_fully_validated` | 重要 L1–L3 检查为 `NOT_CHECKED`（主机限制） |
| `semantically_unreviewed` | 结构大致正常，但 L4 人工审查未完成 |

亦允许作为粗粒度会话标签：将 `invalid`↔结构性 FAIL，L4 在分层摘要中保持 `NEEDS_HUMAN_REVIEW` / `NOT_CHECKED` — **永不**出现包级“语义 PASS”。

**不得**仅因其他处 smoke 或 schema 夹具通过，就设定最终结构确定性。
**不得**将逐项 `PASS` 视为“完整包校验已完成”。

## 建议 Markdown 模板

```markdown
# ContextBridge 校验报告

- package: <隐私安全路径>
- package_id: <id 或 unknown>
- cbhf_version: <版本或 unresolved>
- validated_at: <时间戳>
- checker: context-validator Phase 3B-1（L1+L2+L3-A；L3-B/C 与 L4 未自动化）

## 能力声明

- L1–L2：经 `scripts/validate_package.py` 自动化
- L3-A：已自动化（I01–I09, I15, I17–I19）
- L3-B/C：**未实现** → 逐项 NOT_CHECKED；该层通常为 NOT_CHECKED
- L4：仅边界 + 人工审查；**无自动语义 PASS**
- 包变更：无（只读）

## 分层摘要

| 层 | 结果 |
| --- | --- |
| L1 Package | PASS / FAIL / WARNING / NOT_CHECKED |
| L2 Schema | ... |
| L3 Integrity | ... |
| L4 Semantic boundary | NEEDS_HUMAN_REVIEW / NOT_CHECKED（永不语义 PASS） |

## 检查明细

| ID | 状态 | 位置 | 原因 |
| --- | --- | --- | --- |
| P01 | ... | ... | ... |

## 失败

- ...

## 警告

- ...

## 未检查

- <id>: <原因>

## 需人工审查

- ...

## 最终包状态

`<invalid | structurally_valid | structurally_valid_with_warnings | not_fully_validated | semantically_unreviewed>`

### 说明

- 本报告默认**未**写入 Package。
- 若检查被跳过，不得将本报告当作伪造的完整校验。
- L4 层不得显示自动语义 PASS。
```

## 可选机器可读草图（非规范）

若用户要求会话内 JSON，非冻结草图可类似：

```json
{
  "report_kind": "contextbridge-validation-session",
  "cbhf_version": "0.1.0",
  "package_id": null,
  "package_label": "generated-output",
  "validated_at": "2026-11-19T00:00:00Z",
  "checker": {
    "name": "context-validator",
    "phase": "3B-1",
    "scripts_implemented": {
      "L1_package": true,
      "L2_schema": true,
      "L3_integrity": false,
      "L3_A_references": true,
      "L3_B_locators": false,
      "L3_C_excerpts": false,
      "L4_semantic": false
    },
    "network": false
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

不得为未运行的检查捏造 pass/fail 行。

## 写入 Package（延期）

写入 `validation/` 或翻转 `manifest.validation.present` **不在 Phase 1 默认范围内**。
若未来阶段写入报告，仍必须保持 knowledge/evidence/source 副本不可变，且不得伪造结果。
