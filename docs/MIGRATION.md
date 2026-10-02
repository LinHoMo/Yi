# 易 v0 → v1 迁移指南

> 本文为从旧版（六爻 58 个脚本、各科学科级独立工具链）迁移到 v1 统一架构的指引。
> v1 已完成——本文档留给后续维护者理解变更全貌。

---

## 一、破坏性变更概览

| 类别 | 变化 | 影响 |
|---|---|---|
| CLI 重设计 | 统一为 `yi <科> <段>` 子命令风格 | 旧参数调用需改 |
| 模块路径 | liuyao 58 脚本合并至 ~32 个 | import 路径可能变化 |
| 文档精简 | 从十余份减至 7 份核心文档 | 部分旧文档已归档 |
| 学科范围 | meihua/xiaoliuren/zeji 归档至 `archive/` | 日常路径不可达 |
| 共享层撤除 | `disciplines/base/`（protocol/cli 基类）2026-10-01 删除（全仓零引用；契约靠 CONTRACT.md + 根 check.py 机械验收） | 新科接入方式见 §3.3 |
| 内功命名拆分 | `ming_tables` 内的纳音/三合/星煞迁出 | 依赖 ming_tables 中这些表的代码需改 import |

---

## 二、用户迁移：CLI 命令对照

### 2.1 六爻

| 用途 | 旧命令（v0） | 新命令（v1） |
|---|---|---|
| 起卦排盘 | `python scripts/chart.py --mode time --datetime "..."` | `python scripts/chart.py --mode time --datetime "..."`（接口不变） |
| 一键闭环 | `python scripts/yi_liuyao.py "所问之事" --when "..."` | 同左（yi_liuyao.py 保留为快捷入口） |
| 推演 | `python scripts/chart.py ... \| python scripts/analyze.py` | `python scripts/analyze.py chart.json -o analyze.json` |
| 正文 | `python scripts/narrate.py --format md --input analyze.json` | `python scripts/narrate.py analyze.json` |
| 报告 | `python scripts/render.py analyze.json -o report.html` | 同左 |
| 评测 | `python scripts/regression_test.py` | `python scripts/evaluate.py --split tune\|holdout` |
| 质量门 | `python tools/check.py` | `python tools/check.py`（统一接口，子检查项调整） |

六爻的四段契约入口（`scripts/chart.py` / `analyze.py` / `narrate.py` / `render.py`）接口保持稳定，合参层消费无需变动。

### 2.2 命科（四柱八字）

| 用途 | 命令 |
|---|---|
| 排盘 | `python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男` |
| 推演 | `python scripts/analyze.py chart.json -o analyze.json` |
| 正文 | `python scripts/narrate.py analyze.json` |
| 报告 | `python scripts/render.py analyze.json -o report.md` |
| 机械回归 | `python tools/regression.py` |

命科无案例对齐评测（`evaluate.py` 不存在），回归走机械因子校验。

### 2.3 仓库级命令

| 用途 | 命令 |
|---|---|
| 快速质量门 | `python tools/check.py` |
| 完整质量门 | `python tools/check.py --full`（+ 评测 + 黑箱 + pytest） |
| 演示 | `python tools/demo.py` |
| 评测汇总 | `python tools/eval.py` |
| 自检 | `python tools/core_selftest.py` |

---

## 三、开发者迁移：Import 路径对照

### 3.1 内核模块（以 `core/` 为包根，pip install -e .）

| 旧引用 | 新引用 |
|---|---|
| `from yishu_core.symbols import ...` | 同左（内核包名不变） |
| `from yishu_core.ming_tables import nayin_element` | ❌ 已移除 → `from yishu_core.symbols import NAYIN_ELEMENT` |
| `from yishu_core.ming_tables import` 星煞相关 | ❌ 已移除 → `from yishu_core.shensha import` |
| `from yishu_core.ming_tables import` 三合相关 | ❌ 已移除 → `from yishu_core.symbols import` |
| `import yishu_core.zeji_tables` | ❌ 已归档至 `archive/yishu_core_zeji_tables.py` |

### 3.2 liuyao scripts

| 旧路径（已删/合并） | 新路径 |
|---|---|
| `from chain_step5 import step5_synthesize` | `from liuyao_engine` 门面（薄聚合入口保留再导出） |
| `from chain_step5_adjust import *` | 通过门面或直引子模块 |
| `from chain_step5_yp_timing import predict_timing_core` | 同左（推荐直引子模块） |
| `from chain_narrate_patterns import _inject_pattern_tags` | 通过 `chain_narrate` 门面再导出 |
| `from human_narrative_segments import _strength_sentence` | 通过 `human_narrative` 门面 |
| `from classical_rules_patterns import ...` | `from classical_analysis` 门面 |
| `from classical_rules_effects import ...` | `from classical_analysis` 门面 |
| `from effects_harmony import ...` | `from effects`（门面合并） |
| `from effects_structure import ...` | `from effects`（门面合并） |
| `from effects_change import ...` | `from effects`（门面合并） |
| `from chain_step5_yp import _predict_timing` | 已拆为 `liuyao_timing.py` |
| `from chain_narrate import _inject_pattern_tags` | 已迁至 `narrative_utils.py` |
| `from human_narrative import _strength_sentence` 等八段素材 | 已迁至 `narrative_utils.py` |
| `import regression_test` | 已移入 `tests/` 目录 |
| `import smoke_test` | 已移入 `tests/` 目录 |
| `from engine_legacy import ...` | ❌ 已删（old CLI 兼容层） |
| `from factor_waterfall import ...` | ❌ 已删 |
| `from hallucination_guard import ...` | ❌ 已删 |

