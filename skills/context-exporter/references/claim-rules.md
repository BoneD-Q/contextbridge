# 主张与状态规则（CBHF 0.1.0）

`context-exporter` 在分类知识项并分配 **知识状态（KnowledgeStatus）** 时使用。

- **字段形态 / 共享类型：** [cbhf-format.md](cbhf-format.md)（schema 权威；此处不得分叉字段名）
- **证据 / 定位器 / 脱敏实践：** [evidence-rules.md](evidence-rules.md)

本文件**不**重新定义包布局。若此处字段形态偏离 `cbhf-format.md`，修正本文件。

## 对象类型

| 类型 | 文件 | 是什么 | 不是什么 |
| --- | --- | --- | --- |
| **事实（Fact）** | `facts.json` | 来自来源的描述性原子（“X 是 Y”） | 不是建议；不是自动真理 |
| **主张（Claim）** | `claims.json` | 需要认识论处理的断言/诠释 | 不是整段原文倾倒 |
| **决策（Decision）** | `decisions.json` | 已做出（或声称已做出）的选择 | 不是模糊目标 |
| **约束（Constraint）** | `constraints.json` | 要求或禁止 | 不是观察 |
| **术语（Term）** | `glossary.json` | 已定义词汇 | 仅因列出并不等于已验证 |
| **未知（Unknown）** | `unknowns.json` | 接收方不得捏造的重要缺口 | 不是琐事 |
| **冲突（Conflict）** | `conflicts.json` | 同主体、同上下文、互斥的一对 | 不是环境/版本不匹配 |

### 提取启发式

1. 当状态可能不同时，拆分复合句。
2. `statement.text` / `summary.text` / `definition.text` 保持源语言；译文仅放 `i18n`。
3. 一句中既有事实又有结论 → 需要时拆成两条（fact + inferred claim）。
4. 不可读图表/二进制 → Unknown——不得捏造内容。
5. 当环境/版本/时间/范围已陈述或明显隐含时，填写可选 `context`。

### 存在 ≠ verified

在 `facts.json`、`claims.json`、`decisions.json`、`constraints.json` 或 `glossary.json` 中创建一行**不会**赋予 `verified`。状态始终显式且须挣得。

---

## KnowledgeStatus 值（封闭集）

`verified` | `user_confirmed` | `inferred` | `unverified` | `unknown` | `disputed`

各处拼写相同（SKILL、format、evidence rules）。

**不是**与 `references[].status`（cbhf-format 中的 **ReferenceStatus**）、动作 `status`（`pending` \| `blocked` \| `cancelled`）或 `manifest.validation` 相同。

### 按对象类型允许的状态

| 状态 | facts | claims | decisions | constraints | glossary terms |
| --- | --- | --- | --- | --- | --- |
| `verified` | 是 | 是 | 是 | 是 | 是 |
| `user_confirmed` | 是 | 是 | 是 | 是 | 是 |
| `inferred` | 是* | 是 | 是* | 是* | 是* |
| `unverified` | 是 | 是 | 是 | 是 | 是 |
| `unknown` | 是 | 是 | 是 | 是 | 是 |
| `disputed` | 是 | 是 | 是 | 是 | 是 |

\* 纯诠释性跳跃优先移到带 `inferred` 的 **claims**。对 facts/decisions/constraints/terms，仅当对象类型仍适合但措辞不显式时使用 `inferred`（例如术语定义由多个片段综合）。

### 分类型判定说明

#### facts

- 优先明确陈述的原子。
- `verified` 仅在有充分证据时（见 evidence-rules）。
- `inferred` 少见——若跳跃属诠释，改为发出 **claim**。
- 环境特定事实**应当**设置 `context.environment`（例如 prod vs test）。

#### claims

- 断言/诠释内容的默认归属。
- 六种状态均常见。
- `inferred` **必须**包含解释跳跃的 `Inference:` 说明。

#### decisions

- `verified`：来源明确记录该决策已做出 + 充分证据。
- `user_confirmed`：用户在会话中确认**该决策**（带 `confirmation`）。
- `inferred`：Exporter 推断已做出决策而来源仅暗示——须清楚标注；不得在 overview 中当作既定政策呈现。
- 提及未来选项 ≠ 决策。

#### constraints

- `verified` / `unverified` 来自有来源的需求文本。
- 当用户确认该约束适用时用 `user_confirmed`。
- 软愿望（“或许我们应当”）不是 `must` 约束；降低 priority 或改用 claim。

#### glossary terms

- `verified`：定义（或等价物）出现在来源中且有充分证据。
- `inferred`：Exporter 写了非来源原文的释义。
- `unverified`：术语出现但定义未钉死。
- `unknown`：使用了术语但含义未确立——若重要，最好另加 Unknown 行。
- **切勿**因录入术语就默认 `verified`。

