# plugins CHANGELOG

> 本卷登记**共享打包层**（`plugins/`）的批次；批次号沿用全仓流水。
> 305 批起，各宿主适配器（`dsh-plugin/`、`yan-plugin/`）自身只留宿主专属文件，
> 共享的运行时、技能正文、构建与自检都归本目录，各宿主卷只记「宿主侧那点事」。
> **497 批起只保留 DSH 一个宿主**：claude/codex/gemini/yan 四家适配器目录、
> `publish.mjs`（git 发行树）及其在 build/selftest/ci/文档里的登记一并删除。

## 2026-11-09 第五百四十五批（共享层·随包登记）：**`plugins/` 运行时与技能正文零改动；本批只动两科 provenance 登记与 `[37]` 共享门，均不在随包新增面内。build 重建后 selftest 8 段全绿、`[1.6]` 产物同源**

## 2026-11-09 第五百四十四批（共享层·随包登记）：**`plugins/` 运行时与技能正文零改动；本批只动六爻 dev_tools 两器、三份文档与一份八字数据，均不在随包白名单的新增面内。build 重建后 selftest 8 段全绿、`[1.6]` 产物同源、`[1.5]` 案例库隔离绿**

## 2026-11-09 第五百四十三批（共享层·随包登记）：**`plugins/` 运行时与技能正文零改动；候选池 `open_result` 位于 `data/cases/`，不在 build 白名单内、不随包发货，selftest `[1.5]` 案例库隔离绿、8 段全绿。CI root-gates 新增一行开卷记录只读校验（守 528 约定不新增门号）**

## 2026-11-09 第五百四十二批（共享层·随包登记）：**本批 `plugins/` 运行时与技能正文零改动；新增的候选池位于 `data/cases/`，本就不在 build 白名单内，不随包发货，selftest `[1.5]` 案例库隔离绿、8 段全绿。CI root-gates 新增一行候选池同源复验（守 528 约定不新增门号）**

## 2026-11-09 第五百四十一批（共享层·真源去钉数与导览口径）：**`plugins/SKILL.md` 去掉最后一处手钉篇目大小（「8KB，短」→ 回指 `references/INDEX.md`），补齐 539 批遗漏；`kb-docs.mjs` 口径注记第③条明确「技能正文真源同样不得钉会变数」。build 重分发后宿主根 SKILL.md 与两处技能目录 SKILL.md 均与真源逐字节同源，selftest `[3]`／`[1]` 全绿。本卷无运行时源码改动**

## 2026-11-09 第五百四十批（共享层·随包登记）：**本批 `plugins/` 无源码改动；`build.mjs` 因两科 `data/*.json` 变化（六爻 `xiang_layer.json`、八字 `narrative_templates.json`）重建 `engine/` 产物，`selftest [1.6]` 全量同源通过。CI root-gates 新增一行 `liuyao/dev_tools/xiang_coverage.py --probe`（象层词表常驻判据，守 528 约定不新增门号）**

## 2026-11-08 第五百三十九批（共享层·单一真源与夹具定性）：**新增 `plugins/scripts/dev-only.mjs`，把 `build.mjs` 的 DEV_ONLY 与 `selftest.mjs [2]` 的 DEV_ONLY_SHIMS 收成一份登记表（528 批 G11 同型的双份手工清单）；521 批已删 shim，名单定性为防复活哨兵，`[2]` 加空表假绿断言。`plugins/mcp/server.mjs`／`schema.mjs` 由「Yan 插件侧 MCP 服务」重定性为「1.0 契约 stdio 自检夹具」——497 批删宿主后不再服务任何宿主，但 `[4]` 真跑 initialize／tools/list／yi_kb／yi_liuyao、`[5]` 吃其 tools/list 断言冻结面，删它等于砍两道有牙的门，故保留并改 SERVER_INFO。`plugins/SKILL.md` 去掉手钉「47KB」、`kb-docs.mjs` 格局数按正文「十二大→十五大」更正并立「描述不得钉会变数」口径。实跑：build 完成、selftest 8 段全绿（知识库 14 篇、包体 201 文件／2.92MB）、`[1]` 逐字节同源**

## 2026-11-06 第五百二十八批（共享层·随包登记）：**门号登记同源门（528 全仓批）：本层无源码改动，仅随包登记**

## 2026-11-06 第五百二十七批（共享层·随包登记）：**根级文档门 --selftest 假绿根治与 526 批结论更正（527 全仓批）：本层无源码改动，仅随包登记**

## 2026-11-06 第五百二十六批（共享层·随包登记）：**器具全体检声明面收口（526 全仓批）：本层无源码改动，仅随包登记**

## 2026-11-06 第五百二十五批（共享层·随包登记）：**生成物同源复验补齐（525 全仓批）：本层无源码改动，仅随包登记**

## 2026-11-06 第五百二十四批（共享层·随包登记）：**六爻 ontology 锚定门假绿根治与产物同源（524 全仓批）：本层无源码改动，仅随包登记**

## 2026-11-06 第五百二十三批（共享层·随包登记）：**文档历史减量、窗口上门与缺口收口（523 全仓批）：本层无源码改动；305 批「未做的事」四条按现状加勘误块（均非现行待办），其余仅随包登记**

## 2026-11-06 第五百二十二批（共享层·随包登记）：**pytest 桥接清单单一真源与覆盖门（522 全仓批）：本层无源码改动，仅随包登记；`node scripts/build.mjs` 已重跑、`scripts/selftest.mjs` RC=0**

## 2026-11-05 第五百二十一批（共享层·随包登记）：**消除 scripts/ 兼容 shim 反向 import eval/（521 全仓批）：本层无源码改动，仅随包登记；`node scripts/build.mjs` 已重跑、`scripts/selftest.mjs` RC=0**

