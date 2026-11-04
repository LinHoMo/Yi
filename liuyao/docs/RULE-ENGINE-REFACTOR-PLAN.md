# 规则仲裁层改造（Rule-Engine Refactor）· 结案记录

> **状态（第五百一十批）**：D1–D5 与 T28–T31 全部结案，本文件从「方案」降为**结案记录**——
> 只留现行结构与完成台账；设计论证、schema 草案、T29 分三批的迁移细目已随结案删除
> （批次身份与一句话见 `CHANGELOG-HISTORY-INDEX.md`，正文在 git 历史）。

## 一、现行结构（真源）

```
liuyao/rules/
├── rule_engine.py   # 仲裁器：evaluate_caps + evaluate_verdict_overrides
├── predicates.py     # 共享纯函数（RANK/月态/冲/破/合/化凶）
├── direction.py     # detect_caps 纯调度（零硬编码 if）
└── registry.json    # 21 条 cap 规则 + 7 条 verdict_overrides

liuyao/engine/       # 推演实现（508 批升格，与 scripts/ 平级）
├── _core.py         # 装卦入口（`import engine` 即此包）
├── pipeline/        # step1~5 + _step5_{dates,factors,timing,weather}
└── classical/       # classical_enhancements 族（含 dufa/fangwei/fushi/menlei 等 7 变体件）
```

- **判据分两层**：`rules/registry.json` 是**可执行规则**（when/gates/rescue/cap/priority），
  `data/rules/legacy/rule_registry.json` 是**台账/书证**（impl 指针＋引文＋verified）。
  两者不是同一张表，改其一不必改另一（改 cap 规则须另批带书证两集出分）。
- **`data/rules/` 已分区**：`legacy/`（旧台账、题类、裁决散文）、`domain/`（判定表、层契约、
  裁决表、千金赋映射等）。dev_tools 读新路径；`_partition_remap` 仍保留作旧指针兜底。
- **台账指针口径（第五百零九批改定）**：台账 impl 的代码路径**与代码同批回改**，不再靠转发兜底；
  505 批「台账不回改」的决策作废，转发逻辑仅作双保险。

## 二、完成台账

| 项 | 结果 |
|---|---|
| D1 `rules/` 独立成树（破环抽 `predicates.py`） | 已完成（批号见 `CHANGELOG-HISTORY-INDEX.md` 标题） |
| D2 `data/rules/` 分区（`legacy/`＋`domain/`） | 已完成（505 批） |
| D3 `engine/pipeline/` 收 step1~5 | 已完成（506 批转发 → 508 批落点升格） |
| D4 `engine/classical/` 收 classical_enhancements 族 | 已完成（505 批 `scripts/classical/` → 508 批 `engine/classical/`） |
| D5 step5 按职责拆模块（＝T31） | 已完成（`_step5_{dates,factors,timing,weather}` 随 step5 迁入 `engine/pipeline/`） |
| T28 cap priority 仲裁 | 已完成（21 条均 priority=0，零漂移） |
| T29 verdict 拆三段（present/rescue/timing_speed） | 已完成（504 批 verdict_overrides 数据化后三段值相同，新旧可比） |
| T30 知识图谱 L2 kids + AI subgraph | 已完成（71 节点无幽灵） |
| T31 step5 瘦身（净删约 510 行） | 已完成（批号见索引标题） |

## 三、边界（有意维持，不是欠账）

- 旧台账 33 条里 12 条 v1-only（yingqi/sanxing/fanyin/fangwei/muku/heban 等）不在 v2 cap 范围，
  保留为书证台账，不迁 `registry.json`。
- 判据迁移的验收门槛仍是 AGENTS §四：golden 双指纹零漂移 + tune/holdout 分别出分；
  纯重构批写「零漂移复现」，动口径批写「新旧不可比」。
- 本文件不再承载新方案；新改造立项写在 `CHANGELOG.md` 当批，避免「文档有计划、代码无进度」。
