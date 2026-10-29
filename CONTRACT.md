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
| 八字 | 单体 `analyze.py`：`bazi_factors.strength_and_pattern` → `dayun_table` / `liunian_table` → `conclusion`（`scripts/pattern.py` 提供格局判定，属同一 analyze 段） | `conclusion` 等 26 键 | 八字**无** `step1`–`step5` 的对应物；不存在可照搬的推演链，也不为对称而克隆（ARCHITECTURE-PLAN.md §八.3） |

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

**禁边表**（机器判据见 JSON `edges.forbidden`，只准减不准增）：

| 起点 | 终点 | 现状 | 判定 |
|---|---|---|---|
| `engine_chart.py` | `trigram_symbolism` | 存在 | 欠账：排盘直连类象解读（§一 第 1 条） |
| `engine.py` | `render` | 存在 | 欠账：引擎门面在 CLI 分支里调呈现层 |
| `thinking_chain.py` / `step5.py` / `step1..4` | `narrate_core` | 不存在（312 批已还） | **零容忍**：装配函数已搬回 `chain_assembly`，回潮即红 |
| `core/**` | `scripts/**` | 不存在 | 零容忍，任何新增即红 |
| `chart.py` | `narrate*` / `chain_verdicts` / `advice_framework` | 不存在 | 零容忍（`chain_verdicts` 承接原 `narrative_utils` 的断语面） |

## §四 输出键白名单

真值源是 `<科>/data/rules/layer_contract.json`（两科各一份，**根目录没有**此文件），本表只是摘要（键数随批更新，**以 JSON 为准**）：

| 科 | chart 顶层键 | analyze 顶层键 | 嵌套白名单 |
|---|---|---|---|
| 六爻 | 8 | 15 | `trigram_interpretation` 22 键（含 4 个欠账字段，见 §六-1）／`conclusion` 12 键 |
| 八字 | 9 | 26 | `conclusion` 27 键 |

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

## §六 已知欠账（本契约尚未满足的条款）

| # | 条款 | 现状 | 计划 |
|---|---|---|---|
| 1 | §一 chart 不许下判断 | `trigram_interpretation` 里 `overview` / `body_use` / `outer_personality` / `inner_personality` / `element_relation` 是成句评价（如「体生用有所付出，待时收功」） | 迁到 analyze 段产出；会动 golden 双指纹，单独一批做，不在 310 批夹带 |
| 2 | §一 analyze 不许写文章 | `analyze.py` docstring 自称「纯机械断卦，无解读成分」，与实测 `verdict="大吉"` + 4 条建议不符 | 310 批改文档（不改行为）：改为「结构推演 + 定性结论」 |
| 3 | §三 禁边表 | **2 条现存禁边**（`engine_chart→trigram_symbolism`、`engine.py→render`）；312 批还清 3 条（`thinking_chain`/`step5`/`step1..4 → narrate_core`），条目由 `known:true` 转为 `known:false` 零容忍 | 剩余 2 条按 §四 单批还；禁边只准减 |
| 4 | §四 白名单 | ~~八字侧 JSON 未建~~ **第三百一十批同批建成**（chart 9／analyze 26／conclusion 27），门 `[28]` 已挂进八字 `check.py` | 已关闭 |
| 5 | §一 render 不许当第二个 narrate | `engine_format.py` 仍有一套 `format_reading_output` 字段报表（narrate 注释称"已弃用"，但 `engine.py --text` 仍挂） | 已关闭（第三百一十一批审计：消费者在册 4 处——`engine.py --text`、`dev_tools/refactor_guard.py` 对拍基准、`narrate.py` 防御层、`SKILL.md` 合同文本——下线条件不成立，裁定维持，非下线） |
| 6 | §三 `narrative_utils` 混装 | **312 批已关闭**：拆成 `scripts/util.py`（纯工具）／`scripts/chain_verdicts.py`（断语装载）／`scripts/chain_assembly.py`（装配，属 analyze 段），`narrative_utils` 与 `narrative_rules` 两模块撤编；禁边表对应条目随之转零容忍 | 已关闭 |
| 7 | §一.2 analyze 不许写文章 | **312 批体检新登记**：`analyze` 实测输出 `thinking_chain.reasoning_chain` 9 条成句（85–759 字）＋`summary_text` 354 字＋`section_advice` 4 句；`[32]` 只白名单两层子键（`trigram_interpretation`/`conclusion`），看不出这一层。且 `narrate_core` 反向从 `reasoning_chain` 的 `[格局] A|B` 串里正则反解标签（§一.3 的隐性违反） | 随 A3 分层批做：叙述句改由 fact 渲染，`reasoning_chain` 降为内部键或迁 narrate；届时把该键加入 `[32]` 的嵌套白名单判据。书证与优先级草案见 `liuyao/docs/JUDGMENT-TABLE.md`（313 批） |

**八字侧契约欠账审计（第三百三十六批 A2-B，逐条问过）**

| §六 条款 | 八字侧实测 | 结论 |
|---|---|---|
| 1 chart 不许下判断 | `chart()` 顶层 9 键无成句评价；递归扫输出字符串 >40 字命中 0 | 0 条 |
| 2 analyze 不许写文章 | `analyze()` 顶层无 >80 字字符串；39 处 >40 字全部是 `basis` 书证/判据说明（最长 123 字），不构成成段正文 | 0 条 |
| 3 禁边表 | `bazi/data/rules/layer_contract.json` 4 条零容忍禁边，`[28]` 实跑全绿 | 0 条 |
| 4 键白名单 | chart 9／analyze 26／conclusion 27，`[28]` 实跑全绿 | 已关闭（310 批） |
| 5 render 不许当第二个 narrate | `render()` = `narrate(a)` ＋机械因子表，无新增断语字面量 | 0 条 |
| 6 模块混装 | 八字无 `narrative_utils`/`narrative_rules` 形态；`scripts/bazi_factors/` 是 analyze 段内实现 | 0 条 |
| 7 reasoning_chain 成句 | 八字无 `thinking_chain.reasoning_chain` 键 | N/A（无对应物） |

**结论：八字侧新增欠账 0 条**——这不是"八字干净"的奖状，而是**已按同一套判据问过**的读数。
六爻侧 7 条里在八字侧没有对应物的两项（1 的 `trigram_interpretation`、7 的 `reasoning_chain`）
如实标 N/A，不冒充"通过"；三件套同步见第 336 批两份 `docs/CHANGELOG.md`。

## §七 变更规程

1. 改段界 / 改键面 → 同一批改 **JSON + 本文件 + CHANGELOG**，跑
   `python dev_tools/check_layer_contract.py --selftest`；
2. 禁边表条目只准减不准增；新增一条须在本文件 §三 写明"为什么暂时必须"；
3. 欠账条目只准减不准增；新增欠账须写明"哪一批还"；
4. 本文件不写读数、不写分数、不写"准确率"——口径见 AGENTS.md §一.3。