## 2026-11-05 第五百二十批（共享层·随包登记）：**引入 pytest 测试框架（520 全仓批）：本层无改动，仅随包登记**

## 2026-11-05 第五百一十九批（共享层·随包登记）：**六爻构建器同步门 [46]（519 全仓批）：本层无改动，仅随包登记**

## 2026-11-05 第五百一十八批（共享层·随包登记）：**门编号规范化（518 全仓批）本层无改动，仅随包登记；Node selftest [1.5]/[1.6]/[2.4] 为独立编号体系、不在本次 liuyao 重排范围**

## 2026-11-05 第五百一十七批（共享层·随包登记）：**DOCS.md 钉数消除（随 517 全仓批）；本层无改动，仅随包登记**

## 2026-11-04 第五百一十六批（共享层）：**冻结面自检与报告口径覆盖**

- `scripts/selftest.mjs` [5] 由「只查 `yi_liuyao` 参数名」扩为四工具参数 schema 与
  required 的逐项比对（真值取 MCP `tools/list`），含改 `required` 的负例自证；
  [7] 新增三份报告模板（`mcp/report.mjs`、两科 `scripts/render.py`）的禁语与
  「专业意见为准」提示语扫描，含 0 目标与缺提示语负例。
- 段号表与卷首说明同步；`build.mjs` 未改。主登记见六爻 CHANGELOG 516 批。

## 2026-11-04 第五百一十五批（共享层·并批）：**产物重建与同源**

- 六爻 `kernel_path.py` 与 14 个 scripts 模块、两科共享门真源有改动；
  `node plugins/scripts/build.mjs` 已重跑，`plugins/engine` 与 `dsh-plugin/engine`
  由 selftest [1.6] 全量逐字节同源校验（165 文件）。
- 本卷无脚本改动；主登记见六爻 CHANGELOG 515 批。

## 2026-11-04 第五百一十四批（共享层·并批）：**自检补齿与产物全量同源**

- `scripts/selftest.mjs`：新增 [1.6] `engine/` 165 文件、`skills/` 15 文件全量逐字节
  同源门（篡改／缺文件／0 文件三类负例）；[5]/[6] 补负例自证；
  [7] 修 `.filter(existsSync)` 造成的「0 份文档也判绿」。
- `SKILL.md` 知识库篇数去钉数，改指 `references/INDEX.md`；本卷第三百零七批
  重复节去重并加 497 批勘误；卷首段号表压缩。
- `build.mjs` 未改；`build.mjs && selftest.mjs` rc=0。主登记见六爻 CHANGELOG 514 批。

## 2026-11-04 第五百零八批（共享打包层）：**六爻 `engine/` 升格后 `RUNTIME_INCLUDE.liuyao` 补收 `engine`——漏收则包能装、`yi_liuyao` 调用即 ImportError**

**性质**：打包白名单补漏（不改四工具 1.0 冻结契约、不改读数）。

- `plugins/scripts/build.mjs`：`RUNTIME_INCLUDE.liuyao` 由 `['core','scripts','rules','data/rules','references','assets']`
  改为同表加 `'engine'`。六爻第五百零八批把 `scripts/engine`＋`scripts/classical` 升格到 `liuyao/engine/`，
  原白名单只收 `scripts`（递归），升格后**整条推演链不再进包**——这类漏收不会让构建报错，只在首次调用时炸。
- `node plugins/scripts/build.mjs` → `selftest.mjs` 全绿：包体 **201 文件／2.93MB**、无符号链接；
  `[2]` 段 engine 布局校验通过；**`yi_liuyao` 引擎冒烟以构建产物树跑通出「贲」**（打包侧唯一端到端证据）。
- 六爻侧搬迁与判据面见 `liuyao/docs/CHANGELOG.md` 同批；八字侧登记见 `bazi/docs/CHANGELOG.md` 同批。

## 2026-11-02 第四百九十七批（共享打包层）：**宿主收敛至仅 DSH——删除 claude/codex/gemini/yan 四家适配器与 git 发行树**

**性质**：分发面裁剪（不改引擎、不改四工具 1.0 冻结契约、不改读数）。

- 删除目录：`claude-plugin/`、`codex-plugin/`、`gemini-plugin/`、`yan-plugin/`（含其 README/CHANGELOG）。
- 删除 `plugins/scripts/publish.mjs`：它唯一服务四家 git 远程通道（独立发行树 `plugins/dist/`），
  DSH 本就走 GitHub Release npm tgz，不依赖发行树。
- `build.mjs`：`ADAPTERS` 只余 `{ id:'dsh', rootSkill:true }`，删去四家的技能附加段与 `--only` 多宿主用法。
- `selftest.mjs`：`ADAPTERS` 只余 dsh；[6] 段删去仅服务非 DSH 宿主的清单规则（claude/codex/gemini/yan
  的 MANIFEST_RULES、MCP 变量断言、Yan resources 双向对账），只留包体预算（≤4000 文件/≤64MB/无符号链接）；
  随之删去不再使用的 `resourceIdFor` import 与 [7] 段 `INSTRUCTIONS.md` 目标。
- `.gitignore`：删四家的 `engine/skills/src/node_modules` 忽略行，保留 dsh 与共享层规则。
- `.github/workflows/ci.yml`：`plugin-gates` 去掉 `host` 矩阵（五家×2OS→仅 DSH×2OS），
  manifest 断言内联简化为 dsh 必备文件。
