# Overview / 概览

## English

This CBHF 0.1.0 package hands off the fictional **Northwind Edge Gateway** technical proposal set for AI-to-AI continuation.

It preserves packaged source copies, atomic facts, one inferred performance claim, decisions, constraints, glossary terms, evidence locators, unknowns, and one production-port conflict.

Trust boundary: treat `verified` items as pinned to package excerpts; treat `inferred` as interpretation; treat `disputed` production ports as unresolved; do not invent answers for unknowns.

## 中文

本 CBHF 0.1.0 交接包用于虚构产品 **Northwind Edge Gateway** 技术方案的 AI 交接续作。

包内保留源文件副本、原子事实、一条推断性性能结论、决策、约束、术语、证据定位、未知项，以及一处生产端口冲突。

信任边界：`verified` 需可回溯到包内摘录；`inferred` 为解释而非直述事实；生产端口 `disputed` 未裁决；不得用外部常识填补 Unknown。

## Scope / 范围

- Input set under `examples/technical-proposal/input/`
- Scenario: docs; form: folder

## Non-goals / 非目标

- Resolving the production listen-port conflict
- Claiming Validator success
- Fetching external references

## How to read this package / 如何阅读本交接包

1. Start with `handoff/receiver-guide.md`
2. Inspect `source/original/` (package copies; may be redacted)
3. Use `knowledge/*` with `evidence/evidence.json` locators
4. Read `uncertainty/conflicts.json` and `uncertainty/unknowns.json` before acting
