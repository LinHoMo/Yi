# 易（Yi）· 四段契约（CONTRACT）

> **本文件是什么**：`chart → analyze → narrate → render` 四段分工与层间调用的**唯一判据**。
> 重建于第三百一十批（2026-10-27）：此前这条判据被 5 个模块的 docstring 引用为
> 「CONTRACT §一」，而文件本身已随仓库扁平化消失，只剩引用没有本体（详见本批 CHANGELOG）。
>
> **三件套分工**：
> - 本文件解释「**为什么**要这样切」；
> - `<科>/data/rules/layer_contract.json` 声明「**是什么**」（机器可读的键白名单与禁边表）；
> - `dev_tools/check_layer_contract.py` 守「**守不守得住**」（实跑 + AST + 负例自证）。
>
> **效力**：与 `AGENTS.md` 冲突时以 `AGENTS.md` 为准（AGENTS.md §二 明文）；与任何单个学科
> 的 `SKILL.md` 冲突时以本文件为准。改本文件必须同批改 JSON 与门，三者不同步即视为缺陷
> （AGENTS.md §六.3）。

---

## §一 四段职责

| 段 | 入口 | 输入 | 输出 | 必须做 | 禁止做 |
|---|---|---|---|---|---|
| **chart** | `scripts/chart.py` | 起卦参数（方式/问题/时刻/种子） | 盘面 JSON | 起卦、装卦、定宫、纳甲、世应、六亲、六神、旬空、月破| 吉凶判语、成句评价、用神选取建议 |
| **analyze** | `scripts/analyze.py` | chart JSON | 结构推演 + 定性结论 JSON | 五步推演、结构标签、分数、判词、结论级短建议 | 成段正文、叙述铺陈、重复叙述层措辞 |
| **narrate** | `scripts/narrate.py` | analyze JSON | 成段正文（唯一出口） | 把已产出的结构事实翻成人话、装配交付对象 | 新增任何象数判断（只能读，不能算） |
| **render** | `scripts/render.py` | analyze JSON | Markdown / 单文件 HTML | 排版、图形（卦盘）、章节编排 | 产新事实、新结论、新措辞来源 |

**四条不许越的界**

1. **chart 不许下判断**。盘面可以带"素材"（卦辞爻辞、八卦类象），但不能带"结论"
   （吉凶、宜忌、成败）。判据不看用词看形状：**成句评价即越界**，哪怕不含「吉/凶」二字。
2. **analyze 不许写文章**。允许定性词（大吉/偏凶）与一句结论级建议，不允许段落铺陈；
   成段文字只有一个出口，就是 narrate。
3. **narrate 不许重算**。正文里的每个象数事实都必须能在 analyze JSON 里指回原键；
   指不回去的即"叙述层自造事实"，按铁律一处理。
4. **render 不许当第二个 narrate**。排版层出现断语字面量，等于绕过外置册直接写文案。

## §二 四段职责的通用边界

四段分工是两科**共同判据**，不因推演链形状不同而改变：chart 只产盘面，analyze 只产
结构标签与定性结论，narrate 是成段正文的唯一出口，render 只排版。某一科把推演实现
拆成几步、模块叫什么名字，都是**段内实现**，不构成第二条交付管道。

共同遵守的边界（机器判据见各科 `layer_contract.json` 的 `edges.forbidden`）：

- `core/**` 不得 import `scripts/**`（AGENTS.md §二 单向依赖）；
- `chart` 不得 import `analyze` / `narrate`（起盘段不依赖推演/正文）；
- `analyze` 不得 import `render`（推演段不依赖呈现段）；
- 叙述层不得 import 推演实现内部模块（要数据请走 analyze JSON）。

### §二-bis 各科剖面

| 科 | analyze 段的内部实现 | 对外键 | 说明 |
|---|---|---|---|
| 六爻 | `step1.py`–`step5.py` 五步链（现状 → 取用神 → 旺衰 → 动变 → 综合），装配在 `chain_assembly` | `thinking_chain` | `step*` 可互相 import（现状 `step3 → step2`、`step4 → step2`、`step5 → step3/step4`）；`step*` 不得 import 叙述层（`narrate_core` / `narrate` / `advice_framework`）；`chain_verdicts` 是数据装载面（断语表），推演段取断语走它不算越界 |
| 八字 | 单体 `analyze.py`：`bazi_factors.strength_and_pattern` → `dayun_table` / `liunian_table` → `conclusion`（`scripts/pattern.py` 提供格局判定，属同一 analyze 段） | `conclusion` 等 26 键 | 八字**无** `step1`–`step5` 的对应物；不存在可照搬的推演链，也不为对称而克隆（ARCHITECTURE-PLAN.md §六.3） |

