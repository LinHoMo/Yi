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

**验证（全绿）**：`selftest` 新增 [12] 十断言（含 4 项负例性质）——扫描层排除用「探针文件
确实存在但不在可检索清单」证明判据在起作用（不是目录为空）；`verify-in-dsh` 新增
yi_kb 注册／执行／render 三查。

## 2026-10-25 第两百七十一批（dsh-plugin）：遗留项清账 + 文档实测对齐

纯文档/配置批：未动引擎、检索逻辑与构建脚本；`engine/`、`skills/` 产物与 270 批一致。

- **default 预设维持 `standard`（落纸决策，非改数）**：Yi 预设刻意最小化子插件列表
  （术数本体 + 技能通道，不塞 bash/web/search），设为默认会改变**所有新会话**的可用
  工具面；术数会话按需在新建时选择。仓内 preset 注释保留一行指引，要翻默认改一行即可。
- **desktop profile 补丁注释同步**：工具清单补 `yi_kb`（与仓内 `presets/yi-divination.yml`
  对齐）。该文件在仓库外（用户自有 profile），不入库；`install-preset.mjs` 不含该注释
  文本，无第二修复点。
- **计数对齐**（消灭「文档说的和做的不一致」）：`npm pack --dry-run --json` 复测 =
  **160 文件 / 2.44 MB / tgz 0.72 MB**（270 加 `kb.mjs`：插件源码 4→5 文件、0.03→0.04 MB；
  引擎 2.21 / 知识库 0.17 不变），两处 README 体积表按实数更新；selftest 复跑全绿
  **58 项 / 0 失败**（269 记 48 项 + [12] 段十项），README「12 段」→「13 段」、
  「48 项」→「58 项」，负例数改定性表述；270 条目「六断言 + 2 负例」系实现中途口径，
  已就地更正为终态十断言；根 README 工具清单两处补 `yi_kb`。
- 复现注记：`npm pack` 对 `--prefix` 不生效（按 CWD 找 package.json），须
  `cd dsh-plugin && npm pack --dry-run --json`（README 复现命令本就如此写）。

## 2026-10-25 第两百七十二批（dsh-plugin）：yi_kb 召回质量——中文 2-gram 兜底 + 同义词展开

迭代地图第 1、2 项（缺口：无空格长 query 整串匹配漏召；术语别称检索不到）：

- **中文 2-gram 兜底分词**（`src/kb.mjs` 新增 `cjkBigrams`）：query 里 ≥3 字的连续汉字串
  自动切出相邻二字窗（「世应怎么安」→ 世应/应怎/怎么/么安），减权重计分（标题 ×1、
  正文封顶 4、不计覆盖）——整串匹配不到时仍能召回，且不压过精确命中；2 字词不切
  （整串即词），不跨中英文边界。返回值新增 `expanded.bigrams` 供复核。
- **同义词展开**（新增 `src/kb-synonyms.json` + `expandWithSynonyms`）：组内任一词命中
  即整组全权重展开；返回值新增 `expanded.synonyms`。只收「确定同义」，不收近义
  （忌神/仇神、旺相/休囚是不同概念，禁止入组）；当前 KB 无「喜用神/调候」覆盖，
  相关组暂不收录（防假扩充）。词表放 `src/` 随 files 白名单进包，不改打包配置。
- **真 Bug 修于自检**：首版把 `if (!covered) continue` 留在 bigram 计分之后——只有二字窗
  命中的节被整节丢弃（「世应怎么安」零命中）；修正为 `if (!covered && !bigramHit) continue`。
- **测试**：selftest [12] 10→15 断言（2-gram 召回／含 najia_rules／expanded.bigrams 可复核；
  同义词 用爻→用神 召回／摘录含「用神」可复核）；无关词探针换「汽车维修zzz量子塌缩」——
  其每个 ≥3 字汉字串的二字窗已验证零库内命中（旧探针「不存在的词」二字窗「存在」在库中
  大量出现，会被兜底误召回）。selftest 全绿 **63 项 / 0 失败**；verify-in-dsh 全绿。
- **文档**：SKILL.md（单一真源）、README、工具 description／参数说明同步
  「2-gram 兜底 + 同义词展开」。
- pack 复测：**161 文件**（+kb-synonyms.json）/ 2.44 MB / tgz 0.72 MB（体积表按实数更新）。

## 2026-10-25 第两百七十三批（dsh-plugin）：yi_bazi 结构化岁运字段

迭代地图第 3 项（缺口：`baziValue` 只给四柱+结论梗概，模型讲大运流年只能复述 narrative）：

- **`baziValue` 重构**（`src/tools.mjs`）：新增三块结构化字段，全部引擎产出、node 只整形——
  - `conclusion` 补全：旺衰/分数/格局/成败/特格外加 调候、空亡与病药（从 verdicts 平铺）、
    胎元、通关、天克地冲、喜忌（`useful_gods`/`taboo_gods` 此前取自 `c.useful_gods` 本就有值，
    本批补 `strength_score`/`pattern_cheng_bai`/`special_pattern` 等）；
  - `dayun`：8 步基础表（干支/起讫岁/十神），并把大运明动按 `dayun_index` 并回对应步；
  - `liunian`：12 年逐年行（干支/十神），并入两类事件——明动（流年×命局）与
    岁运交叉（流年×所临大运，含 `dayun` 字段标明所临何运）；
  - `liuyue`：12 月干支十神。
- **事件 text 一律 clip（140/80 字）**：`basis` 逐字书证是对账层，不进结构化字段
  （analyze JSON 全量保留，铁律二的「引文可指回」不受影响）。
- **自检**：[6] 增 5 断言（dayun 8 步／liunian 12 年且首年 1990 庚午／liuyue 12 月／
  conclusion 旺衰格局真值／verdicts 平铺空亡）。实测发现 `conclusion.liunian` 是
  **12 年**（1990–2001）而非 8 年——首版断言按 8 年写，实跑抓出后改正。
  selftest 全绿 **68 项 / 0 失败**；verify-in-dsh 全绿。
- **文档**：SKILL.md（yi_bazi 节加「结构化岁运字段」说明：讲大运流年直接引字段，
  不要凭 narrative 复述）、README 同步。
