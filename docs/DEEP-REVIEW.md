# 易（Yi）· 第二轮深潜审查：加法 / 减法清单

> 日期：2026-10-01
> 方法：全仓 394 个文本文件 / 201 个 `.py` 的 AST + grep 交叉扫描，两路并行探查后逐条复核
> 口径：一切以 `AGENTS.md` 的三条铁律 + §二内核唯一真值源 + §三断语外置 + §六产出同源为准
> 说明：本轮**只探查、未改码**。所有条目标注「可直接执行 / 建议执行 / 需评估」三档

**一句话结论**：首轮审查修的是「门本身坏了」（假绿）；本轮发现的是**门看得见的不全**——
真值源门只扫模块级 dict、看不见函数内 dict 和干支字符串；narrate 段 7 科无验收；
断语启发式认不出真断语。外加一批确实该删的零引用件。

---

## 〇、核心构建理念 → 本轮的探查维度

| 核心理念 | 本轮对应探查维度 | 结论 |
|---|---|---|
| 内核唯一真值源 | core 之外还有几份同一份数据 | **有漏网**：函数级生克 dict 6 处、干支串 20+ 处（其中 6 处在 `scripts/`，是运行时真副本） |
| 依赖方向单向 | 学科间 import | **干净**：8 科零违规，但门只扫 2 科 |
| 四段契约机械验收 | chart/analyze/narrate/render | **结构齐全 8/8**，但 narrate 只有六爻一科进 golden |
| 断语/引文进 data/references | .py 里还剩多少成段断语 | **有 25+ 处硬编码**，分布在 6 科 analyze 与 2 个 liuyao 文件 |
| 零第三方依赖 / 产出同源 | web 与本地同源 | 映射层健康，但**验收只有 11 个正例、零负例** |
| 书源可回指 | 引文能在书源原文 grep 到吗 | **梅花引文可回指**（已复核，见 §C-4 更正） |

---

# 第一部分 · 减法清单（删无效 / 作用非常小）

## S 档 · 零争议，可直接删

| # | 项 | 证据 | 判据（AGENTS §三） | 动作 |
|---|---|---|---|---|
| S1 | `disciplines/liuren/dev_tools/build_kemu.py`（92 行） | 全仓 `grep -rn build_kemu` **零命中**；连 `liuren/dev_tools/check.py:112-115` 的 `required` 清单都没有它 | 零引用 | **删** |
| S2 | `tools/scratch/` 整目录（17 个 `.py` + 16 个 `.txt`） | 全部 gitignored、全部零引用、全部硬编码 `C:\Users\31103\...` 绝对路径；10 个是纯 `print` 的 `dbg_*`/`diag_*` | 一次性调试残留 | **删**（AGENTS §三只要求"一次性脚本放这里"，是一次性**已用完**，不是永久仓库） |
| S3 | `disciplines/liuyao/dev_tools/scratch/merge_classical.py`（270 行） | 不在 git 索引、零引用；产物已入库 | 一次性合并器 | **删** |
| S4 | `tools/scratch/fetch_book_source.py`（19 KB） | 与主仓 `tools/fetch_source.py`（20 KB）是两套独立实现，前者零引用 | 重复实现 | **删**（保留主仓那份） |
| S5 | `docs/refactor/MAJOR_REFACTOR_PLAN.md`（700 行） | 全仓零引用；规划的三个目录 `liuyao/rules/`、`liuyao/support/` **从未存在**（`:259/:427/:430`） | 废弃 plan | **删** |
| S6 | `docs/AUDIT-2026-09-28-full-system.md`（215 行） | 全仓零引用（llms.txt 都没列）；`:57/:76` 把 8 个已不存在的文件当现状写 | 过期体检报告 | **删**（结论已并入 PROJECT-REVIEW） |

## S 档 · core 死符号（约 30 个顶层定义，外部引用数 = 0）

按「只被同文件自用、学科层完全没碰」为判据：

