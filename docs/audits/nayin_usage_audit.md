# 纳音使用审计报告

- 对应 OPT：**OPT-shenfeng_tongkao_dz-02**（纳音使用审计——与本书批判立场的兼容性）
- 审计脚本：`tools/audit_nayin_usage.py`（可复跑，**只读**；2026-10-08 由
  `disciplines/ming/dev_tools/` 移出——本脚本的反事实探针同时 import 六爻与命科两科模块，
  留在学科目录内即构成 ming→liuyao 反向依赖，违反 AGENTS.md §二 依赖方向单向）
- 复跑命令：`python tools/audit_nayin_usage.py`（EXIT=0 为通过）
- 审计日期：2026-10-07（**2026-10-09 在 HEAD `60b2403` 复跑并订正本文件的过期记载**）
- 审计前读数：liuyao tune strict 96.8%／legacy 99.7%、holdout strict 90.2%／legacy 92.9%；
  ming tune 100.0%／holdout 96.2%；（历史）meihua/zeji/xiaoliuren 均 100.0%——
  **该三科读数已于 2026-10-09 随整科删除失去载体，不得再引用**

## 一、审计要回答的问题

《神峰通考》对纳音持**批判立场**（本书通篇以月令用神为主，纳音只作旁参甚至贬为妄说）。
本项目 `core/yishu_core/symbols.py` 收了 `NAYIN`／`NAYIN_TO_ELEMENT` 全表，
故必须证明一件事：

> **纳音在引擎中只作「排盘取值」与「叙述取象」层，不参与任何吉凶判断。**

否则即与本书立场冲突，且违反 AGENTS.md 铁律一（吉凶断语不得进结构层）。

## 二、方法：静态分类 + 动态反事实（双向证据）

### 2.1 静态分类

扫描全仓 `*.py`（排除 `.git`／`__pycache__`／`site`／`modernized`／`archive`／
`node_modules`／`scratch` 与脚本自身），凡命中 `nayin`／`NAYIN` 的行按上下文分三类：

| 类 | 判据 | 命中（**2026-10-09 实跑现值**；括号为 2026-10-07 八科时点原记） |
|---|---|---|
| **A 排盘取值** | 取名、安星、渲染字段，无结论性字段同现 | 53（原 80） |
| **B 叙述层** | 与 `description`／`narrate`／`append`／`str(` 同现 | 6（原 8） |
| **C 判据层（红线）** | 与 `final_score`／`score`／`verdict`／`strength_score`／`useful`／`taboo`／`bias`／`weight` 等**结论性字段同现** | **0**（原 0） |
| 注释/文档 | 行首为 `#` 或引号开头 | 14（原 30） |
| `nayin`/`NAYIN` 命中行合计 | — | **73**（原 118） |

**结论：判据层消费 0 处——2026-10-09 在新 HEAD 复跑 `python tools/audit_nayin_usage.py` 仍为 0。**
复现即上面那条命令（EXIT=0 为通过；脚本自带注入生效负例，见 §2.2）。
计数下降的原因不是判据层变严，而是**六科代码随 2026-10-09 范围收缩整片删除**，
被扫的 `*.py` 总数变小（原表还包含 ziwei/liuren/meihua/zeji/xiaoliuren/lingqi 六科的消费点）。

> 逐文件消费点计数**不在本文复述**：审计脚本不输出该项，旧版手抄的 17 行清单
> （`pattern.py` 16 点／`symbols.py` 11 点…）已与现树不符，删除并改为指针——
> 需要时按 `python tools/audit_nayin_usage.py` 的分类计数 + `git grep -n "nayin\|NAYIN"` 现算。

### 2.2 动态反事实（**带负例自证**）

静态分类可能漏（纳音可能经中间变量间接进判定），故再做动态验证：
在子进程内把 `core.symbols.NAYIN` **整表替换为伪值**（每个值前置「伪」），
并重绑 `nayin_of` 到 `relations`／`shensha`／`ming_tables` 三个已 `from-import` 的模块，
然后跑完整 `tools/eval.py`，比对两科读数。

**负例自证（铁律四.5：注入必须自证生效，否则「读数不变」是假证据）**：

```json
{"gz": "甲午",
 "core_before": "沙中金",  "core_after": "伪沙中金",
 "chart_before": "沙中金", "chart_after": "伪沙中金",
 "injection_effective": true}
```

⇒ 注入**确实生效**（core 与学科层都看到伪值），不是「改了没生效所以读数不变」。

**读数对照（baseline vs 整表伪值）**：

| 科 · split | baseline | NAYIN 全表伪值 | 差异 |
|---|---|---|---|
| liuyao tune strict | 96.8% | 96.8% | 0 |

### 2026-10-09f 纳音取象接线

