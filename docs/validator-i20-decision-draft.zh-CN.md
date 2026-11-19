# context-validator — I20 规则决策准备（只读草案）

> **历史状态说明（supersession）**  
> 本文记录的是 **I20 规则冻结前** 的决策准备与待拍板清单，**不是**现行规范。  
> 文中开放的 **Q3**、旧 WARNING 讨论、`of` 缺省 vs 精确取值选项、以及「尚不具备冻结条件」等判断，均反映**当时**草案，**不代表当前规则**。  
> **当前生效规则**以 [`skills/context-validator/references/validation-rules.md`](../skills/context-validator/references/validation-rules.md) **§I20** 为准（mismatch=FAIL；仅精确 `alg=="sha256"` 与 `of=="package_copy"`，**无** alg/of 默认；对 `sources[].package_path` raw bytes SHA-256；零适用→NOT_CHECKED；rollup FAIL>NOT_CHECKED>PASS）。  
> 正文为历史决策轨迹保留，**未**把当时讨论改写成冻结结论。

**文档类型：** 决策准备（历史快照；原标注：非冻结、非实现、非测试设计）  
**日期：** 2026-11-19  
**前置：** `docs/validator-i20-audit.zh-CN.md`  
**硬约束：** 不修改任何权威文件；不实现 I20；不擅自关闭 Q3；工程建议与已有规范严格分栏  

---

## 0. 本轮核对过的依据

| # | 材料 | 路径 / 符号 | 核对要点 |
| --- | --- | --- | --- |
| 1 | I20 规则 | `skills/context-validator/references/validation-rules.md` **L343–348**；Q3 于 **L362** | 薄定义；mismatch 的 FAIL/WARNING 未决 |
| 2 | Schema | `spec/cbhf/v0.1.0/source.schema.json` **L60–L68**（`checksum`）；`package_path` **L22/L36** 必填 | 形状，无 alg/of 枚举 |
| 3 | 格式约定 | `skills/context-exporter/references/cbhf-format.md` **L325**、示例 **L283–L307**、开放问题 **L834** | Prefer package copy；`of: package_copy`；checksum **optional** |
| 4 | Exporter Skill | `skills/context-exporter/SKILL.md`（指令型，**无** checksum 计算脚本） | 要求建 `source/original/` 与 source-index；未规定哈希字节算法 |
| 5 | 实际生成样例的脚本 | `tests/schema/v0.1.0/_prepare_export_sources.py` **`main()` L28–93** | **仓库中唯一可执行的 checksum 生成逻辑**（样例再生，非 Skill 运行时） |
| 6 | 路径安全 | `_integrity.py`：`path_form_forbidden` **L154**；`classify_locator_path_safety` **L193**；`locator_path_is_file` **L219**；`check_i11` **L715**（仅 evidence.locator.path） | 可复用函数；I11 **不**扫描 `package_path` |
| 7 | 包指纹（非 I20） | `validate_package.py` `fingerprint_package` **L242–256** | 对包内文件 **raw bytes** 做 sha256（只读断言用） |
| 8 | 样例数据 | `examples/technical-proposal/generated-output/source/source-index.json` | 四条 source 均含 `alg=sha256`、非 null `value`、`of=package_copy` |
| 9 | 审计未决 | `docs/validator-i20-audit.zh-CN.md` **§8 / §10** | Q3、alg/of、哈希对象、汇总、路径结果码等 |

**实证（本轮只读核验，非规范）：** 对 `generated-output` 四条 `package_path`，`hashlib.sha256(Path.read_bytes()).hexdigest()` 与 `checksum.value` **全部 match**。说明当前样例声明值与**磁盘文件原始字节**一致（与 `_prepare_export_sources.py` 写入后再声明的方式相容）。

---

## 1. Q1 — checksum 数据结构

### Schema 已规定（`source.schema.json` L60–L68）

| 项 | Schema |
| --- | --- |
| `checksum` 对象本身 | **可选**（不在 SourceEntry `required` 列表 L19–L28） |
| `checksum.value` | `["string","null"]` → **允许 null** |
| `checksum.alg` | `string`；**非** required |
| `checksum.of` | `string`；**非** required |
| 枚举 | **无**（`alg`/`of` 任意 string） |
| 多条 checksum | **不允许数组**：每个 SourceEntry 最多 **一个** `checksum` object（`additionalProperties: false`） |
| 多 source | `sources` 数组中每条可各自有一个 `checksum` |

### validation-rules / 格式文档

| 项 | 内容 | 层级 |
| --- | --- | --- |
| I20 Logic | 「If checksum.value present…」（`validation-rules.md` L345） | 检查语义：暗示以 **value present** 为门槛 |
| Exporter | checksum **no**（可选）；Prefer hash package copy；`of: package_copy`（`cbhf-format.md` L325） | 格式意图，非 Validator PASS/FAIL 表 |
| 未知算法 | **未**在 Schema / validation-rules 规定 | 未决 |

