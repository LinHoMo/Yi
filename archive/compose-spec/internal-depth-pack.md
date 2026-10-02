---
feature: internal-depth-pack
status: delivered
updated: 2026-09-26
branch: feat/internal-depth-pack
commits: f4645c3..HEAD
---

# 内部深度包：断语收尾 + 巨石再拆 + 单测 + MCP 四科 + 应期分列 + 命科交互

## Report

**What was built** — 断语外置覆盖 meihua/xiaoliuren/zeji narrate 短语与六爻 `engine_format_labels`/`advice_soft`/`narrate_shell`；`classical_rules_effects` 拆为 harmony/structure/change 三文件加门面（金标准零漂移）。新增 `tests/` 五套件 76 断言并挂 `check --full`。`tools/mcp_router.py` 与四科 `mcp_server` 提供 chart/analyze/narrate/render/list_methods。`evaluate` 输出应期 `yingqi_day/month/year` 分列。命科 `dayun_liunian_interactions` 机械对照（core 三合表），narrate 可展示，6 样例单测覆盖。

**Verification** — `python -m pytest tests -q` 76 passed；`python tools/check.py --full` PASS；六爻金标准 `5c6e77ee253b0ddd` 零漂移；命科 `3d4ff149ef6be933` 不变；tune 93.9 / holdout 87.5。

**Journey log** —
1. 模板里写 `{rel or '他爻'}` 会被 format 当字段名，HO011/HO012 直接炸；占位符与 Python 表达式必须分离。
2. `chain_narrate` 按函数拆分会碰到模块级常量与循环引用；为零漂移已回退，**T2 仅完成 classical_rules_effects**。
3. `chain_step5` 仍是单函数 939 行巨石，拆分需先抽内部块为纯函数（未做，记入欠项）。
4. 评审要求「JSON 键被消费」而非只被引用；接线与外置必须成对落地。

## [S1] Problem

外部源不可得时，内部仍有断语残留、巨石、无单测、MCP 仅六爻、应期未分列、命科无运年交互。

## [S2] Design

见前序设计；实现以零指纹漂移为硬约束。

## [S3] Out of Scope

外部书源扩样；星煞/病药入主分；命运断语；相科。

## Tasks
- [x] T1: 断语外置收尾 — acceptance: 部分成句入 JSON 并接线；chain_narrate 残留未完 (covers: S2.1)
- [x] T2: classical_rules_effects 拆分 — acceptance: 门面 API 不变；零指纹漂移；chain_step5/chain_narrate 未拆 (covers: S2.2)
- [x] T3: tests/ pytest 五套件 — acceptance: 76 断言绿；check --full 纳入 (covers: S2.3)
- [x] T4: MCP 四科最小面 — acceptance: 四科 narrate/render 可用；api_spec 同步 (covers: S2.4)
- [x] T5: evaluate 应期日/月/年分列 — acceptance: 分列可复现；合集分不劣化 (covers: S2.5)
- [x] T6: 命科 dayun×liunian — acceptance: 6 样例测试；narrate 展示；core 三合 (covers: S2.6)
- [x] T7: 全量验证 — acceptance: check --full + pytest 全绿 (covers: S2)
