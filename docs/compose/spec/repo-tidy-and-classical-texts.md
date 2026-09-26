---
feature: repo-tidy-and-classical-texts
status: delivered
updated: 2026-09-26
branch: chore/repo-tidy
commits: 0fb5590..(uncommitted working tree on this base)
---

# 仓库整洁 + classical_rules 断语外置

## Report

**What was built** — 仓库去掉了三块死代码（`factor_waterfall`/`engine_legacy`/`hallucination_guard`）与绕开四段契约的 `mei_hua`/`quick`/`batch`/`verify` CLI 模式；`visualization` 从近千行可视化引擎收敛为 render 仍依赖的 SVG 卦盘。过期研究稿（`precision_gaps`/`regression_failure_analysis`/`open_source_research`）删除；`YI-PLAN`/`LIUYAO-PLAN` 收为路线表；双 HANDOFF 合并至根 `docs/HANDOFF.md`。`classical_rules` 的 51 条可交付断语外置到 `verdict_texts.json#classical_rules_notes`，经 `ctext()` 加载，文本一字未改。

**Verification** — 根 `python tools/check.py --full` PASS（含黑箱回归 13/18）；六爻 `python tools/check.py` PASS（金标准 `65e8331c80c4f06a`；tune 93.9/58.8%；holdout 85.7/50%；回归 13/18）。评审发现的 Py3.10 嵌套 f-string 已修（`ctext('…')` 单引号）并复验通过。

**Journey log** — 外置时先按「含中文常量」全量抽取会把拼接碎片（`局，位置`）误收，改为只收 summary/reasons 上下文完整句后收敛到 51 条。`visualization` 的 `_load_hexagram_data` 等看似要保留，AST 调用图证明仅 `generate_hexagram_diagram` 被 render 消费，可整文件收敛。金标准指纹不含 narrate 文案，但本次是等值搬家，指纹与对齐分零漂移正好作证。评审抓到 PEP 701 嵌套引号——外置时用 `ctext("…")` 塞进 `f"…"` 在 3.10 会炸，单引号参数可解。

## [S1] Problem

仓库经过多轮冲刺后留下三类垃圾：

1. **死代码**：`factor_waterfall.py` 语法已坏且零调用；`engine_legacy.py` 的 `mei_hua`/`quick`/`batch` 旧 CLI 模式绕开四段契约（且 `mei_hua` 越界进梅花学科）；`hallucination_guard.py` 仅被 `engine_legacy` 引用；`visualization.py` 里 9 个生成器中仅 `generate_hexagram_diagram` 仍被 `render.py` 使用，其余为旧报告引擎残骸，并残留指向已不存在的 `skills/liu-yao` 回退路径。
2. **过期文档**：`precision_gaps.md` / `regression_failure_analysis.md` / `open_source_research.md` 无任何代码引用，所述缺口多半已修或已否证；`LIUYAO-PLAN.md` / `YI-PLAN.md` 是过程日志式长文，与 HANDOFF/CHANGELOG 职责重叠且多处描述的是「当时的问题」而非现状；双 HANDOFF 有交叉重复。
3. **handoff 未完项**：`classical_rules.py` 仍有大量中文断语字面量未走 `note_text()` 外置到 `data/rules/verdict_texts.json`（HANDOFF 欠项 2），文案搬家与口径审计困难。

另：已合并的 worktree `feat/opt234`、`feat/skills-maturity` 仍在磁盘上，可清。

## [S2] Design

### 2.1 死代码删除边界（只删无行为贡献者）

| 对象 | 动作 | 理由 |
|---|---|---|
| `scripts/factor_waterfall.py` | 删除 | 语法错误（U+FF08 导致无法 parse），零调用；文档中的历史说明保留在 CHANGELOG |
| `scripts/hallucination_guard.py` | 删除 | 仅被 `engine_legacy` import |
| `scripts/engine_legacy.py` | 删除 | 整模块为旧 CLI 兼容层 |
| `liuyao_engine.py` 的 `mei_hua`/`quick`/`batch` 模式 | 删除入口与 import | 绕开 chart/analyze/narrate/render；`mei_hua` 应走 `disciplines/meihua`；MCP `quick_reading` 不依赖本路径 |
| `visualization.py` 中无调用方的生成器 | 删除 | 仅保留 `generate_hexagram_diagram` + 其私有助手 + `_load_hexagram_data`/`_get_hex_text`（卦辞所需） |
| `visualization.py` 的 `skills/liu-yao` 回退路径 | 删除 | 指向已不存在的旧布局 |

**禁止删除**：`lunar.py`、`yishu_core/eval.py`、`calendar_check.py`、`ming_tables`/`zeji_tables`、四段契约脚本、质量门脚本。`visualization.generate_hexagram_diagram` 保留（render HTML 依赖）。

