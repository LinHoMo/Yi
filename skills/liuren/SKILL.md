---
name: yi-liuren
description: 大六壬起课排盘（骨架版）。用户占一事问课式结构（九宗门三传、天将乘临、课目）时使用。输出起课、三传、课体、天将、课目等机械结构标签；本版不出吉凶方向（《毕法赋》未落地），课目识别只落纯结构判据（条数以 disciplines/liuren/scripts/kemu.py 的 IMPLEMENTED 为准）仍不出方向，解读归 LLM 翻译。禁止 LLM 心算起课。
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
# 通道覆盖：本地 CLI / 通道 A 网页（Pyodide）/ 通道 B 云端 Actions 三路皆通，八科全挂载；
# 权威矩阵见仓库根 llms.txt「能力矩阵」，此处只引用不复制。
```

## 输出与纪律

- 通道覆盖见根 `llms.txt` 能力矩阵（八科全挂载），本文件不复制矩阵。
- 输出月将加时、九宗门三传、天将乘临等**机械结构标签**；**无吉凶断语**（骨架科；课目识别只落纯结构判据，条数以 `disciplines/liuren/scripts/kemu.py` 的 `IMPLEMENTED` 为准，仍不出方向）。
- 歧义读数（月将换将/昼夜贵人分界等）以 `verified=False` 如实登记。质量门 `cd disciplines/liuren && python dev_tools/check.py`。
