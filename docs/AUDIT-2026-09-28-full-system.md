# 全系统深度体检审计报告（2026-09-28）

范围：**整个「易」仓库**，非单科、非单次占例。按「架构 → 模块 → 数据 → 代码细节」自顶向下。
方法：静态取证（依赖方向 / 表唯一性 / 规模分布 / 规范符合度）+ 修复后等价性证明 + gate/eval 回归。

## 一、系统规模分布（从大到小）

| 层 | 文件 | 行数 | 占比 |
|---|---|---|---|
| `disciplines/liuyao` | 69 | 25,033 | **78%** |
| `core`（yishu_core） | 13 | 2,777 | 9% |
| `tools` | 6 | 1,349 | 4% |
| `disciplines/ming` | 9 | 1,184 | 4% |
| `synthesis` | 6 | 1,124 | 3% |
| `tests` | 6 | 575 | 2% |
| **合计** | | **32,042** | |

> **结论 1（架构级）**：六爻一科占全仓 78%（25k 行 / 69 文件），而 `tests/` 仅 575 行。
> 复杂度与验证力度严重不成比例——这是后续最重要的结构性风险。

## 二、已合规项（体检通过，无需改）

| 检查项 | 结果 |
|---|---|
| 依赖方向单向（学科→core，禁跨学科） | ✅ 109 处 `yishu_core` 引用，无 ming↔liuyao 互相 import |
| 硬编码绝对路径 `C:\Users\...` | ✅ 0 |
| `sys.argv` 手解（无 argparse） | ✅ 0 |
| 文件名带版本号（如 `_v5`） | ✅ 0 |
| 内核基元表存在唯一真值源 | ✅ `core/yishu_core/symbols.py` 已集中（干支/五行/生克/六合/六冲/旬空/三刑/长生/纳甲/卦表/八宫） |

其中已用内核别名模式的部分（`chain_tables.py` 的 `XUN_KONG`/`TWELVE_GROWTH`、`classical_tables.py` 的 `SAN_HE`/`NAYIN`）写法正确，予以保留。

## 三、发现并修复（P0/P1/P2）

### F1【P0 · 定时炸弹】`engine_tables.py` 存反向爻序副本

- **证据**：`disciplines/liuyao/scripts/engine_tables.py:57-66` 硬编码 `BAGUA[*]["lines"]`，
  其中 **震/巽/艮/兑 四卦与内核 `BAGUA_LINES` 完全相反**：
  震 内核 `[1,0,0]` vs 本地 `[0,0,1]`；巽 `[0,1,1]` vs `[1,1,0]`；艮 `[0,0,1]` vs `[1,0,0]`；兑 `[1,1,0]` vs `[0,1,1]`。
- **为何没炸**：第 68-69 行的覆盖循环 `BAGUA[_n]["lines"] = _lines` 把错值盖掉了。**删掉该循环即复活**。
- **这正是内核注释所记的历史 bug**：「上爻在前的镜像编码 → 恒之鼎的上六动被算成第四爻动」。
- **修复**：删除全部本地爻序/五行字面量，改为内核 `BAGUA_LINES` + `TRIGRAM_ELEMENTS` 派生；本地只保留引擎专属的 `nature`/`symbol`。

### F2【P1】`SHENG_WO` / `KE_WO` 三份副本

- **证据**：`core/symbols.py:377-378`（真值源）、`chain_tables.py:55/58`、`classical_tables.py:67/70` 各自就地推导一份。
- **修复**：两个学科模块改为 import 内核，删除本地推导。3 份 → 1 份。

### F3【P1】`TRIGRAM_ELEMENT` 卦五行四份副本

- **证据**：`core/symbols.py:393 TRIGRAM_ELEMENTS`、`chain_tables.py:110 TRIGRAM_ELEMENT`、
  `classical_tables.py:47 BAGUA`、`engine_tables.py` BAGUA 内 element —— 取值全部相同。
- **修复**：`chain_tables` 改内核别名；`classical_tables.BAGUA` 改内核派生；`engine_tables` element 改内核派生。

### F4【P2】函数内重定义 `TOMB_MAP` 遮蔽内核 import

- **证据**：`classical_rules_patterns.py:265` 在函数内 `TOMB_MAP = {...}`，而模块第 32 行已从内核 import `TOMB_MAP`。
- **取值与内核一致**（火戌/水辰/木未/金丑/土辰），故无 bug，但属遮蔽隐患 + §二 违规。
- **修复**：删除本地重定义，直接用内核 import 的那份。

