---
name: yi-liuren
description: 大六壬起课排盘（骨架版）。用户占一事问课式结构（九宗门三传、天将乘临）时使用。输出起课、三传、课体、天将等机械结构标签；第一版不出吉凶方向（《毕法赋》未落地），只给课式结构，解读归 LLM 翻译。禁止 LLM 心算起课。
---

# 大六壬 · 技能

> 详细执行规程见 `disciplines/liuren/SKILL.md`。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| datetime | 是 | 起课时刻（YYYY-MM-DD HH:MM） |
| question | 是 | 所问之事（占求财/占谋事…） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/liuren/）
python scripts/chart.py --datetime "2024-02-20 10:30" --question "占求财" -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 网页端 AI（零凭证）：拼 ?d=liuren&q=所问之事&dt=起课时刻&auto=1 交用户打开
```

## 输出与纪律

- 输出月将加时、九宗门三传、天将乘临等**机械结构标签**；**无吉凶断语**（课目识别与《毕法赋》未落地，任何方向输出都属占位，禁止）。
- 歧义读数（月将换将/昼夜贵人分界等）以 `verified=False` 如实登记。质量门 `cd disciplines/liuren && python dev_tools/check.py`。