### Exporter / Validator 当前行为

| 方 | 行为 |
| --- | --- |
| `_prepare_export_sources.py` L77–81 | 总是写入 `alg: "sha256"`、`value: <hex>`、`of: "package_copy"` |
| `cbhf-format.md` 示例 L283–L307 | 常写 `value: null` |
| Validator I20 | **未实现**；deferred NOT_CHECKED（`_integrity.py` L43–45、L1601–1607） |

### 工程建议（非规范）

- 将「value present」操作性定义为：`checksum` 存在且 `value` 为 **非 null 字符串**（空字符串是否算 present → 需拍板）。  
- 未知 `alg` → **NOT_CHECKED**（cannot hash），与计划文档建议一致，但须写入 validation-rules 才可冻结。

---

## 2. Q2 — 哈希对象是哪个文件？

| 来源 | 说什么 |
| --- | --- |
| validation-rules L345 | 「recompute **package copy** hash」 |
| cbhf-format L325 | Prefer hashing the **package copy**；`of: package_copy` |
| cbhf-format L76 | `source/original/` = Package copy |
| `_prepare_export_sources.py` | 写入 `OUT/source/original/<name>`（L55–57）；`package_path` = `source/original/{name}`（L65）；hash 基于**即将写入/已规范化的 package copy 文本**（L49–80），**不是** `input/` 用户原文件 |
| Exporter Skill | 包内副本在 `source/original/`；locators 针对 package copy（SKILL / evidence-rules） |

**已验证行为结论：** 现有可执行生成逻辑与样例均指向 **`package_path` 所指的包内副本**（通常 `source/original/...`），**不是** `user_path` 原始文件。

**未在权威检查表写死的点：** I20 是否**必须**用 `sources[].package_path` 定位文件（虽高度一致，但 validation-rules 只写 “package copy”，未写字段名）。

---

## 3. Q3 — 哈希输入字节（Exporter 实际逻辑）

依据：`tests/schema/v0.1.0/_prepare_export_sources.py` `main()`：

| 步骤 | 代码 | 行为 |
| --- | --- | --- |
| 读入 | L46 `src.read_text(encoding="utf-8")` | **文本 UTF-8**，非 `read_bytes` |
| 脱敏 | L48–50 正则替换 | **复制前**对文本脱敏 |
| 换行 | L52–54 CRLF/CR→LF；保证末尾 `\n` | **有**换行规范化 |
| 编码 | L57 `write_text(..., encoding="utf-8", newline="\n")` | 写出 UTF-8 LF |
| 哈希时机 | L77–80：对内存 `text.encode("utf-8")` 做 sha256 | **在写出 package copy 的同一 `text` 上计算**（复制/规范化**之后**） |
| 是否哈希用户原文件 | 否 | `INP` 仅作读入源；hash 不针对未脱敏原文 |

**Validator 能否复现：**

- 对**当前 generated-output**：用磁盘 **raw bytes**（`read_bytes` / 与 `fingerprint_package` 同类）重算 sha256 → **与声明 value 一致**（本轮实证）。  
- 因此：在「文件即 `_prepare_export_sources` 写出结果」的前提下，Validator 对 `package_path` 做 **原始字节 sha256** 即可复现。  
- **不能**假设所有未来 Exporter 宿主都走同一脚本；Skill 未规定统一哈希字节语义。若其他宿主先写文件再哈希、或哈希未规范化文本，可能漂移。

**工程建议（非规范）：** I20 冻结为「对 `package_path` 文件 **原始字节** 做 `alg` 摘要」；与声明比较时用小写 hex（样例为小写）。不把「先 decode UTF-8 再 encode」写成规范，除非与「磁盘 bytes」证明永久等价。

---

## 4. Q4 — 多 source 汇总（场景分析，不擅自定规则）

权威仅给出**单项** Match / Mismatch / No-checksum-or-cannot-hash 语义，**无** package 级汇总公式。

| 场景 | 单项（按权威措辞可推断的方向） | Package 总体 | 状态 |
| --- | --- | --- | --- |
| 全部 value present 且 Match | 各 Match → PASS 方向 | **未规定**是否「全部 PASS 才整体 PASS」 | 未决 |
| 任一条 Mismatch | 该条 FAIL **或** WARNING（Q3） | **未规定**是否整体升级 | 未决；且依赖 Q3 |
| 部分 Match + 部分 cannot hash | Match 与 NOT_CHECKED 并存 | 其他 I\* 常用 FAIL>NC>PASS，**I20 未写** | 未决 |
| 全部 cannot hash / 全部无 checksum | NOT_CHECKED | 可能整体 NOT_CHECKED | 合理但未写 |
| 没有任何 source 带 value | 「No checksum」 | NOT_CHECKED | 与 L348 方向一致；空 sources 未写 |
| 多条 source 指向同一 `package_path` | Schema **不禁止**；每条独立 checksum | 可能重复读同一文件 | 行为未规定；非「多条 checksum 字段」（Schema 每 source 仅一个 object） |

