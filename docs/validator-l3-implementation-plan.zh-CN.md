# context-validator — Phase 3A：L3 Integrity 实施前审计

**文档类型：** 实施前审计 / 测试设计（含 Phase 3B 进度附录）  
**协议版本：** CBHF 0.1.0（不修改）  
**日期：** 2026-11-19  
**状态：** 审计底稿保留；**Phase 3B 进度见 §10–§11**（Batch B 全部关闭；I14 规则已冻结且已实现；**I20 规则已冻结且已实现**（Phase 3B-C2））  
**依据：** `validation-rules.md` I01–I20、`docs/context-validator-design.zh-CN.md` §5.3、`scripts/validate_package.py`、`examples/technical-proposal/generated-output/`、`tests/semantic-review/v0.1.0/`

---

## 0. 审计结论摘要

| 结论 | 说明 |
| --- | --- |
| 编号 | **不重新定义** I01–I20；本文件只做映射与实施设计 |
| 可完全自动化 | I01–I12、I14–I16、I18–I19；I17 为 Schema 覆盖项的 Integrity 记账；I20 在有 `checksum.value` 时可自动化 |
| 需降级 / 部分自动化 | **I13**（0.1.0 **Option B 已冻结并正式关闭**：无查找器；更深「找得到」属未来，非本版） |
| 不得当语义结论 | **I14 PASS ≠ 语义充分**；双向链接 PASS ≠ Evidence 真正支持命题（L4 H01） |
| 协议歧义（不擅自裁决） | ~~Q2（I13）~~ → **0.1.0 已冻结关闭 Option B**；~~Q3（I20）~~ → **0.1.0 已关闭：mismatch=FAIL**；~~checksum.`of`~~ → **须精确 `package_copy`（L3-RQ6 已关闭）**；仍开放：I07 中无类型 `related_ids` 的解析范围、I11 Windows 大小写 |
| L1/L2 | **无需改检查语义**；Phase 3B 仅需兼容性接线（去掉 I\* 桩、`l3_implemented`、复用已解析对象） |
| 包级状态 | L3 任一项硬 FAIL → `invalid`；L3 全跑通且仅 WARNING → 可进入 `structurally_valid_with_warnings` / `semantically_unreviewed`；**禁止**把 L3 PASS 说成整包语义有效 |

### 重点方向 → 已有 I\* 映射（禁止新增协议规则）

| 重点方向 | 映射到 |
| --- | --- |
| 跨文件重复 ID | **I01** |
| 对象间引用存在 | **I02, I03, I05, I06, I07, I08, I09** |
| Evidence 双向关联 | **I04**（依赖 I02/I03 的存在性前提） |
| related_* 引用 | **I07** |
| confirmation.source_ref 存在性 | **I08** |
| Locator 文件路径存在 | **I10** |
| Line range | **I12** |
| Excerpt 匹配 | **I14**（档 C；非语义） |
| readable:false | **I16** |
| 路径穿越 / 绝对路径 / symlink | **I11**（并与 I10 协同） |

---

## 1. I01–I20 完整映射表

**档位：** A=引用存在 · B=定位有效 · C=摘录可匹配 · （D=语义充分 → **仅 L4，不在 I\***）