| 文件 | 死符号 |
|---|---|
| `core/yishu_core/eval.py` | `is_na`(`:39`)、`verdict_direction`(`:25`)、`pct`(`:44`) |
| `core/yishu_core/liuren_tables.py` | `DAY_NIGHT_POLICY`(`:99`)、`DAY_DE_VERIFIED`(`:141`)、`is_day`(`:102`)、`noble_of`(`:106`) |
| `core/yishu_core/ming_tables.py` | `DAYS_PER_SHICHEN`(`:82`) |
| `core/yishu_core/relations.py` | `SHISHEN_NAMES`(`:140`)、`SHISHEN_ALIAS`(`:143`)、`SHISHEN_TABLE`(`:128`)、`SHISHEN_TO_LIUQIN`(`:162`) |
| `core/yishu_core/shensha.py` | `lu_shen`(`:113`)、`hong_yan`(`:118`)、`tian_xi`(`:123`)、`tianyi_guiren`(`:109`)、`shensha_at_branches`(`:138`)、`shensha_of_chart`(`:170`) |
| `core/yishu_core/symbols.py` | `YAO_INDEX_TO_TRIGRAM_SLOT`(`:381`)、`trigram_element`(`:460`)、`sanhui_group`(`:587`)、`TRIGRAM_ELEMENTS`(`:429`) |
| `core/yishu_core/ziwei_tables.py` | `_branch_index`(`:20`)、`_branch_at`(`:28`)、`_stem_index`(`:33`) |
| `core/yishu_core/lunar.py` | 6 个内部函数（`leap_month_of`/`month_days`/`leap_month_days`/`year_days` + 3 张 `LUNAR_*` 常量） |

> ⚠️ 这批必须**与 §A-6「断语外置」一起做**：`shensha.py` 的 12 张神煞表若真删，得先确定
> `disciplines/liuyao/scripts/bing_yao_shensha.py` 那套活着的实现是否等价——不等价就得先把
> 活的那套上收进 core，再删死的那套。**不能只删不上收**（那就是把真值源又造出第二份）。

## A 档 · 作用非常小 / 低价值，建议降级或删

| # | 项 | 现状 | 动作 |
|---|---|---|---|
| A1 | `docs/DEEP-OPTIMIZE-PLAN.md`（1363 行） | 6 处引用 `disciplines/base/protocol.py`（`:65/:66/:120/:171/:1187/:1357`），该目录已于 2026-10-01a 删除；`:1243` 自承"历史叙述文档可能滞后" | **不删**（是本仓最长的改造总纲，有检索价值），但**在文件头加"已过期、6 处 base 引用作废"警示**，并在 `docs/CHANGELOG.md` 登记 |
| A2 | `tools/eval_audit_recheck.py` | `tools/check.py` 的 12 个 gate 里**一个都没挂**它；只被 4 份 `docs/EVAL-AUDIT.md` 文字提及 | **保留**（审计可复算），但在文件头注明"人工复核工具，不在质量门内" |
| A3 | `tools/doc_html.py` + `docs/samples/*.html`（4 份 125 KB） | 靠 `.gitignore` 白名单 `!docs/samples/**` 入库；无自动化调用 | **保留**（人手动归档用），但把白名单收窄到显式文件名，避免以后自动扩表 |
| A4 | `tools/demo.py` / `tools/fetch_source.py` | 无自动化调用，只被 README/MIGRATION 提及 | **保留**（README 演示链），文件头补一行"手工运行、不在质量门" |
| A5 | `tools/eval.py` | `docs/HANDOFF.md:438` 已明说"check.py 不依赖它" | **挂门或删，二选一，需你定**（见 §三 待确认） |
| A6 | `disciplines/liuyao/dev_tools/build_extra_dimensions.py` 等 4 个 `build_*.py` | 只在 CHANGELOG 被文字提及，`liuyao/dev_tools/check.py` 的 `run()` 序列里没有 | **挂进 check 的重建提示**（不删，可复跑重建） |

## B 档 · 需评估，本轮不动