### 3.3 四段契约（新科接入）

> 历史备注：本节原为 `disciplines/base/`（protocol.py 四段 Protocol + cli.py
> DisciplineCLI 基类），因全仓零引用于 2026-10-01 删除（见 `docs/CHANGELOG.md`）。

新学科接入方式（现状）：

1. 按 `docs/CONTRACT.md` 建目录：`SKILL.md` + `scripts/{chart,analyze,narrate,render}.py`
   + `data/verdicts.json` + `dev_tools/{check,golden}.py`（根 `check.py` 结构门核验）；
2. 各段入口脚本自带 argparse（bare 模块互相 import，内核表从 `yishu_core` 取，
   禁止复制/改名复制——内容指纹检测强制）；
3. 在 `cli/main.py` 的 `DISCIPLINE_COMMANDS` 注册命令；
4. golden 回归 + `tools/report_faithfulness.py` 忠实度验收，最后根 `check.py --full` 全绿。

### 3.4 合参层

| 旧路径 | 新路径 |
|---|---|
| `from synthesis.normalize import normalize_liuyao` | 同左（接口不变） |
| `from synthesis.normalize import normalize_ming` | `normalize_ming_ming` 或 `normalize_ming`（支持五科版本含 meihua/xiaoliuren/zeji 归一化） |
| `from synthesis.cross_rules import adjudicate` | 同左（五条裁决规则） |

合参层 `normalize` 在 2026-09-29 还原三科时增加了 `normalize_meihua` / `normalize_xiaoliuren` / `normalize_zeji`，
但当前活动科仅 `liuyao` + `ming`，还原科不影响主路径。

---

## 四、已知兼容层

以下旧入口保留为 deprecated 仍可用，但计划在未来版本移除：

| 入口 | 状态 | 说明 |
|---|---|---|
| `scripts/yi_liuyao.py` | 保留 | 一键闭环快捷命令。内部调用四段契约，可等效替换 |
| `scripts/liuyao_engine.py` | 保留（薄门面） | 再导出子模块聚合入口，不引入新逻辑 |
| `scripts/classical_analysis.py` | 保留（薄门面） | 再导出 classical_* 子模块 |
| `scripts/classical_rules.py` | 已并入 | 门面为 `scripts/classical_analysis.py` |
| `scripts/thinking_chain.py` | 保留 | Step 1-5 推理标记。多处再导出依赖，暂不迁移 |

以上门面类模块均为薄聚合：它们本身不承载推演逻辑，只是 `from xxx import yyy` 的再导出入口。
外部代码引用这些门面不受内部拆分影响，但若直引门面内部的私有辅助函数，可能在某次重构中断链。
推荐直引叶子模块（如 `liuyao_timing.predict_timing_core`）。

---

## 五、流转步骤（给接手者的操作清单）

若要基于当前架构新增学科 `xxx`：

1. `mkdir -p disciplines/xxx/{scripts,data,references,tools}`
2. 编写 `disciplines/xxx/SKILL.md`——只写该科内容，引用 `AGENTS.md` 不复制
3. 编写四段 CLI（`chart.py` / `analyze.py` / `narrate.py` / `render.py`），参考 `disciplines/meihua/scripts/chart.py` 的 argparse 范式
4. 实现四段逻辑，每个判据给出古籍出处
5. 准备案例集：至少 10 例 `tune` + 5 例**未参与调参**的 `holdout`
6. 复用 `yishu_core.eval`，禁止另写评分器
7. 加进 `tools/check.py` 质量门，基线取首次读数
8. 干 tune 与 holdout **分列出分**；tune 无降息跌破基线即回归
9. `grep -r "新科用到的共用表" core/ yishu_confirms`——确认不抄第二份

---

## 六、v1 完成后已知残余

| 项 | 状态 |
|---|---|
| wikisource 应期泛化 top-1 ~20%（n=35） | 阻塞于外部数据，禁止考卷调参 |
| 命科从格判定 | tentative，有意保持（AGENTS.md 铁律三） |
| 报告「格局详释」依赖案例触发 | 非缺陷 |
| 断语残句 | 已确认多为 argparse help/夹具文本，暂不动 |
| 五科全通路 | meihua/xiaoliuren/zeji 已归档于 `archive/`，需时还原 |
