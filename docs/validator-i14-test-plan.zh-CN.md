# context-validator — I14 自动化测试设计（L3-C）

**文档类型：** 测试设计（非实现、非规则变更）  
**协议版本：** CBHF 0.1.0  
**日期：** 2026-11-19  
**规则权威：** `skills/context-validator/references/validation-rules.md` § I14（Frozen Semantics）  
**状态：** I14 **规则已冻结**；本文件为测试设计（含评审修订）；**不得**将本文件解读为 I14 已实现；**I14 仍未实现**  
**测试落点（实现阶段，本文件不改测试代码）：** 扩展现有 `tests/validator/v0.1.0/run_l3_tests.py`（与 B3/B4 同套件）；不另建平行测试体系  

---

## 1. 测试目标

1. 验证未来 `check_i14` 与冻结语义**逐条一致**（Scope、窗口、换行、空白、匹配、门控、汇总）。  
2. 证明 I14 **不**重复 I10/I11/I12/I13/I16，且**不**绕过其门控。  
3. 证明只读、无包外访问、无网络、报告不粘贴 excerpt 秘密。  
4. 证明 I14 PASS **≠** 语义充分（limitations / 无 H\* PASS）。  
5. 为编码阶段提供可执行用例 ID 与验收清单。

**非目标：** 本阶段不写测试代码、不实现 `check_i14`、不改 deferred、不开始 I20。

---

## 2. 冻结规则摘要（唯一依据）

| 项 | 冻结口径 |
| --- | --- |
| 对象 | `evidence[].locator.excerpt` |
| 适用类型 | **仅** `line_range` |
| 非适用类型 | `section` / `json_pointer` / `anchor` / `page_range`：逐条 out-of-scope（不匹配）；**无** finder；**不**单独迫使整体 NOT_CHECKED（空适用集可 PASS） |
| 窗口 | 使用 **I12 同次读取的 in-memory 文本快照**；`lines = text.splitlines()`；`window = "\n".join(lines[start-1:end])`（与 I12 同行号）；**禁止** I14 再 `read_text` |
| excerpt 换行 | `\r\n`→`\n`；`\r`→`\n`；**无** NFC/NFD；无大小写/模糊/语义匹配 |
| 空行 | `line.strip() == ""` → 跳过；非空行**不** strip，字面 `excerpt_line in window` |
| 顺序/连续 | **不要求** |
| PASS | 全匹配；无非空行；已加载且零 `line_range` |
| FAIL | 可信窗口下任一行缺失 |
| NOT_CHECKED | 未加载；I11/I10/I12 失败；`readable:false`；读/UTF-8/无可靠窗口 |
| 汇总 | **FAIL > NOT_CHECKED > PASS**；不用 WARNING；不新增状态 |
| 语义 | PASS 仅字面可找；≠ claim 支撑 / L4 |

---

## 3. 与既有实现的集成审查（设计约束）

| # | 问题 | 设计结论 |
| --- | --- | --- |
| 1 | Batch C 接入 | 在 `run_l3_batch_a`（或后续更名的 L3 runner）中：于 I12/I13 之后调用 `check_i14`；从 `L3_DEFERRED_IDS` 移除 I14；保留 I20 deferred；`L3_C_excerpts: true`；phase 如 `3B-C1`（实现阶段再定） |
| 2 | 消费 I10/I11/I12 | **复用** `path_safety`（同 I12/I13）；I10 存在性用既有 `locator_path_is_file` / 与 I12 相同门控顺序；**I12 FAIL 的 locator 不得建窗**——实现须在匹配前判定该条 I12 是否失败（复用同一判定逻辑或显式 per-eid 结果，禁止“假设 bounds 已过”） |
| 3 | path safety map | **必须**消费 I11 产出的 map；不得另写路径策略 |
| 4 | 文件快照 | I12 成功 `read_text` 后保留 per-evidence 文本快照；I14 **仅**用该快照建窗；禁止 I14 再读；禁止用再读补救缺失快照；快照不进报告/错误消息 |
| 5 | 绕过 I12 | **禁止**。null/越界等 I12 FAIL → I14 该项 NOT_CHECKED，即使 excerpt「碰巧」在文件某处 |
| 6 | 只读 | 无写包；指纹前后相等（沿用 L3 套件） |
| 7 | 包外路径 | I11 unsafe/unresolved 后**零** `read_text`（单元插桩）；包外文件内容不变 |
| 8 | 报告隐私 | FAIL/NOT_CHECKED message 含 `evidence_id` + reason code；**禁止**粘贴完整 excerpt / 疑似密钥；符合 `report-format.md` Privacy |

