# 易（Yi）

> **能力边界一页看清**：[`CAPABILITY.md`](CAPABILITY.md)（T1 排盘已验证／T2 古籍忠实已量化含上限／
> **T3 现实预测不可测、不声称**）；治理面（哪些门在守什么）见 [`GOVERNANCE.md`](GOVERNANCE.md)；
> **全仓文档地图**（每份文档是什么、活文档还是归档）见 [`DOCS.md`](DOCS.md)；
> **架构整改完成记录**（25 张卡全部执行完毕；完成台账、V1–V15 实测与剩余欠账）见
> [`ARCHITECTURE-PLAN.md`](ARCHITECTURE-PLAN.md)；
> **门禁内核与根级门**见 `devkit/`（331–334 批归并，`sync_devkit.py --check` 守同源）。

本仓库只保留两个**相互独立、零耦合**的术数学科，各自携带一套完整可运行的实现：

| 目录 | 学科 | 说明 |
|------|------|------|
| `liuyao/` | 六爻（纳甲） | 六爻纳甲起卦、装卦、旺衰、应期、断语 |
| `bazi/`  | 八字（四柱） | 四柱排盘、格局、强弱、喜用、大运、流年 |

## 设计原则

- **无共享运行时、无合参层**：两科之间没有任何相互 import，也不存在把六爻与八字整合分析的层（`synthesis` 已移除）。
- **内核单一真源、两科各持产物**（316 批起）：内核在 `kernel/yishu_core/`——
  `common/` 10 个共用、`variants/<名>.<科>.py` 4 个在册分叉（`evidence`／`ming_tables`／`shensha`／`symbols`）、
  外加 3 个六爻专用（`hexagram_texts`／`najia`／`calendar_check`）与 1 个八字专用（`conflict_resolution`）。
  两科 `core/yishu_core/` 是**生成物**：`python kernel/sync_kernel.py --write` 写，`[35]` 逐字节比对，
  手改即判红。因此两科仍可各自独立运行、单目录拷走——**"零耦合"约束的是运行时依赖，不是源码来源**。
  （旧口径「17 个同名文件里 13 个逐字节相同」是 308 批的手抄实测，316 批已被本机制取代；
  八字侧同时去掉 3 个用不到的六爻模块，共 −874 行。）
- **各自自包含**：每科目录内均有 `scripts/`（机械推演）、`data/`（案例、古籍底本、规则）、`references/`、`dev_tools/`、`docs/`、`tests/`，并自带 `README.md` 与 `SKILL.md`。
  两科 `tests/` 形态不对称（刻意，D3 中档）：六爻有 `smoke_test.py`／`regression_test.py`／
  `thinking_chain_tests.py`／`six_god_wang_shuai_test.py`；八字只有 `smoke_test.py` 与
  `regression_test.py`（第三百三十五批补建），更深一层的回归/回验仍走 `bazi/dev_tools/check.py`
  （小节号会随门禁增补变化，故此处**不写死区间**——此前写 `[0]–[21]` 时 `[22]`／`[23]`／`[24]`
  已存在，属本行自禁的那类"文档里的旧真值"；现行全量以 `python bazi/dev_tools/check.py` 实跑输出为准）。
  本行此前写「`tests/` 只有六爻有、八字侧没有」——与现状不符（第三百六十一批按 `ls bazi/tests`
  实跑更正：`__init__.py`／`smoke_test.py`／`regression_test.py` 均在）。

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
    ├── scripts/ data/ references/ dev_tools/ docs/ tests/   # 八字 tests/ 仅 smoke+regression（见上）
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
模型直接调用 `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report` 四个工具，无需另装 Python（DSH 桌面自带运行时会被自动发现）：

```bash
# 0) 发布版（推荐）：从 GitHub Release 下载 tgz
#    https://github.com/LinHoMo/Yi/releases/tag/v1.0.0
dsh plugin --profile <你的profile> install ./dsh-yi-divination-1.0.0.tgz

# 1) 开发版：从本仓库 link 安装
dsh plugin --profile <你的profile> add "link:<本仓库>/dsh-plugin"

# 2) 装 agent preset（可选但推荐：新建会话可选「Yi 术数」）
node dsh-plugin/scripts/install-preset.mjs <你的profile>
```

> 口径提醒（AGENTS.md §一.3 铁律三）：本插件一切分数都是**古籍案例对齐分**（回归审计用），
> **不是现实命中率**——现实侧样本为零。六爻外部集主应期 top-1 **31.8%**（n=44，308 批实测，
> 旧登记 27.3）：高于 k=1 的随机 8.3%，但**低于全池随机 34.1%**（池均值 4.1/12），
> Wilson95%CI [20.0, 46.6]——样本小、区间宽，`liuyao/README.md` 同屏。
> ⚠ 该外部集**已参与调参**（181–309 批以 ±0.1 取舍）；315 批起 test 半已封存，
> 哨兵只给红绿，正式开卷须预注册——详见 `README` 上节的「外部集」条与 `CAPABILITY.md`。
> 它是排盘与推演参考工具，不是预言；重大决策以专业意见为准。

它同时提供 DSH 的三层能力：

| 层 | 机制 | 落点 |
|---|---|---|
| 工具 | `ctx.tools.register()` | `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report` |
| 技能 + 知识库 | `ctx.skills.registerProvider()` + `bundledSkillDir` | `dsh-plugin/skills/yi-divination/`（篇数以 INDEX.md 为准） |
| Agent 预设 | `@deepseek-ai/dsh-agent-preset` | `dsh-plugin/presets/yi-divination.yml` |

发布包（`npm pack` 实测）解包 **2.6 MB**、`.tgz` **0.77 MB**；**不含** `data/cases/`（38MB）、
`data/sources/`（9.5MB）与 `references/case_library.md`（165KB）——前者只服务古籍对齐分与回归门，
后者按 AGENTS.md §一.2 铁律二必须与解读物理隔离。

详见 [`dsh-plugin/README.md`](dsh-plugin/README.md)。

- 插件源码：`dsh-plugin/src/`（node 半：工具注册、技能注册、系统提示词段）
- 引擎与知识库打包：`plugins/scripts/build.mjs`（**白名单**从两科收集，产物 `engine/`、`skills/` 不入库，
  一次构建后分发到各宿主适配器；共享运行时真源在 `plugins/mcp/`）
- 自检：`npm --prefix dsh-plugin run check`（包级 13 段 + DSH 内验证，含负例自证）

## 打包与自检（一次构建，分发到 DSH）

同一套四工具（`yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report`）与同一份技能正文，
只适配 **DeepSeek Harness** 一个宿主。共享层在 `plugins/`（唯一真源），
`dsh-plugin/` 只放宿主专属文件（`package.json`、`src/index.mjs`、`presets/`）。
497 批起 claude/codex/gemini/yan 四家适配器已删除。

```bash
node plugins/scripts/build.mjs       # 一次构建，分发到 dsh-plugin/
node plugins/scripts/selftest.mjs    # 共享层自检（判红即 exit≠0）
```

> `engine/`、`skills/`、`src/` 不入库（根 `.gitignore`），由构建产物再生；
> 发布走 GitHub Release 的 npm tgz（见上节），不再有独立发行树。
> 详见 [`plugins/README.md`](plugins/README.md)。

口径与边界同上：一切分数是**古籍案例对齐分**，不是现实命中率；
DSH 桌面自带 Python 运行时，找不到时工具如实报错。


