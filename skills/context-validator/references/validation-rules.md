# 校验规则目录（CBHF 0.1.0）

权威：`docs/context-validator-design.zh-CN.md` + `spec/cbhf/v0.1.0/*.schema.json` + exporter references。
**不得发明协议字段。**

## 结果码（逐项检查）

`PASS` | `FAIL` | `WARNING` | `NOT_CHECKED` | `NEEDS_HUMAN_REVIEW`

## 能力说明（Phase 3B-C2）

下列检查均已**定义**。自动化状态：

| 层 | 自动化 |
| --- | --- |
| L1 (P01–P07) | 已在 `scripts/validate_package.py` 实现 |
| L2 (S01–S15) | 已在 `scripts/validate_package.py` 实现 |
| L3-A (I01–I09, I15, I17–I19) | 已在 `scripts/_integrity.py` 实现 |
| L3-B1 (I11, I10) | 已在 `scripts/_integrity.py` 实现 |
| L3-B2 (I16) | 已在 `scripts/_integrity.py` 实现（Option C） |
| L3-B3 (I12) | 已在 `scripts/_integrity.py` 实现（line_range 边界） |
| L3-B4 (I13) | 已在 `scripts/_integrity.py` 实现（Option B — 无 finders） |
| L3-C I14 | **规则已冻结**，且在 `scripts/_integrity.py` **已自动化**（line_range 摘录匹配） |
| L3-C I20 | **规则已冻结**，且在 `scripts/_integrity.py` **已自动化**（可选 package_copy SHA-256） |
| L4 (H01–H06) | **未**自动化 — 永不语义 PASS |

任何未实际执行的项 → `NOT_CHECKED`。
`tests/schema/v0.1.0/package_smoke_test.py` **不是**本目录的自动化。

## 层级提醒（L3）

| 档 | 含义 | 层 |
| --- | --- | --- |
| A | 引用 ID 存在 | L3 |
| B | Locator 路径/范围有效 | L3 |
| C | 摘录文本可在窗口内匹配 | L3 |
| D | 摘录对命题/状态在语义上充分 | **仅 L4** |

文件存在 ≠ 可解析 ≠ schema-valid ≠ 引用存在 ≠ locator 有效 ≠ 摘录可匹配 ≠ 语义充分。

---

## L1 — 包校验

### P01 — 必需路径存在

| 字段 | 内容 |
| --- | --- |
| 对象 | 包根 |
| 输入 | 目录列表 |
| 逻辑 | 要求 Exporter 必需树：`manifest.yaml`、`source/source-index.json`、`source/original/`、`knowledge/overview.md`、`knowledge/facts.json`、`knowledge/claims.json`、`knowledge/decisions.json`、`knowledge/constraints.json`、`knowledge/glossary.json`、`evidence/evidence.json`、`evidence/references.json`、`uncertainty/unknowns.json`、`uncertainty/conflicts.json`、`handoff/receiver-guide.md`、`handoff/questions.json`、`handoff/recommended-actions.json` |
| PASS | 全部存在 |
| FAIL | 任一缺失 |
| NOT_CHECKED | 无法列出目录 |
| 输出 | 缺失路径列表 |

### P02 — Markdown 可读

| 字段 | 内容 |
| --- | --- |
| 对象 | `knowledge/overview.md`、`handoff/receiver-guide.md` |
| 输入 | 文件字节 |
| 逻辑 | UTF-8 可读文本 |
| PASS | 两者均可读 |
| FAIL | 不可读 / P01 后仍缺失 |
| NOT_CHECKED | 主机无法读取文件 |
| 输出 | 哪个文件失败 |

### P03 — JSON 可解析（拒绝重复键）

| 字段 | 内容 |
| --- | --- |
| 对象 | 包内全部 `.json` 文件 |
| 输入 | 文件文本 |
| 逻辑 | 解析为 JSON；**重复键必须 FAIL**（仅靠会静默覆盖的解析器不够） |
| PASS | 全部解析；未检测到重复键 |
| FAIL | 语法错误或重复键 |
| NOT_CHECKED | 无感知重复键的解析器可用 |
| 输出 | 文件 + 解析错误 |

