# 易 · Yi

> 项目版本 **v0.0.1**｜唯一真值源 `core/yishu_core/__init__.py::__version__`
> 本仓库统一使用一个 git 版本库（仓库根即此处）。

中国传统道数的统一工程。**只做命与卜**：二者是同一套时空符号系统（阴阳·五行·干支·卦象）
的两个投影，建在一份内核上，再由"易"做跨科合参。
**相科（面相、手相、堪舆）明确不做**——不实现、不预留目录、不写占位。

## 定位

`易` 是统领级 skill，不是工具合集：

| 学科 | 输入 | 回答的问题 | 时间尺度 |
|---|---|---|---|
| **命** | 出生时空（四柱八字） | 格局与趋势：宜何业、何时起伏 | 一生，粗颗粒 |
| **卜** | 一念之动（六爻） | 具体一事的趋向与应期 | 一事，细颗粒 |

终局目标：对同一个人分别做命与卜的分析，再由易合参，输出阶段性指导与规划。
合参两科即可成立——命定趋势节律、卜决具体一事，不必依赖相科。

## 目录（现状即目标结构，不再另立一套）

```
Yi/                                   # 单一 git 仓库
├── AGENTS.md                         # 项目铁律：运算归代码、案例隔离、口径诚实、命名规范
├── pyproject.toml                    # 内核包 yishu-core（版本动态取自内核）
├── core/yishu_core/                  # 唯一内核：干支历、节气、农历、纳甲、象数基元、评分器
│   ├── ganzhi_calendar.py            #   自求太阳黄经定节气；立春定年界、十二节定月令
│   ├── lunar.py                      #   农历与公历双向转换（朔望月 + 节气定月双轨制）
│   ├── symbols.py                    #   15 张规则表唯一真值源（六亲生克合冲破墓纳甲八宫）
│   ├── eval.py                       #   全仓库唯一评分器（tune/holdout/excluded 分层）
│   └── calendar_check.py             #   16 项历法自检
├── disciplines/
│   ├── README.md                     # 学科状态表（谁已实现、谁已归档、谁不做）
│   ├── liuyao/                       # 六爻纳甲 —— 已实现（旧实现 + 四段契约薄适配层，可入合参层）
│   ├── ming/                         # 四柱八字 —— 已实现机械推演（强弱/格局/喜用/大运/流年）
│   └── （meihua / xiaoliuren / zeji 已归档至 archive/，不在当前范围）
├── synthesis/                        # 合参层（已实现）：person 档案 + 裁决规则 + 指导生成 + CLI
├── tools/                            # 仓库级命令：check / demo / install
└── docs/                             # YI-PLAN / CONTRACT / CHANGELOG / LIUYAO-PLAN
```

新学科怎么接，看 `docs/CONTRACT.md`（四段管线 chart→analyze→narrate→render）。

## 现在能跑什么

```bash
pip install -e .                                   # 内核包；无必需第三方依赖
python tools/check.py                              # 仓库根：全仓库质量门（--full 加案例评测）
python tools/demo.py                               # 仓库根：全科演示 → tools/scratch/demo.md
powershell -File tools/install.ps1 -Check -Demo    # 环境安装 + 质量门 + 演示
```

各科自检与一条命令出报告（六爻 / 命 两科接口同构）：

```bash
cd disciplines/ming          # 命科（六爻见上方 liuyao 段）
python tools/check.py                          # 该科全部质量门
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男   # 起盘
```

六爻（迁移前旧实现，已接四段契约薄适配层；工作目录 `disciplines/liuyao/`）：

```bash
cd disciplines/liuyao
python tools/check.py                              # 全部质量门
python scripts/liuyao_engine.py --mode coin --question "所问之事" \
       --format html --save-html outputs/report.html
python scripts/chart.py --mode time --datetime "2026-09-23 10:00" \
       --question "所问之事" -o scratch/chart.json        # 四段契约：起卦
python scripts/analyze.py scratch/chart.json -o scratch/analyze.json   # 推演（结论/应期/所本）
python scripts/render.py scratch/analyze.json -o outputs/report.md     # 报告
python scripts/yi_liuyao.py "所问之事" --when "2026-09-23 10:00" -o outputs/report.html   # 一键闭环（chart→analyze→render 单文件报告）
```

黄金样例与验收清单见 `disciplines/liuyao/docs/samples/`（`感情卦_巽之涣.html` 为唯一模板）。

合参层（工作目录 `synthesis/`）：`python cli.py init` 建档 → `add-divination` 登记占问
→ `guide` 生成阶段性指导 → `record-outcome` 回填现实结果。

门户：六爻浏览器直接打开 `disciplines/liuyao/index.html`（自包含，无 CDN、无 fetch；
由 `python scripts/build_portal_assets.py` 生成，产物不入库，改动前先重建）。

## 现在的真实水平（2026-09-23，strict 口径，`python tools/check.py` 全门绿复验）

| 科 | 集合 | 古籍对齐分 | n | 口径说明 |
|---|---|---|---|---|
| 六爻 | tune（参与过调参） | 94.5% | 20 | 参与过调参 |
| 六爻 | holdout（未参与调参） | **84.8%** | 12 | 未参与调参 |
| 六爻 | wikisource_holdout | **56.3%** | 35 | 维基文库《增刪卜易》原本，从未参与任何调参 |
| 梅花 / 小六壬 / 择吉 | — | 已归档（2026-09 范围收缩） | — | 历史读数见 git 历史，不再更新 |

**分数含义**：全部为**古籍案例对齐分**（引擎输出与案例库要点的吻合度），
衡量不了现实命中率（`AGENTS.md` 铁律三）；对外引用最保守集合。

**六爻应期尚不可用**：主应期命中 tune 35.3% / holdout 25.0% / 外部集 20.0%（随机基线 8.3%）。
（2026-09-23 起应期评分改**单位感知**：基准写「未月」而引擎答「未日」不再算命中，旧读数 29.4% / 17.1% 与新读数不可直接比，详见 `disciplines/liuyao/docs/CHANGELOG.md`。）
六爻其余旧读数与"装卦层逐爻对上原书"的详细说明见本文档历史版本与 `disciplines/liuyao/docs/HANDOFF.md`。

## 使用须知

- 排盘、装卦、旺衰、应期一律由代码完成，LLM 不心算（`AGENTS.md` 铁律一）
- 古籍案例库只用于测试与事后校验，不参与预测（铁律二）
- 本仓库所有分数都是**古籍案例对齐分**，衡量不了现实命中率（铁律三）。
  医疗、法律、投资、重大决策请以专业意见为准。
