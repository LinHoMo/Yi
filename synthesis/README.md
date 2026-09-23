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