### P04 — YAML 可解析（拒绝重复键）

| 字段 | 内容 |
| --- | --- |
| 对象 | `manifest.yaml` |
| 输入 | 文件文本 |
| 逻辑 | 以唯一键强制解析 YAML |
| PASS | 解析成功；无重复键 |
| FAIL | 语法 / 重复键 |
| NOT_CHECKED | 无唯一键 YAML 加载器 |
| 输出 | 错误详情 |

### P05 — 包形态

| 字段 | 内容 |
| --- | --- |
| 对象 | 布局 + 可读时的 manifest `package_form` / `scenario` |
| 输入 | 树 + 可用时已解析的 manifest |
| 逻辑 | 期望文件夹包；对 0.1.0 docs 场景，`package_form` 应当为 `folder`，`scenario` 为 `docs` |
| PASS | 文件夹布局一致 |
| FAIL | 明显不是 CBHF 文件夹根 |
| NOT_CHECKED | Manifest 不可读 |
| 输出 | 观察到的形态 |

### P06 — 额外 / 意外条目

| 字段 | 内容 |
| --- | --- |
| 对象 | 顶层与显著额外项 |
| 输入 | 树枚举 |
| 逻辑 | 未知顶层 → **WARNING**（白名单未冻结 — 开放问题 Q1）。**CBHF 0.1.0：** `validation/` 为预留路径且**写入未启用**；期望树不含该目录。若出现 `validation/` → 视为意外额外项 → **WARNING**（不得当作正式包内校验已启用） |
| PASS | 无意外顶层 |
| WARNING | 存在意外额外项 |
| FAIL | （保留；0.1.0 默认不用） |
| NOT_CHECKED | 无法枚举 |
| 输出 | 额外路径 |

### P07 — 只读承诺

| 字段 | 内容 |
| --- | --- |
| 对象 | Validator 运行时行为 |
| 输入 | 进程意图 |
| 逻辑 | 不得修改 knowledge/evidence/source 副本。**CBHF 0.1.0：** 不写包内报告（`validation/` 预留未启用） |
| PASS | 无包变更 |
| FAIL | 校验期间包内知识被变更 |
| NOT_CHECKED | 无法核验文件系统 mtimes/hashes |
| 输出 | 若有，变更证据 |

---

## L2 — Schema 校验

Schema 位于 `spec/cbhf/v0.1.0/`（Draft 2020-12）。

### S01 — 加载 Schema

| 字段 | 内容 |
| --- | --- |
| 对象 | `*.schema.json` |
| 输入 | Spec 目录 |
| 逻辑 | 加载 + `check_schema` |
| PASS | 全部加载 |
| FAIL | Schema 文件损坏（Validator 工具错误） |
| NOT_CHECKED | Spec 路径不可用 |
| 输出 | Schema 加载错误 |

**S02–S14** 共用字段（各项为独立检查）：

| 字段 | 内容 |
| --- | --- |
| 输入 | 来自 L1 的已解析 JSON/YAML 对象 |
| 逻辑 | 对照所列 Draft 2020-12 schema 校验（不得发明字段） |
| PASS | 实例校验通过 |
| FAIL | 任一 schema 错误 |
| NOT_CHECKED | Schema 引擎不可用、S01 失败，或 L1 解析失败 |
| 输出 | 文件路径 + schema `$id` + 错误路径/消息 |

| ID | 对象 | Schema |
| --- | --- | --- |
| S02 | `manifest.yaml`（已解析） | `manifest.schema.json` |
| S03 | `source/source-index.json` | `source.schema.json` |
| S04 | `knowledge/facts.json` | `fact.schema.json` |
| S05 | `knowledge/claims.json` | `claim.schema.json` |
| S06 | `knowledge/decisions.json` | `decision.schema.json` |
| S07 | `knowledge/constraints.json` | `constraint.schema.json` |
| S08 | `knowledge/glossary.json` | `glossary.schema.json` |
| S09 | `evidence/evidence.json` | `evidence.schema.json` |
| S10 | `evidence/references.json` | `evidence.schema.json#/$defs/ReferencesDocument` |
| S11 | `uncertainty/unknowns.json` | `unknown.schema.json` |
| S12 | `uncertainty/conflicts.json` | `conflict.schema.json` |
| S13 | `handoff/questions.json` | `questions.schema.json` |
| S14 | `handoff/recommended-actions.json` | `recommended-actions.schema.json` |

