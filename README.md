# 易 · Yi

> 版本号唯一真值源：`core/yishu_core/__init__.py::__version__`（不在此另写版本号）。
> 本仓库统一使用一个 git 版本库（仓库根即此处）。

## AI READ THIS FIRST

> 如果你（AI Agent）要帮用户生成术数报告（起卦/排盘/测八字/问吉凶应期），
> **不要通读本 README 的其余部分**，按下面顺序取用：
>
> 1. 读仓库根 `llms.txt`（AI 索引地图）。
> 2. 读 `docs/AI-SOP.md` 第 1 节收集该科所需字段，按**通道 A**（GitHub Pages + Pyodide
>    深链，零凭证）或通道 B（云端 Actions）触发引擎出报告。
> 3. 报告由引擎机械生成，你只负责把结构化输出翻译成用户看得懂的话；
>    **禁止 LLM 心算排盘**（`AGENTS.md` 铁律一），禁止把对齐分说成现实命中率（铁律三）。
>
> 需要"某一科怎么调"时，只加载对应 `skills/<科>/SKILL.md`，不要整目录通读。

中国传统术数的统一工程。**八科可用**：命（四柱八字 / 紫微斗数）+
卜（六爻纳甲 / 梅花易数 / 小六壬 / 择吉通书 / 大六壬骨架 / 灵棋经），八科建在同一份内核
（`core/yishu_core/`）与同一条四段契约（`docs/CONTRACT.md`）上，由"易"做跨科合参。
统一 CLI 入口 `yi <discipline> <command>`。
**相科（面相、手相、堪舆）明确不做**——不实现、不预留目录、不写占位。

> **科 × 通道能力矩阵**（权威表在 [`llms.txt`](llms.txt)，本处只引用、不复制）：
> 本地 CLI `yi`、通道 B 云端报告 `tools/report.py`
> （`yishu_core.report.request.DISCIPLINES`）、通道 A 纯前端网页
> （`web/engine_runtime.WEB_DISCIPLINES`）**均为八科全通**，无"网页只能跑几科"的落差。
> 口径：`liuren` 是骨架科（只出机械结构标签，无吉凶断语）；`lingqi` 的断语是
> 《靈棋經》原文逐字直录（无书外发挥）。

## 给网页端 AI：给链接即出报告（无需自建服务器）

把仓库传上 GitHub 后，网页端 AI 只需"仓库链接 + 起卦/排盘信息"就能取回
**Markdown + HTML** 报告，完整步骤见 [`docs/AI-SOP.md`](docs/AI-SOP.md)。

- **没有 GitHub Token**：让 AI 生成一个"预填 issue"链接、人点一下提交即可，报告会以评论回到该 issue。
- **持有 Token（`Actions: write`）**：AI 直接调 `workflow_dispatch` / `repository_dispatch` API，全程自动。
- 报告同时存入独立的 `reports` 分支，用 `raw.githubusercontent.com` **匿名读取**。

一键预填 issue（六爻示例，点击后按 Submit 即触发；可改 title/body 里的学科与参数）：

```
./issues/new?title=%5Byi%5D%20%E5%85%AD%E7%88%BB%20%C2%B7%20%E8%AF%B7%E5%A1%AB%E6%89%80%E9%97%AE&body=discipline%3A%20liuyao%0Aquestion%3A%20%E6%8A%8A%E4%BD%A0%E8%A6%81%E9%97%AE%E7%9A%84%E4%BA%8B%E5%86%99%E5%9C%A8%E8%BF%99%E9%87%8C%0Adatetime%3A%20YYYY-MM-DD%20HH%3AMM
```

> 也可直接用 GitHub 网页 "New Issue"，正文按 `discipline: ...`、`question: ...` 等行填写。

## 定位

`易` 是统领级 skill，不是工具合集：

| 学科 | 目录 | 输入 | 回答的问题 | 时间尺度 |
|---|---|---|---|---|
| **命**（四柱八字） | `disciplines/ming/` | 出生时空 | 格局与趋势：宜何业、何时起伏 | 一生，粗颗粒 |
| **命**（紫微斗数） | `disciplines/ziwei/` | 出生时空 | 星盘格局、四化与大限起伏 | 一生，分宫 |
| **卜·六爻** | `disciplines/liuyao/` | 一念之动 | 具体一事的趋向与应期 | 一事，细颗粒 |
| **卜·梅花易数** | `disciplines/meihua/` | 年月日时/报数/字画 | 一事之吉凶与象应 | 一事 |
| **卜·小六壬** | `disciplines/xiaoliuren/` | 月/日/时掌诀 | 一事之快速判断 | 一事 |
| **卜·择吉** | `disciplines/zeji/` | 日期 + 活动 | 开张/嫁娶/出行等吉凶宜忌 | 一时 |
| **卜·大六壬** | `disciplines/liuren/` | 占时 | 四课三传的机械结构（月将加时、九宗门、天将乘临）；**骨架，无吉凶断语** | 一事 |
| **卜·灵棋经** | `disciplines/lingqi/` | 三部掷数 | 查 124 课表直录《靈棋經》原断语（书源逐字，无书外发挥） | 一事 |