**Validator 当前：** 无汇总实现。  
**工程建议（非规范）：** 对齐其他 L3：`FAIL > NOT_CHECKED > PASS`；仅统计「value present 的适用项」；无适用项 → NOT_CHECKED（与「No checksum」一致），**不要**把「无 checksum」做成 PASS。

---

## 5. Q5 — `package_path` 路径与安全

| 问题 | 证据 | 结论 |
| --- | --- | --- |
| 现成安全解析？ | `path_form_forbidden` L154；`classify_locator_path_safety` L193；`locator_path_is_file` L219 | **有**通用相对路径安全/存在性工具 |
| 能否「复用 I11」？ | `check_i11` L715–788：**仅** `evidence[].locator.path`；docstring 写明 not source.package_path | **不能**直接消费 I11 的 per-evidence map；可**复用同一分类函数**作用于 `package_path`（属实现设计，非现成 I11 依赖） |
| 绝对 / `..` / symlink | `path_form_forbidden` + `resolve` + `relative_to(root)` | 禁止形式 → unsafe；逃逸 symlink → unsafe；部分 OS 错误 → unresolved |
| 不安全是否零读取？ | I11/I12/I14 对 evidence 已实践「unsafe 不读内容」 | I20 **权威未写**；安全上应同样零读取（工程建议） |
| 不存在 / 不可读 / 非文件 | `locator_path_is_file` 要求 `is_file()`；读失败在 I12 为 NC | I20 权威归入笼统「cannot hash → NOT_CHECKED」；是否 FAIL 未写 |

**Exporter 文档：** `package_path` 应为包内安全相对路径（`cbhf-format.md` L317、L99）。

---

## 6. 决策表（未决问题）

图例：**权威**=validation-rules；**Schema**=source.schema；**Fmt**=cbhf-format；**Prep**=`_prepare_export_sources.py`；**Val**=Validator 现状；**建议**=工程建议（非规范）

| 问题 | 当前权威定义 | 现有实现证据 | 未决内容 | 建议选项 | 影响 |
| --- | --- | --- | --- | --- | --- |
| A. value 允许空/null？ | 权威：value **present** 才重算；未定义 null/缺省/空串 | Schema：value 可为 null；Prep：总写非 null hex；Fmt 示例常 null | null / 省略 checksum / `""` 是否均 NOT_CHECKED | null与省略→NC；空串→NC（cannot hash）或不视为 present | 决定适用集大小 |
| B. alg 必填？ | 权威未要求 | Schema：可选 string；Prep：总写 sha256 | 缺 alg 时？ | 缺 alg 或非 sha256 → NC | 与「仅 sha256」绑定 |
| C. of 必填？ | 权威未要求 | Schema：可选；Prep/Fmt：`package_copy` | 缺 of / 非 package_copy？ | 仅 `of==package_copy`（或缺省视为 package_copy）可哈希；否则 NC（对齐计划 L3-RQ6，须升格权威） | 避免哈希 user 原文件 |
| D. 未知算法 | 权威：cannot hash → NC | Val：无实现 | 支持集合 | 0.1.0 仅 `sha256`；其它 NC | 实现范围 |
| E. 多 checksum 字段 | — | Schema：每 source **一个** object | 无 | 沿用 Schema：禁止数组 | 无需改 Schema |
| F. 哈希哪个文件 | 权威：package copy | Prep：`source/original/...`；样例 `package_path`；磁盘 bytes≡value | 是否硬性绑定 `package_path` 字段 | **是**：只哈希 `sources[].package_path` | 实现定位清晰 |
| G. 哈希字节定义 | 权威未写 | Prep：规范化文本后 `encode utf-8`；样例磁盘 bytes 匹配；`fingerprint_package` 用 rb | 规范写成「文件原始字节」还是「UTF-8 文本规范化后再哈希」 | **文件原始字节** sha256 hex（与当前样例一致） | 避免文本层二次规范化 |
| H. 脱敏/换行 | 权威未写 | Prep：先脱敏与换行，再写盘再哈希 | Validator 是否重做脱敏 | **否**；只信盘上 package copy | 与 I14 窗口读盘一致 |
| I. Q3 mismatch 级别 | FAIL **或** WARNING；recommend FAIL | 设计 L334 建议 fail；计划同 | **必须用户拍板** | （不代选）选项：一律 FAIL / 一律 WARNING | 决定整体严重度与回归 |
| J. 多 source 汇总 | 无 | 其它 L3：FAIL>NC>PASS | 是否采用 | 采用 FAIL>NC>PASS；无适用项→整体 NC | 报告层状态 |
| K. 同 path 多 source | 无 | Schema 不禁 | 是否去重读 | 可按 path 缓存摘要但仍逐条比较 value | 性能；结果仍逐条 |
| L. package_path 不安全 | 无 I20 专条 | 有 `classify_locator_path_safety`；I11 不覆盖 | NC vs FAIL；是否零读 | unsafe/unresolved→该条 NC + **零读**；不升级 I11 | 安全 |
| M. 文件缺失/读失败 | cannot hash → NC | I12 同类 NC | 是否对 missing 用独立 reason | NC + reason（missing/read_failed） | 可观测性 |
| N. source 未加载 | 无 | 其它 I\*：NC | 是否 NC | source 未加载→整体 NC | 门控一致 |
| O. reason codes | 无 | — | 列表 | 实现前写入规则（mismatch / unknown_alg / …） | 测试与隐私 |

