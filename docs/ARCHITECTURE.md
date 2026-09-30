# 易 · 架构总览（v1.0）

> 本文描述当前仓库的最终架构状态——不保留已过时的里程碑过程叙事（可查 git 历史）。
> 操作纪律见 `AGENTS.md`；分数口径见 `docs/CHANGELOG.md`；现状读数见 `docs/HANDOFF.md`。

---

## 一、系统定位

易是命、卜两科的统一 skill：一份内核 + 若干学科适配层 + 一个合参层。
差异化不在「算得准」，而在多科结论如何对齐、冲突如何裁决、如何落成可执行建议。

| | 输入 | 回答 | 时间尺度 |
|---|---|---|---|
| **命** | 出生时空（公历年月日时 + 性别） | 格局与趋势（机械推演，不作命运断语） | 一生 |
| **卜** | 一念之动（所问之事 + 起卦方式） | 一事成败与应期 | 一事 |

**范围（六科）**：命科 = `ming`（四柱八字）+ `ziwei`（紫微斗数）；
卜科 = `liuyao`（六爻纳甲）+ `meihua`（梅花易数）+ `xiaoliuren`（小六壬）+ `zeji`（择吉）。
梅花、小六壬、择吉曾于 2026-09 归档，2026-09-29 已还原至 `disciplines/`。
云端出报告见 `.github/workflows/report.yml` 与 `docs/AI-SOP.md`。
相科（面相、手相、堪舆）明确不做。

---

## 二、目录结构