- 文档同批改口径：根 `README.md`（删「五份清单」宿主表与 Yan 安装节）、`AGENTS.md` §二
  （多宿主契约与硬约束表收敛为 DSH 单行）、`DOCS.md` 第五节（删 10 行宿主文档登记）、
  `plugins/README.md`（重写为单宿主）。
- 读数：tune/holdout/外部集逐位不变（本批不动 `core/`、`scripts/`、`data/`）。

## 2026-10-30 第三百六十二批（共享打包层）：**象层进工具输出面（两科）＋ 补上爻辞**

**性质**：能力建设（共享运行时只做搬運与整形，不新增判定逻辑）。

- `mcp/tools.mjs` 的 `liuyaoValue` 增 `xiang` 结构化块：`category`／`ti_yong`／`hu_gua`／
  `guaci`／`yaoci`（限 8 条）／`spirit`／`fangwei`／`class_image`／`basis`；
  缺则整块为 `null`（不塞空壳冒充覆盖）。
- `liuyaoValue.lines[]` 补 **`line_text`（爻辞）**——此前插件面只搬盘面机械字段，
  爻辞一项实测为零出口（爻辞真值源一直在 `kernel/yishu_core/hexagram_texts.py`）。
- `baziValue` 增 `xiang`：`gongwei`（宫位）／`liugin`（六亲，按性别分野）／`zangfu`
  （五行脏腑，带「非医学诊断」声明）。
- 纪律（CONTRACT §五-bis）：象层是素材，不进 `conclusion`、不进评分；两科 `[39] 象层门`
  守「评分侧禁读 `xiang`」，负例自证：偷读即红。
- `node plugins/scripts/build.mjs && node plugins/scripts/selftest.mjs` 全绿；
  新文件（`scripts/xiang.py`、`data/xiang_layer.json`）已随 build 分发到五个宿主。

## 2026-10-30 第三百六十一批（共享打包层）：**报告不再挂到另一卦 ＋ gender 不再是死参数**

**性质**：bug fix（行为变更）。工具名/参数集/冻结面未动（`yi_liuyao` 参数键仍
`datetime,gender,mode,numbers,question,seed,yao`）；输出新增可选 `seed` 字段（minor 级）。

- **P0 · `yi_report` 会重摇一卦**：`runReport()` 用原始参数重新 `cast()`，而六爻默认
  `mode=coin` 无 seed 时每次都是新卦——「先 `yi_liuyao` 断卦、后出报告」实际交付的是
  两个不相干的卦。现在：①`runLiuyao()` 在 coin 且未给 seed 时**显式生成随机种子**并在
  返回值里回传 `seed`；②`yi_report` 的 liuyao+coin 缺 seed 直接报错拒出报告；
  确定性方式（time/number/manual）不受影响。
- **`gender` 从死参数变成真输入**：schema 一直声明「占婚恋等用神取法不同时重要」，
  但 `buildLiuyaoArgs()` 从不转发、六爻脚本也没有 gender 字段——模型按描述传了性别却无效。
  引擎按**问句文本**取用神（`use_god_relations.json`：女家/女方/女占→官鬼，
  男家/男方/男占→妻财），故工具层在问句无性别立场词时补 `男占/女占`，有立场词时不改写
  当事人原话。实测同一问句：女→官鬼、男→妻财。
- **报告落盘不再互相覆盖**：`writeReportFile()` 旧文件名只精确到秒且覆盖写，同秒同格式
  第二次会静默盖掉第一次；现加随机后缀 ＋ `wx` 排他写，并对 `yi-reports` 临时目录做
  24h 前旧文件清理（只认本工具命名的 `yi-<学科>-*.html|md`）。
- 复验：`node plugins/scripts/build.mjs` rc=0；`node plugins/scripts/selftest.mjs` 全绿
  （含 [5] 参数冻结面、[7] 禁语扫描）；实测 `runLiuyao` 回传 seed 且同 seed 复现同卦；
  `runReport` 缺 seed 报错、带 seed 出报告；连续两次落盘路径不同。

分数口径不变（详见同批 `liuyao/docs/CHANGELOG.md`）。

## 2026-10-30 第三百五十九批（共享打包层）：**bazi 评测 shim 不随包——两科 DEV_ONLY 对齐**

**性质**：build fix（行为保持）。零运行时、零工具契约改动。

- `build.mjs` 的 `DEV_ONLY.bazi` 新增 `evaluate.py`：359 批八字评测实现已迁
  `bazi/eval/`，`scripts/evaluate.py` 只剩 re-export shim；包内没有 `eval/`，
  随包会让 `import eval` 失败。liuyao 三项排除不变。
- `selftest.mjs [2]` 的「评测 shim 未随包」断言改为两科登记表
  （liuyao×3／bazi×1），探针负例改用 bazi `scripts/evaluate.py`。
- 实跑：`node plugins/scripts/build.mjs` rc=0；`selftest.mjs` 全绿
  （yan 包体 176 文件 / 2.64MB，无符号链接）；`publish.mjs` 生成 `plugins/dist`
  并 `--check` 通过（发布树可安装性全绿）。
- 分数口径不变（详见同批 `bazi/docs/CHANGELOG.md`）。

## 2026-10-30 第三百五十六批（共享打包层）：**liuyao 评测 shim 不随包**

**性质**：build fix（行为保持）。零运行时、零工具契约改动。

- `build.mjs` 新增 `DEV_ONLY` 登记表：liuyao 的 `scripts/` 不随包
  `evaluate.py` / `case_runner.py` / `build_portal_assets.py`。原因：356 批这
  三件实现已迁 `liuyao/eval/`，`scripts/` 同名文件只是开发期 re-export shim；
  包内没有 `eval/`，随包会让 `import eval` 直接失败（本地实测
  `plugins/engine/liuyao/scripts/evaluate.py` 报 `ModuleNotFoundError`）。
  bazi 的 `scripts/evaluate.py` 是真实实现，不在排除表内（359 批已迁 `eval/`，
  同批起亦排除）。
