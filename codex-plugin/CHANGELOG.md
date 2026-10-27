# codex-plugin CHANGELOG

> 本卷登记 **Codex CLI 插件**（`yi`）自身的批次；批次号沿用全仓流水。
> 共享层改动登记在 `plugins/CHANGELOG.md`，本卷只记宿主侧那点事。

## 2026-10-27 第三百零六批（codex-plugin）：Codex 插件建成（1.0.0）

依托 305 批的共享打包层接入——**本批新增的宿主专属文件只有 2 个**
（`.codex-plugin/plugin.json`、`.mcp.json`，另加 README/CHANGELOG/LICENSE）。

- `.codex-plugin/plugin.json`：`name: "yi"`（kebab-case，Codex 用它做命名空间与缓存键），
  `skills: "./skills/"`、`mcpServers: "./.mcp.json"`，附 `interface` 展示元数据。
  只有清单能放 `.codex-plugin/` 里，组件必须留在插件根。
- `.mcp.json`：本地 stdio MCP，`command: node`，
  `args: ["${CODEX_PLUGIN_ROOT}/src/server.mjs"]`——**必须用宿主变量**，
  写死绝对路径换台机器就指不到包内入口（共享自检 [6] 段有断言 + 负例自证）。
- 技能附加段说明本宿主下 `mcp__yi__` 前缀与知识库读法。

**实跑**：`node plugins/scripts/build.mjs` rc=0（一次构建分发到 dsh/claude/codex/gemini/yan 五家）；
`node plugins/scripts/selftest.mjs` 全绿 rc=0。

### 未做的事（如实）

- **未在真机 Codex 里安装验证**；第三方公开目录**尚未开放**，进不了官方目录，
  只能走 repo/用户级 marketplace.json 或本地安装。
- 远程 git 市场拿不到不入库的 `engine/`、`skills/`、`src/`（通用限制）。
