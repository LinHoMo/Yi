# 易 · 架构总览（v1.0）

> 本文描述当前仓库的最终架构状态——不保留已过时的里程碑过程叙事（可查 git 历史）。
> 操作纪律见 `AGENTS.md`；口径变更史见 `docs/CHANGELOG.md`。
> **现状读数（各科分数与 n、scripts 行数、案例数、金标准指纹）唯一权威源是 `docs/HANDOFF.md`**；
> 科 × 三通道能力矩阵唯一权威表是 `llms.txt`。本文对上述事实**只引用、不复制**（见 §七「文档读数纪律」）。
> 输入→输出的系统工程分析：最新为 `docs/ARCHITECTURE-REVIEW.md`（上一版 `docs/SYS-REVIEW.md`）；
> 目标态架构图：`.archify/architecture-yi-20261001-182134/`。

---

## 一、系统定位

易是命、卜两科的统一 skill：一份内核 + 若干学科适配层 + 一个合参层。
差异化不在「算得准」，而在多科结论如何对齐、冲突如何裁决、如何落成可执行建议。

| | 输入 | 回答 | 时间尺度 |
|---|---|---|---|
| **命** | 出生时空（公历年月日时 + 性别） | 格局与趋势（机械推演，不作命运断语） | 一生 |
| **卜** | 一念之动（所问之事 + 起卦方式） | 一事成败与应期 | 一事 |

**范围（八科）**：命科 = `ming`（四柱八字）+ `ziwei`（紫微斗数）；
卜科 = `liuyao`（六爻纳甲）+ `meihua`（梅花易数）+ `xiaoliuren`（小六壬）+ `zeji`（择吉）
+ `liuren`（大六壬骨架）+ `lingqi`（灵棋经）。

学科清单的唯一权威源是 `core/yishu_core/report/request.py::DISCIPLINES`（八科元组）；
**科 × 本地 CLI / 通道 A 网页 / 通道 B 云端**三通道的能力矩阵见 `llms.txt`（本文件只引用不复制）。
梅花、小六壬、择吉曾于 2026-09 归档，2026-09-29 已还原至 `disciplines/`；
`liuren` / `lingqi` 为两个**骨架科**——liuren 只出月将加时／九宗门三传／天将乘临的机械结构标签、**无吉凶断语**，
lingqi 断语为《靈棋經》原文**逐字直录**、无书外发挥。
云端出报告见 `.github/workflows/report.yml` 与 `docs/AI-SOP.md`。
相科（面相、手相、堪舆）明确不做。

---

## 二、目录结构

