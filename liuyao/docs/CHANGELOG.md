# 六爻 CHANGELOG

> **第三百四十二批精简**：`CHANGELOG-ARCHIVE.md` 全文已删除；更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)。下面历史条目若提到
> ARCHIVE／P0-INVENTORY，按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 51 节标题已并入索引。

## 2026-10-30 第三百七十一批（六爻）：**B 解析器两处缺陷修好——「窗口自证」与「卦宫前缀」；370 批的 5 条裁决由机械复核自动转为共识**

**性质**：解析器缺陷修复（根因）＋ 待裁清零。不改语料、不改期望、不改任何读数。

### 一、370 批判反了一条推论，本批更正

370 批把 B 记 null 归因为「句式缺口」。**修的时候才发现是窗口问题**：

```python
for j in range(lo, max(-1, lo - 40), -1):          # 旧写法：从验注行**自己**开始向上找
    if re.search(r"[干][支]日", lines[j]): win_start = j; break
```
验注行几乎总含「寅日/亥日」这类**应期用语**，于是循环第一次就 break 在验注行自身 ——
窗口退化成单行，卦名永远采不到。这是**判据在被判对象自己身上必真**的老病（AGENTS §四.8
「0 结果先怀疑路径」同族），不是句式不全。改写为「按卦名在哪儿定窗」的三级回退：
① 验注行自身含「得X卦」→ 该行即命例（林氏一行为多例）；② 否则向上找最近的**含卦名行**；
③ 都没有才退回旧的日行／三行窗。

### 二、补「卦宫前缀」文法

底本常把上下卦名冠在卦名前：「得**泽风**大过变**火风**鼎」「得**兑为泽**卦变**雷水**解」。
旧文法只认裸卦名，这类头整条采不到；窗口回退又会抓到**上一例**的头，把 K 的值记到 K+1 身上。
补两层前缀（`[乾坤震巽坎离艮兑天泽火雷风水山地]{2}` 与 `为[卦]`）。修前修后：

| | 修前 | 修后 |
|---|---|---|
| 双器共识 | 10/18 | **13/18** |
| 需人看分歧 | 8 | 5（**全部经原文逐字核实为 B 对**，已裁） |

### 三、5 条裁决（逐字取证，全判 B）

| 记录 | 原文 | 判 | 依据 |
|---|---|---|---|
| `yilin L1279` | 「且如子占父病，五月甲子日，占得观之益卦…后至乙亥日…果然父丧」 | **B**（应期亥） | A 的「子月戊午日/子」是本行后文另一命例的串味 |
| `zengshan L1798` | L1790「又得恒之大过」 | **B** | A 记「晋/无变」＋日期亦错 |
| `zengshan L2093` | L2086「得坎之井卦」＋L2093「果于酉日天变」 | **B**（三项全对） | A 取了上一例「得离卦不动」 |
| `zengshan L3213` | L3206「得需之大过卦」 | **B** | **此条原为「双器共识」——两器共同错了** |
| `zengshan L3338` | L3331「得大畜之益」 | **B** | 同上，共识掩盖的共同错误 |

⇒ **本轮最重要的读数不是「裁了几条」，是「共识率不能当正确率」**：`L3213`／`L3338` 在 370 批前
是 10 条 consensus 之一，而两器给出的卦名与日期**三项全错**。共识只说明两个解析器在同一处同样瞎。

### 四、两处工程护栏

1. **复核器不再冲掉已裁记录**：`recheck()` 每次重写 `restorable_recheck.json`，旧写法会把
   `decision`／`decision_basis` 一并抹掉，「人已经裁过」这件事在下一轮重跑后消失。
   现按 id 继承；B 若已变化，写 `decision_stale_b` 并在简报里挂 ⚠ 提示复核。
2. **简报 B2 按裁决面取数**：370 批的渲染把每条都印成「取 A」（硬编码），现按 `decision` 取 A/B。

**结果**：`ADJUDICATION-BRIEF.md` 待裁事项 76 → **73**（A10 B**0** C13 D15 E批35）；
B 类清零，5 条全部落 B2「已裁（逐字取证）」。

**读数**：无变化。**全门复验**：`liuyao/dev_tools/check.py`、`bazi/dev_tools/check.py`、根级三闸、`devkit --check` 全绿。

## 2026-10-30 第三百七十批（六爻）：**复部分歧 8 条裁掉 5 条——B 解析器是句式漏采，不是文本歧义**

**性质**：待裁项裁决（不改引擎、不改语料、不改任何读数）。C 项「六爻侧欠账」的第一笔。

**怎么裁的**：`ADJUDICATION-BRIEF.md` 的 B 类 8 条是 201 批 A/B 双解析器的不一致。逐条回原文看
**卦例头**（这是唯一能定夺的事实面），发现 5 条的「B 记 null」根本不是分歧：

| 记录 | 原文卦例头（逐字） | 结论 |
|---|---|---|
| L550 | L543「例：酉月辛亥日占求财得兑为泽卦变雷水解卦」 | A 对 |
| L561 | L554「例：巳月乙未日自占病得泽风大过变火风鼎卦」 | A 对 |
| L1581 | L1574「曾如辰月戊子日占小舟过关恐盘阻得水地比变泽山咸卦。」 | A 对（该头**不以「例：」开头**） |
| L1680 | L1673「如午月戊午日占何日雨得地风升变恒卦。」 | A 对 |
| L2084 | L2077「再占一卦。得离卦不动」 | A 对（**「得X卦不动」句式**，无变卦） |

⇒ B 的缺口是**句式**：只认「例：」前缀＋「得…卦变…卦」，遇到「曾如/如…得X变Y」「得X卦不动」就漏采，
于是把「解析不到」记成了「文本没有」。这类漏采会污染「双器共识」的可信度——共识率高不等于解析对，
只是两个解析器在同一种句式上同样瞎。

**改动**（三处，均在裁决面，不触碰语料与读数）：
1. `data/cases/restorable_recheck.json`：5 条 row 写入 `decision: "a"` ＋ `decision_basis`（逐字引文与行号），
   `needs_human` 8 → **3**；`_comment` 记明「本册仍不改毕业册状态、不写 expected」。
2. `dev_tools/adjudication_brief.py`：**已裁的 row 不再进待裁桶**，另立 `B2. 已裁 N 条（逐字取证）`。
   此前「裁过」与「没裁」在简报里长得一样，下一轮值守会把它们重新读一遍——这是重复劳动，不是谨慎。
3. 重生成 `docs/ADJUDICATION-BRIEF.md`：待裁事项 81 → **76**（A10 B**3** C13 D15 E批35）。

**留下的 3 条是真分歧**（都差在应期或卦名，且原文两说并存，需人裁）：
`yilin L1279`（应期 子 vs 亥）、`zengshan L1798`（晋/无变 vs 恒/大过）、`zengshan L2093`（离/无变/寅 vs 坎/井/酉）。

**读数**：无变化（本批不碰案例集、不碰期望、不碰引擎）。

**全门复验**：`liuyao/dev_tools/check.py`、`bazi/dev_tools/check.py`、根级三闸、`devkit/sync_devkit.py --check` 全绿。

## 2026-10-30 第三百六十四批（六爻）：**欠账清理——合绊反号、书源回验补门、假基准校勘**

**性质**：欠账清理（debt closure），不是调参。本批把此前挂着的多笔六爻欠账逐笔结案，
每条都按「先量出来、再有书据地改、最后钉门」的顺序走，未动任何外部集与调参读数。

### 一、合绊极性（本批唯一的行为变更）：`reg_02` 由红转绿，是引擎侧修的

- **缺陷**：`effects.analyze_day_month_bonding`（step5「日月合」）对**用神**无条件套
  《卜筮正宗》「用神合日切近有力、合月事必成就」记 **+0.5／+0.4**；而同一条合在
  step4 贪合忘生克里被判「用神被合绊，暂受阻滞」**−0.2**。两层反号、两边都进总分，
  于是**一条合绊净成 +0.3 加分项**。
- **书证**（《增删卜易》源L738 逐字，动静两式并列在同一句）：
  「静而逢合，谓之合起。动而逢合，合谓之合绊。」
  「爻静或与日月动爻合者得合而起。**即使爻值休囚亦有旺相之意**。」
  「爻动或与日月动爻合者谓之**动逢合而绊住，反不能动之意**。」
  ⇒「切近有力」是**静爻合起**的说法；用神自己动的时候是合绊，不适用。
  该函数早已对**忌神**做动静分计（第两百八十四批，源L1480/L738/L3152），
  **漏的是用神那一半**——本批补的正是那一半。
- **修法**：用神动逢日月合 → 计 0 并在 `bond` 里写明「合绊，减分见 step4，此处不重复计」；
  用神静逢日月合 → 维持 +0.5/+0.4，**且不因用神休囚打折**（底本明说「即使爻值休囚亦有旺相之意」，
  别拿「枯木难生」去改这一条——那是另一句、指另一种情形）。
- **效果**：reg_02（占升官·官鬼亥水动而逢日辰寅合）
  总分 **+0.18 平吉 → −0.32 凶**，合《黄金策》古典断凶；**古籍回归 18/19 → 19/19**。
- **代价**：金标准 288 例中 **4 条**机械读数变化（`大过·占父病` ×2、`蒙·占伯何日回` ×2，
  其中仅 `蒙|[0]` 一例 verdict 翻档），**措辞指纹未动**；
  tune 97.9／64.7／1.53、holdout 90.2／50.0／1.6 与**全部外部集读数零变化**。
  已 capture 记入 `data/golden/digest.json` 的 `drift_log`。
- **新门 `[40] 合绊极性门`**（`dev_tools/check_bond_polarity.py`）：128 路探针（64 卦 × 静/双动），
  判据三条——动用神逢合不得计正／静用神逢合不得计负／step4 与 step5 对同一条合不得反号。
  **已在旧代码上验过齿**：回滚 `effects.py` 后本门实抓 3 条（大有·占讼、蒙·占伯何日回 ×2）。
  同源先例：`step4.py` 4.3c（进退神曾在两层重复计分且符号反向，忌神越化进分数越高）就是同一类病。

### 二、书源指针：`[12]` 补上行号形态回验，两条 `verified=false` 结案

- `devkit/shared/check_rule_registry.py` 原先只验 `quote_in_data`（`#` 形态）与
  `quote_in_code`，**从没验过 `source.quote_in_source`（`底本:行号` 形态）**——
  这正是 `liuyao.yimao_shibafafa`、`liuyao.huozhulin_luandong` 两条长期挂 `verified=false`
  的原因：不是不可验，是**没有门去验**。本批补上该形态（逐字比对指定行内容），并加两式负例。
- 补上的当天就抓到真错：`liuyao.shen_yao_activation` 标着 `verified: true`，
  引文却写作「祸**祸**方凭身象」，底本《易隐》L217 逐字是「祸**福**方凭身象」——已改正。
- 两条 `verified=false` 逐字回验 4/4 命中底本行，翻为 `true`。**六爻注册表现 88/88 指针可回指。**

### 三、假基准校勘：`reg_09` 改「方向不可评」

- `reg_09` 自注「**仿古**从格案例」，`key_reasoning` 谈的是 `special_pattern` 字段存在性，
  是**功能测试**不是古籍占验，`classical_verdict="凶"` 无书据 ⇒ 属**假基准**
  （照 162 批 `reg_07` 先例）。给 `RegressionCase` 增 `expected_direction=None` 一档：
  方向与区间两条断言整体跳过，但**实测值照写进 `reasoning_diff`**，读数不因「跳过」而消失。
- 同时把 `[4]` 门那条写死「reg_07 系仿古自设前提」的注文改通用——`reg_07` 早已转绿，
  注文却留着，等于给新红灯预先发免责声明。

### 四、杂项

- `[11] 文档活引用可达性` 的假红收口：`check_rule_registry` 新增的负例文件名
  `__no_such__` 被当活引用扫出来。在 `NEGATIVE` 白名单补该词（与「病历/负例」同因：
  判红等于逼各门把负例样本删掉，是反向激励），不靠放宽病历口径蒙混。
- 账台 `readout_ledger`：**八字措辞指纹登记值过期**（bazi 已 capture 363 批「行运成格变格」段，
  账台期望值仍停在 362 批的 `baa1`）⇒ 报分家。按 `bazi/data/golden/digest.json` 的 drift_log
  归因回补为 `168c`（机械层 `fda7` 未动）。六爻侧同步回补机械指纹 `6f70→3a19`。
  账台现 **40/40 全部对账一致**。

## 2026-10-30 第三百六十二批（六爻＋八字）：**象层上线——把「象分析」从素材变成能力**

**性质**：能力建设（capability），不是调参、不是 bug fix。起因是深度审查的判据：
断八字、断六爻，除了卦理还有**象分析**；而本仓的象此前**素材在、能力不在**——
八卦类象表、卦辞爻辞、六神属性、四柱十神都在盘面里，正文实测命中数为 0
（六爻 1087 字正文里 类象/方位/爻辞/互/六亲 全为 0；八字 4303 字正文里 宫位/六亲/身体 全为 0）。
**两科 golden 机械层均零漂移**（评分未动），措辞层漂移全部来自新增的【象上看】段与口径提示，
已 capture 记入 `narrate_drift_log`。

### 六爻侧

- **新增 `scripts/xiang.py`**（象层唯一装配点）＋ 数据源 `data/rules/xiang_layer.json`：
  `category`（题类→象类别）／`trigram`（类象）／`ti_yong`（体用）／`guaci`（卦辞）／
  `yaoci`（动爻与世爻爻辞）／`hu_gua`（互体：京房二三四为下互、三四五为上互，此前全仓无此算法）／
  `spirit`（世/应/用神/动爻六神象义）／`fangwei`（体用方位）／`class_image`（题类专属类象）。
- **`category` 不再恒 `general`**：`analyze.py` 原有一行写死 `build_trigram_interpretation(result, category="general")`，
  类象永远只出通用档。现由 `step2.question_class` 经映射表推导，装配点移到 chain 之后；
  `output.py` 的 `attach_trigram` 同口径（两条路径不再取到不同的象类别）。
  实测：疾病→health、失物→loss、功名→career、婚姻→relationship、行人→travel。
- **正文与插件出口**：`narrate.py` 增【象上看】段（无素材则整段不出，不留空壳）；
  `plugins/mcp/tools.mjs` 的 `liuyaoValue` 增 `xiang` 结构化块，并补上此前从未输出的 **`line_text`（爻辞）**。
- **现代问法政策标记**：`step2` 增 `use_god_policy`（只标记、**不改用神取值、不进评分**）。
  兜底层（实测 219 条问法中 44 条）标 `fallback_shi_yao`、词典单字键层（88 条）标
  `thin_single_char_key`，把「薄在哪、建议怎么转问」写进产物面；正文增「用神口径提示」一行。
- **新门 `[39] 象层门`**（`dev_tools/check_xiang.py`，`--only xiang`）：象目须带非空 `basis`／
  类别须随题类联动（负例：恒 general）／评分侧 18 个模块禁读 `xiang` 且 `xiang` 不得进 `WEIGHTS`。
- **新读数器 `dev_tools/xiang_coverage.py`**：13 题类 × 2 种子 = 26 路实跑，报象目产出率与
  题类→象类别分布。**只报「有没有出」，不报「准不准」**——象不进评测维度，故不产任何质量分。
  首轮读数：8 个象目全部 26/26；「天气·占雨」示例问句落到 `travel`（问句「何日有雨」
  未命中 question_classes 的占雨词族，被行人词族「何日」接走）——**登记为待办，不在本批改**
  （改题类关键词会动 step5 门控与评分，属另一条线）。

### 八字侧

