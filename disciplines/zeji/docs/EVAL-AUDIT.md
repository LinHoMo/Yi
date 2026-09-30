# 择吉 · 评测口径审计（EVAL-AUDIT）

> 结论针对 `data/cases/zeji_cases.json` + `scripts/evaluate.py` + `scripts/case_runner.py`
> 的**评测设计**，不评判推演逻辑本身。铁律三：本文所有数字都是**机械因子 + 规则表自洽回归数**，
> 不是古籍案例对齐分，更不是现实预测命中率。
>
> **复核命令**（只读）：`python tools/eval_audit_recheck.py`
> （E 段即本文 §一 的 16/16 逐字段全等实测）。

## 一、一句话结论

**tune n=10 / holdout n=6 均为 100%，这个 100% 是"可确定性复算"的必然结果。**
六个计分维度（合计 100/100 权重）的 expected 全部可由引擎复算：
建除/日值神/黄道/值宿来自内核同一组历法函数，宜忌/综合方向来自本仓 `verdicts.json`。
**审计实测：16/16 例 expected 与 `analyze()` 输出逐字段全等。**
它等价于一次带断言的回归测试，**不是**择吉能力的证据。

## 二、案例集怎么构造的

| 项 | 值 | 证据 |
|---|---|---|
| case 总数 | 18（+ excluded 2 = ZJ016/ZJ017 超出农历表范围） | `_meta.total_cases`；逐例 `split` |
| tune | 10（ZJ001–ZJ010，2026-09-21~30） | 逐例 `split` |
| holdout | 6（ZJ011–ZJ015 为 2026-10-01~15；ZJ022 为 10-09） | 逐例 `split` |
| **古籍日例应验** | **0 例** | 见下 |
| `expected` 字段填充 | `jian_chu`/`day_god`/`huang_dao`/`xiu`/`yi_hit`/`ji_hit`/`verdict` 16/16 全填 | 逐例 `expected` |
| 计分权重 | jian_chu 20 / day_god 20 / huang_dao 10 / xiu 20 / yi_ji 15 / verdict 15 | `evaluate.py:36-43` |

### expected 是"书上的原始结论"还是"反推"？——**逐例 `provenance` 统一为 `engine_derived`**

本库**没有一条古籍日例应验**，文件自己写明了这一点：

> `zeji_cases.json:412` `"expansion_path": "仓库内暂无带日期的古籍宜忌应验全文；holdout 为
> 「机械因子 × 建除/黄黑道/星宿宜忌表」规则应用黑箱，期望独立于 analyze。"`

这句"期望独立于 analyze"**只对代码成立，对数据不成立**：expected 与 `analyze()` 读的是
同一份 `core/yishu_core/zeji_tables.py` 与同一份 `data/verdicts.json`。证据：

- `chart.py:91-93` 建除/日值神/黄道/值宿四项全部来自 `zeji_tables`
  （`jian_chu_of` / `day_god_of` / `is_huang_dao` / `xiuxiu_of`），expected 的这四项与之一字不差。
- `analyze.py:101-106` 宜忌命中 = 活动在 `VERDICTS["jian_chu"][神]["宜"/"忌"]`、
  `VERDICTS["huang_hei_dao"][神]["宜"]`、`VERDICTS["xiu"]["吉宿"/"凶宿"]` 中的落点；
  expected 的 `yi_hit` / `ji_hit` 是同一查表。
- `analyze.py:129-151` 综合方向按 `VERDICTS["verdict_rule"]["thresholds"]` 裁决；
  expected 的 `verdict` 是同一阈值的输出。

`ZJ022`（`zeji_cases.json:390`）的 note 自述"补齐建除「破」覆盖。期望由 verdicts.json
宜忌表+verdict_rule 独立推出，不读 analyze 输出"（`:409`）——独立于 analyze 的**代码**，
但不独立于**同一份表**。

**泄漏实锤**：`git log` 显示 cases 与 `verdicts.json` 在 `1b93b10`/`010bcee`/`878d193`/`b86e4b7`
**同批提交中共同演进**；tune（9 月）与 holdout（10 月）由同一作者在同一次开发中取自
同一套表——属"同源同期"，不是独立情境抽样。且 `dev_tools/check.py` 注释原写 holdout n=5，
实际 n=6（含后补的 ZJ022），说明 holdout 是**开发中反复追加**的。

## 三、打分构成：逐项标「真判据 / 自洽项」

| 维度 | 权重 | 判定 | 依据 |
|---|---|---|---|
| `jian_chu` | 20 | **自洽项（历法真值）** | `chart.py:91` `jian_chu_of(月建, 日支)`；同函数算两遍。随机基线 12 选 1 = 8.3% |
| `day_god` | 20 | **自洽项（历法真值）** | `chart.py:92` `day_god_of()`；随机基线 8.3% |
| `huang_dao` | 10 | **自洽项（历法真值）** | `chart.py:93` `is_huang_dao(day_god)`——即 `day_god` 的布尔投影，与前一项**同源冗余**。随机基线 50% |
| `xiu` | 20 | **自洽项（历法真值）** | `chart.py:93` `xiuxiu_of(d)` 固定序循环；随机基线 28 选 1 = 3.6% |
| `yi_ji` | 15 | **自洽项（查表）** | `analyze.py:101-106` 查 `verdicts.json` 宜忌表；expected 同表 |
| `verdict` | 15 | **自洽项（查表+阈值）** | `analyze.py:129-151` 按 `verdict_rule` 阈值；expected 同阈值 |