```
Yi/
├── AGENTS.md                # 项目铁律（运算归代码·案例隔离·口径诚实）
├── SKILL.md                 # 统领 skill：意图路由 + 选科 + 调用监督 + 合参入口
├── README.md                # 面向用户的介绍
├── pyproject.toml           # 项目配置（yishu-core 包 + pytest）
├── .github/workflows/       # 云端出报告 report.yml（见 docs/AI-SOP.md）
│
├── core/
│   └── yishu_core/          # 唯一真值源
│       ├── ganzhi_calendar.py   # 太阳视黄经→节气→干支历
│       ├── symbols.py          # 干支五行/生克/六合六冲/三合三刑/十二长生/纳音
│       ├── shensha.py          # 星煞起例与安星函数（命·卜共用）
│       ├── najia.py            # 纳甲支表/八宫归属/安世应
│       ├── relations.py        # 五行关系/六亲/生克指数
│       ├── ming_tables.py      # 藏干十神/大运起法/命宫身宫（仅命科）
│       ├── hexagram_texts.py   # 六十四卦卦辞爻辞
│       ├── lunar.py            # 公历↔农历互转
│       ├── eval.py             # 全仓库唯一评分器
│       ├── runtime.py          # UTF-8 子进程/控制台适配
│       ├── calendar_check.py   # 历法自检
│       └── report/             # HTML/MD 报告 kit
│           └── html.py
│
├── disciplines/
│   ├── base/                    # 共享层（协议定义 + CLI 基类）
│   │   ├── protocol.py          # 四段契约 TypedDict/Protocol/合规检查
│   │   └── cli.py               # DisciplineCLI 基类（argparse + chart/analyze/narrate/render/cast）
│   │
│   ├── liuyao/                  # 六爻纳甲（卜科）
│   │   ├── SKILL.md
│   │   ├── scripts/             # ~32 个模块（由 58 个合并而来）
│   │   │   ├── chart.py         # 四段契约入口：起卦→排盘
│   │   │   ├── analyze.py       # 四段契约入口：规则推演
│   │   │   ├── narrate.py       # 四段契约入口：人话叙述
│   │   │   ├── render.py        # 四段契约入口：报告渲染（HTML/MD/SVG）
│   │   │   ├── liuyao_engine.py # 薄聚合入口（再导出 engine_* 子模块）
│   │   │   ├── liuyao_analyze.py# 分析编排（装配 factors + verdict + basis）
│   │   │   ├── liuyao_narrate.py# 叙述编排（师傅口吻正文）
│   │   │   ├── liuyao_timing.py # 应期核心（候选/法则/排序/组装）
│   │   │   ├── classical_enhancements.py  # 古籍增强（格局/神煞/伏返吟等）
│   │   │   ├── effects.py       # 六合六冲/三合/六亲持世效应
│   │   │   ├── chart_tables.py  # 排盘表生成
│   │   │   ├── narrative_utils.py# 叙事辅助（格局标签/引文/详释）
│   │   │   ├── thinking_chain.py# 思维链装配（Step 1-5 推理标记）
│   │   │   ├── classical_analysis.py  # 经典分析门面（再导出 classical_* 子模块）
│   │   │   ├── classical_rules.py     # 经典规则门面（格局识别）
│   │   │   ├── advice_framework.py    # 建议框架（按事类+格局定制）
│   │   │   ├── engine_chart.py        # 排盘引擎
│   │   │   ├── engine_calendar.py     # 历法引擎
│   │   │   ├── engine_format.py       # 格式化门面
│   │   │   ├── engine_format_report.py# 报告九段排版
│   │   │   ├── chain_tables.py        # 合冲刑/六冲六合卦表
│   │   │   ├── narrative_rules.py     # 叙事规则（开场/动变/特殊格局句）
│   │   │   ├── bing_yao_shensha.py    # 病药/星煞面板
│   │   │   ├── trigram_symbolism.py   # 八卦万物类象
│   │   │   ├── visualization.py       # SVG 卦盘
│   │   │   ├── kernel_path.py         # 内核路径解析
│   │   │   ├── evaluate.py            # 古籍案例对齐评测
│   │   │   ├── case_runner.py         # 案例运行器
│   │   │   ├── event_logger.py        # 占问事件日志
│   │   │   ├── yi_liuyao.py           # 一键 CLI（chart→analyze→render 单命令闭环）
│   │   │   └── mcp_server.py          # MCP server（六爻七方法）
│   │   ├── references/        # 知识库
│   │   ├── data/              # 数据层（verdicts/cases/rules/golden）
│   │   ├── tools/             # 学科级工具（check/golden/refactor_guard/regression 等）
│   │   └── guard/             # 重构指纹基线（用于零漂移验收）
│   │
│   ├── ming/                    # 四柱八字（命科）
│   │   ├── SKILL.md
│   │   ├── scripts/             # chart/analyze/narrate/render/pattern/mcp_server
│   │   ├── references/
│   │   ├── data/
│   │   └── dev_tools/           # check/golden/regression
│   │
│   ├── ziwei/                   # 紫微斗数（命科）
│   │   ├── SKILL.md
│   │   ├── scripts/             # chart/analyze/narrate/render
│   │   └── data/
│   │
│   └── README.md                # 学科状态表
│
├── synthesis/                   # 合参层
│   ├── cli.py                   # init/validate/add-divination/record-outcome/guide/selfcheck
│   ├── person.py                # 个人档案模型
│   ├── normalize.py             # 各科 analyze → 归一化占问记录
│   ├── cross_rules.py           # 合参裁决规则（五条）
│   ├── guidance.py              # 阶段性指导生成
│   ├── outcome_eval.py          # 现实回填命中率评估
│   └── README.md
│
├── tools/                       # 仓库级命令
│   ├── check.py                 # 全仓库质量门（门/历法/内核/分科/冒烟/合参/pytest）
│   ├── report.py                # 统一报告运行器（六科 chart→analyze→render→MD+HTML）
│   ├── ci_request.py            # CI：各类触发 → request.json
│   ├── ci_publish_branch.py     # CI：报告提交到 reports 分支
│   ├── ci_deliver.py            # CI：回写 issue 评论
│   ├── eval.py                  # 仓库级对齐分一览（转发各科 evaluate）
│   ├── demo.py                  # 全科演示
│   ├── mcp_router.py            # MCP JSON-RPC 路由（当前统一注册 ming）
│   ├── core_selftest.py         # 内核表自测
│   ├── text_keys_selftest.py    # JSON 键一致性自测
│   └── install.ps1              # 环境安装
│
└── docs/
    ├── ARCHITECTURE.md  ← 本文
    ├── AI-SOP.md        # 网页端 AI 取用报告标准操作手册
    ├── MIGRATION.md     # 迁移指南
    ├── YI-PLAN.md       # 总路线
    ├── CONTRACT.md      # 学科接入契约（新科参考）
    ├── CHANGELOG.md     # 仓库级变更日志
    ├── HANDOFF.md       # 现状交接
    ├── TECH-DEBT.md     # 技术债务登记
    └── samples/         # 样例报告
```