**建议签名（实现阶段，非本文件编码）：**

```text
check_i12(...) -> (CheckOut, item_status, text_snapshot)
check_i14(idx, package, path_safety, i12_item_status, i12_text_snapshot) -> CheckOut
```

- `path_safety`: 同 I12。  
- `i12_item_status` / `i12_text_snapshot`: 由 `check_i12` 产出；I14 **不**再 `read_text`。  
- readable：从已加载 `source-index` 解析 `locator.source_id` → `readable`；未知 source 属 I09，I14 仅在可解析且 `readable:false` 时 NOT_CHECKED。  
- 不得新增报告 Schema 字段；快照不得写入报告。

---

## 4. 用例约定

| 字段 | 含义 |
| --- | --- |
| ID | 稳定 ID：`I14-Tnnn` |
| 类 | N=正常 · B=边界 · G=门控 · R=防回归 · S=汇总 · P=隐私/只读 |
| 前置 | 临时包 / 内存 `PackageIndex`；默认基于 `build_valid_minimal_package` 变异 |
| 预期 | I14 **整体** `result`；必要时注明逐条 reason |
| 原因码（建议，实现时固定） | `excerpt_line_missing` · `i11_unsafe` · `i11_unresolved` · `i10_missing` · `i12_failed` · `i12_not_checked` · `readable_false` · `utf8_decode_failed` · `read_failed` · `evidence_unloaded` · `out_of_scope_type`（仅明细，不驱动整体） |

**原因码分层（勿混用）：**

| 来源 | 建议码 | 含义 |
| --- | --- | --- |
| 消费 I12 **FAIL** | `i12_failed` | 该 locator 边界/合法性失败，I14 不建可信窗 |
| 消费 I12 **NOT_CHECKED** | `i12_not_checked` | I12 因读失败等未完成；I14 跟从门控，**不要求**与 I12 内部码相同 |
| I14 **自身**再读失败 | `utf8_decode_failed` / `read_failed` | I11/I10 已过且 I12 已对该条给出可信通过后，I14 建窗时再读异常 |

**窗口可信前提（匹配类用例默认）：** I11 safe、I10 文件存在、I12 对该条 PASS、`readable:true`、UTF-8 可读。

---

## 5. 测试矩阵

### 5.1 A — 基本匹配（N）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 预期原因 / 明细 |
| --- | --- | --- | --- | --- | --- |
| I14-T001 | N | 单行 excerpt = 窗口内完整一行 | 可信窗；文件 `A\nB\n`；range 覆盖含 `B` | **PASS** | 无 FAIL/NC 适用项 |
| I14-T002 | N | 多行 excerpt 两行均在窗口 | 窗含两行文本 | **PASS** | — |
| I14-T003 | N | 单行 excerpt 不在窗口 | 可信窗；窗为其他行 | **FAIL** | `excerpt_line_missing` |
| I14-T004 | N | 多行中一行缺失、一行命中 | 可信窗 | **FAIL** | 至少一条 missing |
| I14-T005 | G | **空文件** + `line_range`（如 start=1,end=1）+ 非空 excerpt | I11 safe、I10 文件存在（空文件仍「存在」）；按 I12：`line_count=0` ⇒ `end > line_count` → **I12 FAIL**。**不存在**「空文件 + 合法 line_range + I12 PASS + 空窗口」 | **NOT_CHECKED** | `i12_failed`；禁止用空窗判 excerpt FAIL/PASS |
| I14-T006 | N | 窗口内同一子串出现多次；excerpt 取该子串一行 | 可信窗 | **PASS** | `in` 即可 |
| I14-T007 | N | excerpt 为窗口**某一行内的字面子串**（非整行） | 可信窗；如行=`hello world`，excerpt=`world` | **PASS** | 冻结谓词为 `in`，不要求整行相等 |
| I14-T008 | N | excerpt 出现在源文件**其他行**，但不在 locator 指定窗口内 | 可信窗；文件含该串于窗外行 | **FAIL** | `excerpt_line_missing`；禁止「文件某处有就 PASS」 |

