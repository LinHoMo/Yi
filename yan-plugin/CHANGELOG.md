# yan-plugin CHANGELOG

> 本卷登记 Yan Agent 插件（`yan-yi-divination`）自身的批次；批次号沿用全仓流水。
> 插件是两科的**打包层**：引擎与知识库都是构建产物（不入库），两科缺陷修复的判据与
> 实跑记录仍以两科 `docs/CHANGELOG.md` 为准；本卷只记插件半的事（宿主适配、构建、
> 清单、自检、安装）。
>
> **semver 映射**沿用 AGENTS.md §二 的 dsh-plugin 规则（功能批 minor+1、
> 修复/文档批 patch+1）；**批次号是唯一真源**。

## 2026-10-27 第三百零五批（yan-plugin）：并入共享打包层（1.0.1，无对外契约变动）

- `yan-plugin/src/` **整体改为构建产物**（真源 `plugins/mcp/`）；
  `scripts/{build,kb-docs,selftest}.mjs` 删除，构建与自检统一到
  `plugins/scripts/{build,selftest}.mjs`。`package.json` 脚本改指向共享层。
- 知识库登记表合并为 `plugins/scripts/kb-docs.mjs` 一份，原自检 [2.4] 段
  （「与 dsh 侧 KB_DOC 对拍」）随之删除——**那份门是补丁，不是解法**：
  两份真源迟早分叉，门只能事后报警；现在只有一份真源，不需要对拍。
- 技能正文真源改为 `plugins/SKILL.md`（304 批时是 `dsh-plugin/SKILL.md`）。
- 实跑：`node plugins/scripts/selftest.mjs` 全绿 rc=0（含本适配器的清单规范与
  resources 双向对账两组负例自证）。
- 宿主限制不变：远程市场仍不可用（产物不入库），安装走本地文件夹 / 本地市场。

## 2026-10-27 第三百零四批（yan-plugin）：Yan Agent 插件建成（1.0.0）

**背景**：用户要求在 GitHub 上核实 Yan Agent（`ViaTumLab/Yan-Agent`，Electron 44.4.5，
Windows 桌面 AI 工程工作区）的扩展体系，并为 Yi 做一个同级的插件。
核实结论：Yan 的扩展由**插件 / 技能 / MCP / 项目规则**四类组成；插件清单是包根的
`yan-plugin.json`（`schemaVersion: 1`，schema 见 `lib/plugins/manifest.js`），
能力只能经三条声明面暴露——`skills[]`、`resources[]`、`mcpServers[]`（本地 stdio MCP，
支持 `$node` 与 `${pluginRoot}` / `${config.*}` / `${workspace}` 展开），
**安装期不执行任何脚本或钩子**（`upstream.js` 明文）。

- 新增 `yan-plugin/`：
  - `yan-plugin.json`：`id=yi-divination`、1 条 `skills`、10 条 `resources`、
    1 条 `local` MCP（`command: $node`，入口 `src/server.mjs`，`timeoutMs` 120000）、
    配置项 `pythonPath`（非必填）、环境变量 `YI_PYTHON`（非必填、`required=false`）。
  - `src/server.mjs`：零依赖 stdio MCP 服务（JSON-RPC 2025-03-26，换行分隔）。
    **零依赖是硬约束**：Yan 的 `inventory()` 跳过 `node_modules`，随包能力只能靠内建模块。
    工具级失败走 `isError` 而非 JSON-RPC error——让模型看到原因并自行重试一次
    （AGENTS.md §一.1），协议级问题才走 error。
  - `src/schema.mjs`：**唯一一处** dsh 简写参数 → MCP JSON Schema 的方言转译，
    使 `tools.mjs` 的工具定义在两个宿主上逐字同源（不复制第二份定义）。
  - `src/python.mjs`：Yan 版解释器定位（与 dsh 版的差别只有第 1 档——
    **Yan 不自带 Python 运行时**，故显式覆盖变量是 `YI_PYTHON`，四档为
    `YI_PYTHON` → `python` → `python3` → `py`）。
  - `src/{tools,engine,kb,report}.mjs` + `kb-synonyms.json`：从 `dsh-plugin/src/` 逐字复用，
    保住 1.0 冻结契约（工具名/参数集/输出 value 结构）。
  - `src/kb.mjs` 增量：`resourceIdFor()` 与命中项上的 `resource` 句柄——
    **Yan 的包资源不在模型工作区里**，`read` 读不到，必须交出
    `plugins_read_resource` 能用的 `resource:kb-*` 句柄；
    id 生成规则与 `yan-plugin.json` 的 `resources[].id` 同式，由自检 [4] 双向对账。
  - `scripts/build.mjs`：按白名单词典从两科收集 `engine/`（同 dsh 口径，含
    `liuyao/assets`、`case_library.md` 排除），并从 `dsh-plugin/SKILL.md`
    （技能正文**唯一真源**）生成 `skills/`，只**追加**「Yan 侧读法」附加段、不改正文。
  - `scripts/kb-docs.mjs`：知识库登记表（构建与自检共用，双向闸门）。
  - `scripts/selftest.mjs`：包级自检 8 段 —— 清单规范 / 案例库零随包 / 引擎入口 /
    登记表跨宿主一致 / 技能正文同源 / 资源双向对账 / **真起 MCP 进程冒烟** / 包体预算 /
    禁语扫描。三段带负例自证（[1.5] 案例库扫描器、[4] 资源对账 a+b、[7] 禁语扫描器）。
  - `INSTRUCTIONS.md`、`README.md`、`LICENSE`、`package.json`。
