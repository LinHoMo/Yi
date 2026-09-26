# 易 · 现状交接

> 取代口头交接。分数口径的逐次变化一律查 `docs/CHANGELOG.md`；
> 本文件只写「现在是什么、怎么跑、还欠什么」。
> **一切分数是古籍案例对齐分，不是现实预测命中率**（`AGENTS.md` 铁律三）。
> 路线与里程碑：`docs/YI-PLAN.md`、`docs/LIUYAO-PLAN.md`。

---

## 一、现在能不能信（按科）

### 六爻（disciplines/liuyao）— 可上岗助手

| 事项 | 状态 |
|---|---|
| 装卦/历法 | 可信（历法 16 项、爻序 23、金标准 288 例指纹 `65e8331c80c4f06a`；清刻本逐爻核对 822 纳甲/105 卦变/120 世应 0 不合） |
| 用神取法 | 四层：关系法则 → 代码消歧 → 186 键词典 → 世爻兜底；外部集原文明写 4/4 |
| 吉凶方向 | tune 95%、holdout 83%、wikisource 87%（strict） |
| **应期** | **有判别力**：tune top-1 **58.8%**（随机~38，+20.8pt）；holdout **50.0%**（随机~36.5，+13.5pt） |
| 病药/星煞 | 结构化进 analyze/narrate；**尚未**进 step5 加权与评分 |
| 断语治理 | chain_step5 已入 `verdict_texts.json`；`classical_rules` 仍有残余字面量 |
| 现实命中率 | **无法评估** |

**当前读数（strict，`python tools/check.py`）**：

| 集合 | n | 对齐分 | top-1 | 备注 |
|---|---|---|---|---|
| tune | 20 | **93.9** | 58.8% | 参与过调参 |
| holdout | 12 | **85.7** | 50.0% | 未参与调参 |
| wikisource_holdout | 35 | **57.3** | 20.0% | 永不调参 |
| yingqi_holdout | 2 | 87.2 | — | n 过小仅参照 |
| 黑箱回归 | 18 | 13/18 | — | 基线 ≥11 |

对外引用：优先 holdout/wikisource，必须带 n 与集合名。

### 梅花 — 骨架+浅断

- 类象入 `verdicts.json`；多爻动体用（通行扩展口径）
- tune/holdout 100%（n=10/8）——同源自洽，不证明泛化

### 小六壬 — 邻宫/方位已机械化

- tune/holdout 100%（n=10/5）

### 择吉 — 神煞辅助已入裁决

- 天月德/冲肖煞方/彭祖百忌；tune/holdout 100%（n=10/5）
- **仍是历法规则自洽，非古书占验黑箱**

### 命科 / 合参

- 命推演未建（仅 `ming_tables`/`relations`）；合参 CLI / outcome-eval 可用

---

## 二、怎么跑

```bash
# 仓库级
python tools/check.py              # 结构/内核/四科/合参
python tools/check.py --full       # 加六爻黑箱回归与案例评测

# 六爻
cd disciplines/liuyao
python tools/check.py              # 质量门（金标准/回归/对齐分/应期）
python scripts/evaluate.py --split tune|holdout|all
python scripts/yi_liuyao.py "所问之事" --when "..."   # 一键报告

# 其余三科
cd disciplines/{meihua,xiaoliuren,zeji}
python tools/check.py
```

流派开关（改了分数不可比）：`YI_GANZHI_BOUNDARY=day|instant`、`--zi-hour-type late`。

---

## 三、应期规则（核心资产）

位置：`disciplines/liuyao/scripts/chain_step5.py` → `_predict_timing`。
**全部为通用古例归纳，禁止 case-specific**。

优先级（高→低）：

1. **化出之支逢空** → 出空值日
2. **空而化回头生** → 不作空论，期于生我之日（非空卦不前插）
3. 用神旬空：日辰已冲→当日；久病→冲空；近病→填实；一般→填实+冲空
4. 伏藏：**飞克伏→先冲飞**；仅飞空得出→伏神值日
5. 月破/入墓/合住：填实、冲墓、冲开
6. 用神不空：**动爻先值日再逢合**；静爻值日再逢冲
7. 同五行空亡支出空 → 其他空亡出空 → 三合/原神/化出/旺相

否证（勿重复踩坑）：病药应期生硬插队→回退；按书序整体重排日级预算→三集全降已回滚；回头生全局前插→挤掉值日已改仅空卦。

---

## 四、还欠什么（按优先序）

1. **wikisource** 应期 top-1 ~20%（n=35）：泛化未证明；**方向集** `wikisource_direction` n=36（72.2%）；应期扩样须换书或 outcome n≥30，**禁止考卷上调参**
2. ~~classical_rules 断语外置~~ **部分完成**：完整句+模板已入 JSON；符号标签/文档字符串留代码
3. **病药/星煞**：病药有界加减已入 step5；**星煞不进主分**（无古籍定性表）；药码进应期排序已否证
4. **梅花** holdout 13 例（含卷二/三）+「变克体终局」通则；**择吉**通书真黑箱仍待补
5. **命科**：强弱/格局/喜用/大运机械推演已立（起运岁=距节/3）；流年吉凶与从格定论未做
6. 应期相对表述：语义对齐 + 有锚日绝对窗（`yingqi_windows`）；无锚日案例仍不可换算
7. ~~金标准不含 narrate~~ **抽样已含文案哈希**；报告六要素大体齐

---

## 五、口径与纪律

1. 对齐分 ≠ 预测率；禁止「准确率 X%」话术
2. 报分必带：集合名 + n + 是否调参
3. 改引擎：tune/holdout 分列；tune 无故跌破基线即回归；只改通用规则并给古籍出处
4. 口径变更必须记 `docs/CHANGELOG.md`
5. 案例库解读隔离；一卦一事
6. 金标准 `capture` 必须写理由

---

## 六、本轮整洁（2026-09-26）

- 删除死代码：`factor_waterfall.py`、`engine_legacy.py`、`hallucination_guard.py`；`liuyao_engine` 仅保留 coin/time/number/manual；`visualization` 收敛为 SVG 卦盘
- 删除过期研究稿：`precision_gaps.md`、`regression_failure_analysis.md`、`open_source_research.md`
- PLAN 收为路线表；双 HANDOFF 合并为本文件
- 详见 `docs/CHANGELOG.md` 2026-09-26e