## §三 层间调用矩阵

```
core/yishu_core   ←（唯一允许方向）—  scripts/*
                                        ├─ engine_* / chart      机械
                                        ├─ step* / classical_*   推演（chain_assembly 属此段）
                                        ├─ chain_verdicts        数据装载（断语表，非叙述）
                                        ├─ narrate*              叙述
                                        └─ render / visualization 呈现
```

| 允许 | 说明 |
|---|---|
| `scripts → core` | AGENTS.md §二 的唯一依赖方向 |
| `analyze → step* / 规则层` | 推演段内部装配 |
| `analyze → narrate?` **否** | 推演段不得为了取文案去 import 叙述层 |
| `narrate → analyze 输出` | 只能读 JSON，不 import analyze 模块 |
| `render → narrate` | 呈现层可以调用正文生成（现状如此） |
| `narrate → narrative_assembly` | 355 批：叙述重建（`reasoning_chain`/`summary_text`）；只消费 analyze JSON 的 step facts，**不 import analyze.py**；`narrative_assembly` 可复用 `chain_assembly` 的事实装配器 |
| `engine.py → output.py` | CLI 输出装配（349 批）；`output.py` 才触 `render`/`engine_format`，`engine.py` 不再直连呈现层 |

**禁边表**（机器判据见 JSON `edges.forbidden`，只准减不准增）：

| 起点 | 终点 | 现状 | 判定 |
|---|---|---|---|
| `thinking_chain.py` / `step5.py` / `step1..4` | `narrate_core` | 不存在（312 批已还） | **零容忍**：装配函数已搬回 `chain_assembly`，回潮即红 |
| `core/**` | `scripts/**` | 不存在 | 零容忍，任何新增即红 |
| `chart.py` | `narrate*` / `chain_verdicts` / `advice_framework` | 不存在 | 零容忍（`chain_verdicts` 承接原 `narrative_utils` 的断语面） |

> **349/350 批已还**：原 `engine.py → render` 由 `output.py` 承接；原
> `engine_chart → trigram_symbolism` 由 analyze 段产卜象解读、CLI 输出层补键。
> `edges.forbidden` 的 `known` 欠账已归零，余下全是零容忍条目。
> （349 批注释：CLI 三路输出搬到 `scripts/output.py`，`engine.py` 只调 `output_result`。）

## §四 输出键白名单

真值源是 `<科>/data/rules/layer_contract.json`（两科各一份，**根目录没有**此文件），本表只是摘要（键数随批更新，**以 JSON 为准**）：

| 科 | chart 顶层键 | analyze 顶层键 | 嵌套白名单 |
|---|---|---|---|
| 六爻 | 7 | 14 | `trigram_interpretation` 22 键（analyze 段，350 批迁入）／`conclusion` 12 键 |
| 八字 | 9 | 28 | `conclusion` 27 键（另有 `dayun_cheng_bai` 分列读数层，不计入评判键） |

**信封 schema（353 批）**：跨科共用的顶级结构由 `devkit/layer_contract.schema.json`
（JSON Schema 2020-12）约束；`check_layer_contract.py` 的
`validate_contract_envelope()` 零依赖校验 required/type/fixtures/stages/edges/
forbidden 条目字段。**各科 stage 键名仍以各自 JSON 的 `allowed`/`required` 为准**，
信封 schema 只管“契约文件本身是不是一份契约”。

**`conclusion.judgment`（第三百二十批新增，optional）**：九格判定的结构化产出
（`direction` 成/滞/不成 × `confidence` 高/中/低，附 `why`／`cites`／`support`／`dissent`／`base_cell`／`overlay`）。
**为什么属于这一段**：它由推演事实（用神旺衰、动变净效、空破、原神忌神、题类）判定，不是文案；
`verdict` 仍是现行引擎的档位，**两者并列对照**——接线期判定器尚未取代判词
（`liuyao/data/rules/judgment_table.json` 的 `implementation.verdict` 在册；八字侧无判定表）。
`judgment_enabled=False`（CLI `--no-judgment`）时**该键整个不出现**，故它不在 `required` 里。

**新增一个键 = 改契约**。同批必须做三件事：改 JSON、改本表、在 `<科>/docs/CHANGELOG.md` 写一句
"为什么这个键属于这一段"。只改代码不改契约，新键会在下一轮被门拦下——这是刻意的：
过去 `analysis_hints` 与 `trigram_interpretation` 就是这样凭空长在 chart 段里的。

