---
name: yi-lingqi
description: 灵棋经掷棋查课。用户掷灵棋（或报上中下三数）问一事，按书直录断语时使用。输出三部掷数成课、课名/象/卦注/象曰/詩曰全部逐字来自《灵棋经》原文，无书外发挥。禁止 LLM 心算或凭记忆编造课断。
---

# 灵棋经 · 技能

> 详细执行规程见 `disciplines/lingqi/SKILL.md`。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| up / mid / down | 是 | 上/中/下三部掷数（各 0..4，全零不成课） |
| question | 否 | 所占之事（语境） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/lingqi/）
python scripts/chart.py --up 4 --mid 3 --down 2 --question "占谋事" -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 网页端 AI（零凭证）：拼 ?d=lingqi&up=4&mid=3&down=2&q=所占之事&auto=1 交用户打开
```

## 输出与纪律

- 输出课名/象/卦注/象曰/詩曰，**逐字来自书源**（`data/ketables.json`，可回指原文），本仓不做任何书外发挥。
- 解读结合求测语境，但不断章取义、不添补书源没有的判词。质量门 `cd disciplines/lingqi && python dev_tools/check.py`。
