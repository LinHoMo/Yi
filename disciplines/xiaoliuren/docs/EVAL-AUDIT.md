# 小六壬 · 评测口径审计（EVAL-AUDIT）

> 结论针对 `data/cases/xiaoliuren_cases.json` + `scripts/evaluate.py` + `scripts/case_runner.py`
> 的**评测设计**，不评判推演逻辑本身。铁律三：本文所有数字都是**规则自洽回归数**，
> 不是古籍案例对齐分，更不是现实预测命中率。
>
> **复核命令**（只读）：`python tools/eval_audit_recheck.py`（D 段即本文 §二/§三 的逐例实测）。

## 一、一句话结论

**tune n=10 / holdout n=5 均为 100%，该读数不含任何外部信息。**
四个计分维度（合计 100/100 权重）的 expected 全部来自**引擎自己的规则表**：
落宫是同一算法算两遍，吉凶/事类/主数是 `verdicts.json` 的查表回读。
100% 等价于"查表管线没被改坏"，**不是**"断得准"。

## 二、案例集怎么构造的

| 项 | 值 | 证据 |
|---|---|---|
| case 总数 | 17（+ excluded 2 = XLR901、XLR902 原文信息不全） | `_meta.total_cases`；逐例 `split` |
| tune | 10（XLR001–XLR010） | 逐例 `split` |
| holdout | 5（XLR101–XLR105） | 逐例 `split` |
| 来源 | 全部署《贺氏六壬小手册》（国学大师文库本） | 逐例 `source` |
| `expected` 字段填充 | `timing` 15/15、`palace` 15/15、`verdict` 14/15、`topic_line` 14/15 | 逐例 `expected` |
| 计分权重 | palace 30 / verdict 30 / topic 20 / timing 20 | `evaluate.py:35-40` |

### expected 是"书上的原始结论"还是"反推"？——**一半以上是反推**

| provenance | n | 含义 |
|---|---|---|
| `book_original` | 12 | 起课输入取自书上原例（但吉凶/事类是否原文明言另计，见下） |
| `engine_derived` | 3 | XLR103–XLR105「机断练习例」：**无书籍来源**，吉凶/事类/主数直接取 `verdicts.json` 标准义 |

逐例细看（已写进各例 `note`）：

- **XLR001–XLR004**：原文实例，落宫与断语均原文明载，`expected` 是真·书上结论。✔
- **XLR005**：原文落宫明载，且原文自称"空亡不能解释为无座位" → expected 的 `verdict`/`topic_line`
  记 `null` 走 N/A。**这是本库唯一一处"承认引擎口径不适用"的诚实标注。** ✔
- **XLR006–XLR008**：综合判断例，原文落宫明载，但吉凶/事类由本仓表补齐（原文主张不死套宫义）。
- **XLR009 / XLR010 / XLR101 / XLR102**：原文只推至日宫/月宫，**时辰按子时补足**成完整课体；
  `verdict`/`topic_line`/`timing` 三项由本仓标准义补齐 → 即 **tune 与 holdout 用同一张表同一套补法**。
- **XLR103–XLR105**：完全构造，`note` 自述"机断练习例（六宫释义标准义）"。

**泄漏实锤（关键）**：holdout 的 XLR101/XLR102 与 tune 的 XLR009/XLR010 同源同法——
同一份 `verdicts.json` 既参与了 tune 期校参，又充当 holdout 的答案。
更直接的是：expected 的写法与引擎查表的**键完全相同**，命中是必然的。
实测（recheck D 段）：15 例中 13 例「吉凶同表 + 主数同表 + 诀句逐字同表」，
2 例为「回退总诀」路径，唯一不同表的 XLR005 正是被显式豁免的那一例。

## 三、打分构成：逐项标「真判据 / 自洽项」

| 维度 | 权重 | 判定 | 依据 |
|---|---|---|---|
| `palace` | 30 | **自洽项（历法真值）** | 月上起日、日上起时，`chart.py` 与 expected 用同一算法；实测 15/15 相同。随机基线 1/6 = 16.7% |
| `verdict` | 30 | **自洽项** | `analyze.py:118` `direction = VERDICTS["direction"][palace_name]`；expected 亦为同表同键（实测 14/14 相同） |
| `topic` | 20 | **自洽项** | `analyze.py:121` 查 `VERDICTS["topic_lines"][topic][palace]`，空则回退 `palaces[palace].总诀`；实测 15 例中 12 例逐字同表、2 例回退总诀、1 例 N/A |
| `timing` | 20 | **自洽项** | `analyze.py:176` 取 `palaces[palace].主数`；expected 为同一数组（实测 15/15 相同） |