- **新增 `scripts/xiang.py`** ＋ 数据源 `data/xiang_layer.json`：`gongwei`（宫位：年为根／月为苗／
  日为花／时为果，含时限与身位）／`liugin`（六亲：五类反查内核 `LIUQIN_TO_SHISHEN`，
  子平分野按性别——男命正财为妻、女命正官为夫；传统歧异处两说并记不裁决）／
  `zangfu`（五行脏腑，**象意提示、非医学诊断**，交付面强制带此声明）。
  **不借道叙述层私表**：narrate 的 `liushen_image.json`／十神行事表（铁律一）不在读取范围。
- **正文与插件出口**：`narrate.py` 增【象上看】段；`baziValue` 增 `xiang`。
  八字侧 `check_dim_surface.NON_SCORED_SECTIONS` 已登记「象上看」的**不评分理由**
  （§六 要求「看到的没在评」必须说明，不许沉默）。
- **新门 `[39] 象层门`**（`dev_tools/check_xiang.py`）：三象齐备且带出处／六亲性别分野真生效
  （定盘甲辰·己巳·甲子·辛未：男命月干正财应「妻」、女命时干正官应「夫」）／评分侧禁读 `xiang`。
- **新读数器 `dev_tools/xiang_coverage.py`**：5 定盘 × 男女 = 10 盘，三象均 10/10，
  5/5 定盘男女六亲口径均有差异。

### 补记（同批追加）：占雨／占晴题类漏判修复

362 批的象覆盖读数器首轮读数报出「天气·占雨」示例问句落到 `travel`，本批把它**查实并修掉**，
不是我造的问句问题——对拍全语料 417 条问法/题名，查出 **3 条真实漏判**（均出自
`data/cases/zengshan_dz_cases.json`）：

| 问法 | 修前 | 修后 |
|---|---|---|
| `本日何时有雨`（ZD105） | 其他 | 天气·占雨 |
| `何雨`（ZD099） | 其他 | 天气·占雨 |
| `中秋晴否癸巳日又占`（ZD103） | 其他 | 天气·占晴 |

前两条正是第七十四批想堵却没堵住的「何日/何时＋雨」形态（被行人词族的「何日」接走）。

- 补词（一律多字，单字「雨」仍不作关键词，守「雨具」误并的教训）：
  占雨族 +`何日有雨`/`何时有雨`/`有雨`/`何雨`/`下雨`/`降雨`；
  占晴族 +`何时有晴`/`晴否`/`转晴`/`天晴`。
- **影响面实测**：417 条问法里只这 3 条改类，方向全是「其他 → 天气」，**零误伤**
  （没有任何一条从既有题类被抢走）；「雨具」类问句仍判「失物」（失物优先级高于天气）。
- **评分零影响**：这 3 条是**已排除案例**（`reason` 字段在册：ZD099 无可评分令牌、
  ZD103/ZD105 时间不可还原），不在任何评测集内，故 tune 97.9／holdout 90.2／
  应期 top-1 64.7% 与改前逐项一致；golden 机械+措辞双指纹零漂移。
  如实说明：本项修的是**判定正确性**，不产生分数增益——别把它记成涨分。
- **钉进门**：`[39] 象层门` 增 `class_problems()` 判据与 6 条题类回归锚（3 条新增漏判
  ＋3 条古籍问法防倒退）；负例＝把天气词族退化回「只留占雨/占晴」的旧形态，漏判必须重新被抓。
  象类别是题类的下游，题类判错则象必错——这条锚补的是象门的盲区。

### 契约与文档

- `CONTRACT.md` 新增 **§五-bis 象层：象与断的分界**（象在 analyze 产出、象不进断、
  象目带出处、象不冒充成绩）；两科 `data/rules/layer_contract.json` 同步接收 `xiang`
  键与题类专属子键，`batch` 抬到 362；八字 `tests/smoke_test.py` 的 `ANALYZE_KEYS` 接收 `xiang`。

## 2026-10-30 第三百六十一批（六爻）：**时间起卦分支缺失修复 ＋ 三处门禁/文档硬伤**

**性质**：bug fix（行为变更，修的是缺陷不是调参）。零判词、零评分口径改动；
golden 双指纹零漂移（六爻 288 例，见复验）。

- **P0 · `mode=time` 曾落到铜钱随机分支**：`scripts/chart.py` 只有 coin/number/manual
  三个分支，time 被 `else` 兜底接去 `coin_toss()`。实测同一时刻
  `2024-01-01 12:00` 连调两次得「小畜」/「谦」，退出码 0、JSON 完整、盘面仍标 time。
  现补 `elif mode == "time": engine.time_based_hexagram(yy, mm, dd, hh)`；
  未知 mode 不再静默摇卦而是 `ValueError`；time 拒收 `--seed`（确定性起卦不带种子）。
- **新门 `[2.4] 时间起卦确定性`**（挂在 `dev_tools/check.py`，`--only time_mode`）：
  同参两次必须同盘 ＋ 与登记时间算法爻值 `6,7,7,8,7,8`（走 manual 对拍，防止"两次一样"
  把恒阴恒坤也判成过）＋ time 带 seed 必须报错。旧自检只跑 `mode=coin/seed=42`、
  `check.py` 只在编码门用 time 夹具，两条都看不见这个缺陷。
- **冒烟门去恒真断言**：`tests/smoke_test.py` 的 `_seg()/_tc()` 缺段也返回 `{}`，
  于是 `isinstance(..., dict)` 恒真。cov_10/15/17/20、s5_12、bnd_03/04 改为目标键/非空断言；
  `s5_10` 的 `reasoning_chain` 改走 `narrative_assembly.build_reasoning_chain`
  （355 批起该键是叙述层产物，analyze 不再直产——旧断言因此恒红且被基线吸收）。
  改后 36/36、rc=0，基线 `smoke` 35→36。
- **两套测试的矛盾 oracle 收口**：`tests/thinking_chain_tests.py` 的 `case_07`
  仍用旧基准（2024-12-12／凶／net negative），而 `tests/regression_test.py` 的 `reg_07`
  已在 162 批按书二分校勘为 2024-12-28／吉向／net neutral。case_07 现与 reg_07 同 oracle
  （同一盘、同一结论），chain 基线 11→12（12/12）。regression 仍 17/19（reg_02/reg_09
  方向不一致在册待裁），基线 14→17——再退一例即拦，不再允许 5 例被基线吃掉。
- **治理图自证可信度**：`dev_tools/governance_map.py --selftest` 此前算到真实
  `strict` 扫描 rc 却仍 `return 0`；现在真实 rc 非 0 即外传。
- **CI/文档**：`.github/workflows/ci.yml` 新增 `min-python-smoke`（声明最低版 3.10
  跑两科冒烟＋八字回归＋六神单测），root-gates 补三个根级门的 `--selftest` 与治理图自证；
  根 `README.md` 关于「八字无 `tests/`」的旧真值按实更正（335 批已补建），
  `ARCHITECTURE-PLAN.md` 的 CI job 数四/五→六。
- 复验：`python liuyao/dev_tools/check.py` 全绿（含 golden 双指纹零漂移、smoke 36、
  chain 12、regression 17、time_mode 新门）；`python liuyao/dev_tools/governance_map.py
  --selftest` rc=0；`python liuyao/tests/time_mode` 判据见 `[2.4]`。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-30 第三百六十批（全仓）：**AGENTS 目录图与依赖线补上 `eval/` 层**

**性质**：docs（结构同步）。零引擎、零数据、零读数改动。

- `AGENTS.md §二` 目录树为两科补 `eval/` 行（六爻 356 批、八字 359 批迁入），
  依赖线由「`scripts → core`」补为「`eval → scripts + core`」，并写明
  「评测层可读 `data/cases`；交付路径不得反向 import `eval/`」。
- 与 `check_case_isolation.py` 的物理隔离档、两科 `eval/__init__.py` 的边界声明同义；
  无代码改动。
- 复验：`devkit/root/check_root_docs.py`、两科 `check_doc_refs.py` 0 死链；
  `check_docs_index.py` 51 份文档齐；full ledger 40/40（读数不变）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-30 第三百五十九批（六爻/共享门）：**物理隔离档检测泛化（六爻行为不变）**

**性质**：shared gate（行为保持）。零引擎、零数据、零读数改动。

- `devkit/shared/check_case_isolation.py`：`PHYSICAL` 由「`eval/case_runner.py` 存在」
  改为「`eval/` 内有 `evaluate.py` 或 `case_runner.py`」，以容纳八字（只有 evaluate、
  无 case_runner）的物理搬迁；正面断言只要求 evaluate，原 `case_runner` 科再追加验。
- 六爻仍走物理隔离档：51 模块 0 触达、`--selftest` 通过；`sync_devkit --write` 分发
  后 `[37]` 11 件同源。详见同批 `bazi/docs/CHANGELOG.md` 第三百五十九批。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-30 第三百五十七批（六爻）：**§3.4 剩余同名函数结案——两组重命名去重，行为零漂移**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动；golden 双指纹零漂移。

- `classical_enhancements._find_use_god_positions` → `_find_use_god_positions_by_question`：
  两份同名函数签名/语义本就不同——step2 版按 `yao_lines + 用神六亲` 构造候选 dict，
  classical 版按 `question_category/问题关键词` 推断六亲后只返回爻位列表。改名消除
  同名误读，`effects.py` 用 `as` 别名保持内部旧名；`__all__` 同步新名。
- `classical_enhancements._element_to_relation` → `_element_to_relation_or_none`：
  实现改为委托 `util.get_relation_from_element`，仅保留空值守卫。**逐格对拍**：
  木火土金水×5 共 25 格与 util 完全一致；含空/未知的 23 格差异只在「返回 None vs
  返回『未知』」，旧实现本来就返回 None，故行为逐字保持（`effects` 以 None 作缺省）。
- 同名函数组由 347/352 批的 **10 组降至 7 组**：剩余为 `__getattr__`（PEP 562 协议）、
  `main`（7 个 CLI，预期）、`_chong/_he/_elem/_world_line`（域内局部实现）、
  `_pos_to_name`（非法位置回落 `f"{pos}爻"` vs `f"第{pos}爻"`，真实文案差异，接受）。
  **§3.4 不再有可合并的跨模块重复**，本条结案。
- 复验：`golden.py verify` **6f70/405b 零漂移**（288 例）；AST 同名扫描 7 组；
  `python dev_tools/check.py` 全绿；full ledger **40/40**。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-30 第三百五十六批（六爻）：**评测层物理搬迁至 `eval/`——§3.5 关闭**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动；golden 双指纹零漂移。

- `git mv` 三件实现：`scripts/case_runner.py`、`scripts/evaluate.py`、
  `scripts/build_portal_assets.py` → `liuyao/eval/`，新增 `eval/__init__.py`；
  `scripts/` 下同名文件改为纯 re-export 兼容 shim（`evaluate`/`build_portal_assets`
  保留 `main()` 分发，`case_runner` 无 CLI）。旧命令 `python scripts/evaluate.py ...`
  仍可用；新命令与文档统一写 `python eval/...`。
- `eval/evaluate.py` 把 `EVAL_DIR` 置于 `sys.path` 最前，保证 `import case_runner`
  解析到实现而不是 `scripts/` shim；`eval` 三文件先加 `scripts/` 再 import
  `kernel_path`，direct run 可自定位。**356 首跑实踩**：此前顺序反了，
  `python eval/evaluate.py --help` 报 `ModuleNotFoundError: kernel_path`；修复后 rc=0。
- `scripts/evaluate.py` 增模块级 `__getattr__` 代理：Python 星号导出不带下划线名，
  而 `dev_tools/baselines.py` / `rank_experiment.py` / `version_collate.py` 仍按旧路径
  `import evaluate` 调 `_branches_in` / `_expected_unit` / `_offered_branches` /
  `_unit_pool`。**356 首跑实踩**：缺代理时 `baselines.py` AttributeError，
  full ledger `liuyao.baselines` 读到 `(None, None)` 判红；加代理后回 25.0/4.5。
- 两个 CLI shim 在**入口文件自身**加 UTF-8 守卫（AGENTS.md §四.9）；
  `[20]` 静态红线由「缺守卫 2 个」回到 0。
- `check_case_isolation.py`（源 `devkit/shared/`）两档化：**物理隔离档**（有 `eval/`：
  `eval/` 实现必须存在 + `scripts/` 零白名单）／**白名单档**（八字仍走 346 批口径）。
  六爻走物理档：51 模块 0 触达；新增「`eval/` 实现缺失」负例自证。共享 docstring 里
  原写 `eval/case_runner.py` 在八字科是死链（`[11]` 首跑判红），改为「`eval/` 内
  文件名」表述后两科 doc refs 0 死链。
- `check_test_sentinel.py` 的评测路径改 `eval/evaluate.py`；`README` 目录表、
  `CAPABILITY` 复现命令、`YIIN-CASE-AUDIT` 复现段、`rule_registry` 评测覆盖注记
  同步改指 `eval/`（历史 CHANGELOG 条目按登记时点事实不改）。
- `plugins/scripts/build.mjs`：liuyao `scripts/` 排除三个评测 shim（包内没有 `eval/`，
  随包会 import 失败）；`selftest.mjs [2]` 加「shim 未随包」正面断言＋临时探针负例。
- 复验（356 实跑）：`python liuyao/dev_tools/check.py` 全绿；`python bazi/dev_tools/check.py`
  全绿；full ledger **40/40**（quick 34/40、跳过 6）；`check_batch_num` 通过；
  `check_case_isolation --selftest` 两科通过；`sync_devkit --check` 11 件逐字节同源；
  `node plugins/scripts/build.mjs` ＋ `selftest.mjs` 全绿；`publish.mjs` 发布树检查全绿；
  `python eval/evaluate.py --help`、`python eval/build_portal_assets.py --help` rc=0；
  golden 双指纹零漂移。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十五批（六爻）：**`reasoning_chain`/`summary_text` 迁叙述层——CONTRACT §六 归零**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动；golden 双指纹零漂移。

- 新增 `scripts/narrative_assembly.py`：从 analyze JSON 的 step1–5 facts 重建
  `reasoning_chain`（9 条）与 `summary_text`（约 355 字）；只消费 analyze JSON，
  **不 import `analyze.py`**，复用 `chain_assembly` 的事实装配器。
- `thinking_chain.py`：删除顶层 `reasoning_chain`/`summary_text`，新增结构化
  `pattern_lines`（`[格局]`/`[格局要点]`/`[格局详释]`，与旧推理链同位同序）；
  `step5.py` 删除 5.10 推理链生成与 `step5_synthesis.reasoning_chain` 键。
- `narrate_core` / `output.py` / `case_runner` / `build_portal_assets` / `refactor_guard`
  在需要旧字段处调用 `narrative_assembly` 重建；`golden.py` 的 patterns 改读
  `pattern_lines`（源在 `devkit/shared/variants/golden.liuyao.py`，已 sync）。
- `layer_contract.json` `batch 355`：`thinking_chain` 嵌套白名单 8→**7 键**
  （step1–5／pattern_tags／pattern_lines），删 `reasoning_chain`/`summary_text`；
  `CONTRACT §六` **归零**（原 7 关闭），§三 增 `narrate → narrative_assembly` 允许行。
- 连带口径：`[2] 段落有产出数` 基线 36→**35**（`section_advice` 354 批已迁 render，
  analyze 少一段；渲染面由 `[2.7]` parity 守）；`judgment_table` 27 处覆写行号 **-4**
  （step5 5.10 删除导致），`[33]` 8 类负例全过。
- 复验：`golden.py verify` **6f70/405b 零漂移**；`check_layer_contract.py --selftest`
  rc=0（chart 7/analyze 14、7 禁边、信封 schema 通过）；`analyze` 输出无
  `reasoning_chain`/`summary_text`（实测 False/False）；`narrative_assembly` 重建 9 条、
  summary 355 字；`engine --output text --depth full` 五步链正常；`case_runner` rc 9 条；
  `python dev_tools/check.py` 全绿（355 批实跑）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十四批（六爻）：**`section_advice` 从 analyze 迁呈现层（§六-7 第二半）**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动。

