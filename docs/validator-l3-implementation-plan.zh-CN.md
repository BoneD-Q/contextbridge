# context-validator — Phase 3A：L3 Integrity 实施前审计

**文档类型：** 实施前审计 / 测试设计  
**协议版本：** CBHF 0.1.0（不修改）  
**日期：** 2026-11-19  
**状态：** 审计稿 — **本阶段不实现代码**  
**依据：** `validation-rules.md` I01–I20、`docs/context-validator-design.zh-CN.md` §5.3、`scripts/validate_package.py`（Phase 2）、`examples/technical-proposal/generated-output/`、`tests/semantic-review/v0.1.0/`

---

## 0. 审计结论摘要

| 结论 | 说明 |
| --- | --- |
| 编号 | **不重新定义** I01–I20；本文件只做映射与实施设计 |
| 可完全自动化 | I01–I12、I14–I16、I18–I19；I17 为 Schema 覆盖项的 Integrity 记账；I20 在有 `checksum.value` 时可自动化 |
| 需降级 / 部分自动化 | **I13**（section/page 等“找得到”深度，Open Question Q2） |
| 不得当语义结论 | **I14 PASS ≠ 语义充分**；双向链接 PASS ≠ Evidence 真正支持命题（L4 H01） |
| 协议歧义（不擅自裁决） | Q2（I13）、Q3（I20）、I07 中无类型 `related_ids` 的解析范围、I11 Windows 大小写、checksum.`of` 语义 |
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
| I12 | line_range 边界 | B | evidence + 源文件文本 | `locator_type=line_range`：1-based；end≥start；≤行数 | 边界合法 | 越界/非法数字 | — | 非 line_range → 本检查对该条不适用（整体：若无 line_range 则 PASS 空集；若文件不可读 → NOT_CHECKED） | start/end null：Schema 允许；建议 null → FAIL 或 NOT_CHECKED（见 §5） |
| I13 | 其他 locator 类型 | B | evidence | 类型形状由 Schema；**找得到**则宿主验证 | 宿主确认可定位 | 明确找不到（若实现查找） | 无法验证找得到 | 默认推荐：找得到性 **NOT_CHECKED**（Q2） | **Q2** |
| I14 | excerpt 文本匹配 | C | evidence + 定位窗口文本 | 规范化换行后，excerpt **每一非空行** ⊆ 窗口（强于 smoke 首行） | 全部匹配 | 任一行缺失 | — | 无文本窗口 / 不可读 / 非 line_range 且无窗口策略 | **≠ 语义充分（L4）** |
| I15 | verified ⇒ evidence_ids 非空 | A | 知识对象 | status=`verified` ⇒ evidence_ids 非空 | 满足 | 空/缺失 | — | 知识未加载 | Schema 已约束；Integrity 再确认 |
| I16 | readable:false | A/B | source-index + evidence + 知识 | 对 `readable:false` 源：不得有文本摘录式 evidence；不得支撑 `verified` | 无违规依赖 | 有摘录或 verified 依赖 | — | 未加载 | 空 excerpt + readable:false 仍建议 FAIL |
| I17 | content_transformed 形状 | Schema | source-index | `true\|false\|null` 已由 S03 保证 | 若 S03 PASS → 本项 PASS（记账） | — | — | S03 未跑 → NOT_CHECKED | 不重复发明枚举 |
| I18 | manifest.validation 诚实 | — | manifest + 是否存在 validation 报告文件 | `present=true` 但无报告 → FAIL；`present=false` 且无报告 → **正常** | present 与文件系统一致 | present=true 无报告 | present=false 无报告可记 NOTE 或 PASS（非 WARNING 强制）；设计写 WARNING 可选——**推荐 PASS+message** 避免噪声 | manifest 未加载 | Phase 2 默认不写 validation/ |
| I19 | 孤儿 evidence | A | evidence | `supports` 为空 | 无空 supports | — | 存在空 supports | evidence 未加载 | 协议允许未指派 |
| I20 | checksum（可选） | — | source.checksum + 包内文件 | 若 `value` 非 null：按 `alg`/`of` 重算 package_copy | 匹配 | **建议 FAIL**（Q3 推荐） | 若策略改为 warn | 无 checksum / value null / 未知 alg / `of`≠package_copy | **Q3**；generated-output 含 sha256 |

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
**I13 策略（本审计推荐，不改协议）：** 对非 `line_range`：**类型已由 Schema 校验则不重复 FAIL**；找得到性一律 `NOT_CHECKED`（记录 Q2），除非后续明确实现查找器。

### Batch C — 摘录可匹配

**范围：** I14（+ I20 可选同批或紧随）

**价值：** 强于 smoke 首行；对齐 `_check_excerpts.py` 与人工审查中的“可定位”。  
**风险：** 中（换行规范化、Unicode）。  
**硬规则：** I14 PASS **不得**写入语义充分或 H01 PASS。

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

