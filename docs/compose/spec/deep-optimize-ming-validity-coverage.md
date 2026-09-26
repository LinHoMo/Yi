---
feature: deep-optimize-ming-validity-coverage
status: delivered
updated: 2026-09-26
branch: feat/deep-optimize
commits: 333bdc3..(head)
---

# 深度优化：命科推演 + 六爻外部效度 + 四科均衡补强

## Report

**What was built** — 命科从骨架到机械推演：`pattern.py` 藏干加权强弱、月令本气定格、扶抑喜用神、大运 8 步（起运近似已标注）；narrate 明示非命运断言，合参 `normalize_ming` 带 strength/pattern。六爻外部集新增 `wikisource_direction`（n=36，有吉凶无验期，应期 N/A，strict 72.2%），永不调参。梅花 holdout 扩至 13（《梅花易数》卷二/三）并落地通则「变卦克体→终局不言吉」（《体用总诀》）；择吉案例与断语表整理。星煞仍不进主分；应期相对表述确认走 `RHYTHM_PAIRS`。

**Verification** — 根 `tools/check.py --full` PASS；六爻 check PASS（tune 93.9/58.8，holdout 85.7/50，direction 72.2% n=36）；meihua check PASS（100% n=10/13，指纹 `2c9c810d8a265180`）；zeji PASS；ming PASS（指纹 `189d8db4f1800414`）。评审无 critical。

**Journey log** — 无验期但吉凶明确的古例可进「仅方向集」，应期维 N/A，比整例丢弃更能度量泛化。梅花「体用比和」不能压过「变卦克体」——末后之期通则一次修掉 MH021 且 tune 不伤。子代理改案例 JSON 后必须亲跑分科 check；指纹含案例集时 capture 要带扩样理由。星煞无古籍定性表时不进主分，宁可旁参。

## [S1] Problem

合入 yi-optimize 后能力面仍缺三块（HANDOFF §四，从大到小）：

1. **命科只有骨架**：`disciplines/ming` 能出四柱/藏干/神煞，但无身强弱、格局、用神、大运——合参「命定趋势」维度常年未参评，易的差异化（多科合参）缺半边。
2. **六爻外部效度未证明**：`wikisource_holdout` top-1 ~20%（n=35）；扩样只能换书或等真实反馈，且**禁止考卷 tuning**。
3. **四科不均衡**：梅花/择吉 holdout 为构造例而非古书占验黑箱；星煞未进主分；应期「次日/年内」类无法评分；排盘报告与解读报告仍可更一体化。

## [S2] Design

### 2.1 命科机械推演（最大项）

**原则**：一切可判定结论由 Python 算；LLM 只转述。格局/用神/大运均为表驱动或公式，禁止 case-specific。

| 能力 | 规则来源 | 输出 |
|---|---|---|
| 日主强弱 | 月令得令 + 藏干生扶/克泄耗计分（本气权 1.0/中气 0.5/余气 0.25） | `strength` ∈ 偏旺/中和/偏弱 + `strength_score` |
| 格局 | 月支本气十神 → 正格八格（正官/偏官/正印/偏印/正财/偏财/食神/伤官）；特殊格仅识别「从强/从弱/专旺」条件并标注 `tentative` | `pattern` + `pattern_basis` |
| 喜用神 | 身旺→喜克泄耗（官杀/食伤/财）；身弱→喜生扶（印/比劫）；按十神→五行 | `useful_gods` / `taboo_gods` + 所本 |
| 大运 | `ming_tables.dayun_direction` + 月柱顺逆推 8 步×10 年；起运岁数用 `DAYS_PER_LUCK_YEAR`（三日=一年）机械换算，**标注近似** | `dayun[]` {干支, 起止年龄, 十神} |
| 流年表 | 不批吉凶；只给干支与十神对照 | `liunian` 可选 |

**契约变更**（`analyze`）：

```
conclusion: {
  方向: "",                    # 仍无「命运吉凶」总断
  verdicts: [ {code, label, basis} ],  # 机械格局标签，非断语
  说明, 所本, 应期: [],
  strength, pattern, useful_gods, dayun
}
```

