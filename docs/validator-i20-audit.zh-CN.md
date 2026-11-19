# context-validator — I20 规则审查（只读）

> **历史状态说明（supersession）**  
> 本文记录的是 **I20 规则冻结前** 的历史审查过程与当时结论，**不是**现行规范。  
> 文中尚未关闭的 **Q3**、旧 **FAIL/WARNING** 可选语义、薄定义原文引用、以及「不具备冻结/实现条件」等判断，均反映**当时**工作区快照，**不代表当前规则**。  
> **当前生效规则**以 [`skills/context-validator/references/validation-rules.md`](../skills/context-validator/references/validation-rules.md) **§I20** 为准（mismatch=FAIL；仅 `alg=="sha256"` 且 `of=="package_copy"`，无默认；`package_path` raw bytes；零适用→NOT_CHECKED）。  
> 正文为历史证据保留，**未**改写当时结论。

**文档类型：** 规则审计（历史快照；原标注：非实现、非冻结、非测试设计）  
**协议版本：** CBHF 0.1.0  
**日期：** 2026-11-19  
**阶段：** I14 代码审查完成后；进入 I20 **规则审查**（本文件）  
**硬约束：** 不发明协议字段；不重新定义已冻结的 I12/I13/I14；不将 deferred stub 当作实现；不自行裁决 Open Question Q3  

---

## 1. I20 权威规则原文及位置

### 1.1 首要权威（检查语义）

文件：`skills/context-validator/references/validation-rules.md`

**能力表中的自动化状态（L343 节之前的能力注）：**

| 位置 | 原文要点 |
| --- | --- |
| L10–L25 | Phase 3B-C1 能力注：`L3-C I20` → **Not** implemented — report `NOT_CHECKED` |
| L23–L24 | 同表将 I14 标为已冻结且已自动化；I20 明确未实现 |

**I20 检查条目全文（权威检查语义，无增删）：**

```343:348:skills/context-validator/references/validation-rules.md
### I20 — Checksum (optional)

| Logic | If checksum.value present, recompute package copy hash when possible |
| PASS | Match |
| FAIL/WARNING | Mismatch (resolve Open Question Q3; recommend FAIL when value present) |
| NOT_CHECKED | No checksum or cannot hash |
```

**Open Question 记录（同文件，未关闭）：**

```362:362:skills/context-validator/references/validation-rules.md
- Q3 checksum mismatch severity  
```

`validation-rules.md` 文首声明权威来源（L3）：

> Authority: `docs/context-validator-design.zh-CN.md` + `spec/cbhf/v0.1.0/*.schema.json` + exporter references.  
> **Do not invent protocol fields.**

### 1.2 设计文档中的对应条目（支撑，非更细冻结表）

文件：`docs/context-validator-design.zh-CN.md`

| 位置 | 内容 |
| --- | --- |
| L188 | I20 \| checksum（若存在）\| — \| 可选：重算 package_copy 哈希；不匹配 → `warn`/`fail`（策略见 Q3） |
| L334 | Q3：checksum 不匹配严重级别？→ **建议**「有 checksum 则 `fail`；无则 `not_checked`」（**建议，非已关闭裁决**） |

### 1.3 Schema（字段形状，非 I20 PASS/FAIL 逻辑）

文件：`spec/cbhf/v0.1.0/source.schema.json` L60–L68：

- `checksum`：可选 object；`additionalProperties: false`
- 属性：`alg`（string）、`value`（string \| null）、`of`（string）
- **无**枚举约束 `alg` / `of`；**无**要求 `value` 非 null

### 1.4 Exporter 格式说明（字段意图）

文件：`skills/context-exporter/references/cbhf-format.md`

| 位置 | 内容 |
| --- | --- |
| L325 | `checksum` 可选；Prefer hashing the **package copy**；set `of: package_copy` |
| L283–L307 | 示例中常见 `alg: sha256`、`value: null`、`of: package_copy` |

### 1.5 实施计划中的扩展映射（**非** validation-rules 冻结正文）

文件：`docs/validator-l3-implementation-plan.zh-CN.md`（映射/建议）：

| 位置 | 建议性内容（审计记录，不得当作已冻结规则） |
| --- | --- |
| L65 | 若 `value` 非 null：按 `alg`/`of` 重算 package_copy；匹配 PASS；建议 FAIL（Q3）；无 checksum / value null / 未知 alg / `of`≠package_copy → NOT_CHECKED |
| L95 | `source checksum 字段 ──► I20` |
| L307 | value 匹配 PASS；无 checksum NOT_CHECKED；不匹配 FAIL（Q3 推荐）；未知 alg NOT_CHECKED |
| L335 | Q3：有 value → FAIL；无 → NOT_CHECKED |
| L343 | L3-RQ6：`checksum.of` 非 `package_copy` → NOT_CHECKED |
| L357 | 仅实现 sha256；其余 NOT_CHECKED |