---

## 三、四段契约 Protocol

每个学科必须按四段暴露能力，段与段之间只传结构化数据。
契约定义在 `disciplines/base/protocol.py`，核心 TypedDict 与 Protocol：

| 类型 | 说明 |
|---|---|
| `ChartData` | 盘面（discipline + timestamp + input_params + chart） |
| `AnalysisData` | 推演结论（chart + factors + verdict + basis） |
| `NarrativeData` | 正文摘要（summary + reasoning + advice） |
| `Verdict` | 吉凶 + 置信度 + 描述 |

四个 runtime-checkable Protocol：

| Protocol | 方法 | 输入 → 输出 |
|---|---|---|
| `ChartProtocol` | `chart(params)` | 参数 → `ChartData`（纯确定性，无解读） |
| `AnalyzeProtocol` | `analyze(chart)` | 盘面 → `AnalysisData`（因子/判据/所本法则） |
| `NarrateProtocol` | `narrate(analysis)` | 推演 → Markdown 正文 |
| `RenderProtocol` | `render(analysis, fmt)` | 推演 → HTML/MD/JSON 报告 |

合规检查函数 `check_protocols()` 返回四段实现情况。
共享 CLI 基类 `DisciplineCLI`（`disciplines/base/cli.py`）提供统一 argparse 入口。

每段的硬性边界：

| 段 | 允许 | 禁止 |
|---|---|---|
| `chart` | 查内核表、算干支、装配盘 | 任何吉凶措辞 |
| `analyze` | 输出 `{因子, 权重, 判据, 所本法则}` | 成段中文断语 |
| `narrate` | 把分析数据翻译成人话 | 自行推断象数结论 |
| `render` | 调内核报告模板 | 自带 HTML 模板 |

---

## 四、数据流

完整的占问交付流程：

```
用户求测
   │
   ▼
[路由] SKILL.md 意图识别 → 选科
   │
   ▼
[输入] 收集所需参数（时间/方式/问题/身份）
   │
   ▼
[chart]  参数 → 盘面结构（JSON）
   │
   ▼
[analyze] 盘面 → {factors, verdict, basis, timing}
   │                              │
   ├── [narrate] ─────────────────┤→ Markdown 正文
   │                              │
   ▼                              ▼
[render]  analyze JSON → 单文件 HTML/MD 报告
   │
   ▼
[交付] 报告 + 应期日期 + 边界声明
```

合参场景：两科各自走完 chart→analyze 后，`normalize` 归一化为统一记录，
经 `cross_rules.adjudicate` 裁决再由 `guidance` 产出阶段性指导。

---

## 五、合参裁决规则

定义在 `synthesis/cross_rules.py`，核心五条：

1. **各守其位**：命定趋势节律，卜决具体一事。卜科问命域（"一生"/"命运"/"格局"等关键词）→ 判为无效输入，不参与合参。
2. **同向则确**：各科指向一致时可提升陈述强度，但不用"注定/一定"；给触发条件与时间窗。
3. **两同一异**：以两科为趋向，异向单列并给其成立条件。
4. **异向裁诸因**：先查输入是否同一时空（年界/月界/日辰口径），再查起局时间与用神选取；核对后仍分歧 → 如实并列两种趋向及触发条件。
5. **缺数据降级**：任一科缺数据 → 标记"该维度未参评"，不用其他科补位猜测。

裁决只输出结构化判定与说明，不写成段断语（解释权归解读层）。

---

## 六、依赖方向

**严格单向**：

```
disciplines → core/yishu_core          # 学科只能 import 内核
synthesis   → disciplines 的 schema      # 合参只依赖输出契约
disciplines/base → core                 # 共享层不依赖任何学科
```

禁止的依赖：

- ❌ 学科间互相 import（`liuyao` 不应 import `ming`）
- ❌ 内核 import 学科
- ❌ `disciplines/base` import 任何学科
- ❌ 学科自带第二份共用规则表（旬空/三刑/纳音/三合/卦表只能在 core 存在一份）

