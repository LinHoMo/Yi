# 易学图谱（Yi Knowledge Graph）设计

> **核心目标**：构建一张从**哲学公理**演化到**术数具体概念**、再到**古籍断语**的有向知识图谱。
> 让 AI 能据此学习推演，让人能二次理解"为什么这么判"，让引擎的每一条判据都能向上追溯到哲学依据、向下锚定到代码实现。
>
> 本文档是总纲：五层架构、kid 命名规范、节点 schema、现有资产映射、分阶段执行路线。
> 创建：T30（2026-11-02），承接 RULE-ENGINE-REFACTOR-PLAN.md 的规则仲裁层成果。

---

## 一、为什么要这张图谱

现有引擎把"术数怎么判"做得很扎实（registry_v2 14 条规则、use_god_relations 取用神、domain_citations 分占域），但存在三个断层：

1. **哲学断层**：一条规则（如"回头克主凶"）直接给出判词，却说不清它从五行生克、从"反吟覆吟"的哪条公理推出来。
2. **溯源断层**：断语有逐字书源，但书源之间没有"这几条说的是同一回事的不同侧面"的关系。
3. **学习断层**：AI 拿到的是散落 JSON，人拿到的是古籍原文，两者没有同一张可双向跳转的索引。

图谱要做的就是把这三个断层补成一条**可推演的链**：

```
哲学公理 (why)  →  象数模型 (how the world is built)  →  术数术语 (what to look at)
                →  判卦规则 (how to judge)  →  古籍断语 (evidence)
```

每一层的每个节点都向上指"我从哪条公理来"，向下指"我派生出哪些规则"，旁挂"哪些书说了我"。

---

## 二、五层架构

| 层 | 名称 | 回答的问题 | 内容 | 现状 |
|---|---|---|---|---|
| **L0** | 元理层（哲学） | 世界为什么是这样 | 阴阳、五行（金木水火土）、太极→两仪→四象→八卦、体用 | **待建** |
| **L1** | 象数层（模型） | 卦盘是怎么搭出来的 | 天干、地支、纳甲装卦、五行生克（SHENG/KE）、六冲（CHONG）、六合（HE）、三合、十二长生、卦气 | **已有内核数据**（yishu_core/symbols.py），待知识化 |
| **L2** | 概念层（术语） | 看盘时认哪些东西 | 用神/原神/忌神/仇神、世应、动静变爻、月建日辰、旬空、月破、回头克、化退、伏飞、六神 | **已有**（use_god_relations/question_classes），待挂哲学依据 |
| **L3** | 规则层（判法） | 凭什么定吉凶 | 持世类、出现无情、变鬼、元神无力、救应时间窗、六冲变合… | **已有**（registry_v2 + rule_registry），待挂哲学依据和 kid |
| **L4** | 书证层（断语） | 古籍怎么说 | 增删卜易、卜筮正宗、易冒、火珠林、易林补遗、断易天机、易隐 的逐字断语 | **已有**（domain_citations/verdict_texts/caiguan_fushi），待挂节点 |

**层间方向是"演化"，不是"包含"**：L0 的五行生克公理 → L1 的 KE_CYCLE 数据表 → L2 的"回头克"术语（动爻变出克自己的五行）→ L3 的 shi_hua_ke 规则（世动回头克压凶）→ L4 的《增删卜易》逐字断语。一条链贯穿到底。

---

## 三、kid 命名规范与节点 schema

### kid（knowledge id）稳定唯一，永不重用

命名空间按层.域.概念：

```
yi.<layer>.<domain>.<concept>
```

- `yi.l0.wuxing.ke`          —— L0 五行相克公理
- `yi.l1.wuxing.ke_cycle`    —— L1 五行相克数据表（锚 KE_CYCLE）
- `yi.l2.concept.huitouke`  —— L2 回头克术语
- `yi.l3.rule.shi_hua_ke`    —— L3 世动回头克规则
- `yi.l4.book.zengshan.L551` —— L4 某条逐字断语

### 节点 schema（统一五类）

```json
{
  "kid": "yi.l2.concept.huitouke",
  "layer": 2,
  "name": "回头克",
  "def": "动爻所变出之爻，其五行反克本爻之五行，谓之回头克。",
  "parents": ["yi.l1.wuxing.ke_cycle", "yi.l2.concept.dong_bian"],
  "children": ["yi.l3.rule.shi_hua_ke", "yi.l3.rule.yong_shen_hua_ke"],
  "relations": [{"to": "yi.l2.concept.hua_tui", "type": "同属化凶"}],
  "evidence": [{"book": "增删卜易", "offset": 948, "text": "凡用神原神动化回头克…皆为化凶"}],
  "engine_impl": "rules/rule_engine.py:HUA_XIONG"
}
```

字段约定：
- `parents`：向上的哲学/公理依据（这条概念从哪来）。
- `children`：向下派生出的规则/术语。
- `relations`：旁系关系（生/克/冲/合/救/应/同属），带方向。
- `evidence`：逐字书证（书名 + offset + 原文）。
- `engine_impl`：代码锚点（哪个文件哪个符号实现了它）——保证"知识-代码"一致性可被看门狗回验。

---

## 四、一张完整的链（示例：回头克 → 待时吉）

用本轮 T29 刚落地的规则做示范，展示一条链如何贯穿五层：

