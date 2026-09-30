---
name: yi-meihua
description: 梅花易数起卦断事。用户报数字/时间/字画快速起卦问一事吉凶与象应时使用。输出体用生克、互变卦、卦气旺衰、万物类象、数应；走四段契约 chart→analyze→narrate→render，起卦推演由引擎完成，禁止 LLM 心算。
---

# 梅花易数 · 技能

> 详细执行规程见 `disciplines/meihua/SKILL.md`。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| question | 是 | 所问之事 |
| way | 否 | datetime（时间起卦，默认）/ lunar / numbers（报数）/ two_numbers / manual |
| numbers | 否 | 数字（逗号分隔，way=numbers 时用） |
| datetime | 否 | 起卦时刻；留空默认当前时间 |
| motion | 否 | 行 / 立 / 坐 / 卧（数应迟速） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/meihua/）
python scripts/chart.py --question "所占之事" --way datetime --datetime "2026-09-30T10:00" -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 网页端 AI（零凭证）：拼 ?d=meihua&q=所问之事&dt=起卦时刻&auto=1 交用户打开
```

## 输出与纪律

- 输出体用/互变/卦气旺衰/类象/数应；分数为古籍案例对齐分（规则与案例同源，仅作回归参考）。
- 禁止 LLM 心算体用/互变/旺衰；一卦一事，换角度另起。质量门 `cd disciplines/meihua && python dev_tools/check.py`。