违反上述方向的 import 视为缺陷，评审直接驳回。

---

## 七、验收标准

### 功能验收

- `python tools/check.py` 全绿（结构/内核/断语键/冒烟/合参/分科）
- `python tools/check.py --full` 全绿（+ 案例评测 + 黑箱回归 + pytest）
- tune/holdout **分列出分**，禁止 holdout 混进 tune
- 金标准 288 例指纹 `5c6e77ee253b0ddd` 零漂移

### 结构验收

- 内核规则表 `grep` 全仓只有唯一一份
- 学科代码里没有成段断语字面量（断语进 `data/*.json`）
- 文件名不携带版本号（`run_blind_v5.py` 禁写）
- 一次性脚本进 `tools/scratch/`（已 gitignore）或写完即删

### 体验验收

- 百秒级单命令闭环（`yi liuyao cast` 或 `python scripts/yi_liuyao.py`）
- 一条命令从"所问之事"到可分享单文件报告
- README 附带真实截图与可复制命令

### 债务验收

- 无外部书源缺口（`/火珠林/卜筮正宗` 未数字化须诚实登记）
- 分数必带：集合名 + n + 是否调参
- 无"现实预测命中率 X%"类表述
- 口径变更全部登记 `docs/CHANGELOG.md`

---

## 八、内核真值表（仅此一份）

以下数据在 `core/yishu_core` 中只存在一份，学科不得复制：

| 类别 | 位于模块 |
|---|---|
| 天干地支、阴阳五行 | `symbols.py` |
| 六合六冲三合三刑六破 | `symbols.py` |
| 十二长生、墓库、进退神 | `symbols.py` |
| 纳音（沙中金等正写） | `symbols.py` |
| 三合局分组 | `symbols.py` |
| 旬空 | `symbols.py` |
| 六十四卦卦表、八宫归属 | `najia.py` / `hexagram_texts.py` |
| 纳甲支表 | `najia.py` |
| 卦辞爻辞 | `hexagram_texts.py` |
| 星煞起例（天乙/文昌/驿马等） | `shensha.py` |
| 干支历换算（节气/年界/月令/日柱） | `ganzhi_calendar.py` |
| 评分器 | `eval.py` |
| 报告 HTML kit | `report/html.py` |

曾发生过 15 张表在三个文件里各存一份且取值不一致的历史教训（详见 `docs/CHANGELOG.md` §26n）。

---

## 九、术语表

| 术语 | 含义 |
|---|---|
| 四段契约 | chart → analyze → narrate → render 的固定管线 |
| 薄适配层 | 包装已有引擎实现四段接口但不引入新断法 |
| 用神 | 卦中代表所问之事的爻位（取法：关系法则→覆盖→词典→世爻兜底） |
| 原神 | 生用神之爻（旺衰分析的核心参照） |
| 忌神 | 克用神之爻 |
| 仇神 | 克原神之神 |
| 六神 | 青龙/朱雀/勾陈/螣蛇/白虎/玄武（赋义于爻位） |
| 六亲 | 父母/子孙/官鬼/妻财/兄弟（五行生克角色） |
| 应期 | 事情应验的时间点（由盘面结构推出） |
| 格局 | 特殊爻象组合（三刑/六冲/伏吟/反吟/六合冲等） |
| 病药 | 用神之"病"（衰弱/旬空/伏藏）与"药"（生扶/填实/出伏） |
| 星煞 | 天乙贵人/文昌/桃花/驿马等辅助参照（不进主分） |
| tune | 调参案例集（允许用来校准评分器权重） |
| holdout | 未参与调参的案例集（最终评估用，禁止调参） |
| wikisource | 维基文库外部来源的 holdout 子集（永不调参） |
| 对齐分 | 引擎输出与古籍案例要点的吻合度（非现实预测率） |
| 合参 | 多科结论对齐与冲突裁决 |
| 金标准 | 固定输入的全字段行为指纹（漂移看门狗） |
| 零指纹漂移 | 拆分/搬家前后金标准完全一致的验收方法 |
| 口径 | 交界口径、子时处理等影响推演的参数选择 |
| 一卦一事 | 同一问题不重复占卜（"再三则渎"） |