### S15 — Enum / required / type / additionalProperties / if-then

| 字段 | 内容 |
| --- | --- |
| 对象 | 全部经 schema 校验的实例 |
| 输入 | 与 S02–S14 相同（关键字级失败的汇总） |
| 逻辑 | 由 schema 关键字覆盖（如 KnowledgeStatus 枚举、`verified`→`evidence_ids` minItems、`user_confirmed`→非 null `confirmation`、ReferenceStatus 仅为 `unverified`） |
| PASS | 除已在 S02–S14 报告者外，无 schema 违规 |
| FAIL | 非法枚举、缺 required、类型错误、禁止的额外字段、if-then 失败 |
| NOT_CHECKED | Schema 引擎不可用 |
| 输出 | 可能时使用类 JSON Pointer 路径 |

---

## L3 — 完整性校验

### I01 — 重复 ID（档 A）

| 字段 | 内容 |
| --- | --- |
| 对象 | 全部有类型的 ID（`source_id`、`fact_id`、`claim_id`、`decision_id`、`constraint_id`、`term_id`、`evidence_id`、`reference_id`、`unknown_id`、`conflict_id`、`question_id`、`action_id`、`package_id`） |
| 逻辑 | **在各类内部**唯一（跨类相同字符串允许） |
| PASS | 每个适用 id 集合均已加载并检查；无类内重复 |
| FAIL | 在任一**已加载**类中确认重复（即使其他集合缺失） |
| NOT_CHECKED | 无已确认重复，但一个或多个适用集合未加载 / 非 schema-ok |
| 输出 | 重复的 ids |

### I02 — evidence.supports → knowledge 存在（A）

| 逻辑 | 每个 `supports[{type,id}]` 可解析 |
| PASS/FAIL/NOT_CHECKED | 按常规 |

### I03 — knowledge.evidence_ids → evidence 存在（A）

| 逻辑 | facts/claims/decisions/constraints/terms 中每个 evidence_id 在 evidence.json 中存在 |

### I04 — 双向一致性（A）

| 逻辑 | 若 A 列出 ev_X 且 ev_X.supports 包含 A（类型匹配），反之亦然 |
| FAIL | 单向链接 |

### I05 — conflict.parties 存在（A）

| 逻辑 | party type+id 解析到 knowledge 对象 |

### I06 — conflict.evidence_ids 存在（A）

| 逻辑 | 每个 id 在 evidence.json 中 |

### I07 — 交叉 related_* ids（A）

| 对象 | `related_conflict_ids`、`related_unknown_ids`、`related_ids`、`conflict_ids`、`related_fact_ids` |
| 逻辑 | 目标存在；缺失则 **FAIL**（设计建议） |
| WARNING | 仅当策略日后软化时（开放问题） |

### I08 — confirmation.source_ref 对应 user_authored_source（A）

| 逻辑 | 当 `source_type=user_authored_source` 时，`source_ref` 必须是真实的 `source_id` |
| FAIL | 缺失 / 未知 source_id |

### I09 — locator.source_id 在索引中（A）

| 逻辑 | 每个 evidence locator.source_id ∈ source-index |

### I10 — locator.path 存在（B）

| 逻辑 | 相对包根的路径；文件存在 |
| FAIL | 文件缺失 |

### I11 — 路径安全（B）

| 逻辑 | 拒绝 `..`、绝对路径、盘符、UNC；解析后路径必须留在包根下；不跟随逃逸符号链接 |
| FAIL | 逃逸 / 禁止形态 |
| NOT_CHECKED | 主机无法解析符号链接 |

### I12 — line_range 边界（B）

冻结语义（**L3-B3 / I12**）。不实现 I13 可发现性或 I14 摘录匹配。不发明 Schema 字段。

