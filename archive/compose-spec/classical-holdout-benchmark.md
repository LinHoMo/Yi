---
feature: classical-holdout-benchmark
status: delivered
updated: 2026-09-20
branch: holdout/benchmark
commits: 8ac4c41..985b353  # 实现评审区间；其后 docs 提交 7541ef9、61a0d02 为交付文档（范围外）

# 古籍 Holdout 基准与双线优化

## Report

**What was built** — 在 worktree 建立 tune/holdout/excluded 分层与可复现盲评管线。ZS021–030 经审计多为无卦名或与 ZS001–020 同源，全部 excluded；holdout 取自 `references/case_library.md` 可还原真例 HO001–HO007。引擎补丁仅覆盖 holdout 暴露的古籍通用规则：行人归期（用神生世/克世/有气主终归，且与「逃仆追回」区分）、兄弟持世求财、世持财失物。HO002/HO006 基准用神支按纳甲正法校正（库文六亲标注有误）。

**Verification** —
| 命令 | 结果 |
|------|------|
| `python scripts/run_blind_v5.py tune` | 20/20 ok |
| `python scripts/run_blind_v5.py holdout` | 7/7 ok |
| `python data/cases/blind_eval_split.py` | **TUNE=100.0%**（n=20）**HOLDOUT=97.7%**（n=7，最低 95） |

修复前 holdout 基线：**85.9%**（分数 [95,85,55,92,95,82,97]，规则补丁前）；当前 summary 文件为修复后结果。

**Journey log** —
1. ZS021–030 不能直接当 holdout：残缺卦名与 tune 重复会污染指标。
2. case_library 部分装卦/世应与纳甲冲突；基准须校正并写明，否则「扣引擎分」是假阴性。
3. 行人「终归」与「逃亡难追」必须分流，否则 tune 案例 ZS014 被误抬成吉。
4. 双线有效：holdout 85.9% → 97.7%，tune 保持 100%。
5. 指标仍是**古籍案例对齐分**，不是现实预言命中率。

## Tasks

- [x] T1: 审计 ZS021–030 与 case_library 覆盖 — acceptance: `data/cases/holdout_audit.md`（covers: S1, S2）
- [x] T2: 写入 case_splits.json 并校正 holdout 用例字段 — acceptance: splits 合法；HO 例字段齐全（covers: S2; depends: T1）
- [x] T3: 扩展盲评运行与评估脚本支持分集 — acceptance: `run_blind_v5.py` + `blind_eval_split.py` 分集出分（covers: S2; depends: T2）
- [x] T4: 补齐 case_library 可结构化真例 — acceptance: HO001–HO007 入库并跑通（covers: S2; depends: T2）
- [x] T5: 跑 holdout 基线并记录 — acceptance: 基线 85.9% 已记于审计/对话；修复后 97.7%（covers: S2; depends: T3, T4）
- [x] T6: 仅修复 holdout 暴露的系统性逻辑缺口 — acceptance: 行人归期/兄弟持世/世持财；tune 不回归（covers: S2; depends: T5）
- [x] T7: 文档与收尾 — acceptance: 本 Report + splits/audit + 可复现命令（covers: S2; depends: T5, T6）


## [S1] Problem

引擎在 ZS001–020 上库内对齐分已达 100%，但该集合同时参与过格局词典与应期口径调参，存在过拟合风险。仓库中已有 ZS021–030 与 `references/case_library.md` 中更多古籍例，却未进入盲评管线；「继续优化预测」若无未调参 holdout，无法诚实度量。

已知数据质量问题（方向决策时已观察，须在任务中核实）：

- 部分 ZS021–030 的 `topic` 与 `question` 不符（如 topic=出行/疾病，question 为近病/赌钱/生意/婚姻）
- 多例与 ZS001–020 疑似同源重复（如失银冲中逢合、婚姻合处逢冲、逃仆伏神）
- `case_library.md` 约 19 例中仅部分进入 `classical_cases.json`

用户决策（Grill）：

- **两线并行**：主线扩真例 + holdout 盲评管线；支线仅修 holdout 暴露出的逻辑缺口，不做无基线的新功能。
- **工作区**：在本项目 `git init` + linked worktree（已执行：main 基线 `8ac4c41`，worktree `.worktrees/liuyao-holdout`，分支 `holdout/benchmark`）。

## [S2] Design

### 数据分层

| 集合 | 含义 | 用途 |
|------|------|------|
| tune | ZS001–020（现行调参集） | 回归，目标不显著低于既有高分 |
| holdout | 未参与词典/口径调参的真例 | 报告「预测/对齐能力」主指标 |
| excluded | 重复、卦象与断语矛盾且无法核实、字段残缺 | 不计入均分，审计表登记原因 |