#### I12 line_range

| 样本 | 预期 |
| --- | --- |
| start=1,end=1 单行文件 | PASS |
| end > 行数 | FAIL |
| start=0 或 end\<start | FAIL |
| start/end null | FAIL 或 NOT_CHECKED（实施前冻结为：**FAIL**「line_range 缺起止」） |
| 仅 section 类型证据 | 本检查对该条跳过；无 line_range 时 I12 PASS |

#### I13 其他类型

| 样本 | 预期 |
| --- | --- |
| 仅 line_range 包 | PASS（无可查项） |
| 含 section、未实现查找 | **NOT_CHECKED**（Q2）或 WARNING |
| 禁止因找不到 heading 自动语义 FAIL | — |

#### I14 excerpt

| 样本 | 预期 | 说明 |
| --- | --- | --- |
| generated-output 22 条（对齐 `_check_excerpts.py`） | PASS | |
| 多行 excerpt 全在窗口 | PASS | |
| 缺一行 | FAIL | |
| Unicode（中文/emoji） | PASS/FAIL 按字面 | 不 NFC 强制除非文档规定 |
| CRLF 文件 + LF excerpt 行 | PASS | **规范化：统一 `\n`，匹配前不 strip 行内空白**（与现 `_check_excerpts`：`ln.strip()` 仅用于跳过空行，匹配用原始 `ln not in span`——**实施须固定一种**；推荐与现脚本一致：非空行（`strip()` 判定）用 **未 strip 的行文本** 做 `in`） |
| 空 excerpt | PASS（无非空行） | 是否另 WARNING 留给 Open Q；0.1.0 不新增 |
| 窗口文件空 | 非空 excerpt → FAIL | |
| 非 line_range 无窗口 | NOT_CHECKED | |
| **PASS 后** | 报告 limitations 声明 ≠ 语义充分 | |

#### I15 verified

| 样本 | 预期 |
| --- | --- |
| verified + 非空 evidence_ids | PASS |
| verified + []（若绕过 Schema 的手工坏包） | FAIL |

#### I16 readable:false

| 样本 | 预期 |
| --- | --- |
| readable:true + excerpt | PASS |
| readable:false + 非空 excerpt evidence | FAIL |
| verified 知识依赖上述 evidence | FAIL |
| readable:false 无 evidence 引用 | PASS |

#### I17 / I18 / I19 / I20

| ID | 正常 | 错误 / 边界 |
| --- | --- | --- |
| I17 | S03 PASS → I17 PASS | S03 NOT_CHECKED → I17 NOT_CHECKED |
| I18 | present=false 无 validation/ → PASS | present=true 无报告 → FAIL；有报告文件（未来）→ PASS |
| I19 | 无空 supports → PASS | 空 supports → WARNING（不升级 FAIL） |
| I20 | value 匹配 → PASS；无 checksum → NOT_CHECKED | value 不匹配 → FAIL（Q3 推荐）；未知 alg → NOT_CHECKED |

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
| Q2 | section/page_range「找得到」深度 | I13 | 默认 NOT_CHECKED；勿假装已验证 |
| Q3 | checksum 不匹配严重级别 | I20 | 有 value → FAIL；无 → NOT_CHECKED |
| Q1 | 额外文件 warn/fail | 非 I\*（P06） | 保持 WARNING |
| Q4/Q5 | 是否写 validation/ | I18 相关 | Phase 3 仍默认不写包 |
| L3-RQ1 | 无类型 `related_ids` 解析范围 | I07 | 全已知 id 集合 |
| L3-RQ2 | line_range start/end null | I12 | 建议 FAIL |
| L3-RQ3 | I14 是否 Unicode 规范化 | I14 | 建议不做 NFC；按码点字面 |
| L3-RQ4 | I14 空 excerpt | I14 | PASS；不新增 WARNING |
| L3-RQ5 | I18 present=false 是否 WARNING | I18 | 建议 PASS + 说明，避免与 P06 噪声叠加 |
| L3-RQ6 | `checksum.of` 非 `package_copy` | I20 | NOT_CHECKED |
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
3. **Batch B：** I11 → I10 → I12；I16；I13 占位 NOT_CHECKED。  
4. **Batch C：** I14（规范化策略写死并单测）；I20（sha256 + package_copy）。  
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

## 9. 本阶段交付清单

- [x] I01–I20 映射与依赖  
- [x] A/B/C 批次  
- [x] 测试矩阵与边界（Unicode/CRLF/symlink/空集合等）  
- [x] Open Questions  
- [x] 风险与实现顺序  
- [x] 预计文件变更  
- [ ] **不**实现代码（遵守）  

**下一步：** 等待审查通过后，再启动 Phase 3B（建议先 Batch A）。
