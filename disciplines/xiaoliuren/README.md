# 小六壬（卜③）

六宫掌诀占卜：大安、留连、速喜、赤口、小吉、空亡。基于《贺氏六壬小手册·小六壬预测法》推算方法与六宫释义。

## 一条命令出报告

```bash
# 报数起课 → 分析 → 报告
python scripts/chart.py --way numbers --numbers 7,7,2,3,4 --question "纠纷能解决否" -o scratch/chart.json
python scripts/analyze.py scratch/chart.json --out scratch/analyze.json
python scripts/render.py scratch/analyze.json -o scratch/report.md
```

质量门（一条命令跑完所有检查）：

```bash
python tools/check.py
```

## 现在的真实水平（2026-09-23，strict 口径）

| 集合 | 对齐分 | n | 口径说明 |
|---|---|---|---|
| tune | 100% | 10 | 参与过校参（《贺氏六壬小手册》实例 8 + 推算方法书例 2） |
| holdout | 100% | 5 | 未参与校参（正宗起课例 + 机断练习例） |

说明：**本分数衡量引擎输出与古籍案例要点的一致性，不是现实预测命中率**（`AGENTS.md` 铁律三）。
落宫判定是纯机械真值（月上起日、日上起时）；断语要点取自同一原文，故两集合均高发。
综合判断案例（空亡测座位等）吉凶/事类记 N/A——宫义不可死套，engine 不越权改判。

## 已实现

- **chart 段**（`scripts/chart.py`）：月日时起课、变通/随机取数起课、公历时刻起课（内核转农历）、农历+时支起课；可选 `direction` 方位参数；6 例贺氏实例金标准自检
- **analyze 段**（`scripts/analyze.py`）：六宫六要素（五行/颜色/方位/属神/主数/位置）、吉凶方向、十类事类诀辞切句、应期主数、**邻宫速断**（进/退/临）、**方位/五行综合断**（生克关系）；断语全部来自 `data/verdicts.json`（带出处）
- **narrate 段**（`scripts/narrate.py`）：师傅口吻正文，只装配判据不新造结论
- **render 段**（`scripts/render.py`）：单文件 Markdown 报告（正文 + 盘面数据 + 判读因子）
- **案例库**（`data/cases/xiaoliuren_cases.json`）：tune 10 / holdout 5 / excluded 2，全部可还原
- **评分器**（`scripts/evaluate.py`）：复用 `yishu_core.eval`，维度 落宫30/吉凶方向30/事类诀句20/应期主数20
- **质量门**（`tools/check.py`）：金标准指纹（15 例）+ 管线冒烟 + tune/holdout 分别出分带 n

## 未来路线

- 与六爻/梅花同题互验（同求测者同一事，跨科合参）

## 纪律

- 起课掐算必须由 `chart.py` 执行，LLM 禁止手动"月上起日"（`AGENTS.md` 铁律一）
- 断语文字只在 `data/verdicts.json`，代码不含断语字面量
- 分数口径只作回归用，对外不宣称预测命中率