## 四、修复验证（零漂移证明）

| 验证 | 结果 |
|---|---|
| 取值等价性（9 项逐表比对学科层 vs 内核） | ✅ 9/9 全等 |
| `tools/check.py --only liuyao` | ✅ 冒烟 + 四段契约 E2E + **结构契约（内核表唯一）** |
| `tools/eval.py --discipline liuyao` | ✅ 与基线一致（strict 87.5%、用神取类/取支/定位 100%） |

> 取值全等 + eval 不变 ⇒ 本次去重为**纯结构性重构**，未改变任何推演语义。

## 五、待办（本轮未改，含理由）

| ID | 问题 | 证据 | 为何本轮未动 |
|---|---|---|---|
| B1 | ~~2,533 行测试住在生产目录~~ → **已清偿（2026-09-29）** | 见下「B1 清偿记录」 | — |
| B2 | **巨型模块 >700 行 ×8**（2026-09-29 复测）：regression_test 966 / chain_step5_adjust 905 / smoke_test 856 / effects_change 769 / chain_step4_patterns 741 / mcp_server 722 / thinking_chain_tests 718 / chain_step2 701。~~trigram_symbolism 702~~ → **已清偿（`0143e5b`）**；~~classical_rules_patterns 923~~ → **已清偿（`0b11419`）**。 | 见规模表 + 下「B2 拆分记录」 | 拆分需逐模块建立「零指纹漂移」基线，工作量大，宜按模块分批（剩余 8 项中 3 项是测试文件，收益低于生产模块）。 |
| B3 | ~~**内核领域命名泄漏**：六爻从 `yishu_core.ming_tables` 取三合/纳音/星煞（`bing_yao_shensha.py:18`、`chain_tables.py:40`、`classical_tables.py:42-43`）。三者实为跨科共用表，却冠以 `ming_`。~~ → **已清偿（2026-09-29）** | 见下「B3 清偿记录」 | — |

## 六、勘误（初判有误，经查证后撤回）

- ~~`fetch_wikisource_cases.py` 是一次性死脚本~~ → **保留**。
  它被 `build_use_god_rules.py` / `build_question_use_gods.py` 依赖其原文缓存，
  且 `--report` 模式用于案例库审计（`disciplines/liuyao/docs/CASE-LIBRARY-AUDIT.md`）。
- ~~`tools/mcp_router.py` 与 `disciplines/liuyao/scripts/mcp_server.py` 重复实现 MCP~~ → **保留**。
  范围收缩（2026-09）后 router 只注册 ming，六爻走专用 CLI/流水线，设计已在文件内文档化（第 3、59-60 行）。

---

## 四之二、B1 清偿记录（2026-09-29）

把三个测试 CLI 从生产 `scripts/` 迁到 **`disciplines/liuyao/tests/`**（不跨树，保「每科自包含」，
AGENTS.md 未规定 tests 位置，故选科内 `tests/` 而非仓库根 `tests/`）。

| 步骤 | 做法 |
|---|---|
| 搬迁 | `git mv`（R=重命名，保 git 历史） |
| 路径基址 | 三处 `_SCRIPT_DIR` 改为 `_TEST_DIR`→`../scripts` 派生，使原有 outputs / 报告路径语义不变 |
| 调用点 | 仓库级 `tools/check.py:203,237`、学科级 `disciplines/liuyao/tools/check.py:230,247,253`、`SKILL.md:294`、docstring 用法行 —— 共 6 处同步更新，复查无残留 |

**零漂移验收**（按 TECH-DEBT §三.2 用官方 `disciplines/liuyao/tools/refactor_guard.py`，未写临时脚本）：

| 手段 | 结果 |
|---|---|
| refactor_guard 115 例 | 指纹 `d754cfaddb105208`，**零漂移**（失败 5 ≤ MAX_ERRORS 8，快照可信） |
| 三脚本输出逐字节 diff | 完全一致（12/12 PASS / 产出率 100% / 回归 12/18）；基线含真实通过，**排除 26u 假阳性** |
| 仓库级 gate | ✅ |
| 学科级 gate | ✅ **全门通过**（含金标准指纹、样式层、tune 93.9 / holdout 87.5） |
| eval | strict 87.5%，不变 |

### 附带查出并处置：金标准指纹漂移（叙述层改动的必然结果）