### 5.2 B — 换行规范化（B）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 说明 |
| --- | --- | --- | --- | --- | --- |
| I14-T010 | B | excerpt 仅 LF（`a\nb`） | 窗含 `a` 与 `b`（文件可用 LF） | **PASS** | 规范化不改变非空行内容 |
| I14-T011 | B | excerpt 使用 CRLF（`a\r\nb`） | 窗为 LF 拼接的 `a\nb` 子串环境 | **PASS** | `\r\n`→`\n` 后拆行 |
| I14-T012 | B | excerpt 使用 CR（`a\rb`） | 同上 | **PASS** | `\r`→`\n` |
| I14-T013 | B | excerpt 混合 `\r\n` / `\n` / `\r` | 各非空行均在窗 | **PASS** | — |
| I14-T014 | B | excerpt 末尾多余 `\n` / `\r\n` | 有效行均命中 | **PASS** | 尾部空行跳过 |
| I14-T015 | B | 断言：换行规范化后，各非空行的**字符内容**与去掉行结束符后的原文一致（未 strip 首尾空白、未改内部空白） | 对照夹具 | **PASS** 且辅助断言 | 防实现误 strip；表述用「字符内容」，不混用字节/码点 |

### 5.3 C — 空白行为（B）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 说明 |
| --- | --- | --- | --- | --- | --- |
| I14-T020 | B | excerpt `""` | 可信窗 | **PASS** | 无非空行；无 WARNING |
| I14-T021 | B | excerpt 仅空格 `"   "` | — | **PASS** | `strip()==""` 跳过 |
| I14-T022 | B | excerpt 仅 Tab `"\t\t"` | — | **PASS** | 同上 |
| I14-T023 | B | 多条空白行（空格/Tab/空行混合） | — | **PASS** | — |
| I14-T024 | B | 空白行 + 一行命中文本 | — | **PASS** | 空白跳过 |
| I14-T025 | B | 非空行带**前导**空格；窗内**无**该带空格子串，但有 trim 后文本 | — | **FAIL** | 匹配不 strip |
| I14-T026 | B | 非空行带**尾随**空格；窗仅无尾随空格版本 | — | **FAIL** | 同上 |
| I14-T027 | B | 行内多空格 `a  b`；窗有 `a  b` | — | **PASS** | 不压缩空白 |
| I14-T028 | B | 行内多空格；窗仅 `a b`（单空格） | — | **FAIL** | — |

### 5.4 D — Unicode（B）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 说明 |
| --- | --- | --- | --- | --- | --- |
| I14-T030 | B | 文件与 excerpt 均为 NFC 同一串 | — | **PASS** | — |
| I14-T031 | B | 文件与 excerpt 均为 NFD 同一串 | — | **PASS** | — |
| I14-T032 | B | 窗为 NFC，excerpt 为 NFD（视觉相同、码点不同） | — | **FAIL** | **禁止**自动规范化匹配 |
| I14-T033 | B | 中英混合行完全字面命中 | — | **PASS** | — |
| I14-T034 | B | 中英混合一行改一字 | — | **FAIL** | — |