| ID | 名称 | 档 | 输入文件 | 确定性逻辑（摘要） | PASS | FAIL | WARNING | NOT_CHECKED | Open Q / 边界 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I01 | 重复 ID | A | manifest + 全部知识/证据/不确定性/handoff JSON | 各 **kind 命名空间内** id 唯一 | 无重复 | 同 kind 重复 | — | 相关文件未加载 | package_id 仅与其他 package_id 比 |
| I02 | supports → 知识存在 | A | evidence.json + facts/claims/decisions/constraints/glossary | 每个 `supports[{type,id}]` 在对应桶可解析 | 全部分辨 | 任一条缺失 | — | evidence 或目标桶未加载 | type 非法已由 Schema；Integrity 再确认 |
| I03 | evidence_ids → evidence 存在 | A | 知识五件套 + evidence.json | 每个 `evidence_ids[]` ∈ evidence | 全部存在 | 任一条缺失 | — | 文件未加载 | — |
| I04 | 双向一致 | A | 同 I02+I03 | supports 与 evidence_ids **对称** | 双向一致 | 单向链接 | — | I02/I03 所需对象未加载 | 不判断命题是否被支持 |
| I05 | conflict.parties 存在 | A | conflicts.json + 知识桶 | party `type+id` 可解析 | 全部存在 | 缺失 | — | 未加载 | 不裁决是否真冲突（L4） |
| I06 | conflict.evidence_ids 存在 | A | conflicts + evidence | id ∈ evidence | 全部存在 | 缺失 | — | 未加载 | — |
| I07 | related_* / conflict_ids 等 | A | questions/actions/unknowns/claims/知识.conflict_ids | 目标 id 存在（见 §1.1） | 全部可解析 | **建议 FAIL**（设计推荐） | 仅当日后软化策略 | 未加载 | **歧义：** 无类型 `related_ids` 搜索范围 |
| I08 | confirmation.source_ref | A | 知识确认对象 + source-index | `source_type=user_authored_source` ⇒ `source_ref` 为真实 `source_id` | 条件满足或无需检查 | 缺失/伪造 | — | confirmation 或 source 未加载 | 真实性属 L4 H03 |
| I09 | locator.source_id | A | evidence + source-index | `locator.source_id` ∈ sources | 全部命中 | 未知 source_id | — | 未加载 | — |
| I10 | locator.path 存在 | B | evidence + 包文件系统 | path 相对包根且文件存在 | 全部存在 | 缺失 | — | path 不安全已 FAIL 于 I11 时可仍报告；文件未读 | 先/并与 I11 |
| I11 | path 安全 | B | evidence.locator.path（及可选 package_path） | 禁 `..`、绝对路径、盘符、UNC；resolve 后不得逃出包根；**不跟随逃逸 symlink** | 全部安全 | 逃逸/禁止形式 | — | 宿主无法 resolve symlink 时该项可 NOT_CHECKED | Windows 大小写见风险 |
| I12 | line_range 边界 | B | evidence + 源文件文本 | **已冻结并实现（L3-B3）**：仅 `line_range`；非 null/有限/整数语义；`start≥1`；`end≥start`；`end≤len(UTF-8 splitlines())`；I11/I10 门控后才读；汇总 FAIL>NOT_CHECKED>PASS（见 `validation-rules.md`） | 无 FAIL 且无适用项未检查（含空适用集） | 越界/非法/null | — | evidence 未加载；或 I11/I10/读失败导致适用项未检查 | **L3-RQ2 已冻结为 null→FAIL**；Schema 仍允许 null；独立审查 CONDITIONAL PASS；**B3 已关闭** |
| I13 | 其他 locator 类型 | B | evidence | **已冻结、已实现、已关闭（Option B / L3-B4）**（见 `validation-rules.md`）：适用 `section`/`json_pointer`/`anchor`/`page_range`；**不含** `line_range`（仍归 I12）；0.1.0 **无**查找器、**无**找得到性 FAIL；不重复 Schema/I10/I11/I12；汇总 FAIL>NOT_CHECKED>PASS；**不用** I13 WARNING | 已加载且 **零** 适用项（空 evidence 或仅 `line_range`） | —（0.1.0 不新增目标存在 FAIL） | — | evidence 未加载；或存在适用项（`no_finder` / I11 门控原因） | **Q2 0.1.0 已冻结关闭**；更深查找器属未来；独立审查 **CONDITIONAL PASS**；**B4 正式关闭** |
| I14 | excerpt 文本匹配 | C | evidence + line_range 窗口文本 | **规则已冻结且已实现（L3-C / I14）**（见 `validation-rules.md`）：仅 `line_range`；窗口=`"\n".join(splitlines()[start-1:end])`；excerpt 换行规范化后逐非空行字面 `in`；空 excerpt PASS；I11/I10/I12/`readable:false`/读失败 → NOT_CHECKED；汇总 FAIL>NOT_CHECKED>PASS；**不用** WARNING；消费 I12 文本快照 | 适用项全匹配 / 空非空行 / 空适用集（已加载） | 可信窗口下任一行缺失 | — | evidence 未加载；或适用项门控/不可读窗口；非 line_range 逐条 out-of-scope | **≠ 语义充分（L4）**；L3-RQ3/RQ4 **已关闭** |
| I15 | verified ⇒ evidence_ids 非空 | A | 知识对象 | status=`verified` ⇒ evidence_ids 非空 | 满足 | 空/缺失 | — | 知识未加载 | Schema 已约束；Integrity 再确认 |
| I16 | readable:false | A/B | source-index + evidence + 知识 | **冻结 Option C**（见 `validation-rules.md`）：Evidence 仅 `readable:false` + `strip(excerpt)!=""` → FAIL；Knowledge 凡 `verified` 依赖指向 `readable:false` 的 evidence → FAIL（不以 excerpt 空豁免） | 无违规且集合齐全 | Evidence quoting 或 verified 依赖 | — | source/evidence 未加载；或 knowledge 未齐全且无 Evidence FAIL | ~~空 excerpt + readable:false 仍建议 FAIL~~ → **已由 Option C 取代**：空/空白 excerpt **不**因 Evidence quoting 单独 FAIL；空 excerpt + verified 仍 Knowledge FAIL |
| I17 | content_transformed 形状 | Schema | source-index | `true\|false\|null` 已由 S03 保证 | 若 S03 PASS → 本项 PASS（记账） | — | — | S03 未跑 → NOT_CHECKED | 不重复发明枚举 |
| I18 | manifest.validation 诚实 | — | manifest + 是否存在 validation 报告文件 | `present=true` 但无报告 → FAIL；`present=false` 且无报告 → **正常** | present 与文件系统一致 | present=true 无报告 | present=false 无报告可记 NOTE 或 PASS（非 WARNING 强制）；设计写 WARNING 可选——**推荐 PASS+message** 避免噪声 | manifest 未加载 | Phase 2 默认不写 validation/ |
| I19 | 孤儿 evidence | A | evidence | `supports` 为空 | 无空 supports | — | 存在空 supports | evidence 未加载 | 协议允许未指派 |
| I20 | checksum（可选） | — | source.checksum + `package_path` 文件 | **规则已冻结且已实现**（见 `validation-rules.md` / `_integrity.check_i20`）：适用非空 `value`；仅 `alg=="sha256"` 且 `of=="package_copy"`；对 `package_path` **raw bytes** SHA-256；64 hex（大小写可，比较前小写）；汇总 FAIL>NOT_CHECKED>PASS；零适用 → 整体 NOT_CHECKED | 适用项全匹配 | **FAIL**（mismatch；不用 WARNING） | — | 无适用 value；或适用但 alg/of/格式/路径/读失败 → 项 NOT_CHECKED | **Q3/L3-RQ6 已关闭**；generated-output 含 sha256 |

