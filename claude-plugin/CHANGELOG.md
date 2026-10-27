# claude-plugin CHANGELOG

> 本卷登记 **Claude Code 插件**（`yi`）自身的批次；批次号沿用全仓流水。
> 共享层的改动（构建、运行时、技能正文、知识库）登记在 `plugins/CHANGELOG.md`，
> 本卷只记宿主侧那点事。

## 2026-10-27 第三百零六批（claude-plugin）：Claude Code 插件建成（1.0.0）

依托 305 批建成的共享打包层接入第二家新宿主——**本批新增的宿主专属文件只有 3 个**
（`.claude-plugin/plugin.json`、`.mcp.json`、README/CHANGELOG/LICENSE），
共享运行时、技能正文、知识库登记表全部复用 `plugins/` 那一份，没有复制第二份。

- `.claude-plugin/plugin.json`：`name: "yi"`（kebab-case，Claude 用它做命名空间），
  version/description/author/license/keywords。**只有清单能放 `.claude-plugin/` 里**，
  组件（`skills/`、`.mcp.json`）必须留在插件根，否则不加载。
- `.mcp.json`：本地 stdio MCP，`command: node`，
  `args: ["${CLAUDE_PLUGIN_ROOT}/src/server.mjs"]`。
  **必须用 `${CLAUDE_PLUGIN_ROOT}`**——换成硬编码绝对路径的话换台机器就指不到包内入口；
  共享自检 [6] 段有一条专门断言＋负例自证盯着这件事。
  `env.YI_PYTHON` 留空作为「用户可填的解释器覆盖位」。
- 技能附加段（构建期追加，不改真源正文）：说明本宿主下怎么用 `yi_kb` 定位
  再用 Read 读节段、工具名带 `mcp__yi__` 前缀、以及 Python 缺失时的处理。
- 共享层同批补强（影响全部宿主）：`python.mjs` 增加**探活**——
  Windows 上 PATH 里的 `python` 常是微软商店的「应用执行别名」空壳
  （`existsSync` 为真、spawn 只会弹商店），306 批前只判存在，
  于是"装了 Python"的机器上第一次起卦就崩在一个打不开的解释器上。
  现在每个候选解释器都要 `-c` 探针跑通才算数，跳过的会被列进报错信息。

**实跑**：`node plugins/scripts/build.mjs` rc=0（一次构建分发到 dsh/claude/yan 三家）；
`node plugins/scripts/selftest.mjs` 全绿 rc=0（含本适配器的 5 条清单断言 + 5 条
`.mcp.json`/技能断言 + 1 条路径变量负例自证）。

### 未做的事（如实）

- **未在真机 Claude Code 里安装验证**：本机无该宿主。`claude --plugin-dir ./claude-plugin`
  与 `claude plugin validate` 都没跑过；协议面是复刻其官方约束的机械断言，**复刻≠放行**。
- **远程市场装不上**：Claude Code 市场走 git，而 `engine/`、`skills/`、`src/` 不入库。
  要开需 `plugins-dist` 发行分支，本批未开（README 已写明，不冒充可用）。
- 未做 slash command / subagent / hooks 等 Claude 独有的组件形态——
  四工具 + 技能 + 知识库已够用，多做的每一件都是要长期维护的第二个真源。