---

## 7. 可直接沿用的现有规则（无需重开）

1. I20 属于 L3；checksum **可选**（Schema + Fmt #4）。  
2. 有 `value` 且能重算时：Match → **PASS**；无法哈希 / 无 checksum → **NOT_CHECKED**（`validation-rules.md` L345–348）。  
3. 对象语义指向 **package copy**，不是 user 原文件（Fmt + Prep 行为）。  
4. Schema：每 source 至多一个 `checksum` object；`value` 可为 null。  
5. 不发明新协议字段；不把 I20 做成 excerpt/语义检查。  
6. I11 **定义范围**仍仅为 evidence.locator.path（可复用函数，不改 I11 职责）。  
7. Q3 **保持开放直至用户拍板**（不得在本草案中关闭）。

---

## 8. 若要冻结 I20，必须改写进权威规则的内容

写入 `validation-rules.md` §I20（并视需要关闭 Q3），至少：

1. **Q3 裁决**：mismatch → `FAIL` 或 `WARNING`（二选一写死）。  
2. 「value present」操作性定义（null / 省略 / 空串）。  
3. 哈希定位字段：`sources[].package_path`。  
4. 哈希输入：文件**原始字节** + 支持的 `alg`（建议写明仅 `sha256`）+ 未知 alg → NC。  
5. `of`：仅 `package_copy`（或缺省规则）；其它 → NC。  
6. 路径安全：unsafe/unresolved → 该条 NC、零读取（可引用与 I11 相同分类函数，但不声称 I11 已检查 package_path）。  
7. 缺失/读失败 → NC。  
8. 多 source 汇总优先级。  
9. source-index 未加载 → NC。  
10. （建议）reason code 表。

**Schema：** 当前形状已够用；**不必**为冻结而改 Schema，除非要将 `alg`/`of` 枚举硬化进协议（那是协议变更，超出本草案默认建议）。

**Exporter：** Skill 仍无统一哈希实现；若冻结「原始字节」，建议后续在 Exporter 文档注明与 Validator 对齐——**属后续文档工作，本阶段不改**。

---

## 9. 需要用户拍板的最小决策清单

1. **Q3：** checksum mismatch → **FAIL** 还是 **WARNING**？  
2. **适用集：** `value: null` / 省略 `checksum` / `value: ""` 是否一律整项 NOT_CHECKED？  
3. **alg：** 0.1.0 是否仅支持 `sha256`，其余 NOT_CHECKED？  
4. **of：** 是否仅当 `of == "package_copy"`（缺 `of` 视为 package_copy 还是 NC）？  
5. **字节定义：** 是否冻结为「`package_path` 文件原始字节」？  
6. **汇总：** 是否采用 `FAIL > NOT_CHECKED > PASS`？无适用项是否整体 NOT_CHECKED（而非 PASS）？  
7. **安全：** `package_path` unsafe 是否强制零读取且该条 NOT_CHECKED？

---

## 10. 是否具备冻结 I20 规则的条件

### 判定：**否**

原因：Q3 未决；哈希字段/字节/`alg`/`of`/汇总/路径结果码均未写入 `validation-rules.md`；Exporter Skill 无规范性哈希算法条文（仅有样例脚本行为可参考）。

完成本草案 **§9** 拍板并将结果写入权威规则后，才具备冻结条件，随后才能进入测试设计。

---

## 11. 本阶段文件变更

- **仅新增**本文件：`docs/validator-i20-decision-draft.zh-CN.md`  
- **未修改** validation-rules、Schema、Exporter、Validator、generated-output、测试  

**停止，等待人工审查与拍板。**