### 1.1 I07 目标解析约定（实施建议，不改协议）

| 字段 | 解析目标集合 |
| --- | --- |
| `questions[].related_conflict_ids` | `conflict_id` |
| `questions[].related_unknown_ids` | `unknown_id` |
| `claims[].related_fact_ids` | `fact_id` |
| `*.conflict_ids`（知识对象） | `conflict_id` |
| `unknowns[].related_ids` | **无类型**：在全包已知 id 集合中查找（fact/claim/decision/constraint/term/evidence/conflict/unknown/question/action/source） |
| `actions[].related_ids` | 同上（无类型） |

若某 id 在任何已知集合均不存在 → FAIL。  
**Open Question L3-RQ1：** 无类型 `related_ids` 是否应限制前缀启发式；0.1.0 建议“全集合存在性”，不发明类型字段。

### 1.2 依赖关系（门控）

```text
L1 解析成功(P03/P04) ──► 构建 ID 索引
         │
         ▼
I01 ──► I02,I03,I05,I06,I07,I08,I09,I15,I19
I02+I03 ──► I04
I09 ──► I10,I11,I12,I14,I16（逻辑上；实现可并行但失败信息分开）
I11 FAIL（逃逸）──► 对同一 path 的 I10/I12/I14 建议 NOT_CHECKED（避免读包外）
I10 FAIL（缺失）──► I12/I14 对该 evidence NOT_CHECKED
I12 窗口可得 ──► I14
S03 PASS/NOT ──► I17
manifest 解析 ──► I18
source checksum 字段 ──► I20
```

**全局门控：** 若 L1 导致关键 JSON 未解析，所有依赖该文件的 I\* → `NOT_CHECKED`（不得 PASS）。  
**不要求** L2 全部 PASS 才跑 L3；但 Schema 严重失败时对象形状不可信 → 依赖字段的 I\* 宜 NOT_CHECKED。推荐：**L2 对应文件 FAIL 时，对该文件导出的索引跳过并 NOT_CHECKED 相关 I\***。

---

## 2. A/B/C 实施批次

按档位分批交付（仍使用原编号；批次 ≠ 改号）。

### Batch A — 引用存在（优先）

**范围：** I01, I02, I03, I04, I05, I06, I07, I08, I09, I15, I19（+ I17/I18 记账项可同批）

**价值：** 与 smoke「basic id/link integrity」对齐并超集（补 related_*、重复 ID、source_ref、orphan warn）。  
**风险：** 低；纯内存图。  
**输出：** 断链 / 重复 id 列表。

### Batch B — 定位有效

**范围：** I10, I11, I12, I13（I13 默认保守）, I16 的路径/可读协同部分

**价值：** 路径安全与行号边界；堵住 `../` 与 symlink 逃逸。  
**风险：** 中（Windows 路径、symlink 权限）。  
**I13 策略（已冻结 Option B，不改协议）：** 适用非 `line_range` 四类；**类型形状不重复 FAIL**（Schema）；0.1.0 **不实现** heading/pointer/anchor/page 查找器；有适用项 → `NOT_CHECKED`；空适用集 → `PASS`；**不用** I13 WARNING。

**Phase 3B 子批进度（实现态，非改协议）：**

| 子批 | 范围 | 状态 |
| --- | --- | --- |
| B1 | I11 → I10 | **正式关闭**（已实现 / 已测试） |
| B2 | I16 Option C | **正式关闭**（已实现 / 已测试） |
| B3 | I12 line_range bounds | **正式关闭** — 已实现、已测试、独立审查 **CONDITIONAL PASS**（详见 §10.4） |
| B4 | I13 Option B | **正式关闭** — 已实现、已测试、独立审查 **CONDITIONAL PASS**（详见 §10） |

### Batch C — 摘录可匹配

**范围：** I14（+ I20 可选同批或紧随）

**价值：** 强于 smoke 首行；对齐 `_check_excerpts.py` 与人工审查中的“可定位”。  
**风险：** 中（换行规范化、门控与窗口一致性）。  
**硬规则：** I14 PASS **不得**写入语义充分或 H01 PASS。

**Phase 3B / Batch C 进度（实现态，非改协议）：**

| 子批 / 项 | 范围 | 状态 |
| --- | --- | --- |
| C / I14 | Excerpt text match | **规则已冻结且已实现**（见 `validation-rules.md` §I14 / `_integrity.check_i14`） |
| C / I20 | Checksum（可选） | **规则已冻结且已实现**（见 `validation-rules.md` §I20 / `check_i20`；Q3/L3-RQ6 已关闭） |
| Importer | context-importer | **尚未开始** |

