# 八字 CHANGELOG

> **第三百三十六批（A2-B）瘦身**：本文件只留最近窗口。
> **第三百四十二批精简**：更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)，`CHANGELOG-ARCHIVE.md` 全文已删除；
> 下面历史条目若提到 ARCHIVE，一律按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 3 节标题已并入索引。
> **第四百零七批（治理·批号归位）**：本文件原 398/399/400/401 四批因与并行六爻的
> 399/400/401 撞号，按提交顺序归位为 **408/409/410/411**；原提交 `46d8bc1` 的提交信息
> 保留旧号作历史，不再改。跨文件引用一律按新号。

## 2026-11-02 第四百六十九批（六爻·六亲持世括注）：**共享件为 19 条断语立「据《…》今译」判据；八字无该册**

**性质**：共享门覆盖扩展（不改判据、不改分数）。

- 六爻 `shi_yao_interpretation` 19 条纹末裸署「（《火珠林·X章》）」而全库 0/19 逐字；
  统一改「（据《…》今译）」，[12] 增 `check_shi_yao_interp`（裸括注即红、标记 ≥19）。
- 八字无 `shi_yao_interpretation`，不受影响；两科全门与账台同批复跑。
- 详见 `liuyao/docs/CHANGELOG.md` 第四百六十九批（两探针、金标准归因、分数未动）。


## 2026-11-02 第四百六十八批（六爻·报告层引文分标）：**467 批的 quote_kind 落到 5 个渲染点；六爻侧改动，八字无同类引文库**

**性质**：输出口径修复（不改判读、不改评分）。

- 六爻报告层标题改「经典引文与今译」，`paraphrase` 词条加「（今译）」；
  `narrate_core` 的引文投影补回 `quote_kind`；`judgment_table.json` 27 条
  `overrides.line` 随 step5 插入 3 行同步 +3。
- 八字无 `quote_database`/同类 5 渲染点，不受影响；两科全门与账台同批复跑。
- 详见 `liuyao/docs/CHANGELOG.md` 第四百六十八批（管线实测、金标准措辞 7960→53e1）。


## 2026-11-02 第四百六十七批（六爻·[12] 引文库 quote_kind）：**共享件为六爻 49 条引文库立 verbatim/paraphrase 判据；八字同名文件结构不同，显式跳过**

**性质**：共享门覆盖扩展（不改判据、不改数据、不改读数）。

- 六爻 `data/verdicts.json#quote_database` 旧称「古籍出处」，全库实测仅 1/49 逐字；
  48 条今译 → 加 `quote_kind`，[12] 只对 `verbatim` 做逐字回验（须 `source_ref`）。
- 八字同名 `data/verdicts.json` 结构不同（无 `quote_database`）→ 按 `DISC.name` 跳过；
  两科 selftest 同跑夹具（1 正例 ＋ 5 负例）。
- 报告层「经典引文」标题的分标登记为第四百六十八批。详见
  `liuyao/docs/CHANGELOG.md` 第四百六十七批。


## 2026-11-02 第四百六十六批（八字·六神取象行号出处）：**`liushen_image` 声明「值只收逐字引文与行号」，实有两处 `取象` 是改写且无 `_src`；narrate 把改写句渲染成「（《千里命稿》 行）」**

**性质**：数据声明修正＋输出修复＋[12] 覆盖扩展（不改判读、不改读数）。

### 一、缺陷（§六.3：声明与实现分家）

- `bazi/data/liushen_image.json` 的 `_meta.口径①` 明写「值只收**逐字**引文与行号，
  不做改写（铁律二：引文可指回原文）」。
- 实际：`正官.取象` 是「与七杀对举」的注释、`偏正财.取象` 是「财为我克之物」的概述，
  **均无 `取象_src`**；`narrate` 对 `取象` 一律按引文渲染，`取象_src` 缺失时
  `split(":")[-1]` 为空 → 输出 `（《千里命稿》 行）`：空行号 + 改写句冒充引文。
- 同一文件的 `偏正财.注` 还写着「只取 L1264 能力句与 **L1258 构成句**照录」，
  但条目里根本没有 `构成` 字段，且真正的构成定义在 **L1257**（L1258 是示例行）。

### 二、数据修正

| 条目 | 改法 |
|---|---|
| `正官` | 删改写式 `取象`，其内容移入 `注`；补 `构成`＝「克我而与我异性者，是也。」＋`构成_src:1119`（逐字） |
| `偏正财` | 删改写式 `取象`，其内容并入 `注`；补 `构成`＝「我所克，而与我异性者。为正财。我所克。而与我同性者，为偏财。」＋`构成_src:1257` |
| `偏正财.注` | 「L1258 构成句」更正为「L1257 构成句」，并注明 L1258-L1260 为例证/形讹行、不引用 |

### 三、输出修复（narrate）

`shi_shen_actions` 的 `source` 有两种写法（`file:NNNN` 与 `file LNNNN 附近`）；
旧 `split(":")[-1]` 对后者返回整串，渲染成 `（《千里命稿》data/sources/… L1026 附近 行）`。
改为正则 `(?:L|:)(\d+)` 提取行号，两种写法都只输出数字。

### 四、门（[12] 扩展）

新增 `check_liushen_sources()`（仅八字册）：

- 每个非空 `能力/构成/取象/别名` 必须有 `<字段>_src`（`data/sources/<书>:<行>`）、
  行号在册、值落在该行；
- `shi_shen_actions` 每条 `source` 必须能解析行号，`actions` 每项落在该行 ±3 行邻域；
- 下限守卫：16 个引文字段、7 条作用枚举；0 条即红。

### 五、自证（§四.8）

- selftest 增 5 式：正例（取象+作用各一）、取象值无 `_src`、取象值不在所署行、
  作用项不在邻域、`source` 无行号，全部按预期。
- 真实探针三式：删 `伤官.能力_src` → `× …缺行号出处`；`偏正财.构成` 改「我所克者，财也。」
  → `× …不在所署行 …:1257`；`伤官.actions` 加「制杀」→ `× …actions 不在所署行 L1026 邻域`；
  三次 EXIT=**1**、逐字节还原。
- 真盘：16 字段、7 条目全符；四段管线 narrate 输出已无空行号/整串路径。
- 金标准：措辞 digest `e158d5cb8a92e005 → fd1a1b0b60e06104`，机械层零漂移
  （`golden.py capture` 已记入 drift log；旧新措辞不可比，属有意显示修复）。
- 引擎读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。


## 2026-11-02 第四百六十五批（八字·[12] 裁决引文书源回验）：**`verdicts.json` 自称「书源引文唯一真值源」，20 个 locator 与 4 条分支总则此前只有 1 个点被 [12] 回指；现逐条行锚/文件内核对**

**性质**：门覆盖面扩展（不改判据、不改数据判读、不改读数）。

### 一、缺陷

`data/verdicts.json` 的 `_meta` 写着「书源引文唯一真值源」，其中：

- 20 个字段带 `locator`（`data/sources/<书>:<行>`）：`滴天髓任注本` 7、`看命口诀` 2×2、
  `格局成败引文` 三命通会 3、`从格引文` 三命通会 2×3；
- 4 条分支总则声明了底本：`病药引文.thesis`→《神峰通考》，`化格引文.verse`（2 条）
  与 `从格引文.verse`→《滴天髓》原文卷。

但 [12] 的 `quote_in_data` 只回指 `病药引文.thesis` **一个点**（且只验「某处出现过」），
20 个 `locator` 从未被任何门读取。

### 二、先实测再挂门

- 20 个 locator 字段：**单行逐字命中 20/20**（保持标点，未折叠）。
- 4 条分支总则：**逐行命中 4/4**（未用跨行拼接，避免把相邻行误拼成「逐字」）。

### 三、改法

- 共享 [12] 新增 `check_verdicts_quotes()`（仅八字册；六爻另有同名 `data/verdicts.json`，
  结构不同 → 显式跳过）：
  - 递归扫描带 `locator` 的条目，核 `quote/full_quote/cond_quote/verse_quote` 是否
    落在该行；行号越界/底本不存在均判红；
  - 三条分支总则按 `_meta` 声明底本逐**行**核对（不跨行）。
- 下限守卫：locator 字段 ≥20、分支总则 ≥4；任一面 0 条即判红。
- **不接**：`格局成败引文` 的非三命通会条目出自《子平真诠》通行本，全书未入库
  （`_meta` 已披露「不标 offset」）；无底本可回指，不造假红。

### 四、自证（§四.8）

- selftest 增 5 式：locator 正例（行内命中）、行号错、行号越界、底本不存在、
  分支总则改字必红。
- 真实探针三式：任注「至理」改「至礼」→
  `× verdicts：$.滴天髓任注本.用神总法.quote 不在所署行 …:212`；看命口诀 locator
  5115→5114 → `× … .quote/.full_quote 不在所署行 …:5114`（两字段同时报）；
  病药 thesis「为贵」改「为贱」→ `× verdicts：病药引文.thesis 非书源逐字`；
  三次均 EXIT=**1**、原字节回填。
- 真盘读数：locator 20 字段、分支总则 4 条全符。
- 引擎读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。


## 2026-11-02 第四百六十四批（两科·剩余三处构建器 `--check` 接线）：**三份规则/语料数据各自声明「引文逐字对不上原文就不出表」，`--check` 却都不在质检门里；接线后改字即红**

**性质**：门接线（不改判据、不改数据、不改读数）。

### 一、缺陷

全仓带 `--check` 的脚本共 7 个（八字）＋4 个（六爻）。463 批接上了
`build_tiaohou.py --check`，其余**声明了自校验却没人跑**的还有三处：

| 科 | 脚本 | 产物 | 自述 |
|---|---|---|---|
| 八字 | `build_dts_corpus.py` | `data/ditian_sui.json` | 章节引文层按页范围重算，`--check` 比对 |
| 六爻 | `build_question_use_gods.py` | `data/rules/question_use_gods.json` | 「引文逐字对不上原文就不出表」（69 条） |
| 六爻 | `build_use_god_rules.py` | `data/rules/use_god_relations.json` | 同上（15 条） |

`fetch_siku_sanming.py --check` **不接**：它是联网抓取器（校验下载原件的完整性），
不是「入库数据 vs 底本重算」的判据；原件完整性由 [42] provenance 与 [43] 重算守。

### 二、改法

- 八字 [9]：追加 `build_dts_corpus.py --check`（与 `build_tiaohou.py --check` 同层）。
- 六爻 [12]：在规则注册表门之后追加两份规则数据的构建器 `--check`（门键仍为
  `rule_registry`，故 `--only rule_registry` 也能定向复验）。
- 两处都只跑现成 `--check`，不新增判据、不改数据。

### 三、自证（§四.8）

- 真实探针 A：`ditian_sui.json` 的「天干論」首句「甲」改「乙」→
  `[9] 滴天髓引文层重算 ×`，整体 EXIT=**1**；原字节回填。
- 真实探针 B：问题词典某族 `basis.citation`「父」改「母」→
  `引文复验：68/69 条仍逐字命中原文`＋`[12] 规则数据引文复验（问题词典）未通过`，
  EXIT=**1**；原字节回填（两处 `还原 True`）。
- 真盘读数：`ditian_sui.json` 与重算一致；问题词典 69/69、法则表 15/15 逐字命中。
- 引擎读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

### 四、账台连锁（同批）

治理表重生成后：bazi 软引用 3→4（新增 `build_dts_corpus.py`）、liuyao 软引用 0→2
（两份规则数据构建器）。`readout_ledger` 的 `tier一致性` 期望同步为
`硬0/0软2/4`，并在期望行登记本批（§六.2 改期望必须带批号）。


## 2026-11-02 第四百六十三批（八字·[9] 接上调候引文重算）：**`build_tiaohou.py` 自带「引文逐字／原文找不到就置空」两道自校验，`--check` 却从未进入质检门；接线后改一个字即红**

**性质**：门接线（不改判据、不改数据、不改读数）。

### 一、缺陷

`tiaohou_quotes.json` 的构建器 `build_tiaohou.py` 在两处声明了自校验：

1. `build_table()` 末尾（L463–470）：「任何 quote 必须能在原文中逐字找到，否则视为臆造，
   强制置空（宁缺勿滥）」——**构建时**有效；
2. `--check`：「不落盘，只比对已入库 data/tiaohou_quotes.json 是否与重算一致」——
   **可复现性**有效。

但 `bazi/dev_tools/check.py` 的 [9] 只跑 `sync_tiaohou_engine.py --check`（引擎表 vs data），
从未调用 `build_tiaohou.py --check`。于是「构建器有校验」成了**没跑过的声明**：
若有人手改 quote（或构建器逻辑漂移），质检门看不见。

### 二、改法

- [9] 在引擎表同步之后追加 `build_tiaohou.py --check`；不一致即判红并指明重建命令。
- 归入 [9]（「调候表同步」→读作「调候表/引文同源」），不新增门号：
  两者都是「静态层 ↔ data 层同源」，且构建器的 `--check` 就是现成的判据。

### 三、自证（§四.8）

- 真实探针：`tiaohou_quotes.json` 的 `1甲.quote`「初春」改「初秋」→
  `[9] 调候引文重算 ×`，明细逐格给出行键与新旧值：
  `$.tiaohou_quotes.json.1甲.quote: 值不同 '，初秋…' ≠ '，初春…'`；整体 EXIT=**1**；
  原字节回填（`还原逐字节一致：True`）。
- 真盘读数：`build_tiaohou.py --check` → `√ tiaohou_quotes.json 与重算一致（可复现）`；
  120 格（110 条非空 quote、10 格 N/A）逐格与底本重算一致。
- 引擎读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

### 四、账台连锁（同批）

[9] 开始消费 `build_tiaohou.py` 后，`governance_map.py` 重生成的
`bazi/docs/GOVERNANCE-MAP.json` 把它从 `run_by_check_py: false` 改为 `true`，
`referenced_not_blocking` 软引用 2→3；`readout_ledger` 的 `tier一致性` 期望同步
2→3，并在期望行登记「463 批 build_tiaohou 由 [9] 以 --check 消费」——**改期望必须带批号**，
禁止静默（§六.2）。


## 2026-11-02 第四百六十二批（两科·[12] 大运起例引文行锚）：**`dayun_quotes` 自称「与 corpus_line 那一行逐字一致」，而 [12] 只验「值在语料某处出现」；补行锚回验，行号错/改字即红**

**性质**：共享门覆盖扩展（不改判据、不改数据判读、不改读数）。

### 一、缺陷

`bazi/data/rules/dayun_quotes.json` 的 `_comment` 与 `_provenance.note` 都写着
「引文必须与 `corpus_line` 那一行逐字一致」。但 `check_rule_registry.py` 的
`quote_in_data` 只做两件事：路径可解析、值非空，且该值**在语料任意位置**出现过
（归一化后）——`corpus_line` 从未被任何门读取。声明比门宽，属 §六.3 的
「文档说的和代码做的不一致」。

### 二、改法（共享件，两科同享）

- `devkit/shared/check_rule_registry.py` 新增 `check_dayun_quotes()`：
  - `_provenance.source_file` 必须可解析（学科根／仓库根）；
  - 每个 `corpus_line`＋`quote` 条目：行号须为整数且在底本范围内；
  - 引文须落在**该行**（与 [14] 同归一化）。
  - 下限守卫：条目数 `<2` 或 `0` 条即判红（0 结果 ≠ 通过）。
- 主入口仅在该册存在时启用（八字有、六爻无 → 六爻跳过，不判红）；
  两科 `--selftest` 都跑夹具，故六爻侧也能证明判据有牙齿。
- `sync_devkit.py --write` 重生成两科副本（[37] 逐字节同源）。

### 三、自证（§四.8）

- selftest 增 4 类：正例（两行正确配对）不误伤；行号错（引文在下一行）必红；
  `corpus_line` 超出底本必红；0 条目必红；另加 `source_file` 不存在必红。
- 真实探针：`yang_male_yin_female` 行号 2608→2607 →
  `× 大运起例引文：… 引文不在所署行 L2607`，EXIT=**1**；`yin_male_yang_female`
  引文「乙丑」改「己丑」→ `× … 不在所署行 L2612`，EXIT=**1**；原字节回填
  （`还原逐字节一致：True`）。
- 真盘读数：2 条条目（L2608／L2612）行内逐字全符。
- 引擎读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。


## 2026-11-02 第四百六十一批（八字·[41] 再扩 observations/cross_source）：**观察集 14 个分段引文字段与交叉来源 24 条引文此前无门；「滴天髓」白文无标点、JSON 用 `**` 强调，须分段有序＋折叠标点**

**性质**：门覆盖面扩展＋一处数据声明收窄（不改判据、不改数据判读、不改读数）。

### 一、缺陷

460 批已把 `excluded[]`／`source_evidence[]` 接进 [41]，但仍有两类引文面在 `cases[]` 之外：

| 载体 | 字段 | 条数 | 省略写法 |
|---|---|---|---|
| `bazi_bing_yao_observations.json` | `observations[].source_quote`／`book_support` | 14 字段 | `……` |
| `bingyao_cross_source.json` | `cross_source_observations[].quote` | 24 条 | `……`／`…` |

且观察集 `_comment` 原写「字段一律书源逐字」——比事实宽：`source_bing`／`difference`
等是摘述。声明与门必须一致（§六.3）。

### 二、先实测再挂门

- 观察集：底本取 `extraction.source`；按省略号**分段**后 14/14 段序全符。
- 交叉来源：按 `source` 标签路由后，22/24 条全符；余 2 条（DTS-D1 次段、DTS-D3）
  的底本是**滴天髓白文（原文卷本身无标点）**，JSON 又用 `**` 强调 → 旧口径比不过。
  改用「折叠标点＋去 `*`」后 24/24 全符；带 `source_ref` 的 17 条行锚邻域也全部命中。

### 三、改法

- 新增 `segments_problem()`：每段须为底本连续子串，且**后段从前段终点之后**开始
  （防把两段拆开重排还称「逐字」）。
- `observation_problem()`：`source_quote`／`book_support` 两字段各自分段核对。
- `cross_problem()`：`source` 未登记判红；`source_ref` 额外三查——所指底本须与
  `source` 路由一致、行号在册、引文落在该行 ±2 行邻域。
- 下限守卫：`MIN_OBSERVATION_FIELDS=14`、`MIN_CROSS_QUOTES=24`；任一面 0 条即判红。
- 观察集 `_comment` 收窄为「引文类字段（source_quote／book_support）书源逐字，
  `……` 分段按序回原文（461 批起由 [41] 机械核对）；其余字段是摘述不是引文」。
- `check.py` 的 [41] 标题同步列出四面。
- **明确不接**：`findings[].evidence_quoted` 是带书名的**复合摘述**（含省略与跨书拼接），
  不是单一引文字段；把它当逐字引文会造出假红，故显式排除并记在此处。

### 四、自证（§四.8）

- selftest 增 9 式：分段有序命中（正例）、分段乱序（负例）、末段尾拼（负例）；
  `**` 强调不影响（正例）、乱序（负例）、来源未登记（负例）、`source_ref` 行号越界、
  `source_ref` 底本与来源不符、`source_ref` 邻域命中（正例）。全部通过（总计 37 件）。
- 真实探针：OBS01 引文「辛金坐未」改「辛金坐申」→
  `× …: OBS01.source_quote 第 1 段非书源逐字`，EXIT=**1**；ZW01 `source_ref` 改
  `#L99999` → `× …: ZW01 source_ref 行号越界 L99999`，EXIT=**1**；
  两份文件逐字节还原（`还原逐字节一致：True`）。
- 真盘读数：observations 14 字段／cross_source 24 条，全部通过。
- 引擎读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。


## 2026-11-02 第四百六十批（八字·[41] 引文面扩到 excluded/source_evidence）：**`cases[].source_quote` 之外的 7＋12 条「自称书源逐字」此前无门；先实测全符再挂门，模板包裹的行要用「保留正文」口径**

**性质**：门覆盖面扩展（不改判据、不改数据判读、不改读数）。

### 一、缺陷

[41] 的循环只认 `cases[]` 数组；[11] 又整目录跳过 `data/cases/`。于是同一批文件里
**另外两类明写书源引文的字段**长期无人核对：

| 载体 | 字段 | 条数 | 声明形式 |
|---|---|---|---|
| `bazi_cong_er_cases.json` / `bazi_hua_cases.json` | `excluded[].source_quote` | 1＋6 | `provenance.file`＋`line` |
| `bazi_fangju_adjudication.json` / `bazi_hehua_adjudication.json` | `source_evidence[].quote` | 6＋6 | `book`＋`corpus_line` |

裁决册的 `source_evidence` 尤其像「已锁定」：三件套齐全、行号具名，却没有任何门读它。

### 二、先实测再挂门（§四.8 的反向顺序）

- 12 条 `source_evidence`：`corpus_line` 所指行**单行逐字命中 12/12**。
- 7 条 `excluded`：`provenance.line` **不是引文行**——滴天髓 dz 本是「一格一行」的
  表格布局，CEX01 的 L5336 只有「辛丑」；引文正文在同文件内不远处。故 excluded 按
  **整文件**比对，line 只当定位坐标（与「行号即引文在处」的 source_evidence 分开）。
- **归一化是第一道坑**：旧 `norm` 把 `{{…}}` 整块当标记删掉，而滴天髓/穷通宝鉴
  wikitext 常用 `{{annotate|任氏曰：…}}` 包住整段——删块后该行变空，引文永远对不上。
  新面改用 `norm_plain`（只去 `{{ }}`/`|`/`''`/`==` 符号，保留正文）：7/7、12/12 全符。

### 三、改法

- [41] 新增 F/G 两面：`audit_surfaces()` 逐份案例 JSON 扫 `excluded[]` 与
  `source_evidence[]`；`excluded_problem()` 按 `provenance.file` 整文件比对；
  `evidence_problem()` 要求 `book` 已登记、`corpus_line` 为整数且在范围内、引文在该行。
- 下限守卫：`MIN_EXCLUDED=7`、`MIN_EVIDENCE=12`；任一面扫到 0 条即判红（0 结果 ≠ 通过）。
- `check.py` 的 [41] 标题同步写明「excluded/source_evidence 引文逐字」。

### 四、自证（§四.8）

- selftest 增 8 式：模板包裹的行内引文**仍能命中**（正例）、行内尾拼必红、行号越界必红、
  书源未登记必红；excluded 整文件命中（正例）、简繁一字之差必红、缺 provenance.file 必红、
  空引文必红。全部通过。
- 真实探针：CEX01 引文「戊」改「己」→ `× … CEX01 excluded 引文非书源逐字`，EXIT=**1**；
  fangju `corpus_line` 改 99999 → `× … source_evidence[0] 引文不在所署行 L99999`，
  EXIT=**1**；两份文件逐字节还原（`还原逐字节一致：True`，`git status` 无数据改动）。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

### 五、仍欠（下一批）

`observations[].source_quote`／`book_support`（7＋7，按 `……` 分段）与
`cross_source_observations[].quote`（24 条，含 `**` 标记与 `source_ref` 行锚）同样是
「自称书源逐字、却不在 `cases[]` 内」的引文面；本批已实测其 `plain` 口径下可回底本，
但尚未接门，留待下一批（§六.1，逐批具名）。


## 2026-11-02 第四百五十九批（八字·案例目录幽灵 tests 指针）：**四份案例/裁决文件写着「回验由 tests/…承担」而该测试从不存在；[41] 补扫 `data/cases/*.json` 的 tests 指针，首版锚点写错被负例当场抓到**

**性质**：数据声明修正＋[41] 覆盖扩展（不改判据、不改数据判读、不改读数）。

### 一、缺陷

459 批前的分工是：[11] 文档活引用**整目录跳过 `data/cases/`**（案例正文含书文，
把它当声明载体扫会造出假红）；[41] 只验 `source_quote` 是否回书源逐字。两边都不看
案例正文里的路径指针，于是四份文件的幽灵测试指针长期无人抓：

| 文件 | 旧说法 | 实况 |
|---|---|---|
| `bazi_bing_yao_observations.json` | 「`tests/test_bazi_bing_yao.py` 会直接判失败」 | bazi/tests 只有 smoke/regression |
| `bazi_fangju_adjudication.json` | 「`tests/test_bazi_fangju_adjudication.py` 已锁定…」 | 同上 |
| `bazi_hehua_adjudication.json` | 「回验由 `tests/test_bazi_hehua_adjudication.py` 锁定」 | 同上 |
| `bazi_external_cases.json` | 「`tests/test_bazi_strength_root_stage.py::…` 持续锁定」 | 同上 |

这正是 458 批在 `dayun_quotes` 抓到的同一类病（幽灵测试指针是 166/168 批两次实抓过的
高发病），只是这次载体落在 [11] 不扫、[41] 不验的案例目录。

### 二、改法

- [41] `check_case_quotes.py` 新增 E 面：`pointer_problems()` 逐行抓 `tests/*.py`，
  `_resolves()` 按学科根／仓库根／同名文件解析，不可达即判红；显式病史行
  （从未存在／全仓不存在／该文件不存在／该测试文件／全历史 0 命中／已随扁平化消失／
  从未重建／现已不存在／已不存在）豁免——与 [11] 的 458 批口径同源。
- **首版正则有 bug**：`(?:^|/)tests/…` 在整行 `finditer` 时，`tests/` 前面是空格
  （「回验由 tests/…」），两个锚点都不成立，**永不命中且无报错**；`--selftest` 的
  负例自证当场抓到（`× 负例未抓到`），改为 `(?<![A-Za-z0-9_.\\])tests/…`。若不先写
  负例，这个门会以「全绿」身份静默全盲——与 §四.8「全绿的新门先怀疑、再证明」同因。
- 四份数据文件的指针改为回指**真实存在的门**或明确的「人工复核」：
  - `bing_yao_observations`：该错误由人工复核（自动门只守 tests 指针可达性）；
  - `fangju` / `hehua` adjudication：「本文件 provenance/引文逐字由人工复核
    （旧 tests 指针从未存在，459 批更正）」；
  - `external_cases`：外集隔离由 `[13] check_case_isolation` 与 `[12] quote_in_code`
    持续锁定（这两个门确实存在且在跑）。
- `check.py` 的 [41] 标题同步写明「案例目录 tests 指针可达」。

### 三、自证（§四.8）

- selftest 增三式：幽灵指针必抓／显式病史行不误杀／**可达指针不误杀**
  （`tests/regression_test.py` 真在盘）。首版负例名为 `tests/test_ghost_459.py`，
  被 [11] 当成本文件里的活声明判红——按 §四.8 的约定改名为
  `tests/__no_such__ghost_459.py`（`__` 双下划线前缀）。
- 真实探针：往 `bazi_bing_yao_cases.json` 临时塞
  `回验由 tests/test_ghost_459_probe.py 承担` → `× …:77 tests 指针不可达 → …`，
  EXIT=**1**；原字节回填，`git diff` 为空（`还原逐字节一致：True`）。
- 真盘复核：13 份案例 JSON 全部 `all-clear`（0 条不可达指针）。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7：
  本轮只动声明文本与门覆盖面，不碰判读）。


## 2026-11-02 第四百五十八批（两科·幽灵 tests 指针）：**`dayun_quotes` 写“回验由 tests/…承担”而该文件从未存在，被同一句历史词遮罩；[11] 给 tests 指针加硬判，真实探针即红**

**性质**：数据声明修正＋共享门覆盖扩展（不改判据、不改数据判读、不改读数）。

### 一、缺陷

`bazi/data/rules/dayun_quotes.json` 的 `_comment` 写「回验由 `tests/test_bazi_rule_registry.py`
承担」，该文件在仓内**从未存在**（bazi/tests 只有 smoke/regression）。同一句还写着
「原记载的…已随…删除」等历史词，[11] 的 HISTORY 豁免按**整行**生效，把这条活指针
一起吞掉了——幽灵测试指针是 166/168 批两次实抓过高发病，这次换了载体再现。

### 二、改法

- 数据声明改为：「回验由 `dev_tools/check_rule_registry.py` 的 `quote_in_data`＋
  `corpus_files` 承担（458 批更正：旧注记所称的测试文件在仓内从未存在）」。
- [11] 新增 tests 指针硬判：`tests/` 下的 `.py` 指针必须可达；只有显式病史行
  （从未存在／全仓不存在／该文件不存在／全历史 0 命中／已随扁平化消失／从未重建／
  现已不存在）才豁免。普通历史词不再整行遮罩活 tests 指针。
- 共享件改 `devkit/shared/` 后 `sync_devkit.py --write` 重生成两科副本。

### 三、自证（§四.8）

- 真实探针：在 `dayun_quotes.json` 临时塞一行 `回验由 tests/test_probe_458.py 承担` →
  `× dayun_quotes.json:4 指向不存在的文件 → tests/test_probe_458.py`，EXIT=**1**；
  原字节回填（`restored True`）。
- selftest 增两式：历史词遮罩下的活 tests 指针必抓；显式病史行不误杀。两科 [11] 实扫
  794/821 条引用，0 条悬空。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百五十七批（两科·[12] 千金赋逐联书源回指）：**共享门的千金赋核对补上“联句↔src 行号”逐字对拍；八字侧无该册，仅跑合成负例、不判实数据**

**性质**：共享门覆盖扩展（不改判据、不改数据、不改读数）。

### 一、缺陷

`qianjin_fu_map.json` 的 `_meta.纪律` 声明「联句与 src 逐字从书源抄来」，但 [12]
（447 批扩统计块）从未核过联句与行号。该册仅六爻有，八字侧无实数据，但门是共享真源。

### 二、改法

- `check_qianjin_map()` 增逐联回指：`src` 必带行号（兼容 `L8`／`源L124`）、行号在底本
  范围内、联句在所指行 ±2 邻域逐字命中；失败逐条点名并汇总。
- selftest 增 2 负例（联句改坏／缺行号），合成夹具经 `src_lines` 注入，八字侧照跑。
- 六爻实数据首跑 **100/100 全符**（0 处改值）；共享真源改后 `sync_devkit.py --write`
  重生成两科副本，六爻 check.py 标题与治理 guards 同批补「逐联书源回指」。

### 三、自证（§四.8）

- 六爻真实探针：首联改坏 → `联句与底本源L8 邻域不符`＋`逐联回指失败 1/100`，EXIT=1；
  原字节回填（`restored True`）。
- 两科 selftest 均通过（八字 25 条指针、六爻 88 条指针全可回指）。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百五十四批（八字·selftest 路径补真实数据面）：**`check_hidden_stems` 与 `[39] check_xiang` 的 `--selftest` 原提前 return，藏干书证对账与禁评分在全量流程里从未执行；真实探针即红**

**性质**：门自身路径覆盖修复（不改判据、不改数据、不改读数）。

### 一、缺陷

`bazi/dev_tools/check.py` 对两道门只以 `--selftest` 调用，而它们的 `--selftest` 分支
跑完负例就 `return`：

- `check_hidden_stems`：真实「书有而表无」对账与「0 支可核」守卫只在主入口执行；
- `check_xiang`（[39]）：③ 禁评分（评分侧不得读 `xiang`）与男女两份真实象层检查只在主入口执行。

两处因此都是全量流程里的盲区（§四.8 的同型）。上一批 453 修的是六爻侧，
本批把八字侧同型门一并收口。

### 二、改法

