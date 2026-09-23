# 梅花易数 · 接口规格（api_spec）

四段管线契约（`docs/CONTRACT.md` §一）：`chart → analyze → narrate → render`。
每一段的输入输出都是结构化 dict，段间只传结构化数据，LLM 只出现在 narrate 之后。

## 一、chart 段（`scripts/chart.py`）

**输入**（`chart(params)`，params 为 dict）：

| 键 | 类型 | 说明 |
|---|---|---|
| `way` | str | `datetime` / `lunar` / `numbers` / `two_numbers`，默认 `datetime` |
| `datetime` | str/datetime | `way=datetime` 时：公历时刻 ISO 字符串 |
| `year` `month` `day` `hour_branch` | int×3 + str | `way=lunar`：农历年月日 + 时支 |
| `year_num` `month` `day` `hour_num` | int | `way=numbers`：四数起卦（观梅占式） |
| `upper_num` `lower_num` `hour_num` | int | `way=two_numbers`：两数 + 时数 |
| `month_branch` | str | 地支字符（如"寅"）；numbers/two_numbers 必传，不传为 None（旺衰"未定"） |
| `motion` | str | `行`/`立`/`坐`/`卧`，默认`立`；数应迟速用 |
| `question` | str | 问事文本（自动识别事类 topic） |

**输出**（chart 段关键字段）：

| 字段 | 说明 |
|---|---|
| `hexagram` / `upper` / `lower` / `moving` | 别卦名、上下经卦、动爻（1–6） |
| `body` / `use` / `body_element` / `use_element` | 体用卦与五行（动爻在下→上为体；动爻在上→下为体） |
| `interacting_lower` / `interacting_upper` | 互卦下、互卦上（去初爻上爻） |
| `changed_hexagram` / `changed_trigram` | 变卦别卦名 / 变出之卦（动爻所在经卦变后的经卦，论五行用） |
| `lines` / `changed_lines` | 六爻线（自下而上）、变后爻线 |
| `total` | 成卦之数（数应迟速用） |
| `month_branch` | 月令支（datetime/lunar 路径自动算；numbers 由调用方传） |
| `topic` / `question` / `way` / `motion` | 事类、问话、起卦方式、动静 |

**起卦规则**（《卷一·年月日时起例》）：上卦=(年+月+日)÷8 之余（余 0 作 8），
下卦=(年+月+日+时)÷8 之余，动爻=(年+月+日+时)÷6 之余（余 0 作 6）；
两数起卦：上卦=物数÷8 之余、下卦=时数（或字数）÷8 之余、动爻=(上下和+时)÷6 之余
（《卷一·卦以八除》"过八数即以八数递除"）。

## 二、analyze 段（`scripts/analyze.py`）

**输入**：chart 段输出 dict。

**输出**（analyze 段关键字段）：

| 字段 | 说明 |
|---|---|
| `body_use` | 体卦/用卦/五行/关系（体克用、用克体、体生用、用生体、比和）+ 关系判语 |
| `interaction` | `生体之卦`/`克体之卦`：各卦的作用（生体/克体/体生/体克/比和）与位（用卦/互卦下/互卦上/变卦） |
| `body_qi` | 卦气旺衰 `{状态(旺相休囚死), 月支, 体卦五行}`；无月令为 None |
| `topic_verdict` | 事类断语（`data/verdicts.json#topics`，带所本） |
| `sheng_ti` / `ke_ti` | 生体/克体卦的具体含义（`verdicts.json#sheng_ti_meaning`） |
| `timing` | 卦气应期干支、应期速度（旺速衰迟）、生体/克体卦应期、数应（《占卜总诀》动静定应期：行取半、立取全、坐卧加倍） |
| `conclusion` | `{方向, 说明, 特断?, 所本}`；特断优先（`verdicts.json#hexagram_special`，《卦断遗论》不拘体用例） |
| `factors` | 判读因子表（体用关系 40 / 生克之卦 30 / 卦气旺衰 20 / 应期 10） |
| `chart_summary` | 盘面摘要（narrate 标题与盘面数据用） |

**综合判断规则**：体用总诀基准分 + 互变净势修正（《卦断遗论》"互变生之而吉""互变俱克之而凶"）
+ 卦气旺衰修正；卦象特断命中即不再套体用生克。

## 三、narrate 段（`scripts/narrate.py`）

**输入**：analyze 段输出 dict。
**输出**：Markdown 正文（唯一交付正文，师傅口吻）。
**边界**：不自行推断任何新的象数结论；正文每个判断都能在 analyze 输出中找到出处。

## 四、render 段（`scripts/render.py`）

**输入**：analyze 段输出 dict；可选 `out_path`。
**输出**：Markdown 报告全文（narrate 正文 + 盘面数据表 + 判读因子表，机器可复核）。

## 五、案例与评分

| 文件 | 作用 |
|---|---|
| `data/cases/meihua_cases.json` | 案例库：tune 10 + holdout 3 + excluded 2（理由见 `_meta`） |
| `scripts/case_runner.py` | 案例 → 引擎输出 `{"cases": [...], "errors": [...]}` |
| `scripts/evaluate.py` | 对齐分（复用 `yishu_core.eval`，权重：关系 30/方向 30/生体 15/克体 15/数应 10） |
| `tools/golden.py` | chart+analyze 逐字段指纹（基线 `data/golden/digest.json`） |
| `tools/check.py` | 质量门：版本/指纹/冒烟/对齐分（只准前进不准后退） |
