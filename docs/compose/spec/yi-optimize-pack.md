---
feature: yi-optimize-pack
status: delivered
updated: 2026-09-26
branch: feat/yi-optimize
commits: 3135c12..(head)
---

# 易优化包：MCP/小缺口 + 断语外置收尾 + 命科骨架 + 病药星煞入 step5

## Report

**What was built** — MCP 补 `liuyao.narrate`/`liuyao.render`（复用四段契约）；新增 `tools/eval.py` 仓库级对齐分入口；删除无引用的 `hexagrams.json`（卦辞真值源在 core）。`classical_rules` 再外置 97 条拼装句模板（`ctpl`）。新建 `disciplines/ming/` M5 骨架：四段契约 + 机械因子，narrate 明示推演未实现，合参 `normalize_ming`。病药结构化码进入 step5 有界加减；药码进应期排序经 holdout 否证后回退。

**Verification** — 根 `tools/check.py --full` PASS（含 ming 质量门、黑箱回归 12/18≥11）；六爻 `tools/check.py` PASS（指纹 `a1a7d34c3532f2f2`；tune 93.9/58.8；holdout 85.7/50；与 26e 基线持平）。命科 `tools/check.py` PASS。

**Journey log** — 药码写入应期主排序会挤掉 holdout 正确日支（top-1 50→37.5），与此前「书序整体重排」同类过拟合，必须三集对照。`ast.get_source_segment` 比手算 offset 可靠，f-string 外置应用源码段替换。命科 chart 需用 `ganzhi_of` 而非不存在的 `get_*_stem_branch`——内核 API 以实际导出为准。

## [S1] Problem

架构扫描与 HANDOFF 欠项对上后，四块可并行推进的缺口：

1. **MCP 工作面不完整**：`mcp_server` 仅 `divinate/quick_reading/validate_hexagram/get_classical_quotes`，缺 narrate 正文与 render 报告导出；SKILL/HANDOFF 已承诺完整交付链。
2. **仓库级命令与承诺不一致**：`AGENTS.md` 写 `tools/ check / eval / demo / install`，实际无 `eval.py`；`data/hexagrams.json` 在 visualization 收敛后已无 Python 消费者，与 `core/hexagram_texts.py` 双源风险仍在文档层。
3. **classical_rules 仍有拼装字面量**：51 条完整句已外置，f-string 模板与片段（约数百条）仍堆在 `.py`。
4. **合参命科常年未参评**：`synthesis` 规则 5 正确降级，但 `disciplines/ming/` 不存在，M5 空转；`person` schema 已预留 `ming`。
5. **病药/星煞只在 analyze/narrate**：`bing_yao_shensha` 已结构化 illness/medicine，未进 step5 加权与应期排序（HANDOFF 欠项 3）。

## [S2] Design

### 2.1 MCP 补 narrate / render（薄适配，不碰推演）

| 方法 | 行为 |
|---|---|
| `liuyao.narrate` | 同 `divinate` 参数 → 返回 `{text, conclusion, use_god_basis}`；内部复用四段契约 `narrate.py` / `human_narrative`，禁止第二套正文 |
| `liuyao.render` | 同参数 + `format=md\|html` → 返回 `{content, format}`；复用 `render.py`，HTML 含 SVG 卦盘 |

与 `list_methods`/api_spec 同步。缺参报错，失败退出码非 0（JSON-RPC error）。

### 2.2 仓库级小缺口

- 新增 `tools/eval.py`：薄封装，转发四科 `scripts/evaluate.py --split …`，打印分集合读数；无第二套评分逻辑（`yishu_core.eval` 唯一）。
- `hexagrams.json`：确认零代码引用后**删除**；`SKILL.md` 查卦辞改为 `core.yishu_core.hexagram_texts`。若必须留数据样例，移 `docs/samples/` 并注明非真值源。
- `AGENTS.md` 工具行与实际对齐（eval 存在或改词）。

### 2.3 classical_rules 拼装句外置（收尾欠项 2）

- f-string 模板进 `verdict_texts.json#classical_rules_templates`，形如 `"fu_emerge_score": "得出评分={score}"`。
- 纯运算符字（`生`/`同`/`处`）、地支五行、docstring **不**外置。
- 文本等值搬家；金标准/对齐分零漂移为验收。

### 2.4 命科骨架 M5（只立契约，不写命理推演）

```
disciplines/ming/
  SKILL.md          # 范围声明：本轮只契约与数据，不断吉凶
  README.md
  references/api_spec.md
  scripts/chart.py  # birth solar/ganzhi → 结构化四柱盘（复用 core.ganzhi_calendar + ming_tables）
  scripts/analyze.py# 输出 {factors, verdicts: [], basis}：仅机械因子（干支/五行/十神表），无断语推演
  scripts/narrate.py# 明示「命科推演未实现」的占位正文
  scripts/render.py # 复用 core/report
  tools/check.py    # 契约完整性 + 冒烟
  data/verdicts.json# 空壳 + _meta 说明
```

- `synthesis/normalize.py` 增加 `normalize_ming`（吃 analyze 契约输出）。
- 合参：有 ming 记录时趋势维度可参评（仍只综合已有因子，不编命运结论）；无则维持未参评。
- **禁止**：四柱格局断语、大运流年推演、任何「准不准」宣称。

### 2.5 病药/星煞进 step5（通用规则，三集对照）

- 位置：`chain_step5` 综合评分/应期排序消费 `evaluate_bing_yao` / `attach_shensha` 的结构化 code。
- 规则（古例通则，非 case-specific）：
  1. **病→药解除优先**：`fill_void`/`heal_break`/`out_of_hiding` 对应应期候选前插（与既有化空/冲开同级，具体优先级以三集读数定，禁止个案微调）
  2. **重病扣分**：`void`+`month_break`+`weak` 同时成立 → 综合分有界扣减（新权重入 CHANGELOG）
  3. **星煞仅旁参**：临用/临世才加减，不进主判定
- **验收**：tune/holdout/wikisource 分列；tune 无故跌破 93.9 即回归；top-1 不劣于现基线（58.8/50）。
- 任一步三集齐跌 → 回滚该条规则并在 CHANGELOG 记否证。

### 2.6 Out of Scope

- 不改纳甲/历法/用神四层/评分公式框架。
- 不做 wikisource 扩样、梅花/择吉古书黑箱、应期相对表述机械评分。
- 命科不写格局断语与大运。

## Tasks

- [x] T1: 工作树与规格 — acceptance: `feat/yi-optimize` 可工作，本文件入库 (covers: S2)
- [x] T2: MCP narrate/render + api_spec 同步 — acceptance: 两条方法可用；正文与 render 同源；list_methods 含新项 (covers: S2.1)
- [x] T3: tools/eval.py + hexagrams.json 双源清理 + AGENTS 对齐 — acceptance: eval 分集合出分；hexagrams.json 不再是第二真值源；文档无死链 (covers: S2.2)
- [x] T4: classical_rules 模板外置 — acceptance: 模板入 JSON；等值；指纹/分数不变 (covers: S2.3)
- [x] T5: disciplines/ming 骨架 + synthesis 接入 — acceptance: 四段契约可跑；合参有/无 ming 路径正确；check 绿 (covers: S2.4)
- [x] T6: 病药/星煞进 step5 — acceptance: 三集分列读数记录；无回归；CHANGELOG 记规则与古籍出处 (covers: S2.5; depends: T4)
- [x] T7: 全量验证与评审 — acceptance: 根 check --full + 四科 + 六爻 check；评审结论 (covers: S2)
