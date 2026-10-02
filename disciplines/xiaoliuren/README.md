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
python dev_tools/check.py
```

## 现在的真实水平（2026-10-01）

> 读数以 `docs/EVAL-AUDIT.md` 为准（集合构成与自洽项占比在那里）；本 README 不另抄分数。

**报法**：`holdout`，n=5（书上原例 2 + 按规则表构造 3），**规则自洽回归：落宫 5/5、
吉凶 5/5、事类 5/5、主数 5/5 命中**（n<20 不报百分比，不出具任何"准确率"表述）。

- **100% 的成因**：四个维度（合计 100/100 权重）的 expected 全部来自引擎自己的规则表——
  落宫是同一算法算两遍，吉凶/事类/主数是 `verdicts.json` 的查表回读；
  等价于"查表管线没被改坏"，**不含任何外部信息**。
- 综合判断案例（空亡测座位等）吉凶/事类记 N/A——宫义不可死套，engine 不越权改判。

## 已实现

- **chart 段**（`scripts/chart.py`）：月日时起课、变通/随机取数起课、公历时刻起课（内核转农历）、农历+时支起课；可选 `direction` 方位参数；6 例贺氏实例金标准自检
- **analyze 段**（`scripts/analyze.py`）：六宫六要素（五行/颜色/方位/属神/主数/位置）、吉凶方向、**十一门**事类断语（每门每宫标 `句类`：诀辞/引申/阙）、应期主数、**邻宫速断**（进/退/临）、**方位/五行综合断**（生克关系）；断语全部来自 `data/verdicts.json`（带出处）
- **narrate 段**（`scripts/narrate.py`）：师傅口吻正文，只装配判据不新造结论；含「本门覆盖」行与「断语来源与覆盖」小节（公版书源缺口如实说明）
- **render 段**（`scripts/render.py`）：单文件 Markdown 报告（正文 + 盘面数据 + 判读因子）
- **案例库**（`data/cases/xiaoliuren_cases.json`）：tune 10 / holdout 5 / excluded 2，全部可还原；`expected.topic_line` 是 `verdicts.json#topic_lines` 的镜像（自洽项）
- **评分器**（`scripts/evaluate.py`）：复用 `yishu_core.eval`，维度 落宫30/吉凶方向30/事类诀句20/应期主数20
- **质量门**（`dev_tools/check.py`）：金标准指纹（15 例）+ **`[1c]` 断语口径门**（句类相符 + 矩阵完整 + 记账一致 + 缺口登记）+ 管线冒烟 + tune/holdout 分别出分带 n

## 古籍来源：**无公版书源**（如实登记）

- 实测 `python tools/fetch_source.py --check 小六壬 小六壬掌訣 六壬時課 萬法歸宗 六壬類聚`
  → 维基文库**全部 missingtitle**：小六壬没有可抓的公版专书。
- 现行断语所本《贺氏六壬小手册》是**现代文本、非公版**，本仓一律标该书节次，
  **不冒充古籍原文，也不据记忆补写口诀**。缺口登记在 `data/verdicts.json#source_gap`。
- 因此「真实能力」的增量方向是**把已有断语逐条判类、把无据的如实标阙**，
  而不是堆量：66 条里 诀辞 40 / 引申 25 / 阙 1，全部可机检。

## 未来路线

- 与六爻/梅花同题互验（同求测者同一事，跨科合参）

## 纪律

- 起课掐算必须由 `chart.py` 执行，LLM 禁止手动"月上起日"（`AGENTS.md` 铁律一）
- 断语文字只在 `data/verdicts.json`，代码不含断语字面量
- 分数口径只作回归用，对外不宣称预测命中率
