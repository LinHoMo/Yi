---
name: yi-zeji
description: 择吉通书选日子。用户要搬家/嫁娶/开业/动工/出行等选吉日、查某日吉凶宜忌时使用。输出建除十二神、黄黑道、二十八宿三因子综合裁决与宜忌；裁决口径《协纪辨方书》通行口径，由引擎固定计算，禁止 LLM 心算。
---

# 择吉 · 技能

> 详细执行规程见 `disciplines/zeji/SKILL.md`。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| date | 是 | 用事日期（YYYY-MM-DD） |
| activity | 否 | 事类（开市/嫁娶/出行…，缺省从 question 识别） |
| hour_branch | 否 | 时支（可选） |
| question | 否 | 所问之事（可选） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/zeji/）
python scripts/chart.py --date "2026-10-08" --activity 嫁娶 -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 网页端 AI（零凭证）：拼 ?d=zeji&date=用事日期&activity=事类&auto=1 交用户打开
```

## 输出与纪律

- 输出建除/黄黑道/二十八宿因子与综合裁决（机械因子与多家通书核对，口径固定记录于 `verdicts.json`）。
- 宜忌措辞守铁律三；重大决策（签约、手术等）提示以专业意见为准。质量门 `cd disciplines/zeji && python dev_tools/check.py`。
