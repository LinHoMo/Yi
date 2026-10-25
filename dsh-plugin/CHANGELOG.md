# dsh-plugin CHANGELOG

> 本卷登记 DSH 插件（`dsh-yi-divination`）自身的批次；批次号沿用全仓流水（接两科
> CHANGELOG）。插件是两科的**打包层**：引擎与知识库都是构建产物（不入库），两科缺陷
> 修复的判据与实跑记录仍以两科 `docs/CHANGELOG.md` 为准；本卷只记插件半的事
> （架构、构建、安装、验证、发现）。

## 2026-10-25 第两百六十九批（dsh-plugin）：**Yi 术数 DSH 插件建成入库——agent 预设 + skills 加载 + 知识库 + 内置引擎的分层架构**

**是什么**：把两科包装成 `dsh plugin --profile <p> add "link:<repo>/dsh-plugin"` 一键
安装的 DSH 插件，装了即用（引擎随包、DSH 桌面 Python 运行时自动发现），会话里直接调
工具，无需 clone 本仓库、无需手敲 `python` 命令。

| 层 | 机制 | 落点 |
|---|---|---|
| 工具 | `ctx.tools.register()` | `yi_liuyao`（coin/time/number/manual 四种起卦）／`yi_bazi`（datetime+gender） |
| 技能+知识库 | `ctx.skills.registerProvider()` + 预设侧 `bundledSkillDir` | `skills/yi-divination/SKILL.md` + `references/{liuyao,bazi}/` 9 篇判据 + INDEX.md 路由表 |
| Agent 预设 | `@deepseek-ai/dsh-agent-preset` | `presets/yi-divination.yml`（工具+技能+系统提示词段一体，`- insert:` 方言） |
| 系统提示词段 | `ctx.systemPrompt.section()`（order 900） | 铁律一（机械运算归代码）／一卦一事／口径诚实的会话内重申 |

**构建与产物纪律**：`engine/`（137 文件白名单打包）、`skills/`（9 篇组装 + INDEX.md
再生）均为构建产物，**不入库**（根 `.gitignore` 本批起排除 `dsh-plugin/engine/`、
`dsh-plugin/skills/`、`node_modules/` 与锁文件）——避免 AGENTS.md §二 警告过的
「同表多存、取值不一致」事故土壤。改两科后必须 `npm --prefix dsh-plugin run check`
（build → selftest → verify-in-dsh）再提交，过期副本由逐文件一致性门判红。

**验证（全绿）**：`selftest` 12 段 48 项，含 8 处负例自证（patch 方言缺 `insert` 判红、
引擎指纹不一致判红、案例库混入知识库判红、`__pycache__` 污染判红等）；`verify-in-dsh`
在 DSH 0.2.1-rc.2 真机验证工具注册／技能字段／执行渲染链路。`npm pack` 实测解包
2.43 MB、tgz 0.71 MB；`data/cases/`（38 MB）、`data/sources/`（9.5 MB）、
`references/case_library.md`（165 KB，铁律二）不在包内。

**真机踩坑 9 条**（invocation 必须是 OBJECT、rank 必须有限、systemPrompt 段必须带
order、fallback 必须给 `output.render`、`PYTHONDONTWRITEBYTECODE` 等）逐条记在
`dsh-plugin/README.md`，不在此重复。

**同批对齐**：根 `README.md` 增加「作为 DSH 插件安装」一节；`AGENTS.md` §二目录树
收录 `dsh-plugin/` 并新增「dsh-plugin 契约」小节（同步口径：改两科 → npm run check →
提交）；插件批次自此登记本卷。

**安装态**：desktop profile 已装（link:）且预设已追加（`scripts/install-preset.mjs`
幂等）；预设注册表 `default: standard` 未动，是否把 `yi-divination` 设为默认预设待
用户决定（改一行即可）。

## 2026-10-25 第两百七十批（dsh-plugin）：**新增 `yi_kb` 判据知识库检索工具——先定位再读节段，省上下文**

**动机**：知识库 9 篇单篇最大 52KB，模型凭 INDEX.md 路由表整篇盲读，读错一篇就白占
一大块上下文。`yi_kb` 让模型先关键词定位（返回 文件:行 + 节标题 + 摘录），再按行读
具体节段。

**实现**（`src/kb.mjs`，纯 Node、确定性、零 LLM 零 Python）：
- 只扫 `skills/yi-divination/references/` 下 `.md`；`case_library.md` 在**扫描层**按
  文件名硬排除——与打包层（`build-skills.mjs` NEVER_SHIP）、自检 [1.5] 包内断言构成
  铁律二的三道闸。
- 检索：按 1–3 级标题切节；词频计分（标题命中 ×4、文件名命中 ×3、正文词频封顶 12、
  覆盖词数 ×6）；每文件最多 2 条防单篇刷屏；`limit` 夹在 1..10（默认 5）。
- 无关词返回空清单不编造；缺 `query` 抛错（对齐 [7] 参数语义校验口径）。

**注册与文档**：`src/index.mjs` 恒注册（纯 Node，与 `enableBazi` 无关）；系统提示词段
（「两个工具」→「三个工具」）、SKILL.md（单一真源）、INDEX.md 模板、README、预设注释
同步提法。

**验证（全绿）**：`selftest` 新增 [12] 六断言 + 2 负例自证——扫描层排除用「探针文件
确实存在但不在可检索清单」证明判据在起作用（不是目录为空）；`verify-in-dsh` 新增
yi_kb 注册／执行／render 三查。
