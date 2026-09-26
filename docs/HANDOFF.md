# 易 · 现状交接

> 取代口头交接。分数口径的逐次变化一律查 `docs/CHANGELOG.md`；
> 本文件只写「现在是什么、怎么跑、还欠什么」。
> **一切分数是古籍案例对齐分，不是现实预测命中率**（`AGENTS.md` 铁律三）。
> 路线：`docs/YI-PLAN.md`、`docs/LIUYAO-PLAN.md`。规格归档：`docs/compose/spec/`。

**基线**：`main` @ `c126b02`（2026-09-26，含 repo-tidy / yi-optimize / deep-optimize 三轮）。

---

## 一、现在能不能信（按科）

### 六爻（disciplines/liuyao）— 可上岗助手

| 事项 | 状态 |
|---|---|
| 装卦/历法 | 可信（历法 16 项、爻序 23、金标准 288 例指纹 **`5c6e77ee253b0ddd`**；清刻本 822 纳甲/105 卦变/120 世应 0 不合） |
| 用神取法 | 四层：关系法则 → 代码消歧 → 186 键词典 → 世爻兜底 |
| 吉凶方向 | tune 95%、holdout 83%、wikisource 87%（strict 分项） |
| **应期** | tune top-1 **58.8%**（随机~38）；holdout **50.0%**（随机~36.5） |
| 病药 | 已进 step5 有界加减（重病无药 −0.4 等）；**星煞不进主分**（无古籍定性表） |
| 断语治理 | 完整句 + 拼装模板入 `verdict_texts.json`（`ctext`/`ctpl`）；符号标签/docstring 留代码 |
| 呈现 | `render` 单一出口 + SVG 卦盘；MCP `liuyao.narrate` / `liuyao.render` |
| 现实命中率 | **无法评估** |

**当前读数（strict，`cd disciplines/liuyao && python tools/check.py`）**：

| 集合 | n | 对齐分 | top-1 | 备注 |
|---|---|---|---|---|
| tune | 20 | **93.9** | 58.8% | 参与过调参 |
| holdout | 12 | **87.5** | 50.0% | 未参与调参 |
| wikisource_holdout | 35 | **57.3** | 20.0% | 永不调参（应期） |
| wikisource_direction | 36 | **72.2** | — | 有吉凶无验期；应期 N/A |
| yingqi_holdout | 2 | 87.2 | — | n 过小仅参照 |
| 黑箱回归 | 18 | 12/18 | — | 基线 ≥11 |

对外引用：优先 holdout/wikisource，**必须带 n 与集合名**；勿把 direction 集当应期成绩。

### 梅花 — 可用浅断