### 5.5 E — 顺序与连续性（N/B）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 说明 |
| --- | --- | --- | --- | --- | --- |
| I14-T035 | N | excerpt 行序 = 窗内出现序 | — | **PASS** | — |
| I14-T036 | N | excerpt 行序与窗相反，但每行均存在 | — | **PASS** | 不要求顺序 |
| I14-T037 | N | excerpt 两行在窗中不相邻（中间有其它行） | — | **PASS** | 不要求连续 |

### 5.6 F — Locator 类型（N/G）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 说明 |
| --- | --- | --- | --- | --- | --- |
| I14-T050 | N | 仅一条 `line_range` 且匹配 | — | **PASS** | 适用 |
| I14-T051 | N | 仅 `section`（无 line_range） | 已加载 | **NOT_CHECKED** | 逐条 `out_of_scope_type`；参与汇总 |
| I14-T052 | N | 仅 `json_pointer` | 已加载 | **NOT_CHECKED** | 同上 |
| I14-T053 | N | 仅 `anchor` | 已加载 | **NOT_CHECKED** | 同上 |
| I14-T054 | N | 仅 `page_range` | 已加载 | **NOT_CHECKED** | 同上 |
| I14-T055 | G | 四类非 line_range 混合、无 line_range | — | **NOT_CHECKED** | 无 finder；不建窗 |
| I14-T056 | N | `line_range`(匹配) + `section` | — | **NOT_CHECKED** | section 的 NC 使整体 NC（FAIL>NC>PASS） |
| I14-T057 | R | 非 line_range **不得**因「excerpt 碰巧在文件中」而 PASS 匹配 | 故意让 section 的 excerpt 等于文件全文 | **NOT_CHECKED** | 禁止对 section 建窗匹配 |

### 5.7 G — 依赖门控（G）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 预期原因 | 读文件？ |
| --- | --- | --- | --- | --- | --- | --- |
| I14-T060 | G | I11 unsafe（`../`） | path_safety=unsafe | **NOT_CHECKED**（单适用项） | `i11_unsafe` | **否** |
| I14-T061 | G | I11 unresolved | path_safety=unresolved | **NOT_CHECKED** | `i11_unresolved` | **否** |
| I14-T062 | G | I10 missing（safe 但文件不存在） | — | **NOT_CHECKED** | `i10_missing` | **否**（或不成功读） |
| I14-T063 | G | I12 FAIL：`start`/`end` null | — | **NOT_CHECKED** | `i12_failed` | 可为 I12 已读；I14 **不得**用坏窗判 FAIL/PASS |
| I14-T064 | G | I12 FAIL：`end` > line_count（非空文件越界） | — | **NOT_CHECKED** | `i12_failed` | 同上；空文件越界见 **T005** |
| I14-T065 | G | I12 FAIL：`start < 1` 或 `end < start` | — | **NOT_CHECKED** | `i12_failed` | 同上 |
| I14-T066 | G | **独立 I12 NOT_CHECKED：** I11 **PASS**（safe）、I10 **PASS**（文件存在），I12 因读失败（如非法 UTF-8 或 OSError）→ **I12 NOT_CHECKED** | 不得用「I11 已失败」双门控代替 | **NOT_CHECKED** | `i12_not_checked`（消费 I12 门控；**不要求**与 I12 内部 `utf8_decode_failed` 等同码） | I14 **不得**绕过 I12 自建可信窗；I14 侧匹配读可不再发生 |
| I14-T067 | G | source `readable:false`，path 安全存在，excerpt 非空 | I16 可能另 FAIL | I14 **NOT_CHECKED** | `readable_false` | 建议 **不**为 I14 读（即使文件可读） |
| I14-T068 | G | evidence 未加载（删 evidence.json / 未入 loaded_kinds） | — | **NOT_CHECKED** | `evidence_unloaded` | — |
| I14-T069 | G | 未加载 **≠** 空数组已加载 | 对照 T070 | 未加载 NC；空加载 PASS | 禁止混淆 | — |