| 字段 | 内容 |
| --- | --- |
| 范围 | 仅针对**已加载** evidence 中 `locator_type == "line_range"` 的项。非 `line_range` locator 在此**跳过**（I13）。 |
| Evidence FAIL | 对每个适用项，在通过 I11/I10 门控（见下）之后：`start` 与 `end` 必须各自非 null、有限、且为整数值；`start >= 1`；`end >= start`；`end <=` 文件行数。任一条件不满足 → FAIL（包括 `start` 或 `end` 任一为 `null` — **不得**将 `end=null` 合并为 `start`）。 |
| 行数计算 | `path.read_text(encoding="utf-8").splitlines()` 然后 `len(lines)` — 与 `package_smoke` 的 line_range 检查定义相同。成功读取保留为**内存文本快照**（按 evidence_id），供 I14 使用；快照**不得**写入校验报告或错误消息。 |
| 门控（不读路径） | 若 I11 将 locator.path 归为不安全或未解析 → 该项 NOT_CHECKED（不读文件）。若 I10 未确认路径作为包内文件存在 → 该项 NOT_CHECKED（不读文件）。 |
| 读取失败 | 门控之后 UTF-8 解码失败或其他读错误 → 该项 NOT_CHECKED（不对边界 FAIL）；该 evidence 无快照。 |
| PASS | Evidence 已加载；无 FAIL 项；且无适用项仍为 NOT_CHECKED。包括：已加载 evidence 中 **零** 个 `line_range` 项（空适用集）→ PASS。 |
| NOT_CHECKED | Evidence 未加载；**或**无 FAIL，但至少一个适用 `line_range` 项被门控/未读（I11/I10/读失败）。非 `line_range` 项**本身不会**使 I12 变为 NOT_CHECKED。 |
| 汇总 | 逐项检查：**FAIL > NOT_CHECKED > PASS**。部分跳过必须在 `errors`（或等价明细）中保留逐项 NOT_CHECKED 原因。任何适用项仍未检查时，**不得**报告整体 PASS。 |
| 说明 | Schema 仍可能允许 `line_range` 的 `null` start/end；I12 对 null 的 FAIL 是有意的（将计划项 L3-RQ2 关闭为 FAIL）。未知路径安全仍属 I11；存在性属 I10。Phase 3B-B3 已自动化。 |

### I13 — 其他 locator 类型（B）

冻结语义（**Option B**，L3-B4 / I13）。不发明 Schema 字段。不实现 finders。不裁决摘录↔窗口匹配（I14）或语义充分性（L4）。

| 字段 | 内容 |
| --- | --- |
| 范围 | 已加载 evidence 中 `locator_type` 属于 `{section, json_pointer, anchor, page_range}` 者。**`line_range` 不在范围内**（I12）。 |
| FAIL | **0.1.0 不对目标可发现性 FAIL。** 不得重新 FAIL locator 形态（L2 Schema）、line_range 边界（I12）、路径安全（I11）或路径存在（I10）。 |
| PASS | Evidence 集合完全加载，**且** I13 适用项数为 **零**（例如仅有 `line_range`，或空 evidence 数组）。 |
| NOT_CHECKED | Evidence 未加载；**或**存在一个或多个 I13 适用项且 0.1.0 **无**确定性 finder；**或**适用项被 I11 不安全/未解析 / I10 缺失 / 读或解析条件门控而无法可靠检查。仅合法 locator 字段形态**不得**视为“可发现”。 |
| 门控 | 与 I12 相同：I11 不安全/未解析 → 项 NOT_CHECKED，不读；I10 未确认文件存在 → 项 NOT_CHECKED，不读；无包外读取；无超出 I11/I10 的新路径解析策略。 |
| 汇总 | **FAIL > NOT_CHECKED > PASS**。保留逐项明细。任何适用项仍为 NOT_CHECKED 时不得报告整体 PASS。 |
| WARNING | 0.1.0 **不**将 WARNING 用作 I13 检查结果。无法确认目标 → `NOT_CHECKED`（可用原因/限制说明；不得扩展报告 Schema）。 |
| 语义边界 | 标题/锚点/页/JSON 节点对主张的“正确性”，以及摘录是否支撑命题，**不是** I13 自动 PASS（I14 / L4）。 |
| 说明 | Q2 可发现性深度仍对*未来* finder 强度开放；0.1.0 冻结 Option B（空适用 → PASS；有适用但无 finder → NOT_CHECKED）。Phase 3B-B4 已自动化（无 finders）。 |

