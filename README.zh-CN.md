# ContextBridge

**面向 AI 交接文档的 Agent Skills 开源项目。**

ContextBridge 不是独立的 Python 软件，也不是 Web 应用。它解决的问题是：一份由 AI 生成的文档交给另一个 AI 后，上下文、证据、决策和未知信息常常丢失。

## 它是什么

三个相互独立的 Skill，共用同一套数据协议：

| Skill | 作用 |
| --- | --- |
| [`context-exporter`](skills/context-exporter/) | 将原始文档整理成 CBHF 标准交接包 |
| [`context-validator`](skills/context-validator/) | 检查交接包结构、来源、证据、引用、冲突与文件完整性 |
| [`context-importer`](skills/context-importer/) | 读取交接包，恢复上下文并生成接手理解报告 |

**CBHF**（ContextBridge Handoff Format）是三个 Skill 共用的数据协议，位于 [`spec/cbhf/`](spec/cbhf/)，本身不是 Skill。

## 仓库结构

```
skills/          # Agent Skills（SKILL.md + 可选 scripts/references）
spec/cbhf/       # CBHF 协议版本
examples/        # 端到端示例输入与期望输出
tests/           # 协议与 Skill 相关测试
```

Python 仅作为 Validator 的**可选辅助脚本**，不作为独立应用运行时。

## 当前状态

v0 骨架：仅有目录布局与 Skill 占位文件。完整 Skill 说明、CBHF schema、示例与测试将后续补充。

## 许可

计划采用 Apache-2.0（正式 license 文件随首个实质版本一并加入）。

---

[English](README.md)