### 5.8 H — 文件读取异常（G）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 | 读/异常后 |
| --- | --- | --- | --- | --- | --- |
| I14-T070 | N | 空 evidence 数组已加载 | empty 包 | **PASS** | — |
| I14-T071 | G | **消费 I12 的 UTF-8 NOT_CHECKED**（与 T066 同源场景可共用夹具）：I11/I10 PASS；I12 因解码失败 → NC；I14 跟从 | 强调原因码分层 | **NOT_CHECKED** | 明细用 `i12_not_checked`（或等价「跟从 I12」）；**不要**强制写成 I14 自有的 `utf8_decode_failed` |
| I14-T072 | G | I12 读文件抛 `OSError` → 无快照；I14 **不得**再读 | 真实 `check_i12`→`check_i14`；插桩计数 | **NOT_CHECKED** | `i12_not_checked`；I14 侧 `read_text` 次数=0 |
| I14-T073 | G | I11 unsafe 后 I14 **零次**内容读（插桩 `Path.read_text`） | 与 T060 **同一前置**；本 ID 专责「读次数=0」断言 | **NOT_CHECKED** | `i11_unsafe`；包外文件不变（可与 T091 交叉） |
| I14-T074 | G | I12 UTF-8 解码失败 → 无快照；I14 **不得**再读 | 真实 `check_i12`→`check_i14`；插桩计数 | **NOT_CHECKED** | `i12_not_checked`；I14 侧 `read_text` 次数=0；与 T071 同源分层 |

### 5.9 I — 汇总行为（S）

| ID | 类 | 输入摘要 | 前置 | 预期 I14 |
| --- | --- | --- | --- | --- |
| I14-T080 | S | 多条 line_range 全部匹配 | — | **PASS** |
| I14-T081 | S | 一条匹配 + 一条 missing | — | **FAIL**（保留 NC 明细若有） |
| I14-T082 | S | 一条匹配 PASS + 一条 I11 NC | 无 FAIL | **NOT_CHECKED** |
| I14-T083 | S | 一条 FAIL + 一条 I11 NC | — | **FAIL**（FAIL > NC） |
| I14-T084 | S | 完整空集合（已加载） | — | **PASS** |
| I14-T085 | S | 未加载集合 | — | **NOT_CHECKED**（≠ T084） |
| I14-T086 | S | 结果不得为 WARNING / NEEDS_HUMAN_REVIEW | 任意上述 | 断言 `result ∈ {PASS,FAIL,NOT_CHECKED}` |

### 5.10 只读 / 路径安全 / 隐私 / 防回归（P/R）