- `selftest.mjs [2]` 新增「liuyao 评测 shim 未随包」正面断言（共享层＋五宿主
  各查一次）＋临时探针负例（造一份 `engine/liuyao/scripts/evaluate.py` 必须被抓到）。
- 实跑：`node plugins/scripts/build.mjs` rc=0；`node plugins/scripts/selftest.mjs`
  全绿（yan 包体 177 文件 / 2.67MB，无符号链接）；`publish.mjs` 生成 `plugins/dist`
  并自检「发布树可安装性全绿」；`npm --prefix dsh-plugin run selftest` 全部通过。
- 分数口径不变（详见同批 `liuyao/docs/CHANGELOG.md`）。

## 2026-10-29 第三百三十八批（A4-CI）：**CI 四 job 齐备＋五宿主×2 OS 矩阵**

- `.github/workflows/ci.yml` 现有四 job：`root-gates`（331 批 A0-4）、`kernel-sync`
  （本批：`kernel/sync_kernel.py --check` ＋ `devkit/sync_devkit.py --check`）、
  `gates`（两科 check.py，保持不动）、`plugin-gates`（本批扩成
  `{dsh,claude,codex,gemini,yan} × {windows-latest,ubuntu-latest}`）。
- `plugin-gates` 每格：build once → shared selftest → dsh 格加 `npm run check` →
  该宿主清单在位断言（dsh 3 项／claude 3 项／codex 3 项／gemini 3 项／yan 4 项）。
- 本地实跑：`node plugins/scripts/build.mjs` rc=0；`node plugins/scripts/selftest.mjs`
  全绿（7 段、含负例自证）；`npm --prefix dsh-plugin run check` rc=0；五份清单断言
  全 rc=0。无 `continue-on-error`。
- 实跑抓到并修掉一条宿主侧缺陷：DSH `src/index.mjs` 的 CRLF frontmatter 读取
  （详见 `dsh-plugin/CHANGELOG.md` 同批）。

## 2026-10-29 第三百三十八批（A4-2）：**六份 CHANGELOG 合并评估——结论：维持现状，不合并**

**性质**：评估（零改动）。读数来源：`scratch/changelog_overlap.py`（一次性器，按「第…批」
正则抽批次号，中文数字转整数；六份文件逐一抽取后求交）。

### 一、批次区间读数（2026-10-29 实测）

| 文件 | 批次数 | 区间 |
|---|---|---|
| `plugins/CHANGELOG.md` | 7 | 305–326 |
| `dsh-plugin/CHANGELOG.md` | 3 | 302–305 |
| `yan-plugin/CHANGELOG.md` | 2 | 304–305 |
| `claude-plugin/CHANGELOG.md` | 2 | 306–309 |
| `codex-plugin/CHANGELOG.md` | 2 | 306–309 |
| `gemini-plugin/CHANGELOG.md` | 1 | 306–306 |

六份合计 **10 个不同批次**；两两重叠：`plugins∩dsh` 1（305）、`plugins∩yan` 1（305）、
`plugins∩claude` 2（306/309）、`plugins∩codex` 2（306/309）、`plugins∩gemini` 1（306）、
`dsh∩yan` 1（305）、`claude∩codex` 2（306/309）、`claude∩gemini` 1（306）、
`codex∩gemini` 1（306）。

### 二、结论：**维持六份，不合并**（AGENTS.md §六.5 诚实结案）

- 重叠度低：最大两两重叠 2 批，且这些重叠是**跨宿主同批**（如 306 批在四卷都出现），
  各卷记的是**不同宿主的专属事实**（清单字段、安装命令、验证结果），不是同一段话抄六遍。
- 合并会混掉两类本应分开的语义：共享层变更（`plugins/`）与宿主侧变更（各适配器），
  而各宿主侧还各有独立 semver 映射（275 批纪律）。
- 因此不为了"整洁"合并；**登记本条即结案**。若未来单卷批次量增长到需要检索索引，
  按 330 批六爻做法加「归档＋历史索引」，而不是把六卷揉成一份。

## 2026-10-29 第三百二十六批（共享层）：**知识库 14 → 15 篇（新增八字调候判据篇）＋ 修正一处名不副实的登记**

**性质**：content（登记表增一条 + 描述修正一条）。运行时、工具名、参数 schema、输出结构**一律未动**——
1.0 API 冻结面未触碰。

### 一、新增《调候》判据篇

`KB_DOC` 增列 `bazi/bazi_tiaohou.md`：**需要取用神的气候一路（调候）：某月某日干先取什么、次取什么，
及调候的边界**。

此前该判据**数据在**（`bazi/data/tiaohou_quotes.json` 120 条）、**引擎在**（`analyze` 已出 `tiaohou`
维度），但**成文判据不在知识库里**——会话中要讲「这个月生人取什么用」，模型没有可依据的成文依据。
本篇补上这一段，13 条引文全部逐字可回验（`check_source_readings.py --doc` 实测 13/13 命中，0 判红）。

### 二、修正一处名不副实的登记

`bazi/bazi_yue_shi_ge.md` 原登记为「月支与格局」，而该文件实际是**五虎遁／五鼠遁歌诀**
（推月推时法），与登记描述不符。按现文改登记为「需要核对推月推时：五虎遁（年上起月）、
五鼠遁（日上起时）歌诀与引擎对源」——**按现文改登记，不按登记改文**。

