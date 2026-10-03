# 合参层（Synthesis）

易的立身之本。市面工具多在一事一卦上打转，本项目要做的是：**同一个人，命与卜分别分析，
再由易合起来，给出阶段性指导与规划。** 这层不做，"易"就只是一个路由。
（相科已剔除，合参按命·卜两科成立；日后若增学科，本层规则按同一形式扩展。）

本层**已实现**（2026-09-23）：`person.py`（档案模型）、`normalize.py`（学科输出归一化）、
`cross_rules.py`（裁决规则）、`guidance.py`（指导生成）、`cli.py`（命令行入口）、
`outcome_eval.py`（应期回收闭环评分，2026-09-24）。
入口：`python cli.py --help`（init / validate / add-divination / record-outcome / outcome-eval / guide / selfcheck）。

## 〇、CLI 用法（工作目录 `synthesis/`）

```bash
python cli.py init P001 --solar "1990-05-20 07:15"                        # 新建档案 → person/P001.json
python cli.py validate P001                                               # 校验档案
python cli.py add-divination P001 --discipline liuyao \
       --analyze-json <analyze.json> --at "2026-09-23 10:00"                # 登记占问（归一化，需各科 analyze 输出）
python cli.py record-outcome P001 --event-id EVT001 --result 应验 \
       --occurred-at 2026-10-05 --judged 应验                              # 回填现实结果（应期回收闭环入参）
python cli.py outcome-eval P001                                           # 应期回收评分：回填 × 断卦应期
python cli.py evidence-cross P001                                          # 证据级检视：same/conflict/unassessed 清单
python cli.py guide P001                                                   # 生成指导 → guidance/P001.md
python cli.py selfcheck                                                     # 合参层自检
```

档案存 `person/<id>.json`，指导存 `guidance/<id>.md`（两者均已 gitignore，属运行产物）。
`add-divination` 的良输入是各科 `analyze` 段输出的 JSON；系统归一化为统一占问记录，含方向/应期/判据所本。

### 应期回收闭环（outcome-eval）

断卦时六爻 analyze 输出把应期候选连同法则结构化给出（`conclusion.应期明细`，
归一化后存 `divinations[].yingqi_offered`，按给出顺序即名次）。事后回填
`--occurred-at`（应验/观察日期）+ `--judged`（应验/未应验/部分应验/超期未验），
`outcome-eval` 按候选名次比对：

- 第 1 位候选命中 → 主应期；第 2~4 位 → 次应期；更靠后 → 命中但名次靠后；早于全部候选 → 提前；晚于末位候选 → 超期。
- 断事层面：judged 应验/部分应验 → 断事应验；未应验/超期未验 → 未验。
- 汇总带样本量 n 与集合名（档案内已回填占问）。口径诚实：这是**现实回填命中**，
  不是古籍案例对齐分，也绝不等于"预测率"（`AGENTS.md` §三）。

此闭环让"哪个法则推出哪个日"可事后核验：逐例判定带 `rule` 标签，攒够样本后可按法则统计命中，供六爻应期法则迭代。

### 证据级检视（evidence-cross，2026-10-03 起）

归一化记录自 2026-10-03 起附带 `evidence` 字段（Evidence Contract 派生视图，
schema 与提取器唯一实现在 `core/yishu_core/evidence.py`；评测基线取自能力注册表
`core/yishu_core/execution/registry.py`）。`evidence-cross` 在**旧五条裁决之下**
新增一层证据级检视（实现 `evidence_cross.py`），输出三类结构化清单：

- **same / conflict / single**：按维度（factor）归组的证据一致性。冲突**保留双方**
  claim + 适用条件（applicability）+ 出处，不做平均、不编调和说；方向级分歧的
  裁决权仍在 §二 的五条规则（`cross_rules.adjudicate`，本层不替代）。
- **unassessed**：无评测覆盖（`unassessed`）或仅有出处声明（`source_only`）的证据
  显式登记为缺口——宁登记缺口，不制造假评测。学科无方向表态（liuren 骨架/lingqi
  直录/命科机械标签）单列为 silent，不冒充表态。
- **一致性描述**：跨科同向只提升"证据一致性"的描述强度，**不自动制造新的事实**；
  本层输出无任何趋势/得分字段。

诚实边界：维度级对照仅对**同名词**（同 factor 字符串）成立；跨科维度词表
（六爻「六合/六冲」↔ 梅花「体用关系」）尚未统一，硬造对照属新规则工作、须逐条带古籍依据。

**进主合参文档（2026-10-03 起）**：`guide` 生成的指导文档 §三 内嵌同一份检视
（同一 `cross_examine`，规则注册表挂接口径一致）——「合参结论」的趋向声明带
**方向级计数倾向**口径限定，`two_one`（两吉一凶）不再是无条件的最终逻辑：
异向结论及其成立条件在检视小节单列，采信前须核对双方评测状态；档案未携带
结构化证据（旧档案）时如实声明「证据级检视不可用，描述强度不提升」。
silent（有证据但无方向表态）与 no_evidence（未携带证据）分列，不再混为一谈。