**审计结论：** 可写入报告的**已成文检查语义**仅 `validation-rules.md` L343–348 + Q3 未关闭。计划文档中的 alg/`of`/汇总细节**尚未**写入 `validation-rules.md` 冻结表，**不得**在本阶段当作已定规则实现。

---

## 2. I20 职责解释

| 问题 | 基于权威原文的回答 |
| --- | --- |
| 属于哪一层？ | L3 Integrity；能力表归类为 **L3-C I20**（`validation-rules.md` L24）。设计表 L188 的 Tier 列为 `—`（未标 A/B/C）。 |
| 要解决什么问题？ | 在 **checksum.value 存在** 时，尽可能对 **package copy** 重算哈希并与声明值比较，以发现包内副本与声明不一致。 |
| 检查对象？ | `source-index` 中各 source 的可选 `checksum` 对象（Schema：`alg` / `value` / `of`），以及为重算所需的 **package copy** 文件内容（Exporter：优先 `package_path` 所指包内副本）。 |
| 适用条件？ | 「If checksum.value present」且「when possible」重算（L345）。无 value / 无法哈希 → 不适用完整匹配判定。 |
| 排除 / 非职责？ | **不**判断 excerpt 匹配（I14）；**不**判断 line_range / 其他 locator（I12/I13）；**不**做语义充分性（L4）；**不**替代 I10/I11 对 evidence.locator.path 的存在性/逃逸检查（对象不同）。权威条文**未**要求 I20 验证 `user_path` 原文件。 |

---

## 3. 输入与输出

### 3.1 输入（从权威 + Schema/Exporter 可确定的最小集）

| 输入 | 来源 | 说明 |
| --- | --- | --- |
| 已加载的 `source/source-index.json` | L1/L2 + 索引 | I20 逻辑依赖 source 上的 `checksum` |
| `checksum.value` | Schema | present（非 null 字符串）才进入「重算并比较」路径 |
| `checksum.alg` / `checksum.of` | Schema | 形状存在；**validation-rules 未规定**支持哪些 `alg`、`of` 取值 |
| package copy 字节 | 文件系统 | 「recompute package copy hash」；Exporter 指向包内副本 |

### 3.2 输出

| 输出 | 状态 |
| --- | --- |
| 检查结果码 | 权威允许：`PASS`；不匹配时 `FAIL` **或** `WARNING`（取决于未关闭的 Q3）；`NOT_CHECKED`（无 checksum 或 cannot hash） |
| 报告中的 check 行 | 当前实现：deferred stub（见 §6），`id=I20`，`result=NOT_CHECKED` |
| reason code | **validation-rules.md 未定义** I20 专用 reason code |

---

## 4. PASS / FAIL / NOT_CHECKED 判定表

严格按 `validation-rules.md` L345–348（**不**把计划文档升格为已冻结）：

| 条件（权威措辞） | 结果 |
| --- | --- |
| 重算可能，且与 `checksum.value` **Match** | **PASS** |
| `checksum.value` present，重算可能，且 **Mismatch** | **FAIL 或 WARNING**（Q3 **未解决**；原文 recommend FAIL when value present） |
| No checksum **or** cannot hash | **NOT_CHECKED** |

**权威未写清、因而本审计不得填入「已定」单元格的项：**

| 缺口 | 说明 |
| --- | --- |
| 「No checksum」精确含义 | 缺 `checksum` 对象？`value: null`？空字符串？ |
| 「cannot hash」精确含义 | 未知 `alg`？`of`≠package_copy？文件缺失？路径不安全？读失败？ |
| 多 source 汇总 | 一条 FAIL、其余 PASS 时整体结果？是否 FAIL > NOT_CHECKED > PASS？ |
| 空 source 数组 | PASS 还是 NOT_CHECKED？ |
| source-index 未加载 | 是否 NOT_CHECKED？（与其他 I\* 一致的合理推断，但 **I20 条目未写**） |

---

## 5. 与 I10～I19 的依赖关系

