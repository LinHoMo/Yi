---
name: yi-liuyao
description: 六爻纳甲起卦断事。用户占具体一事的吉凶趋向与应期（成不成、何时成、丢东西何时找到、官司/投资/考试/出行吉凶）时使用。输入所问之事+起卦时间或摇钱结果，走四段契约 chart→analyze→narrate→render 出报告；排盘断卦由引擎完成，禁止 LLM 心算。
---

# 六爻纳甲 · 技能

> 详细执行规程（收集信息/起卦/解读/自检/措辞箴言）见 `disciplines/liuyao/SKILL.md`，本文件只给调用入口。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| question | 是 | 所问之事（占婚需含性别身份，影响用神选取） |
| datetime | 否 | 起卦时刻；留空默认当前时间 |
| mode | 否 | coin（摇钱）/ time（时间起卦）/ number（数字）/ manual（手摇录入） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/liuyao/）
python scripts/chart.py --mode coin --question "所占之事" -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/render.py analyze.json -o report.md          # 或 --format html

# 网页端 AI（GitHub Pages 深链，零凭证）：拼 ?d=liuyao&q=所问之事&dt=起卦时刻&auto=1 交用户打开
# 云端（要留档）：见 docs/AI-SOP.md 通道 B
```

## 输出与纪律

- 报告含：装卦、六亲、用神、月日旺衰、动变、应期；吉凶措辞守 `AGENTS.md` 铁律三（对齐分≠命中率、凶象用"偏向"）。
- 一卦一事：换角度提问→另起一卦。禁止 LLM 心算装卦/纳甲/应期。
- 质量门：`cd disciplines/liuyao && python dev_tools/check.py`。