### I14 — 摘录文本匹配（C）

历史意图（未变）：规范化换行；每个非空摘录行出现在 locator 窗口文本中（严于 smoke 的“仅首行”）；全部此类行匹配则 PASS；任一行缺失则 FAIL；无文本窗口 / 未读二进制时 NOT_CHECKED；**不**证明语义充分性（档 D / L4）。

冻结语义（**L3-C / I14**）。不发明 Schema 字段。不对非 `line_range` 类型实现 finders。**不**裁决摘录是否充分支撑主张或知识状态（L4）。**规则已冻结；Phase 3B-C1 已自动化。**

| 字段 | 内容 |
| --- | --- |
| 范围 | 已加载 evidence。**仅**对 `locator_type == "line_range"`（`evidence[].locator.excerpt`）做匹配。 |
| 范围外（逐项 NOT_CHECKED） | `section`、`json_pointer`、`anchor`、`page_range`：**无** finder，**无**文本窗口匹配。每项记为 NOT_CHECKED（`out_of_scope_type`），**参与**汇总（因此仅有这些类型的包 → 整体 NOT_CHECKED）。不得重新检查 I13 可发现性。 |
| 窗口（必须与 I12 行号一致） | 仅在该项 I12 状态为 `pass` 之后。使用该 evidence 的 **I12 内存 UTF-8 文本快照**（与 I12 计行所用字节相同）。`lines = text.splitlines()`；`window = "\n".join(lines[start - 1:end])`。**不得**为匹配窗口再次调用 `read_text`。 |
| 换行规范化（仅摘录，在 split 前） | `\r\n` → `\n`；单独 `\r` → `\n`。**无** Unicode NFC/NFD；**无**大小写折叠；**无**模糊或语义匹配。 |
| 空行 | normalize+split 之后：`line.strip() == ""` 的行为空，**跳过**（不参与匹配）。 |
| 非空行匹配 | 保留行**未 strip**（无额外 strip，无内部空白折叠）。要求 `excerpt_line in window`（字面子串）。摘录行在窗口内的顺序 / 连续性 / 相邻性**不**要求。 |
| 门控（不构建可信窗口） | 消费**逐 evidence** I12 状态（`pass`/`fail`/`not_checked`）与 I12 文本快照；不得独立重算边界以覆盖 I12。I12 `fail` → 项 NOT_CHECKED（`i12_failed`）。I12 `not_checked` → 项 NOT_CHECKED（可细化为 `i11_unsafe` / `i11_unresolved`）。I12 `pass` 但快照缺失 → NOT_CHECKED（`snapshot_missing`）；**不得**重读文件以恢复。source-index 未加载或 `source_id` 不可解析 → NOT_CHECKED（`source_readable_unresolved`）— 不得 PASS；不得重实现 I09。Source `readable: false` → NOT_CHECKED。无包外读取；无网络；不修改包。快照不得出现在校验报告或错误消息中。 |
| PASS | Evidence 集合完全加载；无 FAIL 项；且**无**项仍为 NOT_CHECKED。包括：(a) 每个 `line_range` 项在 I12 `pass` + `readable` 正常后匹配（或无非空摘录行）；(b) 已加载 evidence 项数为 **零**（空数组）。 |
| FAIL | 至少一个 `line_range` 项有可信窗口，且至少一个非空摘录行**不是**该窗口的字面子串。 |
| NOT_CHECKED | Evidence 未加载；**或**无 FAIL 但至少一项为 NOT_CHECKED（范围外类型、I12 门控、readable 门控、读失败等）。 |
| 汇总 | **FAIL > NOT_CHECKED > PASS**。保留逐项明细。任何项仍为 NOT_CHECKED 时不得报告整体 PASS。未加载 evidence **不得**当作空数组 PASS。 |
| WARNING | 0.1.0 **不**将 WARNING 用作 I14 检查结果。 |
| NEEDS_HUMAN_REVIEW | **不**用作 I14 检查结果；语义判断留在 L4。不得新增报告状态。 |
| 语义边界 | I14 PASS 仅表示每个非空摘录行可作为字面子串在 `line_range` 窗口中找到。它**不**表示语义充分性、主张支撑、证据真实性、正确的 `verified` 状态、冲突解决，或已完成人工 L4 审查。 |
| 说明 | 关闭计划项 L3-RQ3（无 Unicode 规范化）与 L3-RQ4（空摘录 → PASS，无 WARNING）。严于 `package_smoke` 的“仅首行摘录”。不对 I10/I11/I12/I13/I16 问题重新 FAIL。Phase 3B-C1 已自动化。 |

