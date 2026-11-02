# 规则仲裁层改造计划（Rule-Engine Refactor）

> 立项：506 批收口后（zengshan strict 74.4% / verdict 19/26=73.1% / top-1 48.3%）。
> 起因：连续四批（502→506）在 `detect_direction_caps` 里裸写 if 加 cap，每加一条都要
> 手工写门控排除（`qcls not in ("行人","功名科举")`、`ug_cat != "子孙"`），误伤率高
> （3c 连续误伤 ZD050 行人、golden 占胎），靠门控打地鼠修补。本质是**判据硬编码在代码、
> 规则库（rule_registry.json）只是台账两张皮**。

---

## 一、问题诊断（缜密结论）

### 1.1 三张皮的现状
| 资产 | 现状 | 缺陷 |
|---|---|---|
| `data/sources/*.txt` | 16 部经典原文 + provenance，干净 | 断语是纯文本，知识未抽成结构化条目 |
| `data/rules/rule_registry.json` | 33 条规则，schema=`yi-rule-registry-v1`，每条带 source.verified | **是台账不是执行体**：`impl` 指向 `step4.py:1058` 这种代码行号；`applicability` 是自然语言备注，引擎不能仲裁 |
| `scripts/classical_enhancements_direction.py` | 9 类硬编码 cap（L157-427） | 判据真身在这里；`apply_caps` 先到先得取最严档，无优先级、无救应解除语义 |

### 1.2 两个根本错配
- **标量压多段**：`final_score` 一个数想同时回答"即时卦象吉凶"和"最终结局"。
  A 组救应卦（ZD015 回头克但子日冲去忌神终吉、ZD023 六冲变合散而复聚）无解——
  即时凶、应期吉是两个时间窗，一个数装不下。
- **cap 打地鼠**：规则没有"自带适用域 + 救应条件"，每加一条靠 if 排除已对的例，
  误伤随规则数线性增长。

---

## 二、目标四层架构

```
L0 文献库   sources/*.txt + provenance（已有，保持）
L1 知识图谱 断语 → 结构化 kid{locator,原文,卦象前件,吉凶方向,救应条件,适用域}
L2 规则仲裁层 registry v2：每条规则带 machine-readable when/gates/rescue/priority/cap
L3 推理编排  step5 瘦身成调度器：只调 L2 仲裁，不再硬编码判据
```

---

## 三、registry v2 schema（向后兼容 v1）

在 v1 条目基础上新增可执行字段：

```json
{
  "rule_id": "liuyao.shi_hua_ke",
  "domain": "世爻变凶",
  "when": {
    "world_moving": true,
    "world_change_type": "回头克"
  },
  "gates": {
    "qcls_not": ["行人", "功名科举"],
    "ug_cat_not": ["子孙"]
  },
  "rescue": {
    "any_line": {"six_relation": "子孙", "is_moving": true}
  },
  "cap": "凶",
  "priority": 50,
  "source": {"book": "增删卜易", "locator": "dz.txt:3625", "quote_in_code": "...", "verified": true},
  "eval_dim": "verdict"
}
```

**谓词集（务实最小集，不搞通用 DSL）**：
`world_moving`、`world_change_type`、`world_six_relation`、`yongshen_moving`、
`yongshen_change_type_contains`、`qcls_eq/qcls_in/qcls_not`、`ug_cat_eq/ug_cat_not`、
`any_line{six_relation,is_moving}`、`month_state`、`chong(变爻,月建)`、`broken`。

> 设计纪律：when 只表达"卦象静态事实"，gates 表达"适用情境域"，rescue 表达"满足则解除"。
> 三者分离——这正是现在 if 里缠在一起的东西。

---

## 四、阶段划分与验收基线

**保护网（每阶段必须全绿，零漂移）**：
- `tests/regression_test.py` 19/19
- `tests/thinking_chain_tests.py` 12/12
- zengshan_dz_holdout strict 74.4% / verdict 19/26 / top-1 48.3%
- bushi_zhengzong_holdout 68.1%
- wikisource_holdout 75.8%
- golden 机械 8f60e077f66827a7 / 措辞 8168eff9e560d6c2（288 例）

### 阶段 0（地基 + 最小闭环）
- **T24**：建 `rule_engine.py`，实现谓词求值 + registry v2 读取。只建不改输出。
- **T25**：迁 3a/3b/3c（回头克 / 回头生月破 / 用神化退）三条到 registry v2，
  rule_engine 复现。detect_caps 里这三条改成调 rule_engine。**验收：全保护网零漂移**。

### 阶段 1（全面迁移 + 仲裁升级）
- **T26**：迁变鬼三分支（变官不压 / 休囚受克压 / 回头克无解救压）+ 元神无力（疾病久病）。
- **T27**：迁出现无情(功名)、兄弟持世求财/婚姻、天气占。detect_caps 瘦成纯调度。
- **T28**：`apply_caps` 升级——priority 仲裁 + rescue 解除（现在只有"无解救才压"，
  没有"规则被救应规则解除"的双向语义）。

### 阶段 2（认知层革新，救应卦根本解）
- **T29**：verdict 拆成 present(即时卦象) / rescue_chain(救应推演) / timing(应期)。
  输出从一个数变结构化叙述。解决 A 组 4 例（ZD015/023/160/194）。
  同步改 evaluate verdict strict 口径与 readout_ledger（新旧不可比，须登记）。

### 阶段 3（知识图谱）
- **T30**：文献断语批量抽 kid，registry 规则与 kid 双向链接。

### 阶段 4（收尾）
- **T31**：step5.py（110KB）瘦身为调度器。

---

## 五、执行纪律
1. 每阶段一提交，提交信息含"读数新旧不可比"（若改了口径）或"零漂移复现"（若纯重构）。
2. 迁移一条规则 = 从 detect_caps 删一段 if + registry 加一条 v2，**同批回归**。
3. 回补 readout_ledger；破保护网立即回退，不硬上。
4. 八字 congrge（ZC014 灰区）不在本计划，保持作者登记状态。