| # | 项 | 为什么不动 |
|---|---|---|
| B1 | `disciplines/liuyao/scripts/classical_enhancements.py`（2184 行） | 复核发现它**不是死模块**：`classical_analysis.py:36` 一次性 import 了 **38 个**符号，主链路活着。只能合并它与 `narrative_utils.py` 的 3 个同名小函数（见 §A-7），**不能删文件** |
| B2 | `case_runner.py` 三科逐行同构（meihua/xiaoliuren/zeji，`def` 行号 27/37/43/49 一模一样） | 合并进 core 会违反"学科 → 只依赖 core"的颗粒度；收益中等风险中等，建议单开一轮 |
| B3 | `cli/main.py` 与 `tools/mcp_router.py:407` 双份 argparse + `liuyao_step1-5` facade 链 | 三套 CLI 形状并存，重构面大，与核心理念不直接相关 |

---

# 第二部分 · 加法清单（增加有效 / 补盲）

## A 档 · 机械门升级（★ 直接服务「内核唯一真值源」，成本最低、收益最大）

| # | 补什么 | 现在为什么漏 | 改法 | 成本 |
|---|---|---|---|---|
| **A1** | **真值源门升级到全作用域** | `_module_table_fingerprints`（`tools/check.py:270`）与 `CORE_TABLE_ASSIGN` 正则（`:41-49`）都只扫**模块级** dict/list 字面量。**函数内的 dict 100% 漏检** | 用 `ast.walk` 遍历 `FunctionDef` 内部 `Assign`，复用现有 `_canonical_literal`（`:226`）做指纹比对 | ~30 行 |
| **A2** | **干支/天干字符串字面量扫描** | 上面两条都只认 `NAME=[[{`，裸字符串 `"甲乙丙丁戊己庚辛壬癸"` 既不匹配正则也不是指纹 | 新增 `check_core_string_tables`：正则匹配任意缩进下的两个干支串，白名单只放行 `core/`、`site/engine/`、`tests/` | ~15 行 |
| **A3** | **跨科 import 门扩到 8 科** | `tools/check.py:189` 写死 `for disc in ("liuyao", "ming")`，另 6 科门是敞的（实测 6 科零违规，但防不住未来） | 改成 8 科循环、跳过当前科（`:52` 的 `CROSS_DISC_IMPORT` 正则已经是 8 科的，比实现超前） | 1 行 |
| **A4** | **根门 `NEW_DISCIPLINES` 扩到 8 科** | `tools/check.py:37` = `("ming", "ziwei")`，仅这 2 科进快速门；其余 6 科靠各学科自己的 `dev_tools/check.py` | 扩到 8 科，让"按 CONTRACT 新科接入"有机械保障 | 1 行 |
| **A5** | **narrate 段进质量门** | 8 份 `dev_tools/golden.py` 里**只有六爻**（`liuyao/dev_tools/golden.py:83-93`）记 narrate 文案哈希；其余 7 科改一个中文标点 CI 都不红 | 每科 golden 加 5 行记 narrate 哈希 | 中（~7 科） |
| **A6** | **断语外置启发式补假阴性** | `check_verdict_literals`（`:110-175`）只认 `condition/meaning/advice/reason/note/text/description` 键；真断语是 plain `str→str` dict（`"吉": "事势偏顺…"`），**一条都报不出来** | 改成"dict/list 里出现 ≥8 汉字中文值且不在 `KNOWN_DATA_DRIVERS` 白名单即报" | 中（需先建白名单） |
| **A7** | **同源验收扩负例** | `tools/verify_web_parity.py:34-48` 只有 11 个**正例**，零负例；`engine_runtime.py:126-129` 对 liuren/lingqi 的拒绝路径、`request.normalize_request` 的非法时间/缺键报错——**双通道一致性零断言** | 补 4 类负例（非法学科 / 非法时间 / 缺必需键 / lingqi 三步全零），并断言两侧错误文案同源 | ~35 行 |

## B 档 · 真值源收敛（把已有副本删掉，只留 core 一份）