- `check_hidden_stems`：负例通过后**继续跑真实数据面**（删 `return 0`）。
- `check_xiang`：`--selftest` 先取 `selftest()` 返回码，失败即红；通过后继续跑真实三项。
- 两处 docstring 记明 454 批的路径覆盖事实。

### 三、自证（§四.8）

- 真实探针：把内核 `CANG_GAN["寅"]` 临时改为 `['丙','戊']`（删「甲」）后跑
  `check_hidden_stems.py --selftest` → `书有而表无：寅 中 甲`＋`FAIL：1 项`，EXIT=**1**；
  原字节回填（`restored True`）。修复前该路径只会 SELFTEST OK 后返回 0。
- `check_xiang --selftest` 现在同时打印真实盘面（宫位 4/4、脏腑五行 5/5）与分流/禁评分结论。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百五十三批（两科·selftest 路径补 0 结果守卫）：**[29] 正则展平门的 `--selftest` 此前不判“扫到 0 文件”；抽 `audit_scan` 主入口与自证共用**

**性质**：共享门自身 0 结果守卫修复（不改判据、不改数据、不改读数）。

### 一、缺陷

`check.py` 对 [29] 只跑 `--selftest`，而 `cmd_selftest` 只对**实数据**判违规，不判
「扫到多少文件」——`scripts/` 路径挪动/空目录时 `n=0、bad=[]` 照样全绿。
MIN_FILES=40 的守卫只写在主入口，等于在全量流程里从未生效（§四.8）。

### 二、改法（共享件，两科同享）

- 抽出 `audit_scan(bad, n)`：`n < MIN_FILES` 与违规都判红；主入口与 `--selftest` 共用。
- selftest 增负例 `audit_scan([], 0)` 必须非空；实扫结果也经同一判据。
- 共享真源改后 `sync_devkit.py --write` 重生成两科副本。

### 三、自证

- 两科 `--selftest`：八字实扫 89 文件、六爻 172 文件，违规 0；0 文件负例被抓。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百五十一批（两科·AGENTS 回改）：**规程正文对 [42] 的描述仍写“只核四项”；同批按 442–445 实际扩面改写，根级文档闸复验**

**性质**：项目级规程文档同步（§六.2；不改判据、不改数据、不改读数）。

### 一、缺陷

`AGENTS.md` §二「门禁内核真源」把 [42] 写成「provenance 的 sha256/bytes/chars/lines
须与在盘底本逐项相符」——这是**规程正文**，比 README/治理图更权威；442–445 已把
双口径行数、三项扩展统计、三项登记元数据与台账两列接进门，规程却仍按旧口径读。

### 二、改法

- 同段改写为：基础四项＋扩展统计（`ganzhi_pairs/tables/headings`）＋登记元数据
  （`page_count/eol_on_disk/sha256_lf_text`）＋已登记双口径行数，台账表（含干支对/标题
  两列）同源；并注明「442–445 批逐轮扩面，定义均由全仓登记值逐格复算反推」。
- 首跑事故记录（火珠林 CRLF→LF、两份旧册缺 source_file）保留，不改史。

### 三、自证

- `check_root_docs.py`：根级 7 份文档、路径引用仍 0 条悬空；`check_docs_index.py` 51 份
  文档完整。本批只改散文，未新增/删除文档，无需登记新行。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变（§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百五十批（两科·[42] 描述回改）：**四处登记仍写“只核 sha256/bytes/chars/lines”，与 442–445 的四轮扩面脱节；check 标题＋两科治理 JSON 同批改准**

**性质**：登记同步（§六.2；不改判据、不改数据、不改读数）。

### 一、缺陷

[42] 自 433 批只核四项基础统计；442–445 先后补了双口径行数、三项扩展统计
（`ganzhi_pairs/tables/headings`）、三项登记元数据（`page_count/eol_on_disk/sha256_lf_text`）
与台账表两列。但四处**对外描述**没跟着改：两科 `check.py` 的 [42] 标题、
两科 `GOVERNANCE-MAP.json` 的 `guards` 仍写「provenance 的 sha256/bytes/chars/lines
须与在盘底本逐项相等」——按它读，会以为扩展统计与元数据仍无人核（假事实，§六.3）。

### 二、改法（5 个文件，均只改描述）

- 两科 `check.py` [42] 标题改为「基础统计＋扩展统计＋元数据＋双口径行数须与在盘底本
  逐项相等；台账表同源；433 批新增，442–445 批扩」。
- `governance_map.py` 两科 CURATED 的 `check_source_provenance` 同口径改写，
  重生成两科 `GOVERNANCE-MAP.json`（各仅该行 guards 变化）。
- 治理计数不变：bazi 48／blocking 30；liuyao 71／33。

### 三、自证

- `git diff --stat`：5 文件各 1–2 行改写；两科治理 JSON diff 仅
  `check_source_provenance` 的 guards 一行。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变
  （只改描述，读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十九批（八字·登记回改）：**[41] 扩了豁免册自洽，`check.py` 标题与治理地图描述同批回改，治理 JSON 重生成**

**性质**：登记同步（§六.2「改实现必须回头改登记」；不改判据、不改数据、不改读数）。

### 一、缺陷

446 批给 [41] 增加了「豁免册自洽（`case_names⊆ids`／未披露 id／空专名列表）」，但
`bazi/dev_tools/check.py` 的 [41] 标题仍只写「source_quote 逐字；不可路由/夹注段逐条
披露」，`docs/GOVERNANCE-MAP.json` 的 `guards` 同旧——登记与实现分家即假事实（§六.2）。

### 二、改法

- [41] 标题补「豁免册自洽；446 批扩」。
- `governance_map.py` 的 bazi CURATED 同句改写（生成器在六爻侧，两科 JSON 同批重落）：
  `bazi/docs/GOVERNANCE-MAP.json` 仅 `check_case_quotes` 的 guards 一行变化；
  六爻侧 JSON 零 diff。
- 治理计数不变：bazi 48 脚本／blocking 30；liuyao 71／33；tier 链接违例仍为
  「bazi 两条存在性引用合法入账」。

### 三、自证

- `git diff --stat`：3 个文件各 1 行改写（check.py／governance_map.py／GOVERNANCE-MAP.json）。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变
  （只改登记文案，读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；账台 44/44 bad=0；
