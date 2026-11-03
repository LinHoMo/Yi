# 规则仲裁层改造（Rule-Engine Refactor）

> 目标：把硬编码在 `detect_caps`/`step5` 的判据迁成数据化规则，由 `rule_engine` 统一求值。
> 保护网：golden 288 例双指纹零漂移（基线见 `data/golden/digest.json`）、regression 19/19、
> tune/holdout 不退化。每阶段一提交，纯重构写"零漂移复现"，改口径写"新旧不可比"。

## 一、为什么要改

旧架构三张皮：`data/rules/rule_registry.json` 是台账（impl 指代码行号、自然语言备注），
判据真身硬编码在 `rules/direction.py` 的 `detect_direction_caps`。每加一条 cap 都要写 if 排除
已对的例，误伤随规则数线性增长（3c 连续误伤行人/占胎）。

两个根本错配：
- **标量压多段**：`final_score` 一个数同时答"即时卦象吉凶"和"最终结局"，救应卦无解。
- **cap 打地鼠**：规则没有自带适用域与救应条件，靠 if 排除已对的例。

## 二、目标四层架构

```
L0 文献库   data/sources/*.txt + provenance（已有）
L1 知识图谱 data/ontology/（L0 哲学/L1 象数/L2 概念/L3 规则/L4 书证；AI subgraph 检索视图已上线）
L2 规则仲裁 rules/registry.json：每条规则带 machine-readable when/gates/rescue/priority/cap
L3 推理编排 step5 调度器：只调 L2 仲裁，不再硬编码判据
```

## 三、规则数据 schema

在 v1 台账条目上新增可执行字段，谓词集务实最小（不搞通用 DSL）：

```json
{
  "rule_id": "liuyao.shi_hua_ke",
  "when": {"world_moving": true, "world_change_type": "回头克"},
  "gates": {"qcls_not": ["行人", "功名科举"], "ug_cat_not": ["子孙"]},
  "rescue": {"any_line": {"six_relation": "子孙", "is_moving": true}},
  "cap": "凶", "priority": 50,
  "eval_dim": "verdict",
  "source": {"book": "增删卜易", "locator": "dz.txt:3625", "verified": true}
}
```

设计纪律：`when` 只表达卦象静态事实，`gates` 表达适用情境域，`rescue` 表达"满足则解除"——
三者分离，正是旧 if 里缠在一起的东西。`any_of:[{...},{...}]` 表 OR 组（组内仍 AND）。

## 四、当前状态（504 批收尾后）

**rules/ 已独立成树**（D1 破环抽 `predicates.py` 后落位）：

```
liuyao/rules/
├── rule_engine.py   # 仲裁器：evaluate_caps + evaluate_verdict_overrides
├── predicates.py    # 共享纯函数（RANK/月态/冲/破/合/化凶）
├── direction.py     # detect_caps 瘦成纯调度（118 行，零硬编码 if）
└── registry.json    # 21 条 cap 规则 + 7 条 verdict_overrides
```

- **阶段 0/1 已完成**：T24–T27（谓词求值、迁 3a/3b/3c、兄弟持世/天气/功名/出行/占寿/铺面/
  鬼持世等 21 条 cap；变鬼三分支拆 3 条互斥规则；元神无力用 any_of）。
- **verdict_overrides 数据化已完成（504 批）**：step5 里 7 条古籍强凶格局覆写（行人散/合伙散/
  用神弱净动负/三刑六合相战/合处逢冲两档/财价跌）迁为 `registry.json#verdict_overrides` 数据规则，
  由 `evaluate_verdict_overrides` 按数组顺序求值；golden 双指纹零漂移。
- **旧 `rule_registry.json`（33 条）保留为台账**：12 条 v1-only 是非 cap 结构/分值规则
  （yingqi/sanxing/fanyin/fangwei/muku/heban 等），不在 v2 scope，刻意保留。
- **目录分层蓝图**（§七）：`rules/` 已独立；`engine/pipeline`、`engine/classical` 等物理
  收编未启动（见下 D 系列批次表）。

## 五、剩余待办

| 项 | 状态 | 说明 |
|---|---|---|
| **T28 apply_caps priority 仲裁** | ⬜ 有意暂缓 | 当前 first-pass/worst-cap 在全部回归用例零漂移；21 条均无 priority 字段。等需要细粒度冲突解决时再加。 |
| **T29 verdict 拆段** | ⬜ 未启动 | verdict 拆 present(即时)/rescue_chain(救应)/timing(应期)。改 evaluate strict 口径，新旧读数不可比，须专门批次。 |
| **T30 知识图谱 kids.json** | 🔶 部分进行中 | L2 概念 kid 化（回头克/世旺/冲解）与 AI subgraph 视图（`dev_tools/ontology_subgraph.py`）已上线；`use_god_relations/question_classes/caiguan_fushi` 批量转 kid、全量 parents 补全仍待做。 |
| **T31 step5.py 瘦身** | ⬜ 未启动 | step5.py 110KB 上帝模块，按职责拆模块为最高风险批次，须单批走保护网。 |

## 六、目录分层蓝图（后续物理收编批次）

目标（低风险→高风险，每批跑全保护网）：

| 批 | 动作 | 风险 |
|---|---|---|
| D1 | rules/ 独立成树 ✅ | 已完成 |
| D2 | data/rules/ 内部分区（legacy/ 旧台账、domain/ 领域表） | 高（dev_tools 硬编码路径须同步） |
| D3 | engine/pipeline/ 收 step1~5 | 高（step 链互引） |
| D4 | engine/classical/ 收 classical_enhancements 族 | 中 |
| D5 | step5.py 按职责拆模块（=T31） | 最高 |

旧 `rule_registry.json` 被 `check_rule_registry.py / readout_ledger.py / ablation.py /
build_adjudications.py` 硬编码引用，**不物理删除、不直接挪路径**——D2 批在 `data/rules/legacy/`
留实体，dev_tools 改读新路径，旧路径留一版转发或 CHANGELOG 登记弃用期。
