# gemini-plugin CHANGELOG

> 本卷登记 **Gemini CLI 扩展**自身的批次；批次号沿用全仓流水。
> 共享层改动登记在 `plugins/CHANGELOG.md`，本卷只记宿主侧那点事。

## 2026-10-27 第三百零六批（gemini-plugin）：Gemini CLI 扩展建成（1.0.0）

依托 305 批的共享打包层接入——**本批新增的宿主专属文件只有 2 个**
（`gemini-extension.json`、`GEMINI.md`，另加 README/CHANGELOG/LICENSE）。

- `gemini-extension.json`：`mcpServers.yi` 用 `command: node` +
  `${extensionPath}`（**不能用绝对路径**），`contextFileName: "GEMINI.md"`。
  `name` 需与扩展目录同名，故取 `gemini-plugin`。
- `GEMINI.md`：因为 Gemini CLI **没有 `skills/` 发现机制**，入口说明只能走 context 文件；
  里面写清四工具、知识库读法与边界口径。这个差异是三家新宿主里唯一的结构性差异，
  已写进技能附加段与共享自检的按宿主分流断言。
- 知识库仍随包分发在 `skills/yi-divination/references/`，靠 `yi_kb` 定位后读文件。

**实跑**：构建 rc=0；共享自检全绿 rc=0（含本扩展的 3 条清单断言 + 4 条 MCP 断言 + 1 条
路径变量负例自证）。

### 未做的事（如实）

- **未在真机 Gemini CLI 里安装验证**（`gemini extensions install/link` 都没跑过）。
- 从 GitHub 装需要产物已提交，而 `engine/`、`skills/`、`src/` 不入库——
  故 GitHub 直装目前拿不到可用包，只能本地 install/link。