| # | 位置 | 重复了什么 | 改为 |
|---|---|---|---|
| B1 | `disciplines/liuyao/scripts/engine_chart.py:327-330` | `sheng_wo`/`wo_sheng`/`ke_wo`/`wo_ke` 四张 dict，逐一字节复现 `core symbols.py:42/44` 的 `SHENG_CYCLE`/`KE_CYCLE` | `from yishu_core.symbols import SHENG_CYCLE, KE_CYCLE`（`SHENG_WO`/`KE_WO` 已存在于 `core symbols.py:413-414`，零新增表） |
| B2 | `disciplines/liuyao/scripts/trigram_symbolism.py:55,62,68` | `ELEMENT_ORDER`(`:55`) + `sheng_map`/`ke_map`(`:62/:68`)，同上 | 走 core |
| B3 | `disciplines/ming/scripts/pattern.py:738,739,781,782` | **四个**干支串字面量（`dayun_table`/`liunian_table` 各一份） | `from yishu_core.ganzhi_calendar import HEAVENLY_STEMS, EARTHLY_BRANCHES` |
| B4 | `disciplines/meihua/scripts/chart.py:327` | `stems = "甲乙丙丁…"`，而**同一函数 `:328` 已经在用 core 的 `EARTHLY_BRANCHES`** ← 最危险的一处（半复制） | 删 `:327`，`:328` 的 core 引用提前 |
| B5 | `disciplines/liuyao/scripts/{case_runner.py:44-46, evaluate.py:51, liuyao_timing.py:41}` | 5 处干支串（含拼正则的 `_MONTH_RE`/`_DAY_RE`） | 走 core（正则用 `f"[{EARTHLY_BRANCHES}]"` 拼） |
| B6 | `disciplines/liuyao/dev_tools/{build_yingqi_set.py:38-39, feedback_store.py:35, fetch_huozhulin_cases.py:48-49, fetch_wikisource_cases.py:53-54}` + `liuren/dev_tools/build_course_cases.py:31,38` + `ming/dev_tools/{build_tiaohou.py:25, build_tiaohou_cases.py:62}` | dev_tools 层 8 处干支串 | 走 core（一次性构建器，顺手改，成本极低） |
| B7 | `disciplines/zeji/scripts/analyze.py:37-40` | 手写 `_BRANCH_CLASH` 六冲表，与 `core symbols.py:46 CHONG_PAIRS` 同源但第二份 | 从 `CHONG_PAIRS` 派生 |
| B8 | `disciplines/{liuyao,meihua,xiaoliuren,zeji}/scripts/analyze.py` | `_load_verdicts` **四份**各读各的 `data/verdicts.json` | core 或 synthesis 一个 `load_verdicts()` |
| B9 | `tools/report_faithfulness.py:38` / `tests/test_relations.py:14` | 又两份干支串 | 走 core（tools 可用 `yishu_core`） |

## C 档 · 断语 / 引文外置（落实 AGENTS §三「代码只留算法」）

| # | 位置 | 内容 | 搬去哪 |
|---|---|---|---|
| C1 | `disciplines/meihua/scripts/analyze.py:335` | `{"旺":0.5,"相":0.2,"休":0.0,"囚":-0.2,"死":-0.5}` 函数级评分权重 | `data/verdicts.json` |
| C2 | `disciplines/meihua/scripts/analyze.py:341-349` | 5 条 tone 断语（"体用相济，又有生扶之卦，事势顺畅"…） | `data/verdicts.json` |
| C3 | `disciplines/zeji/scripts/analyze.py:145-149` | 3 条黄道/黑道断语 | `data/verdicts.json` |
| C4 | `disciplines/xiaoliuren/scripts/analyze.py:202-204` | 3 条（"事势偏顺，宫义为吉"…） | `data/verdicts.json` |
| C5 | `disciplines/ziwei/scripts/analyze.py:140-142` | 2 条带括注的平断语 | `data/verdicts.json` |
| C6 | `disciplines/ming/scripts/analyze.py:65` | "仅条件识别，未作定论；需人工复核" | `data/verdicts.json` |
| C7 | `disciplines/lingqi/scripts/analyze.py:27,50-51` | 2 条方法论说明 | `data/ketables.json` 元信息段 |
| C8 | `disciplines/liuyao/scripts/liuyao_narrate.py:692-711` | 15 条格局→断语 mapping（"六合卦"/"近病逢合"/"久病逢空"…） | `data/rules/verdict_texts.json`（已存在 + `text_keys_selftest.py` 已有键校验基础设施） |
| C9 | `disciplines/liuyao/scripts/liuyao_step3.py:573-585` | `say` 字典 11 条口语断语（"极旺"/"偏弱"/"休囚"…） | 同上 |