---

## 3. 每项检查的测试矩阵

**通则：**

- 全部使用 **临时目录副本**；禁止改 `generated-output` / `input` / 人工审查文件。  
- 正常基线：① 临时复制 `generated-output`；② Phase 2 最小合法包；③ 空集合包。  
- 预期状态码与 `report-format` 一致：`PASS|FAIL|WARNING|NOT_CHECKED`。  
- 错误信息须含 **对象 id** 与 **相对路径**（隐私：不用用户绝对路径）。

### 3.1 共享正常样本

| 样本 | 预期（Batch 全部实现后） |
| --- | --- |
| `generated-output` 临时副本 | I01–I12,I14–I16,I18 PASS；I19 PASS（无孤儿）；I17 PASS；I20 PASS（现有 sha256）；I13 对全 line_range 包 → PASS 或空集 PASS；L3 层非 FAIL；**L4 仍 NOT_CHECKED**；包级 ≠ 语义 PASS |
| 最小合法包 | 同结构 PASS（无 checksum → I20 NOT_CHECKED） |
| 空集合包 | I01–I06 等空图 PASS；I14 空 evidence PASS；I19 PASS |

### 3.2 分项矩阵

#### I01 重复 ID

| 样本 | 预期 | 错误信息要点 |
| --- | --- | --- |
| 正常无重复 | PASS | — |
| 两 fact 同 `fact_id` | FAIL | `fact_id=… duplicate` |
| fact_id 与 claim_id 同字符串 | PASS | 跨 kind 允许 |
| 边界：空集合 | PASS | — |

#### I02 supports → 知识

| 样本 | 预期 |
| --- | --- |
| 正常双向包 | PASS |
| supports 指向不存在 claim | FAIL |
| 重复 supports 同一 id（仍存在） | PASS（存在性） |
| evidence 文件缺失（L1 已 FAIL） | NOT_CHECKED |

#### I03 evidence_ids → evidence

| 样本 | 预期 |
| --- | --- |
| 正常 | PASS |
| fact 引用缺失 ev | FAIL |
| 重复 evidence_ids 同一存在 id | PASS |

#### I04 双向

| 样本 | 预期 |
| --- | --- |
| 对称 | PASS |
| 仅 knowledge 有 evidence_ids | FAIL |
| 仅 evidence.supports | FAIL |

#### I05 / I06 conflict

| 样本 | 预期 |
| --- | --- |
| cfl 正常（如 generated-output） | PASS |
| party 缺失 | FAIL |
| evidence_ids 缺失 | FAIL |

#### I07 related_*

| 样本 | 预期 |
| --- | --- |
| questions→cfl/unk 存在 | PASS |
| related_conflict_ids 指向假 id | FAIL |
| actions.related_ids 指向假 id | FAIL |
| related_fact_ids 假 id | FAIL |
| 边界：空数组 | PASS |

#### I08 source_ref

| 样本 | 预期 |
| --- | --- |
| user_authored_source + 真 source_id（generated-output dec_*） | PASS |
| user_authored_source + null/假 id | FAIL |
| conversation + source_ref null | PASS（本规则不适用） |

#### I09–I11 路径 / 安全

| 样本 | 预期 | 说明 |
| --- | --- | --- |
| 正常相对 path | I09/I10/I11 PASS | |
| 未知 source_id | I09 FAIL | |
| path 文件缺失 | I10 FAIL | |
| `../outside.md` | I11 FAIL；I10/I12/I14 NOT_CHECKED | 不读包外 |
| `C:\…` / `/etc/passwd` / UNC | I11 FAIL | |
| symlink 指向包外 | I11 FAIL 或 NOT_CHECKED | 宿主相关 |
| symlink 指向包内合法文件 | PASS | 可选边界 |
| 空 path | I11 FAIL | |

#### I12 line_range（冻结规则已落地；B3 已关闭）

| 样本 | 预期 |
| --- | --- |
| start=1,end=1 单行文件 | PASS |
| end > 行数 | FAIL |
| start=0 或 end\<start | FAIL |
| start/end null | **FAIL**（L3-RQ2 冻结；禁止 `end=null` 回退为 start） |
| 仅 section 类型证据 | 本检查对该条跳过；无 line_range 时 I12 PASS |
| I11 unsafe / I10 missing / 读失败 | 该条 NOT_CHECKED；汇总 FAIL > NOT_CHECKED > PASS |

#### I13 其他类型（冻结 Option B；B4 已关闭）

| 样本 | 预期 |
| --- | --- |
| evidence 未加载 | **NOT_CHECKED**（与空集合区分） |
| 空 evidence（已加载）/ 仅 `line_range` | **PASS**（零适用项；`line_range` 归 I12） |
| 含 `section` / `json_pointer` / `anchor` / `page_range`（任一或混合） | **NOT_CHECKED**；逐条明细；原因含 `no_finder`（或 I11 门控） |
| `line_range` + 适用类型混合 | I13 仅对适用类型 NOT_CHECKED；I12 仍独立评 `line_range` |
| I11 unsafe / unresolved | 该条 NOT_CHECKED；**不读**包外 / **不**为找得到性打开文件 |
| 禁止因「字段形状合法」判可定位 PASS | — |
| 禁止 I13 WARNING；禁止找得到性 FAIL（0.1.0） | — |
| 语义正确性 / excerpt↔窗口 | 非 I13（I14/L4） |