### canonical 反馈模型（FeedbackRecord，2026-10-03 起）

本层（`outcome_eval.py`）与六爻侧（`dev_tools/feedback_store.py`）两条反馈链的
**存储与判定口径保留不变**，但记录形态统一折叠为 canonical `FeedbackRecord`
（schema 唯一真值源 `core/yishu_core/feedback.py`）后进入统计：

- `from_synthesis_divination()` / `from_liuyao_feedback()` 为双向 adapter；
  六爻 store 另有 `load_all_canonical()` 出口。判定真值源仍是
  `core/yishu_core/yingqi`（名次制/容差窗两制，门 `[1i]` 锁定）。
- `provenance.kind` 强制区分 **real_outcome / synthetic_regression**：真实回填与
  合成回归数据物理/语义分离，混集（`validate_record_set`）直接判败；
  合成记录只允许存在于测试夹具，永不进真实效度统计。
- 六爻 store 只判应期不断事——adapter 折叠后 `judged` 留空，不冒充断事判定。

## 一、人的档案 `person/<id>.json`

合参的前提是各科的结论能挂到同一个主体上，且可回溯到各自的盘。

```json
{
  "id": "P001",
  "created": "2026-09-22",
  "birth": {
    "solar": "1990-05-20 07:15",
    "place_longitude": 116.4,
    "ganzhi": {"year": "庚午", "month": "辛巳", "day": "…", "hour": "…"},
    "calendar_policy": {"boundary": "day", "zi_hour": "night_same_day"},
    "assembled_from": "ganzhi_resolved"
  },
  "divinations": [
    {"event_id": "…", "asked": "占近三月财运", "at": "2026-09-22",
     "discipline": "liuyao", "verdict": "…", "direction": "吉",
     "timing": ["应期 2026-10-05（冲空填实）"],
     "yingqi_offered": [{"date": "2026-10-05", "rule": "冲空填实"}],
     "outcome": {"recorded": null, "note": "待事后回填，用于真实效度"}}
  ],
  "guidance": [{"issued": "2026-09-22", "window": "2026-Q4", "advice": "…", "based_on": ["liuyao:…"]}]
}
```

要点：
- `birth.ganzhi` 必须带 `calendar_policy`。各科若用了不同的年界/子时口径，合参就是在比两件事。
- `divinations[].outcome` 是**唯一能产生现实效度证据的字段**。六爻已有 300KB 求测日志，
  但没有结果回填，所以永远只能报"古籍对齐分"。这一步在本层补，不在学科层补。
- `divinations[].yingqi_offered` 是六爻断卦时的结构化应期候选（date+rule，顺序即名次），
  现实回填后供 `outcome-eval` 评分；其余学科暂无结构化候选（`timing` 仅文本），应期不评。
- `divinations[].outcome.judged` 取值：应验 / 未应验 / 部分应验 / 超期未验；
  `occurred_at` 为应验/观察日期（YYYY-MM-DD，须为有效日期）。

## 二、合参裁决规则

| 情形 | 处理 |
|---|---|
| 某科结论超出其合法域（用六爻断人一生格局、用八字断某笔钱能否当日到账） | 判为无效输入，不参与合参，并在报告中说明为何剔除 |
| 各科同向 | 可提升陈述强度，但仍不用"注定/一定"；给出触发条件与时间窗 |
| 两科同向、一科异向 | 以两科为趋向，异向单列并给出其成立条件 |
| 各科异向 | **先查输入是否同一个时空**（年界/月界/日辰口径差异会造成假分歧），再查起局时间与用神/十神选取；核对后仍分歧则如实并列两种趋向及各自触发条件，交当事人，不做平均、不编调和说 |
| 任一科缺数据 | 降级为"该维度未参评"，不得用其他科补位猜测 |

分歧九成来自时空口径与取用错误——这条来自六爻实测：历法修正改掉了 236 天的年柱与 44 天的月建，
其中相当一部分原本会表现成"这一卦不准"。

## 三、输出：给一个人的指导

`guidance/<id>.md`，结构固定：

1. **格局与节律**（命，若可用）—— 所宜方向、起伏节律
3. **近期诸事**（卜）—— 逐事给主/次应期与所本法则
4. **合参结论** —— 同向处、互证处、存疑处分列，每条注明来自哪一科的哪个判据
5. **可执行建议** 2–4 条 + 复验时点（到哪个窗口回看结果，回填 `outcome`）
6. **边界声明** —— 医疗、法律、投资以专业意见为准；象征推演给方向不给定论

禁止：拼贴安慰叙事（"真正的正缘在散场之后才会清晰"这类没有判据来源的话）；
凡"未来会怎样"的推演，必须有经文依据（注明出处）或某科的显式判据支撑。