| 层 | kid | 内容 |
|---|---|---|
| L0 | `yi.l0.wuxing.ke` | 五行相克：金克木、木克土…（"克"是制约，过克则伤） |
| L1 | `yi.l1.wuxing.ke_cycle` | `yishu_core/symbols.KE_CYCLE` 数据表 |
| L2 | `yi.l2.concept.huitouke` | 动变爻反克本爻 = 回头克；属"化凶" |
| L3 | `yi.l3.rule.shi_hua_ke` | 世动回头克 → cap=凶（即时压档） |
| L3 | `yi.l3.rule.shi_hua_ke_wang` | 但世临月建旺 → cap=吉（待时救应） |
| L4 | 增删 L? | "世临月建之官定得面见，被午火回头之克，待子日冲去午火方得拜谒" |

**这张链的价值**：书断"逢伤亦伤却有待时之用"不是孤例，而是"五行过克→世旺能任→冲克神解"三步推演。AI 学会这条链，就不是记住"回头克待时吉"，而是能推到"任何过克之象，只要主象旺、有冲解，都待时"。

---

## 五、现有资产映射（哪些已就位，哪些要建）

| 图谱节点 | 现有文件 | 要做的 |
|---|---|---|
| L1 象数 | `core/yishu_core/symbols.py`（BRANCH_ELEMENTS/SHENG/KE/CHONG/HE_PAIRS） | 导出为 L1 节点 JSON，挂哲学释义 |
| L2 取用神 | `data/rules/use_god_relations.json` | 每条规则转成 L2/L3 节点 + kid |
| L2 问类 | `data/rules/question_classes.json` | classes 转成 L2 节点 |
| L2 伏神 | `data/rules/caiguan_fushi.json` | 九宫转成 L2 节点 |
| L3 仲裁规则 | `rules/registry_v2.json`（14 条） | 每条加 kid + parents 哲学依据 |
| L3 旧规则登记 | `data/rules/rule_registry.json`（91KB） | 逐条补 kid，不删（blocking 看门狗仍用） |
| L4 分占域断语 | `data/rules/domain_citations.json` | 挂到所属 L3 节点 |
| L4 断语文案 | `data/rules/verdict_texts.json` | step5_classical_notes 挂 kid |
| **L0 哲学** | **无** | **新建 `data/ontology/l0_metaphysics.json`** |
| **L1 知识化** | **内核数据散在 symbols.py** | **新建 `data/ontology/l1_xiangshu.json`** |

---

## 六、目录规划（图谱落地后的分区）

```
liuyao/
├── rules/                    # L3 仲裁层（已闭环）
│   ├── rule_engine.py
│   ├── registry_v2.json
│   └── ...
├── data/
│   ├── ontology/            # 【新】易学图谱本体
│   │   ├── l0_metaphysics.json    # L0 阴阳五行八卦演化
│   │   ├── l1_xiangshu.json       # L1 象数模型（锚内核数据）
│   │   ├── l2_concepts.json       # L2 术数术语
│   │   ├── l3_rules.json          # L3 判法（kid 化 registry）
│   │   ├── l4_evidence.json       # L4 逐字断语索引
│   │   └── _index.json           # 全图节点索引（kid → 位置/层/parents）
│   ├── rules/               # 现有术数数据（question_classes/use_god_relations…）
│   └── sources/             # 古籍逐字原文（已有）
└── docs/
    └── YI-KNOWLEDGE-GRAPH.md   # 本文档
```

**原则**：ontology/ 是**只读知识层**，不参与评分；rules/ 是**运行时仲裁层**。两者通过 kid 互相引用，不互相 import 代码。

---

## 七、执行路线（分阶段，每阶段可独立交付）

### 阶段 A：骨架（本轮起）
- [ ] 建 `data/ontology/` 目录与 `_index.json` 格式约定
- [ ] 从 `symbols.py` 导出 L1 象数节点（天干地支五行生冲合）
- [ ] 用"回头克→待时吉"一条完整链跑通 kid schema（第四章示例落 JSON）

### 阶段 B：L0 哲学层
- [ ] 阴阳、五行、八卦的演化树（太极→两仪→四象→八卦）
- [ ] 每条 L0 公理挂"它派生出哪些 L1 模型"

### 阶段 C：L2 概念层 kid 化
- [ ] use_god_relations / question_classes / caiguan_fushi 全部转 kid
- [ ] 每个概念补 `parents`（哲学依据）

### 阶段 D：L3 规则层 kid 化
- [ ] registry_v2 14 条 + rule_registry 关键条 补 kid + parents
- [ ] 跑一条"哲学→规则"反链检查：每条规则必须能追溯到 L0，否则标 `orphan: true`

### 阶段 E：L4 书证挂接 + 学习视图
- [ ] domain_citations / verdict_texts 按 kid 索引
- [ ] 生成人可读的"概念卡片"（每个 kid 一页：定义/公理/规则/书证）
- [ ] AI 检索视图：按 kid 出 subgraph（parents + children + evidence）

---

## 八、铁律（防图谱变成又一本散落 JSON）

1. **每个节点必须有 parents**——孤儿节点（追溯不到哲学依据）要么补依据，要么显式标 `orphan` 待补，不许静默悬空。
2. **engine_impl 必须真实**——知识层声称"这条由某代码实现"，看门狗要能回验符号存在；否则就是"知识撒谎"。
3. **ontology 只读、rules 运行时**——图谱不改判分，只做索引和学习；判分仍走 rules/registry_v2。
4. **kid 永不重用**——废弃节点标 `deprecated`，不删 id，防历史引用断链。
