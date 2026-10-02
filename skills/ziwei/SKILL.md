---
name: yi-ziwei
description: 紫微斗数安星排盘与格局推演。用户报出生公历时间问一生星盘格局、四化、大限起伏时使用。输出十二宫安星、四化、格局、大限；走四段契约 chart→analyze→narrate→render，排盘由引擎完成，禁止 LLM 心算。
---

# 紫微斗数 · 技能

> 详细执行规程见 `disciplines/ziwei/SKILL.md`。铁律引 `AGENTS.md`。

## 输入字段

| 字段 | 必填 | 说明 |
|---|---|---|
| datetime | 是 | 出生公历时间（YYYY-MM-DD HH:MM） |
| gender | 是 | 男 / 女（定大限顺逆） |

## 调用

```bash
# 本地/服务器（工作目录 disciplines/ziwei/）
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男 -o chart.json
python scripts/analyze.py chart.json -o analyze.json
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md

# 网页端 AI（零凭证）：拼 ?d=ziwei&dt=出生公历时间&gender=男&auto=1 交用户打开
```

## 排盘口径（复述报告前必须与此一致）

- **安星基准是农历月日**（非公历日）：`chart.py` 先用 `core.lunar` 换算农历，再起五行局、定紫微。
- **五行局由命宫干支纳音定**（非年柱纳音）；年干按**立春**分界。
- **大限起宫**：阳男阴女顺行、第一限在**父母宫**；阴男阳女逆行、第一限在**兄弟宫**（所本《紫微斗數全書》卷二·安大限诀）。
- 闰月按「闰月顺延一月」处理（古籍未明言；见 `chart.json` 的 `calendar_policy` 字段）。
- 出生年份限 1900–2049；越界抛 `PaiPanError`，退出码 2。

## 输出与纪律

- 输出安星（十二宫/三方四正）、四化、格局、大限；吉凶解读只转述引擎结构，不夸大。
- 医疗/法律/投资/重大决策提示以专业意见为准；禁止"注定"式措辞。
- 禁止 LLM 心算安星/四化/大限；质量门 `cd disciplines/ziwei && python dev_tools/check.py`
  （含 `[3] 古法回归` 24 项对书源逐条核对、`[4] 语料接线`）。
- 语料外置于 `data/*.json`（主星性情、十二宫星义、庙陷、四化、格局、安星诀、紫微定位表），逐条带书名+卷篇；
  改语料用 `python dev_tools/build_corpus.py` 从 `data/sources/` 书源重建，**不得手改或凭记忆增删**。
- 本科技能内一切分数为**古籍案例对齐分**，不得表述成预测命中率。