| 规则 | 与 I20 关系 | 说明 |
| --- | --- | --- |
| I10 | **无直接权威依赖** | I10 针对 **evidence.locator.path** 存在性；I20 针对 **source.checksum / package copy**。计划依赖图写 `source checksum → I20`，未写 I10→I20。 |
| I11 | **无直接权威依赖** | I11 管 evidence locator 路径安全。若实现时读取 `package_path`，**安全上应**防逃逸，但 validation-rules **未**写「I20 必须消费 I11 map」。不得把 I11 门控语义强加为已冻结 I20 条款。 |
| I12 | **无直接关系** | line_range 边界；对象不同。 |
| I13 | **无直接关系** | 非 line_range 定位；对象不同。 |
| I14 | **无直接关系** | excerpt 窗口匹配；对象不同。同属 L3-C 批次叙述，非数据依赖。 |
| I15–I19 | **无直接关系** | verified / readable:false / content_transformed / validation 诚实性 / orphan evidence — 权威 I20 条未引用。 |
| I16 | **无强制依赖** | `readable` 与 checksum 正交；opaque 源仍可有 package_copy 哈希（Exporter 示例常见）。 |

**结论：** 不得为通过审查而虚构 I10/I11/I12/I14→I20 的冻结门控链。实现设计阶段再讨论「读 `package_path` 前是否复用 I11 同类安全策略」——那是实现安全要求，不是当前权威条文。

---

## 6. 当前实现状态

| 项 | 状态 | 证据 |
| --- | --- | --- |
| `check_i20` 函数 | **未实现** | `_integrity.py` 仅有 `check_i01`…`check_i19`（无 `check_i20`） |
| Deferred 登记 | **是** | `_integrity.py` L43–45：`L3_DEFERRED_IDS = {"I20": "Phase 3B: checksum verification not implemented (Q3)"}` |
| L3 执行链注册 | **仅 stub** | `run_l3_batch_a` L1601–1607：对 deferred 追加 `CheckOut(..., NOT_CHECKED, reason)`；名称 `"Checksum (optional)"` |
| 真实哈希逻辑 | **无** | 全 `_integrity.py` 无 `hashlib` / checksum 比较 |
| `validate_package.py` | 声明 I20 仍 NOT_CHECKED | 文件头 L6；limitations L384–385；phase `3B-C1` |
| SKILL.md | 诚实声明未自动化 | L63：L3-C I20 → No — not started → NOT_CHECKED |
| 报告字段预留 | **仅标准 check 行** | stub 产出 I20 + NOT_CHECKED + deferred message；**无**专用 Schema 字段、**无**官方 reason code 表 |
| 重复/旧逻辑 | **未发现** Validator 侧 checksum 校验实现 | Exporter/`_prepare_export_sources.py` 可**生成** checksum，≠ Validator I20 |

**分类：** **未实现**（仅 deferred NOT_CHECKED 占位）。**非**部分实现。

---

## 7. 现有测试覆盖情况

| 覆盖类型 | 有无 | 说明 |
| --- | --- | --- |
| I20 PASS（值匹配） | **无** | — |
| I20 FAIL/WARNING（不匹配） | **无** | — |
| I20 NOT_CHECKED（无 checksum / cannot hash） | **仅间接** | 最小包通常无 value → 期望整包流程中 I20 仍为 NOT_CHECKED（因未实现，恒为 NC） |
| Deferred 占位断言 | **有** | `run_l3_tests.py`：`L3_DEFERRED = ["I20"]`；generated/empty/minimal 循环；L507/515 layer mix；L625/638 与 I19 WARNING；I14-T099 L2255 |
| L1/L2 | **有占位** | `run_l1_l2_tests.py` L258：`deferred = ["I20"]` 期望 NOT_CHECKED |
| 对照 generated-output 真实 sha256 | **无 I20 自动化断言** | 样例含非 null sha256（`examples/.../source-index.json` L16–76），但 Validator **不**验证它们 |

**结论：** 现有测试只证明「I20 在报告中存在且为 NOT_CHECKED（未实现）」，**不**覆盖 checksum 语义。

---

## 8. 未覆盖边界（规则层 + 测试层）

规则层未冻结 / 未写清：

1. Q3：mismatch → FAIL 还是 WARNING  
2. `value: null` vs 省略 `checksum` vs 空字符串  
3. 支持的 `alg` 集合（计划建议仅 sha256 — **未写入** validation-rules）  
4. `of` ≠ `package_copy`（计划 L3-RQ6 — **未写入** validation-rules）  
5. 哈希输入：原始字节？文本规范化？与 Exporter 生成方式是否必须一致  
6. `package_path` 缺失/逃逸/不可读时的精确结果码  
7. 多 source 汇总优先级  
8. source-index 未加载时的结果  
9. I20 专用 reason code  
10. 与只读/隐私：哈希是否允许读取二进制 package copy；报告是否禁止粘贴完整 hash 外的路径隐私问题（权威未专写）

