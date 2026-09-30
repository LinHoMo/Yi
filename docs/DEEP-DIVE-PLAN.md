# 各科深度改造方案（按"像不像老师傅"排序）

> 本文是**审计结论 + 可执行清单**，不是进度报告。所有条目都带代码位置、古籍依据与验收方式；
> 已完成项在 `docs/CHANGELOG.md`，现状读数在 `docs/HANDOFF.md`。
> 口径：全文分数均为**古籍案例对齐分**（回归审计用），不是现实命中率。

---

## 〇、怎么读这份文档

"像不像老师傅"拆成三件事，缺一件就露怯：

| 维度 | 含义 | 现状问题 |
|---|---|---|
| **环节完整** | 古法断卦/论命的每一步都有代码，不靠 LLM 临场联想 | 六爻缺三会局、独发独静、卦级反吟伏吟等；八字缺调候/通关/病药、格局成败救应 |
| **判据可检** | 每个环节的结论都由规则表算出，且**有评测覆盖** | 六爻的旺衰定性、六神临用、卦身、墓库开合、独发独静**零评测覆盖**——做错了没人知道 |
| **出处可追** | 每条判据能指到具体古籍通则，不是"感觉" | 部分环节只有 `references/*.md` 有文、代码里没有（文码不一致） |

> 底线（`AGENTS.md` §四.3）：修某类错误只能改**通用规则**并写明古籍出处；
> 禁止为让某个案例过关而写私有别名或 case-specific 分支。

---

## 一、六爻（`disciplines/liuyao`）——最成熟，差距在"边角与可检性"

### 1.1 环节覆盖现状

| 环节 | 态 | 代码位置 | 备注 |
|---|---|---|---|
| 装卦/纳甲/世应/六亲/六神/旬空 | 有 | `engine_chart.py`、`chart_tables.py` | 表全在内核 `symbols.py` |
| 用神多现取舍 | 有 | `liuyao_step2.py::_use_god_priority` | 9 级优先序 |
| 原神/忌神/仇神链条 | 有 | `liuyao_step2.py` | 含伏藏兜底 |
| 伏神飞神 | 有 | `liuyao_step2.py::_check_fu_cang`、`liuyao_step5.py` | 飞空得出 / 飞来生伏 / 飞克伏 / 伏泄气 |
| 进神退神 | 有 | `liuyao_step4.py` | `ADVANCE_PAIRS` / `RETREAT_PAIRS` |
| 反吟伏吟 | **半有** | `classical_enhancements.py` | 只有爻级打分；**无卦级**"内外卦全冲/全同"检测 |
| 六冲六合（含变卦对比） | **半有** | `effects.py`、`liuyao_step5.py` | 只给 ±0.5 加减；无"本卦定始、变卦定终"双卦对比 |
| 三合局/破局/静爻待用 | 有 | `classical_enhancements.py` | 含"合局待用需日月引动" |
| **三会局** | **无** | 全仓无 `三会` | 只有 `SAN_HE_GROUPS`（三合） |
| **独发独静** | **无** | 仅 `references/classical_synthesis.md` 有文 | 文码不一致 |
| 月建日辰权力 | 有 | `liuyao_step3.py` | 月 0.6 / 日 0.4 + 日辰 ±1 |
| 旬空假空 | **半有** | `liuyao_step3.py::compute_empty_modifier` | 有旺衰权重；**未产"真空/假空"标签** |
| 墓库开合 | **半有** | `liuyao_step4.py`（化墓）、`liuyao_step5.py` | 无"冲开墓库" |
| 应期细则 | 有 | `liuyao_timing.py::predict_timing_core` | 出空/填实/逢值/逢冲/待旺/暗动/伏神 7 类 |
| 六亲持世 | 有 | `liuyao_step5.py`、`liuyao_narrate.py` | 7 条情境 |
| 卦身 / 游魂归魂 | 有 | `classical_enhancements.py` | |
| **三传克制**（太岁+月建+日辰俱克） | **无** | 无太岁参与判据 | 文码不一致 |

### 1.2 评测覆盖的盲区（比缺环节更严重）

| 集合 | n | strict 对齐分 | 应期 top-1 |
|---|---|---|---|
| tune | 20 | 86.2 | 58.8% |
| holdout | 12 | 81.0 | 50.0% |
| wikisource_holdout | 35 | 54.9 | 20.0% |
| huozhulin_holdout | 2 | 34.8 | 0.0% |

case 的 `expected` 字段实际填充率：`detail` 117、`verdict` 96、`yingqi` 81、
`key_points` 42、**`use_god` 仅 48、`use_god_branch` 34、`use_god_position` 仅 3**。