```
Yi/
├── AGENTS.md                # 项目铁律（运算归代码·案例隔离·口径诚实）
├── SKILL.md                 # 统领 skill：意图路由 + 选科 + 调用监督 + 合参入口
├── README.md                # 面向用户的介绍
├── llms.txt                 # AI 索引地图 + **能力矩阵唯一权威表**（科 × 三通道）
├── PROMPTS.md               # 面向用户的复制粘贴提示词
├── pyproject.toml           # 项目配置（yishu-core 包 + pytest）
├── .github/workflows/       # report.yml（云端出报告）+ pages.yml（站点发布）
├── .archify/                # 架构图产物（目标态：architecture-yi-20261001-182134/）
│
├── core/
│   └── yishu_core/          # 唯一真值源
│       ├── ganzhi_calendar.py   # 太阳视黄经→节气→干支历
│       ├── symbols.py          # 干支五行/生克/六合六冲/三合三刑/十二长生/纳音
│       ├── shensha.py          # 星煞起例与安星函数（命·卜共用）
│       ├── najia.py            # 纳甲支表/八宫归属/安世应
│       ├── relations.py        # 五行关系/六亲/生克指数
│       ├── ming_tables.py      # 藏干十神/大运起法/命宫身宫（仅命科）
│       ├── ziwei_tables.py     # 紫微斗数安星表（仅命科）
│       ├── liuren_tables.py    # 大六壬月将/天将表（仅卜科）
│       ├── zeji_tables.py      # 择吉建除/黄黑道/二十八宿表（仅卜科）
│       ├── hexagram_texts.py   # 六十四卦卦辞爻辞
│       ├── lunar.py            # 公历↔农历互转
│       ├── eval.py             # 全仓库唯一评分器
│       ├── evidence.py         # Evidence Contract：analyze→结构化证据派生视图（唯一实现）
│       ├── feedback.py         # canonical FeedbackRecord：synthesis/六爻反馈 adapter（判定真值源仍 yingqi）
│       ├── agent.py            # Agent API 稳定最小五入口（capabilities/validate/run/evidence/status）
│       ├── golden_kit.py       # 金标准指纹 kit（机械层 / 措辞层分列）
│       ├── gate_kit.py         # 学科质量门共享壳（子进程 / 取指标 / 跑一套评测）
│       ├── runtime.py          # UTF-8 子进程/控制台适配
│       ├── calendar_check.py   # 历法自检
│       ├── execution/          # 统一执行入口 (YiRuntime)
│       │   ├── runtime.py      # YiRuntime: execute() / chart() / analyze()
│       │   ├── schemas.py      # TypedDict: RequestEnvelope / ChartEnvelope / AnalysisEnvelope / ResultEnvelope
│       │   └── registry.py     # 学科能力注册表（能力性质 + 评测基线 + evaluation_splits 唯一真值源）
│       └── report/             # 报告 kit + 输入协议
│           ├── request.py      # 请求→命令行参数唯一映射（DISCIPLINES 八科元组）
│           └── html.py         # HTML/MD 报告模板
│
├── disciplines/                 # 八科；各科 scripts/ **同名**（每科都有 chart.py），浏览器内隔离见 web/
│   ├── liuyao/                  # 六爻纳甲（卜科）——四段入口 + 域模块，共 37 个 scripts
│   │   ├── SKILL.md
│   │   ├── scripts/             # 四段入口 chart/analyze/narrate/render.py
│   │   │   ├── liuyao_step{1-5}.py        # 主流程（装卦→分析→应期）
│   │   │   ├── classical_enhancements.py / classical_analysis.py / classical_enhancements_dufa.py
│   │   │   ├── effects.py / chart_tables.py / chain_tables.py / narrative_rules.py
│   │   │   ├── liuyao_engine.py / liuyao_analyze.py / liuyao_narrate.py / liuyao_timing.py
│   │   │   ├── thinking_chain.py / narrative_utils.py / advice_framework.py
│   │   │   ├── evaluate.py / case_runner.py / event_logger.py / yi_liuyao.py
│   │   │   └── …（逐文件清单与行数见 `docs/HANDOFF.md` §之一）
│   │   ├── references/          # 知识库（case_library.md 属铁律二隔离标的）
│   │   ├── data/                # 数据层（verdicts/cases/rules/golden）
│   │   ├── dev_tools/           # 学科级门（check/golden/regression/refactor_guard 等）
│   │   └── guard/               # 重构指纹基线（零漂移验收）
│   │
│   ├── ming/                    # 四柱八字（命科）：scripts + references + data + dev_tools
│   ├── ziwei/                   # 紫微斗数（命科）：scripts + data + dev_tools
│   ├── meihua/ xiaoliuren/ zeji/   # 卜科薄科（各 7 个 scripts）
│   ├── liuren/ lingqi/          # 卜科骨架科（liuren 7 / lingqi 4 个 scripts）
│   └── README.md                # 学科状态表
│
├── synthesis/                   # 合参层（只依赖各科 analyze 输出契约）
│   ├── cli.py                   # init/validate/add-divination/record-outcome/outcome-eval/evidence-cross/guide/selfcheck
│   ├── person.py                # 个人档案模型
│   ├── normalize.py             # 各科 analyze → 归一化占问记录
│   ├── cross_rules.py           # 合参裁决规则实现（五类；方向级裁决权在此）
│   ├── evidence_cross.py        # 证据级检视：same/conflict/unassessed（兼容层，不替代五类裁决）
│   │                            #   → 已内嵌 guidance 主合参文档（two_one 降为方向级计数倾向）
│   ├── guidance.py              # 阶段性指导生成
│   ├── outcome_eval.py          # 现实回填命中评估（当前 n=0，开环）
│   └── README.md                # **裁决规则唯一权威表**（§二）
│
├── cli/                         # 统一命令行入口：`yi <discipline> <command>`
│
├── web/                         # 通道 A 纯前端站点源（零凭证；Pyodide 内跑同一份引擎）
│   ├── index.html / web.css / web.js   # 页面 / 样式 / 深链解析
│   ├── engine_runtime.py        # 浏览器侧执行器（同进程 runpy；`WEB_DISCIPLINES` 白名单）
│   └── DESIGN.md
│
├── tools/                       # 仓库级命令
│   ├── check.py                 # 全仓库质量门（[0]-[8]，含 [0b]/[1b]-[1g] 全部机检）
│   ├── case_isolation_check.py  # [1g] 案例库隔离（铁律二：import 闭包 BFS + 审计 hook 实跑）
│   ├── report.py                # 统一报告运行器（八科 chart→analyze→render→MD+HTML）
│   ├── report_faithfulness.py   # 叙事忠实度审计（invented / contradicted 即失败）
│   ├── verdict_audit.py         # 断语外置取证（跑真实报告反查）
│   ├── verdict_consumption.py   # 语料消费审计（语料池 ⊆ 被消费；报告制）
│   ├── request_protocol_golden.py  # 输入协议指纹
│   ├── fetch_source.py          # 唯一外部书源采集器（字符级保存 + provenance）
│   ├── build_web.py / serve_web.py / check_web_site.py / verify_web_parity.py  # 站点构建/预览/自检/同源验收
│   ├── ci_request.py / ci_publish_branch.py / ci_deliver.py  # CI 触发 / 发布 / 回评
│   ├── eval.py / eval_audit_recheck.py   # 对齐分一览 / 三科口径复核
│   ├── demo.py / core_selftest.py / text_keys_selftest.py / doc_html.py
│   └── install.ps1              # 环境安装
│
├── tests/                       # pytest（内核与跨科回归）
├── skills/<科>/SKILL.md         # 面向 AI 的技能层（渐进式披露，被 llms.txt 索引）
├── data/                        # 仓库级数据：sources/（外部书源 + provenance）、golden/（协议指纹）
├── archive/                     # 归档（如 AUDIT.md 过程档）
└── docs/
    ├── ARCHITECTURE.md          # ← 本文（架构总览）
    ├── ARCHITECTURE-REVIEW.md   # 最新系统工程评审（改进项 A1–A11）
    ├── SYS-REVIEW.md            # 上一版评审（含「三之一、落地状态」表）
    ├── AI-SOP.md                # 网页端 AI 取用报告标准操作手册
    ├── CONTRACT.md              # 学科接入契约（新科参考）
    ├── HANDOFF.md               # 现状交接（**现状读数唯一权威源**）
    ├── CHANGELOG.md             # 仓库级口径变更登记
    ├── TECH-DEBT.md             # 技术债务登记
    ├── MIGRATION.md / YI-PLAN.md / DEEP-DIVE-PLAN.md / NEW-DISCIPLINES.md / RESEARCH-HOROSA.md
    ├── LIUYAO-PLAN.md                   # 六爻路线
    └── samples/                 # 样例报告
```

