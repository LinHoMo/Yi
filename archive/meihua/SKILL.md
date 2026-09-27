---
name: mei-hua
description: 梅花易数占卜。基于《梅花易数》（邵雍）年月日时起卦、两数起卦等，体用生克断吉凶，互变定中间与终局，卦气旺衰定应期迟速。当用户提到梅花易数、梅花占、体用、生克、观梅占、数字起卦、时间起卦、快速起卦、报数占卜时使用本技能。与六爻同题互验，是其立项目标。
---

# 梅花易数 Skill

> 易 v0.0.1｜给 LLM agent 的工作指令（给人看的介绍见 `README.md`）。
> 项目铁律在 `AGENTS.md`，与任何冲突时以 `AGENTS.md` 为准。

## ⛔ 铁律：起卦与断卦必须由代码执行，LLM 禁止手动排盘

机械运算归代码，象数解读归 LLM（`AGENTS.md` 铁律一）。梅花易数全部推演
——取数起卦、定体用、立互卦变卦、判生克、查卦气旺衰、算数应——**必须且只能**
由 `scripts/chart.py` 与 `scripts/analyze.py` 完成。

LLM **严禁**：心算"（年+月+日）÷8 余几"、手排互卦变卦、口算体用生克、
拍脑袋定应期。没有脚本可跑就说做不了，不得手起梅花卦。

## LLM 的职责（正面清单，与 `AGENTS.md` §二一致）

1. **收集求测信息**：所问何事（一句话）、可选起卦方式：
   - `datetime`：公历时刻（默认当前时间）——年月日时起卦
   - `lunar`：农历年月日 + 时支（观梅占原文式输入）
   - `numbers`：四个数（年数、月数、日数、时数，如观梅占 5,12,17,9）
   - `two_numbers`：两个数 + 时数（物数/字数/声音占，如扣门借物占 1,5,10）
   - 另可收集起卦时的动静状态（行/立/坐/卧），用于数应迟速（《占卜总诀》）
2. **调用脚本**：`chart.py` → `analyze.py` → `narrate.py` → `render.py` 四段管线
   （命令见下）。脚本失败重试一次；仍失败如实报"排盘异常"，不得手动替代。
3. **翻译输出**：把 analyze 输出的结构化因子与判据讲成人话。正文里每个象数结论
   都要能在脚本输出里找到出处——是翻译不是重写。

**LLM 一律不做**：定体用、判生克、查旺衰、算应期、识别特断，以及打开案例库做类比。

## 起卦参数（chart 段）

| 方式 | 参数 | 示例 |
|---|---|---|
| `datetime` | `datetime`（ISO 字符串） | `2026-09-23 10:30` |
| `lunar` | `year`（农历年）+ `month` + `day` + `hour_branch` | 辰年十二月十七申时 |
| `numbers` | `year_num` + `month` + `day` + `hour_num`（月令另传 `month_branch`） | 5,12,17,9 |
| `two_numbers` | `upper_num` + `lower_num` + `hour_num` | 1,5,10 |

`numbers`/`two_numbers` 没有真实时刻，`month_branch`（地支字符）由调用方显式传；
不传则旺衰判"未定"（可复现，不随时间漂移）。`motion` 字段可传 `行/立/坐/卧`。

## 可跑的命令

```bash
# 四段管线一条龙（出 Markdown 报告）
python scripts/render.py [-o outputs/report.md]

# 分步调试
python scripts/chart.py --selfcheck          # chart 段自检（观梅占金标准）
python scripts/analyze.py                    # analyze 段自检
python scripts/chart.py --way numbers --year-num 5 --month 12 --day 17 --hour-num 9 \
       --month-branch 申 --question "占明晚之事" -o scratch/chart.json   # 起卦
python scripts/analyze.py scratch/chart.json -o scratch/analyze.json    # 推演
python scripts/narrate.py scratch/analyze.json -o scratch/正文.md        # 解读
python scripts/render.py scratch/analyze.json -o outputs/report.md      # 报告

# 案例与评测
python scripts/case_runner.py --split all --save   # 跑全部案例出引擎输出
python scripts/evaluate.py --split tune            # tune 对齐分（n=10，参与调参）
python scripts/evaluate.py --split holdout         # holdout 对齐分（n=3，未参与调参）

# 质量门（一条命令全绿）
python tools/check.py                              # 版本/指纹/冒烟/对齐分
python tools/check.py --raise                      # 确认改进后抬基线
python tools/golden.py                             # 金标准指纹验证
```

## 断卦口径（narrate 段的固定骨架）

1. 接住问题 → 亮结论方向
2. 盘面一句话（卦名、动爻、体用、变卦）
3. 体用总诀 + 事类断语（`data/verdicts.json`，带古籍出处）
4. 互变生克：互卦为中间之应、变卦为末后之期；生体之卦各有所应
5. 卦象特断：《卦断遗论》"不拘体用"的特殊卦例优先（`verdicts.json#hexagram_special`）
6. 卦气旺衰与应期：旺则应速衰则应迟；数应按动静（行取半、立取全、坐卧加倍）
7. 口径收尾：凶象用"偏向/有…信号"，不注定；医疗法律投资以专业意见为准

## 一卦一事与口径诚实

- 用户在既问之后换实质角度（换用神、换层面、假设未来、比较两人）→ 提议另起一卦。
- 仓库内所有分数是**古籍案例对齐分**（与《梅花易数》原文要点的吻合度），
  不是现实命中率。报分必须给集合名 + n + 是否参与调参。
- 医疗、法律、投资、重大决策必须提示以专业意见为准。

详细接口见 `references/api_spec.md`，现状与欠项见 `README.md`。