- `analyze.py` 不再调用 `generate_advice`、不再产 `section_advice`；`analyze` 顶层键
  **15→14**（`layer_contract.json` batch 354；`CONTRACT §四` 表同批回改）。
- `advice_framework.ensure_section_advice(result)`：已存在原样返回；缺失按
  step5 verdict + 问题类别生成（失败回空，不静默造节）。`render_html` 在开场调用它
  并写回传入 dict，所以 HTML 的「趋避建议」节与 `check.py [2.7]` 的 parity 断言仍有源。
  `engine.py` 原本就自产 advice；`narrate_core` 原本就自调 `generate_advice`；两者零改动。
- `CONTRACT §六-7` 改为：narrate 反解已修（351）＋ section_advice 已迁（354）；
  **仍开放**只剩 `reasoning_chain` 9 条成句＋`summary_text` 354 字。
- 复验：`check_layer_contract.py --selftest` rc=0（chart 7/analyze 14、7 禁边、信封 schema 通过）；
  `golden.py verify` **6f70/405b 零漂移**；`analyze` 输出无 `section_advice`（False）、
  `render` HTML 有「趋避建议」（True）；`python dev_tools/check.py` 全绿（354 批实跑）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十三批（全仓）：**跨科共用契约信封 schema 落地（§3.6 关闭）**

**性质**：schema＋shared gate。零引擎、零数据、零读数改动。

- 新增 `devkit/layer_contract.schema.json`（JSON Schema 2020-12）：约束两科
  `layer_contract.json` 的顶级信封 `schema/contract/batch/fixtures/stages/edges`，
  以及 `edges.forbidden[]` 的 `from/to/known/why`；各科 stage 键名仍由各自 JSON 判。
- `devkit/shared/check_layer_contract.py` 增 `validate_contract_envelope()`
  （零依赖 JSON Schema 子集：required/type/items/minLength/minItems），
  `SCHEMA_PATH` 按 `parents[2]/devkit/` 定位；selftest 增 3 类负例
  （真契约误判／缺 stages／禁边 why 为空）。同时修掉旧 `main()` 里
  `problems` 先使用后定义、`fixtures` 空时只挂空壳的潜伏 bug。
- `devkit/sync_devkit.py --write` 分发 11 个共享件；两科
  `check_layer_contract.py --selftest` 均 rc=0：
  六爻 chart 7/analyze 15、7 条禁边；八字 chart 9/analyze 26、4 条禁边；
  两科都打印「信封 schema 通过」。
- `CONTRACT.md` §四 增信封 schema 段；§七 变更规程增「动顶级结构须同批改 schema
  并跑 sync_devkit --check」。
- 347 批 triage 的 §3.6「正式 JSON Schema 未建」由此关闭；schema 是 root 唯一真源，
  **不增加共享件数**（仍 11 件，不随科分叉）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十二批（六爻）：**同名 helper 去重（第一批）——`_branch_element`／`get_twelve_growth_stage` 归 util**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动。

- `classical_enhancements.py` 的本地 `_branch_element` 与 `get_twelve_growth_stage`
  与 `util.py` 的实现在语义上逐行一致；本批改为从 `util` 导入并删除本地副本
  （`__all__` 的再导出面不变）；同时删掉不再使用的 `TWELVE_GROWTH_STAGES`／
  `TWELVE_GROWTH_TABLES` 导入。
- **不合并的两组**：`_pos_to_name` 的非法位置回落不同（`f"{pos}爻"` vs `f"第{pos}爻"`），
  属真实语义差异；`_element_to_relation`／`_find_use_god_positions` 两份实现不同
  （15 vs 3 行、40 vs 50 行），须另批做行为对拍，不在本批夹带。
- 同名函数扫描由 347 批的 10 组降至 **8 组**（`main` 9 个 CLI 属预期，`_chong/_he/_elem/
  _world_line` 为域内局部实现，`_pos_to_name` 与另两组见上）；剩余项仍挂 347 批 triage。
- 复验：`golden.py verify` **6f70/405b 零漂移**；`get_twelve_growth_stage('木','卯')`
  `('帝旺', 4)`、`_branch_element('子')` `'水'`、`__all__` 再导出名仍在；
  `python dev_tools/check.py` 全绿（352 批实跑）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十一批（六爻）：**`pattern_tags` 结构化——narrate 不再正则反解 reasoning_chain（§六-7 第一半）**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动。

- `thinking_chain.run_thinking_chain` 在 `thinking_chain` 里新增结构化事实
  `pattern_tags = _collect_pattern_tags(...)`（同一批标签，`[格局]` 行仍保留给旧消费方）。
- `narrate_core._extract_pattern_tags` 优先读 `thinking_chain.pattern_tags`，**不再**
  从 `reasoning_chain` 的 `[格局] A|B` 串正则反解；旧 analyze JSON 无该键时保留回落。
- `data/rules/layer_contract.json` `batch 351`：`analyze.nested` 新增 `thinking_chain`
  8 键白名单（step1–5／reasoning_chain／summary_text／pattern_tags）；`[32]` 从此能看见
  这一层（此前只白名单 `trigram_interpretation`/`conclusion`）。
- `CONTRACT.md §六-7` 改为**部分还**：反解已修、白名单已就位；`analyze` 仍吐
  `reasoning_chain` 9 条成句＋`summary_text` 354 字＋`section_advice` 4 句，叙述句迁移
  仍开放（另批）。
- 复验：`check_layer_contract.py --selftest` rc=0（chart 7/analyze 15、7 条禁边、0 在册欠账、
  thinking_chain 8 键）；`golden.py verify` **6f70/405b 零漂移**；`python dev_tools/check.py`
  全绿（351 批实跑）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百五十批（六爻）：**还 `engine_chart→trigram_symbolism` 禁边——卜象解读迁 analyze／CLI 输出层补键**

**性质**：refactor（行为保持）。零判词、零评分、零读数改动；`known` 禁边欠账归零。

- `engine_chart.py` 不再 import `trigram_symbolism`、不再产 `trigram_interpretation`；
  chart 顶层键 **8→7**（`CONTRACT §四` 同批回改）。
- `analyze.py`：在 `result = dict(chart_json)` 后补 `build_trigram_interpretation`
  （旧 chart 段的 graceful degradation 照搬：失败记 `None`，不阻塞推演）；
  analyze 顶层键仍 15，`trigram_interpretation` 进 `required`，22 键嵌套白名单从
  chart 迁到 analyze。
- `output.py`：`attach_trigram` 在 CLI 输出前补键——`engine.py` 直接消费 chart 时，
  JSON/Text/HTML 输出面不变（`engine.py` 不触 `trigram_symbolism`）；四段管道的
  analyze 自行产出同一键，不重复计算。
- `data/rules/layer_contract.json`：删除 `engine_chart→trigram_symbolism` 禁边，
  `batch 350`；`edges.forbidden` 只剩 7 条零容忍规则，**known 欠账 0**。
- `CONTRACT.md`：§三 禁边表删除该行；§四 chart 7／analyze 15，嵌套行改「analyze 段，
  350 批迁入」；§六-1/§六-3 销账，§六 只余 **7**（analyze 仍吐 reasoning_chain 成句 +
  narrate 反解标签）。
- 复验：`check_layer_contract.py --selftest` rc=0（5 夹具 × chart 7/analyze 15、7 条禁边、
  0 在册欠账）；`golden.py verify` **6f70/405b 零漂移**；`engine.py --output json` 仍含
  `trigram_interpretation`；`chart.py` 输出**不含**该键、`analyze.py` 输出**含**该键
  （实测 False/True）；`python dev_tools/check.py` 全绿。
- 插件 1.0 面不受影响：`yi_liuyao` 的 value 由 analyze/`narrate` 组装，本就不搬
  chart 的 `trigram_interpretation`；chart 内部 JSON 形状变化属引擎内部面。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十九批（六爻）：**还 `engine.py→render` 禁边——CLI 三路输出迁 `output.py`**

**性质**：refactor（行为保持）。零判词、零评分、零输出文案改动。

- 新增 `scripts/output.py`：`append_advice` ＋ `output_result` 从 `engine.py` 整段搬出，
  HTML/JSON/Text 三路分支、`--save-html` 路径处理、`--open-browser`、`render` 缺失时
  回退 JSON 的旧行为逐行照搬。`engine.py` 只 `from output import output_result`，
  不再 import `render`，也不再 import `engine_format` 的四个输出helper。
- `data/rules/layer_contract.json`：删除 `scripts/engine.py → render` 禁边条目，
  `batch` 320→349；`CONTRACT.md §三` 增允许行 `engine.py→output.py`，
  `§六-3` 由「2 条现存禁边」改为「1 条」（只剩 `engine_chart→trigram_symbolism`）。
- 复验：`check_layer_contract.py --selftest` rc=0（扫 69 模块、8 条禁边、1 条在册欠账）；
  `golden.py verify` **机械 6f70／措辞 405b 零漂移**；`engine.py --mode manual --output json`
  冒烟通过；`check_case_isolation`／`check_house_conventions`／`check_cli_encoding` rc=0；
  `python dev_tools/check.py` 全绿。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十八批（全仓）：**根级文档同步——bazi README 308 读数、GOVERNANCE 43、ARCHITECTURE V9/V12/V13**

**性质**：docs。零代码、零数据、零读数改动。

- `bazi/README.md` 的 `pattern 80.6%／p=0.727`、`外部 53 集` 系 187/308 批前旧读；
  按 308 实测改为 **pattern 100.0%（36/36，b=9 c=0，p=0.004）**、外部 **62 例**。
- `GOVERNANCE.md` 八字 43 的「尚未提交 → clean clone 42」依赖已随 345 批关闭。
- `ARCHITECTURE-PLAN.md` V9 四→五 job（344 批 ledger）、V12 39→40 项、V13 三命通会
  六路径已补交。以上均属 §六.3「文档说的和代码做的不一致即缺陷」的同步。
- 复验：`bazi check.py` rc=0；`readout_ledger` full **bad=0/40**；根级三道门 rc=0。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十七批（全仓）：**结构分层体检 10 项 triage＋step5 补 docstring＋契约 §六-2 销账**

**性质**：docs＋极低风险代码（只加 docstring）。零推演行为、零判词、零读数改动。

### 一、代码/文档改动

- `liuyao/scripts/step5.py` 补模块 docstring（329 批体检原句「step5 连 docstring 都没有」）；
  明确「推演实现，不是叙述层；体量约 2,000 行是既定技术债，拆分另批走 §四」。
- `CONTRACT.md §六` 删除原 2（`analyze` docstring 与实测不符）——310 批已改文档、
  347 批复核 docstring 现为「结构推演 + 定性结论」；已关闭项注记合并原 2/4/5/6。
- `AGENTS.md §一.2` 标题与正文按实改写：运行时隔离的机器判据是
  `check_case_isolation.py` 的**文件白名单**，不是物理目录隔离；`evaluate.py`/
  `case_runner.py` 仍在 `scripts/`，物理搬迁未做、不冒充已做。
- `data/rules/judgment_table.json` 的 27 处覆写 `line` 全部 +8：step5 顶部插入
  docstring 使行号整体下移；`[33]` 首跑即按“盘上 L1398 vs 表内 L1390”抓到，
  逐条同步后 `check_judgment_table.py` 与 `--selftest`（8 类负例）全过。

### 二、329 批结构分层体检 10 项——逐项复核结论

| 条目 | 复核结论（347 批实跑/源码证据） | 处置 |
|---|---|---|
| §3.1 三条 import 环 | **不成立**：`liuyao/scripts/*.py` 模块级 import 边 122 条、**环 0 个**（AST 全扫）；`engine.py` 192/378/388/402/419 五处是函数体内懒加载可选功能，不构成模块环 | 结案 |
| §3.2 三处反向依赖 | **不成立**：`[32]` 的 `core→scripts` 零容忍边全绿；模块级扫描未复现 | 结案（原件证据随 scratch 删除，按 §六.5 记“证据不足”） |
| §3.3 私有名当公共 API | **不成立（显式再导出）**：`effects.py` 导入的 10 个下划线名全部在 `classical_enhancements.__all__` 内，属 PEP 562 再导出面，不是私有名泄漏 | 结案 |
| §3.4 同名函数并存 7 组 | **部分成立**：AST 实测 10 组——`main`（9 个 CLI）属预期；`_chong/_he/_elem/_world_line` 为域内局部实现（语义不同，接受）；`_branch_element/_pos_to_name/get_twelve_growth_stage/_element_to_relation/_find_use_god_positions` 五组跨模块重复**仍未并** | 接受局部项；五组重复另批做行为保持合并（会动 golden，须 §四） |
| §3.5 评测层与交付层同目录 | **成立**：`evaluate.py`/`case_runner.py` 仍在 `scripts/`，隔离靠文件名白名单 | 文档已按实改写；物理搬迁列待办（会改 README/CAPABILITY 的复现命令，须单批） |
| §3.6 跨科共用契约无 schema | **部分成立**：`layer_contract.json` 有 `schema:1`，`[32]` 校验键面/禁边；正式 JSON Schema 文件未建 | 接受现状；正式 schema 若建须两科同批＋`devkit` 分发 |
| §4.1 三个 2,000 行级模块 | **成立（体量）**：实测 `step5.py` 1987 行、`classical_enhancements.py` 1932 行；329 批原记 2176/2227 系行数口径差 | step5 docstring 已补；拆分/瘦身另批（§四 两集出分） |
| §4.2 两科结构不对称 | **不成立（设计）**：D3 中档明确「不克隆六爻 step1–5 与 9 个 classical_enhancements_*」 | 结案（ARCHITECTURE-PLAN §六.3） |
| §4.3 呈现层两套语言 | **不成立（两运行时设计）**：六爻 HTML 在 Python（CLI/报告），八字 HTML 在 Node（MCP 宿主），共用一套运行时反而要跨语言嵌入 | 结案；若统一须先定宿主边界 |
| §4.5 文档覆盖不到一半 | **不成立（无可测分母）**：DOCS 现 51 份源文档；329 批 53 系含已删副本的粗计 | 结案；不设“文档数/脚本数”假指标 |

### 三、复验

- `python liuyao/dev_tools/golden.py verify`：双指纹零漂移（docstring 不进指纹）；
- `python liuyao/dev_tools/check.py`：全绿（含 [32] 分层契约、[38] expected 覆盖）；
- `python liuyao/dev_tools/check_batch_num.py`（根级）：未结案孤儿 0。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十六批（全仓）：**`check_batch_num.py` 落地——批次×提交有了根级门**

**性质**：root gate。零引擎、零数据改动。

- 新增 `devkit/root/check_batch_num.py`：读 HEAD 版本的两科
  `docs/CHANGELOG.md`＋`docs/CHANGELOG-HISTORY-INDEX.md` 的 `## 日期 第N批` 标题，
  读 `git log` 全信息体的「第N批」，**已登记但无提交提及**的批号判红。
- 允许名单**不另抄**：从 `liuyao/dev_tools/readout_ledger.py` 的 `SETTLED_ORPHANS`
  经 AST 读取（单源）；读取失败即判红。提交提及但标题没有的批号只报 NOTE
  （历史合并入库/范围简写的已知形态），不反向考古。
- 负例五类（中文批号解析／一致误伤／登记未提交／已结案误伤／0 结果）全抓到；
  实跑：CHANGELOG 标题批号 151 个、提交提及 158 个、未结案孤儿 **0**。
- 挂 CI `root-gates`（`python devkit/root/check_batch_num.py`）；`ARCHITECTURE-PLAN §五.5`
  的「尚未实现」欠账关闭。`devkit/MANIFEST.json` 的 root 列表本就登记该文件，
  本批只是让名单里那个名字真的存在。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十四批（六爻）：**恢复 wikisource 被清空的书证标签 ＋ [38] expected 覆盖生存线 ＋ 账台 full 口径修正**

**性质**：data＋gate＋docs。零引擎行为改动、零判词改动；恢复的是 292/297/298/282 批
已落库的书证/机械派生基准字段。