**状态**：`nayin_quxiang.json`（《五行精纪》纳音性质名，56 柱 → 171 叶）已在 `disciplines/ming/scripts/narrate.py` 接线（2026-10-09f）。

**接线方式**：narrate 层加载 → 每柱按干支查表得性质名 → 输出「纳音取象」段落。性质名只作物性分类标签旁证，不进 analyze/chart/pattern，不计格，不参与任何评分。

**铁律一合规**：依然合规——纳音取象格层 §二「只作旁证展示」已落地，不在结构层计分；判据层（pattern.py 格局判定、evaluate.py 评分）零消费（C 类 0 命中，与接线前一致）。

**金标准重基线**：机械层零漂移（1be8d5b579463a47）；措辞层哈希从 7d3ddb40bbc74f42 → 568e5bedc0d60500（因 narrate 输出新增纳音取象段，是有意变更，已在 golden.py 登记理由）。

**回归保护**：`check.py` UNWIRED_CORPORA 已摘除该条目——后续再报它 0 命中即为回归。
| liuyao tune legacy | 99.7% | 99.7% | 0 |
| liuyao holdout strict | 90.2% | 90.2% | 0 |
| liuyao holdout legacy | 92.9% | 92.9% | 0 |
| ming tune strict | 100.0% | 100.0% | 0 |
| ming holdout strict | 96.2% | 96.2% | 0 |

> （历史行，2026-10-09 从表中删去并留此注：`meihua`／`zeji`／`xiaoliuren` 三科 tune/holdout
> strict 各 100.0% / 100.0%、差异 0。三科已于 `60b2403` 整科删除，读数**无载体、不可复现**，
> 留在现值表里会让人以为今天还能跑出"十二项相同"。）

**六项读数逐项相同**（2026-10-09 在 HEAD `60b2403` 复跑确认；原记「十二项」含上述三科已删读数）。
这是**比静态分类更强**的证据：纳音取值即使全错，
对齐分与一致率也**完全不动**，说明它对判定层零影响。

## 三、逐消费点定性（为什么都属 A/B 类）

| 消费点 | 实际用途 | 类 |
|---|---|---|
| `core/yishu_core/symbols.py:512-549` `NAYIN_COUPLETS`（`:512`）／`NAYIN`（`:524`）／`NAYIN_TO_ELEMENT`（`:531`）／`nayin_of`（`:541`） | **表定义本身**（六十甲子纳音名＋五行），只做查表 | A |
| `core/yishu_core/shensha.py:315-316`（表在 `:180`） `TONGZI_NAYIN_TARGETS` | 童子煞按**纳音五行**取候选落点——神煞安星是机械步骤（AGENTS.md 铁律一：吉凶解读不在安星层） | A |
| `core/yishu_core/ming_tables.py:156-157` `ming_gong`／`shen_gong` 的 `nayin` 字段 | 命宫/身宫**排盘字段展示** | A |
| ~~`core/ming_tables.py:367`（函数 `:426`） `NAYIN_XIANGGE`／`nayin_xiangge_matched`~~ **本行原为不实记载，2026-10-09 删除该指认**：`core/yishu_core/ming_tables.py` 全文只有 **312 行**，`:367`／`:426` 物理上不可能存在；`NAYIN_XIANGGE` 与 `nayin_xiangge_matched` **全仓不存在**（`git grep -n "NAYIN_XIANGGE" HEAD -- '*.py'` 只命中 `disciplines/ming/scripts/evaluate.py` 的一条注释；`python -c "from core.yishu_core.ming_tables import NAYIN_XIANGGE"` 实跑 EXIT=1 ImportError）。《兰台妙选》纳音取象格层**目前无实体可消费**，只在 `AGENTS.md` §二 与 `docs/OPT-LEDGER.md` §三 作口径登记（OPT-lantai_miaoxuan_dz-01 待落实） | — （**无消费点，原列 A 类是错的**） |
| ~~core/ziwei_tables.py:193-200~~ | 已移除 | A |
| `ming/scripts/chart.py:51` `"nayin": nayin_of(gz)` | 四柱排盘**字段** | A |
| `ming/scripts/render.py:28` | 排盘**表格渲染列** | A |
| `disciplines/ming/scripts/pattern.py` — **查无 `nayin_quxiang`**（`grep -n nayin_quxiang pattern.py analyze.py` 零命中） | 《五行精纪》**性质名**数据已建（`disciplines/ming/data/nayin_quxiang.json`，56 柱）。**接线已落地 narrate.py**（2026-10-09f，只作物性标签旁证、不进 pattern/analyzer 以遵守铁律一）；pattern.py 按判据分层**不得消费**纳音性质名（不参与格局/喜用判定） | — **(合规 0 命中，非缺口)** |
| `disciplines/ming/scripts/analyze.py` — **查无纳音 verdicts 条目** | 上一条已接 narrate.py；analyze.py 按 AGENTS.md §二 判据分层**不得消费**纳音性质名（不挂进评分） | — **(合规 0 命中，非缺口)** |
| `disciplines/liuyao/scripts/classical_enhancements.py:103` `analyze_nayin` | 四柱纳音 + 日柱纳音五行，返回 `description` 字符串 | B |
| `disciplines/liuyao/scripts/classical_analysis.py:160` | 把上条挂进 `advanced_analysis["nayin"]`（**只挂结构事实，不打分**） | B |
| `disciplines/liuyao/scripts/liuyao_step5.py:271-275, 384, 1462` | 取 `nayin["description"]` → `nayin_desc` → 拼进**叙述文本尾巴** | B |
| `tools/core_selftest.py:68-70` | 断言「甲午纳音＝沙中金」——**表值自检**，非判据 | A |
| `tools/check.py:78` | 唯一真值源门的**扫描模式**（防学科复制 NAYIN；正则在 `:72-90` 的 `GANZHI_SEQ_LITERAL`/同义表名块内） | A |