**完全无评测覆盖**（做错无人知）：旺衰定性本身（`score_case` 无 streak 项）；
反吟/伏吟/进退神/入墓/暗动/月破/游魂归魂被降级为**格局词子串匹配**而非结构比对；
应期法则的"依据"不校验；六神临用、卦身、三合、墓库开合、独发独静、三传克制零覆盖；
`dims.use_god_position` 在 tune/holdout **全为 N/A**。

### 1.3 改进清单（按投入产出比）

| # | 改哪里 | 古籍依据 | 怎么验收 |
|---|---|---|---|
| 1 | `liuyao_step3.py::compute_empty_modifier` 增 `is_true_void` / `is_false_void` | 《增删卜易》"旺空待出，真空难起"——旺相+月日动爻生=假空待出；休囚+日克+无生=真空 | `pattern_reference.md` 已列词，先补进 `evaluate.PATTERNS`；跑 wikisource_holdout(35) 看格局命中率与 strict 均分 |
| 2 | `liuyao_step2.py::_use_god_priority` + `_find_use_god_positions` | 《增删卜易》"用神两现，舍闲取动，舍缓取急，舍静取世" | 加 3 例 `use_god_position` 基准；strict 报 `use_god_position.hit/na`，**NA 必须下降** |
| 3 | `liuyao_step4.py::_detect_hexagram_harmony_clash_pattern` 增双卦对比 | 《黄金策》"合处逢冲事已散，冲中逢合事迟成" | `变卦六合/变卦六冲` 词已在 `evaluate.py` 但无人产出；补后 tune 均分不得跌破 86.2 |
| 4 | `liuyao_step5.py::compute_advanced_adjustments` 增三传 | 《增删卜易》"三传俱克，虽旺亦危" | 无含太岁的基准例，属**未验证**；须先自建 3 例标注才可计分 |
| 5 | `classical_enhancements.py` + `effects.py` 增卦级内外卦检测 | 《卜筮正宗》"内卦反吟内不安，外卦反吟外不宁" | 造全冲/全同双卦单元测试；格局维度覆盖 `反吟/伏吟` |
| 6 | `core/yishu_core/symbols.py` 增 `SAN_HUI_GROUPS`，`liuyao_step4.py::_detect_special_pattern` 优先三会 | 《三命通会》寅卯辰/巳午未/申酉戌/亥子丑三会方局，力大于三合 | 单元：三会须优先，且不得被误判"三合破局" |
| 7 | `liuyao_step2.py` 增女命占婚双官鬼标记 | 《卜筮正宗·用神论》 | **只给象不给吉凶断言**，避免过度判 |

**纪律提醒**：第 1–3 项会动推演逻辑，必须按 `AGENTS.md` §四 跑 tune/holdout 分列，
并跑 `dev_tools/golden.py verify`（指纹 `abc7884de0653ee5`）确认漂移是**有意**的。

---

## 二、命科八字（`disciplines/ming`）——差距最大，且**完全没有案例评测**

### 2.1 已覆盖 / 缺失

**已覆盖**：四柱（年界立春、月界节气）｜藏干三元权重 1.0/0.5/0.25｜十神｜
强弱（生扶−克泄耗 + 得令 ±1.2，阈值 ±1.5）｜正格 12 名｜扶抑喜用（只到"类"不到干支）｜
大运 8 步 + 顺逆 + 三日一年｜流年 12 年 + 运年交互（六合/六冲/三合/相刑/比和）｜
空亡｜从格 4 类（tentative）｜命宫身宫｜神煞 9 种。

**缺失**（逐条落实）：调候用神｜通关、病药用神｜**格局成败救应**（现为"月令本气一名定局"，
无成败/破格/救应）｜三会局（三合有）｜四柱之间独立的刑冲合害检测（现仅运-年两支比对，
无合化/争合妒合/冲开墓库）｜胎元｜小运｜流月｜岁运并临、天克地冲｜
十神组合（伤官见官/枭神夺食/食神制杀/财滋弱杀）｜女命夫子星｜童子关煞。

出处纪律：`ming_tables.py`、`shensha.py` 自认"无法逐字核对原文 → `verified=false`"，
新增项必须沿用这个标记，**不得把流俗起例写成古法**。

### 2.2 评测缺口（最要紧的一条）

`disciplines/ming` 下**没有 `evaluate*.py`**；`data/cases/ming_cases.json` 的
`tune: []`、`holdout: []`，只有 5 条机械回归，`expect` 仅含四柱/强弱/格局/空亡/大运方向。
结论：**排盘、十神、神煞、命宫、大运流年、narrate 全部零对齐评测。**