### 一、事故：1592923 把基准标签清空了，聚合分只掉 6 分

`1592923`（易隐批）重跑 `fetch_wikisource_cases.py` 生成
`liuyao/data/cases/wikisource_cases.json`，只写自动解析字段，未保留人工 expected：

| 字段（非空数） | 1592923 前 | 事故后 | 恢复后 |
|---|---:|---:|---:|
| `expected.use_god` | 78/81 | 4/81 | **78/81** |
| `use_god_branch` | 55/81 | 3/81 | **55/81** |
| `use_god_note` | 32 | 0 | **32** |
| `use_god_wangshuai`／`muku`／`six_spirit` | 各 3 | 0 | **各 3** |
| `WS035` verdict（282 批校勘） | 凶 | 吉 | **凶** |
| `WS003` 题面 | 占本年冬今得關差否 | 占本年冬今 | **原题面** |

后果：wiki strict **75.8→69.8**、top-1 **31.8→29.5**、名次 2.03→2.16；
direction 反而 **76.6→83.0**（弱维被 N/A 剔除的假上升）。339 批把 69.8 登记成新期望，
并归因「315 封存后外集组成/分母变了」——**该归因是错的**：315 只把 50 例切 dev/test，
n 与标签都没变；真正原因是本条事故。同 HEAD 引擎放回 308 标签后逐位回到
75.8/31.8/2.03，direction 76.7，证明**引擎未回归，是基准被削薄**。

恢复方式：以 `1592923^` 的 expected 为源，逐字段并回当前文件；保留本次抓取的
`_meta.retrieved=2026-10-29` 与 WS003 `wikitext_head` 的去重修正，新增
`_meta.curation` 说明。不是按读数改 expected：恢复后的读数与原 308 登记一致。

### 二、新门 [38]：expected 覆盖生存线

新增 `dev_tools/check_expected_coverage.py` ＋ `data/rules/expected_coverage.json`：
A 案例数不得低于登记数；B 每个受控字段非空数不得低于下限；C `use_god` 空白 ID 必须
逐条列名（只允许 WS045/WSD007/WSD008）且取值须在七类内。负例五类（整批清空／未登记
空值／乱写取值／删例／清空 note）全部抓到。门 [38] 挂进 `check.py`；
`governance_map` 登记 blocking，六爻 63→64、blocking 27→28。

### 三、账台与对外文书同步

- `liuyao.wikisource` 69.8/29.5/2.16 → **75.8/31.8/2.03**；top1/top3 29.5/59.1 → **31.8/61.4**。
- `liuyao.baselines` 用神 18.2 → **25.0**（恢复题面后实测；事故态为 22.7——
  WS003 题面截短改动了起卦输入）。基线变强是引擎用神取支改进，**未登记**，不是评分口径变化。
- `bazi(tiaohou… pattern)` 80.6 → **100.0**（308 批已实测，账台漏登；零引擎改动）。
- 新增账台项 `liuyao.expected_coverage(78/55/3/32/3/3/3/58)`。
- `--quick` 不再在跳过 6 项时自称「全账 bad=0」：改为「已跑 34/40，跳过 6」，
  结论写「已跑项全部一致（未跑项不计入结论）」；`--selftest` 增两项断言
  （结论口径＋QUICK_SKIP 无死 id）。
- `liuyao/README.md` 基线 18.2/19.0 → 25.0/19.0；重算双侧 exact McNemar
  **p=0.549/0.453**（183 批 18.2 基线时 p=0.34/0.45）——引擎仍高于最强基线，
  但「优于择支基线」照旧不声称。
- `CAPABILITY.md` T1 机械指纹 4cee…→**6f70…**（320–324 批 judgment 块纳入后的现行值；
  措辞层 405b 始终未变）。
- `GOVERNANCE.md` 当前分布 63/27→**64/28**。
- CI 新增 `ledger` job（windows-latest，跑默认 full）：此前全账只有本地 quick，
  被跳过的 6 项（baseline／pattern／wiki top1-top3／collate／bazi 分维／bazi.external）
  长期没有 CI 面；344 批起 full 账台进 CI。

### 四、复验

- `python liuyao/scripts/evaluate.py --split wikisource_holdout`：75.8%（n=50），top-1 31.8%、名次 2.03；
- `--split wikisource_direction`：76.7%（n=31）；
- `python liuyao/dev_tools/baselines.py --split wikisource_holdout`：用神值支 25.0/44；
- `python liuyao/dev_tools/check_expected_coverage.py --selftest` rc=0；
- `python liuyao/dev_tools/governance_map.py --strict` rc=0（64/28 与 43/26）；
- `python liuyao/dev_tools/readout_ledger.py` **full：bad=0，已跑 40/40**；
- `python liuyao/dev_tools/readout_ledger.py --quick` rc=0，输出明确「已跑 34/40，跳过 6」。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十三批（六爻）：**主 CHANGELOG 再瘦身——只留 10-29，51 节标题并入索引**

- 把 10-27 及更早的 51 个 `##` 节从主文件移入 `docs/CHANGELOG-HISTORY-INDEX.md`
  （标题保留、批号与日期原样，账台批号集合不变）。
- 主文件 92KB→69KB；索引 72KB→79KB。连同 342 批删除的 355KB 归档，
  六爻历史记录总量由约 570KB 降至约 148KB。
- 复验：`check_docs_index` 51 份、`check_root_docs` 0 死链、`check_doc_refs` 0 死链、
  `check.py` rc=0、`readout_ledger --quick` rc=0。

## 2026-10-29 第三百四十二批（六爻）：**历史记录精简——删除 355KB 归档全文，只留逐批索引**

**性质**：docs（用户令"历史记录文件可以删减，精简为主"）。零代码、零判据改动。

- 删除 `docs/CHANGELOG-ARCHIVE.md`（355,751 B／154 个批次全文）；
- `docs/CHANGELOG-HISTORY-INDEX.md` 改为**逐批标题索引**：原 154 批的 `## 日期 第N批`
  标题保留（截 120 字）＋ 2026-10-14 已剔除的第49–156批一句话（208 行），共 72KB；
- 删除一次性盘点 `docs/ARCHIVE/P0-INVENTORY-20261014.md`（结论已在历史索引/CHANGELOG）；
- `readout_ledger` 的「登记×提交」扫描面由 `CHANGELOG-ARCHIVE.md` 改为
  `CHANGELOG-HISTORY-INDEX.md`（批号与日期原样保留，孤儿计数不变）；
- `check_doc_refs` 的 EXEMPT 同步改为 `CHANGELOG-HISTORY-INDEX.md`；
- `DOCS.md` 六爻 18→16、全仓 54→51；`AGENTS.md` 历史记录政策改为"索引为主，不保留全文"。
- 复验：`check_docs_index` rc=0（51 份）、`check_root_docs` rc=0（7 份/0 死链）、
  `check_doc_refs` rc=0（761 条/0 死链）、两科 `check.py` rc=0、`readout_ledger --quick` rc=0。

## 2026-10-29 第三百四十一批（全仓文档收口·续）：**已关闭/已完成内容从活文档删除**

**性质**：docs。零代码、零判据改动。

- `CONTRACT.md` §六：删除已关闭的原 4/5/6 行（310/311/312 批关闭登记仍在 CHANGELOG），
  只留未满足的 1/2/3/7；八字侧 7 行审计表压成结论段（已关闭项不再重列）。
- `CAPABILITY.md`：删除已更正的虚构欠账（原②八字 golden），余 ①②③；保留"登记欠账也须可回指"的教训。
- `GOVERNANCE.md` 精神条款：删除已结案案例清单，规则本体保留。
- `AGENTS.md`：删除一条 313→316 措辞沿革注。
- `dsh-plugin/README.md`：删除已修 9 条踩坑表，只留硬性开发流程。
- `bazi/docs/EVAL-PLAN.md` §五：删除已完成步 1–5、7，只留未闭合的步 6。
- 复验：`check_root_docs` rc=0（7 份/0 死链）、`check_docs_index` rc=0（54 份）、
  两科 `check.py` rc=0、`plugins/selftest.mjs` 全绿。

## 2026-10-29 第三百四十批（全仓文档收口）：**删除已执行的派发件＋把总方案压成完成记录**

**性质**：docs。零代码、零门禁判据改动。

- **删除 `DISPATCH.md`**：26 个位（25 卡＋A6-INT）全部执行完毕，提示词与派发清单已无接收方；
  留着会让读者以为还有任务可领。
- **`ARCHITECTURE-PLAN.md` 压缩**：只保留 D1–D3 决策、最终形态、完成台账、V1–V15 收口实测、
  偏差与欠账、显式不做；已修好的"七个问题"、25 张卡的步骤/验收/禁止与派发提示词
  **从正文删除**（逐卡证据留在本卷 331–339 批与 `devkit/handoff/`）。
- `DOCS.md`：根级 8→7、总 55→54，`DISPATCH.md` 行删除，`ARCHITECTURE-PLAN.md` 状态改
  "归档留证"；`README.md`／`AGENTS.md`／`CONTRACT.md` 的指路与计数同步。
- 实测：`check_root_docs` rc=0（7 份根级 md、0 死链）；`check_docs_index` rc=0（54 份全部
  登记可达）；两科 `check.py` rc=0。

## 2026-10-29 第三百三十九批（六爻，A5-1）：**按 GOVERNANCE 五档过存量＋账台期望同步**

- 实跑 `python dev_tools/governance_map.py`：六爻 **63 脚本｜blocking 27｜nightly 11｜
  ondemand 12｜build 10｜tool 3｜未分类 0｜表中有序实无 0**（旧快照 57/24/11/11/8/3 已过期）。
- 登记 1 个存量未分类脚本 `build_yiin_cases`（build，《易隐》dz 底本案例构建）；
  删除 `check_docs_index` 旧条目（331 批 A0-5 已把该门移到 `devkit/root/`）。
- **降档/删除**：逐条对照 §一 门槛后**本批不降不删**——blocking 降 nightly 需连续一季
  0 判红＋负例可跑＋CHANGELOG 具名，本仓无按工具的季度台账；ondemand 删除需两季 0
  使用记录，同样无台账。降档只改调用频率、不改判据；本批连频率也没动。
- `readout_ledger.py --quick` 同步改期望并注明理由：governance 六爻 blocking `28→27`
  （[36] 上提）、`liuyao.wikisource` 与 `wiki top1/top3` 按 315 封存后口径更新
  （69.8/29.5/2.16、29.5/59.1；旧 308 登记值属"文本过期"非引擎回归）、
  `tracked×ignore` 由 9 回 0（9 份历史 wikitext 显式 negated）。账台 **bad=0/全账 39**。
- 墓碑句（A5-1 要求）：**六爻 `[8][9][10][21]–[25]` 是已下线门的墓碑，不回填；新门从 [37] 续。**

## 2026-10-29 第三百三十七批（六爻，A3-1/A3-2）：**core 产物显式化 ＋ data/cache 层**

- **A3-1**：`.gitattributes` 给 `liuyao/core/yishu_core/**` 标 `linguist-generated`（D1=C）；
  `kernel/sync_kernel.py --standalone liuyao --out %TEMP%\yi_ly_standalone` rc=0，
  `python …/scripts/chart.py --help` rc=0；负例：手改 core 产物 → `--check` rc=1 并点名。
- **A3-2**：生成物统一改落 `data/cache/`：`scripts/evaluate.py --save`（OUT_DIR）、
  `scripts/build_portal_assets.py`（EVAL_FILES）、`dev_tools/check.py` 的 eval_file；
  `.gitignore` 加 `**/data/cache/`；`check_doc_refs` 的 GENERATED_ARTIFACT 同时认
  `data/cases/` 与 `data/cache/`（历史文档不造假红）。
  **迁移 0 个 / 落空 0 个**（330 批已清空旧产物）；清空 `data/cache/` 后
  `python dev_tools/check.py` 仍 rc=0（现场重生成 10 个 eval 文件）。

## 2026-10-29 第三百三十六批（六爻侧，A2-B）：**CONTRACT §二-bis／路径修正／八字欠账审计（键面未改）**

**性质**：docs（六爻侧只受契约文档正文影响）。零引擎行为、零键面、零禁边改动。

- `CONTRACT.md`：`data/rules/layer_contract.json` → `<科>/data/rules/layer_contract.json`
  （根目录没有此文件）；§二 改为「四段职责的通用边界」并新增 §二-bis 各科剖面
  （六爻 = `step1`–`step5`；八字 = 单体 `analyze.py`，无推演链对应物）；
  §六 新增「八字侧契约欠账审计」表（新增欠账 0 条，两项无对应物标 N/A）。
- 本轮**未改键面/禁边**，`liuyao/data/rules/layer_contract.json` 不动；§七.1 三件套条件未触发。
- 实测：`python dev_tools/check_layer_contract.py --selftest` rc=0（5 夹具 × 两段键面、
  9 条禁边、2 条在册欠账）。

## 2026-10-29 第三百三十一～三百三十四批（六爻，A0-2/A0-3/A0-5/A1-1/A1-2/A1-3）：**devkit 门禁内核＋[37]**

| 批次 | 内容 |
|---|---|
| 331 | `devkit/` 骨架：`MANIFEST.json` ＋ `sync_devkit.py`（`--write/--check/--selftest`）；`devkit/handoff/` gitignore |
| 331 | `devkit/root/check_root_docs.py`：根级 8 份 `.md`，禁 basename 兜底；上线恰判红四处 `docs/CHANGELOG.md`，A0-3 修正后 rc=0 |
| 331 | `[36]` 文档索引门从 `liuyao/dev_tools/` 上提到 `devkit/root/`；六爻 `check.py` 的 [36] 段位移除，编号空出**不回填** |
| 331 | 根 `AGENTS.md`/`CONTRACT.md` 四处 `docs/CHANGELOG.md` → `<科>/docs/CHANGELOG.md` |
| 331 | CI 加 `root-gates` job（`sync_devkit --check` ＋两道根级文档门） |
| 332–334 | 11 个同名门/器归并：7 个 `devkit/shared/` 单源；`check_source_readings`/`golden`/`baselines`/`feedback_store` 按 kernel 变体范式登记 4 个变体 |
| 334 | 六爻 `check.py` 挂 **[37] 门禁同源**：手改共享产物、dev_tools 野文件、第二份拷贝判红 |
| 334 | `devkit/MANIFEST.json` 登记 `gate_ids`（六爻侧 13/31/32/20/11/29/12/14）＋墓碑说明：`[8][9][10][21]–[25]` 不回填、新门从 [37] 续 |

归并前后逐格对拍：`python dev_tools/check.py` 均 rc=0；`[11]` 检视数 781→774
（差异为 `.wikitext/.meta/_diff` 非声明载体排除与迁出文件的引用），0 条死链不变；
`[12]` 74 条指针 74 条可回指（并入八字的 re-export 可达性判据后仍全绿）。

## 2026-10-29 第三百三十批（六爻）：**文档整理与清垃圾——CHANGELOG 瘦身 522KB→167KB（全文明档）、新增全仓文档索引 DOCS.md**

**性质**：docs（文档整理）。**零行为改动**：两集读数、golden 双指纹、门数全不变。

### 一、删了什么

- `__pycache__` × 10 目录 / 266 个 `.pyc`（Python 自动再生）；
- 六爻 `data/cases/eval_*.json` × 10 / 6.5MB（`evaluate --save` 可再生，
  内核 `gate_kit` 的新鲜度守卫会重跑生成）。

**没删什么，以及为什么**：`git clean -X` 的"一刀切"预览里躺着三样**不能碰**的东西——
① `bazi/data/sources/sanming_tonghui_siku.wikitext.txt`（下载来的底本，删了校勘就做不了）；
② 五个宿主的 `engine/` `skills/` `src/`（构建产物，但并行会话正在用）；
③ `scratch/`（并行会话此刻正在清）。
所以本批**不用 git clean，改外科手术式**：只删明确可再生的两类。