---

## 决策树（全部对象类型）

按序应用；在首次完整匹配处停止。

```
1. 是否存在与另一项的真冲突？
   （同一主体 且 上下文已对齐 且 互斥）
   是 → status disputed + conflicts.json 条目；不要选赢家。
   否 → 继续
   若主体/上下文对齐不确定 → 暂不要 disputed；
   改记 question/unknown；继续用其他状态处理。

2. 用户是否明确确认了本命题
   （不是猜测/建议/不确定）？
   是 → user_confirmed + 必需的 confirmation 对象
   否 → 继续

3. 明确出现在来源中 且 证据+定位器充分
   （且脱敏未破坏支撑）？
   是 → verified
   否 → 继续

4. 出现在来源中 但 证据/定位器不充分
   （未读二进制、弱定位器、脱敏损伤等）？
   是 → unverified
   否 → 继续

5. 合理结论但非原文，且有据可查的前提？
   是 → inferred（notes 解释跳跃；绝不当作 verified 售卖）
   否 → 继续

6. 交接需要但尚未确立？
   是 → unknown（通常同时写 unknowns.json）
   否 → 不要发出该记录
```

---

## 状态定义

### `verified`

- ≥1 条充分证据项，含包内副本中的具体定位器 + 摘录。
- 不依赖外部知识或未读文件。
- **禁止：** 模型先验、“常见做法”、未获取的 URL、未运行的测试、未读 PDF/DOCX/图片主张。

### `user_confirmed`

- 用户明确肯定**该具体命题**。
- 猜测 / 建议 / “也许” / “我觉得可能” / 头脑风暴 ≠ 确认。
- AI 推断绝不可标为 `user_confirmed`。
- 沉默 ≠ 确认。
- **必需字段：** `confirmation`（见下）。

### `inferred`

- 可从来源推出但非原文陈述。
- 尽可能链接前提证据；`notes` 含 `Inference: …`。
- 不得在 overview / receiver-guide 中描述为 verified。

### `unverified`

- 来源（或用户文本）中有说，但未充分钉死——包括脱敏导致支撑丢失。
- 接收方视为“某处说过，未钉死”。

### `unknown`

- 未确立；对继续工作重要。
- 优先带 `why_it_matters` 的 `unk_*`。
- **禁止：** 网页补全或训练数据猜测。

### `disputed`

- 仅在下方冲突规则下存在真 Conflict（`cfl_*`）时。
- 在用户裁决前 `resolution` 保持 `null`。

---

## `confirmation` 对象（仅 `user_confirmed`）

必需形态（规范性共享类型：cbhf-format `Confirmation`）：

```json
{
  "confirmation": {
    "confirmed_by": "user",
    "source_type": "conversation",
    "source_ref": null,
    "confirmation_text": "用户明确确认的原话",
    "confirmed_at": null,
    "limitations": null
  }
}
```

| 字段 | 规则 |
| --- | --- |
| `confirmed_by` | 0.1.0 对该状态始终为 `user` |
| `source_type` | `conversation` \| `user_authored_source` \| `other`（含义见下） |
| `source_ref` | 取决于 `source_type`（下表） |
| `confirmation_text` | 可保留时，针对**该**命题的原话 |
| `confirmed_at` | 已知则为 ISO-8601 UTC；否则 `null` |
| `limitations` | 当 `confirmation_text` 为 `null`/不完整，或 `source_type` 为 `other` 时必需 |

### `source_type` 含义

| 取值 | 含义 |
| --- | --- |
| `conversation` | 用户在**当前** agent 会话 / 聊天中明确肯定该命题 |
| `user_authored_source` | 肯定文本位于**已打包**的用户撰写文件（已索引的 `source_id`） |
| `other` | 肯定归属于用户，但渠道**既非**本会话**也非**已打包用户撰写来源（例如用户转发自己的旧笔记；从外部工单粘贴且**未**将该工单打包为来源）。必须在 `confirmation.limitations` 中说明渠道。**不得**捏造假 `source_id`。 |

### 按 `source_type` 的 `source_ref`

| `source_type` | `source_ref` 规则 |
| --- | --- |
| `conversation` | `null`，或可用时的隐私安全宿主消息 id |
| `user_authored_source` | **必须**为存在于 `source/source-index.json` 的 `source_id` |
| `other` | `null`，或简短的**非 `src_*`** 渠道标签；**不得**为不存在的 `source_id`；优先 `null` + `limitations` 而非伪造 `src_*` |

规则：