#### I14 excerpt（规则已冻结且已实现）

| 样本 | 预期 | 说明 |
| --- | --- | --- |
| evidence 未加载 | **NOT_CHECKED** | 不得当作空适用集 PASS |
| 已加载且无 `line_range`（空适用集） | **PASS** | 非 line_range 非适用项 |
| `line_range` + 全部非空行 ∈ 窗口 | **PASS** | 窗口=`"\n".join(lines[start-1:end])`（与 I12 同行号） |
| 空 excerpt / 仅空白行 | **PASS** | L3-RQ4 已关闭；**不用** WARNING |
| 任一条非空行缺失 | **FAIL** | `excerpt_line in window`；不要求顺序/连续 |
| Unicode（中文/emoji） | PASS/FAIL 按码点字面 | L3-RQ3 已关闭：**不做** NFC/NFD |
| excerpt 含 CRLF/CR | 规范化为 LF 后再拆行匹配 | 文件侧仍用 `splitlines()` 建窗 |
| I11/I10/I12 失败；`readable:false`；读/UTF-8 失败 | 该适用项 **NOT_CHECKED** | 不得用不可信窗口判 PASS/FAIL |
| `section`/`json_pointer`/`anchor`/`page_range` | 逐条 out-of-scope（不匹配） | **无** finder；不单独迫使整体 NOT_CHECKED |
| 汇总 | FAIL > NOT_CHECKED > PASS | 不用 WARNING / 不新增 NEEDS_HUMAN |
| **PASS 含义** | 仅字面行可在窗口找到 | **≠** 语义充分 / claim 支撑 / L4（limitations 须声明） |

#### I15 verified

| 样本 | 预期 |
| --- | --- |
| verified + 非空 evidence_ids | PASS |
| verified + []（若绕过 Schema 的手工坏包） | FAIL |

#### I16 readable:false（冻结 Option C）

| 样本 | 预期 |
| --- | --- |
| readable:true + excerpt | PASS |
| readable:false + 非空 excerpt evidence | Evidence 侧 FAIL（`readable_false_excerpt`） |
| verified 知识依赖上述 evidence | Knowledge 侧 FAIL（`readable_false_verified`）；可与 Evidence 侧同时报告 |
| readable:false + 空 excerpt + non-verified | Evidence 侧**不**因 quoting 条款 FAIL；整体可 PASS |
| readable:false + 空 excerpt + verified 依赖 | Evidence 侧不因 quoting FAIL；**Knowledge 侧 FAIL** |
| readable:false 无 evidence 引用 | PASS |

#### I17 / I18 / I19 / I20

| ID | 正常 | 错误 / 边界 |
| --- | --- | --- |
| I17 | S03 PASS → I17 PASS | S03 NOT_CHECKED → I17 NOT_CHECKED |
| I18 | present=false 无 validation/ → PASS | present=true 无报告 → FAIL；有报告文件（未来）→ PASS |
| I19 | 无空 supports → PASS | 空 supports → WARNING（不升级 FAIL） |
| I20 | 适用且匹配 → PASS；零适用 → 整体 NOT_CHECKED | mismatch → **FAIL**（不用 WARNING）；未知/缺 alg 或 of、格式错、路径不安全、读失败 → 项 NOT_CHECKED（参与汇总） |

### 3.3 交叉 / 门控样本

| 场景 | 预期 |
| --- | --- |
| 缺 facts.json | P01 FAIL；I01/I02/… 依赖 facts 的 → NOT_CHECKED |
| JSON 重复键 | P03 FAIL；相关 I\* NOT_CHECKED |
| L2 某文件 Schema FAIL | 对该文件索引跳过；相关 I\* NOT_CHECKED |
| I11 逃逸 | 不打开包外文件；无异常泄漏绝对用户路径到报告 |

### 3.4 需新增的测试资产（设计，本阶段不建）

| 资产 | 用途 |
| --- | --- |
| `tests/validator/v0.1.0/run_l3_tests.py` | L3 套件入口 |
| 临时包工厂（扩展现有 `build_valid_minimal_package`） | 单点变异 I\* |
| `fixtures/l3/` 可选静态坏片段 | symlink / CRLF / Unicode 文件 |
| 只读哈希断言 | 与 Phase 2 相同 |
| 与 smoke 对照用例 | 同一包上 L3 ⊆ 超集 smoke 链接检查 |

---

## 4. Open Questions（只记录，不自动解决）