> 历史过程规格（2026-09 的 `compose/spec/`，读数已过期、勿当现状引用）已移入 `archive/compose-spec/`。

---

## 三、YiRuntime 统一执行入口

`core/yishu_core/execution/` 是所有宿主调用 Yi 引擎的唯一入口：

```
User / Agent
    │
    ▼
Skill / CLI / Web / Actions
    │
    ▼
YiRuntime (统一入口)
    │
    ▼
Request → discipline routing → chart → analyze → render → Result
```

**原则**：CLI / Web / Actions 不再各自拼接命令行参数或起子进程，
统一通过 `YiRuntime.execute(request)` 进入引擎。
Runtime 负责 discipline routing、request normalization、provenance、
结果封装（schema_version + engine_version + envelope）。

### 数据契约（TypedDict）

`execution/schemas.py` 定义最小稳定 schema：
- `RequestEnvelope`: 入口请求（discipline/question/datetime/.../up/mid/down/seed）
- `ChartEnvelope`: 盘面结构
- `AnalysisEnvelope`: 分析结果（verdict/signal_strength/factors/...）
- `ResultEnvelope`: 最终输出（markdown/html/chart/analysis/provenance）
- `SCHEMA_VERSION = "1.0.0"`

**字段命名**：`signal_strength`（0-100 整数，信号一致性得分，**非概率**）替代原 `confidence`
以避免被用户理解为发生概率。保留 `confidence` 作为 deprecated 别名。