### 二、整理了什么

| 动作 | 做法 | 理由 |
|---|---|---|
| **CHANGELOG 瘦身** | 10-25 之前的 **154 个批次全文**移入 `docs/CHANGELOG-ARCHIVE.md`（**一字未删**），主文件只留最近窗口（522KB→167KB） | 沿用本仓 2026-10-14「仓库瘦身」先例：明细归档＋一行索引 |
| **历史索引扩容** | `CHANGELOG-HISTORY-INDEX.md` 追加这 154 批的逐批标题（截到 90 字） | 按批号与关键词仍可检索到每一批 |
| **一次性盘点归档** | `docs/P0-INVENTORY-20261014.md` → `docs/ARCHIVE/`（零引用的一次性盘点，结论已入 CHANGELOG） | 归位，不是删；CHANGELOG 里唯一那处路径同步修正 |
| **新增总索引** | 根 `DOCS.md`：52 份文档的一句话职责＋状态（活文档／生成物／归档留证／历史索引）＋三条阅读路径 | 此前没有地图，新人只能靠文件名猜 |
| **入口挂指针** | `README.md` 顶部、`AGENTS.md` §二 各加一行指向 `DOCS.md` | 让地图找得到 |

### 三、两处口径同步（不然门会误判）

- **批号在册口径**：账台的「登记×提交」原只读 `docs/CHANGELOG.md`，
  归档后那 154 个批号会"凭空消失"变成孤儿 → 改为**主文件与归档文件都算**。
- **死链门豁免**：归档段是逐字搬来的历史散文，里面指向当年临时文件的路径照样是
  "登记时点的事实"；把它当活文档查，等于要求历史文字永远指向今天还存在的文件
  → 归档文件与 `CHANGELOG.md` **同口径豁免**（`EXEMPT`）。

### 四、给地图配一道门（[36] 文档索引完整性）

地图自己也会烂：新增文档忘了登记、或登记了已删的文件，读者按图去找会扑空，**而没有任何门看得见**。
新门 `dev_tools/check_docs_index.py` 只判两件事：
① 每个被跟踪的 `.md`（除 `DOCS.md` 自身）都在索引表**首列**登记过一次；
② 索引里写的每个仓库内路径都真实存在。负例自证两类（漏登记 / 死链）都被抓到。

写门时踩了一个自己的坑：最初把"登记"判成"文中出现过该路径"，
结果**删掉表格某一行后门仍显示已登记**——因为那文件在阅读路径表里还被提到。
改成**只认表格首列**（那才是"登记"），负例才真能咬住。

### 五、遗留

- `bazi/docs/SANMING-SIKU-COLLATION.md`（零引用的一次性对拍报告）**本轮未归档**：
  它的三处引用在 `bazi/docs/CHANGELOG.md` 里，而那份 CHANGELOG 正被并行会话改动——
  同一文件不同时改。等对方收工再动。

> **归档说明（2026-10-29 第三百三十批）**：本文件只保留 **2026-10-25 起的最近窗口**；
> 更早的 154 个批次全文在 `docs/CHANGELOG-ARCHIVE.md`（一字未删），逐批一行索引在
> `docs/CHANGELOG-HISTORY-INDEX.md`。批号在册口径已同步到两处，账台的「登记×提交」不受影响。


## 2026-10-29 第三百二十九批（六爻）：**B3 扩题库——第二个机器可读底本《增删卜易·dz》采成 36 例；新集上判定器与现行再次平手**

**性质**：data（扩外部案例池）＋ measurement。`verdict` 未动，两集读数与 golden 未动。

### 一、为什么要第二个采集器

313–328 批的外部案例池全部来自 `zengshan_buyi.wikitext.txt`，而它**已经榨干**：
实跑 `fetch_wikisource_cases.py`——爻图块 253 个，可入外部集 50 例、方向集 31 例；
剔除计数里「无应期」107、「无占题头」79。再用 API 全库搜 `insource:/○/`，
命中的六爻书**只有《增删卜易》各卷**——维基文库上没有第二本机器可读的六爻占例。

而仓里的 `zengshan_buyi_dz.dz.txt`（另一底本）用的是另一套卦画记法：
`妻财戌土″应              妻财戌土″`（六亲＋地支＋五行＋阴阳标记＋世应，两列＝本卦｜变卦）。
本批新写 `dev_tools/fetch_zengshan_dz_cases.py` 解析它，**三方校验与既有采集器同源**
（V1 纳甲／V2 卦变／V3 世应直接复用 `fetch_wikisource_cases` 的函数，不另造口径）。

### 二、踩了四个坑（每一个都是"看起来对"的那种）

1. **六亲写成字符类**：`([父母兄弟子孙官鬼妻财])` 只匹配到最后一个字（父母→母），
   整张表解析出来是"母未土"。改成非捕获择一 `(?:父母|兄弟|…)`。
2. **块扫描遇到解析不了的行就跳过** → 把下一例的爻行当成本例；V1 只失配 6/486 就混过去了。
   改成「遇非空非爻行即止」。
3. **变卦记法不同**：dz 用「得X卦**变**Y」，维基本用「得X**之**Y卦」。只认"之" → 变卦列全被当静卦。
4. **′/″ 不是动爻标记，是阴阳（老爻）标记**，每爻都有；动爻是字面的「動」。
   误把 ′/′ 当动爻 → 每个案例都"六爻皆动"，V2 全红。

### 三、实得与代价

98 个案例块 → **成例 36**（V1 纳甲 0/582 不合、V3 世应 2/174 不合、V2 卦变 60/63 不合）。
弃掉的 60 例是**底本自身不自洽**：变卦列与「動」字互相对不上（多例如此）。
按「基准错比基准缺更坏」，一律弃。新集对齐分：应期集 63.2%（n=11）、方向集 80.0%（n=10）——
不是乱码，案例可用。

**一个自己犯的错（如实记）**：本器首版把输出写成了仓里**已有的** `zengshan_dz_cases.json`，
**把维基版那 21 例（ZD*）覆盖了**。是哨兵「取数失败（评测器没交出平均分）」把它逼出来的——
恢复原文件，新案例改用独立文件名 `zengshan_dz_prose_cases.json`（ZDP*），两批并存。

### 四、扩题库后的对拍：**又一次平手**

新集 21 例（17 带吉凶）**整入 dev、不切半**（n=21 切半后每半 n≈10，哨兵在 n<15 的集上设门槛
等于设噪声门槛，故 `threshold=null`，不参与哨兵）。

| 集（两边都没调过的全新外部例） | 判定器 | 现行 |
|---|---|---|
| zengshan_dz_prose·应期（n=6 有书载方向） | 83.3% | 100.0% |
| zengshan_dz_prose·方向（n=8） | 87.5% | 75.0% |
| **合计 n=14** | **85.7%（12/14）** | **85.7%（12/14）** |

**第三次对比，又是平手。** 跨三个批次、三个独立口径（dev 32 例／封存 test 31 例／全新 dz_prose 14 例），
结果是**一次领先、两次平手**——没有稳定优势。**维持 328 批结论：不换判词。**

### 五、留在仓里的

新采集器（带 `--selftest`：错卦名／错变卦名／错動爻三类负例必须被拒）、
36 例新案例、两个新分片、哨兵支持"无门槛集"（n 太小的集明确不参与）、
判定表里的干净证据更新为四集合并 33/46=71.7% vs 29/46=63.0%（多对 4 例，仍不显著）。

## 2026-10-29 第三百二十八批（六爻）：**A3 收官——开封、平手、结论：不换判词**

**性质**：decision（有预注册、有封存、有记账的完整结论）。`verdict` 未动，两集读数与 golden 未动。

### 一、预注册 → 开封 → 记账

- **预注册**（`test_seal.json.judge_preregistration`）：假设、判据、决策规则、冻结版本一次写死；
  并声明**开封只此一次，无论结果**。
- **开封**（`judge_shadow.py --open`，跑在 `git worktree` 钉住的 HEAD 基线上，
  免得并行会话的在制改动把结论带走）：

| 集（封存 test 半边） | 判定器 | 现行 |
|---|---|---|
| wikisource_holdout（n=9） | 6/9 | 4/9 |
| zengshan_dz_holdout（n=7） | 4/7 | 4/7 |
| wikisource_direction（n=15） | 7/15 | 9/15 |
| **合计（n=31）** | **17/31 = 54.8%** | **17/31 = 54.8%** |

- **记账**：结果与结论写进 `test_seal.json.judge_opens`；工具拒绝二次开封。

### 二、结论：**不换判词**

**平手。** dev 上的 +12.5pt（4 例）没有在封存半边复现——那是开发期过拟合。
预注册写的是「≥ 现行则允许另批换判词」，字面上平手满足「≥」；
但那条规则的本意是"判定器要显示出优势才允许破坏性变更"，**平手不是证据**。
另一层硬账：若换，内部 tune 的对齐分将从 97.9 掉到约 36，而干净口径的收益是 **0**——
断崖换平手，不划算。

### 三、这不是"做了一半"

A3 这条线从 313 批走到今天，四步都做完了：
①书证底稿（25 条引文逐字回验）→ ②机器判据（9 格 + 13 覆盖 + 42 书证 + 27 覆写，8 类负例盯门）
→ ③接线（`conclusion.judgment`，可关，verdict 不动）→ ④**预注册开封，结论是不换**。

留在仓里的东西：
- **判定表**＝已签规格（`judgment_table.json` status=accepted，四条裁决在册）；
- **判定器**＝影子通道（`scripts/judge.py`，判定块可关，verdict 一字未动）；
- **三道新门**（[33] 判定表／[34] 考卷哨兵／[35] 内核同源）；
- **一条结论**：在现有证据下，判定表没有推翻现行判词的资格。

将来若要再议：**必须重新采集新案例、重做预注册、再开封一次**——这批考卷已经开封，不重开。

## 2026-10-29 第三百二十七批（六爻）：**第二个试验也回退＋一个方法论补丁——基线会漂，量对比必须钉住 HEAD**

**性质**：shadow 迭代 ＋ 方法论。`verdict` 未动，两集读数与 golden 未动。
（批号取 327：326 被并行会话占用，同号会掩盖它的未结案孤儿——那笔账该它自己结。）

### 一、第二个试验：「世受克 → 不成」也回退

书证《增删卜易》源L1565「诸占最怕克世」，看着像个通用规则；底本紧跟着就给了反例——
源L1685「用克世勿作凶看」（占财／占行人／占医药反作吉）。实测**大幅变差**：
wiki·dev 75.0→41.7、wiki_direction·dev 50.0→35.7。→ **回退**。
结论：这条只能进**题类覆盖层按题类分别判**，不能作通用九格规则。
事实保留（判断块会报"世受克／用神克世／忌神克世"），供后续按题类取用。

### 二、方法论补丁：**基线会漂**

做对比时发现"现行引擎"的读数从 7/12 变成 6/12——并行会话正在改
`liuyao/scripts/evaluate.py`（未提交）。**结论会被别人的在制改动带走。**

处置：`git worktree add /tmp/<名> HEAD --detach` 把基线钉在 HEAD 上量。在钉住的副本上复测：
325 批的记录**逐位复现**（wiki·dev 75.0／direction·dev 50.0／dz·dev 83.3）。
今后凡做「判定器 vs 现行」的对比，**必须在钉住基线上量**。

### 三、外部干净集结论不变

| 集 | 判定器 | 现行（钉住基线） |
|---|---|---|
| wikisource·dev（n=12） | 75.0% | 58.3% |
| zengshan_dz·dev（n=6） | 83.3% | 33.3% |
| wikisource_direction·dev（n=14） | 50.0% | 57.1% |
| **合计 n=32** | **65.6%（21/32）** | **53.1%（17/32）** |

+12.5pt（多对 4 例），**不显著**。仍不换判词；下一步优先级：补归因 > 扩题库 > 换判词。

## 2026-10-29 第三百二十五批（六爻）：**证据基数扩到 n=32——方向集入册；结论修正为「判定器更好，但不显著」**

**性质**：measurement（扩证据，不动判据）。`verdict` 未动，两集读数与 golden 未动。

### 一、《增删卜易》已挖干净，新例只能从别的底本来

跑 `fetch_wikisource_cases.py`（网络可用）：爻图块 253 个、引例头 317 处，
三方校验（纳甲／卦变／世应）**不合 0 处**——但可入外部集仍是 **50 例**，方向集 31 例。
剔除计数说明瓶颈不在解析：应期句缺失 107 处、无占题头 79 处、无月 12 处。
**结论：这个底本榨干了**，扩题库只能换底本（易冒／易隐／易林补遗尚无同格式采集器）。

### 二、但方向集本来就是现成的干净证据

`wikisource_direction`（31 例，有吉凶无应期）此前**未入封存册**，因为它缺应期。
可判定器判的正是**方向**，不需要应期——它就是为这个口径准备的。
本批按 50/50 入册（dev 15／test 16，阈值 35.0），哨兵从 2 个集变 3 个集。

首测就给出个**反例**：方向集 dev 上判定器 **50.0%** vs 现行 **57.1%**——判定器并非全面领先。

### 三、合并后的干净证据（三个外部 dev 半边）

| 集 | 判定器 | 现行 |
|---|---|---|
| wikisource·dev（n=12） | 75.0% | 58.3% |
| zengshan_dz·dev（n=6） | 83.3% | 33.3% |
| wikisource_direction·dev（n=14） | 50.0% | 57.1% |
| **合计（n=32）** | **65.6%（21/32）** | **53.1%（17/32）** |

**+12.5pt（多对 4 例），但不显著**——两 Wilson 区间大幅重叠。
结论修正：证据基数从 n=18 扩到 n=32，方向由「判定器更差」变成「判定器更好但没到显著」。

### 四、因此还是**不换判词**，但理由换了

不是"证据不足所以拖"，而是两条更硬的理由：
① 差 4 例不显著，此时换判词等于拿噪声做破坏性变更；
② 内部 tune 35.7 vs 78.6 的差距还没解释完（归因②九格缺事实、③书内冲突两桶未清）。
下一步优先级：**补归因 > 扩题库 > 换判词**。

### 五、顺带做的一个反证

哨兵 3 秒跑完三个集——太快，怕是假绿。把阈值临时调到 99 试它：三集齐红（rc=1），还原后 rc=0。
**"只给红绿"的门也得自己证明它在算分**，否则它只是一句输出。

## 2026-10-29 第三百二十四批（六爻）：**窄版题类优先——holdout 反超现行；同时给出「现在还不能换判词」的证据理由**

**性质**：shadow 迭代（`verdict` 未动，两集读数与措辞指纹未动）。

### 一、窄版题类优先

323 批的全量版「题类接管」（7 类题类未命中即判待时）实测更差已回退。
本批试**窄版**：只对书证明说「且待时／难求」的三类接管——

- 功名：源L419「占功名者若得官鬼持世即许成名，子孙持世且待时」→ 本类规则未命中即「待时」；
- 求财：源L419「占求财妻财持世者必得，兄弟持世者难求」→ 同上；
- 婚姻：源L756「诸合皆以用神旺者为吉」→ 同上。

### 二、结果（同分母、两引擎同口径）

| 集 | 判定器 v5 | **v6** | 现行 |
|---|---|---|---|
| wikisource·dev（n=12） | 75.0% | **75.0%** | 58.3% |
| zengshan_dz·dev（n=6） | 83.3% | **83.3%** | 33.3% |
| holdout（n=11） | 45.5% | **63.6%** | 54.5% |
| tune（n=14） | 42.9% | **35.7%** | 78.6% |

**holdout 反超现行**（63.6 vs 54.5），外部两半边不变，tune 退 7pt。

### 三、一个明确的结论：**现在还不能换判词**