| ID | 问题 | 与 I\* | 实施前建议（非协议变更） |
| --- | --- | --- | --- |
| Q2 | section/page_range「找得到」深度 | I13 | **0.1.0 已冻结并关闭（Option B / L3-B4）：** 无查找器；有适用项 → NOT_CHECKED（不用 WARNING）；空适用 → PASS；无找得到性 FAIL。更深查找器 / 找不到→FAIL **不在 0.1.0 范围**（未来若重开，勿假装本版已验证） |
| Q3 | checksum 不匹配严重级别 | I20 | **0.1.0 已关闭：** mismatch → **FAIL**（不用 WARNING）；无适用 value → NOT_CHECKED（见 `validation-rules.md` §I20） |
| Q1 | 额外文件 warn/fail | 非 I\*（P06） | 保持 WARNING |
| Q4/Q5 | 是否写 validation/ | I18 相关 | Phase 3 仍默认不写包 |
| L3-RQ1 | 无类型 `related_ids` 解析范围 | I07 | 全已知 id 集合 |
| L3-RQ2 | line_range start/end null | I12 | **已冻结并关闭：FAIL**（见 `validation-rules.md` I12；B3 已实现） |
| L3-RQ3 | I14 是否 Unicode 规范化 | I14 | **已冻结并关闭：不做 NFC/NFD**；码点字面（见 `validation-rules.md` I14） |
| L3-RQ4 | I14 空 excerpt | I14 | **已冻结并关闭：PASS**；**不**使用 WARNING（见 `validation-rules.md` I14） |
| L3-RQ5 | I18 present=false 是否 WARNING | I18 | 建议 PASS + 说明，避免与 P06 噪声叠加 |
| L3-RQ6 | `checksum.of` 必须精确 `package_copy` | I20 | **0.1.0 已关闭：** 仅 `of == "package_copy"`；缺失或其他值 → NOT_CHECKED（无默认） |
| 协议 #12 | handoff.priority 枚举 | 非 L3 | 仍属 Schema/协议债 |

---