### 2.3 案例集与诚实打分方案

| 书 | 可用形态 | 能支撑的维度 |
|---|---|---|
| 《穷通宝鉴》（栏江网） | 月令×日主→调候用神**表** | **最适合逐条对照**（答案是表不是文） |
| 《子平真诠》 | 格局成败救应判词 | 格局成败 |
| 《滴天髓》任铁樵注 | 旺衰/病药/取用注例 | 强弱定性、病药、通关 |
| 《渊海子平》 | 命例 + 女命论 | 十神取格、女命夫子星 |
| 《三命通会》 | 神煞起例、童子关煞 | 神煞安法校验 |

方案骨架：

1. 新文件 `disciplines/ming/data/cases/ming_classical_cases.json`，case 字段
   `{id, source, book, location, pillars{y,m,d,h}, gender, expected{use_god_stem,
   useful_gods, pattern, pattern_cheng_bai, tiaohou, shensha[], strength, dayun_dir},
   confidence, notes}`。
2. **`expected` 只记书上明写的量**；未记一律 `null` → 走 `yishu_core.eval` 的 strict
   **N/A 剔除**，禁止 legacy 满分化。
3. **可评**：调候用神（表对表）、四柱/藏干/十神、大运顺逆、神煞、从格结构。
4. **不可评**：富贵层次、寿夭、六亲克应、吉凶年份——没有客观标的，
   任何"命中率"都是编的。古籍"果于某年"只作定性注记，**不计分**。
5. 指标口径：每维度报 `hit/applicable/na` 三列；n 极小（首版 20 例）时**只报命中数与
   候选集大小**，不报百分比；防骑墙须同时报随机期望基线。tune 10 / holdout 10 分列。

### 2.4 改进清单（按投入产出比）

| # | 改哪里 | 古籍依据 | 怎么验收 |
|---|---|---|---|
| 1 | `core/yishu_core/ming_tables.py` 新增 `TIAO_HOU` 表；`pattern.py::strength_and_pattern` 输出 `tiaohou_god` | 《穷通宝鉴》按月令×日主定调候（如"正月甲木，丙癸并用"） | 20 例表对表断言；holdout 10 例报命中数（非百分比） |
| 2 | `pattern.py` 增格局成败救应层级 | 《子平真诠》"有用神必有相神，相神破则格败" | 自建 ≥15 例（成/破/救应各 5），strict 报 `pattern_cheng_bai` 命中/na |
| 2a | **（已落地 2026-09-30t+30u）**：PATTERN_CB_RULES 十格三分类 + 书源身强条件（财格身弱透官破、偏官格食制需身强）+ 伤官带煞佩印特例；30u 再增强：财格官/煞细分（成=正官/食伤透；败=七杀透/比劫透/身弱透官；救=食伤制煞/合煞存财）、印格合财存印、建禄去伤存官、煞刃格（偏官+阳刃在支+印透=破）；天干五合表入 core；chart_from_pillars 四柱直填起盘；evaluate 双通道；36 例书源命例（27 成/5 破/4 救，全 holdout；30u 新增 ZP031 回归+ZP033-036）→ holdout pattern 36/36 | 同 #2 | **缺口（待补）**：救应 4/5——书源"败中有成全凭救应"命例主干可判面已用尽（谭延闿/张载阳/毛状元/王总兵），剩余判词依赖地支会合/藏干/化气微观（褚辅成"癸水破印生官"、陈陶遗"壬化煞生身"），待位置/合化规则深度化；破格 5 已达标（胡汉民/伍朝枢/杨杏佛/煞刃张季直类/陈陶遗） |
| 3 | `pattern.py` 从格条件收敛 | 《滴天髓·从化论/从象/假从》"从得真者只论从，从中有神论不从"；任注"从旺者四柱皆比劫、从强者印绶重重比劫叠叠、从气者气势在木火/金水、从势者日主无根财官食伤并旺" | **（已落地 2026-09-30w）**：`_from_judge` v4 可判级（真/假从、从旺/从强/从气/从势）+ 地支互动（三合化气/异类冲破根破印破令，同类库冲不破）；15 例 ZC 书源标注集（滴天髓阐微·下篇从象/假从，全 holdout）；evaluate.cong_ge 布尔2+种类1+真/假1；ZC 布尔 15/15、真/假 13/15、种类 12/15；tune 100%、holdout 93.8%（pattern 28/36 因 8 例子平/滴天口径分歧，判据按滴天髓从格论——登记 CHANGELOG 30w）；**残余缺口**：灰区 3 例（ZC012/014/015 书假从判真从）、kind 2 例（ZC011/014 财生杀书从杀判从势）、救应 4/5 可复用本批冲合工具回填 |
| 4 | `analyze.py` 新增小运、流月 | 《三命通会》小运起法；流月自节气起 | 小运与大运起运相接、流月单调；12 步单元测试 |
| 5 | `pattern.py` 运年交互增"岁运并临/天克地冲" | 《渊海子平》"岁运并临，灾殃立至" | 断言某例检出；**只标记不批吉凶**（**已落地 2026-09-30u**：运=年干支相同 → `kind=sui_yun_bing_lin` 标记，narrate 大运×流年对照呈现，pytest 断言无吉凶字段；天克地冲留待后续） |
| 6 | `shensha.py::shensha_of_chart` 补飞刃/金舆/将星/天医/亡神/劫煞/孤辰寡宿/阴差阳错 | 《三命通会·神煞》起例；无逐字出处者一律 `verified=false` | 断言新神煞落地支正确；narrate 禁止吉凶断言（**已落地 2026-09-30u**：8 项全部接入 + `tests/test_shensha.py` 8 断言 + narrate 神煞机械呈现段） |