### 三、宿主侧同步

`yan-plugin/yan-plugin.json` 的 `resources[]` 增登 `kb-bazi-bazi-tiaohou`（Yan 无 `skills/` 目录机制，
知识库只能靠工具返回 + 资源表，故须逐篇登记）。

`node plugins/scripts/build.mjs && node plugins/scripts/selftest.mjs`：知识库 **15 篇**，
Yan 资源表双向一致（15 条），负例自证（抽掉一篇即红、多塞一篇即红）仍成立，自检全绿。
`npm --prefix dsh-plugin run selftest` 亦全绿。

## 2026-10-29 第三百一十九批（plugins）：**知识库 9→13 篇（四篇"读人"文档随包）＋ yi_kb 二字窗打分修正**

**性质**：content＋runtime。1.0 冻结面（四工具名／参数 schema／value 结构／技能条目）未动。

### 一、四篇新判据文档进包

| 文档 | 学科 | 一句话 |
|---|---|---|
| `bazi/bazi_liuqin_gongwei.md` | 八字 | 六亲·家宅·家人：宫位与星双参，含不断生死／不数人数／不判离婚的禁句表 |
| `bazi/bazi_jibing_tizhi.md` | 八字 | 疾病·体质：五行配脏腑、取伤重、虚实、相生亦生病，含不诊断的硬边界 |
| `bazi/bazi_qianshi_yanpan.md` | 八字 | 前事·验盘：时刻切法、三件事校时辰、已过往运只讲感受层 |
| `liuyao/odd_questions.md` | 六爻 | 奇问杂占：失联寻宠、怪梦、异象、越界提问，含不可占清单与拒答话术 |

- `scripts/kb-docs.mjs` 登记四条"何时读"；构建后 `references/INDEX.md` 自动重排（13 篇 + INDEX）；
- `yan-plugin/yan-plugin.json` 的 `resources[]` 同步 10→**14 条**（该清单是手工维护的，
  漏登记会被自检 [6] 判红——本批已实测双向一致）；
- 对外文书的篇数同步：`plugins/SKILL.md`、根 `README.md`、`claude-plugin/README.md`、
  `dsh-plugin/README.md` 由 9 篇改 13 篇（dsh 包体表 11→15 文件）；`mcp/kb.mjs` 头注同步。
  篇数以 `references/INDEX.md` 为准，此后新增文档须一并回改这几处。

### 二、`yi_kb` 打分修正（五宿主同源）

新文档进包后，DSH 自检 [12] 抓到真缺陷：`世应怎么安` 召不回 `najia_rules.md`。

- **停用表**：22 个疑问／功能二字窗（怎么、什么、如何、是否、可以…）不进召回；
- **稀有度权重**：`1 + 3*(1 - df/总节数)`，让「世应」这类实词压过「怎么」这类高频词；
- **对数饱和**：`log2(1+count)` 取代线性封顶，重复出现不再线性加分。

复测：`世应怎么安` 前五含 `najia_rules.md`；`纳甲 装卦 世应` 首位 `najia_rules.md`；
`用爻→用神` 同义展开仍召回；无关词仍零命中。**只改召回排序，不改返回结构**（仍是
`{kb,query,terms,expanded,discipline,files_scanned,matches}`）。

### 三、读数（本批实跑）

- `node plugins/scripts/build.mjs` → 知识库 **13 篇 + INDEX**；五宿主 engine／skills／src 全量重发；
- `node plugins/scripts/selftest.mjs` → **全绿**（含 [1] 逐字节同源、[3] 篇数对账、[6] Yan 双向一致、[7b] 口径声明）；
- `npm --prefix dsh-plugin run selftest` → **自检全部通过**（[8] 引擎逐文件对拍 145 件、
  [12] 召回四例、[13] 报告）；
- 未跑 `publish.mjs`（发行树生成是外部动作，且本机无发布授权）。

### 四、开口

- **知识库篇数在四处硬编码**（本批手工同步）：理想形态是由 `kb-docs.mjs` 生成为常量再注入文书，
  但四份文书分属不同宿主、格式各异，暂不统一；已在本条写明"以 INDEX 为准"作为口径兜底。
- **只重建未真机验证**：Claude Code／Codex 上次真机验证在 309 批；本批改动只在 kb 运行时与文档，
  各宿主 MCP 契约未变，故未重跑远程安装。

## 2026-10-27 第三百零九批（plugins）：Claude Code 与 Codex **真机安装验证通过**（两条远程通道实测）

本机实际装有 Claude Code 2.1.310 与 Codex CLI 0.164.0，故 306-307 批挂着的
「五宿主未真机验证」第一次被真正跑掉两条。

### Claude Code（远程市场 → 装 → 起服务，全通）

1. `claude plugin validate ./claude-plugin` → **√ Validation passed**
   （首跑报 ICON_MISSING 与「README 缺市场安装行」，均已补：512×512 PNG 图标、安装命令行）。
2. `claude plugin marketplace add LinHoMo/yi-plugins` → √ added。
3. `claude plugin install yi@yi-plugins` → √ installed。
4. `claude plugin details yi` → **Skills (1) yi-divination、MCP servers (1) yi**。
5. `claude mcp list` → `plugin:yi:yi: node …\src\server.mjs — √ Connected`
   （宿主真的拉起了我们的 MCP 服务并完成握手）。