删除后 `liuyao_engine.py` 仅保留 `coin|time|number|manual` 四模式（与四段契约的起卦入口一致）。

### 2.2 文档收敛

| 对象 | 动作 |
|---|---|
| `disciplines/liuyao/references/precision_gaps.md` | 删除 |
| `disciplines/liuyao/references/regression_failure_analysis.md` | 删除 |
| `disciplines/liuyao/references/open_source_research.md` | 删除 |
| `docs/LIUYAO-PLAN.md` | 收缩为路线表（保留里程碑与未完成项指针，过程叙事删除） |
| `docs/YI-PLAN.md` | 收缩为路线表（定位/架构要点 + 里程碑状态表） |
| `docs/HANDOFF.md` + `disciplines/liuyao/docs/HANDOFF.md` | 合并为一份现状交接（根 `docs/HANDOFF.md`）：现状读数、怎么跑、还欠什么、口径纪律；六爻细节收进六爻 README/SKILL 或作为附录节，不双写两份「还欠什么」 |
| `docs/CHANGELOG.md` + `disciplines/liuyao/docs/CHANGELOG.md` | **保留双份**（口径变更可追溯），但本轮删除条目不得被误读为历史不存在——只在 HANDOFF/CHANGELOG 增补「删除清单」 |
| `classical-holdout-benchmark.md` 等 compose 旧 spec | 保留（交付审计） |

文档内若引用将删文件，改为「已删除，见 git 历史 / CHANGELOG」一句话，不留死链。

### 2.3 classical_rules 断语外置（handoff 接手）

沿用 `chain_step5` 已建立的模式：

- 断语/判据文案进 `disciplines/liuyao/data/rules/verdict_texts.json`，代码只留算法与键名。
- 访问经 `note_text()`（或与 `chain_verdicts` 同一加载器）；缺键抛错或走显式默认，**不**在 `.py` 里新增第二份字面量。
- 优先外置**完整判语句/可交付断言**（用户可见文案）；纯标签/状态枚举（如「旺」「囚」）可留在代码或进同一 JSON 的 `labels` 段——以「是否进入 narrate/报告」为界。
- **行为不变**：金标准指纹、tune/holdout 对齐分、回归项数不得因文案搬家而漂移（若指纹不含文案则应用 `golden.py capture` 仅在结构变化时；文案外置应零漂移）。
- 只改通用结构；禁止为个案改判。

验收对照：`python tools/check.py` 与 `cd disciplines/liuyao && python tools/check.py` 全绿；`classical_rules.py` 中「可交付断语」类 CJK 字面量显著下降并在注释/数据文件中可追溯。

### 2.4 worktree 清理

删除已合并 worktree：`.worktrees/opt234`、`.worktrees/skills-maturity`（先 `git status` 确认干净）。`repo-tidy` 自身保留到交付结束。

## [S3] Out of Scope

- 不改推演逻辑、应期规则、用神取法、评分口径。
- 不做 wikisource 扩样、病药/星煞进 step5、命科推演（HANDOFF 其余欠项）。
- 不合并双 CHANGELOG，不重写 case_library / classical_synthesis 等古籍参考。
- 不动 `tools/scratch/` 本地一次性脚本（已 gitignore；可顺手清空但不作为验收）。
- 不引入新依赖、不改 CLI 公共契约（除删除已宣布废弃的 `mei_hua`/`quick`/`batch` 模式）。

## Tasks

- [x] T1: 建工作树与规格 — acceptance: `.worktrees/repo-tidy` 上 `chore/repo-tidy` 可工作；本文件入库 (covers: S2)
- [x] T2: 删除死代码并收敛 visualization — acceptance: `factor_waterfall`/`hallucination_guard`/`engine_legacy` 不再被引用；`liuyao_engine --help` 仅 coin/time/number/manual；render HTML 仍出 SVG 卦盘；根+六爻 check 通过 (covers: S2.1)
- [x] T3: 文档删除与收敛 — acceptance: 三份过期研究稿删除；两份 PLAN 收为路线表；HANDOFF 单点现状；文内无死链；CHANGELOG 记删除清单 (covers: S2.2)
- [x] T4: classical_rules 可交付断语外置 — acceptance: 断语入 `verdict_texts.json`；代码无新增字面量；tune/holdout/金标准无行为漂移 (covers: S2.3; depends: T2)
- [x] T5: 清理已合并 worktree — acceptance: `git worktree list` 无 opt234/skills-maturity (covers: S2.4)
- [x] T6: 全量验证与评审 — acceptance: 根 `check --full` 与六爻 `check` 记录在案；独立评审通过或遗留项有据 (covers: S2)
