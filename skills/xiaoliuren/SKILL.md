---
name: yi-xiaoliuren
description: 小六壬掌诀速断。用户需要临场快速断事（掐指一算），报月日时或报数问一事吉凶时使用。输出六宫掌诀、邻宫速断、五行方位综合；起课查诀由引擎完成，禁止 LLM 心算。
---

# 小六壬 · 技能

> 详细执行规程见 `disciplines/xiaoliuren/SKILL.md`。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| question | 是 | 所问之事 |
| way | 否 | datetime（默认当前时间）/ lunar / month_day_hour / numbers |
| datetime | 否 | 起课时刻（月日时） |
| numbers | 否 | 数字（逗号分隔，way=numbers 时用） |
| topic | 否 | 事类（可选，显式给事类） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/xiaoliuren/）
python scripts/chart.py --question "所占之事" --datetime "2026-09-30T10:00" -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 网页端 AI（零凭证）：拼 ?d=xiaoliuren&q=所问之事&dt=起课时刻&auto=1 交用户打开
```

## 输出与纪律

- 输出六宫落位、邻宫速断、五行方位；n=15 案例取自《贺氏六壬小手册》，分数仅作回归用。
- 禁止 LLM 心算掌诀/落宫；凶象用"偏向/有…信号"。质量门 `cd disciplines/xiaoliuren && python dev_tools/check.py`。