### 学科能力矩阵

`execution/registry.py` 维护每个学科的 capability：
- `chart / analyze / evidence / render / narrate / mcp / external_evaluation / holdout / synthesis / source_provenance / outcome_feedback`
- 能力性质：`stable / experimental / mechanical_only / source_only / unavailable`
- **评测基线**（EvaluationBaseline，2026-10-03 起两级分离）：`classical_holdout / external_holdout / mechanical_regression / source_only / unassessed`——能力性质回答"这是什么"，评测基线回答"有没有独立评测覆盖"，两者不得混用；分数读数不进注册表（唯一权威源 `docs/HANDOFF.md` §一）
- `evaluation_splits`：该科已建的评测分列名（结构事实）
- 唯一真值源，CLI / Web / Actions / 文档均从此引用

### 证据链（2026-10-03 收敛）

目标链路 Source → Rule → Engine → Evidence → Evaluation → Synthesis → Narrative
的各段责任与落点：

| 段 | 落点 | 输入 → 输出 |
|---|---|---|
| Source | 各科 `data/*.json`、`references/`、语料构建器 | 古籍文本 → 结构化引文/判据表 |
| Rule | 学科规则表（如六爻 `data/rules/rule_registry.json`、`verdict_texts.json`） | rule_id → 出处指针/适用条件/评测覆盖 |
| Engine | 学科 `scripts/` 四段 + core 表 | 盘面 → analyze JSON（verdict/factors/应期…） |
| Evidence | `core/yishu_core/evidence.py`（唯一实现，纯函数双宿主共用） | analyze JSON → 结构化证据（rule_id/出处/适用条件/观察/评测状态/provenance） |
| Evaluation | 各科 `evaluate.py` + `yishu_core.eval` + 注册表评测基线 | 证据/案例 → 对齐分与覆盖状态（口径分层：机械回归/古籍对齐/外部集/现实回填） |
| Synthesis | `synthesis/cross_rules.py`（方向级裁决）+ `evidence_cross.py`（证据级 same/conflict/unassessed）+ `feedback.py` adapter | 多科证据 → 一致性/冲突/缺口清单与 canonical 反馈记录 |
| Narrative | `narrate/render` + LLM 翻译 + `core/yishu_core/agent.py` 五入口 | 证据与裁决 → 当事人可读报告（LLM 只翻译不推断） |

纪律：Evidence 是**派生视图**，不改动 analyze 输出 schema（golden 零漂移）；
LLM 推断永远不进 Evidence；没有评测覆盖的证据显式标 `unassessed`/`source_only`。

---

## 四、四段契约 Protocol

每个学科必须按四段暴露能力，段与段之间只传结构化数据。
契约由 `docs/CONTRACT.md` 定义，强制手段是**机械验收**而非运行时类型检查：
根 `tools/check.py` 结构门（四段入口文件齐全）+ 各科 `dev_tools/golden.py`
黄金回归 + `tools/report_faithfulness.py` 叙事忠实度审计。

> 历史备注：本节原先定义于 `disciplines/base/protocol.py` 的运行时
> TypedDict/Protocol（ChartData/AnalysisData/ChartProtocol 等）与
> `base/cli.py` 的 DisciplineCLI 基类。二者全仓零引用（学科脚本各自用
> argparse 直接实现四段入口，CLI 由 `cli/main.py` subprocess 透传编排），
> 属闲置抽象，2026-10-01 删除（见 `docs/CHANGELOG.md`）。下表的**语义契约**
> 与每段硬性边界继续有效，验收以机械门为准。

每段的硬性边界：

