# Receiver guide / 接手指南

## English

### Purpose

Continue work on the Northwind Edge Gateway proposal without losing evidence, decisions, unknowns, or conflicts.

### Trust boundaries

| Status | How to treat |
| --- | --- |
| `verified` | Explicit excerpt in package copy with locator |
| `user_confirmed` | Confirmation object present (here: packaged user-authored confirmation text) |
| `inferred` | Interpretation — see claim notes |
| `disputed` | Conflict open; do not pick a winner |
| `unknown` | Missing; do not invent |

### Package copies vs user originals

User originals under `examples/technical-proposal/input/` were not modified. Locators point at `source/original/` package copies. Some copies were redacted (`content_transformed: true`).

### Unknowns and conflicts

- **Conflict `cfl_001`:** production data-plane port 8080 vs 8000 (same environment). Staging port 8000 is **not** that conflict.
- **Unknowns:** replica count, on-call owner, `ff_http3_preview` ship state.

### Do not assume

- Redaction found every secret (best-effort only)
- Production port is settled
- `validation/` missing means validation passed — it means not validated yet
- `integrity.files_touched` (if present) means integrity verification passed

### Suggested next steps

See `handoff/questions.json` and `handoff/recommended-actions.json` (`status: pending` only).

## 中文

### 目的

在不丢失证据、决策、未知与冲突的前提下，继续 Northwind Edge Gateway 方案工作。

### 信任边界

| 状态 | 处理方式 |
| --- | --- |
| `verified` | 包内有可定位摘录 |
| `user_confirmed` | 有 confirmation 对象（本包为已打包的用户确认原文） |
| `inferred` | 解释性结论，见 claim notes |
| `disputed` | 冲突未决，勿自动裁决 |
| `unknown` | 缺失，勿臆造 |

### 副本与原件

`examples/technical-proposal/input/` 下用户原件未改。定位器指向 `source/original/` 副本；部分副本已脱敏。

### 未知与冲突

- **冲突 `cfl_001`：** 生产数据面端口 8080 与 8000（同环境）。staging 的 8000 **不是**该冲突。
- **未知：** 副本数、on-call、`ff_http3_preview` 是否上线。

### 请勿假设

- 脱敏已穷尽全部秘密
- 生产端口已确定
- 缺少 `validation/` 等于已通过校验
- `files_touched` 等于完整性校验通过

### 建议下一步

见 `questions.json` 与 `recommended-actions.json`（仅 `pending`）。