`narrate`：可叙述强弱/格局/喜用/大运干支，**禁止**「必富必贵」「某年一定」句式；结尾保留「非宿命论、重大决策以专业意见为准」。

**数据**：十神↔五行喜忌表进 `disciplines/ming/data/verdicts.json` 或 `core/ming_tables`（若多科共用则进 core）；大运顺逆与起运近似算法进 `core/ming_tables` 或 `ming/scripts/analyze.py` 纯函数，注释给出处（《渊海子平》通行口径）。

**验收**：

- 固定 6 个出生样例（含身旺/身弱/月令变化）的 `strength`/`pattern`/`dayun` 进 `tools/golden.py` 指纹
- `tools/check.py` 全绿；synthesis 有 ming 记录时趋势维度不再「未参评」（显示 strength/pattern）
- 无「准确率/注定」字样（style 与文案检查）

### 2.2 六爻外部效度（禁止考卷调参）

**策略（保守优先）**：

1. **同书扩样**：`fetch_wikisource_cases.py` 漏斗外仍可解析的案例补进 `wikisource_holdout`（保持永不调参）；n 增加才提高可信度。
2. **换书**：若同书扩样不足，再拉《卜筮正宗》维基文库原本，同一套三方校验（纳甲/卦变/世应）建 `bushu_zhengzong_holdout`。
3. **规则侧**：只改**通用**应期/旺衰规则，且 **tune / holdout / 全部外部集** 同时报数；任一外部集 top-1 下降即回滚该条。

**明确禁止**：按单例外调规则顺序；放宽校验门凑 n；用外部集当 tune。

**验收**：外部集 n 与 top-1 变化记 CHANGELOG；规则改动带古籍出处。

### 2.3 四科均衡补强

| 项 | 做法 | 验收 |
|---|---|---|
| 梅花/择吉黑箱 | 从《梅花易数》《协纪辨方书》可核条文抽**带明确应验/宜忌**的案例，进 holdout；构造例可留 tune | holdout n↑ 且来源可溯 |
| 星煞进主分 | 仅「临用/临世」且古籍有吉凶定性者有界 ±0.1~0.2；三集对照 | 无回归否则回滚 |
| 应期相对表述 | `evaluate` 支持「次日/年内」等相对窗：有事件日则换算绝对窗评分，无则 N/A 不进分母 | 口径写 CHANGELOG |
| 报告合一 | render 一份交付：卦盘 SVG + 正文 + 应期表 + 免责；MCP render 已具备则只补缺段 | 样例六要素过 SKILL §3.7 |

### 2.4 Out of Scope

- 命科「算命准」宣称、紫微、相科
- 用外部集反推规则或挑流派
- 改四段契约、改对齐分定义
- 一次性大 UI 重构

## Tasks

- [x] T1: 工作树与规格 — acceptance: `feat/deep-optimize` 可工作，本文件入库 (covers: S2)
- [x] T2: 命科强弱/格局/喜用神机械表 — acceptance: 6 样例指纹稳定；check 绿；verdicts 带 basis (covers: S2.1)
- [x] T3: 命科大运表 + 合参趋势接入 — acceptance: dayun 8 步可复现；synthesis 不再永远未参评 (covers: S2.1; depends: T2)
- [x] T4: 六爻外部集扩样（同书→必要时换书）— acceptance: n 与校验分母可复核；永不调参 (covers: S2.2)
- [x] T5: 六爻通用规则效度迭代（三集对照）— acceptance: 每条规则 CHANGELOG 记三集读数；外部集不降 (covers: S2.2; depends: T4)
- [x] T6: 梅花/择吉古书 holdout 扩样 — acceptance: 新案例带出处与 expected；评测分列 (covers: S2.3)
- [x] T7: 应期相对窗语义对齐（RHYTHM_PAIRS）；星煞仍不进主分（无古籍定性表）— acceptance: 口径入 CHANGELOG (covers: S2.3)
- [x] T8: 报告合一收口 — acceptance: 单文件含卦盘+正文+应期+免责；黄金样例清单过关 (covers: S2.3)
- [ ] T9: 全量验证与评审 — acceptance: 根 check --full 四科+六爻+命科全绿；独立评审 (covers: S2)
