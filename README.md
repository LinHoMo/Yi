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
| **卜** | 一念之动（六爻/梅花/小六壬/择吉） | 具体一事的趋向与应期 | 一事，细颗粒 |

终局目标：对同一个人分别做命与卜的分析，再由易合参，输出阶段性指导与规划。
合参两科即可成立——命定趋势节律、卜决具体一事，不必依赖相科。

## 目录（现状即目标结构，不再另立一套）

```
Yi/                                   # 单一 git 仓库
├── AGENTS.md                         # 项目铁律：运算归代码、案例隔离、口径诚实、命名规范
├── pyproject.toml                    # 内核包 yishu-core（版本动态取自内核）
├── core/yishu_core/                  # 唯一内核：干支历、节气、纳甲、象数基元、运行时
│   ├── ganzhi_calendar.py            #   自求太阳黄经定节气；立春定年界、十二节定月令
│   ├── symbols.py                    #   15 张规则表唯一真值源（六亲生克合冲破墓纳甲八宫）
│   ├── najia.py                      #   卦名+爻位 → 该爻地支（变出支等）
│   └── calendar_check.py             #   16 项历法自检
├── disciplines/
│   ├── README.md                     # 学科状态表（谁已实现、谁只是骨架、谁不做）
│   └── liuyao/                       # 六爻纳甲 —— 唯一有实现的学科
│       ├── SKILL.md                  #   给 LLM 的执行规程
│       ├── scripts/                  #   引擎 / 思维链 / 叙事 / 报告 / 评测
│       ├── tools/check.py            #   六道质量门
│       ├── tools/golden.py           #   288 例排盘金标准（守结构性重构）
│       ├── references/ data/         #   规则文献 / 古籍案例分层
│       └── docs/HANDOFF.md           #   哪些可信、哪些不可信、还欠什么
├── synthesis/README.md               # 合参层：人的档案 + 裁决规则 + 指导输出（未实现）
└── docs/                             # YI-PLAN / LIUYAO-PLAN / CONTRACT / CHANGELOG
```

新学科怎么接，看 `docs/CONTRACT.md`（四段管线 chart→analyze→narrate→render）。

## 现在能跑什么

```bash
pip install -e .                                   # 内核包；无必需第三方依赖
cd disciplines/liuyao
python tools/check.py                              # 一条命令跑全部质量门
python scripts/liuyao_engine.py --mode coin --question "所问之事"
python scripts/liuyao_engine.py --mode coin --question "所问之事" \
       --format html --save-html outputs/report.html     # 一条命令出单文件报告
python scripts/evaluate.py --split holdout --save        # 古籍案例对齐评测
```

门户：浏览器直接打开 `disciplines/liuyao/index.html`（自包含，无 CDN、无 fetch）。

## 现在的真实水平（2026-09-22）

| 集合 | 古籍对齐分 strict | n |
|---|---|---|
| tune（参与过调参） | 94.2% | 20 |
| holdout（未参与调参） | 78.3% | 12 |
| wikisource_holdout（维基文库《增刪卜易》原本，从未参与任何调参） | **47.6%** | 37 |

应期不看召回看判别力：主应期命中 29.4%（随机基线 8.3%）、基准应支平均名次 2.19/12。

**装卦层已经和原书逐爻对上了**：从维基文库原本解析出 253 幅爻图，与内核比对
894 爻纳甲、116 例卦变、132 例世应，**0 处不合**（`tools/fetch_wikisource_cases.py`）。
差距全在断卦层：原书写明用神的 6 例引擎**一个都没取对**、吉凶方向只对 70.6%（12/17）、
主应期命中 13.5%——内部 holdout 的 78.3% / 25% 因此被证明是偏乐观的读数。

**这一堆数字此前是不可信的**：旧评分器已被删、`score.py` 读的是引擎根本不输出的字段、
案例被统一塞进 2024-06-01 并伪造月干、年柱完全不判立春。M0 把这些重建了，所以旧文档宣传的
tune 100% 不再可比。逐次口径变化见 `disciplines/liuyao/docs/CHANGELOG.md`。

**已修的 P0（2026-09-22）**：爻序约定曾在四处各存一份镜像编码（震·巽·艮·兑按"上爻在前"存、
所有代码按"自下而上"读），导致按 SKILL.md 手工喂六爻会得到错的卦。现已收进内核
`symbols.BAGUA_LINES` 单一真值源，并配 23 项断言看门狗（`tools/hexagram_check.py`，
含"恒之鼎必须动在上六且化巳"这类古籍锚点）。自己验一下：

```bash
cd disciplines/liuyao
python -c "import sys;sys.path[:0]=['scripts','../../core'];import liuyao_engine as e; \
print(e.build_hexagram_result([8,7,7,7,8,8],'占','manual',2024,6,1,10)['original_hexagram']['name'])"
# 应输出 恒（修复前输出 损）
python tools/hexagram_check.py    # 应输出 23 项通过
```

残余两例待按古籍重推（`chain case_03`、`reg_03` 的期望值仍带着镜像位次下的标定），见
`disciplines/liuyao/docs/HANDOFF.md`。

## 使用须知

- 排盘、装卦、旺衰、应期一律由代码完成，LLM 不心算（`AGENTS.md` 铁律一）
- 古籍案例库只用于测试与事后校验，不参与预测（铁律二）
- 本仓库所有分数都是**古籍案例对齐分**，衡量不了现实命中率（铁律三）。
  医疗、法律、投资、重大决策请以专业意见为准。