### I15 — verified ⇒ 非空 evidence_ids（A）

| 逻辑 | 加载后再检查（schema 亦强制） |
| FAIL | verified 但 evidence_ids 为空/缺失 |

### I16 — readable:false 源（A/B）

冻结语义（**Option C**）。不裁决摘录↔窗口匹配（I14）或语义充分性（L4）。

| 字段 | 内容 |
| --- | --- |
| 对象 | `source-index` `readable` + evidence `locator.source_id` / `locator.excerpt` + knowledge `status` / `evidence_ids` |
| Evidence FAIL | Evidence 的 `locator.source_id` 解析到 `readable: false` 的源，**且** `strip(excerpt) != ""`（strip 后非空）。空或仅空白的 `excerpt` **不会**仅因 Evidence 引用条款 FAIL。 |
| Knowledge FAIL | 任一 `status: verified` 的 knowledge 对象，其 `evidence_ids` 包含某 evidence，且该 evidence 的 `locator.source_id` 解析到 `readable: false` — **不论**该 evidence 的摘录是否为空。 |
| PASS | 必需集合已加载（见 NOT_CHECKED），且既无 Evidence FAIL 也无 Knowledge FAIL。无违规的空 evidence / knowledge 集合 → PASS。 |
| NOT_CHECKED | `source-index` 未加载和/或 `evidence` 未加载（无法评估任一分支）。若两者已加载但 verified 分支所需 knowledge 集合未加载 → NOT_CHECKED（不得报告 PASS）。 |
| 说明 | 未知 `locator.source_id` 属 I09；I16 仅在 source_id 可解析且 `readable` 为 false 时适用。不发明协议字段。Phase 3B-B2 已自动化。 |

### I17 — content_transformed 形态

| 逻辑 | 由 Schema 覆盖（`true`\|`false`\|`null`）— 在 S03 下记 PASS，或 schema 未跑时 NOT_CHECKED |
| 说明 | 列入目录以求完整 |

### I18 — manifest.validation 诚实性

| 字段 | 内容 |
| --- | --- |
| 逻辑 | 依赖 S02 PASS。若 `validation.present=true`，有效报告路径必须存在于包**内部**（显式 `report_path` 经 strip 后，否则默认 `validation/validation-report.json`）。拒绝绝对/`..`/UNC/盘符/符号链接逃逸。显式路径缺失不得被默认文件掩盖。 |
| PASS | `present` 不为 true（**0.1.0 常态**：Exporter `present: false`，包内报告未启用），或 `present=true` 且权威报告路径安全存在 |
| FAIL | `present=true` 且报告路径缺失/不安全 |
| NOT_CHECKED | S02 非 PASS / manifest 未加载 |
| 说明 | 0.1.0 Validator **不**设置 `present=true`。本检查防手搓/陈旧包撒谎。报告消息仅用原因码 + 包相对路径（无主机绝对路径）。不裁决报告内容语义。 |

### I19 — 孤儿 evidence（supports 为空）（A）

| 逻辑 | 协议偏好允许链接；空 supports → **WARNING** |

### I20 — 校验和（可选）

冻结语义（**L3-C / I20**，CBHF 0.1.0）。对**包内副本**的可选按源完整性检查。不发明 Schema 字段。不证明源真实性、保管链或语义充分性（L4）。规则在 `scripts/_integrity.py` **已冻结并自动化**。

