# 易（Yi）

> **能力边界一页看清**：[`CAPABILITY.md`](CAPABILITY.md)（T1 排盘已验证／T2 古籍忠实已量化含上限／
> **T3 现实预测不可测、不声称**）；治理面（哪些门在守什么）见 [`GOVERNANCE.md`](GOVERNANCE.md)。

本仓库只保留两个**相互独立、零耦合**的术数学科，各自携带一套完整可运行的实现：

| 目录 | 学科 | 说明 |
|------|------|------|
| `liuyao/` | 六爻（纳甲） | 六爻纳甲起卦、装卦、旺衰、应期、断语 |
| `bazi/`  | 八字（四柱） | 四柱排盘、格局、强弱、喜用、大运、流年 |

## 设计原则

- **无共享内核、无合参层**：两科之间没有任何相互 import，也不存在把六爻与八字整合分析的层（`synthesis` 已移除）。
- **各带私有引擎副本**：每一科目录下都有自己的 `core/yishu_core/`（干支、五行、纳甲、日历、神煞、表驱动判据等），因此两科可各自独立运行、独立优化，互不影响。
- **各自自包含**：每科目录内均有 `scripts/`（机械推演）、`data/`（案例、古籍底本、规则）、`references/`、`dev_tools/`、`docs/`，并自带 `README.md` 与 `SKILL.md`。**一处不一致要说清**：`tests/` 目前**只有六爻有**（`liuyao/tests/`）；八字侧**没有 `tests/` 目录**，其回归/冒烟/回验全部走 `bazi/dev_tools/`（`check.py`，小节号会随门禁增补变化，故此处**不写死区间**——此前写 `[0]–[21]` 时 `[22]`／`[23]`／`[24]` 已存在，属本行自禁的那类"文档里的旧真值"，2026-10-13 按实改正；现行全量以 `python bazi/dev_tools/check.py` 实跑输出为准）。本行此前写作两科均有 `tests/`，与实际不符（2026-10-12 按 `ls -d bazi/tests` 实跑更正：`No such file or directory`）。

## 目录结构

```
Yi/
├── README.md          # 本文件
├── liuyao/            # 六爻（独立）
│   ├── core/yishu_core/   # 六爻私有的引擎副本
│   ├── scripts/ data/ references/ dev_tools/ docs/ tests/
│   └── README.md  SKILL.md
└── bazi/             # 八字（独立）
    ├── core/yishu_core/   # 八字私有的引擎副本
    ├── scripts/ data/ references/ dev_tools/ docs/   # 八字暂无 tests/（见上）
    └── README.md  SKILL.md
```

> 注：两科内部的 `core/yishu_core` 文件名相同，但内容各自独立；这是“零耦合、各自可独立运行”的刻意结果。引擎内部仍保留 `ming_tables` 等八字专用模块名，属内核命名，不影响学科独立性。

## 运行

直接进入对应学科目录运行其脚本即可，例如：

```bash
# 六爻：铜钱起卦
python liuyao/scripts/chart.py --mode coin --question "某事如何" --seed 42

# 八字：按出生时间排盘
python bazi/scripts/chart.py --datetime "1990-05-20 12:00" --gender 男
```

两科脚本各自通过“向上搜索 `core/yishu_core`”定位自己的私有内核，因此从任意位置调用都不会串到对方。

## 作为 DSH 插件安装（免手工下载与敲命令）

上面的用法要求先有本仓库、再让 agent 敲 `python ...` 命令。若想**装了即用**，
可把它作为 DeepSeek Harness（DSH）插件安装——插件自带引擎与运行必需数据，
模型直接调用 `yi_liuyao` / `yi_bazi` / `yi_kb` 三个工具，无需另装 Python（DSH 桌面自带运行时会被自动发现）：

```bash
# 1) 装插件
dsh plugin --profile <你的profile> add "link:<本仓库>/dsh-plugin"

# 2) 装 agent preset（可选但推荐：新建会话可选「Yi 术数」）
node dsh-plugin/scripts/install-preset.mjs <你的profile>
```

它同时提供 DSH 的三层能力：

| 层 | 机制 | 落点 |
|---|---|---|
| 工具 | `ctx.tools.register()` | `yi_liuyao` / `yi_bazi` / `yi_kb` |
| 技能 + 知识库 | `ctx.skills.registerProvider()` + `bundledSkillDir` | `dsh-plugin/skills/yi-divination/`（9 篇判据文档） |
| Agent 预设 | `@deepseek-ai/dsh-agent-preset` | `dsh-plugin/presets/yi-divination.yml` |

发布包（`npm pack` 实测）解包 **2.6 MB**、`.tgz` **0.77 MB**；**不含** `data/cases/`（38MB）、
`data/sources/`（9.5MB）与 `references/case_library.md`（165KB）——前者只服务古籍对齐分与回归门，
后者按 AGENTS.md §一.2 铁律二必须与解读物理隔离。

详见 [`dsh-plugin/README.md`](dsh-plugin/README.md)。

- 插件源码：`dsh-plugin/src/`（node 半：工具注册、技能注册、系统提示词段）
- 引擎打包：`dsh-plugin/scripts/build-engine.mjs`（**白名单**从两科收集，产物 `engine/` 不入库）
- 知识库组装：`dsh-plugin/scripts/build-skills.mjs`（产物 `skills/` 不入库）
- 自检：`npm --prefix dsh-plugin run check`（包级 13 段 + DSH 内验证，含负例自证）