终局目标：对同一个人分别做命与卜的分析，再由易合参，输出阶段性指导与规划。
合参即可跨命·卜·多视角闭合，不必依赖相科。

## 给人类贡献者：入口文件导航

四个入口文件各有读者，不要混读：

| 文件 | 读者 | 什么时候读 |
|---|---|---|
| `README.md` | 所有人 | 第一眼总览（本文件） |
| `llms.txt` | 任务 AI | AI 要调用出报告时 |
| `SKILL.md` | 任务 AI | AI 要调用出报告时（§四铁律操作版） |
| `AGENTS.md` | 贡献者 / 编码 Agent | 要改代码、提交、改引擎时（铁律全文） |

## 目录

```
Yi/
├── AGENTS.md                         # 项目铁律：运算归代码、案例隔离、口径诚实、命名规范
├── README.md                         # 本文件
├── pyproject.toml                    # 内核包 yishu-core + entry point yi = cli.main:main
├── .github/workflows/
│   ├── ci.yml                        # push/PR 跑仓库级质量门（tools/check.py --full）
│   ├── report.yml                    # 云端出报告（workflow_dispatch / issues / comment / dispatch）
│   └── pages.yml                     # 通道 A 站点发布（构建 + 自检 + 网页↔本机同源验收）
├── core/yishu_core/                  # 唯一内核：干支历、节气、农历、纳甲、象数基元、评分、shensha、报告
├── disciplines/                      # 八科，每科四段契约 chart→analyze→narrate→render
│   ├── liuyao/                       # 六爻纳甲（最成熟，四段契约 + CLI）
│   ├── ming/                         # 四柱八字（机械推演）
│   ├── ziwei/                        # 紫微斗数（安星/四化/格局/大限）
│   ├── meihua/                       # 梅花易数
│   ├── xiaoliuren/                   # 小六壬
│   ├── zeji/                         # 择吉通书
│   ├── liuren/                       # 大六壬骨架（机械结构标签，无吉凶断语）
│   └── lingqi/                       # 灵棋经（124 课表查表直录书源原文）
├── cli/                              # 统一入口：yi <discipline> <command>
├── synthesis/                        # 合参层：person 档案 + 八科 normalize + 裁决规则 + 指导生成 + CLI
├── tests/                            # pytest（内核层）
├── tools/                            # check / report / build_web / eval / ci_*
└── docs/                             # AI-SOP / ARCHITECTURE / CONTRACT / CHANGELOG / HANDOFF / TECH-DEBT / AUDIT
```

新学科怎么接，看 `docs/CONTRACT.md`（四段管线 chart→analyze→narrate→render）。
架构全局视图：`docs/ARCHITECTURE.md`。迁移指南：`docs/MIGRATION.md`。

## 安装

```bash
pip install -e .    # 内核包 + 注册 yi entry point；无必需第三方依赖
```

## 怎么跑

### 统一 CLI（`yi`）

```bash
# 六爻：起卦 → 排盘 → 推演 → 叙述 → 报告
yi liuyao cast "占买房子何时有结果"
yi liuyao chart --mode coin
yi liuyao analyze chart.json
yi liuyao narrate analyze.json
yi liuyao render analyze.json

# 四柱八字 / 紫微斗数
yi ming chart --datetime "1990-05-20 10:30" --gender 男
yi ming analyze chart.json
yi ziwei chart --datetime "1990-05-20 10:30" --gender 男
yi ziwei analyze chart.json

# 梅花易数 / 小六壬 / 择吉
yi meihua cast "占投资"
yi xiaoliuren cast "占出行"
yi zeji chart --date "2026-10-08" --activity 开市
```

### 一条命令统一出 Markdown + HTML（八科通用，云端同款）

```bash
python tools/report.py --discipline liuyao --question "占买房子何时有结果" \
    --datetime "2026-09-30 10:30" --outdir reports
python tools/report.py --request request.json --outdir reports   # request.json 字段见 docs/AI-SOP
```

>`yi` 由 `pyproject.toml` 的 `[project.scripts]` 注册，安装后全局可用。

## 质量门与评测

```bash
python tools/check.py              # 仓库根：全仓库质量门（--full 加案例评测）
python tools/check.py --full       # + 黑箱回归 + pytest
python -m pytest tests -q          # 单测
python tools/demo.py               # 全科演示

# 各科自检（工作目录为学科根）
disciplines/<科>  → python dev_tools/check.py
```

合参层（工作目录 `synthesis/`）：`python cli.py init` 建档 → `add-divination` 登记占问
→ `guide` 生成阶段性指导 → `record-outcome` 回填现实结果。