## 5. 风险分析

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 将 I14 PASS 误读为语义 PASS | 违背 Skills/L4 边界；与人工审查「充分性」混淆 | 报告 `limitations` + Skill 明文；测试断言无 H\* PASS |
| I11 误读包外 / symlink | 安全与隐私 | 先校验再读；报告只用相对路径 |
| Windows 路径大小写 / `\` | 假 FAIL/PASS | 统一 posix 相对路径；存在性用 Path 语义 |
| CRLF vs 行号 | I12/I14 漂移 | `splitlines()` 统一；测试夹具含 CRLF |
| I07 无类型 id 误匹配 | 假 PASS | 文档化全集合策略；测试假 id |
| I20 哈希算法扩展 | NOT_CHECKED 过多 | 仅实现 sha256；其余 NOT_CHECKED |
| L3 启用后包级状态变化 | Phase 2 测试期望 `not_fully_validated` | 更新 Skill/测试期望；保留 Phase 2 回归 |
| 与 smoke 重复维护 | 漂移 | L3 为权威；smoke 保持「非 Validator」名 |

**不能仅凭结构/文本匹配得出的结论（必须留给 L4）：**

- Evidence 是否真正支持命题（H01）  
- `verified` 是否合理（H02）  
- `user_confirmed` 是否现场确认（H03；generated-output 人工审查为 fixture 源）  
- 冲突是否业务真冲突 / 权威端口（H04/H06；8080 vs 8000）  
- 脱敏是否穷尽（H05）

---

## 6. 推荐实现顺序

1. **索引层：** 从 `parsed_objects` 构建 kind→id 映射与 evidence/knowledge 图（只读）。  
2. **Batch A：** I01 → I02/I03 → I04 → I05/I06 → I07 → I08/I09 → I15 → I19；I17/I18。  
3. **Batch B：** I11 → I10 → I12；I16；I13 Option B — **B1–B4 均已正式关闭**（见 §10）。  
4. **Batch C：** I14 — **规则已冻结且已实现**；I20 — **规则已冻结且已实现**（§I20 / Q3 / L3-RQ6；Phase 3B-C2）。  
5. **接线：** 替换 Phase 2 的 I\* `NOT_CHECKED` 桩；`package_final_status(..., l3_implemented=True)`；P07 仍在全部检查后。  
6. **测试：** `run_l3_tests.py` + 更新/并存 Phase 2 套件期望。  
7. **文档：** 更新 `SKILL.md` 能力表为 Phase 3；**不**开始 L4。

---

## 7. 预计新增与修改文件

### 7.1 预计新增（Phase 3B 编码时）

| 路径 | 职责 |
| --- | --- |
| `skills/context-validator/scripts/_integrity.py`（或同级模块） | I01–I20 实现，供 `validate_package.py` 调用 |
| `tests/validator/v0.1.0/run_l3_tests.py` | L3 测试矩阵 |
| `tests/validator/v0.1.0/fixtures/l3/`（可选） | CRLF/Unicode/symlink 夹具源 |

### 7.2 预计修改（最小兼容）

| 路径 | 变更性质 |
| --- | --- |
| `skills/context-validator/scripts/validate_package.py` | 调用 Integrity；去掉 I\* 桩；最终状态逻辑；**不改** P\*/S\* 检查语义 |
| `skills/context-validator/SKILL.md` | Phase 3 能力表与工作流 |
| `skills/context-validator/references/validation-rules.md` | 能力注记更新为 L3 已实现（Batch 完成后） |
| `tests/validator/v0.1.0/run_l1_l2_tests.py` | 期望：L3 不再整层 NOT_CHECKED；或拆分断言以免误伤 |

### 7.3 明确不修改

- `spec/cbhf/v0.1.0/*`  
- Exporter Skill / EXPECTED / generated-output / input  
- `tests/semantic-review/v0.1.0/*` 人工结论  
- Smoke 测试名称与「非 Validator」定位  
- L4 / H\* 自动化  

### 7.4 L1/L2 兼容性结论

| 项 | 是否需要改检查逻辑 |
| --- | --- |
| P01–P07 / S01–S15 判定规则 | **否** |
| 复用 `parsed_objects` / `parse_ok` / `fingerprint_*` | **是（接线）** |
| `package_final_status` 的 `l3_implemented` | **是（接线）** |
| 报告字段形状 | **否**（已预留 I\*） |
| Phase 2 测试对 `layers.L3 == NOT_CHECKED` 的断言 | **需随 Phase 3B 调整期望** |

---

## 8. 与首次真实包 / 人工审查的对齐（只读引用）

| 观察 | L3 含义 | 非 L3 |
| --- | --- | --- |
| 22 Evidence 可定位且行匹配（`_check_excerpts.py`） | I09–I12、I14 应对临时副本 PASS | 充分性仍属人工/L4 |
| `user_authored_source` + `src_003` | I08 结构 PASS | 现场确认真实性 NOT CHECKED（审查报告） |
| `cfl_001` 8080 vs 8000 | I05/I06 结构 PASS | 权威端口 NEEDS HUMAN |
| sources 带 sha256 | I20 可自动化验证 | — |
| 全 `readable: true` | I16 PASS | — |

**不得**因本审计或未来 L3 PASS 改写 `review-report.md` 结论。

---

## 9. 本阶段交付清单（3A 审计原文）

- [x] I01–I20 映射与依赖  
- [x] A/B/C 批次  
- [x] 测试矩阵与边界（Unicode/CRLF/symlink/空集合等）  
- [x] Open Questions  
- [x] 风险与实现顺序  
- [x] 预计文件变更  
- [x] Phase 3B 已按子批启动（见 §10；3A 当时“不实现”约束已结束）  

**3A 原文下一步（历史）：** 审查通过后启动 Phase 3B（先 Batch A）。

---

## 10. Phase 3B 进度 — L3-B4 / I13 正式关闭

| 字段 | 内容 |
| --- | --- |
| 子批 | **L3-B4** |
| 检查项 | **I13 — Other locator types（Option B）** |
| 规则权威 | `skills/context-validator/references/validation-rules.md` § I13（冻结 Option B；本关闭不改规则） |
| 实现 | `_integrity.check_i13` + `validate_package` phase `3B-B4` / `L3_B4_other_locators` |
| 测试 | `tests/validator/v0.1.0/run_l3_tests.py`（`test_b4_i13_other_locators` 等） |
| 独立审查 | **CONDITIONAL PASS**（无阻断问题） |
| 关闭结论 | **正式关闭 B4**；Batch B（B1–B4）全部正式关闭 |

### 10.1 关闭依据（摘要）

- **I13 Option B 已实现**：不实现任何 Locator 查找器；不产生找得到性 FAIL；`line_range` 仍归 I12。  
- **空适用集 → PASS**（evidence 已加载且零 `section`/`json_pointer`/`anchor`/`page_range`）。  
- **存在适用项 → NOT_CHECKED**（逐条明细；`no_finder` / I11 门控原因）。  
- 独立审查 **CONDITIONAL PASS**；**无阻断问题**；人工接受 N1–N6 为已知非阻断遗留。  
- 用户报告回归：L3 296 / L1+L2 99 / Schema 38 / Smoke 34 — 均 passed。  
- `generated-output` **HASH_IDENTICAL**；`read_only=true`；`network=false`；`wrote_to_package=false`。

### 10.2 遗留非阻断问题（I13 审查；本关闭任务不修复）

| ID | 说明 | 优先级 |
| --- | --- | --- |
| N1 | I13 不消费 I10 `CheckOut`：`path_safety=="safe"` 但文件缺失时逐条仍标 `no_finder`，不单独出现 `i10_missing`（汇总仍为 NOT_CHECKED） | 低 |
| N2 | 汇总 message 固定含 `(no finder)`，即使全部条目为 `i11_unsafe` 也可能误导 | 低 |
| **N3** | `errors[:50]` 明细截断：适用项 >50 时可能影响 NOT_CHECKED 明细完整性 | **后续优先改进** |
| N4 | 未知 `locator_type`（绕过 Schema）被跳过；若包内仅有此类可表现为空适用 PASS | 低 |
| N5 | `validate_package.py` 仍有 “deferred L3-B/C stubs” 类注释与 B4 已实现略不同步 | 低 |
| N6 | 关闭前计划文档进度曾停在 B3；以本 §10 为准同步后仍保留为审查当时记录 | 低 |

> 说明：上表为 **I13 / B4** 审查遗留项，**未修复**。B3/I12 的历史非阻断债见 §10.4（亦未在本任务修复）。

### 10.3 明确未做

- **未实现**任何 I13 Locator 查找器；未引入找得到性 FAIL。  
- 未改 Schema / Exporter / generated-output / input；未改 Python / 测试（本关闭仅更新本计划文档）。  
- B4 关闭后 Batch C：I14 规则已冻结且已实现；**I20 规则已冻结且已实现**（Phase 3B-C2）；Importer 仍未开始。  
- **未处理** N1–N6。

### 10.4 历史：L3-B3 / I12 正式关闭

| 字段 | 内容 |
| --- | --- |
| 子批 | **L3-B3** |
| 检查项 | **I12 — line_range bounds** |
| 规则权威 | `skills/context-validator/references/validation-rules.md` § I12 |
| 实现 | `_integrity.check_i12` + phase `3B-B3` |
| 独立审查 | **CONDITIONAL PASS**（无阻断问题） |
| 关闭结论 | **正式关闭 B3**（先于 B4） |

**B3 关闭依据（摘要）：** I12 规则与实现一致；当时回归 L3 258 / L1+L2 97 / Schema 38 / Smoke 34；`generated-output` HASH_IDENTICAL；只读 / 无网络 / 未写包。

**B3 遗留非阻断问题（历史记录，本任务仍不修复）：**

| ID | 说明 | 优先级 |
| --- | --- | --- |
| N1 | I12 未直接消费 I10 `CheckOut`，而是复用 `locator_path_is_file` 原语 | 低 |
| N2 | 过门控后重复 `resolve`；`ValueError` 与读失败一并归类 | 低 |
| **N3** | `errors[:50]` 截断可能影响 FAIL 场景下 NOT_CHECKED 明细完整性 | **后续优先改进** |
| N4 | 门控后零次 `read_text` 缺少插桩测试 | 低 |
| N5 | 测试中死代码 `out14` 赋值 | 低 |
| N6 | 测试全局 patch `Path.read_text` 的隔离性 | 低 |

---

## 11. Phase 3B / L3-C — I14 规则冻结记录

| 字段 | 内容 |
| --- | --- |
| 阶段 | **L3-C / I14 规则冻结**（本节保留冻结当时记录；其后已编码实现） |
| 检查项 | **I14 — Excerpt text match（Tier C）** |
| 规则权威 | `skills/context-validator/references/validation-rules.md` § I14（Frozen Semantics） |
| Skill | `skills/context-validator/SKILL.md` — 标明规则已冻结且 **已自动化**（Phase 3B-C / `check_i14`） |
| 前序 | 只读规则审计完成；用户确认完整 Frozen Semantics |
| 实现 | **已实现**（`_integrity.check_i14`；`L3_C_excerpts`；I14 已从 `L3_DEFERRED_IDS` 移除） |
| 冻结结论 | **I14 规则正式冻结**；冻结当时不得解读为已实现——**随后已实现**（见文首状态与 Batch C 进度） |

### 11.1 冻结摘要

- **Scope：** 仅 `line_range` 的 `evidence[].locator.excerpt`；非 line_range **无** finder、不建可信窗口。  
- **窗口：** 与 I12 一致 — `read_text(utf-8)` → `splitlines()` → `"\n".join(lines[start-1:end])`。  
- **匹配：** excerpt 换行规范化后，非空行（`strip()==""` 判空）未 strip 字面 `in` 窗口；不要求顺序/连续。  
- **PASS / FAIL / NOT_CHECKED：** 见正式规则；空 excerpt → PASS；汇总 **FAIL > NOT_CHECKED > PASS**；**不用** WARNING / 不新增 NEEDS_HUMAN。  
- **门控：** I11 / I10 / I12 失败 / `readable:false` / 读或 UTF-8 失败 → 适用项 NOT_CHECKED。  
- **语义边界：** I14 PASS ≠ 语义充分 / claim 支撑 / L4。

### 11.2 本冻结任务关闭的 Open Questions

| ID | 冻结结果 |
| --- | --- |
| L3-RQ3 | **不做** Unicode NFC/NFD |
| L3-RQ4 | 空 excerpt → **PASS**；**不**使用 WARNING |
| 适用类型 | **仅** `line_range` |
| 窗口算法 | `splitlines` + `lines[start-1:end]` |
| 匹配谓词 | 每条非空行独立字面包含 |
| 空白 | `strip` 仅判空；匹配不 strip |
| I12 FAIL | 对应 I14 适用项 **NOT_CHECKED** |
| `readable:false` | **NOT_CHECKED** |
| 汇总 | **FAIL > NOT_CHECKED > PASS** |

### 11.3 明确未做 / 后续进度

- **冻结当时：** **未**修改 Python / 测试 / Schema / Exporter / generated-output / input。  
- **当前进度：** I14 **已实现**；**I20 规则已冻结且已实现**（`check_i20`；`L3_DEFERRED_IDS` 已空）；未开始 Importer。  
- **未**处理 B3/B4 历史非阻断债 N1–N6。  
- **历史下一步（冻结当时建议，现已完成）：** I14 测试设计 → 编码实现。