学科级 gate 的 [1.6] 金标准指纹报漂移 `5c6e77ee253b0ddd → abc7884de0653ee5`。归因（不靠猜）：

1. `git worktree` 拉纯净 HEAD → golden verify **√ 一致** ⇒ 漂移来自本人未提交改动，非 HEAD 自带。
2. 用 golden 自带逐条比对 HEAD 快照：**288 例仅 5 条变化，变化字段只有 `narrate_sha`/`narrate_len`**；
   `pillars/lines/palace/empty/changed/use_god/strength/verdict/score/yingqi_branches/adv_keys/adv_summary/patterns`
   **全部 0 漂移、0 异常**。
3. ⇒ 本次表去重与搬迁**零结构性影响**；漂移仅限叙述文案 = 用户要求修的四处缺陷。
4. 按 `golden.py` 纪律 `capture` 新基线并写入带证据的 `drift_log`（无理由不落盘）。

> **流程教训（登记）**：此前只跑仓库级 `tools/check.py --only liuyao` 不足以判「全绿」——
> 学科级 `check.py` 另有金标准指纹门、样式层门、tune/holdout 指标门。**两层 gate 都必须跑。**

### 附带发现（未修，低危）

- 仓库级文档 `docs/TECH-DEBT.md:58`、`docs/HANDOFF.md:98,160`、`docs/CHANGELOG.md` 把
  `tools/refactor_guard.py` 写成仓库根路径，实际位于 **`disciplines/liuyao/tools/refactor_guard.py`**
  （文档默认 cwd=学科根）。建议补一句 cwd 约定或改写全路径。

---

## 四之三、B3 清偿记录（2026-09-29）

`core/yishu_core/ming_tables.py` 模块头一直写着「**唯一消费方：命科 `disciplines/ming`；卜科不用**」，
而六爻三处实际在取——**文档与事实矛盾**，这是 B3 的实锤。按归属拆分后 `ming_tables` 剩 153 行，只留命科专属表：

| 原住 `ming_tables.py` | 迁至 | 谁在用 |
|---|---|---|
| 纳音 `NAYIN_COUPLETS`/`NAYIN`/`NAYIN_TO_ELEMENT`/`nayin_of`/`nayin_of_index` | `symbols.py` | 命 `chart.py`、卜 `classical_tables.py` |
| 三合局分组 `SAN_HE_GROUPS`/`sanhe_group` | `symbols.py` | 命 `pattern.py`、卜 `chain_tables.py`/`classical_tables.py`、神煞驿马桃花华盖 |
| 星煞（天乙/文昌/羊刃/驿马/桃花/华盖/禄神/红艳/天喜/天德/月德 + `shensha_at_branches`/`shensha_of_chart`） | 新建 `shensha.py` | 命 `chart.py`、卜 `bing_yao_shensha.py` |
| 藏干十神 / 大运起法 / 命宫身宫 | 留在 `ming_tables.py` | 命科 |

- 三合局迁入 `symbols.py` 顺带**补齐该模块自己的章程**：它的模块头与 `docs/CONTRACT.md` §二
  本就写着「六合六冲**三合**三刑六破」，而 `SAN_HE_GROUPS` 一直不在里面——章程与实现也不一致。
- `shensha.py` 模块头按 CONTRACT §二「标注只有哪几科用」明写**命、卜两科共用**；
  迁出依据同时写进 `ming_tables` 与 `shensha` 两个模块头，不留第二份叙述。
- 消费方 6 处同步：`ming/scripts/chart.py`、`ming/scripts/pattern.py:332`、
  `liuyao/scripts/chain_tables.py:43`、`liuyao/scripts/classical_tables.py:45-46`、
  `liuyao/scripts/bing_yao_shensha.py:7,18,159`、`tools/core_selftest.py`；
  迁后复查 `grep ming_tables`，生产代码残留项**全部**是命科专属表，无跨科取用。

**取值等价 + 零漂移验收**：

| 手段 | 结果 |
|---|---|
| 迁移前后逐表比对（`NAYIN` / `NAYIN_TO_ELEMENT` / `SAN_HE_GROUPS` / `shensha_at_branches` / `shensha_of_chart` / `nayin_of_index` 60 序，独立解释器） | ✅ 全等，取值零变化 |
| refactor_guard 115 例 | 指纹 `d754cfaddb105208` **零漂移**（失败 5 ≤ MAX_ERRORS 8，快照可信） |
| 金标准 288 例 | `abc7884de0653ee5` 不变 |
| 仓库级 gate / 学科级 gate | ✅ / ✅ 全门通过（tune 93.9 / holdout 87.5、top-1 58.8/50 逐项不变） |
| pytest | 76 passed |