| 段 | 允许 | 禁止 |
|---|---|---|
| `chart` | 查内核表、算干支、装配盘 | 任何吉凶措辞 |
| `analyze` | 输出 `{因子, 权重, 判据, 所本法则}` | 成段中文断语 |
| `narrate` | 把分析数据翻译成人话 | 自行推断象数结论 |
| `render` | 调内核报告模板 | 自带 HTML 模板 |

---

## 五、数据流

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

## 六、合参裁决规则

定义在 `synthesis/cross_rules.py`，核心五条：

1. **各守其位**：命定趋势节律，卜决具体一事。卜科问命域（"一生"/"命运"/"格局"等关键词）→ 判为无效输入，不参与合参。
2. **同向则确**：各科指向一致时可提升陈述强度，但不用"注定/一定"；给触发条件与时间窗。
3. **两同一异**：以两科为趋向，异向单列并给其成立条件。
4. **异向裁诸因**：先查输入是否同一时空（年界/月界/日辰口径），再查起局时间与用神选取；核对后仍分歧 → 如实并列两种趋向及触发条件。
5. **缺数据降级**：任一科缺数据 → 标记"该维度未参评"，不用其他科补位猜测。

裁决只输出结构化判定与说明，不写成段断语（解释权归解读层）。

---

## 七、依赖方向

**严格单向**：

```
disciplines/<科> → core/yishu_core            # 学科只能 import 内核
synthesis        → disciplines 的 schema       # 合参只依赖输出契约，不依赖其内部实现
cli/main.py      → core/yishu_core.execution.YiRuntime  # 统一 CLI 走 Runtime
web/engine_runtime.py → tools/report.py        # 浏览器侧同进程跑同一份引擎
```

学科之间禁止互相 import（违反此方向视为缺陷，评审直接驳回）。

禁止的依赖：

- ❌ 学科间互相 import（`liuyao` 不应 import `ming`）
- ❌ 内核 import 学科
- ❌ 学科自带第二份共用规则表（旬空/三刑/纳音/三合/卦表只能在 core 存在一份，
  含"改名副本"——内容指纹检测由根 `check.py` 强制）
- ❌ 请求 → 命令行参数的映射各写一份（唯一份在 `core/yishu_core/report/request.py`，
  本机/CI 子进程、浏览器同进程两个执行器共用）

---

## 八、验收标准

### 功能验收