外部 dev（干净口径）只有 n=12 与 n=6 两集，现行引擎的对外头条数字却来自 tune/holdout。
**用 n=18 的干净集去推翻 n=32 的污染集，证据不成比例。** 换判词属破坏性变更，
在证据基数不足时做，是拿"看起来更对"换"可核验的证据"——不划算。
下一步应先：① 扩题库（B3，把外部 dev 做到 n≥60）；② 补齐剩余归因（② 九格缺事实、③ 书内冲突）。

判定表现为 `9 格 + 13 覆盖 + 42 书证 + 27 覆写`；golden 机械指纹重基线
（`fe956051…`→`6f707fba…`，**措辞 `405bc8e0…` 六批未动**），账台同步。

## 2026-10-29 第三百二十三批（六爻）：**内部差距归因＋轴分流——外部 dev 两半边 75.0／83.3；一个被回退的试验也留了账**

**性质**：shadow 迭代（`verdict` 未动，两集读数未动，措辞指纹未动）。

### 一、内部两集的 18 处分歧，逐例归成四类

| 类 | 例数 | 处置 |
|---|---|---|
| ① **分流错误**（题类判错、轴没分开） | 6 | **本批已修**：裸「讼」会命中卦名「巽之讼」→ 行人/失物题被误判成讼事题；归期类时间题（何日回/何日领/何日归）与价势题（价/贵贱/涨跌）混进吉凶轴 |
| ② **九格缺事实** | 约 6 | 例：ZS012/HO011——通用「生世→成」在功名、婚姻题上越权（源L419 说功名只有官鬼持世才算成，生世只是「且待时」） |
| ③ **书载判断超出九格可表达范围** | 2 | 例：ZS002 近病逢空、书判凶，与源L1619「不拘日月动爻克害，用神出空之日即愈」直接冲突 → 登记为书内冲突，不硬凑 |
| ④ **量的问题** | 其余 | tune/holdout 是现行引擎的调参集与回归集，引擎天然占优（319 批已把主判据定为外部 dev 半边） |

### 二、本批改了什么

- **轴分流**（依据已签 JT-D「时间题另表」＋ `verdict_map` 里「下跌」那条的注「义为价跌不是事败，不得直接映射」）：
  时间题与价势题**不参与吉凶方向比较**，判定块记 `不适用·时间` / `不适用·价势`。两引擎同口径排除。
- **题类关键词修正**：去掉裸「讼」（命中卦名 巽之讼／天水讼），新增「失物」类（底本暂无对应章，故不接管，仍走九格）。
- **疾病覆盖补一条**：卦六冲或用神真空、且非久病 → 近病不药而愈（Z1/Z2）。

### 三、一个试过又回退的试验（留账）

试过「**题类接管**」：题类在场而本类规则未命中时，不回落通用九格，改按本类默认口径判「待时/未决」。
实测 **tune 42.9→28.6、wiki·dev 75.0→66.7**，明显更差 → **回退**。
结论：**书的总纲与分类占法是叠加关系，不是替代关系**——分类规则命中就接管，没命中仍要走总纲。
（代码里留了注释与 `DOMAIN_DEFAULT` 残迹作反面记录。）

### 四、结果（同一分母、两引擎同口径）

| 集 | 判定器 | 现行 | 轴不适用（排除） |
|---|---|---|---|
| wikisource·dev | **75.0%**（9/12） | 58.3%（7/12） | 4 |
| zengshan_dz·dev | **83.3%**（5/6） | 33.3%（2/6） | 2 |
| holdout | 45.5%（5/11） | 54.5%（6/11） | 1 |
| tune | 42.9%（6/14） | 78.6%（11/14） | 6 |

外部两半边仍显著领先；内部两集仍落后，归因见 §一。
golden 机械指纹随判定块内容重基线（`af965c95…`→`fe956051…`，**措辞 `405bc8e0…` 五批未动**），
账台期望同步。

## 2026-10-29 第三百二十二批（六爻）：**覆盖层补全到 13 条（合伙／讼事／婚姻）——dz dev 62.5→75.0，两个外部 dev 半边都到 75%**

**性质**：shadow 迭代（判定块已接线，`verdict` 未动）。零判词改动，两集读数与措辞指纹未动。

### 一、补了三类题（书证逐条）

- 合伙：《增刪卜易》源L3082「世应临兄不吉，兄爻发动不吉」→ 世临兄弟爻或兄弟爻发动 → 不成。
- 讼事：《增刪卜易》源L419「占防忧虑患者，若得子孙持世无忧，官鬼持世忧疑难解」→ 官鬼持世 → 不成。
- 婚姻：《增刪卜易》源L756「独此六冲卦变六合得不看用神，竟以吉断」→ 卦变六合 → 成。

**书证例外登记未实现**：《增刪卜易》源L1565「独官鬼持世者……最宜日月动爻相冲克，反为吉矣」——
它要"日月动爻冲世"的判定，本批没做，故在表里以 `exception_cites` ＋ `exception_not_implemented` 登记，
**不假装已实现**。门 [33] 新增判据：列了例外书证却不写未实现说明＝判红。

### 二、结果（dev 半边）

| 集 | v3 | **v4** | 现行 |
|---|---|---|---|
| wikisource·dev（n=16） | 75.0% | **75.0%** | 56.2% |
| zengshan_dz·dev（n=8） | 62.5% | **75.0%** | 37.5% |
| holdout（n=12） | 41.7% | **41.7%** | 58.3% |
| tune（n=20） | 45.0% | **45.0%** | 80.0% |

两个外部 dev 半边都到 **75.0%**，比现行引擎高 18.8pt 与 37.5pt。
内部两集仍落后（现行引擎的调参集／回归集，天然占优）。

### 三、golden 与账台

判定块内容变化 → `concl_sha` 漂移 → 按规程 `capture` 重基线（机械 `184e628a…`→`af965c95…`，
**措辞 `405bc8e0…` 四批未动**），`drift_log` 记归因，账台期望同步。
判定表现为 `9 格 + 13 覆盖 + 42 书证 + 27 覆写`。

## 2026-10-29 第三百二十一批（六爻）：**判定器 v3：修一个真 bug、回书证的"有气"口径、补世应层——外部两个 dev 半边超出现行 18.8／25.0pt**

**性质**：shadow→shadow 迭代（判定块已接线在 `conclusion.judgment`，但**未取代 verdict**）。
`step5` 一字未改，两集读数与措辞指纹未动；只有判定块内容变化（机械指纹随重基线更新）。

### 一、摊开逐例事实后抓到的三件事

1. **一个真 bug（我的）**：`忌神无力` 写成 `... or ji_pos`，而 `ji_pos` 是**列表**——
   `if 忌神无力` 恒为真（忌神只要在位就算"无力"）。319 批那条规则基本在空转。
   这是典型的"真值当条件用"：列表非空即真，**门查不出来，因为门只查字面**。
2. **有气口径被我放宽过**：v2 为追分把"中和"算进有气；按书证（源L68 注文「旺相为有气，休囚为无气」）
   中和属"不旺不衰"（《增刪卜易》源L31「旺不旺而衰不衰，凶不凶而吉不吉」），已改回旺相。
3. **缺一整层：世应关系**。底本把它当一等 citizen：
   《增刪卜易》源L3578「受克者必受其殃，生世者反得其济」
   反面条款——《增刪卜易》源L1685「谓忌神既旺，用衰矣，世虽逢生何益」——两条一起进（Z12／Z13），
   只取正面条款就是过拟合。

### 二、结果（dev 半边，test 未动）

| 集 | v2 | **v3** | 现行 |
|---|---|---|---|
| wikisource·dev（n=16） | 62.5% | **75.0%** | 56.2% |
| zengshan_dz·dev（n=8） | 37.5% | **62.5%** | 37.5% |
| holdout（n=12） | 41.7% | **41.7%** | 58.3% |
| tune（n=20） | 40.0% | **45.0%** | 80.0% |

**两个外部 dev 半边都明显超出现行**（+18.8pt／+25.0pt）；内部两集仍落后——
tune/holdout 是现行引擎的调参集与回归集，引擎天然占优（319 批已把主判据定为外部 dev 半边）。

### 三、golden 与账台

判定块内容变化 → `concl_sha` 漂移 → 按规程 `capture` 重基线（机械 `ffa4944b…`→`184e628a…`，
**措辞 `405bc8e0…` 三批未动**），`drift_log` 记归因；账台期望同步并注明。
判定表现为 `9 格 + 10 覆盖 + 38 书证 + 27 覆写`。

### 四、下一步（c：覆盖层补全）

19 处 `domain_overlay` 里只覆盖了 4 个题类（疾病/功名/求财/行人）；
婚姻、合伙、词讼、失物、财货走势五类仍无书证覆盖，待下一批按底本补。

## 2026-10-29 第三百二十六批（六爻）：**《易隐》立册——56 条完整盘面入外部验证集（本批新增案例最多的一集）**

**性质**：content（新增案例集 ＋ 新增抽取器 ＋ 新增审计报告 ＋ 一处分片登记）。零判词改动、零引擎改动、golden 未触碰。

### 一、为什么是《易隐》：书在盘上，案例是零

《易隐》（清·曹九锡辑）底本 151,457 字、**59 个规整六爻卦表**（带六神／伏神两列、`○→`/`×→` 动标、
世应写爻侧），此前只在 `verifications.json` 留了 13 条 `status=「仅验语」` 的台账——**有声无盘，
从未进过任何 `*_cases.json`**。同期《增删卜易》已抽 246 条、《卜筮正宗》已抽 90 条，本书抽取率是 0。

这不是「书里没有」，是「没人抽」。

### 二、`dev_tools/build_yiin_cases.py`：九道门，机器判

底本 `data/sources/yiin_dz.dz.txt`（443,460 字节，sha256 `a9a8ff45…`，与 provenance 一致）。

| # | 门 | 实测 |
|---|---|---|
| 1 | 块高恰 6 行 | 59/59 |
| 2 | 卦名可解析（`山雷颐`→颐、`乾为天`→乾） | 59/59 |
| 3 | **纳甲自洽**：六爻地支 ≡ 内核 `najia_branch` 逐位 | 56/56 |
| 4 | **阴阳自洽**：爻符号 ≡ 内核 `BAGUA_LINES` 推得爻性 | 56/56 |
| 5 | **动爻自洽**：标记位集合 ≡ 本卦⊕变卦差集 | 56/56 |
| 6 | 时点可还原（月建＋日柱） | 56/59 |
| 7 | 占题可解析 | 56/56 |
| 8 | 应期只取实录 | 7/56 |
| 9 | 同案去重（键含**占题**） | 57/57 |

门 3/4/5 三重自洽等于**用内核把 56 个古籍盘面重新装了一遍并逐位对上**——这是转录无误的机器证明。

**门 9 的口径修正**：初版按「本卦＋变卦＋月建＋日柱」判同案，一次剔掉 7 条，把本书的**教学式复用**
误杀了——它把同一盘（同卦同月日）分派给四五个不同占题演示（如「睽之归妹·丙子月丁卯日」分别占
坟茔／婚姻／求官／求财），那是同盘异题、用神各各不同，不是重复占验。判定键改为含占题后误杀归零。

**排除 3 条**（写明原因，不猜补）：L1362 月建写作「巳卯」（干支不合）、L1605 与 L1953 无独立日辰
（后者是「是月是日有占起官者」的承接省略）。

### 三、定位：盘面语料 ＋ 应期语料，吉凶一律留空

- **56 条完整盘面**：静卦 11、单动 31、双动 13、三动 1；八宫全覆盖；占类 12 种（功名 10／疾病 8／
  词讼 7／求财 7／婚姻 4／行人 4／寿命 3…）；54 条带年、27 条带旬。
- **应期**：实录 7 条（`果/故/竟/卒` 前置或 `日故` 后置）进评分；书判预期 9 条（`待/直至/次日/逢`
  之后）记入 `yingqi_claim`，**只作参考、不进分母**——不把「书说会在某日」当成「实际某日」。
- **吉凶一律 null**：本书断语是散文（「决难免死」「理宜多寿」「后果然」），映射吉/凶属解读，越铁律一。
  本批试过关键词规则，实测误判（「故当终命也」被判吉），**宁可留空，不给假基准**。

### 四、读数（strict，n=56）

对齐分 **43.9%**，主应期命中 **28.6%**，应支平均名次 **2.25**。

这个分明显低于在册其他集（wikisource 75.8%、yingqi 87.9%），原因是本书占类偏「迁移／坟茔／婚姻」
等**方位与成败**判断、不给应期日，56 条里仅 7 条有实录应期，分母小、噪声大；加上引擎在方位类占事上
本就弱。**不是案例有问题**，但 n 小，只能当参照。

### 五、附带

- `scripts/evaluate.py` 的 `--split` 增列 `yiin_holdout`；
- `dev_tools/check.py` 的外部集备注表增一行；
- 新增 `docs/YIIN-CASE-AUDIT.md`（采集口径、排除明细、分布、读数、复现命令）。

### 六、顺带修两处存量裸指针（`docs/JUDGMENT-TABLE.md`）

本批收尾跑门时，[14] 报出该文件两行**裸指针**（有行号无同行引文，书名待定位）——那是前序改动留下的，
与本批无关，但门红就得修。查下来根因有二，都不是「引文写错」那么简单：

1. **该文档从未按格式声明底本**（只在正文提了文件名 `zengshan_buyi_dz.dz.txt`，缺 `data/sources/` 前缀），
   于是回验器认不出书名 → 锚点一律「书名待定位」→ 裸指针。补上标准底本声明后，
   该文档其余锚点**722/725 逐字命中**，未引爆其他条目；
2. **行号本身是错的**：原文写「源L68 注文"旺相为有气，休囚为无气"」「源L31」，而按本文件自己声明的
   口径（`源L` 一律指增删卜易/黄金策的 **dz 本**），增删卜易 dz L68 是章题行「月破章第二十七」、
   L31 是野鹤曰那段，**都不是这两句**。全底本检索后找到真出处：
   「旺相为有气，休囚为无气」在**《黄金策》dz L69**，「不旺不衰」在**《增删卜易》dz L2751**。

改成《书名》＋正确行号＋逐字片段后判红归零。**行号写错比不写更坏**——不写只是缺证据，
写错会让后来的人按错行号去核，核到章题行上还以为书证成立。

分片登记在 `data/cases/case_splits.json` 的 `yiin_holdout`：**外部验证集，永不参与调参**。

## 2026-10-29 第三百二十批（六爻）：**判定块接线——`conclusion.judgment` 进产品（可关）；`verdict` 未动；golden coverage-only 重基线**

**性质**：contract（契约面新增一个 optional 键）。**判词一字未改**：两集读数与 verdict 全线未动。

### 一、接了什么

- `scripts/analyze.py`：`analyze(chart_json, judgment_enabled=True)`；CLI `--no-judgment`。
  `conclusion` 里多一个 `judgment` 块（12 键：`direction`／`confidence`／`cell`／`base_cell`／`why`／
  `cites`／`support`／`dissent`／`domain`／`overlay`／`verdict_now`）。
  判定器导入或运行失败时**不产出该键**并写日志——绝不塞一个像结论的空块。
- `judgment` 与 `verdict` **并列**：前者是九格判定，后者仍是现行引擎的档位。
  并列是为了能逐例对拍，不是因为判定器已取代判词（`judgment_table.json.implementation.verdict` 在册）。
- `scripts/judge.py`：题类覆盖层的 10 条规则补上 id（`OV-D1`…`OV-X3`），判定块能报出"哪条规则改的"。

### 二、契约面（三处同步）

- `data/rules/layer_contract.json`：`conclusion.allowed` 加 `judgment`（**不在 `required` 里**——
  `judgment_enabled=False` 时该键整个不出现）；门 `[32]` 复跑绿。
- `CONTRACT.md` §四：六爻 `conclusion` 键数 11→12，并写明"为什么属于这一段"（由推演事实判定、不是文案）。
- `SKILL.md` **故意不动**：判定块尚未取代判词，暴露给宿主模型等于让它拿未定稿的判据下结论；
  插件 1.0 冻结面因此零变更。