## §五 结构层与断语的分界

沿用 AGENTS.md §一.1：结构层只出**标签与数值**；判语字面量进 `<科>/data/rules/*.json`
（现状：`verdict_texts.json` 92K、`scripts_labels.json`）。机械门 `[30]`
（`check_verdict_external.py`），LOCK=0。

本契约不重述该条，只补充一条**归属规则**：一段文字若同时含"事实"与"评价"，
事实归 analyze，评价归 narrate；不要在两段各写半句。

## §五-bis 象层：象与断的分界（第三百六十二批）

**背景**：六爻与八字两科的「象分析」（类象／宫位／六亲／卦爻辞／互体／六神象义／
方位／脏腑）此前**素材在、能力不在**——八卦类象表、卦辞爻辞、六神属性、四柱十神
都在盘面里，正文实测命中数为 0（六爻 1087 字正文里 类象/方位/爻辞/互/六亲 全为 0；
八字 4303 字正文里 宫位/六亲/身体 全为 0）。原因不是缺素材，是缺**装配与出口**：
`analyze.py` 里一行 `category="general"` 让类象永远只出通用档，且象从不进交付面。

四条规定：

1. **象层位置**：象在 analyze 段产出（`xiang` 键，optional——素材不齐或装配失败时
   整块不产，不塞空壳），经 narrate/呈现层进正文与插件结构化输出。
