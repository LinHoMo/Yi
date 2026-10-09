---
name: yi-ming
description: 四柱八字排盘与命理机械推演。用户报出生年月日时问一生格局与趋势（宜何业、何时起伏、性情禀赋、大运流年）时使用。输出四柱、藏干十神、空亡、强弱、月令格局、成败救应、喜用、调候、大运流年机械对照；不做命运断语与流年吉凶定论。
---

# 四柱八字 · 技能

> 详细执行规程见 `disciplines/ming/SKILL.md`；判据书源出处与机械规则见 `docs/HANDOFF.md` §命科。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| datetime | 是 | 出生公历时间（YYYY-MM-DD HH:MM） |
| gender | 是 | 男 / 女（定大运顺逆） |
| question | 否 | 想问的方向（可选） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/ming/）
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男 -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 只有四柱干支、无公历时（书源命例）：chart_from_pillars 直填起盘（缺柱报错不猜）

# 网页端 AI（零凭证）：拼 ?d=ming&dt=出生公历时间&gender=男&auto=1 交用户打开
```

## 输出与纪律

- 输出机械因子：四柱/十神/空亡/强弱/格局（含成败救应，书源《子平真诠》主干）/喜用/调候/大运 8 步/流年对照；**不做**"必富必贵、某年一定"式断语。
- 从格仅 tentative 标注；重大决策提示以专业意见为准。
- 禁止 LLM 心算四柱/十神/旺衰（铁律一）；质量门 `cd disciplines/ming && python dev_tools/check.py`。