> 最刺眼的一处：`disciplines/meihua/scripts/analyze.py:2` 的模块 docstring 白纸黑字写
> 「断语只取 `data/verdicts.json`」，而 `:341-349` 的 tone 表就在同一个文件里硬编码。

## D 档 · 契约与书源（口径诚实）

| # | 项 | 说明 |
|---|---|---|
| D1 | `docs/CONTRACT.md:63` 要求 `references/` 为学科目录必备，但 **ziwei / liuren / lingqi 三科不存在**（实测现存 5 科：liuyao/meihua/ming/xiaoliuren/zeji） | 三选一：建最小 `references/api_spec.md`，或把契约改成"五科以上必需"+ 登记制 |
| D2 | 梅花引文**可回指**（已复核） | `analyze.py:231` 的「《卷二·体用总诀》」→ 原文 `meihua_yishu_卷二.wikitext.txt:29 === 體用總訣 ===`，且 `:34` 逐字有「體克用，諸事吉；用克體，諸事凶。」；代码用的是简体转写，**字面对应成立**。只需在 `disciplines/meihua/references/` 补一份**繁简篇目对照表**（`體用總訣 ⇄ 卷二§29`）把回指钉死，无需修引文 |
| D3 | `docs/CONTRACT.md` 补两条硬条目 | ① `tools/build_web.py:254 _assert_discipline_lists_consistent()` 的 fail-fast 与 `request.DISCIPLINES` 清单升级为 §四.6；② 双通道同源写入契约正文 |
| D4 | `lingqi` 明确免责 | 实测 `lingqi/scripts/*.py` **根本不 import core**（八科里唯一），查表即断、无干支历法运算。在 `SKILL.md` 显式写「本科不接内核、书源为唯一真值源」，避免后人误判为漏接 |
| D5 | `check_verdict_literals` 之外补一条书源回指门 | `data/verdicts.json` 的 `所本` 字符串必须在 `references/` 或 `data/sources/` 中至少命中一处 |

---

## 三、执行顺序建议（按「核心理念贴合度 × 成本」）

| 轮次 | 内容 | 你的判断 |
|---|---|---|
| **第 1 轮（建议立刻做）** | 减法 S1–S6（6 项，都是零引用，删了没风险）+ A1 文档警示 | ☐ |
| **第 2 轮（价值最高）** | 加法 A1 + A2（真值源门升级）+ B1–B5（顺手删掉 8 处运行时真副本） | ☐ |
| **第 3 轮** | 加法 A3 + A4 + A7（门扩覆盖 + 负例），减法 core 死符号（**须与 C 档配套**） | ☐ |
| **第 4 轮（最重）** | 加法 C1–C9（断语外置 9 科）+ A5 + A6 + D 档 | ☐ |

## 四、待你定的三个边界

1. **`tools/scratch/` 整目录删不删？** AGENTS §三 把它列为「一次性脚本的合规去处」，
   但里面的 17 个 `.py` 都是已用完的调试器 + 硬编码绝对路径的本地产物，且不入库。
   我的立场：**删**（目录保留，空的，供将来放新的一次性脚本）。
2. **`tools/eval.py` 挂门还是删？** 它算出的是跨科对齐分（tune/holdout 分别出分，
   是 §四"改引擎必跑 tune+holdout"的落地工具），但确实没有任何自动化调它。
   我的立场：**保留 + 在 check 里加一条 `--full` 才跑的分数快照**，而不是挂进快速门。
3. **`docs/DEEP-OPTIMIZE-PLAN.md`（1363 行）留不留？** 它是全仓最长的改造总纲，
   但 6 处 base 引用已作废。我的立场：**留 + 头部加过期警示**（不删长文档，检索价值还在）。