> **`bing_yao_shensha.py:159` 那句 `basis` 是交付正文里可见的溯源文案**，改它有金标准漂移风险。
> 处置顺序：先 `grep basis` 查有无消费方读取（结论：无读取方）→ 改 → 跑金标准确认不入覆盖域。
> 省掉这一步，就是拿一次文案改动冒充「零漂移」——26u 那次假阳性就是这么来的。

---

## 四之四、B2 拆分记录（2026-09-29 首批）

`classical_rules_patterns.py` **909 行（当时 `scripts/` 最大）**，一个文件塞 18 项断法。
按域切两刀，**纯搬移、块内一行不改**：

| 去向 | 函数 | 行数 |
|---|---|---|
| `classical_rules_combo.py`（新） | `_check_broken_combo` + `analyze_triple_combo` | 251 |
| `classical_rules_growth.py`（新） | `analyze_twelve_growth` + `analyze_desperate_relief` | 311 |
| `classical_rules_patterns.py`（留） | 游魂归魂 / 月破 / 进退神 | 909 → 369 |

- 切口按**调用关系**定：`_check_broken_combo` 全文只被 `analyze_triple_combo` 调用
  （`grep` 证实 3 处：定义 1 + 调用 2），两者必须同走；四个被迁函数彼此无横向调用。
- 新模块头复用原样板段（内核定位 + `kernel_path` 接线，与 `classical_rules_hidden.py` 同构），
  import 按块内实际引用**逐名裁剪**，两个新模块死导入 0；`patterns` 拆完残留的 35 个
  死导入（`najia_branch`/`TOMB_MAP`/`KE_WO`/`SAN_HE`/`g_day_cn`…）一并清掉。
- 门面 `classical_rules.py` 改从新模块取数，`__all__` 24 项不变；
  `classical_analysis.py` 与 `tests/smoke_test.py` 都经门面取名，**消费方零改动**。

**踩坑（首版拆分直接红灯）**：裁剪脚本按**原名**判断 `X as Y` 别名导入，
`CLASSICAL_INTERPRETATIONS as CINTERP` 被判为「块内没用到原名」而删掉，
运行期 `NameError: CINTERP` → 冒烟 36/36 **归零**、金标准指纹变、tune/holdout 双双跌。
改为按**别名 Y** 判有无、保留时仍写原书写 `X as Y` 后恢复全绿。
> 教训：拆分脚本的「死导入裁剪」看着是清潔活，实际是**能直接把引擎打穿**的改动——
> 判据取错一个字段就红。所以裁剪后必须先跑冒烟（最快暴露 NameError），再跑金标准与分数门。

**验收**（与 B3 同一套，全绿）：

| 手段 | 结果 |
|---|---|
| refactor_guard 115 例 | 指纹 `d754cfaddb105208` **零漂移**（失败 5 ≤ MAX_ERRORS 8） |
| 金标准 288 例 | `abc7884de0653ee5` 不变 |
| 冒烟 / 样式层缺定义 / 思维链 / 古籍回归 | 36/36、0、12/12、12/12 |
| tune / holdout（分列出分） | 93.9 / 87.5，主应期命中 58.8 / 50 —— 逐项与基线一致 |
| 仓库级 gate / pytest / `tools/eval.py` | ✅ / 76 passed / strict holdout 87.5 不变 |

**B2 余量复测**（本表首次给出实测行数，取代 09-28 的旧表）：
`trigram_symbolism` 已由 `0143e5b` 清偿（702→487），`classical_rules_patterns` 本轮清偿；
尚余 8 项 >700：regression_test 966、chain_step5_adjust 905、smoke_test 856、
effects_change 769、chain_step4_patterns 741、mcp_server 722、thinking_chain_tests 718、chain_step2 701
—— 其中 3 项是测试 CLI（B1 刚迁过目录），**拆分收益低于生产模块**，下一批优先
`chain_step5_adjust` / `effects_change` / `chain_step4_patterns`。

---

口径声明：本文件所有分数（如 eval 87.5%、tune 93.9%）均为**与古籍案例要点的一致性**，用于回归审计，
不代表现实预测命中率（AGENTS.md §三）。
