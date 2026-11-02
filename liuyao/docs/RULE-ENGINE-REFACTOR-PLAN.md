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

---

## 六、执行进展（507→510 批，纯重构零漂移）

| 批 | commit | 内容 | 保护网 |
|---|---|---|---|
| 507 | 1d077e9 | 阶段0最小闭环：rule_engine.py + v2 JSON 落地；迁 3a回头克/3b回头生月破/3c用神化退 | 全绿 |
| 508 | 087557c | 迁兄弟持世婚姻/天气占雨/占晴；扩谓词集 world_six_relation/moving_or_changed_relation | 全绿 |
| 509 | 3ca6459 | 迁兄弟持世求财；cap 支持动静分档(凶/平凶)、rescue 支持盘面谓词(日月作财例外) | 全绿 |
| 510 | 65e76d1 | 迁出现无情(功名)；加官鬼/父母生世合世谓词 + detail sorted-set 复现 | 全绿 |

**已迁 8/9 条硬编码判据**。detect_direction_caps 从满屏 if 瘦身到只剩 2 块：
变鬼三分支（shi_hua_gui）、元神无力（yuan_shen_wu_li）。
全程 zengshan 74.4/19-26、bushi 68.1、wikisource 75.8、golden 8f60/8168、regression 19、思维链 12 **一字未变**。

### 阶段1攻坚修订（T26 重新定义）
剩两块判据暴露出当前 v2 when 只支持**平铺 AND** 的天花板：
- **变鬼三分支互斥**：旺相回头生=变官不压 / 休囚·月破 且(日克·动克)=压 / 回头克且无救应=压。
- **元神无力**：`休囚 且 (静·月克·日克·动克 任一)` 或 `全空破` 或 `动化凶`——when 里需要 OR 组。

故 T26 拆为两步：
- **T26a（schema 攻坚）**：v2 when 增加 `any_of:[{...},{...}]`（OR 组，组内仍 AND）；detail 增加 `tag_any`（按命中条件拼"月破/日克/动克/休囚"词）。
- **T26b（迁移）**：变鬼拆 2 条互斥 v2 规则（分支2/分支3；分支1"变官不压"写成 gates 排除）；元神无力用 any_of 表达。迁完 detect_caps 瘦成纯调度。

---

## 七、目录分层蓝图（511 批落档）

### 7.1 现状盘点
- `scripts/` 54 个 .py 平铺：step5.py 110KB（上帝模块）、classical_enhancements.py 88KB、
  classical_enhancements_direction.py 8.4KB（已瘦成调度壳）、rule_engine.py 18.3KB（新仲裁器）。
- `data/rules/` 17 个 JSON 平铺：旧 `rule_registry.json` 89KB（dev_tools 链重度引用，**不能物理删**）、
  `verdict_texts.json` 91KB（文案外置）、新 `rule_engine_v2.json` 5.7KB（11 条）。

### 7.2 目标目录树（按职责分层，物理挪动分批做）
```
liuyao/
├── rules/                     # L2 规则仲裁层（新架构核心，先独立成树）
│   ├── engine.py              #   谓词求值仲裁器（现 scripts/rule_engine.py）
│   ├── registry_v2.json      #   规则数据化（现 data/rules/rule_engine_v2.json）
│   └── predicates.py          #   谓词集（后续从 engine.py 拆出，纯函数）
├── engine/                    # L3 推理编排
│   ├── pipeline/              #   step1~step5 五步（现 scripts/step*.py）
│   ├── classical/              #   古典增强族（现 classical_enhancements*.py 8 个）
│   ├── narrative/              #   chain_*/narrate*/thinking_chain
│   └── format/                 #   engine_format*/engine_chart/render/chart*
├── knowledge/                 # L1 知识图谱（T30 建）
│   └── kids.json              #   文献断语结构化条目
├── data/
│   ├── sources/               # L0 文献原文（已有，保持）
│   ├── rules/                 # 旧台账+文案（见 7.4 处置）
│   └── ...
```

### 7.3 迁移批次（低风险→高风险，每批跑全保护网）
| 批 | 动作 | 风险 |
|---|---|---|
| D1 | 建 `rules/` 目录，rule_engine.py + v2 JSON 挪入；改 detect_caps/step5 的 import | 中（2 处 import） |
| D2 | `data/rules/` 内部分区：`legacy/`（rule_registry/verdict_texts 旧台账）、`domain/`（question_use_gods 等领域表） | 高（dev_tools 硬编码路径，须同步改） |
| D3 | `engine/pipeline/` 收 step1~5 | 高（step 链互引） |
| D4 | `engine/classical/` 收 classical_enhancements 族 | 中 |
| D5 | step5.py 110KB 按职责拆模块（T31） | 最高 |

### 7.4 旧 rule_registry.json 处置（硬约束）
被 `dev_tools/check_rule_registry.py / readout_ledger.py / ablation.py / build_adjudications.py`
硬编码引用，**不物理删除、不直接挪路径**。做法：D2 批在 `data/rules/legacy/` 保留实体，
dev_tools 改读新路径；旧路径留 1 个版本的转发或在 CHANGELOG 登记弃用期。

### 7.5 验收
每批同 §四保护网全绿才进下一批；物理挪动不改任何判据输出，golden 双指纹必须一字不动。

---

## 八、D1 落地执行记录（514 批）

**结果：rules/ 物理独立成树，全保护网零漂移（regression 19/19、golden 双指纹、zengshan strict 74.4%）。**

实际落位：
```
liuyao/rules/
├── __init__.py
├── rule_engine.py     # 仲裁器（原 scripts/rule_engine.py）
├── predicates.py      # 共享纯函数库（新建，破环抽出）
└── registry_v2.json   # 11 条规则数据（原 data/rules/rule_engine_v2.json）
```

**破环先行（66c6470）**：旧环 `rule_engine ──import──> classical_enhancements_direction(纯函数)`
与 `classical_enhancements_direction ──延迟 import──> rule_engine.evaluate_caps` 互相引用。
先抽 `predicates.py`（RANK/_world_line/_month_state/_chong/_broken/_he/HUA_XIONG），
两者都单向依赖 predicates，环断后 engine.py 才能干净挪目录。

**踩坑记录**：`scripts/` 下本就存在原生 `engine.py`（其他模块）。若把仲裁器平铺命名为
`engine.py`，`from engine import` 会优先解析到 scripts/engine.py 而非 rules/，
报 `cannot import name 'evaluate_caps'`。故仲裁器保留 `rule_engine.py` 原名，不改名。

**sys.path 现实**：运行时是平铺架构（core/、scripts/ 在 sys.path，liuyao/ 根不在）。
rules/ 下模块自加 scripts/ 找 kernel_path；classical_enhancements_direction 自加 rules/ 找
rule_engine/predicates。未改包导入机制（避免牵动 step 链），分层靠物理目录 + 各自 sys.path 前置。