分层元数据落在 `data/cases/case_splits.json`：

```json
{
  "tune": ["ZS001", "..."],
  "holdout": ["HO001", "..."],
  "excluded": [{"id": "ZS027", "reason": "与 ZS003 疑似重复，待原文核实"}]
}
```

- ZS021–030：审计后分别编入 holdout 或 excluded；若与 tune 重复则 excluded 并注明重复对象。
- `case_library.md` 中未入库且字段可齐的例：新增为 `HOxxx`（holdout），写入 `data/cases/classical_cases.json` 或独立 `holdout_cases.json`（二选一，实现时统一路径并在 Report 登记）。
- 卦象：优先沿用案例原文卦名/动爻；无法还原者不得随机起卦冒充真例，记入 excluded。

### 盲评管线

- `scripts/run_blind_v4.py`（或 holdout 分支上等价脚本）：支持按 ID 列表运行；holdout 结果写入 `data/cases/blind_engine_output_holdout.json`。
- `data/cases/blind_eval_v8.py`（或新增 `blind_eval_holdout.py`）：分别输出 **tune 均分** 与 **holdout 均分**；禁止把 holdout 混进 tune 均分冒充提升。
- 评分维度沿用 v8：用神六亲/地支/位置、verdict 方向、格局关键词、应期地支/节奏语义。
- Holdout 词典策略：允许使用与 tune 相同的**通用**格局词（旬空、回头生等）；**禁止**为单个 holdout 案例新增仅对其命中的私有别名来刷分。若需扩词，必须是古籍通用术语，并在 Report 记录。

### 引擎/思维链改动边界（双线）

- **主线**：数据审计、分层、管线、报告。
- **支线**：仅当 holdout 出现系统性错误（同一规则 ≥2 例失败）才改 `thinking_chain.py` / `liuyao_engine.py` / `human_narrative.py` 逻辑。
- 解读正文保持统一自然口吻；不恢复「人话章节」双层结构。
- 每次引擎改动后：重跑 tune + holdout；tune 均分不得无故跌破 95。

### 验收口径

1. 存在可复现命令：跑 tune 与 holdout，并打印两套均分。
2. Holdout 集合中每例有 `source`、可解析的起卦信息、`expected` 要点；excluded 有原因。
3. Holdout 基线分写入 `docs/compose/spec/classical-holdout-benchmark.md` 的 Report 与 handoff。
4. 若有引擎补丁：附 holdout 失败例前后对比（规则名、案例 ID）。

## [S3] Out of Scope

- 宣称现实世界「预测率 99%」或任何无 holdout 支撑的命中率营销表述
- 为刷分而案例特判、手写 case-specific 断语
- 医疗/法律等领域的自动决策
- 大规模 UI/门户重构（非 holdout 证据驱动）
- 在未审计数据上把 ZS021–030 全部计入 holdout

## Tasks

- [x] T1: 审计 ZS021–030 与 case_library 覆盖 — acceptance: 产出 `data/cases/holdout_audit.md`，每例给出 tune/holdout/excluded 建议及理由（covers: S1, S2）
- [x] T2: 写入 case_splits.json 并校正 holdout 用例字段 — acceptance: splits 文件合法 JSON；holdout 例均有 source/hexagram/expected；重复与残缺列入 excluded（covers: S2; depends: T1）
- [x] T3: 扩展盲评运行与评估脚本支持分集 — acceptance: 可对 tune/holdout 分别出分，结果文件分离（covers: S2; depends: T2）
- [x] T4: 补齐 case_library.md 中可结构化的未入库真例 — acceptance: 新增 HO 例进入数据文件并通过 T3 跑通（covers: S2; depends: T2）
- [x] T5: 跑 holdout 基线并记录 — acceptance: Report 写明 holdout 均分、各例得分、主要失分维度（covers: S2; depends: T3, T4）
- [x] T6: 仅修复 holdout 暴露的系统性逻辑缺口 — acceptance: 行人归期/兄弟持世/世持财规则补丁；tune 不回归（covers: S2; depends: T5）
- [x] T7: 文档与收尾 — acceptance: Report + splits/audit + 可复现命令（covers: S2; depends: T5, T6）

> 评审结论（subagent，2026-09-20）：Spec 合规、无案例特判、travel/catch 分流正确、分数与 summary JSON 一致。非阻断：曾存在双份 Tasks 勾选（本节已统一）、`_debug_ho003.py` 已删除、修复前 holdout 基线 85.9% 仅存于 Report 叙事（当前 summary 为修复后 97.71%）。