| ID | 类 | 输入摘要 | 预期 |
| --- | --- | --- | --- |
| I14-T090 | P | `validate_package` 前后 `fingerprint_package` | 相等；`wrote_to_package=false`；`network=false`；`read_only=true` |
| I14-T091 | P | 包外文件 `../outside_secret.txt` + unsafe locator | 文件内容不变；I14 NC；无包外读 |
| I14-T092 | P | FAIL 用例 excerpt 含伪密钥 `sk-test-SECRET` | 报告 message/**不**含完整 secret；可有 eid + reason code |
| I14-T093 | R | generated-output 临时副本（实现后） | **先逐条**对每个 `line_range` 按冻结窗口算法核对 excerpt；**仅当**全部适用项字面匹配时期望 I14 **PASS**；若发现缺失则期望 **FAIL** 并记录 eid——**禁止**未经验证直接写死 PASS。另：L4 仍 NC；limitations 含 ≠ 语义充分 |
| I14-T094 | R | 最小合法包（实现后） | I14 PASS；I12 PASS |
| I14-T095 | R | smoke「仅首行」弱于 I14：首行命中、次行缺失 | I14 **FAIL**；证明严于 smoke |
| I14-T096 | R | I13 仍对 section NOT_CHECKED；I14 空适用 PASS | 两检查并存不互相改写 |
| I14-T097 | R | I16 readable:false quoting FAIL 与 I14 NC 可同时存在 | I14 不改写 I16 语义 |
| I14-T098 | R | I12 越界 FAIL 时 I14 不得对同条报 excerpt FAIL | I14 NC（`i12_failed`） |
| I14-T099 | R | 实现后 `L3_DEFERRED` 不再含 I14；仍含 I20 | phase / `L3_C_excerpts` 标志一致 |
| I14-T100 | R | 无 H01–H06 PASS | 语义边界 |

### 5.11 快照一致性（R）— 第二轮审查

| ID | 类 | 输入摘要 | 前置 | 预期 |
| --- | --- | --- | --- | --- |
| I14-T101 | R | I12 与 I14 使用同一份文本快照 | 真实 `check_i12`→`check_i14`；I14 期间禁止 `read_text` | I14 结果与快照一致；不得再读 |
| I14-T102 | R | 完整 L3（`validate_package`）中同一目标文件不被 I12+I14 各读一次 | 插桩 `Path.read_text` 计数 `design.md` | I12/I14 合计对该文件内容读 **1** 次（仅 I12） |
| I14-T103 | R | I12 读取失败时 I14 不得再读 | `check_i12` OSError → 传出 status/snapshot → `check_i14` | I14 **NOT_CHECKED**；I14 侧读次数=0 |
| I14-T104 | R | I12 状态 `pass` 但缺少快照 | 注入 status=pass、空 snapshot（专测缺口；非完整流程替代） | I14 **NOT_CHECKED**（`snapshot_missing`）；零再读 |
| I14-T105 | R | 快照中 excerpt 匹配 | 真实 `check_i12`→`check_i14` 或完整 L3 | I14 **PASS** |
| I14-T106 | R | 快照中 excerpt 不匹配 | 真实链路 | I14 **FAIL**（`excerpt_line_missing`） |
| I14-T107 | R | I12 产出快照后修改磁盘文件 | `check_i12` → 改文件 → `check_i14(snapshot)` | I14 仍按**原快照**判断（不受磁盘变更影响） |

---

## 6. 门控与汇总专表（对照冻结条款）

### 6.1 I11 / I10 / I12 / readable

| 门控条件 | 用例 | 整体倾向 | 禁止行为 |
| --- | --- | --- | --- |
| I11 unsafe | T060, T073, T091 | NC | 读包外、判 PASS/FAIL 匹配 |
| I11 unresolved | T061 | NC | 读 |
| I10 missing | T062 | NC | 当存在判匹配 |
| I12 FAIL | T005, T063–T065, T098 | NC | 用不信任窗 FAIL/PASS；空文件无合法 range |
| I12 NC（I11/I10 已 PASS） | T066, T071, T072, T074, T103 | NC | 绕过 I12 自建窗 / I14 再读补救 |
| I12 pass 缺快照 | T104 | NC | 再读补救；误 PASS |
| readable:false | T067, T097 | NC | 为匹配强行读（建议） |
| 未加载 | T068, T085 | NC | 当空集 PASS |

### 6.2 汇总优先级

| 组合 | 用例 | 结果 |
| --- | --- | --- |
| 全适用 PASS | T080 | PASS |
| ∃ FAIL | T081, T083 | FAIL |
| 无 FAIL ∧ ∃ 适用 NC | T082 | NOT_CHECKED |
| 空适用已加载 | T051–T054, T070, T084 | PASS |
| 未加载 | T068, T085 | NOT_CHECKED |

---

## 7. 测试覆盖缺口（已知）

| 缺口 | 说明 | 优先级 |
| --- | --- | --- |
| G1 | Windows 下 unresolved symlink 宿主差异 | 低；可跟 I11 既有宿主 NC |
| G2 | 极大 excerpt（>500 推荐）仍按字面匹配 | 低；Schema 不禁 |
| G3 | `errors[:50]` 截断下 >50 适用项明细 | 中；对齐 I12/I13 N3 |
| G4 | I12 与 I14 之间文件被并发改写 | 超出 0.1.0；不做 |
| G5 | `locator.source_id` 未知时 readable 门控 | 低；属 I09；建议跳过 readable_false 分支 |
| G6 | bool/非 number 的 start/end（I12 invalid） | 由 T063 族覆盖一部分 |
| G7 | I12 PASS 后、I14 再读前文件被替换为非法 UTF-8（T074 依赖 mock） | 低；真实包难稳定复现，以单元插桩为准 |

以上缺口**不**改变冻结规则；实现阶段可择一补测或记入 limitations。

---

## 8. 实现阶段建议执行顺序

1. **落地 `check_i14` + batch 接线**（仍用本矩阵验收；本设计阶段不编码）。  
2. **先单测门控** T005、T060–T069、T071–T074（零误 PASS；T071 vs T074 原因码分层）。  
3. **再匹配核心** T001–T004、T006–T008、T020–T028、T010–T015。  
4. **Unicode / 顺序** T030–T037。  
5. **类型与空适用** T050–T057。  
6. **汇总** T080–T086。  
7. **集成 / 回归** T090–T100；T093 **先逐条核对**再定 PASS/FAIL。  
8. **隐私与只读** T090–T092 贯穿 CI。  

建议在 `run_l3_tests.py` 新增 `test_c1_i14_excerpt_match()`，用例标签带 `I14-Tnnn` 字符串便于对照本文件。

---

## 9. 验收标准（实现完成后）

- [ ] 本矩阵 A–I 及 P/R 用例均有自动化对应（或书面豁免并入 §7）。  
- [ ] 预期与 Frozen Semantics **无矛盾**。  
- [ ] 稳定 ID `I14-Tnnn` 可在测试名/注释中追溯。  
- [ ] I11/I10/I12/`readable:false`/未加载门控全覆盖。  
- [ ] NOT_CHECKED 与空适用 PASS 严格区分。  
- [ ] Unicode NFC≠NFD 不自动匹配；换行规范化不破坏非空行内容。  
- [ ] 汇总 FAIL > NOT_CHECKED > PASS 用例通过。  
- [ ] 无 WARNING / NEEDS_HUMAN 作为 I14 `result`。  
- [ ] 无新报告状态；无 Schema/Exporter/generated-output/input 被测改写。  
- [ ] 指纹只读、无网络、无包外读证明存在。  
- [ ] limitations / Skill 仍声明 I14 PASS ≠ 语义充分。  

---

## 10. 本阶段声明

| 项 | 状态 |
| --- | --- |
| 本文件 | 测试设计（含人工评审修订） |
| Python / 现有测试 / Schema / Exporter / SKILL / validation-rules / 样例包 | **未修改**（本修订仅改本文件） |
| `check_i14` | **未实现** |
| I14 deferred | **仍保持** |
| I20 / Importer / N1–N6 | **未开始 / 未处理** |

### 10.1 修订记录（相对初版测试设计）

| 项 | 修订 |
| --- | --- |
| T005 | 删除「空文件 + I12 PASS + 空窗」；改为空文件 → I12 FAIL → I14 NC |
| T066 | 独立 I11/I10 PASS + I12 NC → I14 NC |
| T071 / T074 | 区分「跟从 I12 UTF-8 NC」与「I14 自身 UTF-8 NC」原因码 |
| T072 / T073 | T072=I14 自身 OSError；T073=unsafe 零读插桩（承接原 T074 与 T060 的读断言） |
| T007 / T008 | 新增：行内子串 PASS；窗外存在 FAIL |
| T015 | 改为「字符内容」表述 |
| T093 | generated-output 须逐条核对后再定预期 |

**下一步（仅建议）：** 人工批准本修订后，再进入 I14 **编码实现**阶段。**I14 仍未实现。**