- `python tools/check.py` 全绿（结构/内核/断语键/冒烟/合参/分科）
- `python tools/check.py --full` 全绿（+ 案例评测 + 黑箱回归 + pytest）
- tune/holdout **分列出分**，禁止 holdout 混进 tune
- 各科金标准行为指纹零漂移（**当前值见 `disciplines/<科>/data/golden/digest.json`**，八科汇总见 `docs/HANDOFF.md`）
- **能力矩阵三通道一致**：本地 CLI / 通道 A 站点 / 通道 B Actions **均挂载全部八科、无落差**——权威表在 `llms.txt`，由 `[1e]` 矩阵锁与 `[7c]` 同源验收共同看住
- 质量门清单（唯一真值源 `tools/check.py` 的输出编号，默认档与 `--full` 档之差见各门 `fast=False` 标注）：
  `[0]` 版本一致性 / **`[0b]` 读数锚点（报告制，不阻断）** / `[1]` 结构契约 / `[1b]` 命名与断语规范 /
  `[1c]` 断语外置取证 / `[1d]` 语料消费审计 / `[1e]` 能力矩阵锁 / `[1f]` 输入协议指纹 /
  **`[1g]` 案例库隔离（铁律二）** / `[2]` 内核自检 / `[3]` ming 门 / `[4]` ziwei 门 /
  `[5]` 八科行为指纹 / `[6]` 六爻（含黑箱回归）/ **`[6b]` 报告契约（render 段：结构断言 + 八科 MD 内容指纹）** /
  `[7]` 合参层 / `[7b]` 站点构建 / `[7c]` 同源验收（MD/HTML/**Evidence** 三列逐例）/
  **`[7d]` 各科案例对齐分一览（口径披露）** / `[8]` pytest
- `[1g]` 把**铁律二从「文档承诺」变成「机械可达」**（此前它是三条铁律里唯一零机械支撑的一条）：
  `tools/case_isolation_check.py` 静态层做四段契约入口的 **import 闭包 BFS + AST 判据**，
  运行层用 `sys.addaudithook` 记录真实 `open`，在受控子进程里实跑一份解读请求，
  断言未打开 `data/cases/**` 或 `references/case_library.md`；判败制（铁律不容「报告制」）。
  **覆盖边界（不美化）**：不覆盖 `tools/report.py` / `cli/` / `synthesis/` / `web/` 的源码，
  不覆盖非四段入口的解读脚本（如六爻 `scripts/yi_liuyao.py`），也不覆盖学科脚本**自起子进程**读文件的情形；
  白名单仅 4 个具名落点（`scripts/case_runner.py`、`scripts/evaluate.py`、`dev_tools/`、`tests/`）。

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

### 文档读数纪律（架构评审改进项 A8）

「现状读数」型事实**每类只允许有一个权威源**，其余文档一律写「见 X」引用句，**禁止内联复制**：

| 事实类别 | 唯一权威源 |
|---|---|
| 科 × 三通道能力矩阵、通道挂载集合 | `llms.txt` |
| 各科分数与 n、scripts 文件数与行数、案例数、外部集 n | `docs/HANDOFF.md` |
| 金标准行为指纹（机械层 / 措辞层） | `disciplines/<科>/data/golden/digest.json` |
| 合参裁决规则 | `synthesis/README.md` §二（实现见 `synthesis/cross_rules.py`） |
| 学科清单 | `core/yishu_core/report/request.py::DISCIPLINES` |
| 口径变更历史 | `docs/CHANGELOG.md` |

引用行数/分数等读数时必须带**读数时点**（评审发现同一指纹曾在库里有两个值，见 `docs/ARCHITECTURE-REVIEW.md` A8）。

### 读数锚点（架构评审改进项 A11 · 与 A8 互引）

**A8 管「读数只有一份」，A11 管「这一份读数属于哪个 revision」**——同一件事的两面，必须成对使用：

- **`[0b]` 读数锚点**（`tools/check.py::print_worktree_drift`，阈值 `DRIFT_THRESHOLD = 50`，**报告制、不阻断**）：
  在门输出顶部显式声明「下述所有门的读数一律取自**工作树**，不等于任何已提交 revision」。
- 工作树偏离 HEAD 超过阈值时，**以 revision 为锚的取证会失败或说谎**
  （如 archify repository-evidence 的文件/行号校验）→ **引用行号前先 commit，或显式声明描述的是工作树**。
- 结论：本文件与 `docs/HANDOFF.md` 的一切读数都是**工作树读数（须带时点）**，不是 HEAD 读数；
  门输出里的「226 处偏离」是**读数状态**，不是失败项。

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

### 八之一、合法分层：「取值层在 core / 引文层在学科 data」

真值源门只拦**取值**复制；以下分层不是违例，是登记在案的合法模式（防止未来误伤）：

- **命科调候**：取值层 `core.yishu_core.ming_tables.TIAO_HOU`（51 格有明文者，
  引擎查表用的就是它）；引文层 `disciplines/ming/data/tiaohou_quotes.json`
  （120 格逐格《穷通宝鉴》原文，只供报告引用），由 `dev_tools/build_tiaohou.py`
  从 `data/sources/qiong-tong-bao-jian.wikitext.txt` 生成。
- **命科格局**：判据逻辑在 `disciplines/ming/scripts/pattern.py`（透干十神有无），
  书源引文在 `disciplines/ming/data/verdicts.json`（`格局成败引文`/`从格引文`）。
- **大六壬**：门类取值在 `core.yishu_core.liuren_tables` + `scripts/jiuzongmen.py`，
  诀文引文在 `disciplines/liuren/data/verdicts.json` 与 `data/kemu.json`。

判据：**引擎判定读哪份，哪份就是取值层**（必须唯一）；书源引文、出处标注、
逐格原文属于引文层（可以整份只存于学科 data，不进 core）。

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