### 三、golden：先补盲区，再重基线

第一次 `golden.py verify` **没漂移**——因为它直接调 `_conclusion_from`，新增的 `judgment` 落在指纹之外：
**新键没有看门狗**。照 193 批的办法把判定块并进指纹，于是漂移被正常抓到，
再按规程 `capture`（附归因）重基线：机械 `4ceef1ee…`→`ffa4944b941a2755`、**措辞 `405bc8e0…` 未动**。
归因写进 `digest.json.drift_log`：coverage-only 重基线，非行为退化。账台期望同步并注明。

### 四、读数与逐格对拍（§四 要求的两样）

- **两集出分**：tune 97.9%（n=20）／holdout 90.2%（n=12）——**与接线前逐位相同**（verdict 未动）。
- **逐格对拍**（判定器 vs 现行 verdict vs 书载方向，内部两集）：
  tune 现行 80.0% / 判定器 40.0%；holdout 现行 58.3% / 判定器 41.7%。
  内部集差距仍大（下一批处理）；外部 dev 半边达标状态不变。

### 五、两条不在本批的红（并行会话在制改动）

- 账台 `governance` 实得 62/38（期望 61/37）：对方给八字加了 dev_tools 脚本。
- 账台 `八字案例分母` 第三项 53→62：对方给八字外部集加了 9 例。
两条都不属本批，期望值未动（等对方提交后由其批次登记）。

## 2026-10-29 第三百一十九批（六爻）：**判定器 v2 加原神/忌神二级事实——外部两个 dev 半边达标（wiki 反超现行 6.3pt）**

**性质**：shadow（A3 第五步）。仍零判词改动，golden 未触碰。

### 一、二级事实从哪来

v1 的结论是"差口在用神无气但事成那批例子，要二级事实"。底本里正好有整套判法：

- 《增刪卜易》源L541「元神能生用神者有五」
- 《增刪卜易》源L553「此忌神者乃无力之忌神也，诸占化凶为吉」
- 《增刪卜易》源L553「倘若用神无根，谓之元神有力亦难生」
- 《增刪卜易》源L561「接续相生，化凶而为吉」

据此加 **4 条书证（Z8–Z11）**、**2 条规则**：

- `R0′ 成·低`：无根 + 原神有力 + 忌神无力 → 成，但**置信只能低**（无根难生，Z10）；
- `R4b 成·中`：有根 + 忌神无力 → 成（化凶为吉，Z9）。

### 二、结果（只看 dev 半边）

| 集 | v0 | v1 | **v2** | 现行 |
|---|---|---|---|---|
| tune（n=20） | 30.0% | 33.3% | **40.0%** | 80.0% |
| holdout（n=12） | 30.0% | 33.3% | **41.7%** | 58.3% |
| wikisource·dev（n=16） | 50.0% | 50.0% | **62.5%** | 56.2% |
| zengshan_dz·dev（n=8） | 12.5% | 37.5% | **37.5%** | 37.5% |

**外部两个 dev 半边已达标**：wiki dev 反超现行 6.3pt，dz dev 与现行打平。
内部 tune/holdout 仍落后——但那两集是现行引擎的调参集与回归集，引擎天然占优，
**不该当主要判据**（这是 315 批封存机制带来的好处：现在能分清哪把尺子干净）。

### 三、验收口径的修正（要说清楚，不藏）

原写的验收线是"dev 半边全数 ≥ 现行"，现改为：**外部 dev 半边 ≥ 现行**（wiki/dz），
内部 tune/holdout 降为**回归护栏**（不得更差）。
理由：内部两集被现行引擎调过参，在其上比较等于拿尺子量自己。

### 四、为什么不接线

接线会动 golden 双指纹、评测 expected 与插件 1.0 契约面——是**破坏性变更**，
按 AGENTS §四 须另批走：两集出分＋逐格对拍＋golden 重基线＋契约变更面登记。
本批只把判定器推到"外部口径达标"，**接线单独立批**。

### 五、门与读数

门 [33] 保持 8 类负例全绿（新增书证后，原负例里的 `Z9` 变成真 id，已改用 `Z99`）。
判定表现为 `9 格 + 10 覆盖 + 36 书证 + 27 覆写`。golden `4ceef1eed62dafe2`／
`405bc8e03a6a99e0` 未动；tune 97.9／holdout 90.2 未动；`check.py` rc=0（[11] 除外，见下）。

## 2026-10-29 第三百一十九批（六爻）：**奇问杂占读法落地 ＋ yi_kb 二字窗停用表与稀有度权重（召回修复）**

**性质**：content＋runtime（C1）。零判词改动、零引擎改动、golden 未触碰。

### 一、`references/odd_questions.md`：问得怪、问得虚、问得越界怎么接

`interpretation_guide.md` 覆盖的是标准题类（财、婚、病、官、行人），而真实会话里大量问题
不在题类表内：失联寻宠、怪梦、异响、"是不是有东西跟着我"、"他有没有骗我"。此前模型只能
靠常识兜，最容易滑向两处：**迎合恐惧**（"确实有东西"）与**替人判决**（"他没出轨"）。

本篇按"先判断该不该用卦答，再谈怎么读"组织，全部判据取自库内底本：

| 节 | 内容 | 书证 |
|---|---|---|
| §二 | 一念只占一事、占勿二念、不诚多因不关切 | 增刪卜易（诚心三句） |
| §四 | 失联寻宠／怪梦／异象／"他在想什么"／号码择方，逐类给"看什么"与"不能说什么" | 增刪卜易占梦三例、占鬼神条 |
| §五 | 前事与未来：爻位分已往未来（进为将来、退为已往） | 易隐、易冒 |
| §六 | 再占之礼：何时可再摇、何时是求签 | 增刪卜易（两说并存，如实并列） |
| §七 | 不可占五类＋拒答话术（拒答后必须给替代问法） | 本库政策（明标非古法） |
| §八 | 人情味七条＋冷暖对照表 | 文风层，非判据 |

**取用神一律不归本文管**：用神仍由 `question_use_gods.json`（74 族／275 键）与关系法则层判定，
`use_god_basis` 会标明是逐字书证、覆盖规则还是无据推断；本篇只讲"取到之后怎么读"，
不另判一遍（铁律一）。

### 二、召回修复：新文档把「世应」问句的正确篇挤出了前五

加文档后 DSH 自检 [12] 判红：`世应怎么安`（无空格长问句，只能靠二字窗兜底）召不回
`najia_rules.md`。查因不是测试挑剔，是**打分本身有缺陷**：

1. 二字窗每个封顶 4 分、不看稀有度——满篇「怎么」的文档与真正讲「世应」的文档同分；
2. 同分再按文件名排序，`bazi/` 恒在 `liuyao/` 前，纳甲规则被挤出前五。

修法（`plugins/mcp/kb.mjs`，五宿主同源）：

- **停用表**：`怎么／什么／如何／是否／可以／我们…` 等 22 个疑问与功能二字窗不进召回
  （精确词项优先，实词一律照旧）；
- **稀有度权重**：`1 + 3*(1 - df/总节数)`，df 为该字窗出现的节数——「世应」压过「怎么」；
- **对数饱和**：`log2(1+count)` 取代线性封顶，出现 12 次不比 3 次更相关。

复测（五宿主构建后）：`世应怎么安` 前五含 `najia_rules.md`；`纳甲 装卦 世应` 首位为
`najia_rules.md`（32.0）；`用爻`→`用神` 同义展开仍召回；无关词 `汽车维修zzz量子塌缩` 仍零命中
（负例未破）。

### 三、读数（本批实跑）

- `python dev_tools/check.py` → **全绿**（含 [35] 内核同源 17 文件／两科）；书证回验新增
  `references/odd_questions.md` **14/14 逐字命中、0 判红**（该科回验器对裸指针本来就判红，
  本篇按"每条锚点必带同行引文"写）。
- `node plugins/scripts/selftest.mjs` → 全绿（知识库 13 篇 + INDEX，Yan resources 14 条双向一致）。
- `npm --prefix dsh-plugin run selftest` → **自检全部通过**（[12] 召回三例全绿）。
- 金标准／判词／应期未动。

### 四、开口

- 奇问里的"非人对象"（宠物、房屋、号码）取用仍属词典类推，古籍无逐条依据；
  `use_god_basis` 会标"无古籍逐条出处"，正文须照实说，本批未把它变成书证。
- 灵异类只做到"降恐惧＋排现实因素"，不提供任何化解方案——无判据，且易滑向收费陷阱。

## 2026-10-29 第三百一十八批（六爻）：**判定器 v1 加题类覆盖层——dz 半边一步追平（12.5→37.5），仍未过验收线**

**性质**：shadow（A3 第四步）。仍零判词改动：`step5` 的 verdict 一字未动，golden 未触碰。

### 一、覆盖层从哪来

314 批量出"27 处覆写里 19 处是题类覆盖"，但没说题类规则该长什么样。本批在底本里找到一句现成的总表
——**源L419**：`占功名者若得官鬼持世即许成名，子孙持世且待时。占求财妻财持世者必得，兄弟持世者难求。
占病者若得六冲卦近病不药而愈，久病妙药难调。`
再加 源L31（近病逢冲逢空／外病灵丹莫救）、源L1694（`占财财为用神，财爻克世者必得。占行人用神克世者即至`）、
源L3298（`世克用兮人未动，用爻克世必然归`／`卦逢六冲，行人无定而不返`），共 **7 条新书证（Z1–Z7）**、
**10 条覆盖规则**，覆盖疾病／功名／求财／行人。

### 二、结果（只看 dev 半边）

| 集 | v0 | **v1** | 现行 | 覆盖命中 |
|---|---|---|---|---|
| holdout（n=12） | 30.0% | **33.3%** | 58.3% | — |
| wikisource·dev（n=16） | 50.0% | **50.0%** | 56.2% | 1/25 |
| zengshan_dz·dev（n=8） | 12.5% | **37.5%** | 37.5% | 3/10 |

**dz 与现行打平**，v0 到 v1 的 1/8→3/8 全部由覆盖层贡献——"缺口主要在题类层"这个判断被证实。
wiki 持平、holdout 差 25pt；剩差在九格对"用神无气但事成"的处理（需原神动／忌神空／日月生扶这类二级事实），
不在题类。**验收线未达，继续影子模式。**

### 三、门 [33] 扩到覆盖层

新判据四条：覆盖层必须有 domain／when／emit 两轴合法／声称 book_verified 就得有 cites；
书证引用闭合（Z1–Z7 被引用后才不算孤儿）。selftest 从 6 类负例增到 **8 类**（新增"方向不在轴内"
"引用不存在的书证"）。判定表现在是 `9 格 + 10 覆盖 + 32 书证 + 27 覆写`。

### 四、读数

golden `4ceef1eed62dafe2`／`405bc8e03a6a99e0` 未动；tune 97.9／holdout 90.2 未动；`check.py` rc=0。

## 2026-10-29 第三百一十七批（六爻）：**四条裁决签署 + 判定器 v0 影子对拍——结论是「不达标，不接线」**

**性质**：design→shadow（A3 第三步）。零判词改动：`step5` 的 verdict 一字未动，golden 双指纹未触碰。

### 一、四条裁决签署（`judgment_table.json` → `accepted`）

| 条 | 问题 | 签的答案 | 依据 |
|---|---|---|---|
| JT-A | 月破兼动 | 采 **F2**（破而静/破而动分开） | 同书作者自验，且 F2 自带分界（源L991） |
| JT-B | 月日权重 | **6:4 标为「非书证·工程默认」**，不改读数 | 书证只说"同功"（A2），改权重须独立批走 §四 |
| JT-C | 用神与世 | **方向由用神定，世只降置信** | 源L436「自占以世为用」＋源L68「用爻有气则成」 |
| JT-D | 时间题 | **判定表只管吉凶题，时间题另表** | 与 `shijian_tiying_verdict_dual` 同批口径 |

### 二、判定器 v0 与影子对拍器

- `scripts/judge.py`：8 条谓词 → 9 格，**不读 verdict／final_score**（读分数＝把被审对象当判据）。
  事实源只用 step2/3/4/5 的结构字段；「有气」按书证取"旺相＋中和＋日辰生扶"（源L68 注文、源L1079）。
- `dev_tools/judge_shadow.py`：三方同屏（现行 / 判定器 / 书载），带 `--dev-only`
  ——**判据开发只许在 dev 半边做**，这是 315 批封存机制第一次真的挡住自己。
- `scripts/case_runner.py` 加 `full=False` 形参：`full=True` 才挂 `_full`（analyze 全量产物），
  默认形状不变，评分器与指纹不受影响。

### 三、结果：v0 差得明白，所以不接线

| 集 | 判定器 vs 书载 | 现行 vs 书载 |
|---|---|---|
| tune（n=20，in-sample） | 30.0% | **80.0%** |
| wikisource·dev（n=16） | 50.0% | **56.2%** |
| zengshan_dz·dev（n=8） | 12.5% | **37.5%** |

失败原因是结构性的，不是调参能补：v0 的 8 条谓词全在"用神有气/受克/有救"这一层，而 314 批
已经量出 27 处覆写里 **19 处是题类覆盖**。dz 半边以占病、官讼为主，题类层一缺席就塌。

**接线条件写进了 JSON**（`implementation.acceptance_criterion`）：dev 半边同向率 ≥ 现行，
且不得只靠 8 条谓词。未达标前 `judge.py` 只做影子。

### 四、一处自纠（[14] 当场抓的）

`judge.py` 初版注释里写了十几个裸 `源L1663`——被 `[14]` 判「裸指针」十条。
改法不是补引文，而是**改指书证 id（E1/A3/F1…）**：引文只存一份在 `judgment_table.json`，
代码里再抄一遍行号就是制造第二个会腐的副本。改后 `[14]` 复跑全绿。

### 五、读数

golden `4ceef1eed62dafe2`／`405bc8e03a6a99e0` 未动；tune 97.9／holdout 90.2 未动；
`check.py` rc=0（35 节）；账台 governance 60→61（新增 `judge_shadow`，ondemand 档）。

## 2026-10-29 第三百一十六批（两科）：**内核收成单一真源——kernel/ 生成两科 core，八字顺手减 874 行；"零耦合"口径改写完成**

**性质**：architecture（C2）。产物字节与原文一致（只删未引用模块），golden 双指纹未动。

### 一、做了什么

- 新建 `kernel/`：`yishu_core/common/`（10 个两科共用）+ `yishu_core/variants/<名>.<科>.py`（4 个在册分叉）
  + 3 个六爻专用 + 1 个八字专用；`kernel/MANIFEST.json` 是唯一登记表（每个变体都写了一句"为什么分叉"）。
- `kernel/sync_kernel.py`：`--check` 比对字节、`--write` 重生成（会删产物里的未登记 `.py`）、`--selftest` 两类负例
  （改产物 / 塞野文件），**负例之后必须再跑真盘**——只证"器是活的"不证"盘是对的，是 §四.8 的老教训。
- 两科 `core/yishu_core/` 降为**产物**，手改即被 `[35]` 判红。`[35]` 挂进六爻 `check.py`（读两科，跨科只读）。

### 二、八字侧删除的三个模块（以及一处自我更正）

`hexagram_texts.py`（591 行，卦辞爻辞）、`najia.py`（39 行，纳甲支表）、`calendar_check.py`（244 行，历法核对）
在八字侧**无任何 import**（AST 全扫），且都被打进过发布包。删后 八字内核 18→15 文件。
**自我更正**：我此前口头报"1029 行死代码"，把 `yingqi.py`（155 行）也算进去了——但
`core/yishu_core/feedback.py` 有两处 `from yishu_core.yingqi import …` 转调用，它**不是死代码**。
实数 **874 行**（591+244+39）。首次筛查只扫了 scripts/dev_tools/tests，漏了 core 内部互相引用，记一笔。

### 三、口径改写（不然就是文档说谎）

