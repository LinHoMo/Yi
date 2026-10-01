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

中国传统术数的统一工程。**六科可用**：命（四柱八字 / 紫微斗数）+
卜（六爻纳甲 / 梅花易数 / 小六壬 / 择吉通书），六科建在同一份内核
（`core/yishu_core/`）与同一条四段契约（`docs/CONTRACT.md`）上，由"易"做跨科合参。
统一 CLI 入口 `yi <discipline> <command>`。
**相科（面相、手相、堪舆）明确不做**——不实现、不预留目录、不写占位。

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

## 给本地 AI 客户端：MCP（stdio，零第三方依赖）

本地 AI 客户端（Claude Desktop / Cursor 等）可直接把 `tools/mcp_router.py` 配为
MCP Server 调用引擎——不需要 GitHub、不需要复制提示词。启动与配置见
[`mcp-server/README.md`](mcp-server/README.md)；当前注册命科 `ming`
（chart/analyze/narrate/render），其余科按同一模式接入。

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
├── .github/workflows/report.yml      # 云端出报告（workflow_dispatch / issues / comment / dispatch）
├── core/yishu_core/                  # 唯一内核：干支历、节气、农历、纳甲、象数基元、评分、shensha、报告
├── disciplines/
│   ├── base/                         # 共享层：protocol.py（四段契约）+ cli.py（CLI 基类）
│   ├── liuyao/                       # 六爻纳甲（最成熟，四段契约 + CLI）
│   ├── ming/                         # 四柱八字（机械推演）
│   ├── ziwei/                        # 紫微斗数（安星/四化/格局/大限）
│   ├── meihua/                       # 梅花易数
│   ├── xiaoliuren/                   # 小六壬
│   └── zeji/                         # 择吉通书
├── cli/                              # 统一入口：yi <discipline> <command>
├── synthesis/                        # 合参层：person 档案 + 六科 normalize + 裁决规则 + 指导生成 + CLI
├── tools/                            # check / eval / demo / install / report / mcp_router / ci_*
└── docs/                             # AI-SOP / ARCHITECTURE / CONTRACT / CHANGELOG / HANDOFF / TECH-DEBT
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

### 一条命令统一出 Markdown + HTML（六科通用，云端同款）

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

## 现在的真实水平（六科 `dev_tools/check.py` 全绿）

| 科 | 集合 | 古籍对齐分 | n | 口径说明 |
|---|---|---|---|---|
| 六爻 | tune（参与过调参） | 93.9% | 20 | 参与过调参 |
| 六爻 | holdout（未参与调参） | **87.5%** | 12 | 未参与调参 |
| 六爻 | wikisource_holdout | **57.3%** | 35 | 维基文库《增刪卜易》原本，从未参与调参（泛化短板） |
| 六爻 | wikisource_direction | **72.2%** | 36 | 有吉凶无应期 |
| 梅花易数 | tune+holdout | **100%** | 10+8 | 古籍案例对齐分 |
| 小六壬 | tune+holdout | **100%** | 15 | 古籍案例对齐分 |
| 择吉 | tune+holdout | **100%** | 5+5 | 古籍案例对齐分 |
| 四柱八字 | — | 机械回归通过 | — | 无案例对齐评测，仅校验机械因子 |
| 紫微斗数 | — | 机械自检通过 | — | 安星/四化/格局/大限，无案例对齐评测 |

**分数含义**：全部为**古籍案例对齐分**（引擎输出与案例库要点的吻合度），
衡量不了现实命中率（`AGENTS.md` 铁律三）；对外引用最保守集合。

六爻应期：主应期 top-1 tune **58.8%** / holdout **50.0%** / wikisource **20%**，
日/月/年分列已输出。详见 `disciplines/liuyao/docs/HANDOFF.md`。

## 使用须知

- 排盘、装卦、旺衰、应期一律由代码完成，LLM 不心算（`AGENTS.md` 铁律一）
- 古籍案例库只用于测试与事后校验，不参与预测（铁律二）
- 本仓库所有分数都是**古籍案例对齐分**，衡量不了现实命中率（铁律三）。
  医疗、法律、投资、重大决策请以专业意见为准。