- 根 `.gitignore` 追加 `yan-plugin/engine/`、`yan-plugin/skills/`（构建产物不入库，
  理由同 dsh-plugin：入库等于给「引擎/知识库 vs 两科真源」多存一份副本）。
- 根 `README.md` 新增「作为 Yan Agent 插件安装」一节；`AGENTS.md` §二 新增
  「yan-plugin 契约」并把 `npm --prefix yan-plugin run check` 并进月巡挂钩。

**首跑实测**（2026-10-27，本机）：build 出 `engine/`（164 文件 / 2.56MB）、
`skills/`（9 篇 + INDEX）；selftest 8 段全绿，其中 [5] 段真起进程冒烟通过——
`tools/list` 四工具在列、`yi_kb` 命中带 `resource:kb-liuyao-interpretation-guide`、
`yi_liuyao` 用 Python 3.13.12 起出「贲」卦。

**首跑抓到并当场修掉的两个自身缺陷**（登记在此，防复发）：
- [4] 负例自证写错方向：抽掉一篇时报的是「登记了不存在的资源」而不是「未登记资源」，
  判红数对了但断言正则错了 → 改为**双向各做一次**负例自证（a 抽一篇 / b 多塞一篇）。
- [7] 禁语扫描器误伤：「预测准确率」在本仓对外文书里几乎只出现在**自己禁令的那句**
  （「不得说预测准确率 X%」里），整文件匹配会把立规矩的那只手判成违规
  （首跑误伤 INSTRUCTIONS.md 与 SKILL.md 两处）→ 改为**逐行 + 否定语境豁免**
  （`不得|禁止|不许|不可|切勿|❌|不是|并非|而非|杜绝|避免`），豁免面刻意做窄，
  单独一句「本工具预测准确率 99%」仍判红（有负例自证盯着）。
  **第二次自咬**：README 的自检覆盖表里把禁语原样写进了表格行（描述规则用的），
  整行没有否定标记又被 [7] 抓到——改表行文案（不写原词）而非放宽豁免面。
  两次都是「写规矩的那段文字自己撞规矩」，说明这条门盯的是**字面**，
  以后写禁语相关说明要注意：要么带否定语境，要么别写原词。

### 未做的事（如实登记，不冒充完成）

- **远程市场通道未开**：Yan 的远程市场是 git 稀疏克隆，只拿已提交文件；
  而 `engine/`、`skills/` 按仓库纪律不入库。要开需一条只放构建产物的发行分支
  （如 `yan-plugin-dist`）＋发布流程，本批未做，README 里也只写了本地两条安装路径。
- **未在真机 Yan 里激活验证**：本机无 Yan 宿主；协议面靠 `scripts/selftest.mjs` [5]
  真起 MCP 进程复刻 Yan 客户端的握手与调用序列（initialize → notifications/initialized →
  tools/list → tools/call），清单面靠本地复刻 `lib/plugins/manifest.js` 的 zod 约束断言。
  **这两条都是复刻，不等于真机放行**——首次在 Yan 里安装请按 README 走一遍并回填本卷。
- 未做 Yan 侧的 agent preset / 子代理角色适配（DSH 侧有 `presets/`，Yan 侧本批无对应机制）。