测试层：上述任一项均无语义级用例（因规则未冻 + 代码未实现）。

---

## 9. 潜在风险

| 风险 | 说明 |
| --- | --- |
| 文件读取 | 实现后需读 package copy；若路径未做逃逸校验，有包外读风险（类似 I11 关切，但权威未绑 I11） |
| 路径安全 | `package_path` 与 evidence `locator.path` 是不同字段；不可假设 I11 已覆盖 |
| 状态误判 | 在 Q3 未关闭时实现「一律 FAIL」或「一律 WARNING」均属**自行裁决** |
| 空/异常输入 | value null、未知 alg、缺文件 — 权威仅笼统「cannot hash → NOT_CHECKED」 |
| 重复检查 | 与 I10/I14 **无**功能重叠；勿把 locator 文件存在性并进 I20 |
| 只读 / 隐私 | 不得写包；报告勿泄漏 host 绝对路径（与现有 L3 惯例一致，I20 条未特书） |
| 回归 | generated-output 含真实 sha256：一旦实现且算法/字节定义与 Exporter 不一致 → 假 FAIL；最小包无 checksum → 应保持 NOT_CHECKED |
| 职责膨胀 | 禁止把 I20 做成「全文完整性 + readable + excerpt」综合检查 |

---

## 10. 是否具备进入测试设计阶段的条件

### 判定：**否（尚不具备完整进入 I20 测试设计的条件）**

理由：

1. 权威条目（`validation-rules.md` L343–348）过薄，关键判定依赖 **未关闭的 Q3**（FAIL vs WARNING）。  
2. 「cannot hash / No checksum」边界、`alg`/`of`、多对象汇总、未加载 source **均未**在 validation-rules 中冻结。  
3. 实施计划中的细化（sha256-only、`of`≠package_copy→NC 等）**尚未**吸收进权威冻结表；若测试设计直接采用，等于**推测规则原文**。  
4. 用户约束：规则不完整或有歧义时 **列出问题并停止，不要自行补充定义**。

### 进入测试设计前必须先冻结（最低清单）

由人类确认并写回 `validation-rules.md`（本审计**不**修改该文件）至少包括：

1. **关闭或显式冻结 Q3**（mismatch → FAIL 或 WARNING；0.1.0 采用哪一个）  
2. `checksum` / `value` 缺省与 null 的 NOT_CHECKED 条件  
3. 支持的 `alg` 与未知 alg 行为  
4. `of` 取值与非 `package_copy` 行为  
5. 哈希对象定义（对哪个路径、何种字节）  
6. 多 source 汇总规则  
7. source 未加载行为  
8. （可选）reason code 列表  

**在上述冻结完成之前：** 允许继续只读讨论；**不允许**开始 I20 实现；**不允许**把计划文档建议当作已冻结语义编写正式测试矩阵并宣称验收权威。

---

## 11. 本审计阅读文件清单

| 文件 | 用途 |
| --- | --- |
| `skills/context-validator/references/validation-rules.md` | I20 权威条文、能力表、Q3 |
| `skills/context-validator/scripts/_integrity.py` | deferred / stub / 无 check_i20 |
| `skills/context-validator/scripts/validate_package.py` | phase / limitations |
| `skills/context-validator/SKILL.md` | 能力诚实表 |
| `tests/validator/v0.1.0/run_l3_tests.py` | I20 deferred 断言 |
| `tests/validator/v0.1.0/run_l1_l2_tests.py` | deferred 列表 |
| `spec/cbhf/v0.1.0/source.schema.json` | checksum 字段形状 |
| `skills/context-exporter/references/cbhf-format.md` | package_copy 意图 |
| `docs/context-validator-design.zh-CN.md` | I20 设计行 + Q3 建议 |
| `docs/validator-l3-implementation-plan.zh-CN.md` | 映射/建议（非冻结） |
| `examples/technical-proposal/generated-output/source/source-index.json` | 样例含非 null sha256 |
| `tests/schema/v0.1.0/_prepare_export_sources.py` | Exporter 侧生成 hash（非 Validator） |

**未修改**上述任一已有文件；本审计**仅新增**本报告。

---

## 12. 停止点

- **不实现 I20**  
- **不修改** `_integrity.py` / `validation-rules.md` / Schema / Exporter / generated-output / 现有测试  
- **不重新打开** I12 / I13 / I14  
- **等待：** 人类对 §10 冻结清单的确认，或明确授权「仅基于 validation-rules 现有薄定义做有限测试设计（并标注 Q3 未决）」——当前默认解释为 **停止于规则审查**  