1. 确认你所存储的命题——不是模糊的相邻话题。
2. 若用户仅确认复合陈述的一部分，拆分原子；只确认被肯定的原子。
3. 用户的猜测 / 建议 / 不确定 ≠ 确认（任何 `source_type`）。
4. AI 推断绝不可获得 `user_confirmed`。
5. 若无法保留原话，设 `confirmation_text: null` 并在 `limitations` 中说明（系统性时也写入 `manifest.limitations`）。
6. 对 `user_authored_source`，仍尽量将该确认片段打包/引用为证据（`kind: user_message` 或 excerpt）。
7. 对 `other`，不要静默抬高信任：保持诚实的 `limitations`；仅当存在真实已打包片段时附着证据。
8. 对非 `user_confirmed` 状态，设 `"confirmation": null`（优先显式 `null`）。

---

## 映射示例

| 情形 | 典型状态 |
| --- | --- |
| “生产端口为 8080” + 行定位器 | `verified`（fact，`context.environment: prod`） |
| 用户：“对，生产就是 8080” | `user_confirmed` + `confirmation` |
| 用户：“也许端口是 8080吧” | 非确认 → 多为 `unverified`/`unknown` 或忽略 |
| 延迟表 → “瓶颈在连接池” | `inferred` 主张（claim） |
| 未读扫描 PDF 中的断言 | `unverified` 或 `unknown` + limitation |
| 测试:8000 vs 生产:8080 | **不是**冲突；两条不同 `context` 的 facts |
| 两份生产文档：8080 vs 8000 | `disputed` + conflict |
| Exporter 自造术语 | `inferred` 术语（term） |
| “副本数 TBD” | `unknown` |

---

## 禁止升级

| 从 | 到 | 允许？ |
| --- | --- | --- |
| `inferred` | `verified` | 仅在有新的明确摘录支撑时 |
| `inferred` | `user_confirmed` | 仅在用户明确确认该命题后 |
| `unverified` | `verified` | 仅在定位器/证据充分后（脱敏后仍充分） |
| `disputed` | 其他 | 仅在记录用户裁决后 |
| `unknown` | `verified` | 仅在有新的有来源证据时——绝不可靠猜测 |

不得对冲突多数表决。不得为“清理”包而删除一方。

---

## Facts vs claims vs decisions vs constraints vs terms

闸门：

1. 规则/需求？ → **constraint**
2. 在备选中已选选项？ → **decision**
3. 词汇定义？ → **term**
4. 纯描述性原子？ → **fact**
5. 否则属断言/诠释？ → **claim**

若在 fact 与 claim 之间不确定，优先保守状态的 **claim**。
不要把同一句话复制到所有文件。

---

## 冲突（严格）

### 仅当全部成立时创建 Conflict

1. **同一主体** — 两条陈述关于同一话语对象。
2. **上下文对齐** — 环境 / 版本 / 时间 / 范围相同或明确同一（`context_alignment: same`）。
3. **互斥** — 在该上下文下不能同真。

### 不要在以下情况创建 Conflict

- 环境不同（测试 `8000` vs 生产 `8080`）
- 版本/时间范围不同且历史上可同真
- 措辞不同但含义兼容
- 上下文对齐**不确定**

### 当上下文不确定时

- **不要**为该对写入 `conflicts.json`。
- 添加 `questions.json`（可选加 `unknowns.json` + `recommended-actions.json`）。
- 各陈述保持其独立挣得的最佳非 `disputed` 状态（`verified` / `unverified` / …）。
- 可在 `notes` 中注明潜在张力而不声明 `disputed`。

### 当存在真 Conflict 时

1. 发出带 `same_subject: true`、`context_alignment: same`、`shared_context`、parties、evidence 的 `cfl_*`。
2. 将相关项设为 `disputed` 并链接 `conflict_ids`。
3. 添加供用户裁决的 `q_*` / `act_*`（`pending`）。
4. 在用户裁决前保持 `resolution: null`。

---

## Unknowns

在缺失信息很可能导致捏造时创建：

- 文档中没有的环境特定值
- 负责人 / 值班
- 某功能是否已上线
- 未读二进制内部内容
- 缺少可保留文本且该缺失阻碍信任的确认

不要滥发琐事。

---

## 双语保真

- 译文中保留认识力（“可能”不得变成 “is”）。
- 不宜翻译 → 目标侧留空 + `manifest.limitations`。

---

## 与脱敏的交互

若脱敏移除或改变了唯一支撑摘录 / 定位器充分性：

1. **不要**保留 `verified`。
2. 降级为 `unverified`；若内容已不可用则用 Unknown。
3. 切勿为保留验证而重新展开密钥。
4. 记入证据 `notes` / `redaction_applied` 与 manifest 脱敏 limitations（尽力而为，非完整发现）。