**途中抓到一个真缺陷（306 批登记的"未验证"正好命中）**：
首装出来是 **Skills 0 / MCP 0 的空壳**。原因——`marketplace.json` 的插件条目
**没有子目录字段**：写 `path: "./claude-plugin"` 会被官方**静默忽略**
（`claude plugin validate` 明确报 `Unknown field 'path'. Claude Code ignores it at load time`），
于是装的是仓库根。官方模型是「市场仓 → 独立插件仓」，故新建 **`LinHoMo/yi-claude`**，
市场条目改用 `{ source: 'github', repo: 'LinHoMo/yi-claude' }` 后即通
（`url` 形式在此版本未被采用，装出来的仍是市场仓本身）。

### Codex（市场 → 装，通；MCP spawn 未实测）

1. `codex plugin marketplace add https://github.com/LinHoMo/yi-plugins` →
   首跑被宿主**明确拒绝**：`unknown variant ON_FIRST_USE, expected ON_INSTALL or ON_USE`
   ——我们 `.agents/plugins/marketplace.json` 的 `policy.authentication` 写错了枚举。改 `ON_USE` 后 √ added。
2. `codex plugin add yi@yi-plugins` → √ installed, enabled 1.0.0，插件根正确指向 `codex-plugin/`
   （**Codex 支持 `source: local + path` 子目录**，与 Claude 不同）。
3. `codex mcp get yi` → 条目已注册（command node、args `${CODEX_PLUGIN_ROOT}/src/server.mjs`、enabled）。
   ⚠ **未实测**：`${CODEX_PLUGIN_ROOT}` 是否在 spawn 时展开、以及模型端到端发起 `tools/call`
   都没跑（非交互模式在本机沙箱里超时/被拦截）。

### 仍未验证

- Gemini CLI、Yan Agent、DSH 三家：本机无宿主（Gemini 未安装）；Yan 那条只做到
  「按 Yan 的方式稀疏克隆发行仓」的拉取级验证。
- Claude 的模型端到端 `tools/call`（非交互 `-p` 在本机超时未完成）。

## 2026-10-27 第三百零八批（plugins）：新增「对外文书口径声明覆盖门」

- `scripts/selftest.mjs` [7b] 段：**每一份对外文档都必须自带口径声明**
  （命中 `古籍案例对齐分 / 不是现实命中率 / 不代表现实预测命中率` 任一），缺一即判红，
  带负例自证（一份明知没写声明的文档必须被抓到）。
- 立这条门的直接原因：304 批抓到的**「诚实徽章反向失真」**——那句本该示弱的话因数字过期
  变成了失真，而它当时所在的那份文档**根本没写口径**。声明到文档，比只写在铁律里更不容易漏。
- 首跑抓到两处自身问题（登记在此）：① 目标面把源码模块 `plugins/mcp/tools.mjs`
  也算进「对外文书」，误判缺声明——禁语要扫它、**口径声明不该要求它**，两个目标面已拆开；
  ② 口径扫描与禁语扫描共用一份 targets 导致耦合，已各自独立。
- 当前覆盖 9 份文档（根 README、CAPABILITY、SKILL.md、五宿主 README/INSTRUCTIONS/GEMINI.md 等），全 √。

## 2026-10-27 第三百零七批（plugins）：发布树建成——远程分发的结构性解法落地
> 勘误：同批初稿的重复节已去重；发行树、publish.mjs 与四家适配器于 497 批删除，本节所述发布方式不再适用。


**问题不是"没写安装文档"，是结构上互斥**：`engine/`、`skills/`、`src/` 按仓库纪律
不入库，而 Claude Code / Codex / Gemini CLI / Yan 的远程分发**全部走 git**（只拿已提交
文件）。于是 304～306 批四家都只能本地安装。改文档解决不了，得改结构。

**解法：源与发行分离。** 新增 `plugins/scripts/publish.mjs`，产出一棵只含可安装产物的
发行树 `plugins/dist/`（不入库），由它单独成为 git 仓/分支被各家拉取；
源仓继续维持"产物不入库"的纪律，两不相犯。

- `publish.mjs`（默认）：把五家适配器的**完整目录**（清单 + `engine/` + `skills/` +
  `src/` + README/CHANGELOG/LICENSE）复制到 `dist/`，并生成三份宿主入口文件：
  - `.claude-plugin/marketplace.json`（Claude 市场目录）
  - `.agents/plugins/marketplace.json`（Codex 仓库级市场，`source: local`）
  - 仓库根 `gemini-extension.json` + `GEMINI.md`——**Gemini 一个仓库 = 一个扩展**，
    没法像 Claude/Codex 那样用市场目录，故把仓库根本身做成扩展、入口指进
    `gemini-plugin/`。这是四家里唯一的结构性差异，已在文件与 README 写明。
  - Yan 不需要目录文件（它遍历树找 `yan-plugin.json`），DSH 不走 git。
- `publish.mjs --check`：发布树**可安装性**检查——五家各自"清单 + MCP 入口 +
  `engine/MANIFEST.json` + `skills/yi-divination/SKILL.md` + 引擎入口脚本"齐备、
  零 `case_library.md`、知识库篇数与登记表一致，**含负例自证**（多塞一个缺失入口即被抓到）。
- 脚本**只生成文件，不 commit、不 push、不建远程**——外部动作留给用户，
  末尾打印两条确切命令（独立发行仓 / 同仓发行分支）。
- `.gitignore` 加 `plugins/dist/`；根 README 与各宿主 README 的"只能本地安装"表述
  改为指向发布流程。

**实跑**：`build` rc=0 → `publish` rc=0 → 内置 `--check` 全绿（5 家自包含 + 负例自证 +
零案例库 + 知识库 9 篇）；`selftest` rc=0。产物 ≈15MB（五份引擎副本，
但相同内容在 git 里只存一份 blob，进仓远小于此）。

### 已发布（本批后续动作）