- tune/holdout **100%**（n=10/**13**，含《梅花易数》卷二/三）
- 通则：**变卦克体 → 终局不言吉**（《体用总诀》变乃末后之期）
- 同源居多，不证明泛化

### 小六壬 — 邻宫/方位已机械化

- tune/holdout 100%（n=10/5）

### 择吉 — 规则应用黑箱

- 天月德/冲肖煞方/彭祖百忌入裁决；**12 建除全覆盖**
- tune/holdout 100%（n=10/**6**）；期望由 `verdicts.json` 独立推出
- **仍非通书日例应验**（仓库无带应验古例，不伪造）

### 命科 — 机械推演已立（非命运断言）

- 强弱（藏干加权+得令）/ 月令本气定格 / 扶抑喜用 / 大运 8 步
- 起运岁 ≈ 距下一节气日数 ÷ 3（`DAYS_PER_LUCK_YEAR`，标 approximate）
- 6 样例金标准 `91f64b857cc6597e`；合参 `normalize_ming` 带 strength/pattern
- **不做**：格局从格定论、流年吉凶、命运断语

### 合参 / 工具

- `tools/eval.py` 四科对齐分一览；`tools/demo.py`；MCP 完整四段
- person 档案 + outcome-eval 可用；命科有记录时趋势维度可参评

---

## 二、怎么跑

```bash
# 仓库级
python tools/check.py              # 结构/内核/五科/合参（含巨石看门狗 ≤2200 行）
python tools/check.py --full       # + 黑箱回归与案例评测
python tools/eval.py               # 四科 tune/holdout 一览

# 六爻
cd disciplines/liuyao
python tools/check.py
python scripts/evaluate.py --split tune|holdout|wikisource_holdout|wikisource_direction
python scripts/yi_liuyao.py "所问之事" --when "..."
python scripts/mcp_server.py       # JSON-RPC：divinate/quick/narrate/render/…

# 命科
cd disciplines/ming
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男
python tools/check.py

# 其余
cd disciplines/{meihua,xiaoliuren,zeji} && python tools/check.py
```

流派开关（改了分数不可比）：`YI_GANZHI_BOUNDARY=day|instant`、`--zi-hour-type late`。

**金标准**：`python tools/golden.py verify`；改动后 `capture "理由"`（无理由不落盘）。

---

## 三、应期规则（核心资产）

位置：`chain_step5_yp._predict_timing`（由 `chain_step5.step5_synthesize` 调用）。
**全部为通用古例归纳，禁止 case-specific**。

优先级（高→低）：

1. **化出之支逢空** → 出空值日
2. **空而化回头生** → 不作空论，期于生我之日（非空卦不前插）
3. 用神旬空：日辰已冲→当日；久病→冲空；近病→填实；一般→填实+冲空
4. 伏藏：**飞克伏→先冲飞**；仅飞空得出→伏神值日
5. 月破/入墓/合住：填实、冲墓、冲开
6. 用神不空：**动爻先值日再逢合**；静爻值日再逢冲
7. 同五行空亡支出空 → 其他空亡出空 → 三合/原神/化出/旺相

**评分口径（strict）**：基准无地支的相对窗（次日/年内/月余…）→ 字面 / `RHYTHM_PAIRS` 0.7× / 有锚日绝对窗（`yingqi_windows`）。与更早 strict 分数**不可比**（见 CHANGELOG 2026-09-26i）。

否证（勿重复踩坑）：

- 病药/药码进应期主排序 → holdout top-1 50→37.5，**已回退**
- 按书序整体重排日级预算 → 三集全降，**已回滚**
- 回头生全局前插 → 挤掉值日，**改仅空卦**

---

## 四、还欠什么（按优先序）

1. **wikisource 应期泛化** top-1 ~20%（n=35）：须换书（《卜筮正宗》《火珠林》）或 outcome n≥30；**禁止考卷上调参**。方向集 n=36 已立（72.2%）。
2. **择吉通书真黑箱**：现为规则应用黑箱；需带应验的古例日例（不伪造）。
3. **星煞**：无古籍定性表前不进主分；有表后须三集对照再进。
4. **命科**：从格定论、流年表（只干支十神可做）、起运余数折算更细。
5. **梅花/小六壬**外部真案例（非同源构造例）。
6. **chain_step5.synthesize** 本体仍约 990 行；`human_narrative` 1035 行——低于看门狗线，可再按域拆。
7. 报告「格局详释」仅在有格局词时渲染——清单项依赖案例是否触发格局。

---

## 五、口径与纪律

1. 对齐分 ≠ 预测率；禁止「准确率 X%」话术
2. 报分必带：集合名 + n + 是否调参；direction 集与应期集分开报
3. 改引擎：tune/holdout 分列；tune 无故跌破基线即回归；只改通用规则并给古籍出处
4. 口径变更必须记 `docs/CHANGELOG.md`，否则分数不可比
5. 案例库解读隔离；一卦一事
6. 金标准 `capture` 必须写理由；因子表增字段也会改指纹
7. 拆分/搬家以**零指纹漂移**为验收；巨石看门狗 2200 行

---

## 六、架构要点（2026-09-26）

```
core/yishu_core     唯一真值源（历法/象数/卦辞/评分/报告/命表）
disciplines/<科>    四段契约 chart→analyze→narrate→render
synthesis           person + 合参 + outcome-eval
tools               check / eval / demo / install
```

- **已拆巨石**：`classical_rules`→hidden/patterns/effects；`chain_step4`→changes/patterns；`chain_step5`→dates/timing/conf/yp（门面保 API，零漂移）
- **MCP**：divinate / quick_reading / **narrate** / **render** / validate / quotes
- 死代码已清：`engine_legacy`/`hallucination_guard`/`factor_waterfall`/`hexagrams.json` 双源

---

## 七、本轮变更索引（便于回查 CHANGELOG）

| 记号 | 内容 |
|---|---|
| 26e | 仓库整洁、断语外置第一批 |
| 26f/g | classical_rules 完整句/模板；病药入 step5；MCP+eval+命骨架 |
| 26h | 命科强弱格局大运；wikisource_direction；梅花变克体 |
| 26i | 起运岁距节折算；相对应期窗 strict |
| 26j | 金标准 narrate 文案哈希；应期绝对窗 |
| 26k/l/m | classical_rules / chain_step5 / chain_step4 拆分 + 巨石门；择吉破日 |
