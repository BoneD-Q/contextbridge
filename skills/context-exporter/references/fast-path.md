# Exporter 快速路径（默认） / Fast path (default)

本文件是 **context-exporter 的默认入口**。先跟本文件执行；**不要**在写出包骨架之前通读
`cbhf-format.md` / `claim-rules.md` / `evidence-rules.md` / 全部 Schema。

完整 references 仅在字段不确定、要标 `verified` / `user_confirmed`、或做证据双向链接时**按需打开**。

硬性规则仍以 `SKILL.md`「硬性规则」为准（只读原件、路径安全、不捏造、不升级信任、不写 `validation/`）。

---

## 1. 何时用快速路径

| 场景 | 用快速路径？ |
| --- | --- |
| 用户给了 **1～3 个可读文档** + 空输出目录 | **是（默认）** |
| 用户说「精简 / 快速 / 先出包 / demo」 | **是** |
| 用户明确要求「完整深度导出 / full export」且接受更长时间 | 否 → 全量工作流 |
| 用户指向**整个代码仓库**且无文件白名单 | **停止**；请用户列出文件，勿扫整仓 |

---

## 2. 反卡顿硬限制（Agent 必须遵守）

1. **禁止整仓递归。** 不得遍历 `node_modules`、`.git`、`dist`、`build`、`__pycache__`、虚拟环境或未点名的源码树。
2. **来源上限（默认）：** ≤ **3** 个用户指定文件（或等价粘贴块）。超出则请用户缩范围或切 full。
3. **知识上限（默认）：** facts ≤ **12**；claims/decisions/constraints/terms 合计 ≤ **12**；证据与知识条一一对应即可。
4. **先落盘再深挖。** 在首轮工具调用内完成：脚手架（或创建必需树）→ 复制来源 → 写 `overview.md`。禁止「读完所有 references 才写第一个文件」。
5. **进度可见。** 每完成一步用一句话向用户汇报（scaffold / copy / facts / evidence / manifest / done）。
6. **不确定字段时：** 空数组或 `unverified` / Unknown；打开对应 reference 一小节，不要整本通读。

---

## 3. 推荐命令顺序

在 **ContextBridge 仓库根**（或能解析到该脚本的路径）执行脚手架，再由 Agent 填内容：

```bash
python skills/context-exporter/scripts/scaffold_package.py <package-root> \
  --package-id pkg_example \
  --title-zh "示例交接包" \
  --title-en "Example handoff"
```

然后：

1. 仅复制用户点名的源文件 → `source/original/`（安全相对名）
2. 更新 `source/source-index.json`（含诚实的 `readable` / `content_transformed` / checksum）
3. 填 `knowledge/*`、`evidence/*`、`uncertainty/*`、`handoff/*`
4. 更新 `manifest.yaml`（`sources_summary`、`limitations`、`redaction`、`files_touched`）
5. 建议用户跑：`python skills/context-validator/scripts/validate_package.py <package-root>`

无 Python 时：按 `SKILL.md`「输出包」手工创建同一树；字段形态仍须兼容 0.1.0 Schema。

---

## 4. 最小字段备忘（避免错 Schema）

| 文件 | 顶层键 | 注意 |
| --- | --- | --- |
| `facts.json` | `facts` | `context.environment` ∈ prod/staging/test/dev/local/unspecified/null |
| `claims.json` | `claims` | 无 `tags`；可有 `kind` |
| `decisions.json` | `decisions` | 用 `summary` 不是 `statement` |
| `constraints.json` | `constraints` | 无 `tags` |
| `glossary.json` | `terms` | 不是 `glossary`；证据 `supports.type` 用 `term` |
| `unknowns.json` | `unknowns` | 用 `question` + `why_it_matters`（无 `status`/`blocking`） |
| `questions.json` | `questions` | 用 `ask`；`related_unknown_ids` / `related_conflict_ids` |
| `recommended-actions.json` | `actions` | 不是 `recommended_actions`；`status` 仅 `pending` 等 |

`verified` 必须有充分证据链接；否则降为 `unverified` / `inferred`。  
证据 `excerpt` 必须命中包内副本的真实行窗口（勿锚定空行）。

---

## 5. 完成时对用户说什么

- 包路径、纳入/跳过的来源
- 计数与「快速路径 / 有上限」说明
- **不要**声称 Validator 已通过，除非真的跑过会话报告
- 提示可继续：`context-validator` → `context-importer`