- 发行仓 **https://github.com/LinHoMo/yi-plugins** 已建（public，默认分支 `main`，828 文件，
  `.git` 1.6MB——五份引擎副本内容相同，git 只存一份 blob）；
  已打 **v1.0.0** release：https://github.com/LinHoMo/yi-plugins/releases/tag/v1.0.0
- **通道实测（唯一一条真跑过的远程通道）**：按 Yan 的方式
  `git clone --depth 1 --filter=blob:none --sparse` + `sparse-checkout set --cone yan-plugin`
  拉取发行仓，结果——清单指向的 12 个文件（instructions + skills + 10 条 resources）
  **零缺失**、两科 `engine` 入口与内核副本在位、`src/server.mjs` 在位、
  **无 `case_library.md` 混入**。即「产物不入库」与「远程可装」第一次同时成立。
- 踩坑记（以免复发）：`publish.mjs` 开头会 `rm -rf dist/`，**会把 dist 里手工 init 的
  `.git` 一起删掉**；之后在 `dist/` 里敲 git 命令会沿目录向上找到**源仓**的 `.git`，
  于是提交落进了源仓。故同步发行仓一律走**克隆**而不是在 dist 里 init。

### 未做的事（如实）

- **其余四条通道仍未真机验证**：Claude 的 `marketplace.json`、Codex 的
  `.agents/plugins/marketplace.json`、Gemini 的根扩展、DSH 的 npm 包——
  本机一家宿主都没有，只做了 Yan 那条通道的拉取级验证。
- **Claude 的 marketplace.json 未真机验证**：官方示例是「市场仓 → 独立插件仓」，
  这里改指**同仓子目录**，能否被 Claude 接受未测。文件里写了 `_note` 提示，
  README 也标了；未跑通前请用 `claude --plugin-dir ./claude-plugin` 本地试装。
- Codex 第三方公开目录仍未开放，即便有发行树也进不了官方目录（只能 repo/用户级市场）。
- 五家宿主**全部未做真机安装验证**（本机无任何一家宿主）。

## 2026-10-27 第三百零六批（plugins）：三家新宿主接入（Claude Code / Codex / Gemini）＋ Python 解释器探活

**这是 305 批「一次构建 + N 份清单」的第一次实战检验**：接三个新宿主，
每个只新增 **2 个宿主专属文件**（清单 + MCP 声明；Gemini 是清单 + 上下文文件），
共享运行时、技能正文真源、知识库登记表**一行没复制**。

- 新增适配器：`claude-plugin/`（`.claude-plugin/plugin.json` + `.mcp.json`）、
  `codex-plugin/`（`.codex-plugin/plugin.json` + `.mcp.json`）、
  `gemini-plugin/`（`gemini-extension.json` + `GEMINI.md`）。
  三家的 MCP 入口都用宿主变量 `${CLAUDE_PLUGIN_ROOT}` / `${CODEX_PLUGIN_ROOT}` /
  `${extensionPath}`——**写死绝对路径换台机器就指不到包内入口**，
  自检 [6] 段各自断言 + 替换负例自证。
- **自检 [6] 段改为按宿主分流**（`MANIFEST_RULES` / `MCP_SPEC` 两张表）。
  原因：306 批首跑时这块只按「有没有 manifest」分两类，把 Claude 也套进 Yan 的
  `resources` 对账里，一口气报了 12 条红——**那是断言写宽，不是真的缺陷**。
  现在 Yan 的 `resources` 对账由 `reconcileResources` 显式开门，其余宿主各走各的规则。
- **共享层补强（影响全部宿主）**：`python.mjs` 增加**探活**。
  Windows 上 PATH 里的 `python` 常是微软商店的「应用执行别名」空壳（0 字节占位，
  `existsSync` 为真、spawn 只会弹商店）；306 批前只判存在，
  于是"装了 Python"的机器上第一次起卦就崩在一个打不开的解释器上。
  现在每个候选都要 `-c` 探针跑通才算数，被跳过的会列进报错信息；
  显式覆盖变量（`DSH_PYTHON`/`YI_PYTHON`）指了但跑不起来则**直接报错，不悄悄回退**。
- 各宿主卷各自登记 306 批（见 `claude-plugin/`、`codex-plugin/`、`gemini-plugin/` 的 CHANGELOG）。

**实跑**：`build` rc=0（一次构建分发到 **dsh / claude / codex / gemini / yan 五家**）；
`selftest` **全绿 rc=0**。

### 未做的事（如实）

- **三家都没做真机安装验证**（本机无 Claude Code / Codex / Gemini 宿主）。
  清单与协议面都是复刻各家官方约束的机械断言，**复刻≠放行**；
  首次安装请按各 README 走一遍并回填对应 CHANGELOG。
- **分发方案仍未定**：`engine/`、`skills/`、`src/` 不入库，而 Claude/Codex/Gemini 的
  远程通道都要已提交文件 → 三家目前都只能本地安装。
  解法未变：开 `plugins-dist` 发行分支，或走 Release tarball 后本地装。
- Codex 的**第三方公开目录尚未开放**，即便产物能提交也进不了官方目录，
  只能走 repo/用户级 marketplace.json。

## 2026-10-27 第三百零五批（plugins）：共享打包层建成——从「N 个宿主 N 套 build」收敛为「一次构建 + N 份清单」

**动机**：304 批建成 yan-plugin 时，`dsh-plugin/` 与 `yan-plugin/` 各有一套
`build*.mjs`、一份 `KB_DOC` 登记表、一份 `src/*.mjs` 运行时副本、一份 `engine/`
与 `skills/` 产物。yan 侧靠自检 [2.4] 段机械对拍两份 `KB_DOC` 防漂移——
**那是补丁，不是解法**：两份真源迟早分叉，门只能事后报警。
照那个形态再接 Claude / Codex / Gemini 三家，就是 5 份产物、5 条漂移面。