2. **象不进断**：`xiang` 不进 `WEIGHTS`、不进 `verdict`、不改 `conclusion`。
   评分侧模块（六爻 step1–5／timing／judge／classical_*，八字 pattern.py／
   bazi_factors/*）**不得读** `xiang`——象可以进眼睛，不可以进分数。
   两科 `[39] 象层门` 守这一条，负例自证：评分侧偷读即红。
3. **象目带出处**：每个象目必须带非空 `basis`（数据文件名／内核表／算法说明）。
   无出处的象目不得产出。文案进 `data/*.json`（AGENTS §三），代码只留算法。
4. **象不冒充成绩**：象的覆盖度由 `dev_tools/xiang_coverage.py` 读数
   （字段非空率、题类分布），**只报「有没有出」，不报「准不准」**；
   象不进评测维度，因此在八字侧 `check_dim_surface.NON_SCORED_SECTIONS`
   登记「象上看」小节的不评分理由（§六 要求「看到的没在评」必须说明）。

两科象层的范围（逐科登记，不互相套用）：
- 六爻：`category`（题类→象类别，映射表 `data/rules/xiang_layer.json`）／
  `trigram`／`ti_yong`（体用）／`guaci`（卦辞）／`yaoci`（爻辞）／`hu_gua`（互体，
  京房二三四为下互、三四五为上互）／`spirit`（六神象义）／`fangwei`（方位）／`class_image`。
- 八字：`gongwei`（宫位，年为根／月为苗／日为花／时为果）／`liugin`（六亲，
  五类反查内核 `LIUQIN_TO_SHISHEN`，子平分野按性别：男命正财为妻、女命正官为夫）／
  `zangfu`（五行脏腑，**象意提示，非医学诊断**）。

- 八字另设 `dayun_cheng_bai`（**行运成格变格裁决层**，363 批；关闭第九十三批起登记的
  「行运成格变格」欠账）。它把 `dayun_ming_yindong` 已逐字回验的结构引动标签命名为
  `成格引动`／`变格引动`／`填实引动`／`守局` 四类，**纯分列读数**：不赋吉凶分、不覆写
  本命格局成败结论、不进 `WEIGHTS`／`verdict`／`conclusion`。书《子平真诠评注》源L325
  「配之以运，亦有成格变格之要权」只给方向不给量级与优先序，故本层只做结构命名，
  不强行压成单一胜者（多机制可并存多类别）。`check_dim_surface.NON_SCORED_SECTIONS`
  已登记「行运成格变格」小节的不评分理由（§六）。

## §六 已知欠账（本契约尚未满足的条款）

> 355 批起本表为空（0 条）。原 7（`analyze` 吐 `reasoning_chain` 9 条＋`summary_text`
> 354 字）于 355 批关闭：叙述改由 `narrative_assembly` 在 narrate/呈现层从 step facts
> 重建；analyze 只留 `pattern_tags`/`pattern_lines` 与 step1–5 的一句事实摘要。
> `[32]` 的 `thinking_chain` 嵌套白名单同步为 7 键（step1–5／pattern_tags／pattern_lines）。
> 原 1/2/3/4/5/6 关闭记录见下方已关闭项注记。

> **已关闭项**：原 1（chart 段卜象解读迁 analyze）于 350 批关闭——`trigram_interpretation`
> 由 analyze 段产出、CLI 输出层补键，golden 6f70/405b 零漂移；原 2（`analyze` docstring）
> 于 310/346 关闭；原 3（禁边表）于 349/350 关闭——`known` 欠账归零，只剩零容忍条目；
> 原 4＝八字侧键白名单（310 批建成）、原 5＝render 不当第二个 narrate（311 批裁定维持）、
> 原 6＝`narrative_utils` 混装（312 批拆模块）。本表只列**尚未满足**的条款；
> 编号保留原号，避免外部引用失指。

**八字侧契约欠账审计（第三百三十六批 A2-B，逐条问过）**

结论：**八字侧新增欠账 0 条**——这不是"八字干净"的奖状，而是已按同一套判据问过的读数。
336 批时开放项 1／2／3／7 在八字侧实测均 0 条；其中 1／2／3 已于 346/349/350 关闭，
**7 于 355 关闭**；无对应物的 1（`trigram_interpretation`）与 7（`reasoning_chain`）
在八字侧如实标 N/A，不冒充"通过"；已关闭的原 4/5/6 不再重列。
逐条实测与三件套登记见 336 批 `liuyao/docs/CHANGELOG.md` 与 `bazi/docs/CHANGELOG.md`。

**行运成格变格裁决层（第三百六十三批关闭，原第九十三批登记为「可验收欠账」）**：
`evaluate.py` 与 `EVAL-PLAN.md` 长期登记的「运层成格变格裁决层缺失」欠账，于 363 批以
`dayun_cheng_bai` 分列读数层关闭——把 `dayun_ming_yindong` 已回验结构标签命名为
`成格引动`／`变格引动`／`填实引动`／`守局`。
性质：书《子平真诠评注》源L325「配之以运，亦有成格变格之要权」只给方向不给量级与优先序，
故本层**只做结构命名、不赋吉凶分、不覆写本命格局成败结论、不进评分**；主评分语料
`expected` 仍带行运字段 0 例，裁决层不参与对齐分（与 `bazi_dayun_cases.json` 同型，仅作见证与回验）。
门禁：既有的 `[18]` 行运见证集回验器已扩展，新增「引擎 judge_dayun_cheng_bai 裁决类别 == 见证集登记类别」校验，
负例自证（塞一条不符期望必被抓）。不另立 [40]，避免与 [18] 重复守同一批见证集。

**行运键回填（第三百六十五批结项：判定「不可回填」，不是「尚未做」）**：
363 批遗留的尾巴——「运层进评分的前置是回填主评分语料行运键（0/338）」——365 批结项为不可行。
三条证据由 `[18]`⑥ `corpus_gap_check` 现场重跑：① 决定性语汇（顺逆/起运/「N 岁…行运」）
扫 338 例全文 **0 命中** ⇒ 书文侧无书证（广义「运」字仅 9 例，均无干支无岁数）；
② 52 例四柱-only 案例的引擎 `start_age` 全等于同一占位常数 ⇒ 起运对该类本就不可评；
③ 顺逆是定义式，回填即自证——实测填 52 例后该维 51/51（100%）而均分 99.5／100.0 一位未动。
⇒ `dayun` 的 N/A 是**真实读数**，不进加权分；运层机械验证由 `[18]` 本体承担（12/12 排运逐字一致）。
`[18]`⑥ 兼作前瞻边界：新收案例若书文真写顺逆/起运，当场判红并要求按书证回填。
证据细节与量级见 `bazi/docs/EVAL-PLAN.md` §五 末注（本文件不重复读数）。

## §七 变更规程

1. 改段界 / 改键面 → 同一批改 **JSON + 本文件 + CHANGELOG**，跑
   `python dev_tools/check_layer_contract.py --selftest`；若动**顶级信封结构**
   （`schema`/`contract`/`batch`/`fixtures`/`stages`/`edges`），同批改
   `devkit/layer_contract.schema.json`，并跑 `devkit/sync_devkit.py --check`；
2. 禁边表条目只准减不准增；新增一条须在本文件 §三 写明"为什么暂时必须"；
3. 欠账条目只准减不准增；新增欠账须写明"哪一批还"；
4. 本文件不写读数、不写分数、不写"准确率"——口径见 AGENTS.md §一.3。
