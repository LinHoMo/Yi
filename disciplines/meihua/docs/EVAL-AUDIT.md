# 梅花易数 · 评测口径审计（EVAL-AUDIT）

> 结论针对 `data/cases/meihua_cases.json` + `scripts/evaluate.py` + `scripts/case_runner.py`
> 的**评测设计**，不评判推演逻辑本身。审计日期：仓库 `main`（v0.0.1）。
> 铁律三：本文所有数字都是**古籍案例对齐分**，不是现实预测命中率。
>
> **复核命令**（只读，复现本文每个数字）：
> `python tools/eval_audit_recheck.py`（覆盖三科；A 来源计数 / B 信息加权分 /
> C 梅花数应同义反复 / D 小六壬查表同源 / E 择吉逐字段全等）。

## 一、一句话结论

**tune n=10 / holdout n=13 均为 100%，读不出"更准"。** 该读数由两件事决定：
expected 与引擎**同源**（4 个维度、合计 70/100 权重由起卦数字经卦画+五行生克唯一确定），
以及 holdout 的 5/13 例本身就是**按本仓规则表构造**的校验例。
它证明的是"卦画→体用→生克的管线没被改坏"，即一条**回归线**。

## 二、案例集怎么构造的

| 项 | 值 | 证据 |
|---|---|---|
| case 总数 | 23（+ excluded 2） | `meihua_cases.json:15` 起 `cases`；`_meta.total_cases` |
| tune | 10（MH001–MH010，全为《梅花易数》卷一·观梅占验原文十占） | `meihua_cases.json:48`（MH001）起 |
| holdout | 13（MH011–MH023） | `meihua_cases.json:322`（MH011）起 |
| excluded | 2（MHX1 断法不对齐 / MHX2 无断语） | `meihua_cases.json` 末尾 `excluded` 数组 |
| `expected` 字段填充 | `relation` 23/23、`verdict` 20/23、`ke_ti` 17/23、`sheng_ti` 9/23、`timing` 5/23（全在 tune） | 实测（recheck A/B 段） |
| 计分权重 | relation 30 / verdict 30 / sheng_ti 15 / ke_ti 15 / timing 10 | `evaluate.py:36-42` |

### expected 是"书上的原始结论"还是"反推"？——**分两类，逐例已标 `provenance`**

| provenance | n | 含义 | 证据 |
|---|---|---|---|
| `book_original` | 18 | 起卦数字与吉凶断语均出自原书，`expected.note` 引原文 | MH001–MH013、MH019–MH023 |
| `engine_derived` | 5 | **非原书占验**，expected 按 `verdicts.json#multi_move_rules` 机械推导 | MH014–MH018，`provenance` 见 `meihua_cases.json:424/455/485/515/545` |

**泄漏实锤（关键）**：`multi_move_rules` 规则表与 MH014–MH018 这 5 例在**同一次提交
`010bcee`** 中一起引入（`git show 010bcee:disciplines/meihua/data/verdicts.json` 已含
`multi_move_rules`，而同提交的 cases 已含 MH014；更早的 `aecb832` 两者都没有）。
即"考卷"与"答案表"是同一批产物——这 5 例只能证明引擎实现了自己的规则，不能证明规则对。

**另一处必须点明的口径问题**：MH012/MH013 采自《周易与预测学》（邵伟华，今人实践转写），
不是古籍；MH019–MH023 是卷二/卷三原书应验，属真·原书例。
即 holdout 13 例的真实构成 = 原书应验 8 + 同源构造 5。

## 三、打分构成：逐项标「真判据 / 自洽项」

| 维度 | 权重 | 判定 | 依据 |
|---|---|---|---|
| `relation` | 30 | **自洽项** | 由 `input` 经 `chart.py` 定体用 + `analyze.py::_relation_of` 五行生克唯一确定；expected 与引擎同一算式，实测 23/23 逐字相同 |
| `verdict` | 30 | **真判据（但弱）** | 唯一由引擎自由裁量的维度（`analyze.py::_synthesize` 阈值分档）。弱点：只有吉/平吉/平/平凶/凶 5 档，且"方向一致"即满分（`evaluate.py:86-94`），`平吉` vs `吉` 也算中 |
| `sheng_ti` | 15 | **自洽项** | 生体之卦 = 用/互/变卦中五行生体者，`analyze.py::_interaction` 机械得出 |
| `ke_ti` | 15 | **自洽项** | 同上（克体侧） |
| `timing` | 10 | **自洽项（同义反复）** | expected 数应 = 起卦总数经 `motion` 折算；`analyze.py::_numerical_timing`（行取半/立取全/坐卧加倍）。**实测 5/5 完全相等**：MH006 total=10→5、MH007→17、MH008→21、MH009→10、MH010→10 |

**自洽项合计 70/100。** 缺失字段（`None`/`[]`）按 `evaluate.py:47-49` 记 N/A 并从分母剔除
（`yishu_core/eval.py:88-96`），方向正确，未被算成答对。

> ⚠ **平均分口径偏乐观**：`eval.py:63-64` 对**每例百分比**取算术平均。MH003 只有 45/100
> 权重适用（其余 N/A），它拿 100% 与 MH007 的 100/100 在均分里等权 → 有效信息被稀释后
> 仍显示 100%。实测适用权重：tune 800/1000（N/A 占 20.0%）、holdout 930/1300（N/A 占 28.5%）。
> 信息加权分同为 100.0，故本例中未造成数字差异，但口径本身应记为已知偏差。

## 四、tune / holdout 切分方式