**改动**

- 新增 `plugins/`：
  - `SKILL.md` —— 技能正文**唯一真源**（从 `dsh-plugin/SKILL.md` 迁来，
    构建期可按宿主追加附加段，正文永不被改）。
  - `mcp/` —— 共享运行时唯一真源（8 个文件）：`server.mjs`（零依赖 stdio MCP）、
    `schema.mjs`（dsh 简写→JSON Schema 的唯一一处方言转译）、`tools.mjs`（1.0 冻结契约）、
    `engine.mjs`、`kb.mjs`、`report.mjs`、`python.mjs`、`kb-synonyms.json`。
  - `scripts/kb-docs.mjs` —— 知识库登记表唯一真源（原两份合并，对拍门随之删除）。
  - `scripts/build.mjs` —— **一次构建**：从两科收集 `plugins/engine/` 与
    `plugins/skills/`，再分发到 `ADAPTERS` 登记表里的每个适配器目录。
  - `scripts/selftest.mjs` —— 7 段自检，见下。
- 删除：`dsh-plugin/scripts/{build-engine,build-skills}.mjs`、
  `yan-plugin/scripts/{build,kb-docs,selftest}.mjs`、
  `dsh-plugin/src/{engine,python,tools,kb,report}.mjs`、`dsh-plugin/src/kb-synonyms.json`、
  `yan-plugin/src/`（全部改为构建分发）。
  两家的 `package.json` 脚本改为指向 `../plugins/scripts/*`。
- `python.mjs` 合成一份：优先级为 `DSH_PYTHON` → `YI_PYTHON` → DSH 桌面自带运行时
  → PATH `python`/`python3` → `py` 启动器。各宿主只走自己那一档，其余同序。
- `.gitignore`：新增 `plugins/engine/`、`plugins/skills/`、
  `dsh-plugin/src/*.mjs`（保留 `index.mjs`）、`dsh-plugin/SKILL.md`、`yan-plugin/src/`。

**自检 7 段**（`node plugins/scripts/selftest.mjs`，判红即 exit≠0）

| 段 | 守什么 |
|---|---|
| [1] | **分发一致性**：适配器 `src/*.mjs` 与 `plugins/mcp/` 真源**逐字节同源**（含负例自证：篡改一个字节即红） |
| [1.5] | 共享层与所有适配器零 `case_library.md`（含负例自证） |
| [2] | 两科 chart/analyze/narrate/render + 内核副本 + MANIFEST 齐备 |
| [3] | 各适配器 SKILL.md 正文以真源为前缀 + frontmatter + 知识库篇数对账 |
| [4] | **直接跑真源** `plugins/mcp/server.mjs` 冒烟：initialize / tools/list / `yi_kb` / `yi_liuyao` |
| [5] | 工具契约：四工具在列、inputSchema 为 object、`yi_liuyao` 参数集与 1.0 冻结面一致 |
| [6] | 适配器清单规范 + resources 双向对账（负例自证 a/b）+ 包体预算 |
| [7] | 对外文本无禁语（逐行 + 否定语境豁免，含负例自证） |

**首跑实测**：构建一次产出 `plugins/engine/` 与 `plugins/skills/`（9 篇 + INDEX），
分发到两家后自检全绿（rc=0）；`yi_kb` 命中带 `resource:kb-liuyao-interpretation-guide`，
`yi_liuyao` 用 Python 3.13.12 起出「贲」卦。

**首跑抓到并当场修掉的真 bug**（登记在此，防复发）：
`kb.mjs` 的 `resolveKbRoot()` 按目录名判层级（`src` 上一级、否则上两级），
而共享真源在 `plugins/mcp/` —— 命中 else 分支后多跳一级到**仓库根**，
于是 `files_scanned: 0`、`yi_kb` 永远空手。**这个 bug 只会在"跑真源"的那条路上现形**：
若自检仍跑适配器里的副本（旧形态），两家都正常，缺陷会被一直盖住。
改法：统一约定模块恒在 `<root>/mcp/` 或 `<root>/src/`，包根恒为 `..`。

### 未做的事（如实）

- **适配器登记表目前只有 dsh 与 yan 两家**，Claude / Codex / Gemini 尚未接入
  （304 批只做了选型核实，未动手）。
- **`dsh-plugin/scripts/selftest.mjs`（13 段）未合并**进本目录——它是已发布包
  （v1.0.23）的宿主侧 QA，含 npm 包内容与 DSH 内验证，本批只改了它的构建入口，
  未改其判据。是否合并、怎么合并，留给下一批。
- 未重跑 `npm --prefix dsh-plugin run verify-in-dsh`（需 DSH 宿主）。
- 分发方案（`plugins-dist` 分支 / Release tarball）仍未定，各宿主"远程市场装不上"
  的限制依然存在。

> **第五百二十三批现状勘误**（上文「未做的事」按登记时点保留原文，不改写）：
> ① 497 批起只保留 DSH 一家宿主，「接入 Claude／Codex／Gemini」的对象已删除；
> ② 已无第二家宿主可「合并」，宿主侧 QA 由 522 批 `npm --prefix dsh-plugin run check`
> 全链跑通（含 `selftest` 与 `verify-in-dsh`），③ 同批跑通，不再依赖手工重跑；
> ④ 分发方案按 AGENTS.md §二已定为 GitHub Release 的 npm tgz，不再有独立发行树。
> 四条均非现行待办，逐条依据见 `GOVERNANCE.md`「当前真缺口」G4。