**自洽项合计 100/100** —— 本集没有一项在检验引擎自己的判断。
缺失字段记 N/A 从分母剔除（`evaluate.py:75-76`、`:92-93`），未被算成答对（XLR005 即用此机制）；
tune 适用权重 950/1000（N/A 5.0%），holdout 500/500（无 N/A），信息加权分同为 100.0。

## 四、tune / holdout 切分方式

- **人工指定**，不是随机切分：逐例 `"split"` 字段，`case_runner.py:37-40` 按字段过滤。
- 无 ID 重叠。**但答案表重叠**（同一份 `verdicts.json` 供两集；补齐方法相同）。
- tune 与 holdout 的**构造方式同源**：都是"书上落点 + 本仓标准义补齐"，只是日期不同。
- 修掉一处文档矛盾：文件原 `note` 写"holdout 为未参与校参的机断练习例与正宗起课例"，
  但 XLR101/XLR102 的吉凶/事类恰是按 tune 期同一张表补齐的（已在 `_provenance` 写明）。

## 五、诚实呈现口径（结论）

**能说明**：六宫掌诀的起课递推（月→日→时）与 `verdicts.json` 的查表管线在 15 例上
**自我一致**，且 `dev_tools/golden.py` 指纹 `0088d638d065402d` 未漂移——可作为
**结构回归的证据**。

**不能说明**：
1. 不能说"准确率 100%"——这是查表回归数，连"古籍案例对齐分"都算不上（expected 多半不是原文明言）。
2. 不能说"六宫释义表对不对"——表既是引擎的断语源，又是考卷的答案源，属循环论证。
3. 不能说"泛化"——n=5 的 holdout，且 3/5 为构造例；无一条独立的"书上原断 + 应验"验证例。
4. 落宫虽然是确定性的，但"落宫对"只说明算术没错，与断事准不准无关。

**建议报法**：
> 小六壬 · `holdout`，n=5（书上原例 2 + 按规则表构造 3），**规则自洽回归：落宫 5/5、
> 吉凶 5/5、事类 5/5、主数 5/5 命中**（n<20 不报百分比，不出具任何"准确率"表述）。

## 六、让读数可检验：最小改动

**本科最该抄六爻的一条**：六爻把外部集（维基文库解析的 35 例）与主库分文件存放，
用 `case_splits.json` 单列成"永不调参"的 split（`liuyao/scripts/case_runner.py:134-153`、
`171-174`）。本库只要新建 `data/cases/external_cases.json`（同一 cases 格式）并在
`case_runner.load_ids` 加一个 `external_holdout` 分支即可，**不动引擎**。
其余可借鉴项（strict/loose 双列、候选集随机基线、名次制防骑墙、N/A 剔除）见
`disciplines/meihua/docs/EVAL-AUDIT.md` §6.0 的对照清单。

### 已做（只动评测集/口径/文档，未动推演逻辑）

1. 逐例 `provenance` + `_meta._provenance` 审计块；XLR101–XLR105 的 `note` 已前置 provenance 说明。
2. `_meta` 计数补登记（`total_cases` 17 / tune 10 / holdout 5 / excluded 2 / provenance 计数）。
3. `evaluate.py`：n<20 显式声明"不发百分比"并打印逐维度命中数；文案明确本读数
   **不是**古籍案例对齐分。
4. `dev_tools/check.py` 基线注释改为"规则自洽回归线"，订正过期 n。
5. 金标准指纹 `0088d638d065402d` 零漂移。

### 建议但未做（按性价比排序）

1. **建外部集**：从《贺氏六壬小手册》其余章节（第四节六宫释义应用、第七节命理篇）逐条录入
   **原文明言吉凶 + 应验结果**的实例，作为 `external_holdout`，只报命中数。这是唯一能
   把"自洽"变成"对齐"的动作。
2. **拆掉循环**：把 `topic` 维度改为"引擎给出的诀句是否被原文/古籍支持"的人工标注，
   而不是"是否等于本仓表"；或至少把 XLR103–XLR105 移出 holdout 报分。
3. **加随机期望基线**：落宫 1/6 = 16.7%，主数表 3 数命中率可算出无信息基线，与命中数并列报出。
4. 均分改信息加权（Σearned/Σapplicable），并把"自洽项得分 / 真判据得分"分列。