## 四、结论

1. **纳音在本项目中只承担「排盘取值」与「叙述取象」两种角色**，
   静态判据层消费 **0 处**（2026-10-09f 复跑分类计数 **A 53／B 6／C 0**，另有注释/文档 14）；
   §三 表中命科 `nayin_quxiang` 接线行（pattern/analyze）已**合规移出判据层**——
   2026-10-09f 接线落地 narrate.py 后两处**保持 0 命中**（按 AGENTS.md §二 不得进判据层，
   有意 0 命中非缺口）。与《神峰通考》的批判立场**不冲突**。
2. **动态反事实证明**：把纳音全表替换成伪值后，**六项读数逐项不变**（2026-10-09f 复跑现值；原记「十二项」含三科已删读数），
   且注入已自证生效。这是「纳音不影响任何判定」的最强证据形式。
3. **与本书立场的表述关系**（须写明，避免误读）：本项目**并未采纳**《神峰通考》
   「纳音为妄说」的**断语**，只是**不使用**纳音作判据——这是两件事：
   - 「不用纳音判吉凶」＝ 引擎的**取舍**（本审计证明的）；
   - 「纳音是妄说」＝ 古籍的**价值判断**（本项目不引用、不改写、不据此删表）。
   `symbols.NAYIN` 作为**排盘取象资料**保留，与本书立场并行不悖。
4. **不采取的动作**（明确边界）：
   - **不删** `NAYIN` 表——现行消费方是**童子煞纳音落点、命宫/身宫与四柱排盘的纳音字段、
     六爻 `analyze_nayin` 叙述、2026-10-09f 新增命科 narrate 纳音取象旁证段落**；
     原记此列为「紫微五行局、童子煞、纳音取象格三处」——
     紫微斗数已随 2026-10-09 收缩删除，「纳音取象格」表**从未落地**（见 §三 订正行），
     两处指认均已去掉。但**保留表本身不变**：它是 §三 所列 A 类消费点的底层，
     且删表等于改动内核唯一真值源（`AGENTS.md` §二），需走 §四 全门槛；
   - **不把**纳音接进任何评分/格局/用神路径；
   - **不因**本书批判立场而修改任何纳音取值。

## 五、留底与复跑

- 审计脚本落在仓库级 `tools/audit_nayin_usage.py`（2026-10-08 自命科 `dev_tools/` 移出：
  探针同时 import 两科模块，属跨科审计，不应让学科层互相依赖），只读、可复跑。
- ⚠️ 2026-10-08 复跑时发现本脚本**从未真跑过**：四处 `subprocess.run(..., text=True)`
  未带 `encoding="utf-8"`，在 GBK 控制台下子进程读线程 `UnicodeDecodeError` →
  `r.stdout` 变 `None` → `AttributeError` 崩在 `negative_proof()`。
  已补 `encoding="utf-8", errors="replace"`；现注入自证 `injection_effective: true`、
  六项读数逐项不变（2026-10-09 于 HEAD `60b2403` 复跑；原记「十二项」含三科已删读数）。
  **留痕意义**：一个"自带负例自证"的脚本如果没人跑过，
  它的自证与"文档里写了测试"一样是空头支票（AGENTS.md §四.8 同一病灶）。
- 脚本自带**负例自证**，若将来有人改了 `nayin_of` 的绑定方式导致注入失效，
  脚本会打印 `injection_effective: false` 并 **EXIT=1**，不会给出假通过。
- 本轮**未改动任何引擎表值**；审计前后 liuyao/ming 读数完全一致（见 §2.2 表）。