## 现在的真实水平

> 本表**只镜像读数，不定义读数**。分数与口径的单一真值源是各科
> `docs/EVAL-AUDIT.md` 与 `docs/HANDOFF.md` §一；两处不一致时以它们为准，
> 并把本表改回来。报告在报分时也会自动打印 `[口径披露]`（集合名 / n / 是否调参）。

**六爻**（`dev_tools/check.py` 全绿，strict 口径）

| 集合 | n | 古籍对齐分 | 是否调参 |
|---|---|---|---|
| tune | 20 | **96.8** | 参与过调参 |
| holdout | 12 | **90.2** | 未参与调参 |
| wikisource_holdout | 44 | **60.8** | 永不调参（维基文库《增刪卜易》原本，泛化短板；strict 均分，应期 top-1 21.1%，读数 2026-10-08；扩样 35→44 见 `69823f2`） |
| wikisource_direction | 36 | **72.2** | 有吉凶无应期 |

六爻应期：主应期 top-1 tune **58.8%**（n=20）/ holdout **50.0%**（n=12）/
wikisource **21.1%**（n=44，读数 2026-10-08），
日/月/年分列已输出（`disciplines/liuyao/dev_tools/check.py`）。
黑箱回归 18 例 **11/18**（基线 ≥11）。

**梅花易数 / 小六壬 / 择吉**：**这三科目前没有古籍对齐分**（梅花例外，见下）。
逐例审计（各科 `docs/EVAL-AUDIT.md`，一键复核 `python tools/eval_audit_recheck.py`）
结论：小六壬/择吉读数性质是**规则自洽回归数**——expected 与引擎口径
同源（择吉 16 例全部 engine_derived，古籍日例应验 0 例）。对外请照此写法、**带 n 不带百分比**：
*规则自洽回归数：小六壬与择吉各维度 n/n 命中*（n 均 < 20）。
梅花已有古籍对齐评测（tune 10 / holdout 13），并于 2026-10-02r 起另有
**外部独立集 external_holdout n=4**（《梅花易数·卷三·變卦式八則》，永不调参；
n<20 按纪律只报命中数：relation 4/4、革卦生克体 1/1，**不报百分比**）。
**想让小六壬/择吉真正可检验，唯一有效动作是建外部独立集**（范式照梅花 4 例与六爻 wikisource 35 例）。

**命科**：四柱八字有案例对齐评测——调候 tune 100.0（30/30）、holdout **strict 97.1**
（n=246；含格局成败 28/36、从格 13/15、from_kind 15/15，2026-10-02t 读数），
性质是**表对表回归 + 历法链路验证，不是泛化证据**；外部独立集（书源基准例）
**尚未建立**——该缺口在册（《滴天髓阐微》语料已取得，判据待落地）。
紫微斗数、大六壬、灵棋经**无案例对齐评测**，只有机械自检与行为指纹（`dev_tools/golden.py`）。

**评测成熟度分层**（机器可读权威表：`core/yishu_core/execution/registry.py`，
此处只引用）：liuyao / ming / meihua 为 **classical_holdout**（古籍案例对齐评测已建，
liuyao/meihua 另有外部独立候选集）；ziwei / xiaoliuren / zeji / liuren 为
**mechanical_regression**（只有规则自洽回归与 golden 指纹）；lingqi 为
**source_only**（书源直录，忠实度门即其基线）。四类评测口径——
机械回归 / 古籍对齐（source alignment）/ 外部独立集（external holdout）/
现实回填反馈（outcome feedback，当前 n=0 开环）——**不得互相冒充**
（`AGENTS.md` 铁律三）。

**证据链与 Agent 入口**（2026-10-03 起）：报告 envelope 附带结构化证据
（`core/yishu_core/evidence.py`：每条结论带规则 id / 出处 / 适用条件 / 观察 / 评测状态）；
六爻规则注册表（书源引文指针 + 评测覆盖）在
`disciplines/liuyao/data/rules/rule_registry.json`；现实反馈经 canonical 模型
`core/yishu_core/feedback.py` 统一折叠（synthesis 与六爻两条链共用 adapter）；
程序化 Agent 用 `core/yishu_core/agent.py` 的五入口，不直接拼脚本命令。

**分数含义**：古籍案例对齐分 = 引擎输出与案例库要点的吻合度，
衡量不了现实命中率（`AGENTS.md` 铁律三）；对外引用最保守集合。

## 使用须知

- 排盘、装卦、旺衰、应期一律由代码完成，LLM 不心算（`AGENTS.md` 铁律一）
- 古籍案例库只用于测试与事后校验，不参与预测（铁律二）
- 本仓库所有分数都是**古籍案例对齐分**，衡量不了现实命中率（铁律三）。
  医疗、法律、投资、重大决策请以专业意见为准。