`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十七批（两科·[12] 自证吞错修复）：**`--selftest` 失败消息原被截掉、以 EXIT=0 溜过；本批改为保留并判红，探针证明「坏仪器 rc=1／好仪器 rc=0」**

**性质**：共享门自身故障修复（不改引擎、不改案例、不改读数；千金赋对照仅六爻有册）。

### 一、缺陷（负例自证失败会被静默吞掉）

`check_rule_registry.py` 的 `--selftest` 分支原文是：

```
problems = problems[:before] if len(problems) > before else problems
```

`selftest()` 只在**自证失败**时向 `problems` 追加消息；这一行却把「新增的失败消息」
连同计数一起截掉，于是「负例没抓到」也以 EXIT=0 通过——门自己证明自己失灵，但门说绿。
这正是 §四.8「全绿的新门先怀疑、再证明」要防的形态。

### 二、改法（两科同享）

- 删除截断行；改为打印「异常：N 条自证失败（保留并判红）」，失败消息随 `problems`
  走正常判红出口。
- 探针：把 `check_qianjin_map` 临时换成恒返回 `(0,0)` 的坏仪器 →
  `[selftest] 异常：5 条自证失败`、rc=**1**；恢复后 rc=**0**（同一进程内验证）。
- 千金赋映射检查（六爻专册）在八字侧因无文件而跳过，不判红。

### 三、读数

- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变
  （只修门自身，读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十六批（八字·[41] 豁免册自洽）：**`case_names` 不得指向册外 id、豁免 id 必须显式披露；斜杠简写披露按人体写法解析，负例自证 12→17**

**性质**：案例门自身登记面补强（不改引擎、不改案例、不改案例引文、不改读数）。

### 一、缺陷（豁免册能「登记了却永远不核」）

`case_quote_exempt.json` 的 `case_names` 只对 `ids` 里的案例执行核对。若出现
「`case_names` 有、`ids` 没有」的 key，那组专名**永远不会被比对**（静默死登记）；
反过来，`ids` 中没有专名、也没有在 `_case_names_note` 说明的项，等于「不机械判」
没有记录。两者都不影响既有读数，但会让「逐条披露」变成半真声明（§六.2）。

### 二、首跑实测与口径修正（没有为过门改数据）

新判据首跑即报「4 个 id 未披露：ZP004/ZP005/ZP031/ZP032」，复核后确认**是解析口径错**：
原注写的是 `ZP003/004/005/031/032 无专名`，斜杠简写只解析出第一个。门改为
「前缀字母 + 首号 + 后续 `/ddd` 展开」，与人的写法一致；不为过门把注记改成五个全写。
修正后实数据 **0 条**（12 个 ids：5 个有专名、7 个在注记中披露）。

### 三、改法

- 新增 `audit_exempt_ledger(exempt)`：
  ① `case_names` 的 key 必须 ⊆ `ids`；
  ② `ids` 中无专名的项必须在 `_case_names_note` 出现（含斜杠简写）；
  ③ 专名值必须是非空字符串列表。
- `check_all` 开跑先调用它；失败与引文逐字失败同一出口（EXIT≠0）。
- selftest 增 5 件（正例含简写展开＋死 key／未披露／空列表三个负例＋简写正例），
  总数 12→**17**；输出摘要列明「豁免册自洽×5」。

### 四、自证（§四.8，真实数据探针即红）

- `case_names` 塞入册外 `ZP099` → `× ZP099 不在 ids 中——该组专名永远不会被核对`，EXIT=1；
- `ids` 塞入未披露 `ZP900` → `× 1 个豁免 id 既无专名登记、也未在 _case_names_note 披露`，
  同时触发既有「册内 id 在案例集找不到」判红，EXIT=1；
  两处均按原字节回填（`restored`）。
- 实数据复跑：豁免 12 条逐条披露、直检 0 条；读数 tune 100.0（n=61）、
  holdout 100.0（n=279）、外部 69 例逐位不变（只补门，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十五批（两科·[42] 台账统计列）：**六爻台账「干支对／标题」两列首次逐格复算（8 格全符）；共享门 docstring 误引六爻专有路径被八字 [11] 当场抓到**

**性质**：共享门覆盖扩展＋文档串修正（不改引擎、不改案例、不改台账任何数值、不改读数）。

### 一、缺陷（台账是 provenance 的第二份抄本，两列仍无人核）

`liuyao/references/source_ledger.md` 的「在库书源」表除字节/哈希/行数外，还有
「干支对」「标题」两列——435 批接入 [42] 时只核了前三项，这两列仍是**第二份抄本
没人对**。443 批已把 `ganzhi_pairs／headings` 的定义用 36/36 实测固定，正好可以
拿来核台账。

### 二、实测与改法（0 处改值）

- 数值格逐格复算：增刪卜易 352/54、黄金策 0/33、火珠林 65/84、卜筮正宗 3/2，
  **8 格全符**；《易冒》《易隐》两行「未测」是合法占位，跳过。
- `audit_ledger` 返回新增「已核统计格数」；数值格少于 8 即判红（防整列被改成占位
  而门空转）。输出行加「（干支对/标题 8 格）」。
- selftest 增 3 件：干支对失配、标题失配、未测占位跳过；总数 27→**30**。
- 共享真源改后 `sync_devkit.py --write` 重生成两科副本。

### 三、自证（§四.8，真实数据探针即红）

- 台账 352→353 → `× 干支对 353 ≠ 在盘 352`，EXIT=1；
- 台账 54→55 → `× 标题 55 ≠ 在盘 54`，EXIT=1；两处均按原字节回填（`restored`）。
- **首轮全量门即抓到一处本批自造的缺陷**：docstring 写 `references/source_ledger.md`
  （该表只在六爻有），八字副本按活引用解析必红（[11]）。改正为裸文件名
  `source_ledger.md`（无 `/` 不构成路径声明）后，两科 [11] 均 0 条。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变
  （只扩门，读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十四批（两科·[42] 登记元数据）：**`page_count↔pages`、`eol_on_disk`、`sha256_lf_text` 三类声明首次机械复算；实测 36/3/1 份全符，三处真实探针即红**

**性质**：共享门覆盖扩展（不改引擎、不改案例、不改任何登记值、不改读数）。

### 一、缺陷（声明的元数据没有一项被复算）

provenance 顶层还有三类可机械验证的声明：

- `page_count` 与 `pages` 列表（36 份）——两者是否一致从未核对；
- `eol_on_disk`（3 份）——声明在盘是 LF 还是 CRLF。这正是 433 批
  `huozhulin` 事故的形态（CRLF 版被规范成 LF 后登记未重测），事故处理了，哨却没设；
- `sha256_lf_text`（1 份，`zengshan_buyi`）——声明「把 CRLF 折成 LF 后」的哈希，
  与在盘原始字节哈希并列保存，此前无人复算后者。

### 二、定义与全量实测（先验证、后入册，0 处改值）

| 字段 | 机械定义 | 实测 |
|---|---|---|
| `page_count` | 等于 `len(pages)` | **36/36** |
| `eol_on_disk` | 原始字节：全 LF→"LF"、全 CRLF→"CRLF"、兼有→"mixed"、无换行→"none" | **3/3** |
| `sha256_lf_text` | `sha256(raw.replace(b"\r\n", b"\n"))`（按原始字节折行，不经解码） | **1/1** |

三项 0 处改值、0 处变空；本轮不改任何 provenance 登记值。

### 三、改法

- `_eol(raw)` 新增在盘换行形态判定；`measure()` 增算 `eol`、`sha256_lf_text`；
  `audit()` 仅对**已登记**的三类元数据逐项比对，未登记不强制补。
- 输出行加「元数据 N 项」（八字 23：22 份 page_count＋1 份 eol）。
- selftest 增 4 件（三类正例＋各一负例），总数 23→**27**。
- 自测中实踩并修掉一个夹具缺陷：Windows 文本模式 `write_text` 会把 `\n` 写成 `\r\n`，
  使「在盘 LF」正例恒红；夹具改用 `write_bytes`（并同步 `tamper`），eol 判据才可测。
- 共享真源改后 `sync_devkit.py --write` 重生成两科副本。

### 四、自证（§四.8，真实数据探针逐项即红）

- `eol_on_disk`：增删卜易 CRLF→LF → `× eol_on_disk 登记 LF ≠ 在盘 CRLF`，EXIT=1；
- `sha256_lf_text`：`897f963b…`→全 0 → `× sha256_lf_text 失配`，EXIT=1；
- `page_count`：黄金策 1→2 → `× page_count 2 ≠ pages 长度 1`，EXIT=1；
  三处均按原字节回填并复验（`all restored`）。
- 全量复跑：bazi 元数据 23 项、六爻 17 项**全符**；selftest 27 件全过。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变
  （只扩门不触判据，读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十三批（两科·[42] 扩展统计）：**`ganzhi_pairs／tables／headings` 三项经 36/36 逐格复算各得唯一定义并纳入门；provenance 注记「统计由 [42] 核对」由半真变字面事实**

**性质**：共享门覆盖扩展（不改引擎、不改案例、不改任何登记值、不改读数）。

### 一、缺陷（注记说「统计由 [42] 核对」，门只核了 4 项）

29 份 provenance 的 note 写着「字节/统计由 [42] 核对」，但 [42] 自 433 批起只核
`sha256/bytes/chars/lines`，模块 docstring 还明文写着「不核
`stats.ganzhi_pairs／tables／headings`：抽取口径散在历史脚本里、没有单一可复算定义」。
442 批补上双口径行数后，这三项仍是**登记了却无人复算**的字段——「统计」二字对读者
是半真声明（§六.3）。

### 二、定义不是猜的：候选口径逐格重算，36/36 命中

对全仓 39 份 provenance 中**登记了该字段**的 36 份逐文件重算，试了多组候选口径：

| 字段 | 采用的机械定义 | 命中 |
|---|---|---|
| `ganzhi_pairs` | `re.findall("[十干][十二支]", text)`：相邻一字干＋一字支（**不要求六十甲子配对合法**） | **36/36** |
| `tables` | `text.count("{|")`：维基表格开标签数 | **36/36** |
| `headings` | 行首为 `=` 的行数（维基标题行；dz 本无此形态，登记值均为 0） | **36/36** |

对照证据：同法按「合法六十甲子配对」计数只有 **8/36** 相符（如 qiong-tong 77 vs 76、
sanming 18339 vs 17752）——故历史口径确为**全组合相邻**，不是合法配对。三项 0 处改值、
0 处变空；本轮**未改任何 provenance 登记值**，只把既有定义固定进 `measure()`。

### 三、改法

- `measure()` 增算三项扩展统计；`audit()` 仅对**已登记**字段逐项比对，未登记不强制补
  （《三命通会》四库本、两份 wikitext 原始件本就没有这三项）。
- 输出行拆开报「69 项基础统计、扩展 66 项、双口径 2 项」（六爻 48／42）。
- selftest 增 4 件：三项正例、`ganzhi_pairs` 错、`tables` 按表格行数计（非 `{|`）、
  `headings` 未按行首 `=` 计；总数 19→**23**（provenance 16＋台账 7）。
- 模块 docstring 删除过时的「不核三项」段，改记 443 批定义与 36/36 实测依据（§六.2）。
- 共享真源改后 `sync_devkit.py --write` 重生成两科副本。

### 四、自证（§四.8，真实数据探针逐项即红）

- `ganzhi_pairs`：黄金策 40→41 → `× stats.ganzhi_pairs 41 ≠ 在盘 40`，EXIT=1；
- `headings`：皇极经世书 0→1 → `× stats.headings 1 ≠ 在盘 0`，EXIT=1；
- `tables`：穷通宝鉴 70→71 → `× stats.tables 71 ≠ 在盘 70`，EXIT=1；
  三处探针均按原字节回填并复验 `restored=True`。
- 全量复跑：bazi 66 项扩展、六爻 42 项扩展**全符**；selftest 23 件全过。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变
  （本批只扩门，读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十二批（两科·[42] 双口径行数）：**`lines_physical` 登记值首次被机械复算，抓到皇极经世书 provenance 多算一行（5496→5495）；可选双口径不强制补，负例自证 15→19**

**性质**：共享门覆盖扩展＋provenance 登记值更正（不改引擎、不改案例、不改读数）。

### 一、缺陷（provenance 自带的两个行号口径字段，433 批的门从未核过）

`bazi/data/sources/huangji_jingshi_shu_dz.provenance.json` 在 2026-10-07 澄清时补登
`stats.lines_nonempty=5358 / stats.lines_physical=5496`，并写明后者「与 cat -n 行号口径
一致，供 dev_tools/check_source_readings.py 逐字核验使用」。但 [42] 自 433 批起只核
`sha256/bytes/chars/lines` 四项，这两个字段**登记了却无人复算**——书源被换行规范化时
`sha256` 会先报警，可登记值本身写错（如末尾换行多算一行）则四门全绿，逐字回验的
「源L」行号口径也就跟着整体错一行。

### 二、首跑实测（§四.8 真实数据负例）

扩判据后 bazi [42] 首跑**精确抓到 1 条**：

```
× huangji_jingshi_shu_dz.provenance.json：stats.lines_physical 5496 ≠ 在盘 5495
```

责任方判定（§二「数据缺陷 vs 引擎缺陷」）：在盘底本 313653 字节、sha256 与登记逐字相符，
换行符恰 5495 个且末尾带换行；`cat -n`／`text.splitlines()`／文件迭代器三种口径均为
**5495**。5496＝「换行符数 +1」的典型多算一行（该笔记却称与 cat -n 一致），故是
**登记值错**，不是底本错、更不是引擎读数。按实测把 `lines_physical` 更正为 5495，
并在 note 末尾追加 442 批更正说明（保留 2026-10-07 原记录，不覆写历史）；
`lines_nonempty` 5358 复算相符，书源字节与 sha256 未动。

### 三、改法

- `measure()` 增算 `lines_nonempty`（非空行，同 `lines` 定义）与 `lines_physical`
  （`len(text.splitlines())`，即 cat -n／迭代器口径，**不是**换行符数 +1）。
- `audit()` 对**已登记**的这两个字段复算比对；未登记的不强制补（保留历史登记形态，
  不为过门批量改数据）。输出行加「双口径 N 项」，0 项不打印。
- selftest 增 4 件：双口径正确（正例）、`lines_physical` 按换行符+1 多算一行（负例）、
  `lines_nonempty` 登记错（负例）、未登记不强制补（正例）；总数 15→**19**。
- 本器为 `devkit/shared/` 单一真源，改后 `sync_devkit.py --write` 重生成两科副本。

### 四、自证与读数

- bazi [42] 更正后 **0 条**（23 份 provenance、69 项统计、双口径 2 项全符）；
  六爻 [42] **0 条**（16 份 provenance、48 项统计；无科登记双口径，故不显示该项）。
- selftest 19 件全过（provenance 12＋台账 7）。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279，满分例数 278/279）、外部 69 例
  逐位不变——本批只动登记值与门，不触任何判据（读数不动属预期，§四.7）。

**全门复验**：两科 `check.py` 全过（[0]–[43]）；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十一批（两科·死链门补 `tools` 前缀）：**已删除的 `tools/` 路径首次纳入裸路径扫描；历史语境加显式豁免词、负例自证 3→4；顺改 `check_case_isolation` 过时头注**

**性质**：共享门覆盖扩展＋文档串修正（不改引擎、不改案例、不改读数）。

### 一、缺陷（440 只守住了 provenance 注记，扫描器仍漏 `tools/`）

`check_doc_refs` 的裸路径前缀集原本是
`docs|scripts|data|references|dev_tools|core|tests|bazi|liuyao`，**不含 `tools`**。
440 批把 provenance 的 note 清干净了，但 `.py`/`.md`/`.json` 里的活引用仍在门外观测区：
`dev_tools/check_case_isolation.py` 头注就写着「由 tools/case_isolation_check.py 机械守」，
而该目录早已随扁平化删除。

### 二、改法

- `BARE` 前缀集加入 `tools`（`(?<![\w/.-])` 仍保证不会把 `dev_tools/` 里的
  `tools` 误当前缀）。
- `HISTORY`（病历/历史语境豁免词）补 `历史上|旧写法|扁平化删除|原抓取|登记时点`，
  让明确标注为历史的旧路径不被当活引用；否则会逼人删掉事故记录（反向激励）。
- selftest 增加一条裸 `tools/zz_probe_deadref_tool.py`，负例下限 3→**4**。
- `check_case_isolation` 头注改正：原文说「没有任何东西在守它」——本器就是补上的门，
  改为「那段时间这句话是空话——本器就是补上的那道门」，并把旧脚本标注为已删除。

### 三、自证（§四.8）

- 首跑两科各精确抓到 1 条：
  `dev_tools/check_case_isolation.py:5 指向不存在的文件 → tools/case_isolation_check.py`；
  改正 + 历史豁免后两科均 **0 条**（检视 793/819 条引用）。
- selftest 4 条死引用全抓到；`dev_tools/` 现行路径不误伤。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变。

**全门复验**：两科 `check.py` 全过；账台全量 bad=0；两科 golden 零漂移；
根级四闸全过；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百四十批（两科·扁平化残留引用清理）：**29 份 provenance 的 `tools/crosscheck_source.py` 活指令、3 个六爻工具 docstring、`liushen_image.json` 的 `tools/eval.py` 全改为现行路径/人工对勘；[42] 增 note 守卫（`dev_tools/` 不误伤），探针即红**

**性质**：数据/meta 注记与文档串修正＋共享门扩展（不改引擎、不改案例、不改读数）。

### 一、缺陷（`tools/` 目录已删，活指令还在）

`check_doc_refs` 的路径前缀集只含 `docs|scripts|data|references|dev_tools|core|tests`，
**不含 `tools`**——于是扁平化删除的 `tools/` 活引用一直落在门的外观测区：
- **29 份 provenance**（bazi 17＋liuyao 12）的 note 写着「引用前须跑
  `tools/crosscheck_source.py` 对勘留痕」——该脚本已随扁平化删除，照着跑必然失败；
- `bazi/data/liushen_image.json` 的「禁入」仍写「不得进 `tools/eval.py` 的计分口径」，
  评分器现为 `eval/evaluate.py`；
- 六爻 3 个工具的 docstring 仍写 `python tools/<脚本>.py`（`build_question_use_gods`、
  `build_use_god_rules`、`use_god_coverage`），照抄命令跑不通。

### 二、改法

- 29 份 provenance 的句子改为「引用前须**人工**对勘留痕（原对勘脚本已随扁平化删除；
  字节/统计由 [42] 核对）」；`huangji_jingshi_shu_dz` 的长注里另两处
  `tools/check_source_readings.py` 改 `dev_tools/…`，旧读法文档路径显式标注
  「该目录已随扁平化删除」。
- `liushen_image.json`：`tools/eval.py` → `eval/evaluate.py`。
- 六爻 3 个 docstring：`python tools/…` → `python dev_tools/…`。
- 共享门 [42] 新增 note 守卫：provenance 的 `note` 里出现裸 `tools/`（先剔除
  `dev_tools/` 再判断）即判红；selftest 14→**15** 件（新增「note 指向已删除 tools/」）。
  这样同类残留会当场显形，不再靠人工读。

### 三、自证（§四.8）

- 门首跑真实抓到 `huangji_jingshi_shu_dz.provenance.json` 长注里残留的
  `tools/check_source_readings.py`（判红），改完转绿；`dev_tools/` 不误伤。
- **真实探针**：往 `mingli_tanyuan_dz.provenance.json` 的 note 里插入 `tools/x.py` →
  [42] 报 `note 仍指向已删除的 tools/ 路径`（EXIT=1）；按原字节恢复后转绿。
- 全量：两科 [42] 15 件自证全过；29 份 provenance 的 sha/字节/字数/非空行仍与在盘一致。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变。
- 插件重建：`liushen_image.json` 随 engine 打包，`build.mjs` 后引擎 151 文件逐字节一致、
  知识库 14 篇一致、DSH 宿主自检全过。

**全门复验**：两科 `check.py` 全过；账台全量 bad=0；两科 golden 零漂移；
根级四闸全过；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百三十九批（八字·四库本构建链）：**raw→dz 重算接进 [43]——meta 与 raw 逐项核对＋builder `--check`；raw 不在盘显式跳过；探针改 raw 即红**

**性质**：门禁新增＋文档口径改正（不改引擎、不改案例、不改读数）。

### 一、缺陷（四库本的最后一段构建链没人看）

433 批已把 `dz ↔ provenance` 接进 [42]，但 `raw 转写件 → dz 校订件` 没有常设检查：
`sanming_tonghui_siku.wikitext.txt` 是 `.gitignore` 的抓取件，`build_siku_dz.py`
只在外部三命通会会话里手动跑。若 raw 被替换而 dz/provenance 未重建，[42] 仍全绿，
案例引文继续指向旧 dz——这正是“底本换了、校订件没换”的静默盲区。

### 二、改法

- 八字 `dev_tools/check.py` 新增 **[43]**：
  - raw 不在盘（fresh clone／转写件未抓）：显式打印「本门未核，不冒充通过」，不判红；
  - raw 在盘：先核对 `sanming_tonghui_siku.meta.json` 的 `sha256`／`bytes`／`chars`
    与 raw 逐项相等，再跑 `build_siku_dz.py --check`（重算校订件并与在盘逐字节比对）。
- 顺带改正 `check.py` 顶部陈旧口径：原文写「tune n=60、holdout n=276」，
  实为 **61／279**（395 批《千里命稿》4 例入册后；368 批 278→276 是此前一步）。
- 治理/账台：`build_siku_dz` 由 [43] 以 `--check` 消费（`run_by_check_py=true`），
  账台 `tier一致性` 的合法软引用由 1 条登记为 **2 条**（build_siku_dz＋diff_tiaohou_vs_head）。

### 三、自证（§四.8）

- 全量：meta 与 raw 一致（**1467204 字节 / 538884 字**，sha `2d070238…`）；
  builder 重算与在盘校订件一致（**1419789 字节**，sha `47028eb5…`）。
- **真实探针**：往 raw 末尾追加 6 字节 → [43] 报
  `meta.sha256 … ≠ 在盘 …`、`meta.bytes 1467204 ≠ 1467210`、`meta.chars 538884 ≠ 538890`，
  且 builder `--check` 判不一致（EXIT=1）；按原字节恢复后 sha 复为 `2d070238…`，
  全量门转绿。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过（新增 [43]）；账台全量 bad=0；
`golden.py verify` 零漂移；根级四闸全过；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百三十七批（八字·豁免专名机械核对）：**5 条专名登记进豁免册并由 [41] 实测——专名一旦在底本出现即 `exempt_bad`；泛称/无专名项显式不机械判**

**性质**：门禁收紧＋登记补全（不改引擎、不改案例、不改读数）。

### 一、缺陷（436 只机械了四柱，人名这一半仍靠人工）

436 批把豁免项的**四柱**接进了 [41]，但豁免理由里的「案例名」仍是人工结论。
12 条中有 5 条带可用于机械对勘的专名（龙济光、江万平、石友三、朱古薇、张载阳）；
若底本后来补进同名案例而引文写法不同，旧门仍会继续判 `exempt`。

### 二、改法

- `case_quote_exempt.json` 新增 `case_names`（5 条专名）与 `_case_names_note`；
  `reason` 改为「已登记专名亦由 [41] 机械核对 0 命中」。
- [41] 豁免分支在四柱检查后，再查已登记专名（`FOLD` 折标点后同法比对两本底本）；
  命中任一 → `exempt_bad` 判红（「豁免项的人名「X」已在底本出现」）。
- **不机械判**：ZP015「某侍郎」、ZP016「某知府」是泛称，ZP003/004/005/031/032
  无专名——不把泛称当身份指纹（若强行登记，「侍郎/知府」会在别处命中，制造假红）。

### 三、自证（§四.8）

- selftest 由 10 件扩到 **12 件**：新增「登记专名也不在底本＝exempt」与
  「登记专名已在底本＝exempt_bad」两件（夹具专名取 `甲子乙丑`）。
- **真实探针**：把 ZP001 的登记专名临时改为「张都统」（子平底本 ZP021 案例中实有）→
  门报 `ZP001：豁免项的人名「张都统」已在底本出现——「不在库」理由不成立`
  （EXIT=1）；恢复为「龙济光」后转绿。
- 全量：5 条专名在两本底本实测 **0 命中**；12 条豁免仍全部 `exempt`，
  逐字 445／豁免 12／不可路由 7 不变。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过（[41] 12 件自证）；账台全量 bad=0；
`golden.py verify` 零漂移；根级四闸全过。


## 2026-11-02 第四百三十六批（八字·豁免四柱机械核对）：**豁免项「四柱不在底本」由 [41] 实测——四柱一旦回潮即 `exempt_bad` 判红；并修掉 `stale`/`exempt_bad` 的册内 id 误报**

**性质**：门禁收紧＋登记口径改正（不改引擎、不改案例、不改读数）。

### 一、缺陷（豁免理由有一半只写在纸上）

`case_quote_exempt.json` 的 12 条豁免理由写着「案例名与四柱在底本 0 命中」，但门 [41]
只核引文：引文不在底本就判 `exempt`，**四柱是否真的不在底本**从未被核对。
432 批打印的是「最长连续块」，也不覆盖四柱——若底本后来补进同一案例（引文写法不同、
整句仍不命中），豁免会继续绿。

### 二、改法

- 新增 `pillars_key(case)`：把 `year/month/day/hour` 连成串并**连标点一起折掉**
  （`FOLD`），避免底本顿号/逗号用法不同漏判。
- 豁免分支：主底本未命中引文后，再在两本底本里查四柱串；命中任一 →
  新状态 **`exempt_bad`** 判红（「豁免项的四柱已在底本出现——『不在库』理由不成立，
  请回接逐字」）。
- 顺带修：`stale` 与 `exempt_bad` 都登记进 `seen_exempt`——旧版只有 `exempt` 登记，
  导致豁免项一旦过期/回潮，末尾还会误报一条「豁免册里的 id 在案例集中找不到」。
- 豁免册 `reason`/`_comment` 改为「四柱由 [41] 机械核对 0 命中；案例名见 432 批人工复核」，
  不再把人工结论说成机械结论。

### 三、自证（§四.8）

- selftest 由 8 件扩到 **10 件**：新增「豁免项四柱也不在底本＝exempt」与
  「豁免项四柱已在底本＝exempt_bad」两件（夹具主底本含 `甲子乙丑丙寅丁卯`）。
- **真实探针**：把 ZP001 的四柱临时改成 ZP025 的四柱（辛丑／庚寅／甲辰／乙亥，
  该串在子平底本中）→ 门报
  `ZP001：豁免项的四柱「辛丑庚寅甲辰乙亥」已在底本出现…`（EXIT=1）；
  修复前同一次探针还并发一条 `豁免册里的 id 在案例集中找不到 ['ZP001']`，
  修复后只剩一条真判红。恢复后转绿。
- 全量：12 条豁免仍全部 `exempt`（四柱实测 0 命中），逐字 445／豁免 12／不可路由 7 不变。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过（[41] 10 件自证）；账台全量 bad=0；
`golden.py verify` 零漂移；根级四闸全过。


## 2026-11-02 第四百三十五批（八字·台账同源门）：**共享 [42] 扩到 `source_ledger` 表核对——八字无此表（0 行，显式跳过）；selftest 7→14，读数零变化**

**性质**：共享门禁扩展（不改引擎、不改数据、不改读数）。

### 一、背景

433 批新增的共享门 `check_source_provenance`（[42]）已核对 provenance ↔ 底本；
435 批把 `references/source_ledger.md` 的「在库书源」表也接进同一道门——它是
provenance 的第二份抄本，六爻侧 433 批刚实测有 4/6 行陈旧。八字科当前**没有**
`references/source_ledger.md`，故行数下限登记为 0，输出显式写「台账 —（无此表）」，
不冒充已核。

### 二、改法

- 共享件 `devkit/shared/check_source_provenance.py` 新增 `audit_ledger`（两科产物
  由 `sync_devkit.py --write` 重生成，手改被 [37] 判红）。
- 台账行数下限：bazi **0**、liuyao 6。
- selftest 由 7 件扩到 **14 件**（provenance 7＋台账 7）。

### 三、自证（§四.8）

- 全量：**23 份 provenance／23 份底本／69 项统计全部相符**；台账无此表（0 行，
  显式打印）。14 件 selftest 全过（含台账字节/行数/缺底本/缺 provenance/0 行/缺表）。
- 读数：tune **100.0**（n=61）、holdout **100.0**（n=279）、外部 69 例逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过（[42] 14 件自证）；账台全量 bad=0；
`golden.py verify` 零漂移；根级四闸全过；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百三十四批（八字·引文书源归属）：**《子平真诠评注》双底本不再拼成一串——只在《命理探原》命中即判 `wrongbook`；实测 0 条误挂，读数零变化**

**性质**：门禁收紧（不改引擎、不改案例、不改读数）。

### 一、缺陷（拼成串的双底本分不出「哪本书说的」）

430 批为《子平真诠评注》登记了第二底本《命理探原》，`verify_case` 把两本
`"\n".join` 后做子串判断——引文**只在命理探原**出现、dz 本根本没有时，也会记「逐字通过」。
433 批实测：36 条子平引文中 20 条只在主底本、4 条两本都有、**0 条只在第二底本**，
所以当前读数未混入误挂；但这条路由对未来的引文是**假绿通道**，且豁免项只在第二底本
命中时会被误判成「豁免过期」。

### 二、改法

- `load_corpus` 改为**逐本返回归一化文本**（不再拼接）；`verify_case` 分别判
  `hit`（任一本）与 `primary`（第一本＝主底本）。
- 非豁免项：`primary=False` 且 `hit=True` → 新状态 **wrongbook** 判红
  （「引文只在第二底本命中，所署《子平真诠评注》主底本不含——书源归属不成立」）。
- 豁免项：只有主底本命中才算 `stale`；仅第二底本命中仍按豁免披露（不冒充过期）。
- 豁免项的最长连续块改为取两本最大值，披露口径不变。
- `BOOK_SOURCES` 注释写明「第一项主底本必须命中；第二项只作对照」。

### 三、自证（§四.8）

- selftest 由 6 件扩到 **8 件**：新增「多底本命中主底本＝ok」与
  「只在第二底本命中＝wrongbook」两件（夹具在临时目录，主底本 `甲子乙丑`、
  第二底本含目标句）。
- **真实探针**：把 ZP009 的引文临时换成只在《命理探原》出现的
  「《五行大义》云：支干者，因五行而立之，昔轩辕之时，大挠之所制也」→
  门报 `ZP009：引文只在第二底本命中（mingli_tanyuan_dz.dz.txt）…书源归属不成立`
  （EXIT=1）；恢复后转绿。
- 全量：**464 条引文 / 逐字 445 / 豁免 12 / 不可路由 7**，`wrongbook` 0 条
  （实测 0 条误挂，读数不动属预期，§四.7）。
- 读数：tune 100.0（n=61）、holdout 100.0（n=279）、外部 69 例逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过；账台全量 bad=0；`golden.py verify` 零漂移；
根级四闸全过。


## 2026-11-02 第四百三十三批（八字·底本完整性门）：**三命通会四库本 provenance 补 `stats`（builder 同步产出）＋新共享门 [42] 核对 23 份底本；探针改坏哈希即红，读数零变化**

**性质**：门禁新增＋登记修正（不改引擎、不改案例、不改读数）。

### 一、缺陷（底本是所有逐字回验的根，却无门核对）

`data/sources/*.provenance.json` 的 note 普遍写着「sha256 与 stats 由对在盘文件实测得出，
可用于后续核对文件是否被改动」，但全仓没有任何门执行这句话。433 批首跑 23 份，
22 份四项全相符；唯一缺陷是 `sanming_tonghui_siku.provenance.json`：
它只有顶层 `bytes`/`chars`（由 `build_siku_dz.py` 写出），没有 `stats`、没有行数，
按「四项核对」口径缺一项，且 builder 重生成会一直缺。

### 二、改法

- `dev_tools/build_siku_dz.py` 产出 `stats`（bytes／chars／**非空行**），同批重生成
  provenance；校订件 `sanming_tonghui_siku.dz.txt` 字节未变（sha `47028eb5…`，
  `--check` 与重算一致）。
- 新增共享门 `devkit/shared/check_source_provenance.py`（`devkit/shared/` 第 12 个共享件；
  两科 `dev_tools/` 同名文件为产物，由 `sync_devkit.py --write` 分发，手改被 [37] 判红）。
- 两科 `dev_tools/check.py` 挂 **[42]**；下限：bazi 23 份、liuyao 16 份。
- 核对口径（四项均机械可复算）：`sha256`＝原始字节哈希、`bytes`＝原始字节数、
  `chars`＝UTF-8 解码后长度、`lines`＝**非空行数**（不是 `splitlines()`）。
  不核 `ganzhi_pairs／tables／headings`：抽取口径散在历史脚本里、无单一定义，
  本门显式写「不核」，不拿半定义判红（§六.5）。
- 治理同步：八字 scripts 47→48、blocking 29→30（六爻 69→70、31→32）；
  `readout_ledger` 的 governance 期望同步改为 (70/48, blk 32/30)。

### 三、自证（§四.8）

- 全量：**23 份 provenance／23 份底本／69 项统计全部相符**。
- 7 件 selftest 全过：正例／sha256 失配／底本追加一字节／缺 source_file／缺 sha256／
  `lines` 用含空行口径必被抓／0 份 provenance 必被抓。
- **真实探针**：把 `mingli_tanyuan_dz.provenance.json` 的 `sha256` 改为全 0 →
  [42] 报 `sha256 失配（登记 000000000000… ≠ 在盘 c245cca314d3…）`（EXIT=1）；
  恢复后转绿。
- 读数：tune **100.0**（n=61）、holdout **100.0**（n=279）、外部 69 例逐位不变
  （底本正文一字未改，只改登记值；§四.7：读数不动属预期）。

**全门复验**：`bazi/dev_tools/check.py` 全过（新增 [42]）；账台全量 bad=0；
`golden.py verify` 零漂移；根级四闸全过；`sync_devkit.py --check` 12 件逐字节一致。


## 2026-11-02 第四百三十二批（八字·豁免册收敛与实测披露）：**ZP025 底本只有句末一字之讹（「官」作「这」）——截到「乙亥」后逐字比对 444→445、豁免 13→12；余 12 条附最长连续块实测，确认为诚实下限**

**性质**：数据修正＋门禁披露增强（不改引擎、不改 expected、不改读数）。

### 一、缺陷（一条本可修的豁免被当成底本缺失）

431 批后余 13 条豁免。复核 ZP025 发现其段落**完整存在**于
`ziping_zhenquan_pingzhu_dz.dz.txt`，只差句末两字：底本作「合煞留**这也**」，
而引文写「合煞留**官也**」（「官」讹作「这」）。整句因此不可连续命中，
被当作「底本未含该段」登记豁免——这是把**底本讹字**误记成了**底本缺失**。

### 二、改法

- ZP025 `source_quote` 截到四柱末「乙亥」：前文「更有禄劫而官煞竞出，必取清方为贵格。
  如一平章命，辛丑、庚寅、甲辰、乙亥」在底本逐字连续；不在引文里照录讹字。
  `note` 同步披露底本原文作「合煞留这也」（「官」讹）、引文为何止于「乙亥」，
  不把截断伪装成原貌。`pillars`／`expected` 逐字段未动。
- `case_quote_exempt.json` 移除 ZP025（剩 12 条）；门下限 `MIN_ROUTED` 444→**445**。
- 余 12 条**逐条重核**（不沿用 431 的结论）：案例名（龙济光／江万平／石友三／
  朱古薇／张载阳／某侍郎／某知府）在两份底本（子平真诠评注 dz、命理探原）**0 命中**；
  四柱串 12/12 **0 命中**；引文与底本的最长连续块仅 5–16 字，且都是通用门径句，
  不含案例身份。故 12 条确属评注夹注未收，维持豁免即诚实下限。

### 三、门禁增强（豁免从「一句声明」变「实测数」）

门 [41] 对每条豁免现打印**最长连续块**（`difflib.SequenceMatcher` 实测，不只写
「不在库」）；`--selftest` 增加块测量自证（库内整句 16/16 字、库外句 2 字）。
432 批全量实测：

`ZP001 5/28、ZP002 7/31、ZP003 6/50、ZP004 5/29、ZP005 5/33、ZP006 5/42、
ZP007 5/49、ZP015 7/35、ZP016 6/59、ZP031 6/70、ZP032 9/60、ZP035 16/92`
（前为最长连续块字数，后为引文归一化长度）。数字会随底本更新而变化，**豁免是否成立
可见可核**，不再依赖本册自述。

### 四、自证（§四.8）

- 全量：**7 文件 464 条；逐字比对 445、豁免 12、不可路由 7**；下限 7/464/445 在位。
- **真实探针**：把 ZP025 改回旧引文（含「官」、且已不在豁免册）→ 门报
  `ZP025：引文非书源逐字子串` ＋ `逐字比对只到 444 条（基线 445）`（EXIT=1）；
  恢复截短引文后转绿。
- 豁免过期判据未变：若底本补入夹注段使整句命中，门仍判 `stale` 红。

### 五、读数

- 零漂移：`source_quote`／`note` 不参与评分；tune 100.0（n=61）、holdout 100.0（n=279）、
  外部 69 例强弱读数逐位不变（§四.7：本轮不触及任何计分格，读数不动属预期）。

**全门复验**：`bazi/dev_tools/check.py` 全过（[7] tune 100.0／holdout 100.0、
满分例数 61/61 与 278/279，[41] 全量+selftest）；账台全量 bad=0；`golden.py verify`
零漂移；根级四闸全过。


## 2026-11-02 第四百三十一批（八字·案例引文连续化）：**10 条《子平真诠评注》省略号摘录换成连续书源段落——豁免 23→13、逐字比对 434→444；探针改回摘录即红**

**性质**：数据修正（source_quote 连续化；不改引擎、不改 expected、不改读数）。

### 一、缺陷

430 批恢复的引文门把 23 条《子平真诠评注》案例夹注/跨段摘录登记为豁免。其中
**10 条**并非「底本没有」，而是引文用「……」把**同一段落内的非连续句子**拼在一起
（如 ZP009「化伤为财……如罗状元命……所以伤官生财……安得不为殿元乎」）——
底本段落完整存在，只是旧引文省略了中间文字，按「连续子串」不可命中。

### 二、改法（逐条回源取连续切片）

用归一化最小窗口在底本中定位同一段落，把 10 条 `source_quote` 换成**连续原文**
（写盘前逐条回验归一化后仍是底本子串，非人工拼接）：

- ZP009 罗状元（97 字）、ZP010 孛罗平章（81）、ZP011 蔡贵妃（63）、ZP013 秦龙图（49）、
  ZP018 金丞相（53）、ZP020 王少师（70）、ZP021 张都统（59）、ZP030 财旺生官（38）、
  ZP033/036 官格败/财格败定义（79/30）。
- 其余 13 条（龙济光、江万平、石友三、朱古薇等底本确无该段或跨段无法连续化）继续
  留在豁免册，逐条披露。
- `case_quote_exempt.json` 移除上述 10 个 id；门的下限 `MIN_ROUTED` 434→**444**。

### 三、自证（§四.8）

- 全量：**7 文件 464 条；逐字比对 444、豁免 13、不可路由 7**；下限 7/464/444 在位。
- **真实探针**：把 ZP009 改回旧省略号摘录（无豁免）→ 门报
  `ZP009：引文非书源逐字子串` ＋ `逐字比对只到 443 条（基线 444）`（EXIT=1）；
  恢复连续段落转绿。

### 四、读数

- 零漂移：`source_quote` 不参与评分；10 条的 `pillars`／`expected`／`ten_gods` 等
  逐字段未动，tune 100.0／holdout 100.0／外部强弱读数逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过（[41] 全量+selftest）；账台全量 bad=0；
`golden.py verify` 零漂移；根级四闸全过。


## 2026-11-02 第四百三十批（八字·案例引文逐字门恢复）：**扁平化删除的旧案例引文门以 `check_case_quotes.py` 恢复为门 [41]——464 条 source_quote 逐字对拍 434＋豁免 23＋不可路由披露 7；探针尾拼即红**

**性质**：门禁恢复＋登记改正（不改引擎、不改评分、不改读数）。

### 一、缺陷

扁平化（`e2c77ad`）删除了旧的案例引文门（原 `tools/` 路径与 `check.py [1k]`），
但 `bazi_external_cases.json` 的 `_provenance` 仍写着「案例引文逐字性机械门 …
上线」——登记成了假事实（§六.2）。与此同时，7 个案例文件的 **464 条
`source_quote`**（自称照录的书源句）没有任何常设门：改写、尾拼、跨段拼接都不会被拦。

### 二、改法

- 新增 `dev_tools/check_case_quotes.py`（门 [41]）：`source_quote` 归一化后必须是
  该书底本的**连续子串**；书源路由优先 `book`（BOOK_SOURCES），其次案例
  `provenance.file`；两条都没有的书进 UNROUTABLE_BOOKS，逐条披露、不静默。
- 新增 `data/rules/case_quote_exempt.json`：23 条《子平真诠评注》案例夹注/跨段摘录
  （dz 本未含该段，全库扫描 0 连续命中；旧门曾把整书列为不可路由，本册细化为逐条
  披露）。**豁免过期即红**：若某条后来能在底本连续命中，门会要求回接。
- 接进 `bazi/dev_tools/check.py` 为 **[41]**；`governance_map` 登记（八字 46→47
  脚本、blocking 28→29）；`readout_ledger` governance 期望同步 69/47·blk 31/29。
- 改正 `bazi_external_cases.json` 的 `_provenance` 旧路径声明为
  `bazi/dev_tools/check_case_quotes.py`（check.py [41]，430 批恢复）。

### 三、自证（§四.8）

- selftest 六件：书源逐字正例／尾拼负例／凭空句负例／豁免披露／豁免过期判红／
  不可路由披露——全过。
- 全量：**7 份案例文件、464 条引文；逐字比对 434、豁免 23、不可路由披露 7**
  （XF001–003／MY001–002／YP001–002，书源不在库）；下限守卫 7/464/434 全在位。
- **真实探针**：给 ZE001 的 source_quote 尾拼「；例：四柱」→ 门报
  `ZE001：引文非书源逐字子串` ＋ `逐字比对只到 433 条（基线 434）`（EXIT=1）；
  恢复后转绿。

### 四、读数

- 零漂移：本批只改 `_provenance` 登记文字与加门，案例 expected／引擎零改动；
  tune 100.0／holdout 100.0／外部 69 例强弱读数逐位不变。

**全门复验**：`bazi/dev_tools/check.py` 全过；`readout_ledger.py --quick` bad=0；
`golden.py verify` 零漂移；根级四闸全过。


## 2026-11-02 第四百二十四批（八字·自检修复）：**baselines `--selftest` 旧断言过期——395 批 QL001 入 tune 后 cong 已有期望，被误报「假多数类」；改为合成夹具负例＋真实 tune 存在性双向断言**

**性质**：自检修复（不改引擎、不改评分、不改读数）。

- 缺陷：`dev_tools/baselines.py --selftest` 第 3 项断言「tune 无 pattern/cong_ge 期望时
  两键必须 None」。395 批把 QL001（cong_ge）入 tune 后 `cong_majority=True`，该断言把
  **真实数据变化**读成「假来源」，器具全体检长期 FAIL（主门不跑 sweep，故未显形）。
- 改法：真源 `devkit/shared/variants/baselines.bazi.py` 抽出
  `_banks_from_rows(rows)`（build_banks 与 selftest 共用同一实现），再
  `sync_devkit.py --write` 分发（`dev_tools/baselines.py` 是产物，不手改）；selftest
  分两层——①合成的无二元维夹具必须给 None（保留原意）；②真实 tune 的 pattern 必须
  None、cong 期望存在性必须与键一致。
- 自证：`--selftest` 全过；`--split tune` 读数不变（61 例，tiaohou 60/60=100%、
  定答 18/60、月支条件众数 19/60）；器具全体检 **71/71 PASS、0 FAIL**。
- 全门复验：`bazi/dev_tools/check.py` 全过（引擎/评分零改动）；账台全量 bad=0。


## 2026-11-02 第四百二十批（八字·治理）：**expected 受控字段覆盖生存线（门 [40]）——419 批六爻事故的八字面复刻防护；7 个案例文件逐字段钉下限**

**性质**：门禁补建（不改引擎、不改语料、不改任何读数）。

### 一、为什么现在补

419 批在六爻侧抓到真实事故：403 批重建 dz 案例册时把 206／208 批逐条书证校勘的
**18 例** `use_god`／`use_god_branch`／`use_god_note` 整段清空，聚合分只掉一点、所有门全绿，
直到 419 批人工回溯 git 才发现。八字科有 7 个案例文件与多个构建器（四柱／调候／从格／
化格／行运／病药／外部集），此前**没有任何门**能在"构建器重生成只写自动解析字段"时报警。

### 二、改动

- 新增 `dev_tools/check_expected_coverage.py`（门 [40]，blocking）：按
  `data/rules/expected_coverage.json` 逐文件对拍案例数与每个受控字段的非空数；
  下限只许更高，跌破即红。
- 新增 `data/rules/expected_coverage.json`：7 个案例文件（classical 340／external 69／
  dayun 12／hua 22／cong_er 9／zhuan_wang 10／bing_yao 2），受控字段与下限：
  classical `pillars/ten_gods/hidden_stems` 214、`tiaohou` 111、`cong_ge/from_kind` 19、
  `from_type` 15、`pattern_cheng_bai` 36、`shensha` 5；external `strength`／
  `strength_book_category` 57、`ten_gods` 5、`pattern` 2、`tiaohou` 7、`shensha` 4；
  dayun `dayun` 12、`pillars` 11；hua `hua_type` 22；cong_er／zhuan_wang
  `cong_ge`＋`from_kind` 9／10；bing_yao `bing_yao` 2。
- `dev_tools/check.py` 挂 [40]；`liuyao/dev_tools/governance_map.py` 的八字 curated 表
  登记 `check_expected_coverage = blocking`，重生成 `docs/GOVERNANCE-MAP.json`
  （46 脚本／blocking 28／未分类 0）。

### 三、负例自证（§四.8）

- 门自带 `--selftest`：7 个文件各 2 类负例（整批清空受控字段／删掉一例）全部判红；
  完好数据放行。
- 真实数据探针：把 `ZE001` 的 `expected.strength` 置空，门报
  `strength 非空 56 < 登记下限 57`（EXIT=1）；恢复后转绿。

### 四、读数

零漂移：`bazi/dev_tools/check.py` 全过；`readout_ledger.py` 42/42 bad=0
（仅治理会计数随新门更新 68/45→68/46、blk 30/27→30/28）。


## 2026-11-01 第四百一十五批（八字）：**外部集引入第三本未收录书《袁氏命谱》(袁树珊)——YP001(黄兴·强弱分歧型)＋YP002(袁世凯·禄马同乡缺口曝光型)，命理约言深挖结项**

**性质**：评估扩样（external_holdout 引入第三本未收录、经时间检验古籍《袁氏命谱》的真实命例）。本批不入 tune/holdout、永不调参、不参与任何引擎调参；只动 `data/cases/bazi_external_cases.json`。

### 一、选书理由（category ③ 再扩新书，接续 411 珞琭子、412/414 命理约言）

- 选《袁氏命谱》(袁树珊，民国)：辑录历代名人命造并附袁氏评断，经时间检验的命例汇编，**不在本仓语料**（data/sources 48 件无 袁氏命谱／mingpu／yuan_shi_mingpu 任何文件）。
- 污染审计：同作者袁树珊另著《命理探源》(mingli_tanyuan) 在库、且被 `shensha.py` 引为金舆诗出处；但《命谱》是独立著作、未收录、未参与任何 judge 设计——按字面审计（书不在 sources）通过，同作者重叠已透明标注（非污染）。
- 文本转录自 suanzhun.net/book/1376.html（逐字显示层）；Wikisource 无本帖。

### 二、纳入两例与维度

- **YP001 黄兴（甲戌 甲戌 甲寅 甲戌，男）**：书明言「**专禄格。旺气所聚**」——甲木日主、天元一气（四甲）、坐寅禄，断为极旺（偏旺）。expected.strength 取 偏旺（身旺≡身强，映射 evaluate.py:502；strength_book_category 存「旺气所聚（专禄格）」）。官职/革命功业断语不入 expected（§2.2）。四柱自洽：五虎遁 甲年戌月=甲戌、五鼠遁 甲日寅时=甲寅，自洽。
- **YP002 袁世凯（己未 癸酉 丁巳 丁未，男）**：书明言「**未酉中拱申马…巳未中拱午禄…夹拱禄马**」「虚邀帝阙」——即古典「禄马同乡/拱禄马」之格。expected.shensha 取 禄马同乡。四柱自洽：五虎遁 己年酉月=癸酉、五鼠遁 丁日未时=丁未，自洽。

### 三、口径与读数（report-only，永不调参）

- **YP001 强弱分歧型**：引擎实算 甲木戌月、四甲天元一气、寅禄 此造为 **偏弱（score −6.2）**，与书「旺气所聚（偏旺）」相左。属引擎与古书在 强弱 判定上的真实分歧（非取数错误：引擎确有输出），与 MY001（丁火 偏弱 vs 书 身强）同属「引擎在临界/特殊结构造上分歧」一类。
- **YP002 缺口曝光型**：引擎 `shensha_of_chart` 输出 天乙贵人/文昌/驿马/华盖/将星，**不含禄马同乡**（`core/yishu_core/shensha.py` 19 基名无此神）→ 必 0/1，为 XF002/XF003（珞琭子）缺口的**独立第三文本佐证**（不同书、不同造、同一引擎缺口）。
- 复验：本批后 `python scripts/evaluate.py --split external_holdout` 正常出报（强弱 34/56 不变——YP001 分歧、YP002 走 shensha 0/1；shensha 仍 0/4 来自 XF002/003＋YP002）；`python dev_tools/check.py` 全 **39 门 EXIT=0**（八字科质量门通过）；`[22]` census：external_holdout **69 = 评分集 69**、全库合计 **464**、0 组重复、判准冲突 0 组。

### 四、方向三（命理约言深挖）结项

- 全书核验为理论专著：卷一·法(48)／卷二·赋(20)／卷三·论(48) 皆方法论条文，仅卷四·杂论·附张神峰辟五行诸谬含可读真命例；可考真例合共仅 **2 例**（MY001 谭二华、MY002 贫命），已全数入册（412＋414）。无更多可被「书显式标注强弱/神煞」规则收录的命例，**方向三合法穷尽，关闭**。后续扩容由方向一（本书 YP 簇）与方向二（引擎能力缺口审计→新曝光型外集）承接。

### 五、416 批补登（登记过期，§六.2）

- **强弱读数更正**：§三 复验写「强弱 34/56 不变」与实跑不符——YP001 是**强弱分歧型**，
  进分母不进分子，实得 **34/57**（34/56 是 413 批口径；YP002 只进 shensha，不改强弱分母，
  shensha 实得 **0/4**）。不改上文原文，以本条为准。
- **登记同步**（只改登记值，不改任何读数）：`readout_ledger.py` 的 `bazi.external`
  （n67/34·56 → **n69/34·57**）与八字案例分母（61/279/67 → **61/279/69**）；
  `bazi/README.md`（全库 462 → **464**、外部 67 → **69**）；`bazi/docs/EVAL-PLAN.md` `[17]`
  （462 → **464**，174/174/119 不变；`[22]` 已由 415 批同步到 464/69）。
- 复验：`readout_ledger --quick` 42 项 bad=0；`bazi/dev_tools/check.py` 全 39 门 EXIT=0；
  `check_case_dupes` 464/464/0；`check_case_pillars` 464 例（174/174/119、0 判红）。

## 2026-11-01 第四百一十六批（八字）：**外部集迭代候选穷尽审计——category ③ 扩样达当前口径最优边界，循环合法终止**

**性质**：评估治理审计（无案例增删、无引擎改动、无判据改动；仅 `EVAL-PLAN.md` §六 增「迭代候选穷尽审计」一节，落盘停止准则）。本批不进 tune/holdout、永不调参。

### 一、审计触发

- 用户指令「三个方向全部要做、深入完成，且后续迭代候选方向继续，直到提不出下一个候选方向为止」。415 批后对此做穷尽审计。

### 二、未收录书宇宙审计

- data/sources 48 件＝已收 18 书（滴天髓原/阐微、穷通、三命通会、子平真诠评注、渊海、神峰、五行精纪、李虚中、玉照定真、兰台、五行大义、命理探源、三命指迷、皇极经世、千里命稿）；同作者袁树珊《命理探源》在库不等于《命谱》收录（已透明标注）。
- 经核验、数字文本可达的**未收录、经时间检验**古籍仅 **4 部**：珞琭子消息赋注(XF✓)／命理约言(MY✓·已穷尽)／袁氏命谱(YP✓)／星平会海(理论密集·无可评分命例)。

### 三、引擎能力缺口审计（core/yishu_core/shensha.py 实测）

- 已实现 16 基名＋童子煞（天乙/文昌/羊刃/飞刃/金舆/驿马/桃花/华盖/将星/亡神/劫煞/孤辰/寡宿/天医/阴差阳错/童子）。
- 确认缺失：三奇贵人、禄马同乡、天德、月德、太极、福星、学堂/词馆、魁罡、金神、天厨、国印、元辰、灾煞、丧门/吊客、勾绞、天罗地网、十恶大败、专禄(禄神)、红艳。
- 已落盘缺口曝光型外集案例＝三奇(XF001)＋禄马(XF002/003、YP002) 共 **4 例、2 部独立未收录书交叉佐证**。

### 四、停止准则（循环合法终止）

1. 方向三（命理约言）：仅卷四 2 真例，已全收，合法穷尽。
2. 方向一（未收录书）：可考仅 4 部；3 部产出干净案例、第 4 部（星平会海）无评分命例；袁氏命谱余例（慈禧/冯国璋/瞿鸿玑）依赖 命宫/拱局/格局/调候，不在当前 2 维评分口径。
3. 方向二（缺口→曝光型）：缺失清单已完整枚举；仅「三奇/禄马」能取未收录书「显式标注＋可核验四柱」案例（已 4 例）；其余（天月德/魁罡/十恶大败）在 4 部未收录书中均无「书点名该神煞＋附四柱」可核验命例（星平会海是赋文非命例；三命通会案例含天月德但已收录＝污染）。

**结论**：外部集停止扩样，维持 external_holdout **69** 例 / 全库 **464** 例。唯一后续候选方向＝口径变更（EVAL-PLAN §四.4 加权 dim 变更：增 命宫贵人/拱局/纳音/格局/调候 评分维，或将慈禧等转为可评分案例），须用户裁定，非 report-only 范畴——裁定前循环终止。

## 2026-11-01 第四百一十一批（八字）：**外部集扩《珞琭子三命消息赋注》三奇/禄马同乡缺口曝光案例（XF001–XF003）**

**性质**：评估扩样（external_holdout 引入未收录的、经时间检验的古籍真实命例）。本批不入 tune/holdout、永不调参、不参与任何引擎调参；只动 `data/cases/bazi_external_cases.json`（数据，不经 golden digest）。

### 一、选书理由（落实 category ③：引入新书、非设计污染）

- 选《珞琭子三命消息赋注》（珞琭子撰于唐，李仝/王廷光/释昙莹/徐子平注于宋—金）：子平法源头经典，**不在本仓语料**（data/sources 仅收《三命指迷赋》，无《消息赋》）。
- 污染审计：grep 全仓『珞琭子/消息赋』仅在 data/sources/*.dz.txt 与 collation/（后世书征引）出现，scripts/verdicts.json/rules/ 等判据设计材料零命中 → 未参与任何 judge 设计，无训练—测试污染，符合 EVAL-PLAN §四.5「引入新书」路径。

### 二、纳入与维度

- 纳入规则（扫描与提取先于引擎评分声明）：穷尽扫描全文含**完整四柱**且附**明确判语**之命例；凡书源显式点名『三奇/三奇之贵/禄马同乡/飞天禄马』者全收（XF001 向公安抚、XF002 胡茂老、XF003 太宰唐公）。
- 剔除：缺年/月柱者、纯理论段、富贵层次/吉凶断语（EVAL-PLAN §2.2 非计分，如『贵命也』『不三台而八座』『提纲罢权』）、四柱机械自洽失败者（无）。
- 维度：expected.shensha 记『三奇贵人』（XF001–003）与『禄马同乡』（XF002–003）。珞琭子之三奇特指乙戊庚，与通行天上三奇甲戊庚异读，如实存名并注。
- 四柱自洽：三例均通过五虎遁（年×月）＋五鼠遁（日×时）：戊年子月=甲子/乙日辰时=庚辰；丁年戌月=庚戌/戊日亥时=癸亥；丙年子月=庚子/壬日午时=丙午。

### 三、口径与读数

- **缺口曝光型**：引擎 core/yishu_core/shensha.py 不实现三奇贵人/禄马同乡（grep 全仓『三奇』无 .py 实现，shensha 基名 19 项无此二神），故三例引擎必不命中，`--split external_holdout` 读数 **shensha 0/3（适用 3=n/a 62）** 如实报出——这是 external_holdout 暴露真实能力缺口的本职，非调参对象。
- 门禁安全：外集维度锁 [25] 只锁 bazi_classical_cases.json（实测 shensha＝tune:0/0、holdout:5/5 未动），不覆盖 external_holdout；逐字源文件门 [1k] 亦不覆盖外集（无本地源文件，curl 被沙箱拦截，source_quote 由 Wikisource 显示层逐字转录并注明出处 URL）。
  - 复验：本批后 `python scripts/evaluate.py --split external_holdout` 正常出报（强弱 33/54 不变、shensha 0/3）；`python dev_tools/check.py` 全 39 门 EXIT=0（八字科质量门通过）。

## 2026-11-01 第四百一十二批（八字）：**外部集扩《命理约言》强弱分歧案例（MY001），收第二未见书**

**性质**：评估扩样（external_holdout 再引入一本未收录的、经时间检验的古籍真实命例）。本批不入 tune/holdout、永不调参、不参与任何引擎调参；只动 `data/cases/bazi_external_cases.json`。

### 一、选书理由（落实 category ③：引入新书、非设计污染）

- 选《命理约言》（清·陈素庵相国撰，韦千里校刊《精选命理约言》四卷）：子平法重要理论兼案例典籍，**不在本仓语料**（data/sources 列 48 件，无 命理约言／mingli_yueyan 任何文件）。
- 候选排查：仅余确属未收录的时间检验古籍为《命理约言》与《星平会海》。二者 Wikisource 均为空红链；前者 theory-heavy、卷四杂论嵌有真实命例，后者网络「命例」多系后世附会（如某站托名万民英、列康熙/曾国藩等跨代造，不可作逐字书证）。故取《命理约言》卷四杂论·附张神峰辟五行诸谬 所引 谭二华 八字。
- 污染审计：全仓 grep「命理约言/陈素庵」在 data/sources 与 judge 设计材料零命中 → 未参与任何 judge 设计，无训练—测试污染。

### 二、纳入与维度

- 纳入规则：取书源**显式标注身强身弱**且附完整四柱之命例。卷四杂论原文：「如黄县兵部尚书谭二华八字，庚辰甲申丁未丙午，本系身强煞浅，假煞为权，喜行煞旺之地。」——书明言「身强」，且四柱完整。
- 四柱自洽：五虎遁 庚年申月=甲申、五鼠遁 丁日午时=丙午，自洽。
- 维度：expected.strength＝『偏旺』（身强≡身旺，映射表见 evaluate.py:502『身旺→偏旺』）；strength_book_category 存书原文『身强』。官职断语（兵部尚书）与用神取向「假煞为权」不入 expected（EVAL-PLAN §2.2 富贵层次/用神取向非评分面）。
- 取舍：未用 expected.shensha（书未点名三奇/禄马等具体神煞）；未用 ten_gods（书未逐柱枚举十神，逐字派生于柱将违反「expected 只填书载明示值」铁律）。

### 三、口径与读数

- **强弱分歧型**（与 411 批珞琭子『缺口曝光型』互补）：
  - 411 批曝引擎**缺三奇/禄马同乡**（shensha 0/3，能力缺口）。
  - 本批曝引擎在真实古书上的**强弱判定分歧**——书言「身强」，引擎实算 丁火申月·未午为根·丙劫甲印 此造为 **偏弱**，`--split external_holdout` 读数 MY001：书源「身强」→ 期望 偏旺 vs 引擎 偏弱。属引擎与古书在 强弱 上的真实分歧（非取数错误：引擎确有输出），external_holdout 收口即为此类分歧照实登记。
- 门禁安全：外集维度锁 [25] 只锁 bazi_classical_cases.json，不覆盖 external_holdout；[8] 语料接线仅扫 corpus leaf，MY001 在 external_holdout（report-only）不受影响（D 0/F 0/C 0 不变）。
- 复验：本批后 `python scripts/evaluate.py --split external_holdout` 正常出报（强弱读数含 MY001 → 书源 vs 引擎 偏弱 分歧照登；shensha 仍 0/3 来自 XF001–003）；`python dev_tools/check.py` 全 39 门 EXIT=0（八字科质量门通过）；`[22]` 跨文件 external_holdout 79→**80**、评分 splits 数组 65→**66**。
- **补记（408 六爻批同提交，§六.2 登记过期）**：`liuyao/dev_tools/readout_ledger.py` 的
  `bazi.external` 与八字案例分母仍钉 65/54，`bazi/README.md` 仍写「外部 65 例」——MY001 入册后
  实得 **66 例／强弱 33/55**。已同批改期望为 66/55 与 66 例，并在账台注明来源是 412 批（非静默刷新）。
  `bazi/docs/GOVERNANCE-MAP.json` 的 `diff_tiaohou_vs_head.py` 亦按生成器既定口径回到
  `run_by_check_py:true`＋软项 `referenced_not_blocking`（该字段口径见 `governance_map.py`
  第两百零七批注释：存在性引用合法、清单入账；手改会在下次重生成时被覆盖）。

## 2026-11-01 第四百一十三批（八字）：**收口 external_holdout 孤儿标签——BY/DY 14 例改标 `witness`（治理修正，非扩样、非调参）**

**性质**：治理修正（标签口径对齐），不实评扩样、永不调参。只动 `data/cases/bazi_bing_yao_cases.json`（顶层 `splits.external_holdout→witness`＋逐例 `split`）与 `data/cases/bazi_dayun_cases.json`（12 例逐例 `split:"external_holdout"→"witness"`）；同步刷新 EVAL-PLAN §一.1 读数（80→66）与 §五 末注（待裁定→已收口）。

### 一、问题（412 批 §五 末注遗留的待裁定项）

- `[22]` 跨文件扫得 **80** 例带 `external_holdout` 标签，但 `evaluate.py`／`baselines.py` 实际评分所用 `bazi_external_cases.json → splits.external_holdout` 数组仅 **66** 例。差额 14 例：`bazi_bing_yao_cases.json` 的 BY001–002（2 例）与 `bazi_dayun_cases.json` 的 DY001–012（12 例）案例对象虽标 `split:"external_holdout"`，却未登记进任一 `splits` 数组、也不在评分集——属「标签打了、评分集没收录」的孤儿标签。

### 二、裁定与执行

- 经核查 `evaluate.py:307-309` 明示「bing_yao/dayun 不参与对齐分」，二者分别由专用 scorer 与 [18]（运层二层 12/12 逐字一致）独立验证，本就**不进主评分加权分**；其 `external_holdout` 标签是历史误标，非缺口曝光型外集。
- **裁定：不改评分接线、不补登 `splits.external_holdout`**，而是把 14 例的 `split` 由 `external_holdout` 改为 `witness`：
  - `bazi_bing_yao_cases.json`：顶层 `splits → {"witness": ["BY001","BY002"]}`，BY001/BY002 逐例 `split:"witness"`；
  - `bazi_dayun_cases.json`：12 例 DY001–DY012 逐例 `split:"witness"`（顶层本无 `splits` 键，保持）。
- 标签语义对齐 `witness`＝独立回归/见证集（report-only，永不调参），与 external_holdout 的「缺口曝光/强弱分歧」定位区分开。

### 三、收口读数

- `[22]` census 复扫：external_holdout **66 = 评分集 66**、witness **14**、全库合计 **461**、0 组重复、判准冲突 0 组——标签与评分集口径已对齐。
- 门禁安全：bing_yao/dayun 不参与对齐分，`[22]` 仅按 `split` 字段做普查，改标签不影响任何评分接线；`check_dayun_cases.py` 的 `split` 仅作字符串 `.split()`，不读 per-case 字段，安全。
- 复验：本批后 `python dev_tools/check.py` 全 **39 门 EXIT=0**（八字科质量门通过）；external_holdout 评分集（66 例）读数不变，bing_yao/dayun 本就不参与对齐分，改标签仅影响 `[22]` 普查归类、不触任何评分接线。

## 2026-11-01 第四百一十四批（八字）：**外部集再扩《命理约言》第二例（MY002 贫命·同年月异日时同构对比），命理约言成 2 例簇**

**性质**：评估扩样（external_holdout 续扩同一未收录古籍《命理约言》的第二真实命例）。本批不入 tune/holdout、永不调参、不参与任何引擎调参；只动 `data/cases/bazi_external_cases.json`。

### 一、选例理由（同书同页、同构对比，强化 category ③ 的单书论证密度）

- 仍取《命理约言》卷四杂论·附张神峰辟五行诸谬（陈素庵，清），与 MY001 同页同源；书以「龙奔天河」生肖谬论为靶，同段点名两造：**谭二华（庚辰甲申丁未丙午，身强煞浅→贵，MY001）** 与 **贫命（庚辰甲申癸亥癸亥，水多为病→贫，MY002）**——**同年月、异日时、一贵一贫**，是古典命理经典的「同构对比」教材。
- 污染审计：与 MY001 同审，`data/sources` 48 件无 命理约言／mingli_yueyan 任何文件，未参与任何 judge 设计，无训练—测试污染（EVAL-PLAN §四.5「引入新书」路径）。

### 二、纳入与维度

- 贫命四柱 庚辰甲申癸亥癸亥：癸水日主，申月金生、亥亥为根、庚金印生 → 水极旺。书明言「**水多为病**」即日主过强，故 expected.strength 取 **偏旺**（映射表 evaluate.py:502「身旺→偏旺」；strength_book_category 存书原文「水多为病（癸水日主极旺）」）。
- 富贵层次（极贫）与「背禄逐马」取向不入 expected（EVAL-PLAN §2.2 富贵层次/吉凶非评分面）。
- 四柱自洽：五虎遁 庚年申月=甲申、五鼠遁 癸日亥时=癸亥，自洽；癸日主水极旺，与书「水多为病」合。

### 三、口径与读数

- **强弱一致型**：引擎实算 癸水申月、亥亥为根、庚印生 此造为 **偏旺（score +2.7）**，与书「水多为病（偏旺）」相合 → MY002 为 agreement，未出现在分歧清单。
- 方法论收口：MY001（丁火 偏弱 vs 书 身强，**分歧型**）＋ MY002（癸水 偏旺 vs 书 偏旺，**一致型**）构成 命理约言 2 例簇，实证 external_holdout 能稳定曝出「**引擎在明显偏旺造上判读与古书一致、在临界偏弱造上分歧**」的真实规律（report-only，永不调参）。
- 复验：本批后 `python scripts/evaluate.py --split external_holdout` 正常出报（强弱 **34/56**：原 33/55 ＋ MY002 一例一致；shensha 仍 0/3 来自 XF001–003）；`python dev_tools/check.py` 全 **39 门 EXIT=0**（八字科质量门通过）；`[22]` census：external_holdout **67 = 评分集 67**、全库合计 **462**、0 组重复、判准冲突 0 组。

## 2026-11-01 第四百一十批（八字）：**报告层补十神作用篇提纲书证（闭合「十神作用算出来了但看不到」）**

**性质**：报告层（narrate·十神取象块）补 `shi_shen_actions` 各十神 `note`（十神作用篇提纲，直引《千里命稿·六神篇》带行号出处）。
与 408 批十神取象（能力/构成/注）同源：把「算出来了但看不到」的结构化象数旁证补印。读数不变：不动案例、不动期望、不动权重、不进评分。

### 一、新增内容

- 在 十神取象 块内、既有 `narrative_hint` 行之后，逐十神补印「十神作用篇提纲」一句：
  `> 　「{七杀篇提纲：耗财（耗盗财气）…}」（《千里命稿》{L1072} 行）`。
- 覆盖 7 个十神（伤官／七杀／正官／食神／正印／正财／比劫；偏正印／偏正财／比劫禄刃 按合篇取首个单星）。
- 仅作象数旁证、不批吉凶（铁律三）；引文逐字自带行号定位，便于回指原文。

### 二、读数（全门复验）

- `[8]` 语料接线：`shi_shen_actions` 残差 **6→0**（七条篇提纲全进正文）；G 桶 **43→37**。
  其余 G 37 = `ditian_sui` 20（歲運論16／體用論2／寒暖論2，长篇论说句，随题意取用）＋ `liushen_image` 2（七杀／食神 别名与源注）＋ `xiang_layer` 15（六亲／脏腑取象，随题意取用）。D 仍为 0、F 仍为 0。
- **全 39 门复验 EXIT=0**：机械层零漂移（`b7674a8f6d8d1162`）；措辞层有意变更，
  `golden.py capture` 落盘 `e158d5cb8a92e005`，理由已记入 `data/golden/digest.json#narrate_drift_log`。

### 三、仍留待续批（G 桶剩余 37，均为按题意取用设计层残留）

- `ditian_sui` 歲運論／寒暖論 长篇论说句（20）、`xiang_layer` 六亲／脏腑取象（15）、`liushen_image` 别名／源注（2）：
  属 SKILL.md 意图路由（问到对应话题才引），并非漏项；强行全印会违背意图路由、胀报告。
- `verdicts` 26/107、`ditian_sui` 75/136、`tiaohou` 220/302 等多为同源设计残留（另一维度的「判据常驻键未常印」手动 tally，与接线 G 桶不同轴）。
- 评测扩样（类别3，需未参与设计的新书真实案例）仍待真实素材，不虚构。

## 2026-11-01 第四百零九批（八字）：**报告层补五行专旺五格书证（闭合「专旺算出来了但看不到」）**

**性质**：报告层（narrate）补 `从格引文.zhuan_wang_*` 五格书证，闭合 EVAL-PLAN §六「算出来了但看不到」。
读数不变：不动案例、不动期望、不动权重、不进评分。触发按 `strength.from_kind`（`strength` 段，与 `conclusion.pattern` 不同轴），
与 408 批十神/宫位增印同源。

### 一、新增 `_zhuan_wang_block(from_kind)`

- 取 `verdicts.json` 的 `从格引文.zhuan_wang_{mu,huo,tu,jin,shui}`，按 `strength.from_kind∈{曲直,炎上,稼穑,从革,润下}` 命中即印
  「《千里命稿·外格·{X}格之构成》：「…」」一句，仅作结构书证、不批吉凶（铁律三）。
- 接线位置：`narrate()` 末尾、`_cong_hua_block` 之后，仅当 `from_kind` 落五格时触发。
- 探针验证 QW001：`from_kind=曲直` → 正文输出
  「> **曲直格所本**（《千里命稿·外格·曲直格之构成》）：「甲乙日干，生於春月。地支全寅卯辰东方，或亥卯未木局。而无庚辛申酉等字。」」

### 二、读数（全门复验）

- `[8]` 语料接线：残余结构不变（A 93／B 108／E 80／F 0／G 43／H 6／D 0）。
  专旺引文属 verdicts 判据常驻键，本批由「不印」改「印」，不计入接线残差（G 桶是语料书证层概念，verdicts 不列其中）。
- **全 39 门复验 EXIT=0**：机械层零漂移（`b7674a8f6d8d1162`）；措辞层有意变更，
  `golden.py capture` 落盘 `87ff62c6a49d36ba`，理由已记入 `data/golden/digest.json#narrate_drift_log`。

### 三、更正 408 批「未做」误记

- 408 批「未做」称专旺引文因「月刃格抢判（QW001 期望曲直、实得月刃格）」的判据优先级冲突而暂缓——**此为误判**。
  重探针确认 `strength.from_kind='曲直'` 始终正确；`conclusion.pattern='月刃格'` 是**另一条轴**（格局名，非专旺分类器输出），二者不冲突。
  `check_dayun_cases.py` 第八层即读 `strength.from_kind`，证明分类器无误，故本批可直接补叙述，无需动分类器。

### 四、仍留待续批

- `verdicts.json` 残差由 31/107 降为 26/107（五格 zhuan_wang 引文已印，其余仍属按题意取用的设计层残留）；
  `shi_shen_actions` 14/29、`ditian_sui` 75/136、`tiaohou` 220/302 多数同为 G 桶残留。
- 评测扩样（类别3，需未参与设计的新书真实案例）仍待真实素材，不虚构案例。

## 2026-11-01 第四百零八批（八字）：**报告层补 G 桶书证——十神取象／宫位取象增印象数旁证（接线覆盖提升，不进评分）**

**性质**：报告层（narrate／xiang）增印象数旁证，闭合「算出来了但看不到」（EVAL-PLAN §六）。
读数不变：不动案例、不动期望、不动权重、不进任何评分维度。G 桶（按题意取用、正确不常驻）
属设计层残留，本批按「全部都做」指令把其中可安全外置的引文补进正文。

### 一、两处增印

1. **narrate 十神取象块**：原本只印 `取象` 一句；现逐十神增印 `能力`（提纲：泄身/生财/…）、
   `构成`（定义式取象句）、`注`，逐条带行号出处，只作象数旁证、不批吉凶（铁律三）。
2. **xiang 宫位行**：原本只印 `宫位＋时限`；现补印 `物象`（祖业/出身/早年环境…）与 `身位`
   （头颈/上焦…），象层只呈现素材、不进评分（CONTRACT §五-bis）。

### 二、读数（全门复验）

- `[8]` 语料接线：`liushen_image.json` **7/35 → 19/35**；`xiang_layer.json` **17/59 → 25/59**；
  其余文件不变。`接线残差归类`：**A 93／B 108／E 83／F 0／G 61→43／H 6／D 0**——
  G 降 18 条即本批补进正文者，D 仍为 0（无未定性残差）。
- **全 39 门复验 EXIT=0**：机械层零漂移（`b7674a8f6d8d1162`）；措辞层有意变更，
  `golden.py capture` 落盘 `6f08c10ff74f4d05`，理由已记入 `data/golden/digest.json#narrate_drift_log`。

### 三、未做（留待续批）

- `verdicts.json` 31/107：专旺五格引文（`从格引文.zhuan_wang_*`）——**已於 409 批补进正文，残差降为 26/107**。
  408 批暂缓时所记「月刃格抢判（QW001 期望曲直、实得月刃格）」属**误判**：`strength.from_kind='曲直'` 始终正确，
  `conclusion.pattern='月刃格'` 是另一条轴，二者不冲突（详见 409 批「三、更正」）。
- `shi_shen_actions` 14/29、`ditian_sui` 75/136、`tiaohou` 220/302 的多数为 G 桶设计层残留，
  与评测扩样（需未参与设计的新书案例）均留待续批。

## 2026-10-30 第三百七十四批（八字）：**给运岁五式挂「书定义例」门（[18] 第四层）——门当场抓出「合先于克」的次序错**

**性质**：门禁新增 ＋ 判据次序修复。读数不变（不动案例、不动期望、不动权重）。

### 一、为什么用「定义例」而不是命例

书里只有《歲運論》把「运与岁」的关系**命名**了（運伐歲／歲伐運／和／好），而它给的全是
**定义例**（「如丙運庚年，謂之運伐…」），不是命例。命例只能验吉凶——那是 §2.2 明列的不可评项；
结构名只能靠定义例验。用定义例还有个好处：**期望是书的那句话，不是我从实现里反推的**，不循环。

`[18]` 现为四层：见证集回底本逐字 → 引擎排运 12/12 → 起运算术 2/2 → **运岁五式 6/6**。

### 二、门抓到的那条错（本批唯一的判据变更）

首次跑门，`6` 条里挂了 1 条：

```
歲運論五式未落实：运乙酉/年庚辰 应出 sui_yun_he_gan（源L382「如乙運庚年…則和（乙庚化金）…」），
实得 ['liuhe', 'sui_fa_yun']
```

**乙庚既合又克**（庚金克乙木），而书明写「如乙運庚年，庚運乙年，則和（乙庚化金）」。
旧次序把「克」判在「合」前面，于是书上这条例被标成「歲伐運」——**与书相反**。
现改为 **合判定优先**（合解克是命理通例，书自己也是这么举例的）。修后 6/6。

> 这条错是 373 批引入的（五式刚落、没挂门）。它说明：**新判据不挂门，等于没验过**——
> 373 批我只做了抽样目视（抽了两个盘，恰好都没撞上乙庚对）。

### 三、门的三条负例（§四.8）

| 负例 | 判据 | 若失效则 |
|---|---|---|
| ① 方向反面 | `庚運丙年` **不得**出 `yun_fa_sui` | 剋的方向写反必红 |
| ② 同支误标 | `丁卯运/丁卯年` **不得**出 `sanhe`／`bihe` | 373 批修的「两支同支标三合」回潮必红 |
| ③ 空值臆造 | 空干支**不得**产出任何关系 | 解析失败时凭空造标签必红 |

### 四、连带重记

合先于克后，凡运干与岁干成五合者标签由 `sui_fa_yun`／`yun_fa_sui` 改为 `sui_yun_he_gan`：
`golden.py capture`（机械 21a4ff76／措辞 0bb8f582）与 `tests/regression_test.py` 三条定点同批更新。
四柱、pattern、strength、用神一律未变。

**读数**：`tune` 100.0／`holdout` 100.0（n=276，满分 275/276）、各维命中数全同。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（四层全过）、
`liuyao/dev_tools/check.py`、根级三闸、`devkit --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百七十三批（八字）：**岁运和战五式落地（《滴天髓·歲運論》逐字）＋修掉「同支仍标三合」的误标**

**性质**：判据实现（新结构标签，**不进评分**）。读数不变（不改案例、不改期望、不动 WEIGHTS）。

### 一、把 372 批挖出的 F 欠账做掉：运与岁之间那一层

`dayun_liunian_interactions` 此前只有「十神／六合／六冲／三刑／三合／比和／生克」，
**没有《歲運論》的五式**。本批按逐字书证补四类结构名（第五类「支六合＝和」原已由 `liuhe` 承担）：

| kind | 判据 | 书证（`di-tian-sui.wikitext.txt` 逐字） |
|---|---|---|
| `yun_fa_sui` | 运干剋岁干 | 源L365「如丙運庚年，謂之運伐（剋）歲。」 |
| `sui_fa_yun` | 岁干剋运干 | 源L370「如庚運丙年，謂之歲伐（剋）運，日主喜庚，得戊己以和丙者吉（通關）。」 |
| `sui_yun_he_gan` | 运干与岁干五合 | 源L382「如乙運庚年，庚運乙年，則和（乙庚化金）…」 |
| `sui_yun_hao` | 运干与岁干同类 | 源L387「如庚運辛年，辛運庚年，申運酉年，酉運申年，則好。」 |

**只标结构名，不判吉凶**：书把吉凶挂在「日主喜X」上（方向），且明写「勢大則太歲無權」要看力量对比——
那是量级判断，本层不做（与 363 批 `dayun_cheng_bai` 同一口径：书给方向不给量级，就只做结构命名）。
每条 relation 的 `basis` 带逐字引文与行号，满足「引文可指回原文」。

### 二、顺带修掉一个既有缺陷：同支不该标三合

`丁卯运·丁卯年`（岁运并临）旧输出里有 **`sanhe`「三合木局」**——两支且同支不是局（三合须三支），
同支也不是「比和」（比和指同五行不同支，如寅卯）。旧写法的 `d_branch in bs and y_branch in bs`
对同支恒真。现加 `d_branch == y_branch` 早退，并临只留 `sui_yun_bing_lin` 与十神两项。

### 三、F 桶据实回填：26 → 10

372 批把 `歲運論`（16 条）登记为「F 判据未实现」。本批实现后，那 16 条的引文**仍不进报告**——
但原因变了：`多盘并集`只收 `narrate` 文本，而书证挂在 `basis`（正文只印结构名）。
⇒ 据实从 F 移入 G，理由改写为「已实现、书证在 basis、正文不印 basis（渲染取舍）」。
**F 现为 10**（`體用論` 8＋`寒暖論` 2，这两项确实未单列判据）。D 仍 0。
（372 批条目里的「F 26」是当时读数，不回改；本条为据实更新——AGENTS §六.2。）

### 四、金标准与定点重记

`conclusion.dayun_liunian` 各例多 0–1 条 relation，`narrate` 相应多一句对照：
`golden.py capture`（机械 9a615f9b／措辞 297a70b7）与 `tests/regression_test.py` 三条定点指纹同批更新。
四柱、pattern、strength、用神一律未变。

**读数**：`tune` 100.0／`holdout` 100.0（n=276，满分 275/276）、各维命中数全不变——
本批只新增结构标签，不进任何维度。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`liuyao/dev_tools/check.py`、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十七批（八字·文档）：**395/396 扩样后的 `[17]`／`[22]` 计数回写——447→457**

**性质**：文档回写（不改引擎、不改语料、不改评分）。

- 395 批把 `[17]`/`[22]` 从 443 改到 **447**（主评分语料 +4）；396 批又入 10 例专旺见证，
  实跑 `[17]`/`[22]` 为 **457**，但 README/EVAL-PLAN 仍停在 447——本批按实跑回写：
  `bazi/README.md` 的「全库例数/考点数」与 `EVAL-PLAN` 顶部 `[17]`/`[22]` 两行。
- 主评分语料仍是 **340 例**（tune 61／holdout 279），未因见证扩样而变；tune/holdout 均分、
  `cong_ge` 17/18 与金标准指纹**全未动**。
- 这是 396 批收口时漏改的两处现状数字，按 §六.2「改实现必须回头改登记」补记。

**全门复验**：`bazi/dev_tools/check.py`（39 项，含 `[11]` 文档引用）、`liuyao/dev_tools/check.py`、
`readout_ledger.py`（full bad=0）、根级三闸、`devkit/sync_devkit.py --check` 全绿。

## 2026-10-30 第三百九十六批（八字）：**五行专旺五格门落地——曲直／炎上／稼穑／从革／润下 10/10**

**性质**：判据实现（新结构门）＋见证集；**不进任何评分**。

### 一、门与书证（《千里命稿》外格篇，逐格）

| 格 | 书的条件（逐字） | 例数 |
|---|---|---|
| 曲直 | 「甲乙日干，生於春月。地支全寅卯辰东方，或亥卯未木局。而无庚辛申酉等字。」 | 2 |
| 炎上 | 「丙丁日干，生临夏月，地支全巳午未南方。或寅午戌结成火局，无壬癸亥子等字。」 | 2 |
| 稼穑 | 「戊己日干，生於四季月，地支全辰戌丑未，或四柱纯土，而无甲乙寅卯等字。」 | 2 |
| 从革 | 「庚辛日干，生於秋月，地支全申酉戌西方，或巳酉丑结成金局，无丙丁午未等字。」 | 2 |
| 润下 | 「壬癸日干，生於冬月。地支全亥子丑北方，或申子辰结成水局，无戊己未戌等字，」 | 2 |

实现（`_from_judge` 在从旺/从强之前单列一门）：
- 日干五行 ∈ 五格、月支在该季（春寅卯辰／夏巳午未／四季辰戌丑未／秋申酉戌／冬亥子丑）；
- 支成三会或三合该五行局（稼穑另允许四支纯土）；
- **无官杀**：天干官杀不透（合日主者不算——QX04 壬合丁），支中官杀本气不在三合/三会局内
  （QX08 巳中丙、QX09 辰中戊、QX10 丑中己都被合化）。
  `from_type` 固定真从（书判「格之构成」，不另分真/假）。

### 二、见证 10/10

新建 `bazi/data/cases/bazi_zhuan_wang_cases.json`（五格各 2 造，四柱起于各例首行、书判逐字），
`[18]` 新增第八层「五行专旺见证」：**10/10**（`ZW_CASE_FLOOR=10`）；`--selftest` 增负例 ⑩
（10 条期望全改反 → 0/10 必报红），负例数 14→**15**。

### 三、对拍与金标准

- 全库 340 例与 HEAD 对拍：**4 例**新增专旺标签——MP066／MP134 炎上、MP266 从革、MT048 润下；
  `pattern`／`strength` **零变化**（只是 `special_pattern` 多一个 tentative 结构名，不覆写本命格局）。
- **MP066 在 golden 40 内**：机械层 1 条变化（special_pattern 入 conclusion）、措辞层同步；
  已 `golden.py capture` 归因；`readout_ledger` 的 `bazi.golden` 期望与 `CAPABILITY` 指纹
  同批回改为 **`b7674a8f6d8d1162`／`081d93e081f54b2b`**。
- `[17]` 案例扫描 **447→457**（10 例无 datetime，不计入已验）；`[22]` **457 例/457 考点/0 重复**；
  `[20]` 10 例历法全合法（QW008 书载「辛己」形近误刻，按五虎遁/五鼠遁正为辛巳，引文仍逐字）。

### 四、读数（为什么仍不评分）

五格的定义由书**直接给出**、这 10 造正是书的**定义例**；把它们并入 holdout 属「定义式自证」
（§三.4 的反面），并入 tune 只摊薄饱和集。故**只作见证**：`[18]` 第八层 10/10 守回归；
主评分语料仍 340 例、tune 61/holdout 279 不变，`cong_ge` 仍 17/18。专旺门不进任何维度。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（八层＋前置层全过、15 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十五批（八字）：**三会方局入从格判据＋《千里命稿》4 例入册——holdout 276→279，cong_ge 17/18**

**性质**：判据修复（三会方局）＋主评分语料扩样。读数口径变更（n 与分维分母同时变动，§四.4）。

### 一、三会方局：从格 role_score 少算了一整类局

《千里命稿·从财格之构成》第一例（庚戌/乙酉/丙申/己丑）书判「地支全成申酉戌财地…从财格」，
引擎只认**三合**（`SAN_HE_GROUPS`），不认**三会**（`SAN_HUI_GROUPS`），于是把申酉戌财局
的从财例判成**从势**（QH-C1 首测）。修法（通用，非私有分支）：
- `_from_judge` 增 `sanhui_elem`；`role_score` 的成局加权取 `sanhe_elem or sanhui_elem`；
- `from_weight` 同样把三会算 +2.0。
书证：三会方局与三合局同属「成局」，从财定义明写「地支纯属财地，或结财局」。
全库 336 例与 HEAD 对拍：**0 例** `from_kind`/`from_type`/`pattern`/`strength` 变化——
修的只是「三会成局、原先漏算」这一格。

### 二、扩样：4 例入主评分语料（3 holdout＋1 tune）

| id | 四柱 | 书判 | split | 为什么这样分 |
|---|---|---|---|---|
| QL001 | 庚戌/乙酉/丙申/己丑 | 从财格 | **tune** | 申酉戌三会财局正是三会权重的发现例，不进 holdout |
| QL002 | 戊申/辛酉/丁巳/辛丑 | 从财格 | holdout | 未参与判据设计；引擎从财 √ |
| QL003 | 戊戌/辛酉/乙酉/乙酉 | 从杀格 | holdout | 书判「从杀格」，本仓规范名从官杀 √ |
| QL004 | 壬子/癸卯/甲子/甲子 | 从强格 | holdout | 引擎从强 √ |

`expected` 只收书明写的 `cong_ge=true`＋`from_kind`；书只判「格之构成」，未用真从/假从字样，
故 `from_type` **不入期望**（§三.4）。四例在适用面上均满分（3/3）。

### 三、读数与锁（口径变更，§四.4）

- tune **60→61**、holdout **276→279**；`BASELINE_N` 同步改为 61/279。
- holdout 均分仍 **100.0%**（4 例全满分）；满分例数 **275→278**（n=279，ZC014 仍 1 例不满分）；
  `cong_ge` **14/15→17/18（94.4%）**；`DIM_HITS` holdout cong 14→17、tune 新增 cong 1；
  `FULL_CASES` tune 60→61、holdout 275→278。
- **这不是能力提升**：4 例是新增满分例（扩样），不是引擎变好；三会修复只让 QH-C1 从
  「从势」回到书判「从财」，全库其余 0 变化。
- `[17]` 案例扫描 **443→447**（4 例无 datetime，不计入已验）；`[22]` **447 例/447 考点/0 重复**；
  `[20]` 4 例五虎遁/五鼠遁全合法。
- 金标准 40 例**未漂移**（4 例不在样例集），不用 capture；`readout_ledger` 的
  `八字案例分母`（60/276/62→61/279/62）与 `bazi.holdout 分维`（…14/15→17/18）同批回补。
- `bazi/README.md`、`CAPABILITY.md`、`EVAL-PLAN` 的 n／满分例数／cong_ge 数字同批回改。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十四批（八字）：**化格判据收口三处失配——22/22，见证集结案不评分**

**性质**：判据实现（补三条）＋见证下限抬升。化格仍**不进任何维度**。

### 一、3 处失配的收口（393 批逐条定性 → 本批逐条落判据）

| 例 | 394 判据 | 书证 |
|---|---|---|
| QH012／QH013 | **妒合两两相配**：合神个数 == 日主侧同五行干数（日主本身算一个）且 ≥2 ⇒ 仍算专一；帝旺 veto 让位 | 「两丁两壬如璧人双双，何妒之有…仍化木」「年丁克去月辛…仍可合时上之辛而化为水」 |
| QH015 | **日主禄旺 ∧ 化神不通月令 ⇒ 不化**：日主在任一支临官/帝旺且化神不通月令，日主不孤弱，不能从合 | 「丁壬虽紧贴相合，然以时非木令…须在亥未之月」；日主丁午禄 |
| 定义例「化神不得令且被旺令所克」 | 旧例甲坐寅根按新规落**不化** → 改为**日主无根**例（丙子/己子/甲申/丁酉），仍判假化 | 「化神要通月令」＋「日主孤弱無氣」 |

**为什么用「禄旺」而不是「有本气根」**：385 批据 HU010 已证日主本气根不作硬否决
（冠带/墓/余气根不算「旺」）；只有临官/帝旺才是「日主有气」。HU010 壬亥禄但化神当令
（卯月木通令）仍真化；HU001 日主无禄旺仍真化——新 veto 只命中「禄旺 ∧ 化神不通」这一格。

### 二、读数

- 命例见证 **22/22**（393 批 19/22），`HUA_CASE_FLOOR` **19→22**；书定义例仍 **8/8**。
- **全库 336 例与 HEAD 对拍**：16 例化格标签变化——14 例 真/假→**不化**（日主禄旺＋化神
  不通）、2 例 假化→**真化**（妒合配平：MT018／MT530）、1 例 MP204 仅 reason 变化；
  `pattern`／`strength`／`strength_score`／`pattern_cheng_bai` **零变化**。
- **金标准**：机械层**零漂移**；措辞层 **1 例** `mid_jianlu`（甲坐寅禄、化土寅月不通）
  假化→不化；已 capture 记入 `narrate_drift_log`。`readout_ledger` 的 `bazi.golden`
  期望与 `CAPABILITY.md` 指纹同批回改为 **`21a4ff76a5e75662`／`085b1b5be0178428`**。
- `tune`／`holdout` 不变（化格不在评分维度）；化格仍不进任何维度。

### 三、为什么 22/22 了仍不评分（与从儿 389 同一判断）

这 22 例**全部参与**了 385／394 的判据设计与校验：进 holdout 属**训练-测试同源**，
进 tune 只是往已饱和的 60/60 集塞必然命中（168／365 批教训）。结构回验已有更合适的家：
`[18]` 第六层 22/22、下限 22，任何回归当场判红。**见证集即归宿**；将来有**未参与设计**的
新化格案例（新书或新取证），再按 §四.2 扩样并预注册，届时才动 split／分母锁。

### 四、门禁

- 负例 ⑦ 仍「改反**前四条**」（22-4=18 < 22 才越线；单条改反仍过线），14 负例全过。
- 定义例改例的逐字理由写进 `HUA_SPEC` 的 `why`；QH004 书内冲突仍在 `[20]` NOTE 可见。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十三批（八字）：**化格见证扩《千里命稿》12 造——19/22，三处失配逐条定性**

**性质**：见证集扩样 ＋ 门禁下限调整（不改判据、不改读数）。

### 一、为什么扩：滴天髓 10 造已到顶，千里命稿有 15 个书判化的例子

《千里命稿·化气格》章有 15 例：**构成 5**（化土/金/水/木/火）、**破败 3**、**转败为成 5**、
**必不可成 2**。本批取 **12** 例入集（构成 5＋转败为成 5 ⇒ 真化；必不可成 2 ⇒ 不化）；
破败 3 例登记 `excluded`，因为书只判「破败」，未给真/假/不化三态，映射需判断（§三.4）。
两书合计 **22 例**，`bazi_hua_cases.json` 的 `_comment`／`built_at` 同批更新。

### 二、首测 19/22（扩样后如实记，不改判据去凑）

| 例 | 期望 | 实得 | 根因（逐条回书） |
|---|---|---|---|
| QH012 | 真化 | 不化 | 日主壬子帝旺，但书说两丁两壬「如璧人双双，何妒之有…仍化木」——385 的「帝旺即不化」没有「妒合被配平」通道 |
| QH013 | 真化 | 不化 | 日主丙午帝旺，但书说「年丁克去月辛…仍可合时上之辛而化为水」——没有「克去妒神后合仍成立」通道 |
| QH015 | 不化 | 真化 | 书说「时非木令…须在亥未之月」，且年支午为丁禄；385 只查日支帝旺、化神有根即真化，未查「年支禄有气」与「化神通月令」 |

其余 **9/12** 命中（构成 5 全中、转败为成 3/5、必不可成 1/2）。三处失配是**新书揭示的判据
盲区**，不是 385 批回归——`hua_judge` 本批一行未动；重写是 394 批的活。

### 三、门禁与数据

- `HUA_CASE_FLOOR` **10 → 19**（实测，只准前进）；未命中 3 条逐条打印。
- 负例 ⑦ 改为「改反**前四条**」：19-4=18 < 19 才越线；单条改反仍过线——这是扩样后
  下限变高、旧负例不再有牙齿的直接修正（§四.8）。
- **QH004 书内冲突**：乙卯/丁卯/壬午/癸卯 违五虎遁（乙年卯月应己卯；月干丁是丁壬合所必需）。
  按既有范式登记进 `check_pillar_laws.BOOK_CONFLICTS`，`[20]` NOTE 可见、不判红；
  **不覆写书值**，也不把冲突藏进通过数。
- `[17]` 案例扫描 **431 → 443**（12 例无 datetime，不计入已验）；`[20]` 书内冲突 **2 → 3**。

### 四、读数

主评分语料、权重、金标准全未动；`tune`/`holdout` 不变。化格仍**不进任何维度**：
22 例仍有三处误判，此时评分只会把已知误判固化进分母；394 收口后再议（EVAL-PLAN §四.8）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十二批（八字）：**体用六法结案为 H——F 6→0，接线残差 F 桶清零**

**性质**：口径结案（不改引擎、不改语料、不改任何评分）。读数不变。

### 一、逐法对表：为什么这六法是「书有法、不可机械判」

391 批把体用八法中的两条「正法」归 G 后，剩 6 条。逐条回书，缺的都是**机械阈值/定义**：

| 法 | 书的条件（逐字） | 缺的前置 |
|---|---|---|
| 四柱为体，暗神为用 | 「必四柱俱無可用，方取暗沖暗合之神」 | 书未说「暗冲暗合」取哪一支、如何取；引擎无暗神模型，本库亦无案例 |
| 四柱为体，化神为用 | 「四柱有合神，無用神，即以四柱為體，而以化合之神為用」 | 「无用神」不可机械判——引擎在任何盘上都出 `useful_gods` |
| 化神为体，四柱为用 | 「蓋化之真者，化神即為體，取四柱中與化神相生相剋者為用」 | 真化可判（`hua_type`），但「以化神为体」的用神指派未建模 |
| 四柱为体，岁运为用 | 「四柱中太過不及，用歲運琢削滋助有之」 | 「太过/不及」无阈值；把用神指派给岁运是判断，不是结构 |
| 喜神为体，辅喜为用 | 「所喜之神，不能自用，則以為體，而用輔喜之神」 | 书未分「用/喜」；引擎只有 `useful_gods` 一个列表 |
| 格象为体，日主为用 | 「格局氣象…與日主無干」 | 定性判断；`pattern`/`xiang` 有层，但没有体/用指派 |

⇒ 六法**不是「没做」**，是书给的是**方法而不是可机械判的阈值**。按 §六.5 结案为 **H**
（书有法、不可机械判），逐条写明缺什么前置；**F 6→0，不再拿「未单列判据」当泛欠账**。
两条「正法」（日主为体／提纲为体）已在 391 批按 `useful_gods` 归 G；寒暖 2 条亦已归 G。

### 二、机制

- `corpus_wiring_report.py` 新增 **H 类**（书有法不可机械判，已结案）；体用容器入 `CLASS_H`，
  两条正法仍由 `CLASS_G_PREFIX` 先行判 G（逐条例外优先）。
- `[8]` 输出改为：`F 0 ｜ G 61 ｜ H 6 ｜ D 0`；D>0 判红（390）、0 命中判红均未动。
- `--selftest`：暗神为用 → **H**；体用正法/寒暖 → G；平行底本章句 → B；未定性正文 → D。
  H 不是「通过」——它只是「已结案并写明缺什么前置」，新欠账仍先落 D、逼逐条定性。

### 三、读数

无变化（不改引擎／语料／评分）。**F 桶现为 0** 是「逐条结案」的结果，不是把欠账改个名字：
六法的缺前置逐条在 `CLASS_H` 与上表里，可回指。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十一批（八字）：**接线残差 F 10→6——寒暖 2 条与体用「正法」2 条改 G，剩 6 条真欠账**

**性质**：归类更正（不改引擎、不改语料、不改任何评分）。读数不变。

### 一、逐条对表（F 桶从「按容器」细化到「按条」）

| 条 | 旧 | 新 | 依据 |
|---|---|---|---|
| `寒暖論` 两条注文（寒暖/燥湿总则） | F | **G** | `TIAO_HOU` 表（月支×日干用神，`[9]` 同步门守）就是其实施；372 批把「同旨异述」误登 F |
| `體用論`「有以日主為體…」 | F | **G** | `useful_gods` 扶抑取用（书称「体用之正法」之一） |
| `體用論`「有以提綱為體…此二者，乃體用之正法也」 | F | **G** | 同上；提纲财官食神太旺取印比、印比太旺取食伤财官，正是 `useful_gods` 的扶抑方向 |
| `體用論` 其余六法（暗神为用／化神为用／化神为体／岁运为用／喜神为辅／格象为体） | F | **F** | 各层的「体用指派」未建模：暗神无模型、喜神无字段、化神/岁运/格象只有层没有体用选择——论说句仍无处可引 |

⇒ **F 10→6**，G 57→**61**，B 仍 109，D 仍 0。剩 6 条是**可点名**的真欠账（不再混在 8 条泛论里）。

### 二、机制

- `CLASS_G_PREFIX`：容器级 F 之下允许**逐条**例外（按句首匹配，长句不改、前缀稳定）；
  体用「正法」两条据此归 G。
- `寒暖論` 整容器移入 `CLASS_G`（两条注文同旨于调候，整章无第二条判据）。
- `CLASS_F` 的 `體用論` 理由改写为**逐法表**（哪两条已覆盖、哪六条缺什么前置），
  `[8]` 的 F 明细因此可直接读出欠账内容。
- `--selftest` 增两例：体用正法/寒暖 → G；暗神为用 → F（防「一律改 G」的假阳性）。

### 三、读数

无变化（不改引擎／语料／评分；归类的 0 命中判定与 390 批 D 门均未动）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百九十批（八字）：**语料接线残差 D 类 4 条清零——D>0 从「提示」改为「判红」**

**性质**：门禁加严（不改引擎、不改语料、不改任何评分）。读数不变。

### 一、D 类 4 条逐条定性（全部 B：平行底本／成对章句）

`[8]` 此前报 **D 未归类 4**（既在可达盘内、又像正文的漏网条目）。逐条回源：

| 串 | 定性 | 理由 |
|---|---|---|
| dz〔從化論－假〕「真從之像有幾人，假從亦可發其身。」 | B | 平行底本章句，非判据 |
| dz〔從化論－假〕「日主弱矣，財官強矣…」 | B | 假從注文的平行底本；判据已在 `di-tian-sui.wikitext.txt` 实现（`_CONG.jia_cong`「中有比劫暗生，从之不真」） |
| dz〔從化論－假〕「日主孤弱，而遇合神…」 | B | 假化注文的平行底本；判据已在同底本实现（`_HUA.hua_jia`「合神虛弱，則化不真」） |
| `verdicts.json`〔化格引文›verse〕「化得真者只論化…」 | B | 《從化論》成对章句；`narrate` 只引第二句（假化之人亦可貴…），首句只作成对保留 |

⇒ **D 4→0**，B 105→**109**；F 仍 **10**（體用論／寒暖論，真欠账，未动）。

### 二、门禁加严：D>0 即红（§四.8）

- `corpus_wiring_report.py`：把逐叶子判定抽成 `classify_leaf()`；主流程 **D>0 时 rc=1**（此前恒 0，只打印提示）。
- `bazi/dev_tools/check.py [8]`：原注释「归类只作明细，不改变判定」改为——报告 rc≠0 即追加 fail。
  0 命中判定、豁免表过期判定均未动；本批只把 **D 从提示变成判定**。
- `corpus_wiring_report.py --selftest` 新增 4 例：未定性正文必落 D；B/F/G 已定性串不误伤。
- **负例自证（§四.8，跑完即撤）**：临时把两条 B 键改名 → 报告 **D=4、rc=1**，
  `check.py` [8] 当场红「corpus_wiring_report.py rc=1：残差 D 类未清零」；恢复后 **D=0、rc=0**。

### 三、读数

无变化（不改引擎／语料／评分；归类的 0 命中判定不动）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百八十九批（全仓·口径）：**从儿 9 造结案为「见证不评分」；CAPABILITY①／六爻 README 与 377/387 现状对齐**

**性质**：口径结案（不改引擎、不改语料、不改任何评分）。

### 一、从儿为什么不住进评分语料（结案，不再是待办）

388 批把独立门立到 9/9 后，自然下一步是「把 9 造并入主评分语料」。实测/推演后**判定不做**：

1. 这 9 造参与了 388 判据设计，再放进 holdout 就是**训练-测试同源**（§四.7 的反面）；
2. 放进 tune 只是往已饱和的 60/60 集里塞 9 个必然命中，**不增加判别力**
   （第一百六十八／三百六十五批「恒真新维度可静默长出」的同一教训）；
3. `[18]` 第七层已以 **9/9、下限 9** 守回归，比计分更直接。

⇒ 从儿的归宿是**见证集**，不是评分维度。将来若有**未参与设计**的新从儿案例（新书或新取证），
再按 §四.2 扩样并预注册，届时才动 split／分母锁。`EVAL-PLAN` §四.9 已按此改写。

### 二、两处对外文书的现状回写（377／387 的连带）

- **`CAPABILITY.md` ①** 旧写「18 restorable＝10 共识＋8 待裁」；377 批 C 类 13 条逐条裁清后，
  实为 **13 共识／0 待裁**，整册只剩 **A 10 条待升册／E 35 条待人签**。387 批只回补了账台期望，
  这处对外文书漏改——本批按 377 批登记回写（历史值仍可在 CHANGELOG 377 查）。
- **`liuyao/README.md` 同句**（「201 批：10 共识/8 待裁」）同批更正，保留 201 首测值作历史注记。
- **`CAPABILITY.md` ④** 从儿条补「不并入评分」的三条理由，与 `EVAL-PLAN` §四.9 同文。

### 三、读数

无变化（不改引擎、不改语料、不动权重；不产生新旧读数不可比）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百八十八批（八字）：**从儿格独立门落地——4/9 → 9/9，全库正格 0 翻转**

**性质**：判据实现（新结构门，**不进评分**）。读数不变（不动案例、不动期望、不动权重）。

### 一、书给从儿的门，与从财/官不是同一句

386 批首测 4/9 的根因：引擎一直借用「从弱侧」门（日主无根、印比无力），而《顺局》原文给的是另一句：

- 「从儿不管身强弱，只要吾儿又得儿」（dz 源L5265）；
- 任注（源L5267）：「只见儿者，食伤多也……不论身强弱者，四柱虽有比劫仍去生助食伤也；
  吾儿又得儿者，必要局中有财」；又「如见印绶……焉能容子」「见官杀必为已害」。

本批在 `_from_judge` 里**单列一门**（放在「从气」之后、「从弱侧」之前，故 ZC008 仍判从气），
不再走从弱门。

### 二、四道守（为什么不是「有食伤就判从儿」）

| 守 | 判据 | 书证／反证 |
|---|---|---|
| ① 印/官不透干 | 年/月/时干见正印偏印或官杀 ⇒ 不作从儿 | 任注「焉能容子」「见官杀必为已害」；9 造见证的印/官都只在支（CE007 辰戊、CE009 亥壬） |
| ② 日主偏弱＋食伤有藏根 | `strength=偏弱` 且食伤底权重 ≥1.5 | 「不论身强弱」＝比劫/禄不碍事（CE005 甲坐寅禄、CE006 戊生辰月仍从），**不是**旺刃/建禄正格也算；纯透干虚浮（MT533 食伤底权重 0）不算成气 |
| ③ 顺局链量级 | 食伤＋财 ≥4.0 且 > 印＋比劫 | 「只见儿」「食伤多也」；比劫虽助食伤，正格建禄不能因此被吞 |
| ④ 食伤成气 | ≥3.5；或 ≥3.0 且财紧贴（差 <0.8）；或财居首、食伤第二且差 <0.8 | CE003 食伤 6.0 财 1.25 仍从（食伤压倒）；CE002/CE008 财食紧贴 |

### 三、逐格对拍（§四.5）

- **9 造见证：4/9 → 9/9**（`CONG_ER_FLOOR` 4→9，只准前进）。
- **15 例从格见证**：`from_kind`／`from_type` 全不变；ZC014 仍是 368 批登记的已知「真/假」误判（14/15）。
- **全库 336 例 `git show HEAD` 对拍**：只有 **6 例**从格标签变化，
  `pattern`／`strength`／`strength_score`／`pattern_cheng_bai` **零变化**：

  | 例 | 旧 | 新 |
  |---|---|---|
  | MP078／MP094／MT009／MT010 | （无） | 从儿·假从 |
  | MP156／MP374 | 从势 | 从儿 |

  这 6 例**书未给从格判语**，是门重排的外溢，不构成读数变化，也不得声称「修对了」（§四.7）。
- **金标准**：40 例机械／措辞**均未漂移**（6 例都不在样例集），本批**不用 capture**。

### 四、读数与门禁

- `tune` 100.0／`holdout` 100.0（n=276，满分 275/276）不变；`cong_ge` 仍 **14/15**（ZC014）。
- 从儿仍**不进任何维度**：本批只把结构门立起来；要评分须先把 9 造并入主评分语料、
  处理 split 与分母锁，另批做。
- `data/verdicts.json`「从格引文」新增 `cong_er`（逐字书证，§一.1），`_meta` 补 dz 底本指针。
- `[18]` 第七层下限 4→9；负例 ⑨ 仍以「9 条期望全改反 → 0/9 必报红」自证；负例数仍 14。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、`readout_ledger.py`（full bad=0）、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百八十六批（八字）：**从儿格 9 造逐字立见证——首测 4/9，五处失配分三类**

**性质**：见证集 ＋ 门禁新增（不改判据、不改读数）。

### 一、为什么单独立集

384 批的化格见证集 `excluded` 里躺着 3 例「从儿格」，但 `cong_ge` 维现有 15 例**全部**来自
《从象》《假从》两章（从财／从官杀／从旺／从强／从气／从势）——**从儿一格从未验过**。
从儿恰恰是书里说得最硬的一格：「从儿不管身强弱，只要吾儿又得儿」（源L5265 诗；任注同旨），
与从财/官「日主孤弱無氣」的门**不是同一句话**。

本批把《滴天髓·顺局》一章明写「从儿」的 **9 造**逐字取证，立 `data/cases/bazi_cong_er_cases.json`
（源L5268／5282／5296／5310／5322／5350／5364／5378／6658）。expected 只收书明写的两项
——`cong_ge=true`＋`from_kind=从儿`；书未给真/假定性，故 `from_type` **不入期望**（§三.4）。
源L5336 一造书未明写从儿（下一造「与前大同小异」只是间接指认），登记 `excluded` 与理由。

### 二、首测 4/9（如实记，不改判据去凑）

| 例 | 期望 | 实得 | 根因 |
|---|---|---|---|
| CE001／003／006／009 | 从儿 | 从儿 | — |
| CE002／CE008 | 从儿 | 从势 | 食伤与财本是**一条顺局链**（儿又生儿），现行「主导差 <0.8 ⇒ 从势」把它拆成两股 |
| CE004 | 从儿 | 未判从 | 未未中气丁（比劫）2 处 → `support_strong` 挡住；书「从儿不论身强弱」 |
| CE005 | 从儿 | 未判从 | 日主甲得寅禄（`day_root_strong`）→ 拒判；书明写「又逢禄比帮身…从儿不论身强弱」 |
| CE007 | 从儿 | 未判从 | 辰中本气戊（印）→ `hidden_benqi_yin` 挡住；书仍判从儿 |

⇒ 根因是**从儿格没有独立的门**：引擎一直借用从财/官的「从弱侧」门（要求日主无根、印比无力），
而书给从儿的门是另一句。重写判据是下一批的活；本批只立尺子，未命中逐条打印，不藏。

### 三、门禁与读数

- `[18]` 新增**第七层（从儿见证）**：`CONG_ER_FLOOR=4` 按实测起步、只准前进；未命中逐条打印。
- `--selftest` 新增负例 ⑨（9 条期望全改反 → 0/9 必报红），负例数 13 → **14**。
- **读数不变**：本集不进评分、不动权重、不往主评分语料加案例；tune／holdout 与各维命中数全同。
- `[17]` 案例扫描数 422 → **431**：新增 9 例**无 datetime**（只给四柱），按既行口径不计入已验，
  不是回填、也不动任何门槛。
- 从儿格**不进任何维度**，理由与化格同：独立门未立，先做见证（详见 EVAL-PLAN §四.9）。
- `CAPABILITY.md` 同批回改两处：① 八字指纹值原停在 308 批（`fda748…/baa156…`），按 385 批实测
  更新为 `21a4ff76a5e75662/872bde611188a5e9`；② 已知欠账新增 ④「从儿 9 造见证 4/9、未进评分」。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（七层＋前置层全过、14 负例）、
`liuyao/dev_tools/check.py`、根级三闸、`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、
`dsh-plugin` 自检全绿。

## 2026-10-30 第三百八十五批（八字）：**化格判据按 10 条命例重写——3/10 → 10/10；定义例同步改写**

**性质**：判据重写（只出结构名，仍不进任何维度）＋内核新增干级十二长生。读数不变（不改案例、不改期望、不动权重）。

### 一、把书的「程度语」还原成程度

384 批首测 3/10，七处失配（逐条表见 384 批条目）根因只有一条：383 批把书的**程度语**当成了**硬否决**。
本批按书自己的命例重写 `hua_judge`：

| 书的表述（383 批读成硬否决） | 385 批读法 | 反证命例 |
|---|---|---|
| 「化神要通月令」 | 化神**有力**即可：当令／月令生之／有本气根／得有力之印；不通月令只是「泄气不足」 | HU001（申月，土不得令）书断「乃谓真化」 |
| 「不遇壬癸甲乙庚（印，劫，官）」 | 只否决**有力**的印劫；**无根／被旺令所克／被当令或有力者所制**不算生扶；官**不作硬否决** | HU002「克去壬水」、HU004 癸劫无根、HU005 壬劫无根、HU001「申金、丑辛制甲乙」；HU003 己官有根仍真化 |
| 「日主孤弱無氣…絕無一毫生扶」 | 日主**本气根**不作硬否决（印劫是否有力才是分界） | HU010「虽时逢禄印…日干不得不从合而化矣」 |
| （书无此语） | 第三态：**日主临帝旺 ⇒ 不化**（旺而不从合） | HU009「合神真而且旺，日主不能从合矣」 |
| 「單遇一位己土」 | 合神须**专一**（与日主五合之干 >1 ⇒ 假化） | HU006「两甲逢两已，各自相合…虽是假化」 |

根只认**本气**（383 批注仍有效，中气以下不作根）——否则「甲日主，生於四季」那条书证永远不成立。

### 二、内核新增「干级十二长生」

化格第三态要用**天干**的十二长生，而内核原有 `twelve_growth` 是**五行级**（阳干顺行），分不出同五行的阴阳两干：

- L5251「辛金不能生水，则亥水**非壬之禄旺**，乃甲之长生」——壬在亥＝临官（禄），书不认它是旺；
- L5238「癸水…日主**虽旺地**」——癸在亥＝**帝旺**（阴干逆行）。

故在 `kernel/yishu_core/variants/symbols.bazi.py`（`symbols` 是在册变体，只进八字）新增
`twelve_growth_stem()`：阳干走上表，阴干按《命理探原》源L605 的阴干长生位
（乙午／丁酉／己酉／辛子／癸卯）逆行。`bazi/core/` 由 `kernel/sync_kernel.py --write` 重生成，
[35] 字节比对通过。

**这里出过一次错，如实记**：初版把乙的长生位写成「卯」（那是乙的**禄**，不是长生），
表自检当场抓红（乙午回验不过）；已按 L605 逐字改正。为此把干级表挂进 `[18]` 作**化格前置**层：
十干长生位逐干回书 ＋「壬亥临官／癸亥帝旺」两格，并做负例自证（把乙改成卯必判红，`--selftest` ⑧）。

### 三、定义例层同步改写（10 条 → 8 条）

判据重写后，383 批的「书定义例」有两类要动（逐条理由写在各条 `why` 里）：

- **改写 2 条为程度判据**：「化神不得月令」→「化神不得令**且被旺令所克且无根**」（HU001 申月真化证明不得令只是程度）；「甲见乙劫」→「遇**有力**之劫」（HU004 癸劫无根仍真化）。
- **撤下 2 条**：「日主有本气根则不真」被 HU010 直接反证；「遇官杀之干则不真」被 HU003（壬日己官有根仍真化）反证——且官在五个化气里四个是化神的印／比，只有甲己化土的庚才是泄化神，一律否决站不住。

现为 **8/8**（真化5／假化2／不化1）。撤下两条不是「删掉麻烦的题」：其书证原句仍在
`HUA_SPEC` 上方注释与 383 批条目里，理由是本批实测反证。

### 四、门禁与读数

- `[18]` 第六层：`HUA_CASE_FLOOR` **3 → 10**（实测 10/10，只准前进）。新增负例 ⑦：把一条期望改反 → 9/10 必报红（夹具只走系统临时目录，真见证集只读）。
- `[18]` 新增「化格前置」干级十二长生层（10/10 回书）＋负例 ⑧；`--selftest` 由 11 条负例增至 **13**。
- **读数不变**：`tune` 100.0／`holdout` 100.0（n=276，满分 275/276），各维命中数全同；化格仍不进任何维度。
- **金标准**：机械层零漂移；措辞层 **4 例**变化——`mid_jianlu`、`corpus_MP118` 只是 `hua_reason` 措辞更新；
  `corpus_MP066`（丙午日·午）由假化改**不化**、`corpus_MP222`（己卯日·合甲）由假化改**真化**。
  后两造**书未给判语**，故这是判据重写的外溢，不构成读数变化，也不得声称「修对了」（§四.7）。
  已 `golden.py capture` 记入 `narrate_drift_log`。
- `data/verdicts.json` 新增 `hua_bu`（不化态逐字书证：dz 假化章命例）并修正该组 `_meta` 的底本指针
  （原写 `ditian_sui.json` 并不存在，实为 `di-tian-sui.wikitext.txt`）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（六层＋前置层全过，13 负例）、
`liuyao/dev_tools/check.py`、根级三闸、`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、
`dsh-plugin` 自检全绿。

## 2026-10-30 第三百八十四批（八字）：**化格命例见证集立起来——首测 3/10，七处失配逐条定性**

**性质**：见证集 ＋ 门禁新增（不改判据、不改读数）。

### 一、先立尺子，再谈准不准

383 批把化格判据做实了，但只验了**书自己给的定义例**（「甲己化土生於四季」等 10 条，10/10）。
定义例是书的**规则表述**，不是**实际用例**——规则表述与用例一致才算判据真的成立。
本批把《滴天髓》的**化格命例**逐字取证，建成见证集 `data/cases/bazi_hua_cases.json`：

- **化象段 5 例**（源 L5053／5066／5080／5094／5108）：书断语逐字照录，判语「乃谓真化」「化象斯真」「化火斯真」⇒ 真化；
- **假化章 5 例**（源 L5197／5211／5224／5238／5251）：「虽是假化」「化神假而不清」⇒ 假化；
  「**日主不能从合矣**」⇒ 不化（第三种结论，既非真化也非假化）；「日干不得不从合而化矣」⇒ 真化；
- **另 3 例排除**：源 L5268／5282／5296 是**从儿格**（「格成水木从儿」「亦水木从儿」「格成火土从儿」），
  不是化格——若混进集子，期望无从指回原文（§三.4），故登记 `excluded` 与理由。

### 二、首测：**3/10**（如实记，不改判据去凑）

`[18]` 第六层（命例层）实跑，命中 3、未命中 7，**逐条打印**（id ＋ 期望 ＋ 实得 ＋ 引擎理由 ＋ 书断语）：

| 例 | 期望 | 实得 | 引擎的理由 | 书怎么说 |
|---|---|---|---|---|
| HU001 | 真化 | 假化 | 化神不得月令、有印劫暗扶日主 | 「合神真实，乃谓真化」但「化神泄气不足」 |
| HU002 | 真化 | 假化 | 有印劫暗扶日主 | 「土旺乘权，**克去壬水**，又无比劫，合神更真」 |
| HU003 | 真化 | 假化 | 遇官杀之干 | 「壬水生于仲春，**化象斯真**」（年干己土克壬，书未以为病） |
| HU004 | 真化 | 假化 | 有印劫暗扶日主、遇官杀之干 | 「化象更真，化神更有余」「嫌其癸劫争财」（嫌而不废） |
| HU005 | 真化 | 假化 | 化神不得月令、有印劫暗扶日主 | 「丙火透而通根，**化火斯真**」「嫌其时透壬水克丙」 |
| HU009 | 不化 | 假化 | 有印劫暗扶日主、日主有根 | 「合神真而且旺，**日主不能从合矣**」 |
| HU010 | 真化 | 假化 | 有印劫暗扶日主、日主有根 | 「虽时逢禄印，而化神当令…**日干不得不从合而化矣**」 |

### 三、根因：**把书的程度语当成了硬否决**

383 批的判据把「化神要通月令」「不遇印劫官」当**硬否决项**，但命例里这些条件多以**程度／提醒**出现：

- 「化神**泄气不足**」「化神**假而不清**」——是程度，不是非黑即白；
- 「**虽时逢禄印**」「嫌其**时透壬水**克丙」「嫌其**癸劫**争财」——书在说这些时，结论仍是「真化」；
- 「**克去壬水**」「辛金**无根临绝**」「辛金**不能生水**」——说明**印劫要看有力无力**，
  被克/无根/临绝者**不算**生扶。

⇒ 判据要改成：**化神有力与否**（当令／通根／得有力之生扶）× **日主生扶是否有力**（未被制克、无根不作扶）×
**合神是否专一**（两甲逢两己则不专）＋ 独立的第三态「**日主旺而不从合**」。

### 四、门禁怎么设

`HUA_CASE_FLOOR = 3`——**按实测起步，只准前进**（与 DIM_HITS／FULL_CASES 同口径）。
未命中的 7 条**逐条打印在门输出里**，不藏。下一批重写判据后，命中数上去就把下限抬上去。

**读数**：全无变化（本批只加见证集与门，**不动判据**）。
**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（六层全过）、
`liuyao/dev_tools/check.py`、根级三闸、`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、
`dsh-plugin` 自检全绿。

## 2026-10-30 第三百八十三批（八字）：**化格维度落地——《滴天髓·從化論》真/假两章；判据、见证门、断语外置一次做完**

**性质**：新判据实现（**分列读数，不进任何维度**）。读数不变。

### 一、这是什么

与从格并列的另一条主线，此前引擎**零建模**：《滴天髓》从化论分真、假两章，化格有自己的成立条件。
372 批把它列为「唯一还开着的真判据活」，本批做掉。

**判据四条（真化）**，逐条对着书：
① 合在**月干或时干**（书明写「在年幹不是」）；② 化神**通月令**（「化神要通月令」：
丙辛生於冬月、戊癸生於夏月、乙庚生於秋月、丁壬生於春月、甲己生於四季）；③ 日主**绝无一毫生扶**
（「日主孤弱無氣…絕無一毫生扶之意」）；④ 不遇**印、劫、官**之干（「不遇壬癸甲乙庚（印，劫，官）」）。
**假化**：「日主孤弱，而遇合神，不能不化，但有暗扶日主，如合神虛弱，則化不真」。

### 二、两处必须记下来的判据细节（都是书逼出来的，不是选口味）

1. **根只认本气**：书证「如甲日主，生於四季…乃為化得真」，而四季（辰戌丑未）里甲只得**中气**余根
   （辰中乙、未中乙、戌中丁、丑中己）。若把中气也算根，「甲日生四季化真」这条书证就**永远不成立**
   ——与书直接矛盾。故 `yougen` 只取 `hid[:1]`。
2. **年干作合不算**：「在月時上作合，（在年幹不是）」。故合只在月干／时干上取。

### 三、落点

| 层 | 改动 |
|---|---|
| 内核 `kernel/yishu_core/common/relations.py` | 新增 `STEM_WUHE_HUA`（甲己土／乙庚金／丙辛水／丁壬木／戊癸火）与 `wuhe_hua_element()`；**化气五行是干支关系不是学科口径**，按 §二 放内核，`sync_kernel.py --write` 重生两科 |
| `scripts/bazi_factors/congrge.py` | 新增 `hua_judge()`（四条真化要件 ＋ 两条假化） |
| `scripts/bazi_factors/strength.py` | 挂 `hua_kind/hua_type/hua_basis/hua_reason`（在既有 `strength` 段内，**不新增顶层键** ⇒ 不动 `layer_contract.json`） |
| `scripts/narrate.py` | 有化格时多一行「**化格**：化X·真化/假化（…）」＋章句 |
| `data/verdicts.json` | 新增「化格引文」组（断语字面量外置，§一.1） |

### 四、见证门：`[18]` 第五层 10/10

与岁运五式同法——用**书自己给的定义例**（「甲己化土生於四季」「丙辛生於冬月」……），
期望来自书的那句话，**不是从实现反推**，故不循环。10 条：真化 5／假化 4／不化 1，
另含四条负例（化神不得月令、日主有本气根、遇印劫之干、遇官杀之干 ⇒ 都不是真化）。

### 五、为什么不进评分

化格出的是**结构名**（真化/假化），与岁运五式、`dayun_cheng_bai` 同类：书把吉凶挂在「化神喜忌」
与「岁运」上；更根本的是——**化格命例在书里散在从象章末与假化章**，其中若干实为从儿格
（如「格成水木从儿」），要评分须先逐字取证并辨清类型。那是独立立批的活——
本批先把判据与见证做实。

**读数**：全无变化（tune 100.0／holdout 100.0、n=276、满分 275/276，各维命中数全同）。
金标准**措辞层**重记（机械层零漂移——`conclusion` 未变，化格字段挂在 `strength` 段内）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`check_dayun_cases.py`（五层全过）、
`liuyao/dev_tools/check.py`、根级三闸、`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、
`dsh-plugin` 自检全绿。

## 2026-10-30 第三百七十二批（八字）：**D 类「68 条未归类」逐容器定性清零——其中 26 条是真欠账：岁运和战五式未实现**

**性质**：归因收口（只改归类器，不改判定、不改语料、不改读数）。C 项 ①「流年维度零评分」的根因诊断。

### 一、为什么盯这 68 条

`[8] 语料接线` 长期打印「D 类 68 条**未归类**——是缺陷候选而非定论」。这条提示挂了很多批，
每次都被当成噪音略过；但它按定义就是「书证在库、却在 276 盘报告里从没出现过」的那批语料。
逐条点名后发现它们**混着两件性质完全相反的事**，混在一起时真欠账被数量淹没了：

| 桶 | 条数 | 性质 | 处理 |
|---|---|---|---|
| **F 判据未实现** | **26** | 书证在库、引擎**没有对应判据** ⇒ 论说句无处可引 | **真欠账**，逐容器登记理由 |
| **G 按题意取用** | **41** | 象层／十神取象按 `SKILL.md` 意图路由取用，不常驻默认正文 | 设计如此，不是漏 |
| **B 方法论登记** | 1 | `verdicts.json›看命口诀` 的 `_meta` 自明「不是判据、不进任何评分」 | 归入既有 B 桶 |
| **D 未归类** | **0** | — | — |

### 二、F 那 26 条里的真欠账：岁运和战五式

`ditian_sui.json` 的 `歲運論`（16 条）论的是**运与岁之间**的关系：

> 「如丙運庚年，謂之**運伐（剋）歲**。」「如庚運丙年，謂之**歲伐（剋）運**…得戊己以和丙者吉（**通關**）。」
> 「如子運午年，謂之**運沖歲**…」「如午運子年，謂之**歲沖運**…」

实测引擎：`liunian_ming_yindong` 只有「**流年 vs 命局**」的引动（`xing_ru_mu`／`san_he_ban_he`／
`zhi_chong_ming`），**没有「大运 vs 流年」那一层**（`grep 運伐|歲伐|運沖歲` 在 scripts/core 零命中）。
⇒ 这些论说句不是「漏接线」，是**没判据可接**。**登记为真欠账**。

`體用論`（8 条）与`寒暖論`（2 条）同理但性质轻：前者引擎以「用神／格局」表达体用、未单列体用判据；
后者与调候同旨（寒暖 vs 调候表），引擎走 `TIAO_HOU` 查表，不逐句引用论述。

### 三、这条诊断改写了 C 项 ① 的提法

此前把 ①「流年维度」记作「只有结构标签、零评分」，暗示是**接线**没做完。
实测结论相反：**先缺的是判据，不是接线**——

- 书里的流年文字，一半是吉凶叙述（`EVAL-PLAN` §2.2 已判不可评）；
- 另一半**结构性的**（运岁相伐／相冲／和解）**引擎根本还没实现**；
- 而已经实现的「流年 vs 命局」引动是定义式查表，给它评分只会长出恒满分项（369 批否掉格名扩样时同一条理由）。

⇒ ① 的正解不是「加个 `liunian` 维度打分」，而是**先实现岁运和战五式**（书证齐、可机械判），
再谈要不要评、怎么评。这条顺序错了，做出来的会是一个 100% 的空维度。

### 四、改动（只改归类器）

`dev_tools/corpus_wiring_report.py`：新增 `CLASS_F`／`CLASS_G`／`CLASS_B` 三张登记表（逐容器带理由），
`tot` 扩到 A–G 七桶，D 清零后打印正面结论而不是警报。**判定未变**：仍是 `[8]` 的「0 命中即红」，
本器只作明细（`check.py` 里 `corpus_wiring_report` 的输出一贯只打印、不参与判定）。

**读数**：无变化（不改案例、不改期望、不改引擎判据、不动分数）。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`liuyao/dev_tools/check.py`、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百六十九批（八字）：**C 项开工——先把「扩样」这条路修通，再量清楚它还剩多少**

**性质**：门禁口径修正 ＋ 可行性实测定案。**不改任何评分权重、不改任何案例内容、不动读数。**
本批只做一件必须做的事：让「扩样」在门禁里重新变成一件**可合入**的操作，并把「还能扩多少」量成读数。

### 一、修掉的硬阻塞：均分基线在 100 分位上把扩样锁死了

367 批把 holdout 均分基线抬到 100.0（按实测、只准前进）。副作用是：**此后任何扩样，只要新例有一例不过，
均分就跌破 100 → 判红 → 合不进来**。这与 AGENTS.md §四.2 明文相反（扩样应按**绝对命中数**判，不该被百分比拦）。

修法：`check.py` 新增 `BASELINE_N`（登记时的分母），均分只在**分母不变**时作门槛：

| n 与登记值 | 处理 | 理由 |
|---|---|---|
| `n < BASELINE_N` | **判红**「分母缩水」 | 用删案例过门是最省力的作弊路 |
| `n > BASELINE_N` | 均分**不作门槛**，只报 NOTE；门槛交给 `DIM_HITS`／`FULL_CASES` | 两者都是绝对量，扩样不会压低它们 |
| `n == BASELINE_N` | 照旧按均分判 | — |

**负例自证（真数据，跑完即撤）**：
① 注入 1 例必错新案 → `n=277`、均分 99.6%、**门仍绿**，且 `[7]` 点名 `ZZTEST1 0.0%（tiaohou:0/10）`；
② 删 1 例 holdout → **判红**「holdout 分母缩水 n=275（登记 276）」。
（顺带查实：check.py 的评测走子进程，split 里留着不存在的 id 会让 `evaluate.py` 直接 rc=1 报「评测未跑成」——
这条也当场验到了。）

### 二、量清楚还剩多少可扩：三书「明写判语」已采尽

C 项要求扩样。本批没有直接加案例，先把**可扩范围**量出来，结论是**书里能当标准答案的句子已经用完了**：

- **《滴天髓阐微》从格两章**：从象 15 例、假从 5 例，共 20 例；已入库 15（`ZC001–ZC015`）。
  从象章余下 6 例逐条读过，是**化格**（「合神真实，乃谓真化」「化象斯真」「化火斯真」），不是从格。
- **《子平真诠评注》**：全书 88 个唯一四柱串，已入库 36 例（20 个四柱）。余 68 例抽查后确认多为
  **论说举例**（例：「如壬申、癸丑、己丑、甲戌，本杂气财旺生官也，而以为乙亥时…皆误收格局也」）——
  只给格名、**不给成破**，按 §三.4「expected 必须指回原文」不能定 `pattern_cheng_bai`。
- **神煞名**：按 169 批口径（19 项基名＋变体名）重扫 336 例，仍只有那 5 例明写，0 新增。

⇒ 本库当前语料上 §四.2 说的「扩样会压低百分比」**暂时触发不了**；真正的下一步只有两条，
都要独立立批：① 开**化格**维度（化象 5＋假化 8，其中 `L5268` 实为「格成水木从儿」，须逐例辨类型）；
② 引入**新书**（须先做逐字回验）。两者都要动判据面，不该在收尾批里顺手做。

### 三、顺手排掉的假线索（省下一批的探查成本）

- 从象章「未入库 6 例」初看像漏采，逐条读后确认是化格；`ZC007` 四柱与 dz 版逐字一致
  （我第一遍的块检测把 4995 那例的年份错位成 4996，属检测器的问题，不是数据问题）。
- 「格名（`pattern` 的名 8 分）」看似可扩（章节即格名），实测 `第41章论伤官` 10/10、`第45章论建禄月劫` 11/11
  引擎与章节完全一致——**它本质是定义式派生**（月令＋透干），补进去只会长出又一个恒满分项，
  按第一百六十八批的教训不做。

**读数**：全无变化（`tune` 100.0／`holdout` 100.0／n=276／满分 275/276）。本批不改案例、不改期望、不改权重。

**全门复验**：`bazi/dev_tools/check.py`（39 项，含两次真数据负例）、`liuyao/dev_tools/check.py`、
根级三闸、`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百六十八批（八字）：**把 367 批「没做」的三项结掉——清例、从格真假收口、调候覆盖率复核；门禁补「满分例数」堵四舍五入**

**性质**：语料口径变更（清例）＋ 判据落地 ＋ 门禁加严。**三项均属 367 批自己登记为「待裁/等书证/待复核」的尾巴**，
本批按「能解的按书证解、不能解的把边界写成读数」逐条收口。

### 一、清例（367 批登记为「须另批裁定」的那笔）

367 批查出 2 组同考点双建（`MT042≡MT529`、`MT046≡MT540`：同书·同逐字引文·**同命盘**），
当时只登记进 `dup_ledger.json`、不动分母。本批裁定清例，按 **#39 既定口径「留最小 id」**：

- 删 `MT529`／`MT540`（保留 id 更小、注释更完整的 `MT042`／`MT046`），`bazi_classical_cases.json` 338→**336**，
  holdout 278→**276**；`dup_ledger.json` 重生后 `dup_groups=0`、台账清空。
- **属口径变更、新旧不可比**（§四.4）：删掉的两例原本都是满分例，分母与均分同时变动。
  这不是「删案例让分数好看」——两例的内容与保留的那份逐字相同，删的只是重复计数。

### 二、从格真/假：收掉 ZC015，ZC014 证否结案

- **新增判据「天干层有气印比」**（`congrge.py::dry_yinbi_youqi`）：印比透干 ＋ 其五行得月令（旺/相/休）
  ＋ 坐支**有效五行**生我或同我（三合局内按局五行——三合只化根、不化生）⇒ 仍算「有微弱生扶之意」⇒ **假从**。
  书证：《假从》任注「局中虽有劫印，亦自顾不暇」「虽有比劫印绶生扶，而…」；反面对照 ZC002「戊土虽生犹死」、
  ZC003「一点庚金临绝」——印比死囚者书仍作真从。
- 读数：15 例真假定性 **13/15 → 14/15**（`cong_ge` 13/15→**14/15**，93.3%），零回归。
- **代价如实登记**：同一判据另把 **15 例不带 `from_type` 期望**的从格由真从改判假从
  （MP158/164/356/382、MT023/465/488/489/538/539/544/546/560、ZP005/036）。书文对它们未定性，
  故**不构成读数变化**，也不得据此声称「修对了」（§四.7）。金标准 `weak_zhengguan` 正是其中之一。
- **ZC014 仍判真从而书判假从，且已证不可由该类判据修复**：ZC003 与它的印比局部配置逐项相同
  （同一颗庚金、同坐寅、同在寅月、同被丙火克）而书判相反，任何只读（印比干/坐支/月令）的判据必错一例。
  缺的前置是「从神纯度／日主与从神生克方向」，未立。此为**结案**，不是待办。

### 三、报告措辞：别让 basis 与盘面自相矛盾

此前真从一律挂「绝无一毫生扶」，可 ZC002/ZC003/ZC014 干上明明有印比。新增断语
`从格引文.yinbi_wuqi`＝「透干印比无气，不作生扶论（《从象》书例：戊土虽生犹死／一点庚金临绝）」，
在「真从且有透干印比」时改用它。（断语仍外置 `data/verdicts.json`，代码只留算法——§一.1。）

### 四、门禁：`[7]` 新增「满分例数」与 `FULL_CASES` 下限

holdout 均分现在打印 100.0%（真实 99.99x），**一个回落只要不足以压过 99.95 就完全静默**——
本仓已踩过两次同型坑（第一百六十八批丢 214 例、365 批恒真新维度静默长出，均分都一位未动）。
故把「pct==100 的例数」也写成绝对量下限（holdout **275/276**、tune 60/60），并在 `[7]` 输出里
点名未满分的例（现为 `ZC014 98.1%（cong_ge:3/4）`）。分母涨不会压低它，与 §四.2 同口径。

### 五、调候覆盖率复核（367 批列为「待复核」的 B 项）

「117 条未引全部落在不可达格／可达 97/120」这句**在本库文档里找不到出处**。按实跑重测：
表内 **110 格**中 **105 格**有案例带调候期望（111 例＝tune 60＋holdout 51）；缺的 5 格
(丑丁)(丑己)(酉丁)(酉己)(子己) **全部是季节总论兜底格**（`exact_paragraph:false`、`via=*(season)`，
登记自标「过泛慎用」），其中 4 格有案例可补、1 格无案例。
**不补**：这 5 格的引擎表值与期望同出一句季节总论，补进去测的是「提取回路」不是「判断」，
且 15 例季节兜底格已在册全中——补格等于往分母塞 5 个必然命中。结论登记进 `EVAL-PLAN.md` §五，**不再作为待办**。

### 六、读数（含口径变更声明）

| 项 | 367 批 | 368 批 |
|---|---|---|
| holdout n | 278 | **276**（清例 −2） |
| holdout 加权均分 | 100.0（＝99.986） | **100.0（＝99.99x）**，满分例数 **275/276** |
| holdout `tiaohou` | 53/53 | **51/51**（分母随清例 −2） |
| holdout `cong_ge` | 13/15 | **14/15（93.3%）** |
| `[22]` 全库 | 414 例／412 考点／2 组在册重复 | **412 例／412 考点／0 组／判准冲突 0 组** |
| tune | 100.0（`tiaohou` 60/60） | 不变 |

**新旧不可比**（分母与适用数同时变）。**引擎能力的变化只有 1 例带书证**（ZC015）；其余全是分母与
答案键层面的调整，**不得读作提升**。

### 七、金标准与回归定点重记（附理由）

`golden.py capture` 与 `tests/regression_test.py` 的 `1984-12-08 08:00` 指纹同批更新。
**A/B 逐字段实测**：临时回退新判据后对拍 `conclusion` 全字段，变化只有 `verdicts[2]` 的
`label`（从官杀·真从→假从）与 `basis` 两处，`pattern`/`strength`/`strength_score`/`useful_gods`/`dayun` 全同。
`narrate` 措辞指纹未动（72b4802cb4065f96）。

### 八、未做，及为什么

- **C 项（流年维度／扩样／六爻侧欠账）本批未动**：三项都要动 `WEIGHTS` 或评分面，
  按 AGENTS.md §四.4 与 CONTRACT.md §七 须先改契约再动代码，属独立批次，不在「收尾」范围内硬塞。
- **ZC014 不改**：见第二节，已证不可由该类判据修复，强行拟合即 §四.3 禁止的私有规则。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`liuyao/dev_tools/check.py`、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿。

## 2026-10-30 第三百六十七批（八字）：**holdout 余量核实——4 例失配里 2 例是答案键写错（非引擎），2 例从格边界实测结案**

**性质**：语料校正 ＋ 门禁补洞 ＋ 欠账结案。**引擎判据一行未改**，`narrate` 未动（golden 指纹零漂移）。

**起因**：上一轮交办的清单把 4 例 holdout 失配（ZC014／ZC015／MT042／MT046）判为「引擎缺陷」。
按要求先核实再动手，实测结论与此不同——**2 例是数据缺陷，2 例是不可由通用规则修复的边界**。

### 一、核实到了什么（先查证据，再决定改谁）

1. **MT042／MT046 不是引擎错，是答案键错**。三条独立证据同向：
   - **书文侧**：`qiong_tong_bao_jian_dz.dz.txt` 源L622「九月戊土当权，**不可专用丙**，先看甲木，次取癸水」——
     MT042 期望记「主丙」，与原文「不可专用丙」**直接相反**；源L887「十月庚金…**非丁莫造，非丙不暖**」——
     MT046 期望记「佐甲」，系误读下句「丁甲两透」的**成格组合**（用神句只点名丁、丙）。
   - **表源自证**：`data/tiaohou_quotes.json` 的 `9戊`／`10庚` 两格本来就登记 `main=甲 assist=癸`、
     `main=丁 assist=丙`（`via` 分别为「先看X次取Y」「非X莫造Y不」）。该文件是 `TIAO_HOU` 的**上游**，
     引擎表由它生成——故此处是「答案键 vs 表源」，不是「答案键 vs 引擎」。
   - **库内同案反证**：同一书、同一句引文、**同一命盘**（同日同时刻）在库里还有一份 `MT529`／`MT540`，
     期望正是甲/癸、丁/丙。即**正确读数本来就在库里**，不是本轮现造的。
2. **同一盲区另有 2 组**：`MT020/MT482`（四月丙火）、`MT026/MT498`（六月丙火）同引文同命盘，
   差异只在「只记主神」与「主神+佐神」。这两例的期望**并不错**（少记键＝N/A，§三 规则 1 允许），
   但 `note` 写的「佐神原文未单列」是**假事实**——原文分别有「得庚发水源」「取庚辅佐」。改注不改期望。
3. **为什么两道门都没拦住**：`[22]` 的判重键是（书·逐字引文·**判准**），把 `expected` 算进身份，
   于是「同一句书证配两个互斥答案」被当成两个不同考点、双双放行。**这是门的洞，不是人的疏忽。**
4. **ZC014／ZC015 是另一回事**：见第三节，实测证明不是「调一下阈值」能收的。

### 二、改了什么

1. **校正 2 份写错的期望**（＋2 份假注释）：
   | id | 旧期望 | 新期望 | 书证 |
   |---|---|---|---|
   | MT042 | `tiaohou.main=丙` | `main=甲, assist=癸` | 源L622「不可专用丙，先看甲木，次取癸水」 |
   | MT046 | `main=丁, assist=甲` | `main=丁, assist=丙` | 源L887「非丁莫造，非丙不暖」 |
   | MT020／MT026 | 期望不动 | 只改 `note` | 源L220「得庚发水源」／源L254「取庚辅佐」 |
2. **`[22]` 新增第二条判据「判准冲突」**（`check_case_dupes.py::conflicts`）：
   同书·同逐字引文下，**同一 `expected` 叶键出现 ≥2 个不同取值**即判红并点名到 id 与取值。
   刻意只认「同键异值」——「少记一个键」是如实留空（N/A），不算冲突，否则会把粒度差误伤成错误。
   负例自证两件（§四.8）：同引文 丙 vs 甲 必判红；同引文 壬 vs 壬/庚 不得误伤。
   **另做真数据负例**：把 MT042 改回「主丙」的临时副本喂给本门，实测 rc=1 且报
   `tiaohou.main=丙←['MT042'] vs 甲←['MT529']`，撤掉即回绿（临时目录，未落盘）。
3. **`data/cases/dup_ledger.json` 登记 2 组**（`MT042≡MT529`、`MT046≡MT540`）：
   同一考点被早期 MT0xx 批次与后期 MT4xx/MT5xx 批次各建一份，校正后重复随之显形。
   **清例（每组删 1 份）属口径变更、须另批裁定，本批不动分母**（台账 `_comment` 已写入该约束）。
4. **`check.py` 的 `DIM_HITS` 随实测上调**：holdout `tiaohou` 51 → **53**（§四.2 只准前进）。

### 三、ZC014／ZC015：把「约数」换成实测，并证明其一不可修

`congrge.py` 的灰区①此前写「改读任一层生扶使 ZC001/ZC005/ZC010 三例反吐，净 −1，故不改」。
该记载**实测不符，已作废**：

- 实际翻转的是 `ZC002/ZC003/ZC005/ZC009/ZC010` **五例**（+2 −5，净 −3，15 例命中 13→10）；
  `ZC001` 根本没有印比透干（戊丙丙 全是财伤），不会翻转。
- 另测四种更细读法，15 例命中 9／9／11／12，**没有一种超过现行 13**。
- **ZC014 不可由「印比自身状态」修复（有反例的证明，不是没试）**：`ZC003` 与 `ZC014` 的印比局部
  配置逐项相同——同一颗庚金、同坐寅、同在寅月、同被丙火克——而书判 ZC003 真从、ZC014 假从。
  任何只读（印比干／坐支／月令）的判据对二者返回同值，故必错一例。要分开只能引入日主与从神的
  生克方向，而该线索在 15 例里与「从官杀→假」高度重合（6 例从官杀中 5 例假，唯一反例 ZC005 因
  支全金局），样本不足以立判据，强立即过拟合（§四.3）。⇒ 按「读得懂、不能机械判」结案，
  缺的前置是**从神纯度／日主与从神生克方向**这一层。
- **ZC015 单独看可收**（+1、15 例内零回归），但同一判据会把 10 例**无书证**的从格由真从翻成假从，
  全书无文可验对错 ⇒ 按「改了会动 10 例、却一例都验不了」**不落码**，登记为「等书证」。

### 四、读数（引擎未动，变化全部来自答案键校正）

| 项 | 旧 | 新 |
|---|---|---|
| holdout 加权均分 | 99.5 | **100.0（打印值＝99.986 四舍五入）**；仍有 2 例不满分、最低 98.1 |
| holdout `tiaohou` | 51/53 | **53/53** |
| holdout `cong_ge` | 13/15 | 13/15（不变，即那 2 例不满分） |
| tune | 100.0（`tiaohou` 60/60） | 不变 |
| `[22]` 全库 | 405 例＝405 考点、0 冗余组 | **414 例／412 考点／2 组在册重复（净多余 2）**，判准冲突 0 组 |

**口径声明（必读）**：**新旧均分不可比**——2 例的判准被改正，旧 99.5 里含 2 个写错的答案；
这不是「提升」，**引擎能力一格未变**。反向也要说清：均分现在四舍五入显示 100.0，**不等于「全对」**，
`cong_ge` 仍有 2 例、真实均分 99.986。谁若为了让这个 100.0 好看去放宽判据或改答案，就是 §三.4 与
§一.3 明令禁止的自证——本批把这句话写在这里，是因为本批恰好造出了「看起来满分」的读数。

**全门复验**：`bazi/dev_tools/check.py`（39 项）、`liuyao/dev_tools/check.py`、根级三闸、
`devkit/sync_devkit.py --check`、`plugins` 构建＋自检、`dsh-plugin` 自检全绿（见交付记录）。

## 2026-10-30 第三百六十六批（八字）：**收口校勘——批号/编号冲突修正、两处陈旧口径、冗余收敛、分发产物重建**

**性质**：校勘与收口（不新增判据、不改评分面、不改读数）。起因是对 365 批做一轮完整复查，
查出四类问题，全部当场修掉。

1. **编号冲突（365 批自己引入）**：门 `[18]` 的 docstring 早已用 ①–⑤ 标注各层，其中 **④＝方向唯一**
   并写明「④ 是本器存在的主要理由」；365 批却把新的空档核验段标成「④」，docstring 里又写
   「第六至八层」「⑥／⑦」——三种说法并存。**统一为 ⑥**，改遍 8 个文件（门内 3 处 + 外部引用 6 处：
   `evaluate.py`×3、`check.py`、`CONTRACT.md`×2、`EVAL-PLAN.md`、`README.md`、`rule_registry.json`）。
2. **两处陈旧口径（非本批引入，复查时暴露）**：① `evaluate.py` 原写「`shensha`／`dayun` 两维
   0 例带期望」——`shensha` 自 169 批起已 5 例书证回填，改为「`dayun` 一维 0 例」并注明缘由；
   ② `EVAL-PLAN.md` 步 6 单元格仍写「待书载起运岁数入册后整维接入」，与 365 批的结项结论**相抵**，
   改为「不注 + 已证回填不可行」，与本表末注一致。
3. **冗余收敛**：365 批把同一组证据（338/0/9/52/51-51/99.5）在 8 处写了全文。现定
   **`docs/EVAL-PLAN.md` §五 末注为唯一详版**，其余各处只留结论与指针（`evaluate.py` ⑥ 段压到
   14 行、`CONTRACT.md` §六 压到 9 行、`README.md` 压到 4 行、`check.py`/`check_dayun_cases.py`
   注释与 `rule_registry` 注同步缩短）。除本条登记外，上述各文件逐项净减，事实一条未删。
4. **分发产物过期（真缺陷）**：365 批改了 `bazi/scripts/` 与 `data/rules/` 却未重跑打包，
   五家插件 `engine/` 里的 `dayun.py` 仍无 `judge_dayun_cheng_bai`；`dsh-plugin` 自检 [8]
   当场判红（「已过期：bazi/data/rules/rule_registry.json、bazi/README.md，引擎 2/149 文件过期」）。
   已 `node plugins/scripts/build.mjs` 重建，五家分发包均含新函数，`plugins/selftest.mjs` 七段
   与 `dsh-plugin` 自检全绿。
   - **操作规程（写进本批以免重犯）**：`bazi/README.md`、`data/rules/*.json` 都在分发包体内，
     故顺序必须是「**先改完 → 再 build → 再自检**」；build 之后再动这些文件，包体立刻过期。
   - 环境注记：本次 build 在 `gemini-plugin/engine` 处被安全删除器拦下（`trash` 操作 aborted），
     导致 gemini／yan 未被更新；清掉该 gitignore 产物目录后重建即通过，非代码缺陷。

**读数**：`tune` 100.0／`holdout` 99.5 及各维命中数不变（本轮不触碰任何 `expected`）。

**全门复验**：`bazi/dev_tools/check.py`、`liuyao/dev_tools/check.py`、`check_dayun_cases.py --selftest`
（11 负例）、根级三闸（批次／文档索引／根文档引用）、`devkit/sync_devkit.py --check`、
`plugins/scripts/selftest.mjs`、`npm --prefix dsh-plugin run selftest` 全绿。

## 2026-10-30 第三百六十五批（八字）：**行运维度结项——「回填主评分语料行运键」实测判定不可行，空档改为被监控的边界**

**性质**：口径结项（governance/scope closure），**不改引擎、不改评分面、不改任何分数**（§四.7 读数不动属预期）。golden 指纹零漂移（本批未碰 narrate）。

**起因**：363 批关闭裁决层后仍留一条尾巴——「要把运层真正纳入评分，前置条件是把主评分语料
`bazi_classical_cases.json` 回填行运键（`expected.dayun_direction`／`dayun_start_age`，实测 0/338）」。
本批按此推进，实测发现该前提**不成立**，于是把它从「待办」结项为「不可行（已证）」，并把证据
做成机械可重跑的读数，防止下一批又从头怀疑同一个 0。

**三条证据**（均由门禁 `[18]` 新增第⑥段 `corpus_gap_check` 现场重跑，非一次性断言）：

1. **书文侧无书证**。决定性语汇（`顺行|逆行|顺排|逆排|顺布|逆布` ＋ `起运|交运` ＋
   `[0-9一二三四五六七八九十百]+岁.{0,4}(行|起|上|交)运`）扫 338 例 `source_quote+note+location`
   全文 **0 命中**；广义「运」字仅 9 例，逐例登记语境（MP064「庚运夺魁」吉凶断语、MT011「运用相生」
   常语、MT019/MT023/MT034/MT045/MT497 只言方位、ZC012「运根拔尽」、ZP003 徐注转述），**均无干支、无岁数**。
   书源全库侧亦只有命例级方向 1 处（《滴天髓阐微》「此造运用逆行」；按「此造/此命/一造…顺行|逆行」
   定向检索，全库唯此一条），另有《千里命稿》源L258-279 的 4 个方向教学例（只给年、月柱，无日时）
   与源L294-322 的 2 个起运算例（给日期不给四柱，且「甲子年」在该书跨 60 年无法定公历）——都不成可评命例。
   神峰通考／三命通会的 39～67 处「顺行/逆行」经抽查全属**歌诀与起例**（「甲日子提为印绶，顺行不似
   逆行高」论格、五虎遁／命宫／长生起例），不是某一造的方向。
2. **起运对「四柱-only」案例本就不可评**。52 例书只给四柱、无公历的案例，引擎 `start_age`
   **全部等于同一个占位值**（实测唯一值集合大小＝1）——四柱无公历即无「距节气日数」，起运无从折算。
   即便将来补到书证，这类案例也拿不出可比对的引擎值。
3. **顺逆不能靠定义式回填**。顺逆是「年干阴阳×性别」的唯一定义（`ming_tables.dayun_direction`）；
   按 AGENTS.md §三.4 定义式例外把 338 例全填上，等于让该项恒真、零信息——那是自证，不是评测。

**实测代价（本批一次性对照，临时副本，未落盘、不改案例文件）**：把 52 例带显式四柱的案例按定义式
填上 `dayun_direction` 后 —— `dayun` 维 holdout **0/0 → 51/51（100%）**、tune **0/0 → 1/1（100%）**，
而均分 holdout **99.5**、tune **100.0** 一位都没动。即：一个恒真的 100% 新维度可以完全静默地长出来，
没有任何读数会报警——与第一百六十八批「少 214 例而均分四舍五入不动」同型，只是方向相反
（那次是**丢**数据看不见，这次是**加**自证看不见）。防它的不是分数，是 `[25]` 的 0/0 锁。
复现：读主案例集 → 对 `pillars.year` 存在者写 `dayun_direction(年干, 性别)` → `evaluate --ids <holdout>` 对照。

**改动**（八处同步，证据细节以 `docs/EVAL-PLAN.md` §五 末注为准，其余各点只留结论与指针）：

- `dev_tools/check_dayun_cases.py`（门禁 `[18]`）新增第⑥段 `corpus_gap_check`：扫主语料全文，
  断言 ① 决定性语汇命中＝0（命中即判红并要求「必须按书证回填」）；② 广义「运」字案例集合与
  `YUN_NEAR_MISS` 登记表**逐格相等**（多一例＝新增未登记语境判红；少一例＝登记漂移判红）；
  ③ 四柱-only 案例的起运取值唯一值个数＝1（若将来引擎真能算，本项判红提示口径须重判）。
  `selftest` 增第 10、11 个负例（「顺行＋五岁起运」假案例必被要求回填／近失登记漂移必被抓），
  现 11 个负例全部被抓。
- 口径回写：`eval/evaluate.py` ⑥ 关账段、`dev_tools/check.py`（`DIM_HITS` 注释：
  **不设下限是对的，不是漏设**）、`data/rules/rule_registry.json`（`ming.dayun` 注，状态维持
  `mechanical_regression`）、`docs/EVAL-PLAN.md`（摘要 + §五 末注）、`CONTRACT.md` §六、`bazi/README.md`。
- 顺手清掉两处陈旧口径：`evaluate.py` 原写「`shensha`／`dayun` 两维 0 例带期望」（shensha 自 169 批起
  已 5 例）；`EVAL-PLAN` 步 6 单元格原写「待书载起运岁数入册后整维接入」（与本批结项结论相抵）。

**读数**：`tune`／`holdout` 加权均分与各维命中数**一格未动**（本批不触碰任何案例文件的
`expected`；`[25]` 维度适用数锁仍为 `dayun` 0/0）。这不等于「跑了没事」——是**本批的设计目标**：
把「没做」与「不可做」分开，且不允许用无书证的回填把 12 分变成自证。

**全门复验**：`check_dayun_cases.py --selftest`（11 负例全抓；主语料空档读数 0 例／9 例登记／
起运占位唯一值 1 个）、`check_dim_lock.py --selftest`（0/0 未变）、`check_rule_registry.py`、
`check_layer_contract.py --selftest`、`check_source_readings.py`、`tests/smoke_test.py`、
`dev_tools/check.py` 全绿。


## 2026-10-30 第三百六十三批（八字）：**行运成格变格裁决层落地——关闭第九十三批起的「行运成格变格」欠账**

**性质**：能力建设（capability），不是调参、不是 bug fix。**golden 机械层零漂移**（只动 narrate 措辞层，已 capture 记入 digest；评分未动、指纹不动）。

**起因**：`eval/evaluate.py` 与 `docs/EVAL-PLAN.md` 长期登记的「运层成格变格裁决层缺失」欠账
（第九十三批登记为「可验收欠账」）。书《子平真诠评注》源L325 逐字「命之格局，成于八字，然配之以运，
亦有成格变格之要权。其成格变格，较之喜忌祸福尤重」明确把成格变格之权延伸到行运，但**只给方向、
不给量级与优先序**；主评分语料 `expected` 带行运字段 0 例 ⇒ 接「裁决」若写进评分面即把未验证机制凑分，
故此前故意不做。本批以**分列读数**形态落地，不抵触护栏。

- **新增 `bazi_factors/dayun.py::judge_dayun_cheng_bai`**：遍历完整大运表，对每步依据
  `dayun_ming_yindong` 已逐字回验的结构引动标签，判定 **成格引动／变格引动／填实引动／守局** 四类
  （每类带书据 basis，复用 `yindong_relations` 各机制源行）。**只做结构命名、不赋吉凶分、
  不覆写本命格局成败结论**——纯分列读数（CONTRACT §五-bis 同型：运层是结构读数，不是判决）。
  判定只看机制 kind，不重新推导本命格局；书未给优先级，故 verdict 保留触发的所有类别（可多类并存）。
- **接入 `analyze` 输出** 新键 `dayun_cheng_bai`（layer_contract.json analyze.allowed 增、batch 362→363）；
  `narrate` 行运引动段内增【行运成格变格】分列读数（注明不覆写本命结论、不批吉凶）。
- **扩容见证集**：`data/cases/bazi_dayun_cases.json` 的 7 例（DY004/007/008/009/010/011/012）
  增 `成格变格` 期望（与既有 ENGINE_EXPECT 机制同批核验）；`dev_tools/check_dayun_cases.py` [18]
  扩展校验「引擎裁决类别 == 见证集登记类别」（8 处一致），selftest 增第 9 个负例
  （塞不符期望必被抓）。
- **契约同步**：CONTRACT.md §四 八字 analyze 顶层键 27→28、§五-bis 增 `dayun_cheng_bai` 裁决层说明、
  §六 登记「行运成格变格欠账 363 批关闭」（裁决层不另立 [40]，由扩展后的 [18] 守同一批见证集）；
  `tests/smoke_test.py` ANALYZE_KEYS 增 `dayun_cheng_bai`；
  `dev_tools/check_dim_surface.py` NON_SCORED_SECTIONS 登记「行运成格变格」不评分理由；
  `eval/evaluate.py` 与 `EVAL-PLAN.md` 更新「裁决层仍无」为「363 批以分列读数落地」。
- **全门复验**：`check.py` 全绿（[3] narrate 措辞漂移已 capture 记入 digest）；
  `check_layer_contract.py --selftest`、`check_dayun_cases.py --selftest`（9 负例全抓）、
  `check_source_readings.py`（153/153 逐字命中、0 真欠账）均通过。

## 2026-10-30 第三百六十二批（八字＋六爻）：**象层上线——宫位与六亲这两条线此前整条缺**

**性质**：能力建设（capability），不是调参、不是 bug fix。起因：断八字除卦理外还有**象分析**，
而八字侧的宫位与六亲实测为 0——四柱、十神、五行计数全在盘面里，正文却从不出现
「哪一柱是哪一门亲眷／哪一段人生」。素材在、能力不在，原有门一条都拦不住（键面合规、
评分未变、指纹不动）。**golden 机械层零漂移**（评分未动），措辞层漂移来自新增【象上看】段，
已 capture 记入 `narrate_drift_log`。

- **新增 `scripts/xiang.py`** ＋ 数据源 `data/xiang_layer.json`：
  - `gongwei` 宫位象：年为根（祖上/父母宫，主少年）／月为苗（父母兄弟宫，主青年）／
    日为花（日干自身、日支夫妻宫，主中年）／时为果（子女宫，主晚年），各带时限与身位。
  - `liugin` 六亲象：**五类**反查内核 `LIUQIN_TO_SHISHEN`（唯一真源，不在模块里抄表）；
    **子平分野**按性别（男命正财为妻、女命正官为夫），传统歧异处（官杀为子女孰为子孰为女）
    两说并记、不代古人裁决。
  - `zangfu` 五行脏腑象：偏盛/偏弱/缺失，取自 `bing_yao.element_counts`（同源不另算），
    **象意提示、非医学诊断**——交付面强制带此声明。
  - **不借道叙述层私表**：narrate 的 `liushen_image.json`／十神行事表（铁律一）不在读取范围。
- **正文与插件出口**：`narrate.py` 增【象上看】段（无素材整段不出）；
  `plugins/mcp/tools.mjs` 的 `baziValue` 增 `xiang`。
  `dev_tools/check_dim_surface.py` 的 `NON_SCORED_SECTIONS` 登记「象上看」的不评分理由
  （§六 要求「看到的没在评」必须说明，不许沉默）：象是素材不是判据，可进眼睛不可进分数。
- **新门 `[39] 象层门`**（`dev_tools/check_xiang.py`）：三象齐备且每块 `basis` 非空／
  六亲性别分野真生效（定盘 甲辰·己巳·甲子·辛未：男命月干正财应「妻」、女命时干正官应「夫」）／
  评分侧（pattern.py、bazi_factors/*）禁读 `xiang`、`xiang` 不得进 `WEIGHTS`。
- **新读数器 `dev_tools/xiang_coverage.py`**：5 定盘 × 男女 = 10 盘；三象 10/10；
  5/5 定盘男女六亲口径均有差异（比劫的兄弟/姐妹亦按性别分列）。
- **契约**：`data/rules/layer_contract.json` 接收 `xiang` 与三子键，`batch` 310→362；
  `tests/smoke_test.py` 的 `ANALYZE_KEYS` 接收 `xiang`；`CONTRACT.md` 新增
  **§五-bis 象层：象与断的分界**（象在 analyze 产出／象不进断／象目带出处／象不冒充成绩）。
- 六爻侧同批的对应改动见 `liuyao/docs/CHANGELOG.md` 第三百六十二批。

## 2026-10-30 第三百五十九批（八字）：**评测层物理搬迁至 `eval/`——两科隔离形态对齐**

**性质**：refactor（行为保持）。零引擎、零数据、零评分改动；八字 golden 双指纹零漂移。

- `git mv bazi/scripts/evaluate.py bazi/eval/evaluate.py`，新增 `bazi/eval/__init__.py`；
  `scripts/evaluate.py` 改为纯 re-export 兼容 shim（入口自带 UTF-8 守卫，保留 `main()`
  分发）。旧命令 `python scripts/evaluate.py ...` 仍可用；新命令/文档统一写 `python eval/...`。
- 调用方同步：`dev_tools/check.py` 的存在性断言改 `eval/evaluate.py`；
  `eval_selftest.py`、`corpus_reports.py` 子进程改走 `eval/`；`baselines`／
  `check_dim_lock`／`check_dim_surface`／`eval_unique_keys` 仍 `import evaluate`，
  由 shim 星号导出与 `__getattr__` 代理维持原属性面。
- `check_case_isolation.py`（源 `devkit/shared/`）：`PHYSICAL` 检测改为「`eval/` 内
  有 `evaluate.py` 或 `case_runner.py`」；八字因此进入**物理隔离档**（14 模块 0 触达），
  正面断言只要求 `evaluate.py`（有 `case_runner` 的科才加验）。liuyao 行为不变。
- `plugins/scripts/build.mjs`：`DEV_ONLY.bazi` 排除 `scripts/evaluate.py`（包内无 `eval/`，
  随包会 import 失败）；`selftest.mjs [2]` 的「shim 未随包」断言扩到两科。
- 文档：`bazi/README.md`、`docs/EVAL-PLAN.md`、根 `CAPABILITY.md` 的复现命令改 `eval/`；
  `AGENTS.md §一.2` 改为「两科均已物理隔离」，白名单档仅留作未来新科过渡判据。
- 复验：`python bazi/dev_tools/check.py` 全绿；八字 golden **fda7/3512 零漂移**（40 例）；
  `python eval/evaluate.py --help`、`python scripts/evaluate.py --help` rc=0；
  full ledger 40/40；`node plugins/scripts/build.mjs`＋`selftest.mjs` 全绿；
  `sync_devkit --check` 11 件同源。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-30 第三百五十八批（八字）：**EVAL-PLAN 与实测对齐——shensha 5 例／holdout 99.5**

**性质**：docs（口径更正）。零引擎、零数据、零评分改动。

- `docs/EVAL-PLAN.md` 两处旧真值按实测改正：
  ① 「`shensha`／`dayun` 仍 0 例带期望」→ `shensha` **5 例**（169 批神煞书证回填，
     holdout 5/5、`check_dim_lock` 锁死，仅算薄覆盖）；`dayun` 仍 0 例、整维 N/A；
  ② holdout 加权均分 **97.6%／门内基线 ≥96.6** → **99.5%／基线 ≥99.5**（308 批实测；
     163 批的 97.6 保留为历史注记）。表内「上表 holdout 97.6」与「96.6 是现行下限」
     两句同步改正。
- `bazi/README.md` 同款旧句改正：96.6 是 2026-10-10 快照期下限，现行基线 99.5。
- 依据：`bazi_classical_cases.json` 338 例 `expected` 键频实测（shensha 5、dayun 0、
  pillars/ten_gods/hidden_stems 214、tiaohou 113、pattern_cheng_bai 36、cong_ge 15）；
  `python bazi/dev_tools/check.py` 的 `[24]/[25]` 实测锁 `shensha holdout 5/5`。
- 复验：`python bazi/dev_tools/check.py` 全绿；`check_doc_refs.py` 0 死链；
  full ledger 40/40（无读数变化）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-30 第三百五十六批（共享门）：**`check_case_isolation` 两档化——八字仍白名单**

**性质**：shared gate（行为保持）。零引擎、零数据、零读数改动。

- `devkit/shared/check_case_isolation.py` 按科有无 `eval/` 自动选档：六爻走**物理隔离档**
  （实现必须在 `eval/`，`scripts/` 零白名单）；八字无 `eval/`，继续 346 批**白名单档**
  （`scripts/` 下 evaluate / case_runner / build_portal_assets 允许读 `data/cases`）。
  八字 13 模块 0 触达，行为与判据均未变。
- 修正共享 docstring 的路径写法：原写 `eval/case_runner.py`，在八字科是死链，
  `[11]` doc refs 首跑判红（436 条引用 1 条不存在）；改为「`eval/` 内文件名」后
  434 条引用 0 条不存在。
- `sync_devkit.py --write` 分发 11 件；`[37]` 同源门通过；`python bazi/dev_tools/check.py`
  全绿。详见同批 `liuyao/docs/CHANGELOG.md` 第三百五十六批。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十三批（全仓）：**跨科共用契约信封 schema 落地（§3.6 关闭；八字侧同步）**

**性质**：schema＋shared gate。零引擎、零数据、零读数改动。

- 新增 `devkit/layer_contract.schema.json`；`devkit/shared/check_layer_contract.py`
  增 `validate_contract_envelope()` 零依赖信封校验（含 3 类负例），并由
  `sync_devkit.py --write` 分发到两科 `dev_tools/`。
- 八字 `check_layer_contract.py --selftest` rc=0：chart 9/analyze 26、4 条禁边、
  「信封 schema 通过」。
- 详见同批 `liuyao/docs/CHANGELOG.md` 第三百五十三批；`CONTRACT.md §四/§七` 同批回改。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十八批（八字）：**bazi README 回改 308 批读数（pattern 100.0／外部 62）＋根级文档同步**

**性质**：docs。零引擎、零数据、零读数改动。

- `bazi/README.md` 的判断维×常数段仍停在 187 批旧读：`pattern 80.6%／p=0.727 未达显著`、
  `外部 53 集`。308 批已实测 **pattern 100.0%（36/36，配对 b=9 c=0，McNemar p=0.004，
  已显著优于常数）**，339 批外部集扩样后为 **62 例**。本批按 308/339 实测回改，
  **不是新提升**（旧值保留为历史注记）。
- `GOVERNANCE.md`：八字 43 的 `build_siku_dz.py` 已随 345 批入库，clean clone 不再是 42；
  `ARCHITECTURE-PLAN.md` V9 改五 job（344 批新增 ledger）、V12 改 40 项/full bad=0、
  V13 改「327–329 六路径已补交」。
- 复验：`python bazi/dev_tools/check.py` rc=0；`readout_ledger.py` full **bad=0/40**；
  `check_root_docs.py`／`check_docs_index.py`／`check_batch_num.py` 全 rc=0。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十七批（全仓）：**329 批结构分层体检 10 项 triage（八字侧只读结论）**

**性质**：docs。零引擎、零数据。

- 329 批登记的 10 项结构体检条目已逐项复核：§3.1/§3.2/§3.3 复核不成立（0 模块级 import 环、
  [32] 零反向依赖、`effects.py` 导入名全在 `classical_enhancements.__all__`）；
  §3.4 部分成立（10 组同名，5 组跨模块重复另批）；§3.5 成立（白名单隔离，物理搬迁待办）；
  §3.6 部分成立；§4.1 体量成立（step5 已补 docstring）；§4.2/§4.3/§4.5 为设计或无可测分母，结案。
- 详细证据与处置表见同批 `liuyao/docs/CHANGELOG.md` 第三百四十七批；`CONTRACT.md §六-2` 销账，
  `AGENTS.md §一.2` 按“白名单隔离”实况改写。
- 复验：`liuyao/scripts/step5.py` docstring 不动行为，`liuyao golden verify` 双指纹零漂移。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十六批（全仓）：**`check_batch_num.py` 落地——八字 CHANGELOG 批号纳入根级门**

**性质**：root gate。零引擎、零数据改动。

- 根级 `devkit/root/check_batch_num.py` 已挂 CI `root-gates`：读两科
  `CHANGELOG.md`＋`CHANGELOG-HISTORY-INDEX.md` 的标题批号，与 `git log` 的「第N批」
  对账；允许名单从 `readout_ledger.py` 的 `SETTLED_ORPHANS` 单源读取。
- 实跑：标题批号 151、提交提及 158、未结案孤儿 0；负例五类全过。
- 详见同批 `liuyao/docs/CHANGELOG.md` 第三百四十六批；`ARCHITECTURE-PLAN §五.5` 欠账关闭。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十五批（八字）：**《三命通会》校订件补交入库 ＋ 抓取/校订链复跑 ＋ 报告元数据口径修正**

**性质**：content＋tooling＋docs。把 327–329 批一直留在工作区、导致干净 HEAD 判红的
三命通会文件正式落库；零引擎、零评分口径改动。

- **补交文件**：`data/sources/sanming_tonghui_siku.dz.txt`（1,419,789 字节，
  sha256 `47028eb5…`）、`data/sources/sanming_tonghui_siku.provenance.json`、
  `dev_tools/build_siku_dz.py`、`dev_tools/diff_siku_sanming.py`（改读校订件、章名顶格切分、
  `_meta.siku_file` 改 `.dz.txt`）、`dev_tools/scan_siku_gaps.py`（改读校订件、【】注文统一）、
  `docs/SANMING-SIKU-COLLATION.md`。
- **可复跑实测**：`fetch_siku_sanming.py` 重新抓取 12 卷，raw 1,467,204 字节／sha256
  `2d070238…`；`fetch_siku_sanming.py --check` rc=0；`build_siku_dz.py --check` rc=0
  （校订件 1,419,789 字节／sha256 `47028eb5…` 与重算一致）。
- **报告口径修正**：原底部注记把 `.meta.json` 说成“旧命名、应改 `.provenance.json`”，
  与抓取链实际契约相反——`.meta.json` 是抓取侧车（gitignore），`.provenance.json` 是
  入库真源；`build_siku_dz.py` 读前者写后者。注记已按实改写。
- **干净 HEAD**：此前 `[11]` 判红（`scan_siku_gaps.py:6` 指向旧路径）与账台
  `governance 42≠43` 均因这批文件未提交；本批落库后 clean worktree 复跑见下。
- 复验：`python bazi/dev_tools/check.py` rc=0；clean worktree `bazi check.py --fast`
  与 `readout_ledger --quick` 均 rc=0；`diff_siku_sanming.py`／`scan_siku_gaps.py`
  实跑产出可重现报告读数。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十四批（八字）：**账台 pattern 期望回填 80.6→100.0（308 批实测漏登）**

**性质**：docs/账台。零引擎、零判据、零读数改动。

- `readout_ledger.py` 的 `bazi(tiaohou96.2 pattern80.6 …)` 行仍停在 187 批旧值；
  308 批已实测 pattern **100.0%（36/36，McNemar p=0.004）** 并写入 CAPABILITY／check.py，
  但账台期望漏改。本批按 308 实测回填为 `pattern100.0`，并删掉该函数里一行重复正则
  （`th` 死变量）。
- `readout_ledger.py` full 实跑：**bad=0，已跑 40/40**；quick 实跑 rc=0，输出明确
  「已跑 34/40，跳过 6」（不再自称「全账」）。
- `python bazi/dev_tools/check.py` 全量 rc=0（本批未改八字门）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十三批（八字）：**主 CHANGELOG 再瘦身——只留 10-29，3 节标题并入索引**

- 把 10-27 及更早的 3 个 `##` 节移入 `docs/CHANGELOG-HISTORY-INDEX.md`（标题保留、批号不变）。
- 主文件 43KB→38KB；索引 14.7KB→15.2KB；连同 342 批删除的 240KB 归档，
  八字历史记录总量由约 294KB 降至约 53KB。
- 复验：`check_docs_index` 51 份、`check_root_docs` 0 死链、`check_doc_refs` 0 死链、
  `check.py` rc=0、`readout_ledger --quick` rc=0。

## 2026-10-29 第三百四十二批（八字）：**历史记录精简——删除 240KB 归档全文，只留逐批索引**

**性质**：docs（用户令"历史记录文件可以删减，精简为主"）。零代码、零判据改动。

- 删除 `docs/CHANGELOG-ARCHIVE.md`（239,520 B／81 个 `##` 标题）；
- `docs/CHANGELOG-HISTORY-INDEX.md` 改为**逐批标题索引**：原 81 节保留
  `## 日期 第N批` 标题（截 120 字），14.7KB；
- `readout_ledger` 的「登记×提交」扫描面改扫 `CHANGELOG-HISTORY-INDEX.md`；
  `check_doc_refs` 的 EXEMPT 同步；
- `DOCS.md` 八字 15→14、全仓 54→51；`AGENTS.md` 历史记录政策改为"索引为主，不保留全文"。
- 复验：`check_docs_index` rc=0（51 份）、`check_root_docs` rc=0、
  `check_doc_refs` rc=0（432 条/0 死链）、`dev_tools/check.py` rc=0、`readout_ledger --quick` rc=0。

## 2026-10-29 第三百四十一批（全仓文档收口·续）：**已关闭/已完成内容从活文档删除**

- `docs/EVAL-PLAN.md` §五：删除已完成步 1–5、7，只留未闭合的步 6（关闭登记在本卷 CHANGELOG）；
  节名改为「剩余落地项」。
- `CONTRACT.md` §六 删除已关闭原 4/5/6；`CAPABILITY.md` 删除已更正虚构欠账；
  `GOVERNANCE.md` 删除已结案案例清单；`AGENTS.md` 删一条措辞沿革；`dsh-plugin/README.md`
  删已修踩坑表。
- 复验：`check_root_docs` rc=0、`check_docs_index` rc=0（54 份）、`dev_tools/check.py` rc=0、
  `plugins/selftest.mjs` 全绿。

## 2026-10-29 第三百四十批（全仓文档收口）：**删除已执行的派发件＋把总方案压成完成记录**

**性质**：docs。零代码、零门禁判据改动。

- 删除 `DISPATCH.md`（26 个位全部执行完毕）；`ARCHITECTURE-PLAN.md` 压成完成记录
  （D1–D3、最终形态、完成台账、V1–V15 实测、偏差/欠账、显式不做），已修好的问题描述
  与 25 张卡的逐步指令从正文删除。
- `DOCS.md` 根级 8→7、总 55→54；`README.md`／`AGENTS.md`／`CONTRACT.md` 指路同步。
- 实测：`check_root_docs` rc=0、`check_docs_index` rc=0（54 份）、两科 `check.py` rc=0。

## 2026-10-29 第三百三十九批（八字，A5-1）：**按 GOVERNANCE 五档过存量——本批无降档、无删除**

- 实跑 `python dev_tools/governance_map.py`：八字 **43 脚本｜blocking 26｜nightly 0｜
  ondemand 7｜build 8｜tool 2｜未分类 0｜表中有序实无 0**（旧快照 36/25/0/5/4/2 已过期）。
- 登记 6 个存量未分类脚本：`build_dts_cases`/`build_t2s_table`/`build_siku_dz`/
  `fetch_siku_sanming` 归 build，`diff_siku_sanming`/`scan_siku_gaps` 归 ondemand
  （后三者属外部三命通会会话，**只登记不改文件**）。
- **降档/删除判据逐条对照 §一**：blocking→nightly 需连续一季 0 判红＋负例可跑＋CHANGELOG
  具名，本仓无按工具的季度判红台账；ondemand 删除需两季 0 使用记录＋活引用检查，同样
  无台账。故本批**不降不删**，只让地图不再报"未分类"。
- `readout_ledger.py --quick` 同步改期望并注明理由：governance `37→43`（含外部会话的
  `build_siku_dz.py`，clean clone 在其提交前为 42）、八字案例分母 `53→62`（语料扩样）、
  `bazi.external n53→n62（33/54）`；`tracked×ignore` 由 9 回 0（9 份历史 wikitext
  显式 negated，新增抓取件仍不入库）。账台实跑 **bad=0/全账 39**。

## 2026-10-29 第三百三十七批（八字，A3-1/A3-2）：**core 产物显式化 ＋ data/cache 层**

- **A3-1**：`.gitattributes` 给两科 `core/yishu_core/**` 标 `linguist-generated`（D1=C：
  仍入库，不 gitignore）；`kernel/sync_kernel.py` 新增 `--standalone <科> --out <目录>`，
  产出 `core＋scripts＋data/rules/golden＋data/*.json` 的独立可拷目录。
  实测：`python kernel/sync_kernel.py --standalone bazi --out %TEMP%\yi_bz_standalone`
  rc=0；`python …/scripts/chart.py --help` rc=0 且 cp936 下产物可按 UTF-8 读；
  负例：手改 `core/yishu_core/runtime.py` → `--check` rc=1 并点名，`--write` 后回绿。
- **A3-2**：`.gitignore` 加 `**/data/cache/`；`scripts/evaluate.py --save` 改落
  `data/cache/eval_*.json`；`dev_tools/corpus_reports.py` / `corpus_wiring_report.py` 与
  八字 `check.py` 的 eval_file 同步改读 cache。**迁移 0 个 / 落空 0 个**（330 批已清空盘上
  旧产物，本次无存量可迁；改写的是写入点与读取点）。
  关键验收：清空两科 `data/cache/` 后 `python dev_tools/check.py` 仍 rc=0（现场重生成
  13 个 eval 文件），`git ls-files '*/data/cache/*'` = 0。

## 2026-10-29 第三百三十六批（八字，A2-B）：**CHANGELOG 三件套瘦身 ＋ 契约文档修正 ＋ 八字侧欠账审计**

**性质**：docs。零引擎行为、零评分口径、零键面改动。

### 一、三件套（照 330 批六爻同款做法）

| 文件 | 内容 | 实测行数 |
|---|---|---|
| `docs/CHANGELOG-ARCHIVE.md` | 原文**全文，一字未删**（`read_bytes`/`write_bytes` 保字节） | 2500 |
| `docs/CHANGELOG.md` | 最近窗口：2026-10-27 及之后的条目 | 460 |
| `docs/CHANGELOG-HISTORY-INDEX.md` | 归档 71 节的逐节一句话（标题截 90 字） | 76 |

### 二、`CONTRACT.md` 三项修正

1. §三件套/§四/§五 的 `data/rules/layer_contract.json` → `<科>/data/rules/layer_contract.json`
   （根目录没有此文件，A4 诊断）；
2. §二 改为「四段职责的通用边界」，新增 **§二-bis 各科剖面**：六爻 = `step1`–`step5`；
   八字 = 单体 `analyze.py`（`bazi_factors.strength_and_pattern` → `dayun_table`/`liunian_table`
   → `conclusion`），并写明八字**无**推演链对应物、不为对称而克隆；
3. §六 新增「八字侧契约欠账审计」7 行表：**新增欠账 0 条**，`trigram_interpretation` 与
   `reasoning_chain` 两项无对应物如实标 N/A。

本轮**未改键面/禁边**，故两科 `data/rules/layer_contract.json` 不动——§七.1 的三件套条件
未触发，已在 §六 结论行注明；两科 `check_layer_contract.py --selftest` 实跑均 rc=0。

### 三、验收

- `python dev_tools/check_layer_contract.py --selftest` rc=0（3 夹具 × 两段键面、4 条禁边）；
- `python dev_tools/check.py` rc=0（含 [37] 门禁同源、[38] tests）；
- 归档件行数 2500 = 原文行数（`wc -l` 口径见 handoff）。

## 2026-10-29 第三百三十五批（八字，A2-A）：**补 `tests/`（smoke ＋ regression）并挂 [38] 门**

**性质**：tests ＋ tooling。零引擎行为改动。

- `tests/smoke_test.py`：两条起盘入参路径（公历 datetime／书载四柱）× 四段
  （chart→analyze→narrate→render）都要有产出；只验接线，不验对错。
  键面直接取 `data/rules/layer_contract.json`（chart 9／analyze 26）。
- `tests/regression_test.py`：固定 3 例的四柱与 `conclusion` 规范化哈希（前 16 位）。
  四柱是定义式机械层（干支历唯一确定），指纹只作回归哨兵，不代表正确率。
- `dev_tools/check.py` 新增 **[38] 八字 tests**：任一测试 rc≠0 即判红。
  编号取当前最大号 +1（[37] 之后；[29]–[36] 在八字侧不使用）。
- 负例自证：把期望指纹改成 `deadbeef…` → `[38]` 判红并点名该例；恢复后 rc=0。

## 2026-10-29 第三百三十二～三百三十四批（八字，A1-1/A1-2/A1-3）：**门禁内核归并到 `devkit/`＋挂 [37]**

| 批次 | 内容 |
|---|---|
| 332–334 | 11 个同名门/器归并：7 个进 `devkit/shared/` 单一真源；`check_source_readings`／`golden`／`baselines`／`feedback_store` 两科逻辑不同，按 **kernel 变体范式**登记为 4 个变体（`shared/variants/<名>.<科>.py`），不伪造"合并成一份" |
| 334 | 两科 `check.py` 挂 **[37] 门禁同源**：手改共享产物、dev_tools 野文件（`_*.py`）、第二份异名拷贝都判红 |
| 334 | `devkit/MANIFEST.json`：`files.shared` 11 项、4 个变体、8 个共享门的两科现行编号（`gate_ids`） |

归并前后逐格对拍：两科 `check.py` 均 rc=0；`check_doc_refs` 检视数 781→774（差异为
`.wikitext/.meta/_diff` 非声明载体排除与迁出文件的引用），0 条死链不变。
**八字侧 `check_doc_refs.py` 的校勘豁免改动本属外部三命通会会话的工作区改动，
由 A1-1-06 以六爻 HEAD 版（已含同款豁免）为归并源一并落库，未替该会话提交其它文件。**

## 2026-10-29 第三百三十一批（八字，A0/A1-2）：**根级文档门与 `devkit/` 骨架**

- `devkit/` 建立：`MANIFEST.json` ＋ `sync_devkit.py`（`--write`/`--check`/`--selftest`），
  handoff 目录 gitignore；
- `devkit/root/check_root_docs.py`：扫根级 8 份 `.md`，**禁 basename 兜底**；上线实测恰判红
  `AGENTS.md:200/226/262` 与 `CONTRACT.md:94` 四处 `docs/CHANGELOG.md`，A0-3 修正后 rc=0；
- `devkit/root/check_docs_index.py`：原 `liuyao/dev_tools/check_docs_index.py`（[36]）上提到根，
  六爻 `check.py` 的 [36] 段位移除，编号空出不回填；
- CI 加 `root-gates` job（`sync_devkit --check` ＋两道根级文档门）。

## 2026-10-29 第三百二十九批（八字，兼全仓整理）：**四库本转成「校订件」真源形态（可入库）＋ 清掉 55 MB 垃圾产物 ＋ 承接《结构分层体检》的未决条目立案**

**性质**：content＋tooling（新增规范化脚本 ＋ 底本换形态 ＋ 全仓清理 ＋ 未决项登记）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、底本形态没按仓库约定走＝交付物不入库

`.gitignore` 第 23–30 行早已定调（commit 17c8407）：抓取/校对原始件（维基文库转写 `*.wikitext.txt`、
元数据 `*.meta.json`）与衍生比对件 `*_diff.json` **不入库**——**校订件 `*.dz.txt` + `*.provenance.json`
才是真源**；注释里甚至直接点名 `diff_siku_sanming.py`、`scan_siku_gaps.py`。
本批前半程把四库本留在抓取件形态，**等于交付物不入库**。

新增 `dev_tools/build_siku_dz.py`：抓取件 → 校订件（只动标记形态，正文与注文**一字不改**）——
`SK anchor` → 顶格章名行（981 个）、`SK notes` → `【】`（3,272 条，**与在库 dz 本同一套注文标记**）、
版式包装（`SKQS header/footer`、`poem/onlyinclude`、注释、页脚标记）删除。

**底本形态统一后对拍口径又简化一层**（注文标记两边一致，不必再靠归一化剥【】消解差异）：

| 读数 | 327 批 | 328 批 | **329 批（校订件）** |
|---|---|---|---|
| 逐字一致章数 | 180 | 319 | **328 / 765（42.9%）** |
| dz 本无此段 | 0 | 0 | **0** |
| 反向真脱漏候选 | 92 | 26 | **16** |
| 去注文后正文互相覆盖 | — | 76.4% / 88.5% | **92.9% / 89.8%** |

校订件：`data/sources/sanming_tonghui_siku.dz.txt`（483,593 字 / 1,419,789 字节）＋
`data/sources/sanming_tonghui_siku.provenance.json`（title=「三命通会（四库全书本）」，
与在库 dz 本的「三命通会」区分开，否则 `_source_titles()` 的 title→`.dz.txt` 映射会指错底本）。

### 二、文档整理：清掉 55 MB 垃圾产物

盘点发现全仓 593 个 `.md` 里**只有 61 个是源文档**，其余全是构建产物副本
（`plugins/{engine,skills,dist}` 与五个适配器各一份同一文件）。清理清单：

| 删除 | 体积 | 理由 |
|---|---|---|
| `scratch/dist-clone/` `scratch/yi-claude/` `scratch/yan-verify/` | 24 MB | 仓库/适配器副本，`build.mjs`／`publish.mjs` 可重建 |
| `plugins/dist/` | 15 MB | 发行树产物（`publish.mjs` 生成） |
| `liuyao/outputs/` `liuyao/scratch/` | 10 MB | 一次性报告与探针产物（`.gitignore` 已定） |
| `scratch/*.png|log|txt|json|py`（38 件） | 1.5 MB | 截图、日志、一次性探针 |
| `scratch/REVIEW-2026-10-27.md` | 12 KB | **自述不入库**（结论已拆进 CHANGELOG） |
| `scratch/release-notes-v1.0.0.md` | 4 KB | 已被 `dsh-plugin/README.md` 取代（后者口径章节更全：含 CI、随机期望、封存状态） |
| `scratch/incident-20261029/` `scratch/311/` | — | 1 例自检夹具与旧批产物 |

**保留**：`dsh-plugin/dsh-yi-divination-1.0.0.tgz`（发布包）、`scratch/` 目录本身。
**未动任何被 git 跟踪的文件**（`git status` 无 ` D` 条目）。清理后 175 MB → **120 MB**。

### 三、承接《结构分层体检》的未决条目（原件按 scratch 规矩不入库，此处只留条目）

2026-10-27 全仓审查（304 批过程稿）的未决条目，原件在 scratch 一次性区、按 AGENTS §六.1
「不另立台账」不入库；删除前把条目与出处登记在此，**链不断**：

| 条目 | 要点 | 状态 |
|---|---|---|
| §3.1 三条 import 环 | `effects.py:34` 引 `classical_enhancements` 三个私有名；`engine.py` 函数体内 5 处 import（192/378/388/402/419 行） | 未修，待复核 |
| §3.2 三处明确的反向依赖 | — | 未修，待复核 |
| §3.3 私有名当公共 API | 与 §3.1 同源 | 未修，待复核 |
| §3.4 同名函数并存 7 组 | — | 未修，待复核 |
| §3.5 评测层与交付层同目录 | `case_runner.py`（365 行）、`evaluate.py`（672 行）住在 `scripts/`，隔离靠 `check_case_isolation.py:34` 的**文件名白名单**——AGENTS §一.2 承诺的是「物理隔离」，实际是「名单隔离」 | 未修，待复核 |
| §3.6 跨科「共用契约」无 schema | — | 未修，待复核 |
| §4.1 三个 2,000 行级模块 | `liuyao/scripts/step5.py` 2,176 行、`classical_enhancements.py` 2,227 行；step5 连 docstring 都没有 | **仍成立**（329 批实测） |
| §4.2 两科结构不对称 | 同一份规程两种落地 | 未修，待复核 |
| §4.3 呈现层分裂成两套语言 | 六爻 HTML 在 Python（`render.py`＋`visualization.py`＋`core/report/html.py`），八字 HTML 在 Node（`plugins/mcp/report.mjs` 315 行） | 未修，待复核 |
| §4.5 文档覆盖不到一半 | 329 批源文档 53 篇 | 待复核 |

**已解决，不再列**：§4.4「分发副本没有同源门」——`plugins/scripts/selftest.mjs` **[1] 段现为逐字节同源门**
（含负例自证，329 批实跑全绿）。

### 四、门

八字全量门 ✓、六爻全量门 ✓、`plugins/scripts/selftest.mjs` ✓、`dsh-plugin` selftest ✓；
`fetch_siku_sanming.py --check` 哈希一致、`build_siku_dz.py --check` 可复跑。

## 2026-10-29 第三百二十八批（八字）：**修掉 327 批埋的四层口径缺陷（吞字＋漏转）＋ 全量扫描与注文集合比对：结论是「两本各有所取，必须并用」**

**性质**：content＋tooling（修脚本缺陷 ＋ 新增扫描脚本 ＋ 读数更新 ＋ 结论改写）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、327 批的口径有四层问题，其中两层是我自己的实现缺陷

| 层 | 问题 | 修法 |
|---|---|---|
| 一 | 全文正则 `\{\{SK anchor\|[^\n]*\}\}` **贪婪**匹配，吞掉同行 notes 与其后正文（40 行 anchor+notes 组合、400 行 notes 后接正文）→ 四库本**少归一化 7,506 字** | 模板取「`{{` 与其后**第一个** `}}` 之间的内容」 |
| 二 | 字表转换写成逐字 `tbl.get(c,c)`，而**注文是整段字符串** append 进缓冲的 → **注文内容从未被繁简转换**，四库本注文一直是繁体，与 dz 简体注文处处失配 | 字表用 `str.maketrans` 一次编译，注文按整段 `translate` |
| 三 | 注文标记两边形态不同（dz【】3,449 处 / 四库本 `{{SK notes}}`，原文含【】0 次）→ 注文边界窗口必然失配 | 两边统一剥掉【】 |
| 四 | 字表「以 dz 本字集消歧、歧义保留原形」是**净损失**（dz 是词组转换过的转录本：「乾坤」34 处保留「乾」、「天干」213 处用「干」；四库「乾」162 处 vs dz 49 处） | 改回 zhconv 逐字表（1,308 条），生成过程留档 `dev_tools/build_t2s_table.py` |

**只修第二层，逐字一致就从 120 章涨到 311 章**；四层修完 319 章。
**读数从 180 涨到 319，不是数据变好，是口径从四层缺陷里爬出来了。**

### 二、最终读数

| 读数 | 327 批 | 328 批最终 |
|---|---|---|
| 四库本归一后字数 | 427,265 | **434,771** |
| 逐字一致章数 | 180 | **319 / 767（41.6%）** |
| 局部差异章数 | 591 | 448 |
| dz 本无此段 | 0 | **0** |
| 反向真脱漏候选（抽样 289 窗） | 92 | **26** |
| 去注文后正文互相覆盖 | — | **四库→dz 76.4% / dz→四库 88.5%** |

### 三、结论再改一次：不是「一方选择性录入」，是「两本各有所取」

328 批中期的「四库本选择性录入」说法**作废**。最硬的证据是**注文集合直接比对**
（集合比对不受一字之差干扰，比窗口匹配可靠）：

| | 条数 | 字数 |
|---|---|---|
| dz 注文（【】） | 3,449（去重 2,669） | 126,288 |
| 四库本 notes | 2,504（去重 2,342） | 155,994 |
| 两本都有 | 1,776 | — |
| **仅 dz 有** | **893** | **50,753** |
| **仅四库有** | **566** | **81,562** |

**两本的注文各有对方没有的内容。** 再加：dz 正文多 4.2 万字（307,383 vs 265,235）。
故两本**互补、必须并用**——dz 本给正文与注文的**量**，四库本给**章节结构与注文归属**
（981 个 `{{SK anchor}}` 把归属标得清清楚楚，dz 本无此结构）。

### 四、全量扫描（新增 `dev_tools/scan_siku_gaps.py`）

不抽样，逐 12 字滑窗全量扫。**连续失配 ≥4 个 12-gram（跨度 ≥48 字）才算一段**——
一字之差只影响 11 个窗口，按单点聚合会把「字面差异」放大成「整段缺失」
（实测按单点判会得出 35% 连续失配，那是假象）。

结果：dz 有四库无 3,534 段 / 109,957 字（25.4%）；四库有 dz 无 3,413 段 / 108,915 字（25.1%）。
**双向几乎对称** → 剩余差异**主要是字面差异**（一字之差、生僻字、异体字），
**这份区段清单不可直接当缺失清单用**；唯一干净的缺失信号是注文集合比对。

### 五、两条硬校勘条目不变（脚本内自检）

- **E1** dz 本卷标「三命通**防**」18 处（应为「会」），四库本统一「三命通會」54 处；
- **E2** dz 本「著」仅 6 处、「着」52 处（四库本「著」36 处）——四库本「復著之述作」↔ dz 本「复着之述作」；
  **引用 dz 本时凡「著」字词不可直接采信。**

### 六、产物

| 文件 | 变化 |
|---|---|
| `dev_tools/diff_siku_sanming.py` | 归一化重写（四层修正）＋行映射＋反向逐条判定；`data/collation/sanming_tonghui_siku_diff.json` 随之重出 |
| `dev_tools/scan_siku_gaps.py` | **新增**：全量双向扫描 ＋ 注文集合比对 ＋ 正文覆盖率 |
| `dev_tools/build_t2s_table.py` | **新增**：字表生成脚本（**唯一需要 zhconv 的一步**，表入库后日常零依赖） |
| `data/collation/sanming_tonghui_siku_gaps.json` | **新增**：区段清单、注文集合比对、正文覆盖率 |
| `docs/SANMING-SIKU-COLLATION.md` | 重写：§二 四层修正记录、§五 注文集合比对、§七 两本怎么用 |

### 七、局限

全量扫描的区段清单**不可直接当缺失清单**（见 §四）；`present_but_differs`（49 条抽样）里
注文位置差与字面异文尚未逐条拆；两本都没有标点，断句责任在引用者。

## 2026-10-29 第三百二十七批（八字）：**《三命通会》四库本入册（12 卷）＋ 两转录渠道内容级对拍：查出 dz 本两处系统性转写缺陷**

**性质**：content（新增底本 ＋ 新增抓取/对拍脚本 ＋ 新增校勘报告）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、先弄清两底本是什么关系

在库底本 `data/sources/sanming_tonghui_dz.dz.txt` 开头是「钦定四库全书　子部七／三命通会　术数类五」
＋四库提要＋「乾隆四十四年九月恭校上」，每卷卷首还带四库版式标记
`<子部,术数类,命书相书之属,三命通会>`（全文 12 处，均单行内闭合）——
**它本身就是四库全书本**，只是经殆知阁渠道转录。

维基文库把同一底本按卷切成 12 页数字化，于是同一本书有了**第二条转录渠道**。
所以这批做的**不是版本校勘，是转录校勘**：差异即脱漏与转写处理之差。

### 二、新底本（`dev_tools/fetch_siku_sanming.py`，可复跑）

`data/sources/sanming_tonghui_siku.wikitext.txt`：卷01–卷12，**538,884 字 / 1,467,204 字节**，
字符级保存，一字不改（**无标点**，四库扫描版原文如此，卷首自注「加標點請另外建立頁面」）。
逐卷 sha256 与全文件字节 sha256 记在 `data/sources/sanming_tonghui_siku.meta.json`。

**元数据刻意不叫 `*.provenance.json`**：八字科 `check_source_readings.py` 的 `_source_titles()`
硬编码「`*.provenance.json` → 同名 `*.dz.txt`」，任何 provenance 都会被登记成「书名 → 底本文件名」。
本底本不是 dz 底本文件，登记成 provenance 会指向**并不存在的文件**，污染既有回验的书名映射。
故另起 `*.meta.json`，台账信息写在里面。

### 三、对拍口径（三道，写死在脚本里）

**行号体系不同，绝不能按行号对拍**（四库本 981 个 `{{SK anchor}}` 章节锚点，dz 本无对应锚），只做内容级：

1. **繁简**：四库本繁体、dz 本简体，按 `dev_tools/t2s_table.json`（1153 条）转成 dz 本字形。
   该表**以 dz 本字集为判据**消歧：字 c 若 dz 本同时含 c 与其简体形（歧义，如「乾/干」）则保留原形。
   比全局词组转换准——通用转换工具会把「乾坤」转成「干坤」（实测 65 处）。
2. **注文**：四库本夹注以 `{{SK notes}}` 独立标记、dz 本与正文连排，故对拍**含注文**
   （不取注文会把「排版差异」误报成「缺文」）。
3. **模板与标签**：`{{…}}`（notes/anchor 除外）、`<…>`、全角空格与换行一律去除，**不改一个字**。

### 四、结果（`data/collation/sanming_tonghui_siku_diff.json`，报告 `docs/SANMING-SIKU-COLLATION.md`）

| 项 | 结果 |
|---|---|
| dz 本**整段缺失** | **0 章**（四库本 771 个有实质正文的章，dz 本全部找得到） |
| 逐字一致 | 180 / 771（23%） |
| 存在字面差异 | 591 / 771（77%） |
| 反向（dz 本有、四库本无） | 293 个等距采样窗中 117 窗为四库本所无（候选脱漏，含大量**表格转文本顺序差**） |

失配窗按首尾 20 字各自是否命中分四类：`middle_dropped`（首尾都在、中段 dz 本没有，**真脱漏候选**，
11 例样本）/`tail_differs`/`head_differs`（多为一字之差）/`both_differ`（多为注文位置与表格换序）。

### 五、两条硬校勘条目（**脚本内自检**，底本一变即失效）

机器猜的配对噪声大（短前缀会把配对算到别处，实测随机配对一度盖过真差异；故只收公共前缀 ≥30
的对齐，且**不做抹平**——「乾/干」「著/着」这类**就是校勘结论本身**，抹掉等于把发现藏起来）。
下列两条是逐字比对原文后确认的，计数写死在 `dev_tools/diff_siku_sanming.py` 里：

- **E1　dz 本卷标误字**：dz 本「三命通**防**」**18 处**、「三命通会」20 处（同一卷标两形并存）；
  四库本统一作「三命通會」54 处。刻工/转录层错字，不是版本差异。
- **E2　dz 本「著」被系统性过度转成「着」**：dz 本「著」仅 6 处、「着」52 处。已核实例：
  四库本「復著之述作」↔ dz 本「复着之述作」；四库本「萬物皆炳然著見」↔ dz 本「万物皆炳然着见」。
  **引用 dz 本时，凡「著」字词不可直接采信。**

### 六、局限（别跳过）

本对拍是**机器初筛**，只指出「两本不同」的位置，**不判谁是正本**（按理校断字是人的活）；
对照文本按位置截取，可能有一两字错位，定位以行号为准；
「dz 本无整段缺失」**只覆盖四库本那 771 章**，反向 117 窗候选脱漏尚未逐条人工核，
现在就说「四库本更全」是过头的；两本**都没有标点**，凡需断句的引用，断句责任在引用者。

### 七、产物

| 文件 | 是什么 |
|---|---|
| `data/sources/sanming_tonghui_siku.wikitext.txt` | 四库本原文（12 卷，卷次有 grep 标记） |
| `data/sources/sanming_tonghui_siku.meta.json` | 出处、逐卷哈希、字节哈希、许可 |
| `dev_tools/fetch_siku_sanming.py` | 抓取脚本（`--check` 只验哈希） |
| `dev_tools/diff_siku_sanming.py` | 内容级对拍脚本（含校勘条目自检） |
| `dev_tools/t2s_table.json` | 繁简字表（以 dz 本字集消歧） |
| `data/collation/sanming_tonghui_siku_diff.json` | 逐章命中率、字面差异清单、校勘条目 |
| `docs/SANMING-SIKU-COLLATION.md` | 校勘报告 |

## 2026-10-29 第三百二十六批（八字）：**调候判据补进本体（新建 `bazi_tiaohou.md`，13 条逐字可回验）＋《滴天髓阐微》9 例显式标注命例入外部集**

**性质**：content（新建一篇判据文档 ＋ 新增抽取器 ＋ 外部集扩容 ＋ 一处登记表修正）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、本体：调候这一路此前**没有文档**

全库检索「调候」「穷通宝鉴」命中 **0 处**——而 `data/tiaohou_quotes.json` 里躺着 120 条
（10 日干 × 12 月）带主用／辅用／逐字引文的成品数据，引擎 `analyze` 也已出 `tiaohou` 维度。
**数据在、引擎在、判据不在**：会话里模型要讲「这个月生人取什么用」，没有可依据的成文判据，
只能靠通识补，那就是在编。

新建 `references/bazi_tiaohou.md`：

- 底本 `data/sources/qiong_tong_bao_jian_dz.dz.txt`（殆知阁本），引文一律以它为准；
- **异文明写**：120 条引文中只有 **30 条**能在 dz 本逐字命中，其余属异文或断行差异——
  **不拿两个版本拼一句话**；
- 十二个月各一条代表判据（逐字引文 + 行号），讲清三种句式的差别：
  「专用 X」是只此一路，「先取 X 次用 Y」有先后，「X 为君 Y 为臣」是配合不是备选；
- 三条读法：调候看**太过不及**不是「缺什么补什么」；**月令是提纲、日干是受体**；
  透与藏分量不同（方向 ≠ 已经有这个字）；
- 边界写死：调候≠命局总评；不据调候断吉凶；引用原文的「富贵双全」是**记录该书怎么判**，
  不是本库背书。

`dev_tools/check_source_readings.py --doc references/bazi_tiaohou.md` 实测：
**可验 13 条，逐字命中 13 条，判红 0，NOTE 0**。

### 二、验证集：《滴天髓阐微》扩容 9 例，且只收**人工认定**的

既有 `bazi_external_cases.json` 53 例是**人工构建**的，纳入规则是「任注**显式标注**衰旺类别者全收，
无显式类别词者剔除」。该书全书 513 个命造块里，带显式类别词的只有 69 条——逐条人读后，
**机器规则只能确认 12 条**，其余是两类误判：

- **主语不是日主**：「地旺极矣」「财官太旺」「木旺金衰」「劫刃太旺」「金水太旺」……把旺衰安在别的五行上；
- **成语与通理**：「旺者冲衰衰者拔」「衰神冲旺旺神发」「身旺者杀皆是官」——不是对本造的判断。

这两类混进来等于给引擎喂**假基准**，比不收更糟。所以本批的做法是：
**机器负责定位与自洽，人工负责认定，结论固化在脚本 `APPROVED` 表里可审计可复跑**——
每条写明「书里原话是哪一句」「归到哪一档」「为什么收」。12 条认定中 3 条与在册案例同四柱，
去重后**新增 9 例**（DT001–DT009），外部集 53 → **62 例**。

机器自洽门（不靠人判）：四柱竖排解析 → 判语「X日生／X日元」须与日干相符、「X月生」须与月支相符 →
原话逐字命中 → 公历由**内核历法反查**（穷举 1900–2100 逐日取四柱全同者）→ 与在册案例四柱去重。

**两处口径写死**：

- **datetime 的年份不是命例真实年份**（同一四柱在窗口内多解，取首个命中）。本集只作
  四柱级与强弱级校验，**不用于大运/流年判断**。
- **强弱分布偏斜是文本特征不是抽样偏差**：9 例里偏弱 8、中和 1——任注多言「病」少言「旺」。
  故本集**不可用于推断总体强弱分布**，只作逐例对拍与回归。

实测：`check_case_pillars.py` 合计 414 例、174 例可对账、**174 例与内核反算一致、0 判红**；
`evaluate.py --split external_holdout` 62 例，强弱对齐 33/54（report-only，不设门槛、非命中率），
新例确有分歧（DT001 书「日主本衰」→ 引擎判偏旺），**在真实检验引擎，不是凑数**。

### 三、顺带修一处名不副实的登记

`plugins/scripts/kb-docs.mjs` 里 `bazi/bazi_yue_shi_ge.md` 登记为「月支与格局」，
而该文件实际是**五虎遁／五鼠遁歌诀**（推月推时），与登记描述不符。按现文改登记，
不按登记改文。

## 2026-10-29 第三百一十九批（八字）：**三篇「读人」文档落地（六亲家宅／疾病体质／前事验盘）＋ 引文回验器支持多底本 ＋ 评测自检不再写真实案例集**

**性质**：content＋tooling（C1/C2）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、为什么做这一批

`bazi/references/` 此前只有四篇：十神术语、纳音、月支格局、接口速查——**全是"术语与口径"，
没有一篇讲"落到人身上怎么读"**。用户问"我跟我妈怎么回事""我身体哪块要留心""你先说我以前"，
模型手上只有盘面 JSON，没有判据，只能自由发挥，这正是铁律一最该防的空档。

本批补三篇，全部以**库内古籍**为据、逐字引文、可机器回验：

| 文档 | 解决 | 主底本 | 附底本 |
|---|---|---|---|
| `references/bazi_liuqin_gongwei.md` | 父母／配偶／子女／家庭氛围；星宫双参、五种「破」的关系语义、禁句表、三样不读（人数／性别／生死） | 命理探源 | 三命通会、神峰通考、滴天髓阐微、渊海子平 |
| `references/bazi_jibing_tizhi.md` | 体质倾向与关注部位；五行配脏腑、取伤重、虚实、相生亦生病；不诊断的硬边界 | 三命通会 | 渊海子平、五行精纪、千里命稿 |
| `references/bazi_qianshi_yanpan.md` | 「你先说我以前」与出生时辰校定；时刻切法、三件事验盘、已过往运只讲感受层 | 命理探源 | 滴天髓阐微、千里命稿 |

三篇共同的写法约束（写进各篇正文）：**只读关系质地与结构倾向，不读生死、不数人数、不判离婚、
不诊断**；古法原话里的"克"一律译成"张力"，并在文中给出禁句／改写对照表。

### 二、引文回验器升级：多底本（本批唯一的工具改动）

旧 `dev_tools/check_source_readings.py` 只认文档头声明的**一个**底本；锚点左边写着别的书名时，
整条锚被剔除并记「跨书锚点，无从回验」——而六亲、疾病这类题目天然跨书，
等于新文档一半引文落在门的盲区里，NOTE 还把盲区说成"已尽力"。

改动（`check_source_readings.py`）：

1. 文档可用 `附底本：data/sources/….dz.txt` 声明多本；锚点按**最近的《书名》**绑到对应底本逐字核，
   未声明的书仍只记不判（宁可显式说"没核"，不给假绿）；
2. 书名归一（`闡→阐`、`刪→删`、`淵→渊`、`黃→黄` 等），否则正文写简体《滴天髓阐微》会回落主底本，
   把一条正确引文判成"与底本不符"；
3. `bad` 键由行号改为 `(底本, 行号)`（两本书都有 L54，旧键会串）；
4. selftest 增**多底本正负例**：挂在附底本书名下的真引文必须命中，编造引文必须判红——
   没有这条自证，"支持多底本"只是措辞。

### 三、顺带修掉一个会毁数据的地雷（如实登记）

跑 `check.py` 时发现 `data/cases/bazi_classical_cases.json` 已被覆盖成一份
`（框架自检，非古籍）` 的夹具（338 例 → 1 例），导致 holdout 为空、评测门全线报红。

- **根因**：`dev_tools/eval_selftest.py` 把夹具**写进真实案例集**，再靠 `finally` 还原。
  进程被硬杀（超时／内存／终端关闭）时 `finally` 不执行，真实案例集就被永久覆盖。
- **恢复**：从版本库恢复（`git checkout --`），实测 **338 例／tune 60／holdout 278**，与 316 批登记一致；
  覆盖前的坏副本留档 `scratch/incident-20261029/`（不入库）。本批**未改任何评分口径**，不产生读数不可比。
- **修复**：`scripts/evaluate.py` 新增 `--cases`（缺省仍为主案例集）；`eval_selftest.py` 改为
  **夹具只走系统临时目录**，真实案例集全程只读，并加一道守卫——若发现案例集里残留自检夹具，
  直接报错并提示从版本库恢复，不再"备份坏文件再还原回去"。
  这也正是 AGENTS.md §四.8「自检夹具只走临时目录」的既定口径，本器此前是唯一违例。

### 四、读数（本批实跑）

- `python dev_tools/check.py` → **rc=0，28 节全过**；`[10] 书证行号逐字回验` 由 **101 条**增至 **140 条**，
  140/140 命中、0 判红；新增三篇分别 **12／19／8 条**全部逐字命中。
- `python dev_tools/eval_selftest.py` → 9 场景全过（夹具改临时目录后行为不变）。
- `python dev_tools/check_doc_refs.py` → 394 条路径引用 0 断链。
- 金标准指纹未动（本批不碰 `analyze`，`golden.py verify` 随 `check.py` 通过）。

### 五、开口（如实登记，未在本批解决）

- **本文三篇是"读法"，不是"新因子"**：六亲宫位、脏腑对应目前仍要模型从 `chart`／`analyze`
  已有字段里组合，没有独立的结构化输出。要变成引擎因子，须按 CONTRACT §四 加键（会动 golden 指纹），
  单独一批做。
- **多底本回验只在八字科**：六爻科的 `check_source_readings.py`（688 行）早已支持按《书名》解析，
  两科实现仍不同文；是否收敛成共享实现，留待内核/门壳统一批。
- **古症候名与现代病名的映射**：本篇只做到"系统"层，不做病名映射（需医学资质）。

## 2026-10-29 第三百一十六批（八字，六爻侧主批）：**内核降为生成物 + 删掉三个用不到的六爻模块（−874 行）**

**性质**：architecture（C2）。字节层不改行为：保留下来的文件与原文逐字节相同，只删未引用模块。

1. **内核改由 `kernel/` 生成**：八字收 10 个共用 + 1 个专用（`conflict_resolution.py`）+ 4 个在册变体，
   共 **15 文件**（原 18）。`core/yishu_core/` 从此是产物，由 `python kernel/sync_kernel.py --write` 写，
   手改会被六爻 `check.py` 的 `[35]` 判红。
2. **删除** `hexagram_texts.py`（591）／`calendar_check.py`（244）／`najia.py`（39）——AST 全扫确认
   八字侧无任何 import，却一直被塞进发布包。**`yingqi.py` 不删**：`core/yishu_core/feedback.py`
   有两处转调用。
3. **口径**：`AGENTS.md` §二 与根 `README.md` 的「17 同名 13 相同」改写成"单一真源 + 4 变体 + 产物"。
4. **读数**：`bazi/dev_tools/check.py` **rc=0**（28 节）；40 例指纹 `fda7482656967518`／
   `3512deff79fa1f72` 未动；holdout 99.5%（n=278）未动。

## 2026-10-29 第三百一十二批（八字，六爻侧主批）：**仅治理图补登记与读数归位，零引擎零判据**

**性质**：bookkeeping（承接六爻 312 批归位）。本批对八字只有两处副作用，逐条记：

1. **治理图补一条 curated**：`dev_tools/check_layer_contract.py` 系 310 批新增，当时未入 `governance_map.py` 的人工分类表，
   `--strict` 会判 UNCLASSIFIED。补后重生成 `docs/GOVERNANCE-MAP.json`：脚本 36→**37**、blocking 25→**26**；
   账台 `governance` 期望值随之改（57/36→58/37、blk 24/25→25/26），理由写在六爻 312 批条目里。
2. **无代码改动**：八字 `check.py` 28 节实跑 **rc=0**，40 例指纹 `fda7482656967518`／`3512deff79fa1f72` 未动，
   holdout 99.5%（n=278）未动。310 批的分层契约门在本批复跑仍绿（chart 9 键／analyze 26 键，禁边 4 条规则）。

六爻侧的 import 收敛、禁边还清、账台假阳性修复见 `liuyao/docs/CHANGELOG.md` 同批。