| 字段 | 内容 |
| --- | --- |
| 范围 | 已加载的 `source/source-index.json` 条目。对象文件 = 在包根下解析的 `sources[].package_path`。 |
| 适用 vs 排除 | 在以下情况**无适用校验和值**：缺少 `checksum` 对象；`checksum` 为 `null`；缺少 `value`；`value` 为 `null`；或 `value` 为 `""`。每个此类源条目**必须**标为项级 `NOT_CHECKED`，且**必须**从包级汇总中**排除**（不参与汇总）。**不得**将“零适用条目”当作 I12/I14 空适用的 **PASS** — 若每个源都缺少适用校验和值，包级 I20 **必须**为整体 **NOT_CHECKED**。 |
| 适用（参与汇总） | `value` 为非空字符串。然后要求：`alg` 精确为 `"sha256"`（区分大小写；无默认）；`of` 精确为 `"package_copy"`（区分大小写；无默认；缺失/其他 → 项 `NOT_CHECKED`）；`value` 精确 64 位十六进制字符（接受 A–F/a–f；比较前将声明值规范化为**小写**；畸形非空 → 项 `NOT_CHECKED`，**不是** FAIL）。 |
| 哈希输入 | 已解析 package-copy 文件（`package_path`）的精确**原始字节**。校验时不得再施加文本规范化、脱敏或编码变换。摘要 = SHA-256 hex（小写比较）。 |
| 路径安全 | 相对包根解析 `package_path`。最终目标必须留在包根内。仅当符号链接最终解析目标为包根内的**常规文件**时才允许。逃逸或未解析的符号链接不安全。**不安全 / 未解析 → 项 `NOT_CHECKED`，且零次文件内容读取。** 路径缺失、非文件或读失败 → 项 `NOT_CHECKED`（参与）。对相对路径复用与 I11 路径安全相同的包含分类方法；I20 **不**扩展 I11 范围（I11 仍仅针对 evidence `locator.path`）。 |
| PASS（项） | 适用；路径安全；文件可读；`alg`/`of`/`value` 形态 OK；重算摘要等于规范化后的声明值。 |
| FAIL（项） | 适用；已获得可信哈希；摘要**不匹配**。**CBHF v0.1.0：校验和不匹配为 FAIL。** 不匹配时**永不** WARNING。 |
| NOT_CHECKED（项，参与） | 适用但无法校验：坏/缺失的 `alg` 或 `of`；畸形非空 `value`；不安全/未解析路径；缺失/非文件；读失败；source-index 未加载（检查级）。 |
| 汇总 | 仅在**适用**项中：**FAIL > NOT_CHECKED > PASS**。被排除（无 value）的条目不驱动 PASS。零适用条目 → 整体 **NOT_CHECKED**。 |
| WARNING | 0.1.0 **不**将 WARNING 用作 I20 不匹配的检查结果。 |
| 多源同路径 | 每个源条目独立比较。允许按路径缓存读/摘要。 |
| 说明 | 对 0.1.0 关闭开放问题 Q3 与 L3-RQ6（`of` 必须精确为 `package_copy`）。只读；无包写入；无网络。不确立上游用户文件真实性。 |

---

## L4

见 [semantic-review-boundary.md](semantic-review-boundary.md)。L4 检查**永不**为自动化语义 PASS。

---

## 开放问题（仅记录）

- Q1 额外文件：警告 vs 失败
- Q2 section/page 可发现性深度 — **0.1.0 I13 Option B 已冻结：** 无 finder；适用项 → `NOT_CHECKED`（非 WARNING）；空适用 → PASS。更深 finders / 缺失则 FAIL 仍属未来 Q2，不得声称已核验。
- Q3 校验和不匹配严重性 — **CBHF v0.1.0 已关闭：** 校验和不匹配为 **FAIL**（非 WARNING）。见 § I20。
- Q4/Q5 包内写入报告 — **CBHF 0.1.0 已冻结为：仅会话报告**；`validation/` 路径预留、写入未启用；不翻转 `manifest.validation`
- handoff `priority` 字符串 vs 未来枚举（cbhf-format #12）