- **人工指定**，不是随机切分：逐例 `"split"` 字段，`case_runner.load_ids` 按该字段过滤
  （`case_runner.py:37-40`），无随机种子、无哈希分层。
- 无 ID 重叠；**无任何重叠检查机制**（卦象确实重复：MH002/MH003/MH006 同为姤、
  MH001/MH010 同为用克体兑离）。
- **存在"规则表知识写进代码/数据"**：见 §二 的 `010bcee` 证据。这是本集唯一的硬泄漏。
- 另有一处文档过期：`dev_tools/check.py` 原写 holdout n=8，实际 n=13（本次已订正）。

## 五、诚实呈现口径（结论）

**能说明**：体用分侧、五行生克、互变取象、数应折算这条管线在 10+13 例上与《梅花易数》
观梅占验十占的要点**逐项吻合**，且金标准指纹 `2c9c810d8a265180` 未漂移——可作为
**结构回归的证据**。

**不能说明**：
1. 不能说"预测准确率 100%"——评测的是与案例要点的对齐度（铁律三）。
2. 不能说"泛化能力强"——23 例全部来自同一部书的同一章（卷一·观梅占验 10 例 + 卷二/卷三 5 例
   + 今人转写 2 例 + 构造 5 例），没有外部盲集。
3. 不能说"引擎判断力被验证"——70/100 权重是自洽项；唯一真判据 `verdict` 只有 5 档。
4. n=10/13 < 20，**百分比是伪精度**。

**建议报法**：
> 梅花易数 · `holdout`，n=13（原书应验 8 + 引擎口径构造 5），**古籍案例对齐分：全维度命中
> 13/13、11/11、6/6、8/8**（n<20 不报百分比）；其中 relation/sheng_ti/ke_ti/timing
> 为自洽项（70/100 权重），不构成泛化证据。

## 六、让读数可检验：最小改动

### 6.0 六爻有什么、本科缺什么（可借鉴清单）

| 六爻的评测设计 | 证据 | 三科现状 |
|---|---|---|
| **外部独立集**（wikisource 35 例，从维基文库原文解析，非本仓构造） | `liuyao/scripts/case_runner.py:134-153` `load_cases()` glob `*_cases.json`；`data/cases/case_splits.json` 单列 `wikisource_holdout`，注释"永不参与调参" | ❌ 三科全部只有本仓构造集 |
| **strict / loose 双列** | `liuyao/scripts/evaluate.py:277-372` `score_yingqi_loose`；`:533-537` 同批输出 strict+legacy | ❌ 单列 |
| **候选集大小 + 随机期望基线** | `evaluate.py:391-482` `yingqi_discrimination()`：`avg_candidate_set_size`、`random_full_coverage_expectancy`、`avg_rank_of_correct`、`by_unit` | ❌ 无 |
| **名次制（防骑墙）** | `evaluate.py:232-269`：top-1 满分 / 第 2 位 0.8 / 前 4 位 0.55 / 仅在依据句出现 0.35 | ⚠ 梅花/小六壬用集合命中（含半中 0.66），比六爻宽松 |
| **N/A 剔除**（两模型对照，显式说明 legacy 是历史 100% 的产物） | `evaluate.py:139-143`、`175-176`、`197`；`yishu_core/eval.py:10-12` | ✅ 已有（`eval.py:88-96`），但未做 legacy 对照 |
| **外部集字段诚实降级**：全库 117 例中 `detail` 117、`verdict` 96、`yingqi` 81，而 `key_points` 42、`use_god_position` **仅 3** → 缺失即 N/A，不硬填 | 实测；`docs/DEEP-DIVE-PLAN.md:57-58` | ✅ 口径一致；但三科是"整例 N/A"而非"整维 N/A"，信息量更少 |

**本科最该抄的一条**：六爻用 `load_cases()` 把外部集与主库合并、再用 `case_splits.json`
把外部集单列成"永不调参"的 split。三科只要新建一个 `data/cases/external_cases.json`
（格式与本科 cases 相同）并在 `case_runner` 里加同名 split，就能落地外部集，
**不必改推演逻辑**。

### 6.1 已做（只动评测集/口径/文档，未动推演逻辑）

1. 逐例 `provenance` 字段 + `_meta._provenance` 审计块（`meihua_cases.json:14`）→
   报分时自动披露集合名 / n / 调参状态 / 自洽项 / 泄漏。
2. `_meta` 计数订正（`total_cases` 25→23；`holdout` 核实为 13）。
3. `evaluate.py`：n<20 显式声明"不发百分比"并打印逐维度命中数。
4. `dev_tools/check.py` 基线注释改为"规则表自洽回归线"，并订正过期 n。
5. 金标准指纹 `2c9c810d8a265180` 零漂移（评测层改动未触及引擎行为）。

### 6.2 建议但未做（按性价比排序）

1. **扩外部集**：把《梅花易数》卷二/卷三其余应验例（心易占卜、三要十应）逐条录入独立
   `external_holdout`，只报命中数——这是唯一能真正提高可信度的动作。
2. **降 verdict 的粒度依赖**：把"方向一致"拆成"方向 + 强弱档"两级命中，避免 `平吉/吉` 白送分。
3. **拆掉 MH014–MH018 的自洽环**：把这 5 例改判为 `regression` 集（不进 holdout 报分），
   或为其补一条**不来自本仓规则表**的古籍依据再入 holdout。
4. 均分改为**信息加权**（Σearned/Σapplicable），消除 N/A 稀释，并在报告里同时给出。