**自洽项合计 100/100。** 缺失字段处理：本集 16 例 `expected` 无 N/A，故 N/A 机制未起作用
（`evaluate.py:81-90` 的 `yi_ji` 半中给 0.5 分逻辑亦未触发）。适用权重 tune 1000/1000、
holdout 600/600。

> ⚠ 冗余项提示：`huang_dao`（10 分）与 `day_god`（20 分）是同一个量的两种写法，
> 合计 30/100 权重实际只考一件事（已记入 `_meta._provenance.self_consistent_note`）。
> 另有 `score` 字段存在于 expected 中但**未参与打分**（`evaluate.py` 无 `score` 维度）。

## 四、tune / holdout 切分方式

- **人工指定**：逐例 `"split"` 字段，`case_runner.py:37-40` 过滤。
- 无 ID 重叠、无日期重叠。**但答案表完全重叠**（同一份 `zeji_tables` + `verdicts.json`），
  且两集同源同期（见 §二）。
- 唯一的**真外部核对**发生在开发期的三个锚点：`chart.py:115-125` `_selfcheck()`
  断言 2026-09-23/24/25 与通书一致。这个核对有价值，但它不在评测分数里——
  **分数里看不到它的贡献，因为它已被吸收进 expected 的写法**。

## 五、诚实呈现口径（结论）

**能说明**：
1. `jian_chu`/`day_god`/`huang_dao`/`xiu` 四项历法推算在 2026-09-21~10-15 的 16 个日期上
   与开发期核对过的通书口径**自洽**（历法表未被改坏）。
2. `verdicts.json` 的宜忌表与裁决阈值被一致地实现，`analyze` 输出可复现。
3. 金标准指纹 `9e206e9a93aa3cf3` 未漂移。

**不能说明**：
1. 不能说"择吉准确率 100%""择日如神"——expected 由引擎复算，属循环论证。
2. 不能说"宜忌表对"——表既是引擎的判据源，又是考卷的答案源。
3. 不能说"泛化到别的日期/事类"——只覆盖 2026 年 9–10 月的 16 个日期、7 个事类
   （嫁娶/开市/纳财/安葬/出行/祭祀/动土）；无古籍日例应验，无真实用事结果。
4. 不能说"与多家在线黄历核对"——那只发生在开发期少数锚点，不是本集的读数。

**建议报法**：
> 择吉 · `holdout`，n=6（古籍日例应验 0，全部为机械因子 + 规则表构造），
> **自洽回归：建除 6/6、日值神 6/6、黄道 6/6、值宿 6/6、宜忌 6/6、方向 6/6 命中**
> （n<20 不报百分比，不出具"准确率"表述）。历法层另有开发期通书锚点 3 天。

## 六、让读数可检验：最小改动

**本科最该抄六爻的一条**：六爻把外部集（维基文库解析的 35 例）与主库分文件存放，
用 `case_splits.json` 单列成"永不调参"的 split（`liuyao/scripts/case_runner.py:134-153`、
`171-174`）；且外部集字段缺失时诚实记 N/A（实测全库 `use_god_position` 仅 3/117）。
本库只要新建 `data/cases/external_cases.json` 并在 `case_runner.load_ids` 加一个
`external_holdout` 分支即可，**不动引擎**。其余可借鉴项（strict/loose 双列、
候选集随机基线、名次制防骑墙、N/A 剔除）见 `disciplines/meihua/docs/EVAL-AUDIT.md` §6.0。

### 已做（只动评测集/口径/文档，未动推演逻辑）

1. 逐例 `provenance="engine_derived"` + `_meta._provenance` 审计块
   （含"16/16 逐字段全等"实测结论）。
2. `_meta` 计数补登记（`total_cases` 18 / tune 10 / holdout 6 / excluded 2）。
3. `evaluate.py`：n<20 显式声明"不发百分比"并打印逐维度命中数；文案明确本读数
   **不是**古籍案例对齐分。
4. `dev_tools/check.py` 基线注释改为"历法表+规则表自洽回归线"，订正过期 n（5→6）。
5. 金标准指纹 `9e206e9a93aa3cf3` 零漂移。

### 建议但未做（按性价比排序）

1. **建外部集（最关键）**：录入有日期的古籍宜忌应验（如《协纪辨方书》所引日例、
   《象吉通书》《鳌头通书》的用事验例），作为 `external_holdout`，只报命中数；
   在此之前不宜对外给出任何"对齐分"。
2. **扩历法锚点**：把 `chart.py::_selfcheck` 的 3 天扩到跨 12 个月、覆盖 12 建除与 28 宿的
   锚点表（人工逐日核对），作为独立于引擎的**真判据**计入评分——这是本科最划算的改动。
3. **去冗余**：`huang_dao` 与 `day_god` 合并为一维，腾出的权重给历法锚点核对。
4. 均分改信息加权（Σearned/Σapplicable），并报出随机期望基线（8.3%/8.3%/50%/3.6%）。