**报告层同步**：以上每项落地后，`disciplines/ming/scripts/narrate.py` 与
`render.py` 要按同一口径呈现（如调候用神单列一节），否则"算出来了但用户看不到"。

---

## 三、梅花 / 小六壬 / 择吉——三科**评测不可信**，先修尺子

现状（2026-09-30 逐例审计**已完成**，全文见各科 `docs/EVAL-AUDIT.md`，一键复核
`python tools/eval_audit_recheck.py`）：三科 tune/holdout 的 100% 是**规则自洽回归数**，
不是古籍案例对齐分——expected 与引擎同源（梅花自洽项 70/100 权重、holdout 5 例按本仓
规则表构造；小六壬四维 100/100 权重全查同一张表；择吉 16/16 与 `analyze()` 逐字段全等，
古籍日例应验 0 例）。梅花 MH014–MH018 为硬泄漏：expected 出自 `verdicts.json#multi_move_rules`，
与案例同一提交 `010bcee` 引入。

**优先级高于任何推演增强**：

1. ~~独立审计~~ ✅ 已完成（2026-09-30）：结论落三科 `docs/EVAL-AUDIT.md`，逐例
   `provenance` 入 cases，复核工具 `tools/eval_audit_recheck.py`。
2. ~~分数呈现口径~~ ✅ 已落地：三科 `evaluate.py` 报分自动打印 `[口径披露]`
   （集合名 / n / 是否调参 / 自洽项 / 泄漏警告）；**n<20 不发百分比**，改打逐维度命中数。
3. **唯一剩余有效动作：扩外部独立案例**（古书原文、非本项目构造；范式照六爻
   `case_runner` 合并 `*_cases.json` + `case_splits.json`「永不调参」split）。
   **扩判据、调权重都不解决**——外部集落地前，三科任何"提分"都是自洽环内打转。

---

## 四、新门类（见 `docs/NEW-DISCIPLINES.md`）

- 推荐落地顺序：**大六壬 → 奇门遁甲（时家转盘）→ 七政四余**；备选灵棋经、大衍筮法。
- 判据：古书出处可编程取用 / 判据树清晰 / 内核复用度高 / 可建评测集 / 可合参。
- 相科（面相、手相、堪舆）按 `AGENTS.md` **明确不做**。
- 落地任一新科时的验收线：各科 `dev_tools/check.py` 全绿 + 仓库根 `tools/check.py --full` 全绿
  + `tools/report.py` 六科之外新增一科可端到端出报告（含 `web/manifest` 与同源验收）。

---

## 五、执行纪律（改引擎前先读）

1. **分列出分**：tune 与 holdout 分别报，禁止混合冒充提升（`AGENTS.md` §四.1）。
2. **指纹验收**：六爻跑 `cd disciplines/liuyao && python dev_tools/golden.py verify`；
   有意漂移必须 `capture "理由"`，理由写清"改的是哪条通则"。
3. **通用规则 + 出处**：禁止 case-specific 分支（§四.3）。
4. **口径变更登记**：计分方式/词典/缺失字段处理一变就写 `docs/CHANGELOG.md`（§四.4）。
5. **端到端不回归**：改完跑 `python tools/check.py --full`（含站点构建/自检与
   网页↔本机同源验收）。
6. **报告层同步**：引擎多算出什么，`narrate`/`render` 就要按同一口径呈现出来。