- `AGENTS.md` §二 目录树 + 「零耦合」条：13/17 的手抄实测改为"kernel 单一真源 + 4 变体 + 产物"，
  并写明**"零耦合"约束的是运行时依赖，不是源码来源**。
- 根 `README.md` 设计原则同改；`bazi/core` 不再携带六爻专用模块这条也写进去了。
- 五家发布包已重建（`plugins/scripts/build.mjs`）并跑 `selftest.mjs` 七段：全绿。

### 四、读数

两科 `check.py` rc=0／rc=0（六爻 35 节、八字 28 节）；golden `4ceef1eed62dafe2`／`fda7482656967518` 逐位未动；
`kernel/sync_kernel.py --check` 报「liuyao 17 文件／bazi 15 文件，与 kernel/ 逐字节一致」。

## 2026-10-29 第三百一十五批（六爻）：**考卷封存 + 口径回改——外部集不再是"未调参集"；哨兵只给红绿**

**性质**：measurement（B1＋B2）。零引擎改动、零读数变化。

### 一、切分与封存（B1）

- `data/rules/test_seal.json`：两集按 case id 的 `sha1` 排序 50/50 切——
  wikisource 50→**dev 25 / test 25**（封存日实测 80.5%，阈值 **65.0**）；
  zengshan_dz 21→**dev 10 / test 11**（55.9%，阈值 **35.0**）。阈值 = 封存日实测 −15～20pt，
  写明依据；只准上调，上调须预注册。
- **不把 dev/test 并列进 `case_splits.json`**：账台的「集合两两∅」断言会把同集的两半判成泄漏。
  改为在 `case_splits.json` 里留一句 `note_test_seal` 指向封存册。
- 新门 `[34] check_test_sentinel.py`：五类判据（dev/test 不相交、test 不落在其它分片、阈值有理由、
  开卷记账齐全、迁移指向真实 test 例），selftest 五类负例全抓。
  **默认只输出 PASS/FAIL，不输出分数**；要分数只能 `--open --hypothesis`（并写进 `opens`）；
  要看逐例只能把该例迁进 dev 并登记 `migrations`。

### 二、口径回改（B2）

删掉全部"未调参/永不调参"声称，改成可核对的现状：

| 位置 | 原文 | 改为 |
|---|---|---|
| `CAPABILITY.md` | "未调参集加 ⚗"＋4 行 ⚗ | 明写"已无未调参集"＋181–309 批的取舍史＋封存机制；行标签改"开发集" |
| `check.py [6]` 横幅 | "未参与任何调参；只报数不设门槛" | "开发集：已参与调参；test 半自 2026-10-29 封存，见 [34]" |
| `window_report.py` | "外部原本集·永不调参" | "外部集·已参与调参（test 半自 315 批封存）" |
| `rank_experiment.py` | "永不调参" | 同上 |
| `build_extra_dimensions.py` | "永不调参的真检验" | "已于 181–309 批参与调参" |
| 根 `README.md`／`liuyao/README.md`／`dsh-plugin/README.md` | "未参与调参" | 同上，并加一句封存说明 |

### 三、一句必须写下来的判断

**切分洗不白已经看过的题。** 这 71 例全参与过历史调参，test 半第一次开卷的成绩仍带污染；
切分的价值是**从此不再看**，不是**从此干净**。对外表述按这句写，不要给读者"切了就等于没看过"的错觉。

## 2026-10-29 第三百一十四批（六爻）：**判定表机器化——25 书证 / 9 格 / 27 处覆写进账；发现"题类覆盖"才是大头**

**性质**：design→data（A3 第二步）。判定表从此有机器判据，但仍 `status: proposed`，未接引擎。

### 一、`data/rules/judgment_table.json`

- 25 条书证（与 `docs/JUDGMENT-TABLE.md` 同源，逐字可回验）；
- 9 格（方向 3 × 置信 3），每格有 enter 谓词与书证引用；
- 9 个判词的二维映射，其中 `平/不利`、`下跌`、`平凶` 标 `legacy`（非标准值，三态化须改 expected）；
- 27 处覆写逐条登记（行号＋条件原文＋赋值＋kind＋domain）；
- 4 条待裁（`JT-A` 月破兼动／`JT-B` 月日 6:4／`JT-C` 用神与世／`JT-D` 时间题分流），全部 `pending`。

### 二、新门 `[33] check_judgment_table.py`（六条判据）

格面恰好 9 格；书证在所指行邻域逐字命中；引用闭合（无孤儿书证）；**表随码动**（从 step5 AST 重算
覆写清单与表内逐条对齐，多一处少一处都红）；kind 合法且 `domain_overlay` 必带 domain；
**值面覆盖**（step5 产出的每个判词字面量都要在 `verdict_map` 里有归处）。
`status: accepted` 的硬条件是四条裁决全部签押——那是人的判断，机器不代签。
selftest 六类负例全抓（含"未签就 accepted"）。

### 三、本批最重要的发现：覆写的大头不是"优先级打架"

AST 实数 **27 处**改判分支（此前口头说 20 处），分类后：`priority` 3 ／ `exception` 5 ／
**`domain_overlay` 19**（行人、合伙、讼事、考试、疾病、失物、财货）。也就是说：
**9 格吸收不了三分之二的覆写**——v2 必须有第三层"题类覆盖"，否则把 27 处硬塞进 9 格只会换个地方堆 if。
该结论已回写 `docs/JUDGMENT-TABLE.md` §三·补。

### 四、读数

零引擎改动：golden 288 例指纹未动，tune 97.9／holdout 90.2 同上批。`check.py` rc=0（33 节）。

## 2026-10-29 第三百一十三批（六爻）：**A3 第一步——判定表书证底稿：25 条引文逐字回验，读出「日月并列」而不是 6:4；四条待裁落纸**

**性质**：design（只出判据底稿，零代码、零读数、零门改动）。产出 `docs/JUDGMENT-TABLE.md`。

### 一、为什么先做书证

A3 要把「一维分数 + 20 处覆写」换成「方向 × 置信」9 格。9 格的内容不能由工程直觉定，
必须能指回书。所以第一批不做代码，只做一件可验证的事：**把"谁压谁"从古籍里读出来，逐条钉行号**。

### 二、读到什么（25 条引文，全部 `源L` 可回指）

- **层级**：`日辰爲六爻之主宰﹐月將是萬卜之提綱`（源L915）＋`日月如天如君﹐六爻如臣如萬物…
  卦爻不能刑沖克害日月`（源L1079）→ 日月并列最高，**卦爻（含动爻）不得反作用于日月**；太岁不入方向（源L917）。
- **取用三级瀑布**：`飛爻變爻俱無用神者﹐始尋伏神`（源L418）→ 现 > 变 > 伏；
  用神不现则`卽以日月爲用神`（源L309）；伏神"有用"有**六条可枚举条件**（源L338）——天然是事实层形状。
- **夺取而非加权**：`貪生貪合﹐刑沖克害皆忘`（源L1000）＋三合成局`反來生火`（源L1002）
  → 合/生 成立即**抑制**克/刑，不该再按分加减；`變爻…從無幫助正卦之爻`（源L1200）给作用域。
- **抗性**：`用神旺相可以敵之`（源L1257）、`月拱日克﹐可以敵之`（源L2380）→ 旺衰压单克；月日可相抵。
- **冲突不合并**：月破段前说`日辰之生亦不能生…動不能爲害`（源L247），紧接野鶴曰`動則能傷於爻`（源L249）——
  同一段两说，本文件并列登记、留人裁，不替古人调和。

### 三、最重要的一条差（这条才是 A3 的真动机）

`step3.py:176` 写着 `base_score = god_month_score * 0.6 + god_day_score * 0.4`。
**书证只说"主宰/提纲"并列（源L915、黄金策 源L12），并支持月日可相抵（源L2380），没有一处给 6:4。**
这个权重是隐式常数，却决定了所有卦的旺衰基线——正是"分数说不清自己"的源头。
处置建议：本批只登记不改（改它会重排全部分档）；要么补书证，要么在判定表里明标"非书证·工程默认"。

### 四、逐字回验抓到自己两轮错（照录纪律的现成教材）

写完先跑 `dev_tools/check_source_readings.py --file docs/JUDGMENT-TABLE.md`，连吃两轮红：

- **第一轮：整张表的行号体系错了。** 我按 `zengshan_buyi.wikitext.txt`（繁体抄本，4475 行）记的
  `源L`，而本门 `load_corpora()` 在同名两本间**以 dz 优先**——《增刪卜易》被解析到
  `zengshan_buyi_dz.dz.txt`（3696 行）。同一句在两本里行号差 200–400 行，于是 13 条判红、
  另有多条被判"书名/行号双疑"。**病根不是抄错字，是没先问"这道门认哪本"**。
  处置：全表改指 dz，引文改抄 dz 的简体原文（异文也照录——dz 作`用爻有气`，wikitext 作`用神有气`，
  两本不同就得跟着所引的那本走）。
- **第二轮：长引文超出绑定窗。** B3（伏神六条件）单条 110 字，引文起点距行号锚 >80 字，
  门按"裸指针"判红（提示语还很客气：「底本该行有同题句可抄＝欠账」）。拆成 B3a/B3b 两条即过。
- **终验：25 条可验、25 条逐字命中、0 判红 0 NOTE。**

教训两句：**引文回验先问"门认哪本底本"**（同名两本时以 dz 优先，是既有口径不是本批新规）；
**长引文要拆**，绑定窗 80 字是硬的。

### 五、留给人的四条（文件 §五 已写明倾向，等人签）

① 月破兼动选 F1 还是 F2；② 月日 6:4 的处置；③ 用神与世谁主方向；④ 时间题与吉凶题分流
（后者与 `adjudications.liuyao.shijian_tiying_verdict_dual` 同批看）。未签之前判定表不得进代码。

### 六、读数

零引擎改动：golden 288 例指纹未触碰，tune 97.9／holdout 90.2 与 312 批同。
`check.py` 复跑 rc=0（文档门 [11] 认新文件路径可达）。

## 2026-10-29 第三百一十二批（六爻，两科联动）：**把 311 批的分层大清账做完并归位——3 条禁边还清、账台 bad 11→0、金标准零漂移；顺手修掉一处长期假阳性**

**性质**：engineering（完成未提交的重构＋补登记）。引擎判定逻辑零改动，288 例指纹逐位未动，两集读数不变。

### 一、接手时的真实状态（别人看到的是绿的，盘上不是）

311 批的「分层大清账」只做了一半就留在工作区：`narrative_utils.py` 与 `narrative_rules.py` 已删，
`util.py` / `chain_verdicts.py` / `chain_assembly.py` 已建，但 **10 个模块仍 import 已删模块**——
`dev_tools/check.py` rc=1、`readout_ledger.py --quick` **bad=11**，而 CHANGELOG 311 批写着「两科全量实跑 rc=0／rc=0」。
同时 `CONTRACT.md`、`layer_contract.json`、两个 `check_layer_contract.py` 全在**未跟踪**状态（310 批的产物没进 git）。
本批先按 §六.2 把「登记先于事实」这个洞补上：先修好，再逐条登记。

### 二、改动清单

1. **import 收敛（行为零改动）**：`classical_enhancements{,_dufa,_menlei,_shen_yao,_yimao_zhugui,_zhugui}`、`effects`、`step1`、`step2`、`timing` 共 10 处改指 `util`（机械工具）／`chain_verdicts`（断语装载）；
   `thinking_chain` 的 5 个装配函数改指 `chain_assembly`（311 批从 `narrate_core` 搬出的那一批）。
   逐字对拍依据：13 个被搬函数在旧 `narrative_utils` 与新模块中**源码逐字节相同**（本批 AST 抽取比对，13/13 相同），所以这是纯搬迁，不是改写。
2. **修一处真 bug**：`chain_verdicts.strength_reason` 引用 `FREASON` 而该别名未随搬迁带过来（旧 `narrative_rules` 里是 `STEP5_FACTOR_REASONS as FREASON`）——首跑即 `NameError`，改指 `STEP5_FACTOR_REASONS`。
3. **撤四份 `.bak-20261027`**：三份与 `git show HEAD:` 逐字节相同（可复原）、一份与现文件相同（纯副本）。已移到系统临时目录留档，不进树——版本走 git，不写进文件名（§三 A 条）。
4. **禁边还清三条**：`thinking_chain → narrate_core`、`step5 → narrate_core`、`step1..4 → narrative_utils` 均不再存在。
   `layer_contract.json` 里这三条由 `known:true` 改为 **`known:false` 零容忍**（不是删除——把已修的债转成硬规矩，回潮即红）；`chart.py → narrative_utils` 一条改指其后继 `chain_verdicts`。
   门首跑即按设计判红「欠账已还但条目还在」，逼出这次同步——**这是该门第一次以这种方式生效**。
   `CONTRACT.md` 同步：§二 叙述层定义、§三 层间图与禁边表、§六 第 3／6 条。
5. **补两条治理登记**：`check_layer_contract.py` 两科各一，310 批新增时未入 curated 表（`--strict` 会判 UNCLASSIFIED）。
   补后重生成 `GOVERNANCE-MAP.json`：六爻 57→**58**（blk 24→**25**）、八字 36→**37**（blk 25→**26**）；
   账台 `governance` 期望值同步改并注明来由（310 批新增门），不是静默刷新。
6. **修账台一处长期假阳性**：`tracked 完整性(解码0/JSON0)` 的判据是「全库可 UTF-8 解码」，把 `claude-plugin/assets/icon.png` 当破损件，
   该项自 238 批起**恒计 1**、长期挂在 × 里被当噪声——而「恒红的哨兵等于没有哨兵」。判据改为二进制按扩展名豁免，**期望值不动（仍是 0/0）**：修的是尺子，不是读数。
7. **新登记一条欠账（§六-7）**：`analyze` 实测仍吐 `reasoning_chain` 9 条成句＋`summary_text` 354 字，`[32]` 只白名单两层子键看不出来；
   `narrate_core` 还反向从 `[格局] A|B` 串里正则反解标签。这条不在本批修（动叙述结构要单独一批），按 §七.3 写明由 A3 分层批还。

### 三、读数

- `golden.py verify`：288 例｜机械 `4ceef1eed62dafe2`｜措辞 `405bc8e03a6a99e0`——**与基线逐位一致**
- `evaluate`：tune 97.9%（n=20）／holdout 90.2%（n=12），与上批同
- 质量门：`liuyao/dev_tools/check.py` **rc=0**（32 节全绿）／`bazi/dev_tools/check.py` **rc=0**（28 节）
- 账台：`readout_ledger.py --quick` **bad=0／全账 39**（接手时 11）
- 契约门：5 个夹具 × 两段键面在册；禁边 9 条规则、欠账由 5 条降为 **2 条**

### 四、未做（下一批起按 A3 → B2/B1 → C1→C2 的顺序）

本批只归位，不动判定结构。A3（判定表＋可关闭判定模块）从**古籍书证分析**起步，见下一批。

### 五、入库锚（312 批自曝一条机械口径）

- 入库提交 `969bcdc`：310／311／312 三批**合并为一条提交**。理由：三批本就摊在同一棵工作树上，
  按批拆文件归属只能靠猜，猜出来的"分批历史"是假历史，比合并提交更坏。三批各自的内容已在提交信息里分段署名。
- **本批踩到自己一道门的机械边界**：`readout_ledger` 的「登记×提交在册」用 `第([中文数字]+)批` 匹配提交信息，
  而本批标题写成范围简写「第三百一十～三百一十二批」——正则只认「第X批」连写，于是 310／311／312 **全被判孤儿**（11→14）。
  这不是"没提交"，是**匹配形态**问题（与 309 批结案的 264-268 同族：范围简写只匹配首号，本批连首号都没匹配上）。
  处置：不改门（改门＝把尺子改成迎合），补一条显式提及三个批号的提交把它登记进册，并在此留痕。
  口径教训入册：**提交信息里的批号必须写成「第X批」可匹配形，范围简写请逐条展开**。
