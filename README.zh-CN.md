# ContextBridge

**Skills-first 的 AI 交接方案**：用共享文件夹协议（**CBHF 0.1.0**）做文档级上下文交接。

ContextBridge 是开源 **Agent Skills** 项目——不是 SaaS、不是 Web 控制台、也不是独立应用运行时。目标是让一个 AI Agent 把工作交给另一个 Agent（或后续会话）时，**不悄悄丢掉证据、决策、未知项与冲突**。

[English](README.md) · [快速开始](docs/getting-started.md) · [文档索引](docs/README.md)

## 要解决的问题

当一份由 AI 生成的材料交给另一个 AI（或下一轮会话）时，常会丢失：

- 哪些是 **事实**，哪些是 **推断**
- 主张是否有可定位 **证据**
- **决策** 如何被确认
- 还有哪些 **未知**
- 来源何处 **冲突**、不能自动裁决

普通 Markdown 摘要和聊天记录往往抹平这些边界。

## 核心设计理念

1. **CBHF Package 是交接载体** — 带版本的文件夹：manifest、源副本、知识、证据、不确定性、接手指引。
2. **Skills-first** — Agent 遵循 `SKILL.md`；Python 仅作为 Validator 可选辅助脚本。
3. **认识论诚实** — 保留 KnowledgeStatus（`verified` / `user_confirmed` / `inferred` / `unverified` / `unknown` / `disputed`）；Importer 不得升级状态。
4. **结构 ≠ 语义** — L1–L3 自动检查 ≠ L4 人工语义审核。
5. **缺口保持缺口** — Unknown 不联网补齐；Conflict 不自动选边。
6. **缺少校验 ≠ 已通过** — 没有 Validator 报告（或没有 `validation/`）表示「尚未校验」。

## 三个 Skill

| Skill | 职责 |
| --- | --- |
| [`context-exporter`](skills/context-exporter/SKILL.md) | 在宿主能力范围内读取文档，生成 CBHF 0.1.0 文件夹包 |
| [`context-validator`](skills/context-validator/SKILL.md) | 只读结构校验（包/Schema/完整性 L1–L3）；L4 永不自动 PASS |
| [`context-importer`](skills/context-importer/SKILL.md) | 只读恢复上下文，并在会话中产出 **Receiver Understanding Report** |

不要把三者合并成一个大 Skill。Exporter 写包；Validator 判结构；Importer 接手消费。

**CBHF**（ContextBridge Handoff Format）位于 [`spec/cbhf/`](spec/cbhf/) 与 [`skills/context-exporter/references/cbhf-format.md`](skills/context-exporter/references/cbhf-format.md)。它是**协议**，不是 Skill。

## CBHF 0.1.0 Package 结构

Exporter 必写树：

```text
<package-root>/
├── manifest.yaml
├── source/
│   ├── source-index.json
│   └── original/                 # 包内副本（可能已脱敏）
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

可选（Validator 预留；Exporter 不得伪造）：

```text
<package-root>/validation/validation-report.json
```

缺少 `validation/` 表示 **尚未校验**，不是「已通过」。

## 快速开始

1. 克隆本仓库，用 **Cursor**（Agent 模式）打开。
2. 按 [docs/getting-started.md](docs/getting-started.md) 启用三个 Skill 并跑通演示。
3. 查看样例包：[`examples/technical-proposal/`](examples/technical-proposal/)。

Validator 辅助脚本（可选，确定性 L1–L3），在仓库根目录执行：

```bash
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output
```

可选：`--schema-dir` 指向本地 `spec/cbhf/v0.1.0`（默认即此）。脚本向 stdout 打印会话 JSON，**不修改** Package；仅当 `final_status` 为 `invalid` 时退出码为 `1`。

## 端到端流程

```text
源文档  →  context-exporter  →  CBHF Package
                                   ↓
                         context-validator（建议）
                                   ↓
                         context-importer  →  Receiver Understanding Report（会话）
```

1. **导出** — 按 `context-exporter` 从文档生成包。
2. **校验** — 按 `context-validator`（优先辅助脚本）做 L1–L3。
3. **导入** — 接收方按 `context-importer` 恢复上下文；可附带 Validator 会话 JSON。

## 示例：技术方案样例

[`examples/technical-proposal/`](examples/technical-proposal/) 是虚构的 **Northwind Edge Gateway** 语料，用于演示与测试。

| 路径 | 含义 |
| --- | --- |
| `input/` | 合成源文档（**不是** Exporter 产物）。可含脱敏演练用的**假**密钥字符串——不是真实凭据。 |
| `generated-output/` | 完整 CBHF 0.1.0 包（已脱敏副本、知识、证据、未知、一处冲突）。 |
| `expected-output/EXPECTED.md` | 人工期望说明——不是第二套协议。 |

## 文档导航

| 文档 | 对象 |
| --- | --- |
| [docs/getting-started.md](docs/getting-started.md) | 首次跑通 |
| [docs/README.md](docs/README.md) | 总索引（用户文档 vs 审计底稿） |
| [cbhf-format.md](skills/context-exporter/references/cbhf-format.md) | CBHF 人读字段/布局 |
| [spec/cbhf/v0.1.0/](spec/cbhf/v0.1.0/) | JSON Schema |
| [`skills/`](skills/) 下各 `SKILL.md` | Agent 指令 |

## 当前能力与边界（v0.1.0）

**已实现**

- 三个 Skill，面向 CBHF **0.1.0** folder 包（`docs` 场景）。
- `spec/cbhf/v0.1.0/` Schema。
- Validator 辅助脚本覆盖 L1、L2 与 L3（含路径安全、locator、摘录匹配 I14、可选 package_copy 校验和 I20）。
- Importer 门禁（未验证 / invalid / 强制 + `UNTRUSTED_STRUCTURE`）已文档化并经 E2E。
- `examples/` 与 `tests/` 下有样例与验收材料。

**不做 / 不声称**

- L4 语义审核**永不**自动 PASS。
- 不承诺在所有 AI 宿主上行为一致；本仓库主要以 **Cursor** Agent Skills 流程验证。
- v0.1.0 无 Dashboard、数据库、MCP 产品、ZIP 同步或云知识库产品。
- 脱敏 best-effort ≠ 穷尽发现全部密钥/PII。
- 不提供虚构性能、成功率或用户数。

## 路线图（示意）

- 保持 CBHF 0.1.0 稳定；补充宿主打包说明时不夸大未测宿主。
- 可选的包内 validation-report 形状冻结（仍由 Validator 侧拥有）。
- 增加更多 fixture（如 `readable: false` 演示），谨慎改冻结规则。
- 首个公开 tag 后补充贡献指南。

## 许可

采用 **Apache License, Version 2.0**。见 [`LICENSE`](LICENSE)。
